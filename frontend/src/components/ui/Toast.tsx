import React, { createContext, useCallback, useContext, useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, WifiOff, Wifi, AlertTriangle, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextValue {
  addToast: (message: string, type?: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
  addToast: () => {},
  removeToast: () => {},
});

export const useToast = () => useContext(ToastContext);

const ICONS: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />,
  error: <WifiOff className="w-4 h-4 text-rose-400 shrink-0" />,
  info: <Wifi className="w-4 h-4 text-amber-400 shrink-0" />,
  warning: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
};

const BORDER_COLORS: Record<ToastType, string> = {
  success: 'rgba(16,185,129,0.35)',
  error: 'rgba(244,63,94,0.35)',
  info: 'rgba(212,175,55,0.35)',
  warning: 'rgba(251,191,36,0.35)',
};

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  useEffect(() => {
    const t = setTimeout(onRemove, toast.duration ?? 4000);
    return () => clearTimeout(t);
  }, [toast.duration, onRemove]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 48, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 48, scale: 0.9 }}
      transition={{ type: 'spring', stiffness: 420, damping: 32 }}
      className="toast"
      style={{ borderColor: BORDER_COLORS[toast.type] }}
    >
      {ICONS[toast.type]}
      <span style={{ fontSize: 13, flex: 1, fontFamily: 'Inter, sans-serif', color: 'var(--text-secondary)' }}>
        {toast.message}
      </span>
      <button
        onClick={onRemove}
        className="shrink-0 text-slate-500 hover:text-slate-300 transition-colors ml-1"
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: ToastType = 'info', duration = 4000) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev.slice(-4), { id, type, message, duration }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div className="toast-container">
        <AnimatePresence mode="popLayout">
          {toasts.map(toast => (
            <ToastItem key={toast.id} toast={toast} onRemove={() => removeToast(toast.id)} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
