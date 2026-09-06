"use client";

import React from "react";
import { DomainType, ExecutionMode, StageType } from "@/lib/types";
import {
  Activity,
  Cpu,
  Layers,
  Sparkles,
  Zap,
  PlayCircle,
  Database,
  ShieldCheck,
  Compass,
  Terminal,
  ArrowLeft,
} from "lucide-react";
import { CloudAuthPill } from "./CloudAuthPill";

export interface HeaderProps {
  currentStage: StageType;
  onSelectStage: (stage: StageType) => void;
  domain: DomainType;
  onChangeDomain: (d: DomainType) => void;
  mode: ExecutionMode;
  onToggleMode: (m: ExecutionMode) => void;
  isRunning?: boolean;
  viewMode?: "overview" | "console";
  onToggleViewMode?: (mode: "overview" | "console") => void;
  tier?: "free" | "pro";
  onToggleTier?: (tier: "free" | "pro") => void;
  isCloudConnected?: boolean;
  sessionId?: string;
  tokenStatus?: string;
  onOpenBilling?: () => void;
  onGoToLanding?: () => void;
}

const STAGES: { id: StageType; label: string; num: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "BUILD", label: "Build", num: "01", icon: Cpu },
  { id: "RUN", label: "Run", num: "02", icon: PlayCircle },
  { id: "UNDERSTAND", label: "Understand", num: "03", icon: Activity },
  { id: "IMPROVE", label: "Improve", num: "04", icon: Sparkles },
  { id: "VALIDATE", label: "Validate", num: "05", icon: ShieldCheck },
];

