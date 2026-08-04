from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine.monitoring.samsung_widget_entry_notify import (
    SamsungWidgetEntryTelegramNotifier,
    build_entry_message,
)

KST = ZoneInfo("Asia/Seoul")


def _payload(state: str = "ENTRY_CAUTION", observed_at: datetime | None = None) -> dict:
    now = observed_at or datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    return {
        "status": "ok",
        "current_price": 233_250,
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "state": state,
            "session": "KRX_REGULAR",
            "entry_price_low": 233_000,
            "entry_price_high": 233_500,
            "invalidation_price": 232_000,
            "reasons": [
                "vwap_or_resistance_reclaimed",
                "three_five_minute_not_down",
            ],
            "unmet_conditions": ["regular_flow_unavailable"],
            "valid_until": (now + timedelta(seconds=60)).isoformat(),
            "observed_at": now.isoformat(),
            "external_risk": {"level": "DATA_LIMITED"},
            "source_quality": {"status": "PASS"},
            "authority": "widget_advisory_only",
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }


def test_entry_notice_is_admin_only_and_deduplicates_active_episode(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda token, admin_id, message: sent.append((token, admin_id, message)),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(), now) == "sent"
    assert notifier.observe(
        _payload(observed_at=now + timedelta(seconds=10)),
        now + timedelta(seconds=10),
    ) == ("duplicate_active_episode")
    assert len(sent) == 1
    assert sent[0][0:2] == ("TOKEN", "ADMIN")
    assert "233,000원 ~ 233,500원" in sent[0][2]
    assert "자동주문 아님" in sent[0][2]
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["telegram_audience"] == "ADMIN_ONLY"
    assert state["telegram_event_type"] == "samsung_widget_entry_advisory"
    assert state["runtime_effect"] is False
    assert state["actual_order_submitted"] is False
    assert state["last_entry_price_low"] == 233_000
    assert state["last_entry_price_high"] == 233_500


def test_caution_to_ready_upgrade_sends_one_additional_notice(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(), now) == "sent"
    assert notifier.observe(
        _payload("ENTRY_READY", now + timedelta(seconds=10)),
        now + timedelta(seconds=10),
    ) == ("sent")
    assert (
        notifier.observe(
            _payload("ENTRY_READY", now + timedelta(seconds=20)),
            now + timedelta(seconds=20),
        )
        == "duplicate_active_episode"
    )
    assert len(sent) == 2


def test_new_episode_requires_full_non_actionable_rearm_window(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    watch = _payload("WATCH")
    watch["advisory"]["entry_price_low"] = None
    watch["advisory"]["entry_price_high"] = None

    assert notifier.observe(_payload(), now) == "sent"
    assert notifier.observe(watch, now + timedelta(seconds=10)) == "not_actionable"
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=110)),
            now + timedelta(seconds=110),
        )
        == "rearm_wait"
    )
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=130)),
            now + timedelta(seconds=130),
        )
        == "sent"
    )
    assert len(sent) == 2


def test_restart_restores_active_episode_and_does_not_resend(tmp_path):
    sent = []
    state_file = tmp_path / "state.json"
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    first = SamsungWidgetEntryTelegramNotifier(
        state_file=state_file,
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    assert first.observe(_payload(), now) == "sent"

    restarted = SamsungWidgetEntryTelegramNotifier(
        state_file=state_file,
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    assert restarted.observe(
        _payload(observed_at=now + timedelta(seconds=10)),
        now + timedelta(seconds=10),
    ) == ("duplicate_active_episode")
    assert len(sent) == 1


def test_invalid_authority_and_missing_config_never_send(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("", ""),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    invalid = _payload()
    invalid["advisory"]["runtime_effect"] = True

    assert notifier.observe(invalid, now) == "invalid_actionable_contract"
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "missing_config"
    )
    assert sent == []


def test_expired_or_stale_actionable_advisory_never_sends(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    stale = _payload()
    stale["advisory"]["observed_at"] = (now - timedelta(seconds=26)).isoformat()
    expired = _payload()
    expired["advisory"]["valid_until"] = (now - timedelta(seconds=1)).isoformat()
    expires_now = _payload()
    expires_now["advisory"]["valid_until"] = now.isoformat()

    assert notifier.observe(stale, now) == "invalid_actionable_contract"
    assert notifier.observe(expired, now) == "invalid_actionable_contract"
    assert notifier.observe(expires_now, now) == "invalid_actionable_contract"
    assert sent == []


def test_missing_config_uses_retry_backoff(tmp_path):
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("", ""),
        sender=lambda *_args: None,
        retry_sec=30,
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(observed_at=now), now) == "missing_config"
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "retry_wait"
    )


def test_send_failure_is_isolated_and_retried_after_backoff(tmp_path):
    attempts = []

    def sender(*args):
        attempts.append(args)
        if len(attempts) == 1:
            raise TimeoutError("telegram unavailable")

    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=sender,
        retry_sec=30,
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(), now) == "send_failed"
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "retry_wait"
    )
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=31)),
            now + timedelta(seconds=31),
        )
        == "sent"
    )
    assert len(attempts) == 2


def test_message_contains_no_sell_or_order_instruction():
    message = build_entry_message(_payload())

    assert "매도" not in message
    assert "청산" not in message
    assert "주문" in message
    assert "자동주문 아님" in message


def test_exit_advisory_suppresses_conflicting_entry_notice(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    payload = _payload(observed_at=now)
    payload["exit_advisory"] = {"state": "EXIT_READY"}

    assert notifier.observe(payload, now) == "exit_advisory_conflict"
    assert sent == []
