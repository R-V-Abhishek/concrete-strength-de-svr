# Project Work Log: Concrete Strength DE-SVR

Project: **Concrete Compressive Strength Prediction Using Differential Evolution–Optimized Support Vector Regression**  
Sequential Workflow: Stage 1 (Sushanth) → Stage 2 (Abhishek) → Stage 3 (Ullas) → Stage 4 (Vedantha)
Working Branch: `S_branch`  

---

## Stage 1: Setup, Data Ingestion, Evaluation Pipeline & Baselines

- **Owner:** Sushanth S (USN: 1BM23CD063)
- **Status:** Completed
- **Tasks Assigned:** T01, T02, T03, T04, T05
- **Working Branch:** `S_branch`
- **Start Time:** 26 October 2026
- **Completion Time:** 26 October 2026

### 1. Implementation Details & Decisions
- **Environment & Tooling:** Created isolated Python virtual environment `.venv` on Windows using Python 3.11.9. Installed and locked dependencies: `numpy`, `pandas`, `xlrd`, `scikit-learn`, `matplotlib`, `typer`, `pytest`.
- **Data Ingestion & Provenance:**
  - Raw source file: `data/raw/Concrete_Data.xls`
  - Expected: 1,030 instances, 8 input variables (cement, slag, fly ash, water, superplasticizer, coarse aggregate, fine aggregate, age), 1 target (compressive strength in MPa).
  - Raw checksum and audited schema recorded below.
- **Auditing & Grouping Strategy:**
  - Duplicate inputs with differing targets or identical recipes are preserved.
  - Formed exact 8-input recipe tuples to assign a deterministic `group_id`.
  - Group leakage prevention: partitioned groups using `GroupShuffleSplit(test_size=0.20, random_state=42)` for holdout, and `GroupKFold(n_splits=5)` for cross-validation on the development set. No group crosses between train and validation or holdout test sets.
- **Pipeline & Scaler:**
  - Fold-local scaling using `StandardScaler` inside `sklearn.pipeline.Pipeline` with `SVR(kernel='rbf')`.
  - No global pre-scaling of inputs or target; target remains in MPa.
- **Evaluation Interface:**
  - Unified interface: `evaluate_hyperparameters(log_C, log_gamma, log_epsilon) -> (mean_cv_rmse, fold_rmses)`
  - Parameter decoding: $C = 10^{\text{log\_C}}$, $\gamma = 10^{\text{log\_gamma}}$, $\epsilon = 10^{\text{log\_epsilon}}$.
- **Baselines:**
  - Dummy Regressor baseline: `DummyRegressor(strategy='mean')`.
  - Default SVR baseline: $C = 1.0$, $\gamma = \text{'scale'}$, $\epsilon = 0.1$.
  - Equal-budget Random Search: Uniform random search in log space: $\log_{10}(C) \in [-2, 4]$, $\log_{10}(\gamma) \in [-5, 1]$, $\log_{10}(\epsilon) \in [-3, 1]$. Budget: 300 evaluations $\times$ 5 seeds (`[11, 22, 33, 44, 55]`).

### 2. Exact Commands Run
- Virtual environment creation: `python -m venv .venv`
- Package installation: `.venv\Scripts\pip install numpy pandas xlrd scikit-learn matplotlib typer pytest`
- Audit and split: `.venv\Scripts\python -m concrete_strength.cli audit`
- Baselines run: `.venv\Scripts\python -m concrete_strength.cli baseline`
- Random search run: `.venv\Scripts\python -m concrete_strength.cli random-search`
- Tests execution: `.venv\Scripts\pytest tests/`

### 3. Verification & Actual Outcomes
- **Raw File Verification:**
  - File path: `data/raw/Concrete_Data.xls`
  - SHA-256 Checksum: `710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4`
  - Total Instances: 1,030 rows, 9 columns (8 inputs + 1 compressive strength in MPa)
  - Missing/NaN count: 0 across all attributes
- **Auditing & Grouping Results:**
  - Exact 9-column duplicate rows: 25
  - 8-input recipe duplicate rows: 34
  - Unique recipe groups: 996
  - Distinct test results with identical mixture recipe & age: 9
- **Data Splits:**
  - Partitioning method: `GroupShuffleSplit` (test_size=0.20, random_state=42) and `GroupKFold` (n_splits=5)
  - Development Set: 826 rows (796 unique groups)
  - Holdout Test Set: 204 rows (200 unique groups)
  - Group Leakage: Confirmed 0 overlapping groups between dev and holdout, and 0 overlapping groups across all 5 CV folds.
  - Saved to: `data/processed/concrete_cleaned.csv` and `data/processed/splits_manifest.json`
