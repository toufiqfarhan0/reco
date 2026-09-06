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
    <div className="rounded-xl border border-[#e4e4e3] bg-white p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e4e4e3] pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold tracking-tight text-[#0a0a0a]">
                Neatlogs Production Execution Trace
              </h3>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-mono font-semibold text-emerald-700 border border-emerald-200">
                VERIFIED TRACE
              </span>
            </div>
            <p className="text-xs font-mono text-[#525250]">
              Trace ID: <span className="text-[#0a0a0a] font-semibold">{trace.trace_id}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1 text-[#525250]">
            <Clock className="h-3.5 w-3.5 text-[#8a8a88]" />
            <span>{trace.total_duration_ms} ms</span>
          </div>
          <div className="flex items-center gap-1 text-[#525250]">
            <Coins className="h-3.5 w-3.5 text-emerald-600" />
            <span>${trace.total_cost_usd.toFixed(4)}</span>
          </div>
          <div className="flex items-center gap-1 text-[#525250]">
            <Cpu className="h-3.5 w-3.5 text-[#8a8a88]" />
            <span>{trace.total_tokens} tokens</span>
          </div>
        </div>
      </div>

      {/* Trace Span Waterfall */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[#8a8a88] block mb-2">
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
                    ? "border-[#0a0a0a] bg-[#f4f4f3] ring-1 ring-[#0a0a0a]"
                    : "border-[#e4e4e3] bg-[#f9f9f8] hover:border-[#d1d1cf]"
                }`}
              >
                <div className="flex items-center gap-2 z-10">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      span.status === "ok" ? "bg-emerald-500" : "bg-rose-500"
                    }`}
                  />
                  <span className="font-semibold text-[#0a0a0a]">
                    {span.name}
                  </span>
                  <span className="rounded bg-white border border-[#e4e4e3] px-1.5 py-0.2 text-[10px] text-[#525250]">
                    {span.kind}
                  </span>
                </div>

                <div className="flex items-center gap-3 z-10">
                  <span className="text-[#525250] text-[11px]">
                    {span.duration_ms.toFixed(1)} ms
                  </span>
                </div>

                {/* Waterfall Visual Bar */}
                <div
                  className="absolute inset-y-1 bg-emerald-100/60 rounded pointer-events-none"
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
        <div className="rounded-lg border border-[#e4e4e3] bg-[#f9f9f8] p-3.5 space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between border-b border-[#e4e4e3] pb-2">
            <span className="text-[#0a0a0a] font-bold">
              Span: {selectedSpan.span_id} ({selectedSpan.name})
            </span>
            <span className="text-emerald-700 font-medium">
              Offset: +{selectedSpan.start_offset_ms}ms | Duration: {selectedSpan.duration_ms}ms
            </span>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-[11px]">
            {Object.entries(selectedSpan.attributes).map(([k, v]) => (
              <div key={k} className="flex justify-between py-1 border-b border-[#e4e4e3]">
                <span className="text-[#8a8a88]">{k}:</span>
                <span className="text-[#0a0a0a] font-semibold">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
