"""Independent unit, conservation and limiting-case checks for the SI variant."""
from dataclasses import replace

import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from intelligent_control.hydrostatic_si import (
    hydrostatic_power, hydrostatic_si_rhs, run_hydrostatic_si, table5_interpretation,
)


def parameters():
    return table5_interpretation(displacement_basis="per_revolution", capacitance_basis="effective")


def test_explicit_conventions_and_geometric_units():
    p = parameters()
    np.testing.assert_allclose(p.pump_m3_per_rad * 2*np.pi, 145e-6, rtol=1e-15)
    # A full pump at one revolution/second delivers precisely its swept volume.
    dx = hydrostatic_si_rhs([1, 0, 0, 0], [1, 0], 2*np.pi, 0, p)
    np.testing.assert_allclose(dx[2]*p.capacitance_m3_per_pa, 145e-6, rtol=1e-15)
    q = table5_interpretation(displacement_basis="per_radian", capacitance_basis="per_line")
    assert q.capacitance_m3_per_pa == p.capacitance_m3_per_pa/2
    np.testing.assert_allclose(q.motor_m3_per_rad/p.motor_m3_per_rad, 2*np.pi)


def test_bar_mm3_equations_equal_si_with_declared_corrections():
    # Independent evaluation in the units explicitly stated in Schulte 2008 p.95.
    # Motor displacement follows derived Eq.13, not inconsistent combined Eq.16.
    p = parameters()
    vp, vm = 145e3/(2*np.pi), 170e3/(2*np.pi)  # mm3/rad
    for ap, am, pressure_bar, omega, wp, load in [
        (.3,.8,100,50,180,5000), (-.4,.6,-80,-40,200,-3000), (0,0,0,0,0,0)]:
        command = [.2,.7]
        native = np.array([
            (command[0]-ap)/.13, (command[1]-am)/.22,
            10/1840.8*(vp*ap*wp-vm*am*omega-.14*pressure_bar),
            ((-6.12)**2*(-23.3)**2*.98*.697*vm*1e-4*am*pressure_bar
             -.33*(-23.3)**2*omega-load*(-6.12)*(-23.3))/16512,
        ])
        native[2] *= 1e5
        actual = hydrostatic_si_rhs([ap,am,pressure_bar*1e5,omega],command,wp,load,p)
        np.testing.assert_allclose(actual, native, rtol=2e-14, atol=2e-10)


def test_motor_torque_uses_motor_displacement_and_gear_work():
    p = replace(parameters(), gearbox_efficiency=1, motor_efficiency=1,
                cardan_damping_nm_s=0, leakage_m3_per_s_pa=0)
    x = [0,.5,2e6,10]
    dx = hydrostatic_si_rhs(x,[0,.5],0,3000,p)
    expected_torque = (170e-6/(2*np.pi))*.5*2e6
    assert abs(dx[3]*p.motor_inertia + 3000/p.ratio - expected_torque) < 1e-12
    other = hydrostatic_si_rhs(x,[0,.5],0,3000,replace(p,pump_m3_per_rad=3*p.pump_m3_per_rad))
    assert other[3] == dx[3]  # A different pump cannot change a motor's torque constant.
    power = hydrostatic_power(x,[0,.5],0,3000,p)
    np.testing.assert_allclose(power["load_power_w"],3000*(10/p.ratio),rtol=2e-15)


def test_closed_ports_have_analytic_leakage_decay_and_actuator_response():
    p = replace(parameters(), leakage_m3_per_s_pa=2e-12)
    initial = [0,0,3e6,0]
    sol = solve_ivp(lambda t,x: hydrostatic_si_rhs(x,[.4,0],0,0,p), [0,1],initial,
                    rtol=1e-10,atol=1e-11)
    expected_p = 3e6*np.exp(-p.leakage_m3_per_s_pa/p.capacitance_m3_per_pa)
    np.testing.assert_allclose(sol.y[2,-1],expected_p,rtol=1e-9)
    np.testing.assert_allclose(sol.y[0,-1],.4*(1-np.exp(-1/.13)),rtol=1e-9)
    assert np.all(sol.y[0]>=0) and np.all(sol.y[0]<=.4)
    assert np.all(sol.y[3]==0)


