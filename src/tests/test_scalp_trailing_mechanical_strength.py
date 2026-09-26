"""M1 source identity, state transitions and completed-path replay contracts."""

from __future__ import annotations

from src.engine.scalping.trailing_mechanical_strength import (
    CONFIG_DEFAULTS, classify_ws_history, normalize_config, _ofi,
)
from src.engine.scalping.exit_safety_monitor import ScalpExitSafetyMonitor
import threading
import json
import pytest
from copy import deepcopy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.engine.scalping.trailing_mechanical_policy import (
    CLASSIFIER_VERSION, DEFAULTS, START_MARKETS, classifier_hash,
    market_values_hash, value_hash,
)
from src.engine.scalping.trailing_mechanical_replay import (
    _classifier_variant_rows, prepare_position, replay_vector, summarize_mechanical,
)
from src.tests.test_scalp_trailing_four_axis_replay import _path
from src.tests.test_scalp_trailing_start_replay import _at
from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit


def _depth(seq: int, at: int, bid_qty: int, ask_qty: int) -> dict:
    return {"item": "123456", "transport_epoch": 1, "route_sequence": seq,
            "received_at_ms": at,
            "bid_levels": [{"price": 100, "quantity": bid_qty}],
            "ask_levels": [{"price": 101, "quantity": ask_qty}]}


def _trade(seq: int, at: int, side: str, qty: int = 10) -> dict:
    return {"item": "123456", "transport_epoch": 1, "route_sequence": seq,
            "received_at_ms": at, "price": 10050, "volume": qty,
            "aggressor_side": side,
            "aggressor_source": "kiwoom_0b_signed_trade_volume",
            "aggressor_quality": ("signed_trade_volume_positive" if side == "BUY"
                                  else "signed_trade_volume_negative")}


def _snapshot(depths: list[dict], trades: list[dict]) -> dict:
    return {"last_realtime_type_item": {"0D": "123456", "0B": "123456"},
            "last_realtime_type_market_route": {"0D": "KRX", "0B": "KRX"},
            "last_realtime_type_market_suffix": {"0D": "KRX", "0B": "KRX"},
            "market_data_transport_epoch": 1,
            "recent_depth_ticks_by_route": {"KRX|KRX": list(reversed(depths))},
            "recent_trade_ticks_by_route": {"KRX|KRX": list(reversed(trades))}}


def test_m1_promotes_retains_and_requires_two_adverse_updates():
    d = [_depth(1, 1000, 10, 10), _depth(2, 1100, 20, 5),
         _depth(3, 1200, 5, 20), _depth(4, 1300, 4, 22)]
    t = [_trade(1, 1100, "BUY"), _trade(2, 1200, "SELL", 20),
         _trade(3, 1300, "SELL", 20)]
    baseline, state = classify_ws_history(_snapshot(d[:1], []), None,
                                          now_ms=1000, max_quote_age_ms=700)
    assert baseline.state == "UNKNOWN"
    first, state = classify_ws_history(_snapshot(d[:2], t[:1]), state,
                                       now_ms=1100, max_quote_age_ms=700)
    assert first.state == "STRONG"
    held, state = classify_ws_history(_snapshot(d[:3], t[:2]), state,
                                      now_ms=1200, max_quote_age_ms=700)
    assert held.state == "STRONG"
    weak, state = classify_ws_history(_snapshot(d, t), state,
                                      now_ms=1300, max_quote_age_ms=700)
    assert weak.state == "WEAK"
    expired, _ = classify_ws_history(_snapshot(d, t), state,
                                     now_ms=2501, max_quote_age_ms=700)
    assert expired.state == "UNKNOWN"


def test_market_config_recomputes_trade_window_and_strict_support_boundaries():
    depths = [_depth(1, 1000, 10, 10), _depth(2, 2000, 20, 5)]
    trades = [_trade(1, 1200, "BUY", 10)]
    _, base = classify_ws_history(_snapshot(depths[:1], []), None,
                                  now_ms=1000, max_quote_age_ms=1500)
    strong, _ = classify_ws_history(_snapshot(depths, trades), base,
                                    now_ms=2000, max_quote_age_ms=1500)
    assert strong.state == "STRONG"


    short_config = {**CONFIG_DEFAULTS, "trade_window_ms": 500}
    _, short_base = classify_ws_history(_snapshot(depths[:1], []), None,
                                        now_ms=1000, max_quote_age_ms=1500,
                                        config=short_config)
    short, _ = classify_ws_history(
        _snapshot(depths, trades), short_base, now_ms=2000, max_quote_age_ms=1500,
        config=short_config,
    )
    assert short.state == "UNKNOWN"
    qty_config = {**CONFIG_DEFAULTS, "strong_signed_qty_min": 10}
    _, qty_base = classify_ws_history(_snapshot(depths[:1], []), None,
                                      now_ms=1000, max_quote_age_ms=1500,
                                      config=qty_config)
    exact_qty, _ = classify_ws_history(
        _snapshot(depths, trades), qty_base, now_ms=2000, max_quote_age_ms=1500,
        config=qty_config,
    )
    assert exact_qty.state == "WEAK"
    with pytest.raises(ValueError, match="classifier_config_keys_invalid"):
        normalize_config({"trade_window_ms": 500})
    with pytest.raises(ValueError, match="type_invalid"):
        normalize_config({**CONFIG_DEFAULTS, "strong_queue_min": "0.1"})


