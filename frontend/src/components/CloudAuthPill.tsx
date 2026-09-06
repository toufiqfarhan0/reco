"use client";

import React, { useState } from "react";
import {
  Database,
  ShieldCheck,
  Zap,
  Check,
  Copy,
  CheckCheck,
  X,
  CreditCard,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Server,
  Lock,
} from "lucide-react";

export interface CloudAuthPillProps {
  tier?: "free" | "pro";
  isCloudConnected?: boolean;
  sessionId?: string;
  tokenStatus?: string;
  onOpenBilling?: () => void;
  onToggleTier?: (newTier: "free" | "pro") => void;
}

export const CloudAuthPill: React.FC<CloudAuthPillProps> = ({
  tier = "free",
  isCloudConnected = true,
  sessionId = "usr_demo_anon_9f82c1",
  tokenStatus = "GoTrue JWT: Valid",
  onOpenBilling,
  onToggleTier,
}) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const isPro = tier === "pro";

  return (
    <>
      {/* Status Pill in Header */}
      <button
        type="button"
        onClick={() => setIsDrawerOpen(true)}
        className={`group flex items-center gap-2 rounded-xl border px-2.5 py-1 text-xs font-medium transition-all cursor-pointer shadow-xs ${
          isPro
            ? "border-indigo-200 bg-indigo-50/70 text-indigo-900 hover:bg-indigo-100/70"
            : "border-zinc-200 bg-white text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50"
        }`}
        aria-label="Cloud Session Status and Entitlements"
        aria-haspopup="dialog"
      >
        {/* Supabase Cloud Sync Indicator Dot */}
        <span className="relative flex h-2 w-2">
          {isCloudConnected && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${
              isCloudConnected ? "bg-emerald-600" : "bg-amber-500"
            }`}
          />
        </span>

        {/* Tier Label */}
        <span className="font-mono text-[11px] font-semibold tracking-wide">
          {isPro ? "PRO TIER (ACTIVE)" : "FREE TIER (LOCAL)"}
        </span>

        <span className={isPro ? "text-indigo-600 group-hover:text-indigo-800" : "text-zinc-400 group-hover:text-zinc-700"}>
          <ChevronRight className="h-3 w-3" />
        </span>
      </button>

      {/* Quick Session Drawer (Slide-Over Panel) */}
      {isDrawerOpen && (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-xs transition-opacity"
          role="dialog"
          aria-modal="true"
          aria-labelledby="session-drawer-title"
        >
          {/* Backdrop Click Dismiss */}
          <div
            className="fixed inset-0"
            onClick={() => setIsDrawerOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Content */}
          <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-zinc-200 bg-white p-6 shadow-2xl text-zinc-900 overflow-y-auto">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-zinc-200 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200">
                  <Database className="h-4 w-4" />
                </div>
                <div>
                  <h3 id="session-drawer-title" className="text-sm font-semibold text-zinc-900">
                    Supabase Cloud Session
                  </h3>
                  <p className="text-[11px] text-zinc-500 font-mono">
                    PostgreSQL RLS & Entitlements
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsDrawerOpen(false)}
                className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 transition-colors cursor-pointer"
                aria-label="Close session drawer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Main Drawer Body */}
            <div className="flex-1 space-y-6 py-5">
              {/* Entitlement Banner */}
              <div
                className={`rounded-2xl border p-4 ${
                  isPro
                    ? "border-indigo-200 bg-indigo-50/50 text-zinc-900 shadow-xs"
                    : "border-zinc-200 bg-zinc-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isPro ? (
                      <Sparkles className="h-4 w-4 text-indigo-600" />
                    ) : (
                      <Zap className="h-4 w-4 text-zinc-500" />
                    )}
                    <span className="text-xs font-bold uppercase tracking-wider text-zinc-900">
                      {isPro ? "Reco Pro Tier" : "Free Tier"}
                    </span>
                  </div>
                  <span
                    className={`rounded-xl px-2.5 py-0.5 text-[10px] font-mono font-semibold ${
                      isPro
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-zinc-100 text-zinc-600 border border-zinc-200"
                    }`}
                  >
                    {isPro ? "ACTIVE ($29/mo)" : "LOCAL ($0/mo)"}
                  </span>
                </div>

                <p className="mt-2 text-xs leading-relaxed text-zinc-600">
                  {isPro
                    ? "Unlimited autonomous mutations, full Supabase cloud lineage sync, and Neatlogs distributed traces."
                    : "5 daily optimizations with local in-memory storage. 100% non-blocking free access."}
                </p>

                <div className="mt-4 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsDrawerOpen(false);
                      onOpenBilling?.();
                    }}
                    className={`flex-1 flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium transition-all cursor-pointer ${
                      isPro
                        ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs"
                        : "bg-zinc-900 text-white hover:bg-zinc-800 shadow-xs"
                    }`}
                  >
                    <CreditCard className="h-3.5 w-3.5" />
                    {isPro ? "Manage Subscription" : "Upgrade to Pro"}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      onToggleTier?.(isPro ? "free" : "pro");
                    }}
                    className="rounded-xl border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors cursor-pointer shadow-xs"
                    title="Simulate tier toggle for judging evaluation"
                  >
                    Switch to {isPro ? "Free" : "Pro"}
                  </button>
                </div>
              </div>

              {/* Session Identity Card */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 font-mono">
                  Anonymous Session Identity
                </h4>

                <div className="space-y-2 rounded-2xl border border-zinc-200 bg-zinc-50/80 p-3.5 text-xs font-mono">
                  {/* Anonymous Session ID */}
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Session ID:</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-zinc-900 font-medium">{sessionId}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sessionId, "sessionId")}
                        className="text-zinc-400 hover:text-zinc-700 transition-colors cursor-pointer"
                        title="Copy Session ID"
                        aria-label="Copy Session ID"
                      >
                        {copiedField === "sessionId" ? (
                          <CheckCheck className="h-3.5 w-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Token Status */}
                  <div className="flex items-center justify-between border-t border-zinc-200 pt-2">
                    <span className="text-zinc-500">Token Status:</span>
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      {tokenStatus}
                    </span>
                  </div>

                  {/* Auth Provider */}
                  <div className="flex items-center justify-between border-t border-zinc-200 pt-2">
                    <span className="text-zinc-500">Auth Provider:</span>
                    <span className="text-zinc-900">Supabase GoTrue (HS256)</span>
                  </div>

                  {/* User Role */}
                  <div className="flex items-center justify-between border-t border-zinc-200 pt-2">
                    <span className="text-zinc-500">Tenant Isolation:</span>
                    <span className="text-zinc-900">RLS (auth.uid() isolated)</span>
                  </div>
                </div>
              </div>

              {/* Persistence Status */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 font-mono">
                  Persistence Architecture
                </h4>

                <div className="space-y-2 rounded-2xl border border-zinc-200 bg-zinc-50/80 p-3.5 text-xs">
                  <div className="flex items-center justify-between font-mono">
                    <span className="text-zinc-500">Cloud Sync:</span>
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                      <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
                      {isCloudConnected ? "Supabase Live" : "Local In-Memory"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between font-mono border-t border-zinc-200 pt-2">
                    <span className="text-zinc-500">Module:</span>
                    <span className="text-zinc-900">reco/db/supabase.py</span>
                  </div>

                  <div className="flex items-center justify-between font-mono border-t border-zinc-200 pt-2">
                    <span className="text-zinc-500">Repository:</span>
                    <span className="text-zinc-900">
                      {isCloudConnected ? "SupabaseRepository" : "InMemoryRepository"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between font-mono border-t border-zinc-200 pt-2">
                    <span className="text-zinc-500">Gate Policy:</span>
                    <span className="text-emerald-700">Non-Blocking Free Access</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="border-t border-zinc-200 pt-4">
              <button
                type="button"
                onClick={() => setIsDrawerOpen(false)}
                className="w-full rounded-xl border border-zinc-200 bg-white px-4 py-2 text-xs font-medium text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 transition-colors cursor-pointer shadow-xs"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
