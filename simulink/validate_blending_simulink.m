function report = validate_blending_simulink(output_dir)
%VALIDATE_BLENDING_SIMULINK Execute fresh diagrams in MATLAB with Simulink.
% This script is an execution recipe, not evidence that Simulink was run.
% All physical parameters are declared in each model workspace.
% No Control System Toolbox is needed.
% A new temporary folder is kept for inspection when output_dir is omitted.
if nargin<1,output_dir=tempname;end
base=fileparts(mfilename('fullpath'));addpath(base);addpath(fullfile(base,'..','matlab'));
paths=build_blending_tank(output_dir,false);p=bt_parameters();
report=struct('runtime','MATLAB with Simulink','paths',{paths});

name='bt_nonlinear_corrected';load_system(paths{1});
cleanup=onCleanup(@() close_system(name,0));
assert(strcmp(get_param([name '/Nonlinear'],'FunctionName'),'bt_sfun'));
output=sim(name);data=output.get('state_history');
t=data.time(:);x=data.signals.values;
% Independent total/solute-balance closed form for startup at constant volume.
expected=[.5*(1-exp(-.35*t)),2*ones(size(t))];
report.startup_max_error=max(abs(x(:)-expected(:)));
assert(report.startup_max_error<2e-7);

% A distinct filling case deliberately has no fixed-volume equilibrium.
ws=get_param(name,'ModelWorkspace');filling=p.ubar;filling(5)=650;
assignin(ws,'physical_input',filling);
output=sim(name);data=output.get('state_history');
t=data.time(:);x=data.signals.values;volume=2+.05*t;
expected=[.5*(1-(2./volume).^14),volume];
report.filling_max_error=max(abs(x(:)-expected(:)));
assert(report.filling_max_error<2e-7);

% Physical-domain validation must fail instead of dividing by an empty volume.
assignin(ws,'xinit',[.5;0]);failed=false;rejected=false;diagnostic='';
try
 sim(name);
catch err
 rejected=true;failed=volume_guard_exception(err);
 diagnostic=getReport(err,'extended','hyperlinks','off');
end
assert(rejected,'An invalid initial volume must be rejected.');
assert(failed,sprintf('Invalid volume raised an unexpected exception:\n%s',diagnostic));
report.invalid_initial_volume_rejected=failed;
report.invalid_initial_volume_diagnostic=diagnostic;
fprintf('Invalid initial volume rejected by the physical-domain guard.\n%s\n',diagnostic);
% Restore the saved startup settings before exporting the model view.
assignin(ws,'xinit',[0;2]);assignin(ws,'physical_input',p.ubar);
export_model_diagram(name,fullfile(output_dir,[name '.png']));
clear cleanup;

name='bt_comparison_corrected';load_system(paths{2});
cleanup=onCleanup(@() close_system(name,0));
output=sim(name);nonlinear=output.get('nonlinear_states');
linear=output.get('linear_states');transfer=output.get('transfer_states');
assert(isequal(nonlinear.time,linear.time)&&isequal(linear.time,transfer.time));
t=nonlinear.time(:);xn=nonlinear.signals.values;
xl=linear.signals.values;xt=transfer.signals.values;
assert(max(abs(xl(1,:)-p.xbar'))<1e-12&&max(abs(xt(1,:)-p.xbar'))<1e-12);
report.state_space_transfer_max_error=max(abs(xl(:)-xt(:)));
assert(report.state_space_transfer_max_error<2e-7);

elapsed=max(t-5,0);volume=2+.01*elapsed;mixture=354/710;
expected=[mixture+(.5-mixture)*(2./volume).^71,volume];
report.perturbed_nonlinear_max_error=max(abs(xn(:)-expected(:)));
assert(report.perturbed_nonlinear_max_error<2e-7);
% Analytic linear response confirms input ordering and the negative G11 sign.
expected_linear=[.5-(.00005*10/.35)*(1-exp(-.35*elapsed)),volume];
report.linear_formula_max_error=max(abs(xl(:)-expected_linear(:)));
assert(report.linear_formula_max_error<2e-7);
assert(xl(end,1)<.5&&xl(end,2)>2);
report.local_approximation_max_error=max(abs(xn(:)-xl(:)));
assert(report.local_approximation_max_error<1e-3);
export_model_diagram(name,fullfile(output_dir,[name '.png']));
clear cleanup;
report.passed=true;
fprintf('Corrected Simulink startup, filling, linear/transfer and domain checks passed.\n');
end

function matches=volume_guard_exception(err)
% Simulink wraps Level-2 S-function errors in MSLException causes. Check the
% actual guard diagnostic recursively; an unrelated simulation error fails.
matches=any(strcmp(err.identifier,{'bt_sfun:InitialState','bt_sfun:MinimumVolume'}))||...
 contains(err.message,'Initial state must be [X;V]')||...
 contains(err.message,'Volume reached min_volume');
for j=1:numel(err.cause)
 matches=matches||volume_guard_exception(err.cause{j});
end
end
