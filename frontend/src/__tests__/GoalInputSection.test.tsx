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

  it("renders a blank canvas on initial load with domain='' (empty)", () => {
    const onSynthesize = vi.fn();
    const onProceedToRun = vi.fn();

    render(
      <GoalInputSection
        domain=""
        currentDag={INITIAL_DAG_V0}
        onSynthesize={onSynthesize}
        onProceedToRun={onProceedToRun}
      />
    );

    // Goal textarea starts empty with proper placeholder
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.value).toBe("");
    expect(textarea.placeholder).toContain("Describe your agent's goal in plain English");

    // Domain chips are hidden
    expect(screen.queryByText(/Domain Preset Chips/i)).not.toBeInTheDocument();

    // Tool catalog is hidden
    expect(screen.queryByText(/Active Tool Catalog & Capabilities/i)).not.toBeInTheDocument();

    // DAG Architecture shows empty state placeholder
    expect(screen.getByText("No architecture yet")).toBeInTheDocument();
    expect(screen.getByText(/Click 'Synthesize DAG Architecture' to generate your agent graph/i)).toBeInTheDocument();

    // Synthesize button is disabled
    const synthButton = screen.getByRole("button", {
      name: /Synthesize DAG Architecture/i,
    });
    expect(synthButton).toBeDisabled();

    // Budget inputs are empty with placeholder hints
    const latencyInput = screen.getByLabelText(/Latency Budget/i) as HTMLInputElement;
    const costInput = screen.getByLabelText(/Cost Budget/i) as HTMLInputElement;
    expect(latencyInput.value).toBe("");
    expect(latencyInput.placeholder).toBe("e.g. 5000");
    expect(costInput.value).toBe("");
    expect(costInput.placeholder).toBe("e.g. 0.05");
  });

  it("reveals tool catalog and enables synthesize button when user types >= 20 characters", () => {
    const onSynthesize = vi.fn();

    render(
      <GoalInputSection
        domain=""
        currentDag={INITIAL_DAG_V0}
        onSynthesize={onSynthesize}
        onProceedToRun={vi.fn()}
      />
    );

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    const synthButton = screen.getByRole("button", {
      name: /Synthesize DAG Architecture/i,
    });

    expect(synthButton).toBeDisabled();
    expect(screen.queryByText(/Active Tool Catalog & Capabilities/i)).not.toBeInTheDocument();

    // Type goal >= 20 chars
    fireEvent.change(textarea, {
      target: { value: "Reconcile daily payments against bank statements." },
    });

    expect(synthButton).not.toBeDisabled();
    expect(screen.getByText(/Active Tool Catalog & Capabilities/i)).toBeInTheDocument();

    // Clicking synthesize reveals DAG architecture nodes
    fireEvent.click(synthButton);
    expect(onSynthesize).toHaveBeenCalledWith("Reconcile daily payments against bank statements.");
    expect(screen.queryByText("No architecture yet")).not.toBeInTheDocument();
    expect(screen.getByText("Nodes")).toBeInTheDocument();
  });
});
