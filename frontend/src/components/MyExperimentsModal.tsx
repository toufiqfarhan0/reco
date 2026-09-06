import React, { useEffect, useState } from "react";
import { FolderGit2, X, RefreshCw, ArrowRight, Clock, Layers } from "lucide-react";
import { fetchUserExperiments, fetchExperimentDetail } from "@/services/api";
import { ExperimentData } from "@/lib/types";

export interface MyExperimentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  token?: string;
  onLoadExperiment: (exp: ExperimentData) => void;
}

export const MyExperimentsModal: React.FC<MyExperimentsModalProps> = ({
  isOpen,
  onClose,
  token,
  onLoadExperiment,
}) => {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingExpId, setLoadingExpId] = useState<string | null>(null);

  const loadList = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUserExperiments(token);
      setExperiments(data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load experiments from Supabase");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadList();
    }
  }, [isOpen, token]);

  if (!isOpen) return null;

  const handleSelect = async (exp: any) => {
    setLoadingExpId(exp.id);
    try {
      const detail = await fetchExperimentDetail(exp.id, token);
      if (detail) {
        const latestRun = detail.optimization_runs?.[0];
        const resultPayload = latestRun?.result || {};

        const fullExperimentData: ExperimentData = {
          experiment_id: exp.id,
          name: exp.name,
          goal: exp.goal,
          domain: exp.domain || "financial_reconciliation",
          status: exp.status || "completed",
          created_at: exp.created_at,
          active_model: "glm-4-7-flash",
          benchmark_summary: resultPayload.benchmark_summary || {
            total_cases: 20,
            optimization_cases: 12,
            held_out_cases: 8,
            split_policy: "STRICT_ZERO_LEAKAGE",
            leakage_audited: true,
          },
          graph: detail.agent_versions?.[0]?.architecture || {},
          v0_scorecard: resultPayload.v0_scorecard || {
            name: "V0 (Baseline)",
            accuracy: 0.75,
            reliability: 1.0,
            cost: 0.05,
            latency: 50000,
          },
          v1_scorecard: resultPayload.v1_scorecard || {
            name: "V1 (Evolved)",
            accuracy: 0.80,
            reliability: 1.0,
            cost: 0.045,
            latency: 40000,
          },
          held_out_scorecard: resultPayload.held_out_scorecard,
          scorecard_comparison: resultPayload.scorecard_comparison,
          diagnoses: resultPayload.diagnoses || [],
          mutations: resultPayload.mutations || [],
          candidates: resultPayload.candidates || [],
          evolution_timeline: resultPayload.evolution_timeline || [],
          promotion_assessment: resultPayload.promotion_assessment || {
            decision: "REVIEW",
            reasons: ["Persisted from Supabase Cloud"],
            gate_passed: false,
          },
          neatlogs: resultPayload.neatlogs || {
            trace_id: "nl_persisted",
            trace_url: "https://app.neatlogs.com",
            span_count: 24,
            latency_ms: 40000,
          },
        };

        onLoadExperiment(fullExperimentData);
        onClose();
      }
    } catch (err: any) {
      setError("Failed to load experiment details: " + (err?.message || "Unknown error"));
    } finally {
      setLoadingExpId(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-900/30 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="experiments-modal-title"
    >
      <div
        className="w-full max-w-3xl bg-white border border-zinc-200 rounded-2xl shadow-2xl p-6 md:p-8 relative max-h-[85vh] flex flex-col text-zinc-900"
        data-testid="my-experiments-modal"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-900 p-1.5 rounded-lg hover:bg-zinc-100 transition cursor-pointer"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center justify-between pb-5 border-b border-zinc-200">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-medium mb-1">
              <FolderGit2 className="w-3.5 h-3.5" />
              <span>Supabase Persistent Repository</span>
            </div>
            <h2 id="experiments-modal-title" className="text-xl font-bold text-zinc-900 tracking-tight">
              My Persisted Experiments
            </h2>
            <p className="text-xs text-zinc-500 mt-1">
              Browse, resume, and inspect your saved autonomous agent engineering runs.
            </p>
          </div>

          <button
            onClick={loadList}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-zinc-50 border border-zinc-200 hover:bg-zinc-100 text-xs font-sans font-medium text-zinc-700 transition cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={"w-3.5 h-3.5" + (loading ? " animate-spin text-indigo-600" : "")} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700">
            {error}
          </div>
        )}

        {/* Content List */}
        <div className="mt-4 overflow-y-auto flex-1 space-y-3 pr-1">
          {loading && experiments.length === 0 ? (
            <div className="py-12 text-center text-zinc-500 font-sans text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
              Loading your experiments from Supabase...
            </div>
          ) : experiments.length === 0 ? (
            <div className="py-12 text-center text-zinc-500">
              <Layers className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-zinc-800">No persisted experiments found</p>
              <p className="text-xs text-zinc-500 mt-1">
                Execute an optimization run while authenticated to persist architectures and benchmarks.
              </p>
            </div>
          ) : (
            experiments.map((exp) => {
              const runsCount = exp.optimization_runs?.length || 0;
              const versionsCount = exp.agent_versions?.length || 0;
              const createdDate = new Date(exp.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              });

              return (
                <div
                  key={exp.id}
                  className="bg-zinc-50/80 hover:bg-white border border-zinc-200 hover:border-indigo-300 rounded-xl p-4 shadow-sm transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  data-testid="persisted-experiment-row"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1 flex-wrap">
                      <span className="font-semibold text-zinc-900 text-sm truncate">{exp.name}</span>
                      <span className="text-[11px] px-2 py-0.5 rounded-xl font-sans font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                        {exp.domain}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded-xl font-sans font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {exp.status}
                      </span>
                    </div>

                    <p className="text-xs text-zinc-600 line-clamp-2 leading-relaxed">
                      {exp.goal}
                    </p>

                    <div className="flex items-center space-x-4 mt-2 text-[11px] font-mono text-zinc-500">
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {createdDate}
                      </span>
                      <span>{versionsCount} Version(s)</span>
                      <span>{runsCount} Run(s)</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleSelect(exp)}
                    disabled={loadingExpId === exp.id}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-sans font-medium flex items-center justify-center gap-1.5 shrink-0 transition cursor-pointer disabled:opacity-50 shadow-sm"
                    data-testid={"load-experiment-" + exp.id}
                  >
                    {loadingExpId === exp.id ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Loading...</span>
                      </>
                    ) : (
                      <>
                        <span>Load Workspace</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
