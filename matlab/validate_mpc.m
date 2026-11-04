function records=validate_mpc()
%VALIDATE_MPC Independent optima, bounds, prediction timing and failure behavior.
% Analytic one-step optimum intersects actuator and slew limits at u=.5.
[u,a]=mpc_control(.9,.1,.2,.8,1,1,.01,.4,struct('max_move',.1));
assert(a.success && abs(u-.5)<1e-7 && a.max_constraint_violation<1e-7);
% The output constraint is active at u=.2, below the unconstrained optimum.
[v,b]=mpc_control(1,1,0,1,1,1,.05,0,struct('max_move',1,'output_lower',0,'output_upper',.2));
assert(b.success && abs(v-.2)<1e-7);
% Coupled optimum: solve an independent equality-constrained KKT system for
% the known active first-output upper bound and verify positive multiplier.
B=[1 .2;.1 1];r=[.8;.6];previous=[.2;.2];rho=.1;Q=B'*B+rho*eye(2);row=B(1,:);
expected=[2*Q row';row 0]\[2*(B'*r+rho*previous);.52];
assert(expected(3)>0 && all(expected(1:2)>0) && all(expected(1:2)<[.5;.6]));
[w,c]=mpc_control(zeros(2),B,[0;0],r,1,1,rho,previous,...
 struct('max_move',[.3;.4],'output_lower',[0;0],'output_upper',[.52;.8]));
assert(c.success && norm(w-expected(1:2),Inf)<2e-6);
% Prediction timing and tail hold: direct recurrence independent of F/G.
[~,d]=mpc_control([.9 .05;0 .8],[.1;.2],[.2;.3],[.5;.6],6,2,.1,.3,...
 struct('max_move',.07,'affine',[.01;-.02],'output_lower',0,'output_upper',1));
assert(d.success);state=[.2;.3];truth=zeros(6,2);
for k=1:6,state=[.9 .05;0 .8]*state+[.1;.2]*d.planned_inputs(min(k,2),:)+[.01;-.02];truth(k,:)=state';end
assert(norm(truth-d.predicted_outputs,Inf)<1e-12);
assert(max(abs(d.moves(:)))<=.07+1e-7);
% Impossible output constraint: holding the feasible input is explicit, and
% the report admits the output violation instead of returning a false success.
[held,e]=mpc_control(1,0,1,0,2,1,.1,.4,struct('output_lower',0,'output_upper',.1));
assert(~e.success && strcmp(e.status,'infeasible_constraint') && held==.4 && e.held_previous);
assert(e.applied_plan_max_violation>.8);
% Forced solver budget exhaustion must also hold the previous command.
[held,f]=mpc_control(.9,.1,.2,.8,1,1,.01,.4,struct('max_iterations',0,'max_move',.1));
assert(~f.success && held==.4 && f.held_previous);
% Input-domain misuse raises an error; it is not silently clipped.
failed=false;try,mpc_control(1,1,0,1,2,1,.1,1.2);catch,failed=true;end;assert(failed);
records=struct('one_step',u,'output_bound',v,'coupled',w,'infeasible_hold',held,...
 'coupled_kkt_residual',max([c.max_constraint_violation c.stationarity_residual c.complementarity_residual]));
fprintf('Seven MPC constraint, independent-optimum and fallback check groups passed.\n');
end
