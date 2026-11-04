"""Nine reproducible laboratories using a shared, explicitly hypothetical tank."""
from pathlib import Path
import json
import time
import numpy as np
from scipy.linalg import expm
from .methods import (Tank, PID, imc_pi, fit_arx, arx_rollout, identification_metrics,
    control_metrics, LinearMPC, FuzzyPI, FuzzyPID, diagnose, train_perceptron,
    MLP, RBF, fit_som, genetic_optimize, fuzzy_inference)

TITLES = {
 1:'Modeling, identification and simulation',
 2:'Feedback, stability and IMC tuning',
 3:'Multiloop, feedforward and cascade structures',
 4:'Constrained model predictive control',
 5:'Expert supervision and fuzzy control',
 6:'Neural identification and control',
 7:'Evolutionary controller tuning',
 8:'Integrated validation and robustness',
 9:'Markov chains and hidden-state diagnosis'}
SLUGS = {1:'01-modeling-identification',2:'02-feedback-imc',3:'03-control-structures',
         4:'04-model-predictive-control',5:'05-expert-fuzzy-control',
         6:'06-neural-identification-control',7:'07-evolutionary-tuning',
         8:'08-integrated-validation',9:'09-markov-hidden-state-diagnosis'}


def scenario(dt=.2, duration=80.):
    t=np.arange(0,duration+dt/2,dt)
    r=np.where(t<10,.35,np.where(t<55,.65,.45))
    d=np.where(t>=45,.08,0.)
    return t,r,d


def simulate(controller, tank=None, dt=.2, duration=80., feedforward=False,
             seed=42, noise=0.):
    tank=Tank() if tank is None else tank
    t,r,d=scenario(dt,duration);rng=np.random.default_rng(seed)
    y=np.empty(len(t));u=np.empty(len(t));y[0]=.35
    for k in range(len(t)-1):
        observed=y[k]+noise*rng.normal()
        # Apply feedforward before PID saturation so antiwindup sees the true command.
        raw=controller(r[k],observed,d[k],offset=-d[k]) if feedforward else controller(r[k],observed,d[k])
        u[k]=np.clip(raw,0,1)
        y[k+1]=tank.step(y[k],u[k],dt,d[k])
    u[-1]=u[-2]
    return dict(t=t,reference=r,disturbance=d,output=y,control=u,
                metrics=control_metrics(t,r,y,u))


def unit1():
    tank=Tank();dt=.5;n=601;rng=np.random.default_rng(21)
    u=np.repeat(rng.uniform(.1,.9,61),10)[:n]
    y=np.empty(n);y[0]=.35
    for k in range(n-1):y[k+1]=tank.step(y[k],u[k],dt)
    measured=y+rng.normal(0,.002,n)
    theta=fit_arx(u,measured)
    # New excitation and fresh trajectory; no random split of adjacent samples.
    ut=np.repeat(np.random.default_rng(73).uniform(.05,.95,61),10)[:n]
    yt=np.empty(n);yt[0]=.6
    for k in range(n-1):yt[k+1]=tank.step(yt[k],ut[k],dt)
    predicted=arx_rollout(theta,ut,yt[0])
    one_step=theta[0]*yt[:-1]+theta[1]*ut[:-1]+theta[2]
    tau=-dt/np.log(theta[0]);gain=theta[1]/(1-theta[0])
    analytic=1-np.exp(-np.arange(n)*dt/tank.tau)
    numerical=np.empty(n);numerical[0]=0
    for k in range(n-1):numerical[k+1]=tank.step(numerical[k],1.,dt)
    return dict(summary={'arx_coefficients':theta.tolist(),'estimated_tau_min':tau,
        'estimated_gain':gain,'free_run':identification_metrics(yt,predicted),
        'one_step':identification_metrics(yt[1:],one_step),
        'analytic_max_error':float(np.max(abs(analytic-numerical))),
        'split':'Independent excitation trajectories, seeds 21 and 73; noise in training only'},
        traces={'held_out':{'t':np.arange(n)*dt,'reference':yt,'output':predicted,'control':ut}},
        extra={'training_input':u,'training_output':measured})


