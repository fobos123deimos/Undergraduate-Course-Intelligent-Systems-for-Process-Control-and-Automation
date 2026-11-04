function pneumatic_physical_sfun(block)
%PNEUMATIC_PHYSICAL_SFUN Continuous six-state SI mass/energy adapter.
block.NumDialogPrms=2;block.DialogPrmsTunable={'Nontunable','Nontunable'};
block.NumInputPorts=1;block.NumOutputPorts=2;block.SetPreCompPortInfoToDefaults;
block.InputPort(1).Dimensions=1;block.InputPort(1).DirectFeedthrough=false;
block.InputPort(1).DatatypeID=0;block.InputPort(1).Complexity='Real';
block.OutputPort(1).Dimensions=6;block.OutputPort(2).Dimensions=2;
for j=1:2,block.OutputPort(j).DatatypeID=0;block.OutputPort(j).Complexity='Real';end
block.NumContStates=6;block.SampleTimes=[0 0];block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('CheckParameters',@check_parameters);
block.RegBlockMethod('InitializeConditions',@initialize);
block.RegBlockMethod('Outputs',@outputs);block.RegBlockMethod('Derivatives',@derivatives);
check_parameters(block);
end

function check_parameters(block)
pneumatic_physical('rhs',block.DialogPrm(1).Data,0,block.DialogPrm(2).Data);
end

function initialize(block)
block.ContStates.Data=block.DialogPrm(1).Data(:);
end

function outputs(block)
x=block.ContStates.Data;block.OutputPort(1).Data=x;
block.OutputPort(2).Data=pneumatic_physical('observe',x,block.DialogPrm(2).Data);
end

function derivatives(block)
block.Derivatives.Data=pneumatic_physical('rhs',block.ContStates.Data,block.InputPort(1).Data,block.DialogPrm(2).Data);
end
