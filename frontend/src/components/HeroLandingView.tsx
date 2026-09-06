"use client";

import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, useInView, AnimatePresence } from "motion/react";
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
  XCircle,
  Database,
  Broadcast,
  CreditCard,
  GithubLogo,
  Check,
} from "@phosphor-icons/react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

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
  color: string;
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
    color: "indigo",
  },
  {
    id: "RUN",
    num: "02",
    title: "RUN",
    subtitle: "Deterministic execution & 4-axis scorecard",
    summary: "Reco executes your agent against edge-case test suites, measuring accuracy, latency, and cost.",
    Icon: Play,
    tag: "Evaluation",
    color: "violet",
  },
  {
    id: "UNDERSTAND",
    num: "03",
    title: "UNDERSTAND",
    subtitle: "12-category diagnostic root cause analysis",
    summary: "Deep failure analysis maps issues to a 12-category failure taxonomy automatically.",
    Icon: Pulse,
    tag: "Diagnostics",
    color: "blue",
  },
  {
    id: "IMPROVE",
    num: "04",
    title: "IMPROVE",
    subtitle: "Self-reflection, mutation tournament & Pareto frontier",
    summary: "Evolutionary search mutates prompts, tool configs, and verifies invariant rules.",
    Icon: Sparkle,
    tag: "Optimization",
    color: "indigo",
  },
  {
    id: "VALIDATE",
    num: "05",
    title: "VALIDATE",
    subtitle: "Air-gapped held-out promotion gate",
    summary: "Air-gapped held-out validation proves zero leakage before production deployment.",
    Icon: ShieldCheck,
    tag: "Verification",
    color: "emerald",
  },
];

interface TechBadge {
  label: string;
  provider: string;
  detail: string;
  Icon: React.ElementType;
  href?: string;
}

const TECH_BADGES: TechBadge[] = [
  { label: "Inference", provider: "TensorMux", detail: "GLM-4.7-Flash", Icon: Lightning },
  { label: "Observability", provider: "Neatlogs", detail: "Distributed Tracing", Icon: Broadcast },
  { label: "Persistence", provider: "Supabase", detail: "Cloud Ledger", Icon: Database },
  { label: "Monetization", provider: "Dodo Payments", detail: "Pro Tier", Icon: CreditCard },
];

const STAT_TARGETS = [
  { label: "Pipeline Stages", value: 5, suffix: "" },
  { label: "Failure Categories", value: 12, suffix: "" },
  { label: "Scorecard Axes", value: 4, suffix: "" },
  { label: "Optimization Loops", value: 100, suffix: "+" },
];

const RADAR_DATA = [
  { axis: "Accuracy", reco: 94, baseline: 61 },
  { axis: "Reliability", reco: 91, baseline: 58 },
  { axis: "Latency", reco: 88, baseline: 72 },
  { axis: "Cost Eff.", reco: 85, baseline: 65 },
];

const FREE_FEATURES = [
  "5 pipeline stages",
  "Demo benchmark harness",
  "4-axis scorecard",
  "In-memory lineage",
  "GitHub integration",
];

const PRO_FEATURES = [
  "Everything in Free",
  "Unlimited mutations",
  "Cloud lineage persistence",
  "Distributed trace telemetry",
  "Priority TensorMux inference",
  "Supabase experiment ledger",
];

// Counter hook
function useCounter(target: number, duration = 1200, startCount = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!startCount) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration, startCount]);
  return count;
}

// Individual stat counter
const StatCounter: React.FC<{ stat: typeof STAT_TARGETS[0]; started: boolean }> = ({ stat, started }) => {
  const count = useCounter(stat.value, 1000, started);
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-3xl sm:text-4xl font-bold text-zinc-900 font-geist tabular-nums">
        {count}{stat.suffix}
      </span>
      <span className="text-xs text-zinc-500 font-geist text-center leading-tight">{stat.label}</span>
    </div>
  );
};

