import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type LuxuryTheme = 'royal_gold' | 'obsidian_titanium' | 'emerald_sovereign';

interface ThemeConfig {
  id: LuxuryTheme;
  name: string;
  icon: string;
  tag: string;
  bgZ0: string;
  bgZ1: string;
  bgZ2: string;
  bgZ3: string;
  bgZ4: string;
  accentPrimary: string;
  accentSecondary: string;
  accentGlow: string;
  cardBorder: string;
  cardBorderHover: string;
  cardShadow: string;
}

export const THEME_CONFIGS: Record<LuxuryTheme, ThemeConfig> = {
  royal_gold: {
    id: 'royal_gold',
    name: 'Royal Champagne Gold',
    icon: '👑',
    tag: 'Sovereign VIP',
    bgZ0: '#07090e',
    bgZ1: '#0c101a',
    bgZ2: '#121724',
    bgZ3: '#181f30',
    bgZ4: '#202a40',
    accentPrimary: '#d4af37',
    accentSecondary: '#f59e0b',
    accentGlow: 'rgba(212, 175, 55, 0.25)',
    cardBorder: 'rgba(212, 175, 55, 0.22)',
    cardBorderHover: 'rgba(212, 175, 55, 0.55)',
    cardShadow: '0 12px 35px -5px rgba(0, 0, 0, 0.6), 0 0 25px rgba(212, 175, 55, 0.1)',
  },
  obsidian_titanium: {
    id: 'obsidian_titanium',
    name: 'Obsidian Titanium',
    icon: '⚡',
    tag: 'Institutional Pro',
    bgZ0: '#06080e',
    bgZ1: '#0b0f19',
    bgZ2: '#101522',
    bgZ3: '#161c2c',
    bgZ4: '#1d2538',
    accentPrimary: '#38bdf8',
    accentSecondary: '#818cf8',
    accentGlow: 'rgba(56, 189, 248, 0.22)',
    cardBorder: 'rgba(56, 189, 248, 0.18)',
    cardBorderHover: 'rgba(56, 189, 248, 0.45)',
    cardShadow: '0 12px 35px -5px rgba(0, 0, 0, 0.6), 0 0 25px rgba(56, 189, 248, 0.08)',
  },
  emerald_sovereign: {
    id: 'emerald_sovereign',
    name: 'Emerald Sovereign',
    icon: '💎',
    tag: 'Alpha Quant',
    bgZ0: '#05090a',
    bgZ1: '#091114',
    bgZ2: '#0e181c',
    bgZ3: '#142126',
    bgZ4: '#1b2c33',
    accentPrimary: '#10b981',
    accentSecondary: '#06b6d4',
    accentGlow: 'rgba(16, 185, 129, 0.25)',
    cardBorder: 'rgba(16, 185, 129, 0.2)',
    cardBorderHover: 'rgba(16, 185, 129, 0.5)',
    cardShadow: '0 12px 35px -5px rgba(0, 0, 0, 0.6), 0 0 25px rgba(16, 185, 129, 0.1)',
  },
};

interface ThemeContextType {
  theme: LuxuryTheme;
  themeConfig: ThemeConfig;
  setTheme: (theme: LuxuryTheme) => void;
  cycleTheme: () => void;
}

const STORAGE_THEME_KEY = 'indian_stock_market_ai_luxury_theme_v3';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<LuxuryTheme>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(STORAGE_THEME_KEY) as LuxuryTheme;
        if (saved && THEME_CONFIGS[saved]) return saved;
      } catch (err) {
        console.warn('Failed to parse saved theme:', err);
      }
    }
    // Default to Royal Champagne Gold (Executive Sovereign VIP)
    return 'royal_gold';
  });

  const themeConfig = THEME_CONFIGS[theme] || THEME_CONFIGS.royal_gold;

  const setTheme = (newTheme: LuxuryTheme) => {
    setThemeState(newTheme);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(STORAGE_THEME_KEY, newTheme);
      } catch (err) {
        console.error('Failed to save theme:', err);
      }
    }
  };

  const cycleTheme = () => {
    const keys: LuxuryTheme[] = ['royal_gold', 'obsidian_titanium', 'emerald_sovereign'];
    const nextIdx = (keys.indexOf(theme) + 1) % keys.length;
    setTheme(keys[nextIdx]);
  };

  // Synchronize CSS custom properties with selected theme
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    root.style.setProperty('--z0', themeConfig.bgZ0);
    root.style.setProperty('--z1', themeConfig.bgZ1);
    root.style.setProperty('--z2', themeConfig.bgZ2);
    root.style.setProperty('--z3', themeConfig.bgZ3);
    root.style.setProperty('--z4', themeConfig.bgZ4);
    root.style.setProperty('--accent-luxury', themeConfig.accentPrimary);
    root.style.setProperty('--accent-luxury-glow', themeConfig.accentGlow);
    root.style.setProperty('--card-border-luxury', themeConfig.cardBorder);
    root.style.setProperty('--card-shadow-luxury', themeConfig.cardShadow);
  }, [theme, themeConfig]);

  return (
    <ThemeContext.Provider value={{ theme, themeConfig, setTheme, cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
