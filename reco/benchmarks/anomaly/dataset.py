"""Multi-case benchmark dataset for System Anomaly Detection.

Strictly split into 6 optimization cases and 4 held-out cases with zero cross-split leakage.
Covers:
- Metric time-series analysis (Z-score surge and trends)
- Threshold alerts (warning and critical breaches)
- Root-cause diagnosis (log error bursts and cascade isolation)
- Multi-metric correlation and system health checks
"""

from __future__ import annotations

from typing import List
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite


def create_anomaly_benchmark_cases() -> List[BenchmarkCase]:
    """Instantiate the 10 canonical benchmark test cases for system anomaly detection."""
    cases: List[BenchmarkCase] = []

    # =========================================================================
    # OPTIMIZATION SPLIT (6 Cases)
    # =========================================================================

    # 1. Single Metric Sudden Spike (Time Series)
    cases.append(BenchmarkCase(
        case_id="anom_opt_001_cpu_spike",
        name="CPU Metric Time-Series Spike",
        description="CPU utilization time series experiencing an isolated spike exceeding statistical Z-score threshold.",
        category="metric_time_series",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "values": [22.0, 24.0, 23.5, 25.0, 24.2, 98.5, 23.8, 24.5, 25.2, 23.9],
            "threshold": 2.5
        },
        expected_output={
            "status": "anomaly_detected",
            "has_anomaly": True,
            "anomaly_count": 1,
            "anomaly_indices": [5]
        },
        metadata={"difficulty": "easy", "domain": "system_anomaly", "split_target": "optimization"}
    ))

    # 2. Critical Threshold Breach (System Health)
    cases.append(BenchmarkCase(
        case_id="anom_opt_002_memory_threshold_critical",
        name="Memory Utilization Critical Threshold Breach",
        description="Multi-metric server resource monitoring where memory crosses the critical 90% alert boundary.",
        category="threshold_alerts",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "metrics": {"cpu_percent": 45.2, "memory_percent": 94.5, "disk_percent": 62.0},
            "thresholds": {
                "cpu_percent": {"warning": 80.0, "critical": 90.0},
                "memory_percent": {"warning": 85.0, "critical": 90.0},
                "disk_percent": {"warning": 80.0, "critical": 90.0}
            }
        },
        expected_output={
            "status": "critical",
            "is_healthy": False,
            "critical_count": 1,
            "warning_count": 0,
            "breach_count": 1
        },
        metadata={"difficulty": "easy", "domain": "system_anomaly", "split_target": "optimization"}
    ))

    # 3. Database Timeout Log Burst (Root Cause Diagnosis)
    cases.append(BenchmarkCase(
        case_id="anom_opt_003_database_timeout_log_burst",
        name="Database Timeout Log Error Burst",
        description="Log stream analysis isolating connection pool exhaustion and DatabaseConnectionTimeout root cause.",
        category="root_cause_diagnosis",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "logs": [
                "2026-04-01 10:00:01 [INFO] [web-gateway] Handled GET /api/v1/orders in 45ms",
                "2026-04-01 10:00:03 [ERROR] [order-service] DatabaseConnectionTimeout: query failed after 30000ms",
                "2026-04-01 10:00:04 [ERROR] [order-service] DatabaseConnectionTimeout: unable to acquire connection pool slot",
                "2026-04-01 10:00:05 [CRITICAL] [order-service] DatabaseConnectionTimeout: pool exhausted, failing requests",
                "2026-04-01 10:00:06 [WARN] [web-gateway] Upstream returned 504 Gateway Timeout"
            ],
            "min_level": "WARN"
        },
        expected_output={
            "status": "errors_detected",
            "error_count": 2,
            "critical_count": 1,
            "warning_count": 1,
            "root_cause_candidate": "DatabaseConnectionTimeout"
        },
        metadata={"difficulty": "medium", "domain": "system_anomaly", "split_target": "optimization"}
    ))

    # 4. Healthy Baseline Normal Operations
    cases.append(BenchmarkCase(
        case_id="anom_opt_004_healthy_baseline_metrics",
        name="Healthy Baseline Normal Operations",
        description="System operating safely within all threshold boundaries with zero error events.",
        category="threshold_alerts",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "metrics": {"cpu_percent": 35.0, "memory_percent": 52.0, "disk_percent": 41.0},
            "thresholds": {
                "cpu_percent": {"warning": 80.0, "critical": 90.0},
                "memory_percent": {"warning": 80.0, "critical": 90.0},
                "disk_percent": {"warning": 80.0, "critical": 90.0}
            }
        },
        expected_output={
            "status": "healthy",
            "is_healthy": True,
            "critical_count": 0,
            "warning_count": 0,
            "breach_count": 0
        },
        metadata={"difficulty": "easy", "domain": "system_anomaly", "split_target": "optimization"}
    ))

    # 5. Correlated Multi-Metric Degradation
    cases.append(BenchmarkCase(
        case_id="anom_opt_005_multi_metric_correlation",
        name="Correlated Multi-Metric Degradation",
        description="Concurrent latency surge and error rate spikes indicating system saturation.",
        category="multi_metric_correlation",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "metrics": {"cpu_percent": 88.0, "latency_ms": 520.0, "error_rate": 0.08},
            "thresholds": {
                "cpu_percent": {"warning": 80.0, "critical": 95.0},
                "latency_ms": {"warning": 200.0, "critical": 500.0},
                "error_rate": {"warning": 0.02, "critical": 0.05}
            }
        },
        expected_output={
            "status": "critical",
            "is_healthy": False,
            "critical_count": 2,
            "warning_count": 1,
            "breach_count": 3
        },
        metadata={"difficulty": "hard", "domain": "system_anomaly", "split_target": "optimization"}
    ))

    # 6. Multi-Service OutOfMemory Cascade
    cases.append(BenchmarkCase(
        case_id="anom_opt_006_distributed_log_exceptions",
        name="Multi-Service OutOfMemory Cascade",
        description="Auth service memory exhaustion triggering authentication failures across dependent services.",
        category="root_cause_diagnosis",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "logs": [
                "2026-04-01 11:15:00 [ERROR] [auth-service] OutOfMemoryError: Java heap space",
                "2026-04-01 11:15:02 [ERROR] [auth-service] OutOfMemoryError: GC overhead limit exceeded",
                "2026-04-01 11:15:05 [WARN] [gateway] Auth token verification degraded"
            ]
        },
        expected_output={
            "status": "errors_detected",
            "error_count": 2,
            "critical_count": 0,
            "warning_count": 1,
            "root_cause_candidate": "OutOfMemoryError"
        },
        metadata={"difficulty": "medium", "domain": "system_anomaly", "split_target": "optimization"}
    ))

    # =========================================================================
    # HELD-OUT SPLIT (4 Cases)
    # =========================================================================

    # 7. Held-Out Univariate Z-Score Anomaly
    cases.append(BenchmarkCase(
        case_id="anom_held_001_univariate_zscore_boundary",
        name="Held-Out Univariate Z-Score Anomaly",
        description="Air-gapped verification of time-series outlier isolation on index 8.",
        category="metric_time_series",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "values": [10.0, 10.5, 9.8, 10.2, 10.1, 9.9, 10.3, 10.0, 42.0, 10.2],
            "threshold": 2.5
        },
        expected_output={
            "status": "anomaly_detected",
            "has_anomaly": True,
            "anomaly_count": 1,
            "anomaly_indices": [8]
        },
        metadata={"difficulty": "medium", "domain": "system_anomaly", "split_target": "held-out"}
    ))

    # 8. Held-Out Dual Critical Threshold Alerts
    cases.append(BenchmarkCase(
        case_id="anom_held_002_dual_critical_breaches",
        name="Held-Out Dual Critical Threshold Alerts",
        description="Air-gapped verification of compound low-disk and high-connection critical threshold alerts.",
        category="threshold_alerts",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "metrics": {"disk_free_gb": 2.0, "connection_count": 1500.0},
            "thresholds": {
                "disk_free_gb": {"critical": 5.0, "operator": "<="},
                "connection_count": {"critical": 1000.0, "operator": ">="}
            }
        },
        expected_output={
            "status": "critical",
            "is_healthy": False,
            "critical_count": 2,
            "breach_count": 2
        },
        metadata={"difficulty": "medium", "domain": "system_anomaly", "split_target": "held-out"}
    ))

    # 9. Held-Out Payment Failure Root-Cause Analysis
    cases.append(BenchmarkCase(
        case_id="anom_held_003_payment_gateway_502_cascade",
        name="Held-Out Payment Failure Root-Cause Analysis",
        description="Air-gapped verification identifying ConnectionTimeout as the root cause candidate.",
        category="root_cause_diagnosis",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "logs": [
                "2026-04-02 14:00:10 [ERROR] [payment-processor] ConnectionTimeout: SSL handshake to banking provider failed",
                "2026-04-02 14:00:12 [ERROR] [payment-processor] ConnectionTimeout: read timed out",
                "2026-04-02 14:00:15 [ERROR] [payment-processor] ConnectionTimeout: connection refused on port 443"
            ],
            "min_level": "ERROR"
        },
        expected_output={
            "status": "errors_detected",
            "error_count": 3,
            "root_cause_candidate": "ConnectionTimeout"
        },
        metadata={"difficulty": "medium", "domain": "system_anomaly", "split_target": "held-out"}
    ))

    # 10. Held-Out Clean Multi-Service Health Audit
    cases.append(BenchmarkCase(
        case_id="anom_held_004_all_clear_audit",
        name="Held-Out Multi-Service Clean Health Check",
        description="Air-gapped verification proving zero false-positive alerts on balanced workload telemetry.",
        category="threshold_alerts",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "metrics": {"cpu_percent": 18.5, "memory_percent": 42.1, "io_wait": 0.4},
            "thresholds": {
                "cpu_percent": {"warning": 75.0, "critical": 90.0},
                "memory_percent": {"warning": 75.0, "critical": 90.0},
                "io_wait": {"warning": 5.0, "critical": 10.0}
            }
        },
        expected_output={
            "status": "healthy",
            "is_healthy": True,
            "critical_count": 0,
            "warning_count": 0,
            "breach_count": 0
        },
        metadata={"difficulty": "easy", "domain": "system_anomaly", "split_target": "held-out"}
    ))

    return cases


def get_anomaly_benchmark_suite() -> BenchmarkSuite:
    """Build and validate the standard 10-case system anomaly benchmark suite."""
    cases = create_anomaly_benchmark_cases()
    suite = BenchmarkSuite(
        name="system_anomaly_benchmark_v1",
        description="Standard 10-case system anomaly detection benchmark partitioned 6/4 (opt/held-out).",
        cases=cases
    )
    # Strictly validate partition isolation
    suite.validate_partition_isolation()
    return suite
