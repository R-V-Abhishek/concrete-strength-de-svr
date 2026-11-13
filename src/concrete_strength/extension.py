"""Log-age extension: matched-budget searches on engineered features, then one holdout pass.

Follows docs/protocol-extension.md. `extension-search` is validation-only and writes all
selections; `extension-finalize` refits each frozen selection once and scores the holdout.
"""

import csv
import json
from pathlib import Path

import numpy as np
import typer

from concrete_strength.data import FEATURE_SETS, add_engineered_features, compute_sha256, load_processed_data
from concrete_strength.de import run_de_single_seed
from concrete_strength.evaluation import evaluate_default_svr
from concrete_strength.search import evaluate_selected_on_holdout, run_random_search_single_seed
from concrete_strength.stage2 import output_path, provenance, save_json

CONFIG = Path("configs/extension.json")
DATA = Path("data/processed/concrete_cleaned.csv")
MANIFEST = Path("data/processed/splits_manifest.json")
SEARCH_FILE = "extension_search.json"


def _mean_std(values: list[float]) -> dict[str, float]:
    return {"mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values, ddof=1)), 4) if len(values) > 1 else 0.0}


def extension_search(output_dir: Path = Path("results/extension")) -> None:
    """Run all configured extension searches (CV only; no holdout access)."""
    destination = output_path(output_dir, SEARCH_FILE)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    base = json.loads(Path("configs/experiment.json").read_text(encoding="utf-8"))
    df, manifest = load_processed_data(DATA, MANIFEST)
    df = add_engineered_features(df)
    folds, bounds, de = manifest["cv_folds"], base["search_space"], config["de"]
    result = {"stage": "validation_only", "config": config,
              "provenance": provenance(CONFIG, DATA, MANIFEST), "runs": []}
    for spec in config["runs"]:
        columns = FEATURE_SETS[spec["feature_set"]]
        for seed in config["seeds"]:
            typer.echo(f"{spec['feature_set']} / {spec['method']} / seed {seed}")
            if spec["method"] == "RandomSearch":
                run = run_random_search_single_seed(df, folds, seed, config["budget"], bounds, columns)
            else:
                run = run_de_single_seed(
                    df, folds, seed, config["budget"], bounds, de["population_size"],
                    de["mutation_weight"], de["crossover_rate"], columns, spec["method"])
            result["runs"].append({"feature_set": spec["feature_set"], "method": spec["method"], **run})
    save_json(destination, result)
    typer.echo(f"Saved validation-selected candidates: {destination}")


def extension_finalize(
    search_path: Path = Path("results/extension/extension_search.json"),
    output_dir: Path = Path("results/extension"),
) -> None:
    """Refit the frozen selections once on development data and score the holdout."""
    destination = output_path(output_dir, "extension_results.json")
    metrics_path = output_path(output_dir, "metrics.csv")
    search = json.loads(search_path.read_text(encoding="utf-8"))
    df, manifest = load_processed_data(DATA, MANIFEST)
    df = add_engineered_features(df)
    dev, holdout = manifest["development_indices"], manifest["holdout_indices"]

    rows = []
    for run in search["runs"]:
        evaluation = evaluate_selected_on_holdout(
            df, dev, holdout, run["best_decoded_params"], FEATURE_SETS[run["feature_set"]])
        rows.append({"feature_set": run["feature_set"], "method": run["method"], "seed": run["seed"],
                     "val_rmse": run["best_cv_rmse"], "params": run["best_decoded_params"],
                     "runtime_seconds": run["total_runtime_seconds"],
                     "holdout": evaluation["holdout_metrics"],
                     "holdout_predictions": evaluation["holdout_predictions"]})

    aggregates = []
    for key in dict.fromkeys((r["feature_set"], r["method"]) for r in rows):
        group = [r for r in rows if (r["feature_set"], r["method"]) == key]
        aggregates.append({
            "feature_set": key[0], "method": key[1], "validation_rmse": _mean_std([r["val_rmse"] for r in group]),
            **{f"holdout_{m}": _mean_std([r["holdout"][m] for r in group]) for m in ("rmse", "mae", "r2")},
            "runtime_seconds": _mean_std([r["runtime_seconds"] for r in group])})

    defaults = {name: evaluate_default_svr(df, manifest["cv_folds"], dev, holdout,
                                           feature_columns=FEATURE_SETS[name])
                for name in search["config"]["default_feature_sets"]}
    best = min(rows, key=lambda r: (r["val_rmse"], r["method"], r["seed"]))
    result = {"stage": "holdout_evaluated_once", "holdout_used_for_selection": False,
              "selection_rule": "lowest mean CV RMSE per run; demonstration ties by method then seed",
              "aggregates": aggregates, "default_svr": defaults,
              "demonstration": {k: best[k] for k in ("feature_set", "method", "seed", "val_rmse", "params", "holdout")},
              "runs": rows, "search_sha256": compute_sha256(search_path),
              "provenance": provenance(CONFIG, DATA, MANIFEST)}
    save_json(destination, result)
    with metrics_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["feature_set", "method", "seed", "val_rmse", "rmse", "mae", "r2"])
        for r in rows:
            writer.writerow([r["feature_set"], r["method"], r["seed"], r["val_rmse"],
                             r["holdout"]["rmse"], r["holdout"]["mae"], r["holdout"]["r2"]])
    typer.echo(f"Saved {destination} and {metrics_path}")
