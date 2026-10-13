import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { NavTab } from './components/layout/Navigation';
import { AppHeader } from './components/layout/AppHeader';
import { MarketTickerTape } from './components/layout/MarketTickerTape';
import { DesktopSidebar } from './components/layout/DesktopSidebar';
import { MobileNavigation } from './components/layout/MobileNavigation';
import { Footer } from './components/layout/Footer';
import { CommandPalette } from './components/ui/CommandPalette';
import { ToastProvider, useToast } from './components/ui/Toast';
import { PageTransition } from './components/ui/PageTransition';

import { HomeMarketOverviewView } from './views/HomeMarketOverviewView';
import { TradingTerminalView } from './views/TradingTerminalView';
import { OptionsChainPageView } from './views/OptionsChainPageView';
import { AIMarketAnalystView } from './views/AIMarketAnalystView';
import { StrategyLabView } from './views/StrategyLabView';
import { WatchlistPortfolioView } from './views/WatchlistPortfolioView';
import { ScreenerHeatmapView } from './views/ScreenerHeatmapView';
import { TechnicalAnalysisDeskView } from './views/TechnicalAnalysisDeskView';
import { NewsView } from './views/NewsView';
import { SettingsConnectionsView } from './views/SettingsConnectionsView';
import { OthersToolsView } from './views/OthersToolsView';

import { PaperTradingProvider } from './context/PaperTradingContext';
import { AuthProvider, useAuth, ExperienceLevel } from './context/AuthContext';
import { AuthModal } from './components/auth/AuthModal';
import { LandingLoginPage } from './components/auth/LandingLoginPage';
import { CyberMarketBackground } from './components/background/CyberMarketBackground';
import { OrderPadModal } from './components/trading/OrderPadModal';
import { PortfolioDesk } from './components/trading/PortfolioDesk';
import { ThemeProvider } from './context/ThemeContext';
import { api } from './api/client';
import {
  MarketQuote, Candle, OptionChainSnapshot,
  ProviderHealth, MarketRegime,
} from './types/market';

// ─── Default state (shown while loading / backend offline) ──────────────────
const DEFAULT_NIFTY: MarketQuote = {
  symbol: 'NIFTY', provider: 'NSE', last_price: 24652.8,
  bid_price: null, ask_price: null, volume: 142800000,
  data_status: 'DELAYED', is_executable: false,
  execution_rejection_reason: 'HISTORICAL_OR_DELAYED',
  price_classification: 'VALUATION_MARK_ONLY', timestamps: {},
};
const DEFAULT_BANKNIFTY: MarketQuote = {
  symbol: 'BANKNIFTY', provider: 'NSE', last_price: 51240.5,
  bid_price: null, ask_price: null, volume: 84300000,
  data_status: 'DELAYED', is_executable: false,
  execution_rejection_reason: 'HISTORICAL_OR_DELAYED',
  price_classification: 'VALUATION_MARK_ONLY', timestamps: {},
};
const DEFAULT_CHAIN: OptionChainSnapshot = {
  underlying: 'NIFTY', spot_price: 24652.8, expiry: 'NEAR_MONTH',
  atm_strike: 24650, pcr: 0.94, total_call_oi: 1245000,
  total_put_oi: 1170300, max_pain: 24600, iv_regime: 'NORMAL',
  rows: [], status: 'HISTORICAL',
};
const DEFAULT_REGIME: MarketRegime = {
  symbol: 'NIFTY', regime: 'RANGE', confidence: 0.72,
  adx: 18.4, atr: 142.5, historical_volatility: 13.8,
  transition_probabilities: { TREND: 0.15, RANGE: 0.65, BREAKOUT: 0.1, HIGH_VOLATILITY: 0.1 },
  data_status: 'HISTORICAL',
};

