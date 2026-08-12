from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine.monitoring.samsung_widget_entry_notify import (
    SamsungWidgetEntryTelegramNotifier,
    build_entry_message,
    build_exit_message,
)

KST = ZoneInfo("Asia/Seoul")


def _payload(state: str = "ENTRY_CAUTION", observed_at: datetime | None = None) -> dict:
    now = observed_at or datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    return {
        "status": "ok",
        "current_price": 233_250,
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "observation": {
            "latest_completed_bar": {
                "source_time": now.strftime("%Y%m%d%H%M00"),
                "close": 233_250,
            }
        },
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


def _exit_payload(observed_at: datetime | None = None) -> dict:
    now = observed_at or datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    payload = _payload("WATCH", now)
    payload["advisory"]["entry_price_low"] = None
    payload["advisory"]["entry_price_high"] = None
    payload["exit_advisory"] = {
        "state": "EXIT_READY",
        "session": "KRX_REGULAR",
        "reference_exit_price": 231_500,
        "broken_support": 232_000,
        "peak_price": 235_000,
        "peak_drawdown_pct": 1.4894,
        "reasons": [
            "rolling_peak_drawdown",
            "prior_five_bar_support_broken",
            "broken_support_reclaim_failed",
            "three_and_five_minute_down",
        ],
        "valid_until": (now + timedelta(seconds=60)).isoformat(),
        "observed_at": now.isoformat(),
        "source_quality": {"status": "PASS"},
        "continuity": {"ready_bar": "20260804143200"},
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "holding_independent": True,
        "future_prediction": False,
    }
    return payload


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


def test_caution_to_ready_upgrade_does_not_duplicate_open_episode(tmp_path):
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
    ) == ("duplicate_active_episode")
    assert (
        notifier.observe(
            _payload("ENTRY_READY", now + timedelta(seconds=20)),
            now + timedelta(seconds=20),
        )
        == "duplicate_active_episode"
    )
    assert len(sent) == 1


def test_watch_does_not_close_open_entry_episode(tmp_path):
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
        == "duplicate_active_episode"
    )
    assert (
        notifier.observe(
            _payload(observed_at=now + timedelta(seconds=130)),
            now + timedelta(seconds=130),
        )
        == "duplicate_active_episode"
    )
    assert len(sent) == 1


