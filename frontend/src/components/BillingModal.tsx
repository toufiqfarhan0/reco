"use client";

import React, { useState } from "react";
import {
  Check,
  CreditCard,
  ExternalLink,
  Sparkles,
  X,
  Copy,
  CheckCheck,
  ShieldCheck,
  Database,
  Zap,
  Activity,
  AlertCircle,
  Loader2,
} from "lucide-react";

export interface BillingModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentTier?: "free" | "pro";
  onTierChange?: (tier: "free" | "pro") => void;
  userId?: string;
}

export const BillingModal: React.FC<BillingModalProps> = ({
  isOpen,
  onClose,
  currentTier = "free",
  onTierChange,
  userId = "usr_demo",
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState<"checkout" | "portal" | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successUrl, setSuccessUrl] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  // Handler for Upgrade to Pro (POST /billing/checkout)
  const handleUpgradeToPro = async () => {
    setIsLoading(true);
    setLoadingAction("checkout");
    setErrorMessage(null);
    setSuccessUrl(null);

    try {
      const response = await fetch("/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          product_id: "prod_pro_monthly",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || "Failed to generate checkout session");
      }

      if (data.checkout_url) {
        setSuccessUrl(data.checkout_url);
        // Open checkout session in a new tab
        window.open(data.checkout_url, "_blank", "noopener,noreferrer");
        onTierChange?.("pro");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Network error contacting Dodo Payments.");
    } finally {
      setIsLoading(false);
      setLoadingAction(null);
    }
  };

  // Handler for Manage Subscription (POST /billing/portal)
  const handleManageSubscription = async () => {
    setIsLoading(true);
    setLoadingAction("portal");
    setErrorMessage(null);
    setSuccessUrl(null);

    try {
      const response = await fetch("/billing/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || "Failed to open customer portal");
      }

      if (data.portal_url) {
        setSuccessUrl(data.portal_url);
        window.open(data.portal_url, "_blank", "noopener,noreferrer");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Network error contacting customer portal.");
    } finally {
      setIsLoading(false);
      setLoadingAction(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-slate-950/80 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="billing-modal-title"
    >
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden text-slate-100 my-8">
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="billing-modal-title" className="text-lg font-semibold tracking-tight text-white">
                  Dodo Payments Monetization & Tiers
                </h2>
                <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-[11px] font-mono text-cyan-400 ring-1 ring-cyan-500/30">
                  Track 1
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Non-blocking hosted billing, customer portal & cloud entitlement sync
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            aria-label="Close billing modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Test Mode Judge Credentials Callout Pill */}
        <div className="mx-6 mt-6 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 rounded-md bg-amber-500/20 p-1 text-amber-400">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-amber-400/20 px-1.5 py-0.5 text-[11px] font-mono font-bold tracking-wide text-amber-300">
                    TEST MODE ACTIVE
                  </span>
                  <span className="text-xs font-medium text-amber-200">
                    Judges & Evaluators Sandbox
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-300">
                  Zero real charges. Use simulated test card details below during Dodo hosted checkout.
                </p>
              </div>
            </div>

            {/* Test Card Quick Reference Box */}
            <div className="flex flex-wrap items-center gap-2 text-xs font-mono bg-slate-950/70 border border-slate-800 rounded-lg p-2 text-slate-300">
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400">Card:</span>
                <span className="text-cyan-300 font-semibold">4242 4242 4242 4242</span>
                <button
                  type="button"
                  onClick={() => copyToClipboard("4242424242424242", "card")}
                  className="p-1 hover:text-white transition-colors cursor-pointer"
                  title="Copy card number"
                  aria-label="Copy card number"
                >
                  {copiedField === "card" ? (
                    <CheckCheck className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
              <span className="text-slate-600">|</span>
              <div className="flex items-center gap-1">
                <span className="text-slate-400">Exp:</span>
                <span className="text-slate-200">12/28</span>
              </div>
              <span className="text-slate-600">|</span>
              <div className="flex items-center gap-1">
                <span className="text-slate-400">CVC:</span>
                <span className="text-slate-200">123</span>
              </div>
              <span className="text-slate-600">|</span>
              <div className="flex items-center gap-1">
                <span className="text-slate-400">ZIP:</span>
                <span className="text-slate-200">90210</span>
              </div>
            </div>
          </div>
        </div>

        {/* Error / Success Feedback Banner */}
        {errorMessage && (
          <div className="mx-6 mt-4 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-xs text-red-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
            <span className="flex-1">{errorMessage}</span>
          </div>
        )}

        {successUrl && (
          <div className="mx-6 mt-4 flex items-center justify-between rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-xs text-emerald-300">
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 shrink-0 text-emerald-400" />
              <span>Dodo Payments session generated successfully.</span>
            </div>
            <a
              href={successUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 font-semibold underline hover:text-white"
            >
              Open Link <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        )}

        {/* 2-Tier Pricing Comparison Grid (High Visual Contrast) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
          {/* Tier 1: Free Tier */}
          <div
            className={`relative flex flex-col justify-between rounded-xl border p-6 transition-all ${
              currentTier === "free"
                ? "border-slate-700 bg-slate-950/80 ring-1 ring-slate-700 shadow-md"
                : "border-slate-800 bg-slate-950/40 opacity-90"
            }`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Free Tier
                </span>
                {currentTier === "free" && (
                  <span className="rounded-full bg-slate-800 border border-slate-700 px-2.5 py-0.5 text-[11px] font-mono text-slate-300">
                    CURRENT PLAN
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-white tracking-tight">$0</span>
                <span className="text-xs text-slate-400">/ forever</span>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Full console access with local in-memory storage. 100% non-blocking.
              </p>

              {/* Free Features List */}
              <ul className="mt-6 space-y-3 text-xs text-slate-300">
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-slate-800 p-0.5 text-slate-400">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">5 daily optimizations</strong> for DAG mutations
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-slate-800 p-0.5 text-slate-400">
                    <Database className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">Local in-memory storage</strong> ($0 setup friction)
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-slate-800 p-0.5 text-slate-400">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">Community support</strong> & open docs
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-slate-800 p-0.5 text-slate-400">
                    <Activity className="h-3.5 w-3.5" />
                  </div>
                  <span>4-axis benchmark scoring & 12-category diagnostics</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 pt-4 border-t border-slate-800/80">
              <button
                type="button"
                onClick={() => {
                  onTierChange?.("free");
                }}
                disabled={currentTier === "free"}
                className={`w-full rounded-lg px-4 py-2.5 text-xs font-semibold transition-all cursor-pointer ${
                  currentTier === "free"
                    ? "bg-slate-800/70 text-slate-400 border border-slate-700/50 cursor-default"
                    : "border border-slate-700 bg-slate-800 text-white hover:bg-slate-700"
                }`}
              >
                {currentTier === "free" ? "Active Plan" : "Switch to Free Tier"}
              </button>
            </div>
          </div>

          {/* Tier 2: Pro Tier ($29/mo) with High Contrast Glow */}
          <div
            className={`relative flex flex-col justify-between rounded-xl border p-6 transition-all ${
              currentTier === "pro"
                ? "border-cyan-500 bg-gradient-to-b from-cyan-950/40 via-slate-900 to-slate-950 ring-2 ring-cyan-500/40 shadow-cyan-950/50 shadow-xl"
                : "border-cyan-500/40 bg-gradient-to-b from-cyan-950/20 via-slate-900 to-slate-950 hover:border-cyan-500/70 shadow-lg"
            }`}
          >
            {/* Top Ribbon */}
            <div className="absolute -top-3 right-6">
              <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500 px-3 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-950 shadow-md">
                <Sparkles className="h-3 w-3" /> Recommended
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                  <Zap className="h-4 w-4" /> Pro Tier
                </span>
                {currentTier === "pro" && (
                  <span className="rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2.5 py-0.5 text-[11px] font-mono font-semibold text-emerald-400">
                    ACTIVE
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-white tracking-tight">$29</span>
                <span className="text-xs text-slate-400">/ month</span>
              </div>
              <p className="mt-2 text-xs text-cyan-200/80">
                Production-grade autonomous loop with Supabase cloud persistence & Neatlogs tracing.
              </p>

              {/* Pro Features List */}
              <ul className="mt-6 space-y-3 text-xs text-slate-200">
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-cyan-500/20 p-0.5 text-cyan-400 ring-1 ring-cyan-500/30">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">Unlimited autonomous mutations</strong> & tournaments
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-cyan-500/20 p-0.5 text-cyan-400 ring-1 ring-cyan-500/30">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">Full Supabase cloud lineage sync</strong> with RLS
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-cyan-500/20 p-0.5 text-cyan-400 ring-1 ring-cyan-500/30">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">Neatlogs distributed trace export</strong> & telemetry
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-cyan-500/20 p-0.5 text-cyan-400 ring-1 ring-cyan-500/30">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-white">Priority inference</strong> on TensorMux GLM-4.7-Flash
                  </span>
                </li>
              </ul>
            </div>

            {/* Interactive Actions */}
            <div className="mt-8 pt-4 border-t border-cyan-500/20 flex flex-col gap-2">
              <button
                type="button"
                onClick={handleUpgradeToPro}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-emerald-500 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-md hover:from-cyan-400 hover:to-emerald-400 transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoading && loadingAction === "checkout" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Launching Dodo Checkout...
                  </>
                ) : (
                  <>
                    <CreditCard className="h-4 w-4" />
                    Upgrade to Pro ($29/mo)
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleManageSubscription}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer disabled:opacity-50"
              >
                {isLoading && loadingAction === "portal" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading Portal...
                  </>
                ) : (
                  <>
                    <ExternalLink className="h-3.5 w-3.5" />
                    Manage Subscription
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer / Demo Gating Info */}
        <div className="border-t border-slate-800 bg-slate-950/80 px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <span className="text-emerald-400">●</span>
            <span>NON-BLOCKING CONSOLE: Core synthesis & benchmarks remain 100% accessible</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const nextTier = currentTier === "pro" ? "free" : "pro";
                onTierChange?.(nextTier);
              }}
              className="text-cyan-400 hover:underline cursor-pointer"
            >
              [Simulate Toggle: {currentTier === "pro" ? "Free" : "Pro"}]
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={onClose}
              className="text-slate-300 hover:text-white cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
