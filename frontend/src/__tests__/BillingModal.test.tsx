import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { BillingModal } from "@/components/BillingModal";

describe("BillingModal Component", () => {
  const originalFetch = global.fetch;
  const originalOpen = window.open;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    window.open = originalOpen;
  });

  it("does not render when isOpen is false", () => {
    render(<BillingModal isOpen={false} onClose={vi.fn()} />);
    expect(screen.queryByText(/Dodo Payments Monetization & Tiers/i)).not.toBeInTheDocument();
  });

  it("renders 2 tiers with high contrast and required features", () => {
    render(<BillingModal isOpen={true} onClose={vi.fn()} currentTier="free" />);

    // Title and Track 1 badge
    expect(screen.getByText(/Dodo Payments Monetization & Tiers/i)).toBeInTheDocument();
    expect(screen.getByText(/Track 1/i)).toBeInTheDocument();

    // Free Tier checks
    expect(screen.getByText(/Free Tier/i)).toBeInTheDocument();
    expect(screen.getByText(/5 daily optimizations/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Local in-memory storage/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Community support/i)).toBeInTheDocument();

    // Pro Tier checks
    expect(screen.getByText(/Pro Tier/i)).toBeInTheDocument();
    expect(screen.getAllByText(/\$29/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Unlimited autonomous mutations/i)).toBeInTheDocument();
    expect(screen.getByText(/Full Supabase cloud lineage sync/i)).toBeInTheDocument();
    expect(screen.getByText(/Neatlogs distributed trace export/i)).toBeInTheDocument();
    expect(screen.getByText(/Priority inference/i)).toBeInTheDocument();
  });

  it("displays visible TEST MODE pill with simulated card credentials for judges", () => {
    render(<BillingModal isOpen={true} onClose={vi.fn()} />);

    expect(screen.getByText(/TEST MODE ACTIVE/i)).toBeInTheDocument();
    expect(screen.getByText(/Judges & Evaluators Sandbox/i)).toBeInTheDocument();
    expect(screen.getByText(/4242 4242 4242 4242/i)).toBeInTheDocument();
    expect(screen.getByText(/12\/28/i)).toBeInTheDocument();
    expect(screen.getByText(/123/i)).toBeInTheDocument();
    expect(screen.getByText(/90210/i)).toBeInTheDocument();
  });

  it("sends POST to /billing/checkout when Upgrade to Pro is clicked and opens checkout_url", async () => {
    const mockCheckoutUrl = "https://test.dodopayments.com/checkout/cs_test_abc123";
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: "cs_test_abc123",
        checkout_url: mockCheckoutUrl,
        user_id: "usr_demo",
        product_id: "prod_pro_monthly",
      }),
    });

    const windowOpenSpy = vi.fn();
    window.open = windowOpenSpy;
    const onTierChange = vi.fn();

    render(
      <BillingModal
        isOpen={true}
        onClose={vi.fn()}
        userId="usr_demo"
        onTierChange={onTierChange}
      />
    );

    const upgradeBtn = screen.getByRole("button", { name: /Upgrade to Pro/i });
    fireEvent.click(upgradeBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "usr_demo",
        }),
      });
    });

    await waitFor(() => {
      expect(windowOpenSpy).toHaveBeenCalledWith(
        mockCheckoutUrl,
        "_blank",
        "noopener,noreferrer"
      );
      expect(onTierChange).toHaveBeenCalledWith("pro");
    });
  });

  it("sends POST to /billing/portal when Manage Subscription is clicked and opens portal_url", async () => {
    const mockPortalUrl = "https://test.dodopayments.com/portal/cus_demo_usr_demo";
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        portal_url: mockPortalUrl,
        customer_id: "cus_demo_usr_demo",
      }),
    });

    const windowOpenSpy = vi.fn();
    window.open = windowOpenSpy;

    render(<BillingModal isOpen={true} onClose={vi.fn()} userId="usr_demo" />);

    const portalBtn = screen.getByRole("button", { name: /Manage Subscription/i });
    fireEvent.click(portalBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/billing/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "usr_demo",
        }),
      });
    });

    await waitFor(() => {
      expect(windowOpenSpy).toHaveBeenCalledWith(
        mockPortalUrl,
        "_blank",
        "noopener,noreferrer"
      );
    });
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    render(<BillingModal isOpen={true} onClose={onClose} />);

    const closeButtons = screen.getAllByRole("button", { name: /close/i });
    fireEvent.click(closeButtons[0]);
    expect(onClose).toHaveBeenCalled();
  });
});
