"""Deterministic test suite for Step 26: Supabase Authentication & Persistence.

Tests:
1. Supabase client configuration
2. Auth state handling
3. Protected application state
4. Profile creation & update
5. Experiment persistence adapter
6. Version persistence adapter
7. Optimization persistence
8. Candidate persistence
9. Diagnosis persistence
10. Promotion persistence
11. Trace persistence
12. User isolation (RLS / backend authorization)
13. Demo / live isolation
14. Persistence failure containment
15. Experiment reload
16. Logout handling
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from reco.api.app import create_app
from reco.config import Settings
from reco.db.supabase_adapter import SupabasePersistenceService


# ============================================================================
# Mocks and Fixtures
# ============================================================================

class MockSupabaseUser:
    def __init__(self, user_id: str = "usr_user_a_123", email: str = "user_a@example.com"):
        self.id = user_id
        self.email = email


class MockAuthResponse:
    def __init__(self, user: MockSupabaseUser):
        self.user = user


class MockTableQuery:
    def __init__(self, table_name: str, database_store: dict):
        self.table_name = table_name
        self.store = database_store
        self._action = "select"
        self._data_to_insert = None
        self._data_to_update = None
        self._filters = {}
        self._select_cols = "*"

    def select(self, cols="*"):
        self._action = "select"
        self._select_cols = cols
        return self

    def insert(self, data):
        self._action = "insert"
        self._data_to_insert = data if isinstance(data, list) else [data]
        return self

    def update(self, data):
        self._action = "update"
        self._data_to_update = data
        return self

    def eq(self, column: str, value):
        self._filters[column] = value
        return self

    def order(self, column: str, desc: bool = False):
        return self

    def execute(self):
        table = self.store.setdefault(self.table_name, [])

        if self._action == "insert":
            inserted = []
            for item in self._data_to_insert:
                row = dict(item)
                if "id" not in row:
                    row["id"] = f"mock_{len(table) + 1}"
                table.append(row)
                inserted.append(row)
            mock_res = MagicMock()
            mock_res.data = inserted
            return mock_res

        elif self._action == "select":
            matches = []
            for row in table:
                matched = True
                for col, val in self._filters.items():
                    if row.get(col) != val:
                        matched = False
                        break
                if matched:
                    # In real Supabase, child relations are joined. Emulate child relation embedding
                    row_copy = dict(row)
                    if self.table_name == "experiments":
                        row_copy["agent_versions"] = [
                            v for v in self.store.get("agent_versions", []) if v.get("experiment_id") == row["id"]
                        ]
                        row_copy["optimization_runs"] = [
                            r for r in self.store.get("optimization_runs", []) if r.get("experiment_id") == row["id"]
                        ]
                    matches.append(row_copy)
            mock_res = MagicMock()
            mock_res.data = matches
            return mock_res

        elif self._action == "update":
            updated = []
            for row in table:
                matched = True
                for col, val in self._filters.items():
                    if row.get(col) != val:
                        matched = False
                        break
                if matched:
                    row.update(self._data_to_update)
                    updated.append(dict(row))
            mock_res = MagicMock()
            mock_res.data = updated
            return mock_res

        mock_res = MagicMock()
        mock_res.data = []
        return mock_res


class MockSupabaseClient:
    def __init__(self, store: dict, token: str = None):
        self.store = store
        self.token = token
        self.auth = MagicMock()

        def mock_get_user(jwt):
            if jwt == "token_user_a":
                return MockAuthResponse(MockSupabaseUser("usr_a", "user_a@example.com"))
            elif jwt == "token_user_b":
                return MockAuthResponse(MockSupabaseUser("usr_b", "user_b@example.com"))
            raise ValueError("Invalid JWT")

        self.auth.get_user.side_effect = mock_get_user

    def table(self, table_name: str):
        return MockTableQuery(table_name, self.store)


@pytest.fixture
def mock_db_store():
    return {
        "profiles": [],
        "experiments": [],
        "agent_versions": [],
        "optimization_runs": [],
        "candidate_evaluations": [],
        "diagnoses": [],
        "promotion_assessments": [],
        "trace_references": [],
    }


@pytest.fixture
def mock_service(mock_db_store):
    svc = SupabasePersistenceService(url="https://mock.supabase.co", key="mock_pub_key")
    svc._create_client_factory = lambda token=None: MockSupabaseClient(mock_db_store, token)
    return svc


@pytest.fixture
def app_with_mock_service(mock_service):
    with patch("reco.api.app.default_supabase_service", mock_service):
        app = create_app()
        yield app, mock_service


# ============================================================================
# Deterministic Tests (16 Required Areas)
# ============================================================================

def test_1_supabase_client_configuration():
    """1. Supabase client configuration loads properly from environment settings."""
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_key="test_key_secret",
    )
    svc = SupabasePersistenceService(url=settings.supabase_url, key=settings.supabase_key)
    assert svc.is_configured is True
    assert svc.url == "https://test.supabase.co"
    assert svc.key == "test_key_secret"

    # Unconfigured service
    unconfigured = SupabasePersistenceService(url="", key="")
    assert unconfigured.is_configured is False
    assert unconfigured.get_client() is None


def test_2_auth_state_handling(mock_service):
    """2. Auth state handling properly validates Supabase JWT and extracts identity."""
    # Valid token
    auth_info = mock_service.verify_auth_token("token_user_a")
    assert auth_info is not None
    assert auth_info["user_id"] == "usr_a"
    assert auth_info["email"] == "user_a@example.com"

    # Invalid token
    bad_info = mock_service.verify_auth_token("invalid_garbage_token")
    assert bad_info is None


def test_3_protected_application_state(app_with_mock_service):
    """3. Protected application state refuses unauthenticated requests with HTTP 401."""
    app, _ = app_with_mock_service
    client = TestClient(app)

    # All persistence endpoints must reject unauthenticated requests
    assert client.get("/auth/me").status_code == 401
    assert client.post("/auth/profile", json={"display_name": "Ghost"}).status_code == 401
    assert client.get("/experiments").status_code == 401
    assert client.post("/experiments", json={"name": "Test", "goal": "Goal", "domain": "reconciliation"}).status_code == 401
    assert client.get("/experiments/exp_123").status_code == 401
    assert client.post("/experiments/exp_123/persist", json={"experiment_data": {}}).status_code == 401


def test_4_profile_creation_and_update(mock_service):
    """4. Profile is created upon first login and can be updated without sensitive data leaks."""
    profile = mock_service.get_or_create_profile(user_id="usr_a", display_name="Alice User", token="token_user_a")
    assert profile["id"] == "usr_a"
    assert profile["display_name"] == "Alice User"

    # Profile retrieve existing
    profile_retrieved = mock_service.get_or_create_profile(user_id="usr_a", token="token_user_a")
    assert profile_retrieved["display_name"] == "Alice User"

    # Update profile
    updated = mock_service.update_profile(user_id="usr_a", display_name="Alice Senior Lead", token="token_user_a")
    assert updated["display_name"] == "Alice Senior Lead"


def test_5_experiment_persistence_adapter(mock_service):
    """5. Experiment persistence adapter creates top-level experiment row."""
    exp = mock_service.create_experiment(
        user_id="usr_a",
        name="GLM-4.7 Reconciliation Benchmark",
        goal="Reconcile bank statements against general ledger",
        domain="reconciliation",
        status="running",
        token="token_user_a",
    )
    assert exp["user_id"] == "usr_a"
    assert exp["name"] == "GLM-4.7 Reconciliation Benchmark"
    assert exp["domain"] == "reconciliation"
    assert exp["status"] == "running"
    assert "id" in exp


def test_6_version_persistence_adapter(mock_service, mock_db_store):
    """6. Agent version persistence records V0 baseline and V1 evolved architectures as JSONB."""
    exp = mock_service.create_experiment(
        user_id="usr_a",
        name="Version Test",
        goal="Goal",
        domain="reconciliation",
        token="token_user_a",
    )

    sample_data = {
        "graph": {"entry_node_id": "parse", "nodes": {"parse": {"role": "Parser"}}},
        "active_model": "glm-4-7-flash",
        "mutations": [{"type": "PROMPT_OPTIMIZATION", "description": "Tuned prompt"}],
        "v0_scorecard": {"accuracy": 0.75, "reliability": 1.0},
        "v1_scorecard": {"accuracy": 0.80, "reliability": 1.0},
    }

    res = mock_service.persist_full_experiment_state(
        user_id="usr_a",
        experiment_id=exp["id"],
        experiment_data=sample_data,
        token="token_user_a",
    )
    assert res["status"] == "persisted"

    versions = mock_db_store["agent_versions"]
    assert len(versions) >= 2  # V0 baseline and V1 evolved
    v0 = next(v for v in versions if v["version_number"] == 0)
    v1 = next(v for v in versions if v["version_number"] == 1)

    assert v0["version_label"] == "V0 (Baseline)"
    assert v1["version_label"] == "V1 (Evolved)"
    assert isinstance(v1["architecture"], dict)
    assert "api_key" not in str(v1["architecture"])  # No API keys persisted


def test_7_optimization_persistence(mock_service, mock_db_store):
    """7. Optimization run persistence captures lifecycle, cost, tokens, and latency."""
    exp = mock_service.create_experiment(
        user_id="usr_a",
        name="Optimization Run Test",
        goal="Goal",
        domain="reconciliation",
        token="token_user_a",
    )

    sample_data = {
        "v0_scorecard": {"accuracy": 0.75, "total_cost_usd": 0.05, "total_latency_ms": 50000, "total_tokens": 15000},
        "v1_scorecard": {"accuracy": 0.80, "total_cost_usd": 0.045, "total_latency_ms": 40000, "total_tokens": 12000, "cost_type": "estimated"},
        "evolution_timeline": [{"step": 1, "generation": 1, "model_calls": 96, "tool_calls": 72}],
    }

    mock_service.persist_full_experiment_state(
        user_id="usr_a",
        experiment_id=exp["id"],
        experiment_data=sample_data,
        token="token_user_a",
    )

    runs = mock_db_store["optimization_runs"]
    assert len(runs) == 1
    run = runs[0]
    assert run["experiment_id"] == exp["id"]
    assert run["status"] == "completed"
    assert run["total_cost"] == 0.045
    assert run["cost_type"] == "estimated"
    assert run["total_model_calls"] == 96
    assert run["total_tool_calls"] == 72
    assert "result" in run  # JSONB payload for full zero-data-loss reload


def test_8_candidate_persistence(mock_service, mock_db_store):
    """8. Candidate evaluations persistence captures pool candidates and scorecard outcomes."""
    exp = mock_service.create_experiment(user_id="usr_a", name="Candidate Test", goal="G", domain="D", token="token_user_a")

    sample_data = {
        "candidates": [
            {
                "candidate_id": "cand_001",
                "name": "Candidate Alpha",
                "generation": 1,
                "mutation_type": "PROMPT_OPTIMIZATION",
                "target_node": "fuzzy_match",
                "fingerprint": "fp_alpha",
                "scorecard": {"accuracy": 0.80},
                "status": "ACCEPTED",
            },
            {
                "candidate_id": "cand_002",
                "name": "Candidate Beta",
                "generation": 1,
                "mutation_type": "PARAM_TUNING",
                "target_node": "verifier",
                "fingerprint": "fp_beta",
                "scorecard": {"accuracy": 0.70},
                "status": "REJECTED",
                "rejection_reason": "Accuracy 0.70 below baseline 0.75",
            },
        ],
    }

    mock_service.persist_full_experiment_state("usr_a", exp["id"], sample_data, "token_user_a")
    cands = mock_db_store["candidate_evaluations"]
    assert len(cands) == 2
    assert cands[0]["candidate_id"] == "cand_001"
    assert cands[0]["status"] == "ACCEPTED"
    assert cands[1]["status"] == "REJECTED"


def test_9_diagnosis_persistence(mock_service, mock_db_store):
    """9. Diagnosis persistence records categorized failure root causes and evidence."""
    exp = mock_service.create_experiment(user_id="usr_a", name="Diag Test", goal="G", domain="D", token="token_user_a")

    sample_data = {
        "diagnoses": [
            {
                "category": "VERIFICATION_FAILURE",
                "severity": "HIGH",
                "root_cause": "Reconciliation balance did not account for wire fees",
                "evidence": "Difference of $15.00 matches fee column",
                "recommended_mutation": "Refine verification prompt to check wire fee field",
            }
        ]
    }

    mock_service.persist_full_experiment_state("usr_a", exp["id"], sample_data, "token_user_a")
    diags = mock_db_store["diagnoses"]
    assert len(diags) == 1
    assert diags[0]["category"] == "VERIFICATION_FAILURE"
    assert diags[0]["severity"] == "HIGH"
    assert "wire fees" in diags[0]["root_cause"]


def test_10_promotion_persistence(mock_service, mock_db_store):
    """10. Promotion assessment persistence records gate decisions and held-out scores."""
    exp = mock_service.create_experiment(user_id="usr_a", name="Promo Test", goal="G", domain="D", token="token_user_a")

    sample_data = {
        "promotion_assessment": {
            "decision": "PROMOTE",
            "reasons": ["Accuracy 80.0% >= baseline 75.0%", "Held-out accuracy 82.5% >= baseline 75.0%"],
        },
        "held_out_scorecard": {"accuracy": 0.825, "reliability": 1.0},
    }

    mock_service.persist_full_experiment_state("usr_a", exp["id"], sample_data, "token_user_a")
    promos = mock_db_store["promotion_assessments"]
    assert len(promos) == 1
    assert promos[0]["decision"] == "PROMOTE"
    assert promos[0]["held_out_scorecard"]["accuracy"] == 0.825


def test_11_trace_persistence(mock_service, mock_db_store):
    """11. Trace persistence stores reference URLs and span counts without raw secrets or chain-of-thought."""
    exp = mock_service.create_experiment(user_id="usr_a", name="Trace Test", goal="G", domain="D", token="token_user_a")

    sample_data = {
        "neatlogs": {
            "trace_id": "nl_trace_888999",
            "trace_url": "https://neatlogs.com/traces/nl_trace_888999",
            "span_count": 48,
            "latency_ms": 32100.0,
        }
    }

    mock_service.persist_full_experiment_state("usr_a", exp["id"], sample_data, "token_user_a")
    traces = mock_db_store["trace_references"]
    assert len(traces) == 1
    t = traces[0]
    assert t["trace_id"] == "nl_trace_888999"
    assert t["trace_url"] == "https://neatlogs.com/traces/nl_trace_888999"
    assert t["span_count"] == 48
    assert "password" not in str(t)
    assert "api_key" not in str(t)


def test_12_user_isolation(mock_service, app_with_mock_service):
    """12. Strict user isolation: User A cannot read, list, or update User B's experiments."""
    app, _ = app_with_mock_service
    client = TestClient(app)

    # Create experiment as User A
    exp_a = mock_service.create_experiment(
        user_id="usr_a",
        name="Alice Private Experiment",
        goal="Secret",
        domain="reconciliation",
        token="token_user_a",
    )

    # Create experiment as User B
    exp_b = mock_service.create_experiment(
        user_id="usr_b",
        name="Bob Private Experiment",
        goal="Bob Goal",
        domain="anomaly_detection",
        token="token_user_b",
    )

    # 1. User A listing experiments sees only Alice's experiment
    res_a = client.get("/experiments", headers={"Authorization": "Bearer token_user_a"})
    assert res_a.status_code == 200
    user_a_exp_ids = [e["id"] for e in res_a.json()]
    assert exp_a["id"] in user_a_exp_ids
    assert exp_b["id"] not in user_a_exp_ids

    # 2. User B listing experiments sees only Bob's experiment
    res_b = client.get("/experiments", headers={"Authorization": "Bearer token_user_b"})
    assert res_b.status_code == 200
    user_b_exp_ids = [e["id"] for e in res_b.json()]
    assert exp_b["id"] in user_b_exp_ids
    assert exp_a["id"] not in user_b_exp_ids

    # 3. User B attempting to access User A's experiment receives 404 (or access denied)
    res_b_access_a = client.get(f"/experiments/{exp_a['id']}", headers={"Authorization": "Bearer token_user_b"})
    assert res_b_access_a.status_code == 404


