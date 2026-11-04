function report=validate_throttle_reference(output_directory)
%VALIDATE_THROTTLE_REFERENCE Exercise the entire importer/fit on artificial data.
% This fixture is a stable known recurrence, not a physical throttle simulator
% or recovered measurement. No network or additional toolbox is required.
if nargin<1,output_directory=tempname;end
assert(~exist(output_directory,'dir') && ~exist(output_directory,'file'),'Use a fresh validation directory');
mkdir(output_directory);source_directory=fullfile(output_directory,'synthetic-source');mkdir(source_directory);
source_path=fullfile(source_directory,'fixture-description.txt');
description='SYNTHETIC integration fixture. Stable second-order recursion; no measured throttle records.';
fid=fopen(source_path,'wt');assert(fid>=0);fprintf(fid,'%s\n',description);fclose(fid);
provenance=struct('source_url','local:synthetic-integration-fixture', ...
 'source_title','Artificial throttle pipeline fixture','source_file','fixture-description.txt', ...
 'source_sha256',file_sha256(source_path), ...
 'license_notes','Repository-authored synthetic fixture; no third-party measurements.', ...
 'conversion_notes','Generated directly as CSV; no original experiment or archive.');
manifest=struct('schema_version',1,'dataset_kind','synthetic_fixture','sample_time_s',.01, ...
 'units',struct('time_s','s','duty_percent','%','angle_deg','deg'),'provenance',provenance, ...
 'experiments',struct);
