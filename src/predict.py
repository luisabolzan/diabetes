import os
import torch
import random
import numpy as np
from PIL import Image
from torchvision import transforms
from src.data_loader import load_data
from src.train import DualBranchModel, IMG_SIZE, device

def predict_random_samples(model_path, num_samples=5):
    print(f"Loading data from {os.path.join('mobile-ios-pwa', 'data', 'raw')}...")
    data_dir = os.path.join("mobile-ios-pwa", "data", "raw")
    full_data = load_data(data_dir)
    
    if len(full_data) == 0:
        print("No data found!")
        return

    print(f"Total dataset size: {len(full_data)}")
    
    # Select random samples
    if len(full_data) < num_samples:
        samples = full_data
    else:
        samples = random.sample(full_data, num_samples)

    # Prepare Model
    print(f"Loading model from {model_path}...")
    model = DualBranchModel().to(device)
    
    if not os.path.exists(model_path):
        print(f"Error: Model file {model_path} not found. Run training first.")
        return

    # Load weights
    # map_location ensures we can load on CPU even if trained on GPU
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # Transforms (Must match Validation transform in train.py)
    val_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    depth_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
    ])

    print("\n--- Prediction Results ---")
    print(f"{'Dish ID':<20} | {'True Carbs':<12} | {'Pred Carbs':<12} | {'Error (g)':<10}")
    print("-" * 65)

    mae_sum = 0.0

    with torch.no_grad():
        for i, sample in enumerate(samples):
            rgb_path, depth_path, calories, true_carbs = sample
            
            # Extract Dish ID from path for display
            # Path structure: .../realsense_overhead/dish_[ID]/rgb.png
            dish_id = os.path.basename(os.path.dirname(rgb_path))
            
            # Load Images
            try:
                rgb_img = Image.open(rgb_path).convert('RGB')
                depth_img = Image.open(depth_path).convert('L')
            except Exception as e:
                print(f"Error loading image for {dish_id}: {e}")
                continue

            # Transform
            rgb_tensor = val_transforms(rgb_img).unsqueeze(0).to(device) # Add batch dim
            depth_tensor = depth_transforms(depth_img).unsqueeze(0).to(device)

            # Predict
            output = model(rgb_tensor, depth_tensor)
            pred_carbs = output.item()
            
            # Calculate Error
            error = abs(pred_carbs - true_carbs)
            mae_sum += error

            print(f"{dish_id:<20} | {true_carbs:<12.2f} | {pred_carbs:<12.2f} | {error:<10.2f}")

    avg_error = mae_sum / len(samples)
    print("-" * 65)
    print(f"Average Error on these {len(samples)} samples: {avg_error:.2f} g")

if __name__ == "__main__":
    predict_random_samples("nutrition5k_model.pth")
