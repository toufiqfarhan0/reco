import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { AuthModal } from "@/components/AuthModal";
import { MyExperimentsModal } from "@/components/MyExperimentsModal";
import { Header } from "@/components/Header";

describe("Supabase Integration: AuthModal, MyExperimentsModal & Header User Controls", () => {
  it("renders Header in unauthenticated state with Sign In button", () => {
    const onOpenAuth = vi.fn();
    render(
      <Header
        mode="demo"
        user={null}
        onOpenAuth={onOpenAuth}
      />
    );

    const signInBtn = screen.getByTestId("open-auth-modal-button");
    expect(signInBtn).toBeInTheDocument();
    expect(signInBtn).toHaveTextContent(/sign in/i);

    fireEvent.click(signInBtn);
    expect(onOpenAuth).toHaveBeenCalledTimes(1);
  });

  it("renders Header in authenticated state with user badge, My Experiments button, and Sign Out button", () => {
    const onOpenExperiments = vi.fn();
    const onSignOut = vi.fn();
    const mockUser = {
      id: "usr_mock_123",
      email: "engineer@example.com",
      user_metadata: {
        display_name: "Lead Engineer",
      },
    };

    render(
      <Header
        mode="live"
        user={mockUser}
        onOpenExperiments={onOpenExperiments}
        onSignOut={onSignOut}
      />
    );

    expect(screen.getByText("Lead Engineer")).toBeInTheDocument();

    const myExpBtn = screen.getByTestId("open-my-experiments-button");
    expect(myExpBtn).toBeInTheDocument();
    fireEvent.click(myExpBtn);
    expect(onOpenExperiments).toHaveBeenCalledTimes(1);

    const signOutBtn = screen.getByTestId("sign-out-button");
    expect(signOutBtn).toBeInTheDocument();
    fireEvent.click(signOutBtn);
    expect(onSignOut).toHaveBeenCalledTimes(1);
  });

  it("renders AuthModal when open and toggles between Sign In and Sign Up", () => {
    const onClose = vi.fn();
    const onAuthSuccess = vi.fn();

    const { rerender } = render(
      <AuthModal
        isOpen={false}
        onClose={onClose}
        onAuthSuccess={onAuthSuccess}
      />
    );

    // Closed modal should not render
    expect(screen.queryByText(/sign in to reco/i)).not.toBeInTheDocument();

    // Open modal
    rerender(
      <AuthModal
        isOpen={true}
        onClose={onClose}
        onAuthSuccess={onAuthSuccess}
      />
    );

    expect(screen.getByText(/sign in to reco/i)).toBeInTheDocument();
    expect(screen.getByTestId("auth-email-input")).toBeInTheDocument();
    expect(screen.getByTestId("auth-password-input")).toBeInTheDocument();
    expect(screen.getByTestId("auth-evaluator-signin")).toBeInTheDocument();

    // Toggle to Sign Up
    const toggleBtn = screen.getByTestId("auth-toggle-mode");
    fireEvent.click(toggleBtn);

    expect(screen.getByText(/create engineer account/i)).toBeInTheDocument();
    expect(screen.getByTestId("auth-displayname-input")).toBeInTheDocument();
  });

  it("activates 1-click Judge / Evaluator Demo Sign In and invokes onAuthSuccess", () => {
    const onClose = vi.fn();
    const onAuthSuccess = vi.fn();

    render(
      <AuthModal
        isOpen={true}
        onClose={onClose}
        onAuthSuccess={onAuthSuccess}
      />
    );

    const demoBtn = screen.getByTestId("auth-evaluator-signin");
    expect(demoBtn).toBeInTheDocument();
    fireEvent.click(demoBtn);

    expect(onAuthSuccess).toHaveBeenCalledTimes(1);
    const [userArg, tokenArg] = onAuthSuccess.mock.calls[0];
    expect(userArg.email).toBe("judge@reco.ai");
    expect(tokenArg).toBeTruthy();
  });

  it("renders MyExperimentsModal when open with persisted experiments", () => {
    const onClose = vi.fn();
    const onLoadExperiment = vi.fn();

    render(
      <MyExperimentsModal
        isOpen={true}
        onClose={onClose}
        token="mock_token"
        onLoadExperiment={onLoadExperiment}
      />
    );

    expect(screen.getByTestId("my-experiments-modal")).toBeInTheDocument();
    expect(screen.getByText(/my persisted experiments/i)).toBeInTheDocument();
  });
});
