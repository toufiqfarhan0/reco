"use client";

import React, { useState } from "react";
import { Scorecard, ScorecardComparison } from "@/lib/types";
import {
  ShieldCheck,
  Zap,
  TrendingUp,
  DollarSign,
  Clock,
  ArrowRight,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Award,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface ScorecardViewProps {
  scorecard: Scorecard;
  comparison?: ScorecardComparison;
  onProceedToUnderstand: () => void;
}

export const ScorecardView: React.FC<ScorecardViewProps> = ({
  scorecard,
  comparison,
  onProceedToUnderstand,
}) => {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case "PARETO_DOMINANT":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 font-mono text-xs font-bold text-emerald-700 border border-emerald-200">
            <Award className="h-3.5 w-3.5" />
            PARETO DOMINANT
          </span>
        );
      case "TRADEOFF":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 font-mono text-xs font-bold text-amber-700 border border-amber-200">
            <TrendingUp className="h-3.5 w-3.5" />
            TRADEOFF IDENTIFIED
          </span>
        );
      case "REGRESSION":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 font-mono text-xs font-bold text-red-700 border border-red-200">
            <XCircle className="h-3.5 w-3.5" />
            REGRESSION DETECTED
          </span>
        );
      default:
        return (
          <span className="rounded-full bg-zinc-100 px-3 py-1 font-mono text-xs font-medium text-zinc-600 border border-zinc-200">
            NEUTRAL
          </span>
        );
    }
  };

  return (
    <div className="space-y-5">
      {/* Header & Pareto Verdict Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-zinc-200/90 rounded-2xl p-5 shadow-2xs">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 02
            </span>
            <h2 className="text-lg font-bold tracking-tight text-zinc-950">
              RUN: 4-Axis Scorecard & Empirical Evaluation
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl">
            Evaluating on <span className="font-mono font-semibold text-zinc-900">{scorecard.split}</span> split ({scorecard.total_cases} test cases). Deterministic scoring across all 4 canonical axes.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {comparison && getVerdictBadge(comparison.verdict)}
          <button
            type="button"
            onClick={onProceedToUnderstand}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 active:scale-[0.98] cursor-pointer"
          >
            <span>Diagnose Failures (Stage 03)</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* 4 Canonical Axes Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Axis 1: Accuracy */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs transition hover:border-zinc-300">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-500">
              1. Accuracy
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-mono font-bold ${
                  comparison.accuracy_delta > 0
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : comparison.accuracy_delta < 0
                    ? "bg-red-50 text-red-700 border border-red-200"
                    : "bg-zinc-100 text-zinc-600"
                }`}
              >
                Δ {comparison.accuracy_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono">
              {(scorecard.accuracy * 100).toFixed(1)}%
            </span>
            <span className="text-xs font-mono text-zinc-400">
              ({scorecard.accurate_cases}/{scorecard.total_cases} passed)
            </span>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            Ground-truth match rate on partitioned cases.
          </p>
        </div>

        {/* Axis 2: Reliability */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs transition hover:border-zinc-300">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-500">
              2. Reliability
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-mono font-bold ${
                  comparison.reliability_delta >= 0
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-red-50 text-red-700 border border-red-200"
                }`}
              >
                Δ {comparison.reliability_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono">
              {(scorecard.reliability * 100).toFixed(1)}%
            </span>
            <span className="text-xs font-mono text-zinc-400">
              ({scorecard.reliable_cases}/{scorecard.total_cases} error-free)
            </span>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            Error-free execution rate (zero exceptions/panics).
          </p>
        </div>

        {/* Axis 3: Cost */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs transition hover:border-zinc-300">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-500">
              3. Cost (USD)
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-mono font-bold ${
                  comparison.cost_delta_usd <= 0
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-amber-50 text-amber-700 border border-amber-200"
                }`}
              >
                Δ {comparison.cost_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono">
              ${scorecard.cost_usd.toFixed(4)}
            </span>
            <span className="text-xs font-mono text-zinc-400">total</span>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            Exact token-derived inference and tool cost.
          </p>
        </div>

        {/* Axis 4: Speed / Latency */}
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs transition hover:border-zinc-300">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-500">
              4. Speed (Wall-Clock)
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-mono font-bold ${
                  comparison.latency_delta_ms <= 0
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "bg-red-50 text-red-700 border border-red-200"
                }`}
              >
                Δ {comparison.latency_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono">
              {scorecard.latency_ms.toFixed(1)} ms
            </span>
            <span className="text-xs font-mono text-zinc-400">
              (~{scorecard.avg_latency_ms.toFixed(1)} ms/case)
            </span>
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            Total wall-clock runtime across test cases.
          </p>
        </div>
      </div>

      {/* Comparison Delta Badges Table if comparison exists */}
      {comparison && (
        <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950">
              Multi-Axis Comparison: {comparison.candidate_name} vs {comparison.baseline_name}
            </h3>
            <span className="text-[10px] font-mono text-zinc-400">
              Empirical Delta Ledger
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-zinc-200/70">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-50/70 border-b border-zinc-200/70 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
                <tr>
                  <th className="py-2.5 px-3.5">Axis</th>
                  <th className="py-2.5 px-3.5">Baseline</th>
                  <th className="py-2.5 px-3.5">Candidate</th>
                  <th className="py-2.5 px-3.5">Delta (Δ) Badge</th>
                  <th className="py-2.5 px-3.5">Assessment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 font-mono">
                <tr className="hover:bg-zinc-50/50 transition-colors">
                  <td className="py-2.5 px-3.5 font-semibold text-zinc-950">1. Accuracy</td>
                  <td className="py-2.5 px-3.5 text-zinc-500">{(comparison.baseline.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3.5 text-zinc-950 font-bold">{(comparison.candidate.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3.5 text-emerald-700 font-bold">{comparison.accuracy_badge}</td>
                  <td className="py-2.5 px-3.5 text-emerald-700 font-medium">[Improved]</td>
                </tr>
                <tr className="hover:bg-zinc-50/50 transition-colors">
                  <td className="py-2.5 px-3.5 font-semibold text-zinc-950">2. Reliability</td>
                  <td className="py-2.5 px-3.5 text-zinc-500">{(comparison.baseline.reliability * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3.5 text-zinc-950 font-bold">{(comparison.candidate.reliability * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3.5 text-zinc-500">{comparison.reliability_badge}</td>
                  <td className="py-2.5 px-3.5 text-zinc-400">[Equal]</td>
                </tr>
                <tr className="hover:bg-zinc-50/50 transition-colors">
                  <td className="py-2.5 px-3.5 font-semibold text-zinc-950">3. Cost</td>
                  <td className="py-2.5 px-3.5 text-zinc-500">${comparison.baseline.cost_usd.toFixed(4)}</td>
                  <td className="py-2.5 px-3.5 text-zinc-950 font-bold">${comparison.candidate.cost_usd.toFixed(4)}</td>
                  <td className="py-2.5 px-3.5 text-emerald-700 font-bold">{comparison.cost_badge}</td>
                  <td className="py-2.5 px-3.5 text-emerald-700 font-medium">[Cheaper]</td>
                </tr>
                <tr className="hover:bg-zinc-50/50 transition-colors">
                  <td className="py-2.5 px-3.5 font-semibold text-zinc-950">4. Speed</td>
                  <td className="py-2.5 px-3.5 text-zinc-500">{comparison.baseline.latency_ms.toFixed(1)} ms</td>
                  <td className="py-2.5 px-3.5 text-zinc-950 font-bold">{comparison.candidate.latency_ms.toFixed(1)} ms</td>
                  <td className="py-2.5 px-3.5 text-emerald-700 font-bold">{comparison.latency_badge}</td>
                  <td className="py-2.5 px-3.5 text-emerald-700 font-medium">[Faster]</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Per-Case Breakdown Table */}
      <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-100 pb-3">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950">
              Partitioned Benchmark Case Results ({scorecard.case_results.length} cases)
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Click any row to inspect expected ground truth vs actual agent telemetry
            </p>
          </div>
          <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200">
            Interactive Inspector
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-zinc-200/70">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50/70 border-b border-zinc-200/70 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
              <tr>
                <th className="py-2.5 px-3.5">Case ID</th>
                <th className="py-2.5 px-3.5">Description</th>
                <th className="py-2.5 px-3.5">Accuracy</th>
                <th className="py-2.5 px-3.5">Reliability</th>
                <th className="py-2.5 px-3.5">Latency</th>
                <th className="py-2.5 px-3.5">Diagnostics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 font-mono">
              {scorecard.case_results.map((c) => {
                const isSelected = selectedCaseId === c.case_id;
                return (
                  <React.Fragment key={c.case_id}>
                    <tr
                      onClick={() => setSelectedCaseId(isSelected ? null : c.case_id)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? "bg-zinc-50/90 font-medium" : "hover:bg-zinc-50/50"
                      }`}
                    >
                      <td className="py-2.5 px-3.5 font-semibold text-zinc-950">{c.case_id}</td>
                      <td className="py-2.5 px-3.5 text-zinc-600 font-sans">{c.name}</td>
                      <td className="py-2.5 px-3.5">
                        {c.is_accurate ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                            <CheckCircle2 className="h-3 w-3" /> MATCH
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-700 font-medium">
                            <XCircle className="h-3 w-3" /> MISMATCH
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3.5">
                        {c.is_reliable ? (
                          <span className="text-emerald-700 font-medium">PASS</span>
                        ) : (
                          <span className="text-red-700 font-medium">FAIL</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3.5 text-zinc-600">{c.latency_ms.toFixed(1)} ms</td>
                      <td className="py-2.5 px-3.5">
                        {c.error ? (
                          <span className="text-red-700 truncate max-w-[200px] block" title={c.error}>
                            {c.error}
                          </span>
                        ) : (
                          <span className="text-zinc-400">-</span>
                        )}
                      </td>
                    </tr>

                    {/* Expandable Case Details */}
                    {isSelected && (
                      <tr className="bg-zinc-50/60">
                        <td colSpan={6} className="p-4 border-b border-zinc-100">
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-[11px]">
                            <div className="rounded-xl border border-zinc-200/80 bg-white p-3.5 shadow-2xs">
                              <span className="text-zinc-400 font-mono text-[10px] font-bold uppercase tracking-wider block mb-1">
                                Expected Ground Truth:
                              </span>
                              <pre className="text-emerald-700 whitespace-pre-wrap font-mono leading-relaxed">
                                {c.expected_output || "Ground truth match verified"}
                              </pre>
                            </div>
                            <div className="rounded-xl border border-zinc-200/80 bg-white p-3.5 shadow-2xs">
                              <span className="text-zinc-400 font-mono text-[10px] font-bold uppercase tracking-wider block mb-1">
                                Actual Agent Output:
                              </span>
                              <pre className={`whitespace-pre-wrap font-mono leading-relaxed ${c.is_accurate ? "text-zinc-900" : "text-red-700"}`}>
                                {c.actual_output || "Execution completed"}
                              </pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
