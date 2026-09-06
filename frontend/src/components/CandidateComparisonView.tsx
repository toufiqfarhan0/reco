"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { Candidate, LineageNode } from "@/lib/types";
import { CANDIDATES_TOURNAMENT, EVOLUTION_LINEAGE } from "@/lib/mockData";
import { MutationInspector } from "./MutationInspector";
import { EvolutionTimeline } from "./EvolutionTimeline";
import {
  Trophy,
  ArrowRight,
  Sparkle,
  GitBranch,
  CheckCircle,
  Lightning,
} from "@phosphor-icons/react";

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
              STAGE 04
            </span>
            <h2 className="text-xl font-bold tracking-tight text-zinc-950 font-geist">
              IMPROVE: Multi-Candidate Tournament & Prompt Diff Inspector
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-geist">
            Autonomous tournament evaluating mutated candidates (A, B, C) against the 4-axis empirical benchmark.
          </p>
        </div>

        <button
          type="button"
          onClick={onProceedToValidate}
          className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all active:scale-[0.98] cursor-pointer font-geist"
        >
          <span>Validate on Held-Out (Stage 05)</span>
          <ArrowRight size={14} weight="bold" />
        </button>
      </div>

      {/* Slim Candidate Comparison Table (No side-by-side bulky cards) */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-100">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-900 font-mono">
            Candidate Architecture Tournament
          </h3>
          <span className="text-[10px] font-mono text-zinc-400">
            Pareto Frontier Analysis
          </span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-zinc-100">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50/50 border-b border-zinc-100 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
              <tr>
                <th className="py-2.5 px-3.5">Candidate</th>
                <th className="py-2.5 px-3.5">Status / Win Rate</th>
                <th className="py-2.5 px-3.5">Accuracy</th>
                <th className="py-2.5 px-3.5">Reliability</th>
                <th className="py-2.5 px-3.5">Cost</th>
                <th className="py-2.5 px-3.5">Latency</th>
                <th className="py-2.5 px-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 font-mono">
              {candidates.map((cand) => {
                const isSelected = selectedCandidateId === cand.id;
                const isWinner = cand.status === "verified_champion";
                return (
                  <tr
                    key={cand.id}
                    onClick={() => setSelectedCandidateId(cand.id as "A" | "B" | "C")}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-indigo-50/40 border-l-[3px] border-l-indigo-600"
                        : "hover:bg-zinc-50/50 border-l-[3px] border-l-transparent"
                    }`}
                  >
                    <td className="py-3 px-3.5">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`flex h-6 w-6 items-center justify-center rounded-md font-mono text-xs font-bold ${
                            isWinner ? "bg-indigo-600 text-white" : "bg-zinc-800 text-white"
                          }`}
                        >
                          {cand.id}
                        </span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-zinc-900 font-geist">
                              {cand.name}
                            </span>
                            {isWinner && (
                              <span className="flex items-center gap-1 rounded bg-emerald-50 px-1.5 py-0.2 text-[10px] font-mono font-bold text-emerald-700 border border-emerald-200">
                                <Trophy size={11} weight="fill" className="text-emerald-600" />
                                <span>CHAMPION</span>
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-zinc-500 font-geist max-w-sm truncate mt-0.5">
                            {cand.description}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3.5">
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                        <Sparkle size={11} weight="fill" />
                        {cand.win_rate}%
                      </span>
                    </td>
                    <td className="py-3 px-3.5 font-bold text-emerald-700">
                      {(cand.scorecard.accuracy * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-3.5 font-bold text-zinc-950">
                      {(cand.scorecard.reliability * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-3.5 text-zinc-600">
                      ${cand.scorecard.cost_usd.toFixed(4)}
                    </td>
                    <td className="py-3 px-3.5 text-zinc-600">
                      {cand.scorecard.latency_ms.toFixed(1)} ms
                    </td>
                    <td className="py-3 px-3.5 text-right font-geist">
                      <span className={`text-xs font-semibold ${isSelected ? "text-indigo-600" : "text-zinc-500"}`}>
                        Inspect Diff &rarr;
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mutation Diff Inspector for Selected Candidate */}
      <MutationInspector candidate={activeCandidate} />

      {/* Evolutionary Lineage Timeline */}
      <EvolutionTimeline lineage={lineage} />
    </motion.div>
  );
};
