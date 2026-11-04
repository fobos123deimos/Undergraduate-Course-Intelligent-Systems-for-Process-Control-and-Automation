function report=validate_intelligent_adapters(fuzzy,neural)
%VALIDATE_INTELLIGENT_ADAPTERS Streaming policies versus independent lab loops.
if nargin<1,fuzzy=run_lesson(5,false);end
if nargin<2,neural=run_lesson(6,false);end
dt=.2;a=exp(-dt/10);p=struct('dt',dt,'filter_time',.5);
x=.35;state=[.35;.35;0];xf=zeros(numel(fuzzy.t),1);uf=zeros(numel(fuzzy.t)-1,1);xf(1)=x;
for k=1:numel(uf)
 [uf(k),state]=fuzzy_pid_step(state,[fuzzy.reference(k);x],p);
 x=a*x+(1-a)*(uf(k)+.08*(fuzzy.t(k)>=45));xf(k+1)=x;
end
report.fuzzy_state_max_error=max(abs(xf-fuzzy.fuzzy_pid.y));
report.fuzzy_input_max_error=max(abs(uf-fuzzy.fuzzy_pid.u(1:end-1)));
assert(max([report.fuzzy_state_max_error report.fuzzy_input_max_error])<1e-11);
x=0;xn=zeros(numel(neural.t),1);un=zeros(numel(neural.t)-1,1);model=neural.neural_models.rbf;
for k=1:numel(un)
 un(k)=neural_inverse_action(model,neural.reference(k),x);
 x=a*x+(1-a)*un(k)+.015*sin(3*x)*un(k);xn(k+1)=x;
end
report.neural_state_max_error=max(abs(xn-neural.y));
report.neural_input_max_error=max(abs(un-neural.neural_inputs(1:end-1)));
assert(max([report.neural_state_max_error report.neural_input_max_error])<1e-11);
report.passed=true;fprintf('Fuzzy PID and neural inverse-controller adapters matched native labs.\n');
end
