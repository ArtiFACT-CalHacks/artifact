# DeepAction Classification Pipeline

A minimal two-stage deep learning pipeline for detecting AI-generated videos using EfficientNet-V2-L and ConvNeXt-V2 models.

## Overview

This project implements a robust two-stage classification system for the DeepAction v1 dataset:

1. **Stage 1 (EfficientNet-V2-L)**: High texture sensitivity for initial classification
2. **Stage 2 (ConvNeXt-V2)**: Broader receptive field analysis for low-confidence cases

The system uses confidence-based routing where ConvNeXt is only used when EfficientNet's confidence is below 0.2.

## Project Structure

```
artifact-models/
├── 📂 data/                       # where datasets live
│   ├── train/
│   │   ├── ai/
│   │   └── real/
│   ├── val/
│   │   ├── ai/
│   │   └── real/
│   └── videos/                    # (optional) raw FaridLab .mp4s
├── 📂 models/                     # where your trained weights go
│   ├── efficientnetv2l.pth
│   └── convnextv2base.pth
├── train.py                       # main script that loads data + trains both models
├── dataset_utils.py               # helper for loading, augmenting, and splitting data
├── frame_extractor.py             # (optional) extract frames from FaridLab videos
├── evaluate.py                    # metrics + confusion matrix
├── requirements.txt               # only training dependencies
└── .gitignore                     # ignore data + cache
```

## Features

- **Two-Stage Pipeline**: Confidence-based model selection
- **Apple Silicon Support**: Optimized for MPS (Metal Performance Shaders)
- **Comprehensive Logging**: Detailed training and evaluation logs
- **Modular Design**: Each component can be used standalone
- **Rich Metrics**: Accuracy, precision, recall, F1, confusion matrix
- **Visualization**: Confusion matrix plots and confidence analysis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd artifact
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure you have the required datasets access:
```bash
# The dataset will be automatically downloaded from Hugging Face
# Make sure you have internet access and proper authentication
```

## Usage

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Prepare your data:
```bash
# Create data directory structure
mkdir -p data/train/ai data/train/real data/val/ai data/val/real

# Download FaridLab dataset (optional)
python -c "from dataset_utils import download_faridlab_dataset; download_faridlab_dataset()"

# Or extract frames from your own videos
python frame_extractor.py /path/to/videos data/videos --max-frames 16
```

### Training

Train both models sequentially:

```bash
python train.py
```

This will:
- Load videos from `./data/train/` and `./data/val/`
- Train EfficientNet-V2-L (Stage 1)
- Train ConvNeXt-V2 (Stage 2)
- Save checkpoints to `./models/`
- Log progress to `training.log`

### Evaluation

Run the two-stage evaluation:

```bash
python evaluate.py
```

This will:
- Load trained models from `./models/`
- Run two-stage inference on validation set
- Generate results in `results.csv`
- Create confusion matrix visualization
- Output detailed metrics

### Data Organization

Your data should be organized as:
```
data/
├── train/
│   ├── ai/          # AI-generated videos (*.mp4)
│   └── real/        # Real videos (*.mp4)
└── val/
    ├── ai/          # AI-generated videos (*.mp4)
    └── real/        # Real videos (*.mp4)
```

## Two-Stage Logic

The confidence-based two-stage approach improves robustness:

1. **High Confidence (≥0.2)**: Use EfficientNet result directly
2. **Low Confidence (<0.2)**: Use ConvNeXt for refinement

This leverages:
- EfficientNet's texture sensitivity for clear cases
- ConvNeXt's broader receptive field for ambiguous cases

## Model Architecture

### EfficientNet-V2-L (Stage 1)
- **Backbone**: EfficientNet-V2-L (pretrained)
- **Input**: Video frames (T, 3, 224, 224)
- **Output**: Probability + Confidence
- **Features**: 1280 → 512 → 1

### ConvNeXt-V2 (Stage 2)
- **Backbone**: ConvNeXt-V2-Base (pretrained)
- **Input**: Video frames (T, 3, 224, 224)
- **Output**: Probability + Confidence
- **Features**: 1024 → 512 → 1

## Dataset

Uses the `faridlab/deepaction_v1` dataset from Hugging Face:
- **Real videos**: Label 0
- **AI-generated videos**: Label 1
- **Frame sampling**: Up to 16 frames per video
- **Preprocessing**: Resize to 224×224, normalize with ImageNet stats

## Results

The evaluation generates:
- `results.csv`: Detailed per-video predictions
- `evaluation_results.json`: Complete results with metrics
- `metrics_summary.txt`: Human-readable summary
- `confusion_matrix.png`: Visualization

## Configuration

Key parameters can be modified in the training script:
- `epochs`: Number of training epochs (default: 20)
- `learning_rate`: Learning rate (default: 1e-4)
- `batch_size`: Batch size (default: 8)
- `confidence_threshold`: Stage 2 activation threshold (default: 0.2)

## Hardware Requirements

- **Minimum**: CPU with 8GB RAM
- **Recommended**: Apple Silicon Mac or NVIDIA GPU
- **Storage**: ~2GB for models and checkpoints

## Troubleshooting

### Common Issues

1. **CUDA/MPS not available**: The system will fall back to CPU
2. **Dataset download fails**: Check internet connection and Hugging Face access
3. **Memory issues**: Reduce batch size in training script
4. **Model loading errors**: Ensure models are trained first

### Performance Tips

- Use smaller batch sizes for evaluation
- Enable mixed precision training for faster training
- Use multiple workers for data loading (adjust based on CPU cores)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of CalHacks 2025. Please refer to the event guidelines for usage terms.

## Acknowledgments

- DeepAction v1 dataset creators
- Hugging Face for dataset hosting
- PyTorch and torchvision teams
- Apple for MPS support
