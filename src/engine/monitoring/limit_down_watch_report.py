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


def build_report(target_date: str, *, event_path: Path | None = None) -> dict[str, Any]:
    event_path = event_path or (
        DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    )
    events = _load_events(event_path)
    snapshots: dict[str, dict[str, Any]] = {}
    transitions: dict[str, list[str]] = defaultdict(list)
    registered_codes = set()
    for event in events:
        code = str(event.get("stock_code") or "").strip()
        stage = str(event.get("stage") or "")
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if stage == "limit_down_watch_registered" and code:
            registered_codes.add(code)
        elif stage == "limit_down_watch_state_transition" and code:
            transitions[code].append(str(fields.get("phase") or ""))
        elif stage == "limit_down_watch_snapshot" and code:
            snapshots[code] = fields

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for code, fields in snapshots.items():
        key = (
            str(fields.get("cohort") or "unknown"),
            str(fields.get("price_band") or "unknown"),
        )
        row = grouped.setdefault(
            key,
            {
                "cohort": key[0],
                "price_band": key[1],
                "observed_codes": 0,
                "unlocked_codes": 0,
                "relocked_codes": 0,
                "ordered_path_captured_codes": 0,
                "_ranges": [],
                "_highs": [],
                "_lows": [],
            },
        )
        row["observed_codes"] += 1
        phases = transitions.get(code, [])
        unlocked = any(phase in {"UNLOCKED", "UNLOCKED_AGAIN"} for phase in phases)
        relocked = "RELOCKED" in phases
        if unlocked:
            row["unlocked_codes"] += 1
        if relocked:
            row["relocked_codes"] += 1
        if phases:
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
        count = row["observed_codes"]
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
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "pass" if snapshots else "no_observation",
        "registered_code_count": len(registered_codes),
        "snapshot_code_count": len(snapshots),
        "group_count": len(groups),
        "groups": groups,
        **CONTRACT,
    }


def write_report(target_date: str) -> Path:
    payload = build_report(target_date)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"limit_down_watch_{target_date}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build_report(args.target_date)
    if args.write:
        print(write_report(args.target_date))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
