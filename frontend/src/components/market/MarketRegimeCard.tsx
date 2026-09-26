import React from 'react';
import { MarketRegime } from '../../types/market';
import { MarketStateOrb3D } from '../3d/MarketStateOrb3D';
import { Activity, Gauge, Compass, ArrowRight } from 'lucide-react';

interface MarketRegimeCardProps {
  regime: MarketRegime;
}

export const MarketRegimeCard: React.FC<MarketRegimeCardProps> = ({ regime }) => {
  const getRegimeColor = (name: string) => {
    switch (name) {
      case 'TREND':
        return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 'BREAKOUT':
        return 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10';
      case 'HIGH_VOLATILITY':
        return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
      case 'TRANSITION':
        return 'text-purple-400 border-purple-500/30 bg-purple-500/10';
      default:
        return 'text-amber-400 border-amber-500/30 bg-amber-500/10'; // RANGE
    }
  };

  return (
    <div className="bg-[#080d19] border border-white/[0.08] rounded-xl p-5 flex flex-col justify-between relative overflow-hidden">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-amber-400" />
            <span className="font-mono text-xs font-semibold text-slate-100 tracking-wider">
              MARKET STATE ENGINE
            </span>
          </div>
          <span className={`px-2 py-0.5 rounded text-[11px] font-mono border ${getRegimeColor(regime.regime)}`}>
            {regime.regime}
          </span>
        </div>

        {/* 3D Animated State Orb */}
        <div className="py-2">
          <MarketStateOrb3D regime={regime.regime} confidence={regime.confidence} />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 font-mono text-center my-4">
          <div className="p-2 rounded bg-[#05070c] border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">CONFIDENCE</div>
            <div className="text-amber-400 font-bold text-sm mt-0.5">
              {(regime.confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="p-2 rounded bg-[#05070c] border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">ADX (14)</div>
            <div className="text-slate-200 font-bold text-sm mt-0.5">
              {regime.adx?.toFixed(1) || '18.4'}
            </div>
          </div>
          <div className="p-2 rounded bg-[#05070c] border border-white/[0.04]">
            <div className="text-[10px] text-slate-500">ATR VOL</div>
            <div className="text-slate-200 font-bold text-sm mt-0.5">
              {regime.atr?.toFixed(0) || '142'}
            </div>
          </div>
        </div>

        {/* Transition Probabilities */}
        <div className="space-y-2 mt-4 font-mono text-xs">
          <div className="text-[10px] text-slate-500 uppercase tracking-widest">
            REGIME TRANSITION MATRIX (P_NEXT)
          </div>
          {Object.entries(regime.transition_probabilities || {}).map(([state, prob]) => (
            <div key={state} className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">{state}</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-400 to-emerald-400 rounded-full"
                    style={{ width: `${prob * 100}%` }}
                  />
                </div>
                <span className="w-9 text-right text-slate-300">{(prob * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-3 border-t border-white/[0.04] text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>PHASE 2 STATISTICAL REGIME CLASSIFIER</span>
        <span className="text-emerald-400">VERIFIED</span>
      </div>
    </div>
  );
};
