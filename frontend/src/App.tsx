import React, { useState, useEffect } from "react";
import {
  DomainType,
  ExecutionMode,
  StageType,
  DAGArchitecture,
  Scorecard,
  ScorecardComparison,
} from "@/lib/types";
import {
  INITIAL_DAG_V0,
  OPTIMIZED_DAG_V2,
  V0_BASELINE_SCORECARD,
  V1_CANDIDATE_B_SCORECARD,
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
import { LandingPage } from "@/components/LandingPage";
import { Header } from "@/components/Header";
import { HeroLandingView } from "@/components/HeroLandingView";
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
import { ToolSchema } from "@/lib/types";
import { fetchTools } from "@/services/api";
import { getSession, signOut, onAuthStateChange } from "@/lib/supabaseClient";

export interface AppProps {
  initialViewMode?: "overview" | "console";
  initialPage?: "landing" | "console";
}

export default function App({ initialViewMode = "overview", initialPage }: AppProps = {}) {
  const defaultPage =
    initialPage ??
    (typeof process !== "undefined" && process.env.NODE_ENV === "test"
      ? "console"
      : "landing");

  const [page, setPage] = useState<"landing" | "console">(defaultPage);
  const [viewMode, setViewMode] = useState<"overview" | "console">(initialViewMode);
  const [currentStage, setCurrentStage] = useState<StageType>("BUILD");
  const [domain, setDomain] = useState<DomainType>("financial_reconciliation");
  const [mode, setMode] = useState<ExecutionMode>("demo");
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isLiveRunning, setIsLiveRunning] = useState(false);

  // Monetization & Cloud Session state
  const [tier, setTier] = useState<"free" | "pro">("free");
  const [isBillingModalOpen, setIsBillingModalOpen] = useState(false);
  const [isCloudConnected] = useState(true);

  // Supabase Cloud Auth & Session state
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
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
    setViewMode("console");
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
  const handleDomainChange = (newDomain: DomainType) => {
    setDomain(newDomain);
    const preset = DOMAIN_PRESETS[newDomain];
    setCurrentDag({
      ...INITIAL_DAG_V0,
      domain: newDomain,
      name: `Agent_${preset.name.replace(/\s+/g, "_")}_V0`,
    });
  };

  // Handle Architecture Synthesis Trigger
  const handleSynthesize = (goalText: string) => {
    setIsSynthesizing(true);
    setTimeout(() => {
      setIsSynthesizing(false);
      setCurrentDag(INITIAL_DAG_V0);
      setCurrentStage("RUN");
      setViewMode("console");
    }, 600);
  };

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
      {/* Landing Page -- full screen, no header/footer */}
      {page === "landing" && (
        <LandingPage
          onEnterConsole={() => {
            setPage("console");
            setViewMode("console");
            setCurrentStage("BUILD");
          }}
        />
      )}

      {/* Engineering Console */}
      {page === "console" && (
        <>
          {/* Sticky Header with Stage Navigator & Tools */}
          <Header
            currentStage={currentStage}
            onSelectStage={setCurrentStage}
            domain={domain}
            onChangeDomain={handleDomainChange}
            mode={mode}
            onToggleMode={setMode}
            isRunning={isLiveRunning}
            viewMode={viewMode}
            onToggleViewMode={setViewMode}
            tier={tier}
            onToggleTier={setTier}
            isCloudConnected={isCloudConnected}
            onOpenBilling={() => setIsBillingModalOpen(true)}
            onGoToLanding={() => setPage("landing")}
            user={user}
            onOpenAuth={() => setIsAuthModalOpen(true)}
            onOpenExperiments={() => setIsExperimentsModalOpen(true)}
            onSignOut={handleSignOut}
          />

          {/* Main Container */}
          <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 bg-zinc-50">
            {/* Overview Landing View */}
            {viewMode === "overview" && (
              <HeroLandingView
                onLaunchConsole={() => setViewMode("console")}
                onExploreLineage={() => {
                  setViewMode("console");
                  setCurrentStage("IMPROVE");
                }}
                onSelectStage={(stage) => {
                  setViewMode("console");
                  setCurrentStage(stage);
                }}
              />
            )}

            {/* 5-Stage Interactive Console Workspace */}
            {viewMode === "console" && (
              <>
                {currentStage === "BUILD" && (
                  <GoalInputSection
                    domain={domain}
                    currentDag={currentDag}
                    onSynthesize={handleSynthesize}
                    onProceedToRun={() => setCurrentStage("RUN")}
                    isSynthesizing={isSynthesizing}
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
              </>
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
                <span>VIEW: {viewMode.toUpperCase()}</span>
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

          {/* Non-blocking Dodo Payments Monetization Modal */}
          <BillingModal
            isOpen={isBillingModalOpen}
            onClose={() => setIsBillingModalOpen(false)}
            currentTier={tier}
            onTierChange={setTier}
            userId={user?.id || "usr_demo"}
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
        </>
      )}
    </div>
  );
}

export { App as EngineeringConsolePage };
