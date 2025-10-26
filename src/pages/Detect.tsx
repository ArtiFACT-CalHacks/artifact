import React, { useState, useRef } from 'react';
import { uploadFile, detectAuthenticity, checkApiHealth } from '@/utils/api';

// Types (matching your backend)
interface UploadResponse {
  media_id: string;
  success: boolean;
}

interface DetectionResponse {
  is_ai: boolean;
  confidence: number;
  success: boolean;
}

const Detect: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [mediaId, setMediaId] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [result, setResult] = useState<DetectionResponse | null>(null);
  const [apiHealth, setApiHealth] = useState<boolean | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check API health on component mount
  React.useEffect(() => {
    const checkHealth = async () => {
      const healthy = await checkApiHealth();
      setApiHealth(healthy);
    };
    checkHealth();
  }, []);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null); // Clear previous results
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    try {
      const uploadResult: UploadResponse = await uploadFile(file);
      
      if (uploadResult.success) {
        setMediaId(uploadResult.media_id);
        console.log('✅ File uploaded successfully:', uploadResult.media_id);
      } else {
        console.error('❌ Upload failed');
        alert('Upload failed. Please try again.');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDetection = async () => {
    if (!mediaId) return;

    setIsDetecting(true);
    try {
      const detectionResult: DetectionResponse = await detectAuthenticity(mediaId);
      
      if (detectionResult.success) {
        setResult(detectionResult);
        console.log('✅ Detection completed:', detectionResult);
      } else {
        console.error('❌ Detection failed');
        alert('Detection failed. Please try again.');
      }
    } catch (error) {
      console.error('Detection error:', error);
      alert('Detection failed. Please try again.');
    } finally {
      setIsDetecting(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setMediaId('');
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
        AI Detection Tool
      </h1>

      {/* API Health Status */}
      <div className="mb-6 p-4 rounded-lg">
        {apiHealth === null ? (
          <div className="text-yellow-600">🔄 Checking API connection...</div>
        ) : apiHealth ? (
          <div className="text-green-600">✅ API Connected & Model Loaded</div>
        ) : (
          <div className="text-red-600">❌ API Connection Failed - Check Backend</div>
        )}
      </div>

      {/* File Upload Section */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload Image or Video
        </label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/*"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        
        {file && (
          <div className="mt-2 text-sm text-gray-600">
            Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}
      </div>

      {/* Upload Button */}
      <div className="mb-6">
        <button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className="w-full bg-blue-500 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded"
        >
          {isUploading ? 'Uploading...' : 'Upload File'}
        </button>
      </div>

      {/* Detection Section */}
      {mediaId && (
        <div className="mb-6">
          <div className="text-sm text-gray-600 mb-2">
            Media ID: {mediaId}
          </div>
          <button
            onClick={handleDetection}
            disabled={isDetecting}
            className="w-full bg-green-500 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded"
          >
            {isDetecting ? 'Analyzing...' : 'Run Detection'}
          </button>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-3">Detection Results</h3>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Result:</span>
              <span className={`font-bold ${result.is_ai ? 'text-red-600' : 'text-green-600'}`}>
                {result.is_ai ? '🤖 AI-Generated' : '👤 Real'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="font-medium">Confidence:</span>
              <span className="font-bold text-blue-600">
                {(result.confidence * 100).toFixed(1)}%
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="font-medium">Success:</span>
              <span className={`font-bold ${result.success ? 'text-green-600' : 'text-red-600'}`}>
                {result.success ? '✅' : '❌'}
              </span>
            </div>
          </div>

          {/* Confidence Bar */}
          <div className="mt-4">
            <div className="text-sm text-gray-600 mb-1">Confidence Level</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${result.is_ai ? 'bg-red-500' : 'bg-green-500'}`}
                style={{ width: `${result.confidence * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Button */}
      {(file || mediaId || result) && (
        <div className="mt-6">
          <button
            onClick={resetForm}
            className="w-full bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
          >
            Reset
          </button>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 text-sm text-gray-600">
        <h4 className="font-semibold mb-2">Instructions:</h4>
        <ol className="list-decimal list-inside space-y-1">
          <li>Select an image or video file</li>
          <li>Click "Upload File" to upload to the backend</li>
          <li>Click "Run Detection" to analyze the content</li>
          <li>View the results showing if it's AI-generated or real</li>
        </ol>
      </div>
    </div>
  );
};

export default Detect;
