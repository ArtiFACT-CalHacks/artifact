# Frontend-Backend Integration Guide

## 🎯 Overview

This guide shows how to connect your React frontend with the Flask backend API for AI detection.

## 📁 Files Created

### Backend Files (in `/backend/`)
- `app.py` - Main Flask API server
- `model_loader.py` - EfficientNet model loading
- `inference.py` - Image/video inference engine
- `upload_handler.py` - File upload management
- `requirements.txt` - Python dependencies
- `README.md` - Backend documentation

### Frontend Integration Files
- `src/utils/api.ts` - Real API integration (replaces mock)
- `src/pages/Detect.tsx` - Updated Detect component
- `env.example` - Environment variables template

## 🚀 Quick Start

### 1. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python3 app.py
```
Backend will run on `http://localhost:8000`

### 2. Configure Frontend Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env file
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Update Frontend Imports
In your existing `src/pages/Detect.tsx`, change:
```typescript
// From:
import { uploadFile, detectAuthenticity } from '@/utils/mockApi';

// To:
import { uploadFile, detectAuthenticity } from '@/utils/api';
```

## 🔌 API Endpoints

### Upload Endpoint
```
POST /api/upload
Content-Type: multipart/form-data

Request: file (image/video)
Response: { media_id: string, success: boolean }
```

### Detection Endpoint
```
POST /api/detect
Content-Type: application/json

Request: { media_id: string }
Response: { is_ai: boolean, confidence: number, success: boolean }
```

### Health Check
```
GET /api/health
Response: { status: "healthy", model_loaded: boolean }
```

## 🧪 Testing

### 1. Test Backend Health
```bash
curl http://localhost:8000/api/health
```

### 2. Test File Upload
```bash
curl -X POST -F "file=@test_image.jpg" http://localhost:8000/api/upload
```

### 3. Test Detection
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"media_id":"your-media-id"}' \
  http://localhost:8000/api/detect
```

## 🔄 Switching Between Mock and Real API

### Use Real API (Production)
```typescript
import { uploadFile, detectAuthenticity } from '@/utils/api';
```

### Use Mock API (Development/Testing)
```typescript
import { uploadFile, detectAuthenticity } from '@/utils/mockApi';
```

## 🐛 Troubleshooting

### Backend Issues
- **Model not loading**: Check if `../models/effnetv2_test.pth` exists
- **Port conflicts**: Change port in `app.py` (line 80)
- **CORS errors**: Ensure Flask-CORS is installed

### Frontend Issues
- **API not connecting**: Check `VITE_API_BASE_URL` in `.env`
- **Upload fails**: Check file size limits (100MB max)
- **Detection fails**: Verify media_id is valid

### Common Errors
- **"File not found"**: Media ID doesn't exist or file was deleted
- **"Model not loaded"**: Backend model loading failed
- **"CORS error"**: Frontend/backend URL mismatch

## 📊 Response Format

### Upload Response
```typescript
interface UploadResponse {
  media_id: string;      // UUID for uploaded file
  success: boolean;      // Upload success status
}
```

### Detection Response
```typescript
interface DetectionResponse {
  is_ai: boolean;        // true = AI-generated, false = Real
  confidence: number;    // 0.0 to 1.0 (e.g., 0.85 = 85%)
  success: boolean;      // Detection success status
}
```

## 🎨 Frontend Features

The updated `Detect.tsx` includes:
- ✅ API health check indicator
- ✅ File upload with progress
- ✅ Detection with loading states
- ✅ Results display with confidence bar
- ✅ Error handling and user feedback
- ✅ Reset functionality

## 🔧 Customization

### Change API URL
Update `.env` file:
```
VITE_API_BASE_URL=https://your-production-api.com
```

### Modify File Limits
Edit `backend/app.py`:
```python
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
```

### Add More File Types
Edit `backend/app.py`:
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv', 'webm'}
```

## 🚀 Production Deployment

### Backend
- Use production WSGI server (Gunicorn)
- Set up proper logging
- Configure environment variables
- Use HTTPS in production

### Frontend
- Build for production: `npm run build`
- Update API URL to production endpoint
- Configure CORS for production domain

## 📝 Next Steps

1. **Test the integration** with sample images/videos
2. **Customize the UI** to match your design
3. **Add error handling** for edge cases
4. **Deploy to production** when ready
5. **Monitor performance** and optimize as needed

## 🆘 Support

If you encounter issues:
1. Check browser console for frontend errors
2. Check backend logs for server errors
3. Verify API endpoints with curl/Postman
4. Ensure all dependencies are installed
5. Check file permissions and paths
