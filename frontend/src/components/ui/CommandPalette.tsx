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
  { id: 'trading', label: 'Derivatives Terminal & P&L', description: 'Options execution terminal & portfolio P&L', icon: TrendingUp, shortcut: '1' },
  { id: 'options', label: 'Options Chain', description: 'Full options chain & Black-76 matrix', icon: Layers, shortcut: '2' },
  { id: 'news', label: 'Live Financial News & Sentiment', description: 'Real-time breaking market headlines & AI sentiment', icon: Newspaper, shortcut: '3' },
  { id: 'markets', label: 'Markets', description: 'NIFTY & BANKNIFTY terminal', icon: BarChart3, shortcut: '4' },
  { id: 'overview', label: 'Overview', description: 'Executive command flagship', icon: Compass, shortcut: '5' },
  { id: 'volatility', label: '3D Volatility Studio', description: 'IV surface & OI landscape', icon: Box, shortcut: '6' },
  { id: 'research', label: 'Research Governance', description: 'Hypothesis registry & audit', icon: FileCheck, shortcut: '7' },
  { id: 'data-health', label: 'Data Health', description: 'Provider topology & coverage', icon: Server, shortcut: '8' },
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
