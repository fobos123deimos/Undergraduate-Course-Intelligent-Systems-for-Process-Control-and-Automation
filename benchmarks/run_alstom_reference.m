function [report,data] = run_alstom_reference(source_directory,output_csv,options)
%RUN_ALSTOM_REFERENCE Run the author's R2017 nonlinear plant and supplied PI.
% Requires Windows MATLAB/Simulink and the verified author archive. The plant
% is supplied only as a Windows MEX; this wrapper does not replace its physics.
if nargin<3,options=struct;end
assert(ispc && strcmp(computer('arch'),'win64'),...
 'ALSTOM:Platform','The supplied gasifier.mexw64 requires Windows x64 MATLAB/Simulink.');
here=fileparts(mfilename('fullpath'));
if nargin<1||isempty(source_directory)
 source_directory=fullfile(here,'external','alstom-gasifier','Gasifier_R2017');
end
if nargin<2,output_csv=fullfile(here,'results','alstom-mode100-nominal.csv');end
source_directory=char(java.io.File(source_directory).getCanonicalPath());
output_csv=char(java.io.File(output_csv).getCanonicalPath());
load_percent=option(options,'load_percent',100);scenario=char(option(options,'scenario','nominal'));
assert(ismember(load_percent,[0 50 100]),'Use the official 0, 50 or 100 percent initial condition');
assert(any(strcmp(scenario,{'nominal','pressure_step','pressure_sine','load_ramp','coal_quality'})),...
 'Unknown ALSTOM scenario');
duration=300;if any(strcmp(scenario,{'load_ramp','coal_quality'})),duration=5000;end
assert(~isfile(output_csv),'Choose a new output file to avoid stale results');
if strcmp(scenario,'load_ramp'),assert(load_percent==50,'The supplied load ramp starts at 50 percent');end
manifest=jsondecode(fileread(fullfile(here,'alstom_manifest.json')));
for k=1:numel(manifest.source_files)
 entry=manifest.source_files(k);filename=fullfile(source_directory,entry.relative_path);
 assert(isfile(filename),'Missing official package file: %s',filename);
 assert(strcmp(digest(filename),entry.sha256),'Modified official package file: %s',filename);
end
model='cgasifier_cl';assert(~bdIsLoaded(model),'Close the existing ALSTOM model first');
run_directory=tempname;mkdir(run_directory);
official=fullfile(source_directory,'PI_closed_loop');
for extension={'.mdl','.mat','.mexw64'}
 files=dir(fullfile(official,['*' extension{1}]));
 for k=1:numel(files),copyfile(fullfile(official,files(k).name),run_directory);end
end
original_directory=pwd;original_path=path;
cleanup=onCleanup(@() restore_environment(original_directory,original_path,model)); %#ok<NASGU>
cd(run_directory);addpath(run_directory);
initialization=load(fullfile(run_directory,sprintf('clss%d_x.mat',load_percent)));
initialization.distsine=double(strcmp(scenario,'pressure_sine'));
initialization.diststep=double(strcmp(scenario,'pressure_step'));
initialization.ld_final=50*double(strcmp(scenario,'load_ramp'));
load_system(fullfile(run_directory,[model '.mdl']));
plants=find_system(model,'LookUnderMasks','all','FollowLinks','on',...
 'BlockType','S-Function','FunctionName','gasifier');
assert(numel(plants)==1,'Expected the official nonlinear gasifier S-function');
coal=find_system(model,'SearchDepth',1,'MaskType','Ramp Change of Coal Quality as a Percentage');
assert(numel(coal)==1,'Expected the supplied coal-quality input');
coal_percent=8*double(strcmp(scenario,'coal_quality'));
set_param(coal{1},'init','0','fin',num2str(coal_percent),'tzero','10','tfin','20');
pressure=[model '/' sprintf('Downstream pressure\ndisturbance set-up')];
assert(strcmp(get_param([pressure '/psink_step'],'Time'),'30.0'));
assert(strcmp(get_param([pressure '/psink_step'],'After'),'-0.2e5 * diststep'));
assert(strcmp(get_param([pressure '/psink_sine'],'Amplitude'),'2e4 * distsine'));
assert(strcmp(get_param([pressure '/psink_sine'],'Frequency'),'0.04*2*pi'));
% Observe the existing disturbance outputs without changing their dynamics.
log_output(model,pressure,'psink_disturbance_Pa');
log_output(model,coal{1},'coal_quality_percent');
exports=find_system(model,'LookUnderMasks','all','FollowLinks','on','BlockType','ToWorkspace');
for k=1:numel(exports),set_param(exports{k},'SaveFormat','Array','MaxDataPoints','inf','Decimation','1');end
siminput=Simulink.SimulationInput(model);
fields=fieldnames(initialization);
for k=1:numel(fields),siminput=siminput.setVariable(fields{k},initialization.(fields{k}));end
siminput=siminput.setModelParameter('StopTime',num2str(duration),'ReturnWorkspaceOutputs','on',...
 'Solver','ode23tb','RelTol','1e-6','AbsTol','1e-8','MaxStep','0.25',...
 'LoadInitialState','on','InitialState','x0c','SaveState','off','SaveFinalState','off');
