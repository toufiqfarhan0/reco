import { useState } from 'react';
import { motion } from 'motion/react';
import {
  Hammer,
  Play,
  MagnifyingGlass,
  GitBranch,
  CheckCircle,
  ArrowRight,
  List,
  X as XIcon,
  Check,
  GithubLogo,
} from '@phosphor-icons/react';

interface LandingPageProps {
  onEnterConsole: () => void;
}

// ---------------------------------------------------------------------------
// Navbar
// ---------------------------------------------------------------------------
function Navbar({ onEnterConsole }: { onEnterConsole: () => void }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 bg-white/90 backdrop-blur-sm border-b border-[#e4e4e3]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
        <div className="flex items-center gap-2.5">
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
          <span className="font-semibold text-[#0a0a0a] text-lg leading-none font-geist">Reco</span>
          <span className="text-xs text-[#525250] hidden sm:inline font-geist">AI Agent Engineering</span>
        </div>

        <ul className="hidden md:flex items-center gap-6">
          <li>
            <a
              href="#how-it-works"
              className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors font-geist"
            >
              How it works
            </a>
          </li>
          <li>
            <a
              href="#pricing"
              className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors font-geist"
            >
              Pricing
            </a>
          </li>
        </ul>

        <div className="flex items-center gap-3">
          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center h-8 w-8 rounded-lg border border-zinc-200 bg-white text-zinc-700 hover:text-zinc-900 hover:bg-zinc-50 transition-colors shadow-2xs"
            title="View on GitHub"
            aria-label="View on GitHub"
          >
            <GithubLogo size={18} weight="bold" />
          </a>
          <button
            onClick={onEnterConsole}
            className="hidden sm:inline-flex items-center bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-xs cursor-pointer active:scale-[0.98] font-geist"
          >
            Open console
          </button>
          <button
            className="md:hidden p-1.5 rounded-md text-[#525250] hover:text-[#0a0a0a] hover:bg-[#f4f4f3] transition-colors cursor-pointer"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <XIcon size={20} /> : <List size={20} />}
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden bg-white border-b border-[#e4e4e3] px-4 pb-4 pt-2 flex flex-col gap-3">
          <a
            href="#how-it-works"
            className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors py-1 font-geist"
            onClick={() => setMenuOpen(false)}
          >
            How it works
          </a>
          <a
            href="#pricing"
            className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors py-1 font-geist"
            onClick={() => setMenuOpen(false)}
          >
            Pricing
          </a>
          <a
            href="https://github.com/toufiqfarhan0/reco"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors py-1 font-geist"
          >
            <GithubLogo size={16} weight="bold" />
            <span>GitHub Repository</span>
          </a>
          <button
            onClick={() => { setMenuOpen(false); onEnterConsole(); }}
            className="mt-1 w-full bg-indigo-600 text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-all text-center cursor-pointer font-geist"
          >
            Open console
          </button>
        </div>
      )}
    </nav>
  );
}

