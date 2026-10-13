import React, { useState, useMemo } from 'react';
import {
  Newspaper, TrendingUp, TrendingDown, MinusCircle, Search,
  Filter, Sparkles, Zap, Heart, Clock, ExternalLink, ShieldCheck, Tag
} from 'lucide-react';

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timeAgo: string;
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  sentimentScore: number; // -1.0 to +1.0
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
  category: 'BANKING' | 'IT' | 'MACRO' | 'AUTO' | 'ENERGY' | 'INDICES';
  entities: string[];
  topicTag: string;
}

const INITIAL_NEWS: NewsItem[] = [
  {
    id: 'news-1',
    title: 'RBI Monetary Policy Update: Inflation Under Comfort Band, Liquidity Injections Propel NIFTY Over 24,650',
    summary: 'The Reserve Bank of India maintained an accommodative stance on core liquidity, noting resilient domestic consumption and sustained capex cycle in banking and infrastructure.',
    source: 'Economic Times',
    timeAgo: '4 mins ago',
    sentiment: 'BULLISH',
    sentimentScore: 0.88,
    impact: 'HIGH',
    category: 'MACRO',
    entities: ['NIFTY 50', 'BANK NIFTY', 'RBI'],
    topicTag: 'Macro Liquidity',
  },
  {
    id: 'news-2',
    title: 'HDFC Bank & ICICI Bank Post Record Deposit Growth & Asset Quality Surge in Q2 Pre-Earnings',
    summary: 'Private banking majors witnessed a 16.4% year-on-year surge in high-yielding advances with net non-performing assets descending to historic lows.',
    source: 'Moneycontrol',
    timeAgo: '12 mins ago',
    sentiment: 'BULLISH',
    sentimentScore: 0.82,
    impact: 'HIGH',
    category: 'BANKING',
    entities: ['HDFCBANK', 'ICICIBANK', 'BANK NIFTY'],
    topicTag: 'Banking Advances',
  },
  {
    id: 'news-3',
    title: 'Crude Oil Prices Ease Below $74/bbl; Favorable For Indian Refiners & Rupee Stability',
    summary: 'Brent crude recorded back-to-back weekly pullbacks as global supply prospects loosened, alleviating import bill pressure for Indian state refiners.',
    source: 'Bloomberg Quint',
    timeAgo: '26 mins ago',
    sentiment: 'BULLISH',
    sentimentScore: 0.65,
    impact: 'MEDIUM',
    category: 'ENERGY',
    entities: ['RELIANCE', 'BPCL', 'USDINR'],
    topicTag: 'Energy Dynamics',
  },
  {
    id: 'news-4',
    title: 'TCS & Infosys Land Multi-Billion Dollar Generative AI Transformation Contracts in North America',
    summary: 'Indian IT bellwethers announced major digital infrastructure partnerships, signaling an inflection in discretionary technology enterprise spending.',
    source: 'Livemint',
    timeAgo: '45 mins ago',
    sentiment: 'BULLISH',
    sentimentScore: 0.74,
    impact: 'HIGH',
    category: 'IT',
    entities: ['TCS', 'INFY', 'NIFTY IT'],
    topicTag: 'Enterprise Tech',
  },
  {
    id: 'news-5',
    title: 'FIIs Net Infuse ₹2,840 Crore in Single Session Derivatives & Cash Markets',
    summary: 'Foreign Institutional Investors turned aggressive net buyers in index futures and call options, lowering net short exposure across NSE benchmarks.',
    source: 'NSE Circulars',
    timeAgo: '1 hour ago',
    sentiment: 'BULLISH',
    sentimentScore: 0.91,
    impact: 'HIGH',
    category: 'INDICES',
    entities: ['NIFTY', 'FII FLOWS'],
    topicTag: 'Institutional Flow',
  },
  {
    id: 'news-6',
    title: 'Automobile Retail Sales Clock 14% Festivity Boost Driven by Premium SUV Shipments',
    summary: 'FADA data indicated heavy festive deliveries for Mahindra and Tata Motors, with customer waitlists expanding across electric and hybrid portfolios.',
    source: 'CNBC-TV18',
    timeAgo: '2 hours ago',
    sentiment: 'BULLISH',
    sentimentScore: 0.68,
    impact: 'MEDIUM',
    category: 'AUTO',
    entities: ['TATAMOTORS', 'M&M', 'NIFTY AUTO'],
    topicTag: 'Auto Retail',
  },
  {
    id: 'news-7',
    title: 'Global Chip Supply Constraints Cause Short-Term Delays in Select Electronics Exports',
    summary: 'Freight bottlenecks in key regional shipping corridors created transitory delivery deferrals for niche hardware manufacturing units.',
    source: 'Financial Express',
    timeAgo: '3 hours ago',
    sentiment: 'BEARISH',
    sentimentScore: -0.42,
    impact: 'LOW',
    category: 'IT',
    entities: ['NIFTY IT', 'TECHM'],
    topicTag: 'Supply Dynamics',
  },
  {
    id: 'news-8',
    title: 'SEBI Enhances Framework For Index Derivatives To Foster Genuine Risk Hedging',
    summary: 'Regulator rolled out calibrated margin frameworks and single weekly expiry guidelines designed to protect retail participants while sustaining institutional liquidity.',
    source: 'SEBI Gazette',
    timeAgo: '4 hours ago',
    sentiment: 'NEUTRAL',
    sentimentScore: 0.05,
    impact: 'HIGH',
    category: 'INDICES',
    entities: ['SEBI', 'NIFTY OPTIONS'],
    topicTag: 'Regulatory Standard',
  },
];

