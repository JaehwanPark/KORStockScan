from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.engine.lifecycle import avg_down_policy_replay as policy
from src.engine.lifecycle.avg_down_replay import replay_exit_paths
from src.engine.lifecycle.avg_down_replay import canonical_digest, build_replay_evidence
from src.engine.scalping import avg_down_replay_capture as capture
from src.tests.test_avg_down_replay import replay_fixture


def policy_fixture():
    from src.engine import sniper_state_handlers as handlers
    from src.utils.constants import TRADING_RULES

    observation, frames = replay_fixture()
    epoch = datetime.fromisoformat(observation["emitted_at"]).timestamp()
    runtime = SimpleNamespace(**vars(handlers))
    runtime.TRADING_RULES = TRADING_RULES
    runtime.COOLDOWNS = {}
    runtime.ALERTED_STOCKS = set()
    runtime.HIGHEST_PRICES = {}
    runtime.LAST_AI_CALL_TIMES = {}
    runtime.LAST_LOG_TIMES = {}
    stock = {
        "id": 91,
        "code": observation["stock_code"],
        "name": "REPLAY_TEST",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": observation["pre_add_buy_price"],
        "buy_qty": observation["pre_add_buy_qty"],
        "holding_started_at": datetime.fromtimestamp(epoch - 120),
        "order_time": epoch - 120,
        "last_ai_reviewed_at": epoch,
        "scale_in_locked": True,
        "exit_token": "test_already_owned_exit",
    }
    observation["initial_policy_state"] = capture.holding_state(runtime, stock)
    snapshot = capture.policy_snapshot(runtime, epoch)
    for name in snapshot["files"]:
        if "manual_control_excluded_codes" in name or "symbol_owner_policy_" in name:
            snapshot["files"][name] = None
    # Explicit test-only control exclusion makes a deterministic full-handler
    # early HOLD, without replacing the handler with a callback fixture.
    snapshot["environment"]["KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES"] = observation[
        "stock_code"
    ]
    observation["policy_snapshot"] = snapshot
    observation["exit_policy_version"] = policy.snapshot_version(snapshot)
    for arm in observation["route_replay"].values():
        arm["should_add"] = False
    for frame in frames:
        frame["source_observation_id"] = observation["source_event_id"]
        frame["scale_in_decision_id"] = observation["scale_in_decision_id"]
        frame["exit_policy_version"] = observation["exit_policy_version"]
        frame["market"].update(
            ws_data={"curr": frame["market"]["best_bid"]}, market_regime="BULL"
        )
    return observation, frames


def test_isolated_existing_policy_has_no_parent_global_mutation():
    from src.engine import sniper_state_handlers as handlers

    observation, frames = policy_fixture()
    original = handlers.TRADING_RULES
    result = policy.isolated_replay(observation, frames)
    assert "adapter_error" not in result, result
    assert result["policy_adapter"] == policy.ADAPTER_VERSION
    assert result["actual_order_submitted"] is False
    assert result["broker_order_forbidden"] is True
    assert handlers.TRADING_RULES is original
    assert set(result["blockers"].values()) == {"pending_exit_outcome"}, result


def test_actual_receipt_state_transition_runs_independently_in_worker():
    observation, frames = policy_fixture()
    observation["route_replay"]["80"].update(
        should_add=True,
        add_type="AVG_DOWN",
        action_reason="shallow_volatility_avg_down",
    )
    result = policy.isolated_replay(observation, frames)
    assert "adapter_error" not in result, result
    assert set(result["blockers"].values()) == {"pending_exit_outcome"}, result


