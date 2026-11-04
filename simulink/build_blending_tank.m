function paths = build_blending_tank(output_dir, overwrite)
%BUILD_BLENDING_TANK Generate two fresh corrected physical-tank diagrams.
%   paths = build_blending_tank() requires MATLAB with Simulink only.
%   No Control System Toolbox and no files from the historical project are used.
%   Existing files and loaded model names are refused unless overwrite=true
%   is explicitly supplied; loaded models are always refused.
%
% First model: nonlinear startup, editable model-workspace physical_input.
% Second model: matched nonlinear, deviation state-space and transfer matrix.
% All three comparison branches start at the SAME physical equilibrium.
% State [X;V]; input [w1;w2;x1;x2;wout]; kg/min, min, m^3, kg/m^3.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
if exist('new_system','file')==0&&exist('new_system','builtin')==0
 error('build_blending_tank:Runtime','MATLAB with Simulink is required.');
end
if ~isscalar(overwrite)||(~islogical(overwrite)&&~ismember(overwrite,[0 1]))
 error('build_blending_tank:Overwrite','overwrite must be true or false.');
end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
p=bt_parameters();lin=bt_linearize(p.xbar,p.ubar,p,true);
if norm(lin.A-diag(diag(lin.A)),Inf)>1e-12||abs(lin.A(2,2))>1e-12||...
   norm(lin.C-eye(2),Inf)>1e-12||norm(lin.D,Inf)>1e-12
 error('build_blending_tank:Structure','The transfer diagram requires the stated tank equilibrium structure.');
end
names={'bt_nonlinear_corrected','bt_comparison_corrected'};
paths=cell(size(names));
for k=1:numel(names)
 paths{k}=fullfile(output_dir,[names{k} '.slx']);
 if bdIsLoaded(names{k}),error('build_blending_tank:Loaded','Close loaded model %s first.',names{k});end
 if exist(paths{k},'file')&&~overwrite
  error('build_blending_tank:Exists','File exists: %s. Supply overwrite=true to replace it.',paths{k});
 end
end
if ~exist(output_dir,'dir'),mkdir(output_dir);end

name=names{1};new_system(name);
try
 ws=get_param(name,'ModelWorkspace');assignin(ws,'p',p);
 assignin(ws,'xinit',[0;2]);assignin(ws,'physical_input',p.ubar);
 add_block('simulink/Sources/Constant',[name '/Physical input'],...
  'Value','physical_input','Position',[50 90 150 130]);
 add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[name '/Nonlinear'],...
  'FunctionName','bt_sfun','Parameters','xinit,p','Position',[235 80 385 140]);
 add_sink(name,'Physical states','state_history',[490 80 620 140]);
 add_line(name,'Physical input/1','Nonlinear/1');
 add_line(name,'Nonlinear/1','Physical states/1');
 configure_solver(name);
 set_param(name,'Description',sprintf(['Corrected variable-volume physical tank.\n'...
  'Input [w1,w2,x1,x2,wout]; output [X,V].\n'...
  'Edit model-workspace physical_input(5) from 700 to 650 for filling.\n'...
  'Density 1000 kg/m^3 is an explicit teaching assumption.']));
 save_system(name,paths{1});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end

