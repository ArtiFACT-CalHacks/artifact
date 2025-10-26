import { useCallback, useState } from 'react';
import { Upload, X, FileVideo, FileImage } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  disabled?: boolean;
}

const FileUpload = ({ onFileSelect, selectedFile, onClear, disabled }: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    const validVideoTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
    const validImageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const validTypes = [...validVideoTypes, ...validImageTypes];
    
    if (!validTypes.includes(file.type)) {
      alert('Invalid file type. Please upload MP4, MOV, AVI, JPG, PNG, GIF, or WebP files.');
      return false;
    }
    
    const maxSize = file.type.startsWith('video/') ? 100 * 1024 * 1024 : 10 * 1024 * 1024;
    if (file.size > maxSize) {
      alert(`File too large. Maximum size: ${file.type.startsWith('video/') ? '100MB' : '10MB'}`);
      return false;
    }
    
    return true;
  };

  const handleFile = useCallback((file: File) => {
    if (validateFile(file)) {
      onFileSelect(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, [onFileSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (disabled) return;
    
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile, disabled]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleClear = () => {
    setPreview(null);
    onClear();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!selectedFile ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all ${
              isDragging 
                ? 'border-[#2D44C8] bg-[#2D44C8]/10' 
                : 'border-[#2D44C8]/30 bg-white hover:border-[#2D44C8]/50'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <input
              type="file"
              onChange={handleFileInput}
              accept="video/mp4,video/quicktime,video/x-msvideo,image/jpeg,image/png,image/gif,image/webp"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={disabled}
            />
            
            <Upload className="w-16 h-16 mx-auto mb-4 text-[#2D44C8]/70" />
            <h3 className="text-xl font-semibold text-black mb-2 font-serif">
              Drop your media here
            </h3>
            <p className="text-black/70 mb-4">
              or click to browse files
            </p>
            <p className="text-sm text-black/60">
              Supports: MP4, MOV, AVI (max 100MB) • JPG, PNG, GIF, WebP (max 10MB)
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white rounded-xl p-6 border border-[#2D44C8]/30 shadow-md"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                {selectedFile.type.startsWith('video/') ? (
                  <FileVideo className="w-8 h-8 text-[#2D44C8]" />
                ) : (
                  <FileImage className="w-8 h-8 text-[#2D44C8]" />
                )}
                <div>
                  <h4 className="text-black font-medium">{selectedFile.name}</h4>
                  <p className="text-sm text-black/70">
                    {formatFileSize(selectedFile.size)} • {selectedFile.type.split('/')[1].toUpperCase()}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClear}
                disabled={disabled}
                className="text-black/60 hover:text-black"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            
            {preview && (
              <div className="rounded-lg overflow-hidden bg-gray-50">
                {selectedFile.type.startsWith('video/') ? (
                  <video src={preview} controls className="w-full max-h-64 object-contain" />
                ) : (
                  <img src={preview} alt="Preview" className="w-full max-h-64 object-contain" />
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FileUpload;