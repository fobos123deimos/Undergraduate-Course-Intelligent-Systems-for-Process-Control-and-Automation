"""Nine learning stages applied to the survey's mathematical models.

The first stage integrates the declared nonlinear model with two independent,
small excitation records. Later scalar control exercises use a fitted ARX
predictor, **not the nonlinear apparatus**. This deliberate reduction makes
model error, saturation and information limits visible across very different
plants. The accompanying illustrated case pages retain each physical unit and
the source qualifications for pneumatic, hydrostatic and wind variants.

`generate_records` creates synthetic records. `study` fits on the first record
only and evaluates the second. `closed_loop` runs the explicitly labelled
scalar surrogate; `sensor_diagnosis` injects new synthetic sensor faults into a
held-out record. No function downloads or reruns external simulators.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize
from . import benchmarks as b, methods as m, pneumatic_physical as p
from . import hydrostatic_si as h, wind_control as w
from .markov import CategoricalHMM, fit_supervised


def case_catalog():
    """Return case titles, selected channels, units and interpretation limits.

    Each tuple is ``(title, paper section, output, output unit, input,
    input unit, time unit, qualification)``. Two artificial systems share
    section 3.1; the three external plant families and data-only sections are
    handled separately by the reporting command.
    """
    return {
        'artificial_siso': ('Artificial SISO', '3.1 / Eq. 30', 'y', 'dimensionless', 'u', 'dimensionless', 'sample', 'Exact recurrence; short independent excitation records.'),
        'artificial_mimo': ('Artificial MIMO', '3.1 / Eq. 31', 'y1', 'dimensionless', 'u1', 'dimensionless', 'sample', 'Both outputs retained; u2 is an independently excited omitted input in the scalar fit.'),
        'pendulum': ('Inverted pendulum', '3.3 / Eq. 32', 'angle', 'rad', 'force', 'N', 's', 'Short upright-window experiment; cart Coulomb friction explicitly set to zero, as in the existing local study.'),
        'pneumatic': ('Pneumatic actuator', '3.5', 'position', 'm', 'valve command', 'V', 's', 'Separate six-state mass/energy interpretation; assumed valve closure, not apparatus calibration.'),
        'hydrostatic': ('Hydrostatic drive', '3.6', 'motor speed', 'rad/s', 'pump command', 'normalized', 's', 'Separate SI model: displacement per revolution and effective capacitance; no electrical calibration.'),
        'three_tank': ('Three tanks', '3.7 / Eq. 36', 'h1', 'm', 'q1', 'm3/s', 's', 'Nominal drains remain closed; positive pumping has no steady equilibrium. Surrogate tracking is not physical tank regulation.'),
        'bioreactor': ('Bioreactor', '3.8 / Eq. 37', 'biomass', 'dimensionless', 'dilution', 'dimensionless', 'dimensionless', 'Paper sampled model: 50 Euler substeps of 0.01 per 0.5 hold.'),
        'cstr': ('CSTR', '3.9 / Eqs. 39-43', 'reactor temperature', 'deg C', 'cooling', 'MJ/h', 'h', 'Rounded SP1 initial state; dilution held at 8.256/h; short excitation around -6.239 MJ/h.'),
        'column_a': ('Column A', '3.10', 'top composition', 'mole fraction', 'reflux', 'kmol/min', 'min', '82-state LV model; separate end-vessel P level loops, gain 10/min; boilup held fixed.'),
        'wind_reduced': ('Reduced wind turbine', '3.12 and 4.2', 'rotor speed', 'rad/s', 'generator torque', 'N m', 's', 'Eight regulation coordinates of the nine-state plant, constant wind 14 m/s, later ROSCO map; no historical Table 12 claim.'),
    }


def _excitation(t, duration, seed):
    rng = np.random.default_rng(seed)
    phases = rng.uniform(-np.pi, np.pi, 3)
    z = np.asarray(t) / duration
    return sum(weight*np.sin(2*np.pi*cycles*z+phase)
               for weight, cycles, phase in zip([.5,.3,.2],[2,5,9],phases))


def generate_records(case, root, *, samples=301):
    """Create independent training/test records from a declared model.

    ``root`` is the repository directory containing the documented rotor map
    and Column A equilibrium. Return two dictionaries with ``time``, ``input``,
    scalar ``output``, full ``states`` and fixed ``seed``. Continuous inputs
    are smooth multisines, not zero-order holds. ODEs use Radau, relative
    tolerance 1e-8 and absolute tolerance 1e-10. No output clipping is used.
    Discrete artificial and bioreactor models retain their own update rules.
    """
    from pathlib import Path
    root = Path(root)
    if case not in case_catalog() or samples < 30:
        raise ValueError('Known case and at least 30 samples required')
    records = []
    for seed in (1401, 2401):
        if case.startswith('artificial'):
            kind = 'siso' if case.endswith('siso') else 'mimo'
            u, x = b.artificial_data(samples-1, kind, 'train', seed=seed)
            u = np.vstack([u, u[-1]])
            records.append(dict(time=np.arange(samples), input=u[:,0], all_inputs=u, output=x[:,0], states=x, seed=seed))
            continue
        if case == 'bioreactor':
            end = (samples-1)*.5; t = np.linspace(0,end,samples)
            u = .769 + .008*_excitation(t,end,seed)
            c2 = brentq(lambda s:(1-s)*np.exp(s/.4)-.769,.8,1)
            x = np.empty((samples,2)); x[0] = [c2*(1.02-c2)/1.02,c2]
            for k in range(samples-1): x[k+1] = b.bioreactor_sample(x[k],u[k])
            records.append(dict(time=t,input=u,output=x[:,0],states=x,seed=seed)); continue
        if case == 'pendulum':
            end, base, amplitude, output = .6, 0., .2, 0
            x0 = np.array([.01,0,0,0]); par = b.PendulumParameters(cart_coulomb=0.)
            rhs = lambda t,x,u:b.pendulum_rhs(t,x,u,par)
        elif case == 'pneumatic':
            end, base, amplitude, output = 1., 0., .12, 0
            x0 = p.equilibrium(); rhs = lambda t,x,u:p.rhs(t,x,u)
        elif case == 'hydrostatic':
            end, base, amplitude, output = 6., .25, .012, 3
            par = h.table5_interpretation(displacement_basis='per_revolution',capacitance_basis='effective')
            dm=par.motor_m3_per_rad*.8; eta=par.gearbox_efficiency*par.motor_efficiency
            q=par.pump_m3_per_rad*.25*180
            omega=(q-par.leakage_m3_per_s_pa*5000/(par.ratio*eta*dm))/(dm+par.leakage_m3_per_s_pa*par.motor_damping/(eta*dm))
            pressure=(par.motor_damping*omega+5000/par.ratio)/(eta*dm)
            x0=np.array([.25,.8,pressure,omega])
            rhs=lambda t,x,u:h.hydrostatic_si_rhs(x,[u,.8],180.,5000.,par)
        elif case == 'three_tank':
            end, base, amplitude, output = 30., 2e-5, .5e-5, 0
            x0=np.array([.3,.2,.25]); rhs=lambda t,x,u:b.three_tank_rhs(t,x,[u,1e-5])
        elif case == 'cstr':
            end, base, amplitude, output = .2, -6.239, .2, 2
            x0=b.CSTR_SP1.copy(); rhs=lambda t,x,u:b.cstr_rhs(t,x,[8.256,u])
        elif case == 'column_a':
            end, base, amplitude, output = 8., 2.70629, .025, 40
            x0=np.loadtxt(root/'benchmarks/results/column_a_steady_state.csv',delimiter=',',skiprows=1)
            rhs=lambda t,x,u:b.column_a_lv_rhs(t,x,[u,3.20629,1.,.5,1.])
        elif case == 'wind_reduced':
            end, amplitude, output = 12., 1e5, 5
            aero=b.RotorMap(root/'benchmarks/data/Cp_Ct_Cq.NREL5MW.txt')
            x0,command=w.equilibrium(14.,aero); base=command[0]
            rhs=lambda t,x,u:w.regulation_rhs(x,[u,command[1]],14.,aero)
        t=np.linspace(0,end,samples)
        signal=lambda time:base+amplitude*_excitation(time,end,seed)
        sol=solve_ivp(lambda time,x:rhs(time,x,signal(time)),(0,end),x0,t_eval=t,
                      method='Radau',rtol=1e-8,atol=1e-10,max_step=end/100)
        if not sol.success or not np.isfinite(sol.y).all(): raise RuntimeError(f'{case}: {sol.message}')
        records.append(dict(time=t,input=signal(t),output=sol.y[output],states=sol.y.T,seed=seed))
    return records


def fit_record(record):
    """Fit a normalized scalar ARX using training statistics only.

    Return coefficients ``[a,b,c]`` of ``z_next=a*z+b*v+c`` and the four
    means/scales needed to recover physical output and input coordinates.
    The fit is an empirical first-order reduction, not a physical linearization.
    """
    y,u=np.asarray(record['output']),np.asarray(record['input'])
    ym,um=float(y.mean()),float(u.mean()); ys,us=float(y.std()),float(u.std())
    if min(ys,us)<1e-12: raise ValueError('Output/input excitation is too small')
    z,v=(y-ym)/ys,(u-um)/us
    theta=m.fit_arx(v,z)
    return dict(theta=theta,output_mean=ym,output_scale=ys,input_mean=um,input_scale=us)


def _normalized(record,fit):
    return ((record['output']-fit['output_mean'])/fit['output_scale'],
            (record['input']-fit['input_mean'])/fit['input_scale'])


def closed_loop(theta, *, policy='pi', steps=80, gains=(1.,1.), mismatch=1., scenario='test'):
    """Run a bounded-control exercise on the fitted scalar surrogate only.

    Time is measured in samples, states/inputs in training standard deviations.
    Input bounds are [-2,2]; they are exercise constraints, not equipment limits.
    PI gains place the unsaturated predictor poles at 0.80 and 0.85. The test
    reference changes sign and the disturbance occurs at a different time from
    the tuning scenario. ``mismatch`` scales b without refitting the controller.
    Return traces and metrics; divergence is recorded, never hidden by clipping
    the output. A non-finite/unbounded state stops the trace and marks failure.

    Policies are PI, measured-disturbance feedforward, actuator cascade, fuzzy
    PI and affine constrained MPC. These are new teaching designs, not recovered
    historical controllers. No nonlinear-plant stability claim follows.
    """
    a,beta,c=np.asarray(theta,float)
    if abs(beta)<1e-8: return {'status':'unusable_input_gain','rmse':None}
    kp=(a-.80*.85)/beta*gains[0]; ki=(1-.80)*(1-.85)/beta*gains[1]
    bias=-c/beta; integral=0.; olderror=0.; previous=0.; actuator=0.
    y=0.; rows=[]; failures=0; diverged=False
    for k in range(steps):
        ref=(.35 if k>=8 else 0.) if scenario=='train' else (.3 if 10<=k<45 else -.15 if k>=45 else 0.)
        d=.15 if (steps//2 if scenario=='train' else 55)<=k<steps-8 else 0.
        e=ref-y
        if policy=='mpc':
            def objective(plan):
                pred=y; value=0.; prev=previous
                for j in range(8):
                    action=plan[min(j,2)]; pred=a*pred+beta*action+c
                    value+=(pred-ref)**2+.1*(action-prev)**2; prev=action
                return value
            opt=minimize(objective,np.full(3,previous),method='SLSQP',bounds=[(-2,2)]*3,
                constraints=[{'type':'ineq','fun':lambda z:.4-np.abs(np.diff(np.r_[previous,z]))}],
                options={'maxiter':60,'ftol':1e-8})
            valid=opt.success and np.max(np.abs(np.diff(np.r_[previous,opt.x])))<=.4000001
            u=float(opt.x[0]) if valid else previous; failures+=int(not valid)
        elif policy=='fuzzy':
            u=float(np.clip(previous+np.sign(beta)*.12*m.fuzzy_inference(e,(e-olderror)*4,'sugeno'),-2,2))
        else:
            offset=-d if policy=='feedforward' else 0.
            raw=bias+kp*e+integral+ki*e+offset; u=float(np.clip(raw,-2,2))
            if raw==u or (raw-u)*ki*e<0: integral+=ki*e
            if policy=='cascade':
                command=float(np.clip(u+2*(u-actuator),-2,2))
                actuator=.7*actuator+.3*command; u=actuator
        rows.append([k,ref,y,u,d]); previous=u; olderror=e
        y=a*y+beta*mismatch*(u+d)+c
        if not np.isfinite(y) or abs(y)>1e6:
            diverged=True
            break
    trace=np.asarray(rows)
    return dict(status='diverged' if diverged else 'completed',trace=trace,
                terminal_state=float(y) if np.isfinite(y) else None,
                rmse=float(np.sqrt(np.mean((trace[:,1]-trace[:,2])**2))),
                movement=float(np.abs(np.diff(trace[:,3])).sum()),
                max_input=float(np.abs(trace[:,3]).max()),solver_failures=failures,
                nominal_poles=np.linalg.eigvals([[a-beta*(kp+ki),beta],[-ki,1.]]).tolist())


def sensor_diagnosis(clean, scale, *, seed=3401):
    """Inject independent synthetic sensor bias and compare HMM decisions.

    ``clean`` is a held-out output record. A *known clean reference* is provided
    to the residual calculation, an information advantage that excludes a field
    fault-detection claim. Calibration uses 20 independent 150-sample records;
    no evaluation labels select emissions, thresholds or state names. Return
    accuracy, stationary assumptions and plotted states/causal probabilities.
    """
    if scale<=0: raise ValueError('Positive physical output scale required')
    truth=CategoricalHMM([1.,0.,0.],[[.97,.025,.005],[.04,.94,.02],[.03,.02,.95]],
                         [[.94,.05,.01],[.08,.86,.06],[.01,.09,.9]])
    train=[truth.sample(150,seed=4000+j) for j in range(20)]
    model=fit_supervised([r[0] for r in train],[r[1] for r in train],3,3,pseudocount=1.)
    states,symbols=truth.sample(len(clean),seed=seed)
    # Symbol-specific bias plus bounded jitter guarantees the declared cutpoints.
    residual=np.array([0.,1.,2.])[symbols]+np.random.default_rng(seed+1).uniform(-.2,.2,len(clean))
    noisy=np.asarray(clean)+scale*residual
    observed=np.digitize((noisy-clean)/scale,[.5,1.5])
    posterior=model.filter(observed)['filtered']; smooth=model.smooth(observed)['smoothed']
    path=model.viterbi(observed)['states']; instant=model.emission[:,observed].argmax(0)
    return dict(filtered_accuracy=float(np.mean(posterior.argmax(1)==states)),
                instantaneous_accuracy=float(np.mean(instant==states)),
                smoothed_accuracy=float(np.mean(smooth.argmax(1)==states)),
                viterbi_accuracy=float(np.mean(path==states)),
                traces=np.c_[states,observed,posterior],noise_scale=float(scale),
                calibration_sequences=20,test_seed=seed,
                true_state_support=np.bincount(states,minlength=3).tolist())


def study(records):
    """Execute all nine learning stages on a native model's two records.

    Stage 1: ARX one-step/free-run; 2: PI predictor control; 3: feedforward and
    actuator cascade; 4: constrained predictor MPC; 5: fuzzy PI; 6: MLP/RBF
    held-out prediction; 7: real-coded GA tuning of PI on a separate reference;
    8: paired +/-20% input-gain mismatch; 9: independent sensor Markov/HMM.
    All identification and neural normalization uses the training record only.
    Scores use normalized coordinates; physical conversion is saved in ``fit``.
    """
    train,test=records; fit=fit_record(train); z,u=_normalized(train,fit); zv,uv=_normalized(test,fit)
    theta=fit['theta']; one=theta[0]*zv[:-1]+theta[1]*uv[:-1]+theta[2]
    free=m.arx_rollout(theta,uv,zv[0])
    features=np.c_[z[:-1],u[:-1]]; held=np.c_[zv[:-1],uv[:-1]]
    mlp=m.MLP(hidden=10,seed=19).fit(features,z[1:],epochs=500)
    rbf=m.RBF().fit(features,z[1:],centers=16,seed=19,ridge=1e-4)
    neural=np.c_[zv[1:],one,mlp.predict(held),rbf.predict(held)]
    loops={name:closed_loop(theta,policy=name) for name in ('pi','feedforward','cascade','mpc','fuzzy')}
    def objective(g):
        r=closed_loop(theta,gains=g,scenario='train')
        return 1e9 if r['status']!='completed' else r['rmse']+.003*r['movement']
    ga=m.genetic_optimize(objective,[(.4,1.6),(.4,1.6)],population=10,generations=8,seed=19)
    loops['genetic_pi']=closed_loop(theta,gains=ga['parameters'])
    robustness={str(g):{name:closed_loop(theta,policy=name,mismatch=g) for name in ('pi','mpc','fuzzy')}
                for g in (.8,1.,1.2)}
    diagnosis=sensor_diagnosis(test['output'],.2*fit['output_scale'])
    return dict(fit=fit,identification=dict(one_step_rmse=float(np.sqrt(np.mean((one-zv[1:])**2))),
        free_run_rmse=float(np.sqrt(np.mean((free-zv)**2))),predictor_pole=float(theta[0])),
        prediction=np.c_[test['time'],zv,free],neural=neural,
        neural_rmse=dict(zip(['ARX','MLP','RBF'],np.sqrt(np.mean((neural[:,1:]-neural[:,0,None])**2,axis=0)).tolist())),
        loops=loops,ga=ga,robustness=robustness,diagnosis=diagnosis)
