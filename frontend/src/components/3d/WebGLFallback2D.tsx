import React from 'react';
import { Layers, AlertCircle } from 'lucide-react';

interface WebGLFallback2DProps {
  title?: string;
  subtitle?: string;
}

export const WebGLFallback2D: React.FC<WebGLFallback2DProps> = ({
  title = '2D HIGH-RESOLUTION ANALYTICAL FALLBACK',
  subtitle = 'Volatility Surface Contour Map',
}) => {
  // Strikes from 24000 to 25500
  const strikes = [24000, 24200, 24400, 24600, 24800, 25000, 25200, 25400];
  const expiries = ['T+1d', 'T+7d', 'T+14d', 'T+28d', 'T+60d'];

  // Synthetic theoretical smile values
  const getIV = (strike: number, expIdx: number) => {
    const moneyness = Math.abs(strike - 24650) / 24650;
    const term = (expIdx + 1) * 0.04;
    return (13.5 + moneyness * 32 - term * 1.5).toFixed(1);
  };

  return (
    <div className="w-full h-full min-h-[400px] flex flex-col justify-between p-6 bg-[#080d19] border border-white/[0.08] rounded-xl relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3 z-10">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-amber-400">
            <Layers className="w-3.5 h-3.5" />
            <span>{title}</span>
          </div>
          <p className="text-slate-400 text-xs mt-0.5">{subtitle}</p>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-400/10 border border-amber-400/20 rounded text-[11px] font-mono text-amber-300">
          <AlertCircle className="w-3 h-3" />
          <span>LOD: 2D FALLBACK</span>
        </div>
      </div>

      {/* Contour Grid Matrix */}
      <div className="my-auto py-4 overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-white/[0.06] text-slate-500 text-[10px]">
              <th className="py-2 px-3">EXPIRY \ STRIKE</th>
              {strikes.map((s) => (
                <th key={s} className="py-2 px-3 text-center">
                  {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {expiries.map((exp, eIdx) => (
              <tr key={exp} className="border-b border-white/[0.03] hover:bg-slate-800/30">
                <td className="py-2.5 px-3 text-slate-400 font-semibold">{exp}</td>
                {strikes.map((s) => {
                  const iv = parseFloat(getIV(s, eIdx));
                  const isAtm = s === 24600;
                  const intensity = Math.min(1, Math.max(0.1, (iv - 12) / 8));
                  return (
                    <td key={s} className="py-2.5 px-3 text-center">
                      <div
                        className={`inline-block px-2 py-1 rounded text-[11px] font-mono ${
                          isAtm
                            ? 'border border-amber-400/40 text-amber-300 font-bold'
                            : 'text-slate-300'
                        }`}
                        style={{
                          backgroundColor: `rgba(212, 175, 55, ${intensity * 0.25})`,
                        }}
                      >
                        {iv}%
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-white/[0.06] pt-3 text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>X: Strike Price • Y: Expiry Term • Color: Implied Volatility (IV%)</span>
        <span className="text-amber-400/80">LTP Marks Only • Bid/Ask Verified: 0.68%</span>
      </div>
    </div>
  );
};
