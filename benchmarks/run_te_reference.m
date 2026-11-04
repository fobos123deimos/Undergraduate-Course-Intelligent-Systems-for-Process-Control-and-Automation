function run_te_reference(source_directory, output_csv)
% Run the retrieved 2015 TE mode-1 closed-loop model for 0.1 hours.
% This interface is supplied for MATLAB/Simulink; no local execution is claimed.
% Retains the official initial state and controller; suppresses plot callback.
source_directory = char(java.io.File(source_directory).getCanonicalPath());
output_csv = char(java.io.File(output_csv).getCanonicalPath());
assert(isfile(fullfile(source_directory,'temexd_mod.c')), 'Fetch te-revised first');
assert(~isfile(output_csv), 'Choose a new output file to avoid stale results');
original_directory = pwd;
cleanup = onCleanup(@() cd(original_directory));
cd(source_directory);
% Compile for this MATLAB/runtime instead of relying on an old prebuilt MEX.
mex('temexd_mod.c');
model = 'MultiLoop_mode1';
load_system(model);
close_model = onCleanup(@() close_system(model,0));
set_param(model,'StopFcn','');
% The official initialization callback defines the controller and save periods.
% Model To Workspace blocks export tout, simout, xmv, idv and OpCost.
simulation = sim(model,'StopTime','0.1','ReturnWorkspaceOutputs','on');
t = simulation.get('tout');
y = simulation.get('simout');
u = simulation.get('xmv');
assert(isnumeric(t) && isnumeric(y) && isnumeric(u), 'Inspect exported signal format for this runtime');
assert(size(y,2)==41 && size(u,2)==12, 'Unexpected TE output dimensions');
assert(numel(t)==size(y,1) && numel(t)==size(u,1), 'Unaligned TE output times');
assert(all(isfinite([t(:);y(:);u(:)])), 'Nonfinite TE output');
[folder,~,~]=fileparts(output_csv);
if ~isfolder(folder), mkdir(folder); end
names=[{'time_h'},arrayfun(@(k)sprintf('xmeas_%02d',k),1:41,'UniformOutput',false),...
    arrayfun(@(k)sprintf('xmv_%02d',k),1:12,'UniformOutput',false)];
writetable(array2table([t(:),y,u],'VariableNames',names),output_csv);
fprintf('Exported %d measured-output rows to %s\n',numel(t),output_csv);
end
