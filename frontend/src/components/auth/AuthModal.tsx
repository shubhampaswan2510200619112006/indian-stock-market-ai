import React, { useState } from 'react';
import { useAuth, ExperienceLevel } from '../../context/AuthContext';
import { usePaperTrading } from '../../context/PaperTradingContext';
import { X, Lock, User, Mail, Shield, Zap, Sparkles, CheckCircle2, ArrowRight, DollarSign } from 'lucide-react';

export const AuthModal: React.FC = () => {
  const {
    user,
    isAuthenticated,
    isAuthModalOpen,
    closeAuthModal,
    login,
    register,
    loginAsDemo,
    logout,
  } = useAuth();

  const { account } = usePaperTrading();

  const [activeTab, setActiveTab] = useState<'signin' | 'demo' | 'register'>('demo');
  const [loginIdent, setLoginIdent] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Register Form State
  const [regFullName, setRegFullName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regCapital, setRegCapital] = useState<number>(1000000);
  const [regLevel, setRegLevel] = useState<ExperienceLevel>('BEGINNER');

  if (!isAuthModalOpen) return null;

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginIdent) {
      setErrorMsg('Please enter your username or email address');
      return;
    }
    setErrorMsg('');
    const res = await login(loginIdent, loginPassword);
    if (res.success) {
      setSuccessMsg(res.message);
      setTimeout(() => {
        setSuccessMsg('');
        closeAuthModal();
      }, 700);
    } else {
      setErrorMsg(res.message);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regFullName || !regUsername || !regEmail) {
      setErrorMsg('Please fill out all registration fields');
      return;
    }
    setErrorMsg('');
    const res = await register({
      fullName: regFullName,
      username: regUsername,
      email: regEmail,
      startingCapital: regCapital,
      experienceLevel: regLevel,
    });
    if (res.success) {
      setSuccessMsg(res.message);
      setTimeout(() => {
        setSuccessMsg('');
        closeAuthModal();
      }, 700);
    } else {
      setErrorMsg(res.message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-lg rounded-2xl bg-[#090e1a] border border-white/[0.14] shadow-2xl overflow-hidden"
        style={{
          boxShadow: '0 0 50px rgba(0, 245, 160, 0.08), 0 20px 40px rgba(0,0,0,0.8)',
        }}
      >
        {/* Top Glowing Header Strip */}
        <div className="relative px-6 pt-6 pb-4 border-b border-white/[0.08] bg-gradient-to-r from-[#0c1426] via-[#101b33] to-[#0c1426]">
          <button
            onClick={closeAuthModal}
            className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-cyan-500/20 to-emerald-500/20 border border-amber-400/40 flex items-center justify-center text-xl shadow-lg">
              {user ? user.avatar : '🏛️'}
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                {isAuthenticated ? 'Trader Profile & Account' : 'Indian Stock Market AI — Portal'}
              </h2>
              <p className="text-xs text-slate-400">
                {isAuthenticated
                  ? `Signed in as ${user?.fullName} (${user?.experienceLevel})`
                  : 'Institutional Grade Paper Trading & Options Terminal'}
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          {!isAuthenticated ? (
            <div className="flex items-center gap-2 mt-5">
              <button
                onClick={() => { setActiveTab('demo'); setErrorMsg(''); }}
                className={`flex-1 py-2 px-3 text-xs font-semibold rounded-lg transition-all ${
                  activeTab === 'demo'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                ⚡ 1-Click Demo Profiles
              </button>
              <button
                onClick={() => { setActiveTab('signin'); setErrorMsg(''); }}
                className={`flex-1 py-2 px-3 text-xs font-semibold rounded-lg transition-all ${
                  activeTab === 'signin'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                🔐 Sign In
              </button>
              <button
                onClick={() => { setActiveTab('register'); setErrorMsg(''); }}
                className={`flex-1 py-2 px-3 text-xs font-semibold rounded-lg transition-all ${
                  activeTab === 'register'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                📝 Register
              </button>
            </div>
          ) : (
            <div className="mt-4 flex items-center justify-between text-xs bg-slate-950/60 px-3 py-2 rounded-xl border border-white/[0.06]">
              <span className="text-slate-400">Active Capital:</span>
              <span className="font-mono font-bold text-emerald-400">
                ₹{account.available_balance.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
            </div>
          )}
        </div>

        {/* Content Body */}
        <div className="p-6">
          {errorMsg && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
              {errorMsg}
            </div>
          )}
          {successMsg && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* If already authenticated, show profile summary & quick switch */}
          {isAuthenticated && user ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-white/[0.08] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Username</span>
                  <span className="text-xs font-mono font-bold text-white">@{user.username}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Email</span>
                  <span className="text-xs font-mono text-slate-300">{user.email}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Experience Tier</span>
                  <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30">
                    {user.experienceLevel}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Starting Portfolio</span>
                  <span className="text-xs font-mono text-cyan-300">
                    ₹{user.startingCapital.toLocaleString('en-IN')}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Quick Switch Trader Profile:
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => loginAsDemo('beginner')}
                    className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/[0.08] text-center transition-all"
                  >
                    <div className="text-base mb-1">🔰</div>
                    <div className="text-[11px] font-bold text-slate-200">Beginner</div>
                    <div className="text-[9px] text-slate-400">Priya (₹5L)</div>
                  </button>

                  <button
                    onClick={() => loginAsDemo('pro')}
                    className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/[0.08] text-center transition-all"
                  >
                    <div className="text-base mb-1">⚡</div>
                    <div className="text-[11px] font-bold text-slate-200">Pro Trader</div>
                    <div className="text-[9px] text-slate-400">Rahul (₹10L)</div>
                  </button>

                  <button
                    onClick={() => loginAsDemo('quant')}
                    className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/[0.08] text-center transition-all"
                  >
                    <div className="text-base mb-1">🧠</div>
                    <div className="text-[11px] font-bold text-slate-200">Quant Lab</div>
                    <div className="text-[9px] text-slate-400">Dr. Vikram (₹50L)</div>
                  </button>
                </div>
              </div>

              <div className="pt-2 flex items-center gap-3">
                <button
                  onClick={logout}
                  className="w-full py-2.5 px-4 rounded-xl border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 font-semibold text-xs transition-colors"
                >
                  Sign Out
                </button>
                <button
                  onClick={closeAuthModal}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg transition-colors"
                >
                  Continue Trading
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* TAB 1: 1-Click Demo Profiles */}
              {activeTab === 'demo' && (
                <div className="space-y-4">
                  <p className="text-xs text-slate-400">
                    Jump right in with a pre-configured, funded virtual paper trading account:
                  </p>

                  <div className="space-y-2.5">
                    {/* Beginner Profile */}
                    <div
                      onClick={() => loginAsDemo('beginner')}
                      className="group p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/[0.08] hover:border-emerald-500/40 cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                          🔰
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">Beginner Investor</span>
                            <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-500/20 text-emerald-300 font-semibold">
                              Priya Patel
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Simplified 3-step trade wizard, educational guidance & ₹5,00,000 capital.
                          </p>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
                    </div>

                    {/* Pro Profile */}
                    <div
                      onClick={() => loginAsDemo('pro')}
                      className="group p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/[0.08] hover:border-amber-500/40 cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl p-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
                          ⚡
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">Pro Derivatives Trader</span>
                            <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-300 font-semibold">
                              Rahul Sharma
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Full Sensibull-style option chain, Greek analytics & ₹10,00,000 capital.
                          </p>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 group-hover:translate-x-1 transition-all" />
                    </div>

                    {/* Quant Profile */}
                    <div
                      onClick={() => loginAsDemo('quant')}
                      className="group p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-white/[0.08] hover:border-cyan-500/40 cursor-pointer transition-all flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                          🧠
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-white">Quant Fund Lab</span>
                            <span className="px-1.5 py-0.2 rounded text-[10px] bg-cyan-500/20 text-cyan-300 font-semibold">
                              Dr. Vikram Sen
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            3D Volatility surfaces, Markov regimes & ₹50,00,000 capital.
                          </p>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: Sign In */}
              {activeTab === 'signin' && (
                <form onSubmit={handleSignIn} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Username or Email Address
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                      <input
                        type="text"
                        value={loginIdent}
                        onChange={(e) => setLoginIdent(e.target.value)}
                        placeholder="e.g. rahul_trader or email@example.com"
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-white/[0.1] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Password (Optional for Paper Mode)
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                      <input
                        type="password"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-white/[0.1] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-lg transition-all"
                  >
                    🚀 Sign In to Trading Account
                  </button>
                </form>
              )}

              {/* TAB 3: Register */}
              {activeTab === 'register' && (
                <form onSubmit={handleRegister} className="space-y-3.5">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-medium text-slate-300 mb-1">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={regFullName}
                        onChange={(e) => setRegFullName(e.target.value)}
                        placeholder="e.g. Amit Verma"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/[0.1] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-slate-300 mb-1">
                        Username
                      </label>
                      <input
                        type="text"
                        value={regUsername}
                        onChange={(e) => setRegUsername(e.target.value)}
                        placeholder="amit_trader"
                        className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/[0.1] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-300 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="amit@gmail.com"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-white/[0.1] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-300 mb-1">
                      Starting Virtual Capital
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[500000, 1000000, 2500000].map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          onClick={() => setRegCapital(amt)}
                          className={`py-1.5 px-2 rounded-lg text-xs font-mono font-semibold transition-all ${
                            regCapital === amt
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50'
                              : 'bg-slate-950 text-slate-400 border border-white/[0.06]'
                          }`}
                        >
                          ₹{(amt / 100000).toFixed(0)} Lakhs
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-300 mb-1">
                      Experience Tier
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['BEGINNER', 'PRO', 'QUANT'] as ExperienceLevel[]).map((lvl) => (
                        <button
                          key={lvl}
                          type="button"
                          onClick={() => setRegLevel(lvl)}
                          className={`py-1.5 px-2 rounded-lg text-[11px] font-semibold transition-all ${
                            regLevel === lvl
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                              : 'bg-slate-950 text-slate-400 border border-white/[0.06]'
                          }`}
                        >
                          {lvl === 'BEGINNER' ? '🔰 Beginner' : lvl === 'PRO' ? '⚡ Pro' : '🧠 Quant'}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full mt-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-amber-500 hover:from-emerald-400 hover:to-amber-400 text-slate-950 font-bold text-xs shadow-lg transition-all"
                  >
                    ✨ Create Free Paper Trading Account
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
