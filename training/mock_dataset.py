"""
Mock dataset for testing when Hugging Face dataset is not available.
Creates synthetic video data for training and testing.
"""

import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import logging
from typing import Tuple, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockVideoDataset(Dataset):
    """Mock dataset that generates synthetic video data for testing."""
    
    def __init__(self, 
                 num_samples: int = 1000,
                 max_frames: int = 16,
                 image_size: Tuple[int, int] = (224, 224),
                 transform: Optional[transforms.Compose] = None):
        """
        Initialize mock video dataset.
        
        Args:
            num_samples: Number of synthetic samples to generate
            max_frames: Maximum frames per video
            image_size: Target image size
            transform: Optional transforms
        """
        self.num_samples = num_samples
        self.max_frames = max_frames
        self.image_size = image_size
        
        # Generate synthetic data
        self.samples = []
        for i in range(num_samples):
            # Randomly assign labels (0 for real, 1 for AI-generated)
            label = np.random.randint(0, 2)
            self.samples.append({
                'video_id': f'mock_video_{i}',
                'label': label,
                'num_frames': np.random.randint(8, max_frames + 1)
            })
        
        logger.info(f"Created mock dataset with {num_samples} samples")
        logger.info(f"  - AI videos: {sum(s['label'] for s in self.samples)}")
        logger.info(f"  - Real videos: {num_samples - sum(s['label'] for s in self.samples)}")
        
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
    
    def _generate_synthetic_frames(self, num_frames: int, label: int) -> List[np.ndarray]:
        """Generate synthetic video frames."""
        frames = []
        
        for i in range(num_frames):
            # Create synthetic frame based on label
            if label == 1:  # AI-generated - more artificial patterns
                # Create more structured, artificial-looking patterns
                frame = np.random.rand(*self.image_size, 3) * 255
                # Add some artificial patterns
                if i % 3 == 0:
                    frame[50:100, 50:100] = [255, 0, 0]  # Red square
                if i % 5 == 0:
                    frame[150:200, 150:200] = [0, 255, 0]  # Green square
            else:  # Real - more natural patterns
                # Create more natural-looking patterns
                frame = np.random.rand(*self.image_size, 3) * 200 + 50
                # Add some natural variations
                noise = np.random.normal(0, 20, frame.shape)
                frame = np.clip(frame + noise, 0, 255)
            
            frames.append(frame.astype(np.uint8))
        
        return frames
    
    def __len__(self) -> int:
        return self.num_samples
    
    def __getitem__(self, idx: int) -> dict:
        """Get a single video sample."""
        sample = self.samples[idx]
        video_id = sample['video_id']
        label = sample['label']
        num_frames = sample['num_frames']
        
        # Generate synthetic frames
        frames = self._generate_synthetic_frames(num_frames, label)
        
        # Convert to tensors
        frame_tensors = []
        for frame in frames:
            try:
                # Convert to PIL Image
                pil_image = Image.fromarray(frame)
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
        frames_tensor = torch.stack(frame_tensors)
        
        return {
            'frames': frames_tensor,
            'label': torch.tensor(label, dtype=torch.float32),
            'video_id': video_id
        }


def create_mock_data_loaders(batch_size: int = 8,
                            num_workers: int = 2,
                            image_size: Tuple[int, int] = (224, 224),
                            train_samples: int = 800,
                            val_samples: int = 200) -> Tuple[DataLoader, DataLoader]:
    """Create mock data loaders for testing."""
    
    # Create datasets
    train_dataset = MockVideoDataset(
        num_samples=train_samples,
        image_size=image_size
    )
    val_dataset = MockVideoDataset(
        num_samples=val_samples,
        image_size=image_size
    )
    
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
    
    logger.info(f"Created mock data loaders - Train: {len(train_loader)}, Val: {len(val_loader)}")
    
    return train_loader, val_loader


if __name__ == "__main__":
    # Test mock dataset
    logger.info("Testing mock dataset...")
    
    train_loader, val_loader = create_mock_data_loaders(batch_size=4)
    
    # Test a batch
    for batch in train_loader:
        logger.info(f"Batch frames shape: {batch['frames'].shape}")
        logger.info(f"Batch labels: {batch['label']}")
        logger.info(f"Batch video IDs: {batch['video_id']}")
        break
    
    logger.info("Mock dataset test completed!")
