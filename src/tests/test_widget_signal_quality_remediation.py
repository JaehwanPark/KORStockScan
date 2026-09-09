from copy import deepcopy
from datetime import date, datetime, timedelta
import json

import pytest

from src.engine.monitoring.widget_execution_quality import load_execution_incidents
from src.engine.monitoring.widget_signal_quality import (
    confirmation_comparison,
    component_arms,
)
from src.engine.monitoring.samsung_widget_advisory import AdvisoryPromotionFilter
from src.engine.monitoring.low_price_two_leg_tuning import _aggregate, _policy_windows


def _event(**changes):
    return {
        "observed_at": "2026-09-08T15:22:08+09:00",
        "symbol": "005930",
        "execution_authority": "operator_directed_widget_auto_trade_v1",
        "execution_policy_id": "policy",
        "execution_policy_session": "KRX_REGULAR",
        "parent_entry_signal_id": "parent",
        "order_role": "TAKE_PROFIT_SELL",
        "side": "SELL",
        "requested_qty": 30,
        "event_type": "order_submit_failed",
        **changes,
    }


def _write_events(tmp_path, events):
    by_date = {}
    for row in events:
        day = row["observed_at"][:10].replace("-", "")
        by_date.setdefault(day, []).append(row)
    for day, rows in by_date.items():
        (tmp_path / f"widget_signal_auto_trade_events_{day}.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows)
        )


@pytest.mark.parametrize(
    "kind,closed",
    [
        ("full", True),
        ("partial", False),
        ("pending", False),
        ("other_owner", False),
        ("wrong_hash", False),
        ("future", False),
    ],
)
def test_manual_registry_projection_closes_only_exact_flat_custody(
    tmp_path, kind, closed
):
    import hashlib
    from src.trading.order.owner_custody_registry import (
        OrderOwnerRegistry,
        REGISTRY_SCHEMA,
    )

    _write_events(tmp_path, [_event()])
    common = dict(
        schema=REGISTRY_SCHEMA,
        account_key="fixture",
        symbol="005930",
        owner_type="widget_auto_trade",
        owner_id="widget_auto_trade:005930:2026-09-08",
        position_id="widget_auto_trade:005930:2026-09-08:parent",
        action="NEW",
        state="ORDER_TERMINAL",
        quantity=30,
        filled_qty=30,
        fill_amount=30000,
    )
    buy = dict(
        common,
        intent_id="buy",
        event="ORDER_EXECUTION_UPDATED",
        side="BUY",
        observed_at_kst="2026-09-08T10:00:00+09:00",
    )
    sell = dict(
        common,
        intent_id="sell",
        event="MANUAL_EXIT_RECONCILED",
        side="SELL",
        execution_owner_type="manual_operator",
        observed_at_kst="2026-09-08T16:00:00+09:00",
        manual_exit_evidence_sha256="a" * 64,
        broker_order_no="0000007",
    )
    if kind == "partial":
        sell.update(quantity=5, filled_qty=5)
    elif kind == "pending":
        buy["state"] = "ORDER_BOUND"
    elif kind == "other_owner":
        sell["owner_type"] = "episode"
    elif kind == "future":
        sell["observed_at_kst"] = "2026-09-10T10:00:00+09:00"
    previous, lines = "0" * 64, []
    for row in (buy, sell):
        row["previous_hash"] = previous
        row["event_hash"] = hashlib.sha256(
            previous.encode() + OrderOwnerRegistry._canonical(row)
        ).hexdigest()
        previous = row["event_hash"]
        lines.append(json.dumps(row))
    if kind == "wrong_hash":
        lines[1] = lines[1].replace(sell["event_hash"], "0" * 64)
    registry = tmp_path / "registry.jsonl"
    registry.write_text("\n".join(lines))
    result = load_execution_incidents(
        "005930",
        target_date=date(2026, 9, 9),
        session="KRX_REGULAR",
        event_dir=tmp_path,
        custody_registry_path=registry,
    )
    assert (result["unresolved_incident_count"] == 0) is closed
    assert result["full_fill_order_count"] == 0
    assert result["runtime_apply_allowed"] is closed


