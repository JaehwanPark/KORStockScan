"""Evaluator-local sources survive competing native owners without new authority."""

from copy import deepcopy
import json

import pytest

from src.engine import sniper_state_handlers as handlers
from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.position_peak_ledger import position_cycle_id
from src.tests.test_main_stop_runtime_source import stage_stock, stage_inputs


def context(stock, *, at=1792112400.0, evaluator="normal", bid=9900):
    return dict(
        at=at,
        bid=bid,
        bid_qty=20,
        quote=dict(
            market_route="KRX", item="005930", transport_epoch=1, observed_epoch=at
        ),
        complete=True,
        market="REGULAR",
        evaluator=evaluator,
        decision_profit_pct=-1.0,
        position_key=position_cycle_id(stock),
        quantity=stock["buy_qty"],
        buy_price=stock["buy_price"],
        pending_exit=bool(stock.get("exit_requested")),
        quote_max_age_sec=3.0,
    )


@pytest.mark.parametrize(
    "name,slot", [("normal_rest_recovery", "normal"), ("fast_rest_confirmed", "fast")]
)
def test_real_rest_evaluators_keep_original_identity_in_bounded_owner_slot(name, slot):
    stock = stage_stock()
    for evaluator in ("normal", "fast", "fast_prearm", name):
        source = context(stock, evaluator=evaluator)
        handlers._store_main_stop_quote_context(stock, source)
        source["quote"]["item"] = "changed_after_capture"
    slots = stock["_main_stop_quote_context_by_evaluator"]
    assert len(slots) == 3 and slots[slot]["evaluator"] == name
    assert slots[slot]["quote"]["item"] == "005930"
    before = deepcopy(slots)
    with pytest.raises(ValueError, match="evaluator_invalid"):
        handlers._store_main_stop_quote_context(
            stock, context(stock, evaluator="unknown")
        )
    assert slots == before


def test_failed_same_clock_normal_context_cannot_reuse_previous_slot(monkeypatch):
    stock = stage_stock()
    normal = context(stock)
    fast = context(stock, evaluator="fast")
    handlers._store_main_stop_quote_context(stock, normal)
    handlers._store_main_stop_quote_context(stock, fast)

    def invalid(*args, **kwargs):
        raise ValueError("actual_input_invalid")

    monkeypatch.setattr(handlers, "_trusted_scalp_trailing_bid", invalid)
    handlers._prepare_main_stop_limit_up_quote(
        stock,
        "005930",
        ws_data={},
        quote_fields={},
        now_ts=normal["at"],
        profit_rate=-1.0,
    )
    assert "normal" not in stock["_main_stop_quote_context_by_evaluator"]
    assert stock["_main_stop_quote_context_by_evaluator"]["fast"] == fast
    assert stock["_main_stop_current_quote_context"] == fast
    rows = []
    monkeypatch.setattr(
        policy,
        "enqueue_source",
        lambda stock, code, row: rows.append(deepcopy(row)) or True,
    )
    actual = handlers._observe_main_stop_evaluation(
        stock,
        "005930",
        at=normal["at"],
        evaluator="normal",
        stage="common_soft",
        decision_price=9900,
        decision_price_basis="mark_price",
        decision_profit_pct=-1.0,
        decision_inputs=stage_inputs(),
    )
    assert actual and actual["quote_binding_status"] == "source_gap"
    assert rows[0]["coverage_complete"] is False and rows[0]["bid"] is None


@pytest.mark.parametrize("evaluator", ["normal", "normal_rest_recovery"])
def test_terminal_observer_uses_original_normal_owner_context(monkeypatch, evaluator):
    stock = stage_stock()
    normal = context(stock, evaluator=evaluator)
    handlers._store_main_stop_quote_context(stock, normal)
    handlers._store_main_stop_quote_context(
        stock, context(stock, at=normal["at"] + 0.01, evaluator="fast", bid=9800)
    )
    rows = []
    monkeypatch.setattr(
        policy,
        "enqueue_source",
        lambda stock, code, row: rows.append(deepcopy(row)) or True,
    )
    actual = handlers._main_stop_normal_exit_fields(
        stock,
        "005930",
        at=normal["at"],
        mark_price=9900,
        exit_rule="scalp_trailing_take_profit",
    )
    receipt = json.loads(actual["main_stop_normal_exit_decision"])
    assert (
        receipt["executable_bid"] == normal["bid"]
        and receipt["decision_at"] == normal["at"]
    )
    assert rows[0]["capture_evaluator"] == evaluator and rows[0]["bid"] == normal["bid"]


