import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type ExperienceLevel = 'BEGINNER' | 'PRO' | 'QUANT';

export interface TraderUser {
  id: string;
  username: string;
  fullName: string;
  email: string;
  avatar: string;
  experienceLevel: ExperienceLevel;
  startingCapital: number;
  createdAt: string;
  lastLogin: string;
}

interface AuthContextType {
  user: TraderUser | null;
  isAuthenticated: boolean;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
  login: (usernameOrEmail: string, password?: string) => Promise<{ success: boolean; message: string }>;
  register: (data: {
    fullName: string;
    username: string;
    email: string;
    password?: string;
    startingCapital: number;
    experienceLevel: ExperienceLevel;
  }) => Promise<{ success: boolean; message: string }>;
  loginAsDemo: (profileType: 'beginner' | 'pro' | 'quant') => void;
  logout: () => void;
  updateExperienceLevel: (level: ExperienceLevel) => void;
}

const STORAGE_AUTH_KEY = 'indian_stock_market_ai_trader_auth_v2';

const DEMO_PROFILES: Record<'beginner' | 'pro' | 'quant', TraderUser> = {
  beginner: {
    id: 'demo-beginner-001',
    username: 'priyatrader',
    fullName: 'Priya Patel',
    email: 'priya.investor@gmail.com',
    avatar: '👩‍💼',
    experienceLevel: 'BEGINNER',
    startingCapital: 500000,
    createdAt: '2026-01-15T09:15:00.000Z',
    lastLogin: new Date().toISOString(),
  },
  pro: {
    id: 'demo-pro-002',
    username: 'rahul_alpha',
    fullName: 'Rahul Sharma',
    email: 'rahul.alpha@trader.in',
    avatar: '👨‍💻',
    experienceLevel: 'PRO',
    startingCapital: 1000000,
    createdAt: '2025-08-10T09:15:00.000Z',
    lastLogin: new Date().toISOString(),
  },
  quant: {
    id: 'demo-quant-003',
    username: 'dr_vikram',
    fullName: 'Dr. Vikram Sen',
    email: 'vikram.sen@quantlab.ai',
    avatar: '🧠',
    experienceLevel: 'QUANT',
    startingCapital: 5000000,
    createdAt: '2025-02-01T09:15:00.000Z',
    lastLogin: new Date().toISOString(),
  },
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<TraderUser | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(STORAGE_AUTH_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.username) return parsed;
        }
      } catch (err) {
        console.warn('Failed to parse saved auth state:', err);
      }
    }
    // Default to Rahul Sharma (Pro) so users start with a fully initialized trader profile
    return DEMO_PROFILES.pro;
  });

  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        if (user) {
          localStorage.setItem(STORAGE_AUTH_KEY, JSON.stringify(user));
        } else {
          localStorage.removeItem(STORAGE_AUTH_KEY);
        }
      } catch (err) {
        console.error('Failed to save auth state:', err);
      }
    }
  }, [user]);

  const openAuthModal = () => setIsAuthModalOpen(true);
  const closeAuthModal = () => setIsAuthModalOpen(false);

  const login = async (usernameOrEmail: string, _password?: string): Promise<{ success: boolean; message: string }> => {
    // Client-side instant authentication
    const trimmed = usernameOrEmail.trim().toLowerCase();
    let matchedUser: TraderUser;

    if (trimmed.includes('priya') || trimmed.includes('begin')) {
      matchedUser = { ...DEMO_PROFILES.beginner, lastLogin: new Date().toISOString() };
    } else if (trimmed.includes('vikram') || trimmed.includes('quant')) {
      matchedUser = { ...DEMO_PROFILES.quant, lastLogin: new Date().toISOString() };
    } else {
      matchedUser = {
        id: `user-${Date.now()}`,
        username: usernameOrEmail.trim(),
        fullName: usernameOrEmail.includes('@') ? usernameOrEmail.split('@')[0] : usernameOrEmail,
        email: usernameOrEmail.includes('@') ? usernameOrEmail : `${usernameOrEmail}@trader.ai`,
        avatar: '⚡',
        experienceLevel: 'PRO',
        startingCapital: 1000000,
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
      };
    }

    setUser(matchedUser);
    setIsAuthModalOpen(false);
    return { success: true, message: `Welcome back, ${matchedUser.fullName}!` };
  };

  const register = async (data: {
    fullName: string;
    username: string;
    email: string;
    password?: string;
    startingCapital: number;
    experienceLevel: ExperienceLevel;
  }): Promise<{ success: boolean; message: string }> => {
    const newUser: TraderUser = {
      id: `trader-${Date.now()}`,
      username: data.username.trim(),
      fullName: data.fullName.trim(),
      email: data.email.trim(),
      avatar: data.experienceLevel === 'BEGINNER' ? '🔰' : data.experienceLevel === 'QUANT' ? '🧠' : '⚡',
      experienceLevel: data.experienceLevel,
      startingCapital: data.startingCapital || 1000000,
      createdAt: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
    };

    setUser(newUser);
    setIsAuthModalOpen(false);
    return { success: true, message: `Account created successfully for ${newUser.fullName}!` };
  };

  const loginAsDemo = (profileType: 'beginner' | 'pro' | 'quant') => {
    const profile = { ...DEMO_PROFILES[profileType], lastLogin: new Date().toISOString() };
    setUser(profile);
    setIsAuthModalOpen(false);
  };

  const logout = () => {
    setUser(null);
  };

  const updateExperienceLevel = (level: ExperienceLevel) => {
    if (user) {
      setUser({ ...user, experienceLevel: level });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isAuthModalOpen,
        openAuthModal,
        closeAuthModal,
        login,
        register,
        loginAsDemo,
        logout,
        updateExperienceLevel,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
