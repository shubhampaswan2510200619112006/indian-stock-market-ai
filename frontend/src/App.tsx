import React, { useState, useEffect, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Navigation, NavTab } from './components/layout/Navigation';
import { StatusBanner } from './components/layout/StatusBanner';
import { Footer } from './components/layout/Footer';
import { CommandPalette } from './components/ui/CommandPalette';
import { ToastProvider, useToast } from './components/ui/Toast';
import { PageTransition } from './components/ui/PageTransition';
import { OverviewView } from './views/OverviewView';
import { MarketsView } from './views/MarketsView';
import { OptionsCommandView } from './views/OptionsCommandView';
import { VolatilityStudioView } from './views/VolatilityStudioView';
import { ResearchGovernanceView } from './views/ResearchGovernanceView';
import { DataHealthView } from './views/DataHealthView';
import { TradingTerminalView } from './views/TradingTerminalView';
import { BeginnerTerminalView } from './views/BeginnerTerminalView';
import { NewsView } from './views/NewsView';
import { PaperTradingProvider } from './context/PaperTradingContext';
import { AuthProvider, ExperienceLevel } from './context/AuthContext';
import { AuthModal } from './components/auth/AuthModal';
import { CyberMarketBackground } from './components/background/CyberMarketBackground';
import { OrderPadModal } from './components/trading/OrderPadModal';
import { PortfolioDesk } from './components/trading/PortfolioDesk';
import { api } from './api/client';
import {
  MarketQuote, Candle, OptionChainSnapshot,
  ProviderHealth, MarketRegime, GovernanceState,
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

// ─── Inner app (needs access to toast context) ───────────────────────────────
function AppInner() {
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState<NavTab>('trading');
  const [commandOpen, setCommandOpen] = useState(false);
  const [isLowPerf, setIsLowPerf] = useState(false);
  const [marketOpen, setMarketOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Data state
  const [niftyQuote, setNiftyQuote] = useState<MarketQuote>(DEFAULT_NIFTY);
  const [bankniftyQuote, setBankniftyQuote] = useState<MarketQuote>(DEFAULT_BANKNIFTY);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [chain, setChain] = useState<OptionChainSnapshot>(DEFAULT_CHAIN);
  const [expiries, setExpiries] = useState<string[]>([]);
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [regime, setRegime] = useState<MarketRegime>(DEFAULT_REGIME);
  const governance: GovernanceState = api.getGovernanceState();

  const fetchAll = useCallback(async (isInitial = false) => {
    let online = false;
    try {
      const health = await api.getHealth();
      setMarketOpen(health.market_open);
      online = true;
      if (backendOnline === false) {
        addToast('Backend reconnected — data refreshed.', 'success');
      }
    } catch {
      if (backendOnline !== false) {
        addToast('Backend offline — showing cached data.', 'error', 6000);
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

  // Experience Mode State (BEGINNER vs PRO vs QUANT)
  const [experienceMode, setExperienceMode] = useState<ExperienceLevel>('PRO');

  // Initial load
  useEffect(() => { fetchAll(true); }, []); // eslint-disable-line

  // Poll every 30s during market hours
  useEffect(() => {
    if (!marketOpen) return;
    const interval = setInterval(() => fetchAll(false), 30000);
    return () => clearInterval(interval);
  }, [marketOpen, fetchAll]);

  return (
    <div
      className="min-h-screen flex flex-col relative overflow-x-hidden"
      style={{
        background: 'transparent',
        color: 'var(--text-primary)',
      }}
    >
      {/* 1. Live Ambient Market Background */}
      <CyberMarketBackground isLowPerf={isLowPerf} />

      {/* 2. Sticky Clean Navigation */}
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

      {/* 3. Command palette */}
      <CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
        onNavigate={setActiveTab}
        activeTab={activeTab}
      />

      {/* 4. Main content (Simple, Sweet & Focused) */}
      <main className="flex-1 max-w-[1500px] w-full mx-auto px-4 py-5 pb-16 relative z-10">
        <AnimatePresence mode="wait">
          {activeTab === 'trading' && (
            <PageTransition tabKey="trading">
              <TradingTerminalView />
            </PageTransition>
          )}
          {activeTab === 'positions' && (
            <PageTransition tabKey="positions">
              <div className="space-y-4">
                <PortfolioDesk onNavigateToOptions={() => setActiveTab('trading')} />
              </div>
            </PageTransition>
          )}
          {activeTab === 'news' && (
            <PageTransition tabKey="news">
              <NewsView />
            </PageTransition>
          )}
          {activeTab === 'overview' && (
            <PageTransition tabKey="overview">
              <OverviewView
                niftyQuote={niftyQuote}
                bankniftyQuote={bankniftyQuote}
                regime={regime}
                isLowPerf={isLowPerf}
                onNavigate={setActiveTab}
              />
            </PageTransition>
          )}
          {activeTab === 'markets' && (
            <PageTransition tabKey="markets">
              <MarketsView
                niftyQuote={niftyQuote}
                bankniftyQuote={bankniftyQuote}
                candles={candles}
                regime={regime}
              />
            </PageTransition>
          )}
          {activeTab === 'options' && (
            <PageTransition tabKey="options">
              <OptionsCommandView chain={chain} expiries={expiries} />
            </PageTransition>
          )}
          {activeTab === 'volatility' && (
            <PageTransition tabKey="volatility">
              <VolatilityStudioView isLowPerf={isLowPerf} />
            </PageTransition>
          )}
          {activeTab === 'research' && (
            <PageTransition tabKey="research">
              <ResearchGovernanceView />
            </PageTransition>
          )}
          {activeTab === 'data-health' && (
            <PageTransition tabKey="data-health">
              <DataHealthView providers={providers} />
            </PageTransition>
          )}
        </AnimatePresence>
      </main>

      <Footer />
    </div>
  );
}

import { ThemeProvider } from './context/ThemeContext';

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
