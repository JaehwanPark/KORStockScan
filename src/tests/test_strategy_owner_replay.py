"""First-use research -> verified source -> bounded PREOPEN, without live writes."""

from copy import deepcopy
from datetime import datetime, timedelta
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.engine.scalping import strategy_owner_replay as mod
from src.engine.scalping import strategy_owner_components as owner
from src.engine.lifecycle import avg_down_policy_replay as adapter
from src.engine.automation import operator_policy_succession as succession
from src.engine import threshold_cycle_preopen_apply as preopen
from src.tests.test_strategy_owner_components import (
    profiles,
    economic_report,
    scope as scope,
)
from src.tests.test_score_recovery_net_approval import sign


@pytest.fixture(autouse=True)
def isolate_native_replay_generation(monkeypatch, tmp_path):
    """Keep source generation deterministic; never inspect live raw paths."""
    from src.engine.monitoring import machine_microstructure_attribution as micro
    monkeypatch.setattr(micro, "OBSERVATION_ROOT", tmp_path / "native_observations")
    monkeypatch.setattr(micro, "DEFAULT_SOURCE_EXCLUSION_MANIFEST", tmp_path / "exclusions.json")
    monkeypatch.setattr(micro, "DEFAULT_CANARY_SNAPSHOT_PATH", tmp_path / "canary.json")
    monkeypatch.setattr(micro, "CANARY_DAILY_SNAPSHOT_DIR", tmp_path / "canary_daily")


def test_native_replay_still_rejects_generation_change_with_mock_windows():
    from src.engine.monitoring import machine_microstructure_attribution as micro
    event = entry_owner_event()

    def changing_source(*args):
        micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST.write_text("{}")
        return native_entry_loader(*args)

    result = mod.build_entry_opportunity_replays(event.signal_date, [event],
        evaluated_at=datetime.fromisoformat(event.emitted_at).timestamp() + 181,
        micro_loader=changing_source)
    assert result["native_source"]["reason"] == "native_source_generation_changed_during_replay"
    assert result["rows"][0]["status"] == "source_gap"
    assert result["quantity_leg_events"] == []


def seed(day="2026-09-08", family=owner.PROFIT, ordinal=0):
    values = profiles()
    rules = {k: v for p in values.values() for k, v in p.items()}
    snapshot = {"rules": rules, "schema": adapter.SNAPSHOT_SCHEMA}
    identity = "owner-component-" + owner.digest([day, family, ordinal])
    return {
        "schema": mod.SCHEMA,
        "family": family,
        "profiles": values,
        "score_profile": None,
        "context_sha256": owner.context_fingerprint(SimpleNamespace(**rules)),
        "strategy_owner_replay": {
            "family": family,
            "baseline": values[family],
            "profile": mod.proposal(family, values[family]),
        },
        "source_event_id": identity,
        "position_episode_id": identity,
        "scale_in_decision_id": identity,
        "stock_code": "005930",
        "venue": "KRX",
        "session": "krx_regular",
        "emitted_at": day + "T10:00:00+09:00",
        "pre_add_buy_price": 10000,
        "pre_add_buy_qty": 10,
        "cost_rate": 0.0023,
        "policy_snapshot": snapshot,
        "exit_policy_version": adapter.snapshot_version(snapshot),
        "entry_authority": {"blocked": False},
        "entry_submit_attempt_id": "native-attempt-test",
        "entry_guard_inputs": {},
        "entry_fill_model": "conditional_full_executable_ask_not_broker_receipt",
        **mod.AUTHORITY,
    }


def successful_replay(source, frames, **kwargs):
    assert kwargs["max_provider_calls"] <= mod.MAX_PROVIDER_CALLS
    start = datetime.fromisoformat(source["emitted_at"])
    outcomes = {}
    for key, seconds, net in (("baseline", 600, 20), ("profile", 300, 30)):
        outcomes[key] = {
            "status": "COMPLETED",
            "exit_time": (start + timedelta(seconds=seconds)).isoformat(),
            "net_pnl_krw": net,
            "filled_add_qty": 0,
            "exit_qty": 10,
            "full_policy_evaluation": True,
        }
    result = {
        "state": "paired_exit_complete_source_only",
        "blockers": {},
        "outcomes": outcomes,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "policy_ai_provider_call_count": 1,
    }
    if source["family"] == owner.WEAK:
        outcomes["baseline"].update(
            known_no_entry=True,
            net_pnl_krw=0,
            exit_time=source["emitted_at"],
            exit_qty=0,
        )
    return {**result, "evidence_digest": owner.digest(result)}


def source_book(report_dir=None, families=(owner.PROFIT,)):
    books = []
    # Four first seeds/owner/day, with four distinct days: no synthetic repeat
    # of one episode can satisfy the ten paired-observation floor.
    for day in ("2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"):
        report = economic_report(day)
        example = seed(day)
        for row in report["rows"]:
            row["strategy_owner_profiles"] = profiles()
            row["score_recovery_profile"] = None
            row["strategy_owner_context_sha256"] = example["context_sha256"]
        report = sign(report)
        book = owner.evidence_book(report, day)
        replay = mod.build(
            day,
            [(seed(day, f, i), []) for f in families for i in range(4)],
            executor=successful_replay,
        )
        assert not replay["blocked"], replay
        book["replays"] = {r["id"]: r for r in replay["rows"]}
        book["replay_sources"] = {day: replay["sha256"]}
        if report_dir:
            path = (
                report_dir
                / "main_scalping_lifecycle_paired"
                / f"main_scalping_lifecycle_paired_{day}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report))
            mod._publish(replay, report_dir, day)
        books.append(book)
    return owner.merge_books(books)


def test_terminal_replay_cache_and_generation_are_verified(tmp_path):
    source = seed()
    executor = Mock(side_effect=successful_replay)
    checkpoints = []
    result = mod.build(
        "2026-09-08", [(source, [])], executor=executor, checkpoint=checkpoints.append
    )
    assert len(result["rows"]) == 1 and len(checkpoints) == 2
    reserved = next(iter(checkpoints[0]["attempts"].values()))
    assert reserved["provider_calls"] == 8 and reserved["provider_calls_known"] is False
    mod._publish(result, tmp_path, "2026-09-08")
    assert mod.load(tmp_path, "2026-09-08") == result
    repeated = mod.build("2026-09-08", [(source, [])], executor=executor, cached=result)
    assert repeated["rows"] == result["rows"] and executor.call_count == 1
    changed = mod.build(
        "2026-09-08", [(source, [{"changed": True}])], executor=executor, cached=result
    )
    assert not changed["rows"] and executor.call_count == 1
    assert (
        next(iter(changed["blocked"].values()))["state"]
        == "terminal_first_attempt_not_retried"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_effect", True),
        ("broker_order_forbidden", False),
        ("schema", "old"),
        ("context_sha256", "bad"),
        ("cost_rate", None),
        ("cost_rate", float("nan")),
        ("pre_add_buy_qty", -1),
        ("pre_add_buy_price", 0),
        ("emitted_at", "2026-09-08T10:00:00"),
        ("venue", "UNKNOWN"),
        ("session", "nxt"),
    ],
)
def test_bad_seed_never_reaches_executor(field, value):
    source = seed()
    source[field] = value
    executor = Mock(side_effect=AssertionError("invalid source must not execute"))
    result = mod.build("2026-09-08", [(source, [])], executor=executor)
    assert not result["rows"] and result["blocked"] and not executor.called


