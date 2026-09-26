import React from 'react';
import { HelpCircle, TrendingUp, Clock, Zap, ShieldAlert, Cpu } from 'lucide-react';

export const GreeksMatrix: React.FC = () => {
  const greeks = [
    {
      name: 'DELTA (Δ)',
      symbol: 'Directional Exposure',
      callValue: '+0.52',
      putValue: '-0.48',
      unit: '₹ per ₹1 index move',
      description: 'First derivative of option price with respect to underlying spot price.',
      formula: '∂V / ∂S',
      color: 'text-emerald-400',
    },
    {
      name: 'GAMMA (Γ)',
      symbol: 'Convexity & Acceleration',
      callValue: '+0.0018',
      putValue: '+0.0018',
      unit: 'Δ change per ₹1 move',
      description: 'Second derivative of option price with respect to underlying spot price.',
      formula: '∂²V / ∂S²',
      color: 'text-cyan-400',
    },
    {
      name: 'THETA (Θ)',
      symbol: 'Time Decay Bleed',
      callValue: '-14.80',
      putValue: '-13.90',
      unit: '₹ erosion per calendar day',
      description: 'First derivative of option price with respect to passing time.',
      formula: '∂V / ∂t',
      color: 'text-rose-400',
    },
    {
      name: 'VEGA (ν)',
      symbol: 'Volatility Sensitivity',
      callValue: '+24.50',
      putValue: '+24.50',
      unit: '₹ change per 1% IV move',
      description: 'First derivative of option price with respect to implied volatility.',
      formula: '∂V / ∂σ',
      color: 'text-purple-400',
    },
    {
      name: 'RHO (ρ)',
      symbol: 'Interest Rate Sensitivity',
      callValue: '+4.12',
      putValue: '-3.85',
      unit: '₹ change per 100 bps rate move',
      description: 'First derivative with respect to risk-free rate (6.5% MIBOR benchmark).',
      formula: '∂V / ∂r',
      color: 'text-amber-400',
    },
  ];

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
            BLACK-76 OPTIONS GREEKS SENSITIVITY MATRIX
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-500">
          ATM BENCHMARK (STRIKE: 24,650 • EXPIRY: NEAR MONTH)
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 font-mono text-xs">
        {greeks.map((g) => (
          <div
            key={g.name}
            className="bg-[#05070c] p-3.5 rounded-lg border border-white/[0.04] hover:border-white/[0.12] transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">{g.name}</span>
                <span className="text-[10px] text-slate-500 font-mono">{g.formula}</span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">{g.symbol}</div>

              <div className="my-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 text-[11px]">ATM CE:</span>
                  <span className={`font-bold ${g.color}`}>{g.callValue}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 text-[11px]">ATM PE:</span>
                  <span className={`font-bold ${g.color}`}>{g.putValue}</span>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-white/[0.04] text-[10px] text-slate-500">
              {g.unit}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-white/[0.04] text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>ANALYTICAL BLACK-76 CLOSED-FORM PARTIAL DERIVATIVES</span>
        <span className="text-amber-400/80">RISK-FREE BENCHMARK: 6.50% (RBI REPO PROXIED)</span>
      </div>
    </div>
  );
};
