# Unit 07 - Evolutionary optimization and controller tuning

[Exercises](exercises.md) · [Lesson](../../course/07-evolutionary-tuning/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 07.1 - Binary resolution has a physical cost

(a) Binary 1001 is integer 9, hence $K_p=4(9)/15=2.4$. Resolution is $4/15=0.2666667$. (b) Integers 7 and 8 give 1.8666667 and 2.1333333, equally far from 2. There is no exact code for 2 with this endpoint mapping. (c) Require $4/(2^b-1)\leq0.02$, or $2^b\geq201$, so $b=8$. A single parameter now has 256 codes instead of 16; two such parameters have 65,536 combinations. More resolution increases possible candidates but does not by itself improve the algorithm's ability to find a useful region.

## Problem 07.2 - Selection, crossover and mutation

(a) $p_c=0.25p_1+0.75p_2=[1.25,0.125]$. (b) Mutation gives $[1.45,-0.025]$; projection gives $[1.45,0.02]$. The repair creates a pileup at the lower bound if many mutations cross it, which can affect diversity. (c) For minimization the cost-0.4 member wins. A seed reproduces pseudo-random choices only with the same generator, ordering and software behavior. Initial states, plant parameters, sampling, constraints, termination thresholds and cost definitions are also needed to reproduce fitness and selection.

## Problem 07.3 - A fitness function that does not hide violations

(a) The scalar costs are 0.50 and 0.34, so B appears better if the violation is ignored. (b) B is infeasible and must be rejected or ranked behind every feasible candidate under a feasibility-first policy; A is preferred. A hard limit cannot be traded away merely because tracking is good. (c) Detect the nonfinite state, terminate the trial, label it invalid and assign the predetermined worst fitness. Do not average only the successful prefix, because an unstable controller would then appear cheap by ending early. Preserve the failure count and cause in optimization results.

## Problem 07.4 - Tune MPC parameters without changing the ruler

(a) Round a bounded horizon gene to the nearest allowed integer and decode weight genes logarithmically, for example $q=10^{z_q}$ with $z_q\in[-1,1]$ and $r_u=10^{z_r}$ with $z_r\in[-3,0]$. Log encoding allocates resolution across ratios. (b) A positive common scaling multiplies the entire objective by a constant and leaves its minimizer unchanged, although solver numerical tolerances can be affected. (c) Use a fixed external tracking/variation/constraint metric on the same scenarios, independent of the internal MPC weights, and include deadline misses. Otherwise candidates could lower their reported internal objective simply by shrinking both weights without changing any control behavior.

## Problem 07.5 - Assess a stochastic tuning claim

(a) The nominal budget is $20\times15=300$ evaluations if every generation evaluates 20 candidates and caching/elitism do not reduce the count. Report actual calls as well. (b) Run both methods for the same number of independent seeds with matched total simulation budgets and identical training scenarios. Choose any algorithm settings on validation scenarios, freeze the selected design, then evaluate a separate family of disturbances, delays and plant parameters. Report median, spread, failures and evaluation time. (c) The best seed is a selection-biased statistic, and repeated training queries can overfit the scenario family. A finite heuristic search does not prove a global optimum. A defensible claim is an observed improvement under the specified budgets and independent test protocol.
