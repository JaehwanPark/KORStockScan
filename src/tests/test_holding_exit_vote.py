"""Pure contract checks for observation-only pre-signal exit votes."""

import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest


def test_holding_vote_review_scheduler_never_waits_for_provider(monkeypatch):
    import threading
    import time
    from src.engine import sniper_state_handlers as handlers

    started = threading.Event()
    release = threading.Event()
    monkeypatch.setattr(handlers, "_HOLDING_VOTE_INFLIGHT", {})

    def slow_provider():
        started.set()
        release.wait(2.0)

    began = time.perf_counter()
    assert handlers._schedule_holding_vote_review("000001", slow_provider) == "scheduled"
    assert time.perf_counter() - began < 0.1
    assert started.wait(1.0)
    assert handlers._schedule_holding_vote_review("000001", slow_provider) == "inflight_skip"
    release.set()
    handlers._HOLDING_VOTE_INFLIGHT["000001"].result(timeout=2.0)

from src.engine.ai.holding_exit_vote import (
    append_vote_file,
    append_vote,
    input_snapshot_id,
    load_votes_file,
    normalize_vote_response,
    research_decision,
    signal_snapshot,
    vote_store_path,
)

BUY_IDENTITY = input_snapshot_id([["BUY-1", "FILL-1", 1]])


def _vote(*, source_generation="item:1", requested_at=10.0,
          received_at=11.0, verdict="PASS", market="REGULAR"):
    response = {
        "verdict": verdict,
        "conviction": "FIRM",
        "reason_codes": ["tape_adverse"],
        "input_snapshot_id": "snapshot-1",
    }
    return normalize_vote_response(
        response, expected_snapshot_id="snapshot-1",
        position_key="record:7", market=market, session_key="2026-09-25",
        model="gpt-5.4-nano", prompt_version="holding_exit_vote_v1",
        route="KRX", transport_epoch="2",
        source_generation=source_generation,
        requested_at=requested_at, received_at=received_at,
    )


def test_snapshot_id_is_stable_for_same_exact_input():
    assert input_snapshot_id({"a": 1, "b": 2}) == input_snapshot_id(
        {"b": 2, "a": 1}
    )


def test_pass_is_only_exit_permission_evidence():
    vote = _vote()
    assert vote["status"] == "VALID"
    assert vote["purpose"] == "EXIT_PERMISSION"
    ledger, status = append_vote([], vote)
    assert status == "appended"
    snapshot = signal_snapshot(
        ledger, position_key="record:7", market="REGULAR",
        session_key="2026-09-25", model="gpt-5.4-nano",
        prompt_version="holding_exit_vote_v1", signal_at=12.0,
        window_sec=60.0,
    )
    assert snapshot["pass_count"] == 1
    assert snapshot["decision_authority"] == "observation_only"
    assert "order" not in snapshot
    assert "add" not in snapshot


def test_score_and_cache_cannot_become_votes():
    arguments = {
        "expected_snapshot_id": "snapshot-1", "position_key": "record:7",
        "market": "REGULAR", "session_key": "2026-09-25",
        "model": "gpt-5.4-nano", "prompt_version": "holding_exit_vote_v1",
        "route": "KRX", "transport_epoch": "2",
        "source_generation": "item:1", "requested_at": 10.0,
        "received_at": 11.0,
    }
    response = {
        "verdict": "PASS", "conviction": "FIRM",
        "reason_codes": ["tape_adverse"],
        "input_snapshot_id": "snapshot-1", "score": 99,
    }
    assert normalize_vote_response(response, **arguments)["status"] == "INSUFFICIENT"
    response.pop("score")
    response["cache_hit"] = True
    assert normalize_vote_response(response, **arguments)["status"] == "INSUFFICIENT"