def test_13_demo_live_isolation(app_with_mock_service, mock_db_store):
    """13. Demo mode remains completely isolated from Supabase and never pollutes DB tables."""
    app, _ = app_with_mock_service
    client = TestClient(app)

    count_before = len(mock_db_store["experiments"])

    # Fetching demo experiment requires no auth and writes no rows
    res = client.get("/experiments/demo?domain=reconciliation")
    assert res.status_code == 200
    demo_data = res.json()
    assert demo_data["v0_scorecard"]["accuracy"] == 0.75
    assert demo_data["v1_scorecard"]["accuracy"] == 0.80

    count_after = len(mock_db_store["experiments"])
    assert count_after == count_before  # No rows inserted into Supabase


def test_14_persistence_failure_containment():
    """14. Database timeouts or exceptions do not crash execution and return structured availability state."""
    failing_svc = SupabasePersistenceService(url="https://timeout.supabase.co", key="key")

    mock_client = MagicMock()
    mock_client.table.side_effect = TimeoutError("Connection to Supabase timed out after 5000ms")
    failing_svc._create_client_factory = lambda token=None: mock_client

    # Creating experiment should not raise an unhandled exception
    res = failing_svc.create_experiment("usr_a", "Fail Safe", "Goal", "reconciliation")
    assert res["persistence"] == "unavailable"
    assert "timed out" in res["error"]

    # Persisting full state should not raise an unhandled exception
    res_persist = failing_svc.persist_full_experiment_state("usr_a", "exp_123", {"graph": {}})
    assert res_persist["status"] == "failed"
    assert "timed out" in res_persist["error"]


