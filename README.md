# Concrete Strength Prediction with Differential Evolution–Optimized SVR

Bio-Inspired Algorithms semester AAT project for a four-member team.

| Member | USN |
|---|---|
| R V Abhishek | 1BM23CD047 |
| Sushanth S | 1BM23CD063 |
| Ullas N | 1BM23CD067 |
| Vedantha V V | 1BM23CD069 |

**Full title:** Concrete Compressive Strength Prediction Using Differential Evolution–Optimized Support Vector Regression.

## Objective

Evaluate whether Differential Evolution (DE) improves the hyperparameters of an RBF Support Vector Regression (SVR) model for predicting concrete compressive strength. Compare default SVR, random-search tuning, and DE tuning using the same data splits and comparable search budgets.

Status: Stages 1–3 and the technical closeout are complete. The [45-page report](report/concrete-strength-de-svr-report.pdf) and [28-slide editable presentation](presentation/concrete-strength-de-svr-presentation.pptx) have been prepared and locally validated from the frozen evidence. See [deliverable validation](docs/deliverable-validation.md) for checks and remaining signatures, access and submission tasks. Original model selections, holdout results and technical evidence are preserved.

## Repository layout

```text
data/
  raw/                  Original UCI spreadsheet and readme; keep unchanged
  source/               Original downloaded dataset ZIP
docs/
  project-brief.md       Agreed topic and proposed experimental scope
  submission-checklist.md  Professor's presentation and report requirements
references/
  examples/             Professor-provided stock-price report and PPT examples
  rubrics/              Original AAT marking rubric
report/                 Our report sources and final report
presentation/           Our slide sources and final PPT
results/                Experiment tables, plots, and run metadata
```

The files in `references/examples/` concern a different project. Use them as structural references; they are not this project's report or results.

## Dataset

The UCI Concrete Compressive Strength dataset contains 1,030 observations, eight numerical input features, and one target: compressive strength in MPa. Inputs describe concrete ingredients and curing age. The source documentation reports no missing values.

- Working source file: `data/raw/Concrete_Data.xls`
- Original dataset documentation: `data/raw/Concrete_Readme.txt`
- Download archive: `data/source/uci-concrete-compressive-strength.zip`
- Dataset page: <https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength>
- Dataset DOI: <https://doi.org/10.24432/C5PK67>

Retain the original attribution and notices. Cite I-Cheng Yeh, “Modeling of strength of high-performance concrete using artificial neural networks,” *Cement and Concrete Research*, 28(12), 1797–1808, 1998, alongside the dataset citation.

## Planned workflow

1. Validate the spreadsheet schema and inspect duplicate records before fixing the split.
2. Establish a reproducible default-SVR baseline.
3. Implement DE mutation, crossover, selection, and bound handling explicitly.
4. Compare DE and random search with matching search spaces and candidate-evaluation budgets.
5. Record RMSE, MAE, R², runtime, convergence, and variation across optimizer seeds.
6. Prepare the report and presentation from the measured evidence package.

Use Python with `uv` for dependency management and execution. The surrounding BIO lab environment is separate from this repository.

```sh
uv sync --locked
uv run pytest -q
uv run concrete-strength verify-stage1
```

Stage 2 commands:

```sh
uv run concrete-strength pilot --output-dir results/pilot-rerun
uv run concrete-strength synthetic-benchmarks --output-dir results/synthetic-rerun
uv run concrete-strength de-search
```

The pilot and synthetic checks are saved under `results/pilot/`. `de-search` selects candidates using validation only and saves to `results/de/de_search_results.json`. `finalize-experiments` refits those frozen candidates on development data, evaluates the fixed holdout, and writes the complete package under `results/final/`. These commands refuse to overwrite existing outputs.

Read the [protocol and final handoff](docs/protocol.md), [work log](docs/work-log.md), and [results guide](results/README.md) before preparing deliverables. The existing baseline/random-search artifacts already include holdout evaluations; preserve this chronology when reporting results.

See the [detailed four-member implementation plan and task network](docs/implementation-plan.md), [project scope](docs/project-brief.md), and [submission checklist](docs/submission-checklist.md).

**Extension (5 Nov 2026).** A pre-registered follow-up ([protocol](docs/protocol-extension.md)) tests `ln(age)` input for default SVR, Random Search and DE, plus DE-variant and water-ratio ablations: `uv run concrete-strength extension-search` then `extension-finalize` write `results/extension/`. The frozen results above are unchanged. Charts and the LaTeX table regenerate with `uv run python scripts/make_report_figures.py evidence|extension|tables`; TikZ diagrams are in `report/figures/` (`sh report/scripts/render_figures.sh` makes PNGs for the slides).

**Extension 2 (6 Nov 2026).** A second pre-registered follow-up ([protocol](docs/protocol-extension2.md)) tests an ARD kernel (10-D search space, Random Search vs DE) and replicates the `ln(age)` Random Search vs DE comparison on five new outer splits: `uv run concrete-strength ext2-ard-search`, `ext2-ard-finalize`, `ext2-replication-search`, `ext2-replication-finalize` write `results/extension2/`. ARD did not improve validation RMSE; DE's small advantage over Random Search was consistent across splits (descriptive only).
