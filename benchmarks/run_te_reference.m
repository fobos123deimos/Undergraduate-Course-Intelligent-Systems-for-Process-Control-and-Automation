function [report,data] = run_te_reference(source_directory, output_csv, options)
%RUN_TE_REFERENCE Execute official revised TE mode1 in an isolated source copy.
% Options: duration_h (.2), disturbance (0 or IDV1:28), seed (17),
% measurement_noise (false). A selected disturbance is active from t=0.
if nargin<3,options=struct;end
duration=option(options,'duration_h',.2);fault=option(options,'disturbance',0);
seed=option(options,'seed',17);noise=option(options,'measurement_noise',false);
assert(isscalar(duration)&&isfinite(duration)&&duration>0);
assert(isscalar(fault)&&fault==fix(fault)&&fault>=0&&fault<=28);
source_directory=char(java.io.File(source_directory).getCanonicalPath());
output_csv=char(java.io.File(output_csv).getCanonicalPath());
assert(isfile(fullfile(source_directory,'temexd_mod.c')),'Fetch te-revised first');
assert(~isfile(output_csv),'Choose a new output file to avoid stale results');
model='MultiLoop_mode1';assert(~bdIsLoaded(model),'Close the existing TE model first');
run_directory=tempname;mkdir(run_directory);files=dir(source_directory);
for k=1:numel(files)
 [~,~,extension]=fileparts(files(k).name);
 if ~files(k).isdir&&any(strcmpi(extension,{'.m','.mdl','.mat','.c','.h'}))
  copyfile(fullfile(source_directory,files(k).name),run_directory);
 end
end
% Historical PreLoadFcn would populate the base workspace. Supply the same
% initialization through SimulationInput instead, preserving the user's workspace.
model_file=fullfile(run_directory,[model '.mdl']);contents=fileread(model_file);
assert(numel(regexp(contents,'PreLoadFcn\s+"Mode_1_Init"'))==1);
contents=regexprep(contents,'PreLoadFcn\s+"Mode_1_Init"','PreLoadFcn ""');
fid=fopen(model_file,'w');assert(fid>0);fwrite(fid,contents);fclose(fid);
original_directory=pwd;original_path=path;
cleanup=onCleanup(@() restore_environment(original_directory,original_path,model));
cd(run_directory);addpath(run_directory);mex('temexd_mod.c');
initialization=initialize_mode1(run_directory);
load_system(model_file);set_param(model,'StopFcn','');siminput=Simulink.SimulationInput(model);
fields=fieldnames(initialization);
for k=1:numel(fields),siminput=siminput.setVariable(fields{k},initialization.(fields{k}));end
disturbances=zeros(1,28);if fault>0,disturbances(fault)=1;end
set_param([model '/Disturbances'],'Value',mat2str(disturbances));
blocks=find_system(model,'LookUnderMasks','all','FollowLinks','on','BlockType','S-Function','FunctionName','temexd_mod');
assert(numel(blocks)==1,'Expected one official TE plant');
flags=16*double(~noise); % Official bit4 disables measurement noise.
set_param(blocks{1},'Parameters',sprintf('[],%.17g,%d',seed,flags));
exports=find_system(model,'LookUnderMasks','all','FollowLinks','on','BlockType','ToWorkspace');
for k=1:numel(exports),set_param(exports{k},'SaveFormat','Array');end
siminput=siminput.setModelParameter('StopTime',num2str(duration,17),'ReturnWorkspaceOutputs','on',...
 'Solver','ode45','RelTol','1e-7','AbsTol','1e-9','MaxStep','0.0005');
simulation=sim(siminput);
t=simulation.get('tout');y=simulation.get('simout');u=simulation.get('xmv');idv=simulation.get('idv');
assert(isnumeric(t)&&isnumeric(y)&&isnumeric(u)&&isnumeric(idv),'Unexpected output format');
t=t(:);assert(size(y,2)==41&&size(u,2)==12,'Unexpected TE channel dimensions');
assert(numel(t)==size(y,1)&&numel(t)==size(u,1)&&numel(t)==size(idv,1),'Unaligned output times');
assert(all(isfinite([t;y(:);u(:);idv(:)])),'Nonfinite TE output');
assert(all(diff(t)>0)&&abs(t(end)-duration)<1e-8,'Incomplete TE run');
assert(all(u(:)>=-1e-7 & u(:)<=100+1e-7),'Manipulated-variable bounds violated');
assert(all(y(:,7)>0 & y(:,7)<3000),'Reactor pressure outside check range');
assert(all(y(:,8)>0 & y(:,8)<100),'Reactor level outside check range');
folder=fileparts(output_csv);if ~isfolder(folder),mkdir(folder);end
names=[{'time_h'},arrayfun(@(k)sprintf('xmeas_%02d',k),1:41,'UniformOutput',false),...
 arrayfun(@(k)sprintf('xmv_%02d',k),1:12,'UniformOutput',false)];
writetable(array2table([t,y,u],'VariableNames',names),output_csv);
report=struct('model','official revised 2015 Tennessee Eastman','continuous_states',52,...
 'operating_mode',1,'disturbance_from_start',fault,'seed',seed,'measurement_noise',noise,...
 'duration_h',duration,'sample_count',numel(t),'outputs',41,'manipulated_variables',12,...
 'solver','ode45','relative_tolerance',1e-7,'absolute_tolerance',1e-9,'max_step_h',.0005,...
 'source_c_sha256',digest(fullfile(source_directory,'temexd_mod.c')),...
 'source_header_sha256',digest(fullfile(source_directory,'teprob_mod.h')),...
 'source_model_sha256',digest(fullfile(source_directory,[model '.mdl'])),...
 'all_outputs_finite',true,'max_scaled_output_drift',max(max(abs(y-y(1,:))./max(1,abs(y(1,:))))),...
 'reactor_pressure_range_kPa',[min(y(:,7)) max(y(:,7))],...
 'reactor_temperature_range_C',[min(y(:,9)) max(y(:,9))],'matlab_version',version,...
 'scope','Short integration and disturbance test; not all six modes or full challenge performance');
data=struct('time_h',t,'measurements',y,'inputs',u,'disturbances',idv);
fprintf('Official TE mode1 completed: %d rows, IDV=%d, %.3g h.\n',numel(t),fault,duration);
end
function state=initialize_mode1(folder)
run(fullfile(folder,'Mode_1_Init.m'));
names=[{'u0','Fp_0','Eadj_0','SP17_0','xInitial','Ts_base','Ts_save'},...
 arrayfun(@(k)sprintf('xmv%d_0',k),1:12,'UniformOutput',false),...
 arrayfun(@(k)sprintf('r%d_0',k),1:7,'UniformOutput',false)];
state=struct;for n=1:numel(names),state.(names{n})=eval(names{n});end
end
function value=option(options,name,fallback)
if isfield(options,name),value=options.(name);else,value=fallback;end
end
function restore_environment(folder,original_path,model)
if bdIsLoaded(model),close_system(model,0);end
clear temexd_mod;cd(folder);path(original_path);
end
function value=digest(filename)
fid=fopen(filename,'rb');assert(fid>0);cleanup=onCleanup(@() fclose(fid));
engine=java.security.MessageDigest.getInstance('SHA-256');engine.update(fread(fid,Inf,'*uint8'));
value=lower(reshape(dec2hex(typecast(engine.digest(),'uint8'),2)',1,[]));
end
