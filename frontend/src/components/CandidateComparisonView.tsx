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
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-zinc-200/90 rounded-2xl p-5 shadow-2xs">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 04
            </span>
            <h2 className="text-lg font-bold tracking-tight text-zinc-950">
              IMPROVE: Multi-Candidate Tournament & Prompt Diff Inspector
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl">
            Autonomous tournament evaluating mutated candidates (A, B, C) against the 4-axis empirical benchmark.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToValidate}
          className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 active:scale-[0.98] cursor-pointer"
        >
          <span>Validate on Held-Out (Stage 05)</span>
          <ArrowRight className="h-3.5 w-3.5" />
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
              className={`relative flex flex-col justify-between rounded-2xl border p-5 transition-all cursor-pointer shadow-xs ${
                isSelected
                  ? "border-indigo-600 bg-white shadow-xs ring-1 ring-indigo-600"
                  : isChampion
                  ? "border-emerald-300 bg-white hover:border-emerald-400"
                  : "border-zinc-200 bg-white hover:border-zinc-300"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-zinc-900 font-mono text-xs font-bold text-white shadow-xs">
                      {cand.id}
                    </span>
                    <h3 className="text-sm font-semibold text-zinc-900">
                      {cand.name}
                    </h3>
                  </div>

                  {isChampion ? (
                    <span className="flex items-center gap-1 rounded-xl bg-emerald-50 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-700 border border-emerald-200">
                      <Trophy className="h-3 w-3" />
                      CHAMPION
                    </span>
                  ) : cand.status === "pareto_dominant" ? (
                    <span className="rounded-xl bg-indigo-50 px-2 py-0.5 text-[10px] font-mono font-bold text-indigo-700 border border-indigo-200">
                      PARETO
                    </span>
                  ) : (
                    <span className="rounded-xl bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-500 border border-zinc-200">
                      BASELINE
                    </span>
                  )}
                </div>

                <p className="mt-2 text-xs text-zinc-500 line-clamp-2 leading-relaxed">
                  {cand.description}
                </p>

                {/* Scorecard Matrix Metrics */}
                <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-zinc-200/70 bg-zinc-50/50 p-3 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase block font-medium">
                      Accuracy
                    </span>
                    <span className="text-sm font-bold text-emerald-700">
                      {(cand.scorecard.accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase block font-medium">
                      Reliability
                    </span>
                    <span className="text-sm font-bold text-zinc-950">
                      {(cand.scorecard.reliability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase block font-medium">
                      Cost
                    </span>
                    <span className="text-xs text-zinc-600">
                      ${cand.scorecard.cost_usd.toFixed(4)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase block font-medium">
                      Latency
                    </span>
                    <span className="text-xs text-zinc-600">
                      {cand.scorecard.latency_ms.toFixed(1)} ms
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-zinc-100 pt-3 text-[11px]">
                <span className="text-zinc-500 font-mono">
                  Win Rate: <strong className="text-zinc-950">{cand.win_rate}%</strong>
                </span>
                <span className="text-zinc-900 font-semibold hover:underline">
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
