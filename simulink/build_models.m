function paths = build_models(output_dir, overwrite)
%BUILD_MODELS Generate executable plants and closed-loop Simulink diagrams.
% Requires MATLAB with Simulink. Existing files are preserved by default.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
if exist('new_system','file')==0 && exist('new_system','builtin')==0,error('MATLAB with Simulink is required.');end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if ~exist(output_dir,'dir'),mkdir(output_dir);end
specs=paper_simulink_cases('continuous');
paths=cell(size(specs,1)+2,1);
for k=1:size(specs,1)
 name=['si_' specs{k,1}];paths{k}=prepare(name,output_dir,overwrite);
 new_system(name);
 try
  ws=get_param(name,'ModelWorkspace');assignin(ws,'xinit',specs{k,3});assignin(ws,'inlet',specs{k,4});assignin(ws,'params',specs{k,5});
  add_block('simulink/Sources/Constant',[name '/Input'],'Value','inlet','Position',[40 70 100 100]);
  add_block('simulink/User-Defined Functions/S-Function',[name '/Plant'],'FunctionName','process_sfun',...
   'Parameters',['''' specs{k,2} ''',xinit,params'],'Position',[160 60 300 110]);
  add_block('simulink/Sinks/To Workspace',[name '/States'],'VariableName','state_history','SaveFormat','StructureWithTime','Position',[370 60 470 110]);
  add_line(name,'Input/1','Plant/1');add_line(name,'Plant/1','States/1');
  set_param(name,'Solver','ode15s','StopTime',num2str(specs{k,6}),...
   'MaxStep',num2str(min(.01,specs{k,6}/100),17),'RelTol','1e-8','AbsTol','1e-10','ReturnWorkspaceOutputs','on');
  save_system(name,paths{k});close_system(name,0);
 catch err
  close_system(name,0);rethrow(err);
 end
end
name='si_tank_pi';paths{end-1}=prepare(name,output_dir,overwrite);new_system(name);
try
 add_block('simulink/Sources/Step',[name '/Reference'],'Time','10','Before','.35','After','.65','Position',[40 180 90 220]);
 add_block('simulink/Sources/Step',[name '/FinalReferenceChange'],'Time','55','Before','0','After','-.2','Position',[40 50 90 90]);
 add_block('simulink/Math Operations/Sum',[name '/ReferenceSum'],'Inputs','++','Position',[210 160 240 200]);
 add_block('simulink/Math Operations/Sum',[name '/Error'],'Inputs','+-','Position',[350 160 380 200]);
 add_block('simulink/Math Operations/Gain',[name '/Kp'],'Gain','2','Position',[480 75 530 115]);
 add_block('simulink/Math Operations/Gain',[name '/Ki'],'Gain','.2','Position',[480 280 530 320]);
 add_block('simulink/Continuous/Integrator',[name '/Integral'],'InitialCondition','.35','Position',[790 280 825 320]);
 add_block('simulink/Math Operations/Sum',[name '/PI'],'Inputs','++','Position',[930 160 960 200]);
 add_block('simulink/Discontinuities/Saturation',[name '/Actuator'],'UpperLimit','1','LowerLimit','0','Position',[1060 160 1120 200]);
 add_block('simulink/Continuous/State-Space',[name '/Tank'],'A','-.1','B','.1','C','1','D','0','X0','.35','Position',[1410 160 1530 200]);
 add_block('simulink/Sources/Step',[name '/InletDisturbance'],'Time','45','Before','0','After','.08','Position',[1100 30 1160 70]);
 add_block('simulink/Math Operations/Sum',[name '/Feed'],'Inputs','++','Position',[1260 160 1290 200]);
 add_block('simulink/Sinks/To Workspace',[name '/Output'],'VariableName','concentration','SaveFormat','StructureWithTime','Position',[1640 155 1770 205]);
 add_line(name,'Reference/1','ReferenceSum/1');add_line(name,'FinalReferenceChange/1','ReferenceSum/2');add_line(name,'ReferenceSum/1','Error/1');add_line(name,'Error/1','Kp/1');add_line(name,'Error/1','Ki/1');
 add_line(name,'Ki/1','Integral/1');add_line(name,'Integral/1','PI/2');add_line(name,'Kp/1','PI/1');
 add_line(name,'PI/1','Actuator/1');add_line(name,'Actuator/1','Feed/1');add_line(name,'InletDisturbance/1','Feed/2');add_line(name,'Feed/1','Tank/1');add_line(name,'Tank/1','Output/1');add_line(name,'Tank/1','Error/2','autorouting','on');
 % Back-calculation anti-windup: I_dot = Ki*e + .6*(u_sat-u_raw).
 add_block('simulink/Math Operations/Sum',[name '/SatDifference'],'Inputs','+-','Position',[1075 440 1105 480]);
 add_block('simulink/Math Operations/Gain',[name '/BackCalculation'],'Gain','.6','Orientation','left','Position',[825 440 885 480]);
 add_block('simulink/Math Operations/Sum',[name '/IntegralRate'],'Inputs','++','Position',[640 280 670 320]);
 delete_line(name,'Ki/1','Integral/1');add_line(name,'Ki/1','IntegralRate/1');add_line(name,'IntegralRate/1','Integral/1');
 add_line(name,'Actuator/1','SatDifference/1','autorouting','on');add_line(name,'PI/1','SatDifference/2','autorouting','on');
 add_line(name,'SatDifference/1','BackCalculation/1','autorouting','on');add_line(name,'BackCalculation/1','IntegralRate/2','autorouting','on');
 set_param(name,'StopTime','80','Solver','ode45','MaxStep','.05','ReturnWorkspaceOutputs','on');
 save_system(name,paths{end-1});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
name='si_mimo_mpc';paths{end}=prepare(name,output_dir,overwrite);new_system(name);
try
 add_block('simulink/Sources/Constant',[name '/Reference'],'Value','[.4;.5]','Position',[40 210 130 250]);
 add_block('simulink/Signal Routing/Mux',[name '/StateReference'],'Inputs','2','Position',[230 80 235 240]);
 add_block('simulink/User-Defined Functions/S-Function',[name '/MPC'],'FunctionName','mpc_sfun','Position',[360 110 490 170]);
 add_block('simulink/Discrete/Discrete State-Space',[name '/Plant'],'A','diag([.96 .94])','B','[.04 .012;.01 .05]','C','eye(2)','D','zeros(2)','SampleTime','.2','Position',[650 110 800 170]);
 add_block('simulink/Sinks/To Workspace',[name '/States'],'VariableName','mimo_states','SaveFormat','StructureWithTime','Position',[960 110 1090 170]);
 add_line(name,'Reference/1','StateReference/2');add_line(name,'StateReference/1','MPC/1');
 add_line(name,'MPC/1','Plant/1');add_line(name,'Plant/1','States/1');add_line(name,'Plant/1','StateReference/1','autorouting','on');
 set_param(name,'StopTime','20','Solver','FixedStepDiscrete','FixedStep','.2','ReturnWorkspaceOutputs','on');
 save_system(name,paths{end});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
fprintf('Generated %d Simulink models in %s.\n',numel(paths),output_dir);
end
function path=prepare(name,folder,overwrite)
path=fullfile(folder,[name '.slx']);
if bdIsLoaded(name),error('Model %s is open; close it before generating.',name);end
if exist(path,'file') && ~overwrite,error('File exists: %s. Pass overwrite=true explicitly to replace.',path);end
end