counts=[10000 2500];splits={'train','test'};data=struct;
for j=1:2
 n=counts(j);t=(0:n-1)'*.01;rng(1400+j,'twister');
 levels=50+40*(rand(ceil(n/17),1)-.5);u=levels(ceil((1:n)'/17));y=ones(n,1)*(41+j);
 for k=3:n,y(k)=1.2*y(k-1)-.3*y(k-2)+.05*u(k-1)+2;end
 name=[splits{j} '.csv'];path=fullfile(source_directory,name);
 fid=fopen(path,'wt');assert(fid>=0);fprintf(fid,'time_s,duty_percent,angle_deg\n');
 fprintf(fid,'%.17g,%.17g,%.17g\n',[t u y]');fclose(fid);
 manifest.experiments.(splits{j})=struct('csv_file',name,'sha256',file_sha256(path), ...
  'rows',n,'original_member',['synthetic:' splits{j}]);
 data.(splits{j})=struct('u',u,'y',y);
end
manifest_path=fullfile(source_directory,'manifest.json');fid=fopen(manifest_path,'wt');assert(fid>=0);
fprintf(fid,'%s\n',jsonencode(manifest));fclose(fid);

% A PK prefix alone is not an archive. Construct a tiny valid empty member
% independently of external ZIP utilities to exercise both structure and
% membership rejection in the measured-candidate path.
archive_path=fullfile(source_directory,'archive-fixture.zip');
fid=fopen(archive_path,'wb');fwrite(fid,uint8([80 75 3 4 0 0]));fclose(fid);
candidate=manifest;candidate.dataset_kind='measured_original_candidate';
candidate.provenance.source_file='archive-fixture.zip';candidate.provenance.source_sha256=file_sha256(archive_path);
candidate_path=fullfile(source_directory,'candidate-rejection-manifest.json');write_manifest(candidate_path,candidate);
rejected=false;
try,run_throttle_reference(candidate_path,fullfile(output_directory,'fake-pk'),true);
catch err,rejected=~isempty(strfind(err.message,'ZIP'));end
assert(rejected,'A fake PK signature must not be accepted as an archive');
write_empty_member_zip(archive_path,'present.txt');
assert(isequal(throttle_zip_members(archive_path),{'present.txt'}),'Valid ZIP central directory must be read');
candidate.provenance.source_sha256=file_sha256(archive_path);write_manifest(candidate_path,candidate);
rejected=false;
try,run_throttle_reference(candidate_path,fullfile(output_directory,'missing-member'),true);
catch err,rejected=~isempty(strfind(err.message,'original_member is absent'));end
assert(rejected,'Missing original archive members must be rejected');

rejected=false;
try,run_throttle_reference(manifest_path,fullfile(output_directory,'no-opt-in'));
catch err,rejected=~isempty(strfind(err.message,'opt-in'));end
assert(rejected,'Synthetic data must require opt-in');

fid=fopen(source_path,'at');fprintf(fid,'modified source\n');fclose(fid);
rejected=false;
try,run_throttle_reference(manifest_path,fullfile(output_directory,'modified-source'),true);
catch err,rejected=~isempty(strfind(err.message,'SHA-256 mismatch'));end
assert(rejected,'Changed source bytes must be rejected');
fid=fopen(source_path,'wt');fprintf(fid,'%s\n',description);fclose(fid);

report=run_throttle_reference(manifest_path,fullfile(output_directory,'evaluation'),true);
assert(strcmp(report.status,'executed_synthetic_fixture'));
assert(~report.paper_table_11_reproduced && ~report.historical_source_authenticity_verified_by_this_runner);
modes={'crisp','soft'};
for j=1:2
 mode=modes{j};model=local_arx_fit(data.train.u,data.train.y,mode,8);
 expected_z=[diff(data.train.y(1:end-1)) data.train.u(2:end-1)];
 assert(max(abs(model.mean-mean(expected_z)))<1e-12,'Partition scaling must use training only');
 first=local_arx_predict(model,data.test.u,data.test.y,true);
 changed=data.test.y;changed(3:end)=changed(3:end)+80;
 second=local_arx_predict(model,data.test.u,changed,true);
 assert(isequal(first,second),'Free run must ignore all measured outputs after its two seeds');
 measured_prediction=local_arx_predict(model,data.test.u,data.test.y,false);
 altered_prediction=local_arx_predict(model,data.test.u,changed,false);
 assert(max(abs(measured_prediction-altered_prediction))>1,'One-step mode must read measured history');
 for k=1:2
  result=report.models.(mode).experiments.(splits{k});types={'one_step','free_run'};
  for m=1:2
   metric=result.(types{m});
   assert(metric.scored_samples==counts(k)-2 && metric.seed_samples_excluded==2);
   assert(metric.rmse_deg<1e-5,'Known synthetic recurrence should be recovered accurately');
  end
 end
end
report.fixture_checks_passed=true;
report.fixture_checks={'explicit synthetic opt-in','original-source hash mismatch rejection', ...
 'fake PK signature rejection','valid ZIP central-directory parsing','missing archive member rejection', ...
 'full 10000/2500-row experiment import','train-only partition normalization', ...
 'free-run independence from future measured outputs','one-step measured-history dependence', ...
 'two seed samples excluded','known synthetic recurrence accuracy'};
fid=fopen(fullfile(output_directory,'fixture-validation.json'),'wt');assert(fid>=0);
fprintf(fid,'%s\n',jsonencode(report));fclose(fid);
fprintf('Throttle synthetic integration fixture passed: train=10000, test=2500, rules=8.\n');
end

function write_manifest(path,value)
fid=fopen(path,'wt');assert(fid>=0);fprintf(fid,'%s\n',jsonencode(value));fclose(fid);
end

function write_empty_member_zip(path,name)
% Classic ZIP with a zero-byte, uncompressed ASCII member, CRC-32 = 0.
name=uint8(name);local=[uint8([80 75 3 4]) le(20,2) zeros(1,20,'uint8') le(numel(name),2) le(0,2) name];
central=[uint8([80 75 1 2]) le(20,2) le(20,2) zeros(1,20,'uint8') ...
 le(numel(name),2) zeros(1,16,'uint8') name];
eocd=[uint8([80 75 5 6]) zeros(1,4,'uint8') le(1,2) le(1,2) ...
 le(numel(central),4) le(numel(local),4) le(0,2)];
fid=fopen(path,'wb');assert(fid>=0);fwrite(fid,[local central eocd],'uint8');fclose(fid);
end

function bytes=le(value,width)
bytes=uint8(mod(floor(double(value)./(256.^(0:width-1))),256));
end

function result=file_sha256(path)
fid=fopen(path,'rb');assert(fid>=0);bytes=fread(fid,Inf,'*uint8');fclose(fid);
if exist('OCTAVE_VERSION','builtin')
 result=hash('sha256',char(bytes'));
else
 digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);
 result=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2)',1,[]));
end
end
