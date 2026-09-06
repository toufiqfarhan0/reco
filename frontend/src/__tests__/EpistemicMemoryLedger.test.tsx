import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EpistemicMemoryLedger } from "@/components/EpistemicMemoryLedger";

describe("EpistemicMemoryLedger Component", () => {
  it("renders header, judge query callout, and summary metrics", () => {
    render(<EpistemicMemoryLedger />);

    expect(
      screen.getByText(/Epistemic Memory Ledger: Generational Self-Reflection/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/JUDGE QUERY:/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Can you show the outputs of the agent getting better over time/i)
    ).toBeInTheDocument();
    expect(screen.getAllByText(/\+25\.0%/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders all 3 canonical epistemic lessons with required metrics", () => {
    render(<EpistemicMemoryLedger />);

    // Lesson 01
    expect(screen.getByText("Lesson 01")).toBeInTheDocument();
    expect(
      screen.getByText(/Third-party API timestamps require ISO-8601 UTC coercion before line-item matching/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/normalize_timestamp \(Node 02\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/SCHEMA_VIOLATION/i).length).toBeGreaterThanOrEqual(1);

    // Lesson 02
    expect(screen.getByText("Lesson 02")).toBeInTheDocument();
    expect(
      screen.getByText(/Floating-point discrepancies in financial reconciliation drift by 0\.001; synthesized dedicated Verifier node/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/verifier_tolerance_guard \(Node 04\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/VERIFICATION_MISS/i).length).toBeGreaterThanOrEqual(1);

    // Lesson 03
    expect(screen.getByText("Lesson 03")).toBeInTheDocument();
    expect(
      screen.getByText(/Parameter 'record_id' must be integer, not string; injected schema validator/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/schema_validator \(Node 03\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/TOOL_PARAMETER_ERROR/i).length).toBeGreaterThanOrEqual(1);
  });

  it("filters lessons by generation tab", () => {
    render(<EpistemicMemoryLedger />);

    const v0ToV1Tab = screen.getByRole("button", { name: /V0 to V1/i });
    fireEvent.click(v0ToV1Tab);

    // Only Lesson 01 should remain
    expect(screen.getByText("Lesson 01")).toBeInTheDocument();
    expect(screen.queryByText("Lesson 02")).not.toBeInTheDocument();
    expect(screen.queryByText("Lesson 03")).not.toBeInTheDocument();

    const v1ToV2Tab = screen.getByRole("button", { name: /V1 to V2/i });
    fireEvent.click(v1ToV2Tab);

    // Lessons 02 & 03 should now appear
    expect(screen.queryByText("Lesson 01")).not.toBeInTheDocument();
    expect(screen.getByText("Lesson 02")).toBeInTheDocument();
    expect(screen.getByText("Lesson 03")).toBeInTheDocument();
  });

  it("toggles code inspection diff preview", () => {
    render(<EpistemicMemoryLedger defaultExpanded={false} />);

    // Initially collapsed
    expect(screen.queryByText(/Synthesized Architectural Invariant/i)).not.toBeInTheDocument();

    // Expand Lesson 01
    const inspectButtons = screen.getAllByRole("button", { name: /Inspect Invariant/i });
    fireEvent.click(inspectButtons[0]);

    expect(screen.getByText(/Synthesized Architectural Invariant/i)).toBeInTheDocument();
    expect(screen.getByText(/normalizeTimestamp/i)).toBeInTheDocument();
  });
});
