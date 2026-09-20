"""
Core analysis pipeline for Replacement Trap.

Single source of truth for building the analysis DataFrame and golden
reference outputs. Used by the core notebook and regenerate script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from replacement_trap_config import (
    BASELINES,
    DISHWASHER_CYCLES_PER_YEAR,
    EFFICIENCY_DEGRADATION_RATE,
    ELECTRICITY_RATE,
    HELOC_LOAN_TERM,
    HELOC_RATE,
    SYSTEMS_DATA_PATH,
    TIME_HORIZON,
)
from replacement_trap_utils import (
    calculate_ac_annual_cost,
    calculate_dishwasher_annual_cost,
    calculate_lifetime_value_cash,
    calculate_lifetime_value_heloc,
    calculate_lifetime_value_scenario_b_cash,
    calculate_lifetime_value_scenario_b_heloc,
    calculate_payback_period,
    calculate_rp_ratio,
    calculate_scenario_b_rp,
    calculate_water_heater_annual_cost,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_core_dataframe(systems_data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Build the full analysis DataFrame (Scenario A + B metrics and comfort gap).

    Args:
        systems_data_path: Optional override for systems-data.json location.
    """
    path = systems_data_path or SYSTEMS_DATA_PATH
    systems_json = json.loads(path.read_text(encoding='utf-8'))
    categories = systems_json['appliance_categories']
    systems_list = []

    dishwasher_baseline = BASELINES['Dishwasher']
    baseline_dw_cost = calculate_dishwasher_annual_cost(
        dishwasher_baseline['annual_kWh_point'],
        dishwasher_baseline['water_gal_per_cycle'],
        DISHWASHER_CYCLES_PER_YEAR,
        include_labor_savings=False,
    )
    for model in categories['Category 1: Dishwashers']['Models']:
        annual_cost = calculate_dishwasher_annual_cost(
            model['annual_kWh'],
            model['water_gal_per_cycle'],
            DISHWASHER_CYCLES_PER_YEAR,
            include_labor_savings=False,
        )
        systems_list.append({
            'category': 'Dishwasher',
            'model': model['Model'],
            'lifespan_years': model['expected_lifespan_years'],
            'warranty_years': model['warranty_years'],
            'installed_cost': model['installed_cost_usd'],
            'baseline_annual_cost': baseline_dw_cost,
            'annual_operating_cost': annual_cost,
            'annual_savings': baseline_dw_cost - annual_cost,
            'annual_kwh': model['annual_kWh'],
            'water_gal_per_cycle': model['water_gal_per_cycle'],
        })

    water_heater_baseline = BASELINES['Water Heater']
    baseline_wh_cost = calculate_water_heater_annual_cost(
        water_heater_baseline['annual_kWh_point']
    )
    for model in categories['Category 2: Water Heaters']['Models']:
        annual_cost = calculate_water_heater_annual_cost(model['annual_kWh'])
        systems_list.append({
            'category': 'Water Heater',
            'model': model['Model'],
            'lifespan_years': model['expected_lifespan_years'],
            'warranty_years': model['warranty_years'],
            'installed_cost': model['installed_cost_usd'],
            'baseline_annual_cost': baseline_wh_cost,
            'annual_operating_cost': annual_cost,
            'annual_savings': baseline_wh_cost - annual_cost,
            'annual_kwh': model['annual_kWh'],
        })

    ac_baseline = BASELINES['Air Conditioner']
    baseline_ac_cost = calculate_ac_annual_cost(ac_baseline['annual_kWh_point'])
    for model in categories['Category 3: Air Conditioning - Atlanta']['Models']:
        annual_cost = calculate_ac_annual_cost(model['annual_kWh'])
        systems_list.append({
            'category': 'Air Conditioner',
            'model': model['Model'],
            'lifespan_years': model['expected_lifespan_years'],
            'warranty_years': model['warranty_years'],
            'installed_cost': model['installed_cost_usd'],
            'baseline_annual_cost': baseline_ac_cost,
            'annual_operating_cost': annual_cost,
            'annual_savings': baseline_ac_cost - annual_cost,
            'annual_kwh': model['annual_kWh'],
        })

    lighting_baseline = BASELINES['Lighting']
    baseline_lighting_cost = calculate_ac_annual_cost(lighting_baseline['annual_kWh_point'])
    for model in categories['Category 4: Lighting - LED Retrofits']['Models']:
        annual_cost = calculate_ac_annual_cost(model['annual_kWh'])
        systems_list.append({
            'category': 'Lighting',
            'model': model['Model'],
            'lifespan_years': model['expected_lifespan_years'],
            'warranty_years': model['warranty_years'],
            'installed_cost': model['installed_cost_usd'],
            'baseline_annual_cost': baseline_lighting_cost,
            'annual_operating_cost': annual_cost,
            'annual_savings': baseline_lighting_cost - annual_cost,
            'annual_kwh': model['annual_kWh'],
        })

    insulation_baseline = BASELINES['Attic Insulation']
    baseline_insulation_cost = calculate_ac_annual_cost(
        insulation_baseline['annual_kWh_point']
    )
    for model in categories['Category 5: Attic Insulation Upgrades']['Models']:
        annual_savings = model['annual_kWh_savings'] * ELECTRICITY_RATE
        annual_kwh_post_upgrade = (
            insulation_baseline['annual_kWh_point'] - model['annual_kWh_savings']
        )
        annual_cost = calculate_ac_annual_cost(annual_kwh_post_upgrade)
        systems_list.append({
            'category': 'Attic Insulation',
            'model': model['Model'],
            'lifespan_years': model['expected_lifespan_years'],
            'warranty_years': model['warranty_years'],
            'installed_cost': model['installed_cost_usd'],
            'baseline_annual_cost': baseline_insulation_cost,
            'annual_operating_cost': annual_cost,
            'annual_savings': annual_savings,
            'annual_kwh': annual_kwh_post_upgrade,
            'annual_kwh_savings_raw': model['annual_kWh_savings'],
        })

    df = pd.DataFrame(systems_list)

    df['payback_period'] = df.apply(
        lambda row: calculate_payback_period(row['installed_cost'], row['annual_savings']),
        axis=1,
    )
    df['rp_ratio_scenario_a'] = df.apply(
        lambda row: calculate_rp_ratio(row['lifespan_years'], row['payback_period']),
        axis=1,
    )
    df['rp_ratio_low'] = (df['lifespan_years'] * 0.8) / df['payback_period']
    df['rp_ratio_high'] = (df['lifespan_years'] * 1.2) / df['payback_period']
    df['rp_ratio_scenario_b'] = df.apply(
        lambda row: calculate_scenario_b_rp(
            row['lifespan_years'],
            row['warranty_years'],
            row['payback_period'],
        ),
        axis=1,
    )

    def cash_a(row):
        cash_flow, cash_npv = calculate_lifetime_value_cash(
            row['installed_cost'],
            row['annual_savings'],
            row['lifespan_years'],
            horizon=TIME_HORIZON,
            degradation_rate=EFFICIENCY_DEGRADATION_RATE,
            discount_rate=0.04,
        )
        return pd.Series({
            'lifetime_value_cash_scenario_a': cash_flow[-1],
            'npv_cash_4pct': cash_npv,
        })

    def heloc_a(row):
        heloc_flow, heloc_npv = calculate_lifetime_value_heloc(
            row['installed_cost'],
            row['annual_savings'],
            row['lifespan_years'],
            rate=HELOC_RATE,
            loan_term=HELOC_LOAN_TERM,
            horizon=TIME_HORIZON,
            degradation_rate=EFFICIENCY_DEGRADATION_RATE,
            discount_rate=0.04,
        )
        return pd.Series({
            'lifetime_value_heloc_scenario_a': heloc_flow[-1],
            'npv_heloc_4pct': heloc_npv,
        })

    def cash_b(row):
        cash_flow, cash_npv = calculate_lifetime_value_scenario_b_cash(
            row['installed_cost'],
            row['annual_savings'],
            row['warranty_years'],
            horizon=TIME_HORIZON,
            degradation_rate=EFFICIENCY_DEGRADATION_RATE,
            discount_rate=0.04,
        )
        return pd.Series({
            'lifetime_value_cash_scenario_b': cash_flow[-1],
            'npv_cash_4pct_scenario_b': cash_npv,
        })

    def heloc_b(row):
        heloc_flow, heloc_npv = calculate_lifetime_value_scenario_b_heloc(
            row['installed_cost'],
            row['annual_savings'],
            row['warranty_years'],
            rate=HELOC_RATE,
            loan_term=HELOC_LOAN_TERM,
            horizon=TIME_HORIZON,
            degradation_rate=EFFICIENCY_DEGRADATION_RATE,
            discount_rate=0.04,
        )
        return pd.Series({
            'lifetime_value_heloc_scenario_b': heloc_flow[-1],
            'npv_heloc_4pct_scenario_b': heloc_npv,
        })

    df = pd.concat([df, df.apply(cash_a, axis=1), df.apply(heloc_a, axis=1)], axis=1)
    cash_values = df['lifetime_value_cash_scenario_a']
    heloc_values = df['lifetime_value_heloc_scenario_a']
    cash_npv_values = df['npv_cash_4pct']
    negative_cash_mask = cash_values < 0
    cash_zero_mask = np.isclose(cash_values, 0, atol=1e-9)
    financing_penalty = heloc_values - cash_values
    df['financing_penalty_usd'] = financing_penalty
    df['amplification_factor'] = np.where(
        negative_cash_mask,
        np.abs(financing_penalty / cash_values),
        np.nan,
    )
    df['npv_penalty_pct'] = np.where(
        cash_zero_mask,
        np.nan,
        (np.abs(cash_values) - np.abs(cash_npv_values)) / np.abs(cash_values) * 100,
    )
    df = pd.concat([df, df.apply(cash_b, axis=1), df.apply(heloc_b, axis=1)], axis=1)

    df['breakeven_annual_savings'] = df['installed_cost'] / df['lifespan_years']
    df['comfort_gap'] = df['breakeven_annual_savings'] - df['annual_savings']
    df['comfort_gap_per_hour'] = df['comfort_gap'] / 8760
    return df


