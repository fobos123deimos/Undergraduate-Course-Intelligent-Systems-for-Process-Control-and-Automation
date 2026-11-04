function report=validate_pneumatic_simulink(output_dir)
%VALIDATE_PNEUMATIC_SIMULINK Run three constant-payload cases on one new model.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated-pneumatic');end
path=build_pneumatic_physical(output_dir,false);[~,name]=fileparts(path);load_system(path);
cleanup=onCleanup(@()close_system(name,0));ws=get_param(name,'ModelWorkspace');
reference=jsondecode(fileread(fullfile(fileparts(mfilename('fullpath')),'..','matlab','pneumatic_reference.json')));
errors=zeros(3,1);pressure_errors=zeros(3,1);scale=[.125 1 .01 .01 300 300];
for j=1:3
 p=pneumatic_physical('parameters');p.load_mass=reference.cases(j).load_kg;
 assignin(ws,'p',p);assignin(ws,'xinit',pneumatic_physical('equilibrium',0,5e5,p));
 output=sim(name);trace=output.get('state_history');pressures=output.get('pressure_history');
 assert(numel(trace.time)==201&&max(abs(trace.time(:)-reference.cases(j).time(:)))<1e-10);
 delta=bsxfun(@rdivide,trace.signals.values-reference.cases(j).state,scale);errors(j)=max(abs(delta(:)));
 assert(errors(j)<2e-6,'Pneumatic Simulink/Python trajectory mismatch.');
 expected=zeros(201,2);
 for k=1:201,expected(k,:)=pneumatic_physical('observe',reference.cases(j).state(k,:)',p)';end
 pressure_errors(j)=max(abs(pressures.signals.values(:)-expected(:)))/9e5;
 assert(pressure_errors(j)<2e-6,'Pneumatic pressure output mismatch.');
end
p=pneumatic_physical('parameters');assignin(ws,'p',p);assignin(ws,'xinit',pneumatic_physical('equilibrium',0,5e5,p));
export_model_diagram(name,fullfile(output_dir,[name '.png']));clear cleanup;
report=struct('runtime',version,'model',name,'payloads_kg',[3 6 9],...
 'state_scaled_errors',errors,'pressure_scaled_errors',pressure_errors,...
 'canonical_valve_calibration_recovered',false,'generated_models',1,'passed',true);
fid=fopen(fullfile(output_dir,'validation.json'),'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(report,'PrettyPrint',true));clear cleanup;
fprintf('Separate pneumatic mass/energy Simulink variant passed three payload cases.\n');
end