def test_open_premarket_episode_survives_krx_session_transition_until_exit(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    premarket = datetime(2026, 8, 7, 8, 29, 13, tzinfo=KST)
    first = _payload(observed_at=premarket)
    first["market_venue"] = "NXT"
    first["advisory"]["session"] = "NXT_PREMARKET"
    first["advisory"]["entry_price_low"] = 232_500
    first["advisory"]["entry_price_high"] = 233_000
    first["advisory"]["invalidation_price"] = 231_500

    assert notifier.observe(first, premarket) == "sent"

    watch = _payload("WATCH", premarket + timedelta(minutes=2))
    watch["market_venue"] = "NXT"
    watch["advisory"]["session"] = "NXT_PREMARKET"
    watch["advisory"]["entry_price_low"] = None
    watch["advisory"]["entry_price_high"] = None
    assert notifier.observe(watch, premarket + timedelta(minutes=2)) == "not_actionable"

    regular = datetime(2026, 8, 7, 9, 7, 33, tzinfo=KST)
    second = _payload(observed_at=regular)
    second["current_price"] = 238_000
    second["advisory"]["entry_price_low"] = 238_000
    second["advisory"]["entry_price_high"] = 238_500
    second["advisory"]["invalidation_price"] = 236_500
    assert notifier.observe(second, regular) == "duplicate_active_episode"

    exit_at = datetime(2026, 8, 7, 9, 18, 4, tzinfo=KST)
    exit_payload = _exit_payload(exit_at)
    assert notifier.observe(exit_payload, exit_at) == "exit_sent"
    assert len(sent) == 2
    assert "진입 알림" in sent[0][2]
    assert "청산 알림" in sent[1][2]

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["scope"] == "2026-08-07"
    assert state["entry_episode_status"] == "closed"
    assert state["entry_episode_close_reason"] == "exit_ready"
    assert state["entry_episode_close_reference_price"] == 231_500
    assert state["entry_episode_closed_session"] == "KRX_REGULAR"
    assert state["entry_episode_peak_price"] == 235_000


def test_displayed_invalidation_closes_episode_before_reentry(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
        rearm_sec=120,
    )
    now = datetime(2026, 8, 7, 10, 0, 0, tzinfo=KST)
    assert notifier.observe(_payload(observed_at=now), now) == "sent"

    broken = _payload("WATCH", now + timedelta(minutes=1))
    broken["advisory"]["entry_price_low"] = None
    broken["advisory"]["entry_price_high"] = None
    broken["observation"]["latest_completed_bar"]["close"] = 232_000
    assert (
        notifier.observe(broken, now + timedelta(minutes=1))
        == "entry_episode_invalidated"
    )

    early = _payload(observed_at=now + timedelta(minutes=2))
    assert notifier.observe(early, now + timedelta(minutes=2)) == "rearm_wait"
    later = _payload(observed_at=now + timedelta(minutes=3, seconds=1))
    assert notifier.observe(later, now + timedelta(minutes=3, seconds=1)) == "sent"
    assert len(sent) == 2


def test_source_blocked_payload_cannot_close_open_entry_episode(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 7, 10, 0, 0, tzinfo=KST)
    assert notifier.observe(_payload(observed_at=now), now) == "sent"

    blocked = _payload("WATCH", now + timedelta(minutes=1))
    blocked["advisory"]["entry_price_low"] = None
    blocked["advisory"]["entry_price_high"] = None
    blocked["advisory"]["source_quality"] = {
        "status": "BLOCKED",
        "issues": ["bbo_stale"],
    }
    blocked["observation"]["latest_completed_bar"]["close"] = 231_500
    assert notifier.observe(blocked, now + timedelta(minutes=1)) == "not_actionable"

    fresh = _payload(observed_at=now + timedelta(minutes=2))
    assert (
        notifier.observe(fresh, now + timedelta(minutes=2))
        == "duplicate_active_episode"
    )
    assert len(sent) == 1


def test_live_invalidation_requires_confirmed_ask_pressure(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 7, 10, 0, 20, tzinfo=KST)
    assert notifier.observe(_payload(observed_at=now), now) == "sent"

    live_break = _payload("WATCH", now + timedelta(seconds=10))
    live_break["current_price"] = 231_500
    live_break["advisory"]["entry_price_low"] = None
    live_break["advisory"]["entry_price_high"] = None
    live_break["advisory"]["derived"] = {"live_reversal": {"ask_pressure": False}}
    assert notifier.observe(live_break, now + timedelta(seconds=10)) == "not_actionable"

    live_break["observed_at_kst"] = (now + timedelta(seconds=20)).isoformat()
    live_break["advisory"]["observed_at"] = live_break["observed_at_kst"]
    live_break["advisory"]["valid_until"] = (now + timedelta(seconds=80)).isoformat()
    live_break["advisory"]["derived"]["live_reversal"]["ask_pressure"] = True
    assert (
        notifier.observe(live_break, now + timedelta(seconds=20))
        == "entry_episode_invalidated"
    )
    assert len(sent) == 1


def test_pre_entry_completed_bar_cannot_invalidate_new_episode(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 7, 10, 0, 20, tzinfo=KST)
    entry = _payload(observed_at=now)
    entry["observation"]["latest_completed_bar"]["close"] = 233_000
    assert notifier.observe(entry, now) == "sent"

    same_bar = _payload("WATCH", now + timedelta(seconds=10))
    same_bar["advisory"]["entry_price_low"] = None
    same_bar["advisory"]["entry_price_high"] = None
    same_bar["observation"]["latest_completed_bar"]["close"] = 231_500
    assert notifier.observe(same_bar, now + timedelta(seconds=10)) == "not_actionable"
    assert len(sent) == 1


def test_legacy_session_state_restores_entry_bar_before_invalidation(tmp_path):
    sent = []
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "2026-08-07:NXT_PREMARKET",
                "active": True,
                "active_state": "ENTRY_CAUTION",
                "last_sent_at": "2026-08-07T08:29:13+09:00",
                "last_invalidation_price": 231_500,
            }
        ),
        encoding="utf-8",
    )
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=state_file,
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )

    now = datetime(2026, 8, 7, 8, 29, 30, tzinfo=KST)
    same_bar = _payload("WATCH", now)
    same_bar["market_venue"] = "NXT"
    same_bar["advisory"]["session"] = "NXT_PREMARKET"
    same_bar["advisory"]["entry_price_low"] = None
    same_bar["advisory"]["entry_price_high"] = None
    same_bar["observation"]["latest_completed_bar"].update(
        {"source_time": "20260807082900", "close": 231_000}
    )
    assert notifier.observe(same_bar, now) == "not_actionable"
    migrated = json.loads(state_file.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == 2
    assert migrated["scope"] == "2026-08-07"
    assert migrated["entry_episode_opened_bar"] == "20260807082900"

    next_bar = _payload("WATCH", now + timedelta(minutes=1))
    next_bar["market_venue"] = "NXT"
    next_bar["advisory"]["session"] = "NXT_PREMARKET"
    next_bar["advisory"]["entry_price_low"] = None
    next_bar["advisory"]["entry_price_high"] = None
    next_bar["observation"]["latest_completed_bar"].update(
        {"source_time": "20260807083000", "close": 231_000}
    )
    assert (
        notifier.observe(next_bar, now + timedelta(minutes=1))
        == "entry_episode_invalidated"
    )
    assert sent == []


def test_legacy_closed_episode_uses_exit_time_for_rearm(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "2026-08-07:KRX_REGULAR",
                "active": False,
                "last_sent_at": "2026-08-07T09:07:33+09:00",
                "last_exit_sent_at": "2026-08-07T09:18:04+09:00",
                "last_exit_reference_price": 235_000,
                "non_actionable_since": "2026-08-07T09:08:04+09:00",
            }
        ),
        encoding="utf-8",
    )
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=state_file,
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: None,
        rearm_sec=120,
    )

    early = datetime(2026, 8, 7, 9, 19, 0, tzinfo=KST)
    assert notifier.observe(_payload(observed_at=early), early) == "rearm_wait"
    migrated = json.loads(state_file.read_text(encoding="utf-8"))
    assert migrated["non_actionable_since"] == "2026-08-07T09:18:04+09:00"
    assert migrated["entry_episode_closed_at"] == "2026-08-07T09:18:04+09:00"
    assert migrated["entry_episode_close_reason"] == "legacy_exit_notification"
    assert migrated["entry_episode_close_reference_price"] == 235_000


