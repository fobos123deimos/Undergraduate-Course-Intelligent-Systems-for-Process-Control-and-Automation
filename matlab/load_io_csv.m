function [t,u,y]=load_io_csv(path,input_columns,output_columns,sample_time)
%LOAD_IO_CSV Strict named-column import of externally supplied I/O records.
% Supported CSV: one unquoted header, comma separators, finite real decimal
% or scientific-notation numbers, equal-width rows, no blank/comment records.
% No imputation, interpolation, row dropping, normalization or unit conversion.
% The source/version/units and split provenance belong in a separate manifest.
assert(isnumeric(sample_time) && isreal(sample_time) && isscalar(sample_time) && ...
 isfinite(sample_time) && sample_time>0,'Sample time must be finite and positive');
inputs=column_names(input_columns);outputs=column_names(output_columns);
selected=[inputs outputs];
assert(numel(unique(selected))==numel(selected),'Selected columns must be distinct');
if isstring(path),assert(isscalar(path),'One CSV path required');path=char(path);end
assert(ischar(path) && isrow(path) && ~isempty(path),'One CSV path required');
[fid,message]=fopen(path,'rt','n','UTF-8');
if fid<0,error('load_io_csv:OpenFailed','Cannot read CSV: %s',message);end
cleanup=onCleanup(@() fclose(fid));
header=fgetl(fid);assert(ischar(header),'CSV header is missing');
if ~isempty(header) && double(header(1))==65279,header=header(2:end);end
assert(~any(header=='"'),'Quoted CSV fields are not supported');
names=regexp(header,',','split');names=cellfun(@strtrim,names,'UniformOutput',false);
assert(all(~cellfun(@isempty,names)),'CSV header contains an empty name');
assert(numel(unique(names))==numel(names),'CSV header contains duplicate names');
[present,indices]=ismember(selected,names);
assert(all(present),'Required input/output CSV columns are missing');
data=zeros(1024,numel(names));count=0;line_number=1;
number='^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?$';
line=fgetl(fid);
while ischar(line)
 line_number=line_number+1;
 assert(~isempty(strtrim(line)),sprintf('Blank CSV record at line %d',line_number));
 assert(~any(line=='"'),sprintf('Quoted CSV field at line %d is unsupported',line_number));
 fields=regexp(line,',','split');
 assert(numel(fields)==numel(names),sprintf('CSV width mismatch at line %d',line_number));
 values=zeros(1,numel(names));
 for j=1:numel(names)
  token=strtrim(fields{j});
  assert(~isempty(regexp(token,number,'once')),sprintf('Invalid numeric field at line %d, column %d',line_number,j));
  values(j)=str2double(token);
 end
 assert(all(isfinite(values)),sprintf('Nonfinite CSV record at line %d',line_number));
 count=count+1;
 if count>size(data,1),data=[data;zeros(size(data))];end
 data(count,:)=values;
 line=fgetl(fid);
end
assert(count>=2,'CSV requires at least two complete finite observations');
data=data(1:count,:);
t=(0:size(data,1)-1)'*sample_time;
assert(all(isfinite(t)),'Sample-time range overflows finite time values');
u=data(:,indices(1:numel(inputs)));y=data(:,indices(numel(inputs)+1:end));
end

function names=column_names(value)
if ischar(value),value={value};elseif isstring(value),value=cellstr(value);end
assert(iscell(value) && ~isempty(value),'A nonempty column-name list is required');
names=reshape(value,1,[]);
for k=1:numel(names)
 assert(ischar(names{k}) && isrow(names{k}) && ~isempty(strtrim(names{k})),'Column names must be nonempty text');
 names{k}=strtrim(names{k});
 assert(~any(names{k}==',') && ~any(names{k}=='"') && ...
  ~any(names{k}==char(10)) && ~any(names{k}==char(13)),'Unsupported column name');
end
end
