import React, { useState, useEffect } from 'react';
import {
  Activity, TrendingUp, Layers, Sparkles, Menu,
  PieChart, DollarSign, Newspaper, ChevronRight, X
} from 'lucide-react';
import { NavTab } from './Navigation';

interface MobileNavigationProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  onOpenMenu: () => void;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  activeTab,
  onSelectTab,
  onOpenMenu,
}) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = (e?: Event) => {
      const target = e?.target as HTMLElement | undefined;
      const scrollY =
        window.scrollY ||
        document.documentElement.scrollTop ||
        document.body.scrollTop ||
        target?.scrollTop ||
        0;

      setIsScrolled(scrollY > 45);
    };

    window.addEventListener('scroll', handleScroll, { capture: true, passive: true });
    return () => window.removeEventListener('scroll', handleScroll, { capture: true } as any);
  }, []);

  const primaryTabs: { id: NavTab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Home', icon: Activity },
    { id: 'trading', label: 'Trade', icon: TrendingUp },
    { id: 'options', label: 'Options', icon: Layers },
    { id: 'ai-analyst', label: 'AI Alpha', icon: Sparkles },
    { id: 'positions', label: 'P&L', icon: DollarSign },
  ];

  const activeLabel =
    primaryTabs.find((t) => t.id === activeTab)?.label ||
    (activeTab === 'strategy-lab'
      ? 'Quant'
      : activeTab === 'technical'
      ? 'Tech'
      : activeTab === 'news'
      ? 'News'
      : 'Menu');

  return (
    <>
      {/* ── 1. Scrolled State: Sleek Floating Button on TOP RIGHT ── */}
      {isScrolled && (
        <button
          type="button"
          onClick={onOpenMenu}
          aria-label="Open Navigation Menu"
          className="md:hidden fixed top-3 right-3 z-50 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#101622]/95 border border-[#B6FF5C]/60 text-[#F3F6FC] shadow-[0_0_20px_rgba(182,255,92,0.35),0_4px_16px_rgba(0,0,0,0.7)] backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200 active:scale-95 cursor-pointer font-mono text-xs font-bold"
        >
          <span className="w-2 h-2 rounded-full bg-[#B6FF5C] animate-pulse" />
          <Menu className="w-4 h-4 text-[#B6FF5C]" />
          <span className="text-[11px] font-black tracking-wider text-[#B6FF5C] uppercase">
            {activeLabel}
          </span>
        </button>
      )}

      {/* ── 2. Top Navigation Bar on Phone (Visible when at top of page) ── */}
      {!isScrolled && (
        <nav className="md:hidden sticky top-16 z-30 w-full bg-[#101622]/95 backdrop-blur-xl border-b border-[#283345] px-2 py-1.5 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
          <div className="flex items-center justify-between gap-1">
            
            {/* Quick Desk Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto scrollbar-none py-0.5">
              {primaryTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id || (tab.id === 'overview' && activeTab === 'markets');

                return (
                  <button
                    key={tab.id}
                    onClick={() => onSelectTab(tab.id)}
                    className={`flex items-center gap-1.5 py-1 px-2.5 rounded-lg text-xs font-mono font-bold transition-all whitespace-nowrap cursor-pointer ${
                      isActive
                        ? 'bg-[#161F2D] text-[#B6FF5C] border border-[#B6FF5C]/40 shadow-[0_0_10px_rgba(182,255,92,0.15)]'
                        : 'text-[#929DB0] hover:text-[#F3F6FC] bg-[#0B1220]/60 border border-transparent'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Menu Trigger on the Right */}
            <button
              onClick={onOpenMenu}
              className="flex items-center gap-1 py-1 px-2.5 rounded-lg text-xs font-mono font-bold bg-[#161F2D] text-[#43D9FF] border border-[#43D9FF]/30 hover:border-[#43D9FF] transition-all whitespace-nowrap cursor-pointer flex-shrink-0"
            >
              <Menu className="w-3.5 h-3.5" />
              <span>More</span>
            </button>
          </div>
        </nav>
      )}
    </>
  );
};
