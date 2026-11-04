"""Inspectably small models, controllers and learning algorithms for the course.

The common `Tank` uses litres, minutes and dimensionless concentration. Time
constants, sample times and controller time units must remain consistent.
Array-oriented identification functions use rows for samples and columns for
features. `LinearMPC` predicts measured full states, with no output matrix or
state estimator. Neural normalization and model fitting use training data only.

Controllers are stateful: create a fresh instance for each independent run.
These educational implementations use synthetic data and do not certify
industrial stability, safety or generalization.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class Tank:
    """Constant-volume mixture: V dc/dt = q (u + d - c).

    V in L, q in L/min, c and u dimensionless concentrations/fractions.
    The disturbance d represents an additive change in inlet concentration.
    """
    volume: float = 100.0
    flow: float = 10.0

    def __post_init__(self):
        if self.volume <= 0 or self.flow <= 0:
            raise ValueError('Positive volume and flow required')

    @property
    def tau(self):
        """Return the residence time ``volume / flow`` in minutes."""
        return self.volume / self.flow

    def step(self, c, u, dt, disturbance=0.0):
        """Advance the exact constant-input concentration solution by one sample.

        Parameters
        ----------
        c : float or ndarray
            Current dimensionless concentration.
        u : float or ndarray
            Applied inlet concentration, held constant over the sample.
        dt : float
            Positive elapsed time in minutes.
        disturbance : float or ndarray, optional
            Additive inlet-concentration change, also held constant.

        Returns
        -------
        float or ndarray
            Concentration after ``dt``. Inputs are not clipped by this plant model.
        """
        if dt <= 0:
            raise ValueError('dt must be positive')
        a = np.exp(-dt / self.tau)
        return a*c + (1-a)*(u+disturbance)


def variable_tank_rhs(t, state, q1, q2, qout, c1, c2):
    """Mass balance with state [volume, concentration], arbitrary flow units."""
    v, c = np.asarray(state, float)
    if v <= 0 or min(q1, q2, qout) < 0:
        raise ValueError('Positive volume and nonnegative flows required')
    return np.array([q1+q2-qout, (q1*(c1-c)+q2*(c2-c))/v])


def identification_metrics(y, yhat):
    """Compare matching nonempty measured and predicted arrays.

    Parameters
    ----------
    y, yhat : array_like
        Reference and predicted values with identical shape and compatible units.

    Returns
    -------
    dict
        Maximum and mean absolute error, SSE, MSE, RMSE, variance accounted for
        in percent, and coefficient of determination. All array elements are
        aggregated together; multichannel results are not computed separately.
        ``vaf_percent`` and ``r_squared`` are ``None`` for a constant reference.

    Notes
    -----
    VAF removes the mean prediction error through its variance calculation;
    R-squared retains bias through SSE. Neither metric alone establishes
    independent validation or recursive predictive accuracy.
    """
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    if y.shape != yhat.shape or y.size == 0:
        raise ValueError('Nonempty matching arrays required')
    e = y-yhat
    var = np.var(y)
    sst = np.sum((y-y.mean())**2)
    return dict(max_abs_error=float(np.max(np.abs(e))),
                mean_abs_error=float(np.mean(np.abs(e))),
                sse=float(np.sum(e**2)), mse=float(np.mean(e**2)),
                rmse=float(np.sqrt(np.mean(e**2))),
                vaf_percent=float(100*(1-np.var(e)/var)) if var > 0 else None,
                r_squared=float(1-np.sum(e**2)/sst) if sst > 0 else None)


def control_metrics(t, reference, output, control, lower=0., upper=1.):
    """Summarize tracking, control effort and actuator excursions.

    Parameters
    ----------
    t : array_like, shape (n,)
        Sample times, in increasing order and in the chosen time unit.
    reference, output, control : array_like, shape (n,)
        Aligned scalar setpoint, plant output and applied-input traces.
    lower, upper : float, optional
        Actuator limits used to measure the largest violation.

    Returns
    -------
    dict
        Trapezoidal IAE, ISE, ITAE and integral of squared control; summed
        absolute input movement; largest input-bound violation; and final
        signed tracking error ``reference[-1] - output[-1]``.

    Notes
    -----
    ITAE uses the supplied absolute time coordinate. It is not reset at each
    setpoint change. The last stored control value contributes to trapezoidal
    effort metrics, so callers should state their terminal-sample convention.
    """
    t, r, y, u = map(lambda x: np.asarray(x, float), (t, reference, output, control))
    if not (t.shape == r.shape == y.shape == u.shape) or len(t) < 2:
        raise ValueError('Matching traces with at least two samples required')
    e = r-y
    return dict(iae=float(np.trapezoid(np.abs(e), t)),
                ise=float(np.trapezoid(e*e, t)),
                itae=float(np.trapezoid(t*np.abs(e), t)),
                control_energy=float(np.trapezoid(u*u, t)),
                total_variation=float(np.sum(np.abs(np.diff(u)))),
                constraint_violation=float(max(0., np.max(u-upper), np.max(lower-u))),
                final_error=float(e[-1]))


class PID:
    """Stateful PI/PID with filtered derivative on measurement and anti-windup.

    ``kp``, ``ki`` and ``kd`` are parallel-form gains. ``dt`` and derivative
    filter time ``tf`` use the same time unit as the plant; the teaching tank
    uses minutes. ``limits`` bounds the applied input and ``bias`` defines its
    nominal value. Integral, derivative and previous-measurement state start at
    zero, zero and unavailable, respectively.

    Conditional integration holds the integrator when a proposed update would
    drive the actuator farther into saturation. Call a new instance for each
    independent experiment; no global nonlinear stability guarantee is implied.
    """
    def __init__(self, kp, ki, kd=0., dt=.2, limits=(0., 1.), bias=.35, tf=.5):
        if dt <= 0 or tf <= 0 or limits[0] >= limits[1]:
            raise ValueError('Invalid sampling, derivative filter or limits')
        self.kp, self.ki, self.kd, self.dt = kp, ki, kd, dt
        self.limits, self.bias, self.tf = limits, bias, tf
        self.integral, self.derivative, self.last_y = 0., 0., None

    def __call__(self, r, y, disturbance=0., *, offset=0.):
        """Update the controller from a scalar reference and measurement.

        ``offset`` adds feedforward before saturation and conditional integration.
        The positional ``disturbance`` argument is accepted for the common
        simulation interface but is not used by this controller. Return a bounded
        scalar command and update the integral, derivative and measurement memory.
        """
        error = r-y
        dy = 0. if self.last_y is None else (y-self.last_y)/self.dt
        self.derivative += self.dt/(self.tf+self.dt)*(dy-self.derivative)
        candidate = self.integral + self.ki*self.dt*error
        raw = self.bias + offset + self.kp*error + candidate - self.kd*self.derivative
        value = np.clip(raw, *self.limits)
        # Hold integration only if it drives the actuator further into saturation.
        if raw == value or (raw > value and error < 0) or (raw < value and error > 0):
            self.integral = candidate
        else:
            raw = self.bias+offset+self.kp*error+self.integral-self.kd*self.derivative
            value = np.clip(raw, *self.limits)
        self.last_y = y
        return float(value)


def imc_pi(gain, tau, delay=0., lam=5.):
    """FOPDT IMC-inspired PI: Kc=tau/[K(lambda+theta)], Ti=tau."""
    if gain == 0 or tau <= 0 or delay < 0 or lam <= 0:
        raise ValueError('Invalid FOPDT parameters')
    kp = tau/(gain*(lam+delay))
    return kp, kp/tau


def fit_arx(u, y):
    """Least-squares y[k+1] = a*y[k] + b*u[k] + offset."""
    u, y = np.asarray(u), np.asarray(y)
    if len(y) != len(u) or len(y) < 4:
        raise ValueError('Matching sufficiently long input/output series required')
    x = np.column_stack([y[:-1], u[:-1], np.ones(len(y)-1)])
    theta, _, rank, _ = np.linalg.lstsq(x, y[1:], rcond=None)
    if rank < 3:
        raise ValueError('Experiment is not sufficiently exciting')
    return theta


def arx_rollout(theta, u, y0):
    """Recursively simulate an affine first-order ARX model.

    Parameters
    ----------
    theta : array_like, shape (3,)
        Coefficients ``[a, b, offset]`` returned by `fit_arx`.
    u : array_like, shape (n,)
        Nonempty input sequence; the final input is not used for a transition.
    y0 : float
        Initial measured output, supplied as the first predicted sample.

    Returns
    -------
    ndarray, shape (n,)
        Free-run predictions using previous predictions rather than future
        measured outputs. The returned first value is the given initial seed.
    """
    y = np.empty(len(u)); y[0] = y0
    for k in range(len(u)-1):
        y[k+1] = theta[0]*y[k]+theta[1]*u[k]+theta[2]
    return y


class LinearMPC:
    """Full-state linear MPC with input, input-move and optional state bounds.

    The prediction is ``x[k+1] = a @ x[k] + b @ (u[k] + disturbance)``. Matrix
    ``a`` has shape ``(n, n)`` and ``b`` has shape ``(n, m)``. ``horizon`` and
    ``control_horizon`` count samples; the last optimized input is held after
    the control horizon. Scalar ``q`` weights squared state-tracking errors,
    and ``move_weight`` weights squared successive input differences.

    ``lower``, ``upper`` and ``max_move`` apply to every input component.
    ``initial`` initializes each component of the previous feasible command.
    Optional ``output_bounds=(lo, hi)`` constrains every predicted state because
    the output is the full state; there is no separate output matrix.

    SLSQP solves the convex quadratic problem. A failed or insufficiently
    feasible solve holds the previous input and increments ``failures``;
    ``calls`` counts all solves. This fallback does not guarantee future state
    feasibility. No terminal stability condition or state estimator is added.
    """
    def __init__(self, a, b, horizon=12, control_horizon=4, q=1., move_weight=.1,
                 lower=0., upper=1., max_move=.08, initial=.35, output_bounds=None):
        self.a, self.b = np.atleast_2d(a).astype(float), np.atleast_2d(b).astype(float)
        self.n, self.m = self.b.shape
        if self.a.shape != (self.n, self.n) or not 1 <= control_horizon <= horizon:
            raise ValueError('Invalid model/horizons')
        if not (np.all(np.isfinite(self.a)) and np.all(np.isfinite(self.b))):
            raise ValueError('Finite model matrices required')
        if q <= 0 or move_weight < 0 or max_move <= 0 or lower >= upper or not lower <= initial <= upper:
            raise ValueError('Positive state weight/move bound, nonnegative move weight and feasible initial input required')
        if output_bounds is not None and output_bounds[0] >= output_bounds[1]:
            raise ValueError('Invalid output bounds')
        self.h, self.hc, self.q, self.rho = horizon, control_horizon, q, move_weight
        self.lower, self.upper, self.max_move = lower, upper, max_move
        self.previous = np.full(self.m, initial, float)
        self.output_bounds = output_bounds
        self.failures, self.calls = 0, 0

    def predict(self, z, x, disturbance):
        """Predict full-state trajectories for a flattened candidate input plan.

        Parameters
        ----------
        z : ndarray, shape (control_horizon * m,)
            Absolute actuator values, arranged sample first and input second.
        x : ndarray, shape (n,)
            Current full state.
        disturbance : float or array_like, shape (m,)
            Constant additive input disturbance over the prediction horizon.

        Returns
        -------
        ndarray, shape (horizon, n)
            States from the next sample through the final prediction step. This
            evaluation does not check constraints or change controller memory.
        """
        moves = z.reshape(self.hc, self.m)
        ys = []
        for k in range(self.h):
            x = self.a@x + self.b@(moves[min(k, self.hc-1)]+disturbance)
            ys.append(x.copy())
        return np.asarray(ys)

    def __call__(self, reference, state, disturbance=0.):
        """Solve one receding-horizon problem and apply its first command.

        ``reference`` is a constant full-state target over the horizon and
        ``state`` is the current measured full state. ``disturbance`` is an
        additive input-channel estimate. Return a float for one input or a copied
        vector for multiple inputs; update ``previous``, ``calls`` and ``failures``
        according to the solve outcome.
        """
        x, ref = np.atleast_1d(state), np.atleast_1d(reference)
        def objective(z):
            yp = self.predict(z, x, disturbance)
            du = np.diff(np.vstack([self.previous, z.reshape(self.hc,self.m)]), axis=0)
            return self.q*np.sum((yp-ref)**2) + self.rho*np.sum(du**2)
        def moves_constraint(z):
            du = np.diff(np.vstack([self.previous,z.reshape(self.hc,self.m)]),axis=0)
            return self.max_move-np.abs(du).ravel()
        constraints = [{'type':'ineq','fun':moves_constraint}]
        if self.output_bounds is not None:
            lo, hi = self.output_bounds
            def outputs_constraint(z):
                yp = self.predict(z,x,disturbance)
                return np.r_[ (yp-lo).ravel(), (hi-yp).ravel() ]
            constraints.append({'type':'ineq','fun':outputs_constraint})
        result = minimize(objective, np.tile(self.previous,self.hc), method='SLSQP',
                          bounds=[(self.lower,self.upper)]*(self.hc*self.m),
                          constraints=constraints, options={'maxiter':100,'ftol':1e-9})
        self.calls += 1
        feasible = all(np.min(c['fun'](result.x)) >= -1e-7 for c in constraints)
        feasible = feasible and np.all(result.x >= self.lower-1e-7) and np.all(result.x <= self.upper+1e-7)
        if result.success and feasible:
            self.previous = result.x[:self.m].copy()
        else:
            self.failures += 1
        return float(self.previous[0]) if self.m == 1 else self.previous.copy()


def memberships(x):
    """Three shoulder/triangle sets covering the full normalized domain."""
    x = float(np.clip(x, -1., 1.))
    return np.array([max(-x,0.), 1.-abs(x), max(x,0.)])


def fuzzy_inference(error, delta_error, kind='mamdani'):
    """9-rule PD surface; min/max/centroid or product/singleton Sugeno."""
    me, md = memberships(error), memberships(delta_error)
    labels = np.array([-1.,0.,1.])
    rules = np.clip(labels[:,None]+.5*labels[None,:], -1, 1)
    if kind == 'sugeno':
        firing = me[:,None]*md[None,:]
        return float(np.sum(firing*rules)/np.sum(firing))
    if kind != 'mamdani':
        raise ValueError('Unknown inference family')
    universe = np.linspace(-1.5,1.5,301)
    aggregate = np.zeros_like(universe)
    for i in range(3):
        for j in range(3):
            mf = np.maximum(1-abs(universe-rules[i,j])/.5,0)
            aggregate = np.maximum(aggregate,np.minimum(min(me[i],md[j]),mf))
    return float(np.trapezoid(universe*aggregate,universe)/np.trapezoid(aggregate,universe))


class FuzzyPI:
    """Incremental fuzzy PI; bounded increment and actuator prevent windup."""
    def __init__(self, dt=.2, kind='mamdani', initial=.35):
        self.dt, self.kind, self.u, self.old_error = dt, kind, initial, 0.
    def __call__(self,r,y,disturbance=0.):
        """Update the bounded incremental controller from scalar tracking error.

        The selected Mamdani or Sugeno surface uses the current error and its
        sampled change. Return an inlet fraction in ``[0, 1]`` and update command
        and error memory. ``disturbance`` is an unused interface argument.
        """
        e = r-y
        f = fuzzy_inference(e/.25,(e-self.old_error)/(.1*self.dt),self.kind)
        self.u = float(np.clip(self.u+.18*self.dt*f,0,1))
        self.old_error = e
        return self.u


class FuzzyPID(PID):
    """Gain-scheduled PID; fuzzy surface changes gains, not the error sign."""
    def __call__(self,r,y,disturbance=0.):
        """Schedule all three gains from error severity, then apply PID.

        The inherited filtered-derivative and conditional-integration states are
        updated by `PID`. Return its bounded command. Scheduling is a declared
        teaching rule, not an identified plant-dependent gain law.
        """
        severity = abs(fuzzy_inference((r-y)/.3,0,'sugeno'))
        self.kp, self.ki, self.kd = 1.4+1.2*severity, .14+.08*severity, .1*severity
        return super().__call__(r,y,disturbance)


def diagnose(y, u, reference, sensor_valid=True, residual=0.):
    """Transparent priority-ordered expert rules; outputs reasons and actions."""
    if not sensor_valid or not np.isfinite(y):
        return {'state':'sensor_fault','action':'hold_safe','reason':'invalid measurement'}
    if y > .9:
        return {'state':'high_concentration','action':'reduce_high_feed','reason':'c > 0.9'}
    if u >= .999 and reference-y > .1:
        return {'state':'actuator_limit','action':'review_setpoint','reason':'saturation with positive error'}
    if abs(residual) > .08:
        return {'state':'model_mismatch','action':'inspect_disturbance','reason':'prediction residual exceeds 0.08'}
    return {'state':'normal','action':'continue','reason':'no rule threshold exceeded'}


def train_perceptron(x, labels, epochs=100, rate=.1):
    """Train an affine binary classifier by sequential mistake updates.

    Parameters
    ----------
    x : array_like, shape (n_samples, n_features)
        Training feature rows, in the order visited during every epoch.
    labels : array_like, shape (n_samples,)
        Target labels encoded as ``-1`` or ``+1``.
    epochs : int, optional
        Maximum number of passes; stop early after a mistake-free pass.
    rate : float, optional
        Positive learning-rate coefficient.

    Returns
    -------
    ndarray, shape (n_features + 1,)
        Feature weights followed by the intercept. Classify an augmented row
        as ``+1`` when its score is nonnegative and ``-1`` otherwise. Inputs
        are not normalized internally; nonseparable data need not converge.
    """
    x, labels = np.asarray(x), np.asarray(labels)
    xb = np.column_stack([x,np.ones(len(x))]); w = np.zeros(xb.shape[1])
    for _ in range(epochs):
        changes = 0
        for row,target in zip(xb,labels):
            predicted = 1 if row@w >= 0 else -1
            if predicted != target:
                w += rate*target*row; changes += 1
        if changes == 0: break
    return w


class MLP:
    """One hidden tanh layer with normalized training data and Adam updates."""
    def __init__(self, hidden=12, seed=42):
        self.hidden, self.seed = hidden, seed
    def fit(self,x,y,epochs=1800,rate=.01):
        """Fit a scalar regressor using training-only normalization and Adam.

        Parameters
        ----------
        x : array_like, shape (n_samples, n_features)
            Training inputs; column means and standard deviations are saved.
        y : array_like, shape (n_samples,)
            Scalar targets, normalized using their training statistics.
        epochs : int, optional
            Number of full-batch gradient updates.
        rate : float, optional
            Adam learning rate.

        Returns
        -------
        MLP
            This fitted instance. ``loss`` records normalized training MSE every
            100 updates; no validation data or early stopping are used. Repeated
            calls reinitialize parameters from the instance's seed.
        """
        x,y=np.asarray(x,float),np.asarray(y,float).reshape(-1,1)
        self.xmean,self.xstd=x.mean(0),np.maximum(x.std(0),1e-8)
        self.ymean,self.ystd=y.mean(0),np.maximum(y.std(0),1e-8)
        z,target=(x-self.xmean)/self.xstd,(y-self.ymean)/self.ystd
        rng=np.random.default_rng(self.seed)
        self.params=[rng.normal(0,.3,(x.shape[1],self.hidden)),np.zeros(self.hidden),
                     rng.normal(0,.3,(self.hidden,1)),np.zeros(1)]
        m=[np.zeros_like(p) for p in self.params]; v=[p.copy() for p in m]
        self.loss=[]
        for k in range(1,epochs+1):
            w,b,wo,bo=self.params; h=np.tanh(z@w+b); e=h@wo+bo-target
            out=2*e/len(z); dh=(out@wo.T)*(1-h*h)
            grads=[z.T@dh,dh.sum(0),h.T@out,out.sum(0)]
            for j,g in enumerate(grads):
                m[j]=.9*m[j]+.1*g;v[j]=.999*v[j]+.001*g*g
                self.params[j]-=rate*(m[j]/(1-.9**k))/(np.sqrt(v[j]/(1-.999**k))+1e-8)
            if k%100==0:self.loss.append(float(np.mean(e*e)))
        return self
    def predict(self,x):
        """Predict scalar outputs in the original target units.

        Pass input rows of shape ``(n_samples, n_features)`` after calling `fit`.
        The return is a flat vector of length ``n_samples``. Saved training
        statistics are reused, without refitting on evaluation inputs.
        """
        w,b,wo,bo=self.params
        return ((np.tanh((np.asarray(x)-self.xmean)/self.xstd@w+b)@wo+bo)*self.ystd+self.ymean).ravel()


class RBF:
    """Gaussian features; centers chosen only from training inputs, ridge fit."""
    def fit(self,x,y,centers=20,seed=42,width=1.,ridge=1e-6):
        """Fit an affine-plus-Gaussian regressor from training inputs only.

        Parameters
        ----------
        x : array_like, shape (n_samples, n_features)
            Training inputs, normalized using their saved column statistics.
        y : array_like, shape (n_samples,) or (n_samples, n_outputs)
            Targets in the units retained by predictions.
        centers : int, optional
            Maximum number of centers sampled without replacement from training
            rows; at most ``n_samples`` centers are used.
        seed : int, optional
            Seed for center selection.
        width : float, optional
            Positive Gaussian width in normalized feature coordinates.
        ridge : float, optional
            Ridge penalty applied to all feature weights, including the intercept.

        Returns
        -------
        RBF
            This fitted instance. Features include an intercept, normalized linear
            inputs and Gaussian radial responses. No evaluation samples select
            centers, normalization or fitted weights.
        """
        x=np.asarray(x,float);self.mean=x.mean(0);self.std=np.maximum(x.std(0),1e-8)
        z=(x-self.mean)/self.std
        rng=np.random.default_rng(seed)
        self.centers=z[rng.choice(len(z),min(centers,len(z)),replace=False)]
        self.width=width; phi=self._features(z)
        self.weights=np.linalg.solve(phi.T@phi+ridge*np.eye(phi.shape[1]),phi.T@np.asarray(y))
        return self
    def _features(self,z):
        d=np.sum((z[:,None,:]-self.centers[None,:,:])**2,axis=2)
        return np.column_stack([np.ones(len(z)),z,np.exp(-d/(2*self.width**2))])
    def predict(self,x):
        """Predict from input rows using the fitted training transformation.

        Call `fit` first. A scalar target fit returns shape ``(n_samples,)``;
        multiple target columns retain shape ``(n_samples, n_outputs)``. This
        function neither clips predictions nor guarantees extrapolation accuracy.
        """
        return self._features((np.asarray(x)-self.mean)/self.std)@self.weights


def fit_som(x,shape=(3,3),epochs=30,seed=42):
    """Rectangular self-organizing map with neighborhood and learning decay."""
    x=np.asarray(x,float);rng=np.random.default_rng(seed)
    coords=np.array(list(np.ndindex(shape))); w=x[rng.choice(len(x),len(coords),replace=False)].copy()
    for epoch in range(epochs):
        rate=.4*(1-epoch/epochs)+.02; sigma=max(.5,2*(1-epoch/epochs))
        for row in x[rng.permutation(len(x))]:
            bmu=np.argmin(np.sum((w-row)**2,axis=1))
            influence=np.exp(-np.sum((coords-coords[bmu])**2,axis=1)/(2*sigma*sigma))
            w+=rate*influence[:,None]*(row-w)
    distances=np.linalg.norm(x[:,None,:]-w[None,:,:],axis=2)
    return w,np.argmin(distances,axis=1),float(np.mean(np.min(distances,axis=1)))


def genetic_optimize(objective,bounds,population=24,generations=24,seed=42,encoding='real',bits=12):
    """Elitism, tournament selection, crossover and mutation; fixed evaluation budget."""
    bounds=np.asarray(bounds,float); dim=len(bounds);rng=np.random.default_rng(seed)
    if encoding not in ('real','binary') or population < 4 or np.any(bounds[:,1]<=bounds[:,0]):
        raise ValueError('Invalid GA configuration')
    if encoding=='real':
        pop=rng.uniform(0,1,(population,dim))
        decode=lambda z:bounds[:,0]+z*(bounds[:,1]-bounds[:,0])
    else:
        pop=rng.integers(0,2,(population,dim*bits))
        def decode(z):
            ints=z.reshape(dim,bits)@(2**np.arange(bits-1,-1,-1))
            return bounds[:,0]+ints/(2**bits-1)*(bounds[:,1]-bounds[:,0])
    history=[]; evaluations=0
    for generation in range(generations+1):
        score=np.array([objective(decode(row)) for row in pop]); evaluations+=len(pop)
        if not np.all(np.isfinite(score)):raise ValueError('Nonfinite fitness')
        best=np.argmin(score);history.append(float(score[best]))
        if generation==generations:break
        new=[pop[best].copy()]
        def select():
            ids=rng.integers(population,size=3);return pop[ids[np.argmin(score[ids])]]
        while len(new)<population:
            a,b=select(),select()
            if encoding=='real':
                alpha=rng.random(dim);child=alpha*a+(1-alpha)*b
                child+=rng.normal(0,.08,dim)*(rng.random(dim)<.25)
                child=np.clip(child,0,1)
            else:
                cut=rng.integers(1,len(a));child=np.r_[a[:cut],b[cut:]].copy()
                child^=(rng.random(len(child))<1/len(child)).astype(int)
            new.append(child)
        pop=np.asarray(new)
    return {'parameters':decode(pop[best]).tolist(),'fitness':float(score[best]),
            'history':history,'evaluations':evaluations,'encoding':encoding,'seed':seed}
