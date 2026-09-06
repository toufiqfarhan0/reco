"use client";

import React, { useState } from "react";
import { motion } from "motion/react";
import { HeldOutValidationData, NeatlogsTrace } from "@/lib/types";
import { HELD_OUT_VALIDATION_DATA, NEATLOGS_TRACE } from "@/lib/mockData";
import { NeatlogsTraceCard } from "./NeatlogsTraceCard";
import {
  ShieldCheck,
  CheckCircle,
  WarningCircle,
  XCircle,
  Lock,
} from "@phosphor-icons/react";

interface HeldOutValidationViewProps {
  data?: HeldOutValidationData;
  trace?: NeatlogsTrace;
  isDemo?: boolean;
}

export const HeldOutValidationView: React.FC<HeldOutValidationViewProps> = ({
  data = HELD_OUT_VALIDATION_DATA,
  trace = NEATLOGS_TRACE,
  isDemo = false,
}) => {
  const [decisionState, setDecisionState] = useState<
    "PROMOTED" | "REQUIRES_REVIEW" | "REJECTED"
  >(data.promotion_decision);

  const renderDecisionBanner = () => {
    switch (decisionState) {
      case "PROMOTED":
        return (
            <motion.div
            key="promoted"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="rounded-lg border-l-4 border-emerald-600 bg-emerald-50/40 p-6 border border-zinc-200/80 space-y-4"
          >
            <div className="flex flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700 border border-emerald-200">
                <ShieldCheck size={28} weight="fill" className="text-emerald-600" />
              </div>

              <div>
                <div className="flex items-center justify-center gap-2">
                  <span className="font-mono text-xs font-bold text-emerald-800 uppercase tracking-widest">
                    FORMAL PROMOTION DECISION
                  </span>
                  <span className="rounded bg-emerald-200/80 px-2 py-0.5 text-xs font-mono font-bold text-emerald-900 border border-emerald-300">
                    PROMOTED TO PRODUCTION
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-950 mt-1 font-geist">
                  Candidate C Verified & Approved for Autonomous Deployment
                </h3>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-3 font-mono text-xs pt-1">
                <span className="rounded-lg bg-white px-3 py-1.5 text-emerald-800 border border-emerald-200 font-semibold shadow-2xs">
                  Held-Out: 100.0% (4/4 Passed)
                </span>
                <span className="rounded-lg bg-white px-3 py-1.5 text-zinc-900 border border-zinc-200 font-semibold shadow-2xs">
                  Leakage: 0.00%
                </span>
              </div>
            </div>

            <div className="border-t border-emerald-200/60 pt-4 max-w-2xl mx-auto text-left">
              <span className="text-[11px] font-semibold text-emerald-900 uppercase tracking-wider block mb-2 font-mono text-center">
                Automated Sign-Off Rationale:
              </span>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs text-zinc-800 font-geist">
                {data.rationale.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 bg-white/80 p-2.5 rounded-lg border border-emerald-100">
                    <CheckCircle size={16} weight="fill" className="text-emerald-600 shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        );

      case "REQUIRES_REVIEW":
        return (
          <motion.div
            key="review"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="rounded-lg border-l-4 border-amber-500 bg-amber-50/40 p-6 border border-zinc-200/80 space-y-3"
          >
            <div className="flex flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-100 text-amber-800 border border-amber-300">
                <WarningCircle size={28} weight="fill" className="text-amber-600" />
              </div>

              <div>
                <div className="flex items-center justify-center gap-2">
                  <span className="font-mono text-xs font-bold text-amber-800 uppercase tracking-widest">
                    PROMOTION DECISION
                  </span>
                  <span className="rounded bg-amber-200/80 px-2.5 py-0.5 text-xs font-mono font-bold text-amber-900 border border-amber-300">
                    REQUIRES_REVIEW
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-950 mt-1 font-geist">
                  Multi-Axis Tradeoffs Flagged During Evaluation
                </h3>
                <p className="text-xs text-amber-800 max-w-lg mx-auto mt-2 font-geist">
                  Candidate demonstrates improvements on accuracy but exhibits latency regressions exceeding budget thresholds. Manual engineering sign-off required.
                </p>
              </div>
            </div>
          </motion.div>
        );

      case "REJECTED":
        return (
          <motion.div
            key="rejected"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="rounded-lg border-l-4 border-red-500 bg-red-50/40 p-6 border border-zinc-200/80 space-y-3"
          >
            <div className="flex flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-red-100 text-red-800 border border-red-300">
                <XCircle size={28} weight="fill" className="text-red-600" />
              </div>

              <div>
                <div className="flex items-center justify-center gap-2">
                  <span className="font-mono text-xs font-bold text-red-800 uppercase tracking-widest">
                    PROMOTION DECISION
                  </span>
                  <span className="rounded bg-red-200/80 px-2.5 py-0.5 text-xs font-mono font-bold text-red-900 border border-red-300">
                    REJECTED
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-zinc-950 mt-1 font-geist">
                  Candidate Failed Held-Out Generalization Criteria
                </h3>
                <p className="text-xs text-red-800 max-w-lg mx-auto mt-2 font-geist">
                  Performance on unobserved test partitions dropped significantly below the required baseline threshold, indicating prompt overfitting.
                </p>
              </div>
            </div>
          </motion.div>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-zinc-100">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="rounded-md bg-zinc-100 px-2.5 py-0.5 text-[11px] font-mono font-bold text-zinc-700 border border-zinc-200">
              STAGE 05
            </span>
            <h2 className="text-lg font-bold tracking-tight text-zinc-900 font-geist">
              VALIDATE: Air-Gapped Held-Out Generalization &amp; Promotion
            </h2>
          </div>
          <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-geist">
            Blind verification on unpolluted test cases with air-gap checksum isolation.
          </p>
        </div>

        {/* Promotion State Switcher */}
        <div className="flex items-center gap-1 rounded-lg border border-zinc-200 bg-zinc-100 p-0.5 text-xs font-mono">
          <button
            type="button"
            onClick={() => setDecisionState("PROMOTED")}
            className={`rounded-md px-2.5 py-1 font-medium transition cursor-pointer ${
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
            className={`rounded-md px-2.5 py-1 font-medium transition cursor-pointer ${
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
            className={`rounded-md px-2.5 py-1 font-medium transition cursor-pointer ${
              decisionState === "REJECTED"
                ? "bg-white text-red-800 shadow-xs font-bold border border-zinc-200/80"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            REJECTED
          </button>
        </div>
      </div>

      {/* Decision Banner (Centered, Color-Schemed) */}
      {renderDecisionBanner()}

      {/* Air-Gapped Security & Integrity Card */}
      <div className="space-y-4 pt-2">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-zinc-100">
          <div className="flex items-center gap-2">
            <Lock size={16} weight="duotone" className="text-zinc-900" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-900 font-mono">
              Air-Gapped Partition Isolation &amp; Zero-Leakage Audit
            </h3>
          </div>
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
            <CheckCircle size={14} weight="fill" />
            ZERO LEAKAGE CONFIRMED
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs font-mono">
          <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3.5">
            <span className="text-[10px] text-zinc-400 uppercase block font-medium">
              Air-Gap Checksum
            </span>
            <span className="text-zinc-950 font-bold truncate block mt-1">
              {data.air_gap_checksum}
            </span>
          </div>

          <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3.5">
            <span className="text-[10px] text-zinc-400 uppercase block font-medium">
              Cross-Split Overlap
            </span>
            <span className="text-emerald-700 font-bold block mt-1">
              0 / 4 cases (Strict Disjoint)
            </span>
          </div>

          <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3.5">
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
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-950 font-mono">
            Air-Gapped Held-Out Test Cases ({data.cases.length} cases)
          </h3>
          <span className="text-[10px] font-mono text-zinc-400">
            Split: blind_validation
          </span>
        </div>

        <div className="overflow-x-auto border-b border-zinc-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-zinc-50 border-b border-zinc-200 font-mono uppercase text-[10px] text-zinc-500 tracking-wider">
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
                  <td className="py-2.5 px-3.5 text-zinc-900 font-geist font-medium">
                    {c.phenomenon}
                  </td>
                  <td className="py-2.5 px-3.5">
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold">
                      <CheckCircle size={14} weight="fill" /> PASSED
                    </span>
                  </td>
                  <td className="py-2.5 px-3.5 text-zinc-600">{c.latency_ms} ms</td>
                  <td className="py-2.5 px-3.5 text-zinc-500 font-geist">
                    {c.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Neatlogs Production Trace Integration */}
      <NeatlogsTraceCard trace={trace} isDemo={isDemo} />
    </motion.div>
  );
};
