import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth, ExperienceLevel } from '../../context/AuthContext';
import { CyberMarketBackground } from '../background/CyberMarketBackground';
import {
  Sparkles, Lock, User, Mail, ShieldCheck, ArrowRight,
  TrendingUp, CheckCircle, Zap, DollarSign, Activity
} from 'lucide-react';

export const LandingLoginPage: React.FC = () => {
  const { login, register, loginAsDemo } = useAuth();

  const [activeTab, setActiveTab] = useState<'demo' | 'signin' | 'register'>('demo');
  const [isLaunching, setIsLaunching] = useState(false);
  const [launchStep, setLaunchStep] = useState('');

  // Sign In State
  const [loginIdent, setLoginIdent] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register State
  const [regFullName, setRegFullName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regCapital, setRegCapital] = useState<number>(1000000);
  const [regLevel, setRegLevel] = useState<ExperienceLevel>('PRO');

  const [errorMsg, setErrorMsg] = useState('');

  const triggerLaunchAnimation = (callback: () => void) => {
    setIsLaunching(true);
    setErrorMsg('');
    setLaunchStep('Connecting to NSE Institutional Co-Location Gateway...');

    setTimeout(() => {
      setLaunchStep('Synthesizing Live Derivatives Matrix & Black-Scholes Greeks...');
    }, 400);

    setTimeout(() => {
      setLaunchStep('Calibrating AI Candlestick Recognition & ML Signals...');
    }, 800);

    setTimeout(() => {
      callback();
    }, 1200);
  };

  const handleDemoLaunch = (profile: 'pro' | 'beginner' | 'quant') => {
    triggerLaunchAnimation(() => {
      loginAsDemo(profile);
    });
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginIdent) {
      setErrorMsg('Please enter your username or email address.');
      return;
    }
    triggerLaunchAnimation(async () => {
      await login(loginIdent, loginPassword);
    });
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regFullName || !regUsername || !regEmail) {
      setErrorMsg('Please complete all registration fields.');
      return;
    }
    triggerLaunchAnimation(async () => {
      await register({
        fullName: regFullName,
        username: regUsername,
        email: regEmail,
        password: regPassword,
        startingCapital: regCapital,
        experienceLevel: regLevel,
      });
    });
  };

  return (
    <div className="min-h-screen w-full relative flex items-center justify-center p-4 overflow-hidden bg-[#070b14] text-white">
      {/* 1. Live Animated Stock Market Chart Canvas Background */}
      <CyberMarketBackground isLowPerf={false} />

      {/* 2. Ambient Cyber Grid & Glow Orbs */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-gradient-to-r from-cyan-500/10 via-[#B6FF5C]/15 to-emerald-500/10 blur-[130px] rounded-full" />
      </div>

      {/* 3. Launching Transition Screen */}
      <AnimatePresence>
        {isLaunching && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#070b14]/95 backdrop-blur-2xl text-center p-6"
          >
            <div className="relative mb-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-[#B6FF5C] via-cyan-400 to-emerald-400 p-[2px] animate-spin">
                <div className="w-full h-full bg-[#070b14] rounded-2xl" />
              </div>
              <Activity className="w-10 h-10 text-[#B6FF5C] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
            </div>

            <h2 className="text-2xl font-extrabold text-white mb-2 font-['Outfit'] tracking-wide">
              ENTERING INDIAN FINANCIAL TRADING AI
            </h2>
            <p className="text-cyan-300 font-mono text-sm max-w-md animate-pulse">
              {launchStep}
            </p>

            <div className="w-64 h-1.5 bg-white/10 rounded-full mt-6 overflow-hidden">
              <motion.div
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: 1.2, ease: 'easeInOut' }}
                className="h-full bg-gradient-to-r from-[#B6FF5C] to-cyan-400 rounded-full"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 4. Main Authentication Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative z-10 w-full max-w-xl bg-[#0b101d]/90 border border-white/[0.12] rounded-3xl p-6 sm:p-8 backdrop-blur-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8),0_0_40px_rgba(182,255,92,0.08)]"
      >
        {/* Top Branding */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#B6FF5C]/15 border border-[#B6FF5C]/40 text-[#B6FF5C] text-xs font-semibold tracking-wider uppercase mb-3 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#B6FF5C]" />
            <span>Autonomous Trading Intelligence</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white font-['Outfit']">
            Indian Financial Trading AI
          </h1>
          <p className="text-slate-400 text-xs sm:text-sm mt-1">
            Real-time derivatives strike matrix, automated AI patterns, and high-probability ML signals.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-3 gap-1 bg-[#060810] p-1.5 rounded-xl border border-white/[0.08] mb-6 text-xs font-semibold">
          <button
            type="button"
            onClick={() => { setActiveTab('demo'); setErrorMsg(''); }}
            className={`py-2 px-2 rounded-lg transition-all cursor-pointer ${
              activeTab === 'demo'
                ? 'bg-gradient-to-r from-[#B6FF5C] to-emerald-400 text-black font-extrabold shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            ⚡ Instant Demo
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('signin'); setErrorMsg(''); }}
            className={`py-2 px-2 rounded-lg transition-all cursor-pointer ${
              activeTab === 'signin'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-extrabold shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            🔑 Sign In
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('register'); setErrorMsg(''); }}
            className={`py-2 px-2 rounded-lg transition-all cursor-pointer ${
              activeTab === 'register'
                ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-extrabold shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            📝 Register
          </button>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs text-center font-medium">
            {errorMsg}
          </div>
        )}

        {/* TAB 1: 1-Click Instant Demo Access */}
        {activeTab === 'demo' && (
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-[#121929] to-[#18233a] border border-[#B6FF5C]/30 shadow-md">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-[#B6FF5C] uppercase tracking-wider font-mono">
                  Recommended Demo Profile
                </span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded font-bold">
                  Zero Real Money
                </span>
              </div>
              <div className="text-lg font-bold text-white mb-1">
                Executive VIP Trader (Rahul Sharma)
              </div>
              <p className="text-xs text-slate-300 mb-4">
                Instant access to full live option chain, real-time candlestick charts with AI patterns, and ₹10,00,000 demo trading margin.
              </p>

              <button
                type="button"
                onClick={() => handleDemoLaunch('pro')}
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-[#B6FF5C] via-emerald-300 to-[#B6FF5C] text-slate-950 font-black text-sm tracking-wide flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.99] transition-all shadow-[0_0_20px_rgba(182,255,92,0.3)] cursor-pointer"
              >
                <span>🚀 Launch Demo Desk (₹10,00,000 Capital)</span>
                <ArrowRight className="w-4 h-4 text-black" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <button
                type="button"
                onClick={() => handleDemoLaunch('beginner')}
                className="p-3 rounded-xl bg-[#090d16] border border-white/[0.08] hover:border-cyan-400/40 text-left transition-all cursor-pointer"
              >
                <div className="font-bold text-cyan-300 mb-0.5">🔰 Guided Beginner</div>
                <div className="text-[11px] text-slate-400">Priya Patel • ₹5,00,000</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoLaunch('quant')}
                className="p-3 rounded-xl bg-[#090d16] border border-white/[0.08] hover:border-purple-400/40 text-left transition-all cursor-pointer"
              >
                <div className="font-bold text-purple-300 mb-0.5">🧠 Quant Lab</div>
                <div className="text-[11px] text-slate-400">Dr. Vikram • ₹50,00,000</div>
              </button>
            </div>
          </div>
        )}

        {/* TAB 2: Sign In */}
        {activeTab === 'signin' && (
          <form onSubmit={handleSignIn} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Username or Email
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={loginIdent}
                  onChange={(e) => setLoginIdent(e.target.value)}
                  placeholder="e.g. rahul_alpha or your@email.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#060810] border border-white/[0.1] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#060810] border border-white/[0.1] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-extrabold text-sm tracking-wide flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.99] transition-all shadow-[0_0_20px_rgba(6,182,212,0.3)] cursor-pointer"
            >
              <span>Sign In & Enter Terminal</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        )}

        {/* TAB 3: Register */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegister} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  placeholder="e.g. Shubham Paswan"
                  className="w-full px-3.5 py-2 bg-[#060810] border border-white/[0.1] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={regUsername}
                  onChange={(e) => setRegUsername(e.target.value)}
                  placeholder="e.g. shubham_trader"
                  className="w-full px-3.5 py-2 bg-[#060810] border border-white/[0.1] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                placeholder="trader@indianmarket.ai"
                className="w-full px-3.5 py-2 bg-[#060810] border border-white/[0.1] rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Starting Virtual Funds
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[500000, 1000000, 2500000].map((cap) => (
                  <button
                    key={cap}
                    type="button"
                    onClick={() => setRegCapital(cap)}
                    className={`py-2 px-2 rounded-lg border text-xs font-bold transition-all cursor-pointer ${
                      regCapital === cap
                        ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 shadow-sm'
                        : 'bg-[#060810] border-white/[0.08] text-slate-400 hover:text-white'
                    }`}
                  >
                    ₹{(cap / 100000).toFixed(0)} Lakhs
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-extrabold text-sm tracking-wide flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.99] transition-all shadow-[0_0_20px_rgba(16,185,129,0.3)] cursor-pointer mt-2"
            >
              <span>Create Account & Start Trading</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        )}

        {/* Security & Regulatory Invariant Footer */}
        <div className="mt-6 pt-4 border-t border-white/[0.08] flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Simulated Paper Trading Practice Node</span>
          </div>
          <div className="font-mono text-slate-500">
            v18.0 AI Engine
          </div>
        </div>
      </motion.div>
    </div>
  );
};