def test_verified_runtime_vector_is_pinned_until_bootstrap_hash_changes(monkeypatch):
    from src.engine.scalping.trailing_mechanical_policy import (
        MARKET_ENV_KEYS, VECTOR_SHA_ENV_KEY, market_values_hash,
        runtime_policy_vector_snapshot,
    )

    vector = {market: dict(DEFAULTS) for market in START_MARKETS}
    vector["REGULAR"]["SCALP_TRAILING_START_PCT"] = 0.5
    key = MARKET_ENV_KEYS["SCALP_TRAILING_START_PCT"]["REGULAR"]
    monkeypatch.setenv(key, "0.5")
    monkeypatch.setenv(VECTOR_SHA_ENV_KEY, market_values_hash(vector))
    values, _, _, digest = runtime_policy_vector_snapshot(DEFAULTS)
    assert values["REGULAR"]["SCALP_TRAILING_START_PCT"] == 0.5
    assert digest == market_values_hash(vector)
    monkeypatch.setenv(key, "0.4")
    assert runtime_policy_vector_snapshot(DEFAULTS)[0]["REGULAR"][
        "SCALP_TRAILING_START_PCT"] == 0.5
    monkeypatch.setenv(VECTOR_SHA_ENV_KEY, market_values_hash({
        market: dict(DEFAULTS) for market in START_MARKETS
    }))
    assert runtime_policy_vector_snapshot(DEFAULTS)[0]["REGULAR"][
        "SCALP_TRAILING_START_PCT"] == 0.4


def test_candidate_window_uses_raw_receipt_times_not_logged_one_second_sum():
    segment = ("123456", 1, "KRX|KRX", "REGULAR")
    at = 2_000
    prepared = {
        "classifier_observations": [{
            "_classifier_segment": segment, "sequence": 2, "at_ms": at,
            "queue_imbalance": 0.3, "ofi_proxy": 0.2,
            "signed_trade_qty": 10, "trade_gap": None,
            "trade_receipts": [
                {"received_at_ms": 1200, "side": "BUY", "qty": 20},
                {"received_at_ms": 1900, "side": "SELL", "qty": 10},
            ],
        }],
        "rows": [{"classifier_item": "123456", "classifier_transport_epoch": 1,
                  "classifier_route_key": "KRX|KRX", "classifier_market": "REGULAR",
                  "classifier_quote_sequence": 2, "classifier_state": "STRONG"}],
    }
    incumbent = {market: dict(CONFIG_DEFAULTS) for market in START_MARKETS}
    short = {market: dict(values) for market, values in incumbent.items()}
    short["REGULAR"]["trade_window_ms"] = 500
    assert _classifier_variant_rows(prepared, incumbent)[0]["classifier_state"] == "STRONG"
    assert _classifier_variant_rows(prepared, short)[0]["classifier_state"] == "WEAK"


def test_m1_source_gaps_never_promote():
    depths = [_depth(1, 1000, 10, 10), _depth(3, 1100, 20, 5)]
    _, old = classify_ws_history(_snapshot(depths[:1], []), None,
                                 now_ms=1000, max_quote_age_ms=700)
    decision, _ = classify_ws_history(_snapshot(depths, [_trade(1, 1100, "BUY")]),
                                      old, now_ms=1100, max_quote_age_ms=700)
    assert decision.state != "STRONG"
    no_signed, _ = classify_ws_history(_snapshot(depths, []), None,
                                       now_ms=1100, max_quote_age_ms=700)
    assert no_signed.state == "UNKNOWN"
    mixed_route = _snapshot(depths, [_trade(1, 1100, "BUY")])
    mixed_route["last_realtime_type_market_route"]["0B"] = "NXT"
    route_decision, _ = classify_ws_history(mixed_route, old,
                                            now_ms=1100, max_quote_age_ms=700)
    assert route_decision.state == "UNKNOWN"


