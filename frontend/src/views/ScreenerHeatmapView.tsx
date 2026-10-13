import React, { useState, useMemo } from 'react';
import {
  Flame, Filter, Search, ArrowUpDown, TrendingUp, TrendingDown,
  Layers, ArrowUpRight, BarChart2, CheckCircle2, Sliders, RefreshCw, Sparkles
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { NavTab } from '../components/layout/Navigation';

interface ScreenerStock {
  symbol: string;
  name: string;
  sector: string;
  marketCap: 'LARGE' | 'MID' | 'SMALL';
  price: number;
  change: number;
  changePct: number;
  volume: string;
  rsi: number;
  ema20: number;
  peRatio: number;
  signal: 'STRONG BUY' | 'BUY' | 'NEUTRAL' | 'SELL';
  setup: string;
}

const STOCK_UNIVERSE: ScreenerStock[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd', sector: 'Energy', marketCap: 'LARGE', price: 2984.50, change: 22.80, changePct: 0.77, volume: '4.8M', rsi: 62.4, ema20: 2950.0, peRatio: 28.4, signal: 'BUY', setup: 'Breakout above 20 EMA' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'IT', marketCap: 'LARGE', price: 4210.30, change: 52.00, changePct: 1.25, volume: '2.1M', rsi: 68.2, ema20: 4120.0, peRatio: 32.1, signal: 'STRONG BUY', setup: 'Bullish Flag Breakout' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', sector: 'Banking', marketCap: 'LARGE', price: 1645.20, change: -7.50, changePct: -0.45, volume: '12.4M', rsi: 44.1, ema20: 1660.0, peRatio: 18.9, signal: 'NEUTRAL', setup: 'Consolidation at 200 EMA' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd', sector: 'Banking', marketCap: 'LARGE', price: 1224.50, change: 8.20, changePct: 0.67, volume: '8.3M', rsi: 58.7, ema20: 1210.0, peRatio: 17.5, signal: 'BUY', setup: 'Ascending Triangle' },
  { symbol: 'INFY', name: 'Infosys Ltd', sector: 'IT', marketCap: 'LARGE', price: 1890.60, change: 16.50, changePct: 0.88, volume: '5.2M', rsi: 61.3, ema20: 1860.0, peRatio: 29.8, signal: 'BUY', setup: 'MACD Golden Cross' },
  { symbol: 'TATAMOTORS', name: 'Tata Motors Ltd', sector: 'Auto', marketCap: 'LARGE', price: 968.40, change: 20.30, changePct: 2.14, volume: '9.6M', rsi: 74.2, ema20: 935.0, peRatio: 16.2, signal: 'STRONG BUY', setup: '52-Week High Surge' },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd', sector: 'Telecom', marketCap: 'LARGE', price: 1712.80, change: 24.10, changePct: 1.43, volume: '3.9M', rsi: 67.5, ema20: 1680.0, peRatio: 58.2, signal: 'BUY', setup: 'Momentum Continuation' },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical Ltd', sector: 'Pharma', marketCap: 'LARGE', price: 1845.00, change: -12.40, changePct: -0.67, volume: '1.8M', rsi: 49.0, ema20: 1855.0, peRatio: 38.6, signal: 'NEUTRAL', setup: 'Mean Reversion Support' },
  { symbol: 'MARUTI', name: 'Maruti Suzuki India Ltd', sector: 'Auto', marketCap: 'LARGE', price: 12450.00, change: 180.00, changePct: 1.47, volume: '0.8M', rsi: 64.9, ema20: 12200.0, peRatio: 27.3, signal: 'BUY', setup: 'Volume Expansion' },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking', marketCap: 'LARGE', price: 1782.10, change: -15.30, changePct: -0.85, volume: '3.4M', rsi: 38.2, ema20: 1810.0, peRatio: 21.0, signal: 'NEUTRAL', setup: 'Oversold RSI Reversal' },
  { symbol: 'TATASTEEL', name: 'Tata Steel Ltd', sector: 'Metals', marketCap: 'LARGE', price: 158.40, change: 3.20, changePct: 2.06, volume: '24.1M', rsi: 66.8, ema20: 152.0, peRatio: 42.1, signal: 'BUY', setup: 'Channel Breakout' },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance Ltd', sector: 'Banking', marketCap: 'LARGE', price: 7120.00, change: -45.00, changePct: -0.63, volume: '1.2M', rsi: 46.5, ema20: 7190.0, peRatio: 31.4, signal: 'NEUTRAL', setup: 'Support Retest' },
  { symbol: 'ZOMATO', name: 'Zomato Ltd', sector: 'Consumer', marketCap: 'MID', price: 274.50, change: 8.90, changePct: 3.35, volume: '35.4M', rsi: 78.4, ema20: 255.0, peRatio: 94.2, signal: 'STRONG BUY', setup: 'All-Time High Momentum' },
  { symbol: 'DIXON', name: 'Dixon Technologies Ltd', sector: 'Electronics', marketCap: 'MID', price: 13850.00, change: 420.00, changePct: 3.13, volume: '0.9M', rsi: 76.1, ema20: 13100.0, peRatio: 88.0, signal: 'STRONG BUY', setup: 'Earnings Momentum' },
  { symbol: 'POLYCAB', name: 'Polycab India Ltd', sector: 'Industrials', marketCap: 'MID', price: 6890.00, change: 110.00, changePct: 1.62, volume: '0.7M', rsi: 63.2, ema20: 6720.0, peRatio: 45.1, signal: 'BUY', setup: 'Cup and Handle' },
  { symbol: 'SUZLON', name: 'Suzlon Energy Ltd', sector: 'Energy', marketCap: 'SMALL', price: 78.20, change: 2.40, changePct: 3.17, volume: '48.9M', rsi: 71.0, ema20: 74.0, peRatio: 65.0, signal: 'BUY', setup: 'Clean Energy Breakout' },
];