def test_duplicate_quote_and_late_old_request_are_rejected():
    first, status = append_vote([], _vote())
    assert status == "appended"
    duplicate, status = append_vote(
        first, _vote(source_generation="item:1", requested_at=12.0,
                     received_at=13.0)
    )
    assert status == "duplicate_snapshot"
    assert len(duplicate) == 1
    second, status = append_vote(
        first, _vote(source_generation="item:2", requested_at=12.0,
                     received_at=13.0)
    )
    assert status == "appended"
    old, status = append_vote(
        second, _vote(source_generation="item:3", requested_at=11.0,
                      received_at=14.0)
    )
    assert status == "out_of_order"
    assert len(old) == 2


def test_signal_does_not_count_late_or_other_market_votes():
    ledger = [
        _vote(),
        _vote(source_generation="item:2", requested_at=12.0,
              received_at=13.0, verdict="VETO"),
        _vote(source_generation="item:3", requested_at=10.0,
              received_at=11.0, market="PREMARKET"),
    ]
    snapshot = signal_snapshot(
        ledger, position_key="record:7", market="REGULAR",
        session_key="2026-09-25", model="gpt-5.4-nano",
        prompt_version="holding_exit_vote_v1", signal_at=12.0,
        window_sec=60.0,
    )
    assert snapshot["vote_count"] == 1
    assert snapshot["pass_count"] == 1
    assert snapshot["veto_count"] == 0


def test_provider_input_and_prompt_keep_pass_exit_only(monkeypatch):
    from src.engine import ai_engine_openai

    engine = object.__new__(ai_engine_openai.GPTSniperEngine)
    engine.lock = threading.Lock()
    engine.ai_disabled = False
    engine._extract_quote_snapshot = lambda _ws: {
        "best_bid": 101, "best_ask": 102,
        "best_bid_qty": 10, "best_ask_qty": 20,
    }
    monkeypatch.setattr(
        ai_engine_openai, "ai_input_preflight", lambda _: {"allowed": True}
    )
    captured = {}

    def call(prompt, user_input, **kwargs):
        captured["prompt"] = prompt
        captured["payload"] = json.loads(user_input)
        captured["kwargs"] = kwargs
        return {
            "verdict": "PASS", "conviction": "TENTATIVE",
            "reason_codes": ["tape_adverse"],
            "input_snapshot_id": captured["payload"]["input_snapshot_id"],
        }

    engine._call_openai_safe = call
    engine._merge_last_transport_meta = lambda result: result
    monkeypatch.setattr(
        ai_engine_openai, "settle_scalping_feature_delivery",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        ai_engine_openai, "record_ai_decision_trace",
        lambda *_args, **_kwargs: {"ai_decision_trace_id": "trace-1"},
    )
    vote = engine.evaluate_scalping_holding_exit_vote(
        "Stock", "005930", {"curr": 101}, [], [],
        {"buy_price": 100, "curr_price": 101, "profit_rate": 1,
         "peak_profit": 2, "held_sec": 20, "prior_score": 99},
        market="REGULAR", session_key="2026-09-25",
        position_key="record:7", route="KRX", transport_epoch="2",
        source_generation="item:1", holding_context={},
    )
    assert vote["status"] == "VALID"
    assert vote["verdict"] == "PASS"
    assert vote["purpose"] == "EXIT_PERMISSION"
    assert vote["ai_decision_trace_id"] == "trace-1"
    assert "prior_score" not in json.dumps(captured["payload"])
    assert "adding" in captured["prompt"]
    assert captured["kwargs"]["schema_name"] == "holding_exit_vote_v1"


