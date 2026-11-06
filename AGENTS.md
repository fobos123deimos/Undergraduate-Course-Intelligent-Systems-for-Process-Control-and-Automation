# Diagram conventions

## User-specific quality standard for technical and professional graphics

The user expects **exceptionally rigorous, meticulous, detail-oriented,
publication-quality visual refinement**, not merely a valid render. Treat this
as an explicit acceptance criterion for diagrams, figures, schematics,
engineering illustrations, plots, and professional graphics in this repository.

- **Technical fidelity first:** preserve physical topology, actual connections,
  stream directions, units, mathematical notation, equipment identity, and
  source-to-target relationships. Do not add implied devices, connections, or
  process meaning simply to fill empty space. If a feature is illustrative,
  label it accurately.
- **Geometric precision:** connect pipes, shafts, ports and actuation symbols
  exactly; avoid disjoint endpoints, tiny hooks, kinks, non-tangent transitions,
  overhangs, doubled segments and arbitrary floating arrowheads. Make straight
  sections truly straight and use intentional smooth elbows only where needed.
  Inspect vessel-wall exits and entries at high magnification.
- **Professional visual hierarchy:** use a coherent restrained palette,
  consistent strokes, tip styles, equipment rendering, typography and spacing.
  Keep precise visual relationships among labels, their referenced geometry,
  and callouts, without needless decorations or duplicate labels.
- **Micro-spacing and legibility:** check superscripts/subscripts, punctuation,
  numbers, captions, sources, labels and symbol clearances individually.
  Ensure text never visually collides with an enclosure, valve, control marker,
  adjacent label or pipe. Give adequate whitespace without making annotations
  look disconnected from the element they describe.
- **Follow provided references faithfully:** when the user points to an existing
  element as the model (e.g., “like the condenser CW inlet”), match its
  notation, unboxed/boxed treatment, alignment, connection and spacing instead
  of inventing a different design. Preserve already-approved details while
  changing only the requested region.
- **Iterative quality assurance:** render the exact editable source, review the
  whole page and detailed crops around every changed region, check the
  neighboring elements, then correct residual visual defects. Do not treat
  compilation, successful tests, or a visually plausible first pass as proof
  of finished design.
- **Traceability and deliverables:** keep editable source and generated
  SVG/PDF/PNG or other committed outputs consistent, validate repository checks,
  report concrete commits and verification results, and distinguish source
  updates from artifact-rendering or publication steps still pending. Never
  assert an unverified image review or CI result.

Tennessee Eastman examples that define this user's expected refinement level:
the $y_{20}$ compressor label must have clean separation; the agitator motor M
must join its shaft; reactor-effluent pipe exits must start flush with the
vessel wall without S-shaped micro-kinks; utility arrows must sit on continuous
paths, not look detached; and the reactor cooling-water inlet ultimately
matches the condenser's simple unboxed “CW” notation. These choices are
specific examples of the general standard, not templates to impose on unrelated
physical systems.

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
