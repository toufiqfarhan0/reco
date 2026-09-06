"""Canonical 20-case deterministic synthetic reconciliation dataset.

Split:
- 12 Optimization Cases (REC-OPT-01 to REC-OPT-12)
- 8 Held-Out Cases (REC-HLD-01 to REC-HLD-08)

All financial values are deterministic Decimals.
Benchmark Version: reconciliation-v1
"""

from decimal import Decimal
from typing import Dict, List, Optional

from reco.benchmarks.reconciliation.models import (
    ExpectedMatchPair,
    ReconciliationCase,
    ReconciliationGroundTruth,
)

BENCHMARK_VERSION = "reconciliation-v1"
BENCHMARK_NAME = "reconciliation"

# ---------------------------------------------------------------------------
# 12 OPTIMIZATION CASES
# ---------------------------------------------------------------------------

_OPTIMIZATION_CASES: List[ReconciliationCase] = [
    # 1. Exact Match
    ReconciliationCase(
        case_code="REC-OPT-01",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="easy",
        exception_class="exact_match",
        description="Single exact match with identical amount, vendor, date, and invoice reference.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-101",
                "date": "2026-03-01",
                "amount": "1500.00",
                "currency": "USD",
                "vendor": "Acme Corp",
                "reference": "INV-1001",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-101",
                "date": "2026-03-01",
                "amount": "1500.00",
                "currency": "USD",
                "account": "1000-Cash",
                "vendor": "Acme Corp",
                "reference": "INV-1001",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-101",
                    ledger_entry_id="GL-OPT-101",
                    match_type="exact_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.95,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="exact_match",
            expected_exceptions={"exact_match": 1},
            total_discrepancy=Decimal("0.00"),
            verification_rules=["exact_amount_match", "exact_vendor_match"],
        ),
    ),
    # 2. Near Match (Vendor Typo)
    ReconciliationCase(
        case_code="REC-OPT-02",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="easy",
        exception_class="near_match",
        description="Near match with identical amount but minor vendor abbreviation/suffix.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-201",
                "date": "2026-03-02",
                "amount": "450.00",
                "currency": "USD",
                "vendor": "Amazon Web Services Inc",
                "reference": "AWS-REF",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-201",
                "date": "2026-03-02",
                "amount": "450.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Amazon Web Services",
                "reference": "AWS-REF",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-201",
                    ledger_entry_id="GL-OPT-201",
                    match_type="near_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.80,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="near_match",
            expected_exceptions={"near_match": 1},
            total_discrepancy=Decimal("0.00"),
            verification_rules=["vendor_similarity_high", "exact_amount_match"],
        ),
    ),
    # 3. Processing Fee
    ReconciliationCase(
        case_code="REC-OPT-03",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="medium",
        exception_class="processing_fee",
        description="Payment gateway gross settlement deduction (2.9% fee on $1000 = $29).",
        bank_records=[
            {
                "transaction_id": "TX-OPT-301",
                "date": "2026-03-03",
                "amount": "971.00",
                "currency": "USD",
                "vendor": "Stripe Payments",
                "reference": "STRIPE-PAY",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-301",
                "date": "2026-03-03",
                "amount": "1000.00",
                "currency": "USD",
                "account": "1000-Cash",
                "vendor": "Stripe Payments",
                "reference": "STRIPE-PAY",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-301",
                    ledger_entry_id="GL-OPT-301",
                    match_type="processing_fee",
                    amount_discrepancy=Decimal("29.00"),
                    confidence_min=0.75,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="processing_fee",
            expected_exceptions={"processing_fee": 1},
            total_discrepancy=Decimal("29.00"),
            verification_rules=["fee_rate_deduction_matched"],
        ),
    ),
    # 4. Timing Difference
    ReconciliationCase(
        case_code="REC-OPT-04",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="easy",
        exception_class="timing_difference",
        description="Settlement clearing delay across 4 calendar days between bank and ledger booking.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-401",
                "date": "2026-03-07",
                "amount": "2400.00",
                "currency": "USD",
                "vendor": "FedEx Freight",
                "reference": "SHP-990",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-401",
                "date": "2026-03-03",
                "amount": "2400.00",
                "currency": "USD",
                "account": "6200-Freight",
                "vendor": "FedEx Freight",
                "reference": "SHP-990",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-401",
                    ledger_entry_id="GL-OPT-401",
                    match_type="timing_difference",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.75,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="timing_difference",
            expected_exceptions={"timing_difference": 1},
            total_discrepancy=Decimal("0.00"),
            verification_rules=["date_lag_bounded"],
        ),
    ),
    # 5. Duplicate Transaction
    ReconciliationCase(
        case_code="REC-OPT-05",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="medium",
        exception_class="duplicate",
        description="Bank contains duplicate debit for a single general ledger entry.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-501",
                "date": "2026-03-05",
                "amount": "325.50",
                "currency": "USD",
                "vendor": "Office Depot",
                "reference": "OFF-55",
            },
            {
                "transaction_id": "TX-OPT-502",
                "date": "2026-03-05",
                "amount": "325.50",
                "currency": "USD",
                "vendor": "Office Depot",
                "reference": "OFF-55",
            },
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-501",
                "date": "2026-03-05",
                "amount": "325.50",
                "currency": "USD",
                "account": "6300-Supplies",
                "vendor": "Office Depot",
                "reference": "OFF-55",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-501",
                    ledger_entry_id="GL-OPT-501",
                    match_type="duplicate",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.60,
                ),
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-502",
                    ledger_entry_id="GL-OPT-501",
                    match_type="duplicate",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.60,
                ),
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="duplicate",
            expected_exceptions={"duplicate": 2},
            total_discrepancy=Decimal("325.50"),
            verification_rules=["multi_record_duplicate_flagged"],
        ),
    ),
    # 6. Missing in Ledger
    ReconciliationCase(
        case_code="REC-OPT-06",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="medium",
        exception_class="missing_transaction",
        description="Bank shows unexpected wire service fee not recorded in general ledger.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-601",
                "date": "2026-03-06",
                "amount": "120.00",
                "currency": "USD",
                "vendor": "Zoom Video",
                "reference": "ZM-44",
            },
            {
                "transaction_id": "TX-OPT-602",
                "date": "2026-03-06",
                "amount": "35.00",
                "currency": "USD",
                "vendor": "Wire Transfer Fee",
                "reference": "BANK-FEE",
            },
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-601",
                "date": "2026-03-06",
                "amount": "120.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Zoom Video",
                "reference": "ZM-44",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-601",
                    ledger_entry_id="GL-OPT-601",
                    match_type="exact_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.95,
                )
            ],
            unmatched_bank_ids=["TX-OPT-602"],
            unmatched_ledger_ids=[],
            primary_exception="missing_in_ledger",
            expected_exceptions={"exact_match": 1, "missing_in_ledger": 1},
            total_discrepancy=Decimal("35.00"),
            verification_rules=["unmatched_bank_transaction_isolated"],
        ),
    ),
    # 7. Missing in Bank
    ReconciliationCase(
        case_code="REC-OPT-07",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="medium",
        exception_class="missing_transaction",
        description="Ledger has booked an invoice payment that has not yet appeared on bank statement.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-701",
                "date": "2026-03-07",
                "amount": "850.00",
                "currency": "USD",
                "vendor": "Catering Co",
                "reference": "EVT-10",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-701",
                "date": "2026-03-07",
                "amount": "850.00",
                "currency": "USD",
                "account": "6400-Events",
                "vendor": "Catering Co",
                "reference": "EVT-10",
            },
            {
                "entry_id": "GL-OPT-702",
                "date": "2026-03-07",
                "amount": "600.00",
                "currency": "USD",
                "account": "6500-Cleaning",
                "vendor": "Cleaning Services",
                "reference": "CLN-01",
            },
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-701",
                    ledger_entry_id="GL-OPT-701",
                    match_type="exact_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.95,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=["GL-OPT-702"],
            primary_exception="missing_in_bank",
            expected_exceptions={"exact_match": 1, "missing_in_bank": 1},
            total_discrepancy=Decimal("600.00"),
            verification_rules=["unmatched_ledger_entry_isolated"],
        ),
    ),
    # 8. Wrong Vendor
    ReconciliationCase(
        case_code="REC-OPT-08",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="hard",
        exception_class="wrong_vendor",
        description="Same monetary amount and date, but completely unrelated vendors (no false match).",
        bank_records=[
            {
                "transaction_id": "TX-OPT-801",
                "date": "2026-03-08",
                "amount": "750.00",
                "currency": "USD",
                "vendor": "Apex Logistics",
                "reference": "LOG-1",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-801",
                "date": "2026-03-08",
                "amount": "750.00",
                "currency": "USD",
                "account": "6600-Travel",
                "vendor": "Delta Hotel Group",
                "reference": "HTL-9",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[],
            unmatched_bank_ids=["TX-OPT-801"],
            unmatched_ledger_ids=["GL-OPT-801"],
            primary_exception="wrong_vendor",
            expected_exceptions={"missing_in_ledger": 1, "missing_in_bank": 1},
            total_discrepancy=Decimal("750.00"),
            verification_rules=["no_unsupported_false_match"],
        ),
    ),
    # 9. Wrong Amount
    ReconciliationCase(
        case_code="REC-OPT-09",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="medium",
        exception_class="wrong_amount",
        description="Matching vendor and date with an arbitrary dollar mismatch ($1280.00 vs $1200.00).",
        bank_records=[
            {
                "transaction_id": "TX-OPT-901",
                "date": "2026-03-09",
                "amount": "1280.00",
                "currency": "USD",
                "vendor": "Hardware Depot",
                "reference": "HD-101",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-901",
                "date": "2026-03-09",
                "amount": "1200.00",
                "currency": "USD",
                "account": "6700-Equipment",
                "vendor": "Hardware Depot",
                "reference": "HD-101",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-901",
                    ledger_entry_id="GL-OPT-901",
                    match_type="wrong_amount",
                    amount_discrepancy=Decimal("80.00"),
                    confidence_min=0.60,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="wrong_amount",
            expected_exceptions={"wrong_amount": 1},
            total_discrepancy=Decimal("80.00"),
            verification_rules=["amount_discrepancy_calculated"],
        ),
    ),
    # 10. Transposition Error
    ReconciliationCase(
        case_code="REC-OPT-10",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="hard",
        exception_class="transposition",
        description="Accounting digit transposition: $540.00 vs $450.00 (diff $90.00, divisible by 9).",
        bank_records=[
            {
                "transaction_id": "TX-OPT-1001",
                "date": "2026-03-10",
                "amount": "540.00",
                "currency": "USD",
                "vendor": "Consulting Partners",
                "reference": "CNS-77",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-1001",
                "date": "2026-03-10",
                "amount": "450.00",
                "currency": "USD",
                "account": "6800-ProfessionalServices",
                "vendor": "Consulting Partners",
                "reference": "CNS-77",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-1001",
                    ledger_entry_id="GL-OPT-1001",
                    match_type="transposition",
                    amount_discrepancy=Decimal("90.00"),
                    confidence_min=0.70,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="transposition",
            expected_exceptions={"transposition": 1},
            total_discrepancy=Decimal("90.00"),
            verification_rules=["transposition_rule_of_nine_verified"],
        ),
    ),
    # 11. Foreign Exchange Difference
    ReconciliationCase(
        case_code="REC-OPT-11",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="hard",
        exception_class="fx_difference",
        description="Foreign exchange settlement variance on international software subscription.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-1101",
                "date": "2026-03-11",
                "amount": "1085.00",
                "currency": "USD",
                "vendor": "Berlin Cloud Tech",
                "reference": "EUR-INV",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-1101",
                "date": "2026-03-11",
                "amount": "1000.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Berlin Cloud Tech",
                "reference": "EUR-INV",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-1101",
                    ledger_entry_id="GL-OPT-1101",
                    match_type="fx_difference",
                    amount_discrepancy=Decimal("85.00"),
                    confidence_min=0.65,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="fx_difference",
            expected_exceptions={"fx_difference": 1},
            total_discrepancy=Decimal("85.00"),
            verification_rules=["fx_variance_isolated"],
        ),
    ),
    # 12. Compound Exception
    ReconciliationCase(
        case_code="REC-OPT-12",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="optimization",
        difficulty="hard",
        exception_class="compound_exception",
        description="Compound scenario: 2.9% processing fee ($58 on $2000) + 2-day timing delay + slight vendor suffix.",
        bank_records=[
            {
                "transaction_id": "TX-OPT-1201",
                "date": "2026-03-14",
                "amount": "1942.00",
                "currency": "USD",
                "vendor": "Shopify Payments LLC",
                "reference": "SP-202",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-OPT-1201",
                "date": "2026-03-12",
                "amount": "2000.00",
                "currency": "USD",
                "account": "1000-Cash",
                "vendor": "Shopify Payments",
                "reference": "SP-202",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-OPT-1201",
                    ledger_entry_id="GL-OPT-1201",
                    match_type="compound_exception",
                    amount_discrepancy=Decimal("58.00"),
                    confidence_min=0.65,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="compound_exception",
            expected_exceptions={"compound_exception": 1},
            total_discrepancy=Decimal("58.00"),
            verification_rules=["multi_factor_resolution_verified"],
        ),
    ),
]

# ---------------------------------------------------------------------------
# 8 HELD-OUT CASES
# ---------------------------------------------------------------------------

_HELD_OUT_CASES: List[ReconciliationCase] = [
    # 1. Exact Match Batch
    ReconciliationCase(
        case_code="REC-HLD-01",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="easy",
        exception_class="exact_match",
        description="Two-line multi-record exact match batch with zero discrepancies.",
        bank_records=[
            {
                "transaction_id": "TX-HLD-101",
                "date": "2026-04-01",
                "amount": "3100.00",
                "currency": "USD",
                "vendor": "DataCorp Systems",
                "reference": "DC-100",
            },
            {
                "transaction_id": "TX-HLD-102",
                "date": "2026-04-01",
                "amount": "1450.25",
                "currency": "USD",
                "vendor": "Nordic Telecom",
                "reference": "NT-200",
            },
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-101",
                "date": "2026-04-01",
                "amount": "3100.00",
                "currency": "USD",
                "account": "1000-Cash",
                "vendor": "DataCorp Systems",
                "reference": "DC-100",
            },
            {
                "entry_id": "GL-HLD-102",
                "date": "2026-04-01",
                "amount": "1450.25",
                "currency": "USD",
                "account": "6200-Telecom",
                "vendor": "Nordic Telecom",
                "reference": "NT-200",
            },
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-101",
                    ledger_entry_id="GL-HLD-101",
                    match_type="exact_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.95,
                ),
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-102",
                    ledger_entry_id="GL-HLD-102",
                    match_type="exact_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.95,
                ),
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="exact_match",
            expected_exceptions={"exact_match": 2},
            total_discrepancy=Decimal("0.00"),
            verification_rules=["multi_record_exact_resolution"],
        ),
    ),
    # 2. Near Match (Vendor Expansion)
    ReconciliationCase(
        case_code="REC-HLD-02",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="medium",
        exception_class="near_match",
        description="Near match with vendor suffix variation ('Google Cloud Platform' vs 'Google Cloud') and 1-day drift.",
        bank_records=[
            {
                "transaction_id": "TX-HLD-201",
                "date": "2026-04-03",
                "amount": "780.00",
                "currency": "USD",
                "vendor": "Google Cloud Platform",
                "reference": "GCP-9",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-201",
                "date": "2026-04-02",
                "amount": "780.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Google Cloud",
                "reference": "GCP-9",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-201",
                    ledger_entry_id="GL-HLD-201",
                    match_type="near_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.80,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="near_match",
            expected_exceptions={"near_match": 1},
            total_discrepancy=Decimal("0.00"),
            verification_rules=["vendor_fuzzy_resolution"],
        ),
    ),
    # 3. Processing Fee
    ReconciliationCase(
        case_code="REC-HLD-03",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="medium",
        exception_class="processing_fee",
        description="POS terminal fee: $500.00 gross minus 2.9% fee ($14.50) -> $485.50 net.",
        bank_records=[
            {
                "transaction_id": "TX-HLD-301",
                "date": "2026-04-05",
                "amount": "485.50",
                "currency": "USD",
                "vendor": "Square POS",
                "reference": "SQ-88",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-301",
                "date": "2026-04-05",
                "amount": "500.00",
                "currency": "USD",
                "account": "1000-Cash",
                "vendor": "Square POS",
                "reference": "SQ-88",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-301",
                    ledger_entry_id="GL-HLD-301",
                    match_type="processing_fee",
                    amount_discrepancy=Decimal("14.50"),
                    confidence_min=0.75,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="processing_fee",
            expected_exceptions={"processing_fee": 1},
            total_discrepancy=Decimal("14.50"),
            verification_rules=["fee_variance_verified"],
        ),
    ),
    # 4. Timing Difference
    ReconciliationCase(
        case_code="REC-HLD-04",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="easy",
        exception_class="timing_difference",
        description="Weekend bank settlement lag (4 days between ledger entry and bank settlement).",
        bank_records=[
            {
                "transaction_id": "TX-HLD-401",
                "date": "2026-04-09",
                "amount": "5200.00",
                "currency": "USD",
                "vendor": "Midwest Supply",
                "reference": "MS-44",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-401",
                "date": "2026-04-05",
                "amount": "5200.00",
                "currency": "USD",
                "account": "6300-Supplies",
                "vendor": "Midwest Supply",
                "reference": "MS-44",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-401",
                    ledger_entry_id="GL-HLD-401",
                    match_type="timing_difference",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.75,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="timing_difference",
            expected_exceptions={"timing_difference": 1},
            total_discrepancy=Decimal("0.00"),
            verification_rules=["timing_window_resolved"],
        ),
    ),
    # 5. Duplicate in Ledger
    ReconciliationCase(
        case_code="REC-HLD-05",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="hard",
        exception_class="duplicate",
        description="General ledger contains duplicate accrual entries matching one bank debit.",
        bank_records=[
            {
                "transaction_id": "TX-HLD-501",
                "date": "2026-04-08",
                "amount": "920.00",
                "currency": "USD",
                "vendor": "Adobe Systems",
                "reference": "ADB-01",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-501",
                "date": "2026-04-08",
                "amount": "920.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Adobe Systems",
                "reference": "ADB-01",
            },
            {
                "entry_id": "GL-HLD-502",
                "date": "2026-04-08",
                "amount": "920.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Adobe Systems",
                "reference": "ADB-01",
            },
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-501",
                    ledger_entry_id="GL-HLD-501",
                    match_type="duplicate",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.60,
                ),
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-501",
                    ledger_entry_id="GL-HLD-502",
                    match_type="duplicate",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.60,
                ),
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="duplicate",
            expected_exceptions={"duplicate": 2},
            total_discrepancy=Decimal("920.00"),
            verification_rules=["ledger_duplicate_detected"],
        ),
    ),
    # 6. Transposition Error
    ReconciliationCase(
        case_code="REC-HLD-06",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="hard",
        exception_class="transposition",
        description="Accounting transposition error: $730.00 bank vs $370.00 ledger (diff $360.00, divisible by 9).",
        bank_records=[
            {
                "transaction_id": "TX-HLD-601",
                "date": "2026-04-10",
                "amount": "730.00",
                "currency": "USD",
                "vendor": "Pinnacle Legal",
                "reference": "PIN-55",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-601",
                "date": "2026-04-10",
                "amount": "370.00",
                "currency": "USD",
                "account": "6800-ProfessionalServices",
                "vendor": "Pinnacle Legal",
                "reference": "PIN-55",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-601",
                    ledger_entry_id="GL-HLD-601",
                    match_type="transposition",
                    amount_discrepancy=Decimal("360.00"),
                    confidence_min=0.70,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="transposition",
            expected_exceptions={"transposition": 1},
            total_discrepancy=Decimal("360.00"),
            verification_rules=["transposition_flagged"],
        ),
    ),
    # 7. Missing Transaction in Ledger
    ReconciliationCase(
        case_code="REC-HLD-07",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="medium",
        exception_class="missing_transaction",
        description="Unidentified merchant charge on bank statement not in general ledger.",
        bank_records=[
            {
                "transaction_id": "TX-HLD-701",
                "date": "2026-04-12",
                "amount": "1600.00",
                "currency": "USD",
                "vendor": "Enterprise Rental",
                "reference": "ENT-99",
            },
            {
                "transaction_id": "TX-HLD-702",
                "date": "2026-04-12",
                "amount": "245.00",
                "currency": "USD",
                "vendor": "Unknown Merchant 99",
                "reference": "UNK-01",
            },
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-701",
                "date": "2026-04-12",
                "amount": "1600.00",
                "currency": "USD",
                "account": "6600-Travel",
                "vendor": "Enterprise Rental",
                "reference": "ENT-99",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-701",
                    ledger_entry_id="GL-HLD-701",
                    match_type="exact_match",
                    amount_discrepancy=Decimal("0.00"),
                    confidence_min=0.95,
                )
            ],
            unmatched_bank_ids=["TX-HLD-702"],
            unmatched_ledger_ids=[],
            primary_exception="missing_in_ledger",
            expected_exceptions={"exact_match": 1, "missing_in_ledger": 1},
            total_discrepancy=Decimal("245.00"),
            verification_rules=["unmatched_bank_identified"],
        ),
    ),
    # 8. Compound Exception (FX + Timing)
    ReconciliationCase(
        case_code="REC-HLD-08",
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        split="held_out",
        difficulty="hard",
        exception_class="compound_exception",
        description="Foreign exchange variance ($2170 vs $2000) combined with 3-day timing delay and vendor suffix.",
        bank_records=[
            {
                "transaction_id": "TX-HLD-801",
                "date": "2026-04-16",
                "amount": "2170.00",
                "currency": "USD",
                "vendor": "Tokyo AI Labs K.K.",
                "reference": "TYO-001",
            }
        ],
        ledger_entries=[
            {
                "entry_id": "GL-HLD-801",
                "date": "2026-04-13",
                "amount": "2000.00",
                "currency": "USD",
                "account": "6100-CloudServices",
                "vendor": "Tokyo AI Labs",
                "reference": "TYO-001",
            }
        ],
        ground_truth=ReconciliationGroundTruth(
            expected_pairs=[
                ExpectedMatchPair(
                    bank_transaction_id="TX-HLD-801",
                    ledger_entry_id="GL-HLD-801",
                    match_type="compound_exception",
                    amount_discrepancy=Decimal("170.00"),
                    confidence_min=0.65,
                )
            ],
            unmatched_bank_ids=[],
            unmatched_ledger_ids=[],
            primary_exception="compound_exception",
            expected_exceptions={"compound_exception": 1},
            total_discrepancy=Decimal("170.00"),
            verification_rules=["compound_fx_timing_resolved"],
        ),
    ),
]