- **Baseline Evaluation Metrics:**
  - **Dummy Regressor (Mean Prediction):**
    - 5-Fold CV RMSE: 17.0246 ± 1.0993 MPa
    - Holdout Test RMSE: 15.2409 MPa
    - Holdout Test MAE: 12.3745 MPa
    - Holdout Test R²: -0.0046
  - **Default RBF-SVR (C=1.0, gamma="scale", epsilon=0.1):**
    - 5-Fold CV RMSE: 10.3140 ± 0.8743 MPa
    - Holdout Test RMSE: 9.9069 MPa
    - Holdout Test MAE: 7.8854 MPa
    - Holdout Test R²: 0.5755
    - Refit runtime: ~0.02s
- **Random Search (300 evaluations per seed, 5 seeds: 11, 22, 33, 44, 55):**
  - **Seed 11:** Best Val RMSE = 5.9027 | Best C = 7320.67, gamma = 0.03339, epsilon = 1.0858 | Holdout RMSE = 6.3884, R² = 0.8235 | Runtime = 102.2s
  - **Seed 22:** Best Val RMSE = 5.9449 | Best C = 1014.28, gamma = 0.04320, epsilon = 0.1932 | Holdout RMSE = 6.0950, R² = 0.8393 | Runtime = 93.0s
  - **Seed 33:** Best Val RMSE = 5.9821 | Best C = 1304.58, gamma = 0.03859, epsilon = 0.0041 | Holdout RMSE = 6.1456, R² = 0.8367 | Runtime = 129.1s
  - **Seed 44:** Best Val RMSE = 5.9294 | Best C = 4077.84, gamma = 0.04440, epsilon = 0.0053 | Holdout RMSE = 6.3112, R² = 0.8277 | Runtime = 154.5s
  - **Seed 55:** Best Val RMSE = 5.9405 | Best C = 2014.85, gamma = 0.04960, epsilon = 0.0053 | Holdout RMSE = 6.2238, R² = 0.8325 | Runtime = 162.3s
  - **Summary (Mean ± Std):**
    - 5-Fold Validation RMSE: 5.9399 ± 0.0287 MPa
    - Holdout Test RMSE: 6.2328 ± 0.1194 MPa (37.1% RMSE reduction relative to Default SVR baseline of 9.9069 MPa)
  - Saved to: `results/baseline/random_search_results.json`
- **Automated Test Suite:**
  - Ran `pytest tests/` (14 passing tests across `test_data.py`, `test_evaluation.py`, `test_search.py`, `test_integration.py`).
  - Verified zero group overlap, pipeline scaling isolation, bounds enforcement, call budget accounting, and output schema.
- **Stage 1 Status:** Complete and verified. Ready for Stage 2 handoff.

### 4. Problems Encountered & Resolutions
- Git branch creation required resolving permissions on `.git` directory; checked out `S_branch`.
- Direct global package installation avoided in favor of local `.venv` as requested.
- `xlrd` library installed to parse legacy `.xls` format.

### 5. Sources Used
- I-Cheng Yeh (1998), "Modeling of strength of high performance concrete using artificial neural networks", Cement and Concrete Research, Vol. 28, No. 12, pp. 1797-1808.
- UCI Machine Learning Repository: Concrete Compressive Strength dataset. DOI: 10.24432/C5PK67.
- Scikit-Learn SVR & Cross-Validation Documentation: https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html

### 6. Handoff to Stage 2 (R V Abhishek)
- **Handoff Commit:** `e27e6e0`
- **Files to Read:** `configs/experiment.json`, `src/concrete_strength/evaluation.py`, `src/concrete_strength/search.py`
- **Handoff Command to Run:**
  ```powershell
  .venv\Scripts\pytest tests/
  .venv\Scripts\python -m concrete_strength.cli verify-stage1
  ```

---

## Stage 2: Differential Evolution (DE) Implementation, Tests & Pilot

- **Owner:** R V Abhishek (USN: 1BM23CD047)
- **Status:** Completed locally; ready for Stage 3 technical handoff
- **Tasks Assigned:** T06, T07, T08, T09
- **Date:** 26 October 2026
- **Working branch / source handoff:** `S_branch`, based on `1ab359a` (Stage 1 implementation `e27e6e0`).
- **Ownership correction:** Sushanth completed Stage 1; Abhishek completed Stage 2. The original handoff log had the old assignment; names/USNs in this document, the plan and the brief were corrected to match the actual ownership. Historical Windows installation commands/results above are retained as reported, not represented as commands rerun on this Mac.

### 1. Implementation and decisions

