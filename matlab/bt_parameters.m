function p = bt_parameters()
%BT_PARAMETERS Explicit teaching specification for the corrected tank.
% Time: min; mass flows: kg/min; density: kg/m^3; volume: m^3.
% State [X;V]; input [w1;w2;x1;x2;wout]. Fractions are dimensionless.
% Density is a declared choice, not recovered from historical coefficients.
p=struct('rho',1000,'min_volume',1e-6,'Vbar',2,...
 'ubar',[500;200;.4;.75;700]);
p.xbar=bt_equilibrium(p.ubar,p.Vbar,p);
p.state_names={'solute mass fraction','volume'};
p.input_names={'w1','w2','x1','x2','wout'};
p.input_units={'kg/min','kg/min','1','1','kg/min'};
p.state_units={'1','m^3'};
end
