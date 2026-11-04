function report=validate_online_hmm(lab)
%VALIDATE_ONLINE_HMM Check streaming interfaces against batch/native references.
if nargin<1,lab=run_markov_lab(false);end
prior=lab.fit.initial;post=zeros(size(lab.filtered));ll=0;
for k=1:numel(lab.observations)
 [post(k,:),prior,scale]=hmm_filter_step(lab.fit.transition,lab.fit.emission,prior,lab.observations(k));
 ll=ll+scale;
end
batch=markov_models('filter',lab.fit.transition,lab.fit.emission,lab.fit.initial,lab.observations);
report.filter_max_error=max(abs(post(:)-batch.filtered(:)));
assert(report.filter_max_error<1e-12&&abs(ll-batch.log_likelihood)<1e-9);
% Compare all four policies with run_markov_lab's independent loop.
names={'nominal_baseline','nominal_supervisor','mismatch_baseline','mismatch_supervisor'};
errors=zeros(4,1);
for j=1:4
 reference=lab.(names{j});tau=reference.time_constant;dt=lab.t(2)-lab.t(1);
 p=struct('transition',lab.fit.transition,'emission',lab.fit.emission,...
  'bias',lab.calibration_bias,'cutpoints',lab.cutpoints,'dt',dt,'nominal_tau',10,...
  'kp',2,'ki',.2,'actuator_bias',.35,'supervised',mod(j,2)==0);
 state=[.35;0;lab.fit.initial(:)];x=.35;trace=zeros(numel(lab.t),6);
 for k=1:numel(lab.t)
  measurement=x+lab.residual(k);
  [v,state]=hmm_pi_step(state,[reference.reference(k);measurement],p);
  trace(k,:)=v';x=exp(-dt/tau)*x+(1-exp(-dt/tau))*v(1);
 end
 expected=[reference.input reference.posterior reference.corrected_measurement];
 difference=trace(:,1:5)-expected;errors(j)=max(abs(difference(:)));
 assert(errors(j)<1e-11);
end
% A future observation cannot change a streaming prefix already calculated.
changed=lab.observations;changed(301:end)=1;prior=lab.fit.initial;prefix=zeros(300,3);
for k=1:300,[prefix(k,:),prior]=hmm_filter_step(lab.fit.transition,lab.fit.emission,prior,changed(k));end
difference=prefix-post(1:300,:);assert(max(abs(difference(:)))<1e-12);
report.policy_names=names;report.policy_max_errors=errors;report.passed=true;
fprintf('Streaming HMM filtering and four causal PI policies passed.\n');
end
