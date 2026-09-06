"use client";

import React from "react";
import { LineageNode } from "@/lib/types";
import { GitCommit, Sparkles, CheckCircle2, ArrowRight } from "lucide-react";

interface EvolutionTimelineProps {
  lineage: LineageNode[];
  activeNodeId?: string;
  onSelectNode?: (nodeId: string) => void;
}

export const EvolutionTimeline: React.FC<EvolutionTimelineProps> = ({
  lineage,
  activeNodeId,
  onSelectNode,
}) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
      <div className="mb-4 flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <GitCommit className="h-4 w-4 text-cyan-400" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Autonomous Evolutionary Lineage Timeline
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-500">
          {lineage.length} Iterations Synthesized
        </span>
      </div>

      <div className="relative">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {lineage.map((node, index) => {
            const isSelected = activeNodeId === node.id;
            return (
              <div
                key={node.id}
                onClick={() => onSelectNode && onSelectNode(node.id)}
                className={`relative flex flex-col justify-between rounded-lg border p-4 transition-all cursor-pointer ${
                  isSelected
                    ? "border-cyan-500 bg-cyan-950/20 ring-1 ring-cyan-500/40"
                    : node.status === "promoted"
                    ? "border-emerald-500/40 bg-emerald-950/15 hover:border-emerald-500/60"
                    : "border-slate-800 bg-slate-950 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono font-semibold text-cyan-300">
                      GEN 0{node.generation}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold uppercase ${
                        node.status === "promoted"
                          ? "text-emerald-400"
                          : node.status === "candidate"
                          ? "text-cyan-400"
                          : "text-slate-500"
                      }`}
                    >
                      {node.status}
                    </span>
                  </div>

                  <h4 className="mt-2 text-sm font-semibold text-white">
                    {node.label}
                  </h4>
                  <span className="text-[11px] font-mono text-slate-500">
                    Version: {node.version}
                  </span>

                  <div className="mt-2 text-xs text-slate-400">
                    <span className="text-[10px] uppercase tracking-wider text-slate-500 block">
                      Mutation Operator:
                    </span>
                    <span className="font-mono text-slate-300">
                      {node.mutation}
                    </span>
                  </div>

                  <p className="mt-2 text-[11px] text-slate-400 leading-relaxed">
                    {node.notes}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3">
                  <span className="text-xs font-mono text-slate-400">
                    Accuracy:
                  </span>
                  <span
                    className={`font-mono text-base font-bold ${
                      node.accuracy >= 1.0
                        ? "text-emerald-400"
                        : node.accuracy > 0.5
                        ? "text-cyan-400"
                        : "text-rose-400"
                    }`}
                  >
                    {(node.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
