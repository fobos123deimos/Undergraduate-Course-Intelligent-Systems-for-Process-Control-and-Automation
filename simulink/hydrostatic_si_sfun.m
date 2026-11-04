function hydrostatic_si_sfun(block)
%HYDROSTATIC_SI_SFUN Four continuous states, with explicit SI parameters.
% Input vector: [requested normalized pump/motor angles, pump rad/s, wheel Nm].
block.NumDialogPrms=2;block.DialogPrmsTunable={'Nontunable','Nontunable'};
block.NumInputPorts=1;block.NumOutputPorts=1;block.SetPreCompPortInfoToDefaults;
block.InputPort(1).Dimensions=4;block.InputPort(1).DirectFeedthrough=false;
block.OutputPort(1).Dimensions=4;block.NumContStates=4;
block.SampleTimes=[0 0];block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('CheckParameters',@check_parameters);
block.RegBlockMethod('InitializeConditions',@initialize);
block.RegBlockMethod('Outputs',@outputs);block.RegBlockMethod('Derivatives',@derivatives);
check_parameters(block);
end

function check_parameters(block)
x=block.DialogPrm(1).Data;
hydrostatic_si(x,x(1:2),0,0,block.DialogPrm(2).Data);
end

function initialize(block)
block.ContStates.Data=block.DialogPrm(1).Data(:);
end

function outputs(block)
block.OutputPort(1).Data=block.ContStates.Data;
end

function derivatives(block)
u=block.InputPort(1).Data;
block.Derivatives.Data=hydrostatic_si(block.ContStates.Data,u(1:2),u(3),u(4),block.DialogPrm(2).Data);
end
