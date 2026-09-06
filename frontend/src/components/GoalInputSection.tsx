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
            <span className="rounded-md bg-[#f4f4f3] px-2 py-0.5 text-xs font-mono font-semibold text-[#525250] border border-[#e4e4e3]">
              STAGE 01
            </span>
            <h2 id="stage1-heading" className="text-xl font-bold tracking-tight text-[#0a0a0a]">
              BUILD: Natural Language Goal & DAG Synthesis
            </h2>
          </div>
          <p className="text-sm text-[#525250] mt-1">
            Deconstruct natural language domain goals into formal typed TaskSpecifications and directed acyclic execution graphs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onSynthesize(goalText)}
            disabled={isSynthesizing}
            className="flex items-center gap-2 rounded-lg bg-[#0a0a0a] px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:bg-[#1a1a1a] active:scale-[0.98] disabled:opacity-50 cursor-pointer"
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
            className="flex items-center gap-2 rounded-lg border border-[#e4e4e3] bg-white px-4 py-2 text-sm font-semibold text-[#0a0a0a] transition-all hover:bg-[#f4f4f3] cursor-pointer shadow-xs"
          >
            Run Stage 02
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Natural language input & presets */}
        <div className="space-y-4 lg:col-span-7">
          <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs">
            <div className="mb-2 flex items-center justify-between">
              <label htmlFor="goal-input" className="text-xs font-semibold uppercase tracking-wider text-[#525250]">
                Natural Language Engineering Goal
              </label>
              <span className="text-[11px] font-mono text-[#8a8a88]">
                Domain: {preset.name}
              </span>
            </div>

            <textarea
              id="goal-input"
              rows={4}
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              placeholder="Describe the agent task, constraints, and validation criteria..."
              className="w-full rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-3 text-sm text-[#0a0a0a] placeholder-[#8a8a88] focus:border-[#0a0a0a] focus:bg-white focus:ring-1 focus:ring-[#0a0a0a] focus:outline-none transition-colors"
            />

            {/* Domain Preset Chips */}
            <div className="mt-3">
              <span className="text-[11px] font-semibold text-[#8a8a88] uppercase tracking-wider block mb-1.5">
                Domain Preset Chips (Click to Apply)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {preset.sampleChips.map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => handleChipClick(chip)}
                    className="rounded-md border border-[#e4e4e3] bg-white px-2.5 py-1 text-xs text-[#525250] transition hover:border-[#0a0a0a] hover:bg-[#0a0a0a] hover:text-white cursor-pointer shadow-xs"
                  >
                    + {chip}
                  </button>
                ))}
              </div>
            </div>

            {/* Constraints Row */}
            <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[#e4e4e3] pt-4">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-[#8a8a88]" />
                <div className="text-xs">
                  <label htmlFor="latency-budget" className="text-[#525250] block font-medium">
                    Latency Budget (ms)
                  </label>
                  <input
                    id="latency-budget"
                    type="number"
                    value={latencyBudget}
                    onChange={(e) => setLatencyBudget(e.target.value)}
                    className="w-24 rounded border border-[#e4e4e3] bg-white px-2 py-0.5 text-xs text-[#0a0a0a] focus:border-[#0a0a0a] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Coins className="h-4 w-4 text-[#8a8a88]" />
                <div className="text-xs">
                  <label htmlFor="cost-budget" className="text-[#525250] block font-medium">
                    Cost Budget ($USD)
                  </label>
                  <input
                    id="cost-budget"
                    type="number"
                    step="0.01"
                    value={costBudget}
                    onChange={(e) => setCostBudget(e.target.value)}
                    className="w-24 rounded border border-[#e4e4e3] bg-white px-2 py-0.5 text-xs text-[#0a0a0a] focus:border-[#0a0a0a] focus:outline-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Active Tool Registry Badges */}
          <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-[#525250]" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#525250]">
                  Active Tool Catalog & Capabilities
                </h3>
              </div>
              <span className="rounded-full bg-[#f4f4f3] px-2 py-0.5 text-[10px] font-mono text-[#525250] border border-[#e4e4e3]">
                {preset.availableTools.length} Registered Tools
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {preset.availableTools.map((tool) => (
                <div
                  key={tool.name}
                  className="flex flex-col justify-between rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-2.5 transition hover:border-[#d1d1cf]"
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-mono text-xs font-semibold text-[#0a0a0a]">
                      {tool.name}
                    </span>
                    <span className="rounded bg-[#f4f4f3] px-1.5 py-0.5 text-[10px] font-mono text-[#525250] border border-[#e4e4e3]">
                      {tool.capability}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-[#525250]">
                    {tool.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Synthesized DAG Architecture Preview */}
        <div className="space-y-4 lg:col-span-5">
          <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-[#0a0a0a]" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[#0a0a0a]">
                  Synthesized DAG Architecture
                </h3>
              </div>
              <span className="rounded bg-[#f4f4f3] px-2 py-0.5 text-[10px] font-mono text-[#525250] border border-[#e4e4e3]">
                {currentDag.id}
              </span>
            </div>

            {/* Architecture Node Flow */}
            <div className="space-y-2.5">
              {currentDag.nodes.map((node, idx) => {
                return (
                  <div
                    key={node.id}
                    className="relative flex items-center gap-3 rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-3 transition hover:border-[#d1d1cf]"
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-white border border-[#e4e4e3] text-xs font-mono font-bold text-[#0a0a0a]">
                      {idx + 1}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-xs font-semibold text-[#0a0a0a]">
                          {node.name}
                        </span>
                        <span className="rounded bg-[#f4f4f3] px-1.5 py-0.5 text-[10px] font-mono text-[#525250] border border-[#e4e4e3]">
                          {node.type}
                        </span>
                      </div>
                      {node.tool_name && (
                        <span className="mt-0.5 block text-[11px] font-mono text-[#525250]">
                          tool: {node.tool_name}
                        </span>
                      )}
                      {node.outputSummary && (
                        <span className="mt-0.5 block text-[10px] text-[#8a8a88] truncate">
                          {node.outputSummary}
                        </span>
                      )}
                    </div>

                    <div className="shrink-0 text-right">
                      <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-600 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Valid
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Graph Metrics */}
            <div className="mt-4 grid grid-cols-3 gap-2 border-t border-[#e4e4e3] pt-3 text-center">
              <div className="rounded-lg bg-[#f9f9f8] border border-[#e4e4e3] p-2">
                <span className="text-[10px] uppercase tracking-wider text-[#8a8a88] block font-medium">
                  Nodes
                </span>
                <span className="text-sm font-mono font-bold text-[#0a0a0a]">
                  {currentDag.nodes.length}
                </span>
              </div>
              <div className="rounded-lg bg-[#f9f9f8] border border-[#e4e4e3] p-2">
                <span className="text-[10px] uppercase tracking-wider text-[#8a8a88] block font-medium">
                  Edges
                </span>
                <span className="text-sm font-mono font-bold text-[#0a0a0a]">
                  {currentDag.edges.length}
                </span>
              </div>
              <div className="rounded-lg bg-[#f9f9f8] border border-[#e4e4e3] p-2">
                <span className="text-[10px] uppercase tracking-wider text-[#8a8a88] block font-medium">
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