def test_holding_independent_exit_does_not_notify_without_entry_episode(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
        rearm_sec=120,
    )
    now = datetime(2026, 8, 7, 10, 0, 0, tzinfo=KST)
    assert (
        notifier.observe(_exit_payload(now), now) == "exit_without_active_entry_episode"
    )

    entry = _payload(observed_at=now + timedelta(seconds=60))
    assert notifier.observe(entry, now + timedelta(seconds=60)) == "sent"
    assert len(sent) == 1
    assert "진입 알림" in sent[0][2]


def test_missing_invalidation_price_is_not_an_actionable_contract(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 7, 10, 0, 0, tzinfo=KST)
    payload = _payload(observed_at=now)
    payload["advisory"]["invalidation_price"] = None

    assert notifier.observe(payload, now) == "invalid_actionable_contract"
    assert sent == []


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


def test_entry_message_formats_bid_only_scope_as_single_price():
    payload = _payload()
    payload["advisory"]["entry_price_high"] = payload["advisory"]["entry_price_low"]
    payload["advisory"]["unmet_conditions"] = [
        "nxt_aftermarket_reclaim_structure_unconfirmed"
    ]

    message = build_entry_message(payload)

    assert "권장가격: 233,000원" in message
    assert "권장가격: 233,000원 ~ 233,000원" not in message
    assert "주의: 애프터마켓 저항·상승구조 미확인" in message


def test_exit_ready_sends_one_notice_and_suppresses_conflicting_entry(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    assert notifier.observe(_payload(observed_at=now), now) == "sent"
    payload = _exit_payload(now)
    payload["advisory"] = _payload("ENTRY_READY", now)["advisory"]

    assert notifier.observe(payload, now) == "exit_sent"
    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=10)), now + timedelta(seconds=10)
        )
        == "duplicate_exit_episode"
    )
    assert len(sent) == 2
    assert "삼성전자 청산 알림" in sent[1][2]
    assert "231,500원" in sent[1][2]
    assert "수집기 진입 에피소드 연계 관측용" in sent[1][2]
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["last_telegram_event_type"] == "samsung_widget_exit_advisory"
    assert state["last_exit_reference_price"] == 231_500


def test_exit_ready_retries_failure_without_cross_suppressing_entry_state(tmp_path):
    attempts = []

    def sender(*args):
        attempts.append(args)
        if len(attempts) == 2:
            raise TimeoutError("telegram unavailable")

    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=sender,
        retry_sec=30,
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(observed_at=now), now) == "sent"
    assert notifier.observe(_exit_payload(now), now) == "exit_send_failed"
    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=10)), now + timedelta(seconds=10)
        )
        == "exit_retry_wait"
    )
    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=31)), now + timedelta(seconds=31)
        )
        == "exit_sent"
    )
    assert len(attempts) == 3


