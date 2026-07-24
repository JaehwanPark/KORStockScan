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

    assert snapshot["ai_input_preflight_v1"]["position_reconciled"] is False


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
