import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Navigation, NavTab } from './components/layout/Navigation';
import { Footer } from './components/layout/Footer';
import { CommandPalette } from './components/ui/CommandPalette';
import { ToastProvider, useToast } from './components/ui/Toast';
import { PageTransition } from './components/ui/PageTransition';
import { OptionsCommandView } from './views/OptionsCommandView';
import { TradingTerminalView } from './views/TradingTerminalView';
import { TechnicalAnalysisDeskView } from './views/TechnicalAnalysisDeskView';
import { NewsView } from './views/NewsView';
import { OthersToolsView } from './views/OthersToolsView';
import { LandingLoginPage } from './components/auth/LandingLoginPage';
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
  const [activeTab, setActiveTab] = useState<NavTab>('trading');
  const [commandOpen, setCommandOpen] = useState(false);
  const [isLowPerf, setIsLowPerf] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const [, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

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
      if (backendOnline !== false) {
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

  const [experienceMode, setExperienceMode] = useState<ExperienceLevel>('PRO');

  // Initial load
  useEffect(() => { fetchAll(true); }, []); // eslint-disable-line

  // Poll every 30s during market hours
  useEffect(() => {
    if (!marketOpen) return;
    const interval = setInterval(() => fetchAll(false), 30000);
    return () => clearInterval(interval);
  }, [marketOpen, fetchAll]);

  // 1. Initial Gate: If user is not authenticated, show Landing Login / Registration Page!
  if (!user) {
    return <LandingLoginPage />;
  }

  // 2. Authenticated State: Full Website Experience
  return (
    <div
      className="min-h-screen flex flex-col relative overflow-x-hidden"
      style={{
        background: 'transparent',
        color: 'var(--text-primary)',
      }}
    >
      {/* Live Animated Background */}
      <CyberMarketBackground isLowPerf={isLowPerf} />

      {/* Sticky Navigation (Contains Top Welcome Tagline, Live Index Tickers & 6 Nav Tabs) */}
      <Navigation
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isLowPerf={isLowPerf}
        onToggleLowPerf={() => setIsLowPerf(p => !p)}
        marketOpen={marketOpen}
        onOpenCommandPalette={() => setCommandOpen(true)}
        experienceMode={experienceMode}
        onSelectExperienceMode={(mode) => setExperienceMode(mode)}
      />

      {/* Command palette */}
      <CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
        onNavigate={setActiveTab}
        activeTab={activeTab}
      />

      {/* Main Terminal Viewport (The 6 Sections) */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 py-5 pb-16 relative z-10">
        <AnimatePresence mode="wait">
          {/* Section 1: Trading Desk */}
          {activeTab === 'trading' && (
            <PageTransition tabKey="trading">
              <TradingTerminalView onNavigateToOptions={() => setActiveTab('options')} />
            </PageTransition>
          )}

          {/* Section 2: Technical Analysis */}
          {activeTab === 'technical' && (
            <PageTransition tabKey="technical">
              <TechnicalAnalysisDeskView />
            </PageTransition>
          )}

          {/* Section 3: News */}
          {activeTab === 'news' && (
            <PageTransition tabKey="news">
              <NewsView />
            </PageTransition>
          )}

          {/* Section 4: Option Chain */}
          {activeTab === 'options' && (
            <PageTransition tabKey="options">
              <OptionsCommandView chain={chain} expiries={expiries} />
            </PageTransition>
          )}

          {/* Section 5: Position & P&L */}
          {activeTab === 'positions' && (
            <PageTransition tabKey="positions">
              <div className="space-y-4">
                <PortfolioDesk onNavigateToOptions={() => setActiveTab('trading')} />
              </div>
            </PageTransition>
          )}

          {/* Section 6: Others Tools */}
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
