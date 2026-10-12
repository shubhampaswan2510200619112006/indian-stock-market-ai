import React, { useState } from 'react';
import {
  Bookmark, Plus, Trash2, ArrowUpRight, TrendingUp, TrendingDown,
  Layers, Wallet, PieChart, ShieldCheck, Activity, BarChart2
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { NavTab } from '../components/layout/Navigation';

interface WatchlistPortfolioViewProps {
  onNavigateToOptions?: () => void;
  onNavigateToExplorer?: () => void;
}

interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  lotSize: number;
}

export const WatchlistPortfolioView: React.FC<WatchlistPortfolioViewProps> = ({
  onNavigateToOptions,
  onNavigateToExplorer,
}) => {
  const { instruments, setSelectedSymbol } = useRealtimeMarket();
  const { account, openOrderModal } = usePaperTrading();

  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([
    { symbol: 'NIFTY', name: 'NIFTY 50 Index', price: 24652.8, change: 128.4, changePct: 0.52, lotSize: 25 },
    { symbol: 'BANKNIFTY', name: 'NIFTY Bank Index', price: 51240.5, change: -115.3, changePct: -0.22, lotSize: 15 },
    { symbol: 'FINNIFTY', name: 'NIFTY Financial Services', price: 23892.15, change: 74.2, changePct: 0.31, lotSize: 25 },
    { symbol: 'RELIANCE', name: 'Reliance Industries', price: 2984.5, change: 22.8, changePct: 0.77, lotSize: 250 },
    { symbol: 'TCS', name: 'Tata Consultancy Services', price: 4210.3, change: 52.0, changePct: 1.25, lotSize: 175 },
    { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', price: 1645.2, change: -7.5, changePct: -0.45, lotSize: 550 },
    { symbol: 'TATAMOTORS', name: 'Tata Motors Ltd', price: 968.4, change: 20.3, changePct: 2.14, lotSize: 1425 },
  ]);

  const handleRemove = (sym: string) => {
    setWatchlist(prev => prev.filter(item => item.symbol !== sym));
  };

  const handleQuickTrade = (item: WatchlistItem) => {
    if (instruments[item.symbol]) {
      setSelectedSymbol(item.symbol);
    }
    openOrderModal({
      symbol: `${item.name} (Paper Spot)`,
      underlying: item.name,
      strike: item.price,
      option_type: 'CE',
      expiry: '17 OCT 2026',
      side: 'BUY',
      product: 'INTRADAY',
      order_type: 'MARKET',
      quantity: item.lotSize,
      lots: 1,
      lot_size: item.lotSize,
      price: item.price,
    });
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Top Header ── */}
      <div className="p-4 rounded-2xl bg-[#080d19]/95 border border-white/[0.08] backdrop-blur-xl shadow-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/40 flex items-center justify-center text-amber-400">
            <Bookmark className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-black text-white font-['Outfit'] tracking-tight">
              Watchlists & Portfolio Analytics
            </h1>
            <p className="text-xs text-slate-400">
              Personalized instrument tracking, allocation breakdowns & simulated equity curves
            </p>
          </div>
        </div>
      </div>

      {/* ── 2. Main Grid ── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Left 8 Cols: Watchlist Table */}
        <div className="xl:col-span-8 p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.08]">
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider">
              Primary Watchlist ({watchlist.length} Instruments)
            </h2>
            <span className="text-xs font-mono text-slate-400">NSE Spot Feeds</span>
          </div>

          <div className="divide-y divide-white/[0.06]">
            {watchlist.map((item) => {
              const isUp = item.change >= 0;
              return (
                <div
                  key={item.symbol}
                  className="py-3.5 flex flex-wrap items-center justify-between gap-3 hover:bg-white/[0.02] px-2 rounded-xl transition-all"
                >
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleRemove(item.symbol)}
                      className="text-slate-500 hover:text-rose-400 text-xs p-1"
                      title="Remove from watchlist"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-extrabold text-white font-mono">{item.symbol}</span>
                        <span className="text-[10px] text-slate-400 font-mono">Lot: {item.lotSize}</span>
                      </div>
                      <div className="text-xs text-slate-400">{item.name}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-sm font-black font-mono text-white">
                        ₹{item.price.toLocaleString('en-IN', { minimumFractionDigits: 1 })}
                      </div>
                      <div className={`text-[11px] font-mono font-bold ${isUp ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isUp ? '+' : ''}{item.change.toFixed(1)} ({isUp ? '+' : ''}{item.changePct.toFixed(2)}%)
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleQuickTrade(item)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-400 text-xs font-bold transition-all cursor-pointer"
                      >
                        Trade
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 4 Cols: Portfolio Allocation & Risk Invariants */}
        <div className="xl:col-span-4 space-y-6">
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl space-y-4">
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider">
              Asset Allocation Breakdown
            </h2>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Available Liquid Cash:</span>
                <span className="font-bold text-white">
                  ₹{account.available_balance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Blocked Margin:</span>
                <span className="font-bold text-[#f6d776]">
                  ₹{account.invested_margin.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#0c1222]">
                <span className="text-slate-400">Total Account Value:</span>
                <span className="font-extrabold text-emerald-400">
                  ₹{account.portfolio_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl space-y-3">
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Risk Limits & Governance
            </h2>

            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span>Max Daily Loss Limit:</span>
                <strong className="font-mono text-rose-400">5.0% (₹50,000)</strong>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span>Max Risk Per Trade:</span>
                <strong className="font-mono text-[#f6d776]">2.0% (₹20,000)</strong>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.04]">
                <span>Max Open Positions:</span>
                <strong className="font-mono text-white">5 Contracts</strong>
              </div>
              <div className="flex justify-between py-1">
                <span>SEBI Broker Routing:</span>
                <strong className="font-mono text-emerald-400">DISABLED (PAPER ONLY)</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
