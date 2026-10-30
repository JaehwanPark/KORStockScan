"""Diagnostic lifecycle, source-only labels and readiness; no broker/provider I/O."""

from collections import OrderedDict, deque
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from types import SimpleNamespace
import json
import threading
import pytest

from src.engine.monitoring import runtime_performance as R
from src.engine.scalping import reversal_source_diagnostics as D
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_shared_ledger as L
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal as K
from src.scanners.zero_base_discovery_queue import DiscoveryQueue
from src.engine.scalping.zero_base_probe import consumer_readiness

T = datetime(2026, 10, 12, 10, tzinfo=K.KST).timestamp()


def quote(seq, stamp=None, price=100, valid=True, epoch=1):
    return [
        T + seq if stamp is None else stamp,
        epoch,
        seq,
        price,
        price,
        price,
        10,
        1,
        valid,
        0,
        0,
    ]


@pytest.fixture
def native(monkeypatch):
    for name in ("_READY", "_SELECTED_READY", "_LIFECYCLE_PENDING"):
        monkeypatch.setattr(R, name, OrderedDict())
    for name in ("_ACTIVE_SELECTED", "_LIFECYCLE_EVICTED"):
        monkeypatch.setattr(R, name, {})
    monkeypatch.setattr(
        R, "_SELECTED_EVICTED", dict(claimed=0, expired_before_claim=0, unobservable=0)
    )
    monkeypatch.setattr(R, "_LIFECYCLE_APPEND_DROPPED", 0)
    monkeypatch.setattr(R, "_LIFECYCLE_SINK", None)
    monkeypatch.setattr(
        R, "_MAIN_PHASE", dict(name="not_observed", code=None, epoch=None, perf=None)
    )
    monkeypatch.setattr(
        R,
        "_COVERAGE",
        {kind: dict(ready=0, claimed=0) for kind in ("fixed_watch", "other")},
    )
    monkeypatch.setattr(R.time, "time", lambda: T + 1)
    band = C.cell_key("123456", "REGULAR", 100)
    scope = ("123456", "SOR", "123456_AL", "REGULAR", "2026-10-12", band)
    event = dict(
        epoch=T,
        event_id="event",
        signal_id="signal",
        native_epoch=1,
        native_sequence=0,
        symbol="123456",
        source_item="123456_AL",
        venue="SOR",
        market="REGULAR",
        confirmation_price=100,
        branch_signals={
            "first": {"decision_phase": "FIRST_UPTICK", "event_id": "event"}
        },
    )
    ready = dict(event=event, claimed=False)
    state = SimpleNamespace(
        generation="scope",
        ready=[ready],
        legacy=SimpleNamespace(
            turn={"event_id": "event"}, last=quote(0), segment_start=T
        ),
    )
    backend = SimpleNamespace(
        _LOCK=threading.RLock(),
        _STATES={scope: state},
        _GENERATION="family",
        _CLAIMS={},
        _FAMILY=dict(
            schema="continuous_reversal_policy_v6",
            family_sha256="family",
            machine_cells={
                band: {
                    "routes": {
                        "SOR": dict(
                            backend="union_v6",
                            scope_execution_hash="scope",
                            payload={
                                "branches": [
                                    {"branch_id": "first"},
                                    {"branch_id": "momentum"},
                                ]
                            },
                        )
                    }
                }
            },
        ),
    )
    return backend, scope, state, event


def observe(native, at=T):
    backend, scope, *_ = native
    R.record_native_ready(backend, *scope[:4], at)
    return next(iter(R._SELECTED_READY.values()))


def test_selected_projection_preserves_issued_deadline_past_legacy_five(native, monkeypatch):
    from src.engine.scalping import entry_deadline as E
    event = native[3]
    event["registry_generation"] = "scope"
    perf = [10.0]
    monkeypatch.setattr(E.time, "perf_counter", lambda: perf[0])
    E.bind_signal_lifetime(event, dict(schema="entry_signal_lifetime_policy_v1", version="projection", max_signal_age_sec=8.0), live_clock=True)
    perf[0] = 15.0
    row = observe(native, at=T + 6)
    assert row["original_deadline"] == T + 8
    assert R._READY[event["signal_id"]]["selections"][0]["reason"] == "selected"
    assert not row["claimed"] and not native[0]._CLAIMS


def test_raw_first_can_be_ineligible_without_ever_being_a_delivery_miss(native):
    native[2].legacy.turn = None
    before = deepcopy(native[2].ready)
    row = observe(native)
    assert row["terminal"] == "invalidated_before_claim"
    assert row["first_eligible_seen"] is None
    assert native[2].ready == before
    assert R.snapshot()["native_signal_lifecycle"]["count"] == 1


@pytest.mark.parametrize(
    "damage,reason",
    [
        ("band", "price_band_not_selected"),
        ("parent", "carried_backend_not_selected"),
        ("generation", "scope_generation_mismatch"),
        ("branch", "selected_branch_missing"),
        ("missing_cell", "selection_contract_unobservable"),
        (None, "selected"),
    ],
)
def test_raw_ready_selection_keeps_exact_nonselection_evidence(native, damage, reason):
    backend, scope, state, event = native
    if damage == "band":
        other = scope[:-1] + ("other_non_fixed|REGULAR|GE_100000",)
        backend._STATES = {other: state}
    elif damage == "parent":
        backend.R = SimpleNamespace(
            _LOCK=threading.RLock(), _STATES={scope[:-1]: state}, _GENERATION="scope"
        )
        backend._STATES = {}
    elif damage == "generation":
        state.generation = "older-scope"
    elif damage == "branch":
        event["branch_signals"] = {"unselected": {"decision_phase": "FIRST_UPTICK"}}
    elif damage == "missing_cell":
        backend._FAMILY["machine_cells"] = {}
    before = deepcopy(state.ready)
    R.record_native_ready(backend, *scope[:4], T)
    report = R.snapshot()["native_ready_selection"]
    assert report["retained_ready_count"] == 1
    receipt = report["recent"][0]
    assert receipt["signal_id"] == event["signal_id"]
    assert receipt["native_epoch"] == 1 and receipt["native_sequence"] == 0
    assert receipt["selections"][0]["reason"] == reason
    assert receipt["selections"][0]["family_sha256"] == "family"
    assert receipt["selections"][0]["expected_scope"] == scope[-1]
    assert state.ready == before and not backend._CLAIMS
    assert R.snapshot()["selected_native_coverage"]["count"] == int(damage is None)
    # Published views cannot mutate the next diagnostic snapshot.
    receipt["selections"][0]["reason"] = "tampered"
    assert (
        R.snapshot()["native_ready_selection"]["recent"][0]["selections"][0]["reason"]
        == reason
    )


def test_same_tick_raw_scopes_do_not_hide_the_selected_scope(native):
    backend, scope, state, event = native
    other = scope[:-1] + ("other_non_fixed|REGULAR|GE_100000",)
    backend._STATES = {other: deepcopy(state), scope: state}
    R.record_native_ready(backend, *scope[:4], T)
    view = R.snapshot()["native_ready_selection"]
    assert view["retained_ready_count"] == 1
    assert {r["reason"] for r in view["recent"][0]["selections"]} == {
        "price_band_not_selected",
        "selected",
    }
    assert R.snapshot()["selected_native_coverage"]["count"] == 1


def _preclaim_guard_source(native):
    _, scope, _, event = native
    return dict(
        stock=dict(
            id=42,
            watch_origin="MAIN_FIXED_WATCH",
            watch_admission_id="admission",
            watch_generation_id="watch-generation",
            market_session_bucket="krx_regular",
        ),
        code=scope[0],
        ws_data=dict(
            last_realtime_type_item={"0B": scope[2]},
            realtime_type_snapshots_by_route={
                "_AL|krx_nxt_integrated": {
                    "0B": dict(
                        item=scope[2],
                        market_route="krx_nxt_integrated",
                        transport_epoch=event["native_epoch"],
                        route_sequence=event["native_sequence"],
                        observed_epoch=event["epoch"],
                    )
                }
            },
        ),
        reason="extreme_sell_dominant",
        now=T + 0.1,
    )


def test_preclaim_gate_records_actual_blocked_and_clear_visits_without_renewal(native):
    row = observe(native)
    R.acknowledge_native_watch_visit(dict(code=native[1][0]), None, now=T + 0.05)
    args = _preclaim_guard_source(native)
    original = deepcopy(native[2].ready)
    metrics = dict(window_sec=8, window_buy_ratio=0.13, window_net_buy_qty=-23042)
    assert R.record_native_preclaim_gate(**{**args, "reason": ""}) == 0
    assert R.record_native_preclaim_gate(**args, metrics=metrics) == 1
    assert R.record_native_preclaim_gate(**{**args, "now": T + 2}, metrics=metrics) == 1
    assert row["main_preclaim_guard"]["observed_epoch"] == T + 0.1
    assert row["main_preclaim_guard_last"]["observed_epoch"] == T + 2
    assert row["main_preclaim_guard_observed_visits"] == 2
    assert row["main_preclaim_guard"]["metrics"]["window_buy_ratio"] == 0.13
    assert row["main_preclaim_guard"]["metrics"]["window_total_value"] is None
    metrics["window_buy_ratio"] = float("nan")
    assert (
        R.record_native_preclaim_gate(
            **{**args, "reason": "", "now": T + 3}, metrics=metrics
        )
        == 1
    )
    assert row["main_preclaim_guard_clear"]["metrics"]["window_buy_ratio"] is None
    assert (
        row["main_preclaim_guard_clear"]["gate_action"]
        == "continue_to_remaining_guards"
    )
    assert R.record_native_preclaim_gate(**{**args, "reason": "", "now": T + 3.1}) == 0
    assert R.record_native_preclaim_gate(**{**args, "now": T + 2.5}) == 0
    assert R.record_native_preclaim_gate(**{**args, "now": T + 4}) == 1
    assert R.record_native_preclaim_gate(**{**args, "reason": "", "now": T + 5}) == 0
    assert row["main_preclaim_guard_observed_visits"] == 3
    assert row["original_deadline"] == T + 5 and not row["claimed"]
    assert native[2].ready == original
    view = R.snapshot()["native_signal_lifecycle"]["recent"][0]
    view["main_preclaim_guard"]["metrics"]["window_buy_ratio"] = 999
    assert row["main_preclaim_guard"]["metrics"]["window_buy_ratio"] == 0.13


def test_main_phase_aggregate_covers_truncated_tail_without_filling_missing_prefix(
    monkeypatch,
):
    monkeypatch.setattr(
        R,
        "_MAIN_PHASE_HISTORY",
        deque(
            [
                dict(
                    name="target_visit" if i % 2 else "idle_wait",
                    code="123456",
                    perf=float(i),
                )
                for i in range(100)
            ],
            maxlen=256,
        ),
    )
    result = R._phase_window_locked(0.0, 100.0)
    assert result["coverage"] == "complete" and result["truncated"]
    assert len(result["intervals"]) == 32
    assert result["interval_count"] == 100
    assert result["seconds_by_phase"] == {"target_visit": 50.0, "idle_wait": 50.0}
    assert result["observed_seconds"] == 100.0
    assert R._phase_window_locked(-5.0, 100.0)["coverage"] == "prefix_unobserved"


