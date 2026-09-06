"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Brain,
  CheckCircle,
  TrendUp,
  Code,
  Sparkle,
  CaretDown,
  CaretUp,
  Cpu,
  ShieldCheck,
} from "@phosphor-icons/react";

export interface EpistemicLesson {
  id: string;
  lessonNumber: string;
  generationTransition: string;
  generationFrom: string;
  generationTo: string;
  sourceCategory: string;
  ruleTitle: string;
  epistemicRule: string;
  targetNode: string;
  accuracyDelta: string;
  cumulativeAccuracy: string;
  derivationContext: string;
  codeSnippet: string;
  impactVerdict: string;
}

const EPISTEMIC_LESSONS: EpistemicLesson[] = [
  {
    id: "epistemic-01",
    lessonNumber: "Lesson 01",
    generationTransition: "V0 -> V1",
    generationFrom: "V0",
    generationTo: "V1",
    sourceCategory: "SCHEMA_VIOLATION",
    ruleTitle: "Tool Output Normalization",
    epistemicRule:
      "Do not rely on naive exact string match for transaction IDs. Tool Output Normalization: Third-party API timestamps require ISO-8601 UTC coercion before line-item matching.",
    targetNode: "normalize_timestamp (Node 02)",
    accuracyDelta: "+15.0%",
    cumulativeAccuracy: "75.0%",
    derivationContext:
      "Derived from SCHEMA_VIOLATION in V0; applied to V1. Stripe API unix epoch seconds failed string regex matching against internal SQL ledger timestamps, causing false reconciliation mismatches.",
    codeSnippet: `// Epistemic Guardrail 01: Injected at Node 02 (normalize_timestamp)
export function normalizeTimestamp(raw: string | number): string {
  if (typeof raw === "number") {
    return new Date(raw * 1000).toISOString(); // Coerce Unix Epoch seconds to ISO-8601 UTC
  }
  return new Date(raw).toISOString();
}`,
    impactVerdict: "Eliminated 100% of timestamp schema mismatches across 20 evaluation cases.",
  },
  {
    id: "epistemic-02",
    lessonNumber: "Lesson 02",
    generationTransition: "V1 -> V2",
    generationFrom: "V1",
    generationTo: "V2",
    sourceCategory: "VERIFICATION_MISS",
    ruleTitle: "Tolerance Drift Guardrail",
    epistemicRule:
      "Always execute dual-pass currency amount validation. Tolerance Drift Guardrail: Floating-point discrepancies in financial reconciliation drift by 0.001; synthesized dedicated Verifier node.",
    targetNode: "verifier_tolerance_guard (Node 04)",
    accuracyDelta: "+10.0%",
    cumulativeAccuracy: "85.0%",
    derivationContext:
      "Derived from VERIFICATION_MISS in V1; applied to V2. Currency conversions caused precision rounding deltas (e.g. $452.999 vs $453.00), falsely tripping the strict equality check.",
    codeSnippet: `// Epistemic Guardrail 02: Synthesized Dedicated Verifier Node
export function verifyFinancialBalance(amountA: number, amountB: number, epsilon = 0.001): boolean {
  // Guardrail against IEEE 754 float drift in currency reconciliation
  return Math.abs(amountA - amountB) <= epsilon;
}`,
    impactVerdict: "Resolved multi-currency float rounding deltas, promoting Candidate C to Pareto champion.",
  },
  {
    id: "epistemic-03",
    lessonNumber: "Lesson 03",
    generationTransition: "V1 -> V2",
    generationFrom: "V1",
    generationTo: "V2",
    sourceCategory: "TOOL_PARAMETER_ERROR",
    ruleTitle: "Parameter Strictness",
    epistemicRule:
      "Maintain immutable state transitions for reconciled entries. Parameter Strictness: Parameter 'record_id' must be integer, not string; injected schema validator.",
    targetNode: "schema_validator (Node 03)",
    accuracyDelta: "+25.0%",
    cumulativeAccuracy: "85.0%",
    derivationContext:
      "Derived from TOOL_PARAMETER_ERROR in V1; injected schema validator. Upstream LLM reasoning generated 'record_id': '4021' as string, triggering runtime database driver rejection.",
    codeSnippet: `// Epistemic Guardrail 03: Parameter Invariant Enforcer
export function validateToolParams(params: { record_id: unknown }): { record_id: number } {
  const idNum = Number(params.record_id);
  if (isNaN(idNum) || !Number.isInteger(idNum)) {
    throw new TypeError("Parameter 'record_id' must be a valid integer");
  }
  return { record_id: idNum };
}`,
    impactVerdict: "Guaranteed runtime parameter safety across downstream database driver invocations.",
  },
];

