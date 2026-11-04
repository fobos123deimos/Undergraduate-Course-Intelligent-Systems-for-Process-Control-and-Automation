function checks = validate_markov()
%VALIDATE_MARKOV Independent finite-state and HMM mathematical checks.
%   Uses exhaustive path enumeration as an oracle, not a second recursion.
checks = struct();
P=[.9 .1;.2 .8]; pi=[.7 .3];
assert(norm(markov_models('propagate',P,pi,0)-pi,Inf)<1e-13);
assert(norm(markov_models('propagate',P,pi,2)-[.683 .317],Inf)<1e-13);
stationary=markov_models('stationary',P);
assert(norm(stationary-[2/3 1/3],Inf)<1e-12);
assert(norm(stationary*P-stationary,Inf)<1e-12);
checks.chain= true;

% Stop at the first target visit, even when the original target has exits.
A=[.8 .2 0;0 .75 .25;1 0 0];
[m,p]=markov_models('hitting',A,3);
assert(norm(m-[9;4;0],Inf)<1e-11 && norm(p-ones(3,1),Inf)<1e-12);
[m,p]=markov_models('hitting',[0 .5 .5;0 1 0;0 0 1],2);
assert(norm(p-[.5;1;0],Inf)<1e-12 && isinf(m(1)) && m(2)==0 && isinf(m(3)));
[m,p]=markov_models('hitting',[0 1 0;0 0 1;0 0 1],2);
assert(norm(p-[1;1;0],Inf)<1e-12 && m(1)==1 && m(2)==0 && isinf(m(3)));
checks.hitting = true;

% Same fixed fixture is independently enumerated in the Python tests.
P=[.7 .3;.2 .8]; B=[.6 .3 .1;.1 .3 .6]; pi=[.6 .4]; o=[1;2;3;2];
oracle=enumerate_paths(P,B,pi,o);
f=markov_models('filter',P,B,pi,o);
s=markov_models('smooth',P,B,pi,o);
v=markov_models('viterbi',P,B,pi,o);
assert(abs(exp(f.log_likelihood)-oracle.likelihood)<1e-14);
assert(abs(oracle.likelihood-.01215)<1e-14);
fixed_filter=[.9 .1;.65 .35;7/45 38/45;5/18 13/18];
fixed_smoother=[13/15 2/15;13/27 14/27;7/45 38/45;5/18 13/18];
assert(norm(f.filtered-fixed_filter,Inf)<1e-12);
assert(norm(s.smoothed-fixed_smoother,Inf)<1e-12);
assert(norm(s.smoothed-oracle.smoothed,Inf)<1e-12);
assert(norm(s.transition_expectations-oracle.transitions,Inf)<1e-12);
assert(norm(sum(s.smoothed,2)-1,Inf)<1e-12);
assert(isequal(v.path,oracle.path));
assert(isequal(v.path,[1;2;2;2]));
assert(abs(exp(v.log_probability)-oracle.path_probability)<1e-14);
for t=1:numel(o)
 prefix=enumerate_paths(P,B,pi,o(1:t));
 assert(norm(f.filtered(t,:)-prefix.smoothed(end,:),Inf)<1e-12);
end
one=markov_models('smooth',P,B,pi,1);
assert(norm(one.smoothed-[.9 .1],Inf)<1e-12);
assert(all(one.transition_expectations(:)==0));
checks.enumerated_hmm = true;

% Scaling remains finite when an unscaled sequence likelihood underflows.
long_o=repmat([1;2;3],1000,1);
long_f=markov_models('filter',P,B,pi,long_o);
long_s=markov_models('smooth',P,B,pi,long_o);
long_v=markov_models('viterbi',P,B,pi,long_o);
assert(isfinite(long_f.log_likelihood) && exp(long_f.log_likelihood)==0);
assert(all(isfinite(long_s.smoothed(:))) && norm(sum(long_s.smoothed,2)-1,Inf)<1e-12);
assert(isfinite(long_v.log_probability) && numel(long_v.path)==numel(long_o));
checks.scaling = true;

