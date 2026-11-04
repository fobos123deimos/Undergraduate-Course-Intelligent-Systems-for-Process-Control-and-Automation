function result = run_markov_lab(make_plots)
%RUN_MARKOV_LAB Markov sensor regimes, categorical HMM and PI supervision.
%   The nominal tank predictor knows its applied input and initial state.
%   Residual conditional independence is a sensor-calibration assumption;
%   the mismatched-plant experiment deliberately violates that assumption.
if nargin<1,make_plots=false;end
dt=.2;P=[.97 .025 .005;.04 .93 .03;.02 .08 .9];pi=[.8 .15 .05];
bias=[0;.055;.14];sigma=.035;cuts=[.025 .095];ntrain=20;Ntrain=150;Ntest=600;
names={'normal','drift','sensor fault'};
% Analytic emissions are a simulation reference; fitting uses labels only.
cdf_low=.5*(1+erf((cuts(1)-bias)/(sigma*sqrt(2))));
cdf_high=.5*(1+erf((cuts(2)-bias)/(sigma*sqrt(2))));
Btrue=[cdf_low cdf_high-cdf_low 1-cdf_high];
rng(17,'twister');zs=cell(ntrain,1);os=zs;sum_residual=zeros(3,1);counts=zeros(3,1);
for k=1:ntrain
 zs{k}=markov_models('simulate_chain',P,pi,Ntrain);
 residual=bias(zs{k})+sigma*randn(Ntrain,1);os{k}=categorize(residual,cuts);
 for j=1:3
  selected=zs{k}==j;sum_residual(j)=sum_residual(j)+sum(residual(selected));
  counts(j)=counts(j)+sum(selected);
 end
