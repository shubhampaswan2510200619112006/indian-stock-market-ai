import React, { useState, useMemo } from 'react';
import {
  TrendingUp, TrendingDown, Search, ArrowUpRight, ArrowDownRight,
  Layers, Sliders, ShieldCheck, Zap, Activity, Clock, BarChart2,
  CheckCircle2, AlertTriangle, Play, RefreshCw, Eye, Sparkles,
  Maximize2, Plus, DollarSign, ListOrdered, Briefcase, ChevronRight
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { usePaperTrading } from '../context/PaperTradingContext';
import { CandlestickChart } from '../components/market/CandlestickChart';
import { OptionChainTableDesk } from '../components/options/OptionChainTableDesk';
import { PortfolioDesk } from '../components/trading/PortfolioDesk';
import { MLEngineSignalCard } from '../components/trading/MLEngineSignalCard';
import { useToast } from '../components/ui/Toast';

interface TradingTerminalViewProps {
  onNavigateToOptions?: () => void;
}

type BottomTab = 'ORDERS' | 'POSITIONS' | 'OPTION_CHAIN' | 'AI_SIGNALS' | 'MARKET_DEPTH';

export const TradingTerminalView: React.FC<TradingTerminalViewProps> = ({
  onNavigateToOptions,
}) => {
  const {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    selectedExpiry,
    setSelectedExpiry,
    activeInstrument,
    chainRows,
    timeState,
    intradayCandles,
  } = useRealtimeMarket();

  const { account, openOrderModal, placeOrder } = usePaperTrading();
  const { addToast } = useToast();

  const [chartTimeframe, setChartTimeframe] = useState<string>('5m');
  const [watchlistTab, setWatchlistTab] = useState<'ALL' | 'INDICES' | 'F&O' | 'EQUITIES'>('ALL');
  const [watchlistSearch, setWatchlistSearch] = useState('');
  const [activeBottomTab, setActiveBottomTab] = useState<BottomTab>('ORDERS');

  // Quick Order Ticket State
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderProduct, setOrderProduct] = useState<'INTRADAY' | 'DELIVERY'>('INTRADAY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [orderQty, setOrderQty] = useState<number>(activeInstrument.lot_size || 25);
  const [limitPrice, setLimitPrice] = useState<number>(activeInstrument.spot_price || 24650);

  // Watchlist universe
  const watchlistUniverse = useMemo(() => [
    { symbol: 'NIFTY', name: 'NIFTY 50 Index', category: 'INDICES', price: instruments['NIFTY']?.spot_price || 24652.80, change: instruments['NIFTY']?.change || 128.40, changePct: instruments['NIFTY']?.change_pct || 0.52, volume: '142.8M' },
    { symbol: 'BANKNIFTY', name: 'NIFTY Bank Index', category: 'INDICES', price: instruments['BANKNIFTY']?.spot_price || 51240.50, change: instruments['BANKNIFTY']?.change || -115.30, changePct: instruments['BANKNIFTY']?.change_pct || -0.22, volume: '84.3M' },
    { symbol: 'FINNIFTY', name: 'NIFTY Fin Services', category: 'INDICES', price: instruments['FINNIFTY']?.spot_price || 23892.15, change: instruments['FINNIFTY']?.change || 74.20, changePct: instruments['FINNIFTY']?.change_pct || 0.31, volume: '32.1M' },
    { symbol: 'MIDCPNIFTY', name: 'NIFTY Midcap 50', category: 'INDICES', price: 12854.30, change: 165.80, changePct: 1.31, volume: '45.0M' },
    { symbol: 'SENSEX', name: 'BSE SENSEX Index', category: 'INDICES', price: 81420.75, change: 412.10, changePct: 0.51, volume: '68.4M' },
    { symbol: 'RELIANCE', name: 'Reliance Industries', category: 'F&O', price: 2984.50, change: 22.80, changePct: 0.77, volume: '4.8M' },
    { symbol: 'TCS', name: 'Tata Consultancy Services', category: 'F&O', price: 4210.30, change: 52.00, changePct: 1.25, volume: '2.1M' },
    { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', category: 'F&O', price: 1645.20, change: -7.50, changePct: -0.45, volume: '12.4M' },
    { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd', category: 'F&O', price: 1224.50, change: 8.20, changePct: 0.67, volume: '8.3M' },
    { symbol: 'INFY', name: 'Infosys Ltd', category: 'F&O', price: 1890.60, change: 16.50, changePct: 0.88, volume: '5.2M' },
    { symbol: 'TATAMOTORS', name: 'Tata Motors Ltd', category: 'EQUITIES', price: 968.40, change: 20.30, changePct: 2.14, volume: '9.6M' },
    { symbol: 'SUNPHARMA', name: 'Sun Pharma Ltd', category: 'EQUITIES', price: 1845.00, change: -12.40, changePct: -0.67, volume: '1.8M' },
  ], [instruments]);

  const filteredWatchlist = useMemo(() => {
    return watchlistUniverse.filter((item) => {
      if (watchlistTab !== 'ALL' && item.category !== watchlistTab) return false;
      if (watchlistSearch.trim()) {
        const query = watchlistSearch.toLowerCase();
        return item.symbol.toLowerCase().includes(query) || item.name.toLowerCase().includes(query);
      }
      return true;
    });
  }, [watchlistUniverse, watchlistTab, watchlistSearch]);

  // Market Depth Data (Level 2 Orderbook Ladder - Screenshot 2 style)
  const spot = activeInstrument.spot_price || 24652.80;
  const marketDepth = useMemo(() => {
    const bids = [
      { orders: 42, qty: 1850, price: Math.round((spot - 0.5) * 100) / 100 },
      { orders: 28, qty: 3200, price: Math.round((spot - 1.0) * 100) / 100 },
      { orders: 65, qty: 5400, price: Math.round((spot - 1.5) * 100) / 100 },
      { orders: 19, qty: 2100, price: Math.round((spot - 2.0) * 100) / 100 },
      { orders: 54, qty: 6800, price: Math.round((spot - 2.5) * 100) / 100 },
    ];
    const asks = [
      { orders: 35, qty: 1600, price: Math.round((spot + 0.5) * 100) / 100 },
      { orders: 41, qty: 2900, price: Math.round((spot + 1.0) * 100) / 100 },
      { orders: 58, qty: 4800, price: Math.round((spot + 1.5) * 100) / 100 },
      { orders: 22, qty: 1950, price: Math.round((spot + 2.0) * 100) / 100 },
      { orders: 60, qty: 7200, price: Math.round((spot + 2.5) * 100) / 100 },
    ];
    return { bids, asks };
  }, [spot]);

  const handleQuickPlaceOrder = async () => {
    const execPrice = orderType === 'MARKET' ? spot : limitPrice;
    const res = await placeOrder({
      symbol: `${activeInstrument.name} SPOT`,
      underlying: activeInstrument.name,
      strike: Math.round(spot),
      option_type: 'CE',
      expiry: 'INTRADAY',
      side: orderSide,
      product: orderProduct,
      order_type: orderType,
      quantity: orderQty,
      lots: Math.max(1, Math.round(orderQty / (activeInstrument.lot_size || 25))),
      lot_size: activeInstrument.lot_size || 25,
      price: execPrice,
      limit_price: orderType === 'LIMIT' ? limitPrice : undefined,
    });

    if (res.success) {
      addToast(`Order executed: ${orderSide} ${orderQty} ${activeInstrument.name} @ ₹${execPrice.toFixed(2)}`, 'success');
    } else {
      addToast(res.message || 'Order rejected: insufficient margin', 'error');
    }
  };

  const isUp = activeInstrument.change >= 0;

  return (
    <div className="space-y-4">
      
      {/* ── 1. Top Terminal Instrument Bar (HIXO Screenshot 1 Header) ── */}
      <div className="p-3.5 rounded-2xl bg-[#101622] border border-[#283345] shadow-xl flex flex-wrap items-center justify-between gap-4">
        
        {/* Left: Active Instrument & Live Price */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#161F2D] border border-[#283345] flex items-center justify-center font-bold text-[#F3F6FC] font-['Outfit'] text-sm">
              {activeInstrument.name.slice(0, 3)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold text-[#F3F6FC] font-['Outfit'] tracking-tight">
                  {activeInstrument.name}
                </h1>
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#161F2D] text-[#43D9FF] border border-[#283345]">
                  NSE
                </span>
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#B6FF5C]/15 text-[#B6FF5C] border border-[#B6FF5C]/30">
                  PAPER MODE
                </span>
              </div>
              <div className="text-[11px] font-mono text-[#929DB0]">
                Lot Size: {activeInstrument.lot_size} • Strike Step: {activeInstrument.strike_step} pts
              </div>
            </div>
          </div>

          <div className="h-8 w-px bg-[#283345] hidden sm:block" />

          {/* Price Metrics */}
          <div className="flex items-baseline gap-2.5 font-mono">
            <span className="text-xl font-extrabold text-[#F3F6FC] tracking-tight">
              ₹{spot.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className={`inline-flex items-center text-xs font-bold ${isUp ? 'text-[#22C983]' : 'text-[#FF5D6C]'}`}>
              {isUp ? <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> : <TrendingDown className="w-3.5 h-3.5 mr-0.5" />}
              {isUp ? '+' : ''}{activeInstrument.change.toFixed(2)} ({isUp ? '+' : ''}{activeInstrument.change_pct.toFixed(2)}%)
            </span>
          </div>

          <div className="hidden xl:flex items-center gap-4 text-[11px] font-mono text-[#929DB0] pl-2">
            <div>HIGH: <strong className="text-[#F3F6FC]">₹{(spot + 65.4).toFixed(2)}</strong></div>
            <div>LOW: <strong className="text-[#F3F6FC]">₹{(spot - 72.1).toFixed(2)}</strong></div>
            <div>PCR: <strong className={activeInstrument.pcr >= 1 ? 'text-[#22C983]' : 'text-[#F3F6FC]'}>{activeInstrument.pcr.toFixed(2)}</strong></div>
          </div>
        </div>

        {/* Right: Quick Action Buttons & Timeframe Selector */}
        <div className="flex items-center gap-3">
          
          {/* Timeframe Chips */}
          <div className="flex items-center bg-[#0B1220] p-1 rounded-xl border border-[#283345] text-xs font-mono font-bold">
            {['1m', '5m', '15m', '1h', '1D'].map((tf) => (
              <button
                key={tf}
                onClick={() => setChartTimeframe(tf)}
                className={`px-2.5 py-1 rounded-lg transition-all cursor-pointer ${
                  chartTimeframe === tf
                    ? 'bg-[#161F2D] text-[#B6FF5C] border border-[#B6FF5C]/30 shadow-xs'
                    : 'text-[#929DB0] hover:text-[#F3F6FC]'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Quick Buy / Sell Buttons (Screenshot 1 / HIXO style) */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => {
                setOrderSide('BUY');
                openOrderModal({
                  symbol: `${activeInstrument.name} SPOT`,
                  underlying: activeInstrument.name,
                  strike: Math.round(spot),
                  option_type: 'CE',
                  expiry: 'INTRADAY',
                  side: 'BUY',
                  product: 'INTRADAY',
                  order_type: 'MARKET',
                  quantity: activeInstrument.lot_size || 25,
                  lots: 1,
                  lot_size: activeInstrument.lot_size || 25,
                  price: spot,
                });
              }}
              className="px-4 py-2 rounded-xl bg-[#22C983] hover:bg-[#2fe699] text-[#080B12] font-black text-xs font-mono tracking-wide shadow-md transition-all cursor-pointer active:scale-95"
            >
              BUY
            </button>
            <button
              onClick={() => {
                setOrderSide('SELL');
                openOrderModal({
                  symbol: `${activeInstrument.name} SPOT`,
                  underlying: activeInstrument.name,
                  strike: Math.round(spot),
                  option_type: 'PE',
                  expiry: 'INTRADAY',
                  side: 'SELL',
                  product: 'INTRADAY',
                  order_type: 'MARKET',
                  quantity: activeInstrument.lot_size || 25,
                  lots: 1,
                  lot_size: activeInstrument.lot_size || 25,
                  price: spot,
                });
              }}
              className="px-4 py-2 rounded-xl bg-[#FF5D6C] hover:bg-[#ff7582] text-white font-black text-xs font-mono tracking-wide shadow-md transition-all cursor-pointer active:scale-95"
            >
              SELL
            </button>
          </div>

        </div>

      </div>

      {/* ── 2. Terminal Main Workstation Grid ── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
        
        {/* Left Column (3 Cols): Watchlist (HIXO Screenshot 1) */}
        <div className="xl:col-span-3 rounded-2xl bg-[#101622] border border-[#283345] shadow-xl p-3.5 space-y-3">
          
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[#F3F6FC] flex items-center gap-1.5">
              <span>WATCHLIST</span>
              <span className="text-[10px] text-[#929DB0]">({filteredWatchlist.length})</span>
            </h2>
            <div className="flex items-center gap-1 text-[10px] font-mono text-[#929DB0]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#22C983] animate-pulse" />
              <span>NSE STREAM</span>
            </div>
          </div>

          {/* Search box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[#929DB0]" />
            <input
              type="text"
              value={watchlistSearch}
              onChange={(e) => setWatchlistSearch(e.target.value)}
              placeholder="Search symbol..."
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC] placeholder-[#929DB0] focus:border-[#43D9FF] focus:outline-none"
            />
          </div>

          {/* Watchlist Tabs */}
          <div className="flex items-center bg-[#0B1220] p-0.5 rounded-lg border border-[#283345] text-[10px] font-mono font-bold">
            {(['ALL', 'INDICES', 'F&O', 'EQUITIES'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setWatchlistTab(tab)}
                className={`flex-1 py-1 rounded text-center transition-colors cursor-pointer ${
                  watchlistTab === tab
                    ? 'bg-[#161F2D] text-[#B6FF5C] border border-[#B6FF5C]/30'
                    : 'text-[#929DB0] hover:text-[#F3F6FC]'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Watchlist List */}
          <div className="space-y-1.5 max-h-[520px] overflow-y-auto scrollbar-none pr-0.5">
            {filteredWatchlist.map((item) => {
              const isSelected = selectedSymbol === item.symbol;
              const itemUp = item.change >= 0;

              return (
                <div
                  key={item.symbol}
                  onClick={() => {
                    if (instruments[item.symbol]) {
                      setSelectedSymbol(item.symbol);
                    }
                  }}
                  className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between group ${
                    isSelected
                      ? 'bg-[#161F2D] border-[#B6FF5C]/60 shadow-[0_0_15px_rgba(182,255,92,0.1)]'
                      : 'bg-[#0B1220]/60 border-[#283345]/60 hover:bg-[#161F2D]/50 hover:border-[#43D9FF]/40'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-[#F3F6FC] font-['Outfit'] text-xs">{item.symbol}</span>
                      <span className="text-[9px] font-mono text-[#5E697D] px-1 rounded bg-[#101622]">{item.category}</span>
                    </div>
                    <div className="text-[10px] font-mono text-[#929DB0]">{item.volume} vol</div>
                  </div>

                  <div className="text-right font-mono">
                    <div className="text-xs font-bold text-[#F3F6FC]">
                      ₹{item.price.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                    </div>
                    <div className={`text-[10px] font-semibold ${itemUp ? 'text-[#22C983]' : 'text-[#FF5D6C]'}`}>
                      {itemUp ? '+' : ''}{item.changePct.toFixed(2)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

        </div>

        {/* Center Column (6 Cols): Candlestick Chart */}
        <div className="xl:col-span-6 space-y-4">
          <CandlestickChart
            candles={intradayCandles}
            symbol={activeInstrument.name}
            timeframe={chartTimeframe}
            onTimeframeChange={setChartTimeframe}
            currentPrice={spot}
            istTime={timeState.timeWithMillis}
          />
        </div>

        {/* Right Column (3 Cols): Market Depth Level 2 & Quick Order Ticket (DXtrade Screenshot 2) */}
        <div className="xl:col-span-3 space-y-4">
          
          {/* Market Depth Level 2 Ladder */}
          <div className="rounded-2xl bg-[#101622] border border-[#283345] shadow-xl p-3.5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#283345]">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#F3F6FC] flex items-center gap-1.5">
                <BarChart2 className="w-3.5 h-3.5 text-[#43D9FF]" />
                LEVEL 2 MARKET DEPTH
              </span>
              <span className="text-[10px] font-mono text-[#929DB0]">SPREAD: 0.10</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              {/* Bids Column */}
              <div>
                <div className="flex justify-between text-[10px] text-[#929DB0] mb-1 font-semibold">
                  <span>ORDERS</span>
                  <span>BID (₹)</span>
                </div>
                <div className="space-y-1">
                  {marketDepth.bids.map((b, idx) => (
                    <div key={idx} className="flex justify-between items-center px-1.5 py-0.5 rounded bg-[#22C983]/10 text-[#22C983] border border-[#22C983]/20 text-[10px]">
                      <span className="text-[#929DB0]">{b.qty}</span>
                      <span className="font-bold">{b.price.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Asks Column */}
              <div>
                <div className="flex justify-between text-[10px] text-[#929DB0] mb-1 font-semibold">
                  <span>ASK (₹)</span>
                  <span>ORDERS</span>
                </div>
                <div className="space-y-1">
                  {marketDepth.asks.map((a, idx) => (
                    <div key={idx} className="flex justify-between items-center px-1.5 py-0.5 rounded bg-[#FF5D6C]/10 text-[#FF5D6C] border border-[#FF5D6C]/20 text-[10px]">
                      <span className="font-bold">{a.price.toFixed(2)}</span>
                      <span className="text-[#929DB0]">{a.qty}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Quick Order Pad Ticket */}
          <div className="rounded-2xl bg-[#101622] border border-[#283345] shadow-xl p-3.5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#283345]">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#F3F6FC]">
                QUICK ORDER TICKET
              </span>
              <span className="text-[10px] font-mono text-[#B6FF5C]">0 BROKERAGE</span>
            </div>

            {/* Buy / Sell selector */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setOrderSide('BUY')}
                className={`py-1.5 rounded-lg text-xs font-black font-mono transition-all cursor-pointer ${
                  orderSide === 'BUY'
                    ? 'bg-[#22C983] text-[#080B12] shadow-sm'
                    : 'bg-[#0B1220] text-[#929DB0] border border-[#283345]'
                }`}
              >
                BUY
              </button>
              <button
                onClick={() => setOrderSide('SELL')}
                className={`py-1.5 rounded-lg text-xs font-black font-mono transition-all cursor-pointer ${
                  orderSide === 'SELL'
                    ? 'bg-[#FF5D6C] text-white shadow-sm'
                    : 'bg-[#0B1220] text-[#929DB0] border border-[#283345]'
                }`}
              >
                SELL
              </button>
            </div>

            {/* Product & Order Type */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <label className="text-[10px] text-[#929DB0]">PRODUCT</label>
                <select
                  value={orderProduct}
                  onChange={(e) => setOrderProduct(e.target.value as any)}
                  className="w-full mt-0.5 px-2 py-1 rounded bg-[#0B1220] border border-[#283345] text-xs text-[#F3F6FC]"
                >
                  <option value="INTRADAY">MIS (Intraday)</option>
                  <option value="DELIVERY">CNC (Delivery)</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-[#929DB0]">TYPE</label>
                <select
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value as any)}
                  className="w-full mt-0.5 px-2 py-1 rounded bg-[#0B1220] border border-[#283345] text-xs text-[#F3F6FC]"
                >
                  <option value="MARKET">Market</option>
                  <option value="LIMIT">Limit</option>
                </select>
              </div>
            </div>

            {/* Quantity and Price */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <label className="text-[10px] text-[#929DB0]">QTY ({activeInstrument.lot_size}x)</label>
                <input
                  type="number"
                  value={orderQty}
                  onChange={(e) => setOrderQty(Math.max(1, Number(e.target.value)))}
                  step={activeInstrument.lot_size || 25}
                  className="w-full mt-0.5 px-2 py-1 rounded bg-[#0B1220] border border-[#283345] text-xs text-[#F3F6FC]"
                />
              </div>

              <div>
                <label className="text-[10px] text-[#929DB0]">PRICE (₹)</label>
                <input
                  type="number"
                  value={orderType === 'MARKET' ? spot : limitPrice}
                  disabled={orderType === 'MARKET'}
                  onChange={(e) => setLimitPrice(Number(e.target.value))}
                  className="w-full mt-0.5 px-2 py-1 rounded bg-[#0B1220] border border-[#283345] text-xs text-[#F3F6FC] disabled:opacity-60"
                />
              </div>
            </div>

            {/* Margin Info & Place Order button */}
            <div className="pt-2 border-t border-[#283345] space-y-2 font-mono">
              <div className="flex justify-between text-[11px] text-[#929DB0]">
                <span>Req. Margin:</span>
                <span className="text-[#F3F6FC] font-bold">
                  ₹{Math.round((spot * orderQty) / (orderProduct === 'INTRADAY' ? 5 : 1)).toLocaleString('en-IN')}
                </span>
              </div>

              <button
                onClick={handleQuickPlaceOrder}
                className={`w-full py-2 rounded-xl text-xs font-black tracking-wider transition-all cursor-pointer shadow-md ${
                  orderSide === 'BUY'
                    ? 'bg-[#22C983] hover:bg-[#2fe699] text-[#080B12]'
                    : 'bg-[#FF5D6C] hover:bg-[#ff7582] text-white'
                }`}
              >
                PLACE {orderSide} ORDER
              </button>
            </div>
          </div>

        </div>

      </div>

      {/* ── 3. Bottom Multi-Tab Console (HIXO Screenshot 1) ── */}
      <div className="rounded-2xl bg-[#101622] border border-[#283345] shadow-xl overflow-hidden">
        
        {/* Navigation Tabs Header */}
        <div className="flex items-center gap-1 bg-[#0B1220] border-b border-[#283345] px-4 pt-2 overflow-x-auto scrollbar-none text-xs font-mono font-bold">
          {[
            { id: 'ORDERS', label: 'ORDERS & EXECUTIONS', badge: account.orders.length },
            { id: 'POSITIONS', label: 'PORTFOLIO POSITIONS', badge: account.positions.length },
            { id: 'OPTION_CHAIN', label: 'OPTION CHAIN PREVIEW' },
            { id: 'AI_SIGNALS', label: 'AI ALPHA PREDICTIONS' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveBottomTab(tab.id as any)}
              className={`px-4 py-2.5 border-b-2 font-bold transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
                activeBottomTab === tab.id
                  ? 'border-[#B6FF5C] text-[#B6FF5C] bg-[#101622]'
                  : 'border-transparent text-[#929DB0] hover:text-[#F3F6FC]'
              }`}
            >
              <span>{tab.label}</span>
              {typeof tab.badge === 'number' && (
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-[#161F2D] text-[#43D9FF] border border-[#283345]">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content Panes */}
        <div className="p-4">
          {activeBottomTab === 'ORDERS' && (
            <div className="space-y-3 font-mono">
              {account.orders.length === 0 ? (
                <div className="text-center py-8 text-xs text-[#929DB0]">
                  No orders placed in this session. Use the order pad or buy/sell buttons to place paper trades.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="text-[#929DB0] border-b border-[#283345] text-[11px]">
                        <th className="py-2 px-3">Order ID</th>
                        <th className="py-2 px-3">Symbol</th>
                        <th className="py-2 px-3">Action</th>
                        <th className="py-2 px-3">Quantity</th>
                        <th className="py-2 px-3">Execution Price</th>
                        <th className="py-2 px-3">Status</th>
                        <th className="py-2 px-3">Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#283345]/50">
                      {account.orders.map((ord) => (
                        <tr key={ord.order_id} className="hover:bg-[#161F2D]/50 transition-colors">
                          <td className="py-2 px-3 text-[#929DB0]">#{ord.order_id.slice(-6)}</td>
                          <td className="py-2 px-3 font-bold text-[#F3F6FC]">{ord.symbol}</td>
                          <td className="py-2 px-3 font-bold">
                            <span className={ord.side === 'BUY' ? 'text-[#22C983]' : 'text-[#FF5D6C]'}>
                              {ord.side}
                            </span>
                          </td>
                          <td className="py-2 px-3">{ord.quantity}</td>
                          <td className="py-2 px-3">₹{ord.execution_price.toFixed(2)}</td>
                          <td className="py-2 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#22C983]/15 text-[#22C983] border border-[#22C983]/30">
                              {ord.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-[#929DB0]">{ord.timestamp_ist}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeBottomTab === 'POSITIONS' && (
            <PortfolioDesk compact={true} onNavigateToOptions={onNavigateToOptions} />
          )}

          {activeBottomTab === 'OPTION_CHAIN' && (
            <OptionChainTableDesk
              instrument={activeInstrument}
              instruments={instruments}
              selectedSymbol={selectedSymbol}
              onSelectSymbol={setSelectedSymbol}
              selectedExpiry={selectedExpiry}
              onSelectExpiry={setSelectedExpiry}
              rows={chainRows}
              compact={true}
            />
          )}

          {activeBottomTab === 'AI_SIGNALS' && (
            <MLEngineSignalCard
              currentSpot={spot}
              onNavigateToOptions={onNavigateToOptions}
            />
          )}
        </div>

      </div>

    </div>
  );
};
