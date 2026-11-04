function report = validate_alstom_reference(source_directory,output_directory)
%VALIDATE_ALSTOM_REFERENCE Native Windows checks and canonical PI experiments.
% No result is produced on platforms that cannot load the author's MEX.
here=fileparts(mfilename('fullpath'));
if nargin<1||isempty(source_directory)
 source_directory=fullfile(here,'external','alstom-gasifier','Gasifier_R2017');
end
if nargin<2,output_directory=fullfile(here,'results','alstom-native');end
assert(ispc && strcmp(computer('arch'),'win64'),...
 'ALSTOM:Platform','The official package requires Windows x64 MATLAB/Simulink.');
fixture=reshape(1:35,7,5);
assert(isequal(alstom_log_matrix(fixture,7,5,'fixture'),fixture));
assert(isequal(alstom_log_matrix(reshape(fixture',5,1,7),7,5,'fixture'),fixture));
assert(isequal(alstom_log_matrix(reshape(fixture',1,5,7),7,5,'fixture'),fixture));
assert(~isfolder(output_directory),'Choose a new result directory');
mkdir(output_directory);cases=cell(1,11);index=0;
comparisons=struct('case',{},'maximum_scaled_output_change',{});
for load_percent=[0 50 100]
 nominal=[];
 for scenario={'nominal','pressure_step','pressure_sine'}
  index=index+1;name=sprintf('load%03d-%s',load_percent,scenario{1});
  [cases{index},data]=run_alstom_reference(source_directory,fullfile(output_directory,[name '.csv']),...
   struct('load_percent',load_percent,'scenario',scenario{1}));
  if strcmp(scenario{1},'nominal')
   nominal=data;
   if load_percent==50,nominal50=data;end
  else
   % Compare trajectories on the disturbed run's grid. Solvers may choose
   % different output times, and events may create duplicate timestamps.
   [reference_times,unique_index]=unique(nominal.time_s,'stable');
   reference=interp1(reference_times,nominal.outputs(unique_index,:),data.time_s,'linear');
   scale=max(1,max(abs(reference),[],1));
   separation=max(max(abs(data.outputs-reference)./scale));
   assert(isfinite(separation)&&separation>1e-8,'Pressure disturbance did not affect the plant');
   comparisons(end+1)=struct('case',name,'maximum_scaled_output_change',separation); %#ok<AGROW>
  end
 end
end
for scenario={'load_ramp','coal_quality'}
 index=index+1;load_percent=100;if strcmp(scenario{1},'load_ramp'),load_percent=50;end
 [cases{index},~]=run_alstom_reference(source_directory,fullfile(output_directory,[scenario{1} '.csv']),...
  struct('load_percent',load_percent,'scenario',scenario{1}));
end
% Recheck the observed nominal drift with tighter integration and the exact
% solver/tolerance settings stored in the author's diagram. Keep this separate
% from the eleven challenge cases and do not retune the official controller.
sensitivity=cell(1,2);
for k=1:2
 profiles={'refined','author_default'};profile=profiles{k};
 [record,data]=run_alstom_reference(source_directory,...
  fullfile(output_directory,['load050-nominal-' profile '.csv']),...
  struct('load_percent',50,'scenario','nominal','solver_profile',profile));
 grid=(0:1:300)';[t0,i0]=unique(nominal50.time_s,'stable');[t1,i1]=unique(data.time_s,'stable');
 baseline=interp1(t0,nominal50.outputs(i0,:),grid,'linear');
 candidate=interp1(t1,data.outputs(i1,:),grid,'linear');
 scaled=max(abs(candidate-baseline)./[10000 500 10000 1],[],1);
 record.maximum_output_difference_scaled_to_pressure_limits=scaled;
 record.final_temperature_error_K=data.outputs(end,4)-data.setpoints(end,4);
 if strcmp(profile,'refined')
  assert(max(scaled)<.05,'Nominal output changed materially under solver refinement');
 end
 sensitivity{k}=record;
end
report=struct('date',datestr(now,'yyyy-mm-dd'),'status','integration_and_input_checks_passed',...
 'case_count',index,'cases',{cases},'pressure_comparisons',comparisons,...
 'solver_sensitivity',{sensitivity},'solver_refinement_check_passed',true,...
 'controller_performance_claim','See measured violations in each case; passing integration is not satisfaction of all challenge constraints',...
 'uncovered_challenge_scope','Other candidate controllers, full +/-18 percent coal-quality sweep, global stability assessment');
filename=fullfile(output_directory,'validation.json');
fid=fopen(filename,'w');assert(fid>0);cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
fwrite(fid,jsonencode(report,'PrettyPrint',true));
fprintf('ALSTOM: %d native PI cases completed; performance violations retained in %s.\n',index,filename);
end
