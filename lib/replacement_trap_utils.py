"""
Utility functions for replacement trap analysis.

Contains all calculation functions, validation, and comparison utilities.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any

from replacement_trap_config import (
    ELECTRICITY_RATE,
    WATER_RATE,
    DISHWASHER_CYCLES_PER_YEAR,
    DISHWASHER_ANNUAL_LABOR_SAVINGS,
    HELOC_RATE,
    HELOC_LOAN_TERM,
    TIME_HORIZON,
    EFFICIENCY_DEGRADATION_RATE,
)


def get_notebooks_root():
    """
    Find the notebooks root directory (containing lib/ and data/ subdirectories).
    
    Works in both Python scripts (using __file__) and Jupyter notebooks (using cwd).
    Handles various execution contexts and working directories.
    
    Returns:
        Path to notebooks root directory
    """
    # If running as a script, use __file__
    if '__file__' in globals():
        return Path(__file__).parent.parent
    
    # Otherwise, we're in a Jupyter notebook - find notebooks root
    cwd = Path.cwd()
    
    # Check if we're in analysis directory (notebooks/analysis/)
    if (cwd.parent / 'lib' / 'replacement_trap_utils.py').exists() and cwd.name == 'analysis':
        return cwd.parent
    # Check if we're in notebooks directory (notebooks/)
    elif (cwd / 'lib' / 'replacement_trap_utils.py').exists():
        return cwd
    # Check if notebooks directory is a subdirectory
    elif (cwd / 'notebooks' / 'lib' / 'replacement_trap_utils.py').exists():
        return cwd / 'notebooks'
    # Walk up from current directory
    else:
        for parent in [cwd] + list(cwd.parents):
            if (parent / 'lib' / 'replacement_trap_utils.py').exists():
                return parent
    
    # Fallback: assume we're in analysis/ directory
    return cwd.parent if cwd.name == 'analysis' else cwd


def calculate_dishwasher_annual_cost(kwh_per_year, gal_per_cycle, cycles_per_year=None,
                                      include_labor_savings=True):
    """
    Calculate annual operating cost for dishwasher.
    
    Includes labor savings vs hand-washing (all dishwashers save time).
    Labor savings reduce the effective annual cost.
    
    Args:
        kwh_per_year: Annual electricity consumption in kWh
        gal_per_cycle: Water consumption per cycle in gallons
        cycles_per_year: Number of dishwasher cycles per year (default from config)
        include_labor_savings: If True, subtract labor savings from cost (default True)
    
    Returns:
        Annual operating cost (energy + water - labor savings)
    
    Labor Savings Logic:
    -------------------
    Labor savings represent time saved vs hand-washing (~182.5 hours/year = $2,737.50/year).
    
    When comparing old dishwasher → new dishwasher:
    - Both units provide identical labor benefit vs hand-washing
    - Net labor savings difference = 0
    - Therefore, set include_labor_savings=False for replacement comparisons
    - Only energy/water differences matter for ROI calculation
    
    Labor savings only matter when comparing:
    - Hand-washing → Any dishwasher (saves labor)
    - No dishwasher → New dishwasher (saves labor)
    
    Usage in replacement_trap_core.ipynb:
    - Both baseline and new model use include_labor_savings=False
    - This correctly excludes labor from annual_savings calculation
    """
    if cycles_per_year is None:
        cycles_per_year = DISHWASHER_CYCLES_PER_YEAR
    
    energy_cost = kwh_per_year * ELECTRICITY_RATE
    water_cost = cycles_per_year * gal_per_cycle * WATER_RATE
    operating_cost = energy_cost + water_cost
    
    if include_labor_savings:
        # Subtract labor savings (labor is a negative cost)
        operating_cost = operating_cost - DISHWASHER_ANNUAL_LABOR_SAVINGS
    
    return operating_cost


def calculate_water_heater_annual_cost(kwh_per_year):
    """Calculate annual operating cost for water heater"""
    return kwh_per_year * ELECTRICITY_RATE


def calculate_ac_annual_cost(kwh_per_year):
    """Calculate annual operating cost for AC"""
    return kwh_per_year * ELECTRICITY_RATE


def calculate_payback_period(installed_cost, annual_savings):
    """Calculate simple payback period in years"""
    if annual_savings <= 0:
        return np.inf
    return installed_cost / annual_savings


def calculate_rp_ratio(lifespan, payback_period):
    """
    Calculate Replacement/Payback ratio
    
    Args:
        lifespan: Expected lifespan in years
        payback_period: Payback period in years (must be positive)
    
    Returns:
        R/P ratio (lifespan / payback_period), or 0 if payback is infinite/negative
    """
    if payback_period == np.inf or payback_period <= 0:
        return 0
    return lifespan / payback_period


def calculate_npv(cash_flows, discount_rate=0.04):
    """
    Calculate net present value of annual cash flows using a 4% default discount rate.

    Args:
        cash_flows: Iterable of cash flows by year (year 0 to N)
        discount_rate: Annual discount rate (default 4%)

    Returns:
        Net present value of the cash flow stream
    """
    npv = 0.0
    for year, cash_flow in enumerate(cash_flows):
        npv += cash_flow / ((1 + discount_rate) ** year)
    return npv


def calculate_lifetime_value_cash(installed_cost, annual_savings, lifespan, horizon=None,
                                  degradation_rate=None, discount_rate=0.04):
    """
    Calculate cumulative and discounted cash flows over the time horizon with a cash purchase.
    Accounts for multiple replacement cycles, efficiency degradation, and an optional discount rate.
    
    Args:
        installed_cost: Initial installed cost
        annual_savings: Annual savings in year 1 (before degradation)
        lifespan: Expected lifespan in years
        horizon: Time horizon in years (default from config)
        degradation_rate: Annual efficiency degradation rate (default from config)
        discount_rate: Annual discount rate for NPV (default 4%). Pass None to skip NPV.

    Returns:
        Tuple of (cumulative cash flow array by year, discounted NPV or None when disabled)
    
    Replacement Logic:
    ------------------
    Models "Emergency replacement at expected lifespan" - captures real-world behavioral
    pattern (replacing at failure) with deterministic timing at expected lifespan.
    
    Behavioral pattern: People know when appliances are getting old but wait until failure
    rather than replacing proactively. First-time homeowners typically replace at failure,
    not proactively.
    
    Conservative assumption: Real-world emergency replacements cost 20-30% more due to rush
    fees, limited shopping time, and contractor markup. We model same cost at expected
    lifespan (documented, not modeled - conclusion is robust). If deterministic replacement
    shows a replacement trap, real emergency replacement (higher cost, potentially earlier
    failure) would show worse outcomes. This conservative approach strengthens the replacement
    trap thesis.
    """
    if horizon is None:
        horizon = TIME_HORIZON
    if degradation_rate is None:
        degradation_rate = EFFICIENCY_DEGRADATION_RATE
    
    cash_flow = np.zeros(horizon + 1)
    annual_cash_flow = None
    cash_flow[0] = -installed_cost  # Initial purchase
    if discount_rate is not None:
        annual_cash_flow = np.zeros(horizon + 1)
        annual_cash_flow[0] = cash_flow[0]

    years_since_last_replacement = 0

    for year in range(1, horizon + 1):
        # Apply efficiency degradation: savings decline by degradation_rate per year
        # Degradation resets to 0 when unit is replaced
        # Calculate degradation BEFORE incrementing so first year after replacement has no degradation
        degradation_factor = (1 - degradation_rate) ** years_since_last_replacement
        current_annual_savings = annual_savings * degradation_factor
        
        # Increment years since last replacement after calculating degradation
        years_since_last_replacement += 1
        
        # Add annual savings (with degradation applied)
        annual_cash = current_annual_savings

        # Replace if lifespan exceeded
        if years_since_last_replacement >= lifespan:
            annual_cash -= installed_cost
            years_since_last_replacement = 0  # Reset degradation counter

        cash_flow[year] = cash_flow[year - 1] + annual_cash
        if annual_cash_flow is not None:
            annual_cash_flow[year] = annual_cash

    npv_value = None
    if annual_cash_flow is not None:
        npv_value = calculate_npv(annual_cash_flow, discount_rate=discount_rate)
    return cash_flow, npv_value


def calculate_lifetime_value_heloc(installed_cost, annual_savings, lifespan,
                                   rate=None, loan_term=None, horizon=None,
                                   degradation_rate=None, discount_rate=0.04):
    """
    Calculate cumulative and discounted cash flow with HELOC financing (interest-only for first 10 years).
    Accounts for efficiency degradation and an optional discount rate for NPV.

    Args:
        installed_cost: Initial installed cost
        annual_savings: Annual savings in year 1 (before degradation)
        lifespan: Expected lifespan in years
        rate: Annual interest rate (default from config)
        loan_term: Loan term in years (default from config) - interest-only period
        horizon: Time horizon in years (default from config)
        degradation_rate: Annual efficiency degradation rate (default from config)
        discount_rate: Annual discount rate for NPV (default 4%). Pass None to skip NPV.

    Returns:
        Tuple of (cumulative cash flow array by year, discounted NPV or None when disabled)
    
    Replacement Logic:
    ------------------
    Models "Emergency replacement at expected lifespan" - captures real-world behavioral
    pattern (replacing at failure) with deterministic timing at expected lifespan.
    
    Behavioral pattern: People know when appliances are getting old but wait until failure
    rather than replacing proactively. First-time homeowners typically replace at failure,
    not proactively.
    
    Conservative assumption: Real-world emergency replacements cost 20-30% more due to rush
    fees, limited shopping time, and contractor markup. We model same cost at expected
    lifespan (documented, not modeled - conclusion is robust). If deterministic replacement
    shows a replacement trap, real emergency replacement (higher cost, potentially earlier
    failure) would show worse outcomes. This conservative approach strengthens the replacement
    trap thesis.
    
    HELOC Principal Payment Logic:
    ------------------------------
    Principal is paid in one of two scenarios (whichever occurs first):
    
    1. At replacement time: When appliance reaches end of lifespan, homeowner pays off
       old HELOC principal and takes out new HELOC for replacement unit. This models the
       real-world pattern where homeowners roll debt forward by financing each replacement.
    
    2. At end of draw period: If no replacement occurs during the 10-year interest-only
       period, principal is paid when loan term ends (loan converts to amortization).
    
    This captures the "replacement trap" dynamic: if replacement cycles are shorter than
    payback periods, homeowners never build equity—they just roll debt forward with each
    replacement, paying interest indefinitely.
    
    Edge case: If replacement occurs exactly at year 10 (end of loan term), principal is
    paid for the old loan and a new loan is taken out in the same year (no double payment).
    """
    if rate is None:
        rate = HELOC_RATE
    if loan_term is None:
        loan_term = HELOC_LOAN_TERM
    if horizon is None:
        horizon = TIME_HORIZON
    if degradation_rate is None:
        degradation_rate = EFFICIENCY_DEGRADATION_RATE
    
    # Interest-only payment: only pay interest, not principal
    annual_interest_payment = installed_cost * rate

    cash_flow = np.zeros(horizon + 1)
    cash_flow[0] = 0  # No initial cash outlay (loan taken out at year 0)
    annual_cash_flow = None if discount_rate is None else np.zeros(horizon + 1)
    years_since_last_replacement = 0
    years_remaining_on_loan = loan_term  # Start with initial loan at year 0
    loan_balance = installed_cost  # Track principal balance

    for year in range(1, horizon + 1):
        # Apply efficiency degradation: savings decline by degradation_rate per year
        # Degradation resets to 0 when unit is replaced
        # Calculate degradation BEFORE incrementing so first year after replacement has no degradation
        degradation_factor = (1 - degradation_rate) ** years_since_last_replacement
        current_annual_savings = annual_savings * degradation_factor
        
        # Increment years since last replacement after calculating degradation
        years_since_last_replacement += 1
        
        # Check if replacement needed AFTER incrementing (so replacement occurs at correct year)
        # This ensures new loan payments start immediately when replacement happens
        replacement_occurred = False
        loan_balance_payment = 0  # Track loan balance payment for replacement
        new_loan_draw = 0  # Track new HELOC draw when replacing
        # Save old loan state before potential replacement (needed for branch logic)
        was_in_interest_period = years_remaining_on_loan > 0
        if years_since_last_replacement >= lifespan:
            # Pay off remaining principal balance when replacing
            loan_balance_payment = loan_balance
            # Take out new loan - payments start this year
            # Record the cash inflow from the new HELOC draw (rolls debt forward)
            if loan_balance > 0:
                # Existing loan still active: payoff old balance, draw new loan (net 0 apart from interest)
                new_loan_draw = installed_cost
            else:
                # Old loan already paid off: homeowner fronts replacement cost, then draws new HELOC
                # (net cash impact remains 0, but cost isn't treated as "free").
                loan_balance_payment = installed_cost
                new_loan_draw = installed_cost
            loan_balance = installed_cost
            years_remaining_on_loan = loan_term
            years_since_last_replacement = 0  # Reset degradation counter
            replacement_occurred = True
            # If replacement occurred after loan term ended, don't pay interest on new loan this year
            # (interest starts next year, similar to initial loan at year 0)
            if not was_in_interest_period:
                # Skip interest payment for replacement year when old loan was already paid off
                pass

        annual_cash = current_annual_savings

        # Net annual cash flow = savings - interest payment (if still in interest-only period)
        # Use was_in_interest_period to determine branch when replacement occurred
        if was_in_interest_period or (years_remaining_on_loan > 0 and not replacement_occurred):
            # Still in interest-only period
            # Account for loan balance payment and new loan draw if replacement occurred
            # Replacement year is cash-neutral apart from interest: payoff old loan (-) offset by new draw (+)
            annual_cash -= annual_interest_payment
            annual_cash -= loan_balance_payment
            annual_cash += new_loan_draw
            # Only decrement the remaining term when we did NOT just start a new loan.
            # If a replacement occurred, the interest this year belonged to the old loan,
            # and the new loan should start next year with the full `loan_term`.
            if not replacement_occurred:
                years_remaining_on_loan -= 1
            # Check if loan term just ended (transitioning from 1 to 0)
            # Only pay principal if replacement didn't occur this year (replacement already paid it)
            if years_remaining_on_loan == 0 and loan_balance > 0 and not replacement_occurred:
                # Pay principal when loan term ends (and no replacement occurred)
                annual_cash -= loan_balance
                loan_balance = 0
        else:
            # After interest-only period ends, principal already paid
            # Account for loan balance payment and new loan draw if replacement occurred
            # Replacement year is cash-neutral apart from interest: payoff old loan (-) offset by new draw (+)
            annual_cash -= loan_balance_payment
            annual_cash += new_loan_draw

        cash_flow[year] = cash_flow[year - 1] + annual_cash
        if annual_cash_flow is not None:
            annual_cash_flow[year] = annual_cash

    npv_value = None
    if annual_cash_flow is not None:
        npv_value = calculate_npv(annual_cash_flow, discount_rate=discount_rate)
    return cash_flow, npv_value


def calculate_scenario_b_rp(expected_lifespan, warranty_years, payback_period):
    """
    Calculate R/P ratio for proactive replacement at warranty expiration.

    Effective lifespan = warranty years (when you actually replace)
    This is always worse than emergency replacement scenario.

    Mirrors `calculate_rp_ratio` behavior: return 0 when payback is
    infinite or non-positive (including zero-cost immediate payback).
    """
    if payback_period == np.inf or payback_period <= 0:
        return 0
    return warranty_years / payback_period


def calculate_lifetime_value_scenario_b_cash(installed_cost, annual_savings,
                                             warranty_years, horizon=None,
                                             discount_rate=0.04):
    """
    Calculate lifetime value with proactive replacement at warranty end (cash).

    Returns:
        Tuple[np.ndarray, Optional[float]]: cumulative cash flow by year and
        optional NPV (defaults to 4%, pass None to disable).
    """
    return calculate_lifetime_value_cash(
        installed_cost,
        annual_savings,
        warranty_years,
        horizon,
        discount_rate=discount_rate,
    )


def calculate_lifetime_value_scenario_b_heloc(installed_cost, annual_savings,
                                              warranty_years, rate=None,
                                              loan_term=None, horizon=None,
                                              discount_rate=0.04):
    """
    Calculate lifetime value with proactive replacement at warranty end (HELOC).

    Returns:
        Tuple[np.ndarray, Optional[float]]: cumulative cash flow by year and
        optional NPV (defaults to 4%, pass None to disable).
    """
    return calculate_lifetime_value_heloc(
        installed_cost,
        annual_savings,
        warranty_years,
        rate,
        loan_term,
        horizon,
        discount_rate=discount_rate,
    )


def validate_scenario(result: Dict[str, Any], scenario_name: str):
    """
    Assert internal consistency of scenario results with enhanced unit and consistency checks.
    
    Args:
        result: Dictionary containing scenario results with keys like:
            - payback_years: Payback period in years
            - net_value: Net lifetime value
            - total_savings: Total savings over lifetime
            - upfront_cost: Initial cost
            - lifespan: Expected lifespan in years
            - annual_savings: Annual savings in dollars
            - rp_ratio: Replacement/Payback ratio
        scenario_name: Name of scenario for error messages
    
    Raises:
        AssertionError: If validation checks fail
    """
    # Payback period validation
    if 'payback_years' in result:
        payback = result['payback_years']
        # Allow payback >= 0 (0 represents immediate payback for zero-cost upgrades)
        assert payback >= 0 or payback == np.inf, \
            f"{scenario_name}: Invalid payback period: {payback}"
        
        # Check payback period is reasonable (warn if > 50 years)
        if payback != np.inf and payback > 50:
            import warnings
            warnings.warn(
                f"{scenario_name}: Payback period ({payback} years) exceeds 50 years - verify calculation",
                UserWarning
            )
    
    # Net value consistency check
    if 'net_value' in result and 'total_savings' in result and 'upfront_cost' in result:
        expected_net = result['total_savings'] - result['upfront_cost']
        assert abs(result['net_value'] - expected_net) < 1e-6, \
            f"{scenario_name}: net_value ({result['net_value']}) != total_savings ({result['total_savings']}) - upfront_cost ({result['upfront_cost']})"
    
    # Lifespan validation
    if 'lifespan' in result:
        lifespan = result['lifespan']
        assert lifespan > 0, \
            f"{scenario_name}: Invalid lifespan: {lifespan}"
        
        # Check lifespan is reasonable (5-30 years typical)
        if lifespan < 5 or lifespan > 30:
            import warnings
            warnings.warn(
                f"{scenario_name}: Lifespan ({lifespan} years) outside typical range (5-30 years)",
                UserWarning
            )
    
    # Annual savings validation
    if 'annual_savings' in result:
        annual_savings = result['annual_savings']
        assert annual_savings >= 0, \
            f"{scenario_name}: Negative annual savings: {annual_savings}"
        
        # Check annual savings is reasonable (warn if > $10,000/year)
        if annual_savings > 10000:
            import warnings
            warnings.warn(
                f"{scenario_name}: Annual savings ({annual_savings}) seems very high - verify calculation",
                UserWarning
            )
    
    # R/P ratio validation
    if 'rp_ratio' in result:
        rp_ratio = result['rp_ratio']
        assert rp_ratio >= 0, \
            f"{scenario_name}: Invalid R/P ratio (negative): {rp_ratio}"
        
        # R/P ratio should be finite (unless payback is infinite, then R/P = 0)
        if not np.isfinite(rp_ratio) and rp_ratio != 0:
            assert False, \
                f"{scenario_name}: Invalid R/P ratio (infinite): {rp_ratio}"
    
    # Cross-validation: If payback and lifespan present, verify R/P ratio
    if 'payback_years' in result and 'lifespan' in result and 'rp_ratio' in result:
        payback = result['payback_years']
        lifespan = result['lifespan']
        rp_ratio = result['rp_ratio']
        
        if payback != np.inf and payback > 0:
            expected_rp = lifespan / payback
            if abs(rp_ratio - expected_rp) > 1e-6:
                assert False, \
                    f"{scenario_name}: R/P ratio mismatch: {rp_ratio} != {lifespan} / {payback} = {expected_rp}"
    
    # Unit consistency: upfront_cost should be positive
    if 'upfront_cost' in result:
        upfront_cost = result['upfront_cost']
        assert upfront_cost > 0, \
            f"{scenario_name}: Invalid upfront_cost (non-positive): {upfront_cost}"
        
        # Check upfront cost is reasonable (warn if > $50,000)
        if upfront_cost > 50000:
            import warnings
            warnings.warn(
                f"{scenario_name}: Upfront cost (${upfront_cost}) seems very high - verify calculation",
                UserWarning
            )
    
    # Unit consistency: total_savings should be non-negative
    if 'total_savings' in result:
        total_savings = result['total_savings']
        assert total_savings >= 0, \
            f"{scenario_name}: Invalid total_savings (negative): {total_savings}"
    
    # Consistency: If annual_savings and payback present, verify payback calculation
    if 'annual_savings' in result and 'payback_years' in result and 'upfront_cost' in result:
        annual_savings = result['annual_savings']
        payback = result['payback_years']
        upfront_cost = result['upfront_cost']
        
        if annual_savings > 0 and payback != np.inf:
            expected_payback = upfront_cost / annual_savings
            if abs(payback - expected_payback) > 1e-6:
                import warnings
                warnings.warn(
                    f"{scenario_name}: Payback period mismatch: {payback} != {upfront_cost} / {annual_savings} = {expected_payback}",
                    UserWarning
                )


def load_reference_and_compare(current_outputs: Dict[str, Any], tolerance: float = 1e-6):
    """
    Compare current run against reference outputs from reference_outputs.json.
    
    Args:
        current_outputs: Dictionary of current outputs to compare
        tolerance: Tolerance for numeric comparisons (default 1e-6)
    
    Raises:
        AssertionError: If outputs don't match reference within tolerance
    """
    # Look for reference_outputs.json starting from repo root
    reference_candidates = [
        Path(__file__).parent.parent / 'reference_outputs.json',  # repository root
        Path(__file__).parent / 'reference_outputs.json',  # notebooks directory
        Path(__file__).parent.parent / 'data' / 'reference_outputs.json',  # data directory fallback
    ]

    reference_path = next((path for path in reference_candidates if path.exists()), None)
    if reference_path is None:
        search_list = ", ".join(str(path) for path in reference_candidates)
        print(f"Warning: Reference file not found in any of [{search_list}]. Skipping comparison.")
        return
    
    with open(reference_path, 'r') as f:
        reference = json.load(f)
    
    for key in reference:
        if key not in current_outputs:
            print(f"Warning: Key '{key}' in reference but not in current outputs")
            continue
        
        ref_val = reference[key]
        curr_val = current_outputs[key]
        
        if isinstance(ref_val, (int, float)) and isinstance(curr_val, (int, float)):
            if np.isinf(ref_val) and np.isinf(curr_val):
                continue  # Both infinite, match
            assert abs(curr_val - ref_val) < tolerance, \
                f"{key} changed: {ref_val} → {curr_val} (diff: {abs(curr_val - ref_val)})"
        elif isinstance(ref_val, dict) and isinstance(curr_val, dict):
            # Recursive comparison for nested dicts
            for subkey in ref_val:
                if subkey in curr_val:
                    ref_subval = ref_val[subkey]
                    curr_subval = curr_val[subkey]
                    if isinstance(ref_subval, (int, float)) and isinstance(curr_subval, (int, float)):
                        if not (np.isinf(ref_subval) and np.isinf(curr_subval)):
                            assert abs(curr_subval - ref_subval) < tolerance, \
                                f"{key}.{subkey} changed: {ref_subval} → {curr_subval}"
        elif isinstance(ref_val, list) and isinstance(curr_val, list):
            assert len(ref_val) == len(curr_val), \
                f"{key} list length changed: {len(ref_val)} → {len(curr_val)}"
            for i, (ref_item, curr_item) in enumerate(zip(ref_val, curr_val)):
                if isinstance(ref_item, (int, float)) and isinstance(curr_item, (int, float)):
                    if not (np.isinf(ref_item) and np.isinf(curr_item)):
                        assert abs(curr_item - ref_item) < tolerance, \
                            f"{key}[{i}] changed: {ref_item} → {curr_item}"

