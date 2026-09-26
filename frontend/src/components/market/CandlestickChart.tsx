import React, { useEffect, useRef, useState } from 'react';
import { Candle } from '../../types/market';
import { BarChart2, Eye, Sliders, Maximize2 } from 'lucide-react';

interface CandlestickChartProps {
  candles: Candle[];
  symbol: string;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
}

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  candles,
  symbol,
  timeframe,
  onTimeframeChange,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredCandle, setHoveredCandle] = useState<Candle | null>(null);
  const [showVwap, setShowVwap] = useState<boolean>(true);
  const [showSR, setShowSR] = useState<boolean>(true);

  // Generate synthetic candles if real candles are empty
  const displayCandles: Candle[] =
    candles && candles.length > 0
      ? candles
      : (() => {
          const list: Candle[] = [];
          let current = symbol.includes('BANK') ? 51200 : 24500;
          for (let i = 40; i >= 0; i--) {
            const date = new Date(Date.now() - i * 86400000);
            const delta = (Math.random() - 0.48) * 160;
            const open = current;
            const close = current + delta;
            const high = Math.max(open, close) + Math.random() * 80;
            const low = Math.min(open, close) - Math.random() * 80;
            const volume = 2000000 + Math.random() * 3000000;
            current = close;
            list.push({
              timestamp: date.toISOString().split('T')[0],
              open,
              high,
              low,
              close,
              volume,
              vwap: (open + high + low + close) / 4,
            });
          }
          return list;
        })();

  const timeframes = ['5m', '15m', '1h', '1D'];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear background
    ctx.fillStyle = '#060912';
    ctx.fillRect(0, 0, width, height);

    // Padding
    const pTop = 30;
    const pBottom = 70; // for volume & date
    const pRight = 65; // for price axis
    const pLeft = 10;

    const chartW = width - pLeft - pRight;
    const chartH = height - pTop - pBottom;
    const volH = 45;
    const volTop = height - pBottom + 10;

    if (displayCandles.length === 0) return;

    // Min & Max prices
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    let maxVol = 0;

    displayCandles.forEach((c) => {
      if (c.low < minPrice) minPrice = c.low;
      if (c.high > maxPrice) maxPrice = c.high;
      if (c.volume > maxVol) maxVol = c.volume;
    });

    const priceMargin = (maxPrice - minPrice) * 0.08 || 50;
    minPrice -= priceMargin;
    maxPrice += priceMargin;
    const priceRange = maxPrice - minPrice;

    // Price to Y coord
    const getY = (val: number) => pTop + chartH - ((val - minPrice) / priceRange) * chartH;
    // Vol to Y coord
    const getVolY = (vol: number) => volTop + volH - (vol / (maxVol || 1)) * volH;

    // Draw Grid Lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const p = minPrice + (priceRange / 5) * i;
      const y = getY(p);
      ctx.beginPath();
      ctx.moveTo(pLeft, y);
      ctx.lineTo(width - pRight, y);
      ctx.stroke();

      // Price labels on right
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(p.toFixed(1), width - pRight + 8, y + 3);
    }

    // Support & Resistance reference lines
    if (showSR && displayCandles.length > 5) {
      const resistance = maxPrice - priceMargin * 1.5;
      const support = minPrice + priceMargin * 1.5;

      // Resistance
      ctx.strokeStyle = 'rgba(244, 63, 94, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(pLeft, getY(resistance));
      ctx.lineTo(width - pRight, getY(resistance));
      ctx.stroke();
      ctx.fillStyle = '#f43f5e';
      ctx.fillText('R1 ' + resistance.toFixed(0), width - pRight + 8, getY(resistance) + 3);

      // Support
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
      ctx.beginPath();
      ctx.moveTo(pLeft, getY(support));
      ctx.lineTo(width - pRight, getY(support));
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = '#10b981';
      ctx.fillText('S1 ' + support.toFixed(0), width - pRight + 8, getY(support) + 3);
    }

    // Candle widths
    const count = displayCandles.length;
    const candleSlotW = chartW / count;
    const bodyW = Math.max(2, candleSlotW * 0.7);

    // Draw Candlesticks and Volume
    displayCandles.forEach((c, idx) => {
      const x = pLeft + idx * candleSlotW + candleSlotW / 2;
      const isUp = c.close >= c.open;
      const color = isUp ? '#10b981' : '#f43f5e';

      // 1. Volume Bar
      ctx.fillStyle = isUp ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)';
      const vy = getVolY(c.volume);
      ctx.fillRect(x - bodyW / 2, vy, bodyW, volTop + volH - vy);

      // 2. High-Low Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, getY(c.high));
      ctx.lineTo(x, getY(c.low));
      ctx.stroke();

      // 3. Open-Close Body
      const openY = getY(c.open);
      const closeY = getY(c.close);
      const topY = Math.min(openY, closeY);
      const barH = Math.max(2, Math.abs(closeY - openY));

      ctx.fillStyle = color;
      ctx.fillRect(x - bodyW / 2, topY, bodyW, barH);
    });

    // VWAP Line Overlay
    if (showVwap) {
      ctx.strokeStyle = '#d4af37';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      displayCandles.forEach((c, idx) => {
        const x = pLeft + idx * candleSlotW + candleSlotW / 2;
        const y = getY(c.vwap || (c.high + c.low + c.close) / 3);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
  }, [displayCandles, showVwap, showSR]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pLeft = 10;
    const pRight = 65;
    const chartW = rect.width - pLeft - pRight;
    const candleSlotW = chartW / displayCandles.length;

    const idx = Math.floor((x - pLeft) / candleSlotW);
    if (idx >= 0 && idx < displayCandles.length) {
      setHoveredCandle(displayCandles[idx]);
    }
  };

  const handleMouseLeave = () => {
    setHoveredCandle(null);
  };

  const currentCandle = hoveredCandle || displayCandles[displayCandles.length - 1];

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl overflow-hidden relative">
      {/* Top Header: Controls & Hover Values */}
      <div className="flex flex-wrap items-center justify-between p-4 border-b border-white/[0.06] bg-[#090e1c]/80 backdrop-blur-sm gap-3">
        {/* Ticker & Active Candle Readout */}
        <div className="flex flex-wrap items-center gap-4 font-mono text-xs">
          <div className="font-semibold text-slate-100 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-amber-400" />
            <span>{symbol} HISTORICAL & INTRADAY</span>
          </div>

          {currentCandle && (
            <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
              <span>
                DATE: <strong className="text-slate-200">{currentCandle.timestamp}</strong>
              </span>
              <span>
                O: <strong className="text-slate-200">{currentCandle.open.toFixed(1)}</strong>
              </span>
              <span>
                H: <strong className="text-emerald-400">{currentCandle.high.toFixed(1)}</strong>
              </span>
              <span>
                L: <strong className="text-rose-400">{currentCandle.low.toFixed(1)}</strong>
              </span>
              <span>
                C: <strong className="text-amber-300">{currentCandle.close.toFixed(1)}</strong>
              </span>
              <span>
                VOL:{' '}
                <strong className="text-slate-200">
                  {(currentCandle.volume / 1e6).toFixed(2)}M
                </strong>
              </span>
            </div>
          )}
        </div>

        {/* Timeframe & Overlays */}
        <div className="flex items-center gap-2 font-mono text-xs">
          {/* VWAP Toggle */}
          <button
            onClick={() => setShowVwap(!showVwap)}
            className={`px-2 py-1 rounded text-[11px] border transition-all ${
              showVwap
                ? 'bg-amber-400/20 text-amber-300 border-amber-400/40'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            VWAP
          </button>

          {/* S/R Toggle */}
          <button
            onClick={() => setShowSR(!showSR)}
            className={`px-2 py-1 rounded text-[11px] border transition-all ${
              showSR
                ? 'bg-blue-400/20 text-blue-300 border-blue-400/40'
                : 'bg-slate-900 text-slate-500 border-slate-800'
            }`}
          >
            S/R PIVOTS
          </button>

          {/* Timeframe Selector */}
          <div className="flex items-center bg-slate-900 p-0.5 rounded border border-slate-800">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(tf)}
                className={`px-2.5 py-1 rounded text-[11px] transition-all ${
                  timeframe === tf
                    ? 'bg-amber-400/20 text-amber-300 font-bold border border-amber-400/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* HTML5 Canvas Chart */}
      <div className="w-full h-[400px] relative">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          className="w-full h-full cursor-crosshair"
        />
      </div>

      {/* Footer status */}
      <div className="p-2.5 bg-[#05070c] border-t border-white/[0.04] flex items-center justify-between text-[10px] font-mono text-slate-500">
        <span>CANDLESTICKS WITH VOLUME HISTOGRAM & CONTINUOUS VWAP</span>
        <span className="text-slate-400">NSE DAILY & INTRADAY RESOLUTION</span>
      </div>
    </div>
  );
};
