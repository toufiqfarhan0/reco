export type DomainType =
  | "financial_reconciliation"
  | "anomaly_detection"
  | "research_comparison";

export type ExecutionMode = "demo" | "live";

export type StageType =
  | "BUILD"
  | "RUN"
  | "UNDERSTAND"
  | "IMPROVE"
  | "VALIDATE";

export type NodeType =
  | "input_node"
  | "tool_node"
  | "reasoning_node"
  | "verifier_node"
  | "output_node";

export type NodeExecutionStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export interface DAGNode {
  id: string;
  type: NodeType;
  name: string;
  tool_name?: string;
  status: NodeExecutionStatus;
  latency_ms?: number;
  outputSummary?: string;
  error?: string;
  dependencies: string[];
}

export interface DAGEdge {
  source: string;
  target: string;
}

export interface DAGArchitecture {
  id: string;
  name: string;
  domain: DomainType;
  nodes: DAGNode[];
  edges: DAGEdge[];
}

export interface CaseResult {
  case_id: string;
  name: string;
  split: "optimization" | "held-out";
  is_accurate: boolean;
  is_reliable: boolean;
  cost_usd: number;
  latency_ms: number;
  error?: string;
  actual_output?: string;
  expected_output?: string;
}

export interface Scorecard {
  name: string;
  split: "optimization" | "held-out" | "full";
  total_cases: number;
  accurate_cases: number;
  reliable_cases: number;
  accuracy: number;
  reliability: number;
  cost_usd: number;
  latency_ms: number;
  avg_latency_ms: number;
  latency_s: number;
  case_results: CaseResult[];
}

export interface ScorecardComparison {
  baseline_name: string;
  candidate_name: string;
  split: string;
  baseline: Scorecard;
  candidate: Scorecard;
  accuracy_delta: number;
  reliability_delta: number;
  cost_delta_usd: number;
  latency_delta_ms: number;
  latency_pct_delta: number;
  accuracy_badge: string;
  reliability_badge: string;
  cost_badge: string;
  latency_badge: string;
  is_pareto_dominant: boolean;
  has_tradeoff: boolean;
  tradeoffs: string[];
  verdict: "PARETO_DOMINANT" | "TRADEOFF" | "REGRESSION" | "NEUTRAL";
}

export type FailureCategory =
  | "prompt_ambiguity"
  | "tool_selection_error"
  | "tool_parameter_error"
  | "schema_violation"
  | "verification_miss"
  | "routing_misdirect"
  | "context_overflow"
  | "retry_exhaustion"
  | "model_capability_limit"
  | "timeout_exceeded"
  | "state_corruption"
  | "unhandled_exception";

export interface FailureDiagnostic {
  case_id: string;
  case_name: string;
  category: FailureCategory;
  symptoms: string[];
  root_cause: string;
  target_node_id?: string;
  remedy_suggestion: string;
  recommended_mutator: string;
  confidence: number;
}

export interface Candidate {
  id: "A" | "B" | "C";
  name: string;
  tag: string;
  generation: number;
  description: string;
  scorecard: Scorecard;
  mutator_applied: string;
  targeted_node: string;
  prompt_diff?: {
    original: string;
    mutated: string;
  };
  config_diff?: {
    original: string;
    mutated: string;
  };
  win_rate: number;
  status: "baseline" | "pareto_dominant" | "verified_champion";
}

export interface LineageNode {
  id: string;
  label: string;
  version: string;
  generation: number;
  accuracy: number;
  mutation: string;
  status: "baseline" | "candidate" | "promoted" | "rejected";
  parentId?: string;
  notes: string;
}

export interface HeldOutCaseResult {
  case_id: string;
  name: string;
  phenomenon: string;
  passed: boolean;
  latency_ms: number;
  ground_truth: string;
  actual_output: string;
  notes: string;
}

export interface HeldOutValidationData {
  split_name: string;
  total_cases: number;
  passed_cases: number;
  accuracy: number;
  reliability: number;
  air_gap_checksum: string;
  leakage_detected: boolean;
  generalization_gap: number;
  promotion_decision: "PROMOTED" | "REQUIRES_REVIEW" | "REJECTED";
  rationale: string[];
  cases: HeldOutCaseResult[];
}

export interface NeatlogsSpan {
  span_id: string;
  name: string;
  kind: "dag" | "node" | "tool" | "verifier" | "llm";
  status: "ok" | "error" | "warn";
  start_offset_ms: number;
  duration_ms: number;
  tokens?: number;
  cost_usd?: number;
  attributes: Record<string, string | number | boolean>;
}

export interface NeatlogsTrace {
  trace_id: string;
  architecture_id: string;
  status: "success" | "warning" | "error";
  total_duration_ms: number;
  total_tokens: number;
  total_cost_usd: number;
  timestamp: string;
  spans: NeatlogsSpan[];
}
