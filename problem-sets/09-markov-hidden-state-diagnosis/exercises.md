# Unit 09 - Markov chains and hidden-state diagnosis

[Lesson](../../course/09-markov-hidden-state-diagnosis/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 09.1 - Predict sensor regimes and interpret a stationary distribution

A simplified sensor has states normal and drift, sampled every 0.2 min, with $P=\left[\begin{smallmatrix}0.9&0.1\\0.2&0.8\end{smallmatrix}\right]$ and $p_0=[1,0]$. (a) Explain the Markov and time-homogeneity assumptions, and calculate $P^2$ and the probability of drift after two steps. (b) Derive the stationary distribution and an expression for $p_n$; calculate $p_5$. (c) Find the expected consecutive duration of a normal episode. (d) Explain why stationarity does not mean that the sensor stops changing state, and give a two-state example with a stationary distribution but no convergence from $p_0$.

## Problem 09.2 - Separate expected lifetime from near-term fault probability

For a different maintenance model, use states normal, degraded and failed, with $P=\left[\begin{smallmatrix}0.8&0.15&0.05\\0.1&0.7&0.2\\0&0&1\end{smallmatrix}\right]$ and 0.2-minute sampling. (a) Identify the transient block and derive expected steps to failure using first-step equations. (b) Starting in normal, calculate the probability of failure within two transitions. (c) Convert the expected times into minutes and distinguish them from a guaranteed operating duration. (d) Explain why these calculations cannot be transferred unchanged to the recoverable three-state laboratory chain or to a model with a closed healthy class.

## Problem 09.3 - Check three different HMM inference questions by enumeration

Use a two-state HMM with $p_0=[0.6,0.4]$, $P=\left[\begin{smallmatrix}0.7&0.3\\0.4&0.6\end{smallmatrix}\right]$ and $B=\left[\begin{smallmatrix}0.5&0.5\\0.1&0.9\end{smallmatrix}\right]$, where columns of $B$ represent observation symbols 0 and 1. Observe $[0,1,0]$, with emission before the first transition. (a) Calculate the three scaled filtered distributions and the observation likelihood. (b) Enumerate the eight state paths and obtain the smoothed probability of state 0 at each sample. (c) Identify the Viterbi path and its joint probability. (d) Explain which outputs can be used by a controller at the second sample and why long sequences require scaling or log arithmetic.

## Problem 09.4 - Learn from separate trajectories and preserve state meaning

Two independent labelled experiments have state sequences $[0,0,1,1]$ and $[1,0,0]$, with corresponding symbol sequences $[0,0,1,1]$ and $[1,0,1]$. (a) Estimate the initial distribution, transition matrix and emission matrix using pseudocount one in every category. (b) Show exactly how joining the experiments would corrupt a transition estimate. (c) Describe the expected counts needed for Baum-Welch if the labels were removed. (d) State which conclusions can and cannot follow from an increase in training likelihood, and design a test split suitable for sensor diagnosis.

## Problem 09.5 - Turn a posterior into a reviewable supervisory decision

At one sample of the three-state tank experiment, the filtered probabilities for normal, drift and sensor fault are $[0.10,0.25,0.65]$. The measurement is $y=0.70$. For this worked calculation, suppose the calibrated per-state bias estimates are $[0,0.055,0.14]$; finite training records in the laboratory produce their own estimates. Use the laboratory transition matrix from the lesson. (a) Calculate posterior mean bias, the corrected concentration measurement and next-step fault probability. (b) Apply an alarm threshold of 0.7 to the current fault probability. For a separate single-sample decision model with false-alarm cost 2 and missed-fault cost 8, derive the Bayes alarm threshold and compare its decision. (c) Design a causal comparison between raw-measurement PI and filtered-bias-corrected PI. (d) Explain how changing actual tank residence time to 14 min while keeping a 10-minute predictor can defeat the diagnostic interpretation, and state what evidence is still needed before physical use.
