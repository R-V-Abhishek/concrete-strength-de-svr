"""Verify the frozen report evidence and reproduce selected-model metrics."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from concrete_strength.data import TARGET_COLUMN, compute_sha256, load_processed_data
from concrete_strength.evaluation import compute_metrics, evaluate_hyperparameters
from concrete_strength.search import evaluate_selected_on_holdout
from concrete_strength.stage2 import provenance


def recorded_checksum(path: Path, expected: str) -> str:
    """Match original bytes, or explicitly recorded Windows text line endings.

    Git can convert LF/CRLF text during checkout. Only known text formats may
    be compared this way; binary source data must match byte for byte.
    """
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() == expected:
        return "exact"
    if path.suffix in (".json", ".csv", ".lock", ".py"):
        lf = content.replace(b"\r\n", b"\n")
        if hashlib.sha256(lf).hexdigest() == expected:
            return "LF text checkout"
        if hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest() == expected:
            return "CRLF text checkout"
    raise ValueError(f"Changed evidence content (not a line-ending difference): {path}")


def verify_evidence(output_path: Path = Path("results/final/verification.json")) -> None:
    """Check all saved evidence; refit five selections without changing results.

    Cross-environment metric tolerance is fixed at 0.001. Saved prediction
    rounding is checked separately with a 0.0002 tolerance. Failed checks abort
    before writing a successful verification record.
    """
    def read(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    final_path = Path("results/final/final_results.json")
    final = read(final_path)
    de = read("results/de/de_search_results.json")
    random = read("results/baseline/random_search_results.json")
    baseline = read("results/baseline/default_baseline.json")
    config = read("configs/experiment.json")
    df, manifest = load_processed_data("data/processed/concrete_cleaned.csv",
                                       "data/processed/splits_manifest.json")
    checksum_checks = {}
    for name, expected in final["input_sha256"].items():
        path = Path(name.replace("\\", "/"))
        checksum_checks[str(path)] = recorded_checksum(path, expected)
    original_hashes = {name.replace("\\", "/"): digest
                       for name, digest in final["provenance"]["sha256"].items()}
    for name in ("data/raw/Concrete_Data.xls", "data/processed/concrete_cleaned.csv",
                 "data/processed/splits_manifest.json", "configs/experiment.json", "uv.lock"):
        checksum_checks[name] = recorded_checksum(Path(name), original_hashes[name])
    assert compute_sha256("data/raw/Concrete_Data.xls") == "710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4"

    dev, test = set(manifest["development_indices"]), set(manifest["holdout_indices"])
    groups = df["group_id"].to_numpy()
    assert len(dev) == 826 and len(test) == 204
    assert not dev.intersection(test) and dev.union(test) == set(range(len(df)))
    assert not set(groups[list(dev)]).intersection(groups[list(test)])
    for fold in manifest["cv_folds"]:
        train, val = set(fold["train_indices"]), set(fold["val_indices"])
        assert not train.intersection(val) and train.union(val) == dev
        assert not set(groups[list(train)]).intersection(groups[list(val)])

    csv = pd.read_csv("results/final/metrics.csv")
    selected = {run["seed"]: run for run in final["runs"]}
    actuals = df.iloc[manifest["holdout_indices"]][TARGET_COLUMN].to_numpy()
    summary_checks = {}
    reproduction = []
    for method, runs in (("de", de["runs"]), ("random_search", random["runs"])):
        assert [r["seed"] for r in runs] == config["de"]["seeds"]
        holdout_metrics = []
        for run in runs:
            history = run["history"]
            assert run["budget"] == run["total_evaluations"] == len(history) == 300
            assert [h["call_index"] for h in history] == list(range(1, 301))
            means = [h["mean_cv_rmse"] for h in history]
            np.testing.assert_allclose([h["best_so_far_rmse"] for h in history],
                                       np.minimum.accumulate(means), atol=0.0001, rtol=0)
            assert run["best_cv_rmse"] == min(means)
            first_best = min(history, key=lambda entry: entry["mean_cv_rmse"])
            assert run["best_log_params"] == first_best["log_params"]
            assert run["best_decoded_params"] == first_best["decoded_params"]
            for entry in history:
                assert len(entry["fold_rmses"]) == 5
                np.testing.assert_allclose(entry["mean_cv_rmse"], np.mean(entry["fold_rmses"]),
                                           atol=0.0001, rtol=0)
                for position, name in zip(entry["log_params"], ("log_C", "log_gamma", "log_epsilon"), strict=True):
                    assert config["search_space"][name][0] <= position <= config["search_space"][name][1]
            if method == "de":
                saved = selected[run["seed"]]
                assert saved["history"] == history
                assert saved["best_decoded_params"] == run["best_decoded_params"]
                assert saved["best_cv_rmse"] == run["best_cv_rmse"]
                np.testing.assert_allclose(saved["holdout_actuals"], actuals, atol=1e-10)
                metrics = saved["holdout_metrics"]
                predictions = saved["holdout_predictions"]
                np.testing.assert_allclose(saved["residuals"], actuals - predictions, atol=0.0001)
                fitted = evaluate_selected_on_holdout(df, manifest["development_indices"],
                    manifest["holdout_indices"], run["best_decoded_params"])["holdout_metrics"]
                cv, _ = evaluate_hyperparameters(*run["best_log_params"], df, manifest["cv_folds"])
                delta = {metric: abs(fitted[metric] - metrics[metric]) for metric in metrics}
                assert max(delta.values()) <= 0.001, (run["seed"], delta)
                assert abs(cv - run["best_cv_rmse"]) <= 0.001, (run["seed"], cv)
                reproduction.append({"seed": run["seed"], "holdout_metrics": fitted,
                    "holdout_absolute_differences": delta, "cv_rmse": cv,
                    "cv_absolute_difference": abs(cv-run["best_cv_rmse"])})
            else:
                metrics = run["holdout_evaluation"]["holdout_metrics"]
                predictions = run["holdout_evaluation"]["holdout_predictions"]
            recalculated = compute_metrics(actuals, predictions)
            for metric in metrics:
                assert abs(recalculated[metric] - metrics[metric]) <= 0.0002, (method, run["seed"], metric)
            label = "DE" if method == "de" else "RandomSearch"
            row = csv[(csv["method"] == label) & (csv["seed"] == run["seed"])]
            assert len(row) == 1
            for metric in metrics:
                np.testing.assert_allclose(row.iloc[0][metric], metrics[metric], atol=1e-10)
            holdout_metrics.append(metrics)
        for metric in ("rmse", "mae", "r2"):
            values = [m[metric] for m in holdout_metrics]
            expected = final["comparison"][method]["holdout"][metric]
            assert round(float(np.mean(values)), 4) == expected["mean"]
            assert round(float(np.std(values, ddof=1)), 4) == expected["std"]
        vals = [r["best_cv_rmse"] for r in runs]
        assert round(float(np.mean(vals)), 4) == final["comparison"][method]["validation"]["mean"]
        assert round(float(np.std(vals, ddof=1)), 4) == final["comparison"][method]["validation"]["std"]
        summary_checks[method] = final["comparison"][method]

    assert len(csv) == 10
    assert final["comparison"]["default_svr"]["holdout"] == baseline["default_svr"]["holdout_metrics"]
    for key, value in compute_metrics(actuals, baseline["default_svr"]["holdout_predictions"]).items():
        assert abs(value - baseline["default_svr"]["holdout_metrics"][key]) <= 0.0002
    demo = min(final["runs"], key=lambda r: (r["best_cv_rmse"], r["optimizer"], r["seed"]))
    assert final["demonstration"] == demo
    assert final["holdout_used_for_selection"] is False

    previous = [set(), set(), set()]
    curve = final["learning_curve_development_only"]
    assert [row["fraction"] for row in curve] == [0.25, 0.5, 0.75, 1.0]
    curve_csv = pd.read_csv("results/final/learning_curve.csv")
    assert len(curve_csv) == len(curve)
    for number, row in enumerate(curve):
        for key, value in row.items():
            if key != "folds":
                np.testing.assert_allclose(curve_csv.iloc[number][key], value, atol=1e-10)
        assert len(row["folds"]) == 3
        for fold in row["folds"]:
            train, val = set(fold["training_indices"]), set(fold["validation_indices"])
            assert train.union(val).issubset(dev) and not train.intersection(val)
            train_groups, val_groups = set(groups[list(train)]), set(groups[list(val)])
            assert not train_groups.intersection(val_groups)
            assert fold["training_group_count"] == len(train_groups)
            assert previous[fold["fold"]].issubset(train)
            previous[fold["fold"]] = train
            for group in train_groups:
                assert set(np.flatnonzero(groups == group)).issubset(train)
            if row["fraction"] == 1.0:
                assert train.union(val) == dev
        for prefix, field in (("train_rmse", "train_rmse"), ("rmse", "validation_rmse")):
            values = [f[field] for f in row["folds"]]
            assert row[prefix+"_mean"] == round(float(np.mean(values)), 4)
            assert row[prefix+"_std"] == round(float(np.std(values, ddof=1)), 4)

    report = {
        "status": "passed", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": ["original data/config/input checksums", "holdout and CV group isolation",
                   "all 3000 candidate records and budgets", "validation-only demonstration selection",
                   "all saved prediction metrics and CSV rows", "aggregate means and sample SDs",
                   "nested whole-group three-fold learning curve", "five selected-model CV/holdout refits"],
        "cross_environment_tolerance": 0.001, "saved_prediction_rounding_tolerance": 0.0002,
        "historical_checksum_checks": checksum_checks,
        "selected_model_reproduction": reproduction, "comparison": summary_checks,
        "provenance": provenance(Path("configs/experiment.json"),
                                 Path("data/processed/concrete_cleaned.csv"),
                                 Path("data/processed/splits_manifest.json")),
        "verifier_sha256": compute_sha256(Path(__file__)),
        "stage3_sha256": compute_sha256(Path("src/concrete_strength/stage3.py")),
        "evidence_sha256": {str(path): compute_sha256(path) for path in sorted(Path("results/final").iterdir())
                            if path.is_file() and path.name not in (output_path.name, "SHA256SUMS")},
    }
    output_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Evidence verification passed; saved {output_path}")
