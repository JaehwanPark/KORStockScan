"""Offline physical-send regression tests; no broker/provider calls."""

from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from src.engine import kiwoom_orders as orders
from src.trading.entry import physical_send_guard as guard
from src.trading.order.owner_custody_registry import OwnerOrderContext
from src.trading.entry.quote_time_policy import QuoteTimePolicy


def snapshot(stamp=99.8, *, epoch=7, bid=100, ask=101, curr=100):
    return {
        "curr": curr,
        "last_ws_update_ts": 100.0,
        "market_data_transport_epoch": epoch,
        "last_realtime_type_ts": {"0D": stamp},
        "last_realtime_type_item": {"0D": "005930_AL"},
        "orderbook": {
            "bids": [{"price": bid, "volume": 10}],
            "asks": [{"price": ask, "volume": 10}],
        },
        "realtime_type_snapshots_by_route": {
            "005930_AL": {
                "0D": {
                    "item": "005930_AL",
                    "market_route": "krx_nxt_integrated",
                    "transport_epoch": epoch,
                    "observed_epoch": stamp,
                    "route_sequence": 10,
                }
            }
        },
    }


@pytest.fixture
def case(monkeypatch):
    clock = SimpleNamespace(epoch=100.0, perf=10.0)
    monkeypatch.setattr(guard.time, "time", lambda: clock.epoch)
    monkeypatch.setattr(guard.time, "perf_counter", lambda: clock.perf)
    monkeypatch.setattr(
        orders.kiwoom_utils, "resolve_kiwoom_request_token", lambda token: token
    )
    policy = QuoteTimePolicy()
    policy_binding = guard.canonical_binding(policy.active_contract_dict())
    state = {"snapshot": snapshot(), "binding": ("decision", policy_binding)}
    owner = OwnerOrderContext(
        "main_scalping", "main:t", "position:t", "initial_quantity:e:leg0"
    )
    context = guard.PhysicalEntrySendContext(
        operation="INITIAL_QUANTITY_LEG0",
        owner_identity=(
            owner.owner_type,
            owner.owner_id,
            owner.position_id,
            owner.client_intent_id,
        ),
        code="005930",
        quantity=2,
        broker_route="SOR",
        order_type="0",
        broker_price="100",
        evaluation_attempt_id="evaluation",
        ai_decision_trace_id="trace",
        decision_binding="decision",
        source_policy_binding=policy_binding,
        source_policy_receipt=guard.canonical_binding(policy.to_dict()),
        source_policy_version="configured_quote_time_policy_v1",
        max_quote_age_ms=700,
        original_deadline_epoch=105,
        original_deadline_perf=15,
        source_item="005930_AL",
        source_market_route="krx_nxt_integrated",
        source_transport_epoch=7,
        quote_observed_epoch=99.8,
        source_type="0D",
        source_route_sequence=10,
        best_bid=100,
        best_ask=101,
        current_price=100,
        snapshot_reader=lambda: state["snapshot"],
        binding_reader=lambda: state["binding"],
    )
    payload = {
        "stk_cd": "005930",
        "ord_qty": "2",
        "dmst_stex_tp": "SOR",
        "trde_tp": "0",
        "ord_uv": "100",
    }
    return SimpleNamespace(
        clock=clock, state=state, context=context, owner=owner, payload=payload
    )


def check(case, **kwargs):
    return guard.check_entry_send_context(
        case.context,
        api_id="kt10000",
        owner_context=case.owner,
        payload=case.payload,
        **kwargs,
    )


@pytest.mark.parametrize("clock", ["epoch", "perf"])
def test_expired_original_budget_never_enters_expensive_readers(case, clock):
    setattr(case.clock, clock, 105.001 if clock == "epoch" else 15.001)
    calls = []
    context = replace(
        case.context,
        binding_reader=lambda: calls.append("binding") or case.state["binding"],
        snapshot_reader=lambda: calls.append("snapshot") or case.state["snapshot"],
    )
    with pytest.raises(guard.EntrySendGuardBlocked) as blocked:
        context.check(api_id="kt10000", owner_context=case.owner, payload=case.payload)
    assert blocked.value.receipt["reason"] == "original_entry_deadline_expired"
    assert calls == []


