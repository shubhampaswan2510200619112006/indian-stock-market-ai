import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { PaperAccount, PaperPosition, PaperOrder, OrderSide, ProductType, OrderType, OptionType } from '../types/trading';
import { sound } from '../utils/audio';

const STORAGE_KEY = 'indian_market_ai_paper_account_v1';
const DEFAULT_INITIAL_BALANCE = 1000000; // ₹10,00,000 (10 Lakhs)

interface PlaceOrderParams {
  symbol: string;
  underlying: string;
  strike: number;
  option_type: OptionType;
  expiry: string;
  side: OrderSide;
  product: ProductType;
  order_type: OrderType;
  quantity: number;
  lots: number;
  lot_size: number;
  price: number;
  limit_price?: number;
}

interface PaperTradingContextType {
  account: PaperAccount;
  placeOrder: (params: PlaceOrderParams) => Promise<{ success: boolean; order: PaperOrder; message?: string }>;
  closePosition: (position_id: string, qty?: number) => Promise<{ success: boolean; order?: PaperOrder; message?: string }>;
  squareOffAll: () => Promise<void>;
  addFunds: (amount: number) => void;
  resetAccount: () => void;
  updatePositionPrices: (priceMap: Record<string, { ltp: number; tick_direction?: 'up' | 'down' | 'neutral' }>) => void;
  isOrderModalOpen: boolean;
  orderModalData: PlaceOrderParams | null;
  openOrderModal: (params: PlaceOrderParams) => void;
  closeOrderModal: () => void;
}

const PaperTradingContext = createContext<PaperTradingContextType | undefined>(undefined);

// Helper to get formatted IST timestamp with millisecond precision
export function getISTTimestamp(): { istString: string; ms: number } {
  const now = new Date();
  const ms = now.getTime();
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  };
  const parts = new Intl.DateTimeFormat('en-IN', options).format(now);
  const millis = String(now.getMilliseconds()).padStart(3, '0');
  return {
    istString: `${parts}.${millis} IST`,
    ms,
  };
}

