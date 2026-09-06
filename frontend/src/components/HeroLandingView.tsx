"use client";

import React from "react";
import { StageType } from "@/lib/types";
import {
  Cpu,
  PlayCircle,
  Activity,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  GitBranch,
  Terminal,
  Zap,
  CheckCircle2,
  Database,
  Radio,
  CreditCard,
} from "lucide-react";

export interface HeroLandingViewProps {
  onLaunchConsole: () => void;
  onExploreLineage: () => void;
  onSelectStage?: (stage: StageType) => void;
}

interface PipelineStageCard {
  id: StageType;
  num: string;
  title: string;
  subtitle: string;
  summary: string;
  icon: React.ComponentType<{ className?: string }>;
  tag: string;
}

const PIPELINE_STAGES: PipelineStageCard[] = [
  {
    id: "BUILD",
    num: "01",
    title: "Build",
    subtitle: "Goal deconstruction & initial DAG synthesis",
    summary: "Translates high-level natural language into typed DAG nodes, tool bindings, and execution graphs.",
    icon: Cpu,
    tag: "Synthesis",
  },
  {
    id: "RUN",
    num: "02",
    title: "Run",
    subtitle: "Deterministic execution & 4-axis scorecard",
    summary: "Executes topologically with runtime tracing, quantifying Accuracy, Reliability, Cost, and Speed.",
    icon: PlayCircle,
    tag: "Evaluation",
  },
  {
    id: "UNDERSTAND",
    num: "03",
    title: "Understand",
    subtitle: "12-category diagnostic root cause analysis",
    summary: "Dissects failure traces to isolate underlying root causes from observable surface symptoms.",
    icon: Activity,
    tag: "Diagnostics",
  },
  {
    id: "IMPROVE",
    num: "04",
    title: "Improve",
    subtitle: "Self-reflection, mutation tournament & Pareto frontier",
    summary: "Autonomous mutations guided by epistemic memory ledger rules to find non-dominated architectures.",
    icon: Sparkles,
    tag: "Optimization",
  },
  {
    id: "VALIDATE",
    num: "05",
    title: "Validate",
    subtitle: "Air-gapped held-out promotion gate",
    summary: "Rigorous zero-leakage evaluation on held-out test splits before automated production promotion.",
    icon: ShieldCheck,
    tag: "Verification",
  },
];

interface TechBadge {
  label: string;
  provider: string;
  detail: string;
  icon: React.ComponentType<{ className?: string }>;
}

const TECH_BADGES: TechBadge[] = [
  {
    label: "Inference",
    provider: "TensorMux",
    detail: "GLM-4.7-Flash",
    icon: Zap,
  },
  {
    label: "Observability",
    provider: "Neatlogs",
    detail: "Distributed Tracing",
    icon: Radio,
  },
  {
    label: "Persistence",
    provider: "Supabase",
    detail: "Cloud Ledger",
    icon: Database,
  },
  {
    label: "Monetization",
    provider: "Dodo Payments",
    detail: "Pro Tier",
    icon: CreditCard,
  },
];

