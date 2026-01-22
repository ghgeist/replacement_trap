"""
Configuration module for replacement trap analysis.

Centralizes all constants, rates, and baseline parameters.
"""

import json
from pathlib import Path

# Load systems data
SYSTEMS_DATA_PATH = Path(__file__).parent.parent / 'data' / 'systems-data.json'

with open(SYSTEMS_DATA_PATH, 'r') as f:
    systems_json = json.load(f)

# Extract rates and constants from JSON
ELECTRICITY_RATE = systems_json['metadata']['baseline_parameters']['electricity_rate']['value']
WATER_RATE = systems_json['metadata']['baseline_parameters']['water_rate']['value']

# Dishwasher parameters
DISHWASHER_CYCLES_PER_YEAR = 215  # DOE standard (2003 update)

# Labor cost parameters for dishwashers
HAND_WASHING_MINUTES_PER_DAY = 30  # Conservative estimate
HAND_WASHING_HOURS_PER_YEAR = (HAND_WASHING_MINUTES_PER_DAY / 60) * 365  # 182.5 hours/year
HOURLY_LABOR_RATE = 15.0  # $/hour
DISHWASHER_ANNUAL_LABOR_SAVINGS = HAND_WASHING_HOURS_PER_YEAR * HOURLY_LABOR_RATE  # $2,737.50/year

# Extract baselines
BASELINES = {item['category']: item for item in systems_json['appliance_baselines']}

# HELOC parameters
HELOC_RATE = 0.085  # 8.5% annual interest rate (Nov 2025 market rate)
HELOC_LOAN_TERM = 10  # years (interest-only period)

# Analysis parameters
# NOTE: These parameters are fixed (not varied in sensitivity analysis) as a scope limitation.
# Rationale:
# - TIME_HORIZON (30 years): Standard for residential analysis; Monte Carlo covers main price volatility uncertainties
# - EFFICIENCY_DEGRADATION_RATE (1.5%): Middle of documented range (1-3% per ACEEE); conservative assumption
# - DISHWASHER_CYCLES_PER_YEAR (215): DOE standard; covers typical usage patterns
# These fixed values are documented as scope limitations in replacement_trap_validation.md Section 4.3
TIME_HORIZON = 30  # years
EFFICIENCY_DEGRADATION_RATE = 0.015  # 1.5% per year

# Monte Carlo parameters
MONTE_CARLO_SCENARIOS = 1000
MONTE_CARLO_SEED = 42  # For reproducibility

# Price volatility ranges for Monte Carlo
# Lower bound (0.5x = 50% decrease): Represents aggressive renewable deployment + modest demand
# reduction. Historical precedent exists (Utah/Nebraska ~2% annual declines). Even with dramatic
# renewable scaling, fixed costs (transmission, distribution, maintenance) represent 40-60% of
# residential bills and don't compress away - these costs typically grow with inflation.
ELECTRICITY_MULTIPLIER_MIN = 0.5  # 50% decrease (more defensible than 0.2x)
ELECTRICITY_MULTIPLIER_MAX = 3.0  # 3x increase
WATER_MULTIPLIER_MIN = 1.0  # No decrease
WATER_MULTIPLIER_MAX = 10.0  # 10x increase
HELOC_RATE_MIN = 0.06  # 6%
HELOC_RATE_MAX = 0.12  # 12%

# Lifespan variance by category for Monte Carlo
# Variance represents ±percentage around baseline lifespan
# Based on industry data and material properties:
# - Appliances: ±20% (mechanical systems with typical variation)
# - Lighting: ±15% (solid-state LEDs, predictable but system-level variation)
# - Insulation: ±10% (passive material, installation quality dependent)
LIFESPAN_VARIANCE_BY_CATEGORY = {
    'Dishwasher': 0.20,
    'Water Heater': 0.20,
    'Air Conditioner': 0.20,
    'Lighting': 0.15,
    'Attic Insulation': 0.10
}

