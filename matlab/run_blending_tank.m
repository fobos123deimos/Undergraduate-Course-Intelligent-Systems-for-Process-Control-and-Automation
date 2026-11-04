function result = run_blending_tank(make_plots)
%RUN_BLENDING_TANK Corrected physical model, filling and local linearization.
if nargin<1,make_plots=false;end
p=bt_parameters();t=(0:.2:30)';
startup=bt_simulate(t,[0;2],p.ubar,p);
fillinput=p.ubar;fillinput(5)=650;
filling=bt_simulate(t,[0;2],fillinput,p);
model=bt_linearize(p.xbar,p.ubar,p);
U=repmat(p.ubar',numel(t)-1,1);U(t(1:end-1)>=5,1)=510;
perturbed=bt_simulate(t,p.xbar,U,p);
linear=linear_response(t,U,model);
epsilons=[20;10;5];errors=zeros(size(epsilons));
for j=1:numel(epsilons)
 uj=repmat(p.ubar',numel(t)-1,1);uj(t(1:end-1)>=5,1)=500+epsilons(j);
 nj=bt_simulate(t,p.xbar,uj,p);lj=linear_response(t,uj,model);
 errors(j)=max(abs(nj.x(:,1)-lj(:,1)));
end
result=struct('parameters',p,'linear_model',model,'startup',startup,...
 'filling',filling,'perturbed',perturbed,'linear_states',linear,...
 'flow_perturbations',epsilons,'max_concentration_errors',errors);
if make_plots
 figure;
 subplot(2,2,1);plot(t,startup.x(:,1),t,filling.x(:,1));ylabel('Mass fraction X');
 legend('Balanced flow','Filling: outlet 650 kg/min');title('Nonlinear startup');grid on;
 subplot(2,2,3);plot(t,startup.x(:,2),t,filling.x(:,2));ylabel('Volume / m^3');xlabel('Time / min');grid on;
 subplot(2,2,2);plot(t,perturbed.x(:,1),t,linear(:,1),'--');ylabel('Mass fraction X');
 legend('Nonlinear','Equilibrium plus deviation');title('Inlet 1 step of 10 kg/min at 5 min');grid on;
 subplot(2,2,4);plot(t,perturbed.x(:,2),t,linear(:,2),'--');ylabel('Volume / m^3');xlabel('Time / min');grid on;
end
fprintf('Corrected Blending Tank: Xeq=%.6f; G11 numerator=%g; filling V(30)=%.6f m^3.\n',...
 p.xbar(1),model.transfer_num{1,1},filling.x(end,2));
end

function states=linear_response(t,U,model)
% Exact propagation of the deviation equations under held interval inputs.
N=numel(t);delta=zeros(N,2);
for k=1:N-1
 E=expm([model.A,model.B;zeros(5,7)]*(t(k+1)-t(k)));
 delta(k+1,:)=(E(1:2,1:2)*delta(k,:)'+E(1:2,3:7)*(U(k,:)'-model.ubar))';
end
states=delta+repmat(model.xbar',N,1);
end
