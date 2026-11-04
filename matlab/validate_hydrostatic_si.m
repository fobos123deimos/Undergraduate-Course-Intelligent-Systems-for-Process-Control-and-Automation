function report = validate_hydrostatic_si()
% Eight independent validation groups, including a short runnable SI study.
% No measured data or original IEEE 2007 simulation is claimed.
p=hydrostatic_si_parameters('per_revolution','effective');
ratio=p.gear_ratio*p.axle_ratio; inertia=p.vehicle_inertia_kg_m2/ratio^2;
dx=hydrostatic_si([1 0 0 0],[1 0],2*pi,0,p);
assert(abs(dx(3)*p.capacitance_m3_per_pa-145e-6)<1e-18);
q=hydrostatic_si_parameters('per_radian','per_line');
assert(abs(q.motor_m3_per_rad/p.motor_m3_per_rad-2*pi)<1e-14);
assert(q.capacitance_m3_per_pa==p.capacitance_m3_per_pa/2);

% Independently evaluate the corrected equations in bar and mm3/rad.
cases=[.3 .8 100 50 180 5000; -.4 .6 -80 -40 200 -3000; 0 0 0 0 0 0];
derivatives=zeros(3,4); residual=zeros(3,1);
vp=145e3/(2*pi); vm=170e3/(2*pi);
for k=1:3
    a=cases(k,:); command=[.2;.7];
    expected=[(command(1)-a(1))/.13; (command(2)-a(2))/.22; ...
        1e5*10/1840.8*(vp*a(1)*a(5)-vm*a(2)*a(4)-.14*a(3)); ...
        ((-6.12)^2*(-23.3)^2*.98*.697*vm*1e-4*a(2)*a(3) ...
        -.33*(-23.3)^2*a(4)-a(6)*(-6.12)*(-23.3))/16512];
    actual=hydrostatic_si([a(1:2) a(3)*1e5 a(4)],command,a(5),a(6),p);
    residual(k)=max(abs(actual-expected)./max(1,abs(expected)));
    derivatives(k,:)=actual';
end
assert(max(residual)<3e-14);

% Motor displacement controls torque; pump geometry cannot change it.
ideal=p; ideal.gearbox_efficiency=1; ideal.motor_efficiency=1;
ideal.cardan_damping_nm_s=0; ideal.leakage_m3_per_s_pa=0;
[dx,power]=hydrostatic_si([0 .5 2e6 10],[0 .5],0,3000,ideal);
assert(abs(dx(4)*inertia+3000/ratio-(170e-6/(2*pi))*.5*2e6)<1e-12);
other=ideal; other.pump_m3_per_rad=3*ideal.pump_m3_per_rad;
dz=hydrostatic_si([0 .5 2e6 10],[0 .5],0,3000,other);
assert(dx(4)==dz(4)); assert(abs(power.load_power_w-3000*10/ratio)<1e-12);

% Closed ports: exact leakage exponential and first-order actuator response.
leaky=p; leaky.leakage_m3_per_s_pa=2e-12;
opts=odeset('RelTol',1e-9,'AbsTol',1e-11,'MaxStep',.005);
[~,x]=ode45(@(t,z)hydrostatic_si(z,[.4 0],0,0,leaky),[0 1],[0 0 3e6 0],opts);
expected_pressure=3e6*exp(-leaky.leakage_m3_per_s_pa/leaky.capacitance_m3_per_pa);
assert(abs(x(end,3)/expected_pressure-1)<1e-8);
assert(abs(x(end,1)-.4*(1-exp(-1/.13)))<1e-8);
assert(all(x(:,1)>=0 & x(:,1)<=.4)); assert(all(x(:,4)==0));

% Lossless closed exchange: exact matrix exponential plus conserved storage.
dm=ideal.motor_m3_per_rad*.6;
A=[0 -dm/ideal.capacitance_m3_per_pa; dm/inertia 0];
[~,x]=ode45(@(t,z)hydrostatic_si(z,[0 .6],0,0,ideal),[0 1],[0 .6 2e6 15],opts);
exact=expm(A)*[2e6;15];
assert(max(abs(x(end,3:4)'-exact)./max(1,abs(exact)))<2e-7);
energy=.5*(ideal.capacitance_m3_per_pa*x(:,3).^2+inertia*x(:,4).^2);
energy_drift=max(abs(energy/energy(1)-1)); assert(energy_drift<2e-7);

% Independent directional finite difference of stored energy, plus validity.
z=[.3;.8;1e7;50];
[dx,power]=hydrostatic_si(z,[.3 .8],180,5000,p);
storage=@(v)(p.capacitance_m3_per_pa*v(3)^2+inertia*v(4)^2)/2;
h=1e-7; rate=(storage(z+h*dx)-storage(z-h*dx))/(2*h);
expected=power.hydraulic_input_w-power.load_power_w-power.leakage_loss_w ...
    -power.conversion_loss_w-power.damping_loss_w;
assert(abs(rate/expected-1)<1e-7); assert(power.motoring_valid);
assert(all([power.leakage_loss_w power.conversion_loss_w power.damping_loss_w]>=0));
[~,back]=hydrostatic_si([.3 .8 -1e7 50],[.3 .8],180,5000,p);
assert(~back.motoring_valid && back.conversion_loss_w<0);

coarse=run_hydrostatic_si(.004); fine=run_hydrostatic_si(.002);
scaled=bsxfun(@rdivide,coarse.x-fine.x(1:2:end,:),[1 1 1e7 100]);
refinement=max(abs(scaled(:))); assert(refinement<3e-7);
assert(fine.report.all_motoring && fine.report.pressure_min_pa>0);
assert(fine.report.max_abs_power_balance_residual_w<1e-9);
assert(fine.report.motor_speed_max_rad_s-fine.report.motor_speed_min_rad_s>5);

must_fail(@()hydrostatic_si_parameters('guess','effective'));
must_fail(@()hydrostatic_si_parameters('per_revolution','guess'));
must_fail(@()hydrostatic_si([2 .8 1e6 10],[.3 .8],180,0,p));
must_fail(@()hydrostatic_si([0 -.1 0 0],[0 .8],180,0,p));
must_fail(@()hydrostatic_si([0 .8 0 0],[0 2],180,0,p));
must_fail(@()hydrostatic_si([0 .8 NaN 0],[0 .8],180,0,p));
must_fail(@()hydrostatic_si([0 .8 0 0],[0 .8],Inf,0,p));
invalid=p; invalid.gear_ratio=0;
must_fail(@()hydrostatic_si([0 .8 0 0],[0 .8],180,0,invalid));
invalid=p; invalid.motor_efficiency=1.1;
must_fail(@()hydrostatic_si([0 .8 0 0],[0 .8],180,0,invalid));
report=struct('checks',8,'source_units_relative_error',max(residual), ...
    'lossless_energy_relative_drift',energy_drift,'step_refinement_scaled_error',refinement, ...
    'derivative_fixtures',derivatives,'demo',fine.report);
fprintf('Hydrostatic SI: %d validation groups passed; source-unit error %.3g.\n', ...
    report.checks,report.source_units_relative_error);
end

function must_fail(f)
failed=false;
try, f(); catch, failed=true; end
assert(failed,'Expected invalid input to fail.');
end