- Implemented explicit NumPy `DE/rand/1/bin` in `src/concrete_strength/de.py`, with separate donor selection, differential mutation, clipping, binomial crossover and greedy selection functions.
- Three distinct donors exclude the target; F=0.8, CR=0.9; force one mutant coordinate. Deferred updates keep the source population frozen for each generation.
- Generic scalar-objective DE also supports synthetic test functions. SVR integration uses Stage 1's `evaluate_hyperparameters` unchanged: exactly the same fold-local scaling, log decoding and four-decimal CV fitness as Random Search.
- Count initialization in the budget; reject incomplete-generation budgets and invalid settings before evaluating anything. Repeated candidates count; no caching or local polishing.
- Save all evaluated coordinates, decoded values, generation/target index, per-fold RMSE, best-so-far score and per-call/cumulative timing. Keep DE parameter values at full precision for later refits.
- Added `pilot`, `de-search`, and `synthetic-benchmarks` CLI commands. DE search saves validation-only selections and never accesses holdout for fitting/scoring. Output commands refuse overwrite; select a fresh output directory for reruns.
- Added missing `uv.lock` and declared `rich` directly because the existing CLI imports it. Project still supports Python >=3.11; this verification used Python 3.12. Existing Stage 1 data/baseline results were not overwritten.
- Final settings/config are frozen in `configs/experiment.json` and explained in `docs/protocol.md`.

### 2. Commands actually run

```sh
uv sync
uv run pytest -q
uv run concrete-strength verify-stage1
uv run pytest tests/test_de.py -q
uv run concrete-strength --help
uv run concrete-strength pilot
uv run concrete-strength synthetic-benchmarks
```

The Codex sandbox required `UV_CACHE_DIR=/tmp/bio-aat-uv-cache` before uv commands; this is a local cache location, not a project requirement. `uv sync --locked` initially failed because the incoming branch had no lockfile; `uv sync` generated it successfully. Future setups should use `uv sync --locked`.

Separate development-only timing probes called the existing evaluator at log coordinates `(4,-5,-3)`, `(4,1,-3)`, `(4,-1,-3)` on the saved pilot folds and wrote `results/pilot/timing_probes.json`. Their calls are outside the matched optimizer comparison and explicitly labelled diagnostics.

### 3. Verification and measured outcomes

- Reproduced incoming Stage 1 suite: **14 tests passed**. `verify-stage1` also passed against committed processed data and baseline JSON.
- Combined suite after DE addition: **35 tests passed** (14 existing + 21 added). New tests exercise donor exclusion, clipped/unclipped mutation, forced crossover, seed reproducibility, exact initialization-inclusive budget, deferred updates, acceptance/rejection, invalid/nonfinite fitness, known synthetic minima and a real SVR integration whose holdout targets are replaced with NaN to prove they are unused.
- CLI integration verifies configuration-controlled budgets/folds, validation-only output and overwrite protection.
- Matched pilot: population 6, budget 24, three development folds, seeds 11/22 for both methods: **288 tuning fits**, zero holdout scoring.

| Method | Seed | Best pilot CV RMSE (MPa) | Search seconds |
|---|---:|---:|---:|
| Random Search | 11 | 6.1751 | 1.01 |
| DE | 11 | 6.1163 | 2.03 |
| Random Search | 22 | 6.5326 | 2.67 |
| DE | 22 | 5.9864 | 5.26 |

These are pilot feasibility results, not final performance. The largest measured timing probe took about 2.95 seconds for three-fold fitness. Retain final population 15, budget 300, five seeds/five folds, based on feasible measured runtime; allow substantial runtime margin and monitor the final run.

Synthetic checks (3 dimensions, bounds [-5.12,5.12], five seeds, 300 calls per method): mean best Sphere fitness DE=0.067805 vs Random Search=1.041886; Rastrigin DE=7.685621 vs Random Search=10.432464. Individual seeds and best-so-far histories are saved; no claim that DE always wins or finds an exact global optimum.

### 4. Evidence, caveats and sources

- `results/pilot/stage2_pilot.json`: full pilot candidate histories, fold lists, provenance, source/config/lockfile checksums and run settings.
- `results/pilot/synthetic_benchmarks.json`: all five-seed synthetic comparisons and convergence traces.
- `results/pilot/timing_probes.json`: extreme-parameter runtime probes.
- `docs/protocol.md`: frozen algorithm settings, chronology, runtime decision, precision caveat and Stage 3 commands.
- Stage 1 had already evaluated baseline/random-search holdout scores. Stage 2 never used these to change DE settings, but the report must not claim the holdout had never been inspected.
- Stage 1 runtimes were measured on Windows; Stage 2 used macOS arm64. Compare final runtime only on a shared machine/configuration.
- The existing pandas/xlrd reader emits a deprecation warning but all ingestion tests pass. No reader replacement or warning suppression was introduced.
- Sources: Stage 1's actual evaluator/search code and saved split contract; Storn & Price (1997), original DE method, DOI `10.1023/A:1008202821328`; UCI source readme/dataset DOI `10.24432/C5PK67`. Actual settings and behavior are documented explicitly rather than inheriting library optimizer defaults.

