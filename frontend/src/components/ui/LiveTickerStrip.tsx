import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TickerItem {
  symbol: string;
  price: number;
  change: number;
  changePct: number;
}

interface LiveTickerStripProps {
  niftyPrice?: number;
  bankniftyPrice?: number;
}

export const LiveTickerStrip: React.FC<LiveTickerStripProps> = ({ niftyPrice = 24652.8, bankniftyPrice = 51240.5 }) => {
  const items: TickerItem[] = [
    { symbol: 'NIFTY 50', price: niftyPrice, change: 184.2, changePct: 0.75 },
    { symbol: 'BANK NIFTY', price: bankniftyPrice, change: 295.4, changePct: 0.58 },
    { symbol: 'INDIA VIX', price: 13.82, change: -0.44, changePct: -3.09 },
    { symbol: 'NIFTY IT', price: 35840.0, change: 412.3, changePct: 1.16 },
    { symbol: 'NIFTY FIN SVC', price: 21360.5, change: -48.2, changePct: -0.23 },
    { symbol: 'MIDCAP 100', price: 51206.0, change: 620.4, changePct: 1.23 },
    { symbol: 'NIFTY METAL', price: 8924.2, change: -112.4, changePct: -1.24 },
    { symbol: 'NIFTY PHARMA', price: 21048.5, change: 258.7, changePct: 1.24 },
    { symbol: 'FII NET', price: 0, change: 1842, changePct: 0 }, // crore
  ];

  const renderItem = (item: TickerItem, idx: number) => {
    const isUp = item.change > 0;
    const isFlat = item.change === 0;
    const color = isFlat ? 'var(--text-muted)' : isUp ? 'var(--emerald-accent)' : 'var(--rose-accent)';
    const Icon = isFlat ? Minus : isUp ? TrendingUp : TrendingDown;

    return (
      <div
        key={`${item.symbol}-${idx}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '0 24px',
          borderRight: '1px solid var(--border-0)',
          flexShrink: 0,
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)', letterSpacing: '0.06em', fontWeight: 600 }}>
          {item.symbol}
        </span>
        {item.symbol === 'FII NET' ? (
          <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: item.change > 0 ? 'var(--emerald-accent)' : 'var(--rose-accent)', fontWeight: 600 }}>
            {item.change > 0 ? '+' : ''}{new Intl.NumberFormat('en-IN').format(item.change)} Cr
          </span>
        ) : (
          <>
            <span style={{ fontSize: 12, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-primary)', fontWeight: 600 }}>
              {new Intl.NumberFormat('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(item.price)}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 3, color, fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }}>
              <Icon style={{ width: 10, height: 10 }} />
              {isUp ? '+' : ''}{item.changePct.toFixed(2)}%
            </span>
          </>
        )}
      </div>
    );
  };

  // Duplicate for seamless infinite scroll
  const allItems = [...items, ...items];

  return (
    <div style={{
      width: '100%',
      background: 'linear-gradient(135deg, var(--z2) 0%, var(--z1) 100%)',
      borderTop: '1px solid var(--border-0)',
      borderBottom: '1px solid var(--border-0)',
      overflow: 'hidden',
      position: 'relative',
      height: 36,
    }}>
      {/* Left + right gradient fade */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, bottom: 0,
        width: 80,
        background: 'linear-gradient(to right, var(--z2), transparent)',
        zIndex: 2,
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        top: 0, right: 0, bottom: 0,
        width: 80,
        background: 'linear-gradient(to left, var(--z1), transparent)',
        zIndex: 2,
        pointerEvents: 'none',
      }} />

      {/* Live dot */}
      <div style={{
        position: 'absolute',
        left: 16,
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 3,
        display: 'flex',
        alignItems: 'center',
        gap: 5,
      }}>
        <div className="animate-pulse-subtle" style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: 'var(--emerald-accent)',
          boxShadow: '0 0 6px rgba(16,185,129,0.6)',
        }} />
        <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono, monospace', color: 'var(--emerald-accent)', letterSpacing: '0.1em', fontWeight: 700 }}>
          LIVE
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', height: '100%', paddingLeft: 64 }}>
        <div className="ticker-track">
          {allItems.map((item, idx) => renderItem(item, idx))}
        </div>
      </div>
    </div>
  );
};