def test_terminal_failure_is_not_retried_or_given_free_budget():
    executor = Mock(side_effect=RuntimeError("unknown provider result"))
    result = mod.build("2026-09-08", [(seed(), [])], executor=executor)
    assert next(iter(result["attempts"].values()))["provider_calls"] == 8
    repeated = mod.build("2026-09-08", [(seed(), [])], executor=executor, cached=result)
    assert executor.call_count == 1 and not repeated["rows"]
    second = Mock(side_effect=successful_replay)
    mod.build("2026-09-08", [(seed(ordinal=1), [])], executor=second, cached=result)
    assert second.call_args.kwargs["max_provider_calls"] == 0


@pytest.mark.parametrize(
    "mutation",
    ["unbound_digest", "cost_missing", "foreign_day", "add_fill", "authority"],
)
def test_partial_or_unbound_replay_never_enters_economics(mutation):
    def executor(source, frames, **kwargs):
        result = successful_replay(source, frames, **kwargs)
        if mutation == "cost_missing":
            result["outcomes"]["profile"]["net_pnl_krw"] = None
        elif mutation == "foreign_day":
            result["outcomes"]["profile"]["exit_time"] = "2026-09-09T10:00:00+09:00"
        elif mutation == "add_fill":
            result["outcomes"]["profile"]["filled_add_qty"] = 1
        elif mutation == "authority":
            result["actual_order_submitted"] = True
        result["evidence_digest"] = owner.digest(
            {k: v for k, v in result.items() if k != "evidence_digest"}
        )
        if mutation == "unbound_digest":
            result["evidence_digest"] = "f" * 64
        return result

    result = mod.build("2026-09-08", [(seed(), [])], executor=executor)
    assert not result["rows"] and result["blocked"]


def test_collect_preserves_identity_and_rejects_conflicting_seed():
    value = seed()
    event = {
        "stage": mod.SEED_STAGE,
        "owner_component_seed": json.dumps(value),
        "source_event_id": value["source_event_id"],
        "decision_authority": "source_only_owner_component_replay",
        "emitted_at": value["emitted_at"],
        "stock_code": value["stock_code"],
        **mod.AUTHORITY,
    }
    assert mod.collect([event], "2026-09-08") == [(value, [])]
    other = deepcopy(value)
    other["cost_rate"] = 0.003
    assert not mod.collect(
        [event, {**event, "owner_component_seed": other}], "2026-09-08"
    )
    assert not mod.collect([{**event, "actual_order_submitted": True}], "2026-09-08")


def test_replay_alone_or_small_daily_real_sample_cannot_start_canary():
    book = source_book()
    policy = mod.first_use_policies(
        book, owner.PROFIT, profiles()[owner.PROFIT], "2026-09-14"
    )
    assert len(policy) == 1 and owner.valid_canary(policy[0], "2026-09-14")
    assert not owner.valid_canary(policy[0], "2026-09-21")
    assert not mod.first_use_policies(
        {**book, "rows": {}}, owner.PROFIT, profiles()[owner.PROFIT], "2026-09-14"
    )
    one_day = {k: r for k, r in book["rows"].items() if r["date"] == "2026-09-08"}
    assert not mod.first_use_policies(
        {**book, "rows": one_day}, owner.PROFIT, profiles()[owner.PROFIT], "2026-09-14"
    )
    assert not mod.first_use_policies(
        book,
        owner.PROFIT,
        profiles()[owner.PROFIT],
        "2026-09-21",
        [policy[0]["trial_id"]],
    )
    for r in book["rows"].values():
        r["net"] = -1
    assert not mod.first_use_policies(
        book, owner.PROFIT, profiles()[owner.PROFIT], "2026-09-14"
    )


