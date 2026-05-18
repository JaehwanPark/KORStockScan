"""Recommend next-preopen latency classifier thresholds from pipeline events."""

from __future__ import annotations

import argparse
import gzip
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.utils.constants import DATA_DIR


PIPELINE_EVENT_DIR = DATA_DIR / "pipeline_events"
REPORT_DIR = DATA_DIR / "report" / "latency_classifier_recommendation"

FAMILY = "latency_classifier_runtime_profile"
STAGE = "entry_latency_classifier"
TARGET_ENV_KEYS = [
    "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION",
    "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION",
    "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION",
]
DEFAULT_CURRENT_VALUES = {
    "max_ws_age_ms_for_caution": 700,
    "max_ws_jitter_ms_for_caution": 300,
    "max_spread_ratio_for_caution": 0.005,
}
SYNTHETIC_CODES = {"123456", "000000", "-", ""}
SYNTHETIC_NAMES = {"TEST", "DUMMY", "MOCK"}


@dataclass(frozen=True)
class ThresholdProfile:
    profile_id: str
    max_ws_age_ms_for_caution: int
    max_ws_jitter_ms_for_caution: int
    max_spread_ratio_for_caution: float


PROFILES = [
    ThresholdProfile("current_700_300_0050", 700, 300, 0.0050),
    ThresholdProfile("quote_fresh_950_450_0075", 950, 450, 0.0075),
    ThresholdProfile("mechanical_1200_500_0085", 1200, 500, 0.0085),
    ThresholdProfile("balanced_1200_1500_0100", 1200, 1500, 0.0100),
    ThresholdProfile("loose_age_1500_1500_0100", 1500, 1500, 0.0100),
]
RECOMMENDED_PROFILE_ID = "balanced_1200_1500_0100"


def report_json_path(target_date: str) -> Path:
    return REPORT_DIR / f"latency_classifier_recommendation_{target_date}.json"


def report_md_path(target_date: str) -> Path:
    return REPORT_DIR / f"latency_classifier_recommendation_{target_date}.md"


