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
    <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e4e4e3] pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#f4f4f3] text-[#0a0a0a] border border-[#e4e4e3]">
            <FileDiff className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-[#0a0a0a]">
              Prompt & Configuration Mutation Inspector
            </h3>
            <p className="text-xs text-[#525250]">
              {candidate.name} ({candidate.tag})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-[#e4e4e3] bg-[#f4f4f3] p-0.5 text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab("prompt")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              activeTab === "prompt"
                ? "bg-white text-[#0a0a0a] shadow-xs"
                : "text-[#525250] hover:text-[#0a0a0a]"
            }`}
          >
            Prompt Diff
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("config")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              activeTab === "config"
                ? "bg-white text-[#0a0a0a] shadow-xs"
                : "text-[#525250] hover:text-[#0a0a0a]"
            }`}
          >
            Config Diff
          </button>
        </div>
      </div>

      {/* Mutator Metadata Card */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-3 text-xs">
        <div>
          <span className="text-[10px] uppercase font-mono text-[#8a8a88] block font-medium">
            Mutator Operator
          </span>
          <span className="font-mono font-semibold text-[#0a0a0a]">
            {candidate.mutator_applied}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-[#8a8a88] block font-medium">
            Targeted Node
          </span>
          <span className="font-mono font-semibold text-[#0a0a0a]">
            {candidate.targeted_node}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-mono text-[#8a8a88] block font-medium">
            Tournament Status
          </span>
          <span className="font-mono font-semibold text-emerald-700">
            {candidate.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Diff View */}
      {activeTab === "prompt" ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Baseline Prompt */}
          <div className="rounded-lg border border-[#e4e4e3] bg-white p-3.5 space-y-2">
            <div className="flex items-center justify-between border-b border-[#e4e4e3] pb-1.5 text-xs font-mono text-[#525250]">
              <span>Baseline Prompt (V0)</span>
              <span className="text-[10px] text-[#8a8a88]">ORIGINAL</span>
            </div>
            <pre className="text-xs text-red-700 whitespace-pre-wrap font-mono leading-relaxed bg-red-50/50 p-2.5 rounded border border-red-200">
              {candidate.prompt_diff?.original || "No prompt diff available."}
            </pre>
          </div>

          {/* Mutated Prompt */}
          <div className="rounded-lg border border-[#e4e4e3] bg-white p-3.5 space-y-2">
            <div className="flex items-center justify-between border-b border-[#e4e4e3] pb-1.5 text-xs font-mono text-[#0a0a0a]">
              <span>Mutated Prompt ({candidate.name})</span>
              <span className="text-[10px] font-bold text-emerald-700">
                ACTIVE MUTATION
              </span>
            </div>
            <pre className="text-xs text-emerald-700 whitespace-pre-wrap font-mono leading-relaxed bg-emerald-50/50 p-2.5 rounded border border-emerald-200">
              {candidate.prompt_diff?.mutated || "No prompt diff available."}
            </pre>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-[#e4e4e3] bg-white p-3.5 space-y-2">
          <div className="flex items-center justify-between border-b border-[#e4e4e3] pb-1.5 text-xs font-mono text-[#525250]">
            <span>Unified Architecture Configuration Diff</span>
            <span className="text-[10px] text-[#0a0a0a] font-medium">YAML / JSON</span>
          </div>
          <pre className="text-xs text-[#0a0a0a] whitespace-pre-wrap font-mono leading-relaxed p-3 bg-[#f9f9f8] rounded border border-[#e4e4e3]">
            {candidate.config_diff?.mutated || "No configuration diff recorded."}
          </pre>
        </div>
      )}
    </div>
  );
};
