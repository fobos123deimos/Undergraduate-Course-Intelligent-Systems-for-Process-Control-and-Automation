"""Independent conservation, sonic-flow and domain checks of the SI variant."""
from dataclasses import replace
import numpy as np
import pytest
from intelligent_control import pneumatic_physical as p


def test_molar_to_specific_units_and_geometry():
    a=p.Parameters()
    assert a.R==pytest.approx(287.058,rel=1e-6)
    assert a.cp-a.cv==pytest.approx(a.R)
    assert a.cp/a.cv==pytest.approx(1.4)
    assert a.residual_volume==pytest.approx(1.5e-4)
    for position in [-.125,0,.125]:
        x=p.state_from_pressures(position=position,p=a);pressures,volumes=p.observe(x,a)
        np.testing.assert_allclose(pressures,[5e5,5e5])
        assert min(volumes)>=a.residual_volume*(1-1e-14)


def test_sonic_limit_independent_mach_one_expression_and_scaling():
    a=p.Parameters();g=a.gamma;area=1e-6;up=9e5;T=293.15
    expected=a.discharge_coefficient*area*up/np.sqrt(T)*np.sqrt(g/a.R)*((g+1)/2)**(-(g+1)/(2*(g-1)))
    q=p.orifice_flow(up,1e5,T,T,area,a)
    assert q==pytest.approx(expected)
    assert p.orifice_flow(up,2e5,T,T,area,a)==pytest.approx(q)
    assert p.orifice_flow(up,1e5,T*4,T,area*2,a)==pytest.approx(q)
    assert p.orifice_flow(2*up,2e5,T,T,area,a)==pytest.approx(2*q)


def test_flow_continuity_reverse_direction_and_zero_difference():
    a=p.Parameters();critical=(2/(a.gamma+1))**(a.gamma/(a.gamma-1));up=9e5
    low=p.orifice_flow(up,up*critical*(1-1e-8),300,280,1e-6,a)
    high=p.orifice_flow(up,up*critical*(1+1e-8),300,280,1e-6,a)
    assert low==pytest.approx(high,rel=1e-12)
    q=p.orifice_flow(up,8e5,310,290,1e-6,a)
    assert q>0 and q<low
    assert p.orifice_flow(8e5,up,290,310,1e-6,a)==pytest.approx(-q)
    assert p.orifice_flow(up,up,300,280,1e-6,a)==0
    assert p.orifice_flow(up,1e5,300,280,0,a)==0


@pytest.mark.parametrize('voltage',[-.7,.7])
def test_mass_and_open_system_first_law(voltage):
    a=replace(p.Parameters(),bypass_area=1e-8,wall_conductance=.2)
    x=p.state_from_pressures(.02,.03,[6e5,4e5],[305,285],a)
    dx,info=p.balances(x,voltage,a,external_force=3.)
    q=info['mass_flows'];P,V=p.observe(x,a)
    # Internal bypass cancels from the two-chamber total mass.
    assert sum(dx[2:4])==pytest.approx(q[1]+q[2]-q[0]-q[3],abs=1e-17)
    Udot=a.cv*(x[4:6]*dx[2:4]+x[2:4]*dx[4:6])
    external_enthalpy=a.cp*(a.reservoir_temperature*(q[1]+q[2])-x[4]*q[0]-x[5]*q[3])
    assert sum(Udot)==pytest.approx(external_enthalpy+sum(info['heat_rate'])-a.area*(P[0]-P[1])*x[1],abs=1e-10)
    total_energy_rate=sum(Udot)+a.total_mass*x[1]*dx[1]+a.total_mass*a.gravity*dx[0]
    expected=external_enthalpy+sum(info['heat_rate'])-info['friction']*x[1]-3*x[1]
    assert total_energy_rate==pytest.approx(expected,abs=1e-10)
    epsilon=1e-7
    Pplus=p.observe(x+epsilon*dx,a)[0];Pminus=p.observe(x-epsilon*dx,a)[0]
    np.testing.assert_allclose((Pplus-Pminus)/(2*epsilon),info['pressure_rate'],rtol=1e-6,atol=.001)


def test_bypass_conserves_mass_and_enthalpy_for_unequal_temperatures():
    a=replace(p.Parameters(),bypass_area=2e-7)
    x=p.state_from_pressures(0,0,[7e5,3e5],[320,270],a)
    dx,info=p.balances(x,0,a)
    assert info['mass_flows'][4]>0 and dx[2]<0 and dx[3]>0
    assert sum(dx[2:4])==pytest.approx(0,abs=1e-18)
    assert sum(a.cv*(x[4:6]*dx[2:4]+x[2:4]*dx[4:6]))==pytest.approx(0,abs=1e-10)