def _event_source_path(target_date: str) -> Path:
    plain = PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl"
    if plain.exists():
        return plain
    gz = PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl.gz"
    return gz


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _to_float(value: Any) -> float | None:
    if value in {None, "", "-"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_synthetic(event: dict[str, Any]) -> bool:
    code = str(event.get("stock_code") or "").strip().zfill(6)
    name = str(event.get("stock_name") or "").strip().upper()
    if code in SYNTHETIC_CODES:
        return True
    return any(token in name for token in SYNTHETIC_NAMES)


def _latency_block_events(target_date: str, *, source_path: Path | None = None) -> list[dict[str, Any]]:
    path = source_path or _event_source_path(target_date)
    events: list[dict[str, Any]] = []
    for event in _read_jsonl(path):
        if event.get("pipeline") != "ENTRY_PIPELINE" or event.get("stage") != "latency_block":
            continue
        if _is_synthetic(event):
            continue
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        ws_age_ms = _to_float(fields.get("ws_age_ms"))
        ws_jitter_ms = _to_float(fields.get("ws_jitter_ms"))
        spread_ratio = _to_float(fields.get("spread_ratio"))
        if ws_age_ms is None or ws_jitter_ms is None or spread_ratio is None:
            continue
        events.append(
            {
                "stock_code": str(event.get("stock_code") or "").strip(),
                "stock_name": event.get("stock_name"),
                "record_id": event.get("record_id"),
                "ws_age_ms": ws_age_ms,
                "ws_jitter_ms": ws_jitter_ms,
                "spread_ratio": spread_ratio,
                "quote_stale": str(fields.get("quote_stale") or "").lower() == "true",
                "latency": fields.get("latency"),
                "decision": fields.get("decision"),
                "latency_danger_reasons": fields.get("latency_danger_reasons"),
            }
        )
    return events


def _profile_result(profile: ThresholdProfile, events: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [
        event
        for event in events
        if event["ws_age_ms"] <= profile.max_ws_age_ms_for_caution
        and event["ws_jitter_ms"] <= profile.max_ws_jitter_ms_for_caution
        and event["spread_ratio"] <= profile.max_spread_ratio_for_caution
    ]
    unique_codes = {str(event.get("stock_code") or "") for event in passed if event.get("stock_code")}
    total = len(events)
    return {
        "profile_id": profile.profile_id,
        "max_ws_age_ms_for_caution": profile.max_ws_age_ms_for_caution,
        "max_ws_jitter_ms_for_caution": profile.max_ws_jitter_ms_for_caution,
        "max_spread_ratio_for_caution": profile.max_spread_ratio_for_caution,
        "would_pass_events": len(passed),
        "would_pass_unique_codes": len(unique_codes),
        "would_pass_ratio": round(len(passed) / total, 6) if total else 0.0,
    }


def _build_candidate(target_date: str, profile: dict[str, Any], total_events: int) -> dict[str, Any]:
    sample_floor = 20
    pass_floor = max(10, int(total_events * 0.20))
    pass_count = int(profile.get("would_pass_events") or 0)
    eligible = total_events >= sample_floor and pass_count >= pass_floor
    state = "adjust_up" if eligible else "hold_sample"
    reason = (
        f"latency_block_profile_pass_count={pass_count}>=floor={pass_floor}"
        if eligible
        else f"sample_or_pass_floor_not_met latency_blocks={total_events} pass_count={pass_count} floor={pass_floor}"
    )
    return {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 6,
        "allowed_runtime_apply": eligible,
        "runtime_effect": True,
        "safety_revert_required": False,
        "calibration_state": state,
        "calibration_reason": reason,
        "target_env_keys": TARGET_ENV_KEYS,
        "current_values": DEFAULT_CURRENT_VALUES,
        "recommended_values": {
            "max_ws_age_ms_for_caution": int(profile["max_ws_age_ms_for_caution"]),
            "max_ws_jitter_ms_for_caution": int(profile["max_ws_jitter_ms_for_caution"]),
            "max_spread_ratio_for_caution": float(profile["max_spread_ratio_for_caution"]),
        },
        "threshold_version": f"{FAMILY}:{target_date}:{profile['profile_id']}",
        "sample_count": total_events,
        "sample_floor": sample_floor,
        "source_reports": [str(report_json_path(target_date))],
        "source_metrics": {
            "metric_role": "runtime_latency_classifier_calibration",
            "decision_authority": "next_preopen_env_apply_only",
            "window_policy": "same_day_postclose_latency_block_events",
            "primary_decision_metric": "would_pass_events",
            "source_quality_gate": "ENTRY_PIPELINE latency_block with numeric age/jitter/spread, synthetic excluded",
            "forbidden_uses": [
                "intraday_threshold_mutation",
                "provider_transport_change",
                "broker_submit_guard_bypass",
            ],
            "selected_profile": profile,
        },
    }


def build_report(target_date: str, *, source_path: Path | None = None) -> dict[str, Any]:
    events = _latency_block_events(target_date, source_path=source_path)
    profile_results = [_profile_result(profile, events) for profile in PROFILES]
    recommended = next(item for item in profile_results if item["profile_id"] == RECOMMENDED_PROFILE_ID)
    candidate = _build_candidate(target_date, recommended, len(events))
    return {
        "date": target_date,
        "family": FAMILY,
        "stage": STAGE,
        "source_path": str(source_path or _event_source_path(target_date)),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "latency_block_count": len(events),
        "unique_codes": sorted({str(event.get("stock_code") or "") for event in events if event.get("stock_code")}),
        "quote_stale_true_count": sum(1 for event in events if bool(event.get("quote_stale"))),
        "profile_results": profile_results,
        "selected_profile_id": recommended["profile_id"],
        "calibration_candidate": candidate,
        "calibration_candidates": [candidate],
    }


def _render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# Latency Classifier Recommendation {payload.get('date')}",
        "",
        f"- latency_block_count: {payload.get('latency_block_count')}",
        f"- unique_codes: {len(payload.get('unique_codes') or [])}",
        f"- selected_profile_id: {payload.get('selected_profile_id')}",
        "",
        "| profile | age_ms | jitter_ms | spread | pass_events | pass_ratio |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in payload.get("profile_results") or []:
        lines.append(
            "| {profile_id} | {age} | {jitter} | {spread:.4f} | {passes} | {ratio:.3f} |".format(
                profile_id=item.get("profile_id"),
                age=item.get("max_ws_age_ms_for_caution"),
                jitter=item.get("max_ws_jitter_ms_for_caution"),
                spread=float(item.get("max_spread_ratio_for_caution") or 0.0),
                passes=item.get("would_pass_events"),
                ratio=float(item.get("would_pass_ratio") or 0.0),
            )
        )
    candidate = payload.get("calibration_candidate") or {}
    lines.extend(
        [
            "",
            "## Apply Candidate",
            "",
            f"- calibration_state: {candidate.get('calibration_state')}",
            f"- allowed_runtime_apply: {candidate.get('allowed_runtime_apply')}",
            f"- recommended_values: `{json.dumps(candidate.get('recommended_values') or {}, ensure_ascii=False)}`",
            f"- reason: {candidate.get('calibration_reason')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(target_date: str, *, source_path: Path | None = None) -> dict[str, Any]:
    payload = build_report(target_date, source_path=source_path)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_json_path(target_date).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md_path(target_date).write_text(_render_md(payload), encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build latency classifier threshold recommendation.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target source date")
    parser.add_argument("--source-path", default=None, help="Optional pipeline_events jsonl/jsonl.gz path")
    args = parser.parse_args(argv)
    payload = write_report(args.date, source_path=Path(args.source_path) if args.source_path else None)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
