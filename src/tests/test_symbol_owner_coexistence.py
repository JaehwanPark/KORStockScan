from src.engine import kiwoom_orders
from datetime import date, datetime
import json
import pytest
from src.trading.order.owner_custody_registry import (OrderOwnerRegistry, OwnerOrderContext, OwnerRegistryBusy, OwnerRegistryConflict, OwnerRegistryError)
TARGET_DATE = date(2026, 9, 3)
SYMBOL = "005930"
@pytest.fixture(autouse=True)
def _explicit_owner_account(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE",
        str(tmp_path / "excluded.txt"),
    )
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "test-account")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH",
        str(tmp_path / "registry.jsonl"),
    )


def _context(owner_type: str, suffix: str) -> OwnerOrderContext:
    owner_id = f"{owner_type}:{suffix}"
    return OwnerOrderContext(
        owner_type=owner_type,
        owner_id=owner_id,
        position_id=(
            owner_id if owner_type == "main_scalping" else f"{owner_id}:position"
        ),
        client_intent_id=f"{owner_type}:{suffix}:intent",
    )


def test_registry_rejects_malformed_symbol_and_order_date(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = _context("main_scalping", "strict-input")

    with pytest.raises(OwnerRegistryError, match="symbol_invalid"):
        registry.reserve(
            context=context,
            symbol="1234567",
            side="BUY",
            quantity=1,
            route="KRX",
            order_date=TARGET_DATE,
        )
    with pytest.raises(OwnerRegistryError, match="order_date_invalid"):
        registry.reserve(
            context=context,
            symbol=SYMBOL,
            side="BUY",
            quantity=1,
            route="KRX",
            order_date="2026-09-03T09:00:00+09:00",
        )


def test_registry_rejects_incoherent_main_owner_position_identity(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")

    with pytest.raises(
        OwnerRegistryError, match="main_owner_position_identity_invalid"
    ):
        registry.reserve(
            context=OwnerOrderContext(
                owner_type="main_scalping",
                owner_id="main_scalping:101",
                position_id="main_scalping:202",
                client_intent_id="main-owner-mismatch",
            ),
            symbol=SYMBOL,
            side="BUY",
            quantity=1,
            route="KRX",
            order_date=TARGET_DATE,
        )


def test_registry_serializes_unbound_lane_and_forbids_cross_owner_cancel(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "101")
    widget = _context("manual_operator", "005930")
    main_intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=10,
        route="SOR",
        order_date=TARGET_DATE,
    )
    with pytest.raises(OwnerRegistryBusy):
        registry.reserve(
            context=widget,
            symbol=SYMBOL,
            side="BUY",
            quantity=10,
            route="KRX",
            order_date=TARGET_DATE,
        )

    registry.transition(main_intent, state="ORDER_BOUND", broker_order_no="1234567")
    widget_intent = registry.reserve(
        context=widget,
        symbol=SYMBOL,
        side="BUY",
        quantity=10,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(widget_intent, state="ORDER_BOUND", broker_order_no="1234568")

    with pytest.raises(OwnerRegistryConflict, match="cross_owner"):
        registry.reserve(
            context=OwnerOrderContext(
                owner_type=widget.owner_type,
                owner_id=widget.owner_id,
                position_id=widget.position_id,
                client_intent_id="widget:cancel:foreign",
            ),
            symbol=SYMBOL,
            side="BUY",
            quantity=0,
            route="SOR",
            order_date=TARGET_DATE,
            action="CANCEL",
            original_order_no="1234567",
        )


def test_registry_reconciles_owner_quantities_and_external_remainder(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "201")
    episode = _context("manual_operator", "morning")
    for context, order_no, qty in (
        (main, "2234567", 12),
        (episode, "2234568", 20),
    ):
        intent = registry.reserve(
            context=context,
            symbol=SYMBOL,
            side="BUY",
            quantity=qty,
            route="SOR",
            order_date=TARGET_DATE,
        )
        registry.transition(intent, state="ORDER_BOUND", broker_order_no=order_no)
        registry.record_fill(
            context=context,
            symbol=SYMBOL,
            side="BUY",
            order_quantity=qty,
            order_date=TARGET_DATE,
            broker_order_no=order_no,
            cumulative_filled_qty=qty,
            cumulative_fill_amount=qty * 70_000,
        )

    result = registry.reconcile_symbol_quantity(symbol=SYMBOL, broker_quantity=37)
    assert result["registered_owner_quantity"] == 32
    assert result["external_manual_remainder"] == 5
    assert result["position_quantities"][main.position_id] == 12
    assert result["position_quantities"][episode.position_id] == 20
    with pytest.raises(OwnerRegistryConflict, match="broker_quantity_deficit"):
        registry.reconcile_symbol_quantity(symbol=SYMBOL, broker_quantity=31)


def test_registry_position_and_symbol_reconciliation_are_account_scoped(
    tmp_path, monkeypatch
):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    shared_position = "episode:shared-position"

    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "account-a")
    registry.register_migrated_position(
        context=OwnerOrderContext(
            owner_type="manual_operator",
            owner_id="episode:shared",
            position_id=shared_position,
            client_intent_id="account-a:migration",
        ),
        symbol=SYMBOL,
        quantity=10,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="1234501",
        evidence_sha256="a" * 64,
    )
    registry.register_migrated_position(
        context=OwnerOrderContext(
            owner_type="manual_operator",
            owner_id="episode:shared",
            position_id=shared_position,
            client_intent_id="account-a:other-symbol-migration",
        ),
        symbol="000660",
        quantity=100,
        average_price=200_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="1234503",
        evidence_sha256="c" * 64,
    )

    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "account-b")
    registry.register_migrated_position(
        context=OwnerOrderContext(
            owner_type="manual_operator",
            owner_id="episode:shared",
            position_id=shared_position,
            client_intent_id="account-b:migration",
        ),
        symbol=SYMBOL,
        quantity=20,
        average_price=70_000,
        route="NXT",
        order_date=TARGET_DATE,
        broker_order_no="1234502",
        evidence_sha256="b" * 64,
    )

    assert registry.owner_position_qty(shared_position, symbol=SYMBOL) == 20
    assert (
        registry.reconcile_symbol_quantity(symbol=SYMBOL, broker_quantity=20)[
            "registered_owner_quantity"
        ]
        == 20
    )

    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "account-a")
    assert registry.owner_position_qty(shared_position, symbol=SYMBOL) == 10
    assert (
        registry.reconcile_symbol_quantity(symbol=SYMBOL, broker_quantity=10)[
            "registered_owner_quantity"
        ]
        == 10
    )
    with pytest.raises(OwnerRegistryConflict, match="sell_quantity_exceeds"):
        registry.reserve(
            context=OwnerOrderContext(
                owner_type="manual_operator",
                owner_id="episode:shared",
                position_id=shared_position,
                client_intent_id="account-a:sell-too-many",
            ),
            symbol=SYMBOL,
            side="SELL",
            quantity=15,
            route="SOR",
            order_date=TARGET_DATE,
        )


