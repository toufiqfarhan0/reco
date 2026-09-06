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
            <span className="rounded-md bg-purple-500/10 px-2 py-0.5 text-xs font-mono font-semibold text-purple-400 ring-1 ring-purple-500/30">
              STAGE 04
            </span>
            <h2 className="text-xl font-bold tracking-tight text-white">
              IMPROVE: Multi-Candidate Tournament & Prompt Diff Inspector
            </h2>
          </div>
          <p className="text-sm text-slate-400">
            Autonomous tournament evaluating mutated candidates (A, B, C) against the 4-axis empirical benchmark.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToValidate}
          className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white shadow-xs transition hover:bg-cyan-500 cursor-pointer"
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
              className={`relative flex flex-col justify-between rounded-xl border p-5 transition-all cursor-pointer ${
                isSelected
                  ? "border-cyan-500 bg-slate-900/90 shadow-lg shadow-cyan-950/40 ring-1 ring-cyan-500/50"
                  : isChampion
                  ? "border-emerald-500/40 bg-slate-900/60 hover:border-emerald-500/60"
                  : "border-slate-800 bg-slate-900/40 hover:border-slate-700"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-slate-800 font-mono text-xs font-bold text-cyan-300">
                      {cand.id}
                    </span>
                    <h3 className="text-sm font-semibold text-white">
                      {cand.name}
                    </h3>
                  </div>

                  {isChampion ? (
                    <span className="flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-400 ring-1 ring-emerald-500/40">
                      <Trophy className="h-3 w-3" />
                      CHAMPION
                    </span>
                  ) : cand.status === "pareto_dominant" ? (
                    <span className="rounded-full bg-cyan-500/15 px-2 py-0.5 text-[10px] font-mono font-bold text-cyan-400">
                      PARETO
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-500">
                      BASELINE
                    </span>
                  )}
                </div>

                <p className="mt-2 text-xs text-slate-400 line-clamp-2">
                  {cand.description}
                </p>

                {/* Scorecard Matrix Metrics */}
                <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">
                      Accuracy
                    </span>
                    <span className="text-sm font-bold text-emerald-400">
                      {(cand.scorecard.accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">
                      Reliability
                    </span>
                    <span className="text-sm font-bold text-slate-200">
                      {(cand.scorecard.reliability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">
                      Cost
                    </span>
                    <span className="text-xs text-slate-300">
                      ${cand.scorecard.cost_usd.toFixed(4)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">
                      Latency
                    </span>
                    <span className="text-xs text-slate-300">
                      {cand.scorecard.latency_ms.toFixed(1)} ms
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-[11px]">
                <span className="text-slate-400 font-mono">
                  Win Rate: <strong className="text-white">{cand.win_rate}%</strong>
                </span>
                <span className="text-cyan-400 hover:underline">
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
