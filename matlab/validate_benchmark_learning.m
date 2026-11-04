function records=validate_benchmark_learning(case_names)
%VALIDATE_BENCHMARK_LEARNING Nine native learning stages on ten saved cases.
%   records=validate_benchmark_learning() reads the independent train/test
%   CSV files under benchmarks/results/learning. An optional cell array of
%   case names selects a subset explicitly; missing requested data is an error.
%
%   Stages 1-5 replay scalar identification/control using the saved physical
%   records. MPC uses the existing toolbox-free constrained quadratic solver.
%   Stages 6-7 retrain MLP/RBF and a real-coded GA with native RNG seed 19.
%   RNG streams and optimizers differ from NumPy/SciPy: equality of learned
%   weights, tuned gains or MPC traces is NOT claimed. Saved Python scalar
%   PI/feedforward/cascade/fuzzy/selected-GA traces are separately replayed.
%   Stage 8 varies the predictor input gain. Stage 9 calibrates an independent
%   native HMM and scores saved synthetic observations; test labels score only.
%
%   This function does not integrate the original nonlinear plants, rerun an
%   external simulator, acquire throttle measurements, write files, or prove
%   equipment-level stability. Control bounds refer to normalized exercises.

all_cases={'artificial_siso','artificial_mimo','pendulum','pneumatic',...
 'hydrostatic','three_tank','bioreactor','cstr','column_a','wind_reduced'};
