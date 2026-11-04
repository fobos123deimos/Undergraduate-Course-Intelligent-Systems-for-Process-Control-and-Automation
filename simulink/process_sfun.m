function [sys,x0,str,ts] = process_sfun(t,x,u,flag,kind,xinit,parameters)
%PROCESS_SFUN Level-1 continuous adapter for the implemented process equations.
% Used by build_models; no clipping of physical states is hidden here.
x0=[];str=[];ts=[];
switch flag
 case 0
  nx=numel(xinit);sizes=simsizes;sizes.NumContStates=nx;sizes.NumDiscStates=0;
  sizes.NumOutputs=nx;sizes.NumInputs=parameters.ninputs;
  sizes.DirFeedthrough=0;sizes.NumSampleTimes=1;
  sys=simsizes(sizes);x0=xinit(:);ts=[0 0];
 case 1
  if strcmp(kind,'blending')
   % Corrected tank input order: [w1,w2,x1,x2,wout].
   p=bt_parameters();p.rho=parameters.rho;
   sys=bt_rhs(t,x,u,p);
  else
   sys=paper_models(kind,x,u,parameters);
  end
 case 3,sys=x;
 case {2,4,9},sys=[];
 otherwise,error('Unsupported S-function flag %d.',flag);
end
end
