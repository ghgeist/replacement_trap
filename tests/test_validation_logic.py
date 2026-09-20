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

from replacement_trap_validation import validate_internal_consistency
from validate_reference_data import validate_systems_data
from replacement_trap_utils import load_reference_and_compare


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


def test_systems_data_requires_warranty_years():
    """Real systems-data.json must include warranty_years on every model."""
    result = validate_systems_data()
    warranty_errors = [e for e in result.errors if 'warranty_years' in e]
    assert not warranty_errors, f"Unexpected warranty errors: {warranty_errors}"
    assert result.passed or not any('Missing required field' in e for e in result.errors)


def test_missing_warranty_years_errors(tmp_path, monkeypatch):
    """Missing warranty_years on a model is a validation error."""
    import json
    from pathlib import Path
    import validate_reference_data as vrd

    systems = json.loads(Path(vrd.SYSTEMS_DATA_PATH).read_text(encoding='utf-8'))
    model = systems['appliance_categories']['Category 1: Dishwashers']['Models'][0]
    model.pop('warranty_years', None)

    bad_path = tmp_path / 'systems-data.json'
    bad_path.write_text(json.dumps(systems), encoding='utf-8')
    monkeypatch.setattr(vrd, 'SYSTEMS_DATA_PATH', bad_path)

    result = vrd.validate_systems_data()
    assert not result.passed
    assert any('Missing required field \'warranty_years\'' in e for e in result.errors)


def test_warranty_longer_than_lifespan_errors(tmp_path, monkeypatch):
    """warranty_years > expected_lifespan_years is a validation error."""
    import json
    from pathlib import Path
    import validate_reference_data as vrd

    systems = json.loads(Path(vrd.SYSTEMS_DATA_PATH).read_text(encoding='utf-8'))
    model = systems['appliance_categories']['Category 1: Dishwashers']['Models'][0]
    model['warranty_years'] = model['expected_lifespan_years'] + 5

    bad_path = tmp_path / 'systems-data.json'
    bad_path.write_text(json.dumps(systems), encoding='utf-8')
    monkeypatch.setattr(vrd, 'SYSTEMS_DATA_PATH', bad_path)

    result = vrd.validate_systems_data()
    assert not result.passed
    assert any('exceeds expected_lifespan_years' in e for e in result.errors)


def test_load_reference_raises_when_file_missing(tmp_path):
    """Missing golden file is an error, not a silent skip."""
    missing = tmp_path / 'does-not-exist.json'
    with pytest.raises(FileNotFoundError, match='Reference file not found'):
        load_reference_and_compare({'rp_ratio_mean': 1.0}, reference_path=missing)


def test_load_reference_raises_when_top_level_key_missing(tmp_path):
    """A golden key absent from current outputs must fail the comparison."""
    import json

    ref_path = tmp_path / 'reference_outputs.json'
    ref_path.write_text(json.dumps({'rp_ratio_mean': 1.0, 'surplus_generator_count': 2}), encoding='utf-8')
    with pytest.raises(AssertionError, match="Key 'surplus_generator_count'"):
        load_reference_and_compare({'rp_ratio_mean': 1.0}, reference_path=ref_path)


def test_load_reference_raises_when_nested_key_missing(tmp_path):
    """A nested golden key absent from current outputs must fail the comparison."""
    import json

    ref_path = tmp_path / 'reference_outputs.json'
    ref_path.write_text(
        json.dumps({'payback_periods': {'0': 10.0, '1': 20.0}}),
        encoding='utf-8',
    )
    with pytest.raises(AssertionError, match=r'payback_periods\.1 in reference'):
        load_reference_and_compare(
            {'payback_periods': {0: 10.0}},
            reference_path=ref_path,
        )


def test_load_reference_accepts_stringified_nested_keys(tmp_path):
    """JSON string keys match in-memory integer keys after normalization."""
    import json

    ref_path = tmp_path / 'reference_outputs.json'
    ref_path.write_text(json.dumps({'payback_periods': {'0': 10.0}}), encoding='utf-8')
    load_reference_and_compare({'payback_periods': {0: 10.0}}, reference_path=ref_path)
