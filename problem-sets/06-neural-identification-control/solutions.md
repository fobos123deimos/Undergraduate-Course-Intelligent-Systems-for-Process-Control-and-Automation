# Unit 06 - Neural modeling and control of dynamic systems

[Exercises](exercises.md) · [Lesson](../../course/06-neural-identification-control/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 06.1 - A perceptron for a simple supervisory condition

(a) $w=[1,1]$ and $b=-0.5$ classify only $[0,0]$ as zero. (b) The initial prediction for $[0,0]$ is 1 because of the specified tie rule. With $\Delta w=(t-\hat t)x$ and $\Delta b=t-\hat t$, the new state is $w=[0,0],b=-1$. The next sample is incorrectly predicted zero, so $w=[1,0],b=0$. (c) OR identifies a combined alarm condition, not a unique cause. Several faults and ordinary operating changes can generate either indicator. Validate labels, persistence and class imbalance, and preserve the distinction between classification performance and causal diagnosis.

## Problem 06.2 - Differentiate a minimal neural predictor

(a) $h=\tanh(0.5)=0.4621172$ and $\hat y=0.3696937$. (b) With residual $e=-0.0303063$, $\partial L/\partial w_2=eh\approx-0.0140050$. The chain rule gives $\partial L/\partial w_1=ew_2(1-h^2)x\approx-0.0095337$. Gradient descent subtracts these derivatives, so both weights initially increase. (c) Centered finite differences compare code derivatives with the implemented loss and detect chain-rule/indexing errors. An independent trajectory tests whether learning generalizes beyond the fitted samples. A correct gradient can still optimize an overfitted or causally invalid model.

## Problem 06.3 - Fit and interpret a two-center RBF

(a) With $r=e^{-1/2}$, $\Psi=\begin{bmatrix}1&r\\r&1\end{bmatrix}$. (b) Solving gives $w_1=-r/(1-r^2)\approx-0.9595174$ and $w_2=1/(1-r^2)\approx1.5819767$. The interpolating values follow directly by substitution. (c) Both radial basis functions approach zero far from their centers, so the prediction approaches zero regardless of the process physics. This is unsupported extrapolation, not evidence that the real output vanishes. Ridge regularization shrinks the weights and usually sacrifices exact interpolation to reduce variance and ill-conditioning; choose its strength using independent validation.

## Problem 06.4 - A SOM organizes operating modes

(a) Squared distances are 0.02 and 0.34, so unit 1 wins. (b) $m_1^+=[0.2,0.3]+0.5[0.1,0.1]=[0.25,0.35]$. The second unit moves by $0.5(0.2)([-0.5,-0.3])$, giving $m_2^+=[0.75,0.67]$. (c) Euclidean distances depend on feature scales, so estimate normalization on training data and keep it fixed. A cluster of high residuals is not automatically a known fault; attach labels only using independently documented operating/fault evidence. A SOM can reveal a regime shift while leaving its physical cause unresolved.

## Problem 06.5 - Put a neural prediction inside a bounded control decision

(a) The prediction is $0.36+0.04+0.0032=0.4032$, and the derivative is $0.1+0.04(0.4)=0.116$. The Newton candidate is $0.4-(0.4032-0.5)/0.116=1.234483$. (b) The feasible interval is $[0.3,0.5]$, so the bounded candidate is 0.5; its prediction is 0.415. The target is not immediately reachable within the rate limit. (c) The model derivative may be unreliable outside its supported region, and plant mismatch or unobserved dynamics may invalidate the prediction. Repeated bounded steps are not a closed-loop stability proof. Compare on independent trajectories and use a tested controller when confidence or numerical conditions fail.