def test_policy_revalidation_clock_survives_physical_terminal(case):
    error = ValueError("auxiliary_decision_generation_changed")
    error.entry_submit_revalidation = {
        "entered_epoch": 104.9,
        "checked_epoch": 105.2,
        "original_signal_epoch": 100.0,
        "native_load_ms": 300.0,
    }

    def fail():
        raise error

    with pytest.raises(guard.EntrySendGuardBlocked) as blocked:
        guard.check_entry_send_context(
            replace(case.context, binding_reader=fail),
            api_id="kt10000",
            owner_context=case.owner,
            payload=case.payload,
        )
    result = blocked.value.receipt
    assert not result["allowed"]
    assert result["revalidation_error"] == str(error)
    assert result["entry_submit_revalidation"] == error.entry_submit_revalidation


def transport(case, monkeypatch, responses):
    posts = []

    def post(*args, **kwargs):
        posts.append(kwargs)
        result = responses[len(posts) - 1]
        if isinstance(result, Exception):
            raise result
        return SimpleNamespace(status_code=200, json=lambda: result)

    monkeypatch.setattr(orders.requests, "post", post)
    monkeypatch.setattr(
        orders.kiwoom_utils, "get_kiwoom_token_after_auth_failure", lambda **_: "fresh"
    )
    return posts


def send(case, **kwargs):
    return orders._post_kiwoom_with_auth_retry(
        "https://example.test/api/dostk/ordr",
        {"api-id": "kt10000", "authorization": "Bearer token"},
        case.payload,
        "kt10000",
        entry_send_context=case.context,
        entry_owner_context=case.owner,
        **kwargs,
    )


def test_context_is_immutable_and_leg0_intent_does_not_need_entry_buy_substring(case):
    assert check(case)["allowed"] is True
    with pytest.raises(FrozenInstanceError):
        case.context.original_deadline_epoch = 200


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"snapshot": snapshot(98)}, "canonical_quote_source_binding_invalid"),
        ({"snapshot": snapshot(100.1)}, "canonical_quote_expired_or_future"),
        ({"snapshot": snapshot(epoch=8)}, "canonical_quote_source_binding_invalid"),
        ({"snapshot": snapshot(ask=102)}, "execution_price_changed_reprice_required"),
        ({"snapshot": snapshot(curr=102)}, "execution_price_changed_reprice_required"),
        (
            {"binding": ("new-evaluation", "policy")},
            "decision_or_time_policy_binding_changed",
        ),
        (
            {"binding": ("decision", "new-policy")},
            "decision_or_time_policy_binding_changed",
        ),
    ],
)
def test_changed_source_price_or_authority_blocks_before_post(case, change, reason):
    case.state.update(change)
    with pytest.raises(guard.EntrySendGuardBlocked, match=reason):
        check(case)


def test_new_same_price_exact_quote_can_refresh_age_without_renewing_deadline(case):
    case.clock.epoch = 101
    case.state["snapshot"] = snapshot(100.9)
    assert check(case)["canonical_quote_age_ms"] == pytest.approx(100)
    case.clock.perf = 15
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="original_entry_deadline_expired"
    ):
        check(case)
    assert case.context.original_deadline_epoch == 105


@pytest.mark.parametrize(
    "flag", ["quote_stale", "context_stale", "price_conflict", "source_conflict"]
)
def test_explicit_current_source_conflict_is_not_hidden_by_matching_prices(case, flag):
    case.state["snapshot"][flag] = True
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="current_quote_explicitly_invalid"
    ):
        check(case)


