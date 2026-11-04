function report=validate_intelligent_simulink(output_dir)
%VALIDATE_INTELLIGENT_SIMULINK Match both diagrams to independent lesson loops.
if nargin<1,output_dir=tempname;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
fuzzy=run_lesson(5,false);neural=run_lesson(6,false);native=validate_intelligent_adapters(fuzzy,neural);
paths=build_intelligent_models(output_dir,false,neural);records=cell(2,1);
for j=1:2
 [~,name]=fileparts(paths{j});load_system(paths{j});cleanup=onCleanup(@()close_system(name,0));
 output=sim(name);trace=output.get('concentration');controller=output.get('controller_trace');
 if j==1
  expected=fuzzy.fuzzy_pid.y;inputs=fuzzy.fuzzy_pid.u(1:end-1);
  assert(max(abs(controller.signals.values(:,5)))>1e-5,'Derivative action must be active.');
 else
  expected=neural.y;inputs=neural.neural_inputs(1:end-1);
 end
 assert(numel(trace.time)==numel(neural.t)&&max(abs(trace.time(:)-neural.t))<1e-10);
 state_error=max(abs(trace.signals.values(:)-expected));
 input_error=max(abs(controller.signals.values(1:end-1,1)-inputs));
 assert(state_error<1e-10&&input_error<1e-10);
 records{j}=struct('model',name,'state_max_error',state_error,'input_max_error',input_error,'passed',true);
 export_model_diagram(name,fullfile(output_dir,[name '.png']));clear cleanup;
end
report=struct('models',{records},'native_checks',native,'generated_models',2,'passed',true);
fprintf('Fuzzy PID and neural RBF Simulink diagrams matched native labs.\n');
end
