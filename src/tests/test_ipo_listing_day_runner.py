from __future__ import annotations

from datetime import datetime

import pytest

import src.engine.ipo_listing_day_runner as ipo


class FakeWs:
    def __init__(self, data=None):
        self.data = data or {}
        self.subscribed = []

    def execute_subscribe(self, codes):
        self.subscribed.extend(codes)

    def get_latest_data(self, code):
        return self.data.get(code, {})


class FakeAi:
    def __init__(self, entry=None, exit=None):
        self.entry = entry or {}
        self.exit = exit or {}

    def review_entry(self, target, ws_data):
        return dict(self.entry)

    def review_exit(self, target, ws_data, position):
        return dict(self.exit)


@pytest.fixture()
def target():
    return ipo.IpoTarget(
        code="123456",
        name="IPO",
        listing_date="2026-05-11",
        offer_price=10_000,
        budget_cap_krw=300_000,
    )


@pytest.fixture()
def config(target):
    return ipo.IpoRunConfig(
        trade_date="2026-05-11",
        global_daily_loss_cap_krw=100_000,
        max_order_failures=2,
        active_symbol_limit=1,
        targets=(target,),
    )


def ws_snapshot(
    price=20_000, ask=20_000, bid=19_950, ask_volume=100, bid_volume=100, ts=1_000.0
):
    return {
        "curr": price,
        "last_ws_update_ts": ts,
        "orderbook": {
            "asks": [
                {"price": ask, "volume": ask_volume},
                {"price": ask + 50, "volume": ask_volume},
                {"price": ask + 100, "volume": ask_volume},
            ],
            "bids": [
                {"price": bid, "volume": bid_volume},
                {"price": bid - 50, "volume": bid_volume},
            ],
        },
    }


def test_load_ipo_config_yaml_and_select_targets(tmp_path):
    path = tmp_path / "ipo.yaml"
    path.write_text(
        """
trade_date: "2026-05-11"
global_daily_loss_cap_krw: 100000
max_order_failures: 2
active_symbol_limit: 1
targets:
  - code: "A123456"
    name: "IPO"
    listing_date: "2026-05-11"
    offer_price: 10000
    budget_cap_krw: 300000
  - code: "654321"
    name: "DISABLED"
    listing_date: "2026-05-11"
    offer_price: 10000
    budget_cap_krw: 300000
    enabled: false
""",
        encoding="utf-8",
    )

    config = ipo.load_ipo_config(path)

    selected = ipo.select_enabled_targets(config, today="2026-05-11")
    assert len(selected) == 1
    assert selected[0].code == "123456"
    assert selected[0].premium_guard_pct == 250.0


def test_budget_to_qty_rounds_down_but_keeps_one_when_budget_allows():
    assert ipo.calculate_entry_qty(300_000, 20_000) == 15
    assert ipo.calculate_entry_qty(10_000, 30_000) == 1
    assert ipo.calculate_entry_qty(0, 30_000) == 0


def test_indicative_open_snapshot_prefers_0d_expected_open_fields():
    snapshot = ipo.indicative_open_snapshot(
        {
            "curr": 20_000,
            "expected_open": {
                "price": 19_850,
                "qty": 12_300,
                "source": "0D_expected_open",
                "price_vs_prev_rate": 4.2,
                "valid_during_expected_session": True,
            },
        }
    )

    assert snapshot["indicative_open_price"] == 19_850
    assert snapshot["indicative_open_source"] == "0D_expected_open"
    assert snapshot["explicit_expected_open_available"] is True
    assert snapshot["expected_open_qty"] == 12_300
    assert snapshot["expected_open_meta"]["price_vs_prev_rate"] == 4.2


def test_indicative_open_snapshot_falls_back_to_ws_curr_without_expected_fields():
    snapshot = ipo.indicative_open_snapshot({"curr": 20_000})

    assert snapshot["indicative_open_price"] == 20_000
    assert snapshot["indicative_open_source"] == "ws_curr"
    assert snapshot["explicit_expected_open_available"] is False


