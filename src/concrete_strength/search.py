"""Equal-budget Random Search baseline for SVR hyperparameter optimization.

Uniformly samples hyperparameters in the shared 3D log-parameter space:
  - log10(C) in [-2.0, 4.0]
  - log10(gamma) in [-5.0, 1.0]
  - log10(epsilon) in [-3.0, 1.0]
Under the exact same evaluation budget (300 calls per seed) and folds as DE.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import pandas as pd

from concrete_strength.data import FEATURE_COLUMNS, TARGET_COLUMN
from concrete_strength.evaluation import (
    build_svr_pipeline,
    compute_metrics,
    evaluate_hyperparameters,
)

DEFAULT_BOUNDS: dict[str, tuple[float, float]] = {
    "log_C": (-2.0, 4.0),
    "log_gamma": (-5.0, 1.0),
    "log_epsilon": (-3.0, 1.0),
}


def sample_log_hyperparameters(
    rng: np.random.Generator,
    bounds: dict[str, tuple[float, float]] | None = None,
) -> tuple[float, float, float]:
    """Sample one coordinate (log_C, log_gamma, log_epsilon) uniformly within bounds."""
    b = bounds or DEFAULT_BOUNDS
    log_c = float(rng.uniform(b["log_C"][0], b["log_C"][1]))
    log_gamma = float(rng.uniform(b["log_gamma"][0], b["log_gamma"][1]))
    log_eps = float(rng.uniform(b["log_epsilon"][0], b["log_epsilon"][1]))
    return log_c, log_gamma, log_eps


def run_random_search_single_seed(
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
    seed: int,
    budget: int = 300,
    bounds: dict[str, tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Execute random search for a single seed with exact call budget accounting."""
    b = bounds or DEFAULT_BOUNDS
    rng = np.random.default_rng(seed)

    best_cv_rmse = float("inf")
    best_log_params: tuple[float, float, float] | None = None
    best_fold_rmses: list[float] = []

    history = []
    start_total = time.perf_counter()

    for call_idx in range(1, budget + 1):
        t0 = time.perf_counter()
        log_c, log_gamma, log_eps = sample_log_hyperparameters(rng, b)
        mean_rmse, fold_rmses = evaluate_hyperparameters(
            log_C=log_c,
            log_gamma=log_gamma,
            log_epsilon=log_eps,
            df=df,
            cv_folds=cv_folds,
        )
        call_time = time.perf_counter() - t0

        if mean_rmse < best_cv_rmse:
            best_cv_rmse = mean_rmse
            best_log_params = (log_c, log_gamma, log_eps)
            best_fold_rmses = fold_rmses

        history.append({
            "call_index": call_idx,
            "log_params": [round(log_c, 5), round(log_gamma, 5), round(log_eps, 5)],
            "decoded_params": {
                "C": round(float(10.0 ** log_c), 5),
                "gamma": round(float(10.0 ** log_gamma), 6),
                "epsilon": round(float(10.0 ** log_eps), 5),
            },
            "mean_cv_rmse": round(mean_rmse, 4),
            "fold_rmses": [round(r, 4) for r in fold_rmses],
            "best_so_far_rmse": round(best_cv_rmse, 4),
            "elapsed_seconds": round(call_time, 4),
        })

    total_time = time.perf_counter() - start_total

    assert best_log_params is not None
    best_c = float(10.0 ** best_log_params[0])
    best_gamma = float(10.0 ** best_log_params[1])
    best_eps = float(10.0 ** best_log_params[2])

    return {
        "optimizer": "RandomSearch",
        "seed": seed,
        "budget": budget,
        "total_evaluations": len(history),
        "total_runtime_seconds": round(total_time, 2),
        "best_log_params": [round(p, 5) for p in best_log_params],
        "best_decoded_params": {
            "C": round(best_c, 5),
            "gamma": round(best_gamma, 6),
            "epsilon": round(best_eps, 5),
        },
        "best_cv_rmse": round(best_cv_rmse, 4),
        "best_fold_rmses": [round(r, 4) for r in best_fold_rmses],
        "history": history,
    }


def evaluate_selected_on_holdout(
    df: pd.DataFrame,
    dev_indices: list[int],
    holdout_indices: list[int],
    decoded_params: dict[str, float],
) -> dict[str, Any]:
    """Refit the validation-selected candidate on the full development set and evaluate on holdout."""
    X = df[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y = df[TARGET_COLUMN].to_numpy(dtype=np.float64)

    pipeline = build_svr_pipeline(
        C=decoded_params["C"],
        gamma=decoded_params["gamma"],
        epsilon=decoded_params["epsilon"],
    )

    t0 = time.perf_counter()
    pipeline.fit(X[dev_indices], y[dev_indices])
    fit_time = time.perf_counter() - t0

    preds = pipeline.predict(X[holdout_indices])
    metrics = compute_metrics(y[holdout_indices], preds)

    return {
        "holdout_metrics": metrics,
        "refit_time_seconds": round(fit_time, 4),
        "holdout_predictions": [round(float(p), 4) for p in preds],
    }


def run_random_search_multi_seeds(
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
    dev_indices: list[int],
    holdout_indices: list[int],
    seeds: list[int],
    budget: int = 300,
    bounds: dict[str, tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Run random search across multiple seeds and evaluate validation-best candidates on holdout."""
    runs = []
    all_best_val_rmses = []
    all_holdout_rmses = []

    for seed in seeds:
        res = run_random_search_single_seed(
            df=df,
            cv_folds=cv_folds,
            seed=seed,
            budget=budget,
            bounds=bounds,
        )
        holdout_eval = evaluate_selected_on_holdout(
            df=df,
            dev_indices=dev_indices,
            holdout_indices=holdout_indices,
            decoded_params=res["best_decoded_params"],
        )
        res["holdout_evaluation"] = holdout_eval
        runs.append(res)
        all_best_val_rmses.append(res["best_cv_rmse"])
        all_holdout_rmses.append(holdout_eval["holdout_metrics"]["rmse"])

    summary = {
        "seeds": seeds,
        "budget_per_seed": budget,
        "val_rmse_mean": round(float(np.mean(all_best_val_rmses)), 4),
        "val_rmse_std": round(float(np.std(all_best_val_rmses, ddof=1)), 4) if len(seeds) > 1 else 0.0,
        "holdout_rmse_mean": round(float(np.mean(all_holdout_rmses)), 4),
        "holdout_rmse_std": round(float(np.std(all_holdout_rmses, ddof=1)), 4) if len(seeds) > 1 else 0.0,
        "runs": runs,
    }
    return summary
