import React, { useState } from 'react';
import { Box, Compass, FileCheck, Server } from 'lucide-react';
import { VolatilityStudioView } from './VolatilityStudioView';
import { MarketsView } from './MarketsView';
import { ResearchGovernanceView } from './ResearchGovernanceView';
import { DataHealthView } from './DataHealthView';
import { MarketQuote, Candle, MarketRegime, ProviderHealth } from '../types/market';

interface OthersToolsViewProps {
  niftyQuote: MarketQuote;
  bankniftyQuote: MarketQuote;
  candles: Candle[];
  regime: MarketRegime;
  providers: ProviderHealth[];
  isLowPerf: boolean;
}

export const OthersToolsView: React.FC<OthersToolsViewProps> = ({
  niftyQuote,
  bankniftyQuote,
  candles,
  regime,
  providers,
  isLowPerf,
}) => {
  const [activeSubTool, setActiveSubTool] = useState<'volatility' | 'regime' | 'research' | 'health'>('volatility');

  return (
    <div className="space-y-5">
      {/* Sub-tool selector pills */}
      <div className="flex flex-wrap items-center gap-2 bg-[#090e1a]/90 p-1.5 rounded-2xl border border-white/[0.08] text-xs">
        <button
          type="button"
          onClick={() => setActiveSubTool('volatility')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold transition-all cursor-pointer ${
            activeSubTool === 'volatility'
              ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Box className="w-3.5 h-3.5" />
          <span>3D Volatility Studio</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTool('regime')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold transition-all cursor-pointer ${
            activeSubTool === 'regime'
              ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Market Regime Scanner</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTool('research')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold transition-all cursor-pointer ${
            activeSubTool === 'research'
              ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <FileCheck className="w-3.5 h-3.5" />
          <span>Research & Governance</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTool('health')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold transition-all cursor-pointer ${
            activeSubTool === 'health'
              ? 'bg-[#d4af37]/20 text-[#f6d776] border border-[#d4af37]/40 shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Server className="w-3.5 h-3.5" />
          <span>Data Telemetry Health</span>
        </button>
      </div>

      {/* Render selected sub-tool */}
      <div>
        {activeSubTool === 'volatility' && <VolatilityStudioView isLowPerf={isLowPerf} />}
        {activeSubTool === 'regime' && (
          <MarketsView
            niftyQuote={niftyQuote}
            bankniftyQuote={bankniftyQuote}
            candles={candles}
            regime={regime}
          />
        )}
        {activeSubTool === 'research' && <ResearchGovernanceView />}
        {activeSubTool === 'health' && <DataHealthView providers={providers} />}
      </div>
    </div>
  );
};
