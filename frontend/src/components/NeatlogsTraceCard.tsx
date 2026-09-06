"use client";

import React, { useState } from "react";
import { NeatlogsTrace, NeatlogsSpan } from "@/lib/types";
import {
  Activity,
  CheckCircle2,
  Clock,
  Coins,
  Cpu,
  ExternalLink,
  Layers,
  Sparkles,
} from "lucide-react";

interface NeatlogsTraceCardProps {
  trace: NeatlogsTrace;
}

export const NeatlogsTraceCard: React.FC<NeatlogsTraceCardProps> = ({
  trace,
}) => {
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(
    trace.spans[0]?.span_id || null
  );

  const selectedSpan =
    trace.spans.find((s) => s.span_id === selectedSpanId) || trace.spans[0];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/30">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold tracking-tight text-white">
                Neatlogs Production Execution Trace
              </h3>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-mono font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
                VERIFIED TRACE
              </span>
            </div>
            <p className="text-xs font-mono text-slate-400">
              Trace ID: <span className="text-cyan-300">{trace.trace_id}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1 text-slate-300">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span>{trace.total_duration_ms} ms</span>
          </div>
          <div className="flex items-center gap-1 text-slate-300">
            <Coins className="h-3.5 w-3.5 text-emerald-400" />
            <span>${trace.total_cost_usd.toFixed(4)}</span>
          </div>
          <div className="flex items-center gap-1 text-slate-300">
            <Cpu className="h-3.5 w-3.5 text-purple-400" />
            <span>{trace.total_tokens} tokens</span>
          </div>
        </div>
      </div>

      {/* Trace Span Waterfall */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
          Span Waterfall & Execution Latency Breakdown
        </span>

        <div className="space-y-1.5 font-mono text-xs">
          {trace.spans.map((span) => {
            const isSelected = selectedSpan?.span_id === span.span_id;
            const widthPct = Math.max(
              (span.duration_ms / trace.total_duration_ms) * 100,
              6
            );
            const leftOffsetPct = (span.start_offset_ms / trace.total_duration_ms) * 100;

            return (
              <div
                key={span.span_id}
                onClick={() => setSelectedSpanId(span.span_id)}
                className={`relative flex items-center justify-between rounded-lg border p-2.5 transition-all cursor-pointer ${
                  isSelected
                    ? "border-cyan-500 bg-cyan-950/20 ring-1 ring-cyan-500/40"
                    : "border-slate-800/80 bg-slate-950/70 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center gap-2 z-10">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      span.status === "ok" ? "bg-emerald-400" : "bg-rose-400"
                    }`}
                  />
                  <span className="font-semibold text-slate-200">
                    {span.name}
                  </span>
                  <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-400">
                    {span.kind}
                  </span>
                </div>

                <div className="flex items-center gap-3 z-10">
                  <span className="text-slate-400 text-[11px]">
                    {span.duration_ms.toFixed(1)} ms
                  </span>
                </div>

                {/* Waterfall Visual Bar */}
                <div
                  className="absolute inset-y-1 bg-cyan-500/10 rounded pointer-events-none"
                  style={{
                    left: `${leftOffsetPct}%`,
                    width: `${widthPct}%`,
                  }}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Span Detail Card */}
      {selectedSpan && (
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-3.5 space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <span className="text-cyan-300 font-bold">
              Span: {selectedSpan.span_id} ({selectedSpan.name})
            </span>
            <span className="text-emerald-400">
              Offset: +{selectedSpan.start_offset_ms}ms | Duration: {selectedSpan.duration_ms}ms
            </span>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-[11px]">
            {Object.entries(selectedSpan.attributes).map(([k, v]) => (
              <div key={k} className="flex justify-between py-1 border-b border-slate-800/40">
                <span className="text-slate-500">{k}:</span>
                <span className="text-slate-300 font-semibold">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
