import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Compass, BarChart3, Layers, Box, FileCheck, Server,
  Zap, Clock, Search, TrendingUp, Newspaper, DollarSign, LogOut,
  Sparkles, PieChart, ShieldCheck, Bookmark, Activity
} from 'lucide-react';

export type NavTab =
  | 'markets'
  | 'explorer'
  | 'options'
  | 'ai-analyst'
  | 'strategy-lab'
  | 'paper-trading'
  | 'portfolio'
  | 'tools'
  | 'trading'
  | 'technical'
  | 'news'
  | 'positions'
  | 'overview'
  | 'volatility'
  | 'research'
  | 'data-health'
  | 'screener'
  | 'settings';

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
  { id: 'trading',      label: 'Trading Desk',        short: 'TRADE', icon: TrendingUp },
  { id: 'news',         label: 'Market News',         short: 'NEWS',  icon: Newspaper  },
  { id: 'options',      label: 'Option Chain',        short: 'OPT',   icon: Layers     },
  { id: 'technical',    label: 'Technical Analysis',  short: 'TECH',  icon: BarChart3  },
  { id: 'ai-analyst',   label: 'AI Analyst',          short: 'AI',    icon: Sparkles   },
  { id: 'strategy-lab', label: 'Strategy Lab',        short: 'LAB',   icon: PieChart   },
  { id: 'positions',    label: 'Position & P&L',      short: 'P&L',   icon: DollarSign },
  { id: 'markets',      label: 'Market Overview',     short: 'MKT',   icon: Activity   },
  { id: 'tools',        label: 'Others Tools',        short: 'TOOLS', icon: Compass    },
];

export const Navigation: React.FC<NavigationProps> = ({
  activeTab, onSelectTab, isLowPerf, onToggleLowPerf, marketOpen: _propMarketOpen, onOpenCommandPalette,
  experienceMode: _expMode, onSelectExperienceMode: _onSelectExp,
}) => {
  const { user, openAuthModal, logout } = useAuth();
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

  // Keyboard shortcuts 1-6
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
      {/* ── 1. Top Welcome & Indian Index Tickers Strip ───────────────── */}
      <div className="w-full bg-[#050811]/95 border-b border-white/[0.08] py-2 px-4 backdrop-blur-xl">
        <div className="max-w-[1600px] mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Welcome Tagline */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#d4af37]/15 border border-[#d4af37]/40 text-[#f6d776] text-[11px] font-extrabold shadow-sm font-['Outfit']">
              ✨ Welcome to Indian Financial Trading AI
            </span>
            <span className="text-slate-400 hidden xl:inline text-[11px]">
              Autonomous Quantitative Derivatives & Execution Platform
            </span>
          </div>

          {/* Major Indian Indices Strip (NIFTY, BANK NIFTY, SENSEX, FINNIFTY) */}
          <div className="flex items-center gap-2 sm:gap-3 overflow-x-auto text-[11px] font-mono scrollbar-none">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0a0f1d] border border-white/[0.08]">
              <span className="text-slate-400 font-bold">🏛️ NIFTY:</span>
              <span className="text-white font-extrabold">₹24,652.8</span>
              <span className="text-emerald-400 font-bold">+0.52%</span>
            </div>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0a0f1d] border border-white/[0.08]">
              <span className="text-slate-400 font-bold">🏦 BANK NIFTY:</span>
              <span className="text-white font-extrabold">₹51,240.5</span>
              <span className="text-rose-400 font-bold">-0.22%</span>
            </div>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0a0f1d] border border-white/[0.08]">
              <span className="text-slate-400 font-bold">📈 SENSEX:</span>
              <span className="text-white font-extrabold">₹81,380.0</span>
              <span className="text-emerald-400 font-bold">+0.48%</span>
            </div>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0a0f1d] border border-white/[0.08] hidden sm:flex">
              <span className="text-slate-400 font-bold">💳 FINNIFTY:</span>
              <span className="text-white font-extrabold">₹23,892.2</span>
              <span className="text-emerald-400 font-bold">+0.31%</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. Primary Desktop Navigation Header ───────────────────────── */}
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
          padding: '0 20px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}>
          {/* Brand & Logo */}
          <div onClick={() => onSelectTab('trading')} className="cursor-pointer flex-shrink-0">
            <CyberLogo size="md" />
          </div>

          {/* Desktop Nav Tabs: 1. Trading Desk 2. Technical Analysis 3. News 4. Option Chain 5. Position & P&L 6. Others Tools */}
          <nav className="hidden lg:flex" style={{ position: 'relative', alignItems: 'center', gap: 4 }}>
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
                    padding: '8px 14px',
                    borderRadius: 10,
                    fontFamily: '"Outfit", sans-serif',
                    fontSize: 12,
                    fontWeight: isActive ? 700 : 500,
                    letterSpacing: '0.03em',
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
                  <Icon style={{ width: 14, height: 14, flexShrink: 0 }} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Controls: User Profile + Logout + Theme + Live Clock */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            {/* Active Trader Profile Pill */}
            <button
              onClick={openAuthModal}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#111726] hover:bg-[#182136] border border-white/[0.1] hover:border-[#d4af37]/40 transition-all text-xs flex-shrink-0 cursor-pointer shadow-sm"
              title="Trader Account & Virtual Funds"
            >
              <span className="text-sm">{user ? user.avatar : '👤'}</span>
              <div className="text-left hidden sm:block">
                <div className="font-bold text-white text-[11px] font-['Outfit']">
                  {user ? user.fullName.split(' ')[0] : 'Trader'}
                </div>
                <div className="text-[10px] text-emerald-400 font-mono font-bold">
                  ₹{(user ? user.startingCapital : 1000000).toLocaleString('en-IN')} Demo
                </div>
              </div>
            </button>

            {/* Sign Out Button (returns user to landing login page) */}
            <button
              onClick={logout}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-white/[0.04] hover:bg-rose-500/15 border border-white/[0.08] hover:border-rose-500/30 text-slate-400 hover:text-rose-300 transition-all text-xs cursor-pointer shadow-sm"
              title="Sign Out & Lock Terminal"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden xl:inline text-[11px] font-medium">Sign Out</span>
            </button>

            {/* Theme Switcher */}
            <button
              onClick={cycleTheme}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#111726] hover:bg-[#182136] border border-white/[0.1] hover:border-[#d4af37]/40 text-xs font-bold text-slate-200 transition-all shadow-sm flex-shrink-0 cursor-pointer"
              title={`Current Theme: ${themeConfig.name}`}
            >
              <span className="text-sm">{themeConfig.icon}</span>
              <span className="hidden sm:inline font-['Outfit'] text-[11px]">{themeConfig.name.split(' ')[1] || 'Theme'}</span>
            </button>

            {/* Clock + Market Status */}
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
                padding: '5px 8px',
                borderRadius: 7,
                border: `1px solid ${isLowPerf ? 'rgba(212,175,55,0.4)' : 'var(--border-1)'}`,
                background: isLowPerf ? 'var(--gold-glow)' : 'var(--z3)',
                color: isLowPerf ? 'var(--gold-primary)' : 'var(--text-muted)',
                fontSize: 9,
                fontFamily: 'JetBrains Mono, monospace',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <Zap style={{ width: 10, height: 10 }} />
              <span>{isLowPerf ? 'ECO' : '3D'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Mobile Bottom Tab Bar ─────────────────────────── */}
      <div className="lg:hidden mobile-tab-bar">
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
                <Icon style={{ width: 18, height: 18 }} />
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
              <span className="text-[10px]">{item.short}</span>
            </button>
          );
        })}
      </div>
    </>
  );
};
