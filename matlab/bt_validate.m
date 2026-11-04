function [x,u,p] = bt_validate(x,u,p)
%BT_VALIDATE Shared physical-domain checks without clipping the state.
if nargin<3,p=bt_parameters();end
if ~isstruct(p)||~isscalar(p)||~isfield(p,'rho')
 error('bt:parameters','Parameters must contain scalar density rho.');
end
if ~isfield(p,'min_volume'),p.min_volume=1e-6;end
if ~isnumeric(p.rho)||~isreal(p.rho)||~isscalar(p.rho)||~isfinite(p.rho)||p.rho<=0
 error('bt:density','Density must be finite and positive.');
end
if ~isnumeric(p.min_volume)||~isreal(p.min_volume)||~isscalar(p.min_volume)||~isfinite(p.min_volume)||p.min_volume<=0
 error('bt:volumeFloor','Minimum volume must be finite and positive.');
end
if ~isnumeric(x)||~isreal(x)||~isvector(x)||numel(x)~=2||any(~isfinite(x(:)))
 error('bt:state','State must be a finite real [X;V] vector.');
end
if ~isnumeric(u)||~isreal(u)||~isvector(u)||numel(u)~=5||any(~isfinite(u(:)))
 error('bt:input','Input must be finite [w1;w2;x1;x2;wout].');
end
x=x(:);u=u(:);
if x(1)<0||x(1)>1,error('bt:fraction','State mass fraction must lie in [0,1].');end
if x(2)<=p.min_volume,error('bt:volume','Volume must exceed the declared positive minimum.');end
if any(u([1 2 5])<0),error('bt:flow','Mass flows must be nonnegative.');end
if any(u([3 4])<0)||any(u([3 4])>1)
 error('bt:feedFraction','Feed mass fractions must lie in [0,1].');
end
end
