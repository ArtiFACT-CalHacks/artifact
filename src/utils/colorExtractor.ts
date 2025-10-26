export const extractColorsFromImage = (imageSrc: string): Promise<string[]> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Could not get canvas context'));
        return;
      }
      
      // Use smaller canvas for performance
      canvas.width = 100;
      canvas.height = 100;
      
      ctx.drawImage(img, 0, 0, 100, 100);
      
      try {
        const imageData = ctx.getImageData(0, 0, 100, 100);
        const pixels = imageData.data;
        
        // Sample pixels and collect colors
        const colorMap: { [key: string]: number } = {};
        
        // Sample every 10th pixel for performance
        for (let i = 0; i < pixels.length; i += 40) {
          const r = pixels[i];
          const g = pixels[i + 1];
          const b = pixels[i + 2];
          const a = pixels[i + 3];
          
          // Skip transparent pixels
          if (a < 125) continue;
          
          // Round to reduce color variations
          const roundedR = Math.round(r / 20) * 20;
          const roundedG = Math.round(g / 20) * 20;
          const roundedB = Math.round(b / 20) * 20;
          
          const colorKey = `${roundedR},${roundedG},${roundedB}`;
          colorMap[colorKey] = (colorMap[colorKey] || 0) + 1;
        }
        
        // Get top 3 most common colors
        const sortedColors = Object.entries(colorMap)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([color]) => {
            const [r, g, b] = color.split(',').map(Number);
            return `rgba(${r}, ${g}, ${b}, 0.4)`;
          });
        
        // Ensure we have at least 3 colors
        while (sortedColors.length < 3) {
          sortedColors.push('rgba(74, 36, 0, 0.4)');
        }
        
        resolve(sortedColors);
      } catch (error) {
        // Fallback to default colors if extraction fails
        resolve([
          'rgba(74, 36, 0, 0.4)',
          'rgba(109, 54, 0, 0.3)',
          'rgba(139, 69, 19, 0.2)'
        ]);
      }
    };
    
    img.onerror = () => {
      // Fallback to default colors
      resolve([
        'rgba(74, 36, 0, 0.4)',
        'rgba(109, 54, 0, 0.3)',
        'rgba(139, 69, 19, 0.2)'
      ]);
    };
    
    img.src = imageSrc;
  });
};