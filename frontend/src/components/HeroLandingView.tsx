"use client";

import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { StageType } from "@/lib/types";
import {
  Cpu,
  Play,
  Pulse,
  Sparkle,
  ShieldCheck,
  ArrowRight,
  GitBranch,
  Terminal,
  Lightning,
  CheckCircle,
  Database,
  Broadcast,
  CreditCard,
  GithubLogo,
  Graph,
  ArrowUpRight,
} from "@phosphor-icons/react";

export interface HeroLandingViewProps {
  onLaunchConsole: () => void;
  onExploreLineage: () => void;
  onSelectStage?: (stage: StageType) => void;
  onOpenBilling?: () => void;
}

interface PipelineStageCard {
  id: StageType;
  num: string;
  title: string;
  subtitle: string;
  summary: string;
  Icon: React.ElementType;
  tag: string;
}

const PIPELINE_STAGES: PipelineStageCard[] = [
  {
    id: "BUILD",
    num: "01",
    title: "BUILD",
    subtitle: "Goal deconstruction & initial DAG synthesis",
    summary: "Define your goal in plain English. Reco synthesizes the tool DAG and sets evaluation criteria.",
    Icon: Cpu,
    tag: "Synthesis",
  },
  {
    id: "RUN",
    num: "02",
    title: "RUN",
    subtitle: "Deterministic execution & 4-axis scorecard",
    summary: "Reco executes your agent against edge-case test suites, measuring accuracy, latency, and cost.",
    Icon: Play,
    tag: "Evaluation",
  },
  {
    id: "UNDERSTAND",
    num: "03",
    title: "UNDERSTAND",
    subtitle: "12-category diagnostic root cause analysis",
    summary: "Deep failure analysis maps issues to a 12-category failure taxonomy automatically.",
    Icon: Pulse,
    tag: "Diagnostics",
  },
  {
    id: "IMPROVE",
    num: "04",
    title: "IMPROVE",
    subtitle: "Self-reflection, mutation tournament & Pareto frontier",
    summary: "Evolutionary search mutates prompts, tool configs, and verifies invariant rules.",
    Icon: Sparkle,
    tag: "Optimization",
  },
  {
    id: "VALIDATE",
    num: "05",
    title: "VALIDATE",
    subtitle: "Air-gapped held-out promotion gate",
    summary: "Air-gapped held-out validation proves zero leakage before production deployment.",
    Icon: ShieldCheck,
    tag: "Verification",
  },
];

interface TechBadge {
  label: string;
  provider: string;
  detail: string;
  Icon: React.ElementType;
}

const TECH_BADGES: TechBadge[] = [
  {
    label: "Inference",
    provider: "TensorMux",
    detail: "GLM-4.7-Flash",
    Icon: Lightning,
  },
  {
    label: "Observability",
    provider: "Neatlogs",
    detail: "Distributed Tracing",
    Icon: Broadcast,
  },
  {
    label: "Persistence",
    provider: "Supabase",
    detail: "Cloud Ledger",
    Icon: Database,
  },
  {
    label: "Monetization",
    provider: "Dodo Payments",
    detail: "Pro Tier",
    Icon: CreditCard,
  },
];