def test_exact_book_preopen_export_canary_consumption_expiry_and_no_rearm(
    scope, tmp_path, monkeypatch
):
    runtime, locks, lock_rows = scope
    reports = tmp_path / "reports"
    book = source_book(reports)
    assert (
        owner.verify_research(book, reports, "2026-09-14")["replays"] == book["replays"]
    )
    monkeypatch.setattr(preopen, "REPORT_DIR", reports)

    def publish(day):
        selected, decisions, env = preopen._select_auto_apply_candidates(
            [],
            ai_review={},
            require_ai=True,
            target_date=day,
            operator_locks=lock_rows,
            strategy_owner_component_economics=book,
        )
        preopen._write_runtime_env(
            day,
            {
                "source_date": "2026-09-11",
                "auto_apply_selected": selected,
                "auto_apply_decisions": decisions,
            },
            env,
        )
        manifest = json.loads(
            (runtime / f"threshold_runtime_env_{day}.json").read_text()
        )
        return manifest, succession.validate_receipt(manifest, runtime, locks)

    manifest, exports = publish("2026-09-14")
    profit = next(
        r
        for r in manifest["strategy_owner_components"]["components"]
        if r["family"] == owner.PROFIT
    )
    assert (
        profit["state"] == "first_use_bounded_canary"
        and len(profit["trial_history"]) == 1
    )
    rules = SimpleNamespace(**seed()["policy_snapshot"]["rules"])
    state = owner.runtime_state(
        rules,
        venue="KRX",
        session="krx_regular",
        environment=exports,
        today="2026-09-14",
    )
    assert state["status"] == "first_use_bounded_canary" and state[
        "applied_families"
    ] == [owner.PROFIT]
    assert (
        state["profiles"][owner.PROFIT]["SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC"]
        == 1500
    )
    repeated, _ = publish("2026-09-14")
    for before, after in zip(
        manifest["strategy_owner_components"]["components"],
        repeated["strategy_owner_components"]["components"],
    ):
        assert before["policies"] == after["policies"]
        assert before["trial_history"] == after["trial_history"]
    carried, _ = publish("2026-09-17")
    assert any(
        r["policies"] for r in carried["strategy_owner_components"]["components"]
    )
    expired, env = publish("2026-09-21")
    assert not any(
        r["policies"] for r in expired["strategy_owner_components"]["components"]
    )
    assert (
        owner.runtime_state(
            rules,
            venue="KRX",
            session="krx_regular",
            environment=env,
            today="2026-09-21",
        )["status"]
        == "baseline"
    )
    renewed, _ = publish("2026-09-22")
    assert not any(
        r["policies"] for r in renewed["strategy_owner_components"]["components"]
    )


def test_two_first_use_candidates_cannot_invalidate_each_others_context(scope):
    runtime, locks, lock_rows = scope
    _, decisions, _ = succession.prepare_components(
        lock_rows,
        {},
        runtime,
        locks,
        "2026-09-14",
        source_book(families=(owner.WEAK, owner.PROFIT)),
    )
    assert all(d["strategy_owner_component"]["policies"] for d in decisions)
    succession.reconcile_component_changes(decisions)
    rows = {d["family"]: d["strategy_owner_component"] for d in decisions}
    assert rows[owner.WEAK]["policies"]
    assert (
        not rows[owner.PROFIT]["policies"] and not rows[owner.PROFIT]["trial_history"]
    )
    assert rows[owner.PROFIT]["state"] == "other_component_change_deferred"


def test_changed_replay_generation_cannot_be_reused_by_preopen(tmp_path):
    book = source_book(tmp_path)
    value = mod.load(tmp_path, "2026-09-08")
    value["rows"][0]["arms"][1]["net"] += 1
    mod._publish(mod._signed(value), tmp_path, "2026-09-08")
    with pytest.raises(ValueError, match="replay_generation_changed"):
        owner.verify_research(book, tmp_path, "2026-09-14")


@pytest.mark.parametrize("family", [owner.WEAK, owner.PROFIT])
def test_isolated_current_holding_guard_is_preserved_for_both_arms(family):
    from src.tests.test_avg_down_policy_replay import exit_fixture
    from src.engine import sniper_state_handlers as handlers

    observation, frames = exit_fixture()
    observation["strategy_owner_replay"] = {
        "family": family,
        "baseline": profiles()[family],
        "profile": mod.proposal(family, profiles()[family]),
    }
    observation["entry_guard_inputs"] = {
        "strategy": "SCALPING",
        "stock": {"strategy": "SCALPING"},
        "latency_gate": {
            "latency_state": "CAUTION",
            "decision": "ALLOW_NORMAL",
            "conditional_1tick_real_override_context": {"buy_pressure_ok": True},
        },
        "pre_ai_fields": {"strength_momentum_risk_state": "weak_momentum_context"},
        "guard_fields": {},
        "orderbook_fields": {"orderbook_micro_state": "neutral"},
        "microstructure_fields": {},
    }
    before = handlers.TRADING_RULES
    result = adapter.isolated_replay(observation, frames)
    assert "adapter_error" not in result, result
    assert result["state"] == "paired_exit_complete_source_only", result
    assert set(result["outcomes"]) == {"baseline", "profile"}
    assert all(r["filled_add_qty"] == 0 for r in result["outcomes"].values())
    assert (
        result["actual_order_submitted"] is False and handlers.TRADING_RULES is before
    )
    if family == owner.WEAK:
        assert result["outcomes"]["baseline"]["known_no_entry"] is True
        assert result["outcomes"]["profile"]["net_pnl_krw"] < 0


@pytest.mark.parametrize("depth_shape", ["top", "nested"])
def test_live_seed_roundtrips_string_wire_and_keeps_original_position(
    monkeypatch, depth_shape
):
    from src.engine.scalping import avg_down_replay_capture as capture

    base = seed(family=owner.WEAK)
    epoch = datetime.fromisoformat(base["emitted_at"]).timestamp()
    prepared = {k: base[k] for k in ("policy_snapshot", "exit_policy_version")}
    prepared.update(
        replay_capture_state="armed_source_only",
        initial_policy_state={},
        replay_start_sequence=0,
    )
    monkeypatch.setattr(capture, "prepare", lambda *args, **kwargs: deepcopy(prepared))
    registered = Mock()
    monkeypatch.setattr(capture, "register", registered)
    ai_state = Mock()
    monkeypatch.setattr(capture, "record_ai_state", ai_state)
    monkeypatch.setattr(mod, "_SEED_COUNTS", {})
    stock = {
        "id": 1,
        "code": "005930",
        "name": "TEST",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "venue": "KRX",
        "market_session_bucket": "krx_regular",
        "date": datetime.fromtimestamp(epoch),
    }
    events = []

    def emit(pipeline, name, code, stage, *, fields):
        assert name == "TEST" and code == "005930"
        events.append(
            {
                "stage": stage,
                "stock_code": code,
                "emitted_at": "2026-09-08T10:00:00",
                "fields": {str(k): str(v) for k, v in fields.items()},
            }
        )
        return {"structured_append_succeeded": True}

    handlers = SimpleNamespace(
        _is_any_simulated_position=lambda *a: False,
        _strategy_owner_component_state=lambda s: {
            "profiles": profiles(),
            "context_sha256": base["context_sha256"],
            "applied_families": [],
        },
        submit_attempt_fields=lambda *a: {"entry_submit_attempt_id": "attempt1"},
        _build_quote_consistency_fields=lambda *a, **k: (
            {
                "quote_consistency_state": "single_source",
                "quote_consistency_reason": "ws_only_fresh",
            },
            9990,
            10000,
            9990,
        ),
        get_trade_cost_rate=lambda: 0.0023,
        emit_pipeline_event=emit,
    )
    kwargs = {
        "now_ts": epoch,
        "ws_data": {"best_ask": 10000, "best_ask_qty": 100, "last_ws_update_ts": epoch},
        "entry": {
            "authority": {"blocked": False},
            "ai_engine": handlers,
            "planned_orders": [{"qty": 10, "price": 10000}],
            "order_type_code": "00",
            "guard_inputs": {"stock": stock},
        },
    }
    if depth_shape == "nested":
        kwargs["ws_data"].pop("best_ask_qty")
        kwargs["ws_data"]["orderbook"] = {"asks": [{"price": 10000, "volume": 100}]}
    mod.observe_seed(handlers, stock, "005930", **kwargs)
    assert stock["status"] == "WATCHING" and "buy_qty" not in stock
    assert stock["_strategy_owner_replay_capture_state"] == "armed_source_only"
    assert registered.call_count == 1 and len(mod.collect(events, "2026-09-08")) == 1
    ai_state.assert_called_once_with("005930", handlers)
    handlers.submit_attempt_fields = lambda *a: {"entry_submit_attempt_id": "retry2"}
    mod.observe_seed(handlers, stock, "005930", **kwargs)
    assert registered.call_count == 1


