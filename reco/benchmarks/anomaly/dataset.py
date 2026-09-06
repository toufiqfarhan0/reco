"""Deterministic synthetic benchmark cases for Dataset Anomaly Detection (Domain B)."""

from typing import List, Optional
from reco.benchmarks.anomaly.models import AnomalyCase, AnomalyGroundTruth

BENCHMARK_NAME = "anomaly_detection"
BENCHMARK_VERSION = "anomaly_detection-v1"


def get_optimization_cases() -> List[AnomalyCase]:
    """Return the 5 canonical optimization cases for Domain B."""
    return [
        # 1. ANOM-OPT-01: Obvious numerical outlier
        AnomalyCase(
            case_code="ANOM-OPT-01",
            name="Severe Numerical Temperature Outlier",
            description="Industrial temperature monitoring dataset with one extreme sensor value (950°C vs 22-25°C normal).",
            split="optimization",
            dataset=[
                {"id": "rec_01", "timestamp": "2026-03-01T08:00:00", "temperature": 22.4, "pressure": 101.3, "status": "normal"},
                {"id": "rec_02", "timestamp": "2026-03-01T08:05:00", "temperature": 23.1, "pressure": 101.5, "status": "normal"},
                {"id": "rec_03", "timestamp": "2026-03-01T08:10:00", "temperature": 950.0, "pressure": 101.4, "status": "normal"},  # ANOMALY
                {"id": "rec_04", "timestamp": "2026-03-01T08:15:00", "temperature": 22.8, "pressure": 101.2, "status": "normal"},
                {"id": "rec_05", "timestamp": "2026-03-01T08:20:00", "temperature": 23.5, "pressure": 101.6, "status": "normal"},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=["rec_03"],
                expected_types={"rec_03": "numerical_outlier"},
                required_explanations=["temperature", "950", "outlier"],
            ),
            difficulty="easy",
        ),

        # 2. ANOM-OPT-02: Temporal anomaly (midnight activity spike)
        AnomalyCase(
            case_code="ANOM-OPT-02",
            name="Off-Hours Authentication Timestamp Spike",
            description="Office building access log where access occurs at 03:15 AM on Sunday outside approved hours.",
            split="optimization",
            dataset=[
                {"id": "rec_11", "timestamp": "2026-03-02T09:02:14", "user_id": "usr_402", "hour": 9, "day": "Monday", "bytes_transferred": 1200},
                {"id": "rec_12", "timestamp": "2026-03-02T11:15:00", "user_id": "usr_105", "hour": 11, "day": "Monday", "bytes_transferred": 3400},
                {"id": "rec_13", "timestamp": "2026-03-02T14:30:22", "user_id": "usr_882", "hour": 14, "day": "Monday", "bytes_transferred": 2100},
                {"id": "rec_14", "timestamp": "2026-03-01T03:15:44", "user_id": "usr_009", "hour": 3, "day": "Sunday", "bytes_transferred": 98000},  # ANOMALY
                {"id": "rec_15", "timestamp": "2026-03-02T16:45:10", "user_id": "usr_201", "hour": 16, "day": "Monday", "bytes_transferred": 1850},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=["rec_14"],
                expected_types={"rec_14": "temporal_anomaly"},
                required_explanations=["off-hours", "sunday", "3:15", "bytes_transferred"],
            ),
            difficulty="medium",
        ),

        # 3. ANOM-OPT-03: Categorical anomaly
        AnomalyCase(
            case_code="ANOM-OPT-03",
            name="Unauthorized Categorical Protocol Code",
            description="Network request dataset where one record contains an unlisted, malicious protocol enum.",
            split="optimization",
            dataset=[
                {"id": "rec_21", "service": "auth", "protocol": "HTTPS", "port": 443, "latency": 15},
                {"id": "rec_22", "service": "api", "protocol": "HTTPS", "port": 443, "latency": 22},
                {"id": "rec_23", "service": "db", "protocol": "TCP", "port": 5432, "latency": 8},
                {"id": "rec_24", "service": "cache", "protocol": "TCP", "port": 6379, "latency": 3},
                {"id": "rec_25", "service": "gateway", "protocol": "MALFORMED_EXFIL_PAYLOAD", "port": 9999, "latency": 540},  # ANOMALY
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=["rec_25"],
                expected_types={"rec_25": "categorical_anomaly"},
                required_explanations=["protocol", "MALFORMED_EXFIL_PAYLOAD", "port 9999"],
            ),
            difficulty="easy",
        ),

        # 4. ANOM-OPT-04: Mixed normal records + single subtle anomaly
        AnomalyCase(
            case_code="ANOM-OPT-04",
            name="Mixed Financial Transaction Drift",
            description="Transaction amounts with mean $50.00 and std $5.00, containing one subtle anomaly at $245.00.",
            split="optimization",
            dataset=[
                {"id": "rec_31", "amount": 48.50, "merchant": "Store A", "currency": "USD"},
                {"id": "rec_32", "amount": 52.10, "merchant": "Store B", "currency": "USD"},
                {"id": "rec_33", "amount": 49.90, "merchant": "Store A", "currency": "USD"},
                {"id": "rec_34", "amount": 245.00, "merchant": "Store C", "currency": "USD"},  # ANOMALY (Z ~ 3.9)
                {"id": "rec_35", "amount": 51.00, "merchant": "Store B", "currency": "USD"},
                {"id": "rec_36", "amount": 47.80, "merchant": "Store A", "currency": "USD"},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=["rec_34"],
                expected_types={"rec_34": "numerical_outlier"},
                required_explanations=["amount", "245", "z-score"],
            ),
            difficulty="medium",
        ),

        # 5. ANOM-OPT-05: High-variance legitimate edge case (V0 Failure Case)
        # Without distribution tolerance or statistical IQR check, naive V0 treats this as an anomaly,
        # but it is within the 99th percentile of valid business payroll and should NOT be flagged as an anomaly!
        AnomalyCase(
            case_code="ANOM-OPT-05",
            name="Legitimate High-Variance Payroll Edge Case",
            description="Quarterly executive bonus payroll batch where $15,000 is legitimate and expected.",
            split="optimization",
            dataset=[
                {"id": "rec_41", "employee_type": "engineer", "payout": 4500.0, "is_executive": False},
                {"id": "rec_42", "employee_type": "manager", "payout": 6200.0, "is_executive": False},
                {"id": "rec_43", "employee_type": "executive", "payout": 15000.0, "is_executive": True},  # LEGITIMATE EDGE CASE (NOT AN ANOMALY)
                {"id": "rec_44", "employee_type": "designer", "payout": 4200.0, "is_executive": False},
                {"id": "rec_45", "employee_type": "support", "payout": 3800.0, "is_executive": False},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=[],  # Completely clean: NO anomaly!
                allow_empty=True,
                expected_types={},
                required_explanations=["executive", "bonus", "legitimate", "normal"],
            ),
            difficulty="hard",
            metadata={"intended_v0_failure": "false_positive_on_extreme_value"},
        ),
    ]


