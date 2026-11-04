function report = run_throttle_reference(manifest_path, output_directory, allow_synthetic_fixture)
%RUN_THROTTLE_REFERENCE Evaluate independently supplied throttle experiments.
% Same manifest/CSV contract as benchmarks/run_throttle_reference.py.
% Integrity does not establish historical authenticity. The LocalARX fit is
% educational; original fitted partitions and coefficients are unavailable.
if nargin<3,allow_synthetic_fixture=false;end
manifest_path=canonical_path(manifest_path);base=fileparts(manifest_path);
manifest=jsondecode(fileread(manifest_path));
assert(manifest.schema_version==1,'Unsupported manifest version');
kind=manifest.dataset_kind;
assert(any(strcmp(kind,{'measured_original_candidate','synthetic_fixture'})),'Explicit dataset kind required');
assert(~strcmp(kind,'synthetic_fixture') || allow_synthetic_fixture,'Synthetic fixture requires explicit opt-in');
assert(manifest.sample_time_s==.01,'Sampling must be 0.01 s');
assert(strcmp(manifest.units.time_s,'s') && strcmp(manifest.units.duty_percent,'%') && ...
 strcmp(manifest.units.angle_deg,'deg'),'Required units are s, percent, degrees');
source=manifest.provenance;
required={'source_url','source_title','license_notes','conversion_notes'};
for j=1:numel(required)
 assert(isfield(source,required{j}) && ischar(source.(required{j})) && ...
 ~isempty(strtrim(source.(required{j}))),'Incomplete source provenance');
end
source_path=bound_file(base,source.source_file,source.source_sha256);
members={};
if strcmp(kind,'measured_original_candidate')
 members=throttle_zip_members(source_path);
end
splits={'train','test'};counts=[10000 2500];records=struct;metadata=struct;
for j=1:2
 split=splits{j};item=manifest.experiments.(split);
 assert(item.rows==counts(j) && ischar(item.original_member) && ...
 ~isempty(strtrim(item.original_member)),'Incorrect row count or original member provenance');
 if strcmp(kind,'measured_original_candidate')
  assert(any(strcmp(item.original_member,members)),'Declared original_member is absent from the source ZIP');
 end
 path=bound_file(base,item.csv_file,item.sha256);
 [~,inputs,y]=load_io_csv(path,{'time_s','duty_percent'},{'angle_deg'},.01);
 t=inputs(:,1);u=inputs(:,2);
 assert(numel(t)==counts(j) && all(abs(diff(t)-.01)<=1e-9), ...
 'Incorrect experiment length or sample times');
 records.(split)=struct('t',t,'u',u,'y',y);
 item.first_time_s=t(1);item.last_time_s=t(end);
 item.angle_range_deg=[min(y) max(y)];item.duty_range_percent=[min(u) max(u)];
 metadata.(split)=item;
end
assert(~strcmp(metadata.train.sha256,metadata.test.sha256),'Train and test must be distinct files');
assert(~exist(output_directory,'file') && ~exist(output_directory,'dir'), ...
 'Use a fresh output directory; old results are not validation');
modes={'crisp','soft'};models=struct;traces=struct;
for j=1:2
 mode=modes{j};training=records.train;
 model=local_arx_fit(training.u,training.y,mode,8);
 summary=struct('training_mean',model.mean,'training_scale',model.scale, ...
 'centers',model.centers,'coefficients',model.coefficients,'experiments',struct);
 for k=1:2
  split=splits{k};data=records.(split);
  one_step=local_arx_predict(model,data.u,data.y,false);
  free_run=local_arx_predict(model,data.u,data.y,true);
  summary.experiments.(split)=struct('one_step',metrics(data.y,one_step),'free_run',metrics(data.y,free_run));
  traces.([mode '_' split])=[data.t data.u data.y one_step free_run];
 end
 models.(mode)=summary;
end
report=struct('status',['executed_' kind],'runtime',version,'manifest_sha256',file_sha256(manifest_path), ...
 'dataset_kind',kind,'provenance',source,'experiments',metadata,'rules',8,'sample_time_s',.01,'models',models, ...
 'historical_source_authenticity_verified_by_this_runner',false,'paper_table_11_reproduced',false, ...
 'method','Teaching LocalARX fit: training-only k-means partitions, nearest-center crisp or inverse-distance soft weights, ridge 1e-8. Original fitted partitions/coefficients are not supplied.', ...
 'protocol','Whole supplied experiments; no shuffled split or test fitting. Two measured seeds per experiment, excluded from scores. Free run then uses predicted outputs only.');
mkdir(output_directory);names=fieldnames(traces);
for j=1:numel(names)
 path=fullfile(output_directory,[names{j} '.csv']);fid=fopen(path,'wt');
 assert(fid>=0,'Cannot create prediction CSV');
 fprintf(fid,'time_s,duty_percent,angle_deg,one_step_deg,free_run_deg\n');
 fprintf(fid,'%.17g,%.17g,%.17g,%.17g,%.17g\n',traces.(names{j})');fclose(fid);
end
fid=fopen(fullfile(output_directory,'validation.json'),'wt');assert(fid>=0,'Cannot create report');
fprintf(fid,'%s\n',jsonencode(report));fclose(fid);
end

function result=metrics(measured,predicted)
measured=measured(3:end);predicted=predicted(3:end);
assert(isequal(size(measured),size(predicted)) && all(isfinite(predicted)),'Invalid predictions');
error=predicted-measured;denominator=norm(measured-mean(measured));
fit=NaN;if denominator>0,fit=100*(1-norm(error)/denominator);end
result=struct('scored_samples',numel(error),'seed_samples_excluded',2, ...
 'rmse_deg',sqrt(mean(error.^2)),'maximum_absolute_error_deg',max(abs(error)), 'fit_percent',fit);
end

function path=bound_file(base,name,expected)
assert(ischar(name) && ~isempty(name) && isempty(regexp(name,'(^[/\\]|^[A-Za-z]:)','once')), ...
 'Manifest paths must be relative');
path=canonical_path(fullfile(base,name));prefix=[base filesep];
assert(strncmp(path,prefix,numel(prefix)) && exist(path,'file')==2,'Manifest file is absent or outside its directory');
assert(ischar(expected) && ~isempty(regexp(expected,'^[0-9a-f]{64}$','once')), ...
 'Actual SHA-256 required, not a placeholder');
assert(strcmp(file_sha256(path),expected),['SHA-256 mismatch: ' name]);
end

function path=canonical_path(path)
if exist('OCTAVE_VERSION','builtin')
 path=canonicalize_file_name(path);assert(~isempty(path),'Path does not exist');
else
 path=char(java.io.File(path).getCanonicalPath());
end
end

function result=file_sha256(path)
fid=fopen(path,'rb');assert(fid>=0,'Cannot read source file');
bytes=fread(fid,Inf,'*uint8');fclose(fid);
if exist('OCTAVE_VERSION','builtin')
 result=hash('sha256',char(bytes'));
else
 digest=java.security.MessageDigest.getInstance('SHA-256');digest.update(bytes);
 result=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2)',1,[]));
end
end
