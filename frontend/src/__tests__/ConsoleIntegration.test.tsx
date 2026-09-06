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

    // Navigate to Stage 2: RUN on clean blank canvas -> shows clean awaiting state
    const runNav = screen.getByRole("button", { name: /Run 02/i });
    fireEvent.click(runNav);
    expect(screen.getByText(/No Benchmark Execution Yet/i)).toBeInTheDocument();

    // Select "Financial Reconcile" from domain preset dropdown in sidebar to activate pipeline
    const domainSelect = screen.getByLabelText(/Select Domain/i);
    fireEvent.change(domainSelect, { target: { value: "financial_reconciliation" } });

    // Now Stage 2: RUN is populated with 4-Axis Scorecard
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

  it("initial load of /console?stage=2 shows clean awaiting state rather than pre-completed cards", () => {
    render(<EngineeringConsolePage initialEntries={["/console?stage=2"]} />);

    // Verify it shows clean awaiting state
    expect(screen.getByText(/No Benchmark Execution Yet/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Synthesize an agent graph in Stage 01 \(BUILD\) or select a domain preset/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Go to Stage 01: BUILD →/i })).toBeInTheDocument();

    // Select "Financial Reconcile" from domain preset dropdown in sidebar
    const domainSelect = screen.getByLabelText(/Select Domain/i);
    fireEvent.change(domainSelect, { target: { value: "financial_reconciliation" } });

    // Verify Stage 2 now populates with complete data
    expect(screen.getByText(/RUN: 4-Axis Scorecard & Empirical Evaluation/i)).toBeInTheDocument();
    expect(screen.getByText(/DAG Execution Progress & Topological Traversal/i)).toBeInTheDocument();

    // Verify Stages 3-5 populate immediately
    const understandNav = screen.getByRole("button", { name: /Understand 03/i });
    fireEvent.click(understandNav);
    expect(screen.getByText(/UNDERSTAND: 12-Category Failure Diagnostics Taxonomy/i)).toBeInTheDocument();

    const improveNav = screen.getByRole("button", { name: /Improve 04/i });
    fireEvent.click(improveNav);
    expect(screen.getByText(/IMPROVE: Multi-Candidate Tournament/i)).toBeInTheDocument();

    const validateNav = screen.getByRole("button", { name: /Validate 05/i });
    fireEvent.click(validateNav);
    expect(screen.getByText(/VALIDATE: Air-Gapped Held-Out Generalization/i)).toBeInTheDocument();
  });

  it("RunProgressTracker starts with nodes in pending status and 0.0 ms until Execute DAG is clicked", () => {
    render(<EngineeringConsolePage initialEntries={["/console?stage=2&preset=financial_reconciliation"]} />);

    // Total elapsed time and pending nodes display 0.0 ms
    const elapsedBadges = screen.getAllByText(/0\.0\s*ms/);
    expect(elapsedBadges.length).toBeGreaterThanOrEqual(1);

    // Nodes are in PENDING status initially
    const pendingBadges = screen.getAllByText("PENDING");
    expect(pendingBadges.length).toBe(4);

    // Execute DAG button is available
    const executeBtn = screen.getByRole("button", { name: /Execute DAG/i });
    expect(executeBtn).toBeInTheDocument();

    // Click Execute DAG
    fireEvent.click(executeBtn);
    expect(screen.getByText(/Executing.../i)).toBeInTheDocument();
  });

  it("displays DEMO and LIVE execution harness banners in Stage 02 and Stage 04", () => {
    render(<EngineeringConsolePage initialEntries={["/console?stage=2&preset=financial_reconciliation"]} />);

    // Default mode is demo: displays Demo harness banner
    expect(
      screen.getByText(/DEMO BENCHMARK HARNESS/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Static Canonical Artifacts \(Offline Sandbox\)/i)
    ).toBeInTheDocument();

    // Switch to Live mode in sidebar
    const liveRadio = screen.getByRole("radio", { name: /Live/i });
    fireEvent.click(liveRadio);

    // Displays Live harness banner
    expect(
      screen.getByText(/LIVE EXECUTION HARNESS/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Real GLM-4\.7-Flash \(TensorMux\) & Supabase Cloud Persistence/i)
    ).toBeInTheDocument();

    // Navigate to Stage 04: IMPROVE and verify Live harness banner is displayed there too
    const improveNav = screen.getByRole("button", { name: /Improve 04/i });
    fireEvent.click(improveNav);
    expect(
      screen.getByText(/LIVE EXECUTION HARNESS/i)
    ).toBeInTheDocument();
  });
});
