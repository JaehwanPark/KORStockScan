"""Retained research parity and owner receipt recovery; no live WS reader."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import json

from src.engine.bd_fbuy_accum_pre_scanner import _ws_machine_route_payload
from src.tests.test_machine_adaptive_exit_activation import OPEN
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.market.confirmation_window import build_confirmation_window
from src.trading.order.adaptive_exit.market_source import (
    MarketSourceGap,
    snapshot_payload_from_window,
)
from src.trading.order.adaptive_exit.runtime import OwnerSession

MS = int(OPEN.timestamp() * 1000)
pytest_plugins = ["src.tests.test_machine_adaptive_exit_enrollment"]


def projection(route="SOR", *, now_ms=MS):
    item = "005930" + {"SOR": "_AL", "KRX": "", "NXT": "_NX"}[route]
    depth, trades = [], []
    for seq, offset in enumerate((-1400, -1000, -500, 0), 1):
        common = dict(
            item=item,
            transport_epoch=16,
            route_sequence=seq,
            received_at_ms=now_ms + offset,
        )
        depth.append(
            common
            | dict(
                ask_levels=[dict(price=10010, quantity=100 if seq < 3 else 30)],
                bid_levels=[
                    dict(price=10000, quantity=100),
                    dict(price=9995, quantity=200),
                ],
            )
        )
        trades.append(common | dict(price=10010, volume=10, aggressor_side="BUY"))
    types = {
        kind: dict(
            item=item,
            transport_epoch=16,
            route_sequence=4,
            observed_epoch=now_ms / 1000,
            market_route=route,
            orderbook=dict(asks=depth[-1]["ask_levels"], bids=depth[-1]["bid_levels"]),
            trade_price=10010,
            trade_qty=10,
            aggressor_side="BUY",
        )
        for kind in ("0B", "0D")
    }
    # Exercise the real bounded producer, not an imagined adapter-only shape.
    routes = _ws_machine_route_payload(
        {
            "realtime_type_snapshots_by_route": {route: types},
            "recent_trade_ticks_by_route": {route: list(reversed(trades))},
            "recent_depth_ticks_by_route": {route: list(reversed(depth))},
        },
        now_ts=now_ms / 1000,
    )
    payload = dict(
        schema_version="kiwoom_ws_dashboard_snapshot_v1",
        decision_authority="source_quality_only",
        runtime_effect=False,
        generated_at_epoch=now_ms / 1000,
        machine_confirmation_input_contract=dict(
            schema="machine_entry_confirmation_ws_snapshot_v1",
            decision_authority="market_data_input_only_no_order_authority",
            exact_route_required=True,
            causal_past_only=True,
            runtime_effect=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
        ),
        stocks={"005930": {"machine_confirmation_routes": routes}},
    )
    # JSON consumers do not share the producer's in-memory dict aliases.
    return json.loads(json.dumps(payload))


def route_row(payload, route="SOR"):
    return payload["stocks"]["005930"]["machine_confirmation_routes"][route]


def test_shared_exit_support_calculation_and_research_hash_preserved():
    row = route_row(projection())
    feature = build_confirmation_window(
        depth_rows=row["recent_depth"],
        trade_rows=row["recent_trades"],
        item="005930_AL",
        epoch=16,
        checkpoint_at_ms=MS,
    )
    projected = row["recent_depth"][0]
    raw = deepcopy(projected)
    raw["local_receive_timestamp"] = datetime.fromtimestamp(
        MS / 1000, timezone.utc
    ).isoformat()
    raw["sequence_epoch"] = raw.pop("transport_epoch")
    raw["series_sequence"] = raw.pop("route_sequence")
    raw.pop("received_at_ms")
    raw["bid_levels"] = [
        [i, r["price"], r["quantity"]] for i, r in enumerate(raw["bid_levels"], 1)
    ]
    options = dict(
        feature=feature,
        scope_key="scope",
        position_epoch="position",
        observed_at_ms=MS,
        sequence=1,
    )
    old = snapshot_payload_from_window(depth=raw, **options)
    live = snapshot_payload_from_window(depth=projected, **options)
    assert old["source_hash"] == canonical_sha256({"depth": raw, "feature": feature})
    assert {k: v for k, v in old.items() if k != "source_hash"} == {
        k: v for k, v in live.items() if k != "source_hash"
    }
    assert old["supportive"] is True and old["improvement_bps"] == 0


def unavailable_snapshot(*args):
    raise MarketSourceGap("fixture_unavailable")


def test_source_gap_retains_target_and_reconciles_receipts(enrolled_owner, tmp_path):
    x = enrolled_owner
    assert x.propose()
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services,
        snapshot_loader=unavailable_snapshot,
    )
    x.machine.run_once(OPEN)
    session = OwnerSession.from_payload(x.raw())
    assert session.driver.orders.phase == "TARGET_WORKING" and session.manager_required
    assert x.wire.calls and not x.wire.writes
    assert "adaptive_exit_market_source_gap" in str(x.machine._state)


def test_market_absence_does_not_hide_owned_target_full_fill(enrolled_owner, tmp_path):
    x = enrolled_owner
    assert x.propose()
    x.machine.adaptive_exit_services = replace(
        x.machine.adaptive_exit_services,
        snapshot_loader=unavailable_snapshot,
    )
    x.wire.detailed[0].update(cntr_qty="10", ord_remnq="0")
    x.wire.current = []
    x.machine.run_once(OPEN)
    # The first pass durably accounts the exact full fill before its independent
    # terminal/cost handoff. Market availability cannot conceal those 10 shares.
    if x.owner == "widget":
        history = x.machine._state["symbols"]["005930"]["adaptive_exit_history"][-1]
        session = OwnerSession.from_payload(history["sessions"]["entry"])
        assert history["enrollments"]["entry"]
        assert history["terminals"]["entry"]["realized_pnl_status"] != "reconciled"
    else:
        session = OwnerSession.from_payload(x.raw())
    assert session.driver.orders.target_filled_qty == 10
    assert session.driver.orders.open_qty == 0 and not x.wire.writes
