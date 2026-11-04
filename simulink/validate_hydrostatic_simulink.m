function report=validate_hydrostatic_simulink(output_dir)
%VALIDATE_HYDROSTATIC_SIMULINK Separate SI model, independent continuous solver.
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if nargin<1,output_dir=fullfile(base,'generated-hydrostatic');end
reference=run_hydrostatic_si();path=build_hydrostatic_si(output_dir,false,reference);
name='si_hydrostatic_si';load_system(path);cleanup=onCleanup(@()close_system(name,0));
output=sim(name);trace=output.get('state_history');
assert(numel(trace.time)==601&&max(abs(trace.time(:)-reference.t(1:5:end)))<1e-10);
delta=bsxfun(@rdivide,trace.signals.values-reference.x(1:5:end,:),[1 1 1e7 100]);
error_scaled=max(abs(delta(:)));
assert(error_scaled<2e-6,'Hydrostatic continuous/RK4 state mismatch.');
power_error=0;all_motoring=true;
for k=1:601
 [~,power]=hydrostatic_si(trace.signals.values(k,:),reference.command(1+5*(k-1),:),180,5000,reference.report.parameters);
 power_error=max(power_error,abs(power.balance_residual_w));
 all_motoring=all_motoring && power.motoring_valid;
end
assert(power_error<1e-8 && all_motoring);
export_model_diagram(name,fullfile(output_dir,[name '.png']));clear cleanup;
report=struct('runtime',version,'model',name,'generated_models',1,'passed',true, ...
 'state_scaled_error',error_scaled,'power_balance_residual_w',power_error, ...
 'all_motoring',all_motoring,'samples',601,'displacement_basis','per_revolution', ...
 'capacitance_basis','effective','input_contract','requested_normalized_angles', ...
 'command_interpolation','piecewise linear samples every 0.002 seconds', ...
 'canonical_2007_calibration_recovered',false);
fid=fopen(fullfile(output_dir,'validation.json'),'w');assert(fid>=0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(report,'PrettyPrint',true));clear cleanup;
fprintf('Separate hydrostatic SI Simulink model matched the native trajectory.\n');
end
