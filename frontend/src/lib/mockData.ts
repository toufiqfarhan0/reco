import {
  DomainType,
  DAGArchitecture,
  Scorecard,
  ScorecardComparison,
  FailureDiagnostic,
  Candidate,
  LineageNode,
  HeldOutValidationData,
  NeatlogsTrace,
} from "./types";

export const DOMAIN_PRESETS: Record<
  DomainType,
  {
    name: string;
    label: string;
    description: string;
    defaultGoal: string;
    availableTools: { name: string; desc: string; capability: string }[];
    sampleChips: string[];
  }
> = {
  financial_reconciliation: {
    name: "Financial Reconciliation",
    label: "Financial Reconciliation",
    description:
      "Dual-ledger transaction matching with currency parsing, duplicate detection, and schema validation.",
    defaultGoal:
      "Reconcile internal transaction ledger against payment gateway exports, normalize currency strings, flag discrepancies, and isolate duplicate charges.",
    availableTools: [
      {
        name: "exact_reconcile",
        desc: "Strict ID and numeric amount matching across source & target ledgers",
        capability: "exact_match",
      },
      {
        name: "smart_reconcile",
        desc: "Advanced normalization: casing, whitespace, $ symbols, and commas",
        capability: "advanced_reconciliation",
      },
      {
        name: "json_validator",
        desc: "Enforces strict JSON schema contracts on reconciliation outputs",
        capability: "verification",
      },
      {
        name: "tabular_summary",
        desc: "Calculates record counts, schema null values, and column typing",
        capability: "tabular_parsing",
      },
    ],
    sampleChips: [
      "Stripe Gateway vs ERP Ledger",
      "Currency & Whitespace Normalization",
      "Multi-Currency Refund Discrepancy",
      "High-Volume Duplicate Detection",
    ],
  },
  anomaly_detection: {
    name: "Anomaly Detection",
    label: "Anomaly Detection",
    description:
      "Statistical outlier detection on numerical datasets using standard Z-score deviations.",
    defaultGoal:
      "Detect outlier transaction amounts and high-frequency velocity anomalies using statistical Z-score thresholds >= 2.5.",
    availableTools: [
      {
        name: "compute_distributions",
        desc: "Calculates mean, std, median, and interquartile ranges per numeric column",
        capability: "distribution_analysis",
      },
      {
        name: "detect_anomalies",
        desc: "Identifies observations exceeding parameterized Z-score thresholds",
        capability: "outlier_detection",
      },
      {
        name: "tabular_summary",
        desc: "Summarizes column dimensions and null distributions",
        capability: "tabular_parsing",
      },
      {
        name: "json_validator",
        desc: "Verifies anomaly payload schema compatibility",
        capability: "schema_validation",
      },
    ],
    sampleChips: [
      "Z-score Outlier Detection (Z >= 2.5)",
      "Log-Normal Latency Spikes",
      "Volume Surge Anomaly",
      "High-Frequency Trade Discrepancies",
    ],
  },
  research_comparison: {
    name: "Research Comparison",
    label: "Research Comparison",
    description:
      "Multi-candidate entity extraction, citation verification, and factual consistency scoring.",
    defaultGoal:
      "Synthesize competitor benchmarks across multiple financial reports, extract quantitative metrics, and verify ground-truth consistency.",
    availableTools: [
      {
        name: "tabular_summary",
        desc: "Structures parsed tabular financial statements",
        capability: "tabular_parsing",
      },
      {
        name: "smart_reconcile",
        desc: "Cross-checks reported revenue metrics across filings",
        capability: "advanced_reconciliation",
      },
      {
        name: "json_validator",
        desc: "Verifies extraction schema consistency",
        capability: "schema_validation",
      },
    ],
    sampleChips: [
      "Quarterly Earnings Cross-Check",
      "Vendor Contract Rate Comparison",
      "Model Evaluation Score Synthesis",
      "Regulatory Filing Discrepancy",
    ],
  },
};

