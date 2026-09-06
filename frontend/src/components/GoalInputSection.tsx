"use client";

import React, { useState } from "react";
import { DomainType, DAGArchitecture } from "@/lib/types";
import { DOMAIN_PRESETS } from "@/lib/mockData";
import {
  Wand2,
  CheckCircle2,
  Layers,
  ArrowRight,
  Terminal,
  Cpu,
  RefreshCw,
  Clock,
  Coins,
} from "lucide-react";

interface GoalInputSectionProps {
  domain: DomainType;
  currentDag: DAGArchitecture;
  onSynthesize: (goalText: string) => void;
  onProceedToRun: () => void;
  isSynthesizing?: boolean;
  onOpenToolCatalog?: () => void;
}

export const GoalInputSection: React.FC<GoalInputSectionProps> = ({
  domain,
  currentDag,
  onSynthesize,
  onProceedToRun,
  isSynthesizing = false,
  onOpenToolCatalog,
}) => {
  const preset = DOMAIN_PRESETS[domain];
  const [goalText, setGoalText] = useState(preset.defaultGoal);
  const [latencyBudget, setLatencyBudget] = useState("5000");
  const [costBudget, setCostBudget] = useState("0.05");

  // Keep synced if domain changes
  React.useEffect(() => {
    setGoalText(DOMAIN_PRESETS[domain].defaultGoal);
  }, [domain]);

  const handleChipClick = (chip: string) => {
    setGoalText(
      `${preset.defaultGoal} Focus specifically on: ${chip}.`
    );
  };

  return (
    <section className="space-y-5" aria-labelledby="stage1-heading">
      {/* Stage Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-zinc-200/90 rounded-2xl p-5 shadow-2xs">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 01
            </span>
            <h2 id="stage1-heading" className="text-lg font-bold tracking-tight text-zinc-950">
              BUILD: Natural Language Goal & DAG Synthesis
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl">
            Deconstruct natural language domain goals into formal typed TaskSpecifications and directed acyclic execution graphs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onSynthesize(goalText)}
            disabled={isSynthesizing}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-all hover:bg-indigo-700 active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            {isSynthesizing ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Synthesizing DAG...</span>
              </>
            ) : (
              <>
                <Wand2 className="h-3.5 w-3.5" />
                <span>Synthesize DAG Architecture</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onProceedToRun}
            className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-800 transition-all hover:bg-zinc-50 hover:text-zinc-900 cursor-pointer shadow-xs"
          >
            <span>Run Stage 02</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Natural language input & presets */}
        <div className="space-y-5 lg:col-span-7">
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-zinc-600" />
                <label htmlFor="goal-input" className="text-xs font-semibold uppercase tracking-wider text-zinc-700">
                  Natural Language Engineering Goal
                </label>
              </div>
              <span className="rounded-xl bg-zinc-50 border border-zinc-200 px-2.5 py-0.5 text-[10px] font-mono text-zinc-600">
                Domain: {preset.name}
              </span>
            </div>

            <textarea
              id="goal-input"
              rows={4}
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              placeholder="Describe the agent task, constraints, and validation criteria..."
              className="w-full rounded-xl border border-zinc-200 bg-zinc-50/50 p-3.5 text-xs text-zinc-900 leading-relaxed placeholder-zinc-400 focus:border-indigo-600 focus:bg-white focus:ring-1 focus:ring-indigo-600 focus:outline-none transition-colors font-mono"
            />

            {/* Domain Preset Chips */}
            <div>
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2">
                Domain Preset Chips (Click to Apply)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {preset.sampleChips.map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => handleChipClick(chip)}
                    className="inline-flex items-center gap-1 rounded-xl border border-zinc-200 bg-white px-2.5 py-1 text-[11px] text-zinc-600 transition hover:border-indigo-300 hover:bg-indigo-50/60 hover:text-indigo-700 cursor-pointer shadow-xs font-mono"
                  >
                    + {chip}
                  </button>
                ))}
              </div>
            </div>

            {/* Constraints Row */}
            <div className="grid grid-cols-2 gap-3 border-t border-zinc-100 pt-4">
              <div className="flex items-center gap-2.5 rounded-xl border border-zinc-200 bg-zinc-50/50 p-2.5">
                <Clock className="h-4 w-4 text-zinc-500 shrink-0" />
                <div className="text-xs">
                  <label htmlFor="latency-budget" className="text-zinc-600 block text-[11px] font-medium">
                    Latency Budget (ms)
                  </label>
                  <input
                    id="latency-budget"
                    type="number"
                    value={latencyBudget}
                    onChange={(e) => setLatencyBudget(e.target.value)}
                    className="w-24 rounded-lg border border-zinc-200 bg-white px-2 py-0.5 text-xs font-mono text-zinc-900 focus:border-indigo-600 focus:outline-none mt-0.5"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2.5 rounded-xl border border-zinc-200 bg-zinc-50/50 p-2.5">
                <Coins className="h-4 w-4 text-zinc-500 shrink-0" />
                <div className="text-xs">
                  <label htmlFor="cost-budget" className="text-zinc-600 block text-[11px] font-medium">
                    Cost Budget ($USD)
                  </label>
                  <input
                    id="cost-budget"
                    type="number"
                    step="0.01"
                    value={costBudget}
                    onChange={(e) => setCostBudget(e.target.value)}
                    className="w-24 rounded-lg border border-zinc-200 bg-white px-2 py-0.5 text-xs font-mono text-zinc-900 focus:border-indigo-600 focus:outline-none mt-0.5"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Active Tool Registry Badges */}
          <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs">
            <div className="mb-3.5 flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-zinc-600" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-700">
                  Active Tool Catalog & Capabilities
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-xl bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200">
                  {preset.availableTools.length} Registered Tools
                </span>
                {onOpenToolCatalog && (
                  <button
                    type="button"
                    onClick={onOpenToolCatalog}
                    className="rounded-xl border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-[10px] font-mono font-medium text-indigo-700 hover:bg-indigo-100 transition-colors cursor-pointer shadow-xs"
                    data-testid="open-tool-catalog-button"
                  >
                    Inspect Registry →
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {preset.availableTools.map((tool) => (
                <div
                  key={tool.name}
                  className="flex flex-col justify-between rounded-xl border border-zinc-200/80 bg-zinc-50/40 p-3 transition hover:border-zinc-300 hover:bg-white"
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono text-xs font-semibold text-zinc-950">
                      {tool.name}
                    </span>
                    <span className="rounded bg-white px-1.5 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200">
                      {tool.capability}
                    </span>
                  </div>
                  <p className="mt-1.5 text-[11px] text-zinc-500 leading-normal">
                    {tool.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Synthesized DAG Architecture Preview */}
        <div className="space-y-5 lg:col-span-5">
          <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-zinc-950" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950">
                  Synthesized DAG Architecture
                </h3>
              </div>
              <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200">
                {currentDag.id}
              </span>
            </div>

            {/* Architecture Node Flow with Visual Connectors */}
            <div className="space-y-2">
              {currentDag.nodes.map((node, idx) => {
                return (
                  <div key={node.id} className="relative">
                    <div
                      className="relative flex items-center gap-3 rounded-xl border border-zinc-200/80 bg-zinc-50/40 p-3 transition hover:border-zinc-300 hover:bg-white hover:shadow-2xs"
                    >
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white border border-zinc-200 text-xs font-mono font-bold text-zinc-950 shadow-2xs">
                        0{idx + 1}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-xs font-semibold text-zinc-950">
                            {node.name}
                          </span>
                          <span className="rounded bg-white border border-zinc-200 px-1.5 py-0.5 text-[9px] font-mono text-zinc-600">
                            {node.type}
                          </span>
                        </div>
                        {node.tool_name && (
                          <span className="mt-0.5 block text-[10px] font-mono text-zinc-500">
                            tool: {node.tool_name}
                          </span>
                        )}
                        {node.outputSummary && (
                          <span className="mt-0.5 block text-[10px] text-zinc-400 truncate">
                            {node.outputSummary}
                          </span>
                        )}
                      </div>

                      <div className="shrink-0 text-right">
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3" />
                          Valid
                        </span>
                      </div>
                    </div>

                    {idx < currentDag.nodes.length - 1 && (
                      <div className="flex justify-center py-0.5" aria-hidden="true">
                        <span className="h-2 w-px bg-zinc-300" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Graph Metrics Strip */}
            <div className="grid grid-cols-3 gap-2 border-t border-zinc-100 pt-3 text-center">
              <div className="rounded-xl bg-zinc-50 border border-zinc-200/80 p-2.5">
                <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium">
                  Nodes
                </span>
                <span className="text-sm font-mono font-bold text-zinc-950">
                  {currentDag.nodes.length}
                </span>
              </div>
              <div className="rounded-xl bg-zinc-50 border border-zinc-200/80 p-2.5">
                <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium">
                  Edges
                </span>
                <span className="text-sm font-mono font-bold text-zinc-950">
                  {currentDag.edges.length}
                </span>
              </div>
              <div className="rounded-xl bg-zinc-50 border border-zinc-200/80 p-2.5">
                <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium">
                  Topological
                </span>
                <span className="text-sm font-mono font-bold text-emerald-600">
                  Acyclic
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
