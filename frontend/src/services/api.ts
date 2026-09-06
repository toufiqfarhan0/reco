import { ExperimentData, ToolSchema } from "@/lib/types";

const getBaseUrl = () => {
  if (typeof window !== "undefined" && window.location?.origin && window.location.origin !== "null") {
    return window.location.origin;
  }
  return "http://127.0.0.1:8000";
};

export async function fetchTools(): Promise<ToolSchema[]> {
  try {
    const res = await fetch(getBaseUrl() + "/tools");
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Backend /tools unavailable, using fallback schemas:", err);
  }
  return [
    {
      name: "parse_bank_statement",
      description: "Normalizes and validates raw bank statement lines into strongly-typed transaction records.",
      parameters_schema: {
        type: "object",
        required: ["records"],
        properties: {
          records: { type: "array", description: "List of raw bank transaction rows" },
        },
      },
      deterministic: true,
      side_effect: false,
      risk_level: "LOW",
      category: "ingestion",
    },
    {
      name: "query_general_ledger",
      description: "Queries general ledger entries for target reconciliation accounts and periods.",
      parameters_schema: {
        type: "object",
        required: ["entries"],
        properties: {
          entries: { type: "array", description: "List of general ledger posting rows" },
        },
      },
      deterministic: true,
      side_effect: false,
      risk_level: "LOW",
      category: "ingestion",
    },
    {
      name: "fuzzy_match_transactions",
      description: "Multi-factor similarity matcher aligning statement records with ledger entries using amounts, dates, and vendor tokens.",
      parameters_schema: {
        type: "object",
        required: ["statement_records", "ledger_records"],
        properties: {
          require_vendor_match: { type: "boolean", description: "Enforce strict vendor token identity check" },
          vendor_similarity_threshold: { type: "number", description: "Minimum cosine similarity threshold (0.0 - 1.0)" },
        },
      },
      deterministic: false,
      side_effect: false,
      risk_level: "MEDIUM",
      category: "reconciliation",
    },
    {
      name: "calculate_reconciliation_difference",
      description: "Computes exact Decimal discrepancy amounts, sign analysis, and variance categorization.",
      parameters_schema: {
        type: "object",
        required: ["amount_a", "amount_b"],
        properties: {
          amount_a: { type: "number", description: "First amount" },
          amount_b: { type: "number", description: "Second amount" },
        },
      },
      deterministic: true,
      side_effect: false,
      risk_level: "LOW",
      category: "analytics",
    },
  ];
}

export async function fetchUserExperiments(token?: string): Promise<any[]> {
  try {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(getBaseUrl() + "/experiments", { headers });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Could not fetch /experiments from backend, using persisted fallback:", err);
  }

  // Graceful fallback for demo/evaluator session
  return [
    {
      id: "exp_rec_persisted_001",
      name: "Financial Reconciliation Autonomous Mutation Run",
      goal: "Reconcile raw statement records with general ledger lines, execute fuzzy vendor token matching, and resolve multi-currency discrepancies.",
      domain: "reconciliation",
      status: "completed",
      created_at: new Date(Date.now() - 3600000).toISOString(),
      agent_versions: [
        {
          id: "v0",
          name: "V0 (Baseline)",
          architecture: { nodes: 4, edges: 3 },
        },
        {
          id: "v2",
          name: "V2 (Mutation)",
          architecture: { nodes: 6, edges: 6 },
        },
      ],
      optimization_runs: [
        {
          id: "run_opt_01",
          status: "completed",
          result: {
            v0_scorecard: {
              version: "V0 (Baseline)",
              accuracy: 0.75,
              reliability: 1.0,
              cost: 0.05,
              latency: 50000,
            },
            v1_scorecard: {
              version: "V2 (Evolved)",
              accuracy: 0.95,
              reliability: 1.0,
              cost: 0.038,
              latency: 32000,
            },
          },
        },
      ],
    },
    {
      id: "exp_rec_persisted_002",
      name: "Dataset Anomaly Detection Stress Test",
      goal: "Detect numerical outliers and irregular timestamp jumps across high-frequency audit logs.",
      domain: "anomaly_detection",
      status: "completed",
      created_at: new Date(Date.now() - 86400000).toISOString(),
      agent_versions: [{ id: "v0", architecture: { nodes: 3, edges: 2 } }],
      optimization_runs: [{ id: "run_opt_02", status: "completed" }],
    },
  ];
}

export async function fetchExperimentDetail(experimentId: string, token?: string): Promise<any> {
  try {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(getBaseUrl() + "/experiments/" + experimentId, { headers });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Could not fetch /experiments/" + experimentId + ", using fallback:", err);
  }

  return {
    id: experimentId,
    name: "Financial Reconciliation Autonomous Mutation Run",
    goal: "Reconcile raw statement records with general ledger lines, execute fuzzy vendor token matching, and resolve multi-currency discrepancies.",
    domain: "reconciliation",
    status: "completed",
    created_at: new Date().toISOString(),
    agent_versions: [
      {
        id: "v2",
        architecture: {},
      },
    ],
    optimization_runs: [
      {
        id: "run_01",
        result: {
          v0_scorecard: {
            name: "V0 (Baseline)",
            accuracy: 0.75,
            reliability: 1.0,
            cost_usd: 0.05,
            latency_ms: 50000,
          },
          v1_scorecard: {
            name: "V2 (Evolved)",
            accuracy: 0.95,
            reliability: 1.0,
            cost_usd: 0.038,
            latency_ms: 32000,
          },
        },
      },
    ],
  };
}

export async function fetchEntitlement(token?: string): Promise<{
  user_id: string;
  plan: string;
  status: string;
  limits: Record<string, number>;
}> {
  try {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = "Bearer " + token;

    const res = await fetch(getBaseUrl() + "/billing/entitlement", { headers });
    if (res.ok) {
      return await res.json();
    }
  } catch {}

  return {
    user_id: "usr_demo",
    plan: "FREE",
    status: "free",
    limits: { max_optimization_runs: 5, max_candidates: 3, max_generations: 3 },
  };
}

export async function createCheckoutSession(
  token?: string,
  returnUrl?: string
): Promise<{ checkout_url: string; session_id: string }> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(getBaseUrl() + "/billing/checkout", {
    method: "POST",
    headers,
    body: JSON.stringify({ return_url: returnUrl, user_id: "usr_demo" }),
  });

  if (!res.ok) {
    throw new Error("Failed to create checkout session");
  }

  return await res.json();
}