def test_runtime_collection_uses_one_path_bundle_and_one_vote_is_insufficient(monkeypatch, tmp_path):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.ai.holding_exit_vote import normalize_path_vote_bundle
    from src.engine.scalping import ai_market_snapshot, holding_decision_context

    class Budget:
        def reserve(self, **_kwargs):
            return type("Decision", (), {"allowed": True})()

    calls = []
    class AI:
        def evaluate_scalping_holding_path_votes(self, *_args, **kwargs):
            calls.append(kwargs["requested_paths"])
            response = {
                "input_snapshot_id": "snapshot-1",
                "votes": [
                    {"path_id": path, "verdict": "PASS", "conviction": "FIRM",
                     "reason_codes": [(
                         "add_rebound_tape_supportive" if path == "ADD_REBOUND"
                         else "exit_tp_tape_adverse" if path == "EXIT_TRAILING_TP"
                         else "exit_soft_tape_adverse" if path == "EXIT_SOFT_STOP"
                         else "exit_post_add_tape_adverse" if path == "EXIT_POST_ADD_FAIL"
                         else "exit_bad_entry_tape_adverse"
                     )]}
                    for path in kwargs["requested_paths"]
                ],
            }
            events = normalize_path_vote_bundle(
                response, requested_paths=kwargs["requested_paths"],
                expected_snapshot_id="snapshot-1", position_key=kwargs["position_key"],
                market=kwargs["market"], session_key=kwargs["session_key"],
                model="gpt-5.4-nano", route=kwargs["route"],
                transport_epoch=kwargs["transport_epoch"],
                source_generation=kwargs["source_generation"],
                buy_fill_identity=kwargs["buy_fill_identity"],
                buy_fill_legs=kwargs["buy_fill_legs"],
                quote_observed_at=8.9,
                requested_at=9.0, received_at=9.5,
            )
            for event in events:
                event["provider_called"] = True
                event["path_decision_input_sha256"] = kwargs[
                    "expected_path_hashes"
                ][event["path_id"]]
            return events

    stock = {"id": 7, "name": "Stock", "strategy": "SCALPING",
             "_entry_receipt_filled_by_order_no": {"BUY-1": 1},
             "_entry_receipt_executions_by_order_no": {
                 "BUY-1": {"FILL-1": {"cumulative_qty": 1}}}}
    monkeypatch.setattr(handlers.time, "time", lambda: 10.0)
    monkeypatch.setattr(handlers, "scalp_trailing_market_type_at", lambda _: "REGULAR")
    monkeypatch.setattr(handlers, "_holding_path_vote_paths", lambda *a, **k:
                        ("EXIT_TRAILING_TP", "ADD_REBOUND"))
    monkeypatch.setattr(handlers, "ws_quote_source_receipt", lambda *_args, **_kwargs: {
        "item": "005930", "observed_epoch": 10.0,
        "market_route": "KRX", "transport_epoch": 2, "route_sequence": 1,
    })
    monkeypatch.setattr(handlers, "DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET", Budget())
    monkeypatch.setattr(handlers, "path_vote_store_path", lambda *_args: tmp_path / "vote.jsonl")
    monkeypatch.setattr(handlers, "path_vote_claims_path", lambda *_args: tmp_path / "claims.jsonl")
    monkeypatch.setattr(ai_market_snapshot, "ai_input_preflight", lambda _: {
        "allowed": True, "status": "ok", "blockers": [],
    })
    monkeypatch.setattr(holding_decision_context,
                        "holding_decision_context_model_payload",
                        lambda _: {"signed_tape": {"state": "buy"},
                                   "microstructure": {"best_bid": 99,
                                                      "best_ask": 100},
                                   "execution_pnl": {
                                       "executable_sell_price": 99,
                                       "estimated_net_executable_pnl_pct": -1,
                                   }})
    monkeypatch.setattr(handlers, "_log_holding_pipeline", lambda *_args, **_fields: None)
    assert handlers._collect_holding_path_votes(
        stock=stock, code="005930", ai_engine=AI(), ws_data={
            "curr": 99, "bid_tot": 1000, "ask_tot": 1200,
            "orderbook": {"bids": [{"price": 99}],
                                       "asks": [{"price": 100}]},
        },
        recent_ticks=[{"price": 99}], recent_candles=[{"close": 99}],
        position_ctx={"buy_price": 100, "curr_price": 99,
                      "profit_rate": -1, "peak_profit": 0,
                      "drawdown_from_peak_pct": 1, "held_sec": 10},
        holding_context={}, now_ts=10.0, min_interval_sec=1.0,
    ) == "appended"
    assert calls == [("EXIT_TRAILING_TP", "ADD_REBOUND")]
    assert len(stock["holding_path_vote_ledger"]) == 2
    assert handlers._collect_holding_path_votes(
        stock=stock, code="005930", ai_engine=AI(), ws_data={
            "curr": 99, "bid_tot": 1000, "ask_tot": 1200,
            "orderbook": {"bids": [{"price": 99}],
                                       "asks": [{"price": 100}]},
        }, recent_ticks=[{"price": 99}], recent_candles=[{"close": 99}],
        position_ctx={"buy_price": 100, "curr_price": 99,
                      "profit_rate": -1, "peak_profit": 0,
                      "drawdown_from_peak_pct": 1, "held_sec": 10},
        holding_context={}, now_ts=10.0, min_interval_sec=1.0,
    ) == "unchanged_input_skip"
    assert len(calls) == 1
    assert handlers._collect_holding_path_votes(
        stock=stock, code="005930", ai_engine=AI(), ws_data={
            "curr": 99, "bid_tot": 1000, "ask_tot": 1200,
            "orderbook": {"bids": [{"price": 99}],
                                       "asks": [{"price": 100}]},
        }, recent_ticks=[{"price": 99}], recent_candles=[{"close": 99}],
        position_ctx={"buy_price": 100, "curr_price": 99,
                      "profit_rate": -1, "peak_profit": 0,
                      "drawdown_from_peak_pct": 1, "held_sec": 11},
        holding_context={}, now_ts=10.0, min_interval_sec=1.0,
    ) == "duplicate_quote_generation_skip"
    assert len(stock["holding_path_vote_ledger"]) == 2
    snapshot = handlers._holding_path_signal_decision(
        stock, "005930", path_id="ADD_REBOUND", signal_id="add-1", signal_at=12.0,
    )
    assert snapshot["vote_count"] == 1
    assert snapshot["decision"] == "INSUFFICIENT"