def test_lossless_closed_exchange_matches_matrix_exponential_and_conserves_energy():
    p = replace(parameters(), leakage_m3_per_s_pa=0,cardan_damping_nm_s=0,
                motor_efficiency=1,gearbox_efficiency=1)
    dm = p.motor_m3_per_rad*.6
    a = np.array([[0,-dm/p.capacitance_m3_per_pa],[dm/p.motor_inertia,0]])
    initial = np.array([0,.6,2e6,15])
    sol = solve_ivp(lambda t,x: hydrostatic_si_rhs(x,[0,.6],0,0,p),[0,1],initial,
                    rtol=2e-10,atol=1e-10,max_step=.005)
    np.testing.assert_allclose(sol.y[2:,-1],expm(a)@initial[2:],rtol=2e-8)
    energy = .5*(p.capacitance_m3_per_pa*sol.y[2]**2+p.motor_inertia*sol.y[3]**2)
    assert np.max(abs(energy/energy[0]-1)) < 2e-8


def test_power_balance_dissipation_and_backdrive_limit_are_visible():
    p = parameters()
    x = np.array([.3,.8,1e7,50.])
    dx = hydrostatic_si_rhs(x,[.3,.8],180,5000,p)
    powers = hydrostatic_power(x,[.3,.8],180,5000,p)
    # Differentiate independently defined total storage in the RHS direction.
    def energy(z):
        return (p.capacitance_m3_per_pa*z[2]**2+p.motor_inertia*z[3]**2)/2
    h = 1e-7
    derivative = (energy(x+h*dx)-energy(x-h*dx))/(2*h)
    expected = powers["hydraulic_input_w"]-powers["load_power_w"]-sum(
        powers[key] for key in ("leakage_loss_w","conversion_loss_w","damping_loss_w"))
    np.testing.assert_allclose(derivative,expected,rtol=1e-7)
    assert powers["motoring_valid"]
    assert all(powers[k]>=0 for k in ("leakage_loss_w","conversion_loss_w","damping_loss_w"))
    backdrive = hydrostatic_power([.3,.8,-1e7,50],[.3,.8],180,5000,p)
    assert not backdrive["motoring_valid"] and backdrive["conversion_loss_w"] < 0


def test_example_refinement_and_physical_operating_region():
    coarse, fine = run_hydrostatic_si(dt=.004), run_hydrostatic_si(dt=.002)
    # Scale heterogeneous state units before comparing the two integrations.
    error = (coarse["x"]-fine["x"][::2])/np.array([1,1,1e7,100])
    assert np.max(abs(error)) < 3e-7
    r = fine["report"]
    assert r["all_motoring"] and r["pressure_min_pa"] > 0
    assert r["max_abs_power_balance_residual_w"] < 1e-9
    assert r["motor_speed_max_rad_s"]-r["motor_speed_min_rad_s"] > 5


def test_invalid_inputs_and_unresolved_choices_are_not_silently_filled():
    p = parameters()
    for kwargs in ({},{"displacement_basis":"guess","capacitance_basis":"effective"}):
        with pytest.raises((ValueError,TypeError)):
            table5_interpretation(**kwargs)
    for change in ({"gear_ratio":0},{"motor_efficiency":1.1},{"pump_m3_per_rad":-1},
                   {"motor_time_constant_s":np.nan},{"leakage_m3_per_s_pa":-1},
                   {"gear_ratio":1j},{"gear_ratio":"6"}):
        with pytest.raises(ValueError): replace(p,**change)
    for x,u,wp in [([2,.8,1e6,10],[.3,.8],180),([0,-.1,0,0],[0,.8],180),
                   ([0,.8,0,0],[0,2],180),([0,.8,np.nan,0],[0,.8],180),
                   ([0,.8,0,0],[0,.8],"180"),([0,.8,0,0],[0,.8],np.inf)]:
        with pytest.raises(ValueError): hydrostatic_si_rhs(x,u,wp,0,p)