// ─── Inner app (needs access to toast and auth context) ───────────────────────
function AppInner() {
  const { user, logout } = useAuth();
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [commandOpen, setCommandOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isLowPerf, setIsLowPerf] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const [, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [experienceMode, setExperienceMode] = useState<ExperienceLevel>('PRO');

  // Data state
  const [niftyQuote, setNiftyQuote] = useState<MarketQuote>(DEFAULT_NIFTY);
  const [bankniftyQuote, setBankniftyQuote] = useState<MarketQuote>(DEFAULT_BANKNIFTY);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [chain, setChain] = useState<OptionChainSnapshot>(DEFAULT_CHAIN);
  const [expiries, setExpiries] = useState<string[]>([]);
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [regime, setRegime] = useState<MarketRegime>(DEFAULT_REGIME);

  const fetchAll = useCallback(async (isInitial = false) => {
    let online = false;
    try {
      const health = await api.getHealth();
      setMarketOpen(health.market_open);
      online = true;
      if (backendOnline === false) {
        addToast('Backend reconnected — live data streaming.', 'success');
      }
    } catch {
      if (backendOnline !== false && !isInitial) {
        addToast('Showing simulated exchange data.', 'info', 4000);
      }
    }

    setBackendOnline(online);

    const fetches = [
      api.getMarketQuote('NIFTY').then(q => { if (q?.last_price > 0) setNiftyQuote(q); }).catch(() => {}),
      api.getMarketQuote('BANKNIFTY').then(q => { if (q?.last_price > 0) setBankniftyQuote(q); }).catch(() => {}),
      api.getMarketCandles('NIFTY', '1D', 50).then(c => { if (c.length > 0) setCandles(c); }).catch(() => {}),
      api.getOptionExpiries('NIFTY').then(e => { if (e.length > 0) setExpiries(e); }).catch(() => {}),
      api.getOptionChain('NIFTY').then(c => { if (c) setChain(c); }).catch(() => {}),
      api.getProvidersHealth().then(p => { if (p.length > 0) setProviders(p); }).catch(() => {}),
      api.getMarketRegime('NIFTY').then(r => { if (r) setRegime(r); }).catch(() => {}),
    ];

    await Promise.allSettled(fetches);
    if (isInitial) setLoading(false);
  }, [backendOnline, addToast]);

  // Initial load
  useEffect(() => { fetchAll(true); }, []); // eslint-disable-line

  // Poll every 30s during market hours
  useEffect(() => {
    if (!marketOpen) return;
    const interval = setInterval(() => fetchAll(false), 30000);
    return () => clearInterval(interval);
  }, [marketOpen, fetchAll]);

  // Keyboard shortcut ⌘K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Show Landing & Login Page if not authenticated
  if (!user) {
    return <LandingLoginPage />;
  }

  return (
    <div
      className="min-h-screen flex flex-col relative overflow-x-hidden bg-[#080B12]/85 text-[#F3F6FC] backdrop-blur-[1px]"
    >
      {/* Background Ambience & Live Candlestick Video Display */}
      <CyberMarketBackground isLowPerf={isLowPerf} />

      {/* ── 1. Top Header ── */}
      <AppHeader
        onSelectTab={setActiveTab}
        onOpenCommandPalette={() => setCommandOpen(true)}
        backendOnline={backendOnline}
        experienceMode={experienceMode}
        onSelectExperienceMode={setExperienceMode}
      />

      {/* ── 1.1 Mobile Top Navigation & Floating Trigger ── */}
      <MobileNavigation
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenMenu={() => setMobileMenuOpen(true)}
      />

      {/* ── 2. Market Ticker Marquee Strip ── */}
      <MarketTickerTape />

      {/* ── 3. Main Split Shell (Sidebar + Viewport) ── */}
      <div className="flex-1 flex max-w-[1920px] w-full mx-auto relative z-10">
        
        {/* Desktop Sidebar Dock */}
        <DesktopSidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(c => !c)}
        />

        {/* Dynamic Viewport Container */}
        <main className="flex-1 min-w-0 p-3 sm:p-5 pb-10 md:pb-8 overflow-y-auto">
          <AnimatePresence mode="wait">
            
            {/* 1. Home Dashboard */}
            {(activeTab === 'overview' || activeTab === 'markets') && (
              <PageTransition tabKey="overview">
                <HomeMarketOverviewView
                  onNavigate={setActiveTab}
                  onSelectSymbol={() => setActiveTab('trading')}
                />
              </PageTransition>
            )}

            {/* 2. Trading Terminal */}
            {activeTab === 'trading' && (
              <PageTransition tabKey="trading">
                <TradingTerminalView onNavigateToOptions={() => setActiveTab('options')} />
              </PageTransition>
            )}

            {/* 3. Options Terminal */}
            {activeTab === 'options' && (
              <PageTransition tabKey="options">
                <OptionsChainPageView chain={chain} expiries={expiries} />
              </PageTransition>
            )}

            {/* 4. AI Market Intelligence */}
            {activeTab === 'ai-analyst' && (
              <PageTransition tabKey="ai-analyst">
                <AIMarketAnalystView
                  onNavigateToOptions={() => setActiveTab('options')}
                  onNavigateToStrategy={() => setActiveTab('strategy-lab')}
                />
              </PageTransition>
            )}

            {/* 5. Quant Lab & Backtesting */}
            {activeTab === 'strategy-lab' && (
              <PageTransition tabKey="strategy-lab">
                <StrategyLabView
                  onNavigateToPaper={() => setActiveTab('positions')}
                />
              </PageTransition>
            )}

            {/* 6. Screener & Sector Heatmap */}
            {activeTab === 'screener' && (
              <PageTransition tabKey="screener">
                <ScreenerHeatmapView
                  onNavigateToTrade={() => setActiveTab('trading')}
                  onNavigateToOptions={() => setActiveTab('options')}
                />
              </PageTransition>
            )}

            {/* 7. Portfolio & Risk Management */}
            {activeTab === 'portfolio' && (
              <PageTransition tabKey="portfolio">
                <WatchlistPortfolioView
                  onNavigateToOptions={() => setActiveTab('options')}
                  onNavigateToExplorer={() => setActiveTab('technical')}
                />
              </PageTransition>
            )}

            {/* 8. Company Research & Financials */}
            {(activeTab === 'technical' || activeTab === 'explorer') && (
              <PageTransition tabKey="technical">
                <TechnicalAnalysisDeskView />
              </PageTransition>
            )}

            {/* 9. News & Economic Calendar */}
            {activeTab === 'news' && (
              <PageTransition tabKey="news">
                <NewsView />
              </PageTransition>
            )}

            {/* 10. Orders & Execution */}
            {(activeTab === 'positions' || activeTab === 'paper-trading') && (
              <PageTransition tabKey="positions">
                <PortfolioDesk onNavigateToOptions={() => setActiveTab('trading')} />
              </PageTransition>
            )}

            {/* 11. Settings & Connections */}
            {activeTab === 'settings' && (
              <PageTransition tabKey="settings">
                <SettingsConnectionsView />
              </PageTransition>
            )}

            {/* Supplementary 3D Volatility & Diagnostics */}
            {activeTab === 'tools' && (
              <PageTransition tabKey="tools">
                <OthersToolsView
                  niftyQuote={niftyQuote}
                  bankniftyQuote={bankniftyQuote}
                  candles={candles}
                  regime={regime}
                  providers={providers}
                  isLowPerf={isLowPerf}
                />
              </PageTransition>
            )}

          </AnimatePresence>
        </main>
      </div>

      {/* Mobile Menu Drawer Modal */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col justify-end"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="bg-[#101622] border-t border-[#283345] rounded-t-3xl p-5 space-y-4 max-h-[85vh] overflow-y-auto shadow-2xl animate-in slide-in-from-bottom duration-300"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header: User & Margin Meta */}
            <div className="flex items-center justify-between pb-3.5 border-b border-[#283345]">
              <div>
                <div className="text-xs font-mono text-[#929DB0] uppercase">Active Trading Desk</div>
                <div className="font-bold text-[#F3F6FC] text-sm font-['Outfit'] flex items-center gap-2">
                  <span>{user?.fullName || 'VIP HFT Trader'}</span>
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-[#B6FF5C]/15 text-[#B6FF5C] border border-[#B6FF5C]/30">
                    LIVE SIM
                  </span>
                </div>
              </div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1.5 rounded-xl bg-[#161F2D] border border-[#283345] text-[#929DB0] hover:text-[#F3F6FC]"
              >
                ✕
              </button>
            </div>

            {/* Quick Command Search Trigger */}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                setCommandOpen(true);
              }}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#929DB0]"
            >
              <span>Search stocks, strikes, commands...</span>
              <span className="px-1.5 py-0.5 rounded bg-[#161F2D] text-[#43D9FF] text-[10px]">⌘K</span>
            </button>

            {/* Desk Navigation Matrix */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono font-bold">
              {[
                { id: 'overview', label: 'Dashboard', icon: '⚡' },
                { id: 'trading', label: 'Trading Desk', icon: '📈' },
                { id: 'options', label: 'Option Chain', icon: '📊' },
                { id: 'ai-analyst', label: 'AI Intelligence', icon: '🧠' },
                { id: 'strategy-lab', label: 'Quant Lab', icon: '🔬' },
                { id: 'screener', label: 'Screener', icon: '🎯' },
                { id: 'portfolio', label: 'Portfolio & Risk', icon: '💼' },
                { id: 'technical', label: 'Technical Desk', icon: '📉' },
                { id: 'news', label: 'Market News', icon: '📰' },
                { id: 'positions', label: 'Orders & P&L', icon: '📑' },
                { id: 'settings', label: 'Brokers & Keys', icon: '⚙️' },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => {
                    setActiveTab(m.id as NavTab);
                    setMobileMenuOpen(false);
                  }}
                  className={`p-3 rounded-xl text-left border transition-all flex items-center gap-2 ${
                    activeTab === m.id
                      ? 'bg-[#161F2D] text-[#B6FF5C] border-[#B6FF5C]/50 shadow-[0_0_15px_rgba(182,255,92,0.15)]'
                      : 'bg-[#0B1220] text-[#929DB0] border-[#283345] hover:text-[#F3F6FC]'
                  }`}
                >
                  <span className="text-sm">{m.icon}</span>
                  <span className="truncate">{m.label}</span>
                </button>
              ))}
            </div>

            {/* Logout / Exit Portal Action */}
            <div className="pt-2 border-t border-[#283345]">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  logout();
                }}
                className="w-full py-2.5 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-400 font-mono text-xs font-bold hover:bg-rose-500/20 transition-all text-center"
              >
                Exit Desk / Return to Landing
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── 5. Command Palette ── */}
      <CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
        onNavigate={setActiveTab}
        activeTab={activeTab}
      />

      <Footer />
    </div>
  );
}

// ─── Root with providers ─────────────────────────────────────────────────────
export const App: React.FC = () => (
  <ToastProvider>
    <ThemeProvider>
      <AuthProvider>
        <PaperTradingProvider>
          <AppInner />
          <OrderPadModal />
          <AuthModal />
        </PaperTradingProvider>
      </AuthProvider>
    </ThemeProvider>
  </ToastProvider>
);

export default App;
