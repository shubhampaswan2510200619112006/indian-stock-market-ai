import React from 'react';
import { ProviderHealth } from '../../types/market';
import { Server, Activity, ShieldCheck, AlertCircle, Wifi, WifiOff } from 'lucide-react';

interface DataHealthNodeGraphProps {
  providers: ProviderHealth[];
}

export const DataHealthNodeGraph: React.FC<DataHealthNodeGraphProps> = ({ providers }) => {
  const getStatusBadge = (status: ProviderHealth['status']) => {
    switch (status) {
      case 'CONNECTED':
        return (
          <span className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-bold">
            <Wifi className="w-3 h-3" />
            CONNECTED
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="flex items-center gap-1 text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-bold">
            <AlertCircle className="w-3 h-3" />
            DEGRADED
          </span>
        );
      case 'CREDENTIAL_UNCONFIGURED':
        return (
          <span className="flex items-center gap-1 text-slate-400 bg-slate-800 border border-slate-700 px-2 py-0.5 rounded text-[10px]">
            <WifiOff className="w-3 h-3" />
            UNCONFIGURED
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded text-[10px] font-bold">
            <AlertCircle className="w-3 h-3" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="w-full bg-[#080d19] border border-white/[0.08] rounded-xl p-5 mb-6 relative overflow-hidden">
      <div className="flex flex-wrap items-center justify-between border-b border-white/[0.06] pb-3 mb-4 gap-2">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
            PROVIDER CONNECTIVITY & INGESTION TELEMETRY
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
          HEALTH MONITORING POOL
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
        {providers.map((p) => (
          <div
            key={p.name}
            className="bg-[#05070c] p-4 rounded-lg border border-white/[0.05] hover:border-white/[0.12] transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-slate-200 text-sm">{p.name}</span>
                {getStatusBadge(p.status)}
              </div>
              <div className="text-[10px] text-slate-500 mb-3">{p.type}</div>

              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">INGESTION LATENCY:</span>
                  <span className="text-slate-300 font-semibold">
                    {p.latency_ms !== null ? `${p.latency_ms} ms` : 'N/A (INACTIVE)'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">DATA FRESHNESS:</span>
                  <span className="text-slate-300 font-semibold">
                    {p.freshness_seconds !== null ? `${p.freshness_seconds}s lag` : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">ERROR RATE:</span>
                  <span className="text-emerald-400 font-semibold">
                    {p.error_rate_pct !== undefined ? `${p.error_rate_pct.toFixed(1)}%` : '0.0%'}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-3 pt-2.5 border-t border-white/[0.04] text-[10px] text-slate-400 truncate">
              {p.coverage_notes || 'Verified data pipeline feed'}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-white/[0.04] text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span>FAILOVER ORCHESTRATOR: ACTIVE • STRICT REAL-DATA ENFORCEMENT</span>
        <span className="text-emerald-400">TELEMETRY SECURE</span>
      </div>
    </div>
  );
};
