// Real API integration for backend models
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface UploadResponse {
  media_id: string;
  success: boolean;
}

export interface DetectionResponse {
  is_ai: boolean;
  confidence: number;
  success: boolean;
}

/**
 * Upload a media file to the backend
 * POST /api/upload
 */
export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary for FormData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || `Upload failed with status ${response.status}`);
    }

    const data: UploadResponse = await response.json();
    
    if (!data.media_id) {
      throw new Error('Invalid response: missing media_id');
    }

    return data;
  } catch (error) {
    console.error('Upload error:', error);
    throw error instanceof Error ? error : new Error('Upload failed');
  }
};

/**
 * Run authenticity detection on uploaded media
 * POST /api/detect
 */
export const detectAuthenticity = async (mediaId: string): Promise<DetectionResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ media_id: mediaId }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Detection failed' }));
      throw new Error(error.message || `Detection failed with status ${response.status}`);
    }

    const data: DetectionResponse = await response.json();
    
    if (typeof data.is_ai !== 'boolean' || typeof data.confidence !== 'number') {
      throw new Error('Invalid response format');
    }

    // Validate confidence is between 0 and 1
    if (data.confidence < 0 || data.confidence > 1) {
      throw new Error('Confidence score must be between 0 and 1');
    }

    return data;
  } catch (error) {
    console.error('Detection error:', error);
    throw error instanceof Error ? error : new Error('Detection failed');
  }
};