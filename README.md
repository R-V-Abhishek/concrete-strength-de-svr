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

Status: dataset and professor-provided references organized; implementation and experimental results are pending. No performance improvement is claimed yet.

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
6. Complete the report and presentation from measured results.

Use Python with `uv` for dependency management and execution. Project dependencies and run commands will be added with implementation; no training pipeline is included in this setup commit. The surrounding BIO lab environment is separate from this repository.

See the [detailed four-member implementation plan and task network](docs/implementation-plan.md), [project scope](docs/project-brief.md), and [submission checklist](docs/submission-checklist.md).
