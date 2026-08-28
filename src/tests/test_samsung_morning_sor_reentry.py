from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
)

from src.trading.samsung_morning_one_share.gateway import (
    ExecutionSnapshot,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.samsung_morning_one_share.machine import KST
from src.trading.samsung_morning_one_share.policy import (
    DEFAULT_REENTRY_POLICY,
    MinuteBar,
)
from src.trading.samsung_morning_one_share.reentry import (
    SamsungMorningSORReentryMachine,
    prior_reentry_allows_new_first_episode,
    runtime_ledgers_allow_service_start,
)


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 8, 13, hour, minute, tzinfo=KST)


def _signal_bars() -> tuple[MinuteBar, ...]:
    bars = []
    for index in range(14):
        timestamp = _at(9, 1) + timedelta(minutes=index)
        bars.append(MinuteBar(timestamp, 100_500, 101_000, 100_000, 100_500))
    bars.extend(
        [
            MinuteBar(_at(9, 15), 100_500, 100_500, 100_000, 100_200),
            MinuteBar(_at(9, 16), 100_200, 100_300, 100_000, 100_200),
            MinuteBar(_at(9, 17), 100_200, 100_400, 100_000, 100_300),
        ]
    )
    return tuple(bars)


def _write_first_episode(
    path: Path,
    *,
    second_status: str = "COMPLETE",
    trade_date: date = date(2026, 8, 13),
) -> None:
    completed_at = datetime(
        trade_date.year, trade_date.month, trade_date.day, 9, 0, tzinfo=KST
    )
    payload = {
        "schema": "samsung_morning_two_leg_state_v2",
        "trade_date": trade_date.isoformat(),
        "status": "COMPLETE",
        "position_qty": 0,
        "legs": [
            {
                "leg_id": "base_plus_1tick",
                "status": "COMPLETE",
                "target_filled_qty": 1,
            },
            {
                "leg_id": "base",
                "status": second_status,
                "target_filled_qty": 1 if second_status == "COMPLETE" else 0,
            },
        ],
        "audit": [
            {
                "at_kst": completed_at.isoformat(),
                "action": "target_fill_confirmed",
                "leg_id": "base_plus_1tick",
            },
            {
                "at_kst": completed_at.isoformat(),
                "action": "target_fill_confirmed",
                "leg_id": "base",
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class ReentryGateway:
    def __init__(self, bars: tuple[MinuteBar, ...]) -> None:
        self.bars = bars
        self.buy_calls: list[int] = []
        self.sell_calls: list[int] = []
        self.cancel_calls: list[str] = []
        self.snapshots: dict[str, ExecutionSnapshot] = {}
        self.sequence = 0

    def completed_sor_minute_bars(self, *, trade_date, now):
        return MinuteBarsSnapshot(True, self.bars)

    def entry_liquidity_snapshot(self, *, route="SOR"):
        return EntryLiquiditySnapshot(
            True,
            "005930",
            route,
            "005930_AL",
            best_bid=100_000,
            best_ask=100_100,
            best_bid_qty=1_000,
            best_ask_qty=1_000,
            age_ms=0,
            received_ts_ms=1,
        )

    def entry_execution_velocity_snapshot(self, *, route="SOR"):
        return EntryExecutionVelocitySnapshot(
            True,
            "005930",
            route,
            "005930_AL",
            print_count=10,
            recent_print_span_ms=1_000,
            latest_print_age_ms=0,
            recent_volume=1_000,
            observed_at_kst="2026-08-13T09:17:00+09:00",
            print_times=("091700",) * 10,
            venues=("KRX",) * 10,
        )

    def _accepted(self, prefix: str) -> SubmitResult:
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def submit_limit_buy(self, *, price, quantity):
        assert quantity in {1, 10}
        self.buy_calls.append(price)
        return self._accepted("B")

    def submit_limit_sell(self, *, price, quantity):
        assert 1 <= quantity <= 10
        self.sell_calls.append(price)
        return self._accepted("T")

    def cancel_buy(self, *, order_no):
        self.cancel_calls.append(order_no)
        return self._accepted("C")

    def execution_snapshot(self, *, order_no, order_date, expected_order_qty):
        snapshot = self.snapshots.get(
            order_no,
            ExecutionSnapshot(True, True, 0, expected_order_qty, expected_order_qty),
        )
        if snapshot.order_qty == 1 and expected_order_qty == 10:
            return ExecutionSnapshot(
                snapshot.source_ok,
                snapshot.found,
                snapshot.filled_qty * 10,
                snapshot.remaining_qty * 10,
                10,
                snapshot.fill_price,
                snapshot.error,
            )
        return snapshot


def test_reentry_policy_requires_low_hold_and_reclaim_then_prices_minus_one_two_ticks():
    signal = DEFAULT_REENTRY_POLICY.evaluate(list(_signal_bars()))

    assert signal is not None
    assert signal.setup_bar.timestamp == _at(9, 15)
    assert signal.signal_bar.timestamp == _at(9, 17)
    assert signal.drawdown_pct >= 0.75
    assert signal.near_low_pct <= 0.35
    assert [
        leg["entry_price"]
        for leg in DEFAULT_REENTRY_POLICY.entry_legs(signal.signal_bar.close_price)
    ] == [100_200, 100_100]

    broken = list(_signal_bars())
    broken[-1] = MinuteBar(_at(9, 17), 100_200, 100_400, 99_900, 100_300)
    assert DEFAULT_REENTRY_POLICY.evaluate(broken) is None


def test_live_reentry_policy_is_pinned_to_the_reviewed_research_artifact():
    project_root = Path(__file__).resolve().parents[2]
    report_path = (
        project_root
        / "data/report/samsung_morning_reentry_research"
        / "samsung_morning_reentry_research_2026-08-10.json"
    )
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    parameters = report["selection"]["candidate"]["parameters"]

    assert hashlib.sha256(report_bytes).hexdigest() == (
        DEFAULT_REENTRY_POLICY.runtime_policy_hash
    )
    assert report["decision"] == "holdout_pass_source_only_reentry_candidate"
    assert report["selection"]["candidate"]["calibration"]["held_legs"] == 0
    assert report["selection"]["candidate"]["holdout"]["held_legs"] == 0
    assert parameters == {
        "confirmation_bars": DEFAULT_REENTRY_POLICY.confirmation_bars,
        "confirmation_low_hold_required": True,
        "entry_anchor": "confirmation_close",
        "entry_offset_ticks": -DEFAULT_REENTRY_POLICY.entry_offset_ticks,
        "entry_valid_completed_bars": DEFAULT_REENTRY_POLICY.entry_valid_completed_bars,
        "family": "low_hold_reclaim_passive_split",
        "lookback_bars": DEFAULT_REENTRY_POLICY.lookback_bars,
        "reclaim_ticks": DEFAULT_REENTRY_POLICY.reclaim_ticks,
        "rolling_high_drawdown_pct": (DEFAULT_REENTRY_POLICY.rolling_high_drawdown_pct),
        "rolling_low_proximity_pct": (DEFAULT_REENTRY_POLICY.rolling_low_proximity_pct),
        "scan_end": DEFAULT_REENTRY_POLICY.scan_last_bar.strftime("%H:%M"),
    }


def test_reentry_arms_only_after_both_first_episode_legs_complete(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=tmp_path / "reentry.json",
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(9, 18))

    assert state["status"] == "BUY_OPEN"
    assert state["attempt_consumed"] is True
    assert gateway.buy_calls == [100_200, 100_100]
    assert state["signal_features"]["family"] == "low_hold_reclaim_passive_split"
    assert state["signal_features"]["confirmation_bars"] == 2
    assert state["prerequisite"]["required_completed_leg_count"] == 2


def test_reentry_uses_durable_leg_completion_when_bounded_audit_was_evicted(
    tmp_path,
):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    payload = json.loads(first_state.read_text(encoding="utf-8"))
    payload["legs"][0]["target_filled_at"] = _at(9, 2).isoformat()
    payload["legs"][1]["target_filled_at"] = _at(9, 10).isoformat()
    payload["audit"] = [
        {
            "at_kst": _at(9, 11).isoformat(),
            "action": "target_open_wait",
            "leg_id": "base",
        }
        for _ in range(100)
    ]
    first_state.write_text(json.dumps(payload), encoding="utf-8")
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=tmp_path / "reentry.json",
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(9, 18))

    assert state["status"] == "READY"
    assert state["blocked_reason"] == ""
    assert state["prerequisite"]["first_episode_completed_at"] == (
        "2026-08-13T09:10:00+09:00"
    )
    assert gateway.buy_calls == []


def test_unarmed_same_day_provenance_block_retries_from_durable_leg_fields(
    tmp_path,
):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    first_payload = json.loads(first_state.read_text(encoding="utf-8"))
    for leg in first_payload["legs"]:
        leg["target_filled_at"] = _at(9, 0).isoformat()
    first_payload["audit"] = []
    first_state.write_text(json.dumps(first_payload), encoding="utf-8")
    reentry_state = tmp_path / "reentry.json"
    reentry_state.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "position_qty": 0,
                "legs": [],
                "owned_order_nos": [],
                "blocked_reason": "first_episode_completion_provenance_missing",
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=reentry_state,
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(9, 18))

    assert state["status"] == "BUY_OPEN"
    assert state["blocked_reason"] == ""
    assert any(
        event.get("action") == "same_day_completion_provenance_block_recovered"
        for event in state["audit"]
    )
    assert gateway.buy_calls == [100_200, 100_100]


def test_same_day_provenance_block_with_owned_order_never_retries(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    first_payload = json.loads(first_state.read_text(encoding="utf-8"))
    for leg in first_payload["legs"]:
        leg["target_filled_at"] = _at(9, 0).isoformat()
    first_payload["audit"] = []
    first_state.write_text(json.dumps(first_payload), encoding="utf-8")
    reentry_state = tmp_path / "reentry.json"
    reentry_state.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "position_qty": 0,
                "legs": [],
                "owned_order_nos": ["B1"],
                "blocked_reason": "first_episode_completion_provenance_missing",
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=reentry_state,
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(9, 18))

    assert state["status"] == "BLOCKED"
    assert state["owned_order_nos"] == ["B1"]
    assert gateway.buy_calls == []


def test_reentry_waits_until_krx_regular_without_calling_market_source(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    gateway = ReentryGateway(_signal_bars())
    source_calls = []
    original = gateway.completed_sor_minute_bars

    def counted_source(**kwargs):
        source_calls.append(kwargs)
        return original(**kwargs)

    gateway.completed_sor_minute_bars = counted_source
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=tmp_path / "reentry.json",
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(8, 30))

    assert state["status"] == "READY"
    assert state["last_action"] == "waiting_for_morning_sor_reentry_window"
    assert source_calls == []


def test_reentry_blocks_when_first_episode_contains_a_no_fill_leg(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state, second_status="NO_FILL")
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=tmp_path / "reentry.json",
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(_at(9, 18))

    assert state["status"] == "BLOCKED"
    assert state["blocked_reason"] == "first_episode_both_legs_not_complete"
    assert gateway.buy_calls == []


def test_reentry_buy_orders_cancel_only_after_three_completed_bars(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=tmp_path / "reentry.json",
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    machine.run_once(_at(9, 18))
    gateway.bars += (
        MinuteBar(_at(9, 18), 100_300, 100_400, 100_300, 100_300),
        MinuteBar(_at(9, 19), 100_300, 100_400, 100_300, 100_300),
    )
    machine.run_once(_at(9, 20))
    assert gateway.cancel_calls == []

    gateway.bars += (MinuteBar(_at(9, 20), 100_300, 100_400, 100_300, 100_300),)
    state = machine.run_once(_at(9, 21))

    assert state["status"] == "BUY_CANCEL_PENDING"
    assert gateway.cancel_calls == ["B1", "B2"]


def test_reentry_targets_are_two_ticks_and_closed_unfilled_positions_are_held(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state)
    state_path = tmp_path / "reentry.json"
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=state_path,
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    machine.run_once(_at(9, 18))
    gateway.snapshots.update(
        {
            "B1": ExecutionSnapshot(True, True, 1, 0, 1, 100_200),
            "B2": ExecutionSnapshot(True, True, 1, 0, 1, 100_100),
        }
    )

    filled = machine.run_once(_at(9, 19))

    assert filled["status"] == "TARGET_OPEN"
    assert filled["position_qty"] == 20
    assert gateway.sell_calls == [100_400, 100_300]
    gateway.snapshots.update(
        {
            "T3": ExecutionSnapshot(True, True, 0, 0, 1),
            "T4": ExecutionSnapshot(True, True, 0, 0, 1),
        }
    )

    held = machine.run_once(_at(9, 20))

    assert held["status"] == "HELD"
    assert held["position_qty"] == 20
    assert gateway.cancel_calls == []
    assert prior_reentry_allows_new_first_episode(
        state_path, target_date=date(2026, 8, 14)
    ) == (False, "prior_reentry_order_or_position_unresolved")


def test_prior_reentry_position_blocks_next_day_first_episode(tmp_path):
    path = tmp_path / "reentry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-12",
                "status": "HELD",
                "attempt_consumed": True,
                "position_qty": 1,
                "legs": [
                    {"status": "HELD", "quantity": 1},
                    {"status": "NO_FILL", "quantity": 1},
                ],
            }
        ),
        encoding="utf-8",
    )

    assert prior_reentry_allows_new_first_episode(
        path, target_date=date(2026, 8, 13)
    ) == (False, "prior_reentry_order_or_position_unresolved")


