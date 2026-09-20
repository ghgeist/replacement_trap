# Validation Checklist

Manual verification items for the Replacement Trap analysis. Run automated validators (`python tests/test_validation.py` and `pytest`) regularly; review this checklist quarterly or before major assumption updates.

## Source Authority

- [ ] Electricity and water rates match cited utility / EIA sources for the modeled geography
- [ ] Baseline consumption figures cite ENERGY STAR, DOE, or manufacturer datasheets
- [ ] Installed costs reflect installed (not MSRP-only) residential quotes where claimed
- [ ] Warranty years and lifespan assumptions match manufacturer documentation

## Real-World Range Validation (Monte Carlo)

- [ ] Electricity multiplier bounds remain defensible against historical rate paths
- [ ] Water multiplier floor (no decrease) still matches local rate behavior
- [ ] HELOC rate range matches current consumer credit conditions
- [ ] Category lifespan variance bands match industry / material guidance

## Scenario Modeling

- [ ] Scenario A (replace at expected lifespan) remains the essay / executive-summary baseline
- [ ] Scenario B (replace at warranty end) uses `warranty_years` from `data/systems-data.json`
- [ ] HELOC terms (interest-only period, rate) match documented assumptions
- [ ] Efficiency degradation rate is still within the documented ACEEE-style range

## Sensitivity and Threshold Robustness

- [ ] Structural-loss threshold (R/P < 0.8) and surplus threshold (R/P > 1.0) still match narrative claims
- [ ] ±20% lifespan sensitivity does not silently invert headline findings without explanation
- [ ] Comfort-gap calculation still applies only to environmental utilities as documented

## Outputs

- [ ] Re-run `analysis/replacement_trap_core.ipynb` after changing `data/systems-data.json`
- [ ] Refresh `data/reference_outputs.json` after intentional metric changes
- [ ] Confirm `scripts/generate_executive_summary.py` still reads required Scenario A columns
