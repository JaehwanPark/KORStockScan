from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.tests.bedrock_nova_micro_shadow import REPORT_DIR, shadow_jsonl_path
from src.utils.jsonl_io import read_jsonl

POST_SELL_DIR = Path("data/post_sell")


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        return numeric
    except Exception:
        return None


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q / 100
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def _stats(values: list[Any]) -> dict[str, Any]:
    cleaned = [v for v in (_safe_float(value) for value in values) if v is not None]
    if not cleaned:
        return {"n": 0, "avg": None, "median": None, "p75": None, "p90": None, "p95": None, "max": None}
    return {
        "n": len(cleaned),
        "avg": round(sum(cleaned) / len(cleaned), 2),
        "median": round(statistics.median(cleaned), 2),
        "p75": round(_percentile(cleaned, 75) or 0.0, 2),
        "p90": round(_percentile(cleaned, 90) or 0.0, 2),
        "p95": round(_percentile(cleaned, 95) or 0.0, 2),
        "max": round(max(cleaned), 2),
    }


def _sum_float(rows: list[dict[str, Any]], key: str) -> float:
    return round(sum(_safe_float(row.get(key)) or 0.0 for row in rows), 8)


def _sum_numeric(rows: list[dict[str, Any]], key: str) -> int:
    return int(sum(_safe_float(row.get(key)) or 0.0 for row in rows))


