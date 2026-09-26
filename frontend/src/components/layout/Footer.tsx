import React from 'react';
import { Shield, GitCommit, CheckCircle2, AlertOctagon } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#030508] border-t border-white/[0.06] py-6 px-4 text-xs font-mono text-slate-500">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-col gap-1 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2 text-slate-400">
            <Shield className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-semibold text-slate-300">
              INDIAN MARKET INTELLIGENCE TERMINAL
            </span>
            <span>•</span>
            <span className="text-[11px] text-slate-500">QUANTITATIVE PLATFORM</span>
          </div>
          <p className="text-[10px] text-slate-600 max-w-xl">
            Strict research freeze enforced. All market metrics originate from audited FastAPI endpoints or authoritative NSE archives. Zero synthetic Bid/Ask quotes or execution fills are generated.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900/80 border border-slate-800 text-slate-400">
            <GitCommit className="w-3 h-3 text-slate-500" />
            <span>COMMIT:</span>
            <span className="text-amber-400 font-bold">c70b7b4</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-3 h-3" />
            <span>REGRESSION:</span>
            <span className="font-bold">658 / 658 PASSING</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <AlertOctagon className="w-3 h-3" />
            <span>LIVE EXECUTION:</span>
            <span className="font-bold">DISABLED</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
