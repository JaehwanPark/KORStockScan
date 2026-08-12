from __future__ import annotations

from datetime import datetime, timedelta

from src.engine.monitoring.doosan_widget_telegram_notify import (
    DoosanWidgetTelegramNotifier,
)
from src.engine.monitoring.samsung_widget_contract import KST


def _event_payload(now: datetime) -> dict:
    common = {
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_quality_status": "PASS",
        "strategy_profile": "DOOSAN_FIRST_PULLBACK_V1",
        "observed_at": now.isoformat(),
        "valid_until": (now + timedelta(seconds=60)).isoformat(),
    }
    return {
        "status": "ok",
        "symbol": "034020",
        "current_price": 68_200,
        "entry_event": {
            **common,
            "event_id": "034020:2026-08-05:ENTRY:100005",
            "event_type": "ENTRY",
            "status": "ACTIVE",
            "state": "ENTRY_READY",
            "signal_tier": "HIGH",
            "entry_price_low": 68_100,
            "entry_price_high": 68_200,
            "entry_reference_price": 68_200,
            "structural_support": 67_800,
            "target_price": 68_900,
            "session_return_pct": -1.2,
            "relative_signal": "NOT_WEAK",
            "flow_signal": "NONWORSENING",
            "external_risk_level": "CLEAR",
        },
        "exit_event": None,
    }


def test_admin_notifier_sends_entry_and_exit_once(tmp_path):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    sent = []
    notifier = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *args: sent.append(args),
    )
    payload = _event_payload(now)

    assert notifier.observe(payload, now) == {"entry": "sent", "exit": "no_event"}
    assert (
        notifier.observe(payload, now + timedelta(seconds=10))["entry"] == "duplicate"
    )
    assert sent[0][:2] == ("TOKEN", "ADMIN")
    assert "진입 신호" in sent[0][2]
    assert "청산 후 새 구조 재진입 가능" in sent[0][2]
    assert "상대 NOT_WEAK · 수급 NONWORSENING · 외부 CLEAR" in sent[0][2]
    assert "자동주문 아님" in sent[0][2]

    payload["exit_event"] = {
        **payload["entry_event"],
        "event_id": "034020:2026-08-05:EXIT:101005",
        "event_type": "EXIT",
        "reason": "doosan_target_1pct_reached",
        "reference_exit_price": 68_900,
        "entry_reference_price": 68_200,
        "observed_at": (now + timedelta(seconds=20)).isoformat(),
        "valid_until": (now + timedelta(seconds=80)).isoformat(),
    }
    result = notifier.observe(payload, now + timedelta(seconds=20))

    assert result == {"entry": "exit_event_conflict", "exit": "sent"}
    assert len(sent) == 2
    assert "청산 신호" in sent[1][2]
    assert "+1% 기준가 도달" in sent[1][2]


def test_admin_notifier_sends_each_distinct_same_day_entry_episode(tmp_path):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    sent = []
    notifier = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *args: sent.append(args),
    )
    payload = _event_payload(now)
    assert notifier.observe(payload, now)["entry"] == "sent"

    second_at = now + timedelta(minutes=5)
    payload["entry_event"] = {
        **payload["entry_event"],
        "event_id": "034020:2026-08-05:ENTRY:02:100505",
        "episode_sequence": 2,
        "observed_at": second_at.isoformat(),
        "valid_until": (second_at + timedelta(seconds=60)).isoformat(),
    }

    assert notifier.observe(payload, second_at)["entry"] == "sent"
    assert len(sent) == 2


def test_notifier_rejects_runtime_authority_and_retries_failure(tmp_path):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    payload = _event_payload(now)
    payload["entry_event"]["runtime_effect"] = True
    notifier = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: None,
    )
    assert notifier.observe(payload, now)["entry"] == "invalid_event"

    attempts = []
    payload = _event_payload(now)

    def sender(*args):
        attempts.append(args)
        if len(attempts) == 1:
            raise TimeoutError

    retrying = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "retry.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=sender,
        retry_sec=30,
    )
    assert retrying.observe(payload, now)["entry"] == "send_failed"
    assert (
        retrying.observe(payload, now + timedelta(seconds=10))["entry"] == "retry_wait"
    )
    assert retrying.observe(payload, now + timedelta(seconds=31))["entry"] == "sent"


def test_notifier_does_not_send_closed_entry_after_exit(tmp_path):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    sent = []
    payload = _event_payload(now)
    payload["entry_event"]["status"] = "CLOSED"
    notifier = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *args: sent.append(args),
    )

    assert notifier.observe(payload, now)["entry"] == "invalid_event"
    assert sent == []


def test_valid_exit_event_suppresses_unsent_entry_event(tmp_path):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    payload = _event_payload(now)
    payload["exit_event"] = {
        **payload["entry_event"],
        "event_id": "034020:2026-08-05:EXIT:100005",
        "event_type": "EXIT",
        "reason": "doosan_target_1pct_reached",
        "reference_exit_price": 68_900,
    }
    sent = []
    notifier = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *args: sent.append(args),
    )

    result = notifier.observe(payload, now)

    assert result == {"entry": "exit_event_conflict", "exit": "sent"}
    assert len(sent) == 1
    assert "청산 신호" in sent[0][2]


def test_collector_entry_is_suppressed_but_exit_remains_enabled(tmp_path):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    sent = []
    notifier = DoosanWidgetTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *args: sent.append(args),
        entry_messages_enabled=False,
    )
    payload = _event_payload(now)

    assert notifier.observe(payload, now) == {
        "entry": "entry_observed_no_telegram",
        "exit": "no_event",
    }
    first_state_mtime = (tmp_path / "state.json").stat().st_mtime_ns
    assert notifier.observe(payload, now + timedelta(seconds=1)) == {
        "entry": "entry_observed_no_telegram",
        "exit": "no_event",
    }
    assert (tmp_path / "state.json").stat().st_mtime_ns == first_state_mtime
    assert sent == []

    payload["exit_event"] = {
        **payload["entry_event"],
        "event_id": "034020:2026-08-05:EXIT:100025",
        "event_type": "EXIT",
        "reason": "doosan_target_1pct_reached",
        "reference_exit_price": 68_900,
    }
    result = notifier.observe(payload, now + timedelta(seconds=20))

    assert result == {"entry": "exit_event_conflict", "exit": "sent"}
    assert len(sent) == 1
    assert "청산 신호" in sent[0][2]
