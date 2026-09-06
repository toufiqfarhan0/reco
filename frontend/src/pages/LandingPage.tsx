"use client";

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { StageType } from "@/lib/types";
import { HeroLandingView } from "@/components/HeroLandingView";
import { BillingModal } from "@/components/BillingModal";
import { GithubLogo, Terminal } from "@phosphor-icons/react";

const STAGE_MAP: Record<StageType, number> = {
  BUILD: 1,
  RUN: 2,
  UNDERSTAND: 3,
  IMPROVE: 4,
  VALIDATE: 5,
};

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [isBillingOpen, setIsBillingOpen] = useState(false);

  const handleLaunchConsole = () => {
    navigate("/console");
  };

  const handleExploreLineage = () => {
    navigate("/console?stage=4&preset=financial_reconciliation");
  };

  const handleSelectStage = (stage: StageType) => {
    const stageNum = STAGE_MAP[stage] || 1;
    navigate(`/console?stage=${stageNum}`);
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
      {/* Standalone Slim Top Navbar */}
      <nav className="sticky top-0 z-50 h-14 bg-white/95 backdrop-blur-sm border-b border-zinc-200 px-4 sm:px-6 lg:px-8 flex items-center justify-between shadow-2xs">
        {/* Left: Brand + Track 1 Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white border border-zinc-200 shadow-xs overflow-hidden shrink-0">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 32 32"
                width="22"
                height="22"
                fill="none"
                aria-label="Reco Logomark"
              >
                <path
                  fill="#4F46E5"
                  fillRule="evenodd"
                  clipRule="evenodd"
                  d="M4 4H24V15H17.2L25.5 28H18L10.5 16.5V28H4V4ZM10.5 8.5V12H18V8.5H10.5Z"
                />
              </svg>
            </div>
            <span className="font-geist font-bold text-zinc-900 text-lg leading-none">
              Reco
            </span>
          </div>

          <div className="h-4 w-px bg-zinc-200 hidden sm:block" />

          <div className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-indigo-600" />
            <span className="text-xs font-mono font-medium text-zinc-700 hidden sm:inline">
              Track 1
            </span>
            <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-mono font-medium text-indigo-700">
              Automated Agent Engineering
            </span>
          </div>
        </div>

        {/* Right: Anchors + GitHub + Launch Console CTA */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-5 text-xs font-medium text-zinc-600 font-geist">
            <a
              href="#how-it-works"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              How it works
            </a>
            <a
              href="#pricing"
              className="hover:text-zinc-900 transition-colors cursor-pointer"
            >
              Pricing
            </a>
          </div>

          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center h-8 w-8 rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors shadow-2xs"
            title="View on GitHub"
            aria-label="View on GitHub"
          >
            <GithubLogo size={17} weight="bold" />
          </a>

          <button
            type="button"
            onClick={handleLaunchConsole}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white px-4 py-2 text-xs font-semibold shadow-xs transition-all cursor-pointer font-geist"
          >
            <Terminal size={15} weight="bold" />
            <span>Launch Console</span>
          </button>
        </div>
      </nav>

      {/* Main Full-Width Centered Landing View */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <HeroLandingView
          onLaunchConsole={handleLaunchConsole}
          onExploreLineage={handleExploreLineage}
          onSelectStage={handleSelectStage}
          onOpenBilling={() => setIsBillingOpen(true)}
        />
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-zinc-200 bg-white py-6 text-center text-xs font-mono text-zinc-500">
        <p>Reco • Autonomous Agent Engineering System</p>
      </footer>

      {/* Dodo Payments Hosted Billing Modal */}
      <BillingModal
        isOpen={isBillingOpen}
        onClose={() => setIsBillingOpen(false)}
        onOpenAuth={() => {
          setIsBillingOpen(false);
          navigate("/console");
        }}
      />
    </div>
  );
};

export default LandingPage;
