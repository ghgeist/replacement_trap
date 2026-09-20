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
    calculate_lifetime_value_heloc,
    calculate_scenario_b_rp,
    calculate_lifetime_value_scenario_b_cash,
    calculate_lifetime_value_scenario_b_heloc,
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


class TestScenarioB:
    """Tests for proactive warranty-replacement (Scenario B) helpers"""

    def test_scenario_b_rp_uses_warranty_years(self):
        """Scenario B R/P uses warranty years, not expected lifespan"""
        rp_ratio = calculate_scenario_b_rp(
            expected_lifespan=15,
            warranty_years=10,
            payback_period=5,
        )
        assert rp_ratio == 2.0, f"Expected 2.0, got {rp_ratio}"

    def test_scenario_b_rp_worse_than_or_equal_to_scenario_a(self):
        """When warranty <= lifespan, Scenario B R/P is not better than A"""
        lifespan = 15
        warranty = 10
        payback = 5
        rp_a = calculate_rp_ratio(lifespan, payback)
        rp_b = calculate_scenario_b_rp(lifespan, warranty, payback)
        assert rp_b <= rp_a

    def test_scenario_b_cash_matches_lifespan_as_warranty(self):
        """Scenario B cash flow matches cash helper with lifespan=warranty"""
        kwargs = dict(
            installed_cost=1000,
            annual_savings=200,
            warranty_years=5,
            horizon=12,
            degradation_rate=0.015,
            discount_rate=0.04,
        )
        flow_b, npv_b = calculate_lifetime_value_scenario_b_cash(**kwargs)
        flow_a, npv_a = calculate_lifetime_value_cash(
            installed_cost=kwargs['installed_cost'],
            annual_savings=kwargs['annual_savings'],
            lifespan=kwargs['warranty_years'],
            horizon=kwargs['horizon'],
            degradation_rate=kwargs['degradation_rate'],
            discount_rate=kwargs['discount_rate'],
        )
        np.testing.assert_allclose(flow_b, flow_a)
        np.testing.assert_allclose(npv_b, npv_a)

    def test_scenario_b_heloc_matches_lifespan_as_warranty(self):
        """Scenario B HELOC flow matches HELOC helper with lifespan=warranty"""
        kwargs = dict(
            installed_cost=1000,
            annual_savings=200,
            warranty_years=5,
            rate=0.085,
            loan_term=10,
            horizon=12,
            degradation_rate=0.015,
            discount_rate=0.04,
        )
        flow_b, npv_b = calculate_lifetime_value_scenario_b_heloc(**kwargs)
        flow_a, npv_a = calculate_lifetime_value_heloc(
            installed_cost=kwargs['installed_cost'],
            annual_savings=kwargs['annual_savings'],
            lifespan=kwargs['warranty_years'],
            rate=kwargs['rate'],
            loan_term=kwargs['loan_term'],
            horizon=kwargs['horizon'],
            degradation_rate=kwargs['degradation_rate'],
            discount_rate=kwargs['discount_rate'],
        )
        np.testing.assert_allclose(flow_b, flow_a)
        np.testing.assert_allclose(npv_b, npv_a)

