"""Partitioned Benchmark Harness base models and partition isolation enforcement."""

from __future__ import annotations

from enum import Enum
import math
from typing import Any, Callable, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, field_validator


class BenchmarkSplit(str, Enum):
    """Strict partition split for benchmark evaluation."""

    OPTIMIZATION = "optimization"
    HELD_OUT = "held-out"


class BenchmarkCase(BaseModel):
    """Deterministic benchmark test case with strict partition assignment."""

    case_id: str = Field(description="Deterministic unique ID for the test case")
    name: str = Field(default="", description="Descriptive human-readable test case name")
    description: str = Field(default="", description="Detailed scenario description")
    category: str = Field(default="general", description="Scenario category (e.g., exact_match, missing_records)")
    input_data: Dict[str, Any] = Field(description="Payload provided to the agent DAG")
    expected_output: Dict[str, Any] = Field(description="Ground-truth assertion criteria")
    split: BenchmarkSplit = Field(
        description="Partition split: 'optimization' (mutation discovery) or 'held-out' (promotion gate)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary case metadata")

    @field_validator("split", mode="before")
    @classmethod
    def normalize_split(cls, v: Any) -> BenchmarkSplit:
        """Normalize split string values to BenchmarkSplit enum."""
        if isinstance(v, BenchmarkSplit):
            return v
        if isinstance(v, str):
            normalized = v.strip().lower().replace("_", "-")
            if normalized in ("optimization", "opt", "train"):
                return BenchmarkSplit.OPTIMIZATION
            if normalized in ("held-out", "heldout", "test", "validation"):
                return BenchmarkSplit.HELD_OUT
        raise ValueError(f"Invalid split '{v}'. Expected 'optimization' or 'held-out'.")

    def eval_match(self, actual_output: Any) -> bool:
        """Evaluate if the actual output matches ground-truth assertion criteria.

        Args:
            actual_output: Output dictionary or payload from agent execution.

        Returns:
            True if all ground truth criteria in expected_output are satisfied.
        """
        if actual_output is None:
            return False

        if actual_output == self.expected_output:
            return True

        if not isinstance(actual_output, dict):
            return False

        # If actual_output has a nested domain payload, look inside
        candidate_payloads = [actual_output]
        for wrapper_key in ("reconciliation", "result", "output", "data", "anomaly", "research", "synthesis", "summary"):
            if wrapper_key in actual_output and isinstance(actual_output[wrapper_key], dict):
                candidate_payloads.append(actual_output[wrapper_key])

        for payload in candidate_payloads:
            if self._matches_criteria(self.expected_output, payload):
                return True

        return False

    def _matches_criteria(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """Check recursively if all fields in expected are matched in actual."""
        for key, exp_val in expected.items():
            if key not in actual:
                return False
            act_val = actual[key]

            if isinstance(exp_val, list):
                if not isinstance(act_val, list):
                    return False
                # If list of simple identifiers / strings, compare set-wise (case-insensitive for strings)
                if all(isinstance(x, (str, int)) for x in exp_val):
                    exp_set = {x.strip().lower() if isinstance(x, str) else x for x in exp_val}
                    act_set = {x.strip().lower() if isinstance(x, str) else x for x in act_val}
                    if exp_set != act_set:
                        return False
                # If list of dicts, match by length and element containment
                elif all(isinstance(x, dict) for x in exp_val):
                    if len(exp_val) != len(act_val):
                        return False
                    # Check that each expected dict has a matching actual dict
                    matched_indices: Set[int] = set()
                    for item in exp_val:
                        found = False
                        for idx, act_item in enumerate(act_val):
                            if idx not in matched_indices and isinstance(act_item, dict):
                                if self._dict_subset_match(item, act_item):
                                    matched_indices.add(idx)
                                    found = True
                                    break
                        if not found:
                            return False
                else:
                    if exp_val != act_val:
                        return False

            elif isinstance(exp_val, dict):
                if not isinstance(act_val, dict):
                    return False
                if not self._matches_criteria(exp_val, act_val):
                    return False

            elif isinstance(exp_val, (int, float)) and not isinstance(exp_val, bool):
                if not isinstance(act_val, (int, float)) or isinstance(act_val, bool):
                    return False
                if not math.isclose(float(exp_val), float(act_val), rel_tol=1e-3, abs_tol=1e-3):
                    return False

            elif isinstance(exp_val, str):
                if not isinstance(act_val, str) or exp_val.strip().lower() != act_val.strip().lower():
                    return False

            else:
                if exp_val != act_val:
                    return False

        return True

    @staticmethod
    def _dict_subset_match(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
        """Check if all key-values in expected match in actual."""
        for k, v in expected.items():
            if k not in actual:
                return False
            act_v = actual[k]
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if not isinstance(act_v, (int, float)) or not math.isclose(float(v), float(act_v), abs_tol=1e-3):
                    return False
            elif isinstance(v, str):
                if not isinstance(act_v, str) or v.strip().lower() != act_v.strip().lower():
                    return False
            else:
                if v != act_v:
                    return False
        return True


class BenchmarkSuite(BaseModel):
    """Collection of benchmark cases enforcing strict partition isolation."""

    name: str = Field(description="Name of the benchmark suite")
    description: str = Field(default="", description="Suite description")
    cases: List[BenchmarkCase] = Field(default_factory=list, description="Benchmark cases")

    def add_case(self, case: BenchmarkCase) -> None:
        """Add a benchmark case and ensure case_id uniqueness."""
        if any(c.case_id == case.case_id for c in self.cases):
            raise ValueError(f"Duplicate case_id '{case.case_id}' cannot be added to suite.")
        self.cases.append(case)

    def get_case(self, case_id: str) -> Optional[BenchmarkCase]:
        """Lookup a case by its deterministic case_id."""
        for c in self.cases:
            if c.case_id == case_id:
                return c
        return None

    def get_split(self, split: Union[BenchmarkSplit, str]) -> List[BenchmarkCase]:
        """Retrieve cases belonging strictly to the requested partition split."""
        if isinstance(split, str):
            norm = split.strip().lower().replace("_", "-")
            split_enum = BenchmarkSplit.OPTIMIZATION if norm in ("optimization", "opt", "train") else BenchmarkSplit.HELD_OUT
        else:
            split_enum = split

        return [c for c in self.cases if c.split == split_enum]

    def get_optimization_cases(self) -> List[BenchmarkCase]:
        """Retrieve all cases in the optimization split."""
        return self.get_split(BenchmarkSplit.OPTIMIZATION)

    def get_held_out_cases(self) -> List[BenchmarkCase]:
        """Retrieve all cases in the held-out split."""
        return self.get_split(BenchmarkSplit.HELD_OUT)

    def validate_partition_isolation(self) -> bool:
        """Verify strict air-gapped isolation between splits with zero leakage.

        Raises:
            ValueError: If partition isolation constraints are violated.

        Returns:
            True if partitioning is strictly valid.
        """
        if not self.cases:
            raise ValueError("BenchmarkSuite contains no cases.")

        opt_ids = {c.case_id for c in self.cases if c.split == BenchmarkSplit.OPTIMIZATION}
        held_ids = {c.case_id for c in self.cases if c.split == BenchmarkSplit.HELD_OUT}

        # 1. Non-empty check
        if not opt_ids:
            raise ValueError("Optimization partition cannot be empty.")
        if not held_ids:
            raise ValueError("Held-out partition cannot be empty.")

        # 2. Strict disjointness (zero cross-split leakage)
        leakage = opt_ids.intersection(held_ids)
        if leakage:
            raise ValueError(f"Cross-split leakage detected! Case IDs present in both partitions: {leakage}")

        # 3. Overall uniqueness
        all_ids = [c.case_id for c in self.cases]
        if len(all_ids) != len(set(all_ids)):
            seen = set()
            duplicates = {x for x in all_ids if x in seen or seen.add(x)}
            raise ValueError(f"Duplicate case IDs found in suite: {duplicates}")

        return True

    def __len__(self) -> int:
        return len(self.cases)

    def __iter__(self):
        return iter(self.cases)

    def __getitem__(self, idx: int) -> BenchmarkCase:
        return self.cases[idx]
