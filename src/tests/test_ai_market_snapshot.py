import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.scalping import ai_market_snapshot as mod

KST = ZoneInfo("Asia/Seoul")


def _ws(
    now_ts,
    *,
    suffix="",
    route="krx_only",
    code="005930",
    effective_venue="",
):
    item = f"{code}{suffix}"
    return {
        "curr": 10000,
        "best_bid": 9990,
        "best_ask": 10000,
        "last_realtime_type_ts": {"0B": now_ts - 0.1, "0D": now_ts - 0.2},
        "last_realtime_type_item": {"0B": item, "0D": item},
        "last_realtime_type_market_suffix": {
            "0B": suffix,
            "0D": suffix,
        },
        "last_realtime_type_market_route": {
            "0B": route,
            "0D": route,
        },
        "last_realtime_type_effective_venue": {
            "0B": effective_venue,
            "0D": effective_venue,
        },
    }


def _candle(
    *,
    age_sec=1.0,
    rest_route="KRX",
    ws_route="krx_only",
    request_code="005930",
):
    return {
        "schema": "session_candle_source_v1",
        "request_code": request_code,
        "rest_route": rest_route,
        "ws_route": ws_route,
        "latest_bar_age_sec": age_sec,
        "source_quality": {"status": "fresh_consistent", "blockers": []},
    }


def _nxt_integrated_candle():
    candle = _candle(
        rest_route="_NX",
        ws_route="krx_nxt_integrated",
        request_code="005930_NX",
    )
    candle.update(
        {
            "route_equivalence_proven": True,
            "route_equivalence": "nxt_aftermarket_integrated_ws_to_nx_rest",
        }
    )
    candle["source_quality"]["route_equivalence_proof"] = {
        "proven": True,
        "proof_session": "nxt_aftermarket",
        "krx_regular_closed_by_clock": True,
        "required_rest_suffix": "_NX",
        "required_ws_suffix": "_AL",
        "required_ws_route": "krx_nxt_integrated",
    }
    return candle


def test_krx_snapshot_uses_exact_per_type_provenance():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["source_allowed"] is True
    assert preflight["venue_consistent"] is True
    assert snapshot["realtime_type_provenance"]["0B"]["item"] == "005930"
    assert snapshot["sources"]["program"]["value"] is None
    assert snapshot["sources"]["program"]["missing_reason"] == "program_source_missing"
    assert (
        mod.ai_market_snapshot_log_fields(snapshot)[
            "ai_market_snapshot_missing_as_zero"
        ]
        is False
    )


def test_program_source_uses_event_driven_freshness_and_explicit_wait_reason():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    waiting_ws = _ws(now)
    waiting_ws["program_subscription_requested_at"] = now - 5
    waiting = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=waiting_ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    observed_ws = _ws(now)
    observed_ws["received_types"] = {"0B", "0D", "0w"}
    observed_ws["last_realtime_type_ts"]["0w"] = now - 30
    observed_ws["last_realtime_type_market_suffix"]["0w"] = ""
    observed_ws["last_realtime_type_market_route"]["0w"] = "krx_only"
    observed_ws["prog_net_qty"] = 0
    observed = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=observed_ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )
    stale_ws = dict(observed_ws)
    stale_ws["last_realtime_type_ts"] = dict(observed_ws["last_realtime_type_ts"])
    stale_ws["last_realtime_type_ts"]["0w"] = now - 61
    stale = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=stale_ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    assert waiting["sources"]["program"]["value"] is None
    assert waiting["sources"]["program"]["missing_reason"] == (
        "program_0w_awaiting_first_observation"
    )
    assert observed["sources"]["program"]["quality"] == "fresh"
    assert observed["sources"]["program"]["freshness_limit_ms"] == 60_000.0
    assert observed["sources"]["program"]["value"]["net_qty"] == 0
    assert stale["sources"]["program"]["value"] is None
    assert stale["sources"]["program"]["missing_reason"] == "program_source_stale"
    assert "program" in stale["ai_input_preflight_v1"]["missing_sources"]
    assert stale["ai_input_preflight_v1"]["status"] == "partial"


def test_historical_session_gap_does_not_block_fresh_decision_window():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    candle = _candle()
    candle["source_quality"].update(
        {
            "decision_window": {
                "status": "fresh_consistent",
                "horizon_minutes": 60,
                "missing_bar_count": 0,
                "blockers": [],
            },
            "session_integrity": {
                "status": "blocked",
                "missing_bar_count": 30,
                "blockers": ["consecutive_bar_gap"],
            },
        }
    )

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=candle,
        now_ts=now,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["source_allowed"] is True
    assert "candle_source_quality" not in preflight["source_blockers"]