### 5. Handoff to Stage 3 (Ullas N)

```sh
uv sync --locked
uv run pytest -q
uv run concrete-strength verify-stage1
uv run concrete-strength de-search
```

The final command is ready but **was not run in Stage 2**. It performs five final-budget searches and writes `results/de/de_search_results.json` with validation-selected candidates only. Stage 3 must lock all candidates, perform the holdout refits using the existing helper, save final metrics/predictions/plots and complete reproduction. Follow `docs/protocol.md` for exact rules; preserve incoming baseline artifacts and pilot/final separation. Vedantha will prepare the report and slides from these logs and Stage 3's evidence.

---

## Stage 3: Final Optimization Experiments, Holdout Evaluation & Plots

- **Owner:** Ullas N (USN: 1BM23CD067)
- **Status:** Completed
- **Tasks Assigned:** T10, T11, T12, T13
- **Date:** 26 October 2026
- **Working branch:** `final-experiments`

### 1. Implementation and decisions

- Added `src/concrete_strength/stage3.py` and the
  `finalize-experiments` CLI command.
- Ran the frozen `de-search` protocol unchanged: five seeds (`11, 22, 33, 44,
  55`), five saved development folds, population 15, DE/rand/1/bin, and 300
  objective calls per seed including initialization.
- Kept DE selection validation-only. Each saved full-precision DE candidate was
  refit once on all 826 development rows and evaluated on the fixed 204-row
  holdout. No holdout result influenced selection.
- Generated convergence, holdout comparison, prediction/residual, and
  development-only learning-curve plots. The demonstration model was selected
  by validation RMSE; seed 11 was the best DE run.

### 2. Exact commands run

```powershell
python -m pip install -e .
python -m pytest -q
python -m concrete_strength.cli de-search
python -m concrete_strength.cli finalize-experiments
```

The local run used Python 3.13 on Windows. The repository's reproducible
environment remains `uv sync --locked`; the direct pip install was only needed
because `uv` was not available on this machine.

### 3. Verification and measured outcomes

- Existing and DE test suite: **35 passed**.
- Final DE output: 5 runs × 300 calls = **1,500 development CV objective
  evaluations**, with no holdout scoring during search.
- DE validation-best RMSE: **5.8797 ± 0.0198 MPa** across seeds.
- DE holdout: **RMSE 6.2250 ± 0.1104 MPa, MAE 4.3143 ± 0.0526 MPa,
  R² 0.8324 ± 0.0060**.
- Random Search holdout: **RMSE 6.2328 ± 0.1194 MPa**.
- Default SVR holdout: **RMSE 9.9069 MPa, MAE 7.8854 MPa, R² 0.5755**.

Full precision candidates, per-seed metrics, predictions, residuals, histories,
plots, checksums and machine provenance are saved in
[`results/final/`](../results/final/). The summary and reproduction commands
are in [`results/README.md`](../results/README.md).

### 4. Limitations and handoff to Stage 4

- The holdout is a single fixed partition and optimizer variability is reported
  descriptively; no unsupported statistical significance claim is made.
- DE's mean holdout improvement over Random Search is small (0.12% RMSE), so
  the conclusion is that both tuned methods substantially improve the default
  model, while DE is marginally better in this protocol.
- Stage 2 pilot results remain separate from the final five-fold results.
- Vedantha should use `results/final/final_results.json`, `results/final/metrics.csv`,
  the four PNG plots, this work log, and `docs/protocol.md` when preparing the
  report and presentation.

---

## Technical closeout before Stage 4 — 27 October 2026

- **Owner:** R V Abhishek; closes f1, f2 and f3 requested after Ullas's handoff.
- Corrected the learning curve to three group-disjoint development folds, nested
  complete-group samples, fixed demonstration parameters and both training and
  validation RMSE. Seed 42 + fold index; fractions 0.25/0.50/0.75/1.0. Saved fold
  row IDs and group counts, plus `results/final/learning_curve.csv`.
- Validation RMSE decreases from 8.3838 to 5.9784 MPa as diagnostic training data
  increase. Training RMSE increases from 2.7596 to 3.7728 MPa. This diagnostic
  does not change any five-fold search, holdout metric, candidate or prediction.
- Redrew and visually inspected all four plots. Convergence now includes all
  five Random Search traces as well as all five DE traces.
- `verify-evidence` audits all 3,000 candidate records, original inputs/splits,
  selections, saved predictions, CSV rows, metric means/SDs and corrected groups.
  It also recomputes CV fitness and refits all five fixed DE selections.
