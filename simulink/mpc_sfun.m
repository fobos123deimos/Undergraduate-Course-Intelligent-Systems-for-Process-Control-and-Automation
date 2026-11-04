function [sys,x0,str,ts] = mpc_sfun(~,x,u,flag)
%MPC_SFUN Two-output constrained discrete controller, Ts=.2 min.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=2;s.NumOutputs=2;s.NumInputs=4;
  s.DirFeedthrough=1;s.NumSampleTimes=1;sys=simsizes(s);x0=[0;0];ts=[.2 0];
 case {2,3}
  sys=mpc_control(diag([.96 .94]),[.04 .012;.01 .05],u(1:2),u(3:4),12,4,.15,x);
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