def unit2():
    traces={};summary={}
    for lam in (2.,5.,12.):
        kp,ki=imc_pi(1,10,lam=lam)
        result=simulate(PID(kp,ki));traces[f'IMC lambda={lam:g}']=result
        # For G=1/(10s+1), PI characteristic 10s²+(1+Kp)s+Ki.
        poles=np.roots([10,1+kp,ki])
        summary[f'lambda_{lam:g}']={'kp':kp,'ki':ki,'poles':[[p.real,p.imag] for p in poles],
                                    **result['metrics']}
    result=simulate(PID(2,.2,.3));traces['filtered PID']=result
    summary['filtered_PID']=result['metrics']
    return dict(summary=summary,traces=traces)


def unit3():
    t,r,d=scenario();dt=t[1]-t[0];traces={};summary={}
    traces['feedback']=simulate(PID(2,.2))
    traces['measured feedforward']=simulate(PID(2,.2),feedforward=True)
    # Fast flow actuator: tau_a*qdot = valve + load - q. Cascade measures q.
    for cascade in (False,True):
        y=np.empty(len(t));q=np.empty(len(t));u=np.zeros(len(t));y[0]=q[0]=.35
        outer=PID(2,.2,dt=dt);inner=PID(2,2,dt=dt)
        for k in range(len(t)-1):
            desired=outer(r[k],y[k]);u[k]=inner(desired,q[k]) if cascade else desired
            load=-.15 if 35<=t[k]<60 else 0.
            q[k+1]=q[k]+dt/1.5*(u[k]+load-q[k])
            y[k+1]=Tank().step(y[k],q[k],dt)
        u[-1]=u[-2];label='cascade' if cascade else 'single loop with actuator'
        traces[label]=dict(t=t,reference=r,output=y,control=u)
        summary[label]=control_metrics(t,r,y,u)
    # Interacting two-output first-order plant. Static decoupler preserves steady gains.
    gain=np.array([[1.,.4],[.3,1.2]]);rga=gain*np.linalg.inv(gain).T
    a=np.diag(np.exp(-dt/np.array([10.,15.])))
    b=(np.eye(2)-a)@gain; req=np.array([.6,.65]);x0=gain@np.array([.3,.3])
    for decouple in (False,True):
        y=np.zeros((len(t),2));y[0]=x0;u=np.zeros_like(y)
        loops=[PID(1.5,.15,bias=x0[0] if decouple else .3),
               PID(1.5,.1,bias=x0[1] if decouple else .3)]
        for k in range(len(t)-1):
            rr=x0 if t[k]<10 else req
            v=np.array([loops[j](rr[j],y[k,j]) for j in range(2)])
            u[k]=np.clip(np.linalg.solve(gain,v) if decouple else v,0,1)
            y[k+1]=a@y[k]+b@u[k]
        u[-1]=u[-2];label='decoupled' if decouple else 'decentralized'
        for j in range(2):traces[f'{label} output {j+1}']=dict(t=t,reference=np.where(t<10,x0[j],req[j]),output=y[:,j],control=u[:,j])
        summary[label]={'final_output':y[-1].tolist(),'max_actuator':float(u.max())}
    for label in ('feedback','measured feedforward'):summary[label]=traces[label]['metrics']
    summary['steady_gain_matrix']=gain.tolist();summary['relative_gain_array']=rga.tolist()
    summary['comparison_scope']='Cascade pair uses an actuator-load disturbance; feedforward pair uses an inlet-concentration disturbance.'
    return dict(summary=summary,traces=traces)


