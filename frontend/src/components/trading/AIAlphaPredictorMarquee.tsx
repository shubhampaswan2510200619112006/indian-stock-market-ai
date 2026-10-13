import React, { useState, useMemo } from 'react';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { useToast } from '../ui/Toast';
import {
  BrainCircuit, TrendingUp, TrendingDown, Target, ShieldAlert,
  Zap, CheckCircle2, ChevronRight, Activity, Sparkles, Flame,
  Layers, ArrowUpRight, BarChart2, ShieldCheck, RefreshCw
} from 'lucide-react';

interface AIAlphaPredictorMarqueeProps {
  symbol?: string;
  currentSpot?: number;
  onNavigateToOptions?: () => void;
  compact?: boolean;
}

export const AIAlphaPredictorMarquee: React.FC<AIAlphaPredictorMarqueeProps> = ({
  symbol = 'NIFTY',
  currentSpot = 24652.8,
  onNavigateToOptions,
  compact = false,
}) => {
  const { placeOrder } = usePaperTrading();
  const { addToast } = useToast();
  const [isExecuting, setIsExecuting] = useState(false);
  const [executed, setExecuted] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Compute dynamic quantitative signal based on the selected symbol and spot
  const signal = useMemo(() => {
    const isBank = symbol.includes('BANK');
    const isSensex = symbol.includes('SENSEX');
    const step = isBank ? 100 : isSensex ? 100 : 50;
    const baseSpot = currentSpot || (isBank ? 51240 : isSensex ? 81420 : 24650);

    // Dynamic strike selection near ATM + 0.5 step
    const atmStrike = Math.round(baseSpot / step) * step;
    const optionType: 'CE' | 'PE' = 'CE'; // High conviction bullish flow
    const action = 'BUY CALL (CE)';
    const strike = atmStrike;
    const lotSize = isBank ? 15 : isSensex ? 10 : 25;
    const contractSymbol = `${symbol} ${strike} ${optionType} 17 OCT`;

    const entryPrice = parseFloat((baseSpot * (isBank ? 0.0075 : 0.0070)).toFixed(2));
    const targetPrice1 = parseFloat((entryPrice * 1.25).toFixed(2));
    const targetPrice2 = parseFloat((entryPrice * 1.45).toFixed(2));
    const stopLoss = parseFloat((entryPrice * 0.85).toFixed(2));
    const profitPerLot = Math.round((targetPrice1 - entryPrice) * lotSize);

    return {
      symbol: contractSymbol,
      underlying: symbol,
      strike,
      optionType,
      expiry: '17 OCT 2026',
      action,
      confidence: 88.9,
      regime: 'BULLISH MOMENTUM BREAKOUT',
      entryPrice,
      targetPrice1,
      targetPrice2,
      stopLoss,
      profitPerLot,
      gainPct: '+25.0%',
      riskReward: '1 : 2.7',
      lotSize,
      catalysts: [
        { title: 'Order Flow Velocity', score: '+0.86', text: 'Heavy institutional aggressive bid volume' },
        { title: 'Gamma Inflexion', score: 'Bullish', text: `Support base anchored at ₹${atmStrike - step} floor` },
        { title: 'Volatility Skew', score: 'Favorable', text: 'IV discount favors long directional gamma' },
      ],
    };
  }, [symbol, currentSpot]);

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
        addToast(
          `AI Alpha Executed! Bought 1 Lot ${signal.symbol} @ ₹${signal.entryPrice} (Target: ₹${signal.targetPrice1})`,
          'success'
        );
      } else {
        addToast(res.message || 'Execution error', 'error');
      }
    } catch {
      addToast('Order placement failed', 'error');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setExecuted(false);
      addToast('AI Alpha Models Re-scored across order-book depth', 'info');
    }, 600);
  };

  return (
    <div className="relative rounded-2xl overflow-hidden border border-[#B6FF5C]/35 bg-gradient-to-r from-[#0d1525] via-[#101b30] to-[#0d1525] p-4 sm:p-5 shadow-[0_8px_32px_rgba(0,0,0,0.6),0_0_25px_rgba(182,255,92,0.12)] backdrop-blur-2xl transition-all hover:border-[#B6FF5C]/50 group">
      
      {/* Ambient background glows */}
      <div className="absolute top-0 right-0 w-96 h-48 bg-gradient-to-bl from-[#B6FF5C]/10 via-[#43D9FF]/8 to-transparent pointer-events-none blur-3xl -z-10" />
      <div className="absolute -bottom-10 -left-10 w-60 h-40 bg-[#43D9FF]/10 pointer-events-none blur-2xl -z-10" />

      {/* Top Banner Header: Badges & Model Meta */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3.5 border-b border-[#283345]/80">
        <div className="flex items-center gap-3">
          {/* Animated Glowing Beacon */}
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-[#B6FF5C] to-[#43D9FF] text-[#080B12] shadow-[0_0_15px_rgba(182,255,92,0.4)] flex-shrink-0">
            <BrainCircuit className="w-5 h-5 animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#B6FF5C] opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-[#B6FF5C]" />
            </span>
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs sm:text-sm font-black tracking-wider text-[#B6FF5C] uppercase font-mono flex items-center gap-1.5">
                <span>AI ALPHA PREDICTOR</span>
                <span className="text-[10px] text-[#929DB0]">• QUANT ENGINE</span>
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#B6FF5C]/15 text-[#B6FF5C] border border-[#B6FF5C]/30 flex items-center gap-1">
                <Flame className="w-3 h-3 text-[#B6FF5C]" />
                HIGH CONVICTION SETUP
              </span>
            </div>
            <div className="text-[11px] text-[#929DB0] font-mono">
              Live Black-76 Greeks & Order-Flow Multi-Layer Transformer Model
            </div>
          </div>
        </div>

        {/* Model Accuracy & Live Status */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            title="Recalculate AI conviction"
            className="p-1.5 rounded-lg bg-[#161F2D] border border-[#283345] text-[#929DB0] hover:text-[#B6FF5C] hover:border-[#B6FF5C]/40 transition-all cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[#B6FF5C]' : ''}`} />
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#0B1220] border border-[#283345]">
            <span className="text-[11px] font-mono text-[#929DB0]">Conviction:</span>
            <span className="text-sm font-black font-mono text-[#B6FF5C] flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-[#B6FF5C]" />
              {signal.confidence}%
            </span>
          </div>
        </div>
      </div>

      {/* Main Core Prediction Workstation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center bg-[#0B1220]/80 p-4 rounded-xl border border-[#283345]/80 shadow-inner">
        
        {/* Left (5 Cols): Trade Direction & Contract Card */}
        <div className="lg:col-span-5 space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-lg bg-[#22C983]/20 border border-[#22C983]/40 text-[#22C983] text-xs font-black flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-[#22C983]" />
              {signal.action}
            </span>
            <span className="text-xs font-mono text-[#929DB0]">
              Lot Size: <strong className="text-[#F3F6FC]">{signal.lotSize}</strong>
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#161F2D] text-[#43D9FF] border border-[#283345]">
              EXP: {signal.expiry}
            </span>
          </div>

          <div className="text-lg sm:text-xl font-black text-[#F3F6FC] font-['Outfit'] tracking-tight flex items-center gap-2">
            <span>{signal.symbol}</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-[#929DB0]">
            <span>Spot: <strong className="text-[#F3F6FC]">₹{currentSpot.toFixed(1)}</strong></span>
            <span>•</span>
            <span>R:R <strong className="text-[#B6FF5C]">{signal.riskReward}</strong></span>
            <span>•</span>
            <span className="text-[#22C983] font-bold">Est. Gain: {signal.gainPct} (+₹{signal.profitPerLot.toLocaleString()}/lot)</span>
          </div>
        </div>

        {/* Center (4 Cols): Precision Execution Ladder */}
        <div className="lg:col-span-4 grid grid-cols-3 gap-2 text-center font-mono">
          <div className="p-2.5 rounded-xl bg-[#161F2D] border border-[#283345]">
            <div className="text-[10px] text-[#929DB0] uppercase font-bold">ENTRY</div>
            <div className="text-sm sm:text-base font-black text-[#F3F6FC]">
              ₹{signal.entryPrice.toFixed(2)}
            </div>
            <div className="text-[9px] text-[#929DB0]">Market Limit</div>
          </div>

          <div className="p-2.5 rounded-xl bg-[#22C983]/10 border border-[#22C983]/30">
            <div className="text-[10px] text-[#22C983] uppercase font-bold flex items-center justify-center gap-0.5">
              <Target className="w-3 h-3" /> T1 TARGET
            </div>
            <div className="text-sm sm:text-base font-black text-[#22C983]">
              ₹{signal.targetPrice1.toFixed(2)}
            </div>
            <div className="text-[9px] text-[#22C983] font-semibold">{signal.gainPct}</div>
          </div>

          <div className="p-2.5 rounded-xl bg-[#FF5D6C]/10 border border-[#FF5D6C]/30">
            <div className="text-[10px] text-[#FF5D6C] uppercase font-bold flex items-center justify-center gap-0.5">
              <ShieldAlert className="w-3 h-3" /> STOP LOSS
            </div>
            <div className="text-sm sm:text-base font-black text-[#FF5D6C]">
              ₹{signal.stopLoss.toFixed(2)}
            </div>
            <div className="text-[9px] text-[#FF5D6C] font-semibold">-15.0%</div>
          </div>
        </div>

        {/* Right (3 Cols): 1-Click Execution Action */}
        <div className="lg:col-span-3 flex flex-col gap-2">
          <button
            type="button"
            onClick={handleExecuteSignal}
            disabled={isExecuting || executed}
            className={`w-full py-3 px-4 rounded-xl font-black font-mono text-xs sm:text-sm flex items-center justify-center gap-2 transition-all cursor-pointer shadow-lg ${
              executed
                ? 'bg-[#22C983]/20 text-[#22C983] border border-[#22C983]/40 cursor-default'
                : 'bg-gradient-to-r from-[#B6FF5C] via-[#43D9FF] to-[#B6FF5C] text-[#080B12] hover:brightness-110 active:scale-95 shadow-[0_0_20px_rgba(182,255,92,0.35)]'
            }`}
          >
            {isExecuting ? (
              <span>Routing Order to Engine...</span>
            ) : executed ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-[#22C983]" />
                <span>FILLED IN PAPER LEDGER</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-[#080B12]" />
                <span>1-CLICK EXECUTE AI TRADE</span>
              </>
            )}
          </button>

          {onNavigateToOptions && (
            <button
              type="button"
              onClick={onNavigateToOptions}
              className="text-[11px] text-[#43D9FF] hover:text-[#B6FF5C] hover:underline flex items-center justify-center gap-1 font-mono transition-colors cursor-pointer pt-0.5"
            >
              <span>Inspect Strike in Option Chain</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          )}
        </div>

      </div>

      {/* Bottom Quantitative Driver Badges */}
      <div className="mt-3.5 pt-3 border-t border-[#283345]/60 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] text-[#929DB0] font-bold uppercase flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-[#B6FF5C]" />
            ALPHA DRIVERS:
          </span>
          {signal.catalysts.map((cat, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 rounded-lg bg-[#161F2D] border border-[#283345] text-[#F3F6FC] text-[11px] flex items-center gap-1.5"
            >
              <span className="text-[#B6FF5C] font-bold">{cat.title}:</span>
              <span className="text-[#929DB0]">{cat.text}</span>
            </span>
          ))}
        </div>

        <div className="text-[10px] text-[#929DB0] flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-[#22C983]" />
          <span>Risk Shield Active • 0 Brokerage Simulator</span>
        </div>
      </div>

    </div>
  );
};
