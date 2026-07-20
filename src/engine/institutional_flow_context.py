"""Build source-only foreign/institutional flow context features.

Kiwoom API access stays in ``src.utils.kiwoom_utils`` and the websocket manager.
This module only orchestrates helper calls, normalizes fields, and writes
postclose/source-only artifacts for lifecycle matrix consumers.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils import kiwoom_utils
from src.utils.jsonl_io import iter_jsonl

REPORT_DIR_PATH = REPORT_DIR / "institutional_flow_context"
PIPELINE_EVENTS_DIR = Path(__file__).resolve().parents[2] / "data" / "pipeline_events"

STATUS_VALUES = {
    "OK",
    "MISSING",
    "STALE",
    "PARSE_ERROR",
    "PARTIAL",
    "RATE_LIMITED",
    "TOKEN_ERROR",
}
RUNTIME_FEATURE_KEYS = [
    "foreign_net_intraday_qty",
    "foreign_net_intraday_amt",
    "institution_net_intraday_qty",
    "institution_net_intraday_amt",
    "foreign_broker_est_net_qty",
    "foreign_broker_est_delta_qty",
    "program_net_qty",
    "program_delta_qty",
    "program_net_amt",
    "foreign_net_roll5",
    "inst_net_roll5",
    "dual_net_buy",
    "smart_money_net",
    "institutional_accumulation_score",
    "institutional_flow_regime",
    "institutional_flow_source",
    "institutional_flow_status",
    "institutional_flow_age_sec",
]


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR_PATH / f"institutional_flow_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(str(value).replace(",", "").replace("+", "")))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_code(code: Any) -> str:
    return str(code or "").strip().lstrip("A")


def _load_pipeline_event_codes(target_date: str, limit: int = 120) -> list[str]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    codes: list[str] = []
    seen: set[str] = set()
    for item in iter_jsonl(path, errors="ignore"):
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        code = _normalize_code(item.get("stock_code") or fields.get("stock_code"))
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
        if len(codes) >= limit:
            break
    return codes


def _ws_age_sec(
    ws_data: dict[str, Any] | None, now_ts: float | None = None
) -> float | None:
    if not isinstance(ws_data, dict):
        return None
    now_ts = float(now_ts or time.time())
    candidates = [
        _safe_float(ws_data.get("last_foreign_broker_update_ts"), 0.0),
        _safe_float(ws_data.get("last_prog_update_ts"), 0.0),
        _safe_float(ws_data.get("last_ws_update_ts"), 0.0),
    ]
    latest = max(candidates)
    if latest <= 0:
        return None
    return round(max(0.0, now_ts - latest), 3)


def normalize_institutional_flow_context(
    code: str,
    *,
    daily_summary: dict[str, Any] | None = None,
    period_summary: dict[str, Any] | None = None,
    intraday_chart_qty: dict[str, Any] | None = None,
    intraday_chart_amt: dict[str, Any] | None = None,
    ws_data: dict[str, Any] | None = None,
    status_hint: str | None = None,
) -> dict[str, Any]:
    """Normalize REST/WS helper outputs into lifecycle runtime features."""
    code = _normalize_code(code)
    daily_summary = daily_summary if isinstance(daily_summary, dict) else {}
    period_summary = period_summary if isinstance(period_summary, dict) else {}
    intraday_chart_qty = (
        intraday_chart_qty if isinstance(intraday_chart_qty, dict) else {}
    )
    intraday_chart_amt = (
        intraday_chart_amt if isinstance(intraday_chart_amt, dict) else {}
    )
    ws_data = ws_data if isinstance(ws_data, dict) else {}

    foreign_intraday_qty = _safe_int(intraday_chart_qty.get("foreign_net"))
    inst_intraday_qty = _safe_int(intraday_chart_qty.get("inst_net"))
    foreign_intraday_amt = _safe_int(intraday_chart_amt.get("foreign_net"))
    inst_intraday_amt = _safe_int(intraday_chart_amt.get("inst_net"))
    foreign_roll5 = _safe_int(period_summary.get("foreign_net"))
    inst_roll5 = _safe_int(period_summary.get("inst_net"))
    smart_money_net = _safe_int(
        daily_summary.get("smart_money_net"), foreign_roll5 + inst_roll5
    )
    broker_net = _safe_int(ws_data.get("foreign_broker_net_est_qty"))
    broker_delta = _safe_int(ws_data.get("foreign_broker_net_est_delta_qty"))
    program_net_qty = _safe_int(ws_data.get("prog_net_qty"))
    program_delta_qty = _safe_int(ws_data.get("prog_delta_qty"))
    program_net_amt = _safe_int(ws_data.get("prog_net_amt"))

    dual_net_buy = foreign_roll5 > 0 and inst_roll5 > 0
    score = 0
    score += 25 if dual_net_buy else 0
    score += 20 if smart_money_net > 0 else 0
    score += 15 if broker_delta > 0 else 0
    score += 15 if program_delta_qty > 0 else 0
    score += 25 if (foreign_intraday_qty + inst_intraday_qty) > 0 else 0
    score = min(100, score)

    if dual_net_buy and score >= 45:
        regime = "DUAL_ACCUMULATION"
    elif foreign_roll5 > 0 or broker_delta > 0:
        regime = "FOREIGN_ACCUMULATION"
    elif inst_roll5 > 0 or inst_intraday_qty > 0:
        regime = "INSTITUTION_ACCUMULATION"
    elif program_delta_qty > 0:
        regime = "PROGRAM_SUPPORT"
    elif smart_money_net < 0 and broker_delta < 0:
        regime = "DISTRIBUTION"
    elif any(
        value for value in (foreign_roll5, inst_roll5, broker_delta, program_delta_qty)
    ):
        regime = "MIXED"
    else:
        regime = "UNKNOWN"

    sources = []
    if daily_summary:
        sources.append("ka10059")
    if period_summary:
        sources.append("ka10061")
    if intraday_chart_qty or intraday_chart_amt:
        sources.append("ka10064")
    if ws_data:
        if "0F" in (ws_data.get("received_types") or set()) or ws_data.get(
            "foreign_broker_net_est_qty"
        ):
            sources.append("WS_0F")
        if "0w" in (ws_data.get("received_types") or set()) or ws_data.get(
            "prog_net_qty"
        ):
            sources.append("WS_0w")

    status = status_hint if status_hint in STATUS_VALUES else None
    if not status:
        status = (
            "OK"
            if {"ka10059", "ka10061"} <= set(sources)
            else "PARTIAL" if sources else "MISSING"
        )

    return {
        "stock_code": code,
        "foreign_net_intraday_qty": foreign_intraday_qty,
        "foreign_net_intraday_amt": foreign_intraday_amt,
        "institution_net_intraday_qty": inst_intraday_qty,
        "institution_net_intraday_amt": inst_intraday_amt,
        "foreign_broker_est_net_qty": broker_net,
        "foreign_broker_est_delta_qty": broker_delta,
        "program_net_qty": program_net_qty,
        "program_delta_qty": program_delta_qty,
        "program_net_amt": program_net_amt,
        "foreign_net_roll5": foreign_roll5,
        "inst_net_roll5": inst_roll5,
        "dual_net_buy": dual_net_buy,
        "smart_money_net": smart_money_net,
        "institutional_accumulation_score": score,
        "institutional_flow_regime": regime,
        "institutional_flow_source": (
            "+".join(dict.fromkeys(sources)) if sources else "none"
        ),
        "institutional_flow_status": status,
        "institutional_flow_age_sec": _ws_age_sec(ws_data),
        "runtime_effect": False,
        "decision_authority": "source_only_lifecycle_feature",
    }


def resolve_institutional_flow_context(
    code: str,
    *,
    token: str | None,
    target_date: str,
    ws_data: dict[str, Any] | None = None,
    live_intraday: bool = False,
) -> dict[str, Any]:
    if not token:
        return normalize_institutional_flow_context(
            code, ws_data=ws_data, status_hint="TOKEN_ERROR"
        )
    code = _normalize_code(code)
    base_dt = str(target_date).replace("-", "")
    start_dt = (datetime.strptime(base_dt, "%Y%m%d") - timedelta(days=7)).strftime(
        "%Y%m%d"
    )
    try:
        daily = kiwoom_utils.get_investor_flow_summary_ka10059(
            token, code, base_dt=base_dt
        )
        period = kiwoom_utils.get_investor_period_total_ka10061(
            token, code, start_dt, base_dt
        )
        chart_qty: dict[str, Any] = {}
        chart_amt: dict[str, Any] = {}
        if live_intraday:
            chart_qty = kiwoom_utils.get_intraday_investor_chart_ka10064(
                token, code, amt_qty_tp="2"
            )
            chart_amt = kiwoom_utils.get_intraday_investor_chart_ka10064(
                token, code, amt_qty_tp="1"
            )
        return normalize_institutional_flow_context(
            code,
            daily_summary=daily,
            period_summary=period,
            intraday_chart_qty=chart_qty,
            intraday_chart_amt=chart_amt,
            ws_data=ws_data,
        )
    except Exception as exc:
        context = normalize_institutional_flow_context(
            code, ws_data=ws_data, status_hint="PARSE_ERROR"
        )
        context["error"] = str(exc)
        return context


def build_institutional_flow_context_report(
    target_date: str,
    *,
    codes: list[str] | None = None,
    token: str | None = None,
    ws_data_by_code: dict[str, dict[str, Any]] | None = None,
    live_intraday: bool = False,
    max_codes: int = 120,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    if codes is None:
        codes = _load_pipeline_event_codes(target_date, limit=max_codes)
    normalized_codes = []
    seen = set()
    for code in codes or []:
        norm = _normalize_code(code)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        normalized_codes.append(norm)
        if len(normalized_codes) >= max_codes:
            break
    if token is None:
        try:
            token = kiwoom_utils.get_kiwoom_token()
        except Exception:
            token = None
    ws_data_by_code = ws_data_by_code if isinstance(ws_data_by_code, dict) else {}
    rows = []
    sleep_sec = max(
        0.0,
        _safe_float(
            os.getenv("KORSTOCKSCAN_INSTITUTIONAL_FLOW_CONTEXT_SLEEP_SEC"), 0.15
        ),
    )
    for idx, code in enumerate(normalized_codes):
        rows.append(
            resolve_institutional_flow_context(
                code,
                token=token,
                target_date=target_date,
                ws_data=ws_data_by_code.get(code),
                live_intraday=live_intraday,
            )
        )
        if sleep_sec > 0 and idx < len(normalized_codes) - 1:
            time.sleep(sleep_sec)
    status_counts = Counter(
        str(row.get("institutional_flow_status") or "MISSING") for row in rows
    )
    source_counts = Counter(
        str(row.get("institutional_flow_source") or "none") for row in rows
    )
    ok_count = status_counts.get("OK", 0)
    top_net_buy = sorted(
        rows, key=lambda row: _safe_int(row.get("smart_money_net")), reverse=True
    )[:10]
    report = {
        "schema_version": 1,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "institutional_flow_context",
        "runtime_effect": False,
        "decision_authority": "source_only_lifecycle_feature",
        "metric_role": "source_quality_feature",
        "forbidden_uses": [
            "single_factor_buy_or_scale_in",
            "broker_guard_override",
            "threshold_mutation",
            "provider_route_mutation",
        ],
        "runtime_feature_keys": RUNTIME_FEATURE_KEYS,
        "summary": {
            "code_count": len(normalized_codes),
            "row_count": len(rows),
            "ok_count": ok_count,
            "partial_count": status_counts.get("PARTIAL", 0),
            "missing_count": status_counts.get("MISSING", 0),
            "token_error_count": status_counts.get("TOKEN_ERROR", 0),
            "parse_error_count": status_counts.get("PARSE_ERROR", 0),
            "join_rate_pct": round((ok_count / len(rows)) * 100.0, 2) if rows else 0.0,
            "source_mix": dict(sorted(source_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "top_net_buy": [
                {
                    "stock_code": row.get("stock_code"),
                    "smart_money_net": row.get("smart_money_net"),
                    "foreign_net_roll5": row.get("foreign_net_roll5"),
                    "inst_net_roll5": row.get("inst_net_roll5"),
                    "regime": row.get("institutional_flow_regime"),
                }
                for row in top_net_buy
            ],
        },
        "rows": rows,
        "warnings": [
            message
            for message in [
                "codes_missing" if not normalized_codes else "",
                "token_error" if status_counts.get("TOKEN_ERROR", 0) else "",
                (
                    "all_rows_missing"
                    if rows and ok_count == 0 and status_counts.get("PARTIAL", 0) == 0
                    else ""
                ),
            ]
            if message
        ],
    }
    REPORT_DIR_PATH.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(
        render_institutional_flow_context_markdown(report), encoding="utf-8"
    )
    return report


def render_institutional_flow_context_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Institutional Flow Context - {report.get('date')}",
        "",
        "- runtime_effect: `False`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        "",
        "## Summary",
        f"- code_count: `{summary.get('code_count')}`",
        f"- row_count: `{summary.get('row_count')}`",
        f"- ok/partial/missing/token_error: `{summary.get('ok_count')}` / `{summary.get('partial_count')}` / `{summary.get('missing_count')}` / `{summary.get('token_error_count')}`",
        f"- join_rate_pct: `{summary.get('join_rate_pct')}`",
        f"- source_mix: `{summary.get('source_mix') or {}}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Top Net Buy",
        "| code | smart_money | foreign_roll5 | inst_roll5 | regime |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary.get("top_net_buy") or []:
        lines.append(
            f"| `{row.get('stock_code')}` | `{row.get('smart_money_net')}` | `{row.get('foreign_net_roll5')}` | `{row.get('inst_net_roll5')}` | `{row.get('regime')}` |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build source-only institutional flow context artifact."
    )
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--code", action="append", default=[])
    parser.add_argument("--max-codes", type=int, default=120)
    parser.add_argument("--live-intraday", action="store_true")
    args = parser.parse_args(argv)
    report = build_institutional_flow_context_report(
        args.date,
        codes=args.code or None,
        live_intraday=bool(args.live_intraday),
        max_codes=args.max_codes,
    )
    print(
        json.dumps(
            {
                "date": report.get("date"),
                "summary": report.get("summary"),
                "warnings": report.get("warnings"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