const SECTOR_HEATMAP = [
  { sector: 'NIFTY IT', change: 1.18, marketCapWeight: '22%', color: '#22C983', leaders: 'TCS (+1.25%), INFY (+0.88%)' },
  { sector: 'NIFTY AUTO', change: 1.84, marketCapWeight: '14%', color: '#22C983', leaders: 'TATAMOTORS (+2.14%), MARUTI (+1.47%)' },
  { sector: 'NIFTY METAL', change: 1.56, marketCapWeight: '8%', color: '#22C983', leaders: 'TATASTEEL (+2.06%), JSWSTEEL (+1.2%)' },
  { sector: 'NIFTY ENERGY', change: 0.72, marketCapWeight: '18%', color: '#22C983', leaders: 'RELIANCE (+0.77%), ONGC (+0.95%)' },
  { sector: 'NIFTY PHARMA', change: -0.42, marketCapWeight: '10%', color: '#FF5D6C', leaders: 'SUNPHARMA (-0.67%), CIPLA (-0.3%)' },
  { sector: 'NIFTY BANK', change: -0.22, marketCapWeight: '28%', color: '#FF5D6C', leaders: 'ICICI (+0.67%), HDFC (-0.45%), KOTAK (-0.85%)' },
];

interface ScreenerHeatmapViewProps {
  onNavigateToTrade?: (symbol: string) => void;
  onNavigateToOptions?: () => void;
}

