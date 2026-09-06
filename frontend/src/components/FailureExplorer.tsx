"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { FailureDiagnostic } from "@/lib/types";
import { ALL_TAXONOMY_CATEGORIES } from "@/lib/mockData";
import {
  Funnel,
  MagnifyingGlass,
  Wrench,
  WarningCircle,
  CheckCircle,
  CaretDown,
  CaretUp,
  ArrowRight,
  ShieldWarning,
  Bug,
} from "@phosphor-icons/react";

interface FailureExplorerProps {
  diagnostics: FailureDiagnostic[];
  onProceedToImprove: () => void;
}

export const FailureExplorer: React.FC<FailureExplorerProps> = ({
  diagnostics,
  onProceedToImprove,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(
    diagnostics[0]?.case_id || null
  );

  // Compute category frequency counts
  const categoryCounts = React.useMemo(() => {
    const counts: Record<string, number> = {};
    diagnostics.forEach((d) => {
      counts[d.category] = (counts[d.category] || 0) + 1;
    });
    return counts;
  }, [diagnostics]);

  // Filter diagnostics
  const filteredDiagnostics = diagnostics.filter((d) => {
    const matchesCategory =
      selectedCategory === "all" || d.category === selectedCategory;
    const matchesSearch =
      searchQuery.trim() === "" ||
      d.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.case_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.root_cause.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.symptoms.some((s) =>
        s.toLowerCase().includes(searchQuery.toLowerCase())
      );
    return matchesCategory && matchesSearch;
  });

  const getSeverityPill = (confidence: number) => {
    if (confidence >= 0.9) {
      return (
        <span className="rounded-md bg-red-100 text-red-800 border border-red-200 px-2 py-0.5 text-[10px] font-mono font-bold">
          HIGH SEVERITY
        </span>
      );
    }
    if (confidence >= 0.8) {
      return (
        <span className="rounded-md bg-amber-100 text-amber-800 border border-amber-200 px-2 py-0.5 text-[10px] font-mono font-bold">
          MEDIUM SEVERITY
        </span>
      );
    }
    return (
      <span className="rounded-md bg-zinc-100 text-zinc-700 border border-zinc-200 px-2 py-0.5 text-[10px] font-mono font-bold">
        LOW SEVERITY
      </span>
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
              STAGE 03
            </span>
            <h2 className="text-xl font-bold tracking-tight text-zinc-950 font-geist">
              UNDERSTAND: 12-Category Failure Diagnostics Taxonomy
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-geist">
            Isolate underlying root causes from intermediate observable symptoms to prescribe targeted autonomous mutations.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToImprove}
          className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all active:scale-[0.98] cursor-pointer font-geist"
        >
          <span>Synthesize Mutations (Stage 04)</span>
          <ArrowRight size={14} weight="bold" />
        </button>
      </div>

      {/* 12-Category Taxonomy Interactive Pills Matrix (No outer card) */}
      <div className="space-y-3 pb-5 border-b border-zinc-100">
        <div className="flex items-center justify-between pb-1">
          <div className="flex items-center gap-2">
            <Funnel size={16} weight="duotone" className="text-zinc-500" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-900 font-mono">
              Root-Cause Taxonomy Classification Matrix (12 Categories)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-zinc-400">
            Active Failures: {diagnostics.length}
          </span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => setSelectedCategory("all")}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-mono transition-all cursor-pointer ${
              selectedCategory === "all"
                ? "bg-indigo-600 text-white font-medium"
                : "border border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900 hover:bg-zinc-50"
            }`}
          >
            <span>All Categories</span>
            <span
              className={`rounded px-1.5 py-0.2 text-[10px] font-bold ${
                selectedCategory === "all"
                  ? "bg-white/20 text-white"
                  : "bg-zinc-100 text-zinc-700"
              }`}
            >
              {diagnostics.length}
            </span>
          </button>

          {ALL_TAXONOMY_CATEGORIES.map((cat) => {
            const count = categoryCounts[cat.id] || 0;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-mono transition-all cursor-pointer ${
                  isSelected
                    ? "bg-indigo-600 text-white font-medium"
                    : count > 0
                    ? "border border-amber-300 bg-amber-50 text-amber-800 hover:border-amber-400"
                    : "border border-zinc-200 bg-white text-zinc-400 hover:text-zinc-700 hover:bg-zinc-50"
                }`}
                title={cat.description}
              >
                <span>{cat.name}</span>
                {count > 0 && (
                  <span
                    className={`rounded px-1 text-[10px] font-bold ${
                      isSelected
                        ? "bg-white/20 text-white"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Search Filter Bar */}
      <div className="relative">
        <MagnifyingGlass size={16} className="absolute left-3.5 top-2.5 text-zinc-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search failure cases, symptoms, root causes..."
          className="w-full rounded-lg border border-zinc-200 bg-white py-2 pl-10 pr-4 text-xs text-zinc-900 placeholder-zinc-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors font-mono"
        />
      </div>

      {/* Failure taxonomy entries: plain list with left-border accent (3px indigo-600 left bar on active) instead of cards */}
      <div className="divide-y divide-zinc-100 border-y border-zinc-100">
        {filteredDiagnostics.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-400 font-mono">
            No failure diagnostics match the selected filter.
          </div>
        ) : (
          filteredDiagnostics.map((diag) => {
            const isExpanded = expandedCaseId === diag.case_id;
            return (
              <div
                key={diag.case_id}
                className={`transition-all ${
                  isExpanded
                    ? "border-l-[3px] border-l-indigo-600 bg-zinc-50/40"
                    : "border-l-[3px] border-l-transparent hover:bg-zinc-50/20"
                }`}
              >
                {/* List Item Header */}
                <button
                  type="button"
                  onClick={() => setExpandedCaseId(isExpanded ? null : diag.case_id)}
                  className="w-full text-left py-4 px-3 flex flex-wrap items-center justify-between gap-3 cursor-pointer select-none transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-bold text-zinc-900">
                        {diag.case_id}
                      </span>
                      {/* Category Badge */}
                      <span className="rounded bg-amber-50 px-2 py-0.5 text-[10px] font-mono font-bold text-amber-800 border border-amber-200">
                        {diag.category}
                      </span>
                      {/* Severity Pill */}
                      {getSeverityPill(diag.confidence)}
                    </div>

                    <h4 className="mt-1 text-sm font-semibold text-zinc-900 font-geist">
                      {diag.case_name}
                    </h4>

                    {/* Root Cause Preview */}
                    <div className="mt-1 flex items-start gap-1.5 text-xs text-zinc-600 font-geist line-clamp-1">
                      <span className="font-mono font-semibold text-zinc-800 shrink-0">
                        Root Cause:
                      </span>
                      <span className="text-zinc-500 truncate">{diag.root_cause}</span>
                    </div>

                    {/* Remediation Preview */}
                    <div className="mt-0.5 flex items-start gap-1.5 text-xs text-zinc-600 font-geist line-clamp-1">
                      <span className="font-mono font-semibold text-indigo-700 shrink-0">
                        Remediation:
                      </span>
                      <span className="text-indigo-600 truncate">{diag.remedy_suggestion}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right hidden sm:block">
                      <span className="text-[10px] font-mono text-zinc-400 block">Confidence</span>
                      <span className="text-xs font-mono font-bold text-zinc-900">
                        {(diag.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="p-1 text-zinc-400 rounded">
                      {isExpanded ? (
                        <CaretUp size={16} weight="bold" />
                      ) : (
                        <CaretDown size={16} weight="bold" />
                      )}
                    </div>
                  </div>
                </button>

                {/* Expandable Details */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                      className="px-4 pb-5 pt-2 space-y-4"
                    >
                      {/* Symptom vs Root Cause Panels */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Panel 1: Observable Symptoms */}
                        <div className="rounded-lg border border-red-200 bg-white p-3.5 space-y-1.5">
                          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-red-700 font-mono">
                            <WarningCircle size={15} weight="bold" />
                            <span>Observable Symptoms</span>
                          </div>
                          <p className="text-[11px] text-zinc-500 font-geist">
                            External test failure artifacts & visible discrepancies:
                          </p>
                          <ul className="space-y-1 pt-1 font-mono text-xs">
                            {diag.symptoms.map((sym, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-zinc-900">
                                <span className="text-red-500 font-bold">•</span>
                                <span>{sym}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Panel 2: Isolated Root Cause */}
                        <div className="rounded-lg border border-indigo-200 bg-white p-3.5 space-y-1.5">
                          <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-indigo-700 font-mono">
                            <CheckCircle size={15} weight="bold" />
                            <span>Isolated Root Cause</span>
                          </div>
                          <p className="text-[11px] text-zinc-500 font-geist">
                            Underlying architectural defect or configuration gap:
                          </p>
                          <p className="text-xs text-zinc-900 pt-1 leading-relaxed font-mono">
                            {diag.root_cause}
                          </p>
                        </div>
                      </div>

                      {/* Remediation Panel: Targeted Autonomous Remedy */}
                      <div className="rounded-lg border border-zinc-200 bg-white p-3.5 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-950 font-mono">
                            <Wrench size={15} weight="duotone" className="text-zinc-600" />
                            <span>Targeted Autonomous Remedy</span>
                          </div>
                          <span className="font-mono text-xs font-semibold text-emerald-700">
                            Confidence: {(diag.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        <p className="text-xs text-zinc-600 leading-relaxed font-geist">
                          {diag.remedy_suggestion}
                        </p>

                        <div className="flex flex-wrap items-center gap-4 border-t border-zinc-100 pt-2 text-xs font-mono">
                          <div>
                            <span className="text-zinc-400">Target Node: </span>
                            <span className="text-zinc-950 font-semibold">
                              {diag.target_node_id || "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="text-zinc-400">Recommended Mutator: </span>
                            <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-zinc-950 border border-zinc-200 font-semibold">
                              {diag.recommended_mutator}
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        )}
      </div>
    </motion.div>
  );
};
