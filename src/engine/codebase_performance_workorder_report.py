"""Build report-only workorder source from codebase performance analysis."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "data" / "report" / "codebase_performance_workorder"
SOURCE_DOC = PROJECT_ROOT / "docs" / "codebase-performance-bottleneck-analysis.md"
SCHEMA_VERSION = 1

FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "provider_route_change",
    "broker_order_guard_change",
    "bot_restart",
    "tuning_axis_change",
    "source_quality_policy_change",
    "raw_forensic_stream_suppression",
]

IMPLEMENTATION_CHECKS: dict[str, list[dict[str, Any]]] = {
    "order_perf_buy_funnel_json_scan": [
        {
            "path": "src/engine/buy_funnel_sentinel.py",
            "tokens": ["load_pipeline_event_summaries", "--use-summary"],
        }
    ],
    "order_perf_daily_report_bulk_history": [
        {
            "path": "src/engine/daily_report_service.py",
            "tokens": ["history_rows", "history_by_code"],
        }
    ],
    "order_perf_daily_report_engine_singleton": [
        {
            "path": "src/engine/daily_report_service.py",
            "tokens": ["_ENGINE_CACHE", "def _get_engine"],
        }
    ],
    "order_perf_recommend_update_vectorization": [
        {
            "path": "src/model/recommend_daily_v2.py",
            "tokens": ["pd.MultiIndex.from_frame", ".isin(selected_index)"],
        },
        {
            "path": "src/utils/update_kospi.py",
            "tokens": ["pd.MultiIndex.from_frame", "row_keys.isin(existing_index)"],
        },
    ],
    "order_perf_swing_simulation_iteration": [
        {
            "path": "src/engine/swing_daily_simulation_report.py",
            "tokens": ["_quote_groups_by_code", 'to_dict("records")'],
            "forbidden_tokens": ["for _, row in recommendations.iterrows()"],
        }
    ],
    "order_perf_monitor_snapshot_stream_tail": [
        {
            "path": "src/engine/monitor_snapshot_runtime.py",
            "tokens": ["TAIL_READ_BYTES", "reversed(text.splitlines())"],
        }
    ],
    "order_perf_final_ensemble_records": [
        {
            "path": "src/scanners/final_ensemble_scanner.py",
            "tokens": ['to_dict("records")'],
            "forbidden_tokens": ["iterrows()"],
        }
    ],
    "order_perf_sentinel_event_cache_incremental_review": [
        {
            "path": "src/tests/test_sentinel_event_cache_parity.py",
            "tokens": [
                "test_incremental_cache_parity_for_malformed_partial_unchanged_and_appended_jsonl",
                "test_buy_sentinel_raw_cache_report_parity",
                "test_holding_exit_sentinel_raw_cache_report_parity",
            ],
        }
    ],
}


def _base_candidate(
    *,
    item_id: str,
    title: str,
    risk_tier: str,
    target_subsystem: str,
    files_likely_touched: list[str],
    acceptance_tests: list[str],
    parity_contract: str,
    priority: int,
    state: str,
    defer_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "order_id": item_id,
        "title": title,
        "risk_tier": risk_tier,
        "target_subsystem": target_subsystem,
        "source_report_type": "codebase_performance_workorder",
        "lifecycle_stage": "ops_performance",
        "route": "performance_optimization_order",
        "confidence": "consensus",
        "priority": priority,
        "candidate_state": state,
        "runtime_effect": False,
        "strategy_effect": False,
        "data_quality_effect": False,
        "tuning_axis_effect": False,
        "forbidden_uses": list(FORBIDDEN_USES),
        "files_likely_touched": files_likely_touched,
        "acceptance_tests": acceptance_tests,
        "parity_contract": parity_contract,
        "defer_reason": defer_reason,
    }


def _accepted_candidates() -> list[dict[str, Any]]:
    return [
        _base_candidate(
            item_id="order_perf_buy_funnel_json_scan",
            title="BUY funnel sentinel field scan without repeated json.dumps",
            risk_tier="low",
            target_subsystem="buy_funnel_sentinel",
            files_likely_touched=["src/engine/buy_funnel_sentinel.py"],
            acceptance_tests=[
                "pytest src/tests/test_buy_funnel_sentinel.py",
                "BUY Sentinel classification parity on same raw/cache input",
            ],
            parity_contract=(
                "classification, blocker counts, unique submitted count, actual_order_submitted split, "
                "source-quality/provenance fields exact match"
            ),
            priority=1,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_daily_report_bulk_history",
            title="Daily report market snapshot bulk history query",
            risk_tier="medium",
            target_subsystem="daily_report",
            files_likely_touched=["src/engine/daily_report_service.py"],
            acceptance_tests=[
                "pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py",
                "daily report output parity on injected DB/model fixture",
            ],
            parity_contract="per-stock history window, feature columns, model input row count, and report JSON exact match",
            priority=2,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_daily_report_engine_singleton",
            title="Daily report SQLAlchemy engine singleton",
            risk_tier="low",
            target_subsystem="daily_report",
            files_likely_touched=["src/engine/daily_report_service.py"],
            acceptance_tests=[
                "pytest src/tests/test_daily_report_service.py src/tests/test_daily_report.py",
                "engine creation count regression test",
            ],
            parity_contract="query result and rendered daily report exact match",
            priority=3,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_recommend_update_vectorization",
            title="Recommendation and update_kospi vectorized membership checks",
            risk_tier="low",
            target_subsystem="swing_daily_recommendation",
            files_likely_touched=[
                "src/model/recommend_daily_v2.py",
                "src/utils/update_kospi.py",
            ],
            acceptance_tests=[
                "pytest src/tests/test_swing_retrain_automation.py src/tests/test_swing_feature_ssot.py",
                "recommendation CSV and diagnostics parity",
            ],
            parity_contract="selected keys, diagnostics rows, CSV row order, and update_kospi inserted-row set exact match",
            priority=4,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_swing_simulation_iteration",
            title="Swing simulation iteration and quote grouping",
            risk_tier="medium",
            target_subsystem="swing_daily_simulation",
            files_likely_touched=["src/engine/swing_daily_simulation_report.py"],
            acceptance_tests=[
                "pytest src/tests/test_swing_model_selection_funnel_repair.py",
                "swing simulation JSON parity on injected sources",
            ],
            parity_contract="selection funnel, lifecycle arms, gate counterfactuals, and runtime funnel summary exact match",
            priority=5,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_monitor_snapshot_stream_tail",
            title="Monitor snapshot runtime streaming tail read",
            risk_tier="low",
            target_subsystem="monitor_snapshot",
            files_likely_touched=["src/engine/monitor_snapshot_runtime.py"],
            acceptance_tests=[
                "pytest src/tests/test_log_archive_service.py",
                "last valid JSON line parity",
            ],
            parity_contract="latest parsed snapshot payload and missing/malformed fallback behavior exact match",
            priority=6,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_final_ensemble_records",
            title="Final ensemble scanner records conversion without iterrows",
            risk_tier="low",
            target_subsystem="final_ensemble_scanner",
            files_likely_touched=["src/scanners/final_ensemble_scanner.py"],
            acceptance_tests=[
                "pytest src/tests/test_swing_model_selection_funnel_repair.py",
                "V2 CSV pick list parity",
            ],
            parity_contract="Code/Name record list, selection count, and diagnostics output exact match",
            priority=7,
            state="accepted",
        ),
        _base_candidate(
            item_id="order_perf_sentinel_event_cache_incremental_review",
            title="Sentinel event cache incremental parse review",
            risk_tier="medium",
            target_subsystem="sentinel_event_cache",
            files_likely_touched=[
                "src/engine/sentinel_event_cache.py",
                "src/tests/test_sentinel_event_cache_parity.py",
            ],
            acceptance_tests=[
                "pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py",
                "pytest src/tests/test_sentinel_event_cache_parity.py",
            ],
            parity_contract=(
                "cached row ordering, malformed-line tolerance, source-quality fields, and empty/no-new-event "
                "fallback behavior exact match"
            ),
            priority=8,
            state="accepted",
        ),
    ]


def _deferred_candidates() -> list[dict[str, Any]]:
    return [
        _base_candidate(
            item_id="order_perf_kiwoom_orders_http_session_review",
            title="Kiwoom orders HTTP session reuse manual review",
            risk_tier="high",
            target_subsystem="broker_transport",
            files_likely_touched=["src/engine/kiwoom_orders.py"],
            acceptance_tests=[
                "pytest src/tests/test_kiwoom_orders.py src/tests/test_sniper_scale_in.py"
            ],
            parity_contract="request headers/body/api-id, timeout, retry, auth failure handling, and receipt parsing exact match",
            priority=20,
            state="deferred",
            defer_reason="broker request lifecycle may change; requires manual review before implementation",
        ),
        _base_candidate(
            item_id="order_perf_config_cache_scope_review",
            title="Config cache scope review",
            risk_tier="medium",
            target_subsystem="config_loading",
            files_likely_touched=[
                "src/utils/constants.py",
                "src/utils/kiwoom_utils.py",
            ],
            acceptance_tests=["pytest config/import smoke tests"],
            parity_contract="runtime config reload semantics must be explicitly preserved or limited to one-shot/postclose modules",
            priority=21,
            state="deferred",
            defer_reason="runtime config reload semantics are not yet bounded",
        ),
    ]


def _rejected_candidates() -> list[dict[str, Any]]:
    return [
        _base_candidate(
            item_id="order_perf_kiwoom_ws_tick_parse_fastpath",
            title="Kiwoom websocket tick parsing fast path",
            risk_tier="high",
            target_subsystem="quote_data_quality",
            files_likely_touched=["src/engine/kiwoom_websocket.py"],
            acceptance_tests=["pytest websocket parsing/data-quality tests"],
            parity_contract="quote fields, orderbook levels, stale quote behavior, and source-quality flags exact match",
            priority=30,
            state="rejected",
            defer_reason="quote/data-quality semantics can change; requires separate data-quality approval owner",
        ),
        _base_candidate(
            item_id="order_perf_raw_event_suppression_out_of_scope",
            title="Raw pipeline event suppression out of scope",
            risk_tier="high",
            target_subsystem="pipeline_event_storage",
            files_likely_touched=["src/utils/pipeline_event_logger.py"],
            acceptance_tests=["pytest pipeline event verbosity tests"],
            parity_contract="must follow existing V2 parity and approval guard; not part of this performance workorder source",
            priority=31,
            state="rejected",
            defer_reason="raw suppression is governed by pipeline event V2 suppress guard",
        ),
    ]


def output_paths(target_date: str) -> tuple[Path, Path]:
    base = f"codebase_performance_workorder_{target_date}"
    return REPORT_DIR / f"{base}.json", REPORT_DIR / f"{base}.md"


def _source_doc_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _implementation_probe(item_id: str) -> dict[str, Any]:
    checks = IMPLEMENTATION_CHECKS.get(item_id) or []
    if not checks:
        return {"implementation_status": "not_checked", "implementation_checks": []}
    results: list[dict[str, Any]] = []
    for check in checks:
        rel_path = str(check.get("path") or "")
        path = PROJECT_ROOT / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        required = [str(token) for token in check.get("tokens") or []]
        forbidden = [str(token) for token in check.get("forbidden_tokens") or []]
        missing = [token for token in required if token not in text]
        present_forbidden = [token for token in forbidden if token in text]
        results.append(
            {
                "path": rel_path,
                "exists": path.exists(),
                "required_tokens_present": not missing,
                "missing_tokens": missing,
                "forbidden_tokens_absent": not present_forbidden,
                "present_forbidden_tokens": present_forbidden,
            }
        )
    implemented = bool(results) and all(
        item["exists"]
        and item["required_tokens_present"]
        and item["forbidden_tokens_absent"]
        for item in results
    )
    return {
        "implementation_status": "implemented" if implemented else "pending",
        "implementation_checks": results,
    }


def build_codebase_performance_workorder_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_hash = _source_doc_hash(SOURCE_DOC)
    accepted = _accepted_candidates()
    accepted = [
        {**item, **_implementation_probe(str(item.get("item_id") or ""))}
        for item in accepted
    ]
    deferred = _deferred_candidates()
    rejected = _rejected_candidates()
    implemented_count = sum(
        1 for item in accepted if item.get("implementation_status") == "implemented"
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "codebase_performance_workorder",
        "source_doc": str(SOURCE_DOC),
        "source_doc_exists": SOURCE_DOC.exists(),
        "source_doc_hash": source_hash,
        "policy": {
            "runtime_effect": False,
            "strategy_effect": False,
            "data_quality_effect": False,
            "tuning_axis_effect": False,
            "decision_authority": "ops_performance_workorder_source",
            "workorder_only": True,
            "implementation_requires_user_instruction": True,
            "forbidden_uses": list(FORBIDDEN_USES),
        },
        "summary": {
            "accepted_count": len(accepted),
            "implemented_count": implemented_count,
            "pending_accepted_count": len(accepted) - implemented_count,
            "deferred_count": len(deferred),
            "rejected_count": len(rejected),
            "source_doc_hash": source_hash,
        },
        "accepted_candidates": accepted,
        "deferred_candidates": deferred,
        "rejected_candidates": rejected,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = output_paths(target_date)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Codebase Performance Workorder Source - {report.get('date')}",
        "",
        "## Policy",
        "- authority: `ops_performance_workorder_source`",
        "- runtime_effect: `false`",
        "- strategy_effect: `false`",
        "- data_quality_effect: `false`",
        "- tuning_axis_effect: `false`",
        "- implementation requires explicit user instruction",
        "",
        "## Summary",
        f"- source_doc: `{report.get('source_doc')}`",
        f"- source_doc_hash: `{summary.get('source_doc_hash')}`",
        f"- accepted/implemented/pending/deferred/rejected: `{summary.get('accepted_count')}` / `{summary.get('implemented_count')}` / `{summary.get('pending_accepted_count')}` / `{summary.get('deferred_count')}` / `{summary.get('rejected_count')}`",
        "",
        "## Accepted Candidates",
    ]
    for item in report.get("accepted_candidates") or []:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('item_id')}` priority=`{item.get('priority')}` risk=`{item.get('risk_tier')}` "
                f"subsystem=`{item.get('target_subsystem')}` implementation_status=`{item.get('implementation_status')}`"
            )
    lines.extend(["", "## Deferred Candidates"])
    for item in report.get("deferred_candidates") or []:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('item_id')}` reason=`{item.get('defer_reason')}`"
            )
    lines.extend(["", "## Rejected Candidates"])
    for item in report.get("rejected_candidates") or []:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('item_id')}` reason=`{item.get('defer_reason')}`"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build codebase performance workorder source report."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args(argv)
    report = build_codebase_performance_workorder_report(args.target_date)
    json_path, md_path = output_paths(args.target_date)
    result = {
        "status": "success",
        "target_date": args.target_date,
        "artifacts": {"json": str(json_path), "markdown": str(md_path)},
        "accepted_count": len(report.get("accepted_candidates") or []),
        "deferred_count": len(report.get("deferred_candidates") or []),
        "rejected_count": len(report.get("rejected_candidates") or []),
    }
    print(
        json.dumps(
            result if args.print_json else result,
            ensure_ascii=False,
            indent=2 if args.print_json else None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
