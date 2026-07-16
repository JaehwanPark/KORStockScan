from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

WINDOWS_ARTIFACT_DIR = "source_quality/market_halt_windows/windows"
SESSION_EVENTS_ARTIFACT_DIR = "source_quality/market_halt_windows/session_events"


def artifact_path(target_date: str, *, data_dir: Path | None = None) -> Path:
    base = data_dir or DATA_DIR
    return base / WINDOWS_ARTIFACT_DIR / f"{target_date}.json"


def session_events_path(target_date: str, *, data_dir: Path | None = None) -> Path:
    base = data_dir or DATA_DIR
    return base / SESSION_EVENTS_ARTIFACT_DIR / f"{target_date}.json"


def load_market_halt_windows(
    target_date: str, *, data_dir: Path | None = None
) -> list[dict[str, Any]]:
    path = artifact_path(target_date, data_dir=data_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = payload.get("windows") if isinstance(payload, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def append_market_session_event(
    *,
    target_date: str,
    event: dict[str, Any],
    data_dir: Path | None = None,
) -> Path:
    path = session_events_path(target_date, data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    events = payload.get("session_events")
    if not isinstance(events, list):
        events = []
    events.append(
        {
            "observed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            **event,
        }
    )
    payload.update(
        {
            "report_type": "market_halt_windows",
            "target_date": target_date,
            "schema_version": 1,
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "provider_route_change",
                "bot_restart",
                "cap_release",
                "hard_safety_relaxation",
            ],
            "windows_source": str(artifact_path(target_date, data_dir=data_dir)),
            "session_events": events[-500:],
        }
    )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
