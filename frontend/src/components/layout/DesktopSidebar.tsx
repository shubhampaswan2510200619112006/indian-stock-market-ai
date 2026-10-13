import React, { useState } from 'react';
import {
  Activity, TrendingUp, Layers, Sparkles, FlaskConical,
  Briefcase, Flame, BarChart3, Newspaper, CheckCircle2,
  Settings, ChevronLeft, ChevronRight, ShieldCheck, Compass
} from 'lucide-react';
import { NavTab } from './Navigation';

interface DesktopSidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavDestination {
  id: NavTab;
  label: string;
  badge?: string;
  badgeColor?: string;
  icon: React.ElementType;
  group: 'CORE' | 'ANALYTICS' | 'EXECUTION' | 'SYSTEM';
}

const DESTINATIONS: NavDestination[] = [
  { id: 'overview', label: 'Home Dashboard', icon: Activity, group: 'CORE' },
  { id: 'trading', label: 'Trading Terminal', icon: TrendingUp, badge: 'PRO', badgeColor: '#B6FF5C', group: 'CORE' },
  { id: 'options', label: 'Options Terminal', icon: Layers, badge: 'F&O', badgeColor: '#43D9FF', group: 'CORE' },
  
  { id: 'ai-analyst', label: 'AI Intelligence', icon: Sparkles, badge: 'AI', badgeColor: '#B6FF5C', group: 'ANALYTICS' },
  { id: 'strategy-lab', label: 'Quant Lab', icon: FlaskConical, group: 'ANALYTICS' },
  { id: 'screener', label: 'Screener & Heatmap', icon: Flame, group: 'ANALYTICS' },
  { id: 'technical', label: 'Company Research', icon: BarChart3, group: 'ANALYTICS' },
  
  { id: 'portfolio', label: 'Portfolio & Risk', icon: Briefcase, group: 'EXECUTION' },
  { id: 'positions', label: 'Orders & Execution', icon: CheckCircle2, group: 'EXECUTION' },
  { id: 'news', label: 'News & Calendar', icon: Newspaper, group: 'EXECUTION' },
  
  { id: 'settings', label: 'Settings & Brokers', icon: Settings, group: 'SYSTEM' },
];

export const DesktopSidebar: React.FC<DesktopSidebarProps> = ({
  activeTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
}) => {
  return (
    <aside
      className={`hidden md:flex flex-col bg-[#101622] border-r border-[#283345] transition-all duration-300 select-none relative z-20 flex-shrink-0 ${
        collapsed ? 'w-[72px]' : 'w-[240px]'
      }`}
      style={{ minHeight: 'calc(100vh - 105px)' }}
    >
      {/* Toggle button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-6 w-6 h-6 rounded-full bg-[#161F2D] border border-[#283345] text-[#929DB0] hover:text-[#F3F6FC] hover:border-[#B6FF5C] flex items-center justify-center transition-colors shadow-md z-30 cursor-pointer"
        title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
      >
        {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>

      {/* Navigation Groups */}
      <div className="flex-1 py-4 px-2 space-y-6 overflow-y-auto scrollbar-none">
        
        {/* Navigation Items */}
        <div className="space-y-1">
          {DESTINATIONS.map((dest) => {
            const Icon = dest.icon;
            const isActive = activeTab === dest.id || 
              (dest.id === 'overview' && activeTab === 'markets') ||
              (dest.id === 'positions' && activeTab === 'paper-trading') ||
              (dest.id === 'technical' && activeTab === 'explorer');

            return (
              <button
                key={dest.id}
                onClick={() => onSelectTab(dest.id)}
                title={collapsed ? dest.label : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer group relative ${
                  isActive
                    ? 'bg-[#161F2D] text-[#F3F6FC] border border-[#B6FF5C]/40 shadow-[0_0_15px_rgba(182,255,92,0.08)]'
                    : 'text-[#929DB0] hover:text-[#F3F6FC] hover:bg-[#161F2D]/60 border border-transparent'
                }`}
              >
                {/* Active indicator bar */}
                {isActive && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 rounded-r bg-[#B6FF5C] shadow-[0_0_8px_#B6FF5C]" />
                )}

                <Icon
                  className={`w-4 h-4 flex-shrink-0 transition-colors ${
                    isActive ? 'text-[#B6FF5C]' : 'text-[#929DB0] group-hover:text-[#F3F6FC]'
                  }`}
                />

                {!collapsed && (
                  <div className="flex-1 flex items-center justify-between overflow-hidden">
                    <span className="truncate tracking-wide">{dest.label}</span>
                    {dest.badge && (
                      <span
                        className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold uppercase tracking-wider"
                        style={{
                          backgroundColor: `${dest.badgeColor}15`,
                          color: dest.badgeColor,
                          border: `1px solid ${dest.badgeColor}40`,
                        }}
                      >
                        {dest.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>

      </div>

      {/* Footer Info / Safety status */}
      {!collapsed && (
        <div className="p-3 m-2 rounded-lg bg-[#0B1220] border border-[#283345] text-[11px] font-mono text-[#929DB0]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[#F3F6FC] font-bold">PAPER RUNTIME</span>
            <span className="text-[#22C983] font-bold">ACTIVE</span>
          </div>
          <div className="text-[10px] text-[#5E697D]">Live broker orders locked for account safety.</div>
        </div>
      )}
    </aside>
  );
};
