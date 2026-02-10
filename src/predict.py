import os
import io
try:
    import torch
    import torch.nn as nn
    from torchvision import transforms, models
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    # Mock classes to prevent ImportErrors in other files
    class nn:
        Module = object
    
import random
from PIL import Image
from src.data_loader import load_data

import numpy as np
import cv2

# --- Configuration ---
IMG_SIZE = 224
if HAS_TORCH:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
else:
    device = None

# --- RGB Model Architecture ---
if HAS_TORCH:
    class RGBModel(nn.Module):
        def __init__(self):
            super(RGBModel, self).__init__()
            # Load Pre-trained ResNet18
            self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
            
            # Replace the final fully connected layer for Regression
            num_features = self.backbone.fc.in_features
            
            self.backbone.fc = nn.Sequential(
                nn.Linear(num_features, 128),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 1)
            )

        def forward(self, x):
            return self.backbone(x)
else:
    class RGBModel:
        pass

# --- TEXTURE ANALYSIS (NEW) ---
def calculate_texture_area(image_bytes):
    """
    Analyzes the image for high-frequency texture (roughness) to detect
    'invisible' food like white rice on white plates.
    
    Returns:
        texture_area (float): Percentage of the image (0-100) considered 'textured'.
    """
    try:
        if image_bytes is None:
            return 0.0

        # 1. Convert bytes to OpenCV Image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return 0.0

        # Resize for consistency and speed (target width 640px)
        height, width = img.shape[:2]
        target_width = 640
        if width > target_width:
            scale = target_width / width
            new_height = int(height * scale)
            img = cv2.resize(img, (target_width, new_height))

        # 2. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Laplacian Filter (Highlight edges/texture)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)

        # 4. Local Variance (Texture Energy)
        # Using a 9x9 kernel to capture grain-sized texture
        mu = cv2.blur(laplacian, (9, 9))
        mu2 = cv2.blur(laplacian * laplacian, (9, 9))
        variance = mu2 - mu * mu

        # 5. Thresholding
        # Variance threshold > 80.0 (Heuristic for rice grains/rough food)
        # Background/Smooth plate usually has variance < 20.0
        mask = (variance > 80.0).astype(np.uint8)

        # 6. Calculate Area Percentage
        non_zero_pixels = np.count_nonzero(mask)
        total_pixels = mask.size
        texture_percentage = (non_zero_pixels / total_pixels) * 100.0
        
        return texture_percentage

    except Exception as e:
        print(f"Warning: Texture analysis failed: {e}")
        return 0.0

# --- SMART CALIBRATION LOGIC (UPDATED) ---
def apply_smart_calibration(raw_pred, texture_pct=0.0):
    """
    Applies 'Balanced Calibration' with Texture-Aware overrides.
    
    Logic Tiers:
    1. High Density Boost ('Carreteiro' Logic):
       - IF Raw < 20.0 AND Texture > 35.0%
       - Confirms dense/granular food (rice/beans mix) that is camouflaged.
       - Formula: y = 2.5x + 30.0 (Stronger Boost)
       
    2. Standard Texture Override ('White Rice' Logic):
       - IF Raw < 10.0 AND Texture > 15.0%
       - Confirms simpler low-contrast food.
       - Formula: y = 2.3x + 18.0 (Standard Safety)
       
    3. Default Calibration:
       - No texture anomalies detected.
       - Formula: y = 2.3x + 18.0 (Standard Curve)
    """
    # 1. Sanity Check
    if raw_pred < 0: raw_pred = 0.0
    
    final_carbs = 0.0
    override_msg = None
    
    # 2. Logic Tiers
    
    # Tier 1: High Density Boost (Carreteiro / Mixed Rice)
    # Why? Raw 9g -> needs 60-70g. Current formula gives ~40g.
    # New curve: 9 * 2.5 = 22.5 + 30 = 52.5g (Closer to reality)
    if raw_pred < 20.0 and texture_pct > 35.0:
        final_carbs = (raw_pred * 2.5) + 30.0
        override_msg = "HIGH DENSITY BOOST (Carreteiro/Mixed)"
        
    # Tier 2: Standard Texture Override (White Rice)
    # Why? Raw 6g -> needs ~30g.
    # Curve: 6 * 2.3 = 13.8 + 18 = 31.8g (Safe floor)
    elif raw_pred < 10.0 and texture_pct > 15.0:
        final_carbs = (raw_pred * 2.3) + 18.0
        override_msg = "TEXTURE OVERRIDE (White Rice/Simple)"
        
    # Tier 3: Default
    else:
        final_carbs = (raw_pred * 2.3) + 18.0
        override_msg = None # Normal operation
    
    # 4. Safety Cap
    # Cap at 110g to prevent huge outliers
    if final_carbs > 110.0:
        final_carbs = 110.0
        
    return final_carbs, override_msg

def predict_bytes(model, image_bytes):
    """
    Predict carbs from raw image bytes using RGB-only model + Texture Analysis.
    """
    try:
        if image_bytes is None:
            raise ValueError("image_bytes is None")
            
        # 1. Texture Analysis (OpenCV)
        texture_pct = calculate_texture_area(image_bytes)
            
        # 2. RGB Prediction (PyTorch)
        img = Image.open(io.BytesIO(image_bytes))
        rgb_img = img.convert('RGB')
        
        val_transforms = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
        ])
        
        rgb_tensor = val_transforms(rgb_img).unsqueeze(0).to(device)
        
        model.eval()
        with torch.no_grad():
            output = model(rgb_tensor)
            raw_pred = output.item()
            
        # 3. Smart Calibration with Texture Input
        final_carbs, override_type = apply_smart_calibration(raw_pred, texture_pct)
        
        # 4. Robust Logging
        log_msg = f"DEBUG: Raw={raw_pred:.2f} | Texture={texture_pct:.1f}%"
        if override_type:
            log_msg += f" [{override_type}] -> Confirmed Food Presence"
        
        print(f"{log_msg} | Final={final_carbs:.2f}g")
            
        return final_carbs
        
    except Exception as e:
        print(f"Error in predict_bytes: {e}")
        import traceback
        traceback.print_exc()
        raise e

# --- Test Function (Optional) ---
def predict_random_samples(model_path, num_samples=5):
    pass