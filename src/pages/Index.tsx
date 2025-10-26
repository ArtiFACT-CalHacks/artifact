import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Shield, Zap, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { extractColorsFromImage } from '@/utils/colorExtractor';

// Import hero images
import heroImage1 from '@/utils/heroImages/B3-CC200_11_ORj_750RV_20181018181410.jpg';
import heroImage2 from '@/utils/heroImages/basquiat_untitled.jpg.webp';
import heroImage3 from '@/utils/heroImages/IMG_0107 2.jpg';

const Index = () => {
  const navigate = useNavigate();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageShadows, setImageShadows] = useState<string[]>([]);
  
  const heroImages = [heroImage1, heroImage2, heroImage3];

  useEffect(() => {
    // Extract colors from all images on mount
    const extractAllColors = async () => {
      const shadows = await Promise.all(
        heroImages.map(async (img) => {
          const colors = await extractColorsFromImage(img);
          return `0 25px 50px -12px ${colors[0]}, 0 35px 60px -15px ${colors[1]}, 0 45px 70px -20px ${colors[2]}`;
        })
      );
      setImageShadows(shadows);
    };
    
    extractAllColors();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % heroImages.length);
    }, 5000); // Change image every 5 seconds

    return () => clearInterval(interval);
  }, [heroImages.length]);

  const features = [
    {
      icon: Shield,
      title: 'Instant Verification',
      description: 'Upload any video or image and get authenticity results in seconds'
    },
    {
      icon: Zap,
      title: 'AI-Powered Detection',
      description: 'Advanced algorithms analyze patterns and artifacts to determine authenticity'
    },
    {
      icon: TrendingUp,
      title: 'Track Your History',
      description: 'Keep records of all your analyses with sortable and searchable history'
    }
  ];

  return (
    <div className="min-h-screen bg-white text-[#4a2400] flex flex-col">
      <Navbar />
      
      <main className="flex-1 pt-16">
        {/* Hero Section with Background Images */}
        <section className="relative overflow-hidden">
          {/* Background Image Carousel - Full Section */}
          <div className="absolute inset-0">
            <AnimatePresence initial={false}>
              <motion.div
                key={currentImageIndex}
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '-100%' }}
                transition={{ duration: 0.8, ease: 'easeInOut' }}
                className="absolute inset-0"
              >
                <div 
                  className="absolute inset-0 bg-cover bg-center"
                  style={{ backgroundImage: `url(${heroImages[currentImageIndex]})` }}
                />
                {/* Subtle base overlay */}
                <div className="absolute inset-0 bg-white/20" />
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Hero Content */}
          <div className="relative container mx-auto px-4 py-16 md:py-24">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center max-w-4xl mx-auto"
            >
              {/* Glass morphism text backdrop - Apple Liquid Glass style */}
              <div 
                className="rounded-3xl p-8 md:p-12 border border-white/20"
                style={{
                  background: 'rgba(255, 255, 255, 0.25)',
                  backdropFilter: 'blur(20px) saturate(180%)',
                  WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                  boxShadow: '0 8px 32px 0 rgba(74, 36, 0, 0.1), inset 0 1px 0 0 rgba(255, 255, 255, 0.5)'
                }}
              >
                <h1 className="text-5xl md:text-7xl font-bold mb-6 text-[#2D44C8] font-serif">
                  Keep your art real.
                </h1>
                
                <p className="text-xl md:text-2xl text-black font-semibold mb-10 max-w-2xl mx-auto">
                  Verify whether media content is AI-generated or authentic. Protect your creative work and maintain trust in digital content.
                </p>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <Button
                    onClick={() => navigate('/detect')}
                    size="lg"
                    className="bg-[#2D44C8] hover:bg-[#1F2E8A] text-white text-lg px-8 py-6 rounded-full shadow-[inset_0_2px_4px_rgba(255,255,255,0.3)] hover:shadow-lg transition-all"
                  >
                    Check Media Now
                  </Button>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Features Section with Gradient Background */}
        <section 
          className="py-16"
          style={{
            background: 'linear-gradient(to bottom, rgba(255, 255, 255, 0.3), rgba(90, 127, 190, 0.43))'
          }}
        >
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="grid md:grid-cols-3 gap-6"
            >
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div 
                    className="p-6 rounded-xl border border-white/20 h-full transition-all hover:scale-105"
                    style={{
                      background: 'rgba(255, 255, 255, 0.4)',
                      backdropFilter: 'blur(16px) saturate(180%)',
                      WebkitBackdropFilter: 'blur(16px) saturate(180%)',
                      boxShadow: '0 8px 32px 0 rgba(74, 36, 0, 0.08), inset 0 1px 0 0 rgba(255, 255, 255, 0.5)'
                    }}
                  >
                    <feature.icon className="w-12 h-12 text-[#60718F] mb-4" />
                    <h3 className="text-xl font-semibold text-[#60718F] mb-2 font-serif">
                      {feature.title}
                    </h3>
                    <p className="text-black/70">
                      {feature.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Index;