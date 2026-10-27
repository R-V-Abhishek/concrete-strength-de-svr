"""Data ingestion, auditing, group assignment, and deterministic split generation.

This module validates the raw UCI Concrete Compressive Strength Excel workbook,
assigns group identifiers to identical 8-feature recipes to prevent data leakage,
and generates GroupShuffleSplit holdout and GroupKFold cross-validation splits.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
import warnings

# Suppress deprecation warning for xlrd engine in pandas
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas.io.excel._xlrd")

COLUMN_MAPPING: dict[str, str] = {
    "Cement (component 1)(kg in a m^3 mixture)": "cement",
    "Blast Furnace Slag (component 2)(kg in a m^3 mixture)": "blast_furnace_slag",
    "Fly Ash (component 3)(kg in a m^3 mixture)": "fly_ash",
    "Water  (component 4)(kg in a m^3 mixture)": "water",
    "Superplasticizer (component 5)(kg in a m^3 mixture)": "superplasticizer",
    "Coarse Aggregate  (component 6)(kg in a m^3 mixture)": "coarse_aggregate",
    "Fine Aggregate (component 7)(kg in a m^3 mixture)": "fine_aggregate",
    "Age (day)": "age",
    "Concrete compressive strength(MPa, megapascals) ": "compressive_strength",
}

FEATURE_COLUMNS: list[str] = [
    "cement",
    "blast_furnace_slag",
    "fly_ash",
    "water",
    "superplasticizer",
    "coarse_aggregate",
    "fine_aggregate",
    "age",
]

TARGET_COLUMN: str = "compressive_strength"


def compute_sha256(filepath: str | Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    path = Path(filepath)
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_raw_data(filepath: str | Path) -> pd.DataFrame:
    """Read the raw Excel workbook and rename columns to canonical snake_case names."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {path}")

    df = pd.read_excel(path, engine="xlrd")
    
    # Verify expected column count and presence
    missing_cols = [c for c in COLUMN_MAPPING if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Raw Excel missing expected columns: {missing_cols}")

    df = df.rename(columns=COLUMN_MAPPING)
    expected_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    df = df[expected_cols].copy()

    # Verify types and non-finites
    if df.shape[0] != 1030:
        raise ValueError(f"Expected 1030 rows, found {df.shape[0]}")
    if df.shape[1] != 9:
        raise ValueError(f"Expected 9 columns, found {df.shape[1]}")
    if df.isna().any().any():
        raise ValueError("Raw data contains null or NaN values")

    return df


def audit_data(df: pd.DataFrame) -> dict[str, Any]:
    """Audit missing values, duplicates, and unique recipe groups."""
    total_rows = int(df.shape[0])
    null_count = int(df.isna().sum().sum())
    exact_duplicates = int(df.duplicated().sum())
    feature_duplicates = int(df.duplicated(subset=FEATURE_COLUMNS).sum())
    unique_recipes = int(len(df.drop_duplicates(subset=FEATURE_COLUMNS)))

    stats = {
        "total_rows": total_rows,
        "total_columns": int(df.shape[1]),
        "null_count": null_count,
        "exact_duplicates": exact_duplicates,
        "feature_duplicates": feature_duplicates,
        "unique_recipes": unique_recipes,
        "differing_target_same_recipe": feature_duplicates - exact_duplicates,
    }
    return stats


def assign_groups(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Assign deterministic integer group IDs based on exact 8-feature tuples.
    
    Returns the dataframe with 'group_id' and 'row_id', and the group series.
    """
    df_out = df.copy()
    df_out["row_id"] = np.arange(len(df_out), dtype=int)
    
    # Group by exact feature values
    # Factorize returns (labels, uniques)
    group_tuples = [tuple(row) for row in df_out[FEATURE_COLUMNS].to_numpy()]
    unique_mapping: dict[tuple, int] = {}
    group_ids = []
    
    for t in group_tuples:
        if t not in unique_mapping:
            unique_mapping[t] = len(unique_mapping)
        group_ids.append(unique_mapping[t])
        
    df_out["group_id"] = np.array(group_ids, dtype=int)
    return df_out, df_out["group_id"]


def create_group_splits(
    df: pd.DataFrame,
    group_series: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42,
    cv_folds: int = 5,
) -> dict[str, Any]:
    """Partition dataset into holdout test and 5-fold cross-validation sets using group awareness.
    
    Asserts:
    1. Zero group overlap between dev and holdout.
    2. Zero group overlap between train and validation in each CV fold.
    """
    groups = group_series.to_numpy()
    indices = np.arange(len(df))

    # Step 1: Holdout split via GroupShuffleSplit
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    dev_idx, holdout_idx = next(gss.split(indices, groups=groups))

    dev_groups = set(groups[dev_idx])
    holdout_groups = set(groups[holdout_idx])

    # Assert zero overlap
    overlap_dev_holdout = dev_groups.intersection(holdout_groups)
    if overlap_dev_holdout:
        raise ValueError(f"Leakage detected between dev and holdout! Overlapping groups: {overlap_dev_holdout}")

    # Step 2: 5-Fold GroupKFold on Development set
    dev_df_groups = groups[dev_idx]
    gkf = GroupKFold(n_splits=cv_folds)
    
    cv_folds_list = []
    for fold_num, (train_sub_idx, val_sub_idx) in enumerate(gkf.split(dev_idx, groups=dev_df_groups)):
        train_indices = dev_idx[train_sub_idx].tolist()
        val_indices = dev_idx[val_sub_idx].tolist()

        train_grps = set(groups[train_indices])
        val_grps = set(groups[val_indices])

        overlap_fold = train_grps.intersection(val_grps)
        if overlap_fold:
            raise ValueError(f"Leakage detected in fold {fold_num}! Overlapping groups: {overlap_fold}")

        cv_folds_list.append({
            "fold": fold_num,
            "train_indices": train_indices,
            "val_indices": val_indices,
            "num_train_samples": len(train_indices),
            "num_val_samples": len(val_indices),
            "num_train_groups": len(train_grps),
            "num_val_groups": len(val_grps),
        })

    manifest = {
        "random_state": random_state,
        "test_size_fraction": test_size,
        "num_cv_folds": cv_folds,
        "total_samples": len(df),
        "total_unique_groups": len(unique_mapping_count := set(groups)),
        "development_samples": len(dev_idx),
        "development_groups": len(dev_groups),
        "holdout_samples": len(holdout_idx),
        "holdout_groups": len(holdout_groups),
        "development_indices": dev_idx.tolist(),
        "holdout_indices": holdout_idx.tolist(),
        "cv_folds": cv_folds_list,
    }
    return manifest


def save_processed_data(
    df_with_groups: pd.DataFrame,
    manifest: dict[str, Any],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Persist cleaned data and split manifest."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    csv_path = out_path / "concrete_cleaned.csv"
    manifest_path = out_path / "splits_manifest.json"

    df_with_groups.to_csv(csv_path, index=False)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return csv_path, manifest_path


def load_processed_data(
    data_path: str | Path, manifest_path: str | Path
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the processed CSV and JSON split manifest."""
    df = pd.read_csv(data_path)
    with Path(manifest_path).open("r", encoding="utf-8") as f:
        manifest = json.load(f)
    return df, manifest
