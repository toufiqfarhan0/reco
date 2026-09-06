"use client";

import React, { useState } from "react";
import { Candidate, LineageNode } from "@/lib/types";
import { CANDIDATES_TOURNAMENT, EVOLUTION_LINEAGE } from "@/lib/mockData";
import { MutationInspector } from "./MutationInspector";
import { EvolutionTimeline } from "./EvolutionTimeline";
import {
  Trophy,
  ArrowRight,
  TrendingUp,
  Award,
  CheckCircle2,
  Zap,
  Sparkles,
  Layers,
} from "lucide-react";

interface CandidateComparisonViewProps {
  candidates?: Candidate[];
  lineage?: LineageNode[];
  onProceedToValidate: () => void;
}

export const CandidateComparisonView: React.FC<CandidateComparisonViewProps> = ({
  candidates = CANDIDATES_TOURNAMENT,
  lineage = EVOLUTION_LINEAGE,
  onProceedToValidate,
}) => {
  const [selectedCandidateId, setSelectedCandidateId] = useState<"A" | "B" | "C">("C");

  const activeCandidate =
    candidates.find((c) => c.id === selectedCandidateId) || candidates[2];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-[#f4f4f3] px-2 py-0.5 text-xs font-mono font-semibold text-[#525250] border border-[#e4e4e3]">
              STAGE 04
            </span>
            <h2 className="text-xl font-bold tracking-tight text-[#0a0a0a]">
              IMPROVE: Multi-Candidate Tournament & Prompt Diff Inspector
            </h2>
          </div>
          <p className="text-sm text-[#525250] mt-1">
            Autonomous tournament evaluating mutated candidates (A, B, C) against the 4-axis empirical benchmark.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToValidate}
          className="flex items-center gap-2 rounded-lg bg-[#0a0a0a] px-4 py-2 text-sm font-semibold text-white shadow-xs transition hover:bg-[#1a1a1a] cursor-pointer"
        >
          Validate on Held-Out (Stage 05)
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Multi-Candidate Tournament Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {candidates.map((cand) => {
          const isSelected = selectedCandidateId === cand.id;
          const isChampion = cand.status === "verified_champion";
          return (
            <div
              key={cand.id}
              onClick={() => setSelectedCandidateId(cand.id)}
              className={`relative flex flex-col justify-between rounded-xl border p-5 transition-all cursor-pointer shadow-xs ${
                isSelected
                  ? "border-[#0a0a0a] bg-white shadow-md ring-1 ring-[#0a0a0a]"
                  : isChampion
                  ? "border-emerald-300 bg-white hover:border-emerald-500"
                  : "border-[#e4e4e3] bg-white hover:border-[#d1d1cf]"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#0a0a0a] font-mono text-xs font-bold text-white">
                      {cand.id}
                    </span>
                    <h3 className="text-sm font-semibold text-[#0a0a0a]">
                      {cand.name}
                    </h3>
                  </div>

                  {isChampion ? (
                    <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-700 border border-emerald-200">
                      <Trophy className="h-3 w-3" />
                      CHAMPION
                    </span>
                  ) : cand.status === "pareto_dominant" ? (
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-mono font-bold text-blue-700 border border-blue-200">
                      PARETO
                    </span>
                  ) : (
                    <span className="rounded-full bg-[#f4f4f3] px-2 py-0.5 text-[10px] font-mono text-[#525250] border border-[#e4e4e3]">
                      BASELINE
                    </span>
                  )}
                </div>

                <p className="mt-2 text-xs text-[#525250] line-clamp-2">
                  {cand.description}
                </p>

                {/* Scorecard Matrix Metrics */}
                <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-3 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-[#8a8a88] uppercase block font-medium">
                      Accuracy
                    </span>
                    <span className="text-sm font-bold text-emerald-700">
                      {(cand.scorecard.accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#8a8a88] uppercase block font-medium">
                      Reliability
                    </span>
                    <span className="text-sm font-bold text-[#0a0a0a]">
                      {(cand.scorecard.reliability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#8a8a88] uppercase block font-medium">
                      Cost
                    </span>
                    <span className="text-xs text-[#525250]">
                      ${cand.scorecard.cost_usd.toFixed(4)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#8a8a88] uppercase block font-medium">
                      Latency
                    </span>
                    <span className="text-xs text-[#525250]">
                      {cand.scorecard.latency_ms.toFixed(1)} ms
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-[#e4e4e3] pt-3 text-[11px]">
                <span className="text-[#525250] font-mono">
                  Win Rate: <strong className="text-[#0a0a0a]">{cand.win_rate}%</strong>
                </span>
                <span className="text-[#0a0a0a] font-medium hover:underline">
                  Inspect Diff →
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Mutation Diff Inspector for Selected Candidate */}
      <MutationInspector candidate={activeCandidate} />

      {/* Evolutionary Lineage Timeline */}
      <EvolutionTimeline lineage={lineage} />
    </div>
  );
};