def test_market_or_route_switch_starts_unknown_baseline_without_old_strength():
    depths = [_depth(1, 1000, 10, 10), _depth(2, 1100, 20, 5)]
    trade = _trade(1, 1100, "BUY")
    _, state = classify_ws_history(_snapshot(depths[:1], []), None,
                                   now_ms=1000, max_quote_age_ms=700,
                                   market="REGULAR")
    strong, state = classify_ws_history(_snapshot(depths, [trade]), state,
                                        now_ms=1100, max_quote_age_ms=700,
                                        market="REGULAR")
    assert strong.state == "STRONG"
    new_route = _snapshot([_depth(1, 1200, 30, 5)],
                          [_trade(1, 1200, "BUY")])
    new_route["last_realtime_type_market_route"] = {"0D": "NXT", "0B": "NXT"}
    new_route["recent_depth_ticks_by_route"] = {
        "KRX|NXT": new_route["recent_depth_ticks_by_route"].pop("KRX|KRX")
    }
    new_route["recent_trade_ticks_by_route"] = {
        "KRX|NXT": new_route["recent_trade_ticks_by_route"].pop("KRX|KRX")
    }
    route_baseline, state = classify_ws_history(
        new_route, state, now_ms=1200, max_quote_age_ms=700,
        market="REGULAR",
    )
    assert route_baseline.state == "UNKNOWN"
    assert state["route_key"] == "KRX|NXT"
    market_baseline, state = classify_ws_history(
        new_route, state, now_ms=1200, max_quote_age_ms=700,
        market="INTEGRATED_AFTERMARKET",
    )
    assert market_baseline.state == "UNKNOWN"
    assert state["market"] == "INTEGRATED_AFTERMARKET"


def test_m1_trade_window_capacity_gap_is_unknown():
    depths = [_depth(1, 1000, 10, 10), _depth(2, 1200, 20, 5)]
    _, old = classify_ws_history(_snapshot(depths[:1], []), None,
                                 now_ms=1000, max_quote_age_ms=700)
    trades = [_trade(i + 1, 1100 + i, "BUY") for i in range(120)]
    decision, _ = classify_ws_history(_snapshot(depths, trades), old,
                                      now_ms=1220, max_quote_age_ms=700)
    assert decision.state == "UNKNOWN"
    assert decision.reason == "trade_window_capacity_gap"


def test_m1_expired_source_cannot_revive_strong_without_fresh_book_support():
    depths = [_depth(1, 1000, 10, 10), _depth(2, 1100, 20, 5),
              _depth(3, 2100, 25, 4), _depth(4, 2200, 30, 3)]
    trades = [_trade(1, 1100, "BUY"), _trade(2, 2100, "BUY"),
              _trade(3, 2200, "BUY")]
    _, state = classify_ws_history(_snapshot(depths[:1], []), None,
                                   now_ms=1000, max_quote_age_ms=700)
    strong, state = classify_ws_history(_snapshot(depths[:2], trades[:1]), state,
                                        now_ms=1100, max_quote_age_ms=700)
    assert strong.state == "STRONG"
    expired, state = classify_ws_history(_snapshot(depths[:2], trades[:1]), state,
                                         now_ms=1900, max_quote_age_ms=700)
    assert expired.state == "UNKNOWN"
    fresh_baseline, state = classify_ws_history(
        _snapshot(depths[:3], trades[:2]), state,
        now_ms=2100, max_quote_age_ms=700,
    )
    assert fresh_baseline.state != "STRONG"
    renewed, _ = classify_ws_history(_snapshot(depths, trades), state,
                                     now_ms=2200, max_quote_age_ms=700)
    assert renewed.state == "STRONG"


def test_batched_quotes_can_hide_the_first_weak_crossing():
    depths = [_depth(1, 1000, 10, 10), _depth(2, 1100, 20, 5),
              _depth(3, 1200, 25, 4)]
    for row, bid in zip(depths, (10070, 10050, 10090)):
        row["bid_levels"][0]["price"] = bid
        row["ask_levels"][0]["price"] = bid + 10
    trades = [_trade(1, 1100, "SELL", 10), _trade(2, 1200, "BUY", 30)]
    _, previous = classify_ws_history(_snapshot(depths[:1], []), None,
                                      now_ms=1000, max_quote_age_ms=700)
    batch, _ = classify_ws_history(_snapshot(depths, trades), previous,
                                   now_ms=1200, max_quote_age_ms=700)
    assert len(batch.new_observations) == 2
    first, latest = batch.new_observations
    assert first["state"] == "WEAK" and latest["state"] == "STRONG"
    first_signal = evaluate_trailing_take_profit(
        peak_price=10100, executable_bid=first["best_bid"],
        peak_profit_pct=1.0, start_pct=.6, strong=False,
        weak_limit_pct=.4, strong_limit_pct=.8,
    )
    latest_signal = evaluate_trailing_take_profit(
        peak_price=10100, executable_bid=latest["best_bid"],
        peak_profit_pct=1.0, start_pct=.6, strong=True,
        weak_limit_pct=.4, strong_limit_pct=.8,
    )
    assert first_signal.triggered and not latest_signal.triggered


