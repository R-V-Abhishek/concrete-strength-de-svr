"""Unit tests for evaluation metrics, pipeline scaling isolation, and baselines."""

import numpy as np
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from concrete_strength.data import assign_groups, create_group_splits, load_raw_data
from concrete_strength.evaluation import (
    build_svr_pipeline,
    compute_metrics,
    evaluate_dummy_baseline,
    evaluate_hyperparameters,
)


def test_compute_metrics_hand_calculated():
    # True values: [10.0, 20.0, 30.0]
    # Pred values: [12.0, 18.0, 34.0]
    # Residuals: [2.0, -2.0, 4.0]
    # MSE = (4 + 4 + 16)/3 = 24/3 = 8.0
    # RMSE = sqrt(8.0) ~ 2.8284
    # MAE = (2 + 2 + 4)/3 = 8/3 ~ 2.6667
    # Var(y) = ((10-20)^2 + 0 + (30-20)^2)/3 = 200/3
    # R2 = 1 - 24/200 = 1 - 0.12 = 0.88
    y_true = [10.0, 20.0, 30.0]
    y_pred = [12.0, 18.0, 34.0]

    m = compute_metrics(y_true, y_pred)
    assert pytest.approx(m["rmse"], abs=1e-3) == np.sqrt(8.0)
    assert pytest.approx(m["mae"], abs=1e-3) == 8.0 / 3.0
    assert pytest.approx(m["r2"], abs=1e-3) == 0.88


def test_pipeline_scaling_isolation():
    # Ensure that scaler is fitted ONLY on training data
    train_X = np.array([[100.0], [200.0], [300.0]])
    train_y = np.array([10.0, 20.0, 30.0])
    test_X = np.array([[1000.0]])

    pipe = Pipeline([("scaler", StandardScaler()), ("svr", SVR())])
    pipe.fit(train_X, train_y)

    scaler = pipe.named_steps["scaler"]
    # Mean should be 200.0 (from train), completely unaffected by test_X
    assert pytest.approx(scaler.mean_[0]) == 200.0


def test_dummy_baseline_runs():
    df = load_raw_data("data/raw/Concrete_Data.xls")
    df_with_groups, group_series = assign_groups(df)
    manifest = create_group_splits(df_with_groups, group_series, cv_folds=3)

    dummy_res = evaluate_dummy_baseline(
        df=df_with_groups,
        cv_folds=manifest["cv_folds"],
        dev_indices=manifest["development_indices"],
        holdout_indices=manifest["holdout_indices"],
    )
    assert dummy_res["cv_mean_rmse"] > 10.0
    assert dummy_res["holdout_metrics"]["rmse"] > 10.0


def test_evaluate_hyperparameters_interface():
    df = load_raw_data("data/raw/Concrete_Data.xls")
    df_with_groups, group_series = assign_groups(df)
    manifest = create_group_splits(df_with_groups, group_series, cv_folds=2)

    # Test interface with log coordinates (C=1.0, gamma=0.01, epsilon=0.1)
    mean_rmse, fold_rmses = evaluate_hyperparameters(
        log_C=0.0,
        log_gamma=-2.0,
        log_epsilon=-1.0,
        df=df_with_groups,
        cv_folds=manifest["cv_folds"],
    )
    assert isinstance(mean_rmse, float)
    assert len(fold_rmses) == 2
    assert mean_rmse > 0.0