def test_capture_register_rechecks_capacity_after_prepare(monkeypatch):
    from src.engine.scalping import avg_down_replay_capture as capture

    monkeypatch.setattr(
        capture, "_ACTIVE", {str(i): {} for i in range(capture.MAX_ACTIVE)}
    )
    monkeypatch.setattr(capture, "_SEEN", set())
    capture.register(
        episode="new",
        source_id="new",
        decision_id="new",
        code="005930",
        venue="KRX",
        now_ts=1,
        fields={
            "replay_capture_state": "armed_source_only",
            "exit_policy_version": "x",
        },
    )
    assert len(capture._ACTIVE) == capture.MAX_ACTIVE and "new" not in capture._ACTIVE


def test_nonterminal_checkpoint_cannot_become_first_use_evidence(tmp_path):
    checkpoints = []
    mod.build(
        "2026-09-08",
        [(seed(), [])],
        executor=successful_replay,
        checkpoint=checkpoints.append,
    )
    mod._publish(checkpoints[0], tmp_path, "2026-09-08")
    assert mod.load(tmp_path, "2026-09-08") is None
    assert mod.load(tmp_path, "2026-09-08", require_terminal=False)["attempts"]


def test_current_score_cohort_is_required_for_canary_and_real_research():
    book = source_book()
    for row in book["rows"].values():
        row["score_profile"] = {"different": "cohort"}
    assert not mod.first_use_policies(
        book, owner.PROFIT, profiles()[owner.PROFIT], "2026-09-14"
    )


def test_real_no_edge_terminates_canary_before_expiry(scope):
    runtime, locks, lock_rows = scope
    book = source_book()
    _, decisions, env = succession.prepare_components(
        lock_rows, {}, runtime, locks, "2026-09-14", book
    )
    preopen._write_runtime_env(
        "2026-09-14",
        {
            "source_date": "2026-09-11",
            "auto_apply_selected": [],
            "auto_apply_decisions": decisions,
        },
        env,
    )
    previous = json.loads(
        (runtime / "threshold_runtime_env_2026-09-14.json").read_text()
    )
    for day in ("2026-09-14", "2026-09-15"):
        book["sources"][day] = "a" * 64
        for i in range(12):
            actual = deepcopy(next(iter(book["rows"].values())))
            actual["date"] = day
            actual["profiles"][owner.PROFIT] = mod.proposal(
                owner.PROFIT, profiles()[owner.PROFIT]
            )
            actual["net"] = -10
            book["rows"][day + str(i)] = actual
    _, decisions, _ = succession.prepare_components(
        lock_rows, previous, runtime, locks, "2026-09-16", book
    )
    profit = next(
        d["strategy_owner_component"] for d in decisions if d["family"] == owner.PROFIT
    )
    assert not profit["policies"] and not profit["previous_policies"]
    assert len(profit["trial_history"]) == 1
    assert profit["state"] == "first_use_canary_terminal_baseline_retained"


def test_lost_pinned_replay_source_cannot_carry_first_use_canary(scope):
    runtime, locks, lock_rows = scope
    book = source_book()
    _, decisions, env = succession.prepare_components(
        lock_rows, {}, runtime, locks, "2026-09-14", book
    )
    preopen._write_runtime_env(
        "2026-09-14",
        {
            "source_date": "2026-09-11",
            "auto_apply_selected": [],
            "auto_apply_decisions": decisions,
        },
        env,
    )
    previous = json.loads(
        (runtime / "threshold_runtime_env_2026-09-14.json").read_text()
    )
    book["replay_sources"].clear()
    _, decisions, _ = succession.prepare_components(
        lock_rows, previous, runtime, locks, "2026-09-15", book
    )
    assert not any(d["strategy_owner_component"]["policies"] for d in decisions)


def test_crash_reservation_precedes_executor_and_prevents_duplicate_request():
    checkpoints = []

    def interrupted(*args, **kwargs):
        assert (
            checkpoints
            and next(iter(checkpoints[0]["attempts"].values()))["provider_calls"] == 8
        )
        raise SystemExit("simulated worker/process interruption")

    with pytest.raises(SystemExit):
        mod.build(
            "2026-09-08",
            [(seed(), [])],
            executor=interrupted,
            checkpoint=checkpoints.append,
        )
    executor = Mock(side_effect=AssertionError("unknown paid attempt must not repeat"))
    result = mod.build(
        "2026-09-08", [(seed(), [])], executor=executor, cached=checkpoints[0]
    )
    assert not executor.called and not result["rows"]
    assert (
        next(iter(result["blocked"].values()))["first_result"]
        == "reserved_inflight_unknown_request_outcome"
    )


