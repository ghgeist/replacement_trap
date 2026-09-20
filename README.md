# Replacement Trap Analysis

Residential systems often fail a simple economic test: they wear out before they repay what it cost to install them. This repo analyzes that replacement cycle across common home systems using lifecycle cash-flow modeling, financing assumptions, and sensitivity analysis.

**Read the essay:** [The Replacement Trap: Why Most Home Systems Die Before They Pay for Themselves](https://substack.com/@grantgeist/p-179539887)

## What This Repo Does

This project models whether residential upgrades create compounding household value or reset into recurring structural loss. It evaluates 11 scenarios across five categories:

- Dishwashers
- Water heaters
- Air conditioners
- Whole-home LED lighting
- Attic insulation

The analysis centers on four outputs:

- **R/P ratio**: lifespan divided by payback period
- **Lifetime value**: multi-year cash flow under degradation and replacement cycles
- **Comfort gap**: non-cash value needed to justify a system that does not repay on energy savings alone
- **Monte Carlo sensitivity**: exposure to rate and price volatility

## Main Finding

Nine of the 11 modeled scenarios do not repay their installed cost within their lifespan under conservative, monetizable household cash-flow assumptions. In this framework, most replacements create a recurring drag rather than a durable return. The strongest exceptions are the whole-home LED retrofit and the hybrid heat-pump water heater, both of which clear the threshold of short payback and long enough life to generate surplus.

## Interpretation Boundary

This repo intentionally evaluates **monetizable household cash flows**, not the full social or moral case for replacing a system. It does **not** price externalities such as:

- Carbon reduction
- Health risk reduction
- Resilience
- Code compliance
- Comfort beyond what can be monetized

That means a system can fail this model and still be a rational household choice. It just means the non-cash benefits have to be large enough to justify the structural loss.

## Who This Is For

This repo is useful if you are:

- Evaluating residential retrofit economics
- Studying replacement cycles under uncertainty
- Building policy, climate, or housing decision tools
- Writing about the economics of home infrastructure

## Quick Start

### 1. Create an environment

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you are using macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the core analysis

```bash
jupyter notebook analysis/replacement_trap_core.ipynb
```

This notebook:

- Loads `data/systems-data.json`
- Calculates payback, R/P ratios, lifetime value, and comfort gap metrics
- Writes the core output to `data/replacement_trap_df.pkl`

### 3. Run optional follow-on notebooks

Visualizations:

```bash
jupyter notebook analysis/replacement_trap_visualizations.ipynb
```

Monte Carlo sensitivity analysis:

```bash
jupyter notebook analysis/replacement_trap_monte_carlo.ipynb
```

The Monte Carlo notebook writes `data/monte_carlo_results.pkl`.

### 4. Generate executive summary data

```bash
python scripts/generate_executive_summary.py
```

This creates a date-stamped markdown file in `notes/` with the computed sections needed for an executive summary. Narrative sections marked `[MANUAL]` are meant to be completed by hand.

## Typical Workflow

1. Update assumptions in `data/systems-data.json`
2. Run `analysis/replacement_trap_core.ipynb`
3. Run `analysis/replacement_trap_monte_carlo.ipynb` if you want volatility analysis
4. Run `python scripts/generate_executive_summary.py`
5. Review the generated markdown in `notes/`

If you change `data/systems-data.json`, re-run the core notebook before trusting any downstream outputs.

## Project Layout

```text
replacement_trap/
├── analysis/
│   ├── replacement_trap_core.ipynb
│   ├── replacement_trap_visualizations.ipynb
│   └── replacement_trap_monte_carlo.ipynb
├── data/
│   ├── systems-data.json
│   ├── replacement_trap_df.pkl
│   ├── monte_carlo_results.pkl
│   ├── replacement_trap_df.csv
│   ├── monte_carlo_results.csv
│   └── reference_outputs.json
├── lib/
│   ├── replacement_trap_pipeline.py
│   ├── replacement_trap_config.py
│   ├── replacement_trap_utils.py
│   ├── replacement_trap_validation.py
│   └── validate_reference_data.py
├── scripts/
│   ├── generate_executive_summary.py
│   └── convert_pkl_to_csv.py
├── tests/
│   ├── test_calculations.py
│   ├── test_heloc_cash_flow.py
│   ├── test_validation_logic.py
│   └── test_validation.py
├── validation_checklist.md
├── replacement_trap_validation.md
└── notes/
```

## Key Files

### Data

- `data/systems-data.json`: source assumptions for all modeled systems
- `data/replacement_trap_df.pkl`: core analysis output used by downstream scripts and notebooks (includes Scenario A and Scenario B metrics)
- `data/monte_carlo_results.pkl`: Monte Carlo output
- `data/reference_outputs.json`: golden headline metrics for regression comparison
- `data/*.csv`: exported tabular outputs for easier inspection and sharing

### Notebooks

- `analysis/replacement_trap_core.ipynb`: main analysis notebook, run this first (Scenario A = replace at expected lifespan; Scenario B = replace at warranty end)
- `analysis/replacement_trap_visualizations.ipynb`: charts and visual outputs
- `analysis/replacement_trap_monte_carlo.ipynb`: volatility and sensitivity analysis

### Validation Docs

- `validation_checklist.md`: manual review checklist for sources, ranges, and thresholds
- `replacement_trap_validation.md`: validation notes and fixed-parameter scope (Section 4.3)

### Python Modules

- `lib/replacement_trap_pipeline.py`: shared builder for the core analysis DataFrame and golden reference outputs
- `lib/replacement_trap_config.py`: configuration, baseline assumptions, and ranges
- `lib/replacement_trap_utils.py`: core calculation logic
- `lib/replacement_trap_validation.py`: validation helpers
- `lib/validate_reference_data.py`: reference data checks

### Scripts

- `scripts/generate_executive_summary.py`: generates the data-heavy sections for an executive summary
- `scripts/convert_pkl_to_csv.py`: exports notebook outputs to CSV
- `scripts/regenerate_core_outputs.py`: thin CLI that calls the shared pipeline to rebuild the core DataFrame, CSV, and `data/reference_outputs.json` without launching Jupyter

## Testing

Run the test suite from the project root:

```bash
pytest tests/ -v
```

You can also run a focused test:

```bash
pytest tests/test_heloc_cash_flow.py
pytest tests/test_heloc_cash_flow.py::test_heloc_replacement_year_cash_neutral_after_loan_term
```

Testing is concentrated around critical calculation paths:

- Payback and R/P logic
- HELOC cash-flow behavior
- Validation rules and integration behavior

When fixing a bug, add a regression test that fails before the fix and passes after it.

## Dependencies

This repo currently expects:

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn
- pytest
- jupyter
- ipykernel

Install them with `pip install -r requirements.txt`.

## Troubleshooting

### Import errors in notebooks

- Make sure the virtual environment is activated
- Launch Jupyter from the project root
- Confirm that `lib/replacement_trap_config.py` exists and has not been moved

### Missing output files

- Run `analysis/replacement_trap_core.ipynb` to generate `data/replacement_trap_df.pkl`
- Run `analysis/replacement_trap_monte_carlo.ipynb` to generate `data/monte_carlo_results.pkl`

### Executive summary script fails

- Confirm the core notebook has already been run
- Monte Carlo output is optional; that section can be skipped if the file is missing
- Check that `notes/` exists and is writable

## Notes

- Generated `.pkl` outputs can be deleted and regenerated
- CSV outputs are convenience exports, not the canonical intermediate artifacts
- Notebook path detection is designed to work from either the project root or the `analysis/` directory