def exit_fixture():
    observation, frames = policy_fixture()
    snapshot = observation["policy_snapshot"]
    snapshot["environment"]["KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES"] = ""
    snapshot["environment"]["KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED"] = "1"
    snapshot["environment"][
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE"
    ] = "2026-09-04"
    observation["exit_policy_version"] = policy.snapshot_version(snapshot)
    stock = observation["initial_policy_state"]["stock"]
    stock.pop("exit_token")
    stock["effective_venue"] = "KRX"
    stock["hard_stop_pct"] = -0.7
    stock["hard_stop_emergency_pct"] = -1.2
    for frame in frames:
        frame["exit_policy_version"] = observation["exit_policy_version"]
        epoch = datetime.fromisoformat(frame["emitted_at"]).timestamp()
        frame["market"].update(best_bid=9500, best_ask=9510)
        frame["market"]["ws_data"] = {
            "curr": 9500,
            "best_bid": 9500,
            "best_ask": 9510,
            "best_bid_qty": 100,
            "best_ask_qty": 100,
            "last_ws_update_ts": epoch,
            "last_realtime_type_ts": {"0D": epoch},
            "quote_stale": False,
        }
    return observation, frames


def test_existing_fast_policy_reaches_virtual_exit_without_order_transport():
    observation, frames = exit_fixture()
    result = policy.isolated_replay(observation, frames)
    assert result.get("state") == "paired_exit_complete_source_only", result
    assert result["runtime_authority_ready"] is False
    assert result["outcomes"]["85"]["exit_price"] == 9500


def test_virtual_add_receipt_then_actual_exit_preserves_independent_quantities():
    observation, frames = exit_fixture()
    observation["route_replay"]["80"].update(
        should_add=True,
        add_type="AVG_DOWN",
        action_reason="shallow_volatility_avg_down",
    )
    result = policy.isolated_replay(observation, frames)
    assert result["state"] == "paired_exit_complete_source_only", result
    assert result["outcomes"]["80"]["exit_qty"] == 15
    assert result["outcomes"]["85"]["exit_qty"] == 10
    assert result["outcomes"]["NO_ADD"]["exit_qty"] == 10
    assert result["outcomes"]["80"]["final_policy_state"]["stock"][
        "buy_price"
    ] == pytest.approx(9966.6667)


def test_changed_implementation_is_not_replayed_as_original():
    observation, frames = policy_fixture()
    observation["policy_snapshot"]["implementation"][
        policy.IMPLEMENTATION_PATHS[0]
    ] = "old"
    observation["exit_policy_version"] = policy.snapshot_version(
        observation["policy_snapshot"]
    )
    result = policy.isolated_replay(observation, frames)
    assert result["adapter_error"] == "recorded_policy_implementation_changed"


def test_exact_state_service_never_reuses_another_state_or_future_answer():
    service = policy.RecordedServices({}, cutoff="2026-09-04T10:00:00+09:00")
    with pytest.raises(policy.ReplayInputGap) as error:
        service.call("ai_engine.evaluate_scalping_holding_score", {"buy_price": 100})
    request = error.value.request
    service.records[request["input_digest"]] = {**request, "result": {"action": "HOLD"}}
    assert service.call(
        "ai_engine.evaluate_scalping_holding_score", {"buy_price": 100}
    ) == {"action": "HOLD"}
    with pytest.raises(policy.ReplayInputGap):
        service.call("ai_engine.evaluate_scalping_holding_score", {"buy_price": 99})
    service.records[request["input_digest"]][
        "input_cutoff"
    ] = "2026-09-04T10:00:01+09:00"
    with pytest.raises(policy.ReplayInputGap):
        service.call("ai_engine.evaluate_scalping_holding_score", {"buy_price": 100})


def test_typed_snapshot_roundtrip_and_unknown_object_block():
    value = {"time": datetime(2026, 9, 4), "codes": {"123456"}, "tuple": (1, 2)}
    assert policy.thaw(policy._json_value(value)) == value
    with pytest.raises(ValueError):
        policy._json_value({"lock": object()})


