"use client";

import React from "react";
import { motion } from "motion/react";
import { DomainType, ExecutionMode, StageType } from "@/lib/types";
import {
  Cpu,
  Play,
  Pulse,
  Sparkle,
  ShieldCheck,
  Compass,
  Terminal,
  ArrowLeft,
  User,
  SignIn,
  SignOut,
  FolderDashed,
  Database,
  Lightning,
  GithubLogo,
  Bell,
} from "@phosphor-icons/react";
import { CloudAuthPill } from "./CloudAuthPill";

export interface HeaderProps {
  currentStage?: StageType;
  onSelectStage?: (stage: StageType) => void;
  domain?: DomainType | "";
  onChangeDomain?: (d: DomainType) => void;
  mode?: ExecutionMode | "mock" | "tensormux";
  onToggleMode?: (m: ExecutionMode) => void;
  onModeChange?: (m: any) => void;
  isRunning?: boolean;
  viewMode?: "overview" | "console";
  onToggleViewMode?: (mode: "overview" | "console") => void;
  tier?: "free" | "pro";
  billingPlan?: "FREE" | "PRO";
  onToggleTier?: (tier: "free" | "pro") => void;
  isCloudConnected?: boolean;
  sessionId?: string;
  tokenStatus?: string;
  onOpenBilling?: () => void;
  onGoToLanding?: () => void;
  user?: any;
  onOpenAuth?: () => void;
  onOpenExperiments?: () => void;
  onSignOut?: () => void;
  sidebarPresent?: boolean;
}

const STAGES: { id: StageType; label: string; num: string; Icon: React.ElementType }[] = [
  { id: "BUILD", label: "Build", num: "01", Icon: Cpu },
  { id: "RUN", label: "Run", num: "02", Icon: Play },
  { id: "UNDERSTAND", label: "Understand", num: "03", Icon: Pulse },
  { id: "IMPROVE", label: "Improve", num: "04", Icon: Sparkle },
  { id: "VALIDATE", label: "Validate", num: "05", Icon: ShieldCheck },
];

