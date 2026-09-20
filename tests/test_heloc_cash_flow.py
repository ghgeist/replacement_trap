"""
Pytest tests for HELOC cash flow calculations.

Focuses on regression prevention for the replacement year cash-neutrality bug fix.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

from replacement_trap_utils import calculate_lifetime_value_heloc


@pytest.fixture
def standard_params():
    """Common test parameters"""
    return {
        'cost': 1000,
        'savings': 200,
        'rate': 0.085,
        'loan_term': 10,
        'degradation': 0.0
    }


def test_heloc_year_zero_no_cash_outlay(standard_params):
    """Verify year 0 = 0 (no cash outlay, loan taken at year 0)"""
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=standard_params['cost'],
        annual_savings=standard_params['savings'],
        lifespan=20,  # No replacement in first year
        rate=standard_params['rate'],
        loan_term=standard_params['loan_term'],
        horizon=5,
        degradation_rate=standard_params['degradation']
    )
    assert cash_flow[0] == 0, f"Year 0 should be 0, got {cash_flow[0]}"


def test_heloc_first_year_interest_payment(standard_params):
    """Verify year 1 = savings - interest"""
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=standard_params['cost'],
        annual_savings=standard_params['savings'],
        lifespan=20,  # No replacement in first year
        rate=standard_params['rate'],
        loan_term=standard_params['loan_term'],
        horizon=5,
        degradation_rate=standard_params['degradation']
    )
    expected_year1 = standard_params['savings'] - (standard_params['cost'] * standard_params['rate'])
    np.testing.assert_almost_equal(
        cash_flow[1], expected_year1,
        err_msg=f"Year 1 should be {expected_year1} (savings - interest), got {cash_flow[1]}"
    )


def test_heloc_replacement_year_cash_neutral_during_loan_term(standard_params):
    """
    Verify replacement year net cash flow = savings - interest only.
    
    This test catches the double-counting bug we fixed. The replacement year
    should be cash-neutral apart from interest: principal payoff (-) is offset
    by new loan draw (+).
    """
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=standard_params['cost'],
        annual_savings=standard_params['savings'],
        lifespan=5,  # Replacement at year 5
        rate=standard_params['rate'],
        loan_term=standard_params['loan_term'],
        horizon=10,
        degradation_rate=standard_params['degradation']
    )
    
    year5_change = cash_flow[5] - cash_flow[4]
    # Replacement year: savings - interest only (principal offset by new draw)
    expected_change = standard_params['savings'] - (standard_params['cost'] * standard_params['rate'])
    # NOT: savings - cost - interest = -885 (old buggy behavior)
    
    np.testing.assert_almost_equal(
        year5_change, expected_change,
        err_msg=f"Year 5 change should be {expected_change} (savings - interest), got {year5_change}. "
                f"This catches the double-counting bug."
    )


def test_heloc_replacement_year_cash_neutral_after_loan_term(standard_params):
    """
    Verify replacement year cash-neutrality when replacement occurs after loan term ends.
    
    After loan term, no interest is paid, so replacement year should be savings only
    (principal payoff offset by new loan draw).
    """
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=standard_params['cost'],
        annual_savings=standard_params['savings'],
        lifespan=15,  # Replacement at year 15 (after loan term ends at year 10)
        rate=standard_params['rate'],
        loan_term=standard_params['loan_term'],
        horizon=20,
        degradation_rate=standard_params['degradation']
    )
    
    year15_change = cash_flow[15] - cash_flow[14]
    # After loan term: savings only (no interest, principal offset by new draw)
    expected_change = standard_params['savings']
    
    np.testing.assert_almost_equal(
        year15_change, expected_change,
        err_msg=f"Year 15 change should be {expected_change} (savings only), got {year15_change}"
    )


def test_heloc_replacement_exactly_at_loan_term_end(standard_params):
    """
    Edge case: replacement occurs exactly when loan term ends.
    
    Verify no double principal payment and correct cash-neutral behavior.
    """
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=standard_params['cost'],
        annual_savings=standard_params['savings'],
        lifespan=10,  # Replacement at year 10 (exactly when loan term ends)
        rate=standard_params['rate'],
        loan_term=standard_params['loan_term'],
        horizon=15,
        degradation_rate=standard_params['degradation']
    )
    
    year10_change = cash_flow[10] - cash_flow[9]
    # Replacement at loan term end: savings - interest (principal offset by new draw)
    # Interest is still paid in year 10 because replacement happens during the year
    expected_change = standard_params['savings'] - (standard_params['cost'] * standard_params['rate'])
    
    np.testing.assert_almost_equal(
        year10_change, expected_change,
        err_msg=f"Year 10 change should be {expected_change} (savings - interest), got {year10_change}"
    )


def test_heloc_multiple_replacements_debt_roll_forward(standard_params):
    """
    Verify debt rolls forward correctly across multiple replacement cycles.
    
    Each replacement year should follow the cash-neutral pattern.
    """
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=standard_params['cost'],
        annual_savings=standard_params['savings'],
        lifespan=3,  # Replacements at years 3, 6, 9
        rate=standard_params['rate'],
        loan_term=standard_params['loan_term'],
        horizon=10,
        degradation_rate=standard_params['degradation']
    )
    
    # Check replacement years (3, 6, 9)
    replacement_years = [3, 6, 9]
    expected_replacement_change = standard_params['savings'] - (standard_params['cost'] * standard_params['rate'])
    
    for year in replacement_years:
        year_change = cash_flow[year] - cash_flow[year - 1]
        np.testing.assert_almost_equal(
            year_change, expected_replacement_change,
            err_msg=f"Year {year} change should be {expected_replacement_change} (cash-neutral + interest), "
                    f"got {year_change}"
        )
    
    # Check non-replacement years accumulate correctly
    # Year 2 should be: savings - interest (no replacement)
    year2_change = cash_flow[2] - cash_flow[1]
    expected_year2_change = standard_params['savings'] - (standard_params['cost'] * standard_params['rate'])
    np.testing.assert_almost_equal(
        year2_change, expected_year2_change,
        err_msg=f"Year 2 change should be {expected_year2_change}, got {year2_change}"
    )


def test_heloc_npv_matches_manual_discount():
    """NPV should match manual discounted sum when interest and replacements are absent"""
    discount_rate = 0.05
    horizon = 3
    annual_savings = 150
    installed_cost = 2000
    _, npv = calculate_lifetime_value_heloc(
        installed_cost=installed_cost,
        annual_savings=annual_savings,
        lifespan=40,
        rate=0.0,          # Remove interest so cash flow equals savings until terminal payoff
        loan_term=30,
        horizon=horizon,
        degradation_rate=0.0,
        discount_rate=discount_rate,
    )
    expected_npv = sum(
        annual_savings / ((1 + discount_rate) ** year)
        for year in range(1, horizon)
    )
    expected_npv += (annual_savings - installed_cost) / ((1 + discount_rate) ** horizon)
    np.testing.assert_allclose(
        npv, expected_npv, rtol=1e-6,
        err_msg="HELOC NPV should match manual discounted cash flow including terminal principal"
    )


def test_heloc_settles_remaining_principal_at_horizon(standard_params):
    """Unpaid principal at the horizon is a terminal cash outflow."""
    cost = standard_params['cost']
    savings = standard_params['savings']
    rate = standard_params['rate']
    horizon = 6
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=cost,
        annual_savings=savings,
        lifespan=20,  # No replacement during the horizon
        rate=rate,
        loan_term=10,
        horizon=horizon,
        degradation_rate=0.0,
    )
    # Years 1-5: savings - interest only. Year 6 also settles remaining principal.
    expected_before_terminal = 5 * (savings - cost * rate)
    expected_year6 = expected_before_terminal + (savings - cost * rate) - cost
    np.testing.assert_almost_equal(cash_flow[5], expected_before_terminal)
    np.testing.assert_almost_equal(
        cash_flow[horizon],
        expected_year6,
        err_msg="Horizon cash flow should subtract remaining HELOC principal",
    )


def test_heloc_does_not_double_charge_when_term_ends_before_horizon(standard_params):
    """If principal is paid when the draw period ends, do not settle it again."""
    cost = standard_params['cost']
    savings = standard_params['savings']
    cash_flow, _ = calculate_lifetime_value_heloc(
        installed_cost=cost,
        annual_savings=savings,
        lifespan=40,
        rate=0.0,
        loan_term=3,
        horizon=5,
        degradation_rate=0.0,
    )
    # Year 3 pays principal at term end; years 4-5 are savings only.
    np.testing.assert_almost_equal(cash_flow[3], savings * 3 - cost)
    np.testing.assert_almost_equal(cash_flow[5], savings * 5 - cost)
