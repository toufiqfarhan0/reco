import React, { useState } from "react";
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
    <div className="min-h-screen bg-[#fafafa] text-zinc-950 flex flex-col font-sans selection:bg-zinc-950 selection:text-white">
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
          />

          {/* Main Container */}
          <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6 bg-[#fafafa]">
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
          <footer className="w-full border-t border-zinc-200/80 bg-white py-3.5 text-xs text-zinc-400 font-mono">
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
                <span className={tier === "pro" ? "text-violet-600 font-semibold" : ""}>
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
            userId="usr_demo"
          />
        </>
      )}
    </div>
  );
}

export { App as EngineeringConsolePage };
