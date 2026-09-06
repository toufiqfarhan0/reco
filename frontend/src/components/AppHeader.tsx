import { useState, useRef, useEffect } from 'react';
import type { StageType, DomainType } from '@/lib/types';
import {
  Hammer,
  Play,
  MagnifyingGlass,
  GitBranch,
  CheckCircle,
  Crown,
  CaretDown,
  List,
  X,
} from '@phosphor-icons/react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AppHeaderProps {
  currentStage: StageType;
  onSelectStage: (stage: StageType) => void;
  domain: DomainType;
  onChangeDomain: (domain: DomainType) => void;
  tier: 'free' | 'pro';
  onOpenBilling: () => void;
  onGoToLanding: () => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DOMAIN_LABELS: Record<DomainType, string> = {
  financial_reconciliation: 'Financial Reconciliation',
  anomaly_detection: 'Anomaly Detection',
  research_comparison: 'Research Comparison',
  cybersecurity_triage: 'Cybersecurity Incident Triage',
  biomedical_literature: 'Biomedical Literature',
  devops_root_cause: 'DevOps Diagnostics',
};

const DOMAIN_OPTIONS: DomainType[] = [
  'financial_reconciliation',
  'anomaly_detection',
  'research_comparison',
  'cybersecurity_triage',
  'biomedical_literature',
  'devops_root_cause',
];

interface StageConfig {
  key: StageType;
  label: string;
  Icon: React.ElementType;
}

const STAGE_CONFIGS: StageConfig[] = [
  { key: 'BUILD', label: 'Build', Icon: Hammer },
  { key: 'RUN', label: 'Run', Icon: Play },
  { key: 'UNDERSTAND', label: 'Understand', Icon: MagnifyingGlass },
  { key: 'IMPROVE', label: 'Improve', Icon: GitBranch },
  { key: 'VALIDATE', label: 'Validate', Icon: CheckCircle },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Dropdown for selecting the active domain. */
function DomainSelector({
  domain,
  onChangeDomain,
}: {
  domain: DomainType;
  onChangeDomain: (d: DomainType) => void;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  function handleSelect(d: DomainType) {
    onChangeDomain(d);
    setOpen(false);
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-md text-sm font-medium text-[#0a0a0a] hover:bg-[#f4f4f3] transition-colors focus:outline-none"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="max-w-[160px] truncate">{DOMAIN_LABELS[domain]}</span>
        <CaretDown
          size={14}
          weight="bold"
          className={`text-[#8a8a88] flex-shrink-0 transition-transform duration-150 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute left-0 top-full mt-1 z-50 w-56 rounded-lg border border-[#e4e4e3] bg-white shadow-md py-1"
        >
          {DOMAIN_OPTIONS.map((d) => (
            <button
              key={d}
              role="option"
              aria-selected={d === domain}
              onClick={() => handleSelect(d)}
              className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                d === domain
                  ? 'bg-[#f4f4f3] text-[#0a0a0a] font-medium'
                  : 'text-[#525250] hover:bg-[#f4f4f3] hover:text-[#0a0a0a]'
              }`}
            >
              {DOMAIN_LABELS[d]}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** A single stage navigation tab. */
function StageTab({
  config,
  isActive,
  onClick,
}: {
  config: StageConfig;
  isActive: boolean;
  onClick: () => void;
}) {
  const { label, Icon } = config;

  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md text-sm flex items-center gap-1.5 cursor-pointer transition-colors focus:outline-none whitespace-nowrap ${
        isActive
          ? 'bg-[#f4f4f3] text-[#0a0a0a] font-medium'
          : 'text-[#525250] hover:text-[#0a0a0a] hover:bg-[#f4f4f3]'
      }`}
      aria-current={isActive ? 'page' : undefined}
    >
      <Icon size={15} weight={isActive ? 'bold' : 'regular'} />
      <span>{label}</span>
    </button>
  );
}

/** Mobile drawer that lists all stage tabs inline below the header bar. */
function MobileStageMenu({
  currentStage,
  onSelectStage,
  onClose,
}: {
  currentStage: StageType;
  onSelectStage: (s: StageType) => void;
  onClose: () => void;
}) {
  return (
    <div className="lg:hidden border-t border-[#e4e4e3] bg-white px-4 py-2 flex flex-col gap-0.5">
      {STAGE_CONFIGS.map((cfg) => (
        <button
          key={cfg.key}
          onClick={() => {
            onSelectStage(cfg.key);
            onClose();
          }}
          className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors w-full text-left ${
            cfg.key === currentStage
              ? 'bg-[#f4f4f3] text-[#0a0a0a] font-medium'
              : 'text-[#525250] hover:bg-[#f4f4f3] hover:text-[#0a0a0a]'
          }`}
        >
          <cfg.Icon size={15} weight={cfg.key === currentStage ? 'bold' : 'regular'} />
          {cfg.label}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AppHeader({
  currentStage,
  onSelectStage,
  domain,
  onChangeDomain,
  tier,
  onOpenBilling,
  onGoToLanding,
}: AppHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Fixed top bar */}
      <header className="fixed top-0 inset-x-0 z-50 h-14 bg-white border-b border-[#e4e4e3]">
        <div className="flex items-center h-full px-4 gap-3">

          {/* LEFT ZONE */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={onGoToLanding}
              className="font-semibold text-[#0a0a0a] text-sm leading-none hover:opacity-70 transition-opacity focus:outline-none"
              aria-label="Go to landing page"
            >
              Reco
            </button>

            <span className="text-[#d1d1cf] text-sm select-none" aria-hidden="true">
              /
            </span>

            <DomainSelector domain={domain} onChangeDomain={onChangeDomain} />
          </div>

          {/* CENTER ZONE - desktop only */}
          <nav
            className="hidden lg:flex items-center gap-0.5 flex-1 justify-center"
            aria-label="Stage navigation"
          >
            {STAGE_CONFIGS.map((cfg) => (
              <StageTab
                key={cfg.key}
                config={cfg}
                isActive={cfg.key === currentStage}
                onClick={() => onSelectStage(cfg.key)}
              />
            ))}
          </nav>

          {/* Spacer on mobile to push right zone to the edge */}
          <div className="flex-1 lg:hidden" aria-hidden="true" />

          {/* RIGHT ZONE */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Tier badge */}
            {tier === 'pro' ? (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[#0a0a0a] text-white select-none">
                Pro
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[#f4f4f3] text-[#525250] select-none">
                Free
              </span>
            )}

            {/* Upgrade button - free tier, hidden on smallest screens */}
            {tier === 'free' && (
              <button
                onClick={onOpenBilling}
                className="hidden sm:flex items-center gap-1 text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors focus:outline-none"
                aria-label="Upgrade plan"
              >
                <Crown size={14} weight="regular" />
                <span>Upgrade</span>
              </button>
            )}

            {/* Mobile hamburger */}
            <button
              className="lg:hidden flex items-center justify-center p-1.5 rounded-md text-[#525250] hover:text-[#0a0a0a] hover:bg-[#f4f4f3] transition-colors focus:outline-none"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X size={18} /> : <List size={18} />}
            </button>
          </div>
        </div>

        {/* Mobile stage menu - expands below the bar */}
        {mobileMenuOpen && (
          <MobileStageMenu
            currentStage={currentStage}
            onSelectStage={onSelectStage}
            onClose={() => setMobileMenuOpen(false)}
          />
        )}
      </header>

      {/* Page content spacer to clear fixed header */}
      <div className="h-14" aria-hidden="true" />
    </>
  );
}
