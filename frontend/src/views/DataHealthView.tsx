import React from 'react';
import { ProviderHealth } from '../types/market';
import { DataHealthNodeGraph } from '../components/investor/DataHealthNodeGraph';
import { StaggerContainer, FadeUp } from '../components/ui/PageTransition';
import { Server, Database, HardDrive } from 'lucide-react';

interface DataHealthViewProps {
  providers: ProviderHealth[];
}

export const DataHealthView: React.FC<DataHealthViewProps> = ({ providers }) => {
  const coverageItems = [
    {
      label: 'EQUITY DAILY BARS',
      value: '1,250 SESSIONS',
      desc: 'Complete OHLCV coverage across NIFTY 50 and major constituents from 2020 to present.',
      status: 'SUFFICIENT',
      statusColor: 'var(--emerald-accent)',
      borderColor: 'rgba(16,185,129,0.15)',
    },
    {
      label: 'OPTIONS CONTRACT ARCHIVE',
      value: '15,106 CONTRACTS',
      desc: 'NSE Bhavcopy daily settlement marks (LTP, Volume, Open Interest). Sufficient for surface estimation.',
      status: 'VALUATION ONLY',
      statusColor: 'var(--gold-primary)',
      borderColor: 'rgba(212,175,55,0.15)',
    },
    {
      label: 'PAIRED BID/ASK DEPTH',
      value: '102 QUOTES (0.68%)',
      desc: 'Continuous intraday tick depth unavailable in EOD archive. Live order execution blocked by governance.',
      status: 'INSUFFICIENT / BLOCKED',
      statusColor: 'var(--rose-accent)',
      borderColor: 'rgba(244,63,94,0.15)',
    },
  ];

  return (
    <StaggerContainer>
      {/* Header */}
      <FadeUp>
        <div className="panel" style={{ padding: '20px 24px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Server style={{ width: 16, height: 16, color: 'var(--gold-primary)' }} />
              <h2 style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-primary)', textTransform: 'uppercase', margin: 0 }}>
                DATA INFRASTRUCTURE & PROVENANCE COMMAND CENTRE
              </h2>
            </div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: 'var(--text-muted)' }}>
              DETERMINISTIC LATENCY, TIMESTAMPS & CONTINUOUS BID/ASK AUDIT
            </div>
          </div>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fontWeight: 600, padding: '4px 12px', borderRadius: 6, background: 'rgba(212,175,55,0.08)', border: '1px solid rgba(212,175,55,0.22)', color: 'var(--gold-primary)' }}>
            <Database style={{ width: 12, height: 12 }} />
            PROVENANCE: HISTORICAL + DELAYED FEED
          </span>
        </div>
      </FadeUp>

      {/* Node graph */}
      <FadeUp>
        <DataHealthNodeGraph providers={providers} />
      </FadeUp>

      {/* Coverage audit */}
      <FadeUp>
        <div className="panel" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-1)', paddingBottom: 14, marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <HardDrive style={{ width: 15, height: 15, color: 'var(--gold-primary)' }} />
              <h3 style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-primary)', textTransform: 'uppercase', margin: 0 }}>
                DATASET SUFFICIENCY & CONTINUOUS COVERAGE AUDIT
              </h3>
            </div>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 9, color: 'var(--text-muted)' }}>PHASE 10A HISTORICAL DATA REPOSITORY</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {coverageItems.map(item => (
              <div key={item.label} style={{
                background: 'var(--z2)',
                padding: '18px 20px',
                borderRadius: 12,
                border: `1px solid ${item.borderColor}`,
              }}>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10 }}>{item.label}</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 20, fontWeight: 700, color: item.statusColor, marginBottom: 10, lineHeight: 1.2 }}>{item.value}</div>
                <p style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.55, margin: '0 0 12px' }}>{item.desc}</p>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 9, fontWeight: 700, color: item.statusColor, letterSpacing: '0.06em' }}>STATUS: {item.status}</div>
              </div>
            ))}
          </div>
        </div>
      </FadeUp>
    </StaggerContainer>
  );
};