def test_component_selector_does_not_apply_joint_change_or_search_holdout():
    from src.engine.monitoring.widget_signal_quality import select_policy_component

    def arm(ev, pnl):
        summary = dict(
            episode_count=12,
            notional_weighted_ev_pct=ev,
            worst_episode_return_pct=-0.1,
            modeled_net_pnl_per_qualified_day=pnl,
            observed_occupancy_seconds_sum=100,
            small_profit_completed_within_180s_count=3,
            profitable_completed_within_180s_count=3,
        )
        return {
            "parameters": {"max_completed_entries_per_day": 1},
            **{
                window: dict(summary)
                for window in (
                    "calibration",
                    "calibration_first_half",
                    "calibration_second_half",
                    "holdout",
                )
            },
        }

    comparison = {
        "arms": {
            "applied_baseline": arm(0.1, 100),
            "signal_only": arm(0.2, 120),
            "exit_only": arm(0.3, 130),
            "combined_candidate": arm(10, 10000),
        }
    }
    for window in (
        "calibration",
        "calibration_first_half",
        "calibration_second_half",
        "holdout",
    ):
        # A profitable exit leaving the diagnostic <=0.5% bin is not a lost win.
        comparison["arms"]["exit_only"][window][
            "small_profit_completed_within_180s_count"
        ] = 0
    assert select_policy_component(comparison)["selected_arm"] == "exit_only"
    comparison["arms"]["exit_only"]["holdout"]["notional_weighted_ev_pct"] = -0.1
    assert select_policy_component(comparison)["selected_arm"] == "applied_baseline"
    comparison["arms"]["applied_baseline"]["holdout"]["notional_weighted_ev_pct"] = None
    assert select_policy_component(comparison)["selected_arm"] is None


def test_retry_terminal_is_one_incident_and_carries_across_empty_day(tmp_path):
    rows = [
        _event(observed_at=f"2026-09-08T15:22:{second}+09:00")
        for second in ("08", "13", "18")
    ]
    rows.append(
        _event(
            observed_at="2026-09-08T15:22:19+09:00",
            event_type="take_profit_terminal_failure",
        )
    )
    _write_events(tmp_path, [*rows, rows[0]])
    result = load_execution_incidents(
        "005930",
        target_date=date(2026, 9, 9),
        session="KRX_REGULAR",
        event_dir=tmp_path,
    )
    assert result["incident_count"] == 1
    assert result["duplicate_event_count"] == 1
    assert result["incidents"][0]["failed_submit_attempt_count"] == 3
    assert result["incidents"][0]["terminal_failure_event_count"] == 1
    assert result["runtime_apply_allowed"] is False


@pytest.mark.parametrize(
    "changes,resolved",
    [
        ({}, True),
        ({"filled_qty": 5, "requested_qty": 5}, False),
        ({"execution_authority": "main"}, False),
        ({"execution_policy_id": "other"}, False),
        ({"execution_policy_session": "NXT_AFTERMARKET"}, False),
        ({"parent_entry_signal_id": "other"}, False),
        ({"actual_order_submitted": False}, False),
        ({"remaining_qty": 1}, False),
    ],
)
def test_only_exact_later_full_fill_resolves(tmp_path, changes, resolved):
    receipt = _event(
        observed_at="2026-09-09T10:00:00+09:00",
        event_type="order_execution_reconciled",
        filled_qty=30,
        remaining_qty=0,
        fill_price=1000,
        order_no="7",
        order_status="FILLED",
        actual_order_submitted=True,
    )
    receipt.update(changes)
    _write_events(tmp_path, [_event(), receipt])
    result = load_execution_incidents(
        "005930", target_date=date(2026, 9, 9), event_dir=tmp_path
    )
    assert result["runtime_apply_allowed"] is resolved
    assert result["resolved_incident_count"] == int(resolved)


