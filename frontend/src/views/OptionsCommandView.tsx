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
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-[#080d19]/95 border border-[#d4af37]/25 rounded-xl text-xs backdrop-blur-xl">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-white font-bold tracking-wide uppercase font-['Outfit']">
            Unified Derivatives Strike Matrix & Execution Hub
          </span>
        </div>

        <div className="flex items-center bg-[#060a14] p-1 rounded-lg border border-white/[0.08] gap-1 font-medium">
          <button
            type="button"
            onClick={() => setViewMode('standard')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
              viewMode === 'standard'
                ? 'bg-[#d4af37]/20 text-[#f6d776] font-bold border border-[#d4af37]/40 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Interactive Strike Matrix & Order Desk</span>
          </button>

          <button
            type="button"
            onClick={() => setViewMode('matrix')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
              viewMode === 'matrix'
                ? 'bg-[#d4af37]/20 text-[#f6d776] font-bold border border-[#d4af37]/40 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-[#d4af37]" />
            <span>Black-76 Greeks & PCR Heatmap</span>
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
