"""Unit tests for dataset ingestion, auditing, and group-aware splitting."""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from concrete_strength.data import (
    COLUMN_MAPPING,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    assign_groups,
    audit_data,
    compute_sha256,
    create_group_splits,
    load_raw_data,
)

RAW_PATH = "data/raw/Concrete_Data.xls"
EXPECTED_SHA256 = "710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4"


def test_raw_file_checksum():
    assert Path(RAW_PATH).exists()
    sha = compute_sha256(RAW_PATH)
    assert sha == EXPECTED_SHA256


def test_load_raw_data():
    df = load_raw_data(RAW_PATH)
    assert df.shape == (1030, 9)
    assert not df.isna().any().any()
    for col in FEATURE_COLUMNS + [TARGET_COLUMN]:
        assert col in df.columns


def test_audit_data():
    df = load_raw_data(RAW_PATH)
    stats = audit_data(df)
    assert stats["total_rows"] == 1030
    assert stats["total_columns"] == 9
    assert stats["null_count"] == 0
    assert stats["exact_duplicates"] == 25
    assert stats["feature_duplicates"] == 34
    assert stats["unique_recipes"] == 996
    assert stats["differing_target_same_recipe"] == 9


def test_group_assignment():
    df = load_raw_data(RAW_PATH)
    df_with_groups, group_series = assign_groups(df)
    assert len(group_series.unique()) == 996
    assert "group_id" in df_with_groups.columns
    assert "row_id" in df_with_groups.columns

    # Verify duplicate 8-features share identical group_id
    dups = df_with_groups[df_with_groups.duplicated(subset=FEATURE_COLUMNS, keep=False)]
    for _, group_chunk in dups.groupby(FEATURE_COLUMNS):
        assert len(group_chunk["group_id"].unique()) == 1


def test_zero_group_leakage_in_splits():
    df = load_raw_data(RAW_PATH)
    df_with_groups, group_series = assign_groups(df)
    manifest = create_group_splits(
        df_with_groups,
        group_series,
        test_size=0.20,
        random_state=42,
        cv_folds=5,
    )

    dev_idx = manifest["development_indices"]
    holdout_idx = manifest["holdout_indices"]
    groups = df_with_groups["group_id"].to_numpy()

    dev_groups = set(groups[dev_idx])
    holdout_groups = set(groups[holdout_idx])

    # Assert zero overlap between dev and holdout
    assert len(dev_groups.intersection(holdout_groups)) == 0

    # Assert zero overlap across every CV fold
    for fold in manifest["cv_folds"]:
        t_groups = set(groups[fold["train_indices"]])
        v_groups = set(groups[fold["val_indices"]])
        assert len(t_groups.intersection(v_groups)) == 0
