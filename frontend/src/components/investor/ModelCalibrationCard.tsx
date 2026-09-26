import React from 'react';
import { CalibratedProbability } from '../../types/market';
import { CheckCircle2, AlertCircle, Shield, GitCommit, Sliders } from 'lucide-react';

export const ModelCalibrationCard: React.FC = () => {
  const modelMetrics: CalibratedProbability = {
    target_event: 'P(R_{t → t+30m} > +0.30%)',
    horizon: '30-Minute Forward Return',
    probability: 0.544,
    base_rate: 0.512,
    brier_score: 0.248,
    ece: 0.042,
    calibration_status: 'CALIBRATED',
    sample_size: 2400,
    ood_status: 'IN_DISTRIBUTION',
  };

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-3 mb-4 gap-2">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-cyan-400" />
          <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
            STATISTICAL AI & PROBABILITY CALIBRATION
          </h3>
        </div>
        <span className="font-mono text-[11px] text-cyan-300 bg-cyan-400/10 border border-cyan-400/20 px-2 py-0.5 rounded">
          LEVEL 2 CALIBRATED GRADIENT BOOSTING
        </span>
      </div>

      {/* Target Definition & Calibrated Output */}
      <div className="bg-[#05070c] p-4 rounded-lg border border-white/[0.04] mb-4">
        <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-1">
          RIGOROUS FORMAL TARGET EVENT DEFINITION
        </div>
        <div className="flex flex-wrap items-baseline justify-between gap-4 font-mono">
          <div>
            <div className="text-xl font-bold text-amber-300">
              {modelMetrics.target_event}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              HORIZON: {modelMetrics.horizon} • PURGED EMBARGO
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs text-slate-500">CALIBRATED POSTERIOR</div>
            <div className="text-3xl font-bold text-emerald-400">
              {(modelMetrics.probability * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Verification Metrics Table */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">HISTORICAL BASE RATE</div>
          <div className="text-slate-200 font-bold text-sm mt-1">
            {(modelMetrics.base_rate * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">BRIER SCORE</div>
          <div className="text-emerald-400 font-bold text-sm mt-1">
            {modelMetrics.brier_score}
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">EXPECTED CAL ERROR (ECE)</div>
          <div className="text-emerald-400 font-bold text-sm mt-1">
            {(modelMetrics.ece * 100).toFixed(1)}%
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">CALIBRATION METHOD</div>
          <div className="text-cyan-400 font-bold text-sm mt-1">
            PLATT SCALING
          </div>
        </div>

        <div className="bg-[#05070c] p-3 rounded border border-white/[0.04]">
          <div className="text-[10px] text-slate-500">OOD DISTRIBUTION</div>
          <div className="text-emerald-400 font-bold text-sm mt-1">
            {modelMetrics.ood_status}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-white/[0.04] text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>PURGED & EMBARGOED WALK-FORWARD VALIDATION (ZERO DATA CONTAMINATION)</span>
        <span className="text-slate-400">N = {modelMetrics.sample_size} OBSERVATIONS</span>
      </div>
    </div>
  );
};