def test_definitive_rejected_buy_is_not_open_custody_or_execution_success(tmp_path):
    _write_events(
        tmp_path,
        [
            _event(
                side="BUY",
                order_role="ENTRY_BUY",
                ambiguous=False,
                actual_order_submitted=False,
                order_no="",
                return_code="20",
            )
        ],
    )
    result = load_execution_incidents(
        "005930", target_date=date(2026, 9, 9), event_dir=tmp_path
    )
    assert result["closed_rejected_no_order_count"] == 1
    assert result["resolved_incident_count"] == 0
    assert result["unique_order_count"] == 0
    assert result["runtime_apply_allowed"] is True


@pytest.mark.parametrize("changes", [{"filled_qty": 30.5}, {"remaining_qty": False}])
def test_invalid_quantity_receipt_does_not_close_incident(tmp_path, changes):
    receipt = _event(
        observed_at="2026-09-09T10:00:00+09:00",
        event_type="order_execution_reconciled",
        filled_qty=30,
        requested_qty=30,
        remaining_qty=0,
        fill_price=1000,
        order_no="7",
        order_status="FILLED",
        actual_order_submitted=True,
    )
    receipt.update(changes)
    _write_events(tmp_path, [_event(), receipt])
    assert (
        load_execution_incidents(
            "005930", target_date=date(2026, 9, 9), event_dir=tmp_path
        )["runtime_apply_allowed"]
        is False
    )


def test_prebaseline_and_future_events_never_enter_current_incident(tmp_path):
    _write_events(
        tmp_path,
        [
            _event(observed_at="2026-06-04T10:00:00+09:00"),
            _event(observed_at="2026-09-10T10:00:00+09:00"),
        ],
    )
    assert (
        load_execution_incidents(
            "005930", target_date=date(2026, 9, 9), event_dir=tmp_path
        )["incident_count"]
        == 0
    )


def test_missing_realized_economics_is_null():
    for status in ("NO_FILL", "HELD", "proxy"):
        row = {
            "eligible_for_tuning": status != "HELD",
            "source_quality": "pass",
            "attempted": True,
            "legs": [
                {
                    "completed": status == "proxy",
                    "quantity": 10,
                    "entry_price": 1000,
                    "buy_filled_qty": 10,
                    "fill_price": 1000,
                    "net_profit_pct": 0.2,
                    "profit_price_source": "configured_target_price_proxy",
                }
            ],
        }
        result = _aggregate([row])
        assert result["notional_weighted_ev_pct"] is None
        assert result["cost_adjusted_net_profit_krw"] is None


def test_semantic_cohort_and_contiguous_epoch_separate_a_b_a():
    a, b = {"target": 2, "lookback": 15}, {"target": 4, "lookback": 15}
    rows = [
        {"target_date": day, "legs": []}
        for day in ("2026-09-04", "2026-09-07", "2026-09-08")
    ]
    cohort, epoch = _policy_windows(
        rows,
        current_policy=a,
        policies_by_date={
            rows[0]["target_date"]: a,
            rows[1]["target_date"]: b,
            rows[2]["target_date"]: deepcopy(a),
        },
    )
    assert len(cohort["rows"]) == 2
    assert len(epoch["rows"]) == 1
    assert epoch["applied_epoch_start"] == "2026-09-08"
    _, missing_epoch = _policy_windows(
        rows, current_policy=a, policies_by_date={"2026-09-08": a, "2026-09-09": None}
    )
    assert missing_epoch["rows"] == []


def test_confirmation_trace_preserves_hidden_range_and_replays_extra_ten_seconds():
    promotion = AdvisoryPromotionFilter()
    start = datetime.fromisoformat("2026-09-09T10:00:00+09:00")
    rows = []
    for second in (0, 10, 20):
        result = promotion.apply(
            {
                "observed_at": (start + timedelta(seconds=second)).isoformat(),
                "session": "KRX_REGULAR",
                "raw_state": "ENTRY_READY",
                "state": "ENTRY_READY",
                "entry_price_low": 1000,
                "entry_price_high": 1010,
            },
            required_confirmations=3,
        )
        rows.append({"advisory": result})
    assert rows[0]["advisory"]["entry_price_low"] is None
    assert (
        rows[0]["advisory"]["confirmation_input_trace"]["rows"][0]["entry_price_low"]
        == 1000
    )
    comparison = confirmation_comparison([*rows, rows[-1]], target_date=start.date())
    assert comparison["exact_input_count"] == 3
    assert comparison["episodes"][0]["additional_confirmation_delay_sec"] == 10
    assert comparison["episodes"][0]["executable_net_ev_delta_pct"] is None
    assert comparison["allowed_runtime_apply"] is False