simulation=sim(siminput);
t=simulation.get('tsim');y=simulation.get('yt');u=simulation.get('ut');sp=simulation.get('sp');
ld=simulation.get('ld');ldsp=simulation.get('ldsp');
psink=simulation.get('psink_disturbance_Pa');coal_change=simulation.get('coal_quality_percent');
t=t(:);ld=ld(:);ldsp=ldsp(:);psink=psink(:);coal_change=coal_change(:);
y=alstom_log_matrix(y,numel(t),4,'yt');
sp=alstom_log_matrix(sp,numel(t),4,'sp');
% The official ut log contains five flows. Limestone is constrained to
% one tenth of coal; only the first four are independent manipulated inputs.
all_inputs=alstom_log_matrix(u,numel(t),5,'ut');
u=all_inputs(:,1:4);limestone=all_inputs(:,5);
assert(max(abs(limestone-.1*u(:,3)))<1e-8,'Official limestone/coal ratio changed');
arrays={y,u,sp,ld,ldsp,psink,coal_change};
for k=1:numel(arrays),assert(size(arrays{k},1)==numel(t),'Unaligned official output grids');end
values=[t,y,u,sp,ld,ldsp,psink,coal_change,limestone];
assert(all(isfinite(values(:))),'Nonfinite official gasifier output');
assert(numel(t)>2 && all(diff(t)>=0) && any(diff(t)>0) && abs(t(1))<1e-9 && ...
 abs(t(end)-duration)<1e-7,'Incomplete official gasifier run');
expected_pressure=-20000*initialization.diststep*(t>=30)+...
 20000*initialization.distsine*sin(2*pi*.04*t);
assert(max(abs(psink-expected_pressure))<1e-6,'Pressure disturbance differs from the specified challenge');
expected_coal=coal_percent*min(1,max(0,(t-10)/10));
assert(max(abs(coal_change-expected_coal))<1e-8,'Coal-quality input differs from the specified ramp');
expected_load=load_percent+initialization.ld_final*min(1,max(0,(t-100)/600));
assert(max(abs(ldsp-expected_load))<1e-8,'Load demand differs from the supplied 100-to-700 s ramp');
error=y-sp;limits=[10000 500 10000 1];upper=[3.5 20 10 6];rate_limit=[.2 1 .2 1];
dt=diff(t);du=diff(u);moving=dt>1e-10;
rates=abs(du(moving,:))./dt(moving);
max_error=max(abs(error),[],1);iae=trapz(t,abs(error),1);
output_violation=max(0,max_error-limits);
input_violation=max(0,max([max(u-upper,[],1);max(-u,[],1)],[],1));
rate_violation=max(0,max(rates,[],1)-rate_limit);
folder=fileparts(output_csv);if ~isfolder(folder),mkdir(folder);end
names={'time_s','CV_J_kg','bed_mass_kg','pressure_Pa','temperature_K',...
 'char_kg_s','air_kg_s','coal_kg_s','steam_kg_s',...
 'CV_setpoint_J_kg','bed_mass_setpoint_kg','pressure_setpoint_Pa','temperature_setpoint_K',...
 'load_actual_percent','load_demand_percent','psink_disturbance_Pa','coal_quality_percent','limestone_kg_s'};
writetable(array2table(values,'VariableNames',names),output_csv);
report=struct('model','ALSTOM Gasifier II author R2017 package with supplied PI',...
 'scenario',scenario,'initial_load_percent',load_percent,'plant_states',25,'controller_states',3,...
 'duration_s',duration,'sample_count',numel(t),'source_archive_sha256',manifest.archive_sha256,...
 'solver','ode23tb','relative_tolerance',1e-6,'absolute_tolerance',1e-8,'maximum_step_s',.25,...
 'matlab_version',version,'all_outputs_finite',true,'specified_inputs_verified',true,...
 'output_order',{{'CV_J_kg','bed_mass_kg','pressure_Pa','temperature_K'}},...
 'input_order',{{'char_kg_s','air_kg_s','coal_kg_s','steam_kg_s'}},...
 'maximum_absolute_error',max_error,'integrated_absolute_error',iae,...
 'maximum_input_limit_violation',input_violation,'maximum_input_rate_violation',rate_violation,...
 'output_limit_applicable',any(strcmp(scenario,{'pressure_step','pressure_sine'})),...
 'pressure_test_output_limits',limits,'maximum_pressure_test_limit_violation',output_violation,...
 'coal_quality_final_percent',coal_percent,'limestone_to_coal_ratio_verified',true,...
 'scope','Integration/input checks and PI performance measurements; violations remain reported, not discarded');
data=struct('time_s',t,'outputs',y,'inputs',u,'setpoints',sp,'load_demand_percent',ldsp,...
 'psink_disturbance_Pa',psink,'coal_quality_percent',coal_change);
fprintf('Official ALSTOM %s at %g%% load: %d rows over %g s.\n',scenario,load_percent,numel(t),duration);
end
function log_output(model,source,variable)
sink=add_block('simulink/Sinks/To Workspace',[model '/' variable],...
 'VariableName',variable,'SaveFormat','Array','MaxDataPoints','inf','SampleTime','-1');
ports=get_param(source,'PortHandles');destination=get_param(sink,'PortHandles');
add_line(model,ports.Outport(1),destination.Inport(1),'autorouting','on');
end
function value=option(options,name,fallback)
if isfield(options,name),value=options.(name);else,value=fallback;end
end
function restore_environment(folder,original_path,model)
if bdIsLoaded(model),close_system(model,0);end
clear gasifier;cd(folder);path(original_path);
end
function value=digest(filename)
fid=fopen(filename,'rb');assert(fid>0);cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
engine=java.security.MessageDigest.getInstance('SHA-256');engine.update(fread(fid,Inf,'*uint8'));
value=lower(reshape(dec2hex(typecast(engine.digest(),'uint8'),2)',1,[]));
end
