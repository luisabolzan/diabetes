import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split
import numpy as np
from src.data_loader import load_data

# --- Data Configuration ---
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 10
IMG_SIZE = 224
DATA_DIR = os.path.join("mobile-ios-pwa", "data", "raw")

# --- Device Config ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# --- Dataset Class ---
class Nutrition5kDataset(Dataset):
    def __init__(self, data, transform=None):
        """
        Args:
            data: List of tuples (rgb_path, depth_path, calories, carbs)
            transform: PyTorch transforms for RGB images
        """
        self.data = data
        self.transform = transform
        self.depth_transform = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            # Normalize depth roughly if needed, usually just ToTensor is enough for 16-bit or 8-bit pngs 
            # interpreted as 0-1 float.
        ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        rgb_path, depth_path, calories, carbs = self.data[idx]

        # Load RGB
        try:
            rgb_img = Image.open(rgb_path).convert('RGB')
        except Exception:
            # Fallback for corrupted images creates a black image
            rgb_img = Image.new('RGB', (IMG_SIZE, IMG_SIZE))

        # Load Depth
        try:
            depth_img = Image.open(depth_path).convert('L') # Grayscale
        except Exception:
            depth_img = Image.new('L', (IMG_SIZE, IMG_SIZE))

        if self.transform:
            rgb_tensor = self.transform(rgb_img)
        else:
            rgb_tensor = transforms.ToTensor()(rgb_img)

        # Process Depth
        depth_tensor = self.depth_transform(depth_img)

        # Targets
        # We are predicting Carbs (index 3). We could also predict calories (index 2) if desired.
        target = torch.tensor([carbs], dtype=torch.float32)

        return rgb_tensor, depth_tensor, target

# --- Model Architecture ---
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

# --- Training Function ---
def train_model():
    print("Loading data...")
    # 1. Load Data
    full_data = load_data(DATA_DIR)
    
    if len(full_data) == 0:
        print("No data found! Check paths in data_loader.py")
        return

    print(f"Total samples: {len(full_data)}")
    
    # 2. Split Data
    train_data, val_data = train_test_split(full_data, test_size=0.2, random_state=42)
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")

    # 3. Transforms
    train_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transforms = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 4. Data Loaders
    train_dataset = Nutrition5kDataset(train_data, transform=train_transforms)
    val_dataset = Nutrition5kDataset(val_data, transform=val_transforms)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # 5. Initialize Model
    model = DualBranchModel().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # 6. Training Loop
    print("\nStarting training...")
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        
        for rgb, depth, targets in train_loader:
            rgb, depth, targets = rgb.to(device), depth.to(device), targets.to(device)
            
            optimizer.zero_grad()
            outputs = model(rgb, depth)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * rgb.size(0)
            
        epoch_loss = running_loss / len(train_dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_mae = 0.0
        
        with torch.no_grad():
            for rgb, depth, targets in val_loader:
                rgb, depth, targets = rgb.to(device), depth.to(device), targets.to(device)
                outputs = model(rgb, depth)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * rgb.size(0)
                
                # Calculate MAE
                mae = torch.abs(outputs - targets).sum()
                val_mae += mae.item()
                
        epoch_val_loss = val_loss / len(val_dataset)
        epoch_val_mae = val_mae / len(val_dataset)
        
        print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {epoch_loss:.2f} | Val Loss: {epoch_val_loss:.2f} | Val MAE: {epoch_val_mae:.2f} g")

    print("\nTraining complete.")
    
    # Save Model
    save_path = "nutrition5k_model.pth"
    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")

if __name__ == "__main__":
    train_model()
