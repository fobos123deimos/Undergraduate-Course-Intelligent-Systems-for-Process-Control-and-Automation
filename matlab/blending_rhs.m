function dx = blending_rhs(t, x, p)
%BLENDING_RHS Compatibility entry point to the corrected physical tank.
% This adapter calls the bt_rhs implementation with the canonical input order.
% State [mass fraction; volume/m^3], flows kg/min, density kg/m^3.
settings=bt_parameters();settings.rho=p.rho;
dx=bt_rhs(t,x,[p.w1;p.w2;p.x1;p.x2;p.wout],settings);
end