def test_registry_migrates_existing_position_with_evidence_and_preserves_owner_qty(
    tmp_path, monkeypatch
):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    episode = _context("manual_operator", "legacy-morning")
    registry.register_migrated_position(
        context=episode,
        symbol=SYMBOL,
        quantity=20,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="2734567",
        evidence_sha256="a" * 64,
    )

    assert registry.owner_position_qty(episode.position_id, symbol=SYMBOL) == 20
    monkeypatch.setattr(
        registry,
        "reconcile_symbol_quantity",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("migration receipt must use one locked state snapshot")
        ),
    )
    receipt = registry.migration_receipt(
        symbol=SYMBOL,
        broker_quantity=25,
        active_date=TARGET_DATE,
        verified_exchanges={"KRX", "NXT"},
        broker_open_order_nos=(),
        broker_snapshot_sha256="e" * 64,
    )
    assert receipt["registered_owner_quantity"] == 20
    assert receipt["external_manual_remainder"] == 5
    assert receipt["broker_account_key"] == "test-account"


def test_registry_rejects_duplicate_cancel_for_same_exact_order(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "cancel-owner")
    buy_intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=10,
        route="SOR",
        order_date=TARGET_DATE,
    )
    registry.transition(buy_intent, state="ORDER_BOUND", broker_order_no="2834567")
    first_cancel = OwnerOrderContext(
        owner_type=main.owner_type,
        owner_id=main.owner_id,
        position_id=main.position_id,
        client_intent_id="cancel-owner:first",
    )
    cancel_intent = registry.reserve(
        context=first_cancel,
        symbol=SYMBOL,
        side="BUY",
        quantity=0,
        route="SOR",
        order_date=TARGET_DATE,
        action="CANCEL",
        original_order_no="2834567",
    )
    registry.transition(cancel_intent, state="ORDER_BOUND", broker_order_no="2834568")
    with pytest.raises(OwnerRegistryConflict, match="cancel_already"):
        registry.reserve(
            context=OwnerOrderContext(
                owner_type=main.owner_type,
                owner_id=main.owner_id,
                position_id=main.position_id,
                client_intent_id="cancel-owner:second",
            ),
            symbol=SYMBOL,
            side="BUY",
            quantity=0,
            route="SOR",
            order_date=TARGET_DATE,
            action="CANCEL",
            original_order_no="2834567",
        )