@pytest.mark.parametrize(
    "mutation",
    [
        {"operation": "INITIAL_QUANTITY_LEG1"},
        {"operation": "SCALE_IN_BUY"},
        {"operation": "ENTRY_RESIDUAL_BUY"},
        {"operation": "ENTRY_REPRICE_BUY"},
        {
            "owner_identity": (
                "manual",
                "main:t",
                "position:t",
                "initial_quantity:e:leg0",
            )
        },
        {"owner_identity": ()},
        {"original_deadline_epoch": float("nan")},
        {"max_quote_age_ms": 1000},
    ],
)
def test_invalid_explicit_context_fails_closed(case, mutation):
    case.context = replace(case.context, **mutation)
    with pytest.raises(guard.EntrySendGuardBlocked):
        check(case)


def test_token_preparation_delay_is_checked_after_resolve_before_first_post(
    case, monkeypatch
):
    posts = transport(case, monkeypatch, [{"return_code": "0", "ord_no": "1234567"}])

    def delayed_token(token):
        case.clock.epoch = 105
        return token

    monkeypatch.setattr(
        orders.kiwoom_utils, "resolve_kiwoom_request_token", delayed_token
    )
    with pytest.raises(guard.EntrySendGuardBlocked) as result:
        send(case)
    assert posts == []
    assert result.value.response()["broker_order_attempted"] is False


def test_auth_refresh_delay_cannot_reset_original_deadline(case, monkeypatch):
    auth = {"return_code": "8005", "return_msg": "token expired"}
    posts = transport(case, monkeypatch, [auth])

    def delayed_auth(**_):
        case.clock.perf = 15
        return "fresh"

    monkeypatch.setattr(
        orders.kiwoom_utils, "get_kiwoom_token_after_auth_failure", delayed_auth
    )
    with pytest.raises(guard.EntrySendGuardBlocked) as result:
        send(case)
    assert len(posts) == 1
    blocked = result.value.response()
    assert blocked["physical_send_attempt_count"] == 1
    assert blocked["rejected_auth_response"]["return_code"] == "8005"


def test_each_permitted_auth_post_has_same_original_identity(case, monkeypatch):
    posts = transport(
        case,
        monkeypatch,
        [
            {"return_code": "8005", "return_msg": "token expired"},
            {"return_code": "0", "ord_no": "1234567"},
        ],
    )
    _, data = send(case)
    assert len(posts) == 2
    receipts = data["entry_send_guard_receipts"]
    assert len(receipts) == 2
    assert {r["client_intent_id"] for r in receipts} == {case.owner.client_intent_id}
    assert {r["original_deadline_epoch"] for r in receipts} == {105}


def test_uncertain_transport_does_not_retry(case, monkeypatch):
    posts = transport(case, monkeypatch, [TimeoutError("unknown send")])
    with pytest.raises(TimeoutError):
        send(case)
    assert len(posts) == 1


def test_successful_post_is_not_reclassified_when_response_arrives_after_deadline(
    case, monkeypatch
):
    def post(*_, **__):
        case.clock.epoch = 110
        return SimpleNamespace(
            status_code=200, json=lambda: {"return_code": "0", "ord_no": "1234567"}
        )

    monkeypatch.setattr(orders.requests, "post", post)
    _, data = send(case)
    assert data["return_code"] == "0"
    assert data["ord_no"] == "1234567"


@pytest.mark.parametrize(
    "api_id", ["kt10000", "kt10001", "kt10003", "kt00001", "kt00018"]
)
def test_no_explicit_context_leaves_other_operations_and_followup_buys_unchanged(
    case, monkeypatch, api_id
):
    posts = transport(case, monkeypatch, [{"return_code": "0"}])
    case.clock.epoch = 1000
    monkeypatch.setattr(
        orders.kiwoom_utils,
        "acquire_kiwoom_read_capacity",
        lambda **_: SimpleNamespace(admitted=True),
    )
    _, data = orders._post_kiwoom_with_auth_retry(
        "https://example.test/api", {"api-id": api_id}, {}, api_id
    )
    assert len(posts) == 1
    assert "entry_send_guard_receipts" not in data


