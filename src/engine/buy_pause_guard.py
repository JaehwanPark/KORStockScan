from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path
from typing import Any

from src.core.event_bus import EventBus
from src.engine.trade_pause_control import set_buy_side_pause
from src.engine.sniper_trade_review_report import (
    _build_trade_row,
    _event_sort_key,
    _fetch_trade_rows,
    _iter_target_lines,
    _match_trade_events,
    _parse_dt,
    _parse_event,
    _safe_float,
    _safe_int,
)
from src.utils.constants import DATA_DIR, LOGS_DIR
from src.utils.logger import log_error, log_info
from src.utils.runtime_flags import is_trading_paused


RUNTIME_DIR = DATA_DIR / "runtime"
BUY_PAUSE_GUARD_STATE_PATH = RUNTIME_DIR / "buy_pause_guard_state.json"
BUY_PAUSE_GUARD_VERSION = 1
BUY_PAUSE_GUARD_TTL_MINUTES = 60
BUY_PAUSE_GUARD_TRIGGER_START = dt_time(9, 30)
BUY_PAUSE_GUARD_TRIGGER_SAMPLE_READY = dt_time(9, 45)
BUY_PAUSE_GUARD_TRIGGER_END = dt_time(11, 0)
BUY_PAUSE_GUARD_LOSS_RATE_LIMIT = -0.60
BUY_PAUSE_GUARD_LOSS_RATE_DELTA_LIMIT = -0.20
BUY_PAUSE_GUARD_REALIZED_PNL_LIMIT = -20_000


RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def _now(now_dt: datetime | None = None) -> datetime:
    return now_dt or datetime.now()


def _default_state() -> dict[str, Any]:
    return {
        "version": BUY_PAUSE_GUARD_VERSION,
        "active_guard_id": "",
        "status": "",
        "created_at": "",
        "resolved_at": "",
        "expires_at": "",
        "trigger_flags": {},
        "metrics_snapshot": {},
        "latest_trade_fingerprint": "",
        "sequence": 0,
    }


