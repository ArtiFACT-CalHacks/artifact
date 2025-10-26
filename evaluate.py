"""
Model evaluation script for binary AI video classification.
Tests trained models and shows confidence scores.
"""

import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from frame_extractor import create_data_loaders

# Set up logging
logging.basicConfig(level=logging.INFO)
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


# ConvNeXt model removed - only using EfficientNet

def load_model(model_path, model_class, device):
    """Load trained model from checkpoint."""
    # Create model with pretrained backbone
    model = model_class(pretrained=True)
    
    # Load only our custom classifier weights
    checkpoint = torch.load(model_path, map_location=device)
    classifier_state = checkpoint['classifier_state_dict']
    
    # Debug: Print what we're loading
    print(f"🔍 Loading classifier parameters:")
    for name in classifier_state.keys():
        print(f"  - {name}: {classifier_state[name].shape}")
    
    # Debug: Print model's current classifier parameters
    print(f"🔍 Model's current classifier parameters:")
    for name, param in model.named_parameters():
        if 'backbone.classifier' in name:
            print(f"  - {name}: {param.shape}")
    
    # Load classifier weights
    model_dict = model.state_dict()
    print(f"🔍 Model state dict keys: {len(model_dict)} total")
    
    # Check if keys match
    missing_keys = []
    unexpected_keys = []
    for key in classifier_state.keys():
        if key not in model_dict:
            missing_keys.append(key)
    for key in model_dict.keys():
        if key in classifier_state and key not in classifier_state:
            unexpected_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing keys: {missing_keys}")
    if unexpected_keys:
        print(f"❌ Unexpected keys: {unexpected_keys}")
    
    model_dict.update(classifier_state)
    result = model.load_state_dict(model_dict)
    
    # Debug: Check if loading was successful
    print(f"🔍 Load state dict result: {result}")
    
    model.to(device)
    model.eval()
    return model


def evaluate_model(model, model_name, device, val_loader):
    """Evaluate model on validation set."""
    logger.info(f"Evaluating {model_name}...")
    
    all_predictions = []
    all_labels = []
    all_confidences = []
    frame_confidences = []
    
    with torch.no_grad():
        for i, batch in enumerate(tqdm(val_loader, desc=f"Evaluating {model_name}")):
                
            frames = batch['frames'].to(device)
            labels = batch['label'].to(device).long()
            
            # Get predictions
            outputs = model(frames)
            probabilities = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs, 1)
            
            # Store results
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_confidences.extend(probabilities.cpu().numpy())
            
            # Get frame-level confidences
            batch_size_actual, num_frames, channels, height, width = frames.shape
            frames_flat = frames.view(batch_size_actual * num_frames, channels, height, width)
            frame_outputs = model.backbone(frames_flat)
            frame_probs = torch.softmax(frame_outputs, dim=1)
            frame_confidences.extend(frame_probs.cpu().numpy())
    
    # Calculate metrics
    accuracy = accuracy_score(all_labels, all_predictions)
    precision = precision_score(all_labels, all_predictions, average='binary')
    recall = recall_score(all_labels, all_predictions, average='binary')
    f1 = f1_score(all_labels, all_predictions, average='binary')
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_predictions)
    
    # Confidence statistics
    confidences = np.array(all_confidences)
    ai_mask = np.array(all_labels) == 1
    real_mask = np.array(all_labels) == 0
    
    ai_confidences = confidences[ai_mask, 1] if np.any(ai_mask) else np.array([])
    real_confidences = confidences[real_mask, 0] if np.any(real_mask) else np.array([])
    
    logger.info(f"\n{model_name} Results:")
    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall: {recall:.4f}")
    logger.info(f"F1-Score: {f1:.4f}")
    logger.info(f"Confusion Matrix:")
    logger.info(f"  Real: {cm[0,0]} correct, {cm[0,1]} misclassified")
    logger.info(f"  AI:   {cm[1,1]} correct, {cm[1,0]} misclassified")
    if len(ai_confidences) > 0:
        logger.info(f"Average AI confidence: {np.mean(ai_confidences):.4f}")
    else:
        logger.info("Average AI confidence: N/A (no AI samples)")
    
    if len(real_confidences) > 0:
        logger.info(f"Average Real confidence: {np.mean(real_confidences):.4f}")
    else:
        logger.info("Average Real confidence: N/A (no Real samples)")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'confidences': confidences,
        'frame_confidences': np.array(frame_confidences)
    }


def main():
    """Main evaluation function."""
    # Set device
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Using CUDA GPU")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using Apple Silicon GPU (MPS)")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    
    # Check if models exist
    models_dir = Path("./models")
    if not models_dir.exists():
        logger.error("Models directory not found. Please run train.py first.")
        return
    
    # Load validation data
    logger.info("Loading validation data...")
    try:
        _, val_loader = create_data_loaders(
            data_dir="./data_frames",
            batch_size=8,
            num_workers=2
        )
        logger.info("✅ Validation data loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load validation data: {e}")
        logger.error("Please run: python frame_extractor.py --download --output ./data_frames")
        return
    
    # Evaluate EfficientNet-V2-L
    efficientnet_path = models_dir / "effnetv2_test.pth"
    if efficientnet_path.exists():
        logger.info("\n" + "="*60)
        logger.info("EVALUATING EFFICIENTNET-V2-L")
        logger.info("="*60)
        
        try:
            efficientnet = load_model(efficientnet_path, EfficientNetV2L, device)
            efficientnet_results = evaluate_model(efficientnet, "EfficientNet-V2-L", device, val_loader)
            logger.info("✅ EfficientNet-V2-L evaluation completed successfully")
        except Exception as e:
            logger.error(f"❌ EfficientNet-V2-L evaluation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    else:
        logger.warning("EfficientNet-V2-L model not found")
    
    # ConvNeXt-Base evaluation removed - only using EfficientNet
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("EVALUATION COMPLETED")
    logger.info("="*60)
    logger.info("Check the logs above for detailed results.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation failed with error: {e}")
        raise