def test_old_capture_completion_cannot_replace_newer_quote_cache(monkeypatch):
    stock = stage_stock()
    older = context(stock)
    newer = context(stock, at=older["at"] + 1, evaluator="fast", bid=9800)
    rows = []

    def sink(owner, code, row):
        rows.append(deepcopy(row))
        if row["at"] == older["at"]:
            assert handlers._capture_main_stop_observation(stock, code, newer)
        return True

    monkeypatch.setattr(policy, "enqueue_source", sink)
    assert handlers._capture_main_stop_observation(stock, "005930", older)
    assert [r["quote_generation"] for r in rows] == [1, 2]
    assert stock["_main_stop_last_quote_source"]["at"] == newer["at"]
    assert stock["_main_stop_last_quote_source"]["quote_generation"] == 2
    assert stock["_main_stop_source_observation_generation"] == 2


def test_capture_preserves_immutable_pin_projection_cache(monkeypatch):
    stock = stage_stock()
    calls = []
    original = policy.asdict
    monkeypatch.setattr(
        policy, "asdict", lambda value: calls.append(value) or original(value)
    )
    monkeypatch.setattr(policy, "enqueue_source", lambda *args: True)
    first = context(stock)
    assert handlers._capture_main_stop_observation(stock, "005930", first)
    count = len(calls)
    assert handlers._capture_main_stop_observation(
        stock, "005930", context(stock, at=first["at"] + 1)
    )
    assert len(calls) == count
    assert (
        stock["_main_stop_source_values"][0]
        == stock["main_stop_policy_pin"]["pin_sha256"]
    )


def test_pending_disposition_is_new_source_not_stale_quote_reuse(monkeypatch):
    stock = stage_stock()
    rows = []
    monkeypatch.setattr(
        policy,
        "enqueue_source",
        lambda stock, code, row: rows.append(deepcopy(row)) or True,
    )
    before = context(stock)
    assert handlers._capture_main_stop_observation(stock, "005930", before)
    stock["exit_requested"] = True
    # Actual reached observation records pending custody; this is not an
    # eligible replay quote and gives no additional dispatch authority.
    actual = handlers._capture_main_stop_observation(
        stock,
        "005930",
        context(stock),
        force=True,
        decision_capture=True,
        return_source=True,
    )
    assert actual["pending_exit"] is True and actual["quote_generation"] == 2
    assert rows[0]["pending_exit"] is False
    from src.engine.scalping.main_stop_replay import common_no_exit_prefix

    assert not common_no_exit_prefix(
        actual, dict(decision_profit_pct=1.0, decision_inputs=stage_inputs()), -3.0
    )


def test_lifecycle_replacement_after_quote_never_reserves_old_eval_on_new_buy(
    monkeypatch,
):
    stock = stage_stock()
    ctx = context(stock)
    handlers._store_main_stop_quote_context(stock, ctx)
    rows = []
    monkeypatch.setattr(
        policy,
        "enqueue_source",
        lambda stock, code, row: rows.append(deepcopy(row)) or True,
    )
    original = handlers._capture_main_stop_observation

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        replacement = stage_stock(record=102)
        stock.clear()
        stock.update(replacement)
        return result

    monkeypatch.setattr(handlers, "_capture_main_stop_observation", capture)
    actual = handlers._observe_main_stop_evaluation(
        stock,
        "005930",
        at=ctx["at"],
        evaluator="normal",
        stage="common_soft",
        decision_price=9900,
        decision_price_basis="mark_price",
        decision_profit_pct=-1.0,
        decision_inputs=stage_inputs(),
    )
    assert actual is None and len(rows) == 1
    assert "main_stop_evaluation_source_gap" not in stock
    assert stock["main_stop_source_superseded_rejected_count"] == 1
    assert (
        stock["main_stop_source_superseded_rejection"]["reason"]
        == "native_observation_position_generation_changed"
    )
    assert "_main_stop_evaluation_generation" not in stock