def test_material_input_hash_ignores_receipt_clock_and_claim_survives_restart(tmp_path):
    from src.engine.ai.holding_exit_vote import (
        path_vote_input_hashes, path_vote_claims_path,
        read_path_vote_input_claims, read_path_vote_input_claim_history,
        claim_path_vote_inputs,
        release_path_vote_inputs,
    )

    payload = {
        "input_schema": "holding_path_vote_v10",
        "requested_paths": ["EXIT_TRAILING_TP", "EXIT_SOFT_STOP"],
        "stock_code": "005930", "market": "REGULAR",
        "position_key": "record:7", "buy_fill_identity": "x" * 64,
        "position": {"profit_rate": 1.0, "held_sec": 10},
        "quote": {"best_bid": 100}, "last_ticks": [{"price": 100}],
        "flow": {"signed_tape": {"state": "buy", "age_ms": 100},
                 "ai_market_snapshot_v1": {"captured_at": "clock-a"}},
        "source": {"route": "KRX", "transport_epoch": "1",
                   "source_generation": "a", "quote_observed_at": 1.0},
    }
    first = path_vote_input_hashes(payload, model="gpt-5.4-nano")
    assert first["request_payload_sha256"] == hashlib.sha256(json.dumps(
        {**payload, "input_snapshot_id": first["input_snapshot_id"]},
        ensure_ascii=True, separators=(",", ":"), default=str,
    ).encode("ascii")).hexdigest()
    path = path_vote_claims_path(tmp_path, "record:7")
    assert claim_path_vote_inputs(path, "record:7",
                                  first["path_decision_input_sha256"])
    assert not claim_path_vote_inputs(path, "record:7",
                                      first["path_decision_input_sha256"])
    assert read_path_vote_input_claims(path, "record:7") == first[
        "path_decision_input_sha256"
    ]
    moved_clock = json.loads(json.dumps(payload))
    moved_clock["source"]["source_generation"] = "b"
    moved_clock["source"]["quote_observed_at"] = 2.0
    moved_clock["flow"]["signed_tape"]["age_ms"] = 200
    moved_clock["flow"]["ai_market_snapshot_v1"]["captured_at"] = "clock-b"
    second = path_vote_input_hashes(moved_clock, model="gpt-5.4-nano")
    assert second["request_payload_sha256"] != first["request_payload_sha256"]
    assert second["decision_input_sha256"] == first["decision_input_sha256"]
    assert second["path_decision_input_sha256"] == first[
        "path_decision_input_sha256"
    ]
    moved_bid = json.loads(json.dumps(moved_clock))
    moved_bid["quote"]["best_bid"] = 101
    third = path_vote_input_hashes(moved_bid, model="gpt-5.4-nano")
    assert third["decision_input_sha256"] != first["decision_input_sha256"]
    assert claim_path_vote_inputs(path, "record:7",
                                  third["path_decision_input_sha256"])
    assert not claim_path_vote_inputs(path, "record:7",
                                      first["path_decision_input_sha256"])
    assert release_path_vote_inputs(path, "record:7",
                                    third["path_decision_input_sha256"])
    assert read_path_vote_input_claims(path, "record:7") == first[
        "path_decision_input_sha256"
    ]
    assert read_path_vote_input_claim_history(path, "record:7") == {
        path_id: {path_hash} for path_id, path_hash in
        first["path_decision_input_sha256"].items()
    }
    assert claim_path_vote_inputs(path, "record:7",
                                  third["path_decision_input_sha256"])


