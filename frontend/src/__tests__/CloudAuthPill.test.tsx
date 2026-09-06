import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CloudAuthPill } from "@/components/CloudAuthPill";

describe("CloudAuthPill Component", () => {
  it("renders FREE TIER (LOCAL) by default with cloud sync indicator", () => {
    render(<CloudAuthPill tier="free" isCloudConnected={true} />);

    expect(screen.getByText(/FREE TIER \(LOCAL\)/i)).toBeInTheDocument();
  });

  it("renders PRO TIER (ACTIVE) when tier is pro", () => {
    render(<CloudAuthPill tier="pro" isCloudConnected={true} />);

    expect(screen.getByText(/PRO TIER \(ACTIVE\)/i)).toBeInTheDocument();
  });

  it("opens quick session drawer upon click showing anonymous session ID and token status", () => {
    const onOpenBilling = vi.fn();
    const onToggleTier = vi.fn();

    render(
      <CloudAuthPill
        tier="free"
        isCloudConnected={true}
        sessionId="usr_demo_anon_test_99"
        tokenStatus="GoTrue JWT: Valid"
        onOpenBilling={onOpenBilling}
        onToggleTier={onToggleTier}
      />
    );

    // Initial state: drawer not visible
    expect(screen.queryByText(/Supabase Cloud Session/i)).not.toBeInTheDocument();

    // Click pill to open drawer
    const pill = screen.getByRole("button", { name: /Cloud Session Status and Entitlements/i });
    fireEvent.click(pill);

    // Drawer is now open
    expect(screen.getByText(/Supabase Cloud Session/i)).toBeInTheDocument();
    expect(screen.getByText(/usr_demo_anon_test_99/i)).toBeInTheDocument();
    expect(screen.getByText(/GoTrue JWT: Valid/i)).toBeInTheDocument();
    expect(screen.getByText(/reco\/db\/supabase\.py/i)).toBeInTheDocument();
    expect(screen.getByText(/PostgreSQL RLS & Entitlements/i)).toBeInTheDocument();

    // Test action triggers in drawer
    const switchTierBtn = screen.getByRole("button", { name: /Switch to Pro/i });
    fireEvent.click(switchTierBtn);
    expect(onToggleTier).toHaveBeenCalledWith("pro");

    const billingBtn = screen.getByRole("button", { name: /Upgrade to Pro/i });
    fireEvent.click(billingBtn);
    expect(onOpenBilling).toHaveBeenCalled();

    // Clicking billing button closed the drawer
    expect(screen.queryByText(/Supabase Cloud Session/i)).not.toBeInTheDocument();
  });
});
