"""Build conversion lane and blocker rank for sim-to-real compression."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.automation.key_lineage_ledger import build_key_lineage_ledger, report_paths as key_lineage_paths
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
    if "submit_drought" in text or "latency_pre_submit" in text or "budget_pass" in text:
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
    if "safety" in text or "broker" in text or "stale" in text or "quantity" in text or "cooldown" in text:
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


def _candidate_from_lifecycle(item: dict[str, Any], strategy_scope: str) -> dict[str, Any]:
    candidate_id = str(item.get("bucket_id") or _hash("candidate", item))
    source_key_id = str(item.get("source_bucket_id") or candidate_id)
    state = str(item.get("classification_state") or "source_only_keep_collecting")
    source_gap = str(item.get("source_dimension_gap") or "")
    bridge_state = "ready" if state == "live_auto_apply_ready" else "not_ready"
    source_quality_state = "blocked" if source_gap else "pass"
    sample = _safe_int(item.get("sample"))
    ev = _safe_float(item.get("source_quality_adjusted_ev_pct") or item.get("equal_weight_avg_profit_pct"))
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
        "parent_bucket_id": item.get("parent_bucket_id") or f"{item.get('stage')}:{item.get('bucket_type')}",
        "primary_ev": ev,
        "sample": sample,
        "source_quality_state": source_quality_state,
        "sim_policy_state": state,
        "runtime_observation_state": "not_checked",
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


def _candidate_from_matched_bucket_lineage(row: dict[str, Any]) -> dict[str, Any] | None:
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    source_key_id = str(row.get("source_key_id") or "").strip()
    if not source_key_id or row.get("source_key_type") != "bucket":
        return None
    if row.get("same_key_continuity") != "pass":
        return None
    ev = _safe_float(evidence.get("primary_ev"))
    sample = _safe_int(evidence.get("sample"))
    return {
        "candidate_id": source_key_id,
        "strategy_scope": "scalp",
        "source_key_type": "bucket",
        "source_key_id": source_key_id,
        "parent_bucket_id": evidence.get("bucket_id") or source_key_id.rsplit(":", 1)[0],
        "primary_ev": ev,
        "sample": sample,
        "source_quality_state": "pass",
        "sim_policy_state": str(evidence.get("classification_state") or "runtime_applied_bucket_policy"),
        "runtime_observation_state": "matched",
        "bridge_state": "not_ready",
        "conversion_state": "runtime_observed",
        "next_blocker": "sample_floor",
        "evidence": {
            "source_artifact": row.get("source_artifact"),
            "bucket_id": evidence.get("bucket_id"),
            "source_bucket_kind": evidence.get("source_bucket_kind"),
        },
    }


def _candidates_from_lifecycle(discovery: dict[str, Any], strategy_scope: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in ("live_auto_apply_candidates", "sim_auto_approved_candidates", "surfaced_candidates"):
        for item in discovery.get(section) or []:
            if not isinstance(item, dict):
                continue
            row = _candidate_from_lifecycle(item, strategy_scope)
            if row["candidate_id"] in seen:
                continue
            seen.add(row["candidate_id"])
            candidates.append(row)
    return candidates


def _candidate_from_runtime_gap(row: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(row.get("candidate_id") or _hash("runtime_gap", row))
    derived = str(row.get("derived_review_category") or row.get("final_disposition") or "")
    blocker = _blocker_class(str(row.get("failure_reason") or row.get("recommended_resolution") or derived), row)
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
        "runtime_observation_state": str(row.get("preopen_apply_state") or "not_checked"),
        "bridge_state": str(row.get("bridge_state") or "not_checked"),
        "conversion_state": "bridge_contract_ready" if row.get("bridge_state") == "joined" else "discovered",
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
    if blocker in {"source_quality", "bridge_contract", "key_lineage", "submit_drought"}:
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
    impact = max(1, rank_seed - int(ev * 10) - min(sample, 20) + fix_difficulty * 5 + remaining_gap_count * 3)
    return {
        "blocker_id": _hash("conversion_blocker", [candidate_id, blocker, reason]),
        "conversion_candidate_id": candidate_id,
        "blocker_class": blocker,
        "conversion_impact_rank": impact,
        "ev_potential_rank": 1 if ev > 0 else 5,
        "sample_readiness_rank": 1 if sample >= 10 else 2 if sample >= 3 else 4,
        "fix_difficulty_rank": fix_difficulty,
        "remaining_gap_count": remaining_gap_count,
        "next_repair_action": reason or f"close_{blocker}",
        "acceptance_test": _acceptance_test(blocker),
    }


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
    classification = buy_funnel.get("classification") if isinstance(buy_funnel.get("classification"), dict) else {}
    matches = classification.get("matches") if isinstance(classification.get("matches"), list) else []
    critical = classification.get("primary") == "SUBMIT_DROUGHT_CRITICAL" or "SUBMIT_DROUGHT_CRITICAL" in matches
    if not critical:
        return []
    closure_items = [
        "LATENCY_PRE_SUBMIT",
        "BROKER_RECEIPT",
        "BUDGET_PASS_COLLAPSE",
        "SIM_REAL_AUTHORITY",
        "SOURCE_TAXONOMY_LEAKAGE",
        "UPSTREAM_GATE",
    ]
    return [
        _conversion_blocker(
            candidate_id=f"submit_drought:{item}",
            blocker_class="submit_drought",
            reason=f"close_submit_drought_{item.lower()}",
            rank_seed=30,
        )
        for item in closure_items
    ]


def _lineage_handoff_rows(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = ledger.get("lineage_rows") if isinstance(ledger.get("lineage_rows"), list) else []
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
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        count = _safe_int(summary.get("candidate_count") or summary.get("approved_count") or summary.get("positive_source_count"))
        if count <= 0:
            continue
        candidates.append(
            {
                "candidate_id": f"swing_bottom_rebound:{directory.name}",
                "strategy_scope": "swing",
                "source_key_type": "hypothesis",
                "source_key_id": "bottom_rebound",
                "parent_bucket_id": "bottom_rebound",
                "primary_ev": _safe_float(summary.get("source_quality_adjusted_ev_pct")),
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
    lifecycle = _load_json(DATA_DIR / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json")
    swing_lifecycle = _load_json(
        DATA_DIR / "report" / "swing_lifecycle_bucket_discovery" / f"swing_lifecycle_bucket_discovery_{target_date}.json"
    )
    runtime_gap = _load_json(DATA_DIR / "report" / "runtime_apply_gap_audit" / f"runtime_apply_gap_audit_{target_date}.json")
    buy_funnel = _load_json(DATA_DIR / "report" / "buy_funnel_sentinel" / f"buy_funnel_sentinel_{target_date}.json")

    candidates = _candidates_from_lifecycle(lifecycle, "scalp")
    candidates.extend(_candidates_from_lifecycle(swing_lifecycle, "swing"))
    seen = {item["candidate_id"] for item in candidates}
    for row in runtime_gap.get("candidate_route_ledger") or []:
        if not isinstance(row, dict):
            continue
        candidate = _candidate_from_runtime_gap(row)
        if candidate["candidate_id"] in seen:
            continue
        if candidate.get("primary_ev") is not None or candidate.get("next_blocker") in {"source_quality", "bridge_contract"}:
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
        candidates.append(candidate)
        seen.add(candidate["candidate_id"])

    blockers: list[dict[str, Any]] = []
    for candidate in candidates:
        blocker_class = _blocker_class(str(candidate.get("next_blocker") or ""), candidate)
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
    blockers.extend(_submit_drought_blockers(buy_funnel))
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
        if isinstance(row, dict) and row.get("same_key_continuity") == "pass" and row.get("source_key_id")
    }
    real_queue = [
        item
        for item in candidates
        if item.get("source_quality_state") == "pass"
        and (_safe_float(item.get("primary_ev"), 0.0) or 0.0) > 0
        and (
            item.get("conversion_state") == "bounded_real_canary_requestable"
            or str(item.get("source_key_id") or item.get("candidate_id")) in continuity_pass_ids
        )
        and item.get("conversion_state") in {
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
            "excluded_from_real_queue_reason": row.get("next_blocker") or "observation_priority_only",
        }
        for row in key_ledger.get("lineage_rows") or []
        if isinstance(row, dict)
        and str(row.get("source_key_type") or "") in {"active_seed", "active_arm", "hypothesis"}
        and str(row.get("conversion_state") or "") != "matched"
    ]
    blocker_counts = Counter(str(item.get("blocker_class") or "unknown") for item in blockers)
    summary = {
        "conversion_candidate_count": len(candidates),
        "bounded_real_canary_requestable_count": sum(
            1 for item in candidates if item.get("conversion_state") == "bounded_real_canary_requestable"
        ),
        "top_blocker_class": blockers[0]["blocker_class"] if blockers else None,
        "scalp_conversion_candidate_count": sum(1 for item in candidates if item.get("strategy_scope") == "scalp"),
        "swing_conversion_candidate_count": sum(1 for item in candidates if item.get("strategy_scope") == "swing"),
        "sim_priority_only_count": len(sim_priority_only),
        "key_lineage_blocker_count": _safe_int((key_ledger.get("summary") or {}).get("lineage_blocker_count")),
        "real_conversion_queue_count": len(real_queue),
        "blocker_class_counts": dict(blocker_counts),
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
    blockers = report.get("conversion_blocker_rank") if isinstance(report.get("conversion_blocker_rank"), list) else []
    queue = report.get("real_conversion_queue") if isinstance(report.get("real_conversion_queue"), list) else []
    lines = [
        f"# Conversion Lane - {report.get('date')}",
        "",
        "## Decision",
        f"- conversion candidates: `{summary.get('conversion_candidate_count', 0)}`",
        f"- real conversion queue: `{summary.get('real_conversion_queue_count', 0)}`",
        f"- bounded real canary requestable: `{summary.get('bounded_real_canary_requestable_count', 0)}`",
        f"- top blocker: `{summary.get('top_blocker_class') or 'none'}`",
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
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build conversion lane")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_conversion_lane(args.date)
    json_path, md_path = write_conversion_lane(report)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