def test_header_api_owner_and_quantity_are_bound(case, monkeypatch):
    posts = transport(case, monkeypatch, [])
    case.payload["ord_qty"] = "3"
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="order_payload_binding_changed"
    ):
        send(case)
    case.payload["ord_qty"] = "2"
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="operation_owner_api_binding_invalid"
    ):
        orders._post_kiwoom_with_auth_retry(
            "https://example.test/api",
            {"api-id": "kt10001"},
            case.payload,
            "kt10000",
            entry_send_context=case.context,
            entry_owner_context=case.owner,
        )
    assert posts == []


def test_telemetry_lock_delay_is_consumed_before_guard_and_local_veto_is_not_physical(
    case, monkeypatch
):
    import importlib
    import threading
    from src.utils import kiwoom_transport_telemetry as telemetry

    telemetry = importlib.reload(telemetry)
    lock = threading.Lock()

    class DelayedLock:
        def __enter__(self):
            lock.acquire()
            case.clock.epoch = 105
            case.clock.perf = 15

        def __exit__(self, *_):
            lock.release()

    monkeypatch.setattr(telemetry, "_LOCK", DelayedLock())
    posts = transport(case, monkeypatch, [])
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="original_entry_deadline_expired"
    ):
        send(case)
    assert posts == []
    totals = telemetry.snapshot()["cumulative_totals"]
    assert totals.get("started", 0) == totals.get("terminal", 0) == 0
    assert totals["inflight_unknown"] == 0
    assert totals["local_not_sent"] == 1
    assert telemetry.snapshot()["recent_attempts"] == []


def test_local_veto_accounting_survives_minute_eviction(case, monkeypatch):
    import importlib
    from src.utils import kiwoom_transport_telemetry as telemetry

    telemetry = importlib.reload(telemetry)
    calls = []

    def before_call():
        for index in range(600):
            case.clock.epoch = 1060 + index * 60
            telemetry.measured_http_call(
                lambda *_, **__: SimpleNamespace(status_code=200),
                "https://example.test/read",
                telemetry_owner="real-read",
                headers={"api-id": "ka10080"},
            )
        raise guard.EntrySendGuardBlocked({"reason": "local-veto"})

    with pytest.raises(guard.EntrySendGuardBlocked):
        telemetry.measured_http_call(
            lambda *_, **__: calls.append(True),
            "https://example.test/order",
            telemetry_owner="vetoed-buy",
            headers={"api-id": "kt10000"},
            before_call=before_call,
        )
    assert calls == []
    result = telemetry.snapshot()
    assert (
        result["cumulative_totals"]["started"]
        == result["cumulative_totals"]["terminal"]
        == 600
    )
    assert result["cumulative_totals"]["inflight_unknown"] == 0
    assert (
        sum(row.get("started", 0) for row in result["minute_buckets"])
        + result["evicted_minute_totals"]["started"]
        == 600
    )
    assert (
        sum(row.get("terminal", 0) for row in result["minute_buckets"])
        + result["evicted_minute_totals"]["terminal"]
        == 600
    )


