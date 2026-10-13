import React from 'react';
import { Activity, TrendingUp, Layers, Sparkles, Menu } from 'lucide-react';
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
  const tabs: { id: NavTab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Home', icon: Activity },
    { id: 'trading', label: 'Trade', icon: TrendingUp },
    { id: 'options', label: 'Options', icon: Layers },
    { id: 'ai-analyst', label: 'AI', icon: Sparkles },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#101622]/95 backdrop-blur-xl border-t border-[#283345] px-2 py-1.5 shadow-[0_-4px_20px_rgba(0,0,0,0.6)]">
      <div className="flex items-center justify-around">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id || (tab.id === 'overview' && activeTab === 'markets');

          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer ${
                isActive ? 'text-[#B6FF5C]' : 'text-[#929DB0] hover:text-[#F3F6FC]'
              }`}
            >
              <Icon className="w-5 h-5 mb-0.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}

        {/* More Menu Drawer Trigger */}
        <button
          onClick={onOpenMenu}
          className="flex flex-col items-center justify-center py-1 px-3 rounded-lg text-[10px] font-semibold text-[#929DB0] hover:text-[#F3F6FC] transition-colors cursor-pointer"
        >
          <Menu className="w-5 h-5 mb-0.5" />
          <span>More</span>
        </button>
      </div>
    </nav>
  );
};
