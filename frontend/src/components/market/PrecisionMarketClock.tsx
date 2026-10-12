import React from 'react';
import { ISTTimeData } from '../../utils/istTime';
import { Clock, ShieldCheck, Activity } from 'lucide-react';

interface PrecisionMarketClockProps {
  timeState: ISTTimeData;
}

export const PrecisionMarketClock: React.FC<PrecisionMarketClockProps> = ({ timeState }) => {
  const isLive = timeState.isMarketOpen;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-2.5 bg-[#0c101c]/90 border border-white/[0.08] rounded-xl shadow-lg text-xs backdrop-blur-xl">
      {/* Left: Market Session Status & Indicator */}
      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-lg border shadow-sm ${
            isLive
              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
              : 'bg-rose-500/15 text-rose-300 border-rose-400/30 shadow-[0_0_10px_rgba(244,63,94,0.2)]'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isLive
                ? 'bg-emerald-400 animate-ping'
                : 'bg-rose-500'
            }`}
          />
          <span className="font-bold tracking-wider text-[11px] font-mono">
            {isLive ? 'NSE / BSE LIVE TRADING' : 'NSE / BSE MARKET CLOSED'}
          </span>
        </div>

        <span className="text-slate-600 hidden md:inline">•</span>

        <span className="text-slate-300 text-xs hidden md:inline font-medium">
          {timeState.sessionLabel}
        </span>
      </div>

      {/* Center: Exact High-Precision IST Clock (Showing both 12h and 24h format) */}
      <div className="flex items-baseline gap-2 bg-[#060810] px-4 py-1.5 rounded-lg border border-white/[0.1] font-mono shadow-[inset_0_2px_8px_rgba(0,0,0,0.5)]">
        <Clock className="w-3.5 h-3.5 text-[#d4af37] self-center" />
        {/* 12-hour format prominent */}
        <span className="text-sm font-extrabold text-white tracking-wider">
          {timeState.timeString12}
        </span>
        <span className="text-xs font-bold text-emerald-400">
          .{String(timeState.millis).padStart(3, '0')}
        </span>
        {/* 24-hour format reference */}
        <span className="text-[11px] text-slate-400 ml-1 font-sans">
          ({timeState.timeString} IST)
        </span>
      </div>

      {/* Right: Date, Next Event & Mode */}
      <div className="flex items-center gap-3 text-xs">
        <span className="text-slate-200 font-semibold hidden lg:inline">
          {timeState.dateString}
        </span>

        <span className="text-slate-600 hidden lg:inline">|</span>

        <div className="flex items-center gap-1.5 text-slate-300">
          <span className="text-[11px] font-medium">{timeState.nextEventLabel}</span>
        </div>

        <span className="text-slate-600 hidden sm:inline">|</span>

        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/[0.05] border border-white/[0.08] text-slate-300 font-mono text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Paper Mode (Zero-Risk)</span>
        </div>
      </div>
    </div>
  );
};