- The locked macOS environment reproduces original Windows holdout metrics with
  maximum absolute difference 0.0002; maximum selected CV RMSE difference is
  0.0001. Predeclared reproduction tolerance: 0.001. Original reported scores
  remain authoritative; no additional hyperparameter search was performed.
- Historical Windows path separators and CRLF text checksums needed explicit
  interpretation. Reconstructing CRLF bytes matches the historical hashes;
  the raw XLS matches exactly. Actual content changes still fail verification.
  Added `.gitattributes` to keep future text evidence checksums portable.
- Test suite: **43 passing tests**, including complete-group sampling, nesting,
  holdout exclusion and checksum portability regression checks.
- Exact correction/check commands: `uv sync --locked`, `uv run pytest -q`,
  `uv run concrete-strength refresh-diagnostics`,
  `uv run concrete-strength verify-evidence`. Sandbox runs additionally set
  `UV_CACHE_DIR=/tmp/bio-aat-uv-cache` and `MPLCONFIGDIR=/tmp/bio-aat-mpl`;
  these are local writable cache paths rather than project requirements.
- Independent fresh checkout of code commit `6e7eb0f`: locked setup, all 43 tests,
  selected-model audit and all eight evidence checksums passed. The setup required
  downloading exact pinned wheels after an offline cache miss; no version change.
  Clean-checkout record: `results/closeout/fresh-checkout-verification.json`.
- Frozen report inputs and reproduction steps: `docs/technical-closeout.md`.
  The technical tag is `technical-closeout-2026-10-27`; the saved verification
  report and checksum manifest identify exact evidence files. Report/PPT and
  administrative submission requirements remain pending Stage 4.

---

## Stage 4: Project Report, Presentation & Submission Verification

- **Owner:** Vedantha V V (USN: 1BM23CD069)
- **Status:** Ready for report/PPT from the frozen technical handoff
- **Tasks Assigned:** T14, T15, T16, T17, T18

*(To be filled by Stage 4 owner)*


## Stage 4 deliverable preparation — 1 November 2026

- Prepared the 35-page editable LaTeX report and 18-slide PPTX from frozen evidence; kept the source examples unchanged. Used the stock-price section sequence with concrete/DE/SVR adaptations and explicit statements for unperformed analyses.
- Reorganized the supplied thesis folder into `/Users/rva/Projects/BMSCE_Academic_Templates`, preserving every original in `archive/original-supplied-folder/`. Added separate self-contained course-report and thesis starters plus an editable PPT template.
- User confirmed Prof. Manoj Kumar (Assistant Professor), HOD Dr. Shyamala G, course 23DS7BSBIO and AY 2026–27. The user explicitly requested the source `.tex` border geometry and line weight on **all** pages; initially used 1.5pt at 0.5-inch insets, then updated to 1.8pt medium grey with 6pt rounded corners at the user’s request, with running-header clearance. PPT hierarchy was improved following user review.
- Project report compiled using XeLaTeX, latexmk and Biber with no final warnings, undefined references or overfull boxes. Rendered all pages and slides and checked layout, metadata and displayed results. Both generic starters compiled separately without warning/overfull output after correcting the declaration layout.
- First-party PPTX finalization passed package, dimension, font and editable-table checks with zero findings/warnings. Artifact Tool import itself was unavailable because its Node adapter was missing; that check was explicitly skipped, and the original deck was edited with python-pptx. Native Microsoft PowerPoint execution was not performed.
- Checked all ten report seed rows against the frozen CSV, PPT aggregate cells against the frozen JSON, theme-byte preservation, all 35 border drawing streams and A4 page geometry. All nine technical evidence checksums passed; no training, new searches or changes to frozen results were performed.
- Commands: `TEXMFHOME=/tmp/bmsce-texmf BIBER=/tmp/bmsce-biber/bin/universal-darwin/biber sh report/scripts/build.sh`; `uv run --no-project --python <bundled-runtime> python presentation/scripts/build_presentation.py`; first-party finalization; `pdftoppm`; `soffice --headless --convert-to pdf`; `shasum -a 256 -c results/final/SHA256SUMS`.
- The existing global tooling and project dependency lockfile were preserved. Missing TeX packages/Biber were used from temporary directories. Detailed outputs and exact validation boundaries: `docs/deliverable-validation.md` and `docs/validation/`.
- Local deliverables are prepared; actual signatures, professor access, registration, Drive upload and presentation remain unverified. No external upload/message or Git push was performed.


### Border refinement — 1 November 2026

At the user's request, replaced the single grey border with a closely spaced double border on every page: 2.4pt outer and 1.2pt inner lines, both `black!55`, inset 0.5 and 0.55 inches, with 6pt and 3pt rounded corners. Updated the central canonical style and both starters, rebuilt the report and starter previews, and verified both drawing layers on all 35 report pages. Text geometry and pagination remain unchanged.


