function [sys,x0,str,ts]=paper_discrete_sfun(~,x,u,flag,kind,initial,dt,ninputs)
%PAPER_DISCRETE_SFUN Exact recurrence adapter; output precedes state update.
% SISO stores [current output; previous output]; MIMO/sample bioreactor store
% their two current outputs. The complete state is logged for verification.
x0=[];str=[];ts=[];
switch flag
 case 0
  s=simsizes;s.NumContStates=0;s.NumDiscStates=2;s.NumOutputs=2;
  s.NumInputs=ninputs;s.DirFeedthrough=0;s.NumSampleTimes=1;
  sys=simsizes(s);x0=initial(:);ts=[dt 0];
 case 2
  next=paper_models(kind,x,u);
  if strcmp(kind,'siso'),sys=[next;x(1)];else,sys=next;end
 case 3,sys=x;
 case {1,4,9},sys=[];
 otherwise,error('Unsupported S-function flag.');
end
end