def test_prior_blocked_without_exposure_allows_next_day_first_episode(tmp_path):
    path = tmp_path / "reentry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "position_qty": 0,
                "legs": [],
                "owned_order_nos": [],
                "blocked_reason": "first_episode_both_legs_not_complete",
            }
        ),
        encoding="utf-8",
    )

    assert prior_reentry_allows_new_first_episode(
        path, target_date=date(2026, 8, 14)
    ) == (True, "prior_reentry_terminal_clear")


def test_prior_blocked_with_owned_order_remains_blocked(tmp_path):
    path = tmp_path / "reentry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "position_qty": 0,
                "legs": [],
                "owned_order_nos": ["12345"],
            }
        ),
        encoding="utf-8",
    )

    assert prior_reentry_allows_new_first_episode(
        path, target_date=date(2026, 8, 14)
    ) == (False, "prior_reentry_order_or_position_unresolved")


def test_prior_blocked_for_non_precondition_reason_remains_blocked(tmp_path):
    path = tmp_path / "reentry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "position_qty": 0,
                "legs": [],
                "owned_order_nos": [],
                "blocked_reason": "state_contract_invalid",
            }
        ),
        encoding="utf-8",
    )

    assert prior_reentry_allows_new_first_episode(
        path, target_date=date(2026, 8, 14)
    ) == (False, "prior_reentry_order_or_position_unresolved")