def test_capture_keeps_observing_after_real_exit_and_exposes_lost_append(monkeypatch):
    monkeypatch.setattr(capture, "_ACTIVE", {})
    monkeypatch.setattr(capture, "_SEEN", set())
    capture.register(
        episode="ep",
        source_id="source",
        decision_id="decision",
        code="123456",
        venue="KRX",
        now_ts=100,
        fields={
            "replay_capture_state": "armed_source_only",
            "exit_policy_version": "p",
        },
    )
    rows = []

    def emit(frame):
        rows.append(deepcopy(frame))
        return {"structured_append_succeeded": len(rows) != 1}

    for now in (101, 102):
        capture.observe_cycle(
            now_ts=now,
            snapshot_provider=lambda code: {"curr": 100},
            market_builder=lambda *a: {"source_quality": "fresh_conflict_free"},
            emit=emit,
        )
    assert [row["sequence"] for row in rows] == [1, 2]
    assert all(row["actual_order_submitted"] is False for row in rows)
    assert all(
        row["decision_authority"] == "source_only_paired_exit_replay" for row in rows
    )


def test_capture_cadence_hole_is_not_silently_interpolated():
    observation, frames = replay_fixture()
    frames[0]["capture_gap"] = "observer_cadence_gap"
    result = replay_exit_paths(observation, frames)
    assert "replay_capture_continuity_gap" in result["blockers"].values()


def test_snapshot_policy_cannot_be_bypassed_with_recorded_exit_labels():
    from src.tests.test_avg_down_replay import decision

    observation, frames = policy_fixture()

    def forged(state, frame, version, digest):
        value = decision(state, frame, version, digest, action="EXIT")
        frames[frame["sequence"] - 1].setdefault("full_policy_decisions", {})[
            digest
        ] = value
        return value

    assert (
        replay_exit_paths(observation, frames, full_exit_evaluator=forged)["state"]
        == "paired_exit_complete_source_only"
    )
    result = policy.isolated_replay(observation, frames)
    assert set(result["blockers"].values()) == {"pending_exit_outcome"}, result


@pytest.mark.parametrize(
    "key,value",
    [
        ("buy_qty", 11),
        ("buy_price", 9999),
        ("code", "123456"),
        ("status", "COMPLETED"),
        ("pending_add_order", True),
    ],
)
def test_conflicting_initial_inventory_is_not_overwritten_to_look_valid(key, value):
    observation, frames = policy_fixture()
    observation["initial_policy_state"]["stock"][key] = value
    result = policy.isolated_replay(observation, frames)
    assert (
        result["adapter_error"]
        == "initial_holding_identity_inventory_or_pending_conflict"
    )


def test_existing_report_runs_policy_adapter_but_never_grants_order_authority():
    observation, frames = exit_fixture()
    observation["independent_exit_replay_frames"] = frames
    result = build_replay_evidence([observation])
    assert result["complete_episode_count"] == 1, result
    episode = result["episodes"][observation["position_episode_id"]]
    assert episode["policy_adapter"] == policy.ADAPTER_VERSION
    assert result["allowed_runtime_apply"] is False
    assert episode["runtime_authority_ready"] is False
    from src.engine.lifecycle.avg_down_replay import replay_evidence_contract_errors

    assert replay_evidence_contract_errors(result) == []
    episode["outcomes"]["85"]["evidence_authority"] = "runtime_authoritative"
    assert (
        "avg_down_independent_replay_outcome_authority_invalid"
        in replay_evidence_contract_errors(result)
    )


def test_worker_effect_guard_blocks_database_network_and_file_writes(tmp_path):
    import subprocess
    import sys

    script = """
import socket, sqlite3, sys
from src.engine.lifecycle.avg_down_policy_replay import _install_effect_guard, ReplayInputGap
phase = _install_effect_guard()
phase['importing'] = False
checks = [lambda: open(sys.argv[1], 'w'), lambda: sqlite3.connect(sys.argv[1]),
          lambda: socket.socket().connect(('127.0.0.1', 9))]
for check in checks:
    try:
        check()
    except ReplayInputGap:
        continue
    raise SystemExit('unblocked effect')
print('three_effects_blocked')
"""
    target = tmp_path / "must-not-exist"
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(target)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "three_effects_blocked" in result.stdout
    assert not target.exists()


