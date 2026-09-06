"use client";

import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  DomainType,
  ExecutionMode,
  StageType,
  DAGArchitecture,
  Scorecard,
  ScorecardComparison,
  ToolSchema,
} from "@/lib/types";
import {
  INITIAL_DAG_V0,
  V0_BASELINE_SCORECARD,
  V2_CANDIDATE_C_SCORECARD,
  COMPARISON_V0_VS_CANDIDATE_B,
  COMPARISON_V0_VS_CANDIDATE_C,
  FAILURE_DIAGNOSTICS,
  CANDIDATES_TOURNAMENT,
  EVOLUTION_LINEAGE,
  HELD_OUT_VALIDATION_DATA,
  NEATLOGS_TRACE,
  DOMAIN_PRESETS,
} from "@/lib/mockData";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { EpistemicMemoryLedger } from "@/components/EpistemicMemoryLedger";
import { GoalInputSection } from "@/components/GoalInputSection";
import { ScorecardView } from "@/components/ScorecardView";
import { RunProgressTracker } from "@/components/RunProgressTracker";
import { FailureExplorer } from "@/components/FailureExplorer";
import { CandidateComparisonView } from "@/components/CandidateComparisonView";
import { HeldOutValidationView } from "@/components/HeldOutValidationView";
import { BillingModal } from "@/components/BillingModal";
import { AuthModal } from "@/components/AuthModal";
import { MyExperimentsModal } from "@/components/MyExperimentsModal";
import { ToolCatalogModal } from "@/components/ToolCatalogModal";
import { fetchTools } from "@/services/api";
import { getSession, signOut, onAuthStateChange } from "@/lib/supabaseClient";
import { Clock, Cpu } from "lucide-react";
import { ArrowSquareOut, Broadcast } from "@phosphor-icons/react";

export const ModeHarnessBanner: React.FC<{ mode: ExecutionMode }> = ({ mode }) => {
  if (mode === "demo") {
    return (
      <div className="flex items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-zinc-100/70 px-4 py-2 text-xs font-mono text-zinc-700">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1 rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] font-bold text-zinc-800 uppercase tracking-wide">
            DEMO
          </span>
          <span className="font-semibold text-zinc-900">
            DEMO BENCHMARK HARNESS
          </span>
          <span className="text-zinc-400">•</span>
          <span className="text-zinc-600">
            Static Canonical Artifacts (Offline Sandbox)
          </span>
        </div>
        <span className="text-[10px] text-zinc-400 hidden sm:inline font-medium">
          Deterministic
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-2 text-xs font-mono text-emerald-800">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="inline-flex items-center gap-1 rounded bg-emerald-200 px-1.5 py-0.5 text-[10px] font-bold text-emerald-900 uppercase tracking-wide">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse" />
          LIVE
        </span>
        <span className="font-semibold text-emerald-950">
          LIVE EXECUTION HARNESS
        </span>
        <span className="text-emerald-400">•</span>
        <span className="text-emerald-700">
          Real GLM-4.7-Flash (TensorMux) &amp; Supabase Cloud Persistence
        </span>
      </div>
      <span className="text-[10px] text-emerald-600 hidden sm:inline font-medium">
        Active Runtime
      </span>
    </div>
  );
};

export const StageAwaitingExecutionCard: React.FC<{
  icon?: "clock" | "cpu";
  title?: string;
  description?: string;
  onGoToBuild: () => void;
  onLoadDemo: () => void;
}> = ({
  icon = "cpu",
  title = "Diagnostic Analysis Awaiting Run",
  description = "Complete Stage 01 (BUILD) and Stage 02 (RUN) to inspect failure clusters, mutation tournaments, and held-out validation.",
  onGoToBuild,
  onLoadDemo,
}) => {
  return (
    <div className="rounded-2xl border border-dashed border-zinc-300 bg-white p-10 text-center shadow-xs space-y-4">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 border border-indigo-100">
        {icon === "clock" ? <Clock className="h-6 w-6" /> : <Cpu className="h-6 w-6" />}
      </div>
      <div className="space-y-1.5 max-w-md mx-auto">
        <h3 className="text-base font-semibold text-zinc-900 font-geist">
          {title}
        </h3>
        <p className="text-xs text-zinc-500 font-geist leading-relaxed">
          {description}
        </p>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
        <button
          type="button"
          onClick={onGoToBuild}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white px-4 py-2.5 text-xs font-semibold shadow-xs transition cursor-pointer font-geist"
        >
          <span>Go to Stage 01: BUILD →</span>
        </button>
        <button
          type="button"
          onClick={onLoadDemo}
          className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50 active:scale-[0.98] text-zinc-700 px-4 py-2.5 text-xs font-semibold shadow-2xs transition cursor-pointer font-geist"
        >
          <span>Load Financial Reconcile Demo</span>
        </button>
      </div>
    </div>
  );
};