name=names{2};new_system(name);
try
 ws=get_param(name,'ModelWorkspace');assignin(ws,'p',p);assignin(ws,'lin',lin);
 assignin(ws,'xbar',p.xbar);assignin(ws,'ubar',p.ubar);
 assignin(ws,'delta_u',[10;0;0;0;0]);assignin(ws,'step_time',5);
 add_block('simulink/Sources/Step',[name '/Input deviation'],...
  'Time','step_time','Before','zeros(5,1)','After','delta_u',...
  'SampleTime','0','Position',[30 165 100 205]);
 add_block('simulink/Sources/Constant',[name '/Nominal input'],...
  'Value','ubar','Position',[30 55 100 95]);
 add_block('simulink/Math Operations/Sum',[name '/Physical input'],...
  'Inputs','++','Position',[150 80 175 120]);
 add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[name '/Nonlinear'],...
  'FunctionName','bt_sfun','Parameters','xbar,p','Position',[230 70 390 130]);
 add_sink(name,'Nonlinear states','nonlinear_states',[940 70 1080 120]);
 add_line(name,'Nominal input/1','Physical input/1');
 add_line(name,'Input deviation/1','Physical input/2','autorouting','on');
 add_line(name,'Physical input/1','Nonlinear/1');
 add_line(name,'Nonlinear/1','Nonlinear states/1');

 add_block('simulink/Continuous/State-Space',[name '/Deviation state space'],...
  'A','lin.A','B','lin.B','C','lin.C','D','lin.D','X0','zeros(2,1)',...
  'Position',[230 160 400 220]);
 add_block('simulink/Sources/Constant',[name '/Nominal state'],...
  'Value','xbar','Position',[580 165 660 205]);
 add_block('simulink/Math Operations/Sum',[name '/Restore state offset'],...
  'Inputs','++','Position',[820 165 845 205]);
 add_sink(name,'Linear states','linear_states',[940 160 1080 210]);
 add_line(name,'Input deviation/1','Deviation state space/1','autorouting','on');
 add_line(name,'Deviation state space/1','Restore state offset/1');
 add_line(name,'Nominal state/1','Restore state offset/2','autorouting','on');
 add_line(name,'Restore state offset/1','Linear states/1');

 % Each nonzero scalar transfer uses zero initial DEVIATION, not zero physical
 % concentration/volume. Reduced denominators avoid spurious cancellations.
 add_block('simulink/Signal Routing/Demux',[name '/Split input deviations'],...
  'Outputs','5','Position',[155 315 160 775]);
 add_line(name,'Input deviation/1','Split input deviations/1','autorouting','on');
 source_names={'dw1','dw2','dx1','dx2','dwout'};
 for row=1:2
  columns=find(abs(lin.B(row,:))>0);
  sum_name=sprintf('Sum output %d',row);row_y=405+280*(row-1);
  add_block('simulink/Math Operations/Sum',[name '/' sum_name],...
   'Inputs',repmat('+',1,numel(columns)),'Position',[690 row_y 715 row_y+45]);
  for j=1:numel(columns)
   column=columns(j);block_name=sprintf('G%d%d %s',row,column,source_names{column});
   y=285+70*(j-1)+330*(row-1);
   add_block('simulink/Continuous/Transfer Fcn',[name '/' block_name],...
    'Numerator',sprintf('lin.transfer_num{%d,%d}',row,column),...
    'Denominator',sprintf('lin.transfer_den{%d,%d}',row,column),...
    'Position',[350 y 535 y+40]);
   add_line(name,sprintf('Split input deviations/%d',column),[block_name '/1'],'autorouting','on');
   add_line(name,[block_name '/1'],sprintf('%s/%d',sum_name,j),'autorouting','on');
  end
 end
 add_block('simulink/Signal Routing/Mux',[name '/Transfer deviations'],...
  'Inputs','2','Position',[760 425 765 730]);
 add_block('simulink/Math Operations/Sum',[name '/Restore transfer offset'],...
  'Inputs','++','Position',[820 555 845 595]);
 add_sink(name,'Transfer states','transfer_states',[940 550 1080 600]);
 add_line(name,'Sum output 1/1','Transfer deviations/1');
 add_line(name,'Sum output 2/1','Transfer deviations/2');
 add_line(name,'Transfer deviations/1','Restore transfer offset/1');
 add_line(name,'Nominal state/1','Restore transfer offset/2','autorouting','on');
 add_line(name,'Restore transfer offset/1','Transfer states/1');
 configure_solver(name);
 set_param(name,'Description',sprintf(['Corrected comparison at xbar=[0.5;2], ubar=[500;200;0.4;0.75;700].\n'...
  'All linear paths operate on input/state deviations; offsets are restored.\n'...
  'The transfer branch is valid for zero initial deviation only.\n'...
  'The nonlinear branch is the physical reference; linear models are local approximations.']));
 save_system(name,paths{2});close_system(name,0);
catch err,close_system(name,0);rethrow(err);end
fprintf('Generated two corrected Blending Tank models in %s.\n',output_dir);
end

function add_sink(name,block_name,variable_name,position)
add_block('simulink/Sinks/To Workspace',[name '/' block_name],...
 'VariableName',variable_name,'SaveFormat','StructureWithTime','Position',position);
end

function configure_solver(name)
set_param(name,'Solver','ode45','StartTime','0','StopTime','30',...
 'MaxStep','0.02','RelTol','1e-8','AbsTol','1e-10',...
 'OutputOption','SpecifiedOutputTimes','OutputTimes','0:0.05:30',...
 'ReturnWorkspaceOutputs','on');
end