### Reference corrections — 1 November 2026

Applied the user's reference review after checking the primary UCI, MIT Press and JMLR pages. Changed the dataset citation to UCI's recommended 1998 (2007 is its deposit date). Used a dataset bibliography entry so IEEE prints the year and DOI. Updated the presentation's dataset year, including its editable source. Cited Holland's linked MIT Press edition as 1992 with the full subtitle and an explicit original-publication note for 1975. Qualified the Random Search discussion: the paper motivates the baseline and compares with grid/manual search, while this project's evidence establishes the DE comparison. Yeh's paper DOI was already correct; checked the generated PDF hyperlink for literal parentheses and the expected DOI URL.

Rebuilt and rendered the report and presentation; visually reviewed the changed literature/bibliography pages and reference slide. Report remains 35 pages, PPT 18 slides; double borders and all original experimental metrics remain unchanged. Final report log has no warnings, undefined references or overfull boxes. First-party PPT finalization and the complete deliverable checks passed. The current receipt is `docs/validation/presentation-finalization.json`, with the citation revision receipt also retained as `presentation-reference-finalization.json`.


### Remove bibliography access dates — 1 November 2026

Removed both `urldate` fields from the dataset and scikit-learn bibliography entries at the user's request. Rebuilt the report, checked that no “Accessed” or “Nov. 1” text remains anywhere, and inspected the final reference-page layout. Publication years, citations, links, experimental evidence and the 35-page count are preserved.


### Em-dash removal — 1 November 2026

Replaced the report's two remaining em dashes in bibliography titles with a colon and a comma, as appropriate. The editable BibLaTeX source was updated and the report rebuilt. Full PDF and slide-text checks confirm zero em dashes in either deliverable; the PPT already contained none. Numeric ranges, publication details, results, layout and double borders remain unchanged. Rechecked the reference-page rendering and clean TeX log; access dates remain removed.


### Repository release preparation — 1 November 2026

Prepared all project deliverables, editable sources, local BMSCE style/assets, reusable PPT template and validation records for Git. Added isolated `uv run --script` dependencies for the presentation builder and a portable artifact validator without changing the experiment manifest or lockfile. Both commands were executed using their pinned dependencies. An isolated PPT rebuild matches all delivered slide text, native table values and object geometry; the portable validator passes. All nine frozen evidence checksums and `git diff --check` pass. Remote `main` was fetched before creating `codex/report-presentation`; the project follows its existing pull-request workflow. Temporary build directories, downloaded tools and the unrelated original thesis archive are excluded from this project release.


### Report formatting and consistency pass — 1 November 2026

Reformatted the report at the user's request without changing any experimental result. Front matter now follows the required order (Cover, Certificate, Acknowledgement, Abstract, Contents, List of Figures, List of Tables, Abbreviations) and the contents lists every front-matter section. Cover page spacing was redistributed over the full page and the certificate's doubled space after "Prof." was removed with `\frenchspacing`. Tables gained row padding, centred numeric columns and mid-rules between groups; footer fonts were unified; consecutive hyphenation and mid-word URL breaks were suppressed; the SVR reference entry now prints as a normal web reference with a protected "SVR".

Content corrections: "Paper Organization" is now "Report Organization"; the crossover equation defines its random draw (`\rho_j`) instead of an undefined `r_j` that clashed with donor indices; the Sphere/Rastrigin text states d=3, bounds [-5.12, 5.12], five seeds and 300 calls from `docs/protocol.md`; Tables 5.1, 6.2, 7.2 and Figure 7.4 are now cited in the text; the abbreviation list is alphabetical and adds CR, DOI, SDG and SHAP. Added Table 8.1 (default vs Random Search vs DE) in the comparative chapter using only saved values; all displayed numbers were re-checked against `results/final/final_results.json`, `results/final/metrics.csv` and `results/pilot/synthetic_benchmarks.json`.

Built with XeLaTeX, Biber and latexmk (TinyTeX; installed the missing `algorithms`/`algorithmicx` packages); the log has no warnings, undefined references or overfull/underfull boxes. Report remains 35 pages. Rendered and inspected every page. `scripts/validate_deliverables.py` passes; `docs/validation/deliverables.json` now carries the new report hash. No experiments were rerun. Signatures, uploads and presentation evidence remain pending.

Follow-up: certificate HOD signature block flushed right, spacing added under "Examiners", and the Acknowledgement and Abstract headings centred (`\CenteredStarChapter`); rebuilt with a clean log, 35 pages, validator passes, report hash in `docs/validation/deliverables.json` updated.


### Log-age extension, diagrams and extra charts — 5 November 2026

Branch `codex/log-age-extension`. Goal: find improvements beyond the frozen Random Search/DE results, add an architecture diagram and more charts.

