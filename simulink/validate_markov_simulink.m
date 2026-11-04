function report=validate_markov_simulink(output_dir)
%VALIDATE_MARKOV_SIMULINK Compare actual diagrams to independent batch loops.
if nargin<1,output_dir=tempname;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
lab=run_markov_lab(false);native=validate_online_hmm(lab);
paths=build_markov_models(output_dir,false,lab);records=cell(6,1);
for j=1:6
 [~,name]=fileparts(paths{j});load_system(paths{j});cleanup=onCleanup(@()close_system(name,0));
 output=sim(name);
 if j==1
  trace=output.get('occupancy');actual=trace.signals.values;expected=zeros(size(actual));
  for k=1:size(actual,1),expected(k,:)=markov_models('propagate',lab.transition_true,lab.initial_true,k-1);end
  difference=actual-expected;error_value=max(abs(difference(:)));
  assert(size(actual,1)==101&&error_value<1e-11);
 elseif j==2
  trace=output.get('posterior');actual=trace.signals.values;
  assert(numel(trace.time)==numel(lab.t)&&max(abs(trace.time(:)-lab.t))<1e-10);
  difference=actual-lab.filtered;error_value=max(abs(difference(:)));assert(error_value<1e-11);
 else
  names={'nominal_baseline','nominal_supervisor','mismatch_baseline','mismatch_supervisor'};
  reference=lab.(names{j-2});trace=output.get('concentration');controller=output.get('controller_trace');
  assert(numel(trace.time)==numel(lab.t)&&max(abs(trace.time(:)-lab.t))<1e-10);
  expected=[reference.input reference.posterior reference.corrected_measurement];
  difference=controller.signals.values(:,1:5)-expected;
  error_value=max([abs(difference(:));abs(trace.signals.values(:)-reference.concentration)]);
  assert(error_value<1e-10);
 end
 records{j}=struct('model',name,'samples',numel(trace.time),'max_reference_error',error_value,'passed',true);
 print(['-s' name],'-dpng','-r120',fullfile(output_dir,[name '.png']));
 clear cleanup;
end
report=struct('runtime','MATLAB with Simulink','models',{records},'native_checks',native,'generated_models',6,'passed',true);
fprintf('Six Markov/HMM diagrams matched chain, filter and control references.\n');
end
