"""Source-complete blocked TP1 paths and conditional capital regressions."""

import copy
import json

import pytest

from src.engine.scalping import tp1_capital_replay as capital
from src.engine.monitoring import rising_missed_classifier_prior as prior
from src.engine.monitoring import rising_missed_intraday_feedback as feedback
from src.tests.test_rising_missed_classifier_prior import _feedback, _cost


def complete_source(day, identity, code, *, cash=1000):
    value = dict(
        schema=capital.SCHEMA,
        status="complete",
        evaluation_id=identity,
        stock_code=code,
        venue="KRX",
        session="krx_regular",
        observed_at=day + "T10:00:00+09:00",
        route="KRX",
        transport_epoch="epoch1",
        inventory_sha256="a" * 64,
        policy_sha256="b" * 64,
        capacity_source_sha256="c" * 64,
        account_scope_sha256="f" * 64,
        budget_base_krw=cash,
        available_cash_krw=cash,
        account_deposit_krw=cash,
        price_krw=100,
        allocation_price_krw=100,
        ratio=0.1,
        safety_ratio=1.0,
        absolute_cap_krw=0,
        min_one_share_floor_enabled=True,
        quantity_caps=[10],
        entry_ask_qty=100,
        other_guards_passed=True,
        cost_rate=0.002,
        cost_known_at=day + "T10:00:00+09:00",
    )
    return dict(value, sha256=capital.digest(value))


def opportunity(index=0, *, cash=1000):
    day = "2026-10-08"
    ident = str(index)
    return dict(
        source_date=day,
        evaluation_id=ident,
        stock_code="005930",
        effective_venue="KRX",
        market_session_bucket="krx_regular",
        candidate_ts=day + "T10:00:00+09:00",
        quantity_capital_source=complete_source(day, ident, "005930", cash=cash),
        counterfactual_execution=dict(
            status="full_depth_model",
            route="KRX",
            transport_epoch="epoch1",
            source_sha256="d" * 64,
            observed_epoch=capital.epoch(day + "T10:01:00+09:00"),
            exit_at=day + "T10:01:00+09:00",
            exit_bid_krw=102,
            exit_bid_qty=100,
            buy_cost_rate=0.0,
            sell_cost_rate=0.002,
            cost_source_sha256="e" * 64,
            cost_known_at=day + "T10:00:00+09:00",
        ),
    )


def test_same_cash_is_not_reused_by_overlapping_opportunities():
    rows = [opportunity(i) for i in range(12)]
    result = capital.replay(rows)
    assert result["status"] == "complete"
    # Sequential reservation with the original ratio reduces later quantity.
    assert result["rows"][0]["quantity"] == 1
    assert result["rows"][-1]["quantity"] == 0
    assert sum(r["reserved_krw"] for r in result["rows"]) <= 1000
    assert all(r["baseline_no_trade"] for r in result["rows"])
    assert result["actual_profit_verified"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "future_budget",
        "unknown_exit",
        "different_account",
        "missing_cost",
        "partial_depth",
        "epoch_change",
        "scope_change",
    ],
)
def test_missing_provenance_never_becomes_zero_profit(mutation):
    first, second = opportunity(0), opportunity(1)
    if mutation == "future_budget":
        first["quantity_capital_source"]["observed_at"] = "2026-10-08T10:00:01+09:00"
    elif mutation == "unknown_exit":
        first["counterfactual_execution"]["exit_at"] = "2026-10-09T10:01:00+09:00"
    elif mutation == "different_account":
        second["quantity_capital_source"]["account_deposit_krw"] += 100
    elif mutation == "missing_cost":
        first["counterfactual_execution"].pop("cost_source_sha256")
    elif mutation == "epoch_change":
        first["counterfactual_execution"]["transport_epoch"] = "epoch2"
    elif mutation == "scope_change":
        second["quantity_capital_source"]["account_scope_sha256"] = "1" * 64
    else:
        first["counterfactual_execution"]["exit_bid_qty"] = 0
    for row in (first, second):
        s = row["quantity_capital_source"]
        s["sha256"] = capital.digest({k: v for k, v in s.items() if k != "sha256"})
    result = capital.replay([first, second])
    assert result["status"] == "censored"
    assert result["daily_net_profit_krw"] is None
    assert result["gaps"]


