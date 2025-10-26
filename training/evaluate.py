"""
Evaluation script for DeepAction classification models.
Computes metrics and generates confusion matrix.
"""

import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from tqdm import tqdm

from dataset_utils import create_data_loaders, create_huggingface_data_loaders

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EfficientNetV2L(nn.Module):
    """EfficientNet-V2-L model for video classification."""
    
    def __init__(self, num_classes=1, pretrained=False):
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
    
    def __init__(self, num_classes=1, pretrained=False):
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


class TwoStageEvaluator:
    """Two-stage evaluation with confidence-based routing."""
    
    def __init__(self, efficientnet_path, convnext_path, device, confidence_threshold=0.2):
        self.device = device
        self.confidence_threshold = confidence_threshold
        
        # Load models
        logger.info("Loading trained models...")
        self.efficientnet = self._load_model(EfficientNetV2L, efficientnet_path)
        self.convnext = self._load_model(ConvNeXtV2Base, convnext_path)
        
        logger.info("Models loaded successfully!")
    
    def _load_model(self, model_class, checkpoint_path):
        """Load a trained model from checkpoint."""
        model = model_class(pretrained=False)
        
        if Path(checkpoint_path).exists():
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            model.load_state_dict(checkpoint['model_state_dict'])
            logger.info(f"Loaded model from {checkpoint_path}")
        else:
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
        
        model.to(self.device)
        model.eval()
        return model
    
    def predict_single(self, frames):
        """Predict on a single video using two-stage pipeline."""
        frames = frames.unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            # Stage 1: EfficientNet
            p1 = self.efficientnet(frames).cpu().item()
            c1 = abs(p1 - 0.5) * 2  # Confidence calculation
            
            if c1 >= self.confidence_threshold:
                # Use EfficientNet result
                final_prob = p1
                final_conf = c1
                stage_used = "EfficientNet"
            else:
                # Use ConvNeXt result
                p2 = self.convnext(frames).cpu().item()
                c2 = abs(p2 - 0.5) * 2
                final_prob = p2
                final_conf = c2
                stage_used = "ConvNeXt"
        
        final_label = 1 if final_prob > 0.5 else 0
        
        return {
            'stage1_probability': p1,
            'stage1_confidence': c1,
            'stage2_probability': p2 if stage_used == "ConvNeXt" else None,
            'stage2_confidence': c2 if stage_used == "ConvNeXt" else None,
            'final_probability': final_prob,
            'final_confidence': final_conf,
            'final_label': final_label,
            'stage_used': stage_used
        }
    
    def evaluate_dataset(self, data_loader):
        """Evaluate on entire dataset."""
        results = []
        all_true_labels = []
        all_pred_labels = []
        all_confidences = []
        stage_usage = {"EfficientNet": 0, "ConvNeXt": 0}
        
        logger.info("Starting evaluation...")
        
        for batch in tqdm(data_loader, desc="Evaluating"):
            frames_batch = batch['frames']
            labels_batch = batch['label']
            video_paths = batch['video_path']
            
            for i in range(frames_batch.shape[0]):
                frames = frames_batch[i]
                true_label = labels_batch[i].item()
                video_path = video_paths[i]
                
                prediction = self.predict_single(frames)
                prediction['video_path'] = video_path
                prediction['true_label'] = true_label
                
                results.append(prediction)
                
                # Collect metrics
                all_true_labels.append(true_label)
                all_pred_labels.append(prediction['final_label'])
                all_confidences.append(prediction['final_confidence'])
                stage_usage[prediction['stage_used']] += 1
        
        # Calculate metrics
        metrics = self._calculate_metrics(all_true_labels, all_pred_labels, all_confidences, stage_usage)
        
        logger.info(f"Evaluation completed on {len(results)} samples")
        logger.info(f"Stage usage: EfficientNet={stage_usage['EfficientNet']}, ConvNeXt={stage_usage['ConvNeXt']}")
        
        return results, metrics
    
    def _calculate_metrics(self, true_labels, pred_labels, confidences, stage_usage):
        """Calculate evaluation metrics."""
        accuracy = accuracy_score(true_labels, pred_labels)
        precision = precision_score(true_labels, pred_labels, average='binary', zero_division=0)
        recall = recall_score(true_labels, pred_labels, average='binary', zero_division=0)
        f1 = f1_score(true_labels, pred_labels, average='binary', zero_division=0)
        
        cm = confusion_matrix(true_labels, pred_labels)
        
        avg_confidence = np.mean(confidences)
        std_confidence = np.std(confidences)
        
        total_samples = len(true_labels)
        efficientnet_pct = (stage_usage['EfficientNet'] / total_samples) * 100
        convnext_pct = (stage_usage['ConvNeXt'] / total_samples) * 100
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm,
            'avg_confidence': avg_confidence,
            'std_confidence': std_confidence,
            'stage_usage': {
                'EfficientNet': stage_usage['EfficientNet'],
                'ConvNeXt': stage_usage['ConvNeXt'],
                'EfficientNet_percentage': efficientnet_pct,
                'ConvNeXt_percentage': convnext_pct
            },
            'total_samples': total_samples
        }
    
    def save_results(self, results, metrics):
        """Save evaluation results."""
        # Save CSV results
        csv_data = []
        for result in results:
            csv_data.append({
                'video_path': result['video_path'],
                'true_label': result['true_label'],
                'pred_label': result['final_label'],
                'confidence': result['final_confidence'],
                'stage_used': result['stage_used'],
                'stage1_probability': result['stage1_probability'],
                'stage1_confidence': result['stage1_confidence'],
                'stage2_probability': result.get('stage2_probability'),
                'stage2_confidence': result.get('stage2_confidence'),
                'final_probability': result['final_probability']
            })
        
        df = pd.DataFrame(csv_data)
        df.to_csv('results.csv', index=False)
        logger.info("Results saved to results.csv")
        
        # Save metrics summary
        with open('metrics_summary.txt', 'w') as f:
            f.write("DeepAction Classification Results\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total Samples: {metrics['total_samples']}\n")
            f.write(f"Accuracy: {metrics['accuracy']:.4f}\n")
            f.write(f"Precision: {metrics['precision']:.4f}\n")
            f.write(f"Recall: {metrics['recall']:.4f}\n")
            f.write(f"F1 Score: {metrics['f1_score']:.4f}\n")
            f.write(f"Average Confidence: {metrics['avg_confidence']:.4f}\n")
            f.write(f"Confidence Std: {metrics['std_confidence']:.4f}\n\n")
            f.write("Stage Usage:\n")
            f.write(f"  EfficientNet: {metrics['stage_usage']['EfficientNet']} ({metrics['stage_usage']['EfficientNet_percentage']:.1f}%)\n")
            f.write(f"  ConvNeXt: {metrics['stage_usage']['ConvNeXt']} ({metrics['stage_usage']['ConvNeXt_percentage']:.1f}%)\n\n")
            f.write("Confusion Matrix:\n")
            f.write(f"  [[{metrics['confusion_matrix'][0][0]}, {metrics['confusion_matrix'][0][1]}],\n")
            f.write(f"   [{metrics['confusion_matrix'][1][0]}, {metrics['confusion_matrix'][1][1]}]]\n")
        
        logger.info("Metrics summary saved to metrics_summary.txt")
        
        # Create confusion matrix plot
        self._plot_confusion_matrix(metrics['confusion_matrix'])
    
    def _plot_confusion_matrix(self, cm):
        """Create and save confusion matrix plot."""
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['Real', 'AI-generated'],
                    yticklabels=['Real', 'AI-generated'])
        plt.title('Confusion Matrix - DeepAction Classification')
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Confusion matrix plot saved to confusion_matrix.png")


