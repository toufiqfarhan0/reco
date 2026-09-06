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
} from "lucide-react";

interface HeaderProps {
  currentStage: StageType;
  onSelectStage: (stage: StageType) => void;
  domain: DomainType;
  onChangeDomain: (d: DomainType) => void;
  mode: ExecutionMode;
  onToggleMode: (m: ExecutionMode) => void;
  isRunning?: boolean;
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
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:px-6 lg:px-8">
        {/* Top bar: Brand, Domain Selector, Execution Mode, Status */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold tracking-tight text-white">
                  Autonomous Agent Visual Engineering Console
                </h1>
                <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-[11px] font-medium text-cyan-400 ring-1 ring-inset ring-cyan-500/20">
                  Track 1
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Closed-Loop DAG Synthesis, Diagnostic Taxonomy & 4-Axis Benchmark
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Domain Selector */}
            <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-2 py-1 text-xs text-slate-300">
              <Database className="h-3.5 w-3.5 text-slate-400" />
              <label htmlFor="domain-select" className="text-slate-400 sr-only">
                Domain
              </label>
              <select
                id="domain-select"
                value={domain}
                onChange={(e) => onChangeDomain(e.target.value as DomainType)}
                className="bg-transparent font-medium text-slate-200 outline-none cursor-pointer pr-1"
                aria-label="Select Domain"
              >
                <option value="financial_reconciliation" className="bg-slate-900">
                  Financial Reconciliation
                </option>
                <option value="anomaly_detection" className="bg-slate-900">
                  Anomaly Detection
                </option>
                <option value="research_comparison" className="bg-slate-900">
                  Research Comparison
                </option>
              </select>
            </div>

            {/* Execution Mode Switcher: Demo Mode vs Live Mode */}
            <div
              className="flex items-center rounded-lg border border-slate-800 bg-slate-900 p-0.5 text-xs"
              role="radiogroup"
              aria-label="Execution Mode"
            >
              <button
                type="button"
                onClick={() => onToggleMode("demo")}
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all ${
                  mode === "demo"
                    ? "bg-cyan-500/20 text-cyan-300 shadow-xs ring-1 ring-cyan-500/40"
                    : "text-slate-400 hover:text-slate-200"
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
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all ${
                  mode === "live"
                    ? "bg-emerald-500/20 text-emerald-300 shadow-xs ring-1 ring-emerald-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
                aria-checked={mode === "live"}
                role="radio"
              >
                <span className="relative flex h-2 w-2">
                  <span
                    className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                      isRunning ? "animate-ping bg-emerald-400" : "bg-emerald-500"
                    }`}
                  />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                Live Mode
              </button>
            </div>
          </div>
        </div>

        {/* 5-Stage Engineering Navigator */}
        <nav
          className="grid grid-cols-2 gap-1.5 pt-1 sm:grid-cols-5"
          aria-label="Engineering Pipeline Stages"
        >
          {STAGES.map((s) => {
            const Icon = s.icon;
            const isActive = currentStage === s.id;
            return (
              <button
                key={s.id}
                onClick={() => onSelectStage(s.id)}
                className={`group flex items-center justify-between rounded-lg border px-3 py-2 text-left transition-all ${
                  isActive
                    ? "border-cyan-500/40 bg-cyan-950/30 text-cyan-200 ring-1 ring-cyan-500/30"
                    : "border-slate-800/80 bg-slate-900/50 text-slate-400 hover:border-slate-700 hover:bg-slate-900 hover:text-slate-200"
                }`}
                aria-current={isActive ? "step" : undefined}
              >
                <div className="flex items-center gap-2">
                  <Icon
                    className={`h-4 w-4 ${
                      isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                    }`}
                  />
                  <span className="text-xs font-semibold uppercase tracking-wider">
                    {s.label}
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono ${
                    isActive ? "text-cyan-400" : "text-slate-600"
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
