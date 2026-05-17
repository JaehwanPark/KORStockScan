"""Common observability summary builder for pattern labs."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "report" / "monitor_snapshots"
SCHEMA_VERSION = 2
OBSERVABILITY_METRIC_CONTRACT = {
    "metric_role": "funnel_count",
    "decision_authority": "source_quality_only",
    "window_policy": "daily_only_for_ops_with_rolling_consumer_required",
    "sample_floor": 1,
    "primary_decision_metric": "submitted_drought_and_blocker_count",
    "source_quality_gate": "performance_tuning + wait6579_ev_cohort + trade_review + post_sell_feedback source presence",
    "forbidden_uses": [
        "runtime_threshold_apply",
        "broker_order_enable",
        "provider_route_change",
        "bot_restart",
        "single_day_live_canary_approval",
    ],
    "runtime_effect": False,
}


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                return json.load(handle)
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_snapshot(kind: str, target_date: str) -> dict[str, Any] | None:
    for suffix in (".json", ".json.gz"):
        path = SNAPSHOT_DIR / f"{kind}_{target_date}{suffix}"
        if path.exists():
            return _load_json(path)
    return None


def build_tuning_observability_summary(
    *,
    target_date: str,
    analysis_start: str,
    analysis_end: str,
) -> dict[str, Any]:
    performance = _load_snapshot("performance_tuning", target_date) or {}
    wait6579 = _load_snapshot("wait6579_ev_cohort", target_date) or {}
    trade_review = _load_snapshot("trade_review", target_date) or {}
    post_sell = _load_snapshot("post_sell_feedback", target_date) or {}

    perf_metrics = performance.get("metrics", {}) or {}
    wait_metrics = wait6579.get("metrics", {}) or {}
    preflight = wait6579.get("preflight", {}) or {}
    trade_metrics = trade_review.get("metrics", {}) or {}
    post_metrics = post_sell.get("metrics", {}) or {}
    terminal_rows = wait6579.get("terminal_breakdown", []) or []
    terminal_map = {
        str(row.get("terminal_blocker") or ""): int(row.get("samples") or 0)
        for row in terminal_rows
    }
    submission_rows = preflight.get("submission_blocker_breakdown", []) or []
    submission_map = {
        str(row.get("label") or ""): int(row.get("samples") or 0)
        for row in submission_rows
    }

    blocked_ai_score = terminal_map.get("blocked_ai_score", 0)
    total_candidates = int(wait_metrics.get("total_candidates", 0) or 0)
    blocked_ai_score_share = round((blocked_ai_score / total_candidates) * 100, 1) if total_candidates else 0.0

    summary = {
        "schema_version": SCHEMA_VERSION,
        "metric_contract": OBSERVABILITY_METRIC_CONTRACT,
        "meta": {
            "target_date": target_date,
            "analysis_period": {
                "start_date": analysis_start,
                "end_date": analysis_end,
            },
        },
        "entry_funnel": {
            "gatekeeper_decisions": int(perf_metrics.get("gatekeeper_decisions", 0) or 0),
            "gatekeeper_eval_ms_p95": float(perf_metrics.get("gatekeeper_eval_ms_p95", 0.0) or 0.0),
            "gatekeeper_lock_wait_ms_p95": float(perf_metrics.get("gatekeeper_lock_wait_ms_p95", 0.0) or 0.0),
            "gatekeeper_model_call_ms_p95": float(perf_metrics.get("gatekeeper_model_call_ms_p95", 0.0) or 0.0),
            "budget_pass_events": int(perf_metrics.get("budget_pass_events", 0) or 0),
            "submitted_events": int(perf_metrics.get("order_bundle_submitted_events", 0) or 0),
            "budget_pass_to_submitted_rate": float(perf_metrics.get("budget_pass_to_submitted_rate", 0.0) or 0.0),
            "latency_block_events": int(perf_metrics.get("latency_block_events", 0) or 0),
            "quote_fresh_latency_blocks": int(perf_metrics.get("quote_fresh_latency_blocks", 0) or 0),
            "full_fill_events": int(perf_metrics.get("full_fill_events", 0) or 0),
            "partial_fill_events": int(perf_metrics.get("partial_fill_events", 0) or 0),
            "completed_trades": int(trade_metrics.get("completed_trades", 0) or 0),
            "realized_pnl_krw": int(trade_metrics.get("realized_pnl_krw", 0) or 0),
        },
        "buy_recovery_canary": {
            "total_candidates": total_candidates,
            "recovery_check_candidates": int(preflight.get("recovery_check_candidates", 0) or 0),
            "recovery_promoted_candidates": int(preflight.get("recovery_promoted_candidates", 0) or 0),
            "submitted_candidates": int(preflight.get("submitted_candidates", 0) or 0),
            "latency_block_candidates": int(preflight.get("latency_block_candidates", 0) or 0),
            "blocked_ai_score_samples": blocked_ai_score,
            "blocked_ai_score_share_pct": blocked_ai_score_share,
            "terminal_blockers": terminal_rows,
            "submission_blockers": submission_rows,
        },
        "holding_axis": {
            "evaluated_candidates": int(post_metrics.get("evaluated_candidates", 0) or 0),
            "missed_upside_rate": float(post_metrics.get("missed_upside_rate", 0.0) or 0.0),
            "good_exit_rate": float(post_metrics.get("good_exit_rate", 0.0) or 0.0),
            "capture_efficiency_avg_pct": float(post_metrics.get("capture_efficiency_avg_pct", 0.0) or 0.0),
        },
    }

    findings: list[dict[str, str]] = []
    if blocked_ai_score_share >= 70.0:
        findings.append(
            {
                "label": "AI threshold dominance",
                "judgment": "경고",
                "why": (
                    f"`blocked_ai_score_share={blocked_ai_score_share:.1f}%`로 WAIT/BLOCK 비중이 높아 "
                    "BUY drought 해석을 지지한다."
                ),
            }
        )
    if summary["buy_recovery_canary"]["recovery_promoted_candidates"] > 0 and summary["buy_recovery_canary"]["submitted_candidates"] == 0:
        findings.append(
            {
                "label": "Prompt improved but submit disconnected",
                "judgment": "경고",
                "why": (
                    f"`promoted={summary['buy_recovery_canary']['recovery_promoted_candidates']}`인데 "
                    f"`submitted={summary['buy_recovery_canary']['submitted_candidates']}`라 "
                    "프롬프트 개선과 주문 회복을 동일시할 수 없다."
                ),
            }
        )
    if summary["entry_funnel"]["gatekeeper_eval_ms_p95"] > 15900:
        findings.append(
            {
                "label": "Gatekeeper latency high",
                "judgment": "경고",
                "why": (
                    f"`gatekeeper_eval_ms_p95={summary['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms`로 "
                    "지연 경고 구간에 들어가 있다."
                ),
            }
        )
    if summary["entry_funnel"]["budget_pass_events"] > 0 and summary["entry_funnel"]["submitted_events"] == 0:
        findings.append(
            {
                "label": "Budget pass without submit",
                "judgment": "경고",
                "why": (
                    f"`budget_pass={summary['entry_funnel']['budget_pass_events']}`인데 "
                    f"`submitted={summary['entry_funnel']['submitted_events']}`라 "
                    "제출 전 병목이 기대값 회복을 끊고 있다."
                ),
            }
        )
    if not findings:
        findings.append(
            {
                "label": "No acute observability alert",
                "judgment": "중립",
                "why": "주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.",
            }
        )

    summary["priority_findings"] = findings
    summary["source_presence"] = {
        "performance_tuning": bool(performance),
        "wait6579_ev_cohort": bool(wait6579),
        "trade_review": bool(trade_review),
        "post_sell_feedback": bool(post_sell),
    }
    return summary


def write_tuning_observability_outputs(
    *,
    output_dir: Path,
    target_date: str,
    analysis_start: str,
    analysis_end: str,
) -> dict[str, Any]:
    summary = build_tuning_observability_summary(
        target_date=target_date,
        analysis_start=analysis_start,
        analysis_end=analysis_end,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "tuning_observability_summary.json"
    md_path = output_dir / "tuning_observability_summary.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Tuning Observability Summary",
        "",
        f"- target_date: `{target_date}`",
        f"- analysis_period: `{analysis_start} ~ {analysis_end}`",
        "",
        "## Entry Funnel",
        "",
        f"- gatekeeper_decisions: `{summary['entry_funnel']['gatekeeper_decisions']}`",
        f"- gatekeeper_eval_ms_p95: `{summary['entry_funnel']['gatekeeper_eval_ms_p95']:.0f}ms`",
        f"- gatekeeper_lock_wait_ms_p95: `{summary['entry_funnel']['gatekeeper_lock_wait_ms_p95']:.0f}ms`",
        f"- gatekeeper_model_call_ms_p95: `{summary['entry_funnel']['gatekeeper_model_call_ms_p95']:.0f}ms`",
        f"- budget_pass_events: `{summary['entry_funnel']['budget_pass_events']}`",
        f"- submitted_events: `{summary['entry_funnel']['submitted_events']}`",
        f"- budget_pass_to_submitted_rate: `{summary['entry_funnel']['budget_pass_to_submitted_rate']:.1f}%`",
        f"- latency_block_events: `{summary['entry_funnel']['latency_block_events']}`",
        f"- quote_fresh_latency_blocks: `{summary['entry_funnel']['quote_fresh_latency_blocks']}`",
        "",
        "## Buy Recovery Canary",
        "",
        f"- total_candidates: `{summary['buy_recovery_canary']['total_candidates']}`",
        f"- recovery_check: `{summary['buy_recovery_canary']['recovery_check_candidates']}`",
        f"- promoted: `{summary['buy_recovery_canary']['recovery_promoted_candidates']}`",
        f"- submitted: `{summary['buy_recovery_canary']['submitted_candidates']}`",
        f"- blocked_ai_score_share: `{summary['buy_recovery_canary']['blocked_ai_score_share_pct']:.1f}%`",
        "",
        "## Priority Findings",
        "",
    ]
    for item in summary["priority_findings"]:
        lines.append(f"- `{item['label']}`: {item['judgment']} — {item['why']}")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return summary