def test_seed_snapshot_is_not_duplicated_into_text_payload():
    from src.utils.pipeline_event_logger import _project_fields_for_text

    fields = {
        "source_event_id": "native-id",
        "owner_component_seed": "large-frozen-state" * 1000,
    }
    projected = _project_fields_for_text(mod.SEED_STAGE, fields)
    assert "owner_component_seed" not in projected
    assert (
        fields["owner_component_seed"] and projected["source_event_id"] == "native-id"
    )


@pytest.mark.parametrize("offset,blocked", [(-1, False), (1, True)])
def test_market_regime_cutoff_without_prior_real_holding_inputs(offset, blocked):
    from src.tests.test_avg_down_policy_replay import policy_fixture

    # Exercise the consumer of regime data, not an emergency exit that correctly
    # preempts it without requiring unrelated context.
    observation, frames = policy_fixture()
    for frame in frames:
        frame["market"]["market_regime"] = "BEAR"
        frame["market"]["market_regime_observed_at"] = (
            datetime.fromisoformat(frame["emitted_at"]).timestamp() + offset
        )
        frame["market"].pop("recorded_inputs", None)
    result = adapter.isolated_replay(observation, frames)
    if blocked:
        assert result["state"] != "paired_exit_complete_source_only"
        assert any(
            v == "future_market_regime_input" for v in result["blockers"].values()
        ), result
    else:
        assert "adapter_error" not in result, result
        assert set(result["blockers"].values()) == {"pending_exit_outcome"}, result


def entry_seed(day='2026-09-14', ordinal=0, *, profile='strong_1tick_pressure', bps=11, anchor=10020):
    plan = dict(valid=True, blockers=[], total_qty=10, deferred_probe_residual_qty=0,
        scanner_promotion_id=f'promotion-{day}-{ordinal}', action_receipt_id=f'attempt-{day}-{ordinal}',
        effective_venue='KRX', market_session_bucket='KRX_REGULAR', policy_bundle_hash='a' * 64,
        quantity_policy_version='qty-original', split_policy_version='leg-original',
        price_policy_sha256='c' * 64, price_plan_sha256='d' * 64,
        legs=[dict(qty=10, numeric_price=10000, execution_phase='immediate')])
    clock = datetime.fromisoformat(day + 'T10:00:00+09:00').timestamp() + ordinal * 240
    return mod.freeze_entry_opportunity(plan, stock_code='005930', observed_at=clock,
        profile=profile, profile_bps=bps, anchor_price=anchor)


def entry_native_path(seed):
    from src.tests.test_machine_microstructure_attribution import _depth_row, _micro_row
    start = datetime.fromisoformat(seed['observed_at'])
    depths, trades = [], []
    for i in range(181):
        at = (start + timedelta(seconds=i)).isoformat()
        d = _depth_row('005930', at)
        bid, ask = (10000, 10010) if i < 30 else (10040, 10050)
        d.update(source_sequence=i + 1, series_sequence=i + 1,
                 best_bid=bid, best_ask=ask, bid_levels=[[1, bid, 1000]], ask_levels=[[1, ask, 800]])
        depths.append(d)
        if i <= 10:
            t = _micro_row('005930', at, 10100, venue='KRX', session='KRX_REGULAR')
            t.update(source_sequence=i + 1, series_sequence=i + 1)
            trades.append(t)
    return depths, trades


def entry_replay(seed):
    depths, trades = entry_native_path(seed)
    return mod.replay_entry_opportunity(seed, depths, trades, source_ready=True,
        evaluated_at=datetime.fromisoformat(seed['observed_at']).timestamp() + 181)


def test_entry_union_prices_replay_no_fill_and_registered_marketable_price():
    seed = entry_seed()
    original = deepcopy(seed)
    result = entry_replay(seed)
    assert seed == original
    assert result['status'] == 'completed_source_only'
    assert result['price_arms']['11']['modeled_outcome'] == 'supported_no_fill'
    assert 0 < result['price_arms']['10']['net_return_pct'] < 0.1
    assert result['price_arms']['10']['actual_fill_evidence'] is False
    assert result['actual_order_submitted'] is False
    assert len(result['arms']) == 4


@pytest.mark.parametrize('defect', ['gap', 'epoch', 'depth', 'passive_touch', 'scope', 'source'])
def test_entry_replay_rejects_unsupported_fill_exit_or_native_window(defect):
    seed = entry_seed()
    depths, trades = entry_native_path(seed)
    if defect == 'gap':
        del depths[10:15]
    elif defect == 'epoch':
        depths[10]['sequence_epoch'] = 2
    elif defect == 'depth':
        depths[0]['best_ask_qty'] = 1
        depths[0]['ask_levels'][0][2] = 1
    elif defect == 'passive_touch':
        trades[3]['trade_price'] = 10000
    elif defect == 'scope':
        depths[5]['venue'] = 'NXT'
    result = mod.replay_entry_opportunity(seed, depths, trades,
        source_ready=defect != 'source', evaluated_at=datetime.fromisoformat(seed['observed_at']).timestamp() + 181)
    assert result['status'] == 'source_gap'
    assert result['arms'] is None
    assert result['price_arms'] is None


def test_price_union_small_positive_pair_recomputed_by_final_consumer():
    rows = [entry_replay(entry_seed(day, i)) for day in ['2026-09-14', '2026-09-15'] for i in range(10)]
    selected = mod.select_entry_price_replay(rows, eligible_count=20,
        source_counts={'2026-09-14': 10, '2026-09-15': 10})
    assert len(selected) == 1
    proof = selected[0]
    assert proof['selected_bps'] == 10
    assert proof['holdout_dates'] == ['2026-09-15']
    assert mod.entry_price_selection_evidence_valid(proof)
    forged = deepcopy(proof)
    forged['metrics']['modeled_net_profit_krw'] += 1
    assert not mod.entry_price_selection_evidence_valid(forged)
    from src.engine.scalping.entry_execution_sizing_plan import mechanistic_entry_price_authority_valid
    policy = dict(policy_owner='mechanistic_entry_price_resolver', provider_calls=0, ai_price_authority=False,
        candidate_id='mechanistic:strong_1tick_pressure:union-v2', source_date='2026-09-15',
        minimum_cost_adjusted_ev_pct=0.0, exact_terminal_sample_count=20,
        cost_adjusted_ev_pct=proof['metrics']['source_quality_adjusted_ev_pct'],
        price_selection_evidence=proof, runtime_env={'KORSTOCKSCAN_SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS': '10'})
    assert mechanistic_entry_price_authority_valid(policy)
    policy['runtime_env']['KORSTOCKSCAN_SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS'] = '8'
    assert not mechanistic_entry_price_authority_valid(policy)


