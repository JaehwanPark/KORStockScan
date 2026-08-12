"""Admin-only Telegram notices for Hanwha Ocean widget entry and exit events.

The notifier consumes immutable advisory events.  It has no account, order,
quantity, token lifecycle, or trading-runtime authority.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib import parse, request

from src.engine.monitoring import hanwha_ocean_widget_contract as contract
from src.engine.monitoring.hanwha_ocean_widget_contract import (
    HANWHA_OCEAN_CODE,
    HANWHA_OCEAN_NAME,
)
from src.engine.monitoring.samsung_widget_contract import ADVISORY_AUTHORITY, KST
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "hanwha_ocean_widget_telegram_notify_state.json"
)
DEFAULT_RETRY_SEC = 30

ConfigLoader = Callable[[], tuple[str, str]]
Sender = Callable[[str, str, str], None]


def _env_enabled() -> bool:
    return str(
        os.getenv("KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_TELEGRAM_ENABLED", "true")
    ).strip().lower() not in {"0", "false", "no", "off"}


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return (
        str(payload.get("TELEGRAM_TOKEN") or "").strip(),
        str(payload.get("ADMIN_ID") or "").strip(),
    )


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=5) as response:
        response.read()


def _as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=KST)
    return value.astimezone(KST)


def _timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    return _as_kst(parsed) if parsed.tzinfo is not None else None


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _format_price(value: object) -> str:
    parsed = _positive_int(value)
    return f"{parsed:,}원" if parsed is not None else "-"


def _load_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    os.replace(temporary, path)


def build_entry_message(payload: dict[str, Any], event: dict[str, Any]) -> str:
    tier = str(event.get("signal_tier") or "STANDARD")
    state = str(event.get("state") or "ENTRY_CAUTION")
    valid_until = _timestamp(event.get("valid_until"))
    valid_text = valid_until.strftime("%H:%M:%S") if valid_until else "-"
    return "\n".join(
        [
            f"🟠 [{HANWHA_OCEAN_NAME} 진입 신호]",
            f"상태: {state} / 신뢰구간: {tier}",
            f"현재가: {_format_price(payload.get('current_price'))}",
            (
                "권장가격: "
                f"{_format_price(event.get('entry_price_low'))} ~ "
                f"{_format_price(event.get('entry_price_high'))}"
            ),
            f"+1% 기준가: {_format_price(event.get('target_price'))}",
            f"구조 지지: {_format_price(event.get('structural_support'))}",
            f"세션 등락: {event.get('session_return_pct')}%",
            (
                "보조확인: "
                f"상대 {event.get('relative_signal') or event.get('relative_status') or '-'} · "
                f"수급 {event.get('flow_signal') or event.get('flow_status') or '-'} · "
                f"외부 {event.get('external_risk_level') or '-'}"
            ),
            f"유효시각: {valid_text}",
            "조건: KRX 첫 눌림 · 표준 반등거래량 · 청산 후 새 구조 재진입 가능",
            "권한: 관측용 · 자동주문 아님",
        ]
    )


def build_exit_message(payload: dict[str, Any], event: dict[str, Any]) -> str:
    reason = str(event.get("reason") or "")
    reason_label = {
        "hanwha_ocean_target_1pct_reached": "+1% 기준가 도달",
        "hanwha_ocean_completed_close_below_entry_support": "확정 1분봉 지지 이탈",
    }.get(reason, reason or "청산 조건 확인")
    return "\n".join(
        [
            f"🔵 [{HANWHA_OCEAN_NAME} 청산 신호]",
            f"사유: {reason_label}",
            f"참고 청산가: {_format_price(event.get('reference_exit_price'))}",
            f"진입 기준가: {_format_price(event.get('entry_reference_price'))}",
            f"+1% 기준가: {_format_price(event.get('target_price'))}",
            f"구조 지지: {_format_price(event.get('structural_support'))}",
            "보유 여부와 무관한 진입신호 연계 관측입니다.",
            "권한: 관측용 · 자동주문 아님",
        ]
    )


class HanwhaOceanWidgetTelegramNotifier:
    """Send each valid advisory event once to the configured admin chat."""

    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        retry_sec: int = DEFAULT_RETRY_SEC,
        enabled: bool | None = None,
        entry_messages_enabled: bool = True,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.retry_sec = max(1, int(retry_sec))
        self.enabled = _env_enabled() if enabled is None else bool(enabled)
        self.entry_messages_enabled = bool(entry_messages_enabled)
        self._state = _load_state(state_file)

    @staticmethod
    def _valid_event(
        payload: dict[str, Any],
        event: object,
        *,
        expected_type: str,
        observed_at: datetime,
    ) -> bool:
        if not isinstance(event, dict):
            return False
        return bool(
            payload.get("status") == "ok"
            and payload.get("symbol") == HANWHA_OCEAN_CODE
            and contract.advisory_event_contract_is_valid(
                event,
                expected_type=expected_type,
                evaluated_at=observed_at,
            )
        )

    def _save(self) -> None:
        attempts = self._state.get("attempts")
        if isinstance(attempts, dict) and len(attempts) > 20:
            self._state["attempts"] = dict(list(attempts.items())[-20:])
        self._state.update(
            {
                "schema_version": 1,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "telegram_audience": "ADMIN_ONLY",
            }
        )
        _atomic_write(self.state_file, self._state)

    def _observe_event(
        self,
        payload: dict[str, Any],
        event: object,
        *,
        expected_type: str,
        observed_at: datetime,
    ) -> str:
        if not isinstance(event, dict):
            return "no_event"
        event_id = str(event.get("event_id") or "")
        if not self._valid_event(
            payload, event, expected_type=expected_type, observed_at=observed_at
        ):
            return "invalid_event"
        sent_ids = [str(value) for value in self._state.get("sent_event_ids") or []]
        if event_id in sent_ids:
            return "duplicate"

        attempts = self._state.get("attempts")
        attempts = attempts if isinstance(attempts, dict) else {}
        attempt = attempts.get(event_id)
        attempt = attempt if isinstance(attempt, dict) else {}
        last_attempt_at = _timestamp(attempt.get("at"))
        if (
            attempt.get("status") in {"failed", "missing_config"}
            and last_attempt_at is not None
            and (_as_kst(observed_at) - last_attempt_at).total_seconds()
            < self.retry_sec
        ):
            return "retry_wait"

        token, admin_id = self.config_loader()
        now = _as_kst(observed_at)
        if not token or not admin_id:
            attempts[event_id] = {"at": now.isoformat(), "status": "missing_config"}
            self._state["attempts"] = attempts
            self._save()
            return "missing_config"

        message = (
            build_entry_message(payload, event)
            if expected_type == "ENTRY"
            else build_exit_message(payload, event)
        )
        try:
            self.sender(token, admin_id, message)
        except Exception as exc:
            attempts[event_id] = {
                "at": now.isoformat(),
                "status": "failed",
                "error": type(exc).__name__,
            }
            self._state["attempts"] = attempts
            self._save()
            return "send_failed"

        sent_ids.append(event_id)
        self._state["sent_event_ids"] = sent_ids[-20:]
        attempts.pop(event_id, None)
        self._state["attempts"] = attempts
        self._state["last_sent_at"] = now.isoformat()
        self._state["last_sent_event_id"] = event_id
        self._state["last_sent_event_type"] = expected_type
        self._save()
        return "sent"

    def observe(self, payload: dict[str, Any], observed_at: datetime) -> dict[str, str]:
        if not self.enabled:
            return {"entry": "disabled", "exit": "disabled"}
        exit_event = payload.get("exit_event")
        if self._valid_event(
            payload,
            exit_event,
            expected_type="EXIT",
            observed_at=observed_at,
        ):
            return {
                "entry": "exit_event_conflict",
                "exit": self._observe_event(
                    payload,
                    exit_event,
                    expected_type="EXIT",
                    observed_at=observed_at,
                ),
            }
        entry_event = payload.get("entry_event")
        if not self.entry_messages_enabled and self._valid_event(
            payload,
            entry_event,
            expected_type="ENTRY",
            observed_at=observed_at,
        ):
            event_id = str(entry_event.get("event_id") or "")
            if event_id != self._state.get("last_observed_entry_event_id"):
                self._state.update(
                    {
                        "last_observed_entry_event_id": event_id,
                        "entry_telegram_suppressed": True,
                        "entry_telegram_owner": (
                            "widget_auto_trade_accepted_buy_action"
                        ),
                    }
                )
                self._save()
            entry_result = "entry_observed_no_telegram"
        else:
            entry_result = self._observe_event(
                payload,
                entry_event,
                expected_type="ENTRY",
                observed_at=observed_at,
            )
        return {
            "entry": entry_result,
            "exit": self._observe_event(
                payload,
                exit_event,
                expected_type="EXIT",
                observed_at=observed_at,
            ),
        }
