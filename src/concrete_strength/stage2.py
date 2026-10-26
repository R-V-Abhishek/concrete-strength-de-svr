"""Stage 2 commands: validation-only DE, a matched pilot, and synthetic checks."""

from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
from sklearn.model_selection import GroupKFold
import typer

from concrete_strength.data import compute_sha256, load_processed_data
from concrete_strength.de import minimize_de, run_de_single_seed
from concrete_strength.search import run_random_search_single_seed


def provenance(config_path: Path, data_path: Path, manifest_path: Path) -> dict:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    return {
        "code_revision": revision, "working_tree_dirty": bool(dirty),
        "python": sys.version, "platform": platform.platform(),
        "processor": platform.processor(), "fold_workers": 1,
        "versions": {name: version(name) for name in ("numpy", "pandas", "scikit-learn", "scipy")},
        "sha256": {str(path): compute_sha256(path) for path in (
            config_path, data_path, manifest_path, Path("data/raw/Concrete_Data.xls"),
            Path("src/concrete_strength/de.py"), Path("src/concrete_strength/stage2.py"),
            Path("src/concrete_strength/evaluation.py"), Path("src/concrete_strength/search.py"),
            Path("src/concrete_strength/data.py"), Path("uv.lock"),
        )},
    }


def output_path(output_dir: Path, name: str) -> Path:
    path = output_dir / name
    if path.exists():
        raise typer.BadParameter(f"Output already exists: {path}; choose another --output-dir")
    return path


def save_json(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")


def de_search(
    config_path: Path = Path("configs/experiment.json"),
    data_path: Path = Path("data/processed/concrete_cleaned.csv"),
    manifest_path: Path = Path("data/processed/splits_manifest.json"),
    output_dir: Path = Path("results/de"),
) -> None:
    """Run configured final-budget DE searches; save selections without testing holdout."""
    destination = output_path(output_dir, "de_search_results.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    settings = config["de"]
    if settings["budget"] != config["random_search"]["budget"]:
        raise typer.BadParameter("DE and Random Search budgets must match")
    if settings["seeds"] != config["random_search"]["seeds"]:
        raise typer.BadParameter("DE and Random Search seed lists must match")
    df, manifest = load_processed_data(data_path, manifest_path)
    result = {"stage": "validation_only", "config": config,
              "provenance": provenance(config_path, data_path, manifest_path), "runs": []}
    for seed in settings["seeds"]:
        typer.echo(f"DE seed {seed}, budget {settings['budget']} (CV only)")
        result["runs"].append(run_de_single_seed(
            df, manifest["cv_folds"], seed=seed, budget=settings["budget"],
            bounds=config["search_space"], population_size=settings["population_size"],
            mutation_weight=settings["mutation_weight"], crossover_rate=settings["crossover_rate"],
        ))
    save_json(destination, result)
    typer.echo(f"Saved validation-selected candidates: {destination}")


def pilot(
    config_path: Path = Path("configs/experiment.json"),
    data_path: Path = Path("data/processed/concrete_cleaned.csv"),
    manifest_path: Path = Path("data/processed/splits_manifest.json"),
    output_dir: Path = Path("results/pilot"),
) -> None:
    """Run matched Random Search/DE pilots on development rows only; no holdout refit."""
    destination = output_path(output_dir, "stage2_pilot.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    settings = config["pilot"]
    df, manifest = load_processed_data(data_path, manifest_path)
    dev = np.array(manifest["development_indices"], dtype=int)
    groups = df.iloc[dev]["group_id"].to_numpy()
    folds = [{"train_indices": dev[train].tolist(), "val_indices": dev[val].tolist()}
             for train, val in GroupKFold(settings["cv_folds"]).split(dev, groups=groups)]
    holdout = set(manifest["holdout_indices"])
    for fold in folds:
        if holdout.intersection(fold["train_indices"] + fold["val_indices"]):
            raise ValueError("Pilot fold contains holdout rows")
        train_groups = set(df.iloc[fold["train_indices"]]["group_id"])
        val_groups = set(df.iloc[fold["val_indices"]]["group_id"])
        if train_groups.intersection(val_groups):
            raise ValueError("Pilot fold contains overlapping groups")

    result = {"stage": "pilot_development_only", "config": config,
              "provenance": provenance(config_path, data_path, manifest_path),
              "cv_folds": folds, "runs": []}
    for seed in settings["seeds"]:
        for method in ("RandomSearch", "DE"):
            typer.echo(f"Pilot {method}: seed {seed}, {settings['budget']} candidates")
            common = dict(df=df, cv_folds=folds, seed=seed, budget=settings["budget"],
                          bounds=config["search_space"])
            if method == "RandomSearch":
                run = run_random_search_single_seed(**common)
            else:
                run = run_de_single_seed(
                    **common, population_size=settings["population_size"],
                    mutation_weight=config["de"]["mutation_weight"],
                    crossover_rate=config["de"]["crossover_rate"],
                )
            result["runs"].append(run)
            typer.echo(f"  best CV RMSE={run['best_cv_rmse']:.4f} MPa; "
                       f"time={run['total_runtime_seconds']:.2f}s")
    save_json(destination, result)
    typer.echo(f"Saved pilot (not final results): {destination}")


def sphere(position: np.ndarray) -> float:
    return float(np.sum(position ** 2))


def rastrigin(position: np.ndarray) -> float:
    return float(10 * len(position) + np.sum(position ** 2 - 10 * np.cos(2 * np.pi * position)))


def synthetic_benchmarks(output_dir: Path = Path("results/pilot")) -> None:
    """Save equal-budget Sphere/Rastrigin verification; optimum is zero at the origin."""
    destination = output_path(output_dir, "synthetic_benchmarks.json")
    bounds = [(-5.12, 5.12)] * 3
    results = []
    for name, objective in (("Sphere", sphere), ("Rastrigin", rastrigin)):
        for seed in (11, 22, 33, 44, 55):
            de = minimize_de(objective, bounds, seed, budget=300)
            rng = np.random.default_rng(seed)
            started = time.perf_counter()
            random_fitness = [objective(point) for point in rng.uniform(-5.12, 5.12, (300, 3))]
            results.append({
                "function": name, "seed": seed, "budget": 300, "bounds": bounds,
                "de_best": de.best_fitness, "de_initial_best": de.history[14].best_fitness,
                "de_best_position": de.best_position,
                "de_best_history": [entry.best_fitness for entry in de.history],
                "random_best": min(random_fitness),
                "random_best_history": np.minimum.accumulate(random_fitness).tolist(),
                "de_seconds": de.duration_seconds,
                "random_seconds": time.perf_counter() - started,
            })
    save_json(destination, {"stage": "synthetic_verification", "optimum": 0.0,
                            "de_settings": {"population_size": 15, "F": 0.8, "CR": 0.9},
                            "code_sha256": compute_sha256(Path("src/concrete_strength/de.py")),
                            "runs": results})
    typer.echo(f"Saved Sphere/Rastrigin verification: {destination}")
