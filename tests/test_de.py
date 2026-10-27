"""Behavioral checks for explicit DE and the real SVR integration."""

import json
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from concrete_strength.cli import app
from concrete_strength.data import load_processed_data
from concrete_strength.de import crossover, minimize_de, mutate, run_de_single_seed, select_donors
from concrete_strength.stage2 import rastrigin, sphere


def test_donors_exclude_target_and_are_distinct():
    rng = np.random.default_rng(11)
    for target in range(15):
        for _ in range(10):
            donors = select_donors(rng, 15, target)
            assert len(set(donors)) == 3
            assert target not in donors


def test_mutation_equation_and_clipping():
    pop = np.array([[1., 2.], [8., -5.], [-8., 5.], [0., 0.]])
    actual = mutate(pop, np.array([0, 1, 2]), 0.8, np.array([[-3., 3.], [-3., 3.]]))
    np.testing.assert_allclose(actual, [3., -3.])
    np.testing.assert_allclose(
        mutate(pop * 0.1, np.array([0, 1, 2]), 0.8, np.array([[-3., 3.], [-3., 3.]])),
        [1.38, -0.6],
    )


def test_crossover_forces_one_mutant_coordinate_at_zero_rate():
    target = np.zeros(3)
    mutant = np.ones(3)
    trial = crossover(target, mutant, 0., np.random.default_rng(12))
    assert np.count_nonzero(trial) == 1
    np.testing.assert_array_equal(crossover(target, mutant, 1., np.random.default_rng(12)), mutant)


def test_budget_bounds_seed_and_monotonic_best():
    bounds = [(-5.12, 5.12)] * 3
    one = minimize_de(sphere, bounds, seed=11, budget=300)
    two = minimize_de(sphere, bounds, seed=11, budget=300)
    assert len(one.history) == 300
    assert len([h for h in one.history if h.generation == 0]) == 15
    assert one.history[-1].generation == 19
    assert [h.position for h in one.history] == [h.position for h in two.history]
    assert [h.fitness for h in one.history] == [h.fitness for h in two.history]
    assert one.best_fitness == min(h.fitness for h in one.history)
    assert one.best_fitness < one.history[14].best_fitness
    assert all(np.all(np.abs(h.position) <= 5.12) for h in one.history)
    assert np.all(np.diff([h.best_fitness for h in one.history]) <= 0)


def test_generation_uses_frozen_population_and_accepts_better_trials(monkeypatch):
    seen = []

    def zero_mutant(population, donors, weight, bounds):
        seen.append(population.copy())
        return np.zeros(population.shape[1])

    monkeypatch.setattr("concrete_strength.de.mutate", zero_mutant)
    result = minimize_de(sphere, [(-1., 1.)] * 3, seed=3, budget=12,
                         population_size=4, crossover_rate=1.)
    assert len(seen) == 8
    for population in seen[:4]:
        np.testing.assert_array_equal(population, seen[0])
    for population in seen[4:]:
        np.testing.assert_array_equal(population, np.zeros((4, 3)))
    assert result.best_fitness == 0.


def test_worse_trials_are_rejected(monkeypatch):
    seen = []

    def worst_mutant(population, donors, weight, bounds):
        seen.append(population.copy())
        return np.ones(population.shape[1])

    monkeypatch.setattr("concrete_strength.de.mutate", worst_mutant)
    minimize_de(sphere, [(-1., 1.)] * 3, seed=3, budget=12,
                population_size=4, crossover_rate=1.)
    for population in seen:
        np.testing.assert_array_equal(population, seen[0])


@pytest.mark.parametrize("kwargs", [
    {"population_size": 3}, {"budget": 14}, {"budget": 16},
    {"mutation_weight": 0.}, {"mutation_weight": float("nan")},
    {"crossover_rate": -0.1}, {"crossover_rate": float("inf")},
    {"bounds": []}, {"bounds": [(1., 1.)]}, {"bounds": [(0., float("inf"))]},
])
def test_invalid_settings_fail_before_objective(kwargs):
    settings = dict(bounds=[(-1., 1.)] * 3, seed=1)
    settings.update(kwargs)

    def forbidden(position):
        pytest.fail("Invalid settings must not call the objective")

    with pytest.raises(ValueError):
        minimize_de(forbidden, **settings)


def test_nonfinite_objective_fails_with_call_context():
    with pytest.raises(ValueError, match="Nonfinite objective at call 1"):
        minimize_de(lambda x: float("nan"), [(-1., 1.)] * 3, seed=1)


def test_synthetic_functions_have_known_minimum():
    assert sphere(np.zeros(3)) == 0.
    assert rastrigin(np.zeros(3)) == 0.
    assert sphere(np.ones(3)) == 3.
    assert rastrigin(np.ones(3)) == pytest.approx(3.)


def test_real_svr_search_uses_only_given_development_folds():
    df, manifest = load_processed_data("data/processed/concrete_cleaned.csv",
                                       "data/processed/splits_manifest.json")
    # A small real integration uses one existing fold with a bounded, cheap search space.
    df = df.copy()
    df.loc[manifest["holdout_indices"], "compressive_strength"] = np.nan
    result = run_de_single_seed(
        df, manifest["cv_folds"][:1], seed=11, budget=8, population_size=4,
        bounds={"log_C": (-1., 1.), "log_gamma": (-3., -1.), "log_epsilon": (-2., -1.)},
    )
    assert result["total_evaluations"] == 8
    assert len(result["history"]) == 8
    best = min(result["history"], key=lambda entry: entry["mean_cv_rmse"])
    assert result["best_cv_rmse"] == best["mean_cv_rmse"]
    assert result["best_log_params"] == best["log_params"]
    assert result["best_decoded_params"] == best["decoded_params"]
    assert result["best_fold_rmses"] == best["fold_rmses"]
    assert all(len(entry["fold_rmses"]) == 1 for entry in result["history"])
    assert "holdout_evaluation" not in result


def test_de_command_refuses_to_overwrite_results(tmp_path):
    existing = tmp_path / "de_search_results.json"
    existing.write_text("preserved")
    response = CliRunner().invoke(app, ["de-search", "--output-dir", str(tmp_path)])
    assert response.exit_code != 0
    assert "already exists" in response.output
    assert existing.read_text() == "preserved"


def test_de_cli_respects_config_and_saves_validation_only(tmp_path):
    config = json.loads(Path("configs/experiment.json").read_text(encoding="utf-8"))
    config["random_search"].update(budget=4, seeds=[11])
    config["de"].update(budget=4, population_size=4, seeds=[11])
    config["search_space"] = {"log_C": [-1., 1.], "log_gamma": [-3., -1.],
                              "log_epsilon": [-2., -1.]}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    response = CliRunner().invoke(app, ["de-search", "--config-path", str(path),
                                       "--output-dir", str(tmp_path / "output")])
    assert response.exit_code == 0, response.output
    result = json.loads((tmp_path / "output/de_search_results.json").read_text())
    assert result["stage"] == "validation_only"
    assert len(result["runs"]) == 1
    assert result["runs"][0]["total_evaluations"] == 4
    assert len(result["runs"][0]["best_fold_rmses"]) == 5
    assert "holdout_evaluation" not in result["runs"][0]
