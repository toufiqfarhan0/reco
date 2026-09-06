import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Header } from "@/components/Header";

describe("Header Component", () => {
  it("renders brand title, Track 1 badge, view mode switch, and all 5 stages", () => {
    const onSelectStage = vi.fn();
    const onChangeDomain = vi.fn();
    const onToggleMode = vi.fn();

    render(
      <Header
        currentStage="BUILD"
        onSelectStage={onSelectStage}
        domain="financial_reconciliation"
        onChangeDomain={onChangeDomain}
        mode="demo"
        onToggleMode={onToggleMode}
      />
    );

    expect(screen.getByText(/Autonomous Agent Visual Engineering Console/i)).toBeInTheDocument();
    expect(screen.getByText(/Track 1/i)).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Overview/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Console/i })).toBeInTheDocument();
    expect(screen.getByText(/BUILD/i)).toBeInTheDocument();
    expect(screen.getByText(/RUN/i)).toBeInTheDocument();
    expect(screen.getByText(/UNDERSTAND/i)).toBeInTheDocument();
    expect(screen.getByText(/IMPROVE/i)).toBeInTheDocument();
    expect(screen.getByText(/VALIDATE/i)).toBeInTheDocument();
  });

  it("toggles between Demo Mode and Live Mode", () => {
    const onToggleMode = vi.fn();

    render(
      <Header
        currentStage="BUILD"
        onSelectStage={vi.fn()}
        domain="financial_reconciliation"
        onChangeDomain={vi.fn()}
        mode="demo"
        onToggleMode={onToggleMode}
      />
    );

    const liveBtn = screen.getByRole("radio", { name: /Live Mode/i });
    fireEvent.click(liveBtn);
    expect(onToggleMode).toHaveBeenCalledWith("live");
  });

  it("toggles between Overview and Console view mode", () => {
    const onToggleViewMode = vi.fn();

    render(
      <Header
        currentStage="BUILD"
        onSelectStage={vi.fn()}
        domain="financial_reconciliation"
        onChangeDomain={vi.fn()}
        mode="demo"
        onToggleMode={vi.fn()}
        viewMode="overview"
        onToggleViewMode={onToggleViewMode}
      />
    );

    const consoleBtn = screen.getByRole("tab", { name: /Console/i });
    fireEvent.click(consoleBtn);
    expect(onToggleViewMode).toHaveBeenCalledWith("console");
  });

  it("handles domain selection changes", () => {
    const onChangeDomain = vi.fn();

    render(
      <Header
        currentStage="BUILD"
        onSelectStage={vi.fn()}
        domain="financial_reconciliation"
        onChangeDomain={onChangeDomain}
        mode="demo"
        onToggleMode={vi.fn()}
      />
    );

    const select = screen.getByLabelText(/Select Domain/i);
    fireEvent.change(select, { target: { value: "anomaly_detection" } });
    expect(onChangeDomain).toHaveBeenCalledWith("anomaly_detection");
  });
});