@pytest.mark.parametrize("deferred", [False, True])
@pytest.mark.parametrize("record_id", [101, "00101"])
def test_envelope_uses_original_record_when_live_lifecycle_changes(
    monkeypatch, deferred, record_id
):
    stock = {"id": 202, "name": "native"}
    row = {
        "schema": "main_stop_source_v1",
        "record_id": record_id,
        "at": 1.0,
        "position_key": "record:101",
    }
    submitted = []
    monkeypatch.setattr(
        policy,
        "_SOURCE_SINK",
        lambda fn, *args, **kw: submitted.append(args) or {"status": "queued"},
    )
    if deferred:
        with policy.defer_source_capture():
            assert policy.enqueue_source(stock, "005930", row)
            stock["id"] = 303
    else:
        assert policy.enqueue_source(stock, "005930", row)
    assert (
        submitted[0][2] == record_id
        and json.loads(submitted[0][3])["record_id"] == record_id
    )


@pytest.mark.parametrize(
    "invalid",
    [None, True, 0, -1, 1.0, "", "-", "0", "-1", "abc", "0.0", "１", " 1 ", {}, []],
)
def test_present_invalid_record_never_falls_back_to_live_owner(monkeypatch, invalid):
    submitted = []
    monkeypatch.setattr(
        policy,
        "_SOURCE_SINK",
        lambda *a, **k: submitted.append(a) or {"status": "queued"},
    )
    assert policy.enqueue_source({"id": 999}, "005930", {"record_id": invalid}) is False
    assert submitted == []


def test_same_identity_reset_blocks_old_quote_cache_write(monkeypatch):
    from src.engine.scalping.main_stop_runtime_source import ensure_observation_epoch

    stock = stage_stock()
    old = context(stock)
    replacement = (
        stage_stock()
    )  # Deliberately identical record, pin, quantity and price.
    rows = []

    def sink(owner, code, row):
        rows.append(deepcopy(row))
        if row["at"] == old["at"]:
            stock.clear()
            stock.update(replacement)
            with handlers.ENTRY_LOCK:
                ensure_observation_epoch(stock)
            assert handlers._capture_main_stop_observation(
                stock, code, context(stock, at=old["at"] + 1, bid=9800)
            )
        return True

    monkeypatch.setattr(policy, "enqueue_source", sink)
    assert handlers._capture_main_stop_observation(stock, "005930", old)
    assert rows[0]["record_id"] == rows[1]["record_id"]
    assert rows[0]["quote_generation"] == rows[1]["quote_generation"] == 1
    assert rows[0]["source_lifecycle_epoch"] != rows[1]["source_lifecycle_epoch"]
    assert stock["_main_stop_last_quote_source"]["bid"] == 9800
    assert (
        stock["_main_stop_last_quote_source"]["source_lifecycle_epoch"]
        == stock["_main_stop_observation_epoch"]
    )


def test_deferred_old_lifecycle_failure_keeps_original_evidence_separate(monkeypatch):
    stock = {"id": 101, "_main_stop_observation_epoch": 7}
    seen = []
    monkeypatch.setattr(
        policy,
        "_SOURCE_SINK",
        lambda fn, *args, **kw: seen.append(args) or {"status": "rejected"},
    )
    with policy.defer_source_capture():
        assert policy.enqueue_source(
            stock, "005930", dict(record_id=101, source_lifecycle_epoch=7)
        )
        stock.update(id=102, _main_stop_observation_epoch=8)
    assert seen[0][2] == 101
    assert json.loads(seen[0][3])["source_lifecycle_epoch"] == 7
    assert stock.get("main_stop_source_rejected_count", 0) == 0
    assert stock["main_stop_source_superseded_rejected_count"] == 1
    assert stock["main_stop_source_superseded_rejection"] == dict(
        record_id=101,
        source_lifecycle_epoch=7,
        kind="deferred_queue",
        reason="observation_queue_rejected",
    )


