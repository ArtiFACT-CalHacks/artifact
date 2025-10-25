"""
Frame extractor utility for FaridLab videos.
Extracts frames from video files and saves them as images.
"""

import cv2
import os
from pathlib import Path
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_frames_from_video(video_path, output_dir, max_frames=16, frame_size=(224, 224)):
    """
    Extract frames from a single video file.
    
    Args:
        video_path: Path to input video file
        output_dir: Directory to save extracted frames
        max_frames: Maximum number of frames to extract
        frame_size: Target frame size (width, height)
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return False
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    logger.info(f"Processing {video_path.name}: {total_frames} frames at {fps:.2f} FPS")
    
    # Calculate frame sampling interval
    if total_frames <= max_frames:
        frame_indices = list(range(total_frames))
    else:
        frame_indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
    
    # Extract frames
    extracted_count = 0
    for i, frame_idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            logger.warning(f"Could not read frame {frame_idx}")
            continue
        
        # Resize frame
        frame = cv2.resize(frame, frame_size)
        
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Save frame
        frame_filename = f"{video_path.stem}_frame_{i:03d}.jpg"
        frame_path = output_dir / frame_filename
        
        # Convert back to BGR for saving
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(frame_path), frame_bgr)
        
        extracted_count += 1
    
    cap.release()
    logger.info(f"Extracted {extracted_count} frames to {output_dir}")
    return True


def extract_frames_from_directory(input_dir, output_dir, max_frames=16, frame_size=(224, 224)):
    """
    Extract frames from all videos in a directory.
    
    Args:
        input_dir: Directory containing video files
        output_dir: Directory to save extracted frames
        max_frames: Maximum number of frames per video
        frame_size: Target frame size (width, height)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Find all video files
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(input_dir.glob(f"*{ext}"))
        video_files.extend(input_dir.glob(f"*{ext.upper()}"))
    
    if not video_files:
        logger.warning(f"No video files found in {input_dir}")
        return
    
    logger.info(f"Found {len(video_files)} video files")
    
    # Process each video
    success_count = 0
    for video_file in tqdm(video_files, desc="Extracting frames"):
        video_output_dir = output_dir / video_file.stem
        if extract_frames_from_video(video_file, video_output_dir, max_frames, frame_size):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count}/{len(video_files)} videos")


def organize_frames_by_label(frames_dir, output_dir, label_mapping):
    """
    Organize extracted frames by label.
    
    Args:
        frames_dir: Directory containing extracted frames
        output_dir: Directory to organize frames
        label_mapping: Dictionary mapping video names to labels
    """
    frames_dir = Path(frames_dir)
    output_dir = Path(output_dir)
    
    # Create label directories
    (output_dir / "ai").mkdir(parents=True, exist_ok=True)
    (output_dir / "real").mkdir(parents=True, exist_ok=True)
    
    # Process each video's frames
    for video_dir in frames_dir.iterdir():
        if not video_dir.is_dir():
            continue
        
        video_name = video_dir.name
        label = label_mapping.get(video_name, "unknown")
        
        if label == "unknown":
            logger.warning(f"Unknown label for video: {video_name}")
            continue
        
        # Copy frames to appropriate label directory
        label_dir = output_dir / label
        video_frames = list(video_dir.glob("*.jpg"))
        
        for frame_file in video_frames:
            new_name = f"{video_name}_{frame_file.name}"
            new_path = label_dir / new_name
            
            # Copy file
            import shutil
            shutil.copy2(frame_file, new_path)
        
        logger.info(f"Organized {len(video_frames)} frames for {video_name} -> {label}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract frames from videos")
    parser.add_argument("input", help="Input video file or directory")
    parser.add_argument("output", help="Output directory for frames")
    parser.add_argument("--max-frames", type=int, default=16, help="Maximum frames per video")
    parser.add_argument("--frame-size", nargs=2, type=int, default=[224, 224], help="Frame size (width height)")
    parser.add_argument("--organize", action="store_true", help="Organize frames by label")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    frame_size = tuple(args.frame_size)
    
    if input_path.is_file():
        # Single video file
        extract_frames_from_video(input_path, output_path, args.max_frames, frame_size)
    elif input_path.is_dir():
        # Directory of videos
        extract_frames_from_directory(input_path, output_path, args.max_frames, frame_size)
    else:
        logger.error(f"Input path does not exist: {input_path}")
        return 1
    
    logger.info("Frame extraction completed!")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