def test_production_string_fields_roundtrip_through_logger_and_report(
    monkeypatch, tmp_path
):
    import json
    from src.utils import pipeline_event_logger as logger
    from src.engine.monitoring import (
        scalping_avg_down_recovery_calibration as calibration,
    )
    from src.tests.test_scalping_avg_down_recovery_calibration import _route_arm

    observation, frames = exit_fixture()
    observation["route_replay"] = {
        key: _route_arm(should_add=False, signature="NO_ADD") for key in ("80", "85")
    }
    observation["avg_down_route_schema"] = calibration.ROUTE_EVENT_SCHEMA
    current = {
        "now": datetime.fromisoformat(observation["emitted_at"]).replace(tzinfo=None)
    }

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return current["now"]

    monkeypatch.setattr(logger, "datetime", Clock)
    monkeypatch.setattr(logger, "DATA_DIR", tmp_path)
    monkeypatch.setattr(logger, "_PRODUCER_COMPACTOR", None)
    monkeypatch.setattr(
        logger,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )

    def emit(stage, fields):
        result = logger.emit_pipeline_event(
            "HOLDING_PIPELINE",
            "TEST",
            observation["stock_code"],
            stage,
            fields={
                key: json.dumps(value) if isinstance(value, (list, dict)) else value
                for key, value in fields.items()
                if key != "emitted_at"
            },
        )
        assert result["structured_append_succeeded"] is True
        return result

    emit("avg_down_route_arbitration_observed", observation)
    for frame in frames:
        current["now"] = datetime.fromisoformat(frame["emitted_at"]).replace(
            tzinfo=None
        )
        emit(
            "avg_down_exit_replay_frame_observed",
            {**frame, **capture.AUTHORITY, "replay_observed_at": frame["emitted_at"]},
        )
    collected = calibration._collect_exact_evidence(
        [tmp_path / "pipeline_events/pipeline_events_2026-09-04.jsonl"]
    )
    replay = build_replay_evidence(
        [row["independent_replay_input"] for row in collected["decisions"]]
    )
    assert replay["complete_episode_count"] == 1, (collected, replay)
    assert replay["allowed_runtime_apply"] is False
    paths = [tmp_path / "pipeline_events/pipeline_events_2026-09-04.jsonl"]
    report = {
        "target_date": "2026-09-04",
        "independent_exit_replay": replay,
        "replay_source_files": calibration._replay_source_files(paths),
        "replay_engine_implementation": canonical_digest(
            policy.implementation_identity()
        ),
    }
    output = (
        tmp_path
        / "report"
        / calibration.REPORT_TYPE
        / f"{calibration.REPORT_TYPE}_2026-09-04.json"
    )
    calibration.write_outputs(
        report, output_json=output, output_md=output.with_suffix(".md")
    )
    monkeypatch.setattr(calibration, "DATA_DIR", tmp_path)
    cached, replies, _, _ = calibration._load_replay_cache(paths)
    assert observation["source_event_id"] in cached
    collected = calibration._collect_exact_evidence(paths, replay_cache=cached)
    inputs = [row["independent_replay_input"] for row in collected["decisions"]]
    assert inputs[0]["independent_exit_replay_frames"] == []

    def forbidden(*a, **kw):
        pytest.fail("unchanged historical evidence must not replay or call AI again")

    monkeypatch.setattr(policy, "isolated_replay", forbidden)
    reused = build_replay_evidence(inputs, policy_ai_enabled=True)
    assert reused["cached_episode_count"] == 1
    assert reused["complete_episode_count"] == 1
    assert reused["policy_ai_provider_call_count"] == 0
    # A newly appended source frame invalidates whole-result reuse, even if
    # the old file has not been replaced and the symbol/policy did not change.
    emit(
        "avg_down_exit_replay_frame_observed",
        {**frames[-1], "new_source_marker": "changed", **capture.AUTHORITY},
    )
    cached, _, _, _ = calibration._load_replay_cache(paths)
    assert cached == {}


