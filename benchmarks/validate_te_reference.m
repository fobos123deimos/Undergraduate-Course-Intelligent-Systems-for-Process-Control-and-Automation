function report=validate_te_reference(source_directory,output_directory)
%VALIDATE_TE_REFERENCE Native official simulator integration and disturbance tests.
if nargin<1,source_directory=fullfile(fileparts(mfilename('fullpath')),'external','te-revised','temexd_mod');end
if nargin<2,output_directory=fullfile(fileparts(mfilename('fullpath')),'results','te-native');end
if ~isfolder(output_directory),mkdir(output_directory);end
source_directory=char(java.io.File(source_directory).getCanonicalPath());
output_directory=char(java.io.File(output_directory).getCanonicalPath());
[nominal,base]=run_te_reference(source_directory,fullfile(output_directory,'nominal.csv'));
assert(nominal.max_scaled_output_drift<.2,'Nominal short-horizon stationarity check failed');
faults=[1 4];cases=cell(1,numel(faults));
for k=1:numel(faults)
 [cases{k},data]=run_te_reference(source_directory,fullfile(output_directory,sprintf('idv-%02d.csv',faults(k))),...
  struct('disturbance',faults(k)));
 assert(isequal(data.time_h,base.time_h),'Fault and nominal time grids differ');
 distance=max(max(abs(data.measurements-base.measurements)./max(1,abs(base.measurements))));
 assert(distance>1e-5,'Disturbance has no observed effect');
 assert(all(data.disturbances(:,faults(k))==1),'Selected disturbance not logged active');
 cases{k}.max_scaled_difference_from_nominal=distance;
end
report=struct('date','2026-11-04','status','passed','nominal',nominal,'disturbance_cases',{cases},...
 'limitations','Three short mode1 integration checks; no complete six-mode or long-horizon benchmark claim');
fid=fopen(fullfile(output_directory,'validation.json'),'w');assert(fid>0);
cleanup=onCleanup(@() fclose(fid));fprintf(fid,'%s\n',jsonencode(report,'PrettyPrint',true));
fprintf('Official TE native validation passed: nominal, IDV1 and IDV4.\n');
end
