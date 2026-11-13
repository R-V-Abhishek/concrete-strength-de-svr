"""DE/rand/1/bin with explicit operators and development-only SVR fitness."""

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any

import numpy as np
import pandas as pd

from concrete_strength.data import FEATURE_COLUMNS
from concrete_strength.evaluation import evaluate_hyperparameters
from concrete_strength.search import DEFAULT_BOUNDS

PARAMETER_NAMES = ("log_C", "log_gamma", "log_epsilon")
STRATEGIES = ("rand/1/bin", "current-to-best/1/bin", "jDE")


@dataclass
class Evaluation:
    position: list[float]
    fitness: float
    best_fitness: float
    generation: int
    target_index: int
    duration_seconds: float
    elapsed_seconds: float


@dataclass
class DEResult:
    best_position: list[float]
    best_fitness: float
    history: list[Evaluation]
    duration_seconds: float


def select_donors(rng: np.random.Generator, population_size: int, target: int) -> np.ndarray:
    """Select three distinct donor indices, excluding the target."""
    eligible = np.delete(np.arange(population_size), target)
    return rng.choice(eligible, size=3, replace=False)


def mutate(population: np.ndarray, donors: np.ndarray, weight: float, bounds: np.ndarray) -> np.ndarray:
    """Differential mutation followed by explicit coordinate clipping."""
    a, b, c = population[donors]
    return np.clip(a + weight * (b - c), bounds[:, 0], bounds[:, 1])


def crossover(target: np.ndarray, mutant: np.ndarray, rate: float, rng: np.random.Generator) -> np.ndarray:
    """Binomial crossover with at least one coordinate from the mutant."""
    mask = rng.random(len(target)) < rate
    mask[rng.integers(len(target))] = True
    return np.where(mask, mutant, target)


def mutate_current_to_best(population: np.ndarray, target: int, best: int, donors: np.ndarray,
                           weight: float, bounds: np.ndarray) -> np.ndarray:
    """v = x_i + F (x_best - x_i) + F (x_r1 - x_r2), clipped; best from the frozen generation."""
    r1, r2 = population[donors[:2]]
    return np.clip(population[target] + weight * (population[best] - population[target])
                   + weight * (r1 - r2), bounds[:, 0], bounds[:, 1])


