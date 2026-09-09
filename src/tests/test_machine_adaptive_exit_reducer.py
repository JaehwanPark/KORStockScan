from dataclasses import replace

import pytest

from src.trading.order.adaptive_exit.reducer import (
    ExitEvent,
    ExitState,
    OrderKey,
    reduce_event,
)

TARGET = OrderKey("2026-09-09", "123")
SELL = OrderKey("2026-09-09", "124")


def initial():
    return ExitState("widget", "ep", "lot", "policy", "epoch", TARGET, 10)


def event(kind, **kwargs):
    return ExitEvent(
        kind,
        kind,
        "widget",
        "ep",
        "lot",
        "policy",
        "epoch",
        "intent1",
        kwargs.pop("order", TARGET),
        **kwargs,
    )


def cancel_pending():
    state = reduce_event(initial(), event("EXIT_INTENT"))
    return reduce_event(state, event("CANCEL_REQUESTED"))


def residual(*, filled=0, trailing=False):
    state = initial()
    state = reduce_event(
        state,
        event("EXIT_INTENT", intent_kind="trail_arm" if trailing else "early_exit"),
    )
    state = reduce_event(state, event("CANCEL_REQUESTED"))
    return reduce_event(
        state,
        event(
            "CANCEL_CONFIRMED",
            exact_terminal_reconciled=True,
            receipt_hash="terminal",
            cumulative_fill=filled,
        ),
    )


def test_cancel_ack_not_terminal_and_no_sell_before_terminal():
    state = cancel_pending()
    assert state.reserved_qty == 10
    with pytest.raises(ValueError, match="not_ack"):
        reduce_event(state, event("CANCEL_CONFIRMED", receipt_hash="ack"))
    with pytest.raises(ValueError, match="invalid_transition"):
        reduce_event(state, event("EXIT_SUBMIT_INTENT", quantity=10))


def test_cancel_fill_race_closes_without_reentry_or_extra_sell():
    state = residual(filled=10)
    assert state.phase == "FLAT" and state.open_qty == state.reserved_qty == 0
    with pytest.raises(ValueError):
        reduce_event(state, event("EXIT_SUBMIT_INTENT", quantity=1))


def test_partial_target_then_residual_sell_with_exact_cumulative_fills():
    state = residual(filled=4)
    assert state.open_qty == 6 and state.reserved_qty == 0
    state = reduce_event(state, event("EXIT_SUBMIT_INTENT", quantity=6))
    assert state.phase == "EXIT_SUBMITTING" and state.reserved_qty == 6
    state = reduce_event(state, event("EXIT_SUBMITTED", order=SELL, receipt_hash="ack"))
    assert state.phase == "EXIT_WORKING" and state.open_qty == 6
    state = reduce_event(
        state, event("EXIT_FILL", order=SELL, receipt_hash="fill1", cumulative_fill=2)
    )
    assert state.open_qty == state.reserved_qty == 4
    final = replace(
        event("EXIT_FILL", order=SELL, receipt_hash="fill2", cumulative_fill=6),
        event_id="fill2",
    )
    assert reduce_event(state, final).phase == "FLAT"


def test_crash_before_or_after_api_does_not_grant_resubmit():
    state = reduce_event(residual(), event("EXIT_SUBMIT_INTENT", quantity=10))
    assert reduce_event(state, event("EXIT_SUBMIT_INTENT", quantity=10)) == state
    with pytest.raises(ValueError):
        reduce_event(
            state, replace(event("EXIT_SUBMIT_INTENT", quantity=10), event_id="retry")
        )
    recovery = reduce_event(state, event("RECOVERY_REQUIRED"))
    assert recovery.reserved_qty == 10 and recovery.open_qty == 10
    with pytest.raises(ValueError):
        reduce_event(
            recovery,
            replace(event("EXIT_SUBMIT_INTENT", quantity=10), event_id="retry"),
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"owner_id": "main"},
        {"episode_id": "other"},
        {"policy_hash": "other"},
        {"position_epoch": "other"},
        {"lot_id": "other"},
        {"order": OrderKey("2026-09-08", "123")},
        {"pending_buy": True},
        {"other_reserved_sell_qty": 1},
        {"pending_buy": "false"},
    ],
)
def test_owner_date_and_reservation_guards(patch):
    with pytest.raises(ValueError):
        reduce_event(initial(), replace(event("EXIT_INTENT"), **patch))


def test_duplicate_ids_require_same_payload():
    state = reduce_event(initial(), event("EXIT_INTENT"))
    assert reduce_event(state, event("EXIT_INTENT")) == state
    with pytest.raises(ValueError, match="payload_conflict"):
        reduce_event(state, replace(event("EXIT_INTENT"), quantity=9))


def test_trail_only_arms_after_cancel_and_cannot_lower_stop():
    state = residual(trailing=True)
    state = reduce_event(
        state,
        event("TRAIL_ARMED", receipt_hash="fresh", high_water=10050, stop_price=10030),
    )
    assert state.phase == "TRAIL_ACTIVE"
    with pytest.raises(ValueError, match="monotonic"):
        reduce_event(
            state,
            event(
                "TRAIL_UPDATED",
                receipt_hash="fresh2",
                high_water=10050,
                stop_price=10025,
            ),
        )
    state = reduce_event(state, event("EXIT_SUBMIT_INTENT", quantity=10))
    assert state.phase == "EXIT_SUBMITTING"


@pytest.mark.parametrize("quantity", [-1, 0, True, 11, 1.5])
def test_invalid_exit_quantity(quantity):
    with pytest.raises(ValueError):
        reduce_event(residual(), event("EXIT_SUBMIT_INTENT", quantity=quantity))


@pytest.mark.parametrize(
    "patch",
    [
        {"target_terminal": "false"},
        {"phase": "UNKNOWN"},
        {"phase": "RESIDUAL_READY", "target_terminal": True},
    ],
)
def test_malformed_restored_state_never_drops_target_reservation(patch):
    with pytest.raises(ValueError):
        reduce_event(
            replace(initial(), **patch), event("EXIT_SUBMIT_INTENT", quantity=10)
        )
