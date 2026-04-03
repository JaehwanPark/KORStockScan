"""Structured trade review report for holding lifecycle analysis."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import LOGS_DIR, POSTGRES_URL
from src.engine.sniper_gatekeeper_replay import find_gatekeeper_snapshot_for_trade


_HOLDING_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[HOLDING_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_FIELD_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")

_DISPLAY_STAGE_LABELS = {
    "holding_started": "보유 시작",
    "scale_in_executed": "추가매수 체결",
    "preset_exit_setup": "기본 익절망 설치",
    "ai_holding_review": "AI 보유감시",
    "exit_signal": "청산 시그널",
    "sell_order_sent": "매도 주문 전송",
    "sell_order_failed": "매도 주문 실패",
    "sell_completed": "매도 체결 완료",
}

_EVENT_DETAIL_LABELS = {
    "profit_rate": "수익률",
    "ai_score": "AI 점수",
    "low_score_hits": "하방카운트",
    "held_sec": "보유시간",
    "price_change": "가격변화",
    "review_cd_sec": "AI 주기",
    "sell_reason_type": "청산유형",
    "reason": "사유",
    "exit_rule": "청산 규칙",
    "peak_profit": "고점수익",
    "current_ai_score": "현재 AI",
    "curr_price": "현재가",
    "buy_price": "매수가",
    "buy_qty": "보유수량",
    "qty": "주문수량",
    "ord_no": "주문번호",
    "order_type": "주문타입",
    "sell_price": "매도가",
    "strategy": "전략",
    "entry_mode": "진입모드",
    "position_tag": "포지션",
    "preset_tp_price": "기본 익절가",
    "fill_price": "체결가",
    "fill_qty": "체결수량",
    "new_avg_price": "새 평단",
    "new_buy_qty": "새 보유수량",
    "add_count": "추가매수 횟수",
    "new_status": "후속상태",
    "error": "오류",
    "revive": "부활여부",
    "new_watch_id": "신규 감시 ID",
}

_DETAIL_KEY_ORDER = [
    "reason",
    "exit_rule",
    "profit_rate",
    "ai_score",
    "low_score_hits",
    "peak_profit",
    "sell_reason_type",
    "qty",
    "sell_price",
    "buy_price",
    "buy_qty",
    "new_avg_price",
    "new_buy_qty",
    "add_count",
    "held_sec",
    "ord_no",
    "error",
]


@dataclass
class HoldingEvent:
    timestamp: str
    name: str
    code: str
    stage: str
    fields: dict[str, str]
    raw_line: str


def _parse_since_datetime(target_date: str, since_time: str | None) -> datetime | None:
    if not since_time:
        return None
    candidate = str(since_time).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            if fmt.startswith("%Y"):
                return datetime.strptime(candidate, fmt)
            return datetime.strptime(f"{target_date} {candidate}", f"%Y-%m-%d {fmt}")
        except Exception:
            continue
    return None


def _iter_target_lines(log_paths: list[Path], *, target_date: str) -> list[str]:
    lines: list[str] = []
    for log_path in log_paths:
        candidate_paths = [log_path]
        candidate_paths.extend(sorted(log_path.parent.glob(f"{log_path.name}.*"), key=lambda path: path.name))
        for candidate in candidate_paths:
            if not candidate.exists() or not candidate.is_file():
                continue
            with open(candidate, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    if f"[{target_date}" not in raw_line:
                        continue
                    if "[HOLDING_PIPELINE]" not in raw_line:
                        continue
                    lines.append(raw_line.strip())
    return lines


def _parse_event(line: str) -> HoldingEvent | None:
    match = _HOLDING_RE.match(line.strip())
    if not match:
        return None
    fields = {
        m.group("key"): str(m.group("value") or "").replace("|", " ")
        for m in _FIELD_RE.finditer(match.group("rest") or "")
    }
    return HoldingEvent(
        timestamp=match.group("timestamp"),
        name=match.group("name"),
        code=match.group("code"),
        stage=match.group("stage"),
        fields=fields,
        raw_line=line.strip(),
    )


def _event_sort_key(event: HoldingEvent) -> tuple[datetime, str, str]:
    try:
        parsed = datetime.strptime(event.timestamp, "%Y-%m-%d %H:%M:%S")
    except Exception:
        parsed = datetime.min
    return parsed, event.code, event.stage


def _friendly_stage(stage: str) -> str:
    return _DISPLAY_STAGE_LABELS.get(stage, stage)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, "", "None"):
        return None
    if isinstance(value, datetime):
        return value
    candidate = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return None


def _format_dt(value: Any) -> str:
    parsed = _parse_dt(value)
    if not parsed:
        return ""
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _format_duration_seconds(seconds: float | int | None) -> str:
    if seconds is None:
        return "-"
    total = int(max(0, float(seconds)))
    minutes, sec = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}시간 {minutes}분 {sec}초"
    if minutes > 0:
        return f"{minutes}분 {sec}초"
    return f"{sec}초"


def _value_chip(key: str, value: str) -> dict[str, str] | None:
    if value in (None, "", "None"):
        return None
    label = _EVENT_DETAIL_LABELS.get(key, key)
    display = str(value)
    if key in {"held_sec", "review_cd_sec"}:
        display = _format_duration_seconds(_safe_int(value))
    elif key in {"profit_rate", "peak_profit"}:
        display = f"{_safe_float(value):+.2f}%"
    elif key in {"buy_price", "sell_price", "curr_price", "preset_tp_price", "fill_price"}:
        display = f"{_safe_int(value):,}원"
    elif key == "new_avg_price":
        display = f"{_safe_float(value):,.2f}원"
    elif key in {"buy_qty", "qty", "fill_qty", "new_watch_id"}:
        display = f"{_safe_int(value):,}"
    elif key in {"new_buy_qty", "add_count"}:
        display = f"{_safe_int(value):,}"
    elif key == "price_change":
        display = f"{_safe_float(value):.2f}"
    return {"label": label, "value": display}


def _build_event_details(event: HoldingEvent) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    seen = set()
    for key in _DETAIL_KEY_ORDER + sorted(event.fields.keys()):
        if key in seen:
            continue
        seen.add(key)
        chip = _value_chip(key, event.fields.get(key))
        if chip:
            details.append(chip)
    return details


def _import_sqlalchemy():
    from sqlalchemy import create_engine, text

    return create_engine, text


def _fetch_trade_rows(target_date: str, code: str | None = None) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    try:
        create_engine, text = _import_sqlalchemy()
        engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    except Exception as exc:
        return [], [f"DB 연결 준비 실패: {exc}"]

    params: dict[str, Any] = {"target_date": datetime.strptime(target_date, "%Y-%m-%d").date()}
    code_filter = ""
    if code:
        params["code"] = str(code).strip()[:6]
        code_filter = "AND stock_code = :code"

    query = f"""
        SELECT
            id,
            rec_date,
            stock_code,
            stock_name,
            status,
            strategy,
            position_tag,
            buy_price,
            buy_qty,
            buy_time,
            sell_price,
            sell_time,
            profit_rate
        FROM recommendation_history
        WHERE rec_date = :target_date
        {code_filter}
        ORDER BY COALESCE(sell_time, buy_time) DESC NULLS LAST, id DESC
    """

    rows: list[dict] = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            for row in result.mappings():
                buy_price = _safe_float(row.get("buy_price"))
                sell_price = _safe_float(row.get("sell_price"))
                buy_qty = _safe_int(row.get("buy_qty"))
                pnl_krw = int(round((sell_price - buy_price) * buy_qty)) if sell_price and buy_price and buy_qty else 0
                rows.append({
                    "id": _safe_int(row.get("id")),
                    "rec_date": str(row.get("rec_date") or ""),
                    "code": str(row.get("stock_code") or "").strip()[:6],
                    "name": str(row.get("stock_name") or ""),
                    "status": str(row.get("status") or ""),
                    "strategy": str(row.get("strategy") or ""),
                    "position_tag": str(row.get("position_tag") or ""),
                    "buy_price": buy_price,
                    "buy_qty": buy_qty,
                    "buy_time": _format_dt(row.get("buy_time")),
                    "sell_price": _safe_int(sell_price),
                    "sell_time": _format_dt(row.get("sell_time")),
                    "profit_rate": round(_safe_float(row.get("profit_rate")), 2),
                    "realized_pnl_krw": pnl_krw,
                })
    except Exception as exc:
        warnings.append(f"매매 이력 조회 실패: {exc}")
    return rows, warnings


def _match_trade_events(trade: dict, events: list[HoldingEvent]) -> list[HoldingEvent]:
    trade_id = str(trade.get("id") or "").strip()
    code = str(trade.get("code") or "").strip()[:6]
    buy_time = _parse_dt(trade.get("buy_time"))
    sell_time = _parse_dt(trade.get("sell_time"))

    matched: list[HoldingEvent] = []
    for event in events:
        event_id = str(event.fields.get("id") or "").strip()
        if trade_id and event_id == trade_id:
            matched.append(event)
            continue
        if event.code != code:
            continue
        event_dt = _parse_dt(event.timestamp)
        if not event_dt:
            continue
        if buy_time and event_dt < buy_time:
            continue
        if sell_time and event_dt > sell_time.replace(microsecond=0):
            continue
        if not trade_id:
            matched.append(event)
    matched.sort(key=_event_sort_key)
    return matched


def _build_timeline(events: list[HoldingEvent]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for event in events:
        if timeline and timeline[-1]["stage"] == event.stage:
            continue
        timeline.append({
            "stage": event.stage,
            "label": _friendly_stage(event.stage),
            "timestamp": event.timestamp,
            "details": _build_event_details(event),
            "fields": dict(event.fields),
        })
    return timeline


def _build_latest_event(events: list[HoldingEvent]) -> dict | None:
    if not events:
        return None
    event = events[-1]
    return {
        "stage": event.stage,
        "label": _friendly_stage(event.stage),
        "timestamp": event.timestamp,
        "details": _build_event_details(event),
        "fields": dict(event.fields),
    }


def _build_exit_signal(events: list[HoldingEvent]) -> dict | None:
    for event in reversed(events):
        if event.stage != "exit_signal":
            continue
        return {
            "stage": event.stage,
            "label": _friendly_stage(event.stage),
            "timestamp": event.timestamp,
            "reason": event.fields.get("reason") or "",
            "exit_rule": event.fields.get("exit_rule") or "",
            "sell_reason_type": event.fields.get("sell_reason_type") or "",
            "details": _build_event_details(event),
            "fields": dict(event.fields),
        }
    return None


def _tone_for_trade(trade: dict) -> str:
    if str(trade.get("status") or "").upper() != "COMPLETED":
        return "warn"
    if _safe_float(trade.get("profit_rate")) > 0:
        return "good"
    if _safe_float(trade.get("profit_rate")) < 0:
        return "bad"
    return "muted"


def _build_trade_row(trade: dict, events: list[HoldingEvent]) -> dict:
    buy_dt = _parse_dt(trade.get("buy_time"))
    sell_dt = _parse_dt(trade.get("sell_time"))
    holding_sec = int((sell_dt - buy_dt).total_seconds()) if buy_dt and sell_dt else None
    ai_reviews = [
        {
            "timestamp": event.timestamp,
            "ai_score": event.fields.get("ai_score"),
            "profit_rate": event.fields.get("profit_rate"),
            "low_score_hits": event.fields.get("low_score_hits"),
        }
        for event in events
        if event.stage == "ai_holding_review"
    ]
    gatekeeper_snapshot = find_gatekeeper_snapshot_for_trade(
        str(trade.get("rec_date") or ""),
        str(trade.get("code") or ""),
        buy_dt,
    )
    gatekeeper_replay = None
    if gatekeeper_snapshot:
        replay_time = str(gatekeeper_snapshot.get("signal_time") or "")
        gatekeeper_replay = {
            "timestamp": gatekeeper_snapshot.get("recorded_at") or "",
            "time": replay_time,
            "action": gatekeeper_snapshot.get("action_label") or "",
            "allow_entry": bool(gatekeeper_snapshot.get("allow_entry", False)),
            "report_preview": str(gatekeeper_snapshot.get("report_preview") or ""),
            "url": (
                f"/gatekeeper-replay?date={trade.get('rec_date')}&code={trade.get('code')}"
                + (f"&time={replay_time}" if replay_time else "")
            ),
        }

    return {
        **trade,
        "tone": _tone_for_trade(trade),
        "holding_seconds": holding_sec,
        "holding_duration_text": _format_duration_seconds(holding_sec),
        "timeline": _build_timeline(events),
        "latest_event": _build_latest_event(events),
        "exit_signal": _build_exit_signal(events),
        "ai_reviews": ai_reviews[-6:],
        "gatekeeper_replay": gatekeeper_replay,
    }


def _is_entered_trade(row: dict) -> bool:
    status = str(row.get("status") or "").upper()
    if row.get("buy_time"):
        return True
    if _safe_int(row.get("buy_qty")) > 0:
        return True
    return status in {"BUY_ORDERED", "HOLDING", "SELL_ORDERED", "COMPLETED"}


def build_trade_review_report(
    target_date: str,
    code: str | None = None,
    since_time: str | None = None,
    top_n: int = 10,
    scope: str = "entered",
) -> dict:
    normalized_code = str(code).strip()[:6] if code else None
    since_dt = _parse_since_datetime(target_date, since_time)
    scope = str(scope or "entered").strip().lower()

    log_paths = [
        LOGS_DIR / "sniper_state_handlers_info.log",
        LOGS_DIR / "sniper_execution_receipts_info.log",
    ]
    lines = _iter_target_lines(log_paths, target_date=target_date)
    all_events = [event for line in lines if (event := _parse_event(line))]
    events = all_events
    if normalized_code:
        events = [event for event in events if event.code == normalized_code]
    if since_dt is not None:
        filtered_events: list[HoldingEvent] = []
        for event in events:
            event_dt = _parse_dt(event.timestamp)
            if event_dt and event_dt >= since_dt:
                filtered_events.append(event)
        events = filtered_events
    events.sort(key=_event_sort_key)

    trade_rows, warnings = _fetch_trade_rows(target_date, None)
    per_stage = Counter(event.stage for event in events)

    compiled_rows = []
    for trade in trade_rows:
        matched = _match_trade_events(trade, all_events)
        compiled_rows.append(_build_trade_row(trade, matched))

    all_rows = compiled_rows
    entered_rows = [row for row in all_rows if _is_entered_trade(row)]
    expired_rows = [row for row in all_rows if str(row.get("status") or "").upper() == "EXPIRED"]
    base_rows = all_rows if scope == "all" else entered_rows
    visible_rows = base_rows
    if normalized_code:
        visible_rows = [row for row in visible_rows if str(row.get("code") or "").strip() == normalized_code]

    recent_trades = visible_rows[:top_n]
    realized = [row for row in visible_rows if str(row.get("status") or "").upper() == "COMPLETED"]
    win_count = sum(1 for row in realized if _safe_float(row.get("profit_rate")) > 0)
    loss_count = sum(1 for row in realized if _safe_float(row.get("profit_rate")) < 0)
    available_stocks = []
    seen_codes = set()
    for row in entered_rows:
        code_value = str(row.get("code") or "").strip()
        if not code_value or code_value in seen_codes:
            continue
        seen_codes.add(code_value)
        available_stocks.append({
            "code": code_value,
            "name": str(row.get("name") or ""),
            "label": f"{row.get('name') or '-'} ({code_value})",
        })

    return {
        "date": target_date,
        "code": normalized_code,
        "scope": scope,
        "since": since_dt.strftime("%Y-%m-%d %H:%M:%S") if since_dt else None,
        "has_data": bool(visible_rows or events),
        "meta": {
            "warnings": warnings,
            "available_stocks": available_stocks,
            "log_paths": [str(path) for path in log_paths],
        },
        "metrics": {
            "total_trades": len(visible_rows),
            "completed_trades": len(realized),
            "open_trades": sum(1 for row in visible_rows if str(row.get("status") or "").upper() != "COMPLETED"),
            "win_trades": win_count,
            "loss_trades": loss_count,
            "avg_profit_rate": round(sum(_safe_float(row.get("profit_rate")) for row in realized) / len(realized), 2) if realized else 0.0,
            "realized_pnl_krw": int(sum(_safe_int(row.get("realized_pnl_krw")) for row in realized)),
            "holding_events": len(events),
            "all_rows": len(all_rows),
            "entered_rows": len(entered_rows),
            "expired_rows": len(expired_rows),
        },
        "event_breakdown": [
            {"stage": stage, "label": _friendly_stage(stage), "count": count}
            for stage, count in per_stage.most_common(12)
        ],
        "sections": {
            "recent_trades": recent_trades,
            "completed_trades": [row for row in visible_rows if str(row.get("status") or "").upper() == "COMPLETED"][:top_n],
            "open_trades": [row for row in visible_rows if str(row.get("status") or "").upper() != "COMPLETED"][:top_n],
            "expired_candidates": expired_rows[:top_n],
        },
    }


def format_trade_review_summary(report: dict) -> str:
    metrics = report.get("metrics", {}) or {}
    lines = [f"📘 HOLDING/매매 복기 집계 ({report.get('date')})"]
    if report.get("code"):
        lines.append(f"- 종목: {report['code']}")
    if report.get("since"):
        lines.append(f"- since 필터: {report['since']}")
    lines.append(f"- 총 거래: {metrics.get('total_trades', 0)}건")
    lines.append(f"- 종료 거래: {metrics.get('completed_trades', 0)}건")
    lines.append(f"- 미종료 거래: {metrics.get('open_trades', 0)}건")
    lines.append(f"- 평균 손익률: {metrics.get('avg_profit_rate', 0.0)}%")
    lines.append(f"- 실현손익: {metrics.get('realized_pnl_krw', 0):,}원")
    warnings = report.get("meta", {}).get("warnings", []) or []
    if warnings:
        lines.append("- 경고:")
        for item in warnings:
            lines.append(f"  {item}")

    trades = report.get("sections", {}).get("recent_trades", []) or []
    if trades:
        lines.append("1. 최근 거래")
        for idx, row in enumerate(trades, start=1):
            exit_signal = row.get("exit_signal") or {}
            latest = row.get("latest_event") or {}
            lines.append(
                f"{idx}. {row.get('name')}({row.get('code')}) "
                f"id={row.get('id')} status={row.get('status')} "
                f"profit={row.get('profit_rate', 0):+.2f}% "
                f"hold={row.get('holding_duration_text')} "
                f"exit={exit_signal.get('reason') or latest.get('label') or '-'}"
            )
    return "\n".join(lines)
