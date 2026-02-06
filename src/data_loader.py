import os

import glob
from typing import List, Tuple

def load_data(data_dir: str) -> List[Tuple[str, str, float, float]]:
    """
    Loads data from the Nutrition5k dataset.

    Args:
        data_dir: The root directory containing the dataset.
                  Expected structure:
                  - data_dir/dish_metadata_cafe*.csv OR data_dir/metadata/dish_metadata_cafe*.csv
                  - data_dir/realsense_overhead/dish_[ID]/rgb.png
                  - data_dir/realsense_overhead/dish_[ID]/depth_raw.png

    Returns:
        A list of tuples, where each tuple contains:
        (rgb_image_path, depth_image_path, calories, total_carb)
    """
    
    data = []
    
    # Search for metadata CSVs in root and metadata subdirectory
    csv_patterns = [
        os.path.join(data_dir, "dish_metadata_cafe*.csv"),
        os.path.join(data_dir, "metadata", "dish_metadata_cafe*.csv")
    ]
    
    csv_files = []
    for pattern in csv_patterns:
        csv_files.extend(glob.glob(pattern))
        
    print(f"Found {len(csv_files)} metadata files: {[os.path.basename(f) for f in csv_files]}")

    for csv_file in csv_files:
        try:
            print(f"Reading {csv_file}...")
            with open(csv_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) < 5:
                        continue
                        
                    dish_id = parts[0]
                    try:
                        calories = float(parts[1])
                        total_carb = float(parts[4])
                    except ValueError:
                        continue # Skip header or bad lines
                    
                    rgb_path = os.path.join(data_dir, 'realsense_overhead', dish_id, 'rgb.png')
                    depth_path = os.path.join(data_dir, 'realsense_overhead', dish_id, 'depth_raw.png')
                    
                    if os.path.exists(rgb_path) and os.path.exists(depth_path):
                        data.append((rgb_path, depth_path, calories, total_carb))
                
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue

    return data

if __name__ == "__main__":
    # Example usage
    pass
