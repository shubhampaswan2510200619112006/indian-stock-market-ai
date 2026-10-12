import React, { useState } from 'react';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { PaperPosition } from '../../types/trading';
import {
  TrendingUp, TrendingDown, Wallet, Plus, RotateCcw,
  Clock, ArrowUpRight, ArrowDownRight, Layers, XSquare, Activity,
} from 'lucide-react';

export interface PortfolioDeskProps {
  onNavigateToOptions?: () => void;
  compact?: boolean;
}

export const PortfolioDesk: React.FC<PortfolioDeskProps> = ({
  onNavigateToOptions,
  compact = false,
}) => {
  const {
    account,
    closePosition,
    squareOffAll,
    addFunds,
    resetAccount,
    openOrderModal,
  } = usePaperTrading();

  const [activeTab, setActiveTab] = useState<'positions' | 'orders'>('positions');
  const [closingId, setClosingId] = useState<string | null>(null);

  const isTotalUp = account.total_pnl >= 0;
  const isDayUp = account.day_pnl >= 0;

  const handleSquareOff = async (pos: PaperPosition) => {
    setClosingId(pos.position_id);
    await closePosition(pos.position_id);
    setClosingId(null);
  };

  const handleAddMore = (pos: PaperPosition) => {
    openOrderModal({
      symbol: pos.symbol,
      underlying: pos.underlying,
      strike: pos.strike,
      option_type: pos.option_type,
      expiry: pos.expiry,
      side: pos.side,
      product: pos.product,
      order_type: 'MARKET',
      quantity: pos.lot_size,
      lots: 1,
      lot_size: pos.lot_size,
      price: pos.current_ltp,
    });
  };

  return (
    <div className="w-full space-y-5">
      {/* 1. Executive Portfolio Valuation & Returns Card */}
      <div className="bg-[#0a0e18]/95 border border-white/[0.08] rounded-2xl p-6 shadow-2xl relative overflow-hidden backdrop-blur-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Left: Net Account Equity & Total Returns */}
          <div className="space-y-1.5">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-[#d4af37]" />
              <span>NET PORTFOLIO VALUATION</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </div>

            <div className="flex items-baseline gap-4">
              <span className="text-3xl sm:text-4xl font-extrabold font-['Outfit'] text-white tracking-tight">
                ₹{account.portfolio_value.toLocaleString('en-IN', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>

              <div
                className={`flex items-center gap-1 font-mono text-sm sm:text-base font-bold px-2.5 py-0.5 rounded-lg shadow-sm ${
                  isTotalUp
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-400/25'
                    : 'bg-rose-500/15 text-rose-400 border border-rose-400/25'
                }`}
              >
                {isTotalUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                <span>
                  {isTotalUp ? '+' : ''}₹{Math.abs(account.total_pnl).toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })} ({isTotalUp ? '+' : ''}{account.total_pnl_pct.toFixed(2)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Right: Institutional 4-Metric Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 font-mono text-xs border-t lg:border-t-0 lg:border-l border-white/[0.08] pt-4 lg:pt-0 lg:pl-6">
            <div className="bg-[#101626] p-2.5 rounded-xl border border-white/[0.06]">
              <span className="text-[9px] text-slate-400 block mb-0.5 font-bold uppercase">DAY'S RETURN</span>
              <span
                className={`text-sm font-bold ${
                  isDayUp ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isDayUp ? '+' : ''}₹{account.day_pnl.toFixed(2)}
              </span>
              <span className="text-[9px] text-slate-400 block">
                ({isDayUp ? '+' : ''}{account.day_pnl_pct.toFixed(2)}%)
              </span>
            </div>

            <div className="bg-[#101626] p-2.5 rounded-xl border border-white/[0.06]">
              <span className="text-[9px] text-slate-400 block mb-0.5 font-bold uppercase">DEPLOYED MARGIN</span>
              <span className="text-sm font-bold text-white">
                ₹{account.invested_margin.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </span>
              <span className="text-[9px] text-slate-400 block">Active Exposure</span>
            </div>

            <div className="bg-[#101626] p-2.5 rounded-xl border border-white/[0.06]">
              <span className="text-[9px] text-slate-400 block mb-0.5 font-bold uppercase">AVAILABLE CASH</span>
              <span className="text-sm font-bold text-emerald-400">
                ₹{account.available_balance.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </span>
              <span className="text-[9px] text-slate-400 block">Unencumbered</span>
            </div>
          </div>
        </div>

        {/* Capital Management Toolbar */}
        <div className="mt-5 pt-4 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-mono">
            <Wallet className="w-4 h-4 text-emerald-400" />
            <span>Virtual Reserves:</span>
            <strong className="text-white font-bold bg-white/[0.08] px-2 py-0.5 rounded">
              ₹{account.available_balance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </strong>
          </div>

          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <button
              onClick={() => addFunds(100000)}
              className="flex items-center gap-1 px-3 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 rounded-lg border border-white/[0.1] transition-all font-semibold cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span>+ Add ₹1L</span>
            </button>

            <button
              onClick={() => addFunds(500000)}
              className="flex items-center gap-1 px-3 py-1.5 bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 rounded-lg border border-white/[0.1] transition-all font-semibold cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span>+ Add ₹5L</span>
            </button>

            <button
              onClick={resetAccount}
              className="flex items-center gap-1 px-3 py-1.5 bg-white/[0.03] hover:bg-white/[0.08] text-slate-400 hover:text-white rounded-lg border border-white/[0.06] transition-all cursor-pointer"
              title="Reset balance to initial capital"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset (₹10L)</span>
            </button>

            {account.positions.length > 0 && (
              <button
                onClick={squareOffAll}
                className="flex items-center gap-1 px-3 py-1.5 bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 rounded-lg border border-rose-500/30 transition-all font-bold cursor-pointer"
              >
                <XSquare className="w-3.5 h-3.5" />
                <span>Square Off All</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. Portfolio Tabs (Open Positions | Order History) */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] pb-2 text-xs">
        <button
          onClick={() => setActiveTab('positions')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
            activeTab === 'positions'
              ? 'bg-[#121828] text-white border border-white/[0.12] shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-emerald-400" />
          <span>Open Positions ({account.positions.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('orders')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
            activeTab === 'orders'
              ? 'bg-[#121828] text-white border border-white/[0.12] shadow-sm'
              : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
          }`}
        >
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Execution Ledger ({account.orders.length})</span>
        </button>
      </div>

      {/* 3. Positions Content */}
      {activeTab === 'positions' && (
        <div className="space-y-3">
          {account.positions.length === 0 ? (
            /* Empty State */
            <div className="p-8 text-center bg-[#0a0e18]/80 border border-white/[0.06] rounded-2xl space-y-3 backdrop-blur-xl">
              <div className="w-12 h-12 mx-auto rounded-xl bg-white/[0.04] flex items-center justify-center text-slate-400 border border-white/[0.08]">
                <Layers className="w-6 h-6 text-slate-400" />
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-bold text-white font-['Outfit']">No Open Positions</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Execute derivatives orders from the Options Chain workspace to monitor your live mark-to-market positions.
                </p>
              </div>
              {onNavigateToOptions && (
                <button
                  onClick={onNavigateToOptions}
                  className="px-4 py-2 bg-[#d4af37]/20 hover:bg-[#d4af37]/30 text-[#f6d776] border border-[#d4af37]/40 font-bold rounded-lg text-xs transition-all cursor-pointer"
                >
                  Explore Options Chain →
                </button>
              )}
            </div>
          ) : (
            /* Positions Cards / Rows */
            account.positions.map((pos) => {
              const isPosUp = pos.pnl >= 0;
              const isClosing = closingId === pos.position_id;

              return (
                <div
                  key={pos.position_id}
                  className="bg-[#0a0e18]/90 border border-white/[0.08] hover:border-white/[0.16] rounded-xl p-4 transition-all shadow-md space-y-3 backdrop-blur-xl"
                >
                  {/* Top Row: Symbol, Tags, and Live P&L */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="text-sm font-bold text-white tracking-wide">
                          {pos.symbol}
                        </h4>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/[0.08] text-slate-300">
                          {pos.product}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            pos.side === 'BUY'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                              : 'bg-rose-500/15 text-rose-400 border border-rose-500/25'
                          }`}
                        >
                          {pos.side}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-400/15 text-amber-300 border border-amber-400/25">
                          {pos.option_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono">
                        {pos.quantity} Units ({pos.lots} Lots) • Avg Fill: ₹{pos.avg_price.toFixed(2)}
                      </div>
                    </div>

                    {/* Live Individual P&L */}
                    <div className="text-right font-mono">
                      <div
                        className={`text-base sm:text-lg font-bold ${
                          isPosUp ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {isPosUp ? '+' : ''}₹{pos.pnl.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div
                        className={`text-xs font-semibold ${
                          isPosUp ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        ({isPosUp ? '+' : ''}{pos.pnl_percentage.toFixed(2)}%)
                      </div>
                    </div>
                  </div>

                  {/* Bottom Row: LTP, Exposure, Actions */}
                  <div className="pt-2 border-t border-white/[0.04] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
                    <div className="flex items-center gap-4 text-slate-400">
                      <div>
                        LTP: <strong className="text-white font-bold bg-white/[0.08] px-1.5 py-0.2 rounded">₹{pos.current_ltp.toFixed(2)}</strong>
                      </div>
                      <div>
                        Exposure: <strong className="text-slate-300">₹{pos.invested_amount.toFixed(0)}</strong>
                      </div>
                      <div>
                        Mark: <strong className="text-slate-300">₹{pos.current_value.toFixed(0)}</strong>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleAddMore(pos)}
                        className="px-3 py-1 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 text-xs font-semibold border border-white/[0.08] transition-all cursor-pointer"
                      >
                        + Add Units
                      </button>

                      <button
                        type="button"
                        disabled={isClosing}
                        onClick={() => handleSquareOff(pos)}
                        className="px-3.5 py-1 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 text-xs font-bold border border-rose-500/30 transition-all flex items-center gap-1 disabled:opacity-40 cursor-pointer"
                      >
                        <span>{isClosing ? 'Closing...' : 'Square Off'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* 4. Ledger Content */}
      {activeTab === 'orders' && (
        <div className="bg-[#0a0e18]/90 border border-white/[0.08] rounded-xl overflow-hidden shadow-lg backdrop-blur-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-[#070a12] border-b border-white/[0.08] text-slate-300 text-[11px]">
                <tr>
                  <th className="py-2.5 px-4 font-bold">TIME</th>
                  <th className="py-2.5 px-4 font-bold">INSTRUMENT</th>
                  <th className="py-2.5 px-3 font-bold">SIDE</th>
                  <th className="py-2.5 px-3 font-bold">QTY</th>
                  <th className="py-2.5 px-4 font-bold">PRICE</th>
                  <th className="py-2.5 px-4 font-bold">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {account.orders.map((ord) => (
                  <tr key={ord.order_id} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 px-4 text-slate-400">{ord.timestamp_ist || new Date(ord.timestamp_ms).toLocaleTimeString('en-IN')}</td>
                    <td className="py-2 px-4 font-bold text-white">{ord.symbol}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ord.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                      }`}>
                        {ord.side}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-300">{ord.quantity}</td>
                    <td className="py-2 px-4 text-white font-bold">₹{ord.price.toFixed(2)}</td>
                    <td className="py-2 px-4">
                      <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-400/25 text-[10px] font-bold">
                        {ord.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

