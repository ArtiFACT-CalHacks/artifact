# -*- coding: utf-8 -*-
"""
Kaggle Dataset Frame Extraction - extracts 5 frames from every video.

This module downloads the RealAI video dataset from Kaggle and extracts 
exactly 5 frames from each video for binary classification training.
"""

import os
import argparse
import logging
from pathlib import Path
from typing import Tuple, List
import numpy as np
from tqdm import tqdm
import imageio.v3 as iio
from PIL import Image
import torch
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
import kagglehub
import ssl

# Fix SSL certificate verification for downloads
ssl._create_default_https_context = ssl._create_unverified_context

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_kaggle_dataset() -> str:
    """
    Download the RealAI video dataset from Kaggle.
    
    Returns:
        Path to the downloaded dataset
    """
    logger.info("Downloading RealAI video dataset from Kaggle...")
    
    try:
        # Download the dataset
        path = kagglehub.dataset_download("kanzeus/realai-video-dataset")
        logger.info(f"✅ Dataset downloaded successfully to {path}")
        return path
    except Exception as e:
        logger.error(f"❌ Failed to download dataset: {e}")
        raise


def extract_frames_from_video(video_path: str, output_dir: str, 
                             video_name: str, label: str) -> bool:
    """
    Extract exactly 5 frames from a single video.
    
    Args:
        video_path: Path to the input video file
        output_dir: Base output directory
        video_name: Name of the video (without extension)
        label: Label for the video ("ai" or "real")
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory for this video
        video_output_dir = Path(output_dir) / label / video_name
        video_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if already processed (should have exactly 5 frames)
        existing_frames = list(video_output_dir.glob("*.jpg"))
        if len(existing_frames) >= 5:
            logger.debug(f"Skipping {video_name} - already processed")
            return True
        
        # Read video frames
        frames = iio.imread(video_path, plugin="FFMPEG")
        
        # Handle different video formats
        if len(frames.shape) == 4:  # (T, H, W, C)
            total_frames = frames.shape[0]
        else:
            logger.warning(f"Unexpected video format for {video_path}")
            return False
        
        # Always extract exactly 5 frames
        frames_to_extract = 5
        
        # Sample frames evenly across the video
        if total_frames <= frames_to_extract:
            # If video has <= 5 frames, repeat the last frame to get exactly 5
            frame_indices = list(range(total_frames))
            while len(frame_indices) < frames_to_extract:
                frame_indices.append(frame_indices[-1] if frame_indices else 0)
        else:
            # If video has > 5 frames, sample exactly 5 evenly spaced frames
            frame_indices = np.linspace(0, total_frames - 1, frames_to_extract)
            frame_indices = np.round(frame_indices).astype(int)
        
        # Save frames
        for i, frame_idx in enumerate(frame_indices):
            frame = frames[frame_idx]
            
            # Convert to PIL Image and save
            pil_image = Image.fromarray(frame)
            output_path = video_output_dir / f"{i:03d}.jpg"
            pil_image.save(output_path, "JPEG", quality=95)
        
        logger.debug(f"Extracted {len(frame_indices)} frames from {video_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {video_path}: {e}")
        return False


def process_kaggle_dataset(input_dir: str, output_dir: str):
    """
    Process the Kaggle RealAI dataset and extract exactly 5 frames from each video.
    
    Args:
        input_dir: Path to the downloaded Kaggle dataset
        output_dir: Path to save extracted frames
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directories
    (output_path / "train" / "ai").mkdir(parents=True, exist_ok=True)
    (output_path / "train" / "real").mkdir(parents=True, exist_ok=True)
    (output_path / "val" / "ai").mkdir(parents=True, exist_ok=True)
    (output_path / "val" / "real").mkdir(parents=True, exist_ok=True)
    
    # Find all video files in the dataset
    all_videos = list(input_path.glob("**/*.mp4"))
    logger.info(f"Found {len(all_videos)} total videos in dataset")
    
    # Separate AI and real videos based on folder structure
    ai_videos = []
    real_videos = []
    
    for video_path in all_videos:
        # Check if video is in AI folder (look for "/ai/" in path)
        if "/ai/" in str(video_path):
            ai_videos.append(video_path)
        elif "/real/" in str(video_path):
            real_videos.append(video_path)
    
    logger.info(f"Found {len(ai_videos)} AI videos and {len(real_videos)} real videos")
    
    # Split videos 70/30 for train/val
    ai_train_count = int(len(ai_videos) * 0.7)
    real_train_count = int(len(real_videos) * 0.7)
    
    ai_train_videos = ai_videos[:ai_train_count]
    ai_val_videos = ai_videos[ai_train_count:]
    real_train_videos = real_videos[:real_train_count]
    real_val_videos = real_videos[real_train_count:]
    
    # Process each split
    for split, videos, label in [
        ("train", ai_train_videos, "ai"),
        ("val", ai_val_videos, "ai"),
        ("train", real_train_videos, "real"),
        ("val", real_val_videos, "real")
    ]:
        logger.info(f"Processing {split}/{label} videos...")
        
        for video_path in tqdm(videos, desc=f"Processing {split}/{label}"):
            video_name = video_path.stem
            success = extract_frames_from_video(
                str(video_path),
                str(output_path / split),
                video_name,
                label
            )
            
            if not success:
                logger.warning(f"Failed to process {video_path}")


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
        
        # Should have exactly 5 frames from extraction
        assert len(frames) == 5, f"Expected 5 frames, got {len(frames)} for {video_dir.name}"
        
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
    """CLI runner for Kaggle dataset frame extraction."""
    parser = argparse.ArgumentParser(description="Extract frames from Kaggle RealAI dataset")
    parser.add_argument("--output", type=str, default="./data_frames",
                       help="Output directory for extracted frames")
    parser.add_argument("--download", action="store_true", default=True,
                       help="Download dataset from Kaggle")
    
    args = parser.parse_args()
    
    if args.download:
        # Use local data directory instead of downloading from Kaggle
        data_dir = "./data"
        logger.info(f"Using local videos from: {data_dir}")
    else:
        logger.error("Please use --download flag to process local dataset")
        return
    
    # Process dataset
    process_kaggle_dataset(data_dir, args.output)
    
    logger.info("✅ Frame extraction completed!")
    logger.info(f"Frames saved to: {args.output}")
    logger.info("Each video now has exactly 5 frames extracted")


if __name__ == "__main__":
    main()