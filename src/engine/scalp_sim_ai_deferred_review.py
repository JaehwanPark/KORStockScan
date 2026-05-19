"""Build a postclose source artifact for deferred scalp sim AI holding reviews."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import read_jsonl


REPORT_DIR = DATA_DIR / "report" / "scalp_sim_ai_deferred_review"


def _load_events(target_date: str) -> list[dict]:
    path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    return read_jsonl(path, errors="ignore")


def _event_fields(event: dict) -> dict:
    fields = event.get("fields")
    return fields if isinstance(fields, dict) else {}


def _is_deferred_event(event: dict) -> bool:
    stage = str(event.get("stage") or "")
    fields = _event_fields(event)
    return (
        stage == "scalp_sim_ai_holding_deferred"
        and str(fields.get("simulation_book") or "") == "scalp_ai_buy_all"
        and fields.get("actual_order_submitted") is False
    )


def build_report(target_date: str) -> dict:
    events = _load_events(target_date)
    deferred = [event for event in events if _is_deferred_event(event)]
    reason_counts = Counter(str(_event_fields(event).get("defer_reason") or "-") for event in deferred)
    source_counts = Counter(str(_event_fields(event).get("source_stage") or "-") for event in deferred)
    rows = []
    for event in deferred:
        fields = _event_fields(event)
        rows.append(
            {
                "emitted_at": event.get("emitted_at"),
                "stock_name": event.get("stock_name"),
                "stock_code": event.get("stock_code"),
                "defer_reason": fields.get("defer_reason"),
                "feature_signature": fields.get("feature_signature"),
                "profit_rate": fields.get("profit_rate"),
                "peak_profit": fields.get("peak_profit"),
                "held_sec": fields.get("held_sec"),
                "source_stage": fields.get("source_stage"),
                "decision_authority": fields.get("decision_authority"),
                "actual_order_submitted": fields.get("actual_order_submitted"),
                "broker_order_forbidden": fields.get("broker_order_forbidden"),
                "runtime_effect": fields.get("runtime_effect"),
            }
        )
    return {
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"),
        "artifact_role": "postclose_source_packet_for_sim_ai_quality_review",
        "runtime_effect": False,
        "decision_authority": "sim_observation_only",
        "forbidden_uses": [
            "broker_submit",
            "real_execution_quality_claim",
            "live_buy_promotion",
            "intraday_threshold_mutation",
            "provider_route_change",
        ],
        "summary": {
            "deferred_count": len(rows),
            "defer_reason_counts": dict(sorted(reason_counts.items())),
            "source_stage_counts": dict(sorted(source_counts.items())),
        },
        "rows": rows,
    }


def write_outputs(report: dict, output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = str(report.get("target_date") or datetime.now().date().isoformat())
    json_path = output_dir / f"scalp_sim_ai_deferred_review_{target_date}.json"
    md_path = output_dir / f"scalp_sim_ai_deferred_review_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report.get("summary") or {}
    lines = [
        f"# Scalp Sim AI Deferred Review {target_date}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- source: `{report.get('source_path')}`",
        f"- artifact_role: `{report.get('artifact_role')}`",
        f"- runtime_effect: `{str(report.get('runtime_effect')).lower()}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- deferred_count: `{summary.get('deferred_count', 0)}`",
        "",
        "## Defer Reasons",
        "",
    ]
    for reason, count in (summary.get("defer_reason_counts") or {}).items():
        lines.append(f"- `{reason}`: `{count}`")
    lines.extend(
        [
            "",
            "## Deferred Rows",
            "",
            "| time | stock | reason | profit | peak | held_sec |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in report.get("rows") or []:
        lines.append(
            f"| {row.get('emitted_at') or '-'} | {row.get('stock_name')}({row.get('stock_code')}) | "
            f"`{row.get('defer_reason') or '-'}` | {row.get('profit_rate') or '-'} | "
            f"{row.get('peak_profit') or '-'} | {row.get('held_sec') or '-'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=datetime.now().date().isoformat())
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args(argv)
    json_path, md_path = write_outputs(build_report(args.target_date), args.output_dir)
    print(f"[OK] wrote {json_path}")
    print(f"[OK] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
