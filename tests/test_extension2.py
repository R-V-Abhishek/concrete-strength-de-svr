import json
from pathlib import Path

import numpy as np
import pytest

from concrete_strength.data import FEATURE_SETS, add_engineered_features, create_group_splits, load_processed_data
from concrete_strength.evaluation import evaluate_ard_cv, evaluate_svr_cv

DATA, MANIFEST = Path("data/processed/concrete_cleaned.csv"), Path("data/processed/splits_manifest.json")


@pytest.fixture(scope="module")
def prepared():
    df, manifest = load_processed_data(DATA, MANIFEST)
    return add_engineered_features(df), manifest


def test_ard_with_equal_gammas_matches_isotropic_rbf(prepared):
    df, manifest = prepared
    columns = FEATURE_SETS["log_age"]
    shared = evaluate_svr_cv(df, manifest["cv_folds"], 30.0, 0.1, 0.5, columns)
    ard, fold_rmses = evaluate_ard_cv(df, manifest["cv_folds"], 30.0, [0.1] * len(columns), 0.5, columns)
    assert ard == pytest.approx(shared["mean_cv_rmse"], abs=2e-4)
    assert len(fold_rmses) == 5


def test_ard_gammas_change_the_model(prepared):
    df, manifest = prepared
    columns = FEATURE_SETS["log_age"]
    gammas = [0.1] * len(columns)
    gammas[-1] = 1.0
    changed, _ = evaluate_ard_cv(df, manifest["cv_folds"], 30.0, gammas, 0.5, columns)
    equal, _ = evaluate_ard_cv(df, manifest["cv_folds"], 30.0, [0.1] * len(columns), 0.5, columns)
    assert changed != equal


def test_replication_splits_are_group_disjoint_and_differ_from_original(prepared):
    df, manifest = prepared
    split = create_group_splits(df, df["group_id"], 0.20, 101, 5)
    groups = df["group_id"].to_numpy()
    assert not set(groups[split["development_indices"]]) & set(groups[split["holdout_indices"]])
    assert split["development_samples"] + split["holdout_samples"] == len(df)
    assert set(split["holdout_indices"]) != set(manifest["holdout_indices"])
    for fold in split["cv_folds"]:
        assert not set(groups[fold["train_indices"]]) & set(groups[fold["val_indices"]])


def test_extension2_ard_evidence_consistent(prepared):
    """E2a: 20 runs of 1,500 calls, in bounds, best CV equals the history minimum, metrics match predictions."""
    df, manifest = prepared
    search = json.load(open("results/extension2/ard_search.json"))
    results = json.load(open("results/extension2/ard_results.json"))
    assert results["holdout_used_for_selection"] is False and len(search["runs"]) == len(results["runs"]) == 20
    actual = df["compressive_strength"].to_numpy()[manifest["holdout_indices"]]
    for run in search["runs"]:
        assert run["total_evaluations"] == 1500
        assert run["best_cv_rmse"] == min(h["mean_cv_rmse"] for h in run["history"])
        for h in run["history"]:
            p = h["log_params"]
            assert len(p) == (10 if run["space"] == "ard" else 3)
            if run["space"] == "ard":
                assert -2 <= p[0] <= 4 and -3 <= p[1] <= 1 and all(-5 <= g <= 1 for g in p[2:])
    for run in results["runs"]:
        rmse = np.sqrt(np.mean((np.asarray(run["holdout_predictions"]) - actual) ** 2))
        assert rmse == pytest.approx(run["holdout"]["rmse"], abs=2e-4)


def test_extension2_replication_evidence_consistent():
    """E2b: 50 runs of 300 calls on five splits, selections frozen before holdout, summary recomputable."""
    search = json.load(open("results/extension2/replication_search.json"))
    results = json.load(open("results/extension2/replication_results.json"))
    assert results["holdout_used_for_selection"] is False and len(search["runs"]) == len(results["runs"]) == 50
    assert all(r["total_evaluations"] == 300 and r["best_cv_rmse"] == min(h["mean_cv_rmse"] for h in r["history"])
               for r in search["runs"])
    d = [e["d_holdout"] for e in results["per_split"]]
    assert results["summary"]["new_splits_holdout"]["mean"] == pytest.approx(np.mean(d), abs=1e-3)
    assert len(d) == 5
