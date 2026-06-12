"""Postclose deterministic tuner for the standalone BUY cancel-wait runtime."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.scalping.entry_cancel_wait_runtime import DEFAULT_THRESHOLDS, POLICY_VERSION, RUNTIME_FAMILY
from src.utils.constants import DATA_DIR


REPORT_DIR = DATA_DIR / "report" / "entry_cancel_wait_tuning"
SAMPLE_FLOOR = 5


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"entry_cancel_wait_tuning_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    plain = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    return plain if plain.exists() else plain.with_suffix(plain.suffix + ".gz")


def _iter_events(target_date: str) -> Iterable[dict[str, Any]]:
    path = _event_path(target_date)
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                yield row


def _latest_previous_thresholds(target_date: str) -> dict[str, int]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    for path in sorted(REPORT_DIR.glob("entry_cancel_wait_tuning_*.json"), reverse=True):
        report_date = path.stem.removeprefix("entry_cancel_wait_tuning_")
        if report_date >= target_date:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        values = payload.get("recommended_thresholds")
        if isinstance(values, dict):
            for profile in thresholds:
                if int(values.get(profile, 0) or 0) > 0:
                    thresholds[profile] = int(values[profile])
            break
    return thresholds


def _bounded_next(profile: str, previous: int, proposed: int) -> int:
    if profile in {"standard", "breakout"}:
        delta = 30
    else:
        delta = max(1, int(round(previous * 0.10)))
    return max(5, min(1200, max(previous - delta, min(previous + delta, proposed))))


def build_report(target_date: str) -> dict[str, Any]:
    previous = _latest_previous_thresholds(target_date)
    source_path = _event_path(target_date)
    completed: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    registered = defaultdict(int)
    invalid_rows = 0
    for event in _iter_events(target_date) or []:
        stage = str(event.get("stage") or "")
        fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
        if str(fields.get("runtime_family") or "") != RUNTIME_FAMILY:
            continue
        profile = str(fields.get("wait_profile") or "standard")
        if profile not in DEFAULT_THRESHOLDS:
            invalid_rows += 1
            continue
        if stage == "entry_cancel_wait_counterfactual_registered":
            registered[profile] += 1
            try:
                actual_timeout = int(float(fields.get("actual_timeout_sec") or 0))
                candidates = [
                    int(token)
                    for token in str(fields.get("candidate_timeout_secs") or "").split("|")
                    if token.strip()
                ]
            except Exception:
                invalid_rows += 1
                continue
            for timeout in candidates:
                if timeout <= actual_timeout:
                    completed[profile][timeout].append(0.0)
        elif stage == "entry_cancel_wait_counterfactual_completed":
            try:
                timeout = int(float(fields.get("timeout_sec")))
                ev = float(fields.get("counterfactual_ev_pct"))
            except Exception:
                invalid_rows += 1
                continue
            completed[profile][timeout].append(ev)

    recommended = dict(previous)
    profiles: dict[str, Any] = {}
    for profile in DEFAULT_THRESHOLDS:
        candidates = []
        for timeout, values in sorted(completed[profile].items()):
            candidates.append({
                "timeout_sec": timeout,
                "sample_count": len(values),
                "equal_weight_avg_profit_pct": round(sum(values) / len(values), 6),
            })
        eligible = [item for item in candidates if item["sample_count"] >= SAMPLE_FLOOR]
        if eligible:
            best = max(eligible, key=lambda item: (item["equal_weight_avg_profit_pct"], -abs(item["timeout_sec"] - previous[profile])))
            recommended[profile] = _bounded_next(profile, previous[profile], int(best["timeout_sec"]))
            state = "adjust" if recommended[profile] != previous[profile] else "hold_best_unchanged"
        else:
            state = "hold_sample"
        profiles[profile] = {
            "previous_threshold_sec": previous[profile],
            "recommended_threshold_sec": recommended[profile],
            "registered_count": registered[profile],
            "completed_candidate_count": sum(len(v) for v in completed[profile].values()),
            "sample_floor": SAMPLE_FLOOR,
            "calibration_state": state,
            "candidate_ev": candidates,
        }
    source_quality_status = "missing_source_hold" if not source_path.exists() else "warning" if invalid_rows else "pass"
    return {
        "schema_version": 1,
        "report_type": "entry_cancel_wait_tuning",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_family": RUNTIME_FAMILY,
        "policy_version": POLICY_VERSION,
        "decision_authority": "entry_cancel_wait_deterministic_ev_only",
        "runtime_effect": False,
        "allowed_runtime_apply": True,
        "standalone_operational_family": True,
        "excluded_consumers": ["ADM", "LDM", "lifecycle_bucket", "threshold_cycle_ev", "runtime_apply_bridge"],
        "source_quality_status": source_quality_status,
        "invalid_row_count": invalid_rows,
        "enabled": True,
        "automatic_off_allowed": False,
        "previous_thresholds": previous,
        "recommended_thresholds": recommended,
        "profiles": profiles,
    }


def write_report(target_date: str) -> dict[str, Any]:
    payload = build_report(target_date)
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# Entry Cancel Wait Tuning {target_date}",
        "",
        f"- family: `{RUNTIME_FAMILY}`",
        f"- source_quality_status: `{payload['source_quality_status']}`",
        "- enabled: `true` (automatic OFF forbidden)",
        "- excluded_consumers: `ADM, LDM, lifecycle_bucket, threshold_cycle_ev, runtime_apply_bridge`",
        "",
        "| profile | previous | recommended | state | completed |",
        "|---|---:|---:|---|---:|",
    ]
    for profile, item in payload["profiles"].items():
        lines.append(f"| {profile} | {item['previous_threshold_sec']} | {item['recommended_threshold_sec']} | {item['calibration_state']} | {item['completed_candidate_count']} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    write_report(args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
