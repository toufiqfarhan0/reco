"use client";

import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { motion } from "motion/react";
import { StageType } from "@/lib/types";
import { HeroLandingView } from "@/components/HeroLandingView";
import { BillingModal } from "@/components/BillingModal";
import { GithubLogo, Terminal, ArrowUpRight } from "@phosphor-icons/react";

const STAGE_MAP: Record<StageType, number> = {
  BUILD: 1,
  RUN: 2,
  UNDERSTAND: 3,
  IMPROVE: 4,
  VALIDATE: 5,
};

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isBillingOpen, setIsBillingOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const checkout = searchParams.get("checkout");
    const status = searchParams.get("status");
    if (checkout || status) {
      navigate(`/console?${searchParams.toString()}`, { replace: true });
    }
  }, [searchParams, navigate]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleLaunchConsole = () => navigate("/console");
  const handleExploreLineage = () => navigate("/console?stage=4&preset=financial_reconciliation");
  const handleSelectStage = (stage: StageType) => {
    navigate(`/console?stage=${STAGE_MAP[stage] || 1}`);
  };

  return (
    <div className="min-h-screen bg-[#f8f8f7] flex flex-col font-sans selection:bg-indigo-100 selection:text-indigo-700">

      {/* ── NAVBAR ── */}
      <motion.nav
        initial={{ y: -16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className={`sticky top-0 z-50 h-14 bg-white/95 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between transition-shadow duration-300 ${
          scrolled ? "shadow-md border-b border-zinc-200" : "border-b border-zinc-100"
        }`}
      >
        {/* Left: Brand + Track badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white border border-zinc-200 shadow-xs overflow-hidden shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="22" height="22" fill="none" aria-label="Reco Logomark">
                <path fill="#4F46E5" fillRule="evenodd" clipRule="evenodd" d="M4 4H24V15H17.2L25.5 28H18L10.5 16.5V28H4V4ZM10.5 8.5V12H18V8.5H10.5Z" />
              </svg>
            </div>
            <span className="font-geist font-bold text-zinc-900 text-lg leading-none">Reco</span>
          </div>

          <div className="h-4 w-px bg-zinc-200 hidden sm:block" />

          <div className="hidden sm:flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-600" />
            </span>
            <span className="rounded-md bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-mono font-semibold text-indigo-700">
              Track 1 · Automated Agent Engineering
            </span>
          </div>
        </div>

        {/* Right: Nav + GitHub + CTA */}
        <div className="flex items-center gap-4">
          <nav className="hidden sm:flex items-center gap-5 text-xs font-medium text-zinc-600 font-geist">
            <Link to="/why-reco" className="text-indigo-600 hover:text-indigo-700 font-semibold transition-colors">
              Why Reco?
            </Link>
            <Link to="/architecture" className="hover:text-zinc-900 transition-colors">
              Architecture
            </Link>
            <a href="#how-it-works" className="hover:text-zinc-900 transition-colors">How it works</a>
            <a href="#pricing" className="hover:text-zinc-900 transition-colors">Pricing</a>
          </nav>

          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center h-8 w-8 rounded-lg border border-zinc-200 bg-white text-zinc-600 hover:text-zinc-900 hover:bg-zinc-50 transition shadow-xs"
            title="View on GitHub"
            aria-label="View on GitHub"
          >
            <GithubLogo size={17} weight="bold" />
          </a>

          <motion.button
            type="button"
            onClick={handleLaunchConsole}
            whileHover={{ scale: 1.04, boxShadow: "0 4px 16px rgba(79,70,229,0.28)" }}
            whileTap={{ scale: 0.96 }}
            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 text-xs font-semibold shadow-xs transition cursor-pointer font-geist"
          >
            <Terminal size={15} weight="bold" />
            <span>Launch Console</span>
          </motion.button>
        </div>
      </motion.nav>

      {/* ── MAIN ── */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <HeroLandingView
          onLaunchConsole={handleLaunchConsole}
          onExploreLineage={handleExploreLineage}
          onSelectStage={handleSelectStage}
          onOpenBilling={() => setIsBillingOpen(true)}
        />
      </main>

      {/* ── FOOTER ── */}
      <footer className="w-full border-t border-zinc-200 bg-white">
        {/* Top footer */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
            {/* Brand column */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white border border-zinc-200 shadow-xs overflow-hidden">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="18" height="18" fill="none">
                    <path fill="#4F46E5" fillRule="evenodd" clipRule="evenodd" d="M4 4H24V15H17.2L25.5 28H18L10.5 16.5V28H4V4ZM10.5 8.5V12H18V8.5H10.5Z" />
                  </svg>
                </div>
                <span className="font-bold text-zinc-900 font-geist">Reco</span>
              </div>
              <p className="text-xs text-zinc-500 font-geist leading-relaxed max-w-[200px]">
                Autonomous Agent Engineering System. Build agents that actually improve themselves.
              </p>
              <p className="text-[10px] font-mono text-zinc-400">
                Built for Syndicate by Maximor Hackathon
              </p>
            </div>

            {/* Nav column */}
            <div className="space-y-3">
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400">Navigation</p>
              <ul className="space-y-2">
                {[
                  { label: "Why Reco?", to: "/why-reco", internal: true },
                  { label: "Architecture", to: "/architecture", internal: true },
                  { label: "How it works", to: "#how-it-works", internal: false },
                  { label: "Pricing", to: "#pricing", internal: false },
                ].map((link) => (
                  <li key={link.label}>
                    {link.internal ? (
                      <Link to={link.to} className="text-xs text-zinc-600 hover:text-indigo-600 transition-colors font-geist">
                        {link.label}
                      </Link>
                    ) : (
                      <a href={link.to} className="text-xs text-zinc-600 hover:text-indigo-600 transition-colors font-geist">
                        {link.label}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            {/* Links column */}
            <div className="space-y-3">
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400">Links</p>
              <ul className="space-y-2">
                <li>
                  <a
                    href="https://github.com/toufiqfarhan0/reco"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-zinc-600 hover:text-indigo-600 transition-colors font-geist"
                  >
                    GitHub <ArrowUpRight size={11} />
                  </a>
                </li>
                <li>
                  <a
                    href="https://aoagents.dev/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-zinc-600 hover:text-indigo-600 transition-colors font-geist"
                  >
                    AO Agents <ArrowUpRight size={11} />
                  </a>
                </li>
                <li>
                  <a
                    href="https://maximor.ai/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-zinc-600 hover:text-indigo-600 transition-colors font-geist"
                  >
                    Maximor <ArrowUpRight size={11} />
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-zinc-100 py-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
            <p className="text-[11px] font-mono text-zinc-400">© 2026 Reco · Autonomous Agent Engineering System</p>
            <p className="text-[11px] font-mono text-zinc-400">
              Syndicate by Maximor · Track 1: Automated Agent Engineering
            </p>
          </div>
        </div>
      </footer>

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
