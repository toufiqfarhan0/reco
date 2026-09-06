"use client";

import React, { useEffect, useState } from "react";
import { DAGArchitecture, DAGNode, NodeExecutionStatus } from "@/lib/types";
import {
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  Cpu,
  Layers,
} from "lucide-react";

interface RunProgressTrackerProps {
  architecture: DAGArchitecture;
  onExecutionComplete?: () => void;
  autoStart?: boolean;
}

export const RunProgressTracker: React.FC<RunProgressTrackerProps> = ({
  architecture,
  onExecutionComplete,
  autoStart = false,
}) => {
  const [nodes, setNodes] = useState<DAGNode[]>(architecture.nodes);
  const [activeNodeIndex, setActiveNodeIndex] = useState<number>(-1);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [totalElapsedMs, setTotalElapsedMs] = useState<number>(0);

  // Sync with architecture changes
  useEffect(() => {
    setNodes(architecture.nodes);
    setActiveNodeIndex(-1);
    setIsRunning(false);
    setTotalElapsedMs(0);
  }, [architecture]);

  const handleStartRun = () => {
    if (isRunning) return;
    setIsRunning(true);
    setActiveNodeIndex(0);
    setTotalElapsedMs(0);

    // Reset all nodes to pending
    setNodes((prev) =>
      prev.map((n) => ({
        ...n,
        status: "pending",
      }))
    );
  };

  const handleResetRun = () => {
    setIsRunning(false);
    setActiveNodeIndex(-1);
    setTotalElapsedMs(0);
    setNodes(architecture.nodes);
  };

  useEffect(() => {
    if (autoStart) {
      handleStartRun();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Execution progression effect
  useEffect(() => {
    if (!isRunning || activeNodeIndex < 0) return;

    if (activeNodeIndex >= nodes.length) {
      setIsRunning(false);
      if (onExecutionComplete) {
        onExecutionComplete();
      }
      return;
    }

    // Set current node running
    setNodes((prev) =>
      prev.map((n, i) =>
        i === activeNodeIndex
          ? { ...n, status: "running" }
          : i < activeNodeIndex
          ? { ...n, status: "completed" }
          : { ...n, status: "pending" }
      )
    );

    const stepLatency = nodes[activeNodeIndex].latency_ms || 25;
    const timer = setTimeout(() => {
      setTotalElapsedMs((prev) => prev + stepLatency);
      setNodes((prev) =>
        prev.map((n, i) =>
          i === activeNodeIndex ? { ...n, status: "completed" } : n
        )
      );
      setActiveNodeIndex((prev) => prev + 1);
    }, Math.max(stepLatency * 15, 250)); // Scaled for visible visualization

    return () => clearTimeout(timer);
  }, [isRunning, activeNodeIndex, nodes, onExecutionComplete]);

  const getStatusBadge = (status: NodeExecutionStatus) => {
    switch (status) {
      case "running":
        return (
          <span className="flex items-center gap-1 rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-mono font-medium text-cyan-300 ring-1 ring-cyan-500/40">
            <span className="h-1.5 w-1.5 animate-ping rounded-full bg-cyan-400" />
            RUNNING
          </span>
        );
      case "completed":
        return (
          <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-mono font-medium text-emerald-400 ring-1 ring-emerald-500/30">
            <CheckCircle2 className="h-3 w-3" />
            COMPLETED
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-[10px] font-mono font-medium text-rose-400 ring-1 ring-rose-500/30">
            <AlertCircle className="h-3 w-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-white">
              DAG Execution Progress & Topological Traversal
            </h3>
            <p className="text-xs text-slate-400">
              Topological node progression: {architecture.name}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-950 px-3 py-1 font-mono text-xs text-slate-300">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span>{totalElapsedMs.toFixed(1)} ms</span>
          </div>

          <button
            type="button"
            onClick={handleStartRun}
            disabled={isRunning}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-emerald-500 disabled:opacity-50 cursor-pointer"
          >
            <Play className="h-3.5 w-3.5" />
            {isRunning ? "Executing..." : "Execute DAG"}
          </button>

          <button
            type="button"
            onClick={handleResetRun}
            className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300 transition hover:bg-slate-700 hover:text-white cursor-pointer"
            title="Reset DAG Execution"
            aria-label="Reset DAG Execution"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Topological Nodes Timeline */}
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {nodes.map((node, index) => {
          const isCurrent = activeNodeIndex === index && isRunning;
          return (
            <div
              key={node.id}
              className={`relative flex flex-col justify-between rounded-lg border p-3.5 transition-all ${
                isCurrent
                  ? "border-cyan-500 bg-cyan-950/20 shadow-md shadow-cyan-950/40 ring-1 ring-cyan-500/50"
                  : node.status === "completed"
                  ? "border-slate-800 bg-slate-950/90"
                  : "border-slate-850 bg-slate-950/40 opacity-70"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1">
                  <span className="font-mono text-[10px] text-slate-500">
                    STEP 0{index + 1}
                  </span>
                  {getStatusBadge(node.status)}
                </div>

                <h4 className="mt-2 text-xs font-semibold text-slate-200">
                  {node.name}
                </h4>

                <div className="mt-1 flex flex-wrap items-center gap-1">
                  <span className="rounded bg-slate-800/90 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
                    {node.type}
                  </span>
                  {node.tool_name && (
                    <span className="rounded bg-cyan-950 px-1.5 py-0.5 text-[10px] font-mono text-cyan-300">
                      {node.tool_name}
                    </span>
                  )}
                </div>

                {node.outputSummary && (
                  <p className="mt-2 text-[11px] text-slate-400 line-clamp-2">
                    {node.outputSummary}
                  </p>
                )}
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[10px] font-mono text-slate-500">
                <span>Latency</span>
                <span className="text-slate-300">
                  {node.latency_ms ? `${node.latency_ms} ms` : "0.0 ms"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
