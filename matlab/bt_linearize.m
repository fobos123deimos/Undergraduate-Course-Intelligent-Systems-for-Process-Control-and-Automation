function model = bt_linearize(xbar,ubar,p,require_equilibrium)
%BT_LINEARIZE Jacobians at one common point, with its affine offset.
% At equilibrium: delta_x_dot=A*delta_x+B*delta_u, x=xbar+delta_x.
% Else: x_dot=fbar+A*(x-xbar)+B*(u-ubar), locally at a frozen point.
if nargin<3,p=bt_parameters();end
if nargin<4,require_equilibrium=true;end
if ~isscalar(require_equilibrium)||~isreal(require_equilibrium)||...
   ~(require_equilibrium==0||require_equilibrium==1)
 error('bt:option','require_equilibrium must be a scalar logical value.');
end
[xbar,ubar,p]=bt_validate(xbar,ubar,p);
fbar=bt_rhs(0,xbar,ubar,p);k=1/(p.rho*xbar(2));
A=[-(ubar(1)+ubar(2))*k,-fbar(1)/xbar(2);0,0];
B=[(ubar(3)-xbar(1))*k,(ubar(4)-xbar(1))*k,ubar(1)*k,ubar(2)*k,0;...
 1/p.rho,1/p.rho,0,0,-1/p.rho];
tol=64*eps*max([1;ubar([1 2 5]);ubar(1)+ubar(2)]);
steady=abs(ubar(1)+ubar(2)-ubar(5))<=tol && ...
 abs(ubar(1)*(ubar(3)-xbar(1))+ubar(2)*(ubar(4)-xbar(1)))<=tol;
if require_equilibrium&&~steady
 error('bt:linearization','A deviation model without affine forcing requires an equilibrium point.');
end
model=struct('A',A,'B',B,'C',eye(2),'D',zeros(2,5),'fbar',fbar,...
 'xbar',xbar,'ubar',ubar,'is_equilibrium',steady,'rho',p.rho);
model.transfer_num={};model.transfer_den={};
if steady
 % Reduced zero-initial-deviation transfer functions: output delta X/delta V.
 model.transfer_num=cell(2,5);model.transfer_den=cell(2,5);
 for j=1:5
  if B(1,j)==0,model.transfer_num{1,j}=0;model.transfer_den{1,j}=1;
  else,model.transfer_num{1,j}=B(1,j);model.transfer_den{1,j}=[1,-A(1,1)];end
  if B(2,j)==0,model.transfer_num{2,j}=0;model.transfer_den{2,j}=1;
  else,model.transfer_num{2,j}=B(2,j);model.transfer_den{2,j}=[1,0];end
 end
end
end
