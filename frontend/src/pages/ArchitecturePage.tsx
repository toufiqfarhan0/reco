"use client";

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  Cpu,
  Play,
  Pulse,
  Sparkle,
  ShieldCheck,
  ArrowRight,
  Terminal,
  Lightning,
  CheckCircle,
  Database,
  Broadcast,
  CreditCard,
  GithubLogo,
  Graph,
  Lock,
  BookOpen,
  TreeStructure,
  Check,
  Copy,
  Scales,
  Atom,
} from "@phosphor-icons/react";

// ============================================================================
// DATA DEFINITIONS & CONSTANTS
// ============================================================================

interface StageDetail {
  id: string;
  num: string;
  name: string;
  tagline: string;
  formalName: string;
  color: string;
  badgeColor: string;
  icon: React.ElementType;
  overview: string;
  mathDefinition: string;
  inputs: string[];
  outputs: string[];
  keyInvariants: string[];
  operationalMechanism: string[];
}

const FIVE_STAGES: StageDetail[] = [
  {
    id: "stage-1",
    num: "01",
    name: "BUILD",
    tagline: "Goal Deconstruction & Typed Contract Synthesis",
    formalName: "Task Deconstruction & Initial Graph Synthesis (V₀)",
    color: "indigo",
    badgeColor: "bg-indigo-50 text-indigo-700 border-indigo-200",
    icon: Cpu,
    overview:
      "Stage 01 ingests an unstructured natural language goal G, decomposes it into an ordered set of functional subtasks, cross-references requested capabilities against the authorized Tool Catalog, and synthesizes a deterministic, typed Agent DAG (V₀).",
    mathDefinition:
      "Decompose(G, T_avail) -> T = (G, I, O, C)  s.t.  forall b in B_v, b in T_avail",
    inputs: [
      "Natural Language Goal G (arbitrary string)",
      "Authorized Tool Catalog T_avail with typed JSON schemas",
      "Evaluation Criteria & Domain Bounds C",
    ],
    outputs: [
      "Machine-Readable TaskSpecification T = (G, I, O, C)",
      "Initial Executable Agent DAG G_0 = (V_0, E_0)",
      "Typed Node Contracts & Pydantic Validation Models",
    ],
    keyInvariants: [
      "Anti-Fabrication Guard: Any suggested tool not present in T_avail raises a hard syntax fault.",
      "Acyclicity Guarantee: The synthesized graph G_0 is strictly verified to contain zero directed cycles.",
      "Reachability Bound: All terminal nodes are reachable from the designated entry node v_0.",
    ],
    operationalMechanism: [
      "Subtask Extraction: Partitions the raw goal into atomic, functional steps with explicit input/output signatures.",
      "Tool Recommendation: Matches required capabilities to registered tool schemas in the local or remote catalog.",
      "Topology Synthesis: Emits nodes, state-mapping edges, and runtime execution modes (deterministic vs model-driven).",
    ],
  },
  {
    id: "stage-2",
    num: "02",
    name: "RUN",
    tagline: "Topological Traversal & 4-Axis Multi-Objective Evaluation",
    formalName: "Deterministic Topological Execution & Scorecard Formulation",
    color: "blue",
    badgeColor: "bg-blue-50 text-blue-700 border-blue-200",
    icon: Play,
    overview:
      "Stage 02 runs the synthesized agent DAG deterministically over the benchmark dataset. Each node executes strictly following topological precedence, capturing wall-clock latency, token expenditures, and tool input/output diffs to compute a 4-axis multi-objective scorecard.",
    mathDefinition:
      "J(G) = [ Accuracy(G), Reliability(G), Cost(G), Latency(G) ]^T in [0,1] x [0,1] x R+ x R+",
    inputs: [
      "Agent DAG G = (V, E) with resolved execution modes",
      "Benchmark Scenario Dataset D_opt (Ground Truth Pairs)",
      "Inference Gateway Credentials (TensorMux GLM-4.7-Flash)",
    ],
    outputs: [
      "Complete Execution Traces E with per-node input/output states",
      "4-Axis Multi-Objective Scorecard J(G)",
      "Real-time Distributed Trace lineage streaming to Neatlogs",
    ],
    keyInvariants: [
      "Deterministic State Flow: Edge transitions enforce state immutability via cloned payloads.",
      "Bounded Model Loops: Agentic tool loops are capped at MAX_TOOL_CALL_ROUNDS = 5 to eliminate non-terminating recursion.",
      "Exact Token Accounting: Tracks prompt, completion, and reasoning tokens at $0.10/1M tokens.",
    ],
    operationalMechanism: [
      "Kahn's Topological Runner: Resolves dependencies dynamically as prior nodes write outputs to shared state.",
      "Structured Tool Dispatch: Validates tool arguments against Pydantic schemas before invocation.",
      "Objective Vector Aggregation: Simultaneously records accuracy, unhandled exception rate, token cost, and latency.",
    ],
  },
  {
    id: "stage-3",
    num: "03",
    name: "UNDERSTAND",
    tagline: "Formal 12-Category Diagnostic Taxonomy",
    formalName: "Automated Failure Attribution & Root-Cause Mapping",
    color: "amber",
    badgeColor: "bg-amber-50 text-amber-700 border-amber-200",
    icon: Pulse,
    overview:
      "Stage 03 systematically audits failed execution runs. Rather than vague natural language summaries, the diagnostic engine maps observed failure signatures to a formal 12-category taxonomy with calculated attribution confidence scores.",
    mathDefinition:
      "D(E_fail) -> < C_k, Severity, Confidence, NodeRef, Delta_impact >,  where C_k in Omega_tax",
    inputs: [
      "Failed Node Execution Traces E_fail",
      "Ground Truth vs Predicted Payload Diffs",
      "LLM Reasoning Tokens & Tool Exception Signatures",
    ],
    outputs: [
      "Categorized Failure Diagnostic Record with Root Cause Attribution",
      "Taxonomy Assignment (1 of 12 formal failure classes)",
      "Structured Mutation Directives for Stage 04",
    ],
    keyInvariants: [
      "Deterministic Attribution: Every failure is attributed to exactly one primary category and affected node ID.",
      "Confidence Lower Bound: Diagnoses must exceed confidence c >= 0.70 or trigger unclassified fallback.",
      "Downstream Taint Analysis: Calculates the blast radius of early failures on subsequent nodes in the DAG.",
    ],
    operationalMechanism: [
      "Trace Parser: Analyzes exception tracebacks, regex pattern matches, and semantic prediction divergences.",
      "Heuristic Confidence Scorer: Evaluates evidence weights across parameter types, schema definitions, and tool returns.",
      "Postmortem Generation: Produces structured failure records consumed directly by the mutation engine.",
    ],
  },
  {
    id: "stage-4",
    num: "04",
    name: "IMPROVE",
    tagline: "Multi-Candidate Tournament & Targeted Mutations",
    formalName: "Evolutionary Candidate Synthesis & Pareto Frontier Selection",
    color: "emerald",
    badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
    icon: Sparkle,
    overview:
      "Stage 04 synthesizes a bounded tournament pool of candidate architectures (V_{n+1}). It applies targeted mutators (prompt boundary tightening, tool re-binding, and structural verifier guardrail node injection) and identifies the Pareto-dominating champion.",
    mathDefinition:
      "G* = arg max_{G' in Pool(G)} { G' | G' >_pareto G },  where A >_pareto B iff forall i, J_i(A) >= J_i(B) and exists i, J_i(A) > J_i(B)",
    inputs: [
      "Parent Architecture G_n with baseline scorecard J(G_n)",
      "Diagnostic Postmortem Directives from Stage 03",
      "Evolutionary Mutation Operators M_prompt, M_tool, M_topology",
    ],
    outputs: [
      "Candidate Pool { V_{n+1}^A, V_{n+1}^B, V_{n+1}^C } with audited topological validity",
      "Evaluation Leaderboard over the optimization benchmark split",
      "Winning Champion Architecture G* advancing to Stage 05",
    ],
    keyInvariants: [
      "Complexity Ceiling: Candidates must satisfy |V| <= 10, |E| <= 20, depth <= 6.",
      "Acyclicity Invariant: Structural node additions (e.g. verifier nodes) must preserve the DAG property.",
      "Pareto Monotonicity: A candidate is only selected if it dominates or matches the parent without regression.",
    ],
    operationalMechanism: [
      "Prompt Boundary Specialist: Tightens negative constraints, output schema formatting, and edge-case instructions.",
      "Tool Re-Binding Mutator: Replaces fragile exact matchers with fuzzy or normalized tools.",
      "Verifier Node Injection: Inserts dedicated auditor nodes (e.g. verifier_tolerance_guard with epsilon = 0.001).",
    ],
  },
  {
    id: "stage-5",
    num: "05",
    name: "VALIDATE",
    tagline: "Air-Gapped Held-Out Verification Gate",
    formalName: "Air-Gapped Promotion Gate with Cryptographic Integrity Checksum",
    color: "teal",
    badgeColor: "bg-teal-50 text-teal-700 border-teal-200",
    icon: ShieldCheck,
    overview:
      "Stage 05 enforces an air-gapped promotion gate against an unpolluted held-out benchmark split. Using SHA-256 test integrity hashing, it proves zero training/optimization leakage and strictly emits PROMOTE, REQUIRES_REVIEW, or REJECT decisions.",
    mathDefinition:
      "Delta_gen = |Acc_opt - Acc_held|,  Gate(G*) in { PROMOTE, REQUIRES_REVIEW, REJECT }",
    inputs: [
      "Champion Candidate Architecture G* from Stage 04",
      "Air-Gapped Held-Out Benchmark Split D_held-out",
      "Cryptographic SHA-256 Benchmark Integrity Checksum",
    ],
    outputs: [
      "Formal Promotion Verdict (PROMOTE, REQUIRES_REVIEW, REJECT)",
      "Audited Generalization Gap Metric Delta_gen",
      "Cryptographic Integrity Audit Log in Supabase Cloud Ledger",
    ],
    keyInvariants: [
      "Zero Data Leakage: Mutation synthesis and prompt optimization never inspect held-out test cases.",
      "Cryptographic Immutability: SHA-256 hash verifies that held-out cases remained unaltered throughout the run.",
      "Regression Prohibition: Candidates that decrease held-out accuracy are rejected unconditionally.",
    ],
    operationalMechanism: [
      "Air-Gap Isolation: Dispatches the candidate to an isolated runner holding the blind test cases.",
      "Generalization Auditing: Compares train/opt performance with blind validation performance.",
      "Deployment Promotion: Promotes approved agents to production endpoints or flags multi-axis tradeoffs for human review.",
    ],
  },
];

