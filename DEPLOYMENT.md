# Deployment Guide

## ✅ Pre-Deployment Checklist

### 1. Clean Up Backend Folder
```bash
# Remove the artifact-backend folder from frontend
rm -rf artifact-backend
```

### 2. Update Environment Variables
Create `.env.production`:
```bash
VITE_API_BASE_URL=https://your-backend-api-url.com
```

### 3. Test Build Locally
```bash
npm run build
npm run preview
```

### 4. Verify All Imports
All component imports should use the `@/` alias:
```typescript
import { Button } from '@/components/ui/button';
import Navbar from '@/components/Navbar';
```

## 🚀 Deployment Steps

### Frontend (Render/Vercel/Netlify)

**Build Command:**
```bash
npm run build
```

**Output Directory:**
```
dist
```

**Environment Variables:**
- `VITE_API_BASE_URL` = Your backend API URL

### Backend (Separate Deployment)

Your backend should be deployed separately:
1. Deploy `artifact-backend` folder to a server (Render, Railway, etc.)
2. Ensure model file `models/effnetv2_test.pth` is included
3. Set up Python environment and install dependencies
4. Start Flask server on port 8000 (or configure)

## 🐛 Common Deployment Issues

### Issue: "Could not load component"
**Solution:** Ensure all imports use `@/` alias and include proper extensions

### Issue: "Module not found"
**Solution:** Check `tsconfig.json` paths configuration

### Issue: API calls failing
**Solution:** Update `VITE_API_BASE_URL` to production backend URL

### Issue: CORS errors
**Solution:** Ensure backend has CORS enabled for your frontend domain

## 📝 Post-Deployment

1. Test file upload functionality
2. Test detection with sample images/videos
3. Verify history storage works
4. Check all navigation links
5. Test on mobile devices

## 🔧 Render-Specific Configuration

If deploying to Render, create `render.yaml`:

```yaml
services:
  - type: web
    name: artifact-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./dist
    envVars:
      - key: VITE_API_BASE_URL
        value: https://your-backend-url.onrender.com
```

## 🎯 Backend Deployment (Separate)

Your backend needs to be deployed separately. Recommended options:
- **Render** (Python web service)
- **Railway** (Easy Python deployment)
- **Heroku** (Classic option)
- **AWS EC2** (Full control)

Backend requirements:
- Python 3.9+
- Flask + dependencies
- Model file (effnetv2_test.pth)
- Persistent storage for uploads