def test_main_preclaim_guard_survives_later_native_invalidation(native):
    row = observe(native)
    R.acknowledge_native_watch_visit(dict(code=native[1][0]), None, now=T + 0.05)
    before = deepcopy(native[2].ready)
    assert R.record_native_preclaim_gate(**_preclaim_guard_source(native)) == 1
    native[2].legacy.turn = {"event_id": "new-low"}
    observe(native, T + 0.4)
    assert row["terminal"] == "invalidated_before_claim"
    assert row["main_preclaim_guard"]["reason"] == "extreme_sell_dominant"
    assert row["main_preclaim_guard"]["source_sequence"] == 0
    assert row["main_preclaim_guard"]["observed_epoch"] == T + 0.1
    assert row["claimed"] is False and native[2].ready == before


@pytest.mark.parametrize(
    "damage",
    [
        "origin",
        "item",
        "epoch",
        "sequence",
        "future",
        "before_signal",
        "deadline",
        "market",
        "no_visit",
        "terminal",
        "claimed",
        "missing_market",
        "missing_routes",
        "bad_item_map",
        "route_conflict",
        "nonreason",
        "ambiguous_tape",
        "changed_bundle",
        "unknown_reason",
    ],
)
def test_preclaim_guard_cannot_join_another_source_or_unvisited_signal(native, damage):
    row = observe(native)
    args = _preclaim_guard_source(native)
    R.acknowledge_native_watch_visit(dict(code=native[1][0]), None, now=T + 0.05)
    tape = args["ws_data"]["realtime_type_snapshots_by_route"][
        "_AL|krx_nxt_integrated"
    ]["0B"]
    if damage == "origin":
        args["stock"]["watch_origin"] = "SCANNER"
    elif damage == "item":
        tape["item"] = "other_AL"
    elif damage == "epoch":
        tape["transport_epoch"] = 2
    elif damage == "sequence":
        tape["route_sequence"] = -1
    elif damage == "future":
        tape["observed_epoch"] = T + 0.2
    elif damage == "before_signal":
        tape["observed_epoch"] = T - 0.1
    elif damage == "deadline":
        args["now"] = T + 6
    elif damage == "market":
        args["stock"]["market_session_bucket"] = "nxt_aftermarket"
    elif damage == "no_visit":
        row["main_queue_first_visit"] = None
    elif damage == "terminal":
        row["terminal"] = "invalidated_before_claim"
    elif damage == "claimed":
        row["claimed"] = True
    elif damage == "missing_market":
        args["stock"].pop("market_session_bucket")
    elif damage == "missing_routes":
        args["ws_data"]["realtime_type_snapshots_by_route"] = []
    elif damage == "bad_item_map":
        args["ws_data"]["last_realtime_type_item"] = []
    elif damage == "route_conflict":
        tape["market_route"] = "krx_only"
    elif damage == "nonreason":
        args["reason"] = {}
    elif damage == "ambiguous_tape":
        args["ws_data"]["realtime_type_snapshots_by_route"]["other"] = {
            "0B": deepcopy(tape)
        }
    elif damage == "changed_bundle":
        row["bundle_sha256"] = "other-bundle"
    elif damage == "unknown_reason":
        args["reason"] = "unknown_guard"
    assert R.record_native_preclaim_gate(**args) == 0
    assert "main_preclaim_guard" not in row


def test_guard_evidence_does_not_prevent_a_later_valid_native_claim(native):
    row = observe(native)
    R.acknowledge_native_watch_visit(dict(code=native[1][0]), None, now=T + 0.05)
    assert R.record_native_preclaim_gate(**_preclaim_guard_source(native)) == 1
    claim = dict(snapshot=[native[3], {}], generation="scope")
    R.record_selected_native_claim(claim, family_sha256="family", now=T + 0.2)
    assert row["claimed"] and row["terminal"] == "claimed"
    assert row["main_preclaim_guard"]["reason"] == "extreme_sell_dominant"


def test_signal_arriving_during_main_visit_retains_its_real_guard(native, monkeypatch):
    row = observe(native)
    monkeypatch.setattr(
        R, "_MAIN_PHASE", dict(name="target_visit", code=native[1][0], epoch=T - 0.1)
    )
    assert row.get("main_queue_first_visit") is None
    assert R.record_native_preclaim_gate(**_preclaim_guard_source(native)) == 1
    assert row["main_preclaim_guard"]["main_visit_basis"] == "current_target_phase"
    assert row["claim_attempt"] is None and row["claimed"] is False


def test_raw_selection_recent_limit_is_explicit_and_keeps_original_counter(native):
    backend, scope, state, event = native
    for i in range(40):
        event["signal_id"] = f"signal-{i}"
        R.record_native_ready(backend, *scope[:4], T)
    report = R.snapshot()["native_ready_selection"]
    assert report["retained_ready_count"] == 40 and len(report["recent"]) == 32
    assert report["recent_truncated"] is True
    assert report["recent"][0]["signal_id"] == "signal-8"
    assert not any(r["claimed"] for r in state.ready)


