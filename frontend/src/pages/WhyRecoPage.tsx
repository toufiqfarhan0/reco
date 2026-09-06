"use client";

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Terminal,
  ArrowRight,
  ArrowLeft,
  GithubLogo,
  CheckCircle,
  WarningCircle,
  XCircle,
  Sparkle,
  ShieldCheck,
  Cpu,
  Play,
  Pulse,
  Database,
  Broadcast,
  CreditCard,
  GitBranch,
  Scales,
  Lock,
  ChartBar,
  Lightning,
  Shield,
  TrendUp,
  Coins,
  Bug,
} from "@phosphor-icons/react";

interface ComparisonRow {
  dimension: string;
  description: string;
  manual: {
    status: "bad" | "neutral" | "good";
    text: string;
  };
  frameworks: {
    status: "bad" | "neutral" | "good";
    text: string;
  };
  reco: {
    status: "good";
    text: string;
    highlight?: boolean;
  };
}

const COMPARISON_DATA: ComparisonRow[] = [
  {
    dimension: "Automated DAG Synthesis",
    description: "Derivation of execution graph topology and node contracts from natural language intent",
    manual: {
      status: "bad",
      text: "None (Hardcoded Python scripts & linear chains)",
    },
    frameworks: {
      status: "neutral",
      text: "Manual wiring (Developer specifies all nodes, edges, & branch conditions)",
    },
    reco: {
      status: "good",
      text: "Autonomous Compiler: Deconstructs goal into typed DAG contracts automatically",
      highlight: true,
    },
  },
  {
    dimension: "Diagnostic Taxonomy",
    description: "Systematic failure categorization and root-cause attribution",
    manual: {
      status: "bad",
      text: "Print statements & unstructured exception strings",
    },
    frameworks: {
      status: "neutral",
      text: "Raw tracebacks & uncaught runtime error logs",
    },
    reco: {
      status: "good",
      text: "12-Category Failure Taxonomy with automated root cause clustering",
      highlight: true,
    },
  },
  {
    dimension: "Mutation Tournaments",
    description: "Iterative architectural candidate exploration & multi-objective Pareto optimization",
    manual: {
      status: "bad",
      text: "Manual trial-and-error prompt edits",
    },
    frameworks: {
      status: "bad",
      text: "None (Static graph definitions require manual rewriting)",
    },
    reco: {
      status: "good",
      text: "Evolutionary tournaments optimizing accuracy, latency & cost simultaneously",
      highlight: true,
    },
  },
  {
    dimension: "Epistemic Memory",
    description: "Accumulation and enforcement of invariant rules across optimization cycles",
    manual: {
      status: "bad",
      text: "Scattered Notion notes & developer mental models",
    },
    frameworks: {
      status: "bad",
      text: "Ephemeral session memory; lost on process exit",
    },
    reco: {
      status: "good",
      text: "Cloud ledger of invariant rules enforcing non-regression across versions",
      highlight: true,
    },
  },
  {
    dimension: "Held-Out Leakage Prevention",
    description: "Strict isolation between optimization evaluation sets and held-out validation suites",
    manual: {
      status: "bad",
      text: "Zero isolation (Prompts are overfitted to the active test cases)",
    },
    frameworks: {
      status: "neutral",
      text: "Ad-hoc manual scripts without air-gapped test sandboxes",
    },
    reco: {
      status: "good",
      text: "Air-gapped held-out promotion gate with zero optimization leakage",
      highlight: true,
    },
  },
  {
    dimension: "Built-in Tracing (Neatlogs)",
    description: "Distributed execution telemetry, flamegraphs, and span profiling",
    manual: {
      status: "bad",
      text: "Custom logging boilerplate & homebrewed wrappers",
    },
    frameworks: {
      status: "neutral",
      text: "Requires 3rd-party vendor setup (LangSmith / Arize) with extra costs",
    },
    reco: {
      status: "good",
      text: "Native Neatlogs distributed tracing & span analytics built-in",
      highlight: true,
    },
  },
  {
    dimension: "Cloud Persistence & Multi-Tenant Ledger (Supabase)",
    description: "Durable PostgreSQL ledger for immutable versioned DAGs, candidate lineage, and tenant isolation",
    manual: {
      status: "bad",
      text: "Local scratch files or SQLite wiped on container restarts",
    },
    frameworks: {
      status: "bad",
      text: "Ephemeral in-memory state or unauthenticated local checkpoints",
    },
    reco: {
      status: "good",
      text: "Supabase PostgreSQL cloud ledger with Row-Level Security (RLS) & 1-Click Judge Demo Auth",
      highlight: true,
    },
  },
  {
    dimension: "Billing & Monetization (Dodo Payments)",
    description: "Integrated subscription tiers, metered token gates, and checkout portals",
    manual: {
      status: "bad",
      text: "Custom billing code & manual webhook handling",
    },
    frameworks: {
      status: "bad",
      text: "None (Out of scope for runtime orchestration libraries)",
    },
    reco: {
      status: "good",
      text: "First-class Dodo Payments hosted portal, tier entitlements & credit metering",
      highlight: true,
    },
  },
];

