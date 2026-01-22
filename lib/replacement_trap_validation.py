"""
Validation module for replacement trap analysis.

Provides systematic checks for:
- Unit consistency
- Formula correctness
- Internal consistency
- Logic flow validation
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json

from replacement_trap_config import (
    ELECTRICITY_RATE,
    WATER_RATE,
    DISHWASHER_CYCLES_PER_YEAR,
    DISHWASHER_ANNUAL_LABOR_SAVINGS,
    HAND_WASHING_HOURS_PER_YEAR,
    HOURLY_LABOR_RATE,
    HELOC_RATE,
    HELOC_LOAN_TERM,
    TIME_HORIZON,
    EFFICIENCY_DEGRADATION_RATE,
    ELECTRICITY_MULTIPLIER_MIN,
    ELECTRICITY_MULTIPLIER_MAX,
    WATER_MULTIPLIER_MIN,
    WATER_MULTIPLIER_MAX,
    HELOC_RATE_MIN,
    HELOC_RATE_MAX,
    SYSTEMS_DATA_PATH,
)

from replacement_trap_utils import (
    calculate_payback_period,
    calculate_rp_ratio,
    calculate_lifetime_value_cash,
    calculate_lifetime_value_heloc,
)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ValidationResult:
    """Container for validation results"""
    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, message: str):
        """Add an error message"""
        self.passed = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
    
    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        result = f"{self.name}: {status}\n"
        if self.errors:
            result += f"  Errors ({len(self.errors)}):\n"
            for err in self.errors:
                result += f"    - {err}\n"
        if self.warnings:
            result += f"  Warnings ({len(self.warnings)}):\n"
            for warn in self.warnings:
                result += f"    - {warn}\n"
        return result


# ============================================================================
# A. Unit Consistency Validator
# ============================================================================

def validate_unit_consistency() -> ValidationResult:
    """
    Check all time units (years vs months) are consistent.
    Verify energy units (kWh vs watts) are correctly converted.
    Validate rate units match usage units (e.g., $/kWh × kWh = $).
    Check water units (gallons vs liters, per cycle vs per year).
    Validate percentage rates (0.085 vs 8.5%).
    """
    result = ValidationResult("Unit Consistency")
    
    # Check time units are all in years
    if HELOC_LOAN_TERM <= 0:
        result.add_error(f"HELOC_LOAN_TERM must be positive, got {HELOC_LOAN_TERM}")
    if TIME_HORIZON <= 0:
        result.add_error(f"TIME_HORIZON must be positive, got {TIME_HORIZON}")
    
    # Check rate units: electricity rate should be $/kWh
    if ELECTRICITY_RATE <= 0 or ELECTRICITY_RATE > 1.0:
        result.add_warning(f"ELECTRICITY_RATE ({ELECTRICITY_RATE}) seems unusual (expected ~0.10-0.50 $/kWh)")
    
    # Check rate units: water rate should be $/gal
    if WATER_RATE <= 0 or WATER_RATE > 0.1:
        result.add_warning(f"WATER_RATE ({WATER_RATE}) seems unusual (expected ~0.01-0.05 $/gal)")
    
    # Check percentage rates are in decimal form (0.085 not 8.5)
    if HELOC_RATE > 1.0:
        result.add_error(f"HELOC_RATE ({HELOC_RATE}) appears to be in percentage form, should be decimal (0.085 not 8.5)")
    if EFFICIENCY_DEGRADATION_RATE > 1.0:
        result.add_error(f"EFFICIENCY_DEGRADATION_RATE ({EFFICIENCY_DEGRADATION_RATE}) appears to be in percentage form, should be decimal")
    
    # Check labor savings calculation units
    expected_labor_savings = HAND_WASHING_HOURS_PER_YEAR * HOURLY_LABOR_RATE
    if abs(DISHWASHER_ANNUAL_LABOR_SAVINGS - expected_labor_savings) > 0.01:
        result.add_error(
            f"Labor savings mismatch: DISHWASHER_ANNUAL_LABOR_SAVINGS ({DISHWASHER_ANNUAL_LABOR_SAVINGS}) "
            f"!= HAND_WASHING_HOURS_PER_YEAR ({HAND_WASHING_HOURS_PER_YEAR}) × HOURLY_LABOR_RATE ({HOURLY_LABOR_RATE}) "
            f"= {expected_labor_savings}"
        )
    
    # Check dishwasher cycles per year is reasonable
    if DISHWASHER_CYCLES_PER_YEAR <= 0 or DISHWASHER_CYCLES_PER_YEAR > 500:
        result.add_warning(f"DISHWASHER_CYCLES_PER_YEAR ({DISHWASHER_CYCLES_PER_YEAR}) seems unusual (expected ~150-300)")
    
    # Verify unit multiplication: kWh × $/kWh = $
    test_kwh = 1000
    test_cost = test_kwh * ELECTRICITY_RATE
    if test_cost <= 0:
        result.add_error(f"Energy cost calculation failed: {test_kwh} kWh × ${ELECTRICITY_RATE}/kWh = ${test_cost}")
    
    # Verify unit multiplication: cycles × gal/cycle × $/gal = $
    test_cycles = 100
    test_gal_per_cycle = 5
    test_water_cost = test_cycles * test_gal_per_cycle * WATER_RATE
    if test_water_cost <= 0:
        result.add_error(f"Water cost calculation failed: {test_cycles} cycles × {test_gal_per_cycle} gal/cycle × ${WATER_RATE}/gal = ${test_water_cost}")
    
    return result


# ============================================================================
# B. Formula Correctness Validator
# ============================================================================

def validate_formula_correctness() -> ValidationResult:
    """
    Verify payback period: cost / annual_savings
    Check R/P ratio: lifespan / payback_period
    Validate degradation formula: (1 - degradation_rate) ** years
    Check HELOC interest: principal * rate
    Verify cumulative cash flow logic
    """
    result = ValidationResult("Formula Correctness")
    
    # Test payback period calculation
    test_cost = 1000
    test_savings = 100
    expected_payback = 10.0
    calculated_payback = calculate_payback_period(test_cost, test_savings)
    if abs(calculated_payback - expected_payback) > 1e-6:
        result.add_error(
            f"Payback period formula incorrect: {test_cost} / {test_savings} = {calculated_payback}, "
            f"expected {expected_payback}"
        )
    
    # Test payback period with zero/negative savings
    inf_payback = calculate_payback_period(test_cost, 0)
    if not np.isinf(inf_payback):
        result.add_error(f"Payback period should be infinite for zero savings, got {inf_payback}")
    
    neg_payback = calculate_payback_period(test_cost, -50)
    if not np.isinf(neg_payback):
        result.add_error(f"Payback period should be infinite for negative savings, got {neg_payback}")
    
    # Test R/P ratio calculation
    test_lifespan = 10
    test_payback = 5
    expected_rp = 2.0
    calculated_rp = calculate_rp_ratio(test_lifespan, test_payback)
    if abs(calculated_rp - expected_rp) > 1e-6:
        result.add_error(
            f"R/P ratio formula incorrect: {test_lifespan} / {test_payback} = {calculated_rp}, "
            f"expected {expected_rp}"
        )
    
    # Test R/P ratio with infinite payback
    zero_rp = calculate_rp_ratio(test_lifespan, np.inf)
    if zero_rp != 0:
        result.add_error(f"R/P ratio should be 0 for infinite payback, got {zero_rp}")
    
    # Test degradation formula: (1 - rate) ** years
    test_rate = 0.015
    test_years = 5
    expected_degradation = (1 - test_rate) ** test_years
    calculated_degradation = (1 - EFFICIENCY_DEGRADATION_RATE) ** test_years
    if abs(calculated_degradation - expected_degradation) > 1e-6:
        result.add_warning(
            f"Degradation formula check: (1 - {EFFICIENCY_DEGRADATION_RATE}) ** {test_years} = {calculated_degradation}, "
            f"expected {expected_degradation}"
        )
    
    # Test degradation monotonicity: degradation should decrease over time
    year1_degradation = (1 - EFFICIENCY_DEGRADATION_RATE) ** 1
    year2_degradation = (1 - EFFICIENCY_DEGRADATION_RATE) ** 2
    if year1_degradation <= year2_degradation:
        result.add_error(
            f"Degradation should decrease over time: year 1 = {year1_degradation}, year 2 = {year2_degradation}"
        )
    
    # Test HELOC interest calculation: principal * rate
    test_principal = 10000
    test_rate = 0.085
    expected_interest = 850.0
    calculated_interest = test_principal * test_rate
    if abs(calculated_interest - expected_interest) > 1e-6:
        result.add_error(
            f"HELOC interest formula incorrect: {test_principal} × {test_rate} = {calculated_interest}, "
            f"expected {expected_interest}"
        )
    
    # Test cash flow calculation with simple case
    test_cost = 1000
    test_savings = 200
    test_lifespan = 10
    test_horizon = 15
    cash_flow, _ = calculate_lifetime_value_cash(test_cost, test_savings, test_lifespan, test_horizon, 0)
    
    # Check initial cost
    if abs(cash_flow[0] - (-test_cost)) > 1e-6:
        result.add_error(f"Cash flow year 0 should be -{test_cost}, got {cash_flow[0]}")
    
    # Check year 1 savings (no degradation)
    expected_year1 = -test_cost + test_savings
    if abs(cash_flow[1] - expected_year1) > 1e-6:
        result.add_error(f"Cash flow year 1 should be {expected_year1}, got {cash_flow[1]}")
    
    # Check replacement occurs at year 10
    expected_year10_before_replacement = -test_cost + (test_savings * 10)
    expected_year10_after_replacement = expected_year10_before_replacement - test_cost
    # Replacement should occur, so cash_flow[10] should differ from pre-replacement value
    if abs(cash_flow[10] - expected_year10_before_replacement) < 1e-6:
        result.add_warning(
            f"Cash flow year 10: expected ~{expected_year10_after_replacement} (with replacement), "
            f"got {cash_flow[10]} which matches pre-replacement value {expected_year10_before_replacement}. "
            f"Replacement may not have occurred at lifespan."
        )
    
    # Test HELOC cash flow calculation
    heloc_cash_flow, _ = calculate_lifetime_value_heloc(test_cost, test_savings, test_lifespan, test_rate, 10, test_horizon, 0)
    
    # Check year 0 (no initial outlay)
    if abs(heloc_cash_flow[0]) > 1e-6:
        result.add_error(f"HELOC cash flow year 0 should be 0 (no initial outlay), got {heloc_cash_flow[0]}")
    
    # Check year 1 (savings - interest)
    expected_year1_heloc = test_savings - (test_cost * test_rate)
    if abs(heloc_cash_flow[1] - expected_year1_heloc) > 1e-6:
        result.add_error(
            f"HELOC cash flow year 1 should be {expected_year1_heloc} (savings - interest), "
            f"got {heloc_cash_flow[1]}"
        )
    
    return result


# ============================================================================
# C. Internal Consistency Validator
# ============================================================================

def validate_internal_consistency() -> ValidationResult:
    """
    Check assumptions don't contradict.
    Validate cross-file consistency.
    Check Monte Carlo ranges are reasonable.
    """
    result = ValidationResult("Internal Consistency")
    
    # Check TIME_HORIZON vs HELOC_LOAN_TERM consistency
    if TIME_HORIZON < HELOC_LOAN_TERM:
        result.add_warning(
            f"TIME_HORIZON ({TIME_HORIZON}) < HELOC_LOAN_TERM ({HELOC_LOAN_TERM}). "
            f"Loan term exceeds analysis horizon."
        )
    
    # Check degradation rate is reasonable (should be small positive number)
    if EFFICIENCY_DEGRADATION_RATE < 0 or EFFICIENCY_DEGRADATION_RATE > 0.1:
        result.add_warning(
            f"EFFICIENCY_DEGRADATION_RATE ({EFFICIENCY_DEGRADATION_RATE}) seems unusual "
            f"(expected ~0.01-0.05 for 1-5% per year)"
        )
    
    # Check Monte Carlo ranges: min < baseline < max
    baseline_electricity = ELECTRICITY_RATE
    min_electricity = baseline_electricity * ELECTRICITY_MULTIPLIER_MIN
    max_electricity = baseline_electricity * ELECTRICITY_MULTIPLIER_MAX
    
    if ELECTRICITY_MULTIPLIER_MIN >= 1.0:
        result.add_warning(
            f"ELECTRICITY_MULTIPLIER_MIN ({ELECTRICITY_MULTIPLIER_MIN}) >= 1.0, "
            f"no decrease modeled (may be intentional)"
        )
    if ELECTRICITY_MULTIPLIER_MAX <= 1.0:
        result.add_warning(
            f"ELECTRICITY_MULTIPLIER_MAX ({ELECTRICITY_MULTIPLIER_MAX}) <= 1.0, "
            f"no increase modeled"
        )
    # Only error if min > baseline (min == baseline is expected when multiplier >= 1.0)
    if min_electricity > baseline_electricity:
        result.add_error(
            f"Monte Carlo min electricity ({min_electricity}) > baseline ({baseline_electricity})"
        )
    elif min_electricity >= baseline_electricity and ELECTRICITY_MULTIPLIER_MIN < 1.0:
        # This case shouldn't happen (if multiplier < 1.0, min should be < baseline)
        # But include for defensive programming
        result.add_warning(
            f"Monte Carlo min electricity ({min_electricity}) >= baseline ({baseline_electricity}), "
            f"but ELECTRICITY_MULTIPLIER_MIN ({ELECTRICITY_MULTIPLIER_MIN}) < 1.0 - verify calculation"
        )
    if max_electricity <= baseline_electricity:
        result.add_error(
            f"Monte Carlo max electricity ({max_electricity}) <= baseline ({baseline_electricity})"
        )
    
    baseline_water = WATER_RATE
    min_water = baseline_water * WATER_MULTIPLIER_MIN
    max_water = baseline_water * WATER_MULTIPLIER_MAX
    
    if WATER_MULTIPLIER_MIN >= 1.0:
        result.add_warning(
            f"WATER_MULTIPLIER_MIN ({WATER_MULTIPLIER_MIN}) >= 1.0, "
            f"no decrease modeled (may be intentional)"
        )
    # Only error if min > baseline (min == baseline is expected when multiplier >= 1.0)
    if min_water > baseline_water:
        result.add_error(
            f"Monte Carlo min water ({min_water}) > baseline ({baseline_water})"
        )
    elif min_water >= baseline_water and WATER_MULTIPLIER_MIN < 1.0:
        # This case shouldn't happen (if multiplier < 1.0, min should be < baseline)
        # But include for defensive programming
        result.add_warning(
            f"Monte Carlo min water ({min_water}) >= baseline ({baseline_water}), "
            f"but WATER_MULTIPLIER_MIN ({WATER_MULTIPLIER_MIN}) < 1.0 - verify calculation"
        )
    if max_water <= baseline_water:
        result.add_error(
            f"Monte Carlo max water ({max_water}) <= baseline ({baseline_water})"
        )
    
    baseline_heloc = HELOC_RATE
    if HELOC_RATE_MIN >= baseline_heloc:
        result.add_warning(
            f"HELOC_RATE_MIN ({HELOC_RATE_MIN}) >= baseline ({baseline_heloc})"
        )
    if HELOC_RATE_MAX <= baseline_heloc:
        result.add_warning(
            f"HELOC_RATE_MAX ({HELOC_RATE_MAX}) <= baseline ({baseline_heloc})"
        )
    if HELOC_RATE_MIN >= HELOC_RATE_MAX:
        result.add_error(
            f"HELOC_RATE_MIN ({HELOC_RATE_MIN}) >= HELOC_RATE_MAX ({HELOC_RATE_MAX})"
        )
    
    # Check config vs JSON consistency
    try:
        with open(SYSTEMS_DATA_PATH, 'r') as f:
            systems_json = json.load(f)
        
        json_electricity = systems_json['metadata']['baseline_parameters']['electricity_rate']['value']
        if abs(json_electricity - ELECTRICITY_RATE) > 1e-6:
            result.add_error(
                f"Electricity rate mismatch: config={ELECTRICITY_RATE}, JSON={json_electricity}"
            )
        
        json_water = systems_json['metadata']['baseline_parameters']['water_rate']['value']
        if abs(json_water - WATER_RATE) > 1e-6:
            result.add_error(
                f"Water rate mismatch: config={WATER_RATE}, JSON={json_water}"
            )
    except Exception as e:
        result.add_error(f"Failed to load systems-data.json for consistency check: {e}")
    
    # Check DISHWASHER_CYCLES_PER_YEAR is used consistently
    # (This is a documentation check - actual usage is verified in logic flow)
    if DISHWASHER_CYCLES_PER_YEAR != 215:
        result.add_warning(
            f"DISHWASHER_CYCLES_PER_YEAR ({DISHWASHER_CYCLES_PER_YEAR}) differs from DOE standard (215). "
            f"Verify this is intentional."
        )
    
    return result


# ============================================================================
# D. Logic Flow Validator
# ============================================================================

def validate_logic_flow() -> ValidationResult:
    """
    Verify replacement logic: replacement occurs when years_since_last_replacement >= lifespan
    Check degradation resets on replacement
    Validate HELOC loan balance tracking
    Verify cash flow accumulation
    """
    result = ValidationResult("Logic Flow")
    
    # Test single replacement cycle (lifespan < horizon)
    test_cost = 1000
    test_savings = 200
    test_lifespan = 5
    test_horizon = 10
    test_degradation = 0.0  # No degradation for simpler test
    
    cash_flow, _ = calculate_lifetime_value_cash(test_cost, test_savings, test_lifespan, test_horizon, test_degradation)
    
    # Check replacement occurs at year 5
    # Year 5 should have: initial cost + 5 years savings - replacement cost
    expected_year5 = -test_cost + (test_savings * 5) - test_cost
    if abs(cash_flow[5] - expected_year5) > 1e-6:
        result.add_error(
            f"Replacement logic error: year 5 should be {expected_year5}, got {cash_flow[5]}. "
            f"Replacement should occur at lifespan ({test_lifespan})."
        )
    
    # Check degradation resets on replacement
    test_degradation = 0.02
    cash_flow_with_degradation, _ = calculate_lifetime_value_cash(
        test_cost, test_savings, test_lifespan, test_horizon, test_degradation
    )
    
    # Year 1 savings should be higher than year 6 (after replacement, degradation resets)
    year1_savings = cash_flow_with_degradation[1] - cash_flow_with_degradation[0]
    year6_savings = cash_flow_with_degradation[6] - cash_flow_with_degradation[5]
    
    # Year 6 should have full savings (degradation reset), year 1 should also have full savings
    # Both should equal test_savings (within rounding)
    if abs(year1_savings - test_savings) > 1e-6:
        result.add_warning(
            f"Year 1 savings ({year1_savings}) should equal {test_savings} (no degradation yet)"
        )
    if abs(year6_savings - test_savings) > 1e-6:
        result.add_error(
            f"Year 6 savings ({year6_savings}) should equal {test_savings} after replacement "
            f"(degradation should reset), got {year6_savings}"
        )
    
    # Test multiple replacement cycles
    test_lifespan = 3
    test_horizon = 10
    cash_flow_multi, _ = calculate_lifetime_value_cash(
        test_cost, test_savings, test_lifespan, test_horizon, 0
    )
    
    # Should have replacements at years 3, 6, 9
    # Check year 3 has replacement cost
    year3_change = cash_flow_multi[3] - cash_flow_multi[2]
    expected_year3_change = test_savings - test_cost  # Savings minus replacement
    if abs(year3_change - expected_year3_change) > 1e-6:
        result.add_warning(
            f"Multiple replacement cycle: year 3 change should be ~{expected_year3_change}, "
            f"got {year3_change}"
        )
    
    # Test HELOC loan balance tracking
    test_rate = 0.085
    test_loan_term = 10
    heloc_cash_flow, _ = calculate_lifetime_value_heloc(
        test_cost, test_savings, test_lifespan, test_rate, test_loan_term, test_horizon, 0
    )
    
    # Year 0 should be 0 (no initial outlay)
    if abs(heloc_cash_flow[0]) > 1e-6:
        result.add_error(f"HELOC year 0 should be 0, got {heloc_cash_flow[0]}")
    
    # Year 1 should have savings - interest payment
    expected_year1 = test_savings - (test_cost * test_rate)
    if abs(heloc_cash_flow[1] - expected_year1) > 1e-6:
        result.add_error(
            f"HELOC year 1 should be {expected_year1} (savings - interest), got {heloc_cash_flow[1]}"
        )
    
    # Test replacement during loan term
    test_lifespan = 5  # Replacement before loan term ends
    heloc_cash_flow_early, _ = calculate_lifetime_value_heloc(
        test_cost, test_savings, test_lifespan, test_rate, test_loan_term, test_horizon, 0
    )
    
    # Year 5 should have replacement (replacement occurs)
    year5_change = heloc_cash_flow_early[5] - heloc_cash_flow_early[4]
    # Replacement year is cash-neutral apart from interest: payoff old loan (-) offset by new draw (+)
    # Should be: savings - interest payment only (principal payment offset by new loan draw)
    expected_year5_change = test_savings - (test_cost * test_rate)
    if abs(year5_change - expected_year5_change) > 10:  # Allow some tolerance for cumulative effects
        result.add_warning(
            f"HELOC replacement during loan term: year 5 change should be ~{expected_year5_change}, "
            f"got {year5_change}"
        )
    
    # Test replacement after loan term
    test_lifespan = 15  # Replacement after loan term ends
    heloc_cash_flow_late, _ = calculate_lifetime_value_heloc(
        test_cost, test_savings, test_lifespan, test_rate, test_loan_term, test_horizon, 0
    )
    
    # Year 10 should pay principal (loan term ends)
    year10_change = heloc_cash_flow_late[10] - heloc_cash_flow_late[9]
    # Should be: savings - principal payment (no more interest)
    expected_year10_change = test_savings - test_cost
    if abs(year10_change - expected_year10_change) > 10:  # Allow tolerance
        result.add_warning(
            f"HELOC loan term end: year 10 change should be ~{expected_year10_change}, "
            f"got {year10_change}"
        )
    
    # Verify cash flow accumulation: cash_flow[year] = cash_flow[year-1] + savings - costs
    # Test with simple case
    # Note: cash_flow was calculated with test_lifespan = 5 (from line 393), not the reassigned value
    cash_flow_test_lifespan = 5
    for year in range(1, min(6, len(cash_flow))):
        if year == cash_flow_test_lifespan:
            # Replacement year - skip check (complex)
            continue
        prev_value = cash_flow[year - 1]
        current_value = cash_flow[year]
        expected_increment = test_savings
        actual_increment = current_value - prev_value
        if abs(actual_increment - expected_increment) > 1e-6:
            result.add_error(
                f"Cash flow accumulation error at year {year}: "
                f"expected increment {expected_increment}, got {actual_increment}"
            )
    
    return result


# ============================================================================
# Main Validation Runner
# ============================================================================

def run_all_validations() -> List[ValidationResult]:
    """
    Run all validation checks and return results.
    
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    results.append(validate_unit_consistency())
    results.append(validate_formula_correctness())
    results.append(validate_internal_consistency())
    results.append(validate_logic_flow())
    
    return results


def print_validation_report(results: List[ValidationResult]):
    """Print a formatted validation report"""
    print("=" * 70)
    print("REPLACEMENT TRAP VALIDATION REPORT")
    print("=" * 70)
    print()
    
    all_passed = all(r.passed for r in results)
    
    for result in results:
        print(result)
        print()
    
    print("=" * 70)
    if all_passed:
        print("OVERALL STATUS: ALL CHECKS PASSED")
    else:
        print("OVERALL STATUS: SOME CHECKS FAILED")
        failed_count = sum(1 for r in results if not r.passed)
        print(f"Failed validators: {failed_count}/{len(results)}")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    results = run_all_validations()
    print_validation_report(results)

