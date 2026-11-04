"""Independent balance, equilibrium, sampling and provenance tests."""
from pathlib import Path
import numpy as np
import pytest
from intelligent_control import benchmarks as b


def test_artificial_recurrences_and_validation_signals():
    assert b.siso_step(1,2,.1)==pytest.approx(1.5)
    np.testing.assert_allclose(b.mimo_step([1,2],[.1,.2]),[.3,.6])
    u,y=b.artificial_data(30,"mimo","validation")
    np.testing.assert_allclose(u[0],[0,1])
    np.testing.assert_allclose(u[25],[0,1],atol=1e-14)
    np.testing.assert_allclose(y[1],u[0])
    assert np.isfinite(y).all()


def test_artificial_seed_and_initial_history():
    u,y=b.artificial_data(400,seed=7)
    u2,y2=b.artificial_data(400,seed=7)
    np.testing.assert_array_equal(y,y2)
    assert y[1,0]==u[0,0]
    assert np.all(np.abs(u)<=2)


def test_pendulum_equilibria_and_saturation():
    np.testing.assert_allclose(b.pendulum_rhs(0,[0,0,0,0],0),0,atol=1e-14)
    np.testing.assert_allclose(b.pendulum_rhs(0,[np.pi,0,0,0],0),0,atol=1e-14)
    assert b.pendulum_rhs(0,[.01,0,0,0],0)[1]>0
    np.testing.assert_allclose(b.pendulum_rhs(0,[0,0,0,0],1000),b.pendulum_rhs(0,[0,0,0,0],120))


def test_pneumatic_quiescence_and_domain():
    np.testing.assert_allclose(b.pneumatic_rhs(0,[0,0,5e5,5e5],np.zeros(5)),0)
    with pytest.raises(ValueError): b.pneumatic_rhs(0,[.2,0,5e5,5e5],np.zeros(5))
    q=b.educational_valve_flows(1,5e5,5e5)
    rhs=b.pneumatic_rhs(0,[0,0,5e5,5e5],q,gas_constant=287.05)
    assert rhs[2]>0 and rhs[3]<0


def test_hydrostatic_zero_and_literal_actuator_gain():
    np.testing.assert_allclose(b.hydrostatic_rhs(0,[0,0,0,0],[0,0],pump_speed=100),0)
    out=b.hydrostatic_rhs(0,[0,0,0,0],[1,0],pump_speed=100)
    assert out[0]==pytest.approx(241.67/.13)


def test_tank_total_mass_and_drain_extension():
    h=np.array([.4,.2,.3]); u=np.array([3e-5,2e-5])
    rhs=b.three_tank_rhs(0,h,u)
    assert .0154*rhs.sum()==pytest.approx(u.sum(),abs=1e-18)
    rhs2=b.three_tank_rhs(0,h,u,outlet_openings=[1,0,0])
    assert .0154*rhs2.sum()==pytest.approx(u.sum()-.5e-4*.56*np.sqrt(2*9.81*.4))
    np.testing.assert_allclose(b.three_tank_rhs(0,[.2,.2,.2],[0,0]),0)


def test_bioreactor_washout_and_exact_sampling():
    np.testing.assert_allclose(b.bioreactor_rhs(0,[0,0],.75),0)
    x=np.array([.1,.7]); expected=x.copy()
    for _ in range(50): expected += .01*b.bioreactor_rhs(0,expected,.75)
    np.testing.assert_allclose(b.bioreactor_sample(x,.75),expected,rtol=0,atol=0)
    assert not np.allclose(b.bioreactor_sample(x,.75),x+.01*b.bioreactor_rhs(0,x,.75))


def test_bioreactor_nonwashout_equilibrium_audits_prose_discrepancy():
    x=np.array([.08729754781771586,.9235897740828826])
    np.testing.assert_allclose(b.bioreactor_rhs(0,x,.769),0,atol=1e-12)
    assert b.bioreactor_rhs(0,[.1236837,x[1]],.769)[1]>.29


def test_cstr_reference_points_are_rounded_equilibria():
    # The paper prints rounded values: residuals are not exactly zero.
    for x,u in [(b.CSTR_SP1,b.CSTR_U1),(b.CSTR_SP2,b.CSTR_U2)]:
        residual=b.cstr_rhs(0,x,u)
        assert np.max(np.abs(residual[:2]))<40 # mol/(m3 h)
        assert np.max(np.abs(residual[2:]))<4  # C/h


