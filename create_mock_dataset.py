# -*- coding: utf-8 -*-
"""
Mock Dataset Creator - creates a small test dataset for training verification.

This creates a small dataset with synthetic videos to test the training pipeline
without needing the actual DeepAction dataset.
"""

import os
import argparse
import logging
from pathlib import Path
import numpy as np
from tqdm import tqdm
from PIL import Image
import torch
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
from typing import Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_videos(output_dir: str, num_videos: int = 50):
    """
    Create mock video frames for testing.
    
    Args:
        output_dir: Directory to save mock frames
        num_videos: Number of mock videos to create
    """
    output_path = Path(output_dir)
    
    # Create output directories
    (output_path / "train" / "ai").mkdir(parents=True, exist_ok=True)
    (output_path / "train" / "real").mkdir(parents=True, exist_ok=True)
    (output_path / "val" / "ai").mkdir(parents=True, exist_ok=True)
    (output_path / "val" / "real").mkdir(parents=True, exist_ok=True)
    
    # Create mock videos
    for i in tqdm(range(num_videos), desc="Creating mock videos"):
        # Determine split and label
        split = "train" if i < num_videos * 0.8 else "val"
        label = "ai" if i % 2 == 0 else "real"
        
        # Create video directory
        video_dir = output_path / split / label / f"video_{i:04d}"
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Create 3-5 frames per video
        num_frames = np.random.randint(3, 6)
        
        for frame_idx in range(num_frames):
            # Create a random image
            if label == "ai":
                # AI-generated looking image (more structured patterns)
                img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
                # Add some structured patterns
                img_array[50:150, 50:150] = [255, 0, 0]  # Red square
                img_array[100:200, 100:200] = [0, 255, 0]  # Green square
            else:
                # Real-looking image (more natural noise)
                img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
                # Add some natural-looking patterns
                img_array[75:175, 75:175] = np.random.randint(100, 200, (100, 100, 3), dtype=np.uint8)
            
            # Save frame
            pil_image = Image.fromarray(img_array)
            frame_path = video_dir / f"{frame_idx:03d}.jpg"
            pil_image.save(frame_path, "JPEG", quality=95)
    
    logger.info(f"✅ Created {num_videos} mock videos")
    logger.info(f"Frames saved to: {output_dir}")


class FrameDataset(Dataset):
    """PyTorch dataset for loading pre-extracted frames."""
    
    def __init__(self, data_dir: str, split: str = "train", 
                 transform: transforms.Compose = None):
        """
        Initialize dataset.
        
        Args:
            data_dir: Path to data_frames directory
            split: Dataset split ("train" or "val")
            transform: Image transforms
        """
        self.data_dir = Path(data_dir) / split
        self.split = split
        
        # Default transforms
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transform
        
        # Collect all video directories
        self.video_dirs = []
        self.labels = []
        
        for label in ["ai", "real"]:
            label_dir = self.data_dir / label
            if label_dir.exists():
                for video_dir in label_dir.iterdir():
                    if video_dir.is_dir():
                        self.video_dirs.append(video_dir)
                        self.labels.append(1 if label == "ai" else 0)
        
        logger.info(f"Loaded {len(self.video_dirs)} videos for {split} split")
        logger.info(f"  - AI videos: {sum(self.labels)}")
        logger.info(f"  - Real videos: {len(self.labels) - sum(self.labels)}")
    
    def __len__(self):
        return len(self.video_dirs)
    
    def __getitem__(self, idx):
        """Get a single video sample."""
        video_dir = self.video_dirs[idx]
        label = self.labels[idx]
        
        # Load all frames for this video
        frame_files = sorted(video_dir.glob("*.jpg"))
        frames = []
        
        for frame_file in frame_files:
            image = Image.open(frame_file).convert('RGB')
            tensor = self.transform(image)
            frames.append(tensor)
        
        # Stack frames: (T, C, H, W)
        frames_tensor = torch.stack(frames)
        
        return {
            'frames': frames_tensor,
            'label': torch.tensor(label, dtype=torch.float32),
            'video_id': video_dir.name
        }


def create_data_loaders(data_dir: str = "./data_frames",
                       batch_size: int = 8,
                       num_workers: int = 2) -> Tuple[DataLoader, DataLoader]:
    """Create train and validation data loaders."""
    
    # Create datasets
    train_dataset = FrameDataset(data_dir, split="train")
    val_dataset = FrameDataset(data_dir, split="val")
    
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


def main():
    """CLI runner for mock dataset creation."""
    parser = argparse.ArgumentParser(description="Create mock dataset for testing")
    parser.add_argument("--output", type=str, default="./data_frames",
                       help="Output directory for mock frames")
    parser.add_argument("--num_videos", type=int, default=50,
                       help="Number of mock videos to create")
    
    args = parser.parse_args()
    
    # Create mock dataset
    create_mock_videos(args.output, args.num_videos)
    
    logger.info("✅ Mock dataset creation completed!")
    logger.info(f"Mock frames saved to: {args.output}")


if __name__ == "__main__":
    main()