def test_adapter_returns_known_local_no_call_and_does_not_mark_registry_ambiguous(
    case, monkeypatch
):
    from datetime import datetime

    posts = transport(case, monkeypatch, [])
    monkeypatch.setattr(orders, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(orders, "is_buy_side_time_blocked", lambda _now: False)
    monkeypatch.setattr(orders, "is_scalping_buy_window_blocked", lambda _now: False)
    monkeypatch.setattr(
        orders, "_reserve_owner_registry_intent", lambda **_: (None, None, None)
    )
    finalized = []
    monkeypatch.setattr(
        orders,
        "_finish_owner_registry_intent",
        lambda *_, **kwargs: finalized.append(kwargs),
    )
    case.clock.perf = 15
    result = orders.send_buy_order(
        "005930",
        2,
        100,
        "0",
        token="fake",
        dmst_stex_tp="SOR",
        now=datetime(2026, 10, 15, 10, tzinfo=orders.KST),
        owner_context=case.owner,
        entry_send_context=case.context,
    )
    assert posts == []
    assert result["entry_send_guard_blocked"] is True
    assert result["broker_order_attempted"] is False
    assert finalized[0]["response"]["return_code"] == "ENTRY_SEND_GUARD_BLOCKED"
    assert "ambiguous_reason" not in finalized[0]


@pytest.mark.parametrize("order_type", ["0", "00", "3"])
@pytest.mark.parametrize("unrelated_fields", [False, True])
@pytest.mark.parametrize(
    "mutation",
    [
        "buy_qty",
        "status",
        "pause",
        "manual",
        "decision",
        "policy",
        "native_signal",
        "selected_branch_v5",
        "selected_branch_v6",
        "deadline_owner",
        "arm_owner",
        "inactive_consistency_limit",
        "ai_clock_anchor",
        "ai_confirmation",
    ],
)
def test_main_producer_rechecks_current_state_authority_and_policy_after_token_delay(
    case, monkeypatch, mutation, unrelated_fields, order_type
):
    from src.engine import sniper_state_handlers as main
    from src.engine.scalping import (
        scanner_async_eval,
        reversal_auxiliary_intraday,
        reversal_source_diagnostics,
        reversal_current_backend,
    )
    from src.trading.entry.quote_time_policy import QuoteTimePolicy

    machine = {
        "entry_primary_decision_owner": "mechanistic_entry_adjudicator",
        "entry_mechanistic_action": "ENTER_NOW",
        "evaluation_attempt_id": "evaluation",
        "entry_mechanistic_policy_sha256": "a" * 64,
        "entry_ai_screen_status": "pass",
        "entry_ai_screen_pass": True,
        "entry_ai_effective_assessment": {"effective_verdict": "PASS"},
    }
    if mutation.startswith("selected_branch"):
        machine["entry_mechanistic_policy_decision"] = {
            "policy_version": "continuous_reversal_policy_"
            + mutation.rsplit("_", 1)[-1],
            "matched_policy_refs": ["selected:hash"],
        }
    stock = {
        "id": "target",
        "status": "WATCHING",
        "buy_qty": 0,
        "last_watching_ai_machine_primary_fields": dict(machine),
        "last_watching_ai_decision_trace_id": "trace",
        "last_watching_ai_confirmed_at": 98.0,
    }
    original = SimpleNamespace(
        code="005930",
        native_claim={"event_id": "signal"},
        ai_payload={
            **machine,
            "ai_decision_trace_id": "trace",
            "entry_ai_quote_time_policy_receipt": QuoteTimePolicy().to_dict(),
        },
        prepared_context={
            "final_entry_refresh_fields": {
                "entry_ai_quote_time_policy_receipt": QuoteTimePolicy().to_dict()
            }
        },
        deadline_epoch=105,
        deadline_perf=15,
    )
    if unrelated_fields:

        class Unused(dict):
            def items(self):
                raise AssertionError("unrelated replay payload traversed at submit")

        original.ai_payload["unused_replay_capsule"] = Unused(large="fixture")
        original.prepared_context["unused_feature_packet"] = Unused(large="fixture")
    # The committed provenance includes the exact trace as the production
    # Main consumer does; its display telemetry is not used by this test.
    stock["last_watching_ai_machine_primary_fields"]["ai_decision_trace_id"] = "trace"
    policy = {"value": QuoteTimePolicy()}
    veto = {
        "pause": False,
        "manual": False,
        "native_signal": False,
        "branch": "selected",
    }
    monkeypatch.setattr(main, "_entry_quote_time_policy", lambda: policy["value"])
    monkeypatch.setattr(main, "_machine_submit_revision_is_current", lambda *_: True)
    monkeypatch.setattr(main, "_has_retired_entry_source", lambda *_: False)
    monkeypatch.setattr(
        main,
        "WS_MANAGER",
        SimpleNamespace(get_latest_data=lambda _: case.state["snapshot"]),
    )
    monkeypatch.setattr(main.kiwoom_orders, "is_buy_side_paused", lambda: veto["pause"])
    monkeypatch.setattr(main.kiwoom_orders, "is_buy_side_time_blocked", lambda _: False)
    monkeypatch.setattr(
        main,
        "evaluate_main_bot_control_exclusion",
        lambda *_, **__: SimpleNamespace(excluded=veto["manual"]),
    )
    monkeypatch.setattr(
        reversal_auxiliary_intraday, "validate_submit", lambda *_, **__: None
    )
    monkeypatch.setattr(
        reversal_current_backend,
        "backend",
        lambda *_: SimpleNamespace(_GENERATION="native-family"),
    )

    def validate_native(*_, **__):
        if veto["native_signal"]:
            raise ValueError("reversal_all_signals_invalidated")
        return ({"branch_signals": {veto["branch"]: {}}}, {})

    monkeypatch.setattr(
        reversal_source_diagnostics, "validate_claim_with_receipt", validate_native
    )
    from src.engine.scalping import (
        reversal_extended_union,
        reversal_operating_auxiliary,
    )

    monkeypatch.setattr(reversal_extended_union, "definition_hash", lambda _: "hash")
    monkeypatch.setattr(
        reversal_operating_auxiliary, "definition_hash", lambda _: "hash"
    )
    token = scanner_async_eval.ASYNC_CONSUMPTION.set({"original_result": original})
    try:
        if mutation == "ai_clock_anchor":
            monkeypatch.setattr(main.time, "time", lambda: 99.0)
        context = main._main_initial_physical_send_context(
            stock,
            "005930",
            snapshot(),
            owner_context=case.owner,
            quantity=2,
            broker_route="SOR",
            order_type=order_type,
            broker_price=100,
            ai_authority={
                "entry_ai_submit_authority_confirmed_at": 98.0,
                "entry_ai_submit_authority_max_prior_age_sec": "3.0",
            },
        )
        monkeypatch.setattr(main.time, "time", lambda: case.clock.epoch)
        case.payload.update(trde_tp=order_type, ord_uv="" if order_type == "3" else "100")
        assert context.ai_authority_expires_epoch == 101.0
        assert context.ai_authority_expires_perf == 11.0
        assert context.check(
            api_id="kt10000", owner_context=case.owner, payload=case.payload
        )["allowed"]
        if order_type == "3":
            with pytest.raises(guard.EntrySendGuardBlocked, match="order_payload_binding_changed"):
                context.check(api_id="kt10000", owner_context=case.owner,
                              payload={**case.payload, "ord_uv": "100"})
        if mutation == "buy_qty" and order_type in {"0", "3"}:
            # Exercise the real adapter and transport hook with a fake POST.
            # No broker call, altered payload, or bypassed physical guard.
            from datetime import datetime
            posts = transport(case, monkeypatch, [{"return_code": "0", "ord_no": "offline"}])
            monkeypatch.setattr(orders, "is_scalping_buy_window_blocked", lambda _: False)
            monkeypatch.setattr(orders, "_reserve_owner_registry_intent", lambda **_: (None, None, None))
            monkeypatch.setattr(orders, "_finish_owner_registry_intent", lambda *a, **kw: None)
            result = orders.send_buy_order(
                "005930", 2, 100, order_type, token="fake", dmst_stex_tp="SOR",
                now=datetime(2026, 10, 27, 10, tzinfo=orders.KST),
                owner_context=case.owner, entry_send_context=context,
            )
            assert result["return_code"] == "0" and len(posts) == 1
            assert posts[0]["json"]["ord_uv"] == context.broker_price
        if mutation == "ai_clock_anchor":
            case.clock.perf = 11.1
        elif mutation == "ai_confirmation":
            stock["last_watching_ai_confirmed_at"] = 99.0
        elif mutation == "buy_qty":
            stock["buy_qty"] = 1
        elif mutation == "status":
            stock["status"] = "HOLDING"
        elif mutation in {"pause", "manual", "native_signal"}:
            veto[mutation] = True
        elif mutation == "decision":
            stock["last_watching_ai_machine_primary_fields"][
                "entry_ai_screen_pass"
            ] = False
        elif mutation.startswith("selected_branch"):
            veto["branch"] = "unrelated"
        elif mutation == "deadline_owner":
            stock["_async_entry_decision_deadline"] = {"request_id": "replaced"}
        elif mutation == "arm_owner":
            stock["_entry_arm_native_owner"] = {"request_id": "replaced"}
        elif mutation == "inactive_consistency_limit":
            policy["value"] = replace(policy["value"], consistency_ws_max_age_ms=123)
        else:
            policy["value"] = replace(policy["value"], latency_caution_ms=800)
        if mutation == "inactive_consistency_limit":
            assert context.check(
                api_id="kt10000", owner_context=case.owner, payload=case.payload
            )["allowed"]
        else:
            with pytest.raises(guard.EntrySendGuardBlocked):
                context.check(
                    api_id="kt10000", owner_context=case.owner, payload=case.payload
                )
    finally:
        scanner_async_eval.ASYNC_CONSUMPTION.reset(token)


@pytest.mark.parametrize(
    "changed",
    [
        "none",
        "request",
        "evaluation",
        "trace",
        "native_token",
        "deadline",
        "expired",
        "perf_expired",
    ],
)
def test_deferred_native_arm_uses_only_its_immutable_original_lifetime(
    case, monkeypatch, changed
):
    from src.engine import sniper_state_handlers as main
    from src.engine.scalping.scanner_async_eval import ASYNC_CONSUMPTION

    monkeypatch.setattr(
        guard, "_INITIAL_RESULTS", __import__("collections").OrderedDict()
    )
    original = SimpleNamespace(
        request_id="native-request",
        code="005930",
        native_claim={"token": "native-token"},
        deadline_epoch=105,
        deadline_perf=15,
        ai_payload={
            "evaluation_attempt_id": "evaluation",
            "ai_decision_trace_id": "trace",
        },
    )
    guard.retain_initial_native_result(original)
    stock = {
        "_entry_arm_native_owner": {
            "request_id": "native-request",
            "evaluation_attempt_id": "evaluation",
            "ai_decision_trace_id": "trace",
            "native_claim_token": "native-token",
        },
        "_async_entry_decision_deadline": {
            "request_id": "native-request",
            "evaluation_attempt_id": "evaluation",
            "ai_decision_trace_id": "trace",
            "deadline_epoch": 105,
            "deadline_perf": 15,
        },
    }
    if changed == "request":
        stock["_async_entry_decision_deadline"]["request_id"] = "other"
    elif changed == "evaluation":
        stock["_entry_arm_native_owner"]["evaluation_attempt_id"] = "other"
    elif changed == "trace":
        stock["_entry_arm_native_owner"]["ai_decision_trace_id"] = "other"
    elif changed == "native_token":
        stock["_entry_arm_native_owner"]["native_claim_token"] = "other"
    elif changed == "deadline":
        stock["_async_entry_decision_deadline"]["deadline_epoch"] = 106
    elif changed == "expired":
        case.clock.epoch = 105
    elif changed == "perf_expired":
        case.clock.perf = 15
    token = ASYNC_CONSUMPTION.set(None)
    try:
        if changed == "none":
            assert main._initial_native_result_for_send(stock, "005930") is original
            assert original.deadline_epoch == 105
        else:
            with pytest.raises(
                ValueError, match="deferred_native_result_unavailable_or_changed"
            ):
                main._initial_native_result_for_send(stock, "005930")
    finally:
        ASYNC_CONSUMPTION.reset(token)


@pytest.mark.parametrize("clock_field", ["epoch", "perf"])
def test_applicable_ai_expiry_is_rechecked_before_physical_send(
    case, monkeypatch, clock_field
):
    case.context = replace(
        case.context, ai_authority_expires_epoch=101, ai_authority_expires_perf=11
    )
    posts = transport(case, monkeypatch, [])
    setattr(case.clock, clock_field, 101.1 if clock_field == "epoch" else 11.1)
    case.state["snapshot"] = snapshot(case.clock.epoch - 0.1)
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="ai_authority_expired_before_physical_send"
    ):
        send(case)
    assert posts == []
    assert case.context.original_deadline_epoch == 105


