"""
Convert pickle files to CSV format.

This script converts .pkl files in the data directory to .csv files.
"""

import pandas as pd
from pathlib import Path


def determine_notebooks_root():
    """Determine the notebooks root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def convert_pkl_to_csv(pkl_path: Path, csv_path: Path = None):
    """
    Convert a pickle file to CSV.
    
    Args:
        pkl_path: Path to the .pkl file
        csv_path: Optional path for output CSV. If None, uses same name with .csv extension
    """
    if not pkl_path.exists():
        print(f"Error: File not found: {pkl_path}")
        return False
    
    # Load the pickle file
    try:
        data = pd.read_pickle(pkl_path)
        
        # Determine output path
        if csv_path is None:
            csv_path = pkl_path.with_suffix('.csv')
        
        # Convert to CSV
        if isinstance(data, pd.DataFrame):
            data.to_csv(csv_path, index=False)
            print(f"Converted: {pkl_path.name} -> {csv_path.name}")
            print(f"  Shape: {data.shape}")
            print(f"  Columns: {list(data.columns)}")
            return True
        else:
            print(f"Error: {pkl_path.name} does not contain a DataFrame")
            print(f"  Type: {type(data)}")
            return False
            
    except Exception as e:
        print(f"Error converting {pkl_path.name}: {e}")
        return False


def main():
    """Convert all .pkl files in the data directory to CSV."""
    notebooks_root = determine_notebooks_root()
    data_dir = notebooks_root / 'data'
    
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        return
    
    # Find all .pkl files
    pkl_files = list(data_dir.glob('*.pkl'))
    
    if not pkl_files:
        print(f"No .pkl files found in {data_dir}")
        return
    
    print(f"Found {len(pkl_files)} .pkl file(s) to convert:\n")
    
    for pkl_file in pkl_files:
        convert_pkl_to_csv(pkl_file)
        print()
    
    print("Conversion complete!")


if __name__ == '__main__':
    main()

