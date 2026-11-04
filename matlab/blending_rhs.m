function dx = blending_rhs(~, x, p)
%BLENDING_RHS Constant-density, perfectly mixed variable-volume tank.
% State x = [solute mass fraction; volume / m^3].
% Mass flows w1,w2,wout in kg/time; rho in kg/m^3.
if x(2)<=0 || p.rho<=0,error('Positive volume and density are required.');end
if any([p.w1 p.w2 p.wout]<0),error('Mass flows must be nonnegative.');end
dx=[(p.w1*(p.x1-x(1))+p.w2*(p.x2-x(1)))/(p.rho*x(2));...
    (p.w1+p.w2-p.wout)/p.rho];
end
