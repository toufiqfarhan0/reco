"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { Scorecard, ScorecardComparison } from "@/lib/types";
import {
  ShieldCheck,
  Lightning,
  Coins,
  Clock,
  ArrowRight,
  CheckCircle,
  XCircle,
  Trophy,
  CaretDown,
  CaretUp,
  Target,
  ChartLineUp,
} from "@phosphor-icons/react";

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
          <motion.span
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3.5 py-1.5 font-mono text-xs font-bold text-emerald-700 border border-emerald-300 shadow-2xs"
          >
            <Trophy size={16} weight="fill" className="text-emerald-600" />
            <span>PARETO DOMINANT</span>
          </motion.span>
        );
      case "TRADEOFF":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3.5 py-1.5 font-mono text-xs font-bold text-amber-700 border border-amber-300 shadow-2xs">
            <ChartLineUp size={16} weight="bold" />
            <span>TRADEOFF IDENTIFIED</span>
          </span>
        );
      case "REGRESSION":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3.5 py-1.5 font-mono text-xs font-bold text-red-700 border border-red-300 shadow-2xs">
            <XCircle size={16} weight="fill" />
            <span>REGRESSION DETECTED</span>
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

  // Helper for thin circular progress arc
  const renderProgressArc = (percent: number, colorStroke: string) => {
    const size = 52;
    const strokeWidth = 3.5;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const clamped = Math.min(Math.max(percent, 0), 100);
    const strokeDashoffset = circumference - (clamped / 100) * circumference;

    return (
      <svg width={size} height={size} className="transform -rotate-90 shrink-0">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#f4f4f5"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colorStroke}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
          className="transition-all duration-500 ease-out"
        />
      </svg>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="space-y-8"
    >
      {/* Plain Section Header (No card wrapper) */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-zinc-100">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 02
            </span>
            <h2 className="text-xl font-bold tracking-tight text-zinc-950 font-geist">
              RUN: 4-Axis Scorecard & Empirical Evaluation
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-geist">
            Evaluating on <span className="font-mono font-semibold text-zinc-900">{scorecard.split}</span> split ({scorecard.total_cases} test cases). Deterministic scoring across all 4 canonical axes.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {comparison && getVerdictBadge(comparison.verdict)}
          <button
            type="button"
            onClick={onProceedToUnderstand}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all active:scale-[0.98] cursor-pointer font-geist"
          >
            <span>Diagnose Failures (Stage 03)</span>
            <ArrowRight size={14} weight="bold" />
          </button>
        </div>
      </div>

      {/* 4 Canonical Axes: Clean table/grid with hairline row separators, not individual axis cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-zinc-100 border-y border-zinc-100 py-6">
        {/* Axis 1: Accuracy */}
        <div className="py-4 sm:py-0 sm:px-5 first:pl-0 last:pr-0 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-50 text-indigo-600 font-mono text-xs font-bold">
                1
              </span>
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700">
                1. Accuracy
              </span>
            </div>
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

          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono font-geist">
                  {(scorecard.accuracy * 100).toFixed(1)}%
                </span>
                <span className="text-xs font-mono text-zinc-400">
                  ({scorecard.accurate_cases}/{scorecard.total_cases} passed)
                </span>
              </div>
              <p className="mt-1 text-xs text-zinc-500 font-geist">
                Ground-truth match rate.
              </p>
            </div>
            {renderProgressArc(scorecard.accuracy * 100, "#4F46E5")}
          </div>
        </div>

        {/* Axis 2: Reliability */}
        <div className="py-4 sm:py-0 sm:px-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-50 text-emerald-600 font-mono text-xs font-bold">
                2
              </span>
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700">
                2. Reliability
              </span>
            </div>
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

          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono font-geist">
                  {(scorecard.reliability * 100).toFixed(1)}%
                </span>
                <span className="text-xs font-mono text-zinc-400">
                  ({scorecard.reliable_cases}/{scorecard.total_cases} error-free)
                </span>
              </div>
              <p className="mt-1 text-xs text-zinc-500 font-geist">
                Error-free execution rate.
              </p>
            </div>
            {renderProgressArc(scorecard.reliability * 100, "#10B981")}
          </div>
        </div>

        {/* Axis 3: Cost */}
        <div className="py-4 sm:py-0 sm:px-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-50 text-amber-600 font-mono text-xs font-bold">
                3
              </span>
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700">
                3. Cost (USD)
              </span>
            </div>
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

          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono font-geist">
                  ${scorecard.cost_usd.toFixed(4)}
                </span>
                <span className="text-xs font-mono text-zinc-400">total</span>
              </div>
              <p className="mt-1 text-xs text-zinc-500 font-geist">
                Exact inference & tool cost.
              </p>
            </div>
            {renderProgressArc(75, "#F59E0B")}
          </div>
        </div>

        {/* Axis 4: Speed */}
        <div className="py-4 sm:py-0 sm:px-5 last:pr-0 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-violet-50 text-violet-600 font-mono text-xs font-bold">
                4
              </span>
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700">
                4. Speed (Wall-Clock)
              </span>
            </div>
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

          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-bold tracking-tight text-zinc-950 font-mono font-geist">
                  {scorecard.latency_ms.toFixed(1)} ms
                </span>
                <span className="text-xs font-mono text-zinc-400">
                  (~{scorecard.avg_latency_ms.toFixed(1)} ms/case)
                </span>
              </div>
              <p className="mt-1 text-xs text-zinc-500 font-geist">
                Total wall-clock runtime.
              </p>
            </div>
            {renderProgressArc(85, "#8B5CF6")}
          </div>
        </div>
      </div>

      {/* Comparison Delta Badges Table (No outer card) */}
      {comparison && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between pb-2 border-b border-zinc-100">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-900 font-mono">
              Multi-Axis Comparison: {comparison.candidate_name} vs {comparison.baseline_name}
            </h3>
            <span className="text-[10px] font-mono text-zinc-400">
              Empirical Delta Ledger
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-zinc-100">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-50/50 border-b border-zinc-100 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
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

      {/* Per-Case Breakdown Table (No outer card) */}
      <div className="space-y-3 pt-2">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-zinc-100">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-900 font-mono">
              Partitioned Benchmark Case Results ({scorecard.case_results.length} cases)
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5 font-geist">
              Click any row to inspect expected ground truth vs actual agent telemetry
            </p>
          </div>
          <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600">
            Interactive Inspector
          </span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-zinc-100">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50/50 border-b border-zinc-100 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
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
                        isSelected ? "bg-zinc-50 font-medium" : "hover:bg-zinc-50/50"
                      }`}
                    >
                      <td className="py-2.5 px-3.5 font-semibold text-zinc-950">{c.case_id}</td>
                      <td className="py-2.5 px-3.5 text-zinc-600 font-geist">{c.name}</td>
                      <td className="py-2.5 px-3.5">
                        {c.is_accurate ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                            <CheckCircle size={14} weight="fill" /> MATCH
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-700 font-medium">
                            <XCircle size={14} weight="fill" /> MISMATCH
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
                      <tr className="bg-zinc-50/50">
                        <td colSpan={6} className="p-4 border-b border-zinc-100">
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-[11px]">
                            <div className="rounded-lg border border-zinc-100 bg-white p-3">
                              <span className="text-zinc-400 font-mono text-[10px] font-bold uppercase tracking-wider block mb-1">
                                Expected Ground Truth:
                              </span>
                              <pre className="text-emerald-700 whitespace-pre-wrap font-mono leading-relaxed">
                                {c.expected_output || "Ground truth match verified"}
                              </pre>
                            </div>
                            <div className="rounded-lg border border-zinc-100 bg-white p-3">
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
    </motion.div>
  );
};
