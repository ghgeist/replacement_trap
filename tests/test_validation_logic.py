"""
Pytest tests for validation logic.

Prevents false errors in validation, especially the water multiplier validation fix.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

from replacement_trap_validation import validate_internal_consistency, ValidationResult
from replacement_trap_config import WATER_RATE, WATER_MULTIPLIER_MIN, WATER_MULTIPLIER_MAX


def test_water_multiplier_min_equals_one_no_error():
    """
    Test that WATER_MULTIPLIER_MIN=1.0 does not error (only warns).
    
    This test prevents the false error we fixed. When WATER_MULTIPLIER_MIN=1.0,
    min_water == baseline_water is expected and should not cause an error.
    """
    # Mock WATER_MULTIPLIER_MIN to 1.0 (which is already the case, but being explicit)
    with patch('replacement_trap_validation.WATER_MULTIPLIER_MIN', 1.0):
        result = validate_internal_consistency()
        
        # Should pass (no errors)
        assert result.passed, f"Validation should pass when WATER_MULTIPLIER_MIN=1.0, but got errors: {result.errors}"
        
        # Should have warning about no decrease
        warning_found = any('WATER_MULTIPLIER_MIN' in warn and '>= 1.0' in warn for warn in result.warnings)
        assert warning_found, f"Should warn about WATER_MULTIPLIER_MIN >= 1.0, warnings: {result.warnings}"
        
        # Should NOT have error about min_water >= baseline_water
        error_found = any('min water' in err.lower() and '>= baseline' in err.lower() for err in result.errors)
        assert not error_found, f"Should NOT error when min_water == baseline_water with multiplier=1.0, errors: {result.errors}"


def test_water_multiplier_min_greater_than_one_errors():
    """
    Test that min_water > baseline_water still errors correctly.
    
    When WATER_MULTIPLIER_MIN > 1.0, min_water > baseline_water should error.
    """
    with patch('replacement_trap_validation.WATER_MULTIPLIER_MIN', 1.5):
        result = validate_internal_consistency()
        
        # Should fail (has errors)
        assert not result.passed, f"Validation should fail when WATER_MULTIPLIER_MIN > 1.0"
        
        # Should have error about min_water > baseline
        error_found = any('min water' in err.lower() and '> baseline' in err.lower() for err in result.errors)
        assert error_found, f"Should error when min_water > baseline_water, errors: {result.errors}"


def test_electricity_multiplier_consistency():
    """
    Verify electricity validation follows same pattern (warns when min >= 1.0, doesn't error).
    
    This ensures consistency between electricity and water validation logic.
    """
    # Mock ELECTRICITY_MULTIPLIER_MIN to 1.0 to test the warning path
    with patch('replacement_trap_validation.ELECTRICITY_MULTIPLIER_MIN', 1.0):
        result = validate_internal_consistency()
        
        # Should not error about min_electricity >= baseline
        error_found = any('min electricity' in err.lower() and '>= baseline' in err.lower() for err in result.errors)
        assert not error_found, (
            f"Should NOT error when min_electricity == baseline_electricity with multiplier >= 1.0, "
            f"errors: {result.errors}"
        )


def test_water_multiplier_min_less_than_one_allows_decrease():
    """
    Test that WATER_MULTIPLIER_MIN < 1.0 allows decrease (min < baseline).
    
    This is a sanity check to ensure the validation logic works correctly
    when decreases are allowed.
    """
    with patch('replacement_trap_validation.WATER_MULTIPLIER_MIN', 0.8):
        result = validate_internal_consistency()
        
        # Should not error about min_water >= baseline (since min < baseline)
        error_found = any('min water' in err.lower() and '>= baseline' in err.lower() for err in result.errors)
        assert not error_found, (
            f"Should NOT error when WATER_MULTIPLIER_MIN < 1.0 (allows decrease), "
            f"errors: {result.errors}"
        )