def unit4():
    dt=.2;a=np.exp(-dt/10)
    mpc=LinearMPC([[a]],[[1-a]],horizon=20,control_horizon=5,move_weight=.05,max_move=.05)
    trace=simulate(mpc)
    # A second, genuinely MIMO constrained prediction problem.
    ad=np.diag([.96,.97]);bd=(np.eye(2)-ad)@np.array([[1,.25],[.2,1.]])
    coupled=LinearMPC(ad,bd,horizon=15,control_horizon=4,move_weight=.08,
                      max_move=.06,initial=.3,output_bounds=(0.,.95))
    x=np.array([.375,.36]);ys=[x.copy()];us=[]
    for _ in range(80):
        u=coupled([.65,.55],x);x=ad@x+bd@u;ys.append(x.copy());us.append(u)
    ys=np.array(ys);us=np.array(us)
    traces={'constrained MPC':trace,'PI reference':simulate(PID(2,.2))}
    for j in range(2):
        traces[f'MIMO output {j+1}']=dict(t=np.arange(81),reference=np.full(81,[.65,.55][j]),
                                       output=ys[:,j],control=np.r_[us[:,j],us[-1,j]])
    return dict(summary={'siso':trace['metrics'],'solver_failures':mpc.failures,
        'mimo_solver_failures':coupled.failures,'max_move':float(np.max(abs(np.diff(np.r_[.35,trace['control']])))),
        'mimo_final_output':ys[-1].tolist(),'mimo_max_output':float(ys.max()),
        'note':'Full state is measured; the additive inlet disturbance is measured for prediction. No state estimator is assumed.'},traces=traces)


def unit5():
    controllers={'PI':PID(2,.2),'Mamdani fuzzy PI':FuzzyPI(kind='mamdani'),
                 'Sugeno fuzzy PI':FuzzyPI(kind='sugeno'),'fuzzy gain PID':FuzzyPID(2,.2)}
    traces={name:simulate(controller) for name,controller in controllers.items()}
    rules=[diagnose(.95,.5,.6),diagnose(.4,1.,.7),diagnose(.5,.5,.5,residual=.12),
           diagnose(float('nan'),.5,.5,False),diagnose(.5,.5,.5)]
    grid=np.linspace(-1,1,31)
    surface=np.array([[fuzzy_inference(e,de) for e in grid] for de in grid])
    return dict(summary={'controllers':{k:v['metrics'] for k,v in traces.items()},'diagnostic_cases':rules,
        'rule_policy':'Sensor validity has priority over process alarms; thresholds are educational and require plant-specific review.'},
        traces=traces,extra={'fuzzy_grid':grid,'fuzzy_surface':surface})


def nonlinear_step(y,u,dt=1.):
    """Illustrative state-dependent flushing rate; not an article benchmark."""
    return u+(y-u)*np.exp(-dt*(1+.6*y)/10)


