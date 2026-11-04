"""Build illustrated unit-by-benchmark studies from explicit numerical records."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from intelligent_control import benchmark_learning as learn

UNITS={
1:('Identification and simulation',r'Fit $z_{k+1}=a z_k+b v_k+c$ on an independently excited training record. Compare held-out one-step errors with recursive free-run errors. A good one-step fit can coexist with severe rollout drift. Physical coordinates are recovered with the saved training mean and standard deviation.'),
2:('Feedback and nominal stability',r'Place the two nominal PI predictor poles at $0.80$ and $0.85$: $K_p=(a-0.80\times0.85)/b$ and $K_i=(1-0.80)(1-0.85)/b$. The command includes the current integration increment, $v=K_pe+I+K_ie$, before $I^+=I+K_ie$. Include saturation and conditional integration. These poles refer to the unsaturated scalar predictor; they do not certify the original nonlinear plant.'),
3:('Feedforward and cascade structures',r'Compare ordinary PI with a measured additive-input disturbance cancellation $v_{ff}=-d$. A separate cascade adds a fast first-order actuator and a proportional inner loop. Its plant differs from the no-actuator baseline, so the plot illustrates architecture rather than a fair universal ranking. Multivariable plants are reduced to one channel here; their omitted interactions remain model error.'),
4:('Constrained predictive control',r'Minimize the eight-step prediction error plus $0.1\sum(\Delta v)^2$, using three free moves, $|v|\leq2$ and $|\Delta v|\leq0.4$. Retain the affine term $c$. Each successful solution applies only its first move. A failed solve holds the previous command and is counted. These are normalized exercise bounds, not equipment safety limits.'),
5:('Expert and fuzzy control',r'Apply the nine-rule Sugeno surface to normalized error and its change. The incremental command uses the sign of the fitted input coefficient and is saturated. Interpret severe drift, sustained saturation or predictor error before adjusting rules; fuzzy inference itself supplies no stability certificate.'),
6:('Neural identification',r'Train a ten-hidden-unit tanh MLP and a sixteen-center Gaussian RBF on $[z_k,v_k]\mapsto z_{k+1}$. Statistics and RBF centers use training data only. Compare both with the linear ARX on an untouched second record. This panel is one-step prediction; it is not a recursive neural-control test or a claim that the network resolves omitted states.'),
7:('Evolutionary tuning',r'A real-coded genetic algorithm tunes two PI gain multipliers in $[0.4,1.6]^2$. Ten individuals and eight generations give 90 evaluations, with seed 19. Fitness is training RMSE plus $0.003$ times input movement. The saved validation curve uses a different reference and disturbance time; it is not used to select the gains.'),
8:('Integration and uncertainty',r'Repeat PI, MPC and fuzzy PI on the same reference and disturbance with the surrogate input gain multiplied by $0.8$, $1$ and $1.2$. Keep nominal controllers fixed. The three point scenarios are a sensitivity test, not a probability distribution, confidence interval or nonlinear robustness proof.'),
9:('Markov chains and hidden sensor modes',r'Inject synthetic normal/drift/fault residuals into the held-out physical output and calibrate a categorical HMM on 20 separate records. Compare emission-only decisions, causal filtering, smoothing and Viterbi. A known clean output is available to construct residuals: this is a strong information assumption. Only filtering could enter online supervision; the other two estimates are retrospective.')}
DIAGRAMS={'pendulum':'03-pendulum','pneumatic':'05-pneumatic','hydrostatic':'06-hydrostatic','three_tank':'07-three-tanks','bioreactor':'08-bioreactor','cstr':'09-cstr','column_a':'10-column-a','wind_reduced':'12-wind-turbine'}


def jsonable(value):
    if isinstance(value,np.ndarray): return jsonable(value.tolist())
    if isinstance(value,np.generic): return jsonable(value.item())
    if isinstance(value,complex): return {'real':value.real,'imaginary':value.imag}
    if isinstance(value,dict): return {k:jsonable(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [jsonable(v) for v in value]
    return value


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(jsonable(value),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def computation_hashes():
    sources=list((ROOT/'python/intelligent_control').glob('*.py'))
    sources += [ROOT/'benchmarks/data/Cp_Ct_Cq.NREL5MW.txt',ROOT/'benchmarks/results/column_a_steady_state.csv']
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sources}


def panel(ax,unit,result):
    if unit==1:
        a=result['prediction']; ax.plot(a[:,0],a[:,1],label='Nonlinear record',lw=1.6); ax.plot(a[:,0],a[:,2],label='ARX free-run',lw=1.)
        ax.set_xlabel('Physical time (case unit)'); ax.set_ylabel('Training-standardized output')
    elif unit in (2,3,4,5,7):
        names={2:['pi'],3:['pi','feedforward','cascade'],4:['mpc'],5:['pi','fuzzy'],7:['pi','genetic_pi']}[unit]
        for name in names:
            r=result['loops'][name]
            if 'trace' in r:
                a=r['trace']; ax.plot(a[:,0],a[:,2],label=name,lw=1.3)
        if 'trace' in result['loops']['pi']:
            a=result['loops']['pi']['trace']; ax.plot(a[:,0],a[:,1],'k--',label='Reference',lw=1)
        ax.set_xlabel('Surrogate sample'); ax.set_ylabel('Normalized predictor output')
    elif unit==6:
        a=result['neural']; ax.plot(a[:,0],color='#263238',label='Held-out target',lw=1.6)
        for j,label in enumerate(['ARX','MLP','RBF'],1): ax.plot(a[:,j],label=label,lw=1.)
        ax.set_xlabel('Held-out sample'); ax.set_ylabel('One-step normalized output')
    elif unit==8:
        for name in ('pi','mpc','fuzzy'):
            ax.plot([.8,1,1.2],[result['robustness'][str(g)][name].get('rmse',np.nan) for g in (.8,1.,1.2)],'o-',label=name)
        ax.set_xlabel('Input-gain multiplier'); ax.set_ylabel('Surrogate tracking RMSE')
    else:
        a=result['diagnosis']['traces']; ax.step(np.arange(len(a)),a[:,0]/2,label='True state / 2',color='#263238',lw=1)
        ax.plot(a[:,4],label='Causal P(fault)',color='#bb4c39',lw=1.2); ax.set_xlabel('Held-out sample'); ax.set_ylabel('Synthetic mode / probability'); ax.set_ylim(-.08,1.08)
    ax.grid(alpha=.18); ax.legend(fontsize=7,loc='best')


def external_records(output,figures):
    """Compute read-only diagnostics of saved native traces; never rerun plants."""
    import matplotlib.pyplot as plt
    sources={
      'gasifier':('ALSTOM gasifier','3.11','alstom-native/load050-pressure_step.csv','temperature_K','time_s','K','11-gasifier'),
      'wind_fast':('High-order OpenFAST','3.12','openfast-validation.csv','RotSpeed','time_s','rpm','12-wind-turbine'),
      'tennessee_eastman':('Tennessee Eastman','3.13','te-native/idv-01.csv','xmeas_09','time_h','deg C','13-tennessee-eastman')}
    results={}
    for key,(title,section,path,column,time,unit,diagram) in sources.items():
        source=ROOT/'benchmarks/results'/path; data=np.genfromtxt(source,delimiter=',',names=True)
        # Native solver output may contain nearly duplicate event times. Use an
        # explicit uniform grid rather than treating solver rows as equal steps.
        original_t=np.asarray(data[time]); original_y=np.asarray(data[column])
        unique_t,indices=np.unique(original_t,return_index=True)
        count=min(600,len(unique_t)); t=np.linspace(unique_t[0],unique_t[-1],count)
        y=np.interp(t,unique_t,original_y[indices]); split=int(.6*len(y))
        mean=float(y[:split].mean()); scale=max(float(y[:split].std()),1e-9); z=(y-mean)/scale
        train=np.c_[z[1:split-1],z[:split-2],np.ones(split-2)]
        coef=np.linalg.lstsq(train,z[2:split],rcond=None)[0]
        pred=np.c_[z[split-1:-1],z[split-2:-2],np.ones(len(z)-split)]@coef
        rmse=float(np.sqrt(np.mean((pred-z[split:])**2))*scale)
        diag=learn.sensor_diagnosis(y[split:],.2*scale)
        fig,axes=plt.subplots(1,3,figsize=(13,3.7),constrained_layout=True)
        axes[0].plot(t,y); axes[0].axvline(t[split],color='#bb4c39',ls='--'); axes[0].set(title='Saved native simulation',xlabel=time,ylabel=f'{column} ({unit})')
        axes[1].plot(t[split:],y[split:],label='Held-out'); axes[1].plot(t[split:],pred*scale+mean,label='AR(2) one-step'); axes[1].set(title='Chronological forecast audit',xlabel=time,ylabel=unit); axes[1].legend(fontsize=8)
        a=diag['traces']; axes[2].step(np.arange(len(a)),a[:,0]/2,label='Injected state / 2'); axes[2].plot(a[:,4],label='Causal P(fault)'); axes[2].set(title='Additional synthetic sensor layer',xlabel='Held-out sample'); axes[2].legend(fontsize=8)
        fig.suptitle(title+' — archived trajectory analysis; no simulator rerun',fontsize=13)
        for ext in ('png','svg'):fig.savefig(figures/f'{key}.{ext}',dpi=160)
        plt.close(fig)
        results[key]=dict(title=title,section=section,source='benchmarks/results/'+path,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
          output=column,output_unit=unit,samples=len(y),original_samples=len(data),uniform_step=float(t[1]-t[0]),
          resampling='linear interpolation on uniform endpoint-inclusive time grid',training_samples=split,one_step_rmse_physical=rmse,
          hmm_test_state_support=diag['true_state_support'],
          sensor_accuracy=diag['filtered_accuracy'],simulator_rerun=False,diagram=diagram,
          scope='Chronological output-only AR(2) prediction and additional synthetic sensor HMM. No causal plant identification or new controller evaluation.')
    write_json(output/'external.json',results); return results


def generate_pages(results,externals,directory):
    catalog=learn.case_catalog()
    overview=['# Benchmarks across the nine learning units','',
      'Each native case below has two freshly generated nonlinear records, a training-only scalar model fit and all nine computational stages. The later control curves are explicitly **local fitted-predictor exercises**, not nonlinear-apparatus validation. Full-order and measured-data gaps are retained.','',
      '| Unit | Computation and illustrated results |','|---|---|']
    overview += [f'| {i:02} | [{title}](unit-{i:02}.md) |' for i,(title,_) in UNITS.items()]
    overview+=['','## Case index','', '| Case | Record | Scope |','|---|---|---|']
    for key,r in results.items():
        title,section,*_=catalog[key]
        overview.append(f'| [{title}](cases/{key}.md) | Section {section} | Nonlinear excitation + nine local learning stages |')
    for key,r in externals.items():overview.append(f'| [{r["title"]}](cases/{key}.md) | Section {r["section"]} | Archived native trace + forecast/sensor audit; controller redesign pending |')
    overview += ['| [Throttle](../THROTTLE_RECOVERY.md) | Sections 3.4 and 4.1 | Original measured records unavailable; fixture tests are not replacement measurements |',
      '| [Dataset repositories](../DATASETS.md) | Section 3.2 | Source register and strict importer; a resource collection is not a dynamical plant |','',
      '## Reproduce and interpret','', 'Run `python benchmarks/run_learning_studies.py`. Machine-readable data are in [results/learning](../results/learning/summary.json); each case stores physical input/output records, fit statistics, traces and scores. Fixed seeds are 1401/2401 for training/test generation and 19 for learning. Report the channel, physical units and case qualification when using a figure.','',
      'The ten native cases yield 90 executed learning-stage entries. The three external families have additional offline analyses, while throttle measurements and a chosen historical dataset remain explicit dependencies. Thus this is not a claim of 135 full-order controller validations. See [coverage and source audit](../README.md).']
    (directory/'README.md').write_text('\n'.join(overview)+'\n',encoding='utf-8')
    for i,(title,theory) in UNITS.items():
        lines=[f'# Unit {i:02}: {title} across the article benchmarks','',theory,'',f'![Computed unit {i} benchmark panels](figures/unit-{i:02}.png)','',
          'Each panel reports its own calculation; vertical scales are independent. Normalization makes coordinates comparable in form, not in physical consequence. Read each case before comparing magnitudes.','']
        for key,result in results.items():
            title,section,y,yunit,u,uunit,tunit,limit=catalog[key]
            fit=result['fit']; ident=result['identification']
            lines += [f'## {title} — {section}','',f'Observe **{y} ({yunit})** while exciting **{u} ({uunit})**; time is **{tunit}**. {limit}','',
              f'For this case, the held-out ARX one-step RMSE is **{ident["one_step_rmse"]:.5g}** training standard deviations, versus **{ident["free_run_rmse"]:.5g}** in free run. The fitted output scale is **{fit["output_scale"]:.5g} {yunit}**.']
            if i in (2,3,4,5,7):
                names={2:['pi'],3:['pi','feedforward','cascade'],4:['mpc'],5:['pi','fuzzy'],7:['pi','genetic_pi']}[i]
                for name in names:
                    r=result['loops'][name]; score='unavailable' if r.get('rmse') is None else f'{r["rmse"]:.5g}'
                    lines += [f'- `{name}`: surrogate tracking RMSE **{score}**, status `{r["status"]}`, solver failures **{r.get("solver_failures",0)}**.']
                lines += ['','These commands were applied to the fitted affine recurrence only. Before a full-order experiment, restore all states and channels, select an admissible operating point and test physical constraints using the original model.']
            elif i==6:lines += ['', 'Held-out one-step RMSE: '+', '.join(f'**{k} {v:.5g}**' for k,v in result['neural_rmse'].items())+'.']
            elif i==9:lines += ['',f'Causal accuracy is **{result["diagnosis"]["filtered_accuracy"]:.3f}**; smoothing **{result["diagnosis"]["smoothed_accuracy"]:.3f}** and Viterbi **{result["diagnosis"]["viterbi_accuracy"]:.3f}** use the entire record. All cases use the same normalized injected sensor process; this does not establish plant-specific fault calibration.']
            elif i==8:lines += ['', 'Inspect the three gain-mismatch points, actuator saturation and model-reduction error together. The model fit is frozen before this sensitivity exercise.']
            lines += ['',f'[Nine-stage case sheet](cases/{key}.md) · [Full numerical record](../results/learning/{key}.json)','']
        lines += ['## External models and unavailable measured records','']
        for key,r in externals.items():
            lines += [f'### {r["title"]}','',f'The preserved native trace provides **{r["samples"]}** selected samples of `{r["output"]}`. Output-only held-out prediction RMSE is **{r["one_step_rmse_physical"]:.5g} {r["output_unit"]}**. [Illustrated trace audit](cases/{key}.md).','',
              'Units 1/6 use this as an output-prediction and provenance exercise, unit 8 reviews the preserved validation limits, and unit 9 adds a separate synthetic sensor layer. Units 2–5/7 specify a controller-design protocol but are **not newly executed** on this external plant: archived trajectories cannot be replayed as counterfactual responses to different inputs. Restore the pinned simulator, operating modes, actuator channels and disturbance protocol before redesigning control.','']
        lines += ['### Throttle and identification repositories','',
          'Original throttle measurements remain unavailable. The strict 10,000/2,500-row importer and synthetic fixture tests are documented in [the recovery record](../THROTTLE_RECOVERY.md); no new figure is labeled as measured throttle performance. For section 3.2, first choose and license a specific dataset from [the register](../DATASETS.md), preserve its original split and units, and record its hash. Model fitting, controller design and fault calibration stay pending until those inputs exist.','',
          '[All units and cases](README.md) · [Source equations and boundaries](../README.md)']
        (directory/f'unit-{i:02}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    cases=directory/'cases'; cases.mkdir(exist_ok=True)
    for key,result in results.items():
        title,section,y,yunit,u,uunit,tunit,limit=catalog[key]
        lines=[f'# {title}: nine-stage worked study','',f'Article section **{section}**. {limit}','',
          f'The selected channel is **{u} ({uunit}) → {y} ({yunit})**, with time in **{tunit}**. All generated records are synthetic. A first-order predictor omits other states and possible channel interactions; its control exercise must not be mistaken for full-plant validation.','']
        if key in DIAGRAMS:lines += [f'![Equipment and physical channels](../../figures/{DIAGRAMS[key]}.png)','']
        lines += [f'![Computed nine-stage results](../figures/{key}.png)','',
          '| Stage | Worked explanation |','|---|---|']
        lines += [f'| {i} | [{title}](../unit-{i:02}.md) |' for i,(title,_) in UNITS.items()]
        lines += ['',f'[Physical training record](../../results/learning/{key}-train.csv) · [Independent test record](../../results/learning/{key}-test.csv) · [Numerical results and controller traces](../../results/learning/{key}.json)','',
          'Read the identification panel before trusting a control curve. A large free-run error, a weak input coefficient or extrapolation beyond the excitation region invalidates an apparatus-level interpretation even when the scalar predictor tracks its target. The external-source and conservation audits remain in [the benchmark guide](../../README.md).']
        if key=='pendulum':
            a,b,c=result['fit']['theta']
            lines += ['', '**Negative control result.** The illustrated pendulum predictor does not follow the reference under the tested policies. '
              f'Its fitted pole is {a:.6g}, input coefficient is {b:.6g}, and affine drift is {c:.6g}, in training-normalized coordinates. '
              'With commands limited to [-2, 2], the weak input effect cannot counteract the drift along this trajectory; the output continues to move away from the target. '
              'A status of `completed` records that the numerical loop finished, not that tracking or stabilization passed. '
              'These curves are retained as negative evidence. Establishing pendulum stabilization requires the full cart-pendulum state model, a justified operating point, adequate control authority and a separately validated controller.']
        (cases/f'{key}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for key,r in externals.items():
        (cases/f'{key}.md').write_text(f'# {r["title"]}: preserved execution and new offline analysis\n\n'+
          f'![Equipment](../../figures/{r["diagram"]}.png)\n\n![Archived trajectory and additional sensor audit](../figures/{key}.png)\n\n'+
          f'The source is [{r["source"]}](../../{r["source"].removeprefix("benchmarks/")}); SHA-256 `{r["source_sha256"]}`. No simulator was rerun. {r["scope"]}\n\n'+
          f'The native output is linearly interpolated onto a uniform grid with step {r["uniform_step"]:.6g} in the recorded time unit. The first {r["training_samples"]} of {r["samples"]} samples fit an output-only AR(2); the later segment is held out. One-step physical RMSE is {r["one_step_rmse_physical"]:.6g} {r["output_unit"]}. This split is chronological, not an independent experimental campaign. Closed-loop data and unmeasured disturbances prevent a causal plant-identification claim.\n\n'+
          f'Injected HMM evaluation state counts (normal, drift, fault) are {r["hmm_test_state_support"]}. A short record with absent states cannot demonstrate fault recall.\n\n'+
          'New PI/MPC/fuzzy/evolutionary comparisons require the actual simulator and a matched protocol. Saved trajectories cannot determine a plant response to inputs that were never applied. The sensor panel adds fabricated modes to a known-clean reference; these are not observed equipment faults.\n\n'+
          '[All nine unit applications](../README.md) · [External simulator access and limits](../../EXTERNAL_MODELS.md)\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--reuse',action='store_true'); args=parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.prop_cycle':plt.cycler(color=['#14586b','#d26a30','#647c34','#705399'])})
    out=ROOT/'benchmarks/results/learning'; out.mkdir(parents=True,exist_ok=True)
    directory=ROOT/'benchmarks/learning'; figures=directory/'figures'; figures.mkdir(parents=True,exist_ok=True)
    results={}
    for key,info in learn.case_catalog().items():
        file=out/f'{key}.json'
        if args.reuse and file.exists():
            r=json.loads(file.read_text(encoding='utf-8'))
            if r.get('computation_sha256_lf') != computation_hashes():
                raise ValueError(f'{key}: stale numerical record; rerun without --reuse')
            r['prediction']=np.asarray(r['prediction']); r['neural']=np.asarray(r['neural']); r['diagnosis']['traces']=np.asarray(r['diagnosis']['traces'])
            for v in r['loops'].values():
                if 'trace' in v:v['trace']=np.asarray(v['trace'])
        else:
            records=learn.generate_records(key,ROOT); r=learn.study(records)
            for record,part in zip(records,('train','test')):
                auxiliary=record.get('all_inputs',np.empty((len(record['time']),0)))
                values=np.c_[record['time'],record['input'],record['output'],record['states'],auxiliary]
                names=['time','input','output']+['state_'+str(i) for i in range(record['states'].shape[1])]+['input_'+str(i) for i in range(auxiliary.shape[1])]
                np.savetxt(out/f'{key}-{part}.csv',values,delimiter=',',comments='',header=','.join(names))
            r['case']=key; r['physical_contract']=info; r['record_seeds']=[1401,2401]
            r['computation_sha256_lf']=computation_hashes()
            write_json(file,r)
        results[key]=r
        fig,axes=plt.subplots(3,3,figsize=(14,11),constrained_layout=True)
        for i,ax in enumerate(axes.flat,1):panel(ax,i,r); ax.set_title(f'{i:02} {UNITS[i][0]}',fontsize=10)
        fig.suptitle(info[0]+' | nonlinear records + labelled local-predictor learning',fontsize=15)
        for ext in ('png','svg'):fig.savefig(figures/f'{key}.{ext}',dpi=160)
        plt.close(fig); print(key,flush=True)
    for unit,(title,_) in UNITS.items():
        fig,axes=plt.subplots(5,2,figsize=(13,17),constrained_layout=True)
        for ax,(key,r) in zip(axes.flat,results.items()):panel(ax,unit,r); ax.set_title(learn.case_catalog()[key][0])
        fig.suptitle(f'Unit {unit:02}: {title}\nSynthetic native records; controller panels use fitted scalar predictors',fontsize=15)
        for ext in ('png','svg'):fig.savefig(figures/f'unit-{unit:02}.{ext}',dpi=150)
        plt.close(fig)
    external=external_records(out,figures); generate_pages(results,external,directory)
    summary=dict(native_cases=len(results),learning_stages=9,executed_native_case_stages=9*len(results),
      external_offline_analyses=list(external),external_simulators_rerun=False,
      unresolved=['Original throttle measurements','Chosen canonical section-3.2 dataset','Full-order controller comparisons for external plants'],
      source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in [Path(__file__),ROOT/'python/intelligent_control/benchmark_learning.py']},
      cases={k:dict(identification=r['identification'],neural_rmse=r['neural_rmse'],hmm_accuracy=r['diagnosis']['filtered_accuracy']) for k,r in results.items()})
    write_json(out/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('cases','source_sha256')},indent=2))


if __name__=='__main__':main()