def test_registry_binds_fill_before_submit_response_by_unique_pending_intent(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "301")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=7,
        route="KRX",
        order_date=TARGET_DATE,
    )
    bound = registry.bind_unique_pending_receipt(
        symbol=SYMBOL,
        side="BUY",
        order_date=TARGET_DATE,
        broker_order_no="3234567",
        broker_order_qty=7,
    )
    assert bound is not None
    assert bound["intent_id"] == intent
    assert bound["owner_id"] == main.owner_id
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3234567")


def test_registry_binds_late_receipt_to_unique_ambiguous_intent(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "late-receipt")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=7,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="INTENT_AMBIGUOUS", reason="timeout")

    bound = registry.bind_unique_pending_receipt(
        symbol=SYMBOL,
        side="BUY",
        order_date=TARGET_DATE,
        broker_order_no="3334567",
        broker_order_qty=7,
    )

    assert bound is not None
    assert bound["intent_id"] == intent
    assert bound["owner_id"] == main.owner_id


def test_late_submit_response_does_not_downgrade_terminal_receipt_state(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "receipt-first")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=1,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3384567")
    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=1,
        order_date=TARGET_DATE,
        broker_order_no="3384567",
        cumulative_filled_qty=1,
        cumulative_fill_amount=70_000,
    )
    registry.transition(
        intent,
        state="ORDER_TERMINAL",
        broker_order_no="3384567",
        reason="receipt_terminal",
    )

    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3384567")

    row = registry.order_owner(order_date=TARGET_DATE, broker_order_no="3384567")
    assert row is not None
    assert row["state"] == "ORDER_TERMINAL"


def test_late_reject_after_terminal_receipt_requires_reconciliation(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "receipt-before-reject")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=1,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3394567")
    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=1,
        order_date=TARGET_DATE,
        broker_order_no="3394567",
        cumulative_filled_qty=1,
        cumulative_fill_amount=70_000,
    )
    registry.transition(
        intent,
        state="ORDER_TERMINAL",
        broker_order_no="3394567",
        reason="receipt_terminal",
    )

    with pytest.raises(OwnerRegistryConflict, match="terminal_transition"):
        registry.transition(intent, state="INTENT_REJECTED", reason="late_reject")

    row = registry.order_owner(order_date=TARGET_DATE, broker_order_no="3394567")
    assert row is not None
    assert row["state"] == "ORDER_TERMINAL"


def test_terminal_fill_economics_update_does_not_reopen_order(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "terminal-economics")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=2,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3404567")
    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=2,
        order_date=TARGET_DATE,
        broker_order_no="3404567",
        cumulative_filled_qty=2,
        cumulative_fill_amount=140_000,
    )
    registry.transition(
        intent,
        state="ORDER_TERMINAL",
        broker_order_no="3404567",
        reason="receipt_terminal",
    )

    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=2,
        order_date=TARGET_DATE,
        broker_order_no="3404567",
        cumulative_filled_qty=2,
        cumulative_fill_amount=140_100,
        execution_no="late-economic-correction",
    )

    row = registry.order_owner(order_date=TARGET_DATE, broker_order_no="3404567")
    assert row is not None
    assert row["state"] == "ORDER_TERMINAL"
    assert row["fill_amount"] == 140_100