def test_krx_snapshot_selects_candle_route_partition_without_mixing_0b_0d():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ws = _ws(now)
    ws["curr"] = 9900
    ws["last_realtime_type_item"] = {
        "0B": "005930",
        "0D": "005930_AL",
    }
    ws["last_realtime_type_market_suffix"] = {"0B": "", "0D": "_AL"}
    ws["last_realtime_type_market_route"] = {
        "0B": "krx_only",
        "0D": "krx_nxt_integrated",
        "0w": "krx_only",
    }
    ws["last_realtime_type_market_suffix"]["0w"] = ""
    ws["last_realtime_type_ts"]["0w"] = now - 0.3
    ws["received_types"] = {"0B", "0D", "0w"}
    ws["last_prog_update_ts"] = now - 0.3
    ws["prog_net_qty"] = 123
    ws["realtime_type_snapshots_by_route"] = {
        "_AL|krx_nxt_integrated": {
            "0B": {
                "observed_epoch": now - 0.1,
                "item": "005930_AL",
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
                "effective_venue": "",
                "current_price": 10100,
            },
            "0D": {
                "observed_epoch": now - 0.2,
                "item": "005930_AL",
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
                "effective_venue": "",
                "orderbook": {
                    "asks": [{"price": 10100, "volume": 100}],
                    "bids": [{"price": 10090, "volume": 200}],
                },
            },
        }
    }
    candle = _candle(
        rest_route="_AL",
        ws_route="krx_nxt_integrated",
        request_code="005930_AL",
    )
    candle["ws_suffix"] = "_AL"

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=candle,
        now_ts=now,
    )

    assert snapshot["route_partition"] == {
        "used": True,
        "reason": "candle_route_exact_0b_0d_partition",
        "selected_key": "_AL|krx_nxt_integrated",
        "excluded_optional_sources": ["program_route_mismatch"],
    }
    assert snapshot["realtime_type_provenance"]["0B"]["item"] == "005930_AL"
    assert snapshot["sources"]["current_price"]["value"] == 10100
    assert snapshot["sources"]["bbo"]["value"] == {
        "best_bid": 10090,
        "best_ask": 10100,
    }
    assert snapshot["integrated_sor_route_proven"] is True
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True
    assert snapshot["sources"]["program"]["value"] is None
    assert snapshot["sources"]["program"]["missing_reason"] == "program_source_missing"
    assert (
        "realtime_type_route_conflict"
        not in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_route_partition_never_reuses_other_route_price_or_bbo_when_missing():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ws = _ws(now)
    ws.update(
        {
            "curr": 9990,
            "best_bid": 9980,
            "best_ask": 9990,
            "orderbook": {
                "asks": [{"price": 9990, "volume": 100}],
                "bids": [{"price": 9980, "volume": 100}],
            },
            "realtime_type_snapshots_by_route": {
                "_AL|krx_nxt_integrated": {
                    "0B": {
                        "observed_epoch": now - 0.1,
                        "item": "005930_AL",
                        "market_suffix": "_AL",
                        "market_route": "krx_nxt_integrated",
                        "effective_venue": "",
                        "current_price": 0,
                    },
                    "0D": {
                        "observed_epoch": now - 0.1,
                        "item": "005930_AL",
                        "market_suffix": "_AL",
                        "market_route": "krx_nxt_integrated",
                        "effective_venue": "",
                        "orderbook": {},
                    },
                }
            },
        }
    )
    candle = _candle(
        rest_route="_AL",
        ws_route="krx_nxt_integrated",
        request_code="005930_AL",
    )
    candle["ws_suffix"] = "_AL"

    selected, partition = mod._route_partitioned_ws_view(ws, candle)

    assert partition["used"] is True
    assert selected["curr"] == 0
    assert selected["best_bid"] == 0
    assert selected["best_ask"] == 0
    assert selected["orderbook"] == {}


def test_route_partition_status_requires_executable_price_and_bbo():
    now = datetime(2026, 8, 4, 9, 15, tzinfo=KST).timestamp()
    ws = {
        "realtime_type_snapshots_by_route": {
            "_AL|krx_nxt_integrated": {
                "0B": {
                    "observed_epoch": now - 0.1,
                    "market_suffix": "_AL",
                    "market_route": "krx_nxt_integrated",
                    "current_price": 10_000,
                },
                "0D": {
                    "observed_epoch": now - 0.1,
                    "market_suffix": "_AL",
                    "market_route": "krx_nxt_integrated",
                    "orderbook": {},
                },
            }
        }
    }

    status = mod.route_realtime_partition_status(
        ws,
        suffix="_AL",
        route="krx_nxt_integrated",
        now_ts=now,
    )

    assert status["ready"] is False
    assert status["status"] == "unusable"
    assert "0d_executable_bbo_missing_or_invalid" in status["blockers"]


def test_program_source_uses_ws_0w_canonical_fields_and_timestamp():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ws = _ws(now)
    ws["received_types"] = {"0B", "0D", "0w"}
    ws["last_realtime_type_ts"]["0w"] = now - 0.4
    ws["last_realtime_type_market_suffix"]["0w"] = ""
    ws["last_realtime_type_market_route"]["0w"] = "krx_regular"
    ws.update(
        {
            "prog_net_qty": 0,
            "prog_delta_qty": 0,
            "prog_net_amt": 0,
            "prog_delta_amt": 0,
            "prog_buy_qty": 120,
            "prog_sell_qty": 120,
        }
    )

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    program = snapshot["sources"]["program"]
    assert program["source"] == "ws_0w"
    assert program["quality"] == "fresh"
    assert program["value"]["net_qty"] == 0
    assert program["value"]["buy_qty"] == 120
    assert "program" not in snapshot["ai_input_preflight_v1"]["missing_sources"]


def test_shared_broker_snapshot_preserves_verified_zero_for_entry_context():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    mod.publish_broker_account_snapshot(
        inventory=[],
        successful_exchanges={"KRX", "NXT"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now - 1,
    )
    try:
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="entry_screen",
            ws_data=_ws(now),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=_candle(),
            now_ts=now,
        )
    finally:
        mod._clear_broker_account_snapshot_for_tests()

    assert snapshot["sources"]["broker_position"]["value"] == 0
    assert snapshot["sources"]["broker_position"]["verification"] == "verified_absent"
    assert snapshot["sources"]["open_orders"]["value"] == {
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    assert snapshot["sources"]["open_orders"]["verification"] == "verified_zero"
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is True
    assert "broker_position" not in snapshot["ai_input_preflight_v1"]["missing_sources"]
    assert "open_orders" not in snapshot["ai_input_preflight_v1"]["missing_sources"]


def test_shared_pre_fill_zero_is_not_used_as_holding_reconciliation():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    mod.publish_broker_account_snapshot(
        inventory=[],
        successful_exchanges={"KRX"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now - 1,
    )
    try:
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="holding_flow",
            ws_data=_ws(now),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=_candle(),
            position={"status": "HOLDING", "buy_qty": 1, "remaining_qty": 1},
            now_ts=now,
            require_position_reconciliation=True,
        )
    finally:
        mod._clear_broker_account_snapshot_for_tests()

    assert snapshot["sources"]["broker_position"]["quality"] == "missing"
    assert snapshot["sources"]["open_orders"]["quality"] == "missing"
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is False
    assert (
        "broker_position_or_open_orders_unreconciled"
        in snapshot["ai_input_preflight_v1"]["blockers"]
    )


def test_shared_positive_inventory_is_used_for_active_holding_reconciliation():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    mod.publish_broker_account_snapshot(
        inventory=[{"code": "005930", "qty": 1}],
        successful_exchanges={"KRX"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now - 1,
    )
    try:
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="holding_flow",
            ws_data=_ws(now),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=_candle(),
            position={"status": "HOLDING", "buy_qty": 1, "remaining_qty": 1},
            now_ts=now,
            require_position_reconciliation=True,
        )
    finally:
        mod._clear_broker_account_snapshot_for_tests()

    assert snapshot["sources"]["broker_position"]["value"] == 1
    assert snapshot["sources"]["broker_position"]["verification"] == "present"
    assert snapshot["sources"]["broker_position"]["quality"] == "fresh"
    assert snapshot["sources"]["open_orders"]["value"] == {
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    assert snapshot["sources"]["open_orders"]["verification"] == "verified_zero"
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is True
    assert (
        "broker_position_or_open_orders_unreconciled"
        not in snapshot["ai_input_preflight_v1"]["blockers"]
    )


def test_optional_holding_score_marks_stale_broker_snapshot_partial_advisory():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    mod.publish_broker_account_snapshot(
        inventory=[{"code": "005930", "qty": 1}],
        successful_exchanges={"KRX"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now - 61,
    )
    try:
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="holding_score",
            ws_data=_ws(now),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=_candle(),
            position={
                "status": "HOLDING",
                "buy_qty": 1,
                "remaining_qty": 1,
                "buy_price": 10_000,
            },
            now_ts=now,
            require_position_reconciliation=False,
        )
    finally:
        mod._clear_broker_account_snapshot_for_tests()

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is True
    assert preflight["status"] == "partial"
    assert preflight["blockers"] == []
    assert preflight["quality_warnings"] == [
        "broker_position_or_open_orders_stale_advisory"
    ]
    assert mod.ai_market_snapshot_log_fields(snapshot)[
        "ai_input_preflight_quality_warnings"
    ] == ["broker_position_or_open_orders_stale_advisory"]


def test_submit_authority_stage_enforces_reconciliation_without_caller_flag():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score_submit_authority",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position={
            "status": "HOLDING",
            "buy_qty": 1,
            "remaining_qty": 1,
            "buy_price": 10_000,
        },
        now_ts=now,
        require_position_reconciliation=False,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is False
    assert preflight["position_reconciliation_mode"] == "broker_account"
    assert "broker_position_or_open_orders_unreconciled" in preflight["blockers"]
    assert preflight["quality_warnings"] == []


def test_optional_holding_score_marks_quantity_mismatch_partial_advisory():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    mod.publish_broker_account_snapshot(
        inventory=[{"code": "005930", "qty": 2}],
        successful_exchanges={"KRX"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now - 1,
    )
    try:
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="holding_score",
            ws_data=_ws(now),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=_candle(),
            position={
                "status": "HOLDING",
                "buy_qty": 1,
                "remaining_qty": 1,
                "buy_price": 10_000,
            },
            now_ts=now,
        )
    finally:
        mod._clear_broker_account_snapshot_for_tests()

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is True
    assert preflight["position_reconciled"] is True
    assert preflight["status"] == "partial"
    assert preflight["quality_warnings"] == [
        "broker_position_quantity_mismatch_advisory"
    ]


def test_optional_holding_score_marks_broker_route_mismatch_partial_advisory():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="scalping_holding_score",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="NXT",
        candle_context=_candle(),
        position={
            "status": "HOLDING",
            "buy_qty": 1,
            "remaining_qty": 1,
            "broker_holding_qty": 1,
            "broker_snapshot_at": now - 1,
            "open_buy_qty": 0,
            "open_sell_qty": 0,
        },
        now_ts=now,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is True
    assert preflight["position_reconciled"] is True
    assert preflight["status"] == "partial"
    assert preflight["quality_warnings"] == [
        "broker_route_venue_mismatch_or_missing_advisory"
    ]


def test_shared_positive_inventory_quantity_mismatch_blocks_holding_preflight():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    mod.publish_broker_account_snapshot(
        inventory=[{"code": "005930", "qty": 2}],
        successful_exchanges={"KRX"},
        open_orders=[],
        open_orders_request_succeeded=True,
        captured_at=now - 1,
    )
    try:
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="holding_flow",
            ws_data=_ws(now),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=_candle(),
            position={"status": "HOLDING", "buy_qty": 1, "remaining_qty": 1},
            now_ts=now,
            require_position_reconciliation=True,
        )
    finally:
        mod._clear_broker_account_snapshot_for_tests()

    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is True
    assert snapshot["ai_input_preflight_v1"]["allowed"] is False
    assert (
        "broker_position_quantity_mismatch"
        in snapshot["ai_input_preflight_v1"]["blockers"]
    )


def test_simulation_book_reconciles_holding_flow_without_broker_inventory():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position={
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_qty": 1,
            "buy_price": 10_000,
            "simulation_book": "scalp_ai_buy_all",
            "simulation_owner": "ScalpAiBuyAllLiveSimulator0511",
            "scalp_live_simulator": True,
            "sim_record_id": "sim-005930-1",
            "decision_authority": "sim_observation_only",
            "simulated_order": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        now_ts=now,
        require_position_reconciliation=True,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is True
    assert preflight["position_reconciled"] is False
    assert preflight["position_authority_reconciled"] is True
    assert preflight["position_reconciliation_mode"] == "simulation_book"
    assert preflight["simulation_position_reconciled"] is True
    assert "broker_position_or_open_orders_unreconciled" not in preflight["blockers"]


def test_simulation_position_missing_authority_remains_fail_closed():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position={
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_qty": 1,
            "buy_price": 10_000,
            "simulation_book": "scalp_ai_buy_all",
            "simulation_owner": "ScalpAiBuyAllLiveSimulator0511",
            "scalp_live_simulator": True,
            "sim_record_id": "sim-005930-1",
            "simulated_order": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        now_ts=now,
        require_position_reconciliation=True,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is False
    assert preflight["position_authority_reconciled"] is False
    assert preflight["simulation_position_reconciled"] is False
    assert "broker_position_or_open_orders_unreconciled" in preflight["blockers"]


def test_unknown_simulation_book_cannot_bypass_broker_reconciliation():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position={
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_qty": 1,
            "buy_price": 10_000,
            "simulation_book": "unknown_simulation_book",
            "simulation_owner": "unknown_owner",
            "scalp_live_simulator": True,
            "sim_record_id": "sim-005930-1",
            "decision_authority": "sim_observation_only",
            "simulated_order": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        now_ts=now,
        require_position_reconciliation=True,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["allowed"] is False
    assert preflight["simulation_position_reconciled"] is False
    assert "broker_position_or_open_orders_unreconciled" in preflight["blockers"]


def test_disabled_preflight_does_not_read_runtime_artifact(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", raising=False)
    monkeypatch.setattr(
        mod,
        "runtime_preflight_artifact_status",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("disabled preflight must not read report artifact")
        ),
    )
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["runtime_preflight_artifact"]["status"] == "not_required"


def test_future_or_missing_realtime_identity_is_not_fresh():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    future_ws = _ws(now)
    future_ws["last_realtime_type_ts"]["0B"] = now + 2
    future = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=future_ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )
    missing_item_ws = _ws(now)
    missing_item_ws["last_realtime_type_item"]["0D"] = ""
    missing_item = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=missing_item_ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    assert future["realtime_type_provenance"]["0B"]["quality"] == "future"
    assert future["ai_input_preflight_v1"]["source_allowed"] is False
    assert missing_item["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "realtime_type_item_missing"
        in missing_item["ai_input_preflight_v1"]["source_blockers"]
    )


def test_post_fetch_capture_clock_avoids_false_future_without_weakening_guard():
    cycle_started_at = datetime(2026, 7, 24, 9, 31, 49, tzinfo=KST).timestamp()
    snapshot_captured_at = cycle_started_at + 6.0
    ws = _ws(
        snapshot_captured_at,
        suffix="_AL",
        route="krx_nxt_integrated",
        code="011200",
        effective_venue="KRX",
    )
    common = {
        "stock_code": "011200",
        "decision_stage": "entry_screen",
        "ws_data": ws,
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "broker_route": "SOR",
        "candle_context": _candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
            request_code="011200_AL",
        ),
    }

    stale_loop_clock = mod.build_ai_market_snapshot(
        **common,
        now_ts=cycle_started_at,
    )
    post_fetch_clock = mod.build_ai_market_snapshot(
        **common,
        now_ts=snapshot_captured_at,
    )
    truly_future_ws = _ws(
        snapshot_captured_at,
        suffix="_AL",
        route="krx_nxt_integrated",
        code="011200",
        effective_venue="KRX",
    )
    truly_future_ws["last_realtime_type_ts"]["0B"] = snapshot_captured_at + 2.0
    truly_future = mod.build_ai_market_snapshot(
        **{**common, "ws_data": truly_future_ws},
        now_ts=snapshot_captured_at,
    )

    assert (
        "current_price_future"
        in stale_loop_clock["ai_input_preflight_v1"]["source_blockers"]
    )
    assert post_fetch_clock["ai_input_preflight_v1"]["source_allowed"] is True
    assert not {
        "bbo_future",
        "current_price_future",
        "tape_future",
    }.intersection(post_fetch_clock["ai_input_preflight_v1"]["source_blockers"])
    assert truly_future["realtime_type_provenance"]["0B"]["quality"] == "future"
    assert truly_future["ai_input_preflight_v1"]["source_allowed"] is False


def test_item_suffix_conflict_is_blocked():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ws = _ws(now, suffix="_NX", route="nxt_only")
    ws["last_realtime_type_item"]["0D"] = "005930_AL"

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=ws,
        effective_venue="NXT",
        session_bucket="nxt_regular_overlap",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "item_suffix_conflict" in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_post_probe_does_not_require_candle_but_keeps_fresh_market_sources():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="post_probe",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        now_ts=now,
    )

    assert snapshot["required_sources"] == ["current_price", "bbo", "tape"]
    assert snapshot["sources"]["candle"]["value"] is None
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True


def test_nxt_overlap_rejects_ambiguous_integrated_route():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="NXT",
        session_bucket="nxt_regular_overlap",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "nxt_overlap_exact_source_required"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_krx_rejects_integrated_source_without_event_venue_proof():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "krx_integrated_event_venue_unproven"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )
    assert snapshot["effective_venue"] == "KRX"
    assert snapshot["market_data_route"] == "krx_nxt_integrated"
    assert snapshot["underlying_event_venue"] is None
    assert snapshot["underlying_event_venue_source"] == "not_provided"
    assert snapshot["integrated_sor_route_proven"] is False


