"""Rebuild strictly-prior calibration history for the entry-odds observer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping.entry_odds.observer import (
    CALIBRATION_ROW_SCHEMA,
    CLEAN_BASELINE_TS,
    build_report,
)

KST = ZoneInfo("Asia/Seoul")
HISTORY_MANIFEST_SCHEMA = "entry_odds_calibration_history_manifest_v1"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL row at {path}:{line_number}: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
            rows.append(value)
    return rows


def _read_labels(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid outcome label JSON: {path}: {exc.msg}") from exc
    rows = value.get("labels") if isinstance(value, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"outcome label collection is invalid: {path}")
    return [dict(row) for row in rows]


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_source_dates(raw_root: Path, target_date: str) -> list[str]:
    dates: list[str] = []
    prefix = "entry_odds_raw_predictions_"
    for path in raw_root.glob(f"{prefix}*.jsonl"):
        date = path.stem.removeprefix(prefix)
        try:
            parsed = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=KST)
        except ValueError:
            continue
        if parsed >= CLEAN_BASELINE_TS and date < target_date:
            dates.append(date)
    return sorted(set(dates))


def build_history(
    *,
    target_date: str,
    source_dates: Sequence[str],
    raw_root: Path = Path("data/entry_odds_observer/raw"),
    trace_root: Path = Path("data/ai_decision_trace"),
    outcome_root: Path = Path("data/report/ai_decision_outcome_labels"),
    output_path: Path = Path(
        "data/entry_odds_observer/calibration/entry_odds_calibration_history.jsonl"
    ),
    manifest_path: Path | None = None,
    require_complete_producer_manifest: bool = True,
) -> dict[str, Any]:
    try:
        target_start = datetime.fromisoformat(f"{target_date}T00:00:00+09:00")
    except ValueError as exc:
        raise ValueError(f"invalid target_date: {target_date}") from exc
    dates = sorted(set(source_dates))
    if any(date >= target_date for date in dates):
        raise ValueError("calibration source dates must be strictly before target_date")
    history: list[dict[str, Any]] = []
    seen: set[str] = set()
    source_manifest: list[dict[str, Any]] = []
    exclusion_counts: Counter[str] = Counter()
    for date in dates:
        prediction_path = raw_root / f"entry_odds_raw_predictions_{date}.jsonl"
        trace_path = trace_root / f"ai_decision_trace_{date}.jsonl"
        outcome_path = outcome_root / f"ai_decision_outcome_labels_{date}.json"
        for path in (prediction_path, trace_path, outcome_path):
            if not path.exists():
                raise FileNotFoundError(f"required calibration source missing: {path}")
        producer_manifest_path = raw_root / (
            f"entry_odds_raw_predictions_{date}.manifest.json"
        )
        producer_manifest: dict[str, Any] = {}
        if require_complete_producer_manifest:
            if not producer_manifest_path.exists():
                raise FileNotFoundError(
                    f"required producer manifest missing: {producer_manifest_path}"
                )
            try:
                raw_manifest = json.loads(
                    producer_manifest_path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid producer manifest: {producer_manifest_path}"
                ) from exc
            if not isinstance(raw_manifest, dict):
                raise ValueError(
                    f"producer manifest is not an object: {producer_manifest_path}"
                )
            producer_manifest = raw_manifest
            if (
                producer_manifest.get("complete") is not True
                or producer_manifest.get("status") != "complete"
                or producer_manifest.get("failure_count") != 0
            ):
                raise ValueError(
                    f"producer manifest is incomplete: {producer_manifest_path}"
                )
        predictions = _read_jsonl(prediction_path)
        if require_complete_producer_manifest and producer_manifest.get(
            "output_prediction_count"
        ) != len(predictions):
            raise ValueError(
                f"producer manifest row count mismatch: {producer_manifest_path}"
            )
        if require_complete_producer_manifest and producer_manifest.get(
            "output_sha256"
        ) != _sha256(prediction_path):
            raise ValueError(
                f"producer manifest output hash mismatch: {producer_manifest_path}"
            )
        traces = _read_jsonl(trace_path)
        labels = _read_labels(outcome_path)
        report = build_report(
            target_date=date,
            predictions=predictions,
            calibration_rows=history,
            traces=traces,
            outcome_labels=labels,
        )
        updates = report.get("calibration_updates") or []
        if len(updates) != len(predictions):
            exclusions = report.get("source_quality_and_exclusion_manifest") or {}
            raise ValueError(
                "raw predictions did not all produce verified calibration updates: "
                + json.dumps(exclusions, ensure_ascii=True, sort_keys=True)
            )
        accepted = 0
        for raw in updates:
            if (
                not isinstance(raw, Mapping)
                or raw.get("schema") != CALIBRATION_ROW_SCHEMA
            ):
                exclusion_counts["calibration_update_schema_invalid"] += 1
                continue
            trace_id = str(raw.get("decision_trace_id") or "")
            try:
                decision_ts = datetime.fromisoformat(str(raw.get("decision_ts") or ""))
            except ValueError:
                exclusion_counts["calibration_update_decision_ts_invalid"] += 1
                continue
            if decision_ts.tzinfo is None:
                exclusion_counts["calibration_update_decision_ts_naive"] += 1
                continue
            if decision_ts < CLEAN_BASELINE_TS:
                exclusion_counts["calibration_update_pre_clean_baseline"] += 1
                continue
            if decision_ts >= target_start:
                exclusion_counts["calibration_update_not_strictly_prior"] += 1
                continue
            if not trace_id:
                exclusion_counts["calibration_update_trace_id_missing"] += 1
                continue
            if trace_id in seen:
                exclusion_counts["calibration_update_trace_id_duplicate"] += 1
                continue
            history.append(dict(raw))
            seen.add(trace_id)
            accepted += 1
        source_manifest.append(
            {
                "source_date": date,
                "prediction_count": len(predictions),
                "calibration_update_count": len(updates),
                "accepted_update_count": accepted,
                "prediction_sha256": _sha256(prediction_path),
                "producer_manifest_sha256": (
                    _sha256(producer_manifest_path)
                    if producer_manifest_path.exists()
                    else None
                ),
                "trace_sha256": _sha256(trace_path),
                "outcome_sha256": _sha256(outcome_path),
            }
        )

    history.sort(
        key=lambda row: (
            str(row.get("decision_ts") or ""),
            str(row.get("decision_trace_id") or ""),
        )
    )
    _atomic_write(
        output_path,
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in history
        ),
    )
    resolved_manifest_path = manifest_path or output_path.with_name(
        f"entry_odds_calibration_history_{target_date}.manifest.json"
    )
    manifest: dict[str, Any] = {
        "schema": HISTORY_MANIFEST_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "strictly_prior": True,
        "source_dates": dates,
        "source_manifest": source_manifest,
        "history_row_count": len(history),
        "unique_trace_count": len(seen),
        "unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in history
                if row.get("stock_code")
            }
        ),
        "exclusion_counts": dict(sorted(exclusion_counts.items())),
        "history_path": str(output_path),
        "history_sha256": _sha256(output_path),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    _atomic_write(
        resolved_manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument(
        "--source-dates",
        help="comma-separated strictly-prior dates; defaults to discovered raw files",
    )
    parser.add_argument(
        "--raw-root", type=Path, default=Path("data/entry_odds_observer/raw")
    )
    parser.add_argument(
        "--trace-root", type=Path, default=Path("data/ai_decision_trace")
    )
    parser.add_argument(
        "--outcome-root",
        type=Path,
        default=Path("data/report/ai_decision_outcome_labels"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/entry_odds_observer/calibration/entry_odds_calibration_history.jsonl"
        ),
    )
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    dates = (
        [value.strip() for value in args.source_dates.split(",") if value.strip()]
        if args.source_dates
        else discover_source_dates(args.raw_root, args.target_date)
    )
    manifest = build_history(
        target_date=args.target_date,
        source_dates=dates,
        raw_root=args.raw_root,
        trace_root=args.trace_root,
        outcome_root=args.outcome_root,
        output_path=args.output,
        manifest_path=args.manifest,
        require_complete_producer_manifest=True,
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