def test_prior_safe_precondition_block_rolls_when_reentry_episode_starts(tmp_path):
    first_state = tmp_path / "first.json"
    _write_first_episode(first_state, trade_date=date(2026, 8, 14))
    reentry_state = tmp_path / "reentry.json"
    reentry_state.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BLOCKED",
                "attempt_consumed": False,
                "position_qty": 0,
                "legs": [],
                "owned_order_nos": [],
                "blocked_reason": "first_episode_both_legs_not_complete",
                "audit": [],
            }
        ),
        encoding="utf-8",
    )
    gateway = ReentryGateway(_signal_bars())
    machine = SamsungMorningSORReentryMachine(
        gateway=gateway,
        state_path=reentry_state,
        first_episode_state_path=first_state,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )

    state = machine.run_once(datetime(2026, 8, 14, 8, 30, tzinfo=KST))

    assert state["trade_date"] == "2026-08-14"
    assert state["status"] == "READY"
    assert state["last_action"] == "waiting_for_morning_sor_reentry_window"
    assert state["audit"][0] == {
        "at_kst": "2026-08-14T08:30:00+09:00",
        "action": "daily_state_initialized_from_safe_precondition_block",
        "prior_trade_date": "2026-08-13",
        "prior_blocked_reason": "first_episode_both_legs_not_complete",
    }


