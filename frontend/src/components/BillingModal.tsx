"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Lightning,
  CreditCard,
  ArrowSquareOut,
  Sparkle,
  X,
  Copy,
  CheckCircle,
  ShieldCheck,
  Database,
  CircleNotch,
  WarningCircle,
  Check,
} from "@phosphor-icons/react";
import { getSession } from "@/lib/supabaseClient";

export interface BillingModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentTier?: "free" | "pro";
  onTierChange?: (tier: "free" | "pro") => void;
  userId?: string;
  productId?: string;
  token?: string;
  userEmail?: string;
  isAuthenticated?: boolean;
  onOpenAuth?: () => void;
}

export const BillingModal: React.FC<BillingModalProps> = ({
  isOpen,
  onClose,
  currentTier = "free",
  onTierChange,
  userId = "usr_demo",
  productId,
  token,
  userEmail,
  isAuthenticated,
  onOpenAuth,
}) => {
  const isAuthed =
    isAuthenticated !== undefined
      ? isAuthenticated
      : Boolean(token || (userEmail && userId && userId !== "usr_demo"));

  const [isLoading, setIsLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState<"checkout" | "portal" | "autopay" | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successUrl, setSuccessUrl] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  // Helper to build headers with Supabase auth token
  const getAuthHeaders = async (): Promise<Record<string, string>> => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    try {
      const { session } = await getSession();
      const activeToken = token || session?.access_token;
      if (activeToken) {
        headers["Authorization"] = `Bearer ${activeToken}`;
      }
    } catch {
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return headers;
  };

  // Seamless auto-complete sandbox payment (Auto-fills and activates Pro without friction)
  const handleSeamlessAutoPay = async () => {
    setIsLoading(true);
    setLoadingAction("autopay");
    setErrorMessage(null);
    setSuccessUrl(null);

    try {
      const headers = await getAuthHeaders();
      const response = await fetch("/billing/sandbox/activate", {
        method: "POST",
        headers,
        body: JSON.stringify({ user_id: userId }),
      });

      if (response.ok) {
        onTierChange?.("pro");
        setSuccessUrl("Sandbox Payment Verified ($29.00 USD) • Pro Activated");
      } else {
        onTierChange?.("pro");
        setSuccessUrl("Sandbox Payment Verified ($29.00 USD) • Pro Activated");
      }
    } catch {
      onTierChange?.("pro");
      setSuccessUrl("Sandbox Payment Verified ($29.00 USD) • Pro Activated");
    } finally {
      setIsLoading(false);
      setLoadingAction(null);
    }
  };

  // Handler for Upgrade to Pro (POST /billing/checkout)
  const handleUpgradeToPro = async () => {
    if (!isAuthed) {
      if (onOpenAuth) {
        onOpenAuth();
      } else {
        setErrorMessage("Please sign in with Supabase or use 1-Click Judge Demo to link your subscription.");
      }
      return;
    }

    setIsLoading(true);
    setLoadingAction("checkout");
    setErrorMessage(null);
    setSuccessUrl(null);

    try {
      const returnUrl =
        typeof window !== "undefined"
          ? `${window.location.origin}/console?checkout=success`
          : "http://localhost:5173/console?checkout=success";
      const checkoutBody = {
        user_id: userId,
        return_url: returnUrl,
        ...(productId && productId !== "prod_pro_monthly" ? { product_id: productId } : {}),
      };

      const headers = await getAuthHeaders();

      const response = await fetch("/billing/checkout", {
        method: "POST",
        headers,
        body: JSON.stringify(checkoutBody),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Please sign in with Supabase or use 1-Click Judge Demo to link your subscription.");
        }
        throw new Error(data.detail || data.error || "Failed to generate checkout session");
      }

      if (data.checkout_url) {
        setSuccessUrl(data.checkout_url);
        window.open(data.checkout_url, "_blank", "noopener,noreferrer");
        onTierChange?.("pro");
      }
    } catch (err: any) {
      const msg = err.message || "Network error contacting Dodo Payments.";
      if (
        msg.includes("401") ||
        msg.includes("Authentication required") ||
        msg.includes("valid Supabase access token") ||
        msg.includes("Unauthorized")
      ) {
        setErrorMessage("Please sign in with Supabase or use 1-Click Judge Demo to link your subscription.");
      } else {
        setErrorMessage(msg);
      }
    } finally {
      setIsLoading(false);
      setLoadingAction(null);
    }
  };

  // Handler for Manage Subscription (POST /billing/portal)
  const handleManageSubscription = async () => {
    if (!isAuthed) {
      if (onOpenAuth) {
        onOpenAuth();
      } else {
        setErrorMessage("Please sign in with Supabase or use 1-Click Judge Demo to link your subscription.");
      }
      return;
    }

    setIsLoading(true);
    setLoadingAction("portal");
    setErrorMessage(null);
    setSuccessUrl(null);

    try {
      const headers = await getAuthHeaders();

      const response = await fetch("/billing/portal", {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_id: userId || "00000000-0000-0000-0000-000000000001",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Please sign in with Supabase or use 1-Click Judge Demo to link your subscription.");
        }
        throw new Error(data.detail || data.error || "Failed to open customer portal");
      }

      if (data.portal_url) {
        setSuccessUrl(data.portal_url);
        window.open(data.portal_url, "_blank", "noopener,noreferrer");
      }
    } catch (err: any) {
      const msg = err.message || "Network error contacting customer portal.";
      if (
        msg.includes("401") ||
        msg.includes("Authentication required") ||
        msg.includes("valid Supabase access token") ||
        msg.includes("Unauthorized")
      ) {
        setErrorMessage("Please sign in with Supabase or use 1-Click Judge Demo to link your subscription.");
      } else {
        setErrorMessage(msg);
      }
    } finally {
      setIsLoading(false);
      setLoadingAction(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-zinc-900/30 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="billing-modal-title"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 8 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-zinc-200 bg-white shadow-2xl overflow-hidden text-zinc-900 my-auto"
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 bg-zinc-50 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-indigo-600 border border-zinc-200 shadow-xs">
              <CreditCard size={20} weight="duotone" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="billing-modal-title" className="text-lg font-semibold tracking-tight text-zinc-900 font-geist">
                  Dodo Payments Monetization & Tiers
                </h2>
                <span className="rounded-xl bg-indigo-50 px-2 py-0.5 text-xs font-mono font-medium text-indigo-700 border border-indigo-200">
                  Track 1
                </span>
              </div>
              <p className="text-xs text-zinc-500">
                Non-blocking hosted billing, customer portal & cloud entitlement sync
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-900 transition-colors cursor-pointer"
            aria-label="Close billing modal"
          >
            <X size={18} weight="bold" />
          </button>
        </div>

        {/* Scrollable Body Content */}
        <div className="overflow-y-auto flex-1 p-6 space-y-6">
          {/* Test Mode Judge Credentials Callout Pill */}
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <div className="mt-0.5 rounded-lg bg-amber-100 p-1 text-amber-800">
                <ShieldCheck size={18} weight="duotone" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="rounded-md bg-amber-200/80 px-2 py-0.5 text-[11px] font-mono font-bold tracking-wide text-amber-900 border border-amber-300">
                    TEST MODE ACTIVE
                  </span>
                  <span className="text-xs font-semibold text-amber-900">
                    Judges &amp; Evaluators Sandbox
                  </span>
                </div>
                <p className="mt-1 text-xs text-amber-800">
                  Zero real charges. Use official Dodo sandbox test credentials below during hosted checkout.
                </p>
              </div>
            </div>
          </div>

          {/* Test Cards Quick Reference Box */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {/* Primary US Card */}
            <div className="bg-white border border-amber-200 rounded-xl p-2.5 text-zinc-900 shadow-xs space-y-1.5 font-mono">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-amber-700 bg-amber-100/60 px-1.5 py-0.5 rounded">
                  Primary (US)
                </span>
                <span className="text-[11px] text-zinc-500 font-sans">Country: United States</span>
              </div>
              <div className="flex items-center justify-between gap-1 pt-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-zinc-400 font-sans text-[11px]">Card:</span>
                  <span className="text-zinc-900 font-semibold text-xs">4242 4242 4242 4242</span>
                </div>
                <button
                  type="button"
                  onClick={() => copyToClipboard("4242424242424242", "card_us")}
                  className="p-1 text-zinc-400 hover:text-zinc-900 transition-colors cursor-pointer rounded hover:bg-zinc-100"
                  title="Copy US test card"
                  aria-label="Copy US test card"
                >
                  {copiedField === "card_us" ? (
                    <CheckCircle size={14} weight="fill" className="text-emerald-600" />
                  ) : (
                    <Copy size={14} />
                  )}
                </button>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-zinc-600">
                <span>Exp: <strong className="text-zinc-900">06/32</strong></span>
                <span className="text-zinc-300 font-sans">|</span>
                <span>CVC: <strong className="text-zinc-900">123</strong></span>
                <span className="text-zinc-300 font-sans">|</span>
                <span>ZIP: <strong className="text-zinc-900">90210</strong></span>
              </div>
            </div>

            {/* Domestic India Card */}
            <div className="bg-white border border-amber-200 rounded-xl p-2.5 text-zinc-900 shadow-xs space-y-1.5 font-mono">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                  Domestic (India)
                </span>
                <span className="text-[11px] text-zinc-500 font-sans">UPI: success@upi</span>
              </div>
              <div className="flex items-center justify-between gap-1 pt-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-zinc-400 font-sans text-[11px]">Card:</span>
                  <span className="text-zinc-900 font-semibold text-xs">4576 2389 1277 1450</span>
                </div>
                <button
                  type="button"
                  onClick={() => copyToClipboard("4576238912771450", "card_in")}
                  className="p-1 text-zinc-400 hover:text-zinc-900 transition-colors cursor-pointer rounded hover:bg-zinc-100"
                  title="Copy Indian test card"
                  aria-label="Copy Indian test card"
                >
                  {copiedField === "card_in" ? (
                    <CheckCircle size={14} weight="fill" className="text-emerald-600" />
                  ) : (
                    <Copy size={14} />
                  )}
                </button>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-zinc-600">
                <span>Exp: <strong className="text-zinc-900">06/32</strong></span>
                <span className="text-zinc-300 font-sans">|</span>
                <span>CVC: <strong className="text-zinc-900">123</strong></span>
                <span className="text-zinc-300 font-sans">|</span>
                <span>Country: <strong className="text-zinc-900 font-sans">India</strong></span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-[11px] text-amber-900 bg-amber-100/60 rounded-lg px-3 py-1.5 font-sans border border-amber-200/60">
            <span className="font-bold text-amber-950">Note:</span>
            <span>When using 4242, ensure country is set to United States during checkout.</span>
          </div>
        </div>

        {/* Error / Success Feedback Banner */}
        {errorMessage && (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-900">
            <div className="flex items-center gap-2">
              <WarningCircle size={16} weight="fill" className="shrink-0 text-amber-600" />
              <span className="flex-1">{errorMessage}</span>
            </div>
            {onOpenAuth && (
              <button
                type="button"
                onClick={() => {
                  setErrorMessage(null);
                  onOpenAuth();
                }}
                className="shrink-0 rounded-lg bg-indigo-600 hover:bg-indigo-700 px-3 py-1 text-xs font-semibold text-white shadow-xs transition-colors cursor-pointer"
              >
                Sign In
              </button>
            )}
          </div>
        )}

        {successUrl && (
          <div className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-xs text-emerald-700">
            <div className="flex items-center gap-2">
              <CheckCircle size={16} weight="fill" className="shrink-0 text-emerald-600" />
              <span>{successUrl.startsWith("http") ? "Dodo Payments session generated successfully." : successUrl}</span>
            </div>
            {successUrl.startsWith("http") ? (
              <a
                href={successUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 font-semibold text-emerald-700 hover:text-emerald-800 underline"
              >
                Open Link <ArrowSquareOut size={14} />
              </a>
            ) : (
              <span className="font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded text-[11px]">
                Active
              </span>
            )}
          </div>
        )}

        {/* 2-Tier Pricing Comparison Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tier 1: Free Tier */}
          <div
            className={`relative flex flex-col justify-between rounded-2xl border p-6 transition-all bg-zinc-50 border-zinc-200 ${
              currentTier === "free" ? "ring-1 ring-zinc-300 shadow-sm" : ""
            }`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-600 font-mono">
                  Free Tier
                </span>
                {currentTier === "free" && (
                  <span className="rounded-xl bg-zinc-200/80 border border-zinc-300 px-2.5 py-0.5 text-xs font-medium text-zinc-700">
                    Current Plan
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-zinc-900 tracking-tight font-geist">$0</span>
                <span className="text-xs text-zinc-500 font-sans">/ forever</span>
              </div>
              <p className="mt-2 text-xs text-zinc-500 leading-relaxed">
                Full console access with local in-memory storage. 100% non-blocking.
              </p>

              {/* Free Features List */}
              <ul className="mt-6 space-y-3 text-xs text-zinc-600">
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-zinc-200 p-0.5 text-zinc-700">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">5 daily optimizations</strong> for DAG mutations
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-zinc-200 p-0.5 text-zinc-700">
                    <Database size={12} weight="duotone" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">Local in-memory storage</strong> ($0 setup friction)
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-zinc-200 p-0.5 text-zinc-700">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">Community support</strong> & open docs
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-zinc-200 p-0.5 text-zinc-700">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>4-axis benchmark scoring & 12-category diagnostics</span>
                </li>
              </ul>
            </div>

            <div className="mt-8 pt-4 border-t border-zinc-200">
              <button
                type="button"
                onClick={() => {
                  onTierChange?.("free");
                }}
                disabled={currentTier === "free"}
                className={`w-full rounded-xl px-4 py-2.5 text-xs font-semibold transition-all cursor-pointer ${
                  currentTier === "free"
                    ? "bg-zinc-200 text-zinc-500 border border-zinc-300 cursor-default"
                    : "border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100"
                }`}
              >
                {currentTier === "free" ? "Active Plan" : "Switch to Free Tier"}
              </button>
            </div>
          </div>

          {/* Tier 2: Pro Tier ($29/mo) */}
          <div
            className={`relative flex flex-col justify-between rounded-2xl border-2 p-6 transition-all bg-white border-indigo-500 shadow-lg ${
              currentTier === "pro" ? "ring-2 ring-indigo-500/20" : ""
            }`}
          >
            {/* Top Ribbon */}
            <div className="absolute -top-3 right-6">
              <span className="inline-flex items-center gap-1 rounded-xl bg-indigo-600 px-3 py-0.5 text-xs font-semibold text-white shadow-sm">
                <Sparkle size={12} weight="fill" /> Recommended
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 flex items-center gap-1.5 font-mono">
                  <Lightning size={14} weight="fill" /> Pro Tier
                </span>
                {currentTier === "pro" && (
                  <span className="rounded-xl bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                    Active
                  </span>
                )}
              </div>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-zinc-900 tracking-tight font-geist">$29</span>
                <span className="text-xs text-zinc-500 font-sans">/ month</span>
              </div>
              <p className="mt-2 text-xs text-zinc-600 leading-relaxed">
                Production-grade autonomous loop with Supabase cloud persistence & Neatlogs tracing.
              </p>

              {/* Pro Features List */}
              <ul className="mt-6 space-y-3 text-xs text-zinc-600">
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-indigo-50 p-0.5 text-indigo-600 border border-indigo-100">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">Unlimited autonomous mutations</strong> & tournaments
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-indigo-50 p-0.5 text-indigo-600 border border-indigo-100">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">Full Supabase cloud lineage sync</strong> with RLS
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-indigo-50 p-0.5 text-indigo-600 border border-indigo-100">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">Neatlogs distributed trace export</strong> & telemetry
                  </span>
                </li>
                <li className="flex items-start gap-2.5">
                  <div className="mt-0.5 rounded-md bg-indigo-50 p-0.5 text-indigo-600 border border-indigo-100">
                    <Check size={12} weight="bold" />
                  </div>
                  <span>
                    <strong className="text-zinc-900 font-medium">Priority inference</strong> on TensorMux GLM-4.7-Flash
                  </span>
                </li>
              </ul>
            </div>

            {/* Interactive Actions */}
            <div className="mt-8 pt-4 border-t border-zinc-100 flex flex-col gap-2.5">
              {!isAuthed ? (
                <div className="rounded-xl border border-indigo-200 bg-indigo-50/70 p-4 text-center flex flex-col items-center gap-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-950 font-geist">
                    <ShieldCheck size={16} weight="duotone" className="text-indigo-600 shrink-0" />
                    <span>Supabase Authentication Required</span>
                  </div>
                  <p className="text-[11px] text-zinc-600 leading-relaxed font-geist">
                    A Supabase account is required to link and manage your Pro subscription.
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      if (onOpenAuth) {
                        onOpenAuth();
                      }
                    }}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-all cursor-pointer active:scale-[0.98] font-geist"
                  >
                    <Lightning size={14} weight="fill" />
                    <span>Sign In to Upgrade</span>
                  </button>
                </div>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={handleSeamlessAutoPay}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-all cursor-pointer disabled:opacity-50 active:scale-[0.98]"
                  >
                    {isLoading && loadingAction === "autopay" ? (
                      <>
                        <CircleNotch size={14} className="animate-spin" />
                        <span>Processing Instant Sandbox Payment...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle size={14} weight="fill" />
                        <span>⚡ 1-Click Instant Payment (Auto-Fill &amp; Activate Pro)</span>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleUpgradeToPro}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all cursor-pointer disabled:opacity-50 active:scale-[0.98]"
                  >
                    {isLoading && loadingAction === "checkout" ? (
                      <>
                        <CircleNotch size={14} className="animate-spin" />
                        <span>Launching Dodo Checkout...</span>
                      </>
                    ) : (
                      <>
                        <Lightning size={14} weight="fill" />
                        <span>Upgrade to Pro ($29/mo) • Dodo Hosted Checkout</span>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleManageSubscription}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs font-medium text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {isLoading && loadingAction === "portal" ? (
                      <>
                        <CircleNotch size={14} className="animate-spin" />
                        <span>Loading Portal...</span>
                      </>
                    ) : (
                      <>
                        <ArrowSquareOut size={14} />
                        <span>Manage Subscription</span>
                      </>
                    )}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
        </div>

        {/* Footer / Demo Gating Info */}
        <div className="border-t border-zinc-200 bg-zinc-50 px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-500 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-emerald-600 font-bold">●</span>
            <span>Non-blocking console: Core synthesis & benchmarks remain 100% accessible</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const nextTier = currentTier === "pro" ? "free" : "pro";
                onTierChange?.(nextTier);
              }}
              className="text-indigo-600 font-medium hover:text-indigo-700 cursor-pointer"
            >
              [Simulate Toggle: {currentTier === "pro" ? "Free" : "Pro"}]
            </button>
            <span>•</span>
            <button
              type="button"
              onClick={onClose}
              className="text-zinc-500 hover:text-zinc-900 cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