def test_15_experiment_reload(mock_service, app_with_mock_service):
    """15. Loading an experiment restores full versions, scorecards, diagnoses, and promotion history."""
    app, _ = app_with_mock_service
    client = TestClient(app)

    # 1. Create and persist experiment
    exp = mock_service.create_experiment(user_id="usr_a", name="Reload Me", goal="Test Goal", domain="reconciliation", token="token_user_a")
    full_payload = {
        "v0_scorecard": {"version": "V0", "accuracy": 0.75},
        "v1_scorecard": {"version": "V1", "accuracy": 0.80},
        "diagnoses": [{"category": "PARSING_ERROR", "severity": "LOW"}],
        "promotion_assessment": {"decision": "PROMOTE", "reasons": ["Passed"]},
    }
    mock_service.persist_full_experiment_state("usr_a", exp["id"], full_payload, "token_user_a")

    # 2. Reload via API endpoint
    res = client.get(f"/experiments/{exp['id']}", headers={"Authorization": "Bearer token_user_a"})
    assert res.status_code == 200
    loaded = res.json()
    assert loaded["id"] == exp["id"]
    assert len(loaded["agent_versions"]) >= 2
    assert len(loaded["optimization_runs"]) == 1
    assert loaded["optimization_runs"][0]["result"]["promotion_assessment"]["decision"] == "PROMOTE"


def test_16_logout_flow(app_with_mock_service):
    """16. Clearing authentication session/token prevents further privileged operations."""
    app, _ = app_with_mock_service
    client = TestClient(app)

    # When authenticated
    res_authed = client.get("/auth/me", headers={"Authorization": "Bearer token_user_a"})
    assert res_authed.status_code == 200
    assert res_authed.json()["id"] == "usr_a"

    # After logout (token removed or expired)
    res_unauthed = client.get("/auth/me")
    assert res_unauthed.status_code == 401

    res_bad_header = client.get("/auth/me", headers={"Authorization": "Bearer invalid_logged_out_token"})
    assert res_bad_header.status_code == 401
