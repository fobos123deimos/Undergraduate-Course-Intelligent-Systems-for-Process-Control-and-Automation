import numpy as np
import pytest
from intelligent_control.methods import *
from intelligent_control.experiments import simulate, unit1, unit6

def test_tank_analytical_response_and_mass_balance():
    tank=Tank();c=0.
    for _ in range(100):c=tank.step(c,1,.1)
    assert c==pytest.approx(1-np.exp(-1),abs=1e-13)
    v,c=20.,.4;q1,q2,qo,c1,c2=2.,3.,4.,.1,.8
    dv,dc=variable_tank_rhs(0,[v,c],q1,q2,qo,c1,c2)
    assert v*dc+c*dv==pytest.approx(q1*c1+q2*c2-qo*c)

def test_metrics_distinguish_paper_max_error_from_mean_absolute_error():
    m=identification_metrics([0,0,3],[0,1,1])
    assert m['max_abs_error']==2
    assert m['mean_abs_error']==1
    assert identification_metrics([1,1],[1,1])['vaf_percent'] is None

def test_arx_on_held_out_excitation():
    result=unit1()['summary']
    assert result['analytic_max_error']<1e-12
    assert abs(result['estimated_tau_min']-10)<.5
    assert result['free_run']['rmse']<.005

def test_pid_recovery_and_bounds():
    c=PID(3,.5,bias=0.)
    for _ in range(500):assert 0<=c(3,0)<=1
    assert abs(c.integral)<1e-12
    assert c(0,1)==0
    trace=simulate(PID(2,.2))
    assert trace['metrics']['constraint_violation']==0
    assert abs(trace['metrics']['final_error'])<.02

def test_imc_closed_loop_poles():
    kp,ki=imc_pi(1,10,lam=5)
    assert np.all(np.real(np.roots([10,1+kp,ki]))<0)

def test_feedforward_saturation_is_seen_by_antiwindup():
    c=PID(2,.2)
    for _ in range(200):assert c(.1,.4,offset=-.4)==0.
    assert c.integral==0.

def test_mpc_respects_input_and_move_constraints_and_tracks():
    a=np.array([[.9,0],[0,.85]]);b=np.eye(2)-a
    c=LinearMPC(a,b,horizon=12,control_horizon=4,max_move=.06,initial=.3)
    x=np.array([.3,.3]);previous=np.array([.3,.3])
    for _ in range(60):
        u=c([.65,.5],x)
        assert np.max(abs(u-previous))<=.060001
        assert np.all((u>=0)&(u<=1))
        x=a@x+b@u;previous=u
    assert c.failures==0
    assert np.max(abs(x-[.65,.5]))<.005

def test_mpc_rejects_nonconvex_or_infeasible_configuration():
    with pytest.raises(ValueError):LinearMPC([[.9]],[[.1]],move_weight=-1)
    with pytest.raises(ValueError):LinearMPC([[.9]],[[.1]],initial=2.)
    with pytest.raises(ValueError):LinearMPC([[.9]],[[.1]],q=0)

def test_fuzzy_partition_surface_and_rules():
    for x in np.linspace(-2,2,21):assert memberships(x).sum()==pytest.approx(1.)
    for family in ('mamdani','sugeno'):
        assert abs(fuzzy_inference(0,0,family))<1e-12
        assert fuzzy_inference(.5,.2,family)>0
        assert fuzzy_inference(-.5,-.2,family)<0
    assert diagnose(float('nan'),1,1)['state']=='sensor_fault'
    assert diagnose(.95,1,1)['state']=='high_concentration'

def test_neural_held_out_and_recursive_errors():
    result=unit6()['summary']
    for name in ('MLP','RBF'):
        assert result['models'][name]['rmse']<.02
        assert result['models'][name]['free_run_rmse']<.05
    assert result['perceptron_accuracy']>.95

@pytest.mark.parametrize('encoding',['real','binary'])
def test_ga_elitism_bounds_and_budget(encoding):
    result=genetic_optimize(lambda x:np.sum((x-.25)**2),[(0.,1.),(0.,1.)],
                            population=16,generations=20,encoding=encoding)
    assert result['evaluations']==16*21
    assert np.all(np.diff(result['history'])<=1e-15)
    assert result['fitness']<.01
