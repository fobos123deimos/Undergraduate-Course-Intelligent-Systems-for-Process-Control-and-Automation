# Unit 09 - Markov chains and hidden-state diagnosis

[Course guide](../README.md) · [Notebook](../../laboratories/09-markov-hidden-state-diagnosis/notebook.ipynb) · [Exercises](../../problem-sets/09-markov-hidden-state-diagnosis/exercises.md) · [Worked solutions](../../problem-sets/09-markov-hidden-state-diagnosis/solutions.md)

**Prerequisites:** Units 01, 02 and 08; conditional probability, matrix multiplication and elementary statistics.

## An extension from process dynamics to uncertain sensor health

This additional unit extends the eight content areas of the supplied syllabus. Markov chains and hidden Markov models (HMMs) provide a probabilistic diagnosis exercise built around the teaching tank; this is not a model attributed to the 2014 benchmark article or a claim about the professor's official syllabus. The mathematical reading is Grinstead and Snell, Chapter 11, and Rabiner's HMM tutorial, Sections II-III and V, listed as references 14 and 15.

The physical concentration and the sensor's condition answer different questions. The familiar nominal tank has $V=100$ L, $q=10$ L/min and residence time $\tau=10$ min. Its sampled balance remains $c_{k+1}=ac_k+(1-a)u_k$, now with $T_s=0.2$ min and $a=e^{-0.02}$. A discrete regime $z_k$ describes normal operation, drift or a sensor fault. An HMM estimates that regime from measurements; it does not replace the mass balance or make concentration a three-valued variable.

In the synthetic laboratory, $y_k=c_k+b_{z_k}+\epsilon_k$, with biases $b=[0,0.055,0.14]$ and independent Gaussian noise of standard deviation 0.035 in normalized concentration. Form a residual $r_k=y_k-\hat c_k$, where the nominal model prediction uses only the initial condition and previously applied inputs. Assign symbols 0, 1 and 2 using cut points 0.025 and 0.095: symbol 0 for $r_k<0.025$, symbol 1 for $0.025\leq r_k<0.095$, and symbol 2 otherwise. These bins overlap in their possible hidden causes because the noise is nonzero. A large residual is evidence, not a directly observed fault label.

## From conditional probability to a Markov chain

For events with positive conditioning probability, $\Pr(A\mid B)=\Pr(A\cap B)/\Pr(B)$. A first-order Markov model assumes that the present regime contains the information from its history needed to predict the next regime:

$$\Pr(z_{k+1}=j\mid z_k=i,z_{k-1},\ldots,z_0)=\Pr(z_{k+1}=j\mid z_k=i)=P_{ij}.$$

This does not make successive states independent. Time homogeneity additionally assumes that the same $P$ applies at every sample. Here distributions are row vectors, rows index the current state and columns index the next state. Nonnegative entries and row sums of one imply $p_{k+1}=p_kP$ and $p_{k+n}=p_kP^n$. Matrix multiplication sums probabilities over intermediate states; do not raise each entry individually to the $n$th power.

The laboratory uses the state order normal, drift, sensor fault and the following deliberately hypothetical probabilities:

$$P=\begin{bmatrix}0.97&0.025&0.005\\0.04&0.93&0.03\\0.02&0.08&0.90\end{bmatrix},\qquad p_0=[0.80,0.15,0.05].$$

The matrix allows recovery from a fault. Its entries describe one 0.2-minute step, not failure rates per minute. To sample the same discrete model every five steps, use $P^5$; changing to a finer interval requires a justified model, and an arbitrary matrix root need not be a transition matrix. Physical residence time and regime persistence are distinct parameters. A self-transition probability $P_{ii}<1$ produces a geometric consecutive residence duration with mean $1/(1-P_{ii})$ samples, counted from entry through the last sample in state $i$.

## Long-run occupancy and time to failure are different quantities

A stationary row distribution satisfies $\pi P=\pi$ and $\sum_i\pi_i=1$. A finite irreducible chain has a unique stationary distribution; aperiodicity additionally ensures convergence of $p_0P^n$ to it from every initial distribution. Check these conditions rather than interpreting any numerical eigenvector as a unique limiting probability. A two-state chain that always alternates has a stationary distribution but its marginal probabilities can oscillate forever.

An absorbing fault model answers a different question. Partition the states into transient and absorbing groups so $P=\left[\begin{smallmatrix}Q&R\\0&I\end{smallmatrix}\right]$. If every transient state reaches the absorbing set with probability one, the fundamental matrix is $N=(I-Q)^{-1}$ and its row sums give expected steps until absorption. Compute the times by solving $(I-Q)t=\mathbf{1}$, then multiply by $T_s$ for minutes. The derivation is the first-step relation $t_i=1+\sum_jQ_{ij}t_j$. If an unreachable closed class exists, the expected time from some states is infinite and this finite solve is not valid. With one absorbing fault and an initial transient row $q_0$, the probability of absorption within $n$ steps is $1-q_0Q^n\mathbf{1}$. An expected lifetime is neither a deadline nor a guarantee about one trajectory.

## An HMM connects the hidden regime with observable evidence

For a categorical HMM, $B_{is}=\Pr(o_k=s\mid z_k=i)$ is the emission matrix, with one normalized row per hidden state. The model assumes conditional independence of emissions given the state sequence. Its initial distribution, transition matrix and emissions define a joint probability:

$$\Pr(z_{0:T-1},o_{0:T-1})=p_0(z_0)B_{z_0o_0}\prod_{k=1}^{T-1}P_{z_{k-1}z_k}B_{z_ko_k}.$$