@pytest.mark.parametrize(
    ("symbol", "side", "order_quantity"),
    [
        ("000660", "BUY", 2),
        (SYMBOL, "SELL", 2),
        (SYMBOL, "BUY", 3),
    ],
)
def test_registry_rejects_fill_receipt_order_identity_conflict(
    tmp_path, symbol, side, order_quantity
):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "fill-identity")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=2,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3414567")

    with pytest.raises(OwnerRegistryConflict, match="fill_order_identity_conflict"):
        registry.record_fill(
            context=main,
            symbol=symbol,
            side=side,
            order_quantity=order_quantity,
            order_date=TARGET_DATE,
            broker_order_no="3414567",
            cumulative_filled_qty=1,
            cumulative_fill_amount=70_000,
        )


def test_terminal_fill_update_cannot_reopen_registry_order(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "terminal-fill")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=2,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3234567")
    registry.transition(intent, state="ORDER_TERMINAL", broker_order_no="3234567")

    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=2,
        order_date=TARGET_DATE,
        broker_order_no="3234567",
        cumulative_filled_qty=1,
        cumulative_fill_amount=70_000,
    )

    row = registry.order_owner(order_date=TARGET_DATE, broker_order_no="3234567")
    assert row is not None
    assert row["state"] == "ORDER_TERMINAL"


def test_registry_partial_fills_use_monotonic_cumulative_quantity(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "partial-fill")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=10,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3534567")

    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=10,
        order_date=TARGET_DATE,
        broker_order_no="3534567",
        cumulative_filled_qty=3,
        cumulative_fill_amount=210_000,
    )
    registry.record_fill(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        order_quantity=10,
        order_date=TARGET_DATE,
        broker_order_no="3534567",
        cumulative_filled_qty=5,
        cumulative_fill_amount=None,
    )

    row = registry.order_owner(order_date=TARGET_DATE, broker_order_no="3534567")
    assert row is not None
    assert row["filled_qty"] == 5
    assert row["fill_amount"] == 210_000


def test_bound_registry_order_cannot_be_downgraded_to_ambiguous(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "bound-no-downgrade")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=1,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3334567")

    with pytest.raises(OwnerRegistryConflict, match="state_transition_forbidden"):
        registry.transition(intent, state="INTENT_AMBIGUOUS")


def test_registry_owner_check_includes_owner_type(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "type-guard")
    intent = registry.reserve(
        context=main,
        symbol=SYMBOL,
        side="BUY",
        quantity=1,
        route="KRX",
        order_date=TARGET_DATE,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="3434567")
    forged = OwnerOrderContext(
        owner_type="manual_operator",
        owner_id=main.owner_id,
        position_id=main.position_id,
        client_intent_id="episode:forged",
    )

    with pytest.raises(OwnerRegistryConflict, match="cross_owner"):
        registry.assert_owner(
            context=forged,
            order_date=TARGET_DATE,
            broker_order_no="3434567",
        )


def test_registry_finalize_failure_preserves_broker_attempt_and_order_number():
    class BrokenRegistry:
        def transition(self, *args, **kwargs):
            raise OwnerRegistryConflict("journal write failed")

    result = kiwoom_orders._finish_owner_registry_intent(
        BrokenRegistry(),
        "intent-1",
        response={"return_code": "0", "ord_no": "6234567"},
    )

    assert result["return_code"] == "OWNER_REGISTRY_BLOCKED"
    assert result["broker_order_attempted"] is True
    assert result["ord_no"] == "6234567"
    assert result["owner_registry_ambiguous"] is True
    assert result["owner_registry_intent_id"] == "intent-1"


def test_registry_event_binds_exact_policy_provenance(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = _context("main_scalping", "policy-provenance")
    intent = registry.reserve(
        context=context,
        symbol=SYMBOL,
        side="BUY",
        quantity=1,
        route="SOR",
        order_date=TARGET_DATE,
        authority_policy_id="same-symbol-policy",
        authority_policy_hash="f" * 64,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="9234567")

    owner = registry.order_owner(order_date=TARGET_DATE, broker_order_no="9234567")
    assert owner is not None
    assert owner["authority_policy_id"] == "same-symbol-policy"
    assert owner["authority_policy_hash"] == "f" * 64
