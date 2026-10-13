import React from 'react';
import { Search, Bell, Sparkles, User, Shield, Terminal, Settings } from 'lucide-react';
import { CyberLogo } from './CyberLogo';
import { useAuth, ExperienceLevel } from '../../context/AuthContext';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { NavTab } from './Navigation';

interface AppHeaderProps {
  onSelectTab: (tab: NavTab) => void;
  onOpenCommandPalette: () => void;
  backendOnline: boolean | null;
  experienceMode: ExperienceLevel;
  onSelectExperienceMode: (mode: ExperienceLevel) => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  onSelectTab,
  onOpenCommandPalette,
  backendOnline,
  experienceMode,
  onSelectExperienceMode,
}) => {
  const { user, openAuthModal } = useAuth();
  const { account } = usePaperTrading();

  const totalBalance = account.available_balance + account.invested_margin;
  const totalPnl = account.total_pnl;

  return (
    <header className="sticky top-0 z-40 w-full bg-[#101622]/95 backdrop-blur-xl border-b border-[#283345] shadow-[0_4px_25px_rgba(0,0,0,0.5)]">
      <div className="max-w-[1920px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
        
        {/* Left: Brand Logo & Workspace Tag */}
        <div className="flex items-center gap-4 flex-shrink-0">
          <div onClick={() => onSelectTab('overview')} className="cursor-pointer">
            <CyberLogo size="md" />
          </div>

          <div className="hidden xl:flex items-center gap-2 pl-3 border-l border-[#283345]">
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#B6FF5C]/10 text-[#B6FF5C] border border-[#B6FF5C]/30">
              NSE / BSE INSTITUTIONAL
            </span>
          </div>
        </div>

        {/* Center: Global Search Bar with ⌘K Badge */}
        <div className="flex-1 max-w-xl mx-2 hidden sm:block">
          <button
            onClick={onOpenCommandPalette}
            className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-[#0B1220] border border-[#283345] hover:border-[#43D9FF]/50 text-left transition-all group cursor-pointer shadow-inner"
          >
            <div className="flex items-center gap-2.5 text-xs text-[#929DB0] group-hover:text-[#F3F6FC]">
              <Search className="w-4 h-4 text-[#43D9FF]" />
              <span>Search stocks, strikes, AI commands, strategies...</span>
            </div>
            <div className="flex items-center gap-1 font-mono text-[10px] text-[#929DB0] bg-[#161F2D] border border-[#283345] px-1.5 py-0.5 rounded">
              <span>⌘</span>
              <span>K</span>
            </div>
          </button>
        </div>

        {/* Right Controls: Mode, Virtual Wallet, Auth & System Health */}
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          
          {/* Mobile search trigger */}
          <button
            onClick={onOpenCommandPalette}
            className="sm:hidden p-2 rounded-lg bg-[#161F2D] border border-[#283345] text-[#F3F6FC] hover:border-[#43D9FF]"
            title="Search"
          >
            <Search className="w-4 h-4" />
          </button>

          {/* Mode Switcher (Pro vs Standard) */}
          <div className="hidden md:flex items-center bg-[#0B1220] p-1 rounded-lg border border-[#283345]">
            <button
              onClick={() => onSelectExperienceMode('PRO')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold transition-all cursor-pointer ${
                experienceMode === 'PRO'
                  ? 'bg-[#161F2D] text-[#B6FF5C] border border-[#B6FF5C]/30 shadow-xs'
                  : 'text-[#929DB0] hover:text-[#F3F6FC]'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>PRO</span>
            </button>
            <button
              onClick={() => onSelectExperienceMode('BEGINNER')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold transition-all cursor-pointer ${
                experienceMode === 'BEGINNER'
                  ? 'bg-[#161F2D] text-[#43D9FF] border border-[#43D9FF]/30 shadow-xs'
                  : 'text-[#929DB0] hover:text-[#F3F6FC]'
              }`}
            >
              <span>SIMPLE</span>
            </button>
          </div>

          {/* Virtual Paper Portfolio Balance Pill */}
          <div
            onClick={() => onSelectTab('portfolio')}
            className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#0B1220] border border-[#283345] hover:border-[#B6FF5C]/40 transition-colors cursor-pointer"
            title="Click to view full portfolio & risk analysis"
          >
            <div className="text-right">
              <div className="text-[10px] font-mono text-[#929DB0]">SIMULATED CAPITAL</div>
              <div className="text-xs font-mono font-extrabold text-[#F3F6FC]">
                ₹{totalBalance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </div>
            </div>
            <div className="h-6 w-px bg-[#283345]" />
            <div className="text-left">
              <div className="text-[10px] font-mono text-[#929DB0]">P&L</div>
              <div className={`text-xs font-mono font-bold ${totalPnl >= 0 ? 'text-[#22C983]' : 'text-[#FF5D6C]'}`}>
                {totalPnl >= 0 ? '+' : ''}₹{totalPnl.toFixed(1)}
              </div>
            </div>
          </div>

          {/* AI Quick Research button */}
          <button
            onClick={() => onSelectTab('ai-analyst')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-[#B6FF5C]/20 to-[#43D9FF]/20 border border-[#B6FF5C]/40 text-[#F3F6FC] hover:border-[#B6FF5C] transition-all cursor-pointer text-xs font-bold shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#B6FF5C]" />
            <span className="hidden sm:inline">AI Analyst</span>
          </button>

          {/* Backend Online status ping */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#0B1220] border border-[#283345] text-[11px] font-mono"
            title={backendOnline ? 'FastAPI Backend Online' : 'Simulation Mode'}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline ? 'bg-[#22C983] shadow-[0_0_8px_#22C983]' : 'bg-amber-400'
              }`}
            />
            <span className="hidden sm:inline text-[#929DB0]">
              {backendOnline ? 'CORE ONLINE' : 'SIMULATION'}
            </span>
          </div>

          {/* User Profile Pill */}
          <button
            onClick={openAuthModal}
            className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-[#161F2D] hover:bg-[#1a2536] border border-[#283345] transition-colors cursor-pointer"
            title="Account Profile & Settings"
          >
            <span className="text-sm">{user ? user.avatar : '👤'}</span>
            <span className="hidden sm:inline text-xs font-bold text-[#F3F6FC]">
              {user ? user.fullName.split(' ')[0] : 'Trader'}
            </span>
          </button>

        </div>

      </div>
    </header>
  );
};
