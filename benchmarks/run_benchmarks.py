"""Run auditable short experiments; do not substitute industrial benchmarks."""
from pathlib import Path
import json
import sys
import hashlib
import os
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, least_squares

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from intelligent_control import benchmarks as b


def integrate(rhs,x0,end,points=201):
    solution=solve_ivp(rhs,[0,end],x0,t_eval=np.linspace(0,end,points),
                       method='Radau',rtol=1e-8,atol=1e-10)
    if not solution.success or not np.isfinite(solution.y).all():
        raise RuntimeError(solution.message)
    return solution.t,solution.y.T


def preserved_evidence(relative_path, accepted_status, check):
    """Inspect a saved external result; never launch an external simulator."""
    path=ROOT/relative_path
    record={'evidence_path':relative_path,'rerun_by_this_command':False,
            'evidence_state':'missing'}
    if not path.is_file():return record,None
    payload=path.read_bytes();record['evidence_sha256']=hashlib.sha256(payload).hexdigest()
    try:
        data=json.loads(payload)
        if not isinstance(data,dict) or data.get('status')!=accepted_status or not check(data):
            record['evidence_state']='incomplete_or_not_passed'
            return record,None
    except (ValueError,KeyError,TypeError,AttributeError):
        record['evidence_state']='invalid'
        return record,None
    record.update(evidence_state='preserved_passed_record',evidence_date=data.get('date'),
                  evidence_record_status=data['status'])
    return record,data


def external_status():
    """Report preserved evidence separately from the experiments run by main."""
    fast,data=preserved_evidence('benchmarks/results/openfast-validation.json','passed',
        lambda d:all(k in d for k in ('release','case','duration_s','interpretation')) and
        d['all_outputs_finite'] is True and d['sample_count']>0 and
        d['official_reference_comparison']['status']=='passed' and
        d['official_reference_comparison']['channels_compared']>0)
    fast['status']='preserved OpenFAST execution and baseline comparison passed; not rerun by this command' if data else 'no complete passed OpenFAST execution record available; not run by this command'
    if data:
        fast.update(release=data['release'],case=data['case'],sample_count=data['sample_count'],
                    duration_s=data['duration_s'],scope=data['interpretation'])
    te,data=preserved_evidence('benchmarks/results/te-native/validation.json','passed',
        lambda d:'limitations' in d and all(k in d['nominal'] for k in ('matlab_version','duration_h')) and
        d['nominal']['all_outputs_finite'] is True and d['nominal']['sample_count']>0 and
        sorted(c['disturbance_from_start'] for c in d['disturbance_cases'])==[1,4] and
        all(c['all_outputs_finite'] is True and c['sample_count']>0 for c in d['disturbance_cases']))
    te['status']='preserved official revised TE nominal, IDV1 and IDV4 executions passed; not rerun by this command' if data else 'no complete passed native TE execution record available; not run by this command'
    if data:
        te.update(matlab_version=data['nominal']['matlab_version'],case_count=3,
                  duration_h_per_case=data['nominal']['duration_h'],scope=data['limitations'])
    gasifier,data=preserved_evidence('benchmarks/results/alstom-native/validation.json',
        'integration_and_input_checks_passed',lambda d:d['case_count']==11 and len(d['cases'])==11 and
        all(c['all_outputs_finite'] is True and c['specified_inputs_verified'] is True for c in d['cases']))
    gasifier['status']='preserved native ALSTOM integration/input checks passed; inspect reported control violations; not rerun by this command' if data else 'no complete native ALSTOM execution record; compatible Windows MATLAB/Simulink required'
    source,source_data=preserved_evidence('benchmarks/results/alstom-source-inspection.json',
        'source_inspection_passed',lambda d:'archive_sha256' in d and len(d['verified_source_files'])==6 and
        len(d['initial_conditions'])==3 and all(c['finite_initial_conditions'] is True for c in d['initial_conditions']))
    gasifier['source_inspection']=source
    if source_data and data is None:
        gasifier['status']='preserved ALSTOM source inspection passed; native execution pending compatible Windows MATLAB/Simulink'
    if source_data:gasifier['archive_sha256']=source_data['archive_sha256']
    return {'wind_fast':fast,'gasifier':gasifier,'tennessee_eastman':te}


