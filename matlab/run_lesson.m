function result = run_lesson(unit, make_plots)
%RUN_LESSON Nine toolbox-free process-control laboratories.
%   result = run_lesson(1);  run_lesson(9, true)
%   MATLAB and GNU Octave use identical equations. Random streams can differ.
if nargin < 2, make_plots = false; end
if isequal(unit,9),result=run_markov_lab(make_plots);return;end
rng(42, 'twister');
dt = 0.2; tau = 10;
a = exp(-dt/tau); b = 1-a;
t = (0:dt:80)'; r = 0.35 + 0.30*(t>=10) - 0.20*(t>=55);
d = 0.08*(t>=45);
result = struct('unit',unit);
switch unit
 case 1
  % Exact ZOH mass balance, separate training and validation experiments.
  u = kron(rand(80,1),ones(5,1)); u = [u;u(end)];
  y = filter(b,[1 -a],[0;u(1:end-1)]);
  theta = [y(1:end-1) u(1:end-1)]\y(2:end);
  av=theta(1); bv=theta(2);
  uv=0.5+0.3*sin(t/7); truth=zeros(size(t)); pred=truth;
  for k=1:numel(t)-1
   truth(k+1)=a*truth(k)+b*uv(k);
   pred(k+1)=av*pred(k)+bv*uv(k);
  end
  % The corrected independent physical model uses declared mass-flow inputs.
  p=struct('rho',1000,'w1',500,'w2',200,'wout',700,'x1',0.4,'x2',0.75);
  xeq=(p.w1*p.x1+p.w2*p.x2)/(p.w1+p.w2);
  dx=blending_rhs(0,[xeq;2],p);
  assert(norm(dx)<1e-12);
  assert(max(abs(theta-[a;b]))<1e-11);
  result.parameters=theta; result.estimated_tau=-dt/log(av);
  result.validation_rmse=sqrt(mean((truth-pred).^2));
  assert(result.validation_rmse<1e-10);
  result.t=t; result.y=truth; result.pred=pred;
 case 2
  % IMC PI: Kp=tau/(lambda+delay), Ki=Kp/tau, K=1.
  lambda=5; delay=0; kp=tau/(lambda+delay); ki=kp/tau;
  A=[a-b*kp b; -ki*dt 1];
  assert(max(abs(eig(A)))<1);
  result.pi=closed_loop('pi',t,r,d,a,b,[kp ki 0]);
  result.pid=closed_loop('pid',t,r,d,a,b,[kp ki .3]);
  result.gains=[kp ki]; result.closed_loop_eigenvalues=eig(A);
  result.t=t; result.y=result.pi.y; result.reference=r;
  assert(abs(result.pi.y(end)-r(end))<.02);
 case 3
  K=[1 .4;.3 1.2]; RGA=K.*inv(K)';
  D=inv(K); assert(norm(K*D-eye(2))<1e-12);
  assert(max(abs(sum(RGA,2)-1))<1e-12);
  result.feedback=closed_loop('pi',t,r,d,a,b,[2 .2 0]);
  result.feedforward=closed_loop('feedforward',t,r,d,a,b,[2 .2 0]);
  % Cascade: fast actuator loop is inside concentration loop.
  n=numel(t); y=zeros(n,1); v=y; u=y; y(1)=.35;v(1)=.35;I=.35;J=.35;
  for k=1:n-1
   e=r(k)-y(k); target=clip(2*e+I,0,1); I=I+.2*dt*e;
   ev=target-v(k); raw=4*ev+J; u(k)=clip(raw,0,1);
   J=J+dt*(2*ev+2*(u(k)-raw));
   v(k+1)=exp(-dt)*v(k)+(1-exp(-dt))*u(k);
   y(k+1)=a*y(k)+b*(v(k)+d(k));
  end
  result.cascade=struct('y',y,'u',u,'inner_output',v);
  result.gain_matrix=K; result.rga=RGA; result.decoupler=D;
  % Compare two interacting loops on the same 2x2 plant and reference.
  % The transform uses applied actuator commands in anti-windup feedback.
  result.decentralized=multiloop_response(t,K,false);
  result.decoupled=multiloop_response(t,K,true);
  result.t=t; result.y=result.feedforward.y; result.reference=r;
  assert(all(v>=-eps & v<=1+eps));
 case 4
  result.siso=closed_loop('mpc',t,r,d,a,b,[2 .2 0]);
  % 2x2 constrained receding horizon control, H=12, Nc=4.
  A=diag([.96 .94]); B=[.04 .012;.01 .05];
  x=[0;0]; logx=zeros(101,2); logu=zeros(100,2); up=[0;0];failures=0;max_violation=0;
  constraints=struct('max_move',.08,'output_lower',0,'output_upper',.65);
  for k=1:100
   target=[.4;.5]; [u,info]=mpc_control(A,B,x,target,12,4,.15,up,constraints);
   failures=failures+~info.success;max_violation=max(max_violation,info.applied_plan_max_violation);
   x=A*x+B*u; logx(k+1,:)=x'; logu(k,:)=u'; up=u;
  end
  result.mimo=struct('states',logx,'inputs',logu,'last_solver',info,...
   'solver_failures',failures,'max_constraint_violation',max_violation,'constraints',constraints);
  assert(all(logu(:)>=-1e-10 & logu(:)<=1+1e-10));
  assert(max(max(abs(diff([zeros(1,2);logu]))))<=.08+1e-7);
  assert(all(logx(:)>=-1e-7 & logx(:)<=.65+1e-7) && failures==0);
  assert(norm(logx(end,:)'-target)<.03);
  result.t=t; result.y=result.siso.y; result.reference=r;
 case 5
  result.sugeno=closed_loop('fuzzy',t,r,d,a,b,[2 .2 0]);
  result.fuzzy_pi=closed_loop('fuzzy_pi',t,r,d,a,b,[2 .2 0]);
  result.fuzzy_pid=closed_loop('fuzzy_pid',t,r,d,a,b,[2 .2 0]);
  egrid=linspace(-1,1,101); curve=zeros(size(egrid));
  for k=1:numel(curve),curve(k)=mamdani(egrid(k),0);end
  assert(abs(mamdani(0,0))<1e-12);
  assert(mamdani(.8,0)>0 && mamdani(-.8,0)<0);
  result.mamdani_curve=[egrid' curve'];
  result.rules={diagnose(.9,1,.02),diagnose(.2,.5,.4),diagnose(.2,.5,.01)};
  result.t=t; result.y=result.fuzzy_pid.y; result.reference=r;
 case 6
  % Supervised learning uses distinct random training and test samples.
  X=rand(500,2); target=a*X(:,1)+b*X(:,2)+.015*sin(3*X(:,1)).*X(:,2);
  Xt=rand(200,2); yt=a*Xt(:,1)+b*Xt(:,2)+.015*sin(3*Xt(:,1)).*Xt(:,2);
  % Perceptron classifies a linearly separable operating region.
  labels=2*(sum(X,2)>1)-1; W=zeros(3,1);
  for epoch=1:30
   for k=1:size(X,1)
    z=[1 X(k,:)]'; if labels(k)*(W'*z)<=0,W=W+.1*labels(k)*z;end
   end
  end
  result.perceptron_accuracy=mean((([ones(size(Xt,1),1) Xt]*W)>0)==(sum(Xt,2)>1));
  % MLP: one tanh hidden layer, full-batch gradient descent.
  W1=.5*randn(3,12); W2=.1*randn(13,1); XX=[ones(size(X,1),1) X];
  for epoch=1:2500
   H=tanh(XX*W1); HB=[ones(size(H,1),1) H]; err=HB*W2-target;
   g2=HB'*err/size(X,1); g1=XX'*((err*W2(2:end)').*(1-H.^2))/size(X,1);
   W2=W2-.15*g2; W1=W1-.15*g1;
  end
  pred=[ones(size(Xt,1),1) tanh([ones(size(Xt,1),1) Xt]*W1)]*W2;
  result.mlp_rmse=sqrt(mean((pred-yt).^2));
  centers=X(1:25,:); Phi=rbf_features(X,centers,.3);
  weights=(Phi'*Phi+1e-8*eye(size(Phi,2)))\(Phi'*target);
  predR=rbf_features(Xt,centers,.3)*weights;
  result.rbf_rmse=sqrt(mean((predR-yt).^2));
  models=struct('mlp',struct('kind','mlp','W1',W1,'W2',W2),...
   'rbf',struct('kind','rbf','centers',centers,'width',.3,'weights',weights));
  % Fixed models are evaluated on a fresh complete trajectory. One-step
  % prediction uses measured history; recursive free run uses predictions.
  tv=(0:dt:40)';uv=.3+.15*sin(tv(1:end-1)/3)+.05*sin(tv(1:end-1)/1.1);
  actual=zeros(size(tv));actual(1)=.25;
  for k=1:numel(uv),actual(k+1)=a*actual(k)+b*uv(k)+.015*sin(3*actual(k))*uv(k);end
  % Deliberately outside training [0,1]^2; no fitting or parameter selection
  % uses these points, their targets, or the independent trajectory.
  ood=[linspace(1.2,1.6,101)' linspace(1.1,1.4,101)'];
  ood_truth=a*ood(:,1)+b*ood(:,2)+.015*sin(3*ood(:,1)).*ood(:,2);
  validation=struct('time',tv,'inputs',uv,'truth',actual,'training_domain',[0 1;0 1],...
   'ood_inputs',ood,'ood_truth',ood_truth);
  for family={'mlp','rbf'}
   name=family{1};model=models.(name);
   step=neural_predict(model,[actual(1:end-1) uv]);free=neural_rollout(model,uv,actual(1));
   outside=neural_predict(model,ood);
   validation.(name)=struct('one_step',step,'free_run',free,'ood_prediction',outside,...
    'one_step_rmse',sqrt(mean((step-actual(2:end)).^2)),...
    'free_run_rmse',sqrt(mean((free(2:end)-actual(2:end)).^2)),...
    'ood_rmse',sqrt(mean((outside-ood_truth).^2)));
  end
  result.neural_models=models;result.neural_validation=validation;
  % A 1-D self-organizing map preserves neighborhood topology.
  prototypes=rand(8,2);
  for epoch=1:30
   radius=max(.4,3*(1-epoch/31)); rate=.25*(1-epoch/31);
   for k=1:size(X,1)
    [~,winner]=min(sum((prototypes-X(k,:)).^2,2));
    h=exp(-((1:8)'-winner).^2/(2*radius^2));
    prototypes=prototypes+rate*h.*(X(k,:)-prototypes);
   end
  end
  % Learned forward model inversion with a reachable one-step target.
  yc=zeros(size(t)); uc=yc;
  for k=1:numel(t)-1
   goal=yc(k)+.04*(r(k)-yc(k)); lo=0; hi=1;
   for iter=1:24
    mid=(lo+hi)/2; yp=rbf_features([yc(k) mid],centers,.3)*weights;
    if yp<goal,lo=mid;else,hi=mid;end
   end
   uc(k)=(lo+hi)/2;
   yc(k+1)=a*yc(k)+b*uc(k)+.015*sin(3*yc(k))*uc(k);
  end
  result.som=prototypes; result.t=t; result.y=yc; result.reference=r;
  result.neural_inputs=uc;
  assert(result.mlp_rmse<.06 && result.rbf_rmse<.01);
  assert(result.perceptron_accuracy>.9);
 case 7
  % Both encodings tune the same PI objective and keep an elite.
  tt=(0:.5:45)'; rr=.5*ones(size(tt)); dd=.08*(tt>=25);
  aa=exp(-.5/10); bb=1-aa;
  cost=@(g) controller_cost(g,tt,rr,dd,aa,bb);
  [gr,fr,hr]=genetic_search(cost,'real',24,20);
  [gb,fb,hb]=genetic_search(cost,'binary',24,20);
  assert(all(diff(hr)<=1e-10) && all(diff(hb)<=1e-10));
  result.real=struct('gains',gr,'objective',fr,'history',hr);
  result.binary=struct('gains',gb,'objective',fb,'history',hb);
  % Evolution also selects the move penalty in the 2x2 MPC example.
  penalties=[.02 .08 .2 .5]; costs=zeros(size(penalties));
  for j=1:numel(penalties)
   A=diag([.96 .94]); B=[.04 .012;.01 .05]; x=[0;0]; up=[0;0];
   for k=1:50
    u=mpc_move(A,B,x,[.4;.5],8,3,penalties(j),up);
    x=A*x+B*u; costs(j)=costs(j)+sum((x-[.4;.5]).^2)+.02*sum((u-up).^2); up=u;
   end
  end
  [~,ix]=min(costs); result.mimo_penalty_sweep=[penalties' costs'];
  result.selected_mimo_penalty=penalties(ix);
  result.mimo_mpc_genetic=genetic_mpc_weight();
  assert(all(diff(result.mimo_mpc_genetic.history)<=1e-10));
  result.t=(1:numel(hr))'; result.y=[hr hb];
 case 8
  names={'pi','feedforward','fuzzy_pid','mpc'}; result.controllers=struct;
  result.metrics=zeros(4,4); ys=zeros(numel(t),4);
  for j=1:numel(names)
   q=closed_loop(names{j},t,r,d,a,b,[2 .2 0]); result.controllers.(names{j})=q;
   ys(:,j)=q.y; result.metrics(j,:)=[q.iae q.ise q.total_variation max(abs(q.y-r))];
  end
  result.names=names; result.metric_names={'IAE','ISE','total_variation','max_error'};
  % One common unmeasured plant mismatch, same disturbances and limits.
  result.mismatch=closed_loop('pi',t,r,d,exp(-dt/14),1-exp(-dt/14),[2 .2 0]);
  result.t=t; result.y=ys; result.reference=r;
 otherwise,error('Unit must be an integer from 1 to 9.');
end
if make_plots && isfield(result,'t')
 figure; plot(result.t,result.y,'LineWidth',1.4); grid on;
 xlabel('Time / min (or generation in Unit 7)'); ylabel('Output');
 title(sprintf('Process control: Unit %02d',unit));
end
fprintf('Unit %02d: numerical assertions passed.\n',unit);
end

function q=closed_loop(mode,t,r,d,a,b,g)
dt=t(2)-t(1); n=numel(t); y=zeros(n,1); u=y;y(1)=.35; I=.35; olde=0; oldy=.35; deriv=0; up=.35;
gains=zeros(n,3); derivative_term=zeros(n,1);solver_failures=0;solver_max_violation=0;
for k=1:n-1
 e=r(k)-y(k); de=(e-olde)/dt; kp=g(1); ki=g(2);
 switch mode
  case 'mpc'
   % Known disturbance is included as a constant affine term.
   [u(k),status]=mpc_move(a,b,y(k),r(k),18,5,.08,up,b*d(k));
   solver_failures=solver_failures+~status.success;
   solver_max_violation=max(solver_max_violation,status.applied_plan_max_violation);
  case 'fuzzy'
   raw=I+.5*sugeno(clip(e/.3,-1,1),clip(de/.1,-1,1));
   u(k)=clip(raw,0,1); I=I+dt*(.16*e+.5*(u(k)-raw));
  otherwise
   kd=0; if strcmp(mode,'pid'),kd=g(3);end
   if strcmp(mode,'fuzzy_pid') || strcmp(mode,'fuzzy_pi')
    % Three-set zero-order Sugeno schedule, matching the Python error-only
    % section: singleton consequents [-1,0,1], normalized error e/0.3.
    mu=membership(clip(e/.3,-1,1)); severity=abs(mu*[-1;0;1]/sum(mu));
    kp=1.4+1.2*severity; ki=.14+.08*severity;
    if strcmp(mode,'fuzzy_pid'),kd=.1*severity;end
   end
   ff=0; if strcmp(mode,'feedforward'),ff=-d(k);end
   deriv=deriv+dt/(.5+dt)*((y(k)-oldy)/dt-deriv);
   gains(k,:)=[kp ki kd]; derivative_term(k)=-kd*deriv;
   raw=kp*e+I-kd*deriv+ff; u(k)=clip(raw,0,1);
   I=I+dt*(ki*e+.6*(u(k)-raw));
 end
 y(k+1)=a*y(k)+b*(u(k)+d(k)); olde=e; oldy=y(k);up=u(k);
end
u(end)=u(end-1); error=r-y;
gains(end,:)=gains(end-1,:); derivative_term(end)=derivative_term(end-1);
q=struct('y',y,'u',u,'iae',trapz(t,abs(error)),'ise',trapz(t,error.^2),...
 'total_variation',sum(abs(diff(u))),'gains',gains,'derivative_term',derivative_term,...
 'solver_failures',solver_failures,'solver_max_violation',solver_max_violation);
assert(all(isfinite(y)) && all(u>=0 & u<=1));
end

function q=multiloop_response(t,K,decouple)
% Same gain matrix, initial state, reference and limits for both structures.
dt=t(2)-t(1); A=diag(exp(-dt./[10 15])); B=(eye(2)-A)*K;
n=numel(t); y=zeros(n,2); u=zeros(n,2); reference=zeros(n,2);
x0=K*[.3;.3]; y(1,:)=x0'; target=[.6;.65];
if decouple,I=x0;else,I=[.3;.3];end
for k=1:n-1
 if t(k)<10,rr=x0;else,rr=target;end
 reference(k,:)=rr'; e=rr-y(k,:)'; v=[1.5;1.5].*e+I;
 if decouple,requested=K\v;else,requested=v;end
 applied=clip(requested,0,1); u(k,:)=applied';
 if decouple,tracked=K*applied;else,tracked=applied;end
 I=I+dt*([.15;.1].*e+.6*(tracked-v));
 y(k+1,:)=(A*y(k,:)'+B*applied)';
end
u(end,:)=u(end-1,:); reference(end,:)=reference(end-1,:);
q=struct('states',y,'inputs',u,'reference',reference,...
 'iae',trapz(t,abs(reference-y)),'total_variation',sum(abs(diff(u)),1));
end

function [u,info]=mpc_move(A,B,x,reference,H,Nc,rho,previous,affine)
if nargin<9,affine=zeros(size(x));end
[u,info]=mpc_control(A,B,x,reference,H,Nc,rho,previous,struct('affine',affine,'max_move',.08));
end

function mu=membership(x)
mu=[max(0,-x) max(0,1-abs(x)) max(0,x)];
end
function v=sugeno(e,de)
we=membership(e); wd=membership(de); vals=[-1 -.6 0;-.6 0 .6;0 .6 1];
w=we'*wd; v=sum(sum(w.*vals))/sum(w(:));
end
function v=mamdani(e,de)
we=membership(clip(e,-1,1)); wd=membership(clip(de,-1,1)); z=linspace(-1,1,201);
sets=[max(0,-z);max(0,1-abs(z));max(0,z)]; out=zeros(size(z));
table=[1 1 2;1 2 3;2 3 3];
for i=1:3,for j=1:3,out=max(out,min(min(we(i),wd(j)),sets(table(i,j),:)));end,end
v=trapz(z,z.*out)/trapz(z,out);
end
function message=diagnose(level,command,residual)
if level>.85 && command>.95,message='High level with actuator saturation: inspect demand and outlet';
elseif abs(residual)>.15,message='Model residual alarm: inspect sensor and disturbance';
else,message='Nominal monitored conditions';end
end
function Phi=rbf_features(X,C,width)
Phi=ones(size(X,1),size(C,1)+1);
for j=1:size(C,1),Phi(:,j+1)=exp(-sum((X-C(j,:)).^2,2)/(2*width^2));end
end
function f=controller_cost(g,t,r,d,a,b)
q=closed_loop('pi',t,r,d,a,b,[g 0]);f=q.iae+.05*q.total_variation;
end
function [best,score,history]=genetic_search(cost,encoding,np,ng)
limits=[.2 6;.02 .8]; binary=strcmp(encoding,'binary');
if binary,pop=double(rand(np,20)>.5);else,pop=rand(np,2);end
history=zeros(ng,1);
for generation=1:ng
 genes=decode(pop,binary); realgenes=limits(:,1)'+genes.*(limits(:,2)-limits(:,1))';
 scores=zeros(np,1);for k=1:np,scores(k)=cost(realgenes(k,:));end
 [score,ix]=min(scores);best=realgenes(ix,:);history(generation)=score;
 children=pop(ix,:);
 while size(children,1)<np
  idx=randi(np,2,2); [~,a]=min(scores(idx(:,1)));[~,b]=min(scores(idx(:,2)));
  p=pop(idx(a,1),:);q=pop(idx(b,2),:);
  if binary
   cut=randi(19);child=[p(1:cut) q(cut+1:end)];mask=rand(size(child))<.05;child(mask)=1-child(mask);
  else
   alpha=rand;child=alpha*p+(1-alpha)*q+.12*randn(1,2);child=clip(child,0,1);
  end
  children(end+1,:)=child;
 end
 pop=children;
end
end
function genes=decode(pop,binary)
if ~binary,genes=pop;return;end
weights=2.^(9:-1:0)';genes=[pop(:,1:10)*weights pop(:,11:20)*weights]/1023;
end
function result=genetic_mpc_weight()
% Small, counted evolutionary budget: four members, three evaluations.
population=.001+.499*rand(4,1);history=zeros(3,1);
for generation=1:3
 scores=zeros(4,1);
 for j=1:4
  A=diag([.9 .92]);B=(eye(2)-A)*[1 .3;.2 1];x=[.39;.36];up=[.3;.3];
  for k=1:12
   u=mpc_move(A,B,x,[.65;.6],6,2,population(j),up);x=A*x+B*u;
   scores(j)=scores(j)+sum((x-[.65;.6]).^2)+.02*sum((u-up).^2);up=u;
  end
 end
 [score,index]=min(scores);best=population(index);history(generation)=score;
 if generation==3,break;end
 children=zeros(4,1);children(1)=best;
 for j=2:4
  a=randi(4,2,1);[~,ia]=min(scores(a));b=randi(4,2,1);[~,ib]=min(scores(b));
  alpha=rand;children(j)=clip(alpha*population(a(ia))+(1-alpha)*population(b(ib))+.05*randn,.001,.5);
 end
 population=children;
end
result=struct('move_weight',best,'fitness',score,'history',history,'evaluations',12);
end
function x=clip(x,lo,hi),x=min(hi,max(lo,x));end
