import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { HeroLandingView } from "@/components/HeroLandingView";

describe("HeroLandingView Component", () => {
  it("renders headline, top track badge, and subheadline", () => {
    const onLaunchConsole = vi.fn();
    const onExploreLineage = vi.fn();

    render(
      <MemoryRouter>
        <HeroLandingView
          onLaunchConsole={onLaunchConsole}
          onExploreLineage={onExploreLineage}
        />
      </MemoryRouter>
    );

    // Track 1 top badge
    expect(
      screen.getByText(/TRACK 1: AUTOMATED AGENT ENGINEERING • SYNDICATE BY MAXIMOR/i)
    ).toBeInTheDocument();

    // Headline
    expect(
      screen.getByRole("heading", { name: /Autonomous Agent Engineering System/i })
    ).toBeInTheDocument();

    // Subheadline
    expect(
      screen.getByText(/From high-level natural language goals to self-improving/i)
    ).toBeInTheDocument();
  });

  it("renders all 4 live production tech stack badges", () => {
    render(
      <MemoryRouter>
        <HeroLandingView
          onLaunchConsole={vi.fn()}
          onExploreLineage={vi.fn()}
        />
      </MemoryRouter>
    );

    expect(screen.getByText(/Inference:/i)).toBeInTheDocument();
    expect(screen.getByText(/TensorMux/i)).toBeInTheDocument();
    expect(screen.getByText(/GLM-4.7-Flash/i)).toBeInTheDocument();

    expect(screen.getByText(/Observability:/i)).toBeInTheDocument();
    expect(screen.getByText(/Neatlogs/i)).toBeInTheDocument();

    expect(screen.getByText(/Persistence:/i)).toBeInTheDocument();
    expect(screen.getByText(/Supabase/i)).toBeInTheDocument();

    expect(screen.getByText(/Monetization:/i)).toBeInTheDocument();
    expect(screen.getByText(/Dodo Payments/i)).toBeInTheDocument();
  });

  it("renders all 5 pipeline stage steps and animates the execution cycle", () => {
    render(
      <MemoryRouter>
        <HeroLandingView
          onLaunchConsole={vi.fn()}
          onExploreLineage={vi.fn()}
        />
      </MemoryRouter>
    );

    expect(screen.getByText(/01/)).toBeInTheDocument();
    expect(screen.getByText(/Goal deconstruction & initial DAG synthesis/i)).toBeInTheDocument();

    expect(screen.getByText(/02/)).toBeInTheDocument();
    expect(screen.getByText(/Deterministic execution & 4-axis scorecard/i)).toBeInTheDocument();

    expect(screen.getByText(/03/)).toBeInTheDocument();
    expect(screen.getByText(/12-category diagnostic root cause analysis/i)).toBeInTheDocument();

    expect(screen.getByText(/04/)).toBeInTheDocument();
    expect(screen.getByText(/Self-reflection, mutation tournament & Pareto frontier/i)).toBeInTheDocument();

    expect(screen.getByText(/05/)).toBeInTheDocument();
    expect(screen.getByText(/Air-gapped held-out promotion gate/i)).toBeInTheDocument();

    // Verify autonomous pipeline cycle indicator is rendered
    expect(screen.getByText(/Autonomous Pipeline Cycle:/i)).toBeInTheDocument();
  });

  it("fires action button triggers", () => {
    const onLaunchConsole = vi.fn();
    const onExploreLineage = vi.fn();

    render(
      <MemoryRouter>
        <HeroLandingView
          onLaunchConsole={onLaunchConsole}
          onExploreLineage={onExploreLineage}
        />
      </MemoryRouter>
    );

    const launchBtn = screen.getByRole("button", { name: /Launch Interactive Console/i });
    fireEvent.click(launchBtn);
    expect(onLaunchConsole).toHaveBeenCalledTimes(1);

    const lineageBtn = screen.getByRole("button", { name: /Explore Evolution Lineage/i });
    fireEvent.click(lineageBtn);
    expect(onExploreLineage).toHaveBeenCalledTimes(1);
  });
});
