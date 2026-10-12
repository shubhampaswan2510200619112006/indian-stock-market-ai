import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Compass, BarChart3, Layers, Box, FileCheck, Server,
  Zap, Clock, Search, TrendingUp, Newspaper,
} from 'lucide-react';

export type NavTab = 'trading' | 'options' | 'news' | 'markets' | 'overview' | 'volatility' | 'research' | 'data-health';

import { getISTTime } from '../../utils/istTime';
import { CyberLogo } from './CyberLogo';
import { useAuth, ExperienceLevel } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';

export interface NavigationProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isLowPerf: boolean;
  onToggleLowPerf: () => void;
  marketOpen: boolean;
  onOpenCommandPalette: () => void;
  experienceMode?: ExperienceLevel;
  onSelectExperienceMode?: (mode: ExperienceLevel) => void;
}

const navItems: { id: NavTab; label: string; short: string; icon: React.ElementType }[] = [
  { id: 'trading',     label: 'TERMINAL', short: 'TRM', icon: TrendingUp },
  { id: 'options',     label: 'OPTIONS',  short: 'OPT', icon: Layers    },
  { id: 'news',        label: 'NEWS',     short: 'NWS', icon: Newspaper },
  { id: 'markets',     label: 'MARKETS',  short: 'MKT', icon: BarChart3 },
  { id: 'overview',    label: 'OVERVIEW', short: 'OVR', icon: Compass   },
  { id: 'volatility',  label: '3D VOL',   short: '3DV', icon: Box       },
  { id: 'research',    label: 'RESEARCH', short: 'RES', icon: FileCheck },
  { id: 'data-health', label: 'HEALTH',   short: 'DAT', icon: Server    },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab, onSelectTab, isLowPerf, onToggleLowPerf, marketOpen: _propMarketOpen, onOpenCommandPalette,
  experienceMode, onSelectExperienceMode,
}) => {
  const { user, openAuthModal, updateExperienceLevel } = useAuth();
  const { themeConfig, cycleTheme } = useTheme();
  const currentMode = experienceMode || user?.experienceLevel || 'PRO';

  const handleModeSwitch = (mode: ExperienceLevel) => {
    updateExperienceLevel(mode);
    if (onSelectExperienceMode) {
      onSelectExperienceMode(mode);
    }
  };
  const [istData, setIstData] = useState(() => getISTTime());
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number }>({ left: 0, width: 0 });

  // High precision real-time market clock
  useEffect(() => {
    const update = () => {
      setIstData(getISTTime());
    };
    update();
    const t = setInterval(update, 250);
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
        background: 'rgba(8, 11, 18, 0.94)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 4px 25px rgba(0,0,0,0.5)',
      }}>
        <div style={{
          maxWidth: 1600,
          margin: '0 auto',
          padding: '0 24px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}>
          {/* Brand & Logo */}
          <div onClick={() => onSelectTab('overview')} className="cursor-pointer flex-shrink-0">
            <CyberLogo size="md" />
          </div>

          {/* Desktop Nav Tabs */}
          <nav className="hidden md:flex" style={{ position: 'relative', alignItems: 'center', gap: 4 }}>
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
                    padding: '7px 14px',
                    borderRadius: 10,
                    fontFamily: '"Outfit", sans-serif',
                    fontSize: 12,
                    fontWeight: isActive ? 700 : 500,
                    letterSpacing: '0.04em',
                    cursor: 'pointer',
                    border: isActive ? '1px solid rgba(212, 175, 55, 0.4)' : '1px solid transparent',
                    background: isActive ? 'rgba(212, 175, 55, 0.12)' : 'transparent',
                    color: isActive ? '#f6d776' : 'rgba(255, 255, 255, 0.65)',
                    boxShadow: isActive ? '0 0 15px rgba(212, 175, 55, 0.15)' : 'none',
                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                    position: 'relative',
                    whiteSpace: 'nowrap',
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.color = '#ffffff';
                      (e.currentTarget as HTMLElement).style.background = 'rgba(255, 255, 255, 0.08)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.color = 'rgba(255, 255, 255, 0.65)';
                      (e.currentTarget as HTMLElement).style.background = 'transparent';
                    }
                  }}
                >
                  <Icon style={{ width: 14, height: 14, flexShrink: 0 }} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            {/* Experience Level Switcher (Beginner vs Pro vs Quant) */}
            <div className="flex items-center bg-[#0d121e] p-1 rounded-xl border border-white/[0.08] text-xs shadow-sm">
              <button
                onClick={() => handleModeSwitch('BEGINNER')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                  currentMode === 'BEGINNER'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Beginner Guided Mode: 3-step trade wizard, educational guidance & zero jargon"
              >
                <span>🔰</span>
                <span className="hidden xl:inline">Beginner</span>
              </button>
              <button
                onClick={() => handleModeSwitch('PRO')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                  currentMode === 'PRO'
                    ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Pro Terminal: Full Kite/Sensibull Options Chain, Greek analytics & order pad"
              >
                <span>⚡</span>
                <span className="hidden xl:inline">Pro</span>
              </button>
              <button
                onClick={() => handleModeSwitch('QUANT')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                  currentMode === 'QUANT'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-400/40 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Quant Lab: 3D Volatility surfaces, Markov regimes & Black-Scholes pricing"
              >
                <span>🧠</span>
                <span className="hidden xl:inline">Quant</span>
              </button>
            </div>

            {/* Trader Account / Login Button */}
            <button
              onClick={openAuthModal}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-[#111726] to-[#182136] hover:from-[#161f33] hover:to-[#212c48] border border-white/[0.12] hover:border-[#d4af37]/50 transition-all text-xs flex-shrink-0 shadow-sm cursor-pointer"
              title="Trader Account & Virtual Funds"
            >
              <span className="text-sm">{user ? user.avatar : '👤'}</span>
              <div className="text-left hidden sm:block">
                <div className="font-extrabold text-white leading-tight text-[11px] font-['Outfit']">
                  {user ? user.fullName.split(' ')[0] : 'Sign In'}
                </div>
                <div className="text-[9px] text-[#f6d776] font-mono font-bold">
                  {user ? `${user.experienceLevel} VIP` : 'Executive Pro'}
                </div>
              </div>
            </button>

            {/* Elegant Theme Switcher Pill */}
            <button
              onClick={cycleTheme}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#111726] hover:bg-[#182136] border border-white/[0.1] hover:border-[#d4af37]/40 text-xs font-bold text-slate-200 transition-all shadow-sm hover:scale-105 active:scale-95 flex-shrink-0 cursor-pointer"
              title={`Current Theme: ${themeConfig.name} — Click to switch`}
            >
              <span className="text-sm">{themeConfig.icon}</span>
              <span className="hidden sm:inline font-['Outfit'] text-[12px]">{themeConfig.name.split(' ')[1] || 'Theme'}</span>
            </button>

            {/* Search / Command Palette — 2xl only */}
            <button
              onClick={onOpenCommandPalette}
              title="Command Palette (⌘K)"
              className="hidden 2xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[var(--z3)] border border-[var(--border-1)] text-xs text-[var(--text-muted)] cursor-pointer hover:border-[var(--border-gold)]"
            >
              <Search style={{ width: 12, height: 12 }} />
              <span>Search</span>
              <kbd className="px-1 py-0.5 rounded bg-[var(--z5)] border border-[var(--border-1)] text-[9px] font-mono text-[var(--text-faint)]">⌘K</kbd>
            </button>

            {/* Clock + Session */}
            <div className="hidden md:flex flex-shrink-0 flex-col items-end gap-0.5">
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-secondary)' }}>
                <Clock style={{ width: 11, height: 11, color: 'var(--text-muted)' }} />
                <span>{istData.timeString12}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 9 }}>
                <div
                  className={istData.isMarketOpen ? 'animate-pulse-subtle' : ''}
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: istData.isMarketOpen ? 'var(--emerald-accent)' : '#f43f5e',
                    boxShadow: istData.isMarketOpen ? '0 0 6px rgba(16,185,129,0.6)' : '0 0 6px rgba(244,63,94,0.4)',
                  }}
                />
                <span style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  color: istData.isMarketOpen ? 'var(--emerald-accent)' : '#f43f5e',
                  letterSpacing: '0.06em',
                  fontWeight: 600,
                }}>
                  {istData.isMarketOpen ? 'NSE LIVE' : 'NSE CLOSED'}
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
