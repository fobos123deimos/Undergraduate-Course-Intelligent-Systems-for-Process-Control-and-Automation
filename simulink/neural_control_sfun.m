function [sys,x0,str,ts]=neural_control_sfun(~,~,u,flag,model,dt)
%NEURAL_CONTROL_SFUN Bounded inversion of the separately trained RBF model.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=0;s.NumOutputs=1;
  s.NumInputs=2;s.DirFeedthrough=1;s.NumSampleTimes=1;sys=simsizes(s);ts=[dt 0];
 case 3,sys=neural_inverse_action(model,u(1),u(2));
 case {1,2,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
