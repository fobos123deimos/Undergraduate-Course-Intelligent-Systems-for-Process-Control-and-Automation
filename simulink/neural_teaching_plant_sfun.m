function [sys,x0,str,ts]=neural_teaching_plant_sfun(~,x,u,flag,dt)
%NEURAL_TEACHING_PLANT_SFUN Unit06 nonlinear sampled tank extension.
% The .015*sin(3*x)*u term is an explicit synthetic teaching nonlinearity.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=1;s.NumOutputs=1;
  s.NumInputs=1;s.DirFeedthrough=0;s.NumSampleTimes=1;sys=simsizes(s);x0=0;ts=[dt 0];
 case 2,a=exp(-dt/10);sys=a*x+(1-a)*u+.015*sin(3*x)*u;
 case 3,sys=x;
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