def test_reversed_completion_preserves_actual_stage_order_through_native_index(
    monkeypatch, tmp_path
):
    from collections import Counter
    from src.engine.automation import (
        main_stop_postclose as post,
        main_stop_source_index as index,
    )
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.scalping.main_stop_replay import bound_evaluations

    stock = stage_stock()
    normal = context(stock)
    handlers._store_main_stop_quote_context(stock, normal)
    rows = []
    monkeypatch.setattr(
        policy,
        "enqueue_source",
        lambda stock, code, row: rows.append(
            dict(row, source_sha256=policy.digest(row))
        )
        or True,
    )
    original = handlers._capture_main_stop_observation

    def capture(*args, **kwargs):
        receipt = original(*args, **kwargs)
        if kwargs.get("source_view") and args[2]["evaluator"] == "normal":
            fast = context(stock, at=normal["at"] + 0.01, evaluator="fast", bid=9850)
            handlers._store_main_stop_quote_context(stock, fast)
            actual = handlers._observe_main_stop_preset_evaluation(
                stock,
                "005930",
                at=fast["at"],
                evaluator="fast",
                decision_price=9850,
                decision_price_basis="executable_bid",
                profit_rate=-1.5,
                hard_pct=-1.4,
                emergency_pct=-2.4,
                grace_sec=0,
                held_sec=100,
            )
            assert actual
        return receipt

    monkeypatch.setattr(handlers, "_capture_main_stop_observation", capture)
    actual = handlers._observe_main_stop_evaluation(
        stock,
        "005930",
        at=normal["at"],
        evaluator="normal",
        stage="common_soft",
        decision_price=9900,
        decision_price_basis="mark_price",
        decision_profit_pct=-1.0,
        decision_inputs=stage_inputs(),
    )
    assert actual and actual["evaluation_generation"] == 1
    assert [
        r["evaluation_generation"] for r in rows if "evaluation_generation" in r
    ] == [2, 1]
    source = tmp_path / "holding_pipeline_2026-10-16.jsonl"
    source.write_text(
        "".join(
            json.dumps(dict(stage="main_stop_source", fields=dict(main_stop_source=r)))
            + "\n"
            for r in rows
        )
    )
    census = Counter()
    refs = index.prepare(
        tmp_path / "index",
        {str(source): byte_generation(source)},
        post.source_events,
        census,
    )
    count = 0
    for position in index.positions(refs, tmp_path / "positions", census):
        with bound_evaluations(position.rows()) as (bound, state):
            results = list(bound)
            assert all(row["schema"] != "main_stop_contract_gap" for row, ev in results)
            assert [ev["evaluation_generation"] for row, ev in results] == [1, 2]
            assert state["unsupported"] == {}
        count += 1
    assert count == 1


@pytest.mark.parametrize("ticket", [(True, 1), (1.0, 1), (-1, 1), (2, 1), (1, 2), None])
def test_quote_reservation_requires_exact_typed_one_use_ticket(monkeypatch, ticket):
    from src.engine.scalping.main_stop_runtime_source import (
        ensure_observation_epoch,
        observation_view,
        reserve_observation_generations,
    )

    stock = stage_stock()
    ctx = context(stock)
    handlers._main_stop_values(stock, ctx["at"])
    with handlers.ENTRY_LOCK:
        ensure_observation_epoch(stock)
        view = observation_view(stock)
        reserved = reserve_observation_generations(stock, view, quote=True)
        view["_main_stop_quote_reservation"] = ticket
    rows = []
    monkeypatch.setattr(
        policy, "enqueue_source", lambda stock, code, row: rows.append(row) or True
    )
    assert (
        handlers._capture_main_stop_observation(
            stock,
            "005930",
            ctx,
            force=True,
            decision_capture=True,
            source_view=view,
            source_reserved=True,
        )
        is False
    )
    assert not rows
    assert all(stock[key] == value for key, value in reserved.items())


