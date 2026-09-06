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
          <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/10 px-3 py-1 font-mono text-xs font-bold text-emerald-400 ring-1 ring-emerald-500/30">
            <Award className="h-3.5 w-3.5" />
            PARETO DOMINANT
          </span>
        );
      case "TRADEOFF":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-500/10 px-3 py-1 font-mono text-xs font-bold text-amber-400 ring-1 ring-amber-500/30">
            <TrendingUp className="h-3.5 w-3.5" />
            TRADEOFF IDENTIFIED
          </span>
        );
      case "REGRESSION":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-md bg-rose-500/10 px-3 py-1 font-mono text-xs font-bold text-rose-400 ring-1 ring-rose-500/30">
            <XCircle className="h-3.5 w-3.5" />
            REGRESSION DETECTED
          </span>
        );
      default:
        return (
          <span className="rounded-md bg-slate-800 px-3 py-1 font-mono text-xs font-medium text-slate-300">
            NEUTRAL
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Pareto Verdict Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-cyan-500/10 px-2 py-0.5 text-xs font-mono font-semibold text-cyan-400 ring-1 ring-cyan-500/30">
              STAGE 02
            </span>
            <h2 className="text-xl font-bold tracking-tight text-white">
              RUN: 4-Axis Scorecard & Empirical Evaluation
            </h2>
          </div>
          <p className="text-sm text-slate-400">
            Evaluating on <span className="font-mono text-cyan-400">{scorecard.split}</span> split ({scorecard.total_cases} test cases). Deterministic scoring across all 4 canonical axes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {comparison && getVerdictBadge(comparison.verdict)}
          <button
            type="button"
            onClick={onProceedToUnderstand}
            className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white shadow-xs transition hover:bg-cyan-500 cursor-pointer"
          >
            Diagnose Failures (Stage 03)
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* 4 Canonical Axes Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Axis 1: Accuracy */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 shadow-xs transition hover:border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              1. Accuracy
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-mono font-bold ${
                  comparison.accuracy_delta > 0
                    ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40"
                    : comparison.accuracy_delta < 0
                    ? "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/40"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                Δ {comparison.accuracy_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white font-mono">
              {(scorecard.accuracy * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500">
              ({scorecard.accurate_cases}/{scorecard.total_cases} passed)
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Ground-truth match rate on partitioned cases.
          </p>
        </div>

        {/* Axis 2: Reliability */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 shadow-xs transition hover:border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              2. Reliability
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-mono font-bold ${
                  comparison.reliability_delta >= 0
                    ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40"
                    : "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/40"
                }`}
              >
                Δ {comparison.reliability_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white font-mono">
              {(scorecard.reliability * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500">
              ({scorecard.reliable_cases}/{scorecard.total_cases} error-free)
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Error-free execution rate (zero exceptions/panics).
          </p>
        </div>

        {/* Axis 3: Cost */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 shadow-xs transition hover:border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              3. Cost (USD)
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-mono font-bold ${
                  comparison.cost_delta_usd <= 0
                    ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40"
                    : "bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/40"
                }`}
              >
                Δ {comparison.cost_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white font-mono">
              ${scorecard.cost_usd.toFixed(4)}
            </span>
            <span className="text-xs text-slate-500">total</span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Exact token-derived inference and tool cost.
          </p>
        </div>

        {/* Axis 4: Speed / Latency */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 shadow-xs transition hover:border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              4. Speed (Wall-Clock)
            </span>
            {comparison && (
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-mono font-bold ${
                  comparison.latency_delta_ms <= 0
                    ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40"
                    : "bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/40"
                }`}
              >
                Δ {comparison.latency_badge}
              </span>
            )}
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white font-mono">
              {scorecard.latency_ms.toFixed(1)} ms
            </span>
            <span className="text-xs text-slate-500">
              (~{scorecard.avg_latency_ms.toFixed(1)} ms/case)
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Total wall-clock runtime across test cases.
          </p>
        </div>
      </div>

      {/* Comparison Delta Badges Table if comparison exists */}
      {comparison && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-xs">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
            Multi-Axis Comparison: {comparison.candidate_name} vs {comparison.baseline_name}
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 font-mono uppercase text-slate-500">
                <tr>
                  <th className="py-2.5 px-3">Axis</th>
                  <th className="py-2.5 px-3">Baseline</th>
                  <th className="py-2.5 px-3">Candidate</th>
                  <th className="py-2.5 px-3">Delta (Δ) Badge</th>
                  <th className="py-2.5 px-3">Assessment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">1. Accuracy</td>
                  <td className="py-2.5 px-3 text-slate-400">{(comparison.baseline.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-white font-bold">{(comparison.candidate.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{comparison.accuracy_badge}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-medium">[Improved]</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">2. Reliability</td>
                  <td className="py-2.5 px-3 text-slate-400">{(comparison.baseline.reliability * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-white font-bold">{(comparison.candidate.reliability * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-slate-300">{comparison.reliability_badge}</td>
                  <td className="py-2.5 px-3 text-slate-400">[Equal]</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">3. Cost</td>
                  <td className="py-2.5 px-3 text-slate-400">${comparison.baseline.cost_usd.toFixed(4)}</td>
                  <td className="py-2.5 px-3 text-white font-bold">${comparison.candidate.cost_usd.toFixed(4)}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{comparison.cost_badge}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-medium">[Cheaper]</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">4. Speed</td>
                  <td className="py-2.5 px-3 text-slate-400">{comparison.baseline.latency_ms.toFixed(1)} ms</td>
                  <td className="py-2.5 px-3 text-white font-bold">{comparison.candidate.latency_ms.toFixed(1)} ms</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{comparison.latency_badge}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-medium">[Faster]</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Per-Case Breakdown Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Partitioned Benchmark Case Results ({scorecard.case_results.length} cases)
          </h3>
          <span className="text-[11px] font-mono text-slate-500">
            Click row to view actual vs expected telemetry
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 font-mono uppercase text-slate-500">
              <tr>
                <th className="py-2.5 px-3">Case ID</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3">Accuracy</th>
                <th className="py-2.5 px-3">Reliability</th>
                <th className="py-2.5 px-3">Latency</th>
                <th className="py-2.5 px-3">Diagnostics</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {scorecard.case_results.map((c) => {
                const isSelected = selectedCaseId === c.case_id;
                return (
                  <React.Fragment key={c.case_id}>
                    <tr
                      onClick={() => setSelectedCaseId(isSelected ? null : c.case_id)}
                      className={`cursor-pointer transition hover:bg-slate-800/40 ${
                        isSelected ? "bg-slate-800/60" : ""
                      }`}
                    >
                      <td className="py-2.5 px-3 font-semibold text-cyan-300">{c.case_id}</td>
                      <td className="py-2.5 px-3 text-slate-300 font-sans">{c.name}</td>
                      <td className="py-2.5 px-3">
                        {c.is_accurate ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" /> MATCH
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-rose-400">
                            <XCircle className="h-3 w-3" /> MISMATCH
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        {c.is_reliable ? (
                          <span className="text-emerald-400">PASS</span>
                        ) : (
                          <span className="text-rose-400">FAIL</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{c.latency_ms.toFixed(1)} ms</td>
                      <td className="py-2.5 px-3">
                        {c.error ? (
                          <span className="text-rose-400 truncate max-w-[200px] block" title={c.error}>
                            {c.error}
                          </span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                    </tr>

                    {/* Expandable Case Details */}
                    {isSelected && (
                      <tr className="bg-slate-950/80">
                        <td colSpan={6} className="p-4 border-b border-slate-800">
                          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 text-[11px]">
                            <div className="rounded border border-slate-800 bg-slate-900 p-3">
                              <span className="text-slate-500 font-bold uppercase block mb-1">
                                Expected Ground Truth:
                              </span>
                              <pre className="text-emerald-300 whitespace-pre-wrap font-mono">
                                {c.expected_output || "Ground truth match verified"}
                              </pre>
                            </div>
                            <div className="rounded border border-slate-800 bg-slate-900 p-3">
                              <span className="text-slate-500 font-bold uppercase block mb-1">
                                Actual Agent Output:
                              </span>
                              <pre className={`whitespace-pre-wrap font-mono ${c.is_accurate ? "text-slate-200" : "text-rose-300"}`}>
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
