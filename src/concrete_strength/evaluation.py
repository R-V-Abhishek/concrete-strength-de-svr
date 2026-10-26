"""Evaluation pipeline, cross-validation fitness runner, and regression metrics.

Provides fold-local scaling within an sklearn Pipeline, standard regression metrics
(RMSE, MAE, R^2), and baseline evaluators for Dummy and Default SVR models.
"""

from __future__ import annotations

import time
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from concrete_strength.data import FEATURE_COLUMNS, TARGET_COLUMN


def compute_metrics(y_true: Sequence[float] | np.ndarray, y_pred: Sequence[float] | np.ndarray) -> dict[str, float]:
    """Calculate RMSE, MAE, and R^2."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    mse = float(mean_squared_error(y_t, y_p))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_t, y_p))
    r2 = float(r2_score(y_t, y_p))

    return {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
    }


def build_svr_pipeline(
    C: float = 1.0,
    gamma: float | str = "scale",
    epsilon: float = 0.1,
) -> Pipeline:
    """Construct an sklearn Pipeline with StandardScaler and SVR.
    
    Scaling is fitted fold-locally on training data only to prevent data leakage.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "svr",
                SVR(
                    kernel="rbf",
                    C=float(C),
                    gamma=gamma if isinstance(gamma, str) else float(gamma),
                    epsilon=float(epsilon),
                ),
            ),
        ]
    )


def evaluate_svr_cv(
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
    C: float,
    gamma: float | str,
    epsilon: float,
) -> dict[str, Any]:
    """Evaluate SVR across predefined cross-validation folds."""
    X = df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y = df[TARGET_COLUMN].to_numpy(dtype=np.float64)

    fold_metrics = []
    fold_rmses = []

    start_time = time.perf_counter()
    for fold in cv_folds:
        train_idx = fold["train_indices"]
        val_idx = fold["val_indices"]

        pipeline = build_svr_pipeline(C=C, gamma=gamma, epsilon=epsilon)
        pipeline.fit(X[train_idx], y[train_idx])
        preds = pipeline.predict(X[val_idx])

        m = compute_metrics(y[val_idx], preds)
        fold_metrics.append(m)
        fold_rmses.append(m["rmse"])

    elapsed = time.perf_counter() - start_time
    mean_rmse = float(np.mean(fold_rmses))
    std_rmse = float(np.std(fold_rmses, ddof=1)) if len(fold_rmses) > 1 else 0.0

    return {
        "mean_cv_rmse": round(mean_rmse, 4),
        "std_cv_rmse": round(std_rmse, 4),
        "fold_rmses": fold_rmses,
        "fold_metrics": fold_metrics,
        "elapsed_seconds": round(elapsed, 4),
    }


def evaluate_hyperparameters(
    log_C: float,
    log_gamma: float,
    log_epsilon: float,
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
) -> tuple[float, list[float]]:
    """Decode log-parameters and compute 5-fold CV RMSE.
    
    This is the standard interface function used by Random Search and Differential Evolution.
    """
    C = float(10.0 ** log_C)
    gamma = float(10.0 ** log_gamma)
    epsilon = float(10.0 ** log_epsilon)

    res = evaluate_svr_cv(df=df, cv_folds=cv_folds, C=C, gamma=gamma, epsilon=epsilon)
    return res["mean_cv_rmse"], res["fold_rmses"]


def evaluate_dummy_baseline(
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
    dev_indices: list[int],
    holdout_indices: list[int],
) -> dict[str, Any]:
    """Evaluate DummyRegressor (mean prediction) on CV and holdout as a sanity check."""
    X = df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y = df[TARGET_COLUMN].to_numpy(dtype=np.float64)

    # 1. 5-Fold CV
    fold_rmses = []
    fold_metrics = []
    for fold in cv_folds:
        train_idx = fold["train_indices"]
        val_idx = fold["val_indices"]

        dummy = DummyRegressor(strategy="mean")
        dummy.fit(X[train_idx], y[train_idx])
        preds = dummy.predict(X[val_idx])

        m = compute_metrics(y[val_idx], preds)
        fold_metrics.append(m)
        fold_rmses.append(m["rmse"])

    # 2. Refit on entire dev set and test on holdout
    dummy_full = DummyRegressor(strategy="mean")
    dummy_full.fit(X[dev_indices], y[dev_indices])
    holdout_preds = dummy_full.predict(X[holdout_indices])
    holdout_m = compute_metrics(y[holdout_indices], holdout_preds)

    return {
        "model": "DummyRegressor(mean)",
        "cv_mean_rmse": round(float(np.mean(fold_rmses)), 4),
        "cv_std_rmse": round(float(np.std(fold_rmses, ddof=1)), 4),
        "cv_fold_rmses": fold_rmses,
        "holdout_metrics": holdout_m,
    }


def evaluate_default_svr(
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
    dev_indices: list[int],
    holdout_indices: list[int],
    C: float = 1.0,
    gamma: float | str = "scale",
    epsilon: float = 0.1,
) -> dict[str, Any]:
    """Evaluate the Default SVR model on 5-fold CV and holdout test set."""
    X = df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y = df[TARGET_COLUMN].to_numpy(dtype=np.float64)

    # 1. 5-Fold CV
    cv_res = evaluate_svr_cv(df=df, cv_folds=cv_folds, C=C, gamma=gamma, epsilon=epsilon)

    # 2. Refit on full development set and evaluate on holdout
    pipeline = build_svr_pipeline(C=C, gamma=gamma, epsilon=epsilon)
    start_time = time.perf_counter()
    pipeline.fit(X[dev_indices], y[dev_indices])
    fit_time = time.perf_counter() - start_time

    holdout_preds = pipeline.predict(X[holdout_indices])
    holdout_m = compute_metrics(y[holdout_indices], holdout_preds)

    return {
        "model": "Default RBF-SVR",
        "parameters": {
            "C": C,
            "gamma": gamma,
            "epsilon": epsilon,
        },
        "cv_metrics": {
            "mean_rmse": cv_res["mean_cv_rmse"],
            "std_rmse": cv_res["std_cv_rmse"],
            "fold_rmses": cv_res["fold_rmses"],
        },
        "holdout_metrics": holdout_m,
        "holdout_predictions": [round(float(p), 4) for p in holdout_preds],
        "holdout_actuals": [round(float(a), 4) for a in y[holdout_indices]],
        "refit_time_seconds": round(fit_time, 4),
    }
