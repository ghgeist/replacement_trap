#!/usr/bin/env python3
"""
Generate executive summary data sections from analysis results.

This script extracts calculated statistics from the analysis DataFrame and
Monte Carlo results, generating markdown sections 1-7 with current data.
Narrative sections ("Finding:" paragraphs) are left blank for manual completion.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add lib directory to path for imports
script_dir = Path(__file__).parent
notebooks_root = script_dir.parent
lib_dir = notebooks_root / 'lib'

if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

from replacement_trap_config import SYSTEMS_DATA_PATH


def determine_notebooks_root():
    """Determine notebooks root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def load_data():
    """Load DataFrame and Monte Carlo results."""
    notebooks_root = determine_notebooks_root()
    data_dir = notebooks_root / 'data'
    
    # Load core DataFrame
    df_path = data_dir / 'replacement_trap_df.pkl'
    if not df_path.exists():
        raise FileNotFoundError(
            f"DataFrame not found at {df_path}. "
            "Please run analysis/replacement_trap_core.ipynb first."
        )
    
    df = pd.read_pickle(df_path)
    print(f"✓ Loaded DataFrame from {df_path}")
    print(f"  Shape: {df.shape}")
    
    # Check for required columns
    required_columns = [
        'rp_ratio_scenario_a',
        'payback_period',
        'lifetime_value_cash_scenario_a',
        'lifetime_value_heloc_scenario_a',
        'financing_penalty_usd',
        'amplification_factor'
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(
            f"DataFrame is missing required columns: {', '.join(missing_columns)}\n"
            f"Current columns: {', '.join(df.columns.tolist())}\n"
            f"Please re-run analysis/replacement_trap_core.ipynb to regenerate the DataFrame with all calculated metrics."
        )
    
    # Check if systems-data.json is newer than pickle (warn user)
    systems_data_path = data_dir / 'systems-data.json'
    if systems_data_path.exists():
        systems_mtime = systems_data_path.stat().st_mtime
        df_mtime = df_path.stat().st_mtime
        if systems_mtime > df_mtime:
            print(f"⚠ Warning: {systems_data_path.name} is newer than DataFrame.")
            print("  Consider re-running analysis/replacement_trap_core.ipynb to update results.")
    
    # Load Monte Carlo results (optional)
    mc_path = data_dir / 'monte_carlo_results.pkl'
    mc_results = None
    if mc_path.exists():
        mc_results = pd.read_pickle(mc_path)
        print(f"✓ Loaded Monte Carlo results from {mc_path}")
        print(f"  Shape: {mc_results.shape}")
    else:
        print(f"⚠ Monte Carlo results not found at {mc_path}")
        print("  Section 6 will be skipped. Run analysis/replacement_trap_monte_carlo.ipynb to generate.")
    
    return df, mc_results


def generate_section_1_rp_clustering(df):
    """Generate Section 1: R/P clustering statistics."""
    rp_mean = df['rp_ratio_scenario_a'].mean()
    rp_median = df['rp_ratio_scenario_a'].median()
    rp_min = df['rp_ratio_scenario_a'].min()
    rp_max = df['rp_ratio_scenario_a'].max()
    
    below_08 = (df['rp_ratio_scenario_a'] < 0.8).sum()
    above_10 = (df['rp_ratio_scenario_a'] > 1.0).sum()
    total = len(df)
    
    # Find systems above 1.0
    surplus_systems = df[df['rp_ratio_scenario_a'] > 1.0][['model', 'category']].values.tolist()
    surplus_names = [f"{row[0]} ({row[1]})" for row in surplus_systems]
    
    md = f"""### 1. Do systems cluster below R/P = 0.8?

Yes—strong clustering below 0.8 confirms structural loss pattern.

- Mean R/P: {rp_mean:.2f}
- Median R/P: {rp_median:.2f}
- Distribution: {below_08} of {total} systems ({below_08/total*100:.0f}%) below 0.8; {above_10} systems ({above_10/total*100:.0f}%) above 1.0 ({', '.join(surplus_names) if surplus_names else 'none'})
- Range: {rp_min:.2f} to {rp_max:.2f}

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_section_2_threshold_analysis(df):
    """Generate Section 2: Threshold analysis."""
    trapped = df[df['rp_ratio_scenario_a'] < 0.8].copy()
    surplus = df[df['rp_ratio_scenario_a'] > 1.0].copy()
    
    if len(trapped) > 0:
        trapped_payback = trapped[trapped['payback_period'] != np.inf]['payback_period']
        trapped_payback_min = trapped_payback.min() if len(trapped_payback) > 0 else np.inf
        trapped_payback_max = trapped_payback.max() if len(trapped_payback) > 0 else np.inf
        trapped_savings_min = trapped['annual_savings'].min()
        trapped_savings_max = trapped['annual_savings'].max()
        trapped_lifetime_mean = trapped['lifetime_value_cash_scenario_a'].mean()
    else:
        trapped_payback_min = trapped_payback_max = np.inf
        trapped_savings_min = trapped_savings_max = 0
        trapped_lifetime_mean = 0
    
    if len(surplus) > 0:
        surplus_payback = surplus[surplus['payback_period'] != np.inf]['payback_period']
        surplus_payback_min = surplus_payback.min() if len(surplus_payback) > 0 else np.inf
        surplus_payback_max = surplus_payback.max() if len(surplus_payback) > 0 else np.inf
        surplus_savings_min = surplus['annual_savings'].min()
        surplus_savings_max = surplus['annual_savings'].max()
        surplus_lifetime_mean = surplus['lifetime_value_cash_scenario_a'].mean()
    else:
        surplus_payback_min = surplus_payback_max = np.inf
        surplus_savings_min = surplus_savings_max = 0
        surplus_lifetime_mean = 0
    
    md = f"""### 2. Is there a visible threshold between surplus generators and structural loss?

Clear threshold at R/P = 0.8 separates loss from surplus, consistent across categories.

- **Structural loss (R/P < 0.8, {len(trapped)} systems):** All show negative 30-year cash flow
  - Payback periods: {trapped_payback_min:.0f}–{trapped_payback_max:.0f} years (includes 1.5%/year efficiency degradation)
  - Annual savings: ${trapped_savings_min:.0f}–${trapped_savings_max:.0f}/year (energy/water only, declining 1.5%/year)
  - Negative lifetime values: Average ${trapped_lifetime_mean:,.0f} (cash)
- **Surplus generators (R/P > 1.0, {len(surplus)} systems):** Both show positive 30-year cash flow
  - Payback periods: {surplus_payback_min:.1f}–{surplus_payback_max:.1f} years
  - Annual savings: ${surplus_savings_min:.0f}–${surplus_savings_max:.0f}/year
  - Positive lifetime values: Average ${surplus_lifetime_mean:,.0f} (cash)

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_section_3_financing(df):
    """Generate Section 3: HELOC financing amplification."""
    trapped = df[df['rp_ratio_scenario_a'] < 0.8].copy()
    surplus = df[df['rp_ratio_scenario_a'] > 1.0].copy()
    
    if len(trapped) > 0:
        trapped_penalty = trapped['financing_penalty_usd']
        trapped_penalty_min = trapped_penalty.min()
        trapped_penalty_max = trapped_penalty.max()
        trapped_amp = trapped['amplification_factor'].dropna()
        trapped_amp_min = trapped_amp.min() if len(trapped_amp) > 0 else 0
        trapped_amp_max = trapped_amp.max() if len(trapped_amp) > 0 else 0
        trapped_amp_mean = trapped_amp.mean() if len(trapped_amp) > 0 else 0
        
        # Count how many trapped systems worsen with HELOC
        trapped_worse = ((trapped['lifetime_value_heloc_scenario_a'] < trapped['lifetime_value_cash_scenario_a'])).sum()
    else:
        trapped_penalty_min = trapped_penalty_max = 0
        trapped_amp_min = trapped_amp_max = trapped_amp_mean = 0
        trapped_worse = 0
    
    if len(surplus) > 0:
        surplus_penalty = surplus['financing_penalty_usd']
        surplus_penalty_max = surplus_penalty.max() if len(surplus_penalty) > 0 else 0
    else:
        surplus_penalty_max = 0
    
    md = f"""### 3. How much does HELOC financing amplify the problem?

HELOC amplifies losses by {trapped_amp_min:.2f}–{trapped_amp_max:.2f}x (avg {trapped_amp_mean:.2f}x) for trapped systems.

- **Trapped systems ({len(trapped)} of {len(df)}):** All negative with cash; HELOC worsens {trapped_worse}/{len(trapped)}
  - Financing penalty: ${trapped_penalty_min:,.0f}–${trapped_penalty_max:,.0f} over 30 years (interest-only for 10 years)
  - Amplification factor: Up to {trapped_amp_max:.2f}x (makes losses deeper)
- **Surplus generators ({len(surplus)} of {len(df)}):** Both positive with cash; HELOC reduces surplus but remains positive
  - Penalty: ${surplus_penalty_max:,.0f} (heat pump remains positive)

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_section_4_variance(df):
    """Generate Section 4: Lifespan variance sensitivity."""
    # Check if variance columns exist
    if 'rp_ratio_low' not in df.columns or 'rp_ratio_high' not in df.columns:
        return """### 4. How does ±20% lifespan variance affect threshold predictions?

[Variance analysis columns not found in DataFrame. This section requires additional analysis.]

**Finding:** [MANUAL: Your interpretation here]

---
"""
    
    # Systems crossing R/P = 0.8 threshold
    crossing_08 = ((df['rp_ratio_low'] < 0.8) & (df['rp_ratio_high'] >= 0.8)).sum()
    crossing_10 = ((df['rp_ratio_low'] < 1.0) & (df['rp_ratio_high'] >= 1.0)).sum()
    
    # Find near-threshold systems
    near_threshold = df[
        ((df['rp_ratio_low'] < 0.8) & (df['rp_ratio_high'] >= 0.8)) |
        ((df['rp_ratio_low'] < 1.0) & (df['rp_ratio_high'] >= 1.0))
    ][['model', 'rp_ratio_low', 'rp_ratio_high']].copy()
    
    near_threshold_list = []
    for _, row in near_threshold.iterrows():
        near_threshold_list.append(f"{row['model']} [{row['rp_ratio_low']:.2f}, {row['rp_ratio_high']:.2f}]")
    
    md = f"""### 4. How does ±20% lifespan variance affect threshold predictions?

Variance can shift marginal systems across thresholds, but trap remains robust.

- Systems crossing R/P = 0.8 within ±20%: {crossing_08}/{len(df)} ({crossing_08/len(df)*100:.0f}%)
- Systems crossing R/P = 1.0 within ±20%: {crossing_10}/{len(df)}
- Near-threshold systems: {', '.join(near_threshold_list) if near_threshold_list else 'None'}

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_section_5_comfort_gap(df):
    """Generate Section 5: Comfort gap calculations."""
    if 'comfort_gap' not in df.columns:
        return """### 5. What is the "comfort gap" for environmental utilities?

[Comfort gap columns not found in DataFrame. This section requires additional analysis.]

**Finding:** [MANUAL: Your interpretation here]

---
"""
    
    comfort_gaps = df['comfort_gap']
    gap_min = comfort_gaps.min()
    gap_max = comfort_gaps.max()
    gap_mean = comfort_gaps.mean()
    
    comfort_gaps_per_hour = df['comfort_gap_per_hour']
    gap_per_hour_min = comfort_gaps_per_hour.min()
    gap_per_hour_max = comfort_gaps_per_hour.max()
    
    # Find example system with highest gap
    max_gap_idx = comfort_gaps.idxmax()
    max_gap_system = df.loc[max_gap_idx, 'model']
    max_gap_value = comfort_gaps.max()
    max_gap_per_hour = df.loc[max_gap_idx, 'comfort_gap_per_hour']
    
    # Calculate correlation with R/P
    correlation = df['comfort_gap'].corr(df['rp_ratio_scenario_a'])
    
    md = f"""### 5. What is the "comfort gap" for environmental utilities?

Comfort gap: ${gap_min:.0f}–${gap_max:.0f}/year avg (${gap_per_hour_min:.3f}–${gap_per_hour_max:.3f}/hour) in intangible value needed beyond energy savings.

**Calculation:**
- Breakeven savings = Cost ÷ Lifespan
- Gap = Breakeven - Actual savings

**Findings:**
- Gaps: ${gap_min:.0f} to ${gap_max:.0f}/year
- Correlation with R/P: {correlation:.3f} (high gaps → low R/P)
- Example: {max_gap_system} needs ${max_gap_value:.0f}/year (${max_gap_per_hour:.2f}/hour) in comfort value to break even

**Interpretation:** Energy savings alone insufficient—gap filled by non-monetizable benefits (comfort/health) that cannot compound.

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_section_6_monte_carlo(mc_results):
    """Generate Section 6: Monte Carlo volatility analysis."""
    if mc_results is None:
        return """### 6. How vulnerable are systems to price and rate volatility? (Monte Carlo Analysis)

[Monte Carlo results not available. Run analysis/replacement_trap_monte_carlo.ipynb to generate this section.]

**Finding:** [MANUAL: Your interpretation here]

---
"""
    
    avg_negative = mc_results['pct_negative_scenarios'].mean()
    systems_100_negative = (mc_results['pct_negative_scenarios'] == 100.0).sum()
    systems_0_negative = (mc_results['pct_negative_scenarios'] == 0.0).sum()
    
    # Separate trapped vs surplus (need to merge with df for this, but for now use simple threshold)
    # For simplicity, assume systems with >50% negative are "trapped"
    trapped_mc = mc_results[mc_results['pct_negative_scenarios'] > 50]
    surplus_mc = mc_results[mc_results['pct_negative_scenarios'] <= 50]
    
    md = f"""### 6. How vulnerable are systems to price and rate volatility? (Monte Carlo Analysis)

High vulnerability: Avg {avg_negative:.1f}% scenarios negative ({systems_100_negative}/{len(mc_results)} systems at 100%).

**Ranges:** Elec 0.5–3x, Water 1–10x, HELOC 6–12%
- Trapped systems: {systems_100_negative}/{len(mc_results)} systems with 100% negative scenarios
- Surplus: {systems_0_negative}/{len(mc_results)} systems with 0% negative (resilient)

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_section_7_income_burden(df):
    """Generate Section 7: Income burden analysis."""
    # Check if income burden data exists
    # This section may require additional analysis not in current DataFrame
    # For now, check if we can calculate from comfort gap
    
    if 'comfort_gap' not in df.columns:
        return """### 7. What is the income burden of comfort premium? (Income Sensitivity)

[Income burden analysis requires additional calculations. This section needs manual completion or additional analysis.]

**Finding:** [MANUAL: Your interpretation here]

---
"""
    
    # Note: Income burden calculations would require income quintile data
    # This is not currently in the DataFrame, so we'll note that
    md = """### 7. What is the income burden of comfort premium? (Income Sensitivity)

[Income burden calculations require income quintile data not currently in DataFrame. 
This section needs manual completion or additional analysis with Census income data.]

**Finding:** [MANUAL: Your interpretation here]

---
"""
    return md


def generate_summary(df, mc_results):
    """Generate complete summary markdown."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    sections = []
    sections.append(f"""---
generated_date: {date_str}
generated_timestamp: {timestamp}
source_data: data/replacement_trap_df.pkl
source_mc_data: data/monte_carlo_results.pkl
---

## Auto-Generated Executive Summary Data Sections

**Generated:** {timestamp}  
**Source:** Analysis results from `analysis/replacement_trap_core.ipynb`  
**Data:** `data/systems-data.json`

**Note:** This file contains auto-generated data sections. Narrative sections marked "[MANUAL]" should be completed manually.

---

""")
    
    sections.append(generate_section_1_rp_clustering(df))
    sections.append(generate_section_2_threshold_analysis(df))
    sections.append(generate_section_3_financing(df))
    sections.append(generate_section_4_variance(df))
    sections.append(generate_section_5_comfort_gap(df))
    sections.append(generate_section_6_monte_carlo(mc_results))
    sections.append(generate_section_7_income_burden(df))
    
    return ''.join(sections)


def main():
    """Main execution."""
    print("=" * 80)
    print("Executive Summary Data Generation")
    print("=" * 80)
    print()
    
    try:
        # Load data
        df, mc_results = load_data()
        print()
        
        # Generate summary
        print("Generating summary sections...")
        summary_md = generate_summary(df, mc_results)
        
        # Write to file
        notebooks_root = determine_notebooks_root()
        notes_dir = notebooks_root / 'notes'
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_path = notes_dir / f'{date_str}-executive-summary-data.md'
        
        output_path.write_text(summary_md, encoding='utf-8')
        
        print(f"✓ Summary written to {output_path}")
        print()
        print("=" * 80)
        print("Generation complete!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Review generated data sections")
        print("2. Complete [MANUAL] narrative sections")
        print("3. Merge with existing executive summary as needed")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

