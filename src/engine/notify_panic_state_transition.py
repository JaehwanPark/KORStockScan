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
    micro_panic = int((report.get("microstructure_detector") or {}).get("panic_signal_count", 0) or 0) > 0
    panic_metrics = report.get("panic_metrics") if isinstance(report.get("panic_metrics"), dict) else {}
    stop_cluster = bool(panic_metrics.get("panic_detected"))
    if market_breadth_only or (market_breadth_risk_off and not micro_panic and not stop_cluster):
        return "market_breadth_watch"
    if stop_cluster:
        return "stop_loss_cluster"
    if micro_panic:
        return "microstructure_panic"
    return "panic_sell_watch"


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
        if context == "market_breadth_watch":
            title = "⚠️ 시장 breadth risk-off 주의"
            body = "시장/업종 breadth가 약해졌지만 개별 micro panic이나 손절 cluster는 아직 확인되지 않았습니다."
        else:
            title = "⚠️ 패닉셀 주의"
            body = "시장에 급한 매도세가 감지되었습니다. 신규 진입은 평소보다 더 보수적으로 볼 구간입니다."
        intensity_line = f"- 체감 강도\n  {_score_bar(micro_metrics.get('max_panic_score'))}"
    return "\n".join(
        [
            title,
            body,
            intensity_line,
            "- 자동매매 변경: 없음",
        ]
    )


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
    transition = _transition(previous_phase, current_phase, force=force, current_value=current_value)

    now = time.time() if now_ts is None else now_ts
    next_phase = "release_pending" if transition == "release_pending" else current_phase
    next_state = {
        "phase": next_phase,
        "state": current_value,
        "updated_at_ts": now,
        "report_file": str(report_file),
    }

    if transition in {"none", "release_pending"}:
        state[kind] = next_state
        _write_state(state_file, state)
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
