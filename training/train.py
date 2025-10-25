"""
Main training script for DeepAction classification.
Trains EfficientNet-V2-L and ConvNeXt-V2-Base models.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
from torch.utils.data import DataLoader
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm
import json
from datetime import datetime

from dataset_utils import create_data_loaders

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EfficientNetV2L(nn.Module):
    """EfficientNet-V2-L model for video classification."""
    
    def __init__(self, num_classes=1, pretrained=True):
        super().__init__()
        self.backbone = models.efficientnet_v2_l(pretrained=pretrained)
        num_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(num_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        batch_size, num_frames, channels, height, width = x.shape
        x = x.view(batch_size * num_frames, channels, height, width)
        features = self.backbone(x)
        features = features.view(batch_size, num_frames, -1)
        video_features = torch.mean(features, dim=1)
        return torch.sigmoid(video_features.squeeze(-1))


class ConvNeXtV2Base(nn.Module):
    """ConvNeXt-V2-Base model for video classification."""
    
    def __init__(self, num_classes=1, pretrained=True):
        super().__init__()
        self.backbone = models.convnext_v2_base(pretrained=pretrained)
        num_features = self.backbone.classifier[2].in_features
        self.backbone.classifier = nn.Sequential(
            nn.LayerNorm(num_features, eps=1e-6),
            nn.Flatten(start_dim=1),
            nn.Dropout(0.2),
            nn.Linear(num_features, 512),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        batch_size, num_frames, channels, height, width = x.shape
        x = x.view(batch_size * num_frames, channels, height, width)
        features = self.backbone(x)
        features = features.view(batch_size, num_frames, -1)
        video_features = torch.mean(features, dim=1)
        return torch.sigmoid(video_features.squeeze(-1))


class Trainer:
    """Training class for both models."""
    
    def __init__(self, model, model_name, device):
        self.model = model.to(device)
        self.model_name = model_name
        self.device = device
        self.criterion = nn.BCEWithLogitsLoss()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=1e-4)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=2, verbose=True
        )
        
        # Training history
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []
    
    def train_epoch(self, train_loader):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        progress_bar = tqdm(train_loader, desc=f"Training {self.model_name}")
        
        for batch in progress_bar:
            frames = batch['frames'].to(self.device)
            labels = batch['label'].to(self.device)
            
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(frames)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Statistics
            total_loss += loss.item()
            predictions = (outputs > 0.5).float()
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
            
            progress_bar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100. * correct / total:.2f}%'
            })
        
        avg_loss = total_loss / len(train_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def validate_epoch(self, val_loader):
        """Validate for one epoch."""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc=f"Validating {self.model_name}"):
                frames = batch['frames'].to(self.device)
                labels = batch['label'].to(self.device)
                
                outputs = self.model(frames)
                loss = self.criterion(outputs, labels)
                
                total_loss += loss.item()
                predictions = (outputs > 0.5).float()
                correct += (predictions == labels).sum().item()
                total += labels.size(0)
        
        avg_loss = total_loss / len(val_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def train(self, train_loader, val_loader, epochs=20, patience=5):
        """Train the model."""
        best_val_loss = float('inf')
        patience_counter = 0
        
        logger.info(f"Starting training for {self.model_name}")
        logger.info(f"Epochs: {epochs}, Device: {self.device}")
        
        for epoch in range(epochs):
            logger.info(f"\nEpoch {epoch+1}/{epochs}")
            logger.info("-" * 50)
            
            # Train
            train_loss, train_acc = self.train_epoch(train_loader)
            
            # Validate
            val_loss, val_acc = self.validate_epoch(val_loader)
            
            # Update learning rate
            self.scheduler.step(val_loss)
            
            # Store history
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.train_accuracies.append(train_acc)
            self.val_accuracies.append(val_acc)
            
            # Log results
            logger.info(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            logger.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            logger.info(f"Learning Rate: {self.optimizer.param_groups[0]['lr']:.6f}")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                self.save_model(f"./models/{self.model_name.lower()}.pth")
                logger.info("New best model saved!")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered after {epoch+1} epochs")
                break
        
        logger.info(f"Training completed for {self.model_name}")
        logger.info(f"Best validation loss: {best_val_loss:.4f}")
    
    def save_model(self, path):
        """Save model checkpoint."""
        Path("./models").mkdir(exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'train_accuracies': self.train_accuracies,
            'val_accuracies': self.val_accuracies
        }, path)


def main():
    """Main training function."""
    # Set device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using Apple Silicon GPU (MPS)")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Using CUDA GPU")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    
    # Check if data directory exists
    if not Path("./data").exists():
        logger.error("Data directory not found. Please create ./data/train/ai and ./data/train/real directories")
        logger.info("You can use dataset_utils.download_faridlab_dataset() to download the dataset")
        return
    
    # Create data loaders
    logger.info("Loading dataset...")
    try:
        train_loader, val_loader = create_data_loaders(
            batch_size=8,
            num_workers=2,
            image_size=(224, 224)
        )
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        logger.info("Please ensure your data is organized as:")
        logger.info("  ./data/train/ai/*.mp4")
        logger.info("  ./data/train/real/*.mp4")
        logger.info("  ./data/val/ai/*.mp4")
        logger.info("  ./data/val/real/*.mp4")
        return
    
    # Train EfficientNet-V2-L
    logger.info("\n" + "="*60)
    logger.info("TRAINING EFFICIENTNET-V2-L")
    logger.info("="*60)
    
    efficientnet = EfficientNetV2L(pretrained=True)
    efficientnet_trainer = Trainer(efficientnet, "EfficientNetV2L", device)
    efficientnet_trainer.train(train_loader, val_loader, epochs=20)
    
    # Train ConvNeXt-V2-Base
    logger.info("\n" + "="*60)
    logger.info("TRAINING CONVNEXT-V2-BASE")
    logger.info("="*60)
    
    convnext = ConvNeXtV2Base(pretrained=True)
    convnext_trainer = Trainer(convnext, "ConvNeXtV2Base", device)
    convnext_trainer.train(train_loader, val_loader, epochs=20)
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("TRAINING COMPLETED")
    logger.info("="*60)
    logger.info(f"EfficientNet best validation loss: {min(efficientnet_trainer.val_losses):.4f}")
    logger.info(f"ConvNeXt best validation loss: {min(convnext_trainer.val_losses):.4f}")
    logger.info("Models saved to ./models/ directory")
    logger.info("Run evaluate.py to test the models!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.error(f"Training failed with error: {e}")
        raise
