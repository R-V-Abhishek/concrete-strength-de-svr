"""Checks for the log-age extension: engineered features and DE variants."""

import json

import numpy as np
import pandas as pd
import pytest

from concrete_strength.data import FEATURE_SETS, add_engineered_features, load_processed_data
from concrete_strength.de import STRATEGIES, minimize_de, run_de_single_seed
from concrete_strength.stage2 import rastrigin, sphere

BOUNDS = [(-5.12, 5.12)] * 3


def test_engineered_features_values_and_originals_untouched():
    df = pd.DataFrame({"cement": [200.0], "blast_furnace_slag": [50.0], "fly_ash": [50.0],
                       "water": [150.0], "superplasticizer": [1.0], "coarse_aggregate": [900.0],
                       "fine_aggregate": [700.0], "age": [28]})
    out = add_engineered_features(df)
    assert out["log_age"].iloc[0] == pytest.approx(np.log(28))
    assert out["water_cement"].iloc[0] == pytest.approx(0.75)
    assert out["water_binder"].iloc[0] == pytest.approx(0.5)
    pd.testing.assert_frame_equal(out[df.columns], df)
    assert all(c in out.columns for c in FEATURE_SETS["log_age_ratios"])
    assert "age" not in FEATURE_SETS["log_age"]


def test_rand1_matches_saved_frozen_run_prefix():
    df, manifest = load_processed_data("data/processed/concrete_cleaned.csv",
                                       "data/processed/splits_manifest.json")
    saved = json.load(open("results/de/de_search_results.json"))["runs"][0]
    run = run_de_single_seed(df, manifest["cv_folds"], seed=11, budget=30)
    for new, old in zip(run["history"], saved["history"][:30], strict=True):
        np.testing.assert_allclose(new["log_params"], old["log_params"], atol=1e-12)
        assert new["mean_cv_rmse"] == pytest.approx(old["mean_cv_rmse"], abs=1e-3)


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_strategies_deterministic_bounded_and_budgeted(strategy):
    a = minimize_de(sphere, BOUNDS, 3, budget=150, strategy=strategy)
    b = minimize_de(sphere, BOUNDS, 3, budget=150, strategy=strategy)
    assert a.best_fitness == b.best_fitness and len(a.history) == 150
    pos = np.array([e.position for e in a.history])
    assert pos.min() >= -5.12 and pos.max() <= 5.12
    rand = minimize_de(sphere, BOUNDS, 3, budget=150).best_fitness
    assert a.best_fitness < 1.0 or strategy == "rand/1/bin"
    assert rand >= 0


@pytest.mark.parametrize("strategy", ["current-to-best/1/bin", "jDE"])
def test_new_strategies_improve_on_initial_population(strategy):
    result = minimize_de(rastrigin, BOUNDS, 5, budget=300, strategy=strategy)
    assert result.best_fitness < min(e.fitness for e in result.history[:15])


def test_unknown_strategy_rejected():
    with pytest.raises(ValueError):
        minimize_de(sphere, BOUNDS, 1, budget=30, strategy="best/2")


def test_extension_evidence_consistent():
    """Saved extension selections are budgeted, in bounds, and holdout metrics match predictions."""
    df, manifest = load_processed_data("data/processed/concrete_cleaned.csv",
                                       "data/processed/splits_manifest.json")
    search = json.load(open("results/extension/extension_search.json"))
    results = json.load(open("results/extension/extension_results.json"))
    assert results["holdout_used_for_selection"] is False and len(search["runs"]) == len(results["runs"]) == 25
    actual = df["compressive_strength"].to_numpy()[manifest["holdout_indices"]]
    for run in search["runs"]:
        assert run["total_evaluations"] == 300
        assert run["best_cv_rmse"] == min(h["mean_cv_rmse"] for h in run["history"])
        assert all(-2 <= h["log_params"][0] <= 4 and -5 <= h["log_params"][1] <= 1
                   and -3 <= h["log_params"][2] <= 1 for h in run["history"])
    for run in results["runs"]:
        rmse = np.sqrt(np.mean((np.asarray(run["holdout_predictions"]) - actual) ** 2))
        assert rmse == pytest.approx(run["holdout"]["rmse"], abs=2e-4)
