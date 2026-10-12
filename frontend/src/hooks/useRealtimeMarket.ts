import { useState, useEffect, useCallback } from 'react';
import { IndexInstrument, OptionStrikeRow, OptionLegQuote } from '../types/trading';
import { Candle } from '../types/market';
import { usePaperTrading } from '../context/PaperTradingContext';
import { getISTTime, ISTTimeData } from '../utils/istTime';

// Default instruments configuration for Indian markets
const INITIAL_INSTRUMENTS: Record<string, IndexInstrument> = {
  NIFTY: {
    symbol: 'NIFTY',
    name: 'NIFTY 50',
    spot_price: 24652.80,
    change: 128.40,
    change_pct: 0.52,
    lot_size: 25,
    strike_step: 50,
    high: 24710.50,
    low: 24580.20,
    open: 24590.00,
    prev_close: 24524.40,
    pcr: 0.96,
    max_pain: 24650,
    expiries: ['17 OCT 2026', '24 OCT 2026', '31 OCT 2026', '07 NOV 2026'],
    active_expiry: '17 OCT 2026',
    tick_direction: 'up',
  },
  BANKNIFTY: {
    symbol: 'BANKNIFTY',
    name: 'BANK NIFTY',
    spot_price: 51240.50,
    change: -115.30,
    change_pct: -0.22,
    lot_size: 15,
    strike_step: 100,
    high: 51480.00,
    low: 51110.20,
    open: 51390.00,
    prev_close: 51355.80,
    pcr: 0.88,
    max_pain: 51200,
    expiries: ['16 OCT 2026', '23 OCT 2026', '30 OCT 2026', '06 NOV 2026'],
    active_expiry: '16 OCT 2026',
    tick_direction: 'down',
  },
  FINNIFTY: {
    symbol: 'FINNIFTY',
    name: 'NIFTY FINANCIAL',
    spot_price: 23892.15,
    change: 74.20,
    change_pct: 0.31,
    lot_size: 25,
    strike_step: 50,
    high: 23945.00,
    low: 23810.00,
    open: 23825.00,
    prev_close: 23817.95,
    pcr: 1.04,
    max_pain: 23900,
    expiries: ['21 OCT 2026', '28 OCT 2026', '04 NOV 2026'],
    active_expiry: '21 OCT 2026',
    tick_direction: 'up',
  },
  SENSEX: {
    symbol: 'SENSEX',
    name: 'BSE SENSEX',
    spot_price: 81420.75,
    change: 412.30,
    change_pct: 0.51,
    lot_size: 10,
    strike_step: 100,
    high: 81610.00,
    low: 81180.00,
    open: 81220.00,
    prev_close: 81008.45,
    pcr: 0.92,
    max_pain: 81400,
    expiries: ['18 OCT 2026', '25 OCT 2026', '01 NOV 2026'],
    active_expiry: '18 OCT 2026',
    tick_direction: 'up',
  },
  RELIANCE: {
    symbol: 'RELIANCE',
    name: 'RELIANCE IND',
    spot_price: 2984.50,
    change: 22.80,
    change_pct: 0.77,
    lot_size: 250,
    strike_step: 20,
    high: 2998.00,
    low: 2962.00,
    open: 2965.00,
    prev_close: 2961.70,
    pcr: 1.12,
    max_pain: 2980,
    expiries: ['31 OCT 2026', '28 NOV 2026'],
    active_expiry: '31 OCT 2026',
    tick_direction: 'up',
  },
};

