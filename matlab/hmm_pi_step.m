function [output,next_state] = hmm_pi_step(state,input,p)
%HMM_PI_STEP Causal HMM sensor-bias supervision and bounded PI control.
% state=[nominal predictor; integral; current pre-observation probabilities].
% input=[reference; measured concentration]. No true sensor state is an input.
% output=[actuator; posterior(1:3); corrected measurement; predictor].
state=state(:);input=input(:);
assert(numel(state)==5&&numel(input)==2&&all(isfinite([state;input])));
assert(p.dt>0&&p.nominal_tau>0&&numel(p.bias)==3&&numel(p.cutpoints)==2);
residual=input(2)-state(1);
symbol=1+double(residual>=p.cutpoints(1))+double(residual>=p.cutpoints(2));
[posterior,next_prior]=hmm_filter_step(p.transition,p.emission,state(3:5)',symbol);
corrected=input(2);
if p.supervised,corrected=corrected-posterior*p.bias(:);end
e=input(1)-corrected;
candidate=state(2)+p.ki*p.dt*e;
proposal=p.actuator_bias+p.kp*e+candidate;
if (proposal>1&&e>0)||(proposal<0&&e<0)
 integral=state(2);proposal=p.actuator_bias+p.kp*e+integral;
else
 integral=candidate;
end
u=min(1,max(0,proposal));
a=exp(-p.dt/p.nominal_tau);
next_state=[a*state(1)+(1-a)*u;integral;next_prior(:)];
output=[u;posterior(:);corrected;state(1)];
end
