"""Integrity and experiment independence; fixtures are not measured data."""
from pathlib import Path
import importlib.util
import json
import zipfile

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("throttle_reference", Path(__file__).resolve().parents[1] / "benchmarks/run_throttle_reference.py")
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)


@pytest.fixture
def fixture_manifest(tmp_path):
    return reference.make_fixture(tmp_path / "artificial-records")


def test_original_protocol_and_explicit_fixture_opt_in(fixture_manifest):
    with pytest.raises(ValueError, match="explicit"):
        reference.load_experiments(fixture_manifest)
    manifest, records, _ = reference.load_experiments(fixture_manifest, True)
    assert manifest["dataset_kind"] == "synthetic_fixture"
    assert len(records["train"][0]) == 10000 and len(records["test"][0]) == 2500
    assert records["train"][0][-1] == pytest.approx(99.99)
    assert records["test"][0][-1] == pytest.approx(24.99)


def test_integrity_rejects_modified_records_and_html(fixture_manifest):
    manifest = json.loads(fixture_manifest.read_text(encoding="utf-8"))
    path = fixture_manifest.parent / "train.csv"
    path.write_bytes(path.read_bytes().replace(b"time_s", b"time_x", 1))
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        reference.load_experiments(fixture_manifest, True)
    manifest["experiments"]["train"]["sha256"] = reference.sha256(path)
    manifest["dataset_kind"] = "measured_original_candidate"
    fixture_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="ZIP"):
        reference.load_experiments(fixture_manifest)


def test_time_corruption_cannot_be_hidden_by_updating_checksum(fixture_manifest):
    manifest = json.loads(fixture_manifest.read_text(encoding="utf-8"))
    path = fixture_manifest.parent / "test.csv"
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    data[12, 0] = data[11, 0]
    np.savetxt(path, data, delimiter=",", header="time_s,duty_percent,angle_deg", comments="")
    manifest["experiments"]["test"]["sha256"] = reference.sha256(path)
    fixture_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="ordered records"):
        reference.load_experiments(fixture_manifest, True)


def test_fake_pk_and_absent_archive_member_are_rejected(fixture_manifest):
    manifest = json.loads(fixture_manifest.read_text(encoding="utf-8"))
    archive = fixture_manifest.parent / "Throttle.zip"
    archive.write_bytes(b"PK\x03\x04not-a-central-directory")
    manifest["dataset_kind"] = "measured_original_candidate"
    manifest["provenance"].update(source_file=archive.name, source_sha256=reference.sha256(archive))
    fixture_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="valid ZIP"):
        reference.load_experiments(fixture_manifest)
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("present.txt", "An artificial archive used only by this rejection test.")
    manifest["provenance"]["source_sha256"] = reference.sha256(archive)
    fixture_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="original_member is absent"):
        reference.load_experiments(fixture_manifest)


def test_parent_path_escape_is_rejected(tmp_path):
    child = tmp_path / "child"; child.mkdir()
    source = tmp_path / "secret.csv"; source.write_bytes(b"not a dataset")
    with pytest.raises(ValueError, match="outside"):
        reference.bound_file(child.resolve(), "../secret.csv", reference.sha256(source))


def test_training_independence_and_recursive_output_causality(fixture_manifest):
    _, records, _ = reference.load_experiments(fixture_manifest, True)
    _, u_train, y_train = records["train"]; _, u_test, y_test = records["test"]
    for mode in ("crisp", "soft"):
        model = reference.LocalARX(rules=8, mode=mode).fit(u_train, y_train)
        coefficients = model.coefficients.copy()
        original = model.predict(u_test, y_test, recursive=True)
        changed = y_test.copy(); changed[2:] += 80
        np.testing.assert_array_equal(original, model.predict(u_test, changed, recursive=True))
        np.testing.assert_array_equal(coefficients, model.coefficients)
        assert not np.allclose(model.predict(u_test, y_test), model.predict(u_test, changed))
        expected_z = np.column_stack([np.diff(y_train[:-1]), u_train[1:-1]])
        np.testing.assert_allclose(model.mean, expected_z.mean(axis=0))


def test_full_pipeline_scores_only_nonseed_samples(fixture_manifest, tmp_path):
    output = tmp_path / "evaluation"
    report = reference.evaluate(fixture_manifest, output, True)
    assert report["status"] == "executed_synthetic_fixture"
    assert report["paper_table_11_reproduced"] is False
    assert report["historical_source_authenticity_verified_by_this_runner"] is False
    for mode in ("crisp", "soft"):
        for split, count in reference.COUNTS.items():
            for prediction in ("one_step", "free_run"):
                metrics = report["models"][mode]["experiments"][split][prediction]
                assert metrics["scored_samples"] == count - 2
                assert metrics["rmse_deg"] < 1e-5
                assert metrics["seed_samples_excluded"] == 2
    with pytest.raises(FileExistsError, match="fresh"):
        reference.evaluate(fixture_manifest, output, True)


def test_seed_errors_are_excluded_from_metrics():
    y = np.arange(7.)
    predicted = y.copy(); predicted[:2] = -1000; predicted[2:] += 2
    metrics = reference.error_metrics(y, predicted)
    assert metrics["rmse_deg"] == 2 and metrics["scored_samples"] == 5
