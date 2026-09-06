import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { HeldOutValidationView } from "@/components/HeldOutValidationView";
import { HELD_OUT_VALIDATION_DATA, NEATLOGS_TRACE } from "@/lib/mockData";

describe("Stage 5: HeldOutValidationView & NeatlogsTraceCard", () => {
  it("renders formal Promotion Decision banner and air-gapped results", () => {
    render(
      <HeldOutValidationView
        data={HELD_OUT_VALIDATION_DATA}
        trace={NEATLOGS_TRACE}
      />
    );

    expect(screen.getByText(/STAGE 05/i)).toBeInTheDocument();
    expect(screen.getByText(/FORMAL PROMOTION DECISION/i)).toBeInTheDocument();
    expect(screen.getByText(/Candidate C Verified & Approved for Autonomous Deployment/i)).toBeInTheDocument();
    expect(screen.getByText(/ZERO LEAKAGE CONFIRMED/i)).toBeInTheDocument();
    expect(screen.getByText(/reco_held_001_casing_whitespace/i)).toBeInTheDocument();
  });

  it("renders Neatlogs trace card with span waterfall", () => {
    render(
      <HeldOutValidationView
        data={HELD_OUT_VALIDATION_DATA}
        trace={NEATLOGS_TRACE}
      />
    );

    expect(screen.getByText(/Neatlogs Production Execution Trace/i)).toBeInTheDocument();
    expect(screen.getByText("tr_neat_984f7e21a08b")).toBeInTheDocument();
    expect(screen.getByText(/Tool: smart_reconcile/i)).toBeInTheDocument();
    expect(screen.getByText(/Verifier: Schema & Duplicate Guardrail/i)).toBeInTheDocument();
  });

  it("allows switching promotion decision states (PROMOTED / REQUIRES_REVIEW / REJECTED)", () => {
    render(
      <HeldOutValidationView
        data={HELD_OUT_VALIDATION_DATA}
        trace={NEATLOGS_TRACE}
      />
    );

    const reviewBtn = screen.getByRole("button", { name: "REQUIRES_REVIEW" });
    fireEvent.click(reviewBtn);
    expect(screen.getByText(/Multi-Axis Tradeoffs Flagged During Evaluation/i)).toBeInTheDocument();

    const rejectBtn = screen.getByRole("button", { name: "REJECTED" });
    fireEvent.click(rejectBtn);
    expect(screen.getByText(/Candidate Failed Held-Out Generalization Criteria/i)).toBeInTheDocument();
  });
});
