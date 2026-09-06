import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { GoalInputSection } from "@/components/GoalInputSection";
import { INITIAL_DAG_V0 } from "@/lib/mockData";

describe("Stage 1: GoalInputSection", () => {
  it("renders natural language goal input and active tool badges", () => {
    const onSynthesize = vi.fn();
    const onProceedToRun = vi.fn();

    render(
      <GoalInputSection
        domain="financial_reconciliation"
        currentDag={INITIAL_DAG_V0}
        onSynthesize={onSynthesize}
        onProceedToRun={onProceedToRun}
      />
    );

    expect(screen.getByText(/STAGE 01/i)).toBeInTheDocument();
    expect(screen.getByText(/BUILD: Natural Language Goal & DAG Synthesis/i)).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByText("exact_reconcile")).toBeInTheDocument();
    expect(screen.getByText("smart_reconcile")).toBeInTheDocument();
  });

  it("applies domain preset chips to goal input", () => {
    render(
      <GoalInputSection
        domain="financial_reconciliation"
        currentDag={INITIAL_DAG_V0}
        onSynthesize={vi.fn()}
        onProceedToRun={vi.fn()}
      />
    );

    const chip = screen.getByText(/\+ Stripe Gateway vs ERP Ledger/i);
    fireEvent.click(chip);

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.value).toContain("Stripe Gateway vs ERP Ledger");
  });

  it("fires synthesis trigger on button click", () => {
    const onSynthesize = vi.fn();

    render(
      <GoalInputSection
        domain="financial_reconciliation"
        currentDag={INITIAL_DAG_V0}
        onSynthesize={onSynthesize}
        onProceedToRun={vi.fn()}
      />
    );

    const button = screen.getByRole("button", {
      name: /Synthesize DAG Architecture/i,
    });
    fireEvent.click(button);
    expect(onSynthesize).toHaveBeenCalled();
  });
});
