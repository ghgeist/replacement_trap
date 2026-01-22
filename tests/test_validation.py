"""
Integration test runner for replacement trap validation.

Runs all validators and generates a comprehensive validation report.
"""

import sys
import warnings
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

# Suppress deprecation warning from dateutil library
warnings.filterwarnings("ignore", category=DeprecationWarning, module="dateutil")

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent / 'lib'
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

from replacement_trap_validation import (
    run_all_validations,
    print_validation_report,
    ValidationResult,
)
from validate_reference_data import (
    validate_systems_data,
    print_data_validation_report,
    DataValidationResult,
)


def generate_markdown_report(
    validation_results: List[ValidationResult],
    data_result: DataValidationResult,
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a markdown validation report.
    
    Args:
        validation_results: List of ValidationResult objects from code validation
        data_result: DataValidationResult from systems-data.json validation
        output_path: Optional path to save report (if None, returns string only)
    
    Returns:
        Markdown report as string
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Replacement Trap Validation Report

**Generated:** {timestamp}

## Summary

"""
    
    # Overall status
    all_code_passed = all(r.passed for r in validation_results)
    data_passed = data_result.passed
    overall_passed = all_code_passed and data_passed
    
    if overall_passed:
        report += "✅ **ALL VALIDATIONS PASSED**\n\n"
    else:
        report += "❌ **SOME VALIDATIONS FAILED**\n\n"
    
    # Code validation results
    report += "## Code Validation Results\n\n"
    
    for result in validation_results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        report += f"### {result.name}: {status}\n\n"
        
        if result.errors:
            report += f"**Errors ({len(result.errors)}):**\n\n"
            for err in result.errors:
                report += f"- ❌ {err}\n"
            report += "\n"
        
        if result.warnings:
            report += f"**Warnings ({len(result.warnings)}):**\n\n"
            for warn in result.warnings:
                report += f"- ⚠️ {warn}\n"
            report += "\n"
        
        if result.passed and not result.errors and not result.warnings:
            report += "No issues found.\n\n"
    
    # Data validation results
    report += "## Data Validation Results\n\n"
    
    status = "✅ PASS" if data_result.passed else "❌ FAIL"
    report += f"### Systems Data Validation: {status}\n\n"
    
    if data_result.errors:
        report += f"**Errors ({len(data_result.errors)}):**\n\n"
        for err in data_result.errors:
            report += f"- ❌ {err}\n"
        report += "\n"
    
    if data_result.warnings:
        report += f"**Warnings ({len(data_result.warnings)}):**\n\n"
        for warn in data_result.warnings:
            report += f"- ⚠️ {warn}\n"
        report += "\n"
    
    if data_result.passed and not data_result.errors and not data_result.warnings:
        report += "No issues found.\n\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    
    has_errors = any(r.errors for r in validation_results) or data_result.errors
    has_warnings = any(r.warnings for r in validation_results) or data_result.warnings
    
    if has_errors:
        report += "### Critical Issues (Must Fix)\n\n"
        report += "The following errors must be addressed before using the analysis:\n\n"
        
        for result in validation_results:
            if result.errors:
                report += f"- **{result.name}:** {len(result.errors)} error(s)\n"
        
        if data_result.errors:
            report += f"- **Systems Data:** {len(data_result.errors)} error(s)\n"
        
        report += "\n"
    
    if has_warnings:
        report += "### Warnings (Review Recommended)\n\n"
        report += "The following warnings should be reviewed:\n\n"
        
        for result in validation_results:
            if result.warnings:
                report += f"- **{result.name}:** {len(result.warnings)} warning(s)\n"
        
        if data_result.warnings:
            report += f"- **Systems Data:** {len(data_result.warnings)} warning(s)\n"
        
        report += "\n"
    
    if not has_errors and not has_warnings:
        report += "✅ No issues found. All validations passed.\n\n"
    
    # Human judgment items
    report += """## Human Judgment Items

The following items require manual verification (see `validation_checklist.md`):

- [ ] Source authority (EIA, ENERGY STAR, manufacturer specs)
- [ ] Real-world range validation (Monte Carlo inputs)
- [ ] Scenario modeling validation (HELOC terms, degradation rates)
- [ ] Sensitivity analysis validation (threshold robustness)

Run automated validators regularly; review checklist quarterly or before major updates.

"""
    
    # Footer
    report += f"""---

*Report generated by test_validation.py*
*For detailed validation checklist, see validation_checklist.md*
"""
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {output_path}")
    
    return report


def main():
    """Run all validations and generate report"""
    print("Running replacement trap validation...")
    print("=" * 70)
    print()
    
    # Run code validations
    print("1. Running code validations...")
    validation_results = run_all_validations()
    print()
    
    # Run data validation
    print("2. Running data validation...")
    data_result = validate_systems_data()
    print()
    
    # Print console reports
    print("=" * 70)
    print("CONSOLE VALIDATION REPORT")
    print("=" * 70)
    print()
    
    all_code_passed = print_validation_report(validation_results)
    print()
    
    data_passed = print_data_validation_report(data_result)
    print()
    
    # Generate markdown report
    report_path = Path(__file__).parent / 'validation_report.md'
    markdown_report = generate_markdown_report(validation_results, data_result, report_path)
    
    # Overall status
    overall_passed = all_code_passed and data_passed
    
    print("=" * 70)
    if overall_passed:
        print("✅ OVERALL STATUS: ALL VALIDATIONS PASSED")
    else:
        print("❌ OVERALL STATUS: SOME VALIDATIONS FAILED")
        failed_code = sum(1 for r in validation_results if not r.passed)
        print(f"   Failed code validators: {failed_code}/{len(validation_results)}")
        if not data_passed:
            print("   Data validation: FAILED")
    print("=" * 70)
    
    # Exit code
    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()

