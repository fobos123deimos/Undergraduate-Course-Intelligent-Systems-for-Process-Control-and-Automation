function paths = build_models(output_dir, overwrite)
%BUILD_MODELS Generate executable plants and closed-loop Simulink diagrams.
% Requires MATLAB with Simulink. Existing files are preserved by default.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
if exist('new_system','file')==0 && exist('new_system','builtin')==0,error('MATLAB with Simulink is required.');end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if ~exist(output_dir,'dir'),mkdir(output_dir);end
specs={...
 'blend_physical','blending',[0;2],[500;200;.4;.75;700],struct('ninputs',5,'rho',1000),10;...
 'paper_pendulum','pendulum',[.03;0;0;0],0,struct('ninputs',1),.5;...
 'paper_three_tank','three_tank',[.3;.3;.3],[0;0],struct('ninputs',2),20;...
 'paper_bioreactor','bioreactor',[.08729754781771586;.9235897740828826],.769,struct('ninputs',1),5;...
 'paper_cstr','cstr',[3517.5;740;87;79.8],[8.256;-6.239],struct('ninputs',2),.05;...
 'paper_column_a','column_a',[linspace(.01,.99,41)';.5*ones(41,1)],[2.70629;3.20629;.5;.5;1;.5;1],struct('ninputs',7),.2};
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
  set_param(name,'Solver','ode15s','StopTime',num2str(specs{k,6}),'MaxStep','0.01','ReturnWorkspaceOutputs','on');
  save_system(name,paths{k});close_system(name,0);
 catch err
  close_system(name,0);rethrow(err);
 end
end
name='si_tank_pi';paths{end-1}=prepare(name,output_dir,overwrite);new_system(name);
try
 add_block('simulink/Sources/Step',[name '/Reference'],'Time','10','Before','.35','After','.65','Position',[25 70 55 100]);
 add_block('simulink/Sources/Step',[name '/FinalReferenceChange'],'Time','55','Before','0','After','-.2','Position',[25 10 55 40]);
 add_block('simulink/Math Operations/Sum',[name '/ReferenceSum'],'Inputs','++','Position',[65 65 85 95]);
 add_block('simulink/Math Operations/Sum',[name '/Error'],'Inputs','+-','Position',[90 70 110 100]);
 add_block('simulink/Math Operations/Gain',[name '/Kp'],'Gain','2','Position',[155 35 200 65]);
 add_block('simulink/Math Operations/Gain',[name '/Ki'],'Gain','.2','Position',[155 115 200 145]);
 add_block('simulink/Continuous/Integrator',[name '/Integral'],'InitialCondition','.35','Position',[240 115 270 145]);
 add_block('simulink/Math Operations/Sum',[name '/PI'],'Inputs','++','Position',[310 70 330 100]);
 add_block('simulink/Discontinuities/Saturation',[name '/Actuator'],'UpperLimit','1','LowerLimit','0','Position',[370 70 420 100]);
 add_block('simulink/Continuous/State-Space',[name '/Tank'],'A','-.1','B','.1','C','1','D','0','X0','.35','Position',[465 70 540 100]);
 add_block('simulink/Sources/Step',[name '/InletDisturbance'],'Time','45','Before','0','After','.08','Position',[370 5 420 35]);
 add_block('simulink/Math Operations/Sum',[name '/Feed'],'Inputs','++','Position',[435 70 455 100]);
 add_block('simulink/Sinks/To Workspace',[name '/Output'],'VariableName','concentration','SaveFormat','StructureWithTime','Position',[595 65 690 105]);
 add_line(name,'Reference/1','ReferenceSum/1');add_line(name,'FinalReferenceChange/1','ReferenceSum/2');add_line(name,'ReferenceSum/1','Error/1');add_line(name,'Error/1','Kp/1');add_line(name,'Error/1','Ki/1');
 add_line(name,'Ki/1','Integral/1');add_line(name,'Integral/1','PI/2');add_line(name,'Kp/1','PI/1');
 add_line(name,'PI/1','Actuator/1');add_line(name,'Actuator/1','Feed/1');add_line(name,'InletDisturbance/1','Feed/2');add_line(name,'Feed/1','Tank/1');add_line(name,'Tank/1','Output/1');add_line(name,'Tank/1','Error/2','autorouting','on');
 % Back-calculation anti-windup: I_dot = Ki*e + .6*(u_sat-u_raw).
 add_block('simulink/Math Operations/Sum',[name '/SatDifference'],'Inputs','+-','Position',[375 185 395 215]);
 add_block('simulink/Math Operations/Gain',[name '/BackCalculation'],'Gain','.6','Position',[290 185 340 215]);
 add_block('simulink/Math Operations/Sum',[name '/IntegralRate'],'Inputs','++','Position',[215 115 235 145]);
 delete_line(name,'Ki/1','Integral/1');add_line(name,'Ki/1','IntegralRate/1');add_line(name,'IntegralRate/1','Integral/1');
 add_line(name,'Actuator/1','SatDifference/1','autorouting','on');add_line(name,'PI/1','SatDifference/2','autorouting','on');
 add_line(name,'SatDifference/1','BackCalculation/1','autorouting','on');add_line(name,'BackCalculation/1','IntegralRate/2','autorouting','on');
 set_param(name,'StopTime','80','Solver','ode45','MaxStep','.05','ReturnWorkspaceOutputs','on');
 save_system(name,paths{end-1});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
name='si_mimo_mpc';paths{end}=prepare(name,output_dir,overwrite);new_system(name);
try
 add_block('simulink/Sources/Constant',[name '/Reference'],'Value','[.4;.5]','Position',[30 130 95 160]);
 add_block('simulink/Signal Routing/Mux',[name '/MeasurementsReference'],'Inputs','2','Position',[150 65 155 155]);
 add_block('simulink/User-Defined Functions/S-Function',[name '/MPC'],'FunctionName','mpc_sfun','Position',[210 80 295 120]);
 add_block('simulink/Discrete/Discrete State-Space',[name '/Plant'],'A','diag([.96 .94])','B','[.04 .012;.01 .05]','C','eye(2)','D','zeros(2)','SampleTime','.2','Position',[355 80 455 120]);
 add_block('simulink/Sinks/To Workspace',[name '/States'],'VariableName','mimo_states','SaveFormat','StructureWithTime','Position',[520 80 615 120]);
 add_line(name,'Reference/1','MeasurementsReference/2');add_line(name,'MeasurementsReference/1','MPC/1');
 add_line(name,'MPC/1','Plant/1');add_line(name,'Plant/1','States/1');add_line(name,'Plant/1','MeasurementsReference/1','autorouting','on');
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
