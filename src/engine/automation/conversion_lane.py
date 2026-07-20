"""Build conversion lane and blocker rank for sim-to-real compression."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.automation.key_lineage_ledger import (
    build_key_lineage_ledger,
    report_paths as key_lineage_paths,
)
from src.utils.constants import DATA_DIR

REPORT_TYPE = "conversion_lane"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
BLOCKER_CLASSES = {
    "source_quality",
    "sample_floor",
    "submit_drought",
    "runtime_hook",
    "env_mapping",
    "post_apply_attribution",
    "AI_review",
    "bridge_contract",
    "safety_or_broker_guard",
    "user_authority",
    "key_lineage",
}
SUBMIT_DROUGHT_CLOSURE_AXES = (
    "LATENCY_PRE_SUBMIT",
    "BROKER_RECEIPT",
    "BUDGET_PASS_COLLAPSE",
    "SIM_REAL_AUTHORITY",
    "SOURCE_TAXONOMY_LEAKAGE",
    "UPSTREAM_GATE",
)
SUBMIT_DROUGHT_QUOTE_FRESHNESS_SUBACTIONS = (
    "close_ws_snapshot_refresh_stale_source",
    "close_ws_snapshot_refresh_missing_source",
    "close_ws_snapshot_refresh_invalid_source",
    "close_observer_quote_stale_source",
    "close_observer_quote_missing",
    "close_observer_quote_invalid",
    "close_observer_quote_spread_guard",
    "close_refresh_alias_disabled",
    "close_unknown_latency_reason",
)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _hash(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _blocker_class(reason: str, row: dict[str, Any] | None = None) -> str:
    row = row or {}
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    text = " ".join(
        str(value or "")
        for value in (
            reason,
            row.get("next_blocker"),
            row.get("source_quality_state"),
            row.get("sim_policy_state"),
            row.get("runtime_observation_state"),
            row.get("bridge_state"),
            row.get("conversion_state"),
            evidence.get("failure_reason"),
            evidence.get("final_disposition"),
            evidence.get("derived_review_category"),
            evidence.get("recommended_resolution"),
            evidence.get("flow_sim_transition_blocker"),
        )
    ).lower()
    if "key" in text or "catalog" in text or "lineage" in text:
        return "key_lineage"
    if (
        "submit_drought" in text
        or "latency_pre_submit" in text
        or "budget_pass" in text
    ):
        return "submit_drought"
    if "bridge" in text:
        return "bridge_contract"
    if "runtime_hook" in text or "instrumented" in text:
        return "runtime_hook"
    if "env" in text or "preopen" in text:
        return "env_mapping"
    if "post_apply" in text or "attribution" in text:
        return "post_apply_attribution"
    if "ai" in text or "tier2" in text:
        return "AI_review"
    if (
        "safety" in text
        or "broker" in text
        or "stale" in text
        or "quantity" in text
        or "cooldown" in text
    ):
        return "safety_or_broker_guard"
    if "authority" in text or "approval" in text or "user" in text:
        return "user_authority"
    if (
        "source_quality" in text
        or "source_dimension" in text
        or "source gap" in text
        or ("contract" in text and "bridge" not in text)
    ):
        return "source_quality"
    if "sample" in text or "natural_match" in text or "collecting" in text:
        return "sample_floor"
    return "sample_floor"


def _candidate_from_lifecycle(
    item: dict[str, Any], strategy_scope: str
) -> dict[str, Any]:
    candidate_id = str(item.get("bucket_id") or _hash("candidate", item))
    source_key_id = str(item.get("source_bucket_id") or candidate_id)
    state = str(item.get("classification_state") or "source_only_keep_collecting")
    source_gap = str(item.get("source_dimension_gap") or "")
    bridge_state = "ready" if state == "live_auto_apply_ready" else "not_ready"
    source_quality_state = "blocked" if source_gap else "pass"
    sample = _safe_int(item.get("sample"))
    required_sample = _safe_int(
        item.get("parent_sample_floor") or item.get("sample_floor"), 0
    )
    ev = _safe_float(
        item.get("source_quality_adjusted_ev_pct")
        or item.get("equal_weight_avg_profit_pct")
    )
    if state == "lifecycle_flow_sim_probe_candidate":
        conversion_state, blocker = "sim_applied", "sample_floor"
    elif state in {"sim_auto_approved", "entry_only_sim_auto_approved"}:
        conversion_state, blocker = "sim_applied", "complete_parent_flow"
    elif source_gap:
        conversion_state, blocker = "discovered", "source_quality"
    elif ev is not None and ev > 0 and sample > 0:
        conversion_state, blocker = "complete_parent_flow", "bridge_contract"
    else:
        conversion_state, blocker = "discovered", "sample_floor"
    return {
        "candidate_id": candidate_id,
        "strategy_scope": strategy_scope,
        "source_key_type": "bucket",
        "source_key_id": source_key_id,
        "parent_bucket_id": item.get("parent_bucket_id")
        or f"{item.get('stage')}:{item.get('bucket_type')}",
        "primary_ev": ev,
        "sample": sample,
        "required_sample": required_sample or None,
        "sample_floor_window_policy": str(
            item.get("sample_floor_window_policy") or item.get("window_policy") or ""
        ),
        "sample_floor_status": (
            "unknown_floor"
            if not required_sample
            else ("pass" if sample >= required_sample else "below_floor")
        ),
        "source_quality_state": source_quality_state,
        "sim_policy_state": state,
        "runtime_observation_state": "not_checked",
        "runtime_observation_scope": "new_postclose_candidate_not_due_until_next_preopen",
        "bridge_state": bridge_state,
        "conversion_state": conversion_state,
        "next_blocker": blocker,
        "flow_sim_transition_state": item.get("flow_sim_transition_state"),
        "evidence": {
            "classification_state": state,
            "recommended_resolution": item.get("recommended_resolution"),
            "flow_sim_transition_blocker": item.get("flow_sim_transition_blocker"),
        },
    }


def _candidate_from_matched_bucket_lineage(
    row: dict[str, Any],
) -> dict[str, Any] | None:
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    source_key_id = str(row.get("source_key_id") or "").strip()
    if not source_key_id or row.get("source_key_type") != "bucket":
        return None
    if row.get("same_key_continuity") != "pass":
        return None
    ev = _safe_float(evidence.get("primary_ev"))
    sample = _safe_int(evidence.get("sample"))
    required_sample = _safe_int(
        evidence.get("parent_sample_floor") or evidence.get("sample_floor"), 0
    )
    return {
        "candidate_id": source_key_id,
        "strategy_scope": "scalp",
        "source_key_type": "bucket",
        "source_key_id": source_key_id,
        "parent_bucket_id": evidence.get("bucket_id")
        or source_key_id.rsplit(":", 1)[0],
        "primary_ev": ev,
        "sample": sample,
        "required_sample": required_sample or None,
        "sample_floor_window_policy": str(
            evidence.get("sample_floor_window_policy") or ""
        ),
        "sample_floor_status": (
            "unknown_floor"
            if not required_sample
            else ("pass" if sample >= required_sample else "below_floor")
        ),
        "source_quality_state": "pass",
        "sim_policy_state": str(
            evidence.get("classification_state") or "runtime_applied_bucket_policy"
        ),
        "runtime_observation_state": "matched",
        "runtime_observation_scope": "previous_preopen_policy_runtime_observed",
        "bridge_state": "not_ready",
        "conversion_state": "runtime_observed",
        "next_blocker": "sample_floor",
        "evidence": {
            "source_artifact": row.get("source_artifact"),
            "bucket_id": evidence.get("bucket_id"),
            "source_bucket_kind": evidence.get("source_bucket_kind"),
        },
    }


def _annotate_conversion_candidate(candidate: dict[str, Any]) -> None:
    ev = _safe_float(candidate.get("primary_ev"))
    runtime_observed = (
        str(candidate.get("runtime_observation_state") or "")
        in {
            "matched",
            "runtime_observed",
            "joined",
        }
        or candidate.get("conversion_state") == "runtime_observed"
    )
    sample_floor_related = str(candidate.get("next_blocker") or "") == "sample_floor"
    sample = _safe_int(candidate.get("sample"), 0)
    required_sample = _safe_int(candidate.get("required_sample"), 0)
    sample_floor_unknown = sample_floor_related and required_sample <= 0
    sample_floor_blocked = (
        sample_floor_related and required_sample > 0 and sample < required_sample
    )
    candidate["positive_ev_candidate"] = bool(ev is not None and ev > 0)
    candidate["sample_floor_blocked"] = sample_floor_blocked
    candidate["sample_floor_unknown_floor"] = sample_floor_unknown
    candidate["runtime_observed_same_key"] = bool(runtime_observed)
    if candidate.get("runtime_observed_same_key"):
        candidate.setdefault(
            "runtime_observation_scope", "previous_preopen_policy_runtime_observed"
        )
    else:
        candidate.setdefault("runtime_observation_scope", "not_observed_or_not_due")


def _merge_lineage_candidate(
    candidate: dict[str, Any], lineage: dict[str, Any]
) -> None:
    evidence = (
        lineage.get("evidence") if isinstance(lineage.get("evidence"), dict) else {}
    )
    if lineage.get("same_key_continuity") == "pass":
        candidate["runtime_observation_state"] = "matched"
        candidate["runtime_observation_scope"] = (
            "previous_preopen_policy_runtime_observed"
        )
        candidate["runtime_observed_same_key"] = True
        candidate["conversion_state"] = "runtime_observed"
        candidate["runtime_match_key"] = lineage.get("runtime_match_key")
        candidate["postclose_observed_key"] = lineage.get("postclose_observed_key")
        candidate["next_blocker"] = "sample_floor"
    elif lineage.get("conversion_state") == "natural_match_0":
        candidate["runtime_observation_scope"] = (
            "previous_preopen_policy_natural_match_0"
        )
    elif candidate.get("runtime_observation_scope") == "not_observed_or_not_due":
        candidate["runtime_observation_scope"] = (
            "new_postclose_candidate_not_due_until_next_preopen"
        )
    if candidate.get("primary_ev") is None:
        candidate["primary_ev"] = _safe_float(
            evidence.get("primary_ev") or evidence.get("source_quality_adjusted_ev_pct")
        )
    if not candidate.get("required_sample"):
        floor = _safe_int(
            evidence.get("parent_sample_floor") or evidence.get("sample_floor"), 0
        )
        if floor:
            candidate["required_sample"] = floor
            candidate["sample_floor_status"] = (
                "pass" if _safe_int(candidate.get("sample")) >= floor else "below_floor"
            )


def _source_sample_floor_window_policy(discovery: dict[str, Any]) -> str:
    summary = (
        discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    )
    return str(
        summary.get("source_window_policy")
        or discovery.get("window_policy")
        or "source_report_window"
    )


def _candidates_from_lifecycle(
    discovery: dict[str, Any], strategy_scope: str
) -> list[dict[str, Any]]:
    source_window_policy = _source_sample_floor_window_policy(discovery)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in (
        "live_auto_apply_candidates",
        "sim_auto_approved_candidates",
        "surfaced_candidates",
    ):
        for item in discovery.get(section) or []:
            if not isinstance(item, dict):
                continue
            row = _candidate_from_lifecycle(item, strategy_scope)
            if not row.get("sample_floor_window_policy"):
                row["sample_floor_window_policy"] = source_window_policy
            if row["candidate_id"] in seen:
                continue
            seen.add(row["candidate_id"])
            candidates.append(row)
    return candidates


def _candidate_from_runtime_gap(row: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(row.get("candidate_id") or _hash("runtime_gap", row))
    derived = str(
        row.get("derived_review_category") or row.get("final_disposition") or ""
    )
    blocker = _blocker_class(
        str(row.get("failure_reason") or row.get("recommended_resolution") or derived),
        row,
    )
    return {
        "candidate_id": candidate_id,
        "strategy_scope": str(row.get("domain") or "scalp"),
        "source_key_type": "bucket",
        "source_key_id": candidate_id,
        "parent_bucket_id": row.get("parent_bucket_id"),
        "primary_ev": _safe_float(row.get("primary_ev")),
        "sample": _safe_int(row.get("sample")),
        "source_quality_state": "blocked" if blocker == "source_quality" else "pass",
        "sim_policy_state": str(row.get("producer_state") or ""),
        "runtime_observation_state": str(
            row.get("preopen_apply_state") or "not_checked"
        ),
        "bridge_state": str(row.get("bridge_state") or "not_checked"),
        "conversion_state": (
            "bridge_contract_ready"
            if row.get("bridge_state") == "joined"
            else "discovered"
        ),
        "next_blocker": blocker,
        "evidence": {
            "final_disposition": row.get("final_disposition"),
            "failure_reason": row.get("failure_reason"),
            "derived_review_category": derived,
        },
    }


def _conversion_blocker(
    *,
    candidate_id: str,
    blocker_class: str,
    reason: str,
    candidate: dict[str, Any] | None = None,
    rank_seed: int = 100,
) -> dict[str, Any]:
    blocker = blocker_class if blocker_class in BLOCKER_CLASSES else "sample_floor"
    candidate = candidate or {}
    remaining_gap_count = 1
    if blocker in {
        "source_quality",
        "bridge_contract",
        "key_lineage",
        "submit_drought",
    }:
        remaining_gap_count = 2
    ev = _safe_float(candidate.get("primary_ev"), 0.0) or 0.0
    sample = _safe_int(candidate.get("sample"))
    fix_difficulty = {
        "key_lineage": 1,
        "env_mapping": 1,
        "runtime_hook": 2,
        "bridge_contract": 2,
        "submit_drought": 2,
        "source_quality": 3,
        "sample_floor": 4,
        "AI_review": 2,
        "post_apply_attribution": 2,
        "safety_or_broker_guard": 5,
        "user_authority": 5,
    }.get(blocker, 3)
    impact = max(
        1,
        rank_seed
        - int(ev * 10)
        - min(sample, 20)
        + fix_difficulty * 5
        + remaining_gap_count * 3,
    )
    blocker_axis = _blocker_axis(
        candidate_id=candidate_id, blocker_class=blocker, reason=reason
    )
    return {
        "blocker_id": _hash("conversion_blocker", [candidate_id, blocker, reason]),
        "conversion_candidate_id": candidate_id,
        "blocker_class": blocker,
        "blocker_axis": blocker_axis,
        "blocker_resolution_status": "open",
        "blocker_runtime_effect": False,
        "blocker_allowed_runtime_apply": False,
        "conversion_impact_rank": impact,
        "ev_potential_rank": 1 if ev > 0 else 5,
        "sample_readiness_rank": 1 if sample >= 10 else 2 if sample >= 3 else 4,
        "fix_difficulty_rank": fix_difficulty,
        "remaining_gap_count": remaining_gap_count,
        "next_repair_action": reason or f"close_{blocker}",
        "acceptance_test": _acceptance_test(blocker),
    }


def _blocker_axis(*, candidate_id: str, blocker_class: str, reason: str) -> str:
    text = f"{candidate_id} {reason}".upper()
    if blocker_class == "submit_drought":
        for axis in SUBMIT_DROUGHT_CLOSURE_AXES:
            if axis in text:
                return axis
        return "SUBMIT_DROUGHT_UNCLASSIFIED"
    if blocker_class in {"env_mapping", "source_quality"}:
        parts = str(candidate_id or "").split(":")
        if len(parts) >= 2:
            return ":".join(parts[:2])
    return blocker_class


def _acceptance_test(blocker_class: str) -> str:
    mapping = {
        "source_quality": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass",
        "sample_floor": "candidate reaches configured parent sample floor or remains sim_priority_only",
        "submit_drought": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE",
        "runtime_hook": "runtime event emits the candidate key and postclose can observe it",
        "env_mapping": "next PREOPEN policy/env contains the same candidate key",
        "post_apply_attribution": "post-apply attribution joins runtime-applied candidate result",
        "AI_review": "parsed Tier2 review closes explicit contract objections",
        "bridge_contract": "runtime_apply_bridge emits explicit bridge blocker ledger or live_auto_apply_ready",
        "safety_or_broker_guard": "hard safety/broker guard remains closed and candidate is not promoted",
        "user_authority": "user-approved full-live/cap/provider/bot authority artifact exists",
        "key_lineage": "same source key is continuous producer->catalog->PREOPEN->runtime->postclose or closes natural_match_0",
    }
    return mapping.get(blocker_class, "blocker closes with machine-readable evidence")


def _submit_drought_blockers(buy_funnel: dict[str, Any]) -> list[dict[str, Any]]:
    classification = (
        buy_funnel.get("classification")
        if isinstance(buy_funnel.get("classification"), dict)
        else {}
    )
    matches = (
        classification.get("matches")
        if isinstance(classification.get("matches"), list)
        else []
    )
    critical = (
        classification.get("primary") == "SUBMIT_DROUGHT_CRITICAL"
        or "SUBMIT_DROUGHT_CRITICAL" in matches
    )
    if not critical:
        return []
    return [
        _conversion_blocker(
            candidate_id=f"submit_drought:{item}",
            blocker_class="submit_drought",
            reason=f"close_submit_drought_{item.lower()}",
            rank_seed=30,
        )
        for item in SUBMIT_DROUGHT_CLOSURE_AXES
    ]


def _submit_drought_quote_freshness_subactions(
    subreason_counts: dict[str, Any],
) -> dict[str, int]:
    out: Counter[str] = Counter()
    for reason, raw_count in (subreason_counts or {}).items():
        text = str(reason or "").lower()
        count = _safe_int(raw_count)
        if count <= 0:
            continue
        if "ws_snapshot" in text and "stale" in text:
            out["close_ws_snapshot_refresh_stale_source"] += count
        elif "ws_snapshot" in text and "missing" in text:
            out["close_ws_snapshot_refresh_missing_source"] += count
        elif "ws_snapshot" in text and "invalid" in text:
            out["close_ws_snapshot_refresh_invalid_source"] += count
        elif "observer_quote" in text and "stale" in text:
            out["close_observer_quote_stale_source"] += count
        elif "observer_quote" in text and "missing" in text:
            out["close_observer_quote_missing"] += count
        elif "observer_quote" in text and "invalid" in text:
            out["close_observer_quote_invalid"] += count
        elif "observer_quote" in text and "spread" in text:
            out["close_observer_quote_spread_guard"] += count
        elif "disabled" in text or "alias" in text:
            out["close_refresh_alias_disabled"] += count
    return {
        key: out.get(key, 0)
        for key in SUBMIT_DROUGHT_QUOTE_FRESHNESS_SUBACTIONS
        if out.get(key, 0)
    }


def _buy_funnel_provenance(buy_funnel: dict[str, Any]) -> dict[str, Any]:
    classification = (
        buy_funnel.get("classification")
        if isinstance(buy_funnel.get("classification"), dict)
        else {}
    )
    matches = (
        classification.get("matches")
        if isinstance(classification.get("matches"), list)
        else []
    )
    root_cause = (
        classification.get("submit_drought_root_cause")
        if isinstance(classification.get("submit_drought_root_cause"), dict)
        else {}
    )
    quote_freshness = (
        root_cause.get("quote_freshness_attribution")
        if isinstance(root_cause.get("quote_freshness_attribution"), dict)
        else {}
    )
    subreason_counts = quote_freshness.get("refresh_subreason_counts") or {}
    subactions = _submit_drought_quote_freshness_subactions(subreason_counts)
    if root_cause.get("unknown_latency_reason_count"):
        subactions["close_unknown_latency_reason"] = _safe_int(
            root_cause.get("unknown_latency_reason_count")
        )
    return {
        "buy_funnel_source_present": bool(buy_funnel),
        "buy_funnel_report_type": buy_funnel.get("report_type"),
        "buy_funnel_classification_primary": classification.get("primary"),
        "buy_funnel_classification_matches": matches,
        "submit_drought_handoff_state": classification.get(
            "submit_drought_handoff_state"
        ),
        "submit_drought_root_cause_counts": root_cause.get("latency_root_cause_counts")
        or {},
        "submit_drought_quote_freshness_attribution": quote_freshness,
        "submit_drought_quote_freshness_subreason_counts": subreason_counts,
        "submit_drought_quote_freshness_subaction_counts": subactions,
        "submit_drought_refresh_attempted_count": _safe_int(
            quote_freshness.get("refresh_attempted_count")
        ),
        "submit_drought_refresh_applied_count": _safe_int(
            quote_freshness.get("refresh_applied_count")
        ),
        "submit_drought_latency_pass_recovered_count": _safe_int(
            quote_freshness.get("latency_pass_recovered_count")
        ),
        "submit_drought_order_bundle_submitted_after_refresh_count": _safe_int(
            quote_freshness.get("order_bundle_submitted_after_refresh_count")
        ),
        "submit_drought_unknown_latency_reason_count": _safe_int(
            root_cause.get("unknown_latency_reason_count")
        ),
        "submit_drought_unknown_latency_workorder_required": bool(
            root_cause.get("unknown_latency_workorder_required")
        ),
        "submit_drought_blocker_source_state": (
            "submit_drought_critical"
            if classification.get("primary") == "SUBMIT_DROUGHT_CRITICAL"
            or "SUBMIT_DROUGHT_CRITICAL" in matches
            else (
                "not_submit_drought_critical"
                if classification
                else "buy_funnel_missing_or_unclassified"
            )
        ),
    }


def _lineage_by_source_key(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in ledger.get("lineage_rows") or []:
        if not isinstance(row, dict):
            continue
        source_key_id = str(row.get("source_key_id") or "").strip()
        if source_key_id:
            out[source_key_id] = row
    return out


def _lineage_handoff_rows(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = (
        ledger.get("lineage_rows")
        if isinstance(ledger.get("lineage_rows"), list)
        else []
    )
    return [
        {
            "source_key_id": row.get("source_key_id"),
            "source_key_type": row.get("source_key_type"),
            "catalog_key_present": row.get("catalog_key_present"),
            "preopen_policy_selected": row.get("preopen_policy_selected"),
            "runtime_match_key": row.get("runtime_match_key"),
            "postclose_observed_key": row.get("postclose_observed_key"),
            "same_key_continuity": row.get("same_key_continuity"),
            "conversion_state": row.get("conversion_state"),
            "next_blocker": row.get("next_blocker"),
            "positive_ev_candidate": row.get("positive_ev_candidate"),
            "sample_floor_blocked": row.get("sample_floor_blocked"),
            "runtime_observed_same_key": row.get("runtime_observed_same_key"),
        }
        for row in rows
    ]


def _swing_proxy_candidates(target_date: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for directory in (
        DATA_DIR / "report" / "swing_bottom_rebound_candidate_source",
        DATA_DIR / "report" / "swing_bottom_rebound_policy_auto_loop",
    ):
        path = directory / f"{directory.name}_{target_date}.json"
        payload = _load_json(path)
        if not payload:
            continue
        summary = (
            payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        )
        count = _safe_int(
            summary.get("candidate_count")
            or summary.get("approved_count")
            or summary.get("positive_source_count")
        )
        if count <= 0:
            continue
        candidates.append(
            {
                "candidate_id": f"swing_bottom_rebound:{directory.name}",
                "strategy_scope": "swing",
                "source_key_type": "hypothesis",
                "source_key_id": "bottom_rebound",
                "parent_bucket_id": "bottom_rebound",
                "primary_ev": _safe_float(
                    summary.get("source_quality_adjusted_ev_pct")
                ),
                "sample": count,
                "source_quality_state": "pass",
                "sim_policy_state": "proxy_positive_source",
                "runtime_observation_state": "pending_future_label",
                "bridge_state": "not_ready",
                "conversion_state": "discovered",
                "next_blocker": "pending_future_label",
                "swing_conversion_proxy_lane": "proxy_positive_source",
                "evidence": {"source_artifact": str(path)},
            }
        )
    return candidates


def build_conversion_lane(target_date: str) -> dict[str, Any]:
    key_json_path, _ = key_lineage_paths(target_date)
    key_ledger = _load_json(key_json_path)
    if not key_ledger:
        key_ledger = build_key_lineage_ledger(target_date)
    lifecycle = _load_json(
        DATA_DIR
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json"
    )
    swing_lifecycle = _load_json(
        DATA_DIR
        / "report"
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json"
    )
    runtime_gap = _load_json(
        DATA_DIR
        / "report"
        / "runtime_apply_gap_audit"
        / f"runtime_apply_gap_audit_{target_date}.json"
    )
    buy_funnel = _load_json(
        DATA_DIR
        / "report"
        / "buy_funnel_sentinel"
        / f"buy_funnel_sentinel_{target_date}.json"
    )

    candidates = _candidates_from_lifecycle(lifecycle, "scalp")
    candidates.extend(_candidates_from_lifecycle(swing_lifecycle, "swing"))
    seen = {item["candidate_id"] for item in candidates}
    seen_source_keys = {
        str(item.get("source_key_id") or "")
        for item in candidates
        if item.get("source_key_id")
    }
    lineage_by_key = _lineage_by_source_key(key_ledger)
    for candidate in candidates:
        lineage = lineage_by_key.get(str(candidate.get("source_key_id") or ""))
        if lineage:
            _merge_lineage_candidate(candidate, lineage)
    for row in runtime_gap.get("candidate_route_ledger") or []:
        if not isinstance(row, dict):
            continue
        candidate = _candidate_from_runtime_gap(row)
        if candidate["candidate_id"] in seen:
            continue
        if candidate.get("primary_ev") is not None or candidate.get("next_blocker") in {
            "source_quality",
            "bridge_contract",
        }:
            candidates.append(candidate)
            seen.add(candidate["candidate_id"])
    for candidate in _swing_proxy_candidates(target_date):
        if candidate["candidate_id"] not in seen:
            candidates.append(candidate)
            seen.add(candidate["candidate_id"])
    for row in key_ledger.get("lineage_rows") or []:
        if not isinstance(row, dict):
            continue
        candidate = _candidate_from_matched_bucket_lineage(row)
        if not candidate or candidate["candidate_id"] in seen:
            continue
        if str(candidate.get("source_key_id") or "") in seen_source_keys:
            continue
        candidates.append(candidate)
        seen.add(candidate["candidate_id"])
        seen_source_keys.add(str(candidate.get("source_key_id") or ""))
    for candidate in candidates:
        _annotate_conversion_candidate(candidate)

    blockers: list[dict[str, Any]] = []
    for candidate in candidates:
        blocker_class = _blocker_class(
            str(candidate.get("next_blocker") or ""), candidate
        )
        if candidate.get("conversion_state") != "bounded_real_canary_requestable":
            blockers.append(
                _conversion_blocker(
                    candidate_id=str(candidate.get("candidate_id")),
                    blocker_class=blocker_class,
                    reason=str(candidate.get("next_blocker") or blocker_class),
                    candidate=candidate,
                )
            )
    for item in key_ledger.get("lineage_blockers") or []:
        if not isinstance(item, dict):
            continue
        blockers.append(
            _conversion_blocker(
                candidate_id=str(item.get("source_key_id") or item.get("blocker_id")),
                blocker_class="key_lineage",
                reason=str(item.get("next_repair_action") or "repair_key_lineage"),
                rank_seed=20,
            )
        )
    submit_drought_blockers = _submit_drought_blockers(buy_funnel)
    blockers.extend(submit_drought_blockers)
    blockers.sort(
        key=lambda item: (
            _safe_int(item.get("conversion_impact_rank"), 999),
            _safe_int(item.get("fix_difficulty_rank"), 999),
            str(item.get("conversion_candidate_id") or ""),
        )
    )
    for idx, item in enumerate(blockers, start=1):
        item["conversion_impact_rank"] = idx

    continuity_pass_ids = {
        str(row.get("source_key_id"))
        for row in key_ledger.get("lineage_rows") or []
        if isinstance(row, dict)
        and row.get("same_key_continuity") == "pass"
        and row.get("source_key_id")
    }
    real_queue = [
        item
        for item in candidates
        if item.get("source_quality_state") == "pass"
        and (_safe_float(item.get("primary_ev"), 0.0) or 0.0) > 0
        and (
            item.get("conversion_state") == "bounded_real_canary_requestable"
            or str(item.get("source_key_id") or item.get("candidate_id"))
            in continuity_pass_ids
        )
        and item.get("conversion_state")
        in {
            "runtime_observed",
            "complete_parent_flow",
            "bridge_contract_ready",
            "bounded_real_canary_requestable",
        }
    ]
    sim_priority_only = [
        {
            "candidate_id": row.get("source_key_id"),
            "source_key_type": row.get("source_key_type"),
            "conversion_state": row.get("conversion_state"),
            "excluded_from_real_queue_reason": row.get("next_blocker")
            or "observation_priority_only",
        }
        for row in key_ledger.get("lineage_rows") or []
        if isinstance(row, dict)
        and str(row.get("source_key_type") or "")
        in {"active_seed", "active_arm", "hypothesis"}
        and str(row.get("conversion_state") or "") != "matched"
    ]
    blocker_counts = Counter(
        str(item.get("blocker_class") or "unknown") for item in blockers
    )
    blocker_axis_counts = Counter(
        str(item.get("blocker_axis") or "unknown") for item in blockers
    )
    strategy_scope_counts = Counter(
        str(item.get("strategy_scope") or "unscoped") for item in candidates
    )
    submit_drought_axes = sorted(
        {
            str(item.get("blocker_axis"))
            for item in blockers
            if item.get("blocker_class") == "submit_drought"
            and item.get("blocker_axis")
        }
    )
    positive_ev_runtime_observed_count = sum(
        1
        for item in candidates
        if item.get("positive_ev_candidate") and item.get("runtime_observed_same_key")
    )
    positive_ev_real_conversion_queue_count = sum(
        1 for item in real_queue if item.get("positive_ev_candidate")
    )
    positive_ev_sample_floor_blocked_count = sum(
        1
        for item in candidates
        if item.get("positive_ev_candidate") and item.get("sample_floor_blocked")
    )
    positive_ev_sample_floor_unknown_floor_count = sum(
        1
        for item in candidates
        if item.get("positive_ev_candidate") and item.get("sample_floor_unknown_floor")
    )
    positive_ev_sample_floor_related_count = (
        positive_ev_sample_floor_blocked_count
        + positive_ev_sample_floor_unknown_floor_count
    )
    buy_funnel_provenance = _buy_funnel_provenance(buy_funnel)
    submit_drought_quote_freshness_subactions = (
        buy_funnel_provenance.get("submit_drought_quote_freshness_subaction_counts")
        or {}
    )
    for blocker in blockers:
        if (
            blocker.get("blocker_class") == "submit_drought"
            and blocker.get("blocker_axis") == "LATENCY_PRE_SUBMIT"
        ):
            blocker["quote_freshness_subaction_counts"] = (
                submit_drought_quote_freshness_subactions
            )
            blocker["quote_freshness_source_only"] = True
            blocker["next_repair_action"] = (
                "close_submit_drought_latency_pre_submit_quote_freshness"
            )
    default_sample_floor_window_policy = _source_sample_floor_window_policy(lifecycle)
    sample_floor_window_counts = Counter(
        str(
            item.get("sample_floor_window_policy") or default_sample_floor_window_policy
        )
        for item in candidates
        if item.get("positive_ev_candidate")
        and (item.get("sample_floor_blocked") or item.get("sample_floor_unknown_floor"))
    )
    sample_floor_window_policy = (
        next(iter(sample_floor_window_counts))
        if len(sample_floor_window_counts) == 1
        else (
            "mixed_source_windows"
            if sample_floor_window_counts
            else default_sample_floor_window_policy
        )
    )
    positive_ev_not_due_until_next_preopen_count = sum(
        1
        for item in candidates
        if item.get("positive_ev_candidate")
        and item.get("runtime_observation_scope")
        == "new_postclose_candidate_not_due_until_next_preopen"
    )
    positive_ev_previous_policy_natural_match_0_count = sum(
        1
        for item in candidates
        if item.get("positive_ev_candidate")
        and item.get("runtime_observation_scope")
        == "previous_preopen_policy_natural_match_0"
    )
    ldm_bucket_blockers = [
        item for item in blockers if item.get("blocker_class") != "submit_drought"
    ]
    top_blocker_by_count = (
        blocker_counts.most_common(1)[0][0] if blocker_counts else None
    )
    summary = {
        "conversion_candidate_count": len(candidates),
        "conversion_candidate_strategy_scope_counts": dict(strategy_scope_counts),
        "bounded_real_canary_requestable_count": sum(
            1
            for item in candidates
            if item.get("conversion_state") == "bounded_real_canary_requestable"
        ),
        "top_blocker_class": blockers[0]["blocker_class"] if blockers else None,
        "top_blocker_ranked_class": blockers[0]["blocker_class"] if blockers else None,
        "top_blocker_by_count_class": top_blocker_by_count,
        "top_ldm_bucket_blocker_class": (
            ldm_bucket_blockers[0]["blocker_class"] if ldm_bucket_blockers else None
        ),
        "submit_funnel_blocker_count": len(submit_drought_blockers),
        "submit_drought_is_ldm_bucket_blocker": False,
        "scalp_conversion_candidate_count": sum(
            1 for item in candidates if item.get("strategy_scope") == "scalp"
        ),
        "swing_conversion_candidate_count": sum(
            1 for item in candidates if item.get("strategy_scope") == "swing"
        ),
        "unscoped_conversion_candidate_count": sum(
            1
            for item in candidates
            if str(item.get("strategy_scope") or "") not in {"scalp", "swing"}
        ),
        "sim_priority_only_count": len(sim_priority_only),
        "key_lineage_blocker_count": _safe_int(
            (key_ledger.get("summary") or {}).get("lineage_blocker_count")
        ),
        "real_conversion_queue_count": len(real_queue),
        "positive_ev_runtime_observed_count": positive_ev_runtime_observed_count,
        "positive_ev_real_conversion_queue_count": positive_ev_real_conversion_queue_count,
        "positive_ev_sample_floor_blocked_count": positive_ev_sample_floor_blocked_count,
        "positive_ev_sample_floor_unknown_floor_count": positive_ev_sample_floor_unknown_floor_count,
        "positive_ev_sample_floor_related_count": positive_ev_sample_floor_related_count,
        "positive_ev_sample_floor_count_scope": "conversion_candidates",
        "positive_ev_sample_floor_window_policy": sample_floor_window_policy,
        "positive_ev_sample_floor_window_policy_counts": dict(
            sorted(sample_floor_window_counts.items())
        ),
        "positive_ev_sample_floor_basis": "candidate_sample_vs_required_sample",
        "positive_ev_not_due_until_next_preopen_count": positive_ev_not_due_until_next_preopen_count,
        "positive_ev_previous_policy_natural_match_0_count": positive_ev_previous_policy_natural_match_0_count,
        "active_sim_policy_observation_window_policy": (
            key_ledger.get("summary") or {}
        ).get("active_sim_policy_observation_window_policy"),
        "active_sim_policy_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get("active_sim_policy_event_count")
        ),
        "active_sim_policy_zero_count_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_sim_policy_zero_count_event_count"
            )
        ),
        "active_sim_policy_positive_count_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_sim_policy_positive_count_event_count"
            )
        ),
        "active_sim_policy_active_seed_id_without_count_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_sim_policy_active_seed_id_without_count_event_count"
            )
        ),
        "active_sim_policy_zero_count_effect_excluded": bool(
            (key_ledger.get("summary") or {}).get(
                "active_sim_policy_zero_count_effect_excluded"
            )
        ),
        "active_sim_priority_entry_source_taxonomy_contract_counts": (
            key_ledger.get("summary") or {}
        ).get("active_sim_priority_entry_source_taxonomy_contract_counts")
        or {},
        "active_sim_priority_pending_taxonomy_contract_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_sim_priority_pending_taxonomy_contract_count"
            )
        ),
        "active_seed_candidate_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get("active_seed_candidate_event_count")
        ),
        "active_seed_candidate_new_entry_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_new_entry_event_count"
            )
        ),
        "active_seed_candidate_followup_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_followup_event_count"
            )
        ),
        "active_seed_candidate_matched_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_matched_event_count"
            )
        ),
        "active_seed_candidate_matched_true_without_seed_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_matched_true_without_seed_id_event_count"
            )
        ),
        "active_seed_candidate_unmatched_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_unmatched_event_count"
            )
        ),
        "active_seed_candidate_new_entry_unmatched_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_new_entry_unmatched_event_count"
            )
        ),
        "active_seed_candidate_followup_unmatched_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_followup_unmatched_event_count"
            )
        ),
        "active_seed_candidate_without_seed_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_without_seed_id_event_count"
            )
        ),
        "active_seed_candidate_raw_without_seed_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_raw_without_seed_id_event_count"
            )
        ),
        "active_seed_candidate_followup_without_seed_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_followup_without_seed_id_event_count"
            )
        ),
        "active_seed_candidate_raw_followup_without_seed_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_raw_followup_without_seed_id_event_count"
            )
        ),
        "active_seed_candidate_eligible_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_eligible_event_count"
            )
        ),
        "active_seed_candidate_not_match_eligible_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_not_match_eligible_event_count"
            )
        ),
        "active_seed_candidate_not_match_eligible_reason_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_not_match_eligible_reason_counts")
        or {},
        "active_seed_candidate_without_seed_id_reason_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_without_seed_id_reason_counts")
        or {},
        "active_seed_candidate_without_seed_id_detail_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_without_seed_id_detail_counts")
        or {},
        "active_seed_candidate_inferred_parent_seed_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_inferred_parent_seed_id_event_count"
            )
        ),
        "active_seed_candidate_inferred_parent_seed_id_stage_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_inferred_parent_seed_id_stage_counts")
        or {},
        "active_seed_candidate_inferred_parent_seed_id_prefix_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_inferred_parent_seed_id_prefix_counts")
        or {},
        "active_seed_candidate_ambiguous_parent_seed_prefix_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_ambiguous_parent_seed_prefix_event_count"
            )
        ),
        "active_seed_candidate_missing_parent_seed_lookup_key_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_missing_parent_seed_lookup_key_counts")
        or {},
        "active_seed_candidate_missing_parent_seed_stage_counts": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_missing_parent_seed_stage_counts")
        or {},
        "active_seed_candidate_lineage_closure_status": (
            key_ledger.get("summary") or {}
        ).get("active_seed_candidate_lineage_closure_status"),
        "active_seed_candidate_lineage_followup_required": bool(
            (key_ledger.get("summary") or {}).get(
                "active_seed_candidate_lineage_followup_required"
            )
        ),
        "active_seed_candidate_validation_scope": (key_ledger.get("summary") or {}).get(
            "active_seed_candidate_validation_scope"
        ),
        "panic_scale_in_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get("panic_scale_in_event_count")
        ),
        "panic_scale_in_unique_sim_record_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "panic_scale_in_unique_sim_record_count"
            )
        ),
        "panic_scale_in_match_status_counts": (key_ledger.get("summary") or {}).get(
            "panic_scale_in_match_status_counts"
        )
        or {},
        "panic_scale_in_no_match_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get("panic_scale_in_no_match_event_count")
        ),
        "panic_scale_in_no_match_unique_sim_record_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "panic_scale_in_no_match_unique_sim_record_count"
            )
        ),
        "panic_scale_in_no_match_missing_sim_record_id_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "panic_scale_in_no_match_missing_sim_record_id_event_count"
            )
        ),
        "panic_scale_in_no_match_repeated_followup_event_count": _safe_int(
            (key_ledger.get("summary") or {}).get(
                "panic_scale_in_no_match_repeated_followup_event_count"
            )
        ),
        "panic_scale_in_no_match_source_stage_counts": (
            key_ledger.get("summary") or {}
        ).get("panic_scale_in_no_match_source_stage_counts")
        or {},
        "panic_scale_in_no_match_count_scope": (key_ledger.get("summary") or {}).get(
            "panic_scale_in_no_match_count_scope"
        ),
        "blocker_class_counts": dict(blocker_counts),
        "conversion_blocker_count": len(blockers),
        "blocker_axis_counts": dict(blocker_axis_counts),
        "submit_drought_closure_axis_count": len(submit_drought_axes),
        "submit_drought_closure_axes": submit_drought_axes,
        "submit_drought_split_complete": set(submit_drought_axes)
        == set(SUBMIT_DROUGHT_CLOSURE_AXES),
        **buy_funnel_provenance,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "conversion_lane_observation_only_no_real_order_authority",
        "summary": summary,
        "conversion_candidates": candidates[:500],
        "real_conversion_queue": real_queue[:100],
        "conversion_blocker_rank": blockers[:200],
        "sim_priority_only": sim_priority_only[:200],
        "handoff_continuity": _lineage_handoff_rows(key_ledger)[:500],
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    blockers = (
        report.get("conversion_blocker_rank")
        if isinstance(report.get("conversion_blocker_rank"), list)
        else []
    )
    queue = (
        report.get("real_conversion_queue")
        if isinstance(report.get("real_conversion_queue"), list)
        else []
    )
    lines = [
        f"# Conversion Lane - {report.get('date')}",
        "",
        "## Decision",
        f"- conversion candidates: `{summary.get('conversion_candidate_count', 0)}`",
        f"- real conversion queue: `{summary.get('real_conversion_queue_count', 0)}`",
        f"- positive EV runtime observed: `{summary.get('positive_ev_runtime_observed_count', 0)}`",
        f"- positive EV not due until next PREOPEN: `{summary.get('positive_ev_not_due_until_next_preopen_count', 0)}`",
        f"- positive EV previous-policy natural match 0: `{summary.get('positive_ev_previous_policy_natural_match_0_count', 0)}`",
        f"- positive EV real conversion queue: `{summary.get('positive_ev_real_conversion_queue_count', 0)}`",
        f"- positive EV sample-floor blocked known floor: `{summary.get('positive_ev_sample_floor_blocked_count', 0)}`",
        f"- positive EV sample-floor unknown floor: `{summary.get('positive_ev_sample_floor_unknown_floor_count', 0)}`",
        f"- positive EV sample-floor related total: `{summary.get('positive_ev_sample_floor_related_count', 0)}`",
        f"- positive EV sample-floor provenance: scope=`{summary.get('positive_ev_sample_floor_count_scope') or '-'}` "
        f"window=`{summary.get('positive_ev_sample_floor_window_policy') or '-'}` "
        f"window_counts=`{summary.get('positive_ev_sample_floor_window_policy_counts') or {}}` "
        f"basis=`{summary.get('positive_ev_sample_floor_basis') or '-'}`",
        f"- active sim policy windows: events=`{summary.get('active_sim_policy_event_count', 0)}` "
        f"zero_count=`{summary.get('active_sim_policy_zero_count_event_count', 0)}` "
        f"positive_count=`{summary.get('active_sim_policy_positive_count_event_count', 0)}` "
        f"id_without_count=`{summary.get('active_sim_policy_active_seed_id_without_count_event_count', 0)}` "
        f"zero_count_effect_excluded=`{summary.get('active_sim_policy_zero_count_effect_excluded')}`",
        f"- active sim taxonomy contracts: pending=`{summary.get('active_sim_priority_pending_taxonomy_contract_count', 0)}` "
        f"counts=`{summary.get('active_sim_priority_entry_source_taxonomy_contract_counts') or {}}`",
        f"- active seed candidate validation: total=`{summary.get('active_seed_candidate_event_count', 0)}` "
        f"eligible=`{summary.get('active_seed_candidate_eligible_event_count', 0)}` "
        f"not_match_eligible=`{summary.get('active_seed_candidate_not_match_eligible_event_count', 0)}` "
        f"not_match_eligible_reasons=`{summary.get('active_seed_candidate_not_match_eligible_reason_counts') or {}}` "
        f"new_entry=`{summary.get('active_seed_candidate_new_entry_event_count', 0)}` "
        f"followup=`{summary.get('active_seed_candidate_followup_event_count', 0)}` "
        f"matched=`{summary.get('active_seed_candidate_matched_event_count', 0)}` "
        f"matched_true_without_seed_id=`{summary.get('active_seed_candidate_matched_true_without_seed_id_event_count', 0)}` "
        f"unmatched=`{summary.get('active_seed_candidate_unmatched_event_count', 0)}` "
        f"new_entry_unmatched=`{summary.get('active_seed_candidate_new_entry_unmatched_event_count', 0)}` "
        f"followup_unmatched=`{summary.get('active_seed_candidate_followup_unmatched_event_count', 0)}` "
        f"eligible_without_seed_id=`{summary.get('active_seed_candidate_without_seed_id_event_count', 0)}` "
        f"without_seed_reasons=`{summary.get('active_seed_candidate_without_seed_id_reason_counts') or {}}` "
        f"without_seed_details=`{summary.get('active_seed_candidate_without_seed_id_detail_counts') or {}}` "
        f"inferred_parent_seed_id=`{summary.get('active_seed_candidate_inferred_parent_seed_id_event_count', 0)}` "
        f"inferred_stages=`{summary.get('active_seed_candidate_inferred_parent_seed_id_stage_counts') or {}}` "
        f"ambiguous_prefix=`{summary.get('active_seed_candidate_ambiguous_parent_seed_prefix_event_count', 0)}` "
        f"missing_parent_stages=`{summary.get('active_seed_candidate_missing_parent_seed_stage_counts') or {}}` "
        f"raw_without_seed_id=`{summary.get('active_seed_candidate_raw_without_seed_id_event_count', 0)}` "
        f"eligible_followup_without_seed_id=`{summary.get('active_seed_candidate_followup_without_seed_id_event_count', 0)}` "
        f"raw_followup_without_seed_id=`{summary.get('active_seed_candidate_raw_followup_without_seed_id_event_count', 0)}`",
        f"- panic scale-in no-match: events=`{summary.get('panic_scale_in_no_match_event_count', 0)}` "
        f"unique_sim_records=`{summary.get('panic_scale_in_no_match_unique_sim_record_count', 0)}` "
        f"missing_sim_record_id=`{summary.get('panic_scale_in_no_match_missing_sim_record_id_event_count', 0)}` "
        f"repeated_followup=`{summary.get('panic_scale_in_no_match_repeated_followup_event_count', 0)}` "
        f"status_counts=`{summary.get('panic_scale_in_match_status_counts') or {}}` "
        f"source_stage_counts=`{summary.get('panic_scale_in_no_match_source_stage_counts') or {}}`",
        f"- conversion candidate strategy scope: scalp=`{summary.get('scalp_conversion_candidate_count', 0)}` "
        f"swing=`{summary.get('swing_conversion_candidate_count', 0)}` "
        f"unscoped=`{summary.get('unscoped_conversion_candidate_count', 0)}`",
        f"- bounded real canary requestable: `{summary.get('bounded_real_canary_requestable_count', 0)}`",
        f"- top blocker ranked: `{summary.get('top_blocker_ranked_class') or 'none'}`; "
        f"top blocker by count: `{summary.get('top_blocker_by_count_class') or 'none'}`",
        f"- top LDM bucket blocker: `{summary.get('top_ldm_bucket_blocker_class') or 'none'}`",
        f"- submit funnel blocker count: `{summary.get('submit_funnel_blocker_count', 0)}` "
        f"(submit_drought_is_ldm_bucket_blocker=`{summary.get('submit_drought_is_ldm_bucket_blocker')}`)",
        f"- buy funnel source: present=`{summary.get('buy_funnel_source_present')}` "
        f"primary=`{summary.get('buy_funnel_classification_primary') or '-'}` "
        f"matches=`{summary.get('buy_funnel_classification_matches') or []}` "
        f"submit_drought_source_state=`{summary.get('submit_drought_blocker_source_state') or '-'}`",
        "",
        "## Top Conversion Blockers",
    ]
    if blockers:
        for item in blockers[:20]:
            lines.append(
                f"- #{item.get('conversion_impact_rank')} `{item.get('conversion_candidate_id')}`: {item.get('blocker_class')} -> {item.get('next_repair_action')}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Real Conversion Queue"])
    if queue:
        for item in queue[:20]:
            lines.append(
                f"- `{item.get('candidate_id')}`: state={item.get('conversion_state')} ev={item.get('primary_ev')} sample={item.get('sample')}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def write_conversion_lane(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build conversion lane")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_conversion_lane(args.date)
    json_path, md_path = write_conversion_lane(report)
    print(
        json.dumps(
            {"json": str(json_path), "md": str(md_path), "summary": report["summary"]},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
