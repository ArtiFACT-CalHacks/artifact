"""
Main training script for binary AI video classification.
Trains EfficientNet-V2-L and ConvNeXt-V2-Base models on streaming dataset.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm
import os
from huggingface_hub import login
from dotenv import load_dotenv

from frame_extractor import create_data_loaders

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

# Load environment variables and authenticate with Hugging Face
load_dotenv()
hf_token = os.getenv("HUGGINGFACE_TOKEN")
if hf_token:
    try:
        login(token=hf_token)
        logger.info("Authenticated with Hugging Face")
    except Exception as e:
        logger.warning(f"Failed to authenticate with Hugging Face: {e}")


class EfficientNetV2L(nn.Module):
    """EfficientNet-V2-L model for binary video classification."""
    
    def __init__(self, num_classes=2, pretrained=True):
        super().__init__()
        if pretrained:
            self.backbone = models.efficientnet_v2_l(weights=models.EfficientNet_V2_L_Weights.IMAGENET1K_V1)
        else:
            self.backbone = models.efficientnet_v2_l(weights=None)
        
        # Replace classifier for 2-class output
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
        return video_features


class ConvNeXtV2Base(nn.Module):
    """ConvNeXt-Base model for binary video classification."""
    
    def __init__(self, num_classes=2, pretrained=True):
        super().__init__()
        if pretrained:
            self.backbone = models.convnext_base(weights=models.ConvNeXt_Base_Weights.IMAGENET1K_V1)
        else:
            self.backbone = models.convnext_base(weights=None)
        
        # Replace classifier for 2-class output
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
        return video_features


class Trainer:
    """Training class for binary classification models."""
    
    def __init__(self, model, model_name, device):
        self.model = model.to(device)
        self.model_name = model_name
        self.device = device
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=1e-4)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=2
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
            labels = batch['label'].to(self.device).long()
            
            self.optimizer.zero_grad()
            
            # Forward pass
            outputs = self.model(frames)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Statistics
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
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
                labels = batch['label'].to(self.device).long()
                
                outputs = self.model(frames)
                loss = self.criterion(outputs, labels)
                
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
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
        """Save only custom classifier weights and training state."""
        Path("./models").mkdir(exist_ok=True)
        
        # Extract only the custom classifier weights
        classifier_state = {}
        for name, param in self.model.named_parameters():
            # Save backbone.classifier parameters (the custom layers we trained)
            if 'backbone.classifier' in name:
                classifier_state[name] = param.data
        
        # Debug: Print what we're saving
        print(f"🔍 Saving classifier parameters:")
        for name in classifier_state.keys():
            print(f"  - {name}: {classifier_state[name].shape}")
        
        torch.save({
            'classifier_state_dict': classifier_state,
            'optimizer_state_dict': self.optimizer.state_dict(),
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'train_accuracies': self.train_accuracies,
            'val_accuracies': self.val_accuracies,
            'model_name': self.model_name
        }, path)


def main():
    """Main training function - Small-scale EfficientNet-V2-L test."""
    # Set device (prefer MPS for Apple Silicon)
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using Apple Silicon GPU (MPS)")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Using CUDA GPU")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    
    # Load pre-extracted frames
    logger.info("Loading pre-extracted frames...")
    try:
        train_loader, val_loader = create_data_loaders(
            data_dir="./data_frames",
            batch_size=8,
            num_workers=2
        )
        logger.info("✅ Data loaders created successfully")
        logger.info(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        logger.error("Please run: python frame_extractor.py --download --output ./data_frames")
        return
    
    # EfficientNet-V2-L training with expanded dataset
    logger.info("\n" + "="*60)
    logger.info("EFFICIENTNET-V2-L TRAINING WITH EXPANDED DATASET")
    logger.info("="*60)
    logger.info("Configuration:")
    logger.info("- Epochs: 15")
    logger.info("- Batch size: 8")
    logger.info("- Learning rate: 1e-4")
    logger.info("- Device: " + str(device))
    logger.info("- Early stopping: val_acc > 0.9 or loss plateau")
    logger.info(f"- Train batches: {len(train_loader)}")
    logger.info(f"- Val batches: {len(val_loader)}")
    
    try:
        efficientnet = EfficientNetV2L(pretrained=True)
        efficientnet_trainer = Trainer(efficientnet, "EfficientNetV2L", device)
        
        # Custom training loop for small-scale test
        best_val_loss = float('inf')
        patience_counter = 0
        epochs = 15
        
        for epoch in range(epochs):
            logger.info(f"\nEpoch {epoch+1}/{epochs}")
            logger.info("-" * 50)
            
            # Train
            train_loss, train_acc = efficientnet_trainer.train_epoch(train_loader)
            
            # Validate
            val_loss, val_acc = efficientnet_trainer.validate_epoch(val_loader)
            
            # Update learning rate
            efficientnet_trainer.scheduler.step(val_loss)
            
            # Store history
            efficientnet_trainer.train_losses.append(train_loss)
            efficientnet_trainer.val_losses.append(val_loss)
            efficientnet_trainer.train_accuracies.append(train_acc)
            efficientnet_trainer.val_accuracies.append(val_acc)
            
            # Log results
            logger.info(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            logger.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            logger.info(f"Learning Rate: {efficientnet_trainer.optimizer.param_groups[0]['lr']:.6f}")
            
            # Early stopping conditions
            # if val_acc > 90.0:  # > 90% accuracy
            #     logger.info(f"🎯 Early stopping: Validation accuracy {val_acc:.2f}% > 90%")
            #     break
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                efficientnet_trainer.save_model("./models/effnetv2_test.pth")
                logger.info("💾 New best model saved to models/effnetv2_test.pth")
            else:
                patience_counter += 1
                # if patience_counter >= 2:  # Early stop if loss doesn't improve for 2 epochs
                #     logger.info(f"🛑 Early stopping: Loss plateaued for {patience_counter} epochs")
                #     break
        
        logger.info("✅ EfficientNet-V2-L training test completed successfully")
        logger.info(f"Final validation accuracy: {efficientnet_trainer.val_accuracies[-1]:.2f}%")
        logger.info(f"Final validation loss: {efficientnet_trainer.val_losses[-1]:.4f}")
        
    except Exception as e:
        logger.error(f"❌ EfficientNet-V2-L training failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # ConvNeXt training commented out for now
    # logger.info("\n" + "="*60)
    # logger.info("TRAINING CONVNEXT-BASE")
    # logger.info("="*60)
    # 
    # try:
    #     convnext = ConvNeXtV2Base(pretrained=True)
    #     convnext_trainer = Trainer(convnext, "ConvNeXtV2Base", device)
    #     convnext_trainer.train(train_loader, val_loader, epochs=20)
    #     logger.info("✅ ConvNeXt-Base training completed successfully")
    # except Exception as e:
    #     logger.error(f"❌ ConvNeXt-Base training failed: {e}")
    #     import traceback
    #     logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("TRAINING COMPLETED")
    logger.info("="*60)
    logger.info("Model saved to ./models/effnetv2_test.pth")
    logger.info("Run evaluate.py to test the model!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.error(f"Training failed with error: {e}")
        raise
