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
import { Header } from "@/components/Header";
import { GoalInputSection } from "@/components/GoalInputSection";
import { ScorecardView } from "@/components/ScorecardView";
import { RunProgressTracker } from "@/components/RunProgressTracker";
import { FailureExplorer } from "@/components/FailureExplorer";
import { CandidateComparisonView } from "@/components/CandidateComparisonView";
import { HeldOutValidationView } from "@/components/HeldOutValidationView";

export default function App() {
  const [currentStage, setCurrentStage] = useState<StageType>("BUILD");
  const [domain, setDomain] = useState<DomainType>("financial_reconciliation");
  const [mode, setMode] = useState<ExecutionMode>("demo");
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isLiveRunning, setIsLiveRunning] = useState(false);

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
    }, 600);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header with Mode Switcher & Domain Selector */}
      <Header
        currentStage={currentStage}
        onSelectStage={setCurrentStage}
        domain={domain}
        onChangeDomain={handleDomainChange}
        mode={mode}
        onToggleMode={setMode}
        isRunning={isLiveRunning || isSynthesizing}
      />

      {/* Main Console Workspace */}
      <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 space-y-6">
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
          <FailureExplorer
            diagnostics={FAILURE_DIAGNOSTICS}
            onProceedToImprove={() => setCurrentStage("IMPROVE")}
          />
        )}

        {currentStage === "IMPROVE" && (
          <CandidateComparisonView
            candidates={CANDIDATES_TOURNAMENT}
            lineage={EVOLUTION_LINEAGE}
            onProceedToValidate={() => setCurrentStage("VALIDATE")}
          />
        )}

        {currentStage === "VALIDATE" && (
          <HeldOutValidationView
            data={HELD_OUT_VALIDATION_DATA}
            trace={NEATLOGS_TRACE}
          />
        )}
      </main>

      {/* Footer / Telemetry status line */}
      <footer className="w-full border-t border-slate-900 bg-slate-950/80 py-3 text-xs text-slate-500 font-mono">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <span>TRACK 1: AUTONOMOUS AGENT ENGINEERING</span>
            <span>•</span>
            <span>AIR-GAPPED BENCHMARK HARNESS</span>
          </div>
          <div className="flex items-center gap-3">
            <span>MODE: {mode.toUpperCase()}</span>
            <span>•</span>
            <span className="text-emerald-400">VITE SPA READY</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export { App as EngineeringConsolePage };
