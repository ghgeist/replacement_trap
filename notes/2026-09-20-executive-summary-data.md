---
generated_date: 2026-09-20
generated_timestamp: 2026-09-20 17:42:45 UTC
source_data: data/replacement_trap_df.pkl
source_mc_data: data/monte_carlo_results.pkl
---

## Auto-Generated Executive Summary Data Sections

**Generated:** 2026-09-20 17:42:45 UTC  
**Source:** Analysis results from `analysis/replacement_trap_core.ipynb`  
**Data:** `data/systems-data.json`

**Note:** This file contains auto-generated data sections. Narrative sections marked "[MANUAL]" should be completed manually.

---

### 1. Do systems cluster below R/P = 0.8?

Yes—strong clustering below 0.8 confirms structural loss pattern.

- Mean R/P: 1.30
- Median R/P: 0.27
- Distribution: 9 of 11 systems (82%) below 0.8; 2 systems (18%) above 1.0 (Rheem ProTerra 50-gal Hybrid Heat Pump (Water Heater), Whole-home LED retrofit (~40 bulbs) (Lighting))
- Range: 0.06 to 8.93

**Finding:** [MANUAL: Your interpretation here]

---
### 2. Is there a visible threshold between surplus generators and structural loss?

Clear threshold at R/P = 0.8 separates loss from surplus, consistent across categories.

- **Structural loss (R/P < 0.8, 9 systems):** All show negative 30-year cash flow
  - Payback periods: 23–218 years (includes 1.5%/year efficiency degradation)
  - Annual savings: $23–$238/year (energy/water only, declining 1.5%/year)
  - Negative lifetime values: Average $-10,719 (cash)
- **Surplus generators (R/P > 1.0, 2 systems):** Both show positive 30-year cash flow
  - Payback periods: 1.5–4.8 years
  - Annual savings: $206–$523/year
  - Positive lifetime values: Average $5,947 (cash)

**Finding:** [MANUAL: Your interpretation here]

---
### 3. How much does HELOC financing amplify the problem?

HELOC amplifies losses by 0.13–1.25x (avg 0.69x) for trapped systems.

- **Trapped systems (9 of 11):** All negative with cash; HELOC worsens 7/9
  - Financing penalty: $-20,400–$495 over 30 years (interest-only for 10 years; remaining principal settled at horizon)
  - Amplification factor: Up to 1.25x (makes losses deeper)
- **Surplus generators (2 of 11):** Both positive with cash; HELOC reduces surplus but remains positive
  - Penalty: Rheem ProTerra 50-gal Hybrid Heat Pump: $-5,525; Whole-home LED retrofit (~40 bulbs): $-612

**Finding:** [MANUAL: Your interpretation here]

---
### 4. How does ±20% lifespan variance affect threshold predictions?

Variance can shift marginal systems across thresholds, but trap remains robust.

- Systems crossing R/P = 0.8 within ±20%: 0/11 (0%)
- Systems crossing R/P = 1.0 within ±20%: 0/11
- Near-threshold systems: None

**Finding:** [MANUAL: Your interpretation here]

---
### 5. What is the "comfort gap" for environmental utilities?

Comfort gap: $-315–$705/year avg ($-0.036–$0.081/hour) in intangible value needed beyond energy savings.

**Calculation:**
- Breakeven savings = Cost ÷ Lifespan
- Gap = Breakeven - Actual savings

**Findings:**
- Gaps: $-315 to $705/year
- Correlation with R/P: -0.764 (high gaps → low R/P)
- Example: Goodman GSX14 3-Ton Split System needs $705/year ($0.08/hour) in comfort value to break even

**Interpretation:** Energy savings alone insufficient—gap filled by non-monetizable benefits (comfort/health) that cannot compound.

**Finding:** [MANUAL: Your interpretation here]

---
### 6. How vulnerable are systems to price and rate volatility? (Monte Carlo Analysis)

High vulnerability: Avg 79.8% scenarios negative (6/11 systems at 100%).

**Ranges:** Elec 0.5–3x, Water 1–10x, HELOC 6–12%
- Trapped systems: 6/11 systems with 100% negative scenarios
- Surplus: 1/11 systems with 0% negative (resilient)

**Finding:** [MANUAL: Your interpretation here]

---
### 7. What is the income burden of comfort premium? (Income Sensitivity)

[Income burden calculations require income quintile data not currently in DataFrame. 
This section needs manual completion or additional analysis with Census income data.]

**Finding:** [MANUAL: Your interpretation here]

---