The first observation is emitted by $z_0$ before a transition. This indexing convention must agree across simulation, filtering and estimation. The training data contain synthetic state labels, allowing emission probabilities to be learned from counts. Labels are available for evaluation but are withheld from the online estimator and controller. For a real experiment, maintenance records or an independent calibration procedure would be needed to justify such labels. Correlated noise, an unmeasured process disturbance or an incorrect tank model can violate the simple emission assumption and be confused with a sensor defect.

## Filtering is causal; smoothing and complete-path decoding use later data

Let $\alpha_k(i)=\Pr(z_k=i\mid o_{0:k})$. Initialize with $\alpha_0\propto p_0\odot B_{:,o_0}$. At later samples, predict $\bar\alpha_k=\alpha_{k-1}P$, multiply by the current emission likelihood and normalize:

$$w_k(i)=\bar\alpha_k(i)B_{i,o_k},\qquad s_k=\sum_iw_k(i),\qquad \alpha_k(i)=w_k(i)/s_k.$$

Use $\bar\alpha_0=p_0$ for the initial update. Scaling at every step avoids the underflow produced by multiplying a long sequence of small probabilities. With this definition of $s_k$, the sequence log likelihood is $\sum_k\log s_k$. Some references use reciprocal scale factors and therefore a negative sum; declare the convention. A zero scale signals an observation sequence impossible under the model, not permission to replace it silently with a uniform posterior.

For offline smoothing, initialize $\beta_{T-1}(i)=1$ and run backwards:

$$\beta_k(i)=\frac{\sum_jP_{ij}B_{j,o_{k+1}}\beta_{k+1}(j)}{s_{k+1}}.$$

Normalize $\alpha_k\odot\beta_k$ to obtain $\gamma_k(i)=\Pr(z_k=i\mid o_{0:T-1})$. The final smoothed posterior equals the final filtered posterior, but earlier values can change when future observations arrive.

Viterbi decoding finds the single most probable complete state path, using maximization, predecessor pointers and a final backward trace. Filtering and smoothing instead sum over alternative paths. Implement Viterbi in log space, treating a zero probability as negative infinity. Taking the largest marginal probability at each time generally does not maximize the joint path probability. All three recursions cost order $Tm^2$ for $T$ observations and $m$ states; exhaustive path enumeration is useful only for small verification examples. Smoothing and full-record Viterbi may be evaluated offline, but feeding their earlier estimates to an online controller leaks future observations.

## Estimate parameters without joining independent experiments

For labelled training sequences, let $C_{ij}$ count transitions within each sequence and $E_{is}$ count state-symbol pairs. With pseudocount $\eta>0$, $\hat P_{ij}=(C_{ij}+\eta)/(\sum_jC_{ij}+m\eta)$; normalize emission counts in the same way using the number of symbols. Estimate the initial distribution from the first state of each sequence. Never count a transition from the end of one experiment to the start of another. The laboratory uses 20 separate training trajectories of 150 samples, seed 17, and a separate 600-sample evaluation trajectory, seed 2026, with $\eta=1$. Bins, bias values, model structure and alarm policy are fixed before test evaluation.

When state labels are unavailable, Baum-Welch alternates forward-backward inference with expected-count updates. The expected occupancy is $\gamma_k(i)$; the expected transition count at a sample is proportional to $\alpha_k(i)P_{ij}B_{j,o_{k+1}}\beta_{k+1}(j)$. Normalize these pair probabilities, sum within trajectories and update $P$, $B$ and the initial distribution. Transition denominators exclude each final sample; emission denominators include it. Exact unregularized EM does not decrease training likelihood, but may find a local optimum and is sensitive to initialization. A larger training likelihood does not establish better fault detection. Hidden-state labels can permute without changing likelihood; assigning the words normal, drift and fault requires separate semantic evidence. Preserve the distinction between an unsupervised fit and labelled validation.

The optional laboratory EM demonstration starts from the known simulator transition matrix, initial distribution and theoretical emission probabilities obtained from its Gaussian noise and bin boundaries. This deliberately favorable synthetic initialization limits conclusions to parameter refinement under that information advantage. It supplies no evidence of discovering meaningful fault regimes from an uninformed initialization. Keep the labelled supervised diagnostic model separate from this training-likelihood demonstration.

## Use diagnosis as evidence for supervision, then test its limitations

The example alarm uses $\alpha_k(\mathrm{fault})\geq0.7$. Estimate a bias $\hat b_i$ for each labelled regime from its mean residual in the training data. A separate demonstration subtracts the posterior expected sensor bias, $\hat b_k=\sum_i\alpha_k(i)\hat b_i$, before passing $y_k-\hat b_k$ to the PI loop. The online controller receives these fitted bias estimates; the generator's true biases $b_i$ remain part of the synthetic experiment definition. Both decisions use filtered probabilities available at sample $k$; neither receives the current true state. Compare with the same PI loop using the raw measurement, the same hidden-state and noise sequences, and the same input constraints. An alarm threshold is an explicit operating choice, not a universal property of an HMM. False alarms, missed faults, fault-episode detection delay, posterior calibration, tracking error and actuator effort describe different tradeoffs.

Stress the diagnosis by changing the actual residence time to 14 min while retaining the 10-minute nominal predictor. The resulting model residual can resemble bias even when the sensor is healthy. Report this confusion, noisy transient classifications and any control degradation rather than assuming that bias compensation must help. This laboratory is a synthetic supervisory experiment. It supplies no formal stability, reliability or safety guarantee, and it does not validate a physical instrument or replace an independently designed protection layer.

## Computational practice

From the repository root, run `python tools/run_course.py --unit 9`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.
