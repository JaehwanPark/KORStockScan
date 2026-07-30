"""Build a source-only postclose report for limit-down raw-tick observations."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "report" / "limit_down_watch"
CANDIDATE_DIR = DATA_DIR / "report" / "limit_down_watch_candidate_source"

CONTRACT = {
    "metric_role": "diagnostic",
    "decision_authority": "limit_down_source_observation_only",
    "window_policy": "same_symbol_same_krx_session_ordered_raw_tick",
    "sample_floor": "not_applicable_source_observation",
    "primary_decision_metric": "ordered_intraday_path_capture_rate",
    "source_quality_gate": "official_ka10017_and_completed_ka10081_db_close_match",
    "forbidden_uses": (
        "real_order,buy_analysis,threshold_change,provider_route_change,"
        "order_price_or_quantity_change,cap_change,broker_guard_change,"
        "bot_restart_authority"
    ),
    "runtime_effect": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "allowed_sim_apply": False,
    "allowed_runtime_apply": False,
}


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_events(path: Path) -> list[dict[str, Any]]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("pipeline") == "LIMIT_DOWN_WATCH":
            rows.append(row)
    return rows


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _evidence_readiness(
    *,
    target_date: str,
    candidate_source: dict[str, Any],
    registered_code_count: int,
    snapshot_code_count: int,
    ordered_path_captured_code_count: int,
) -> dict[str, Any]:
    candidates = (
        candidate_source.get("candidates")
        if isinstance(candidate_source.get("candidates"), list)
        else []
    )
    source_pass_count = sum(
        1
        for row in candidates
        if isinstance(row, dict) and row.get("source_quality") == "pass"
    )
    candidate_source_valid = (
        candidate_source.get("report_type") == "limit_down_watch_candidate_source"
        and candidate_source.get("target_date") == target_date
        and candidate_source.get("status") in {"pass", "partial"}
    )
    if not candidate_source:
        source_quality_status = "missing"
    elif not candidate_source_valid:
        source_quality_status = "stale_or_invalid"
    elif source_pass_count != len(candidates):
        source_quality_status = "blocked"
    elif candidate_source.get("status") == "partial":
        source_quality_status = "pass_with_exclusions"
    elif candidates:
        source_quality_status = "pass"
    else:
        source_quality_status = "no_candidate"
    blockers = []
    if source_quality_status not in {"pass", "pass_with_exclusions", "no_candidate"}:
        blockers.append(f"candidate_source_quality_{source_quality_status}")
    if snapshot_code_count <= 0:
        blockers.append("ordered_intraday_path_sample_missing")
    if ordered_path_captured_code_count <= 0:
        blockers.append("ordered_intraday_path_capture_missing")
    elif ordered_path_captured_code_count < registered_code_count:
        blockers.append("ordered_intraday_path_capture_incomplete")
    blockers.extend(
        [
            "multi_day_cohort_sample_floor_not_established",
            "counterfactual_entry_exit_labels_missing",
            "clean_baseline_rolling_ev_missing",
            "sim_policy_catalog_handoff_missing",
            "post_sim_attribution_missing",
            "separate_live_conversion_approval_missing",
        ]
    )
    return {
        "stage": "source_observation",
        "decision": "collect_source_then_build_sim_candidate",
        "source_quality_status": source_quality_status,
        "candidate_source_valid": candidate_source_valid,
        "candidate_source_report_status": candidate_source.get("status"),
        "candidate_count": len(candidates),
        "source_pass_count": source_pass_count,
        "registered_code_count": registered_code_count,
        "snapshot_code_count": snapshot_code_count,
        "ordered_path_captured_code_count": ordered_path_captured_code_count,
        "sim_candidate_ready": False,
        "real_trading_ready": False,
        "blockers": blockers,
        "required_next_evidence": [
            "multi_day_cohort_and_price_band_sample_floor",
            "ordered_unlock_relock_path_capture",
            "counterfactual_entry_exit_labels_with_mfe_mae",
            "clean_baseline_rolling_source_quality_adjusted_ev_pct",
            "sim_policy_catalog_and_preopen_handoff",
            "post_sim_attribution",
            "separate_operator_live_conversion_approval_and_rollback",
        ],
    }


def build_report(
    target_date: str,
    *,
    event_path: Path | None = None,
    candidate_path: Path | None = None,
) -> dict[str, Any]:
    event_path = event_path or (
        DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    )
    candidate_path = candidate_path or (
        CANDIDATE_DIR / f"limit_down_watch_candidate_source_{target_date}.json"
    )
    events = _load_events(event_path)
    candidate_source = _load_json(candidate_path)
    snapshots: dict[str, dict[str, Any]] = {}
    transitions: dict[str, list[str]] = defaultdict(list)
    registered_meta: dict[str, dict[str, Any]] = {}
    for event in events:
        code = str(event.get("stock_code") or "").strip()
        stage = str(event.get("stage") or "")
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if stage == "limit_down_watch_registered" and code:
            registered_meta[code] = {
                "cohort": fields.get("cohort"),
                "price_band": fields.get("price_band"),
            }
        elif stage == "limit_down_watch_state_transition" and code:
            transitions[code].append(str(fields.get("phase") or ""))
        elif stage == "limit_down_watch_snapshot" and code:
            snapshots[code] = fields

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    report_codes = sorted(set(registered_meta) | set(snapshots))
    ordered_phases = {"LIMIT_LOCKED", "UNLOCKED", "RELOCKED", "UNLOCKED_AGAIN"}
    for code in report_codes:
        fields = snapshots.get(code) or registered_meta.get(code) or {}
        key = (
            str(fields.get("cohort") or "unknown"),
            str(fields.get("price_band") or "unknown"),
        )
        row = grouped.setdefault(
            key,
            {
                "cohort": key[0],
                "price_band": key[1],
                "registered_codes": 0,
                "snapshot_codes": 0,
                "observed_codes": 0,
                "unlocked_codes": 0,
                "relocked_codes": 0,
                "ordered_path_captured_codes": 0,
                "_ranges": [],
                "_highs": [],
                "_lows": [],
            },
        )
        if code in registered_meta:
            row["registered_codes"] += 1
        if code in snapshots:
            row["snapshot_codes"] += 1
            row["observed_codes"] += 1
        phases = transitions.get(code, [])
        unlocked = any(phase in {"UNLOCKED", "UNLOCKED_AGAIN"} for phase in phases)
        relocked = "RELOCKED" in phases
        if unlocked:
            row["unlocked_codes"] += 1
        if relocked:
            row["relocked_codes"] += 1
        if any(phase in ordered_phases for phase in phases):
            row["ordered_path_captured_codes"] += 1
        intraday_range = _safe_float(fields.get("low_to_high_range_pct"))
        high_vs_close = _safe_float(fields.get("high_vs_limit_down_close_pct"))
        low_vs_close = _safe_float(fields.get("low_vs_limit_down_close_pct"))
        if intraday_range is not None:
            row["_ranges"].append(intraday_range)
        if high_vs_close is not None:
            row["_highs"].append(high_vs_close)
        if low_vs_close is not None:
            row["_lows"].append(low_vs_close)

    groups = []
    for row in grouped.values():
        count = max(row["registered_codes"], row["snapshot_codes"])
        ranges = row.pop("_ranges")
        highs = row.pop("_highs")
        lows = row.pop("_lows")
        row.update(
            {
                "unlock_rate_pct": (
                    round(row["unlocked_codes"] / count * 100.0, 4) if count else None
                ),
                "relock_rate_pct": (
                    round(row["relocked_codes"] / count * 100.0, 4) if count else None
                ),
                "ordered_intraday_path_capture_rate": (
                    round(row["ordered_path_captured_codes"] / count * 100.0, 4)
                    if count
                    else None
                ),
                "avg_low_to_high_range_pct": (
                    round(sum(ranges) / len(ranges), 6) if ranges else None
                ),
                "avg_high_vs_limit_down_close_pct": (
                    round(sum(highs) / len(highs), 6) if highs else None
                ),
                "avg_low_vs_limit_down_close_pct": (
                    round(sum(lows) / len(lows), 6) if lows else None
                ),
            }
        )
        groups.append(row)
    groups.sort(key=lambda row: (row["cohort"], row["price_band"]))
    ordered_path_captured_code_count = sum(
        int(row["ordered_path_captured_codes"]) for row in groups
    )
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "pass" if snapshots else "no_observation",
        "registered_code_count": len(registered_meta),
        "snapshot_code_count": len(snapshots),
        "group_count": len(groups),
        "groups": groups,
        "candidate_source_path": str(candidate_path),
        "event_source_path": str(event_path),
        "evidence_readiness": _evidence_readiness(
            target_date=target_date,
            candidate_source=candidate_source,
            registered_code_count=len(registered_meta),
            snapshot_code_count=len(snapshots),
            ordered_path_captured_code_count=ordered_path_captured_code_count,
        ),
        **CONTRACT,
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    readiness = (
        payload.get("evidence_readiness")
        if isinstance(payload.get("evidence_readiness"), dict)
        else {}
    )
    lines = [
        f"# Limit-Down Watch Report — {payload.get('target_date')}",
        "",
        f"- status: `{payload.get('status')}`",
        f"- registered_code_count: `{payload.get('registered_code_count')}`",
        f"- snapshot_code_count: `{payload.get('snapshot_code_count')}`",
        (
            "- ordered_intraday_path_capture: "
            f"`{readiness.get('ordered_path_captured_code_count', 0)}`"
        ),
        f"- sim_candidate_ready: `{readiness.get('sim_candidate_ready')}`",
        f"- real_trading_ready: `{readiness.get('real_trading_ready')}`",
        f"- decision: `{readiness.get('decision')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = (
        readiness.get("blockers") if isinstance(readiness.get("blockers"), list) else []
    )
    lines.extend(f"- `{item}`" for item in blockers)
    lines.extend(
        [
            "",
            "## Contract",
            "",
            f"- decision_authority: `{payload.get('decision_authority')}`",
            f"- runtime_effect: `{payload.get('runtime_effect')}`",
            f"- actual_order_submitted: `{payload.get('actual_order_submitted')}`",
            f"- broker_order_forbidden: `{payload.get('broker_order_forbidden')}`",
            f"- allowed_sim_apply: `{payload.get('allowed_sim_apply')}`",
            f"- allowed_runtime_apply: `{payload.get('allowed_runtime_apply')}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(target_date: str) -> tuple[Path, Path]:
    payload = build_report(target_date)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUTPUT_DIR / f"limit_down_watch_{target_date}"
    json_path = base.with_suffix(".json")
    markdown_path = base.with_suffix(".md")
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build_report(args.target_date)
    if args.write:
        json_path, markdown_path = write_report(args.target_date)
        print(json_path)
        print(markdown_path)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
