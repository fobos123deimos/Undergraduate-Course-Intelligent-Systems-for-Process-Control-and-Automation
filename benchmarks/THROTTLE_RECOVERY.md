# Original throttle measurements: recovery and evaluation

On 2026-11-04, the exact original download address was recovered from the GMA/TU Dortmund benchmark page archived on [2015-07-24](https://web.archive.org/web/20150724223059/http://www.rst.e-technik.tu-dortmund.de:80/cms/de/Veranstaltungen/GMA-Fachausschuss/Benchmark/index.html). Its [2019-12-09 capture](https://web.archive.org/web/20191209193343/http://www.rst.e-technik.tu-dortmund.de:80/cms/de/Veranstaltungen/GMA-Fachausschuss/Benchmark/index.html) links the same file:

`http://www.rst.e-technik.tu-dortmund.de/cms/Medienpool/Downloads/Veranstaltungen/GMA-Fachausschuss/Benchmark/Throttle.zip`

**The archive's measurements were not recovered.** The live HTTP address returns department-homepage HTML after redirecting, despite HTTP status 200. HTTPS failed its SSL connection during this check. The public Wayback index returned no capture for the exact ZIP or its original benchmark download directory; its availability API also returned an empty archive record. These observations concern the checked addresses and date, not proof that every possible copy is lost. Full dated checks are in [throttle_recovery.json](throttle_recovery.json).

The [2014 author chapter](https://www.ksp.kit.edu/books/1123/files/917e2990-49e8-4674-bb3e-7b40e418865d.pdf), by Salman Zaidi and Andreas Kroll, describes the same benchmark. It appears in the proceedings of the 24th Workshop Computational Intelligence, pp. 173–186. The review's sections 3.4 and 4.1 specify the measurement and evaluation protocol. Published figures and descriptions do not replace the raw time series.

## Additional public routes checked

| Route | Observed result |
|---|---|
| [Current TU Dortmund datasets](https://rst.etit.tu-dortmund.de/forschung/datensaetze/) | No throttle download listed; current listed data concern other applications |
| [Kassel MRT research-data collection](https://daks.uni-kassel.de/collections/488b8783-e3be-4fbf-a724-ee8e8d71a853) | Its public collection API returned seven deposits, none concerning throttle measurements |
| [Kassel MRT software directory](https://www.uni-kassel.de/maschinenbau/institute/analyse-und-regelung-technischer-systeme/mess-und-regelungstechnik/forschung/software-projekte.html) | Links the official MRT-RT GitHub account and a TS toolbox |
| [TS toolbox access page](https://www.uni-kassel.de/maschinenbau/institute/analyse-und-regelung-technischer-systeme/mess-und-regelungstechnik/forschung/software-projekte/ts-toolbox.html) | Explicit manual download permission is required; public package access was not available |
| [Later coauthor's public SysID code](https://github.com/arehmer/LPV_SysID) and [ICSTCC 2022 code](https://github.com/arehmer/ICSTCC_2022) | Public file trees contain other benchmark data; no throttle data path was found |
| [Later GRU throttle experiment](https://ifatwww.et.uni-magdeburg.de/ifac2020/media/pdfs/3208.pdf) | Different experiment: about 1000 multisine records and two 2500-record APRBS sequences, different splitting/scaling; not a substitute for the review's records |

No author was contacted and no manual-access restriction was bypassed. The archive's license is unknown until its contents or a provider's permission become available. Third-party source files and measured traces should remain under ignored `benchmarks/external/` until redistribution rights are established.

## Ready-to-run protocol

The Python and MATLAB/Octave runners consume the same explicit manifest and CSV format. Copy [throttle_manifest.template.json](throttle_manifest.template.json) into the local directory containing the recovered original archive. Fill in actual SHA-256 digests, member/variable provenance, license notes, and the precise conversion from original records. Missing metadata and placeholder digests are rejected.

Each CSV must have `time_s,duty_percent,angle_deg` columns. Supply the whole multisine training experiment with 10000 records and the separate quasi-APRBS test experiment with 2500 records, sampled every 0.01 seconds. Preserve original order and measurement units; do not interpolate, smooth, randomly split, or concatenate the experiments. If the source lacks timestamps, state explicitly that the time column was constructed from its documented sampling period. If it uses different units, document the actual calibration/conversion, without estimating it from test performance.

```sh
python benchmarks/run_throttle_reference.py --manifest benchmarks/external/throttle/manifest.json --output benchmarks/external/throttle/evaluation-python
```

```matlab
addpath('matlab');
report = run_throttle_reference( ...
    'benchmarks/external/throttle/manifest.json', ...
    'benchmarks/external/throttle/evaluation-matlab');
```

Both runners verify source/CSV hashes, experiment lengths and timestamps, then fit eight local ARX models using training data only. For a measured candidate, they also inspect the ZIP directory and require each declared original member to exist. A filename, HTTP success response, or bare `PK` signature does not suffice. The portable MATLAB/Octave archive parser accepts classic ZIP; ZIP64, multipart archives and non-UTF8 extended filenames are explicitly unsupported. For a MAT file containing both experiments, name the same archive member and record the distinct variable selections in the conversion notes.

Each independent experiment seeds its first two measured outputs; those samples are excluded from the scores. One-step prediction uses observed output history. Free-run prediction uses only its two initial measured seeds and subsequent predictions. Outputs include all fitted coefficients/partitions, per-experiment one-step and free-run RMSE in degrees, maximum absolute error, fit percentage, and prediction traces. Existing output directories are rejected to prevent stale evidence being mistaken for a new run.

The crisp and soft variants use the repository's educational nearest-center/inverse-distance partitions. They are **not** the publication's fitted polyhedral PWA partition or fuzzy-c-means/optimized TS solution. Python and MATLAB use their native seeded random initializations, so independently fitted parameters may differ. Passing the file contract establishes data integrity, not historical authenticity. Reports retain `paper_table_11_reproduced: false` and `historical_source_authenticity_verified_by_this_runner: false`. The original archive, its documentation and the identification method must be reviewed before making either stronger claim.

## Fixture validation

The integration fixture is generated from a known stable second-order recurrence. It has the exact required record counts and time spacing but contains **no measured throttle data**. It requires explicit opt-in and produces `executed_synthetic_fixture` reports:

```sh
python benchmarks/run_throttle_reference.py --make-fixture benchmarks/external/throttle-fixture
python benchmarks/run_throttle_reference.py --manifest benchmarks/external/throttle-fixture/manifest.json --output benchmarks/external/throttle-fixture/python-result --allow-synthetic-fixture
python -m pytest tests/test_throttle_reference.py -q
```

```matlab
addpath('matlab');
report = run_throttle_reference( ...
    'benchmarks/external/throttle-fixture/manifest.json', ...
    'benchmarks/external/throttle-fixture/matlab-result', true);
assert(strcmp(report.status, 'executed_synthetic_fixture'));
assert(report.models.soft.experiments.test.free_run.scored_samples == 2498);
assert(report.models.soft.experiments.test.free_run.rmse_deg < 1e-5);
```

For native MATLAB or Octave CI, the independent fixture validator creates both synthetic experiments itself and needs no Python process or external download:

```matlab
addpath('matlab');
report = validate_throttle_reference(fullfile('ci-artifacts','throttle-native'));
assert(report.fixture_checks_passed);
```

Omit the argument to use a fresh temporary directory. The Python and Octave executions on the same Python-created fixture are recorded in [Python fixture evidence](results/throttle-fixture-python.json) and [Octave fixture evidence](results/throttle-fixture-octave.json). These files contain artificial-data metrics, never the publication's measurement scores.

Fixture checks cover changed source bytes, HTML or a truncated `PK` response masquerading as the archive, absent declared archive members, corrupted timestamps despite refreshed checksums, path escape, train-only preprocessing, recursive independence from future measured outputs, and exclusion of seed samples from scores. Numerical fixture accuracy checks the importer and evaluation flow; it does not close the original-data access gap or establish the throttle model's physical accuracy.

What remains externally required is the actual original `Throttle.zip` (or an authenticated equivalent with the same experiments), its terms and channel/unit documentation. Matching Table 11 additionally requires the publication's identification procedure and fitted partition/parameter details; merely recovering a file with the right number of rows would not establish that match.

The full-size artificial workflow also passed native MATLAB R2025b Update 7 in [run 41896147563](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41896147563). Its [fixture report](results/throttle-fixture-matlab.json) remains explicitly synthetic; it is not a recovered measurement score.
