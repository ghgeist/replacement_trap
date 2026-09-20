"""
Parity tests: rebuilt pipeline outputs must match committed artifacts.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

lib_path = Path(__file__).parent.parent / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

from replacement_trap_pipeline import build_core_dataframe, build_reference_outputs
from replacement_trap_utils import calculate_npv_penalty_pct

ROOT = Path(__file__).parent.parent
PKL_PATH = ROOT / 'data' / 'replacement_trap_df.pkl'
CSV_PATH = ROOT / 'data' / 'replacement_trap_df.csv'
REF_PATH = ROOT / 'data' / 'reference_outputs.json'

METRIC_COLUMNS = [
    'payback_period',
    'rp_ratio_scenario_a',
    'rp_ratio_scenario_b',
    'lifetime_value_cash_scenario_a',
    'lifetime_value_heloc_scenario_a',
    'lifetime_value_cash_scenario_b',
    'lifetime_value_heloc_scenario_b',
    'warranty_years',
    'comfort_gap',
]


@pytest.fixture(scope='module')
def rebuilt_df():
    return build_core_dataframe()


def test_committed_artifacts_exist():
    assert PKL_PATH.exists(), f"Missing {PKL_PATH}"
    assert CSV_PATH.exists(), f"Missing {CSV_PATH}"
    assert REF_PATH.exists(), f"Missing {REF_PATH}"


def test_rebuilt_matches_pickle_shape_and_columns(rebuilt_df):
    committed = pd.read_pickle(PKL_PATH)
    assert rebuilt_df.shape == committed.shape
    assert list(rebuilt_df.columns) == list(committed.columns)


def test_rebuilt_matches_pickle_metrics(rebuilt_df):
    committed = pd.read_pickle(PKL_PATH)
    for col in METRIC_COLUMNS:
        np.testing.assert_allclose(
            rebuilt_df[col].to_numpy(dtype=float),
            committed[col].to_numpy(dtype=float),
            rtol=1e-9,
            atol=1e-9,
            equal_nan=True,
            err_msg=f"Column {col} diverged from committed pickle",
        )


def test_csv_columns_match_pickle():
    committed = pd.read_pickle(PKL_PATH)
    csv_df = pd.read_csv(CSV_PATH)
    assert list(csv_df.columns) == list(committed.columns)


def test_reference_outputs_match_committed(rebuilt_df):
    current = build_reference_outputs(rebuilt_df)
    committed = json.loads(REF_PATH.read_text(encoding='utf-8'))
    assert set(current.keys()) == set(committed.keys())

    for key, ref_val in committed.items():
        curr_val = current[key]
        if isinstance(ref_val, dict):
            assert set(curr_val.keys()) == set(ref_val.keys())
            for subkey, ref_sub in ref_val.items():
                if isinstance(ref_sub, (int, float)):
                    assert abs(curr_val[subkey] - ref_sub) < 1e-9, f"{key}.{subkey}"
                else:
                    assert curr_val[subkey] == ref_sub
        elif isinstance(ref_val, (int, float)):
            assert abs(curr_val - ref_val) < 1e-9, key
        else:
            assert curr_val == ref_val


def test_npv_penalty_matches_shared_helper(rebuilt_df):
    """Pipeline npv_penalty_pct must use the signed shared helper, not abs-magnitudes."""
    expected = [
        calculate_npv_penalty_pct(npv, cash)
        for npv, cash in zip(
            rebuilt_df['npv_cash_4pct'],
            rebuilt_df['lifetime_value_cash_scenario_a'],
        )
    ]
    np.testing.assert_allclose(
        rebuilt_df['npv_penalty_pct'].to_numpy(dtype=float),
        np.asarray(expected, dtype=float),
        rtol=1e-9,
        atol=1e-9,
        equal_nan=True,
    )
    trane = rebuilt_df[rebuilt_df['model'].str.contains('Trane')].iloc[0]
    assert trane['npv_penalty_pct'] < 0, (
        "Discounting shrinks the Trane loss; penalty must be negative"
    )
    rheem = rebuilt_df[rebuilt_df['model'].str.contains('Rheem')].iloc[0]
    assert rheem['npv_penalty_pct'] > 0, (
        "Discounting shrinks the Rheem surplus; penalty must be positive"
    )