@pytest.mark.parametrize('other_branch', ['normal', 'unregistered'])
def test_price_union_retains_other_owner_price_branches_without_profile_coverage_bias(other_branch):
    from src.engine.monitoring.research_closed_loop import digest
    rows = []
    for day in ('2026-09-14', '2026-09-15'):
        for i in range(30):
            seed = entry_seed(day, i) if i < 10 else entry_seed(day, i,
                profile='normal', bps=20, anchor=10030)
            if i >= 10 and other_branch == 'unregistered':
                # An original plan outside the registered BPS branch remains incumbent.
                seed['price_candidates'] = {}
                for key in ('profile', 'target_value_key', 'incumbent_bps', 'anchor_price'):
                    seed.pop(key, None)
                seed['seed_sha256'] = digest({k: v for k, v in seed.items() if k != 'seed_sha256'})
            rows.append(entry_replay(seed))
    selected = mod.select_entry_price_replay(rows, eligible_count=60,
        source_counts={'2026-09-14': 30, '2026-09-15': 30})
    assert len(selected) == 1
    proof = selected[0]
    assert proof['changed_profile_paired_sample_count'] == 20
    assert proof['metrics']['paired_sample_count'] == 60
    assert len(proof['paired_rows']) == 60
    assert proof['metrics']['source_quality_adjusted_ev_pct'] == pytest.approx(
        rows[0]['price_arms']['10']['net_return_pct'] / 3)
    assert mod.entry_price_selection_evidence_valid(proof)
    # A real missing-source cohort still fails the same union coverage guard.
    assert not mod.select_entry_price_replay(rows, eligible_count=80,
        source_counts={'2026-09-14': 40, '2026-09-15': 40})


def entry_owner_event(day='2026-09-14', ordinal=0):
    from src.tests.test_entry_execution_sizing_plan import _receipt, _priced
    from src.engine.scalping.entry_execution_sizing_plan import compose_entry_execution_sizing_plan
    from src.engine.sniper_missed_entry_counterfactual import EntryEvent
    seed = entry_seed(day, ordinal)
    clock = datetime.fromisoformat(seed['observed_at']).timestamp()
    receipt = _receipt(evaluation_attempt_id=seed['evaluation_attempt_id'],
        scanner_promotion_id=seed['scanner_promotion_id'], policy_bundle_hash='a' * 64,
        effective_venue='KRX', market_session_bucket='KRX_REGULAR')
    order = _priced({'qty': 10, 'price': 10000, 'order_type_code': '00'})
    order.update(entry_price_current_price=10020, entry_price_captured_at=clock)
    _, fields = compose_entry_execution_sizing_plan(planned_orders=[order], action_receipt=receipt,
        quantity_policy_version='qty-original', split_policy_version='leg-original', expected_total_qty=10,
        replay_context=dict(stock_code='005930', observed_at=clock, profile='strong_1tick_pressure', profile_bps=11))
    assert fields['entry_execution_sizing_plan']['valid']
    assert fields['entry_opportunity_replay_seed']
    return EntryEvent(seed['observed_at'], day, 'Samsung', '005930',
        'entry_execution_sizing_plan', f'row-{ordinal}', fields)


def native_entry_loader(day, root, symbols, anchors, manifest, canary, evaluated_at):
    windows = {}
    for anchor in anchors:
        seed = dict(observed_at=anchor['anchor_at'])
        depths, trades = entry_native_path(seed)
        windows[anchor['anchor_id']] = dict(raw_depth_rows=depths, raw_market_rows=trades)
    return {'source_contract_ready': True}, {}, windows


def test_native_entry_producer_generates_signed_quartets_without_submission():
    from src.engine.scalping.entry_split_order_plan import build_quantity_leg_four_arm_evaluation
    event = entry_owner_event()
    out = mod.build_entry_opportunity_replays(event.signal_date, [event, event],
        evaluated_at=datetime.fromisoformat(event.emitted_at).timestamp() + 181,
        micro_loader=native_entry_loader)
    assert out['counts']['completed'] == 1
    assert out['counts']['excluded']['duplicate_exact_plan'] == 1
    receipt = out['quantity_leg_events'][0]['entry_quantity_leg_four_arm_evaluation']
    assert receipt['source_date'] == event.signal_date
    assert receipt['arms']['incumbent_qty_x_incumbent_leg']['actual_fill_evidence'] is False
    evaluation = build_quantity_leg_four_arm_evaluation(out['quantity_leg_events'])
    assert evaluation['complete_exact_attempt_count'] == 1
    assert evaluation['exact_attempt_join_coverage'] == 1
    assert evaluation['status'] == 'evidence_pending_or_blocked'


def test_native_entry_producer_quarantines_conflicts_and_retains_missing_population():
    event = entry_owner_event()
    conflicting = deepcopy(event)
    conflicting.fields['entry_opportunity_replay_seed']['candidate_qty'] = 8
    from src.engine.monitoring.research_closed_loop import digest
    seed = conflicting.fields['entry_opportunity_replay_seed']
    seed['seed_sha256'] = digest({k: v for k, v in seed.items() if k != 'seed_sha256'})
    missing = deepcopy(event)
    missing.record_id = 'missing'
    missing.fields.pop('entry_opportunity_replay_seed')
    out = mod.build_entry_opportunity_replays(event.signal_date, [event, conflicting, missing],
        evaluated_at=datetime.fromisoformat(event.emitted_at).timestamp() + 181,
        micro_loader=native_entry_loader)
    assert out['counts']['raw_plan_rows'] == 3
    assert sum(out['counts']['raw_row_disposition'].values()) == 3
    assert out['counts']['raw_row_disposition']['conflicting_rows'] == 2
    assert out['counts']['excluded']['conflicting_exact_plan'] == 1
    assert out['counts']['excluded']['original_plan_or_frozen_seed_missing_or_invalid'] == 1
    assert out['quantity_leg_events'] == []