// ============================================================================
// 12-CATEGORY DIAGNOSTIC TAXONOMY
// ============================================================================

interface TaxonomyCategory {
  code: string;
  name: string;
  severity: "low" | "medium" | "high" | "critical";
  symptom: string;
  rootCause: string;
  automatedRemediation: string;
}

const TAXONOMY_CATEGORIES: TaxonomyCategory[] = [
  {
    code: "TOOL_ARGUMENT_ERROR",
    name: "Tool Argument Coercion Fault",
    severity: "high",
    symptom: "TypeError: Parameter 'record_id' expected integer but received string '4021'.",
    rootCause: "LLM reasoning emitted JSON parameters that failed Pydantic argument type validation.",
    automatedRemediation: "Inject parameter casting schema validator in upstream node contract.",
  },
  {
    code: "TOOL_RUNTIME_ERROR",
    name: "External Tool Runtime Exception",
    severity: "critical",
    symptom: "HTTP 502 / Socket Hangup during third-party API invocation.",
    rootCause: "External service network glitch, rate-limit rejection, or unhandled tool crash.",
    automatedRemediation: "Synthesize exponential backoff retry policy (max_retries = 3) on retryable error list.",
  },
  {
    code: "ARITHMETIC_MISMATCH",
    name: "Floating-Point Drift / Precision Loss",
    severity: "medium",
    symptom: "Variance check failed: Expected balance difference 0.000, found 0.000999999.",
    rootCause: "IEEE 754 float conversion drift in multi-currency ledger summation.",
    automatedRemediation: "Synthesize verifier_tolerance_guard node with delta threshold epsilon = 0.001.",
  },
  {
    code: "PREMATURE_TERMINATION",
    name: "Premature Workflow Termination",
    severity: "high",
    symptom: "Workflow completed at intermediate node 02 without reaching terminal reconciliation state.",
    rootCause: "Missing edge transition rule or faulty boolean routing condition.",
    automatedRemediation: "Re-synthesize DAG edge routing rules ensuring path reachability to terminal node.",
  },
  {
    code: "HALLUCINATED_MATCH",
    name: "Fabricated Match / Entity Linking",
    severity: "critical",
    symptom: "Agent linked transaction TX-901 to general ledger row GL-410 with mismatched counterparty names.",
    rootCause: "Overly permissive prompt instructions allowing subjective similarity matching.",
    automatedRemediation: "Tighten prompt boundary condition enforcing strict counterparty string or fuzzy threshold >= 0.85.",
  },
  {
    code: "CONTEXT_OVERFLOW",
    name: "Context Window Saturation",
    severity: "high",
    symptom: "Model API error: Prompt tokens (38,400) exceeded context window limit.",
    rootCause: "Unbounded tabular data dumped directly into model reasoning state without summarization.",
    automatedRemediation: "Inject intermediate tabular chunking or statistical summary extraction node.",
  },
  {
    code: "MISSING_TOOL",
    name: "Unbound Required Capability",
    severity: "high",
    symptom: "Subtask required statistical variance computation but no corresponding tool was bound.",
    rootCause: "Goal analyzer failed to map data variance capability to compute_statistical_summary.",
    automatedRemediation: "Update TaskSpecification capability mapping and bind tool to executing node.",
  },
  {
    code: "WRONG_TOOL_SELECTION",
    name: "Suboptimal Tool Selection",
    severity: "medium",
    symptom: "Agent invoked brute-force query_general_ledger instead of indexed fuzzy_match_transactions.",
    rootCause: "Ambiguous tool docstrings causing model to favor generic search tools.",
    automatedRemediation: "Refine tool description schema emphasizing specialization and latency advantages.",
  },
  {
    code: "MISSING_VERIFICATION",
    name: "Missing Downstream Verifier Node",
    severity: "high",
    symptom: "Unverified calculation propagated directly to client report without sanity assertion.",
    rootCause: "Single-stage execution lacked an independent validation check for critical calculations.",
    automatedRemediation: "Inject structural verifier node between calculator and report generator.",
  },
  {
    code: "OUTPUT_SCHEMA_ERROR",
    name: "Output Contract Schema Violation",
    severity: "medium",
    symptom: "Missing required key 'discrepancy_list' in final agent JSON payload.",
    rootCause: "Model returned raw conversational text rather than structured JSON output conforming to contract.",
    automatedRemediation: "Enforce json_object mode and inject explicit output schema Pydantic model.",
  },
  {
    code: "MODEL_FAILURE",
    name: "Model Degeneration / Infinite Loop",
    severity: "critical",
    symptom: "Agent issued identical tool queries across 5 consecutive rounds without progressing.",
    rootCause: "Model got stuck in repetitive reasoning state without identifying new evidence.",
    automatedRemediation: "Cap tool loops at MAX_TOOL_CALL_ROUNDS = 5 with deterministic fallback breakout.",
  },
  {
    code: "FALSE_POSITIVE",
    name: "Over-Sensitive Detection Anomaly",
    severity: "medium",
    symptom: "Benign executive bonus flagged as fraudulent transaction due to naive 3-sigma rule.",
    rootCause: "Rigid single-variable Z-score threshold ignored multi-variable business context.",
    automatedRemediation: "Mutate detection logic to require multi-variable confirmation (temporal + categorical context).",
  },
];

// ============================================================================
// SYSTEM TOPOLOGY NODES
// ============================================================================

interface TopologyItem {
  id: string;
  name: string;
  role: string;
  tech: string;
  icon: React.ElementType;
  color: string;
  badge: string;
  description: string;
  whyAdded?: string;
  specs: { label: string; value: string }[];
  codeExample: string;
}

