#!/usr/bin/env python3
"""
Test script for the AI Detection Backend API
Tests all endpoints to ensure they're working correctly
"""

import requests
import json
import os
from pathlib import Path
from PIL import Image
import io

API_BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a proper test image"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def test_health():
    """Test the health check endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return data.get('model_loaded', False)
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_upload():
    """Test file upload endpoint"""
    print("\n📤 Testing upload endpoint...")
    
    # Create a proper test image
    test_image_data = create_test_image()
    
    try:
        files = {'file': ('test.png', test_image_data, 'image/png')}
        response = requests.post(f"{API_BASE_URL}/api/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful: {data}")
            return data.get('media_id')
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_detection(media_id):
    """Test detection endpoint"""
    print(f"\n🔍 Testing detection endpoint with media_id: {media_id}")
    
    try:
        payload = {"media_id": media_id}
        response = requests.post(
            f"{API_BASE_URL}/api/detect",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detection successful: {data}")
            return True
        else:
            print(f"❌ Detection failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Detection error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API Tests")
    print("=" * 50)
    
    # Test 1: Health check
    model_loaded = test_health()
    if not model_loaded:
        print("❌ Model not loaded. Please check backend logs.")
        return
    
    # Test 2: Upload
    media_id = test_upload()
    if not media_id:
        print("❌ Upload test failed. Cannot proceed with detection test.")
        return
    
    # Test 3: Detection
    detection_success = test_detection(media_id)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Health Check: {'PASSED' if model_loaded else 'FAILED'}")
    print(f"✅ Upload Test: {'PASSED' if media_id else 'FAILED'}")
    print(f"✅ Detection Test: {'PASSED' if detection_success else 'FAILED'}")
    
    if model_loaded and media_id and detection_success:
        print("\n🎉 All tests passed! Your API is working correctly.")
        print("\n🚀 Ready for frontend integration!")
    else:
        print("\n❌ Some tests failed. Please check the backend logs.")

if __name__ == "__main__":
    main()