def test_component_comparison_never_uses_candidate_as_missing_baseline():
    assert (
        component_arms(
            None, {"target": 100}, signal_keys=("signal",), exit_keys=("target",)
        )
        == {}
    )
    baseline = {"signal": 1, "target": 50, "quantity": 10}
    arms = component_arms(
        baseline,
        {"signal": 2, "target": 100, "quantity": 10},
        signal_keys=("signal",),
        exit_keys=("target",),
    )
    assert arms["signal_only"] == {"signal": 2, "target": 50, "quantity": 10}
    assert arms["exit_only"] == {"signal": 1, "target": 100, "quantity": 10}
    arms["applied_baseline"]["signal"] = 9
    assert baseline["signal"] == 1


def test_exact_buy_cancel_receipt_does_not_require_nonexistent_fill(tmp_path):
    _write_events(
        tmp_path,
        [
            _event(
                side="BUY",
                order_no="10",
                parent_entry_signal_id=None,
                event_type="buy_cancel_terminal_failure",
            ),
            _event(
                observed_at="2026-09-09T09:01:00+09:00",
                side="BUY",
                order_no="10",
                parent_entry_signal_id=None,
                event_type="order_execution_reconciled",
                order_role="ENTRY_BUY",
                actual_order_submitted=True,
                order_status="CANCELLED",
                filled_qty=0,
                remaining_qty=0,
            ),
        ],
    )
    result = load_execution_incidents(
        "005930", target_date=date(2026, 9, 9), event_dir=tmp_path
    )
    assert result["unresolved_incident_count"] == 0
    assert result["resolved_incident_count"] == 1
    assert result["runtime_apply_allowed"] is True


def test_both_policy_branches_preserve_same_day_rejection_veto(tmp_path):
    _write_events(
        tmp_path,
        [
            _event(
                side="BUY",
                order_role="ENTRY_BUY",
                ambiguous=False,
                actual_order_submitted=False,
                return_code="20",
            )
        ],
    )
    result = load_execution_incidents(
        "005930", target_date=date(2026, 9, 8), event_dir=tmp_path
    )
    assert result["unresolved_incident_count"] == 0
    assert result["runtime_apply_allowed"] is False


def test_confirmation_missing_or_malformed_trace_is_not_no_opportunity():
    rows = [
        {"advisory": None},
        {"advisory": {"confirmation_input_trace": "bad"}},
        {
            "advisory": {
                "confirmation_input_trace": {
                    "schema": "widget_confirmation_input_trace_v1",
                    "rows": None,
                }
            }
        },
    ]
    result = confirmation_comparison(rows, target_date=date(2026, 9, 9))
    assert result["status"] == "source_gap"
    assert result["legacy_or_invalid_trace_row_count"] == 3


