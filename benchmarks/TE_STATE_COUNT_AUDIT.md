# Tennessee Eastman: continuous-state count audit

On 5 November 2026, the diagram review found that the archived revised Tennessee Eastman **plant has 50 continuous states**. Earlier repository descriptions and the native report said 52 because the runner assigned that number directly. This is an editorial and reporting correction; no simulator equations, historical trajectories or execution dates were changed, and this review is not a new simulation run.

## Source and executable evidence

The [provider's archive](https://depts.washington.edu/control/LARRY/TE/temexd_mod.zip) is pinned by [external_sources.json](external_sources.json). The inspected file is `temexd_mod/temexd_mod.c`, SHA-256:

```text
eff57b75700e7472005785150c21f82b0c3d178ebceebe37e532794f23785aba
```

That hash matches `source_c_sha256` in every preserved [native report](results/te-native/validation.json). Line numbers refer to that exact, unmodified third-party source.

| Location | Evidence | Meaning |
|---|---|---|
| Line 145 | Parameter documentation says “Vector of 52 initial states” | Inconsistent prose; it does not determine the allocated state vector. |
| Line 181 | State inventory is headed `States (50)` | The inventory enumerates 50 plant states. |
| Line 845 | `const integer NX = 50;` | Executable plant dimension. |
| Line 1107 | `Plen[0] = NX;` | Initial-condition parameter length follows `NX`. |
| Line 1171 | `ssSetNumContStates(S, NX);` | The S-function registers 50 continuous plant states. |
| Line 1268 | `real_T dxdt[50];` | Derivative storage has 50 entries. |

The 2014 survey also describes 50 original states. The archived revised source changes numerical and disturbance handling; it does not establish a two-state expansion. Optional extra measured/diagnostic outputs and states of an external controller are separate quantities. No conclusion about another simulator revision follows from this audit.

## Runner and preserved results

Previously, [run_te_reference.m](run_te_reference.m) wrote `'continuous_states',52` without inspecting the plant declaration. It passed an empty initial-state parameter, allowing the S-function's own initialization, and checked the 41 measurement and 12 command channels. The metadata error does not show that 52 plant states were executed.

The runner now normalizes legacy non-ASCII unit-comment bytes for inspection, removes C comments, finds the unique executable `NX` declaration, checks that `ssSetNumContStates` uses it, and requires the audited value 50. This parsing step does not alter the compiled source file. A changed or ambiguous declaration stops the run for a source review. The report records this derived plant count and its basis.

The three `continuous_states` values in `results/te-native/validation.json` were corrected to 50. An `editorial_corrections` entry records the former value, evidence lines and source hash. All numerical result fields, source hashes, original execution metadata and CSV bytes are preserved. Original externally published workflow artifacts may still contain the old metadata; their execution record has not been rewritten.

Eight checks passed on 5 November 2026 using the exact local MATLAB parser function in GNU Octave 11.3.0: the pinned C file, the inconsistent documentation comment, extra commented-out declarations, missing/duplicate declarations, an unexpected 52-state declaration and an inconsistent S-function registration. These are offline source checks and do not require or establish a new MATLAB/Simulink execution. A semantic comparison with the previous report confirmed that only the documented state-count metadata changed; all three CSV files were also checked byte for byte against the previous committed versions.
