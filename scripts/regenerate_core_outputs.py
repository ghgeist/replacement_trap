"""Regenerate core analysis outputs without launching Jupyter."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'lib'))

from replacement_trap_pipeline import (  # noqa: E402
    build_core_dataframe,
    write_reference_outputs,
)


def main() -> None:
    df = build_core_dataframe()
    assert len(df) == 11
    assert (df['warranty_years'] <= df['lifespan_years']).all()
    assert (df['rp_ratio_scenario_b'] <= df['rp_ratio_scenario_a'] + 1e-12).all()

    pkl_path = ROOT / 'data' / 'replacement_trap_df.pkl'
    csv_path = ROOT / 'data' / 'replacement_trap_df.csv'
    df.to_pickle(pkl_path)
    df.to_csv(csv_path, index=False)
    ref_path = write_reference_outputs(df)
    print(f'Wrote {pkl_path} shape={df.shape}')
    print(f'Wrote {csv_path}')
    print(f'Wrote {ref_path}')


if __name__ == '__main__':
    main()