def unit6():
    rng=np.random.default_rng(42);x=rng.uniform(.05,.95,(900,2))
    target=nonlinear_step(x[:,0],x[:,1]);train=x[:650];yt=target[:650]
    validation=x[650:];yvalidation=target[650:]
    mlp=MLP().fit(train,yt);rbf=RBF().fit(train,yt,centers=25)
    scores={name:identification_metrics(yvalidation,model.predict(validation))
            for name,model in [('MLP',mlp),('RBF',rbf)]}
    t=np.arange(201.);inputs=.5+.3*np.sin(t/9)+.1*np.sin(t/2.7)
    y=np.empty(len(t));y[0]=.3;yp={name:np.empty(len(t)) for name in ('MLP','RBF')}
    for p in yp.values():p[0]=y[0]
    for k in range(len(t)-1):
        y[k+1]=nonlinear_step(y[k],inputs[k])
        for name,model in [('MLP',mlp),('RBF',rbf)]:yp[name][k+1]=model.predict([[yp[name][k],inputs[k]]])[0]
    traces={name+' free run':dict(t=t,reference=y,output=yp[name],control=inputs) for name in yp}
    for name in yp:scores[name]['free_run_rmse']=identification_metrics(y,yp[name])['rmse']
    # Model-based one-step control, all candidate actions evaluated through learned model.
    r=np.where(t<15,.3,np.where(t<120,.7,.45));yc=np.empty(len(t));uc=np.empty(len(t));yc[0]=.3
    candidates=np.linspace(0,1,101);previous=.3
    for k in range(len(t)-1):
        pred=mlp.predict(np.column_stack([np.full(len(candidates),yc[k]),candidates]))
        objective=(pred-r[k])**2+.0002*(candidates-previous)**2
        uc[k]=candidates[np.argmin(objective)];previous=uc[k]
        yc[k+1]=nonlinear_step(yc[k],uc[k])
    uc[-1]=uc[-2];traces['neural model-based control']=dict(t=t,reference=r,output=yc,control=uc)
    labels=np.where(train[:,0]+train[:,1]>1,1,-1);w=train_perceptron(train,labels)
    prediction=np.where(np.column_stack([validation,np.ones(len(validation))])@w>=0,1,-1)
    _,clusters,qe=fit_som(train)
    ood=np.array([[1.2,.2],[-.1,.8],[.5,1.3]])
    return dict(summary={'models':scores,'training_samples':650,'validation_samples':250,
        'perceptron_accuracy':float(np.mean(prediction==np.where(validation.sum(1)>1,1,-1))),
        'som_quantization_error':qe,'som_occupied_nodes':int(len(np.unique(clusters))),
        'neural_control':control_metrics(t,r,yc,uc),'out_of_domain_rmse':identification_metrics(nonlinear_step(ood[:,0],ood[:,1]),mlp.predict(ood))['rmse'],
        'validation_protocol':'Train normalization on 650 independent state/input transitions, validate on 250 untouched transitions, then test free-run trajectory. Hyperparameters fixed before validation.'},
        traces=traces,extra={'mlp_loss':np.asarray(mlp.loss)})


def tuning_objective(parameters,tau=10.):
    trace=simulate(PID(*parameters,dt=.5),Tank(100,100/tau),dt=.5)
    m=trace['metrics']
    return m['iae']+.03*m['total_variation']


def unit7():
    bounds=[(.2,6.),(.01,.7)]
    results={encoding:genetic_optimize(tuning_objective,bounds,population=18,generations=16,
                  encoding=encoding,seed=42) for encoding in ('real','binary')}
    traces={'IMC reference':simulate(PID(2,.2))}
    for name,result in results.items():
        traces[name+' GA']=simulate(PID(*result['parameters']))
        result['held_out_tau_14']=simulate(PID(*result['parameters']),Tank(140,10))['metrics']
    # MIMO MPC penalty tuning: identical initial states/reference and fixed solve count.
    # A small search makes solver cost explicit, not a claim of globally optimal weights.
    def mpc_cost(parameters):
        rho=parameters[0];ad=np.diag([.9,.92]);bd=(np.eye(2)-ad)@np.array([[1.,.3],[.2,1.]])
        c=LinearMPC(ad,bd,horizon=6,control_horizon=2,move_weight=rho,max_move=.12,initial=.3)
        x=np.array([.39,.36]);cost=0.;previous=np.array([.3,.3])
        for _ in range(12):
            u=c([.65,.6],x);x=ad@x+bd@u
            cost+=np.sum((x-[.65,.6])**2)+.02*np.sum((u-previous)**2);previous=u
        return float(cost+10*c.failures)
    results['mimo_mpc_weight']=genetic_optimize(mpc_cost,[(.001,.5)],population=4,generations=2,seed=7)
    return dict(summary=results,traces=traces,
                extra={name+'_best_fitness':np.array(result['history']) for name,result in results.items()})


