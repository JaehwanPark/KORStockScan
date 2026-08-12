"""Admin-only Telegram notices for actionable Samsung widget advisories.

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
    exit_advisory_contract_is_valid,
    session_context,
)
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "samsung_widget_entry_telegram_notify_state.json"
)
DEFAULT_AUDIT_DIRECTORY = (
    PROJECT_ROOT / "data" / "report" / "samsung_widget_telegram_notify_audit"
)
DEFAULT_REARM_SEC = 120
DEFAULT_RETRY_SEC = 30

NOTIFICATION_AUDIT_CONTRACT = {
    "metric_role": "diagnostic_notification_delivery",
    "decision_authority": ADVISORY_AUTHORITY,
    "window_policy": "append_only_trade_date_entry_linked_episode",
    "sample_floor": "one_valid_notification_attempt",
    "primary_decision_metric": "telegram_api_send_status",
    "source_quality_gate": "fresh_contract_valid_advisory_and_active_entry_episode",
    "forbidden_uses": [
        "real_order_submission",
        "account_or_quantity_decision",
        "trading_runtime_threshold",
        "provider_route_change",
        "bot_process_control",
        "automatic_live_promotion",
    ],
}

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
    "recovery_episode_armed": "반등 구조 연속 확인",
    "recent_resistance_reclaimed": "직전 저항 회복",
    "pullback_within_two_ticks": "저항 2틱 이내 눌림",
    "recent_rebound_volume_grace": "최근 반등 거래량 유지",
    "early_reversal_retest_confirmed": "저점 재시험 반등 확인",
    "recent_runup_near_rolling_high": "최근 저점 대비 상승 후 고점 근접",
}

_UNMET_LABELS = {
    "vwap_or_resistance_reclaimed": "VWAP/저항 회복 대기",
    "rebound_volume_confirmed": "반등 거래량 확인 대기",
    "pullback_from_recent_high_pending": "최근 고점 대비 눌림 대기",
    "foreign_or_program_flow_not_improving": "외국인/프로그램 수급 주의",
    "regular_flow_unavailable": "정규장 수급 확인 제한",
    "premarket_vwap_not_recovered": "프리마켓 VWAP 미회복",
    "resistance_reclaim_pullback_pending": "저항 돌파 후 눌림 대기",
    "nxt_aftermarket_reclaim_structure_unconfirmed": (
        "애프터마켓 저항·상승구조 미확인"
    ),
}

_EXIT_REASON_LABELS = {
    "rolling_peak_drawdown": "고점 대비 하락폭 확대",
    "prior_five_bar_support_broken": "직전 5개 봉 지지 이탈",
    "below_session_vwap": "세션 VWAP 하회",
    "three_or_five_minute_down": "3분 또는 5분 하락 추세",
    "broken_support_reclaim_failed": "이탈 지지 회복 실패",
    "three_and_five_minute_down": "3분·5분 동시 하락 추세",
    "completed_bar_lower_high": "확정봉 고점 하락",
    "completed_red_bar_after_peak": "고점 이후 음봉 확인",
    "local_peak_rollover_continued": "국지 고점 이탈 지속",
    "three_minute_down_confirmed": "3분 하락 추세 확인",
}


def _env_enabled() -> bool:
    return str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_TELEGRAM_ENABLED", "true")
    ).strip().lower() not in {"0", "false", "no", "off"}


def _entry_env_enabled() -> bool:
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


def _minute_bar_key(value: object) -> str:
    parsed = _parse_timestamp(value)
    return parsed.strftime("%Y%m%d%H%M00") if parsed is not None else ""


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


def _format_entry_price_range(advisory: dict[str, Any]) -> str:
    low = _positive_int(advisory.get("entry_price_low"))
    high = _positive_int(advisory.get("entry_price_high"))
    if low is not None and high == low:
        return _format_price(low)
    return f"{_format_price(low)} ~ {_format_price(high)}"


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
    derived = advisory.get("derived")
    invalidation_confirmation = (
        derived.get("invalidation_confirmation") if isinstance(derived, dict) else None
    )
    invalidation_suffix = (
        " (1분봉 종가 이탈 또는 2틱 이탈+매도압력)"
        if isinstance(invalidation_confirmation, dict)
        and invalidation_confirmation.get("policy")
        == "completed_1m_close_or_two_tick_live_break_with_ask_pressure"
        else ""
    )
    lines = [
        "🟠 [삼성전자 진입 알림]",
        f"상태: {state} / {state_label}",
        f"현재가: {_format_price(payload.get('current_price'))}",
        f"권장가격: {_format_entry_price_range(advisory)}",
        "무효화 기준: "
        f"{_format_price(advisory.get('invalidation_price'))}{invalidation_suffix}",
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


def build_exit_message(payload: dict[str, Any]) -> str:
    """Render an entry-linked EXIT_READY observation for the admin."""
    advisory = payload.get("exit_advisory") or {}
    valid_until = _parse_timestamp(advisory.get("valid_until"))
    valid_text = valid_until.strftime("%H:%M:%S") if valid_until else "-"
    drawdown = advisory.get("peak_drawdown_pct")
    try:
        drawdown_text = f"{float(drawdown):.2f}%"
    except (TypeError, ValueError):
        drawdown_text = "-"
    continuity = advisory.get("continuity") or {}
    local_peak_exit = bool(
        isinstance(continuity, dict)
        and continuity.get("caution_kind") == "local_peak_rollover"
    )
    lines = [
        "🔴 [삼성전자 청산 알림]",
        (
            "상태: EXIT_READY / 고점 이탈·하락 지속 확인"
            if local_peak_exit
            else "상태: EXIT_READY / 지지 이탈·하락 구조 확인"
        ),
        f"현재가: {_format_price(payload.get('current_price'))}",
        f"청산 참고가: {_format_price(advisory.get('reference_exit_price'))}",
        (
            f"확인 지지: {_format_price(advisory.get('broken_support'))}"
            if local_peak_exit
            else f"이탈 지지: {_format_price(advisory.get('broken_support'))}"
        ),
        (
            f"관측 고점: {_format_price(advisory.get('peak_price'))}"
            f" / 고점대비 {drawdown_text}"
        ),
        f"근거: {_format_labels(advisory.get('reasons'), _EXIT_REASON_LABELS, limit=5)}",
        f"유효시각: {valid_text}",
        (
            f"세션: {advisory.get('session') or '-'} / "
            f"venue={payload.get('market_venue') or '-'}"
        ),
        "권한: 수집기 진입 에피소드 연계 관측용 · 자동매도/주문 아님",
    ]
    return "\n".join(lines)


class SamsungWidgetEntryTelegramNotifier:
    """Send one admin notice per confirmed entry-linked advisory episode.

    The historical class name remains as a compatibility surface for the
    collector and service unit. Entry and exit retry/dedup state are kept
    independently so an unavailable Telegram call cannot cross-suppress the
    other advisory type.
    """

    def __init__(
        self,
        *,
        state_file: Path = DEFAULT_STATE_FILE,
        config_loader: ConfigLoader = _load_telegram_config,
        sender: Sender = _send_telegram,
        rearm_sec: int = DEFAULT_REARM_SEC,
        retry_sec: int = DEFAULT_RETRY_SEC,
        enabled: bool | None = None,
        entry_messages_enabled: bool | None = None,
        audit_directory: Path | None = None,
    ) -> None:
        self.state_file = state_file
        self.config_loader = config_loader
        self.sender = sender
        self.rearm_sec = max(0, int(rearm_sec))
        self.retry_sec = max(1, int(retry_sec))
        self.enabled = _env_enabled() if enabled is None else bool(enabled)
        self.entry_messages_enabled = (
            _entry_env_enabled()
            if entry_messages_enabled is None
            else bool(entry_messages_enabled)
        )
        self.audit_directory = (
            audit_directory
            if audit_directory is not None
            else (
                DEFAULT_AUDIT_DIRECTORY
                if state_file == DEFAULT_STATE_FILE
                else state_file.parent / "telegram_audit"
            )
        )
        self._state = _load_state(state_file)

    @staticmethod
    def _scope(payload: dict[str, Any], observed_at: datetime) -> str:
        # One advisory position episode may span NXT premarket, KRX regular,
        # and NXT aftermarket.  Session-scoped state used to forget an open
        # premarket episode at 09:00 and could emit a second "new entry"
        # notice before the first episode was invalidated or exited.
        del payload
        return _as_kst(observed_at).date().isoformat()

    def _ensure_daily_scope(self, scope: str) -> None:
        state_before = dict(self._state)
        stored_scope = str(self._state.get("scope") or "")
        stored_date = stored_scope.split(":", 1)[0]
        if stored_date == scope:
            # Migrate the former YYYY-MM-DD:SESSION state in place so a
            # collector restart or deployment cannot reopen today's episode.
            self._state["schema_version"] = 2
            self._state["scope"] = scope
            self._state.setdefault(
                "entry_episode_status",
                "open" if self._state.get("active") else "closed",
            )
            self._state.setdefault(
                "entry_episode_opened_at", self._state.get("last_sent_at")
            )
            self._state.setdefault(
                "entry_episode_opened_bar",
                _minute_bar_key(
                    self._state.get("entry_episode_opened_at")
                    or self._state.get("last_sent_at")
                ),
            )
            last_exit_at = _parse_timestamp(self._state.get("last_exit_sent_at"))
            non_actionable_at = _parse_timestamp(
                self._state.get("non_actionable_since")
            )
            if not self._state.get("active") and last_exit_at is not None:
                if not self._state.get("entry_episode_closed_at"):
                    self._state["entry_episode_closed_at"] = last_exit_at.isoformat()
                if not self._state.get("entry_episode_close_reason"):
                    self._state["entry_episode_close_reason"] = (
                        "legacy_exit_notification"
                    )
                if not self._state.get("entry_episode_close_reference_price"):
                    self._state["entry_episode_close_reference_price"] = _positive_int(
                        self._state.get("last_exit_reference_price")
                    )
                if non_actionable_at is None or last_exit_at > non_actionable_at:
                    self._state["non_actionable_since"] = last_exit_at.isoformat()
            if self._state != state_before:
                self._save()
            return
        self._state = {
            "schema_version": 2,
            "scope": scope,
            "active": False,
            "active_state": None,
            "entry_episode_status": "none",
            "non_actionable_since": None,
        }
        self._save()

    def _close_entry_episode(
        self,
        *,
        now: datetime,
        reason: str,
        reference_price: int | None = None,
        session: object = None,
        peak_price: int | None = None,
    ) -> None:
        self._state.update(
            {
                "active": False,
                "active_state": None,
                "entry_episode_status": "closed",
                "entry_episode_closed_at": now.isoformat(),
                "entry_episode_close_reason": reason,
                "entry_episode_close_reference_price": reference_price,
                "entry_episode_closed_session": session,
                "entry_episode_peak_price": peak_price,
                "non_actionable_since": now.isoformat(),
            }
        )
        self._save()

    @staticmethod
    def _latest_completed_bar(payload: dict[str, Any]) -> dict[str, Any]:
        latest_bar = (payload.get("observation") or {}).get("latest_completed_bar")
        if not isinstance(latest_bar, dict):
            latest_bar = payload.get("latest_completed_bar")
        return latest_bar if isinstance(latest_bar, dict) else {}

    def _active_episode_invalidation_reason(
        self, payload: dict[str, Any]
    ) -> str | None:
        """Return a displayed-invalidation breach for the open entry episode.

        The stored hard invalidation price is the user-facing episode boundary.
        A completed one-minute close at/below it closes the advisory episode. A
        live touch also closes it when the current advisory confirms ask
        pressure. Missing/stale payloads never synthesize an invalidation.
        """
        advisory = payload.get("advisory") or {}
        source_quality = advisory.get("source_quality") or {}
        if (
            not self._state.get("active")
            or payload.get("status") != "ok"
            or source_quality.get("status") != "PASS"
        ):
            return None
        invalidation_price = _positive_int(
            self._state.get("entry_episode_invalidation_price")
            or self._state.get("last_invalidation_price")
        )
        if invalidation_price is None:
            return None

        latest_bar = self._latest_completed_bar(payload)
        completed_bar_time = str(latest_bar.get("source_time") or "")
        opened_bar_time = str(
            self._state.get("entry_episode_opened_bar")
            or _minute_bar_key(
                self._state.get("entry_episode_opened_at")
                or self._state.get("last_sent_at")
            )
        )
        completed_close = (
            _positive_int(latest_bar.get("close"))
            if isinstance(latest_bar, dict)
            else None
        )
        completed_after_entry = bool(
            len(completed_bar_time) == 14
            and len(opened_bar_time) == 14
            and completed_bar_time > opened_bar_time
        )
        if (
            completed_after_entry
            and completed_close is not None
            and completed_close <= invalidation_price
        ):
            return "completed_1m_close_invalidation"

        live_reversal = advisory.get("live_reversal")
        if not isinstance(live_reversal, dict):
            derived = advisory.get("derived")
            live_reversal = (
                derived.get("live_reversal") if isinstance(derived, dict) else {}
            )
        current_price = _positive_int(payload.get("current_price"))
        if (
            current_price is not None
            and current_price <= invalidation_price
            and isinstance(live_reversal, dict)
            and live_reversal.get("ask_pressure") is True
        ):
            return "live_invalidation_with_ask_pressure"
        return None

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
        invalidation_price = _positive_int(advisory.get("invalidation_price"))
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
            and invalidation_price is not None
            and observation_age_sec is not None
            and 0 <= observation_age_sec <= SNAPSHOT_MAX_AGE_SEC
            and valid_until is not None
            and valid_until > _as_kst(observed_at)
        )

    @staticmethod
    def _exit_contract_valid(payload: dict[str, Any], observed_at: datetime) -> bool:
        exit_advisory = payload.get("exit_advisory")
        snapshot_at = _parse_timestamp(payload.get("observed_at_kst"))
        now = _as_kst(observed_at)
        context = session_context(now)
        valid_until = (
            _parse_timestamp(exit_advisory.get("valid_until"))
            if isinstance(exit_advisory, dict)
            else None
        )
        observation_age_sec = (
            (now - snapshot_at).total_seconds() if snapshot_at is not None else None
        )
        return bool(
            payload.get("status") == "ok"
            and isinstance(exit_advisory, dict)
            and exit_advisory.get("state") == "EXIT_READY"
            and context.active
            and payload.get("market_venue") == context.market_venue
            and snapshot_at is not None
            and observation_age_sec is not None
            and 0 <= observation_age_sec <= SNAPSHOT_MAX_AGE_SEC
            and valid_until is not None
            and valid_until > now
            and exit_advisory_contract_is_valid(
                exit_advisory,
                snapshot_observed_at=snapshot_at,
                context=context,
                evaluated_at=now,
            )
        )

    @staticmethod
    def _exit_episode_key(payload: dict[str, Any], scope: str) -> str:
        exit_advisory = payload.get("exit_advisory") or {}
        continuity = exit_advisory.get("continuity") or {}
        ready_bar = (
            continuity.get("ready_bar") if isinstance(continuity, dict) else None
        )
        return ":".join(
            [
                scope,
                str(ready_bar or "unknown_ready_bar"),
                str(_positive_int(exit_advisory.get("broken_support")) or 0),
                str(_positive_int(exit_advisory.get("peak_price")) or 0),
            ]
        )

    def _save(self) -> None:
        _atomic_write_state(self.state_file, self._state)

    def _append_delivery_audit(
        self,
        *,
        payload: dict[str, Any],
        observed_at: datetime,
        event_type: str,
        status: str,
        episode_key: str,
    ) -> None:
        """Persist low-volume delivery provenance without affecting advisory flow."""
        now = _as_kst(observed_at)
        advisory = payload.get("advisory") or {}
        exit_advisory = payload.get("exit_advisory") or {}
        row = {
            "observed_at_kst": now.isoformat(),
            "event_type": event_type,
            "status": status,
            "episode_key": episode_key,
            "current_price": _positive_int(payload.get("current_price")),
            "advisory_state": advisory.get("state"),
            "exit_advisory_state": exit_advisory.get("state"),
            "session": advisory.get("session") or exit_advisory.get("session"),
            "market_venue": payload.get("market_venue"),
            "authority": ADVISORY_AUTHORITY,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "telegram_audience": "ADMIN_ONLY",
            "metric_contract": NOTIFICATION_AUDIT_CONTRACT,
        }
        target = self.audit_directory / (
            f"samsung_widget_telegram_notify_{now.strftime('%Y%m%d')}.jsonl"
        )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        except OSError as exc:
            self._state["last_audit_error"] = type(exc).__name__
            self._state["last_audit_error_at"] = now.isoformat()
            self._save()
        else:
            self._state["last_audit_error"] = None
            self._state["last_audit_written_at"] = now.isoformat()
            self._save()

    def _observe_exit_ready(
        self, payload: dict[str, Any], *, now: datetime, scope: str
    ) -> str:
        if not self._exit_contract_valid(payload, now):
            return "invalid_exit_contract"
        exit_advisory = payload.get("exit_advisory") or {}
        episode_key = self._exit_episode_key(payload, scope)
        if (
            self._state.get("last_exit_episode_key") == episode_key
            and self._state.get("last_exit_attempt_status") == "sent"
        ):
            return "duplicate_exit_episode"

        last_attempt_at = _parse_timestamp(self._state.get("last_exit_attempt_at"))
        if (
            self._state.get("last_exit_episode_key") == episode_key
            and self._state.get("last_exit_attempt_status")
            in {"failed", "missing_config"}
            and last_attempt_at is not None
            and (now - last_attempt_at).total_seconds() < self.retry_sec
        ):
            return "exit_retry_wait"

        token, admin_id = self.config_loader()
        self._state["last_exit_episode_key"] = episode_key
        self._state["last_exit_attempt_at"] = now.isoformat()
        if not token or not admin_id:
            self._state["last_exit_attempt_status"] = "missing_config"
            self._save()
            self._append_delivery_audit(
                payload=payload,
                observed_at=now,
                event_type="EXIT",
                status="missing_config",
                episode_key=str(self._state.get("entry_episode_id") or episode_key),
            )
            return "exit_missing_config"
        try:
            self.sender(token, admin_id, build_exit_message(payload))
        except Exception as exc:
            self._state["last_exit_attempt_status"] = "failed"
            self._state["last_exit_error"] = type(exc).__name__
            self._save()
            self._append_delivery_audit(
                payload=payload,
                observed_at=now,
                event_type="EXIT",
                status="failed",
                episode_key=str(self._state.get("entry_episode_id") or episode_key),
            )
            return "exit_send_failed"

        self._state.update(
            {
                "last_exit_attempt_status": "sent",
                "last_exit_error": None,
                "last_exit_sent_at": now.isoformat(),
                "last_exit_reference_price": _positive_int(
                    exit_advisory.get("reference_exit_price")
                ),
                "last_exit_broken_support": _positive_int(
                    exit_advisory.get("broken_support")
                ),
                "last_exit_peak_price": _positive_int(exit_advisory.get("peak_price")),
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "telegram_audience": "ADMIN_ONLY",
                "last_telegram_event_type": "samsung_widget_exit_advisory",
            }
        )
        self._save()
        self._append_delivery_audit(
            payload=payload,
            observed_at=now,
            event_type="EXIT",
            status="sent",
            episode_key=str(self._state.get("entry_episode_id") or episode_key),
        )
        return "exit_sent"

    def observe(self, payload: dict[str, Any], observed_at: datetime) -> str:
        """Observe displayed advisories and send admin-only transition notices."""
        if not self.enabled:
            return "disabled"

        now = _as_kst(observed_at)
        advisory = payload.get("advisory") or {}
        state = str(advisory.get("state") or "")
        exit_state = str((payload.get("exit_advisory") or {}).get("state") or "")
        scope = self._scope(payload, now)
        self._ensure_daily_scope(scope)

        if exit_state == "EXIT_READY":
            if not self._exit_contract_valid(payload, now):
                return "invalid_exit_contract"
            if not self._state.get("active"):
                exit_episode_key = self._exit_episode_key(payload, scope)
                if (
                    self._state.get("last_exit_episode_key") == exit_episode_key
                    and self._state.get("last_exit_attempt_status") == "sent"
                ):
                    return "duplicate_exit_episode"
                return "exit_without_active_entry_episode"
            result = self._observe_exit_ready(payload, now=now, scope=scope)
            if result in {"exit_sent", "duplicate_exit_episode"}:
                exit_advisory = payload.get("exit_advisory") or {}
                self._close_entry_episode(
                    now=now,
                    reason="exit_ready",
                    reference_price=_positive_int(
                        exit_advisory.get("reference_exit_price")
                    ),
                    session=exit_advisory.get("session"),
                    peak_price=_positive_int(exit_advisory.get("peak_price")),
                )
            return result

        invalidation_reason = self._active_episode_invalidation_reason(payload)
        if invalidation_reason:
            self._close_entry_episode(
                now=now,
                reason=invalidation_reason,
                reference_price=_positive_int(payload.get("current_price")),
                session=advisory.get("session"),
            )
            return "entry_episode_invalidated"

        if state not in ACTIONABLE_ADVISORY_STATES:
            # WATCH/NO_CHASE/DATA_WAIT ends the short-lived entry opportunity,
            # not the advisory position episode opened by a sent entry notice.
            return "not_actionable"

        if not self._actionable_contract_valid(payload, now):
            return "invalid_actionable_contract"

        if self._state.get("active"):
            return "duplicate_active_episode"

        non_actionable_since = _parse_timestamp(self._state.get("non_actionable_since"))
        if (
            non_actionable_since is not None
            and (now - non_actionable_since).total_seconds() < self.rearm_sec
        ):
            return "rearm_wait"

        episode_id = f"{scope}:{now.isoformat()}"
        episode_state = {
            "active": True,
            "active_state": state,
            "entry_episode_status": "open",
            "entry_episode_id": episode_id,
            "entry_episode_opened_at": now.isoformat(),
            "entry_episode_opened_session": advisory.get("session"),
            "entry_episode_opened_bar": self._latest_completed_bar(payload).get(
                "source_time"
            ),
            "entry_episode_invalidation_price": _positive_int(
                advisory.get("invalidation_price")
            ),
            "entry_episode_closed_at": None,
            "entry_episode_close_reason": None,
            "entry_episode_close_reference_price": None,
            "entry_episode_closed_session": None,
            "entry_episode_peak_price": None,
            "non_actionable_since": None,
            "last_current_price": _positive_int(payload.get("current_price")),
            "last_entry_price_low": _positive_int(advisory.get("entry_price_low")),
            "last_entry_price_high": _positive_int(advisory.get("entry_price_high")),
            "last_invalidation_price": _positive_int(
                advisory.get("invalidation_price")
            ),
            "last_valid_until": advisory.get("valid_until"),
        }
        if not self.entry_messages_enabled:
            self._state.update(
                {
                    **episode_state,
                    "entry_episode_source": "collector_actionable_advisory",
                    "entry_telegram_suppressed": True,
                    "entry_telegram_owner": "widget_auto_trade_accepted_buy_action",
                }
            )
            self._save()
            self._append_delivery_audit(
                payload=payload,
                observed_at=now,
                event_type="ENTRY",
                status="suppressed_action_owner",
                episode_key=episode_id,
            )
            return "entry_observed_no_telegram"

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
            self._append_delivery_audit(
                payload=payload,
                observed_at=now,
                event_type="ENTRY",
                status="missing_config",
                episode_key=episode_id,
            )
            return "missing_config"

        self._state["last_attempt_at"] = now.isoformat()
        try:
            self.sender(token, admin_id, build_entry_message(payload))
        except Exception as exc:
            self._state["last_attempt_status"] = "failed"
            self._state["last_error"] = type(exc).__name__
            self._save()
            self._append_delivery_audit(
                payload=payload,
                observed_at=now,
                event_type="ENTRY",
                status="failed",
                episode_key=episode_id,
            )
            return "send_failed"

        self._state.update(
            {
                **episode_state,
                "last_sent_at": now.isoformat(),
                "last_sent_state": state,
                "last_attempt_status": "sent",
                "last_error": None,
                "authority": ADVISORY_AUTHORITY,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "telegram_audience": "ADMIN_ONLY",
                "telegram_event_type": "samsung_widget_entry_advisory",
                "last_telegram_event_type": "samsung_widget_entry_advisory",
            }
        )
        self._save()
        self._append_delivery_audit(
            payload=payload,
            observed_at=now,
            event_type="ENTRY",
            status="sent",
            episode_key=str(self._state.get("entry_episode_id") or ""),
        )
        return "sent"