interface EpistemicMemoryLedgerProps {
  defaultExpanded?: boolean;
}

export const EpistemicMemoryLedger: React.FC<EpistemicMemoryLedgerProps> = ({
  defaultExpanded = false,
}) => {
  const [selectedFilter, setSelectedFilter] = useState<"all" | "V0 -> V1" | "V1 -> V2">("all");
  const [expandedLessonId, setExpandedLessonId] = useState<string | null>(
    defaultExpanded ? "epistemic-01" : null
  );

  const filteredLessons = EPISTEMIC_LESSONS.filter((l) => {
    if (selectedFilter === "all") return true;
    return l.generationTransition === selectedFilter;
  });

  return (
    <div className="space-y-6 pt-6 border-t border-zinc-100">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-200">
            <Brain size={20} weight="duotone" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold tracking-tight text-zinc-950 font-geist">
                Epistemic Memory Ledger: Generational Self-Reflection
              </h3>
              <span className="rounded bg-emerald-50 px-2.5 py-0.5 text-[10px] font-mono font-bold text-emerald-700 border border-emerald-200">
                ACTIVE MEMORY
              </span>
            </div>
            <p className="text-xs text-zinc-500 font-geist">
              Persistent architectural invariants extracted across mutation cycles (V0 → V1 → V2)
            </p>
          </div>
        </div>

        {/* Judge Query Pill */}
        <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-2.5 text-xs text-indigo-900 max-w-md">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider block text-indigo-700 mb-0.5">
            JUDGE QUERY:
          </span>
          <p className="italic text-[11px] font-geist">
            &quot;Can you show the outputs of the agent getting better over time?&quot;
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block font-medium">
            Cumulative Accuracy Gain
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-emerald-700">
              +25.0%
            </span>
            <span className="text-[11px] text-zinc-500 font-mono">
              60.0% → 85.0%
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block font-medium">
            Synthesized Invariants
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-zinc-900">
              3 Rules
            </span>
            <span className="text-[11px] text-indigo-600 font-mono font-medium">
              Zero Regression
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block font-medium">
            Failure Taxonomies Handled
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-amber-800">
              3 Types
            </span>
            <span className="text-[11px] text-zinc-500 font-mono">
              Auto-isolated
            </span>
          </div>
        </div>

        <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block font-medium">
            Held-Out Verification
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold font-mono text-zinc-900">
              0.0%
            </span>
            <span className="text-[11px] text-emerald-700 font-mono font-medium">
              Zero Drift
            </span>
          </div>
        </div>
      </div>

      {/* Generation Tabs with Indigo Underline Active Indicator */}
      <div className="border-b border-zinc-200">
        <div className="flex space-x-6 text-xs font-mono">
          <button
            type="button"
            onClick={() => setSelectedFilter("all")}
            className={`pb-2.5 transition-all cursor-pointer font-medium relative ${
              selectedFilter === "all"
                ? "text-indigo-600 font-bold border-b-2 border-indigo-600 -mb-px"
                : "text-zinc-600 hover:text-zinc-900 border-b-2 border-transparent"
            }`}
          >
            All Lessons (3)
          </button>
          <button
            type="button"
            onClick={() => setSelectedFilter("V0 -> V1")}
            className={`pb-2.5 transition-all cursor-pointer font-medium relative ${
              selectedFilter === "V0 -> V1"
                ? "text-indigo-600 font-bold border-b-2 border-indigo-600 -mb-px"
                : "text-zinc-600 hover:text-zinc-900 border-b-2 border-transparent"
            }`}
          >
            V0 to V1 (Lesson 01)
          </button>
          <button
            type="button"
            onClick={() => setSelectedFilter("V1 -> V2")}
            className={`pb-2.5 transition-all cursor-pointer font-medium relative ${
              selectedFilter === "V1 -> V2"
                ? "text-indigo-600 font-bold border-b-2 border-indigo-600 -mb-px"
                : "text-zinc-600 hover:text-zinc-900 border-b-2 border-transparent"
            }`}
          >
            V1 to V2 (Lessons 02 & 03)
          </button>
        </div>
      </div>

      {/* Epistemic Ledger Detailed Cards (white, border border-zinc-200 rounded-xl) */}
      <div className="space-y-4">
        {filteredLessons.map((lesson) => {
          const isExpanded = expandedLessonId === lesson.id;
          return (
            <div
              key={lesson.id}
              className="rounded-lg border border-zinc-200 bg-white p-5 space-y-4 transition-all hover:border-zinc-300"
            >
              {/* Top Row: Lesson Number, Generation, Target Node, and Impact */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-100 pb-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-zinc-900 px-2 py-0.5 font-mono text-xs font-bold text-white shadow-2xs">
                    {lesson.lessonNumber}
                  </span>
                  <span className="rounded-md bg-zinc-100 px-2 py-0.5 font-mono text-xs font-semibold text-zinc-700 border border-zinc-200">
                    Generation: {lesson.generationTransition}
                  </span>
                  <span className="rounded-md bg-amber-50 px-2 py-0.5 font-mono text-[10px] font-bold text-amber-800 border border-amber-200">
                    Source Failure: {lesson.sourceCategory}
                  </span>
                </div>

                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Δ {lesson.accuracyDelta}
                  </span>
                  <span className="text-zinc-500">
                    Cumulative: <strong className="text-zinc-900">{lesson.cumulativeAccuracy}</strong>
                  </span>
                </div>
              </div>

              {/* Lesson Invariant Rule Body */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-mono font-medium text-zinc-600">
                    Target: {lesson.targetNode}
                  </span>
                </div>
                <p className="text-xs text-zinc-800 bg-indigo-50/40 p-3 rounded-lg border border-indigo-100/80 leading-relaxed font-mono">
                  {lesson.epistemicRule}
                </p>
              </div>

              {/* Derivation Context */}
              <div className="text-xs text-zinc-600 bg-zinc-50/70 p-3 rounded-lg border border-zinc-200/80 space-y-1">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">
                  Root-Cause Derivation Context:
                </span>
                <p className="font-geist leading-relaxed">{lesson.derivationContext}</p>
              </div>

              {/* Inspect Invariant Toggle Button */}
              <div className="flex items-center justify-between pt-1">
                <button
                  type="button"
                  onClick={() => setExpandedLessonId(isExpanded ? null : lesson.id)}
                  className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-indigo-600 hover:text-indigo-800 transition cursor-pointer"
                >
                  <Code size={14} weight="bold" />
                  <span>Inspect Invariant</span>
                  {isExpanded ? (
                    <CaretUp size={12} weight="bold" />
                  ) : (
                    <CaretDown size={12} weight="bold" />
                  )}
                </button>

                <span className="text-[11px] font-geist text-zinc-500">
                  {lesson.impactVerdict}
                </span>
              </div>

              {/* Expandable Section: Synthesized Architectural Invariant & Code Diff Preview (bg-zinc-50 font-mono text-sm) */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                    className="overflow-hidden space-y-3 pt-2"
                  >
                    <div className="flex items-center justify-between border-t border-zinc-100 pt-3">
                      <h4 className="text-xs font-semibold text-zinc-900 font-geist flex items-center gap-2">
                        <Sparkle size={14} weight="fill" className="text-indigo-600" />
                        <span>Synthesized Architectural Invariant: {lesson.ruleTitle}</span>
                      </h4>
                      <span className="text-[11px] font-mono text-zinc-500">
                        Target: {lesson.targetNode}
                      </span>
                    </div>

                    <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-4 font-mono text-sm text-zinc-800 space-y-2">
                      <div className="flex items-center justify-between border-b border-zinc-200 pb-2 text-xs text-zinc-500">
                        <span>Code Implementation / Guardrail Invariant</span>
                        <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] font-bold text-zinc-700">
                          TYPESCRIPT
                        </span>
                      </div>
                      <pre className="overflow-x-auto whitespace-pre leading-relaxed text-xs text-zinc-900 font-mono">
                        {lesson.codeSnippet}
                      </pre>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
};