def main():
    out=ROOT/'benchmarks/results'; out.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(out/'.mplconfig'))
    result={'seed':2014,'data_type':'synthetic unless explicitly sourced',
            'solver':'Radau rtol=1e-8 atol=1e-10; Euler 0.01 for sampled bioreactor',
            'external_execution_policy':'External entries reference preserved evidence; this command does not rerun OpenFAST, ALSTOM or Tennessee Eastman.',
            'experiments':{}}
    entries=result['experiments']
    for kind in ['siso','mimo']:
        u,y=b.artificial_data(1000,kind,'train')
        uv,yv=b.artificial_data(250,kind,'validation')
        entries['artificial_'+kind]={'equation':30 if kind=='siso' else 31,
            'train_samples':len(u),'validation_samples':len(uv),
            'maximum_output_magnitude':float(np.max(np.abs(y))),
            'note':'short demonstration; paper training length is 100000'}
        np.savetxt(out/f'{kind}_validation.csv',np.column_stack([uv,yv[:-1],yv[1:]]),
                   delimiter=',',header=','.join([f'u{i+1}' for i in range(uv.shape[1])]+
                   [f'y{i+1}_k' for i in range(uv.shape[1])]+[f'y{i+1}_next' for i in range(uv.shape[1])]),comments='')

    tp,xp=integrate(lambda t,x:b.pendulum_rhs(t,x,0,b.PendulumParameters(cart_coulomb=0)),[.03,0,0,0],.4)
    entries['pendulum']={'theta_initial_rad':.03,'theta_final_rad':float(xp[-1,0]),
        'note':'open-loop local instability demonstration; Coulomb friction removed explicitly'}

    pneu=b.pneumatic_rhs(0,[0,.01,5e5,5e5],b.educational_valve_flows(.1,5e5,5e5),gas_constant=287.05)
    entries['pneumatic']={'derivative_at_practice_point':pneu.tolist(),
        'status':'balance/closure evaluation, not canonical valve simulation',
        'closure':'linear flow; R=287.05 J/(kg K), kappa=1.4; no gravity term'}
    entries['hydrostatic']={'derivative_at_practice_point':b.hydrostatic_rhs(0,[.2,.5,2.,10.],[.001,.002],pump_speed=100).tolist(),
        'status':'literal transcription only; unresolved published scale inconsistencies'}

    tt,xt=integrate(lambda t,x:b.three_tank_rhs(t,x,[2e-5,1e-5]),[.3,.2,.25],40.)
    volume_error=.0154*(xt[-1].sum()-xt[0].sum())-40*3e-5
    entries['three_tank']={'maximum_level_m':float(xt.max()),'volume_balance_residual_m3':float(volume_error),
        'note':'all nominal drains closed; total volume increases'}

    cb=brentq(lambda s:(1-s)*np.exp(s/.4)-.769,.8,1)
    ca=cb*(1.02-cb)/1.02
    bio=np.empty((81,2)); bio[0]=[.08,.9]
    for k in range(80): bio[k+1]=b.bioreactor_sample(bio[k],.75)
    entries['bioreactor']={'sample_period':.5,'euler_substep':.01,'substeps_per_hold':50,
        'computed_equilibrium_at_u_0_769':[ca,cb],
        'reported_biomass_substrate_residual':float(b.bioreactor_rhs(0,[.1236837,cb],.769)[1])}

    tc,xc=integrate(lambda t,x:b.cstr_rhs(t,x,b.CSTR_U1),b.CSTR_SP1,.1)
    entries['cstr']={'time_unit':'hours','temperature_unit':'degrees C','input2_unit':'MJ/h',
        'rounded_sp1_derivative':b.cstr_rhs(0,b.CSTR_SP1,b.CSTR_U1).tolist(),
        'final_state':xc[-1].tolist(),'note':'nominal SP1 hold; not observer-based transition benchmark'}

    fit=least_squares(lambda x:b.column_a_rhs(0,np.r_[x,np.full(41,.5)])[:41],
        np.linspace(.01,.99,41),bounds=(np.full(41,1e-9),np.full(41,1-1e-9)),
        ftol=1e-12,xtol=1e-12,gtol=1e-12,max_nfev=500)
    if not fit.success or np.max(np.abs(fit.fun))>1e-7:
        raise RuntimeError('Column A steady-state solve failed')
    column_state=np.r_[fit.x,np.full(41,.5)]
    td,xd=integrate(lambda t,x:b.column_a_lv_rhs(t,x,[2.70629,3.20629,1.01,.5,1]),column_state,2.)
    entries['column_a']={'states':82,'steady_state_max_derivative':float(np.max(np.abs(fit.fun))),
        'steady_bottom_composition':float(fit.x[0]),'steady_top_composition':float(fit.x[-1]),
        'experiment':'1% feed step, D/B P level control gain 10/min, 2 min'}
    np.savetxt(out/'column_a_steady_state.csv',column_state[:,None],delimiter=',',header='state',comments='')

    aero=b.RotorMap(ROOT/'benchmarks/data/Cp_Ct_Cq.NREL5MW.txt')
    wind_state=np.array([0,0,0,0,0,0,1.2,1.2,0.])
    tw,xw=integrate(lambda t,x:b.wind_rhs(t,x,[11.4,3e6,0.],aero),wind_state,2.)
    entries['wind_reduced']={'states':9,'rotor_map_sha256':aero.sha256,
        'map_variant':'ROSCO table 2022-01-13, not identified as 2014 benchmark map',
        'final_rotor_speed_rad_s':float(xw[-1,6]),'duration_s':2.}
    entries.update(external_status())
    entries['throttle']={'status':'LocalARX implementation tested on a synthetic regression case; original measurements absent'}
    entries['repositories']={'status':'dataset register and strict CSV importer supplied; see DATASETS.md'}
    result['implementation_sha256']=hashlib.sha256((ROOT/'python/intelligent_control/benchmarks.py').read_bytes()).hexdigest()
    (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(13,7.2),constrained_layout=True)
    axes[0,0].plot(tp,xp[:,0]); axes[0,0].set(title='Pendulum: local open-loop instability',xlabel='Time (s)',ylabel='Angle (rad)')
    axes[0,1].plot(tt,xt,label=['h1','h2','h3']); axes[0,1].set(title='Three tanks: closed nominal drains',xlabel='Time (s)',ylabel='Level (m)'); axes[0,1].legend()
    axes[0,2].plot(np.arange(81)*.5,bio,label=['Biomass','Conversion']); axes[0,2].set(title='Bioreactor: sampled Euler model',xlabel='Dimensionless time',ylabel='Dimensionless state'); axes[0,2].legend()
    axes[1,0].plot(tc*60,xc[:,2],label='Reactor'); axes[1,0].plot(tc*60,xc[:,3],label='Coolant'); axes[1,0].set(title='CSTR: rounded SP1 nominal hold',xlabel='Time (min)',ylabel='Temperature (°C)'); axes[1,0].legend()
    axes[1,1].plot(td,xd[:,0]-xd[0,0],label='Bottom'); axes[1,1].plot(td,xd[:,40]-xd[0,40],label='Top'); axes[1,1].set(title='Column A: 1% feed step with level loops',xlabel='Time (min)',ylabel='Composition change'); axes[1,1].legend()
    axes[1,2].plot(tw,xw[:,6],label='Rotor'); axes[1,2].plot(tw,xw[:,7],label='Generator, low-speed side'); axes[1,2].set(title='Reduced wind model: later ROSCO map',xlabel='Time (s)',ylabel='Angular speed (rad/s)'); axes[1,2].legend()
    fig.suptitle('Reproducible model checks — synthetic short experiments',fontsize=16)
    fig.savefig(out/'benchmark_overview.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'output':'benchmarks/results','experiments':len(entries),'column_residual':float(np.max(np.abs(fit.fun))),'tank_volume_residual':float(volume_error)},indent=2))
    return result


if __name__=='__main__': main()
