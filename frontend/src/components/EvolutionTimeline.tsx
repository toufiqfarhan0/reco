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
    <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs space-y-4">
      <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
        <div className="flex items-center gap-2">
          <GitCommit className="h-4 w-4 text-zinc-950" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950">
            Autonomous Evolutionary Lineage Timeline
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-400">
          {lineage.length} Iterations Synthesized
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {lineage.map((node) => {
          const isSelected = activeNodeId === node.id;
          return (
            <div
              key={node.id}
              onClick={() => onSelectNode && onSelectNode(node.id)}
              className={`relative flex flex-col justify-between rounded-xl border p-4 transition-all cursor-pointer shadow-2xs ${
                isSelected
                  ? "border-zinc-950 bg-white ring-1 ring-zinc-950 shadow-xs"
                  : node.status === "promoted"
                  ? "border-emerald-300/80 bg-white hover:border-emerald-400"
                  : "border-zinc-200/90 bg-white hover:border-zinc-300"
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="rounded-md bg-zinc-950 px-2 py-0.5 text-[10px] font-mono font-bold text-white shadow-2xs">
                    GEN 0{node.generation}
                  </span>
                  <span
                    className={`text-[10px] font-mono font-bold uppercase ${
                      node.status === "promoted"
                        ? "text-emerald-700"
                        : node.status === "candidate"
                        ? "text-blue-700"
                        : "text-zinc-400"
                    }`}
                  >
                    {node.status}
                  </span>
                </div>

                <h4 className="mt-2.5 text-sm font-semibold text-zinc-950">
                  {node.label}
                </h4>
                <span className="text-[11px] font-mono text-zinc-400">
                  Version: {node.version}
                </span>

                <div className="mt-2 text-xs text-zinc-600">
                  <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium">
                    Mutation Operator:
                  </span>
                  <span className="font-mono text-zinc-900 font-medium">
                    {node.mutation}
                  </span>
                </div>

                <p className="mt-2 text-[11px] text-zinc-500 leading-relaxed">
                  {node.notes}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-zinc-100 pt-3">
                <span className="text-xs font-mono text-zinc-400">
                  Accuracy:
                </span>
                <span
                  className={`font-mono text-base font-bold ${
                    node.accuracy >= 1.0
                      ? "text-emerald-700"
                      : node.accuracy > 0.5
                      ? "text-blue-700"
                      : "text-red-700"
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
  );
};
