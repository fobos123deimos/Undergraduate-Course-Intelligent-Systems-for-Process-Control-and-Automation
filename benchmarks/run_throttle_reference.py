"""Evaluate supplied throttle experiments without confusing fixture and evidence.

The original measurements are not bundled. A manifest binds the original
archive and explicitly converted CSVs by SHA-256. Passing this contract checks
integrity, not historical authenticity or reproduction of the fitted models.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from intelligent_control.benchmarks import LocalARX, load_io_csv

ORIGINAL_URL = "http://www.rst.e-technik.tu-dortmund.de/cms/Medienpool/Downloads/Veranstaltungen/GMA-Fachausschuss/Benchmark/Throttle.zip"
COUNTS = {"train": 10000, "test": 2500}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound_file(directory, name, expected):
    """Manifest paths stay inside its directory; modified files are rejected."""
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("manifest file paths must be nonempty relative paths")
    path = (directory / name).resolve()
    if not path.is_relative_to(directory) or not path.is_file():
        raise ValueError("manifest file is absent or outside its directory")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("manifest requires an actual SHA-256, not a placeholder")
    if sha256(path) != expected:
        raise ValueError(f"SHA-256 mismatch: {name}")
    return path


def load_experiments(manifest_path, allow_synthetic=False):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported throttle manifest version")
    kind = manifest.get("dataset_kind")
    if kind not in {"measured_original_candidate", "synthetic_fixture"}:
        raise ValueError("dataset_kind must explicitly identify measured candidate or fixture")
    if kind == "synthetic_fixture" and not allow_synthetic:
        raise ValueError("synthetic fixture requires explicit --allow-synthetic-fixture")
    if manifest.get("sample_time_s") != .01 or manifest.get("units") != {
        "time_s": "s", "duty_percent": "%", "angle_deg": "deg"
    }:
        raise ValueError("required sampling is 0.01 s and units are s, %, deg")
    provenance = manifest["provenance"]
    for key in ("source_url", "source_title", "license_notes", "conversion_notes"):
        if not isinstance(provenance.get(key), str) or not provenance[key].strip():
            raise ValueError(f"missing provenance: {key}")
    source = bound_file(manifest_path.parent, provenance["source_file"], provenance["source_sha256"])
    members = None
    if kind == "measured_original_candidate":
        try:
            with zipfile.ZipFile(source) as archive:
                members = set(archive.namelist())
        except zipfile.BadZipFile as error:
            raise ValueError("original archive must be a valid ZIP, not HTML or a truncated PK signature") from error
    records, metadata = {}, {}
    for split, count in COUNTS.items():
        item = manifest["experiments"][split]
        if item.get("rows") != count or not isinstance(item.get("original_member"), str) or not item["original_member"].strip():
            raise ValueError(f"{split} requires {count} rows and original member provenance")
        if members is not None and item["original_member"] not in members:
            raise ValueError(f"{split} original_member is absent from the source ZIP")
        path = bound_file(manifest_path.parent, item["csv_file"], item["sha256"])
        _, inputs, output = load_io_csv(path, ["time_s", "duty_percent"], ["angle_deg"], .01)
        t, u, y = inputs[:, 0], inputs[:, 1], output[:, 0]
        if len(t) != count or not np.allclose(np.diff(t), .01, rtol=0, atol=1e-9):
            raise ValueError(f"{split} must contain {count} ordered records sampled every 0.01 s")
        records[split] = (t, u, y)
        metadata[split] = {**item, "first_time_s": float(t[0]), "last_time_s": float(t[-1]),
                           "angle_range_deg": [float(y.min()), float(y.max())],
                           "duty_range_percent": [float(u.min()), float(u.max())]}
    if metadata["train"]["sha256"] == metadata["test"]["sha256"]:
        raise ValueError("train and test must be distinct experimental files")
    # No split boundaries or data are inferred from an arbitrary joined record.
    return manifest, records, metadata


def error_metrics(measured, predicted):
    measured, predicted = np.asarray(measured)[2:], np.asarray(predicted)[2:]
    if measured.shape != predicted.shape or not np.isfinite(predicted).all():
        raise ValueError("invalid prediction")
    error = predicted - measured
    denominator = np.linalg.norm(measured - measured.mean())
    return {"scored_samples": int(len(error)), "seed_samples_excluded": 2,
            "rmse_deg": float(np.sqrt(np.mean(error ** 2))),
            "maximum_absolute_error_deg": float(np.max(np.abs(error))),
            "fit_percent": float(100 * (1 - np.linalg.norm(error) / denominator)) if denominator else None}


def evaluate(manifest_path, output_directory, allow_synthetic=False):
    manifest, records, metadata = load_experiments(manifest_path, allow_synthetic)
    output_directory = Path(output_directory)
    if output_directory.exists():
        raise FileExistsError("use a fresh output directory; old results are not validation")
    results, predictions = {}, {}
    for mode in ("crisp", "soft"):
        _, train_u, train_y = records["train"]
        model = LocalARX(rules=8, mode=mode, seed=2014).fit(train_u, train_y)
        results[mode] = {"training_mean": model.mean.tolist(), "training_scale": model.scale.tolist(),
                         "centers": model.centers.tolist(), "coefficients": model.coefficients.tolist(),
                         "experiments": {}}
        for split, (t, u, y) in records.items():
            one_step = model.predict(u, y, recursive=False)
            free_run = model.predict(u, y, recursive=True)
            results[mode]["experiments"][split] = {"one_step": error_metrics(y, one_step),
                                                    "free_run": error_metrics(y, free_run)}
            predictions[f"{mode}_{split}.csv"] = np.column_stack([t, u, y, one_step, free_run])
    report = {"status": "executed_" + manifest["dataset_kind"], "runtime": "Python " + sys.version.split()[0],
              "manifest_sha256": sha256(manifest_path), "dataset_kind": manifest["dataset_kind"],
              "provenance": manifest["provenance"], "experiments": metadata, "rules": 8,
              "sample_time_s": .01, "models": results,
              "historical_source_authenticity_verified_by_this_runner": False,
              "paper_table_11_reproduced": False,
              "method": "Teaching LocalARX fit: training-only k-means partitions, nearest-center crisp or inverse-distance soft weights, ridge 1e-8. Original fitted partitions/coefficients are not supplied.",
              "protocol": "Whole supplied experiments; no shuffled split or test fitting. Two measured seeds per experiment, excluded from scores. Free run then uses predicted outputs only."}
    output_directory.mkdir(parents=True)
    for name, values in predictions.items():
        np.savetxt(output_directory / name, values, delimiter=",", fmt="%.17g",
                   header="time_s,duty_percent,angle_deg,one_step_deg,free_run_deg", comments="")
    (output_directory / "validation.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def make_fixture(directory):
    """Full-size artificial records exercise the contract, not the apparatus."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    source = directory / "fixture-description.txt"
    source.write_text("SYNTHETIC integration fixture. Stable second-order recursion; no measured throttle records.\n", encoding="utf-8")
    manifest = {"schema_version": 1, "dataset_kind": "synthetic_fixture", "sample_time_s": .01,
                "units": {"time_s": "s", "duty_percent": "%", "angle_deg": "deg"},
                "provenance": {"source_url": "local:synthetic-integration-fixture", "source_title": "Artificial throttle pipeline fixture",
                               "source_file": source.name, "source_sha256": sha256(source),
                               "license_notes": "Repository-authored synthetic fixture; no third-party measurements.",
                               "conversion_notes": "Generated directly as CSV; no original experiment or archive."}, "experiments": {}}
    for i, (split, count) in enumerate(COUNTS.items()):
        t = np.arange(count) * .01
        rng = np.random.default_rng(1401 + i)
        u = 50 + np.repeat(rng.uniform(-20, 20, (count + 16) // 17), 17)[:count]
        y = np.full(count, 42. + i)
        for k in range(2, count):
            y[k] = 1.2 * y[k-1] - .3 * y[k-2] + .05 * u[k-1] + 2.0
        path = directory / f"{split}.csv"
        np.savetxt(path, np.column_stack([t, u, y]), delimiter=",", fmt="%.17g", header="time_s,duty_percent,angle_deg", comments="")
        manifest["experiments"][split] = {"csv_file": path.name, "sha256": sha256(path), "rows": count,
                                           "original_member": "synthetic:" + split}
    path = directory / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-synthetic-fixture", action="store_true")
    parser.add_argument("--make-fixture", type=Path, help="create clearly labeled artificial integration records in a new directory")
    args = parser.parse_args()
    if args.make_fixture:
        print(make_fixture(args.make_fixture))
        return
    if args.manifest is None or args.output is None:
        parser.error("--manifest and --output are required for evaluation")
    report = evaluate(args.manifest, args.output, args.allow_synthetic_fixture)
    print(report["status"] + ": " + str(args.output / "validation.json"))


if __name__ == "__main__":
    main()
