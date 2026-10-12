import React, { useState } from 'react';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { useToast } from '../ui/Toast';
import {
  BrainCircuit, TrendingUp, TrendingDown, Target, ShieldAlert,
  Zap, CheckCircle2, ChevronRight, Activity, Sparkles, AlertCircle
} from 'lucide-react';

interface MLEngineSignalCardProps {
  currentSpot?: number;
  onNavigateToOptions?: () => void;
}

export const MLEngineSignalCard: React.FC<MLEngineSignalCardProps> = ({
  currentSpot = 24652.8,
  onNavigateToOptions,
}) => {
  const { placeOrder } = usePaperTrading();
  const { addToast } = useToast();
  const [isExecuting, setIsExecuting] = useState(false);
  const [executed, setExecuted] = useState(false);

  // Active AI Predictive Recommendation
  const signal = {
    symbol: 'NIFTY 24650 CE 17 OCT',
    underlying: 'NIFTY',
    strike: 24650,
    optionType: 'CE' as const,
    expiry: '17 OCT 2026',
    action: 'BUY CALL (CE)',
    actionType: 'BUY' as const,
    confidence: 87.4,
    entryPrice: 172.65,
    targetPrice1: 215.00,
    targetPrice2: 245.00,
    stopLoss: 148.00,
    riskReward: '1 : 2.6',
    lotSize: 25,
    status: 'ACTIVE_SIGNAL',
    reasons: [
      'Bullish Engulfing reversal pattern confirmed at ₹24,630 demand zone.',
      'Option Chain PCR rose to 0.96 with heavy put writing at 24,600 strike floor.',
      'Institutional order-flow momentum score (+0.84) indicates upward continuation.',
    ],
  };

  const handleExecuteSignal = async () => {
    setIsExecuting(true);
    try {
      const res = await placeOrder({
        symbol: signal.symbol,
        underlying: signal.underlying,
        strike: signal.strike,
        option_type: signal.optionType,
        expiry: signal.expiry,
        side: 'BUY',
        product: 'INTRADAY',
        order_type: 'MARKET',
        quantity: signal.lotSize,
        lots: 1,
        lot_size: signal.lotSize,
        price: signal.entryPrice,
      });

      if (res.success) {
        setExecuted(true);
        addToast(`AI Signal Executed! Bought 1 Lot ${signal.symbol} @ ₹${signal.entryPrice}`, 'success');
      } else {
        addToast(res.message || 'Execution error', 'error');
      }
    } catch {
      addToast('Order placement failed', 'error');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="rounded-2xl bg-gradient-to-r from-[#0c1322] via-[#0f172a] to-[#0c1322] border border-[#d4af37]/35 p-4 sm:p-5 shadow-[0_8px_30px_rgba(0,0,0,0.5),0_0_20px_rgba(212,175,55,0.07)] relative overflow-hidden backdrop-blur-xl">
      {/* Ambient background glow */}
      <div className="absolute top-0 right-0 w-80 h-40 bg-gradient-to-bl from-emerald-500/10 via-cyan-500/5 to-transparent pointer-events-none blur-2xl" />

      {/* Top Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#d4af37] to-amber-500 flex items-center justify-center text-slate-950 shadow-md">
            <BrainCircuit className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black tracking-wider text-[#f6d776] uppercase font-mono">
                QUANT ML PREDICTIVE ENGINE
              </span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                HIGH PROBABILITY SIGNAL
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              Deterministic rule-based gating + Machine Learning alpha model
            </div>
          </div>
        </div>

        {/* Confidence Badge */}
        <div className="flex items-center gap-2 bg-[#060a14] px-3 py-1.5 rounded-xl border border-white/[0.08]">
          <span className="text-xs text-slate-400 font-mono">Model Confidence:</span>
          <span className="text-sm font-extrabold text-emerald-400 font-mono">
            {signal.confidence}%
          </span>
        </div>
      </div>

      {/* Signal Primary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center bg-[#070c17]/80 p-3.5 sm:p-4 rounded-xl border border-white/[0.06]">
        {/* Recommendation & Contract (5 cols) */}
        <div className="md:col-span-5 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs font-extrabold flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              {signal.action}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Lot Size: {signal.lotSize}
            </span>
          </div>
          <div className="text-base sm:text-lg font-black text-white font-['Outfit'] tracking-tight">
            {signal.symbol}
          </div>
          <div className="text-xs text-slate-300 font-mono flex items-center gap-2">
            <span>Spot Reference: <strong>₹{currentSpot.toLocaleString('en-IN', { minimumFractionDigits: 1 })}</strong></span>
            <span>•</span>
            <span>R:R <strong>{signal.riskReward}</strong></span>
          </div>
        </div>

        {/* Pricing Levels (4 cols) */}
        <div className="md:col-span-4 grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded-lg bg-[#0d1424] border border-white/[0.06]">
            <div className="text-[10px] text-slate-400 uppercase font-mono">Entry</div>
            <div className="text-xs sm:text-sm font-extrabold text-white font-mono">
              ₹{signal.entryPrice.toFixed(2)}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/25">
            <div className="text-[10px] text-emerald-400 uppercase font-mono flex items-center justify-center gap-0.5">
              <Target className="w-2.5 h-2.5" /> T1 Target
            </div>
            <div className="text-xs sm:text-sm font-extrabold text-emerald-300 font-mono">
              ₹{signal.targetPrice1.toFixed(2)}
            </div>
          </div>
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/25">
            <div className="text-[10px] text-rose-400 uppercase font-mono flex items-center justify-center gap-0.5">
              <ShieldAlert className="w-2.5 h-2.5" /> Stop Loss
            </div>
            <div className="text-xs sm:text-sm font-extrabold text-rose-300 font-mono">
              ₹{signal.stopLoss.toFixed(2)}
            </div>
          </div>
        </div>

        {/* 1-Click Execution CTA (3 cols) */}
        <div className="md:col-span-3 flex flex-col gap-2">
          <button
            type="button"
            onClick={handleExecuteSignal}
            disabled={isExecuting || executed}
            className={`w-full py-2.5 px-3 rounded-xl font-extrabold text-xs sm:text-sm flex items-center justify-center gap-1.5 transition-all shadow-md cursor-pointer ${
              executed
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40 cursor-default'
                : 'bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 text-slate-950 hover:brightness-110 active:scale-95 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
            }`}
          >
            {isExecuting ? (
              <span>Executing Fill...</span>
            ) : executed ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Trade Active in Ledger</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-slate-950" />
                <span>1-Click Execute AI Trade</span>
              </>
            )}
          </button>

          {onNavigateToOptions && (
            <button
              type="button"
              onClick={onNavigateToOptions}
              className="text-[11px] text-[#f6d776] hover:underline flex items-center justify-center gap-1 font-mono transition-colors cursor-pointer"
            >
              <span>Inspect Strike Chain</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* AI Reasoning Details */}
      <div className="mt-3 pt-3 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-[#d4af37]" />
          <span className="font-semibold text-slate-200">ML Deterministic Catalysts:</span>
          <span className="text-slate-400 hidden lg:inline">
            {signal.reasons.join(' • ')}
          </span>
          <span className="text-slate-400 lg:hidden">
            {signal.reasons[0]}
          </span>
        </div>
      </div>
    </div>
  );
};