% Counts never join the end of one independent experiment to the next.
fit=markov_models('supervised',{[1;1],[2;2]},{[1;2],[2;1]},2,2,1);
default_fit=markov_models('supervised',{[1;1],[2;2]},{[1;2],[2;1]},2,2);
assert(isequal(fit.transition,default_fit.transition));
assert(isequal(fit.transition_counts,[2 1;1 2]));
assert(isequal(fit.emission_counts,[2 2;2 2]));
assert(norm(fit.transition-[2/3 1/3;1/3 2/3],Inf)<1e-12);
assert(norm(fit.initial-[.5 .5],Inf)<1e-12);
single=markov_models('supervised',{1,2},{1,2},2,2,1);
assert(isequal(single.transition_counts,ones(2)));
checks.sequence_boundaries = true;

% EM optimizes the sum of independent training likelihoods without labels.
seqs={[1;1;2;3;3;3;2;1],[3;3;2;2;1;1],[1;3;2;3]};
em=markov_models('baum_welch',seqs,P,B,pi,30,1e-10);
assert(all(diff(em.log_likelihood_history)>=0));
assert(em.log_likelihood_history(end)>em.log_likelihood_history(1)+1e-5);
assert(norm(sum(em.transition,2)-1,Inf)<1e-12 && norm(sum(em.emission,2)-1,Inf)<1e-12);
assert(abs(sum(em.initial)-1)<1e-12);
% A singleton sequence has no transition count; retain the previous rows.
em_one=markov_models('baum_welch',{1,3},P,B,pi,2,0);
assert(norm(em_one.transition-P,Inf)<1e-12);
checks.em = true;

% Reject invalid probabilities, zero-likelihood data and ambiguous stationarity.
must_fail(@() markov_models('propagate',[.8 .1;.2 .8],pi,2));
must_fail(@() markov_models('propagate',P,[1.1 -.1],2));
must_fail(@() markov_models('propagate',P,pi,1.5));
must_fail(@() markov_models('stationary',eye(2)));
must_fail(@() markov_models('filter',P,B,pi,0));
must_fail(@() markov_models('filter',P,B,pi,[]));
must_fail(@() markov_models('filter',P,[1 0;1 0],pi,2));
must_fail(@() markov_models('viterbi',P,[1 0;1 0],pi,2));
must_fail(@() markov_models('supervised',{[1;1]},{[1;2]},2,2,0));
must_fail(@() markov_models('supervised',{[1;2]},{1},2,2,1));
must_fail(@() markov_models('simulate_chain',P,pi,2,-1));
must_fail(@() markov_models('simulate_chain',P,pi,2,1.5));
must_fail(@() markov_models('supervised',{[1;2]},{[1;2]},2,2,1i));
checks.input_validation = true;
fprintf('Seven Markov/HMM mathematical checks passed.\n');
end

function q=enumerate_paths(P,B,pi,o)
% Small exhaustive oracle: enumerate every latent path and its joint mass.
n=size(P,1);T=numel(o);mass=0;marginals=zeros(T,n);counts=zeros(n);
best=-1;best_path=zeros(T,1);
for code=0:n^T-1
 path=zeros(T,1);value=code;
 for t=T:-1:1,path(t)=mod(value,n)+1;value=floor(value/n);end
 joint=pi(path(1))*B(path(1),o(1));
 for t=2:T,joint=joint*P(path(t-1),path(t))*B(path(t),o(t));end
 mass=mass+joint;
 for t=1:T
  marginals(t,path(t))=marginals(t,path(t))+joint;
  if t<T,counts(path(t),path(t+1))=counts(path(t),path(t+1))+joint;end
 end
 if joint>best,best=joint;best_path=path;end
end
q=struct('likelihood',mass,'smoothed',marginals/mass,'transitions',counts/mass,...
 'path',best_path,'path_probability',best);
end

function must_fail(fun)
failed=false;try,fun();catch,failed=true;end
assert(failed,'Expected invalid input to raise an error.');
end
