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
- **Status:** Ready to start after Stage 2 handoff
- **Tasks Assigned:** T10, T11, T12, T13

*(To be filled by Stage 3 owner)*

---

## Stage 4: Project Report, Presentation & Submission Verification

- **Owner:** Vedantha V V (USN: 1BM23CD069)
- **Status:** Pending Stage 3 handoff
- **Tasks Assigned:** T14, T15, T16, T17, T18

*(To be filled by Stage 4 owner)*
