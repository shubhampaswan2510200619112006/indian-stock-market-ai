import React from 'react';
import { Database, ShieldCheck, Cpu, GitBranch, Binary, Activity, Lock, Terminal } from 'lucide-react';

export const PipelineArchitecture: React.FC = () => {
  const stages = [
    { name: 'DATA SOURCES', desc: 'NSE Bhavcopy & Feeds', icon: Database, status: 'CONNECTED', color: 'text-amber-400' },
    { name: 'INGESTION', desc: 'Validation & Timestamps', icon: ShieldCheck, status: 'VERIFIED', color: 'text-emerald-400' },
    { name: 'DATA GATES', desc: '0.68% B/A Audit', icon: ShieldCheck, status: 'ENFORCED', color: 'text-amber-400' },
    { name: 'FEATURE ENGINE', desc: '5-Tier Ablation', icon: Cpu, status: 'ACTIVE', color: 'text-cyan-400' },
    { name: 'OPTIONS ENGINE', desc: 'Black-76 & Surfaces', icon: Binary, status: 'LTP_ONLY', color: 'text-rose-400' },
    { name: 'ML BASELINES', desc: 'Levels 0-3 Purged CV', icon: GitBranch, status: 'BENCHMARKED', color: 'text-blue-400' },
    { name: 'CALIBRATION', desc: 'Brier & ECE Verified', icon: Activity, status: 'CALIBRATED', color: 'text-emerald-400' },
    { name: 'RISK GUARD', desc: 'Execution Disabled', icon: Lock, status: 'LOCKED', color: 'text-rose-400' },
    { name: 'TERMINAL', desc: 'Institutional UX', icon: Terminal, status: 'ACTIVE', color: 'text-amber-400' },
  ];

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-5">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
            END-TO-END DATA FLOW & ARCHITECTURE PIPELINE
          </h3>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded">
          AUDITED DETERMINISTIC PIPELINE
        </span>
      </div>

      {/* Horizontal Flow Container */}
      <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-9 gap-2.5 font-mono text-xs">
        {stages.map((st, idx) => {
          const Icon = st.icon;
          return (
            <div
              key={st.name}
              className="bg-[#05070c] p-3 rounded-lg border border-white/[0.05] hover:border-white/[0.15] transition-all flex flex-col justify-between relative group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-slate-500 font-bold">0{idx + 1}</span>
                  <Icon className={`w-3.5 h-3.5 ${st.color}`} />
                </div>
                <div className="font-bold text-slate-200 text-[11px] truncate tracking-tight">
                  {st.name}
                </div>
                <div className="text-[10px] text-slate-400 mt-1 line-clamp-1">
                  {st.desc}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-white/[0.04] flex items-center justify-between">
                <span className="text-[9px] text-slate-500">GATE</span>
                <span className={`text-[9px] font-bold ${st.color}`}>{st.status}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-white/[0.04] text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>DATA PIPELINE INGESTS NSE OHLCV & OPTIONS RECORDS WITH DETERMINISTIC PROVENANCE</span>
        <span className="text-slate-400">LATENCY & GATING VERIFIED</span>
      </div>
    </div>
  );
};