def test_nxt_same_receipt_capital_model_uses_executable_ask_and_original_allocation_price():
    row = opportunity()
    row.update(effective_venue="NXT", market_session_bucket="nxt_premarket")
    source = row["quantity_capital_source"]
    source.update(venue="NXT", session="nxt_premarket", route="NXT", price_krw=101)
    source["sha256"] = capital.digest(
        {k: v for k, v in source.items() if k != "sha256"}
    )
    row["counterfactual_execution"]["route"] = "NXT"
    result = capital.replay([row])
    assert result["status"] == "complete" and result["rows"][0]["quantity"] == 1
    assert result["rows"][0]["reserved_krw"] == 101
    assert (
        sum(result["daily_net_profit_krw"].values()) > 0
        and result["actual_profit_verified"] is False
    )


@pytest.mark.parametrize("session", ["krx_regular", "krx_nxt_aftermarket"])
def test_integrated_market_is_one_decision_scope_with_sor_route(session):
    row = opportunity()
    row.update(effective_venue="KRX_NXT_INTEGRATED", market_session_bucket=session)
    source = row["quantity_capital_source"]
    source.update(
        venue="KRX_NXT_INTEGRATED",
        decision_market_scope="KRX_NXT_INTEGRATED",
        session=session,
        route="SOR",
    )
    source["sha256"] = capital.digest(
        {k: v for k, v in source.items() if k != "sha256"}
    )
    row["counterfactual_execution"]["route"] = "SOR"
    result = capital.replay([row])
    assert result["status"] == "complete" and len(result["rows"]) == 1
    assert result["actual_profit_verified"] is False


@pytest.mark.parametrize(
    "clock,route,expected",
    [
        ("08:30:00", "nxt_only", "PREMARKET_KRX_LIKE"),
        ("10:00:00", "krx_nxt_integrated", "KRX_NXT_INTEGRATED"),
        ("17:00:00", "krx_nxt_integrated", "KRX_NXT_INTEGRATED"),
        ("17:00:00", "nxt_only", "UNKNOWN"),
    ],
)
def test_native_observation_keeps_integrated_population_separate_from_venue(
    monkeypatch, clock, route, expected
):
    from src.engine import sniper_state_handlers as handler

    monkeypatch.setattr(
        handler, "_holding_sell_nxt_enabled_status", lambda *a: (True, "fixture")
    )
    at = capital.epoch("2026-10-08T" + clock + "+09:00")
    fields = handler._rising_missed_nxt_observation_fields(
        {},
        "005930",
        dict(
            last_realtime_type_ts={"0D": at},
            last_realtime_type_market_route={"0D": route},
        ),
        {},
        now_ts=at,
    )
    assert fields["decision_market_scope"] == expected
    assert fields["actual_execution_venue"] == "UNKNOWN"
    assert feedback._tp1_effective_venue(fields) == (
        expected if expected != "UNKNOWN" else "unknown"
    )


def test_native_session_contract_integrated_scope_alias_is_preserved():
    assert (
        feedback._tp1_effective_venue(
            dict(decision_market_scope="KRX_NXT", rising_missed_effective_venue="NXT")
        )
        == "KRX_NXT_INTEGRATED"
    )


