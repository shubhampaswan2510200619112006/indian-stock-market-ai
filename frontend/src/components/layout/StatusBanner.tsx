import React from 'react';
import { motion } from 'framer-motion';
import { GovernanceState } from '../../types/market';
import { ShieldCheck, Lock, Database, Cpu, Activity } from 'lucide-react';

interface StatusBannerProps {
  governance: GovernanceState;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({ governance }) => {
  const pills = [
    { icon: Cpu, label: 'ENGINEERING', value: governance.software_engineering, color: 'green' as const },
    { icon: Database, label: 'LIVE DATA', value: governance.live_data, color: 'gold' as const },
    { icon: Lock, label: 'EXECUTION', value: governance.execution_research, color: 'red' as const },
    { icon: Activity, label: 'ALPHA', value: governance.statistical_evidence, color: 'gold' as const },
  ];

  const colorMap = {
    green: {
      text: 'var(--emerald-accent)',
      bg: 'rgba(16,185,129,0.08)',
      border: 'rgba(16,185,129,0.22)',
      glow: '0 0 8px rgba(16,185,129,0.25)',
    },
    gold: {
      text: 'var(--gold-primary)',
      bg: 'rgba(212,175,55,0.08)',
      border: 'rgba(212,175,55,0.22)',
      glow: '0 0 8px rgba(212,175,55,0.25)',
    },
    red: {
      text: 'var(--rose-accent)',
      bg: 'rgba(244,63,94,0.08)',
      border: 'rgba(244,63,94,0.22)',
      glow: '0 0 8px rgba(244,63,94,0.2)',
    },
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      style={{
        width: '100%',
        background: 'rgba(2, 4, 10, 0.92)',
        borderBottom: '1px solid var(--border-0)',
        padding: '6px 20px',
      }}
    >
      <div style={{
        maxWidth: 1280,
        margin: '0 auto',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
      }}>
        {/* Left: version + tests */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontSize: 9,
            fontFamily: 'JetBrains Mono, monospace',
            textTransform: 'uppercase',
            letterSpacing: '0.12em',
            color: 'var(--text-faint)',
          }}>
            RELEASE:
          </span>
          <span style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 10,
            fontWeight: 700,
            color: 'var(--gold-primary)',
            padding: '2px 8px',
            borderRadius: 4,
            background: 'rgba(212,175,55,0.08)',
            border: '1px solid rgba(212,175,55,0.2)',
          }}>
            {governance.release_baseline} [{governance.git_commit}]
          </span>

          <span
            className="animate-glow-green"
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 10,
              color: 'var(--emerald-accent)',
              padding: '2px 8px',
              borderRadius: 4,
              background: 'rgba(16,185,129,0.08)',
              border: '1px solid rgba(16,185,129,0.22)',
              display: 'flex',
              alignItems: 'center',
              gap: 5,
            }}
          >
            <ShieldCheck style={{ width: 10, height: 10 }} />
            {governance.tests_passing}/{governance.tests_total} VERIFIED
          </span>
        </div>

        {/* Right: status pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6 }}>
          {pills.map(({ icon: Icon, label, value, color }) => {
            const c = colorMap[color];
            return (
              <span
                key={label}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 5,
                  padding: '2px 8px',
                  borderRadius: 4,
                  background: c.bg,
                  border: `1px solid ${c.border}`,
                  color: c.text,
                  fontSize: 9,
                  fontFamily: 'JetBrains Mono, monospace',
                  letterSpacing: '0.05em',
                  fontWeight: 600,
                }}
              >
                <Icon style={{ width: 9, height: 9, flexShrink: 0 }} />
                {label}: {value}
              </span>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
};
