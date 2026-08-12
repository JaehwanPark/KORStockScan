from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.trading.widget_auto_trade.notifications import (
    WidgetAutoTradeEntryTelegramNotifier,
    build_buy_action_message,
)

KST = ZoneInfo("Asia/Seoul")


def _accepted_order(**overrides):
    order = {
        "side": "BUY",
        "broker_accepted": True,
        "order_role": "ENTRY_BUY",
        "order_no": "B123",
        "order_date": "2026-08-12",
        "requested_qty": 1,
        "market_venue": "KRX",
        "broker_route": "SOR",
        "signal_id": "005930:2026-08-12:ENTRY:KRX_REGULAR:signal",
        "source_advisory_state": "ENTRY_CAUTION",
        "submitted_at": "2026-08-12T10:03:04+09:00",
        "limit_price": None,
        "scale_in_leg_index": None,
    }
    order.update(overrides)
    return order


def test_accepted_buy_action_sends_once_and_does_not_claim_fill(tmp_path):
    sent = []
    notifier = WidgetAutoTradeEntryTelegramNotifier(
        state_path=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda token, admin, message: sent.append((token, admin, message)),
        enabled=True,
    )
    now = datetime(2026, 8, 12, 10, 3, 4, tzinfo=KST)
    order = _accepted_order()

    assert (
        notifier.notify_order_accepted(
            symbol="005930",
            name="삼성전자",
            order=order,
            execution_policy_id="POLICY_V1",
            observed_at=now,
        )
        == "sent"
    )
    restarted = WidgetAutoTradeEntryTelegramNotifier(
        state_path=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda token, admin, message: sent.append((token, admin, message)),
        enabled=True,
    )
    assert (
        restarted.notify_order_accepted(
            symbol="005930",
            name="삼성전자",
            order=order,
            execution_policy_id="POLICY_V1",
            observed_at=now + timedelta(seconds=1),
        )
        == "duplicate"
    )
    assert len(sent) == 1
    message = sent[0][2]
    assert "자동매매 매수 주문 접수" in message
    assert "시장/라우팅: KRX / SOR" in message
    assert "체결 여부는 broker reconciliation 기준" in message
    assert "매수 체결" not in message
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    delivery = next(iter(state["deliveries"].values()))
    assert delivery["actual_order_submitted"] is True
    assert delivery["telegram_audience"] == "ADMIN_ONLY"


def test_default_action_owner_sends_for_all_enabled_widget_symbols(tmp_path):
    sent = []
    notifier = WidgetAutoTradeEntryTelegramNotifier(
        state_path=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda token, admin, message: sent.append((token, admin, message)),
        enabled=True,
    )
    now = datetime(2026, 8, 12, 10, 3, 4, tzinfo=KST)

    for symbol, name in (
        ("005930", "삼성전자"),
        ("034020", "두산에너빌리티"),
        ("042660", "한화오션"),
    ):
        assert (
            notifier.notify_order_accepted(
                symbol=symbol,
                name=name,
                order=_accepted_order(signal_id=f"{symbol}:ENTRY"),
                execution_policy_id="POLICY_V1",
                observed_at=now,
            )
            == "sent"
        )

    assert len(sent) == 3
    assert all("자동매매 매수 주문 접수" in row[2] for row in sent)


def test_rejected_ambiguous_sell_and_unsupported_symbol_never_send(tmp_path):
    sent = []
    notifier = WidgetAutoTradeEntryTelegramNotifier(
        state_path=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
        enabled=True,
    )
    now = datetime(2026, 8, 12, 10, 3, 4, tzinfo=KST)

    for order in (
        _accepted_order(broker_accepted=False),
        _accepted_order(order_no=""),
        _accepted_order(side="SELL"),
        _accepted_order(order_role="TAKE_PROFIT_SELL"),
    ):
        assert (
            notifier.notify_order_accepted(
                symbol="005930",
                name="삼성전자",
                order=order,
                execution_policy_id="POLICY_V1",
                observed_at=now,
            )
            == "not_accepted_buy_action"
        )
    assert (
        notifier.notify_order_accepted(
            symbol="999999",
            name="테스트",
            order=_accepted_order(),
            execution_policy_id=None,
            observed_at=now,
        )
        == "symbol_not_enabled"
    )
    assert sent == []


def test_stale_accepted_order_is_not_backfilled_after_service_restart(tmp_path):
    sent = []
    notifier = WidgetAutoTradeEntryTelegramNotifier(
        state_path=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=lambda *_args: sent.append(_args),
        action_max_age_sec=300,
        enabled=True,
    )
    now = datetime(2026, 8, 12, 10, 10, 0, tzinfo=KST)

    assert (
        notifier.notify_order_accepted(
            symbol="005930",
            name="삼성전자",
            order=_accepted_order(submitted_at="2026-08-12T10:03:04+09:00"),
            execution_policy_id="POLICY_V1",
            observed_at=now,
        )
        == "stale_action_not_notified"
    )
    assert sent == []


def test_failed_delivery_retries_after_bounded_wait(tmp_path):
    attempts = []

    def sender(*args):
        attempts.append(args)
        if len(attempts) == 1:
            raise OSError("temporary")

    notifier = WidgetAutoTradeEntryTelegramNotifier(
        state_path=tmp_path / "state.json",
        config_loader=lambda: ("TOKEN", "ADMIN"),
        sender=sender,
        retry_sec=30,
        enabled=True,
    )
    now = datetime(2026, 8, 12, 10, 3, 4, tzinfo=KST)
    kwargs = {
        "symbol": "005930",
        "name": "삼성전자",
        "order": _accepted_order(),
        "execution_policy_id": "POLICY_V1",
    }

    assert notifier.notify_order_accepted(**kwargs, observed_at=now) == "send_failed"
    assert (
        notifier.notify_order_accepted(
            **kwargs, observed_at=now + timedelta(seconds=10)
        )
        == "retry_wait"
    )
    assert (
        notifier.notify_order_accepted(
            **kwargs, observed_at=now + timedelta(seconds=31)
        )
        == "sent"
    )
    assert len(attempts) == 2


def test_scale_in_message_identifies_leg_without_changing_authority():
    message = build_buy_action_message(
        symbol="005930",
        name="삼성전자",
        order=_accepted_order(order_role="SCALE_IN_BUY", scale_in_leg_index=2),
        execution_policy_id="POLICY_V1",
        observed_at=datetime(2026, 8, 12, 10, 3, 4, tzinfo=KST),
    )

    assert "구분: 추가매수 2차" in message
    assert "실행정책: POLICY_V1" in message
