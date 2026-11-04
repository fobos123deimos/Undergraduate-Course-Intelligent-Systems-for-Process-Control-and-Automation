function [sys,x0,str,ts]=hmm_filter_sfun(~,x,u,flag,p)
%HMM_FILTER_SFUN Discrete pre-observation prior -> posterior -> next prior.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=3;s.NumOutputs=3;
  s.NumInputs=1;s.DirFeedthrough=1;s.NumSampleTimes=1;
  sys=simsizes(s);x0=p.initial(:);ts=[p.dt 0];
 case 2
  [~,next]=hmm_filter_step(p.transition,p.emission,x(:)',u);
  sys=next(:);
 case 3
  posterior=hmm_filter_step(p.transition,p.emission,x(:)',u);
  sys=posterior(:);
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