def test_path_input_gaps_are_specific_to_post_add_and_rebound():
    from src.engine.ai.holding_exit_vote import path_vote_input_gaps

    payload = {
        "requested_paths": ["EXIT_TRAILING_TP", "EXIT_POST_ADD_FAIL", "ADD_REBOUND"],
        "position": {"buy_price": 100, "curr_price": 101,
                     "profit_rate": 1, "peak_profit": 2,
                     "held_sec": 20, "drawdown_from_peak_pct": 1,
                     "reversal_add_state": "POST_ADD_EVAL",
                     "reversal_add_executed_at": 100},
        "quote": {"best_bid": 100, "best_ask": 101,
                  "bid_total_depth": 1000, "ask_total_depth": 1200},
        "last_ticks": [{"price": 100}], "last_candles": [],
        "flow": {"signed_tape": {"state": "buy"},
                 "microstructure": {"best_bid": 100, "best_ask": 101},
                 "execution_pnl": {"executable_sell_price": 100,
                                   "estimated_net_executable_pnl_pct": 1}},
        "source_quality": {"allowed": True},
    }
    gaps = path_vote_input_gaps(payload)
    assert gaps["EXIT_TRAILING_TP"] == ()
    no_depth = json.loads(json.dumps(payload))
    no_depth["quote"]["bid_total_depth"] = None
    assert "orderbook_depth_missing" in path_vote_input_gaps(no_depth)[
        "EXIT_TRAILING_TP"
    ]
    bid_conflict = json.loads(json.dumps(payload))
    bid_conflict["flow"]["execution_pnl"]["executable_sell_price"] = 99
    assert "executable_exit_bid_conflict" in path_vote_input_gaps(bid_conflict)[
        "EXIT_TRAILING_TP"
    ]
    assert gaps["EXIT_POST_ADD_FAIL"] == ("post_add_fill_evidence_missing",)
    assert gaps["ADD_REBOUND"] == ("rebound_candle_evidence_missing",)


def test_path_input_claim_allows_one_concurrent_owner(tmp_path):
    from src.engine.ai.holding_exit_vote import claim_path_vote_inputs

    path = tmp_path / "claims.jsonl"
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(
            lambda _: claim_path_vote_inputs(
                path, "record:7", {"EXIT_TRAILING_TP": "a" * 64}
            ), range(16),
        ))
    assert sum(results) == 1


