import React from 'react';
import { ResearchIntegrityCard } from '../components/investor/ResearchIntegrityCard';
import { StaggerContainer, FadeUp } from '../components/ui/PageTransition';
import { Award, XCircle } from 'lucide-react';

export const ResearchGovernanceView: React.FC = () => {
  const hypotheses = [
    { id: 'H001', name: 'Realized Volatility Autocorrelation', score: '59 pts', reason: 'Negative net Sharpe after statutory transaction frictions' },
    { id: 'H002', name: 'Multi-Day Target Horizon Formulation', score: '51 pts', reason: 'Turnover reduced, but underlying signal lacks gross edge' },
    { id: 'H003', name: 'Regime-Conditioned Volatility Breakout', score: '23 pts', reason: 'Fails to beat baseline out-of-sample; fragile to slippage' },
    { id: 'H004', name: 'High-Confidence Threshold Filtering', score: '23 pts', reason: 'Sample size collapses; fee drag compounds in remaining trades' },
    { id: 'H005', name: 'Long/Short Asymmetric Conditioning', score: '18 pts', reason: 'Insufficient sample size; fails walk-forward test' },
    { id: 'H006', name: 'Swing Multi-Day Holding Period', score: '23 pts', reason: 'Negative net return after carrying costs' },
    { id: 'H007', name: 'Options Open Interest & PCR Alpha', score: '23 pts', reason: '0.00% incremental accuracy over spot price & volume alone' },
    { id: 'H008', name: 'Volatility Regime Strategy Mapping', score: '23 pts', reason: 'Defined-risk spreads limit downside but lack positive gross edge' },
  ];

  return (
    <StaggerContainer>
      {/* Header Banner */}
      <FadeUp>
        <div className="panel" style={{ padding: '20px 24px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Award style={{ width: 16, height: 16, color: 'var(--gold-primary)' }} />
              <h2 style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-primary)', textTransform: 'uppercase', margin: 0 }}>
                QUANTITATIVE RESEARCH GOVERNANCE & HYPOTHESIS REGISTRY
              </h2>
            </div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: 'var(--text-muted)' }}>
              FROZEN BASELINE: v17.0.0-investor-frozen • ZERO P-HACKING OR POST-HOC OVERFITTING
            </div>
          </div>
          <span style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 10,
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: 6,
            background: 'rgba(244,63,94,0.08)',
            border: '1px solid rgba(244,63,94,0.25)',
            color: 'var(--rose-accent)',
          }}>
            PRIMARY CLASSIFICATION: NO_SURVIVING_HYPOTHESIS
          </span>
        </div>
      </FadeUp>

      {/* Research Integrity */}
      <FadeUp>
        <ResearchIntegrityCard />
      </FadeUp>

      {/* Hypothesis Audit Table */}
      <FadeUp>
        <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--border-1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--z3)',
          }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.06em' }}>
              PRE-REGISTERED HYPOTHESES EVALUATION
            </span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 9, color: 'var(--text-muted)' }}>
              PHASE 9.6 SCIENTIFIC RECALIBRATION REGISTRY
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-1)' }}>
                  {['ID', 'HYPOTHESIS DESCRIPTION', 'SCORE', 'RESULT', 'DISQUALIFICATION AUDIT'].map(col => (
                    <th key={col} style={{ padding: '12px 16px', textAlign: 'left', fontSize: 9, letterSpacing: '0.08em', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, background: 'var(--z2)', whiteSpace: 'nowrap' }}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {hypotheses.map((h, i) => (
                  <tr
                    key={h.id}
                    style={{
                      borderBottom: '1px solid var(--border-0)',
                      transition: 'background 0.12s ease',
                    }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--z3)'; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                  >
                    <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--gold-primary)' }}>{h.id}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-primary)' }}>{h.name}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>{h.score}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--rose-accent)', fontWeight: 700, fontSize: 11 }}>
                        <XCircle style={{ width: 12, height: 12 }} />
                        DISQUALIFIED
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 11, color: 'var(--text-muted)', fontFamily: 'Inter, sans-serif' }}>{h.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ padding: '12px 24px', background: 'var(--z2)', borderTop: '1px solid var(--border-1)', display: 'flex', justifyContent: 'space-between', fontSize: 10 }}>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)' }}>ZERO HYPOTHESES PROMOTED TO LIVE TRADING WITHOUT STATISTICAL SIGNIFICANCE</span>
            <span style={{ fontFamily: 'JetBrains Mono, monospace', color: 'var(--emerald-accent)', fontWeight: 600 }}>ACADEMIC RIGOR ENFORCED</span>
          </div>
        </div>
      </FadeUp>
    </StaggerContainer>
  );
};
