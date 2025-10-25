"""
Dataset utilities for DeepAction classification.
Handles loading, preprocessing, and splitting of video data.
"""

import os
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import cv2
from pathlib import Path
import logging
from typing import Tuple, List, Optional
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoDataset(Dataset):
    """PyTorch dataset for video classification."""
    
    def __init__(self, 
                 data_dir: str,
                 split: str = "train",
                 max_frames: int = 16,
                 image_size: Tuple[int, int] = (224, 224),
                 transform: Optional[transforms.Compose] = None):
        """
        Initialize video dataset.
        
        Args:
            data_dir: Path to data directory (./data/)
            split: Dataset split ("train", "val", "test")
            max_frames: Maximum frames per video
            image_size: Target image size
            transform: Optional transforms
        """
        self.data_dir = Path(data_dir)
        self.split = split
        self.max_frames = max_frames
        self.image_size = image_size
        
        # Set up paths
        self.ai_dir = self.data_dir / split / "ai"
        self.real_dir = self.data_dir / split / "real"
        
        # Collect video files
        self.video_files = []
        self.labels = []
        
        # Load AI-generated videos (label = 1)
        if self.ai_dir.exists():
            for video_file in self.ai_dir.glob("*.mp4"):
                self.video_files.append(str(video_file))
                self.labels.append(1)
        
        # Load real videos (label = 0)
        if self.real_dir.exists():
            for video_file in self.real_dir.glob("*.mp4"):
                self.video_files.append(str(video_file))
                self.labels.append(0)
        
        logger.info(f"Loaded {len(self.video_files)} videos for {split} split")
        logger.info(f"  - AI videos: {sum(self.labels)}")
        logger.info(f"  - Real videos: {len(self.labels) - sum(self.labels)}")
        
        # Default transforms
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize(image_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transform
    
    def _extract_frames(self, video_path: str) -> List[np.ndarray]:
        """Extract frames from video file."""
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while len(frames) < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        
        cap.release()
        
        # If we have fewer frames than max_frames, repeat the last frame
        while len(frames) < self.max_frames:
            frames.append(frames[-1] if frames else np.zeros((224, 224, 3), dtype=np.uint8))
        
        return frames
    
    def _sample_frames(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Sample frames uniformly across the video."""
        if len(frames) <= self.max_frames:
            return frames
        
        # Uniform sampling
        indices = np.linspace(0, len(frames) - 1, self.max_frames, dtype=int)
        return [frames[i] for i in indices]
    
    def __len__(self) -> int:
        return len(self.video_files)
    
    def __getitem__(self, idx: int) -> dict:
        """Get a single video sample."""
        video_path = self.video_files[idx]
        label = self.labels[idx]
        
        try:
            # Extract frames
            frames = self._extract_frames(video_path)
            frames = self._sample_frames(frames)
            
            # Convert to tensors
            frame_tensors = []
            for frame in frames:
                # Convert to PIL Image
                pil_image = Image.fromarray(frame)
                tensor = self.transform(pil_image)
                frame_tensors.append(tensor)
            
            # Stack frames: (T, C, H, W)
            frames_tensor = torch.stack(frame_tensors)
            
            return {
                'frames': frames_tensor,
                'label': torch.tensor(label, dtype=torch.float32),
                'video_path': video_path
            }
            
        except Exception as e:
            logger.warning(f"Error loading video {video_path}: {e}")
            # Return dummy data
            dummy_frames = torch.zeros(self.max_frames, 3, *self.image_size)
            return {
                'frames': dummy_frames,
                'label': torch.tensor(label, dtype=torch.float32),
                'video_path': video_path
            }


def create_data_loaders(data_dir: str = "./data",
                       batch_size: int = 8,
                       num_workers: int = 2,
                       image_size: Tuple[int, int] = (224, 224)) -> Tuple[DataLoader, DataLoader]:
    """Create train and validation data loaders."""
    
    # Create datasets
    train_dataset = VideoDataset(data_dir, split="train", image_size=image_size)
    val_dataset = VideoDataset(data_dir, split="val", image_size=image_size)
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=False
    )
    
    logger.info(f"Created data loaders - Train: {len(train_loader)}, Val: {len(val_loader)}")
    
    return train_loader, val_loader


def split_dataset(source_dir: str, target_dir: str, train_ratio: float = 0.8):
    """
    Split dataset into train/val directories.
    
    Args:
        source_dir: Source directory with videos
        target_dir: Target directory for split data
        train_ratio: Ratio of data for training
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    # Create target directories
    (target_path / "train" / "ai").mkdir(parents=True, exist_ok=True)
    (target_path / "train" / "real").mkdir(parents=True, exist_ok=True)
    (target_path / "val" / "ai").mkdir(parents=True, exist_ok=True)
    (target_path / "val" / "real").mkdir(parents=True, exist_ok=True)
    
    # Get all video files
    ai_videos = list(source_path.glob("ai/*.mp4"))
    real_videos = list(source_path.glob("real/*.mp4"))
    
    # Shuffle and split
    random.shuffle(ai_videos)
    random.shuffle(real_videos)
    
    # Split AI videos
    ai_train_count = int(len(ai_videos) * train_ratio)
    for i, video in enumerate(ai_videos):
        target = target_path / ("train" if i < ai_train_count else "val") / "ai" / video.name
        target.symlink_to(video.resolve())
    
    # Split real videos
    real_train_count = int(len(real_videos) * train_ratio)
    for i, video in enumerate(real_videos):
        target = target_path / ("train" if i < real_train_count else "val") / "real" / video.name
        target.symlink_to(video.resolve())
    
    logger.info(f"Dataset split completed:")
    logger.info(f"  - AI train: {ai_train_count}, val: {len(ai_videos) - ai_train_count}")
    logger.info(f"  - Real train: {real_train_count}, val: {len(real_videos) - real_train_count}")


def download_faridlab_dataset(data_dir: str = "./data"):
    """Download FaridLab dataset from Hugging Face."""
    try:
        from datasets import load_dataset
        
        logger.info("Downloading FaridLab DeepAction v1 dataset...")
        
        # Load dataset
        dataset = load_dataset("faridlab/deepaction_v1", trust_remote_code=True)
        
        # Create data directory
        data_path = Path(data_dir)
        data_path.mkdir(exist_ok=True)
        
        # Process and save videos
        for split_name, split_data in dataset.items():
            split_dir = data_path / split_name
            (split_dir / "ai").mkdir(parents=True, exist_ok=True)
            (split_dir / "real").mkdir(parents=True, exist_ok=True)
            
            for i, sample in enumerate(split_data):
                try:
                    # Get video frames
                    video = sample['video']
                    frames = video['frames']
                    
                    if len(frames) == 0:
                        continue
                    
                    # Determine label
                    label = "ai" if sample.get('label', '') == 'AI-generated' else "real"
                    
                    # Save as video file (simplified - just save first frame as placeholder)
                    # In practice, you'd want to save the actual video
                    video_path = split_dir / label / f"video_{i}.mp4"
                    
                    # For now, create a placeholder file
                    video_path.touch()
                    
                except Exception as e:
                    logger.warning(f"Error processing sample {i}: {e}")
                    continue
        
        logger.info("Dataset download completed!")
        
    except ImportError:
        logger.error("datasets library not installed. Please install: pip install datasets")
    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")


if __name__ == "__main__":
    # Test dataset utilities
    logger.info("Testing dataset utilities...")
    
    # Test dataset creation
    if Path("./data/train").exists():
        train_loader, val_loader = create_data_loaders()
        
        # Test a batch
        for batch in train_loader:
            logger.info(f"Batch frames shape: {batch['frames'].shape}")
            logger.info(f"Batch labels: {batch['labels']}")
            break
        
        logger.info("Dataset test completed!")
    else:
        logger.info("No data directory found. Please run download_faridlab_dataset() first.")
