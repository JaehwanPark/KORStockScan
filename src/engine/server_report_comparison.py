"""Compare local monitor/report data with a remote KORStockScan server.

Default comparison intentionally excludes profit-derived metrics because
`profit_rate` may be normalized via fallback values (for example NULL -> 0),
which can distort cross-server conclusions.
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.engine.log_archive_service import load_monitor_snapshot


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class MetricSpec:
    label: str
    path: tuple[str, ...]


@dataclass(frozen=True)
class SectionPolicy:
    key: str
    label: str
    remote_path_template: str
    safe_metrics: tuple[MetricSpec, ...]
    excluded_metric_labels: tuple[str, ...] = ()


def _trade_review_local_loader(target_date: str, since_time: str | None) -> JsonDict:
    snapshot = load_monitor_snapshot("trade_review", target_date)
    if snapshot is not None:
        return snapshot
    from src.engine.sniper_trade_review_report import build_trade_review_report

    return build_trade_review_report(
        target_date=target_date,
        since_time=since_time,
        top_n=300,
        scope="entered",
    )


def _performance_tuning_local_loader(target_date: str, since_time: str | None) -> JsonDict:
    snapshot = load_monitor_snapshot("performance_tuning", target_date)
    if snapshot is not None:
        return snapshot
    from src.engine.sniper_performance_tuning_report import build_performance_tuning_report

    return build_performance_tuning_report(target_date=target_date, since_time=since_time)


def _post_sell_local_loader(target_date: str, since_time: str | None) -> JsonDict:
    snapshot = load_monitor_snapshot("post_sell_feedback", target_date)
    if snapshot is not None:
        return snapshot
    from src.engine.sniper_post_sell_feedback import build_post_sell_feedback_report

    return build_post_sell_feedback_report(target_date=target_date, evaluate_now=True)


def _entry_pipeline_local_loader(target_date: str, since_time: str | None) -> JsonDict:
    from src.engine.sniper_entry_pipeline_report import build_entry_pipeline_flow_report

    return build_entry_pipeline_flow_report(target_date, since_time=since_time, top_n=10)


def _strategy_performance_local_loader(target_date: str, since_time: str | None) -> JsonDict:
    from src.engine.strategy_position_performance_report import build_strategy_position_performance_report

    return build_strategy_position_performance_report(target_date)


LOCAL_LOADERS: dict[str, Callable[[str, str | None], JsonDict]] = {
    "trade_review": _trade_review_local_loader,
    "performance_tuning": _performance_tuning_local_loader,
    "post_sell_feedback": _post_sell_local_loader,
    "entry_pipeline_flow": _entry_pipeline_local_loader,
    "strategy_performance": _strategy_performance_local_loader,
}


SECTION_POLICIES: tuple[SectionPolicy, ...] = (
    SectionPolicy(
        key="trade_review",
        label="Trade Review",
        remote_path_template="/api/trade-review?date={date}",
        safe_metrics=(
            MetricSpec("total_trades", ("metrics", "total_trades")),
            MetricSpec("completed_trades", ("metrics", "completed_trades")),
            MetricSpec("open_trades", ("metrics", "open_trades")),
            MetricSpec("holding_events", ("metrics", "holding_events")),
            MetricSpec("all_rows", ("metrics", "all_rows")),
            MetricSpec("entered_rows", ("metrics", "entered_rows")),
            MetricSpec("expired_rows", ("metrics", "expired_rows")),
        ),
        excluded_metric_labels=(
            "win_trades",
            "loss_trades",
            "avg_profit_rate",
            "realized_pnl_krw",
            "row-level profit_rate",
        ),
    ),
    SectionPolicy(
        key="performance_tuning",
        label="Performance Tuning",
        remote_path_template="/api/performance-tuning?date={date}&since={since}",
        safe_metrics=(
            MetricSpec("holding_reviews", ("metrics", "holding_reviews")),
            MetricSpec("holding_skips", ("metrics", "holding_skips")),
            MetricSpec("holding_skip_ratio", ("metrics", "holding_skip_ratio")),
            MetricSpec("holding_ai_cache_hit_ratio", ("metrics", "holding_ai_cache_hit_ratio")),
            MetricSpec("holding_review_ms_avg", ("metrics", "holding_review_ms_avg")),
            MetricSpec("holding_review_ms_p95", ("metrics", "holding_review_ms_p95")),
            MetricSpec("holding_skip_ws_age_p95", ("metrics", "holding_skip_ws_age_p95")),
            MetricSpec("gatekeeper_decisions", ("metrics", "gatekeeper_decisions")),
            MetricSpec("gatekeeper_fast_reuse_ratio", ("metrics", "gatekeeper_fast_reuse_ratio")),
            MetricSpec("gatekeeper_ai_cache_hit_ratio", ("metrics", "gatekeeper_ai_cache_hit_ratio")),
            MetricSpec("gatekeeper_eval_ms_avg", ("metrics", "gatekeeper_eval_ms_avg")),
            MetricSpec("gatekeeper_eval_ms_p95", ("metrics", "gatekeeper_eval_ms_p95")),
            MetricSpec("gatekeeper_fast_reuse_ws_age_p95", ("metrics", "gatekeeper_fast_reuse_ws_age_p95")),
            MetricSpec("gatekeeper_action_age_p95", ("metrics", "gatekeeper_action_age_p95")),
            MetricSpec("gatekeeper_allow_entry_age_p95", ("metrics", "gatekeeper_allow_entry_age_p95")),
            MetricSpec("gatekeeper_bypass_evaluation_samples", ("metrics", "gatekeeper_bypass_evaluation_samples")),
            MetricSpec("exit_signals", ("metrics", "exit_signals")),
            MetricSpec("dual_persona_shadow_samples", ("metrics", "dual_persona_shadow_samples")),
            MetricSpec("dual_persona_gatekeeper_samples", ("metrics", "dual_persona_gatekeeper_samples")),
            MetricSpec("dual_persona_overnight_samples", ("metrics", "dual_persona_overnight_samples")),
            MetricSpec("dual_persona_conflict_ratio", ("metrics", "dual_persona_conflict_ratio")),
            MetricSpec("dual_persona_conservative_veto_ratio", ("metrics", "dual_persona_conservative_veto_ratio")),
            MetricSpec("dual_persona_extra_ms_p95", ("metrics", "dual_persona_extra_ms_p95")),
            MetricSpec("dual_persona_fused_override_ratio", ("metrics", "dual_persona_fused_override_ratio")),
        ),
    ),
    SectionPolicy(
        key="post_sell_feedback",
        label="Post Sell Feedback",
        remote_path_template="/api/post-sell-feedback?date={date}",
        safe_metrics=(
            MetricSpec("total_candidates", ("metrics", "total_candidates")),
            MetricSpec("evaluated_candidates", ("metrics", "evaluated_candidates")),
        ),
        excluded_metric_labels=(
            "missed_upside_rate",
            "good_exit_rate",
            "avg_realized_profit_rate",
            "avg_extra_upside_10m_pct",
            "median_extra_upside_10m_pct",
            "avg_close_after_sell_10m_pct",
            "capture_efficiency_avg_pct",
            "estimated_extra_upside_10m_krw_sum",
            "estimated_extra_upside_10m_krw_avg",
            "timing_tuning_pressure_score",
            "case-level profit_rate",
        ),
    ),
    SectionPolicy(
        key="entry_pipeline_flow",
        label="Entry Pipeline Flow",
        remote_path_template="/api/entry-pipeline-flow?date={date}&since={since}&top=10",
        safe_metrics=(
            MetricSpec("total_events", ("metrics", "total_events")),
            MetricSpec("tracked_stocks", ("metrics", "tracked_stocks")),
            MetricSpec("submitted_stocks", ("metrics", "submitted_stocks")),
            MetricSpec("blocked_stocks", ("metrics", "blocked_stocks")),
            MetricSpec("waiting_stocks", ("metrics", "waiting_stocks")),
        ),
    ),
    SectionPolicy(
        key="strategy_performance",
        label="Strategy Performance",
        remote_path_template="/api/strategy-performance?date={date}",
        safe_metrics=(
            MetricSpec("completed_count", ("summary", "completed_count")),
            MetricSpec("entered_count", ("summary", "entered_count")),
            MetricSpec("open_count", ("summary", "open_count")),
            MetricSpec("strategy_count", ("summary", "strategy_count")),
            MetricSpec("tag_group_count", ("summary", "tag_group_count")),
        ),
        excluded_metric_labels=(
            "realized_pnl_krw",
            "avg_profit_rate",
            "strategy row outcomes.avg_profit_rate",
            "strategy row outcomes.realized_pnl_krw",
            "trend summaries based on profit_rate",
        ),
    ),
)


def _safe_get(payload: Any, path: tuple[str, ...]) -> Any:
    cursor = payload
    for part in path:
        if not isinstance(cursor, dict) or part not in cursor:
            return None
        cursor = cursor.get(part)
    return cursor


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _fetch_json(url: str) -> JsonDict:
    with urllib.request.urlopen(url, timeout=20) as response:
        raw = response.read().decode("utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return payload


def _normalize_base_url(base_url: str) -> str:
    return str(base_url or "").rstrip("/")


def _build_remote_url(base_url: str, template: str, *, target_date: str, since_time: str | None) -> str:
    resolved_since = urllib.parse.quote(since_time or "09:00:00", safe=":")
    return f"{_normalize_base_url(base_url)}{template.format(date=target_date, since=resolved_since)}"


def _summarize_named_counts(rows: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    summary: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        name = (
            item.get("label")
            or item.get("name")
            or item.get("stage")
            or item.get("key")
            or item.get("reason")
        )
        count = item.get("count")
        ratio = item.get("ratio")
        if not name:
            continue
        entry = {"name": str(name)}
        if _is_number(count):
            entry["count"] = int(count) if float(count).is_integer() else round(float(count), 3)
        if _is_number(ratio):
            entry["ratio"] = round(float(ratio), 3)
        summary.append(entry)
        if len(summary) >= limit:
            break
    return summary


def _summarize_watch_items(rows: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    summary: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        value = item.get("value")
        target = item.get("target")
        if not label:
            continue
        summary.append({"label": str(label), "value": value, "target": target})
        if len(summary) >= limit:
            break
    return summary


def _compare_metrics(local_payload: JsonDict, remote_payload: JsonDict, policy: SectionPolicy) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in policy.safe_metrics:
        local_value = _safe_get(local_payload, spec.path)
        remote_value = _safe_get(remote_payload, spec.path)
        row: dict[str, Any] = {
            "label": spec.label,
            "local": local_value,
            "remote": remote_value,
        }
        if _is_number(local_value) and _is_number(remote_value):
            row["delta_remote_minus_local"] = round(float(remote_value) - float(local_value), 4)
        rows.append(row)
    return rows


def _build_section_result(
    policy: SectionPolicy,
    *,
    local_payload: JsonDict | None,
    remote_payload: JsonDict | None,
    local_error: str | None = None,
    remote_error: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "label": policy.label,
        "status": "ok",
        "excluded_metric_labels": list(policy.excluded_metric_labels),
        "safe_metric_rows": [],
        "distribution_refs": {},
    }
    if local_error:
        result["status"] = "local_error"
        result["local_error"] = local_error
    if remote_error:
        result["status"] = "remote_error" if result["status"] == "ok" else f"{result['status']}+remote_error"
        result["remote_error"] = remote_error
    if local_payload is None or remote_payload is None:
        return result

    result["safe_metric_rows"] = _compare_metrics(local_payload, remote_payload, policy)

    if policy.key == "entry_pipeline_flow":
        result["distribution_refs"]["local_blocker_breakdown"] = _summarize_named_counts(local_payload.get("blocker_breakdown"))
        result["distribution_refs"]["remote_blocker_breakdown"] = _summarize_named_counts(remote_payload.get("blocker_breakdown"))
        result["distribution_refs"]["local_latest_stage_breakdown"] = _summarize_named_counts(local_payload.get("latest_stage_breakdown"))
        result["distribution_refs"]["remote_latest_stage_breakdown"] = _summarize_named_counts(remote_payload.get("latest_stage_breakdown"))
    elif policy.key == "performance_tuning":
        result["distribution_refs"]["local_watch_items"] = _summarize_watch_items(local_payload.get("watch_items"))
        result["distribution_refs"]["remote_watch_items"] = _summarize_watch_items(remote_payload.get("watch_items"))

    return result


def compare_server_reports(
    *,
    target_date: str,
    remote_base_url: str,
    since_time: str | None = "09:00:00",
    include_sections: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    selected = {item for item in (include_sections or tuple(policy.key for policy in SECTION_POLICIES))}
    results: dict[str, Any] = {
        "date": target_date,
        "remote_base_url": _normalize_base_url(remote_base_url),
        "since_time": since_time,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "policy": {
            "safe_only": True,
            "reason": "profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison",
        },
        "sections": {},
    }

    for policy in SECTION_POLICIES:
        if policy.key not in selected:
            continue

        local_payload: JsonDict | None = None
        remote_payload: JsonDict | None = None
        local_error: str | None = None
        remote_error: str | None = None

        loader = LOCAL_LOADERS[policy.key]
        try:
            local_payload = loader(target_date, since_time)
        except Exception as exc:  # pragma: no cover - exercised in integration use
            local_error = f"{type(exc).__name__}: {exc}"

        remote_url = _build_remote_url(
            remote_base_url,
            policy.remote_path_template,
            target_date=target_date,
            since_time=since_time,
        )
        try:
            remote_payload = _fetch_json(remote_url)
        except Exception as exc:  # pragma: no cover - exercised in integration use
            remote_error = f"{type(exc).__name__}: {exc}"

        results["sections"][policy.key] = _build_section_result(
            policy,
            local_payload=local_payload,
            remote_payload=remote_payload,
            local_error=local_error,
            remote_error=remote_error,
        )
        results["sections"][policy.key]["remote_url"] = remote_url

    return results


def render_markdown_report(comparison: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Server Comparison ({comparison.get('date')})")
    lines.append("")
    lines.append(f"- remote: `{comparison.get('remote_base_url')}`")
    lines.append(f"- since: `{comparison.get('since_time')}`")
    lines.append(f"- policy: `{comparison.get('policy', {}).get('reason', '-')}`")

    for section_key, section in (comparison.get("sections") or {}).items():
        lines.append("")
        lines.append(f"## {section.get('label', section_key)}")
        lines.append(f"- status: `{section.get('status', 'unknown')}`")
        if section.get("remote_url"):
            lines.append(f"- remote_url: `{section['remote_url']}`")
        if section.get("local_error"):
            lines.append(f"- local_error: `{section['local_error']}`")
        if section.get("remote_error"):
            lines.append(f"- remote_error: `{section['remote_error']}`")
        excluded = section.get("excluded_metric_labels") or []
        if excluded:
            lines.append(f"- excluded_from_criteria: `{', '.join(excluded)}`")
        rows = section.get("safe_metric_rows") or []
        if rows:
            lines.append("")
            lines.append("| metric | local | remote | delta(remote-local) |")
            lines.append("| --- | ---: | ---: | ---: |")
            for row in rows:
                delta = row.get("delta_remote_minus_local")
                delta_text = "-" if delta is None else str(delta)
                lines.append(
                    f"| `{row['label']}` | `{row.get('local')}` | `{row.get('remote')}` | `{delta_text}` |"
                )
        refs = section.get("distribution_refs") or {}
        for ref_key, ref_rows in refs.items():
            if not ref_rows:
                continue
            lines.append("")
            lines.append(f"- {ref_key}:")
            for item in ref_rows:
                compact = ", ".join(f"{k}={v}" for k, v in item.items())
                lines.append(f"  - `{compact}`")

    lines.append("")
    return "\n".join(lines)


def build_snapshot_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    summary_sections: list[dict[str, Any]] = []
    sections = comparison.get("sections") or {}
    for section_key, section in sections.items():
        safe_rows = list(section.get("safe_metric_rows") or [])
        differing_rows = [row for row in safe_rows if row.get("delta_remote_minus_local") not in (None, 0, 0.0)]
        differing_rows.sort(key=lambda row: abs(float(row.get("delta_remote_minus_local") or 0.0)), reverse=True)
        top_diffs = [
            {
                "label": row.get("label"),
                "local": row.get("local"),
                "remote": row.get("remote"),
                "delta_remote_minus_local": row.get("delta_remote_minus_local"),
            }
            for row in differing_rows[:5]
        ]
        summary_sections.append(
            {
                "key": section_key,
                "label": section.get("label", section_key),
                "status": section.get("status", "unknown"),
                "safe_metric_count": len(safe_rows),
                "differing_metric_count": len(differing_rows),
                "top_diffs": top_diffs,
            }
        )

    return {
        "date": comparison.get("date"),
        "remote_base_url": comparison.get("remote_base_url"),
        "since_time": comparison.get("since_time"),
        "generated_at": comparison.get("generated_at"),
        "policy_reason": (comparison.get("policy") or {}).get("reason", ""),
        "sections": summary_sections,
    }


def render_checklist_append_block(
    comparison: dict[str, Any],
    *,
    report_relpath: str,
) -> str:
    summary = build_snapshot_summary(comparison)
    lines: list[str] = []
    lines.append(
        f"### 본서버 vs songstockscan 자동 비교 (`{summary.get('generated_at') or summary.get('date')}`)"
    )
    lines.append("")
    lines.append(f"- 기준: `{summary.get('policy_reason') or '-'}`")
    lines.append(f"- 상세 리포트: `{report_relpath}`")
    for section in summary.get("sections") or []:
        label = section.get("label", "-")
        status = section.get("status", "unknown")
        diff_count = section.get("differing_metric_count", 0)
        top_diffs = section.get("top_diffs") or []
        if top_diffs:
            diff_text = "; ".join(
                f"{item['label']} local={item['local']} remote={item['remote']} delta={item['delta_remote_minus_local']}"
                for item in top_diffs[:3]
            )
        else:
            diff_text = "safe 기준 차이 없음"
        lines.append(f"- `{label}`: status=`{status}`, differing_safe_metrics=`{diff_count}`")
        lines.append(f"  - {diff_text}")
    lines.append("")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare local KORStockScan reports with a remote server.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD")
    parser.add_argument(
        "--remote-base-url",
        default="https://songstockscan.ddns.net",
        help="Remote base URL",
    )
    parser.add_argument(
        "--since",
        default="09:00:00",
        help="Since time used by pipeline/performance endpoints",
    )
    parser.add_argument(
        "--sections",
        nargs="*",
        default=[policy.key for policy in SECTION_POLICIES],
        help="Subset of sections to compare",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument("--output", help="Optional output file path")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    comparison = compare_server_reports(
        target_date=args.date,
        remote_base_url=args.remote_base_url,
        since_time=args.since,
        include_sections=tuple(args.sections or []),
    )
    rendered = (
        json.dumps(comparison, ensure_ascii=False, indent=2)
        if args.format == "json"
        else render_markdown_report(comparison)
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
