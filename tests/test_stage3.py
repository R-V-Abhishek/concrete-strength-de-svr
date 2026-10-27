"""Learning-curve regression checks: grouping, nesting and held-out isolation."""

import hashlib

import numpy as np
import pandas as pd
import pytest

from concrete_strength.data import FEATURE_COLUMNS, TARGET_COLUMN
from concrete_strength.stage3 import _learning_curve
from concrete_strength.verification import recorded_checksum


def grouped_data():
    groups = np.repeat(np.arange(24), 2)
    df = pd.DataFrame({column: groups.astype(float) for column in FEATURE_COLUMNS})
    df["group_id"] = groups
    df[TARGET_COLUMN] = groups * 2.0 + np.tile([0.1, -0.1], 24)
    # These groups are reserved and must never be used by the diagnostic.
    df.loc[42:, TARGET_COLUMN] = np.nan
    return df


def test_learning_curve_is_group_complete_nested_and_development_only():
    df = grouped_data()
    fractions = [0.25, 0.5, 0.75, 1.0]
    params = {"C": 1., "gamma": 0.1, "epsilon": 0.1}
    curve = _learning_curve(df, list(range(42)), params, fractions)
    assert curve == _learning_curve(df, list(range(42)), params, fractions)
    previous = [set(), set(), set()]
    for row in curve:
        assert len(row["folds"]) == 3
        assert np.isfinite(row["train_rmse_mean"])
        assert np.isfinite(row["rmse_mean"])
        for fold in row["folds"]:
            train = set(fold["training_indices"])
            val = set(fold["validation_indices"])
            assert not train.intersection(val)
            assert train.union(val).issubset(range(42))
            assert previous[fold["fold"]].issubset(train)
            previous[fold["fold"]] = train
            train_groups = set(df.loc[sorted(train), "group_id"])
            assert not train_groups.intersection(df.loc[sorted(val), "group_id"])
            assert len(train) == 2 * len(train_groups)
            assert fold["training_group_count"] == len(train_groups)
            for group in train_groups:
                assert set(df.index[df["group_id"] == group]).issubset(train)
        assert row["rmse_mean"] == round(np.mean([f["validation_rmse"] for f in row["folds"]]), 4)
        assert row["train_rmse_mean"] == round(np.mean([f["train_rmse"] for f in row["folds"]]), 4)
    assert all(len(f["training_indices"]) + len(f["validation_indices"]) == 42
               for f in curve[-1]["folds"])


@pytest.mark.parametrize("fractions", [[], [0.], [-0.1], [1.1], [float("nan")]])
def test_learning_curve_rejects_invalid_fractions(fractions):
    with pytest.raises(ValueError, match="fractions"):
        _learning_curve(grouped_data(), list(range(42)),
                        {"C": 1., "gamma": 0.1, "epsilon": 0.1}, fractions)


def test_historical_windows_text_hash_is_checked_without_ignoring_changes(tmp_path):
    path = tmp_path / "results.json"
    path.write_bytes(b'{"metric": 6.2250}\n')
    windows_hash = hashlib.sha256(b'{"metric": 6.2250}\r\n').hexdigest()
    assert recorded_checksum(path, windows_hash) == "CRLF text checkout"
    path.write_bytes(b'{"metric": 1.0000}\n')
    with pytest.raises(ValueError, match="Changed evidence"):
        recorded_checksum(path, windows_hash)


def test_binary_source_hash_never_gets_text_normalization(tmp_path):
    path = tmp_path / "source.xls"
    path.write_bytes(b'binary\n')
    with pytest.raises(ValueError, match="Changed evidence"):
        recorded_checksum(path, hashlib.sha256(b'binary\r\n').hexdigest())