export const HeroLandingView: React.FC<HeroLandingViewProps> = ({
  onLaunchConsole,
  onExploreLineage,
  onSelectStage,
}) => {
  return (
    <div className="min-h-[90dvh] flex flex-col justify-between py-6 sm:py-10">
      {/* Hero Stack (Max 4 text elements per tasteskill guidelines) */}
      <div className="mx-auto w-full max-w-5xl text-center space-y-6">
        {/* Element 1: Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-3.5 py-1 text-xs font-mono font-medium text-cyan-300 shadow-sm shadow-cyan-950/50">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
          </span>
          <span>TRACK 1: AUTOMATED AGENT ENGINEERING • SYNDICATE BY MAXIMOR</span>
        </div>

        {/* Element 2: Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Autonomous Agent Engineering System
        </h1>

        {/* Element 3: Subheadline (Exactly 20 words per tasteskill brief) */}
        <p className="mx-auto max-w-3xl text-base sm:text-lg text-slate-300 leading-relaxed font-normal">
          From high-level natural language goals to self-improving, Pareto-optimized agent DAGs with closed-loop failure diagnostics, self-reflection memory, and air-gapped held-out verification.
        </p>

        {/* Element 4: Primary & Secondary Action CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            type="button"
            onClick={onLaunchConsole}
            className="inline-flex items-center gap-2 rounded-lg bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/25 transition-all hover:bg-cyan-400 active:scale-[0.98] cursor-pointer"
          >
            <Terminal className="h-4 w-4" />
            <span>Launch Interactive Console</span>
            <ArrowRight className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={onExploreLineage}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/90 px-6 py-3 text-sm font-semibold text-slate-200 shadow-sm transition-all hover:border-slate-600 hover:bg-slate-800 hover:text-white active:scale-[0.98] cursor-pointer"
          >
            <GitBranch className="h-4 w-4 text-cyan-400" />
            <span>Explore Evolution Lineage</span>
          </button>
        </div>
      </div>

      {/* 5-Stage Closed-Loop Pipeline Interactive Grid */}
      <div className="mx-auto w-full max-w-7xl pt-10 pb-8">
        <div className="mb-4 flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-400">
              5-Stage Closed-Loop Architecture
            </span>
            <span className="h-1 w-1 rounded-full bg-slate-600" />
            <span className="text-xs text-slate-500">
              Select any stage to inspect live artifacts
            </span>
          </div>
          <span className="font-mono text-xs text-cyan-400">
            Self-Improving DAG Loop
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {PIPELINE_STAGES.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.id}
                onClick={() => {
                  if (onSelectStage) {
                    onSelectStage(stage.id);
                  } else {
                    onLaunchConsole();
                  }
                }}
                className="group relative flex flex-col justify-between rounded-xl border border-slate-800/90 bg-slate-900/60 p-4 transition-all hover:-translate-y-0.5 hover:border-cyan-500/50 hover:bg-slate-900 hover:shadow-lg hover:shadow-cyan-950/30 cursor-pointer"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800/80 text-cyan-400 ring-1 ring-slate-700 group-hover:bg-cyan-500/10 group-hover:text-cyan-300 group-hover:ring-cyan-500/30 transition-colors">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-mono text-xs font-bold text-slate-500 group-hover:text-cyan-400 transition-colors">
                      {stage.num}
                    </span>
                  </div>

                  <div className="mt-3">
                    <div className="flex items-center gap-1.5">
                      <h2 className="text-sm font-semibold text-white group-hover:text-cyan-200 transition-colors">
                        {stage.title}
                      </h2>
                      <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
                        {stage.tag}
                      </span>
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-cyan-400/90 leading-snug">
                      {stage.subtitle}
                    </p>
                    <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                      {stage.summary}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[11px] text-slate-500 group-hover:text-cyan-300 transition-colors font-mono">
                  <span>Enter Stage</span>
                  <ArrowRight className="h-3.5 w-3.5 transform group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Production Tech Rail (Under the Hero as required by tasteskill) */}
      <div className="mx-auto w-full max-w-7xl border-t border-slate-800/80 pt-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span className="font-semibold uppercase tracking-wider text-slate-300">
              Live Production Stack:
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center sm:gap-3">
            {TECH_BADGES.map((tech) => {
              const Icon = tech.icon;
              return (
                <div
                  key={tech.label}
                  className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs shadow-xs"
                >
                  <Icon className="h-3.5 w-3.5 text-cyan-400" />
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-400 font-mono text-[11px]">
                      {tech.label}:
                    </span>
                    <span className="font-medium text-slate-200">
                      {tech.provider}
                    </span>
                    <span className="rounded bg-slate-800 px-1 py-0.2 font-mono text-[10px] text-cyan-300">
                      {tech.detail}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
