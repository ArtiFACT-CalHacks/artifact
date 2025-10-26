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


class HuggingFaceVideoDataset(Dataset):
    """PyTorch dataset for Hugging Face DeepAction dataset."""
    
    def __init__(self, 
                 split: str = "train",
                 max_frames: int = 16,
                 image_size: Tuple[int, int] = (224, 224),
                 transform: Optional[transforms.Compose] = None,
                 streaming: bool = True):
        """
        Initialize Hugging Face video dataset.
        
        Args:
            split: Dataset split ("train", "validation", "test")
            max_frames: Maximum frames per video
            image_size: Target image size
            transform: Optional transforms
            streaming: Whether to use streaming mode
        """
        self.split = split
        self.max_frames = max_frames
        self.image_size = image_size
        self.streaming = streaming
        
        # Load dataset from Hugging Face
        logger.info(f"Loading DeepAction v1 dataset - {split} split (streaming={streaming})...")
        try:
            from datasets import load_dataset
            self.dataset = load_dataset("faridlab/deepaction_v1", streaming=streaming)
            if streaming:
                self.dataset_iter = iter(self.dataset[split])
                self.length = None  # Unknown length for streaming
            else:
                self.dataset_iter = None
                self.length = len(self.dataset[split])
            logger.info(f"Dataset loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
        
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
    
    def _process_frames(self, frames: List) -> torch.Tensor:
        """Process video frames into tensor."""
        if len(frames) == 0:
            # Return dummy frames if no frames available
            dummy_frames = torch.zeros(self.max_frames, 3, *self.image_size)
            return dummy_frames
        
        # Sample frames uniformly
        if len(frames) <= self.max_frames:
            sampled_frames = frames
        else:
            indices = np.linspace(0, len(frames) - 1, self.max_frames, dtype=int)
            sampled_frames = [frames[i] for i in indices]
        
        # Convert frames to tensors
        frame_tensors = []
        for frame in sampled_frames:
            try:
                # Handle different frame formats
                if isinstance(frame, np.ndarray):
                    if frame.dtype == np.uint8:
                        pil_image = Image.fromarray(frame)
                    else:
                        pil_image = Image.fromarray((frame * 255).astype(np.uint8))
                elif hasattr(frame, 'convert'):
                    pil_image = frame.convert('RGB')
                else:
                    # Fallback
                    pil_image = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
                
                tensor = self.transform(pil_image)
                frame_tensors.append(tensor)
            except Exception as e:
                logger.warning(f"Error processing frame: {e}")
                # Use dummy frame
                dummy_tensor = torch.zeros(3, *self.image_size)
                frame_tensors.append(dummy_tensor)
        
        # Pad with dummy frames if needed
        while len(frame_tensors) < self.max_frames:
            frame_tensors.append(torch.zeros(3, *self.image_size))
        
        # Stack frames: (T, C, H, W)
        return torch.stack(frame_tensors)
    
    def __len__(self) -> int:
        if self.length is not None:
            return self.length
        else:
            # For streaming, return a large number
            return 10000  # Approximate
    
    def __getitem__(self, idx: int) -> dict:
        """Get a single video sample."""
        try:
            if self.streaming:
                # Get next sample from iterator
                sample = next(self.dataset_iter)
            else:
                # Get sample by index
                sample = self.dataset[self.split][idx]
            
            # Extract video frames
            video = sample['video']
            frames = video['frames'] if 'frames' in video else []
            
            # Get label: 0 for "real", 1 for "AI-generated"
            label = 1 if sample.get('label', '') == 'AI-generated' else 0
            
            # Process frames
            frames_tensor = self._process_frames(frames)
            
            return {
                'frames': frames_tensor,
                'label': torch.tensor(label, dtype=torch.float32),
                'video_id': sample.get('video_id', f'video_{idx}')
            }
            
        except StopIteration:
            # End of streaming dataset
            raise IndexError("End of dataset reached")
        except Exception as e:
            logger.warning(f"Error loading sample {idx}: {e}")
            # Return dummy data
            dummy_frames = torch.zeros(self.max_frames, 3, *self.image_size)
            return {
                'frames': dummy_frames,
                'label': torch.tensor(0, dtype=torch.float32),
                'video_id': f'dummy_{idx}'
            }


def create_huggingface_data_loaders(batch_size: int = 8,
                                   num_workers: int = 2,
                                   image_size: Tuple[int, int] = (224, 224),
                                   streaming: bool = True) -> Tuple[DataLoader, DataLoader]:
    """Create data loaders for Hugging Face dataset."""
    
    # Create datasets
    train_dataset = HuggingFaceVideoDataset(split="train", image_size=image_size, streaming=streaming)
    val_dataset = HuggingFaceVideoDataset(split="validation", image_size=image_size, streaming=streaming)
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=not streaming,  # Don't shuffle streaming data
        num_workers=0 if streaming else num_workers,  # No multiprocessing for streaming
        pin_memory=True,
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0 if streaming else num_workers,
        pin_memory=True,
        drop_last=False
    )
    
    logger.info(f"Created HuggingFace data loaders - Train: {len(train_loader)}, Val: {len(val_loader)}")
    
    return train_loader, val_loader


def download_faridlab_dataset(data_dir: str = "./data"):
    """Download FaridLab dataset from Hugging Face (legacy function)."""
    logger.info("Note: Using streaming dataset instead of downloading. Use create_huggingface_data_loaders() instead.")
    return create_huggingface_data_loaders()


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