@pytest.mark.parametrize("with_economics", [False, True])
def test_symbol_research_emits_fixed_baseline_component_windows(
    monkeypatch, with_economics
):
    from src.engine.monitoring import widget_symbol_signal_policy_research as research
    from dataclasses import asdict

    dates = [date(2026, 9, day) for day in (7, 8, 9)]
    if with_economics:
        dates = [
            date(2026, 8, 24) + timedelta(days=offset)
            for offset in range(17)
            if (date(2026, 8, 24) + timedelta(days=offset)).weekday() < 5
        ]
    bars = [
        research.Bar(
            datetime.fromisoformat(f"{day}T10:00:00+09:00"), 1000, 1000, 1000, 1000, 1
        )
        for day in dates
    ]
    policy = research.SignalPolicy(
        "midday", 30, 1.0, 0.5, 1, 50, minimum_history_bars=30
    )
    cap = 2 if with_economics else 1
    parameters = {**asdict(policy), "max_completed_entries_per_day": cap}
    monkeypatch.setattr(research, "HOLDOUT_DAYS", 2 if with_economics else 1)
    monkeypatch.setattr(research, "_clean_trading_dates", lambda _: dates)
    monkeypatch.setattr(
        research,
        "_daily_source_coverage",
        lambda *_: {"status": "PASS", "qualified_dates": [str(day) for day in dates]},
    )
    monkeypatch.setattr(
        research,
        "discover_symbol_policy",
        lambda *_args, **_kwargs: {
            "decision": "holdout_pass_widget_signal_policy_candidate",
            "selected_policy": {**parameters, "target_bps": 100},
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
    )

    def evaluate(_grouped, window_dates, selected, **_kwargs):
        episodes = []
        if with_economics:
            for day in window_dates:
                for ordinal in (1, 2):
                    entry = datetime.fromisoformat(
                        f"{day}T12:{ordinal * 11:02d}:00+09:00"
                    )
                    episodes.append(
                        dict(
                            trade_date=str(day),
                            daily_entry_ordinal=ordinal,
                            entry_at=entry.isoformat(),
                            exit_at=(entry + timedelta(seconds=30)).isoformat(),
                            entry_price=1000,
                            net_return_pct=0.3 if selected.target_bps == 100 else 0.1,
                            exit_reason="target",
                            entry_state="ENTRY_READY",
                            peak_return_pct=0.5,
                        )
                    )
        return {
            "episodes": episodes,
            "entry_cap_comparison": research._entry_cap_comparison(episodes),
        }

    monkeypatch.setattr(research, "evaluate_policy", evaluate)
    monkeypatch.setattr(
        research, "load_execution_incidents", lambda *_args, **_kwargs: {}
    )
    result = research.build_report(
        sources={
            symbol: (bars, {"source_quality_status": "PASS"})
            for symbol in research.SYMBOLS
        },
        end_date=dates[-1],
        applied_baselines={
            symbol: {
                "policy_id": "baseline",
                "signal_policy": asdict(policy),
                "execution_policy": {"max_completed_entries_per_day": cap},
            }
            for symbol in research.SYMBOLS
        },
    )
    comparison = next(iter(result["symbols"].values()))["component_comparison"]
    assert set(comparison["arms"]) == {
        "applied_baseline",
        "signal_only",
        "exit_only",
        "combined_candidate",
    }
    assert comparison["arms"]["signal_only"]["parameters"]["target_bps"] == 50
    assert comparison["arms"]["exit_only"]["parameters"]["target_bps"] == 100
    assert comparison["arms"]["applied_baseline"]["holdout"][
        "notional_weighted_ev_pct"
    ] == (0.1 if with_economics else None)
    assert comparison["baseline_pid_consumption_verified"] is False
    if with_economics:
        from src.engine.monitoring.widget_symbol_runtime_policy import (
            _validated_selected_policy,
        )

        chosen = next(iter(result["symbols"].values()))
        assert chosen["component_selection"]["selected_arm"] == "exit_only"
        assert _validated_selected_policy(chosen) is not None
        chosen["selected_policy"]["max_completed_entries_per_day"] = 3
        assert _validated_selected_policy(chosen) is None


def test_duplicate_runtime_observation_does_not_satisfy_confirmation():
    promotion = AdvisoryPromotionFilter()
    raw = {
        "observed_at": "2026-09-09T10:00:00+09:00",
        "session": "KRX_REGULAR",
        "raw_state": "ENTRY_READY",
        "state": "ENTRY_READY",
        "entry_price_low": 1000,
        "entry_price_high": 1010,
    }
    assert promotion.apply(raw)["state"] == "WATCH"
    assert promotion.apply(raw)["state"] == "WATCH"
    assert (
        promotion.apply({**raw, "observed_at": "2026-09-09T10:00:10+09:00"})["state"]
        == "ENTRY_READY"
    )
