function [dx,power] = hydrostatic_si(x,command,pump_speed,wheel_load,p)
% Separate SI model. x=[normalized angles; delta-p Pa; motor speed rad/s].
% command specifies requested normalized angles, not valve voltage/current.
% Source and unresolved choices: benchmarks/HYDROSTATIC_SOURCE_REVIEW.md.
% Efficiencies describe motoring; power.motoring_valid flags back-driving.
if nargin~=5 || ~isstruct(p) || ~isscalar(p)
    error('hydrostatic:input','An explicit parameter struct is required.');
end
required={'pump_m3_per_rad','motor_m3_per_rad','capacitance_m3_per_pa', ...
    'leakage_m3_per_s_pa','vehicle_inertia_kg_m2','cardan_damping_nm_s', ...
    'gear_ratio','axle_ratio','gearbox_efficiency','motor_efficiency', ...
    'pump_time_constant_s','motor_time_constant_s'};
if ~all(isfield(p,required)), error('hydrostatic:input','Missing parameter.'); end
for k=1:numel(required)
    name=required{k}; value=p.(name);
    if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value)
        error('hydrostatic:input','Parameters must be real finite scalars.');
    end
    if any(strcmp(name,{'gear_ratio','axle_ratio'}))
        if value==0, error('hydrostatic:input','Ratios must be nonzero.'); end
    elseif any(strcmp(name,{'leakage_m3_per_s_pa','cardan_damping_nm_s'}))
        if value<0, error('hydrostatic:input','Loss coefficients must be nonnegative.'); end
    elseif value<=0, error('hydrostatic:input','Parameter must be positive.');
    end
end
if p.gearbox_efficiency>1 || p.motor_efficiency>1
    error('hydrostatic:input','Efficiencies must lie in (0,1].');
end
if ~isnumeric(x) || ~isreal(x) || ~isvector(x) || numel(x)~=4 || any(~isfinite(x(:))) || ...
   ~isnumeric(command) || ~isreal(command) || ~isvector(command) || numel(command)~=2 || any(~isfinite(command(:)))
    error('hydrostatic:input','Invalid state or command vector.');
end
if ~isnumeric(pump_speed) || ~isreal(pump_speed) || ~isscalar(pump_speed) || ~isfinite(pump_speed) || ...
   ~isnumeric(wheel_load) || ~isreal(wheel_load) || ~isscalar(wheel_load) || ~isfinite(wheel_load)
    error('hydrostatic:input','Speed and load must be real finite scalars.');
end
x=x(:); command=command(:);
if abs(x(1))>1 || x(2)<0 || x(2)>1 || abs(command(1))>1 || command(2)<0 || command(2)>1
    error('hydrostatic:input','Pump angles/commands require [-1,1]; motor requires [0,1].');
end
ratio=p.gear_ratio*p.axle_ratio;
inertia=p.vehicle_inertia_kg_m2/ratio^2;
damping=p.cardan_damping_nm_s/p.gear_ratio^2;
eta=p.gearbox_efficiency*p.motor_efficiency;
qp=p.pump_m3_per_rad*x(1)*pump_speed;
qm=p.motor_m3_per_rad*x(2)*x(4);
torque=eta*p.motor_m3_per_rad*x(2)*x(3);
dx=[(command(1)-x(1))/p.pump_time_constant_s; ...
    (command(2)-x(2))/p.motor_time_constant_s; ...
    (qp-qm-p.leakage_m3_per_s_pa*x(3))/p.capacitance_m3_per_pa; ...
    (torque-damping*x(4)-wheel_load/ratio)/inertia];
if nargout>1
    port=x(3)*qm; leak=p.leakage_m3_per_s_pa*x(3)^2;
    conversion=(1-eta)*port; friction=damping*x(4)^2;
    load_power=wheel_load*x(4)/ratio;
    rate=p.capacitance_m3_per_pa*x(3)*dx(3)+inertia*x(4)*dx(4);
    input_power=x(3)*qp;
    power=struct('stored_energy_j',.5*(p.capacitance_m3_per_pa*x(3)^2+inertia*x(4)^2), ...
        'hydraulic_input_w',input_power,'motor_hydraulic_power_w',port, ...
        'load_power_w',load_power,'leakage_loss_w',leak, ...
        'conversion_loss_w',conversion,'damping_loss_w',friction, ...
        'stored_energy_rate_w',rate, ...
        'balance_residual_w',rate-(input_power-load_power-leak-conversion-friction), ...
        'motoring_valid',port>=0 || eta==1);
end
end
