import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

const Navbar = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <motion.nav 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 left-0 right-0 z-50 bg-white/50 backdrop-blur-lg border-b border-[#4a2400]/20"
    >
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold text-[#2D44C8] font-serif">
            <span>Artifact</span>
          </Link>
          
          <div className="flex items-center gap-6">
            <Link 
              to="/" 
              className={`text-sm font-medium transition-colors ${
                isActive('/') 
                  ? 'text-[#2D44C8] font-semibold' 
                  : 'text-black/70 hover:text-[#000000]'
              }`}
            >
              Home
            </Link>
            <Link 
              to="/detect" 
              className={`text-sm font-medium transition-colors ${
                isActive('/detect') 
                  ? 'text-[#2D44C8] font-semibold' 
                  : 'text-black/70 hover:text-[#000000]'
              }`}
            >
              Detect
            </Link>
            <Link 
              to="/news" 
              className={`text-sm font-medium transition-colors ${
                isActive('/news') 
                  ? 'text-[#2D44C8] font-semibold' 
                  : 'text-black/70 hover:text-[#000000]'
              }`}
            >
              Gen-AI News
            </Link>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;