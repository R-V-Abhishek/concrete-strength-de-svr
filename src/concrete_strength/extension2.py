"""Extension 2: ARD-kernel search space (E2a) and split-replicated Random Search vs DE (E2b).

Follows docs/protocol-extension2.md. Search commands are validation-only and write every
selection; finalize commands refit each frozen selection once and score the holdout.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import json
from pathlib import Path
import time

import numpy as np
from scipy import stats
import typer

from concrete_strength.data import FEATURE_SETS, add_engineered_features, compute_sha256, create_group_splits, load_processed_data
from concrete_strength.de import minimize_de, run_de_single_seed
from concrete_strength.evaluation import build_ard_pipeline, compute_metrics, evaluate_ard_cv, evaluate_default_svr
from concrete_strength.search import evaluate_selected_on_holdout, run_random_search_single_seed
from concrete_strength.stage2 import output_path, provenance, save_json

CONFIG = Path("configs/extension2.json")
DATA = Path("data/processed/concrete_cleaned.csv")
MANIFEST = Path("data/processed/splits_manifest.json")
OUTPUT = Path("results/extension2")
ARD_SEARCH, ARD_RESULTS = "ard_search.json", "ard_results.json"
REPLICATION_SPLITS, REPLICATION_SEARCH, REPLICATION_RESULTS = (
    "replication_splits.json", "replication_search.json", "replication_results.json")
ORIGINAL_RESULTS = Path("results/extension/extension_results.json")


def _mean_std(values: list[float]) -> dict[str, float]:
    return {"mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values, ddof=1)), 4) if len(values) > 1 else 0.0}


def _ard_bounds(n_features: int, base: dict) -> list[tuple[float, float]]:
    return [tuple(base["log_C"]), tuple(base["log_epsilon"]), *[tuple(base["log_gamma"])] * n_features]


def run_ard_single_seed(df, folds, seed: int, budget: int, base_bounds: dict, method: str,
                        population_size: int, de: dict, columns: list[str]) -> dict:
    """Random Search or DE over (log C, log epsilon, log gamma_1..d) with the ARD kernel."""
    bounds = _ard_bounds(len(columns), base_bounds)
    fold_scores: list[list[float]] = []

    def objective(position: np.ndarray) -> float:
        mean_rmse, rmses = evaluate_ard_cv(df, folds, 10.0 ** position[0], 10.0 ** position[2:],
                                           10.0 ** position[1], columns)
        fold_scores.append(rmses)
        return mean_rmse

    if method == "RandomSearch":
        rng = np.random.default_rng(seed)
        limits = np.asarray(bounds)
        started = time.perf_counter()
        points = [rng.uniform(limits[:, 0], limits[:, 1]) for _ in range(budget)]
        fitness = [objective(point) for point in points]
        runtime = time.perf_counter() - started
        best = int(np.argmin(fitness))
        positions, best_position, best_fitness = [p.tolist() for p in points], points[best].tolist(), fitness[best]
    else:
        result = minimize_de(objective, bounds, seed, budget, population_size,
                             de["mutation_weight"], de["crossover_rate"], method)
        runtime = result.duration_seconds
        positions = [record.position for record in result.history]
        fitness = [record.fitness for record in result.history]
        best = int(np.argmin(fitness))
        best_position, best_fitness = result.best_position, result.best_fitness
    best_so_far = np.minimum.accumulate(fitness)
    return {
        "optimizer": method, "seed": seed, "budget": budget, "population_size": population_size,
        "total_evaluations": len(fitness), "total_runtime_seconds": round(runtime, 2),
        "best_log_params": best_position,
        "best_decoded_params": {"C": 10 ** best_position[0], "epsilon": 10 ** best_position[1],
                                "gamma": [10 ** g for g in best_position[2:]]},
        "best_cv_rmse": best_fitness, "best_fold_rmses": fold_scores[best],
        "history": [{"call_index": i + 1, "log_params": positions[i], "mean_cv_rmse": fitness[i],
                     "best_so_far_rmse": float(best_so_far[i])} for i in range(len(fitness))],
    }


def _ard_task(task: dict) -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    base = json.loads(Path("configs/experiment.json").read_text(encoding="utf-8"))["search_space"]
    df, manifest = load_processed_data(DATA, MANIFEST)
    df = add_engineered_features(df)
    columns, folds = FEATURE_SETS[config["feature_set"]], manifest["cv_folds"]
    seed, method, budget, population = task["seed"], task["method"], config["ard"]["budget"], task.get("population_size", 15)
    if task["space"] == "ard":
        run = run_ard_single_seed(df, folds, seed, budget, base, method, population, config["de"], columns)
    elif method == "RandomSearch":
        run = run_random_search_single_seed(df, folds, seed, budget, base, columns)
    else:
        run = run_de_single_seed(df, folds, seed, budget, base, population, config["de"]["mutation_weight"],
                                 config["de"]["crossover_rate"], columns, method)
    return {"space": task["space"], "method": method, **run}


def _run_parallel(function, tasks: list[dict], workers: int) -> list[dict]:
    """Run tasks in worker processes; results come back in task order."""
    results: list[dict | None] = [None] * len(tasks)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(function, task): i for i, task in enumerate(tasks)}
        for future in as_completed(futures):
            i = futures[future]
            results[i] = future.result()
            typer.echo(f"done {len([r for r in results if r])}/{len(tasks)}: "
                       f"{ {k: v for k, v in tasks[i].items()} } cv={results[i]['best_cv_rmse']}")
    return results


def ext2_ard_search(output_dir: Path = OUTPUT) -> None:
    """E2a validation-only searches (no holdout access)."""
    destination = output_path(output_dir, ARD_SEARCH)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    tasks = [{**spec, "seed": seed} for spec in config["ard"]["runs"] for seed in config["seeds"]]
    runs = _run_parallel(_ard_task, tasks, config["workers"])
    save_json(destination, {"stage": "validation_only", "config": config,
                            "provenance": provenance(CONFIG, DATA, MANIFEST), "runs": runs})
    typer.echo(f"Saved validation-selected candidates: {destination}")


def _aggregate(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    aggregates = []
    for key in dict.fromkeys(tuple(r[k] for k in keys) for r in rows):
        group = [r for r in rows if tuple(r[k] for k in keys) == key]
        aggregates.append({**dict(zip(keys, key)),
                           "validation_rmse": _mean_std([r["val_rmse"] for r in group]),
                           **{f"holdout_{m}": _mean_std([r["holdout"][m] for r in group]) for m in ("rmse", "mae", "r2")},
                           "runtime_seconds": _mean_std([r["runtime_seconds"] for r in group])})
    return aggregates


def ext2_ard_finalize(search_path: Path = OUTPUT / ARD_SEARCH, output_dir: Path = OUTPUT) -> None:
    """Refit each frozen E2a selection once on development data and score the holdout."""
    destination = output_path(output_dir, ARD_RESULTS)
    metrics_path = output_path(output_dir, "ard_metrics.csv")
    search = json.loads(search_path.read_text(encoding="utf-8"))
    df, manifest = load_processed_data(DATA, MANIFEST)
    df = add_engineered_features(df)
    columns = FEATURE_SETS[search["config"]["feature_set"]]
    dev, holdout = manifest["development_indices"], manifest["holdout_indices"]
    X = df[columns].to_numpy(dtype=float)
    y = df["compressive_strength"].to_numpy(dtype=float)
    rows = []
    for run in search["runs"]:
        params = run["best_decoded_params"]
        if run["space"] == "ard":
            model = build_ard_pipeline(params["C"], params["gamma"], params["epsilon"])
            model.fit(X[dev], y[dev])
            predictions = model.predict(X[holdout])
            metrics = compute_metrics(y[holdout], predictions)
            predictions = [round(float(p), 4) for p in predictions]
        else:
            evaluation = evaluate_selected_on_holdout(df, dev, holdout, params, columns)
            metrics, predictions = evaluation["holdout_metrics"], evaluation["holdout_predictions"]
        rows.append({"space": run["space"], "method": run["method"], "seed": run["seed"],
                     "val_rmse": run["best_cv_rmse"], "params": params,
                     "runtime_seconds": run["total_runtime_seconds"],
                     "holdout": metrics, "holdout_predictions": predictions})
    best = min(rows, key=lambda r: (r["val_rmse"], r["space"], r["method"], r["seed"]))
    result = {"stage": "holdout_evaluated_once", "holdout_used_for_selection": False,
              "aggregates": _aggregate(rows, ("space", "method")),
              "demonstration": {k: best[k] for k in ("space", "method", "seed", "val_rmse", "params", "holdout")},
              "runs": rows, "search_sha256": compute_sha256(search_path),
              "provenance": provenance(CONFIG, DATA, MANIFEST)}
    save_json(destination, result)
    with metrics_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["space", "method", "seed", "val_rmse", "rmse", "mae", "r2"])
        for r in rows:
            writer.writerow([r["space"], r["method"], r["seed"], r["val_rmse"],
                             r["holdout"]["rmse"], r["holdout"]["mae"], r["holdout"]["r2"]])
    typer.echo(f"Saved {destination} and {metrics_path}")


def _replication_task(task: dict) -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    rep = config["replication"]
    base = json.loads(Path("configs/experiment.json").read_text(encoding="utf-8"))["search_space"]
    df, _ = load_processed_data(DATA, MANIFEST)
    df = add_engineered_features(df)
    splits = json.loads((OUTPUT / REPLICATION_SPLITS).read_text(encoding="utf-8"))
    folds = splits[str(task["split"])]["cv_folds"]
    columns = FEATURE_SETS[config["feature_set"]]
    if task["method"] == "RandomSearch":
        run = run_random_search_single_seed(df, folds, task["seed"], rep["budget"], base, columns)
    else:
        run = run_de_single_seed(df, folds, task["seed"], rep["budget"], base, rep["population_size"],
                                 config["de"]["mutation_weight"], config["de"]["crossover_rate"], columns, task["method"])
    return {"split": task["split"], "method": task["method"], **run}


def ext2_replication_search(output_dir: Path = OUTPUT) -> None:
    """E2b: create the new outer splits, then run validation-only searches on each."""
    splits_path = output_path(output_dir, REPLICATION_SPLITS)
    destination = output_path(output_dir, REPLICATION_SEARCH)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    df, _ = load_processed_data(DATA, MANIFEST)
    splits = {str(s): create_group_splits(df, df["group_id"], 0.20, s, 5)
              for s in config["replication"]["split_seeds"]}
    save_json(splits_path, splits)
    tasks = [{"split": s, "method": m, "seed": seed} for s in config["replication"]["split_seeds"]
             for m in config["replication"]["methods"] for seed in config["seeds"]]
    runs = _run_parallel(_replication_task, tasks, config["workers"])
    save_json(destination, {"stage": "validation_only", "config": config,
                            "splits_sha256": compute_sha256(splits_path),
                            "provenance": provenance(CONFIG, DATA, MANIFEST), "runs": runs})
    typer.echo(f"Saved validation-selected candidates: {destination}")


def _t_interval(values: list[float]) -> dict:
    mean, sd = float(np.mean(values)), float(np.std(values, ddof=1))
    half = float(stats.t.ppf(0.975, len(values) - 1)) * sd / np.sqrt(len(values))
    return {"n": len(values), "mean": round(mean, 4), "sd": round(sd, 4),
            "ci95": [round(mean - half, 4), round(mean + half, 4)]}


def ext2_replication_finalize(search_path: Path = OUTPUT / REPLICATION_SEARCH, output_dir: Path = OUTPUT) -> None:
    """Score each frozen E2b selection once on its own split's holdout and summarize d = RS - DE."""
    destination = output_path(output_dir, REPLICATION_RESULTS)
    metrics_path = output_path(output_dir, "replication_metrics.csv")
    search = json.loads(search_path.read_text(encoding="utf-8"))
    splits = json.loads((search_path.parent / REPLICATION_SPLITS).read_text(encoding="utf-8"))
    df, _ = load_processed_data(DATA, MANIFEST)
    df = add_engineered_features(df)
    columns = FEATURE_SETS[search["config"]["feature_set"]]
    rows = []
    for run in search["runs"]:
        split = splits[str(run["split"])]
        evaluation = evaluate_selected_on_holdout(df, split["development_indices"], split["holdout_indices"],
                                                  run["best_decoded_params"], columns)
        rows.append({"split": run["split"], "method": run["method"], "seed": run["seed"],
                     "val_rmse": run["best_cv_rmse"], "params": run["best_decoded_params"],
                     "holdout": evaluation["holdout_metrics"]})
    per_split = []
    for s in search["config"]["replication"]["split_seeds"]:
        split = splits[str(s)]
        default = evaluate_default_svr(df, split["cv_folds"], split["development_indices"],
                                       split["holdout_indices"], feature_columns=columns)
        entry = {"split": s, "default_holdout_rmse": default["holdout_metrics"]["rmse"]}
        for method in search["config"]["replication"]["methods"]:
            group = [r for r in rows if r["split"] == s and r["method"] == method]
            entry[method] = {"validation_rmse": _mean_std([r["val_rmse"] for r in group]),
                             "holdout_rmse": _mean_std([r["holdout"]["rmse"] for r in group])}
        entry["d_holdout"] = round(entry["RandomSearch"]["holdout_rmse"]["mean"] - entry["rand/1/bin"]["holdout_rmse"]["mean"], 4)
        entry["d_validation"] = round(entry["RandomSearch"]["validation_rmse"]["mean"] - entry["rand/1/bin"]["validation_rmse"]["mean"], 4)
        per_split.append(entry)
    original = json.loads(ORIGINAL_RESULTS.read_text(encoding="utf-8"))["aggregates"]
    pick = {a["method"]: a for a in original if a["feature_set"] == "log_age"}
    original_d = {"split": 42,
                  "d_holdout": round(pick["RandomSearch"]["holdout_rmse"]["mean"] - pick["rand/1/bin"]["holdout_rmse"]["mean"], 4),
                  "d_validation": round(pick["RandomSearch"]["validation_rmse"]["mean"] - pick["rand/1/bin"]["validation_rmse"]["mean"], 4)}
    new = [e["d_holdout"] for e in per_split]
    new_val = [e["d_validation"] for e in per_split]
    summary = {"definition": "d = mean holdout RMSE of Random Search minus DE/rand/1/bin; positive favours DE",
               "new_splits_holdout": _t_interval(new), "all_splits_holdout": _t_interval([*new, original_d["d_holdout"]]),
               "new_splits_validation": _t_interval(new_val),
               "all_splits_validation": _t_interval([*new_val, original_d["d_validation"]]),
               "splits_de_better_holdout": sum(d > 0 for d in [*new, original_d["d_holdout"]]),
               "splits_total": len(new) + 1}
    result = {"stage": "holdout_evaluated_once", "holdout_used_for_selection": False,
              "per_split": per_split, "original_split": original_d, "summary": summary, "runs": rows,
              "search_sha256": compute_sha256(search_path), "provenance": provenance(CONFIG, DATA, MANIFEST)}
    save_json(destination, result)
    with metrics_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["split", "method", "seed", "val_rmse", "rmse", "mae", "r2"])
        for r in rows:
            writer.writerow([r["split"], r["method"], r["seed"], r["val_rmse"],
                             r["holdout"]["rmse"], r["holdout"]["mae"], r["holdout"]["r2"]])
    typer.echo(f"Saved {destination} and {metrics_path}")
