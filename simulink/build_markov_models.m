function paths=build_markov_models(output_dir,overwrite,lab)
%BUILD_MARKOV_MODELS Six explicit Markov/HMM and causal sensor-control models.
% Synthetic calibration/test generation precedes model building. The online
% controller receives only reference and measurement, never hidden regimes.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if nargin<3,lab=run_markov_lab(false);end
if ~exist(output_dir,'dir'),mkdir(output_dir);end
dt=lab.t(2)-lab.t(1);paths=cell(6,1);
p=struct('transition',lab.fit.transition,'emission',lab.fit.emission,...
 'initial',lab.fit.initial,'dt',dt,'bias',lab.calibration_bias,...
 'cutpoints',lab.cutpoints,'nominal_tau',10,'kp',2,'ki',.2,'actuator_bias',.35,'supervised',true);
name='si_markov_occupancy';paths{1}=prepare(name,output_dir,overwrite);new_system(name);
try
 ws=get_param(name,'ModelWorkspace');assignin(ws,'P',lab.transition_true);assignin(ws,'initial',lab.initial_true(:));
 add_block('simulink/Sources/Constant',[name '/Zero'],'Value','0','Position',[30 60 65 90]);
 add_block('simulink/Discrete/Discrete State-Space',[name '/ProbabilityPropagation'],...
  'A','P''','B','zeros(3,1)','C','eye(3)','D','zeros(3,1)','X0','initial','SampleTime',num2str(dt),'Position',[130 50 290 100]);
 sink(name,'Occupancy','occupancy',[360 50 470 100]);
 add_line(name,'Zero/1','ProbabilityPropagation/1');add_line(name,'ProbabilityPropagation/1','Occupancy/1');
 configure(name,dt,100*dt);save_system(name,paths{1});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
name='si_hmm_diagnosis';paths{2}=prepare(name,output_dir,overwrite);new_system(name);
try
 ws=get_param(name,'ModelWorkspace');assignin(ws,'p',p);assignin(ws,'symbols',[lab.t lab.observations]);
 source(name,'Symbols','symbols',[30 60 110 90]);
 add_block('simulink/User-Defined Functions/S-Function',[name '/CausalFilter'],'FunctionName','hmm_filter_sfun','Parameters','p','Position',[180 45 320 105]);
 sink(name,'Posterior','posterior',[390 50 480 100]);
 add_line(name,'Symbols/1','CausalFilter/1');add_line(name,'CausalFilter/1','Posterior/1');
 configure(name,dt,lab.t(end));save_system(name,paths{2});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
suffixes={'nominal_baseline','nominal_supervisor','mismatch_baseline','mismatch_supervisor'};
for j=1:4
 name=['si_hmm_' suffixes{j}];paths{j+2}=prepare(name,output_dir,overwrite);new_system(name);
 try
  current=lab.(suffixes{j});p.supervised=mod(j,2)==0;
  ws=get_param(name,'ModelWorkspace');assignin(ws,'p',p);assignin(ws,'a',exp(-dt/current.time_constant));
  assignin(ws,'reference_data',[lab.t current.reference]);assignin(ws,'sensor_error',[lab.t lab.residual]);
  source(name,'Reference','reference_data',[25 145 105 175]);
  source(name,'SensorBiasNoise','sensor_error',[375 20 470 50]);
  add_block('simulink/Signal Routing/Mux',[name '/ReferenceMeasurement'],'Inputs','2','Position',[150 140 155 215]);
  add_block('simulink/User-Defined Functions/S-Function',[name '/HMM_PI'],'FunctionName','hmm_pi_sfun','Parameters','p','Position',[215 145 335 205]);
  add_block('simulink/Signal Routing/Demux',[name '/SeparateOutputs'],'Outputs','[1 3 1 1]','Position',[375 130 380 230]);
  add_block('simulink/Discrete/Discrete State-Space',[name '/Tank'],'A','a','B','1-a','C','1','D','0','X0','.35','SampleTime',num2str(dt),'Position',[440 125 540 165]);
  add_block('simulink/Math Operations/Sum',[name '/Sensor'],'Inputs','++','Position',[580 80 600 110]);
  sink(name,'Concentration','concentration',[650 135 760 165]);
  sink(name,'ControllerTrace','controller_trace',[440 260 555 300]);
  add_line(name,'Reference/1','ReferenceMeasurement/1');add_line(name,'Sensor/1','ReferenceMeasurement/2','autorouting','on');
  add_line(name,'ReferenceMeasurement/1','HMM_PI/1');add_line(name,'HMM_PI/1','SeparateOutputs/1');
  add_line(name,'HMM_PI/1','ControllerTrace/1','autorouting','on');add_line(name,'SeparateOutputs/1','Tank/1');
  add_line(name,'Tank/1','Concentration/1');add_line(name,'Tank/1','Sensor/1','autorouting','on');add_line(name,'SensorBiasNoise/1','Sensor/2','autorouting','on');
  configure(name,dt,lab.t(end));save_system(name,paths{j+2});close_system(name,0);
 catch err,close_system(name,0);rethrow(err);end
end
fprintf('Generated six Markov/HMM Simulink models.\n');
end
function path=prepare(name,folder,overwrite)
path=fullfile(folder,[name '.slx']);
if bdIsLoaded(name),error('Close model %s before building.',name);end
if exist(path,'file')&&~overwrite,error('Existing model preserved: %s',path);end
end
function source(name,block,variable,position)
add_block('simulink/Sources/From Workspace',[name '/' block],'VariableName',variable,'Interpolate','off','SampleTime','p.dt','Position',position);
end
function sink(name,block,variable,position)
add_block('simulink/Sinks/To Workspace',[name '/' block],'VariableName',variable,'SaveFormat','StructureWithTime','Position',position);
end
function configure(name,dt,last)
set_param(name,'Solver','FixedStepDiscrete','FixedStep',num2str(dt,17),'StopTime',num2str(last,17),'ReturnWorkspaceOutputs','on');
end
