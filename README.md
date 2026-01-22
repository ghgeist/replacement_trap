# Replacement Trap Analysis

**Read the essay:** [The Replacement Trap: Why Most Home Systems Die Before They Pay for Themselves](https://substack.com/@grantgeist/p-179539887)

## Domain Context: Housing & Energy Lifecycle Economics

This analysis examines the **replacement trap**—a structural problem in residential infrastructure where systems die before they can repay their installed cost, creating structural loss rather than compounding returns. The model evaluates the full lifecycle economics of home systems, from installation through replacement cycles, under realistic financing constraints and energy price volatility.

**Problem Statement:** In many metro areas, most major systems in a typical home fail the same basic test: they die before they can pay for themselves. This analysis models household economics and residential infrastructure replacement cycles, revealing systems that never return what they take (e.g., most HVAC replacements under energy-only savings) versus those that escape the replacement treadmill.

**Key Finding:** Nine of eleven modeled scenarios never repay their cost within their lifespan. Each cycle loses roughly $500–$1,500, creating a steady drag of about $300–$700 a year that never appears as a clean line item. Systems where value cannot be monetized (comfort/health) remain trapped, while systems with monetizable value (labor savings) can escape the trap. Only two systems escape this pattern entirely: a whole-home LED retrofit and a hybrid heat-pump water heater—both clear the hurdle of short payback and long life, generating enough surplus to break out of the cycle instead of resetting it.

### Interpretation Boundary

This analysis evaluates systems only on monetizable household cash flows under conservative assumptions. It does not attempt to price externalities (carbon, health risk reduction, resilience, or code compliance). Systems that "fail" in this model may still be rational when non-cash benefits dominate—but those benefits must be large enough to justify structural loss.

The underlying mechanism is straightforward: the costs of installation and operation have been rising faster than the efficiency gains meant to offset them. Labor has become more expensive, and energy prices have trended upward over time. But the expected lifespans and performance improvements of major systems haven't kept pace. This creates a structural mismatch where efficiency gains are too small to cover the combined cost of the appliance, the labor to install it, and the energy needed to run it. By the time the system reaches the end of its life, it still hasn't earned back what it took to put it in place.

---

### Who This Is For

This repo is useful if you are:

- Evaluating residential retrofit economics or policy incentives
- Modeling lifecycle payback under uncertainty
- Designing decision tools for housing, climate, or infrastructure systems

## Analysis Overview

This analysis examines whether replacement cycles shorter than payback periods create structural loss for residential infrastructure investments. It evaluates 11 systems across 5 categories:

- **3 Dishwashers** (replacement context - incremental savings only)
- **3 Water Heaters** (energy savings only)
- **3 Air Conditioners** (energy savings only)
- **1 LED Lighting Retrofit** (whole-home LED retrofit)
- **1 Attic Insulation Upgrade** (blown-in cellulose insulation)

**Key Metrics:**
- **R/P Ratio**: Replacement/Payback ratio (lifespan ÷ payback period)
- **Lifetime Value**: 30-year cash flow with efficiency degradation
- **Comfort Gap**: Intangible value needed beyond energy savings
- **Monte Carlo**: Sensitivity to price/rate volatility

**Main Finding:** Nine of eleven modeled scenarios never repay their cost within their lifespan. Systems where value cannot be monetized (comfort/health) remain trapped below R/P = 0.8, while systems with monetizable value (labor savings) can escape the replacement treadmill. Only two systems escape this pattern entirely: a whole-home LED retrofit and a hybrid heat-pump water heater—both clear the hurdle of short payback and long life, generating enough surplus to break out of the cycle instead of resetting it.

The losses are small enough to disappear inside a single utility bill, but persistent enough to shape whether the household feels like it's finally getting ahead or constantly absorbing the next hit. For most households, the replacement trap shows up as a series of liquidity shocks—unplanned replacements that push families into credit cards, HELOC draws, and drained savings while still feeling like bad luck.

---

## Directory Structure

```
replacement_trap/
├── analysis/          # Analysis notebooks (run these)
│   ├── replacement_trap_core.ipynb
│   ├── replacement_trap_visualizations.ipynb
│   └── replacement_trap_monte_carlo.ipynb
├── data/              # Data files (input/output)
│   ├── systems-data.json              # System specifications and baselines
│   ├── replacement_trap_df.pkl         # Core analysis results (generated)
│   └── monte_carlo_results.pkl        # Monte Carlo results (generated)
├── lib/               # Python modules (shared code)
│   ├── replacement_trap_config.py     # Configuration and constants
│   ├── replacement_trap_utils.py       # Calculation functions
│   ├── replacement_trap_validation.py  # Validation functions
│   └── validate_reference_data.py     # Data validation
├── scripts/           # Utility scripts
│   └── generate_executive_summary.py  # Auto-generate summary data sections
├── tests/             # Test files
│   ├── test_calculations.py        # Tests for basic calculation functions
│   ├── test_heloc_cash_flow.py     # Tests for HELOC cash flow calculations
│   ├── test_validation_logic.py    # Tests for validation logic
│   └── test_validation.py          # Integration tests for validation
└── notes/             # Documentation and notes
    └── [markdown files]
```

## Quick Start

### 1. Run Core Analysis

Start with the core analysis notebook:

```bash
# Open in Jupyter
jupyter notebook analysis/replacement_trap_core.ipynb
```

This notebook:
- Loads system data from `data/systems-data.json`
- Calculates payback periods, R/P ratios, and lifetime values
- Performs comfort gap analysis
- Saves results to `data/replacement_trap_df.pkl`

**Output:** DataFrame `df` with all calculated metrics

### 2. Generate Visualizations (Optional)

```bash
jupyter notebook analysis/replacement_trap_visualizations.ipynb
```

Creates charts and plots from the core analysis results.

### 3. Run Monte Carlo Analysis (Optional)

```bash
jupyter notebook analysis/replacement_trap_monte_carlo.ipynb
```

Performs sensitivity analysis with price/rate volatility. Saves results to `data/monte_carlo_results.pkl`.

### 4. Generate Executive Summary Data

After running the core analysis (and optionally Monte Carlo), generate the summary:

```bash
python scripts/generate_executive_summary.py
```

This creates a date-stamped file in `notes/`:
- `notes/YYYY-MM-DD-executive-summary-data.md`

The generated file contains all data sections (1-7) with calculated statistics. Narrative sections marked `[MANUAL]` should be completed manually.

## Workflow

### Standard Analysis Workflow

1. **Update data** (if needed): Edit `data/systems-data.json`
2. **Run core analysis**: Execute `analysis/replacement_trap_core.ipynb`
3. **Run Monte Carlo** (optional): Execute `analysis/replacement_trap_monte_carlo.ipynb`
4. **Generate summary**: Run `python scripts/generate_executive_summary.py`
5. **Complete narrative**: Fill in `[MANUAL]` sections in generated summary

### Updating Analysis

When you update `systems-data.json`:
- The summary script will warn if data file is newer than pickle
- Re-run `replacement_trap_core.ipynb` to regenerate results
- Re-run summary script to get updated numbers

## Key Files

### Data Files

- **`data/systems-data.json`**: Source data for all systems (dishwashers, water heaters, AC, lighting, insulation)
  - Edit this file to add/modify systems or update parameters
- **`data/replacement_trap_df.pkl`**: Core analysis results DataFrame
  - Generated by `replacement_trap_core.ipynb`
  - Contains all calculated metrics (payback, R/P ratios, lifetime values, etc.)
- **`data/monte_carlo_results.pkl`**: Monte Carlo sensitivity results
  - Generated by `replacement_trap_monte_carlo.ipynb`
  - Contains percentage of negative scenarios per system

### Code Modules

- **`lib/replacement_trap_config.py`**: Central configuration
  - Electricity/water rates
  - HELOC parameters
  - Baseline system specifications
  - Monte Carlo ranges
- **`lib/replacement_trap_utils.py`**: Calculation functions
  - Payback period calculations
  - R/P ratio calculations
  - Lifetime value calculations (cash and HELOC)
  - Validation functions

### Notebooks

- **`analysis/replacement_trap_core.ipynb`**: Main analysis
  - Must run first to generate DataFrame
  - Calculates all core metrics
- **`analysis/replacement_trap_visualizations.ipynb`**: Charts and plots
  - Requires core analysis to be run first
- **`analysis/replacement_trap_monte_carlo.ipynb`**: Sensitivity analysis
  - Requires core analysis to be run first
  - Tests price/rate volatility impacts

## Executive Summary Generation

The `scripts/generate_executive_summary.py` script automatically extracts data from analysis results and generates markdown sections:

**Generated Sections:**
1. R/P clustering statistics
2. Threshold analysis (trapped vs surplus)
3. HELOC financing amplification
4. Lifespan variance sensitivity
5. Comfort gap calculations
6. Monte Carlo volatility results
7. Income burden (requires manual completion)

**Output Format:**
- Date-stamped filename: `YYYY-MM-DD-executive-summary-data.md`
- Contains all calculated statistics
- Narrative sections marked `[MANUAL]` for completion
- Can be merged with existing executive summary document

## Path Detection

All notebooks use robust path detection to find the project root directory, allowing them to work regardless of:
- Current working directory
- Whether running from `analysis/` or project root
- Jupyter vs. script execution context

The path detection looks for `lib/replacement_trap_config.py` to identify the project root.

## Dependencies

- Python 3.8+
- pandas
- numpy
- matplotlib (for visualizations)
- seaborn (for visualizations)

All imports are handled automatically via the `lib/` directory structure.

## Testing

### Running Tests

Run all tests from the project root:

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_heloc_cash_flow.py

# Run a specific test
pytest tests/test_heloc_cash_flow.py::test_heloc_replacement_year_cash_neutral_after_loan_term
```

### Test Files

- **`test_calculations.py`**: Tests for basic calculation functions (payback periods, R/P ratios)
- **`test_heloc_cash_flow.py`**: Tests for HELOC cash flow calculations, including edge cases for replacement timing and loan term interactions
- **`test_validation_logic.py`**: Tests for validation logic functions
- **`test_validation.py`**: Integration tests for the full validation workflow

### Adding Tests for Bug Fixes

**Important:** When a bug is discovered (especially during PR review), add a test case to prevent regression:

1. **Create a failing test** that reproduces the bug
2. **Fix the bug** so the test passes
3. **Keep the test** as a regression guard

Example: The HELOC cash flow bug where replacement after loan term ended incorrectly added loan draw was caught and fixed with `test_heloc_replacement_year_cash_neutral_after_loan_term`.

<details>
<summary>Test Conventions and Coverage</summary>

**Test Naming Convention:**
- Use descriptive names that explain what behavior is being tested
- Include edge case scenarios in test names (e.g., `test_heloc_replacement_year_cash_neutral_after_loan_term`)
- Group related tests in the same file

**Test Coverage:**
- Focus on critical calculation logic (cash flows, payback periods, R/P ratios)
- Test edge cases (replacement timing, loan term boundaries, multiple replacements)
- Test validation logic to ensure data integrity

</details>

## Notes

- **Pickle files**: Generated by notebooks, can be deleted and regenerated
- **Cache**: Python `__pycache__` directories are ignored (can be deleted)
- **Reference outputs**: Optional `reference_outputs.json` file for regression testing (if present)

## Troubleshooting

### Import Errors

If you see import errors:
1. Make sure you're running notebooks from the correct directory
2. Check that `lib/replacement_trap_config.py` exists
3. The path detection should handle most cases automatically

### Missing Data Files

If pickle files are missing:
- Run `replacement_trap_core.ipynb` to generate `replacement_trap_df.pkl`
- Run `replacement_trap_monte_carlo.ipynb` to generate `monte_carlo_results.pkl`

### Summary Generation Errors

If summary script fails:
- Ensure core analysis has been run (check for `data/replacement_trap_df.pkl`)
- Monte Carlo results are optional (Section 6 will be skipped if missing)
- Check that `notes/` directory exists

