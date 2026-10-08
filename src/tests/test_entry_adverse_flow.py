"""Synthetic tapes and isolated policies; no broker or profitability claims."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

from src.trading.market.main_entry_micro_window import CONTRACT, evaluate_snapshot

SCOPE = dict(
    owner="widget",
    scope_id="005930:KRX_REGULAR",
    symbol="005930",
    route="SOR",
    session="KRX_REGULAR",
)
NOW = datetime(2026, 9, 9, 4, tzinfo=timezone.utc)


def source(data):
    return data["stocks"]["005930"]["machine_confirmation_routes"]["SOR"]


def snapshot(now):
    cutoff = int(now.timestamp() * 1000)
    item = "005930_AL"

    def depth(seq, offset, qty):
        return dict(
            item=item,
            transport_epoch=1,
            route_sequence=seq,
            received_at_ms=cutoff + offset,
            best_bid=10100,
            best_ask=10110,
            best_ask_qty=qty,
            ask_levels=[dict(price=10110, quantity=qty)],
            bid_levels=[dict(price=10100, quantity=100)],
        )

    def trade(seq, offset, qty):
        return dict(
            item=item,
            transport_epoch=1,
            route_sequence=seq,
            received_at_ms=cutoff + offset,
            price=10110,
            volume=qty,
            aggressor_side="BUY",
        )

    return dict(
        schema_version="kiwoom_ws_dashboard_snapshot_v1",
        decision_authority="source_quality_only",
        runtime_effect=False,
        machine_confirmation_input_contract=dict(
            schema="machine_entry_confirmation_ws_snapshot_v1",
            decision_authority="market_data_input_only_no_order_authority",
            exact_route_required=True,
            causal_past_only=True,
            runtime_effect=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
        stocks={
            "005930": {
                "machine_confirmation_routes": {
                    "SOR": dict(
                        realtime_types={
                            k: dict(
                                item=item,
                                transport_epoch=1,
                                route_sequence=seq,
                                observed_epoch=(cutoff + offset) / 1000,
                            )
                            for k, seq, offset in (("0B", 4, -150), ("0D", 3, 0))
                        },
                        recent_depth=[
                            depth(1, -1000, 120),
                            depth(2, -100, 20),
                            depth(3, 0, 25),
                        ],
                        recent_trades=[
                            trade(1, -1100, 1),
                            trade(2, -800, 40),
                            trade(3, -300, 40),
                            trade(4, -150, 30),
                        ],
                        sequence_authority="local_projection_continuity_not_exchange_completeness",
                    )
                }
            }
        },
    )


def tape(now=NOW, adverse=True):
    data = snapshot(now)
    s = source(data)
    if adverse:
        for row in s["recent_trades"]:
            row["aggressor_side"] = "SELL"
        s["recent_depth"][1]["best_bid"] = 10090
        s["recent_depth"][2]["best_bid"] = 10080
    return data


def calc(data):
    return evaluate_snapshot(
        snapshot=data,
        symbol="005930",
        route="SOR",
        cutoff_ms=int(NOW.timestamp() * 1000),
    )




@pytest.mark.parametrize("adverse", [True, False])
def test_relational_rule(adverse):
    result = calc(tape(adverse=adverse))
    assert result["action"] == ("DEFER_ADVERSE_FLOW" if adverse else "CONTINUE")


def test_integrated_route_identity_is_preserved_without_krx_inference():
    data = tape(adverse=False)
    for receipt in source(data)["realtime_types"].values():
        receipt["effective_venue"] = ""
        receipt["market_route"] = "krx_nxt_integrated"

    result = evaluate_snapshot(
        snapshot=data,
        symbol="005930",
        route="SOR",
        cutoff_ms=int(NOW.timestamp() * 1000),
        market_session="KRX_REGULAR",
    )

    assert result["source_quality_status"] == "eligible"
    assert result["effective_venue"] == "KRX_NXT_INTEGRATED"
    assert result["market_session"] == "KRX_REGULAR"
    assert result["route_identity_source"] == "exact_integrated_market_route"


@pytest.mark.parametrize(
    "mutation", ["bid_recovery", "buy_dominance", "sell_easing", "bid_support"]
)
def test_each_condition_is_necessary(mutation):
    data = tape()
    s = source(data)
    if mutation == "bid_recovery":
        s["recent_depth"][1]["best_bid"] = 10070
    elif mutation == "buy_dominance":
        s["recent_trades"][1]["aggressor_side"] = "BUY"
    elif mutation == "sell_easing":
        s["recent_trades"][1]["volume"] = 1000
    else:
        s["recent_depth"][2]["best_bid"] = 10100
    assert calc(data)["action"] == "CONTINUE"


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "duplicate_conflict",
        "gap",
        "truncated",
        "epoch",
        "authority",
        "missing",
        "stale",
    ],
)
def test_source_failure_is_not_neutral(mutation):
    data = tape()
    s = source(data)
    if mutation == "unknown":
        s["recent_trades"][1]["aggressor_side"] = "UNKNOWN"
    elif mutation == "duplicate_conflict":
        s["recent_trades"].append(dict(s["recent_trades"][1], volume=99))
    elif mutation == "gap":
        s["recent_trades"].pop(2)
    elif mutation == "truncated":
        s["recent_depth"].pop(0)
    elif mutation == "epoch":
        s["realtime_types"]["0B"]["transport_epoch"] = 2
    elif mutation == "authority":
        data["runtime_effect"] = True
    elif mutation == "missing":
        s["recent_trades"] = []
    else:
        s["recent_depth"][0]["received_at_ms"] -= 2000
    assert calc(data)["action"] == "SOURCE_UNAVAILABLE"


def test_causal_cutoff_duplicate_and_half_boundary():
    data = tape()
    s = source(data)
    s["recent_trades"][1]["received_at_ms"] = int(NOW.timestamp() * 1000) - 500
    before = calc(data)
    s["recent_trades"].append(deepcopy(s["recent_trades"][1]))
    s["recent_trades"].append(
        dict(
            s["recent_trades"][-2],
            received_at_ms=int(NOW.timestamp() * 1000) + 1,
            aggressor_side="UNKNOWN",
        )
    )
    assert calc(data) == before
    assert before["sell_qty_halves"] == [40, 70]


























@pytest.mark.parametrize('venue,session', [('KRX_NXT_INTEGRATED', 'KRX_NXT_AFTERMARKET'), ('PREMARKET_KRX_LIKE', 'PREMARKET_KRX_LIKE')])
def test_machine_scope_alias_uses_exact_market_data_route_and_keeps_broker_route_separate(venue, session):
    from src.trading.market.main_entry_micro_window import evaluate_machine_entry_payload
    data = snapshot(NOW)
    for receipt in source(data)['realtime_types'].values():
        receipt['market_route'] = 'krx_nxt_integrated'
        receipt['effective_venue'] = 'KRX_NXT_INTEGRATED'
    payload = {'stock_code': '005930', 'effective_venue': venue, 'session_bucket': session,
               'ai_market_snapshot_v1': {'snapshot_id': 'exact', 'stock_code': '005930',
                   'effective_venue': venue, 'session_bucket': session,
                   'market_data_route': 'krx_nxt_integrated', 'broker_route': 'NXT'}}
    cutoff = int(NOW.timestamp()*1000)
    assert evaluate_snapshot(snapshot=data, symbol='005930', route=venue, cutoff_ms=cutoff)['action'] == 'SOURCE_UNAVAILABLE'
    result = evaluate_machine_entry_payload(snapshot=data, payload=payload, cutoff_ms=cutoff)
    assert result['source_quality_status'] == 'eligible'
    assert result['item'] == '005930_AL'
    assert result['market_session'] == session
    assert result['machine_market_route_binding']['confirmation_route'] == 'SOR'
    assert result['machine_market_route_binding']['effective_venue'] == venue


def test_machine_payload_route_missing_or_identity_conflict_stays_source_gap():
    from src.trading.market.main_entry_micro_window import evaluate_machine_entry_payload
    data = snapshot(NOW)
    payload = {'stock_code': '005930', 'effective_venue': 'KRX_NXT_INTEGRATED', 'session_bucket': 'KRX_NXT_AFTERMARKET',
               'ai_market_snapshot_v1': {'snapshot_id': 'exact', 'stock_code': '005930',
                   'effective_venue': 'NXT', 'session_bucket': 'KRX_NXT_AFTERMARKET', 'market_data_route': 'krx_nxt_integrated'}}
    result = evaluate_machine_entry_payload(snapshot=data, payload=payload, cutoff_ms=int(NOW.timestamp()*1000))
    assert result['action'] == 'SOURCE_UNAVAILABLE'
    assert result['reason'] == 'machine_payload_market_route_missing_or_conflicting'
    payload['ai_market_snapshot_v1']['effective_venue'] = 'KRX_NXT_INTEGRATED'
    payload['ai_market_snapshot_v1'].pop('market_data_route')
    assert evaluate_machine_entry_payload(snapshot=data, payload=payload, cutoff_ms=int(NOW.timestamp()*1000))['action'] == 'SOURCE_UNAVAILABLE'


@pytest.mark.parametrize('payload', [None, [], {'ai_market_snapshot_v1': ['invalid']}])
def test_malformed_machine_route_source_returns_gap_without_fallback(payload):
    from src.trading.market.main_entry_micro_window import evaluate_machine_entry_payload
    result = evaluate_machine_entry_payload(snapshot=snapshot(NOW), payload=payload, cutoff_ms=int(NOW.timestamp()*1000))
    assert result['action'] == 'SOURCE_UNAVAILABLE'
    assert result['reason'] == 'machine_payload_market_route_missing_or_conflicting'
