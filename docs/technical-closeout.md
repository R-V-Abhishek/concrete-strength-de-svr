# Technical closeout and report/PPT handoff

Date: 27 October 2026. Frozen technical tag: **`technical-closeout-2026-10-27`**.

Use the repository snapshot at this tag and the files listed below for the report
and presentation. Technical experiments are closed. Report/PPT writing, certificate
details/signatures, final upload, professor access and presentation remain Stage 4
responsibilities; this closeout does not claim those administrative tasks are done.

## 1. What was corrected and preserved

- Replaced the learning curve's ordered row-prefix samples and five folds with
  three group-disjoint development folds and seeded, nested samples of complete
  training groups at fractions 0.25, 0.50, 0.75 and 1.0. Seed is 42 plus fold index.
- Added training RMSE alongside validation RMSE, sample standard deviations,
  selected row IDs and group/row counts. Fixed demonstration parameters are used
  throughout; no retuning or holdout access occurs in this diagnostic.
- Added Random Search histories to the convergence chart so both methods are
  visible against the same objective-call axis.
- Preserved every original selection, holdout metric, prediction, residual,
  comparison and original experiment provenance field. Only the learning-curve
  data and diagnostic metadata changed in `final_results.json`.
- Added checks that verify the evidence and selected-model refits. Historical
  Windows paths are interpreted explicitly; CRLF/LF text conversions are checked
  by reconstructing and hashing the exact alternate byte representation. Other
  content differences fail verification. The binary XLS must match exactly.
- Added Git text line-ending rules for portable future checksums; original raw
  sources remain byte-preserved.

## 2. Approved result table

These are holdout metrics on the same 204 rows. Tuned-model means and sample SDs
are across five optimizer seeds, not independent datasets or data partitions.

| Model | RMSE, MPa | MAE, MPa | R² |
|---|---:|---:|---:|
| Default RBF-SVR | 9.9069 | 7.8854 | 0.5755 |
| Random Search–SVR | 6.2328 ± 0.1194 | 4.3502 ± 0.0253 | 0.8319 ± 0.0064 |
| DE–SVR | 6.2250 ± 0.1104 | 4.3143 ± 0.0526 | 0.8324 ± 0.0060 |

Mean validation RMSE: Random Search 5.9399 ± 0.0287 MPa; DE 5.8797 ± 0.0198 MPa.
Each method gets 300 objective calls per seed including initialization, on the same
five development folds, with seeds 11, 22, 33, 44 and 55.

**Conclusion to carry forward:** both tuning methods substantially improve default
SVR; DE reduces mean holdout RMSE by about 37.2% against default SVR. DE's difference
from Random Search is about 0.008 MPa, approximately 0.1%, so the two methods achieve
essentially equivalent holdout performance here. Do not claim statistically
significant or general algorithm superiority.

The demonstration is DE seed 11, selected by validation RMSE (5.8601 MPa), not by
its test result. Its original holdout RMSE is 6.3712 MPa; use the five-run aggregate
when describing average performance, and do not confuse the demonstration with
the lowest test-error seed.

## 3. Diagnostic interpretation

| Training-group fraction | Mean training groups | Train RMSE | Validation RMSE |
|---|---:|---:|---:|
| 0.25 | 132.67 | 2.7596 | 8.3838 |
| 0.50 | 265.67 | 3.1542 | 7.2707 |
| 0.75 | 398.00 | 3.4396 | 6.5026 |
| 1.00 | 530.67 | 3.7728 | 5.9784 |

Values are means across three diagnostic folds. Validation error decreases as
training groups increase, while a training/validation gap remains. These scores
are development diagnostics with previously selected parameters, not an additional
independent generalization estimate. They do not replace five-fold search fitness
or holdout scores. Residual plots retain all measurements, including occasional
large errors; no post-hoc outlier removal was performed.

## 4. Evidence audit and environment

