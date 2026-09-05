"""Multi-case benchmark dataset for financial transaction reconciliation.

Strictly split into 6 optimization cases and 4 held-out cases with zero cross-split leakage.
"""

from __future__ import annotations

from typing import List
from reco.benchmarks.base import BenchmarkCase, BenchmarkSplit, BenchmarkSuite


def create_reconciliation_benchmark_cases() -> List[BenchmarkCase]:
    """Instantiate the 10 canonical benchmark test cases."""
    cases: List[BenchmarkCase] = []

    # =========================================================================
    # OPTIMIZATION SPLIT (6 Cases)
    # =========================================================================

    # 1. Exact Match Baseline
    cases.append(BenchmarkCase(
        case_id="reco_opt_001_exact_match",
        name="Exact 1:1 Transaction Match",
        description="Source and target ledgers contain identical records with exact amounts and timestamps.",
        category="exact_match",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "source_records": [
                {"id": "TX101", "amount": 100.0, "date": "2026-01-10", "merchant": "Acme Supplies"},
                {"id": "TX102", "amount": 250.50, "date": "2026-01-11", "merchant": "Cloud Hosting"},
                {"id": "TX103", "amount": 75.25, "date": "2026-01-11", "merchant": "Office Stationery"},
                {"id": "TX104", "amount": 1200.0, "date": "2026-01-12", "merchant": "Hardware Depot"},
                {"id": "TX105", "amount": 42.0, "date": "2026-01-12", "merchant": "Coffee Co"},
            ],
            "target_records": [
                {"id": "TX101", "amount": 100.0, "date": "2026-01-10", "merchant": "Acme Supplies"},
                {"id": "TX102", "amount": 250.50, "date": "2026-01-11", "merchant": "Cloud Hosting"},
                {"id": "TX103", "amount": 75.25, "date": "2026-01-11", "merchant": "Office Stationery"},
                {"id": "TX104", "amount": 1200.0, "date": "2026-01-12", "merchant": "Hardware Depot"},
                {"id": "TX105", "amount": 42.0, "date": "2026-01-12", "merchant": "Coffee Co"},
            ]
        },
        expected_output={
            "matched_ids": ["TX101", "TX102", "TX103", "TX104", "TX105"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 5,
            "discrepancy_count": 0,
            "status": "reconciled"
        },
        metadata={"difficulty": "easy", "split_target": "optimization"}
    ))

    # 2. Missing Records in Target
    cases.append(BenchmarkCase(
        case_id="reco_opt_002_missing_target",
        name="Missing Records in Target Ledger",
        description="Source ledger has transactions that never cleared or were omitted from the target ledger.",
        category="missing_records",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "source_records": [
                {"id": "TX201", "amount": 310.0, "date": "2026-01-15", "merchant": "Logistics Express"},
                {"id": "TX202", "amount": 85.0, "date": "2026-01-16", "merchant": "Postal Service"},
                {"id": "TX203", "amount": 620.0, "date": "2026-01-17", "merchant": "Legal Counsel"},
                {"id": "TX204", "amount": 450.0, "date": "2026-01-18", "merchant": "Marketing Agency"},
                {"id": "TX205", "amount": 90.0, "date": "2026-01-18", "merchant": "Domain Registrar"},
            ],
            "target_records": [
                {"id": "TX201", "amount": 310.0, "date": "2026-01-15", "merchant": "Logistics Express"},
                {"id": "TX202", "amount": 85.0, "date": "2026-01-16", "merchant": "Postal Service"},
                {"id": "TX203", "amount": 620.0, "date": "2026-01-17", "merchant": "Legal Counsel"},
            ]
        },
        expected_output={
            "matched_ids": ["TX201", "TX202", "TX203"],
            "unmatched_source_ids": ["TX204", "TX205"],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 3,
            "discrepancy_count": 0,
            "status": "discrepancy_detected"
        },
        metadata={"difficulty": "medium", "split_target": "optimization"}
    ))

    # 3. Missing Records in Source (Unmatched Target Entries)
    cases.append(BenchmarkCase(
        case_id="reco_opt_003_missing_source",
        name="Missing Records in Source Ledger",
        description="Target ledger has unexpected deposits or credits that have no matching entry in the source system.",
        category="missing_records",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "source_records": [
                {"id": "TX301", "amount": 150.0, "date": "2026-01-20", "merchant": "SaaS Subscription"},
                {"id": "TX302", "amount": 75.0, "date": "2026-01-21", "merchant": "Security Scan"},
                {"id": "TX303", "amount": 540.0, "date": "2026-01-22", "merchant": "Conference Pass"},
            ],
            "target_records": [
                {"id": "TX301", "amount": 150.0, "date": "2026-01-20", "merchant": "SaaS Subscription"},
                {"id": "TX302", "amount": 75.0, "date": "2026-01-21", "merchant": "Security Scan"},
                {"id": "TX303", "amount": 540.0, "date": "2026-01-22", "merchant": "Conference Pass"},
                {"id": "TX304", "amount": 620.0, "date": "2026-01-23", "merchant": "Direct Wire Deposit"},
                {"id": "TX305", "amount": 110.0, "date": "2026-01-23", "merchant": "Interest Credit"},
            ]
        },
        expected_output={
            "matched_ids": ["TX301", "TX302", "TX303"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": ["TX304", "TX305"],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 3,
            "discrepancy_count": 0,
            "status": "discrepancy_detected"
        },
        metadata={"difficulty": "medium", "split_target": "optimization"}
    ))

    # 4. Amount Mismatches (Fee variances / discrepancies)
    cases.append(BenchmarkCase(
        case_id="reco_opt_004_amount_mismatch",
        name="Amount Mismatch on Identical Transaction IDs",
        description="Transactions exist on both sides with same IDs, but amounts deviate due to withholdings or fees.",
        category="amount_mismatch",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "source_records": [
                {"id": "TX401", "amount": 100.0, "date": "2026-02-01", "merchant": "Telecom Bill"},
                {"id": "TX402", "amount": 200.0, "date": "2026-02-02", "merchant": "Cloud Storage"},
                {"id": "TX403", "amount": 450.0, "date": "2026-02-03", "merchant": "Contractor Fee"},
                {"id": "TX404", "amount": 1200.0, "date": "2026-02-04", "merchant": "Server Equipment"},
            ],
            "target_records": [
                {"id": "TX401", "amount": 100.0, "date": "2026-02-01", "merchant": "Telecom Bill"},
                {"id": "TX402", "amount": 200.0, "date": "2026-02-02", "merchant": "Cloud Storage"},
                {"id": "TX403", "amount": 425.0, "date": "2026-02-03", "merchant": "Contractor Fee"},  # $25 discrepancy
                {"id": "TX404", "amount": 1200.50, "date": "2026-02-04", "merchant": "Server Equipment"},  # $0.50 discrepancy
            ]
        },
        expected_output={
            "matched_ids": ["TX401", "TX402"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": ["TX403", "TX404"],
            "duplicate_ids": [],
            "matched_count": 2,
            "discrepancy_count": 2,
            "status": "discrepancy_detected"
        },
        metadata={"difficulty": "medium", "split_target": "optimization"}
    ))

    # 5. Duplicate Records in Target
    cases.append(BenchmarkCase(
        case_id="reco_opt_005_duplicate_records",
        name="Duplicate Transactions in Target Ledger",
        description="Target ledger contains duplicate transactions resulting from double settlement or webhook retry.",
        category="duplicate_records",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "source_records": [
                {"id": "TX501", "amount": 150.0, "date": "2026-02-10", "merchant": "Design Asset"},
                {"id": "TX502", "amount": 300.0, "date": "2026-02-11", "merchant": "Ad Campaign"},
                {"id": "TX503", "amount": 450.0, "date": "2026-02-12", "merchant": "PR Outreach"},
            ],
            "target_records": [
                {"id": "TX501", "amount": 150.0, "date": "2026-02-10", "merchant": "Design Asset"},
                {"id": "TX502", "amount": 300.0, "date": "2026-02-11", "merchant": "Ad Campaign"},
                {"id": "TX502", "amount": 300.0, "date": "2026-02-11", "merchant": "Ad Campaign"},  # Duplicate
                {"id": "TX503", "amount": 450.0, "date": "2026-02-12", "merchant": "PR Outreach"},
            ]
        },
        expected_output={
            "matched_ids": ["TX501", "TX502", "TX503"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "duplicate_ids": ["TX502"],
            "matched_count": 3,
            "duplicate_count": 1,
            "status": "duplicate_detected"
        },
        metadata={"difficulty": "hard", "split_target": "optimization"}
    ))

    # 6. Format Variations
    cases.append(BenchmarkCase(
        case_id="reco_opt_006_format_variations",
        name="Date and Identifier Format Variations",
        description="Records match logically but exhibit differences in date representations, casing, and string numbers.",
        category="format_variation",
        split=BenchmarkSplit.OPTIMIZATION,
        input_data={
            "source_records": [
                {"id": "TX601", "amount": 100.0, "date": "2026-03-01", "merchant": "Acme Co"},
                {"id": "TX602", "amount": 250.0, "date": "2026-03-02", "merchant": "Beta LLC"},
                {"id": "TX603", "amount": 500.0, "date": "2026-03-03", "merchant": "Gamma Inc"},
            ],
            "target_records": [
                {"id": "tx601", "amount": "$100.00", "date": "03/01/2026", "merchant": "ACME CO"},
                {"id": "TX602", "amount": 250.0, "date": "2026-03-02T00:00:00Z", "merchant": "Beta LLC"},
                {"id": "tx603", "amount": "500", "date": "2026/03/03", "merchant": "gamma inc"},
            ]
        },
        expected_output={
            "matched_ids": ["TX601", "TX602", "TX603"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 3,
            "discrepancy_count": 0,
            "status": "reconciled"
        },
        metadata={"difficulty": "hard", "split_target": "optimization"}
    ))

    # =========================================================================
    # HELD-OUT SPLIT (4 Cases)
    # =========================================================================

    # 7. Held-Out Exact Multi-Record Match
    cases.append(BenchmarkCase(
        case_id="reco_held_001_exact_multi_item",
        name="Held-out Clean Multi-Item Batch",
        description="Air-gapped verification baseline of 6 diverse corporate transactions matching exactly.",
        category="exact_match",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "source_records": [
                {"id": "TX701", "amount": 50.0, "date": "2026-04-01", "merchant": "Office Pantry"},
                {"id": "TX702", "amount": 150.0, "date": "2026-04-02", "merchant": "Travel Booking"},
                {"id": "TX703", "amount": 320.0, "date": "2026-04-03", "merchant": "Database License"},
                {"id": "TX704", "amount": 780.0, "date": "2026-04-04", "merchant": "Analytics Suite"},
                {"id": "TX705", "amount": 95.0, "date": "2026-04-05", "merchant": "Courier Express"},
                {"id": "TX706", "amount": 1400.0, "date": "2026-04-06", "merchant": "Annual Audit"},
            ],
            "target_records": [
                {"id": "TX701", "amount": 50.0, "date": "2026-04-01", "merchant": "Office Pantry"},
                {"id": "TX702", "amount": 150.0, "date": "2026-04-02", "merchant": "Travel Booking"},
                {"id": "TX703", "amount": 320.0, "date": "2026-04-03", "merchant": "Database License"},
                {"id": "TX704", "amount": 780.0, "date": "2026-04-04", "merchant": "Analytics Suite"},
                {"id": "TX705", "amount": 95.0, "date": "2026-04-05", "merchant": "Courier Express"},
                {"id": "TX706", "amount": 1400.0, "date": "2026-04-06", "merchant": "Annual Audit"},
            ]
        },
        expected_output={
            "matched_ids": ["TX701", "TX702", "TX703", "TX704", "TX705", "TX706"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 6,
            "discrepancy_count": 0,
            "status": "reconciled"
        },
        metadata={"difficulty": "medium", "split_target": "held-out"}
    ))

    # 8. Held-Out Symmetric Missing Records
    cases.append(BenchmarkCase(
        case_id="reco_held_002_symmetric_missing",
        name="Held-out Symmetrical Missing Records",
        description="Air-gapped test where both source and target contain unilateral un-reconciled items.",
        category="missing_records",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "source_records": [
                {"id": "TX801", "amount": 210.0, "date": "2026-04-10", "merchant": "Compute Node A"},
                {"id": "TX802", "amount": 420.0, "date": "2026-04-11", "merchant": "Compute Node B"},
                {"id": "TX803", "amount": 630.0, "date": "2026-04-12", "merchant": "Compute Node C"},
                {"id": "TX804", "amount": 840.0, "date": "2026-04-13", "merchant": "Compute Node D"},
            ],
            "target_records": [
                {"id": "TX801", "amount": 210.0, "date": "2026-04-10", "merchant": "Compute Node A"},
                {"id": "TX802", "amount": 420.0, "date": "2026-04-11", "merchant": "Compute Node B"},
                {"id": "TX805", "amount": 350.0, "date": "2026-04-14", "merchant": "Storage Bucket A"},
                {"id": "TX806", "amount": 550.0, "date": "2026-04-15", "merchant": "Storage Bucket B"},
            ]
        },
        expected_output={
            "matched_ids": ["TX801", "TX802"],
            "unmatched_source_ids": ["TX803", "TX804"],
            "unmatched_target_ids": ["TX805", "TX806"],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 2,
            "discrepancy_count": 0,
            "status": "discrepancy_detected"
        },
        metadata={"difficulty": "medium", "split_target": "held-out"}
    ))

    # 9. Held-Out Compound Discrepancy & Duplicate
    cases.append(BenchmarkCase(
        case_id="reco_held_003_compound_duplicate_and_discrepancy",
        name="Held-out Duplicate Settlement and Amount Variance",
        description="Air-gapped scenario combining target duplicates with currency amount mismatch.",
        category="compound_discrepancy",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "source_records": [
                {"id": "TX901", "amount": 300.0, "date": "2026-04-20", "merchant": "Vendor Alpha"},
                {"id": "TX902", "amount": 450.0, "date": "2026-04-21", "merchant": "Vendor Beta"},
                {"id": "TX903", "amount": 990.0, "date": "2026-04-22", "merchant": "Vendor Gamma"},
                {"id": "TX904", "amount": 120.0, "date": "2026-04-23", "merchant": "Vendor Delta"},
            ],
            "target_records": [
                {"id": "TX901", "amount": 300.0, "date": "2026-04-20", "merchant": "Vendor Alpha"},
                {"id": "TX902", "amount": 450.0, "date": "2026-04-21", "merchant": "Vendor Beta"},
                {"id": "TX902", "amount": 450.0, "date": "2026-04-21", "merchant": "Vendor Beta"},  # Duplicate
                {"id": "TX903", "amount": 900.0, "date": "2026-04-22", "merchant": "Vendor Gamma"},  # $90 mismatch
                {"id": "TX904", "amount": 120.0, "date": "2026-04-23", "merchant": "Vendor Delta"},
            ]
        },
        expected_output={
            "matched_ids": ["TX901", "TX902", "TX904"],
            "unmatched_source_ids": [],
            "unmatched_target_ids": [],
            "discrepancy_ids": ["TX903"],
            "duplicate_ids": ["TX902"],
            "matched_count": 3,
            "duplicate_count": 1,
            "discrepancy_count": 1,
            "status": "discrepancy_detected"
        },
        metadata={"difficulty": "hard", "split_target": "held-out"}
    ))

    # 10. Held-Out Complex Format Variation & Missing
    cases.append(BenchmarkCase(
        case_id="reco_held_004_complex_format_and_missing",
        name="Held-out Format Variations with Missing Item",
        description="Air-gapped test with currency formatting, padded IDs, ISO timestamps, and a missing source record.",
        category="format_variation",
        split=BenchmarkSplit.HELD_OUT,
        input_data={
            "source_records": [
                {"id": "TX951", "amount": 1500.0, "date": "2026-04-25", "merchant": "Enterprise Cloud"},
                {"id": "TX952", "amount": 750.25, "date": "2026-04-26", "merchant": "Design Retainer"},
                {"id": "TX953", "amount": 340.0, "date": "2026-04-27", "merchant": "Security Token"},
            ],
            "target_records": [
                {"id": "  tx951  ", "amount": "$1,500.00", "date": "2026-04-25T14:30:00Z", "merchant": "enterprise cloud"},
                {"id": "TX952", "amount": "750.25", "date": "04/26/2026", "merchant": "Design Retainer"},
            ]
        },
        expected_output={
            "matched_ids": ["TX951", "TX952"],
            "unmatched_source_ids": ["TX953"],
            "unmatched_target_ids": [],
            "discrepancy_ids": [],
            "duplicate_ids": [],
            "matched_count": 2,
            "discrepancy_count": 0,
            "status": "discrepancy_detected"
        },
        metadata={"difficulty": "hard", "split_target": "held-out"}
    ))

    return cases


def get_reconciliation_benchmark_suite() -> BenchmarkSuite:
    """Build and validate the standard 10-case reconciliation benchmark suite."""
    cases = create_reconciliation_benchmark_cases()
    suite = BenchmarkSuite(
        name="reconciliation_benchmark_v1",
        description="Standard 10-case financial reconciliation benchmark partitioned 6/4 (opt/held-out).",
        cases=cases
    )
    # Strictly validate partition isolation
    suite.validate_partition_isolation()
    return suite
