import React from 'react';
import { ShieldCheck, AlertTriangle, Lock, Award, FileText, CheckCircle2 } from 'lucide-react';

export const ResearchIntegrityCard: React.FC = () => {
  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-3 mb-4 gap-2">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
            SCIENTIFIC RESEARCH EVIDENCE & HYPOTHESIS AUDIT
          </h3>
        </div>
        <span className="font-mono text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
          PRE-REGISTERED REGISTRY (H001 — H008)
        </span>
      </div>

      {/* 4 Flagship Quantitative Audit Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-xs mb-5">
        <div className="bg-[#05070c] p-4 rounded-lg border border-rose-500/20">
          <div className="text-[10px] text-slate-500">HYPOTHESES SURVIVED</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">0 / 8 SURVIVED</div>
          <div className="text-[10px] text-slate-400 mt-1">
            0% survived realistic Indian market transaction frictions.
          </div>
        </div>

        <div className="bg-[#05070c] p-4 rounded-lg border border-amber-500/20">
          <div className="text-[10px] text-slate-500">CONTINUOUS EXECUTABLE SURFACE</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">0.0%</div>
          <div className="text-[10px] text-slate-400 mt-1">
            Historical paired Bid/Ask depth unavailable in public EOD records.
          </div>
        </div>

        <div className="bg-[#05070c] p-4 rounded-lg border border-amber-500/20">
          <div className="text-[10px] text-slate-500">PAIRED BID/ASK COVERAGE</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">0.68%</div>
          <div className="text-[10px] text-slate-400 mt-1">
            102 valid paired quotes out of 15,106 historical options quotes.
          </div>
        </div>

        <div className="bg-[#05070c] p-4 rounded-lg border border-rose-500/20">
          <div className="text-[10px] text-slate-500">OPTIONS EXECUTION BACKTEST</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">BLOCKED</div>
          <div className="text-[10px] text-slate-400 mt-1">
            Multi-week live paper trading blocked until tick data secured.
          </div>
        </div>
      </div>

      {/* Cost Decomposition & Data Snooping Audit */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        {/* Cost Decomposition Table */}
        <div className="bg-[#05070c] p-4 rounded-lg border border-white/[0.04]">
          <div className="text-xs font-bold text-slate-200 mb-2 flex items-center justify-between">
            <span>COST DECOMPOSITION (CASE A)</span>
            <span className="text-[10px] text-rose-400 font-normal">FAILURE: NO GROSS EDGE</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between text-slate-400">
              <span>Gross Strategy PnL:</span>
              <span className="text-rose-400 font-semibold">-17.76%</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Statutory Taxes (STT/GST/Stamp):</span>
              <span className="text-slate-300">-2.85%</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Execution Slippage (conservative):</span>
              <span className="text-slate-300">-2.85%</span>
            </div>
            <div className="flex justify-between text-slate-200 pt-1.5 border-t border-white/[0.04] font-bold">
              <span>Net Strategy Return:</span>
              <span className="text-rose-400">-23.46%</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 mt-3">
            Diagnosis: Losses are compounded by trading turnover on an uninformative predictive signal rather than fee drag alone.
          </p>
        </div>

        {/* Multiple Testing & Data Snooping */}
        <div className="bg-[#05070c] p-4 rounded-lg border border-white/[0.04]">
          <div className="text-xs font-bold text-slate-200 mb-2 flex items-center justify-between">
            <span>DATA SNOOPING & MULTIPLE TESTING</span>
            <span className="text-[10px] text-emerald-400 font-normal">STATUS: CLEAN</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between text-slate-400">
              <span>Pre-Registered Hypotheses:</span>
              <span className="text-slate-200 font-semibold">8</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Final Test Partition Contaminations:</span>
              <span className="text-emerald-400 font-semibold">0 (Zero Leaks)</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Purged Walk-Forward Embargo:</span>
              <span className="text-emerald-400 font-semibold">10-Day Horizon</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Statistical Governance Verdict:</span>
              <span className="text-amber-400 font-semibold">HONEST DISCLOSURE</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 mt-3">
            No p-hacking or synthetic overfitting. Negative research findings are preserved for institutional auditability.
          </p>
        </div>
      </div>
    </div>
  );
};
