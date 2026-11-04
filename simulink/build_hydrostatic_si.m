function path=build_hydrostatic_si(output_dir,overwrite,reference)
%BUILD_HYDROSTATIC_SI Separate declared SI interpretation; preserves Eq.35.
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if nargin<1,output_dir=fullfile(base,'generated-hydrostatic');end
if nargin<2,overwrite=false;end
if nargin<3,reference=run_hydrostatic_si();end
if ~exist(output_dir,'dir'),mkdir(output_dir);end
name='si_hydrostatic_si';path=fullfile(output_dir,[name '.slx']);
if bdIsLoaded(name),error('Close model %s before building.',name);end
if exist(path,'file')&&~overwrite,error('Existing model preserved: %s',path);end
new_system(name);
try
 ws=get_param(name,'ModelWorkspace');assignin(ws,'p',reference.report.parameters);
 assignin(ws,'xinit',reference.x(1,:)');
 assignin(ws,'command_data',[reference.t reference.command]);
 add_block('simulink/Sources/From Workspace',[name '/RequestedAngles'], ...
  'VariableName','command_data','Interpolate','on','Position',[30 20 155 65]);
 add_block('simulink/Sources/Constant',[name '/PumpSpeed_rad_s'], ...
  'Value','180','Position',[30 95 155 130]);
 add_block('simulink/Sources/Constant',[name '/WheelLoad_Nm'], ...
  'Value','5000','Position',[30 165 155 200]);
 add_block('simulink/Signal Routing/Mux',[name '/Inputs'],'Inputs','3','Position',[200 30 205 190]);
 add_block('simulink/User-Defined Functions/S-Function',[name '/HydraulicMechanicalStorage'], ...
  'FunctionName','hydrostatic_si_sfun','Parameters','xinit,p','Position',[260 75 440 145]);
 add_block('simulink/Signal Routing/Demux',[name '/States'],'Outputs','[2 1 1]','Position',[500 40 505 170]);
 names={'NormalizedAngles','Pressure_Pa','MotorSpeed_rad_s'};
 for j=1:3
  add_block('simulink/Sinks/Out1',[name '/' names{j}],'Port',num2str(j), ...
   'Position',[625 35+55*(j-1) 655 55+55*(j-1)]);
  add_line(name,['States/' num2str(j)],[names{j} '/1']);
 end
 add_block('simulink/Sinks/To Workspace',[name '/StateTrace'],'VariableName','state_history', ...
  'SaveFormat','StructureWithTime','Position',[485 225 620 265]);
 add_line(name,'RequestedAngles/1','Inputs/1');add_line(name,'PumpSpeed_rad_s/1','Inputs/2');
 add_line(name,'WheelLoad_Nm/1','Inputs/3');add_line(name,'Inputs/1','HydraulicMechanicalStorage/1');
 add_line(name,'HydraulicMechanicalStorage/1','States/1');
 add_line(name,'HydraulicMechanicalStorage/1','StateTrace/1','autorouting','on');
 note=Simulink.Annotation(name,sprintf(['Separate SI interpretation: 145/170 cm^3 per revolution; effective capacitance.\n' ...
  'Requested normalized angles; no voltage calibration. Constant efficiencies: motoring only.\n' ...
  'See benchmarks/HYDROSTATIC_SOURCE_REVIEW.md; this is not the literal 2014 equation.']));
 note.Position=[25 310];
 set_param(name,'Solver','ode45','RelTol','1e-9','AbsTol','1e-10','MaxStep','.002','StopTime','6', ...
  'OutputOption','SpecifiedOutputTimes','OutputTimes','0:.01:6','ReturnWorkspaceOutputs','on');
 save_system(name,path);close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
end
