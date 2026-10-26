"""Command-Line Interface (CLI) for Concrete Compressive Strength Project."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import typer
from rich import print as rprint
from rich.table import Table

from concrete_strength.data import (
    assign_groups,
    audit_data,
    compute_sha256,
    create_group_splits,
    load_processed_data,
    load_raw_data,
    save_processed_data,
)
from concrete_strength.evaluation import (
    evaluate_default_svr,
    evaluate_dummy_baseline,
)
from concrete_strength.search import (
    run_random_search_multi_seeds,
    run_random_search_single_seed,
)
from concrete_strength.stage2 import de_search, pilot, synthetic_benchmarks

app = typer.Typer(help="Concrete Compressive Strength DE-SVR Pipeline CLI")
app.command()(de_search)
app.command()(pilot)
app.command()(synthetic_benchmarks)


@app.command()
def audit(
    raw_path: str = typer.Option("data/raw/Concrete_Data.xls", help="Path to raw Excel file"),
    output_dir: str = typer.Option("data/processed", help="Directory for processed data and manifests"),
    test_size: float = typer.Option(0.20, help="Fraction of groups for holdout test split"),
    random_state: int = typer.Option(42, help="Seed for GroupShuffleSplit"),
    cv_folds: int = typer.Option(5, help="Number of GroupKFold cross-validation folds"),
) -> None:
    """Audit the raw dataset, assign recipe groups, and save deterministic split manifests."""
    rprint(f"[bold cyan]Auditing raw dataset:[/bold cyan] {raw_path}")
    sha256_hash = compute_sha256(raw_path)
    df_raw = load_raw_data(raw_path)
    stats = audit_data(df_raw)

    table = Table(title="Dataset Ingestion & Duplicate Audit")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Raw File SHA-256", sha256_hash[:16] + "...")
    table.add_row("Total Instances", str(stats["total_rows"]))
    table.add_row("Features + Target", str(stats["total_columns"]))
    table.add_row("Missing / NaN Count", str(stats["null_count"]))
    table.add_row("Exact 9-col Duplicates", str(stats["exact_duplicates"]))
    table.add_row("8-input Recipe Duplicates", str(stats["feature_duplicates"]))
    table.add_row("Unique Recipe Groups", str(stats["unique_recipes"]))
    table.add_row("Same Recipe Differing Target", str(stats["differing_target_same_recipe"]))
    rprint(table)

    rprint("[bold cyan]Generating group-aware splits...[/bold cyan]")
    df_with_groups, group_series = assign_groups(df_raw)
    manifest = create_group_splits(
        df_with_groups,
        group_series,
        test_size=test_size,
        random_state=random_state,
        cv_folds=cv_folds,
    )

    csv_path, manifest_path = save_processed_data(df_with_groups, manifest, output_dir)
    rprint(f"[green]Saved cleaned data to:[/green] {csv_path}")
    rprint(f"[green]Saved splits manifest to:[/green] {manifest_path}")

    split_table = Table(title="Group-Aware Partitioning Summary")
    split_table.add_column("Partition", style="cyan")
    split_table.add_column("Rows", style="green")
    split_table.add_column("Unique Groups", style="magenta")
    split_table.add_row("Development Set", str(manifest["development_samples"]), str(manifest["development_groups"]))
    split_table.add_row("Holdout Test Set", str(manifest["holdout_samples"]), str(manifest["holdout_groups"]))
    for fold in manifest["cv_folds"]:
        split_table.add_row(
            f"  CV Fold {fold['fold']} (Train/Val)",
            f"{fold['num_train_samples']} / {fold['num_val_samples']}",
            f"{fold['num_train_groups']} / {fold['num_val_groups']}",
        )
    rprint(split_table)


@app.command()
def baseline(
    data_path: str = typer.Option("data/processed/concrete_cleaned.csv", help="Processed CSV path"),
    manifest_path: str = typer.Option("data/processed/splits_manifest.json", help="Manifest JSON path"),
    output_dir: str = typer.Option("results/baseline", help="Directory to save baseline results"),
) -> None:
    """Evaluate DummyRegressor and Default SVR baselines on 5-fold CV and holdout test set."""
    df, manifest = load_processed_data(data_path, manifest_path)
    cv_folds = manifest["cv_folds"]
    dev_idx = manifest["development_indices"]
    holdout_idx = manifest["holdout_indices"]

    rprint("[bold cyan]Evaluating Dummy Regressor Baseline (Mean Prediction)...[/bold cyan]")
    dummy_res = evaluate_dummy_baseline(df, cv_folds, dev_idx, holdout_idx)

    rprint("[bold cyan]Evaluating Default RBF-SVR Baseline (C=1.0, gamma='scale', epsilon=0.1)...[/bold cyan]")
    svr_res = evaluate_default_svr(df, cv_folds, dev_idx, holdout_idx)

    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    baseline_file = out_p / "default_baseline.json"
    with baseline_file.open("w", encoding="utf-8") as f:
        json.dump({"dummy": dummy_res, "default_svr": svr_res}, f, indent=2)

    table = Table(title="Baseline Evaluation Metrics (Target in MPa)")
    table.add_column("Model", style="cyan")
    table.add_column("5-Fold CV RMSE", style="magenta")
    table.add_column("Holdout RMSE", style="green")
    table.add_column("Holdout MAE", style="yellow")
    table.add_column("Holdout R^2", style="blue")

    table.add_row(
        dummy_res["model"],
        f"{dummy_res['cv_mean_rmse']} +/- {dummy_res['cv_std_rmse']}",
        str(dummy_res["holdout_metrics"]["rmse"]),
        str(dummy_res["holdout_metrics"]["mae"]),
        str(dummy_res["holdout_metrics"]["r2"]),
    )
    table.add_row(
        svr_res["model"],
        f"{svr_res['cv_metrics']['mean_rmse']} +/- {svr_res['cv_metrics']['std_rmse']}",
        str(svr_res["holdout_metrics"]["rmse"]),
        str(svr_res["holdout_metrics"]["mae"]),
        str(svr_res["holdout_metrics"]["r2"]),
    )
    rprint(table)
    rprint(f"[green]Saved baseline results to:[/green] {baseline_file}")


@app.command()
def random_search(
    budget: int = typer.Option(300, help="Evaluation budget per seed"),
    seeds: list[int] = typer.Option([11, 22, 33, 44, 55], help="Random seeds to evaluate"),
    data_path: str = typer.Option("data/processed/concrete_cleaned.csv", help="Processed CSV path"),
    manifest_path: str = typer.Option("data/processed/splits_manifest.json", help="Manifest JSON path"),
    output_dir: str = typer.Option("results/baseline", help="Directory to save random search results"),
) -> None:
    """Execute equal-budget Random Search across multiple seeds."""
    df, manifest = load_processed_data(data_path, manifest_path)
    cv_folds = manifest["cv_folds"]
    dev_idx = manifest["development_indices"]
    holdout_idx = manifest["holdout_indices"]

    rprint(f"[bold cyan]Running Random Search with budget={budget} across seeds={seeds}...[/bold cyan]")
    summary = run_random_search_multi_seeds(
        df=df,
        cv_folds=cv_folds,
        dev_indices=dev_idx,
        holdout_indices=holdout_idx,
        seeds=seeds,
        budget=budget,
    )

    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    out_file = out_p / "random_search_results.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    table = Table(title=f"Random Search Results (Budget: {budget} evaluations)")
    table.add_column("Seed", style="cyan")
    table.add_column("Best Val RMSE", style="magenta")
    table.add_column("Best C", style="yellow")
    table.add_column("Best Gamma", style="yellow")
    table.add_column("Best Epsilon", style="yellow")
    table.add_column("Holdout RMSE", style="green")
    table.add_column("Holdout R^2", style="blue")
    table.add_column("Runtime (s)", style="white")

    for run in summary["runs"]:
        p = run["best_decoded_params"]
        h = run["holdout_evaluation"]["holdout_metrics"]
        table.add_row(
            str(run["seed"]),
            str(run["best_cv_rmse"]),
            str(p["C"]),
            str(p["gamma"]),
            str(p["epsilon"]),
            str(h["rmse"]),
            str(h["r2"]),
            str(run["total_runtime_seconds"]),
        )
    table.add_row(
        "[bold]Mean +/- Std[/bold]",
        f"{summary['val_rmse_mean']} +/- {summary['val_rmse_std']}",
        "-",
        "-",
        "-",
        f"{summary['holdout_rmse_mean']} +/- {summary['holdout_rmse_std']}",
        "-",
        "-",
    )
    rprint(table)
    rprint(f"[green]Saved random search results to:[/green] {out_file}")


@app.command()
def verify_stage1() -> None:
    """Run verification checks for Stage 1 deliverables."""
    rprint("[bold cyan]Verifying Stage 1 deliverables...[/bold cyan]")
    
    # 1. Processed files check
    csv_file = Path("data/processed/concrete_cleaned.csv")
    manifest_file = Path("data/processed/splits_manifest.json")
    if not csv_file.exists() or not manifest_file.exists():
        rprint("[yellow]Processed files not found. Running audit first...[/yellow]")
        audit()

    df, manifest = load_processed_data(csv_file, manifest_file)
    assert len(df) == 1030, f"Expected 1030 rows, got {len(df)}"
    assert len(manifest["cv_folds"]) == 5, f"Expected 5 CV folds, got {len(manifest['cv_folds'])}"
    rprint("[green][OK] Processed data and 5-fold split manifest verified.[/green]")

    # 2. Check baselines
    baseline_file = Path("results/baseline/default_baseline.json")
    if not baseline_file.exists():
        rprint("[yellow]Baseline results not found. Running baseline...[/yellow]")
        baseline()
    with baseline_file.open("r", encoding="utf-8") as f:
        base_data = json.load(f)
    assert "default_svr" in base_data, "Missing default_svr in baseline results"
    rprint(f"[green][OK] Default SVR baseline verified (Holdout RMSE: {base_data['default_svr']['holdout_metrics']['rmse']}).[/green]")

    rprint("[bold green]All Stage 1 verification checks PASSED successfully![/bold green]")


if __name__ == "__main__":
    app()
