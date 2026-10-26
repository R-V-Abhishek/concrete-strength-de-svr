# Experiment results

The final evidence package is in [`final/`](final/):

- `final_results.json`: full five-seed DE histories, frozen candidates, holdout
  predictions/residuals, aggregate metrics, learning-curve data, and provenance.
- `metrics.csv`: per-seed holdout RMSE, MAE, and R² for DE and Random Search.
- `convergence.png`: validation convergence against objective-call number.
- `holdout_rmse_comparison.png`: default SVR versus matched-search holdout RMSE.
- `prediction_residuals.png`: actual/predicted and residual diagnostics for the
  validation-selected best DE demonstration (seed 11).
- `learning_curve.png`: development-only learning curve for that demonstration.

## Reproduction

From the repository root, with the locked environment:

```powershell
uv sync --locked
uv run pytest -q
uv run concrete-strength de-search
uv run concrete-strength finalize-experiments
```

`de-search` is validation-only. It writes five 300-call DE runs and refuses to
overwrite an existing result. `finalize-experiments` refits those frozen
validation selections once on the full development set and evaluates the fixed
204-row holdout. It does not use holdout scores for selection.

## Final aggregate results

| Method | Validation RMSE (mean ± SD) | Holdout RMSE (mean ± SD) | Holdout MAE | Holdout R² |
|---|---:|---:|---:|---:|
| Default RBF-SVR | 10.3140 ± 0.8743 | 9.9069 | 7.8854 | 0.5755 |
| Random Search | 5.9399 ± 0.0287 | 6.2328 ± 0.1194 | 4.3502 ± 0.0253 | 0.8319 ± 0.0064 |
| DE/rand/1/bin | 5.8797 ± 0.0198 | 6.2250 ± 0.1104 | 4.3143 ± 0.0526 | 0.8324 ± 0.0060 |

The DE mean holdout RMSE is 0.12% lower than Random Search and 37.2% lower
than the default SVR. These are results on one fixed holdout and five optimizer
seeds, not a significance or state-of-the-art claim.
