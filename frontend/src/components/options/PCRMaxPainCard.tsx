import React from 'react';
import { OptionChainSnapshot } from '../../types/market';
import { Target, Layers, Scale, Flame, ShieldAlert } from 'lucide-react';

interface PCRMaxPainCardProps {
  chain: OptionChainSnapshot;
  expiries: string[];
  activeExpiry: string;
  onSelectExpiry: (exp: string) => void;
}

export const PCRMaxPainCard: React.FC<PCRMaxPainCardProps> = ({
  chain,
  expiries,
  activeExpiry,
  onSelectExpiry,
}) => {
  const totalOI = (chain.total_call_oi || 1) + (chain.total_put_oi || 1);
  const callOIPct = ((chain.total_call_oi || 0) / totalOI) * 100;
  const putOIPct = ((chain.total_put_oi || 0) / totalOI) * 100;

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      {/* Top Header: Title, Expiry Selector, PCR */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-400/10 border border-amber-400/20 flex items-center justify-center">
            <Layers className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <h2 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
              OPTIONS COMMAND CENTRE • {chain.underlying}
            </h2>
            <div className="text-[11px] font-mono text-slate-400">
              DERIVATIVES OPEN INTEREST & VOLATILITY POSITIONING
            </div>
          </div>
        </div>

        {/* Expiry Selector */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-500 text-[11px]">EXPIRY:</span>
          <select
            value={activeExpiry}
            onChange={(e) => onSelectExpiry(e.target.value)}
            className="bg-[#05070c] border border-white/[0.1] rounded px-3 py-1.5 text-amber-300 font-mono text-xs focus:outline-none focus:border-amber-400/50 cursor-pointer"
          >
            {expiries.length > 0 ? (
              expiries.map((exp) => (
                <option key={exp} value={exp} className="bg-[#0b0f19] text-slate-200">
                  {exp}
                </option>
              ))
            ) : (
              <option value="CURRENT_WEEKLY">NEAR MONTH EXPIRY</option>
            )}
          </select>
        </div>
      </div>

      {/* Primary Key Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">ATM STRIKE</div>
          <div className="text-amber-400 font-bold text-base mt-1">
            {chain.atm_strike.toLocaleString()}
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">PUT / CALL RATIO (PCR)</div>
          <div className="flex items-baseline gap-2 mt-1">
            <span
              className={`font-bold text-base ${
                chain.pcr > 1.0 ? 'text-emerald-400' : 'text-amber-400'
              }`}
            >
              {chain.pcr.toFixed(2)}
            </span>
            <span className="text-[10px] text-slate-500">
              {chain.pcr > 1.2 ? 'BULLISH' : chain.pcr < 0.8 ? 'BEARISH' : 'NEUTRAL'}
            </span>
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">MAX PAIN</div>
          <div className="text-slate-100 font-bold text-base mt-1">
            {chain.max_pain ? chain.max_pain.toLocaleString() : '24,600'}
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">IV REGIME</div>
          <div className="text-cyan-400 font-bold text-base mt-1">
            {chain.iv_regime || 'NORMAL'}
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04] col-span-2 sm:col-span-1">
          <div className="text-[10px] text-slate-500">DATA FIDELITY</div>
          <div className="text-rose-400 font-bold text-xs mt-1 truncate">
            0.68% PAIRED B/A
          </div>
        </div>
      </div>

      {/* Open Interest Balance Bar */}
      <div className="mt-4 pt-4 border-t border-white/[0.04]">
        <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
          <span className="text-emerald-400 font-semibold">
            TOTAL CALL OI: {chain.total_call_oi.toLocaleString()} ({callOIPct.toFixed(1)}%)
          </span>
          <span className="text-slate-400">OPEN INTEREST POSITIONING</span>
          <span className="text-rose-400 font-semibold">
            TOTAL PUT OI: {chain.total_put_oi.toLocaleString()} ({putOIPct.toFixed(1)}%)
          </span>
        </div>
        <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden flex">
          <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${callOIPct}%` }} />
          <div className="h-full bg-rose-500 transition-all duration-500" style={{ width: `${putOIPct}%` }} />
        </div>
      </div>
    </div>
  );
};
