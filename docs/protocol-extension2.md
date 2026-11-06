# Extension 2 protocol: ARD kernel search space and split-replicated DE vs Random Search

Date: 6 November 2026. Written and committed **before** any Extension 2 run.
The frozen protocol and evidence (`docs/protocol.md`, `results/final/`, `results/de/`,
`results/baseline/`) and Extension 1 (`docs/protocol-extension.md`, `results/extension/`) are unchanged.

## Motivation and disclosure

Extension 1 found DE only 0.13 MPa below Random Search on `log_age` (3-D search space,
300 calls, one split), a gap smaller than seed spread. Two questions follow.

* **E2a (search-space dimension).** Random Search degrades faster than DE as dimension grows.
  An unsaved development-only probe (CV only, no holdout access, one DE run, ~1,350 calls) of an RBF kernel with one
  gamma per feature (ARD) gave mean CV RMSE 4.49 MPa versus about 4.97 for the shared-gamma
  kernel. That probe motivated this experiment and contained no Random Search comparison.
  The holdout was also already inspected in Stage 1 and in Extension 1.
* **E2b (is the 0.13 MPa gap real?).** Repeat the `log_age` Random Search vs DE comparison over
  new outer group splits to estimate the gap's size and spread across partitions.

Five optimizer seeds and few splits support only descriptive claims; no significance test is claimed.

## Fixed (identical to the earlier protocols)

`log_age` features (seven ingredients + ln age); fold-local StandardScaler + RBF-SVR; mean
5-fold group CV RMSE as fitness; log10 bounds C [-2, 4], epsilon [-3, 1], every gamma [-5, 1];
DE/rand/1/bin with F = 0.8, CR = 0.9, deferred updates, clipping; optimizer seeds 11, 22, 33, 44, 55;
selection by lowest CV RMSE only; one holdout evaluation after all selections are frozen.

## E2a: ARD experiment (main split)

ARD kernel: after StandardScaler each column j is multiplied by sqrt(gamma_j) and the SVR uses
gamma = 1, i.e. k(x, x') = exp(-sum_j gamma_j (x_j - x'_j)^2). With all gamma_j equal this is
the ordinary RBF-SVR. Search vector: (log C, log epsilon, log gamma_1..log gamma_8) = 10-D.

Budget 1,500 calls including initialization for every run (larger than 300 because the space is 10-D).
DE population = 5 x dimension: 50 (10-D) and 15 (3-D control), both dividing 1,500.
Runs, each x 5 seeds, validation only:

| Space | Method |
|---|---|
| shared gamma (3-D, control for budget) | Random Search, DE/rand/1/bin |
| ARD gamma (10-D) | Random Search, DE/rand/1/bin |

Headline comparison: ARD Random Search vs ARD DE at the same budget. The shared-gamma 1,500-call
control shows whether any gain comes from the ARD kernel or merely from the larger budget.
Reference rows (reused, not rerun): Default SVR on `log_age` and the 300-call shared-gamma
Random Search / DE from Extension 1.

## E2b: split replication

Five new group-disjoint outer splits made with the same function and sizes as the original
(20% holdout, GroupKFold with 5 folds on the remaining development rows), using
`random_state` 101-105 instead of 42. Holdout indices of different splits overlap
and overlap the original holdout, so splits are not independent. For each split:
Default SVR, Random Search and DE/rand/1/bin on `log_age`, 300 calls, 5 seeds.

Per split, d = (mean-over-seeds holdout RMSE of Random Search) - (same for DE); positive favours DE.
Report d for each split, mean and SD of d over the five new splits and over all six
(new + original), a 95% t-interval over the six (approximate, splits are dependent), the count of splits where d > 0,
and the same for validation RMSE.

## Outputs

`results/extension2/` (new directory, never overwritten, own checksum file) and new tag
`extension2-2026-11-06`. Existing tags are not moved. Runtimes are measured under
parallel execution and are indicative only.
