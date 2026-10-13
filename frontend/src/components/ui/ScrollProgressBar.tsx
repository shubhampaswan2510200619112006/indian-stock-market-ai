import React, { useState, useEffect } from 'react';

export const ScrollProgressBar: React.FC = () => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = (e?: Event) => {
      const target = e?.target as HTMLElement | undefined;
      const scrollTop =
        window.scrollY ||
        document.documentElement.scrollTop ||
        document.body.scrollTop ||
        target?.scrollTop ||
        0;

      const docHeight =
        Math.max(
          document.documentElement.scrollHeight,
          document.body.scrollHeight,
          target?.scrollHeight || 0
        ) - window.innerHeight;

      if (docHeight > 0) {
        const progress = Math.min(100, Math.max(0, (scrollTop / docHeight) * 100));
        setScrollProgress(progress);
      }
    };

    window.addEventListener('scroll', handleScroll, { capture: true, passive: true });
    return () => window.removeEventListener('scroll', handleScroll, { capture: true } as any);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 h-[2.5px] z-[60] pointer-events-none overflow-hidden bg-transparent">
      <div
        className="h-full bg-gradient-to-r from-[#B6FF5C] via-[#43D9FF] to-[#22C983] transition-all duration-75 ease-out shadow-[0_0_12px_rgba(182,255,92,0.8),0_0_20px_rgba(67,217,255,0.6)]"
        style={{ width: `${scrollProgress}%` }}
      />
    </div>
  );
};
