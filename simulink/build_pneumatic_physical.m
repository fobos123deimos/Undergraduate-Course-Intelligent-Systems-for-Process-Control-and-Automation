function path=build_pneumatic_physical(output_dir,overwrite)
%BUILD_PNEUMATIC_PHYSICAL Separate physical variant; preserves survey model.
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if nargin<1,output_dir=fullfile(base,'generated-pneumatic');end
if nargin<2,overwrite=false;end
if ~exist(output_dir,'dir'),mkdir(output_dir);end
name='si_pneumatic_physical';path=fullfile(output_dir,[name '.slx']);
if bdIsLoaded(name),error('Close model %s before building.',name);end
if exist(path,'file')&&~overwrite,error('Existing model preserved: %s',path);end
new_system(name);
try
 p=pneumatic_physical('parameters');ws=get_param(name,'ModelWorkspace');assignin(ws,'p',p);
 assignin(ws,'xinit',pneumatic_physical('equilibrium',0,5e5,p));
 add_block('simulink/Sources/Sine Wave',[name '/Voltage'],'Amplitude','2','Frequency','2*pi','SampleTime','0','Position',[30 90 100 130]);
 add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[name '/MassEnergyCylinder'],...
  'FunctionName','pneumatic_physical_sfun','Parameters','xinit,p','Position',[180 60 400 155]);
 add_block('simulink/Signal Routing/Demux',[name '/MechanicalMassThermal'],'Outputs','[1 1 2 2]','Position',[465 10 470 125]);
 add_block('simulink/Sinks/To Workspace',[name '/StateTrace'],'VariableName','state_history','SaveFormat','StructureWithTime','Position',[465 230 595 270]);
 add_block('simulink/Sinks/To Workspace',[name '/PressureTrace'],'VariableName','pressure_history','SaveFormat','StructureWithTime','Position',[465 165 595 205]);
 labels={'Position','Velocity','GasMasses','Temperatures'};
 for j=1:4
  add_block('simulink/Sinks/Out1',[name '/' labels{j}],'Port',num2str(j),'Position',[650 5+(j-1)*40 680 25+(j-1)*40]);
  add_line(name,['MechanicalMassThermal/' num2str(j)],[labels{j} '/1']);
 end
 add_line(name,'Voltage/1','MassEnergyCylinder/1');add_line(name,'MassEnergyCylinder/1','MechanicalMassThermal/1');
 add_line(name,'MassEnergyCylinder/1','StateTrace/1','autorouting','on');add_line(name,'MassEnergyCylinder/2','PressureTrace/1');
 set_param(name,'Solver','ode45','RelTol','1e-9','AbsTol','1e-11','MaxStep','.005','StopTime','2',...
  'OutputOption','SpecifiedOutputTimes','OutputTimes','0:.01:2','ReturnWorkspaceOutputs','on');
 save_system(name,path);close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
end