// Stagger variants
const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export const HeroLandingView: React.FC<HeroLandingViewProps> = ({
  onLaunchConsole,
  onExploreLineage,
  onSelectStage,
  onOpenBilling,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const statsRef = useRef<HTMLDivElement>(null);
  const statsInView = useInView(statsRef, { once: true, margin: "-80px" });

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % PIPELINE_STAGES.length);
    }, 2400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-[90dvh] flex flex-col justify-between py-6 sm:py-10 space-y-16 bg-[#f8f8f7]">

      {/* ── HERO ── */}
      <section className="relative mx-auto w-full max-w-4xl text-center space-y-8 overflow-hidden">
        {/* Gradient bloom */}
        <div
          aria-hidden
          className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full opacity-30"
          style={{ background: "radial-gradient(ellipse at center, #c7d2fe 0%, #e0e7ff 40%, transparent 75%)" }}
        />

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="relative z-10 space-y-7"
        >
          {/* Track badge */}
          <motion.div variants={itemVariants} className="flex justify-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-4 py-1.5 text-xs font-mono font-semibold text-indigo-700 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
              </span>
              TRACK 1: AUTOMATED AGENT ENGINEERING · SYNDICATE BY MAXIMOR
            </span>
          </motion.div>

          {/* Headline */}
          <motion.div variants={itemVariants} className="space-y-3">
            <h1 className="text-4xl sm:text-5xl lg:text-[3.75rem] font-bold tracking-tight text-zinc-900 leading-[1.1] font-geist">
              Build Agents That{" "}
              <span className="relative">
                <span className="relative z-10 text-indigo-600">Actually Improve</span>
                <span
                  aria-hidden
                  className="absolute -inset-x-2 bottom-0 h-3 bg-indigo-100 rounded-sm -z-0"
                />
              </span>{" "}
              Themselves
            </h1>
            <p className="text-base sm:text-lg font-medium text-zinc-400 font-geist">
              Autonomous Agent Engineering System
            </p>
          </motion.div>

          {/* Subtitle */}
          <motion.p
            variants={itemVariants}
            className="mx-auto max-w-2xl text-base sm:text-lg text-zinc-500 leading-relaxed font-normal font-geist"
          >
            From high-level natural language goals to self-improving, Pareto-optimized agent DAGs — with
            closed-loop failure diagnostics, self-reflection memory, and air-gapped held-out verification.
          </motion.p>

          {/* CTAs */}
          <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-center gap-3 pt-1">
            <motion.button
              type="button"
              onClick={onLaunchConsole}
              whileHover={{ scale: 1.03, boxShadow: "0 8px 24px rgba(79,70,229,0.25)" }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 cursor-pointer font-geist"
            >
              <Terminal size={18} weight="bold" />
              Launch Console
              <ArrowRight size={16} weight="bold" />
            </motion.button>

            <motion.a
              href="https://github.com/toufiqfarhan0/reco"
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-5 py-3 text-sm font-semibold text-zinc-900 shadow-sm transition hover:bg-zinc-50 cursor-pointer font-geist"
            >
              <GithubLogo size={18} weight="bold" />
              View on GitHub
            </motion.a>

            <motion.button
              type="button"
              onClick={onExploreLineage}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-5 py-3 text-sm font-semibold text-zinc-700 shadow-sm transition hover:bg-zinc-50 hover:text-zinc-900 cursor-pointer font-geist"
            >
              <GitBranch size={18} weight="duotone" className="text-indigo-600" />
              Explore Evolution Lineage
            </motion.button>
          </motion.div>
        </motion.div>
      </section>

      {/* ── STAT COUNTERS ── */}
      <motion.div
        ref={statsRef}
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="mx-auto w-full max-w-3xl"
      >
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 rounded-2xl border border-zinc-200 bg-white px-6 py-6 shadow-sm">
          {STAT_TARGETS.map((stat) => (
            <StatCounter key={stat.label} stat={stat} started={statsInView} />
          ))}
        </div>
      </motion.div>

      {/* ── 5-STAGE PIPELINE ── */}
      <section id="how-it-works" className="mx-auto w-full max-w-7xl scroll-mt-20">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center max-w-2xl mx-auto mb-10 space-y-3"
        >
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 font-geist">
            How Reco Works — 5 Steps, Zero Config
          </h2>
          <p className="text-sm text-zinc-500 font-geist">
            From natural language goal to production-grade agent in minutes
          </p>
          <div className="flex items-center justify-center pt-1">
            <span className="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-[11px] font-mono text-indigo-700">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
              </span>
              Autonomous Pipeline Cycle: Stage {activeStep + 1} of 5 · {PIPELINE_STAGES[activeStep].title}
            </span>
          </div>
        </motion.div>

        {/* Stage cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
          {PIPELINE_STAGES.map((stage, i) => {
            const isActive = i === activeStep;
            const isPast = i < activeStep;
            const Icon = stage.Icon;
            return (
              <React.Fragment key={stage.id}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.07 }}
                  whileHover={{ y: -4, boxShadow: "0 12px 32px rgba(79,70,229,0.10)" }}
                  className={`relative flex flex-col gap-3 rounded-2xl border p-4 transition-all duration-300 cursor-default overflow-hidden ${
                    isActive
                      ? "border-indigo-400 bg-white shadow-md ring-2 ring-indigo-100"
                      : isPast
                      ? "border-indigo-200 bg-indigo-50/40"
                      : "border-zinc-200 bg-white opacity-70"
                  }`}
                >
                  {/* Top row: circle + connector line */}
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-mono font-bold shrink-0 transition-all duration-300 ${
                        isActive
                          ? "bg-indigo-600 text-white ring-4 ring-indigo-100 scale-110"
                          : isPast
                          ? "bg-indigo-100 text-indigo-700"
                          : "bg-zinc-100 text-zinc-500"
                      }`}
                    >
                      {isPast ? <Check size={14} weight="bold" /> : stage.num}
                    </div>
                    {isActive && (
                      <span className="relative flex h-1.5 w-1.5">
                        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-indigo-600" />
                      </span>
                    )}
                    <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${isActive ? "bg-indigo-100 text-indigo-700" : "bg-zinc-100 text-zinc-500"}`}>
                      {stage.tag}
                    </span>
                  </div>

                  {/* Body */}
                  <div className="space-y-1">
                    <Icon
                      size={22}
                      weight={isActive ? "fill" : "regular"}
                      className={isActive ? "text-indigo-600" : "text-zinc-400"}
                    />
                    <h3 className={`text-sm font-bold tracking-tight font-geist ${isActive ? "text-indigo-700" : "text-zinc-900"}`}>
                      {stage.title}
                    </h3>
                    <p className="text-[11px] font-mono text-zinc-400 leading-snug">{stage.subtitle}</p>
                    <p className={`text-xs mt-1 leading-relaxed font-geist ${isActive ? "text-zinc-800 font-medium" : "text-zinc-500"}`}>
                      {stage.summary}
                    </p>
                  </div>

                  {/* Progress bar at bottom */}
                  {isActive && (
                    <div className="absolute bottom-0 inset-x-0 h-1 bg-indigo-50/60 overflow-hidden">
                      <motion.div
                        key={`stage-progress-${stage.id}`}
                        initial={{ width: 0 }}
                        animate={{ width: "100%" }}
                        transition={{ duration: 2.4, ease: "linear" }}
                        className="h-full bg-indigo-600"
                      />
                    </div>
                  )}
                </motion.div>

                {i < PIPELINE_STAGES.length - 1 && (
                  <div className="hidden md:flex items-center justify-center absolute"
                    style={{ left: `calc(${(i + 1) * 20}% - 8px)`, top: "20px" }}>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* CTA bar */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 rounded-2xl bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-100 p-5 sm:px-7"
        >
          <div className="text-left">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-indigo-700 block">
              Ready to see it in action?
            </span>
            <p className="text-xs text-zinc-600 font-geist mt-0.5">Start with Stage 1: Build your agent</p>
          </div>
          <motion.button
            type="button"
            onClick={onLaunchConsole}
            whileHover={{ scale: 1.04, boxShadow: "0 6px 20px rgba(79,70,229,0.25)" }}
            whileTap={{ scale: 0.97 }}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 text-sm font-semibold shadow-sm transition cursor-pointer font-geist shrink-0"
          >
            Launch Console →
          </motion.button>
        </motion.div>
      </section>

      {/* ── WHY RECO + RADAR CHART ── */}
      <section id="why-reco" className="mx-auto w-full max-w-7xl border-t border-zinc-200 pt-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="space-y-2"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-mono font-semibold text-indigo-700">
              <Sparkle size={13} weight="fill" />
              THE PARADIGM SHIFT
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 font-geist">
              Why Reco: Beyond Heuristic Prompting
            </h2>
            <p className="text-sm text-zinc-500 max-w-xl font-geist leading-relaxed">
              Building reliable AI agents requires moving past fragile "vibe-coding." Reco turns agent construction into an
              automated compiler pipeline with formal verification and mathematical guarantees.
            </p>
          </motion.div>
          <Link
            to="/why-reco"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors shrink-0 font-geist"
          >
            Full Why-Reco Analysis <ArrowRight size={14} weight="bold" />
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Feature cards */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-5">
            {[
              {
                Icon: Cpu,
                tag: "Formal DAG Synthesis",
                title: "Guaranteed Acyclic Topologies",
                body: "Manual multi-agent architectures often suffer from infinite loops. Reco synthesizes typed DAG contracts and mathematically proves acyclicity in O(|V|+|E|) before any LLM inference begins.",
              },
              {
                Icon: Pulse,
                tag: "Diagnostic Taxonomy",
                title: "12-Class Failure Attribution",
                body: "Rather than guessing why a prompt broke, Reco maps runtime failures to a rigorous 12-category diagnostic taxonomy, synthesizing targeted mutations that fix root causes.",
              },
              {
                Icon: ShieldCheck,
                tag: "Air-Gapped Gate",
                title: "Zero-Leakage Promotion",
                body: "Every candidate is evaluated against blind, held-out test partitions secured by SHA-256 checksums, ensuring genuine generalization before production release.",
              },
            ].map((card, i) => (
              <motion.div
                key={card.tag}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                whileHover={{ y: -4, boxShadow: "0 16px 40px rgba(79,70,229,0.10)" }}
                className="group p-5 rounded-2xl border border-zinc-200 bg-white shadow-xs space-y-3 transition-all duration-300 border-l-4 border-l-indigo-500"
              >
                <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-bold uppercase">
                  <card.Icon size={16} weight="duotone" />
                  <span>{card.tag}</span>
                </div>
                <h3 className="text-sm font-bold text-zinc-900 font-geist">{card.title}</h3>
                <p className="text-xs text-zinc-500 leading-relaxed font-geist">{card.body}</p>
              </motion.div>
            ))}
          </div>

          {/* Radar Chart */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="rounded-2xl border border-zinc-200 bg-white shadow-xs p-5 flex flex-col"
          >
            <div className="mb-2">
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-500">
                4-Axis Performance
              </p>
              <h3 className="text-sm font-bold text-zinc-900 font-geist mt-0.5">Reco vs Baseline</h3>
            </div>
            <div className="flex-1 min-h-[180px]">
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={RADAR_DATA} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                  <PolarGrid stroke="#e4e4e7" />
                  <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: "#71717a", fontFamily: "Geist, sans-serif" }} />
                  <Radar name="Reco" dataKey="reco" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.18} strokeWidth={2} />
                  <Radar name="Baseline" dataKey="baseline" stroke="#a1a1aa" fill="#a1a1aa" fillOpacity={0.10} strokeWidth={1.5} strokeDasharray="4 3" />
                  <Tooltip
                    contentStyle={{ fontSize: 11, fontFamily: "Geist Mono, monospace", borderRadius: 8, border: "1px solid #e4e4e7" }}
                    formatter={(v: any) => [`${v}%`]}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center gap-4 mt-2 pt-3 border-t border-zinc-100">
              <span className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-600">
                <span className="h-2.5 w-2.5 rounded-sm bg-indigo-500 opacity-80" /> Reco
              </span>
              <span className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400">
                <span className="h-2.5 w-2.5 rounded-sm bg-zinc-400 opacity-60" /> Baseline
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── LIVE TECH STACK ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto w-full max-w-7xl border-t border-zinc-200/80 pt-8"
      >
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 shrink-0">
            <CheckCircle size={16} weight="fill" className="text-emerald-600" />
            <span className="font-semibold uppercase tracking-wider text-zinc-900">Live Production Stack:</span>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            {TECH_BADGES.map((tech, i) => (
              <motion.div
                key={tech.label}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                whileHover={{ y: -2, boxShadow: "0 4px 16px rgba(79,70,229,0.12)" }}
                className="flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3.5 py-2 text-xs shadow-xs whitespace-nowrap transition-all cursor-default"
              >
                <tech.Icon size={15} weight="duotone" className="text-indigo-600 shrink-0" />
                <span className="text-zinc-400 font-mono text-[11px]">{tech.label}:</span>
                <span className="font-semibold text-zinc-900">{tech.provider}</span>
                <span className="rounded-md bg-zinc-100 px-1.5 py-0.5 font-mono text-[10px] text-zinc-600 border border-zinc-200">
                  {tech.detail}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* ── PRICING ── */}
      <section id="pricing" className="mx-auto w-full max-w-7xl pt-10 pb-6 scroll-mt-20 border-t border-zinc-200">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-center mb-10 space-y-2"
        >
          <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-600">
            <CreditCard size={14} weight="duotone" />
            Hosted Billing & Plans
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 font-geist">
            Simple, transparent pricing
          </h2>
          <p className="text-sm text-zinc-500 max-w-md mx-auto font-geist">
            Start free, upgrade when you need cloud persistence and unlimited mutations.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
          {/* Free */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.05 }}
            whileHover={{ y: -4 }}
            className="relative rounded-2xl border border-zinc-200 bg-white p-7 shadow-xs flex flex-col gap-6 transition-all"
          >
            <div>
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-500 mb-1">Free</p>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-zinc-900 font-geist">$0</span>
                <span className="text-sm text-zinc-400 font-geist">/month</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1 font-geist">No credit card required</p>
            </div>
            <ul className="space-y-2.5 flex-1">
              {FREE_FEATURES.map((f) => (
                <li key={f} className="flex items-center gap-2.5 text-sm text-zinc-700 font-geist">
                  <CheckCircle size={16} weight="fill" className="text-emerald-500 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <motion.button
              type="button"
              onClick={onLaunchConsole}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="w-full rounded-xl border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 py-2.5 text-sm font-semibold text-zinc-900 transition cursor-pointer font-geist"
            >
              Start Free →
            </motion.button>
          </motion.div>

          {/* Pro */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.12 }}
            whileHover={{ y: -4, boxShadow: "0 20px 48px rgba(79,70,229,0.18)" }}
            className="relative rounded-2xl border-2 border-indigo-500 bg-white p-7 shadow-lg flex flex-col gap-6 transition-all"
          >
            {/* Most popular badge */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
              <span className="inline-flex items-center gap-1 rounded-full bg-indigo-600 px-3 py-1 text-[11px] font-mono font-bold text-white shadow-sm">
                <Sparkle size={11} weight="fill" className="text-amber-300" />
                MOST POPULAR
              </span>
            </div>
            <div>
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-indigo-600 mb-1">Pro</p>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-zinc-900 font-geist">$29</span>
                <span className="text-sm text-zinc-400 font-geist">/month</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1 font-geist">Billed monthly via Dodo Payments</p>
            </div>
            <ul className="space-y-2.5 flex-1">
              {PRO_FEATURES.map((f) => (
                <li key={f} className="flex items-center gap-2.5 text-sm text-zinc-700 font-geist">
                  <CheckCircle size={16} weight="fill" className="text-indigo-500 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <motion.button
              type="button"
              onClick={onOpenBilling || onLaunchConsole}
              whileHover={{ scale: 1.03, boxShadow: "0 8px 24px rgba(79,70,229,0.30)" }}
              whileTap={{ scale: 0.97 }}
              className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-700 py-2.5 text-sm font-semibold text-white transition cursor-pointer font-geist shadow-sm"
            >
              Upgrade to Pro →
            </motion.button>
          </motion.div>
        </div>
      </section>
    </div>
  );
};
