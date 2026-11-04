function record=validate_io_csv()
%VALIDATE_IO_CSV Alignment and strict rejection using temporary test fixtures.
% These small numeric fixtures test import mechanics, not measured benchmarks.
path=[tempname '.csv'];cleanup=onCleanup(@() remove_fixture(path));
write_fixture(path,sprintf('output, valve,flow\n10, .2,1e-3\n20,+.4,2e-3\n30,.6,3e-3\n'));
[t,u,y]=load_io_csv(path,{'flow','valve'},'output',.01);
assert(isequal(size(u),[3 2]) && isequal(size(y),[3 1]));
assert(norm(t-[0;.01;.02],Inf)<eps && norm(y-[10;20;30],Inf)==0);
assert(norm(u-[.001 .2;.002 .4;.003 .6],Inf)<eps);
assert(rejected(@() load_io_csv(path,{'absent'},'output',.01)));
assert(rejected(@() load_io_csv(path,{'flow','flow'},'output',.01)));
assert(rejected(@() load_io_csv(path,'output','output',.01)));
for step=[0 -1 Inf NaN]
 assert(rejected(@() load_io_csv(path,'valve','output',step)));
end
cases={...
 sprintf('u,u\n1,2\n3,4\n'),... % duplicate header
 sprintf('u,y\n1,2\n'),... % insufficient rows
 sprintf('u,y\n1,2\n3,\n'),... % missing selected observation
 sprintf('u,y\n1,2\n3,4,5\n'),... % wrong width
 sprintf('u,y\n1,2\n\n3,4\n'),... % blank row cannot be dropped
 sprintf('u,y\n1,2\n3,NaN\n'),...
 sprintf('u,y\n1,2\n3,1e999\n'),... % parsed infinity
 sprintf('u,y\n1,2\n3,4+2i\n'),... % complex field
 sprintf('u,y\n1,2\n3,"4"\n'),... % quotes unsupported
 sprintf('"u",y\n1,2\n3,4\n'),...
 sprintf('u,y,unused\n1,2,3\n4,5,missing\n'),... % no silent ignored data
 sprintf('u,\n1,2\n3,4\n'),...
 sprintf('u,y\n1,2\n# comment\n3,4\n')};
for k=1:numel(cases)
 write_fixture(path,cases{k});assert(rejected(@() load_io_csv(path,'u','y',.01)));
end
record=struct('passed',true,'aligned_rows',3,'malformed_fixtures_rejected',numel(cases),...
 'source','Temporary import-validation fixtures; not measured benchmark data');
fprintf('CSV ordering, timing, missing-data and %d malformed-record checks passed.\n',numel(cases));
end

function write_fixture(path,contents)
fid=fopen(path,'wt');assert(fid>=0);cleanup=onCleanup(@() fclose(fid));fprintf(fid,'%s',contents);
end
function yes=rejected(action)
yes=false;try,action();catch,yes=true;end
end
function remove_fixture(path)
if exist(path,'file'),delete(path);end
end