@pytest.mark.parametrize("second_offset_ms", [100, 200])
def test_runtime_replays_batched_0d_first_crossing_before_latest_quote(
    monkeypatch, second_offset_ms,
):
    from src.engine import sniper_state_handlers as handlers

    base = int(_at("2026-09-25 10:00:00") * 1000)
    depths = [_depth(1, base, 10, 10), _depth(2, base + 100, 20, 5),
              _depth(3, base + second_offset_ms, 25, 4)]
    for row, bid in zip(depths, (10070, 10050, 10090)):
        row["bid_levels"][0]["price"] = bid
        row["ask_levels"][0]["price"] = bid + 10
    trades = [_trade(1, base + 100, "SELL", 10),
              _trade(2, base + second_offset_ms, "BUY", 30)]
    _, previous = classify_ws_history(_snapshot(depths[:1], []), None,
                                      now_ms=base, max_quote_age_ms=700)
    batch, _ = classify_ws_history(_snapshot(depths, trades), previous,
                                   now_ms=base + second_offset_ms, max_quote_age_ms=700)
    monkeypatch.setattr(handlers, "_scalp_trailing_values_for_evaluation",
                        lambda at: (dict(DEFAULTS), "REGULAR"))
    monkeypatch.setattr(handlers, "_scalp_trailing_arm_was_latched",
                        lambda stock: False)
    monkeypatch.setattr(handlers, "_scalp_trailing_latch_arm",
                        lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "calculate_net_profit_rate",
                        lambda buy, price: (price / buy - 1) * 100)
    stock = {"id": 1, "code": "123456", "buy_price": 10000,
             "scalp_trailing_event_peak_state": {
                 "position_key": "record:1", "peak_price": 10100,
                 "last_quote_at_ms": base,
             }}
    fields = {"classifier_quote_received_at_ms": base + second_offset_ms,
              "classifier_item": "123456", "classifier_transport_epoch": 1,
              "_classifier_observations": batch.new_observations}
    handlers._scalp_trailing_replay_observed_quotes_safe(
        stock, "123456", fields, peak_price=10100, buy_price=10000,
        executable_bid=10090, bid_source="fresh_ws_executable_bid",
        quote_fields={"quote_consistency_state": "ok"},
        observed_at=(base + second_offset_ms) / 1000,
    )
    replay = json.loads(fields["classifier_event_replay"])
    assert not fields.get("classifier_event_time_gap")
    assert replay[0]["raw_triggered"] and not replay[1]["raw_triggered"]
    first = stock["scalp_trailing_first_crossing"]
    assert first["threshold_key"] == "SCALP_TRAILING_LIMIT_WEAK"
    assert first["at_epoch"] == (base + 100) / 1000