@pytest.mark.parametrize("market_block", [False, True])
def test_actual_main_guard_reaches_native_lifecycle_writer(
    native, monkeypatch, tmp_path, market_block
):
    from dataclasses import replace
    from src.engine import sniper_state_handlers as H
    from src.tests.test_sniper_scale_in import _DummyDB
    from src.utils.constants import TRADING_RULES
    from src.utils import pipeline_event_logger as E

    monkeypatch.setattr(R.time, "time", lambda: T + 0.1)
    row = observe(native)
    args = _preclaim_guard_source(native)
    R.acknowledge_native_watch_visit(dict(code=args["code"]), None, now=T + 0.05)
    for name in ("COOLDOWNS", "HIGHEST_PRICES", "LAST_AI_CALL_TIMES", "LAST_LOG_TIMES"):
        monkeypatch.setattr(H, name, {})
    monkeypatch.setattr(H, "ALERTED_STOCKS", set())
    monkeypatch.setattr(H, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(H, "DB", _DummyDB())
    monkeypatch.setattr(
        H,
        "TRADING_RULES",
        replace(
            TRADING_RULES,
            SCALP_PRE_AI_SOFT_GATE_ENABLED=True,
            SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=True,
        ),
    )
    momentum = dict(enabled=True, allowed=False, reason="insufficient_history")
    if market_block:
        # Original 005930 2026-10-28 10:50:36.670 guard input. The native
        # identity below is isolated; no live actor/signal is manufactured.
        momentum.update(
            reason="below_strength_base",
            window_sec=8,
            elapsed_sec=5.201,
            window_total_value=1925939,
            window_buy_ratio=0.0257,
            window_exec_buy_ratio=0.0258,
            window_net_buy_qty=-7585,
        )
    reason = "extreme_sell_dominant" if market_block else "insufficient_history"
    action = "baseline_block" if market_block else "source_quality_block"
    monkeypatch.setattr(
        H,
        "evaluate_scalping_strength_momentum",
        lambda *_: momentum,
    )
    monkeypatch.setattr(H, "arm_big_bite_if_triggered", lambda **_: (False, {}))
    monkeypatch.setattr(H, "confirm_big_bite_follow_through", lambda **_: (True, {}))
    monkeypatch.setattr(H, "build_tick_data_from_ws", lambda *_: {})
    stages = []
    monkeypatch.setattr(
        H,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: stages.append((stage, fields)),
    )
    stock = dict(
        args["stock"],
        name="fixed",
        strategy="SCALPING",
        position_tag="SCANNER",
        prob=0.9,
        rt_ai_prob=0.9,
    )
    ws = dict(
        args["ws_data"],
        curr=100,
        v_pw=121.0,
        ask_tot=50000,
        bid_tot=50000,
        open=99,
        fluctuation=1.0,
        last_ws_update_ts=T,
        orderbook={"asks": [{"price": 101}], "bids": [{"price": 100}]},
    )
    H.handle_watching_state(
        stock=stock,
        code=args["code"],
        ws_data=ws,
        admin_id=1,
        now_ts=T + 0.1,
        now_dt=datetime.fromtimestamp(T + 0.1, K.KST),
        radar=SimpleNamespace(get_smart_target_price=lambda price, **_: (price, 0.0)),
        ai_engine=SimpleNamespace(
            analyze_target=lambda *_a, **_kw: pytest.fail("guard must stop AI")
        ),
    )
    fields = dict(stages)["blocked_strength_momentum"]
    assert fields["gate_action"] == action
    assert fields["source_quality_block_reason"] == ("-" if market_block else reason)
    assert fields["market_state_block_reason"] == (reason if market_block else "-")
    assert row["main_preclaim_guard"]["reason"] == reason
    assert row["main_preclaim_guard"]["gate_action"] == action
    assert row["main_preclaim_guard"]["blocker_role"] == (
        "market_state" if market_block else "source_quality"
    )
    assert stock["trade_quality_block_history"][-1]["gate_action"] == action
    assert stock["scalp_pre_ai_gate_context"]["strength_momentum"]["gate_action"] == action
    native[2].legacy.turn = {"event_id": "new-low"}
    observe(native, T + 0.4)
    monkeypatch.setattr(E, "DATA_DIR", tmp_path)
    monkeypatch.setattr(E, "log_info", lambda *_: None)
    R.set_lifecycle_sink(lambda fn, record: (fn(record), {"status": "queued"})[1])
    R.flush_lifecycle()
    records = [
        json.loads(line)
        for path in (tmp_path / "pipeline_events").glob("*.jsonl")
        for line in path.read_text().splitlines()
    ]
    capsule = json.loads(records[-1]["fields"]["native_signal_lifecycle"])
    assert capsule["terminal"] == "invalidated_before_claim"
    assert capsule["main_preclaim_guard"]["reason"] == reason
    assert capsule["main_preclaim_guard"]["gate_action"] == action
    assert capsule["claimed"] is False and not native[2].ready[0]["claimed"]


def test_later_first_invalidation_preserves_valid_interval_and_main_visit(native):
    observe(native)
    R.record_native_visit("123456", "SOR", "123456_AL", "REGULAR", T + 0.2)
    native[2].legacy.turn = {"event_id": "new_low"}
    row = observe(native, T + 0.4)
    assert row["terminal"] == "invalidated_before_claim"
    assert row["main_first_visit"] == T + 0.2
    assert row["transition_interval"] == [T, T + 0.4]


def test_independent_surviving_branch_keeps_native_eligibility(native):
    native[3]["branch_signals"]["momentum"] = {
        "decision_phase": "MOMENTUM_CROSS",
        "event_id": "momentum",
    }
    native[2].legacy.turn = None
    row = observe(native)
    assert row["terminal"] is None
    assert row["branch_survival"] == {"first": False, "momentum": True}


@pytest.mark.parametrize(
    "change,reason",
    [
        ("source", "source_or_guard_blocked_before_claim"),
        ("epoch", "source_or_guard_blocked_before_claim"),
        ("removed", "unobservable"),
    ],
)
def test_source_and_missing_ready_are_not_all_expired(native, change, reason):
    observe(native)
    if change == "source":
        native[2].legacy.last[8] = False
    if change == "epoch":
        native[2].legacy.last[1] = 2
    if change == "removed":
        native[2].ready.clear()
    row = observe(native, T + 0.3)
    assert row["terminal"] == reason


def test_age_only_timeout_remains_unobservable_and_append_is_real(
    native, monkeypatch, tmp_path
):
    observe(native)
    monkeypatch.setattr(R.time, "time", lambda: T + 6)
    counts = R.snapshot()
    assert counts["selected_native_coverage"]["expired_before_claim"] == 1
    assert counts["selected_native_coverage"]["age_only_not_delivery_failure"] is True
    assert counts["native_signal_lifecycle"]["counts"]["unobservable"] == 1
    from src.utils import pipeline_event_logger as E

    monkeypatch.setattr(E, "DATA_DIR", tmp_path)
    monkeypatch.setattr(E, "log_info", lambda *a: None)
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = E.BoundedObservationQueue(executor)
        R.set_lifecycle_sink(queue.submit)
        R.flush_lifecycle()
        assert queue.close(timeout=5)
        assert queue.snapshot()["append_confirmed"] == 1
    records = [
        json.loads(line)
        for path in (tmp_path / "pipeline_events").glob("*.jsonl")
        for line in path.read_text().splitlines()
    ]
    capsule = json.loads(records[-1]["fields"]["native_signal_lifecycle"])
    assert capsule["terminal"] == "unobservable"
    assert capsule["original_deadline"] == T + 5
    assert capsule["process_start_ticks"] == R._PROCESS_START_TICKS
    from src.engine.pipeline_event_summary import execution_projection_identity

    part = next(
        (tmp_path / "threshold_cycle").glob(
            "date=*/family=entry_mechanical_momentum/part-execution-*"
        )
    )
    projection = json.loads(part.read_text().splitlines()[-1])
    assert json.loads(projection["fields"]["native_signal_lifecycle"]) == capsule
    assert projection["execution_source_event_sha256"] == execution_projection_identity(
        projection
    )


def test_claim_joins_exact_native_scope_not_signal_id_alone(native):
    row = observe(native)
    claim = dict(snapshot=[native[3], {}], generation="wrong")
    R.record_selected_native_claim(claim, family_sha256="family", now=T + 0.2)
    assert row["claimed"] is False
    claim["generation"] = "scope"
    R.record_selected_native_claim(claim, family_sha256="other", now=T + 0.2)
    assert row["claimed"] is False
    R.record_selected_native_claim(claim, family_sha256="family", now=T + 0.2)
    assert row["claimed"] and row["claimed_epoch"] == T + 0.2
    assert R.snapshot()["native_signal_lifecycle"]["counts"]["claimed"] == 1


def test_main_phase_clock_explains_delivery_without_changing_native_authority(
    native, monkeypatch
):
    clock = [100.0]
    monkeypatch.setattr(R.time, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(R, "_MAIN_PHASE_HISTORY", deque(maxlen=256))
    monkeypatch.setattr(
        R, "_MAIN_PHASE", dict(name="not_observed", code=None, epoch=None, perf=None)
    )
    R.record_main_phase("target_visit", "other")
    row = observe(native)
    assert row["main_phase_at_first_eligible"]["name"] == "target_visit"
    assert row["first_eligible_perf"] == 100.0
    clock[0] = 100.5
    R.record_main_phase("optional_maintenance")
    clock[0] = 103.0
    R.record_main_phase("idle_wait")
    clock[0] = 103.105
    R.record_main_phase("main_wake")
    B, scope, *_ = native
    R.record_native_visit(*scope[:4], T + 3.105)
    window = row["main_delivery_phase_window"]
    assert window["coverage"] == "complete" and not window["truncated"]
    assert [
        (x["name"], round(x["ended_perf"] - x["started_perf"], 3))
        for x in window["intervals"]
    ] == [("target_visit", 0.5), ("optional_maintenance", 2.5), ("idle_wait", 0.105)]
    assert row["claim_attempt_perf"] - row["first_eligible_perf"] == pytest.approx(
        3.105
    )
    assert (
        row["original_deadline"] == T + 5 and not B._STATES[scope].ready[0]["claimed"]
    )


def test_eviction_and_observation_queue_rejection_are_explicit(native, monkeypatch):
    monkeypatch.setattr(R, "_LIMIT", 2)
    for i in range(3):
        native[3]["signal_id"] = "signal" + str(i)
        observe(native, T + i * 0.1)
    counts = R.snapshot()["native_signal_lifecycle"]
    assert counts["count"] == 3 and counts["counts"]["unobservable"] >= 1
    R.set_lifecycle_sink(lambda *a: {"status": "unavailable"})
    R.flush_lifecycle()
    assert R.snapshot()["native_signal_lifecycle"]["append_admission_dropped"] == 3


def test_compact_predicates_do_not_copy_raw_registration(native):
    B, scope, state, event = native
    claim = dict(
        token="native-token",
        generation="scope",
        backend="operating_v6",
        snapshot=[event, {}],
        source_registration_receipt={
            "sha256": "registration",
            "snapshot": ["large-input"],
        },
    )
    B._CLAIMS["native-token"] = dict(
        scope=scope, snapshot=claim["snapshot"], generation="scope"
    )
    state.legacy.last[1] = 2
    state.legacy.turn = None
    with B._LOCK:
        receipt = D.compact_claim_state(
            B, claim, "family", T + 0.3, "reversal_signal_path_changed"
        )
    assert receipt["branch_survival"]["first"] is False
    assert "native_epoch_matches" in receipt["failed_predicates"]
    assert receipt["registration_sha256"] == "registration"
    assert receipt["scope_execution_hash"] == "scope"
    assert not any(
        k in receipt for k in ("snapshot", "supplied_snapshot", "claim_token")
    )
    assert "large-input" not in json.dumps(receipt)


def test_consumer_readiness_requires_actual_dependencies_and_no_secrets():
    event = threading.Event()
    event.set()
    ws = SimpleNamespace(
        websocket=object(),
        _session_ready=event,
        _stop_event=threading.Event(),
        _market_data_transport_epoch=3,
        uri="wss://api.kiwoom.com/api/dostk/websocket",
    )
    kwargs = dict(
        ws_manager=ws,
        ai_engine=object(),
        token="secret-test",
        enabled=True,
        family_sha256="f",
        now_epoch=T,
    )
    assert consumer_readiness(**kwargs)["ready"]
    for field, value in [
        ("ws_manager", None),
        ("ai_engine", None),
        ("token", ""),
        ("enabled", False),
        ("family_sha256", None),
    ]:
        receipt = consumer_readiness(**dict(kwargs, **{field: value}))
        assert receipt["ready"] is False and "secret-test" not in json.dumps(receipt)
    event.clear()
    assert consumer_readiness(**kwargs)["reason"] == "ws_session_not_ready"


def test_readiness_generation_binds_reconnect_date_policy_and_runtime_objects(
    monkeypatch,
):
    from src.engine.scalping.zero_base_probe import readiness_issue, kiwoom_utils

    monkeypatch.setattr(kiwoom_utils, "KIWOOM_BASE_URL", "https://api.kiwoom.com")
    event = threading.Event()
    event.set()
    ws = SimpleNamespace(
        websocket=object(),
        _session_ready=event,
        _stop_event=threading.Event(),
        _market_data_transport_epoch=3,
        uri="wss://api.kiwoom.com/api/dostk/websocket",
    )
    kwargs = dict(
        ws_manager=ws,
        ai_engine=object(),
        token="never-publish-me",
        enabled=True,
        family_sha256="family",
        now_epoch=T,
    )
    old = consumer_readiness(**kwargs)
    assert (
        readiness_issue(old, consumer_readiness(**dict(kwargs, now_epoch=T + 1))) == ""
    )
    for key, value in [
        ("family_sha256", "new"),
        ("ai_engine", object()),
        ("token", "replaced"),
        ("now_epoch", T + 86400),
    ]:
        new = consumer_readiness(**dict(kwargs, **{key: value}))
        assert readiness_issue(old, new) == "consumer_readiness_generation_changed"
        assert "never-publish-me" not in json.dumps(new)
    ws._market_data_transport_epoch = 4
    assert (
        readiness_issue(old, consumer_readiness(**kwargs))
        == "consumer_readiness_generation_changed"
    )
    ws.uri = "wss://mockapi.kiwoom.com:10000/api/dostk/websocket"
    assert consumer_readiness(**kwargs)["reason"] == "auth_environment_mismatch"


def test_native_wake_only_first_eligibility_and_no_authority(native, monkeypatch):
    event = threading.Event()
    monkeypatch.setattr(R, "_NATIVE_READY_EVENT", event)
    observe(native)
    assert event.is_set() and not native[2].ready[0]["claimed"]
    event.clear()
    for _ in range(10):
        observe(native, T + 0.1)
    assert not event.is_set()
    native[2].legacy.turn = None
    observe(native, T + 0.2)
    assert not event.is_set()


@pytest.fixture
def main_worker(monkeypatch):
    # These worker races do not use the optional scanner/model initializer.
    # Keep the real Main functions without an unrelated model import writing
    # to the source checkout. Unexpected scanner use has no fake success.
    import sys
    from types import ModuleType

    monkeypatch.setitem(
        sys.modules,
        "src.scanners.final_ensemble_scanner",
        ModuleType("src.scanners.final_ensemble_scanner"),
    )
    from src.engine import kiwoom_sniper_v2

    return kiwoom_sniper_v2


def test_worker_rechecks_generation_before_physical_registration(
    monkeypatch, main_worker
):
    main = main_worker

    current = {"ready": True, "runtime_generation": "one"}
    tasks, results = [], []
    monkeypatch.setattr(main, "_zero_base_runtime_enabled", lambda: True)
    monkeypatch.setattr(main, "_zero_base_active_conflict", lambda _: False)
    monkeypatch.setattr(
        main,
        "evaluate_main_bot_control_exclusion",
        lambda _: SimpleNamespace(excluded=False),
    )
    monkeypatch.setattr(
        main,
        "scalping_session_venue_provenance",
        lambda _: {"market_session_regime": "KRX_REGULAR"},
    )
    monkeypatch.setattr(main, "_zero_base_consumer_readiness", lambda: dict(current))
    monkeypatch.setattr(
        main, "_ZERO_BASE_PROBE_EXECUTOR", SimpleNamespace(submit=tasks.append)
    )
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_SLOTS", threading.BoundedSemaphore(5))
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_IN_FLIGHT", set())
    monkeypatch.setattr(
        main, "run_zero_base_probe", lambda *a, **k: pytest.fail("physical worker ran")
    )
    monkeypatch.setattr(
        main, "event_bus", SimpleNamespace(publish=lambda e, p: results.append(p))
    )
    claim = dict(code="123456", route="krx_nxt_integrated", source_sha256="a" * 64)
    main.handle_zero_base_probe_requested(
        dict(claim=claim, candidate=claim, consumer_readiness=dict(current))
    )
    current["runtime_generation"] = "two"
    tasks.pop()()
    assert results[0]["reason"] == "consumer_readiness_generation_changed"
    assert not main._ZERO_BASE_PROBE_IN_FLIGHT
    assert results[-1]["handoff_closed"] is True


def test_branch_descriptor_changes_to_actual_native_band_without_renewing_deadline(
    native, monkeypatch
):
    from src.engine.scalping import reversal_current_backend as current

    B, scope, state, _ = native
    B._FAMILY["machine_cells"][scope[-1]]["routes"]["SOR"]["payload"]["branches"] = [
        C.branch("G1")
    ]
    new_key = C.cell_key("123456", "REGULAR", 30000)
    cell = deepcopy(B._FAMILY["machine_cells"][scope[-1]])
    bid = "manual_path_dca327a873720e53"
    cell["routes"]["SOR"].update(
        scope_execution_hash="new_scope", payload={"branches": [C.branch(bid)]}
    )
    B._FAMILY["machine_cells"][new_key] = cell
    monkeypatch.setattr(current, "backend", lambda: B)
    candidate = SimpleNamespace(
        code="123456", route="krx_nxt_integrated", discovery_price=100
    )
    original = D.residence_requirements(candidate, T)
    B._STATES = {scope[:5] + (new_key,): state}
    state.generation = "new_scope"
    state.legacy.last = quote(20, stamp=T + 60, price=30000)
    state.coverage_snapshot = {bid: "UNKNOWN"}
    state.coverage_identity = tuple(state.legacy.last[:3])
    state.root_previous = {bid: None}
    state._feature_values = {"ret": None}
    state._feature_key = tuple(state.legacy.last[:3])
    result = D.branch_readiness(
        candidate, now=T + 60, deadline=T + 61, original_requirements=original
    )
    assert result["scope_changed"] and result["policy_scope"] == new_key
    assert result["remaining_seconds"] == 1
    row = result["branch_descriptors"][bid]
    assert row["minimum_seconds"] == 61 and row["transition_required"]
    assert (
        row["detector_truth"] == "UNKNOWN" and row["root_condition_truth"] == "UNKNOWN"
    )
    assert row["window_fits_remaining"] is False
    row["minimum_seconds"] = 0
    assert (
        D.residence_requirements(candidate, T, actual_price=30000)["minimum_seconds"]
        == 61
    )
    state.coverage_snapshot = {bid: "TRUE"}
    state.root_previous[bid] = True
    result = D.branch_readiness(candidate, now=T + 64, deadline=T + 150)
    assert (
        result["branch_descriptors"][bid]["detector_truth"] == "UNKNOWN"
    )  # old tick, no fresh inference


def test_source_clocks_do_not_reuse_depth_freshness_or_unbound_packet_clock():
    from src.engine.scalping.zero_base_probe import probe_ws_observation

    trade = dict(
        item="123456_AL",
        market_route="krx_nxt_integrated",
        transport_epoch=1,
        route_sequence=2,
        observed_epoch=T,
        provider_trade_epoch=T - 0.1,
    )
    depth = dict(trade, route_sequence=5, observed_epoch=T + 3)
    trade["market_source_latency"] = dict(
        item="wrong",
        transport_epoch=1,
        route_sequence=2,
        packet_received_epoch=T,
        normalized_epoch=T + 0.1,
    )
    snap = dict(
        market_data_transport_epoch=1,
        realtime_type_snapshots_by_route={
            "_AL|krx_nxt_integrated": {"0B": trade, "0D": depth}
        },
    )
    clocks = probe_ws_observation(
        snap,
        code="123456",
        route="krx_nxt_integrated",
        after_epoch=T - 1,
        now_epoch=T + 3.2,
    )["source_clocks"]
    assert clocks["0B"]["age_ms"] == 3200 and clocks["0D"]["age_ms"] == 200
    assert clocks["0B"]["packet_received_epoch"] is None
    assert (
        clocks["0D"]["provider_epoch"] == T - 0.1
    )  # explicitly supplied, not copied by observer
    snap["realtime_type_snapshots_by_route"]["_AL|krx_nxt_integrated"].pop("0B")
    clocks = probe_ws_observation(
        snap,
        code="123456",
        route="krx_nxt_integrated",
        after_epoch=T - 1,
        now_epoch=T + 3.2,
    )["source_clocks"]
    assert clocks["0B"]["cause"] == "unobservable" and clocks["0B"]["age_ms"] is None


def test_native_depth_builder_to_probe_counts_exact_unique_receipts_only(monkeypatch):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    from src.engine.scalping.zero_base_probe import probe_ws_observation

    monkeypatch.setattr(
        __import__("src.engine.kiwoom_websocket", fromlist=["time"]).time,
        "time",
        lambda: T,
    )
    depth = KiwoomWSManager._build_micro_reversion_depth_tick(
        "123456_AL", {"41": "100", "61": "10", "51": "99", "71": "10"}
    )
    depth.update(transport_epoch=1, route_sequence=2)
    key = "_AL|krx_nxt_integrated"
    snap = dict(
        market_data_transport_epoch=1,
        recent_depth_ticks_by_route={key: [depth, dict(depth)]},
    )
    result = probe_ws_observation(
        snap,
        code="123456",
        route="krx_nxt_integrated",
        after_epoch=T - 1,
        now_epoch=T + 1,
    )
    assert result["exact_0d_count"] == 1
    assert result["arrival_quality"]["recent_depth_ticks_by_route"]["duplicates"] == 1
    snap["recent_depth_ticks_by_route"][key][1]["received_at_ms"] += 1
    assert (
        probe_ws_observation(
            snap,
            code="123456",
            route="krx_nxt_integrated",
            after_epoch=T - 1,
            now_epoch=T + 1,
        )["exact_0d_count"]
        == 0
    )
    depth.pop("market_route")
    snap["recent_depth_ticks_by_route"][key][1].pop("market_route")
    assert (
        probe_ws_observation(
            snap,
            code="123456",
            route="krx_nxt_integrated",
            after_epoch=T - 1,
            now_epoch=T + 1,
        )["exact_0d_count"]
        == 0
    )


def test_long_wait_does_not_starve_short_cohort_and_retains_original_wait():
    queue = DiscoveryQueue("2026-10-12")
    for i in range(6):
        queue.observe(
            code=f"{i+100001}",
            route="krx_nxt_integrated",
            observed_epoch=T,
            source_sha256="a" * 64,
            source_scope="observed_panel",
            received_epoch=T,
            market="KOSPI",
            source_kind="activity",
        )
    requirements = lambda c, _: {"minimum_seconds": 0 if c.code == "100006" else 61}
    selected = queue.claim(
        now_epoch=T + 1, limit=5, residence_requirements=requirements
    )
    assert len(selected) == 5 and selected[-1]["code"] == "100006"
    assert queue.residence_deferred == {"long_slot_wait": 1}
    waiting = queue.snapshot()["candidates"][4]
    assert (
        waiting["claim_count"] == 0 and waiting["residence_wait_since_epoch"] == T + 1
    )
    first = selected[0]
    assert queue.resolve(
        first,
        result="required_feature_insufficient",
        machine_action="",
        next_due_epoch=T + 100,
        handoff_id=first["physical_probe_lease_id"],
    )
    assert queue.close_handoff(first, first["physical_probe_lease_id"])
    next_claim = queue.claim(
        now_epoch=T + 10, limit=1, residence_requirements=requirements
    )[0]
    assert next_claim["code"] == "100005" and next_claim["residence_wait_seconds"] == 9
    assert next_claim["residence_deadline_epoch"] == T + 160
    assert queue.snapshot()["candidates"][4]["residence_wait_since_epoch"] == 0


def test_probe_capsules_survive_actual_execution_writer_without_text_duplication(
    monkeypatch, tmp_path
):
    import ast
    from src.utils import pipeline_event_logger as E

    monkeypatch.setattr(E, "DATA_DIR", tmp_path)
    logs = []
    monkeypatch.setattr(E, "log_info", logs.append)
    capsule = {
        "runtime_generation": "exact-generation",
        "source_clocks": {"0B": {"age_ms": 3200}, "0D": {"age_ms": 200}},
    }
    result = E.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "test",
        "123456",
        "zero_base_probe_result",
        fields={
            "zero_base_branch_readiness": capsule,
            "physical_probe_lease_id": "lease",
            "zero_base_probe_reason": "feature_window_incomplete",
        },
    )
    assert result["structured_append_succeeded"]
    assert all("exact-generation" not in text for text in logs)
    part = next(
        (tmp_path / "threshold_cycle").glob(
            "date=*/family=entry_mechanical_momentum/part-execution-*"
        )
    )
    projected = json.loads(part.read_text().splitlines()[-1])
    assert (
        ast.literal_eval(projected["fields"]["zero_base_branch_readiness"]) == capsule
    )


def test_real_bus_subscriber_without_readiness_cannot_reserve():
    from src.core.event_bus import EventBus

    class Bus(EventBus):
        _instance = None
        _lock = threading.Lock()

    bus = Bus()
    cb = lambda payload: None
    bus.subscribe("probe", cb)
    assert bus.consumer_readiness("probe")["ready"] is False
    cb.runtime_readiness = lambda: {"ready": True}
    assert bus.consumer_readiness("probe")["ready"] is True

    def check():
        bus.unsubscribe("probe", cb)  # proves callback does not run under bus lock
        return {"ready": False, "reason": "detached"}

    cb.runtime_readiness = check
    assert bus.consumer_readiness("probe")["reason"] == "detached"


def test_required_history_allocates_long_slots_and_preserves_queued_candidates():
    queue = DiscoveryQueue("2026-10-12")
    for i in range(5):
        queue.observe(
            code=f"{i:06}",
            route="krx_nxt_integrated",
            observed_epoch=T,
            source_sha256="a" * 64,
            source_scope="observed_panel",
            received_epoch=T,
        )
    selected = queue.claim(
        now_epoch=T + 1,
        limit=5,
        residence_requirements=lambda *a: {"minimum_seconds": 61},
    )
    assert len(selected) == 4
    assert all(c["residence_deadline_epoch"] == T + 151 for c in selected)
    assert len(queue.snapshot()["candidates"]) == 5
    assert (
        queue.claim(
            now_epoch=T + 2,
            limit=5,
            residence_requirements=lambda *a: {"minimum_seconds": 61},
        )
        == []
    )
    # A genuinely short independent branch can still use existing short slots.
    short = queue.claim(
        now_epoch=T + 3,
        limit=5,
        residence_requirements=lambda *a: {"minimum_seconds": 0},
    )
    assert len(short) == 1 and all(
        c["residence_deadline_epoch"] == T + 63 for c in short
    )
    assert queue.in_flight_count() == 5


def test_history_is_definition_driven_not_maximum_confirmation_wait():
    assert D.branch_required_seconds(C.definition("manual_path_dca327a873720e53")) == 61
    assert D.branch_required_seconds(C.definition("G1")) == 60
    assert D.branch_required_seconds(C.definition("G3")) == 120
    assert (
        D.branch_required_seconds({"root_contract": {"maximum_wait_seconds": 120}}) == 0
    )


def research_record():
    identity = dict(
        source_date="2026-10-12",
        process_pid=123,
        process_start_ticks="456",
        symbol="005930",
        source_item="005930_AL",
        venue="SOR",
        market="REGULAR",
        native_epoch=1,
        family_sha256="family",
        scope_execution_hash="scope",
    )
    contract = dict(
        cost_rate=0.0023, target_net_pct=0.4, stop_net_pct=-3.0, horizon_seconds=1800
    )
    record = dict(
        identity=identity,
        event=dict(
            epoch=T,
            native_sequence=0,
            entry_ask=100,
            signal_id="signal",
            branch_signals={"first": {}},
        ),
        label_contract=contract,
        source_ref="existing-index-entry",
        cohort="PASS_invalidated",
    )
    return record


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("win", "WIN"),
        ("stop", "FAIL_STOP"),
        ("timeout", "FAIL_TIMEOUT"),
        ("partial", "EXCLUDED"),
        ("gap", "EXCLUDED"),
        ("epoch", "EXCLUDED"),
        ("ambiguous", "EXCLUDED"),
    ],
)
def test_native_label_contract_uses_ask_bid_cost_and_exact_path(kind, expected):
    record = research_record()
    rows = [
        quote(0),
        quote(1, T + 1, price=101 if kind == "win" else 96 if kind == "stop" else 100),
    ]
    if kind == "timeout":
        rows.append(quote(2, T + 1800))
    if kind == "gap":
        rows[1][2] = 3
    if kind == "epoch":
        rows[1][1] = 2
    if kind == "ambiguous":
        rows[1][0] = T
    window = dict(
        rows=rows,
        identity=record["identity"],
        label_contract=record["label_contract"],
        rows_sha256=P.digest(rows),
    )
    report = L.native_lifecycle_outcomes([record], window_reader=lambda ref: window)
    assert report["outcomes"][0]["status"] == expected
    assert report["provider_calls"] == 0 and report["actual_order_submitted"] is False
    if expected == "EXCLUDED":
        assert report["groups"][0]["win_rate"] is None