export const Header: React.FC<HeaderProps> = ({
  currentStage = "BUILD",
  onSelectStage = () => {},
  domain = "",
  onChangeDomain = () => {},
  mode = "demo",
  onToggleMode = () => {},
  onModeChange,
  isRunning = false,
  viewMode = "console",
  onToggleViewMode,
  tier = "free",
  billingPlan,
  onToggleTier,
  isCloudConnected = true,
  sessionId = "usr_demo_anon_9f82c1",
  tokenStatus = "GoTrue JWT: Valid",
  onOpenBilling,
  onGoToLanding,
  user,
  onOpenAuth,
  onOpenExperiments,
  onSignOut,
  sidebarPresent = false,
}) => {
  const effectiveTier = billingPlan ? (billingPlan === "PRO" ? "pro" : "free") : tier;

  const handleToggleMode = (m: ExecutionMode) => {
    onToggleMode(m);
    onModeChange?.(m);
  };

  const handleStageClick = (stageId: StageType) => {
    onSelectStage(stageId);
    if (viewMode === "overview" && onToggleViewMode) {
      onToggleViewMode("console");
    }
  };

  // SLIM SINGLE-ROW HEADER (when Sidebar is present in App)
  if (sidebarPresent) {
    return (
      <header className="sticky top-0 z-30 h-[52px] max-h-[52px] w-full bg-white border-b border-zinc-200 shadow-2xs flex items-center px-6">
        <div className="w-full flex items-center justify-between">
          {/* Left: Brand + Track 1 Badge */}
          <div className="flex items-center gap-3">
            <span className="font-geist font-bold text-zinc-900 text-sm tracking-tight">
              Reco
            </span>
            <div className="h-3.5 w-px bg-zinc-200" />
            <div className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-indigo-600" />
              <span className="text-xs font-medium text-zinc-700 font-geist hidden sm:inline">
                Autonomous Agent Engineering
              </span>
              <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-mono font-medium text-indigo-700">
                Track 1
              </span>
            </div>
          </div>

          {/* Right: Nav Links + GitHub + Notification Bell */}
          <div className="flex items-center gap-4">
            <nav className="flex items-center gap-4 text-xs font-medium text-zinc-600 font-geist">
              <a
                href="#how-it-works"
                className="hover:text-zinc-900 transition-colors cursor-pointer"
              >
                How it works
              </a>
              <a
                href="#pricing"
                onClick={(e) => {
                  if (onOpenBilling) {
                    e.preventDefault();
                    onOpenBilling();
                  }
                }}
                className="hover:text-zinc-900 transition-colors cursor-pointer"
              >
                Pricing
              </a>
            </nav>

            <div className="h-3.5 w-px bg-zinc-200" />

            {/* Notification Bell */}
            <button
              type="button"
              className="relative p-1.5 rounded-lg text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 transition cursor-pointer"
              title="Notifications"
              aria-label="Notifications"
            >
              <Bell size={16} weight="duotone" />
              <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-indigo-600" />
            </button>

            {/* GitHub Repo Link */}
            <a
              href="https://github.com/toufiqfarhan0/reco"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center h-7 w-7 rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors shadow-2xs"
              title="View on GitHub"
              aria-label="View on GitHub"
            >
              <GithubLogo size={15} weight="bold" />
            </a>
          </div>
        </div>
      </header>
    );
  }

  // STANDALONE HEADER MODE (Used when Header is tested in isolation)
  return (
    <motion.header
      initial={{ y: -10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="sticky top-0 z-40 w-full bg-white border-b border-zinc-100 shadow-xs"
    >
      {/* Main Top Bar */}
      <div className="px-4 sm:px-6 lg:px-8 py-2.5">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          {/* Left: R Logomark + Wordmark + Console Title */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white border border-zinc-200 shadow-xs overflow-hidden shrink-0">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 32 32"
                  width="22"
                  height="22"
                  fill="none"
                  aria-label="Reco Logomark"
                >
                  <path
                    fill="#4F46E5"
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M4 4H24V15H17.2L25.5 28H18L10.5 16.5V28H4V4ZM10.5 8.5V12H18V8.5H10.5Z"
                  />
                </svg>
              </div>
              <span className="font-geist font-semibold text-zinc-900 text-base tracking-tight leading-none">
                Reco
              </span>
            </div>

            {onGoToLanding && (
              <button
                type="button"
                onClick={onGoToLanding}
                className="hidden sm:inline-flex items-center gap-1 rounded-lg border border-zinc-200 bg-white px-2 py-0.5 text-xs font-medium text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50 transition-colors cursor-pointer shadow-2xs"
                title="Return to Product Landing Page"
                aria-label="Return to Product Landing Page"
              >
                <ArrowLeft size={12} weight="bold" className="text-zinc-400" />
                <span>Landing</span>
              </button>
            )}

            <div className="h-4 w-px bg-zinc-200 hidden sm:block" />

            <div className="flex items-center gap-2">
              <span className="font-geist font-medium text-zinc-800 text-xs tracking-tight flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-indigo-600" />
                Autonomous Agent Visual Engineering Console
              </span>
              <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-mono font-medium text-indigo-700">
                Track 1
              </span>
            </div>

            <div className="h-4 w-px bg-zinc-200 hidden xl:block" />
            <nav className="hidden xl:flex items-center gap-4 text-xs font-medium text-zinc-600">
              <a
                href="#how-it-works"
                className="hover:text-zinc-900 transition-colors cursor-pointer"
              >
                How it works
              </a>
              <a
                href="#pricing"
                onClick={(e) => {
                  if (onOpenBilling) {
                    e.preventDefault();
                    onOpenBilling();
                  }
                }}
                className="hover:text-zinc-900 transition-colors cursor-pointer"
              >
                Pricing
              </a>
            </nav>
          </div>

          {/* Center/Right Controls */}
          <div className="flex items-center gap-2.5">
            {/* Domain Selector */}
            <div className="hidden lg:flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs text-zinc-700">
              <Database size={13} className="text-zinc-400" />
              <label htmlFor="domain-select" className="text-zinc-600 sr-only">
                Select Domain
              </label>
              <select
                id="domain-select"
                value={domain || ""}
                onChange={(e) => onChangeDomain(e.target.value as DomainType)}
                className="bg-transparent font-medium text-zinc-900 outline-none cursor-pointer pr-1 text-xs font-geist"
                aria-label="Select Domain"
              >
                <option value="" disabled>
                  — Select a domain preset —
                </option>
                <option value="financial_reconciliation">Financial Reconciliation</option>
                <option value="anomaly_detection">Anomaly Detection</option>
                <option value="research_comparison">Research Comparison</option>
              </select>
            </div>

            {/* View Mode Switcher: Overview vs Console */}
            <div
              className="flex items-center rounded-xl border border-zinc-200 bg-zinc-100 p-0.5 text-xs"
              role="tablist"
              aria-label="View Mode Switcher"
            >
              <button
                type="button"
                onClick={() => onToggleViewMode?.("overview")}
                className={`flex items-center gap-1 rounded-lg px-2.5 py-1 font-medium transition-all cursor-pointer ${
                  viewMode === "overview"
                    ? "bg-white text-zinc-900 shadow-xs font-semibold border border-zinc-200/80"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
                role="tab"
                aria-selected={viewMode === "overview"}
              >
                <Compass size={14} weight={viewMode === "overview" ? "bold" : "regular"} />
                <span>Overview</span>
              </button>
              <button
                type="button"
                onClick={() => onToggleViewMode?.("console")}
                className={`flex items-center gap-1 rounded-lg px-2.5 py-1 font-medium transition-all cursor-pointer ${
                  viewMode === "console"
                    ? "bg-white text-zinc-900 shadow-xs font-semibold border border-zinc-200/80"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
                role="tab"
                aria-selected={viewMode === "console"}
              >
                <Terminal size={14} weight={viewMode === "console" ? "bold" : "regular"} />
                <span>Console</span>
              </button>
            </div>

            {/* Execution Mode Switcher */}
            <div
              className="hidden sm:flex items-center rounded-xl border border-zinc-200 bg-zinc-100 p-0.5 text-xs"
              role="radiogroup"
              aria-label="Execution Mode"
            >
              <button
                type="button"
                onClick={() => handleToggleMode("demo")}
                className={`flex items-center gap-1 rounded-lg px-2 py-1 font-medium transition-all cursor-pointer ${
                  mode === "demo"
                    ? "bg-white text-zinc-900 shadow-xs font-semibold border border-zinc-200/80"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
                aria-checked={mode === "demo"}
                role="radio"
              >
                <Lightning size={13} weight={mode === "demo" ? "fill" : "regular"} className="text-zinc-500" />
                <span>Demo Mode</span>
              </button>
              <button
                type="button"
                onClick={() => handleToggleMode("live")}
                className={`flex items-center gap-1.5 rounded-lg px-2 py-1 font-medium transition-all cursor-pointer ${
                  mode === "live" || mode === "tensormux"
                    ? "bg-white text-emerald-700 shadow-xs font-semibold border border-zinc-200/80"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
                aria-checked={mode === "live" || mode === "tensormux"}
                role="radio"
              >
                <span className="relative flex h-2 w-2">
                  <span
                    className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                      isRunning ? "animate-ping bg-emerald-500" : "bg-emerald-600"
                    }`}
                  />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-600" />
                </span>
                <span>Live Mode</span>
              </button>
            </div>

            {/* Supabase Cloud Auth Status */}
            <CloudAuthPill
              tier={effectiveTier}
              isCloudConnected={isCloudConnected}
              sessionId={sessionId}
              tokenStatus={tokenStatus}
              onOpenBilling={onOpenBilling}
              onToggleTier={onToggleTier}
            />

            {/* GitHub Link Button */}
            <a
              href="https://github.com/toufiqfarhan0/reco"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center h-8 w-8 rounded-xl border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors shadow-xs"
              title="View on GitHub"
              aria-label="View on GitHub"
            >
              <GithubLogo size={18} weight="bold" />
            </a>

            {/* Dodo Payments Billing Button */}
            {onOpenBilling && (
              <button
                type="button"
                onClick={onOpenBilling}
                className="flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs font-mono"
                aria-label="Open Dodo Payments Pricing and Billing"
                data-testid="open-billing-modal-button"
              >
                <Sparkle size={13} weight="fill" className="text-amber-300" />
                <span>{effectiveTier === "pro" ? "PRO" : "FREE"}</span>
                <span className="text-indigo-200 font-normal hidden sm:inline">
                  {effectiveTier === "pro" ? "($29/mo)" : "($0)"}
                </span>
              </button>
            )}

            {/* Supabase Authentication & User Controls */}
            {user ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onOpenExperiments}
                  className="flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-2.5 py-1.5 text-xs font-medium text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors cursor-pointer shadow-xs"
                  title="View my persisted experiments"
                  data-testid="open-my-experiments-button"
                >
                  <FolderDashed size={15} weight="duotone" className="text-indigo-600" />
                  <span className="hidden sm:inline font-mono">My Experiments</span>
                </button>

                <div className="flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-mono">
                  <User size={13} weight="bold" className="text-indigo-600" />
                  <span className="text-zinc-800 font-semibold max-w-[120px] truncate" title={user.email || ""}>
                    {user.user_metadata?.display_name || user.email?.split("@")[0] || "User"}
                  </span>
                  {onSignOut && (
                    <button
                      type="button"
                      onClick={onSignOut}
                      className="p-0.5 text-zinc-400 hover:text-rose-600 rounded transition ml-0.5 cursor-pointer"
                      title="Sign Out"
                      aria-label="Sign Out"
                      data-testid="sign-out-button"
                    >
                      <SignOut size={13} weight="bold" />
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={onOpenAuth}
                className="flex items-center gap-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 px-3 py-1.5 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs font-mono"
                data-testid="open-auth-modal-button"
                aria-label="Sign In to Reco"
              >
                <SignIn size={14} weight="bold" className="text-white" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 5-Stage Engineering Navigator Strip */}
      <div className="bg-zinc-50/70 border-t border-zinc-100 px-4 sm:px-6 lg:px-8 py-2">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 overflow-x-auto">
          <nav
            className="flex items-center gap-1.5 w-full justify-between"
            aria-label="Engineering Pipeline Stages"
          >
            {STAGES.map((s, idx) => {
              const Icon = s.Icon;
              const isActive = currentStage === s.id && viewMode === "console";
              return (
                <React.Fragment key={s.id}>
                  <button
                    type="button"
                    onClick={() => handleStageClick(s.id)}
                    className={`flex-1 flex items-center justify-between gap-2 px-3 py-1.5 rounded-xl border text-xs transition-all cursor-pointer select-none ${
                      isActive
                        ? "border-indigo-600 bg-indigo-50/80 text-indigo-900 shadow-xs font-semibold"
                        : "border-zinc-200/80 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900 hover:bg-zinc-50"
                    }`}
                    aria-current={isActive ? "step" : undefined}
                  >
                    <div className="flex items-center gap-2">
                      <Icon
                        size={15}
                        weight={isActive ? "fill" : "regular"}
                        className={isActive ? "text-indigo-600" : "text-zinc-400"}
                      />
                      <span className="uppercase tracking-wider text-[11px] font-medium font-geist">
                        {s.label}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-bold ${
                        isActive ? "text-indigo-600" : "text-zinc-400"
                      }`}
                    >
                      {s.num}
                    </span>
                  </button>

                  {idx < STAGES.length - 1 && (
                    <span className="text-zinc-300 text-xs select-none hidden sm:inline" aria-hidden="true">
                      →
                    </span>
                  )}
                </React.Fragment>
              );
            })}
          </nav>
        </div>
      </div>
    </motion.header>
  );
};
