function report=validate_wind_pdc_simulink(output_dir)
%VALIDATE_WIND_PDC_SIMULINK Match sampled diagram to native scheduled controller.
if nargin<1,output_dir=tempname;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
points=wind_control('design');reference=run_wind_control(true,60,.02,points);
path=build_wind_pdc_model(output_dir,false,points,reference);name='si_wind_pdc';
load_system(path);cleanup=onCleanup(@()close_system(name,0));output=sim(name);
states=output.get('wind_states');commands=output.get('wind_commands');
assert(numel(states.time)==numel(reference.time)&&max(abs(states.time(:)-reference.time))<1e-10);
difference=states.signals.values-reference.state;state_error=max(abs(difference(:)));
difference=commands.signals.values(1:end-1,:)-reference.command(1:end-1,:);
scaled=bsxfun(@rdivide,difference,[1e6 .1]);command_error=max(abs(scaled(:)));
assert(state_error<1e-8&&command_error<1e-9);
rate=abs(diff(commands.signals.values));assert(all(all(rate<=[5e5 8*pi/180]*.02+1e-8)));
assert(all(all(commands.signals.values>=[0 0]))&&all(all(commands.signals.values<=[6e6 30*pi/180])));
print(['-s' name],'-dpng','-r120',fullfile(output_dir,[name '.png']));
report=struct('model',name,'state_max_error',state_error,'scaled_command_max_error',command_error,...
 'samples',numel(states.time),'generated_models',1,'map_variant','ROSCO 2022; new LQR/PDC design','passed',true);
fprintf('Scheduled wind LQR/PDC diagram matched native state and actuator traces.\n');
end