export const INITIAL_DAG_V0: DAGArchitecture = {
  id: "arch_v0_reco",
  name: "Agent_Reconciliation_V0",
  domain: "financial_reconciliation",
  nodes: [
    {
      id: "input_01",
      type: "input_node",
      name: "Transaction Ingestion",
      status: "completed",
      latency_ms: 12.4,
      outputSummary: "Parsed 6 source records & 6 target records from raw payload",
      dependencies: [],
    },
    {
      id: "tool_reconcile_01",
      type: "tool_node",
      name: "Exact Reconcile Tool",
      tool_name: "exact_reconcile",
      status: "completed",
      latency_ms: 54.2,
      outputSummary: "Executed exact ID match; failed to parse currency strings with '$'",
      dependencies: ["input_01"],
    },
    {
      id: "reasoning_01",
      type: "reasoning_node",
      name: "Discrepancy Formatter",
      status: "completed",
      latency_ms: 22.8,
      outputSummary: "Assembled matched & discrepancy ID lists into payload",
      dependencies: ["tool_reconcile_01"],
    },
    {
      id: "output_01",
      type: "output_node",
      name: "Scorecard Delivery",
      status: "completed",
      latency_ms: 10.6,
      outputSummary: "Emitted final reconciliation result JSON",
      dependencies: ["reasoning_01"],
    },
  ],
  edges: [
    { source: "input_01", target: "tool_reconcile_01" },
    { source: "tool_reconcile_01", target: "reasoning_01" },
    { source: "reasoning_01", target: "output_01" },
  ],
};

export const OPTIMIZED_DAG_V2: DAGArchitecture = {
  id: "arch_v2_reco",
  name: "Agent_Reconciliation_V2_Candidate_C",
  domain: "financial_reconciliation",
  nodes: [
    {
      id: "input_01",
      type: "input_node",
      name: "Transaction Ingestion",
      status: "completed",
      latency_ms: 11.8,
      outputSummary: "Ingested partitioned records into clean execution memory",
      dependencies: [],
    },
    {
      id: "tool_smart_reconcile_01",
      type: "tool_node",
      name: "Smart Reconcile Tool",
      tool_name: "smart_reconcile",
      status: "completed",
      latency_ms: 46.1,
      outputSummary: "Normalized casing, whitespace, and currency formatting; isolated duplicates",
      dependencies: ["input_01"],
    },
    {
      id: "verifier_01",
      type: "verifier_node",
      name: "Schema & Duplicate Guardrail",
      tool_name: "json_validator",
      status: "completed",
      latency_ms: 18.5,
      outputSummary: "Verified zero schema violations and caught duplicate transaction IDs",
      dependencies: ["tool_smart_reconcile_01"],
    },
    {
      id: "reasoning_01",
      type: "reasoning_node",
      name: "Discrepancy Synthesizer",
      status: "completed",
      latency_ms: 15.6,
      outputSummary: "Generated audit notes and confirmed ground truth compliance",
      dependencies: ["verifier_01"],
    },
    {
      id: "output_01",
      type: "output_node",
      name: "Verified Scorecard Delivery",
      status: "completed",
      latency_ms: 9.2,
      outputSummary: "Emitted compliant 4-axis audit envelope",
      dependencies: ["reasoning_01"],
    },
  ],
  edges: [
    { source: "input_01", target: "tool_smart_reconcile_01" },
    { source: "tool_smart_reconcile_01", target: "verifier_01" },
    { source: "verifier_01", target: "reasoning_01" },
    { source: "reasoning_01", target: "output_01" },
  ],
};

