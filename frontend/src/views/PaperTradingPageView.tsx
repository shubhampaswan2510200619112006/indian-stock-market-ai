import React, { useState } from 'react';
import {
  ShieldCheck, AlertTriangle, Wallet, Plus, RotateCcw,
  CheckCircle2, XCircle, Clock, Zap, ArrowRight,
  TrendingUp, TrendingDown, Layers, Activity
} from 'lucide-react';
import { PortfolioDesk } from '../components/trading/PortfolioDesk';
import { usePaperTrading } from '../context/PaperTradingContext';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';

interface PaperTradingPageViewProps {
  onNavigateToOptions?: () => void;
}

export const PaperTradingPageView: React.FC<PaperTradingPageViewProps> = ({
  onNavigateToOptions,
}) => {
  const { account, openOrderModal } = usePaperTrading();
  const { activeInstrument } = useRealtimeMarket();

  const [breakerTripped, setBreakerTripped] = useState(false);

  const handleManualTrip = () => {
    setBreakerTripped(true);
  };

  const handleManualReset = () => {
    setBreakerTripped(false);
  };

  const handleLaunchOrderPad = () => {
    openOrderModal({
      symbol: `${activeInstrument.name} (Paper Spot)`,
      underlying: activeInstrument.name,
      strike: activeInstrument.spot_price,
      option_type: 'CE',
      expiry: activeInstrument.expiries[0] || '17 OCT 2026',
      side: 'BUY',
      product: 'INTRADAY',
      order_type: 'MARKET',
      quantity: activeInstrument.lot_size,
      lots: 1,
      lot_size: activeInstrument.lot_size,
      price: activeInstrument.spot_price,
    });
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Top Paper Trading Safety Banner & Risk Controls ── */}
      <div className="p-4 rounded-2xl bg-[#080d19]/95 border border-purple-500/25 backdrop-blur-xl shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black text-white font-['Outfit'] tracking-tight">
                Simulated Paper Trading Portal
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-500/15 text-purple-400 border border-purple-500/30">
                NO REAL MONEY AT RISK
              </span>
            </div>
            <p className="text-xs text-slate-400">
              SEBI Compliant Paper Environment • Pre-trade margin checks & statutory NSE fee accounting
            </p>
          </div>
        </div>

        {/* Circuit Breakers & Quick Order Actions */}
        <div className="flex items-center gap-2.5">
          {breakerTripped ? (
            <button
              onClick={handleManualReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-400 text-xs font-bold transition-all cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Breakers</span>
            </button>
          ) : (
            <button
              onClick={handleManualTrip}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-400 text-xs font-bold transition-all cursor-pointer"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Emergency Halt</span>
            </button>
          )}

          <button
            onClick={handleLaunchOrderPad}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400 text-white text-xs font-extrabold transition-all cursor-pointer shadow-lg shadow-purple-500/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Order Pad</span>
          </button>
        </div>
      </div>

      {/* Circuit Breaker Status Banner if Tripped */}
      {breakerTripped && (
        <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <strong>CIRCUIT BREAKER TRIPPED: All pending orders cancelled. New orders rejected until reset.</strong>
          </div>
          <button
            onClick={handleManualReset}
            className="px-3 py-1 rounded bg-rose-500 text-white font-bold text-[11px] hover:bg-rose-600"
          >
            Acknowledge & Reset
          </button>
        </div>
      )}

      {/* ── 2. Primary Portfolio & Orders Desk ── */}
      <PortfolioDesk onNavigateToOptions={onNavigateToOptions} />
    </div>
  );
};
