"""Build daily WS/REST quote consistency normalization reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from src.trading.market.quote_consistency import RUNTIME_FAMILY
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


REPORT_DIR = DATA_DIR / "report" / "quote_consistency"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENTS_DIR = DATA_DIR / "threshold_cycle"


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if text in {"", "-", "None", "null"}:
            return default
        return float(text)
    except Exception:
        return default


def _to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "pipeline_events": existing_or_gzip_path(PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"),
        "threshold_events": existing_or_gzip_path(THRESHOLD_EVENTS_DIR / f"threshold_events_{target_date}.jsonl"),
    }


def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for row in iter_jsonl(path):
        if isinstance(row, dict):
            yield row


def _flatten_event(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(row)
    merged.update(fields)
    return merged


def _percentiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"avg": None, "p50": None, "p95": None, "p99": None, "max": None}
    ordered = sorted(values)

    def pick(percent: float) -> float:
        idx = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percent))))
        return round(float(ordered[idx]), 4)

    return {
        "avg": round(float(mean(ordered)), 4),
        "p50": pick(0.50),
        "p95": pick(0.95),
        "p99": pick(0.99),
        "max": round(float(ordered[-1]), 4),
    }


def build_quote_consistency_report(target_date: str | None = None) -> dict[str, Any]:
    target_date = target_date or date.today().isoformat()
    paths = _source_paths(target_date)
    stage_counts: dict[str, Counter] = defaultdict(Counter)
    source_counts: Counter = Counter()
    action_counts: Counter = Counter()
    gap_values: list[float] = []
    defective_rows: list[dict[str, Any]] = []
    observed_count = 0
    safety_exit_count = 0
    rest_fallback_count = 0
    missing_required_fields = 0
    ev_input_blocked_count = 0

    for source_name, path in paths.items():
        for raw in _iter_rows(path):
            row = _flatten_event(raw)
            state = str(row.get("quote_consistency_state") or "").strip()
            has_family = str(row.get("quote_consistency_family") or "") == RUNTIME_FAMILY
            if not state and not has_family:
                continue
            observed_count += 1
            stage = str(row.get("stage") or row.get("event_type") or "unknown")
            stage_counts[stage][state or "missing_state"] += 1
            source_counts[str(row.get("price_source") or "unknown")] += 1
            action_counts[str(row.get("quote_consistency_runtime_action") or "unknown")] += 1
            gap = _to_float(row.get("ws_rest_gap_bps"))
            if gap is not None:
                gap_values.append(float(gap))
            if _to_bool(row.get("quote_consistency_safety_exit")) or _to_bool(
                row.get("quote_consistency_safety_exit_allowed")
            ):
                safety_exit_count += 1
            if str(row.get("price_source") or "").startswith("rest") or _to_bool(
                row.get("pre_submit_rest_orderbook_refresh_applied")
            ):
                rest_fallback_count += 1
            required_missing = [
                key
                for key in (
                    "canonical_mark_price",
                    "executable_buy_price",
                    "executable_sell_price",
                    "price_source",
                    "normalization_runtime_effect",
                )
                if key not in row or str(row.get(key) or "").strip() == ""
            ]
            if required_missing:
                missing_required_fields += 1
            state_lower = state.lower()
            ev_ineligible = state_lower in {"diverged", "missing", "stale"} or bool(required_missing)
            if ev_ineligible:
                ev_input_blocked_count += 1
                if len(defective_rows) < 200:
                    defective_rows.append(
                        {
                            "source": source_name,
                            "stage": stage,
                            "stock_code": row.get("stock_code"),
                            "stock_name": row.get("stock_name"),
                            "quote_consistency_state": state,
                            "quote_consistency_reason": row.get("quote_consistency_reason"),
                            "missing_fields": required_missing,
                            "ws_rest_gap_bps": gap,
                            "emitted_at": row.get("emitted_at"),
                        }
                    )

    source_missing = [name for name, path in paths.items() if not path.exists()]
    verifier_findings = []
    if source_missing:
        verifier_findings.append(
            {
                "severity": "warning",
                "code": "quote_consistency_source_missing",
                "sources": source_missing,
            }
        )
    if observed_count <= 0:
        verifier_findings.append(
            {
                "severity": "warning",
                "code": "quote_consistency_observation_missing",
                "message": "No quote_consistency_normalization rows were found for the target date.",
            }
        )
    if missing_required_fields:
        verifier_findings.append(
            {
                "severity": "fail",
                "code": "quote_consistency_required_fields_missing",
                "count": missing_required_fields,
            }
        )
    if any(counts.get("diverged", 0) for counts in stage_counts.values()) and safety_exit_count <= 0:
        verifier_findings.append(
            {
                "severity": "warning",
                "code": "quote_consistency_divergence_without_safety_exit_rows",
            }
        )

    return {
        "schema_version": 1,
        "runtime_family": RUNTIME_FAMILY,
        "target_date": target_date,
        "sources": {name: str(path) if path.exists() else None for name, path in paths.items()},
        "summary": {
            "observed_count": observed_count,
            "rest_fallback_count": rest_fallback_count,
            "safety_exit_count": safety_exit_count,
            "missing_required_fields": missing_required_fields,
            "ev_input_blocked_count": ev_input_blocked_count,
            "gap_bps": _percentiles(gap_values),
        },
        "stage_state_counts": {stage: dict(counts) for stage, counts in sorted(stage_counts.items())},
        "source_counts": dict(source_counts),
        "runtime_action_counts": dict(action_counts),
        "defective_row_candidates": defective_rows,
        "verifier_findings": verifier_findings,
    }


def write_quote_consistency_report(report: dict[str, Any], *, output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = str(report.get("target_date"))
    json_path = output_dir / f"quote_consistency_{target_date}.json"
    md_path = output_dir / f"quote_consistency_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        f"# Quote Consistency Report {target_date}",
        "",
        f"- runtime_family: `{report.get('runtime_family')}`",
        f"- observed_count: `{summary.get('observed_count', 0)}`",
        f"- rest_fallback_count: `{summary.get('rest_fallback_count', 0)}`",
        f"- safety_exit_count: `{summary.get('safety_exit_count', 0)}`",
        f"- ev_input_blocked_count: `{summary.get('ev_input_blocked_count', 0)}`",
        f"- missing_required_fields: `{summary.get('missing_required_fields', 0)}`",
        "",
        "## Verifier Findings",
    ]
    findings = report.get("verifier_findings") or []
    if findings:
        lines.extend(f"- `{item.get('severity')}` `{item.get('code')}`" for item in findings)
    else:
        lines.append("- `ok` `none`")
    lines.append("")
    lines.append("## Stage State Counts")
    for stage, counts in (report.get("stage_state_counts") or {}).items():
        count_text = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        lines.append(f"- `{stage}`: {count_text}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_quote_consistency_report(args.target_date)
    if args.write:
        json_path, md_path = write_quote_consistency_report(report)
        print(json.dumps({"json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
