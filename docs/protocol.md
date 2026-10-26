# Frozen Stage 2 protocol

Date: 26 October 2026. Stage 1 owner: Sushanth S (1BM23CD063). Stage 2 owner: R V Abhishek (1BM23CD047). Stage 3 owner: Ullas N (1BM23CD067).

## Scope and data

Use the Stage 1 processed CSV and saved split manifest without changing rows, groups or partitioning. The raw XLS SHA-256 is `710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4`.

The dataset has 1,030 rows, 996 exact input groups, 826 development rows and 204 holdout rows. Use the five existing group-disjoint development CV folds. Fold-local StandardScaler + RBF-SVR predicts strength in MPa. The existing evaluator rounds fold RMSE/mean fitness to four decimals; both Random Search and DE use that same evaluator unchanged.

The Stage 1 baseline/random-search artifacts already contain holdout metrics. Preserve them and disclose this chronology. Stage 2 uses no holdout scores for choosing DE settings; its pilot and search command never refit on holdout. Do not describe the holdout as never previously inspected.

## Search settings

The source of truth is `configs/experiment.json`:

| Setting | Frozen value |
|---|---|
| Coordinates | log10(C), log10(gamma), log10(epsilon) |
| Bounds | [-2,4], [-5,1], [-3,1] respectively |
| Decoding | Each actual parameter is 10 raised to its coordinate |
| Fitness | Mean validation RMSE across the five saved development folds |
| DE strategy | rand/1/bin |
| Population | 15 |
| Mutation F / crossover CR | 0.8 / 0.9 |
| Donors | Three distinct indices, excluding the target |
| Boundary handling | Coordinate clipping |
| Crossover | Binomial, with one forced mutant coordinate |
| Selection | Accept trial when its fitness is no worse than the target |
| Updating | Deferred: all targets use the same frozen source generation |
| Budget | 300 calls = 15 initialization + 19 generations × 15 |
| Seeds | 11, 22, 33, 44, 55 |
| Random Search | Same coordinate box, seeds and 300 calls per seed |
| Extra local search / caching | None; repeated candidates count as calls |

Mutation: `v_i = x_r1 + 0.8 * (x_r2 - x_r3)`. Trial coordinate j comes from the mutant when `uniform(0,1) < 0.9` or `j == j_rand`; otherwise it comes from target i. Acceptance minimizes RMSE. Objective failures or nonfinite values abort clearly rather than being silently assigned an arbitrary fitness.

SVR DE results retain full-precision candidate coordinates and decoded parameters. Existing Random Search artifacts round their saved parameters. Do not silently modify those artifacts; mention this small precision difference when reproducing refits. CV fitness precision remains identical for both optimizers.

## Pilot and compute decision

The pilot uses development data only, three regenerated GroupKFold folds over the original 826 development rows, two seeds (11,22), population 6 and 24 calls per method/seed. Its four searches perform exactly 288 SVR fits. The fold lists are stored in `results/pilot/stage2_pilot.json`; assertions exclude holdout rows and overlapping groups.

| Method | Seed | Best pilot CV RMSE (MPa) | Search seconds |
|---|---:|---:|---:|
| Random Search | 11 | 6.1751 | 1.01 |
| DE | 11 | 6.1163 | 2.03 |
| Random Search | 22 | 6.5326 | 2.67 |
| DE | 22 | 5.9864 | 5.26 |

These are feasibility observations, not final five-fold performance results or a guaranteed DE advantage. Separate high-C timing probes used log coordinates `(4,-5,-3)`, `(4,1,-3)`, `(4,-1,-3)` and took about 0.04s, 0.05s and 2.95s respectively for three-fold fitness. Probe evaluations are separate diagnostics, not hidden calls in either search budget; see `results/pilot/timing_probes.json`.

**Decision:** retain the planned 300 calls and five seeds. Linear extrapolation of measured pilot search times suggests roughly ten minutes for both final methods together on this machine; allow at least a threefold buffer and monitor actual progress. This is an estimate, not a deadline guarantee: DE can visit slower regions more often as it evolves. Final tuning entails 15,000 SVR fits in total, excluding baselines/refits/diagnostics.

The pilot was run sequentially on macOS arm64, Python 3.12, NumPy 2.5.4, pandas 3.1.0, scikit-learn 1.9.1 and SciPy 1.18.1. The saved provenance includes exact Python/platform strings, source/config/lockfile checksums, base Git commit and dirty-worktree flag. Compare runtime only on the same machine/settings. Stage 1's saved Windows runtimes are historical, not fair timing comparators for this macOS pilot.

## Synthetic verification

Sphere: `f(x)=sum(x_j^2)`. Rastrigin: `f(x)=10*d+sum(x_j^2-10*cos(2*pi*x_j))`. Both have global minimum zero at the origin.

Use d=3, bounds [-5.12,5.12], the five fixed seeds and 300 calls per method. Save best-so-far histories for both DE and independent uniform Random Search. Mean best fitness across seeds was 0.067805 vs 1.041886 for Sphere, and 7.685621 vs 10.432464 for Rastrigin (DE vs Random Search). These check optimizer behavior; they do not establish a general superiority claim or require every run to reach the optimum. Raw outputs: `results/pilot/synthetic_benchmarks.json`.

## Stage 3 execution and interpretation

1. Reproduce Stage 2 tests and verify manifests/checksums. Use the locked uv environment; record machine information.
2. Run `uv run concrete-strength de-search`. It reads the frozen JSON configuration, validates matched budget/seeds, and saves all five validation-selected DE runs to `results/de/de_search_results.json`. It never computes holdout scores and refuses to overwrite existing output. Use a different `--output-dir` for a deliberate rerun.
3. Keep existing baseline/random-search results intact. For a fresh same-machine timing comparison, rerun Random Search to a separate output directory using the same fixed settings. The legacy random-search CLI evaluates holdout automatically; do not use those holdout values to change the protocol.
4. Freeze all validation-selected candidates before DE holdout refits. Use the existing `evaluate_selected_on_holdout` function with each run's full-precision decoded parameters and saved development/holdout indices. Final DE holdout evaluation is Stage 3 work, not included in this Stage 2 pilot.
5. Save per-seed and aggregate RMSE/MAE/R², predictions/residuals, runtime and provenance. Select any demonstration model by validation RMSE; break exact ties by method name then ascending seed. Never select by test performance.
6. Add required convergence, performance, residual/prediction and development-only learning curves, following the implementation plan. Build convergence plots against objective calls, including initialization.
7. Report optimizer-seed variability on one fixed holdout. Avoid unsupported significance/state-of-the-art claims. Pilot scores use three folds and must remain separate from final five-fold results.
8. Regenerate summaries from saved outputs, document exact commands, and hand the evidence to Vedantha for the report/PPT.

## Remaining administrative items and limitations

Stage 1's technical handoff passes; this does not independently verify registration, presentation booking, professor repository/Drive access, certificate details or signatures. Confirm these separately. The repository remains private.

The existing XLS reader emits a pandas deprecation warning; it currently loads correctly. Preserve the functioning reader and locked versions for this submission rather than changing the data ingestion path during DE work.

References: the original DE paper by Storn and Price (1997), DOI `10.1023/A:1008202821328`; UCI dataset DOI `10.24432/C5PK67`; existing scikit-learn evaluator and original dataset readme. No external optimization library replaces the implemented operators.
