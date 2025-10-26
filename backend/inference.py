import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import logging
from pathlib import Path
import imageio.v3 as iio

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, model_loader):
        self.model_loader = model_loader
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                              std=[0.229, 0.224, 0.225])
        ])
    
    def predict(self, file_path):
        """Run inference on uploaded file"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                return self._predict_video(file_path)
            else:
                return self._predict_image(file_path)
                
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {
                'is_ai': None,
                'confidence': None,
                'success': False,
                'error': str(e)
            }
    
    def _predict_image(self, image_path):
        """Predict on single image"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            tensor = self.transform(image)
            
            # Add batch and frame dimensions: (1, 1, C, H, W)
            tensor = tensor.unsqueeze(0).unsqueeze(0)
            
            # Run inference
            model = self.model_loader.get_model()
            device = self.model_loader.get_device()
            
            with torch.no_grad():
                tensor = tensor.to(device)
                outputs = model(tensor)
                probabilities = torch.softmax(outputs, dim=1)
                
                # Get prediction
                confidence, predicted = torch.max(probabilities, 1)
                is_ai = predicted.item() == 1
                confidence_score = confidence.item()
            
            logger.info(f"Image prediction: is_ai={is_ai}, confidence={confidence_score:.3f}")
            return {
                'is_ai': is_ai,
                'confidence': confidence_score,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Image prediction error: {e}")
            return {
                'is_ai': None,
                'confidence': None,
                'success': False,
                'error': str(e)
            }
    
    def _predict_video(self, video_path):
        """Predict on video by extracting frames"""
        try:
            # Extract frames (reuse your existing logic)
            frames = self._extract_frames(video_path)
            
            if len(frames) == 0:
                return {
                    'is_ai': None,
                    'confidence': None,
                    'success': False,
                    'error': 'No frames extracted from video'
                }
            
            # Preprocess frames
            frame_tensors = []
            for frame in frames:
                pil_image = Image.fromarray(frame).convert('RGB')
                tensor = self.transform(pil_image)
                frame_tensors.append(tensor)
            
            # Stack frames: (num_frames, C, H, W)
            frames_tensor = torch.stack(frame_tensors)
            
            # Add batch dimension: (1, num_frames, C, H, W)
            frames_tensor = frames_tensor.unsqueeze(0)
            
            # Run inference
            model = self.model_loader.get_model()
            device = self.model_loader.get_device()
            
            with torch.no_grad():
                frames_tensor = frames_tensor.to(device)
                outputs = model(frames_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                
                # Get prediction
                confidence, predicted = torch.max(probabilities, 1)
                is_ai = predicted.item() == 1
                confidence_score = confidence.item()
            
            return {
                'is_ai': is_ai,
                'confidence': confidence_score,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Video prediction error: {e}")
            return {
                'is_ai': None,
                'confidence': None,
                'success': False,
                'error': str(e)
            }
    
    def _extract_frames(self, video_path, num_frames=5):
        """Extract frames from video using your existing logic"""
        try:
            frames = iio.imread(video_path, plugin="FFMPEG")
            
            if len(frames.shape) == 4:  # (T, H, W, C)
                total_frames = frames.shape[0]
            else:
                return []
            
            # Sample frames evenly (reuse your fixed logic)
            if total_frames <= num_frames:
                frame_indices = list(range(total_frames))
                while len(frame_indices) < num_frames:
                    frame_indices.append(frame_indices[-1] if frame_indices else 0)
            else:
                frame_indices = np.linspace(0, total_frames - 1, num_frames)
                frame_indices = np.round(frame_indices).astype(int)
            
            # Extract frames
            extracted_frames = []
            for frame_idx in frame_indices:
                extracted_frames.append(frames[frame_idx])
            
            return extracted_frames
            
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
            return []
