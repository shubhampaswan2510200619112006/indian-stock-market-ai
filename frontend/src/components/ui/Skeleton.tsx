import React from 'react';

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', style }) => (
  <div className={`skeleton ${className}`} style={style} />
);

export const SkeletonCard: React.FC<{ rows?: number; height?: number }> = ({ rows = 3, height = 120 }) => (
  <div className="panel p-5" style={{ height }}>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Skeleton style={{ height: 14, width: '40%' }} />
      <Skeleton style={{ height: 28, width: '60%' }} />
      {Array.from({ length: rows - 2 }).map((_, i) => (
        <Skeleton key={i} style={{ height: 10, width: `${70 - i * 15}%` }} />
      ))}
    </div>
  </div>
);

export const SkeletonChart: React.FC = () => (
  <div className="panel" style={{ height: 480, padding: 0, overflow: 'hidden' }}>
    <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-1)', display: 'flex', gap: 16, alignItems: 'center' }}>
      <Skeleton style={{ height: 14, width: 160 }} />
      <Skeleton style={{ height: 14, width: 80 }} />
    </div>
    <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 40 }}>
          {Array.from({ length: 20 }).map((_, j) => (
            <Skeleton
              key={j}
              style={{
                flex: 1,
                height: `${20 + Math.sin((i + j) * 0.5) * 15 + Math.random() * 10}px`,
              }}
            />
          ))}
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number }> = ({ rows = 6 }) => (
  <div className="panel" style={{ overflow: 'hidden', padding: 0 }}>
    <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-1)' }}>
      <Skeleton style={{ height: 14, width: '30%' }} />
    </div>
    <div style={{ padding: '0 4px' }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{
          padding: '12px 16px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr 80px 1fr 1fr 1fr',
          gap: 12,
          borderBottom: '1px solid var(--border-0)',
        }}>
          {Array.from({ length: 7 }).map((_, j) => (
            <Skeleton key={j} style={{ height: 12, opacity: 1 - i * 0.08 }} />
          ))}
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonHero: React.FC = () => (
  <div className="panel" style={{ height: 360, overflow: 'hidden', position: 'relative' }}>
    <div className="skeleton" style={{ position: 'absolute', inset: 0, borderRadius: 0 }} />
    <div style={{ position: 'absolute', bottom: 24, left: 28, display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Skeleton style={{ height: 14, width: 220 }} />
      <Skeleton style={{ height: 36, width: 420 }} />
      <Skeleton style={{ height: 12, width: 340 }} />
    </div>
  </div>
);