def unit8():
    traces={};rows=[]
    for tau in (7.,10.,14.):
        for name,factory in [('PI',lambda:PID(2,.2)),('fuzzy PID',lambda:FuzzyPID(2,.2)),
                             ('feedforward PI',lambda:PID(2,.2))]:
            # Same sensor-noise realization and disturbance schedule for each method.
            trace=simulate(factory(),Tank(tau*10,10),seed=2026,noise=.003,
                           feedforward=name=='feedforward PI')
            traces[f'{name}, tau={tau:g}']=trace
            rows.append({'method':name,'tau_min':tau,**trace['metrics']})
    return dict(summary={'scenarios':rows,'seed':2026,'noise_std':.003,
         'scope':'Matched deterministic uncertainty scenarios, not experimental validation or a universal ranking. Feedforward receives measured disturbance; PI and fuzzy PID do not.'},traces=traces)


def unit9():
    from .markov_lab import run_markov_experiment
    return run_markov_experiment()


def save_result(unit,result,outdir):
    if unit==9:
        from .markov_lab import save_markov_result
        return save_markov_result(result,outdir)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    (outdir/'metrics.json').write_text(json.dumps(result['summary'],indent=2,allow_nan=False)+'\n',encoding='utf-8')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    traces=result['traces']
    if unit==3:
        groups=[('Inlet disturbance',[k for k in traces if k in ('feedback','measured feedforward')]),
                ('Actuator disturbance',[k for k in traces if k in ('cascade','single loop with actuator')]),
                ('Coupled process',[k for k in traces if 'output' in k])]
    elif unit==4:
        groups=[('Single-input process',[k for k in traces if not k.startswith('MIMO')]),
                ('Two-input process',[k for k in traces if k.startswith('MIMO')])]
    elif unit==6:
        groups=[('Independent free-run validation',[k for k in traces if 'free run' in k]),
                ('Control with learned model',[k for k in traces if 'control' in k])]
    elif unit==8:
        groups=[(f'Residence time {tau} min',[k for k in traces if k.endswith(f'tau={tau}')]) for tau in (7,10,14)]
    else:groups=[(TITLES[unit],list(traces))]
    fig,axes=plt.subplots(2,len(groups),figsize=(7*len(groups) if len(groups)>1 else 10,7),
                          squeeze=False,sharex='col',layout='constrained')
    for col,(title,labels) in enumerate(groups):
        references=[]
        for index,label in enumerate(labels):
            tr=traces[label];color=plt.cm.tab10(index)
            axes[0,col].plot(tr['t'],tr['output'],label=label,color=color,lw=1.6)
            axes[1,col].plot(tr['t'],tr['control'],color=color,lw=1.2)
            if not any(np.array_equal(tr['reference'],r) for r in references):
                axes[0,col].plot(tr['t'],tr['reference'],'--',color=color,alpha=.6,lw=1,
                                 label='target' if len(labels)==1 else f'target {len(references)+1}')
                references.append(tr['reference'])
        axes[0,col].set(ylabel='Concentration / normalized output',title=title)
        axes[1,col].set(ylabel='Input / blend fraction',xlabel='Sample index' if unit==4 and col==1 else 'Time [min]')
        axes[0,col].legend(fontsize=8,ncol=1 if len(groups)>1 else 2)
    for label,tr in traces.items():
        np.savetxt(outdir/(label.replace(' ','_').replace(',','').replace('=','-')+'.csv'),
                   np.column_stack([tr['t'],tr['reference'],tr['output'],tr['control']]),
                   delimiter=',',header='time,reference,output,control',comments='')
    for ax in axes.ravel():ax.grid(alpha=.2)
    fig.suptitle(f'Unit {unit:02d} | {TITLES[unit]}',fontsize=15)
    fig.savefig(outdir/'comparison.png',dpi=160);fig.savefig(outdir/'comparison.svg');plt.close(fig)
    for name,data in result.get('extra',{}).items():np.savetxt(outdir/(name+'.csv'),np.atleast_1d(data),delimiter=',')
    return outdir


def run_unit(unit,outdir=None):
    if unit not in TITLES:raise ValueError(f'Unit must be one of {sorted(TITLES)}')
    start=time.perf_counter();result=globals()[f'unit{unit}']()
    result['summary']['elapsed_seconds']=time.perf_counter()-start
    if outdir is not None:save_result(unit,result,outdir)
    return result
