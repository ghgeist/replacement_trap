"""
Reference data validator for systems-data.json.

Checks that input data is internally consistent and within expected ranges.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from replacement_trap_config import (
    SYSTEMS_DATA_PATH,
    ELECTRICITY_RATE,
    WATER_RATE,
)


class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


class DataValidationResult:
    """Container for data validation results"""
    def __init__(self):
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
        result = f"Data Validation: {status}\n"
        if self.errors:
            result += f"  Errors ({len(self.errors)}):\n"
            for err in self.errors:
                result += f"    - {err}\n"
        if self.warnings:
            result += f"  Warnings ({len(self.warnings)}):\n"
            for warn in self.warnings:
                result += f"    - {warn}\n"
        return result


def validate_systems_data() -> DataValidationResult:
    """
    Validate systems-data.json structure and values.
    
    Checks:
    - All required fields present for each system
    - Numeric values are positive (where expected)
    - Lifespans are reasonable (5-30 years typical)
    - Costs are positive
    - Energy/water values match expected ranges
    - Baseline parameters match config values
    """
    result = DataValidationResult()
    
    # Load JSON file
    if not SYSTEMS_DATA_PATH.exists():
        result.add_error(f"systems-data.json not found at {SYSTEMS_DATA_PATH}")
        return result
    
    try:
        with open(SYSTEMS_DATA_PATH, 'r') as f:
            systems_json = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON in systems-data.json: {e}")
        return result
    except Exception as e:
        result.add_error(f"Failed to load systems-data.json: {e}")
        return result
    
    # Validate metadata structure
    if 'metadata' not in systems_json:
        result.add_error("Missing 'metadata' section in systems-data.json")
        return result
    
    metadata = systems_json['metadata']
    
    # Validate baseline parameters
    if 'baseline_parameters' not in metadata:
        result.add_error("Missing 'baseline_parameters' in metadata")
    else:
        baseline_params = metadata['baseline_parameters']
        
        # Check electricity rate
        if 'electricity_rate' not in baseline_params:
            result.add_error("Missing 'electricity_rate' in baseline_parameters")
        else:
            elec_rate = baseline_params['electricity_rate']
            if 'value' not in elec_rate:
                result.add_error("Missing 'value' in electricity_rate")
            else:
                elec_value = elec_rate['value']
                if not isinstance(elec_value, (int, float)) or elec_value <= 0:
                    result.add_error(f"Invalid electricity_rate value: {elec_value}")
                else:
                    # Check if value seems high
                    if elec_value > 1.0:
                        result.add_warning(f"Electricity rate seems high: ${elec_value}/kWh")
                    # Compare against config value (regardless of whether it's high)
                    if abs(elec_value - ELECTRICITY_RATE) > 1e-6:
                        result.add_error(
                            f"Electricity rate mismatch: JSON={elec_value}, config={ELECTRICITY_RATE}"
                        )
        
        # Check water rate
        if 'water_rate' not in baseline_params:
            result.add_error("Missing 'water_rate' in baseline_parameters")
        else:
            water_rate = baseline_params['water_rate']
            if 'value' not in water_rate:
                result.add_error("Missing 'value' in water_rate")
            else:
                water_value = water_rate['value']
                if not isinstance(water_value, (int, float)) or water_value <= 0:
                    result.add_error(f"Invalid water_rate value: {water_value}")
                else:
                    # Check if value seems high
                    if water_value > 0.1:
                        result.add_warning(f"Water rate seems high: ${water_value}/gal")
                    # Compare against config value (regardless of whether it's high)
                    if abs(water_value - WATER_RATE) > 1e-6:
                        result.add_error(
                            f"Water rate mismatch: JSON={water_value}, config={WATER_RATE}"
                        )
    
    # Validate appliance baselines
    if 'appliance_baselines' not in systems_json:
        result.add_error("Missing 'appliance_baselines' section")
    else:
        baselines = systems_json['appliance_baselines']
        if not isinstance(baselines, list):
            result.add_error("appliance_baselines must be a list")
        else:
            required_baseline_fields = ['category', 'expected_lifespan_years', 'annual_kWh_point']
            
            for i, baseline in enumerate(baselines):
                if not isinstance(baseline, dict):
                    result.add_error(f"Baseline {i} is not a dictionary")
                    continue
                
                category = baseline.get('category', f'Baseline {i}')
                
                # Check required fields
                for field in required_baseline_fields:
                    if field not in baseline:
                        result.add_error(f"{category}: Missing required field '{field}'")
                
                # Validate lifespan
                if 'expected_lifespan_years' in baseline:
                    lifespan = baseline['expected_lifespan_years']
                    if not isinstance(lifespan, (int, float)) or lifespan <= 0:
                        result.add_error(f"{category}: Invalid lifespan: {lifespan}")
                    elif lifespan < 5 or lifespan > 30:
                        result.add_warning(f"{category}: Lifespan ({lifespan} years) outside typical range (5-30 years)")
                
                # Validate energy consumption
                if 'annual_kWh_point' in baseline:
                    kwh = baseline['annual_kWh_point']
                    if not isinstance(kwh, (int, float)) or kwh <= 0:
                        result.add_error(f"{category}: Invalid annual_kWh_point: {kwh}")
                    elif kwh > 10000:
                        result.add_warning(f"{category}: Annual kWh ({kwh}) seems very high")
                
                # Validate installed cost if present
                if 'installed_cost_2025_usd_point' in baseline:
                    cost = baseline['installed_cost_2025_usd_point']
                    if not isinstance(cost, (int, float)) or cost <= 0:
                        result.add_error(f"{category}: Invalid installed_cost_2025_usd_point: {cost}")
    
    # Validate appliance categories
    if 'appliance_categories' not in systems_json:
        result.add_error("Missing 'appliance_categories' section")
    else:
        categories = systems_json['appliance_categories']
        if not isinstance(categories, dict):
            result.add_error("appliance_categories must be a dictionary")
        else:
            for category_name, category_data in categories.items():
                if not isinstance(category_data, dict):
                    result.add_error(f"Category '{category_name}' is not a dictionary")
                    continue
                
                # Check for Models list
                if 'Models' not in category_data:
                    result.add_warning(f"Category '{category_name}' has no 'Models' list")
                    continue
                
                models = category_data['Models']
                if not isinstance(models, list):
                    result.add_error(f"Category '{category_name}': 'Models' must be a list")
                    continue
                
                # Validate each model
                required_model_fields = ['Model', 'installed_cost_usd', 'expected_lifespan_years']
                
                for j, model in enumerate(models):
                    if not isinstance(model, dict):
                        result.add_error(f"Category '{category_name}', Model {j}: Not a dictionary")
                        continue
                    
                    model_name = model.get('Model', f'Model {j}')
                    
                    # Check required fields
                    for field in required_model_fields:
                        if field not in model:
                            result.add_error(f"{category_name}/{model_name}: Missing required field '{field}'")
                    
                    # Validate lifespan
                    if 'expected_lifespan_years' in model:
                        lifespan = model['expected_lifespan_years']
                        if not isinstance(lifespan, (int, float)) or lifespan <= 0:
                            result.add_error(f"{category_name}/{model_name}: Invalid lifespan: {lifespan}")
                        elif lifespan < 5 or lifespan > 30:
                            result.add_warning(
                                f"{category_name}/{model_name}: Lifespan ({lifespan} years) "
                                f"outside typical range (5-30 years)"
                            )
                    
                    # Validate installed cost
                    if 'installed_cost_usd' in model:
                        cost = model['installed_cost_usd']
                        if not isinstance(cost, (int, float)) or cost <= 0:
                            result.add_error(f"{category_name}/{model_name}: Invalid installed_cost_usd: {cost}")
                        elif cost > 50000:
                            result.add_warning(f"{category_name}/{model_name}: Cost (${cost}) seems very high")
                    
                    # Validate energy consumption (if present)
                    if 'annual_kWh' in model:
                        kwh = model['annual_kWh']
                        if not isinstance(kwh, (int, float)) or kwh <= 0:
                            result.add_error(f"{category_name}/{model_name}: Invalid annual_kWh: {kwh}")
                        elif kwh > 10000:
                            result.add_warning(f"{category_name}/{model_name}: Annual kWh ({kwh}) seems very high")
                    
                    # Validate water consumption for dishwashers
                    if 'water_gal_per_cycle' in model:
                        gal = model['water_gal_per_cycle']
                        if not isinstance(gal, (int, float)) or gal <= 0:
                            result.add_error(f"{category_name}/{model_name}: Invalid water_gal_per_cycle: {gal}")
                        elif gal > 20:
                            result.add_warning(f"{category_name}/{model_name}: Water per cycle ({gal} gal) seems high")
                    
                    # Validate SEER for AC units
                    if 'seer' in model:
                        seer = model['seer']
                        if not isinstance(seer, (int, float)) or seer <= 0:
                            result.add_error(f"{category_name}/{model_name}: Invalid seer: {seer}")
                        elif seer < 10 or seer > 30:
                            result.add_warning(f"{category_name}/{model_name}: SEER ({seer}) outside typical range (10-30)")
                    
                    # Validate UEF for water heaters
                    if 'uef' in model or 'uef_equivalent' in model:
                        uef_key = 'uef' if 'uef' in model else 'uef_equivalent'
                        uef = model[uef_key]
                        if not isinstance(uef, (int, float)) or uef <= 0:
                            result.add_error(f"{category_name}/{model_name}: Invalid {uef_key}: {uef}")
                        elif uef > 1.0:
                            result.add_warning(f"{category_name}/{model_name}: UEF ({uef}) > 1.0 (unusual)")
    
    return result


def print_data_validation_report(result: DataValidationResult):
    """Print a formatted data validation report"""
    print("=" * 70)
    print("SYSTEMS DATA VALIDATION REPORT")
    print("=" * 70)
    print()
    print(result)
    print("=" * 70)
    
    return result.passed


if __name__ == "__main__":
    result = validate_systems_data()
    print_data_validation_report(result)

