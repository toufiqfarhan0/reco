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
          <div className="rounded-2xl border border-emerald-300/80 bg-emerald-50/40 p-6 shadow-2xs space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 border border-emerald-200 shadow-2xs">
                  <ShieldCheck className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-emerald-800 uppercase tracking-widest">
                      FORMAL PROMOTION DECISION
                    </span>
                    <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-mono font-bold text-emerald-800 border border-emerald-300">
                      PROMOTED TO PRODUCTION
                    </span>
                  </div>
                  <h3 className="text-lg font-bold tracking-tight text-zinc-950 mt-1">
                    Candidate C Verified & Approved for Autonomous Deployment
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="rounded-lg bg-white px-3 py-1.5 text-emerald-800 border border-emerald-300 shadow-2xs font-semibold">
                  Held-Out: 100.0% (4/4 Passed)
                </span>
                <span className="rounded-lg bg-white px-3 py-1.5 text-zinc-950 border border-zinc-200 shadow-2xs font-semibold">
                  Leakage: 0.00%
                </span>
              </div>
            </div>

            <div className="border-t border-emerald-200/80 pt-4">
              <span className="text-[11px] font-semibold text-emerald-900 uppercase tracking-wider block mb-2 font-mono">
                Automated Sign-Off Rationale:
              </span>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs text-zinc-900">
                {data.rationale.map((r, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-700 shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        );

      case "REQUIRES_REVIEW":
        return (
          <div className="rounded-2xl border border-amber-300/80 bg-amber-50/40 p-6 shadow-2xs">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-100 text-amber-800 border border-amber-200 shadow-2xs">
                  <AlertTriangle className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-amber-800 uppercase tracking-widest">
                      PROMOTION DECISION
                    </span>
                    <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-mono font-bold text-amber-800 border border-amber-300">
                      REQUIRES_REVIEW
                    </span>
                  </div>
                  <h3 className="text-lg font-bold tracking-tight text-zinc-950 mt-1">
                    Multi-Axis Tradeoffs Flagged During Evaluation
                  </h3>
                </div>
              </div>
            </div>
          </div>
        );

      case "REJECTED":
        return (
          <div className="rounded-2xl border border-red-300/80 bg-red-50/40 p-6 shadow-2xs">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-100 text-red-800 border border-red-200 shadow-2xs">
                  <XCircle className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-red-800 uppercase tracking-widest">
                      PROMOTION DECISION
                    </span>
                    <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-mono font-bold text-red-800 border border-red-300">
                      REJECTED
                    </span>
                  </div>
                  <h3 className="text-lg font-bold tracking-tight text-zinc-950 mt-1">
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
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white border border-zinc-200 rounded-2xl p-5 shadow-xs">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-xl bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 05
            </span>
            <h2 className="text-lg font-bold tracking-tight text-zinc-900">
              VALIDATE: Air-Gapped Held-Out Generalization & Promotion
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl">
            Blind verification on unpolluted test cases with air-gap checksum isolation.
          </p>
        </div>

        {/* Promotion State Switcher for Testing/Inspection */}
        <div className="flex items-center gap-1 rounded-xl border border-zinc-200 bg-zinc-100 p-0.5 text-xs font-mono">
          <button
            type="button"
            onClick={() => setDecisionState("PROMOTED")}
            className={`rounded-lg px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "PROMOTED"
                ? "bg-white text-emerald-800 shadow-xs font-bold border border-zinc-200/80"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            PROMOTED
          </button>
          <button
            type="button"
            onClick={() => setDecisionState("REQUIRES_REVIEW")}
            className={`rounded-lg px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "REQUIRES_REVIEW"
                ? "bg-white text-amber-800 shadow-xs font-bold border border-zinc-200/80"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            REQUIRES_REVIEW
          </button>
          <button
            type="button"
            onClick={() => setDecisionState("REJECTED")}
            className={`rounded-lg px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "REJECTED"
                ? "bg-white text-red-800 shadow-xs font-bold border border-zinc-200/80"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            REJECTED
          </button>
        </div>
      </div>

      {/* Decision Banner */}
      {renderDecisionBanner()}

      {/* Air-Gapped Security & Integrity Card */}
      <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-zinc-900" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-900">
              Air-Gapped Partition Isolation & Zero-Leakage Audit
            </h3>
          </div>
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2.5 py-0.5 rounded-xl border border-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5" />
            ZERO LEAKAGE CONFIRMED
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs font-mono">
          <div className="rounded-xl border border-zinc-200/70 bg-zinc-50/50 p-3.5">
            <span className="text-[10px] text-zinc-400 uppercase block font-medium">
              Air-Gap Checksum
            </span>
            <span className="text-zinc-950 font-bold truncate block mt-1">
              {data.air_gap_checksum}
            </span>
          </div>

          <div className="rounded-xl border border-zinc-200/70 bg-zinc-50/50 p-3.5">
            <span className="text-[10px] text-zinc-400 uppercase block font-medium">
              Cross-Split Overlap
            </span>
            <span className="text-emerald-700 font-bold block mt-1">
              0 / 4 cases (Strict Disjoint)
            </span>
          </div>

          <div className="rounded-xl border border-zinc-200/70 bg-zinc-50/50 p-3.5">
            <span className="text-[10px] text-zinc-400 uppercase block font-medium">
              Generalization Gap
            </span>
            <span className="text-emerald-700 font-bold block mt-1">
              0.0% (Opt: 100% vs Held-Out: 100%)
            </span>
          </div>
        </div>
      </div>

      {/* Held-Out Case Results Table */}
      <div className="rounded-2xl border border-zinc-200/90 bg-white p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950">
            Air-Gapped Held-Out Test Cases ({data.cases.length} cases)
          </h3>
          <span className="text-[10px] font-mono text-zinc-400">
            Split: blind_validation
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-zinc-200/70">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50/70 border-b border-zinc-200/70 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
              <tr>
                <th className="py-2.5 px-3.5">Case ID</th>
                <th className="py-2.5 px-3.5">Phenomenon Tested</th>
                <th className="py-2.5 px-3.5">Outcome</th>
                <th className="py-2.5 px-3.5">Latency</th>
                <th className="py-2.5 px-3.5">Audit Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 font-mono">
              {data.cases.map((c) => (
                <tr key={c.case_id} className="hover:bg-zinc-50/50 transition-colors">
                  <td className="py-2.5 px-3.5 font-semibold text-zinc-950">
                    {c.case_id}
                  </td>
                  <td className="py-2.5 px-3.5 text-zinc-900 font-sans font-medium">
                    {c.phenomenon}
                  </td>
                  <td className="py-2.5 px-3.5">
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold">
                      <CheckCircle2 className="h-3 w-3" /> PASSED
                    </span>
                  </td>
                  <td className="py-2.5 px-3.5 text-zinc-600">{c.latency_ms} ms</td>
                  <td className="py-2.5 px-3.5 text-zinc-500 font-sans">
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
