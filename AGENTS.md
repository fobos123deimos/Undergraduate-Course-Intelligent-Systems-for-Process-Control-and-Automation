# Diagram conventions

## Required reference

The user's standing preference is to **always use [TikZ.net](https://tikz.net/)
as the primary visual and implementation reference for technical diagrams and
TikZ figures in this repository**. Consult relevant examples before creating or
revising a drawing, and record the exact example URLs in the editable source.
If the homepage is unavailable, consult specific example pages or their linked
source downloads; report access limits accurately. Adapt the techniques to the
diagram's physical model and established notation.

Examples consulted for the Tennessee Eastman drawing:

- [Laminar and turbulent flow](https://tikz.net/fluid_dynamics_laminar/): reusable
  visual styles, rounded paths and material rendering.
- [Torricelli's experiment and barometers](https://tikz.net/fluid_dynamics_barometer/):
  explicit pipe arcs, rounded line ends and anchored labels.
- [Mechanics branches chart](https://tikz.net/mechanics/): named coordinates and
  separately positioned annotations.

## Tennessee Eastman preferences

The user approved the natural industrial palette on 2026-11-06. Use that palette
when making subsequent layout refinements to `13-tennessee-eastman.tex`.

- Use a consistent type hierarchy: 9 pt equipment titles and 8 pt annotations,
  signal labels and stream numbers. The confined compressor nameplate uses
  7.5 pt text. Give text visible clearance from vessels and pipes.
- Draw unmarked, continuous T-junctions without filled connection dots. Keep the
  numbered stream labels and the white bridge indicating an unconnected crossing.
- Round elbows modestly, but never round away a real T-junction. Keep arrowheads
  on straight pipe segments, clear of valves, bends and junctions.
- Share coordinates between equipment ports, pipe centre lines and valve centres.
  Connect actuator stems to a closed actuator base without a gap.

## Verification and derived files

Compile the changed source, inspect its log and rendered page, then update the
corresponding PDF/PNG, complete atlas, documentation copies and build hashes.
Run `python tools/build_benchmark_atlas.py --check`,
`python tools/build_api_docs.py --check`, and `git diff --check`.
Keep source geometry and signal assignments consistent with the process model.
