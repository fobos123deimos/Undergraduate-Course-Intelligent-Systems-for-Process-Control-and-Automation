function path=build_wind_pdc_model(output_dir,overwrite,points,reference)
%BUILD_WIND_PDC_MODEL Full-state scheduled LQR/PDC design exercise diagram.
% Later ROSCO map and newly selected gains; not a recovered published controller.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if nargin<3,points=wind_control('design');end
if nargin<4,reference=run_wind_control(true,60,.02,points);end
if ~exist(output_dir,'dir'),mkdir(output_dir);end
name='si_wind_pdc';path=fullfile(output_dir,[name '.slx']);
if bdIsLoaded(name),error('Close model %s before building.',name);end
if exist(path,'file')&&~overwrite,error('Existing model preserved: %s',path);end
new_system(name);
try
 dt=reference.time(2)-reference.time(1);initial=wind_control('equilibrium',reference.wind(1));
 ws=get_param(name,'ModelWorkspace');assignin(ws,'points',points);assignin(ws,'dt',dt);
 assignin(ws,'initial_state',initial.state);assignin(ws,'initial_command',initial.command);
 assignin(ws,'wind_data',[reference.time reference.wind]);
 add_block('simulink/Sources/From Workspace',[name '/Wind'],'VariableName','wind_data','Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','dt','Position',[30 20 105 55]);
 add_block('simulink/Signal Routing/Mux',[name '/StateWind'],'Inputs','2','Position',[160 90 165 190]);
 add_block('simulink/User-Defined Functions/S-Function',[name '/ScheduledLQR_PDC'],'FunctionName','wind_pdc_sfun',...
  'Parameters','points,initial_command,dt','Position',[225 105 365 165]);
 add_block('simulink/Signal Routing/Mux',[name '/CommandWind'],'Inputs','2','Position',[420 100 425 190]);
 add_block('simulink/User-Defined Functions/S-Function',[name '/NonlinearWind'],'FunctionName','wind_regulation_sfun',...
  'Parameters','initial_state,dt','Position',[490 110 635 170]);
 add_block('simulink/Sinks/To Workspace',[name '/StateLog'],'VariableName','wind_states','SaveFormat','StructureWithTime','Position',[715 110 825 155]);
 add_block('simulink/Sinks/To Workspace',[name '/CommandLog'],'VariableName','wind_commands','SaveFormat','StructureWithTime','Position',[445 255 570 295]);
 add_line(name,'Wind/1','StateWind/2','autorouting','on');add_line(name,'NonlinearWind/1','StateWind/1','autorouting','on');
 add_line(name,'StateWind/1','ScheduledLQR_PDC/1');add_line(name,'ScheduledLQR_PDC/1','CommandWind/1');
 add_line(name,'Wind/1','CommandWind/2','autorouting','on');add_line(name,'CommandWind/1','NonlinearWind/1');
 add_line(name,'NonlinearWind/1','StateLog/1');add_line(name,'ScheduledLQR_PDC/1','CommandLog/1','autorouting','on');
 set_param(name,'Solver','FixedStepDiscrete','FixedStep',num2str(dt,17),'StopTime',num2str(reference.time(end),17),'ReturnWorkspaceOutputs','on');
 save_system(name,path);close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
end