def test_new_lower_support_exit_does_not_renotify_before_new_entry(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
        rearm_sec=0,
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(observed_at=now), now) == "sent"
    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "exit_sent"
    )

    lower = _exit_payload(now + timedelta(minutes=5))
    lower["exit_advisory"]["continuity"]["ready_bar"] = "20260804143800"
    lower["exit_advisory"]["broken_support"] = 231_000
    lower["exit_advisory"]["reference_exit_price"] = 230_500
    assert (
        notifier.observe(lower, now + timedelta(minutes=5))
        == "exit_without_active_entry_episode"
    )
    assert len(sent) == 2


def test_successful_notifications_write_append_only_delivery_audit(tmp_path):
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        audit_directory=tmp_path / "audit",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: None,
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(observed_at=now), now) == "sent"
    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "exit_sent"
    )

    audit = tmp_path / "audit" / "samsung_widget_telegram_notify_20260804.jsonl"
    rows = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    assert [row["event_type"] for row in rows] == ["ENTRY", "EXIT"]
    assert all(row["status"] == "sent" for row in rows)
    assert all(row["runtime_effect"] is False for row in rows)
    assert all(row["actual_order_submitted"] is False for row in rows)


def test_invalid_or_stale_exit_advisory_never_sends(tmp_path):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)
    invalid = _exit_payload(now)
    invalid["exit_advisory"]["runtime_effect"] = True
    stale = _exit_payload(now)
    stale["observed_at_kst"] = (now - timedelta(seconds=26)).isoformat()
    stale["exit_advisory"]["observed_at"] = stale["observed_at_kst"]
    expired = _exit_payload(now)
    expired["exit_advisory"]["valid_until"] = now.isoformat()

    assert notifier.observe(invalid, now) == "invalid_exit_contract"
    assert notifier.observe(stale, now) == "invalid_exit_contract"
    assert notifier.observe(expired, now) == "invalid_exit_contract"
    assert sent == []


def test_exit_message_is_entry_linked_and_has_no_order_authority():
    message = build_exit_message(_exit_payload())

    assert "수집기 진입 에피소드 연계 관측용" in message
    assert "자동매도/주문 아님" in message
    assert "이탈 지지: 232,000원" in message


def test_collector_entry_message_can_be_suppressed_while_exit_remains_enabled(
    tmp_path,
):
    sent = []
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
        entry_messages_enabled=False,
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert notifier.observe(_payload(observed_at=now), now) == (
        "entry_observed_no_telegram"
    )
    assert sent == []
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["active"] is True
    assert state["entry_telegram_suppressed"] is True
    assert state["entry_telegram_owner"] == "widget_auto_trade_accepted_buy_action"

    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "exit_sent"
    )
    assert len(sent) == 1
    assert "삼성전자 청산 알림" in sent[0][2]


def test_entry_specific_env_does_not_disable_collector_exit_delivery(
    tmp_path, monkeypatch
):
    sent = []
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ENTRY_TELEGRAM_ENABLED", "false")
    monkeypatch.setenv("KORSTOCKSCAN_SAMSUNG_WIDGET_TELEGRAM_ENABLED", "true")
    notifier = SamsungWidgetEntryTelegramNotifier(
        state_file=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
    )
    now = datetime(2026, 8, 4, 14, 33, 20, tzinfo=KST)

    assert (
        notifier.observe(_payload(observed_at=now), now) == "entry_observed_no_telegram"
    )
    assert (
        notifier.observe(
            _exit_payload(now + timedelta(seconds=10)),
            now + timedelta(seconds=10),
        )
        == "exit_sent"
    )
    assert len(sent) == 1


def test_local_peak_exit_message_does_not_claim_support_was_broken():
    payload = _exit_payload()
    payload["exit_advisory"]["continuity"]["caution_kind"] = "local_peak_rollover"
    payload["exit_advisory"]["reasons"] = [
        "rolling_peak_drawdown",
        "completed_bar_lower_high",
        "local_peak_rollover_continued",
        "three_minute_down_confirmed",
    ]

    message = build_exit_message(payload)

    assert "고점 이탈·하락 지속 확인" in message
    assert "확인 지지: 232,000원" in message
    assert "이탈 지지: 232,000원" not in message
    assert "국지 고점 이탈 지속" in message
