function varargout = markov_models(action, varargin)
%MARKOV_MODELS Finite-state Markov chains and categorical hidden Markov models.
%   Matrices are row-stochastic. States/symbols are one-based in MATLAB/Octave.
%   HMM convention: z(1)~pi, o(1)~B(z(1),:), then z(t+1)~P(z(t),:).
%   filter/smooth use scaling; Viterbi uses log probabilities. Impossible
%   sequences raise errors rather than returning invented posterior values.
switch action
 case 'propagate'
  P=stochastic(varargin{1},'P'); n=size(P,1); square(P);
  pi=distribution(varargin{2},n,'pi'); steps=varargin{3};
  scalar_integer(steps,0,'steps');varargout{1}=pi*(P^steps);
 case 'stationary'
  P=stochastic(varargin{1},'P');square(P);n=size(P,1);
  if rank(P'-eye(n))~=n-1,error('Stationary distribution is not unique.');end
  pi=[P'-eye(n);ones(1,n)]\[zeros(n,1);1];
  if min(pi)<-1e-10,error('Failed to obtain nonnegative stationary distribution.');end
  pi=max(pi,0);varargout{1}=(pi/sum(pi))';
 case 'hitting'
  P=stochastic(varargin{1},'P');square(P);n=size(P,1);
  targets=indices(varargin{2},n,'targets');targets=unique(targets);
  reachable=false(n,1);reachable(targets)=true;
  for k=1:n,reachable=reachable|any(P(:,reachable)>0,2);end
  unknown=find(reachable);unknown=setdiff(unknown,targets);
  probability=zeros(n,1);probability(targets)=1;
  if ~isempty(unknown)
   probability(unknown)=(eye(numel(unknown))-P(unknown,unknown))\sum(P(unknown,targets),2);
  end
  % Any path to a closed non-target region makes unconditional mean infinite.
  bad=~reachable;
  for k=1:n,bad=bad|any(P(:,bad)>0,2);bad(targets)=false;end
  finite=setdiff(find(~bad),targets);expected=Inf(n,1);expected(targets)=0;
  if ~isempty(finite)
   expected(finite)=(eye(numel(finite))-P(finite,finite))\ones(numel(finite),1);
  end
  varargout{1}=expected;if nargout>1,varargout{2}=probability;end
 case 'simulate_chain'
  P=stochastic(varargin{1},'P');square(P);pi=distribution(varargin{2},size(P,1),'pi');
  N=varargin{3};scalar_integer(N,1,'length');
  if numel(varargin)>3,set_seed(varargin{4});end
  states=zeros(N,1);states(1)=draw(pi);
  for t=2:N,states(t)=draw(P(states(t-1),:));end
  varargout{1}=states;
 case 'simulate'
  [P,B,pi]=model(varargin{1},varargin{2},varargin{3});N=varargin{4};scalar_integer(N,1,'length');
  if numel(varargin)>4,set_seed(varargin{5});end
  states=zeros(N,1);observations=states;states(1)=draw(pi);observations(1)=draw(B(states(1),:));
  for t=2:N,states(t)=draw(P(states(t-1),:));observations(t)=draw(B(states(t),:));end
  varargout{1}=struct('states',states,'observations',observations);
 case {'filter','forward'}
  [P,B,pi]=model(varargin{1},varargin{2},varargin{3});o=indices(varargin{4},size(B,2),'observations');
  varargout{1}=forward(P,B,pi,o);
 case 'smooth'
  [P,B,pi]=model(varargin{1},varargin{2},varargin{3});o=indices(varargin{4},size(B,2),'observations');
  varargout{1}=posterior(P,B,pi,o);
 case 'viterbi'
  [P,B,pi]=model(varargin{1},varargin{2},varargin{3});o=indices(varargin{4},size(B,2),'observations');
  n=size(P,1);T=numel(o);delta=zeros(T,n);psi=zeros(T,n);
  delta(1,:)=log(pi)+log(B(:,o(1)))';
  for t=2:T
   for j=1:n
    [best,psi(t,j)]=max(delta(t-1,:)+log(P(:,j))');delta(t,j)=best+log(B(j,o(t)));
   end
  end
  [value,last]=max(delta(T,:));
  if ~isfinite(value),error('Observation sequence has zero probability.');end
  path=zeros(T,1);path(T)=last;
  for t=T-1:-1:1,path(t)=psi(t+1,path(t+1));end
  varargout{1}=struct('path',path,'log_probability',value);
 case 'supervised'
  zs=sequence_list(varargin{1},'state sequences');os=sequence_list(varargin{2},'observation sequences');
  n=varargin{3};m=varargin{4};scalar_integer(n,1,'states');scalar_integer(m,1,'symbols');
  pseudocount=1;if numel(varargin)>4,pseudocount=varargin{5};end
  if ~isnumeric(pseudocount)||~isreal(pseudocount)||~isscalar(pseudocount)||~isfinite(pseudocount)||pseudocount<0,error('Invalid pseudocount.');end
  if numel(zs)~=numel(os),error('Paired sequence lists must have equal length.');end
  cp=pseudocount*ones(n);cb=pseudocount*ones(n,m);ci=pseudocount*ones(1,n);
  for k=1:numel(zs)
   z=indices(zs{k},n,'states');o=indices(os{k},m,'observations');
   if numel(z)~=numel(o),error('State and observation sequences must align.');end
   ci(z(1))=ci(z(1))+1;
   for t=1:numel(z)
    cb(z(t),o(t))=cb(z(t),o(t))+1;
    if t<numel(z),cp(z(t),z(t+1))=cp(z(t),z(t+1))+1;end
   end
  end
  if any(sum(cp,2)==0)||any(sum(cb,2)==0),error('Unobserved rows require explicit positive pseudocount.');end
  varargout{1}=struct('transition',cp./sum(cp,2),'emission',cb./sum(cb,2),...
                     'initial',ci/sum(ci),'transition_counts',cp,'emission_counts',cb);
 case 'baum_welch'
  os=sequence_list(varargin{1},'observation sequences');
  [P,B,pi]=model(varargin{2},varargin{3},varargin{4});
  maxiter=40;tol=1e-7;
  if numel(varargin)>4,maxiter=varargin{5};end
  if numel(varargin)>5,tol=varargin{6};end
  scalar_integer(maxiter,1,'iterations');
  if ~isnumeric(tol)||~isreal(tol)||~isscalar(tol)||~isfinite(tol)||tol<0,error('Tolerance must be finite and nonnegative.');end
  for k=1:numel(os),os{k}=indices(os{k},size(B,2),'observations');end
  history=total_loglik(P,B,pi,os);n=size(P,1);m=size(B,2);
  for iter=1:maxiter
   cp=zeros(n);cb=zeros(n,m);ci=zeros(1,n);
   for k=1:numel(os)
    o=os{k};q=posterior(P,B,pi,o);ci=ci+q.smoothed(1,:);cp=cp+q.transition_expectations;
    for symbol=1:m,cb(:,symbol)=cb(:,symbol)+sum(q.smoothed(o==symbol,:),1)';end
   end
   newP=P;newB=B;
   for i=1:n
    if sum(cp(i,:))>0,newP(i,:)=cp(i,:)/sum(cp(i,:));end
    if sum(cb(i,:))>0,newB(i,:)=cb(i,:)/sum(cb(i,:));end
   end
   newpi=ci/sum(ci);ll=total_loglik(newP,newB,newpi,os);
   if ll<history(end)-1e-7*max(1,abs(history(end))),error('EM likelihood decreased unexpectedly.');end
   previous=history(end);improvement=ll-previous;
   % Preserve the preceding iterate if roundoff produces a tiny decrease.
   if improvement<0,break;end
   P=newP;B=newB;pi=newpi;history(end+1,1)=ll;
   if improvement<=tol*max(1,abs(previous)),break;end
  end
  varargout{1}=struct('transition',P,'emission',B,'initial',pi,'log_likelihood_history',history(:));
 otherwise,error('Unknown Markov operation: %s',action);
end
end

function q=forward(P,B,pi,o)
T=numel(o);n=size(P,1);alpha=zeros(T,n);scales=zeros(T,1);prior=pi;
for t=1:T
 value=prior.*B(:,o(t))';scales(t)=sum(value);
 if scales(t)<=0 || ~isfinite(scales(t)),error('Observation sequence has zero probability.');end
 alpha(t,:)=value/scales(t);prior=alpha(t,:)*P;
end
q=struct('filtered',alpha,'scales',scales,'log_likelihood',sum(log(scales)));
end

function q=posterior(P,B,pi,o)
q=forward(P,B,pi,o);T=numel(o);n=size(P,1);beta=ones(T,n);
for t=T-1:-1:1,beta(t,:)=(P*(B(:,o(t+1)).*beta(t+1,:)'))'/q.scales(t+1);end
gamma=q.filtered.*beta;gamma=gamma./sum(gamma,2);xi=zeros(n);
for t=1:T-1
 pair=(q.filtered(t,:)'*(B(:,o(t+1)).*beta(t+1,:)')').*P;
 xi=xi+pair/sum(pair(:));
end
q.smoothed=gamma;q.transition_expectations=xi;
end

function ll=total_loglik(P,B,pi,sequences)
ll=0;for k=1:numel(sequences),q=forward(P,B,pi,sequences{k});ll=ll+q.log_likelihood;end
end

function [P,B,pi]=model(P,B,pi)
P=stochastic(P,'P');square(P);B=stochastic(B,'B');
if size(B,1)~=size(P,1),error('Emission and transition state counts differ.');end
pi=distribution(pi,size(P,1),'pi');
end

function x=stochastic(x,name)
if ~isnumeric(x)||~isreal(x)||isempty(x)||ndims(x)~=2||any(~isfinite(x(:)))||any(x(:)<0)||any(x(:)>1)||any(abs(sum(x,2)-1)>1e-10)
 error('%s must be a finite nonnegative row-stochastic matrix.',name);
end
x=double(x);
end

function square(P)
if size(P,1)~=size(P,2),error('Transition matrix must be square.');end
end

function pi=distribution(pi,n,name)
if ~isnumeric(pi)||~isreal(pi)||~isvector(pi)||numel(pi)~=n,error('%s has wrong shape.',name);end
pi=stochastic(double(pi(:)'),name);
end

function x=indices(x,n,name)
if ~isnumeric(x)||~isreal(x)||~isvector(x)||isempty(x)||any(~isfinite(x(:)))||any(x(:)~=fix(x(:)))||any(x(:)<1)||any(x(:)>n)
 error('%s must contain one-based integer indices in range.',name);
end
x=x(:);
end

function scalar_integer(x,lower,name)
if ~isnumeric(x)||~isreal(x)||~isscalar(x)||~isfinite(x)||x~=fix(x)||x<lower,error('Invalid integer %s.',name);end
end

function list=sequence_list(list,name)
if ~iscell(list)||isempty(list),error('%s must be a nonempty cell array of independent sequences.',name);end
end

function value=draw(probability)
value=find(rand<cumsum(probability),1);if isempty(value),value=numel(probability);end
end

function set_seed(seed)
scalar_integer(seed,0,'seed');
if seed>2^32-1,error('Seed must fit an unsigned 32-bit integer.');end
rng(double(seed),'twister');
end
