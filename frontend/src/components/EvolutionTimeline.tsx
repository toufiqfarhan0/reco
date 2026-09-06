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
    <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs">
      <div className="mb-4 flex items-center justify-between border-b border-[#e4e4e3] pb-3">
        <div className="flex items-center gap-2">
          <GitCommit className="h-4 w-4 text-[#0a0a0a]" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#0a0a0a]">
            Autonomous Evolutionary Lineage Timeline
          </h3>
        </div>
        <span className="text-[11px] font-mono text-[#8a8a88]">
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
                className={`relative flex flex-col justify-between rounded-lg border p-4 transition-all cursor-pointer shadow-xs ${
                  isSelected
                    ? "border-[#0a0a0a] bg-white ring-1 ring-[#0a0a0a] shadow-md"
                    : node.status === "promoted"
                    ? "border-emerald-300 bg-white hover:border-emerald-500"
                    : "border-[#e4e4e3] bg-white hover:border-[#d1d1cf]"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="rounded bg-[#0a0a0a] px-2 py-0.5 text-[10px] font-mono font-semibold text-white">
                      GEN 0{node.generation}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold uppercase ${
                        node.status === "promoted"
                          ? "text-emerald-700"
                          : node.status === "candidate"
                          ? "text-blue-700"
                          : "text-[#8a8a88]"
                      }`}
                    >
                      {node.status}
                    </span>
                  </div>

                  <h4 className="mt-2 text-sm font-semibold text-[#0a0a0a]">
                    {node.label}
                  </h4>
                  <span className="text-[11px] font-mono text-[#8a8a88]">
                    Version: {node.version}
                  </span>

                  <div className="mt-2 text-xs text-[#525250]">
                    <span className="text-[10px] uppercase tracking-wider text-[#8a8a88] block font-medium">
                      Mutation Operator:
                    </span>
                    <span className="font-mono text-[#0a0a0a]">
                      {node.mutation}
                    </span>
                  </div>

                  <p className="mt-2 text-[11px] text-[#525250] leading-relaxed">
                    {node.notes}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-[#e4e4e3] pt-3">
                  <span className="text-xs font-mono text-[#8a8a88]">
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
    </div>
  );
};
