# Project Work Log: Concrete Strength DE-SVR

Project: **Concrete Compressive Strength Prediction Using Differential Evolution–Optimized Support Vector Regression**  
Sequential Workflow: Stage 1 (Abhishek) → Stage 2 (Sushanth) → Stage 3 (Ullas) → Stage 4 (Vedantha)  
Working Branch: `S_branch`  

---

## Stage 1: Setup, Data Ingestion, Evaluation Pipeline & Baselines

- **Owner:** R V Abhishek (USN: 1BM23CD047)
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

### 6. Handoff to Stage 2 (Sushanth S)
- **Handoff Commit:** `e27e6e0`
- **Files to Read:** `configs/experiment.json`, `src/concrete_strength/evaluation.py`, `src/concrete_strength/search.py`
- **Handoff Command to Run:**
  ```powershell
  .venv\Scripts\pytest tests/
  .venv\Scripts\python -m concrete_strength.cli verify-stage1
  ```

---

## Stage 2: Differential Evolution (DE) Implementation, Tests & Pilot

- **Owner:** Sushanth S (USN: 1BM23CD063)
- **Status:** Pending Stage 1 handoff
- **Tasks Assigned:** T06, T07, T08, T09

*(To be filled by Stage 2 owner)*

---

## Stage 3: Final Optimization Experiments, Holdout Evaluation & Plots

- **Owner:** Ullas N (USN: 1BM23CD067)
- **Status:** Pending Stage 2 handoff
- **Tasks Assigned:** T10, T11, T12, T13

*(To be filled by Stage 3 owner)*

---

## Stage 4: Project Report, Presentation & Submission Verification

- **Owner:** Vedantha V V (USN: 1BM23CD069)
- **Status:** Pending Stage 3 handoff
- **Tasks Assigned:** T14, T15, T16, T17, T18

*(To be filled by Stage 4 owner)*