def test_price_replay_allocation_keeps_overlap_rows_without_summing_capital():
    rows = [entry_replay(entry_seed(day, 0)) for day in ['2026-09-14', '2026-09-15'] for _ in range(10)]
    # Different real attempts, same source time: one common research reservation.
    from src.engine.monitoring.research_closed_loop import digest
    for i, row in enumerate(rows):
        row['seed']['evaluation_attempt_id'] += f'-{i}'
        row['seed']['seed_sha256'] = digest({k: v for k, v in row['seed'].items() if k != 'seed_sha256'})
        row['seed_sha256'] = row['seed']['seed_sha256']
        row['replay_sha256'] = digest({k: v for k, v in row.items() if k != 'replay_sha256'})
    proof = mod.select_entry_price_replay(rows, eligible_count=20,
        source_counts={'2026-09-14': 10, '2026-09-15': 10})[0]
    assert proof['metrics']['paired_sample_count'] == 20
    one = rows[0]['price_arms']['10']['net_pnl_krw']
    assert proof['metrics']['modeled_net_profit_krw'] == pytest.approx(2 * one)


def test_latest_valid_source_without_complete_outcomes_cannot_be_skipped():
    rows = [entry_replay(entry_seed(day, i)) for day in ['2026-09-14', '2026-09-15'] for i in range(10)]
    census = {'2026-09-14': 10, '2026-09-15': 10, '2026-09-17': 1}
    assert mod.select_entry_price_replay(rows, eligible_count=21, source_counts=census) == []
    census.pop('2026-09-17')
    proof = mod.select_entry_price_replay(rows, eligible_count=20, source_counts=census)[0]
    assert mod.entry_price_selection_evidence_valid(proof)
    proof['source_counts']['2026-09-17'] = 1
    assert not mod.entry_price_selection_evidence_valid(proof)


@pytest.mark.parametrize('census', [None, {'2026-09-14': 0, '2026-09-15': 20},
    {'2026-09-14': 9, '2026-09-15': 11}, {'2026-09-15': 20}])
def test_price_union_requires_original_per_date_eligible_population(census):
    rows = [entry_replay(entry_seed(day, i)) for day in
        ['2026-09-14', '2026-09-15'] for i in range(10)]
    assert mod.select_entry_price_replay(rows, eligible_count=20, source_counts=census) == []
    proof = mod.select_entry_price_replay(rows, eligible_count=20,
        source_counts={'2026-09-14': 10, '2026-09-15': 10})[0]
    # Even a recomputed digest cannot make a shifted/absent census authoritative.
    from src.engine.monitoring.research_closed_loop import digest
    proof['source_counts'] = census
    proof['evidence_sha256'] = digest({k: v for k, v in proof.items() if k != 'evidence_sha256'})
    assert not mod.entry_price_selection_evidence_valid(proof)


@pytest.mark.parametrize('profile,other_profile', [('favorable_micro', 'favorable_wide_micro'),
    ('favorable_wide_micro', 'favorable_micro')])
def test_price_union_shared_env_profiles_consume_only_the_selected_profile(monkeypatch, profile, other_profile):
    from src.engine.scalping import entry_execution_sizing_plan as sizing
    rows = [entry_replay(entry_seed(day, i, profile=profile)) for day in
        ['2026-09-14', '2026-09-15'] for i in range(10)]
    proof = mod.select_entry_price_replay(rows, eligible_count=20,
        source_counts={'2026-09-14': 10, '2026-09-15': 10})[0]
    monkeypatch.setattr(sizing, 'runtime_mechanistic_entry_price_policy',
        lambda: ({'price_selection_evidence': proof}, 'loaded'))
    scope = dict(venue='KRX', session='KRX_REGULAR', policy_bundle_sha256='a' * 64)
    assert sizing.scoped_entry_price_bps(profile, 10, **scope) == 10
    # Both profiles share the env key, but the replay left the other unchanged.
    assert sizing.scoped_entry_price_bps(other_profile, 10, **scope) == 11


def test_native_leg_control_preserves_original_policy_and_weights():
    event = entry_owner_event()
    seed = event.fields['entry_opportunity_replay_seed']
    assert seed['candidate_leg_control_only'] is True
    assert seed['candidate_leg_policy_version'] == seed['incumbent_leg_policy_version']
    assert seed['candidate_legs'] == seed['legs']
    result = entry_replay(seed)
    ids = ['incumbent_qty_x_incumbent_leg', 'candidate_qty_x_incumbent_leg',
           'incumbent_qty_x_candidate_leg', 'candidate_qty_x_candidate_leg']
    assert result['arms'][ids[0]] == result['arms'][ids[2]]
    assert result['arms'][ids[1]] == result['arms'][ids[3]]


def test_registered_candidate_leg_plan_requires_same_owner_action_and_original_prices():
    event = entry_owner_event()
    plan = event.fields['entry_execution_sizing_plan']
    candidate = deepcopy(plan)
    candidate['split_policy_version'] = 'known-registered-leg-candidate'
    clock = datetime.fromisoformat(event.emitted_at).timestamp()
    args = dict(stock_code='005930', observed_at=clock, candidate_leg_plan=candidate)
    seed = mod.freeze_entry_opportunity(plan, **args)
    assert seed['candidate_leg_control_only'] is False
    assert seed['candidate_leg_policy_version'] == 'known-registered-leg-candidate'
    assert mod._entry_seed_valid(seed)
    candidate['legs'][0]['numeric_price'] += 10
    assert mod.freeze_entry_opportunity(plan, **args) is None
    candidate = deepcopy(plan)
    candidate['action_receipt_id'] = 'other-attempt'
    assert mod.freeze_entry_opportunity(plan, **{**args, 'candidate_leg_plan': candidate}) is None