def load_buy_pause_guard_state(now_dt: datetime | None = None) -> dict[str, Any]:
    state = _default_state()
    if BUY_PAUSE_GUARD_STATE_PATH.exists():
        try:
            with open(BUY_PAUSE_GUARD_STATE_PATH, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                state.update(payload)
        except Exception as exc:
            log_error(f"[BUY_PAUSE_GUARD] state load failed: {exc}")
    state["version"] = BUY_PAUSE_GUARD_VERSION
    expires_at = _parse_guard_timestamp(state.get("expires_at"))
    if state.get("status") == "pending" and expires_at and expires_at <= _now(now_dt):
        state["status"] = "expired"
        state["resolved_at"] = _format_guard_timestamp(_now(now_dt))
        save_buy_pause_guard_state(state)
    return state


def save_buy_pause_guard_state(state: dict[str, Any]) -> Path:
    payload = dict(_default_state())
    payload.update(state or {})
    payload["version"] = BUY_PAUSE_GUARD_VERSION
    with open(BUY_PAUSE_GUARD_STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return BUY_PAUSE_GUARD_STATE_PATH


def _format_guard_timestamp(value: datetime | None) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _parse_guard_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def _collect_trade_rows(target_date: str) -> list[dict[str, Any]]:
    log_paths = [
        LOGS_DIR / "sniper_state_handlers_info.log",
        LOGS_DIR / "sniper_execution_receipts_info.log",
    ]
    lines = _iter_target_lines(log_paths, target_date=target_date)
    all_events = [event for line in lines if (event := _parse_event(line))]
    all_events.sort(key=_event_sort_key)
    trade_rows, _warnings = _fetch_trade_rows(target_date, None)
    compiled_rows: list[dict[str, Any]] = []
    for trade in trade_rows:
        matched = _match_trade_events(trade, all_events)
        compiled_rows.append(_build_trade_row(trade, matched))
    return compiled_rows


def _filter_completed_fallback_scalps(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("strategy") or "").upper() != "SCALPING":
            continue
        if str(row.get("status") or "").upper() != "COMPLETED":
            continue
        if str(row.get("entry_mode") or "").strip().lower() != "fallback":
            continue
        filtered.append(row)
    filtered.sort(
        key=lambda row: (
            _parse_dt(row.get("sell_time")) or _parse_dt(row.get("buy_time")) or datetime.min,
            _safe_int(row.get("id")),
        )
    )
    return filtered


def _find_previous_trading_day_avg_loss(now_dt: datetime, *, max_lookback_days: int = 7) -> tuple[str, float | None]:
    for day_delta in range(1, max_lookback_days + 1):
        candidate = (now_dt - timedelta(days=day_delta)).strftime("%Y-%m-%d")
        rows = _filter_completed_fallback_scalps(_collect_trade_rows(candidate))
        losses = [_safe_float(row.get("profit_rate")) for row in rows if _safe_float(row.get("profit_rate")) < 0]
        if losses:
            return candidate, round(sum(losses) / len(losses), 2)
    return "", None


def _build_latest_trade_fingerprint(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "no-completed-fallback"
    latest = rows[-1]
    last_trade_id = _safe_int(latest.get("id"))
    last_sell_time = str(latest.get("sell_time") or latest.get("buy_time") or "")
    realized_total = int(sum(_safe_int(row.get("realized_pnl_krw")) for row in rows))
    return f"{len(rows)}:{last_trade_id}:{last_sell_time}:{realized_total}"


def _build_metrics_snapshot(target_date: str, now_dt: datetime) -> dict[str, Any]:
    completed_rows = _filter_completed_fallback_scalps(_collect_trade_rows(target_date))
    completed_count = len(completed_rows)
    wins = [row for row in completed_rows if _safe_float(row.get("profit_rate")) > 0]
    losses = [row for row in completed_rows if _safe_float(row.get("profit_rate")) < 0]
    win_rate = round((len(wins) / completed_count) * 100, 1) if completed_count else 0.0
    avg_loss_rate = round(sum(_safe_float(row.get("profit_rate")) for row in losses) / len(losses), 2) if losses else 0.0
    realized_pnl_krw = int(sum(_safe_int(row.get("realized_pnl_krw")) for row in completed_rows))
    exit_rule_counts = Counter(
        str((row.get("exit_signal") or {}).get("exit_rule") or row.get("exit_rule") or "unknown")
        for row in losses
    )
    prev_loss_date, prev_avg_loss_rate = _find_previous_trading_day_avg_loss(now_dt)
    avg_loss_delta = (
        round(avg_loss_rate - prev_avg_loss_rate, 2)
        if prev_avg_loss_rate is not None and losses
        else None
    )
    sample_ready = bool(
        completed_count >= 3
        or (now_dt.time() >= BUY_PAUSE_GUARD_TRIGGER_SAMPLE_READY and completed_count >= 2)
    )
    trigger_flags = {
        "win_rate_bad": completed_count >= 3 and win_rate <= 0.0,
        "avg_loss_bad": bool(
            losses
            and (
                avg_loss_rate <= BUY_PAUSE_GUARD_LOSS_RATE_LIMIT
                or (
                    prev_avg_loss_rate is not None
                    and avg_loss_delta is not None
                    and avg_loss_delta <= BUY_PAUSE_GUARD_LOSS_RATE_DELTA_LIMIT
                )
            )
        ),
        "loss_total_bad": realized_pnl_krw <= BUY_PAUSE_GUARD_REALIZED_PNL_LIMIT,
    }
    return {
        "target_date": target_date,
        "evaluated_at": _format_guard_timestamp(now_dt),
        "window_label": f"{BUY_PAUSE_GUARD_TRIGGER_START.strftime('%H:%M')}~{BUY_PAUSE_GUARD_TRIGGER_END.strftime('%H:%M')}",
        "completed_fallback_trades": completed_count,
        "completed_fallback_win_trades": len(wins),
        "completed_fallback_loss_trades": len(losses),
        "fallback_win_rate": win_rate,
        "fallback_losing_avg_loss_rate": avg_loss_rate,
        "fallback_realized_pnl_krw": realized_pnl_krw,
        "fallback_loss_exit_rules": dict(exit_rule_counts),
        "previous_loss_date": prev_loss_date,
        "previous_fallback_losing_avg_loss_rate": prev_avg_loss_rate,
        "fallback_avg_loss_rate_delta_vs_prev": avg_loss_delta,
        "sample_ready": sample_ready,
        "trigger_flags": trigger_flags,
        "triggered_flag_names": [name for name, active in trigger_flags.items() if active],
        "latest_trade_fingerprint": _build_latest_trade_fingerprint(completed_rows),
    }


def _should_alert(metrics_snapshot: dict[str, Any]) -> bool:
    if not bool(metrics_snapshot.get("sample_ready")):
        return False
    return len(metrics_snapshot.get("triggered_flag_names") or []) >= 2


def _next_guard_sequence(state: dict[str, Any], now_dt: datetime) -> int:
    prior_guard_id = str(state.get("active_guard_id") or "").strip()
    current_date_token = now_dt.strftime("%Y%m%d")
    prior_seq = _safe_int(state.get("sequence"))
    if prior_guard_id.startswith(f"BPG-{current_date_token}-"):
        return max(1, prior_seq + 1)
    return 1


def _build_guard_id(state: dict[str, Any], now_dt: datetime) -> tuple[str, int]:
    sequence = _next_guard_sequence(state, now_dt)
    return f"BPG-{now_dt.strftime('%Y%m%d-%H%M')}-{sequence:02d}", sequence


def _format_guard_alert_message(guard_id: str, metrics_snapshot: dict[str, Any]) -> str:
    trigger_names = ", ".join(metrics_snapshot.get("triggered_flag_names") or []) or "-"
    exit_rules = metrics_snapshot.get("fallback_loss_exit_rules") or {}
    exit_rule_text = ", ".join(f"{key}:{value}" for key, value in sorted(exit_rules.items())) or "없음"
    prev_loss_text = (
        f"{metrics_snapshot.get('previous_loss_date')} avg_loss={metrics_snapshot.get('previous_fallback_losing_avg_loss_rate')}%"
        if metrics_snapshot.get("previous_fallback_losing_avg_loss_rate") is not None
        else "없음"
    )
    return (
        f"BUY PAUSE 후보 감지 [{guard_id}]\n"
        f"- 평가시각: {metrics_snapshot.get('evaluated_at')}\n"
        f"- 평가구간: {metrics_snapshot.get('window_label')}\n"
        f"- completed fallback: {metrics_snapshot.get('completed_fallback_trades')}건\n"
        f"- fallback 승률: {metrics_snapshot.get('fallback_win_rate')}%\n"
        f"- fallback 평균손실: {metrics_snapshot.get('fallback_losing_avg_loss_rate')}%\n"
        f"- fallback 실현손익: {int(metrics_snapshot.get('fallback_realized_pnl_krw') or 0):,}원\n"
        f"- 직전 비교: {prev_loss_text}\n"
        f"- 발화 플래그: {trigger_names}\n"
        f"- loss exit_rule 분포: {exit_rule_text}\n"
        f"- 권고: BUY PAUSE 후보\n"
        f"- 승인: /buy_pause_confirm {guard_id}\n"
        f"- 거절: /buy_pause_reject {guard_id}\n"
        "- 상태확인: /pause_status"
    )


def _publish_guard_alert(message: str) -> None:
    try:
        import src.notify.telegram_manager  # noqa: F401
    except Exception as exc:
        log_error(f"[BUY_PAUSE_GUARD] telegram import failed: {exc}")
        return
    EventBus().publish(
        "TELEGRAM_BROADCAST",
        {"message": message, "audience": "ADMIN_ONLY", "parse_mode": None},
    )


def evaluate_buy_pause_guard(
    target_date: str | None = None,
    *,
    now_dt: datetime | None = None,
    send_alert: bool = True,
) -> dict[str, Any]:
    current = _now(now_dt)
    resolved_date = str(target_date or current.strftime("%Y-%m-%d"))
    state = load_buy_pause_guard_state(now_dt=current)
    metrics_snapshot = _build_metrics_snapshot(resolved_date, current)
    latest_trade_fingerprint = str(metrics_snapshot.get("latest_trade_fingerprint") or "")
    should_alert = _should_alert(metrics_snapshot)

    result = {
        "target_date": resolved_date,
        "evaluated_at": _format_guard_timestamp(current),
        "should_alert": should_alert,
        "alert_sent": False,
        "guard_id": str(state.get("active_guard_id") or ""),
        "state_status": str(state.get("status") or ""),
        "metrics_snapshot": metrics_snapshot,
    }

    if not should_alert:
        return result

    active_status = str(state.get("status") or "")
    active_fingerprint = str(state.get("latest_trade_fingerprint") or "")
    if active_status in {"pending", "confirmed", "rejected"} and active_fingerprint == latest_trade_fingerprint:
        result["guard_id"] = str(state.get("active_guard_id") or "")
        result["state_status"] = active_status
        return result

    guard_id, sequence = _build_guard_id(state, current)
    expires_at = current + timedelta(minutes=BUY_PAUSE_GUARD_TTL_MINUTES)
    new_state = {
        "version": BUY_PAUSE_GUARD_VERSION,
        "active_guard_id": guard_id,
        "status": "pending",
        "created_at": _format_guard_timestamp(current),
        "resolved_at": "",
        "expires_at": _format_guard_timestamp(expires_at),
        "trigger_flags": dict(metrics_snapshot.get("trigger_flags") or {}),
        "metrics_snapshot": metrics_snapshot,
        "latest_trade_fingerprint": latest_trade_fingerprint,
        "sequence": sequence,
    }
    save_buy_pause_guard_state(new_state)
    if send_alert:
        _publish_guard_alert(_format_guard_alert_message(guard_id, metrics_snapshot))
        result["alert_sent"] = True
    log_info(
        f"[BUY_PAUSE_GUARD] pending guard created id={guard_id} "
        f"flags={','.join(metrics_snapshot.get('triggered_flag_names') or [])} "
        f"fingerprint={latest_trade_fingerprint}"
    )
    result["guard_id"] = guard_id
    result["state_status"] = "pending"
    return result


def confirm_buy_pause_guard(guard_id: str, *, event_bus=None, now_dt: datetime | None = None) -> dict[str, Any]:
    current = _now(now_dt)
    state = load_buy_pause_guard_state(now_dt=current)
    requested_guard_id = str(guard_id or "").strip()
    active_guard_id = str(state.get("active_guard_id") or "").strip()
    if not requested_guard_id or requested_guard_id != active_guard_id:
        return {"ok": False, "message": "대기 중인 guard_id와 일치하지 않습니다."}
    if str(state.get("status") or "") != "pending":
        return {"ok": False, "message": f"현재 상태는 `{state.get('status') or '-'}` 입니다."}
    expires_at = _parse_guard_timestamp(state.get("expires_at"))
    if expires_at and expires_at <= current:
        state["status"] = "expired"
        state["resolved_at"] = _format_guard_timestamp(current)
        save_buy_pause_guard_state(state)
        return {"ok": False, "message": "guard 승인 가능 시간이 지났습니다. 필요하면 /pause 를 직접 사용하세요."}

    paused = set_buy_side_pause(
        True,
        source="canary_guard",
        reason=requested_guard_id,
        event_bus=event_bus or EventBus(),
    )
    state["status"] = "confirmed"
    state["resolved_at"] = _format_guard_timestamp(current)
    save_buy_pause_guard_state(state)
    return {
        "ok": True,
        "paused": paused,
        "message": (
            f"BUY PAUSE guard `{requested_guard_id}` 승인 완료. "
            f"현재 상태: {'신규 매수/추가매수 중단' if paused else '정상운영'}"
        ),
        "state": state,
    }


def reject_buy_pause_guard(guard_id: str, *, now_dt: datetime | None = None) -> dict[str, Any]:
    current = _now(now_dt)
    state = load_buy_pause_guard_state(now_dt=current)
    requested_guard_id = str(guard_id or "").strip()
    active_guard_id = str(state.get("active_guard_id") or "").strip()
    if not requested_guard_id or requested_guard_id != active_guard_id:
        return {"ok": False, "message": "대기 중인 guard_id와 일치하지 않습니다."}
    if str(state.get("status") or "") != "pending":
        return {"ok": False, "message": f"현재 상태는 `{state.get('status') or '-'}` 입니다."}

    state["status"] = "rejected"
    state["resolved_at"] = _format_guard_timestamp(current)
    save_buy_pause_guard_state(state)
    return {
        "ok": True,
        "message": f"BUY PAUSE guard `{requested_guard_id}` 거절 처리 완료. 동일 fingerprint는 재경보하지 않습니다.",
        "state": state,
    }


def get_buy_pause_guard_status(now_dt: datetime | None = None) -> dict[str, Any]:
    current = _now(now_dt)
    state = load_buy_pause_guard_state(now_dt=current)
    return {
        "state_path": str(BUY_PAUSE_GUARD_STATE_PATH),
        "active_guard_id": str(state.get("active_guard_id") or ""),
        "status": str(state.get("status") or ""),
        "created_at": str(state.get("created_at") or ""),
        "resolved_at": str(state.get("resolved_at") or ""),
        "expires_at": str(state.get("expires_at") or ""),
        "paused": bool(is_trading_paused()),
        "metrics_snapshot": dict(state.get("metrics_snapshot") or {}),
        "latest_trade_fingerprint": str(state.get("latest_trade_fingerprint") or ""),
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="Buy pause guard evaluator and status helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate buy pause guard conditions")
    evaluate_parser.add_argument("--date", dest="target_date", default=None)
    evaluate_parser.add_argument("--no-alert", action="store_true", help="Skip Telegram alert publishing")

    status_parser = subparsers.add_parser("status", help="Show current buy pause guard state")
    status_parser.add_argument("--json", action="store_true", help="Print full JSON payload")

    args = parser.parse_args()

    if args.command == "evaluate":
        result = evaluate_buy_pause_guard(args.target_date, send_alert=not args.no_alert)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "status":
        result = get_buy_pause_guard_status()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(
                f"guard={result.get('active_guard_id') or '-'} "
                f"status={result.get('status') or '-'} paused={result.get('paused')}"
            )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