def get_held_out_cases() -> List[AnomalyCase]:
    """Return the 3 isolated held-out cases for Domain B regression protection."""
    return [
        # 1. ANOM-HLD-01: Multi-field correlated anomaly
        AnomalyCase(
            case_code="ANOM-HLD-01",
            name="Correlated CPU and Memory Leak Anomaly",
            description="Server metrics where CPU is low but memory usage reaches 99.8% with constant thread spawn.",
            split="held_out",
            dataset=[
                {"id": "hld_01", "cpu_pct": 15.2, "mem_pct": 32.0, "threads": 45},
                {"id": "hld_02", "cpu_pct": 18.0, "mem_pct": 34.5, "threads": 48},
                {"id": "hld_03", "cpu_pct": 14.8, "mem_pct": 99.8, "threads": 2500},  # ANOMALY
                {"id": "hld_04", "cpu_pct": 16.5, "mem_pct": 33.1, "threads": 44},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=["hld_03"],
                expected_types={"hld_03": "correlated_resource_leak"},
                required_explanations=["mem_pct", "threads", "memory leak"],
            ),
            difficulty="medium",
        ),

        # 2. ANOM-HLD-02: Clean normal dataset (zero anomalies)
        AnomalyCase(
            case_code="ANOM-HLD-02",
            name="Clean Sensor Stream",
            description="Completely uniform baseline dataset without any anomalies.",
            split="held_out",
            dataset=[
                {"id": "hld_11", "vibration": 0.021, "rpm": 1800, "status": "OK"},
                {"id": "hld_12", "vibration": 0.024, "rpm": 1805, "status": "OK"},
                {"id": "hld_13", "vibration": 0.022, "rpm": 1798, "status": "OK"},
                {"id": "hld_14", "vibration": 0.023, "rpm": 1802, "status": "OK"},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=[],
                allow_empty=True,
                expected_types={},
                required_explanations=["clean", "normal", "no anomalies"],
            ),
            difficulty="medium",
        ),

        # 3. ANOM-HLD-03: Categorical rarity anomaly
        AnomalyCase(
            case_code="ANOM-HLD-03",
            name="Rogue Geo Location Access",
            description="User logins where one login originates from an unauthorized geopolitical region.",
            split="held_out",
            dataset=[
                {"id": "hld_21", "user": "alice", "country": "US", "success": True},
                {"id": "hld_22", "user": "bob", "country": "US", "success": True},
                {"id": "hld_23", "user": "carol", "country": "US", "success": True},
                {"id": "hld_24", "user": "dan", "country": "XX_SANCTIONED_ZONE", "success": True},  # ANOMALY
                {"id": "hld_25", "user": "erin", "country": "US", "success": True},
            ],
            ground_truth=AnomalyGroundTruth(
                expected_anomaly_ids=["hld_24"],
                expected_types={"hld_24": "categorical_anomaly"},
                required_explanations=["country", "XX_SANCTIONED_ZONE"],
            ),
            difficulty="easy",
        ),
    ]


def load_cases(split: Optional[str] = None) -> List[AnomalyCase]:
    """Load cases for Domain B according to designated split."""
    if split == "optimization":
        return get_optimization_cases()
    elif split == "held_out":
        return get_held_out_cases()
    elif split in (None, "full"):
        return get_optimization_cases() + get_held_out_cases()
    raise ValueError(f"Unknown split '{split}' for Anomaly Detection benchmark.")
