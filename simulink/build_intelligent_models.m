function paths=build_intelligent_models(output_dir,overwrite,neural)
%BUILD_INTELLIGENT_MODELS Explicit feedback diagrams for fuzzy PID and RBF control.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if nargin<3,neural=run_lesson(6,false);end
if ~exist(output_dir,'dir'),mkdir(output_dir);end
names={'si_fuzzy_pid_tank','si_neural_rbf_tank'};paths=cell(2,1);
for j=1:2
 name=names{j};paths{j}=fullfile(output_dir,[name '.slx']);
 if bdIsLoaded(name),error('Close model %s before building.',name);end
 if exist(paths{j},'file')&&~overwrite,error('Existing model preserved: %s',paths{j});end
 new_system(name);
 try
  ws=get_param(name,'ModelWorkspace');assignin(ws,'dt',.2);assignin(ws,'p',struct('dt',.2,'filter_time',.5));
  assignin(ws,'model',neural.neural_models.rbf);assignin(ws,'reference_data',[neural.t neural.reference]);
  add_block('simulink/Sources/From Workspace',[name '/Reference'],'VariableName','reference_data','Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','dt','Position',[25 40 105 75]);
  add_block('simulink/Signal Routing/Mux',[name '/ReferenceMeasurement'],'Inputs','2','Position',[155 40 160 140]);
  if j==1
   add_block('simulink/User-Defined Functions/S-Function',[name '/Controller'],'FunctionName','fuzzy_pid_sfun','Parameters','p','Position',[215 55 335 115]);
   add_block('simulink/Signal Routing/Demux',[name '/CommandGains'],'Outputs','[1 4]','Position',[370 45 375 140]);
   add_block('simulink/Sources/Step',[name '/Disturbance'],'Time','45','Before','0','After','.08','SampleTime','dt','Position',[400 5 450 35]);
   add_block('simulink/Math Operations/Sum',[name '/PlantInput'],'Inputs','++','Position',[440 60 460 90]);
   add_block('simulink/Discrete/Discrete State-Space',[name '/Plant'],'A','exp(-dt/10)','B','1-exp(-dt/10)','C','1','D','0','X0','.35','SampleTime','dt','Position',[505 55 610 100]);
   add_line(name,'Controller/1','CommandGains/1');add_line(name,'CommandGains/1','PlantInput/1');
   add_line(name,'Disturbance/1','PlantInput/2');add_line(name,'PlantInput/1','Plant/1');
  else
   add_block('simulink/User-Defined Functions/S-Function',[name '/Controller'],'FunctionName','neural_control_sfun','Parameters','model,dt','Position',[215 55 335 115]);
   add_block('simulink/User-Defined Functions/S-Function',[name '/Plant'],'FunctionName','neural_teaching_plant_sfun','Parameters','dt','Position',[505 55 610 100]);
   add_line(name,'Controller/1','Plant/1');
  end
  add_block('simulink/Sinks/To Workspace',[name '/Concentration'],'VariableName','concentration','SaveFormat','StructureWithTime','Position',[685 55 790 95]);
  add_block('simulink/Sinks/To Workspace',[name '/ControllerTrace'],'VariableName','controller_trace','SaveFormat','StructureWithTime','Position',[420 210 550 250]);
  add_line(name,'Reference/1','ReferenceMeasurement/1');add_line(name,'Plant/1','ReferenceMeasurement/2','autorouting','on');
  add_line(name,'ReferenceMeasurement/1','Controller/1');add_line(name,'Controller/1','ControllerTrace/1','autorouting','on');add_line(name,'Plant/1','Concentration/1');
  set_param(name,'Solver','FixedStepDiscrete','FixedStep','.2','StopTime','80','ReturnWorkspaceOutputs','on');
  save_system(name,paths{j});close_system(name,0);
 catch err,close_system(name,0);rethrow(err);end
end
fprintf('Generated fuzzy PID and neural RBF closed-loop diagrams.\n');
end