export const PaperTradingProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [account, setAccount] = useState<PaperAccount>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && typeof parsed.available_balance === 'number') {
            return parsed;
          }
        }
      } catch (e) {
        console.warn('Failed to load saved paper account:', e);
      }
    }
    return {
      available_balance: DEFAULT_INITIAL_BALANCE,
      initial_balance: DEFAULT_INITIAL_BALANCE,
      invested_margin: 0,
      portfolio_value: DEFAULT_INITIAL_BALANCE,
      total_pnl: 0,
      total_pnl_pct: 0,
      day_pnl: 0,
      day_pnl_pct: 0,
      positions: [],
      orders: [],
    };
  });

  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [orderModalData, setOrderModalData] = useState<PlaceOrderParams | null>(null);

  // Save to localStorage on state change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(account));
    } catch (e) {
      console.warn('Failed to save paper account to localStorage:', e);
    }
  }, [account]);

  // Recalculate portfolio metrics whenever positions change
  const recalculateAccount = useCallback((positions: PaperPosition[], balance: number, orders: PaperOrder[]): PaperAccount => {
    let totalInvested = 0;
    let totalCurrentVal = 0;
    let totalUnrealizedPnL = 0;
    let dayPnL = 0;

    positions.forEach((pos) => {
      totalInvested += pos.invested_amount;
      totalCurrentVal += pos.current_value;
      totalUnrealizedPnL += pos.pnl;
      dayPnL += pos.day_pnl;
    });

    const portfolioVal = balance + totalCurrentVal;
    const initialBal = account.initial_balance || DEFAULT_INITIAL_BALANCE;
    const totalPnL = portfolioVal - initialBal;
    const totalPnLPct = initialBal > 0 ? (totalPnL / initialBal) * 100 : 0;
    const dayPnLPct = portfolioVal > 0 ? (dayPnL / portfolioVal) * 100 : 0;

    return {
      available_balance: Math.max(0, balance),
      initial_balance: initialBal,
      invested_margin: totalInvested,
      portfolio_value: portfolioVal,
      total_pnl: totalPnL,
      total_pnl_pct: totalPnLPct,
      day_pnl: dayPnL,
      day_pnl_pct: dayPnLPct,
      positions,
      orders,
    };
  }, [account.initial_balance]);

  // High-frequency live LTP updater called from real-time tick engine
  const updatePositionPrices = useCallback((priceMap: Record<string, { ltp: number; tick_direction?: 'up' | 'down' | 'neutral' }>) => {
    setAccount((prev) => {
      if (prev.positions.length === 0) return prev;
      let hasChanges = false;

      const updatedPositions = prev.positions.map((pos) => {
        const update = priceMap[pos.symbol];
        if (!update || update.ltp <= 0 || update.ltp === pos.current_ltp) {
          return pos;
        }

        hasChanges = true;
        const newLtp = update.ltp;
        const prevLtp = pos.current_ltp;
        const currentVal = pos.side === 'BUY'
          ? newLtp * pos.quantity
          : (pos.avg_price * 2 - newLtp) * pos.quantity;

        const pnl = pos.side === 'BUY'
          ? (newLtp - pos.avg_price) * pos.quantity
          : (pos.avg_price - newLtp) * pos.quantity;

        const pnlPct = pos.invested_amount > 0 ? (pnl / pos.invested_amount) * 100 : 0;

        return {
          ...pos,
          prev_ltp: prevLtp,
          current_ltp: newLtp,
          current_value: currentVal,
          pnl,
          pnl_percentage: pnlPct,
          day_pnl: pnl,
          tick_direction: update.tick_direction || (newLtp > prevLtp ? 'up' : newLtp < prevLtp ? 'down' : 'neutral'),
        };
      });

      if (!hasChanges) return prev;
      return recalculateAccount(updatedPositions, prev.available_balance, prev.orders);
    });
  }, [recalculateAccount]);

  // Place order
  const placeOrder = useCallback(async (params: PlaceOrderParams) => {
    const { istString, ms } = getISTTimestamp();
    const simulatedLatencyMs = Math.floor(12 + Math.random() * 20); // 12ms - 32ms execution

    const executionPrice = params.order_type === 'LIMIT' && params.limit_price
      ? params.limit_price
      : params.price;

    const marginRequired = params.side === 'BUY'
      ? executionPrice * params.quantity
      : (executionPrice * params.quantity) * 1.5; // realistic selling margin

    // Check margin sufficiency
    if (account.available_balance < marginRequired) {
      const rejectOrder: PaperOrder = {
        order_id: `ORD_${Date.now()}_REJ`,
        symbol: params.symbol,
        underlying: params.underlying,
        strike: params.strike,
        option_type: params.option_type,
        expiry: params.expiry,
        side: params.side,
        product: params.product,
        order_type: params.order_type,
        quantity: params.quantity,
        lots: params.lots,
        lot_size: params.lot_size,
        price: params.price,
        execution_price: 0,
        status: 'REJECTED',
        timestamp_ist: istString,
        timestamp_ms: ms,
        execution_latency_ms: simulatedLatencyMs,
        margin_used: 0,
        rejection_reason: `Insufficient Margin. Required: ₹${marginRequired.toFixed(2)}, Available: ₹${account.available_balance.toFixed(2)}`,
      };

      setAccount((prev) => ({
        ...prev,
        orders: [rejectOrder, ...prev.orders],
      }));

      return {
        success: false,
        order: rejectOrder,
        message: rejectOrder.rejection_reason,
      };
    }

    // Execution success
    const completedOrder: PaperOrder = {
      order_id: `ORD_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      symbol: params.symbol,
      underlying: params.underlying,
      strike: params.strike,
      option_type: params.option_type,
      expiry: params.expiry,
      side: params.side,
      product: params.product,
      order_type: params.order_type,
      quantity: params.quantity,
      lots: params.lots,
      lot_size: params.lot_size,
      price: params.price,
      execution_price: executionPrice,
      status: 'COMPLETED',
      timestamp_ist: istString,
      timestamp_ms: ms,
      execution_latency_ms: simulatedLatencyMs,
      margin_used: marginRequired,
    };

    // Update positions: merge if matching position exists or append
    let newPositions = [...account.positions];
    const existingIndex = newPositions.findIndex(
      (p) => p.symbol === params.symbol && p.side === params.side && p.product === params.product
    );

    if (existingIndex >= 0) {
      const existing = newPositions[existingIndex];
      const totalQty = existing.quantity + params.quantity;
      const totalCost = (existing.avg_price * existing.quantity) + (executionPrice * params.quantity);
      const newAvg = totalCost / totalQty;
      const currentVal = executionPrice * totalQty;
      const pnl = (executionPrice - newAvg) * totalQty;
      const pnlPct = totalCost > 0 ? (pnl / totalCost) * 100 : 0;

      newPositions[existingIndex] = {
        ...existing,
        quantity: totalQty,
        lots: existing.lots + params.lots,
        avg_price: parseFloat(newAvg.toFixed(2)),
        current_ltp: executionPrice,
        invested_amount: totalCost,
        current_value: currentVal,
        pnl,
        pnl_percentage: pnlPct,
        day_pnl: pnl,
      };
    } else {
      const currentVal = executionPrice * params.quantity;
      const newPos: PaperPosition = {
        position_id: `POS_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
        symbol: params.symbol,
        underlying: params.underlying,
        strike: params.strike,
        option_type: params.option_type,
        expiry: params.expiry,
        product: params.product,
        side: params.side,
        quantity: params.quantity,
        lots: params.lots,
        lot_size: params.lot_size,
        avg_price: executionPrice,
        current_ltp: executionPrice,
        invested_amount: marginRequired,
        current_value: currentVal,
        pnl: 0,
        pnl_percentage: 0,
        day_pnl: 0,
        timestamp_ist: istString,
        timestamp_ms: ms,
      };
      newPositions = [newPos, ...newPositions];
    }

    const newBalance = account.available_balance - marginRequired;
    const newOrders = [completedOrder, ...account.orders];

    setAccount(recalculateAccount(newPositions, newBalance, newOrders));
    sound.playOrderSuccess();

    return {
      success: true,
      order: completedOrder,
      message: `Order Executed! ${params.side} ${params.quantity} Qty ${params.symbol} @ ₹${executionPrice.toFixed(2)}`,
    };
  }, [account, recalculateAccount]);

  // Close / Square off position
  const closePosition = useCallback(async (position_id: string, qty?: number) => {
    const pos = account.positions.find((p) => p.position_id === position_id);
    if (!pos) return { success: false, message: 'Position not found' };

    const { istString, ms } = getISTTimestamp();
    const closeQty = qty && qty < pos.quantity ? qty : pos.quantity;
    const closeSide: OrderSide = pos.side === 'BUY' ? 'SELL' : 'BUY';
    const closePrice = pos.current_ltp;
    const latencyMs = Math.floor(10 + Math.random() * 15);

    // Calculate proceeds returned to balance
    // Margin originally used for this portion + realized PnL
    const fraction = closeQty / pos.quantity;
    const investedPortion = pos.invested_amount * fraction;
    const realizedPnL = pos.side === 'BUY'
      ? (closePrice - pos.avg_price) * closeQty
      : (pos.avg_price - closePrice) * closeQty;

    const returnedToBalance = investedPortion + realizedPnL;

    const closeOrder: PaperOrder = {
      order_id: `ORD_${Date.now()}_CLOSE`,
      symbol: pos.symbol,
      underlying: pos.underlying,
      strike: pos.strike,
      option_type: pos.option_type,
      expiry: pos.expiry,
      side: closeSide,
      product: pos.product,
      order_type: 'MARKET',
      quantity: closeQty,
      lots: Math.round(closeQty / pos.lot_size),
      lot_size: pos.lot_size,
      price: closePrice,
      execution_price: closePrice,
      status: 'COMPLETED',
      timestamp_ist: istString,
      timestamp_ms: ms,
      execution_latency_ms: latencyMs,
      margin_used: 0,
    };

    let newPositions: PaperPosition[];
    if (closeQty >= pos.quantity) {
      newPositions = account.positions.filter((p) => p.position_id !== position_id);
    } else {
      const remainingQty = pos.quantity - closeQty;
      const remainingInvested = pos.invested_amount - investedPortion;
      const remainingVal = closePrice * remainingQty;
      const remainingPnL = pos.pnl * (1 - fraction);
      newPositions = account.positions.map((p) =>
        p.position_id === position_id
          ? {
              ...p,
              quantity: remainingQty,
              lots: Math.round(remainingQty / p.lot_size),
              invested_amount: remainingInvested,
              current_value: remainingVal,
              pnl: remainingPnL,
              pnl_percentage: remainingInvested > 0 ? (remainingPnL / remainingInvested) * 100 : 0,
            }
          : p
      );
    }

    const newBalance = account.available_balance + returnedToBalance;
    const newOrders = [closeOrder, ...account.orders];

    setAccount(recalculateAccount(newPositions, newBalance, newOrders));
    sound.playOrderSuccess();

    return {
      success: true,
      order: closeOrder,
      message: `Position Squared Off: ${pos.symbol} @ ₹${closePrice.toFixed(2)} (P&L: ${realizedPnL >= 0 ? '+' : ''}₹${realizedPnL.toFixed(2)})`,
    };
  }, [account, recalculateAccount]);

  // Square off all open positions
  const squareOffAll = useCallback(async () => {
    if (account.positions.length === 0) return;
    for (const pos of account.positions) {
      await closePosition(pos.position_id);
    }
  }, [account.positions, closePosition]);

  // Add paper funds
  const addFunds = useCallback((amount: number) => {
    setAccount((prev) => {
      const newBal = prev.available_balance + amount;
      const newInitial = (prev.initial_balance || DEFAULT_INITIAL_BALANCE) + amount;
      return {
        ...prev,
        available_balance: newBal,
        initial_balance: newInitial,
        portfolio_value: prev.portfolio_value + amount,
      };
    });
  }, []);

  // Reset account back to initial ₹10 Lakhs
  const resetAccount = useCallback(() => {
    const cleanAccount: PaperAccount = {
      available_balance: DEFAULT_INITIAL_BALANCE,
      initial_balance: DEFAULT_INITIAL_BALANCE,
      invested_margin: 0,
      portfolio_value: DEFAULT_INITIAL_BALANCE,
      total_pnl: 0,
      total_pnl_pct: 0,
      day_pnl: 0,
      day_pnl_pct: 0,
      positions: [],
      orders: [],
    };
    setAccount(cleanAccount);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cleanAccount));
    } catch {}
  }, []);

  const openOrderModal = useCallback((params: PlaceOrderParams) => {
    setOrderModalData(params);
    setIsOrderModalOpen(true);
    sound.playClick();
  }, []);

  const closeOrderModal = useCallback(() => {
    setIsOrderModalOpen(false);
  }, []);

  return (
    <PaperTradingContext.Provider
      value={{
        account,
        placeOrder,
        closePosition,
        squareOffAll,
        addFunds,
        resetAccount,
        updatePositionPrices,
        isOrderModalOpen,
        orderModalData,
        openOrderModal,
        closeOrderModal,
      }}
    >
      {children}
    </PaperTradingContext.Provider>
  );
};

export const usePaperTrading = () => {
  const context = useContext(PaperTradingContext);
  if (!context) {
    throw new Error('usePaperTrading must be used within a PaperTradingProvider');
  }
  return context;
};
