import React from 'react';
import { ShieldCheck, Zap, TrendingUp, Award, Layers } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const Footer: React.FC = () => {
  const { themeConfig } = useTheme();

  return (
    <footer className="w-full border-t border-white/[0.08] py-8 px-5 text-xs backdrop-blur-xl relative z-10"
      style={{
        background: 'linear-gradient(180deg, rgba(7, 9, 14, 0.85) 0%, rgba(10, 14, 22, 0.98) 100%)',
      }}
    >
      <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Left Branding */}
        <div className="flex flex-col gap-1.5 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2.5">
            <span className="text-xl">{themeConfig.icon}</span>
            <span className="font-bold text-white tracking-wide text-sm"
              style={{
                fontFamily: 'Plus Jakarta Sans, sans-serif',
                background: 'linear-gradient(135deg, #ffffff 40%, #d4af37 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              INDIAN STOCK MARKET AI
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#d4af37]/15 text-[#f6d776] border border-[#d4af37]/30">
              v18.0 PRO
            </span>
          </div>
          <p className="text-[11px] text-slate-400 max-w-xl leading-relaxed">
            Institutional-grade quantitative derivatives intelligence and paper trading execution suite. Engineered strictly for NSE and BSE markets with real-time millisecond market data feeds.
          </p>
        </div>

        {/* Right Institutional Status Chips */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 font-mono text-[11px]">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 font-semibold shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>100% REAL-TIME NSE STREAM</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 font-semibold shadow-sm">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>SUB-MS MATCHING ENGINE</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#d4af37]/10 border border-[#d4af37]/25 text-[#f6d776] font-semibold shadow-sm">
            <TrendingUp className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>TECHNICAL ENGINE ONLINE</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
