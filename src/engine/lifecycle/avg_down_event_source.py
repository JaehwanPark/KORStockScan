"""Bounded native lifecycle-event projection shared by Main postclose readers."""

from __future__ import annotations

import hashlib

from datetime import datetime, timedelta, timezone

from pathlib import Path

from typing import Any, Iterable

from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))

REPORT_TYPE = "scalping_avg_down_recovery_calibration"

CLEAN_BASELINE_DATE = "2026-06-05"

CLEAN_BASELINE_TS = datetime(2026, 6, 5, tzinfo=KST)


def _parse_time(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _events_paths_for_date(target_date: str) -> list[Path]:
    path = _events_path(target_date)
    result: list[Path] = []
    gzip_path = path.with_suffix(path.suffix + ".gz")
    if path.exists():
        result.append(path)
    elif gzip_path.exists():
        result.append(gzip_path)
    late = path.with_name(f"{path.stem}.late.jsonl")
    late_gzip = late.with_suffix(late.suffix + ".gz")
    if late.exists():
        result.append(late)
    elif late_gzip.exists():
        result.append(late_gzip)
    return result


def _date_from_events_path(path: Path) -> str | None:
    name = path.name
    for suffix in (".late.jsonl.gz", ".late.jsonl", ".jsonl.gz", ".jsonl"):
        if name.startswith("pipeline_events_") and name.endswith(suffix):
            return name.removeprefix("pipeline_events_").removesuffix(suffix)
    return None


def _iter_events(paths: list[Path]) -> Iterable[dict[str, Any]]:
    from src.engine.sentinel_event_cache import load_verified_day_projection

    relevant = {
        "avg_down_runtime_config_observed",
        "avg_down_route_arbitration_observed",
        "avg_down_route_sizing_observed",
        "avg_down_exit_replay_frame_observed",
        "sell_completed",
        "scale_in_executed",
        "avg_down_route_arbitration_terminal",
        "scalp_sim_scale_in_candidate_funnel",
        "stop_line_touch_mandatory_avg_down_submitted",
    }
    import inspect

    parser_version = (
        "avg_down_day_facts_v1:"
        + hashlib.sha256(
            (
                inspect.getsource(_iter_events)
                + inspect.getsource(_parse_time)
                + inspect.getsource(load_verified_day_projection)
                + CLEAN_BASELINE_DATE
            ).encode()
        ).hexdigest()
    )
    for source in paths:
        source_date = _date_from_events_path(source)
        if not source.exists():
            continue

        def project(event):
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            row = {**event, **fields, "_source_event_date": source_date}
            if row.get("stage") in relevant:
                return {
                    key: value
                    for key, value in row.items()
                    if key not in {"fields", "text_payload"}
                }
            stamp = _parse_time(row.get("emitted_at"))
            reason = (
                "invalid_or_prebaseline_timestamp"
                if stamp is None or stamp < CLEAN_BASELINE_TS
                else (
                    "timestamp_file_date_mismatch"
                    if stamp.date().isoformat() != source_date
                    else "irrelevant_valid_event_count"
                )
            )
            return {"_census": {reason: 1, "projected_out_count": 1}}

        rows, census = load_verified_day_projection(
            raw_path=source,
            cache_dir=DATA_DIR / "cache" / REPORT_TYPE,
            cache_name="day-facts",
            parser_version=parser_version,
            parse_payload=project,
        )
        yield {"_projection_census": census}
        yield from rows
