import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FailureExplorer } from "@/components/FailureExplorer";
import { FAILURE_DIAGNOSTICS } from "@/lib/mockData";

describe("Stage 3: FailureExplorer", () => {
  it("renders 12-category taxonomy classification and failure cases", () => {
    render(
      <FailureExplorer
        diagnostics={FAILURE_DIAGNOSTICS}
        onProceedToImprove={vi.fn()}
      />
    );

    expect(screen.getByText(/STAGE 03/i)).toBeInTheDocument();
    expect(screen.getByText(/12-Category Failure Diagnostics Taxonomy/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Observable Symptoms/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Isolated Root Cause/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Targeted Autonomous Remedy/i)[0]).toBeInTheDocument();
  });

  it("filters diagnostics by taxonomy category", () => {
    render(
      <FailureExplorer
        diagnostics={FAILURE_DIAGNOSTICS}
        onProceedToImprove={vi.fn()}
      />
    );

    const toolSelectionBtn = screen.getByRole("button", {
      name: /Tool Selection Error/i,
    });
    fireEvent.click(toolSelectionBtn);

    expect(screen.getAllByText("reco_opt_002_casing_mismatch")[0]).toBeInTheDocument();
  });

  it("navigates forward to Stage 4 on action click", () => {
    const onProceedToImprove = vi.fn();
    render(
      <FailureExplorer
        diagnostics={FAILURE_DIAGNOSTICS}
        onProceedToImprove={onProceedToImprove}
      />
    );

    const button = screen.getByRole("button", {
      name: /Synthesize Mutations/i,
    });
    fireEvent.click(button);
    expect(onProceedToImprove).toHaveBeenCalled();
  });
});
