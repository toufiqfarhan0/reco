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
  productId?: string;
  token?: string;
  userEmail?: string;
}

export const BillingModal: React.FC<BillingModalProps> = ({
  isOpen,
  onClose,
  currentTier = "free",
  onTierChange,
  userId = "usr_demo",
  productId,
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
      const checkoutBody: Record<string, any> = {
        user_id: userId,
      };
      if (productId) {
        checkoutBody.product_id = productId;
      }

      const response = await fetch("/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(checkoutBody),
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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="billing-modal-title"
    >
      <div className="relative w-full max-w-4xl rounded-2xl border border-[#e4e4e3] bg-white shadow-xl overflow-hidden text-[#0a0a0a] my-8">
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-[#e4e4e3] px-6 py-4 bg-[#f9f9f8]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#f4f4f3] text-[#0a0a0a] border border-[#e4e4e3]">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="billing-modal-title" className="text-lg font-semibold tracking-tight text-[#0a0a0a]">
                  Dodo Payments Monetization & Tiers
                </h2>
                <span className="rounded-full bg-[#f4f4f3] px-2 py-0.5 text-[11px] font-mono text-[#525250] border border-[#e4e4e3]">
                  Track 1
                </span>
              </div>
              <p className="text-xs text-[#525250]">
                Non-blocking hosted billing, customer portal & cloud entitlement sync
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-[#525250] hover:bg-[#f4f4f3] hover:text-[#0a0a0a] transition-colors cursor-pointer"
            aria-label="Close billing modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Test Mode Judge Credentials Callout Pill */}
        <div className="mx-6 mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 rounded-md bg-amber-100 p-1 text-amber-700">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-amber-200/80 px-1.5 py-0.5 text-[11px] font-mono font-bold tracking-wide text-amber-900 border border-amber-300">
                    TEST MODE ACTIVE
                  </span>
                  <span className="text-xs font-medium text-amber-900">
                    Judges & Evaluators Sandbox
                  </span>
                </div>
                <p className="mt-1 text-xs text-amber-800">
                  Zero real charges. Use simulated test card details below during Dodo hosted checkout.
                </p>
              </div>
            </div>

            {/* Test Card Quick Reference Box */}
            <div className="flex flex-wrap items-center gap-2 text-xs font-mono bg-white border border-amber-200 rounded-lg p-2 text-[#0a0a0a]">
              <div className="flex items-center gap-1.5">
                <span className="text-[#8a8a88]">Card:</span>
                <span className="text-[#0a0a0a] font-semibold">4242 4242 4242 4242</span>
                <button
                  type="button"
                  onClick={() => copyToClipboard("4242424242424242", "card")}
                  className="p-1 text-[#525250] hover:text-[#0a0a0a] transition-colors cursor-pointer"
                  title="Copy card number"
                  aria-label="Copy card number"
                >
                  {copiedField === "card" ? (
                    <CheckCheck className="h-3.5 w-3.5 text-emerald-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
              <span className="text-[#d1d1cf]">|</span>
              <div className="flex items-center gap-1">
                <span className="text-[#8a8a88]">Exp:</span>
                <span className="text-[#0a0a0a]">12/28</span>
              </div>
              <span className="text-[#d1d1cf]">|</span>
              <div className="flex items-center gap-1">
                <span className="text-[#8a8a88]">CVC:</span>
                <span className="text-[#0a0a0a]">123</span>
              </div>
              <span className="text-[#d1d1cf]">|</span>
              <div className="flex items-center gap-1">
                <span className="text-[#8a8a88]">ZIP:</span>
                <span className="text-[#0a0a0a]">90210</span>
              </div>
            </div>
          </div>
        </div>

        {/* Error / Success Feedback Banner */}
        {errorMessage && (
          <div className="mx-6 mt-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-xs text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
            <span className="flex-1">{errorMessage}</span>
          </div>
        )}

        {successUrl && (
          <div className="mx-6 mt-4 flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs text-emerald-700">
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 shrink-0 text-emerald-600" />
              <span>Dodo Payments session generated successfully.</span>
            </div>
            <a
              href={successUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 font-semibold underline hover:text-[#0a0a0a]"
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
                ? "border-[#0a0a0a] bg-white ring-1 ring-[#0a0a0a] shadow-xs"
                : "border-[#e4e4e3] bg-[#f9f9f8]"
            }`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold uppercase tracking-wider text-[#525250]">
                  Free Tier
                </span>
                {currentTier === "free" && (
                  <span className="rounded-full bg-[#f4f4f3] border border-[#e4e4e3] px-2.5 py-0.5 text-[11px] font-mono text-[#525250]">
                    CURRENT PLAN
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-[#0a0a0a] tracking-tight">$0</span>
                <span className="text-xs text-[#8a8a88]">/ forever</span>
              </div>
              <p className="mt-2 text-xs text-[#525250]">
                Full console access with local in-memory storage. 100% non-blocking.
              </p>

              {/* Free Features List */}
              <ul className="mt-6 space-y-3 text-xs text-[#525250]">
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-[#f4f4f3] p-0.5 text-[#0a0a0a]">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">5 daily optimizations</strong> for DAG mutations
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-[#f4f4f3] p-0.5 text-[#0a0a0a]">
                    <Database className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">Local in-memory storage</strong> ($0 setup friction)
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-[#f4f4f3] p-0.5 text-[#0a0a0a]">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">Community support</strong> & open docs
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-[#f4f4f3] p-0.5 text-[#0a0a0a]">
                    <Activity className="h-3.5 w-3.5" />
                  </div>
                  <span>4-axis benchmark scoring & 12-category diagnostics</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 pt-4 border-t border-[#e4e4e3]">
              <button
                type="button"
                onClick={() => {
                  onTierChange?.("free");
                }}
                disabled={currentTier === "free"}
                className={`w-full rounded-lg px-4 py-2.5 text-xs font-semibold transition-all cursor-pointer ${
                  currentTier === "free"
                    ? "bg-[#f4f4f3] text-[#8a8a88] border border-[#e4e4e3] cursor-default"
                    : "border border-[#e4e4e3] bg-white text-[#0a0a0a] hover:bg-[#f4f4f3]"
                }`}
              >
                {currentTier === "free" ? "Active Plan" : "Switch to Free Tier"}
              </button>
            </div>
          </div>

          {/* Tier 2: Pro Tier ($29/mo) */}
          <div
            className={`relative flex flex-col justify-between rounded-xl border p-6 transition-all ${
              currentTier === "pro"
                ? "border-[#0a0a0a] bg-white ring-2 ring-[#0a0a0a] shadow-md"
                : "border-[#0a0a0a] bg-white shadow-sm hover:border-[#1a1a1a]"
            }`}
          >
            {/* Top Ribbon */}
            <div className="absolute -top-3 right-6">
              <span className="inline-flex items-center gap-1 rounded-full bg-[#0a0a0a] px-3 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-xs">
                <Sparkles className="h-3 w-3" /> Recommended
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold uppercase tracking-wider text-[#0a0a0a] flex items-center gap-1.5">
                  <Zap className="h-4 w-4" /> Pro Tier
                </span>
                {currentTier === "pro" && (
                  <span className="rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-[11px] font-mono font-semibold text-emerald-700">
                    ACTIVE
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-[#0a0a0a] tracking-tight">$29</span>
                <span className="text-xs text-[#8a8a88]">/ month</span>
              </div>
              <p className="mt-2 text-xs text-[#525250]">
                Production-grade autonomous loop with Supabase cloud persistence & Neatlogs tracing.
              </p>

              {/* Pro Features List */}
              <ul className="mt-6 space-y-3 text-xs text-[#525250]">
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-emerald-50 p-0.5 text-emerald-600 border border-emerald-200">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">Unlimited autonomous mutations</strong> & tournaments
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-emerald-50 p-0.5 text-emerald-600 border border-emerald-200">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">Full Supabase cloud lineage sync</strong> with RLS
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-emerald-50 p-0.5 text-emerald-600 border border-emerald-200">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">Neatlogs distributed trace export</strong> & telemetry
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded bg-emerald-50 p-0.5 text-emerald-600 border border-emerald-200">
                    <Check className="h-3.5 w-3.5" />
                  </div>
                  <span>
                    <strong className="text-[#0a0a0a]">Priority inference</strong> on TensorMux GLM-4.7-Flash
                  </span>
                </li>
              </ul>
            </div>

            {/* Interactive Actions */}
            <div className="mt-8 pt-4 border-t border-[#e4e4e3] flex flex-col gap-2">
              <button
                type="button"
                onClick={handleUpgradeToPro}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#0a0a0a] px-4 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-[#1a1a1a] transition-all cursor-pointer disabled:opacity-50"
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
                className="w-full flex items-center justify-center gap-2 rounded-lg border border-[#e4e4e3] bg-white px-4 py-2 text-xs font-medium text-[#525250] hover:bg-[#f4f4f3] hover:text-[#0a0a0a] transition-colors cursor-pointer disabled:opacity-50"
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
        <div className="border-t border-[#e4e4e3] bg-[#f9f9f8] px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-[#525250]">
          <div className="flex items-center gap-2">
            <span className="text-emerald-600">●</span>
            <span>NON-BLOCKING CONSOLE: Core synthesis & benchmarks remain 100% accessible</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const nextTier = currentTier === "pro" ? "free" : "pro";
                onTierChange?.(nextTier);
              }}
              className="text-[#0a0a0a] font-semibold hover:underline cursor-pointer"
            >
              [Simulate Toggle: {currentTier === "pro" ? "Free" : "Pro"}]
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={onClose}
              className="text-[#525250] hover:text-[#0a0a0a] cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
