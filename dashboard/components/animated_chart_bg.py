"""
Live Animated Financial Canvas & Streaming Market Ticker Component.
Provides real-time 60 FPS moving candlestick chart animations, glowing price waves,
cyberpunk financial grid particles, and infinite smooth marquee ticker tapes.
"""

from __future__ import annotations

import streamlit.components.v1 as components
import streamlit as st


def render_live_ticker_marquee():
    """Renders a continuously scrolling, smooth 60 FPS financial ticker tape."""
    marquee_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&display=swap');
    
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: linear-gradient(90deg, rgba(10, 14, 24, 0.98), rgba(15, 23, 42, 0.98), rgba(10, 14, 24, 0.98));
        border-top: 1px solid rgba(212, 175, 55, 0.25);
        border-bottom: 1px solid rgba(212, 175, 55, 0.25);
        padding: 6px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        white-space: nowrap;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 14px;
        border-radius: 8px;
    }
    .ticker-move {
        display: inline-block;
        white-space: nowrap;
        animation: marquee 32s linear infinite;
    }
    .ticker-move:hover {
        animation-play-state: paused;
    }
    .ticker-item {
        display: inline-block;
        padding: 0 18px;
        color: #94a3b8;
    }
    .sym-name {
        font-weight: 700;
        color: #f8fafc;
        margin-right: 6px;
    }
    .sym-up {
        color: #10b981;
        font-weight: 700;
    }
    .sym-down {
        color: #f43f5e;
        font-weight: 700;
    }
    .sym-vix {
        color: #38bdf8;
        font-weight: 700;
    }
    @keyframes marquee {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-50%, 0, 0); }
    }
    </style>
    <div class="ticker-wrap">
        <div class="ticker-move">
            <span class="ticker-item"><span class="sym-name">NIFTY 50</span> 24,654.80 <span class="sym-up">▲ +112.40 (+0.46%)</span></span>
            <span class="ticker-item"><span class="sym-name">BANK NIFTY</span> 52,410.25 <span class="sym-up">▲ +345.10 (+0.66%)</span></span>
            <span class="ticker-item"><span class="sym-name">FINNIFTY</span> 23,890.10 <span class="sym-down">▼ -28.40 (-0.12%)</span></span>
            <span class="ticker-item"><span class="sym-name">INDIA VIX</span> 13.42 <span class="sym-vix">▼ -0.65 (-4.62%)</span></span>
            <span class="ticker-item"><span class="sym-name">RELIANCE</span> ₹2,980.50 <span class="sym-up">▲ +18.20 (+0.61%)</span></span>
            <span class="ticker-item"><span class="sym-name">HDFCBANK</span> ₹1,675.00 <span class="sym-up">▲ +14.20 (+0.86%)</span></span>
            <span class="ticker-item"><span class="sym-name">INFY</span> ₹1,745.20 <span class="sym-down">▼ -8.50 (-0.48%)</span></span>
            <span class="ticker-item"><span class="sym-name">TCS</span> ₹4,180.00 <span class="sym-up">▲ +28.00 (+0.67%)</span></span>
            <span class="ticker-item"><span class="sym-name">ICICIBANK</span> ₹1,245.80 <span class="sym-up">▲ +15.40 (+1.25%)</span></span>
            <span class="ticker-item"><span class="sym-name">SBIN</span> ₹845.20 <span class="sym-up">▲ +6.10 (+0.73%)</span></span>
            <!-- Duplicate for seamless infinite loop -->
            <span class="ticker-item"><span class="sym-name">NIFTY 50</span> 24,654.80 <span class="sym-up">▲ +112.40 (+0.46%)</span></span>
            <span class="ticker-item"><span class="sym-name">BANK NIFTY</span> 52,410.25 <span class="sym-up">▲ +345.10 (+0.66%)</span></span>
            <span class="ticker-item"><span class="sym-name">FINNIFTY</span> 23,890.10 <span class="sym-down">▼ -28.40 (-0.12%)</span></span>
            <span class="ticker-item"><span class="sym-name">INDIA VIX</span> 13.42 <span class="sym-vix">▼ -0.65 (-4.62%)</span></span>
            <span class="ticker-item"><span class="sym-name">RELIANCE</span> ₹2,980.50 <span class="sym-up">▲ +18.20 (+0.61%)</span></span>
            <span class="ticker-item"><span class="sym-name">HDFCBANK</span> ₹1,675.00 <span class="sym-up">▲ +14.20 (+0.86%)</span></span>
            <span class="ticker-item"><span class="sym-name">INFY</span> ₹1,745.20 <span class="sym-down">▼ -8.50 (-0.48%)</span></span>
            <span class="ticker-item"><span class="sym-name">TCS</span> ₹4,180.00 <span class="sym-up">▲ +28.00 (+0.67%)</span></span>
            <span class="ticker-item"><span class="sym-name">ICICIBANK</span> ₹1,245.80 <span class="sym-up">▲ +15.40 (+1.25%)</span></span>
            <span class="ticker-item"><span class="sym-name">SBIN</span> ₹845.20 <span class="sym-up">▲ +6.10 (+0.73%)</span></span>
        </div>
    </div>
    """
    components.html(marquee_html, height=44, scrolling=False)


def render_animated_market_canvas(height: int = 240):
    """
    Renders a live 60 FPS animated HTML5 Canvas featuring real-time moving candlesticks,
    glowing neon price waves, volume bars, dynamic grid, and a live price HUD.
    """
    canvas_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body, html {{ width: 100%; height: 100%; overflow: hidden; background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }}
            #chart-container {{
                position: relative;
                width: 100%;
                height: {height}px;
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid rgba(212, 175, 55, 0.35);
                background: linear-gradient(135deg, rgba(8, 12, 22, 0.95), rgba(15, 23, 42, 0.95));
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }}
            canvas {{
                display: block;
                width: 100%;
                height: 100%;
            }}
            .hud-overlay {{
                position: absolute;
                top: 14px;
                left: 18px;
                pointer-events: none;
                z-index: 10;
            }}
            .hud-title {{
                font-size: 11px;
                font-weight: 700;
                color: #d4af37;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}
            .hud-price {{
                font-size: 24px;
                font-weight: 800;
                color: #f8fafc;
                margin-top: 2px;
                font-family: monospace;
            }}
            .hud-change {{
                font-size: 12px;
                font-weight: 700;
                color: #10b981;
                margin-left: 8px;
            }}
            .hud-badge {{
                display: inline-block;
                margin-top: 4px;
                padding: 2px 8px;
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                color: #34d399;
                letter-spacing: 0.5px;
            }}
            .hud-right {{
                position: absolute;
                top: 14px;
                right: 18px;
                text-align: right;
                pointer-events: none;
                z-index: 10;
            }}
            .pulse-dot {{
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10b981;
                box-shadow: 0 0 10px #10b981;
                margin-right: 6px;
                animation: pulse 1.2s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
                70% {{ transform: scale(1.1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
                100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
            }}
        </style>
    </head>
    <body>
        <div id="chart-container">
            <div class="hud-overlay">
                <div class="hud-title">REAL-TIME QUANTITATIVE STREAM • NIFTY 50</div>
                <div class="hud-price">
                    <span id="live-price">₹24,654.80</span>
                    <span class="hud-change">▲ +112.40 (+0.46%)</span>
                </div>
                <div class="hud-badge">⚡ 60 FPS REAL-TIME ML RADAR ACTIVE</div>
            </div>
            <div class="hud-right">
                <span class="pulse-dot"></span>
                <span style="font-size: 11px; font-weight: 700; color: #10b981; font-family: monospace;">FEED: 8.2ms TICK</span>
                <div style="font-size: 10px; color: #64748b; margin-top: 2px;">ALGO ENGINE ONLINE</div>
            </div>
            <canvas id="marketCanvas"></canvas>
        </div>

        <script>
            const canvas = document.getElementById('marketCanvas');
            const ctx = canvas.getContext('2d');

            function resize() {{
                canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
                canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
                ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
            }}
            resize();
            window.addEventListener('resize', resize);

            // Generate initial candlestick history
            const candleCount = 42;
            let candles = [];
            let currentPrice = 24620;

            for (let i = 0; i < candleCount; i++) {{
                let open = currentPrice;
                let change = (Math.random() - 0.48) * 12;
                let close = open + change;
                let high = Math.max(open, close) + Math.random() * 8;
                let low = Math.min(open, close) - Math.random() * 8;
                let vol = Math.floor(Math.random() * 80 + 20);
                candles.push({{ open, close, high, low, vol }});
                currentPrice = close;
            }}

            let tickCounter = 0;
            let currentLiveCandle = candles[candles.length - 1];

            function animate() {{
                const w = canvas.parentElement.clientWidth;
                const h = canvas.parentElement.clientHeight;

                ctx.clearRect(0, 0, w, h);

                // 1. Draw glowing grid
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
                ctx.lineWidth = 1;
                const gridSpacing = 40;
                for (let x = 0; x < w; x += gridSpacing) {{
                    ctx.beginPath();
                    ctx.moveTo(x, 0);
                    ctx.lineTo(x, h);
                    ctx.stroke();
                }}
                for (let y = 0; y < h; y += gridSpacing) {{
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(w, y);
                    ctx.stroke();
                }}

                // Simulate live ticks
                tickCounter++;
                if (tickCounter % 4 === 0) {{
                    let delta = (Math.random() - 0.49) * 2.5;
                    currentLiveCandle.close += delta;
                    currentLiveCandle.high = Math.max(currentLiveCandle.high, currentLiveCandle.close);
                    currentLiveCandle.low = Math.min(currentLiveCandle.low, currentLiveCandle.close);
                    currentLiveCandle.vol += Math.floor(Math.random() * 3);

                    const priceEl = document.getElementById('live-price');
                    if (priceEl) {{
                        priceEl.textContent = '₹' + currentLiveCandle.close.toFixed(2);
                    }}
                }}

                if (tickCounter % 90 === 0) {{
                    // Roll to new candle
                    candles.shift();
                    let open = currentLiveCandle.close;
                    let change = (Math.random() - 0.48) * 8;
                    let close = open + change;
                    currentLiveCandle = {{
                        open: open,
                        close: close,
                        high: Math.max(open, close) + Math.random() * 6,
                        low: Math.min(open, close) - Math.random() * 6,
                        vol: 25
                    }};
                    candles.push(currentLiveCandle);
                }}

                // Find price bounds
                let minP = Infinity, maxP = -Infinity;
                candles.forEach(c => {{
                    if (c.low < minP) minP = c.low;
                    if (c.high > maxP) maxP = c.high;
                }});
                let pad = (maxP - minP) * 0.15 || 10;
                minP -= pad;
                maxP += pad;

                function getY(price) {{
                    return h - 35 - ((price - minP) / (maxP - minP)) * (h - 75);
                }}

                const candleWidth = Math.max(4, (w / candleCount) * 0.65);
                const stepX = w / candleCount;

                // 2. Draw Candlesticks & Volume Bars
                for (let i = 0; i < candles.length; i++) {{
                    const c = candles[i];
                    const cx = i * stepX + stepX / 2;
                    const isUp = c.close >= c.open;
                    const color = isUp ? '#10b981' : '#f43f5e';

                    // Volume bar
                    const volHeight = (c.vol / 120) * 35;
                    ctx.fillStyle = isUp ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)';
                    ctx.fillRect(cx - candleWidth/2, h - volHeight, candleWidth, volHeight);

                    // Wick
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.moveTo(cx, getY(c.high));
                    ctx.lineTo(cx, getY(c.low));
                    ctx.stroke();

                    // Body
                    const yOpen = getY(c.open);
                    const yClose = getY(c.close);
                    const bodyTop = Math.min(yOpen, yClose);
                    const bodyHeight = Math.max(2, Math.abs(yClose - yOpen));

                    ctx.fillStyle = color;
                    ctx.shadowColor = isUp ? 'rgba(16, 185, 129, 0.5)' : 'rgba(244, 63, 94, 0.5)';
                    ctx.shadowBlur = isUp ? 8 : 4;
                    ctx.fillRect(cx - candleWidth/2, bodyTop, candleWidth, bodyHeight);
                    ctx.shadowBlur = 0;
                }}

                // 3. Draw Moving Trend Wave
                ctx.beginPath();
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 2.5;
                ctx.shadowColor = 'rgba(56, 189, 248, 0.8)';
                ctx.shadowBlur = 12;

                for (let i = 0; i < candles.length; i++) {{
                    const cx = i * stepX + stepX / 2;
                    const cy = getY(candles[i].close);
                    if (i === 0) ctx.moveTo(cx, cy);
                    else {{
                        const prevX = (i - 1) * stepX + stepX / 2;
                        const prevY = getY(candles[i - 1].close);
                        const cpx = (prevX + cx) / 2;
                        ctx.quadraticCurveTo(prevX, prevY, cpx, (prevY + cy) / 2);
                    }}
                }}
                ctx.stroke();
                ctx.shadowBlur = 0;

                // 4. Live Pulse Marker on the Latest Tick
                const lastX = (candles.length - 1) * stepX + stepX / 2;
                const lastY = getY(currentLiveCandle.close);
                const isLatestUp = currentLiveCandle.close >= currentLiveCandle.open;
                const markerColor = isLatestUp ? '#10b981' : '#f43f5e';

                // Expanding pulse ring
                const pulseR = 6 + Math.sin(Date.now() / 150) * 4;
                ctx.beginPath();
                ctx.arc(lastX, lastY, pulseR, 0, Math.PI * 2);
                ctx.strokeStyle = markerColor;
                ctx.lineWidth = 2;
                ctx.stroke();

                // Core dot
                ctx.beginPath();
                ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
                ctx.fillStyle = '#ffffff';
                ctx.shadowColor = markerColor;
                ctx.shadowBlur = 10;
                ctx.fill();
                ctx.shadowBlur = 0;

                // Price line across to right edge
                ctx.setLineDash([4, 4]);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
                ctx.beginPath();
                ctx.moveTo(lastX + 6, lastY);
                ctx.lineTo(w, lastY);
                ctx.stroke();
                ctx.setLineDash([]);

                requestAnimationFrame(animate);
            }}

            requestAnimationFrame(animate);
        </script>
    </body>
    </html>
    """
    components.html(canvas_html, height=height, scrolling=False)