def minimize_de(
    objective: Callable[[np.ndarray], float],
    bounds: list[tuple[float, float]],
    seed: int,
    budget: int = 300,
    population_size: int = 15,
    mutation_weight: float = 0.8,
    crossover_rate: float = 0.9,
    strategy: str = "rand/1/bin",
) -> DEResult:
    """Minimize a scalar objective using deferred, complete-generation DE.

    The budget includes initialization. Every attempted objective evaluation counts,
    including repeated candidates. A nonfinite fitness fails the run explicitly.
    """
    limits = np.asarray(bounds, dtype=float)
    if limits.ndim != 2 or limits.shape[1] != 2 or len(limits) == 0:
        raise ValueError("bounds must contain at least one (lower, upper) pair")
    if not np.isfinite(limits).all() or np.any(limits[:, 0] >= limits[:, 1]):
        raise ValueError("bounds must be finite with lower < upper")
    if population_size < 4:
        raise ValueError("population_size must be at least 4 for three distinct donors")
    if budget < population_size or budget % population_size:
        raise ValueError("budget must include initialization and complete populations")
    if not np.isfinite(mutation_weight) or not 0 < mutation_weight <= 2:
        raise ValueError("mutation_weight must be in (0, 2]")
    if not np.isfinite(crossover_rate) or not 0 <= crossover_rate <= 1:
        raise ValueError("crossover_rate must be in [0, 1]")
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}")

    rng = np.random.default_rng(seed)
    population = rng.uniform(limits[:, 0], limits[:, 1], size=(population_size, len(limits)))
    history: list[Evaluation] = []
    best_value = float("inf")
    best_position: list[float] = []
    started = time.perf_counter()

    def evaluate(position: np.ndarray, generation: int, target_index: int) -> float:
        nonlocal best_value, best_position
        call_started = time.perf_counter()
        # Isolate the population from an objective that mutates its argument.
        value = float(objective(position.copy()))
        if not np.isfinite(value):
            raise ValueError(f"Nonfinite objective at call {len(history) + 1}: {position.tolist()}")
        if value < best_value:
            best_value = value
            best_position = position.tolist()
        history.append(Evaluation(
            position=position.tolist(), fitness=value, best_fitness=best_value,
            generation=generation, target_index=target_index,
            duration_seconds=time.perf_counter() - call_started,
            elapsed_seconds=time.perf_counter() - started,
        ))
        return value

    fitness = np.array([evaluate(point, 0, i) for i, point in enumerate(population)])
    # jDE keeps one (F, CR) pair per individual; other strategies use the fixed controls.
    weights = np.full(population_size, mutation_weight)
    rates = np.full(population_size, crossover_rate)
    for generation in range(1, budget // population_size):
        # All donors and targets come from the same frozen source generation.
        next_population = population.copy()
        next_fitness = fitness.copy()
        next_weights, next_rates = weights.copy(), rates.copy()
        best = int(np.argmin(fitness))
        for i in range(population_size):
            weight, rate = weights[i], rates[i]
            if strategy == "jDE":
                if rng.random() < 0.1:
                    weight = 0.1 + 0.9 * rng.random()
                if rng.random() < 0.1:
                    rate = rng.random()
            donors = select_donors(rng, population_size, i)
            if strategy == "current-to-best/1/bin":
                mutant = mutate_current_to_best(population, i, best, donors, weight, limits)
            else:
                mutant = mutate(population, donors, weight, limits)
            trial = crossover(population[i], mutant, rate, rng)
            trial_fitness = evaluate(trial, generation, i)
            if trial_fitness <= fitness[i]:
                next_population[i] = trial
                next_fitness[i] = trial_fitness
                next_weights[i], next_rates[i] = weight, rate
        population, fitness = next_population, next_fitness
        weights, rates = next_weights, next_rates

    return DEResult(best_position, best_value, history, time.perf_counter() - started)


def run_de_single_seed(
    df: pd.DataFrame,
    cv_folds: list[dict[str, Any]],
    seed: int,
    budget: int = 300,
    bounds: dict[str, tuple[float, float]] | None = None,
    population_size: int = 15,
    mutation_weight: float = 0.8,
    crossover_rate: float = 0.9,
    feature_columns: list[str] = FEATURE_COLUMNS,
    strategy: str = "rand/1/bin",
) -> dict[str, Any]:
    """Evaluate DE with the same CV objective as Random Search; no holdout access.

    Match the existing Random Search result keys, while retaining full-precision
    coordinates and decoded parameters for reproducible later refitting.
    """
    search_bounds = DEFAULT_BOUNDS if bounds is None else bounds
    fold_scores: list[list[float]] = []

    def objective(position: np.ndarray) -> float:
        mean_rmse, rmses = evaluate_hyperparameters(
            log_C=float(position[0]), log_gamma=float(position[1]),
            log_epsilon=float(position[2]), df=df, cv_folds=cv_folds,
            feature_columns=feature_columns,
        )
        fold_scores.append(rmses)
        return mean_rmse

    result = minimize_de(
        objective, [search_bounds[name] for name in PARAMETER_NAMES], seed,
        budget, population_size, mutation_weight, crossover_rate, strategy,
    )

    def decode(position: list[float]) -> dict[str, float]:
        return dict(zip(("C", "gamma", "epsilon"), (float(10 ** p) for p in position), strict=True))

    history = [{
        "call_index": i + 1, "generation": record.generation,
        "target_index": record.target_index, "log_params": record.position,
        "decoded_params": decode(record.position), "mean_cv_rmse": record.fitness,
        "fold_rmses": fold_scores[i], "best_so_far_rmse": record.best_fitness,
        "elapsed_seconds": record.duration_seconds,
        "cumulative_elapsed_seconds": record.elapsed_seconds,
    } for i, record in enumerate(result.history)]
    best_index = min(range(len(history)), key=lambda i: history[i]["mean_cv_rmse"])
    return {
        "optimizer": "DE/" + strategy if strategy != "jDE" else "jDE", "seed": seed, "budget": budget,
        "total_evaluations": len(history), "population_size": population_size,
        "generations": budget // population_size - 1,
        "mutation_weight": mutation_weight, "crossover_rate": crossover_rate,
        "boundary_handling": "clip", "updating": "deferred",
        "total_runtime_seconds": result.duration_seconds,
        "best_log_params": result.best_position,
        "best_decoded_params": decode(result.best_position),
        "best_cv_rmse": result.best_fitness,
        "best_fold_rmses": history[best_index]["fold_rmses"], "history": history,
    }
