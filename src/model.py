import torch
import torch.nn as nn
from torchvision import models

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
