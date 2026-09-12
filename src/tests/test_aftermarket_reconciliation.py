from dataclasses import replace

from src.trading.order.aftermarket_reconciliation import (
    ChildOrderBinding,
    DurableParentIntent,
    OrderEvidence,
    ReconciliationState,
    reconcile_aftermarket_boundary,
)


INTENT_HASH = "a" * 64


def _binding(order_no: str, route: str, qty: int, **kwargs: object) -> ChildOrderBinding:
    return ChildOrderBinding(
        broker_order_no=order_no,
        original_order_no=str(kwargs.get("original_order_no", "")),
        route=route,
        requested_qty=qty,
        cancel_order_no=str(kwargs.get("cancel_order_no", "")),
    )


def _intent(route: str, qty: int, children: tuple[ChildOrderBinding, ...]) -> DurableParentIntent:
    return DurableParentIntent(
        intent_id="intent-1",
        account_key="account-a",
        order_date="2026-09-11",
        symbol="005930",
        side="BUY",
        requested_route=route,
        requested_qty=qty,
        parent_order_no="9000001",
        intent_sha256=INTENT_HASH,
        children=children,
    )


def _evidence(
    binding: ChildOrderBinding,
    source_api: str,
    *,
    filled: int,
    canceled: int,
    remaining: int,
    state: str,
    hash_char: str,
) -> OrderEvidence:
    return OrderEvidence(
        source_api=source_api,
        account_key="account-a",
        symbol="005930",
        side="BUY",
        broker_order_no=binding.broker_order_no,
        original_order_no=binding.original_order_no,
        route=binding.route,
        requested_qty=binding.requested_qty,
        filled_qty=filled,
        confirmed_cancel_qty=canceled,
        remaining_qty=remaining,
        state=state,
        receipt_sha256=hash_char * 64,
        order_date="2026-09-11",
        cancel_order_no=binding.cancel_order_no,
    )


def test_krx_terminal_cancel_releases_only_conserved_quantity() -> None:
    child = _binding("1000001", "KRX", 10, cancel_order_no="2000001")
    result = reconcile_aftermarket_boundary(
        _intent("KRX", 10, (child,)),
        [_evidence(child, "kt00007", filled=4, canceled=6, remaining=0, state="TERMINAL", hash_char="b")],
        [],
        current_snapshot_complete=True,
    )

    assert result.state is ReconciliationState.TERMINAL
    assert result.terminal is True
    assert result.intent_sha256 == INTENT_HASH
    assert result.parent_order_no == "9000001"
    assert result.source_sha256s == ("b" * 64,)
    assert (result.filled_qty, result.confirmed_cancel_qty, result.broker_remaining_qty) == (4, 6, 0)
    assert result.releasable_qty == 6
    assert result.successor_blocked is False


def test_nxt_open_child_blocks_successor_and_preserves_remaining() -> None:
    child = _binding("1000002", "NXT", 10)
    dated = _evidence(child, "kt00007", filled=3, canceled=0, remaining=7, state="OPEN", hash_char="c")
    current = _evidence(child, "ka10075", filled=3, canceled=0, remaining=7, state="OPEN", hash_char="d")
    result = reconcile_aftermarket_boundary(
        _intent("NXT", 10, (child,)),
        [dated],
        [current],
        current_snapshot_complete=True,
    )

    assert result.state is ReconciliationState.OPEN
    assert result.terminal is False
    assert result.broker_remaining_qty == 7
    assert result.releasable_qty == 0
    assert result.successor_blocked is True
    assert "nxt_child_open" in result.reasons


def test_sor_parent_is_not_terminal_when_krx_closes_but_nxt_is_open() -> None:
    krx = _binding("1000003", "KRX", 4, original_order_no="9000001")
    nxt = _binding("1000004", "NXT", 6, original_order_no="9000001")
    result = reconcile_aftermarket_boundary(
        _intent("SOR", 10, (krx, nxt)),
        [
            _evidence(krx, "kt00007", filled=4, canceled=0, remaining=0, state="TERMINAL", hash_char="e"),
            _evidence(nxt, "kt00007", filled=0, canceled=0, remaining=6, state="OPEN", hash_char="f"),
        ],
        [_evidence(nxt, "ka10075", filled=0, canceled=0, remaining=6, state="OPEN", hash_char="1")],
        current_snapshot_complete=True,
    )

    assert result.state is ReconciliationState.OPEN
    assert result.terminal is False
    assert (result.filled_qty, result.broker_remaining_qty) == (4, 6)
    assert result.releasable_qty == 0


def test_partial_cancel_quantity_mismatch_fails_closed() -> None:
    child = _binding("1000005", "KRX", 10, cancel_order_no="2000005")
    result = reconcile_aftermarket_boundary(
        _intent("KRX", 10, (child,)),
        [_evidence(child, "kt00007", filled=4, canceled=5, remaining=0, state="TERMINAL", hash_char="2")],
        [],
        current_snapshot_complete=True,
    )

    assert result.state is ReconciliationState.UNKNOWN
    assert result.terminal is False
    assert result.filled_qty is None
    assert "quantity_conservation_failed" in result.reasons


def test_empty_incomplete_page_and_ack_cannot_prove_terminal() -> None:
    child = _binding("1000006", "KRX", 1)
    ack = _evidence(child, "kt00007", filled=0, canceled=1, remaining=0, state="ACK", hash_char="3")
    ack = replace(ack, cancel_order_no="2000006")
    intent = _intent("KRX", 1, (replace(child, cancel_order_no="2000006"),))
    result = reconcile_aftermarket_boundary(
        intent,
        [ack],
        [],
        current_snapshot_complete=False,
    )

    assert result.state is ReconciliationState.UNKNOWN
    assert result.terminal is False
    assert "current_snapshot_incomplete" in result.reasons
    assert "dated_receipt_not_terminal" in result.reasons


def test_restart_requires_exact_durable_intent_hash() -> None:
    child = _binding("1000007", "NXT", 2)
    dated = _evidence(child, "kt00007", filled=1, canceled=0, remaining=1, state="OPEN", hash_char="4")
    current = _evidence(child, "ka10075", filled=1, canceled=0, remaining=1, state="OPEN", hash_char="5")
    intent = _intent("NXT", 2, (child,))

    blocked = reconcile_aftermarket_boundary(
        intent,
        [dated],
        [current],
        current_snapshot_complete=True,
        restart=True,
        restart_intent_sha256="9" * 64,
    )
    recovered = reconcile_aftermarket_boundary(
        intent,
        [dated],
        [current],
        current_snapshot_complete=True,
        restart=True,
        restart_intent_sha256=INTENT_HASH,
    )

    assert blocked.state is ReconciliationState.UNKNOWN
    assert "restart_durable_intent_mismatch" in blocked.reasons
    assert recovered.state is ReconciliationState.OPEN


def test_cancel_and_route_identity_must_match_explicit_binding() -> None:
    child = _binding("1000008", "KRX", 3, cancel_order_no="2000008")
    wrong = _evidence(child, "kt00007", filled=0, canceled=3, remaining=0, state="TERMINAL", hash_char="6")
    wrong = replace(
        wrong,
        account_key="account-b",
        route="NXT",
        cancel_order_no="2000999",
    )
    result = reconcile_aftermarket_boundary(
        _intent("KRX", 3, (child,)),
        [wrong],
        [],
        current_snapshot_complete=True,
    )

    assert result.state is ReconciliationState.UNKNOWN
    assert "account_key_mismatch" in result.reasons
    assert "route_mismatch" in result.reasons
    assert "cancel_order_no_mismatch" in result.reasons