def test_missing_index_and_current_price_diagnostic_never_become_zero_winrate():
    record = research_record()
    report = L.native_lifecycle_outcomes([record], window_reader=lambda ref: None)
    assert report["outcomes"][0]["reason"] == "indexed_source_missing"
    assert report["groups"][0]["win_rate"] is None
    record["label_contract"] = {"target_net_pct": 0.5}
    report = L.native_lifecycle_outcomes(
        [record],
        window_reader=lambda ref: pytest.fail("invalid source should not read"),
    )
    assert report["outcomes"][0]["reason"] == "native_label_contract_mismatch"


def test_exact_deadline_needs_fresh_contiguous_evidence_and_a_visit(native):
    observe(native)
    R.record_native_visit("123456", "SOR", "123456_AL", "REGULAR", T + 0.5)
    for i in range(1, 6):
        native[2].legacy.last = quote(i)
        row = observe(native, T + i)
    assert row["terminal"] == "observed_valid_until_deadline_unclaimed"


def test_replacement_is_only_named_when_new_turn_has_ready_evidence(native):
    observe(native)
    native[2].legacy.turn = {"event_id": "replacement"}
    new_event = dict(
        native[3],
        event_id="replacement",
        signal_id="replacement_signal",
        branch_signals={
            "first": {"decision_phase": "FIRST_UPTICK", "event_id": "replacement"}
        },
    )
    native[2].ready = [dict(event=new_event, claimed=False)]
    observe(native, T + 0.2)
    assert list(R._SELECTED_READY.values())[0]["terminal"] == "replaced_before_claim"