def test_runtime_route_baseline_advances_event_clock_without_source_gap(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    base = int(_at("2026-09-25 10:00:00") * 1000)
    stock = {"id": 1, "code": "123456", "buy_price": 10000,
             "scalp_trailing_event_peak_state": {
                 "position_key": "record:1", "peak_price": 10100,
                 "last_quote_at_ms": base,
             }}
    fields = {"classifier_reason": "position_or_transport_baseline",
              "classifier_quote_received_at_ms": base + 100,
              "_classifier_observations": ()}
    handlers._scalp_trailing_replay_observed_quotes_safe(
        stock, "123456", fields, peak_price=10100, buy_price=10000,
        executable_bid=10090, bid_source="fresh_ws_executable_bid",
        quote_fields={"quote_consistency_state": "ok"},
        observed_at=(base + 100) / 1000,
    )
    assert stock["scalp_trailing_event_peak_state"]["last_quote_at_ms"] == base + 100
    assert not fields.get("classifier_event_time_gap")


def test_m1_replay_excludes_legacy_score_and_uses_three_numeric_axes():
    position, _ = _path(score=80, strong=True, limit=0.8)
    vector = {market: dict(DEFAULTS) for market in START_MARKETS}
    fields = position["timeline"][-1]["fields"]
    fields.update({
        "classifier_version": CLASSIFIER_VERSION,
        "classifier_sha256": classifier_hash(),
        "classifier_state": "STRONG",
        "classifier_item": "123456",
        "classifier_transport_epoch": 1,
        "classifier_route_key": "KRX|KRX",
        "classifier_market": "REGULAR",
        "classifier_quote_sequence": 1,
        "classifier_quote_received_at_ms": int(fields["evaluation_at_epoch"] * 1000 - 100),
        "classifier_new_event_count": 1,
        "tuning_mechanical_bin_version": "start_0p1_width_0p1_mechanical_v1",
        "scalp_trailing_policy_values": dict(DEFAULTS),
        "scalp_trailing_policy_value_sha256": value_hash(DEFAULTS),
        "scalp_trailing_market_values": vector,
        "scalp_trailing_market_values_sha256": market_values_hash(vector),
        "trailing_start_pct": DEFAULTS["SCALP_TRAILING_START_PCT"],
    })
    fields["classifier_event_replay"] = [{
        "sequence": 1,
        "at_ms": fields["classifier_quote_received_at_ms"],
        "peak_price": 10100,
        "peak_profit_pct": 0.6,
        "executable_bid": 10050,
        "executable_bid_qty": 20,
        "classifier_state": "STRONG",
        "market": "REGULAR",
        "start_pct": DEFAULTS["SCALP_TRAILING_START_PCT"],
        "raw_limit_pct": 0.8,
    }]
    position["timeline"].insert(-1, {
        "stage": "scalp_trailing_mechanical_input",
        "fields": {
            "classifier_version": CLASSIFIER_VERSION,
            "classifier_sha256": classifier_hash(),
            "classifier_position_key": "record:1",
            "classifier_item": "123456",
            "classifier_transport_epoch": 1,
            "classifier_route_key": "KRX|KRX",
            "classifier_market": "REGULAR",
            "classifier_events": [{
                "sequence": 1,
                "at_ms": fields["classifier_quote_received_at_ms"],
                "state": "STRONG",
                "touch": [10050, 20, 10060, 5],
                "previous_touch": [10050, 10, 10060, 10],
                "ofi_proxy": 0.75,
                "queue_imbalance": 0.6,
                "signed_trade_qty": 10,
                "trade_peak_price_since_prior_depth": 0,
                "trade_peak_receipts": [],
                "trade_receipts": [{"sequence": 1,
                                    "received_at_ms": fields["classifier_quote_received_at_ms"],
                                    "side": "BUY", "qty": 10,
                                    "source": "kiwoom_0b_signed_trade_volume",
                                    "quality": "signed_trade_volume_positive"}],
            }],
        },
    })
    prepared = prepare_position(position)
    assert prepared["source_gap"] is None
    baseline = replay_vector(position, prepared, vector,
                             actual_exit_rule="scalp_hard_stop_pct")
    assert baseline["paired_delta_pnl_krw"] == 0
    changed = {market: dict(values) for market, values in vector.items()}
    changed["REGULAR"]["SCALP_TRAILING_LIMIT_STRONG"] = 0.4
    candidate = replay_vector(position, prepared, changed,
                              actual_exit_rule="scalp_hard_stop_pct")
    assert candidate["status"] == "modeled_earlier_full_sell"
    report = summarize_mechanical([position], [{"record_id": "1", "exit_rule": "scalp_hard_stop_pct",
                                               "rec_date": "2026-09-25"}], population_complete=True)
    assert "SCALP_TRAILING_STRONG_AI_SCORE" not in report.get("grid", {})
    assert report["research_candidate"] is None
    research = report["classifier_parameter_research"]
    assert research["status"] == "research_only_no_live_candidate"
    assert research["markets"]["REGULAR"]["scenarios"]
    assert research["research_candidate"] is None
    closed_loop = report["classifier_policy_research"]
    assert closed_loop["candidate_count"] >= 18
    assert any(
        len(row["changed_axes"]) == 2
        and "SCALP_TRAILING_LIMIT_STRONG" in row["changed_axes"]
        and row["values"]["REGULAR"]["SCALP_TRAILING_LIMIT_STRONG"]
            != vector["REGULAR"]["SCALP_TRAILING_LIMIT_STRONG"]
        for row in closed_loop["candidates"].values()
    )
    tampered = deepcopy(position)
    receipt = tampered["timeline"][-2]["fields"]["classifier_events"][0]["trade_receipts"][0]
    receipt["source"] = "price_change_inferred"
    assert prepare_position(tampered)["source_gap"] == "source_gap_classifier_journal_trade_receipt"
    gapped = deepcopy(position)
    gapped["timeline"][-1]["fields"]["classifier_event_time_gap"] = True
    assert prepare_position(gapped)["source_gap"] == (
        "source_gap_classifier_event_time_crossing_unresolved"
    )
    missing_route = deepcopy(position)
    missing_route["timeline"][-1]["fields"]["classifier_route_key"] = None
    assert prepare_position(missing_route)["source_gap"] == (
        "source_gap_mechanical_source_identity"
    )


def _batched_position():
    position, vector = _path(score=50, strong=False, peak=10100,
                             bid=10070, limit=0.4)
    vector = {market: {key: values[key] for key in DEFAULTS}
              for market, values in vector.items()}
    first = position["timeline"][-1]["fields"]
    second = deepcopy(_path(score=50, strong=False, peak=10100,
                            bid=10090, limit=0.4)[0]["timeline"][-1]["fields"])
    base = int(first["evaluation_at_epoch"] * 1000)
    for row in (first, second):
        row.update({
            "classifier_version": CLASSIFIER_VERSION,
            "classifier_sha256": classifier_hash(),
            "classifier_item": "123456",
            "classifier_transport_epoch": 1,
            "classifier_route_key": "KRX|KRX",
            "classifier_market": "REGULAR",
            "tuning_mechanical_bin_version": "start_0p1_width_0p1_mechanical_v1",
            "scalp_trailing_policy_values": dict(DEFAULTS),
            "scalp_trailing_policy_value_sha256": value_hash(DEFAULTS),
            "scalp_trailing_market_values": vector,
            "scalp_trailing_market_values_sha256": market_values_hash(vector),
        })
    first.update({"classifier_state": "UNKNOWN", "classifier_quote_sequence": 1,
                  "classifier_quote_received_at_ms": base,
                  "classifier_new_event_count": 0, "classifier_event_replay": []})
    second.update({
        "event_sequence": 2, "evaluation_at_epoch": (base + 200) / 1000,
        "bid_source_received_at_epoch": (base + 200) / 1000,
        "classifier_state": "STRONG", "classifier_quote_sequence": 3,
        "classifier_quote_received_at_ms": base + 200,
        "classifier_new_event_count": 2,
        "selected_width_from_latch": True,
        "first_crossing": {
            "classifier_version": CLASSIFIER_VERSION,
            "threshold_key": "SCALP_TRAILING_LIMIT_WEAK",
            "at_epoch": (base + 100) / 1000,
        },
        "classifier_event_replay": [
            {"sequence": 2, "at_ms": base + 100, "peak_price": 10100,
             "peak_profit_pct": 0.6, "executable_bid": 10050,
             "executable_bid_qty": 20, "classifier_state": "WEAK",
             "market": "REGULAR", "start_pct": 0.6, "raw_limit_pct": 0.4},
            {"sequence": 3, "at_ms": base + 200, "peak_price": 10100,
             "peak_profit_pct": 0.6, "executable_bid": 10090,
             "executable_bid_qty": 25, "classifier_state": "STRONG",
             "market": "REGULAR", "start_pct": 0.6, "raw_limit_pct": 0.8},
        ],
    })
    touch1 = (10070, 10, 10080, 10)
    touch2 = (10050, 20, 10060, 5)
    touch3 = (10090, 25, 10100, 4)
    observations = []
    for sequence, at_ms, previous, touch, side, qty, state in (
        (2, base + 100, touch1, touch2, "SELL", 10, "WEAK"),
        (3, base + 200, touch2, touch3, "BUY", 30, "STRONG"),
    ):
        observations.append({
            "sequence": sequence, "at_ms": at_ms, "state": state,
            "touch": list(touch), "previous_touch": list(previous),
            "ofi_proxy": _ofi(previous, touch),
            "queue_imbalance": (touch[1] - touch[3]) / (touch[1] + touch[3]),
            "signed_trade_qty": qty if side == "BUY" else -qty,
            "trade_receipts": [{
                "sequence": sequence - 1, "received_at_ms": at_ms,
                "side": side, "qty": qty,
                "source": "kiwoom_0b_signed_trade_volume",
                "quality": ("signed_trade_volume_positive" if side == "BUY"
                            else "signed_trade_volume_negative"),
            }],
            "trade_peak_price_since_prior_depth": touch[0],
            "trade_peak_receipts": [{
                "sequence": sequence - 1, "received_at_ms": at_ms,
                "price": touch[0],
            }],
        })
    position["timeline"].insert(-1, {
        "stage": "scalp_trailing_mechanical_input",
        "fields": {
            "classifier_version": CLASSIFIER_VERSION,
            "classifier_sha256": classifier_hash(),
            "classifier_position_key": "record:1",
            "classifier_item": "123456",
            "classifier_transport_epoch": 1,
            "classifier_route_key": "KRX|KRX",
            "classifier_market": "REGULAR",
            "classifier_events": observations,
        },
    })
    position["timeline"].append({"stage": "scalp_trailing_input_transition",
                                 "fields": second})
    position["exit_signal"] = {"timestamp": (base + 200) / 1000}
    return position, vector, base


def test_completed_position_replays_first_weak_crossing_inside_batched_quotes():
    position, vector, base = _batched_position()
    prepared = prepare_position(position)
    assert prepared["source_gap"] is None
    assert [row["classifier_quote_sequence"] for row in prepared["rows"]] == [1, 2, 3]
    outcome = replay_vector(position, prepared, vector,
                            actual_exit_rule="scalp_trailing_take_profit")
    assert outcome["status"] == "same_observed_exit"
    assert outcome["first_trigger_at_epoch"] == (base + 100) / 1000
    tampered = deepcopy(position)
    tampered["timeline"][-3]["fields"]["classifier_events"][0][
        "trade_peak_receipts"][0]["price"] = 99999
    assert prepare_position(tampered)["source_gap"] == (
        "source_gap_classifier_journal_trade_peak"
    )
    tampered_crossing = deepcopy(position)
    tampered_crossing["timeline"][-1]["fields"]["first_crossing"][
        "at_epoch"] = (base + 200) / 1000
    assert prepare_position(tampered_crossing)["source_gap"] == (
        "source_gap_first_crossing_replay_mismatch"
    )


def test_three_market_censored_variant_does_not_erase_other_common_support():
    base, _, base_ms = _batched_position()
    trades, outcomes = [], []
    for ident in range(1, 121):
        hour, market = ((8, "PREMARKET"), (9, "REGULAR"),
                        (17, "INTEGRATED_AFTERMARKET"))[(ident - 1) % 3]
        delta = (datetime(2026, 9, 25, hour, 30,
                          tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
                 - base_ms / 1000)

        def moved(value, key=""):
            if isinstance(value, dict):
                return {name: moved(item, name) for name, item in value.items()}
            if isinstance(value, list):
                return [moved(item, key) for item in value]
            if "market" in key and value == "REGULAR":
                return market
            if isinstance(value, (int, float)) and (
                key.endswith("_at_epoch") or key in {"at_epoch", "timestamp"}
            ):
                return value + delta
            if isinstance(value, (int, float)) and (
                key.endswith("_at_ms") or key in {"at_ms", "received_at_ms"}
            ):
                return value + int(delta * 1000)
            if isinstance(value, str) and key in {"timestamp", "at"}:
                try:
                    return (datetime.fromisoformat(value) + timedelta(
                        seconds=delta)).isoformat(sep=" ")
                except ValueError:
                    pass
            return value

        trade = moved(deepcopy(base))
        trade["id"] = ident
        trade["code"] = f"{ident:06d}"
        for event in trade["timeline"]:
            fields = event.get("fields") or {}
            if "position_key" in fields:
                fields["position_key"] = f"record:{ident}"
            if "classifier_position_key" in fields:
                fields["classifier_position_key"] = f"record:{ident}"
        assert prepare_position(trade)["source_gap"] is None
        trades.append(trade)
        outcomes.append({"record_id": str(ident),
                         "exit_rule": "scalp_trailing_take_profit",
                         "completion_observed_date": "2026-09-25"})
    report = summarize_mechanical(trades, outcomes, population_complete=True)
    research = report["classifier_policy_research"]
    assert research["candidate_count"] == 66
    assert len(research["train_ineligible_candidate_sha256"]) > 0
    assert len(research["common_support_ids"]) == 120
    assert all(len(research["markets"][market]["exposed_ids"]) == 40
               for market in START_MARKETS)
    assert report["research_candidate"] is None


def test_replay_binds_new_route_segment_and_ignores_non_executable_journal():
    position, vector, base = _batched_position()
    first = position["timeline"][-2]["fields"]
    later = position["timeline"][-1]["fields"]
    journal = position["timeline"][-3]["fields"]
    first.update(classifier_route_key="KRX|KRX", classifier_market="REGULAR")
    later.update(classifier_route_key="KRX|NXT", classifier_market="REGULAR")
    journal.update(classifier_route_key="KRX|NXT", classifier_market="REGULAR")
    premarket = deepcopy(journal)
    premarket["classifier_market"] = "PREMARKET"
    premarket["classifier_route_key"] = "KRX|KRX"
    premarket["classifier_events"][0]["sequence"] = 2
    premarket["classifier_events"][1]["sequence"] = 3
    position["timeline"].insert(1, {"stage": "scalp_trailing_mechanical_input",
                                    "fields": premarket})
    prepared = prepare_position(position)
    assert prepared["source_gap"] is None
    assert prepared["rows"][1]["classifier_route_key"] == "KRX|NXT"
    outcome = replay_vector(position, prepared, vector,
                            actual_exit_rule="scalp_trailing_take_profit")
    assert outcome["first_trigger_at_epoch"] == (base + 100) / 1000


def test_ws_wakeup_is_targeted_to_active_holding_codes():
    observed = []
    monitor = ScalpExitSafetyMonitor(
        targets_provider=lambda: [
            {"status": "HOLDING", "code": "123456"},
            {"status": "HOLDING", "code": "654321"},
        ],
        ws_snapshot_provider=lambda code: {"code": code},
        evaluator=lambda target, code, snapshot, **kwargs: observed.append(code),
        state_lock=threading.RLock(),
    )
    assert monitor.run_once() == 2
    observed.clear()
    monitor.wake("999999")
    assert not monitor._wakeup_event.is_set()
    monitor.wake("123456")
    assert monitor._wakeup_event.is_set()
    assert monitor.run_once(only_codes={"123456"}) == 1
    assert observed == ["123456"]


def test_pre_arm_fast_monitor_updates_classifier_without_rest(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    calls = []
    monkeypatch.setattr(handlers, "_scalp_fast_exit_guard_active", lambda **kwargs: False)
    monkeypatch.setattr(handlers, "_has_active_sell_order_pending", lambda stock: False)
    monkeypatch.setattr(handlers, "_is_any_simulated_position", lambda *args: False)
    monkeypatch.setattr(handlers, "_manual_control_exclusion_blocked",
                        lambda *args, **kwargs: False)
    monkeypatch.setattr(handlers, "_scalp_trailing_trusted_peak",
                        lambda *args, **kwargs: 10010)
    monkeypatch.setattr(handlers, "calculate_net_profit_rate",
                        lambda buy, price: (price / buy - 1) * 100)
    monkeypatch.setattr(handlers, "_scalp_trailing_values_for_evaluation",
                        lambda now: (dict(DEFAULTS), "REGULAR"))
    monkeypatch.setattr(handlers, "_scalp_trailing_arm_was_latched", lambda stock: False)
    monkeypatch.setattr(handlers, "_build_quote_consistency_fields",
                        lambda *args, **kwargs: ({"quote_consistency_state": "ok"},
                                                  10010, 10011, 10009))
    monkeypatch.setattr(handlers, "_trusted_scalp_trailing_bid",
                        lambda *args, **kwargs: (10009, "fresh_ws_executable_bid"))
    monkeypatch.setattr(handlers, "_scalp_trailing_mechanical_strength_safe",
                        lambda *args, **kwargs: calls.append(kwargs) or (False, {}))
    monkeypatch.setattr(handlers, "_fetch_rest_orderbook_snapshot_bounded",
                        lambda *args, **kwargs: (_ for _ in ()).throw(
                            AssertionError("pre_arm_must_not_fetch_rest")))
    stock = {"id": 1, "code": "123456", "strategy": "SCALPING",
             "status": "HOLDING", "buy_price": 10000, "buy_qty": 1}
    assert not handlers.evaluate_and_dispatch_fast_scalp_exit(
        stock, "123456", {"best_bid": 10009},
        now_ts=_at("2026-09-25 10:00:00"),
    )
    assert len(calls) == 1


def test_trade_review_preserves_each_mechanical_journal_event():
    from src.engine.sniper_trade_review_report import (
        HoldingEvent, _build_timeline, _decode_threshold_json_fields,
    )

    events = []
    for sequence in (1, 2):
        fields = _decode_threshold_json_fields({
            "classifier_events": json.dumps([{"sequence": sequence}]),
            "first_crossing": json.dumps({"threshold_key": "SCALP_TRAILING_LIMIT_WEAK"}),
        })
        events.append(HoldingEvent(
            timestamp="2026-09-25 09:31:55", name="test", code="123456",
            stage="scalp_trailing_mechanical_input", fields=fields,
            raw_line="",
        ))
    timeline = _build_timeline(events)
    assert len(timeline) == 2
    assert [row["fields"]["classifier_events"][0]["sequence"]
            for row in timeline] == [1, 2]


def test_first_crossing_latches_weak_width_and_premarket_cannot_signal():
    from src.engine import sniper_state_handlers as handlers

    stock = {"id": 1, "code": "123456", "buy_price": 10000}
    crossed = evaluate_trailing_take_profit(
        peak_price=10100, executable_bid=10050, peak_profit_pct=1.0,
        start_pct=.6, strong=False, weak_limit_pct=.4, strong_limit_pct=.8,
    )
    fields = {"classifier_state": "WEAK", "classifier_quote_sequence": 2,
              "classifier_new_event_count": 1}
    first = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", crossed, observed_at=_at("2026-09-25 10:00:00"),
        mechanical_fields=fields, market="REGULAR",
    )
    assert first.triggered and first.threshold_pct == .4
    later = evaluate_trailing_take_profit(
        peak_price=10100, executable_bid=10090, peak_profit_pct=1.0,
        start_pct=.6, strong=True, weak_limit_pct=.4, strong_limit_pct=.8,
    )
    latched = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", later, observed_at=_at("2026-09-25 10:00:01"),
        mechanical_fields={"classifier_state": "STRONG"}, market="REGULAR",
    )
    assert latched.triggered and latched.threshold_key == "SCALP_TRAILING_LIMIT_WEAK"
    premarket = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", later, observed_at=_at("2026-09-25 08:40:00"),
        mechanical_fields={}, market="PREMARKET",
    )
    assert not premarket.triggered


