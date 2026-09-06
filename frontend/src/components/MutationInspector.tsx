"use client";

import React, { useState } from "react";
import { Candidate } from "@/lib/types";
import { Code, FileDiff, Sparkles, Wand2, Shield, Wrench } from "lucide-react";

interface MutationInspectorProps {
  candidate: Candidate;
}

export const MutationInspector: React.FC<MutationInspectorProps> = ({
  candidate,
}) => {
  const [activeTab, setActiveTab] = useState<"prompt" | "config">("prompt");

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-cyan-500/10 text-cyan-400">
            <FileDiff className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-white">
              Prompt & Configuration Mutation Inspector
            </h3>
            <p className="text-xs text-slate-400">
              {candidate.name} ({candidate.tag})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950 p-0.5 text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab("prompt")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              activeTab === "prompt"
                ? "bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Prompt Diff
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("config")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              activeTab === "config"
                ? "bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Config Diff
          </button>
        </div>
      </div>

      {/* Mutator Metadata Card */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 rounded-lg border border-slate-800/80 bg-slate-950 p-3 text-xs">
        <div>
          <span className="text-[10px] uppercase font-mono text-slate-500 block">
            Mutator Operator
          </span>
          <span className="font-mono font-semibold text-cyan-300">
            {candidate.mutator_applied}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-slate-500 block">
            Targeted Node
          </span>
          <span className="font-mono font-semibold text-slate-200">
            {candidate.targeted_node}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-slate-500 block">
            Tournament Status
          </span>
          <span className="font-mono font-semibold text-emerald-400">
            {candidate.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Diff View */}
      {activeTab === "prompt" ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Baseline Prompt */}
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3.5 space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5 text-xs font-mono text-slate-400">
              <span>Baseline Prompt (V0)</span>
              <span className="text-[10px] text-slate-500">ORIGINAL</span>
            </div>
            <pre className="text-xs text-rose-300/90 whitespace-pre-wrap font-mono leading-relaxed bg-rose-950/10 p-2.5 rounded border border-rose-900/30">
              {candidate.prompt_diff?.original || "No prompt diff available."}
            </pre>
          </div>

          {/* Mutated Prompt */}
          <div className="rounded-lg border border-cyan-900/40 bg-slate-950 p-3.5 space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5 text-xs font-mono text-cyan-400">
              <span>Mutated Prompt ({candidate.name})</span>
              <span className="text-[10px] font-bold text-emerald-400">
                ACTIVE MUTATION
              </span>
            </div>
            <pre className="text-xs text-emerald-300 whitespace-pre-wrap font-mono leading-relaxed bg-emerald-950/10 p-2.5 rounded border border-emerald-900/30">
              {candidate.prompt_diff?.mutated || "No prompt diff available."}
            </pre>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-3.5 space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-1.5 text-xs font-mono text-slate-400">
            <span>Unified Architecture Configuration Diff</span>
            <span className="text-[10px] text-cyan-400">YAML / JSON</span>
          </div>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed p-3 bg-slate-900/60 rounded border border-slate-800">
            {candidate.config_diff?.mutated || "No configuration diff recorded."}
          </pre>
        </div>
      )}
    </div>
  );
};
