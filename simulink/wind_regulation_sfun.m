function [sys,x0,str,ts]=wind_regulation_sfun(~,x,u,flag,initial,dt)
%WIND_REGULATION_SFUN Held-input RK4 integration of the eight-state wind model.
% Inputs=[generator torque; pitch demand; wind speed]. Rotor-map limits apply.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=8;s.NumOutputs=8;
  s.NumInputs=3;s.DirFeedthrough=0;s.NumSampleTimes=1;
  sys=simsizes(s);x0=initial(:);ts=[dt 0];
 case 2
  f=@(z)wind_control('rhs',z,u(1:2),u(3));
  a=f(x);b=f(x+dt*a/2);c=f(x+dt*b/2);d=f(x+dt*c);
  sys=x+dt*(a+2*b+2*c+d)/6;
 case 3,sys=x;
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
