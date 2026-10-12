import React, { useState } from 'react';
import {
  TrendingUp, TrendingDown, Search, ArrowRight, Layers,
  Compass, ShieldCheck, Activity, Sparkles, BarChart2,
  Clock, Zap, CheckCircle2, ChevronRight, PieChart, AlertCircle
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { PrecisionMarketClock } from '../components/market/PrecisionMarketClock';
import { CandlestickChart } from '../components/market/CandlestickChart';
import { useAnimatedNumber, formatIndian } from '../hooks/useAnimatedNumber';
import { NavTab } from '../components/layout/Navigation';

interface HomeMarketOverviewViewProps {
  onNavigate: (tab: NavTab) => void;
  onSelectSymbol?: (symbol: string) => void;
}

export const HomeMarketOverviewView: React.FC<HomeMarketOverviewViewProps> = ({
  onNavigate,
  onSelectSymbol,
}) => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    activeInstrument,
    timeState,
    intradayCandles,
  } = useRealtimeMarket();
  const { account } = usePaperTrading();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeMoverTab, setActiveMoverTab] = useState<'gainers' | 'losers' | 'volume'>('gainers');

  // Search filter
  const allSymbols = [
    { symbol: 'NIFTY', name: 'NIFTY 50 Index', category: 'INDEX', price: instruments['NIFTY']?.spot_price || 24652.8, changePct: instruments['NIFTY']?.change_pct || 0.52 },
    { symbol: 'BANKNIFTY', name: 'NIFTY Bank Index', category: 'INDEX', price: instruments['BANKNIFTY']?.spot_price || 51240.5, changePct: instruments['BANKNIFTY']?.change_pct || -0.22 },
    { symbol: 'FINNIFTY', name: 'NIFTY Financial Services', category: 'INDEX', price: instruments['FINNIFTY']?.spot_price || 23892.15, changePct: instruments['FINNIFTY']?.change_pct || 0.31 },
    { symbol: 'SENSEX', name: 'BSE SENSEX Index', category: 'INDEX', price: instruments['SENSEX']?.spot_price || 81420.75, changePct: instruments['SENSEX']?.change_pct || 0.51 },
    { symbol: 'RELIANCE', name: 'Reliance Industries Ltd', category: 'EQUITY', price: instruments['RELIANCE']?.spot_price || 2984.5, changePct: instruments['RELIANCE']?.change_pct || 0.77 },
    { symbol: 'TCS', name: 'Tata Consultancy Services', category: 'EQUITY', price: 4210.3, changePct: 1.25 },
    { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', category: 'EQUITY', price: 1645.2, changePct: -0.45 },
    { symbol: 'INFY', name: 'Infosys Ltd', category: 'EQUITY', price: 1890.6, changePct: 0.88 },
    { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd', category: 'EQUITY', price: 1224.5, changePct: 0.65 },
    { symbol: 'TATAMOTORS', name: 'Tata Motors Ltd', category: 'EQUITY', price: 968.4, changePct: 2.14 },
  ];

  const filteredSymbols = searchQuery.trim()
    ? allSymbols.filter(
        s => s.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
             s.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const handleSelectInstrument = (sym: string) => {
    if (instruments[sym]) {
      setSelectedSymbol(sym);
    }
    if (onSelectSymbol) onSelectSymbol(sym);
    setSearchQuery('');
  };

  const animSpot = useAnimatedNumber(activeInstrument.spot_price, 600);

  return (
    <div className="space-y-6">
      {/* ── 1. Top Market Session Header & Status Strip ── */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-4 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#d4af37]/30 to-amber-500/10 border border-[#d4af37]/40 flex items-center justify-center text-lg shadow-sm">
            🇮🇳
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-extrabold text-white font-['Outfit'] tracking-tight">
                Indian Financial Markets
              </h1>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold flex items-center gap-1.5 ${
                timeState.isMarketOpen ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${timeState.isMarketOpen ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
                {timeState.isMarketOpen ? 'NSE LIVE' : 'NSE CLOSED'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              National Stock Exchange of India (NSE) • Mumbai • Real-Time Derivatives
            </p>
          </div>
        </div>

        {/* Global Stock & Index Search */}
        <div className="relative w-full md:w-80">
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0d1424] border border-white/[0.12] focus-within:border-[#d4af37]/60 focus-within:shadow-[0_0_15px_rgba(212,175,55,0.15)] transition-all">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search NIFTY, RELIANCE, TCS..."
              className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full font-['Outfit']"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="text-xs text-slate-400 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* Search Results Dropdown */}
          {filteredSymbols.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 rounded-xl bg-[#0c1222] border border-white/[0.15] shadow-2xl p-2 z-50 max-h-64 overflow-y-auto backdrop-blur-2xl">
              {filteredSymbols.map((item) => (
                <button
                  key={item.symbol}
                  onClick={() => handleSelectInstrument(item.symbol)}
                  className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/[0.06] text-left transition-all cursor-pointer"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white font-mono">{item.symbol}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-white/[0.08] text-slate-400">{item.category}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">{item.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono font-bold text-white">₹{item.price.toFixed(2)}</div>
                    <div className={`text-[10px] font-mono font-bold ${item.changePct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {item.changePct >= 0 ? '+' : ''}{item.changePct.toFixed(2)}%
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── 2. Real-Time Index Tickers Grid ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.keys(instruments).map((sym) => {
          const inst = instruments[sym];
          const isSelected = selectedSymbol === sym;
          const isUp = inst.change >= 0;

          return (
            <div
              key={sym}
              onClick={() => setSelectedSymbol(sym)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer relative overflow-hidden backdrop-blur-xl ${
                isSelected
                  ? 'bg-gradient-to-br from-[#11192e] to-[#0c1222] border-[#d4af37]/60 shadow-[0_8px_30px_rgba(212,175,55,0.15)] ring-1 ring-[#d4af37]/40'
                  : 'bg-[#090d19]/80 border-white/[0.08] hover:border-white/[0.18] hover:bg-[#0d1426]'
              }`}
            >
              {isSelected && (
                <div className="absolute top-0 right-0 w-16 h-16 bg-[#d4af37]/10 rounded-bl-full pointer-events-none" />
              )}

              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-300 font-['Outfit'] tracking-wide">
                  {inst.name}
                </span>
                <span className={`text-[11px] font-mono font-extrabold px-2 py-0.5 rounded-full ${
                  isUp ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                }`}>
                  {isUp ? '+' : ''}{inst.change_pct.toFixed(2)}%
                </span>
              </div>

              <div className="text-2xl font-black font-mono text-white tracking-tight mb-2">
                ₹{inst.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
              </div>

              {/* Day Range Mini Bar */}
              <div className="space-y-1 pt-1 border-t border-white/[0.06]">
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                  <span>L: ₹{inst.low.toFixed(0)}</span>
                  <span>H: ₹{inst.high.toFixed(0)}</span>
                </div>
                <div className="w-full h-1 rounded-full bg-white/[0.08] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${isUp ? 'bg-emerald-400' : 'bg-rose-400'}`}
                    style={{
                      width: `${Math.max(5, Math.min(95, ((inst.spot_price - inst.low) / Math.max(1, inst.high - inst.low)) * 100))}%`
                    }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 mt-2 border-t border-white/[0.06] text-[10px] text-slate-400">
                <span>PCR: <strong className={inst.pcr >= 1 ? 'text-emerald-400' : 'text-slate-200'}>{inst.pcr.toFixed(2)}</strong></span>
                <span>Max Pain: <strong className="text-[#f6d776]">₹{inst.max_pain}</strong></span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── 3. Main Market Workspace Grid ── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Left 8 Columns: Live Market Chart & Market Movers */}
        <div className="xl:col-span-8 space-y-6">
          {/* Main Chart Panel */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-white/[0.08]">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-extrabold text-white font-['Outfit']">
                    {activeInstrument.name} Technical Trend
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/[0.06] text-slate-300">
                    5m Intraday
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Real-time algorithmic price feed with volume profile
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => onNavigate('explorer')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-xs font-bold text-white transition-all cursor-pointer border border-white/[0.1]"
                >
                  <BarChart2 className="w-3.5 h-3.5 text-[#d4af37]" />
                  <span>Full Explorer Desk</span>
                </button>
                <button
                  onClick={() => onNavigate('options')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#d4af37]/20 hover:bg-[#d4af37]/30 text-xs font-bold text-[#f6d776] border border-[#d4af37]/40 transition-all cursor-pointer shadow-sm"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Option Chain</span>
                </button>
              </div>
            </div>

            <CandlestickChart
              candles={intradayCandles}
              symbol={selectedSymbol}
              timeframe="5m"
            />
          </div>

          {/* Market Movers Tabs (Gainers, Losers, Active F&O) */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                NSE Market Movers & Derivatives Flow
              </h2>

              <div className="flex items-center bg-[#0d1424] p-1 rounded-xl border border-white/[0.08] text-xs">
                <button
                  onClick={() => setActiveMoverTab('gainers')}
                  className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                    activeMoverTab === 'gainers' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Top Gainers
                </button>
                <button
                  onClick={() => setActiveMoverTab('losers')}
                  className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                    activeMoverTab === 'losers' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Top Losers
                </button>
                <button
                  onClick={() => setActiveMoverTab('volume')}
                  className={`px-3 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                    activeMoverTab === 'volume' ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Most Active F&O
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {activeMoverTab === 'gainers' && [
                { symbol: 'TATAMOTORS', name: 'Tata Motors', price: 968.4, change: 20.3, pct: 2.14, oi: '+8.4%' },
                { symbol: 'TCS', name: 'TCS Ltd', price: 4210.3, change: 52.0, pct: 1.25, oi: '+12.1%' },
                { symbol: 'INFY', name: 'Infosys', price: 1890.6, change: 16.5, pct: 0.88, oi: '+5.7%' },
              ].map((stock) => (
                <div key={stock.symbol} className="p-3.5 rounded-xl bg-[#0d1424] border border-white/[0.06] hover:border-emerald-500/30 transition-all">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white text-xs font-mono">{stock.symbol}</span>
                    <span className="text-[11px] font-mono font-bold text-emerald-400">+{stock.pct}%</span>
                  </div>
                  <div className="text-base font-extrabold font-mono text-white">₹{stock.price.toFixed(2)}</div>
                  <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
                    <span>{stock.name}</span>
                    <span className="text-emerald-400/80">OI {stock.oi}</span>
                  </div>
                </div>
              ))}

              {activeMoverTab === 'losers' && [
                { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 1645.2, change: -7.5, pct: -0.45, oi: '-3.2%' },
                { symbol: 'AXISBANK', name: 'Axis Bank', price: 1180.0, change: -8.2, pct: -0.69, oi: '+2.1%' },
                { symbol: 'KOTAKBANK', name: 'Kotak Bank', price: 1740.5, change: -14.0, pct: -0.80, oi: '+4.5%' },
              ].map((stock) => (
                <div key={stock.symbol} className="p-3.5 rounded-xl bg-[#0d1424] border border-white/[0.06] hover:border-rose-500/30 transition-all">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white text-xs font-mono">{stock.symbol}</span>
                    <span className="text-[11px] font-mono font-bold text-rose-400">{stock.pct}%</span>
                  </div>
                  <div className="text-base font-extrabold font-mono text-white">₹{stock.price.toFixed(2)}</div>
                  <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
                    <span>{stock.name}</span>
                    <span className="text-rose-400/80">OI {stock.oi}</span>
                  </div>
                </div>
              ))}

              {activeMoverTab === 'volume' && [
                { symbol: 'NIFTY 24650 CE', name: 'Call Strike', price: 138.5, change: 18.2, pct: 15.1, oi: '1.24M Lots' },
                { symbol: 'NIFTY 24650 PE', name: 'Put Strike', price: 122.0, change: -12.4, pct: -9.2, oi: '1.17M Lots' },
                { symbol: 'BANKNIFTY 51200 CE', name: 'Call Strike', price: 285.0, change: -24.0, pct: -7.7, oi: '840K Lots' },
              ].map((stock) => (
                <div key={stock.symbol} className="p-3.5 rounded-xl bg-[#0d1424] border border-white/[0.06] hover:border-[#d4af37]/30 transition-all">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white text-xs font-mono">{stock.symbol}</span>
                    <span className={`text-[11px] font-mono font-bold ${stock.pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {stock.pct >= 0 ? '+' : ''}{stock.pct}%
                    </span>
                  </div>
                  <div className="text-base font-extrabold font-mono text-white">₹{stock.price.toFixed(2)}</div>
                  <div className="text-[10px] text-slate-400 mt-1 flex justify-between">
                    <span>{stock.name}</span>
                    <span className="text-[#f6d776]">{stock.oi}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 4 Columns: Fast Launchpad & Simulated Portfolio Overview */}
        <div className="xl:col-span-4 space-y-6">
          {/* Quick Action Navigation Launchpad */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-[#d4af37]/25 backdrop-blur-xl shadow-xl">
            <h2 className="text-sm font-extrabold text-white font-['Outfit'] uppercase tracking-wider mb-3 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#d4af37]" />
              Platform Workspaces
            </h2>

            <div className="space-y-2.5">
              <button
                onClick={() => onNavigate('options')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-[#0d1424] hover:bg-[#121c33] border border-white/[0.08] hover:border-[#d4af37]/50 transition-all text-left cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#d4af37]/15 flex items-center justify-center text-[#f6d776]">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white group-hover:text-[#f6d776] transition-colors">
                      Options Chain Desk
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Greeks, strike matrix, PCR & live order pad
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
              </button>

              <button
                onClick={() => onNavigate('ai-analyst')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-[#0d1424] hover:bg-[#121c33] border border-white/[0.08] hover:border-emerald-500/50 transition-all text-left cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center text-emerald-400">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white group-hover:text-emerald-400 transition-colors">
                      AI Market Analyst
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Quantitative insights & institutional bias
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
              </button>

              <button
                onClick={() => onNavigate('strategy-lab')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-[#0d1424] hover:bg-[#121c33] border border-white/[0.08] hover:border-sky-500/50 transition-all text-left cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-sky-500/15 flex items-center justify-center text-sky-400">
                    <PieChart className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white group-hover:text-sky-400 transition-colors">
                      Strategy Lab & Backtesting
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Spreads, straddles & payoff diagrams
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
              </button>

              <button
                onClick={() => onNavigate('paper-trading')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-[#0d1424] hover:bg-[#121c33] border border-white/[0.08] hover:border-purple-500/50 transition-all text-left cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/15 flex items-center justify-center text-purple-400">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white group-hover:text-purple-400 transition-colors">
                      Paper Trading Portal
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Simulated portfolio, orders & risk controls
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
              </button>
            </div>
          </div>

          {/* User Paper Account Summary Widget */}
          <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
                Simulated Account
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-bold border border-emerald-500/30">
                PAPER ACTIVE
              </span>
            </div>

            <div className="text-2xl font-black font-mono text-white mb-1">
              ₹{account.portfolio_value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-400 mb-4 flex items-center gap-1.5">
              <span>Available Cash:</span>
              <strong className="text-white font-mono">₹{account.available_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-3 border-t border-white/[0.08] text-xs">
              <div className="p-2.5 rounded-xl bg-[#0d1424]">
                <div className="text-[10px] text-slate-400">Open Positions</div>
                <div className="text-sm font-bold text-white font-mono">{account.positions.length}</div>
              </div>
              <div className="p-2.5 rounded-xl bg-[#0d1424]">
                <div className="text-[10px] text-slate-400">Total Orders</div>
                <div className="text-sm font-bold text-white font-mono">{account.orders.length}</div>
              </div>
            </div>

            <button
              onClick={() => onNavigate('paper-trading')}
              className="w-full mt-4 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-xs font-bold text-white transition-all cursor-pointer border border-white/[0.1] text-center"
            >
              Open Paper Trading Terminal →
            </button>
          </div>

          {/* Safety Invariant Notice */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300/90 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-amber-300">SEBI Compliant Paper Trading:</strong> Real-money broker order routing is architecturally disabled. All simulations run on real-time and delayed NSE feeds.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