def test_same_0d_quote_cannot_create_a_new_ws_crossing_after_0b_peak():
    from src.engine import sniper_state_handlers as handlers

    stock = {"id": 2, "code": "123456", "buy_price": 10000}
    quiet = evaluate_trailing_take_profit(
        peak_price=10100, executable_bid=10070, peak_profit_pct=1.0,
        start_pct=.6, strong=False, weak_limit_pct=.4, strong_limit_pct=.8,
    )
    fields = {"classifier_state": "WEAK", "classifier_quote_sequence": 10,
              "classifier_item": "123456", "classifier_transport_epoch": 1}
    first = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", quiet, observed_at=_at("2026-09-25 10:00:00"),
        mechanical_fields=fields, market="REGULAR",
        bid_source="fresh_ws_executable_bid",
    )
    assert not first.triggered
    peak_changed = evaluate_trailing_take_profit(
        peak_price=10130, executable_bid=10070, peak_profit_pct=1.3,
        start_pct=.6, strong=False, weak_limit_pct=.4, strong_limit_pct=.8,
    )
    repeated = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", peak_changed, observed_at=_at("2026-09-25 10:00:00.100000"),
        mechanical_fields=dict(fields), market="REGULAR",
        bid_source="fresh_ws_executable_bid",
    )
    assert not repeated.triggered
    route_switched = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", peak_changed,
        observed_at=_at("2026-09-25 10:00:00.150000"),
        mechanical_fields={**fields, "classifier_route_key": "KRX|NXT"},
        market="REGULAR", bid_source="fresh_ws_executable_bid",
    )
    assert route_switched.triggered
    assert stock["scalp_trailing_first_crossing"]["quote_route_key"] == "KRX|NXT"
    next_quote = handlers._scalp_trailing_latch_first_crossing(
        stock, "123456", peak_changed, observed_at=_at("2026-09-25 10:00:00.200000"),
        mechanical_fields={**fields, "classifier_quote_sequence": 11}, market="REGULAR",
        bid_source="fresh_ws_executable_bid",
    )
    assert next_quote.triggered