// ---------------------------------------------------------------------------
// Hero pipeline SVG
// ---------------------------------------------------------------------------
function HeroPipelineSVG() {
  const stages = [
    { label: 'Build',      desc: 'Synthesize DAG',    abbr: 'B' },
    { label: 'Run',        desc: 'Execute pipeline',  abbr: 'R' },
    { label: 'Understand', desc: 'Analyze failures',  abbr: 'U' },
    { label: 'Improve',    desc: 'Mutate and select', abbr: 'I' },
    { label: 'Validate',   desc: 'Held-out test',     abbr: 'V' },
  ];

  const nodeW = 88;
  const nodeH = 72;
  const gapX  = 28;
  const totalW = stages.length * nodeW + (stages.length - 1) * gapX;
  const svgH   = nodeH + 24;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${totalW + 16} ${svgH + 16}`}
        width="100%"
        style={{ minWidth: 360 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <marker id="arrow-hero" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#c7c7c5" />
          </marker>
        </defs>
        {stages.map((stage, i) => {
          const x       = 8 + i * (nodeW + gapX);
          const y       = 8;
          const cx      = x + nodeW / 2;
          const midY    = y + nodeH / 2;
          return (
            <g key={stage.label}>
              {i < stages.length - 1 && (
                <line
                  x1={x + nodeW} y1={midY}
                  x2={x + nodeW + gapX} y2={midY}
                  stroke="#c7c7c5" strokeWidth="1.5"
                  markerEnd="url(#arrow-hero)"
                />
              )}
              <rect x={x} y={y} width={nodeW} height={nodeH} rx="10"
                fill="white" stroke="#e4e4e3" strokeWidth="1.5" />
              <rect x={cx - 12} y={y + 10} width={24} height={24} rx="6" fill="#f4f4f3" />
              <text x={cx} y={y + 27} textAnchor="middle" fontSize="11" fontWeight="700" fill="#525250">
                {stage.abbr}
              </text>
              <text x={cx} y={y + 46} textAnchor="middle" fontSize="10" fontWeight="600" fill="#0a0a0a">
                {stage.label}
              </text>
              <text x={cx} y={y + 59} textAnchor="middle" fontSize="8.5" fill="#8a8a88">
                {stage.desc}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Hero Section
// ---------------------------------------------------------------------------
function HeroSection({ onEnterConsole }: { onEnterConsole: () => void }) {
  return (
    <section id="hero" className="min-h-[100dvh] bg-[#f9f9f8] pt-32 pb-20 flex items-center">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="flex flex-col lg:flex-row lg:items-center gap-12 lg:gap-16">
          <div className="lg:w-1/2 flex flex-col gap-6">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-4xl md:text-5xl font-semibold tracking-tight leading-[1.15] text-[#0a0a0a]"
            >
              Engineer AI agents that actually work.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-base text-[#525250] max-w-[45ch] leading-relaxed"
            >
              Reco turns a natural language goal into a complete agent pipeline. Run it, analyze
              failures, mutate the architecture, and ship something reliable.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.18 }}
              className="flex flex-col sm:flex-row gap-3"
            >
              <button
                onClick={onEnterConsole}
                className="inline-flex items-center justify-center gap-2 bg-[#0a0a0a] text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-[#1a1a1a] transition-colors"
              >
                Open console
                <ArrowRight size={15} weight="bold" />
              </button>
              <a
                href="#how-it-works"
                className="inline-flex items-center justify-center gap-2 border border-[#e4e4e3] text-[#0a0a0a] px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-[#f4f4f3] transition-colors"
              >
                See how it works
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.26 }}
              className="flex flex-row gap-6 pt-4 border-t border-[#e4e4e3] mt-2"
            >
              {[
                { stat: '5 stages',   label: 'From NL goal to production' },
                { stat: '<3 min',     label: 'Agent synthesis time' },
                { stat: 'Zero infra', label: 'No servers to configure' },
              ].map((m) => (
                <div key={m.stat} className="flex flex-col gap-0.5">
                  <span className="text-sm font-semibold text-[#0a0a0a]">{m.stat}</span>
                  <span className="text-xs text-[#8a8a88] leading-snug">{m.label}</span>
                </div>
              ))}
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.32 }}
            className="lg:w-1/2 bg-white border border-[#e4e4e3] rounded-2xl p-6 shadow-sm"
          >
            <p className="text-xs font-medium text-[#8a8a88] uppercase tracking-wider mb-5">
              Agent pipeline
            </p>
            <HeroPipelineSVG />
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// How It Works
// ---------------------------------------------------------------------------
const HOW_IT_WORKS_STEPS = [
  {
    num: '01',
    Icon: Hammer,
    name: 'Build',
    desc: 'Describe your goal in plain English. Reco synthesizes a full DAG architecture with typed node contracts.',
    tag: 'DAG Architecture',
  },
  {
    num: '02',
    Icon: Play,
    name: 'Run',
    desc: 'The execution engine runs each node, collecting traces, latencies, and output diffs for every call.',
    tag: 'Execution Trace',
  },
  {
    num: '03',
    Icon: MagnifyingGlass,
    name: 'Understand',
    desc: 'Reco pinpoints which node failed, why it failed, and what the downstream impact was on the pipeline.',
    tag: 'Failure Report',
  },
  {
    num: '04',
    Icon: GitBranch,
    name: 'Improve',
    desc: 'A mutation tournament generates candidate architectures and scores them against your eval set automatically.',
    tag: 'Candidate Pool',
  },
  {
    num: '05',
    Icon: CheckCircle,
    name: 'Validate',
    desc: 'The winning candidate runs against a held-out validation set before it is promoted to production.',
    tag: 'Validation Score',
  },
] as const;

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-14">
          <p className="text-xs font-medium text-[#8a8a88] uppercase tracking-wider mb-2">Process</p>
          <h2 className="text-3xl font-semibold text-[#0a0a0a] tracking-tight">How it works</h2>
          <p className="text-base text-[#525250] mt-3 max-w-[50ch]">
            Five automated stages take your natural language goal to a validated, production-ready agent.
          </p>
        </div>

        <div className="relative flex flex-col gap-0">
          <div
            className="absolute left-[23px] top-8 bottom-8 w-px bg-[#e4e4e3] hidden sm:block"
            aria-hidden="true"
          />
          {HOW_IT_WORKS_STEPS.map((step) => (
            <div key={step.num} className="relative flex gap-6 sm:gap-10 pb-6 last:pb-0">
              <div className="flex-shrink-0 relative z-10">
                <div className="w-12 h-12 rounded-full bg-white border border-[#e4e4e3] flex items-center justify-center">
                  <span className="text-xs font-semibold text-[#525250]">{step.num}</span>
                </div>
              </div>
              <div className="flex-1 bg-white border border-[#e4e4e3] rounded-xl p-5 mb-2 hover:shadow-sm transition-shadow">
                <div className="flex items-start gap-3 mb-2">
                  <span className="mt-0.5 text-[#525250]">
                    <step.Icon size={18} weight="duotone" />
                  </span>
                  <h3 className="text-sm font-semibold text-[#0a0a0a]">{step.name}</h3>
                  <span className="ml-auto inline-block bg-[#f4f4f3] border border-[#e4e4e3] rounded px-2 py-0.5 text-[10px] font-mono text-[#525250] whitespace-nowrap">
                    {step.tag}
                  </span>
                </div>
                <p className="text-sm text-[#525250] leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Pipeline Diagram Section
// ---------------------------------------------------------------------------
function PipelineDiagramSVG() {
  const boxes = [
    { label: 'NL Goal',             sublabel: 'User input',     abbr: 'NL', color: '#f4f4f3', stroke: '#c7c7c5', dark: false },
    { label: 'DAG Synthesis',       sublabel: 'Architecture',   abbr: 'DS', color: '#fff',    stroke: '#e4e4e3', dark: false },
    { label: 'Execution Engine',    sublabel: 'Node runner',    abbr: 'EE', color: '#fff',    stroke: '#e4e4e3', dark: false },
    { label: 'Failure Analysis',    sublabel: 'Root cause',     abbr: 'FA', color: '#fff',    stroke: '#e4e4e3', dark: false },
    { label: 'Mutation Tournament', sublabel: 'Candidate pool', abbr: 'MT', color: '#fff',    stroke: '#e4e4e3', dark: false },
    { label: 'Held-out Validation', sublabel: 'Eval set',       abbr: 'HV', color: '#fff',    stroke: '#e4e4e3', dark: false },
    { label: 'Production Agent',    sublabel: 'Deployed',       abbr: 'PA', color: '#0a0a0a', stroke: '#0a0a0a', dark: true  },
  ];

  const bw = 120, bh = 68, gap = 24;
  const totalW = boxes.length * bw + (boxes.length - 1) * gap;

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${totalW + 24} ${bh + 40}`}
        style={{ minWidth: 720 }}
        width="100%"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <marker id="arrow-pipe" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#c7c7c5" />
          </marker>
        </defs>
        {boxes.map((box, i) => {
          const x    = 12 + i * (bw + gap);
          const y    = 16;
          const cx   = x + bw / 2;
          const midY = y + bh / 2;
          const textFill = box.dark ? 'white'   : '#0a0a0a';
          const subFill  = box.dark ? '#c7c7c5' : '#8a8a88';
          const abbrFill = box.dark ? '#c7c7c5' : '#525250';
          return (
            <g key={box.label}>
              {i < boxes.length - 1 && (
                <line
                  x1={x + bw} y1={midY} x2={x + bw + gap} y2={midY}
                  stroke="#c7c7c5" strokeWidth="1.5" markerEnd="url(#arrow-pipe)"
                />
              )}
              <rect x={x} y={y} width={bw} height={bh} rx="10"
                fill={box.color} stroke={box.stroke} strokeWidth="1.5" />
              <text x={cx} y={y + 22} textAnchor="middle" fontSize="10" fontWeight="700" fill={abbrFill}>
                {box.abbr}
              </text>
              <text x={cx} y={y + 40} textAnchor="middle" fontSize="9.5" fontWeight="600" fill={textFill}>
                {box.label}
              </text>
              <text x={cx} y={y + 54} textAnchor="middle" fontSize="8" fill={subFill}>
                {box.sublabel}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function PipelineDiagramSection() {
  return (
    <section id="pipeline" className="py-24 bg-[#f9f9f8]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <p className="text-xs font-medium text-[#8a8a88] uppercase tracking-wider mb-2">System overview</p>
          <h2 className="text-3xl font-semibold text-[#0a0a0a] tracking-tight">The full Reco loop</h2>
          <p className="text-base text-[#525250] mt-3 max-w-[50ch]">
            From a natural language goal to a production agent, every stage is automated and observable.
          </p>
        </div>
        <div className="bg-white border border-[#e4e4e3] rounded-2xl p-6 sm:p-8 shadow-sm">
          <PipelineDiagramSVG />
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Mini DAG SVG for bento
// ---------------------------------------------------------------------------
function MiniDAGSvg() {
  const nodes = [
    { x: 10,  y: 35, label: 'Fetch' },
    { x: 90,  y: 10, label: 'Parse' },
    { x: 90,  y: 62, label: 'Embed' },
    { x: 175, y: 35, label: 'Rank'  },
    { x: 210, y: 35, label: 'Reply' },
  ];
  const edges = [
    [68, 49, 90, 24], [68, 49, 90, 76],
    [148, 24, 175, 45], [148, 76, 175, 55],
    [233, 49, 210, 49],
  ];
  return (
    <svg viewBox="0 0 280 110" width="100%" xmlns="http://www.w3.org/2000/svg" className="mt-4">
      <defs>
        <marker id="dag-arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#c7c7c5" />
        </marker>
      </defs>
      {edges.map(([x1,y1,x2,y2], idx) => (
        <line key={idx} x1={x1} y1={y1} x2={x2} y2={y2}
          stroke="#c7c7c5" strokeWidth="1.2" markerEnd="url(#dag-arrow)" />
      ))}
      {nodes.map((n) => (
        <g key={n.label}>
          <rect x={n.x} y={n.y} width={58} height={28} rx="7"
            fill="white" stroke="#e4e4e3" strokeWidth="1.2" />
          <text x={n.x + 29} y={n.y + 18} textAnchor="middle"
            fontSize="9" fontWeight="600" fill="#0a0a0a">
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Features Bento
// ---------------------------------------------------------------------------
function FeaturesBentoSection() {
  return (
    <section id="features" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <p className="text-xs font-medium text-[#8a8a88] uppercase tracking-wider mb-2">Capabilities</p>
          <h2 className="text-3xl font-semibold text-[#0a0a0a] tracking-tight">Built for reliability</h2>
          <p className="text-base text-[#525250] mt-3 max-w-[50ch]">
            Every feature maps to a stage in the pipeline so you always know what is happening and why.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Cell 1: Agent DAG Synthesis (col-span-2) */}
          <div className="md:col-span-2 bg-[#f9f9f8] border border-[#e4e4e3] rounded-2xl p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-1">
              <Hammer size={18} weight="duotone" className="text-[#525250]" />
              <h3 className="text-sm font-semibold text-[#0a0a0a]">Agent DAG Synthesis</h3>
            </div>
            <p className="text-sm text-[#525250] leading-relaxed max-w-[40ch]">
              Reco generates a typed directed acyclic graph from your goal, with explicit node contracts and data flow edges.
            </p>
            <MiniDAGSvg />
          </div>

          {/* Cell 2: Failure Explorer */}
          <div className="bg-[#f5f3ff] border border-[#e4e4e3] rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <MagnifyingGlass size={18} weight="duotone" className="text-[#7c3aed]" />
                <h3 className="text-sm font-semibold text-[#0a0a0a]">Failure Explorer</h3>
              </div>
              <p className="text-sm text-[#525250] leading-relaxed">
                Drill into every failed node. See the input, output, exception trace, and which downstream nodes were affected.
              </p>
            </div>
            <div className="mt-6 bg-white rounded-xl border border-[#e4e4e3] px-4 py-3">
              <p className="text-[10px] font-mono text-[#8a8a88] mb-1">Failure at node</p>
              <p className="text-xs font-mono text-[#7c3aed]">embed_query</p>
              <p className="text-[10px] font-mono text-[#8a8a88] mt-1">KeyError: 'embedding'</p>
            </div>
          </div>

          {/* Cell 3: Mutation Tournament */}
          <div className="bg-[#f0fdf4] border border-[#e4e4e3] rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <GitBranch size={18} weight="duotone" className="text-[#16a34a]" />
                <h3 className="text-sm font-semibold text-[#0a0a0a]">Mutation Tournament</h3>
              </div>
              <p className="text-sm text-[#525250] leading-relaxed">
                Multiple architecture variants compete head-to-head against your eval set. The best one advances automatically.
              </p>
            </div>
            <div className="mt-6 flex flex-col gap-2">
              {[
                { label: 'Variant A', pct: '94%', best: true  },
                { label: 'Variant B', pct: '87%', best: false },
                { label: 'Variant C', pct: '81%', best: false },
              ].map((v) => (
                <div key={v.label} className="flex items-center gap-2">
                  <span className="text-xs text-[#525250] w-16">{v.label}</span>
                  <div className="flex-1 bg-white border border-[#e4e4e3] rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: v.pct, background: v.best ? '#16a34a' : '#c7c7c5' }}
                    />
                  </div>
                  <span className="text-xs font-mono text-[#0a0a0a]">{v.pct}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Cell 4: Held-out Validation (col-span-3) */}
          <div className="md:col-span-3 bg-[#0a0a0a] rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle size={18} weight="duotone" className="text-white" />
                <h3 className="text-sm font-semibold text-white">Held-out Validation</h3>
              </div>
              <p className="text-sm text-[#c7c7c5] leading-relaxed max-w-[55ch]">
                Before any candidate is promoted, it runs against a held-out set that the mutation process never saw. No overfitting to your eval data.
              </p>
            </div>
            <div className="flex flex-col gap-2 min-w-[160px]">
              {[
                { label: 'Train eval', val: '94%' },
                { label: 'Held-out',   val: '91%' },
                { label: 'Gap',        val: '3%'  },
              ].map((row) => (
                <div key={row.label} className="flex justify-between items-center gap-4">
                  <span className="text-xs text-[#8a8a88]">{row.label}</span>
                  <span className="text-xs font-mono font-semibold text-white">{row.val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Pricing
// ---------------------------------------------------------------------------
const FREE_FEATURES = [
  '3 agents per month',
  'Up to 5 pipeline stages',
  'Community support',
];

const PRO_FEATURES = [
  'Unlimited agents',
  'Up to 20 pipeline stages',
  'Mutation tournament (up to 8 variants)',
  'Held-out validation',
  'Failure Explorer with full traces',
  'Priority support',
  'Team collaboration (up to 5 seats)',
];

function PricingSection({ onEnterConsole }: { onEnterConsole: () => void }) {
  return (
    <section id="pricing" className="py-24 bg-[#f9f9f8]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <p className="text-xs font-medium text-[#8a8a88] uppercase tracking-wider mb-2">Pricing</p>
          <h2 className="text-3xl font-semibold text-[#0a0a0a] tracking-tight">
            Simple, transparent pricing
          </h2>
          <p className="text-base text-[#525250] mt-3 max-w-[48ch]">
            Start free. Upgrade when you need more power.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
          {/* Free */}
          <div className="bg-white border border-[#e4e4e3] rounded-2xl p-6 flex flex-col">
            <div className="mb-5">
              <h3 className="text-sm font-semibold text-[#0a0a0a]">Free</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-3xl font-semibold text-[#0a0a0a]">$0</span>
                <span className="text-sm text-[#8a8a88]">/mo</span>
              </div>
              <p className="mt-1 text-xs text-[#8a8a88]">No credit card required</p>
            </div>
            <ul className="flex flex-col gap-2.5 mb-6">
              {FREE_FEATURES.map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <Check size={14} weight="bold" className="text-[#525250] mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-[#525250]">{f}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={onEnterConsole}
              className="mt-auto w-full border border-[#e4e4e3] text-[#0a0a0a] px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-[#f4f4f3] transition-colors"
            >
              Get started free
            </button>
          </div>

          {/* Pro */}
          <div className="bg-white border border-[#e4e4e3] border-t-2 border-t-[#0a0a0a] rounded-2xl p-6 flex flex-col">
            <div className="mb-5">
              <h3 className="text-sm font-semibold text-[#0a0a0a]">Pro</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-3xl font-semibold text-[#0a0a0a]">$29</span>
                <span className="text-sm text-[#8a8a88]">/mo</span>
              </div>
              <p className="mt-1 text-xs text-[#8a8a88]">Per workspace, billed monthly</p>
            </div>
            <ul className="flex flex-col gap-2.5 mb-6">
              {PRO_FEATURES.map((f) => (
                <li key={f} className="flex items-start gap-2">
                  <Check size={14} weight="bold" className="text-[#0a0a0a] mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-[#525250]">{f}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={onEnterConsole}
              className="mt-auto w-full bg-[#0a0a0a] text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-[#1a1a1a] transition-colors"
            >
              Upgrade to Pro
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Footer
// ---------------------------------------------------------------------------
function Footer({ onEnterConsole }: { onEnterConsole: () => void }) {
  const year = new Date().getFullYear();
  return (
    <footer className="py-12 bg-white border-t border-[#e4e4e3]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-10">
          <div className="flex flex-col gap-2">
            <span className="font-semibold text-[#0a0a0a]">Reco</span>
            <p className="text-sm text-[#8a8a88] max-w-[28ch] leading-relaxed">
              AI Agent Engineering. Build, run, and ship reliable agents.
            </p>
          </div>

          <div className="flex flex-col gap-1">
            <p className="text-xs font-semibold text-[#0a0a0a] uppercase tracking-wider mb-2">Quick links</p>
            {['How it works', 'Features', 'Pricing'].map((l) => (
              <a
                key={l}
                href={`#${l.toLowerCase().replace(/\s+/g, '-')}`}
                className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors"
              >
                {l}
              </a>
            ))}
            <button
              onClick={onEnterConsole}
              className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors text-left mt-1"
            >
              Open console
            </button>
          </div>

          <div className="flex flex-col gap-1">
            <p className="text-xs font-semibold text-[#0a0a0a] uppercase tracking-wider mb-2">Resources</p>
            {[
              { label: 'GitHub',        href: 'https://github.com' },
              { label: 'Documentation', href: '#' },
              { label: 'Changelog',     href: '#' },
              { label: 'Status',        href: '#' },
            ].map((link) => (
              <a
                key={link.label}
                href={link.href}
                target={link.href.startsWith('http') ? '_blank' : undefined}
                rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                className="text-sm text-[#525250] hover:text-[#0a0a0a] transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>

        <div className="pt-6 border-t border-[#e4e4e3] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <p className="text-xs text-[#8a8a88]">{year} Reco. All rights reserved.</p>
          <p className="text-xs text-[#8a8a88]">Built for engineers who ship.</p>
        </div>
      </div>
    </footer>
  );
}

// ---------------------------------------------------------------------------
// Root export
// ---------------------------------------------------------------------------
export function LandingPage({ onEnterConsole }: LandingPageProps) {
  return (
    <div className="bg-[#f9f9f8] font-sans antialiased">
      <Navbar onEnterConsole={onEnterConsole} />
      <HeroSection onEnterConsole={onEnterConsole} />
      <HowItWorksSection />
      <PipelineDiagramSection />
      <FeaturesBentoSection />
      <PricingSection onEnterConsole={onEnterConsole} />
      <Footer onEnterConsole={onEnterConsole} />
    </div>
  );
}
