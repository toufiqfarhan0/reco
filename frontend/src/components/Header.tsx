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
    <header className="sticky top-0 z-40 w-full border-b border-[#e4e4e3] bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:px-6 lg:px-8">
        {/* Top bar: Brand, View Mode Switcher, Domain Selector, Execution Mode, Status */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {onGoToLanding && (
              <button
                type="button"
                onClick={onGoToLanding}
                className="flex items-center gap-1.5 rounded-lg border border-[#e4e4e3] bg-white px-2.5 py-1.5 text-xs font-medium text-[#525250] hover:text-[#0a0a0a] hover:bg-[#f4f4f3] transition-colors cursor-pointer shadow-xs"
                title="Return to Product Landing Page"
                aria-label="Return to Product Landing Page"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Landing</span>
              </button>
            )}
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#f4f4f3] text-[#0a0a0a] border border-[#e4e4e3]">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold tracking-tight text-[#0a0a0a]">
                  Autonomous Agent Visual Engineering Console
                </h1>
                <span className="rounded-full bg-[#f4f4f3] px-2 py-0.5 text-[11px] font-medium text-[#525250] border border-[#e4e4e3]">
                  Track 1
                </span>
              </div>
              <p className="text-xs text-[#525250]">
                Closed-Loop DAG Synthesis, Diagnostic Taxonomy & 4-Axis Benchmark
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Top-Level View Mode Switcher: Overview vs Console */}
            <div
              className="flex items-center rounded-lg border border-[#e4e4e3] bg-[#f4f4f3] p-0.5 text-xs"
              role="tablist"
              aria-label="View Mode Switcher"
            >
              <button
                type="button"
                onClick={() => onToggleViewMode?.("overview")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1 font-medium transition-all cursor-pointer ${
                  viewMode === "overview"
                    ? "bg-white text-[#0a0a0a] shadow-xs font-semibold"
                    : "text-[#525250] hover:text-[#0a0a0a]"
                }`}
                role="tab"
                aria-selected={viewMode === "overview"}
              >
                <Compass className="h-3.5 w-3.5" />
                Overview
              </button>
              <button
                type="button"
                onClick={() => onToggleViewMode?.("console")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1 font-medium transition-all cursor-pointer ${
                  viewMode === "console"
                    ? "bg-white text-[#0a0a0a] shadow-xs font-semibold"
                    : "text-[#525250] hover:text-[#0a0a0a]"
                }`}
                role="tab"
                aria-selected={viewMode === "console"}
              >
                <Terminal className="h-3.5 w-3.5" />
                Console
              </button>
            </div>

            {/* Domain Selector */}
            <div className="flex items-center gap-1.5 rounded-lg border border-[#e4e4e3] bg-white px-2 py-1 text-xs text-[#525250]">
              <Database className="h-3.5 w-3.5 text-[#8a8a88]" />
              <label htmlFor="domain-select" className="text-[#525250] sr-only">
                Domain
              </label>
              <select
                id="domain-select"
                value={domain}
                onChange={(e) => onChangeDomain(e.target.value as DomainType)}
                className="bg-transparent font-medium text-[#0a0a0a] outline-none cursor-pointer pr-1"
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

            {/* Execution Mode Switcher: Demo Mode vs Live Mode */}
            <div
              className="flex items-center rounded-lg border border-[#e4e4e3] bg-[#f4f4f3] p-0.5 text-xs"
              role="radiogroup"
              aria-label="Execution Mode"
            >
              <button
                type="button"
                onClick={() => onToggleMode("demo")}
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all cursor-pointer ${
                  mode === "demo"
                    ? "bg-white text-[#0a0a0a] shadow-xs font-semibold"
                    : "text-[#525250] hover:text-[#0a0a0a]"
                }`}
                aria-checked={mode === "demo"}
                role="radio"
              >
                <Zap className="h-3 w-3" />
                Demo Mode
              </button>
              <button
                type="button"
                onClick={() => onToggleMode("live")}
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all cursor-pointer ${
                  mode === "live"
                    ? "bg-white text-emerald-700 shadow-xs font-semibold"
                    : "text-[#525250] hover:text-[#0a0a0a]"
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
                Live Mode
              </button>
            </div>

            {/* Supabase Cloud Auth & Entitlement Status Pill */}
            <CloudAuthPill
              tier={tier}
              isCloudConnected={isCloudConnected}
              sessionId={sessionId}
              tokenStatus={tokenStatus}
              onOpenBilling={onOpenBilling}
              onToggleTier={onToggleTier}
            />

            {/* Direct Monetization / Billing Modal Button */}
            {onOpenBilling && (
              <button
                type="button"
                onClick={onOpenBilling}
                className="flex items-center gap-1.5 rounded-lg border border-[#0a0a0a] bg-[#0a0a0a] px-2.5 py-1 text-xs font-semibold text-white hover:bg-[#1a1a1a] transition-all cursor-pointer shadow-xs"
                aria-label="Open Dodo Payments Pricing and Billing"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                <span>{tier === "pro" ? "Manage Pro" : "Upgrade $29/mo"}</span>
              </button>
            )}
          </div>
        </div>

        {/* 5-Stage Engineering Navigator */}
        <nav
          className="grid grid-cols-2 gap-1.5 pt-1 sm:grid-cols-5"
          aria-label="Engineering Pipeline Stages"
        >
          {STAGES.map((s) => {
            const Icon = s.icon;
            const isActive = currentStage === s.id && viewMode === "console";
            return (
              <button
                key={s.id}
                onClick={() => handleStageClick(s.id)}
                className={`group flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-all cursor-pointer ${
                  isActive
                    ? "border-[#0a0a0a] bg-[#0a0a0a] text-white shadow-xs"
                    : "border-[#e4e4e3] bg-white text-[#525250] hover:border-[#d1d1cf] hover:text-[#0a0a0a] hover:bg-[#f4f4f3]"
                }`}
                aria-current={isActive ? "step" : undefined}
              >
                <div className="flex items-center gap-2">
                  <Icon
                    className={`h-4 w-4 ${
                      isActive ? "text-white" : "text-[#8a8a88] group-hover:text-[#0a0a0a]"
                    }`}
                  />
                  <span className="text-xs font-semibold uppercase tracking-wider">
                    {s.label}
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono ${
                    isActive ? "text-white/80" : "text-[#8a8a88]"
                  }`}
                >
                  {s.num}
                </span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