_ALL_CASES: List[ReconciliationCase] = _OPTIMIZATION_CASES + _HELD_OUT_CASES
_CASES_BY_CODE: Dict[str, ReconciliationCase] = {c.case_code: c for c in _ALL_CASES}


def load_cases(split: Optional[str] = None) -> List[ReconciliationCase]:
    """Load deterministic benchmark cases for the requested split.

    Args:
        split: 'optimization' (12 cases), 'held_out' (8 cases), or None / 'full' (all 20 cases).

    Returns:
        Deterministic list of ReconciliationCase objects.

    Raises:
        ValueError: If an unknown split is requested.
    """
    if split is None or split == "full":
        return [c.model_copy(deep=True) for c in _ALL_CASES]
    if split == "optimization":
        return [c.model_copy(deep=True) for c in _OPTIMIZATION_CASES]
    if split == "held_out":
        return [c.model_copy(deep=True) for c in _HELD_OUT_CASES]
    raise ValueError(f"Unknown benchmark split '{split}'. Valid options are 'optimization', 'held_out', or 'full'.")


def get_optimization_cases() -> List[ReconciliationCase]:
    """Return the 12 canonical optimization benchmark cases."""
    return load_cases("optimization")


def get_held_out_cases() -> List[ReconciliationCase]:
    """Return the 8 isolated held-out benchmark cases."""
    return load_cases("held_out")


def get_case_by_code(case_code: str) -> Optional[ReconciliationCase]:
    """Retrieve an individual benchmark case by its unique immutable code."""
    case = _CASES_BY_CODE.get(case_code)
    return case.model_copy(deep=True) if case else None
