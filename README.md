# Binary AI Video Classification

A simple binary classifier to detect AI-generated videos using EfficientNet-V2-L and ConvNeXt-Base models with adaptive frame extraction.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Hugging Face authentication (optional):
```bash
export HUGGINGFACE_TOKEN=your_token_here
```

## Usage

### Step 1: Extract Frames
Download the dataset and extract frames adaptively:
```bash
python frame_extractor.py --download --output ./data_frames
```

This will:
- Download the DeepAction dataset locally
- Extract 1-7 frames per video based on duration
- Save frames as JPG images in `./data_frames/`

### Step 2: Training
Train both models on the extracted frames:
```bash
python train.py
```

### Step 3: Evaluation
Test trained models and see confidence scores:
```bash
python evaluate.py
```

## Models

- **EfficientNet-V2-L**: 145M parameters, pretrained on ImageNet
- **ConvNeXt-Base**: 88M parameters, pretrained on ImageNet

Both models are modified for 2-class binary classification (Real vs AI-generated).

## Dataset

Uses the `faridlab/deepaction_v1` dataset from Hugging Face, which contains:
- Real videos
- AI-generated videos

The system downloads videos locally and extracts frames adaptively:
- ≤1s: 1 frame
- ≤5s: 2 frames  
- ≤10s: 3 frames
- ≤20s: 5 frames
- ≤30s: 6 frames
- >30s: 7 frames (cap)

## Output

- Extracted frames saved to `data_frames/` directory
- Trained models saved to `models/` directory (only classifier weights)
- Training logs saved to `training.log`
- Evaluation shows accuracy, precision, recall, F1-score, and confidence scores