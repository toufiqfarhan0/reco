"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import {
  signInWithPassword,
  signUp,
  signInAsEvaluator,
} from "@/lib/supabaseClient";
import {
  EnvelopeSimple,
  LockKey,
  Lightning,
  X,
  User,
  ShieldCheck,
  CircleNotch,
} from "@phosphor-icons/react";

export interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess?: (user: any, token: string) => void;
  onSuccess?: (user: any, token?: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onAuthSuccess,
  onSuccess,
}) => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isSignUp) {
        const { data, error: signUpError } = await signUp(
          email,
          password,
          displayName
        );
        if (signUpError) throw signUpError;
        if (data?.user) {
          onAuthSuccess?.(data.user, data.session?.access_token || "");
          onSuccess?.(data.user, data.session?.access_token || "");
        }
        onClose();
      } else {
        const { data, error: signInError } = await signInWithPassword(
          email,
          password
        );
        if (signInError) throw signInError;
        if (data?.user) {
          onAuthSuccess?.(data.user, data.session?.access_token || "");
          onSuccess?.(data.user, data.session?.access_token || "");
        }
        onClose();
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluatorSignIn = () => {
    setError(null);
    try {
      const { user, session } = signInAsEvaluator();
      onAuthSuccess?.(user, session.access_token);
      onSuccess?.(user, session.access_token);
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to sign in as evaluator.");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-900/30 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      data-testid="auth-modal"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 8 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="relative w-full max-w-md rounded-2xl border border-zinc-200 bg-white/90 backdrop-blur-md p-6 shadow-2xl text-zinc-900"
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-xl p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-900 transition-colors cursor-pointer"
          aria-label="Close modal"
        >
          <X size={18} weight="bold" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 border-b border-zinc-100 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100 shadow-2xs">
            <ShieldCheck size={22} weight="duotone" />
          </div>
          <div>
            <h2 id="auth-modal-title" className="text-base font-bold tracking-tight text-zinc-950 font-geist">
              {isSignUp ? "Create Engineer Account" : "Sign In to Reco"}
            </h2>
            <p className="text-xs text-zinc-500 font-geist">
              Supabase Cloud Lineage & Tournament Sync
            </p>
          </div>
        </div>

        {/* 1-Click Judge/Evaluator Access Button */}
        <div className="mt-5 rounded-xl border border-indigo-100 bg-indigo-50/50 p-3.5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-indigo-800">
              Evaluator Quick Access
            </span>
            <span className="rounded-md bg-indigo-100 px-1.5 py-0.5 text-[10px] font-mono font-bold text-indigo-700">
              Instant
            </span>
          </div>
          <button
            type="button"
            onClick={handleEvaluatorSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 active:scale-[0.98] py-2.5 px-4 text-xs font-semibold text-white transition-all cursor-pointer disabled:opacity-50 shadow-xs font-geist"
            data-testid="auth-evaluator-signin"
          >
            <Lightning size={16} weight="fill" className="text-amber-400" />
            <span>Judge / Evaluator Demo Sign In</span>
          </button>
        </div>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-zinc-200" />
          </div>
          <div className="relative flex justify-center text-[10px] uppercase font-mono">
            <span className="bg-white/90 px-2 text-zinc-400">Or with email</span>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-700 font-geist">
            {error}
          </div>
        )}

        {/* Form Inputs with Clean Icons Inside */}
        <form onSubmit={handleSubmit} className="space-y-3">
          {isSignUp && (
            <div className="space-y-1">
              <label className="text-xs font-medium text-zinc-700 font-geist">
                Display Name
              </label>
              <div className="relative">
                <User size={16} className="absolute left-3.5 top-3 text-zinc-400" />
                <input
                  type="text"
                  required={isSignUp}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Ada Lovelace"
                  className="w-full rounded-xl border border-zinc-200 bg-white py-2.5 pl-10 pr-3 text-xs text-zinc-900 placeholder-zinc-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors shadow-2xs font-geist"
                  data-testid="auth-displayname-input"
                />
              </div>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-700 font-geist">
              Email Address
            </label>
            <div className="relative">
              <EnvelopeSimple size={16} className="absolute left-3.5 top-3 text-zinc-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="engineer@reco.internal"
                className="w-full rounded-xl border border-zinc-200 bg-white py-2.5 pl-10 pr-3 text-xs text-zinc-900 placeholder-zinc-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors shadow-2xs font-mono"
                data-testid="auth-email-input"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-zinc-700 font-geist">
              Password
            </label>
            <div className="relative">
              <LockKey size={16} className="absolute left-3.5 top-3 text-zinc-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-zinc-200 bg-white py-2.5 pl-10 pr-3 text-xs text-zinc-900 placeholder-zinc-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors shadow-2xs font-mono"
                data-testid="auth-password-input"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] py-2.5 px-4 text-xs font-semibold text-white transition-all cursor-pointer disabled:opacity-50 shadow-xs font-geist flex items-center justify-center gap-2"
            data-testid="auth-submit-button"
          >
            {loading ? (
              <CircleNotch size={16} className="animate-spin text-white" />
            ) : isSignUp ? (
              "Create Account"
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        {/* Toggle Mode */}
        <div className="mt-4 text-center border-t border-zinc-100 pt-3 text-xs font-geist">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
            }}
            className="text-indigo-600 font-medium hover:underline cursor-pointer"
            data-testid="auth-toggle-mode"
          >
            {isSignUp
              ? "Already have an account? Sign In"
              : "Need an account? Create Engineer Account"}
          </button>
        </div>
      </motion.div>
    </div>
  );
};