const PARSE_STAGE_PARAM = (param: string | null): StageType | null => {
  if (!param) return null;
  const p = param.trim().toUpperCase();
  if (p === "1" || p === "BUILD") return "BUILD";
  if (p === "2" || p === "RUN") return "RUN";
  if (p === "3" || p === "UNDERSTAND") return "UNDERSTAND";
  if (p === "4" || p === "IMPROVE") return "IMPROVE";
  if (p === "5" || p === "VALIDATE") return "VALIDATE";
  return null;
};

export const ConsolePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Parse initial stage from query param ?stage=N
  const initialStage = PARSE_STAGE_PARAM(searchParams.get("stage")) || "BUILD";
  const [currentStage, setCurrentStage] = useState<StageType>(initialStage);

  // Sync stage if query param updates
  useEffect(() => {
    const parsed = PARSE_STAGE_PARAM(searchParams.get("stage"));
    if (parsed && parsed !== currentStage) {
      setCurrentStage(parsed);
    }
  }, [searchParams]);

  // One-time dismissible onboarding guide state
  const [isOnboarded, setIsOnboarded] = useState<boolean>(() => {
    try {
      return localStorage.getItem("reco_onboarded") === "true";
    } catch {
      return false;
    }
  });

  const handleDismissOnboarding = () => {
    setIsOnboarded(true);
    try {
      localStorage.setItem("reco_onboarded", "true");
    } catch {
      // ignore
    }
  };

  // Global console execution configuration
  const presetParam = searchParams.get("preset") || searchParams.get("domain");
  const initialDomain: DomainType | "" =
    presetParam === "financial_reconciliation" || presetParam === "reconciliation"
      ? "financial_reconciliation"
      : presetParam === "anomaly_detection"
      ? "anomaly_detection"
      : presetParam === "research_comparison"
      ? "research_comparison"
      : "";

  const [domain, setDomain] = useState<DomainType | "">(initialDomain);
  const [hasSynthesized, setHasSynthesized] = useState<boolean>(Boolean(initialDomain));
  const [hasExecutedRun, setHasExecutedRun] = useState<boolean>(false);

  const handleSelectStage = (stage: StageType) => {
    setCurrentStage(stage);
  };
  const [mode, setMode] = useState<ExecutionMode>("demo");
  const [tier, setTier] = useState<"free" | "pro">("free");
  const [dodoBanner, setDodoBanner] = useState<{
    type: "success" | "failed";
    message: string;
  } | null>(null);

  // Handle Dodo Payments checkout return parameters (?checkout=success&status=...)
  useEffect(() => {
    const checkout = searchParams.get("checkout");
    const status = searchParams.get("status");

    if (status === "failed") {
      setDodoBanner({
        type: "failed",
        message:
          "Test payment declined by sandbox. To test successful checkout, use card 4242 4242 4242 4242 with expiry 06/32 and country set to United States (or Indian test card 4576 2389 1277 1450).",
      });
      if (typeof window !== "undefined") {
        window.history.replaceState({}, "", window.location.pathname);
      }
    } else if (
      checkout === "success" &&
      (status === "active" || status === "succeeded" || !status || status !== "failed")
    ) {
      setTier("pro");
      setDodoBanner({
        type: "success",
        message: "🎉 Welcome to Reco Pro! Subscription activated via Dodo Payments.",
      });
      if (typeof window !== "undefined") {
        window.history.replaceState({}, "", window.location.pathname);
      }
    }
  }, [searchParams]);

  const [isCloudConnected] = useState<boolean>(true);
  const [isLiveRunning, setIsLiveRunning] = useState<boolean>(false);
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);

  // Supabase Auth and User persistence state
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isBillingModalOpen, setIsBillingModalOpen] = useState(false);
  const [isExperimentsModalOpen, setIsExperimentsModalOpen] = useState(false);
  const [isToolCatalogOpen, setIsToolCatalogOpen] = useState(false);
  const [tools, setTools] = useState<ToolSchema[]>([]);
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set());

  useEffect(() => {
    getSession().then(({ session, user }) => {
      if (user) {
        setUser(user);
        setToken(session?.access_token);
      }
    });

    const {
      data: { subscription },
    } = onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
      setToken(session?.access_token);
    });

    return () => {
      subscription?.unsubscribe?.();
    };
  }, []);

  useEffect(() => {
    fetchTools().then((fetched) => {
      if (fetched && fetched.length > 0) {
        setTools(fetched);
        setSelectedTools(new Set(fetched.map((t) => t.name)));
      }
    });
  }, []);

  const handleToggleTool = (toolName: string) => {
    setSelectedTools((prev) => {
      const next = new Set(prev);
      if (next.has(toolName)) {
        next.delete(toolName);
      } else {
        next.add(toolName);
      }
      return next;
    });
  };

  const handleSignOut = async () => {
    await signOut();
    setUser(null);
    setToken(undefined);
  };

  const [activeExperiment, setActiveExperiment] = useState<any>(null);

  const handleLoadExperiment = (expData: any) => {
    setActiveExperiment(expData);
    if (expData.domain) {
      handleDomainChange(expData.domain as DomainType);
    }
    if (expData.v0_scorecard) {
      setCurrentScorecard(expData.v1_scorecard || expData.v0_scorecard);
    }
    setHasSynthesized(true);
    setHasExecutedRun(true);
    setCurrentStage("RUN");
  };

  // Active architecture and scorecards
  const [currentDag, setCurrentDag] = useState<DAGArchitecture>(() => {
    if (initialDomain && DOMAIN_PRESETS[initialDomain]) {
      const preset = DOMAIN_PRESETS[initialDomain];
      return {
        ...INITIAL_DAG_V0,
        domain: initialDomain,
        name: `Agent_${preset.name.replace(/\s+/g, "_")}_V0`,
      };
    }
    return INITIAL_DAG_V0;
  });
  const [currentScorecard, setCurrentScorecard] = useState<Scorecard>(
    V0_BASELINE_SCORECARD
  );
  const [currentComparison, setCurrentComparison] = useState<
    ScorecardComparison | undefined
  >(COMPARISON_V0_VS_CANDIDATE_B);

  // Handle Domain Change (supports alias "reconciliation")
  const handleDomainChange = (newDomain: DomainType | "reconciliation" | "") => {
    const resolvedDomain: DomainType | "" =
      newDomain === "reconciliation" ? "financial_reconciliation" : newDomain;

    setDomain(resolvedDomain);
    if (resolvedDomain && DOMAIN_PRESETS[resolvedDomain]) {
      const preset = DOMAIN_PRESETS[resolvedDomain];
      setCurrentDag({
        ...INITIAL_DAG_V0,
        domain: resolvedDomain,
        name: `Agent_${preset.name.replace(/\s+/g, "_")}_V0`,
      });
      setHasSynthesized(true);
      // Keep hasExecutedRun = false so Stage 02 starts in clean pending state
    }
  };

  // Handle Architecture Synthesis Trigger
  const handleSynthesize = () => {
    setIsSynthesizing(true);
    setHasSynthesized(true);
    setTimeout(() => {
      setIsSynthesizing(false);
      setCurrentDag(INITIAL_DAG_V0);
    }, 600);
  };

  const handleProceedToRun = () => {
    setHasSynthesized(true);
    setCurrentStage("RUN");
    navigate("/console?stage=2");
  };

  const isPipelineReady = Boolean((hasSynthesized || domain) && hasExecutedRun);


  return (
    <div className="min-h-screen bg-zinc-50 flex font-sans selection:bg-indigo-600 selection:text-white">
      {/* Fixed Left Sidebar (~220px) */}
      <Sidebar
        currentStage={currentStage}
        onSelectStage={handleSelectStage}
        domain={domain}
        onChangeDomain={handleDomainChange}
        mode={mode}
        onToggleMode={setMode}
        isRunning={isLiveRunning}
        viewMode="console"
        onToggleViewMode={(vm) => {
          if (vm === "overview") {
            navigate("/");
          }
        }}
        tier={tier}
        onToggleTier={setTier}
        isCloudConnected={isCloudConnected}
        onOpenBilling={() => setIsBillingModalOpen(true)}
        onGoToLanding={() => navigate("/")}
        user={user}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onOpenExperiments={() => setIsExperimentsModalOpen(true)}
        onSignOut={handleSignOut}
      />

      {/* Main Layout Area offset by 220px Sidebar */}
      <div className="pl-[220px] flex-1 flex flex-col min-h-screen w-full">
        {/* Slim Single-Row Header */}
        <Header
          currentStage={currentStage}
          onSelectStage={handleSelectStage}
          domain={domain}
          onChangeDomain={handleDomainChange}
          mode={mode}
          onToggleMode={setMode}
          isRunning={isLiveRunning}
          viewMode="console"
          onToggleViewMode={(vm) => {
            if (vm === "overview") {
              navigate("/");
            }
          }}
          tier={tier}
          onToggleTier={setTier}
          isCloudConnected={isCloudConnected}
          onOpenBilling={() => setIsBillingModalOpen(true)}
          onGoToLanding={() => navigate("/")}
          user={user}
          onOpenAuth={() => setIsAuthModalOpen(true)}
          onOpenExperiments={() => setIsExperimentsModalOpen(true)}
          onSignOut={handleSignOut}
          sidebarPresent={true}
        />

        {/* 5-Stage Interactive Console Workspace */}
        <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 bg-zinc-50">
          {/* Dodo Payments Checkout Redirect Banner */}
          <AnimatePresence>
            {dodoBanner && (
              <motion.div
                initial={{ opacity: 0, height: 0, y: -8 }}
                animate={{ opacity: 1, height: "auto", y: 0 }}
                exit={{ opacity: 0, height: 0, y: -8 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="overflow-hidden"
              >
                <div
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border px-4 py-3 text-xs font-geist shadow-xs ${
                    dodoBanner.type === "success"
                      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                      : "border-amber-200 bg-amber-50 text-amber-900"
                  }`}
                >
                  <div className="flex items-center gap-2 flex-1">
                    <span className="font-medium leading-relaxed">
                      {dodoBanner.message}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setDodoBanner(null)}
                    className={`text-xs font-semibold hover:underline cursor-pointer shrink-0 text-left sm:text-right ${
                      dodoBanner.type === "success"
                        ? "text-emerald-700 hover:text-emerald-900"
                        : "text-amber-800 hover:text-amber-950"
                    }`}
                  >
                    Dismiss
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* One-Time Onboarding Guide Banner */}
          <AnimatePresence>
            {!isOnboarded && (
              <motion.div
                initial={{ opacity: 0, height: 0, y: -8 }}
                animate={{ opacity: 1, height: "auto", y: 0 }}
                exit={{ opacity: 0, height: 0, y: -8 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="overflow-hidden"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-lg bg-indigo-50/60 border border-indigo-100 px-6 py-3 text-xs font-geist">
                  <div className="flex flex-wrap items-center gap-2 text-zinc-800">
                    <span className="font-bold text-zinc-900 font-geist">
                      Getting Started with Reco:
                    </span>
                    <span className="text-zinc-600 font-mono text-[11px]">
                      1. Enter your goal below &rarr; 2. Reco generates the pipeline &rarr; 3. Inspect mutations &amp; promotion in stages 2-5
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={handleDismissOnboarding}
                    className="text-xs font-medium text-indigo-600 hover:text-indigo-800 hover:underline cursor-pointer shrink-0 text-left sm:text-right font-geist"
                  >
                    Got it
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {currentStage === "BUILD" && (
            <div className="space-y-4">
              <GoalInputSection
                domain={domain}
                currentDag={currentDag}
                onSynthesize={handleSynthesize}
                onProceedToRun={handleProceedToRun}
                isSynthesizing={isSynthesizing}
                hasSynthesized={hasSynthesized}
                onOpenToolCatalog={() => setIsToolCatalogOpen(true)}
              />
            </div>
          )}

          {currentStage === "RUN" && (
            <div className="space-y-6">
              <ModeHarnessBanner mode={mode} />

              {!hasSynthesized && !domain ? (
                <StageAwaitingExecutionCard
                  icon="clock"
                  title="No Benchmark Execution Yet"
                  description="Synthesize an agent graph in Stage 01 (BUILD) or select a domain preset to execute the baseline evaluation."
                  onGoToBuild={() => {
                    setCurrentStage("BUILD");
                    navigate("/console?stage=1");
                  }}
                  onLoadDemo={() => handleDomainChange("reconciliation")}
                />
              ) : (
                <>
                  <RunProgressTracker
                    architecture={currentDag}
                    autoStart={false}
                    onExecutionStart={() => {
                      // hasExecutedRun only becomes true when execution completes
                    }}
                    onExecutionComplete={() => {
                      setHasExecutedRun(true);
                      if (mode === "live") {
                        setCurrentScorecard(V2_CANDIDATE_C_SCORECARD);
                        setCurrentComparison(COMPARISON_V0_VS_CANDIDATE_C);
                      }
                    }}
                  />
                  {hasExecutedRun ? (
                    <ScorecardView
                      scorecard={currentScorecard}
                      comparison={currentComparison}
                      onProceedToUnderstand={() => {
                        setCurrentStage("UNDERSTAND");
                        navigate("/console?stage=3");
                      }}
                    />
                  ) : (
                    <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center space-y-3">
                      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                        <Clock className="h-5 w-5" />
                      </div>
                      <div className="space-y-1 max-w-sm mx-auto">
                        <h4 className="text-sm font-semibold text-zinc-900 font-geist">
                          Scorecard Awaiting DAG Execution
                        </h4>
                        <p className="text-xs text-zinc-500 font-geist">
                          Click &quot;Execute DAG&quot; above to run the topological traversal and generate the 4-axis scorecard evaluation.
                        </p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {currentStage === "UNDERSTAND" && (
            <div className="space-y-6">
              {!isPipelineReady ? (
                <StageAwaitingExecutionCard
                  title="Diagnostic Analysis Awaiting Run"
                  description="Complete Stage 01 (BUILD) and Stage 02 (RUN) to inspect failure clusters, mutation tournaments, and held-out validation."
                  onGoToBuild={() => {
                    setCurrentStage("BUILD");
                    navigate("/console?stage=1");
                  }}
                  onLoadDemo={() => handleDomainChange("reconciliation")}
                />
              ) : (
                <>
                  <FailureExplorer
                    diagnostics={FAILURE_DIAGNOSTICS}
                    onProceedToImprove={() => {
                      setCurrentStage("IMPROVE");
                      navigate("/console?stage=4");
                    }}
                  />
                  <EpistemicMemoryLedger />
                </>
              )}
            </div>
          )}

          {currentStage === "IMPROVE" && (
            <div className="space-y-6">
              {!isPipelineReady ? (
                <StageAwaitingExecutionCard
                  title="Diagnostic Analysis Awaiting Run"
                  description="Complete Stage 01 (BUILD) and Stage 02 (RUN) to inspect failure clusters, mutation tournaments, and held-out validation."
                  onGoToBuild={() => {
                    setCurrentStage("BUILD");
                    navigate("/console?stage=1");
                  }}
                  onLoadDemo={() => handleDomainChange("reconciliation")}
                />
              ) : (
                <>
                  <ModeHarnessBanner mode={mode} />
                  <CandidateComparisonView
                    candidates={CANDIDATES_TOURNAMENT}
                    lineage={EVOLUTION_LINEAGE}
                    onProceedToValidate={() => {
                      setCurrentStage("VALIDATE");
                      navigate("/console?stage=5");
                    }}
                  />
                  <EpistemicMemoryLedger />
                </>
              )}
            </div>
          )}

          {currentStage === "VALIDATE" && (
            <div className="space-y-6">
              {!isPipelineReady ? (
                <StageAwaitingExecutionCard
                  title="Diagnostic Analysis Awaiting Run"
                  description="Complete Stage 01 (BUILD) and Stage 02 (RUN) to inspect failure clusters, mutation tournaments, and held-out validation."
                  onGoToBuild={() => {
                    setCurrentStage("BUILD");
                    navigate("/console?stage=1");
                  }}
                  onLoadDemo={() => handleDomainChange("reconciliation")}
                />
              ) : (
                <>
                  {/* Stage 05: Neatlogs Live Trace Deep-Link Header */}
                  <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/70 via-purple-50/30 to-white p-4 shadow-2xs">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs">
                        <Broadcast size={20} weight="duotone" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold uppercase tracking-wider text-indigo-950">
                            Neatlogs Distributed Telemetry
                          </span>
                          {mode === "demo" && !(activeExperiment?.neatlogs_trace_url || activeExperiment?.neatlogs?.trace_url) ? (
                            <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-mono font-bold text-zinc-600 border border-zinc-200">
                              DEMO ARTIFACT REPLAY
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-800 border border-emerald-200">
                              LIVE CLOUD LINKED
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-zinc-600 font-geist mt-0.5">
                          {mode === "demo" && !(activeExperiment?.neatlogs_trace_url || activeExperiment?.neatlogs?.trace_url)
                            ? "Displaying canonical verification trace. Configure your NEATLOGS_API_KEY in .env to stream live flamegraphs."
                            : "Real-time OpenTelemetry trace exported to Neatlogs Cloud with 4-axis evaluation scorecards."}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1">
                      {mode === "demo" && !(activeExperiment?.neatlogs_trace_url || activeExperiment?.neatlogs?.trace_url) ? (
                        <div className="relative group">
                          <button
                            type="button"
                            disabled
                            title="Demo trace — configure your Neatlogs API key to see live traces"
                            className="inline-flex items-center gap-2 rounded-xl bg-zinc-100 text-zinc-400 border border-zinc-200 px-4 py-2 text-xs font-semibold cursor-not-allowed shadow-none font-geist"
                          >
                            <ArrowSquareOut size={16} weight="bold" className="text-zinc-400" />
                            <span>Inspect Live Trace on Neatlogs ↗</span>
                          </button>
                          <div className="absolute right-0 bottom-full mb-1.5 hidden group-hover:block z-30 w-72 rounded-lg bg-zinc-900 text-zinc-100 text-[11px] p-2.5 shadow-lg border border-zinc-800 font-sans leading-snug pointer-events-none">
                            Demo trace — configure your Neatlogs API key to see live traces
                          </div>
                        </div>
                      ) : (
                        <a
                          href={
                            activeExperiment?.neatlogs_trace_url ||
                            activeExperiment?.neatlogs?.trace_url ||
                            (NEATLOGS_TRACE.neatlogs_trace_url || NEATLOGS_TRACE.trace_url || `https://app.neatlogs.com/traces/${NEATLOGS_TRACE.trace_id}`)
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-4 py-2 text-xs font-semibold shadow-xs transition-all active:scale-[0.98] font-geist border border-indigo-500/30 cursor-pointer"
                        >
                          <ArrowSquareOut size={16} weight="bold" />
                          <span>Inspect Live Trace on Neatlogs ↗</span>
                        </a>
                      )}
                      {mode === "demo" && !(activeExperiment?.neatlogs_trace_url || activeExperiment?.neatlogs?.trace_url) && (
                        <span className="text-[10px] font-mono text-zinc-400">
                          (Demo trace — set up your Neatlogs key to see live traces)
                        </span>
                      )}
                    </div>
                  </div>

                  <HeldOutValidationView
                    data={HELD_OUT_VALIDATION_DATA}
                    trace={NEATLOGS_TRACE}
                    isDemo={mode === "demo" && !(activeExperiment?.neatlogs_trace_url || activeExperiment?.neatlogs?.trace_url)}
                  />
                </>
              )}
            </div>
          )}
        </main>

        {/* Footer / Telemetry status line */}
        <footer className="w-full border-t border-zinc-200 bg-white py-3.5 text-xs text-zinc-500 font-mono">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <span>TRACK 1: AUTONOMOUS AGENT ENGINEERING</span>
              <span>•</span>
              <span>AIR-GAPPED BENCHMARK HARNESS</span>
            </div>
            <div className="flex items-center gap-3">
              <span>STAGE: {currentStage}</span>
              <span>•</span>
              <span>MODE: {mode.toUpperCase()}</span>
              <span>•</span>
              <span className={tier === "pro" ? "text-indigo-600 font-semibold" : ""}>
                TIER: {tier.toUpperCase()}
              </span>
              <span>•</span>
              <span className="text-emerald-700 font-medium">SUPABASE: SYNCED</span>
            </div>
          </div>
        </footer>
      </div>

      {/* Non-blocking Dodo Payments Monetization Modal */}
      <BillingModal
        isOpen={isBillingModalOpen}
        onClose={() => setIsBillingModalOpen(false)}
        currentTier={tier}
        onTierChange={setTier}
        userId={user?.id || "usr_demo"}
        token={token}
        userEmail={user?.email}
        isAuthenticated={Boolean(user && token)}
        onOpenAuth={() => {
          setIsBillingModalOpen(false);
          setIsAuthModalOpen(true);
        }}
      />

      {/* Supabase Cloud Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={(authedUser, authToken) => {
          setUser(authedUser);
          setToken(authToken);
        }}
      />

      {/* Supabase Persistent Experiments Repository Modal */}
      <MyExperimentsModal
        isOpen={isExperimentsModalOpen}
        onClose={() => setIsExperimentsModalOpen(false)}
        token={token}
        onLoadExperiment={handleLoadExperiment}
      />

      {/* Central Tool Registry Catalog Modal */}
      <ToolCatalogModal
        isOpen={isToolCatalogOpen}
        onClose={() => setIsToolCatalogOpen(false)}
        tools={tools}
        selectedTools={selectedTools}
        onToggleTool={handleToggleTool}
      />
    </div>
  );
};

export default ConsolePage;
