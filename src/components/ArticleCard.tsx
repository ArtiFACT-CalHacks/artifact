import { motion } from 'framer-motion';
import { ExternalLink, Calendar, Tag, Image as ImageIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Article } from '@/types/article';
import { useState } from 'react';

interface ArticleCardProps {
  article: Article;
  index: number;
}

const ArticleCard = ({ article, index }: ArticleCardProps) => {
  const [imageError, setImageError] = useState(false);
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  const getTypeColor = (type: string): string => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes('regulation') || lowerType.includes('policy')) return 'bg-blue-500/20 text-blue-700 border-blue-500/50';
    if (lowerType.includes('misinformation') || lowerType.includes('deepfake')) return 'bg-red-500/20 text-red-700 border-red-500/50';
    if (lowerType.includes('entertainment') || lowerType.includes('art')) return 'bg-purple-500/20 text-purple-700 border-purple-500/50';
    if (lowerType.includes('education') || lowerType.includes('journalism')) return 'bg-green-500/20 text-green-700 border-green-500/50';
    if (lowerType.includes('healthcare') || lowerType.includes('therapy')) return 'bg-teal-500/20 text-teal-700 border-teal-500/50';
    if (lowerType.includes('ethics') || lowerType.includes('privacy')) return 'bg-orange-500/20 text-orange-700 border-orange-500/50';
    return 'bg-gray-500/20 text-gray-700 border-gray-500/50';
  };

  const types = article.type.split(',').map(t => t.trim());

  // Generate gradient background based on article index (fallback)
  const gradients = [
    'linear-gradient(135deg, rgba(96, 113, 143, 0.15), rgba(45, 68, 200, 0.15))',
    'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.15))',
    'linear-gradient(135deg, rgba(236, 72, 153, 0.15), rgba(239, 68, 68, 0.15))',
    'linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.15))',
    'linear-gradient(135deg, rgba(251, 146, 60, 0.15), rgba(245, 158, 11, 0.15))',
  ];
  
  const gradient = gradients[index % gradients.length];

  // Generate thumbnail URL using a link preview service
  // Using microlink.io API for Open Graph image extraction
  const getThumbnailUrl = (url: string) => {
    try {
      const encodedUrl = encodeURIComponent(url);
      return `https://api.microlink.io/?url=${encodedUrl}&screenshot=true&meta=false&embed=screenshot.url`;
    } catch {
      return null;
    }
  };

  const thumbnailUrl = getThumbnailUrl(article.url);

  return (
    <motion.a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      className="block group"
    >
      <div 
        className="h-full rounded-xl border border-white/20 overflow-hidden transition-all hover:shadow-lg"
        style={{
          background: 'rgba(255, 255, 255, 0.4)',
          backdropFilter: 'blur(16px) saturate(180%)',
          WebkitBackdropFilter: 'blur(16px) saturate(180%)',
          boxShadow: '0 8px 32px 0 rgba(74, 36, 0, 0.08), inset 0 1px 0 0 rgba(255, 255, 255, 0.5)'
        }}
      >
        {/* Header with image or gradient fallback */}
        <div className="h-32 relative overflow-hidden">
          {thumbnailUrl && !imageError ? (
            <>
              <img 
                src={thumbnailUrl}
                alt={article.title}
                className="w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
            </>
          ) : (
            <div style={{ background: gradient }} className="w-full h-full flex items-center justify-center">
              <ImageIcon className="w-12 h-12 text-white/30" />
            </div>
          )}
          <div className="absolute top-3 right-3">
            <ExternalLink className="w-5 h-5 text-white/80 group-hover:text-white transition-colors drop-shadow-lg" />
          </div>
        </div>

        {/* Content */}
        <div className="p-5 space-y-3">
          {/* Title */}
          <h3 className="text-lg font-semibold text-[#2D44C8] font-serif line-clamp-2 group-hover:text-[#1F2E8A] transition-colors">
            {article.title}
          </h3>

          {/* Summary */}
          <p className="text-sm text-black/70 line-clamp-3">
            {article.summary}
          </p>

          {/* Type badges */}
          <div className="flex flex-wrap gap-2">
            {types.slice(0, 3).map((type, i) => (
              <Badge 
                key={i}
                variant="outline"
                className={`text-xs ${getTypeColor(type)}`}
              >
                {type}
              </Badge>
            ))}
            {types.length > 3 && (
              <Badge variant="outline" className="text-xs bg-gray-500/20 text-gray-700 border-gray-500/50">
                +{types.length - 3}
              </Badge>
            )}
          </div>

          {/* AI Involvement */}
          <div className="flex items-center gap-2 flex-wrap">
            <Tag className="w-4 h-4 text-[#60718F]" />
            <div className="flex flex-wrap gap-1">
              {article.ai_involvement.slice(0, 3).map((ai, i) => (
                <span key={i} className="text-xs text-black/60 bg-[#60718F]/10 px-2 py-1 rounded-full">
                  {ai}
                </span>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-black/10">
            <span className="text-sm font-medium text-[#2D44C8]">
              {article.source}
            </span>
            <div className="flex items-center gap-1 text-xs text-black/60">
              <Calendar className="w-3 h-3" />
              {formatDate(article.date)}
            </div>
          </div>

          {/* Impact */}
          <div className="pt-2">
            <p className="text-xs text-black/60 italic line-clamp-2">
              {article.impact}
            </p>
          </div>
        </div>
      </div>
    </motion.a>
  );
};

export default ArticleCard;