def _sum_nova_total_input_tokens(rows: list[dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        explicit = _safe_float(row.get("nova_total_input_tokens"))
        if explicit is not None:
            total += int(explicit)
            continue
        total += int(_safe_float(row.get("nova_input_tokens")) or 0)
        total += int(_safe_float(row.get("nova_cache_read_input_tokens")) or 0)
        total += int(_safe_float(row.get("nova_cache_write_input_tokens")) or 0)
    return total


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _action_bucket(action: Any) -> str:
    normalized = str(action or "").strip().upper()
    if normalized in {"EXIT", "DROP", "SELL", "TRIM"}:
        return "defensive"
    if normalized in {"BUY", "HOLD", "ADD", "SCALE_IN"}:
        return "risk_on_or_hold"
    if normalized == "WAIT":
        return "neutral_wait"
    return "unknown"


def _outcome_score(action: Any, profit_rate: Any) -> int:
    profit = _safe_float(profit_rate)
    if profit is None or profit == 0:
        return 0
    bucket = _action_bucket(action)
    if bucket == "defensive":
        return 1 if profit < 0 else -1
    if bucket == "risk_on_or_hold":
        return 1 if profit > 0 else -1
    return 0


def _sim_post_sell_path(target_date: str) -> Path:
    return POST_SELL_DIR / f"sim_post_sell_candidates_{target_date}.jsonl"


def _build_outcome_linked_performance(target_date: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    post_sell_path = _sim_post_sell_path(target_date)
    sells = read_jsonl(post_sell_path) if post_sell_path.exists() else []
    shadow_by_sim_id: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        sim_record_id = str(row.get("sim_record_id") or "").strip()
        if sim_record_id:
            shadow_by_sim_id.setdefault(sim_record_id, []).append(row)

    matched: list[dict[str, Any]] = []
    unmatched_count = 0
    for sell in sells:
        profit = _safe_float(sell.get("profit_rate"))
        if profit is None:
            continue
        sim_record_id = str(sell.get("sim_record_id") or "").strip()
        candidates = shadow_by_sim_id.get(sim_record_id) or []
        if not candidates:
            unmatched_count += 1
            continue
        best = max(candidates, key=lambda item: str(item.get("created_at") or ""))
        openai_score = _outcome_score(best.get("openai_action"), profit)
        nova_score = _outcome_score(best.get("nova_action"), profit)
        matched.append(
            {
                "sim_record_id": sim_record_id,
                "symbol": best.get("symbol") or sell.get("stock_name") or sell.get("stock_code"),
                "stock_name": sell.get("stock_name"),
                "sell_time": sell.get("sell_time"),
                "profit_rate": profit,
                "exit_rule": sell.get("exit_rule"),
                "source_event_stage": best.get("source_event_stage"),
                "openai_action": best.get("openai_action"),
                "openai_score": best.get("openai_score"),
                "nova_action": best.get("nova_action"),
                "nova_score": best.get("nova_score"),
                "openai_outcome_score": openai_score,
                "nova_outcome_score": nova_score,
                "model_edge": "nova" if nova_score > openai_score else "openai" if openai_score > nova_score else "tie",
                "join_type": "exact_sim_record_id",
                "post_sell_id": sell.get("post_sell_id"),
                "entry_adm_candidate_id": best.get("entry_adm_candidate_id") or sell.get("entry_adm_candidate_id"),
            }
        )

    by_stage: dict[str, dict[str, Any]] = {}
    for item in matched:
        stage = str(item.get("source_event_stage") or "unknown")
        bucket = by_stage.setdefault(
            stage,
            {
                "matched_count": 0,
                "openai_outcome_score_sum": 0,
                "nova_outcome_score_sum": 0,
                "nova_edge_count": 0,
                "openai_edge_count": 0,
                "tie_count": 0,
                "avg_profit_rate": None,
            },
        )
        bucket["matched_count"] += 1
        bucket["openai_outcome_score_sum"] += item["openai_outcome_score"]
        bucket["nova_outcome_score_sum"] += item["nova_outcome_score"]
        if item["model_edge"] == "nova":
            bucket["nova_edge_count"] += 1
        elif item["model_edge"] == "openai":
            bucket["openai_edge_count"] += 1
        else:
            bucket["tie_count"] += 1

    for stage, bucket in by_stage.items():
        profits = [item["profit_rate"] for item in matched if str(item.get("source_event_stage") or "unknown") == stage]
        bucket["avg_profit_rate"] = round(sum(profits) / len(profits), 4) if profits else None

    return {
        "metric_role": "sim_probe_ev",
        "decision_authority": "shadow_observation_only",
        "runtime_effect": False,
        "source_path": str(post_sell_path),
        "sell_completed_count": len([sell for sell in sells if _safe_float(sell.get("profit_rate")) is not None]),
        "exact_matched_count": len(matched),
        "unmatched_sell_count": unmatched_count,
        "join_quality": {
            "method": "exact_sim_record_id_only",
            "exact_match_rate": round(len(matched) / (len(matched) + unmatched_count), 4) if (matched or unmatched_count) else 0.0,
            "note": "Rows before sim_record_id instrumentation remain unmatched instead of being treated as reliable performance evidence.",
        },
        "overall": {
            "openai_outcome_score_sum": sum(item["openai_outcome_score"] for item in matched),
            "nova_outcome_score_sum": sum(item["nova_outcome_score"] for item in matched),
            "nova_minus_openai_outcome_score": sum(item["nova_outcome_score"] - item["openai_outcome_score"] for item in matched),
            "nova_edge_count": sum(1 for item in matched if item["model_edge"] == "nova"),
            "openai_edge_count": sum(1 for item in matched if item["model_edge"] == "openai"),
            "tie_count": sum(1 for item in matched if item["model_edge"] == "tie"),
        },
        "by_stage": by_stage,
        "sample_rows": matched[:50],
        "scoring_note": "defensive action is positive when final sim PnL is negative and negative when final sim PnL is positive; HOLD/BUY is the inverse; WAIT is neutral.",
        "forbidden_uses": ["provider route change", "runtime threshold mutation", "broker order decision", "bot restart trigger"],
    }


def build_report(target_date: str) -> dict[str, Any]:
    path = shadow_jsonl_path(target_date)
    rows = read_jsonl(path) if path.exists() else []
    parse_ok = [row for row in rows if str(row.get("parse_ok")).lower() == "true"]
    comparable = [row for row in parse_ok if row.get("openai_action") and row.get("nova_action")]
    action_matches = sum(1 for row in comparable if str(row.get("action_match")).lower() == "true")
    total_openai_cost = _sum_float(rows, "estimated_openai_cost_usd")
    total_nova_cost = _sum_float(rows, "estimated_nova_cost_usd")
    return {
        "report_type": "bedrock_nova_micro_shadow_report",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_path": str(path),
        "decision_authority": "shadow_observation_only",
        "runtime_effect": False,
        "summary": {
            "row_count": len(rows),
            "parse_ok_count": len(parse_ok),
            "parse_ok_rate": round(len(parse_ok) / len(rows), 4) if rows else 0.0,
            "comparable_count": len(comparable),
            "action_match_count": action_matches,
            "action_match_rate": round(action_matches / len(comparable), 4) if comparable else 0.0,
        },
        "latency": {
            "openai_latency_ms": _stats([row.get("openai_latency_ms") for row in rows]),
            "nova_latency_ms": _stats([row.get("nova_latency_ms") for row in rows]),
        },
        "cost": {
            "estimated_openai_cost_usd": total_openai_cost,
            "estimated_nova_cost_usd": total_nova_cost,
            "estimated_nova_minus_openai_usd": round(total_nova_cost - total_openai_cost, 8),
            "estimated_nova_to_openai_ratio": round(total_nova_cost / total_openai_cost, 4) if total_openai_cost else None,
        },
        "prompt_cache": {
            "enabled_row_count": sum(1 for row in rows if str(row.get("nova_prompt_cache_enabled")).lower() == "true"),
            "nova_input_tokens": _sum_numeric(rows, "nova_input_tokens"),
            "nova_cache_read_input_tokens": _sum_numeric(rows, "nova_cache_read_input_tokens"),
            "nova_cache_write_input_tokens": _sum_numeric(rows, "nova_cache_write_input_tokens"),
            "nova_total_input_tokens": _sum_nova_total_input_tokens(rows),
            "cache_read_stats": _stats([row.get("nova_cache_read_input_tokens") for row in rows]),
            "cache_write_stats": _stats([row.get("nova_cache_write_input_tokens") for row in rows]),
            "pricing_note": "When Bedrock prompt caching is enabled, inputTokens can exclude cache read/write tokens; cost uses all three buckets when present.",
        },
        "decision_agreement": {
            "endpoint_counts": dict(Counter(str(row.get("endpoint_name") or "-") for row in rows)),
            "source_event_stage_counts": dict(Counter(str(row.get("source_event_stage") or "unknown") for row in rows)),
            "score_delta": _stats([row.get("score_delta") for row in comparable]),
            "openai_action_counts": dict(Counter(str(row.get("openai_action") or "-") for row in comparable)),
            "nova_action_counts": dict(Counter(str(row.get("nova_action") or "-") for row in comparable)),
        },
        "parse_schema_quality": {
            "error_counts": dict(Counter(str(row.get("error_type") or "-") for row in rows if row.get("error_type"))),
            "parse_fail_count": len(rows) - len(parse_ok),
        },
        "tuning_linkage": {
            "join_keys": ["openai_request_id", "pipeline_stage", "symbol", "record_id", "cache_key"],
            "sample_rows": [
                {
                    "openai_request_id": row.get("openai_request_id"),
                    "pipeline_stage": row.get("pipeline_stage"),
                    "endpoint_name": row.get("endpoint_name"),
                    "symbol": row.get("symbol"),
                    "record_id": row.get("record_id"),
                    "sim_record_id": row.get("sim_record_id"),
                    "sim_parent_record_id": row.get("sim_parent_record_id"),
                    "entry_adm_candidate_id": row.get("entry_adm_candidate_id"),
                    "source_event_stage": row.get("source_event_stage"),
                    "cache_key": row.get("cache_key"),
                }
                for row in rows[:50]
            ],
            "forbidden_uses": ["runtime threshold mutation", "provider route change", "broker order decision", "bot restart trigger"],
        },
        "outcome_linked_performance": _build_outcome_linked_performance(target_date, rows),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    return "\n".join(
        [
            f"# Bedrock Nova Micro Shadow Report - {report['target_date']}",
            "",
            f"- generated_at: `{report['generated_at']}`",
            f"- decision_authority: `{report['decision_authority']}`",
            f"- runtime_effect: `{report['runtime_effect']}`",
            f"- rows: `{summary['row_count']}`",
            f"- parse_ok_rate: `{summary['parse_ok_rate']}`",
            f"- action_match_rate: `{summary['action_match_rate']}`",
            "",
            "## Latency",
            "",
            f"- latency: `{report['latency']}`",
            "",
            "## Cost",
            "",
            f"- cost: `{report['cost']}`",
            "",
            "## Prompt Cache",
            "",
            f"- prompt_cache: `{report.get('prompt_cache', {})}`",
            "",
            "## Decision Agreement",
            "",
            f"- decision_agreement: `{report['decision_agreement']}`",
            "",
            "## Outcome-Linked Performance",
            "",
            f"- outcome_linked_performance: `{report.get('outcome_linked_performance', {})}`",
            "",
            "## Parse / Schema Quality",
            "",
            f"- parse_schema_quality: `{report['parse_schema_quality']}`",
            "- forbidden: threshold/provider/order/bot restart 변경 근거로 사용하지 않는다.",
            "",
        ]
    )


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_date = str(report["target_date"])
    json_path = REPORT_DIR / f"bedrock_nova_micro_shadow_report_{target_date}.json"
    md_path = REPORT_DIR / f"bedrock_nova_micro_shadow_report_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build test-only Bedrock Nova Micro shadow comparison report.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args(argv)
    report = build_report(args.date)
    json_path, md_path = write_report(report)
    print(json.dumps({"json": str(json_path), "md": str(md_path), "rows": report["summary"]["row_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
