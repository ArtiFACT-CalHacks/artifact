import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Newspaper, TrendingUp, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import ArticleCard from '@/components/ArticleCard';
import { mockNewsData } from '@/utils/mockNewsData';
import { fetchNewsFromToolhouse, getCachedNews, getCacheAge } from '@/utils/toolhouseAgent';
import { Article } from '@/types/article';
import { toast } from 'sonner';

const GenAINews = () => {
  const [articles, setArticles] = useState<Article[]>(mockNewsData.articles);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [usingCache, setUsingCache] = useState(false);

  useEffect(() => {
    // Try to load cached data on mount
    const cached = getCachedNews();
    if (cached) {
      setArticles(cached.articles);
      setLastUpdated(getCacheAge());
      setUsingCache(true);
    }
  }, []);

  const handleRefreshNews = async () => {
    setIsLoading(true);
    toast.loading('Fetching latest AI news articles...', { id: 'fetch-news' });

    try {
      const newsData = await fetchNewsFromToolhouse();
      setArticles(newsData.articles);
      setLastUpdated('Just now');
      setUsingCache(false);
      toast.success(`Loaded ${newsData.articles.length} fresh articles!`, { id: 'fetch-news' });
    } catch (error) {
      console.error('Failed to fetch news:', error);
      toast.error('Failed to fetch news. Showing cached/mock data.', { id: 'fetch-news' });
      
      // Fallback to cached or mock data
      const cached = getCachedNews();
      if (cached) {
        setArticles(cached.articles);
        setUsingCache(true);
      } else {
        setArticles(mockNewsData.articles);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-[#4a2400] flex flex-col">
      <Navbar />
      
      <main className="flex-1 pt-24 pb-8">
        <div className="container mx-auto px-4 max-w-7xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-4xl font-bold text-[#2D44C8] font-serif">Gen-AI News</h1>
                  {usingCache && (
                    <span className="text-xs bg-yellow-500/20 text-yellow-700 px-2 py-1 rounded-full border border-yellow-500/50">
                      Cached
                    </span>
                  )}
                </div>
                <p className="text-black/70 text-lg max-w-3xl">
                  Stay informed about the latest developments in AI-generated media.
                </p>
              </div>

              <Button
                onClick={handleRefreshNews}
                disabled={isLoading}
                className="bg-[#2D44C8] hover:bg-[#1F2E8A] text-white rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,0.3)]"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh News
                  </>
                )}
              </Button>
            </div>
          </motion.div>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <div 
              className="rounded-xl p-6 border border-white/20"
              style={{
                background: 'rgba(255, 255, 255, 0.4)',
                backdropFilter: 'blur(16px) saturate(180%)',
                WebkitBackdropFilter: 'blur(16px) saturate(180%)',
                boxShadow: '0 8px 32px 0 rgba(74, 36, 0, 0.08), inset 0 1px 0 0 rgba(255, 255, 255, 0.5)'
              }}
            >
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-[#60718F]" />
                  <span className="text-black/70">
                    <strong className="text-[#2D44C8] font-semibold">{articles.length}</strong> articles from trusted sources
                  </span>
                </div>
                <div className="text-sm text-black/60">
                  {lastUpdated ? `Last updated: ${lastUpdated}` : 'Using mock data'}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Loading State */}
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="h-96 rounded-xl border border-white/20 animate-pulse"
                  style={{
                    background: 'rgba(255, 255, 255, 0.4)',
                    backdropFilter: 'blur(16px) saturate(180%)',
                  }}
                />
              ))}
            </div>
          )}

          {/* Articles Grid */}
          {!isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article, index) => (
                <ArticleCard 
                  key={index} 
                  article={article} 
                  index={index}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && articles.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <Newspaper className="w-16 h-16 mx-auto mb-4 text-black/30" />
              <h3 className="text-xl font-semibold text-black/70 mb-2">No articles available</h3>
              <p className="text-black/50 mb-4">Click "Refresh News" to fetch the latest articles</p>
              <Button
                onClick={handleRefreshNews}
                className="bg-[#2D44C8] hover:bg-[#1F2E8A] text-white rounded-full"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Fetch Articles
              </Button>
            </motion.div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default GenAINews;