def build_reference_outputs(df: pd.DataFrame) -> Dict[str, Any]:
    """Build the golden-metrics payload used for regression comparison."""
    finite_paybacks = df.loc[df['payback_period'] != np.inf, 'payback_period']

    def _indexed(series: pd.Series) -> Dict[str, Any]:
        # JSON object keys are strings; keep golden payload JSON-native.
        return {str(k): v for k, v in series.to_dict().items()}

    return {
        'payback_periods': _indexed(df['payback_period']),
        'rp_ratios_scenario_a': _indexed(df['rp_ratio_scenario_a']),
        'rp_ratio_mean': float(df['rp_ratio_scenario_a'].mean()),
        'rp_ratio_min': float(df['rp_ratio_scenario_a'].min()),
        'rp_ratio_max': float(df['rp_ratio_scenario_a'].max()),
        'lifetime_value_cash_scenario_a': _indexed(df['lifetime_value_cash_scenario_a']),
        'lifetime_value_heloc_scenario_a': _indexed(df['lifetime_value_heloc_scenario_a']),
        'mean_payback_period': float(finite_paybacks.mean()),
        'mean_cash_lifetime_value': float(df['lifetime_value_cash_scenario_a'].mean()),
        'mean_heloc_lifetime_value': float(df['lifetime_value_heloc_scenario_a'].mean()),
        'dishwasher_rp_mean': float(
            df[df['category'] == 'Dishwasher']['rp_ratio_scenario_a'].mean()
        ),
        'water_heater_rp_mean': float(
            df[df['category'] == 'Water Heater']['rp_ratio_scenario_a'].mean()
        ),
        'ac_rp_mean': float(
            df[df['category'] == 'Air Conditioner']['rp_ratio_scenario_a'].mean()
        ),
        'structural_loss_count': int((df['rp_ratio_scenario_a'] < 0.8).sum()),
        'surplus_generator_count': int((df['rp_ratio_scenario_a'] > 1.0).sum()),
        'rp_ratio_scenario_b_mean': float(df['rp_ratio_scenario_b'].mean()),
    }


def write_reference_outputs(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Path:
    """Write golden reference outputs JSON; return the path written."""
    path = output_path or (REPO_ROOT / 'data' / 'reference_outputs.json')
    payload = build_reference_outputs(df)
    path.write_text(json.dumps(payload, indent=2, default=str) + '\n', encoding='utf-8')
    return path
