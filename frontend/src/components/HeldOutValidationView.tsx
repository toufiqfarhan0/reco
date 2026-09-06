"use client";

import React, { useState } from "react";
import { HeldOutValidationData, NeatlogsTrace } from "@/lib/types";
import { HELD_OUT_VALIDATION_DATA, NEATLOGS_TRACE } from "@/lib/mockData";
import { NeatlogsTraceCard } from "./NeatlogsTraceCard";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Lock,
  Award,
  Layers,
  FileCheck,
  HelpCircle,
  RefreshCw,
} from "lucide-react";

interface HeldOutValidationViewProps {
  data?: HeldOutValidationData;
  trace?: NeatlogsTrace;
}

export const HeldOutValidationView: React.FC<HeldOutValidationViewProps> = ({
  data = HELD_OUT_VALIDATION_DATA,
  trace = NEATLOGS_TRACE,
}) => {
  const [decisionState, setDecisionState] = useState<
    "PROMOTED" | "REQUIRES_REVIEW" | "REJECTED"
  >(data.promotion_decision);

  const renderDecisionBanner = () => {
    switch (decisionState) {
      case "PROMOTED":
        return (
          <div className="rounded-xl border border-emerald-500/50 bg-emerald-950/20 p-6 shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500/40">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/50">
                  <ShieldCheck className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-emerald-400 uppercase tracking-widest">
                      FORMAL PROMOTION DECISION
                    </span>
                    <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-xs font-mono font-bold text-emerald-300 ring-1 ring-emerald-500/40">
                      PROMOTED TO PRODUCTION
                    </span>
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-white mt-1">
                    Candidate C Verified & Approved for Autonomous Deployment
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="rounded bg-slate-900 px-3 py-1.5 text-emerald-400 border border-emerald-800">
                  Held-Out: 100.0% (4/4 Passed)
                </span>
                <span className="rounded bg-slate-900 px-3 py-1.5 text-cyan-400 border border-slate-800">
                  Leakage: 0.00%
                </span>
              </div>
            </div>

            <div className="mt-4 border-t border-emerald-900/60 pt-4">
              <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider block mb-2">
                Automated Sign-Off Rationale:
              </span>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs text-slate-300">
                {data.rationale.map((r, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        );

      case "REQUIRES_REVIEW":
        return (
          <div className="rounded-xl border border-amber-500/50 bg-amber-950/20 p-6 shadow-lg ring-1 ring-amber-500/40">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/50">
                  <AlertTriangle className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-amber-400 uppercase tracking-widest">
                      PROMOTION DECISION
                    </span>
                    <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-mono font-bold text-amber-300 ring-1 ring-amber-500/40">
                      REQUIRES_REVIEW
                    </span>
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-white mt-1">
                    Multi-Axis Tradeoffs Flagged During Evaluation
                  </h3>
                </div>
              </div>
            </div>
          </div>
        );

      case "REJECTED":
        return (
          <div className="rounded-xl border border-rose-500/50 bg-rose-950/20 p-6 shadow-lg ring-1 ring-rose-500/40">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400 ring-1 ring-rose-500/50">
                  <XCircle className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-rose-400 uppercase tracking-widest">
                      PROMOTION DECISION
                    </span>
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-xs font-mono font-bold text-rose-300 ring-1 ring-rose-500/40">
                      REJECTED
                    </span>
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-white mt-1">
                    Candidate Failed Held-Out Generalization Criteria
                  </h3>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 text-xs font-mono font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
              STAGE 05
            </span>
            <h2 className="text-xl font-bold tracking-tight text-white">
              VALIDATE: Air-Gapped Held-Out Generalization & Promotion
            </h2>
          </div>
          <p className="text-sm text-slate-400">
            Blind verification on unpolluted test cases with air-gap checksum isolation.
          </p>
        </div>

        {/* Promotion State Switcher for Testing/Inspection */}
        <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-900 p-1 text-xs font-mono">
          <button
            type="button"
            onClick={() => setDecisionState("PROMOTED")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "PROMOTED"
                ? "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            PROMOTED
          </button>
          <button
            type="button"
            onClick={() => setDecisionState("REQUIRES_REVIEW")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "REQUIRES_REVIEW"
                ? "bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            REQUIRES_REVIEW
          </button>
          <button
            type="button"
            onClick={() => setDecisionState("REJECTED")}
            className={`rounded px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "REJECTED"
                ? "bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            REJECTED
          </button>
        </div>
      </div>

      {/* Decision Banner */}
      {renderDecisionBanner()}

      {/* Air-Gapped Security & Integrity Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-cyan-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Air-Gapped Partition Isolation & Zero-Leakage Audit
            </h3>
          </div>
          <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            ZERO LEAKAGE CONFIRMED
          </span>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs font-mono">
          <div className="rounded border border-slate-800 bg-slate-950 p-3">
            <span className="text-[10px] text-slate-500 uppercase block">
              Air-Gap Checksum
            </span>
            <span className="text-cyan-300 font-bold truncate block">
              {data.air_gap_checksum}
            </span>
          </div>

          <div className="rounded border border-slate-800 bg-slate-950 p-3">
            <span className="text-[10px] text-slate-500 uppercase block">
              Cross-Split Overlap
            </span>
            <span className="text-emerald-400 font-bold">
              0 / 4 cases (Strict Disjoint)
            </span>
          </div>

          <div className="rounded border border-slate-800 bg-slate-950 p-3">
            <span className="text-[10px] text-slate-500 uppercase block">
              Generalization Gap
            </span>
            <span className="text-emerald-400 font-bold">
              0.0% (Opt: 100% vs Held-Out: 100%)
            </span>
          </div>
        </div>
      </div>

      {/* Held-Out Case Results Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xs">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 mb-3">
          Air-Gapped Held-Out Test Cases ({data.cases.length} cases)
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 font-mono uppercase text-slate-500">
              <tr>
                <th className="py-2.5 px-3">Case ID</th>
                <th className="py-2.5 px-3">Phenomenon Tested</th>
                <th className="py-2.5 px-3">Outcome</th>
                <th className="py-2.5 px-3">Latency</th>
                <th className="py-2.5 px-3">Audit Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {data.cases.map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-3 font-semibold text-cyan-300">
                    {c.case_id}
                  </td>
                  <td className="py-2.5 px-3 text-slate-300 font-sans font-medium">
                    {c.phenomenon}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="inline-flex items-center gap-1 text-emerald-400 font-bold">
                      <CheckCircle2 className="h-3 w-3" /> PASSED
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">{c.latency_ms} ms</td>
                  <td className="py-2.5 px-3 text-slate-400 font-sans">
                    {c.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Neatlogs Production Trace Integration */}
      <NeatlogsTraceCard trace={trace} />
    </div>
  );
};
