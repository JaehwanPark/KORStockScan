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