export const ScreenerHeatmapView: React.FC<ScreenerHeatmapViewProps> = ({
  onNavigateToTrade,
  onNavigateToOptions,
}) => {
  const { setSelectedSymbol } = useRealtimeMarket();
  const { openOrderModal } = usePaperTrading();

  const [search, setSearch] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');
  const [activePreset, setActivePreset] = useState<string>('ALL');
  const [sortField, setSortField] = useState<keyof ScreenerStock>('changePct');
  const [sortAsc, setSortAsc] = useState(false);

  // Filtered & Sorted stocks
  const filteredStocks = useMemo(() => {
    return STOCK_UNIVERSE.filter((stock) => {
      if (search.trim()) {
        const matchesQuery =
          stock.symbol.toLowerCase().includes(search.toLowerCase()) ||
          stock.name.toLowerCase().includes(search.toLowerCase());
        if (!matchesQuery) return false;
      }
      if (selectedSector !== 'ALL' && stock.sector.toLowerCase() !== selectedSector.toLowerCase()) {
        return false;
      }
      if (activePreset === 'MOMENTUM' && stock.changePct < 1.0) return false;
      if (activePreset === 'OVERSOLD' && stock.rsi > 45) return false;
      if (activePreset === 'HIGH_RSI' && stock.rsi < 65) return false;
      if (activePreset === 'STRONG_BUY' && stock.signal !== 'STRONG BUY') return false;
      return true;
    }).sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return 0;
    });
  }, [search, selectedSector, activePreset, sortField, sortAsc]);

  const handleSort = (field: keyof ScreenerStock) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const handleOpenTerminal = (stock: ScreenerStock) => {
    setSelectedSymbol(stock.symbol);
    if (onNavigateToTrade) {
      onNavigateToTrade(stock.symbol);
    }
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Header & Title ── */}
      <div className="p-5 rounded-2xl bg-[#101622] border border-[#283345] shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#B6FF5C]/15 border border-[#B6FF5C]/40 flex items-center justify-center text-[#B6FF5C]">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-black text-[#F3F6FC] font-['Outfit'] tracking-tight flex items-center gap-2">
              Indian Stock Screener & Sector Heatmap
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#B6FF5C]/15 text-[#B6FF5C] border border-[#B6FF5C]/30">
                LIVE SCAN
              </span>
            </h1>
            <p className="text-xs text-[#929DB0]">
              Quantitative momentum scanners, technical breakout filters & market breadth heatmap
            </p>
          </div>
        </div>

        {/* Global Search inside Screener */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#929DB0]" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search stock by symbol or name..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[#0B1220] border border-[#283345] text-xs text-[#F3F6FC] placeholder-[#929DB0] focus:border-[#43D9FF] focus:outline-none"
          />
        </div>
      </div>

      {/* ── 2. Sector Performance Heatmap ── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#929DB0]">
            NSE Sector Breadth Heatmap (Market Cap Weighted)
          </h2>
          <span className="text-[11px] font-mono text-[#43D9FF]">Click sector card to filter</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {SECTOR_HEATMAP.map((sec) => {
            const isUp = sec.change >= 0;
            const isSelected = selectedSector.toLowerCase() === sec.sector.replace('NIFTY ', '').toLowerCase();

            return (
              <button
                key={sec.sector}
                onClick={() => {
                  const cleaned = sec.sector.replace('NIFTY ', '');
                  setSelectedSector(selectedSector === cleaned ? 'ALL' : cleaned);
                }}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#161F2D] border-[#B6FF5C] shadow-[0_0_15px_rgba(182,255,92,0.15)]'
                    : 'bg-[#101622] border-[#283345] hover:border-[#43D9FF]/50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-[#F3F6FC]">{sec.sector}</span>
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                      isUp ? 'bg-[#22C983]/15 text-[#22C983]' : 'bg-[#FF5D6C]/15 text-[#FF5D6C]'
                    }`}
                  >
                    {isUp ? '+' : ''}{sec.change.toFixed(2)}%
                  </span>
                </div>
                <div className="text-[10px] text-[#929DB0] truncate">{sec.leaders}</div>
                <div className="text-[9px] font-mono text-[#5E697D] mt-1">Weight: {sec.marketCapWeight}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── 3. Filter Chips & Quick Presets ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-[#101622] border border-[#283345]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-[#929DB0] mr-1">PRESETS:</span>
          {[
            { id: 'ALL', label: 'All Stocks' },
            { id: 'STRONG_BUY', label: '🔥 Strong Buy Signals' },
            { id: 'MOMENTUM', label: '🚀 High Momentum (>1%)' },
            { id: 'HIGH_RSI', label: '📈 RSI Breakout (>65)' },
            { id: 'OVERSOLD', label: '🛡️ Oversold Reversal (<45)' },
          ].map((preset) => (
            <button
              key={preset.id}
              onClick={() => setActivePreset(preset.id)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activePreset === preset.id
                  ? 'bg-[#B6FF5C] text-[#080B12] font-bold shadow-sm'
                  : 'bg-[#0B1220] text-[#929DB0] hover:text-[#F3F6FC] border border-[#283345]'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {selectedSector !== 'ALL' && (
          <button
            onClick={() => setSelectedSector('ALL')}
            className="text-xs text-[#FF5D6C] hover:underline font-mono"
          >
            Clear Sector Filter ({selectedSector})
          </button>
        )}
      </div>

      {/* ── 4. Screener Financial Table ── */}
      <div className="rounded-2xl bg-[#101622] border border-[#283345] shadow-xl overflow-hidden">
        <div className="p-4 border-b border-[#283345] flex items-center justify-between">
          <div className="text-xs font-mono font-bold text-[#F3F6FC]">
            QUALIFIED CANDIDATES: <strong className="text-[#B6FF5C]">{filteredStocks.length}</strong>
          </div>
          <span className="text-[11px] font-mono text-[#929DB0]">
            Prices update continuously with NSE market tick
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#0B1220] border-b border-[#283345] text-[#929DB0] font-mono uppercase text-[11px]">
                <th className="py-3 px-4">Instrument</th>
                <th className="py-3 px-3">Sector</th>
                <th className="py-3 px-3 cursor-pointer hover:text-[#F3F6FC]" onClick={() => handleSort('price')}>
                  <div className="flex items-center gap-1">Price (₹) <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-3 cursor-pointer hover:text-[#F3F6FC]" onClick={() => handleSort('changePct')}>
                  <div className="flex items-center gap-1">1D Change <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-3 cursor-pointer hover:text-[#F3F6FC]" onClick={() => handleSort('rsi')}>
                  <div className="flex items-center gap-1">RSI (14) <ArrowUpDown className="w-3 h-3" /></div>
                </th>
                <th className="py-3 px-3">20 EMA</th>
                <th className="py-3 px-3">P/E</th>
                <th className="py-3 px-3">Quant Signal</th>
                <th className="py-3 px-3">Technical Setup</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#283345]/50 font-mono">
              {filteredStocks.map((stock) => {
                const isUp = stock.change >= 0;

                return (
                  <tr key={stock.symbol} className="hover:bg-[#161F2D]/60 transition-colors group">
                    <td className="py-3 px-4">
                      <div className="font-bold text-[#F3F6FC] font-['Outfit'] text-[13px]">{stock.symbol}</div>
                      <div className="text-[10px] text-[#929DB0] font-sans truncate max-w-[140px]">{stock.name}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-[#0B1220] border border-[#283345] text-[10px] text-[#929DB0]">
                        {stock.sector}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-bold text-[#F3F6FC]">
                      ₹{stock.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3 font-bold">
                      <span className={`inline-flex items-center gap-1 ${isUp ? 'text-[#22C983]' : 'text-[#FF5D6C]'}`}>
                        {isUp ? '+' : ''}{stock.changePct.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`font-semibold ${
                        stock.rsi >= 70 ? 'text-[#FF5D6C]' : stock.rsi <= 40 ? 'text-[#43D9FF]' : 'text-[#F3F6FC]'
                      }`}>
                        {stock.rsi.toFixed(1)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[#929DB0]">₹{stock.ema20.toFixed(1)}</td>
                    <td className="py-3 px-3 text-[#929DB0]">{stock.peRatio.toFixed(1)}x</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        stock.signal === 'STRONG BUY'
                          ? 'bg-[#B6FF5C]/20 text-[#B6FF5C] border border-[#B6FF5C]/40 shadow-xs'
                          : stock.signal === 'BUY'
                          ? 'bg-[#22C983]/15 text-[#22C983] border border-[#22C983]/30'
                          : 'bg-[#0B1220] text-[#929DB0] border border-[#283345]'
                      }`}>
                        {stock.signal}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-[11px] text-[#929DB0] font-sans">
                      {stock.setup}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleOpenTerminal(stock)}
                          className="px-2.5 py-1 rounded-md bg-[#161F2D] hover:bg-[#B6FF5C] text-[#F3F6FC] hover:text-[#080B12] border border-[#283345] hover:border-[#B6FF5C] font-semibold text-[11px] transition-all cursor-pointer"
                        >
                          Trade
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
