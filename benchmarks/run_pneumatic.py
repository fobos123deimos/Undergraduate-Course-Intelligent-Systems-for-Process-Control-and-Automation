"""Run the explicitly parameterized teaching variant and export parity fixtures."""
from pathlib import Path
from dataclasses import asdict
import argparse
import json
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from intelligent_control import pneumatic_physical as p


def main(write_reference=False):
    out=ROOT/'benchmarks/results';out.mkdir(exist_ok=True)
    report={'data_type':'synthetic','canonical_valve_calibration_recovered':False,
            'model':'six-state SI mass/energy variant with vertical gravity',
            'solver':'DOP853, rtol1e-9, atol1e-11, max_step0.005s',
            'input':'2 sin(2 pi t) V; each payload constant during its own 2s run',
            'parameters':asdict(p.Parameters()),'cases':[]}
    reference={'state_order':['x_m','velocity_m_s','mass_I_kg','mass_II_kg','temperature_I_K','temperature_II_K'],
               'cases':[],'local_models':[]}
    plots=[]
    for mass in [3.,6.,9.]:
        params=p.Parameters(load_mass=mass);time,state=p.simulate(lambda t:2*np.sin(2*np.pi*t),p=params,duration=2.,samples=201)
        pressure=np.array([p.observe(row,params)[0] for row in state])
        balance_residual=0.
        for tt,row in zip(time,state):
            dx,info=p.balances(row,2*np.sin(2*np.pi*tt),params)
            q=info['mass_flows']
            source=params.cp*(params.reservoir_temperature*(q[1]+q[2])-row[4]*q[0]-row[5]*q[3])
            energy_rate=sum(params.cv*(row[4:6]*dx[2:4]+row[2:4]*dx[4:6]))+params.total_mass*row[1]*dx[1]+params.total_mass*params.gravity*row[1]
            balance_residual=max(balance_residual,abs(energy_rate-source+info['friction']*row[1]))
        entry={'load_kg':mass,'position_min_m':float(state[:,0].min()),'position_max_m':float(state[:,0].max()),
               'temperature_min_K':float(state[:,4:].min()),'temperature_max_K':float(state[:,4:].max()),
               'pressure_min_Pa':float(pressure.min()),'pressure_max_Pa':float(pressure.max()),
               'energy_balance_max_residual_W':balance_residual}
        report['cases'].append(entry)
        reference['cases'].append({'load_kg':mass,'time':time.tolist(),'state':state.tolist()})
        np.savetxt(out/f'pneumatic_mass_{int(mass)}kg.csv',np.c_[time,2*np.sin(2*np.pi*time),state,pressure],delimiter=',',
                   header='time_s,voltage_V,x_m,velocity_m_s,mass_I_kg,mass_II_kg,T_I_K,T_II_K,p_I_Pa,p_II_Pa',comments='')
        plots.append((mass,time,state,pressure))
    for index in [1,3,15]:
        local=p.identified_local_model(index)
        reference['local_models'].append({k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in local.items()})
    report['specific_R_J_kgK']=p.Parameters().R
    report['implicit_end_volume_m3']=p.Parameters().residual_volume
    report['limitations']=['No measured valve area/discharge/leakage calibration recovered.',
        'No experimental validation; synthetic traces are not published tracking results.',
        'Smoothed Coulomb friction has no static stick-slip or hysteresis.',
        'Constant payload within each run; no attachment momentum or hard-stop impact model.']
    (out/'pneumatic_physical_metrics.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if write_reference:
        (ROOT/'matlab/pneumatic_reference.json').write_text(json.dumps(reference,indent=2)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,2,figsize=(10,6),layout='constrained')
    for mass,t,x,pressure in plots:
        label=f'{mass:g} kg payload'
        ax[0,0].plot(t,x[:,0]*1000,label=label)
        ax[0,1].plot(t,(pressure[:,0]-pressure[:,1])/1000,label=label)
        ax[1,0].plot(t,x[:,4]-293.15,label=label)
        ax[1,1].plot(t,x[:,5]-293.15,label=label)
    for axis,title,unit in zip(ax.flat,['Vertical displacement','Chamber pressure difference','Chamber I heating','Chamber II heating'],['mm','kPa','K above293.15','K above293.15']):
        axis.set(title=title,xlabel='Time (s)',ylabel=unit);axis.grid(alpha=.25)
    ax[0,0].legend();fig.suptitle('Pneumatic SI variant: synthetic response with assumed valve geometry')
    fig.savefig(out/'pneumatic_physical.png',dpi=160);plt.close(fig)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write-reference',action='store_true');args=parser.parse_args()
    main(args.write_reference)
