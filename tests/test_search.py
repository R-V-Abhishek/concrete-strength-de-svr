"""Unit tests for Random Search sampling bounds, budget accounting, and reproducibility."""

import numpy as np
import pytest

from concrete_strength.data import assign_groups, create_group_splits, load_raw_data
from concrete_strength.search import (
    DEFAULT_BOUNDS,
    run_random_search_single_seed,
    sample_log_hyperparameters,
)


def test_random_sampling_bounds():
    rng = np.random.default_rng(123)
    for _ in range(100):
        log_c, log_gamma, log_eps = sample_log_hyperparameters(rng, DEFAULT_BOUNDS)
        assert DEFAULT_BOUNDS["log_C"][0] <= log_c <= DEFAULT_BOUNDS["log_C"][1]
        assert DEFAULT_BOUNDS["log_gamma"][0] <= log_gamma <= DEFAULT_BOUNDS["log_gamma"][1]
        assert DEFAULT_BOUNDS["log_epsilon"][0] <= log_eps <= DEFAULT_BOUNDS["log_epsilon"][1]


def test_seed_reproducibility():
    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)

    samples1 = [sample_log_hyperparameters(rng1) for _ in range(10)]
    samples2 = [sample_log_hyperparameters(rng2) for _ in range(10)]

    assert samples1 == samples2


def test_call_budget_accounting_fast():
    df = load_raw_data("data/raw/Concrete_Data.xls")
    df_with_groups, group_series = assign_groups(df)
    manifest = create_group_splits(df_with_groups, group_series, cv_folds=2)

    budget = 4
    res = run_random_search_single_seed(
        df=df_with_groups,
        cv_folds=manifest["cv_folds"],
        seed=11,
        budget=budget,
    )

    assert res["total_evaluations"] == budget
    assert len(res["history"]) == budget
    assert res["best_cv_rmse"] > 0.0
    for entry in res["history"]:
        assert len(entry["fold_rmses"]) == 2
        assert entry["mean_cv_rmse"] > 0.0
