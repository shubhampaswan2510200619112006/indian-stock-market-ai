import React from 'react';

interface CyberLogoProps {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const CyberLogo: React.FC<CyberLogoProps> = ({ size = 'md', showSubtitle = true }) => {
  const iconSize = size === 'sm' ? 30 : size === 'lg' ? 44 : 36;
  const titleSize = size === 'sm' ? '12px' : size === 'lg' ? '16px' : '13px';

  return (
    <div className="flex items-center gap-3 select-none group cursor-pointer">
      {/* Futuristic Cyber Bull & Circuit Icon */}
      <div
        className="relative flex items-center justify-center rounded-xl overflow-hidden transition-all duration-300 group-hover:scale-105"
        style={{
          width: iconSize,
          height: iconSize,
          background: 'radial-gradient(circle at 30% 30%, rgba(182,255,92,0.2) 0%, rgba(16,22,34,0.95) 100%)',
          border: '1px solid rgba(182,255,92,0.4)',
          boxShadow: '0 0 16px rgba(182,255,92,0.18), inset 0 0 8px rgba(67,217,255,0.15)',
        }}
      >
        {/* Ambient spinning cyber glow ring */}
        <div className="absolute inset-0 bg-gradient-to-tr from-[#43D9FF]/20 via-transparent to-[#B6FF5C]/20 opacity-70 group-hover:opacity-100 transition-opacity" />

        {/* Vector SVG Bull Head with Technical Candlestick Horns & Circuitry */}
        <svg
          viewBox="0 0 40 40"
          className="w-4/5 h-4/5 relative z-10"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Cyber Bull Horns (Left & Right Candlestick shapes) */}
          <path
            d="M8 8 C 12 14, 15 17, 16 22 L 20 20 L 24 22 C 25 17, 28 14, 32 8 C 29 12, 26 15, 24 16 L 20 18 L 16 16 C 14 15, 11 12, 8 8 Z"
            fill="url(#bullGoldGrad)"
          />
          {/* Central Candlestick Core */}
          <line x1="20" y1="12" x2="20" y2="30" stroke="#B6FF5C" strokeWidth="1.5" strokeLinecap="round" />
          <rect x="18" y="18" width="4" height="8" rx="1" fill="#B6FF5C" />
          
          {/* Holographic Cheek Plates & Eyes */}
          <polygon points="14,24 18,28 16,33 12,27" fill="url(#bullAccent)" opacity="0.85" />
          <polygon points="26,24 22,28 24,33 28,27" fill="url(#bullAccent)" opacity="0.85" />
          <circle cx="16" cy="22" r="1.2" fill="#43D9FF" />
          <circle cx="24" cy="22" r="1.2" fill="#43D9FF" />
          
          {/* Cyber Nodes */}
          <circle cx="8" cy="8" r="1.5" fill="#B6FF5C" />
          <circle cx="32" cy="8" r="1.5" fill="#B6FF5C" />

          <defs>
            <linearGradient id="bullGoldGrad" x1="8" y1="8" x2="32" y2="22" gradientUnits="userSpaceOnUse">
              <stop stopColor="#B6FF5C" />
              <stop offset="0.6" stopColor="#43D9FF" />
              <stop offset="1" stopColor="#0B1220" />
            </linearGradient>
            <linearGradient id="bullAccent" x1="12" y1="24" x2="28" y2="33" gradientUnits="userSpaceOnUse">
              <stop stopColor="#43D9FF" />
              <stop offset="1" stopColor="#080B12" />
            </linearGradient>
          </defs>
        </svg>

        {/* Energy Pulse Dot */}
        <div className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-[#43D9FF] animate-ping opacity-75" />
      </div>

      {/* Typography & Subtitle */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2">
          <span
            style={{
              fontFamily: 'Inter, sans-serif',
              fontWeight: 800,
              fontSize: titleSize,
              letterSpacing: '0.04em',
              background: 'linear-gradient(135deg, #F3F6FC 30%, #E2E8F0 70%, #929DB0 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            INDIAN STOCK MARKET AI
          </span>
          <span
            className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold tracking-wider uppercase border"
            style={{
              background: 'rgba(182,255,92,0.12)',
              borderColor: 'rgba(182,255,92,0.35)',
              color: '#B6FF5C',
            }}
          >
            QUANT v18.0
          </span>
        </div>

        {showSubtitle && (
          <div className="flex items-center gap-2 text-[10px] font-mono tracking-wider uppercase text-slate-400">
            <span className="text-cyan-400">NSE / BSE</span>
            <span>•</span>
            <span className="text-slate-400">QUANTITATIVE TRADING INTELLIGENCE</span>
          </div>
        )}
      </div>
    </div>
  );
};