def ai_request(observation, frame, *, call="ai_provider.current_prompt"):
    args, kwargs = ("system", "user"), {"endpoint_name": "holding_score"}
    return {
        "call": call,
        "args": policy._json_value(args),
        "kwargs": kwargs,
        "input_digest": policy.external_call_key(call, args, kwargs),
        "input_cutoff": frame["emitted_at"],
        "policy_version": observation["exit_policy_version"],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_ai_replay_is_exact_bound_deduplicated_and_reuses_cache(monkeypatch):
    observation, frames = policy_fixture()
    request = ai_request(observation, frames[0])
    calls = []

    def replay(observation, rows, **kwargs):
        available = request["input_digest"] in rows[0].get("external_results", {})
        return {
            "external_replay_requests": [] if available else [request, request],
            "runtime_effect": False,
        }

    def executor(snapshot, requested):
        calls.append(requested)
        return {
            **requested,
            "result": {
                "schema": "avg_down_raw_provider_reply_v1",
                "provider_response": {"score": 70},
            },
        }

    monkeypatch.setattr(policy, "isolated_replay", replay)
    result = policy.replay_with_current_policy_ai(
        observation, frames, executor=executor
    )
    assert result["policy_ai_provider_call_count"] == len(calls) == 1
    second = policy.replay_with_current_policy_ai(
        observation,
        frames,
        executor=executor,
        cached_records=result["policy_ai_replay_records"],
    )
    assert second["policy_ai_provider_call_count"] == 0
    assert len(calls) == 1
    assert all(not frame.get("external_results") for frame in frames)


@pytest.mark.parametrize("change", ["future", "wrong_policy", "live_authority"])
def test_ai_replay_rejects_unbound_replies(monkeypatch, change):
    observation, frames = policy_fixture()
    request = ai_request(observation, frames[0])
    monkeypatch.setattr(
        policy,
        "isolated_replay",
        lambda *a, **kw: {"external_replay_requests": [request]},
    )

    def executor(*args):
        answer = {**request, "result": {}}
        key, value = {
            "future": ("input_cutoff", frames[1]["emitted_at"]),
            "wrong_policy": ("policy_version", "wrong"),
            "live_authority": ("actual_order_submitted", True),
        }[change]
        answer[key] = value
        return answer

    result = policy.replay_with_current_policy_ai(
        observation, frames, executor=executor, max_provider_calls=1
    )
    assert result["policy_ai_replay_records"] == []
    assert result["policy_ai_provider_call_count"] == 1
    assert result["policy_ai_budget_exhausted"] is True


def test_non_ai_missing_input_and_exhausted_time_never_invoke_provider(monkeypatch):
    observation, frames = policy_fixture()
    request = ai_request(observation, frames[0], call="kiwoom_orders.get_deposit")
    monkeypatch.setattr(
        policy,
        "isolated_replay",
        lambda *a, **kw: {"external_replay_requests": [request]},
    )

    def forbidden(*args):
        pytest.fail("a missing broker/market input is not an AI request")

    result = policy.replay_with_current_policy_ai(
        observation, frames, executor=forbidden
    )
    assert result["policy_ai_provider_call_count"] == 0
    result = policy.replay_with_current_policy_ai(
        observation, frames, executor=forbidden, deadline=0
    )
    assert result["adapter_error"] == "policy_replay_wall_time_budget_exhausted"


def test_policy_env_keeps_token_budget_but_excludes_credentials(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_AI_MAX_TOKENS", "123")
    monkeypatch.setenv("KORSTOCKSCAN_ACCESS_TOKEN", "not-a-real-credential")
    monkeypatch.setenv("KORSTOCKSCAN_API_KEY", "not-a-real-key")
    values = capture.policy_environment()
    assert values["KORSTOCKSCAN_AI_MAX_TOKENS"] == "123"
    assert "KORSTOCKSCAN_ACCESS_TOKEN" not in values
    assert "KORSTOCKSCAN_API_KEY" not in values


def test_compressed_market_inputs_roundtrip_and_corruption_is_explicit(monkeypatch):
    monkeypatch.setattr(capture, "_MARKET_INPUTS", {})
    value = {"candles": ["recorded-source" * 50] * 20}
    capture.record_market_inputs("123456", now_ts=100, source=value)
    encoded = capture._MARKET_INPUTS["123456"]
    assert "value_gzip_b64" in encoded["source"]
    assert policy.decode_market_inputs(encoded)["source"]["value"] == value
    encoded["source"]["value_sha256"] = "wrong"
    with pytest.raises(policy.ReplayInputGap, match="digest_mismatch"):
        policy.decode_market_inputs(encoded)


def test_capture_byte_budget_stops_and_hash_includes_final_reason(monkeypatch):
    monkeypatch.setattr(capture, "_ACTIVE", {})
    monkeypatch.setattr(capture, "_SEEN", set())
    monkeypatch.setattr(capture, "_DAILY_FRAME_BYTES", 0)
    monkeypatch.setattr(capture, "MAX_EPISODE_BYTES", 1)
    capture.register(
        episode="ep",
        source_id="src",
        decision_id="decision",
        code="123456",
        venue="KRX",
        now_ts=100,
        fields={
            "replay_capture_state": "armed_source_only",
            "exit_policy_version": "p",
        },
    )
    rows = []
    capture.observe_cycle(
        now_ts=101,
        snapshot_provider=lambda code: {},
        market_builder=lambda *a: {},
        emit=lambda row: rows.append(row),
    )
    assert not capture._ACTIVE
    frame = rows[0]
    assert frame["capture_end"] == "capture_byte_budget_exhausted"
    assert frame["source_event_id"] == "avgdn-frame-" + canonical_digest(
        {key: value for key, value in frame.items() if key != "source_event_id"}
    )


def test_runtime_capture_uses_only_matching_bbo_quantity(monkeypatch):
    from src.engine import sniper_state_handlers as handlers

    now = datetime.fromisoformat("2026-09-04T10:00:01+09:00").timestamp()
    ws = {
        "curr": 10000,
        "best_bid": 10000,
        "best_ask": 10010,
        "last_ws_update_ts": now,
        "last_realtime_type_ts": {"0D": now},
        "orderbook": {
            "bids": [{"price": 10000, "volume": 10}],
            "asks": [{"price": 10010, "volume": 20}],
        },
    }
    monkeypatch.setattr(
        handlers, "WS_MANAGER", SimpleNamespace(get_latest_data=lambda code: ws)
    )
    monkeypatch.setattr(capture, "warm_policy_cache", lambda *a, **kw: None)
    markets = []

    def observe(**kwargs):
        markets.append(kwargs["market_builder"]("005930", ws, now))
        return 1

    monkeypatch.setattr(capture, "observe_cycle", observe)
    assert handlers.observe_avg_down_exit_replay_cycle(now_ts=now) == 1
    assert markets[0]["source_quality"] == "fresh_conflict_free"
    assert markets[0]["best_bid_qty"] == 10
    ws["orderbook"]["bids"][0]["price"] = 9990
    handlers.observe_avg_down_exit_replay_cycle(now_ts=now)
    assert markets[-1]["best_bid_qty"] is None


def test_frozen_files_reject_expansion_and_unknown_data_reads(tmp_path):
    import base64
    import gzip

    path = str(tmp_path / "policy.json")
    files = policy.FrozenFiles(
        {
            path: {
                "size": 1,
                "content_gzip_b64": base64.b64encode(
                    gzip.compress(b"too-long")
                ).decode(),
            }
        }
    )
    with pytest.raises(policy.ReplayInputGap, match="size_mismatch"):
        files.open(path)
    with pytest.raises(policy.ReplayInputGap, match="unrecorded_file_read"):
        files.open(str(tmp_path / "not-recorded"))
