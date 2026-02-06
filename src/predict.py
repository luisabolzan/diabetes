import os
import io
import torch
import torch.nn as nn
import random
import numpy as np
from PIL import Image
from torchvision import transforms, models
from src.data_loader import load_data

# --- Configuration ---
IMG_SIZE = 224
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# --- Model Architecture (Self-Contained) ---
class DualBranchModel(nn.Module):
    def __init__(self):
        super(DualBranchModel, self).__init__()
        
        # Branch 1: RGB (Pre-trained ResNet18)
        self.rgb_backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        # Remove the final fully connected layer
        self.rgb_features = nn.Sequential(*list(self.rgb_backbone.children())[:-1])
        # ResNet18 output dim is 512
        
        # Branch 2: Depth (Simple CNN)
        self.depth_cnn = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2), # 112
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2), # 56
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)) # Output 64x1x1
        )
        # Depth output dim is 64

        # Fusion
        fusion_dim = 512 + 64 # 576
        
        self.regressor = nn.Sequential(
            nn.Linear(fusion_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1) # Output: Total Carbs
        )

    def forward(self, rgb, depth):
        # RGB Branch
        x_rgb = self.rgb_features(rgb)
        x_rgb = torch.flatten(x_rgb, 1) # (Batch, 512)
        
        # Depth Branch
        x_depth = self.depth_cnn(depth)
        x_depth = torch.flatten(x_depth, 1) # (Batch, 64)
        
        # Concatenate
        combined = torch.cat((x_rgb, x_depth), dim=1)
        
        # Regression
        output = self.regressor(combined)
        return output

# --- Prediction Functions ---

def predict_bytes(model, image_bytes):
    """
    Predict carbs from raw image bytes.
    Automatically generates a synthetic depth map (Grayscale) for the Dual-Branch model.
    """
    try:
        # Load RGB from bytes
        rgb_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Fake Depth Map (Grayscale) idea:
        # Use simple grayscale conversion as structural proxy for depth
        depth_img = rgb_img.convert('L')
        
        # Transforms (Must match training validation)
        val_transforms = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        depth_transforms = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
        ])
        
        # Apply Transforms & Batch Dim
        rgb_tensor = val_transforms(rgb_img).unsqueeze(0).to(device)
        depth_tensor = depth_transforms(depth_img).unsqueeze(0).to(device)
        
        # Inference
        with torch.no_grad():
            output = model(rgb_tensor, depth_tensor)
            pred_carbs = output.item()
            
        return pred_carbs
        
    except Exception as e:
        print(f"Error in predict_bytes: {e}")
        raise e

def predict_random_samples(model_path, num_samples=5):
    print(f"Loading data from {os.path.join('mobile-ios-pwa', 'data', 'raw')}...")
    data_dir = os.path.join("mobile-ios-pwa", "data", "raw")
    full_data = load_data(data_dir)
    
    if len(full_data) == 0:
        print("No data found!")
        return

    print(f"Total dataset size: {len(full_data)}")
    
    if len(full_data) < num_samples:
        samples = full_data
    else:
        samples = random.sample(full_data, num_samples)

    print(f"Loading model from {model_path}...")
    model = DualBranchModel().to(device)
    
    if not os.path.exists(model_path):
        print(f"Error: Model file {model_path} not found.")
        return

    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    # Transforms
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
            dish_id = os.path.basename(os.path.dirname(rgb_path))
            
            try:
                rgb_img = Image.open(rgb_path).convert('RGB')
                depth_img = Image.open(depth_path).convert('L')
            except Exception as e:
                continue

            rgb_tensor = val_transforms(rgb_img).unsqueeze(0).to(device)
            depth_tensor = depth_transforms(depth_img).unsqueeze(0).to(device)

            output = model(rgb_tensor, depth_tensor)
            pred_carbs = output.item()
            
            error = abs(pred_carbs - true_carbs)
            mae_sum += error

            print(f"{dish_id:<20} | {true_carbs:<12.2f} | {pred_carbs:<12.2f} | {error:<10.2f}")

    print("-" * 65)
    print(f"Average Error on these {len(samples)} samples: {mae_sum / len(samples):.2f} g")

if __name__ == "__main__":
    predict_random_samples("nutrition5k_model.pth")
