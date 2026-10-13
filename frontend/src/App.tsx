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
  const { user } = useAuth();
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

  return (
    <div
      className="min-h-screen flex flex-col relative overflow-x-hidden"
      style={{
        background: '#080B12',
        color: '#F3F6FC',
      }}
    >
      {/* Background Ambience */}
      <CyberMarketBackground isLowPerf={isLowPerf} />

      {/* ── 1. Top Header ── */}
      <AppHeader
        onSelectTab={setActiveTab}
        onOpenCommandPalette={() => setCommandOpen(true)}
        backendOnline={backendOnline}
        experienceMode={experienceMode}
        onSelectExperienceMode={setExperienceMode}
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
        <main className="flex-1 min-w-0 p-3 sm:p-5 pb-24 md:pb-8 overflow-y-auto">
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

      {/* ── 4. Mobile Bottom Navigation Bar ── */}
      <MobileNavigation
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        onOpenMenu={() => setMobileMenuOpen(true)}
      />

      {/* Mobile Menu Drawer Modal */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col justify-end"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="bg-[#101622] border-t border-[#283345] rounded-t-2xl p-5 space-y-4 max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#283345]">
              <span className="font-bold text-[#F3F6FC] text-sm font-['Outfit']">Platform Navigation</span>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="text-xs font-mono text-[#929DB0] hover:text-[#F3F6FC]"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
              {[
                { id: 'overview', label: 'Dashboard' },
                { id: 'trading', label: 'Trading Desk' },
                { id: 'options', label: 'Option Chain' },
                { id: 'ai-analyst', label: 'AI Intelligence' },
                { id: 'strategy-lab', label: 'Quant Lab' },
                { id: 'screener', label: 'Screener & Heatmap' },
                { id: 'portfolio', label: 'Portfolio & Risk' },
                { id: 'technical', label: 'Company Research' },
                { id: 'news', label: 'News & Calendar' },
                { id: 'positions', label: 'Orders & Execution' },
                { id: 'settings', label: 'Settings & Brokers' },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => {
                    setActiveTab(m.id as NavTab);
                    setMobileMenuOpen(false);
                  }}
                  className={`p-3 rounded-xl text-left border ${
                    activeTab === m.id
                      ? 'bg-[#161F2D] text-[#B6FF5C] border-[#B6FF5C]/40'
                      : 'bg-[#0B1220] text-[#929DB0] border-[#283345]'
                  }`}
                >
                  {m.label}
                </button>
              ))}
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
