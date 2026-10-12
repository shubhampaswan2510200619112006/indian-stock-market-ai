import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { OrderSide, ProductType, OrderType } from '../../types/trading';
import { X, CheckCircle2, AlertCircle, ChevronRight, ArrowRight } from 'lucide-react';
import { sound } from '../../utils/audio';

export const OrderPadModal: React.FC = () => {
  const { isOrderModalOpen, orderModalData, closeOrderModal, placeOrder, account } = usePaperTrading();

  if (!isOrderModalOpen || !orderModalData) return null;

  const [side, setSide] = useState<OrderSide>(orderModalData.side || 'BUY');
  const [product, setProduct] = useState<ProductType>('INTRADAY');
  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [lots, setLots] = useState<number>(orderModalData.lots || 1);
  const [limitPrice, setLimitPrice] = useState<number>(orderModalData.price || 100);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [stopLoss, setStopLoss] = useState<string>('');
  const [target, setTarget] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const lotSize = orderModalData.lot_size || 25;
  const quantity = lots * lotSize;
  const activePrice = orderType === 'LIMIT' ? limitPrice : orderModalData.price;

  // Margin calculation
  const marginRequired = side === 'BUY'
    ? activePrice * quantity
    : activePrice * quantity * 1.5;

  const hasSufficientMargin = account.available_balance >= marginRequired;

  const isBuy = side === 'BUY';
  const themeColor = isBuy ? '#10B981' : '#F43F5E';

  const handleLotsChange = (delta: number) => {
    sound.playClick();
    setLots((prev) => Math.max(1, prev + delta));
  };

  const handleSetExactLots = (numLots: number) => {
    sound.playClick();
    setLots(numLots);
  };

  const handlePriceChange = (delta: number) => {
    sound.playClick();
    setLimitPrice((prev) => parseFloat(Math.max(0.05, prev + delta).toFixed(2)));
  };

  const handleSubmit = async () => {
    if (!hasSufficientMargin) {
      setErrorMessage(`Insufficient capital: Required ₹${marginRequired.toFixed(2)}, Available ₹${account.available_balance.toFixed(2)}`);
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    setTimeout(async () => {
      const res = await placeOrder({
        symbol: orderModalData.symbol,
        underlying: orderModalData.underlying,
        strike: orderModalData.strike,
        option_type: orderModalData.option_type,
        expiry: orderModalData.expiry,
        side,
        product,
        order_type: orderType,
        quantity,
        lots,
        lot_size: lotSize,
        price: activePrice,
        limit_price: orderType === 'LIMIT' ? limitPrice : undefined,
      });

      setIsSubmitting(false);

      if (res.success) {
        setSuccessMessage(`Order filled: ${side} ${quantity} units @ ₹${activePrice.toFixed(2)}`);
        setTimeout(() => {
          setSuccessMessage(null);
          closeOrderModal();
        }, 1100);
      } else {
        setErrorMessage(res.message || 'Execution error');
      }
    }, 35);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0"
          onClick={closeOrderModal}
        />

        {/* Modal Ticket */}
        <motion.div
          initial={{ scale: 0.96, opacity: 0, y: 12 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.96, opacity: 0, y: 12 }}
          transition={{ duration: 0.16, ease: 'easeOut' }}
          className="relative w-full max-w-[460px] max-h-[90vh] overflow-y-auto bg-[#0d121f] border border-white/[0.1] rounded-2xl shadow-2xl z-10"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Top subtle accent bar */}
          <div
            className="h-1 w-full transition-colors duration-200"
            style={{ backgroundColor: themeColor }}
          />

          {/* Header */}
          <div className="px-5 py-4 border-b border-white/[0.06] flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  {orderModalData.symbol}
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-300">
                  {orderModalData.option_type}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                <span>Expiry: {orderModalData.expiry}</span>
                <span>•</span>
                <span>
                  LTP: <strong className="text-white font-bold">₹{orderModalData.price.toFixed(2)}</strong>
                </span>
              </div>
            </div>

            <button
              onClick={closeOrderModal}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Form Content */}
          <div className="p-5 space-y-4 text-xs font-sans">
            {/* 1. Side Segmented Control: BUY vs SELL */}
            <div className="grid grid-cols-2 p-1 bg-[#090d16] rounded-xl border border-white/[0.06]">
              <button
                type="button"
                onClick={() => { sound.playClick(); setSide('BUY'); }}
                className={`py-2 rounded-lg text-xs font-semibold transition-all ${
                  isBuy
                    ? 'bg-emerald-500 text-slate-950 font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                BUY
              </button>
              <button
                type="button"
                onClick={() => { sound.playClick(); setSide('SELL'); }}
                className={`py-2 rounded-lg text-xs font-semibold transition-all ${
                  !isBuy
                    ? 'bg-rose-500 text-white font-bold shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                SELL
              </button>
            </div>

            {/* 2. Product & Order Type Rows */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Product</label>
                <div className="flex bg-[#090d16] p-0.5 rounded-lg border border-white/[0.06]">
                  <button
                    type="button"
                    onClick={() => { sound.playClick(); setProduct('INTRADAY'); }}
                    className={`flex-1 py-1 text-center rounded text-xs transition-all ${
                      product === 'INTRADAY'
                        ? 'bg-slate-700 text-white font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Intraday (MIS)
                  </button>
                  <button
                    type="button"
                    onClick={() => { sound.playClick(); setProduct('DELIVERY'); }}
                    className={`flex-1 py-1 text-center rounded text-xs transition-all ${
                      product === 'DELIVERY'
                        ? 'bg-slate-700 text-white font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Normal (NRML)
                  </button>
                </div>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Order Type</label>
                <div className="flex bg-[#090d16] p-0.5 rounded-lg border border-white/[0.06]">
                  <button
                    type="button"
                    onClick={() => { sound.playClick(); setOrderType('MARKET'); }}
                    className={`flex-1 py-1 text-center rounded text-xs transition-all ${
                      orderType === 'MARKET'
                        ? 'bg-slate-700 text-white font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Market
                  </button>
                  <button
                    type="button"
                    onClick={() => { sound.playClick(); setOrderType('LIMIT'); }}
                    className={`flex-1 py-1 text-center rounded text-xs transition-all ${
                      orderType === 'LIMIT'
                        ? 'bg-slate-700 text-white font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Limit
                  </button>
                </div>
              </div>
            </div>

            {/* 3. Lots and Quick Lot Chips */}
            <div className="bg-[#090d16] p-3.5 rounded-xl border border-white/[0.06] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">Quantity</span>
                <span className="text-[11px] font-mono text-slate-400">
                  1 Lot = {lotSize} Units
                </span>
              </div>

              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center bg-[#101524] px-2 py-1 rounded-lg border border-white/[0.08]">
                  <button
                    type="button"
                    onClick={() => handleLotsChange(-1)}
                    disabled={lots <= 1}
                    className="w-7 h-7 flex items-center justify-center rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm disabled:opacity-30 transition-all"
                  >
                    -
                  </button>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={lots}
                    onChange={(e) => setLots(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-12 text-center bg-transparent font-mono font-bold text-white text-base focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => handleLotsChange(1)}
                    className="w-7 h-7 flex items-center justify-center rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm transition-all"
                  >
                    +
                  </button>
                </div>

                <div className="text-right font-mono">
                  <span className="text-sm font-bold text-white">
                    {quantity} <span className="text-xs text-slate-400 font-normal">Units ({lots} Lots)</span>
                  </span>
                </div>
              </div>

              {/* Quick Lot Chips */}
              <div className="flex items-center gap-1.5 pt-1">
                <span className="text-[10px] text-slate-500 mr-1">Quick:</span>
                {[1, 2, 4, 10].map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => handleSetExactLots(l)}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all ${
                      lots === l
                        ? 'bg-slate-700 text-white font-bold'
                        : 'bg-[#101524] text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {l}x ({l * lotSize})
                  </button>
                ))}
              </div>
            </div>

            {/* 4. Limit Price Stepper (if Limit selected) */}
            {orderType === 'LIMIT' && (
              <div className="bg-[#090d16] p-3.5 rounded-xl border border-white/[0.06] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300 font-medium">Limit Price (₹)</span>
                  <span className="text-[11px] font-mono text-slate-500">Tick: 0.05</span>
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center bg-[#101524] px-2 py-1 rounded-lg border border-white/[0.08]">
                    <button
                      type="button"
                      onClick={() => handlePriceChange(-0.5)}
                      className="w-7 h-7 flex items-center justify-center rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm transition-all"
                    >
                      -
                    </button>
                    <input
                      type="number"
                      step="0.05"
                      min="0.05"
                      value={limitPrice}
                      onChange={(e) => setLimitPrice(parseFloat(e.target.value) || 0)}
                      className="w-20 text-center bg-transparent font-mono font-bold text-white text-base focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handlePriceChange(0.5)}
                      className="w-7 h-7 flex items-center justify-center rounded bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm transition-all"
                    >
                      +
                    </button>
                  </div>

                  <span className="text-xs font-mono text-slate-400">
                    LTP: ₹{orderModalData.price.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            {/* 5. Advanced SL & Target Toggle */}
            <div className="pt-0.5">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
              >
                <ChevronRight className={`w-3.5 h-3.5 transition-transform ${showAdvanced ? 'rotate-90' : ''}`} />
                <span>Stop Loss & Target Protection (Optional)</span>
              </button>

              {showAdvanced && (
                <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-white/[0.04] font-mono">
                  <div>
                    <label className="block text-[10px] text-slate-400 mb-1">Stop Loss Trigger (₹)</label>
                    <input
                      type="number"
                      placeholder="e.g. 140.00"
                      value={stopLoss}
                      onChange={(e) => setStopLoss(e.target.value)}
                      className="w-full bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-400 mb-1">Target Price (₹)</label>
                    <input
                      type="number"
                      placeholder="e.g. 210.00"
                      value={target}
                      onChange={(e) => setTarget(e.target.value)}
                      className="w-full bg-[#090d16] border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Error & Success Feedback */}
            {errorMessage && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center gap-2 text-rose-300 text-xs font-sans">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {successMessage && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center gap-2 text-emerald-300 text-xs font-sans">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{successMessage}</span>
              </div>
            )}

            {/* Margin Breakdown Card */}
            <div className="p-3 bg-[#090d16] rounded-xl border border-white/[0.06] space-y-1.5 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">Required Margin</span>
                <span className="text-white font-bold">
                  ₹{marginRequired.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-500 font-sans">Available Trading Capital</span>
                <span className={hasSufficientMargin ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                  ₹{account.available_balance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Submit Execution Button */}
            <button
              type="button"
              disabled={isSubmitting || !hasSufficientMargin}
              onClick={handleSubmit}
              className={`w-full py-3.5 rounded-xl font-bold text-xs tracking-wider uppercase transition-all flex items-center justify-center gap-2 shadow-lg disabled:opacity-40 disabled:pointer-events-none ${
                isBuy
                  ? 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-[0_0_15px_rgba(16,185,129,0.25)]'
                  : 'bg-rose-500 hover:bg-rose-400 text-white shadow-[0_0_15px_rgba(244,63,94,0.25)]'
              }`}
            >
              {isSubmitting ? (
                <span>Routing to Execution Engine...</span>
              ) : (
                <>
                  <span>
                    Execute {side} Order ({quantity} Units @ ₹{activePrice.toFixed(2)})
                  </span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

