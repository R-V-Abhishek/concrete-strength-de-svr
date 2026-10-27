"""Final holdout evaluation, analysis tables, and plots."""

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from concrete_strength.data import FEATURE_COLUMNS, TARGET_COLUMN, compute_sha256, load_processed_data
from concrete_strength.evaluation import build_svr_pipeline, compute_metrics
from concrete_strength.search import evaluate_selected_on_holdout
from concrete_strength.stage2 import provenance


def _ensure_outputs(output_dir: Path, names: list[str]) -> None:
    existing = [str(output_dir / name) for name in names if (output_dir / name).exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing Stage 3 outputs: {existing}")


def _mean_std(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(float(np.mean(values)), 4),
        "std": round(float(np.std(values, ddof=1)), 4) if len(values) > 1 else 0.0,
    }


def _learning_curve(
    df: pd.DataFrame,
    development_indices: list[int],
    params: dict[str, float],
    fractions: list[float],
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Three-fold diagnostic with nested, randomly ordered whole training groups.

    Every fold and fraction uses the same fixed model parameters. No holdout
    rows are eligible, and no tuning is performed for this diagnostic.
    """
    if not fractions or any(not 0 < fraction <= 1 for fraction in fractions):
        raise ValueError("Learning-curve fractions must be in (0, 1]")
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df[TARGET_COLUMN].to_numpy(dtype=float)
    dev = np.asarray(development_indices, dtype=int)
    groups = df["group_id"].to_numpy()
    fold_subsets = []
    for number, (train, val) in enumerate(GroupKFold(3).split(dev, groups=groups[dev])):
        train_idx, val_idx = dev[train], dev[val]
        shuffled_groups = np.random.default_rng(seed + number).permutation(np.unique(groups[train_idx]))
        fold_subsets.append((train_idx, val_idx, shuffled_groups))

    rows = []
    for fraction in fractions:
        details = []
        for number, (train_idx, val_idx, shuffled_groups) in enumerate(fold_subsets):
            count = max(1, int(round(len(shuffled_groups) * fraction)))
            selected_groups = shuffled_groups[:count]
            selected = train_idx[np.isin(groups[train_idx], selected_groups)]
            model = build_svr_pipeline(**params)
            model.fit(X[selected], y[selected])
            details.append({
                "fold": number,
                "training_indices": selected.tolist(), "validation_indices": val_idx.tolist(),
                "training_group_count": count,
                "validation_group_count": len(np.unique(groups[val_idx])),
                "training_row_count": len(selected), "validation_row_count": len(val_idx),
                "train_rmse": compute_metrics(y[selected], model.predict(X[selected]))["rmse"],
                "validation_rmse": compute_metrics(y[val_idx], model.predict(X[val_idx]))["rmse"],
            })
        rows.append({
            "fraction": fraction,
            "training_rows_mean": round(float(np.mean([d["training_row_count"] for d in details])), 2),
            "training_groups_mean": round(float(np.mean([d["training_group_count"] for d in details])), 2),
            "train_rmse_mean": _mean_std([d["train_rmse"] for d in details])["mean"],
            "train_rmse_std": _mean_std([d["train_rmse"] for d in details])["std"],
            "rmse_mean": _mean_std([d["validation_rmse"] for d in details])["mean"],
            "rmse_std": _mean_std([d["validation_rmse"] for d in details])["std"],
            "folds": details,
        })
    return rows


def _save_plots(
    output_dir: Path,
    runs: list[dict[str, Any]],
    summary: dict[str, Any],
    learning_curve: list[dict[str, Any]],
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(9, 5))
    for run in runs:
        history = run["history"]
        ax.plot(
            [entry["call_index"] for entry in history],
            [entry["best_so_far_rmse"] for entry in history],
            alpha=0.8,
            label=f'{run["optimizer"]} seed {run["seed"]}',
        )
    ax.set(title="Validation convergence by objective call", xlabel="Objective calls", ylabel="Best-so-far CV RMSE (MPa)")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "convergence.png", dpi=180)
    plt.close(fig)

    methods = ["Default SVR", "Random Search", "DE"]
    values = [
        summary["comparison"]["default_svr"]["holdout"]["rmse"],
        summary["comparison"]["random_search"]["holdout"]["rmse"]["mean"],
        summary["comparison"]["de"]["holdout"]["rmse"]["mean"],
    ]
    errors = [0.0, summary["comparison"]["random_search"]["holdout"]["rmse"]["std"],
              summary["comparison"]["de"]["holdout"]["rmse"]["std"]]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(methods, values, yerr=errors, capsize=5, color=["#9e9e9e", "#4c78a8", "#f58518"])
    ax.set(title="Holdout RMSE comparison", ylabel="RMSE (MPa)")
    fig.tight_layout()
    fig.savefig(output_dir / "holdout_rmse_comparison.png", dpi=180)
    plt.close(fig)

    demo = summary["demonstration"]
    actual = np.asarray(demo["holdout_actuals"])
    predicted = np.asarray(demo["holdout_predictions"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].scatter(actual, predicted, alpha=0.65, edgecolors="none")
    limits = [min(actual.min(), predicted.min()), max(actual.max(), predicted.max())]
    axes[0].plot(limits, limits, "k--", linewidth=1)
    axes[0].set(title=f'Best DE demonstration (seed {demo["seed"]})', xlabel="Actual strength (MPa)", ylabel="Predicted strength (MPa)")
    residuals = actual - predicted
    axes[1].scatter(predicted, residuals, alpha=0.65, edgecolors="none")
    axes[1].axhline(0, color="k", linestyle="--", linewidth=1)
    axes[1].set(title="Residual diagnostic", xlabel="Predicted strength (MPa)", ylabel="Actual - predicted (MPa)")
    fig.tight_layout()
    fig.savefig(output_dir / "prediction_residuals.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    x = [row["training_groups_mean"] for row in learning_curve]
    y = [row["rmse_mean"] for row in learning_curve]
    err = [row["rmse_std"] for row in learning_curve]
    ax.errorbar(x, y, yerr=err, marker="o", capsize=4, label="Validation")
    ax.errorbar(x, [row["train_rmse_mean"] for row in learning_curve],
                yerr=[row["train_rmse_std"] for row in learning_curve],
                marker="s", capsize=4, label="Training")
    ax.set(title="Development-only learning curve (3 group-disjoint folds)",
           xlabel="Training groups per fold", ylabel="RMSE (MPa)")
    ax.legend(title="Mean ± sample SD")
    fig.tight_layout()
    fig.savefig(output_dir / "learning_curve.png", dpi=180)
    plt.close(fig)


def finalize_experiments(
    de_path: Path = Path("results/de/de_search_results.json"),
    random_path: Path = Path("results/baseline/random_search_results.json"),
    baseline_path: Path = Path("results/baseline/default_baseline.json"),
    data_path: Path = Path("data/processed/concrete_cleaned.csv"),
    manifest_path: Path = Path("data/processed/splits_manifest.json"),
    output_dir: Path = Path("results/final"),
) -> None:
    """Evaluate frozen DE selections on holdout and generate the evidence package."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_names = [
        "final_results.json", "metrics.csv", "convergence.png",
        "holdout_rmse_comparison.png", "prediction_residuals.png", "learning_curve.png",
    ]
    _ensure_outputs(output_dir, output_names)
    df, manifest = load_processed_data(data_path, manifest_path)
    de_result = json.loads(de_path.read_text(encoding="utf-8"))
    random_result = json.loads(random_path.read_text(encoding="utf-8"))
    baseline_result = json.loads(baseline_path.read_text(encoding="utf-8"))
    de_runs = []
    for run in de_result["runs"]:
        evaluation = evaluate_selected_on_holdout(
            df, manifest["development_indices"], manifest["holdout_indices"],
            run["best_decoded_params"],
        )
        actuals = df.iloc[manifest["holdout_indices"]][TARGET_COLUMN].astype(float).tolist()
        predictions = evaluation["holdout_predictions"]
        de_runs.append({
            "optimizer": run["optimizer"], "seed": run["seed"], "budget": run["budget"],
            "best_cv_rmse": run["best_cv_rmse"], "best_log_params": run["best_log_params"],
            "best_decoded_params": run["best_decoded_params"],
            "holdout_metrics": evaluation["holdout_metrics"],
            "refit_time_seconds": evaluation["refit_time_seconds"],
            "holdout_actuals": actuals, "holdout_predictions": predictions,
            "residuals": [round(a - p, 4) for a, p in zip(actuals, predictions, strict=True)],
            "history": run["history"],
        })

    random_runs = random_result["runs"]
    de_metric_rows = [{"method": "DE", "seed": run["seed"], **run["holdout_metrics"]} for run in de_runs]
    random_metric_rows = [{
        "method": "RandomSearch", "seed": run["seed"],
        **run["holdout_evaluation"]["holdout_metrics"],
    } for run in random_runs]
    metric_rows = de_metric_rows + random_metric_rows
    comparison = {
        "default_svr": {"cv": baseline_result["default_svr"]["cv_metrics"], "holdout": baseline_result["default_svr"]["holdout_metrics"]},
        "random_search": {
            "validation": {key: value for key, value in _mean_std([run["best_cv_rmse"] for run in random_runs]).items()},
            "holdout": {metric: _mean_std([row[metric] for row in random_metric_rows]) for metric in ("rmse", "mae", "r2")},
        },
        "de": {
            "validation": {key: value for key, value in _mean_std([run["best_cv_rmse"] for run in de_runs]).items()},
            "holdout": {metric: _mean_std([row[metric] for row in de_metric_rows]) for metric in ("rmse", "mae", "r2")},
        },
    }
    demonstration = min(de_runs, key=lambda run: (run["best_cv_rmse"], run["optimizer"], run["seed"]))
    learning_curve = _learning_curve(
        df, manifest["development_indices"], demonstration["best_decoded_params"], [0.25, 0.5, 0.75, 1.0],
    )
    final = {
        "stage": "final_holdout_evaluation",
        "selection_rule": "validation CV RMSE; ties by method then ascending seed",
        "holdout_used_for_selection": False,
        "comparison": comparison,
        "demonstration": demonstration,
        "runs": de_runs,
        "learning_curve_development_only": learning_curve,
        "provenance": provenance(Path("configs/experiment.json"), data_path, manifest_path),
        "input_sha256": {
            str(path): compute_sha256(path) for path in (de_path, random_path, baseline_path)
        },
    }
    (output_dir / "final_results.json").write_text(json.dumps(final, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(metric_rows).to_csv(output_dir / "metrics.csv", index=False)
    _save_plots(output_dir, de_runs + random_runs, final, learning_curve)


def refresh_diagnostics(output_dir: Path = Path("results/final")) -> None:
    """Correct the learning curve and redraw saved evidence without holdout refits.

    Existing experiment selections, metrics, predictions and original provenance
    are preserved. Changes to tracked artifacts remain recoverable through Git.
    """
    final_path = output_dir / "final_results.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    random_result = json.loads(Path("results/baseline/random_search_results.json").read_text())
    df, manifest = load_processed_data(
        "data/processed/concrete_cleaned.csv", "data/processed/splits_manifest.json",
    )
    curve = _learning_curve(df, manifest["development_indices"],
                            final["demonstration"]["best_decoded_params"], [0.25, 0.5, 0.75, 1.0])
    final["learning_curve_development_only"] = curve
    final["diagnostic_correction"] = {
        "reason": "Replace ordered row prefixes/five folds with nested whole-group samples/three folds; add training RMSE",
        "seed": 42, "fractions": [0.25, 0.5, 0.75, 1.0], "cv_folds": 3,
        "model_selection_changed": False, "holdout_metrics_changed": False,
        "provenance": provenance(Path("configs/experiment.json"),
                                 Path("data/processed/concrete_cleaned.csv"),
                                 Path("data/processed/splits_manifest.json")),
        "stage3_source_sha256": compute_sha256(Path("src/concrete_strength/stage3.py")),
    }
    _save_plots(output_dir, final["runs"] + random_result["runs"], final, curve)
    pd.DataFrame([{k: v for k, v in row.items() if k != "folds"} for row in curve]).to_csv(
        output_dir / "learning_curve.csv", index=False,
    )
    final_path.write_text(json.dumps(final, indent=2, allow_nan=False) + "\n", encoding="utf-8")