def test_full_cylinder_reverse_ports_use_actual_upstream_enthalpy():
    a=p.Parameters();x=p.state_from_pressures(0,0,[1.2e6,.8e5],[330,270],a)
    dx,info=p.balances(x,.7,a);q=info['mass_flows']
    assert q[1]<0 and q[3]<0
    expected=a.cp*(q[1]*x[4]-q[3]*a.reservoir_temperature)
    actual=sum(a.cv*(x[4:6]*dx[2:4]+x[2:4]*dx[4:6]))
    assert actual==pytest.approx(expected,abs=1e-10)


@pytest.mark.parametrize('mass',[3.,6.,9.])
def test_vertical_equilibrium_and_missing_gravity_counterexample(mass):
    a=replace(p.Parameters(),load_mass=mass);x=p.equilibrium(p=a)
    np.testing.assert_allclose(p.rhs(0,x,0,a),0,atol=1e-10)
    P,_=p.observe(x,a)
    assert P[0]-P[1]==pytest.approx(a.total_mass*a.gravity/a.area)
    assert p.rhs(0,p.state_from_pressures(p=a),0,a)[1]==pytest.approx(-a.gravity)


def test_equilibrium_with_heat_transfer_uses_wall_temperature():
    a=replace(p.Parameters(),wall_conductance=.2,wall_temperature=313.15)
    x=p.equilibrium(p=a)
    np.testing.assert_array_equal(x[4:6],[313.15,313.15])
    np.testing.assert_allclose(p.rhs(0,x,0,a),0,atol=1e-10)


def test_complex_states_rejected_before_conversion():
    x=p.equilibrium().astype(complex);x[0]=.01j
    for function in [lambda:p.observe(x),lambda:p.balances(x,0),lambda:p.rhs(0,x,0),
                     lambda:p.state_from_pressures(position=.01j),
                     lambda:p.state_from_pressures(pressures=[5e5+1j,5e5]),
                     lambda:p.state_from_pressures(temperatures=[293+1j,293]),
                     lambda:p.balances(p.equilibrium(),1j),
                     lambda:p.orifice_flow(5e5+1j,1e5,300,300,1e-6)]:
        with pytest.raises(ValueError,match='real'):function()


def test_sealed_adiabatic_invariants_and_total_energy():
    a=replace(p.Parameters(),viscous=0,coulomb=0,gravity=0)
    initial=p.state_from_pressures(0,.03,p=a)
    t,x=p.simulate(lambda t:0,initial,a,duration=.3,samples=151)
    values=[];energies=[]
    for row in x:
        P,V=p.observe(row,a);values.append(P*V**a.gamma)
        energies.append(sum(a.cv*row[2:4]*row[4:6])+.5*a.total_mass*row[1]**2)
    values=np.array(values)
    np.testing.assert_allclose(values/values[0],1,rtol=2e-9,atol=0)
    np.testing.assert_allclose(np.array(energies)/energies[0],1,rtol=2e-10,atol=0)


def test_voltage_saturation_and_dissipative_regularized_friction():
    a=p.Parameters()
    for velocity in [-.1,-.001,0,.001,.1]:
        x=p.state_from_pressures(velocity=velocity,p=a)
        dx,info=p.balances(x,100,a)
        assert info['voltage']==10 and info['spool_m']==pytest.approx(.001)
        assert info['orifice_area_m2']==pytest.approx(2e-6)
        assert info['friction']*velocity>=0
        np.testing.assert_array_equal(dx,p.rhs(0,x,10,a))


@pytest.mark.parametrize('kwargs',[{'gamma':1},{'midpoint_volume':1e-4},{'load_mass':-1},{'discharge_coefficient':2},{'air_molar_mass':0},{'friction_velocity':0},{'port_width':float('nan')}])
def test_invalid_parameters_rejected(kwargs):
    with pytest.raises(ValueError):p.Parameters(**kwargs)


def test_invalid_states_flows_and_unsupported_stroke_rejected():
    for position in [-.126,.126]:
        with pytest.raises(ValueError,match='stroke'):p.state_from_pressures(position=position)
    with pytest.raises(ValueError):p.orifice_flow(0,1e5,300,300,1e-6)
    with pytest.raises(ValueError):p.orifice_flow(1e5,2e5,300,300,-1e-6)
    with pytest.raises(ValueError):p.observe([0,0,-.01,.01,300,300])


def test_published_local_models_keep_operating_point_and_voltage_units():
    expected=[(1,0,0,-26,-8.7e6,1.1e10),(3,6,0,-11,-8.9e6,1e10),(15,6,.08,-14,-1.06e7,1.24e10)]
    for index,mass,position,ql,qv,qu in expected:
        m=p.identified_local_model(index)
        assert m['load_kg']==mass and m['position_m']==position
        assert m['B'][2]==pytest.approx(qu*1e-4)
        np.testing.assert_allclose(m['A']@np.array([0,.1,1e4]),[.1,(-135*.1+2.8e-3*1e4)/(mass+2.9),qv*.1+ql*1e4])
    with pytest.raises(ValueError):p.identified_local_model(2)
