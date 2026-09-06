import React, { useState } from "react";
import { Lock, Mail, User, X, AlertCircle, CheckCircle2, ArrowRight, Sparkles, ShieldCheck, Loader2 } from "lucide-react";
import { signInWithPassword, signUp, signInAsEvaluator } from "@/lib/supabaseClient";

export interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (user: any, token?: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onAuthSuccess }) => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (isSignUp) {
        const { data, error: signUpErr } = await signUp(email, password, displayName);
        if (signUpErr) throw signUpErr;

        if (data?.user) {
          setSuccessMsg("Account created successfully!");
          onAuthSuccess(data.user, data.session?.access_token);
          setTimeout(() => {
            onClose();
          }, 800);
        }
      } else {
        const { data, error: signInErr } = await signInWithPassword(email, password);
        if (signInErr) throw signInErr;

        if (data?.user) {
          setSuccessMsg("Signed in successfully!");
          onAuthSuccess(data.user, data.session?.access_token);
          setTimeout(() => {
            onClose();
          }, 600);
        }
      }
    } catch (err: any) {
      setError(err?.message || "Authentication failed. Please check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluatorSignIn = () => {
    setError(null);
    setLoading(true);
    try {
      const { user, session } = signInAsEvaluator();
      setSuccessMsg("Evaluator demo session activated!");
      onAuthSuccess(user, session.access_token);
      setTimeout(() => {
        setLoading(false);
        onClose();
      }, 500);
    } catch (err: any) {
      setError(err?.message || "Failed to initialize evaluator session");
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
    >
      <div
        className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 md:p-8 relative overflow-hidden"
        data-testid="auth-modal"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold mb-1">
            <Lock className="w-3.5 h-3.5" />
            <span>Supabase Cloud Persistence</span>
          </div>
          <h2 id="auth-modal-title" className="text-xl font-bold text-white">
            {isSignUp ? "Create Engineer Account" : "Sign In to Reco"}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {isSignUp
              ? "Sign up to persist agent graph architectures, benchmark runs, and evolution histories."
              : "Access your persisted experiments, agent versions, and promotion lineages."}
          </p>
        </div>

        {/* 1-Click Judge / Evaluator Demo Sign In Button */}
        <div className="mb-5">
          <button
            type="button"
            onClick={handleEvaluatorSignIn}
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-indigo-500/20 hover:from-emerald-500/30 hover:via-cyan-500/30 hover:to-indigo-500/30 border border-emerald-500/40 hover:border-emerald-400 text-emerald-300 font-mono text-xs font-bold transition flex items-center justify-center gap-2 group cursor-pointer disabled:opacity-50"
            data-testid="auth-evaluator-signin"
            title="Instant 1-Click Evaluator Authentication for Hackathon Evaluation"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
            <span>Judge / Evaluator Demo Sign In (1-Click)</span>
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
          </button>
        </div>

        <div className="relative flex py-2 items-center mb-4">
          <div className="flex-grow border-t border-slate-800"></div>
          <span className="flex-shrink mx-3 text-[10px] uppercase font-mono text-slate-500 tracking-wider">
            or email credentials
          </span>
          <div className="flex-grow border-t border-slate-800"></div>
        </div>

        {/* Error / Success Notifications */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-950/60 border border-emerald-800 text-xs text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignUp && (
            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1">
                Display Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Lead Agent Engineer"
                  className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                  data-testid="auth-displayname-input"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1">
              Email Address <span className="text-cyan-400">*</span>
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="engineer@domain.com"
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                data-testid="auth-email-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1">
              Password <span className="text-cyan-400">*</span>
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                data-testid="auth-password-input"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            data-testid="auth-submit-button"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Processing...</span>
              </span>
            ) : (
              <>
                <span>{isSignUp ? "Create Account" : "Sign In"}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Toggle */}
        <div className="mt-5 pt-4 border-t border-slate-800/80 text-center">
          <p className="text-xs text-slate-400">
            {isSignUp ? "Already have an account?" : "Don't have an account yet?"}{" "}
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setError(null);
              }}
              className="text-cyan-400 hover:text-cyan-300 font-bold ml-1 transition cursor-pointer"
              data-testid="auth-toggle-mode"
            >
              {isSignUp ? "Sign In" : "Sign Up"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