**Finding.** A development-only probe (scipy DE, seed 11, five saved folds, nothing saved, no holdout access) gave CV RMSE 5.85 (raw) vs 4.97 (ln(age)) vs 4.96 (+ratios) vs 4.99 (+log target). The optimizer was not the bottleneck; the age representation was. Disclosed in the report: ln(age) is probe-motivated and the holdout was inspected in Stage 1.

**Protocol.** `docs/protocol-extension.md` was committed before any extension run (commit 0e31cfb). Same splits/folds/bounds/budget/seeds; frozen raw results reused, not rerun; default SVR, Random Search and DE all on ln(age); ablations: DE current-to-best/1/bin, jDE, water ratios.

**Code.** `data.py` (`FEATURE_SETS`, `add_engineered_features`), optional `feature_columns` through `evaluation.py`/`search.py`, DE `strategy` option in `de.py` (default rand/1/bin unchanged and checked against the saved seed-11 history), `extension.py` with CLI `extension-search` and `extension-finalize`. Tests: 52 pass (`tests/test_extension.py` is new).

**Commands.** `uv run concrete-strength extension-search` (25 runs, ~1 h, clean tree at launch, 300 calls each); `uv run concrete-strength extension-finalize` (one holdout pass); `shasum` manifest in `results/extension/SHA256SUMS`.

**Results (holdout RMSE, MPa, mean ± SD over 5 seeds).** Default SVR 9.9069 raw / 7.4780 ln(age); Random Search 6.2328 / 4.9700 ± 0.2656; DE 6.2250 / 4.8402 ± 0.1039 (22.2% below frozen DE); current-to-best/1/bin 4.8363 ± 0.0582; jDE 4.8890 ± 0.0820; DE + ratios 4.7849 ± 0.0630. Validation RMSE: RS 5.0171, DE 4.9670, current-to-best 4.9028, jDE 4.8976, ratios 4.9611. Demonstration (lowest validation): current-to-best seed 55, validation 4.8606, holdout 4.8672. DE is 0.13 MPa below Random Search and less variable, untested for significance; variants and ratios are within seed SD.

**Deliverables.** TikZ architecture and DE flowchart (`report/figures/`, PNGs via `report/scripts/render_figures.sh` + `crop_png.py`); charts via `scripts/make_report_figures.py` (EDA, correlation, search-space, representation comparison, DE variants, extension predictions) and generated `report/tables/extension.tex`. Report: new Section 7.12 plus updates to Ch5, Ch6, Ch8, abstract, conclusion, future work, jDE reference; 43 pages, clean log. PPT: 24 slides (architecture, flowchart, search-space, extension table/chart/variants added).

**Verification.** `pytest` 52 passed; `verify-stage1`, `verify-evidence` (alternate output path), `results/final/SHA256SUMS` and extension checksums pass; `git diff` of `results/final`, `results/de`, `results/baseline`, `configs/experiment.json`, `uv.lock` is empty. Report rendered and extension/architecture/flowchart pages inspected. TeX packages came from a scratch user tree and Biber 2.22 from Homebrew; no project dependency or lockfile changed.

**Not done / limits.** No renderer for slides (`soffice` absent): new slides were checked programmatically (shapes in bounds, table values match JSON), not visually; `presentation/*.pdf` preview is stale. `docs/validation/presentation-finalization.json` is the old first-party finalization receipt, so `validate_deliverables.py` reports `ppt_matches_finalization_receipt: false` (every other check passes). Registration, signatures, upload and presentation remain unverified.

## Extension 2 (6 November 2026): ARD kernel search space and split replication

**Why.** After Extension 1 the DE-vs-Random-Search gap (0.13 MPa) was smaller than seed spread. A development-only, unsaved probe of a per-feature-gamma (ARD) kernel (CV only, no holdout, no Random Search arm) suggested a lower CV RMSE and motivated testing whether DE gains more in a 10-D space. Disclosed in the report; the holdout was already seen in Stage 1 and Extension 1.

**Protocol.** `docs/protocol-extension2.md` + `configs/extension2.json` committed before any run (commit c37b0db). E2a: ARD (10-D) vs shared gamma (3-D control), Random Search vs DE/rand/1/bin, 1,500 calls, population 5 x dimension, 5 seeds. E2b: `log_age`, Random Search vs DE, 300 calls, 5 seeds, five new group-disjoint outer splits (`random_state` 101-105).

**Code.** `evaluation.py` (`build_ard_pipeline`, `evaluate_ard_cv`: columns scaled by sqrt(gamma_j), SVR gamma = 1; equal gammas reproduce the standard RBF-SVR, tested), `extension2.py` (process-parallel runs, 7 workers) and CLI `ext2-ard-search`, `ext2-ard-finalize`, `ext2-replication-search`, `ext2-replication-finalize`. Searches ran with `OMP_NUM_THREADS=1`; runtimes under parallel load are indicative only. Tests: 57 pass.

