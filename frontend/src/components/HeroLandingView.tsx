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
    <div className="min-h-[85dvh] flex flex-col justify-between py-4 sm:py-8 space-y-8">
      {/* Hero Stack */}
      <div className="mx-auto w-full max-w-4xl text-center space-y-6">
        {/* Eyebrow Badge */}
        <div className="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/70 px-3.5 py-1 text-xs font-mono font-medium text-indigo-700 shadow-xs">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-500 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
          </span>
          <span>TRACK 1: AUTOMATED AGENT ENGINEERING • SYNDICATE BY MAXIMOR</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-zinc-900 leading-tight">
          Autonomous Agent Engineering System
        </h1>

        {/* Subheadline */}
        <p className="mx-auto max-w-2xl text-base sm:text-lg text-zinc-600 leading-relaxed font-normal">
          From high-level natural language goals to self-improving, Pareto-optimized agent DAGs with closed-loop failure diagnostics, self-reflection memory, and air-gapped held-out verification.
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={onLaunchConsole}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 active:scale-[0.98] cursor-pointer"
          >
            <Terminal className="h-4 w-4" />
            <span>Launch Interactive Console</span>
            <ArrowRight className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={onExploreLineage}
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-6 py-3 text-sm font-semibold text-zinc-900 shadow-xs transition-all hover:bg-zinc-50 active:scale-[0.98] cursor-pointer"
          >
            <GitBranch className="h-4 w-4 text-zinc-500" />
            <span>Explore Evolution Lineage</span>
          </button>
        </div>
      </div>

      {/* 5-Stage Closed-Loop Pipeline Interactive Grid */}
      <div className="mx-auto w-full max-w-7xl pt-4">
        <div className="mb-4 flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-600">
              5-Stage Closed-Loop Architecture
            </span>
            <span className="h-1 w-1 rounded-full bg-zinc-300" />
            <span className="text-xs text-zinc-500">
              Select any stage to inspect live artifacts
            </span>
          </div>
          <span className="font-mono text-xs font-semibold text-zinc-900">
            Self-Improving DAG Loop
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-5">
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
                className="group relative flex flex-col justify-between rounded-2xl border border-zinc-200 bg-white p-4.5 transition-all hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-xs cursor-pointer shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-100 text-zinc-700 border border-zinc-200 group-hover:bg-indigo-50 group-hover:text-indigo-700 group-hover:border-indigo-200 transition-colors">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-mono text-xs font-bold text-zinc-400 group-hover:text-zinc-900 transition-colors">
                      {stage.num}
                    </span>
                  </div>

                  <div className="mt-3.5">
                    <div className="flex items-center gap-1.5">
                      <h2 className="text-sm font-semibold text-zinc-900">
                        {stage.title}
                      </h2>
                      <span className="rounded-lg bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200 group-hover:bg-indigo-50/60 group-hover:text-indigo-700 group-hover:border-indigo-200 transition-colors">
                        {stage.tag}
                      </span>
                    </div>
                    <p className="mt-1 font-mono text-[11px] text-zinc-500 leading-snug">
                      {stage.subtitle}
                    </p>
                    <p className="mt-2 text-xs text-zinc-500 leading-relaxed">
                      {stage.summary}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-zinc-100 pt-2.5 text-[11px] text-zinc-400 group-hover:text-indigo-600 transition-colors font-mono font-medium">
                  <span>Enter Stage</span>
                  <ArrowRight className="h-3.5 w-3.5 transform group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Production Tech Rail */}
      <div className="mx-auto w-full max-w-7xl border-t border-zinc-200/80 pt-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span className="font-semibold uppercase tracking-wider text-zinc-950">
              Live Production Stack:
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center sm:gap-3">
            {TECH_BADGES.map((tech) => {
              const Icon = tech.icon;
              return (
                <div
                  key={tech.label}
                  className="flex items-center gap-2 rounded-xl border border-zinc-200/80 bg-white px-3 py-1.5 text-xs shadow-2xs"
                >
                  <Icon className="h-3.5 w-3.5 text-zinc-500" />
                  <div className="flex items-center gap-1.5">
                    <span className="text-zinc-400 font-mono text-[11px]">
                      {tech.label}:
                    </span>
                    <span className="font-medium text-zinc-950">
                      {tech.provider}
                    </span>
                    <span className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-[10px] text-zinc-600 border border-zinc-200">
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