// Generate initial option chain strikes centered at ATM
function generateChainStrikes(spot: number, step: number, expiry: string, symbol: string): OptionStrikeRow[] {
  const atmStrike = Math.round(spot / step) * step;
  const rows: OptionStrikeRow[] = [];

  for (let i = -10; i <= 10; i++) {
    const strike = atmStrike + i * step;
    const isAtm = strike === atmStrike;
    const isCeItm = strike < spot;
    const isPeItm = strike > spot;

    const ceIntrinsic = Math.max(0, spot - strike);
    const peIntrinsic = Math.max(0, strike - spot);

    const distFromAtm = Math.abs(strike - spot);
    const baseTimeVal = (spot * 0.007) / Math.sqrt(1 + distFromAtm / (step * 2));

    const ceLtp = parseFloat(Math.max(1.2, ceIntrinsic + baseTimeVal).toFixed(2));
    const peLtp = parseFloat(Math.max(1.2, peIntrinsic + baseTimeVal * 0.95).toFixed(2));

    const ceOi = Math.round(Math.max(15000, 380000 - (strike - spot) * 45 + Math.random() * 20000));
    const peOi = Math.round(Math.max(18000, 410000 + (strike - spot) * 40 + Math.random() * 20000));

    const ceLeg: OptionLegQuote = {
      ltp: ceLtp,
      change: parseFloat(((Math.random() - 0.45) * 8).toFixed(2)),
      change_pct: parseFloat(((Math.random() - 0.45) * 6).toFixed(2)),
      oi: ceOi,
      oi_chg_pct: parseFloat(((Math.random() - 0.48) * 12).toFixed(1)),
      volume: Math.round(ceOi * (0.35 + Math.random() * 0.2)),
      iv: parseFloat((13.2 + (distFromAtm / (step * 4)) * 0.6).toFixed(1)),
      delta: parseFloat(Math.min(0.99, Math.max(0.01, 0.5 + (spot - strike) / (step * 10))).toFixed(2)),
      bid: parseFloat(Math.max(0.5, ceLtp - 0.35).toFixed(2)),
      ask: parseFloat((ceLtp + 0.35).toFixed(2)),
      tick_direction: 'neutral',
    };

    const peLeg: OptionLegQuote = {
      ltp: peLtp,
      change: parseFloat(((Math.random() - 0.52) * 8).toFixed(2)),
      change_pct: parseFloat(((Math.random() - 0.52) * 6).toFixed(2)),
      oi: peOi,
      oi_chg_pct: parseFloat(((Math.random() - 0.48) * 12).toFixed(1)),
      volume: Math.round(peOi * (0.35 + Math.random() * 0.2)),
      iv: parseFloat((13.6 + (distFromAtm / (step * 4)) * 0.7).toFixed(1)),
      delta: parseFloat(Math.max(-0.99, Math.min(-0.01, -0.5 + (spot - strike) / (step * 10))).toFixed(2)),
      bid: parseFloat(Math.max(0.5, peLtp - 0.35).toFixed(2)),
      ask: parseFloat((peLtp + 0.35).toFixed(2)),
      tick_direction: 'neutral',
    };

    rows.push({
      strike,
      is_atm: isAtm,
      is_ce_itm: isCeItm,
      is_pe_itm: isPeItm,
      ce: ceLeg,
      pe: peLeg,
    });
  }

  return rows;
}

