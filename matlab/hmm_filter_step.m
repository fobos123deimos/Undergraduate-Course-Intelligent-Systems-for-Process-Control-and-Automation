function [posterior,next_prior,log_scale] = hmm_filter_step(P,B,prior,symbol)
%HMM_FILTER_STEP One causal categorical observation, before the next transition.
% prior is the distribution of the current state before observing symbol.
% The next call receives next_prior, never posterior without a transition.
result=markov_models('filter',P,B,prior,symbol);
assert(size(result.filtered,1)==1,'Supply exactly one observation.');
posterior=result.filtered(1,:);
next_prior=posterior*P;
log_scale=result.log_likelihood;
end