def test_auth_refresh_does_not_renew_ai_authority(case, monkeypatch):
    case.context = replace(
        case.context, ai_authority_expires_epoch=101, ai_authority_expires_perf=11
    )
    posts = transport(
        case, monkeypatch, [{"return_code": "8005", "return_msg": "Token expired"}]
    )

    def refresh(**_):
        case.clock.epoch = 101.1
        case.clock.perf = 11.1
        case.state["snapshot"] = snapshot(101.0)
        return "refreshed"

    monkeypatch.setattr(
        orders.kiwoom_utils, "get_kiwoom_token_after_auth_failure", refresh
    )
    with pytest.raises(
        guard.EntrySendGuardBlocked, match="ai_authority_expired_before_physical_send"
    ) as raised:
        send(case)
    assert len(posts) == 1 and raised.value.attempts == 1
    assert raised.value.response()["broker_order_attempted"] is True
    assert not orders.is_verified_local_buy_no_call_response(raised.value.response())


def test_decoded_no_call_fields_cannot_forge_adapter_local_proof():
    forged = {
        "return_code": "ENTRY_SEND_GUARD_BLOCKED",
        "entry_send_guard_blocked": True,
        "physical_send_attempt_count": 0,
        "broker_order_attempted": False,
        "ord_no": "",
    }
    assert not orders.is_verified_local_buy_no_call_response(forged)
    local = orders._local_buy_no_call_response(forged)
    assert orders.is_verified_local_buy_no_call_response(local)
    import json

    assert not orders.is_verified_local_buy_no_call_response(
        json.loads(json.dumps(local))
    )
    assert not orders.is_verified_local_buy_no_call_response(
        {**local, "ord_no": "0000123"}
    )
    assert not orders.is_verified_local_buy_no_call_response(
        {**local, "physical_send_attempt_count": 1}
    )


