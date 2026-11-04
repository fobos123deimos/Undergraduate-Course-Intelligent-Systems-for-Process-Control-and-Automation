function dx = bt_rhs(~,x,u,p)
%BT_RHS Corrected, independent variable-volume mass and solute balances.
% d(rho*V)/dt=w1+w2-wout; d(rho*V*X)/dt=w1*x1+w2*x2-wout*X.
if nargin<4,p=bt_parameters();end
[x,u,p]=bt_validate(x,u,p);
dx=[(u(1)*(u(3)-x(1))+u(2)*(u(4)-x(1)))/(p.rho*x(2));...
 (u(1)+u(2)-u(5))/p.rho];
end