def test_bad_quote_cannot_be_labeled_as_delivery_miss(native):
    native[2].legacy.last[4] = None
    assert observe(native)["terminal"] == "source_or_guard_blocked_before_claim"


def test_readiness_race_releases_only_before_any_physical_worker(
    monkeypatch, main_worker
):
    main = main_worker

    monkeypatch.setattr(main, "_zero_base_runtime_enabled", lambda: True)
    monkeypatch.setattr(main, "_zero_base_active_conflict", lambda code: False)
    monkeypatch.setattr(
        main,
        "evaluate_main_bot_control_exclusion",
        lambda code: SimpleNamespace(excluded=False),
    )
    monkeypatch.setattr(
        main,
        "scalping_session_venue_provenance",
        lambda now: {"market_session_regime": "KRX_REGULAR"},
    )
    monkeypatch.setattr(
        main,
        "_zero_base_consumer_readiness",
        lambda: {"ready": False, "reason": "ws_session_not_ready"},
    )
    monkeypatch.setattr(
        main,
        "_ZERO_BASE_PROBE_EXECUTOR",
        SimpleNamespace(submit=lambda *a: pytest.fail("unsent request started")),
    )
    outcomes = []
    monkeypatch.setattr(main, "_zero_base_probe_result", lambda *a: outcomes.append(a))
    claim = dict(code="123456", route="krx_nxt_integrated", source_sha256="a" * 64)
    main.handle_zero_base_probe_requested(dict(claim=claim, candidate=claim))
    assert outcomes[0][1:] == ("policy_unavailable", "ws_session_not_ready")


def test_real_selected_requirements_bind_scope_without_source_or_provider_io(
    native, monkeypatch
):
    from src.engine.scalping import reversal_current_backend as current

    B, scope, _, _ = native
    B._FAMILY["machine_cells"][scope[-1]]["routes"]["SOR"]["payload"]["branches"] = [
        {"branch_id": "G1"},
        {"branch_id": "manual_path_dca327a873720e53"},
    ]
    monkeypatch.setattr(current, "backend", lambda: B)
    result = D.residence_requirements(
        SimpleNamespace(code="123456", route="krx_nxt_integrated", discovery_price=100),
        T,
    )
    assert result["minimum_seconds"] == 60
    assert result["branch_required_seconds"]["manual_path_dca327a873720e53"] == 61
    assert (
        result["family_sha256"] == "family"
        and result["scope_execution_hash"] == "scope"
    )


def test_selector_consumed_without_exact_claim_ack_is_not_eligible(native):
    observe(native)
    native[2].ready[0]["claimed"] = True
    row = observe(native, T + 0.2)
    assert row["terminal"] == "unobservable"
    assert row["terminal_reason"] == "selector_consumed_without_claim_receipt"
    assert row["claimed"] is False


def test_concurrent_observation_and_claim_conserve_one_signal(native):
    observe(native)
    claim = dict(snapshot=[native[3], {}], generation="scope")
    barrier = threading.Barrier(4)
    before = deepcopy(native[2].ready)

    def worker(index):
        barrier.wait(timeout=5)
        for _ in range(40):
            if index % 2:
                R.record_selected_native_claim(
                    claim, family_sha256="family", now=T + 0.1
                )
            else:
                observe(native, T + 0.1)

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(worker, range(4)))
    result = R.snapshot()["native_signal_lifecycle"]
    assert result["count"] == 1 and result["counts"]["claimed"] == 1
    assert native[2].ready == before


def test_duplicate_source_is_counted_once_but_conflict_excluded():
    record = research_record()
    rows = [quote(0), quote(1, price=101)]
    window = dict(
        rows=rows,
        identity=record["identity"],
        label_contract=record["label_contract"],
        rows_sha256=P.digest(rows),
    )
    result = L.native_lifecycle_outcomes(
        [record, deepcopy(record)], window_reader=lambda ref: window
    )
    assert len(result["outcomes"]) == 1 and result["duplicate_count"] == 1
    conflict = deepcopy(record)
    conflict["event"]["entry_ask"] = 99
    result = L.native_lifecycle_outcomes(
        [record, conflict],
        window_reader=lambda ref: pytest.fail("conflicted join must not read"),
    )
    assert result["outcomes"][0]["reason"] == "duplicate_opportunity_conflict"
    assert result["groups"][0]["win_rate"] is None


def test_late_win_is_secondary_and_paired_veto_remains_false_negative_only_for_30m_win():
    record = dict(
        research_record(), auxiliary_verdict="VETO", symbol_type="samsung_fixed"
    )
    rows = [quote(0), quote(1, T + 1800), quote(2, T + 1801, price=101)]
    window = dict(
        rows=rows,
        identity=record["identity"],
        label_contract=record["label_contract"],
        rows_sha256=P.digest(rows),
    )
    result = L.native_lifecycle_outcomes([record], window_reader=lambda ref: window)
    assert result["outcomes"][0]["status"] == "FAIL_TIMEOUT"
    assert result["outcomes"][0]["late_outcome"]["status"] == "WIN"
    assert result["paired"]["false_negative"] == 0
    assert result["paired"]["winner_retention"] is None
    rows[1][3:6] = [101, 101, 101]
    window["rows_sha256"] = P.digest(rows)
    result = L.native_lifecycle_outcomes([record], window_reader=lambda ref: window)
    assert (
        result["paired"]["false_negative"] == 1
        and result["paired"]["winner_retention"] == 0
    )
    assert result["groups"][0]["symbol_type"] == "samsung_fixed"


def test_unjoinable_identity_does_not_abort_other_research_rows():
    invalid = research_record()
    invalid["identity"]["native_epoch"] = {"bad": 1}
    result = L.native_lifecycle_outcomes(
        [invalid, research_record()], window_reader=lambda ref: None
    )
    assert result["outcomes"][0]["reason"] == "exact_identity_missing"
    assert result["outcomes"][1]["reason"] == "indexed_source_missing"


@pytest.fixture
def hold_invalidation(native, monkeypatch, request):
    """Exercise the real ready survival rule, without reconstructing qualification."""
    from src.engine.scalping.reversal_extended_state import State
    from src.engine.scalping import reversal_current_backend

    bid = getattr(request, "param", "manual_residual_0d7e29b0230e5b49")
    family, bundle, generation = "a" * 64, "b" * 64, "c" * 64
    symbol = "066970"
    venue, suffix, market, session = (
        ("SOR", "_AL", "AFTER", "SOR_AFTERMARKET")
        if bid in C.CUMULATIVE_DEFINITIONS
        else ("NXT", "_NX", "PRE", "NXT_PREMARKET")
    )
    item = symbol + suffix
    band = C.cell_key(symbol, market, 100100)
    scope = (symbol, venue, item, market, "2026-10-12", band)
    state = State(branch_ids=[bid], generation=generation)

    def tick(seq, price, **changes):
        row = quote(seq, stamp=T + seq * 0.1, price=price)
        row[9] = item
        for key, value in changes.items():
            row[int(key)] = value
        state.observe(row, symbol=symbol, venue=venue, session=session)
        return row

    tick(0, 100100)
    eid = f"2026-10-12:{venue}:{session}:{symbol}:1:0"
    event = dict(
        epoch=T,
        event_id=eid,
        signal_id=eid,
        native_epoch=1,
        native_sequence=0,
        symbol=symbol,
        source_item=item,
        venue=venue,
        market=market,
        confirmation_price=100100,
        registry_generation=generation,
        entry_ask=100100,
        branch_signals={
            bid: dict(
                extended_definition_id=bid,
                decision_phase="FIRST_PRICE_HOLD",
                signal_proof={"price": 100100},
            )
        },
    )
    from src.engine.scalping.reversal_cumulative_catalog import REFINEMENTS

    if bid in REFINEMENTS:
        event["branch_signals"][bid]["signal_proof"] = {
            "original_confirmation": {
                "decision_phase": "FIRST_PRICE_HOLD",
                "signal_proof": {"price": 100100},
            }
        }
    state.ready.append(dict(event=deepcopy(event), claimed=False, path_inputs={}))
    carried = SimpleNamespace(
        _LOCK=threading.RLock(), _STATES={}, _GENERATION="d" * 64, __name__="registered"
    )
    backend = SimpleNamespace(
        __name__="reversal_operating_runtime",
        _LOCK=threading.RLock(),
        _STATES={scope: state},
        _GENERATION=family,
        R=carried,
        _FAMILY=dict(
            schema="continuous_reversal_policy_v6",
            family_sha256=family,
            native_parent_bundle={"continuous_reversal": {"family_sha256": "d" * 64}},
            machine_cells={
                band: {
                    "routes": {
                        venue: dict(
                            backend="union_v6",
                            scope_execution_hash=generation,
                            payload={"branches": [{"branch_id": bid}]},
                        )
                    }
                }
            },
        ),
    )
    monkeypatch.setattr(R, "_GENERATION", bundle)
    monkeypatch.setattr(reversal_current_backend, "backend", lambda *a: backend)
    R.record_native_ready(backend, *scope[:4], T)
    return backend, state, event, tick


