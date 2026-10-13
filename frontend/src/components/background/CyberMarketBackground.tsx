import React, { useEffect, useRef } from 'react';
import { useTheme } from '../../context/ThemeContext';

interface CyberMarketBackgroundProps {
  isLowPerf?: boolean;
}

interface TelemetryTicker {
  x: number;
  y: number;
  vx: number;
  vy: number;
  text: string;
  color: string;
  alpha: number;
}

interface ChartNode {
  x: number;
  open: number;
  close: number;
  high: number;
  low: number;
  isUp: boolean;
}

export const CyberMarketBackground: React.FC<CyberMarketBackgroundProps> = ({ isLowPerf = false }) => {
  const { theme } = useTheme();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef<{ x: number; y: number }>({ x: -1000, y: -1000 });
  const themeRef = useRef(theme);

  useEffect(() => {
    themeRef.current = theme;
  }, [theme]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Institutional Financial Telemetry Pool
    const TICKER_POOL = [
      'NIFTY 24,652.80 ▲ +0.75%',
      'BANKNIFTY 51,240.50 ▲ +0.58%',
      'FINNIFTY 23,892.20 ▲ +0.34%',
      'PCR: 1.04 BULLISH',
      'IV: 13.82% REGIME: NORMAL',
      'MAX PAIN: 24,600',
      'AI TICK EXECUTION 0.8ms',
      'VWAP: ₹24,618.40',
      'CALL OI: 1.24M',
      'PUT OI: 1.18M',
      'SMART MONEY INFLOW +₹480Cr',
      'NSE CO-LO LATENCY: 0.2ms',
    ];

    const tickers: TelemetryTicker[] = [];
    const tickerCount = isLowPerf ? 8 : 16;

    for (let i = 0; i < tickerCount; i++) {
      tickers.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: -Math.random() * 0.35 - 0.1,
        text: TICKER_POOL[Math.floor(Math.random() * TICKER_POOL.length)],
        color: i % 2 === 0 ? '#B6FF5C' : '#43D9FF',
        alpha: Math.random() * 0.45 + 0.3,
      });
    }

    // Smooth wave nodes
    const slotWidth = 24;
    const numSlots = Math.ceil(width / slotWidth) + 8;
    const nodes: ChartNode[] = [];
    let curY = height * 0.52;

    for (let i = 0; i < numSlots; i++) {
      const isUp = Math.random() > 0.48;
      const bodyH = Math.random() * 18 + 4;
      const open = curY;
      const close = isUp ? open - bodyH : open + bodyH;
      const high = Math.min(open, close) - Math.random() * 8;
      const low = Math.max(open, close) + Math.random() * 8;
      nodes.push({
        x: i * slotWidth,
        open,
        close,
        high,
        low,
        isUp,
      });
      curY = close + (Math.random() - 0.5) * 10;
      if (curY < height * 0.28) curY += 18;
      if (curY > height * 0.72) curY -= 18;
    }

    let wavePhase = 0;
    let scrollOffset = 0;
    const scrollSpeed = isLowPerf ? 0.3 : 0.5;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const currentTheme = themeRef.current;

      // ─── 1. Deep Executive Backdrop Gradient ────────────────────────
      let bgGrad = ctx.createRadialGradient(width * 0.5, height * 0.35, 100, width * 0.5, height * 0.5, width * 0.85);
      if (currentTheme === 'royal_gold') {
        bgGrad.addColorStop(0, '#111520');
        bgGrad.addColorStop(0.45, '#0a0d16');
        bgGrad.addColorStop(1, '#05070c');
      } else if (currentTheme === 'obsidian_titanium') {
        bgGrad.addColorStop(0, '#0f1422');
        bgGrad.addColorStop(0.45, '#090d17');
        bgGrad.addColorStop(1, '#05070d');
      } else {
        bgGrad.addColorStop(0, '#0d181c');
        bgGrad.addColorStop(0.45, '#081014');
        bgGrad.addColorStop(1, '#04080a');
      }
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // ─── 2. Institutional Precision Grid ─────────────────────────────
      ctx.lineWidth = 1;
      const gridSize = 64;
      ctx.strokeStyle = currentTheme === 'royal_gold'
        ? 'rgba(212, 175, 55, 0.04)'
        : 'rgba(56, 189, 248, 0.04)';

      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // ─── 3. Subtle Ambient Light Halo ────────────────────────────────
      if (!isLowPerf) {
        const glowGrad = ctx.createRadialGradient(width * 0.5, height * 0.2, 50, width * 0.5, height * 0.2, 450);
        const glowColor = currentTheme === 'royal_gold'
          ? 'rgba(212, 175, 55, 0.08)'
          : currentTheme === 'obsidian_titanium'
          ? 'rgba(56, 189, 248, 0.08)'
          : 'rgba(16, 185, 129, 0.08)';
        glowGrad.addColorStop(0, glowColor);
        glowGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(width * 0.5, height * 0.2, 450, 0, Math.PI * 2);
        ctx.fill();
      }

      // ─── 4. Flowing Institutional Spline Wave ────────────────────────
      wavePhase += 0.012;
      scrollOffset += scrollSpeed;
      if (scrollOffset >= slotWidth) {
        scrollOffset -= slotWidth;
        const last = nodes[nodes.length - 1];
        const isUp = Math.random() > 0.48;
        const bodyH = Math.random() * 18 + 4;
        const open = last.close;
        const close = isUp ? open - bodyH : open + bodyH;
        nodes.shift();
        nodes.push({
          x: nodes[nodes.length - 1].x + slotWidth,
          open,
          close,
          high: Math.min(open, close) - Math.random() * 8,
          low: Math.max(open, close) + Math.random() * 8,
          isUp,
        });
        for (let i = 0; i < nodes.length; i++) {
          nodes[i].x = i * slotWidth;
        }
      }

      ctx.beginPath();
      let firstX = 0;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        const drawX = n.x - scrollOffset;
        const drawY = (n.open + n.close) / 2 + Math.sin(i * 0.1 + wavePhase) * 16;
        if (i === 0) {
          firstX = drawX;
          ctx.moveTo(drawX, drawY);
        } else {
          const prevN = nodes[i - 1];
          const prevX = prevN.x - scrollOffset;
          const prevY = (prevN.open + prevN.close) / 2 + Math.sin((i - 1) * 0.1 + wavePhase) * 16;
          const cpX = (prevX + drawX) / 2;
          ctx.quadraticCurveTo(prevX, prevY, cpX, (prevY + drawY) / 2);
        }
      }

      ctx.lineWidth = 1.8;
      ctx.strokeStyle = currentTheme === 'royal_gold'
        ? 'rgba(212, 175, 55, 0.3)'
        : 'rgba(56, 189, 248, 0.3)';
      ctx.stroke();

      // Shaded area under spline
      ctx.lineTo(width + 20, height);
      ctx.lineTo(firstX, height);
      ctx.closePath();
      const areaGrad = ctx.createLinearGradient(0, height * 0.45, 0, height);
      const areaColor = currentTheme === 'royal_gold'
        ? 'rgba(212, 175, 55, 0.04)'
        : 'rgba(56, 189, 248, 0.04)';
      areaGrad.addColorStop(0, areaColor);
      areaGrad.addColorStop(1, 'transparent');
      ctx.fillStyle = areaGrad;
      ctx.fill();

      // ─── 5. Executive Telemetry Micro-Labels ────────────────────────
      ctx.font = '10px "JetBrains Mono", monospace';
      for (const t of tickers) {
        t.x += t.vx;
        t.y += t.vy;

        if (t.y < -20) {
          t.y = height + 10;
          t.x = Math.random() * width;
        }
        if (t.x < -100) t.x = width + 50;
        if (t.x > width + 100) t.x = -50;

        ctx.fillStyle = t.color;
        ctx.globalAlpha = t.alpha * 0.45;
        ctx.fillText(t.text, t.x, t.y);
      }
      ctx.globalAlpha = 1.0;

      // ─── 6. Elegant Subtle Mouse Illumination ────────────────────────
      if (mouseRef.current.x > 0 && !isLowPerf) {
        const mouseGrad = ctx.createRadialGradient(
          mouseRef.current.x,
          mouseRef.current.y,
          0,
          mouseRef.current.x,
          mouseRef.current.y,
          220
        );
        mouseGrad.addColorStop(0, currentTheme === 'royal_gold' ? 'rgba(212, 175, 55, 0.06)' : 'rgba(56, 189, 248, 0.06)');
        mouseGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = mouseGrad;
        ctx.beginPath();
        ctx.arc(mouseRef.current.x, mouseRef.current.y, 220, 0, Math.PI * 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, [isLowPerf]);

  return (
    <>
      {/* 1. Stock Market Chart Candlestick Display Video Background */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 w-full h-full object-cover pointer-events-none opacity-20 mix-blend-screen z-0"
      >
        <source
          src="https://assets.mixkit.co/videos/preview/mixkit-stock-market-candlestick-chart-display-42021-large.mp4"
          type="video/mp4"
        />
      </video>

      {/* 2. Ambient Cyber Grid & Glow Orbs */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-gradient-to-r from-cyan-500/10 via-[#B6FF5C]/10 to-emerald-500/10 blur-[140px] rounded-full" />
      </div>

      {/* 3. 60 FPS Interactive Candlestick Canvas & Floating Telemetry */}
      <canvas
        ref={canvasRef}
        className="fixed inset-0 pointer-events-none z-0 w-full h-full"
        style={{ opacity: 0.9 }}
      />
    </>
  );
};