export const V0_BASELINE_SCORECARD: Scorecard = {
  name: "V0_Baseline_Reconciliation",
  split: "optimization",
  total_cases: 6,
  accurate_cases: 1,
  reliable_cases: 6,
  accuracy: 0.1667,
  reliability: 1.0,
  cost_usd: 0.005,
  latency_ms: 100.0,
  avg_latency_ms: 16.67,
  latency_s: 0.1,
  case_results: [
    {
      case_id: "reco_opt_001_exact_match",
      name: "Exact Match Clean",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0008,
      latency_ms: 15.2,
      actual_output: "{ matched_ids: ['TX1001', 'TX1002'], status: 'reconciled' }",
      expected_output: "{ matched_ids: ['TX1001', 'TX1002'], status: 'reconciled' }",
    },
    {
      case_id: "reco_opt_002_casing_mismatch",
      name: "ID Casing Variation (tx1003 vs TX1003)",
      split: "optimization",
      is_accurate: false,
      is_reliable: true,
      cost_usd: 0.0008,
      latency_ms: 16.4,
      error: "Strict equality missed lowercased ID 'tx1003'",
      actual_output: "{ matched_ids: [], unmatched_source_ids: ['tx1003'] }",
      expected_output: "{ matched_ids: ['TX1003'] }",
    },
    {
      case_id: "reco_opt_003_currency_string",
      name: "Currency String ($1,250.00)",
      split: "optimization",
      is_accurate: false,
      is_reliable: true,
      cost_usd: 0.0008,
      latency_ms: 18.1,
      error: "String '$1,250.00' != float 1250.00",
      actual_output: "{ discrepancy_ids: ['TX1004'] }",
      expected_output: "{ matched_ids: ['TX1004'] }",
    },
    {
      case_id: "reco_opt_004_duplicate_charge",
      name: "Target Duplicate Ingestion",
      split: "optimization",
      is_accurate: false,
      is_reliable: true,
      cost_usd: 0.0009,
      latency_ms: 17.5,
      error: "Duplicate TX1005 not flagged in exact reconcile",
      actual_output: "{ matched_ids: ['TX1005'], duplicate_ids: [] }",
      expected_output: "{ duplicate_ids: ['TX1005'], status: 'duplicate_detected' }",
    },
    {
      case_id: "reco_opt_005_missing_target",
      name: "Unmatched Ledger Entry",
      split: "optimization",
      is_accurate: false,
      is_reliable: true,
      cost_usd: 0.0008,
      latency_ms: 16.1,
      error: "Incomplete discrepancy isolation",
      actual_output: "{ unmatched_source_ids: [] }",
      expected_output: "{ unmatched_source_ids: ['TX1006'], status: 'discrepancy_detected' }",
    },
    {
      case_id: "reco_opt_006_whitespace_padding",
      name: "Whitespace Trailing Key",
      split: "optimization",
      is_accurate: false,
      is_reliable: true,
      cost_usd: 0.0009,
      latency_ms: 16.7,
      error: "Trailing whitespace 'TX1007 ' failed exact match",
      actual_output: "{ unmatched_source_ids: ['TX1007 '] }",
      expected_output: "{ matched_ids: ['TX1007'] }",
    },
  ],
};

export const V1_CANDIDATE_B_SCORECARD: Scorecard = {
  name: "Candidate_B_Tool_Mutated",
  split: "optimization",
  total_cases: 6,
  accurate_cases: 5,
  reliable_cases: 6,
  accuracy: 0.8333,
  reliability: 1.0,
  cost_usd: 0.004,
  latency_ms: 85.0,
  avg_latency_ms: 14.17,
  latency_s: 0.085,
  case_results: [
    {
      case_id: "reco_opt_001_exact_match",
      name: "Exact Match Clean",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0006,
      latency_ms: 13.5,
    },
    {
      case_id: "reco_opt_002_casing_mismatch",
      name: "ID Casing Variation",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 14.2,
    },
    {
      case_id: "reco_opt_003_currency_string",
      name: "Currency String ($1,250.00)",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 14.8,
    },
    {
      case_id: "reco_opt_004_duplicate_charge",
      name: "Target Duplicate Ingestion",
      split: "optimization",
      is_accurate: false,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 15.1,
      error: "Missing explicit verifier node to catch edge-case secondary duplicate",
    },
    {
      case_id: "reco_opt_005_missing_target",
      name: "Unmatched Ledger Entry",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0006,
      latency_ms: 13.8,
    },
    {
      case_id: "reco_opt_006_whitespace_padding",
      name: "Whitespace Trailing Key",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 13.6,
    },
  ],
};

