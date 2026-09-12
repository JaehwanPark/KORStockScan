"""Daily strategy/position-tag performance mart and report builder."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from sqlalchemy import delete

from src.database.db_manager import DBManager
from src.database.models import StrategyPositionPerformanceDaily, TradePerformanceFact
from src.engine.ai_response_contracts import normalize_gatekeeper_action_key
from src.engine.sniper_position_tags import normalize_position_tag, normalize_strategy
from src.engine.sniper_trade_review_report import build_trade_review_report
from src.engine.trade_profit import (
    calculate_net_profit_rate,
    calculate_net_realized_pnl,
    get_trade_cost_rate,
)

_DB = DBManager()
_PIPELINE_EVENTS_DIR = Path("data/pipeline_events")
_FACT_SYNC_STATUS_DIR = Path("data/report/strategy_position_fact_sync")
_SCANNER_PROMOTION_STAGES = {
    "scalping_scanner_candidate_promoted",
    "scalping_scanner_runtime_target_attach",
}
_NOT_APPLICABLE_VALUES = {
    "",
    "-",
    "none",
    "null",
    "not_applicable",
    "not_applicable_scanner_promotion_id",
    "not_applicable_scanner_promotion_reason",
    "not_applicable_source_signature",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _optional_float(value: Any) -> float | None:
    if value in (None, "", "-", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    if value in (None, "", "-", "None"):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class FactSyncSourceError(RuntimeError):
    """A source-wide fact-sync contract failure that must preserve prior facts."""


def _is_completed(fact: dict[str, Any]) -> bool:
    return str(fact.get("status") or "").upper() == "COMPLETED"


def _has_complete_economics(fact: dict[str, Any]) -> bool:
    if not _is_completed(fact):
        return False
    try:
        return bool(
            float(fact.get("buy_price") or 0) > 0
            and int(fact.get("buy_qty") or 0) > 0
            and fact.get("buy_time") is not None
            and float(fact.get("sell_price") or 0) > 0
            and fact.get("sell_time") is not None
            and fact.get("profit_rate") is not None
            and fact.get("realized_pnl_krw") is not None
        )
    except (TypeError, ValueError):
        return False


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _status_path(target_date: str) -> Path:
    return (
        _FACT_SYNC_STATUS_DIR / f"strategy_position_fact_sync_{target_date}.status.json"
    )


def _write_status(target_date: str, payload: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema_version": 1,
        "report_type": "strategy_position_fact_sync",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "cost_basis": {
            "kind": "fixed_comparison_cost_model",
            "trade_cost_rate": get_trade_cost_rate(),
            "broker_cost_reconciled": False,
        },
        **payload,
    }
    receipt["artifact_sha256"] = _canonical_sha256(receipt)
    path = _status_path(target_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, ensure_ascii=False, indent=2, default=str)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return receipt


def _parse_datetime(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if "T" in raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except Exception:
            pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def _parse_date(value: Any) -> date:
    raw = str(value or "").strip()
    if raw:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    return datetime.now().date()


def _clean_scanner_value(value: Any) -> str:
    text = str(value or "").strip()
    if text.lower() in _NOT_APPLICABLE_VALUES:
        return ""
    return text


def _scanner_discovery_type(fields: dict[str, Any]) -> str:
    reason = _clean_scanner_value(fields.get("scanner_promotion_reason")).lower()
    source_signature = _clean_scanner_value(fields.get("source_signature")).upper()
    source_role = _clean_scanner_value(
        fields.get("scanner_source_role") or fields.get("scanner_candidate_role")
    ).lower()
    priority_tier = _clean_scanner_value(fields.get("scanner_priority_tier")).lower()
    lineage = _clean_scanner_value(fields.get("rising_missed_lineage")).lower()

    if (
        lineage
        or "LOW_REBOUND_RISING_MISSED" in source_signature
        or "low_rebound" in reason
    ):
        return "low_rebound_rising_missed"
    if reason in {"price_jump_multisource_confirmation"}:
        return "price_volume_confirmation"
    if reason in {"price_jump_breakout_confirmation"}:
        return "price_breakout_confirmation"
    if reason in {"price_jump_start_acceleration", "new_price_jump_start_source"}:
        return "price_jump_acceleration"
    if "rank_jump" in reason or "realtime_rank" in reason:
        return "rank_acceleration"
    if "execution_strength" in reason:
        return "execution_strength"
    if reason in {"spike_rate_acceleration", "priority_score_acceleration"}:
        return "general_acceleration"
    if (
        "BID_IMBALANCE_SURGE" in source_signature
        and source_signature == "BID_IMBALANCE_SURGE"
    ):
        return "bid_imbalance_only"
    if (
        source_role in {"late_confirmation", "liquidity_enrichment_only"}
        or priority_tier == "tier_d_late_rank_only"
    ):
        return "late_rank_or_liquidity"
    if reason:
        return reason
    if priority_tier:
        return priority_tier
    return "unknown_scanner_provenance"


def _load_scanner_promotion_events(target_date: str) -> dict[str, list[dict[str, Any]]]:
    path = _PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not path.exists():
        return by_code
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except Exception:
                continue
            if event.get("stage") not in _SCANNER_PROMOTION_STAGES:
                continue
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            promotion_reason = _clean_scanner_value(
                fields.get("scanner_promotion_reason")
            )
            source_signature = _clean_scanner_value(fields.get("source_signature"))
            promotion_id = _clean_scanner_value(fields.get("scanner_promotion_id"))
            if not (promotion_reason or source_signature or promotion_id):
                continue
            stock_code = str(
                event.get("stock_code") or fields.get("stock_code") or ""
            ).strip()[:10]
            if not stock_code:
                continue
            emitted_at = _parse_datetime(
                event.get("emitted_at") or event.get("event_time")
            )
            payload = {
                "stock_code": stock_code,
                "emitted_at": emitted_at,
                "scanner_promotion_id": promotion_id,
                "scanner_promotion_reason": promotion_reason,
                "source_signature": source_signature,
                "scanner_source_role": _clean_scanner_value(
                    fields.get("scanner_source_role")
                    or fields.get("scanner_candidate_role")
                ),
                "scanner_priority_tier": _clean_scanner_value(
                    fields.get("scanner_priority_tier")
                ),
                "rising_missed_lineage": _clean_scanner_value(
                    fields.get("rising_missed_lineage")
                ),
            }
            payload["scanner_discovery_type"] = _scanner_discovery_type(payload)
            by_code[stock_code].append(payload)
    for events in by_code.values():
        events.sort(key=lambda item: item.get("emitted_at") or datetime.min)
    return by_code


def _select_scanner_event_for_trade(
    fact: dict[str, Any],
    events_by_code: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    if fact.get("strategy") != "SCALPING" or fact.get("position_tag") != "SCANNER":
        return None
    events = events_by_code.get(str(fact.get("stock_code") or "").strip()[:10]) or []
    if not events:
        return None
    buy_time = fact.get("buy_time")
    if isinstance(buy_time, str):
        buy_time = _parse_datetime(buy_time)
    if isinstance(buy_time, datetime):
        before = [
            event
            for event in events
            if event.get("emitted_at") and event["emitted_at"] <= buy_time
        ]
        if before:
            return before[-1]
    # A promotion emitted after the BUY is not causal evidence for that BUY.
    # Keep the source gap visible instead of assigning a future event.
    return None


def _enrich_scanner_provenance(
    facts: list[dict[str, Any]],
    target_date: str,
) -> list[dict[str, Any]]:
    events_by_code = _load_scanner_promotion_events(target_date)
    enriched: list[dict[str, Any]] = []
    for fact in facts:
        row = dict(fact)
        event = _select_scanner_event_for_trade(row, events_by_code)
        if event:
            row.update(
                {
                    "scanner_provenance_status": "matched",
                    "scanner_discovery_type": event.get("scanner_discovery_type")
                    or "unknown_scanner_provenance",
                    "scanner_promotion_id": event.get("scanner_promotion_id") or "",
                    "scanner_promotion_reason": event.get("scanner_promotion_reason")
                    or "",
                    "scanner_source_signature": event.get("source_signature") or "",
                    "scanner_source_role": event.get("scanner_source_role") or "",
                    "scanner_priority_tier": event.get("scanner_priority_tier") or "",
                    "rising_missed_lineage": event.get("rising_missed_lineage") or "",
                }
            )
        elif row.get("strategy") == "SCALPING" and row.get("position_tag") == "SCANNER":
            row.update(
                {
                    "scanner_provenance_status": "missing",
                    "scanner_discovery_type": "unknown_scanner_provenance",
                    "scanner_promotion_id": "",
                    "scanner_promotion_reason": "",
                    "scanner_source_signature": "",
                    "scanner_source_role": "",
                    "scanner_priority_tier": "",
                    "rising_missed_lineage": "",
                }
            )
        else:
            row["scanner_provenance_status"] = "not_applicable"
        enriched.append(row)
    return enriched


def _build_trade_fact_rows(target_date: str) -> tuple[list[dict[str, Any]], list[str]]:
    report = build_trade_review_report(
        target_date=target_date,
        since_time=None,
        top_n=100_000,
        scope="entered",
    )
    rows = list((report.get("sections", {}) or {}).get("recent_trades", []) or [])
    warnings = list((report.get("meta", {}) or {}).get("warnings", []) or [])
    facts: list[dict[str, Any]] = []
    for row in rows:
        strategy = normalize_strategy(row.get("strategy"))
        position_tag = normalize_position_tag(strategy, row.get("position_tag"))
        exit_signal = row.get("exit_signal") or {}
        gatekeeper = row.get("gatekeeper_replay") or {}
        ai_summary = row.get("ai_review_summary") or {}
        status = str(row.get("status") or "").upper()
        buy_price = _safe_float(row.get("buy_price"))
        buy_qty = _safe_int(row.get("buy_qty"))
        buy_time = _parse_datetime(row.get("buy_time"))
        sell_price = _safe_float(row.get("sell_price"))
        sell_time = _parse_datetime(row.get("sell_time"))
        economics_complete = bool(
            status == "COMPLETED"
            and buy_price > 0
            and buy_qty > 0
            and buy_time is not None
            and sell_price > 0
            and sell_time is not None
        )
        facts.append(
            {
                "recommendation_id": _safe_int(row.get("id")),
                "rec_date": _parse_date(row.get("rec_date") or target_date),
                "stock_code": str(row.get("code") or "").strip()[:10],
                "stock_name": str(row.get("name") or ""),
                "strategy": strategy,
                "position_tag": position_tag,
                "status": status,
                "buy_price": buy_price,
                "buy_qty": buy_qty,
                "buy_time": buy_time,
                "sell_price": sell_price,
                "sell_time": sell_time,
                # The fact mart is the cost-adjusted economic source.  A
                # completed row without executable prices/times remains NULL,
                # rather than becoming a misleading flat trade.
                "profit_rate": (
                    calculate_net_profit_rate(buy_price, sell_price)
                    if economics_complete
                    else None
                ),
                "realized_pnl_krw": (
                    calculate_net_realized_pnl(buy_price, sell_price, buy_qty)
                    if economics_complete
                    else None
                ),
                "holding_seconds": _safe_int(row.get("holding_seconds"), default=0)
                or None,
                "exit_rule": str(exit_signal.get("exit_rule") or ""),
                "sell_reason_type": str(exit_signal.get("sell_reason_type") or ""),
                "add_count": _safe_int(row.get("add_count")),
                "avg_down_count": _safe_int(row.get("avg_down_count")),
                "pyramid_count": _safe_int(row.get("pyramid_count")),
                "ai_review_headline": str(ai_summary.get("headline") or ""),
                "gatekeeper_action": str(gatekeeper.get("action") or ""),
                "gatekeeper_action_key": normalize_gatekeeper_action_key(
                    gatekeeper.get("action_key") or gatekeeper.get("action")
                ),
                "gatekeeper_allow_entry": (
                    bool(gatekeeper.get("allow_entry")) if gatekeeper else None
                ),
            }
        )
    return _enrich_scanner_provenance(facts, target_date), warnings


def _aggregate_daily_rows(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[date, str, str], list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        grouped[(fact["rec_date"], fact["strategy"], fact["position_tag"])].append(fact)

    rows: list[dict[str, Any]] = []
    for (rec_date, strategy, position_tag), items in sorted(
        grouped.items(), key=lambda item: item[0]
    ):
        completed = [item for item in items if _is_completed(item)]
        economic_completed = [
            item for item in completed if _has_complete_economics(item)
        ]
        open_rows = [item for item in items if not _is_completed(item)]
        profits = [float(item["profit_rate"]) for item in economic_completed]
        holding_values = [
            _safe_int(item.get("holding_seconds"))
            for item in economic_completed
            if _safe_int(item.get("holding_seconds")) > 0
        ]
        best = max(
            economic_completed,
            key=lambda item: float(item["profit_rate"]),
            default=None,
        )
        worst = min(
            economic_completed,
            key=lambda item: float(item["profit_rate"]),
            default=None,
        )
        rows.append(
            {
                "rec_date": rec_date,
                "strategy": strategy,
                "position_tag": position_tag,
                "entered_count": len(items),
                "completed_count": len(completed),
                "economics_valid_completed_count": len(economic_completed),
                "economics_missing_completed_count": len(completed)
                - len(economic_completed),
                "open_count": len(open_rows),
                "win_count": sum(1 for value in profits if value > 0),
                "loss_count": sum(1 for value in profits if value < 0),
                "flat_count": sum(1 for value in profits if value == 0),
                "realized_pnl_krw": (
                    int(
                        sum(
                            int(item["realized_pnl_krw"]) for item in economic_completed
                        )
                    )
                    if economic_completed
                    else None
                ),
                "avg_profit_rate": (
                    round(sum(profits) / len(profits), 2) if profits else None
                ),
                "avg_holding_seconds": (
                    round(sum(holding_values) / len(holding_values), 1)
                    if holding_values
                    else 0.0
                ),
                "best_trade_code": str(best.get("stock_code") or "") if best else "",
                "best_trade_name": str(best.get("stock_name") or "") if best else "",
                "best_profit_rate": (
                    round(_safe_float(best.get("profit_rate")), 2) if best else None
                ),
                "worst_trade_code": str(worst.get("stock_code") or "") if worst else "",
                "worst_trade_name": str(worst.get("stock_name") or "") if worst else "",
                "worst_profit_rate": (
                    round(_safe_float(worst.get("profit_rate")), 2) if worst else None
                ),
            }
        )
    return rows


def _format_bucket_label(row: dict[str, Any] | None) -> str:
    if not row:
        return "-"
    return f"{row.get('strategy')}/{row.get('position_tag')}"


def _build_scanner_discovery_rows(
    fact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in fact_rows:
        if fact.get("strategy") == "SCALPING" and fact.get("position_tag") == "SCANNER":
            grouped[
                str(fact.get("scanner_discovery_type") or "unknown_scanner_provenance")
            ].append(fact)

    rows: list[dict[str, Any]] = []
    for discovery_type, items in grouped.items():
        completed = [item for item in items if _is_completed(item)]
        economic_completed = [
            item for item in completed if _has_complete_economics(item)
        ]
        profits = [float(item["profit_rate"]) for item in economic_completed]
        pnl = (
            int(sum(int(item["realized_pnl_krw"]) for item in economic_completed))
            if economic_completed
            else None
        )
        wins = sum(1 for value in profits if value > 0)
        losses = sum(1 for value in profits if value < 0)
        flats = sum(1 for value in profits if value == 0)
        reason_counts: dict[str, int] = defaultdict(int)
        signature_counts: dict[str, int] = defaultdict(int)
        matched_count = 0
        for item in items:
            if item.get("scanner_provenance_status") == "matched":
                matched_count += 1
            reason = str(item.get("scanner_promotion_reason") or "").strip()
            signature = str(item.get("scanner_source_signature") or "").strip()
            if reason:
                reason_counts[reason] += 1
            if signature:
                signature_counts[signature] += 1
        best = max(
            economic_completed,
            key=lambda item: float(item["profit_rate"]),
            default=None,
        )
        worst = min(
            economic_completed,
            key=lambda item: float(item["profit_rate"]),
            default=None,
        )
        rows.append(
            {
                "scanner_discovery_type": discovery_type,
                "entered_count": len(items),
                "completed_count": len(completed),
                "economics_valid_completed_count": len(economic_completed),
                "economics_missing_completed_count": len(completed)
                - len(economic_completed),
                "open_count": len(items) - len(completed),
                "win_count": wins,
                "loss_count": losses,
                "flat_count": flats,
                "win_rate": (
                    round((wins / len(economic_completed)) * 100, 1)
                    if economic_completed
                    else None
                ),
                "avg_profit_rate": (
                    round(sum(profits) / len(profits), 2) if profits else None
                ),
                "realized_pnl_krw": pnl,
                "expectancy_krw": (
                    int(round(pnl / len(economic_completed)))
                    if economic_completed and pnl is not None
                    else None
                ),
                "provenance_matched_count": matched_count,
                "provenance_missing_count": len(items) - matched_count,
                "top_promotion_reason": (
                    max(reason_counts.items(), key=lambda item: item[1])[0]
                    if reason_counts
                    else ""
                ),
                "top_source_signature": (
                    max(signature_counts.items(), key=lambda item: item[1])[0]
                    if signature_counts
                    else ""
                ),
                "best_trade_code": str(best.get("stock_code") or "") if best else "",
                "best_trade_name": str(best.get("stock_name") or "") if best else "",
                "best_profit_rate": (
                    round(_safe_float(best.get("profit_rate")), 2) if best else None
                ),
                "worst_trade_code": str(worst.get("stock_code") or "") if worst else "",
                "worst_trade_name": str(worst.get("stock_name") or "") if worst else "",
                "worst_profit_rate": (
                    round(_safe_float(worst.get("profit_rate")), 2) if worst else None
                ),
                "decision_authority": "scanner_discovery_performance_report_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            item["realized_pnl_krw"] is not None,
            item["realized_pnl_krw"] or 0,
            item["completed_count"],
        ),
        reverse=True,
    )


def _build_kpis(
    rows: list[dict[str, Any]], fact_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    entered_count = sum(int(row.get("entered_count") or 0) for row in rows)
    open_count = sum(int(row.get("open_count") or 0) for row in rows)
    economic_facts = [
        row
        for row in fact_rows
        if _is_completed(row)
        and _optional_float(row.get("profit_rate")) is not None
        and _optional_int(row.get("realized_pnl_krw")) is not None
    ]
    economic_completed_count = len(economic_facts)
    win_count = sum(1 for row in economic_facts if float(row["profit_rate"]) > 0)
    realized_pnl = (
        sum(int(row["realized_pnl_krw"]) for row in economic_facts)
        if economic_facts
        else None
    )
    avg_hold_values = [
        _safe_float(row.get("avg_holding_seconds"))
        for row in rows
        if _safe_float(row.get("avg_holding_seconds")) > 0
    ]
    economic_rows = [
        row for row in rows if _optional_int(row.get("realized_pnl_krw")) is not None
    ]
    best_bucket = max(
        economic_rows,
        key=lambda item: _optional_int(item.get("realized_pnl_krw")) or 0,
        default=None,
    )
    worst_bucket = min(
        economic_rows,
        key=lambda item: _optional_int(item.get("realized_pnl_krw")) or 0,
        default=None,
    )

    win_rate = (
        round((win_count / economic_completed_count) * 100, 1)
        if economic_completed_count
        else None
    )
    expectancy_krw = (
        int(round(realized_pnl / economic_completed_count))
        if economic_completed_count and realized_pnl is not None
        else None
    )
    open_ratio = round((open_count / entered_count) * 100, 1) if entered_count else 0.0
    avg_hold_sec = (
        round(sum(avg_hold_values) / len(avg_hold_values), 1)
        if avg_hold_values
        else 0.0
    )

    top_winner = max(
        (
            row
            for row in fact_rows
            if _is_completed(row)
            and (_optional_int(row.get("realized_pnl_krw")) or 0) > 0
        ),
        key=lambda item: _optional_int(item.get("realized_pnl_krw")) or 0,
        default=None,
    )
    top_loser = min(
        (
            row
            for row in fact_rows
            if _is_completed(row)
            and (_optional_int(row.get("realized_pnl_krw")) or 0) < 0
        ),
        key=lambda item: _optional_int(item.get("realized_pnl_krw")) or 0,
        default=None,
    )

    return [
        {
            "label": "종료 승률",
            "value": f"{win_rate:.1f}%" if win_rate is not None else "-",
            "tone": (
                "good"
                if win_rate is not None and win_rate >= 55
                else "warn" if win_rate is not None and win_rate >= 45 else "bad"
            ),
            "detail": f"경제성 유효 종료 {economic_completed_count}건 중 승 {win_count}건",
        },
        {
            "label": "평균 기대손익",
            "value": f"{expectancy_krw:,}원" if expectancy_krw is not None else "-",
            "tone": (
                "good"
                if expectancy_krw is not None and expectancy_krw > 0
                else "warn" if expectancy_krw == 0 else "bad"
            ),
            "detail": "종료 거래 1건당 평균 실현손익",
        },
        {
            "label": "미종료 비중",
            "value": f"{open_ratio:.1f}%",
            "tone": (
                "bad" if open_ratio >= 35 else "warn" if open_ratio >= 20 else "good"
            ),
            "detail": f"진입 {entered_count}건 중 미종료 {open_count}건",
        },
        {
            "label": "평균 보유시간",
            "value": f"{avg_hold_sec:.1f}초",
            "tone": "muted",
            "detail": "종료 거래 기준 평균 보유시간",
        },
        {
            "label": "최고 성과 버킷",
            "value": _format_bucket_label(best_bucket),
            "tone": (
                "good"
                if best_bucket and int(best_bucket.get("realized_pnl_krw") or 0) > 0
                else "muted"
            ),
            "detail": (
                f"{int(best_bucket.get('realized_pnl_krw') or 0):,}원 / 평균 {float(best_bucket.get('avg_profit_rate') or 0):+.2f}%"
                if best_bucket
                else "-"
            ),
        },
        {
            "label": "주의 버킷",
            "value": _format_bucket_label(worst_bucket),
            "tone": (
                "bad"
                if worst_bucket and int(worst_bucket.get("realized_pnl_krw") or 0) < 0
                else "muted"
            ),
            "detail": (
                f"{int(worst_bucket.get('realized_pnl_krw') or 0):,}원 / 평균 {float(worst_bucket.get('avg_profit_rate') or 0):+.2f}%"
                if worst_bucket
                else "-"
            ),
        },
        {
            "label": "최고 익절 거래",
            "value": (
                f"{top_winner.get('stock_name')}({top_winner.get('stock_code')})"
                if top_winner
                else "-"
            ),
            "tone": (
                "good"
                if top_winner and _safe_float(top_winner.get("profit_rate")) > 0
                else "muted"
            ),
            "detail": (
                f"{_safe_float(top_winner.get('profit_rate')):+.2f}% / {int(top_winner.get('realized_pnl_krw') or 0):,}원"
                if top_winner
                else "-"
            ),
        },
        {
            "label": "최대 손실 거래",
            "value": (
                f"{top_loser.get('stock_name')}({top_loser.get('stock_code')})"
                if top_loser
                else "-"
            ),
            "tone": (
                "bad"
                if top_loser and _safe_float(top_loser.get("profit_rate")) < 0
                else "muted"
            ),
            "detail": (
                f"{_safe_float(top_loser.get('profit_rate')):+.2f}% / {int(top_loser.get('realized_pnl_krw') or 0):,}원"
                if top_loser
                else "-"
            ),
        },
    ]


def _build_report_payload(
    target_date: str, fact_rows: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> dict[str, Any]:
    economic_facts = [
        row
        for row in fact_rows
        if _is_completed(row)
        and _optional_float(row.get("profit_rate")) is not None
        and _optional_int(row.get("realized_pnl_krw")) is not None
    ]
    completed_fact_count = sum(1 for row in fact_rows if _is_completed(row))
    strategy_totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "strategy": "",
            "entered_count": 0,
            "completed_count": 0,
            "open_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "flat_count": 0,
            "economics_valid_completed_count": 0,
            "economics_missing_completed_count": 0,
            "realized_pnl_krw": None,
        }
    )
    for row in rows:
        bucket = strategy_totals[row["strategy"]]
        bucket["strategy"] = row["strategy"]
        for key in (
            "entered_count",
            "completed_count",
            "open_count",
            "win_count",
            "loss_count",
            "flat_count",
            "economics_valid_completed_count",
            "economics_missing_completed_count",
        ):
            bucket[key] += int(row.get(key) or 0)
        realized_pnl = _optional_int(row.get("realized_pnl_krw"))
        if realized_pnl is not None:
            bucket["realized_pnl_krw"] = (
                int(bucket["realized_pnl_krw"] or 0) + realized_pnl
            )

    top_winners = [
        row
        for row in fact_rows
        if _is_completed(row) and (_optional_float(row.get("profit_rate")) or 0) > 0
    ][:5]
    top_losers = sorted(
        [
            row
            for row in fact_rows
            if _is_completed(row) and (_optional_float(row.get("profit_rate")) or 0) < 0
        ],
        key=lambda item: _optional_float(item.get("profit_rate")) or 0,
    )[:5]
    scanner_discovery_rows = _build_scanner_discovery_rows(fact_rows)

    return {
        "date": target_date,
        "has_data": bool(rows),
        "summary": {
            "strategy_count": len(strategy_totals),
            "tag_group_count": len(rows),
            "entered_count": sum(row["entered_count"] for row in rows),
            "completed_count": sum(row["completed_count"] for row in rows),
            "economics_valid_completed_count": len(economic_facts),
            "economics_missing_completed_count": completed_fact_count
            - len(economic_facts),
            "open_count": sum(row["open_count"] for row in rows),
            "realized_pnl_krw": (
                int(sum(int(row["realized_pnl_krw"]) for row in economic_facts))
                if economic_facts
                else None
            ),
            "scanner_discovery_type_count": len(scanner_discovery_rows),
            "scanner_provenance_matched_count": sum(
                int(row.get("provenance_matched_count") or 0)
                for row in scanner_discovery_rows
            ),
            "scanner_provenance_missing_count": sum(
                int(row.get("provenance_missing_count") or 0)
                for row in scanner_discovery_rows
            ),
        },
        "kpis": _build_kpis(rows, fact_rows),
        "strategy_totals": sorted(
            strategy_totals.values(),
            key=lambda item: (
                item["realized_pnl_krw"] is not None,
                item["realized_pnl_krw"] or 0,
            ),
            reverse=True,
        ),
        "rows": rows,
        "sections": {
            "top_winners": top_winners,
            "top_losers": top_losers,
            "scanner_discovery_rows": scanner_discovery_rows,
        },
    }


def _trade_fact_db_payload(fact: dict[str, Any]) -> dict[str, Any]:
    allowed = {column.name for column in TradePerformanceFact.__table__.columns}
    return {key: value for key, value in fact.items() if key in allowed}


def _summary_db_payload(row: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        column.name for column in StrategyPositionPerformanceDaily.__table__.columns
    }
    return {key: value for key, value in row.items() if key in allowed}


def _validate_fact_batch(
    facts: list[dict[str, Any]], warnings: list[str], target_date: str
) -> list[str]:
    issues = [f"source_warning:{warning}" for warning in warnings]
    target = _parse_date(target_date)
    seen_ids: set[int] = set()
    for fact in facts:
        recommendation_id = _safe_int(fact.get("recommendation_id"))
        if recommendation_id <= 0:
            issues.append("recommendation_id_invalid")
        elif recommendation_id in seen_ids:
            issues.append(f"recommendation_id_duplicate:{recommendation_id}")
        seen_ids.add(recommendation_id)
        if fact.get("rec_date") != target:
            issues.append("rec_date_mismatch")
        if not str(fact.get("stock_code") or "").strip():
            issues.append("stock_code_missing")
        if not str(fact.get("strategy") or "").strip():
            issues.append("strategy_missing")
        if not str(fact.get("position_tag") or "").strip():
            issues.append("position_tag_missing")
        if not str(fact.get("status") or "").strip():
            issues.append("status_missing")
    return sorted(set(issues))


def _sync_status_payload(
    *,
    status: str,
    facts: list[dict[str, Any]],
    warnings: list[str],
    issues: list[str],
    prior_fact_count: int | None,
    source_digest: str,
) -> dict[str, Any]:
    completed = [fact for fact in facts if _is_completed(fact)]
    economics_valid = [fact for fact in completed if _has_complete_economics(fact)]
    return {
        "status": status,
        "consumer_ready": status in {"succeeded", "valid_empty"},
        "source_fact_count": len(facts),
        "fact_count": len(facts),
        "completed_count": len(completed),
        "economics_valid_completed_count": len(economics_valid),
        "economics_missing_completed_count": len(completed) - len(economics_valid),
        "prior_fact_count": prior_fact_count,
        "warning_count": len(warnings),
        "warnings": warnings,
        "issues": issues,
        "source_digest": source_digest,
    }


def sync_trade_performance_for_date(target_date: str) -> dict[str, Any]:
    _DB.init_db()
    facts, warnings = _build_trade_fact_rows(target_date)
    rec_date = _parse_date(target_date)

    with _DB.get_session() as session:
        prior_fact_count = int(
            session.query(TradePerformanceFact)
            .filter(TradePerformanceFact.rec_date == rec_date)
            .count()
        )
    source_digest = _canonical_sha256(facts)
    issues = _validate_fact_batch(facts, warnings, target_date)
    if issues:
        receipt = _write_status(
            target_date,
            _sync_status_payload(
                status="source_blocked",
                facts=facts,
                warnings=warnings,
                issues=issues,
                prior_fact_count=prior_fact_count,
                source_digest=source_digest,
            ),
        )
        raise FactSyncSourceError(
            f"strategy_position_fact_sync_source_blocked:{receipt['artifact_sha256']}"
        )

    summary_rows = _aggregate_daily_rows(facts)
    sync_status = "succeeded" if facts else "valid_empty"
    with _DB.get_session() as session:
        session.execute(
            delete(TradePerformanceFact).where(
                TradePerformanceFact.rec_date == rec_date
            )
        )
        session.execute(
            delete(StrategyPositionPerformanceDaily).where(
                StrategyPositionPerformanceDaily.rec_date == rec_date
            )
        )
        synced_at = datetime.now()
        if facts:
            session.bulk_insert_mappings(
                TradePerformanceFact,
                [
                    {**_trade_fact_db_payload(fact), "synced_at": synced_at}
                    for fact in facts
                ],
            )
        if summary_rows:
            session.bulk_insert_mappings(
                StrategyPositionPerformanceDaily,
                [
                    {**_summary_db_payload(row), "synced_at": synced_at}
                    for row in summary_rows
                ],
            )

    _DB.analyze_performance_tables()
    receipt = _write_status(
        target_date,
        _sync_status_payload(
            status=sync_status,
            facts=facts,
            warnings=warnings,
            issues=[],
            prior_fact_count=prior_fact_count,
            source_digest=source_digest,
        ),
    )

    return {
        "target_date": target_date,
        "fact_count": len(facts),
        "summary_count": len(summary_rows),
        "warnings": warnings,
        "status": sync_status,
        "status_path": str(_status_path(target_date)),
        "artifact_sha256": receipt["artifact_sha256"],
    }


def build_strategy_position_performance_report(
    target_date: str, *, refresh: bool = False
) -> dict[str, Any]:
    rec_date = _parse_date(target_date)
    _DB.init_db()
    try:
        if refresh:
            sync_trade_performance_for_date(target_date)

        with _DB.get_session() as session:
            summary_rows = (
                session.query(StrategyPositionPerformanceDaily)
                .filter(StrategyPositionPerformanceDaily.rec_date == rec_date)
                .order_by(
                    StrategyPositionPerformanceDaily.realized_pnl_krw.desc(),
                    StrategyPositionPerformanceDaily.entered_count.desc(),
                )
                .all()
            )
            if not summary_rows:
                sync_trade_performance_for_date(target_date)
                summary_rows = (
                    session.query(StrategyPositionPerformanceDaily)
                    .filter(StrategyPositionPerformanceDaily.rec_date == rec_date)
                    .order_by(
                        StrategyPositionPerformanceDaily.realized_pnl_krw.desc(),
                        StrategyPositionPerformanceDaily.entered_count.desc(),
                    )
                    .all()
                )

            facts = (
                session.query(
                    TradePerformanceFact.recommendation_id,
                    TradePerformanceFact.stock_code,
                    TradePerformanceFact.stock_name,
                    TradePerformanceFact.strategy,
                    TradePerformanceFact.position_tag,
                    TradePerformanceFact.status,
                    TradePerformanceFact.profit_rate,
                    TradePerformanceFact.realized_pnl_krw,
                    TradePerformanceFact.exit_rule,
                    TradePerformanceFact.sell_reason_type,
                    TradePerformanceFact.buy_time,
                    TradePerformanceFact.sell_time,
                )
                .filter(TradePerformanceFact.rec_date == rec_date)
                .order_by(
                    TradePerformanceFact.realized_pnl_krw.desc(),
                    TradePerformanceFact.profit_rate.desc(),
                )
                .all()
            )

        rows = [
            {
                "rec_date": row.rec_date.isoformat(),
                "strategy": row.strategy,
                "position_tag": row.position_tag,
                "entered_count": int(row.entered_count or 0),
                "completed_count": int(row.completed_count or 0),
                "open_count": int(row.open_count or 0),
                "win_count": int(row.win_count or 0),
                "loss_count": int(row.loss_count or 0),
                "flat_count": int(row.flat_count or 0),
                "realized_pnl_krw": _optional_int(row.realized_pnl_krw),
                "avg_profit_rate": (
                    round(float(row.avg_profit_rate), 2)
                    if row.avg_profit_rate is not None
                    else None
                ),
                "avg_holding_seconds": round(_safe_float(row.avg_holding_seconds), 1),
                "best_trade_code": row.best_trade_code or "",
                "best_trade_name": row.best_trade_name or "",
                "best_profit_rate": (
                    round(_safe_float(row.best_profit_rate), 2)
                    if row.best_profit_rate is not None
                    else None
                ),
                "worst_trade_code": row.worst_trade_code or "",
                "worst_trade_name": row.worst_trade_name or "",
                "worst_profit_rate": (
                    round(_safe_float(row.worst_profit_rate), 2)
                    if row.worst_profit_rate is not None
                    else None
                ),
            }
            for row in summary_rows
        ]

        fact_rows = [
            {
                "recommendation_id": fact.recommendation_id,
                "stock_code": fact.stock_code,
                "stock_name": fact.stock_name or "",
                "strategy": fact.strategy,
                "position_tag": fact.position_tag,
                "status": fact.status,
                "profit_rate": (
                    round(float(fact.profit_rate), 2)
                    if fact.profit_rate is not None
                    else None
                ),
                "realized_pnl_krw": _optional_int(fact.realized_pnl_krw),
                "exit_rule": fact.exit_rule or "",
                "sell_reason_type": fact.sell_reason_type or "",
                "buy_time": (
                    fact.buy_time.strftime("%Y-%m-%d %H:%M:%S") if fact.buy_time else ""
                ),
                "sell_time": (
                    fact.sell_time.strftime("%Y-%m-%d %H:%M:%S")
                    if fact.sell_time
                    else ""
                ),
            }
            for fact in facts
        ]
        fact_rows = _enrich_scanner_provenance(fact_rows, target_date)
        return _build_report_payload(target_date, fact_rows, rows)
    except Exception:
        facts, _warnings = _build_trade_fact_rows(target_date)
        rows = _aggregate_daily_rows(facts)
        fact_rows = [
            {
                "recommendation_id": fact["recommendation_id"],
                "stock_code": fact["stock_code"],
                "stock_name": fact["stock_name"],
                "strategy": fact["strategy"],
                "position_tag": fact["position_tag"],
                "status": fact["status"],
                "profit_rate": (
                    round(float(fact["profit_rate"]), 2)
                    if fact["profit_rate"] is not None
                    else None
                ),
                "realized_pnl_krw": _optional_int(fact["realized_pnl_krw"]),
                "exit_rule": fact["exit_rule"],
                "sell_reason_type": fact["sell_reason_type"],
                "buy_time": (
                    fact["buy_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if fact["buy_time"]
                    else ""
                ),
                "sell_time": (
                    fact["sell_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if fact["sell_time"]
                    else ""
                ),
            }
            for fact in facts
        ]
        row_payloads = [
            {
                **row,
                "rec_date": row["rec_date"].isoformat(),
            }
            for row in rows
        ]
        return _build_report_payload(target_date, fact_rows, row_payloads)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize exact trade performance facts for a target date."
    )
    parser.add_argument(
        "--date",
        dest="target_date",
        default=date.today().isoformat(),
        help="Target date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--print",
        dest="print_stdout",
        action="store_true",
        help="Print the synchronization summary as JSON.",
    )
    args = parser.parse_args(argv)
    try:
        result = sync_trade_performance_for_date(args.target_date)
    except FactSyncSourceError as exc:
        if args.print_stdout:
            print(json.dumps({"status": "source_blocked", "reason": str(exc)}))
        return 2
    except Exception as exc:
        try:
            _write_status(
                args.target_date,
                {
                    "status": "failed",
                    "consumer_ready": False,
                    "source_fact_count": None,
                    "fact_count": None,
                    "completed_count": None,
                    "economics_valid_completed_count": None,
                    "economics_missing_completed_count": None,
                    "prior_fact_count": None,
                    "warning_count": 0,
                    "warnings": [],
                    "issues": [f"exception:{type(exc).__name__}"],
                    "source_digest": None,
                },
            )
        except Exception:
            pass
        if args.print_stdout:
            print(json.dumps({"status": "failed", "reason": str(exc)}))
        return 1
    if args.print_stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
