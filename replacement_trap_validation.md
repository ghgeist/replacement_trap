# Replacement Trap Validation Notes

Working notes for automated and manual validation of the Replacement Trap analysis. Companion checklist: [validation_checklist.md](validation_checklist.md).

## 1. Purpose

Validators in `lib/replacement_trap_validation.py` and `lib/validate_reference_data.py` catch unit mistakes, formula regressions, and internal inconsistencies. This document records modeling scope decisions that automated tests do not vary.

## 2. How to Run

```bash
pytest tests/ -v
python tests/test_validation.py
```

`tests/test_validation.py` writes `tests/validation_report.md` (UTF-8). That report is generated and gitignored.

## 3. Reference Outputs

Golden metrics live in `data/reference_outputs.json`, built by `build_reference_outputs()` in `lib/replacement_trap_pipeline.py`. The core notebook and regenerate script compare the **full** payload (not a subset) via `load_reference_and_compare`. Refresh with `python scripts/regenerate_core_outputs.py` after intentional metric changes; `tests/test_pipeline_parity.py` locks the committed pickle/CSV/reference trio.

## 4. Scope Limitations

### 4.1 Monetizable Cash Flows Only

The model prices energy and water cash flows. It does not monetize carbon, health, resilience, code compliance, or comfort beyond the derived comfort-gap residual.

### 4.2 Replacement Timing

- **Scenario A:** emergency / failure-timed replacement at expected lifespan
- **Scenario B:** proactive replacement at warranty expiration

Scenario A is the published baseline. Scenario B is a stress case that shortens effective life and typically worsens R/P.

### 4.3 Fixed Analysis Parameters

These parameters are fixed (not swept in Monte Carlo) as an intentional scope limit:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `TIME_HORIZON` | 30 years | Standard residential planning horizon; price volatility is covered by Monte Carlo multipliers |
| `EFFICIENCY_DEGRADATION_RATE` | 1.5%/year | Midpoint of documented ~1–3% ACEEE-style range; conservative middle assumption |
| `DISHWASHER_CYCLES_PER_YEAR` | 215 | DOE standard usage assumption |

If these become first-class sensitivity axes, update Monte Carlo inputs and regenerate reference outputs.

## 5. HELOC Modeling Notes

HELOC cash flows assume interest-only payments during the loan term, with replacement-year debt roll-forward while the facility is open. Unit tests in `tests/test_heloc_cash_flow.py` encode the intended cash-neutrality invariants.