def test_fresh_rest_bbo_reanchors_quote_only_without_waiving_tape_or_venue():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    ws["last_realtime_type_ts"] = {"0B": now - 10.0, "0D": now - 10.0}
    ws.update(
        {
            "curr": 10020,
            "best_bid": 10010,
            "best_ask": 10020,
            "market_data_effective_price_source": "ka10004_rest_orderbook",
            "market_data_freshness_state": "rest_enriched",
            "market_data_effective_quote_observed_epoch": now - 0.1,
            "market_data_effective_quote_request_code": "005930_AL",
        }
    )

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
            request_code="005930_AL",
        ),
        now_ts=now,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert snapshot["sources"]["current_price"]["source"] == ("ka10004_rest_orderbook")
    assert snapshot["sources"]["current_price"]["quality"] == "fresh"
    assert snapshot["sources"]["bbo"]["quality"] == "fresh"
    assert snapshot["executable_quote_reanchor"] == {
        "applied": True,
        "source": "ka10004_rest_orderbook",
        "freshness_state": "rest_enriched",
        "observed_epoch": now - 0.1,
        "request_code": "005930_AL",
        "authority": "quote_and_current_price_only",
        "tape_or_event_venue_authority": False,
    }
    assert "current_price_stale" not in preflight["source_blockers"]
    assert "bbo_stale" not in preflight["source_blockers"]
    assert "tape_stale" in preflight["source_blockers"]
    assert "realtime_type_provenance_missing_or_stale" in preflight["source_blockers"]
    assert preflight["source_allowed"] is False
    assert snapshot["underlying_event_venue"] is None
    assert snapshot["venue_attribution_allowed"] is False
    log_fields = mod.ai_market_snapshot_log_fields(snapshot)
    assert log_fields["ai_market_snapshot_executable_quote_reanchor_applied"] is True
    assert (
        log_fields["ai_market_snapshot_executable_quote_reanchor_authority"]
        == "quote_and_current_price_only"
    )
    assert (
        log_fields[
            "ai_market_snapshot_executable_quote_reanchor_tape_or_event_venue_authority"
        ]
        is False
    )


