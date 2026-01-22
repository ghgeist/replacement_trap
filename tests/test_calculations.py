"""
Pytest tests for basic calculation functions.

Sanity checks for core calculation logic to prevent regressions.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

from replacement_trap_utils import (
    calculate_payback_period,
    calculate_rp_ratio,
    calculate_lifetime_value_cash,
)


class TestPaybackPeriod:
    """Tests for payback period calculation"""
    
    def test_normal_case(self):
        """Normal case: cost=1000, savings=100 → 10 years"""
        payback = calculate_payback_period(installed_cost=1000, annual_savings=100)
        assert payback == 10.0, f"Expected 10.0, got {payback}"
    
    def test_zero_savings_returns_infinity(self):
        """Zero savings → infinity"""
        payback = calculate_payback_period(installed_cost=1000, annual_savings=0)
        assert np.isinf(payback), f"Expected infinity for zero savings, got {payback}"
    
    def test_negative_savings_returns_infinity(self):
        """Negative savings → infinity"""
        payback = calculate_payback_period(installed_cost=1000, annual_savings=-50)
        assert np.isinf(payback), f"Expected infinity for negative savings, got {payback}"
    
    def test_zero_cost_returns_zero(self):
        """Edge case: cost=0 → 0"""
        payback = calculate_payback_period(installed_cost=0, annual_savings=100)
        assert payback == 0.0, f"Expected 0.0 for zero cost, got {payback}"


class TestRPRatio:
    """Tests for R/P ratio calculation"""
    
    def test_normal_case(self):
        """Normal case: lifespan=10, payback=5 → 2.0"""
        rp_ratio = calculate_rp_ratio(lifespan=10, payback_period=5)
        assert rp_ratio == 2.0, f"Expected 2.0, got {rp_ratio}"
    
    def test_infinite_payback_returns_zero(self):
        """Infinite payback → 0"""
        rp_ratio = calculate_rp_ratio(lifespan=10, payback_period=np.inf)
        assert rp_ratio == 0, f"Expected 0 for infinite payback, got {rp_ratio}"
    
    def test_zero_payback_returns_zero(self):
        """Zero payback → 0"""
        rp_ratio = calculate_rp_ratio(lifespan=10, payback_period=0)
        assert rp_ratio == 0, f"Expected 0 for zero payback, got {rp_ratio}"
    
    def test_negative_payback_returns_zero(self):
        """Negative payback → 0"""
        rp_ratio = calculate_rp_ratio(lifespan=10, payback_period=-5)
        assert rp_ratio == 0, f"Expected 0 for negative payback, got {rp_ratio}"


class TestCashFlow:
    """Tests for basic cash flow calculation"""
    
    def test_initial_cost_at_year_zero(self):
        """Verify initial cost at year 0"""
        cash_flow, _ = calculate_lifetime_value_cash(
            installed_cost=1000,
            annual_savings=200,
            lifespan=10,
            horizon=5,
            degradation_rate=0.0
        )
        assert cash_flow[0] == -1000, f"Year 0 should be -1000, got {cash_flow[0]}"
    
    def test_replacement_occurs_at_lifespan(self):
        """Verify replacement occurs at lifespan"""
        cash_flow, _ = calculate_lifetime_value_cash(
            installed_cost=1000,
            annual_savings=200,
            lifespan=5,
            horizon=10,
            degradation_rate=0.0
        )
        
        # Year 5 should have replacement cost deducted
        # Year 4: -1000 + (200 * 4) = -200
        # Year 5: -200 + 200 - 1000 = -1000
        expected_year5 = -1000 + (200 * 5) - 1000
        np.testing.assert_almost_equal(
            cash_flow[5], expected_year5,
            err_msg=f"Year 5 should be {expected_year5} (with replacement), got {cash_flow[5]}"
        )
    
    def test_single_replacement_cycle(self):
        """Verify single replacement cycle accumulates correctly"""
        cash_flow, _ = calculate_lifetime_value_cash(
            installed_cost=1000,
            annual_savings=200,
            lifespan=5,
            horizon=5,
            degradation_rate=0.0
        )
        
        # Year 1: -1000 + 200 = -800
        expected_year1 = -1000 + 200
        np.testing.assert_almost_equal(
            cash_flow[1], expected_year1,
            err_msg=f"Year 1 should be {expected_year1}, got {cash_flow[1]}"
        )
        
        # Year 5: -1000 + (200 * 5) - 1000 = -1000
        expected_year5 = -1000 + (200 * 5) - 1000
        np.testing.assert_almost_equal(
            cash_flow[5], expected_year5,
            err_msg=f"Year 5 should be {expected_year5}, got {cash_flow[5]}"
        )

    def test_cash_npv_matches_manual_discount(self):
        """NPV should match manual discounted sum for constant savings"""
        discount_rate = 0.05
        horizon = 3
        _, npv = calculate_lifetime_value_cash(
            installed_cost=0,
            annual_savings=100,
            lifespan=50,
            horizon=horizon,
            degradation_rate=0.0,
            discount_rate=discount_rate,
        )
        expected_npv = sum(
            100 / ((1 + discount_rate) ** year)
            for year in range(1, horizon + 1)
        )
        np.testing.assert_allclose(
            npv, expected_npv, rtol=1e-6,
            err_msg="Discounted cash NPV should match manual calculation"
        )

