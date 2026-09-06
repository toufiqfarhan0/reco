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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-[#f4f4f3] px-2 py-0.5 text-xs font-mono font-semibold text-[#525250] border border-[#e4e4e3]">
              STAGE 03
            </span>
            <h2 className="text-xl font-bold tracking-tight text-[#0a0a0a]">
              UNDERSTAND: 12-Category Failure Diagnostics Taxonomy
            </h2>
          </div>
          <p className="text-sm text-[#525250] mt-1">
            Isolate underlying root causes from intermediate observable symptoms to prescribe targeted autonomous mutations.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToImprove}
          className="flex items-center gap-2 rounded-lg bg-[#0a0a0a] px-4 py-2 text-sm font-semibold text-white shadow-xs transition hover:bg-[#1a1a1a] cursor-pointer"
        >
          Synthesize Mutations (Stage 04)
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* 12-Category Taxonomy Interactive Pills Matrix */}
      <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-[#525250]" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#0a0a0a]">
              Root-Cause Taxonomy Classification Matrix (12 Categories)
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[#8a8a88]">
            Active Failures: {diagnostics.length}
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setSelectedCategory("all")}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-mono transition cursor-pointer ${
              selectedCategory === "all"
                ? "bg-[#0a0a0a] text-white font-medium"
                : "border border-[#e4e4e3] bg-[#f9f9f8] text-[#525250] hover:border-[#d1d1cf] hover:text-[#0a0a0a]"
            }`}
          >
            <span>All Categories</span>
            <span className={`rounded px-1 py-0.2 text-[10px] ${selectedCategory === "all" ? "bg-white/20 text-white" : "bg-[#e4e4e3] text-[#525250]"}`}>
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
                className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-mono transition cursor-pointer ${
                  isSelected
                    ? "bg-[#0a0a0a] text-white font-medium"
                    : count > 0
                    ? "border border-amber-300 bg-amber-50 text-amber-800 hover:border-amber-400"
                    : "border border-[#e4e4e3] bg-[#f9f9f8] text-[#8a8a88] hover:text-[#0a0a0a]"
                }`}
                title={cat.description}
              >
                <span>{cat.name}</span>
                {count > 0 && (
                  <span className={`rounded px-1 text-[10px] font-bold ${isSelected ? "bg-white/20 text-white" : "bg-amber-100 text-amber-800"}`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Breakdown: Left list of cases, Right deep root-cause vs symptom breakdown */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Diagnostics List & Search */}
        <div className="space-y-3 lg:col-span-5">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#8a8a88]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search failures, symptoms, causes..."
              className="w-full rounded-lg border border-[#e4e4e3] bg-white py-2 pl-9 pr-3 text-xs text-[#0a0a0a] placeholder-[#8a8a88] focus:border-[#0a0a0a] focus:outline-none"
            />
          </div>

          <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
            {filteredDiagnostics.length === 0 ? (
              <div className="rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-6 text-center text-xs text-[#8a8a88]">
                No failures match the selected category filter.
              </div>
            ) : (
              filteredDiagnostics.map((diag) => {
                const isActive = activeDiagnostic?.case_id === diag.case_id;
                return (
                  <div
                    key={diag.case_id}
                    onClick={() => setActiveDiagnosticId(diag.case_id)}
                    className={`cursor-pointer rounded-lg border p-3.5 transition-all ${
                      isActive
                        ? "border-[#0a0a0a] bg-white shadow-md ring-1 ring-[#0a0a0a]"
                        : "border-[#e4e4e3] bg-white hover:border-[#d1d1cf] shadow-xs"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-[#0a0a0a] truncate">
                        {diag.case_id}
                      </span>
                      <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-mono text-amber-700 border border-amber-200">
                        {diag.category}
                      </span>
                    </div>

                    <h4 className="mt-1 text-xs font-medium text-[#0a0a0a] line-clamp-1">
                      {diag.case_name}
                    </h4>

                    <p className="mt-1.5 text-[11px] text-[#525250] line-clamp-2">
                      {diag.root_cause}
                    </p>

                    <div className="mt-2.5 flex items-center justify-between border-t border-[#e4e4e3] pt-2 text-[10px] font-mono text-[#8a8a88]">
                      <span>Mutator: {diag.recommended_mutator}</span>
                      <span className="text-[#0a0a0a] font-semibold">
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
            <div className="rounded-xl border border-[#e4e4e3] bg-white p-6 shadow-xs space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e4e4e3] pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-[#8a8a88]">
                      CASE ID:
                    </span>
                    <span className="font-mono text-sm font-bold text-[#0a0a0a]">
                      {activeDiagnostic.case_id}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-[#0a0a0a] mt-0.5">
                    {activeDiagnostic.case_name}
                  </h3>
                </div>

                <div className="text-right">
                  <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-mono font-bold text-amber-700 border border-amber-200">
                    {activeDiagnostic.category}
                  </span>
                </div>
              </div>

              {/* Symptom vs Cause Comparison Panels */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Panel 1: Observable Symptoms */}
                <div className="rounded-lg border border-red-200 bg-red-50/40 p-4 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-red-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Observable Symptoms
                  </div>
                  <p className="text-[11px] text-[#525250]">
                    External test failure artifacts & visible discrepancies:
                  </p>
                  <ul className="space-y-1.5 pt-1">
                    {activeDiagnostic.symptoms.map((sym, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2 text-xs text-[#0a0a0a]"
                      >
                        <span className="text-red-500 font-bold">•</span>
                        <span>{sym}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Panel 2: Isolated Root Cause */}
                <div className="rounded-lg border border-blue-200 bg-blue-50/40 p-4 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-blue-700">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Isolated Root Cause
                  </div>
                  <p className="text-[11px] text-[#525250]">
                    Underlying architectural defect or configuration gap:
                  </p>
                  <p className="text-xs text-[#0a0a0a] pt-1 leading-relaxed">
                    {activeDiagnostic.root_cause}
                  </p>
                </div>
              </div>

              {/* Prescribed Targeted Remedy & Mutator */}
              <div className="rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#0a0a0a]">
                    <Wrench className="h-4 w-4 text-[#525250]" />
                    Targeted Autonomous Remedy
                  </div>
                  <span className="font-mono text-xs font-semibold text-emerald-700">
                    Confidence: {(activeDiagnostic.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <p className="text-xs text-[#525250] leading-relaxed">
                  {activeDiagnostic.remedy_suggestion}
                </p>

                <div className="flex flex-wrap items-center gap-3 border-t border-[#e4e4e3] pt-3 text-xs font-mono">
                  <div>
                    <span className="text-[#8a8a88]">Target Node: </span>
                    <span className="text-[#0a0a0a] font-medium">
                      {activeDiagnostic.target_node_id || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#8a8a88]">Recommended Mutator: </span>
                    <span className="rounded bg-white px-2 py-0.5 text-[#0a0a0a] border border-[#e4e4e3] font-medium">
                      {activeDiagnostic.recommended_mutator}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-xl border border-[#e4e4e3] bg-white p-6 text-sm text-[#8a8a88]">
              Select a failure case from the left list to view root-cause diagnostics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
