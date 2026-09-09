"""Read-only native recommendation/disposition ledger for final summaries.

Owner reports remain authoritative. This automation helper never creates a
recommendation ID, evaluates economic promotion, or authorizes runtime changes.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from src.engine.automation.postclose_workorder_contract import (
    AUTHORITY_FLAGS,
    EFFECTIVE_DATE,
    authority_class,
    contract_issues,
    digest,
)
from src.engine.monitoring.machine_recommendation_identity import (
    recommendation_inventory,
)

SCHEMA = "postclose_recommendation_intake_v1"
DISPOSITION_SCHEMA = "postclose_recommendation_dispositions_v1"
SECTION_START = "<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->"
SECTION_END = "<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->"
SOURCE_LABELS = (
    "code_improvement_workorder",
    "widget_collector_expansion_recommendation",
    "widget_advisory_calibration",
    "widget_auto_trade_policy_calibration",
    "widget_symbol_signal_policy_research",
    "widget_symbol_runtime_policy_apply",
    "samsung_machine_entry_tuning",
    "low_price_two_leg_tuning",
    "low_price_two_leg_expanded_candidate_research",
    "machine_microstructure_attribution",
    "machine_entry_timing_tuning",
    "machine_microstructure_policy_approval",
)
IMPLEMENT = {"implement_now", "code_patch_required", "already_implemented"}
COMPLETED = {"already_implemented_verified", "implemented_pass1", "implemented_pass2"}
DISPOSITIONS = COMPLETED | {
    "blocked_missing_evidence",
    "blocked_external_dependency",
    "user_authority",
    "invalid_or_missing_authority",
    "observed_no_patch",
    "deferred",
    "rejected",
    "eligible_actionable_open",
}


def source_paths(report_dir: Path, target_date: str) -> dict[str, Path]:
    report_dir = report_dir.resolve()
    result = {
        label: report_dir
        / label
        / (
            f"{label}_{'postclose_' if label == 'machine_microstructure_policy_approval' else ''}{target_date}.json"
        )
        for label in SOURCE_LABELS
    }
    result["postclose_recommendation_dispositions"] = (
        report_dir
        / "postclose_recommendation_dispositions"
        / f"postclose_recommendation_dispositions_{target_date}.json"
    )
    # Evidence is acyclic (code/review/test/direct source), not a summary or
    # verifier referring back to this ledger. Its bytes participate in freshness.
    receipt, _, _ = _read(result["postclose_recommendation_dispositions"])
    root = report_dir.parent.parent.resolve()
    for index, row in enumerate(
        receipt.get("rows", []) if isinstance(receipt.get("rows"), list) else []
    ):
        for offset, evidence in enumerate(
            row.get("evidence", [])
            if isinstance(row, dict) and isinstance(row.get("evidence"), list)
            else []
        ):
            path = _evidence_path(evidence, root)
            if path is not None:
                result[f"disposition_evidence_{index}_{offset}"] = path
    return result


def _read(path: Path) -> tuple[dict[str, Any], str | None, str | None]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return {}, None, "missing"
    except OSError:
        return {}, None, "read_error"
    sha = hashlib.sha256(raw).hexdigest()
    try:

        def reject_constant(value: str) -> None:
            raise ValueError(f"nonfinite JSON: {value}")

        def finite_float(value: str) -> float:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("nonfinite JSON number")
            return number

        data = json.loads(raw, parse_constant=reject_constant, parse_float=finite_float)
        if not isinstance(data, dict):
            raise ValueError("object required")
        return data, sha, None
    except (ValueError, UnicodeError):
        return {}, sha, "invalid_json"


def _report_date(report: dict[str, Any]) -> Any:
    return next(
        (
            report[key]
            for key in (
                "source_target_date",
                "target_date",
                "date",
                "end_date",
                "source_date",
            )
            if report.get(key)
        ),
        None,
    )


def _authority(row: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    inherited = report.get("authority")
    inherited = inherited if isinstance(inherited, dict) else report
    local = row.get("authority")
    local = local if isinstance(local, dict) else {}
    return {
        key: row[key] if key in row else local.get(key, inherited.get(key))
        for key in (
            "runtime_effect",
            "allowed_runtime_apply",
            *AUTHORITY_FLAGS,
            "broker_order_forbidden",
        )
    }


def _default_disposition(row: dict[str, Any]) -> str:
    if row["authority_class"] == "invalid_or_missing_authority" or not row["native_id"]:
        return "invalid_or_missing_authority"
    if row["authority_class"] == "user_authority":
        return "user_authority"
    decision = row["decision"]
    if row["implementation_requested"]:
        if not all(
            _valid_contract_text(row[k])
            for k in ("consumer", "acceptance", "implementation_location")
        ):
            return "blocked_missing_evidence"
        return "eligible_actionable_open"
    if decision in {"reject", "rejected", "holdout_failed_no_widget_runtime_promotion"}:
        return "rejected"
    if decision in {
        "defer",
        "defer_evidence",
        "defer_design",
        "design_family_candidate",
        "research_watch",
        "source_only_requires_review_and_user_approval",
    }:
        return "deferred"
    if decision in {
        "observe",
        "keep_collecting",
        "attach_existing_family",
        "EVIDENCE_ACCUMULATING",
        "objective_followup_required",
        "hold",
        "hold_sample",
        "hold_no_edge",
    }:
        return "observed_no_patch"
    # Unknown decisions are visible evidence gaps, never invented implementation orders.
    return "blocked_missing_evidence"


def _valid_contract_text(value: Any) -> bool:
    return (isinstance(value, str) and bool(value.strip())) or (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def _entry(
    owner: str,
    native_id: Any,
    raw: dict[str, Any],
    report: dict[str, Any],
    *,
    label: str,
    path: Path,
    sha: str,
    location: str,
) -> dict[str, Any]:
    native_id = (
        native_id
        if isinstance(native_id, str)
        and native_id.strip()
        and native_id == native_id.strip()
        else None
    )
    decision_field = next(
        (
            key
            for key in (
                "decision",
                "recommendation_tier",
                "implementation_status",
                "state",
            )
            if isinstance(raw.get(key), str) and raw[key]
        ),
        None,
    )
    decision = raw.get(decision_field) if decision_field else None
    consumer = (
        raw.get("recommendation_consumer")
        or raw.get("required_downstream")
        or raw.get("intended_consumer")
    )
    acceptance = (
        raw.get("recommendation_acceptance")
        or raw.get("acceptance_tests")
        or raw.get("acceptance_test")
    )
    implementation_location = raw.get("files_likely_touched") or raw.get(
        "implementation_location"
    )
    authority = _authority(raw, report)
    requested = decision in IMPLEMENT or (
        decision == "objective_followup_required"
        and all(
            _valid_contract_text(value)
            for value in (consumer, acceptance, implementation_location)
        )
    )
    entry = {
        "owner": owner,
        "native_id": native_id,
        "decision_field": decision_field,
        "decision": decision,
        "authority": authority,
        "authority_class": authority_class(authority),
        "consumer": consumer,
        "acceptance": acceptance,
        "implementation_location": implementation_location,
        "implementation_requested": requested,
        "row_sha256": digest(raw),
        "sources": [
            {"label": label, "path": str(path), "sha256": sha, "location": location}
        ],
        "code_review": "unverified",
        "deployment": "unverified",
        "natural_consumption": "unverified",
        "economic_acceptance": "not_evaluated_by_handoff",
    }
    entry["final_disposition"] = _default_disposition(entry)
    return entry


def _evidence_path(evidence: Any, root: Path) -> Path | None:
    if (
        not isinstance(evidence, dict)
        or not isinstance(evidence.get("path"), str)
        or not evidence["path"]
    ):
        return None
    try:
        path = (root / evidence["path"]).resolve()
    except (OSError, ValueError, RuntimeError):
        return None
    if not path.is_relative_to(root.resolve()) or any(
        token in str(path)
        for token in (
            "postclose_recommendation_dispositions",
            "tuning_performance_control_tower",
            "threshold_cycle_postclose_verification",
            "postclose_done_controller",
            "stage2-todo-checklist",
        )
    ):
        return None
    return path


def _evidence_valid(item: dict[str, Any], root: Path) -> bool:
    evidence = item.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return False
    kinds = set()
    for evidence_row in evidence:
        path = _evidence_path(evidence_row, root)
        if (
            path is None
            or not path.is_file()
            or not isinstance(evidence_row.get("kind"), str)
        ):
            return False
        try:
            valid_hash = hashlib.sha256(
                path.read_bytes()
            ).hexdigest() == evidence_row.get("sha256")
        except OSError:
            valid_hash = False
        if not valid_hash:
            return False
        kinds.add(evidence_row.get("kind"))
    required = {"code_review", "targeted_validation", "consumer_handoff"}
    return (
        required.issubset(kinds)
        if item.get("final_disposition") in COMPLETED
        else bool(kinds)
    )


def _native_rows(payload: dict[str, Any], label: str):
    """Walk only native recommendation surfaces, never broker order IDs.

    Invalid siblings stay in the denominator with their original location. A bad
    row must not discard an entire producer's otherwise valid recommendations.
    """

    def visit(value: Any, location: str, kind: str | None = None):
        if isinstance(value, dict):
            if (
                "recommendation_id" in value or kind == "recommendation"
            ) and kind not in {"workorder", "followup"}:
                probe = {
                    k: v
                    for k, v in value.items()
                    if k.startswith("recommendation_")
                    or k in ("runtime_effect", "allowed_runtime_apply", "decision")
                }
                try:
                    recommendation_inventory({"recommendations": [probe]})
                    valid = True
                except (ValueError, TypeError):
                    valid = False
                scope = value.get("recommendation_scope")
                owner = scope.get("producer") if isinstance(scope, dict) else None
                yield (
                    owner if isinstance(owner, str) and owner else label,
                    value.get("recommendation_id"),
                    value,
                    location,
                    valid,
                    "recommendation",
                )
            elif kind == "workorder":
                yield (label, value.get("order_id"), value, location, True, "workorder")
            elif kind == "followup":
                owner = (
                    "machine_microstructure_attribution"
                    if label == "machine_microstructure_policy_approval"
                    else label
                )
                yield (
                    owner,
                    value.get("followup_id"),
                    value,
                    location,
                    True,
                    "followup",
                )
            for key, child in value.items():
                child_kind = {
                    "recommendations": "recommendation",
                    "postclose_logic_recommendations": "recommendation",
                    "code_improvement_orders": "workorder",
                    "objective_followups": "followup",
                }.get(key)
                child_path = f"{location}[{json.dumps(key)}]"
                if child_kind and not isinstance(child, list):
                    yield (
                        label,
                        None,
                        {"invalid_value": child},
                        child_path,
                        False,
                        child_kind,
                    )
                else:
                    yield from visit(child, child_path, child_kind)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from visit(child, f"{location}[{index}]", kind)
        elif kind:
            yield (label, None, {"invalid_value": value}, location, False, kind)

    yield from visit(payload, "$")


def build_intake(report_dir: Path, target_date: str) -> dict[str, Any]:
    """Build a deterministic read-only ledger; never count a claimed fix as verified."""
    report_dir = report_dir.resolve()
    paths = source_paths(report_dir, target_date)
    rows: list[dict[str, Any]] = []
    sources = {}
    issues = []
    for label in SOURCE_LABELS:
        payload, sha, error = _read(paths[label])
        sources[label] = {"sha256": sha, "status": error or "loaded"}
        if error:
            # Missing sources remain explicit. Existing producer/mandatory-stage guards
            # own due status, so early summary rendering does not invent a new wait floor.
            if error != "missing":
                issues.append(f"{label}:{error}")
            continue
        if _report_date(payload) != target_date:
            issues.append(f"{label}:target_date_mismatch")
            continue
        if label == "code_improvement_workorder":
            issues.extend(
                f"main:{issue}" for issue in contract_issues(payload, target_date)
            )
            for partition in ("orders", "non_selected_orders"):
                values = payload.get(partition)
                for index, raw in enumerate(values if isinstance(values, list) else []):
                    if not isinstance(raw, dict):
                        issues.append(f"main:{partition}[{index}]:invalid_row")
                        continue
                    rows.append(
                        _entry(
                            "main",
                            raw.get("order_id"),
                            raw,
                            payload,
                            label=label,
                            path=paths[label],
                            sha=sha,
                            location=f"$.{partition}[{index}]",
                        )
                    )
            continue
        for owner, native_id, raw, location, valid, kind in _native_rows(
            payload, label
        ):
            entry = _entry(
                owner,
                native_id,
                raw,
                payload,
                label=label,
                path=paths[label],
                sha=sha,
                location=location,
            )
            entry["native_kind"] = kind
            entry["identity_valid"] = valid and entry["native_id"] is not None
            # Mirror comparison retains only the shared semantic contract, not
            # display-only fields added by the approval consumer.
            entry["mirror_contract"] = {
                key: raw.get(key)
                for key in (
                    "recommendation_contract",
                    "recommendation_scope",
                    "recommendation_proposal_sha256",
                    "recommendation_consumer",
                    "recommendation_acceptance",
                    "followup_id",
                    "source_date",
                    "state",
                    "metric_contract",
                    "current_capability",
                    "next_action",
                    "remaining_gap_codes",
                )
                if key in raw
            }
            if not entry["identity_valid"]:
                entry["authority_class"] = "invalid_or_missing_authority"
                entry["final_disposition"] = "invalid_or_missing_authority"
                # This row has an exact source location and remains accounted for.
                # Quarantine it without making unrelated owner completion fail.
                entry["validation_issues"] = ["native_identity_invalid"]
            rows.append(entry)
    by_key = {}
    unique = []
    for row in rows:
        key = (row["owner"], row["native_id"])
        if row["native_id"] is None:
            unique.append(row)
        elif key not in by_key:
            by_key[key] = row
            unique.append(row)
        else:
            old = by_key[key]
            mirror = (
                row.get("native_kind") in {"recommendation", "followup"}
                and row.get("native_kind") == old.get("native_kind")
                and row.get("identity_valid")
                and old.get("identity_valid")
                and all(
                    digest(row.get(k)) == digest(old.get(k))
                    for k in (
                        "mirror_contract",
                        "authority",
                        "authority_class",
                        "decision",
                        "consumer",
                        "acceptance",
                        "implementation_location",
                    )
                )
            )
            if not mirror:
                issues.append(f"duplicate_or_conflicting_native_id:{key[0]}:{key[1]}")
            old["sources"].extend(row["sources"])
    dispositions, sha, error = _read(paths["postclose_recommendation_dispositions"])
    sources["postclose_recommendation_dispositions"] = {
        "sha256": sha,
        "status": error or "loaded",
    }
    if error != "missing":
        if (
            error
            or dispositions.get("schema") != DISPOSITION_SCHEMA
            or dispositions.get("source_date") != target_date
            or dispositions.get("runtime_effect") is not False
            or dispositions.get("allowed_runtime_apply") is not False
            or not isinstance(dispositions.get("rows"), list)
        ):
            issues.append("disposition_contract_invalid")
        else:
            seen = set()
            for item in dispositions["rows"]:
                if not isinstance(item, dict):
                    issues.append("disposition_row_invalid")
                    continue
                key = (item.get("owner"), item.get("native_id"))
                if not all(isinstance(value, str) for value in key):
                    issues.append("disposition_identity_invalid")
                    continue
                row = by_key.get(key)
                if key in seen or not row:
                    issues.append(f"disposition_unmatched_or_duplicate:{key}")
                    continue
                seen.add(key)
                if (
                    item.get("row_sha256") != row["row_sha256"]
                    or not isinstance(item.get("source_sha256"), str)
                    or item.get("source_sha256")
                    not in {s["sha256"] for s in row["sources"]}
                    or not isinstance(item.get("final_disposition"), str)
                    or item.get("final_disposition") not in DISPOSITIONS
                    or any(
                        not isinstance(item.get(k), str) or not item[k].strip()
                        for k in ("reason", "acceptance_owner")
                    )
                    or not _evidence_valid(item, report_dir.parent.parent)
                ):
                    issues.append(f"disposition_evidence_invalid:{key}")
                    continue
                if row["authority_class"] != "eligible_runtime_effect_false":
                    issues.append(f"disposition_authority_mismatch:{key}")
                    continue
                allowed = (
                    COMPLETED
                    | {
                        "blocked_missing_evidence",
                        "blocked_external_dependency",
                        "eligible_actionable_open",
                    }
                    if row["implementation_requested"]
                    else {
                        "observed_no_patch",
                        "deferred",
                        "rejected",
                        "blocked_missing_evidence",
                        "blocked_external_dependency",
                    }
                )
                if item["final_disposition"] not in allowed:
                    issues.append(f"disposition_request_class_mismatch:{key}")
                    continue
                row["final_disposition"] = item["final_disposition"]
                row["disposition_receipt"] = item
                if item["final_disposition"] in COMPLETED:
                    row["code_review"] = "verified_with_consumer_and_tests"
    unique.sort(key=lambda r: (r["owner"], r["native_id"] or "", str(r["sources"])))
    counts = {
        "intake_total": len(unique),
        "implementation_requested_total": 0,
        "nonimplementation_total": 0,
        "eligible_runtime_effect_false_total": 0,
        "user_authority_total": 0,
        "invalid_or_missing_authority_total": 0,
        "eligible_actionable_open": 0,
        "intake_unaccounted_count": 0,
        "implement_now_unaccounted_count": 0,
    }
    eligible_keys = {
        "already_implemented_verified": "already_implemented_verified_eligible",
        "implemented_pass1": "implemented_pass1",
        "implemented_pass2": "implemented_pass2",
        "blocked_missing_evidence": "blocked_missing_evidence",
        "blocked_external_dependency": "blocked_external_dependency",
        "eligible_actionable_open": "eligible_actionable_open",
    }
    nonrequest_keys = {
        "already_implemented_verified": "already_implemented_verified_nonrequest",
        "observed_no_patch": "observed_no_patch",
        "deferred": "deferred",
        "rejected": "rejected",
        "blocked_missing_evidence": "blocked_missing_evidence_nonrequest",
        "blocked_external_dependency": "blocked_external_dependency_nonrequest",
        "invalid_or_missing_authority": "invalid_or_missing_authority_nonrequest",
        "user_authority": "user_authority_nonrequest",
    }
    counts.update(
        {key: 0 for key in (*eligible_keys.values(), *nonrequest_keys.values())}
    )
    for row in unique:
        requested = row["implementation_requested"]
        counts[
            "implementation_requested_total" if requested else "nonimplementation_total"
        ] += 1
        if requested:
            authority = (
                row["authority_class"]
                if row["native_id"]
                else "invalid_or_missing_authority"
            )
            counts[f"{authority}_total"] += 1
            if authority == "eligible_runtime_effect_false":
                bucket = eligible_keys.get(row["final_disposition"])
                if bucket:
                    counts[bucket] += 1
                else:
                    counts["implement_now_unaccounted_count"] += 1
        else:
            bucket = nonrequest_keys.get(row["final_disposition"])
            if bucket:
                counts[bucket] += 1
            else:
                counts["intake_unaccounted_count"] += 1
    counts["intake_unaccounted_count"] += counts["implement_now_unaccounted_count"]
    conservation = (
        counts["intake_total"]
        == counts["implementation_requested_total"] + counts["nonimplementation_total"]
        and counts["implementation_requested_total"]
        == sum(
            counts[k]
            for k in (
                "eligible_runtime_effect_false_total",
                "user_authority_total",
                "invalid_or_missing_authority_total",
            )
        )
        and counts["eligible_runtime_effect_false_total"]
        == sum(counts[k] for k in eligible_keys.values())
        and counts["nonimplementation_total"]
        == sum(counts[k] for k in nonrequest_keys.values())
    )
    if not conservation or counts["intake_unaccounted_count"]:
        issues.append("intake_conservation_failed")
    dispositions_count = dict(
        sorted(Counter(r["final_disposition"] for r in unique).items())
    )
    owners = {
        owner: dict(
            sorted(
                Counter(
                    r["final_disposition"] for r in unique if r["owner"] == owner
                ).items()
            )
        )
        for owner in sorted({r["owner"] for r in unique})
    }
    blocked = sum(
        n
        for key, n in dispositions_count.items()
        if key
        in {
            "blocked_missing_evidence",
            "blocked_external_dependency",
            "invalid_or_missing_authority",
            "user_authority",
        }
    )
    missing_sources = [
        label for label in SOURCE_LABELS if sources[label]["status"] == "missing"
    ]
    return {
        "schema": SCHEMA,
        "source_date": target_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "sources": sources,
        "rows": unique,
        "counts": counts,
        "disposition_counts": dispositions_count,
        "owner_counts": owners,
        "issues": sorted(set(issues)),
        "rows_sha256": digest(unique),
        "conservation_pass": conservation,
        "missing_sources": missing_sources,
        "status": (
            "fail"
            if issues
            else (
                "waiting_sources"
                if missing_sources
                else (
                    "actionable_open"
                    if counts["eligible_actionable_open"]
                    else "warning" if blocked else "accounted"
                )
            )
        ),
        "implementation_fixed_point": not issues
        and not missing_sources
        and not counts["eligible_actionable_open"],
        "all_implementations_completed": not issues
        and not missing_sources
        and not blocked
        and not counts["eligible_actionable_open"],
        "metric_contract": {
            "metric_role": "recommendation_handoff_integrity",
            "decision_authority": "source_only_tracking_not_policy_apply",
            "window_policy": "exact_source_generation",
            "sample_floor": "all_native_recommendations_no_economic_floor",
            "primary_decision_metric": "intake_unaccounted_count",
            "source_quality_gate": "exact_source_native_identity_authority_and_receipt",
            "forbidden_uses": [
                "runtime_policy_mutation",
                "broker_authority",
                "economic_acceptance_substitution",
            ],
        },
    }


def markdown_section(intake: dict[str, Any]) -> str:
    """Deterministic visible projection verified independently of source hash markers."""
    lines = [
        SECTION_START,
        "## 추천 전수 전달 대사",
        "",
        f"- source-date: `{intake['source_date']}`; status: `{intake['status']}`",
        f"- native rows SHA256: `{intake['rows_sha256']}`",
        f"- counts: `{json.dumps(intake['counts'], sort_keys=True)}`",
        f"- dispositions: `{json.dumps(intake['disposition_counts'], sort_keys=True)}`",
        "- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.",
        "",
        "| Owner | Native recommendation dispositions |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| {owner} | `{json.dumps(counts, sort_keys=True)}` |"
        for owner, counts in intake["owner_counts"].items()
    )
    lines.extend([SECTION_END, ""])
    return "\n".join(lines)
