import React from 'react';

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', style }) => (
  <div
    className={`relative overflow-hidden bg-[#161F2D]/80 rounded-xl before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.8s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/[0.07] before:to-transparent ${className}`}
    style={style}
  />
);

/** Complete Dashboard Desk Skeleton */
export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6 animate-pulse-subtle">
    {/* 1. Header strip skeleton */}
    <div className="p-4 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl flex justify-between items-center">
      <div className="space-y-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-3 w-72" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-28" />
      </div>
    </div>

    {/* 2. 4 Index Cards Skeleton */}
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="p-4 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl space-y-3">
          <div className="flex justify-between items-center">
            <Skeleton className="h-3.5 w-20" />
            <Skeleton className="h-4 w-14 rounded-full" />
          </div>
          <Skeleton className="h-7 w-32" />
          <Skeleton className="h-2 w-full rounded-full" />
          <div className="flex justify-between pt-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>

    {/* 3. AI Alpha Predictor Marquee Skeleton */}
    <div className="p-5 rounded-2xl bg-[#101622]/80 border border-[#B6FF5C]/20 backdrop-blur-xl space-y-4">
      <div className="flex justify-between items-center">
        <div className="flex gap-3 items-center">
          <Skeleton className="w-9 h-9 rounded-xl" />
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-64" />
          </div>
        </div>
        <Skeleton className="h-8 w-32 rounded-xl" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 bg-[#0B1220]/70 p-4 rounded-xl border border-white/[0.06]">
        <div className="md:col-span-5 space-y-2">
          <Skeleton className="h-5 w-28" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-3 w-56" />
        </div>
        <div className="md:col-span-4 grid grid-cols-3 gap-2">
          <Skeleton className="h-14 rounded-xl" />
          <Skeleton className="h-14 rounded-xl" />
          <Skeleton className="h-14 rounded-xl" />
        </div>
        <div className="md:col-span-3">
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      </div>
    </div>

    {/* 4. Chart Workspace Skeleton */}
    <div className="p-5 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl space-y-4">
      <div className="flex justify-between items-center pb-3 border-b border-white/[0.06]">
        <Skeleton className="h-5 w-48" />
        <div className="flex gap-2">
          <Skeleton className="h-7 w-12" />
          <Skeleton className="h-7 w-12" />
          <Skeleton className="h-7 w-12" />
        </div>
      </div>
      <div className="h-[380px] w-full flex items-end gap-1.5 p-4 bg-[#070a14]/60 rounded-xl border border-white/[0.04]">
        {Array.from({ length: 36 }).map((_, i) => (
          <div key={i} className="flex-1 flex flex-col justify-end items-center gap-1 h-full">
            <Skeleton
              className="w-full rounded-sm"
              style={{
                height: `${25 + Math.abs(Math.sin(i * 0.4)) * 60}%`,
                opacity: 0.35 + (i / 36) * 0.45,
              }}
            />
            <Skeleton
              className="w-full rounded-xs"
              style={{
                height: `${10 + Math.abs(Math.cos(i * 0.6)) * 25}%`,
                opacity: 0.25,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  </div>
);

/** Complete Trading Terminal Skeleton */
export const TradingTerminalSkeleton: React.FC = () => (
  <div className="space-y-4 animate-pulse-subtle">
    {/* Top Instrument Ticker Strip */}
    <div className="p-4 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl flex justify-between items-center">
      <div className="flex gap-4 items-center">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-6 w-24" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>

    {/* AI Predictor Marquee Skeleton */}
    <div className="p-4 rounded-2xl bg-[#101622]/80 border border-[#B6FF5C]/20 backdrop-blur-xl">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
        <div className="md:col-span-5 space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-5 w-44" />
        </div>
        <div className="md:col-span-4 grid grid-cols-3 gap-2">
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
        </div>
        <div className="md:col-span-3">
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    </div>

    {/* 3-Column Workstation Grid */}
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
      {/* Watchlist (3 cols) */}
      <div className="xl:col-span-3 p-3.5 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl space-y-3">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-8 w-full" />
        <div className="space-y-2">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-xl" />
          ))}
        </div>
      </div>

      {/* Chart Canvas (6 cols) */}
      <div className="xl:col-span-6 p-4 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl space-y-3">
        <div className="flex justify-between">
          <Skeleton className="h-5 w-36" />
          <Skeleton className="h-6 w-48" />
        </div>
        <div className="h-[400px] w-full flex items-end gap-1.5 p-4 bg-[#070a14]/60 rounded-xl">
          {Array.from({ length: 30 }).map((_, i) => (
            <Skeleton
              key={i}
              className="flex-1 rounded-sm"
              style={{ height: `${30 + Math.abs(Math.sin(i * 0.5)) * 55}%` }}
            />
          ))}
        </div>
      </div>

      {/* Market Depth Ladder (3 cols) */}
      <div className="xl:col-span-3 p-3.5 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl space-y-3">
        <Skeleton className="h-4 w-32" />
        <div className="space-y-1.5">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-6 w-full" />
          ))}
        </div>
        <Skeleton className="h-4 w-24 pt-2" />
        <Skeleton className="h-28 w-full rounded-xl" />
      </div>
    </div>
  </div>
);

/** Option Chain Table Skeleton */
export const OptionChainSkeleton: React.FC = () => (
  <div className="p-4 rounded-2xl bg-[#101622]/80 border border-white/[0.06] backdrop-blur-xl space-y-4 animate-pulse-subtle">
    <div className="flex justify-between items-center pb-3 border-b border-white/[0.06]">
      <Skeleton className="h-5 w-48" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-28" />
        <Skeleton className="h-8 w-28" />
      </div>
    </div>
    <div className="space-y-1.5">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="grid grid-cols-11 gap-2">
          {Array.from({ length: 11 }).map((_, j) => (
            <Skeleton key={j} className="h-7 rounded" style={{ opacity: j === 5 ? 0.9 : 0.5 }} />
          ))}
        </div>
      ))}
    </div>
  </div>
);
