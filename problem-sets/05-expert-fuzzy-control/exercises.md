# Unit 05 - Knowledge-based supervision and fuzzy control

[Lesson](../../course/05-expert-fuzzy-control/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 05.1 - Diagnose a symptom without overclaiming a fault

During a 20-minute experiment the concentration residual becomes positive, the commanded blend is 0.5, and measured blend remains 0.3. (a) Construct a rule that flags a flow-tracking problem after three consecutive samples. (b) Add a reset condition with hysteresis. (c) Explain which alternative hypotheses remain and what additional measurement would separate them.

## Problem 05.2 - A reproducible Sugeno control action

Use the three memberships from the lesson with normalized error $e=0.3$. Single-input zero-order consequents are $z_N=-1,z_Z=0,z_P=1$. (a) Calculate every membership and the Sugeno output. (b) If this gives an input increment with $K_u=0.2$ and previous input 0.96, determine the requested and applied actions. (c) Explain why changing the error normalization changes the physical controller.

## Problem 05.3 - Mamdani centroid is not singleton averaging

Two disjoint triangular output sets have centers -0.5 and 0.5, each base width 1 and height 1. Their supports are $[-1,0]$ and $[0,1]$. Minimum implication clips them at heights 0.8 and 0.2; aggregation is maximum. (a) Calculate each clipped area. (b) Calculate the centroid of the aggregate. (c) Compare with a Sugeno system using the centers as singleton consequents and the same firing strengths.

## Problem 05.4 - A fuzzy gain schedule with an explicit implementation

Let $K_p(e)=1+2\min(|e|/0.2,1)$ and $K_i=K_p/10$. (a) Calculate the gains at errors 0, 0.1 and 0.3. (b) Write a sampled PI update with saturation and back-calculation using these gains. (c) State why testing the three fixed-gain linear models is useful but insufficient to validate the gain-scheduled loop.

## Problem 05.5 - Validate the rule surface before a closed-loop comparison

A two-input fuzzy controller uses concentration error and its sampled difference. (a) Specify a grid-based test that checks correct sign, boundedness and coverage. (b) Explain why a symmetric rule table need not produce an odd control surface. (c) Design an ablation comparison between PI, fuzzy PI and fuzzy gain scheduling.
