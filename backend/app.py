from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import tempfile
from pathlib import Path
import logging
from werkzeug.utils import secure_filename

from model_loader import ModelLoader
from inference import InferenceEngine
from upload_handler import UploadHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Initialize components
model_loader = ModelLoader()
inference_engine = InferenceEngine(model_loader)
upload_handler = UploadHandler(UPLOAD_FOLDER)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload endpoint - accepts image/video files"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'media_id': None,
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'media_id': None,
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'media_id': None,
                'success': False,
                'error': 'File type not allowed'
            }), 400
        
        # Generate unique media ID
        media_id = str(uuid.uuid4())
        
        # Save file
        success = upload_handler.save_file(file, media_id)
        
        if success:
            logger.info(f"File uploaded successfully: {media_id}")
            return jsonify({
                'media_id': media_id,
                'success': True
            })
        else:
            return jsonify({
                'media_id': None,
                'success': False,
                'error': 'Failed to save file'
            }), 500
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'media_id': None,
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detect', methods=['POST'])
def detect_authenticity():
    """Detection endpoint - analyzes uploaded file"""
    try:
        data = request.get_json()
        if not data or 'media_id' not in data:
            return jsonify({
                'is_ai': None,
                'confidence': None,
                'success': False,
                'error': 'media_id required'
            }), 400
        
        media_id = data['media_id']
        
        # Check if file exists
        file_path = upload_handler.get_file_path(media_id)
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'is_ai': None,
                'confidence': None,
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Run inference
        result = inference_engine.predict(file_path)
        
        if result['success']:
            logger.info(f"Detection completed for {media_id}: {result['is_ai']} ({result['confidence']:.2f})")
            return jsonify({
                'is_ai': result['is_ai'],
                'confidence': result['confidence'],
                'success': True
            })
        else:
            return jsonify({
                'is_ai': None,
                'confidence': None,
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Detection error: {str(e)}")
        return jsonify({
            'is_ai': None,
            'confidence': None,
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loader.is_loaded()
    })

if __name__ == '__main__':
    logger.info("Starting AI Detection API...")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")
    
    # Load model on startup
    if model_loader.load_model():
        logger.info("✅ Model loaded successfully")
    else:
        logger.error("❌ Failed to load model")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