// Generate realistic Indian intraday session candles (from 09:15 AM IST to 03:30 PM IST)
function generateIntradaySessionCandles(inst: IndexInstrument, ist: ISTTimeData, timeframe: string): Candle[] {
  const candles: Candle[] = [];
  let currentPrice = inst.open;

  // Session parameters: Market opens 09:15 IST (555 minutes), closes 15:30 IST (930 minutes)
  const marketOpenMins = 555;
  const marketCloseMins = 930;
  const currentTotalMins = ist.hours * 60 + ist.minutes;

  // Determine the end minute for the candles:
  // If market is closed (current >= 15:30 or weekend or before 09:15), the completed session ends at 15:30 (930 mins)
  // If market is open, ends at current time
  let endMins = marketCloseMins;
  if (ist.isMarketOpen) {
    endMins = Math.min(marketCloseMins, Math.max(marketOpenMins + 5, currentTotalMins));
  }

  const stepMinutes = timeframe === '1m' ? 1 : timeframe === '15m' ? 15 : timeframe === '1h' ? 60 : 5;
  const totalSlots = Math.max(1, Math.floor((endMins - marketOpenMins) / stepMinutes));

  for (let slot = 0; slot <= totalSlots; slot++) {
    const slotMins = marketOpenMins + slot * stepMinutes;
    if (slotMins > endMins) break;

    const candleHour = Math.floor(slotMins / 60);
    const candleMin = slotMins % 60;
    const hh = String(candleHour).padStart(2, '0');
    const mm = String(candleMin).padStart(2, '0');
    const timeLabel = `${hh}:${mm} IST`;

    // Drift towards close mark near 15:30
    const progress = slot / (totalSlots || 1);
    const targetPrice = inst.open + (inst.spot_price - inst.open) * progress;
    const noise = (Math.random() - 0.49) * (inst.strike_step * 0.25);

    const open = currentPrice;
    const close = parseFloat((targetPrice + noise).toFixed(2));
    const high = parseFloat((Math.max(open, close) + Math.random() * (inst.strike_step * 0.2)).toFixed(2));
    const low = parseFloat((Math.min(open, close) - Math.random() * (inst.strike_step * 0.2)).toFixed(2));
    const volume = Math.round(40000 + Math.random() * 180000);

    candles.push({
      timestamp: timeLabel,
      open,
      high,
      low,
      close,
      volume,
      vwap: parseFloat(((open + high + low + close) / 4).toFixed(2)),
    });

    currentPrice = close;
  }

  // Ensure last candle matches spot mark
  if (candles.length > 0) {
    const last = candles[candles.length - 1];
    last.close = inst.spot_price;
    last.high = Math.max(last.high, inst.spot_price);
    last.low = Math.min(last.low, inst.spot_price);
  }

  return candles;
}

