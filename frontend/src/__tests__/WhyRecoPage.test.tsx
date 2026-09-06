import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { WhyRecoPage } from "@/pages/WhyRecoPage";

const mockedNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

describe("WhyRecoPage Component", () => {
  beforeEach(() => {
    mockedNavigate.mockClear();
  });

  it("renders the hero section with the core shift headline", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      /Why Reco\?/i
    );
    expect(
      screen.getByText(
        /The Shift from Prompt Guesswork to Automated Agent Engineering/i
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(/THE PARADIGM SHIFT: PROMPT GUESSWORK → AGENT COMPILER/i)
    ).toBeInTheDocument();
  });

  it("renders all 4 crisis failure modes of the 'Prompt & Pray' trap", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    expect(
      screen.getByText(/Why 95% of AI Agents Break in Production/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Manual Prompt Tweaking")).toBeInTheDocument();
    expect(screen.getByText("Brittle Tool Glue Code")).toBeInTheDocument();
    expect(screen.getByText("Silent Regression")).toBeInTheDocument();
    expect(screen.getByText("Zero Held-Out Validation")).toBeInTheDocument();
  });

  it("renders the competitive benchmark comparison matrix with all axes", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    expect(
      screen.getByText(/How Reco Compares to Existing Frameworks/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Automated DAG Synthesis")).toBeInTheDocument();
    expect(screen.getByText("Diagnostic Taxonomy")).toBeInTheDocument();
    expect(screen.getByText("Mutation Tournaments")).toBeInTheDocument();
    expect(screen.getByText("Epistemic Memory")).toBeInTheDocument();
    expect(
      screen.getByText("Held-Out Leakage Prevention")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Built-in Tracing (Neatlogs)")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Billing & Monetization (Dodo Payments)")
    ).toBeInTheDocument();
  });

  it("renders empirical benchmark results with accurate metrics", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    expect(
      screen.getByText(/Empirical ROI & Performance Multipliers/i)
    ).toBeInTheDocument();
    expect(screen.getByText("+83.3% Lift")).toBeInTheDocument();
    expect(screen.getByText("100.0%")).toBeInTheDocument();
    expect(screen.getByText("-20% Latency")).toBeInTheDocument();
    expect(screen.getByText("80.0ms")).toBeInTheDocument();
    expect(screen.getByText("-18% Spend")).toBeInTheDocument();
    expect(screen.getByText("$0.0041")).toBeInTheDocument();
    expect(screen.getByText("0.0%")).toBeInTheDocument();
  });

  it("renders the real-world financial invoice reconciliation case study and toggles tabs", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    expect(
      screen.getByText(
        /Real-World Failure Cluster: Financial Invoice Reconciliation/i
      )
    ).toBeInTheDocument();

    // Default tab is 'solution'
    expect(
      screen.getByText(
        /Reco Closed-Loop Compiler Synthesized Candidate C/i
      )
    ).toBeInTheDocument();

    // Switch to problem tab
    const problemTab = screen.getByRole("button", {
      name: /1\. The Naive Failures/i,
    });
    fireEvent.click(problemTab);
    expect(
      screen.getByText(/Baseline V0 Architecture Failed 5 out of 6 Cases/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Floating-Point Currency Drift/i)).toBeInTheDocument();

    // Switch to diff tab
    const diffTab = screen.getByRole("button", {
      name: /3\. Verifier Node Diff/i,
    });
    fireEvent.click(diffTab);
    expect(
      screen.getByText(/Synthesized Architecture Diff/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/verifier_node \[JSON Validator\]/i)
    ).toBeInTheDocument();
  });

  it("renders enterprise architecture pillars", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Air-Gapped Test Isolation")).toBeInTheDocument();
    expect(screen.getByText("Supabase Multi-Tenant RLS")).toBeInTheDocument();
    expect(screen.getByText("Neatlogs Distributed Tracing")).toBeInTheDocument();
    expect(screen.getByText("SLA & Cost Constraints")).toBeInTheDocument();
    expect(screen.getByText("Dodo Payments Monetization")).toBeInTheDocument();
    expect(screen.getByText("Deterministic Output Verification")).toBeInTheDocument();
  });

  it("navigates to console when Launch Console is clicked", () => {
    render(
      <MemoryRouter>
        <WhyRecoPage />
      </MemoryRouter>
    );

    const consoleButtons = screen.getAllByRole("button", {
      name: /Launch Console/i,
    });
    fireEvent.click(consoleButtons[0]);
    expect(mockedNavigate).toHaveBeenCalledWith("/console");
  });
});