@pytest.mark.parametrize(
    "hold_invalidation",
    ["manual_residual_0d7e29b0230e5b49", "manual_cumulative_59846db468e4602a246ef839"],
    indirect=True,
)
def test_real_hold_breach_records_terminal_and_does_not_resurrect(hold_invalidation):
    backend, state, event, tick = hold_invalidation
    tick(1, 100000)
    assert not state.ready
    R.record_native_ready(
        backend,
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        T + 0.1,
    )
    life = next(iter(R._SELECTED_READY.values()))
    assert life["terminal"] == "invalidated_before_claim"
    assert life["terminal_reason"] == "first_price_hold_breached"
    assert life["branch_survival"] == {next(iter(event["branch_signals"])): False}
    original = deepcopy(life)
    tick(2, 100100)
    R.record_native_ready(
        backend,
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        T + 0.2,
    )
    assert next(iter(R._SELECTED_READY.values())) == original
    assert not state.ready and life["original_deadline"] == T + 5


@pytest.mark.parametrize(
    "damage", ["source", "epoch", "gap", "generation", "unknown_removal", "quote"]
)
@pytest.mark.parametrize(
    "hold_invalidation",
    ["manual_residual_0d7e29b0230e5b49", "manual_cumulative_59846db468e4602a246ef839"],
    indirect=True,
)
def test_hold_terminal_never_upgrades_invalid_or_unobserved_source(
    hold_invalidation, damage
):
    backend, state, event, tick = hold_invalidation
    changes = {"source": {"8": False}, "epoch": {"1": 2}, "quote": {"5": None}}.get(
        damage, {}
    )
    tick(
        2 if damage == "gap" else 1,
        100100 if damage == "unknown_removal" else 100000,
        **changes,
    )
    if damage == "generation":
        state.generation = "e" * 64
    if damage == "unknown_removal":
        state.ready.clear()
    R.record_native_ready(
        backend,
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        T + (0.2 if damage == "gap" else 0.1),
    )
    life = next(iter(R._SELECTED_READY.values()))
    assert life["terminal_reason"] != "first_price_hold_breached"


def _hold_rejection(hold_invalidation, monkeypatch, *, lifetime=None, breach_seq=1):
    from src.engine.scalping import entry_machine_source_recovery as recovery

    backend, state, event, tick = hold_invalidation
    from src.engine.scalping.entry_deadline import (
        bind_signal_lifetime,
        signal_deadline_epoch,
    )

    if lifetime is not None:
        monkeypatch.setattr(D.time, "time", lambda: T)
        bind_signal_lifetime(
            event,
            {
                "schema": "entry_signal_lifetime_policy_v1",
                "version": "native-diagnostic-fixture-v1",
                "max_signal_age_sec": lifetime,
            },
            live_clock=True,
        )
        state.ready[0]["event"] = deepcopy(event)
        R._SELECTED_READY.clear()
        R._ACTIVE_SELECTED.clear()
        R.record_native_ready(
            backend,
            event["symbol"],
            event["venue"],
            event["source_item"],
            event["market"],
            T,
        )
        for seq in range(1, breach_seq):
            tick(seq, 100100)
            R.record_native_ready(
                backend,
                event["symbol"],
                event["venue"],
                event["source_item"],
                event["market"],
                T + seq * 0.1,
            )
    breach = T + breach_seq * 0.1
    tick(breach_seq, 100000)
    R.record_native_ready(
        backend,
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        breach,
    )
    monkeypatch.setattr(D.time, "time", lambda: breach + 0.1)
    observation = dict(
        schema="entry_source_quote_observer_v1",
        snapshot=[event, {}],
        family_sha256=backend._GENERATION,
        deadline_epoch=signal_deadline_epoch(event),
        deadline_perf=(
            (event.get("entry_signal_lifetime") or {}).get("clock") or {}
        ).get("deadline_perf", R.time.perf_counter() + 5),
        observer_pid=R.os.getpid(),
        observer_start_ticks=R._PROCESS_START_TICKS,
    )
    with pytest.raises(
        ValueError, match="machine_source_quote_observer_native_root_changed"
    ) as caught:
        recovery.validated_observer_snapshot(
            observation,
            now=breach + 0.1,
            evaluation_attempt_id="hold-attempt",
            machine_bundle_sha256="b" * 64,
        )
    return dict(
        decision_ts=K.iso(breach + 0.2),
        decision_stage="entry_screen",
        stock_code="066970",
        evaluation_attempt_id="hold-attempt",
        machine_bundle_sha256="b" * 64,
        market_data_route={"NXT": "nxt_only", "SOR": "krx_nxt_integrated"}[
            event["venue"]
        ],
        provider_called=False,
        machine_evaluation_status="assessment_contract_invalid",
        machine_contract_error=str(caught.value),
        continuous_reversal_rejected_claim_receipt=caught.value.reversal_source_receipt,
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "hash",
        "attempt",
        "bundle",
        "pid",
        "family",
        "scope",
        "item",
        "signal",
        "epoch",
        "sequence",
        "gap",
        "quote",
        "floor",
        "deadline",
        "future",
        "claimed",
        "survivor",
        "ready",
        "source",
        "unknown",
        "bool_price",
        "bool_sequence",
        "new_root_conflict",
    ],
)
@pytest.mark.parametrize(
    "hold_invalidation",
    ["manual_residual_0d7e29b0230e5b49", "manual_cumulative_59846db468e4602a246ef839"],
    indirect=True,
)
def test_hold_rejection_consumes_exact_native_terminal_only(
    hold_invalidation, monkeypatch, damage
):
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )
    from src.engine.scalping.entry_machine_source_recovery import _digest

    trace = _hold_rejection(hold_invalidation, monkeypatch)
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    selection = receipt["native_selection"]
    life = selection["original_signal_lifecycle"]
    bid = next(iter(life["branch_survival"]))
    if damage == "bool_price":
        life["latest_native_observation"][3] = True
    elif damage == "bool_sequence":
        life["latest_native_observation"][2] = True
    elif damage == "new_root_conflict":
        receipt["current_root"] = dict(
            receipt["original_root"], signal_id="new", native_epoch=2
        )
    elif damage == "attempt":
        trace["evaluation_attempt_id"] = "other"
    elif damage == "bundle":
        trace["machine_bundle_sha256"] = "d" * 64
    elif damage == "pid":
        life["process_pid"] += 1
    elif damage == "family":
        life["family_sha256"] = "d" * 64
    elif damage == "scope":
        selection["scope_execution_hash"] = "d" * 64
    elif damage == "item":
        life["latest_native_observation"][9] = "999999_AL"
    elif damage == "signal":
        life["signal_id"] = "other"
    elif damage == "epoch":
        life["latest_native_observation"][1] += 1
    elif damage == "sequence":
        life["latest_native_observation"][2] = 0
    elif damage == "gap":
        life["continuous_ingress"] = False
    elif damage == "quote":
        selection["native_quote_current"] = False
    elif damage == "floor":
        life["branch_hold_floors"][bid] = 99900
    elif damage == "deadline":
        receipt["original_deadline_epoch"] += 1
    elif damage == "future":
        life["first_ineligible_seen"] = T + 1
    elif damage == "claimed":
        life["claimed"] = True
    elif damage == "survivor":
        life["branch_survival"][bid] = True
    elif damage == "ready":
        life["ready_membership_present"] = True
    elif damage == "source":
        selection["native_source_current"] = False
    elif damage == "unknown":
        life["terminal_reason"] = "ready_removed_without_terminal_receipt"
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    if damage == "hash":
        receipt["sha256"] = "0" * 64
    assert _reversal_lifecycle_diagnostic(trace) == (
        "reversal_first_price_hold_invalidated" if damage is None else None
    )
    from src.engine.scalping.ai_decision_trace import sanitize_ai_trace_value

    safe, redacted = sanitize_ai_trace_value(trace)
    assert not redacted and safe == trace


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("extended", "reversal_first_price_hold_invalidated"),
        ("conflicting_deadlines", None),
        ("after_legacy_window", None),
        ("past_issued_deadline", None),
    ],
)
@pytest.mark.parametrize(
    "hold_invalidation",
    ["manual_cumulative_59846db468e4602a246ef839"],
    indirect=True,
)
def test_observer_lifetime_classification_preserves_issued_boundary(
    hold_invalidation, monkeypatch, mode, expected
):
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )
    from src.engine.scalping.entry_machine_source_recovery import _digest

    trace = _hold_rejection(hold_invalidation, monkeypatch)
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    selection = receipt["native_selection"]
    life = selection["original_signal_lifecycle"]
    receipt["original_deadline_epoch"] = T + 9.6
    life["original_deadline"] = T + 9.6
    if mode == "conflicting_deadlines":
        life["original_deadline"] = T + 8
    elif mode == "after_legacy_window":
        receipt["observed_epoch"] = selection["observed_epoch"] = T + 5.1
        selection["native_last_received_epoch"] = T + 5
        trace["decision_ts"] = K.iso(T + 5.2)
    elif mode == "past_issued_deadline":
        receipt["original_deadline_epoch"] = life["original_deadline"] = T + 0.15
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    assert _reversal_lifecycle_diagnostic(trace) == expected


