"use client";

import React, { useState } from "react";
import { NeatlogsTrace } from "@/lib/types";
import {
  Broadcast,
  Clock,
  Coins,
  Cpu,
  CheckCircle,
} from "@phosphor-icons/react";

interface NeatlogsTraceCardProps {
  trace: NeatlogsTrace;
}

const SPAN_KIND_THEMES: Record<
  string,
  {
    badge: string;
    bar: string;
    dot: string;
  }
> = {
  dag: {
    badge: "bg-indigo-50 text-indigo-700 border-indigo-200",
    bar: "bg-indigo-200/70 border border-indigo-400/80 shadow-2xs",
    dot: "bg-indigo-600",
  },
  node: {
    badge: "bg-blue-50 text-blue-700 border-blue-200",
    bar: "bg-blue-200/70 border border-blue-400/80 shadow-2xs",
    dot: "bg-blue-600",
  },
  tool: {
    badge: "bg-amber-50 text-amber-800 border-amber-200",
    bar: "bg-amber-200/70 border border-amber-400/80 shadow-2xs",
    dot: "bg-amber-500",
  },
  verifier: {
    badge: "bg-emerald-50 text-emerald-800 border-emerald-200",
    bar: "bg-emerald-200/70 border border-emerald-400/80 shadow-2xs",
    dot: "bg-emerald-600",
  },
  llm: {
    badge: "bg-purple-50 text-purple-800 border-purple-200",
    bar: "bg-purple-200/70 border border-purple-400/80 shadow-2xs",
    dot: "bg-purple-600",
  },
};

const getKindTheme = (kind: string) => {
  return (
    SPAN_KIND_THEMES[kind.toLowerCase()] || {
      badge: "bg-zinc-100 text-zinc-700 border-zinc-200",
      bar: "bg-zinc-200/70 border border-zinc-300 shadow-2xs",
      dot: "bg-zinc-500",
    }
  );
};

export const NeatlogsTraceCard: React.FC<NeatlogsTraceCardProps> = ({
  trace,
}) => {
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(
    trace.spans[0]?.span_id || null
  );

  const selectedSpan =
    trace.spans.find((s) => s.span_id === selectedSpanId) || trace.spans[0];

  return (
    <div className="space-y-4 pt-6 border-t border-zinc-100">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-zinc-100">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200">
            <Broadcast size={16} weight="duotone" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold tracking-tight text-zinc-900 font-geist">
                Neatlogs Production Execution Trace
              </h3>
              <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-mono font-semibold text-emerald-700 border border-emerald-200">
                VERIFIED TRACE
              </span>
            </div>
            <p className="text-xs font-mono text-zinc-500">
              Trace ID: <span className="text-zinc-900 font-semibold">{trace.trace_id}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-zinc-600 bg-zinc-50 border border-zinc-200 px-2.5 py-1 rounded-lg">
            <Clock size={13} className="text-zinc-400" />
            <span>{trace.total_duration_ms} ms</span>
          </div>
          <div className="flex items-center gap-1.5 text-zinc-600 bg-zinc-50 border border-zinc-200 px-2.5 py-1 rounded-lg">
            <Coins size={13} className="text-emerald-600" />
            <span>${trace.total_cost_usd.toFixed(4)}</span>
          </div>
          <div className="flex items-center gap-1.5 text-zinc-600 bg-zinc-50 border border-zinc-200 px-2.5 py-1 rounded-lg">
            <Cpu size={13} className="text-zinc-400" />
            <span>{trace.total_tokens} tokens</span>
          </div>
        </div>
      </div>

      {/* Trace Timeline with Colored Dots and Zinc Lines */}
      <div className="space-y-3">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400 block mb-2">
          Span Waterfall & Execution Latency Breakdown
        </span>

        <div className="relative pl-6 space-y-3 border-l-2 border-zinc-200 ml-2">
          {trace.spans.map((span) => {
            const isSelected = selectedSpan?.span_id === span.span_id;
            const kindTheme = getKindTheme(span.kind);
            const widthPct = Math.max(
              (span.duration_ms / trace.total_duration_ms) * 100,
              8
            );
            const leftOffsetPct = (span.start_offset_ms / trace.total_duration_ms) * 100;

            return (
              <div key={span.span_id} className="relative">
                {/* Colored Dot on the Zinc Line */}
                <span
                  className={`absolute -left-[31px] top-3.5 h-3 w-3 rounded-full border-2 border-white transition-transform ${
                    isSelected ? `${kindTheme.dot} ring-2 ring-indigo-300 scale-125` : kindTheme.dot
                  }`}
                />

                <div
                  onClick={() => setSelectedSpanId(span.span_id)}
                  className={`relative flex items-center justify-between rounded-xl border p-3 transition-all cursor-pointer overflow-hidden ${
                    isSelected
                      ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600 shadow-xs"
                      : "border-zinc-200 bg-white hover:border-zinc-300"
                  }`}
                >
                  <div className="flex items-center gap-2.5 z-10 font-mono text-xs">
                    <span className="font-semibold text-zinc-900 font-geist">
                      {span.name}
                    </span>
                    <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-mono ${kindTheme.badge}`}>
                      {span.kind}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 z-10 font-mono">
                    <span className="text-zinc-500 text-xs">
                      {span.duration_ms.toFixed(1)} ms
                    </span>
                  </div>

                  {/* Waterfall Latency Bar with Kind Color */}
                  <div
                    className={`absolute inset-y-1.5 rounded-lg pointer-events-none transition-all ${kindTheme.bar}`}
                    style={{
                      left: `${leftOffsetPct}%`,
                      width: `${widthPct}%`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Span Detail Card */}
      {selectedSpan && (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50/70 p-4 space-y-3 font-mono text-xs shadow-2xs">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-200 pb-2.5">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-zinc-950 font-bold font-geist">
                Span: {selectedSpan.span_id}
              </span>
              <span className="text-zinc-500 font-sans text-xs">({selectedSpan.name})</span>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono">
              <span className="text-zinc-500">Offset: <strong className="text-zinc-800">+{selectedSpan.start_offset_ms}ms</strong></span>
              <span className="text-zinc-300">|</span>
              <span className="text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                Duration: {selectedSpan.duration_ms}ms
              </span>
            </div>
          </div>

          {/* Structured Telemetry Tiles */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 pt-1">
            {Object.entries(selectedSpan.attributes).map(([k, v]) => (
              <div
                key={k}
                className="rounded-lg border border-zinc-200 bg-white p-2.5 shadow-2xs font-mono transition-colors hover:border-zinc-300"
              >
                <div className="text-[10px] text-zinc-400 font-semibold uppercase tracking-wider truncate">
                  {k.replace(/_/g, " ")}
                </div>
                <div className="text-xs font-bold text-zinc-900 mt-1 truncate">
                  {String(v)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