def test_holding_sor_accepts_exact_integrated_execution_route_without_inventing_venue():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    position = {
        "buy_qty": 1,
        "buy_price": 10000,
        "broker_holding_qty": 1,
        "broker_snapshot_at": now - 1,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
        ),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["source_allowed"] is True
    assert preflight["venue_consistent"] is True
    assert snapshot["underlying_event_venue"] is None
    assert snapshot["integrated_sor_route_proven"] is True
    assert (
        snapshot["integrated_sor_route_proof"]
        == "holding_sor_integrated_execution_view"
    )
    assert snapshot["integrated_sor_execution_view_only"] is True
    assert snapshot["venue_attribution_allowed"] is False
    assert (
        snapshot["venue_attribution_reason"]
        == "integrated_sor_execution_view_not_event_venue"
    )


def test_holding_sor_active_position_prefers_authoritative_broker_quantity():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    common = {
        "stock_code": "005930",
        "decision_stage": "holding_flow",
        "ws_data": _ws(now, suffix="_AL", route="krx_nxt_integrated"),
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "broker_route": "SOR",
        "candle_context": _candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
        ),
        "now_ts": now,
    }

    broker_holding = mod.build_ai_market_snapshot(
        **common,
        position={
            "remaining_qty": 0,
            "buy_qty": 1,
            "buy_price": 10000,
            "broker_holding_qty": 1,
        },
    )
    broker_flat = mod.build_ai_market_snapshot(
        **common,
        position={
            "remaining_qty": 1,
            "buy_qty": 1,
            "buy_price": 10000,
            "broker_holding_qty": 0,
        },
    )

    assert broker_holding["integrated_sor_route_proven"] is True
    assert broker_flat["integrated_sor_route_proven"] is False