def test_reserved_quote_cannot_be_consumed_twice_even_after_another_reservation(
    monkeypatch,
):
    from src.engine.scalping.main_stop_runtime_source import (
        ensure_observation_epoch,
        observation_view,
        reserve_observation_generations,
    )

    stock = stage_stock()
    ctx = context(stock)
    handlers._main_stop_values(stock, ctx["at"])
    with handlers.ENTRY_LOCK:
        ensure_observation_epoch(stock)
        view = observation_view(stock)
        reserved = reserve_observation_generations(stock, view, quote=True)
        view["_main_stop_quote_reservation"] = tuple(reserved.values())
    rows = []
    monkeypatch.setattr(
        policy, "enqueue_source", lambda stock, code, row: rows.append(row) or True
    )
    kwargs = dict(
        force=True, decision_capture=True, source_view=view, source_reserved=True
    )
    assert handlers._capture_main_stop_observation(stock, "005930", ctx, **kwargs)
    with handlers.ENTRY_LOCK:
        reserve_observation_generations(stock, observation_view(stock), quote=True)
    assert (
        handlers._capture_main_stop_observation(stock, "005930", ctx, **kwargs) is False
    )
    assert len(rows) == 1


@pytest.mark.parametrize(
    "fault", [None, "route", "epoch", "bid", "ask", "depth_clock", "stale", "future"]
)
@pytest.mark.parametrize("native_book", [True, False])
def test_replay_depth_identity_uses_0d_clock_separately_from_newer_0b(
    fault, native_book
):
    from src.trading.market.quote_consistency import ws_quote_source_receipt

    at = 1793143045.3392675
    depth_at = 1793143045.239
    trade_at = depth_at + 0.05
    depth = dict(
        item="053800_NX",
        market_route="nxt_only",
        transport_epoch=7,
        observed_epoch=depth_at,
        route_sequence=11,
        best_bid=96000,
        best_ask=96100,
        best_bid_qty=330,
        best_ask_qty=250,
    )
    trade = dict(
        depth,
        observed_epoch=trade_at,
        route_sequence=25,
        inline_best_bid=96000,
        inline_best_ask=96100,
    )
    if native_book:
        depth["orderbook"] = {
            "bids": [{"price": depth.pop("best_bid"), "volume": 330}],
            "asks": [{"price": depth.pop("best_ask"), "volume": 250}],
        }
    ws = dict(
        best_bid=96000,
        best_ask=96100,
        best_bid_qty=330,
        market_data_transport_epoch=7,
        last_realtime_type_item={"0B": "053800_NX", "0D": "053800_NX"},
        last_realtime_type_ts={"0B": trade_at, "0D": depth_at},
        realtime_type_snapshots_by_route={"_NX|nxt_only": {"0B": trade, "0D": depth}},
    )
    receipt = ws_quote_source_receipt(ws, now_ts=at)
    assert receipt["source_type"] == "0B"
    if fault == "route":
        depth["market_route"] = "KRX"
    if fault == "epoch":
        depth["transport_epoch"] = 6
    if fault == "bid":
        if native_book:
            depth["orderbook"]["bids"][0]["price"] = 95900
        else:
            depth["best_bid"] = 95900
    if fault == "ask":
        if native_book:
            depth["orderbook"]["asks"][0]["price"] = 96200
        else:
            depth["best_ask"] = 96200
    if fault == "depth_clock":
        depth["observed_epoch"] -= 0.01
    if fault == "stale":
        at += 2
    if fault == "future":
        receipt["observed_epoch"] = at + 1
    ctx = handlers._main_stop_quote_context(
        {},
        "053800",
        snapshot=ws,
        quote_receipt=receipt,
        executable_bid=96000,
        bid_source="fresh_ws_executable_bid",
        rest_snapshot=None,
        quality={"quote_consistency_state": "single_source"},
        nxt_quality={},
        quote_received_at=depth_at,
        bid_received_at=depth_at,
        market_type="PREMARKET",
        exit_allowed_by_clock=True,
        price_usable=True,
        now_ts=at,
        evaluator="fast",
        holding_profit_rate_at_eval=-0.44,
    )
    assert ctx["complete"] is (fault is None)
    if fault == "stale":
        assert "bid_quote_stale_or_future" in ctx["source_gap_reasons"]
        assert "coverage_exhausted" not in ctx["source_gap_reasons"]
    if fault is None:
        assert ctx["source_gap_reasons"] == []
        assert ctx["bid_qty"] == 330
        assert ctx["quote"]["observed_epoch"] == depth_at
        assert ctx["quote"]["source_type"] == "0D"
        assert ctx["quote"]["route_sequence"] == 11
        assert receipt["route_sequence"] == 25
