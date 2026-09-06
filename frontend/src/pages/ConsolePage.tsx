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
  const [domain, setDomain] = useState<DomainType | "">("");
  const [hasSynthesized, setHasSynthesized] = useState<boolean>(false);
  const [mode, setMode] = useState<ExecutionMode>("demo");
  const [tier, setTier] = useState<"free" | "pro">("free");
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

  const handleLoadExperiment = (expData: any) => {
    if (expData.domain) {
      handleDomainChange(expData.domain as DomainType);
    }
    if (expData.v0_scorecard) {
      setCurrentScorecard(expData.v1_scorecard || expData.v0_scorecard);
    }
    setCurrentStage("RUN");
  };

  // Active architecture and scorecards
  const [currentDag, setCurrentDag] = useState<DAGArchitecture>(INITIAL_DAG_V0);
  const [currentScorecard, setCurrentScorecard] = useState<Scorecard>(
    V0_BASELINE_SCORECARD
  );
  const [currentComparison, setCurrentComparison] = useState<
    ScorecardComparison | undefined
  >(COMPARISON_V0_VS_CANDIDATE_B);

  // Handle Domain Change
  const handleDomainChange = (newDomain: DomainType | "") => {
    setDomain(newDomain);
    if (newDomain && DOMAIN_PRESETS[newDomain]) {
      const preset = DOMAIN_PRESETS[newDomain];
      setCurrentDag({
        ...INITIAL_DAG_V0,
        domain: newDomain,
        name: `Agent_${preset.name.replace(/\s+/g, "_")}_V0`,
      });
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
    setCurrentStage("RUN");
    navigate("/console?stage=2");
  };


  return (
    <div className="min-h-screen bg-zinc-50 flex font-sans selection:bg-indigo-600 selection:text-white">
      {/* Fixed Left Sidebar (~220px) */}
      <Sidebar
        currentStage={currentStage}
        onSelectStage={setCurrentStage}
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
          onSelectStage={setCurrentStage}
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
            <GoalInputSection
              domain={domain}
              currentDag={currentDag}
              onSynthesize={handleSynthesize}
              onProceedToRun={handleProceedToRun}
              isSynthesizing={isSynthesizing}
              hasSynthesized={hasSynthesized}
              onOpenToolCatalog={() => setIsToolCatalogOpen(true)}
            />
          )}

          {currentStage === "RUN" && (
            <div className="space-y-6">
              <RunProgressTracker
                architecture={currentDag}
                onExecutionComplete={() => {
                  if (mode === "live") {
                    setCurrentScorecard(V2_CANDIDATE_C_SCORECARD);
                    setCurrentComparison(COMPARISON_V0_VS_CANDIDATE_C);
                  }
                }}
              />
              <ScorecardView
                scorecard={currentScorecard}
                comparison={currentComparison}
                onProceedToUnderstand={() => setCurrentStage("UNDERSTAND")}
              />
            </div>
          )}

          {currentStage === "UNDERSTAND" && (
            <div className="space-y-6">
              <FailureExplorer
                diagnostics={FAILURE_DIAGNOSTICS}
                onProceedToImprove={() => setCurrentStage("IMPROVE")}
              />
              <EpistemicMemoryLedger />
            </div>
          )}

          {currentStage === "IMPROVE" && (
            <div className="space-y-6">
              <CandidateComparisonView
                candidates={CANDIDATES_TOURNAMENT}
                lineage={EVOLUTION_LINEAGE}
                onProceedToValidate={() => setCurrentStage("VALIDATE")}
              />
              <EpistemicMemoryLedger />
            </div>
          )}

          {currentStage === "VALIDATE" && (
            <HeldOutValidationView
              data={HELD_OUT_VALIDATION_DATA}
              trace={NEATLOGS_TRACE}
            />
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
