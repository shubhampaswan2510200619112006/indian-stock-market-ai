import React, { useState } from 'react';
import { MarketQuote, Candle, MarketRegime } from '../types/market';
import { InstrumentHeader } from '../components/market/InstrumentHeader';
import { CandlestickChart } from '../components/market/CandlestickChart';
import { MarketRegimeCard } from '../components/market/MarketRegimeCard';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { StaggerContainer, FadeUp } from '../components/ui/PageTransition';
import { Activity } from 'lucide-react';

interface MarketsViewProps {
  niftyQuote: MarketQuote;
  bankniftyQuote: MarketQuote;
  candles: Candle[];
  regime: MarketRegime;
}

export const MarketsView: React.FC<MarketsViewProps> = ({
  niftyQuote, bankniftyQuote, candles, regime,
}) => {
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');
  const [timeframe, setTimeframe] = useState('1D');
  const activeQuote = selectedSymbol === 'NIFTY' ? niftyQuote : bankniftyQuote;

  return (
    <StaggerContainer>
      <FadeUp>
        <InstrumentHeader
          quote={activeQuote}
          activeSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
          dayChange={selectedSymbol === 'NIFTY' ? 184.2 : 295.4}
          dayChangePct={selectedSymbol === 'NIFTY' ? 0.75 : 0.58}
          regime={regime.regime}
        />
      </FadeUp>

      <FadeUp>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <CandlestickChart
              candles={candles}
              symbol={selectedSymbol}
              timeframe={timeframe}
              onTimeframeChange={setTimeframe}
              currentPrice={activeQuote.last_price}
            />
          </div>
          <div>
            <MarketRegimeCard regime={regime} />
          </div>
        </div>
      </FadeUp>

      {/* AI Insight for markets */}
      <FadeUp>
        <AIInsightCard
          regime={regime.regime}
          adx={regime.adx}
          iv={regime.historical_volatility}
        />
      </FadeUp>

      {/* Technical Indicators */}
      <FadeUp>
        <div className="panel" style={{ padding: '20px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-1)', paddingBottom: 14, marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Activity style={{ width: 15, height: 15, color: 'var(--cyan-accent)' }} />
              <h3 style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-primary)', textTransform: 'uppercase', margin: 0 }}>
                TECHNICAL MICROSTRUCTURE INDICATORS
              </h3>
            </div>
            <span style={{ fontSize: 10, fontFamily: 'JetBrains Mono, monospace', color: 'var(--text-muted)' }}>
              DETERMINISTIC FORMULAS
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'RSI (14)', value: '54.8', sub: 'Neutral Momentum', color: 'var(--text-primary)' },
              { label: 'BOLLINGER (20,2)', value: 'MID-BAND', sub: 'Bandwidth: 2.4%', color: 'var(--text-primary)' },
              { label: 'MACD (12,26,9)', value: '+14.2', sub: 'Mild Bullish Divergence', color: 'var(--emerald-accent)' },
              { label: 'VWAP POSITION', value: '+0.32% ABOVE', sub: 'Intraday Value Anchor', color: 'var(--gold-primary)' },
            ].map(item => (
              <div key={item.label} style={{
                background: 'var(--z2)',
                padding: '14px 16px',
                borderRadius: 10,
                border: '1px solid var(--border-0)',
              }}>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>{item.label}</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 18, fontWeight: 700, color: item.color, marginBottom: 4 }}>{item.value}</div>
                <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: 'var(--text-muted)' }}>{item.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </FadeUp>
    </StaggerContainer>
  );
};
