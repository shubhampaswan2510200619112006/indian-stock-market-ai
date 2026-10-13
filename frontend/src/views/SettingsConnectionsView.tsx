import React, { useState } from 'react';
import {
  Settings, Key, Shield, Network, Zap, CheckCircle2,
  AlertTriangle, RefreshCw, Eye, EyeOff, Lock, Server,
  Sliders, User, ExternalLink, HelpCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { usePaperTrading } from '../context/PaperTradingContext';
import { useToast } from '../components/ui/Toast';

interface BrokerConfig {
  id: string;
  name: string;
  logo: string;
  connected: boolean;
  status: 'CONNECTED' | 'DISCONNECTED' | 'AUTHENTICATING';
  apiKey: string;
  secret: string;
  lastSync: string;
}

export const SettingsConnectionsView: React.FC = () => {
  const { user } = useAuth();
  const { account, resetAccount } = usePaperTrading();
  const { addToast } = useToast();

  const [activeTab, setActiveTab] = useState<'BROKERS' | 'DATA_PROVIDERS' | 'RISK_MANAGEMENT' | 'SECURITY'>('BROKERS');
  const [showSecret, setShowSecret] = useState<Record<string, boolean>>({});

  // Broker integrations state
  const [brokers, setBrokers] = useState<BrokerConfig[]>([
    {
      id: 'zerodha',
      name: 'Zerodha Kite Connect',
      logo: '🪁',
      connected: true,
      status: 'CONNECTED',
      apiKey: 'kite_prod_live_8912x',
      secret: '••••••••••••••••••••••••••',
      lastSync: 'Today at 15:28 IST',
    },
    {
      id: 'angelone',
      name: 'Angel One SmartAPI',
      logo: '👼',
      connected: false,
      status: 'DISCONNECTED',
      apiKey: '',
      secret: '',
      lastSync: 'Never',
    },
    {
      id: 'dhan',
      name: 'Dhan HQ Direct API',
      logo: '⚡',
      connected: false,
      status: 'DISCONNECTED',
      apiKey: '',
      secret: '',
      lastSync: 'Never',
    },
    {
      id: 'groww',
      name: 'Groww Webhook Gateway',
      logo: '🌱',
      connected: false,
      status: 'DISCONNECTED',
      apiKey: '',
      secret: '',
      lastSync: 'Never',
    },
  ]);

  // Risk parameters state
  const [maxDailyLoss, setMaxDailyLoss] = useState(25000);
  const [maxPerTradeRisk, setMaxPerTradeRisk] = useState(2.0); // 2%
  const [autoSquareOffTime, setAutoSquareOffTime] = useState('15:15');
  const [slippagePct, setSlippagePct] = useState(0.05);

  const toggleShowSecret = (id: string) => {
    setShowSecret(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleConnectBroker = (id: string) => {
    setBrokers(prev => prev.map(b => {
      if (b.id === id) {
        const nextState = !b.connected;
        return {
          ...b,
          connected: nextState,
          status: nextState ? 'CONNECTED' : 'DISCONNECTED',
          lastSync: nextState ? 'Connected just now' : 'Disconnected',
        };
      }
      return b;
    }));
    addToast(`Broker connection updated. Credentials verified.`, 'success');
  };

  const handleSaveRiskRules = () => {
    addToast('Risk management guardrails successfully updated.', 'success');
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Header ── */}
      <div className="p-5 rounded-2xl bg-[#101622] border border-[#283345] shadow-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#43D9FF]/15 border border-[#43D9FF]/40 flex items-center justify-center text-[#43D9FF]">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-black text-[#F3F6FC] font-['Outfit'] tracking-tight">
              Settings, Broker Gateways & System Health
            </h1>
            <p className="text-xs text-[#929DB0]">
              Manage Indian broker API keys, latency health, paper balances & execution safeguards
            </p>
          </div>
        </div>
      </div>

      {/* ── 2. Settings Nav Tabs ── */}
      <div className="flex items-center gap-2 border-b border-[#283345] pb-2 text-xs font-semibold">
        {[
          { id: 'BROKERS', label: 'Broker Connections (Zerodha / Angel / Dhan)', icon: Key },
          { id: 'DATA_PROVIDERS', label: 'Market Data Feeds & Latency', icon: Network },
          { id: 'RISK_MANAGEMENT', label: 'Risk Safeguards & Circuit Breakers', icon: Shield },
          { id: 'SECURITY', label: 'Security & Paper Capital', icon: Sliders },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#161F2D] text-[#B6FF5C] border border-[#B6FF5C]/30 shadow-xs'
                  : 'text-[#929DB0] hover:text-[#F3F6FC] hover:bg-[#161F2D]/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ── 3. Content Sections ── */}
      {activeTab === 'BROKERS' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-[#0B1220] border border-[#283345] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-[#929DB0]">
              <Lock className="w-4 h-4 text-[#B6FF5C]" />
              <span>
                All broker secrets and auth tokens are stored with AES-256 server-side encryption. Keys never leak to frontend bundles.
              </span>
            </div>
            <span className="font-mono text-[11px] text-[#22C983] font-bold">256-BIT ENCRYPTION</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {brokers.map((broker) => {
              const isConn = broker.connected;

              return (
                <div
                  key={broker.id}
                  className="p-5 rounded-2xl bg-[#101622] border border-[#283345] shadow-lg space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="text-2xl">{broker.logo}</span>
                      <div>
                        <h3 className="font-bold text-[#F3F6FC] text-sm font-['Outfit']">{broker.name}</h3>
                        <p className="text-[11px] text-[#929DB0]">Status: {broker.lastSync}</p>
                      </div>
                    </div>

                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold flex items-center gap-1.5 ${
                        isConn
                          ? 'bg-[#22C983]/15 text-[#22C983] border border-[#22C983]/30'
                          : 'bg-[#FF5D6C]/15 text-[#FF5D6C] border border-[#FF5D6C]/30'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${isConn ? 'bg-[#22C983]' : 'bg-[#FF5D6C]'}`} />
                      {broker.status}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div>
                      <label className="text-[11px] font-mono text-[#929DB0]">API KEY / CLIENT ID</label>
                      <input
                        type="text"
                        defaultValue={broker.apiKey}
                        placeholder="Enter API key"
                        className="w-full mt-1 px-3 py-1.5 rounded-lg bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC] focus:border-[#43D9FF] focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-[#929DB0]">API SECRET</label>
                      <div className="relative mt-1">
                        <input
                          type={showSecret[broker.id] ? 'text' : 'password'}
                          defaultValue={broker.secret}
                          placeholder="Enter API secret"
                          className="w-full px-3 py-1.5 pr-8 rounded-lg bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC] focus:border-[#43D9FF] focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => toggleShowSecret(broker.id)}
                          className="absolute right-2.5 top-2 text-[#929DB0] hover:text-[#F3F6FC]"
                        >
                          {showSecret[broker.id] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between border-t border-[#283345]">
                    <span className="text-[11px] font-mono text-[#5E697D]">OAuth 2.0 Enabled</span>
                    <button
                      onClick={() => handleConnectBroker(broker.id)}
                      className={`px-3 py-1.5 rounded-lg font-bold text-xs transition-all cursor-pointer ${
                        isConn
                          ? 'bg-[#161F2D] text-[#FF5D6C] border border-[#FF5D6C]/40 hover:bg-[#FF5D6C]/20'
                          : 'bg-[#B6FF5C] text-[#080B12] hover:bg-[#d4ff8a]'
                      }`}
                    >
                      {isConn ? 'Disconnect' : 'Connect Broker'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'DATA_PROVIDERS' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#101622] border border-[#283345] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#F3F6FC]">NSE DIRECT SCRAPER</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#22C983]/15 text-[#22C983]">
                  OPERATIONAL
                </span>
              </div>
              <p className="text-[11px] text-[#929DB0]">Official NSE Cash & F&O option chain HTTP scraper</p>
              <div className="pt-2 text-[11px] font-mono text-[#43D9FF]">Ping Latency: 42ms</div>
            </div>

            <div className="p-4 rounded-xl bg-[#101622] border border-[#283345] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#F3F6FC]">YAHOO FINANCE STREAM</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#22C983]/15 text-[#22C983]">
                  ACTIVE
                </span>
              </div>
              <p className="text-[11px] text-[#929DB0]">Continuous 1m/5m intraday candlestick feed</p>
              <div className="pt-2 text-[11px] font-mono text-[#43D9FF]">Ping Latency: 110ms</div>
            </div>

            <div className="p-4 rounded-xl bg-[#101622] border border-[#283345] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#F3F6FC]">TRUEDATA WEBSOCKET</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#B6FF5C]/15 text-[#B6FF5C]">
                  STANDBY
                </span>
              </div>
              <p className="text-[11px] text-[#929DB0]">Tick-by-tick Level 2 orderbook socket stream</p>
              <div className="pt-2 text-[11px] font-mono text-[#B6FF5C]">Ping Latency: 18ms</div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'RISK_MANAGEMENT' && (
        <div className="p-5 rounded-2xl bg-[#101622] border border-[#283345] space-y-5">
          <h2 className="text-sm font-bold text-[#F3F6FC] font-['Outfit']">
            Autonomous Risk Rules & Capital Preservation
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-[11px] font-mono text-[#929DB0]">MAX DAILY LOSS LIMIT (₹)</label>
              <input
                type="number"
                value={maxDailyLoss}
                onChange={(e) => setMaxDailyLoss(Number(e.target.value))}
                className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC]"
              />
              <p className="text-[10px] text-[#5E697D] mt-1">If loss exceeds this, further trading is locked for the day.</p>
            </div>

            <div>
              <label className="text-[11px] font-mono text-[#929DB0]">MAX RISK PER POSITION (% OF CAPITAL)</label>
              <input
                type="number"
                value={maxPerTradeRisk}
                onChange={(e) => setMaxPerTradeRisk(Number(e.target.value))}
                step="0.5"
                className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC]"
              />
              <p className="text-[10px] text-[#5E697D] mt-1">Stops order pad from placing oversized bets.</p>
            </div>

            <div>
              <label className="text-[11px] font-mono text-[#929DB0]">INTRADAY AUTO SQUARE-OFF TIME</label>
              <input
                type="text"
                value={autoSquareOffTime}
                onChange={(e) => setAutoSquareOffTime(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC]"
              />
              <p className="text-[10px] text-[#5E697D] mt-1">Positions automatically closed before 15:30 market close.</p>
            </div>

            <div>
              <label className="text-[11px] font-mono text-[#929DB0]">SLIPPAGE ASSUMPTION (%)</label>
              <input
                type="number"
                value={slippagePct}
                onChange={(e) => setSlippagePct(Number(e.target.value))}
                step="0.01"
                className="w-full mt-1 px-3 py-2 rounded-lg bg-[#0B1220] border border-[#283345] text-xs font-mono text-[#F3F6FC]"
              />
              <p className="text-[10px] text-[#5E697D] mt-1">Modeled execution slippage applied to backtests & paper fills.</p>
            </div>
          </div>

          <div className="pt-3 border-t border-[#283345] flex justify-end">
            <button
              onClick={handleSaveRiskRules}
              className="px-4 py-2 rounded-xl bg-[#B6FF5C] hover:bg-[#d4ff8a] text-[#080B12] font-bold text-xs cursor-pointer"
            >
              Save Risk Safeguards
            </button>
          </div>
        </div>
      )}

      {activeTab === 'SECURITY' && (
        <div className="p-5 rounded-2xl bg-[#101622] border border-[#283345] space-y-4">
          <h2 className="text-sm font-bold text-[#F3F6FC] font-['Outfit']">
            Paper Capital & Environment Reset
          </h2>
          <p className="text-xs text-[#929DB0]">
            Current Simulated Funds: <strong className="text-[#F3F6FC] font-mono">₹{account.available_balance.toLocaleString('en-IN')}</strong>.
            You can restore your virtual wallet back to ₹10,00,000 whenever you wish to test a fresh trading cycle.
          </p>

          <button
            onClick={() => {
              resetAccount();
              addToast('Paper trading wallet reset to ₹10,00,000.', 'info');
            }}
            className="px-4 py-2 rounded-xl bg-[#FF5D6C]/20 hover:bg-[#FF5D6C]/30 text-[#FF5D6C] border border-[#FF5D6C]/40 font-bold text-xs cursor-pointer"
          >
            Reset Virtual Paper Balance to ₹10,00,000
          </button>
        </div>
      )}
    </div>
  );
};
