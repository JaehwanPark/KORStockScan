from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.bedrock_nova_lite_v2_shadow import REPORT_DIR
from src.utils.jsonl_io import read_jsonl


def shadow_jsonl_path(target_date: str) -> Path:
    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d"))
    return REPORT_DIR / f"bedrock_nova_lite_v2_shadow_{safe_date}.jsonl"


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def build_report(target_date: str) -> dict[str, Any]:
    path = shadow_jsonl_path(target_date)
    rows = read_jsonl(path) if path.exists() else []
    parse_ok = [row for row in rows if bool(row.get("parse_ok")) or bool(row.get("v2_parse_ok"))]
    action_match = [
        row
        for row in parse_ok
        if bool(row.get("v1_v2_action_match"))
        or (
            str(row.get("baseline_action") or row.get("openai_action") or "").strip().upper()
            == str(row.get("candidate_action") or row.get("nova_action") or "").strip().upper()
            and str(row.get("baseline_action") or row.get("openai_action") or "").strip()
        )
    ]
    latency_values = [
        value
        for value in (_safe_float(row.get("v2_latency_ms") or row.get("nova_latency_ms")) for row in parse_ok)
        if value is not None
    ]
    endpoint_counts = Counter(str(row.get("endpoint_name") or "unknown") for row in rows)
    return {
        "report_type": "bedrock_nova_lite_v2_shadow_report",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision_authority": "shadow_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_path": str(path),
        "summary": {
            "row_count": len(rows),
            "parse_ok_count": len(parse_ok),
            "parse_ok_rate": round(len(parse_ok) / len(rows), 4) if rows else 0.0,
            "v1_v2_action_match_count": len(action_match),
            "v1_v2_action_match_rate": round(len(action_match) / len(parse_ok), 4) if parse_ok else 0.0,
            "avg_v2_latency_ms": round(sum(latency_values) / len(latency_values), 2) if latency_values else None,
        },
        "endpoint_counts": dict(endpoint_counts),
        "model_ids": sorted({str(row.get("candidate_bedrock_model_id") or row.get("model_id") or "") for row in rows if row}),
        "baseline_model_ids": sorted({str(row.get("baseline_bedrock_model_id") or row.get("baseline_model_id") or "") for row in rows if row}),
        "forbidden_uses": [
            "provider_route_change",
            "threshold_mutation",
            "order_guard_change",
            "bot_restart_trigger",
            "lite_v1_promotion_evidence_mixing",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    return "\n".join(
        [
            f"# Bedrock Nova Lite v2 Shadow Report - {report['target_date']}",
            "",
            "- decision_authority: `shadow_observation_only`",
            "- runtime_effect: `false`",
            "- actual_order_submitted: `false`",
            "",
            "## Summary",
            "",
            f"- row_count: `{summary['row_count']}`",
            f"- parse_ok_rate: `{summary['parse_ok_rate']}`",
            f"- v1_v2_action_match_rate: `{summary['v1_v2_action_match_rate']}`",
            f"- avg_v2_latency_ms: `{summary['avg_v2_latency_ms']}`",
            f"- endpoint_counts: `{report['endpoint_counts']}`",
            f"- model_ids: `{report['model_ids']}`",
            f"- baseline_model_ids: `{report['baseline_model_ids']}`",
            "",
        ]
    )


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_date = str(report["target_date"])
    json_path = REPORT_DIR / f"bedrock_nova_lite_v2_shadow_report_{target_date}.json"
    md_path = REPORT_DIR / f"bedrock_nova_lite_v2_shadow_report_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Bedrock Nova Lite v2 shadow report.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args(argv)
    report = build_report(args.date)
    json_path, md_path = write_report(report)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "rows": report["summary"]["row_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