**Results (mean ± SD over 5 seeds; validation / holdout RMSE, MPa).** 1,500 calls: shared-gamma Random Search 4.9185 / 4.8381 ± 0.1064; shared-gamma DE 4.8581 ± 0.0000 / 4.8699 ± 0.0060; ARD Random Search 5.1116 / 4.9693 ± 0.3940; ARD DE 4.8811 / 4.6787 ± 0.4899. Random Search degrades in 10-D, DE does not (validation advantage 0.06 -> 0.23 MPa), but ARD did not improve validation RMSE over the shared kernel, and the probe's lower CV value was not reproduced. Replication (d = RS - DE; positive favours DE): validation d > 0 on all six splits (mean 0.071, approx. 95% t-interval 0.045-0.097); holdout d > 0 on five of six (mean 0.118, interval 0.012-0.224; new five alone 0.116, interval -0.024 to 0.256). Splits overlap, so intervals are indicative only.

**Deliverables.** Report Section 7.13 (44 pages, clean log). Slides were not updated for Extension 2. Evidence in `results/extension2/` with its own `SHA256SUMS`; tag `extension2-2026-11-06` (local).

**Verification.** `pytest` 57 passed; `verify-stage1` passes; checksums pass; `git diff` of the frozen evidence, `results/extension`, `configs/experiment.json`, `uv.lock` and `data` is empty.

## Deliverable data sync after Extension 2 (11 November 2026)

**Goal.** Bring the report and presentation in line with all saved evidence (frozen study, Extension 1, Extension 2) and improve the deck's indexing. Branch `codex/log-age-extension`. No training or search was rerun.

**Report.** Extension 2 existed only in Section 7.13. Added it to the abstract (new paragraph), Chapter 1 contributions, Chapter 5 (ARD kernel), Chapter 6 (3-D vs 10-D and replication), the Chapter 7 scope sentence, Chapter 8 comparison, the conclusion and future work (replication now done; non-overlapping/nested splits remain future). Numbers were checked against `results/extension2/ard_results.json` and `replication_results.json`. Rebuilt with XeLaTeX/latexmk/Biber 2.22: 45 pages, no warnings, undefined references or over/underfull boxes. `biblatex`, `biblatex-ieee` and `logreq` were installed with `tlmgr --usermode` into `~/Library/texmf` because the earlier temporary TeX tree was gone; the system TeX install was not changed.

**Presentation.** 24 to 28 slides (`presentation/scripts/build_presentation.py`). Added: Objectives and Scope (RQ1-RQ4), Extension 2a (ARD), Extension 2b (replication), Key Findings. Table of Contents now lists five sections with slide ranges computed from the deck order; every content slide has a "Section k: name" footer tag and `n / N` numbering; every slide has specific speaker notes with its evidence source. Stale text fixed: "Forty-three tests" to 57 passing tests; limitations, future scope and closing statement updated for Extension 2. New charts `report/assets/ard_comparison.png` and `replication_gap.png` come from `scripts/make_report_figures.py extension2`. The preview PDF was regenerated by exporting the PPTX through Keynote and every slide was inspected as a contact sheet; the agenda, Key Findings and closing slides were inspected at full size.

**Verification.** `uv run pytest -q`: 57 passed. Checksums in `results/final`, `results/extension` and `results/extension2` all pass. `scripts/validate_deliverables.py`: every check passes except `ppt_matches_finalization_receipt`; the first-party PPTX finalizer was not available, so `docs/validation/presentation-finalization.json` still describes the older deck and `deliverables.json` was not rewritten. No em dashes in either deliverable. PowerPoint itself was not used.

**Open.** Visual changes to report and deck are awaiting the user's instructions. Signatures, registration, Drive upload, professor access and presentation remain unverified.

### Slide layout pass — 11 November 2026

At the user's request: slides 3-8, 10, 11, 13, 18 and 23-26 now share one pattern (`panel()` in `presentation/scripts/build_presentation.py`): a heading, real bullets with bold lead-ins on the left, and "key data" cards on the right (tables on slides 13 and 18 keep their native tables with bulleted conclusions below). Slide 12 uses a new widescreen TikZ flowchart (`report/figures/de-flowchart-wide.tex`, rendered by `report/scripts/render_figures.sh`; the report keeps the vertical flowchart). The reference slide has clickable DOI/source links and the closing slide was rebuilt (takeaway cards, questions, team, clickable repository link); previously it was the template's closing layout with text appended. Preview PDF re-rendered via Keynote and every changed slide inspected. All card numbers are computed from saved results or are fixed protocol values; the 57-test and three-checksum-set figures are from this session's runs.