@pytest.mark.parametrize("market", (
    "PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET",
))
def test_each_path_has_a_complete_projected_input_in_each_market(
    monkeypatch, market,
):
    from src.engine.ai.holding_exit_vote import (
        PATH_IDS, build_path_vote_input, path_vote_input_gaps,
    )
    from src.engine.scalping import ai_market_snapshot, holding_decision_context

    monkeypatch.setattr(ai_market_snapshot, "ai_input_preflight", lambda _: {
        "allowed": True, "status": "ok", "blockers": [],
    })
    monkeypatch.setattr(holding_decision_context,
                        "holding_decision_context_model_payload",
                        lambda _: {
                            "signed_tape": {"state": "buy"},
                            "microstructure": {"best_bid": 100,
                                               "best_ask": 101},
                            "execution_pnl": {
                                "executable_sell_price": 100,
                                "estimated_net_executable_pnl_pct": 0,
                            },
                            "position_lifecycle": {
                                "scale_in_filled_qty": 1, "never_green": False,
                            },
                        })
    payload = build_path_vote_input(
        stock_code="005930", ws_data={
            "orderbook": {"bids": [{"price": 100}],
                          "asks": [{"price": 101}]},
            "bid_tot": 1000, "ask_tot": 900,
        }, recent_ticks=[{"price": 100}],
        recent_candles=[{"close": 100}],
        position_ctx={
            "buy_price": 100, "curr_price": 100, "profit_rate": 0,
            "peak_profit": 1, "drawdown_from_peak_pct": 1,
            "held_sec": 20, "reversal_add_state": "POST_ADD_EVAL",
            "reversal_add_executed_at": 10,
        }, requested_paths=tuple(sorted(PATH_IDS)), market=market,
        session_key="2026-09-25", position_key="record:7",
        buy_fill_identity=BUY_IDENTITY,
        route="KRX" if market == "REGULAR" else "NXT",
        transport_epoch="1", source_generation="item:1",
        quote_observed_at=20, holding_context={},
    )
    assert payload["quote"]["bid_total_depth"] == 1000
    assert payload["quote"]["ask_total_depth"] == 900
    assert all(not reasons for reasons in path_vote_input_gaps(payload).values())


def test_research_counting_rule_requires_quorum_and_firm_veto():
    votes = []
    for index, verdict in enumerate(("VETO", "VETO", "PASS"), 1):
        votes.append(_vote(
            source_generation=f"item:{index}",
            requested_at=float(index), received_at=float(index) + 0.1,
            verdict=verdict,
        ))
    snapshot = signal_snapshot(
        votes, position_key="record:7", market="REGULAR",
        session_key="2026-09-25", model="gpt-5.4-nano",
        prompt_version="holding_exit_vote_v1", signal_at=5.0,
        window_sec=60.0,
    )
    decision = research_decision(
        snapshot, min_votes=3, pass_votes=2, veto_votes=2,
        firm_veto_votes=2, max_latest_age_sec=5.0,
    )
    assert decision["verdict"] == "VETO"
    assert decision["decision_authority"] == "offline_research_only"
    assert research_decision(
        snapshot, min_votes=4, pass_votes=2, veto_votes=2,
        firm_veto_votes=2, max_latest_age_sec=5.0,
    )["verdict"] == "INSUFFICIENT"


def test_vote_file_survives_restart_and_rejects_duplicate(tmp_path):
    path = vote_store_path(tmp_path, "record:7")
    stored, status = append_vote_file(path, "record:7", _vote())
    assert status == "appended"
    assert len(stored) == 1
    assert load_votes_file(path, "record:7") == stored
    stored_again, status = append_vote_file(path, "record:7", _vote())
    assert status == "duplicate_snapshot"
    assert len(stored_again) == 1
    assert len(path.read_text().splitlines()) == 1
    with pytest.raises(ValueError, match="vote_store_contract_corrupt"):
        load_votes_file(path, "record:other")


def test_corrupt_vote_file_is_not_silently_ignored(tmp_path):
    path = vote_store_path(tmp_path, "record:7")
    path.parent.mkdir(parents=True)
    path.write_text("{invalid json\n")
    with pytest.raises(ValueError, match="vote_store_json_corrupt"):
        load_votes_file(path, "record:7")