export const WhyRecoPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeCaseTab, setActiveCaseTab] = useState<"problem" | "solution" | "diff">("solution");

  const handleLaunchConsole = () => {
    navigate("/console");
  };

  const handleExploreCaseStudy = () => {
    navigate("/console?stage=4&preset=financial_reconciliation");
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
      {/* Slim Fixed Top Navbar */}
      <nav className="sticky top-0 z-50 h-14 bg-white/95 backdrop-blur-sm border-b border-zinc-200 px-4 sm:px-6 lg:px-8 flex items-center justify-between shadow-2xs">
        {/* Left: Brand + Track 1 Badge */}
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white border border-zinc-200 shadow-xs overflow-hidden shrink-0 group-hover:border-indigo-300 transition-colors">
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
            <span className="font-geist font-bold text-zinc-900 text-lg leading-none">
              Reco
            </span>
          </Link>

          <div className="h-4 w-px bg-zinc-200 hidden sm:block" />

          <div className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-indigo-600" />
            <span className="text-xs font-mono font-medium text-zinc-700 hidden sm:inline">
              Track 1
            </span>
            <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-mono font-medium text-indigo-700">
              Autonomous Agent Compiler
            </span>
          </div>
        </div>

        {/* Right: Anchors + GitHub + Launch Console CTA */}
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-5 text-xs font-medium text-zinc-600 font-geist">
            <Link
              to="/"
              className="hover:text-zinc-900 transition-colors cursor-pointer flex items-center gap-1"
            >
              <ArrowLeft size={13} weight="bold" />
              <span>Home</span>
            </Link>
            <Link
              to="/architecture"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              Architecture
            </Link>
            <span className="text-indigo-600 font-semibold px-2 py-1 rounded-md bg-indigo-50/70 border border-indigo-100">
              Why Reco?
            </span>
            <a
              href="/#pricing"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              Pricing
            </a>
          </div>

          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center h-8 w-8 rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors shadow-2xs"
            title="View on GitHub"
            aria-label="View on GitHub"
          >
            <GithubLogo size={17} weight="bold" />
          </a>

          <button
            type="button"
            onClick={handleLaunchConsole}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white px-4 py-2 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist"
          >
            <Terminal size={15} weight="bold" />
            <span>Launch Console</span>
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-20">
        {/* Hero Section */}
        <section className="text-center space-y-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white px-4 py-1.5 text-xs font-mono font-medium text-indigo-700 shadow-2xs">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
            </span>
            <span>THE PARADIGM SHIFT: PROMPT GUESSWORK &rarr; AGENT COMPILER</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-950 font-geist leading-[1.15]">
            Why Reco?
            <span className="block text-2xl sm:text-3xl lg:text-4xl font-semibold text-zinc-500 mt-3 font-geist">
              The Shift from Prompt Guesswork to Automated Agent Engineering
            </span>
          </h1>

          <p className="mx-auto max-w-3xl text-base sm:text-lg text-zinc-600 leading-relaxed font-geist">
            Building reliable compound AI systems should operate like an optimizing compiler—not prompt roulette.
            95% of AI agents break in production because manual prompt tweaking and brittle framework orchestration
            cannot diagnose root causes or guarantee zero regression. Reco automates synthesis, evolutionary mutation
            tournaments, epistemic memory, and air-gapped held-out verification.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <button
              type="button"
              onClick={handleLaunchConsole}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 active:scale-[0.98] cursor-pointer font-geist"
            >
              <Terminal size={18} weight="bold" />
              <span>Launch Interactive Console</span>
              <ArrowRight size={16} weight="bold" />
            </button>

            <a
              href="#matrix"
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-5 py-3 text-sm font-semibold text-zinc-800 shadow-xs transition-all hover:bg-zinc-50 active:scale-[0.98] cursor-pointer font-geist"
            >
              <Scales size={18} weight="duotone" className="text-indigo-600" />
              <span>Compare Frameworks</span>
            </a>

            <button
              type="button"
              onClick={handleExploreCaseStudy}
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-5 py-3 text-sm font-semibold text-zinc-700 shadow-xs transition-all hover:bg-zinc-50 hover:text-zinc-900 active:scale-[0.98] cursor-pointer font-geist"
            >
              <GitBranch size={18} weight="duotone" className="text-indigo-600" />
              <span>Explore Financial Case Study</span>
            </button>
          </div>

          {/* Key Value Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 text-left">
            <div className="rounded-xl border border-zinc-200/90 bg-white p-4 shadow-2xs">
              <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-semibold">
                <CheckCircle size={16} weight="fill" />
                <span>100% Deterministic</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1 font-geist">
                Strict input/output JSON contracts on all DAG nodes
              </p>
            </div>
            <div className="rounded-xl border border-zinc-200/90 bg-white p-4 shadow-2xs">
              <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-semibold">
                <Pulse size={16} weight="bold" />
                <span>12-Axis Diagnostics</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1 font-geist">
                Automated root cause attribution on every failure
              </p>
            </div>
            <div className="rounded-xl border border-zinc-200/90 bg-white p-4 shadow-2xs">
              <div className="flex items-center gap-2 text-emerald-600 font-mono text-xs font-semibold">
                <ShieldCheck size={16} weight="fill" />
                <span>0.0% Regressions</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1 font-geist">
                Guaranteed by persistent Epistemic Invariant checks
              </p>
            </div>
            <div className="rounded-xl border border-zinc-200/90 bg-white p-4 shadow-2xs">
              <div className="flex items-center gap-2 text-indigo-600 font-mono text-xs font-semibold">
                <Lock size={16} weight="bold" />
                <span>Air-Gapped Eval</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1 font-geist">
                Strict mathematical isolation of held-out splits
              </p>
            </div>
          </div>
        </section>

        {/* Section 1: The Agent Engineering Crisis (The "Prompt & Pray" Trap) */}
        <section className="space-y-8">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-rose-600">
              <WarningCircle size={15} weight="bold" />
              <span>The Industry Crisis</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-950 font-geist">
              Why 95% of AI Agents Break in Production: The &ldquo;Prompt &amp; Pray&rdquo; Trap
            </h2>
            <p className="text-sm text-zinc-600 font-geist leading-relaxed">
              Teams build quick prototypes in a weekend, then spend months in an endless loop of manual prompt tweaking.
              Without systematic compilation, compound AI systems inevitably suffer from four fatal failure modes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Crisis Item 1 */}
            <div className="rounded-2xl border border-rose-200/80 bg-rose-50/30 p-6 space-y-3 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-100 text-rose-700 font-mono text-sm font-bold">
                  01
                </span>
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-rose-600 bg-rose-100/70 px-2.5 py-0.5 rounded-full border border-rose-200">
                  Fragile Heuristic
                </span>
              </div>
              <h3 className="text-lg font-bold text-zinc-900 font-geist">
                Manual Prompt Tweaking
              </h3>
              <p className="text-xs sm:text-sm text-zinc-600 font-geist leading-relaxed">
                English is not a formal programming language. Developers continuously rewrite system prompts with paragraphs
                of instructions and negative examples, hoping the LLM complies. But fixing prompt behavior for Case A
                almost always quietly degrades Case B and Case C.
              </p>
              <div className="rounded-lg bg-white/80 border border-rose-200 p-3 text-xs font-mono text-rose-800">
                &ldquo;Please, I beg you, never output currency symbols unless specified...&rdquo; &rarr; Breaks 2 days later on currency edge-cases.
              </div>
            </div>

            {/* Crisis Item 2 */}
            <div className="rounded-2xl border border-rose-200/80 bg-rose-50/30 p-6 space-y-3 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-100 text-rose-700 font-mono text-sm font-bold">
                  02
                </span>
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-rose-600 bg-rose-100/70 px-2.5 py-0.5 rounded-full border border-rose-200">
                  Brittle Plumbing
                </span>
              </div>
              <h3 className="text-lg font-bold text-zinc-900 font-geist">
                Brittle Tool Glue Code
              </h3>
              <p className="text-xs sm:text-sm text-zinc-600 font-geist leading-relaxed">
                Frameworks like LangChain or CrewAI rely on manually hardcoded Python glue. Tool signatures change,
                APIs return unexpected whitespace, floating-point numbers format differently, or nested JSON schemas fail.
                The agent crashes with unhandled tracebacks instead of self-healing.
              </p>
              <div className="rounded-lg bg-white/80 border border-rose-200 p-3 text-xs font-mono text-rose-800">
                TypeError: float() argument must be a string or a real number, not &apos;dict&apos;
              </div>
            </div>

            {/* Crisis Item 3 */}
            <div className="rounded-2xl border border-rose-200/80 bg-rose-50/30 p-6 space-y-3 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-100 text-rose-700 font-mono text-sm font-bold">
                  03
                </span>
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-rose-600 bg-rose-100/70 px-2.5 py-0.5 rounded-full border border-rose-200">
                  Hidden Decay
                </span>
              </div>
              <h3 className="text-lg font-bold text-zinc-900 font-geist">
                Silent Regression
              </h3>
              <p className="text-xs sm:text-sm text-zinc-600 font-geist leading-relaxed">
                Without a persistent invariant ledger, teams cannot track regressions. An engineer updates a prompt
                to handle a new customer edge-case, and 4 previously working test benchmarks regress unnoticed until
                production traffic catches fire.
              </p>
              <div className="rounded-lg bg-white/80 border border-rose-200 p-3 text-xs font-mono text-rose-800">
                Fix applied for Case 14 &bull; Regressed Cases 2, 7, and 9 (0 alerts triggered)
              </div>
            </div>

            {/* Crisis Item 4 */}
            <div className="rounded-2xl border border-rose-200/80 bg-rose-50/30 p-6 space-y-3 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-100 text-rose-700 font-mono text-sm font-bold">
                  04
                </span>
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-rose-600 bg-rose-100/70 px-2.5 py-0.5 rounded-full border border-rose-200">
                  Test Contamination
                </span>
              </div>
              <h3 className="text-lg font-bold text-zinc-900 font-geist">
                Zero Held-Out Validation
              </h3>
              <p className="text-xs sm:text-sm text-zinc-600 font-geist leading-relaxed">
                Most agent evaluations test on the exact same synthetic samples used during prompt development.
                This severe data leakage creates the false illusion of 90%+ reliability in notebooks, which collapses
                to 15-20% when faced with genuine out-of-distribution user inputs.
              </p>
              <div className="rounded-lg bg-white/80 border border-rose-200 p-3 text-xs font-mono text-rose-800">
                Optimization Eval: 95% &bull; Live Held-Out Production: 16.7% (Catastrophic Overfit)
              </div>
            </div>
          </div>

          {/* Contrast Callout */}
          <div className="rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50/90 via-white to-indigo-50/40 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-1.5 text-xs font-mono font-bold uppercase tracking-wider text-indigo-700">
                <Sparkle size={15} weight="fill" />
                <span>The Reco Solution</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-zinc-900 font-geist">
                Closed-Loop Automated Agent Engineering
              </h3>
              <p className="text-xs sm:text-sm text-zinc-600 font-geist">
                Reco treats agent building as automated compilation: Goal &rarr; Synthesize DAG &rarr; Deterministic Execution
                &rarr; 12-Category Failure Taxonomy &rarr; Mutation Tournament &rarr; Air-Gapped Held-Out Verification.
              </p>
            </div>
            <button
              type="button"
              onClick={handleLaunchConsole}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist shrink-0"
            >
              <span>Compile Your First Agent &rarr;</span>
            </button>
          </div>
        </section>

        {/* Section 2: Competitive Benchmark Comparison Matrix */}
        <section id="matrix" className="space-y-8 scroll-mt-20">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-600">
              <Scales size={15} weight="duotone" />
              <span>Competitive Benchmark Matrix</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-950 font-geist">
              How Reco Compares to Existing Frameworks
            </h2>
            <p className="text-sm text-zinc-600 font-geist leading-relaxed">
              Why manual prompt engineering and static orchestration frameworks fall short when building production-critical AI agents.
            </p>
          </div>

          {/* Structured Responsive Matrix Table */}
          <div className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white shadow-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50/80">
                  <th className="py-4 px-5 text-xs font-mono font-bold uppercase tracking-wider text-zinc-600 w-1/4">
                    Capability / Dimension
                  </th>
                  <th className="py-4 px-5 text-xs font-mono font-semibold uppercase tracking-wider text-zinc-500 w-1/4">
                    Manual Prompt Engineering
                  </th>
                  <th className="py-4 px-5 text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700 w-1/4">
                    Orchestration Frameworks
                    <span className="block text-[10px] font-normal normal-case text-zinc-400">
                      LangGraph, CrewAI, AutoGen
                    </span>
                  </th>
                  <th className="py-4 px-5 text-xs font-mono font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50/70 border-l border-indigo-200 w-1/4">
                    <div className="flex items-center gap-1.5">
                      <Sparkle size={14} weight="fill" className="text-indigo-600" />
                      <span>Reco Autonomous Compiler</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 text-xs sm:text-sm font-geist">
                {COMPARISON_DATA.map((row, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50/50 transition-colors">
                    {/* Dimension Name & Description */}
                    <td className="py-4 px-5 align-top">
                      <div className="font-semibold text-zinc-900 font-geist">
                        {row.dimension}
                      </div>
                      <div className="text-[11px] text-zinc-500 mt-0.5 leading-relaxed font-geist">
                        {row.description}
                      </div>
                    </td>

                    {/* Manual */}
                    <td className="py-4 px-5 align-top text-zinc-600">
                      <div className="flex items-start gap-2">
                        {row.manual.status === "bad" ? (
                          <XCircle size={16} weight="fill" className="text-rose-500 shrink-0 mt-0.5" />
                        ) : (
                          <span className="size-2 rounded-full bg-zinc-400 shrink-0 mt-1.5" />
                        )}
                        <span className="text-xs leading-relaxed">{row.manual.text}</span>
                      </div>
                    </td>

                    {/* Orchestration Frameworks */}
                    <td className="py-4 px-5 align-top text-zinc-700">
                      <div className="flex items-start gap-2">
                        {row.frameworks.status === "bad" ? (
                          <XCircle size={16} weight="fill" className="text-rose-500 shrink-0 mt-0.5" />
                        ) : row.frameworks.status === "neutral" ? (
                          <WarningCircle size={16} weight="fill" className="text-amber-500 shrink-0 mt-0.5" />
                        ) : (
                          <CheckCircle size={16} weight="fill" className="text-emerald-500 shrink-0 mt-0.5" />
                        )}
                        <span className="text-xs leading-relaxed">{row.frameworks.text}</span>
                      </div>
                    </td>

                    {/* Reco */}
                    <td className="py-4 px-5 align-top bg-indigo-50/30 border-l border-indigo-200 text-zinc-900 font-medium">
                      <div className="flex items-start gap-2">
                        <CheckCircle size={17} weight="fill" className="text-indigo-600 shrink-0 mt-0.5" />
                        <span className="text-xs leading-relaxed text-indigo-950 font-semibold">
                          {row.reco.text}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 3: Empirical Benchmark Results & ROI */}
        <section className="space-y-8">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-emerald-600">
              <TrendUp size={15} weight="bold" />
              <span>Empirical Benchmark Results</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-950 font-geist">
              Empirical ROI &amp; Performance Multipliers
            </h2>
            <p className="text-sm text-zinc-600 font-geist leading-relaxed">
              Measured improvements on production-grade reconciliation and anomaly test suites across multiple mutation generations.
            </p>
          </div>

          {/* 4 Empirical Data Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Accuracy */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500">
                <span className="uppercase tracking-wider">Target Accuracy</span>
                <span className="rounded bg-emerald-50 text-emerald-700 px-2 py-0.5 text-[10px] font-bold border border-emerald-200">
                  +83.3% Lift
                </span>
              </div>
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-zinc-400 line-through font-mono">16.7%</span>
                  <ArrowRight size={16} className="text-indigo-600" />
                  <span className="text-3xl sm:text-4xl font-extrabold text-zinc-950 font-mono">100.0%</span>
                </div>
                <p className="text-xs text-zinc-500 font-geist">
                  From naive string matching baseline (1/6 passing) to 100% verifier-guarded DAG.
                </p>
              </div>
              <div className="pt-2 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-mono text-emerald-600">
                <CheckCircle size={14} weight="fill" />
                <span>Zero unhandled edge cases</span>
              </div>
            </div>

            {/* Card 2: Latency */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500">
                <span className="uppercase tracking-wider">P95 Latency</span>
                <span className="rounded bg-indigo-50 text-indigo-700 px-2 py-0.5 text-[10px] font-bold border border-indigo-200">
                  -20% Latency
                </span>
              </div>
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-zinc-400 line-through font-mono">100ms</span>
                  <ArrowRight size={16} className="text-indigo-600" />
                  <span className="text-3xl sm:text-4xl font-extrabold text-zinc-950 font-mono">80.0ms</span>
                </div>
                <p className="text-xs text-zinc-500 font-geist">
                  Pruned redundant reasoning hops and streamlined DAG node execution paths.
                </p>
              </div>
              <div className="pt-2 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-mono text-indigo-600">
                <Lightning size={14} weight="fill" />
                <span>Faster sub-second turnarounds</span>
              </div>
            </div>

            {/* Card 3: Token Cost */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500">
                <span className="uppercase tracking-wider">Inference Cost</span>
                <span className="rounded bg-indigo-50 text-indigo-700 px-2 py-0.5 text-[10px] font-bold border border-indigo-200">
                  -18% Spend
                </span>
              </div>
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-zinc-400 line-through font-mono">$0.005</span>
                  <ArrowRight size={16} className="text-indigo-600" />
                  <span className="text-3xl sm:text-4xl font-extrabold text-zinc-950 font-mono">$0.0041</span>
                </div>
                <p className="text-xs text-zinc-500 font-geist">
                  Typed validation prevents bloated hallucinated re-tries and verbose prompt tokens.
                </p>
              </div>
              <div className="pt-2 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-mono text-indigo-600">
                <Coins size={14} weight="bold" />
                <span>Direct TensorMux savings</span>
              </div>
            </div>

            {/* Card 4: Regression Rate */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-500">
                <span className="uppercase tracking-wider">Regression Rate</span>
                <span className="rounded bg-emerald-50 text-emerald-700 px-2 py-0.5 text-[10px] font-bold border border-emerald-200">
                  Guaranteed
                </span>
              </div>
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl sm:text-4xl font-extrabold text-emerald-600 font-mono">0.0%</span>
                </div>
                <p className="text-xs text-zinc-500 font-geist">
                  Protected by Epistemic Invariant rules stored in the persistent cloud ledger.
                </p>
              </div>
              <div className="pt-2 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] font-mono text-emerald-600">
                <ShieldCheck size={14} weight="fill" />
                <span>Epistemic Invariant Lockdown</span>
              </div>
            </div>
          </div>

          {/* ROI Breakdown Callout */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 space-y-4 shadow-xs">
            <h3 className="text-lg font-bold text-zinc-900 font-geist flex items-center gap-2">
              <ChartBar size={18} weight="duotone" className="text-indigo-600" />
              <span>The Engineering ROI of Compiling Agents vs Guessing Prompts</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs sm:text-sm font-geist">
              <div className="space-y-1.5 border-l-2 border-indigo-600 pl-3">
                <div className="font-semibold text-zinc-900">40+ Engineering Hours Saved</div>
                <p className="text-zinc-500 text-xs leading-relaxed">
                  Eliminate weeks of manual edge-case debugging, script tweaking, and prompt rewrites with automated DAG evolution.
                </p>
              </div>
              <div className="space-y-1.5 border-l-2 border-indigo-600 pl-3">
                <div className="font-semibold text-zinc-900">Zero Production Rollbacks</div>
                <p className="text-zinc-500 text-xs leading-relaxed">
                  Air-gapped validation gates ensure only candidates beating the Pareto frontier across all splits ever deploy.
                </p>
              </div>
              <div className="space-y-1.5 border-l-2 border-indigo-600 pl-3">
                <div className="font-semibold text-zinc-900">Auditable Cloud Traceability</div>
                <p className="text-zinc-500 text-xs leading-relaxed">
                  Every node execution, failure classification, and mutation diff is stored in Supabase with Neatlogs flamegraphs.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4: Real-World Failure Cluster Case Study */}
        <section className="space-y-8">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-600">
              <Bug size={15} weight="duotone" />
              <span>Case Study Deep-Dive</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-950 font-geist">
              Real-World Failure Cluster: Financial Invoice Reconciliation
            </h2>
            <p className="text-sm text-zinc-600 font-geist leading-relaxed">
              How Reco automatically diagnosed and repaired a multi-million-dollar reconciliation problem that broke every naive LLM chain.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-white overflow-hidden shadow-xs">
            {/* Case Study Header & Navigation Tabs */}
            <div className="border-b border-zinc-200 bg-zinc-50/60 p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
                  Domain: Financial Reconciliation &bull; Stripe vs Internal ERP
                </span>
                <h3 className="text-base font-bold text-zinc-900 font-geist">
                  The Dual-Ledger Currency Drift &amp; Casing Anomaly
                </h3>
              </div>

              <div className="flex items-center gap-1.5 bg-zinc-200/70 p-1 rounded-xl">
                <button
                  type="button"
                  onClick={() => setActiveCaseTab("problem")}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer font-geist ${
                    activeCaseTab === "problem"
                      ? "bg-white text-zinc-900 shadow-2xs font-semibold"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  1. The Naive Failures
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCaseTab("solution")}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer font-geist ${
                    activeCaseTab === "solution"
                      ? "bg-white text-zinc-900 shadow-2xs font-semibold"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  2. Reco Autonomous Evolution
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCaseTab("diff")}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all cursor-pointer font-geist ${
                    activeCaseTab === "diff"
                      ? "bg-white text-zinc-900 shadow-2xs font-semibold"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  3. Verifier Node Diff
                </button>
              </div>
            </div>

            {/* Case Study Tab Content */}
            <div className="p-6 sm:p-8">
              {activeCaseTab === "problem" && (
                <div className="space-y-6">
                  <div className="rounded-xl border border-rose-200 bg-rose-50/40 p-4 space-y-2">
                    <div className="flex items-center gap-2 text-rose-700 font-mono text-xs font-bold">
                      <XCircle size={16} weight="fill" />
                      <span>Baseline V0 Architecture Failed 5 out of 6 Cases (16.7% Accuracy)</span>
                    </div>
                    <p className="text-xs text-zinc-700 font-geist leading-relaxed">
                      A naive LLM agent relying on exact ID and amount matching without normalization broke across multiple real-world formatting variations.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-geist">
                    <div className="border border-zinc-200 rounded-xl p-4 space-y-2">
                      <span className="font-mono text-[11px] font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
                        Case #reco_opt_002: ID Casing Mismatch
                      </span>
                      <p className="text-zinc-700">
                        Stripe webhook sent <code className="font-mono bg-zinc-100 px-1 py-0.5 rounded text-zinc-900">tx1003</code>,
                        while ERP ledger logged <code className="font-mono bg-zinc-100 px-1 py-0.5 rounded text-zinc-900">TX1003</code>.
                      </p>
                      <p className="text-zinc-500 text-[11px]">
                        Strict equality failed, creating false discrepancy tickets for accounting staff.
                      </p>
                    </div>

                    <div className="border border-zinc-200 rounded-xl p-4 space-y-2">
                      <span className="font-mono text-[11px] font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
                        Case #reco_opt_003: Floating-Point Currency Drift
                      </span>
                      <p className="text-zinc-700">
                        Source ledger contained string <code className="font-mono bg-zinc-100 px-1 py-0.5 rounded text-zinc-900">&quot;$1,250.00&quot;</code>,
                        target had float <code className="font-mono bg-zinc-100 px-1 py-0.5 rounded text-zinc-900">1250.00</code>.
                      </p>
                      <p className="text-zinc-500 text-[11px]">
                        String comparison failed; LLM hallucinated an unpaid balance instead of normalizing symbols.
                      </p>
                    </div>

                    <div className="border border-zinc-200 rounded-xl p-4 space-y-2">
                      <span className="font-mono text-[11px] font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
                        Case #reco_opt_004: Target Duplicate Ingestion
                      </span>
                      <p className="text-zinc-700">
                        Payment gateway retried webhook, generating duplicate row for <code className="font-mono bg-zinc-100 px-1 py-0.5 rounded text-zinc-900">TX1005</code>.
                      </p>
                      <p className="text-zinc-500 text-[11px]">
                        Naive matcher stopped at the first match, missing duplicate double-billing.
                      </p>
                    </div>

                    <div className="border border-zinc-200 rounded-xl p-4 space-y-2">
                      <span className="font-mono text-[11px] font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-100">
                        Case #reco_opt_006: Whitespace Key Padding
                      </span>
                      <p className="text-zinc-700">
                        Export CSV had trailing space in key <code className="font-mono bg-zinc-100 px-1 py-0.5 rounded text-zinc-900">&quot;TX1007 &quot;</code>.
                      </p>
                      <p className="text-zinc-500 text-[11px]">
                        Exact dictionary lookups failed silently, leaving customer account un-reconciled.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeCaseTab === "solution" && (
                <div className="space-y-6">
                  <div className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-4 space-y-2">
                    <div className="flex items-center gap-2 text-indigo-700 font-mono text-xs font-bold">
                      <Sparkle size={16} weight="fill" />
                      <span>Reco Closed-Loop Compiler Synthesized Candidate C &rarr; 100.0% Accuracy</span>
                    </div>
                    <p className="text-xs text-zinc-700 font-geist leading-relaxed">
                      Without human intervention, Reco categorized the failures, mutated the tool pipeline, and inserted a Verifier Node with Epistemic Invariants.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="rounded-xl border border-zinc-200 p-4 space-y-2">
                      <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase">
                        Phase 1 &bull; Diagnostic
                      </span>
                      <h4 className="text-xs font-bold text-zinc-900 font-geist">
                        12-Category Attribution
                      </h4>
                      <p className="text-xs text-zinc-500 font-geist">
                        Failures clustered under <code className="font-mono text-zinc-800 bg-zinc-100 px-1 py-0.5 rounded">DATA_FORMAT_MISMATCH</code> and <code className="font-mono text-zinc-800 bg-zinc-100 px-1 py-0.5 rounded">SCHEMA_VIOLATION</code>.
                      </p>
                    </div>

                    <div className="rounded-xl border border-zinc-200 p-4 space-y-2">
                      <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase">
                        Phase 2 &bull; Tool Mutation
                      </span>
                      <h4 className="text-xs font-bold text-zinc-900 font-geist">
                        Candidate B (83.3%)
                      </h4>
                      <p className="text-xs text-zinc-500 font-geist">
                        Replaced <code className="font-mono text-zinc-800 bg-zinc-100 px-1 py-0.5 rounded">exact_reconcile</code> with <code className="font-mono text-zinc-800 bg-zinc-100 px-1 py-0.5 rounded">smart_reconcile</code> for whitespace and currency stripping.
                      </p>
                    </div>

                    <div className="rounded-xl border border-indigo-200 bg-indigo-50/30 p-4 space-y-2">
                      <span className="text-[10px] font-mono font-bold text-indigo-700 uppercase">
                        Phase 3 &bull; Verifier Guard
                      </span>
                      <h4 className="text-xs font-bold text-indigo-950 font-geist">
                        Candidate C (100.0%)
                      </h4>
                      <p className="text-xs text-zinc-600 font-geist">
                        Inserted dedicated <code className="font-mono text-indigo-800 bg-indigo-100/70 px-1 py-0.5 rounded">verifier_node</code> and <code className="font-mono text-indigo-800 bg-indigo-100/70 px-1 py-0.5 rounded">json_validator</code> to catch duplicate charges.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeCaseTab === "diff" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-zinc-700 uppercase tracking-wider">
                      Synthesized Architecture Diff (V0 Baseline &rarr; V2 Evolved)
                    </span>
                    <span className="text-xs font-mono text-indigo-600">
                      +1 Verifier Node &bull; +1 Schema Invariant Rule
                    </span>
                  </div>

                  <div className="rounded-xl bg-zinc-900 p-4 text-xs font-mono text-zinc-100 overflow-x-auto space-y-1">
                    <div className="text-zinc-500">// DAG Node Execution Topology Evolution</div>
                    <div className="text-rose-400">- input_node &rarr; tool_exact_reconcile &rarr; reasoning_node &rarr; output_node</div>
                    <div className="text-emerald-400 font-semibold">+ input_node &rarr; tool_smart_reconcile &rarr; verifier_node [JSON Validator] &rarr; reasoning_node &rarr; output_node</div>
                    <div className="pt-2 text-zinc-400">// Invariant Rule Applied to Epistemic Ledger:</div>
                    <div className="text-indigo-300">RULE #INV-004: If duplicate transaction IDs detected in target, emit status=&apos;duplicate_detected&apos; with severity=&apos;HIGH&apos;</div>
                  </div>
                </div>
              )}
            </div>

            {/* Action footer */}
            <div className="border-t border-zinc-200 bg-zinc-50/70 p-4 sm:px-6 flex items-center justify-between">
              <span className="text-xs font-geist text-zinc-500">
                Inspect the full candidate evolution tournament in the live interactive console.
              </span>
              <button
                type="button"
                onClick={handleExploreCaseStudy}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 cursor-pointer font-geist"
              >
                <span>Open Financial Lineage in Console &rarr;</span>
              </button>
            </div>
          </div>
        </section>

        {/* Section 5: Enterprise-Ready Architecture */}
        <section className="space-y-8">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-600">
              <Shield size={15} weight="duotone" />
              <span>Production Reliability</span>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-zinc-950 font-geist">
              Enterprise-Grade Foundation Built for Scale
            </h2>
            <p className="text-sm text-zinc-600 font-geist leading-relaxed">
              Reco is engineered from the ground up to meet enterprise security, compliance, and multi-tenant operational requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {/* Feature 1 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 space-y-3 shadow-xs">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                <Lock size={20} weight="duotone" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 font-geist">
                Air-Gapped Test Isolation
              </h3>
              <p className="text-xs text-zinc-600 font-geist leading-relaxed">
                Candidate mutation search runs strictly on training optimization splits. The held-out validation suite
                is mathematically isolated in an air-gapped harness, preventing data contamination and prompt leakage.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 space-y-3 shadow-xs">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                <Database size={20} weight="duotone" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 font-geist">
                Supabase Multi-Tenant RLS
              </h3>
              <p className="text-xs text-zinc-600 font-geist leading-relaxed">
                Organizations benefit from granular Row-Level Security (RLS) and GoTrue JWT authentication.
                Every epistemic memory rule, candidate lineage graph, and scorecard is cryptographically tenant-isolated.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 space-y-3 shadow-xs">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                <Broadcast size={20} weight="duotone" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 font-geist">
                Neatlogs Distributed Tracing
              </h3>
              <p className="text-xs text-zinc-600 font-geist leading-relaxed">
                Native distributed telemetry captures every node invocation, token budget, latency profile,
                and failure diagnostic. Real-time flamegraphs enable sub-millisecond bottleneck isolation.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 space-y-3 shadow-xs">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                <Lightning size={20} weight="duotone" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 font-geist">
                SLA &amp; Cost Constraints
              </h3>
              <p className="text-xs text-zinc-600 font-geist leading-relaxed">
                Specify hard P95 latency bounds and maximum token budgets. Reco’s Pareto tournament automatically
                disqualifies candidate architectures that violate strict enterprise SLA thresholds.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 space-y-3 shadow-xs">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                <CreditCard size={20} weight="duotone" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 font-geist">
                Dodo Payments Monetization
              </h3>
              <p className="text-xs text-zinc-600 font-geist leading-relaxed">
                Built-in hosted checkout, customer portal, and tiered monetization. Gate Pro capabilities (unlimited mutations,
                cross-session persistence) with seamless global compliance and subscription lifecycles.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 space-y-3 shadow-xs">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600">
                <ShieldCheck size={20} weight="duotone" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 font-geist">
                Deterministic Output Verification
              </h3>
              <p className="text-xs text-zinc-600 font-geist leading-relaxed">
                Every agent graph synthesized by Reco incorporates strict typed schema verification nodes,
                preventing malformed payloads, unescaped quotes, or missing properties from reaching downstream systems.
              </p>
            </div>
          </div>

          {/* Spotlight: Why We Added Supabase */}
          <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50/70 via-white to-emerald-50/30 p-6 sm:p-8 space-y-4 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs">
                  <Database size={22} weight="fill" />
                </div>
                <div>
                  <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-emerald-700">
                    Architectural Deep-Dive
                  </div>
                  <h3 className="text-xl font-bold text-zinc-950 font-geist">
                    Why We Added Supabase: The Cloud Ledger for Autonomous Agent Evolution
                  </h3>
                </div>
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-mono font-medium text-emerald-800 bg-emerald-100/80 px-2.5 py-1 rounded-md border border-emerald-200 self-start sm:self-auto">
                <span>PostgreSQL 16 + GoTrue RLS</span>
              </span>
            </div>

            <p className="text-xs sm:text-sm text-zinc-600 font-geist leading-relaxed">
              Autonomous agent systems fail in production when they treat agent memory as ephemeral in-memory variables or local flat files. Container restarts, worker autoscaling, and blue-green redeployments silently wipe candidate mutation histories, Pareto evaluation metrics, and postmortems. We added Supabase to serve as an immutable cloud ledger with mathematical rollback and cryptographic multi-tenancy.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-3.5 rounded-xl bg-white border border-emerald-100 space-y-1.5 shadow-2xs">
                <div className="text-xs font-bold text-zinc-900 font-geist flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-emerald-600" />
                  Immutable Versioned DAGs
                </div>
                <p className="text-[11px] text-zinc-500 font-geist leading-relaxed">
                  Every generation ($V_0 \to V_1 \to V_2$) produces candidate DAGs, prompt diffs, and tool contracts immutably recorded in PostgreSQL for instant reproducible rollbacks.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white border border-emerald-100 space-y-1.5 shadow-2xs">
                <div className="text-xs font-bold text-zinc-900 font-geist flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-emerald-600" />
                  Multi-Tenant RLS Isolation
                </div>
                <p className="text-[11px] text-zinc-500 font-geist leading-relaxed">
                  GoTrue JWT authentication enforces database-level Row-Level Security (<code className="text-[10px] bg-zinc-100 px-1 py-0.5 rounded font-mono">auth.uid() = user_id</code>), ensuring sensitive enterprise prompts never leak across tenants.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white border border-emerald-100 space-y-1.5 shadow-2xs">
                <div className="text-xs font-bold text-zinc-900 font-geist flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-emerald-600" />
                  Cross-Run Epistemic Memory
                </div>
                <p className="text-[11px] text-zinc-500 font-geist leading-relaxed">
                  Learned failure invariants (e.g., currency float drift, datetime coercion) are persisted across sessions and re-injected into subsequent runs, permanently eliminating regression loops.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Call to Action Section */}
        <section className="rounded-3xl border border-indigo-200 bg-gradient-to-b from-indigo-900 to-zinc-950 text-white p-8 sm:p-14 text-center space-y-6 shadow-md relative overflow-hidden">
          {/* Subtle background glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 space-y-4 max-w-2xl mx-auto">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-400/40 bg-indigo-500/20 px-3 py-1 text-xs font-mono font-medium text-indigo-200">
              <Sparkle size={14} weight="fill" />
              <span>READY TO LEAP FROM PROMPT GUESSWORK?</span>
            </span>

            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white font-geist">
              Experience Autonomous Agent Engineering
            </h2>

            <p className="text-sm sm:text-base text-indigo-100/80 font-geist leading-relaxed">
              Stop guessing prompts. Compile reliable, self-optimizing compound AI agents with automated failure diagnostics,
              mutation tournaments, and zero regression.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
              <button
                type="button"
                onClick={handleLaunchConsole}
                className="inline-flex items-center gap-2 rounded-xl bg-white hover:bg-zinc-100 text-zinc-950 px-6 py-3 text-sm font-bold shadow-xs transition-all cursor-pointer font-geist active:scale-[0.98]"
              >
                <Terminal size={18} weight="bold" />
                <span>Launch Console Now</span>
                <ArrowRight size={16} weight="bold" />
              </button>

              <a
                href="https://github.com/toufiqfarhan0/reco"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl border border-indigo-400/30 bg-white/10 hover:bg-white/15 text-white px-5 py-3 text-sm font-semibold transition-all cursor-pointer font-geist"
              >
                <GithubLogo size={18} weight="bold" />
                <span>View Source on GitHub</span>
              </a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-zinc-200 bg-white py-8 text-center text-xs font-mono text-zinc-500">
        <div className="flex flex-wrap items-center justify-center gap-6 mb-3 font-geist">
          <Link to="/" className="hover:text-indigo-600 transition-colors text-zinc-600 font-medium">
            Home
          </Link>
          <Link to="/architecture" className="hover:text-indigo-600 transition-colors text-zinc-600 font-medium">
            Architecture
          </Link>
          <Link to="/why-reco" className="text-indigo-600 font-semibold transition-colors">
            Why Reco?
          </Link>
          <a href="/#pricing" className="hover:text-indigo-600 transition-colors text-zinc-600 font-medium">
            Pricing
          </a>
          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-indigo-600 transition-colors text-zinc-600 font-medium"
          >
            GitHub
          </a>
        </div>
        <p>Reco &bull; Autonomous Agent Engineering System &bull; Syndicate by Maximor</p>
      </footer>
    </div>
  );
};

export default WhyRecoPage;
