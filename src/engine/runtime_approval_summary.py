"""Summarize family-owned postclose evidence and direct runtime handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.automation.runtime_policy_bootstrap import (
    direct_policy_digest,
    validate_rising_missed_policy_receipt,
)
from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "runtime_approval_summary"
MAX_DIRECT_JSON_BYTES = 64 * 1024 * 1024

DIRECT_EVIDENCE_COMPLETE = "direct_evidence_complete"
DIRECT_EVIDENCE_INCOMPLETE = "direct_evidence_incomplete"

PRIMARY_DIRECT_OWNERS = (
    "source_quality",
    "entry_cancel_wait",
    "entry_split",
    "scale_in_split",
    "machine_entry",
    "low_price_two_leg",
    "low_price_expansion",
    "ws_freshness",
    "ai_outcome",
    "rising_missed",
)
REQUIRED_DIRECT_OWNERS = frozenset(PRIMARY_DIRECT_OWNERS)

PRODUCER_FLAG_BY_OWNER = {
    "source_quality": "observation_source_quality_audit",
    "entry_split": "entry_split_order_plan",
    "scale_in_split": "scale_in_split_order_plan",
    "machine_entry": "samsung_machine_entry_tuning",
    "low_price_two_leg": "low_price_two_leg_tuning",
    "low_price_expansion": "low_price_two_leg_candidate_recommendation",
    "ws_freshness": "intraday_ws_freshness_finalize",
    "ai_outcome": "ai_decision_action_outcome_calibration",
    "rising_missed": "rising_missed_classifier_prior",
}

POLICY_OWNER_BY_SOURCE = {
    "entry_cancel_wait": "entry_cancel_wait_policy",
    "entry_split": "entry_split_policy",
    "scale_in_split": "scale_in_split_policy",
    "machine_entry": "machine_entry_candidate",
    "low_price_two_leg": "low_price_candidate",
    "low_price_expansion": "low_price_expansion_policy",
    "rising_missed": "rising_missed_policy",
}

DEFAULT_CLOSURE_OWNER = {
    "source_quality": "observation_source_quality_audit",
    "entry_cancel_wait": "entry_cancel_wait_tuning",
    "entry_split": "entry_split_order_plan",
    "scale_in_split": "scale_in_split_order_plan",
    "machine_entry": "samsung_machine_entry_tuning",
    "low_price_two_leg": "low_price_two_leg_tuning",
    "low_price_expansion": "low_price_two_leg_expanded_candidate_research",
    "ws_freshness": "intraday_ws_freshness_monitor",
    "ai_outcome": "ai_decision_action_outcome_calibration",
    "rising_missed": "rising_missed_classifier_prior",
}


def summary_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"runtime_approval_summary_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _paths(target_date: str) -> dict[str, Path]:
    report = DATA_DIR / "report"
    threshold = DATA_DIR / "threshold_cycle"
    return {
        "source_quality": report / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json",
        "entry_cancel_wait": report / "entry_cancel_wait_tuning" / f"entry_cancel_wait_tuning_{target_date}.json",
        "entry_cancel_wait_policy": report / "entry_cancel_wait_tuning" / f"entry_cancel_wait_policy_{target_date}.json",
        "entry_split": report / "entry_split_order_plan" / f"entry_split_order_plan_{target_date}.json",
        "entry_split_policy": threshold / "entry_split_order_policy" / f"entry_split_order_policy_{target_date}.json",
        "scale_in_split": report / "scale_in_split_order_plan" / f"scale_in_split_order_plan_{target_date}.json",
        "scale_in_split_policy": threshold / "scale_in_split_order_policy" / f"scale_in_split_order_policy_{target_date}.json",
        "machine_entry": report / "samsung_machine_entry_tuning" / f"samsung_machine_entry_tuning_{target_date}.json",
        "machine_entry_candidate": threshold / "samsung_machine_entry_policy" / "candidates" / f"samsung_machine_entry_policy_candidate_{target_date}.json",
        "low_price_two_leg": report / "low_price_two_leg_tuning" / f"low_price_two_leg_tuning_{target_date}.json",
        "low_price_candidate": threshold / "low_price_two_leg" / "candidates" / f"low_price_two_leg_policy_candidate_{target_date}.json",
        "low_price_expansion": report / "low_price_two_leg_expanded_candidate_research" / f"low_price_two_leg_expanded_candidate_research_{target_date}.json",
        "low_price_expansion_policy": DATA_DIR / "runtime" / "low_price_two_leg_auto_expansion" / f"low_price_two_leg_auto_expansion_{target_date}.json",
        "ws_freshness": report / "intraday_ws_freshness_monitor" / f"intraday_ws_freshness_monitor_{target_date}.json",
        "ai_outcome": report / "ai_decision_action_outcome_calibration" / f"ai_decision_action_outcome_calibration_{target_date}.json",
        "rising_missed": report / "rising_missed_classifier_prior" / f"rising_missed_classifier_prior_{target_date}.json",
        "rising_missed_policy": report / "rising_missed_classifier_prior" / f"rising_missed_tp1_policy_source_{target_date}.json",
        "runtime_bootstrap": DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_{target_date}.json",
        "runtime_bootstrap_verify": DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_verify_{target_date}.json",
    }


def _postclose_status_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json"


def _read(path: Path) -> tuple[dict[str, Any], str | None, str, int | None]:
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return {}, "missing", "absent", None
    except OSError as exc:
        return {}, f"unreadable:{type(exc).__name__}", "stat_failed", None
    if size > MAX_DIRECT_JSON_BYTES:
        return {}, None, "stream_hash_only_large_json", size
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {}, f"unreadable:{type(exc).__name__}", "bounded_json", size
    if not isinstance(value, dict):
        return {}, "object_required", "bounded_json", size
    return value, None, "bounded_json", size


def _load_json(path: Path) -> dict[str, Any]:
    value, error, _, _ = _read(path)
    return value if error is None else {}


def _read_top_level_sections(path: Path, wanted: set[str]) -> dict[str, Any]:
    """Read selected pretty-printed top-level members without materializing JSON."""
    sections: dict[str, Any] = {}
    current: str | None = None
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.startswith('  "'):
                    if current in wanted:
                        sections[current] = json.loads(
                            "".join(sections[current]).rstrip().rstrip(",")
                        )
                    current = line.split('"', 2)[1]
                    if current in wanted:
                        sections[current] = [line.split(":", 1)[1]]
                elif current in wanted:
                    if line.strip() == "}" and line.startswith("}"):
                        sections[current] = json.loads(
                            "".join(sections[current]).rstrip().rstrip(",")
                        )
                        current = None
                    else:
                        sections[current].append(line)
    except (OSError, ValueError, TypeError):
        return {}
    return sections if wanted <= sections.keys() else {}


def _sha(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _date_matches(payload: dict[str, Any], target_date: str) -> bool:
    values = [payload.get(key) for key in ("target_date", "date", "source_date", "end_date") if payload.get(key)]
    return bool(values) and target_date in {str(value) for value in values}


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _flag_enabled(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _owner_requirements(target_date: str) -> tuple[dict[str, bool], dict[str, Any]]:
    status_path = _postclose_status_path(target_date)
    status = _load_json(status_path)
    flags = status.get("producer_flags") if isinstance(status.get("producer_flags"), dict) else {}
    required: dict[str, bool] = {}
    missing_flags: list[str] = []
    for owner in PRIMARY_DIRECT_OWNERS:
        flag = PRODUCER_FLAG_BY_OWNER.get(owner)
        if flag is not None and flag not in flags:
            missing_flags.append(flag)
        required[owner] = True if flag is None else _flag_enabled(flags.get(flag), True)
    return required, {
        "path": str(status_path),
        "exists": status_path.exists(),
        "sha256": _sha(status_path),
        "producer_flags": flags,
        "fallback_used": bool(missing_flags),
        "missing_producer_flags": sorted(missing_flags),
        "fallback_contract": "current_wrapper_default_active_direct_owners",
    }


def _large_companion(
    owner: str,
    path: Path,
    target_date: str,
    artifact_sha256: str | None,
    paths: dict[str, Path],
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    if owner == "low_price_two_leg":
        companion_path = paths["low_price_candidate"]
        payload, error, read_mode, _ = _read(companion_path)
        projection = _read_top_level_sections(
            path,
            {"schema", "target_date", "artifact_hash", "paired_economic_search"},
        )
        embedded_sha = projection.get("artifact_hash")
        source_path = Path(str(payload.get("source_report_path") or ""))
        source_name_matches = source_path.name == path.name
        semantic_sha_matches = bool(
            embedded_sha and payload.get("source_report_artifact_hash") == embedded_sha
        )
        projection_matches = bool(
            projection.get("target_date") == target_date
            and payload.get("source_report_schema") == projection.get("schema")
            and payload.get("paired_economic_search") == projection.get("paired_economic_search")
        )
        verified = (
            error is None and _date_matches(payload, target_date) and source_name_matches
            and semantic_sha_matches and projection_matches
        )
        return payload, {
            "path": str(companion_path),
            "sha256": _sha(companion_path),
            "read_mode": read_mode,
            "contract": "low_price_candidate_source_semantic_hash",
            "source_name_matches": source_name_matches,
            "source_semantic_sha256": embedded_sha,
            "semantic_sha_matches": semantic_sha_matches,
            "economic_projection_matches": projection_matches,
            "verified": verified,
        }, None if verified else "semantic_unverified_large_source"
    if owner == "low_price_expansion":
        companion_path = path.with_name(path.name + ".reuse-contract.json")
        payload, error, read_mode, _ = _read(companion_path)
        source_path = Path(str(payload.get("artifact_path") or ""))
        source_name_matches = source_path.name == path.name
        byte_sha_matches = bool(artifact_sha256 and payload.get("artifact_sha256") == artifact_sha256)
        verified = error is None and _date_matches(payload, target_date) and source_name_matches and byte_sha_matches
        return payload, {
            "path": str(companion_path),
            "sha256": _sha(companion_path),
            "read_mode": read_mode,
            "contract": "postclose_artifact_reuse_contract_v1",
            "source_name_matches": source_name_matches,
            "artifact_sha_matches": byte_sha_matches,
            "verified": verified,
        }, None if verified else "semantic_unverified_large_source"
    return {}, {"path": None, "sha256": None, "contract": None, "verified": False}, "semantic_unverified_large_source"


def _dict_value(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _economic_section(owner: str, payload: dict[str, Any]) -> dict[str, Any]:
    if owner == "entry_cancel_wait":
        return _dict_value(payload, "economic_evaluation")
    if owner == "entry_split":
        return _dict_value(payload, "economic_acceptance")
    if owner == "scale_in_split":
        return _dict_value(payload, "evaluation_state")
    if owner == "low_price_two_leg":
        return _dict_value(payload, "paired_economic_search")
    if owner == "ws_freshness":
        return _dict_value(payload, "postclose_quality_handoff")
    if owner == "ai_outcome":
        return _dict_value(payload, "hierarchical_entry_quality", "machine_decision_case_table", "ai_quality_diagnostics", "diagnostic_price_path_summary")
    return _dict_value(payload, "economic_evaluation")


def _status_texts(owner: str, payload: dict[str, Any]) -> list[str]:
    economic = _economic_section(owner, payload)
    values = [
        economic.get("comparison_status"), economic.get("status"), economic.get("decision"), economic.get("disposition"),
        payload.get("comparison_status"), payload.get("selection_status"), payload.get("decision"), payload.get("status"), payload.get("conclusion"),
    ]
    if owner == "low_price_two_leg":
        for row in (_dict_value(payload, "paired_economic_search").get("profiles") or {}).values():
            if isinstance(row, dict):
                values.extend([row.get("disposition"), row.get("promotion_disposition")])
    return [str(value).strip().lower() for value in values if value not in (None, "")]


def _comparison_status(owner: str, payload: dict[str, Any]) -> str:
    if owner in {"source_quality", "low_price_expansion"}:
        return "not_applicable"
    texts = _status_texts(owner, payload)
    joined = " ".join(texts)
    if any("validated_edge" in value for value in texts):
        return "validated_edge"
    if owner == "low_price_two_leg":
        profiles = _dict_value(payload, "paired_economic_search").get("profiles") or {}
        profile_states = {
            str(row.get("disposition") or row.get("promotion_disposition") or "").lower()
            for row in profiles.values() if isinstance(row, dict)
        }
        profile_states.discard("")
        if len(profile_states) > 1:
            return "mixed"
    if "source_gap" in joined or "contract_block" in joined or "missing_source" in joined:
        return "source_gap"
    if "unsupported" in joined:
        return "unsupported_scope"
    if "no_edge" in joined or "negative_edge" in joined or "hold_no_edge" in joined:
        return "measured_no_edge"
    if "skipped_no_applicable_fill" in joined or "insufficient_sample" in joined:
        return "insufficient_sample"
    if any(token in joined for token in ("pending_maturity", "hold_actual_sample", "paired_search_incomplete")):
        return "pending_maturity"
    if any(token in joined for token in ("identical_policy", "incumbent_preserved")):
        return "identical_policy"
    return "not_applicable"


def _first_blocker(owner: str, payload: dict[str, Any]) -> str | None:
    economic = _economic_section(owner, payload)
    values = [economic.get("blocker"), economic.get("reason"), economic.get("blocked_reason"), payload.get("blocked_reason")]
    for key in ("blockers", "blocking_reasons", "promotion_blocking_reasons"):
        rows = economic.get(key)
        if isinstance(rows, list) and rows:
            values.append(rows[0])
    if owner == "low_price_two_leg":
        for row in (_dict_value(payload, "paired_economic_search").get("profiles") or {}).values():
            if not isinstance(row, dict):
                continue
            blockers = row.get("promotion_blocking_reasons")
            if isinstance(blockers, list) and blockers:
                values.append(blockers[0])
                break
            if row.get("disposition") == "source_gap":
                values.append("profile_source_gap")
                break
    value = _first_nonempty(*values)
    return str(value) if value is not None else None


def _economic_projection(owner: str, payload: dict[str, Any]) -> dict[str, Any]:
    economic = _economic_section(owner, payload)
    status = _comparison_status(owner, payload)
    recommended = _dict_value(payload, "recommended_policy")
    policy_allowed_values = (
        (
            recommended.get("runtime_apply_allowed"),
            recommended.get("ev_validated_runtime_apply_allowed"),
            economic.get("allowed_runtime_apply"),
            payload.get("allowed_runtime_apply"),
        )
        if owner == "rising_missed"
        else (
            recommended.get("runtime_apply_allowed"),
            recommended.get("ev_validated_runtime_apply_allowed"),
            payload.get("allowed_runtime_apply"),
            economic.get("allowed_runtime_apply"),
        )
    )
    policy_allowed = _first_nonempty(*policy_allowed_values)
    candidate_count = _first_nonempty(
        recommended.get("candidate_count"), recommended.get("runtime_candidate_count"),
        len(economic.get("candidates") or []) if isinstance(economic.get("candidates"), list) else None,
    )
    paired_sample_count = _first_nonempty(
        economic.get("paired_sample_count"), economic.get("paired_economic_sample_count"),
        economic.get("paired_comparison_count"), economic.get("comparison_sample_count"),
        economic.get("completed_candidate_count"), economic.get("applicable_receipt_count"),
        economic.get("eligible_sample_count"), economic.get("sample_count"),
    )
    source_day_count = _first_nonempty(
        economic.get("source_date_count"), economic.get("economic_source_date_count"),
        len(economic.get("source_counts") or {}) if isinstance(economic.get("source_counts"), dict) else None,
    )
    first_blocker = _first_blocker(owner, payload)
    if status == "measured_no_edge" and not paired_sample_count:
        status = "source_gap"
        first_blocker = first_blocker or "paired_comparison_denominator_missing"
    future_contract_verified = _first_nonempty(
        economic.get("future_generation_contract_verified"),
        economic.get("future_source_contract_verified"),
        economic.get("producer_consumer_contract_verified"),
    ) is True
    if status == "pending_maturity" and not future_contract_verified:
        status = "source_gap"
        first_blocker = first_blocker or "future_generation_contract_unverified"
    if status == "validated_edge" and (policy_allowed is not True or not candidate_count):
        status = "source_gap"
        first_blocker = first_blocker or "validated_candidate_contract_incomplete"
    if status == "validated_edge":
        resolution_mode = "validated_economic_action"
    elif status == "measured_no_edge":
        resolution_mode = "measured_no_edge"
    elif status in {"pending_maturity", "insufficient_sample"}:
        resolution_mode = "natural_maturity"
    elif status in {"source_gap", "unsupported_scope", "mixed"}:
        resolution_mode = (
            "historical_unrecoverable"
            if any("irrecoverable" in value for value in _status_texts(owner, payload))
            else "producer_repair"
        )
    else:
        resolution_mode = "retired_or_not_applicable"
    if status == "validated_edge":
        handoff = "candidate_published"
    elif status in {"measured_no_edge", "identical_policy", "pending_maturity", "insufficient_sample"}:
        handoff = "incumbent_preserved"
    elif status in {"source_gap", "unsupported_scope", "mixed"}:
        handoff = "blocked"
    else:
        handoff = "not_applicable"
    return {
        "comparison_status": status,
        "raw_statuses": _status_texts(owner, payload),
        "metric_role": _first_nonempty(economic.get("metric_role"), payload.get("metric_role")),
        "incumbent_cost_adjusted_ev_pct": _first_nonempty(economic.get("incumbent_ev_pct"), economic.get("primary_operating_ev_pct")),
        "candidate_cost_adjusted_ev_pct": economic.get("candidate_ev_pct"),
        "paired_delta_ev_pct": _first_nonempty(economic.get("delta_ev_pct"), economic.get("ev_uplift_pct_point")),
        "conservative_delta_ev_lower_bound_pct": _first_nonempty(economic.get("delta_ev_lower_bound_pct"), economic.get("robust_paired_delta_ev_lower_bound_pct")),
        "actual_net_profit_improvement": _first_nonempty(economic.get("actual_net_profit_improvement"), economic.get("net_profit_uplift_krw_per_observation_day")),
        "paired_tail_delta_pct": _first_nonempty(
            economic.get("paired_tail_delta_pct"), economic.get("tail_delta_pct"),
            economic.get("downside_tail_delta_pct"),
        ),
        "capital_exposure_delta": _first_nonempty(
            economic.get("capital_exposure_delta"), economic.get("reserve_delta_krw"),
            economic.get("capital_occupation_delta_krw"),
        ),
        "fill_participation_delta_pct": _first_nonempty(
            economic.get("fill_participation_delta_pct"), economic.get("fill_rate_delta_pct"),
        ),
        "model_holdout_status": _first_nonempty(
            economic.get("model_holdout_status"), economic.get("chronological_model_holdout_status"),
        ),
        "candidate_holdout_status": _first_nonempty(
            economic.get("candidate_holdout_status"), economic.get("selection_holdout_status"),
        ),
        "paired_sample_count": paired_sample_count,
        "source_day_count": source_day_count,
        "candidate_count": candidate_count or 0,
        "policy_apply_allowed": policy_allowed is True and status == "validated_edge",
        "policy_handoff_state": handoff,
        "resolution_mode": resolution_mode,
        "first_blocker": first_blocker,
        "closure_owner": DEFAULT_CLOSURE_OWNER.get(owner),
        "closure_test": economic.get("closure_test"),
        "model_delta_ev_is_actual_profit": False,
    }


def _runtime_consumption_state(
    target_date: str, sources: dict[str, dict[str, Any]]
) -> tuple[str, str, dict[str, Any]]:
    effective_dates = sorted(
        {
            str(row.get("effective_date"))
            for row in sources.values()
            if row.get("exists") and row.get("target_date_matches")
            and not row.get("error") and row.get("effective_date")
        }
    )
    apply_date = effective_dates[-1] if effective_dates else target_date
    runtime_dir = DATA_DIR / "runtime" / "policy_bootstrap"
    manifest_path = runtime_dir / f"runtime_policy_bootstrap_{apply_date}.json"
    verification_path = runtime_dir / f"runtime_policy_bootstrap_verify_{apply_date}.json"
    manifest = _load_json(manifest_path)
    verification = _load_json(verification_path)
    runtime_pid = verification.get("pid")
    receipt_runtime_pid = (
        runtime_pid
        if isinstance(runtime_pid, int)
        and not isinstance(runtime_pid, bool)
        and runtime_pid > 0
        else None
    )
    actual_pid_consumed = bool(
        receipt_runtime_pid is not None
        and verification.get("status") == "pass"
        and verification.get("passed") is True
        and verification.get("pid_passed") is True
        and verification.get("pid_env_available") is True
    )
    receipt = {
        "source_date": target_date,
        "effective_dates": effective_dates,
        "apply_date": apply_date if effective_dates else None,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha(manifest_path),
        "verification_path": str(verification_path),
        "verification_sha256": _sha(verification_path),
        "runtime_pid": receipt_runtime_pid,
        "pid_passed": verification.get("pid_passed"),
        "pid_env_available": verification.get("pid_env_available"),
        "actual_pid_consumed": actual_pid_consumed,
    }
    if not effective_dates:
        return "not_due", "not_applicable", receipt
    if (
        manifest.get("target_date") == apply_date
        and verification.get("status") == "pass"
        and verification.get("passed") is True
        and verification.get("target_date") == apply_date
    ):
        return "verified", ("pending" if actual_pid_consumed else "not_due"), receipt
    if verification_path.exists():
        return "rejected", "not_due", receipt
    if manifest_path.exists():
        return "pending", "not_due", receipt
    return "pending", "not_due", receipt


def build_runtime_approval_summary(
    target_date: str, *, include_swing: bool = True, include_producer_gap: bool = True
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    paths = _paths(target_date)
    required_by_owner, owner_contract = _owner_requirements(target_date)
    sources: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []

    for owner, path in paths.items():
        payload, error, read_mode, size_bytes = _read(path)
        artifact_sha256 = _sha(path)
        companion: dict[str, Any] | None = None
        if read_mode == "stream_hash_only_large_json":
            payload, companion, semantic_error = _large_companion(owner, path, target_date, artifact_sha256, paths)
            if semantic_error:
                error = semantic_error
            else:
                read_mode = "bounded_terminal_companion"
        exact_name_date = path.stem.endswith(target_date)
        target_date_matches = _date_matches(payload, target_date) if payload else exact_name_date
        required = required_by_owner.get(owner, False)
        applicability = "active_required" if required else ("not_applicable_disabled_by_wrapper" if owner in PRIMARY_DIRECT_OWNERS else "optional_handoff")
        row = {
            "owner": owner, "path": str(path), "exists": path.exists(), "size_bytes": size_bytes,
            "sha256": artifact_sha256, "report_type": payload.get("report_type") or payload.get("schema"),
            "status": payload.get("status") or payload.get("decision") or payload.get("conclusion") or ("artifact_complete" if payload else None),
            "target_date_matches": target_date_matches, "runtime_effect": payload.get("runtime_effect"),
            "source_date": payload.get("source_date"), "publication_date": payload.get("publication_date"),
            "effective_date": payload.get("effective_date"),
            "allowed_runtime_apply": payload.get("allowed_runtime_apply"), "actual_order_submitted": payload.get("actual_order_submitted"),
            "error": error, "read_mode": read_mode, "required": required, "applicability": applicability,
            "producer_flag": PRODUCER_FLAG_BY_OWNER.get(owner), "semantic_companion": companion,
            "artifact_semantic_sha256": payload.get("artifact_sha256"),
            "policy_sha256": payload.get("policy_sha256"),
            "source_report_sha256": payload.get("source_report_sha256"),
            "consumer_schema": payload.get("consumer_schema"),
        }
        if owner in PRIMARY_DIRECT_OWNERS:
            projection = _economic_projection(owner, payload)
            row["economic_evidence"] = projection
            row["policy_owner"] = POLICY_OWNER_BY_SOURCE.get(owner)
        sources[owner] = row
        if required and error:
            blockers.append(f"{owner}:{error}")
        elif required and not target_date_matches:
            blockers.append(f"{owner}:target_date_mismatch")
        elif required and not artifact_sha256:
            blockers.append(f"{owner}:artifact_hash_missing")

    # A validated family result is actionable only when its direct dated policy
    # receipt is also present and hash-bound.  Diagnostic and incumbent outcomes
    # remain valid without inventing a policy handoff.
    for owner in PRIMARY_DIRECT_OWNERS:
        row = sources[owner]
        policy_owner = row.get("policy_owner")
        if not policy_owner:
            continue
        policy = sources.get(str(policy_owner)) or {}
        policy_receipt_valid = bool(
            policy.get("exists") and policy.get("target_date_matches")
            and policy.get("sha256") and not policy.get("error")
        )
        if owner == "rising_missed" and policy_receipt_valid:
            policy_payload = _load_json(Path(str(policy.get("path") or "")))
            source_payload = _load_json(Path(str(row.get("path") or "")))
            policy_receipt_valid = bool(
                policy.get("source_report_sha256")
                == row.get("artifact_semantic_sha256")
                and policy.get("consumer_schema")
                == "rising_missed_tp1_selector_bounded_env_v1"
                and policy.get("policy_sha256")
                == direct_policy_digest(policy_payload)
                and validate_rising_missed_policy_receipt(
                    policy_payload,
                    source_payload,
                    str(policy_payload.get("effective_date") or ""),
                )
                is None
            )
        row["policy_receipt"] = {
            "owner": policy_owner,
            "path": policy.get("path"),
            "sha256": policy.get("sha256"),
            "target_date_matches": policy.get("target_date_matches"),
            "valid": policy_receipt_valid,
        }
        evidence = row["economic_evidence"]
        if policy.get("exists") and not policy_receipt_valid:
            evidence["policy_handoff_state"] = "blocked"
            evidence["first_blocker"] = (
                evidence["first_blocker"] or "dated_policy_receipt_invalid"
            )
        if evidence["comparison_status"] == "validated_edge" and not policy_receipt_valid:
            evidence.update({
                "comparison_status": "source_gap",
                "policy_handoff_state": "blocked",
                "resolution_mode": "producer_repair",
                "first_blocker": "validated_candidate_policy_receipt_missing",
                "policy_apply_allowed": False,
            })

    active_states = {
        owner: sources[owner]["economic_evidence"]["comparison_status"]
        for owner in PRIMARY_DIRECT_OWNERS if required_by_owner.get(owner)
    }
    comparable_states = {state for state in active_states.values() if state != "not_applicable"}
    economic_counts: Counter[str] = Counter(active_states.values())
    overall_economic_state = "not_applicable" if not comparable_states else next(iter(comparable_states)) if len(comparable_states) == 1 else "mixed"
    preopen_state, natural_state, preopen_receipt = _runtime_consumption_state(target_date, sources)
    direct_state = "complete" if not blockers else "incomplete"
    status = DIRECT_EVIDENCE_COMPLETE if direct_state == "complete" else DIRECT_EVIDENCE_INCOMPLETE
    handoff_states = Counter(
        sources[owner]["economic_evidence"]["policy_handoff_state"]
        for owner in PRIMARY_DIRECT_OWNERS if required_by_owner.get(owner)
    )
    report = {
        "schema_version": 3, "report_type": "runtime_approval_summary", "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "status": status,
        "direct_evidence_state": direct_state, "economic_state": overall_economic_state,
        "economic_state_counts": dict(sorted(economic_counts.items())),
        "validated_edge_count": economic_counts.get("validated_edge", 0),
        "policy_candidate_count": sum(1 for owner in PRIMARY_DIRECT_OWNERS if sources[owner]["economic_evidence"]["policy_handoff_state"] == "candidate_published"),
        "preopen_consumption_state": preopen_state, "natural_acceptance_state": natural_state,
        "preopen_consumption_receipt": preopen_receipt,
        "policy_handoff_state": (
            "candidate_published" if handoff_states.get("candidate_published")
            else "blocked" if handoff_states.get("blocked")
            else "incumbent_preserved" if handoff_states.get("incumbent_preserved")
            else "not_applicable"
        ),
        "policy_handoff_state_counts": dict(sorted(handoff_states.items())),
        "decision_authority": "family_owned_direct_evidence_summary_only", "common_tuning_candidate_created": False,
        "daily_threshold_cycle_retired": True, "threshold_cycle_ev_retired": True, "owner_contract": owner_contract,
        "sources": sources, "required_source_count": sum(required_by_owner.values()),
        "available_required_source_count": sum(
            1 for owner, required in required_by_owner.items()
            if required and sources[owner]["exists"] and sources[owner]["target_date_matches"] and sources[owner]["sha256"] and not sources[owner]["error"]
        ),
        "blocking_reasons": blockers,
        "economic_blockers": [
            {
                "owner": owner, "comparison_status": sources[owner]["economic_evidence"]["comparison_status"],
                "first_blocker": sources[owner]["economic_evidence"]["first_blocker"],
                "closure_owner": sources[owner]["economic_evidence"]["closure_owner"],
                "closure_test": sources[owner]["economic_evidence"]["closure_test"],
            }
            for owner in PRIMARY_DIRECT_OWNERS
            if required_by_owner.get(owner) and sources[owner]["economic_evidence"]["comparison_status"] in {"source_gap", "unsupported_scope", "mixed"}
        ],
        "runtime_effect": False, "allowed_runtime_apply": False, "actual_order_submitted": False,
        "include_swing": include_swing, "include_producer_gap": include_producer_gap,
    }
    json_path, md_path = summary_paths(target_date)
    _atomic_write(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        f"# Runtime approval summary - {target_date}", "", f"- status: `{report['status']}`",
        f"- direct evidence: `{report['direct_evidence_state']}`", f"- economic state: `{report['economic_state']}`",
        f"- PREOPEN consumption: `{report['preopen_consumption_state']}`", "- authority: family-owned direct evidence summary only",
        "- common Daily/EV candidate generation: `retired`",
        f"- required sources: `{report['available_required_source_count']}/{report['required_source_count']}`", "", "## Direct owners", "",
        "| Owner | Required | Evidence | Economic | Policy handoff | First blocker |", "|---|---:|---|---|---|---|",
    ]
    for name, row in sources.items():
        economic = row.get("economic_evidence") or {}
        lines.append(
            f"| `{name}` | `{row['required']}` | `{row.get('status') or row.get('error') or '-'}` | "
            f"`{economic.get('comparison_status') or '-'}` | `{economic.get('policy_handoff_state') or '-'}` | "
            f"`{economic.get('first_blocker') or '-'}` |"
        )
    if blockers:
        lines.extend(["", "## Blocking reasons", *[f"- `{value}`" for value in blockers]])
    _atomic_write(md_path, "\n".join(lines) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--exclude-swing", action="store_true")
    parser.add_argument("--producer-gap-disabled", action="store_true")
    args = parser.parse_args(argv)
    report = build_runtime_approval_summary(
        args.target_date,
        include_swing=not args.exclude_swing,
        include_producer_gap=not args.producer_gap_disabled,
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
