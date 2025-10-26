// Real API integration for backend models
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Response interfaces (matching backend)
interface UploadResponse {
  media_id: string;      // Unique identifier for the uploaded file
  success: boolean;
}

interface DetectionResponse {
  is_ai: boolean;        // true = AI-generated, false = Real
  confidence: number;    // 0.0 to 1.0 (e.g., 0.85 = 85%)
  success: boolean;
}

// Mock function 1: File Upload
export const uploadFile = async (file: File): Promise<UploadResponse> => {
  try {
    console.log('🚀 Uploading file:', file.name, 'Size:', file.size);
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('✅ Upload successful:', result);
    
    return result;
  } catch (error) {
    console.error('❌ Upload error:', error);
    return {
      media_id: '',
      success: false
    };
  }
};

// Mock function 2: Detection
export const detectAuthenticity = async (mediaId: string): Promise<DetectionResponse> => {
  try {
    console.log('🔍 Running detection for media_id:', mediaId);
    
    const response = await fetch(`${API_BASE_URL}/api/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ media_id: mediaId }),
    });
    
    if (!response.ok) {
      throw new Error(`Detection failed: ${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('✅ Detection successful:', result);
    
    return result;
  } catch (error) {
    console.error('❌ Detection error:', error);
    return {
      is_ai: false,
      confidence: 0,
      success: false
    };
  }
};

// Health check function
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const result = await response.json();
    console.log('🏥 API Health:', result);
    return result.status === 'healthy' && result.model_loaded;
  } catch (error) {
    console.error('❌ Health check failed:', error);
    return false;
  }
};
