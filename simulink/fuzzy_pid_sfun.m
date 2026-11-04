function [sys,x0,str,ts]=fuzzy_pid_sfun(~,x,u,flag,p)
%FUZZY_PID_SFUN Discrete fuzzy-scheduled PID; output=[actuator,Kp,Ki,Kd,Dterm].
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=3;s.NumOutputs=5;
  s.NumInputs=2;s.DirFeedthrough=1;s.NumSampleTimes=1;
  sys=simsizes(s);x0=[.35;.35;0];ts=[p.dt 0];
 case 2,[~,sys]=fuzzy_pid_step(x,u,p);
 case 3
  [actuator,~,details]=fuzzy_pid_step(x,u,p);
  sys=[actuator;details.gains(:);details.derivative_action];
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
