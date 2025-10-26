#!/usr/bin/env python3
"""
Test script to verify Hugging Face dataset loading works correctly.
"""

import sys
import os
from pathlib import Path

# Add training directory to path
sys.path.append(str(Path(__file__).parent / "training"))

from dataset_utils import create_huggingface_data_loaders
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dataset_loading():
    """Test the Hugging Face dataset loading."""
    logger.info("Testing Hugging Face dataset loading...")
    
    try:
        # Create data loaders
        train_loader, val_loader = create_huggingface_data_loaders(
            batch_size=2,
            num_workers=0,
            image_size=(224, 224),
            streaming=True
        )
        
        logger.info("✅ Data loaders created successfully")
        logger.info(f"Train loader: {len(train_loader)} batches")
        logger.info(f"Val loader: {len(val_loader)} batches")
        
        # Test loading a few batches
        logger.info("\nTesting batch loading...")
        
        for i, batch in enumerate(train_loader):
            if i >= 3:  # Test only first 3 batches
                break
                
            frames = batch['frames']
            labels = batch['label']
            video_ids = batch['video_id']
            
            logger.info(f"Batch {i+1}:")
            logger.info(f"  Frames shape: {frames.shape}")
            logger.info(f"  Labels: {labels}")
            logger.info(f"  Video IDs: {video_ids}")
            logger.info(f"  Label distribution: {labels.sum().item()}/{len(labels)} AI-generated")
        
        logger.info("✅ Dataset loading test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dataset loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dataset_loading()
    sys.exit(0 if success else 1)
