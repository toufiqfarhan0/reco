"use client";

import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { DomainType, DAGArchitecture } from "@/lib/types";
import { DOMAIN_PRESETS } from "@/lib/mockData";
import {
  Graph,
  CheckCircle,
  ArrowRight,
  Terminal,
  Cpu,
  CircleNotch,
  Clock,
  Coins,
  Wrench,
  Sparkle,
} from "@phosphor-icons/react";

interface GoalInputSectionProps {
  domain?: DomainType | "";
  currentDag: DAGArchitecture;
  onSynthesize: (goalText: string) => void;
  onProceedToRun: () => void;
  isSynthesizing?: boolean;
  hasSynthesized?: boolean;
  onOpenToolCatalog?: () => void;
}

export const GoalInputSection: React.FC<GoalInputSectionProps> = ({
  domain = "",
  currentDag,
  onSynthesize,
  onProceedToRun,
  isSynthesizing = false,
  hasSynthesized = false,
  onOpenToolCatalog,
}) => {
  const preset = domain && DOMAIN_PRESETS[domain] ? DOMAIN_PRESETS[domain] : undefined;
  const [goalText, setGoalText] = useState(preset ? preset.defaultGoal : "");
  const [latencyBudget, setLatencyBudget] = useState(preset ? "5000" : "");
  const [costBudget, setCostBudget] = useState(preset ? "0.05" : "");
  const [localSynthesized, setLocalSynthesized] = useState(false);

  // Keep synced if domain changes
  useEffect(() => {
    if (domain && DOMAIN_PRESETS[domain]) {
      setGoalText(DOMAIN_PRESETS[domain].defaultGoal);
      setLatencyBudget("5000");
      setCostBudget("0.05");
    }
  }, [domain]);

  const handleChipClick = (chip: string) => {
    setGoalText((prev) => {
      const base = preset?.defaultGoal || prev;
      return `${base} Focus specifically on: ${chip}.`;
    });
  };

  const isGoalEmpty = goalText.trim().length === 0;
  const isButtonDisabled = isGoalEmpty || isSynthesizing;

  const handleSynthesizeClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!isButtonDisabled) {
      setLocalSynthesized(true);
      onSynthesize(goalText);
    }
  };

  const handleProceedClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onProceedToRun();
  };

  const hasSelectedDomain = Boolean(preset);
  const hasGoalEntered = goalText.trim().length >= 20;
  const showToolCatalog = hasSelectedDomain || hasGoalEntered;
  const toolsToDisplay = hasSelectedDomain && preset
    ? preset.availableTools
    : DOMAIN_PRESETS["financial_reconciliation"].availableTools;

  const isArchitectureVisible = Boolean(hasSynthesized || localSynthesized);

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="space-y-8"
      aria-labelledby="stage1-heading"
    >
      {/* Plain Section Header (No card wrapper) */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-zinc-100">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 01
            </span>
            <h2 id="stage1-heading" className="text-xl font-bold tracking-tight text-zinc-950 font-geist">
              BUILD: Natural Language Goal & DAG Synthesis
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-geist">
            Deconstruct natural language domain goals into formal typed TaskSpecifications and directed acyclic execution graphs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleProceedClick}
            className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-800 transition-all hover:bg-zinc-50 hover:text-zinc-900 cursor-pointer shadow-xs active:scale-[0.98]"
          >
            <span>Run Stage 02</span>
            <ArrowRight size={14} weight="bold" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Column: Natural language input & presets (No outer card) */}
        <div className="space-y-6 lg:col-span-7">
          <div className="space-y-5">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-2.5">
              <div className="flex items-center gap-2">
                <Terminal size={16} weight="bold" className="text-indigo-600" />
                <label htmlFor="goal-input" className="text-xs font-semibold uppercase tracking-wider text-zinc-700 font-mono">
                  Natural Language Engineering Goal
                </label>
              </div>
              <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600">
                Domain: {preset ? preset.name : "Not selected"}
              </span>
            </div>

            {/* Borderless surface textarea with bottom border */}
            <textarea
              id="goal-input"
              rows={4}
              value={goalText}
              onChange={(e) => setGoalText(e.target.value)}
              placeholder={`Describe your agent's goal in plain English...\ne.g. 'Reconcile internal transactions against payment gateway exports'`}
              className="w-full bg-transparent border-0 border-b border-zinc-200 focus:border-indigo-600 text-zinc-800 py-3 text-xs leading-relaxed placeholder-zinc-400 placeholder:italic focus:ring-0 focus:outline-none transition-colors font-mono resize-y"
            />

            {/* Domain Preset Chips */}
            {preset && preset.sampleChips && preset.sampleChips.length > 0 && (
              <div>
                <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2 font-mono">
                  Domain Preset Chips (Click to Apply)
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {preset.sampleChips.map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => handleChipClick(chip)}
                      className="inline-flex items-center gap-1 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 px-2.5 py-1 text-[11px] transition-transform hover:scale-[1.03] active:scale-[0.98] cursor-pointer shadow-2xs font-mono"
                    >
                      + {chip}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Latency & Cost Budget: Inline labeled inputs with border-b underline style */}
            <div className="grid grid-cols-2 gap-6 pt-2">
              <div className="flex flex-col gap-1">
                <label htmlFor="latency-budget" className="text-zinc-500 text-[11px] font-medium font-geist flex items-center gap-1.5">
                  <Clock size={14} className="text-zinc-400" />
                  Latency Budget (ms)
                </label>
                <input
                  id="latency-budget"
                  type="number"
                  value={latencyBudget}
                  onChange={(e) => setLatencyBudget(e.target.value)}
                  placeholder="e.g. 5000"
                  className="w-full bg-transparent border-0 border-b border-zinc-200 focus:border-indigo-600 px-0 py-1 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:ring-0 focus:outline-none transition-colors"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="cost-budget" className="text-zinc-500 text-[11px] font-medium font-geist flex items-center gap-1.5">
                  <Coins size={14} className="text-zinc-400" />
                  Cost Budget ($USD)
                </label>
                <input
                  id="cost-budget"
                  type="number"
                  step="0.01"
                  value={costBudget}
                  onChange={(e) => setCostBudget(e.target.value)}
                  placeholder="e.g. 0.05"
                  className="w-full bg-transparent border-0 border-b border-zinc-200 focus:border-indigo-600 px-0 py-1 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:ring-0 focus:outline-none transition-colors"
                />
              </div>
            </div>

            {/* Large Full-Width Button */}
            <div className="pt-3">
              <button
                type="button"
                onClick={handleSynthesizeClick}
                disabled={isButtonDisabled}
                className={`w-full inline-flex items-center justify-center gap-2.5 rounded-xl py-3 px-4 text-sm font-semibold transition-all font-geist ${
                  isGoalEmpty
                    ? "bg-zinc-200 text-zinc-400 cursor-not-allowed"
                    : isSynthesizing
                    ? "bg-indigo-600 text-white opacity-80 cursor-not-allowed"
                    : "bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99] text-white shadow-xs cursor-pointer"
                }`}
              >
                {isSynthesizing ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center gap-2"
                  >
                    <CircleNotch size={18} className="animate-spin text-white" />
                    <span>Synthesizing DAG Architecture...</span>
                  </motion.div>
                ) : (
                  <>
                    <Graph size={18} weight="bold" />
                    <span>Synthesize DAG Architecture</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Synthesized DAG Architecture Preview (No outer card) */}
        <div className="space-y-5 lg:col-span-5">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-2.5">
              <div className="flex items-center gap-2">
                <Cpu size={16} weight="duotone" className="text-indigo-600" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 font-mono">
                  SYNTHESIZED DAG ARCHITECTURE
                </h3>
              </div>
              {isArchitectureVisible && (
                <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600">
                  {currentDag.id}
                </span>
              )}
            </div>

            {isArchitectureVisible ? (
              <>
                {/* Architecture Node Flow: minimal row cards (rounded-lg, border-zinc-100) */}
                <div className="space-y-2">
                  {currentDag.nodes.map((node, idx) => {
                    return (
                      <div key={node.id} className="relative">
                        <div className="relative flex items-center gap-3 rounded-lg border border-zinc-100 bg-white p-2.5 transition hover:border-zinc-300">
                          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-zinc-50 border border-zinc-200 text-xs font-mono font-bold text-zinc-950">
                            0{idx + 1}
                          </div>

                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="truncate text-xs font-semibold text-zinc-950 font-geist">
                                {node.name}
                              </span>
                              <span className="rounded bg-zinc-50 border border-zinc-200 px-1.5 py-0.5 text-[9px] font-mono text-zinc-600">
                                {node.type}
                              </span>
                            </div>
                            {node.tool_name && (
                              <span className="mt-0.5 block text-[10px] font-mono text-zinc-500">
                                tool: {node.tool_name}
                              </span>
                            )}
                            {node.outputSummary && (
                              <span className="mt-0.5 block text-[10px] text-zinc-400 truncate font-geist">
                                {node.outputSummary}
                              </span>
                            )}
                          </div>

                          <div className="shrink-0 text-right">
                            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                              <CheckCircle size={12} weight="fill" />
                              Valid
                            </span>
                          </div>
                        </div>

                        {idx < currentDag.nodes.length - 1 && (
                          <div className="flex justify-center py-0.5" aria-hidden="true">
                            <span className="h-2 w-px bg-zinc-200" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Graph Metrics Strip: 3 plain inline stat blocks separated by dividers */}
                <div className="grid grid-cols-3 divide-x divide-zinc-100 border-t border-zinc-100 pt-3 text-center">
                  <div className="px-2">
                    <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium font-mono">
                      Nodes
                    </span>
                    <span className="text-sm font-mono font-bold text-zinc-950">
                      {currentDag.nodes.length}
                    </span>
                  </div>
                  <div className="px-2">
                    <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium font-mono">
                      Edges
                    </span>
                    <span className="text-sm font-mono font-bold text-zinc-950">
                      {currentDag.edges.length}
                    </span>
                  </div>
                  <div className="px-2">
                    <span className="text-[10px] uppercase tracking-wider text-zinc-400 block font-medium font-mono">
                      Topological
                    </span>
                    <span className="text-sm font-mono font-bold text-emerald-600">
                      Acyclic
                    </span>
                  </div>
                </div>

                {/* Pipeline Advancement Banner */}
                {!isSynthesizing && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50/90 to-purple-50/70 p-4 shadow-sm"
                  >
                    <div className="flex flex-col gap-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 border border-emerald-300 px-2.5 py-0.5 text-xs font-mono font-semibold text-emerald-800">
                          <CheckCircle size={14} weight="fill" className="text-emerald-600 shrink-0" />
                          <span>Acyclic Architecture Validated</span>
                        </div>
                        <span className="text-[10px] font-mono font-medium text-indigo-700">
                          Topological Sort Confirmed
                        </span>
                      </div>

                      <p className="text-xs text-zinc-700 font-geist leading-relaxed">
                        Agent graph synthesized with 0 circular dependencies. Ready for deterministic benchmark execution and failure diagnostics.
                      </p>

                      <button
                        type="button"
                        onClick={handleProceedClick}
                        className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white px-4 py-2.5 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist"
                      >
                        <span>Proceed to Stage 02: Run Baseline Evaluation</span>
                        <ArrowRight size={14} weight="bold" />
                      </button>
                    </div>
                  </motion.div>
                )}
              </>

            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center text-zinc-400">
                <Graph size={36} weight="duotone" className="mb-3 text-zinc-300" />
                <p className="text-xs font-semibold text-zinc-600 font-geist">No architecture yet</p>
                <p className="text-[11px] text-zinc-400 mt-1 max-w-xs font-geist">
                  Click &apos;Synthesize DAG Architecture&apos; to generate your agent graph
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Tool Catalog section (No outer card, hairline divider rows) */}
      {showToolCatalog && (
        <div className="border-t border-zinc-100 pt-6 space-y-4">
          <div className="flex items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <Wrench size={16} weight="duotone" className="text-zinc-600" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 font-mono">
                Active Tool Catalog & Capabilities
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600">
                {toolsToDisplay.length} Registered Tools
              </span>
              {onOpenToolCatalog && (
                <button
                  type="button"
                  onClick={onOpenToolCatalog}
                  className="rounded-md border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-[10px] font-mono font-medium text-indigo-700 hover:bg-indigo-100 transition-colors cursor-pointer"
                  data-testid="open-tool-catalog-button"
                >
                  Inspect Registry &rarr;
                </button>
              )}
            </div>
          </div>

          {/* 2-Column CSS grid of BORDERLESS rows with hairline separators */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 divide-y md:divide-y-0 divide-zinc-50">
            {toolsToDisplay.map((tool) => (
              <div
                key={tool.name}
                className="py-3 border-b border-zinc-100 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-semibold text-zinc-950">
                    {tool.name}
                  </span>
                  <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono text-zinc-600">
                    {tool.capability}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-zinc-500 leading-normal font-geist">
                  {tool.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.section>
  );
};