const TOPOLOGY_STACK: TopologyItem[] = [
  {
    id: "tensormux",
    name: "TensorMux",
    role: "Inference Gateway",
    tech: "GLM-4.7-Flash Model Provider",
    icon: Lightning,
    color: "amber",
    badge: "Active LLM Gateway",
    description:
      "Enterprise-grade OpenAI-compatible gateway directing high-throughput model inference to GLM-4.7-Flash. Extracts native reasoning tokens ('reasoning' message field) for deep epistemic analysis and enforces structured multi-round tool calling loops.",
    specs: [
      { label: "Target Model", value: "glm-4-7-flash" },
      { label: "Cost Accounting", value: "$0.10 / 1M tokens" },
      { label: "Tool Calling", value: "Multi-round (max 5 rounds)" },
      { label: "Reasoning Capture", value: "Full native reasoning tokens" },
    ],
    codeExample: `// TensorMux Gateway Client Execution
const response = await tensorMux.chat.completions.create({
  model: "glm-4-7-flash",
  messages: [{ role: "system", content: node.system_prompt }, ...history],
  tools: node.tools.map(t => toolRegistry.getSchema(t)),
  temperature: 0.0,
});
// Capture epistemic reasoning trace
const reasoning = response.choices[0].message.reasoning;`,
  },
  {
    id: "neatlogs",
    name: "Neatlogs",
    role: "Distributed Observability",
    tech: "Asynchronous Telemetry Ingest",
    icon: Broadcast,
    color: "indigo",
    badge: "5-Tier Span Telemetry",
    description:
      "Non-blocking distributed tracing engine providing fine-grained execution waterfalls across all stages. Hierarchy spans: optimization_run -> generation -> candidate_benchmark -> benchmark_case -> node_execution -> tool_invocation.",
    specs: [
      { label: "Ingestion Endpoint", value: "https://ingest.neatlogs.com" },
      { label: "Execution Impact", value: "0ms runtime overhead (async worker)" },
      { label: "Trace Depth", value: "5-tier hierarchical spans" },
      { label: "Deep Linking", value: "app.neatlogs.com/traces/:id" },
    ],
    codeExample: `// Neatlogs Distributed Trace Emission
await neatlogs.emitSpan({
  traceId: run.trace_id,
  spanName: "node_execution:" + node.id,
  parentSpanId: candidate.span_id,
  attributes: {
    "node.role": node.role,
    "tokens.reasoning": tokens.reasoning,
    "latency.wall_clock_ms": latencyMs,
  }
});`,
  },
  {
    id: "supabase",
    name: "Supabase",
    role: "Cloud Persistence & RLS",
    tech: "PostgreSQL Cloud Ledger",
    icon: Database,
    color: "emerald",
    badge: "Immutable State Store",
    description:
      "Relational PostgreSQL persistence layer backing experiments, immutable agent version DAGs, candidate evaluations, failure diagnoses, and promotion records. Secured with GoTrue Row-Level Security (RLS) and instant 1-Click Judge Demo Auth.",
    whyAdded:
      "Autonomous agent engineering cannot rely on ephemeral container memory or local SQLite files that wipe on container restarts. In real-world enterprise deployments, worker autoscaling and redeployments destroy candidate mutation histories, Pareto metrics, and postmortems. We added Supabase as an immutable PostgreSQL cloud ledger to guarantee mathematical rollback across generations (V0 → V1 → V2), cryptographic multi-tenant RLS isolation (auth.uid() = user_id), cross-session epistemic memory preservation, and frictionless 1-Click Judge Demo evaluation.",
    specs: [
      { label: "Storage Engine", value: "PostgreSQL 16 + RLS" },
      { label: "Auth Isolation", value: "GoTrue JWT (auth.uid() = user_id)" },
      { label: "Key Tables", value: "agent_versions, candidates, held_out_scorecards" },
      { label: "Judge Experience", value: "1-Click Evaluator Demo Sign-In" },
    ],
    codeExample: `// Supabase Cloud Ledger Insertion
const { data, error } = await supabase
  .from('candidate_evaluations')
  .insert({
    experiment_id: expId,
    generation: 1,
    candidate_id: "candidate_b",
    accuracy: 0.85,
    cost_usd: 0.0034,
    latency_ms: 2840,
    pareto_dominant: true,
  });`,
  },
  {
    id: "dodopayments",
    name: "Dodo Payments",
    role: "Monetization & Pro Entitlements",
    tech: "Hosted Checkout & HMAC Webhooks",
    icon: CreditCard,
    color: "cyan",
    badge: "Merchant of Record",
    description:
      "Monetization infrastructure providing recurring Pro subscriptions ($29/mo), hosted checkout sessions, customer billing portal, and cryptographically verified HMAC webhooks via standardwebhooks to manage evolutionary generation quotas.",
    specs: [
      { label: "Product ID", value: "pdt_0Nmvzbo4wJETkRyCMAEPt (Pro $29)" },
      { label: "Webhook Signing", value: "HMAC SHA-256 via standardwebhooks" },
      { label: "Anti-Replay", value: "Timestamp tolerance verification (5 min)" },
      { label: "Entitlements", value: "Free (1 gen, 3 runs) vs Pro (5 gen, 100 runs)" },
    ],
    codeExample: `// Dodo Payments Webhook Verification
import { Webhook } from "standardwebhooks";
const wh = new Webhook(process.env.DODO_PAYMENTS_WEBHOOK_KEY);
const payload = wh.verify(rawBody, {
  "webhook-id": req.headers["webhook-id"],
  "webhook-timestamp": req.headers["webhook-timestamp"],
  "webhook-signature": req.headers["webhook-signature"],
});`,
  },
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedStage, setSelectedStage] = useState<string>("stage-1");
  const [activeTaxonomy, setActiveTaxonomy] = useState<string>("TOOL_ARGUMENT_ERROR");
  const [activeTopology, setActiveTopology] = useState<string>("tensormux");
  const [activeLesson, setActiveLesson] = useState<number>(0);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, []);

  // Copy helper
  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const currentStage = FIVE_STAGES.find((s) => s.id === selectedStage) || FIVE_STAGES[0];
  const currentTopology = TOPOLOGY_STACK.find((t) => t.id === activeTopology) || TOPOLOGY_STACK[0];
  const currentTaxonomy = TAXONOMY_CATEGORIES.find((c) => c.code === activeTaxonomy) || TAXONOMY_CATEGORIES[0];

  return (
    <div className="min-h-screen bg-[#f8f8f7] flex flex-col font-sans selection:bg-indigo-100 selection:text-indigo-700 text-zinc-900">
      {/* ---------------------------------------------------------------------- */}
      {/* 1. Header & Navigation matching Reco Design System                     */}
      {/* ---------------------------------------------------------------------- */}
      <nav className="sticky top-0 z-50 h-14 bg-white/95 backdrop-blur-md border-b border-zinc-200 px-4 sm:px-6 lg:px-8 flex items-center justify-between shadow-sm">
        {/* Left: Brand + Back + Track Pill */}
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
            title="Return to Reco Home"
          >
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
            <span className="font-geist font-bold text-zinc-900 text-lg leading-none">
              Reco
            </span>
          </Link>

          <div className="h-4 w-px bg-zinc-200 hidden sm:block" />

          <div className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-indigo-600 animate-pulse" />
            <span className="text-xs font-mono font-medium text-zinc-700 hidden sm:inline">
              Track 1
            </span>
            <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-mono font-medium text-indigo-700">
              Architecture &amp; Theory
            </span>
          </div>
        </div>

        {/* Right Navigation Actions */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-5 text-xs font-medium text-zinc-600 font-geist">
            <Link to="/" className="hover:text-zinc-900 transition-colors cursor-pointer">
              Home
            </Link>
            <a
              href="#problem-formulation"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              DAG Theory
            </a>
            <a
              href="#compilation-engine"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              5-Stage Loop
            </a>
            <a
              href="#epistemic-memory"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              Epistemic Proofs
            </a>
            <a
              href="#system-topology"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              Topology
            </a>
            <a
              href="#why-reco"
              className="text-indigo-600 hover:text-indigo-800 font-semibold transition-colors cursor-pointer"
            >
              Why Reco
            </a>
          </div>

          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center h-8 w-8 rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors shadow-2xs"
            title="View Source on GitHub"
            aria-label="View Source on GitHub"
          >
            <GithubLogo size={17} weight="bold" />
          </a>

          <button
            type="button"
            onClick={() => navigate("/console")}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white px-3.5 py-1.5 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist"
          >
            <Terminal size={15} weight="bold" />
            <span>Launch Console</span>
          </button>
        </div>
      </nav>

      {/* ---------------------------------------------------------------------- */}
      {/* 2. Hero Section: Formal AutoML Theory & Mathematical Compiler          */}
      {/* ---------------------------------------------------------------------- */}
      <header className="relative bg-white border-b border-zinc-200 py-16 sm:py-20 overflow-hidden">
        <div className="absolute inset-0 opacity-40" style={{ background: "radial-gradient(ellipse at 60% 0%, #e0e7ff 0%, transparent 60%)" }} />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          {/* Track 1 Pill Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50/70 px-4 py-1.5 text-xs font-mono font-semibold text-indigo-800 shadow-2xs">
            <Atom size={16} weight="bold" className="text-indigo-600 animate-spin" />
            <span>RESEARCH MONOGRAPH • TRACK 1: AUTOMATED AGENT ENGINEERING</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-zinc-950 font-geist max-w-4xl mx-auto leading-[1.14]">
            The Architecture of Autonomous Agent Engineering
          </h1>

          <p className="text-base sm:text-lg text-zinc-600 max-w-3xl mx-auto font-geist leading-relaxed">
            An in-depth mathematical treatise on Reco&apos;s AutoML compilation engine: transforming
            declarative task specifications into deterministic, Pareto-optimal agent DAGs with closed-loop
            failure diagnostics, epistemic memory proofs, and air-gapped generalization guarantees.
          </p>

          {/* Research Metric Badges */}
          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-4xl mx-auto text-left">
            <div className="p-3.5 rounded-xl border border-zinc-200 bg-zinc-50/70 shadow-2xs">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block">
                Graph Verification
              </span>
              <span className="text-sm font-bold text-zinc-900 font-mono mt-0.5 block">
                100% Deterministic DAG
              </span>
              <span className="text-[11px] text-zinc-500 font-geist">Acyclicity verified in O(|V|+|E|)</span>
            </div>

            <div className="p-3.5 rounded-xl border border-zinc-200 bg-zinc-50/70 shadow-2xs">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block">
                Optimization Objective
              </span>
              <span className="text-sm font-bold text-zinc-900 font-mono mt-0.5 block">
                4-Axis Pareto Frontier
              </span>
              <span className="text-[11px] text-zinc-500 font-geist">Accuracy, Reliability, Cost, Latency</span>
            </div>

            <div className="p-3.5 rounded-xl border border-zinc-200 bg-zinc-50/70 shadow-2xs">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block">
                Diagnostic Taxonomy
              </span>
              <span className="text-sm font-bold text-zinc-900 font-mono mt-0.5 block">
                12 Failure Classes
              </span>
              <span className="text-[11px] text-zinc-500 font-geist">Root cause attribution c &ge; 0.70</span>
            </div>

            <div className="p-3.5 rounded-xl border border-zinc-200 bg-zinc-50/70 shadow-2xs">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block">
                Test Integrity Checksum
              </span>
              <span className="text-sm font-bold text-zinc-900 font-mono mt-0.5 block">
                SHA-256 Air-Gapped
              </span>
              <span className="text-[11px] text-zinc-500 font-geist">Zero train-test data leakage</span>
            </div>
          </div>
        </div>
      </header>

      {/* ---------------------------------------------------------------------- */}
      {/* 3. Main Content Sections                                               */}
      {/* ---------------------------------------------------------------------- */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-16">
        {/* ==================================================================== */}
        {/* SECTION 1: FORMAL PROBLEM FORMULATION & DAG COMPILATION              */}
        {/* ==================================================================== */}
        <section id="problem-formulation" className="space-y-8 scroll-mt-20">
          <div className="border-b border-zinc-200 pb-4">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-100 text-indigo-800 px-2.5 py-0.5 text-xs font-mono font-bold">
                SECTION 01
              </span>
              <h2 className="text-2xl font-bold tracking-tight text-zinc-950 font-geist">
                Formal Problem Formulation &amp; DAG Compilation Theory
              </h2>
            </div>
            <p className="text-sm text-zinc-600 mt-1 font-geist">
              Mathematical definitions governing task synthesis, topological execution orders, and
              acyclic graph verification.
            </p>
          </div>

          {/* Math Definition Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Task Specification Card */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TreeStructure size={18} weight="duotone" className="text-indigo-600" />
                  <h3 className="text-sm font-bold text-zinc-900 font-mono uppercase">
                    Definition 1: TaskSpecification T
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded">
                  reco.core.task_spec
                </span>
              </div>

              <div className="rounded-xl bg-zinc-900 text-zinc-100 p-4 font-mono text-xs overflow-x-auto">
                <p className="text-indigo-300 font-bold mb-1">// Formal Tuple Definition</p>
                <p className="text-emerald-400">T = (G, I, O, C)</p>
                <div className="mt-3 space-y-1 text-[11px] text-zinc-300">
                  <p>
                    <span className="text-amber-400">G:</span> Normalized Goal Statement &amp;
                    Objective Function
                  </p>
                  <p>
                    <span className="text-amber-400">I:</span> Typed Input Schemas &#123;x&#8321;:
                    &tau;&#8321;, ..., x&#8342;: &tau;&#8342;&#125;
                  </p>
                  <p>
                    <span className="text-amber-400">O:</span> Structural Output Contracts
                    &#123;y&#8321;: &sigma;&#8321;, ..., y&#8344;: &sigma;&#8344;&#125;
                  </p>
                  <p>
                    <span className="text-amber-400">C:</span> Constraint Quadruple &lang;
                    T_avail, K_req, B_latency, B_cost, R_risk &rang;
                  </p>
                </div>
              </div>

              <p className="text-xs text-zinc-600 leading-relaxed font-geist">
                The <code className="font-mono text-zinc-800 bg-zinc-100 px-1 py-0.5 rounded">TaskSpecification</code> is
                domain-agnostic and machine-readable. It bounds operational risk R_risk &isin;
                &#123;low, medium, high&#125; and enforces strict anti-fabrication: every suggested tool binding
                must satisfy <code className="font-mono text-indigo-700 font-bold">b &isin; T_avail</code>.
              </p>
            </div>

            {/* Agent DAG Card */}
            <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Graph size={18} weight="duotone" className="text-indigo-600" />
                  <h3 className="text-sm font-bold text-zinc-900 font-mono uppercase">
                    Definition 2: Agent DAG G
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded">
                  reco.engine.models
                </span>
              </div>

              <div className="rounded-xl bg-zinc-900 text-zinc-100 p-4 font-mono text-xs overflow-x-auto">
                <p className="text-indigo-300 font-bold mb-1">// Directed Acyclic Workflow Graph</p>
                <p className="text-emerald-400">G = (V, E, v&#8320;, V_term)</p>
                <div className="mt-3 space-y-1 text-[11px] text-zinc-300">
                  <p>
                    <span className="text-amber-400">V:</span> Executable Node Models &#123;v&#8321;,
                    ..., v&#8345;&#125;, where v = &lang;role, &pi;&#7525;, B&#7525;, &mu;&#7525;,
                    &rho;&#7525;&rang;
                  </p>
                  <p>
                    <span className="text-amber-400">E:</span> Directed Causal Transitions &#123;(u,
                    v, c&#7512;&#7525;)&#125;
                  </p>
                  <p>
                    <span className="text-amber-400">v&#8320;:</span> Designated Start Node with
                    in-degree deg&#713;(v&#8320;) = 0
                  </p>
                  <p>
                    <span className="text-amber-400">V_term:</span> Terminal Output Nodes with
                    out-degree deg&#8314;(v) = 0
                  </p>
                </div>
              </div>

              <p className="text-xs text-zinc-600 leading-relaxed font-geist">
                Each node v specifies its operational prompt &pi;&#7525;, authorized tools B&#7525;
                &sube; T_avail, execution mode &mu;&#7525; &isin; &#123;deterministic_tool, model_driven,
                model_inference&#125;, and retry policies &rho;&#7525;.
              </p>
            </div>
          </div>

          {/* Topological Traversal & Graph Validation Deep Dive */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xs space-y-6">
            <div className="flex items-center gap-2 pb-2 border-b border-zinc-100">
              <Scales size={20} weight="duotone" className="text-indigo-600" />
              <h3 className="text-base font-bold text-zinc-950 font-geist">
                Deterministic Topological Traversal &amp; Acyclicity Proof
              </h3>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Algorithm Explanation */}
              <div className="lg:col-span-2 space-y-4">
                <h4 className="text-xs font-mono font-bold text-zinc-700 uppercase tracking-wider">
                  The Acyclicity Invariant (Kahn&apos;s Linear Algorithm)
                </h4>
                <p className="text-xs text-zinc-600 leading-relaxed font-geist">
                  An Agent Architecture is strictly executable if and only if it admits a linear
                  topological sort ordering &tau;: V &rarr; &#123;1, ..., |V|&#125; such that for every
                  directed edge (u, v) &isin; E, &tau;(u) &lt; &tau;(v). Reco guarantees this
                  invariant during compilation using Kahn&apos;s algorithm in O(|V| + |E|) time:
                </p>

                <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 font-mono text-xs space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">1.</span>
                    <span>Compute in-degrees deg&#713;(v) = |&#123;u &isin; V | (u, v) &isin; E&#125;| for all v &isin; V.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">2.</span>
                    <span>Enqueue all nodes with deg&#713;(v) = 0 into queue Q. Initialize count = 0.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">3.</span>
                    <span>While Q is not empty: pop node u, increment count, and for each neighbor v of u, decrement deg&#713;(v). If deg&#713;(v) = 0, enqueue v.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">4.</span>
                    <span className="text-emerald-700 font-semibold">Invariant Check: If count &ne; |V|, throw GraphValidationError (Cyclic Dependency Detected).</span>
                  </div>
                </div>

                <div className="pt-2">
                  <h4 className="text-xs font-mono font-bold text-zinc-700 uppercase tracking-wider mb-2">
                    Runtime Latency Profiling on the Critical Path
                  </h4>
                  <p className="text-xs text-zinc-600 leading-relaxed font-geist">
                    The total end-to-end latency L_crit of the pipeline is bounded by the
                    longest path through the DAG:
                  </p>
                  <div className="mt-2 p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 font-mono text-xs text-indigo-950">
                    L_crit = max_&#123;p &isin; P(v&#8320;, V_term)&#125; &sum;_&#123;v &isin; p&#125; [ t_inference(v) + &sum;_k t_tool(v, k) + t_guard(v) ]
                  </div>
                </div>
              </div>

              {/* Complexity Bounds Card */}
              <div className="rounded-xl border border-zinc-200 bg-zinc-50/70 p-5 space-y-4 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-zinc-900 uppercase block mb-3">
                    Compiler Complexity Bounds
                  </span>
                  <div className="space-y-2.5 text-xs font-mono">
                    <div className="flex justify-between items-center py-1.5 border-b border-zinc-200/80">
                      <span className="text-zinc-500">Max Node Count |V|</span>
                      <span className="font-bold text-zinc-900">&le; 10 nodes</span>
                    </div>
                    <div className="flex justify-between items-center py-1.5 border-b border-zinc-200/80">
                      <span className="text-zinc-500">Max Edge Count |E|</span>
                      <span className="font-bold text-zinc-900">&le; 20 edges</span>
                    </div>
                    <div className="flex justify-between items-center py-1.5 border-b border-zinc-200/80">
                      <span className="text-zinc-500">Max Graph Depth</span>
                      <span className="font-bold text-zinc-900">&le; 6 levels</span>
                    </div>
                    <div className="flex justify-between items-center py-1.5 border-b border-zinc-200/80">
                      <span className="text-zinc-500">Max Tools per Node</span>
                      <span className="font-bold text-zinc-900">&le; 4 tools</span>
                    </div>
                    <div className="flex justify-between items-center py-1.5 border-b border-zinc-200/80">
                      <span className="text-zinc-500">Cycle Check Complexity</span>
                      <span className="font-bold text-emerald-700">O(|V| + |E|)</span>
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-white border border-zinc-200 shadow-2xs text-[11px] text-zinc-600">
                  <div className="flex items-center gap-1.5 text-emerald-700 font-bold mb-1">
                    <CheckCircle size={14} weight="fill" />
                    <span>Deterministic Compilation</span>
                  </div>
                  Every generated architecture is validated before execution. Disconnected nodes or
                  cyclic loops are caught prior to initiating LLM inference.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ==================================================================== */}
        {/* SECTION 2: THE 5-STAGE CLOSED-LOOP COMPILATION ENGINE               */}
        {/* ==================================================================== */}
        <section id="compilation-engine" className="space-y-8 scroll-mt-20">
          <div className="border-b border-zinc-200 pb-4">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-100 text-indigo-800 px-2.5 py-0.5 text-xs font-mono font-bold">
                SECTION 02
              </span>
              <h2 className="text-2xl font-bold tracking-tight text-zinc-950 font-geist">
                The 5-Stage Closed-Loop Compilation Engine
              </h2>
            </div>
            <p className="text-sm text-zinc-600 mt-1 font-geist">
              Interactive architectural specification of each phase in Reco&apos;s autonomous lifecycle.
            </p>
          </div>

          {/* Stage Selector Tabs */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 select-none">
            {FIVE_STAGES.map((s) => {
              const isSelected = s.id === selectedStage;
              const Icon = s.icon;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setSelectedStage(s.id)}
                  className={`flex flex-col items-start p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                    isSelected
                      ? "border-indigo-600 bg-white ring-2 ring-indigo-100 shadow-xs"
                      : "border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-600"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1.5">
                    <span className="text-[11px] font-mono font-bold text-zinc-400">
                      STAGE {s.num}
                    </span>
                    <Icon
                      size={17}
                      weight={isSelected ? "fill" : "duotone"}
                      className={isSelected ? "text-indigo-600" : "text-zinc-400"}
                    />
                  </div>
                  <span className={`text-sm font-bold font-geist ${isSelected ? "text-indigo-600" : "text-zinc-900"}`}>
                    {s.name}
                  </span>
                  <span className="text-[10px] text-zinc-500 line-clamp-1 mt-0.5 font-geist">
                    {s.tagline}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Detailed Active Stage Card */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStage.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xs space-y-6"
            >
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-zinc-200">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`rounded-md px-2.5 py-0.5 text-xs font-mono font-bold border ${currentStage.badgeColor}`}>
                      STAGE {currentStage.num} &bull; {currentStage.name}
                    </span>
                    <span className="text-xs font-mono text-zinc-400 hidden sm:inline">
                      {currentStage.formalName}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-zinc-950 font-geist">
                    {currentStage.tagline}
                  </h3>
                </div>

                <div className="p-3 rounded-xl bg-zinc-900 text-zinc-100 font-mono text-xs max-w-md shadow-2xs">
                  <span className="text-zinc-400 block text-[10px] uppercase font-semibold">
                    Mathematical Formulation
                  </span>
                  <p className="text-emerald-400 font-bold mt-0.5">{currentStage.mathDefinition}</p>
                </div>
              </div>

              {/* Stage Overview & Mechanism */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-5">
                  <div>
                    <h4 className="text-xs font-mono font-bold text-zinc-900 uppercase tracking-wider mb-2">
                      Stage Overview
                    </h4>
                    <p className="text-xs sm:text-sm text-zinc-700 leading-relaxed font-geist">
                      {currentStage.overview}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-xs font-mono font-bold text-zinc-900 uppercase tracking-wider mb-2">
                      Key Operational Mechanisms
                    </h4>
                    <ul className="space-y-2">
                      {currentStage.operationalMechanism.map((item, idx) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2.5 text-xs text-zinc-700 font-geist bg-zinc-50 p-3 rounded-lg border border-zinc-100"
                        >
                          <CheckCircle
                            size={16}
                            weight="fill"
                            className="text-indigo-600 shrink-0 mt-0.5"
                          />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-xs font-mono font-bold text-zinc-900 uppercase tracking-wider mb-2">
                      Formal Invariants &amp; Architectural Guarantees
                    </h4>
                    <div className="space-y-2">
                      {currentStage.keyInvariants.map((inv, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2.5 text-xs text-indigo-950 font-geist bg-indigo-50/50 p-3 rounded-lg border border-indigo-100/80"
                        >
                          <Lock size={16} weight="duotone" className="text-indigo-700 shrink-0 mt-0.5" />
                          <span className="font-medium">{inv}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* I/O Sidebar */}
                <div className="space-y-5">
                  <div className="rounded-xl border border-zinc-200 bg-zinc-50/70 p-4 space-y-3">
                    <span className="text-xs font-mono font-bold text-zinc-900 uppercase block">
                      Contract Inputs
                    </span>
                    <ul className="space-y-2 text-xs font-mono text-zinc-600">
                      {currentStage.inputs.map((inp, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-indigo-600 font-bold">&bull;</span>
                          <span>{inp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-xl border border-zinc-200 bg-zinc-50/70 p-4 space-y-3">
                    <span className="text-xs font-mono font-bold text-zinc-900 uppercase block">
                      Contract Outputs
                    </span>
                    <ul className="space-y-2 text-xs font-mono text-zinc-600">
                      {currentStage.outputs.map((out, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-600 font-bold">&bull;</span>
                          <span>{out}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Interactive Deep-Dive: 12-Category Diagnostic Taxonomy Explorer */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-zinc-200">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Pulse size={20} weight="duotone" className="text-amber-600" />
                  <h3 className="text-lg font-bold text-zinc-950 font-geist">
                    Interactive Taxonomy: 12 Core Diagnostic Failure Classes
                  </h3>
                </div>
                <p className="text-xs text-zinc-500 font-geist">
                  Select any failure classification to inspect runtime symptoms, root cause triggers,
                  and automated mutator mappings.
                </p>
              </div>

              <span className="text-xs font-mono text-zinc-500 bg-zinc-100 px-3 py-1 rounded-md self-start sm:self-auto">
                reco.diagnostics.taxonomy
              </span>
            </div>

            {/* Category Grid Pills */}
            <div className="flex flex-wrap gap-2">
              {TAXONOMY_CATEGORIES.map((tax) => {
                const isActive = tax.code === activeTaxonomy;
                return (
                  <button
                    key={tax.code}
                    type="button"
                    onClick={() => setActiveTaxonomy(tax.code)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-mono transition-all cursor-pointer ${
                      isActive
                        ? "bg-zinc-900 text-white font-bold shadow-xs scale-105"
                        : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                    }`}
                  >
                    {tax.code}
                  </button>
                );
              })}
            </div>

            {/* Active Taxonomy Detail Panel */}
            <div className="rounded-xl border border-zinc-200 bg-zinc-50/80 p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-zinc-200">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-zinc-900">
                    {currentTaxonomy.code}
                  </span>
                  <span className="text-xs text-zinc-500 font-geist">({currentTaxonomy.name})</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase">Severity:</span>
                  <span
                    className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold ${
                      currentTaxonomy.severity === "critical"
                        ? "bg-rose-100 text-rose-800 border border-rose-200"
                        : currentTaxonomy.severity === "high"
                        ? "bg-amber-100 text-amber-800 border border-amber-200"
                        : "bg-blue-100 text-blue-800 border border-blue-200"
                    }`}
                  >
                    {currentTaxonomy.severity}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-geist">
                <div className="p-3.5 bg-white rounded-lg border border-zinc-200 shadow-2xs space-y-1">
                  <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase block">
                    Observable Runtime Symptom
                  </span>
                  <p className="text-rose-700 font-mono text-[11px] leading-relaxed">
                    {currentTaxonomy.symptom}
                  </p>
                </div>

                <div className="p-3.5 bg-white rounded-lg border border-zinc-200 shadow-2xs space-y-1">
                  <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase block">
                    Root Cause Attribution
                  </span>
                  <p className="text-zinc-700 leading-relaxed">{currentTaxonomy.rootCause}</p>
                </div>

                <div className="p-3.5 bg-white rounded-lg border border-indigo-200 shadow-2xs space-y-1">
                  <span className="text-[10px] font-mono font-bold text-indigo-600 uppercase block">
                    Automated Mutation Remediation
                  </span>
                  <p className="text-indigo-900 leading-relaxed font-medium">
                    {currentTaxonomy.automatedRemediation}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ==================================================================== */}
        {/* SECTION 3: EPISTEMIC MEMORY LEDGER & INVARIANT GUARANTEES            */}
        {/* ==================================================================== */}
        <section id="epistemic-memory" className="space-y-8 scroll-mt-20">
          <div className="border-b border-zinc-200 pb-4">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-100 text-indigo-800 px-2.5 py-0.5 text-xs font-mono font-bold">
                SECTION 03
              </span>
              <h2 className="text-2xl font-bold tracking-tight text-zinc-950 font-geist">
                Epistemic Memory Ledger &amp; Invariant Guarantees
              </h2>
            </div>
            <p className="text-sm text-zinc-600 mt-1 font-geist">
              Mathematical proofs showing how postmortems become durable architectural rules that
              prevent regressions across evolution cycles.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Theory Card */}
            <div className="lg:col-span-1 rounded-2xl border border-zinc-200 bg-white p-6 shadow-xs space-y-4">
              <div className="flex items-center gap-2">
                <Lock size={18} weight="duotone" className="text-indigo-600" />
                <h3 className="text-sm font-bold text-zinc-900 font-mono uppercase">
                  Epistemic Invariant Proof
                </h3>
              </div>

              <p className="text-xs text-zinc-600 leading-relaxed font-geist">
                Let <code className="font-mono text-indigo-600 font-bold">I: S -&gt; &#123;0, 1&#125;</code> be a
                state assertion predicate codified into the ledger from generation V_j. For any
                subsequent generation V_k (k &gt; j), the mutator enforces the structural satisfaction
                guarantee:
              </p>

              <div className="p-3.5 rounded-xl bg-zinc-900 text-zinc-100 font-mono text-xs space-y-1">
                <p className="text-indigo-300 font-bold">// Non-Regression Guarantee</p>
                <p className="text-emerald-400">forall s in States(V_k), I(s) = 1</p>
                <p className="text-zinc-400 text-[10px] mt-2 leading-snug">
                  Postmortem codified rules are hard-injected into node contracts, ensuring that bugs fixed
                  in V_0 or V_1 cannot reoccur in V_2.
                </p>
              </div>

              <div className="pt-2 space-y-2 text-xs font-mono">
                <div className="flex justify-between items-center py-1 border-b border-zinc-100">
                  <span className="text-zinc-500">Cumulative Accuracy Gain</span>
                  <span className="font-bold text-emerald-600">+25.0% (V0 &rarr; V2)</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-zinc-100">
                  <span className="text-zinc-500">Regressions Introduced</span>
                  <span className="font-bold text-zinc-900">0 regressions</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-zinc-100">
                  <span className="text-zinc-500">Codification Format</span>
                  <span className="font-bold text-zinc-900">Pydantic / TypeScript</span>
                </div>
              </div>
            </div>

            {/* Empirical Lessons Tabs */}
            <div className="lg:col-span-2 rounded-2xl border border-zinc-200 bg-white p-6 shadow-xs space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-200">
                <div className="flex items-center gap-2">
                  <BookOpen size={18} weight="duotone" className="text-indigo-600" />
                  <h3 className="text-sm font-bold text-zinc-950 font-mono uppercase">
                    Codified Epistemic Invariants from Benchmark Runs
                  </h3>
                </div>
                <span className="text-xs font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                  Verified In Production
                </span>
              </div>

              {/* Lesson Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {[
                  { title: "Lesson 01", sub: "Timestamp Normalization", gen: "V0 -> V1", delta: "+15.0%" },
                  { title: "Lesson 02", sub: "Tolerance Guardrail", gen: "V1 -> V2", delta: "+10.0%" },
                  { title: "Lesson 03", sub: "Parameter Strictness", gen: "V1 -> V2", delta: "+25.0%" },
                ].map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setActiveLesson(idx)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      activeLesson === idx
                        ? "border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-200"
                        : "border-zinc-200 bg-zinc-50/50 hover:bg-zinc-100"
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] font-mono text-zinc-500 mb-1">
                      <span>{item.title}</span>
                      <span className="text-indigo-700 font-bold">{item.delta}</span>
                    </div>
                    <span className="text-xs font-bold text-zinc-900 font-geist block truncate">
                      {item.sub}
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400 mt-0.5 block">{item.gen}</span>
                  </button>
                ))}
              </div>

              {/* Lesson Code Snippet and Context */}
              {activeLesson === 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-zinc-500">
                      Rule: Tool Output Normalization (Unix Epoch to ISO-8601 UTC Coercion)
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        handleCopy(
                          `export function normalizeTimestamp(raw: string | number): string {\n  if (typeof raw === "number") {\n    return new Date(raw * 1000).toISOString();\n  }\n  return new Date(raw).toISOString();\n}`,
                          "lesson-0"
                        )
                      }
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-500 hover:text-zinc-900 cursor-pointer"
                    >
                      {copiedCode === "lesson-0" ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
                      <span>{copiedCode === "lesson-0" ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                  <div className="rounded-xl bg-zinc-900 text-zinc-100 p-4 font-mono text-xs overflow-x-auto">
                    <p className="text-zinc-400">// Injected at Node 02 (normalize_timestamp)</p>
                    <p className="text-indigo-300">export function <span className="text-amber-300">normalizeTimestamp</span>(raw: string | number): string &#123;</p>
                    <p className="pl-4 text-zinc-300">if (typeof raw === &quot;number&quot;) &#123;</p>
                    <p className="pl-8 text-emerald-400">return new Date(raw * 1000).toISOString(); // Coerce Unix seconds</p>
                    <p className="pl-4 text-zinc-300">&#125;</p>
                    <p className="pl-4 text-zinc-300">return new Date(raw).toISOString();</p>
                    <p className="text-indigo-300">&#125;</p>
                  </div>
                  <p className="text-xs text-zinc-600 font-geist">
                    <strong>Derivation:</strong> Derived from <code className="font-mono text-zinc-800">SCHEMA_VIOLATION</code> in V0. Stripe API
                    timestamps in Unix Epoch seconds caused string matching errors against internal ISO SQL records. Eliminating this mismatch drove a <strong>+15.0% accuracy gain</strong>.
                  </p>
                </div>
              )}

              {activeLesson === 1 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-zinc-500">
                      Rule: Tolerance Drift Guardrail (IEEE 754 Currency Rounding Tolerance)
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        handleCopy(
                          `export function verifyFinancialBalance(amountA: number, amountB: number, epsilon = 0.001): boolean {\n  return Math.abs(amountA - amountB) <= epsilon;\n}`,
                          "lesson-1"
                        )
                      }
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-500 hover:text-zinc-900 cursor-pointer"
                    >
                      {copiedCode === "lesson-1" ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
                      <span>{copiedCode === "lesson-1" ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                  <div className="rounded-xl bg-zinc-900 text-zinc-100 p-4 font-mono text-xs overflow-x-auto">
                    <p className="text-zinc-400">// Injected at Node 04 (verifier_tolerance_guard)</p>
                    <p className="text-indigo-300">export function <span className="text-amber-300">verifyFinancialBalance</span>(amountA: number, amountB: number, epsilon = 0.001): boolean &#123;</p>
                    <p className="pl-4 text-emerald-400">// Guardrail against IEEE 754 float drift in currency reconciliation</p>
                    <p className="pl-4 text-zinc-300">return Math.abs(amountA - amountB) &lt;= epsilon;</p>
                    <p className="text-indigo-300">&#125;</p>
                  </div>
                  <p className="text-xs text-zinc-600 font-geist">
                    <strong>Derivation:</strong> Multi-currency conversion introduced $0.000999 float drift ($452.999 vs $453.00),
                    falsely failing exact equality assertions. Synthesizing a dedicated verifier with epsilon = 0.001 yielded a <strong>+10.0% accuracy lift</strong>.
                  </p>
                </div>
              )}

              {activeLesson === 2 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-zinc-500">
                      Rule: Parameter Strictness (Integer Type Enforcement on Record Identifiers)
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        handleCopy(
                          `export function validateToolParams(params: { record_id: unknown }): { record_id: number } {\n  const idNum = Number(params.record_id);\n  if (isNaN(idNum) || !Number.isInteger(idNum)) {\n    throw new TypeError("Parameter 'record_id' must be integer");\n  }\n  return { record_id: idNum };\n}`,
                          "lesson-2"
                        )
                      }
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-500 hover:text-zinc-900 cursor-pointer"
                    >
                      {copiedCode === "lesson-2" ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
                      <span>{copiedCode === "lesson-2" ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                  <div className="rounded-xl bg-zinc-900 text-zinc-100 p-4 font-mono text-xs overflow-x-auto">
                    <p className="text-zinc-400">// Injected at Node 03 (schema_validator)</p>
                    <p className="text-indigo-300">export function <span className="text-amber-300">validateToolParams</span>(params: &#123; record_id: unknown &#125;): &#123; record_id: number &#125; &#123;</p>
                    <p className="pl-4 text-zinc-300">const idNum = Number(params.record_id);</p>
                    <p className="pl-4 text-zinc-300">if (isNaN(idNum) || !Number.isInteger(idNum)) &#123;</p>
                    <p className="pl-8 text-rose-400">throw new TypeError(&quot;Parameter &apos;record_id&apos; must be integer&quot;);</p>
                    <p className="pl-4 text-zinc-300">&#125;</p>
                    <p className="pl-4 text-emerald-400">return &#123; record_id: idNum &#125;;</p>
                    <p className="text-indigo-300">&#125;</p>
                  </div>
                  <p className="text-xs text-zinc-600 font-geist">
                    <strong>Derivation:</strong> Upstream LLM reasoning emitted record IDs as string literals, crashing the SQL driver.
                    Runtime type coercion prevented unhandled crashes across 100% of benchmark queries.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ==================================================================== */}
        {/* SECTION 4: SYSTEM TOPOLOGY & INFRASTRUCTURE STACK                   */}
        {/* ==================================================================== */}
        <section id="system-topology" className="space-y-8 scroll-mt-20">
          <div className="border-b border-zinc-200 pb-4">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-100 text-indigo-800 px-2.5 py-0.5 text-xs font-mono font-bold">
                SECTION 04
              </span>
              <h2 className="text-2xl font-bold tracking-tight text-zinc-950 font-geist">
                System Topology &amp; Production Infrastructure Stack
              </h2>
            </div>
            <p className="text-sm text-zinc-600 mt-1 font-geist">
              Architectural integration across TensorMux (GLM-4.7-Flash), Neatlogs distributed tracing,
              Supabase cloud persistence, and Dodo Payments.
            </p>
          </div>

          {/* Infrastructure Topology Visual Flow */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 sm:p-8 shadow-xs space-y-6">
            <h3 className="text-xs font-mono font-bold text-zinc-900 uppercase tracking-wider">
              Data &amp; Control Flow Architecture
            </h3>

            {/* Architecture Flow Diagram */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
              <div className="p-4 rounded-xl border border-zinc-200 bg-zinc-50 space-y-2">
                <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold">Client Layer</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white mx-auto shadow-xs">
                  <Terminal size={20} weight="bold" />
                </div>
                <span className="text-xs font-bold text-zinc-900 font-geist block">Reco Console</span>
                <span className="text-[11px] text-zinc-500 font-mono block">Vite + React SPA</span>
              </div>

              <div className="p-4 rounded-xl border border-zinc-200 bg-zinc-50 space-y-2">
                <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold">Execution Core</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-900 text-white mx-auto shadow-xs">
                  <Cpu size={20} weight="bold" />
                </div>
                <span className="text-xs font-bold text-zinc-900 font-geist block">FastAPI + Python 3.11</span>
                <span className="text-[11px] text-zinc-500 font-mono block">DAG Compilation &amp; Eval</span>
              </div>

              <div className="p-4 rounded-xl border border-zinc-200 bg-zinc-50 space-y-2">
                <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold">Inference Gateway</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500 text-white mx-auto shadow-xs">
                  <Lightning size={20} weight="fill" />
                </div>
                <span className="text-xs font-bold text-zinc-900 font-geist block">TensorMux Gateway</span>
                <span className="text-[11px] text-zinc-500 font-mono block">GLM-4.7-Flash LLM</span>
              </div>

              <div className="p-4 rounded-xl border border-zinc-200 bg-zinc-50 space-y-2">
                <span className="text-[10px] font-mono text-zinc-400 uppercase font-bold">Persistence &amp; Billing</span>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-600 text-white mx-auto shadow-xs">
                  <Database size={20} weight="bold" />
                </div>
                <span className="text-xs font-bold text-zinc-900 font-geist block">Supabase + Dodo</span>
                <span className="text-[11px] text-zinc-500 font-mono block">PostgreSQL RLS + Webhooks</span>
              </div>
            </div>

            {/* Pillar Selector Tabs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-4">
              {TOPOLOGY_STACK.map((item) => {
                const isActive = item.id === activeTopology;
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setActiveTopology(item.id)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      isActive
                        ? "border-indigo-600 bg-white ring-2 ring-indigo-100 shadow-xs"
                        : "border-zinc-200 bg-zinc-50/60 hover:bg-zinc-100"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon size={16} weight="duotone" className={isActive ? "text-indigo-600" : "text-zinc-500"} />
                      <span className={`text-xs font-bold font-mono ${isActive ? "text-indigo-600" : "text-zinc-900"}`}>
                        {item.name}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500 block truncate font-geist">
                      {item.role}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Active Pillar Detail Card */}
            <div className="rounded-xl border border-zinc-200 bg-zinc-50/70 p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-zinc-200">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-zinc-950 font-geist">
                      {currentTopology.name} &bull; {currentTopology.tech}
                    </span>
                    <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                      {currentTopology.badge}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-600 max-w-2xl font-geist leading-relaxed">
                    {currentTopology.description}
                  </p>
                </div>
              </div>

              {/* Specs & Code */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Specs List */}
                <div className="rounded-xl bg-white border border-zinc-200 p-4 space-y-3">
                  <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase block">
                    Technical Specifications
                  </span>
                  <div className="space-y-2 text-xs font-mono">
                    {currentTopology.specs.map((spec, idx) => (
                      <div key={idx} className="flex justify-between items-center py-1 border-b border-zinc-100">
                        <span className="text-zinc-500">{spec.label}</span>
                        <span className="font-bold text-zinc-900">{spec.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Code Snippet */}
                <div className="lg:col-span-2 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-zinc-400 uppercase">
                      Integration Code Pattern
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopy(currentTopology.codeExample, currentTopology.id)}
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-500 hover:text-zinc-900 cursor-pointer"
                    >
                      {copiedCode === currentTopology.id ? (
                        <Check size={13} className="text-emerald-600" />
                      ) : (
                        <Copy size={13} />
                      )}
                      <span>{copiedCode === currentTopology.id ? "Copied" : "Copy Code"}</span>
                    </button>
                  </div>
                  <div className="rounded-xl bg-zinc-900 text-zinc-100 p-4 font-mono text-xs overflow-x-auto leading-relaxed">
                    <pre>{currentTopology.codeExample}</pre>
                  </div>
                </div>
              </div>

              {currentTopology.whyAdded && (
                <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 space-y-1.5">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-800 uppercase">
                    <Database size={15} weight="fill" className="text-emerald-700" />
                    <span>Architectural Rationale: Why We Added {currentTopology.name}</span>
                  </div>
                  <p className="text-xs text-emerald-950 font-geist leading-relaxed">
                    {currentTopology.whyAdded}
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ==================================================================== */}
        {/* SECTION 5: WHY RECO PARADIGM SHIFT                                   */}
        {/* ==================================================================== */}
        <section id="why-reco" className="space-y-8 scroll-mt-20">
          <div className="border-b border-zinc-200 pb-4">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-100 text-indigo-800 px-2.5 py-0.5 text-xs font-mono font-bold">
                PARADIGM SHIFT
              </span>
              <h2 className="text-2xl font-bold tracking-tight text-zinc-950 font-geist">
                Why Reco: The Paradigm Shift from Heuristic Prompting to Autonomous Engineering
              </h2>
            </div>
            <p className="text-sm text-zinc-600 mt-1 font-geist">
              A side-by-side comparison between traditional trial-and-error agent building and Reco&apos;s
              closed-loop AutoML compiler.
            </p>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white shadow-xs">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-50 border-b border-zinc-200 font-mono text-[11px] text-zinc-600 uppercase">
                <tr>
                  <th className="py-3.5 px-4 font-bold">Engineering Dimension</th>
                  <th className="py-3.5 px-4 text-rose-700 font-bold bg-rose-50/50">
                    Traditional &quot;Vibe-Coding&quot; Agent Setup
                  </th>
                  <th className="py-3.5 px-4 text-emerald-800 font-bold bg-emerald-50/50">
                    Reco Autonomous Agent Engineering
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 font-geist text-zinc-700">
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    Architecture Design
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Hand-wired graph nodes without acyclicity validation or formal contracts.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    Autonomous DAG synthesis from TaskSpecification with O(|V|+|E|) topological proof.
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    Failure Diagnosis
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Engineers manually read through verbose console logs to guess why an agent broke.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    Automated 12-category diagnostic taxonomy isolating exact root cause and affected node.
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    Optimization Loop
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Heuristic prompt tweaking that silently introduces regressions in other edge cases.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    Multi-candidate tournament (prompt boundary, tool re-binding, structural verifier guardrails).
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    Multi-Objective Evaluation
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Subjective &quot;vibe checks&quot; ignoring inference costs and execution latencies.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    4-Axis Pareto Frontier simultaneously tracking Accuracy, Reliability, Cost, and Latency.
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    Deployment Verification
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Deployed straight to production with severe prompt overfitting to training samples.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    Air-gapped held-out verification gate with cryptographic SHA-256 test integrity hashing.
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    Generational Memory
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Ephemeral memory: earlier debugging insights are lost when prompts are updated.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    Epistemic Memory Ledger preserving durable invariants across all future generations (+25.0% lift).
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-mono font-semibold text-zinc-950">
                    State &amp; Lineage Persistence
                  </td>
                  <td className="py-3.5 px-4 text-rose-800 bg-rose-50/20">
                    Ephemeral RAM or local scratch SQLite wiped on container restarts; zero multi-tenant security.
                  </td>
                  <td className="py-3.5 px-4 text-emerald-900 bg-emerald-50/20 font-medium">
                    Supabase PostgreSQL cloud ledger storing immutable versioned DAGs with GoTrue Row-Level Security (RLS).
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* ==================================================================== */}
        {/* CALL TO ACTION                                                       */}
        {/* ==================================================================== */}
        <div className="rounded-2xl bg-zinc-900 text-white p-8 sm:p-10 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <span className="text-xs font-mono font-bold text-indigo-400 uppercase tracking-wider">
              Experience the Compiler Live
            </span>
            <h3 className="text-2xl font-bold tracking-tight text-white font-geist">
              Ready to automate agent engineering?
            </h3>
            <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed font-geist">
              Open the interactive engineering console to synthesize, execute, benchmark, diagnose,
              and evolve agents with live GLM-4.7-Flash inference and distributed trace streaming.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={() => navigate("/console")}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist"
            >
              <Terminal size={16} weight="bold" />
              <span>Launch Interactive Console</span>
              <ArrowRight size={14} weight="bold" />
            </button>
            <a
              href="https://github.com/toufiqfarhan0/reco"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-4 py-3 text-xs font-semibold transition-all cursor-pointer font-geist"
            >
              <GithubLogo size={16} weight="bold" />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </main>

      {/* ---------------------------------------------------------------------- */}
      {/* 4. Footer                                                              */}
      {/* ---------------------------------------------------------------------- */}
      <footer className="w-full border-t border-zinc-200 bg-white py-8 text-xs font-mono text-zinc-500">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-zinc-800 font-geist">Reco</span>
            <span>&bull;</span>
            <span>Autonomous Agent Engineering System</span>
          </div>

          <div className="flex items-center gap-4 text-zinc-600">
            <button
              type="button"
              onClick={() => navigate("/console")}
              className="hover:text-zinc-950 transition-colors cursor-pointer"
            >
              Console
            </button>
            <Link to="/#why-reco" className="hover:text-zinc-950 transition-colors cursor-pointer">
              Why Reco
            </Link>
            <a
              href="https://github.com/toufiqfarhan0/reco"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-950 transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://reco-b1ac.onrender.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-950 transition-colors"
            >
              Live Deployment
            </a>
          </div>

          <p className="text-[11px] text-zinc-400">
            Syndicate by Maximor &bull; Track 1 Submission
          </p>
        </div>
      </footer>
    </div>
  );
};

export default ArchitecturePage;
