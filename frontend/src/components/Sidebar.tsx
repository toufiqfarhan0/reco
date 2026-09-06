"use client";

import React from "react";
import { DomainType, ExecutionMode, StageType } from "@/lib/types";
import {
  Cpu,
  Play,
  Pulse,
  Sparkle,
  ShieldCheck,
  Terminal,
  ArrowLeft,
  User,
  SignIn,
  SignOut,
  FolderDashed,
  Database,
  Lightning,
} from "@phosphor-icons/react";
import { CloudAuthPill } from "./CloudAuthPill";

export interface SidebarProps {
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
}

const STAGES: { id: StageType; label: string; num: string; Icon: React.ElementType }[] = [
  { id: "BUILD", label: "Build", num: "01", Icon: Cpu },
  { id: "RUN", label: "Run", num: "02", Icon: Play },
  { id: "UNDERSTAND", label: "Understand", num: "03", Icon: Pulse },
  { id: "IMPROVE", label: "Improve", num: "04", Icon: Sparkle },
  { id: "VALIDATE", label: "Validate", num: "05", Icon: ShieldCheck },
];

export const Sidebar: React.FC<SidebarProps> = ({
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

  return (
    <aside className="fixed top-0 bottom-0 left-0 z-40 w-[220px] bg-white border-r border-zinc-200 shadow-sm flex flex-col justify-between overflow-y-auto select-none">
      {/* Top Section */}
      <div className="p-3.5 space-y-4">
        {/* App Logo & Wordmark */}
        <div className="flex items-center justify-between pb-2 border-b border-zinc-100">
          <div className="flex items-center gap-2.5">
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
            <div>
              <span className="font-geist font-bold text-zinc-900 text-base leading-none block">
                Reco
              </span>
              <span className="text-[10px] font-mono text-zinc-400 block leading-tight">
                Agent Engineering
              </span>
            </div>
          </div>

          {onGoToLanding && (
            <button
              type="button"
              onClick={onGoToLanding}
              className="p-1 rounded-md text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 transition cursor-pointer"
              title="Return to Product Landing Page"
              aria-label="Return to Product Landing Page"
            >
              <ArrowLeft size={14} weight="bold" />
            </button>
          )}
        </div>

        {/* Active Console Workspace Indicator */}
        <div className="space-y-1">
          <button
            type="button"
            onClick={() => onToggleViewMode?.("console")}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
              viewMode === "console"
                ? "bg-zinc-100 text-zinc-900 font-semibold"
                : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
            }`}
          >
            <Terminal size={15} weight="bold" className="text-indigo-600" />
            <span>Console</span>
          </button>
        </div>

        {/* Section Divider: TRACK 1 */}
        <div>
          <div className="flex items-center justify-between px-2 py-1">
            <span className="text-[10px] font-mono font-bold tracking-wider text-zinc-400 uppercase">
              TRACK 1
            </span>
            <span className="text-[9px] font-mono text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded border border-indigo-100">
              Active
            </span>
          </div>

          {/* Stage Navigation (Vertical list, numbered) */}
          <nav className="space-y-1 mt-1" aria-label="Engineering Pipeline Stages">
            {STAGES.map((s) => {
              const Icon = s.Icon;
              const isActive = currentStage === s.id && viewMode === "console";
              const accessibleLabel = `${s.label} ${s.num}`;

              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => handleStageClick(s.id)}
                  aria-label={accessibleLabel}
                  className={`w-full relative flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition cursor-pointer ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700 font-semibold"
                      : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
                  }`}
                  aria-current={isActive ? "step" : undefined}
                >
                  {/* Active Indigo 3px Left Edge Bar */}
                  {isActive && (
                    <span className="absolute left-0 top-1 bottom-1 w-[3px] rounded-r bg-indigo-600" />
                  )}

                  <div className="flex items-center gap-2 pl-0.5">
                    <Icon
                      size={15}
                      weight={isActive ? "fill" : "regular"}
                      className={isActive ? "text-indigo-600" : "text-zinc-400"}
                    />
                    <span className="uppercase tracking-wide text-[11px] font-medium font-geist">
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
              );
            })}
          </nav>
        </div>

        {/* Section Divider: SETTINGS */}
        <div>
          <div className="px-2 py-1 text-[10px] font-mono font-bold tracking-wider text-zinc-400 uppercase">
            SETTINGS
          </div>

          <div className="space-y-2 mt-1 px-1">
            {/* Domain Preset Selector */}
            <div className="space-y-1">
              <label htmlFor="sidebar-domain-select" className="text-[10px] font-mono text-zinc-500 block">
                Domain Preset
              </label>
              <div className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs">
                <Database size={12} className="text-zinc-400 shrink-0" />
                <select
                  id="sidebar-domain-select"
                  value={domain || ""}
                  onChange={(e) => onChangeDomain(e.target.value as DomainType)}
                  className="w-full bg-transparent font-medium text-zinc-900 outline-none cursor-pointer text-[11px] font-geist"
                  aria-label="Select Domain"
                >
                  <option value="" disabled>
                    — Select a domain preset —
                  </option>
                  <option value="financial_reconciliation">Financial Reconcile</option>
                  <option value="anomaly_detection">Anomaly Detection</option>
                  <option value="research_comparison">Research Comparison</option>
                </select>
              </div>
            </div>

            {/* Demo Mode / Live Mode Toggle */}
            <div className="space-y-1 pt-1">
              <span className="text-[10px] font-mono text-zinc-500 block">
                Execution Engine
              </span>
              <div
                className="grid grid-cols-2 rounded-lg border border-zinc-200 bg-zinc-100 p-0.5 text-xs"
                role="radiogroup"
                aria-label="Execution Mode"
              >
                <button
                  type="button"
                  onClick={() => handleToggleMode("demo")}
                  className={`flex items-center justify-center gap-1 rounded py-1 text-[11px] font-medium transition cursor-pointer ${
                    mode === "demo"
                      ? "bg-white text-zinc-900 shadow-xs font-semibold"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                  aria-checked={mode === "demo"}
                  role="radio"
                >
                  <span>Demo</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleMode("live")}
                  className={`flex items-center justify-center gap-1 rounded py-1 text-[11px] font-medium transition cursor-pointer ${
                    mode === "live" || mode === "tensormux"
                      ? "bg-white text-emerald-700 shadow-xs font-semibold"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                  aria-checked={mode === "live" || mode === "tensormux"}
                  role="radio"
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${isRunning ? "animate-ping bg-emerald-500" : "bg-emerald-600"}`} />
                  <span>Live</span>
                </button>
              </div>
            </div>

            {/* FREE TIER (Local) Status Badge */}
            <div className="pt-1">
              <CloudAuthPill
                tier={effectiveTier}
                isCloudConnected={isCloudConnected}
                sessionId={sessionId}
                tokenStatus={tokenStatus}
                onOpenBilling={onOpenBilling}
                onToggleTier={onToggleTier}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Auth & Billing */}
      <div className="p-3 border-t border-zinc-100 bg-zinc-50/50 space-y-2">
        {/* User / Auth Button */}
        {user ? (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between px-2 py-1 rounded-lg bg-white border border-zinc-200 text-xs font-mono">
              <div className="flex items-center gap-1.5 min-w-0">
                <User size={12} weight="bold" className="text-indigo-600 shrink-0" />
                <span className="text-zinc-800 font-semibold truncate text-[11px]" title={user.email || ""}>
                  {user.user_metadata?.display_name || user.email?.split("@")[0] || "User"}
                </span>
              </div>
              {onSignOut && (
                <button
                  type="button"
                  onClick={onSignOut}
                  className="p-1 text-zinc-400 hover:text-rose-600 rounded transition cursor-pointer"
                  title="Sign Out"
                  aria-label="Sign Out"
                  data-testid="sign-out-button"
                >
                  <SignOut size={12} weight="bold" />
                </button>
              )}
            </div>

            {onOpenExperiments && (
              <button
                type="button"
                onClick={onOpenExperiments}
                className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-zinc-200 bg-white py-1.5 text-[11px] font-medium text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition cursor-pointer shadow-2xs font-mono"
                data-testid="open-my-experiments-button"
              >
                <FolderDashed size={13} weight="duotone" className="text-indigo-600" />
                <span>My Experiments</span>
              </button>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={onOpenAuth}
            className="w-full flex items-center justify-center gap-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 py-2 text-xs font-semibold text-white transition cursor-pointer shadow-xs font-mono"
            data-testid="open-auth-modal-button"
            aria-label="Sign In to Reco"
          >
            <SignIn size={14} weight="bold" />
            <span>Sign In</span>
          </button>
        )}

        {/* Billing Button */}
        {onOpenBilling && (
          <button
            type="button"
            onClick={onOpenBilling}
            className="w-full flex items-center justify-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 py-2 text-xs font-semibold text-white transition cursor-pointer shadow-xs font-mono"
            aria-label="Open Dodo Payments Pricing and Billing"
            data-testid="open-billing-modal-button"
          >
            <Sparkle size={13} weight="fill" className="text-amber-300" />
            <span>{effectiveTier === "pro" ? "PRO ($29/mo)" : "FREE ($0)"}</span>
          </button>
        )}
      </div>
    </aside>
  );
};
