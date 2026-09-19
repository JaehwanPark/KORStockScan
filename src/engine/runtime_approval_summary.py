"""Summarize family-owned postclose evidence and direct runtime handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "runtime_approval_summary"
MAX_DIRECT_JSON_BYTES = 64 * 1024 * 1024
REQUIRED_DIRECT_OWNERS = frozenset(
    {
        "source_quality",
        "entry_cancel_wait",
        "entry_split",
        "scale_in_split",
        "machine_entry",
        "low_price_two_leg",
        "low_price_expansion",
        "ws_freshness",
        "ai_outcome",
    }
)


def summary_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"runtime_approval_summary_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _paths(target_date: str) -> dict[str, Path]:
    report = DATA_DIR / "report"
    threshold = DATA_DIR / "threshold_cycle"
    return {
        "source_quality": report / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json",
        "entry_cancel_wait": report / "entry_cancel_wait_tuning" / f"entry_cancel_wait_tuning_{target_date}.json",
        "entry_cancel_wait_policy": report / "entry_cancel_wait_tuning" / f"entry_cancel_wait_policy_{target_date}.json",
        "entry_split": report / "entry_split_order_plan" / f"entry_split_order_plan_{target_date}.json",
        "entry_split_policy": threshold / "entry_split_order_policy" / f"entry_split_order_policy_{target_date}.json",
        "scale_in_split": report / "scale_in_split_order_plan" / f"scale_in_split_order_plan_{target_date}.json",
        "scale_in_split_policy": threshold / "scale_in_split_order_policy" / f"scale_in_split_order_policy_{target_date}.json",
        "machine_entry": report / "samsung_machine_entry_tuning" / f"samsung_machine_entry_tuning_{target_date}.json",
        "machine_entry_candidate": threshold / "samsung_machine_entry_policy" / "candidates" / f"samsung_machine_entry_policy_candidate_{target_date}.json",
        "low_price_two_leg": report / "low_price_two_leg_tuning" / f"low_price_two_leg_tuning_{target_date}.json",
        "low_price_candidate": threshold / "low_price_two_leg" / "candidates" / f"low_price_two_leg_policy_candidate_{target_date}.json",
        "low_price_expansion": report / "low_price_two_leg_expanded_candidate_research" / f"low_price_two_leg_expanded_candidate_research_{target_date}.json",
        "ws_freshness": report / "intraday_ws_freshness_monitor" / f"intraday_ws_freshness_monitor_{target_date}.json",
        "ai_outcome": report / "ai_decision_action_outcome_calibration" / f"ai_decision_action_outcome_calibration_{target_date}.json",
        "runtime_bootstrap": DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_{target_date}.json",
        "runtime_bootstrap_verify": DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_verify_{target_date}.json",
    }


def _read(path: Path) -> tuple[dict[str, Any], str | None, str]:
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return {}, "missing", "absent"
    except OSError as exc:
        return {}, f"unreadable:{type(exc).__name__}", "stat_failed"
    if size > MAX_DIRECT_JSON_BYTES:
        return {}, None, "stream_hash_only_large_json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {}, f"unreadable:{type(exc).__name__}", "bounded_json"
    if not isinstance(value, dict):
        return {}, "object_required", "bounded_json"
    return value, None, "bounded_json"


def _sha(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _date_matches(payload: dict[str, Any], target_date: str) -> bool:
    values = [payload.get(key) for key in ("target_date", "date", "source_date") if payload.get(key)]
    return bool(values) and target_date in {str(value) for value in values}


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_runtime_approval_summary(
    target_date: str, *, include_swing: bool = True, include_producer_gap: bool = True
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    required = REQUIRED_DIRECT_OWNERS
    sources: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for owner, path in _paths(target_date).items():
        payload, error, read_mode = _read(path)
        exact_name_date = path.stem.endswith(target_date)
        row = {
            "owner": owner,
            "path": str(path),
            "exists": path.exists(),
            "sha256": _sha(path),
            "report_type": payload.get("report_type"),
            "status": payload.get("status")
            or payload.get("decision")
            or payload.get("conclusion")
            or ("artifact_complete" if payload else None)
            or ("large_artifact_present" if read_mode == "stream_hash_only_large_json" else None),
            "target_date_matches": (
                _date_matches(payload, target_date) if payload else exact_name_date
            ),
            "runtime_effect": payload.get("runtime_effect"),
            "allowed_runtime_apply": payload.get("allowed_runtime_apply"),
            "actual_order_submitted": payload.get("actual_order_submitted"),
            "error": error,
            "read_mode": read_mode,
            "required": owner in required,
        }
        sources[owner] = row
        if owner in required and error:
            blockers.append(f"{owner}:{error}")
        elif owner in required and not row["target_date_matches"]:
            blockers.append(f"{owner}:target_date_mismatch")
        elif owner not in required and row["exists"] and not row["target_date_matches"]:
            blockers.append(f"{owner}:optional_receipt_date_mismatch")
    report = {
        "schema_version": 2,
        "report_type": "runtime_approval_summary",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass" if not blockers else "incomplete_direct_evidence",
        "decision_authority": "family_owned_direct_evidence_summary_only",
        "common_tuning_candidate_created": False,
        "daily_threshold_cycle_retired": True,
        "threshold_cycle_ev_retired": True,
        "sources": sources,
        "required_source_count": len(required),
        "available_required_source_count": sum(
            1
            for key in required
            if sources[key]["exists"]
            and sources[key]["target_date_matches"]
            and sources[key]["sha256"]
        ),
        "blocking_reasons": blockers,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "include_swing": include_swing,
        "include_producer_gap": include_producer_gap,
    }
    json_path, md_path = summary_paths(target_date)
    _atomic_write(
        json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    lines = [
        f"# Runtime approval summary - {target_date}",
        "",
        f"- status: `{report['status']}`",
        "- authority: family-owned direct evidence summary only",
        "- common Daily/EV candidate generation: `retired`",
        f"- required sources: `{report['available_required_source_count']}/{report['required_source_count']}`",
        "",
        "## Direct owners",
    ]
    lines.extend(
        f"- `{name}`: exists=`{row['exists']}` date_match=`{row['target_date_matches']}` status=`{row['status']}`"
        for name, row in sources.items()
    )
    if blockers:
        lines.extend(["", "## Blocking reasons", *[f"- `{value}`" for value in blockers]])
    _atomic_write(md_path, "\n".join(lines) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--exclude-swing", action="store_true")
    parser.add_argument("--producer-gap-disabled", action="store_true")
    args = parser.parse_args(argv)
    report = build_runtime_approval_summary(
        args.target_date,
        include_swing=not args.exclude_swing,
        include_producer_gap=not args.producer_gap_disabled,
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