@pytest.mark.parametrize(
    "hold_invalidation",
    ["manual_residual_0d7e29b0230e5b49", "manual_cumulative_59846db468e4602a246ef839"],
    indirect=True,
)
@pytest.mark.parametrize("lifetime", [5, 9.6])
def test_same_hold_attempt_probe_and_trace_are_diagnostics_not_source_loss(
    hold_invalidation, monkeypatch, tmp_path, lifetime
):
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    from src.engine.scalping.entry_machine_source_recovery import _digest
    from src.tests.test_submission_bottleneck_monitor import _source_gap_files

    trace = _hold_rejection(hold_invalidation, monkeypatch)
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    receipt["original_deadline_epoch"] = T + lifetime
    receipt["native_selection"]["original_signal_lifecycle"]["original_deadline"] = T + lifetime
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    probe = dict(
        emitted_at=K.iso(T + 0.4),
        pipeline="ENTRY_PIPELINE",
        stage="zero_base_probe_result",
        stock_code="066970",
        fields=dict(
            zero_base_probe_result="policy_unavailable",
            zero_base_probe_reason="assessment_contract_invalid",
            zero_base_producer_pid=R.os.getpid(),
            native_observation_reference=dict(
                observer_pid=R.os.getpid(),
                observer_start_ticks=R._PROCESS_START_TICKS,
                family_sha256="a" * 64,
                deadline_epoch=T + lifetime,
            ),
            zero_base_route=trace["market_data_route"],
            zero_base_machine_contract_error=trace["machine_contract_error"],
            evaluation_attempt_id=trace["evaluation_attempt_id"],
            machine_bundle_sha256="b" * 64,
            provider_called="False",
            continuous_reversal_rejected_claim_receipt=trace[
                "continuous_reversal_rejected_claim_receipt"
            ],
        ),
    )
    from src.utils import pipeline_event_logger as logger

    monkeypatch.setattr(logger, "DATA_DIR", tmp_path)
    monkeypatch.setattr(logger, "log_info", lambda *a: None)
    probe = logger.emit_pipeline_event(
        probe["pipeline"],
        "test",
        probe["stock_code"],
        probe["stage"],
        fields=probe["fields"],
        observed_at_epoch=T + 0.4,
    )
    assert probe["structured_append_succeeded"] is True
    assert isinstance(
        probe["fields"]["continuous_reversal_rejected_claim_receipt"], str
    )
    now = datetime.fromtimestamp(T + 1, K.KST)
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"] == {}
    assert result["diagnostics"] == {
        "machine_probe:reversal_first_price_hold_invalidated": 1,
        "machine_trace:reversal_first_price_hold_invalidated": 1,
    }
    assert result["observed"]["probe_native_invalidated"] == 1
    from src.tests.test_submission_bottleneck_monitor import _observation_health_fixture

    health_input = _observation_health_fixture()
    health_input["source_gap_semantics"] = dict(result, as_of=health_input["as_of"])
    unmet = monitor.observation_health_projection(health_input)["unmet_conditions"]
    assert "unknown_or_unbound_source_diagnostic" not in unmet
    assert "source_observation_counts_invalid" not in unmet
    probe["fields"]["zero_base_producer_pid"] = (
        int(probe["fields"]["zero_base_producer_pid"]) + 1
    )
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
    conflict = monitor.source_gap_semantics(tmp_path, now)
    assert conflict["issues"] == {
        "machine_probe:machine_source_quote_observer_native_root_changed": 1
    }
    probe["fields"]["zero_base_producer_pid"] -= 1
    for malformed in ("{}", "{broken", '__import__("os")', "x" * 65537):
        probe["fields"]["continuous_reversal_rejected_claim_receipt"] = malformed
        _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
        result = monitor.source_gap_semantics(tmp_path, now)
        assert result["issues"] == {
            "machine_probe:machine_source_quote_observer_native_root_changed": 1
        }


def _first_turn_rejection(hold_invalidation, monkeypatch, *, batch_clock=False):
    """The issued observer receipt also carries native FIRST turn terminals."""
    from src.engine.scalping.entry_machine_source_recovery import _digest

    trace = _hold_rejection(hold_invalidation, monkeypatch)
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    root = receipt["original_root"]
    life = receipt["native_selection"]["original_signal_lifecycle"]
    for signal in root["branch_signals"].values():
        signal.update(
            {
                k: root[k]
                for k in (
                    "event_id",
                    "signal_id",
                    "epoch",
                    "native_epoch",
                    "native_sequence",
                    "source_item",
                    "confirmation_price",
                )
            }
        )
        signal.update(decision_phase="FIRST_UPTICK", signal_proof={})
    life.update(
        branch_hold_floors={},
        terminal_reason="first_turn_invalidated",
        branch_membership={bid: root["event_id"] for bid in root["branch_signals"]},
    )
    if batch_clock:
        life["last_eligible_seen"] = life["first_ineligible_seen"]
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    return trace


def test_hold_breach_can_share_a_receive_clock_with_last_eligible_tick(
    hold_invalidation, monkeypatch
):
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )
    from src.engine.scalping.entry_machine_source_recovery import _digest

    trace = _hold_rejection(hold_invalidation, monkeypatch)
    r = trace["continuous_reversal_rejected_claim_receipt"]
    life = r["native_selection"]["original_signal_lifecycle"]
    life["last_eligible_seen"] = life["first_ineligible_seen"]
    r["sha256"] = _digest({k: v for k, v in r.items() if k != "sha256"})
    assert (
        _reversal_lifecycle_diagnostic(trace) == "reversal_first_price_hold_invalidated"
    )
    life["last_eligible_seen"] += 0.01
    r["sha256"] = _digest({k: v for k, v in r.items() if k != "sha256"})
    assert _reversal_lifecycle_diagnostic(trace) is None


def test_native_first_turn_can_end_after_eligible_tick_with_same_batch_clock(native):
    backend, scope, state, event = native
    legacy = K.ReversalState()
    state.legacy = legacy

    def ingest(sequence, at, price):
        row = quote(sequence, stamp=at, price=price)
        row[9] = scope[2]
        legacy.observe(row, symbol=scope[0], venue=scope[1], session="SOR_REGULAR")

    for seq, price in enumerate((101, 100, 99, 100)):
        ingest(seq, T + (seq - 3) * 0.1, price)
    assert legacy.turn
    event.update(
        epoch=T,
        event_id=legacy.turn["event_id"],
        signal_id=legacy.turn["event_id"],
        native_sequence=3,
    )
    event["branch_signals"]["first"]["event_id"] = event["event_id"]
    observe(native, T)
    ingest(4, T + 0.1, 100)
    observe(native, T + 0.1)
    ingest(5, T + 0.1, 99)
    assert legacy.turn is None
    life = observe(native, T + 0.1)
    assert life["terminal_reason"] == "first_turn_invalidated"
    assert life["last_eligible_seen"] == life["first_ineligible_seen"] == T + 0.1
    assert life["latest_native_observation"][2] == 5 > life["native_sequence"]


def _first_turn_probe(trace, *, original_reference=False):
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    probe = dict(
        emitted_at=K.iso(T + 0.4),
        pipeline="ENTRY_PIPELINE",
        stage="zero_base_probe_result",
        stock_code=trace["stock_code"],
        fields=dict(
            zero_base_probe_result="policy_unavailable",
            zero_base_probe_reason="assessment_contract_invalid",
            zero_base_route="nxt_only",
            zero_base_producer_pid=R.os.getpid(),
            native_observation_reference=dict(
                observer_pid=R.os.getpid(),
                observer_start_ticks=R._PROCESS_START_TICKS,
                family_sha256="a" * 64,
                deadline_epoch=T + 5,
            ),
            zero_base_machine_contract_error=trace["machine_contract_error"],
            evaluation_attempt_id=trace["evaluation_attempt_id"],
            machine_bundle_sha256="b" * 64,
            provider_called="False",
            continuous_reversal_rejected_claim_receipt=json.dumps(receipt),
        ),
    )
    if original_reference:
        root = receipt["original_root"]
        scope = receipt["native_selection"]["original_signal_lifecycle"]["scope"]
        original = dict(
            schema="native_observation_selection_v1",
            evaluation_role="probe_observation",
            observed_epoch=T,
            process_pid=R.os.getpid(),
            process_start_ticks=R._PROCESS_START_TICKS,
            family_sha256="a" * 64,
            scope_execution_hash=root["registry_generation"],
            selected_scope=scope[5],
            item=root["source_item"],
            venue=root["venue"],
            native_event_id=root["event_id"],
            signal_id=root["signal_id"],
            native_epoch=root["native_epoch"],
            native_sequence=root["native_sequence"],
            native_deadline_epoch=T + 5,
            native_source_current=True,
            native_quote_current=True,
            raw_ready_count=1,
            selected_ready_count=1,
            selected_branch_truth={bid: "TRUE" for bid in root["branch_signals"]},
            reason="ready",
            runtime_effect=False,
        )
        probe["fields"].update(
            native_observation_reference={}, native_observation_receipt=repr(original)
        )
    return probe


@pytest.mark.parametrize("batch_clock", [False, True])
@pytest.mark.parametrize("original_reference", [False, True])
def test_first_turn_observer_terminal_is_not_source_loss(
    hold_invalidation, monkeypatch, tmp_path, batch_clock, original_reference
):
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    from src.tests.test_submission_bottleneck_monitor import _source_gap_files

    trace = _first_turn_rejection(
        hold_invalidation, monkeypatch, batch_clock=batch_clock
    )
    assert (
        monitor._reversal_lifecycle_diagnostic(trace)
        == "reversal_first_signal_invalidated"
    )
    probe = _first_turn_probe(trace, original_reference=original_reference)
    now = datetime.fromtimestamp(T + 1, K.KST)
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"] == {}
    assert result["diagnostics"] == {
        stage + ":reversal_first_signal_invalidated": 1
        for stage in ("machine_probe", "machine_trace")
    }
    assert result["observed"]["probe_native_invalidated"] == 1
    from src.tests.test_submission_bottleneck_monitor import _observation_health_fixture

    health = _observation_health_fixture()
    health["source_gap_semantics"] = dict(result, as_of=health["as_of"])
    assert (
        "unknown_or_unbound_source_diagnostic"
        not in monitor.observation_health_projection(health)["unmet_conditions"]
    )


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "schema",
        "role",
        "actor",
        "family",
        "scope",
        "signal",
        "epoch",
        "sequence",
        "bool_sequence",
        "clock",
        "deadline",
        "source",
        "quote",
        "ready_count",
        "branch",
        "conflicting_reference",
        "malformed",
        "oversize",
    ],
)
def test_empty_observer_reference_requires_intact_original_selection(
    hold_invalidation, monkeypatch, tmp_path, damage
):
    import ast
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    from src.tests.test_submission_bottleneck_monitor import _source_gap_files

    trace = _first_turn_rejection(hold_invalidation, monkeypatch)
    probe = _first_turn_probe(trace, original_reference=True)
    f = probe["fields"]
    original = ast.literal_eval(f["native_observation_receipt"])
    if damage == "schema":
        original["schema"] = "unknown"
    elif damage == "role":
        original["evaluation_role"] = "main_live"
    elif damage == "actor":
        original["process_pid"] += 1
    elif damage == "family":
        original["family_sha256"] = "e" * 64
    elif damage == "scope":
        original["scope_execution_hash"] = "e" * 64
    elif damage == "signal":
        original["signal_id"] = "other"
    elif damage == "epoch":
        original["native_epoch"] += 1
    elif damage == "sequence":
        original["native_sequence"] += 1
    elif damage == "bool_sequence":
        original["native_sequence"] = False
    elif damage == "clock":
        original["observed_epoch"] = T + 1
    elif damage == "deadline":
        original["native_deadline_epoch"] += 1
    elif damage == "source":
        original["native_source_current"] = False
    elif damage == "quote":
        original["native_quote_current"] = False
    elif damage == "ready_count":
        original["selected_ready_count"] = 0
    elif damage == "branch":
        original["selected_branch_truth"] = {}
    elif damage == "conflicting_reference":
        f["native_observation_reference"] = {"observer_pid": 1}
    f["native_observation_receipt"] = repr(original)
    if damage == "missing":
        f.pop("native_observation_receipt")
    elif damage == "malformed":
        f["native_observation_receipt"] = "{broken"
    elif damage == "oversize":
        f["native_observation_receipt"] = "x" * 65537
    now = datetime.fromtimestamp(T + 1, K.KST)
    _source_gap_files(tmp_path, now, probes=[probe], traces=[trace])
    result = monitor.source_gap_semantics(tmp_path, now)
    assert result["issues"] == {
        "machine_probe:machine_source_quote_observer_native_root_changed": 1
    }
    assert result["diagnostics"] == {
        "machine_trace:reversal_first_signal_invalidated": 1
    }