def main():
    """Main evaluation function."""
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
    
    # Check if models exist
    efficientnet_path = "./models/efficientnetv2l.pth"
    convnext_path = "./models/convnextv2base.pth"
    
    if not Path(efficientnet_path).exists() or not Path(convnext_path).exists():
        logger.error("Trained models not found!")
        logger.error("Please run train.py first to train the models")
        return
    
    # Create data loaders
    logger.info("Loading test dataset...")
    try:
        # Try Hugging Face dataset first
        train_loader, val_loader = create_huggingface_data_loaders(
            batch_size=4,
            num_workers=0,
            image_size=(224, 224),
            streaming=True
        )
        logger.info("✅ Using Hugging Face dataset")
    except Exception as e:
        logger.warning(f"Error loading Hugging Face dataset: {e}")
        logger.info("Falling back to local dataset...")
        try:
            train_loader, val_loader = create_data_loaders(
                batch_size=4,
                num_workers=2,
                image_size=(224, 224)
            )
        except Exception as e2:
            logger.error(f"Error loading local dataset: {e2}")
            return
    
    # Initialize evaluator
    evaluator = TwoStageEvaluator(
        efficientnet_path=efficientnet_path,
        convnext_path=convnext_path,
        device=device,
        confidence_threshold=0.2
    )
    
    # Run evaluation
    logger.info("Starting two-stage evaluation...")
    results, metrics = evaluator.evaluate_dataset(val_loader)
    
    # Print results
    logger.info("\n" + "="*60)
    logger.info("EVALUATION RESULTS")
    logger.info("="*60)
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall: {metrics['recall']:.4f}")
    logger.info(f"F1 Score: {metrics['f1_score']:.4f}")
    logger.info(f"Average Confidence: {metrics['avg_confidence']:.4f}")
    logger.info(f"Stage Usage - EfficientNet: {metrics['stage_usage']['EfficientNet_percentage']:.1f}%")
    logger.info(f"Stage Usage - ConvNeXt: {metrics['stage_usage']['ConvNeXt_percentage']:.1f}%")
    
    # Save results
    evaluator.save_results(results, metrics)
    
    logger.info("\nEvaluation completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation failed with error: {e}")
        raise