def test_integrated_sor_execution_view_opens_regular_entry_ai_only():
    position = {"buy_qty": 1, "buy_price": 10000}
    regular_now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    entry = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(regular_now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
        ),
        position=position,
        now_ts=regular_now,
    )
    premarket_now = datetime(2026, 7, 23, 8, 59, tzinfo=KST).timestamp()
    premarket_mislabeled = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(premarket_now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
        ),
        position=position,
        now_ts=premarket_now,
    )

    assert entry["integrated_sor_route_proven"] is True
    assert entry["integrated_sor_route_proof"] == (
        "entry_sor_integrated_execution_view"
    )
    assert entry["underlying_event_venue"] is None
    assert entry["underlying_event_venue_source"] == "not_provided"
    assert entry["integrated_sor_execution_view_only"] is True
    assert entry["venue_attribution_allowed"] is False
    assert entry["ai_input_preflight_v1"]["source_allowed"] is True
    assert premarket_mislabeled["integrated_sor_route_proven"] is False
    assert premarket_mislabeled["ai_input_preflight_v1"]["source_allowed"] is False


def test_integrated_sor_execution_view_accepts_runtime_entry_context_schema():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    candle = {
        **_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
            request_code="005930_AL",
        ),
        "schema": "entry_candle_context_v1",
    }

    for stage in ("entry_context", "gatekeeper"):
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage=stage,
            ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
            effective_venue="KRX",
            session_bucket="krx_regular",
            broker_route="SOR",
            candle_context=candle,
            now_ts=now,
        )

        assert snapshot["integrated_sor_route_proven"] is True
        assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True
        assert snapshot["venue_attribution_allowed"] is False
        log_fields = mod.ai_market_snapshot_log_fields(snapshot)
        assert (
            log_fields["ai_market_snapshot_integrated_sor_execution_view_only"] is True
        )
        assert log_fields["ai_market_snapshot_venue_attribution_allowed"] is False


def test_integrated_sor_execution_view_rejects_nxt_event_and_post_probe():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    common = {
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "krx_regular",
        "broker_route": "SOR",
        "candle_context": _candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
            request_code="005930_AL",
        ),
        "now_ts": now,
    }
    nxt_event = mod.build_ai_market_snapshot(
        **common,
        decision_stage="entry_context",
        ws_data=_ws(
            now,
            suffix="_AL",
            route="krx_nxt_integrated",
            effective_venue="NXT",
        ),
    )
    post_probe = mod.build_ai_market_snapshot(
        **common,
        decision_stage="post_probe",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
    )

    for snapshot in (nxt_event, post_probe):
        assert snapshot["integrated_sor_route_proven"] is False
        assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
        assert snapshot["venue_attribution_allowed"] is False


def test_integrated_sor_post_probe_accepts_only_frozen_filled_probe_execution_view():
    now = datetime(2026, 8, 4, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="post_probe",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        position={
            "status": "HOLDING",
            "buy_qty": 1,
            "buy_price": 10000,
            "entry_execution_broker_route": "SOR",
            "entry_split_probe_bundle_id": "005930-probe-test",
            "entry_split_probe_fill_price": 10000,
            "entry_split_probe_filled_at": now - 0.2,
        },
        now_ts=now,
    )

    assert snapshot["integrated_sor_route_proven"] is True
    assert snapshot["integrated_sor_route_proof"] == (
        "post_probe_sor_integrated_execution_view"
    )
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True
    assert snapshot["venue_attribution_allowed"] is False


def test_integrated_sor_holding_requires_matching_al_candle_route():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position={"buy_qty": 1, "buy_price": 10000},
        now_ts=now,
    )

    assert snapshot["integrated_sor_route_proven"] is False
    assert (
        "krx_integrated_event_venue_unproven"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_integrated_sor_holding_rejects_cross_symbol_candle_context():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
            request_code="000660_AL",
        ),
        position={"buy_qty": 1, "buy_price": 10000},
        now_ts=now,
    )

    assert snapshot["integrated_sor_route_proven"] is False
    assert (
        "krx_integrated_event_venue_unproven"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_minute_candle_has_interval_aware_freshness_without_weakening_ws():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    fresh_candle = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(age_sec=55.0),
        now_ts=now,
    )
    stale_candle = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(age_sec=91.0),
        now_ts=now,
    )
    stale_ws_data = _ws(now)
    stale_ws_data["last_realtime_type_ts"] = {
        "0B": now - 3.1,
        "0D": now - 3.1,
    }
    stale_ws = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=stale_ws_data,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(age_sec=55.0),
        now_ts=now,
    )

    assert fresh_candle["sources"]["candle"]["quality"] == "fresh"
    assert fresh_candle["sources"]["candle"]["freshness_limit_ms"] == 90000.0
    assert fresh_candle["ai_input_preflight_v1"]["source_allowed"] is True
    assert stale_candle["sources"]["candle"]["quality"] == "stale"
    assert "candle_stale" in stale_candle["ai_input_preflight_v1"]["source_blockers"]
    assert stale_ws["sources"]["current_price"]["quality"] == "stale"
    assert stale_ws["sources"]["bbo"]["quality"] == "stale"