def test_entry_gate_clamps_budget_to_five_million_cap(target):
    high_budget = ipo.IpoTarget(
        code=target.code,
        name=target.name,
        listing_date=target.listing_date,
        offer_price=target.offer_price,
        budget_cap_krw=10_000_000,
    )

    decision = ipo.evaluate_entry_gate(
        high_budget,
        ws_snapshot(ask_volume=500),
        now_ts=1_000.5,
        ai_result={"risk_score": 0},
    )

    assert decision.allowed
    assert decision.fields["budget_cap_krw"] == 10_000_000
    assert decision.fields["effective_budget_cap_krw"] == 5_000_000
    assert decision.fields["qty"] == 250


def test_entry_gate_blocks_premium_above_guard(target):
    decision = ipo.evaluate_entry_gate(
        target, ws_snapshot(price=26_000, ask=26_000), now_ts=1_000.5
    )

    assert not decision.allowed
    assert decision.reason == "premium_guard"
    assert decision.fields["premium_pct"] == 260.0


def test_entry_gate_blocks_depth_below_three_times_budget(target):
    shallow = ws_snapshot(price=20_000, ask=20_000, ask_volume=2)

    decision = ipo.evaluate_entry_gate(target, shallow, now_ts=1_000.5)

    assert not decision.allowed
    assert decision.reason == "depth_gate"


def test_entry_gate_blocks_ai_risk_score(target):
    decision = ipo.evaluate_entry_gate(
        target, ws_snapshot(), now_ts=1_000.5, ai_result={"risk_score": 80}
    )

    assert not decision.allowed
    assert decision.reason == "ai_risk_block"


def test_entry_gate_allows_fresh_liquid_non_overheated_quote(target):
    decision = ipo.evaluate_entry_gate(
        target, ws_snapshot(), now_ts=1_000.5, ai_result={"risk_score": 79}
    )

    assert decision.allowed
    assert decision.reason == "entry_allowed"
    assert decision.fields["qty"] == 15


def test_exit_hard_stop_precedes_ai_and_profit_logic(target):
    position = ipo.IpoPosition(
        code=target.code,
        name=target.name,
        qty=10,
        avg_price=10_000,
        entry_time=datetime(2026, 5, 11, 9, 0, 0),
    )

    decision = ipo.evaluate_exit_action(
        position,
        {"curr": 8_900},
        now_dt=datetime(2026, 5, 11, 9, 0, 10),
        ai_result={"hold_confidence": 100, "continuation_reasons": ["flow", "book"]},
    )

    assert decision.allowed
    assert decision.reason == "hard_stop"
    assert decision.fields["sell_qty"] == 10


def test_twenty_percent_partial_tp_can_be_deferred_by_strong_ai(target):
    position = ipo.IpoPosition(
        code=target.code,
        name=target.name,
        qty=10,
        avg_price=10_000,
        entry_time=datetime(2026, 5, 11, 9, 0, 0),
    )

    decision = ipo.evaluate_exit_action(
        position,
        {"curr": 12_100},
        now_dt=datetime(2026, 5, 11, 9, 5, 0),
        ai_result={
            "hold_confidence": 75,
            "continuation_reasons": ["order_flow", "orderbook"],
        },
    )

    assert not decision.allowed
    assert decision.reason == "ai_defer_partial_tp"


def test_twenty_percent_partial_tp_sells_thirty_percent_without_strong_ai(target):
    position = ipo.IpoPosition(
        code=target.code,
        name=target.name,
        qty=10,
        avg_price=10_000,
        entry_time=datetime(2026, 5, 11, 9, 0, 0),
    )

    decision = ipo.evaluate_exit_action(
        position,
        {"curr": 12_100},
        now_dt=datetime(2026, 5, 11, 9, 5, 0),
        ai_result={
            "hold_confidence": 74,
            "continuation_reasons": ["order_flow", "orderbook"],
        },
    )

    assert decision.allowed
    assert decision.reason == "partial_take_profit_20pct"
    assert decision.fields["sell_qty"] == 3


