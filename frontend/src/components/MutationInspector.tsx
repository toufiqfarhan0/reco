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
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200">
            <FileDiff className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-zinc-900">
              Prompt & Configuration Mutation Inspector
            </h3>
            <p className="text-xs text-zinc-500">
              {candidate.name} ({candidate.tag})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 rounded-xl border border-zinc-200 bg-zinc-100 p-0.5 text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab("prompt")}
            className={`rounded-lg px-3 py-1 font-medium transition cursor-pointer ${
              activeTab === "prompt"
                ? "bg-white text-zinc-900 shadow-xs border border-zinc-200/80 font-semibold"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            Prompt Diff
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("config")}
            className={`rounded-lg px-3 py-1 font-medium transition cursor-pointer ${
              activeTab === "config"
                ? "bg-white text-zinc-900 shadow-xs border border-zinc-200/80 font-semibold"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            Config Diff
          </button>
        </div>
      </div>

      {/* Mutator Metadata Card */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 rounded-xl border border-zinc-200/70 bg-zinc-50/50 p-3.5 text-xs">
        <div>
          <span className="text-[10px] uppercase font-mono text-zinc-400 block font-medium">
            Mutator Operator
          </span>
          <span className="font-mono font-semibold text-zinc-950">
            {candidate.mutator_applied}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-zinc-400 block font-medium">
            Targeted Node
          </span>
          <span className="font-mono font-semibold text-zinc-950">
            {candidate.targeted_node}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-zinc-400 block font-medium">
            Tournament Status
          </span>
          <span className="font-mono font-semibold text-emerald-700">
            {candidate.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Diff View */}
      {activeTab === "prompt" ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Baseline Prompt */}
          <div className="rounded-xl border border-red-200/80 bg-red-50/20 p-4 space-y-2">
            <div className="flex items-center justify-between border-b border-red-200/60 pb-2 text-xs font-mono text-zinc-700">
              <span className="font-semibold">Baseline Prompt (V0)</span>
              <span className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold text-red-700">
                ORIGINAL
              </span>
            </div>
            <pre className="text-xs text-red-800 whitespace-pre-wrap font-mono leading-relaxed bg-white/80 p-3 rounded-lg border border-red-200/60">
              {candidate.prompt_diff?.original || "No prompt diff available."}
            </pre>
          </div>

          {/* Mutated Prompt */}
          <div className="rounded-xl border border-emerald-200/80 bg-emerald-50/20 p-4 space-y-2">
            <div className="flex items-center justify-between border-b border-emerald-200/60 pb-2 text-xs font-mono text-zinc-950">
              <span className="font-semibold">Mutated Prompt ({candidate.name})</span>
              <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700">
                ACTIVE MUTATION
              </span>
            </div>
            <pre className="text-xs text-emerald-800 whitespace-pre-wrap font-mono leading-relaxed bg-white/80 p-3 rounded-lg border border-emerald-200/60">
              {candidate.prompt_diff?.mutated || "No prompt diff available."}
            </pre>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-zinc-200/80 bg-zinc-50/50 p-4 space-y-2">
          <div className="flex items-center justify-between border-b border-zinc-200 pb-2 text-xs font-mono text-zinc-700">
            <span className="font-semibold">Unified Architecture Configuration Diff</span>
            <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] text-zinc-800 font-medium">
              YAML / JSON
            </span>
          </div>
          <pre className="text-xs text-zinc-900 whitespace-pre-wrap font-mono leading-relaxed p-3.5 bg-white rounded-lg border border-zinc-200 shadow-2xs">
            {candidate.config_diff?.mutated || "No configuration diff recorded."}
          </pre>
        </div>
      )}
    </div>
  );
};
