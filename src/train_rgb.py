import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split
from src.data_loader import load_data

# --- Configuration ---
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 10
IMG_SIZE = 224
DATA_DIR = os.path.join("mobile-ios-pwa", "data", "raw")
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# --- Dataset ---
class Nutrition5kRGBDataset(Dataset):
    def __init__(self, data, transform=None):
        self.data = data
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # We ignore depth_path (index 1)
        rgb_path, _, _, carbs = self.data[idx]
        
        try:
            rgb_img = Image.open(rgb_path).convert('RGB')
        except Exception:
            rgb_img = Image.new('RGB', (IMG_SIZE, IMG_SIZE))
            
        if self.transform:
            rgb_tensor = self.transform(rgb_img)
        else:
            rgb_tensor = transforms.ToTensor()(rgb_img)
            
        return rgb_tensor, torch.tensor([carbs], dtype=torch.float32)

# --- Model ---
class RGBModel(nn.Module):
    def __init__(self):
        super(RGBModel, self).__init__()
        # Load Pre-trained ResNet18
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        
        # Replace the final fully connected layer
        # ResNet18.fc is Linear(in_features=512, out_features=1000)
        # We want output=1 (regression)
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

# --- Training Loop ---
def train_rgb_model():
    print(f"Using device: {DEVICE}")
    print("Loading data...")
    full_data = load_data(DATA_DIR)
    
    if not full_data:
        print("No data found!")
        return

    train_data, val_data = train_test_split(full_data, test_size=0.2, random_state=42)
    print(f"Train: {len(train_data)} | Val: {len(val_data)}")

    # Transforms
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

    # Loaders
    train_dataset = Nutrition5kRGBDataset(train_data, transform=train_transforms)
    val_dataset = Nutrition5kRGBDataset(val_data, transform=val_transforms)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # Model
    model = RGBModel().to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print("Starting training...")
    best_mae = float('inf')

    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0
        
        for rgb, targets in train_loader:
            rgb, targets = rgb.to(DEVICE), targets.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(rgb)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * rgb.size(0)
            
        epoch_loss = running_loss / len(train_dataset)
        
        # Validation
        model.eval()
        val_mae = 0.0
        
        with torch.no_grad():
            for rgb, targets in val_loader:
                rgb, targets = rgb.to(DEVICE), targets.to(DEVICE)
                outputs = model(rgb)
                mae = torch.abs(outputs - targets).sum()
                val_mae += mae.item()
                
        epoch_val_mae = val_mae / len(val_dataset)
        
        print(f"Epoch {epoch+1}/{EPOCHS} -> Loss: {epoch_loss:.2f} | Val MAE: {epoch_val_mae:.2f} g")
        
        # Save Best
        if epoch_val_mae < best_mae:
            best_mae = epoch_val_mae
            torch.save(model.state_dict(), "nutrition5k_model_rgb.pth")

    print(f"Training complete. Best MAE: {best_mae:.2f} g")
    print("Model saved to nutrition5k_model_rgb.pth")

if __name__ == "__main__":
    train_rgb_model()