def test_same_date_armed_reentry_requires_consistent_completed_first_ledger(tmp_path):
    reentry_path = tmp_path / "reentry.json"
    reentry_path.write_text(
        json.dumps(
            {
                "schema": "samsung_morning_sor_reentry_two_leg_state_v1",
                "trade_date": "2026-08-13",
                "status": "BUY_OPEN",
                "attempt_consumed": True,
                "position_qty": 0,
                "legs": [{"status": "BUY_OPEN"}, {"status": "BUY_OPEN"}],
            }
        ),
        encoding="utf-8",
    )

    assert (
        runtime_ledgers_allow_service_start(
            first_episode_path=tmp_path / "missing-first.json",
            reentry_path=reentry_path,
            target_date=date(2026, 8, 13),
        )[0]
        is False
    )

    first_path = tmp_path / "first.json"
    _write_first_episode(first_path)
    assert runtime_ledgers_allow_service_start(
        first_episode_path=first_path,
        reentry_path=reentry_path,
        target_date=date(2026, 8, 13),
    ) == (True, "same_date_ledgers_consistent")


def test_corrupt_prior_terminal_reentry_state_blocks_new_first_episode(tmp_path):
    path = tmp_path / "reentry.json"
    path.write_text(
        json.dumps(
            {
                "schema": "unexpected_schema",
                "trade_date": "2026-08-12",
                "status": "COMPLETE",
                "attempt_consumed": True,
                "position_qty": 0,
                "legs": [],
            }
        ),
        encoding="utf-8",
    )

    assert prior_reentry_allows_new_first_episode(
        path, target_date=date(2026, 8, 13)
    ) == (False, "reentry_state_schema_invalid")
