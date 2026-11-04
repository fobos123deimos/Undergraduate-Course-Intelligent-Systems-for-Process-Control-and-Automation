function p = hydrostatic_si_parameters(displacement_basis, capacitance_basis)
% Explicit conventions: see benchmarks/HYDROSTATIC_SOURCE_REVIEW.md.
% Table 5 does not resolve geometric/reduced volume or per-line capacitance.
% This constructor requires both choices; it is not authenticated calibration.
if nargin~=2 || ~ischar(displacement_basis) || ~ischar(capacitance_basis)
    error('hydrostatic:parameters','Choose displacement and capacitance conventions.');
end
switch displacement_basis
    case 'per_revolution', volume_factor=1e-6/(2*pi);
    case 'per_radian', volume_factor=1e-6;
    otherwise, error('hydrostatic:parameters','Unknown displacement basis.');
end
switch capacitance_basis
    case 'effective', capacitance_factor=1e-15;
    case 'per_line', capacitance_factor=1e-15/2;
    otherwise, error('hydrostatic:parameters','Unknown capacitance basis.');
end
p=struct('pump_m3_per_rad',145*volume_factor, ...
    'motor_m3_per_rad',170*volume_factor, ...
    'capacitance_m3_per_pa',1840.8*capacitance_factor, ...
    'leakage_m3_per_s_pa',.14e-14,'vehicle_inertia_kg_m2',16512, ...
    'cardan_damping_nm_s',.33,'gear_ratio',-6.12,'axle_ratio',-23.3, ...
    'gearbox_efficiency',.98,'motor_efficiency',.697, ...
    'pump_time_constant_s',.13,'motor_time_constant_s',.22);
end
