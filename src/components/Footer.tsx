import { ExternalLink } from 'lucide-react';

const Footer = () => {
  const sponsors = [
    { name: 'CREAO', url: 'https://creao.ai' },
    { name: 'Toolhouse', url: 'https://toolhouse.ai' },
    { name: 'Groq', url: 'https://groq.com' }
  ];
  
  return (
    <footer className="bg-[#5A7FBE]/60 border-t border-[#4a2400]/20 py-6 mt-auto">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-black/60 text-sm">
            © 2025 Artifact. Built for artists and creators.
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-black/50 text-sm">Powered by:</span>
            {sponsors.map((sponsor) => (
              <a
                key={sponsor.name}
                href={sponsor.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-sm text-black/60 hover:text-[#6d3600] transition-colors"
              >
                {sponsor.name}
                <ExternalLink className="w-3 h-3" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;