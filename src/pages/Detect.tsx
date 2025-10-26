import { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, History } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import FileUpload from '@/components/FileUpload';
import ResultsDisplay from '@/components/ResultsDisplay';
import { uploadFile, detectAuthenticity } from '@/utils/mockApi';
import { addToHistory } from '@/utils/historyStorage';
import { AnalysisResult } from '@/types/analysis';
import { toast } from 'sonner';

const Detect = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setResult(null);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setResult(null);
  };

  const handleRunDetection = async () => {
    if (!selectedFile) return;

    try {
      // Step 1: Upload file
      setIsUploading(true);
      toast.loading('Uploading file...', { id: 'upload' });
      
      const uploadResponse = await uploadFile(selectedFile);
      toast.success('File uploaded successfully', { id: 'upload' });

      // Step 2: Run detection
      setIsUploading(false);
      setIsDetecting(true);
      toast.loading('Analyzing authenticity...', { id: 'detect' });

      const detectionResponse = await detectAuthenticity(uploadResponse.media_id);
      toast.success('Analysis complete!', { id: 'detect' });

      // Step 3: Create result and save to history
      const analysisResult: AnalysisResult = {
        id: uploadResponse.media_id,
        filename: selectedFile.name,
        fileType: selectedFile.type,
        fileSize: selectedFile.size,
        result: detectionResponse.is_ai ? 'AI' : 'Real',
        confidence: detectionResponse.confidence,
        timestamp: new Date().toISOString(),
        mediaId: uploadResponse.media_id
      };

      setResult(analysisResult);
      addToHistory(analysisResult);
      setIsDetecting(false);

    } catch (error) {
      setIsUploading(false);
      setIsDetecting(false);
      toast.error(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  const handleDownloadReport = () => {
    if (!result) return;

    const report = {
      filename: result.filename,
      result: result.result,
      confidence: `${Math.round(result.confidence * 100)}%`,
      timestamp: new Date(result.timestamp).toLocaleString(),
      mediaId: result.mediaId
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `artifact-report-${result.id}.json`;
    a.click();
    URL.revokeObjectURL(url);

    toast.success('Report downloaded successfully');
  };

  const handleNewAnalysis = () => {
    setSelectedFile(null);
    setResult(null);
  };

  const isProcessing = isUploading || isDetecting;

  return (
    <div className="min-h-screen bg-white text-[#4a2400] flex flex-col">
      <Navbar />
      
      <main className="flex-1 pt-24 pb-8">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-[#2d44c8] mb-2 font-serif">Media Detection</h1>
                <p className="text-black/70">Upload a video or image to verify its authenticity</p>
              </div>
              
              <Button
                onClick={() => navigate('/history')}
                variant="outline"
                className="border-[#2D44C8]/30 text-[#2D44C8] hover:text-[#000000] hover:bg-[#2D44C8]/10 rounded-full px-6"
              >
                <History className="w-4 h-4 mr-2" />
                View History
              </Button>
            </div>
          </motion.div>

          {!result ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6"
            >
              <FileUpload
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
                onClear={handleClear}
                disabled={isProcessing}
              />

              {selectedFile && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Button
                    onClick={handleRunDetection}
                    disabled={isProcessing}
                    className="w-full bg-[#4a2400] hover:bg-[#5c2e00] text-white rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,0.3)]"
                    size="lg"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        {isUploading ? 'Uploading...' : 'Analyzing...'}
                      </>
                    ) : (
                      'Run Detection'
                    )}
                  </Button>
                </motion.div>
              )}
            </motion.div>
          ) : (
            <div className="space-y-6">
              <ResultsDisplay
                result={result.result}
                confidence={result.confidence}
                filename={result.filename}
                onDownloadReport={handleDownloadReport}
              />

              <Button
                onClick={handleNewAnalysis}
                variant="outline"
                className="w-full border-[#4a2400]/30 text-[#4a2400] hover:bg-gray-50 rounded-full"
                size="lg"
              >
                Analyze Another File
              </Button>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Detect;