import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ScorecardView } from "@/components/ScorecardView";
import { RunProgressTracker } from "@/components/RunProgressTracker";
import {
  V0_BASELINE_SCORECARD,
  COMPARISON_V0_VS_CANDIDATE_B,
  INITIAL_DAG_V0,
} from "@/lib/mockData";

describe("Stage 2: ScorecardView & RunProgressTracker", () => {
  it("renders 4 canonical axes: Accuracy, Reliability, Cost, and Speed", () => {
    render(
      <ScorecardView
        scorecard={V0_BASELINE_SCORECARD}
        comparison={COMPARISON_V0_VS_CANDIDATE_B}
        onProceedToUnderstand={vi.fn()}
      />
    );

    expect(screen.getAllByText(/1\. Accuracy/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/2\. Reliability/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/3\. Cost/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/4\. Speed/i)[0]).toBeInTheDocument();

    // Verify baseline accuracy
    expect(screen.getAllByText(/16\.7%/i)[0]).toBeInTheDocument();
    // Verify delta badges
    expect(screen.getByText(/Δ \+66\.7%/i)).toBeInTheDocument();
    expect(screen.getByText(/Δ -\$0\.0010/i)).toBeInTheDocument();
  });

  it("renders Pareto dominant verdict badge", () => {
    render(
      <ScorecardView
        scorecard={V0_BASELINE_SCORECARD}
        comparison={COMPARISON_V0_VS_CANDIDATE_B}
        onProceedToUnderstand={vi.fn()}
      />
    );

    expect(screen.getByText(/PARETO DOMINANT/i)).toBeInTheDocument();
  });

  it("renders RunProgressTracker with topological execution controls", () => {
    render(<RunProgressTracker architecture={INITIAL_DAG_V0} />);

    expect(screen.getByText(/DAG Execution Progress & Topological Traversal/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Execute DAG/i })).toBeInTheDocument();
    expect(screen.getByText("Transaction Ingestion")).toBeInTheDocument();
    expect(screen.getByText("Exact Reconcile Tool")).toBeInTheDocument();
  });
});