export const V2_CANDIDATE_C_SCORECARD: Scorecard = {
  name: "Candidate_C_Verifier_Guarded",
  split: "optimization",
  total_cases: 6,
  accurate_cases: 6,
  reliable_cases: 6,
  accuracy: 1.0,
  reliability: 1.0,
  cost_usd: 0.0042,
  latency_ms: 91.2,
  avg_latency_ms: 15.2,
  latency_s: 0.0912,
  case_results: [
    {
      case_id: "reco_opt_001_exact_match",
      name: "Exact Match Clean",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 14.5,
    },
    {
      case_id: "reco_opt_002_casing_mismatch",
      name: "ID Casing Variation",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 15.1,
    },
    {
      case_id: "reco_opt_003_currency_string",
      name: "Currency String ($1,250.00)",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 15.4,
    },
    {
      case_id: "reco_opt_004_duplicate_charge",
      name: "Target Duplicate Ingestion",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 15.9,
    },
    {
      case_id: "reco_opt_005_missing_target",
      name: "Unmatched Ledger Entry",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 15.0,
    },
    {
      case_id: "reco_opt_006_whitespace_padding",
      name: "Whitespace Trailing Key",
      split: "optimization",
      is_accurate: true,
      is_reliable: true,
      cost_usd: 0.0007,
      latency_ms: 15.3,
    },
  ],
};

export const COMPARISON_V0_VS_CANDIDATE_B: ScorecardComparison = {
  baseline_name: "Baseline V0",
  candidate_name: "Candidate B (Tool Mutated)",
  split: "optimization",
  baseline: V0_BASELINE_SCORECARD,
  candidate: V1_CANDIDATE_B_SCORECARD,
  accuracy_delta: 0.6666,
  reliability_delta: 0.0,
  cost_delta_usd: -0.001,
  latency_delta_ms: -15.0,
  latency_pct_delta: -15.0,
  accuracy_badge: "+66.7%",
  reliability_badge: "+0.0%",
  cost_badge: "-$0.0010",
  latency_badge: "-15.00ms (-15.0%)",
  is_pareto_dominant: true,
  has_tradeoff: false,
  tradeoffs: [],
  verdict: "PARETO_DOMINANT",
};

export const COMPARISON_V0_VS_CANDIDATE_C: ScorecardComparison = {
  baseline_name: "Baseline V0",
  candidate_name: "Candidate C (Verifier Guarded)",
  split: "optimization",
  baseline: V0_BASELINE_SCORECARD,
  candidate: V2_CANDIDATE_C_SCORECARD,
  accuracy_delta: 0.8333,
  reliability_delta: 0.0,
  cost_delta_usd: -0.0008,
  latency_delta_ms: -8.8,
  latency_pct_delta: -8.8,
  accuracy_badge: "+83.3%",
  reliability_badge: "+0.0%",
  cost_badge: "-$0.0008",
  latency_badge: "-8.80ms (-8.8%)",
  is_pareto_dominant: true,
  has_tradeoff: false,
  tradeoffs: [],
  verdict: "PARETO_DOMINANT",
};

export const FAILURE_DIAGNOSTICS: FailureDiagnostic[] = [
  {
    case_id: "reco_opt_002_casing_mismatch",
    case_name: "ID Casing Variation (tx1003 vs TX1003)",
    category: "tool_selection_error",
    symptoms: [
      "Unmatched source ID 'tx1003' reported as discrepancy",
      "False negative match against target 'TX1003'",
    ],
    root_cause:
      "exact_reconcile performs raw string matching without case folding or string trimming.",
    target_node_id: "tool_reconcile_01",
    remedy_suggestion:
      "Upgrade tool assignment from exact_reconcile to smart_reconcile.",
    recommended_mutator: "ToolAssignmentMutator",
    confidence: 0.98,
  },
  {
    case_id: "reco_opt_003_currency_string",
    case_name: "Currency String Formatting ($1,250.00)",
    category: "tool_parameter_error",
    symptoms: [
      "Numeric parse exception swallowed as string mismatch",
      "Amounts '$1,250.00' and '1250.00' flagged as discrepancy",
    ],
    root_cause:
      "Tool arguments expected float amount; received raw unparsed currency string with '$' symbol.",
    target_node_id: "tool_reconcile_01",
    remedy_suggestion:
      "Add input amount sanitization or switch to currency-aware parser.",
    recommended_mutator: "PromptMutator",
    confidence: 0.95,
  },
  {
    case_id: "reco_opt_004_duplicate_charge",
    case_name: "Target Duplicate Ingestion",
    category: "verification_miss",
    symptoms: [
      "Duplicate target records TX1005 omitted from duplicate_ids list",
      "Status emitted as 'reconciled' instead of 'duplicate_detected'",
    ],
    root_cause:
      "No verifier node exists in DAG to validate uniqueness invariants across input sets.",
    target_node_id: "reasoning_01",
    remedy_suggestion:
      "Insert json_validator or duplicate guardrail verifier node prior to output stage.",
    recommended_mutator: "VerifierNodeMutator",
    confidence: 0.92,
  },
  {
    case_id: "reco_opt_005_missing_target",
    case_name: "Unmatched Ledger Entry",
    category: "schema_violation",
    symptoms: [
      "Output JSON omitted required 'unmatched_target_ids' key",
      "Evaluation assertion failed on schema contract keys",
    ],
    root_cause:
      "Discrepancy Formatter prompt lacked explicit instruction to include all required reconciliation keys.",
    target_node_id: "reasoning_01",
    remedy_suggestion:
      "Enforce JSON schema contract via system prompt mutation and structured verifier.",
    recommended_mutator: "PromptMutator",
    confidence: 0.89,
  },
  {
    case_id: "reco_opt_006_whitespace_padding",
    case_name: "Whitespace Trailing Key ('TX1007 ')",
    category: "tool_selection_error",
    symptoms: [
      "ID 'TX1007 ' failed equality check against 'TX1007'",
      "Record dropped into unmatched list",
    ],
    root_cause:
      "exact_reconcile lacks string strip() pre-processing on key lookups.",
    target_node_id: "tool_reconcile_01",
    remedy_suggestion:
      "Switch to smart_reconcile with automated string whitespace normalization.",
    recommended_mutator: "ToolAssignmentMutator",
    confidence: 0.97,
  },
];

