function report=validate_simulink_suite(output_dir)
%VALIDATE_SIMULINK_SUITE Build/run diagrams and export inspectable evidence.
% MATLAB+Simulink required. This function does not modify external simulators.
if nargin<1,output_dir=fullfile(fileparts(mfilename('fullpath')),'generated');end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
assert(license('test','Simulink'),'A licensed Simulink runtime is required.');
if ~exist(output_dir,'dir'),mkdir(output_dir);end
paths=build_models(fullfile(output_dir,'general'),false);cases=paper_simulink_cases('continuous');
records=cell(numel(paths),1);
for j=1:numel(paths)
 [~,name]=fileparts(paths{j});load_system(paths{j});cleanup=onCleanup(@()close_system(name,0));
 output=sim(name);
 if j<=size(cases,1)
  trace=output.get('state_history');t=trace.time(:);x=trace.signals.values;
  if strcmp(cases{j,2},'blending')
   p=bt_parameters();p.rho=cases{j,5}.rho;rhs=@(tt,xx)bt_rhs(tt,xx,cases{j,4},p);
  else
   rhs=@(~,xx)paper_models(cases{j,2},xx,cases{j,4},cases{j,5});
  end
  [~,reference]=ode15s(rhs,t,cases{j,3},odeset('RelTol',1e-10,'AbsTol',1e-12,'MaxStep',cases{j,6}/100));
  scale=max(1,max(abs(reference),[],1));difference=bsxfun(@rdivide,x-reference,scale);
  error_value=max(abs(difference(:)));assert(error_value<5e-5,'State adapter/reference mismatch.');
  records{j}=struct('model',name,'comparison','MATLAB ODE integration at logged times','scaled_max_error',error_value,'passed',true);
 elseif strcmp(name,'si_tank_pi')
  trace=output.get('concentration');x=trace.signals.values;
  assert(all(isfinite(x(:)))&&abs(x(end)-.45)<.015);
  records{j}=struct('model',name,'comparison','finite state and final tracking','final_tracking_error',abs(x(end)-.45),'passed',true);
 else
  trace=output.get('mimo_states');x=trace.signals.values;
  assert(all(isfinite(x(:)))&&norm(x(end,:)'-[.4;.5],Inf)<.03);
  records{j}=struct('model',name,'comparison','finite state and final tracking','final_tracking_error',norm(x(end,:)'-[.4;.5],Inf),'passed',true);
 end
 export_diagram(name,fullfile(output_dir,'general',[name '.png']));
 clear cleanup;
end
paths=build_discrete_models(fullfile(output_dir,'discrete'),false);cases=paper_simulink_cases('discrete');discrete=cell(numel(paths),1);
for j=1:numel(paths)
 [~,name]=fileparts(paths{j});load_system(paths{j});cleanup=onCleanup(@()close_system(name,0));
 output=sim(name);trace=output.get('state_history');actual=trace.signals.values;
 inputs=cases{j,4};expected=zeros(size(inputs,1),2);expected(1,:)=cases{j,3}';
 assert(numel(trace.time)==size(inputs,1)&&max(abs(trace.time(:)-inputs(:,1)))<1e-10);
 for k=1:size(inputs,1)-1
  next=paper_models(cases{j,2},expected(k,:)',inputs(k,2:end)');
  if strcmp(cases{j,2},'siso'),expected(k+1,:)=[next expected(k,1)];else,expected(k+1,:)=next';end
 end
 difference=actual-expected;error_value=max(abs(difference(:)));assert(error_value<1e-11);
 discrete{j}=struct('model',name,'max_reference_error',error_value,'passed',true);
 export_diagram(name,fullfile(output_dir,'discrete',[name '.png']));clear cleanup;
end
markov=validate_markov_simulink(fullfile(output_dir,'markov'));
intelligent=validate_intelligent_simulink(fullfile(output_dir,'intelligent'));
wind=validate_wind_pdc_simulink(fullfile(output_dir,'wind-control'));
tank=validate_blending_simulink(fullfile(output_dir,'blending'));
report=struct('runtime',version,'simulink',ver('simulink'),'generated_models',numel(records)+numel(discrete)+6+2+1+2,...
 'general_models',{records},'discrete_models',{discrete},'markov',markov,'intelligent',intelligent,'wind_pdc',wind,'physical_tank',tank,'passed',true);
path=fullfile(output_dir,'validation.json');fid=fopen(path,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(report,'PrettyPrint',true));clear cleanup;
fprintf('All %d generated Simulink models passed; evidence: %s\n',report.generated_models,path);
end
function export_diagram(name,path)
% Export a viewable model image along with each generated model artifact.
print(['-s' name],'-dpng','-r120',path);
end
