# Unit 07 - Evolutionary optimization and controller tuning

[Lesson](../../course/07-evolutionary-tuning/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 07.1 - Binary resolution has a physical cost

Encode $K_p\in[0,4]$ with four bits. (a) Decode chromosome 1001 and compute its resolution. (b) Find the nearest representable value to $K_p=2$. (c) Determine the minimum number of bits needed for resolution no greater than 0.02 and discuss the effect on search-space size.

## Problem 07.2 - Selection, crossover and mutation

Two real chromosomes are $p_1=[2,0.2]$ and $p_2=[1,0.1]$. (a) Perform blend crossover with $\alpha=0.25$. (b) Apply mutation $[0.2,-0.15]$ and repair into bounds $K_p\in[0,4]$, $K_i\in[0.02,0.5]$ by projection. (c) Explain how a two-member tournament chooses among costs 0.6 and 0.4 and why recording the random seed is insufficient without the full evaluation protocol.

## Problem 07.3 - A fitness function that does not hide violations

Candidate A has IAE 0.35, input variation 1.5 and no violations. Candidate B has IAE 0.30, variation 0.4 and one violation of a declared hard concentration limit. (a) Rank them under the soft cost $J=\mathrm{IAE}+0.1\,\mathrm{TV}$. (b) Rank them when the declared hard constraint is enforced. (c) Explain how to treat a simulation that becomes nonfinite rather than completing the horizon.

## Problem 07.4 - Tune MPC parameters without changing the ruler

A chromosome contains horizon $N$, output weight $q$ and move weight $r_u$. Bounds are $N\in\{3,\ldots,20\}$, $q\in[0.1,10]$, $r_u\in[0.001,1]$. (a) Propose a valid decoding for real genes. (b) Explain why multiplying both weights by 10 does not change an exact unconstrained optimizer. (c) Define an external fitness that still permits meaningful comparison among these chromosomes.

## Problem 07.5 - Assess a stochastic tuning claim

Two search methods each use population 20 for 15 evaluated generations, including their initial population. Method A reports only its best seed; B reports ten seeds. (a) Calculate the nominal evaluation budget per seed. (b) Propose a matched experiment and final test. (c) Explain why a lower best training cost does not prove superior generalization or a global optimum.