def test_after_partial_trailing_sells_remainder(target):
    position = ipo.IpoPosition(
        code=target.code,
        name=target.name,
        qty=7,
        avg_price=10_000,
        entry_time=datetime(2026, 5, 11, 9, 0, 0),
        first_partial_taken=True,
        peak_profit_pct=35.0,
    )

    decision = ipo.evaluate_exit_action(
        position,
        {"curr": 12_600},
        now_dt=datetime(2026, 5, 11, 9, 10, 0),
    )

    assert decision.allowed
    assert decision.reason == "post_tp_trailing"
    assert decision.fields["sell_qty"] == 7


def test_max_hold_time_forces_exit(target):
    position = ipo.IpoPosition(
        code=target.code,
        name=target.name,
        qty=5,
        avg_price=10_000,
        entry_time=datetime(2026, 5, 11, 9, 0, 0),
    )

    decision = ipo.evaluate_exit_action(
        position,
        {"curr": 10_100},
        now_dt=datetime(2026, 5, 11, 9, 30, 0),
    )

    assert decision.allowed
    assert decision.reason == "max_hold_time"


def test_engine_never_orders_outside_entry_window(
    monkeypatch, config, target, tmp_path
):
    monkeypatch.setattr(ipo, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        ipo.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail(
            "real entry order must not be called outside entry window"
        ),
    )
    writer = ipo.IpoArtifactWriter(tmp_path, trade_date=config.trade_date)
    engine = ipo.IpoListingDayEngine(
        config,
        token="token",
        ws_manager=FakeWs(),
        ai_advisor=FakeAi(entry={"risk_score": 0}),
        artifact_writer=writer,
        stop_file=tmp_path / "STOP",
    )

    decision = engine.maybe_enter(
        target, ws_snapshot(), now_dt=datetime(2026, 5, 11, 8, 59, 59)
    )

    assert not decision.allowed
    assert decision.reason == "outside_entry_window"


def test_engine_allows_one_retry_and_blocks_reentry(
    monkeypatch, config, target, tmp_path
):
    monkeypatch.setattr(ipo, "is_buy_side_paused", lambda: False)
    calls = []

    def fake_buy(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 1:
            return {"return_code": "99", "return_msg": "first fail"}
        return {"return_code": "0", "ord_no": "ORDER-2"}

    monkeypatch.setattr(ipo.kiwoom_orders, "send_buy_order", fake_buy)
    engine = ipo.IpoListingDayEngine(
        config,
        token="token",
        ws_manager=FakeWs(),
        ai_advisor=FakeAi(entry={"risk_score": 0}),
        artifact_writer=ipo.IpoArtifactWriter(tmp_path, trade_date=config.trade_date),
        stop_file=tmp_path / "STOP",
        now_func=lambda: datetime(2026, 5, 11, 9, 0, 1),
    )

    now_dt = datetime(2026, 5, 11, 9, 0, 1)
    fresh_ws = ws_snapshot(ts=now_dt.timestamp())
    decision = engine.maybe_enter(target, fresh_ws, now_dt=now_dt)
    second = engine.maybe_enter(target, fresh_ws, now_dt=datetime(2026, 5, 11, 9, 0, 2))

    assert decision.allowed
    assert decision.reason == "entry_submitted"
    assert len(calls) == 2
    assert calls[1][1]["tif"] == "IOC"
    assert not second.allowed
    assert second.reason == "reentry_blocked"


def test_engine_kill_switch_blocks_new_order_after_stop_file(
    monkeypatch, config, target, tmp_path
):
    monkeypatch.setattr(ipo, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        ipo.kiwoom_orders,
        "send_buy_order",
        lambda *args, **kwargs: pytest.fail("order must not be called after stop file"),
    )
    stop_file = tmp_path / "STOP"
    stop_file.write_text("stop", encoding="utf-8")
    engine = ipo.IpoListingDayEngine(
        config,
        token="token",
        ws_manager=FakeWs(),
        ai_advisor=FakeAi(entry={"risk_score": 0}),
        artifact_writer=ipo.IpoArtifactWriter(tmp_path, trade_date=config.trade_date),
        stop_file=stop_file,
    )

    decision = engine.maybe_enter(
        target, ws_snapshot(), now_dt=datetime(2026, 5, 11, 9, 0, 1)
    )

    assert not decision.allowed
    assert decision.reason == "manual_stop_file"
