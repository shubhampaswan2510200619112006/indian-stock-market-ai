import React, { useState } from 'react';
import { OptionChainSnapshot } from '../types/market';
import { PCRMaxPainCard } from '../components/options/PCRMaxPainCard';
import { OptionChainTable } from '../components/options/OptionChainTable';
import { GreeksMatrix } from '../components/options/GreeksMatrix';

interface OptionsCommandViewProps {
  chain: OptionChainSnapshot;
  expiries: string[];
}

export const OptionsCommandView: React.FC<OptionsCommandViewProps> = ({ chain, expiries }) => {
  const [activeExpiry, setActiveExpiry] = useState<string>(
    expiries.length > 0 ? expiries[0] : 'NEAR_MONTH'
  );

  return (
    <div className="space-y-6">
      {/* 1. Options Summary & PCR Banner */}
      <PCRMaxPainCard
        chain={chain}
        expiries={expiries}
        activeExpiry={activeExpiry}
        onSelectExpiry={setActiveExpiry}
      />

      {/* 2. Institutional Dense Option Chain Table */}
      <OptionChainTable chain={chain} atmStrike={chain.atm_strike || 24650} />

      {/* 3. Black-76 Greeks Matrix */}
      <GreeksMatrix />
    </div>
  );
};
