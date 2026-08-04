"""Admin-only Telegram notices for actionable Samsung widget entry advisories.

This module observes the already-confirmed widget advisory output.  It does not
evaluate prices, issue orders, access accounts, or mutate the trading runtime.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib import parse, request

from src.engine.monitoring.samsung_widget_contract import (
    ACTIONABLE_ADVISORY_STATES,
    ADVISORY_AUTHORITY,
    KST,
    SNAPSHOT_MAX_AGE_SEC,
)
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "samsung_widget_entry_telegram_notify_state.json"
)
DEFAULT_REARM_SEC = 60
DEFAULT_RETRY_SEC = 30

ConfigLoader = Callable[[], tuple[str, str]]
Sender = Callable[[str, str, str], None]

_REASON_LABELS = {
    "low_structure_confirmed": "저점 구조 확인",
    "vwap_or_resistance_reclaimed": "VWAP/저항 회복",
    "rebound_volume_confirmed": "반등 거래량 확인",
    "three_five_minute_not_down": "3·5분 추세 비하락",
    "relative_strength_not_weak": "상대강도 양호",
    "spread_within_two_ticks": "스프레드 2틱 이내",
    "same_window_relative_recovery": "동일구간 상대강도 회복",
    "foreign_flow_nonworsening": "외국인 수급 비악화",
    "program_flow_nonworsening": "프로그램 수급 비악화",
    "premarket_aux_supportive": "프리마켓 흐름 보조",
}

_UNMET_LABELS = {
    "foreign_or_program_flow_not_improving": "외국인/프로그램 수급 주의",
    "regular_flow_unavailable": "정규장 수급 확인 제한",
    "premarket_vwap_not_recovered": "프리마켓 VWAP 미회복",
}


def _env_enabled() -> bool:
    return str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ENTRY_TELEGRAM_ENABLED", "true")
    ).strip().lower() not in {"0", "false", "no", "off"}


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    token = str(payload.get("TELEGRAM_TOKEN") or "").strip()
    admin_id = str(payload.get("ADMIN_ID") or "").strip()
    return token, admin_id


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


def _parse_timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return _as_kst(parsed)


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _load_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    os.replace(temporary, path)


def _format_price(value: object) -> str:
    parsed = _positive_int(value)
    return f"{parsed:,}원" if parsed is not None else "-"


def _format_labels(values: object, labels: dict[str, str], *, limit: int) -> str:
    if not isinstance(values, list):
        return "-"
    rendered = [labels.get(str(value), str(value)) for value in values if value]
    return " · ".join(rendered[:limit]) if rendered else "-"


def build_entry_message(payload: dict[str, Any]) -> str:
    advisory = payload.get("advisory") or {}
    state = str(advisory.get("state") or "")
    state_label = "조건부 진입 관찰" if state == "ENTRY_CAUTION" else "진입 조건 충족"
    valid_until = _parse_timestamp(advisory.get("valid_until"))
    valid_text = valid_until.strftime("%H:%M:%S") if valid_until else "-"
    external = advisory.get("external_risk") or {}
    lines = [
        "🟠 [삼성전자 진입 알림]",
        f"상태: {state} / {state_label}",
        f"현재가: {_format_price(payload.get('current_price'))}",
        (
            "권장가격: "
            f"{_format_price(advisory.get('entry_price_low'))}"
            f" ~ {_format_price(advisory.get('entry_price_high'))}"
        ),
        f"무효화 기준: {_format_price(advisory.get('invalidation_price'))}",
        f"근거: {_format_labels(advisory.get('reasons'), _REASON_LABELS, limit=4)}",
        (
            "주의: "
            f"{_format_labels(advisory.get('unmet_conditions'), _UNMET_LABELS, limit=3)}"
        ),
        f"외부위험: {external.get('level') or '-'}",
        f"유효시각: {valid_text}",
        (
            f"세션: {advisory.get('session') or '-'} / "
            f"venue={payload.get('market_venue') or '-'}"
        ),
        "권한: 관측용 · 자동주문 아님",
    ]
    return "\n".join(lines)


class SamsungWidgetEntryTelegramNotifier:
    """Send one admin notice per confirmed actionable advisory episode."""

    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        rearm_sec: int = DEFAULT_REARM_SEC,
        retry_sec: int = DEFAULT_RETRY_SEC,
        enabled: bool | None = None,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.rearm_sec = max(0, int(rearm_sec))
        self.retry_sec = max(1, int(retry_sec))
        self.enabled = _env_enabled() if enabled is None else bool(enabled)
        self._state = _load_state(state_file)

    @staticmethod
    def _scope(payload: dict[str, Any], observed_at: datetime) -> str:
        advisory = payload.get("advisory") or {}
        return f"{_as_kst(observed_at).date().isoformat()}:{advisory.get('session') or '-'}"

    @staticmethod
    def _actionable_contract_valid(
        payload: dict[str, Any], observed_at: datetime
    ) -> bool:
        advisory = payload.get("advisory")
        if not isinstance(advisory, dict):
            return False
        state = str(advisory.get("state") or "")
        source_quality = advisory.get("source_quality") or {}
        low = _positive_int(advisory.get("entry_price_low"))
        high = _positive_int(advisory.get("entry_price_high"))
        advisory_observed_at = _parse_timestamp(
            advisory.get("observed_at") or payload.get("observed_at_kst")
        )
        valid_until = _parse_timestamp(advisory.get("valid_until"))
        observation_age_sec = (
            (_as_kst(observed_at) - advisory_observed_at).total_seconds()
            if advisory_observed_at is not None
            else None
        )
        return bool(
            payload.get("status") == "ok"
            and state in ACTIONABLE_ADVISORY_STATES
            and advisory.get("authority") == ADVISORY_AUTHORITY
            and advisory.get("runtime_effect") is False
            and advisory.get("actual_order_submitted") is False
            and advisory.get("broker_order_forbidden") is True
            and source_quality.get("status") == "PASS"
            and low is not None
            and high is not None
            and low <= high
            and observation_age_sec is not None
            and 0 <= observation_age_sec <= SNAPSHOT_MAX_AGE_SEC
            and valid_until is not None
            and valid_until > _as_kst(observed_at)
        )

    def _save(self) -> None:
        _atomic_write_state(self.state_file, self._state)

    def observe(self, payload: dict[str, Any], observed_at: datetime) -> str:
        """Observe the displayed advisory and send only an admin-only entry notice."""
        if not self.enabled:
            return "disabled"

        now = _as_kst(observed_at)
        advisory = payload.get("advisory") or {}
        state = str(advisory.get("state") or "")
        scope = self._scope(payload, now)
        if self._state.get("scope") != scope:
            self._state = {
                "schema_version": 1,
                "scope": scope,
                "active": False,
                "active_state": None,
                "non_actionable_since": None,
            }

        if state not in ACTIONABLE_ADVISORY_STATES:
            if self._state.get("active") or not self._state.get("non_actionable_since"):
                self._state["active"] = False
                self._state["active_state"] = None
                self._state["non_actionable_since"] = now.isoformat()
                self._save()
            return "not_actionable"

        if not self._actionable_contract_valid(payload, now):
            return "invalid_actionable_contract"

        active_state = str(self._state.get("active_state") or "")
        is_upgrade = bool(
            self._state.get("active")
            and active_state == "ENTRY_CAUTION"
            and state == "ENTRY_READY"
        )
        if self._state.get("active") and not is_upgrade:
            return "duplicate_active_episode"

        non_actionable_since = _parse_timestamp(self._state.get("non_actionable_since"))
        if (
            not is_upgrade
            and self._state.get("last_sent_at")
            and non_actionable_since is not None
            and (now - non_actionable_since).total_seconds() < self.rearm_sec
        ):
            return "rearm_wait"

        last_attempt_at = _parse_timestamp(self._state.get("last_attempt_at"))
        if (
            self._state.get("last_attempt_status") in {"failed", "missing_config"}
            and last_attempt_at is not None
            and (now - last_attempt_at).total_seconds() < self.retry_sec
        ):
            return "retry_wait"

        token, admin_id = self.config_loader()
        if not token or not admin_id:
            self._state["last_attempt_at"] = now.isoformat()
            self._state["last_attempt_status"] = "missing_config"
            self._save()
            return "missing_config"

        self._state["last_attempt_at"] = now.isoformat()
        try:
            self.sender(token, admin_id, build_entry_message(payload))
        except Exception as exc:
            self._state["last_attempt_status"] = "failed"
            self._state["last_error"] = type(exc).__name__
            self._save()
            return "send_failed"

        self._state.update(
            {
                "active": True,
                "active_state": state,
                "non_actionable_since": None,
                "last_sent_at": now.isoformat(),
                "last_sent_state": state,
                "last_attempt_status": "sent",
                "last_error": None,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "telegram_audience": "ADMIN_ONLY",
                "telegram_event_type": "samsung_widget_entry_advisory",
                "last_current_price": _positive_int(payload.get("current_price")),
                "last_entry_price_low": _positive_int(advisory.get("entry_price_low")),
                "last_entry_price_high": _positive_int(
                    advisory.get("entry_price_high")
                ),
                "last_invalidation_price": _positive_int(
                    advisory.get("invalidation_price")
                ),
                "last_valid_until": advisory.get("valid_until"),
            }
        )
        self._save()
        return "sent"
