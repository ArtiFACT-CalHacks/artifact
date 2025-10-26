import os
import logging
from pathlib import Path
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class UploadHandler:
    def __init__(self, upload_folder):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
    
    def save_file(self, file, media_id):
        """Save uploaded file with media_id as filename"""
        try:
            # Get file extension
            filename = secure_filename(file.filename)
            file_extension = Path(filename).suffix
            
            # Create filename with media_id
            new_filename = f"{media_id}{file_extension}"
            file_path = self.upload_folder / new_filename
            
            # Save file
            file.save(str(file_path))
            
            logger.info(f"File saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return False
    
    def get_file_path(self, media_id):
        """Get file path for given media_id"""
        try:
            # Look for file with this media_id
            for file_path in self.upload_folder.glob(f"{media_id}.*"):
                return str(file_path)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file path: {e}")
            return None
    
    def delete_file(self, media_id):
        """Delete file for given media_id"""
        try:
            file_path = self.get_file_path(media_id)
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