export const NewsView: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredNews = useMemo(() => {
    return INITIAL_NEWS.filter((item) => {
      const matchCat = selectedCategory === 'ALL' || item.category === selectedCategory;
      const matchSent = selectedSentiment === 'ALL' || item.sentiment === selectedSentiment;
      const matchSearch =
        searchQuery === '' ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.entities.some((e) => e.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchCat && matchSent && matchSearch;
    });
  }, [selectedCategory, selectedSentiment, searchQuery]);

  return (
    <div className="space-y-6">
      {/* 1. Header Hero with Executive Institutional Styling */}
      <div className="p-6 rounded-2xl bg-[#0a0e18]/95 border border-white/[0.08] shadow-2xl relative overflow-hidden backdrop-blur-xl">
        <div className="relative z-10 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-white/[0.05] border border-white/[0.1] flex items-center justify-center text-2xl shadow-sm">
              📰
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#43D9FF]/20 text-[#43D9FF] border border-[#43D9FF]/40">
                  REAL-TIME NEWS RADAR
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  LIVE STREAM ACTIVE
                </span>
              </div>
              <h1 className="text-xl font-bold text-white tracking-wide mt-1 font-['Outfit']">
                Indian Market Intelligence & Financial Feeds
              </h1>
              <p className="text-xs text-slate-400 max-w-xl">
                Curated streaming financial wire from NSE, BSE, RBI, Economic Times, and Bloomberg Quint with automated AI sentiment analysis and impact classification.
              </p>
            </div>
          </div>

          {/* Quick Stats Pill */}
          <div className="flex items-center gap-3 bg-slate-950/70 p-3 rounded-2xl border border-white/[0.08] text-xs">
            <div className="text-center px-2">
              <div className="text-[10px] text-slate-400 font-mono">BULLISH BIAS</div>
              <div className="text-emerald-400 font-bold font-mono text-sm">87.5%</div>
            </div>
            <div className="w-px h-8 bg-white/[0.08]" />
            <div className="text-center px-2">
              <div className="text-[10px] text-slate-400 font-mono">IMPACT PULSE</div>
              <div className="text-pink-300 font-bold font-mono text-sm">HIGH ⚡</div>
            </div>
            <div className="w-px h-8 bg-white/[0.08]" />
            <div className="text-center px-2">
              <div className="text-[10px] text-slate-400 font-mono">LATENCY</div>
              <div className="text-cyan-400 font-bold font-mono text-sm">1.2s</div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Filters & Search Bar */}
      <div className="p-4 rounded-2xl bg-[#0a0f1d]/90 border border-white/[0.08] backdrop-blur-md shadow-lg flex flex-wrap items-center justify-between gap-4">
        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {[
            { id: 'ALL', label: '🌟 All Feeds' },
            { id: 'BANKING', label: '🏦 Banking' },
            { id: 'IT', label: '💻 IT & Tech' },
            { id: 'MACRO', label: '📈 Macro & RBI' },
            { id: 'AUTO', label: '🚗 Auto' },
            { id: 'ENERGY', label: '⚡ Energy' },
            { id: 'INDICES', label: '🎯 Nifty & FII' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl font-medium transition-all ${
                selectedCategory === cat.id
                  ? 'bg-gradient-to-r from-pink-500/25 to-purple-500/25 text-pink-300 border border-pink-400/40 shadow-sm font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Right Search & Sentiment */}
        <div className="flex items-center gap-3">
          {/* Sentiment Filter */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-white/[0.08] text-xs">
            {[
              { id: 'ALL', label: 'All' },
              { id: 'BULLISH', label: '🟢 Bull' },
              { id: 'BEARISH', label: '🔴 Bear' },
            ].map((s) => (
              <button
                key={s.id}
                onClick={() => setSelectedSentiment(s.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                  selectedSentiment === s.id
                    ? 'bg-white/[0.12] text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search news, stocks..."
              className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-950 border border-white/[0.1] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pink-500 w-44 sm:w-56"
            />
          </div>
        </div>
      </div>

      {/* 3. News Feed Cards Stream */}
      <div className="space-y-4">
        {filteredNews.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-dashed border-white/[0.08]">
            <p className="text-sm text-slate-400">No news articles match your current filter.</p>
            <button
              onClick={() => { setSelectedCategory('ALL'); setSelectedSentiment('ALL'); setSearchQuery(''); }}
              className="mt-3 px-4 py-2 rounded-xl bg-pink-500/20 text-pink-300 border border-pink-500/40 text-xs font-bold"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          filteredNews.map((news) => {
            const isBull = news.sentiment === 'BULLISH';
            const isBear = news.sentiment === 'BEARISH';
            const sentimentBg = isBull
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : isBear
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-slate-800 text-slate-300 border-white/[0.1]';

            return (
              <div
                key={news.id}
                className="group p-4 rounded-xl bg-[#0a0e18]/95 hover:bg-[#0f1526] border border-white/[0.08] hover:border-[#43D9FF]/40 transition-all duration-200 shadow-md relative overflow-hidden backdrop-blur-xl"
              >
                {/* Executive Top Ribbon */}
                <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded font-bold bg-white/[0.06] text-[#43D9FF] border border-white/[0.1]">
                      {news.topicTag}
                    </span>
                    <span className="text-xs font-mono font-semibold text-slate-400">
                      {news.source}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {news.timeAgo}
                    </span>
                  </div>

                  {/* Impact & Sentiment Badges */}
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${sentimentBg}`}
                    >
                      {isBull ? '▲ BULLISH' : isBear ? '▼ BEARISH' : '● NEUTRAL'} ({(news.sentimentScore * 100).toFixed(0)}%)
                    </span>

                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                        news.impact === 'HIGH'
                          ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {news.impact} IMPACT
                    </span>
                  </div>
                </div>

                {/* Article Headline */}
                <h3 className="text-base font-bold text-white group-hover:text-pink-200 transition-colors leading-snug">
                  {news.title}
                </h3>

                {/* Article Summary */}
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  {news.summary}
                </p>

                {/* Bottom Entity Chips */}
                <div className="flex flex-wrap items-center justify-between gap-3 mt-4 pt-3 border-t border-white/[0.04]">
                  <div className="flex items-center gap-1.5">
                    <Tag className="w-3 h-3 text-slate-500" />
                    <span className="text-[11px] text-slate-500 font-mono">TAGGED:</span>
                    {news.entities.map((ent) => (
                      <span
                        key={ent}
                        className="px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold bg-slate-900 border border-white/[0.08] text-slate-300"
                      >
                        {ent}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-2 text-xs text-pink-400 group-hover:translate-x-1 transition-transform cursor-pointer">
                    <span className="font-semibold text-[11px]">View Market Impact Analysis</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
