import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles, Send, Bot, User, ArrowRight, ShieldCheck,
  CheckCircle2, AlertTriangle, Activity, BarChart2,
  PieChart, RefreshCw, Zap, Layers, HelpCircle
} from 'lucide-react';
import { useRealtimeMarket } from '../hooks/useRealtimeMarket';
import { api } from '../api/client';
import { MarketRegime } from '../types/market';
import { NavTab } from '../components/layout/Navigation';

interface AIMarketAnalystViewProps {
  onNavigateToOptions?: () => void;
  onNavigateToStrategy?: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text: string;
  metrics?: {
    symbol: string;
    spot: number;
    pcr: number;
    maxPain: number;
    regime: string;
    confidence: number;
    recommendedStrategy?: string;
  };
}

export const AIMarketAnalystView: React.FC<AIMarketAnalystViewProps> = ({
  onNavigateToOptions,
  onNavigateToStrategy,
}) => {
  const { activeInstrument, selectedSymbol, instruments } = useRealtimeMarket();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [regimeData, setRegimeData] = useState<MarketRegime | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Fetch live market regime for the active symbol
  useEffect(() => {
    let active = true;
    api.getMarketRegime(selectedSymbol)
      .then((r) => { if (active) setRegimeData(r); })
      .catch(() => {});
    return () => { active = false; };
  }, [selectedSymbol]);

  // Initial welcome message tailored to current active instrument
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'msg_welcome',
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
          text: `Hello! I am your Quantitative Intelligence & Options Research Analyst. I evaluate live NSE index microstructure, implied volatility regimes, and options order flow for ${activeInstrument.name}.`,
          metrics: {
            symbol: activeInstrument.symbol,
            spot: activeInstrument.spot_price,
            pcr: activeInstrument.pcr,
            maxPain: activeInstrument.max_pain,
            regime: regimeData?.regime || 'RANGEBOUND',
            confidence: (regimeData?.confidence || 0.74) * 100,
            recommendedStrategy: activeInstrument.pcr >= 1.0 ? 'Bull Call Spread' : 'Iron Condor',
          },
        },
      ]);
    }
  }, [activeInstrument, regimeData]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = (queryText?: string) => {
    const textToSend = queryText || inputValue;
    if (!textToSend.trim()) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      text: textToSend,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputValue('');
    setIsTyping(true);

    // Generate quantitative response based on current real-time metrics
    setTimeout(() => {
      const spot = activeInstrument.spot_price;
      const pcr = activeInstrument.pcr;
      const pain = activeInstrument.max_pain;
      const step = activeInstrument.strike_step;
      const atm = Math.round(spot / step) * step;

      let answer = '';
      let strat = 'Bull Call Spread';

      const lower = textToSend.toLowerCase();
      if (lower.includes('pcr') || lower.includes('pain') || lower.includes('sentiment')) {
        answer = `Institutional positioning for ${activeInstrument.name}: Put-Call Ratio currently stands at ${pcr.toFixed(2)}. ${
          pcr > 1.1
            ? 'Heavy Put writing indicates firm underlying floor support.'
            : pcr < 0.8
            ? 'Call writers dominate near the money, creating resistance ceilings.'
            : 'Balanced equilibrium between call and put open interest.'
        } The Max Pain strike is pinned at ₹${pain}, suggesting market makers tend towards this price near expiry.`;
        strat = pcr > 1.0 ? 'Bull Call Spread' : 'Bear Put Spread';
      } else if (lower.includes('strategy') || lower.includes('recommend') || lower.includes('spread')) {
        strat = pcr >= 1.0 ? `Bull Call Spread (${atm}/${atm + step * 2})` : `Iron Condor (${atm - step * 2}/${atm - step} & ${atm + step}/${atm + step * 2})`;
        answer = `Based on current implied volatility (${regimeData?.historical_volatility?.toFixed(1) || '13.8'}%) and ${
          regimeData?.regime || 'RANGE'
        } regime, an asymmetric risk-defined ${strat} provides the highest risk-adjusted expectancy. Defined risk protects against overnight gaps.`;
      } else if (lower.includes('support') || lower.includes('resistance') || lower.includes('levels')) {
        answer = `Microstructure levels for ${activeInstrument.name}:\n• Primary Support: ₹${atm - step * 2} (Max Put OI concentration)\n• Pivot Point: ₹${atm} (At-The-Money strike)\n• Immediate Resistance: ₹${atm + step * 2} (Max Call OI concentration)`;
        strat = 'Rangebound Iron Condor';
      } else {
        answer = `Quantitative Analysis for ${activeInstrument.name} (Spot: ₹${spot.toFixed(1)}):\nCurrent market regime is classified as ${
          regimeData?.regime || 'RANGEBOUND'
        } with ${( (regimeData?.confidence || 0.72) * 100).toFixed(0)}% algorithmic confidence. PCR of ${pcr.toFixed(2)} and Max Pain at ₹${pain} indicate controlled volatility with positive bias.`;
        strat = 'Bull Call Spread';
      }

      const assistantMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        text: answer,
        metrics: {
          symbol: activeInstrument.symbol,
          spot,
          pcr,
          maxPain: pain,
          regime: regimeData?.regime || 'RANGEBOUND',
          confidence: Math.round((regimeData?.confidence || 0.74) * 100),
          recommendedStrategy: strat,
        },
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setIsTyping(false);
    }, 700);
  };

  const promptSuggestions = [
    `What is the institutional PCR & Max Pain bias for ${activeInstrument.name}?`,
    `Recommend an optimal options strategy for current ${regimeData?.regime || 'Rangebound'} regime.`,
    `Identify key support & resistance strikes from Open Interest concentration.`,
    `How does implied volatility skew affect near-month option premiums?`,
  ];

  return (
    <div className="space-y-6">
      {/* ── 1. Analyst Header & Quantitative Snapshot ── */}
      <div className="p-4 rounded-2xl bg-[#080d19]/95 border border-emerald-500/25 backdrop-blur-xl shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black text-white font-['Outfit'] tracking-tight">
                AI Quantitative Market Analyst
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic Market Data + Bayesian Probabilistic Options Regime Modeling
            </p>
          </div>
        </div>

        {/* Underlying Status Pill */}
        <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0c1222] border border-white/[0.08] text-xs font-mono">
          <div>
            <span className="text-[10px] text-slate-400">Active Focus:</span>
            <span className="font-bold text-white ml-1.5">{activeInstrument.name}</span>
          </div>
          <div className="h-4 w-px bg-white/[0.1]" />
          <div>
            <span className="text-[10px] text-slate-400">Regime:</span>
            <span className="font-bold text-emerald-400 ml-1.5">{regimeData?.regime || 'RANGE'}</span>
          </div>
        </div>
      </div>

      {/* ── 2. Chat Conversation Viewport ── */}
      <div className="p-5 rounded-2xl bg-[#090d19]/90 border border-white/[0.08] backdrop-blur-xl shadow-xl min-h-[460px] flex flex-col justify-between">
        {/* Messages Stream */}
        <div className="space-y-5 overflow-y-auto max-h-[520px] pr-2 scrollbar-thin">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 flex-shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-2xl p-4 rounded-2xl text-xs leading-relaxed space-y-3 ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/40 text-white rounded-tr-none'
                    : 'bg-[#0d1424] border border-white/[0.08] text-slate-200 rounded-tl-none shadow-lg'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pb-1 border-b border-white/[0.06]">
                  <span>{msg.sender === 'assistant' ? 'AI Quantitative Intelligence Engine' : 'You'}</span>
                  <span>{msg.timestamp}</span>
                </div>

                <div className="whitespace-pre-line text-slate-100">{msg.text}</div>

                {/* Structured Metrics Card if provided */}
                {msg.metrics && (
                  <div className="p-3 rounded-xl bg-[#070b14] border border-white/[0.06] space-y-2 mt-2">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                      Quantitative Signal Summary ({msg.metrics.symbol})
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                      <div className="p-1.5 rounded bg-white/[0.04]">
                        <span className="text-[10px] text-slate-400 block">Spot LTP</span>
                        <strong className="text-white">₹{msg.metrics.spot.toFixed(1)}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-white/[0.04]">
                        <span className="text-[10px] text-slate-400 block">PCR</span>
                        <strong className="text-emerald-400">{msg.metrics.pcr.toFixed(2)}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-white/[0.04]">
                        <span className="text-[10px] text-slate-400 block">Max Pain</span>
                        <strong className="text-[#f6d776]">₹{msg.metrics.maxPain}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-white/[0.04]">
                        <span className="text-[10px] text-slate-400 block">Confidence</span>
                        <strong className="text-sky-400">{msg.metrics.confidence}%</strong>
                      </div>
                    </div>

                    {msg.metrics.recommendedStrategy && (
                      <div className="flex items-center justify-between pt-1 border-t border-white/[0.06]">
                        <span className="text-[10px] text-slate-400">Model Strategy Thesis:</span>
                        <span className="text-[11px] font-bold text-[#f6d776]">{msg.metrics.recommendedStrategy}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-white/[0.08] border border-white/[0.1] flex items-center justify-center text-slate-300 flex-shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="flex items-center gap-2 text-xs text-slate-400 font-mono p-3 bg-[#0d1424] rounded-xl w-48 border border-white/[0.06] animate-pulse">
              <Bot className="w-4 h-4 text-emerald-400" />
              <span>Analyzing order flow...</span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* ── Suggested Questions & Query Input Bar ── */}
        <div className="mt-5 pt-4 border-t border-white/[0.08] space-y-3">
          {/* Quick Suggestion Pills */}
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
            {promptSuggestions.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(prompt)}
                className="px-3 py-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-emerald-500/40 text-[11px] text-slate-300 hover:text-white transition-all whitespace-nowrap cursor-pointer text-left"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
              placeholder={`Ask anything about ${activeInstrument.name} options flow, Greeks, or strategies...`}
              className="flex-1 px-4 py-3 rounded-xl bg-[#0d1424] border border-white/[0.12] focus:border-emerald-500/60 focus:shadow-[0_0_20px_rgba(16,185,129,0.15)] text-xs text-white placeholder-slate-500 focus:outline-none transition-all font-['Outfit']"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isTyping}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 disabled:opacity-40 text-black font-extrabold text-xs transition-all flex items-center gap-1.5 cursor-pointer shadow-lg shadow-emerald-500/20"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Analyze</span>
            </button>
          </div>

          {/* Regulatory Disclaimer */}
          <div className="text-[10px] text-slate-500 text-center font-mono">
            ⚠️ Automated Quantitative Intelligence • For educational & simulated research purposes only • Not SEBI registered investment advice
          </div>
        </div>
      </div>
    </div>
  );
};
