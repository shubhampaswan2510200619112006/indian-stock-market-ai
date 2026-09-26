import { useEffect, useRef, useState } from 'react';

/** Returns true if the user prefers reduced motion */
export function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e: MediaQueryListEvent) => setPrefersReduced(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  return prefersReduced;
}

/** Smoothly animates a numeric value using requestAnimationFrame easing */
export function useAnimatedNumber(
  target: number,
  duration: number = 600
): number {
  const [current, setCurrent] = useState<number>(target);
  const reduced = useReducedMotion();
  const startRef = useRef<number>(current);
  const startTimeRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (reduced) {
      setCurrent(target);
      return;
    }

    const from = startRef.current;
    startTimeRef.current = null;

    const animate = (time: number) => {
      if (!startTimeRef.current) startTimeRef.current = time;
      const elapsed = time - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = from + (target - from) * eased;
      setCurrent(value);
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        startRef.current = target;
      }
    };

    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration, reduced]);

  return current;
}

/** Formats a number using Indian locale (lakhs/crores) */
export function formatIndian(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Formats volume in Indian units (K, L, Cr) */
export function formatVolume(value: number): string {
  if (value >= 1e7) return `${(value / 1e7).toFixed(2)} Cr`;
  if (value >= 1e5) return `${(value / 1e5).toFixed(1)} L`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(0)} K`;
  return value.toFixed(0);
}
