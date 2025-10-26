import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface ResultsDisplayProps {
  result: 'AI' | 'Real';
  confidence: number;
  filename: string;
  onDownloadReport: () => void;
}

const ResultsDisplay = ({ result, confidence, filename, onDownloadReport }: ResultsDisplayProps) => {
  const isAI = result === 'AI';
  const confidencePercent = Math.round(confidence * 100);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Main Result Card */}
      <Card className={`p-8 border-2 ${
        isAI ? 'border-red-500 bg-red-500/5' : 'border-green-500 bg-green-500/5'
      } shadow-md`}>
        <div className="flex items-center justify-center gap-4 mb-6">
          {isAI ? (
            <AlertTriangle className="w-12 h-12 text-red-500" />
          ) : (
            <CheckCircle className="w-12 h-12 text-green-500" />
          )}
          <div>
            <h2 className="text-3xl font-bold text-black font-serif">
              {isAI ? 'AI-Generated' : 'Authentic'}
            </h2>
            <p className="text-black/70">Detection Result</p>
          </div>
        </div>
        
        <div className="text-center">
          <p className="text-sm text-black/70 mb-2">Analyzed: {filename}</p>
        </div>
      </Card>

      {/* Confidence Score Card */}
      <Card className="p-6 bg-white border-[#2D44C8]/30 shadow-md">
        <h3 className="text-lg font-semibold text-[#2D44C8] mb-4 font-serif">Confidence Score</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-black/70">Detection Confidence</span>
            <span className="text-2xl font-bold text-[#2D44C8]">{confidencePercent}%</span>
          </div>
          
          <Progress 
            value={confidencePercent} 
            className="h-3"
          />
          
          <div className="grid grid-cols-3 gap-2 text-xs text-black/60">
            <div className="text-left">Low (0-33%)</div>
            <div className="text-center">Medium (34-66%)</div>
            <div className="text-right">High (67-100%)</div>
          </div>
        </div>
      </Card>

      {/* Visual Trace Card */}
      <Card className="p-6 bg-white border-[#2D44C8]/30 shadow-md">
        <h3 className="text-lg font-semibold text-[#2D44C8] mb-4 font-serif">Analysis Breakdown</h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-black/70">Pattern Recognition</span>
            <div className="flex items-center gap-2">
              <Progress value={confidencePercent * 0.9} className="w-32 h-2" />
              <span className="text-sm text-black">{Math.round(confidencePercent * 0.9)}%</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-black/70">Artifact Detection</span>
            <div className="flex items-center gap-2">
              <Progress value={confidencePercent * 0.95} className="w-32 h-2" />
              <span className="text-sm text-black">{Math.round(confidencePercent * 0.95)}%</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-black/70">Metadata Analysis</span>
            <div className="flex items-center gap-2">
              <Progress value={confidencePercent * 0.85} className="w-32 h-2" />
              <span className="text-sm text-black">{Math.round(confidencePercent * 0.85)}%</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Download Report Button */}
      <Button 
        onClick={onDownloadReport}
        className="w-full bg-[#2D44C8] hover:bg-[#1F2E8A] text-white rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,0.3)]"
        size="lg"
      >
        <Download className="w-5 h-5 mr-2" />
        Download Report
      </Button>
    </motion.div>
  );
};

export default ResultsDisplay;