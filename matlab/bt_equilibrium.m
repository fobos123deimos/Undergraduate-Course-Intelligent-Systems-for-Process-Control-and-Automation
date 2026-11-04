function xbar = bt_equilibrium(ubar,Vbar,p)
%BT_EQUILIBRIUM Require a balanced mass flow before assigning equilibrium.
if nargin<3,p=bt_parameters();end
[~,ubar,p]=bt_validate([.5;Vbar],ubar,p);
inlet=ubar(1)+ubar(2);
if inlet<=0,error('bt:equilibrium','Positive inlet flow is needed for a unique concentration equilibrium.');end
tolerance=64*eps*max([1,inlet,ubar(5)]);
if abs(inlet-ubar(5))>tolerance
 error('bt:equilibrium','The inlet and outlet mass flows must balance at a fixed-volume equilibrium.');
end
xbar=[(ubar(1)*ubar(3)+ubar(2)*ubar(4))/inlet;Vbar];
end
