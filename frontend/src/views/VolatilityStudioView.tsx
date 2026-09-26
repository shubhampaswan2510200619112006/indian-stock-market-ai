import React, { useState } from 'react';
import { VolatilitySurface3D } from '../components/3d/VolatilitySurface3D';
import { OpenInterestLandscape3D } from '../components/3d/OpenInterestLandscape3D';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { StaggerContainer, FadeUp } from '../components/ui/PageTransition';
import { Box, Layers } from 'lucide-react';

interface VolatilityStudioViewProps {
  isLowPerf: boolean;
}

export const VolatilityStudioView: React.FC<VolatilityStudioViewProps> = ({ isLowPerf }) => {
  const [active3DTab, setActive3DTab] = useState<'IV' | 'OI'>('IV');

  return (
    <StaggerContainer>
      {/* Header */}
      <FadeUp>
        <div className="panel" style={{ padding: '20px 24px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'var(--gold-glow)', border: '1px solid var(--border-gold)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Box style={{ width: 16, height: 16, color: 'var(--gold-primary)' }} />
            </div>
            <div>
              <h2 style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-primary)', textTransform: 'uppercase', margin: 0 }}>
                3D DERIVATIVES VISUALIZATION LABORATORY
              </h2>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
                STRIKE × EXPIRY × VOLATILITY / OPEN INTEREST MANIFOLDS
              </div>
            </div>
          </div>

          {/* Tab switcher */}
          <div style={{ display: 'flex', background: 'var(--z2)', padding: 3, borderRadius: 10, border: '1px solid var(--border-1)', gap: 2 }}>
            {(['IV', 'OI'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActive3DTab(tab)}
                style={{
                  padding: '6px 18px',
                  borderRadius: 8,
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 10,
                  fontWeight: active3DTab === tab ? 700 : 400,
                  cursor: 'pointer',
                  border: active3DTab === tab ? '1px solid var(--border-gold)' : '1px solid transparent',
                  background: active3DTab === tab ? 'var(--gold-glow)' : 'transparent',
                  color: active3DTab === tab ? 'var(--gold-primary)' : 'var(--text-muted)',
                  transition: 'all 0.15s ease',
                }}
              >
                {tab === 'IV' ? '3D IV SURFACE' : '3D OI LANDSCAPE'}
              </button>
            ))}
          </div>
        </div>
      </FadeUp>

      {/* 3D Scene */}
      <FadeUp>
        {active3DTab === 'IV'
          ? <VolatilitySurface3D isLowPerf={isLowPerf} />
          : <OpenInterestLandscape3D isLowPerf={isLowPerf} />
        }
      </FadeUp>

      {/* AI Insight for vol */}
      <FadeUp>
        <AIInsightCard regime="RANGE" pcr={0.94} iv={13.8} />
      </FadeUp>

      {/* Methodology Cards */}
      <FadeUp>
        <div className="panel" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-1)', paddingBottom: 14, marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Layers style={{ width: 15, height: 15, color: 'var(--gold-primary)' }} />
              <h3 style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-primary)', textTransform: 'uppercase', margin: 0 }}>
                MATHEMATICAL METHODOLOGY & DATA LIMITATIONS
              </h3>
            </div>
            <span style={{ fontSize: 9, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)' }}>ARBITRAGE-FREE SPLINE INTERPOLATION</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { title: 'STRIKE SKEW DYNAMICS', color: 'var(--text-primary)', text: 'Downside puts trade at structural volatility premiums reflecting index crash-phobia. OTM calls exhibit flattening skew in rangebound regimes.' },
              { title: 'TERM STRUCTURE SLOPE', color: 'var(--text-primary)', text: 'Near-dated weekly expiries exhibit high gamma sensitivity. Monthly contracts reflect baseline macroeconomic volatility regime.' },
              { title: 'EXECUTION INTEGRITY', color: 'var(--gold-primary)', text: 'Theoretical IV computed from settlement LTPs. Live execution requires continuous Bid/Ask spreads. Current coverage: 0.68% — blocks all alpha claims.' },
            ].map(c => (
              <div key={c.title} style={{ background: 'var(--z2)', padding: '16px', borderRadius: 10, border: '1px solid var(--border-0)' }}>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fontWeight: 700, color: c.color, marginBottom: 8, letterSpacing: '0.06em' }}>{c.title}</div>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>{c.text}</p>
              </div>
            ))}
          </div>
        </div>
      </FadeUp>
    </StaggerContainer>
  );
};
