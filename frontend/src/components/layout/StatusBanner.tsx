import React from 'react';
import { motion } from 'framer-motion';
import { GovernanceState } from '../../types/market';
import { ShieldCheck, Zap, TrendingUp, Award, Activity } from 'lucide-react';

interface StatusBannerProps {
  governance: GovernanceState;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({ governance }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="w-full border-b border-white/[0.08] py-1.5 px-4 backdrop-blur-md"
      style={{
        background: 'linear-gradient(90deg, rgba(8, 11, 18, 0.96) 0%, rgba(14, 18, 28, 0.96) 50%, rgba(8, 11, 18, 0.96) 100%)',
      }}
    >
      <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono">
        {/* Left: Executive Institutional Branding */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-[#d4af37]/15 border border-[#d4af37]/40 text-[#f6d776] font-bold shadow-sm">
            <Award className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>INSTITUTIONAL QUANT SUITE</span>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#d4af37]/25 text-white font-mono">v18.0 PRO</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 font-semibold">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>{governance.tests_passing}/{governance.tests_total} AUDITED SUITE PASS</span>
          </div>
        </div>

        {/* Right: Executive Real-time Telemetry Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Live Data Stream */}
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 font-semibold shadow-[0_0_10px_rgba(16,185,129,0.15)]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>LIVE STREAM: 100% NSE/BSE REAL-TIME</span>
          </div>

          {/* Execution Engine */}
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 font-semibold">
            <Zap className="w-3 h-3 text-cyan-400" />
            <span>HFT EXECUTION: SYNCHRONIZED</span>
          </div>

          {/* Price Action Engine */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-[#d4af37]/10 border border-[#d4af37]/30 text-[#f6d776] font-semibold">
            <TrendingUp className="w-3 h-3 text-[#d4af37]" />
            <span>TECHNICAL ENGINE: ACTIVE</span>
          </div>

          {/* Executive Tier */}
          <div className="hidden lg:flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-white/[0.06] border border-white/[0.1] text-slate-300 text-[10px]">
            <Activity className="w-2.5 h-2.5 text-slate-400" />
            <span>Executive Terminal VIP</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