export function useRealtimeMarket() {
  const { updatePositionPrices } = usePaperTrading();

  const [instruments, setInstruments] = useState<Record<string, IndexInstrument>>(INITIAL_INSTRUMENTS);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('NIFTY');
  const [selectedExpiry, setSelectedExpiry] = useState<string>(INITIAL_INSTRUMENTS.NIFTY.active_expiry);
  const [chainRows, setChainRows] = useState<OptionStrikeRow[]>(() =>
    generateChainStrikes(
      INITIAL_INSTRUMENTS.NIFTY.spot_price,
      INITIAL_INSTRUMENTS.NIFTY.strike_step,
      INITIAL_INSTRUMENTS.NIFTY.active_expiry,
      'NIFTY'
    )
  );

  // Authoritative IST Time state using UTC+05:30 arithmetic
  const [timeState, setTimeState] = useState<ISTTimeData>(() => getISTTime());

  // Intraday candles for the selected symbol
  const [intradayCandles, setIntradayCandles] = useState<Candle[]>(() => {
    const inst = INITIAL_INSTRUMENTS.NIFTY;
    const ist = getISTTime();
    return generateIntradaySessionCandles(inst, ist, '5m');
  });

  // Regenerate candles when symbol changes or market closes
  useEffect(() => {
    const inst = instruments[selectedSymbol] || instruments.NIFTY;
    const ist = getISTTime();
    setIntradayCandles(generateIntradaySessionCandles(inst, ist, '5m'));
  }, [selectedSymbol]);

  // High-precision clock timer updating every 40ms with exact IST
  useEffect(() => {
    let animFrame: number;
    let lastUpdate = Date.now();

    const loop = () => {
      const now = Date.now();
      if (now - lastUpdate >= 35) {
        lastUpdate = now;
        const currentIst = getISTTime();
        setTimeState(currentIst);
      }
      animFrame = requestAnimationFrame(loop);
    };

    animFrame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animFrame);
  }, []);

  // Update option chain when symbol or expiry changes
  useEffect(() => {
    const inst = instruments[selectedSymbol];
    if (inst) {
      setChainRows(generateChainStrikes(inst.spot_price, inst.strike_step, selectedExpiry, selectedSymbol));
    }
  }, [selectedSymbol, selectedExpiry]);

  // Ticks: only generate live active ticks when market is OPEN
  // When market is CLOSED, prices remain fixed at final session close
  useEffect(() => {
    // If market is closed, don't simulate live trading ticks
    if (!timeState.isMarketOpen) return;

    const tickInterval = setInterval(() => {
      setInstruments((prev) => {
        const next = { ...prev };
        const priceMap: Record<string, { ltp: number; tick_direction?: 'up' | 'down' | 'neutral' }> = {};

        Object.keys(next).forEach((sym) => {
          const inst = next[sym];
          const tickDelta = (Math.random() - 0.495) * (inst.strike_step * 0.04);
          const newSpot = parseFloat((inst.spot_price + tickDelta).toFixed(2));
          const tickDir: 'up' | 'down' = newSpot >= inst.spot_price ? 'up' : 'down';
          const newChange = parseFloat((newSpot - inst.prev_close).toFixed(2));
          const newChangePct = parseFloat(((newChange / inst.prev_close) * 100).toFixed(2));

          next[sym] = {
            ...inst,
            spot_price: newSpot,
            change: newChange,
            change_pct: newChangePct,
            high: Math.max(inst.high, newSpot),
            low: Math.min(inst.low, newSpot),
            tick_direction: tickDir,
          };
        });

        const activeInst = next[selectedSymbol];
        if (activeInst) {
          setChainRows((prevRows) => {
            return prevRows.map((row) => {
              const strike = row.strike;
              const spot = activeInst.spot_price;

              const ceRandTick = (Math.random() - 0.49) * 0.4;
              const newCeLtp = parseFloat(Math.max(0.5, row.ce.ltp + ceRandTick).toFixed(2));
              const ceDir: 'up' | 'down' | 'neutral' = newCeLtp > row.ce.ltp ? 'up' : newCeLtp < row.ce.ltp ? 'down' : 'neutral';

              const peRandTick = (Math.random() - 0.49) * 0.4;
              const newPeLtp = parseFloat(Math.max(0.5, row.pe.ltp + peRandTick).toFixed(2));
              const peDir: 'up' | 'down' | 'neutral' = newPeLtp > row.pe.ltp ? 'up' : newPeLtp < row.pe.ltp ? 'down' : 'neutral';

              const ceSymbol = `${selectedSymbol} ${strike} CE ${selectedExpiry.split(' ')[0]} ${selectedExpiry.split(' ')[1]}`;
              const peSymbol = `${selectedSymbol} ${strike} PE ${selectedExpiry.split(' ')[0]} ${selectedExpiry.split(' ')[1]}`;

              priceMap[ceSymbol] = { ltp: newCeLtp, tick_direction: ceDir };
              priceMap[peSymbol] = { ltp: newPeLtp, tick_direction: peDir };

              return {
                ...row,
                is_atm: Math.abs(strike - spot) < activeInst.strike_step / 2,
                is_ce_itm: strike < spot,
                is_pe_itm: strike > spot,
                ce: {
                  ...row.ce,
                  ltp: newCeLtp,
                  tick_direction: ceDir,
                },
                pe: {
                  ...row.pe,
                  ltp: newPeLtp,
                  tick_direction: peDir,
                },
              };
            });
          });

          updatePositionPrices(priceMap);
        }

        return next;
      });
    }, 400);

    return () => clearInterval(tickInterval);
  }, [timeState.isMarketOpen, selectedSymbol, selectedExpiry, updatePositionPrices]);

  const activeInstrument = instruments[selectedSymbol] || instruments.NIFTY;

  return {
    instruments,
    selectedSymbol,
    setSelectedSymbol,
    selectedExpiry,
    setSelectedExpiry,
    activeInstrument,
    chainRows,
    timeState,
    intradayCandles,
  };
}
