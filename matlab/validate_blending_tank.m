function checks = validate_blending_tank()
%VALIDATE_BLENDING_TANK Independent balances, derivatives and exact solutions.
% Requires base MATLAB or GNU Octave; no Control System Toolbox is needed.
p=bt_parameters();u=p.ubar;x=bt_equilibrium(u,2,p);
assert(norm(x-[.5;2],Inf)<1e-14);
assert(norm(bt_rhs(0,x,u,p),Inf)<1e-14);
checks.equilibrium=true;

% Differentiate total/solute inventories, independently of concentration form.
states=[.1 1.2;.4 2.3;.9 .7];feeds=[500 200 .4 .75 650;100 400 .1 .8 700;0 50 .2 .6 25];
for j=1:size(states,1)
 xj=states(j,:)';uj=feeds(j,:)';f=bt_rhs(0,xj,uj,p);
 assert(abs(p.rho*f(2)-(uj(1)+uj(2)-uj(5)))<1e-10);
 solute_rate=p.rho*(xj(2)*f(1)+xj(1)*f(2));
 assert(abs(solute_rate-(uj(1)*uj(3)+uj(2)*uj(4)-uj(5)*xj(1)))<1e-10);
end
checks.conservation=true;

% Centered finite differences verify every column, including off-equilibrium A12.
xj=[.3;1.7];uj=[450;170;.2;.8;590];m=bt_linearize(xj,uj,p,false);
An=zeros(2);Bn=zeros(2,5);
for j=1:2
 h=1e-5*max(1,abs(xj(j)));v=zeros(2,1);v(j)=h;
 An(:,j)=(bt_rhs(0,xj+v,uj,p)-bt_rhs(0,xj-v,uj,p))/(2*h);
end
for j=1:5
 h=1e-5*max(1,abs(uj(j)));v=zeros(5,1);v(j)=h;
 Bn(:,j)=(bt_rhs(0,xj,uj+v,p)-bt_rhs(0,xj,uj-v,p))/(2*h);
end
assert(norm(An-m.A,Inf)<1e-9 && norm(Bn-m.B,Inf)<1e-9);
assert(norm(m.fbar-bt_rhs(0,xj,uj,p),Inf)<1e-14 && ~m.is_equilibrium);
assert(abs(m.A(1,2))>1e-4 && isempty(m.transfer_num));
must_fail(@()bt_linearize(xj,uj,p));
checks.jacobians=true;

% Exact equilibrium matrices and resolvent independently audit all transfers.
m=bt_linearize(p.xbar,u,p);
assert(norm(m.A-[-.35 0;0 0],Inf)<1e-14);
Bexact=[-.00005 .000125 .25 .1 0;.001 .001 0 0 -.001];
assert(norm(m.B-Bexact,Inf)<1e-14);
assert(m.transfer_num{1,1}<0 && m.transfer_num{1,2}>0);
for s=[.2+.7i,1+2i,3]
 G=(s*eye(2)-m.A)\m.B;
 for row=1:2
  for col=1:5
   value=polyval(m.transfer_num{row,col},s)/polyval(m.transfer_den{row,col},s);
   assert(abs(G(row,col)-value)<1e-12);
  end
 end
end
checks.transfer_consistency=true;

% Three closed-form concentration laws test the numerical ODE trajectory.
t=(0:.25:15)';balanced=bt_simulate(t,[0;2],u,p);
expected=.5*(1-exp(-.35*t));
assert(max(abs(balanced.x(:,1)-expected))<1e-8);
assert(max(abs(balanced.x(:,2)-2))<1e-12);
uf=u;uf(5)=650;filling=bt_simulate(t,[0;2],uf,p);
V=2+.05*t;expected=.5*(1-(2./V).^14);
assert(max(abs(filling.x(:,1)-expected))<1e-8);
assert(max(abs(filling.x(:,2)-V))<1e-10);
td=(0:.1:3)';ud=u;ud(5)=1000;draining=bt_simulate(td,[.3;2],ud,p);
V=2-.3*td;expected=.5+(.3-.5)*(2./V).^(-7/3);
assert(max(abs(draining.x(:,1)-expected))<1e-8);
assert(max(abs(draining.x(:,2)-V))<1e-10);
assert(all(draining.x(:,1)>=0 & draining.x(:,1)<=1));
checks.analytical_trajectories=true;

% Emptying is rejected before integration; zero inflow keeps composition fixed.
must_fail(@()bt_simulate([0;7],[.3;2],ud,p));
no_feed=bt_simulate([0;1;2],[.4;2],[0;0;.2;.8;100],p);
assert(max(abs(no_feed.x(:,1)-.4))<1e-12);
assert(max(abs(no_feed.x(:,2)-[2;1.9;1.8]))<1e-10);
must_fail(@()bt_equilibrium([0;0;.2;.8;0],2,p));
must_fail(@()bt_equilibrium(uf,2,p));
must_fail(@()bt_rhs(0,[.2;0],u,p));
must_fail(@()bt_rhs(0,[.2;2],u,struct('rho',0)));
must_fail(@()bt_rhs(0,[NaN;2],u,p));
bad=u;bad(1)=-1;must_fail(@()bt_rhs(0,x,bad,p));
bad=u;bad(3)=1.1;must_fail(@()bt_rhs(0,x,bad,p));
must_fail(@()bt_simulate([0;1;1],x,u,p));
must_fail(@()bt_simulate([0;1;2],x,zeros(3,5),p));
checks.physical_domain=true;

% A genuine small-perturbation linearization gives second-order residuals.
result=run_blending_tank(false);
ratios=result.max_concentration_errors(1:end-1)./result.max_concentration_errors(2:end);
assert(all(ratios>3.6 & ratios<4.2));
assert(max(abs(result.perturbed.x(:,2)-result.linear_states(:,2)))<1e-10);
assert(abs(result.filling.x(end,2)-3.5)<1e-10);
assert(result.perturbed.x(end,1)<.5);
checks.local_linearization=true;
fprintf('Seven corrected Blending Tank check groups passed.\n');
end

function must_fail(fun)
failed=false;
try,fun();catch,failed=true;end
assert(failed,'Expected invalid physical input or incompatible model to fail.');
end
