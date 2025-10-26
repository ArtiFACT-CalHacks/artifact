# AI Detection Backend API

A Flask-based backend API for detecting AI-generated images and videos using EfficientNet-V2-L.

## Features

- **File Upload**: Accept images and videos via multipart form data
- **AI Detection**: Analyze uploaded media and return authenticity results
- **Confidence Scores**: Provide confidence levels (0.0 to 1.0)
- **CORS Support**: Ready for frontend integration
- **Health Check**: Monitor API status

## API Endpoints

### 1. Upload File
```
POST /api/upload
Content-Type: multipart/form-data

Request Body:
- file: File (image or video)

Response:
{
  "media_id": "uuid-string",
  "success": true
}
```

### 2. Detect Authenticity
```
POST /api/detect
Content-Type: application/json

Request Body:
{
  "media_id": "uuid-string"
}

Response:
{
  "is_ai": false,
  "confidence": 0.87,
  "success": true
}
```

### 3. Health Check
```
GET /api/health

Response:
{
  "status": "healthy",
  "model_loaded": true
}
```

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Model Exists**
   - Make sure `../models/effnetv2_test.pth` exists
   - This should be your trained EfficientNet model

3. **Run the API**
   ```bash
   python app.py
   ```

4. **Test the API**
   - API runs on `http://localhost:8000`
   - Test with: `curl http://localhost:8000/api/health`

## Supported File Types

- **Images**: PNG, JPG, JPEG, GIF
- **Videos**: MP4, AVI, MOV, MKV

## Model Architecture

- **Backbone**: EfficientNet-V2-L (pretrained on ImageNet)
- **Classifier**: Custom 2-class classifier (Real vs AI)
- **Input**: 224x224 images or 5 frames from videos
- **Output**: Binary classification with confidence score

## Frontend Integration

Update your frontend's API calls to point to:
```typescript
const API_BASE_URL = 'http://localhost:8000';
```

## Error Handling

All endpoints return consistent error responses:
```json
{
  "success": false,
  "error": "Error message"
}
```

## Logging

The API logs all operations including:
- File uploads
- Model predictions
- Errors and exceptions
- Health status