def test_cstr_cooling_units_and_feed_disturbance():
    x=b.CSTR_SP1; u=b.CSTR_U1
    expected=86.688*(x[2]-x[3])+.1*u[1]*1000
    assert b.cstr_rhs(0,x,u)[3]==pytest.approx(expected)
    disturbed=b.cstr_rhs(0,x,u,feed_concentration=4500)
    nominal=b.cstr_rhs(0,x,u)
    assert disturbed[0]-nominal[0]==pytest.approx(-600*u[0])
    np.testing.assert_allclose(disturbed[1:],nominal[1:])


@pytest.mark.parametrize("feed,qf",[(1.,1.),(.9,.7),(1.1,0.)])
def test_column_total_and_component_conservation(feed,qf):
    x=np.linspace(.01,.99,41); m=np.full(41,.5)
    inputs=[2.70629,3.20629,.45,.55,feed,.4,qf]
    deriv=b.column_a_rhs(0,np.r_[x,m],inputs)
    dx,dm=deriv[:41],deriv[41:]
    assert dm.sum()==pytest.approx(feed-.45-.55,abs=1e-13)
    assert (m*dx+x*dm).sum()==pytest.approx(feed*.4-.45*x[-1]-.55*x[0],abs=1e-13)


def test_column_lv_removes_excess_end_holdup():
    state=np.r_[np.linspace(.01,.99,41),np.full(41,.5)]
    state[41]+=.1; state[-1]+=.1
    dx=b.column_a_lv_rhs(0,state)
    assert dx[41]<0 and dx[-1]<0


def test_wind_mechanics_energy_and_rigid_rotation():
    M,D,K=b.wind_matrices()
    assert np.linalg.eigvalsh(M).min()>0
    assert np.linalg.eigvalsh(D).min()>-1e-8
    assert np.linalg.eigvalsh(K).min()>-1e-6
    np.testing.assert_allclose(K@np.array([0,0,1,1]),0)
    np.testing.assert_allclose(D@np.array([0,0,1,1]),0)


def test_rotor_map_nodes_and_no_extrapolation():
    path=Path(__file__).resolve().parents[1]/"benchmarks/data/Cp_Ct_Cq.NREL5MW.txt"
    aero=b.RotorMap(path)
    ct,cq=aero(7.5,0)
    assert ct==pytest.approx(aero.ct[11,5])
    assert cq==pytest.approx(aero.cq[11,5])
    with pytest.raises(ValueError): aero(1,0)
    x=np.array([0,0,0,0,0,0,1.2,1.2,0.])
    dx=b.wind_rhs(0,x,[10,3e6,.1],aero)
    assert dx.shape==(9,) and np.isfinite(dx).all()
    assert dx[-1]==pytest.approx(1)


def test_rk4_order_against_analytic_solution():
    coarse=b.rk4(lambda t,x:-x,[1],.2,5)[-1,0]
    fine=b.rk4(lambda t,x:-x,[1],.1,10)[-1,0]
    exact=np.exp(-1)
    assert abs(coarse-exact)/abs(fine-exact)>14


def test_dataset_loader_rejects_missing_and_nonfinite_rows(tmp_path):
    p=tmp_path/"record.csv"
    p.write_text("u,y\n1,2\n2,3\n",encoding="utf-8")
    t,u,y=b.load_io_csv(p,["u"],["y"],.01)
    np.testing.assert_allclose(t,[0,.01])
    p.write_text("u,y\n1,nan\n2,3\n",encoding="utf-8")
    with pytest.raises(ValueError): b.load_io_csv(p,["u"],["y"],.01)


def test_external_adapter_refuses_incomplete_provenance(tmp_path):
    with pytest.raises(ValueError): b.run_external(["nonexistent"],tmp_path,"results.csv",{})


@pytest.mark.parametrize("mode",["crisp","soft"])
def test_local_arx_predicts_unseen_linear_dynamics(mode):
    rng=np.random.default_rng(30)
    u=rng.normal(size=600); y=np.zeros(600)
    for k in range(599): y[k+1]=.5*y[k]+.3*u[k]
    model=b.LocalARX(mode=mode).fit(u[:400],y[:400])
    prediction=model.predict(u[400:],y[400:],recursive=True)
    assert np.max(np.abs(prediction-y[400:]))<1e-5