end
assert(all(counts>0),'Calibration must include every sensor regime.');
fit=markov_models('supervised',zs,os,3,3,1);calibration_bias=sum_residual./counts;
assert(abs(sum(fit.transition_counts(:))-(ntrain*(Ntrain-1)+9))<1e-12);
rng(2026,'twister');z=markov_models('simulate_chain',P,pi,Ntest);
noise=sigma*randn(Ntest,1);residual=bias(z)+noise;o=categorize(residual,cuts);
filtered=markov_models('filter',fit.transition,fit.emission,fit.initial,o);
smoothed=markov_models('smooth',fit.transition,fit.emission,fit.initial,o);
decoded=markov_models('viterbi',fit.transition,fit.emission,fit.initial,o);
[~,filter_state]=max(filtered.filtered,[],2);[~,smooth_state]=max(smoothed.smoothed,[],2);
fitted_stationary=markov_models('stationary',fit.transition);
emission_scores=bsxfun(@times,fit.emission(:,o)',fitted_stationary);
[~,emission_state]=max(emission_scores,[],2);
alarm=filtered.filtered(:,3)>=.7;fault=z==3;
metrics=struct('threshold_accuracy',mean(o==z),'filter_accuracy',mean(filter_state==z),...
 'emission_map_accuracy',mean(emission_state==z),...
 'smoother_accuracy',mean(smooth_state==z),'viterbi_accuracy',mean(decoded.path==z),...
 'test_log_likelihood_per_sample',filtered.log_likelihood/Ntest,...
 'fault_brier_score',mean((filtered.filtered(:,3)-double(fault)).^2),...
 'alarm_precision',ratio(sum(alarm&fault),sum(alarm)),...
 'alarm_recall',ratio(sum(alarm&fault),sum(fault)),...
 'alarm_false_positive_rate',ratio(sum(alarm&~fault),sum(~fault)));

% Illustrative irreversible failure chain: stop at first visit to state 3.
absorbing=P;absorbing(3,:)=[0 0 1];
[hitting_steps,hitting_probability]=markov_models('hitting',absorbing,3);
stationary=markov_models('stationary',P);
forecast=markov_models('propagate',P,pi,20);
healthy_forecast=markov_models('propagate',P,[1 0 0],50);
holding_steps=1./(1-diag(P));
failure_forecast=markov_models('propagate',absorbing,pi,100);

% EM uses independent observation records. State names are not identifiable
% without additional calibration: compare likelihood, not raw label numbers.
% Simulator probabilities provide a disclosed favorable initialization.
em=markov_models('baum_welch',os,P,Btrue,pi,30,1e-6);
em_test=markov_models('filter',em.transition,em.emission,em.initial,o);
em.test_log_likelihood_per_sample=em_test.log_likelihood/Ntest;

% All policies receive identical hidden regimes and observation noise.
% Only the forward posterior is available to the online supervisor.
t=(0:Ntest-1)'*dt;r=.35+.30*(t>=10)-.20*(t>=75);
nominal_baseline=closed_loop(10,false,fit,calibration_bias,z,noise,bias,cuts,r,dt);
nominal_supervisor=closed_loop(10,true,fit,calibration_bias,z,noise,bias,cuts,r,dt);
mismatch_baseline=closed_loop(14,false,fit,calibration_bias,z,noise,bias,cuts,r,dt);
mismatch_supervisor=closed_loop(14,true,fit,calibration_bias,z,noise,bias,cuts,r,dt);
assert(norm(sum(filtered.filtered,2)-1,Inf)<1e-12);
assert(norm(sum(smoothed.smoothed,2)-1,Inf)<1e-12);
assert(all(diff(em.log_likelihood_history)>=-1e-7));
assert(norm(stationary*P-stationary,Inf)<1e-12);
assert(all(isfinite(nominal_supervisor.concentration)) && all(isfinite(mismatch_supervisor.concentration)));
result=struct('unit',9,'t',t,'state_names',{names},'transition_true',P,...
 'emission_true',Btrue,'initial_true',pi,'cutpoints',cuts,'bias_true',bias,...
 'noise_standard_deviation',sigma,'calibration_bias',calibration_bias,...
 'calibration_records',ntrain,'samples_per_calibration_record',Ntrain,...
 'fit',fit,'hidden_states',z,'residual',residual,'observations',o,...
 'filtered',filtered.filtered,'smoothed',smoothed.smoothed,'viterbi_path',decoded.path,...
 'alarm',alarm,'metrics',metrics,'stationary',stationary,'four_minute_distribution',forecast,...
 'ten_minute_distribution_from_normal',healthy_forecast,'holding_steps',holding_steps,...
 'holding_minutes',dt*holding_steps,'emission_map_states',emission_state,...
 'emission_map_prior',fitted_stationary,...
 'absorbing_transition',absorbing,'hitting_probability',hitting_probability,...
 'hitting_steps',hitting_steps,'hitting_minutes',dt*hitting_steps,...
 'failure_probability_by_20_minutes',failure_forecast(3),'em',em,...
 'nominal_baseline',nominal_baseline,'nominal_supervisor',nominal_supervisor,...
 'mismatch_baseline',mismatch_baseline,'mismatch_supervisor',mismatch_supervisor);
if make_plots
 figure;
 subplot(3,1,1);stairs(t,z,'k');hold on;stairs(t,filter_state,'b:');
 ylabel('Regime');ylim([.8 3.2]);legend('Actual','Filtered');grid on;
 subplot(3,1,2);plot(t,filtered.filtered);ylabel('Posterior');legend(names);grid on;
 subplot(3,1,3);plot(t,residual);hold on;plot(t,cuts(1)*ones(size(t)),'k--');
 plot(t,cuts(2)*ones(size(t)),'k--');ylabel('Residual');xlabel('Time / min');grid on;
 figure;
 subplot(2,1,1);plot(t,r,'k--',t,nominal_baseline.concentration,t,nominal_supervisor.concentration);
 ylabel('Concentration');title('Nominal tank, time constant 10 min');legend('Reference','PI','HMM-supervised PI');grid on;
 subplot(2,1,2);plot(t,r,'k--',t,mismatch_baseline.concentration,t,mismatch_supervisor.concentration);
 ylabel('Concentration');xlabel('Time / min');title('Mismatched tank, time constant 14 min');grid on;
end
fprintf('Unit 09: Markov/HMM laboratory assertions passed; filtered accuracy %.3f.\n',metrics.filter_accuracy);
end

function out=closed_loop(tau,use_supervisor,fit,calibration_bias,z,noise,bias,cuts,r,dt)
N=numel(r);x=zeros(N,1);x(1)=.35;predictor=.35;a=exp(-dt/tau);a0=exp(-dt/10);
u=zeros(N,1);measurement=u;corrected=u;post=zeros(N,3);integral=0;prior=fit.initial;
for k=1:N
 measurement(k)=x(k)+bias(z(k))+noise(k);
 symbol=categorize(measurement(k)-predictor,cuts);
 f=markov_models('filter',fit.transition,fit.emission,prior,symbol);
 post(k,:)=f.filtered;prior=post(k,:)*fit.transition;
 corrected(k)=measurement(k);
 if use_supervisor,corrected(k)=measurement(k)-post(k,:)*calibration_bias;end
 error_value=r(k)-corrected(k);candidate=integral+.2*dt*error_value;
 proposal=.35+2*error_value+candidate;
 if (proposal>1&&error_value>0)||(proposal<0&&error_value<0)
  proposal=.35+2*error_value+integral;
 else
  integral=candidate;
 end
 u(k)=min(1,max(0,proposal));
 if k<N,x(k+1)=a*x(k)+(1-a)*u(k);predictor=a0*predictor+(1-a0)*u(k);end
end
err=r-x;
out=struct('concentration',x,'measurement',measurement,'corrected_measurement',corrected,...
 'input',u,'reference',r,'posterior',post,'time_constant',tau,...
 'iae',trapz((0:N-1)'*dt,abs(err)),'rmse',sqrt(mean(err.^2)),...
 'input_total_variation',sum(abs(diff(u))),'saturation_fraction',mean(u==0|u==1));
end

function o=categorize(residual,cuts)
o=1+double(residual>=cuts(1))+double(residual>=cuts(2));
end

function value=ratio(numerator,denominator)
value=NaN;if denominator>0,value=numerator/denominator;end
end
