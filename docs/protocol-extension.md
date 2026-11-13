# Extension protocol: log-age representation and DE-variant ablation

Date: 5 November 2026. Written and committed **before** any extension search is run.
The frozen protocol (`docs/protocol.md`) and evidence (`results/final/`, `results/de/`,
`results/baseline/`) are unchanged and remain the primary report evidence.

## Motivation and disclosure

A development-only probe (scipy DE, seed 11, ~150 calls, five saved CV folds, no holdout
access, nothing saved) gave mean CV RMSE 5.85 MPa on raw features versus 4.97 MPa with
age replaced by ln(age). The representation, not the optimizer, limited the frozen results.
This extension tests that finding under the full matched protocol. The probe is the reason
log-age was chosen; the holdout was also already inspected in Stage 1 (baseline/Random Search).
Five optimizer seeds on one partition support no significance claim.

## Fixed (identical to the frozen protocol)

Saved split manifest and five group-disjoint CV folds; fold-local StandardScaler + RBF-SVR;
log10 bounds C [-2,4], gamma [-5,1], epsilon [-3,1]; fitness = mean CV RMSE (evaluator
unchanged); budget 300 calls including initialization; seeds 11, 22, 33, 44, 55; DE
population 15, deferred updates, clipping, equal-budget Random Search.

## Feature sets (row-wise, deterministic, applied before scaling)

| Name | Inputs |
|---|---|
| `raw` | the eight original features (frozen results, reused as-is) |
| `log_age` | seven ingredients + ln(age) |
| `log_age_ratios` | `log_age` + water/cement + water/(cement+slag+fly ash) (ablation) |

## Runs (all 300 calls x 5 seeds, validation only)

1. Default SVR (C=1, gamma=scale, epsilon=0.1) on `log_age` and `log_age_ratios`.
2. Random Search and DE/rand/1/bin on `log_age` (headline: same representation for all three methods).
3. DE/rand/1/bin on `log_age_ratios`.
4. DE ablation on `log_age`: current-to-best/1/bin and jDE (self-adaptive F, CR; tau1 = tau2 = 0.1,
   F in [0.1, 1.0], CR in [0, 1], rand/1/bin base), same budget, deferred updates and clipping.

Raw-feature comparison rows reuse the frozen RS/DE/default results (Windows original runs).

## Selection and evaluation

Each run's candidate is its best-CV-RMSE call. All 25 selections are frozen in
`results/extension/extension_search.json` before `extension-finalize` refits each once on the
full development set and scores the 204 holdout rows. The headline comparison is
default vs Random Search vs DE/rand/1/bin on `log_age`. Variants, ratios and raw rows are
reported as ablations; no result may be used to change the protocol or pick a seed.
Report mean +/- sample SD across seeds, plus the validation-selected demonstration
(lowest CV RMSE, ties by method name then seed).

## Outputs

`results/extension/` (new directory, never overwritten), separate checksum file, new tag
`extension-2026-11-05`. The existing technical tag is not moved.