export const Header: React.FC<HeaderProps> = ({
  currentStage,
  onSelectStage,
  domain,
  onChangeDomain,
  mode,
  onToggleMode,
  isRunning = false,
  viewMode = "console",
  onToggleViewMode,
  tier = "free",
  onToggleTier,
  isCloudConnected = true,
  sessionId = "usr_demo_anon_9f82c1",
  tokenStatus = "GoTrue JWT: Valid",
  onOpenBilling,
  onGoToLanding,
}) => {
  const handleStageClick = (stageId: StageType) => {
    onSelectStage(stageId);
    if (viewMode === "overview" && onToggleViewMode) {
      onToggleViewMode("console");
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-200/80 bg-white/95 backdrop-blur-md shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
      {/* Top Utility Bar */}
      <div className="border-b border-zinc-100 px-4 sm:px-6 lg:px-8 py-2.5">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          {/* Left Brand & Workspace */}
          <div className="flex items-center gap-3">
            {onGoToLanding && (
              <button
                type="button"
                onClick={onGoToLanding}
                className="inline-flex items-center gap-1.5 rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-600 hover:text-zinc-950 hover:bg-zinc-50 transition-colors cursor-pointer shadow-2xs"
                title="Return to Product Landing Page"
                aria-label="Return to Product Landing Page"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Landing</span>
              </button>
            )}

            <div className="h-4 w-px bg-zinc-200 hidden sm:block" />

            <div className="flex items-center gap-2">
              <span className="font-semibold text-zinc-950 text-sm tracking-tight flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-zinc-900" />
                Autonomous Agent Visual Engineering Console
              </span>
              <span className="rounded-full bg-zinc-100 border border-zinc-200/80 px-2 py-0.5 text-[10px] font-mono font-medium text-zinc-600">
                Track 1
              </span>
            </div>

            <div className="h-4 w-px bg-zinc-200 hidden md:block" />

            {/* Domain Selector */}
            <div className="hidden md:flex items-center gap-1.5 rounded-md border border-zinc-200 bg-zinc-50/50 px-2 py-1 text-xs text-zinc-600">
              <Database className="h-3 w-3 text-zinc-400" />
              <label htmlFor="domain-select" className="text-zinc-600 sr-only">
                Select Domain
              </label>
              <select
                id="domain-select"
                value={domain}
                onChange={(e) => onChangeDomain(e.target.value as DomainType)}
                className="bg-transparent font-medium text-zinc-900 outline-none cursor-pointer pr-1 text-xs"
                aria-label="Select Domain"
              >
                <option value="financial_reconciliation">
                  Financial Reconciliation
                </option>
                <option value="anomaly_detection">
                  Anomaly Detection
                </option>
                <option value="research_comparison">
                  Research Comparison
                </option>
              </select>
            </div>
          </div>

          {/* Right Tools & Account */}
          <div className="flex items-center gap-2.5">
            {/* View Mode Switcher: Overview vs Console */}
            <div
              className="flex items-center rounded-md border border-zinc-200 bg-zinc-100/80 p-0.5 text-xs"
              role="tablist"
              aria-label="View Mode Switcher"
            >
              <button
                type="button"
                onClick={() => onToggleViewMode?.("overview")}
                className={`flex items-center gap-1 rounded px-2.5 py-1 font-medium transition-all cursor-pointer ${
                  viewMode === "overview"
                    ? "bg-white text-zinc-950 shadow-2xs font-semibold"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
                role="tab"
                aria-selected={viewMode === "overview"}
              >
                <Compass className="h-3.5 w-3.5" />
                <span>Overview</span>
              </button>
              <button
                type="button"
                onClick={() => onToggleViewMode?.("console")}
                className={`flex items-center gap-1 rounded px-2.5 py-1 font-medium transition-all cursor-pointer ${
                  viewMode === "console"
                    ? "bg-white text-zinc-950 shadow-2xs font-semibold"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
                role="tab"
                aria-selected={viewMode === "console"}
              >
                <Terminal className="h-3.5 w-3.5" />
                <span>Console</span>
              </button>
            </div>

            {/* Execution Mode Switcher */}
            <div
              className="hidden sm:flex items-center rounded-md border border-zinc-200 bg-zinc-100/80 p-0.5 text-xs"
              role="radiogroup"
              aria-label="Execution Mode"
            >
              <button
                type="button"
                onClick={() => onToggleMode("demo")}
                className={`flex items-center gap-1 rounded px-2 py-1 font-medium transition-all cursor-pointer ${
                  mode === "demo"
                    ? "bg-white text-zinc-950 shadow-2xs font-semibold"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
                aria-checked={mode === "demo"}
                role="radio"
              >
                <Zap className="h-3 w-3" />
                <span>Demo Mode</span>
              </button>
              <button
                type="button"
                onClick={() => onToggleMode("live")}
                className={`flex items-center gap-1.5 rounded px-2 py-1 font-medium transition-all cursor-pointer ${
                  mode === "live"
                    ? "bg-white text-emerald-700 shadow-2xs font-semibold"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
                aria-checked={mode === "live"}
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
              tier={tier}
              isCloudConnected={isCloudConnected}
              sessionId={sessionId}
              tokenStatus={tokenStatus}
              onOpenBilling={onOpenBilling}
              onToggleTier={onToggleTier}
            />

            {/* Dodo Payments Upgrade CTA */}
            {onOpenBilling && (
              <button
                type="button"
                onClick={onOpenBilling}
                className="flex items-center gap-1.5 rounded-md bg-zinc-950 px-3 py-1.5 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors cursor-pointer shadow-2xs"
                aria-label="Open Dodo Payments Pricing and Billing"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                <span>{tier === "pro" ? "Manage Pro" : "Upgrade $29/mo"}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 5-Stage Engineering Navigator Strip */}
      <div className="bg-zinc-50/70 px-4 sm:px-6 lg:px-8 py-2">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 overflow-x-auto">
          <nav
            className="flex items-center gap-1.5 w-full justify-between"
            aria-label="Engineering Pipeline Stages"
          >
            {STAGES.map((s, idx) => {
              const Icon = s.icon;
              const isActive = currentStage === s.id && viewMode === "console";
              return (
                <React.Fragment key={s.id}>
                  <button
                    type="button"
                    onClick={() => handleStageClick(s.id)}
                    className={`flex-1 flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg border text-xs transition-all cursor-pointer select-none ${
                      isActive
                        ? "border-zinc-900 bg-zinc-900 text-white shadow-xs font-semibold"
                        : "border-zinc-200/80 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-950 hover:bg-zinc-50"
                    }`}
                    aria-current={isActive ? "step" : undefined}
                  >
                    <div className="flex items-center gap-2">
                      <Icon
                        className={`h-3.5 w-3.5 ${
                          isActive ? "text-white" : "text-zinc-400"
                        }`}
                      />
                      <span className="uppercase tracking-wider text-[11px] font-medium">
                        {s.label}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-bold ${
                        isActive ? "text-zinc-300" : "text-zinc-400"
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
    </header>
  );
};
