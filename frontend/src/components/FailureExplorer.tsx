"use client";

import React, { useState } from "react";
import { FailureDiagnostic, FailureCategory } from "@/lib/types";
import { ALL_TAXONOMY_CATEGORIES } from "@/lib/mockData";
import {
  AlertTriangle,
  ArrowRight,
  Filter,
  Search,
  CheckCircle2,
  Wrench,
  HelpCircle,
  Layers,
  Sparkles,
  ChevronRight,
} from "lucide-react";

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
  const [activeDiagnosticId, setActiveDiagnosticId] = useState<string | null>(
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

  const activeDiagnostic =
    diagnostics.find((d) => d.case_id === activeDiagnosticId) ||
    filteredDiagnostics[0];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-zinc-200/90 rounded-2xl p-5 shadow-2xs">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 03
            </span>
            <h2 className="text-lg font-bold tracking-tight text-zinc-950">
              UNDERSTAND: 12-Category Failure Diagnostics Taxonomy
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl">
            Isolate underlying root causes from intermediate observable symptoms to prescribe targeted autonomous mutations.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToImprove}
          className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-950 px-4 py-2 text-xs font-semibold text-white shadow-2xs transition-all hover:bg-zinc-800 active:scale-[0.98] cursor-pointer"
        >
          <span>Synthesize Mutations (Stage 04)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* 12-Category Taxonomy Interactive Pills Matrix */}
      <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-zinc-500" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950">
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
                ? "bg-zinc-950 text-white font-medium shadow-2xs"
                : "border border-zinc-200/80 bg-zinc-50/50 text-zinc-600 hover:border-zinc-300 hover:text-zinc-950"
            }`}
          >
            <span>All Categories</span>
            <span
              className={`rounded px-1.5 py-0.2 text-[10px] font-bold ${
                selectedCategory === "all"
                  ? "bg-white/20 text-white"
                  : "bg-zinc-200 text-zinc-700"
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
                    ? "bg-zinc-950 text-white font-medium shadow-2xs"
                    : count > 0
                    ? "border border-amber-300/80 bg-amber-50 text-amber-800 hover:border-amber-400"
                    : "border border-zinc-200/70 bg-zinc-50/50 text-zinc-400 hover:text-zinc-700"
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

      {/* Main Breakdown: Left list of cases, Right deep root-cause vs symptom breakdown */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Diagnostics List & Search */}
        <div className="space-y-3 lg:col-span-5">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search failures, symptoms, causes..."
              className="w-full rounded-xl border border-zinc-200 bg-white py-2 pl-9 pr-3 text-xs text-zinc-900 placeholder-zinc-400 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 transition-colors shadow-2xs font-mono"
            />
          </div>

          <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
            {filteredDiagnostics.length === 0 ? (
              <div className="rounded-xl border border-zinc-200 bg-zinc-50/60 p-6 text-center text-xs text-zinc-400 font-mono">
                No failures match the selected category filter.
              </div>
            ) : (
              filteredDiagnostics.map((diag) => {
                const isActive = activeDiagnostic?.case_id === diag.case_id;
                return (
                  <div
                    key={diag.case_id}
                    onClick={() => setActiveDiagnosticId(diag.case_id)}
                    className={`cursor-pointer rounded-xl border p-3.5 transition-all shadow-2xs ${
                      isActive
                        ? "border-zinc-950 bg-white shadow-xs ring-1 ring-zinc-950"
                        : "border-zinc-200/90 bg-white hover:border-zinc-300"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-zinc-950 truncate">
                        {diag.case_id}
                      </span>
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-mono font-bold text-amber-700 border border-amber-200">
                        {diag.category}
                      </span>
                    </div>

                    <h4 className="mt-1 text-xs font-semibold text-zinc-950 line-clamp-1">
                      {diag.case_name}
                    </h4>

                    <p className="mt-1.5 text-[11px] text-zinc-500 line-clamp-2 leading-relaxed">
                      {diag.root_cause}
                    </p>

                    <div className="mt-2.5 flex items-center justify-between border-t border-zinc-100 pt-2 text-[10px] font-mono text-zinc-400">
                      <span>Mutator: {diag.recommended_mutator}</span>
                      <span className="text-zinc-950 font-semibold">
                        {(diag.confidence * 100).toFixed(0)}% conf
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Deep Symptom vs Root Cause Card */}
        <div className="space-y-4 lg:col-span-7">
          {activeDiagnostic ? (
            <div className="rounded-2xl border border-zinc-200/90 bg-white p-6 shadow-2xs space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-100 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-zinc-400">
                      CASE ID:
                    </span>
                    <span className="font-mono text-sm font-bold text-zinc-950">
                      {activeDiagnostic.case_id}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-zinc-950 mt-0.5">
                    {activeDiagnostic.case_name}
                  </h3>
                </div>

                <div className="text-right">
                  <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-mono font-bold text-amber-800 border border-amber-200">
                    {activeDiagnostic.category}
                  </span>
                </div>
              </div>

              {/* Symptom vs Cause Comparison Panels */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Panel 1: Observable Symptoms */}
                <div className="rounded-xl border border-red-200/80 bg-red-50/30 p-4 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-red-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Observable Symptoms
                  </div>
                  <p className="text-[11px] text-zinc-500">
                    External test failure artifacts & visible discrepancies:
                  </p>
                  <ul className="space-y-1.5 pt-1 font-mono text-xs">
                    {activeDiagnostic.symptoms.map((sym, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2 text-zinc-900"
                      >
                        <span className="text-red-500 font-bold">•</span>
                        <span>{sym}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Panel 2: Isolated Root Cause */}
                <div className="rounded-xl border border-blue-200/80 bg-blue-50/30 p-4 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-blue-700">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Isolated Root Cause
                  </div>
                  <p className="text-[11px] text-zinc-500">
                    Underlying architectural defect or configuration gap:
                  </p>
                  <p className="text-xs text-zinc-900 pt-1 leading-relaxed font-mono">
                    {activeDiagnostic.root_cause}
                  </p>
                </div>
              </div>

              {/* Prescribed Targeted Remedy & Mutator */}
              <div className="rounded-xl border border-zinc-200/80 bg-zinc-50/60 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-950">
                    <Wrench className="h-3.5 w-3.5 text-zinc-500" />
                    Targeted Autonomous Remedy
                  </div>
                  <span className="font-mono text-xs font-semibold text-emerald-700">
                    Confidence: {(activeDiagnostic.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <p className="text-xs text-zinc-600 leading-relaxed">
                  {activeDiagnostic.remedy_suggestion}
                </p>

                <div className="flex flex-wrap items-center gap-3 border-t border-zinc-200/70 pt-3 text-xs font-mono">
                  <div>
                    <span className="text-zinc-400">Target Node: </span>
                    <span className="text-zinc-950 font-semibold">
                      {activeDiagnostic.target_node_id || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-400">Recommended Mutator: </span>
                    <span className="rounded-md bg-white px-2 py-0.5 text-zinc-950 border border-zinc-200 font-semibold shadow-2xs">
                      {activeDiagnostic.recommended_mutator}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-2xl border border-zinc-200 bg-white p-6 text-sm text-zinc-400 font-mono">
              Select a failure case from the left list to view root-cause diagnostics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