def test_owner_issued_market_order_zero_keeps_market_semantics_without_price_invention():
    from src.tests.test_entry_execution_sizing_plan import _receipt, _priced
    from src.engine.scalping.entry_execution_sizing_plan import compose_entry_execution_sizing_plan
    from src.engine.sniper_missed_entry_counterfactual import _price_ready_plan
    event = entry_owner_event()
    clock = datetime.fromisoformat(event.emitted_at).timestamp()
    order = _priced({'qty': 10, 'price': 0, 'order_type_code': '03'})
    order.update(entry_price_captured_at=clock, entry_price_current_price=10020)
    _, fields = compose_entry_execution_sizing_plan([order], expected_total_qty=10,
        action_receipt=_receipt(evaluation_attempt_id='market-attempt', scanner_promotion_id='market-promotion',
            policy_bundle_hash='a' * 64, effective_venue='KRX', market_session_bucket='KRX_REGULAR'),
        quantity_policy_version='qty-original', split_policy_version='leg-original',
        replay_context={'stock_code': '005930', 'observed_at': clock,
                        'profile': 'strong_1tick_pressure', 'profile_bps': 11})
    event.fields = fields
    assert _price_ready_plan(event)
    seed = fields['entry_opportunity_replay_seed']
    assert seed['legs'][0]['price'] == 0
    assert seed['legs'][0]['order_type_code'] == '03'
    assert seed['price_candidates'] == {}
    result = entry_replay(seed)
    assert result['status'] == 'completed_source_only'
    assert result['arms']['incumbent_qty_x_incumbent_leg']['modeled_filled_qty'] == 10
    assert result['price_arms'] == {}
    assert result['actual_order_submitted'] is False


def _operating_entry_fixture():
    from src.tests.test_avg_down_policy_replay import exit_fixture
    observation,_=exit_fixture()
    seed=entry_seed('2026-09-04')
    seed['legs'][0]['price']=10010
    seed['price_candidates']={}
    context=dict(order_leg_ttl_sec=[10]*len(seed['legs']),order_bundle_hard_ttl_sec=10,order_timeout_owner='explicit_fixture',schema=mod.ENTRY_OPERATING_SCHEMA,frozen_at=seed['observed_at'],
        policy_snapshot=observation['policy_snapshot'],initial_policy_state=observation['initial_policy_state'],
        exit_policy_version=observation['exit_policy_version'],budget_krw=120000.,cost_rate=.0023,
        cost_policy_version='trade_profit_net_realized_pnl:rate=0.0023',
        cost_provenance='frozen_loaded_trade_profit_configuration_not_broker_settlement',
        stress_cost_rate_increment=.0005,max_frame_gap_sec=5.,**mod.AUTHORITY)
    context['policy_snapshot']['environment']['KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE']='2026-09-04'
    context['exit_policy_version']=adapter.snapshot_version(context['policy_snapshot'])
    context['sha256']=owner.digest(context)
    seed['operating_contract']=context;seed.pop('seed_sha256');seed['seed_sha256']=owner.digest(seed)
    depths,trades=entry_native_path(seed)
    replay=mod.replay_entry_opportunity(seed,depths,trades,evaluated_at=datetime.fromisoformat(seed['observed_at']).timestamp()+181,source_ready=True)
    arm=replay['arms']['incumbent_qty_x_incumbent_leg']
    return seed,arm,depths


def test_operating_entry_executes_existing_full_policy_and_cost_owner():
    from src.engine.trade_profit import calculate_net_realized_pnl
    seed,arm,depths=_operating_entry_fixture()
    for row in depths:
        if row['source_sequence']>1:
            row.update(ws_data=dict(curr=9500,best_bid=9500,best_ask=9510,best_bid_qty=row['best_bid_qty'],best_ask_qty=row['best_ask_qty'],last_ws_update_ts=datetime.fromisoformat(row['exchange_timestamp']).timestamp(),last_realtime_type_ts={'0D':datetime.fromisoformat(row['exchange_timestamp']).timestamp()},quote_stale=False), market_regime='BULL',best_bid=9500,best_ask=9510, bid_levels=[[1,9500,row['best_bid_qty']]], ask_levels=[[1,9510,row['best_ask_qty']]])
    result=mod.replay_operating_entry_arm(seed,arm,depths)
    assert result['status']=='completed_source_only',result
    assert result['net_pnl_krw']==calculate_net_realized_pnl(arm['modeled_entry_vwap'],9500,10,cost_rate=.0023)
    assert result['stress_net_pnl_krw']<=result['net_pnl_krw']
    assert result['capital_krw_minutes']>0 and result['reserve_krw_minutes']>0
    assert result['actual_fill_evidence'] is False and result['broker_order_forbidden'] is True


def test_operating_entry_contract_cannot_copy_an_actual_sell_or_missing_cost():
    seed,arm,depths=_operating_entry_fixture()
    seed['operating_contract']['cost_rate']=None
    result=mod.replay_operating_entry_arm(seed,arm,depths)
    assert result['status']=='source_gap' and result['net_pnl_krw'] is None


def test_initial_entry_only_full_policy_rejects_add_inventory_changes():
    from src.engine.lifecycle.avg_down_replay import replay_exit_paths
    from src.tests.test_avg_down_replay import replay_fixture,decision
    observation,frames=replay_fixture()
    observation.update(entry_split_initial_only=True,route_replay={'ENTRY':dict(should_add=False,route_evaluation_complete=True)})
    def adds(state,frame,policy,input_digest):
        return decision(state,frame,policy,input_digest,action='ADD')
    result=replay_exit_paths(observation,frames,full_exit_evaluator=adds)
    assert result['state']=='paired_exit_replay_blocked' and not result['outcomes']


def test_operating_pending_entry_inventory_is_not_assumed_cancelled():
    seed,arm,depths=_operating_entry_fixture()
    for qty,reason in [(0,'zero_fill'),(5,'partial_pending')]:
        candidate={**arm,'modeled_filled_qty':qty,'modeled_fill_events':[] if not qty else [dict(at=seed['observed_at'],qty=qty,price=10010,reserved_price=10010)]}
        result=mod.replay_operating_entry_arm(seed,candidate,depths)
        assert result['status']=='unsupported_scope' and reason in result['blocker']
        assert result['net_pnl_krw'] is None and result['closure_test']
