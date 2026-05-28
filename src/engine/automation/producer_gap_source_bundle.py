"""Build source-only bundles for producer gap workorders.

This producer reads existing postclose artifacts only. It does not create live
orders, thresholds, provider changes, bot restarts, or cap changes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_TYPE = "producer_gap_source_bundle"
REPORT_SCHEMA_VERSION = 1
POST_SELL_DIR = PROJECT_ROOT / "data" / "post_sell"
OUT_DIR = REPORT_DIR / REPORT_TYPE

FORBIDDEN_USES = [
    "real_order_enablement",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "position_sizing_cap_release",
]

SECTION_SPECS: dict[str, dict[str, Any]] = {
    "swing_sim_probe_label_gap": {
        "pattern_type": "swing_sim_probe_label_gap",
        "tokens": ("swing_probe", "source_probe_id", "probe"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("code", "date", "source_probe_id"),
    },
    "scale_in_counterfactual_gap": {
        "pattern_type": "scale_in_counterfactual_gap",
        "tokens": ("scale_in", "would_add", "counterfactual"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("code", "entry_time", "scale_in_arm"),
    },
    "sim_scale_in_would_add_counterfactual": {
        "pattern_type": "sim_scale_in_would_add_counterfactual",
        "tokens": ("sim_scale_in", "would_add", "assumed_filled"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("sim_record_id", "code", "stage"),
    },
    "sim_holding_runner_counterfactual": {
        "pattern_type": "sim_holding_runner_counterfactual",
        "tokens": ("runner", "holding", "sim"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("sim_record_id", "code", "held_sec"),
    },
    "sim_exit_plateau_breakdown_counterfactual": {
        "pattern_type": "sim_exit_plateau_breakdown_counterfactual",
        "tokens": ("plateau", "breakdown", "sim"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("sim_record_id", "code", "exit_reason"),
    },
    "sim_stop_recovery_counterfactual": {
        "pattern_type": "sim_stop_recovery_counterfactual",
        "tokens": ("stop", "recovery", "sim"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("sim_record_id", "code", "exit_reason"),
    },
    "stop_recovery_counterfactual": {
        "pattern_type": "stop_recovery_counterfactual",
        "tokens": ("stop", "recovery"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("code", "sell_time", "exit_reason"),
    },
    "missed_fill_recovery_counterfactual": {
        "pattern_type": "missed_fill_recovery_counterfactual",
        "tokens": ("missed_fill", "fill_quality", "unfilled", "cancel"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("sim_record_id", "code", "submit_time", "fill_quality"),
    },
    "sim_entry_selection_bucket_producer": {
        "pattern_type": "sim_entry_selection_gap",
        "tokens": ("sim_record_id", "candidate_id", "profit_rate", "score"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("sim_record_id", "candidate_id", "code", "source_stage"),
    },
    "limit_up_plateau_breakdown_exit_counterfactual": {
        "pattern_type": "limit_up_plateau_breakdown_exit_counterfactual",
        "tokens": ("limit_up", "plateau", "breakdown"),
        "required_fields": ("source_paths", "join_keys"),
        "join_keys": ("code", "sell_time", "exit_reason"),
    },
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = OUT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "sim_post_sell_evaluations": POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl",
        "post_sell_candidates": POST_SELL_DIR / f"post_sell_candidates_{target_date}.jsonl",
        "sim_post_sell_candidates": POST_SELL_DIR / f"sim_post_sell_candidates_{target_date}.jsonl",
        "time_window_regime_counterfactual": REPORT_DIR
        / "time_window_regime_counterfactual"
        / f"time_window_regime_counterfactual_{target_date}.json",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "swing_strategy_discovery_ev": REPORT_DIR
        / "swing_strategy_discovery_ev"
        / f"swing_strategy_discovery_ev_{target_date}.json",
        "swing_lifecycle_decision_matrix": REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_bucket_discovery": REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_audit": REPORT_DIR / "swing_lifecycle_audit" / f"swing_lifecycle_audit_{target_date}.json",
    }


def _load_source(path: Path) -> Any:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return None
    if path.suffix == ".jsonl":
        return list(iter_jsonl(path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _iter_dicts(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        rows.append(value)
        for child in value.values():
            rows.extend(_iter_dicts(child))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_iter_dicts(child))
    return rows


def _row_text(row: dict[str, Any]) -> str:
    try:
        return json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).lower()
    except Exception:
        return str(row).lower()


def _section_status(sample_count: int, missing_fields: list[str]) -> str:
    if sample_count <= 0:
        return "implemented_but_hold_sample"
    if missing_fields:
        return "source_field_missing"
    return "implemented"


def _build_section(section_id: str, spec: dict[str, Any], sources: dict[str, Any], source_paths: dict[str, Path]) -> dict[str, Any]:
    tokens = tuple(str(item).lower() for item in spec.get("tokens") or ())
    matched_sources: set[str] = set()
    sample_count = 0
    reason_counts: Counter[str] = Counter()
    for label, payload in sources.items():
        if payload is None:
            continue
        for row in _iter_dicts(payload):
            text = _row_text(row)
            matched = sum(1 for token in tokens if token in text)
            if matched < min(2, len(tokens)):
                continue
            sample_count += 1
            matched_sources.add(label)
            reason_counts[str(row.get("source_quality_gate") or row.get("reason") or row.get("pattern_type") or "matched")] += 1
    source_path_values = [
        str(existing_or_gzip_path(source_paths[label]))
        for label in sorted(matched_sources)
        if existing_or_gzip_path(source_paths[label]).exists()
    ]
    join_keys = list(spec.get("join_keys") or ())
    missing_fields = []
    if not source_path_values:
        missing_fields.append("source_paths")
    if not join_keys:
        missing_fields.append("join_keys")
    status = _section_status(sample_count, missing_fields)
    return {
        "section_id": section_id,
        "pattern_type": spec.get("pattern_type") or section_id,
        "sample_count": sample_count,
        "source_paths": source_path_values,
        "join_keys": join_keys,
        "missing_fields": missing_fields,
        "source_quality_status": status,
        "unknown_reason_counts": dict(reason_counts),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "producer_gap_source_bundle_source_only",
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_producer_gap_source_bundle(target_date: str) -> dict[str, Any]:
    paths = _source_paths(str(target_date))
    sources = {label: _load_source(path) for label, path in paths.items()}
    sections = [
        _build_section(section_id, spec, sources, paths)
        for section_id, spec in SECTION_SPECS.items()
    ]
    status_counts = Counter(str(item.get("source_quality_status") or "unknown") for item in sections)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": str(target_date),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "producer_gap_source_bundle_source_only",
        "forbidden_uses": FORBIDDEN_USES,
        "summary": {
            "section_count": len(sections),
            "status_counts": dict(status_counts),
            "implemented_count": status_counts.get("implemented", 0),
            "hold_sample_count": status_counts.get("implemented_but_hold_sample", 0),
            "source_field_missing_count": status_counts.get("source_field_missing", 0),
        },
        "sources": {
            label: str(existing_or_gzip_path(path)) if existing_or_gzip_path(path).exists() else None
            for label, path in paths.items()
        },
        "sections": sections,
    }
    json_path, md_path = report_paths(str(target_date))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Producer Gap Source Bundle - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- status_counts: `{summary.get('status_counts')}`",
        "",
        "## Sections",
        "",
    ]
    for item in report.get("sections") or []:
        lines.extend(
            [
                f"### {item.get('section_id')}",
                "",
                f"- sample_count: `{item.get('sample_count')}`",
                f"- source_quality_status: `{item.get('source_quality_status')}`",
                f"- missing_fields: `{item.get('missing_fields')}`",
                f"- source_paths: `{len(item.get('source_paths') or [])}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build producer gap source bundle.")
    parser.add_argument("--date", required=True)
    args = parser.parse_args(argv)
    build_producer_gap_source_bundle(args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
