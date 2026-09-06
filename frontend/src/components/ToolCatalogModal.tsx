"use client";

import React, { useState, useMemo } from "react";
import { X, Wrench, Search, Shield, CheckCircle2, ChevronDown, ChevronUp, CheckSquare, Square } from "lucide-react";
import { ToolSchema } from "@/lib/types";

interface ToolCatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
  tools: ToolSchema[];
  selectedTools: Set<string>;
  onToggleTool: (toolName: string) => void;
}

export const ToolCatalogModal: React.FC<ToolCatalogModalProps> = ({
  isOpen,
  onClose,
  tools,
  selectedTools,
  onToggleTool,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  const categories = useMemo(() => {
    const set = new Set<string>();
    tools.forEach((t) => {
      if (t.category) set.add(t.category);
    });
    return ["all", ...Array.from(set)];
  }, [tools]);

  const filteredTools = useMemo(() => {
    return tools.filter((tool) => {
      const matchesSearch =
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory =
        selectedCategory === "all" || tool.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [tools, searchQuery, selectedCategory]);

  const handleSelectAll = () => {
    tools.forEach((t) => {
      if (!selectedTools.has(t.name)) {
        onToggleTool(t.name);
      }
    });
  };

  const handleClearAll = () => {
    tools.forEach((t) => {
      if (selectedTools.has(t.name)) {
        onToggleTool(t.name);
      }
    });
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Tool Registry Catalog"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-900/30 backdrop-blur-sm animate-in fade-in duration-200"
    >
      <div className="bg-white border border-zinc-200 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden text-zinc-900">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 bg-zinc-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-white border border-zinc-200 text-indigo-600 shadow-xs">
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-zinc-900 tracking-tight">Central Tool Registry</h2>
              <p className="text-xs text-zinc-500">
                Authorized tools available for autonomous DAG synthesis.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close tool catalog"
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Bar */}
        <div className="px-6 py-3 border-b border-zinc-200 bg-zinc-50/50 flex flex-col sm:flex-row gap-3 items-center justify-between">
          {/* Search Input */}
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tools..."
              className="w-full bg-white border border-zinc-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-indigo-500 font-sans transition"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-xl text-[11px] font-sans transition cursor-pointer capitalize ${
                  selectedCategory === cat
                    ? "bg-indigo-600 text-white font-medium shadow-xs"
                    : "bg-zinc-100 text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/80 border border-zinc-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Bulk Toggles */}
          <div className="flex items-center space-x-2 text-xs font-sans">
            <button
              onClick={handleSelectAll}
              className="text-indigo-600 hover:text-indigo-700 font-medium transition text-[11px] cursor-pointer"
            >
              Select All
            </button>
            <span className="text-zinc-300">•</span>
            <button
              onClick={handleClearAll}
              className="text-zinc-500 hover:text-zinc-900 transition text-[11px] cursor-pointer"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Modal Content / Tool List */}
        <div className="p-6 overflow-y-auto space-y-3">
          {filteredTools.length === 0 ? (
            <div className="py-12 text-center text-zinc-500 text-xs font-sans">
              No tools match your query "{searchQuery}".
            </div>
          ) : (
            filteredTools.map((tool) => {
              const isSelected = selectedTools.has(tool.name);
              const isExpanded = expandedTool === tool.name;

              return (
                <div
                  key={tool.name}
                  className={`border rounded-xl transition-all ${
                    isSelected
                      ? "bg-indigo-50/20 border-indigo-200 shadow-xs"
                      : "bg-zinc-50/40 border-zinc-200 opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="p-4 flex items-start justify-between gap-4">
                    <div className="flex items-start space-x-3 flex-1">
                      <button
                        type="button"
                        role="checkbox"
                        aria-checked={isSelected}
                        onClick={() => onToggleTool(tool.name)}
                        className="mt-0.5 text-indigo-600 hover:text-indigo-700 cursor-pointer focus:outline-none"
                        aria-label={`Toggle tool ${tool.name}`}
                      >
                        {isSelected ? (
                          <CheckSquare className="w-4 h-4 text-indigo-600" />
                        ) : (
                          <Square className="w-4 h-4 text-zinc-400" />
                        )}
                      </button>

                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-zinc-900">
                            {tool.name}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-700 font-sans capitalize border border-zinc-200">
                            {tool.category || "utility"}
                          </span>

                          {/* Deterministic Badge */}
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-md font-sans ${
                              tool.deterministic
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : "bg-amber-50 text-amber-800 border border-amber-200"
                            }`}
                          >
                            {tool.deterministic ? "Deterministic ($0/0ms)" : "Model-Driven"}
                          </span>

                          {/* Risk Level Badge */}
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-700 border border-zinc-200 font-sans">
                            Risk: {tool.risk_level}
                          </span>

                          {/* Side Effect */}
                          {tool.side_effect && (
                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-700 border border-zinc-200 font-sans">
                              Side Effect
                            </span>
                          )}
                        </div>

                        <p className="text-xs text-zinc-600 mt-1.5 leading-relaxed font-sans">
                          {tool.description}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() => setExpandedTool(isExpanded ? null : tool.name)}
                      className="p-1 text-zinc-400 hover:text-zinc-900 transition-colors cursor-pointer"
                      aria-label="Inspect parameter schema"
                      title="Inspect parameter schema"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Expanded Parameter Schema Inspector */}
                  {isExpanded && tool.parameters_schema?.properties && (
                    <div className="px-4 pb-4 pt-2 border-t border-zinc-200 bg-zinc-50/60 text-xs">
                      <span className="font-sans text-zinc-700 text-xs block mb-2 font-semibold">
                        Parameters Schema:
                      </span>
                      <div className="space-y-1.5 font-sans">
                        {Object.entries(tool.parameters_schema.properties).map(([key, prop]) => (
                          <div key={key} className="flex items-start justify-between bg-white p-2.5 rounded-lg border border-zinc-200">
                            <div>
                              <span className="text-indigo-600 font-mono font-semibold text-xs">{key}</span>
                              <span className="text-zinc-400 ml-1.5 text-[11px] font-mono">({prop.type})</span>
                              {prop.description && (
                                <p className="text-xs text-zinc-500 font-sans mt-0.5">{prop.description}</p>
                              )}
                            </div>
                            {tool.parameters_schema.required?.includes(key) && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 font-sans font-medium">
                                required
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-zinc-200 bg-zinc-50 text-xs">
          <span className="text-zinc-500 font-sans">
            Selected:{" "}
            <strong className="text-zinc-900 font-mono">{selectedTools.size}</strong> of{" "}
            <strong className="text-zinc-900 font-mono">{tools.length}</strong> available
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors cursor-pointer shadow-sm font-sans"
          >
            Apply Tools
          </button>
        </div>
      </div>
    </div>
  );
};

