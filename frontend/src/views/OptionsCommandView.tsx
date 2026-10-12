import React, { useState } from 'react';
import { OptionChainSnapshot } from '../types/market';
import { PCRMaxPainCard } from '../components/options/PCRMaxPainCard';
import { OptionChainTable } from '../components/options/OptionChainTable';
import { GreeksMatrix } from '../components/options/GreeksMatrix';
import { GrowwOptionChain } from '../components/options/GrowwOptionChain';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { Layers, Activity } from 'lucide-react';

interface OptionsCommandViewProps {
  chain: OptionChainSnapshot;
  expiries: string[];
}

export const OptionsCommandView: React.FC<OptionsCommandViewProps> = ({ chain, expiries }) => {
  const [activeExpiry, setActiveExpiry] = useState<string>(
    expiries.length > 0 ? expiries[0] : 'NEAR_MONTH'
  );
  const [viewMode, setViewMode] = useState<'standard' | 'matrix'>('standard');

  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    selectedExpiry,
    setSelectedExpiry,
    activeInstrument,
    chainRows,
  } = useRealtimeMarket();

  return (
    <div className="space-y-6">
      {/* View Mode Toggle: Interactive Chain vs Institutional Matrix */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-[#0a0f21] border border-white/[0.08] rounded-xl text-xs">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-slate-200 font-semibold tracking-wide">
            Options Derivatives Workspace
          </span>
        </div>

        <div className="flex items-center bg-[#101524] p-0.5 rounded-lg border border-white/[0.06] gap-1 font-medium">
          <button
            type="button"
            onClick={() => setViewMode('standard')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
              viewMode === 'standard'
                ? 'bg-slate-700 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Options Chain (Live Execution)</span>
          </button>

          <button
            type="button"
            onClick={() => setViewMode('matrix')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
              viewMode === 'matrix'
                ? 'bg-slate-700 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span>Black-76 Greeks & PCR Analytics</span>
          </button>
        </div>
      </div>

      {viewMode === 'standard' ? (
        /* ── Interactive Options Chain with Buy/Sell Order Pad ── */
        <GrowwOptionChain
          instrument={activeInstrument}
          instruments={instruments}
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
          selectedExpiry={selectedExpiry}
          onSelectExpiry={setSelectedExpiry}
          rows={chainRows}
        />
      ) : (
        /* ── Black-76 Greeks Matrix View ── */
        <div className="space-y-6">
          <PCRMaxPainCard
            chain={chain}
            expiries={expiries}
            activeExpiry={activeExpiry}
            onSelectExpiry={setActiveExpiry}
          />
          <OptionChainTable chain={chain} atmStrike={chain.atm_strike || 24650} />
          <GreeksMatrix />
        </div>
      )}
    </div>
  );
};
