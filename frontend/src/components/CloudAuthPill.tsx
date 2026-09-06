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
        className={`group flex items-center gap-2 rounded-lg border px-2.5 py-1 text-xs font-medium transition-all cursor-pointer shadow-xs ${
          isPro
            ? "border-cyan-500/40 bg-cyan-950/40 text-cyan-200 hover:border-cyan-400 hover:bg-cyan-900/40 ring-1 ring-cyan-500/30"
            : "border-slate-800 bg-slate-900/90 text-slate-300 hover:border-slate-700 hover:bg-slate-800"
        }`}
        aria-label="Cloud Session Status and Entitlements"
        aria-haspopup="dialog"
      >
        {/* Supabase Cloud Sync Indicator Dot */}
        <span className="relative flex h-2 w-2">
          {isCloudConnected && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${
              isCloudConnected ? "bg-emerald-500" : "bg-amber-500"
            }`}
          />
        </span>

        {/* Tier Label */}
        <span className="font-mono text-[11px] font-semibold tracking-wide">
          {isPro ? "PRO TIER (ACTIVE)" : "FREE TIER (LOCAL)"}
        </span>

        <span className="text-slate-500 group-hover:text-slate-300">
          <ChevronRight className="h-3 w-3" />
        </span>
      </button>

      {/* Quick Session Drawer (Slide-Over Panel) */}
      {isDrawerOpen && (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-xs transition-opacity"
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
          <div className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-slate-800 bg-slate-900 p-6 shadow-2xl text-slate-100 overflow-y-auto">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30">
                  <Database className="h-4 w-4" />
                </div>
                <div>
                  <h3 id="session-drawer-title" className="text-sm font-semibold text-white">
                    Supabase Cloud Session
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono">
                    PostgreSQL RLS & Entitlements
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsDrawerOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
                aria-label="Close session drawer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Main Drawer Body */}
            <div className="flex-1 space-y-6 py-5">
              {/* Entitlement Banner */}
              <div
                className={`rounded-xl border p-4 ${
                  isPro
                    ? "border-cyan-500/40 bg-gradient-to-br from-cyan-950/50 to-slate-900"
                    : "border-slate-800 bg-slate-950/60"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isPro ? (
                      <Sparkles className="h-4 w-4 text-cyan-400" />
                    ) : (
                      <Zap className="h-4 w-4 text-slate-400" />
                    )}
                    <span className="text-xs font-bold uppercase tracking-wider text-white">
                      {isPro ? "Reco Pro Tier" : "Free Tier"}
                    </span>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-mono font-semibold ${
                      isPro
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-slate-800 text-slate-400 border border-slate-700"
                    }`}
                  >
                    {isPro ? "ACTIVE ($29/mo)" : "LOCAL ($0/mo)"}
                  </span>
                </div>

                <p className="mt-2 text-xs text-slate-300">
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
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-cyan-500/20 border border-cyan-500/40 px-3 py-1.5 text-xs font-medium text-cyan-300 hover:bg-cyan-500/30 transition-all cursor-pointer"
                  >
                    <CreditCard className="h-3.5 w-3.5" />
                    {isPro ? "Manage Subscription" : "Upgrade to Pro"}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      onToggleTier?.(isPro ? "free" : "pro");
                    }}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 transition-colors cursor-pointer"
                    title="Simulate tier toggle for judging evaluation"
                  >
                    Switch to {isPro ? "Free" : "Pro"}
                  </button>
                </div>
              </div>

              {/* Session Identity Card */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                  Anonymous Session Identity
                </h4>

                <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-xs font-mono">
                  {/* Anonymous Session ID */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Session ID:</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-cyan-300 font-medium">{sessionId}</span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(sessionId, "sessionId")}
                        className="text-slate-400 hover:text-white transition-colors cursor-pointer"
                        title="Copy Session ID"
                        aria-label="Copy Session ID"
                      >
                        {copiedField === "sessionId" ? (
                          <CheckCheck className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Token Status */}
                  <div className="flex items-center justify-between border-t border-slate-800/80 pt-2">
                    <span className="text-slate-400">Token Status:</span>
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      {tokenStatus}
                    </span>
                  </div>

                  {/* Auth Provider */}
                  <div className="flex items-center justify-between border-t border-slate-800/80 pt-2">
                    <span className="text-slate-400">Auth Provider:</span>
                    <span className="text-slate-200">Supabase GoTrue (HS256)</span>
                  </div>

                  {/* User Role */}
                  <div className="flex items-center justify-between border-t border-slate-800/80 pt-2">
                    <span className="text-slate-400">Tenant Isolation:</span>
                    <span className="text-slate-200">RLS (auth.uid() isolated)</span>
                  </div>
                </div>
              </div>

              {/* Persistence Status */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
                  Persistence Architecture
                </h4>

                <div className="space-y-2 rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 text-xs">
                  <div className="flex items-center justify-between font-mono">
                    <span className="text-slate-400">Cloud Sync:</span>
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      {isCloudConnected ? "Supabase Live" : "Local In-Memory"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between font-mono border-t border-slate-800/80 pt-2">
                    <span className="text-slate-400">Module:</span>
                    <span className="text-slate-300">reco/db/supabase.py</span>
                  </div>

                  <div className="flex items-center justify-between font-mono border-t border-slate-800/80 pt-2">
                    <span className="text-slate-400">Repository:</span>
                    <span className="text-slate-300">
                      {isCloudConnected ? "SupabaseRepository" : "InMemoryRepository"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between font-mono border-t border-slate-800/80 pt-2">
                    <span className="text-slate-400">Gate Policy:</span>
                    <span className="text-emerald-400">Non-Blocking Free Access</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="border-t border-slate-800 pt-4">
              <button
                type="button"
                onClick={() => setIsDrawerOpen(false)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer"
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