if nargin<1,case_names=all_cases;end
assert(iscell(case_names)&&~isempty(case_names),'Use a nonempty cell array of case names');
assert(all(ismember(case_names,all_cases))&&numel(unique(case_names))==numel(case_names),'Unknown or duplicate case');
root=fileparts(fileparts(mfilename('fullpath')));
folder=fullfile(root,'benchmarks','results','learning');
saved_rng=rng; restore_rng=onCleanup(@() rng(saved_rng)); %#ok<NASGU>
rows=cell(numel(case_names),1);
for index=1:numel(case_names)
 name=case_names{index};
 train_path=fullfile(folder,[name '-train.csv']);test_path=fullfile(folder,[name '-test.csv']);
 json_path=fullfile(folder,[name '.json']);
 assert(exist(train_path,'file')==2&&exist(test_path,'file')==2&&exist(json_path,'file')==2,...
  ['Missing learning records for ' name '; run benchmarks/run_learning_studies.py first.']);
 train=dlmread(train_path,',',1,0);test=dlmread(test_path,',',1,0);
 reference=jsondecode(fileread(json_path));
 assert(size(train,2)>=3&&size(test,2)>=3&&size(train,1)>=30&&size(test,1)>=30);
 assert(all(isfinite(train(:)))&&all(isfinite(test(:)))&&all(diff(train(:,1))>0)&&all(diff(test(:,1))>0));
 assert(isequal(reference.record_seeds(:),[1401;2401]),'Unexpected record split');

 % Unit 1: population standard deviations, estimated on training rows only.
 ym=mean(train(:,3));ys=std(train(:,3),1);um=mean(train(:,2));us=std(train(:,2),1);
 assert(min(ys,us)>1e-12);
 stats=[ym;ys;um;us];expected=[reference.fit.output_mean;reference.fit.output_scale;reference.fit.input_mean;reference.fit.input_scale];
 close_enough(stats,expected,2e-10,'Training normalization');
 z=(train(:,3)-ym)/ys;v=(train(:,2)-um)/us;
 zv=(test(:,3)-ym)/ys;vv=(test(:,2)-um)/us;
 design=[z(1:end-1) v(1:end-1) ones(numel(z)-1,1)];assert(rank(design)==3);
 fitted=design\z(2:end);theta=reference.fit.theta(:);
 close_enough(fitted,theta,2e-8,'Least-squares coefficients');
 one=[zv(1:end-1) vv(1:end-1) ones(numel(zv)-1,1)]*fitted;
 free=zeros(size(zv));free(1)=zv(1);
 for k=1:numel(zv)-1,free(k+1)=fitted(1)*free(k)+fitted(2)*vv(k)+fitted(3);end
 identification=[sqrt(mean((one-zv(2:end)).^2));sqrt(mean((free-zv).^2))];
 close_enough(identification,[reference.identification.one_step_rmse;reference.identification.free_run_rmse],2e-7,'Held-out ARX scores');
 close_enough(free,reference.prediction(:,3),2e-7,'Recursive held-out prediction');

 % Units 2, 3 and 5: exact update ordering and affine feedforward bias.
 assert(abs(theta(2))>=1e-8,'Input gain is unusable for this scalar exercise');
 kp=(theta(1)-.80*.85)/theta(2);ki=(1-.80)*(1-.85)/theta(2);
 pole_polynomial=poly([theta(1)-theta(2)*(kp+ki),theta(2);-ki,1]);
 close_enough(pole_polynomial,poly([.80 .85]),1e-10,'Unsaturated nominal PI poles');
 policies={'pi','feedforward','cascade','fuzzy'};loops=struct;replay_errors=zeros(1,numel(policies));
 for j=1:numel(policies)
  policy=policies{j};native=learning_loop(theta,policy,[1 1],1,'test');
  expected_trace=reference.loops.(policy).trace;
  replay_errors(j)=close_enough(native.trace,expected_trace,2e-7,[name ' ' policy ' trace']);
  close_enough(native.rmse,reference.loops.(policy).rmse,2e-7,'Controller RMSE');
  loops.(policy)=native;
 end

 % Unit 4: same eight-step affine objective and three independent moves.
 % The dual solver is independent of SciPy SLSQP; check constraints, held
 % fallback and objective quality instead of demanding identical iterates.
 loops.mpc=learning_loop(theta,'mpc',[1 1],1,'test');

 % Unit 6: train native networks without touching held-out means or scales.
 neural=native_neural([z(1:end-1) v(1:end-1)],z(2:end),...
  [zv(1:end-1) vv(1:end-1)],zv(2:end));
 python_scores=sqrt(mean((reference.neural(:,2:4)-reference.neural(:,1)).^2,1));
 close_enough(python_scores,[reference.neural_rmse.ARX reference.neural_rmse.MLP reference.neural_rmse.RBF],1e-10,'Saved neural scores');

 % Unit 7: same population/generation budget; different native RNG stream.
 ga=native_genetic(theta);assert(ga.evaluations==90&&all(diff(ga.history)<=1e-10));
 assert(all(ga.parameters>=.4)&all(ga.parameters<=1.6));
 ga.validation=learning_loop(theta,'pi',ga.parameters,1,'test');
 selected=learning_loop(theta,'pi',reference.ga.parameters(:)',1,'test');
 close_enough(selected.trace,reference.loops.genetic_pi.trace,2e-7,'Saved genetic gains replay');

 % Unit 8: fixed nominal controllers on paired gain-mismatch scenarios.
 gains=[.8 1 1.2];robustness=struct;
 for j=1:3
  factor=gains(j);names={'pi','mpc','fuzzy'};metrics=zeros(3,3);
  for p=1:3
   q=learning_loop(theta,names{p},[1 1],factor,'test');
   metrics(p,:)=[q.rmse q.max_input q.solver_failures];
  end
  robustness.(['gain_' strrep(sprintf('%.1f',factor),'.','_')])=metrics;
 end

 % Unit 9: independent native calibration; only causal filtering is online.
 diagnosis=native_diagnosis(reference.diagnosis.traces);
 rows{index}=struct('case_name',name,'stages_executed',9,'training_rows',size(train,1),...
  'test_rows',size(test,1),'theta',fitted,'arx_rmse',identification,...
  'pi_poles',roots(pole_polynomial),'controller_replay_scaled_error',max(replay_errors),...
  'controllers',loops,'neural',neural,'genetic',ga,'robustness',robustness,'diagnosis',diagnosis);
 fprintf('%s: nine native learning stages passed; ARX one-step %.6g, free-run %.6g.\n',name,identification);
end
records=struct('case_count',numel(rows),'learning_stage_count',9*numel(rows),'cases',{rows},...
 'scope','Saved nonlinear records; scalar predictor control; native learning RNG; no nonlinear/external simulator rerun',...
 'neural_and_genetic_seed',19,'mpc_solver','Existing toolbox-free dual quadratic solver');
end

function q=learning_loop(theta,policy,gains,mismatch,scenario)
a=theta(1);b=theta(2);c=theta(3);kp=(a-.80*.85)/b*gains(1);ki=(1-.80)*(1-.85)/b*gains(2);
bias=-c/b;integral=0;old_error=0;previous=0;actuator=0;y=0;rows=zeros(80,5);failures=0;diverged=false;
for k=0:79
 if strcmp(scenario,'train'),reference=.35*(k>=8);start=40;
 else,reference=.3*(k>=10&&k<45)-.15*(k>=45);start=55;end
 disturbance=.15*(k>=start&&k<72);error_value=reference-y;
 switch policy
  case 'mpc'
   [u,info]=mpc_control(a,b,y,reference,8,3,.1,previous,...
    struct('lower',-2,'upper',2,'max_move',.4,'affine',c,'tolerance',1e-7,'max_iterations',3000));
   assert(abs(u)<=2+1e-6&&abs(u-previous)<=.4+1e-6,'MPC actuator or first-move constraint');
   if info.success
    assert(max(abs(info.planned_inputs))<=2+1e-6&&max(abs(info.moves))<=.4+1e-6);
    hold_cost=0;pred=y;
    for future=1:8,pred=a*pred+b*previous+c;hold_cost=hold_cost+(pred-reference)^2;end
    assert(info.cost<=hold_cost+1e-5*max(1,hold_cost),'MPC worse than feasible hold plan');
   else
    assert(u==previous&&info.held_previous,'Solver failure must hold prior input');failures=failures+1;
   end
  case 'fuzzy'
   u=clip(previous+sign(b)*.12*sugeno(error_value,4*(error_value-old_error)),-2,2);
  otherwise
   offset=0;if strcmp(policy,'feedforward'),offset=-disturbance;end
   request=bias+kp*error_value+integral+ki*error_value+offset;u=clip(request,-2,2);
   if request==u||(request-u)*ki*error_value<0,integral=integral+ki*error_value;end
   if strcmp(policy,'cascade')
    command=clip(u+2*(u-actuator),-2,2);actuator=.7*actuator+.3*command;u=actuator;
   end
 end
 rows(k+1,:)=[k reference y u disturbance];previous=u;old_error=error_value;
 y=a*y+b*mismatch*(u+disturbance)+c;
 if ~isfinite(y)||abs(y)>1e6,diverged=true;break;end
end
rows=rows(1:k+1,:);assert(all(isfinite(rows(:)))&&max(abs(rows(:,4)))<=2+1e-6);
% Independently check state timing from each applied input and disturbance.
if size(rows,1)>1
 predicted=a*rows(1:end-1,3)+b*mismatch*(rows(1:end-1,4)+rows(1:end-1,5))+c;
 close_enough(predicted,rows(2:end,3),1e-12,'Applied-input recurrence');
end
status='completed';if diverged,status='diverged';end
q=struct('trace',rows,'rmse',sqrt(mean((rows(:,2)-rows(:,3)).^2)),...
 'movement',sum(abs(diff(rows(:,4)))),'max_input',max(abs(rows(:,4))),...
 'solver_failures',failures,'status',status,'terminal_state',y);
end

function value=sugeno(error_value,change)
e=clip(error_value,-1,1);d=clip(change,-1,1);
me=[max(-e,0),1-abs(e),max(e,0)];md=[max(-d,0),1-abs(d),max(d,0)];
labels=[-1 0 1];rules=clip(labels'+.5*labels,-1,1);weights=me'*md;
value=sum(sum(weights.*rules))/sum(weights(:));
end

function record=native_neural(X,target,Xtest,ytest)
rng(19,'twister');xm=mean(X,1);xs=max(std(X,1,1),1e-8);ym=mean(target);ys=max(std(target,1),1e-8);
Z=(X-xm)./xs;V=(Xtest-xm)./xs;t=(target-ym)/ys;n=size(X,1);
parameters={.3*randn(2,10),zeros(1,10),.3*randn(10,1),0};
first=cellfun(@(p) zeros(size(p)),parameters,'UniformOutput',false);second=first;history=zeros(5,1);
for epoch=1:500
 hidden=tanh(Z*parameters{1}+parameters{2});residual=hidden*parameters{3}+parameters{4}-t;
 out=2*residual/n;dh=(out*parameters{3}').*(1-hidden.^2);
 gradient={Z'*dh,sum(dh,1),hidden'*out,sum(out)};
 for j=1:4
  first{j}=.9*first{j}+.1*gradient{j};second{j}=.999*second{j}+.001*gradient{j}.^2;
  parameters{j}=parameters{j}-.01*(first{j}/(1-.9^epoch))./(sqrt(second{j}/(1-.999^epoch))+1e-8);
 end
 if mod(epoch,100)==0,history(epoch/100)=mean(residual.^2);end
end
mlp=(tanh(V*parameters{1}+parameters{2})*parameters{3}+parameters{4})*ys+ym;
rng(19,'twister');indices=randperm(n,min(16,n));centers=Z(indices,:);
Phi=rbf_features(Z,centers);held=rbf_features(V,centers);ridge=1e-4;
weights=(Phi'*Phi+ridge*eye(size(Phi,2)))\(Phi'*target);rbf=held*weights;
assert(all(isfinite([mlp;rbf;history])),'Nonfinite native neural result');
record=struct('mlp_rmse',sqrt(mean((mlp-ytest).^2)),'rbf_rmse',sqrt(mean((rbf-ytest).^2)),...
 'training_feature_mean',xm,'training_feature_scale',xs,'mlp_training_loss',history,...
 'rbf_center_training_indices',indices,'seed',19,'python_weight_parity_claimed',false);
end

function Phi=rbf_features(X,centers)
Phi=[ones(size(X,1),1) X zeros(size(X,1),size(centers,1))];
for j=1:size(centers,1),Phi(:,3+j)=exp(-sum((X-centers(j,:)).^2,2)/2);end
end

function record=native_genetic(theta)
rng(19,'twister');population=rand(10,2);history=zeros(9,1);evaluations=0;
for generation=1:9
 scores=zeros(10,1);
 for j=1:10
  q=learning_loop(theta,'pi',.4+1.2*population(j,:),1,'train');
  scores(j)=q.rmse+.003*q.movement;if ~strcmp(q.status,'completed'),scores(j)=1e9;end
 end
 evaluations=evaluations+10;[best,index]=min(scores);history(generation)=best;
 if generation==9,break;end
 children=zeros(10,2);children(1,:)=population(index,:);
 for j=2:10
  ids=randi(10,3,1);[~,chosen]=min(scores(ids));parent=population(ids(chosen),:);
  ids=randi(10,3,1);[~,chosen]=min(scores(ids));other=population(ids(chosen),:);
  alpha=rand(1,2);child=alpha.*parent+(1-alpha).*other;
  child=child+.08*randn(1,2).*(rand(1,2)<.25);children(j,:)=clip(child,0,1);
 end
 population=children;
end
record=struct('parameters',.4+1.2*population(index,:),'fitness',best,'history',history,...
 'evaluations',evaluations,'seed',19,'python_rng_parity_claimed',false);
end

function record=native_diagnosis(traces)
P=[.97 .025 .005;.04 .94 .02;.03 .02 .95];B=[.94 .05 .01;.08 .86 .06;.01 .09 .9];pi=[1 0 0];
states=cell(20,1);observations=cell(20,1);
for k=1:20
 sample=markov_models('simulate',P,B,pi,150,3999+k);
 states{k}=sample.states;observations{k}=sample.observations;
end
model=markov_models('supervised',states,observations,3,3,1);
% JSON uses zero-based symbols; convert once at this language boundary.
test_states=traces(:,1)+1;test_symbols=traces(:,2)+1;
filtered=markov_models('filter',model.transition,model.emission,model.initial,test_symbols);
smoothed=markov_models('smooth',model.transition,model.emission,model.initial,test_symbols);
path=markov_models('viterbi',model.transition,model.emission,model.initial,test_symbols);
split=max(1,floor(numel(test_symbols)/2));prefix=markov_models('filter',model.transition,model.emission,model.initial,test_symbols(1:split));
close_enough(prefix.filtered,filtered.filtered(1:split,:),1e-12,'Causal HMM prefix');
close_enough(sum(filtered.filtered,2),ones(numel(test_symbols),1),1e-12,'Filtered normalization');
close_enough(sum(smoothed.smoothed,2),ones(numel(test_symbols),1),1e-12,'Smoothed normalization');
stationary=markov_models('stationary',model.transition);
close_enough(stationary*model.transition,stationary,1e-12,'Stationary distribution');
[~,online]=max(filtered.filtered,[],2);[~,offline]=max(smoothed.smoothed,[],2);
[~,instantaneous]=max(model.emission(:,test_symbols),[],1);
support=accumarray(test_states,1,[3 1]);
record=struct('filtered_accuracy',mean(online==test_states),'smoothed_accuracy',mean(offline==test_states),...
 'viterbi_accuracy',mean(path.path==test_states),'instantaneous_accuracy',mean(instantaneous(:)==test_states),...
 'test_state_support',support,'stationary',stationary,'calibration_sequences',20,...
 'transition',model.transition,'emission',model.emission,'initial',model.initial,...
 'known_clean_reference_required',true,'python_calibration_parity_claimed',false);
end

function error_value=close_enough(actual,expected,tolerance,label)
assert(isequal(size(actual),size(expected)),[label ': shape mismatch']);
assert(all(isfinite(actual(:)))&&all(isfinite(expected(:))),[label ': nonfinite values']);
error_value=max(abs(actual(:)-expected(:)))/max(1,max(abs(expected(:))));
assert(error_value<=tolerance,sprintf('%s: scaled error %.6g exceeds %.6g',label,error_value,tolerance));
end

function value=clip(value,lower,upper)
value=min(upper,max(lower,value));
end
