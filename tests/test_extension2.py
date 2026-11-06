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
