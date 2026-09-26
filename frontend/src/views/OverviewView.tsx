import React from 'react';
import { HeroScene3D } from '../components/3d/HeroScene3D';
import { MarketQuote, MarketRegime } from '../types/market';
import { PipelineArchitecture } from '../components/investor/PipelineArchitecture';
import { ResearchIntegrityCard } from '../components/investor/ResearchIntegrityCard';
import { ModelCalibrationCard } from '../components/investor/ModelCalibrationCard';
import { VolatilitySurface3D } from '../components/3d/VolatilitySurface3D';
import { MarketRegimeCard } from '../components/market/MarketRegimeCard';
import { LiveTickerStrip } from '../components/ui/LiveTickerStrip';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { StaggerContainer, FadeUp } from '../components/ui/PageTransition';
import { useAnimatedNumber, formatIndian, formatVolume } from '../hooks/useAnimatedNumber';
import { ArrowRight, TrendingUp, TrendingDown, ShieldCheck, Database, Lock } from 'lucide-react';

interface OverviewViewProps {
  niftyQuote: MarketQuote;
  bankniftyQuote: MarketQuote;
  regime: MarketRegime;
  isLowPerf: boolean;
  onNavigate: (tab: any) => void;
}

function QuickStatCard({
  label, value, change, changePct, volume, onClick,
}: {
  label: string;
  value: number;
  change?: number;
  changePct?: number;
  volume?: number;
  onClick: () => void;
}) {
  const animValue = useAnimatedNumber(value, 800);
  const isUp = (change ?? 0) >= 0;

  return (
    <div
      onClick={onClick}
      className="panel panel-interactive"
      style={{ padding: '20px 24px', cursor: 'pointer' }}
    >
      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 10,
          fontWeight: 700,
          color: 'var(--text-muted)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}>{label}</span>
        {changePct !== undefined && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            fontSize: 11,
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 700,
            color: isUp ? 'var(--emerald-accent)' : 'var(--rose-accent)',
            padding: '2px 8px',
            borderRadius: 20,
            background: isUp ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
            border: `1px solid ${isUp ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}`,
          }}>
            {isUp ? <TrendingUp style={{ width: 10, height: 10 }} /> : <TrendingDown style={{ width: 10, height: 10 }} />}
            {isUp ? '+' : ''}{changePct.toFixed(2)}%
          </span>
        )}
      </div>

      {/* Main value */}
      <div style={{
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 28,
        fontWeight: 700,
        color: 'var(--text-primary)',
        letterSpacing: '-0.5px',
        marginBottom: 4,
        lineHeight: 1,
      }}>
        {formatIndian(animValue)}
      </div>

      {/* Sub info */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 10 }}>
        {volume !== undefined && (
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: 'var(--text-muted)' }}>
            VOL: {formatVolume(volume)}
          </span>
        )}
        <span style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          fontSize: 10,
          fontFamily: 'JetBrains Mono, monospace',
          color: 'var(--text-muted)',
          marginLeft: 'auto',
          transition: 'color 0.15s ease',
        }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = 'var(--gold-primary)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'; }}
        >
          TERMINAL <ArrowRight style={{ width: 11, height: 11 }} />
        </span>
      </div>
    </div>
  );
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  niftyQuote, bankniftyQuote, regime, isLowPerf, onNavigate,
}) => {
  return (
    <StaggerContainer>

      {/* 1. CINEMATIC HERO */}
      <FadeUp>
        <div style={{
          width: '100%',
          borderRadius: 16,
          overflow: 'hidden',
          position: 'relative',
          border: '1px solid var(--border-1)',
          background: 'var(--z2)',
          boxShadow: 'var(--shadow-z3)',
        }}>
          {/* Aurora behind the hero */}
          <div className="aurora-bg" style={{ zIndex: 0 }} />

          <div style={{ height: 360, width: '100%', position: 'relative', zIndex: 1 }}>
            <HeroScene3D isLowPerf={isLowPerf} />
          </div>

          {/* Gradient overlay with text */}
          <div style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            background: 'linear-gradient(to top, rgba(5,7,14,0.97) 0%, rgba(5,7,14,0.5) 45%, transparent 100%)',
            zIndex: 2,
          }}>
            <div style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              padding: '32px 36px',
              pointerEvents: 'auto',
            }}>
              {/* Badge */}
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 12px',
                borderRadius: 20,
                background: 'rgba(212,175,55,0.1)',
                border: '1px solid var(--border-gold)',
                marginBottom: 14,
              }}>
                <div className="animate-pulse-subtle" style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: 'var(--gold-primary)',
                  boxShadow: '0 0 6px rgba(212,175,55,0.7)',
                }} />
                <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: 'var(--gold-primary)', letterSpacing: '0.1em', fontWeight: 600 }}>
                  INVESTOR EXECUTIVE INTELLIGENCE TERMINAL
                </span>
              </div>

              <h1 style={{
                fontFamily: 'Inter, sans-serif',
                fontWeight: 800,
                fontSize: 'clamp(24px, 3.5vw, 38px)',
                color: '#fff',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
                margin: '0 0 10px',
              }}>
                INDIAN FINANCIAL<br />MARKET INTELLIGENCE
              </h1>

              <p style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 14,
                color: 'rgba(148,163,184,0.85)',
                lineHeight: 1.6,
                maxWidth: 520,
                margin: 0,
              }}>
                AI-assisted market research, options intelligence, volatility surface modeling, and statistical calibration engine — built strictly for NSE India.
              </p>
            </div>
          </div>
        </div>
      </FadeUp>

      {/* 2. LIVE TICKER STRIP */}
      <FadeUp>
        <LiveTickerStrip niftyPrice={niftyQuote.last_price} bankniftyPrice={bankniftyQuote.last_price} />
      </FadeUp>

      {/* 3. BENCHMARK STRIP */}
      <FadeUp>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
          <QuickStatCard
            label="NIFTY 50"
            value={niftyQuote.last_price}
            change={184.2}
            changePct={0.75}
            volume={niftyQuote.volume}
            onClick={() => onNavigate('markets')}
          />
          <QuickStatCard
            label="BANK NIFTY"
            value={bankniftyQuote.last_price}
            change={295.4}
            changePct={0.58}
            volume={bankniftyQuote.volume}
            onClick={() => onNavigate('markets')}
          />
          {/* Regime tile */}
          <div
            onClick={() => onNavigate('markets')}
            className="panel panel-interactive"
            style={{ padding: '20px 24px', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>MARKET REGIME</span>
              <span style={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace', color: 'var(--gold-primary)', padding: '2px 8px', borderRadius: 20, background: 'var(--gold-glow)', border: '1px solid var(--border-gold)' }}>ACTIVE</span>
            </div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color: 'var(--gold-primary)', letterSpacing: '-0.5px', marginBottom: 10 }}>
              {regime.regime}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)' }}>
              <span>CONF: {(regime.confidence * 100).toFixed(0)}%</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>DETAILS <ArrowRight style={{ width: 10, height: 10 }} /></span>
            </div>
          </div>
        </div>
      </FadeUp>

      {/* 4. AI INSIGHT CARD */}
      <FadeUp>
        <AIInsightCard
          regime={regime.regime}
          pcr={0.94}
          iv={regime.historical_volatility}
          adx={regime.adx}
        />
      </FadeUp>

      {/* 5. DATA PIPELINE */}
      <FadeUp>
        <PipelineArchitecture />
      </FadeUp>

      {/* 6. 3D VOLATILITY + REGIME SPLIT */}
      <FadeUp>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }} className="grid-responsive-3d">
          <div>
            <VolatilitySurface3D isLowPerf={isLowPerf} />
          </div>
          <div>
            <MarketRegimeCard regime={regime} />
          </div>
        </div>
      </FadeUp>

      {/* 7. MODEL CALIBRATION */}
      <FadeUp>
        <ModelCalibrationCard />
      </FadeUp>

      {/* 8. RESEARCH INTEGRITY */}
      <FadeUp>
        <ResearchIntegrityCard />
      </FadeUp>

    </StaggerContainer>
  );
};