def test_nxt_aftermarket_accepts_integrated_route_with_event_and_clock_proof():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(
            now,
            suffix="_AL",
            route="krx_nxt_integrated",
            effective_venue="NXT",
        ),
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True


def test_nxt_aftermarket_rejects_integrated_route_without_event_venue_proof():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_score",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "nxt_aftermarket_source_unproven"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_nxt_aftermarket_accepts_bounded_integrated_execution_view_without_attribution():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_context",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
        broker_route="NXT",
        candle_context=_nxt_integrated_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True
    assert snapshot["ai_input_preflight_v1"]["venue_consistent"] is True
    assert snapshot["nxt_integrated_execution_view_proven"] is True
    assert snapshot["nxt_integrated_execution_view_only"] is True
    assert snapshot["underlying_event_venue"] is None
    assert snapshot["venue_attribution_allowed"] is False
    assert (
        snapshot["venue_attribution_reason"]
        == "nxt_integrated_execution_view_not_event_venue"
    )
    fields = mod.ai_market_snapshot_log_fields(snapshot)
    assert fields["ai_market_snapshot_nxt_integrated_execution_view_proven"] is True


def test_nxt_integrated_execution_view_rejects_unproven_candle_route():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    candle = _candle(
        rest_route="_NX",
        ws_route="krx_nxt_integrated",
        request_code="005930_NX",
    )
    candle.update(
        {
            "route_equivalence_proven": True,
            "route_equivalence": "nxt_aftermarket_integrated_ws_to_nx_rest",
        }
    )
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_context",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
        broker_route="NXT",
        candle_context=candle,
        now_ts=now,
    )

    assert snapshot["nxt_integrated_execution_view_proven"] is False
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "nxt_aftermarket_source_unproven"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_nxt_integrated_execution_view_rejects_wrong_broker_route_and_clock():
    for now, broker_route in (
        (datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp(), "SOR"),
        (datetime(2026, 7, 23, 15, 30, tzinfo=KST).timestamp(), "NXT"),
    ):
        snapshot = mod.build_ai_market_snapshot(
            stock_code="005930",
            decision_stage="entry_context",
            ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
            effective_venue="NXT",
            session_bucket="nxt_aftermarket",
            broker_route=broker_route,
            candle_context=_nxt_integrated_candle(),
            now_ts=now,
        )

        assert snapshot["nxt_integrated_execution_view_proven"] is False
        assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
        assert (
            "nxt_aftermarket_source_unproven"
            in snapshot["ai_input_preflight_v1"]["source_blockers"]
        )


def test_nxt_holding_accepts_integrated_execution_view_only_with_position():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    common = {
        "stock_code": "005930",
        "decision_stage": "holding_score",
        "ws_data": _ws(now, suffix="_AL", route="krx_nxt_integrated"),
        "effective_venue": "NXT",
        "session_bucket": "nxt_aftermarket",
        "broker_route": "NXT",
        "candle_context": _nxt_integrated_candle(),
        "now_ts": now,
    }
    active = mod.build_ai_market_snapshot(
        **common,
        position={"buy_qty": 1, "buy_price": 10000},
    )
    flat = mod.build_ai_market_snapshot(**common, position={})

    assert active["nxt_integrated_execution_view_proven"] is True
    assert active["ai_input_preflight_v1"]["source_allowed"] is True
    assert active["venue_attribution_allowed"] is False
    assert flat["nxt_integrated_execution_view_proven"] is False
    assert flat["ai_input_preflight_v1"]["source_allowed"] is False


def test_nxt_integrated_execution_view_does_not_bypass_stale_realtime_sources():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    ws = _ws(now, suffix="_AL", route="krx_nxt_integrated")
    ws["last_realtime_type_ts"] = {"0B": now - 4.0, "0D": now - 4.0}
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_context",
        ws_data=ws,
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
        broker_route="NXT",
        candle_context=_nxt_integrated_candle(),
        now_ts=now,
    )

    assert snapshot["nxt_integrated_execution_view_proven"] is False
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "realtime_type_provenance_missing_or_stale"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )
    assert "bbo_stale" in snapshot["ai_input_preflight_v1"]["source_blockers"]
    assert "current_price_stale" in snapshot["ai_input_preflight_v1"]["source_blockers"]
    assert "tape_stale" in snapshot["ai_input_preflight_v1"]["source_blockers"]


