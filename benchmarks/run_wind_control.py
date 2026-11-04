"""Execute the new full-load LQR/PDC design with the declared ROSCO map."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from intelligent_control import wind_control as w


def main(write_reference=False):
    aero=w.default_map();points=w.design(aero)
    runs={name:w.simulate(aero,points,scheduled=flag)
          for name,flag in [('scheduled_pdc',True),('fixed_local_lqr',False)]}
    out=ROOT/'benchmarks/results';out.mkdir(exist_ok=True)
    report={'data_type':'synthetic','model':'8-state regulation form of the 9-state reduced turbine',
            'map_sha256':aero.sha256,'map_variant':'ROSCO 2022, not recovered 2014 map',
            'design_winds_m_s':[p['wind'] for p in points],
            'test_winds_m_s':[12.,13.,15.],
            'state_scales':w.STATE_SCALE.tolist(),'input_scales':w.INPUT_SCALE.tolist(),
            'Q_diagonal':np.diag(w.Q).tolist(),'R_diagonal':np.diag(w.R).tolist(),
            'solver':'RK4, held commands; sample and integration step 0.02 s',
            'lower':w.LOWER.tolist(),'upper':w.UPPER.tolist(),'rates_per_s':w.RATE.tolist(),
            'cases':{name:{k:r[k] for k in ['speed_rmse','speed_peak_error','pitch_peak_deg']} for name,r in runs.items()},
            'interpretation':'New operating-point design; no global stability proof or reproduction of Table 12.'}
    (out/'wind_control_metrics.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for name,r in runs.items():
        np.savetxt(out/f'wind_{name}.csv',np.c_[r['time'],r['wind'],r['state'],r['command']],delimiter=',',
                   header='time_s,wind_m_s,tower_m,blade_m,torsion_rad,tower_velocity,blade_velocity,rotor_rad_s,generator_rad_s,pitch_rad,torque_Nm,pitch_command_rad',comments='')
    if write_reference:
        reference={'points':[{'wind':p['wind'],'state':p['state'].tolist(),'gain':p['gain'].tolist()} for p in points],
                   'speed_rmse':runs['scheduled_pdc']['speed_rmse']}
        (ROOT/'matlab/wind_control_reference.json').write_text(json.dumps(reference,indent=2)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,constrained_layout=True)
    for name,r in runs.items():
        axes[0].plot(r['time'],r['state'][:,5],label=name.replace('_',' '))
        axes[1].plot(r['time'],np.rad2deg(r['command'][:,1]))
        axes[2].plot(r['time'],r['command'][:,0]/1e6)
    axes[0].axhline(1.2,color='black',linestyle=':',linewidth=1)
    axes[0].set_ylabel('Rotor speed (rad/s)');axes[0].legend()
    axes[1].set_ylabel('Pitch command (deg)');axes[2].set_ylabel('Torque (MN m)');axes[2].set_xlabel('Time (s)')
    fig.suptitle('Interpolated wind study: 12, 13 and 15 m/s')
    fig.savefig(out/'wind_control.png',dpi=150);plt.close(fig)
    print(json.dumps(report['cases'],indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write-reference',action='store_true')
    main(p.parse_args().write_reference)
