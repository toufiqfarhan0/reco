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
          <span className="flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-mono font-medium text-indigo-700 border border-indigo-200">
            <span className="h-1.5 w-1.5 animate-ping rounded-full bg-indigo-500" />
            RUNNING
          </span>
        );
      case "completed":
        return (
          <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-mono font-medium text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            COMPLETED
          </span>
        );
      case "failed":
        return (
          <span className="flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-mono font-medium text-red-700 border border-red-200">
            <AlertCircle className="h-3 w-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="rounded-xl bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-500 border border-zinc-200">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold tracking-tight text-zinc-900">
                DAG Execution Progress & Topological Traversal
              </h3>
              <span className="rounded-xl bg-zinc-100 px-2 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200">
                {architecture.nodes.length} Steps
              </span>
            </div>
            <p className="text-xs text-zinc-500">
              Topological node progression: {architecture.name}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-zinc-50 px-3 py-1.5 font-mono text-xs text-zinc-900">
            <Clock className="h-3.5 w-3.5 text-zinc-400" />
            <span>{totalElapsedMs.toFixed(1)} ms</span>
          </div>

          <button
            type="button"
            onClick={handleStartRun}
            disabled={isRunning}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
          >
            <Play className="h-3.5 w-3.5" />
            <span>{isRunning ? "Executing..." : "Execute DAG"}</span>
          </button>

          <button
            type="button"
            onClick={handleResetRun}
            className="rounded-xl border border-zinc-200 bg-white px-2.5 py-1.5 text-xs text-zinc-600 transition hover:bg-zinc-50 hover:text-zinc-900 cursor-pointer shadow-xs"
            title="Reset DAG Execution"
            aria-label="Reset DAG Execution"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Topological Nodes Timeline */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {nodes.map((node, index) => {
          const isCurrent = activeNodeIndex === index && isRunning;
          return (
            <div
              key={node.id}
              className={`relative flex flex-col justify-between rounded-xl border p-3.5 transition-all ${
                isCurrent
                  ? "border-indigo-600 bg-white shadow-xs ring-1 ring-indigo-600"
                  : node.status === "completed"
                  ? "border-zinc-200 bg-white shadow-xs"
                  : "border-zinc-200/60 bg-zinc-50/50 opacity-75"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1">
                  <span className="font-mono text-[10px] text-zinc-400 font-semibold">
                    STEP 0{index + 1}
                  </span>
                  {getStatusBadge(node.status)}
                </div>

                <h4 className="mt-2 text-xs font-semibold text-zinc-950">
                  {node.name}
                </h4>

                <div className="mt-1.5 flex flex-wrap items-center gap-1">
                  <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono text-zinc-600 border border-zinc-200">
                    {node.type}
                  </span>
                  {node.tool_name && (
                    <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-mono text-zinc-900 font-medium border border-zinc-200">
                      {node.tool_name}
                    </span>
                  )}
                </div>

                {node.outputSummary && (
                  <p className="mt-2 text-[11px] text-zinc-500 line-clamp-2 leading-normal">
                    {node.outputSummary}
                  </p>
                )}
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-2 text-[10px] font-mono text-zinc-400">
                <span>Latency</span>
                <span className="text-zinc-950 font-semibold">
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
