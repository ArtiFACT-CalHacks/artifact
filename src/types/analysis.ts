export interface AnalysisResult {
  id: string;
  filename: string;
  fileType: string;
  fileSize: number;
  result: 'AI' | 'Real';
  confidence: number;
  timestamp: string;
  mediaId?: string;
}

export interface UploadResponse {
  media_id: string;
  success: boolean;
}

export interface DetectionResponse {
  is_ai: boolean;
  confidence: number;
  success: boolean;
}