def test_nxt_aftermarket_rejects_suffix_route_mismatch():
    now = datetime(2026, 7, 23, 18, 0, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_NX", route="krx_nxt_integrated"),
        effective_venue="NXT",
        session_bucket="nxt_aftermarket",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "market_suffix_route_conflict"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_premarket_normalizes_venue_and_accepts_proven_integrated_route():
    now = datetime(2026, 7, 23, 8, 30, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="SOR",
        session_bucket="premarket_krx_like",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["effective_venue"] == "PREMARKET_KRX_LIKE"
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True


def test_premarket_accepts_exact_nxt_subscription_as_krx_like_cohort():
    now = datetime(2026, 7, 23, 8, 30, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_NX", route="nxt_only"),
        effective_venue="NXT",
        session_bucket="premarket_krx_like",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["effective_venue"] == "PREMARKET_KRX_LIKE"
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True


def test_premarket_rejects_route_outside_actual_time_window():
    now = datetime(2026, 7, 23, 9, 1, tzinfo=KST).timestamp()
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_NX", route="nxt_only"),
        effective_venue="NXT",
        session_bucket="premarket_krx_like",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "premarket_actual_route_proof_missing"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_legacy_sor_venue_input_normalizes_to_krx_without_inventing_event_venue():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ambiguous = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now, suffix="_AL", route="krx_nxt_integrated"),
        effective_venue="SOR",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )
    assert ambiguous["effective_venue"] == "KRX"
    assert ambiguous["venue_resolution"] == "legacy_route_value_normalized_by_session"
    assert ambiguous["market_data_route"] == "krx_nxt_integrated"
    assert ambiguous["underlying_event_venue"] is None
    assert ambiguous["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "krx_integrated_event_venue_unproven"
        in ambiguous["ai_input_preflight_v1"]["source_blockers"]
    )


def test_krx_position_authority_rejects_direct_krx_route_under_sor_contract():
    now = datetime(2026, 7, 23, 14, 0, tzinfo=KST).timestamp()
    position = {
        "broker_holding_qty": 3,
        "buy_price": 10000,
        "broker_snapshot_at": now - 1,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="KRX",
        candle_context=_candle(),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["source_allowed"] is False
    assert preflight["position_reconciled"] is True
    assert preflight["broker_route_matches_venue"] is False
    assert "broker_route_venue_mismatch_or_missing" in preflight["source_blockers"]


def test_krx_position_authority_accepts_normal_sor_broker_route():
    now = datetime(2026, 7, 23, 14, 0, tzinfo=KST).timestamp()
    position = {
        "broker_holding_qty": 3,
        "buy_price": 10000,
        "broker_snapshot_at": now - 1,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(
            now,
            suffix="_AL",
            route="krx_nxt_integrated",
            effective_venue="KRX",
        ),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(
            rest_route="_AL",
            ws_route="krx_nxt_integrated",
        ),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["source_allowed"] is True
    assert preflight["position_reconciled"] is True
    assert preflight["broker_route_matches_venue"] is True
    assert snapshot["broker_route"] == "SOR"
    assert snapshot["market_data_route"] == "krx_nxt_integrated"
    assert snapshot["underlying_event_venue"] is None
    assert snapshot["underlying_event_venue_source"] == "not_provided"
    assert snapshot["integrated_sor_execution_view_only"] is True
    assert snapshot["venue_attribution_allowed"] is False


def test_broker_route_contract_is_exact_per_scalping_cohort():
    assert (
        mod._broker_route_matches_cohort(
            broker_route="SOR",
            venue_cohort="KRX",
            session="krx_regular",
        )
        is True
    )
    assert (
        mod._broker_route_matches_cohort(
            broker_route="KRX",
            venue_cohort="KRX",
            session="krx_regular",
        )
        is False
    )
    assert (
        mod._broker_route_matches_cohort(
            broker_route="NXT",
            venue_cohort="PREMARKET_KRX_LIKE",
            session="premarket_krx_like",
        )
        is True
    )
    assert (
        mod._broker_route_matches_cohort(
            broker_route="SOR",
            venue_cohort="PREMARKET_KRX_LIKE",
            session="premarket_krx_like",
        )
        is False
    )
    assert (
        mod._broker_route_matches_cohort(
            broker_route="NXT",
            venue_cohort="NXT",
            session="nxt_entry_window",
        )
        is True
    )


def test_broker_snapshot_timestamp_expires_even_if_legacy_age_is_zero():
    now = datetime(2026, 7, 23, 14, 0, tzinfo=KST).timestamp()
    position = {
        "broker_holding_qty": 3,
        "broker_snapshot_at": now - 61,
        "broker_snapshot_age_sec": 0,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    assert snapshot["sources"]["broker_position"]["quality"] == "stale"
    assert snapshot["sources"]["open_orders"]["quality"] == "stale"
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is False


def test_broker_snapshot_uses_position_reconciliation_ttl_not_ws_ttl():
    now = datetime(2026, 7, 23, 14, 0, tzinfo=KST).timestamp()
    position = {
        "broker_holding_qty": 3,
        "broker_snapshot_at": now - 30,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
        "broker_position_verification": "present",
        "broker_open_orders_verification": "verified_zero",
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    assert snapshot["sources"]["broker_position"]["quality"] == "fresh"
    assert snapshot["sources"]["open_orders"]["quality"] == "fresh"
    assert snapshot["sources"]["broker_position"]["freshness_limit_ms"] == 60_000.0
    assert snapshot["sources"]["open_orders"]["freshness_limit_ms"] == 60_000.0
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is True


def test_future_broker_snapshot_is_not_reconciled():
    now = datetime(2026, 7, 23, 14, 0, tzinfo=KST).timestamp()
    position = {
        "broker_holding_qty": 3,
        "broker_snapshot_at": now + 2,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="holding_flow",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="SOR",
        candle_context=_candle(),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    assert snapshot["sources"]["broker_position"]["quality"] == "future"
    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is False


def test_overnight_rejects_broker_route_mismatch():
    now = datetime(2026, 7, 23, 15, 20, tzinfo=KST).timestamp()
    position = {
        "broker_holding_qty": 3,
        "broker_snapshot_at": now - 1,
        "open_buy_qty": 0,
        "open_sell_qty": 0,
    }
    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="overnight",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        broker_route="NXT",
        candle_context=_candle(),
        position=position,
        now_ts=now,
        require_position_reconciliation=True,
    )

    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is False
    assert (
        "broker_route_venue_mismatch_or_missing"
        in snapshot["ai_input_preflight_v1"]["source_blockers"]
    )


def test_nested_orderbook_levels_are_valid_bbo_sources():
    now = datetime(2026, 7, 23, 10, 0, tzinfo=KST).timestamp()
    ws = _ws(now)
    ws.pop("best_bid")
    ws.pop("best_ask")
    ws["orderbook"] = {
        "bids": [{"price": 9990, "qty": 10}],
        "asks": [{"price": 10000, "qty": 10}],
    }

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=ws,
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["sources"]["bbo"]["quality"] == "fresh"
    assert snapshot["ai_input_preflight_v1"]["source_allowed"] is True


def test_required_runtime_artifact_blocks_runtime_but_not_source_evidence(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE", "2026-07-24")
    monkeypatch.setattr(mod, "_PREFLIGHT_REPORT_DIR", tmp_path)
    (tmp_path / "entry_context_intraday_probe_2026-07-24.json").write_text(
        json.dumps({"venue_preflight_matrix": {"overall_status": "not_ready"}}),
        encoding="utf-8",
    )
    now = datetime(2026, 7, 24, 10, 0, tzinfo=KST).timestamp()

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    preflight = snapshot["ai_input_preflight_v1"]
    assert preflight["source_allowed"] is True
    assert preflight["allowed"] is False
    assert "runtime_preflight_artifact_not_ready" in preflight["blockers"]


def test_ready_artifact_requires_a_new_process_handoff(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_REQUIRED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE", "2026-07-24")
    monkeypatch.setattr(mod, "_PREFLIGHT_REPORT_DIR", tmp_path)
    path = tmp_path / "entry_context_intraday_probe_2026-07-24.json"
    path.write_text(
        json.dumps({"venue_preflight_matrix": {"overall_status": "ready"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "_PROCESS_STARTED_AT", path.stat().st_mtime - 1)

    pending = mod.runtime_preflight_artifact_status()

    assert pending["ready"] is False
    assert pending["status"] == "ready_pending_restart"

    monkeypatch.setattr(mod, "_PROCESS_STARTED_AT", path.stat().st_mtime + 1)
    active = mod.runtime_preflight_artifact_status()

    assert active["ready"] is True
    assert active["status"] == "ready"


def test_operator_directed_promotion_can_open_exact_v2_preflight_only(
    monkeypatch,
):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "exact_v2")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE", "2026-07-29")
    monkeypatch.setattr(
        mod,
        "promotion_activation_state",
        lambda captured_at: {
            "active": True,
            "target_date": "2026-07-29",
            "promotion_mode": "operator_directed_full_promotion",
            "promotion_artifact": "/tmp/operator-directed-promotion.json",
            "promotion_sha256": "promotion-hash",
        },
    )

    status = mod.runtime_preflight_artifact_status(now_ts=1785285000.0)

    assert status["ready"] is True
    assert status["status"] == "ready_operator_directed_exact_v2"
    assert status["validation_gate_bypassed"] is True


def _baseline_payload():
    return {
        "schema": "ai_input_quality_baseline_v1",
        "policy_version": "baseline_v1",
        "status": "ready_baseline_v1",
        "allowed_runtime_apply": True,
        "runtime_effect": "protective_fail_closed_only",
        "can_open_order_authority": False,
        "can_relax_threshold": False,
        "can_change_provider": False,
        "observation_contract": {
            "decision_authority": "source_quality_fail_closed_only",
        },
    }


def test_baseline_mode_accepts_only_protective_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "baseline_v1")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_BASELINE_ARTIFACT_DATE", "2026-07-23")
    monkeypatch.setattr(mod, "_BASELINE_REPORT_DIR", tmp_path)
    path = tmp_path / "ai_input_quality_baseline_2026-07-23.json"
    path.write_text(json.dumps(_baseline_payload()), encoding="utf-8")
    monkeypatch.setattr(mod, "_PROCESS_STARTED_AT", path.stat().st_mtime + 1)

    status = mod.runtime_preflight_artifact_status()

    assert status["ready"] is True
    assert status["mode"] == "baseline_v1"
    assert status["status"] == "ready_baseline_v1"


def test_baseline_mode_rejects_artifact_that_can_open_authority(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "baseline_v1")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_BASELINE_ARTIFACT_DATE", "2026-07-23")
    monkeypatch.setattr(mod, "_BASELINE_REPORT_DIR", tmp_path)
    payload = _baseline_payload()
    payload["can_open_order_authority"] = True
    path = tmp_path / "ai_input_quality_baseline_2026-07-23.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(mod, "_PROCESS_STARTED_AT", path.stat().st_mtime + 1)

    status = mod.runtime_preflight_artifact_status()

    assert status["ready"] is False
    assert status["status"] == "baseline_contract_not_ready"


def test_unknown_runtime_preflight_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "unsafe_custom")

    assert mod.runtime_preflight_required() is True
    assert mod.runtime_preflight_artifact_status()["status"] == (
        "runtime_preflight_mode_invalid"
    )


def test_baseline_mode_keeps_fresh_exact_snapshot_source_gate(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "baseline_v1")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_BASELINE_ARTIFACT_DATE", "2026-07-23")
    monkeypatch.setattr(mod, "_BASELINE_REPORT_DIR", tmp_path)
    path = tmp_path / "ai_input_quality_baseline_2026-07-23.json"
    path.write_text(json.dumps(_baseline_payload()), encoding="utf-8")
    monkeypatch.setattr(mod, "_PROCESS_STARTED_AT", path.stat().st_mtime + 1)
    now = datetime(2026, 7, 24, 10, 0, tzinfo=KST).timestamp()

    snapshot = mod.build_ai_market_snapshot(
        stock_code="005930",
        decision_stage="entry_screen",
        ws_data=_ws(now),
        effective_venue="KRX",
        session_bucket="krx_regular",
        candle_context=_candle(),
        now_ts=now,
    )

    assert snapshot["runtime_preflight_mode"] == "baseline_v1"
    assert snapshot["ai_input_preflight_v1"]["allowed"] is True
    assert snapshot["runtime_preflight_artifact"]["status"] == "ready_baseline_v1"


def test_runtime_artifact_payload_is_cached_by_mtime(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE", "baseline_v1")
    monkeypatch.setenv("KORSTOCKSCAN_AI_INPUT_BASELINE_ARTIFACT_DATE", "2026-07-23")
    monkeypatch.setattr(mod, "_BASELINE_REPORT_DIR", tmp_path)
    path = tmp_path / "ai_input_quality_baseline_2026-07-23.json"
    path.write_text(json.dumps(_baseline_payload()), encoding="utf-8")
    monkeypatch.setattr(mod, "_PROCESS_STARTED_AT", path.stat().st_mtime + 1)
    mod._ARTIFACT_STATUS_CACHE.clear()
    original_read_text = Path.read_text
    calls = 0

    def counted_read_text(self, *args, **kwargs):
        nonlocal calls
        if self == path:
            calls += 1
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted_read_text)

    first = mod.runtime_preflight_artifact_status()
    second = mod.runtime_preflight_artifact_status()

    assert first == second
    assert calls == 1
