function [sys,x0,str,ts]=hmm_pi_sfun(~,x,u,flag,p)
%HMM_PI_SFUN Discrete online diagnosis/control without true state or lookahead.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=5;s.NumOutputs=6;
  s.NumInputs=2;s.DirFeedthrough=1;s.NumSampleTimes=1;
  sys=simsizes(s);x0=[.35;0;p.initial(:)];ts=[p.dt 0];
 case 2,[~,sys]=hmm_pi_step(x,u,p);
 case 3,sys=hmm_pi_step(x,u,p);
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