`results/final/verification.json` records the executable audit, package versions,
source hashes and individual reproduction differences. It checks:

- Raw/data/config/lockfile and experiment-input checksums, with explicit
  historical Windows newline handling.
- Development/holdout/CV row and group isolation.
- All 3,000 candidate records, five seeds per method, 300 calls per seed,
  parameter bounds, fold means, best-so-far histories and validation selections.
- Per-seed CSV rows, metrics reconstructed from predictions, aggregate means and
  sample SDs, original default baseline, and validation-selected demonstration.
- Whole-group, nested learning-curve samples, three folds and aggregate scores.
- Fresh CV evaluation and holdout refitting of all five fixed DE selections in
  the locked environment, with a predeclared absolute tolerance of 0.001.

Original DE experiments used Windows/Python 3.13.1, NumPy 2.4.6, scikit-learn 1.6.1
and SciPy 1.15.3. The locked verification uses macOS/Python 3.12, NumPy 2.5.4,
scikit-learn 1.9.1 and SciPy 1.18.1. Tiny native-library/version differences are
recorded rather than replacing the original results. Rounded saved-prediction
metrics are checked separately at 0.0002 tolerance.

Independent reproduction also passed in a fresh local clone of code commit
`6e7eb0f`: new virtual environment, `uv sync --locked`, all 43 tests, the complete
selected-model evidence audit and all frozen file checksums. The offline setup
initially lacked a cached SciPy wheel; downloading the exact locked dependencies
resolved that setup issue without changing the lockfile. The clean-checkout audit
is saved as `results/closeout/fresh-checkout-verification.json`; the final handoff
adds this record and documentation/integrity metadata to that verified code.

The test suite includes 43 tests, covering the original pipeline, DE operators,
group-complete diagnostic sampling and historical checksum handling. Full
optimization was not rerun for closeout; all candidate histories were audited and
the five selected configurations were reproduced. No new model-selection decisions
were made using the holdout.

## 5. Files Vedantha should use

| File | Use |
|---|---|
| `docs/work-log.md` | Member work, chronology, methods, sources and closeout notes |
| `docs/protocol.md` | Frozen model/search protocol and limitations |
| `docs/implementation-plan.md`, `docs/submission-checklist.md` | All professor rubric, report and PPT requirements |
| `results/final/final_results.json` | Authoritative aggregate metrics, selections, predictions and corrected diagnostic |
| `results/final/metrics.csv` | Ten per-seed holdout rows for the two tuned methods |
| `results/final/learning_curve.csv` | Corrected diagnostic summary |
| `results/final/convergence.png` | Both methods' validation convergence histories |
| `results/final/holdout_rmse_comparison.png` | Default vs tuned-model means and SDs |
| `results/final/prediction_residuals.png` | Validation-selected demonstration and residuals |
| `results/final/learning_curve.png` | Three-fold training/validation learning curve |
| `results/final/verification.json`, `SHA256SUMS` | Audit evidence and frozen artifact integrity |
| `results/closeout/fresh-checkout-verification.json` | Independent clean-checkout reproduction of code commit `6e7eb0f` |

All four figures were visually inspected after regeneration. Readable labels,
units, legends, demonstration identity and displayed data were checked.

## 6. Reproduction and change policy

From a checkout of the frozen tag:

```sh
uv sync --locked
uv run pytest -q
uv run concrete-strength verify-evidence --output-path /tmp/concrete-evidence-verification.json
```

The verifier refits fixed selections; it does not perform another search or modify
published result metrics. The alternate output path keeps the frozen audit record
unchanged. The checksum manifest contains repository-root-relative paths:

```sh
shasum -a 256 -c results/final/SHA256SUMS
```

For deliberate full reproduction, use separate output folders as documented in
`results/README.md`. Do not rerun searches merely to obtain a more favorable score.
If a substantive defect requires a technical change, document the reason, rerun
affected evidence, and create a new technical tag; update report/PPT references.
