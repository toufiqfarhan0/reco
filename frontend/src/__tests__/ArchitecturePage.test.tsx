import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { ArchitecturePage } from "@/pages/ArchitecturePage";

describe("ArchitecturePage Component", () => {
  const renderComponent = () =>
    render(
      <MemoryRouter initialEntries={["/architecture"]}>
        <ArchitecturePage />
      </MemoryRouter>
    );

  it("renders page header, Track 1 badge, and main research headline", () => {
    renderComponent();

    // Track 1 badges
    expect(
      screen.getAllByText(/Track 1/i).length
    ).toBeGreaterThanOrEqual(1);

    expect(
      screen.getByText(/The Architecture of Autonomous Agent Engineering/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/An in-depth mathematical treatise on Reco/i)
    ).toBeInTheDocument();
  });

  it("renders formal problem formulation definitions T = (G, I, O, C) and Agent DAG G", () => {
    renderComponent();

    expect(
      screen.getByText(/Formal Problem Formulation & DAG Compilation Theory/i)
    ).toBeInTheDocument();

    expect(screen.getByText(/Definition 1: TaskSpecification T/i)).toBeInTheDocument();
    expect(screen.getAllByText(/T = \(G, I, O, C\)/i)[0]).toBeInTheDocument();

    expect(screen.getByText(/Definition 2: Agent DAG G/i)).toBeInTheDocument();
    expect(screen.getAllByText(/G = \(V, E, v₀, V_term\)/i)[0]).toBeInTheDocument();
  });

  it("renders all 5 compilation engine stages with interactive switching", async () => {
    renderComponent();

    // All 5 stages
    expect(screen.getAllByText(/STAGE 01/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/STAGE 02/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/STAGE 03/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/STAGE 04/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/STAGE 05/i)[0]).toBeInTheDocument();

    // Click stage 2 tab
    const stage2Btn = screen.getByRole("button", { name: /STAGE 02/i });
    fireEvent.click(stage2Btn);

    // Verify stage 2 details are visible
    expect(
      await screen.findByText(/Deterministic Topological Execution & Scorecard Formulation/i)
    ).toBeInTheDocument();
  });

  it("renders the 12-category diagnostic taxonomy explorer and switches active category", () => {
    renderComponent();

    expect(
      screen.getByText(/Interactive Taxonomy: 12 Core Diagnostic Failure Classes/i)
    ).toBeInTheDocument();

    // Verify taxonomy buttons exist
    const toolArgBtn = screen.getByRole("button", { name: "TOOL_ARGUMENT_ERROR" });
    const arithBtn = screen.getByRole("button", { name: "ARITHMETIC_MISMATCH" });
    expect(toolArgBtn).toBeInTheDocument();
    expect(arithBtn).toBeInTheDocument();

    // Click ARITHMETIC_MISMATCH
    fireEvent.click(arithBtn);
    expect(screen.getByText(/Floating-Point Drift \/ Precision Loss/i)).toBeInTheDocument();
    expect(screen.getByText(/verifier_tolerance_guard node/i)).toBeInTheDocument();
  });

  it("renders epistemic memory invariant proofs and allows switching codified lessons", () => {
    renderComponent();

    expect(screen.getByText(/Epistemic Invariant Proof/i)).toBeInTheDocument();
    expect(screen.getByText(/forall s in States\(V_k\), I\(s\) = 1/i)).toBeInTheDocument();

    // Check lesson buttons
    const lesson2Btn = screen.getByRole("button", { name: /Lesson 02/i });
    fireEvent.click(lesson2Btn);

    expect(screen.getByText(/verifyFinancialBalance/i)).toBeInTheDocument();
  });

  it("renders system topology and all 4 infrastructure stack pillars", () => {
    renderComponent();

    expect(screen.getByText(/System Topology & Production Infrastructure Stack/i)).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /TensorMux/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Neatlogs/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Supabase/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Dodo Payments/i })).toBeInTheDocument();

    // Click Neatlogs tab
    const neatlogsBtn = screen.getByRole("button", { name: /Neatlogs/i });
    fireEvent.click(neatlogsBtn);

    expect(screen.getByText(/https:\/\/ingest\.neatlogs\.com/i)).toBeInTheDocument();
  });

  it("renders Why Reco paradigm comparison table", () => {
    renderComponent();

    expect(
      screen.getByText(/Why Reco: The Paradigm Shift from Heuristic Prompting to Autonomous Engineering/i)
    ).toBeInTheDocument();

    expect(screen.getByText(/Traditional "Vibe-Coding" Agent Setup/i)).toBeInTheDocument();
    expect(screen.getByText(/Reco Autonomous Agent Engineering/i)).toBeInTheDocument();
  });
});
