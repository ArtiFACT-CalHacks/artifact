import { motion } from 'framer-motion';
import { Newspaper, TrendingUp } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import ArticleCard from '@/components/ArticleCard';
import { mockNewsData } from '@/utils/mockNewsData';

const GenAINews = () => {
  const articles = mockNewsData.articles;

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
            <div className="flex items-center gap-3 mb-4">
              <h1 className="text-4xl font-bold text-[#2D44C8] font-serif">Gen-AI News</h1>
            </div>
            <p className="text-black/70 text-lg max-w-3xl">
              Stay informed about the latest developments in AI-generated media.
            </p>
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
                    <strong className="text-[#2D44C8] font-semibold">{articles.length}</strong> recent articles from trusted sources
                  </span>
                </div>
                <div className="text-sm text-black/60">
                  Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Articles Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {articles.map((article, index) => (
              <ArticleCard 
                key={index} 
                article={article} 
                index={index}
              />
            ))}
          </div>

          {/* Empty State (for future when no articles) */}
          {articles.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-16"
            >
              <Newspaper className="w-16 h-16 mx-auto mb-4 text-black/30" />
              <h3 className="text-xl font-semibold text-black/70 mb-2">No articles available</h3>
              <p className="text-black/50">Check back soon for the latest Gen-AI news</p>
            </motion.div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default GenAINews;