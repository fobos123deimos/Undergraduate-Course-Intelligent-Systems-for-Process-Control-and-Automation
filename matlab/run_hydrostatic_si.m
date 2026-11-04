function result = run_hydrostatic_si(dt)
% Six-second SI example with explicit, unverified Table 5 interpretations.
% Data are simulated. The literal 2014 Eq.35 implementation is separate.
if nargin<1, dt=.002; end
if ~isnumeric(dt) || ~isreal(dt) || ~isscalar(dt) || ~isfinite(dt) || ...
        dt<=0 || dt>.01 || abs(6/dt-round(6/dt))>1e-8
    error('hydrostatic:step','dt must be in (0,.01] and divide six seconds.');
end
p=hydrostatic_si_parameters('per_revolution','effective');
wp=180; load=5000; ap=.25; am=.8;
ratio=p.gear_ratio*p.axle_ratio;
damping=p.cardan_damping_nm_s/p.gear_ratio^2;
dm=p.motor_m3_per_rad*am; eta=p.gearbox_efficiency*p.motor_efficiency;
q=p.pump_m3_per_rad*ap*wp;
omega=(q-p.leakage_m3_per_s_pa*load/(ratio*eta*dm))/ ...
    (dm+p.leakage_m3_per_s_pa*damping/(eta*dm));
pressure=(damping*omega+load/ratio)/(eta*dm);
t=(0:round(6/dt))'*dt; x=zeros(numel(t),4); commands=zeros(numel(t),2);
x(1,:)=[ap am pressure omega];
for k=1:numel(t)-1
    z=x(k,:)'; tk=t(k);
    k1=hydrostatic_si(z,command_at(tk),wp,load,p);
    k2=hydrostatic_si(z+dt*k1/2,command_at(tk+dt/2),wp,load,p);
    k3=hydrostatic_si(z+dt*k2/2,command_at(tk+dt/2),wp,load,p);
    k4=hydrostatic_si(z+dt*k3,command_at(tk+dt),wp,load,p);
    x(k+1,:)=(z+dt*(k1+2*k2+2*k3+k4)/6)';
end
residual=zeros(numel(t),1); valid=true;
for k=1:numel(t)
    commands(k,:)=command_at(t(k))';
    [~,power]=hydrostatic_si(x(k,:),commands(k,:),wp,load,p);
    residual(k)=power.balance_residual_w; valid=valid && power.motoring_valid;
end
report=struct('model','separate_si_interpretation','data_kind','simulated_demonstration', ...
    'displacement_basis','per_revolution','capacitance_basis','effective', ...
    'input_contract','requested_normalized_angles; no voltage/current calibration', ...
    'parameters',p,'dt_s',dt,'duration_s',6,'samples',numel(t), ...
    'max_abs_power_balance_residual_w',max(abs(residual)), 'all_motoring',valid, ...
    'pressure_min_pa',min(x(:,3)),'pressure_max_pa',max(x(:,3)), ...
    'motor_speed_min_rad_s',min(x(:,4)),'motor_speed_max_rad_s',max(x(:,4)), ...
    'final_state',x(end,:), ...
    'limitations',{{'not a replication of IEEE 2007 numerical results', ...
    'unresolved Table 5 conventions are explicit choices', ...
    'constant efficiencies restricted to motoring', ...
    'no relief valves, cavitation or actuator power model'}});
result=struct('t',t,'x',x,'command',commands,'report',report);
end

function u=command_at(t)
u=[.25;.8];
if t>1 && t<5, u(1)=u(1)+.04*sin(pi*(t-1)/4)^2; end
end
