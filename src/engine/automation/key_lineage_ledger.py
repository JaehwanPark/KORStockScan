"""Build daily key-lineage ledger for sim-to-real conversion tracking."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR


REPORT_TYPE = "key_lineage_ledger"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"
SCALP_POLICY_DIR = DATA_DIR / "threshold_cycle" / "scalp_sim_policies"
SWING_POLICY_DIR = DATA_DIR / "threshold_cycle" / "swing_sim_policies"
HYPOTHESIS_PLAN_DIR = DATA_DIR / "threshold_cycle" / "ldm_hypothesis_observation_plans"

LINEAGE_BLOCKER_STATES = {"key_mismatch", "catalog_missing", "preopen_missing", "not_instrumented"}
ALLOWED_STATES = {
    "collecting",
    "cooldown_intentional",
    "cooldown_blocks_conversion",
    "matched",
    "natural_match_0",
    "not_instrumented",
    "key_mismatch",
    "catalog_missing",
    "preopen_missing",
    "postclose_missing",
    "source_quality_blocked",
    "bridge_blocked",
    "real_canary_requestable",
}


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


def _stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _runtime_apply_path(target_date: str) -> Path:
    exact = APPLY_PLAN_DIR / f"threshold_apply_{target_date}.json"
    if exact.exists():
        return exact
    candidates: list[tuple[str, Path]] = []
    if APPLY_PLAN_DIR.exists():
        for path in APPLY_PLAN_DIR.glob("threshold_apply_*.json"):
            apply_date = path.stem.removeprefix("threshold_apply_")
            if apply_date <= target_date:
                candidates.append((apply_date, path))
    if candidates:
        return sorted(candidates)[-1][1]
    return exact


def _apply_source_date(apply_plan: dict[str, Any], target_date: str) -> str:
    return str(apply_plan.get("source_date") or target_date)


def _catalog_path_from_apply(
    apply_plan: dict[str, Any],
    *,
    section_key: str,
    env_key: str,
    default_dir: Path,
    default_prefix: str,
    target_date: str,
) -> Path:
    section = apply_plan.get(section_key) if isinstance(apply_plan.get(section_key), dict) else {}
    for key in ("catalog", "policy_file"):
        value = section.get(key)
        if str(value or "").strip():
            return Path(str(value))
    env_exports = apply_plan.get("env_exports") if isinstance(apply_plan.get("env_exports"), dict) else {}
    value = env_exports.get(env_key)
    if str(value or "").strip():
        return Path(str(value))
    policy_files = _collect_values(section, {"policy_file"})
    for value in sorted(policy_files):
        if default_prefix in value:
            return Path(value)
    source_date = str(apply_plan.get("source_date") or target_date)
    return default_dir / f"{default_prefix}_{source_date}.json"


def _latest_hypothesis_plan_path(target_date: str) -> Path:
    exact = HYPOTHESIS_PLAN_DIR / f"ldm_hypothesis_observation_plan_{target_date}.json"
    if exact.exists():
        return exact
    candidates: list[tuple[str, Path]] = []
    if HYPOTHESIS_PLAN_DIR.exists():
        for path in HYPOTHESIS_PLAN_DIR.glob("ldm_hypothesis_observation_plan_*.json"):
            plan_date = path.stem.removeprefix("ldm_hypothesis_observation_plan_")
            if plan_date <= target_date:
                candidates.append((plan_date, path))
    if candidates:
        return sorted(candidates)[-1][1]
    return exact


def _collect_values(payload: Any, keys: set[str]) -> set[str]:
    values: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in keys:
                if isinstance(value, list):
                    values.update(str(item) for item in value if str(item or "").strip())
                elif str(value or "").strip():
                    values.add(str(value))
            values.update(_collect_values(value, keys))
    elif isinstance(payload, list):
        for item in payload:
            values.update(_collect_values(item, keys))
    return values


def _event_field_values(target_date: str) -> dict[str, set[str]]:
    field_keys = {
        "active_seed_id",
        "active_sim_priority_seed_id",
        "scalp_sim_active_priority_seed_id",
        "priority_policy_id",
        "active_arm_priority_policy_id",
        "swing_priority_policy_id",
        "ldm_hypothesis_id",
        "hypothesis_id",
        "ldm_hypothesis_matched",
        "hypothesis_match_status",
        "ldm_hypothesis_candidate_features",
        "bucket_directed_sim_probe",
        "lifecycle_bucket_match_status",
        "lifecycle_bucket_bucket_id",
        "lifecycle_bucket_source_bucket_id",
        "lifecycle_bucket_matched_bucket_id",
        "lifecycle_bucket_matched_source_bucket_id",
    }
    values = {key: set() for key in field_keys}
    paths = [
        DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl",
    ]
    for path in paths:
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            fields = payload.get("fields") if isinstance(payload, dict) else {}
            for key in field_keys:
                value = fields.get(key) if isinstance(fields, dict) else None
                if str(value or "").strip():
                    values[key].add(str(value))
            if not isinstance(fields, dict):
                continue
            if str(fields.get("lifecycle_bucket_match_status") or "").strip().lower() == "matched":
                bucket_id = str(fields.get("lifecycle_bucket_bucket_id") or "").strip()
                source_bucket_id = str(fields.get("lifecycle_bucket_source_bucket_id") or "").strip()
                if bucket_id:
                    values["lifecycle_bucket_matched_bucket_id"].add(bucket_id)
                if source_bucket_id:
                    values["lifecycle_bucket_matched_source_bucket_id"].add(source_bucket_id)
    return values


def _event_any_hypothesis_instrumented(events: dict[str, set[str]]) -> bool:
    return bool(
        events.get("ldm_hypothesis_id")
        or events.get("hypothesis_id")
        or events.get("ldm_hypothesis_matched")
        or events.get("hypothesis_match_status")
        or events.get("ldm_hypothesis_candidate_features")
    )


def _seed_id(seed: dict[str, Any]) -> str:
    return str(seed.get("active_seed_id") or seed.get("seed_id") or seed.get("source_key_id") or "").strip()


def _policy_id(policy: dict[str, Any]) -> str:
    return str(policy.get("priority_policy_id") or policy.get("policy_id") or policy.get("active_arm_policy_id") or "").strip()


def _hypothesis_id(item: dict[str, Any]) -> str:
    return str(
        item.get("hypothesis_id")
        or item.get("ldm_hypothesis_id")
        or item.get("soft_hypothesis_id")
        or item.get("source_key_id")
        or ""
    ).strip()


def _hypotheses_from_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("hypotheses", "observation_plan", "plans", "items"):
        value = plan.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _catalog_hypotheses(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    section = catalog.get("hypothesis_observation_plan")
    if isinstance(section, dict):
        return _hypotheses_from_plan(section)
    if isinstance(section, list):
        return [item for item in section if isinstance(item, dict)]
    return []


def _row(
    *,
    source_key_id: str,
    source_key_type: str,
    source_artifact: str,
    catalog_key_present: bool,
    preopen_policy_selected: bool,
    runtime_match_key: str | None,
    postclose_observed_key: str | None,
    conversion_state: str,
    next_blocker: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = conversion_state if conversion_state in ALLOWED_STATES else "not_instrumented"
    runtime_key = runtime_match_key or ""
    postclose_key = postclose_observed_key or ""
    same_key = bool(source_key_id and (runtime_key == source_key_id or postclose_key == source_key_id))
    if state == "key_mismatch":
        same_key_continuity = "fail"
    elif same_key:
        same_key_continuity = "pass"
    else:
        same_key_continuity = "not_observed"
    evidence = evidence or {}
    raw_primary_ev = evidence.get("primary_ev")
    if raw_primary_ev in (None, ""):
        raw_primary_ev = evidence.get("source_quality_adjusted_ev_pct")
    primary_ev = _safe_float(raw_primary_ev)
    runtime_observed_same_key = same_key_continuity == "pass"
    positive_ev_candidate = bool(primary_ev is not None and primary_ev > 0)
    return {
        "source_key_id": source_key_id,
        "source_key_type": source_key_type,
        "source_artifact": source_artifact,
        "catalog_key_present": catalog_key_present,
        "preopen_policy_selected": preopen_policy_selected,
        "runtime_match_key": runtime_key or None,
        "postclose_observed_key": postclose_key or None,
        "same_key_continuity": same_key_continuity,
        "conversion_state": state,
        "next_blocker": next_blocker,
        "positive_ev_candidate": positive_ev_candidate,
        "runtime_observed_same_key": runtime_observed_same_key,
        "sample_floor_blocked": next_blocker == "sample_floor",
        "evidence": evidence,
    }


def _scalp_rows(
    *,
    discovery: dict[str, Any],
    catalog: dict[str, Any],
    apply_plan: dict[str, Any],
    events: dict[str, set[str]],
) -> list[dict[str, Any]]:
    catalog_seeds = [item for item in catalog.get("active_sim_priority_seeds") or [] if isinstance(item, dict)]
    catalog_by_id = {_seed_id(item): item for item in catalog_seeds if _seed_id(item)}
    preopen_ids = _collect_values(apply_plan, {"active_sim_priority_seed_ids", "active_seed_id"})
    observed_ids = set().union(
        events.get("active_seed_id", set()),
        events.get("active_sim_priority_seed_id", set()),
        events.get("scalp_sim_active_priority_seed_id", set()),
    )
    rows: list[dict[str, Any]] = []
    source_ids = sorted(catalog_by_id)
    for seed_id in source_ids:
        seed = catalog_by_id.get(seed_id) or {}
        status = str(seed.get("status") or "").strip().lower()
        catalog_present = seed_id in catalog_by_id
        preopen_selected = seed_id in preopen_ids
        observed = seed_id in observed_ids
        if not catalog_present:
            state, blocker = "catalog_missing", "key_lineage_catalog_missing"
        elif observed:
            state, blocker = "matched", ""
        elif status == "cooldown":
            state = "cooldown_intentional" if not preopen_selected else "cooldown_blocks_conversion"
            blocker = "" if state == "cooldown_intentional" else "key_lineage_cooldown_blocks_conversion"
        elif not preopen_selected:
            state, blocker = "preopen_missing", "key_lineage_preopen_missing"
        else:
            state, blocker = "natural_match_0", "runtime_natural_match_0"
        rows.append(
            _row(
                source_key_id=seed_id,
                source_key_type="active_seed",
                source_artifact="scalp_sim_policy_catalog",
                catalog_key_present=catalog_present,
                preopen_policy_selected=preopen_selected,
                runtime_match_key=seed_id if observed else None,
                postclose_observed_key=seed_id if observed else None,
                conversion_state=state,
                next_blocker=blocker,
                evidence={"producer_present": True, "seed_status": status or None},
            )
        )
    for observed_id in sorted(observed_ids - set(catalog_by_id)):
        rows.append(
            _row(
                source_key_id=observed_id,
                source_key_type="active_seed",
                source_artifact="runtime_event",
                catalog_key_present=False,
                preopen_policy_selected=observed_id in preopen_ids,
                runtime_match_key=observed_id,
                postclose_observed_key=observed_id,
                conversion_state="key_mismatch",
                next_blocker="runtime_observed_seed_not_in_catalog",
                evidence={"catalog_seed_count": len(catalog_by_id)},
            )
        )
    return rows


def _swing_rows(*, catalog: dict[str, Any], apply_plan: dict[str, Any], events: dict[str, set[str]]) -> list[dict[str, Any]]:
    policies = [item for item in catalog.get("active_arm_priority_policies") or [] if isinstance(item, dict)]
    catalog_by_id = {_policy_id(item): item for item in policies if _policy_id(item)}
    preopen_ids = _collect_values(apply_plan, {"active_arm_priority_policy_ids", "priority_policy_id"})
    observed_ids = set().union(
        events.get("priority_policy_id", set()),
        events.get("active_arm_priority_policy_id", set()),
        events.get("swing_priority_policy_id", set()),
    )
    rows: list[dict[str, Any]] = []
    for policy_id, policy in sorted(catalog_by_id.items()):
        observed = policy_id in observed_ids
        preopen_selected = policy_id in preopen_ids
        if observed:
            state, blocker = "matched", ""
        elif not preopen_selected:
            state, blocker = "preopen_missing", "swing_active_arm_preopen_missing"
        else:
            state, blocker = "natural_match_0", "swing_active_arm_natural_match_0"
        rows.append(
            _row(
                source_key_id=policy_id,
                source_key_type="active_arm",
                source_artifact="swing_sim_policy_catalog",
                catalog_key_present=True,
                preopen_policy_selected=preopen_selected,
                runtime_match_key=policy_id if observed else None,
                postclose_observed_key=policy_id if observed else None,
                conversion_state=state,
                next_blocker=blocker,
                evidence={"policy_status": policy.get("status") or policy.get("approval_state")},
            )
        )
    for observed_id in sorted(observed_ids - set(catalog_by_id)):
        rows.append(
            _row(
                source_key_id=observed_id,
                source_key_type="active_arm",
                source_artifact="runtime_event",
                catalog_key_present=False,
                preopen_policy_selected=observed_id in preopen_ids,
                runtime_match_key=observed_id,
                postclose_observed_key=observed_id,
                conversion_state="key_mismatch",
                next_blocker="runtime_observed_swing_policy_not_in_catalog",
            )
        )
    return rows


def _hypothesis_rows(
    *,
    plan: dict[str, Any],
    scalp_catalog: dict[str, Any],
    swing_catalog: dict[str, Any],
    refinement: dict[str, Any],
    events: dict[str, set[str]],
) -> list[dict[str, Any]]:
    plan_items = _hypotheses_from_plan(plan)
    plan_by_id = {_hypothesis_id(item): item for item in plan_items if _hypothesis_id(item)}
    catalog_ids = {
        _hypothesis_id(item)
        for item in [*_catalog_hypotheses(scalp_catalog), *_catalog_hypotheses(swing_catalog)]
        if _hypothesis_id(item)
    }
    observed_ids = set().union(events.get("ldm_hypothesis_id", set()), events.get("hypothesis_id", set()))
    refinement_ids = _collect_values(refinement, {"hypothesis_id", "ldm_hypothesis_id", "soft_hypothesis_id"})
    any_instrumented = _event_any_hypothesis_instrumented(events)
    rows: list[dict[str, Any]] = []
    for hypothesis_id, item in sorted(plan_by_id.items()):
        catalog_present = hypothesis_id in catalog_ids
        observed = hypothesis_id in observed_ids or hypothesis_id in refinement_ids
        if not catalog_present:
            state, blocker = "catalog_missing", "hypothesis_catalog_missing"
        elif observed:
            state, blocker = "matched", ""
        elif any_instrumented:
            state, blocker = "natural_match_0", "hypothesis_natural_match_0"
        else:
            state, blocker = "not_instrumented", "hypothesis_runtime_not_instrumented"
        rows.append(
            _row(
                source_key_id=hypothesis_id,
                source_key_type="hypothesis",
                source_artifact=str(plan.get("source_artifact") or "ldm_hypothesis_observation_plan"),
                catalog_key_present=catalog_present,
                preopen_policy_selected=catalog_present,
                runtime_match_key=hypothesis_id if hypothesis_id in observed_ids else None,
                postclose_observed_key=hypothesis_id if hypothesis_id in refinement_ids else None,
                conversion_state=state,
                next_blocker=blocker,
                evidence={
                    "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
                    "parent_bucket_id": item.get("parent_bucket_id") or item.get("hypothesis_parent_bucket_id"),
                },
            )
        )
    return rows


def _bucket_state(item: dict[str, Any]) -> str:
    contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
    return str(
        item.get("classification_state")
        or item.get("review_sub_state")
        or contract.get("state")
        or ""
    ).strip()


def _bucket_identity(item: dict[str, Any]) -> str:
    return str(item.get("source_bucket_id") or item.get("bucket_id") or item.get("source_key_id") or "").strip()


def _iter_bucket_items(payload: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        if _bucket_identity(payload) and (_bucket_state(payload) or payload.get("source_bucket_kind")):
            items.append(payload)
        for value in payload.values():
            items.extend(_iter_bucket_items(value))
    elif isinstance(payload, list):
        for value in payload:
            items.extend(_iter_bucket_items(value))
    return items


def _bucket_rows(
    discovery: dict[str, Any],
    *,
    scalp_catalog: dict[str, Any],
    events: dict[str, set[str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    matched_source_ids = events.get("lifecycle_bucket_matched_source_bucket_id", set())
    matched_bucket_ids = events.get("lifecycle_bucket_matched_bucket_id", set())
    runtime_source_ids = events.get("lifecycle_bucket_source_bucket_id", set())
    runtime_bucket_ids = events.get("lifecycle_bucket_bucket_id", set())
    candidates: list[tuple[dict[str, Any], str, bool]] = []
    seen: set[str] = set()
    for item in _iter_bucket_items(scalp_catalog):
        source_id = _bucket_identity(item)
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        candidates.append((item, "scalp_sim_policy_catalog", True))
    for section in ("live_auto_apply_candidates", "sim_auto_approved_candidates", "surfaced_candidates"):
        for item in discovery.get(section) or []:
            if not isinstance(item, dict):
                continue
            source_id = _bucket_identity(item)
            if not source_id or source_id in seen:
                continue
            seen.add(source_id)
            candidates.append((item, "lifecycle_bucket_discovery", False))
    for item, source_artifact, preopen_from_catalog in candidates:
        if not isinstance(item, dict):
            continue
        candidate_id = _bucket_identity(item)
        if not candidate_id:
            continue
        state = _bucket_state(item)
        bucket_id = str(item.get("bucket_id") or "").strip()
        observed = preopen_from_catalog and (candidate_id in matched_source_ids or bucket_id in matched_bucket_ids)
        runtime_seen = preopen_from_catalog and (candidate_id in runtime_source_ids or bucket_id in runtime_bucket_ids)
        if observed:
            conversion_state, blocker = "matched", ""
        elif preopen_from_catalog and runtime_seen:
            conversion_state, blocker = "natural_match_0", "lifecycle_bucket_runtime_no_match"
        elif preopen_from_catalog:
            conversion_state, blocker = "natural_match_0", "lifecycle_bucket_natural_match_0"
        elif state == "live_auto_apply_ready":
            conversion_state, blocker = "bridge_blocked", "bridge_contract"
        elif state in {"sim_auto_approved", "entry_only_sim_auto_approved", "lifecycle_flow_sim_probe_candidate"}:
            conversion_state, blocker = "collecting", "sample_floor"
        elif str(item.get("source_dimension_gap") or ""):
            conversion_state, blocker = "source_quality_blocked", "source_quality"
        else:
            conversion_state, blocker = "collecting", "sample_floor"
        rows.append(
            _row(
                source_key_id=candidate_id,
                source_key_type="bucket",
                source_artifact=source_artifact,
                catalog_key_present=True,
                preopen_policy_selected=preopen_from_catalog
                or state in {"sim_auto_approved", "entry_only_sim_auto_approved", "lifecycle_flow_sim_probe_candidate"},
                runtime_match_key=candidate_id if observed else None,
                postclose_observed_key=candidate_id if observed else None,
                conversion_state=conversion_state,
                next_blocker=blocker,
                evidence={
                    "classification_state": state,
                    "primary_ev": item.get("primary_ev"),
                    "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
                    "sample": item.get("sample"),
                    "bucket_id": bucket_id or None,
                    "source_bucket_kind": item.get("source_bucket_kind"),
                    "runtime_seen": runtime_seen,
                },
            )
        )
    return rows


def build_key_lineage_ledger(target_date: str) -> dict[str, Any]:
    discovery_path = DATA_DIR / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json"
    refinement_path = DATA_DIR / "report" / "ldm_hypothesis_parent_refinement" / f"ldm_hypothesis_parent_refinement_{target_date}.json"
    apply_path = _runtime_apply_path(target_date)
    apply_plan = _load_json(apply_path)
    apply_source_date = _apply_source_date(apply_plan, target_date)
    scalp_catalog_path = _catalog_path_from_apply(
        apply_plan,
        section_key="scalp_sim_auto_approval",
        env_key="KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE",
        default_dir=SCALP_POLICY_DIR,
        default_prefix="scalp_sim_policy_catalog",
        target_date=target_date,
    )
    swing_catalog_path = _catalog_path_from_apply(
        apply_plan,
        section_key="swing_sim_auto_approval",
        env_key="KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE",
        default_dir=SWING_POLICY_DIR,
        default_prefix="swing_sim_policy_catalog",
        target_date=target_date,
    )
    hypothesis_plan_path = _latest_hypothesis_plan_path(target_date)
    discovery = _load_json(discovery_path)
    refinement = _load_json(refinement_path)
    scalp_catalog = _load_json(scalp_catalog_path)
    swing_catalog = _load_json(swing_catalog_path)
    hypothesis_plan = _load_json(hypothesis_plan_path)
    events = _event_field_values(target_date)

    rows: list[dict[str, Any]] = []
    rows.extend(_scalp_rows(discovery=discovery, catalog=scalp_catalog, apply_plan=apply_plan, events=events))
    rows.extend(_swing_rows(catalog=swing_catalog, apply_plan=apply_plan, events=events))
    rows.extend(
        _hypothesis_rows(
            plan=hypothesis_plan,
            scalp_catalog=scalp_catalog,
            swing_catalog=swing_catalog,
            refinement=refinement,
            events=events,
        )
    )
    rows.extend(_bucket_rows(discovery, scalp_catalog=scalp_catalog, events=events))
    state_counts = Counter(str(row.get("conversion_state") or "unknown") for row in rows)
    continuity_pass_count = sum(1 for row in rows if row.get("same_key_continuity") == "pass")
    positive_ev_runtime_observed_count = sum(
        1 for row in rows if row.get("positive_ev_candidate") and row.get("runtime_observed_same_key")
    )
    positive_ev_sample_floor_blocked_count = sum(
        1 for row in rows if row.get("positive_ev_candidate") and row.get("next_blocker") == "sample_floor"
    )
    blockers = []
    for row in rows:
        state = str(row.get("conversion_state") or "")
        if state not in LINEAGE_BLOCKER_STATES:
            continue
        blockers.append(
            {
                "blocker_id": _stable_id("lineage_blocker", row),
                "blocker_class": "key_lineage",
                "source_key_id": row.get("source_key_id"),
                "source_key_type": row.get("source_key_type"),
                "conversion_state": state,
                "next_repair_action": row.get("next_blocker") or "repair_key_lineage",
                "acceptance_test": "same source_key_id is present in catalog, preopen, runtime, and postclose ledger or closes as natural_match_0",
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "conversion_lineage_observation_only",
        "sources": {
            "lifecycle_bucket_discovery": str(discovery_path),
            "scalp_sim_policy_catalog": str(scalp_catalog_path),
            "swing_sim_policy_catalog": str(swing_catalog_path),
            "threshold_preopen_apply_next": str(apply_path),
            "ldm_hypothesis_observation_plan": str(hypothesis_plan_path),
            "ldm_hypothesis_parent_refinement": str(refinement_path),
        },
        "summary": {
            "runtime_observation_target_date": target_date,
            "runtime_policy_source_date": apply_source_date,
            "postclose_candidate_source_date": target_date,
            "runtime_policy_matches_postclose_candidate_source": apply_source_date == target_date,
            "new_postclose_candidates_due_state": (
                "due_same_day"
                if apply_source_date == target_date
                else "not_due_until_next_preopen"
            ),
            "source_key_count": len(rows),
            "same_key_continuity_pass_count": continuity_pass_count,
            "bucket_same_key_continuity_pass_count": sum(
                1
                for row in rows
                if row.get("source_key_type") == "bucket" and row.get("same_key_continuity") == "pass"
            ),
            "key_mismatch_count": state_counts.get("key_mismatch", 0),
            "catalog_missing_count": state_counts.get("catalog_missing", 0),
            "preopen_missing_count": state_counts.get("preopen_missing", 0),
            "not_instrumented_count": state_counts.get("not_instrumented", 0),
            "natural_match_0_count": state_counts.get("natural_match_0", 0),
            "cooldown_intentional_count": state_counts.get("cooldown_intentional", 0),
            "lineage_blocker_count": len(blockers),
            "positive_ev_runtime_observed_count": positive_ev_runtime_observed_count,
            "positive_ev_sample_floor_blocked_count": positive_ev_sample_floor_blocked_count,
            "state_counts": dict(state_counts),
        },
        "lineage_rows": rows,
        "lineage_blockers": blockers,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Key Lineage Ledger - {report.get('date')}",
        "",
        "## Decision",
        f"- source keys: `{summary.get('source_key_count', 0)}`",
        f"- runtime observation target date: `{summary.get('runtime_observation_target_date') or '-'}`",
        f"- runtime policy source date: `{summary.get('runtime_policy_source_date') or '-'}`",
        f"- postclose candidate source date: `{summary.get('postclose_candidate_source_date') or '-'}`",
        f"- new postclose candidate due state: `{summary.get('new_postclose_candidates_due_state') or '-'}`",
        f"- same-key continuity pass: `{summary.get('same_key_continuity_pass_count', 0)}`",
        f"- positive EV runtime observed: `{summary.get('positive_ev_runtime_observed_count', 0)}`",
        f"- positive EV sample-floor blocked: `{summary.get('positive_ev_sample_floor_blocked_count', 0)}`",
        f"- blockers: mismatch=`{summary.get('key_mismatch_count', 0)}`, catalog_missing=`{summary.get('catalog_missing_count', 0)}`, preopen_missing=`{summary.get('preopen_missing_count', 0)}`, not_instrumented=`{summary.get('not_instrumented_count', 0)}`",
        "",
        "## Top Blockers",
    ]
    blockers = report.get("lineage_blockers") if isinstance(report.get("lineage_blockers"), list) else []
    if blockers:
        for item in blockers[:20]:
            lines.append(
                f"- `{item.get('source_key_id')}` ({item.get('source_key_type')}): {item.get('conversion_state')} -> {item.get('next_repair_action')}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def write_key_lineage_ledger(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build key lineage ledger")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_key_lineage_ledger(args.date)
    json_path, md_path = write_key_lineage_ledger(report)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
