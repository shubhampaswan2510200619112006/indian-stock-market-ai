import React, { useState } from 'react';
import { OptionStrikeRow, IndexInstrument } from '../../types/trading';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { TrendingUp, TrendingDown, ChevronDown, Layers, Activity } from 'lucide-react';

interface GrowwOptionChainProps {
  instrument: IndexInstrument;
  instruments: Record<string, IndexInstrument>;
  selectedSymbol: string;
  onSelectSymbol: (sym: string) => void;
  selectedExpiry: string;
  onSelectExpiry: (exp: string) => void;
  rows: OptionStrikeRow[];
  compact?: boolean;
}

export const GrowwOptionChain: React.FC<GrowwOptionChainProps> = ({
  instrument,
  instruments,
  selectedSymbol,
  onSelectSymbol,
  selectedExpiry,
  onSelectExpiry,
  rows,
  compact = false,
}) => {
  const { openOrderModal } = usePaperTrading();
  const [filterSide, setFilterSide] = useState<'ALL' | 'CE' | 'PE'>('ALL');

  const spot = instrument.spot_price;
  const isUp = instrument.change >= 0;

  // Max OI for relative progress indicators
  let maxOi = 1;
  rows.forEach((r) => {
    if (r.ce.oi > maxOi) maxOi = r.ce.oi;
    if (r.pe.oi > maxOi) maxOi = r.pe.oi;
  });

  const handleOpenTrade = (
    strike: number,
    optionType: 'CE' | 'PE',
    price: number,
    side: 'BUY' | 'SELL'
  ) => {
    const symbolText = `${instrument.symbol} ${strike} ${optionType} ${selectedExpiry.split(' ')[0]} ${selectedExpiry.split(' ')[1]}`;
    openOrderModal({
      symbol: symbolText,
      underlying: instrument.symbol,
      strike,
      option_type: optionType,
      expiry: selectedExpiry,
      side,
      product: 'INTRADAY',
      order_type: 'MARKET',
      quantity: instrument.lot_size,
      lots: 1,
      lot_size: instrument.lot_size,
      price,
    });
  };

  return (
    <div className="w-full bg-[#080d19]/95 border border-[#d4af37]/25 rounded-2xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.6)] transition-all backdrop-blur-xl">
      {/* 1. Integrated Controls Bar */}
      <div className="px-4 py-2.5 bg-[#060a14] border-b border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
        {!compact ? (
          /* Full Page Instrument Pills */
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-0.5">
            {Object.keys(instruments).map((sym) => {
              const inst = instruments[sym];
              const isSelected = selectedSymbol === sym;
              const instUp = inst.change >= 0;

              return (
                <button
                  key={sym}
                  onClick={() => onSelectSymbol(sym)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-all whitespace-nowrap cursor-pointer ${
                    isSelected
                      ? 'bg-[#d4af37]/15 text-[#f6d776] font-bold border border-[#d4af37]/40 shadow-sm'
                      : 'bg-white/[0.03] text-slate-400 hover:text-white hover:bg-white/[0.06] border border-transparent'
                  }`}
                >
                  <span className="font-semibold">{inst.name}</span>
                  <span
                    className={`font-mono text-[11px] ${
                      instUp ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    ₹{inst.spot_price.toLocaleString('en-IN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#f6d776] font-['Outfit'] tracking-wider uppercase flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#d4af37]" />
              {instrument.name} • DERIVATIVES EXECUTION MATRIX
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#d4af37]/15 text-[#d4af37] border border-[#d4af37]/30 font-semibold">
              Lot: {instrument.lot_size} Units
            </span>
          </div>
        )}

        {/* Expiry Selector Dropdown */}
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-slate-400 text-xs font-medium">Expiry:</span>
          <div className="relative">
            <select
              value={selectedExpiry}
              onChange={(e) => onSelectExpiry(e.target.value)}
              className="appearance-none bg-[#101626] text-slate-200 font-mono text-xs px-3 py-1.5 pr-7 rounded-lg border border-white/[0.1] focus:outline-none focus:border-[#d4af37]/60 cursor-pointer shadow-sm"
            >
              {instrument.expiries.map((exp) => (
                <option key={exp} value={exp} className="bg-[#0c101c] text-white">
                  {exp}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* 2. Underlying Quote Header Banner */}
      <div className={`px-4 py-2 bg-gradient-to-r from-[#0d1322] via-[#101729] to-[#0d1322] border-b border-white/[0.06] flex flex-wrap items-center justify-between gap-3 ${compact ? 'text-xs' : ''}`}>
        {/* Left: Spot Price Readout */}
        <div className="flex items-baseline gap-3">
          <div>
            <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
              <span>{instrument.name} SPOT</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 font-mono">LIVE</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-xl sm:text-2xl font-extrabold font-['Outfit'] text-white tracking-tight">
                ₹{instrument.spot_price.toLocaleString('en-IN', {
                  minimumFractionDigits: 1,
                  maximumFractionDigits: 1,
                })}
              </span>

              <span
                className={`flex items-center gap-1 font-mono text-[11px] font-bold px-2 py-0.5 rounded ${
                  isUp
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                    : 'bg-rose-500/15 text-rose-400 border border-rose-500/25'
                }`}
              >
                {isUp ? '+' : ''}{instrument.change_pct.toFixed(2)}%
              </span>
            </div>
          </div>

          {!compact && (
            <div className="hidden lg:flex items-center gap-4 text-xs text-slate-400 pl-4 border-l border-white/[0.08] font-mono">
              <div>
                <span className="text-slate-500 block text-[9px] uppercase font-bold">DAY RANGE</span>
                <span className="text-slate-300 font-semibold">{instrument.low.toFixed(1)} – {instrument.high.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[9px] uppercase font-bold">LOT SIZE</span>
                <span className="font-bold text-white bg-white/[0.08] px-2 py-0.5 rounded">{instrument.lot_size} Units</span>
              </div>
            </div>
          )}
        </div>

        {/* Right: Key Options Analytics & Side Filter */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2 text-xs font-mono">
            <div className="bg-[#101626] px-2.5 py-1 rounded-lg border border-white/[0.08] text-center">
              <span className="text-[8px] text-slate-400 block uppercase font-bold">PCR</span>
              <span className={`font-bold ${instrument.pcr >= 1.0 ? 'text-emerald-400' : 'text-slate-200'}`}>
                {instrument.pcr.toFixed(2)}
              </span>
            </div>

            <div className="bg-[#101626] px-2.5 py-1 rounded-lg border border-[#d4af37]/30 text-center">
              <span className="text-[8px] text-[#f6d776] block uppercase font-bold">MAX PAIN</span>
              <span className="font-bold text-[#f6d776]">
                {instrument.max_pain}
              </span>
            </div>
          </div>

          {/* Segment Filter (All / CE / PE) */}
          <div className="flex items-center bg-[#070a12] p-0.5 rounded-lg border border-white/[0.08] text-xs font-medium">
            <button
              onClick={() => setFilterSide('ALL')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-all cursor-pointer ${
                filterSide === 'ALL'
                  ? 'bg-slate-800 text-white font-bold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterSide('CE')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-all cursor-pointer ${
                filterSide === 'CE'
                  ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30'
                  : 'text-slate-400 hover:text-emerald-300'
              }`}
            >
              Calls
            </button>
            <button
              onClick={() => setFilterSide('PE')}
              className={`px-2.5 py-0.5 rounded text-[11px] transition-all cursor-pointer ${
                filterSide === 'PE'
                  ? 'bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30'
                  : 'text-slate-400 hover:text-rose-300'
              }`}
            >
              Puts
            </button>
          </div>
        </div>
      </div>

      {/* 3. Main Options Chain Table */}
      <div className={`overflow-x-auto overflow-y-auto ${compact ? 'max-h-[460px]' : 'max-h-[620px]'}`}>
        <table className="w-full text-right font-mono text-xs border-collapse">
          {/* Table Header */}
          <thead className="sticky top-0 z-30 bg-[#070a12] border-b border-white/[0.08] shadow-md text-[11px] text-slate-300">
            <tr>
              {/* Calls Side */}
              {(filterSide === 'ALL' || filterSide === 'CE') && (
                <>
                  <th className="py-2.5 px-3 text-left font-semibold text-slate-400">CALL OI</th>
                  <th className="py-2.5 px-2 font-medium text-slate-400">CHG</th>
                  <th className="py-2.5 px-2 font-medium text-slate-400">VOL</th>
                  <th className="py-2.5 px-2 font-medium text-slate-400">IV%</th>
                  <th className="py-2.5 px-3 font-bold text-emerald-400 text-right">CALL LTP (₹)</th>
                </>
              )}

              {/* Center Strike Column */}
              <th className="py-2.5 px-4 text-center font-bold text-[#f6d776] bg-[#0c1220] border-x border-white/[0.08] sticky z-40">
                STRIKE
              </th>

              {/* Puts Side */}
              {(filterSide === 'ALL' || filterSide === 'PE') && (
                <>
                  <th className="py-2.5 px-3 font-bold text-rose-400 text-left">PUT LTP (₹)</th>
                  <th className="py-2.5 px-2 font-medium text-slate-400 text-right">IV%</th>
                  <th className="py-2.5 px-2 font-medium text-slate-400 text-right">VOL</th>
                  <th className="py-2.5 px-2 font-medium text-slate-400 text-right">CHG</th>
                  <th className="py-2.5 px-3 font-semibold text-slate-400 text-right">PUT OI</th>
                </>
              )}
            </tr>
          </thead>

          {/* Table Rows */}
          <tbody>
            {rows.map((row, idx) => {
              const prevRow = idx > 0 ? rows[idx - 1] : null;
              const isSpotDivider = prevRow && prevRow.strike < spot && row.strike >= spot;

              const ceIntensity = Math.min(1, row.ce.oi / maxOi);
              const peIntensity = Math.min(1, row.pe.oi / maxOi);

              return (
                <React.Fragment key={row.strike}>
                  {/* Subtle Spot Divider Line */}
                  {isSpotDivider && (
                    <tr className="bg-[#d4af37]/10 border-y border-[#d4af37]/40 font-semibold z-20">
                      <td
                        colSpan={filterSide === 'ALL' ? 11 : 6}
                        className="py-1 px-4 text-center text-[#f6d776] text-[11px] font-mono tracking-wider"
                      >
                        <div className="flex items-center justify-center gap-3">
                          <span className="h-[1px] flex-1 bg-[#d4af37]/25" />
                          <span className="flex items-center gap-2 px-3 py-0.5 rounded-full bg-[#080d18] border border-[#d4af37]/40">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#d4af37] animate-pulse" />
                            <span>Spot Reference: ₹{instrument.spot_price.toFixed(2)}</span>
                          </span>
                          <span className="h-[1px] flex-1 bg-[#d4af37]/25" />
                        </div>
                      </td>
                    </tr>
                  )}

                  <tr
                    className={`border-b border-white/[0.03] transition-colors group ${
                      row.is_atm
                        ? 'bg-[#d4af37]/15'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    {/* Call Side */}
                    {(filterSide === 'ALL' || filterSide === 'CE') && (
                      <>
                        {/* Call OI */}
                        <td className={`py-1.5 px-3 text-left relative ${row.is_ce_itm ? 'bg-amber-500/[0.03]' : ''}`}>
                          <div
                            className="absolute inset-y-1 left-0 bg-emerald-500/10 pointer-events-none rounded-r"
                            style={{ width: `${ceIntensity * 85}%` }}
                          />
                          <span className="relative z-10 text-slate-300 font-medium text-[11px]">
                            {(row.ce.oi / 100000).toFixed(2)}L
                          </span>
                        </td>

                        {/* Call OI Chg% */}
                        <td className={`py-1.5 px-2 text-[10px] ${row.is_ce_itm ? 'bg-amber-500/[0.03]' : ''} ${
                          row.ce.oi_chg_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {row.ce.oi_chg_pct >= 0 ? '+' : ''}{row.ce.oi_chg_pct}%
                        </td>

                        {/* Call Vol */}
                        <td className={`py-1.5 px-2 text-slate-400 text-[10px] ${row.is_ce_itm ? 'bg-amber-500/[0.03]' : ''}`}>
                          {(row.ce.volume / 1000).toFixed(0)}k
                        </td>

                        {/* Call IV */}
                        <td className={`py-1.5 px-2 text-slate-400 text-[10px] ${row.is_ce_itm ? 'bg-amber-500/[0.03]' : ''}`}>
                          {row.ce.iv}%
                        </td>

                        {/* CALL LTP with Quick Action Chips */}
                        <td className={`py-1.5 px-3 relative ${row.is_ce_itm ? 'bg-amber-500/[0.04]' : ''}`}>
                          <div className="flex items-center justify-end gap-1.5 group-hover:opacity-10 transition-opacity">
                            <span className="font-bold text-emerald-400 text-xs">
                              ₹{row.ce.ltp.toFixed(2)}
                            </span>
                            <span className={`text-[9px] ${row.ce.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {row.ce.change >= 0 ? '+' : ''}{row.ce.change.toFixed(1)}
                            </span>
                          </div>

                          {/* Quick Trade Action Chips */}
                          <div className="absolute inset-0 flex items-center justify-end pr-2 gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-[#080d18]/95 z-10">
                            <button
                              type="button"
                              onClick={() => handleOpenTrade(row.strike, 'CE', row.ce.ltp, 'BUY')}
                              className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500 hover:text-black text-emerald-300 font-bold rounded text-[10px] border border-emerald-500/40 shadow-sm transition-all active:scale-95 cursor-pointer tracking-wider"
                            >
                              BUY
                            </button>
                            <button
                              type="button"
                              onClick={() => handleOpenTrade(row.strike, 'CE', row.ce.ltp, 'SELL')}
                              className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500 hover:text-white text-rose-300 font-bold rounded text-[10px] border border-rose-500/40 shadow-sm transition-all active:scale-95 cursor-pointer tracking-wider"
                            >
                              SELL
                            </button>
                          </div>
                        </td>
                      </>
                    )}

                    {/* Strike Center Column */}
                    <td
                      className={`py-1.5 px-4 text-center font-bold font-mono border-x border-white/[0.08] ${
                        row.is_atm
                          ? 'bg-[#d4af37]/25 text-[#f6d776] border-[#d4af37]/50 shadow-inner'
                          : 'bg-[#080c16] text-white'
                      }`}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <span className="text-xs font-semibold">{row.strike}</span>
                        {row.is_atm && (
                          <span className="px-1 py-0.2 bg-[#d4af37] text-slate-950 rounded text-[8px] font-black">
                            ATM
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Put Side */}
                    {(filterSide === 'ALL' || filterSide === 'PE') && (
                      <>
                        {/* PUT LTP with Quick Action Chips */}
                        <td className={`py-1.5 px-3 text-left relative ${row.is_pe_itm ? 'bg-amber-500/[0.04]' : ''}`}>
                          <div className="flex items-center justify-start gap-1.5 group-hover:opacity-10 transition-opacity">
                            <span className="font-bold text-rose-400 text-xs">
                              ₹{row.pe.ltp.toFixed(2)}
                            </span>
                            <span className={`text-[9px] ${row.pe.change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              {row.pe.change >= 0 ? '+' : ''}{row.pe.change.toFixed(1)}
                            </span>
                          </div>

                          {/* Quick Trade Action Chips */}
                          <div className="absolute inset-0 flex items-center justify-start pl-2 gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-[#080d18]/95 z-10">
                            <button
                              type="button"
                              onClick={() => handleOpenTrade(row.strike, 'PE', row.pe.ltp, 'BUY')}
                              className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500 hover:text-black text-emerald-300 font-bold rounded text-[10px] border border-emerald-500/40 shadow-sm transition-all active:scale-95 cursor-pointer tracking-wider"
                            >
                              BUY
                            </button>
                            <button
                              type="button"
                              onClick={() => handleOpenTrade(row.strike, 'PE', row.pe.ltp, 'SELL')}
                              className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500 hover:text-white text-rose-300 font-bold rounded text-[10px] border border-rose-500/40 shadow-sm transition-all active:scale-95 cursor-pointer tracking-wider"
                            >
                              SELL
                            </button>
                          </div>
                        </td>

                        {/* Put IV */}
                        <td className={`py-1.5 px-2 text-slate-400 text-right text-[10px] ${row.is_pe_itm ? 'bg-amber-500/[0.03]' : ''}`}>
                          {row.pe.iv}%
                        </td>

                        {/* Put Vol */}
                        <td className={`py-1.5 px-2 text-slate-400 text-right text-[10px] ${row.is_pe_itm ? 'bg-amber-500/[0.03]' : ''}`}>
                          {(row.pe.volume / 1000).toFixed(0)}k
                        </td>

                        {/* Put OI Chg% */}
                        <td className={`py-1.5 px-2 text-[10px] text-right ${row.is_pe_itm ? 'bg-amber-500/[0.03]' : ''} ${
                          row.pe.oi_chg_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}>
                          {row.pe.oi_chg_pct >= 0 ? '+' : ''}{row.pe.oi_chg_pct}%
                        </td>

                        {/* Put OI */}
                        <td className={`py-1.5 px-3 text-right relative ${row.is_pe_itm ? 'bg-amber-500/[0.03]' : ''}`}>
                          <div
                            className="absolute inset-y-1 right-0 bg-rose-500/10 pointer-events-none rounded-l"
                            style={{ width: `${peIntensity * 85}%` }}
                          />
                          <span className="relative z-10 text-slate-300 font-medium text-[11px]">
                            {(row.pe.oi / 100000).toFixed(2)}L
                          </span>
                        </td>
                      </>
                    )}
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Institutional Footer */}
      <div className="px-5 py-2.5 bg-[#070a12] border-t border-white/[0.06] flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400">
        <span>Hover strike row to tap <strong>BUY</strong> or <strong>SELL</strong> simulated execution chips</span>
        <span className="text-slate-500">Lot size: {instrument.lot_size} • Tick size: ₹0.05 • Real-time NSE Greeks</span>
      </div>
    </div>
  );
};
