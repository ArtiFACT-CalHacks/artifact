import { UploadResponse, DetectionResponse } from '@/types/analysis';

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock file upload endpoint
export const uploadFile = async (file: File): Promise<UploadResponse> => {
  await delay(1500); // Simulate upload time
  
  // Simulate occasional errors (10% chance)
  if (Math.random() < 0.1) {
    throw new Error('Upload failed. Please try again.');
  }
  
  const mediaId = `ORG${Math.random().toString(36).substring(2, 9).toUpperCase()}`;
  
  return {
    media_id: mediaId,
    success: true
  };
};

// Mock detection endpoint
export const detectAuthenticity = async (mediaId: string): Promise<DetectionResponse> => {
  await delay(2000); // Simulate AI processing time
  
  // Simulate occasional errors (5% chance)
  if (Math.random() < 0.05) {
    throw new Error('Detection failed. Please try again.');
  }
  
  // Generate random but realistic results
  const isAi = Math.random() > 0.5;
  const confidence = isAi 
    ? 0.65 + Math.random() * 0.30 // AI: 65-95%
    : 0.70 + Math.random() * 0.25; // Real: 70-95%
  
  return {
    is_ai: isAi,
    confidence: parseFloat(confidence.toFixed(2)),
    success: true
  };
};