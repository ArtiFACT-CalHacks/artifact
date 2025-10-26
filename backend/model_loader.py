import torch
import torch.nn as nn
import torchvision.models as models
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EfficientNetV2L(nn.Module):
    """EfficientNet-V2-L model for binary video classification."""
    
    def __init__(self, num_classes=2, pretrained=True):
        super().__init__()
        if pretrained:
            self.backbone = models.efficientnet_v2_l(weights=models.EfficientNet_V2_L_Weights.IMAGENET1K_V1)
        else:
            self.backbone = models.efficientnet_v2_l(weights=None)
        
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

class ModelLoader:
    def __init__(self):
        self.model = None
        self.device = self._get_device()
        self.model_path = "../models/effnetv2_test.pth"
        
    def _get_device(self):
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    
    def load_model(self):
        """Load the trained model"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            logger.info(f"Using device: {self.device}")
            
            # Create model
            self.model = EfficientNetV2L(pretrained=True)
            
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device)
            classifier_state = checkpoint['classifier_state_dict']
            
            # Load classifier weights
            model_dict = self.model.state_dict()
            model_dict.update(classifier_state)
            self.model.load_state_dict(model_dict)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("✅ Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False
    
    def is_loaded(self):
        return self.model is not None
    
    def get_model(self):
        return self.model
    
    def get_device(self):
        return self.device
