import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Compass, BarChart3, Layers, Box, FileCheck, Server,
  Zap, Clock, Search, TrendingUp, Newspaper,
} from 'lucide-react';

export type NavTab = 'trading' | 'positions' | 'options' | 'news' | 'markets' | 'overview' | 'volatility' | 'research' | 'data-health';

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
  { id: 'trading',   label: 'TRADING DESK',   short: 'TRADE', icon: TrendingUp },
  { id: 'positions', label: 'POSITIONS & P&L', short: 'POS',   icon: Layers    },
  { id: 'news',      label: 'MARKET NEWS',     short: 'NEWS',  icon: Newspaper },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab, onSelectTab, isLowPerf, onToggleLowPerf, marketOpen: _propMarketOpen, onOpenCommandPalette,
  experienceMode: _expMode, onSelectExperienceMode: _onSelectExp,
}) => {
  const { user, openAuthModal } = useAuth();
  const { themeConfig, cycleTheme } = useTheme();
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

  // Keyboard shortcuts 1-3
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onOpenCommandPalette();
        return;
      }
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
          <div onClick={() => onSelectTab('trading')} className="cursor-pointer flex-shrink-0">
            <CyberLogo size="md" />
          </div>

          {/* Desktop Nav Tabs (Simple & Sweet: 3 Core Items) */}
          <nav className="hidden md:flex" style={{ position: 'relative', alignItems: 'center', gap: 6 }}>
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
                    gap: 7,
                    padding: '8px 16px',
                    borderRadius: 10,
                    fontFamily: '"Outfit", sans-serif',
                    fontSize: 13,
                    fontWeight: isActive ? 700 : 500,
                    letterSpacing: '0.04em',
                    cursor: 'pointer',
                    border: isActive ? '1px solid rgba(212, 175, 55, 0.4)' : '1px solid transparent',
                    background: isActive ? 'rgba(212, 175, 55, 0.12)' : 'transparent',
                    color: isActive ? '#f6d776' : 'rgba(255, 255, 255, 0.7)',
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
                      (e.currentTarget as HTMLElement).style.color = 'rgba(255, 255, 255, 0.7)';
                      (e.currentTarget as HTMLElement).style.background = 'transparent';
                    }
                  }}
                >
                  <Icon style={{ width: 15, height: 15, flexShrink: 0 }} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Controls (Clean, Minimal, User-Friendly) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            {/* Trader Account Button */}
            <button
              onClick={openAuthModal}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#111726] hover:bg-[#182136] border border-white/[0.1] hover:border-[#d4af37]/40 transition-all text-xs flex-shrink-0 cursor-pointer shadow-sm"
              title="Trader Account & Virtual Funds"
            >
              <span className="text-sm">{user ? user.avatar : '👤'}</span>
              <div className="text-left hidden sm:block">
                <div className="font-bold text-white text-[12px] font-['Outfit']">
                  {user ? user.fullName.split(' ')[0] : 'Trader'}
                </div>
                <div className="text-[10px] text-emerald-400 font-mono font-bold">
                  ₹10,00,000 Demo
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