export const ALL_TAXONOMY_CATEGORIES = [
  {
    id: "prompt_ambiguity",
    name: "Prompt Ambiguity",
    description: "Node prompt lacks domain constraints or formatting rules.",
  },
  {
    id: "tool_selection_error",
    name: "Tool Selection Error",
    description: "Sub-optimal or under-capable tool assigned in DAG.",
  },
  {
    id: "tool_parameter_error",
    name: "Tool Parameter Error",
    description: "Arguments failed schema validation or wrong typing.",
  },
  {
    id: "schema_violation",
    name: "Schema Violation",
    description: "Output omitted ground-truth keys or structural shape.",
  },
  {
    id: "verification_miss",
    name: "Verification Miss",
    description: "No guardrail to intercept discrepancy or duplicate error.",
  },
  {
    id: "routing_misdirect",
    name: "Routing Misdirect",
    description: "Topological edge routing bypassed critical stages.",
  },
  {
    id: "context_overflow",
    name: "Context Overflow",
    description: "Memory state exceeded context window token budget.",
  },
  {
    id: "retry_exhaustion",
    name: "Retry Exhaustion",
    description: "Flaky operation exhausted retry policy budget.",
  },
  {
    id: "model_capability_limit",
    name: "Model Capability Limit",
    description: "Reasoning node failed multi-hop synthesis.",
  },
  {
    id: "timeout_exceeded",
    name: "Timeout Exceeded",
    description: "Wall-clock latency exceeded budget limit.",
  },
  {
    id: "state_corruption",
    name: "State Corruption",
    description: "Shared state store lost intermediate record keys.",
  },
  {
    id: "unhandled_exception",
    name: "Unhandled Exception",
    description: "Uncaught runtime crash during graph traversal.",
  },
] as const;

