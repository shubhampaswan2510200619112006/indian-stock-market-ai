import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Compass, BarChart3, Layers, Box, FileCheck, Server,
  Zap, Clock, Search,
} from 'lucide-react';

export type NavTab = 'overview' | 'markets' | 'options' | 'volatility' | 'research' | 'data-health';

interface NavigationProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isLowPerf: boolean;
  onToggleLowPerf: () => void;
  marketOpen: boolean;
  onOpenCommandPalette: () => void;
}

const navItems: { id: NavTab; label: string; short: string; icon: React.ElementType }[] = [
  { id: 'overview',    label: 'OVERVIEW',     short: 'OVR', icon: Compass   },
  { id: 'markets',     label: 'MARKETS',      short: 'MKT', icon: BarChart3 },
  { id: 'options',     label: 'OPTIONS',      short: 'OPT', icon: Layers    },
  { id: 'volatility',  label: '3D VOLATILITY',short: '3DV', icon: Box       },
  { id: 'research',    label: 'RESEARCH',     short: 'RES', icon: FileCheck },
  { id: 'data-health', label: 'DATA HEALTH',  short: 'DAT', icon: Server    },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab, onSelectTab, isLowPerf, onToggleLowPerf, marketOpen, onOpenCommandPalette,
}) => {
  const [istTime, setIstTime] = useState('');
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number }>({ left: 0, width: 0 });

  // Clock
  useEffect(() => {
    const update = () => {
      setIstTime(new Date().toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata', hour12: false,
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      }) + ' IST');
    };
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);

  // Sliding indicator position
  useEffect(() => {
    const el = tabRefs.current[activeTab];
    if (!el) return;
    const parent = el.parentElement;
    if (!parent) return;
    const parentRect = parent.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    setIndicatorStyle({
      left: elRect.left - parentRect.left,
      width: elRect.width,
    });
  }, [activeTab]);

  // Keyboard shortcuts 1-6
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Cmd/Ctrl+K → command palette
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onOpenCommandPalette();
        return;
      }
      // 1–6 tab shortcuts (only when no input focused)
      const active = document.activeElement?.tagName;
      if (active === 'INPUT' || active === 'TEXTAREA') return;
      const idx = parseInt(e.key) - 1;
      if (idx >= 0 && idx < navItems.length) {
        onSelectTab(navItems[idx].id);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onSelectTab, onOpenCommandPalette]);

  return (
    <>
      {/* ── Desktop Header ─────────────────────────────────── */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        width: '100%',
        background: 'rgba(5, 7, 14, 0.94)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border-1)',
        boxShadow: '0 1px 0 var(--border-0), 0 4px 24px rgba(0,0,0,0.4)',
      }}>
        <div style={{
          maxWidth: 1280,
          margin: '0 auto',
          padding: '0 20px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}>
          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, rgba(212,175,55,0.2) 0%, var(--z4) 100%)',
              border: '1px solid var(--border-gold)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 12px rgba(212,175,55,0.12)',
            }}>
              <span style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontWeight: 700,
                fontSize: 13,
                background: 'linear-gradient(175deg, #fef9c3 0%, #d4af37 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                letterSpacing: '-0.5px',
              }}>IM</span>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 600,
                  fontSize: 13,
                  color: 'var(--text-primary)',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}>Indian Market Intelligence</span>
                <span style={{
                  padding: '1px 6px',
                  background: 'var(--z5)',
                  border: '1px solid var(--border-1)',
                  borderRadius: 4,
                  fontSize: 9,
                  fontFamily: 'JetBrains Mono, monospace',
                  color: 'var(--text-muted)',
                }}>v17.0</span>
              </div>
              <div style={{
                fontSize: 9,
                fontFamily: 'JetBrains Mono, monospace',
                color: 'var(--text-faint)',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                marginTop: 1,
              }}>
                QUANTITATIVE RESEARCH & DERIVATIVES TERMINAL
              </div>
            </div>
          </div>

          {/* Desktop Nav Tabs */}
          <nav className="hidden md:flex" style={{ position: 'relative', alignItems: 'center', gap: 2 }}>
            {/* Sliding gold underline */}
            <div
              className="nav-indicator"
              style={{
                left: indicatorStyle.left,
                width: indicatorStyle.width,
                transition: 'left 0.35s cubic-bezier(0.16,1,0.3,1), width 0.35s cubic-bezier(0.16,1,0.3,1)',
              }}
            />

            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  ref={el => { tabRefs.current[item.id] = el; }}
                  onClick={() => onSelectTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 8,
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 10.5,
                    fontWeight: isActive ? 600 : 400,
                    letterSpacing: '0.06em',
                    cursor: 'pointer',
                    border: isActive ? '1px solid var(--border-gold)' : '1px solid transparent',
                    background: isActive ? 'var(--gold-glow)' : 'transparent',
                    color: isActive ? 'var(--gold-primary)' : 'var(--text-muted)',
                    transition: 'all 0.18s ease',
                    position: 'relative',
                    whiteSpace: 'nowrap',
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)';
                      (e.currentTarget as HTMLElement).style.background = 'var(--z4)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
                      (e.currentTarget as HTMLElement).style.background = 'transparent';
                    }
                  }}
                >
                  <Icon style={{ width: 13, height: 13, flexShrink: 0 }} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            {/* Search / Command Palette */}
            <button
              onClick={onOpenCommandPalette}
              title="Command Palette (⌘K)"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 10px',
                borderRadius: 8,
                background: 'var(--z3)',
                border: '1px solid var(--border-1)',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                fontSize: 11,
                fontFamily: 'JetBrains Mono, monospace',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-gold)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-1)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)'; }}
            >
              <Search style={{ width: 12, height: 12 }} />
              <span className="hidden lg:inline">Search</span>
              <kbd style={{
                padding: '1px 5px',
                borderRadius: 3,
                background: 'var(--z5)',
                border: '1px solid var(--border-1)',
                fontSize: 9,
                fontFamily: 'JetBrains Mono, monospace',
                color: 'var(--text-faint)',
              }} className="hidden lg:inline">⌘K</kbd>
            </button>

            {/* Clock + Session — desktop only */}
            <div className="hidden lg:flex" style={{ flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-secondary)' }}>
                <Clock style={{ width: 11, height: 11, color: 'var(--text-muted)' }} />
                {istTime || '09:15:00 IST'}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 9 }}>
                <div
                  className={marketOpen ? 'animate-pulse-subtle' : ''}
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: '50%',
                    background: marketOpen ? 'var(--emerald-accent)' : 'var(--text-faint)',
                    boxShadow: marketOpen ? '0 0 6px rgba(16,185,129,0.6)' : 'none',
                  }}
                />
                <span style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  color: marketOpen ? 'var(--emerald-accent)' : 'var(--text-muted)',
                  letterSpacing: '0.06em',
                }}>
                  {marketOpen ? 'NSE OPEN' : 'NSE CLOSED'}
                </span>
              </div>
            </div>

            {/* LOD Toggle */}
            <button
              onClick={onToggleLowPerf}
              title={isLowPerf ? '2D Mode Active' : 'Switch to 2D / Eco Mode'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                padding: '5px 10px',
                borderRadius: 7,
                border: `1px solid ${isLowPerf ? 'rgba(212,175,55,0.4)' : 'var(--border-1)'}`,
                background: isLowPerf ? 'var(--gold-glow)' : 'var(--z3)',
                color: isLowPerf ? 'var(--gold-primary)' : 'var(--text-muted)',
                fontSize: 9,
                fontFamily: 'JetBrains Mono, monospace',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                letterSpacing: '0.04em',
              }}
            >
              <Zap style={{ width: 11, height: 11 }} />
              <span>{isLowPerf ? 'ECO' : '3D'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Mobile Bottom Tab Bar ─────────────────────────── */}
      <div className="md:hidden mobile-tab-bar">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`mobile-tab-item ${isActive ? 'active' : ''}`}
            >
              <div style={{ position: 'relative' }}>
                <Icon style={{ width: 20, height: 20 }} />
                {isActive && (
                  <motion.div
                    layoutId="mobile-active-dot"
                    style={{
                      position: 'absolute',
                      bottom: -4,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 4,
                      height: 4,
                      borderRadius: '50%',
                      background: 'var(--gold-primary)',
                      boxShadow: '0 0 6px rgba(212,175,55,0.7)',
                    }}
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
              </div>
              {item.short}
            </button>
          );
        })}
      </div>
    </>
  );
};
