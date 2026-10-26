"""Integration tests for Stage 1 outputs and end-to-end verification."""

import json
from pathlib import Path
import pytest

from concrete_strength.data import load_processed_data


def test_processed_files_exist_and_valid():
    csv_path = Path("data/processed/concrete_cleaned.csv")
    manifest_path = Path("data/processed/splits_manifest.json")

    assert csv_path.exists(), "Processed data CSV does not exist"
    assert manifest_path.exists(), "Splits manifest JSON does not exist"

    df, manifest = load_processed_data(csv_path, manifest_path)
    assert len(df) == 1030
    assert manifest["total_samples"] == 1030
    assert manifest["num_cv_folds"] == 5
    assert len(manifest["cv_folds"]) == 5
    assert len(manifest["holdout_indices"]) == 204
    assert len(manifest["development_indices"]) == 826


def test_default_baseline_output_schema():
    baseline_path = Path("results/baseline/default_baseline.json")
    assert baseline_path.exists(), "Default baseline JSON not found"

    with baseline_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert "dummy" in data
    assert "default_svr" in data

    dummy = data["dummy"]
    assert "cv_mean_rmse" in dummy
    assert "holdout_metrics" in dummy
    assert dummy["holdout_metrics"]["rmse"] > 14.0

    svr = data["default_svr"]
    assert "cv_metrics" in svr
    assert "holdout_metrics" in svr
    assert svr["holdout_metrics"]["rmse"] < dummy["holdout_metrics"]["rmse"]
    assert svr["holdout_metrics"]["r2"] > 0.50