export const CANDIDATES_TOURNAMENT: Candidate[] = [
  {
    id: "A",
    name: "Candidate A (Baseline V0)",
    tag: "Gen 0 - Exact Match Only",
    generation: 0,
    description:
      "Initial synthesized architecture relying on exact ID and amount matching without normalization or guardrails.",
    scorecard: V0_BASELINE_SCORECARD,
    mutator_applied: "None (Initial Synthesis)",
    targeted_node: "N/A",
    prompt_diff: {
      original:
        "Prompt: Match transactions by id and amount. Return matched and unmatched ids in JSON.",
      mutated:
        "Prompt: Match transactions by id and amount. Return matched and unmatched ids in JSON.",
    },
    config_diff: {
      original: "tool: exact_reconcile\nretry_count: 0\nverifier: disabled",
      mutated: "tool: exact_reconcile\nretry_count: 0\nverifier: disabled",
    },
    win_rate: 16.7,
    status: "baseline",
  },
  {
    id: "B",
    name: "Candidate B (Smart Reconcile)",
    tag: "Gen 1 - Tool Mutation",
    generation: 1,
    description:
      "Autonomous mutation replacing exact_reconcile with smart_reconcile to normalize casing, whitespace, and currency symbols.",
    scorecard: V1_CANDIDATE_B_SCORECARD,
    mutator_applied: "ToolAssignmentMutator",
    targeted_node: "tool_reconcile_01",
    prompt_diff: {
      original: "reconcile_node -> tool: exact_reconcile",
      mutated:
        "reconcile_node -> tool: smart_reconcile (normalizes casing, strips whitespace, parses $ symbols)",
    },
    config_diff: {
      original: "- tool: exact_reconcile\n- strip_whitespace: false",
      mutated: "+ tool: smart_reconcile\n+ strip_whitespace: true\n+ parse_currency_symbols: true",
    },
    win_rate: 83.3,
    status: "pareto_dominant",
  },
  {
    id: "C",
    name: "Candidate C (Verifier Guarded)",
    tag: "Gen 2 - Verifier Guardrail",
    generation: 2,
    description:
      "Topological mutation inserting json_validator and duplicate check guardrail before output emission.",
    scorecard: V2_CANDIDATE_C_SCORECARD,
    mutator_applied: "VerifierNodeMutator + PromptMutator",
    targeted_node: "verifier_01",
    prompt_diff: {
      original:
        "reasoning_node -> Discrepancy Formatter: Emit JSON with matched and unmatched lists.",
      mutated:
        "verifier_node -> json_validator: Verify schema invariants. Ensure duplicate_ids and unmatched_target_ids are strictly populated.",
    },
    config_diff: {
      original: "- nodes: [input, tool, reasoning, output]",
      mutated:
        "+ nodes: [input, tool, verifier_node, reasoning, output]\n+ verifier_schema: reconciliation_schema_v2\n+ strict_duplicate_enforcement: true",
    },
    win_rate: 100.0,
    status: "verified_champion",
  },
];

export const EVOLUTION_LINEAGE: LineageNode[] = [
  {
    id: "node_gen0",
    label: "Baseline V0",
    version: "v0.1.0",
    generation: 0,
    accuracy: 0.1667,
    mutation: "GoalAnalyzer Initial DAG Generation",
    status: "baseline",
    notes: "Failed 5/6 cases due to strict casing and currency string formatting.",
  },
  {
    id: "node_gen1_a",
    label: "Candidate B (Tool Mutation)",
    version: "v1.0.0",
    generation: 1,
    accuracy: 0.8333,
    mutation: "ToolAssignmentMutator (exact -> smart)",
    status: "candidate",
    parentId: "node_gen0",
    notes:
      "Resolved currency strings and whitespace discrepancies. Pareto dominant over Baseline.",
  },
  {
    id: "node_gen2_champ",
    label: "Candidate C (Verifier Guardrail)",
    version: "v2.0.0",
    generation: 2,
    accuracy: 1.0,
    mutation: "VerifierNodeMutator (inserted schema & duplicate guardrail)",
    status: "promoted",
    parentId: "node_gen1_a",
    notes:
      "Achieved 100% on optimization partition and 100% on held-out air-gapped test cases.",
  },
];

