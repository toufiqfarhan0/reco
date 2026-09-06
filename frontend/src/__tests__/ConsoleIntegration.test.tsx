import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import EngineeringConsolePage from "@/App";

describe("Console Integration: 5-Stage Engineering Navigator", () => {
  it("renders HeroLandingView in overview mode and transitions to console", () => {
    render(<EngineeringConsolePage />);

    // Initial Overview view mode renders HeroLandingView
    expect(
      screen.getByRole("heading", { name: /Autonomous Agent Engineering System/i })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/TRACK 1: AUTOMATED AGENT ENGINEERING • SYNDICATE BY MAXIMOR/i)
    ).toBeInTheDocument();

    // Click Launch Interactive Console to enter 5-stage workspace
    const launchBtn = screen.getByRole("button", { name: /Launch Interactive Console/i });
    fireEvent.click(launchBtn);

    // Stage 1: BUILD is now active
    expect(screen.getByText(/BUILD: Natural Language Goal & DAG Synthesis/i)).toBeInTheDocument();
  });

  it("navigates across all 5 stages from BUILD to VALIDATE with Epistemic Memory Ledger in Stages 3 & 4", () => {
    render(<EngineeringConsolePage initialViewMode="console" />);

    // Stage 1: BUILD
    expect(screen.getByText(/BUILD: Natural Language Goal & DAG Synthesis/i)).toBeInTheDocument();

    // Navigate to Stage 2: RUN
    const runNav = screen.getByRole("button", { name: /Run 02/i });
    fireEvent.click(runNav);
    expect(screen.getByText(/RUN: 4-Axis Scorecard & Empirical Evaluation/i)).toBeInTheDocument();

    // Navigate to Stage 3: UNDERSTAND
    const understandNav = screen.getByRole("button", { name: /Understand 03/i });
    fireEvent.click(understandNav);
    expect(screen.getByText(/UNDERSTAND: 12-Category Failure Diagnostics Taxonomy/i)).toBeInTheDocument();
    // Verify Epistemic Memory Ledger is mounted in Stage 3
    expect(
      screen.getByText(/Epistemic Memory Ledger: Generational Self-Reflection/i)
    ).toBeInTheDocument();

    // Navigate to Stage 4: IMPROVE
    const improveNav = screen.getByRole("button", { name: /Improve 04/i });
    fireEvent.click(improveNav);
    expect(screen.getByText(/IMPROVE: Multi-Candidate Tournament/i)).toBeInTheDocument();
    // Verify Epistemic Memory Ledger is mounted in Stage 4
    expect(
      screen.getByText(/Epistemic Memory Ledger: Generational Self-Reflection/i)
    ).toBeInTheDocument();

    // Navigate to Stage 5: VALIDATE
    const validateNav = screen.getByRole("button", { name: /Validate 05/i });
    fireEvent.click(validateNav);
    expect(screen.getByText(/VALIDATE: Air-Gapped Held-Out Generalization/i)).toBeInTheDocument();
    expect(screen.getByText(/FORMAL PROMOTION DECISION/i)).toBeInTheDocument();
  });

  it("jumps directly to Stage 04: Improve when clicking 'Explore Evolution Lineage' from Hero", () => {
    render(<EngineeringConsolePage initialViewMode="overview" />);

    const lineageBtn = screen.getByRole("button", { name: /Explore Evolution Lineage/i });
    fireEvent.click(lineageBtn);

    // Should switch to console and jump directly to Stage 4: IMPROVE
    expect(screen.getByText(/IMPROVE: Multi-Candidate Tournament/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Epistemic Memory Ledger: Generational Self-Reflection/i)
    ).toBeInTheDocument();
  });

  it("renders dismissible onboarding guide banner and persists dismissal in localStorage", () => {
    localStorage.removeItem("reco_onboarded");
    render(<EngineeringConsolePage initialViewMode="console" />);

    expect(screen.getByText(/Getting Started with Reco:/i)).toBeInTheDocument();
    expect(screen.getByText(/1\. Enter your goal below/i)).toBeInTheDocument();

    const gotItBtn = screen.getByRole("button", { name: /Got it/i });
    fireEvent.click(gotItBtn);

    expect(localStorage.getItem("reco_onboarded")).toBe("true");
  });
});
