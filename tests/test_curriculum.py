"""Independent numerical audits of the worked course exercises.

These checks use integration, quadrature, finite differences or constrained
optimization to cross-check analytical answers, not copied implementation paths.
"""
import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar


def test_variable_volume_tank_closed_form_matches_balance_integration():
    # Unit 01 P1: volume rises because inlet=10 and outlet=8 L/min.
    t=np.linspace(0,60,121)
    result=solve_ivp(lambda time,c:10*(.7-c)/(100+2*time),[0,60],[.2],
                     t_eval=t,rtol=1e-10,atol=1e-12)
    exact=.7-.5*(100/(100+2*t))**5
    np.testing.assert_allclose(result.y[0],exact,rtol=1e-9,atol=1e-10)
    assert .7-.5*np.exp(-1)==pytest.approx(.5160603,abs=5e-8)
    assert -10*np.log(.05)==pytest.approx(29.9573,abs=5e-5)


def test_sampled_pi_eigenvalues_and_coarse_sampling_claim():
    # Unit 02 P2; explicit integral update, exact held plant.
    radii=[]
    for ts in (1,10,20):
        a=np.exp(-ts/10);b=1-a
        matrix=np.array([[a-2*b,b],[-.2*ts,1.]])
        poles=np.linalg.eigvals(matrix)
        radii.append(np.max(abs(poles)))
        if ts==1:
            np.testing.assert_allclose(np.sort(poles),[.82060511316,.89390714095],atol=1e-9)
        if ts==10:
            assert np.linalg.det(matrix)==pytest.approx(np.exp(-1))
    assert radii[0]<1 and radii[1]<1 and radii[2]>1


def test_feedforward_inversion_and_unattainable_target():
    # Unit 03 P1: disturbance enters only through the low-concentration feed.
    target=.5;disturbance=.2
    command=(target-disturbance)/(1-disturbance)
    assert command==pytest.approx(.375)
    assert command+(1-command)*disturbance==pytest.approx(target)
    assert .4+(1-.4)*disturbance==pytest.approx(.52)
    admissible=np.linspace(0,1,1001)
    assert np.min(admissible+(1-admissible)*.7)>.5


def test_mpc_one_step_answer_matches_bounded_optimization():
    # Unit 04 P2: intersection of input and slew limits is [.3,.5].
    objective=lambda u:(.9*.2+.1*u-.8)**2+.01*(u-.4)**2
    optimum=minimize_scalar(objective,bounds=(.3,.5),method='bounded',
                            options={'xatol':1e-12})
    assert optimum.x==pytest.approx(.5,abs=2e-8)
    assert .9*.2+.1*optimum.x==pytest.approx(.23,abs=2e-9)
    assert objective(.5)<objective(.3)


def test_rga_and_unique_infeasible_steady_target():
    # Unit 03 P4 and Unit 04 P4.
    gain=np.array([[1,.6],[.4,1.]])
    rga=gain*np.linalg.inv(gain).T
    np.testing.assert_allclose(rga,[[1/.76,-.24/.76],[-.24/.76,1/.76]])
    target=np.array([1.4,.2]);command=np.linalg.solve(gain,target)
    np.testing.assert_allclose(command,[1.6842105263157894,-.47368421052631576])
    assert command[0]>1 and command[1]<0


def test_mamdani_clipped_areas_and_centroid_by_quadrature():
    # Unit 05 P3: two disjoint symmetric triangular consequents.
    z=np.linspace(-1,1,20001)
    left=np.minimum(.8,np.maximum(1-abs(z+.5)/.5,0))
    right=np.minimum(.2,np.maximum(1-abs(z-.5)/.5,0))
    assert np.trapezoid(left,z)==pytest.approx(.48,abs=1e-10)
    assert np.trapezoid(right,z)==pytest.approx(.18,abs=1e-10)
    aggregate=np.maximum(left,right)
    centroid=np.trapezoid(z*aggregate,z)/np.trapezoid(aggregate,z)
    assert centroid==pytest.approx(-5/22,abs=1e-10)
    assert abs(centroid-(-.3))>.07


def test_neural_gradient_matches_centered_finite_differences():
    # Unit 06 P2; independent numerical derivatives catch chain-rule errors.
    loss=lambda w1,w2:.5*(w2*np.tanh(.5*w1)-.4)**2
    eps=1e-5
    dw1=(loss(1+eps,.8)-loss(1-eps,.8))/(2*eps)
    dw2=(loss(1,.8+eps)-loss(1,.8-eps))/(2*eps)
    assert dw1==pytest.approx(-.009533720253174432,abs=1e-11)
    assert dw2==pytest.approx(-.014005049276745844,abs=1e-11)


def test_two_center_rbf_interpolates_and_bias_metrics_disagree():
    # Unit 06 P3 and Unit 08 P2.
    centers=np.array([0.,1.]);phi=np.exp(-.5*(centers[:,None]-centers[None,:])**2)
    weights=np.linalg.solve(phi,[0.,1.])
    np.testing.assert_allclose(weights,[-.9595173756674719,1.5819767068693265])
    np.testing.assert_allclose(phi@weights,[0.,1.],atol=1e-15)
    y=np.arange(4.);residual=y-(y+.5)
    assert np.sqrt(np.mean(residual**2))==.5
    assert 100*(1-np.var(residual)/np.var(y))==100
    assert 1-np.sum(residual**2)/np.sum((y-y.mean())**2)==pytest.approx(.8)
