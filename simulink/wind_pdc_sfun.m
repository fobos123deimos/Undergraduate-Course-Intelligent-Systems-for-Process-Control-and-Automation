function [sys,x0,str,ts]=wind_pdc_sfun(~,x,u,flag,points,initial_command,dt)
%WIND_PDC_SFUN Measured eight-state/wind feedback with torque/pitch slew limits.
% Discrete state is the previously applied command; no future wind is read.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=2;s.NumOutputs=2;
  s.NumInputs=9;s.DirFeedthrough=1;s.NumSampleTimes=1;
  sys=simsizes(s);x0=initial_command(:);ts=[dt 0];
 case {2,3},sys=wind_control('command',u(1:8),u(9),points,x,dt,true);
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
