function paths=build_discrete_models(output_dir,overwrite)
%BUILD_DISCRETE_MODELS Article SISO/MIMO recurrences and sampled bioreactor.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
if nargin<2,overwrite=false;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
if ~exist(output_dir,'dir'),mkdir(output_dir);end
cases=paper_simulink_cases('discrete');paths=cell(size(cases,1),1);
for j=1:size(cases,1)
 name=['si_' cases{j,1}];paths{j}=fullfile(output_dir,[name '.slx']);
 if bdIsLoaded(name),error('Close model %s before building.',name);end
 if exist(paths{j},'file')&&~overwrite,error('Existing model preserved: %s',paths{j});end
 new_system(name);
 try
  ws=get_param(name,'ModelWorkspace');assignin(ws,'initial',cases{j,3});assignin(ws,'inputs',cases{j,4});
  assignin(ws,'dt',cases{j,5});assignin(ws,'ninputs',size(cases{j,4},2)-1);
  add_block('simulink/Sources/From Workspace',[name '/Excitation'],'VariableName','inputs','Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','dt','Position',[30 70 120 110]);
  add_block('simulink/User-Defined Functions/S-Function',[name '/Recurrence'],'FunctionName','paper_discrete_sfun',...
   'Parameters',['''' cases{j,2} ''',initial,dt,ninputs'],'Position',[185 60 350 120]);
  add_block('simulink/Sinks/To Workspace',[name '/State'],'VariableName','state_history','SaveFormat','StructureWithTime','Position',[420 70 530 110]);
  add_line(name,'Excitation/1','Recurrence/1');add_line(name,'Recurrence/1','State/1');
  set_param(name,'Solver','FixedStepDiscrete','FixedStep',num2str(cases{j,5}),...
   'StopTime',num2str(cases{j,4}(end,1)),'ReturnWorkspaceOutputs','on');
  save_system(name,paths{j});close_system(name,0);
 catch err,close_system(name,0);rethrow(err);end
end
fprintf('Generated three discrete article model diagrams.\n');
end
