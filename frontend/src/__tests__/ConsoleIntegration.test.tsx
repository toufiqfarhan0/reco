import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import EngineeringConsolePage from "@/app/page";

describe("Console Integration: 5-Stage Engineering Navigator", () => {
  it("navigates across all 5 stages from BUILD to VALIDATE", () => {
    render(<EngineeringConsolePage />);

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

    // Navigate to Stage 4: IMPROVE
    const improveNav = screen.getByRole("button", { name: /Improve 04/i });
    fireEvent.click(improveNav);
    expect(screen.getByText(/IMPROVE: Multi-Candidate Tournament/i)).toBeInTheDocument();

    // Navigate to Stage 5: VALIDATE
    const validateNav = screen.getByRole("button", { name: /Validate 05/i });
    fireEvent.click(validateNav);
    expect(screen.getByText(/VALIDATE: Air-Gapped Held-Out Generalization/i)).toBeInTheDocument();
    expect(screen.getByText(/FORMAL PROMOTION DECISION/i)).toBeInTheDocument();
  });
});
