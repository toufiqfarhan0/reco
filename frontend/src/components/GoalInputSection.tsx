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
}

export const GoalInputSection: React.FC<GoalInputSectionProps> = ({
  domain,
  currentDag,
  onSynthesize,
  onProceedToRun,
  isSynthesizing = false,
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
    <section className="space-y-6" aria-labelledby="stage1-heading">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-cyan-500/10 px-2 py-0.5 text-xs font-mono font-semibold text-cyan-400 ring-1 ring-cyan-500/30">
              STAGE 01
            </span>
            <h2 id="stage1-heading" className="text-xl font-bold tracking-tight text-white">
              BUILD: Natural Language Goal & DAG Synthesis
            </h2>
          </div>
          <p className="text-sm text-slate-400">
            Deconstruct natural language domain goals into formal typed TaskSpecifications and directed acyclic execution graphs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onSynthesize(goalText)}
            disabled={isSynthesizing}
            className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-cyan-600/20 transition-all hover:bg-cyan-500 active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            {isSynthesizing ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Synthesizing DAG...
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4" />
                Synthesize DAG Architecture
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onProceedToRun}
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2 text-sm font-semibold text-slate-200 transition-all hover:bg-slate-700 hover:text-white cursor-pointer"
          >
            Run Stage 02
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Natural language input & presets */}
        <div className="space-y-4 lg:col-span-7">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
            <div className="mb-2 flex items-center justify-between">
              <label htmlFor="goal-input" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Natural Language Engineering Goal
              </label>
              <span className="text-[11px] font-mono text-slate-500">
                Domain: {preset.name}
              </span>
            </div>

            <textarea
              id="goal-input"
              rows={4}
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              placeholder="Describe the agent task, constraints, and validation criteria..."
              className="w-full rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm text-slate-200 placeholder-slate-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 focus:outline-none"
            />

            {/* Domain Preset Chips */}
            <div className="mt-3">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                Domain Preset Chips (Click to Apply)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {preset.sampleChips.map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => handleChipClick(chip)}
                    className="rounded-md border border-slate-800 bg-slate-950/80 px-2.5 py-1 text-xs text-slate-300 transition hover:border-cyan-500/50 hover:bg-cyan-950/30 hover:text-cyan-200 cursor-pointer"
                  >
                    + {chip}
                  </button>
                ))}
              </div>
            </div>

            {/* Constraints Row */}
            <div className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-800/80 pt-4">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-400" />
                <div className="text-xs">
                  <label htmlFor="latency-budget" className="text-slate-400 block font-medium">
                    Latency Budget (ms)
                  </label>
                  <input
                    id="latency-budget"
                    type="number"
                    value={latencyBudget}
                    onChange={(e) => setLatencyBudget(e.target.value)}
                    className="w-24 rounded border border-slate-800 bg-slate-950 px-2 py-0.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Coins className="h-4 w-4 text-slate-400" />
                <div className="text-xs">
                  <label htmlFor="cost-budget" className="text-slate-400 block font-medium">
                    Cost Budget ($USD)
                  </label>
                  <input
                    id="cost-budget"
                    type="number"
                    step="0.01"
                    value={costBudget}
                    onChange={(e) => setCostBudget(e.target.value)}
                    className="w-24 rounded border border-slate-800 bg-slate-950 px-2 py-0.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Active Tool Registry Badges */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-cyan-400" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Active Tool Catalog & Capabilities
                </h3>
              </div>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-300">
                {preset.availableTools.length} Registered Tools
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {preset.availableTools.map((tool) => (
                <div
                  key={tool.name}
                  className="flex flex-col justify-between rounded-lg border border-slate-800/80 bg-slate-950/70 p-2.5 transition hover:border-slate-700"
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono text-xs font-semibold text-cyan-300">
                      {tool.name}
                    </span>
                    <span className="rounded bg-cyan-950/60 px-1.5 py-0.5 text-[10px] font-mono text-cyan-400 ring-1 ring-cyan-500/20">
                      {tool.capability}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-slate-400">
                    {tool.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Synthesized DAG Architecture Preview */}
        <div className="space-y-4 lg:col-span-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-cyan-400" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Synthesized DAG Architecture
                </h3>
              </div>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400">
                {currentDag.id}
              </span>
            </div>

            {/* Architecture Node Flow */}
            <div className="space-y-2.5">
              {currentDag.nodes.map((node, idx) => {
                return (
                  <div
                    key={node.id}
                    className="relative flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 p-3 transition hover:border-slate-700"
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-slate-800 text-xs font-mono font-bold text-slate-300">
                      {idx + 1}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-xs font-semibold text-slate-200">
                          {node.name}
                        </span>
                        <span className="rounded bg-slate-800/80 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
                          {node.type}
                        </span>
                      </div>
                      {node.tool_name && (
                        <span className="mt-0.5 block text-[11px] font-mono text-cyan-400">
                          tool: {node.tool_name}
                        </span>
                      )}
                      {node.outputSummary && (
                        <span className="mt-0.5 block text-[10px] text-slate-500 truncate">
                          {node.outputSummary}
                        </span>
                      )}
                    </div>

                    <div className="shrink-0 text-right">
                      <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400">
                        <CheckCircle2 className="h-3 w-3" />
                        Valid
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Graph Metrics */}
            <div className="mt-4 grid grid-cols-3 gap-2 border-t border-slate-800/80 pt-3 text-center">
              <div className="rounded bg-slate-950 p-2">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 block">
                  Nodes
                </span>
                <span className="text-sm font-mono font-bold text-slate-200">
                  {currentDag.nodes.length}
                </span>
              </div>
              <div className="rounded bg-slate-950 p-2">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 block">
                  Edges
                </span>
                <span className="text-sm font-mono font-bold text-slate-200">
                  {currentDag.edges.length}
                </span>
              </div>
              <div className="rounded bg-slate-950 p-2">
                <span className="text-[10px] uppercase tracking-wider text-slate-500 block">
                  Topological
                </span>
                <span className="text-sm font-mono font-bold text-emerald-400">
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