export const HeroLandingView: React.FC<HeroLandingViewProps> = ({
  onLaunchConsole,
  onExploreLineage,
  onSelectStage,
  onOpenBilling,
}) => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % PIPELINE_STAGES.length);
    }, 2400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-[90dvh] flex flex-col justify-between py-6 sm:py-10 space-y-12 bg-zinc-50">
      {/* Hero Stack */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="mx-auto w-full max-w-4xl text-center space-y-6"
      >
        {/* Track 1 Pill Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-3.5 py-1 text-xs font-mono font-medium text-indigo-700 shadow-2xs">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
          </span>
          <span>TRACK 1: AUTOMATED AGENT ENGINEERING • SYNDICATE BY MAXIMOR</span>
        </div>

        {/* Large Headline */}
        <div className="space-y-2">
          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-900 leading-[1.12] font-geist"
            aria-label="Autonomous Agent Engineering System: Build Agents That Actually Improve Themselves"
          >
            Build Agents That Actually Improve Themselves
            <span className="block text-xl sm:text-2xl font-semibold text-zinc-400 mt-2 font-geist">
              Autonomous Agent Engineering System
            </span>
          </h1>
        </div>

        {/* Sub-headline */}
        <p className="mx-auto max-w-2xl text-base sm:text-lg text-zinc-500 leading-relaxed font-normal font-geist">
          From high-level natural language goals to self-improving, Pareto-optimized agent DAGs with closed-loop failure diagnostics, self-reflection memory, and air-gapped held-out verification.
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          {/* Primary Filled CTA */}
          <button
            type="button"
            onClick={onLaunchConsole}
            aria-label="Launch Interactive Console"
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 active:scale-[0.98] cursor-pointer font-geist"
          >
            <Terminal size={18} weight="bold" />
            <span>Launch Console</span>
            <ArrowRight size={16} weight="bold" />
          </button>

          {/* GitHub Outlined CTA */}
          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-5 py-3 text-sm font-semibold text-zinc-900 shadow-xs transition-all hover:bg-zinc-50 active:scale-[0.98] cursor-pointer font-geist"
          >
            <GithubLogo size={18} weight="bold" />
            <span>View on GitHub</span>
          </a>

          {/* Explore Evolution Lineage CTA */}
          <button
            type="button"
            onClick={onExploreLineage}
            aria-label="Explore Evolution Lineage"
            className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-5 py-3 text-sm font-semibold text-zinc-700 shadow-xs transition-all hover:bg-zinc-50 hover:text-zinc-900 active:scale-[0.98] cursor-pointer font-geist"
          >
            <GitBranch size={18} weight="duotone" className="text-indigo-600" />
            <span>Explore Evolution Lineage</span>
          </button>
        </div>
      </motion.div>

      {/* 5-Stage Closed-Loop Pipeline Animated Stepper (Non-clickable) */}
      <section id="how-it-works" className="mx-auto w-full max-w-7xl pt-8 scroll-mt-20">
        <div className="text-center max-w-2xl mx-auto mb-8 space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 font-geist">
            How Reco Works — 5 Steps, Zero Configuration
          </h2>
          <p className="text-sm text-zinc-500 font-geist">
            From natural language goal to production-grade agent in minutes
          </p>

          {/* Live Autonomous Pipeline Cycle Indicator */}
          <div className="pt-2 flex items-center justify-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50/70 px-3 py-1 text-[11px] font-mono text-indigo-700">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
              </span>
              <span>Autonomous Pipeline Cycle: Stage {activeStep + 1} of 5 &bull; {PIPELINE_STAGES[activeStep].title}</span>
            </span>
          </div>
        </div>

        {/* Horizontal Step-Flow Layout (Stacked on Mobile, Horizontal on Desktop) */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 relative select-none">
          {PIPELINE_STAGES.map((stage, i) => {
            const isActive = i === activeStep;
            const isPast = i < activeStep;

            return (
              <div
                key={stage.id}
                className={`relative flex flex-col items-start text-left transition-all duration-300 ${
                  isActive ? "opacity-100" : "opacity-75"
                }`}
              >
                {/* Step Circle (32px) + Animated Connecting Line */}
                <div className="relative flex items-center w-full mb-3">
                  <div
                    className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full text-xs font-mono font-bold transition-all duration-300 shrink-0 ${
                      isActive
                        ? "bg-indigo-600 text-white ring-4 ring-indigo-100 shadow-sm scale-110"
                        : isPast
                        ? "bg-indigo-100 text-indigo-700 border border-indigo-200"
                        : "bg-zinc-200 text-zinc-500"
                    }`}
                  >
                    {stage.num}
                  </div>

                  {/* Connecting Line (Desktop) */}
                  {i < PIPELINE_STAGES.length - 1 && (
                    <div className="hidden md:block flex-1 h-[2px] bg-zinc-200 ml-3 mr-0 relative overflow-hidden rounded-full">
                      {/* Animated Progress Line */}
                      <div
                        className={`absolute inset-0 bg-indigo-600 transition-all duration-500 rounded-full ${
                          isPast
                            ? "w-full"
                            : isActive
                            ? "w-full animate-pulse"
                            : "w-0"
                        }`}
                      />
                    </div>
                  )}
                </div>

                {/* Step Body */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <h3
                      className={`text-sm font-bold tracking-tight font-geist transition-colors duration-300 ${
                        isActive ? "text-indigo-600" : "text-zinc-900"
                      }`}
                    >
                      {stage.title}
                    </h3>
                    {isActive && (
                      <span className="relative flex h-1.5 w-1.5 shrink-0">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-indigo-600" />
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] font-mono text-zinc-400">
                    {stage.subtitle}
                  </p>
                  <p
                    className={`text-xs mt-1 leading-relaxed font-geist transition-colors duration-300 ${
                      isActive ? "text-zinc-800 font-medium" : "text-zinc-500"
                    }`}
                  >
                    {stage.summary}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Callout bar below steps */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-between gap-4 rounded-lg bg-indigo-50/60 border border-indigo-100 p-4 sm:px-6">
          <div className="text-left">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-indigo-700 block">
              Ready to see it in action?
            </span>
            <p className="text-xs text-zinc-700 font-geist mt-0.5">
              Start with Stage 1: Build your agent
            </p>
          </div>
          <button
            type="button"
            onClick={onLaunchConsole}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist shrink-0"
          >
            <span>Launch Console &rarr;</span>
          </button>
        </div>
      </section>

      {/* Why Reco Exists: Paradigm Shift Section */}
      <section id="why-reco" className="mx-auto w-full max-w-7xl pt-10 scroll-mt-20 border-t border-zinc-200">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50/70 px-3 py-1 text-xs font-mono font-medium text-indigo-700">
              <Sparkle size={14} weight="fill" />
              <span>THE PARADIGM SHIFT</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 font-geist">
              Why Reco: Beyond Heuristic Prompting
            </h2>
            <p className="text-xs sm:text-sm text-zinc-500 max-w-2xl font-geist leading-relaxed">
              Building reliable AI agents requires moving past fragile &ldquo;vibe-coding.&rdquo; Reco turns agent construction into an automated compiler pipeline with formal verification and mathematical guarantees.
            </p>
          </div>

          <Link
            to="/architecture"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors shrink-0 font-geist"
          >
            <span>Read Full Architecture &amp; Research Monograph</span>
            <ArrowRight size={14} weight="bold" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="p-5 rounded-xl border border-zinc-200 bg-white shadow-2xs space-y-3">
            <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-bold uppercase">
              <Cpu size={16} weight="duotone" />
              <span>Formal DAG Synthesis</span>
            </div>
            <h3 className="text-sm font-bold text-zinc-900 font-geist">
              Guaranteed Acyclic Topologies
            </h3>
            <p className="text-xs text-zinc-500 leading-relaxed font-geist">
              Manual multi-agent architectures often suffer from infinite loops and unbound tools. Reco synthesizes typed DAG contracts and mathematically proves acyclicity in O(|V|+|E|) before any LLM inference begins.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-zinc-200 bg-white shadow-2xs space-y-3">
            <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-bold uppercase">
              <Pulse size={16} weight="duotone" />
              <span>Diagnostic Taxonomy</span>
            </div>
            <h3 className="text-sm font-bold text-zinc-900 font-geist">
              12-Class Failure Attribution
            </h3>
            <p className="text-xs text-zinc-500 leading-relaxed font-geist">
              Rather than guessing why a prompt broke, Reco maps runtime failures to a rigorous 12-category diagnostic taxonomy, synthesizing targeted mutations that fix root causes rather than symptoms.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-zinc-200 bg-white shadow-2xs space-y-3">
            <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-bold uppercase">
              <ShieldCheck size={16} weight="duotone" />
              <span>Air-Gapped Held-Out Gate</span>
            </div>
            <h3 className="text-sm font-bold text-zinc-900 font-geist">
              Zero-Leakage Promotion
            </h3>
            <p className="text-xs text-zinc-500 leading-relaxed font-geist">
              To prevent prompt overfitting, every candidate is evaluated against blind, held-out test partitions secured by SHA-256 test integrity checksums, ensuring genuine generalization before production release.
            </p>
          </div>
        </div>
      </section>

      {/* Live Production Tech Rail */}
      <div className="mx-auto w-full max-w-7xl border-t border-zinc-200/80 pt-6">
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 shrink-0">
            <CheckCircle size={16} weight="fill" className="text-emerald-600" />
            <span className="font-semibold uppercase tracking-wider text-zinc-950 whitespace-nowrap">
              Live Production Stack:
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-x-2.5 gap-y-2">
            {TECH_BADGES.map((tech) => {
              const Icon = tech.Icon;
              return (
                <div
                  key={tech.label}
                  className="flex items-center gap-2 rounded-lg border border-zinc-200/80 bg-white px-3 py-1.5 text-xs shadow-2xs whitespace-nowrap"
                >
                  <Icon size={15} weight="duotone" className="text-indigo-600 shrink-0" />
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

      {/* Anchor Section: Pricing Overview */}
      <section id="pricing" className="mx-auto w-full max-w-7xl pt-8 pb-4 scroll-mt-20 border-t border-zinc-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-600">
              <CreditCard size={15} weight="duotone" />
              <span>Hosted Billing &amp; Plans</span>
            </div>
            <h3 className="text-xl font-bold tracking-tight text-zinc-900 font-geist">
              Simple, transparent pricing for agent engineers
            </h3>
            <p className="text-xs text-zinc-500 max-w-xl font-geist">
              Start with Free local in-memory execution, or upgrade to Pro ($29/mo) for unlimited mutations, cloud lineage persistence, and distributed trace telemetry.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={onLaunchConsole}
              className="px-4 py-2 rounded-lg border border-zinc-200 bg-white text-xs font-semibold text-zinc-800 hover:bg-zinc-50 transition-colors cursor-pointer shadow-xs"
            >
              Start Free (Console)
            </button>
            <button
              type="button"
              onClick={onOpenBilling || onLaunchConsole}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white transition-colors cursor-pointer shadow-xs"
            >
              View Pricing Tiers &rarr;
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
