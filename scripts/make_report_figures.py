"""Regenerate the extra report/PPT charts from saved evidence (no training).

Usage: uv run python scripts/make_report_figures.py evidence|extension|extension2|tables
`evidence` reads the frozen data/results; `extension` reads results/extension/;
`extension2` reads results/extension2/.
Outputs go to report/assets/.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from concrete_strength.data import FEATURE_COLUMNS, TARGET_COLUMN

OUT = Path("report/assets")
GRAY, BLUE, ORANGE, GREEN, RED = "#9e9e9e", "#4c78a8", "#f58518", "#54a24b", "#e45756"
plt.style.use("seaborn-v0_8-whitegrid")


def load_data() -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv("data/processed/concrete_cleaned.csv")
    manifest = json.loads(Path("data/processed/splits_manifest.json").read_text())
    return df, manifest


def evidence_figures() -> None:
    df, manifest = load_data()
    dev = df.iloc[manifest["development_indices"]]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].scatter(dev["age"], dev[TARGET_COLUMN], s=10, alpha=0.5, color=BLUE)
    axes[0].set(xscale="log", xlabel="Age (days, log scale)", ylabel="Compressive strength (MPa)",
                title="Strength vs age: gains flatten at later ages")
    axes[1].hist(dev[TARGET_COLUMN], bins=30, color=BLUE, edgecolor="white")
    axes[1].set(xlabel="Compressive strength (MPa)", ylabel="Development rows",
                title="Target distribution (826 development rows)")
    fig.tight_layout()
    fig.savefig(OUT / "eda_age_strength.png", dpi=180)
    plt.close(fig)

    corr = dev[FEATURE_COLUMNS + [TARGET_COLUMN]].corr()
    labels = ["cement", "slag", "fly ash", "water", "SP", "coarse", "fine", "age", "strength"]
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    image = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set(xticks=range(9), yticks=range(9), xticklabels=labels, yticklabels=labels,
           title="Pearson correlation (development rows)")
    ax.grid(False)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    for i in range(9):
        for j in range(9):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(corr.iloc[i, j]) > 0.6 else "black")
    fig.colorbar(image, ax=ax, shrink=0.8, label="correlation")
    fig.tight_layout()
    fig.savefig(OUT / "correlation_heatmap.png", dpi=180)
    plt.close(fig)

    de = json.loads(Path("results/de/de_search_results.json").read_text())["runs"]
    rs = json.loads(Path("results/baseline/random_search_results.json").read_text())["runs"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharex=True, sharey=True)
    for ax, runs, name in ((axes[0], rs, "Random Search"), (axes[1], de, "DE/rand/1/bin")):
        pts = np.array([h["log_params"] for run in runs for h in run["history"]])
        rmse = np.array([h["mean_cv_rmse"] for run in runs for h in run["history"]])
        sc = ax.scatter(pts[:, 0], pts[:, 1], c=np.minimum(rmse, 12), s=7, cmap="viridis_r", vmin=5.8, vmax=12)
        ax.set(title=f"{name}: 1,500 candidates (5 seeds)", xlabel=r"$\log_{10} C$")
    axes[0].set_ylabel(r"$\log_{10} \gamma$")
    fig.colorbar(sc, ax=axes, label="CV RMSE (MPa, capped at 12)")
    fig.savefig(OUT / "search_space.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def extension_figures() -> None:
    final = json.loads(Path("results/final/final_results.json").read_text())["comparison"]
    ext = json.loads(Path("results/extension/extension_results.json").read_text())
    agg = {(a["feature_set"], a["method"]): a for a in ext["aggregates"]}
    search = json.loads(Path("results/extension/extension_search.json").read_text())["runs"]

    # Representation x method
    raw = {"Default SVR": (final["default_svr"]["holdout"]["rmse"], 0.0),
           "Random Search": (final["random_search"]["holdout"]["rmse"]["mean"], final["random_search"]["holdout"]["rmse"]["std"]),
           "DE": (final["de"]["holdout"]["rmse"]["mean"], final["de"]["holdout"]["rmse"]["std"])}
    new = {"Default SVR": (ext["default_svr"]["log_age"]["holdout_metrics"]["rmse"], 0.0),
           "Random Search": (agg["log_age", "RandomSearch"]["holdout_rmse"]["mean"], agg["log_age", "RandomSearch"]["holdout_rmse"]["std"]),
           "DE": (agg["log_age", "rand/1/bin"]["holdout_rmse"]["mean"], agg["log_age", "rand/1/bin"]["holdout_rmse"]["std"])}
    fig, ax = plt.subplots(figsize=(8, 5))
    width = 0.36
    for k, (label, vals, color) in enumerate((("Raw features (frozen)", raw, GRAY), ("log(age) features", new, BLUE))):
        xs = np.arange(3) + (k - 0.5) * width
        ax.bar(xs, [v[0] for v in vals.values()], width, yerr=[v[1] for v in vals.values()], capsize=4, label=label, color=color)
        for x, v in zip(xs, vals.values()):
            ax.text(x, v[0] + v[1] + 0.15, f"{v[0]:.3f}", ha="center", fontsize=9)
    ax.set(xticks=range(3), xticklabels=list(raw), ylabel="Holdout RMSE (MPa)",
           title="Same input representation for all three methods")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "representation_comparison.png", dpi=180)
    plt.close(fig)

    # DE variants: convergence + holdout
    methods = [("RandomSearch", "Random Search", GRAY), ("rand/1/bin", "DE rand/1/bin", ORANGE),
               ("current-to-best/1/bin", "DE current-to-best/1", GREEN), ("jDE", "jDE", RED)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for key, label, color in methods:
        curves = np.array([[h["best_so_far_rmse"] for h in r["history"]] for r in search
                           if r["feature_set"] == "log_age" and r["method"] == key])
        calls = np.arange(1, curves.shape[1] + 1)
        axes[0].plot(calls, curves.mean(0), color=color, label=label)
        axes[0].fill_between(calls, curves.min(0), curves.max(0), color=color, alpha=0.15)
    axes[0].set(xlabel="Objective calls", ylabel="Best-so-far CV RMSE (MPa)", ylim=(4.8, 6.0),
                title="log(age) convergence (mean, min-max over 5 seeds)")
    axes[0].legend()
    rows = methods + [("ratios", "DE rand/1 + water ratios", BLUE)]
    for i, (key, label, color) in enumerate(rows):
        a = agg["log_age_ratios", "rand/1/bin"] if key == "ratios" else agg["log_age", key]
        axes[1].barh(i, a["holdout_rmse"]["mean"], xerr=a["holdout_rmse"]["std"], color=color, capsize=4)
        axes[1].text(a["holdout_rmse"]["mean"] + a["holdout_rmse"]["std"] + 0.03, i, f'{a["holdout_rmse"]["mean"]:.3f}', va="center", fontsize=9)
    axes[1].set(yticks=range(len(rows)), yticklabels=[r[1] for r in rows], xlabel="Holdout RMSE (MPa)",
                title="Holdout RMSE (mean $\\pm$ SD, 5 seeds)")
    axes[1].set_xlim(left=min(a["holdout_rmse"]["mean"] for a in ext["aggregates"]) - 0.5)
    axes[1].invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT / "de_variants.png", dpi=180)
    plt.close(fig)

    # Demonstration predictions
    df, manifest = load_data()
    demo = ext["demonstration"]
    run = next(r for r in ext["runs"] if (r["feature_set"], r["method"], r["seed"]) == (demo["feature_set"], demo["method"], demo["seed"]))
    actual = df[TARGET_COLUMN].to_numpy()[manifest["holdout_indices"]]
    pred = np.asarray(run["holdout_predictions"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    axes[0].scatter(actual, pred, s=14, alpha=0.6, color=BLUE)
    lim = [min(actual.min(), pred.min()), max(actual.max(), pred.max())]
    axes[0].plot(lim, lim, "k--", lw=1)
    axes[0].set(xlabel="Actual strength (MPa)", ylabel="Predicted strength (MPa)",
                title=f"{demo['method']} / {demo['feature_set']} seed {demo['seed']}")
    axes[1].scatter(pred, actual - pred, s=14, alpha=0.6, color=ORANGE)
    axes[1].axhline(0, color="k", lw=1)
    axes[1].set(xlabel="Predicted strength (MPa)", ylabel="Residual (MPa)",
                title=f"Holdout RMSE {demo['holdout']['rmse']:.3f} MPa")
    fig.tight_layout()
    fig.savefig(OUT / "extension_prediction.png", dpi=180)
    plt.close(fig)


def extension2_figures() -> None:
    """ARD search-space comparison and per-split Random Search minus DE gap (results/extension2/)."""
    ard = json.loads(Path("results/extension2/ard_results.json").read_text())["aggregates"]
    labels = {("shared", "RandomSearch"): "Shared \u03b3 (3-D)\nRandom Search", ("shared", "rand/1/bin"): "Shared \u03b3 (3-D)\nDE",
              ("ard", "RandomSearch"): "ARD (10-D)\nRandom Search", ("ard", "rand/1/bin"): "ARD (10-D)\nDE"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, key, title in zip(axes, ("validation_rmse", "holdout_rmse"), ("Validation RMSE (selection metric)", "Holdout RMSE (scored once)")):
        for i, a in enumerate(ard):
            ax.bar(i, a[key]["mean"], yerr=a[key]["std"], capsize=4, color=GRAY if a["method"] == "RandomSearch" else BLUE)
            ax.text(i, a[key]["mean"] + a[key]["std"] + 0.03, f"{a[key]['mean']:.3f}", ha="center", fontsize=9)
        ax.set_xticks(range(len(ard)), [labels[a["space"], a["method"]] for a in ard], fontsize=9)
        ax.set(ylim=(4.0, 5.9), ylabel="RMSE (MPa)", title=title)
    fig.suptitle("1,500 calls per run, mean \u00b1 SD over five seeds (grey: Random Search, blue: DE)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "ard_comparison.png", dpi=180)
    plt.close(fig)

    rep = json.loads(Path("results/extension2/replication_results.json").read_text())
    rows = [(str(s["split"]), s["d_validation"], s["d_holdout"]) for s in rep["per_split"]]
    rows.append(("42 (original)", rep["original_split"]["d_validation"], rep["original_split"]["d_holdout"]))
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.bar(x - 0.2, [r[1] for r in rows], 0.4, color=GRAY, label="Validation (selection metric)")
    ax.bar(x + 0.2, [r[2] for r in rows], 0.4, color=BLUE, label="Holdout")
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(x, [r[0] for r in rows])
    ax.set(xlabel="Outer split (random_state)", ylabel="Random Search \u2212 DE RMSE (MPa)",
           title="Positive favours DE; five-seed means per split (splits overlap)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "replication_gap.png", dpi=180)
    plt.close(fig)


def extension_table() -> None:
    """Write report/tables/extension.tex from the saved extension and frozen results."""
    final = json.loads(Path("results/final/final_results.json").read_text())["comparison"]
    ext = json.loads(Path("results/extension/extension_results.json").read_text())
    agg = {(a["feature_set"], a["method"]): a for a in ext["aggregates"]}

    def pm(a: dict) -> str:
        return f"\\mbox{{${a['mean']:.4f}\\pm{a['std']:.4f}$}}"

    def row(label: str, a: dict) -> str:
        return (f"{label} & {pm(a['validation_rmse'])} & {pm(a['holdout_rmse'])} & "
                f"{pm(a['holdout_mae'])} & {pm(a['holdout_r2'])}\\\\")

    def frozen(key: str) -> dict:
        c = final[key]
        return {"validation_rmse": c["validation"], **{f"holdout_{m}": c["holdout"][m] for m in ("rmse", "mae", "r2")}}

    d_raw, d_log = final["default_svr"], ext["default_svr"]["log_age"]
    lines = [
        r"\begin{table}[htbp]\centering\caption[Extension results]{Raw features (frozen) versus ln(age) features. Tuned values are five-seed mean $\pm$ sample SD on the same 204 holdout rows; default rows show the single five-fold CV mean and the single holdout score.}\label{tab:extension}\footnotesize\setlength{\tabcolsep}{2pt}\begin{tabularx}{\textwidth}{lCCCC}\toprule Model&Validation RMSE&Holdout RMSE&Holdout MAE&Holdout $R^2$\\\midrule",
        r"\multicolumn{5}{l}{\textit{Raw features (frozen results)}}\\",
        f"Default SVR & {d_raw['cv']['mean_rmse']:.4f} & {d_raw['holdout']['rmse']:.4f} & {d_raw['holdout']['mae']:.4f} & {d_raw['holdout']['r2']:.4f}\\\\",
        row("Random Search", frozen("random_search")), row("DE rand/1/bin", frozen("de")),
        r"\midrule\multicolumn{5}{l}{\textit{ln(age) features (extension)}}\\",
        f"Default SVR & {d_log['cv_metrics']['mean_rmse']:.4f} & {d_log['holdout_metrics']['rmse']:.4f} & {d_log['holdout_metrics']['mae']:.4f} & {d_log['holdout_metrics']['r2']:.4f}\\\\",
        row("Random Search", agg["log_age", "RandomSearch"]), row("DE rand/1/bin", agg["log_age", "rand/1/bin"]),
        r"\midrule\multicolumn{5}{l}{\textit{DE ablations on ln(age) (same 300-call budget)}}\\",
        row("DE current-to-best/1/bin", agg["log_age", "current-to-best/1/bin"]), row("jDE", agg["log_age", "jDE"]),
        row("DE rand/1/bin + water ratios", agg["log_age_ratios", "rand/1/bin"]),
        r"\bottomrule\end{tabularx}\end{table}",
    ]
    Path("report/tables/extension.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    {"evidence": evidence_figures, "extension": extension_figures, "extension2": extension2_figures, "tables": extension_table}[sys.argv[1]]()