@pytest.mark.parametrize("local_stage", ["pause", "time", "preflight", "owner"])
def test_all_local_buy_adapter_vetoes_have_process_local_zero_wire_proof(
    case, monkeypatch, local_stage
):
    from datetime import datetime

    posts = transport(case, monkeypatch, [])
    monkeypatch.setattr(
        orders, "EventBus", lambda: SimpleNamespace(publish=lambda *a, **k: None)
    )
    monkeypatch.setattr(orders, "is_buy_side_paused", lambda: local_stage == "pause")
    monkeypatch.setattr(
        orders, "is_buy_side_time_blocked", lambda _: local_stage == "time"
    )
    monkeypatch.setattr(orders, "is_scalping_buy_window_blocked", lambda _: False)
    monkeypatch.setattr(
        orders,
        "_reserve_owner_registry_intent",
        lambda **_: (
            None,
            None,
            orders._owner_registry_block_response("already reserved"),
        ),
    )
    if local_stage == "preflight":
        monkeypatch.setattr(
            orders,
            "_resolve_submit_order_type_preflight",
            lambda **_: (None, SimpleNamespace(allowed=False)),
        )
        monkeypatch.setattr(
            orders,
            "_order_type_preflight_block_response",
            lambda **_: dict(
                return_code="ORDER_TYPE_PREFLIGHT_BLOCKED",
                return_msg="nxt_market_to_best_limit",
            ),
        )
    result = orders.send_buy_order(
        "005930",
        2,
        100,
        "0",
        token="fake",
        dmst_stex_tp="SOR",
        now=datetime(2026, 10, 15, 10, tzinfo=orders.KST),
        owner_context=case.owner,
    )
    assert posts == []
    assert orders.is_verified_local_buy_no_call_response(result)
    assert not result.get("_local_buy_reserved_intent_id")
