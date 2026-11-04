"""Four-state hydrostatic transmission with explicit SI conventions.

The state order is ``[pump angle, motor angle, differential pressure,
motor speed]``. Angles are normalized displacements; pressure is in Pa, speed
in rad/s and time in seconds. Inputs are two requested normalized angles,
pump speed in rad/s and wheel-load torque in N m. There is no calibrated
voltage/current-to-angle map.

Start with `table5_interpretation`, choosing both unresolved source conventions,
then evaluate `hydrostatic_si_rhs` or inspect the six-second demonstration in
`run_hydrostatic_si`. `hydrostatic_power` supplies an independent storage and
power accounting interface.

This is a separate physical interpretation, not the literal Eq. 35 transcription
in `intelligent_control.benchmarks`. The repository's
``benchmarks/HYDROSTATIC_SOURCE_REVIEW.md`` documents the primary derivations
and missing historical calibration. Constant efficiencies describe motoring;
the ``motoring_valid`` result exposes back-driving, where this approximation
is not a passive four-quadrant machine model. Relief valves, cavitation and
actuator supply power are outside the model.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from numbers import Real
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class HydrostaticSIParameters:
    """Immutable coefficients for the declared hydraulic and mechanical model.

    Parameters
    ----------
    pump_m3_per_rad, motor_m3_per_rad : float
        Maximum pump and motor displacements in m³/rad. A swept volume per
        revolution must be divided by ``2*pi`` before construction.
    capacitance_m3_per_pa : float
        Effective differential-pressure storage coefficient in m³/Pa.
    leakage_m3_per_s_pa : float
        Linear leakage coefficient in m³/(s Pa), nonnegative.
    vehicle_inertia_kg_m2 : float
        Vehicle-side equivalent inertia in kg m², referred to the motor
        through the squared total transmission ratio by `motor_inertia`.
    cardan_damping_nm_s : float
        Cardan-side viscous damping in N m s/rad, nonnegative.
    gear_ratio, axle_ratio : float
        Signed nonzero transmission ratios; their product is `ratio`.
    gearbox_efficiency, motor_efficiency : float
        Constant efficiencies in ``(0, 1]`` for the motoring approximation.
    pump_time_constant_s, motor_time_constant_s : float
        Positive first-order normalized-angle response times in seconds.

    Notes
    -----
    Construction validates finite real coefficients and their physical ranges.
    It does not authenticate the interpretation of the historical Table 5.
    Use `table5_interpretation` to record those choices explicitly.
    """
    pump_m3_per_rad: float
    motor_m3_per_rad: float
    capacitance_m3_per_pa: float
    leakage_m3_per_s_pa: float
    vehicle_inertia_kg_m2: float = 16512.0
    cardan_damping_nm_s: float = 0.33
    gear_ratio: float = -6.12
    axle_ratio: float = -23.3
    gearbox_efficiency: float = 0.98
    motor_efficiency: float = 0.697
    pump_time_constant_s: float = 0.13
    motor_time_constant_s: float = 0.22

    def __post_init__(self):
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"{name} must be a finite real scalar")
            try:
                finite = np.isfinite(value)
            except TypeError as exc:
                raise ValueError(f"{name} must be a finite real scalar") from exc
            if not finite:
                raise ValueError(f"{name} must be finite")
            if name in ("gear_ratio", "axle_ratio"):
                if value == 0:
                    raise ValueError(f"{name} must be nonzero")
            elif name in ("leakage_m3_per_s_pa", "cardan_damping_nm_s"):
                if value < 0:
                    raise ValueError(f"{name} must be nonnegative")
            elif value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.gearbox_efficiency > 1 or self.motor_efficiency > 1:
            raise ValueError("efficiencies must lie in (0, 1]")

    @property
    def ratio(self):
        """Signed dimensionless motor-to-wheel angular-speed ratio."""
        return self.gear_ratio * self.axle_ratio

    @property
    def motor_inertia(self):
        """Vehicle inertia referred to the motor shaft, in kg m²."""
        return self.vehicle_inertia_kg_m2 / self.ratio**2

    @property
    def motor_damping(self):
        """Cardan viscous damping referred to the motor, in N m s/rad."""
        return self.cardan_damping_nm_s / self.gear_ratio**2


def table5_interpretation(*, displacement_basis: str, capacitance_basis: str):
    """Require the two unresolved Table 5 conventions to be chosen explicitly.

    ``per_revolution`` treats 145/170 cm3 as geometric swept volume and divides
    by 2*pi; ``per_radian`` reads the printed tilde symbol literally. ``effective``
    uses CH as reduced pressure capacitance; ``per_line`` takes two equal closed
    lines and therefore uses CH/2. Neither choice is authenticated source data.
    """
    if displacement_basis not in ("per_revolution", "per_radian"):
        raise ValueError("choose displacement_basis: per_revolution or per_radian")
    if capacitance_basis not in ("effective", "per_line"):
        raise ValueError("choose capacitance_basis: effective or per_line")
    volume_factor = 1e-6 / (2 * np.pi if displacement_basis == "per_revolution" else 1)
    capacitance_factor = 1e-15 / (2 if capacitance_basis == "per_line" else 1)
    return HydrostaticSIParameters(
        pump_m3_per_rad=145 * volume_factor,
        motor_m3_per_rad=170 * volume_factor,
        capacitance_m3_per_pa=1840.8 * capacitance_factor,
        leakage_m3_per_s_pa=0.14 * 1e-14,
    )


def _vector(value, length, name):
    raw = np.asarray(value)
    if np.iscomplexobj(raw) or raw.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real finite numbers")
    result = np.asarray(value, dtype=float)
    if result.shape != (length,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be a finite vector of length {length}")
    return result


def _scalar(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real scalar")
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite real scalar") from exc
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def hydrostatic_si_rhs(x, command, pump_speed, wheel_load, parameters):
    """Return [angle/s, angle/s, Pa/s, rad/s2] for a four-state SI model.

    State: [normalized pump angle, normalized motor angle, delta-p Pa, omega rad/s].
    Positive wheel_load opposes positive wheel angular speed. No clipping hides
    invalid angles or commands. Supply bounded commands to preserve angle bounds.

    Parameters
    ----------
    x : array_like, shape (4,)
        Pump angle in ``[-1, 1]``, motor angle in ``[0, 1]``, differential
        pressure in Pa and motor angular speed in rad/s. Pressure and speed
        may be signed.
    command : array_like, shape (2,)
        Requested pump and motor normalized angles, with the same bounds.
    pump_speed : float
        Pump angular speed in rad/s.
    wheel_load : float
        Signed wheel-load torque in N m.
    parameters : HydrostaticSIParameters
        Explicit SI coefficient set.

    Returns
    -------
    numpy.ndarray, shape (4,)
        State derivative in the same order, per second.

    Raises
    ------
    ValueError
        If parameters have the wrong type, signals are nonfinite/nonreal,
        dimensions disagree or normalized angles exceed their domain.
    """
    p = parameters
    if not isinstance(p, HydrostaticSIParameters):
        raise ValueError("parameters must be HydrostaticSIParameters")
    ap, am, pressure, omega = _vector(x, 4, "x")
    rp, rm = _vector(command, 2, "command")
    wp = _scalar(pump_speed, "pump_speed")
    load = _scalar(wheel_load, "wheel_load")
    if not (-1 <= ap <= 1 and 0 <= am <= 1 and -1 <= rp <= 1 and 0 <= rm <= 1):
        raise ValueError("pump angles/commands require [-1,1]; motor requires [0,1]")
    qp = p.pump_m3_per_rad * ap * wp
    qm = p.motor_m3_per_rad * am * omega
    ideal_torque = p.motor_m3_per_rad * am * pressure
    torque = p.gearbox_efficiency * p.motor_efficiency * ideal_torque
    return np.array([
        (rp - ap) / p.pump_time_constant_s,
        (rm - am) / p.motor_time_constant_s,
        (qp - qm - p.leakage_m3_per_s_pa * pressure) / p.capacitance_m3_per_pa,
        (torque - p.motor_damping * omega - load / p.ratio) / p.motor_inertia,
    ])


def hydrostatic_power(x, command, pump_speed, wheel_load, parameters):
    """Energy bookkeeping; validity flag prevents interpreting negative loss as heat.

    Hydraulic and equivalent mechanical stored energy exclude actuator/control
    supplies. Pump input here is hydraulic-port power, not engine shaft power.

    Parameters use exactly the conventions of `hydrostatic_si_rhs`.

    Returns
    -------
    dict
        ``stored_energy_j`` is hydraulic plus motor-referred mechanical
        storage. The ``*_w`` fields report hydraulic input, motor hydraulic
        power, wheel-load power, leakage/conversion/damping losses and storage
        rate in watts. ``balance_residual_w`` is storage rate minus net input
        power. ``motoring_valid`` is false when motor hydraulic power is
        negative with a nonunit combined efficiency; the resulting negative
        conversion loss must not be interpreted as dissipated heat.
    """
    p = parameters
    dx = hydrostatic_si_rhs(x, command, pump_speed, wheel_load, p)
    ap, am, pressure, omega = np.asarray(x, dtype=float)
    qp = p.pump_m3_per_rad * ap * pump_speed
    qm = p.motor_m3_per_rad * am * omega
    eta = p.gearbox_efficiency * p.motor_efficiency
    motor_port = pressure * qm
    leak_loss = p.leakage_m3_per_s_pa * pressure**2
    conversion_loss = (1 - eta) * motor_port
    damping_loss = p.motor_damping * omega**2
    load_power = wheel_load * omega / p.ratio
    rate = p.capacitance_m3_per_pa * pressure * dx[2] + p.motor_inertia * omega * dx[3]
    input_power = pressure * qp
    return dict(
        stored_energy_j=0.5 * (p.capacitance_m3_per_pa * pressure**2 + p.motor_inertia * omega**2),
        hydraulic_input_w=input_power, motor_hydraulic_power_w=motor_port,
        load_power_w=load_power, leakage_loss_w=leak_loss,
        conversion_loss_w=conversion_loss, damping_loss_w=damping_loss,
        stored_energy_rate_w=rate,
        balance_residual_w=rate - (input_power - load_power - leak_loss - conversion_loss - damping_loss),
        motoring_valid=bool(motor_port >= 0 or eta == 1),
    )


def run_hydrostatic_si(*, dt=0.002):
    """Integrate the six-second smooth-command example with fixed-step RK4.

    The explicit choices are displacement per revolution and effective
    pressure capacitance. Pump speed is 180 rad/s, wheel load is 5000 N m,
    and the initial state is an equilibrium. A smooth pump-angle excursion
    acts between 1 and 5 seconds; the motor command remains 0.8.

    Parameters
    ----------
    dt : float, optional
        Integration step in seconds, in ``(0, 0.01]`` and dividing six seconds.

    Returns
    -------
    dict
        ``t`` contains N sample times, ``x`` has shape ``(N, 4)`` and
        ``command`` has shape ``(N, 2)``. ``report`` records the chosen
        conventions, parameters, power-balance checks, operating ranges and
        limitations. All trajectories are simulated, not measured.
    """
    dt = _scalar(dt, "dt")
    if dt <= 0 or dt > 0.01 or abs(6 / dt - round(6 / dt)) > 1e-8:
        raise ValueError("dt must be in (0,.01] and divide six seconds")
    p = table5_interpretation(displacement_basis="per_revolution", capacitance_basis="effective")
    wp, load, ap, am = 180.0, 5000.0, 0.25, 0.8
    dm = p.motor_m3_per_rad * am
    eta = p.gearbox_efficiency * p.motor_efficiency
    q = p.pump_m3_per_rad * ap * wp
    omega = (q - p.leakage_m3_per_s_pa * load / (p.ratio * eta * dm)) / (
        dm + p.leakage_m3_per_s_pa * p.motor_damping / (eta * dm))
    pressure = (p.motor_damping * omega + load / p.ratio) / (eta * dm)
    time = np.arange(round(6 / dt) + 1) * dt
    states = np.empty((len(time), 4))
    states[0] = (ap, am, pressure, omega)

    def command(t):
        return np.array([0.25 + (0.04 * np.sin(np.pi * (t - 1) / 4)**2 if 1 < t < 5 else 0), 0.8])

    def f(t, x):
        return hydrostatic_si_rhs(x, command(t), wp, load, p)

    for k, t in enumerate(time[:-1]):
        x = states[k]
        k1 = f(t, x)
        k2 = f(t + dt/2, x + dt*k1/2)
        k3 = f(t + dt/2, x + dt*k2/2)
        k4 = f(t + dt, x + dt*k3)
        states[k+1] = x + dt*(k1 + 2*k2 + 2*k3 + k4)/6
    commands = np.array([command(t) for t in time])
    powers = [hydrostatic_power(x, r, wp, load, p) for x, r in zip(states, commands)]
    report = dict(
        model="separate_si_interpretation", data_kind="simulated_demonstration",
        displacement_basis="per_revolution", capacitance_basis="effective",
        input_contract="requested_normalized_angles; no voltage/current calibration",
        parameters=asdict(p), dt_s=dt, duration_s=6.0, samples=len(time),
        max_abs_power_balance_residual_w=max(abs(q["balance_residual_w"]) for q in powers),
        all_motoring=all(q["motoring_valid"] for q in powers),
        pressure_min_pa=float(states[:, 2].min()), pressure_max_pa=float(states[:, 2].max()),
        motor_speed_min_rad_s=float(states[:, 3].min()), motor_speed_max_rad_s=float(states[:, 3].max()),
        final_state=states[-1].tolist(),
        limitations=["not a replication of IEEE 2007 numerical results", "unresolved Table 5 conventions are explicit choices", "constant efficiencies restricted to motoring", "no relief valves, cavitation or actuator power model"],
    )
    return dict(t=time, x=states, command=commands, report=report)


def main():
    """Run the command-line demonstration and write its CSV and JSON report.

    ``--output-dir`` selects the destination, defaulting to
    ``benchmarks/results/hydrostatic-si`` relative to the working directory.
    Existing ``simulation.csv`` and ``python-summary.json`` files there are
    overwritten. The report is also printed to standard output.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/results/hydrostatic-si"))
    args = parser.parse_args()
    result = run_hydrostatic_si()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.output_dir / "simulation.csv", np.column_stack((result["t"], result["command"], result["x"])), delimiter=",", comments="", header="time_s,pump_command,motor_command,pump_angle,motor_angle,pressure_pa,motor_speed_rad_s")
    (args.output_dir / "python-summary.json").write_text(json.dumps(result["report"], indent=2) + "\n", encoding="utf8")
    print(json.dumps(result["report"], indent=2))


if __name__ == "__main__":
    main()
