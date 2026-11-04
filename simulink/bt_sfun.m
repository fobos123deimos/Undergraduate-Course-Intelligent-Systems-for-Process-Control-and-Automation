function bt_sfun(block)
%BT_SFUN Fresh Level-2 continuous adapter for the corrected physical tank.
% Dialog parameters: initial state [X;V], parameter struct from bt_parameters.
% Input vector: [w1;w2;x1;x2;wout]. Outputs are the physical states [X;V].
% Time is min, flows kg/min, density kg/m^3 and volume m^3.
% The adapter has no dependency on any historical model or S-function.
% Interface reference:
% https://www.mathworks.com/help/simulink/sfg/writing-level-2-matlab-s-functions.html
setup(block);
end

function setup(block)
block.NumDialogPrms=2;
block.DialogPrmsTunable={'Nontunable','Nontunable'};
block.NumInputPorts=1;block.NumOutputPorts=1;
block.SetPreCompPortInfoToDefaults;
block.InputPort(1).Dimensions=5;
block.InputPort(1).DatatypeID=0;
block.InputPort(1).Complexity='Real';
block.InputPort(1).DirectFeedthrough=false;
block.OutputPort(1).Dimensions=2;
block.OutputPort(1).DatatypeID=0;
block.OutputPort(1).Complexity='Real';
block.NumContStates=2;
block.SampleTimes=[0 0];
block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('CheckParameters',@check_parameters);
block.RegBlockMethod('InitializeConditions',@initialize_conditions);
block.RegBlockMethod('Outputs',@outputs);
block.RegBlockMethod('Derivatives',@derivatives);
check_parameters(block);
end

function check_parameters(block)
xinit=block.DialogPrm(1).Data;p=block.DialogPrm(2).Data;
if ~isstruct(p)||~isfield(p,'ubar')||~isfield(p,'min_volume')
 error('bt_sfun:Parameters','Use the parameter structure returned by bt_parameters.');
end
if ~isscalar(p.min_volume)||~isreal(p.min_volume)||~isfinite(p.min_volume)||p.min_volume<=0
 error('bt_sfun:MinimumVolume','min_volume must be a finite positive scalar.');
end
if numel(xinit)~=2||~isreal(xinit)||any(~isfinite(xinit(:)))||xinit(2)<=p.min_volume
 error('bt_sfun:InitialState','Initial state must be [X;V], with V above min_volume.');
end
% This also checks composition, density, and the canonical input units/domain.
bt_rhs(0,xinit(:),p.ubar,p);
end

function initialize_conditions(block)
block.ContStates.Data=block.DialogPrm(1).Data(:);
end

function outputs(block)
% No input is read here: state output has no direct feedthrough.
block.OutputPort(1).Data=block.ContStates.Data;
end

function derivatives(block)
x=block.ContStates.Data;p=block.DialogPrm(2).Data;
% Halt before the undefined empty-tank balance is evaluated. This is a domain
% guard, not a saturation or a continuation of the solution after emptying.
if x(2)<=p.min_volume
 error('bt_sfun:MinimumVolume',...
  'Volume reached min_volume. Shorten the simulation or change the outlet flow.');
end
block.Derivatives.Data=bt_rhs(block.CurrentTime,x,block.InputPort(1).Data,p);
end