@pytest.mark.parametrize(
    "damage",
    [
        "hash",
        "attempt",
        "bundle",
        "actor",
        "source",
        "quote",
        "ready",
        "claimed",
        "survivor",
        "unknown",
        "missing_branch",
        "membership",
        "signal",
        "phase",
        "signal_epoch",
        "signal_sequence",
        "bool_sequence",
        "item",
        "price",
        "bool_price",
        "bool_root_price",
        "clock",
        "deadline",
        "gap",
        "mixed",
    ],
)
def test_first_turn_observer_keeps_unproved_or_conflicting_loss_actionable(
    hold_invalidation, monkeypatch, damage
):
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )
    from src.engine.scalping.entry_machine_source_recovery import _digest

    trace = _first_turn_rejection(hold_invalidation, monkeypatch, batch_clock=True)
    r = trace["continuous_reversal_rejected_claim_receipt"]
    root = r["original_root"]
    selection = r["native_selection"]
    life = selection["original_signal_lifecycle"]
    bid = next(iter(root["branch_signals"]))
    signal = root["branch_signals"][bid]
    if damage == "attempt":
        trace["evaluation_attempt_id"] = "other"
    elif damage == "bundle":
        trace["machine_bundle_sha256"] = "d" * 64
    elif damage == "actor":
        life["process_pid"] += 1
    elif damage == "source":
        selection["native_source_current"] = False
    elif damage == "quote":
        selection["native_quote_current"] = False
    elif damage == "ready":
        life["ready_membership_present"] = True
    elif damage == "claimed":
        life["claimed"] = True
    elif damage == "survivor":
        life["branch_survival"][bid] = True
    elif damage == "unknown":
        life["terminal_reason"] = "ready_removed_without_terminal_receipt"
    elif damage == "missing_branch":
        root["branch_signals"] = {}
    elif damage == "membership":
        life["branch_membership"][bid] = "other"
    elif damage == "signal":
        signal["event_id"] = "other"
    elif damage == "phase":
        signal["decision_phase"] = "UNKNOWN"
    elif damage == "signal_epoch":
        signal["epoch"] += 1
    elif damage == "signal_sequence":
        signal["native_sequence"] += 1
    elif damage == "bool_sequence":
        signal["native_sequence"] = False
    elif damage == "item":
        signal["source_item"] = "066970_AL"
    elif damage == "price":
        life["latest_native_observation"][3] = root["confirmation_price"]
    elif damage == "bool_price":
        signal["confirmation_price"] = True
    elif damage == "bool_root_price":
        root["confirmation_price"] = True
    elif damage == "clock":
        life["last_eligible_seen"] = life["first_ineligible_seen"] + 0.01
    elif damage == "deadline":
        r["original_deadline_epoch"] += 1
    elif damage == "gap":
        life["continuous_ingress"] = False
    elif damage == "mixed":
        life["branch_hold_floors"][bid] = root["confirmation_price"]
    r["sha256"] = _digest({k: v for k, v in r.items() if k != "sha256"})
    if damage == "hash":
        r["sha256"] = "0" * 64
    assert _reversal_lifecycle_diagnostic(trace) is None


def test_websocket_cycle_distinguishes_handler_delay_wait_and_wall_clock_change(
    monkeypatch,
):
    monkeypatch.setattr(R, "_WS_SLOW_CYCLES", deque(maxlen=32))
    # An 18s receive wait is not automatically attributed to the network.
    R.record_ws_cycle(
        transport_epoch=7,
        started=(100.0, 10.0, 1.0),
        received_epoch=118.0,
        received=(28.0, 1.1),
        ended=(28.002, 1.102),
    )
    row = R.snapshot()["websocket_receive_cycles"]["slow_recent"][0]
    assert row["wait_seconds"] == 18.0
    assert row["dispatch_seconds"] == pytest.approx(0.002)
    assert row["wall_minus_monotonic_seconds"] == 0
    assert "unresolved" in row["wait_semantics"]
    R.record_ws_cycle(
        transport_epoch=8,
        started=(200.0, 40.0, 2.0),
        received_epoch=218.0,
        received=(40.01, 2.001),
        ended=(42.01, 2.5),
    )
    rows = R.snapshot()["websocket_receive_cycles"]["slow_recent"]
    assert rows[-1]["dispatch_seconds"] == 2.0
    assert rows[-1]["wall_minus_monotonic_seconds"] == pytest.approx(17.99)
    assert rows[-1]["transport_epoch"] == 8
    rows[-1]["dispatch_seconds"] = 999
    assert (
        R.snapshot()["websocket_receive_cycles"]["slow_recent"][-1]["dispatch_seconds"]
        == 2.0
    )


@pytest.mark.parametrize("damage", [None, "hash", "quote", "sequence", "ready", "claimed", "floor", "proof", "deadline", "unknown", "survivor", "pid", "source", "generation"])
def test_observed_missing_nested_hold_terminal_remains_unverified(damage):
    from pathlib import Path
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )
    from src.engine.scalping.entry_machine_source_recovery import _digest
    from src.engine.scalping.reversal_cumulative_catalog import REFINEMENTS

    trace = json.loads(
        (
            Path(__file__).parent / "fixtures/native_hold_observer_20261030.json"
        ).read_text()
    )["row"]
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    life = receipt["native_selection"]["original_signal_lifecycle"]
    branches = receipt["original_root"]["branch_signals"]
    nested = next(b for b in branches if b in REFINEMENTS)
    if damage == "quote":
        receipt["native_selection"]["native_quote_current"] = False
    elif damage == "sequence":
        life["latest_native_observation"][2] += 1
    elif damage == "ready":
        life["ready_membership_present"] = True
    elif damage == "claimed":
        life["claimed"] = True
    elif damage == "floor":
        life["branch_hold_floors"][nested] = 1
    elif damage == "pid":
        life["process_pid"] += 1
    elif damage == "source":
        receipt["native_selection"]["native_source_current"] = False
    elif damage == "generation":
        receipt["original_root"]["registry_generation"] = "0" * 64
    elif damage == "proof":
        branches[nested]["signal_proof"]["original_confirmation"][
            "branch_definition_sha256"
        ] = ("0" * 64)
    elif damage == "deadline":
        receipt["original_deadline_epoch"] = receipt["observed_epoch"]
    elif damage == "unknown":
        life["terminal_reason"] = "UNKNOWN"
    elif damage == "survivor":
        life["latest_native_observation"][3] = 15430
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    if damage == "hash":
        receipt["sha256"] = "0" * 64
    original = deepcopy(trace)
    assert _reversal_lifecycle_diagnostic(trace) is None
    assert trace == original


@pytest.mark.parametrize(
    "hold_invalidation", ["manual_cumulative_6824067d3769bdd90d25759a"], indirect=True
)
@pytest.mark.parametrize("missing", [False, True])
def test_nested_native_hold_floor_publisher_matches_actual_removal(hold_invalidation, missing):
    from src.engine.scalping.reversal_cumulative_catalog import REFINEMENTS

    backend, state, event, tick = hold_invalidation
    bid = next(iter(event["branch_signals"]))
    assert bid in REFINEMENTS
    branch = event["branch_signals"][bid]
    branch["signal_proof"] = {
        "original_confirmation": {
            "decision_phase": "FIRST_PRICE_HOLD",
            "signal_proof": {"price": 100100},
        }
    }
    if missing:
        branch["signal_proof"] = {}
    state.ready[0]["event"] = deepcopy(event)
    R._SELECTED_READY.clear()
    R._ACTIVE_SELECTED.clear()
    R.record_native_ready(
        backend,
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        T,
    )
    life = next(iter(R._SELECTED_READY.values()))
    assert life["branch_hold_floors"] == {bid: None if missing else 100100}
    if missing:
        assert life.get("terminal_reason") != "first_price_hold_breached"
        assert life["terminal"] is None
        return
    tick(1, 100000)
    R.record_native_ready(
        backend,
        event["symbol"],
        event["venue"],
        event["source_item"],
        event["market"],
        T + 0.1,
    )
    assert life["terminal"] == "invalidated_before_claim"
    assert life["terminal_reason"] == "first_price_hold_breached"
    assert not state.ready


@pytest.mark.parametrize(
    "damage", [None, "missing", "hash", "generation", "deadline", "clock_actor"]
)
@pytest.mark.parametrize(
    "hold_invalidation", ["manual_cumulative_59846db468e4602a246ef839"], indirect=True
)
def test_native_published_lifetime_proof_closes_late_guard_without_renewal(
    hold_invalidation, monkeypatch, damage
):
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )
    from src.engine.scalping.entry_machine_source_recovery import _digest

    trace = _hold_rejection(hold_invalidation, monkeypatch, lifetime=9.6, breach_seq=51)
    receipt = trace["continuous_reversal_rejected_claim_receipt"]
    life = receipt["native_selection"]["original_signal_lifecycle"]
    issued = life["entry_signal_lifetime"]
    assert issued is not hold_invalidation[2]["entry_signal_lifetime"]
    assert issued == hold_invalidation[2]["entry_signal_lifetime"]
    if damage == "missing":
        life.pop("entry_signal_lifetime")
    elif damage == "hash":
        issued["policy_sha256"] = "0" * 64
    elif damage == "generation":
        issued["generation"] = "0" * 64
    elif damage == "deadline":
        issued["deadline_epoch"] += 1
    elif damage == "clock_actor":
        issued["clock"] = {
            "pid": receipt["process_pid"] + 1,
            "issued_epoch": T,
            "issued_perf": 1.0,
            "deadline_perf": 1.0 + (issued["deadline_epoch"] - T),
        }
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    original = deepcopy(trace)
    assert _reversal_lifecycle_diagnostic(trace) == (
        "reversal_first_price_hold_invalidated" if damage is None else None
    )
    assert trace == original


@pytest.mark.parametrize(
    "hold_invalidation", ["manual_cumulative_6824067d3769bdd90d25759a"], indirect=True
)
def test_nested_hold_native_producer_and_rejection_reader_agree(
    hold_invalidation, monkeypatch
):
    from src.engine.monitoring.submission_bottleneck_monitor import (
        _reversal_lifecycle_diagnostic,
    )

    trace = _hold_rejection(hold_invalidation, monkeypatch)
    original = deepcopy(trace)
    life = trace["continuous_reversal_rejected_claim_receipt"]["native_selection"][
        "original_signal_lifecycle"
    ]
    assert life["terminal"] == "invalidated_before_claim"
    assert life["terminal_reason"] == "first_price_hold_breached"
    assert (
        _reversal_lifecycle_diagnostic(trace) == "reversal_first_price_hold_invalidated"
    )
    assert trace == original
