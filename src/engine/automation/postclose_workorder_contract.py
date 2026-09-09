"""Complete workorder identity/authority contracts; no runtime authority.

The automation layer owns this validation, not an engine-root producer or a
strategy family. Selection is presentation: it never changes the intake set.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

EFFECTIVE_DATE = "2026-09-09"
SCHEMA = "postclose_workorder_inventory_v1"
PARTITIONS = ("orders", "non_selected_orders")
AUTHORITY_FLAGS = (
    "actual_order_submitted",
    "real_order_authority",
    "order_authority",
    "runtime_authority",
    "provider_authority",
    "bot_authority",
    "safety_authority",
    "runtime_registry_mutation_allowed",
    "provider_budget_increase_allowed",
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def all_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for key in PARTITIONS
        for row in (report[key] if isinstance(report.get(key), list) else [])
        if isinstance(row, dict)
    ]


def exact_equal(left: Any, right: Any) -> bool:
    """JSON identity must distinguish false from 0 and reject nonfinite values."""
    try:
        return digest(left) == digest(right)
    except (ValueError, TypeError, OverflowError):
        return False


def authority_class(row: dict[str, Any]) -> str:
    values = [row.get(key) for key in ("runtime_effect", "allowed_runtime_apply")]
    if any(type(value) is not bool for value in values):
        return "invalid_or_missing_authority"
    for key in (*AUTHORITY_FLAGS, "broker_order_forbidden"):
        if row.get(key) is not None and type(row[key]) is not bool:
            return "invalid_or_missing_authority"
    if (
        any(values)
        or any(row.get(key) is True for key in AUTHORITY_FLAGS)
        or row.get("broker_order_forbidden") is False
    ):
        return "user_authority"
    return "eligible_runtime_effect_false"


def inventory(report: dict[str, Any]) -> dict[str, Any]:
    rows = all_orders(report)
    projection = sorted(
        (
            {
                "order_id": row.get("order_id"),
                "decision": row.get("decision"),
                "authority_class": authority_class(row),
                "row_sha256": digest(row),
            }
            for row in rows
        ),
        key=lambda row: str(row["order_id"]),
    )
    return {
        "schema": SCHEMA,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "total": len(rows),
        "rows_sha256": digest(projection),
        "decision_counts": dict(
            sorted(Counter(str(row.get("decision")) for row in rows).items())
        ),
        "authority_counts": dict(
            sorted(Counter(authority_class(row) for row in rows).items())
        ),
    }


def contract_issues(report: dict[str, Any], target_date: str) -> list[str]:
    """Validate schema2 including historical schema2, and reject new legacy input."""
    if report.get("schema_version") != 2 and target_date < EFFECTIVE_DATE:
        return []
    issues: list[str] = []
    if (
        type(report.get("schema_version")) is not int
        or report.get("schema_version") != 2
    ):
        issues.append("schema_invalid")
    if report.get("date") != target_date:
        issues.append("target_date_mismatch")
    for key in PARTITIONS:
        if not isinstance(report.get(key), list) or any(
            not isinstance(row, dict) for row in report.get(key, [])
        ):
            issues.append(f"{key}_invalid")
    if any(f"{key}_invalid" in issues for key in PARTITIONS):
        return issues
    rows = all_orders(report)
    ids = [row.get("order_id") for row in rows]
    if any(
        not isinstance(value, str) or not value.strip() or value != value.strip()
        for value in ids
    ):
        issues.append("native_id_missing_or_invalid")
    valid_ids = [value for value in ids if isinstance(value, str)]
    if len(set(valid_ids)) != len(valid_ids):
        issues.append("native_id_duplicate")
    if any(
        not isinstance(row.get("decision"), str) or not row["decision"].strip()
        for row in rows
    ):
        issues.append("decision_missing_or_invalid")
    summary = report.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    for key, expected in (
        ("source_order_count", len(rows)),
        ("selected_order_count", len(report["orders"])),
        ("non_selected_order_count", len(report["non_selected_orders"])),
    ):
        if type(summary.get(key)) is not int or summary[key] != expected:
            issues.append(f"{key}_mismatch")
    for key, subset in (
        ("decision_counts", rows),
        ("selected_decision_counts", report["orders"]),
        ("non_selected_decision_counts", report["non_selected_orders"]),
    ):
        expected = dict(Counter(str(row.get("decision")) for row in subset))
        counts = summary.get(key)
        if (
            not isinstance(counts, dict)
            or any(type(v) is not int for v in counts.values())
            or counts != expected
        ):
            issues.append(f"{key}_mismatch")
    entries = report.get("source_fingerprint")
    if (
        not isinstance(entries, list)
        or not entries
        or any(not isinstance(e, dict) for e in entries)
    ):
        issues.append("source_fingerprint_missing_or_invalid")
    else:
        labels = [e.get("label") for e in entries]
        if any(not isinstance(label, str) or not label for label in labels) or len(
            set(map(str, labels))
        ) != len(labels):
            issues.append("source_labels_missing_or_duplicate")
        if any(type(e.get("exists")) is not bool for e in entries):
            issues.append("source_exists_not_boolean")
        if report.get("source_hash") != digest(entries):
            issues.append("source_hash_mismatch")
    inputs = report.get("generation_inputs")
    if not isinstance(inputs, dict):
        issues.append("generation_inputs_missing")
    else:
        if (
            inputs.get("source_hash") != report.get("source_hash")
            or inputs.get("schema_version") != report.get("schema_version")
            or inputs.get("producer_contract_version")
            != report.get("producer_contract_version")
            or not isinstance(report.get("producer_contract_version"), str)
            or not report.get("producer_contract_version")
            or type(inputs.get("max_orders")) is not int
            or inputs["max_orders"] < 1
            or type(inputs.get("include_swing")) is not bool
        ):
            issues.append("generation_inputs_invalid")
        expected_hash = digest(inputs)
        if (
            report.get("generation_hash") != expected_hash
            or report.get("generation_id") != f"{target_date}-{expected_hash[:12]}"
        ):
            issues.append("generation_identity_mismatch")
    # Malformed row authority is quarantined, never silently coerced to false.
    # The published inventory makes that loss visible without blocking unrelated families.
    if target_date >= EFFECTIVE_DATE or "inventory_contract" in report:
        if not any(
            code in issues
            for code in ("decision_missing_or_invalid", "native_id_missing_or_invalid")
        ):
            if not exact_equal(report.get("inventory_contract"), inventory(report)):
                issues.append("inventory_contract_mismatch")
    return sorted(set(issues))
