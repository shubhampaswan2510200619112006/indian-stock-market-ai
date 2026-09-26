import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, RefreshCw, AlertTriangle, TrendingUp, Activity } from 'lucide-react';

interface AIInsightProps {
  regime?: string;
  pcr?: number;
  iv?: number;
  adx?: number;
  className?: string;
}

interface Insight {
  text: string;
  category: 'volatility' | 'flow' | 'momentum' | 'caution';
  confidence: number;
}

function generateInsight(regime?: string, pcr?: number, iv?: number, adx?: number): Insight {
  const insights: Insight[] = [];

  if (iv !== undefined) {
    if (iv > 18) insights.push({ text: 'IV percentile elevated — consider short vega strategies for premium collection.', category: 'volatility', confidence: 0.71 });
    else if (iv < 12) insights.push({ text: 'Compressed IV environment — long vega positions may benefit from mean reversion.', category: 'volatility', confidence: 0.68 });
    else insights.push({ text: 'IV smile in normal regime — skew differential between OTM puts and calls remains structurally premium.', category: 'volatility', confidence: 0.63 });
  }

  if (pcr !== undefined) {
    if (pcr > 1.2) insights.push({ text: `PCR at ${pcr.toFixed(2)} signals put-heavy positioning — contrarian bullish bias historically elevated.`, category: 'flow', confidence: 0.66 });
    else if (pcr < 0.7) insights.push({ text: `PCR at ${pcr.toFixed(2)} — call overwriting dominance. Potential resistance near max pain strike.`, category: 'flow', confidence: 0.64 });
    else insights.push({ text: `PCR ${pcr.toFixed(2)} balanced — institutional flow split. Max pain level acts as gravitational anchor.`, category: 'flow', confidence: 0.58 });
  }

  if (adx !== undefined) {
    if (adx > 25) insights.push({ text: `ADX ${adx.toFixed(1)} — directional trend confirmed. Momentum strategies favoured over mean-reversion.`, category: 'momentum', confidence: 0.72 });
    else insights.push({ text: `ADX ${adx.toFixed(1)} — rangebound structure. Defined-risk spreads and iron condors statistically preferred.`, category: 'momentum', confidence: 0.65 });
  }

  if (regime === 'RANGE') insights.push({ text: 'Range regime detected — short gamma strategies structurally advantaged until breakout signal.', category: 'caution', confidence: 0.60 });
  if (regime === 'BREAKOUT') insights.push({ text: 'Breakout regime — directional bias increasing. Tail risk exposure warrants wider stops.', category: 'caution', confidence: 0.69 });
  if (regime === 'HIGH_VOLATILITY') insights.push({ text: 'High volatility regime active — defined-risk structures only. Raw naked exposure architecturally blocked.', category: 'caution', confidence: 0.82 });

  insights.push({
    text: 'Research baseline: 0/8 hypotheses survived full transaction friction. All signals are observational — not executable edges.',
    category: 'caution',
    confidence: 1.0,
  });

  const idx = Math.floor(Date.now() / 8000) % insights.length;
  return insights[idx];
}

const CATEGORY_CONFIG = {
  volatility: { icon: Activity, color: 'var(--cyan-accent)', label: 'VOLATILITY' },
  flow: { icon: TrendingUp, color: 'var(--emerald-accent)', label: 'FLOW' },
  momentum: { icon: TrendingUp, color: 'var(--gold-primary)', label: 'MOMENTUM' },
  caution: { icon: AlertTriangle, color: 'var(--rose-accent)', label: 'CAUTION' },
};

export const AIInsightCard: React.FC<AIInsightProps> = ({ regime, pcr, iv, adx, className = '' }) => {
  const [insight, setInsight] = useState<Insight>(() => generateInsight(regime, pcr, iv, adx));
  const [key, setKey] = useState(0);

  // Rotate insight every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setInsight(generateInsight(regime, pcr, iv, adx));
      setKey(k => k + 1);
    }, 10000);
    return () => clearInterval(interval);
  }, [regime, pcr, iv, adx]);

  const config = CATEGORY_CONFIG[insight.category];
  const Icon = config.icon;

  return (
    <div
      className={`panel panel-violet relative overflow-hidden ${className}`}
      style={{ padding: '20px 24px' }}
    >
      {/* Violet ambient glow */}
      <div style={{
        position: 'absolute',
        top: -40,
        right: -40,
        width: 160,
        height: 160,
        borderRadius: '50%',
        background: 'radial-gradient(ellipse, rgba(139,92,246,0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            className="animate-glow-violet"
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: 'var(--violet-glow)',
              border: '1px solid var(--border-violet)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Sparkles style={{ width: 13, height: 13, color: '#c4b5fd' }} />
          </div>
          <div>
            <div style={{
              fontSize: 10,
              fontFamily: 'JetBrains Mono, monospace',
              letterSpacing: '0.1em',
              color: '#c4b5fd',
              fontWeight: 600,
              textTransform: 'uppercase',
            }}>
              AI PATTERN OBSERVATION
            </div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
              RESEARCH ONLY — NOT AN EXECUTABLE SIGNAL
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Category badge */}
          <span className="badge badge-violet" style={{ color: config.color, borderColor: `${config.color}44`, background: `${config.color}14` }}>
            <Icon style={{ width: 9, height: 9 }} />
            {config.label}
          </span>
        </div>
      </div>

      {/* Insight text with animated entrance */}
      <AnimatePresence mode="wait">
        <motion.p
          key={key}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          style={{
            fontSize: 13.5,
            lineHeight: 1.65,
            color: 'var(--text-secondary)',
            fontFamily: 'Inter, sans-serif',
            margin: 0,
          }}
        >
          {insight.text}
        </motion.p>
      </AnimatePresence>

      {/* Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
            PATTERN CONFIDENCE:
          </div>
          <div style={{ display: 'flex', gap: 2 }}>
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: 14,
                  height: 3,
                  borderRadius: 2,
                  background: i < Math.round(insight.confidence * 10)
                    ? '#8b5cf6'
                    : 'var(--z5)',
                  opacity: i < Math.round(insight.confidence * 10) ? 0.8 + i * 0.02 : 0.3,
                }}
              />
            ))}
          </div>
          <div style={{ fontSize: 9, color: '#8b5cf6', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
            {(insight.confidence * 100).toFixed(0)}%
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, color: 'var(--text-faint)', fontFamily: 'JetBrains Mono, monospace' }}>
          <RefreshCw style={{ width: 9, height: 9 }} />
          AUTO-ROTATING 10s
        </div>
      </div>
    </div>
  );
};
