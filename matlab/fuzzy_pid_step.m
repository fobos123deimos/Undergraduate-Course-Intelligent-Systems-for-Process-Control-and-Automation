function [u,next_state,details]=fuzzy_pid_step(state,input,p)
%FUZZY_PID_STEP Scheduled PID with filtered derivative and applied-input tracking.
% state=[integral command; previous measurement; filtered derivative].
% input=[reference; measurement]. Same policy as Unit05's fuzzy PID.
state=state(:);input=input(:);
assert(numel(state)==3&&numel(input)==2&&all(isfinite([state;input])));
assert(p.dt>0&&p.filter_time>0);
error_value=input(1)-input(2);normalized=min(1,max(-1,error_value/.3));
membership=[max(0,-normalized) max(0,1-abs(normalized)) max(0,normalized)];
severity=abs(membership*[-1;0;1]/sum(membership));
gains=[1.4+1.2*severity,.14+.08*severity,.1*severity];
derivative=state(3)+p.dt/(p.filter_time+p.dt)*((input(2)-state(2))/p.dt-state(3));
raw=gains(1)*error_value+state(1)-gains(3)*derivative;u=min(1,max(0,raw));
integral=state(1)+p.dt*(gains(2)*error_value+.6*(u-raw));
next_state=[integral;input(2);derivative];
details=struct('gains',gains,'derivative_action',-gains(3)*derivative);
end