@pytest.mark.parametrize(
    "venue,session,route,item",
    [
        ("NXT", "krx_like_premarket", "nxt_only", "005930_NX"),
        ("KRX_NXT_INTEGRATED", "krx_regular", "krx_nxt_integrated", "005930_AL"),
        (
            "KRX_NXT_INTEGRATED",
            "krx_nxt_aftermarket",
            "krx_nxt_integrated",
            "005930_AL",
        ),
    ],
)
def test_native_quantity_capture_reaches_model_without_network(
    monkeypatch, venue, session, route, item
):
    from src.engine import sniper_state_handlers as handler
    from src.trading.market import quote_consistency

    at = capital.epoch("2026-10-08T10:00:00+09:00")
    cached = dict(
        budget_base=1000,
        cash_orderable_qty_cap=10,
        kt00011_requested_unit_price=100,
        kt00011_capacity_source_sha256="c" * 64,
        kt00011_capacity_observed_at="2026-10-08T10:00:00+09:00",
        cash_orderable_amount=1000,
        account_deposit=1000,
    )

    def shared_cache(*args, **kwargs):
        assert kwargs["reuse_only"] is True and kwargs["source_only"] is True
        return cached

    monkeypatch.setattr(handler, "_resolve_scalp_cash_budget_context", shared_cache)
    monkeypatch.setattr(
        handler, "_scale_in_budget_inventory_signature", lambda: "a" * 64
    )
    quote = dict(
        source_type="0D",
        item=item,
        market_route=route,
        transport_epoch="epoch1",
        depth_receipt=dict(
            item=item, market_route=route, transport_epoch="epoch1", observed_epoch=at
        ),
    )
    monkeypatch.setattr(
        quote_consistency, "ws_quote_source_receipt", lambda *a, **kw: quote
    )
    row = opportunity()
    row.update(effective_venue=venue, market_session_bucket=session)
    fields = dict(
        rising_missed_tp1_evaluation_id="0",
        decision_market_scope=venue,
        rising_missed_effective_venue="NXT",
        rising_missed_market_session_bucket=session,
        rising_missed_tp1_counterfactual_submit_safety_action="NO_CURRENT_VETO_EVIDENCE",
    )
    source = handler._capture_tp1_quantity_capital_source(
        {},
        "005930",
        fields,
        dict(curr=100, orderbook=dict(asks=[dict(price=101, volume=100)])),
        at,
    )
    assert source["status"] == "complete", source
    assert (
        source["venue"] == venue
        and source["allocation_price_krw"] == 100
        and source["price_krw"] == 101
    )
    assert source["route"] == ("NXT" if route == "nxt_only" else "SOR")
    assert capital.validate_source(source, row) == source


def test_blocked_zero_submit_can_select_publish_and_load(monkeypatch, tmp_path):
    from src.engine.automation import runtime_policy_bootstrap as bootstrap

    monkeypatch.setattr(prior, "comparison_cost_contract", _cost)
    days = ("2026-09-10", "2026-09-11", "2026-09-14", "2026-09-15", "2026-09-16")
    paths = []
    for day in days:
        path = _feedback(
            tmp_path / f"rising_missed_intraday_feedback_{day}.json",
            day,
            [("gross_target_first", None)] * 12,
        )
        payload = json.loads(path.read_text())
        for support, label in zip(
            payload["rising_missed_tp1_counterfactual_submit_safety_rows"],
            payload["rising_missed_tp1_counterfactual_first_hit_label_rows"],
        ):
            support["quantity_capital_source"] = complete_source(
                day, label["evaluation_id"], label["stock_code"]
            )
            label["post_block_horizon_measurements"][0]["first_hit_execution_quote"] = (
                dict(
                    exit_at=day + "T10:01:00+09:00",
                    exit_bid_krw=102,
                    exit_bid_qty=100,
                    route="KRX",
                    transport_epoch="epoch1",
                    source_sha256="d" * 64,
                    observed_epoch=capital.epoch(day + "T10:01:00+09:00"),
                )
            )
        path.write_text(json.dumps(payload))
        paths.append(path)
    report = prior.build_report(
        days[-1], source_paths=paths, generated_at=days[-1] + "T21:00:00+09:00"
    )
    assert report["status"] == "validated_edge"
    monkeypatch.setattr(prior, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(bootstrap, "RISING_MISSED_REPORT_DIR", tmp_path)
    result = prior.write_outputs(
        report,
        output_json=tmp_path / f"rising_missed_classifier_prior_{days[-1]}.json",
        output_md=tmp_path / "report.md",
        effective_date="2026-09-17",
    )
    accepted, rejected = bootstrap._load_direct_receipts(
        "2026-09-17", [prior.policy_paths(days[-1], "2026-09-17")[1]]
    )
    assert not rejected
    assert accepted[0]["status"] == "validated_edge"
    assert (
        result["policy"]["runtime_env_overrides"][
            prior.RUNTIME_ENV_KEYS["positive_support_min"]
        ]
        == "1"
    )
