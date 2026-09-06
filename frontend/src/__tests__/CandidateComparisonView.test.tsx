import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CandidateComparisonView } from "@/components/CandidateComparisonView";
import { CANDIDATES_TOURNAMENT, EVOLUTION_LINEAGE } from "@/lib/mockData";

describe("Stage 4: CandidateComparisonView & MutationInspector", () => {
  it("renders multi-candidate tournament: Candidate A, B, C", () => {
    render(
      <CandidateComparisonView
        candidates={CANDIDATES_TOURNAMENT}
        lineage={EVOLUTION_LINEAGE}
        onProceedToValidate={vi.fn()}
      />
    );

    expect(screen.getByText(/STAGE 04/i)).toBeInTheDocument();
    expect(screen.getByText(/Candidate A \(Baseline V0\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Candidate B \(Smart Reconcile\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Candidate C \(Verifier Guarded\)/i)[0]).toBeInTheDocument();
    expect(screen.getByText("CHAMPION")).toBeInTheDocument();
  });

  it("renders prompt diff inspector and allows switching tabs", () => {
    render(
      <CandidateComparisonView
        candidates={CANDIDATES_TOURNAMENT}
        lineage={EVOLUTION_LINEAGE}
        onProceedToValidate={vi.fn()}
      />
    );

    expect(screen.getByText(/Prompt & Configuration Mutation Inspector/i)).toBeInTheDocument();
    expect(screen.getByText(/Baseline Prompt \(V0\)/i)).toBeInTheDocument();

    const configTab = screen.getByRole("button", { name: /Config Diff/i });
    fireEvent.click(configTab);
    expect(screen.getByText(/Unified Architecture Configuration Diff/i)).toBeInTheDocument();
  });

  it("renders evolutionary lineage timeline", () => {
    render(
      <CandidateComparisonView
        candidates={CANDIDATES_TOURNAMENT}
        lineage={EVOLUTION_LINEAGE}
        onProceedToValidate={vi.fn()}
      />
    );

    expect(screen.getByText(/Autonomous Evolutionary Lineage Timeline/i)).toBeInTheDocument();
    expect(screen.getByText("GEN 00")).toBeInTheDocument();
    expect(screen.getByText("GEN 01")).toBeInTheDocument();
    expect(screen.getByText("GEN 02")).toBeInTheDocument();
  });
});
