function [u,info] = mpc_control(A,B,x,reference,H,Nc,rho,previous,options)
%MPC_CONTROL Toolbox-free constrained quadratic MPC with explicit failure hold.
% x(k+1)=A*x(k)+B*u(k)+affine. Outputs are the measured full state.
% Input, move and optional predicted-output bounds are hard constraints.
% The final optimized move is held after Nc through the prediction horizon.
% On solver failure, return previous (which must satisfy actuator bounds).
% Holding an input does NOT guarantee future output feasibility or stability.
if nargin<9,options=struct();end
x=x(:);reference=reference(:);previous=previous(:);nx=numel(x);nu=size(B,2);
assert(isequal(size(A),[nx nx]) && size(B,1)==nx && nu>=1,'Invalid model dimensions');
assert(numel(reference)==nx && numel(previous)==nu,'Invalid state/reference/input size');
assert(all(isfinite([A(:);B(:);x;reference;previous])),'Finite model data required');
assert(isscalar(H) && H==fix(H) && H>=1 && isscalar(Nc) && Nc==fix(Nc) && Nc>=1 && Nc<=H,'Invalid horizons');
assert(isscalar(rho) && isfinite(rho) && rho>=0,'Nonnegative finite move weight required');
lo=vector_option(options,'lower',0,nu);hi=vector_option(options,'upper',1,nu);
du=vector_option(options,'max_move',.08,nu);
affine=vector_option(options,'affine',0,nx);
ylo=vector_option(options,'output_lower',-Inf,nx);yhi=vector_option(options,'output_upper',Inf,nx);
weight=option(options,'state_weight',1);tol=option(options,'tolerance',1e-8);
maxiter=option(options,'max_iterations',3000);
assert(all(isfinite([lo;hi;affine])) && all(lo<hi),'Invalid actuator/affine values');
assert(all(du>0) && ~any(isnan(du)),'Positive move bounds required');
assert(all(ylo<yhi) && ~any(isnan([ylo;yhi])),'Invalid output bounds');
assert(all(previous>=lo & previous<=hi),'Previous input violates actuator bounds');
assert(isscalar(weight) && isfinite(weight) && weight>0,'Positive state weight required');
assert(isscalar(tol) && isfinite(tol) && tol>0,'Positive tolerance required');
assert(isscalar(maxiter) && maxiter==fix(maxiter) && maxiter>=0,'Invalid iteration limit');
F=zeros(H*nx,nx);G=zeros(H*nx,Nc*nu);offset=zeros(H*nx,1);op=zeros(nx,1);
for i=1:H
 rows=(i-1)*nx+(1:nx);F(rows,:)=A^i;op=A*op+affine;offset(rows)=op;
 for j=1:i
  column=min(j,Nc);cols=(column-1)*nu+(1:nu);
  G(rows,cols)=G(rows,cols)+A^(i-j)*B;
 end
end
E=eye(Nc*nu);
for j=2:Nc,E((j-1)*nu+(1:nu),(j-2)*nu+(1:nu))=-eye(nu);end
anchor=[previous;zeros((Nc-1)*nu,1)];base=F*x+offset;target=repmat(reference,H,1);
Q=weight*(G'*G)+rho*(E'*E);c=weight*G'*(base-target)-rho*E'*anchor;
% Minimize 0.5*z'*Q*z+c'*z; its minimizer equals the reported tracking cost.
lower=repmat(lo,Nc,1);upper=repmat(hi,Nc,1);moves=repmat(du,Nc,1);
C=[eye(Nc*nu);-eye(Nc*nu);E;-E;G;-G];
d=[upper;-lower;moves+anchor;moves-anchor;repmat(yhi,H,1)-base;base-repmat(ylo,H,1)];
finite=isfinite(d);C=C(finite,:);d=d(finite);
[candidate,diagnostic]=solve_dual(Q,c,C,d,lower,upper,tol,maxiter);
success=diagnostic.success;
if success
 % Remove only actuator roundoff, then recheck all coupled constraints.
 candidate=min(upper,max(lower,candidate));
 if max([0;C*candidate-d])>10*tol,success=false;diagnostic.success=false;diagnostic.status='postcheck_failure';end
end
if success,plan=candidate;u=plan(1:nu);else,plan=repmat(previous,Nc,1);u=previous;end
predicted=reshape(base+G*plan,nx,H)';
violations=C*plan-d;
info=diagnostic;info.held_previous=~success;info.planned_inputs=reshape(plan,nu,Nc)';
info.predicted_outputs=predicted;info.moves=reshape(E*plan-anchor,nu,Nc)';
info.applied_plan_max_violation=max([0;violations]);
info.cost=weight*sum((base+G*plan-target).^2)+rho*sum((E*plan-anchor).^2);
end

function [z,info]=solve_dual(Q,c,C,d,lower,upper,tol,maxiter)
% Hildreth/Dykstra dual coordinate minimization for a strictly convex QP.
% z=-Q\(c+C'*lambda), lambda>=0. Every coordinate update preserves stationarity.
n=numel(c);z=zeros(n,1);lambda=zeros(size(d));
info=struct('success',false,'status','iteration_limit_or_infeasible','iterations',0,...
 'max_constraint_violation',Inf,'stationarity_residual',Inf,'complementarity_residual',Inf);
minimum=sum(max(C,0).*lower'+min(C,0).*upper',2);
if any(minimum>d+tol),info.status='infeasible_constraint';return;end
[~,flag]=chol((Q+Q')/2);
if flag~=0,info.status='non_positive_definite_objective';return;end
z=-Q\c;directions=Q\C';diagonal=sum(C.*directions',2);
for sweep=0:maxiter
 slack=d-C*z;primal=max([0;-slack]);
 stationarity=norm(Q*z+c+C'*lambda,Inf);
 complementary=max([0;abs(lambda.*slack)])/max(1,norm(lambda,Inf));
 info.iterations=sweep;info.max_constraint_violation=primal;
 info.stationarity_residual=stationarity;info.complementarity_residual=complementary;
 if all(isfinite(z)) && primal<=tol && stationarity<=tol*max(1,norm(c,Inf)) && complementary<=tol
  info.success=true;info.status='optimal';return;
 end
 if sweep==maxiter,break;end
 for j=1:numel(d)
  if diagonal(j)<=eps,continue;end
  next=max(0,lambda(j)+(C(j,:)*z-d(j))/diagonal(j));delta=next-lambda(j);
  if delta~=0,z=z-directions(:,j)*delta;lambda(j)=next;end
 end
end
end

function value=option(options,name,fallback)
if isfield(options,name),value=options.(name);else,value=fallback;end
end
function value=vector_option(options,name,fallback,n)
value=option(options,name,fallback);value=value(:);
if isscalar(value),value=repmat(value,n,1);end
assert(isnumeric(value) && numel(value)==n,['Invalid option ' name]);
end
