import os
import sys
from src.data_loader import load_data

def test_loader():
    # Adjust this path if necessary to match your environment
    data_dir = os.path.join("mobile-ios-pwa", "data", "raw")
    
    print(f"Testing data loader with data_dir: {os.path.abspath(data_dir)}")
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found at {os.path.abspath(data_dir)}")
        return

    data = load_data(data_dir)
    
    print(f"Total samples loaded: {len(data)}")
    
    if len(data) > 0:
        print("\nFirst 5 samples:")
        for i, sample in enumerate(data[:5]):
            print(f"Sample {i+1}:")
            print(f"  RGB: {sample[0]}")
            print(f"  Depth: {sample[1]}")
            print(f"  Calories: {sample[2]}")
            print(f"  Carbs: {sample[3]}")
    else:
        print("No samples loaded. Check data paths and metadata files.")

if __name__ == "__main__":
    test_loader()
