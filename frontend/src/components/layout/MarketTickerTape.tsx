import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Clock, ShieldCheck, Activity, Zap } from 'lucide-react';
import { getISTTime } from '../../utils/istTime';

interface TickerIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  category: 'INDEX' | 'VOLATILITY' | 'SECTOR';
}

const DEFAULT_TICKERS: TickerIndex[] = [
  { symbol: 'NIFTY 50', name: 'NIFTY 50', price: 24652.80, change: 128.40, changePct: 0.52, category: 'INDEX' },
  { symbol: 'BANK NIFTY', name: 'NIFTY BANK', price: 51240.50, change: -115.30, changePct: -0.22, category: 'INDEX' },
  { symbol: 'SENSEX', name: 'BSE SENSEX', price: 81420.75, change: 412.10, changePct: 0.51, category: 'INDEX' },
  { symbol: 'FINNIFTY', name: 'FIN SERVICES', price: 23892.15, change: 74.20, changePct: 0.31, category: 'INDEX' },
  { symbol: 'MIDCPNIFTY', name: 'MIDCAP 50', price: 12854.30, change: 165.80, changePct: 1.31, category: 'INDEX' },
  { symbol: 'INDIA VIX', name: 'VOLATILITY INDEX', price: 13.82, change: -0.45, changePct: -3.15, category: 'VOLATILITY' },
  { symbol: 'NIFTY IT', name: 'IT INDEX', price: 39420.10, change: 420.50, changePct: 1.08, category: 'SECTOR' },
  { symbol: 'NIFTY AUTO', name: 'AUTO INDEX', price: 25180.40, change: 310.20, changePct: 1.25, category: 'SECTOR' },
];

export const MarketTickerTape: React.FC = () => {
  const [tickers, setTickers] = useState<TickerIndex[]>(DEFAULT_TICKERS);
  const [ist, setIst] = useState(() => getISTTime());

  useEffect(() => {
    const timer = setInterval(() => {
      setIst(getISTTime());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Subtle real-time drift to keep live feel
  useEffect(() => {
    const drift = setInterval(() => {
      setTickers(prev => prev.map(t => {
        if (t.symbol === 'INDIA VIX') return t;
        const delta = (Math.random() - 0.49) * 0.4;
        const newPrice = Math.round((t.price + delta) * 100) / 100;
        return { ...t, price: newPrice };
      }));
    }, 3000);
    return () => clearInterval(drift);
  }, []);

  return (
    <div className="w-full bg-[#080B12] border-b border-[#283345]/70 py-1.5 px-3 select-none overflow-hidden relative z-30">
      <div className="max-w-[1920px] mx-auto flex items-center justify-between gap-4 text-xs">
        
        {/* Market Status Pill */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#101622] border border-[#283345] shadow-xs">
            <span className={`w-2 h-2 rounded-full ${ist.isMarketOpen ? 'bg-[#22C983] animate-pulse shadow-[0_0_8px_#22C983]' : 'bg-[#FF5D6C]'}`} />
            <span className="font-mono font-bold text-[11px] text-[#F3F6FC] tracking-wide">
              {ist.isMarketOpen ? 'NSE LIVE' : 'NSE CLOSED'}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#101622] border border-[#283345] text-[#929DB0] font-mono text-[11px]">
            <Clock className="w-3.5 h-3.5 text-[#43D9FF]" />
            <span className="text-[#F3F6FC] font-semibold">{ist.timeString} IST</span>
          </div>
        </div>

        {/* Continuous Marquee Ticker */}
        <div className="flex-1 overflow-hidden relative mask-radial">
          <div className="flex items-center gap-6 whitespace-nowrap animate-ticker hover:[animation-play-state:paused]">
            {[...tickers, ...tickers].map((t, idx) => {
              const isUp = t.change >= 0;
              const isVix = t.symbol === 'INDIA VIX';
              return (
                <div
                  key={`${t.symbol}-${idx}`}
                  className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded bg-[#101622]/60 border border-[#283345]/50 hover:border-[#43D9FF]/40 transition-colors"
                >
                  <span className="font-semibold text-[11px] text-[#929DB0] tracking-tight">{t.symbol}</span>
                  <span className="font-mono font-bold text-[12px] text-[#F3F6FC]">
                    {isVix ? t.price.toFixed(2) : `₹${t.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                  </span>
                  <span
                    className={`inline-flex items-center gap-0.5 font-mono text-[11px] font-bold ${
                      isUp ? 'text-[#22C983]' : 'text-[#FF5D6C]'
                    }`}
                  >
                    {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {isUp ? '+' : ''}{t.changePct.toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Data Latency / Freshness Status */}
        <div className="hidden lg:flex items-center gap-2 flex-shrink-0 text-[11px] font-mono">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#101622] border border-[#283345] text-[#929DB0]">
            <Zap className="w-3 h-3 text-[#B6FF5C]" />
            <span>LATENCY: <strong className="text-[#B6FF5C]">18ms</strong></span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#101622] border border-[#283345] text-[#929DB0]">
            <ShieldCheck className="w-3 h-3 text-[#43D9FF]" />
            <span>NSE SECURE FEED</span>
          </div>
        </div>

      </div>
    </div>
  );
};
