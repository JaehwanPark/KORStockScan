"""Send Telegram notices for panic state start/release transitions."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from urllib import parse, request

from src.database.db_manager import DBManager
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT


DEFAULT_STATE_FILE = PROJECT_ROOT / "tmp" / "panic_state_telegram_notify_state.json"

SELL_ACTIVE_STATES = {"PANIC_SELL", "RECOVERY_WATCH"}
SELL_RELEASE_STATES = {"NORMAL", "RECOVERY_CONFIRMED"}
BUY_ACTIVE_STATES = {"PANIC_BUY_WATCH", "PANIC_BUY", "EXHAUSTION_WATCH"}
BUY_RELEASE_STATES = {"NORMAL", "BUYING_EXHAUSTED"}
SELL_RESTART_SUPPRESS_AFTER_RELEASE_SEC = 10 * 60


def _report_session_key(report_file: Path, report: dict) -> str:
    for key in ("target_date", "date", "trade_date"):
        value = str(report.get(key) or "").strip()
        if value:
            return value[:10]
    stem = report_file.stem
    for prefix in (
        "panic_sell_defense_",
        "panic_buying_",
        "market_panic_breadth_",
    ):
        if stem.startswith(prefix):
            return stem.replace(prefix, "", 1)[:10]
    return ""


def _previous_session_key(previous: dict) -> str:
    value = str(previous.get("session_key") or previous.get("target_date") or "").strip()
    if value:
        return value[:10]
    report_file = str(previous.get("report_file") or "")
    stem = Path(report_file).stem
    for prefix in ("panic_sell_defense_", "panic_buying_"):
        if stem.startswith(prefix):
            return stem.replace(prefix, "", 1)[:10]
    return ""


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except OSError:
        return "", ""
    token = str(config.get("TELEGRAM_TOKEN") or "").strip()
    admin_id = str(config.get("ADMIN_ID") or "").strip()
    return token, admin_id


def _load_report(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_state(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _send_telegram(token: str, chat_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


def _load_all_chat_ids() -> list[str]:
    try:
        ids = DBManager().get_telegram_chat_ids()
    except Exception:
        return []
    result: list[str] = []
    for chat_id in ids:
        text = str(chat_id or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _target_chat_ids(audience: str, admin_id: str) -> list[str]:
    if audience == "admin":
        return [admin_id] if admin_id else []
    ids = _load_all_chat_ids()
    if admin_id and admin_id not in ids:
        ids.insert(0, admin_id)
    return ids


def _state_value(kind: str, report: dict) -> str:
    if kind == "panic_sell":
        micro_context = (
            report.get("microstructure_market_context")
            if isinstance(report.get("microstructure_market_context"), dict)
            else {}
        )
        single_market_risk_off = bool(
            micro_context.get("market_panic_breadth_single_market_risk_off_advisory")
        )
        if str(report.get("panic_state") or "UNKNOWN") == "NORMAL" and single_market_risk_off:
            return "RECOVERY_WATCH"
        return str(report.get("panic_state") or "UNKNOWN")
    if kind == "panic_buying":
        return str(report.get("panic_buy_state") or "UNKNOWN")
    raise ValueError(f"unsupported kind: {kind}")


def _state_phase(kind: str, value: str) -> str:
    if kind == "panic_sell":
        if value in SELL_ACTIVE_STATES:
            return "active"
        if value in SELL_RELEASE_STATES:
            return "released"
        return "unknown"
    if value in BUY_ACTIVE_STATES:
        return "active"
    if value in BUY_RELEASE_STATES:
        return "released"
    return "unknown"


def _transition(
    previous_phase: str | None,
    current_phase: str,
    *,
    force: bool,
    current_value: str = "",
) -> str:
    if force:
        return "start" if current_phase == "active" else "release"
    previous_effective_phase = "active" if previous_phase == "release_pending" else previous_phase
    if previous_effective_phase != "active" and current_phase == "active":
        return "start"
    if previous_effective_phase == "active" and current_phase == "released":
        if previous_phase != "release_pending":
            return "release_pending"
        return "release"
    return "none"


SELL_CONTEXT_PRIORITY = {
    "panic_sell_watch": 0,
    "market_breadth_watch": 1,
    "microstructure_panic": 2,
    "stop_loss_cluster": 3,
    "market_and_stop_loss": 4,
    "market_and_micro_panic": 4,
}


def _safe_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_bar(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "░░░░░░░░░░░░ 확인중"
    score = max(0.0, min(1.0, numeric))
    total = 12
    filled = int(round(score * total))
    empty = total - filled
    if score >= 0.75:
        label = "위험 높음"
        icon = "🔴"
    elif score >= 0.45:
        label = "주의"
        icon = "🟠"
    else:
        label = "낮음"
        icon = "🟢"
    pct = int(round(score * 100))
    return f"{icon} {'▰' * filled}{'▱' * empty} {pct}% · {label}"


def _sell_context_label(report: dict) -> str:
    reasons = [str(item or "") for item in (report.get("panic_state_reasons") or [])]
    micro_context = (
        report.get("microstructure_market_context")
        if isinstance(report.get("microstructure_market_context"), dict)
        else {}
    )
    market_breadth_only = any("market breadth risk-off watch without panic confirmation" in item for item in reasons)
    market_breadth_risk_off = bool(micro_context.get("market_panic_breadth_risk_off_advisory"))
    single_market_risk_off = bool(micro_context.get("market_panic_breadth_single_market_risk_off_advisory"))
    micro_panic = int((report.get("microstructure_detector") or {}).get("panic_signal_count", 0) or 0) > 0
    panic_metrics = report.get("panic_metrics") if isinstance(report.get("panic_metrics"), dict) else {}
    stop_cluster = bool(panic_metrics.get("panic_detected"))
    market_weak = market_breadth_risk_off or single_market_risk_off or market_breadth_only
    if market_weak and stop_cluster:
        return "market_and_stop_loss"
    if market_weak and micro_panic:
        return "market_and_micro_panic"
    if market_weak:
        return "market_breadth_watch"
    if stop_cluster:
        return "stop_loss_cluster"
    if micro_panic:
        return "microstructure_panic"
    return "panic_sell_watch"


def _sell_context_escalated(previous_context: str | None, current_context: str) -> bool:
    previous_score = SELL_CONTEXT_PRIORITY.get(str(previous_context or ""), -1)
    current_score = SELL_CONTEXT_PRIORITY.get(current_context, 0)
    return current_score > previous_score


def _sell_notice_copy(context: str) -> tuple[str, str, str]:
    if context == "market_breadth_watch":
        return (
            "⚠️ 시장 전반 약세 주의",
            "지수와 업종 전반이 약해졌습니다. 아직 개별 종목의 급한 매도 흐름이나 반복 청산은 뚜렷하지 않습니다.",
            "시장 전반 약세 관찰",
        )
    if context == "stop_loss_cluster":
        return (
            "⚠️ 손실 방어 구간 진입",
            "최근 보유/감시 종목에서 손실 확정성 청산이 평소보다 많이 발생했습니다. 새 진입은 보수적으로 보고 기존 안전장치는 유지합니다.",
            "손실 방어 구간",
        )
    if context == "microstructure_panic":
        return (
            "⚠️ 개별 종목 급매도 주의",
            "일부 종목에서 짧은 시간에 매도 압력이 강해졌습니다. 무리한 신규 진입보다 가격 안정 여부를 먼저 확인할 구간입니다.",
            "개별 종목 급매도 감지",
        )
    if context == "market_and_stop_loss":
        return (
            "⚠️ 시장 약세 + 손실 방어 구간",
            "시장 전반이 약한 가운데 손실 확정성 청산도 늘었습니다. 신규 진입은 더 보수적으로 보고, 자동매매 설정은 바꾸지 않습니다.",
            "시장 약세와 손실 방어 동시 감지",
        )
    if context == "market_and_micro_panic":
        return (
            "⚠️ 시장 약세 + 급매도 확산 주의",
            "시장 전반이 약한 가운데 일부 종목의 매도 압력도 강해졌습니다. 가격 안정 신호가 확인되기 전까지 추격 진입은 피해야 합니다.",
            "시장 약세와 개별 급매도 동시 감지",
        )
    return (
        "⚠️ 패닉셀 주의",
        "시장에 급한 매도세가 감지되었습니다. 신규 진입은 평소보다 더 보수적으로 볼 구간입니다.",
        "패닉셀 관찰",
    )


def _message_for_sell(report: dict, transition: str) -> str:
    micro = report.get("microstructure_detector") if isinstance(report.get("microstructure_detector"), dict) else {}
    micro_metrics = micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}
    if transition == "release":
        title = "✅ 패닉셀 경보 해제"
        body = "급한 매도세가 진정되어 패닉셀 관찰을 종료합니다."
        intensity_line = "- 해제 상태\n  🟢 회복 확인 · 신규 자동매매 변경 없음"
    elif transition == "status":
        title = "ℹ️ 패닉셀 알림 테스트"
        body = "현재 패닉셀 알림 상태를 관리자 테스트로 확인합니다."
        intensity_line = f"- 체감 강도\n  {_score_bar(micro_metrics.get('max_panic_score'))}"
    else:
        context = _sell_context_label(report)
        title, body, stage_label = _sell_notice_copy(context)
        if transition == "update":
            title = title.replace("⚠️", "🔄", 1)
        intensity_line = f"- 체감 강도\n  {_score_bar(micro_metrics.get('max_panic_score'))}"
    return "\n".join(
        [
            title,
            body,
            f"- 현재 단계\n  {stage_label}" if transition not in {"release", "status"} else "",
            intensity_line,
            "- 자동매매 변경: 없음",
        ]
    ).replace("\n\n", "\n")


def _message_for_buying(report: dict, transition: str) -> str:
    metrics = report.get("panic_buy_metrics") if isinstance(report.get("panic_buy_metrics"), dict) else {}
    if transition == "release":
        title = "✅ 패닉바잉 경보 해제"
        body = "급한 매수세가 진정되어 패닉바잉 관찰을 종료합니다."
        intensity_line = "- 해제 상태\n  🟢 과열 진정 · 신규 자동매매 변경 없음"
    elif transition == "status":
        title = "ℹ️ 패닉바잉 알림 테스트"
        body = "현재 패닉바잉 알림 상태를 관리자 테스트로 확인합니다."
        intensity_line = f"- 체감 강도\n  {_score_bar(metrics.get('max_panic_buy_score'))}"
    else:
        title = "⚠️ 패닉바잉 주의"
        body = "시장에 급한 매수세가 감지되었습니다. 단기 과열과 소진 가능성을 함께 볼 구간입니다."
        intensity_line = f"- 체감 강도\n  {_score_bar(metrics.get('max_panic_buy_score'))}"
    return "\n".join(
        [
            title,
            body,
            intensity_line,
            "- 자동매매 변경: 없음",
        ]
    )


def _build_message(kind: str, report: dict, transition: str) -> str:
    if kind == "panic_sell":
        return _message_for_sell(report, transition)
    return _message_for_buying(report, transition)


def notify_from_report(
    report_file: Path,
    *,
    kind: str,
    audience: str = "all",
    state_file: Path = DEFAULT_STATE_FILE,
    force: bool = False,
    now_ts: float | None = None,
) -> str:
    if str(os.getenv("KORSTOCKSCAN_PANIC_STATE_TELEGRAM_NOTIFY_ENABLED", "true")).lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return "disabled"
    report = _load_report(report_file)
    if not report:
        return "missing_report"
    current_value = _state_value(kind, report)
    current_phase = _state_phase(kind, current_value)
    if current_phase == "unknown":
        return "unknown_state"

    state = _load_state(state_file)
    previous = state.get(kind) if isinstance(state.get(kind), dict) else {}
    previous_phase = str(previous.get("phase") or "") or None
    current_session_key = _report_session_key(report_file, report)
    previous_session_key = _previous_session_key(previous) if isinstance(previous, dict) else ""
    stale_previous_session = (
        not force
        and previous_phase in {"active", "release_pending"}
        and bool(current_session_key)
        and previous_session_key != current_session_key
    )
    if stale_previous_session:
        previous_phase = None
    previous_value = str(previous.get("state") or "") if isinstance(previous, dict) else ""
    transition = _transition(previous_phase, current_phase, force=force, current_value=current_value)
    current_context = _sell_context_label(report) if kind == "panic_sell" else ""
    previous_context = str(previous.get("context_label") or "") if isinstance(previous, dict) else ""
    if (
        kind == "panic_sell"
        and transition == "none"
        and previous_phase == "active"
        and current_phase == "active"
        and (bool(previous_context) or previous_value == current_value)
        and _sell_context_escalated(previous_context, current_context)
    ):
        transition = "update"

    now = time.time() if now_ts is None else now_ts
    previous_last_notification = (
        previous.get("last_notification") if isinstance(previous.get("last_notification"), dict) else {}
    )
    suppress_sell_restart_after_release = False
    if not force and kind == "panic_sell" and transition == "start" and previous_phase == "released":
        previous_release_ts = _safe_float(previous_last_notification.get("sent_at_ts"))
        suppress_sell_restart_after_release = (
            previous_last_notification.get("transition") == "release"
            and bool(current_session_key)
            and previous_session_key == current_session_key
            and previous_release_ts is not None
            and now - previous_release_ts <= SELL_RESTART_SUPPRESS_AFTER_RELEASE_SEC
        )
        if suppress_sell_restart_after_release:
            transition = "restart_suppressed_after_release"

    if transition == "restart_suppressed_after_release":
        next_phase = previous_phase or "released"
        next_value = previous_value or current_value
    else:
        next_phase = "release_pending" if transition == "release_pending" else current_phase
        next_value = current_value
    next_state = {
        "phase": next_phase,
        "state": next_value,
        "session_key": current_session_key,
        "updated_at_ts": now,
        "report_file": str(report_file),
    }
    if kind == "panic_sell":
        next_state["context_label"] = current_context
    if isinstance(previous, dict) and isinstance(previous.get("last_notification"), dict):
        next_state["last_notification"] = previous["last_notification"]

    if transition in {"none", "release_pending", "restart_suppressed_after_release"}:
        state[kind] = next_state
        _write_state(state_file, state)
        if transition == "restart_suppressed_after_release":
            return "restart_suppressed_after_release"
        if stale_previous_session and current_phase == "released":
            return "stale_previous_active_reset"
        return "release_pending" if transition == "release_pending" else "no_transition"

    token, admin_id = _load_telegram_config()
    if not token:
        return "missing_config"
    chat_ids = _target_chat_ids(audience, admin_id)
    if not chat_ids:
        return "missing_recipients"

    message = _build_message(kind, report, transition)
    sent = 0
    for chat_id in chat_ids:
        try:
            _send_telegram(token, chat_id, message)
            sent += 1
        except Exception:
            continue
    if sent <= 0:
        return "send_failed"
    next_state["last_notification"] = {
        "transition": transition,
        "audience": audience,
        "sent_count": sent,
        "sent_at_ts": now,
        "state": current_value,
    }
    state[kind] = next_state
    _write_state(state_file, state)
    return "sent"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notify Telegram users for panic start/release transitions.")
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--kind", choices=["panic_sell", "panic_buying"], required=True)
    parser.add_argument("--audience", choices=["all", "admin"], default="all")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--force", action="store_true", help="Send a status notice even without a transition.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    status = notify_from_report(
        Path(args.report_file),
        kind=args.kind,
        audience=args.audience,
        state_file=Path(args.state_file),
        force=bool(args.force),
    )
    print(f"[INFO] panic state Telegram notify status={status} kind={args.kind} audience={args.audience}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