export const HELD_OUT_VALIDATION_DATA: HeldOutValidationData = {
  split_name: "held-out",
  total_cases: 4,
  passed_cases: 4,
  accuracy: 1.0,
  reliability: 1.0,
  air_gap_checksum: "sha256:4f8e91d03b6e82c3f87a8b66e138a0c4921b714f2e9",
  leakage_detected: false,
  generalization_gap: 0.0,
  promotion_decision: "PROMOTED",
  rationale: [
    "Strict 0% cross-split leakage verified (zero ID or sample overlaps with optimization split).",
    "Candidate C achieved 100.0% ground-truth accuracy (4/4 passed) on unpolluted held-out cases.",
    "Reliability maintained at 100.0% with zero runtime exceptions or timeout violations.",
    "Pareto dominance verified: 0 regressions across Accuracy, Reliability, Cost, or Speed.",
  ],
  cases: [
    {
      case_id: "reco_held_001_casing_whitespace",
      name: "Held-Out: Mixed Casing & Hidden Newlines",
      phenomenon: "Format Variation & Casing",
      passed: true,
      latency_ms: 15.6,
      ground_truth: "{ matched_ids: ['TX_HO_101', 'TX_HO_102'], status: 'reconciled' }",
      actual_output: "{ matched_ids: ['TX_HO_101', 'TX_HO_102'], status: 'reconciled' }",
      notes: "Smart reconcile stripped non-standard whitespace and normalized IDs.",
    },
    {
      case_id: "reco_held_002_missing_in_target",
      name: "Held-Out: Missing Target Settlement",
      phenomenon: "Missing Records",
      passed: true,
      latency_ms: 14.9,
      ground_truth: "{ unmatched_source_ids: ['TX_HO_103'], status: 'discrepancy_detected' }",
      actual_output: "{ unmatched_source_ids: ['TX_HO_103'], status: 'discrepancy_detected' }",
      notes: "Correctly flagged un-settled transaction as discrepancy.",
    },
    {
      case_id: "reco_held_003_amount_decimals",
      name: "Held-Out: Floating Precision (199.999 vs 200.00)",
      phenomenon: "Amount Mismatch",
      passed: true,
      latency_ms: 15.2,
      ground_truth: "{ discrepancy_ids: ['TX_HO_104'] }",
      actual_output: "{ discrepancy_ids: ['TX_HO_104'] }",
      notes: "Tolerance checker flagged discrepancy outside eps margin.",
    },
    {
      case_id: "reco_held_004_duplicate_ids",
      name: "Held-Out: Triple Duplicate Injection",
      phenomenon: "Duplicate Records",
      passed: true,
      latency_ms: 16.1,
      ground_truth: "{ duplicate_ids: ['TX_HO_105'], status: 'duplicate_detected' }",
      actual_output: "{ duplicate_ids: ['TX_HO_105'], status: 'duplicate_detected' }",
      notes: "Verifier guardrail successfully caught duplicate entries.",
    },
  ],
};

export const NEATLOGS_TRACE: NeatlogsTrace = {
  trace_id: "tr_neat_984f7e21a08b",
  architecture_id: "Agent_Reconciliation_V2_Candidate_C",
  status: "success",
  total_duration_ms: 91.2,
  total_tokens: 340,
  total_cost_usd: 0.0042,
  timestamp: "2026-09-06T01:10:00Z",
  spans: [
    {
      span_id: "sp_dag_001",
      name: "DAG Execution: Agent_Reconciliation_V2",
      kind: "dag",
      status: "ok",
      start_offset_ms: 0,
      duration_ms: 91.2,
      tokens: 340,
      cost_usd: 0.0042,
      attributes: {
        split: "held-out",
        nodes_executed: 5,
        acyclic: true,
      },
    },
    {
      span_id: "sp_node_in_001",
      name: "Node: Transaction Ingestion",
      kind: "node",
      status: "ok",
      start_offset_ms: 1.2,
      duration_ms: 11.8,
      attributes: {
        records_loaded: 4,
        source: "gateway_export.csv",
      },
    },
    {
      span_id: "sp_tool_smart_001",
      name: "Tool: smart_reconcile",
      kind: "tool",
      status: "ok",
      start_offset_ms: 13.5,
      duration_ms: 46.1,
      attributes: {
        casing_normalized: true,
        whitespace_stripped: true,
        currency_parsed: true,
      },
    },
    {
      span_id: "sp_verifier_guard_001",
      name: "Verifier: Schema & Duplicate Guardrail",
      kind: "verifier",
      status: "ok",
      start_offset_ms: 60.2,
      duration_ms: 18.5,
      attributes: {
        schema_validation: "passed",
        duplicate_detected: true,
        quarantine_action: "none",
      },
    },
    {
      span_id: "sp_reasoning_001",
      name: "Reasoning: Discrepancy Synthesizer",
      kind: "llm",
      status: "ok",
      start_offset_ms: 79.1,
      duration_ms: 15.6,
      tokens: 340,
      cost_usd: 0.0042,
      attributes: {
        model: "deterministic_rule_engine",
        ground_truth_compliance: 1.0,
      },
    },
  ],
};
