"""Build the unified Scalping sim-only auto-approval artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine import lifecycle_bucket_discovery
from src.engine.lifecycle_bucket_discovery import bucket_catalog_path, sim_auto_approval_path
from src.engine.monitoring import rising_missed_classifier_prior
from src.engine.runtime_apply_bridge import runtime_apply_bridge_report_path
from src.engine.scalp_sim_scale_in_window_approval import approval_path as scale_in_approval_path
from src.utils.constants import DATA_DIR


REPORT_TYPE = "scalp_sim_auto_approval"
SCHEMA_VERSION = "scalp_sim_auto_approval_v1"
POLICY_ID = "scalp_sim_auto_approval"
DECISION_AUTHORITY = "scalp_sim_auto_approval_control_tower"

SIM_AUTO_APPROVAL_DIR = Path(DATA_DIR) / "threshold_cycle" / "sim_auto_approvals"
SCALP_SIM_POLICY_DIR = Path(DATA_DIR) / "threshold_cycle" / "scalp_sim_policies"
LDM_HYPOTHESIS_PLAN_DIR = Path(DATA_DIR) / "threshold_cycle" / "ldm_hypothesis_observation_plans"
RISING_MISSED_CLASSIFIER_PRIOR_DIR = Path(DATA_DIR) / "report" / "rising_missed_classifier_prior"

FORBIDDEN_USES = [
    "broker_order_submit",
    "real_order_enable",
    "live_threshold_apply",
    "provider_route_change",
    "bot_restart",
    "sizing_formula_runtime_apply_without_guard",
    "hard_safety_override",
]


SCALP_SIM_POLICY_GENERATOR_FILES = (
    Path(lifecycle_bucket_discovery.__file__),
    Path(rising_missed_classifier_prior.__file__),
    Path(__file__),
)


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _generator_provenance() -> dict[str, Any]:
    files = {}
    for path in SCALP_SIM_POLICY_GENERATOR_FILES:
        digest = _file_sha256(path)
        if digest:
            files[path.name] = digest
    return {
        "hash_algorithm": "sha256",
        "files": files,
    }


def scalp_sim_auto_approval_path(target_date: str) -> Path:
    return SIM_AUTO_APPROVAL_DIR / f"{REPORT_TYPE}_{target_date}.json"


def scalp_sim_policy_catalog_path(target_date: str) -> Path:
    return SCALP_SIM_POLICY_DIR / f"scalp_sim_policy_catalog_{target_date}.json"


def rising_missed_classifier_prior_path(target_date: str) -> Path:
    return RISING_MISSED_CLASSIFIER_PRIOR_DIR / f"rising_missed_classifier_prior_{target_date}.json"


def _latest_hypothesis_observation_plan(target_date: str) -> dict[str, Any]:
    exact = LDM_HYPOTHESIS_PLAN_DIR / f"ldm_hypothesis_observation_plan_{target_date}.json"
    if exact.exists():
        return _load_json(exact)
    candidates: list[tuple[str, Path]] = []
    if LDM_HYPOTHESIS_PLAN_DIR.exists():
        for path in LDM_HYPOTHESIS_PLAN_DIR.glob("ldm_hypothesis_observation_plan_*.json"):
            plan_date = path.stem.removeprefix("ldm_hypothesis_observation_plan_")
            if plan_date <= target_date:
                candidates.append((plan_date, path))
    if not candidates:
        return {}
    return _load_json(sorted(candidates)[-1][1])


def _lifecycle_contract_ok(payload: dict[str, Any]) -> bool:
    return (
        payload.get("schema_version") == "lifecycle_bucket_sim_auto_approval_v1"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
        and payload.get("human_approval_required") is False
    )


def _scale_in_contract_ok(payload: dict[str, Any]) -> bool:
    return (
        str(payload.get("policy_id") or payload.get("family") or "") == "scalp_sim_scale_in_window_expansion"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("human_approval_required") is False
        and payload.get("source_quality_status") in {None, "pass"}
    )


def _rising_missed_prior_contract_ok(payload: dict[str, Any]) -> bool:
    return (
        payload.get("report_type") == "rising_missed_classifier_prior"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") in {None, False}
        and payload.get("broker_order_forbidden") in {None, True}
        and payload.get("allowed_runtime_apply") is False
        and payload.get("decision_authority") == "rising_missed_classifier_prior_source_only"
    )


def _active_seed_prefix_key(prefix: dict[str, Any] | None) -> str:
    prefix = prefix if isinstance(prefix, dict) else {}
    entry_score = str(prefix.get("entry_score_parent") or "").strip()
    entry_source = str(prefix.get("entry_source_parent") or "").strip()
    submit_quality = str(prefix.get("submit_quality_parent") or "").strip()
    if not entry_score or not entry_source:
        return ""
    parts = [f"entry_score_parent={entry_score}", f"entry_source_parent={entry_source}"]
    if submit_quality:
        parts.append(f"submit_quality_parent={submit_quality}")
    return "|".join(parts)


def _rising_missed_prior_observable_prefix(row: dict[str, Any]) -> dict[str, str]:
    raw = row.get("observable_prefix") if isinstance(row.get("observable_prefix"), dict) else {}
    prefix: dict[str, str] = {}
    for key in ("entry_score_parent", "entry_source_parent", "submit_quality_parent"):
        value = str(raw.get(key) or "").strip()
        if value and value != "-":
            prefix[key] = value
    return prefix


def _rising_missed_prior_metric(row: dict[str, Any]) -> dict[str, Any]:
    window = str(row.get("selected_window") or "").strip()
    metrics = row.get("window_metrics") if isinstance(row.get("window_metrics"), dict) else {}
    metric = metrics.get(window) if isinstance(metrics.get(window), dict) else {}
    return {
        "selected_window": window or None,
        "ev_pct": metric.get("ev_pct"),
        "joined_sample": metric.get("joined_sample") or metric.get("sample"),
    }


def _rising_missed_prior_seed_id(row: dict[str, Any], prefix: dict[str, str]) -> str:
    source = json.dumps(
        {
            "prior_key": row.get("prior_key"),
            "recommendation": row.get("recommendation"),
            "prefix": prefix,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "rising_missed_prior_" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _rising_missed_prior_policy_item(payload: dict[str, Any], source_path: Path) -> dict[str, Any] | None:
    if not _rising_missed_prior_contract_ok(payload):
        return None
    rows = [row for row in (payload.get("priors") or []) if isinstance(row, dict)]
    active_seeds: list[dict[str, Any]] = []
    seed_status_overrides: list[dict[str, Any]] = []
    observation_lanes: list[dict[str, Any]] = []
    for row in rows:
        recommendation = str(row.get("recommendation") or "").strip()
        prefix = _rising_missed_prior_observable_prefix(row)
        prefix_key = _active_seed_prefix_key(prefix)
        metric = _rising_missed_prior_metric(row)
        lane = {
            "prior_key": row.get("prior_key"),
            "recommendation": recommendation,
            "confidence": row.get("confidence"),
            "reason": row.get("reason"),
            "selected_window": metric.get("selected_window"),
            "ev_pct": metric.get("ev_pct"),
            "joined_sample": metric.get("joined_sample"),
            "observable_prefix": row.get("observable_prefix") if isinstance(row.get("observable_prefix"), dict) else {},
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        observation_lanes.append(lane)
        if not prefix_key:
            continue
        if recommendation in {"source_quality_blocked", "loss_filter", "quality_risk"}:
            seed_status_overrides.append(
                {
                    "prefix_key": prefix_key,
                    "observable_prefix": prefix,
                    "forced_status": "cooldown",
                    "reason": f"rising_missed_prior_{recommendation}",
                    "prior_key": row.get("prior_key"),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
            continue
        if recommendation not in {"positive_prior", "recheck_prior"}:
            continue
        active_seeds.append(
            {
                "active_seed_id": _rising_missed_prior_seed_id(row, prefix),
                "source_parent_bucket_id": str(row.get("prior_key") or prefix_key),
                "policy_version": f"rising_missed_classifier_prior:{payload.get('target_date') or payload.get('date')}",
                "status": "active",
                "priority_tier": f"rising_missed_{recommendation}",
                "observable_prefix": prefix,
                "parent_ev_pct": metric.get("ev_pct"),
                "parent_joined_sample": metric.get("joined_sample"),
                "active_collection_reason": f"rising_missed_{recommendation}_active_sim_collection",
                "targeted_sim_quota": {
                    "quota_policy_version": "rising_missed_classifier_prior_v1",
                    "daily_total_share_pct": 15,
                    "per_seed_daily_limit": 8,
                    "sample_goal_per_bucket": 10,
                    "quota_scope": "rising_missed_prior_prefix_revisit",
                },
                "source_quality_status": "pass",
                "rising_missed_prior_recommendation": recommendation,
                "rising_missed_prior_confidence": row.get("confidence"),
                "rising_missed_prior_reason": row.get("reason"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        )
    if not (active_seeds or seed_status_overrides):
        return None
    return {
        "source_id": "rising_missed_classifier_prior",
        "policy_kind": "rising_missed_prior_sim_observation_policy",
        "policy_id": "rising_missed_classifier_prior",
        "policy_file": str(source_path),
        "active_sim_priority_seeds": active_seeds,
        "active_sim_priority_seed_count": len(active_seeds),
        "active_seed_status_overrides": seed_status_overrides,
        "active_seed_status_override_count": len(seed_status_overrides),
        "observation_lanes": observation_lanes,
        "observation_lane_count": len(observation_lanes),
        "recommendation_counts": (payload.get("summary") or {}).get("recommendation_counts") or {},
        "classification_state": "sim_observation_priority",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _lifecycle_policy_item(payload: dict[str, Any], catalog_path: Path) -> dict[str, Any] | None:
    if not _lifecycle_contract_ok(payload):
        return None
    if not catalog_path.exists():
        return None
    bucket_ids = [str(item) for item in (payload.get("approved_bucket_ids") or []) if str(item or "").strip()]
    bucket_rows = [
        item
        for item in (payload.get("approved_bucket_rows") or [])
        if isinstance(item, dict) and str(item.get("bucket_id") or "").strip()
    ]
    active_seeds = [
        item
        for item in (payload.get("active_sim_priority_seeds") or [])
        if isinstance(item, dict) and str(item.get("active_seed_id") or "").strip()
    ]
    if not bool(payload.get("approved")) or not (bucket_rows or bucket_ids or active_seeds):
        return None
    unique_source_bucket_ids = {
        str(item.get("source_bucket_id") or item.get("bucket_id") or "")
        for item in bucket_rows
        if str(item.get("source_bucket_id") or item.get("bucket_id") or "").strip()
    }
    return {
        "source_id": "lifecycle_bucket_discovery",
        "policy_kind": "lifecycle_bucket_sim_policy",
        "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
        "policy_file": str(catalog_path),
        "approved_bucket_ids": bucket_ids,
        "approved_bucket_rows": bucket_rows,
        "active_sim_priority_seeds": active_seeds,
        "active_sim_priority_seed_count": len(active_seeds),
        "active_sim_priority_seed_status_counts": payload.get("active_sim_priority_seed_status_counts") or {},
        "approved_bucket_count": len(bucket_rows) if bucket_rows else len(bucket_ids),
        "approved_unique_source_bucket_count": (
            len(unique_source_bucket_ids)
            if bucket_rows
            else payload.get("approved_unique_source_bucket_count")
        ),
        "approved_evidence_grade_counts": payload.get("approved_evidence_grade_counts") or {},
        "classification_state": "sim_auto_approved",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _scale_in_policy_item(payload: dict[str, Any]) -> dict[str, Any] | None:
    if not _scale_in_contract_ok(payload):
        return None
    if not bool(payload.get("approved")) or payload.get("approval_state") != "sim_auto_approved":
        return None
    return {
        "source_id": "scalp_sim_scale_in_window_approval",
        "policy_kind": "scalp_sim_scale_in_window_policy",
        "policy_id": "scalp_sim_scale_in_window_expansion",
        "stage": "scale_in",
        "target_env_keys": payload.get("target_env_keys") or [],
        "recommended_values": payload.get("recommended_values") if isinstance(payload.get("recommended_values"), dict) else {},
        "source_summary": payload.get("source_summary") if isinstance(payload.get("source_summary"), dict) else {},
        "classification_state": "sim_auto_approved",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "real_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _runtime_bridge_summary(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    live_ready = [
        item
        for item in candidates
        if isinstance(item, dict)
        and item.get("bridge_candidate_state") == "live_auto_apply_ready"
        and item.get("allowed_runtime_apply") is True
        and item.get("live_auto_apply") is True
    ]
    return {
        "candidate_count": len(candidates),
        "live_auto_apply_ready_count": len(live_ready),
        "live_ready_families": sorted({str(item.get("family") or "") for item in live_ready if item.get("family")}),
        "catalog_authority": "summary_only_not_sim_catalog_promotion",
    }


def build_scalp_sim_auto_approval(
    target_date: str,
    *,
    lifecycle_sim_approval: dict[str, Any] | None = None,
    lifecycle_bucket_catalog_path: Path | None = None,
    scale_in_approval: dict[str, Any] | None = None,
    runtime_apply_bridge: dict[str, Any] | None = None,
    rising_missed_prior: dict[str, Any] | None = None,
    source_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    default_paths = {
        "lifecycle_sim_auto_approval": sim_auto_approval_path(date_key),
        "lifecycle_bucket_catalog": bucket_catalog_path(date_key),
        "scalp_sim_scale_in_window_approval": scale_in_approval_path(date_key),
        "runtime_apply_bridge": runtime_apply_bridge_report_path(date_key),
        "rising_missed_classifier_prior": rising_missed_classifier_prior_path(date_key),
    }
    paths = {**default_paths, **(source_paths or {})}
    lifecycle_payload = (
        lifecycle_sim_approval
        if isinstance(lifecycle_sim_approval, dict)
        else _load_json(paths["lifecycle_sim_auto_approval"])
    )
    scale_payload = (
        scale_in_approval
        if isinstance(scale_in_approval, dict)
        else _load_json(paths["scalp_sim_scale_in_window_approval"])
    )
    bridge_payload = (
        runtime_apply_bridge
        if isinstance(runtime_apply_bridge, dict)
        else _load_json(paths["runtime_apply_bridge"])
    )
    rising_missed_prior_payload = (
        rising_missed_prior
        if isinstance(rising_missed_prior, dict)
        else _load_json(paths["rising_missed_classifier_prior"])
    )
    catalog_path = lifecycle_bucket_catalog_path or paths["lifecycle_bucket_catalog"]

    policy_items: list[dict[str, Any]] = []
    lifecycle_policy = _lifecycle_policy_item(lifecycle_payload, catalog_path)
    if lifecycle_policy:
        policy_items.append(lifecycle_policy)
    scale_policy = _scale_in_policy_item(scale_payload)
    if scale_policy:
        policy_items.append(scale_policy)
    rising_missed_prior_policy = _rising_missed_prior_policy_item(
        rising_missed_prior_payload,
        paths["rising_missed_classifier_prior"],
    )
    if rising_missed_prior_policy:
        policy_items.append(rising_missed_prior_policy)

    source_status = {
        "lifecycle_sim_auto_approval": {
            "path": str(paths["lifecycle_sim_auto_approval"]),
            "present": bool(lifecycle_payload),
            "contract_ok": _lifecycle_contract_ok(lifecycle_payload),
            "approved_bucket_count": len((lifecycle_payload.get("approved_bucket_ids") or []) if lifecycle_payload else []),
            "approved_bucket_row_count": len((lifecycle_payload.get("approved_bucket_rows") or []) if lifecycle_payload else []),
            "active_sim_priority_seed_count": len(
                (lifecycle_payload.get("active_sim_priority_seeds") or []) if lifecycle_payload else []
            ),
            "approved_unique_source_bucket_count": (
                lifecycle_payload.get("approved_unique_source_bucket_count")
                if lifecycle_payload
                else None
            ),
        },
        "lifecycle_bucket_catalog": {
            "path": str(catalog_path),
            "present": catalog_path.exists(),
        },
        "scalp_sim_scale_in_window_approval": {
            "path": str(paths["scalp_sim_scale_in_window_approval"]),
            "present": bool(scale_payload),
            "contract_ok": _scale_in_contract_ok(scale_payload),
            "sim_auto_approved": scale_policy is not None,
        },
        "runtime_apply_bridge": {
            "path": str(paths["runtime_apply_bridge"]),
            "present": bool(bridge_payload),
            **_runtime_bridge_summary(bridge_payload),
        },
        "rising_missed_classifier_prior": {
            "path": str(paths["rising_missed_classifier_prior"]),
            "present": bool(rising_missed_prior_payload),
            "contract_ok": _rising_missed_prior_contract_ok(rising_missed_prior_payload),
            "prior_count": (rising_missed_prior_payload.get("summary") or {}).get("prior_count")
            if isinstance(rising_missed_prior_payload.get("summary"), dict)
            else None,
            "recommendation_counts": (rising_missed_prior_payload.get("summary") or {}).get(
                "recommendation_counts"
            )
            if isinstance(rising_missed_prior_payload.get("summary"), dict)
            else {},
            "active_seed_count": len(
                (rising_missed_prior_policy or {}).get("active_sim_priority_seeds") or []
            ),
            "active_seed_status_override_count": len(
                (rising_missed_prior_policy or {}).get("active_seed_status_overrides") or []
            ),
        },
    }
    blocked_reasons: list[str] = []
    if lifecycle_payload and not source_status["lifecycle_sim_auto_approval"]["contract_ok"]:
        blocked_reasons.append("lifecycle_sim_auto_approval_contract_invalid")
    if lifecycle_payload and not catalog_path.exists():
        blocked_reasons.append("lifecycle_bucket_catalog_missing")
    if scale_payload and not source_status["scalp_sim_scale_in_window_approval"]["contract_ok"]:
        blocked_reasons.append("scalp_sim_scale_in_window_contract_invalid")
    if rising_missed_prior_payload and not source_status["rising_missed_classifier_prior"]["contract_ok"]:
        blocked_reasons.append("rising_missed_classifier_prior_contract_invalid")
    if not policy_items:
        blocked_reasons.append("sim_policy_candidate_missing")
    approved_source_ids = sorted({str(item.get("source_id")) for item in policy_items if item.get("source_id")})
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "policy_id": POLICY_ID,
        "approved": bool(policy_items) and not any(reason.endswith("_contract_invalid") for reason in blocked_reasons),
        "human_approval_required": False,
        "runtime_effect": False,
        "source_only": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "decision_authority": DECISION_AUTHORITY,
        "approval_scope": "next_preopen_scalp_sim_policy",
        "final_user_approval_boundary": "real_runtime_only",
        "policy_file": str(scalp_sim_policy_catalog_path(date_key)),
        "approved_source_ids": approved_source_ids,
        "approved_policy_count": len(policy_items),
        "approved_policies": policy_items,
        "source_status": source_status,
        "blocked_reasons": blocked_reasons if not policy_items or not approved_source_ids else [
            reason for reason in blocked_reasons if reason.endswith("_contract_invalid")
        ],
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_policy_catalog(approval: dict[str, Any]) -> dict[str, Any]:
    active_seeds: list[dict[str, Any]] = []
    active_seed_status_overrides: list[dict[str, Any]] = []
    rising_missed_prior_lanes: list[dict[str, Any]] = []
    for policy in approval.get("approved_policies") or []:
        if not isinstance(policy, dict):
            continue
        active_seeds.extend(
            item
            for item in (policy.get("active_sim_priority_seeds") or [])
            if isinstance(item, dict) and str(item.get("active_seed_id") or "").strip()
        )
        active_seed_status_overrides.extend(
            item
            for item in (policy.get("active_seed_status_overrides") or [])
            if isinstance(item, dict) and str(item.get("prefix_key") or "").strip()
        )
        if policy.get("source_id") == "rising_missed_classifier_prior":
            rising_missed_prior_lanes.extend(
                item for item in (policy.get("observation_lanes") or []) if isinstance(item, dict)
            )
    target_date = _date_text(approval.get("date"))
    hypothesis_plan = _latest_hypothesis_observation_plan(target_date)
    overrides_by_prefix = {
        str(item.get("prefix_key") or "").strip(): item
        for item in active_seed_status_overrides
        if str(item.get("prefix_key") or "").strip()
    }
    adjusted_seeds: list[dict[str, Any]] = []
    for seed in active_seeds:
        prefix_key = _active_seed_prefix_key(seed.get("observable_prefix") if isinstance(seed, dict) else {})
        override = overrides_by_prefix.get(prefix_key)
        if override and str(seed.get("status") or "") == "active":
            adjusted = dict(seed)
            adjusted["status"] = str(override.get("forced_status") or "cooldown")
            adjusted["rising_missed_prior_status_override"] = {
                "reason": override.get("reason"),
                "prior_key": override.get("prior_key"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
            adjusted_seeds.append(adjusted)
        else:
            adjusted_seeds.append(seed)
    return {
        "schema_version": "scalp_sim_policy_catalog_v1",
        "date": approval.get("date"),
        "generated_at": approval.get("generated_at"),
        "generator_provenance": _generator_provenance(),
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "approved_source_ids": approval.get("approved_source_ids") or [],
        "policies": approval.get("approved_policies") or [],
        "active_sim_priority_seeds": adjusted_seeds,
        "rising_missed_prior_observation_lanes": rising_missed_prior_lanes,
        "rising_missed_prior_active_seed_status_overrides": active_seed_status_overrides,
        "active_priority_lineage": {
            "source": "scalp_sim_auto_approval",
            "active_sim_priority_seed_count": len(adjusted_seeds),
            "rising_missed_prior_observation_lane_count": len(rising_missed_prior_lanes),
            "rising_missed_prior_active_seed_status_override_count": len(active_seed_status_overrides),
            "lineage_artifact": f"data/report/key_lineage_ledger/key_lineage_ledger_{target_date}.json",
        },
        "hypothesis_observation_plan": hypothesis_plan or {},
        "forbidden_uses": FORBIDDEN_USES,
    }


def write_scalp_sim_auto_approval(approval: dict[str, Any]) -> dict[str, Path]:
    date_key = _date_text(approval.get("date"))
    SIM_AUTO_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    SCALP_SIM_POLICY_DIR.mkdir(parents=True, exist_ok=True)
    approval_path = scalp_sim_auto_approval_path(date_key)
    catalog_path = scalp_sim_policy_catalog_path(date_key)
    approval_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    catalog_path.write_text(
        json.dumps(build_policy_catalog(approval), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return {"approval": approval_path, "catalog": catalog_path}


def refresh_scalp_sim_auto_approval(target_date: str) -> dict[str, Path]:
    return write_scalp_sim_auto_approval(build_scalp_sim_auto_approval(target_date))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build scalp sim-auto approval control tower artifact.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    paths = refresh_scalp_sim_auto_approval(args.target_date)
    print(json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
