import React, { useEffect, useCallback } from 'react';
import { Command } from 'cmdk';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Compass, BarChart3, Layers, Box, FileCheck, Server,
  Keyboard, ArrowRight, TrendingUp, Newspaper,
} from 'lucide-react';
import type { NavTab } from '../layout/Navigation';

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (tab: NavTab) => void;
  activeTab: NavTab;
}

const NAV_ITEMS: { id: NavTab; label: string; description: string; icon: React.ElementType; shortcut: string }[] = [
  { id: 'overview', label: 'Home Dashboard', description: 'Executive market overview & index breadth', icon: Compass, shortcut: '1' },
  { id: 'trading', label: 'Trading Terminal', description: 'Pro candlestick chart & real-time execution', icon: TrendingUp, shortcut: '2' },
  { id: 'options', label: 'Options Chain', description: 'NSE strike matrix, Greeks & strategy payoff', icon: Layers, shortcut: '3' },
  { id: 'ai-analyst', label: 'AI Intelligence', description: 'Explainable AI research analyst & reports', icon: Compass, shortcut: '4' },
  { id: 'strategy-lab', label: 'Quant Lab', description: 'Strategy builder & backtesting engine', icon: Box, shortcut: '5' },
  { id: 'screener', label: 'Screener & Heatmap', description: 'Momentum stock screener & sector heatmap', icon: BarChart3, shortcut: '6' },
  { id: 'portfolio', label: 'Portfolio & Risk', description: 'Holdings, P&L & sector allocation', icon: FileCheck, shortcut: '7' },
  { id: 'technical', label: 'Company Research', description: 'Financial statements & valuation ratios', icon: Server, shortcut: '8' },
  { id: 'news', label: 'News & Economic Calendar', description: 'Breaking news feeds & macro announcements', icon: Newspaper, shortcut: '9' },
  { id: 'positions', label: 'Orders & Execution', description: 'Order book, fills & paper trading audit', icon: FileCheck, shortcut: '0' },
  { id: 'settings', label: 'Settings & Brokers', description: 'Zerodha/Angel/Dhan API keys & risk safeguards', icon: Server, shortcut: 'S' },
];

export const CommandPalette: React.FC<CommandPaletteProps> = ({ open, onClose, onNavigate, activeTab }) => {
  const handleSelect = useCallback((tab: NavTab) => {
    onNavigate(tab);
    onClose();
  }, [onNavigate, onClose]);

  // Close on Escape
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            cmdk-overlay=""
          />

          {/* Dialog */}
          <div cmdk-dialog="">
            <motion.div
              initial={{ opacity: 0, scale: 0.94, y: -12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.94, y: -12 }}
              transition={{ type: 'spring', stiffness: 500, damping: 36 }}
            >
              <Command label="Navigation" cmdk-root="" shouldFilter={true}>
                <div style={{ position: 'relative' }}>
                  <Command.Input
                    cmdk-input=""
                    placeholder="Navigate to a view or search..."
                    autoFocus
                  />
                  <div style={{
                    position: 'absolute',
                    right: 16,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}>
                    <kbd style={{
                      padding: '2px 6px',
                      borderRadius: 4,
                      background: 'var(--z5)',
                      border: '1px solid var(--border-1)',
                      fontSize: 10,
                      fontFamily: 'JetBrains Mono, monospace',
                      color: 'var(--text-muted)',
                    }}>ESC</kbd>
                  </div>
                </div>

                <Command.List cmdk-list="">
                  <Command.Empty cmdk-empty="">No results found.</Command.Empty>

                  <Command.Group heading="Views" cmdk-group-heading="">
                    {NAV_ITEMS.map((item) => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;
                      return (
                        <Command.Item
                          key={item.id}
                          value={`${item.label} ${item.description}`}
                          onSelect={() => handleSelect(item.id)}
                          cmdk-item=""
                          data-selected={isActive ? 'true' : undefined}
                        >
                          <div style={{
                            width: 32,
                            height: 32,
                            borderRadius: 8,
                            background: isActive ? 'var(--gold-glow)' : 'var(--z5)',
                            border: `1px solid ${isActive ? 'var(--border-gold)' : 'var(--border-1)'}`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <Icon
                              style={{
                                width: 14,
                                height: 14,
                                color: isActive ? 'var(--gold-primary)' : 'var(--text-muted)',
                              }}
                            />
                          </div>

                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 13, color: isActive ? 'var(--gold-primary)' : 'var(--text-primary)', fontWeight: 500 }}>
                              {item.label}
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
                              {item.description}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            {isActive && (
                              <span style={{
                                fontSize: 9,
                                fontFamily: 'JetBrains Mono, monospace',
                                color: 'var(--gold-primary)',
                                background: 'var(--gold-glow)',
                                padding: '2px 6px',
                                borderRadius: 4,
                                border: '1px solid var(--border-gold)',
                                letterSpacing: '0.05em',
                              }}>ACTIVE</span>
                            )}
                            <kbd style={{
                              padding: '2px 6px',
                              borderRadius: 4,
                              background: 'var(--z5)',
                              border: '1px solid var(--border-1)',
                              fontSize: 10,
                              fontFamily: 'JetBrains Mono, monospace',
                              color: 'var(--text-muted)',
                            }}>{item.shortcut}</kbd>
                          </div>
                        </Command.Item>
                      );
                    })}
                  </Command.Group>

                  <Command.Group heading="Keyboard Shortcuts" cmdk-group-heading="">
                    <Command.Item value="keyboard shortcuts help" cmdk-item="" disabled>
                      <Keyboard style={{ width: 14, height: 14, color: 'var(--text-muted)', flexShrink: 0 }} />
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        Press <kbd style={{ padding: '1px 5px', borderRadius: 3, background: 'var(--z5)', border: '1px solid var(--border-1)', fontSize: 10 }}>⌘K</kbd> to open •
                        Keys <kbd style={{ padding: '1px 5px', borderRadius: 3, background: 'var(--z5)', border: '1px solid var(--border-1)', fontSize: 10 }}>1–6</kbd> to switch tabs
                      </span>
                    </Command.Item>
                  </Command.Group>
                </Command.List>
              </Command>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
};
