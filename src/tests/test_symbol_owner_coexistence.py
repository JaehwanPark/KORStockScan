from src.engine import kiwoom_orders
from datetime import date, datetime, timedelta
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


@pytest.mark.parametrize('fault', [None, 'unbound', 'other_target', 'quantity', 'other_action', 'cycle', 'date', 'blank_ambiguous'])
@pytest.mark.parametrize('operation', ['ENTRY_RESIDUAL_BUY', 'ENTRY_BUY'])
def test_registered_entry_fill_reaches_native_ledger_before_rest_staging(tmp_path, monkeypatch, fault, operation, native=False):
    from types import SimpleNamespace
    from src.engine import sniper_execution_receipts as receipts
    day = datetime.now(receipts._KST).date()
    registry = OrderOwnerRegistry(tmp_path/'registry.jsonl')
    target = '102' if fault == 'other_target' else '101'
    action = 'AVG_DOWN' if fault == 'other_action' else operation
    owner = OwnerOrderContext('main_scalping', 'main_scalping:'+target, 'main_scalping:'+target,
        f'main_scalping:{target}:{target}:{action}:entry_split_probe_residual_1:unique')
    if operation == 'ENTRY_BUY':
        from src.trading.order.owner_custody_registry import main_owner_context
        owner = main_owner_context({'id':target, 'position_cycle_id':'prior-cycle' if fault=='cycle' else target},
            action=action, ordinal='entry_split_probe_0:1')
    elif fault == 'cycle':
        owner = OwnerOrderContext('main_scalping','main_scalping:'+target,'main_scalping:'+target,
            f'main_scalping:{target}:prior-cycle:{action}:entry_split_probe_residual_1:unique')
    order_day = day - timedelta(days=1) if fault == 'date' else day
    if fault != 'unbound':
        intent = registry.reserve(context=owner, symbol=SYMBOL, side='BUY', quantity=1,
                                  route='SOR', order_date=order_day)
        registry.transition(intent,state='ORDER_BOUND',broker_order_no='0023803')
    stock = dict(id=101, name='fixture', code=SYMBOL, status='BUY_ORDERED', strategy='SCALPING',
        buy_qty=1, buy_price=10000, entry_filled_qty=1, entry_requested_qty=3,
        entry_split_probe_phase='residual_submitting', entry_split_probe_bundle_id='bundle-101',
        odno='0023795', pending_entry_orders=[dict(ord_no='0023795',qty=1,filled_qty=1,status='FILLED')])
    if operation == 'ENTRY_BUY':
        stock.update(status='WATCHING', buy_qty=0, buy_price=0, entry_filled_qty=0, entry_requested_qty=2,
            odno='', pending_entry_orders=[])
        stock.pop('entry_split_probe_bundle_id');stock.pop('entry_split_probe_phase')
    if fault == 'blank_ambiguous':
        stock['pending_entry_orders'] = [dict(ord_no='',qty=1,tag='unidentified') for _ in range(2)]
    monkeypatch.setattr(receipts, 'ACTIVE_TARGETS', [stock])
    monkeypatch.setattr(receipts, '_get_fast_state', lambda _:None)
    monkeypatch.setattr(receipts, 'resolve_symbol_owner_policy', lambda *a, **k:SimpleNamespace(coexistence_enabled=False))
    monkeypatch.setattr(receipts, 'default_order_owner_registry', lambda:registry)
    monkeypatch.setattr(receipts, 'log_info', lambda *a:None)
    monkeypatch.setattr(receipts, 'log_error', lambda *a:None)
    observed=[]
    native_consume = receipts._handle_entry_buy_execution
    if native:
        from src.tests.test_sniper_scale_in import _DummyDB
        class NoThread:
            def __init__(self, *a, **k): pass
            def start(self): pass
        monkeypatch.setattr(receipts, 'DB', _DummyDB())
        monkeypatch.setattr(receipts, 'highest_prices', {})
        monkeypatch.setattr(receipts, 'threading', SimpleNamespace(
            Thread=NoThread, get_ident=receipts.threading.get_ident))
        monkeypatch.setattr(receipts, 'event_bus', SimpleNamespace(publish=lambda *a: None))
        monkeypatch.setattr(receipts.kiwoom_utils, 'get_target_price_up', lambda *a: 10350)
    def consume(**kwargs):
        if native:
            return native_consume(**kwargs)
        observed.append(receipts._resolve_entry_effective_fill_qty(**{
            k:v for k,v in kwargs.items() if k not in {'target_id','now'}}))
    monkeypatch.setattr(receipts, '_handle_entry_buy_execution', consume)
    event=dict(code=SYMBOL, type='BUY', order_no='0023803',price=10000,qty=1,
        order_qty=2 if fault=='quantity' else 1,remaining_qty=0,cumulative_exec_amount=10000,
        execution_no='8752',unit_exec_price=10000,unit_exec_qty=1)
    receipts.handle_real_execution(event)
    if native:
        from src.engine import sniper_state_handlers as handlers
        assert stock['buy_qty'] == 1 and stock['buy_price'] == 10000
        assert stock['entry_filled_qty'] == 1 and stock['pending_entry_orders'][0]['status'] == 'FILLED'
        assert stock['pending_entry_orders'][0]['tag'] == 'entry_split_probe_0'
        receipts.handle_real_execution(event)
        assert stock['buy_qty'] == 1
        # Late REST staging must preserve the already consumed WS fill and
        # must leave no open leg for the cancellation loop to retry.
        handlers._stage_buy_order_submission(stock, SYMBOL, 10000, 2, 'fixture',
            [dict(ord_no='0023803', qty=1, filled_qty=0, status='OPEN', tag='entry_split_probe_0')])
        assert handlers._open_entry_split_orders(stock) == []
        assert handlers._resolve_post_submit_db_state(stock, curr_price=10000, requested_qty=2)[:3] == (
            'HOLDING', 1, 10000)
        return
    if fault is None:
        assert observed[0]['status']=='final', observed
        assert stock['_entry_receipt_filled_by_order_no']['0023803']==1
        receipts.handle_real_execution(event)
        assert observed[-1]['status']=='duplicate'
    else:
        assert not observed or observed[0]['status']=='invalid'
        assert stock.get('_entry_receipt_filled_by_order_no',{}).get('0023803',0)==0


@pytest.mark.parametrize('number', ['', '-', 'abc', '123', '0000000'])
def test_empty_or_invalid_cancel_ack_number_is_false_without_exception(number):
    from src.engine import sniper_execution_receipts as receipts
    assert receipts.pending_sell_cancel_ack_exact(dict(id=101,code=SYMBOL),
        code=SYMBOL,order_no=number) is False


@pytest.mark.parametrize('fault', [None, 'missing', 'amount', 'open', 'sell', 'owner', 'date',
    'bundle', 'extra_order', 'manual', 'foreign_guard', 'sell_custody', 'db_price', 'db_retry',
    'db_already', 'db_already_unbound', 'prior_receipt', 'receipt_conflict', 'receipt_time', 'receipt_price', 'receipt_write'])
def test_sync_recovers_only_complete_exact_unit_entry_census(tmp_path, monkeypatch, fault):
    from types import SimpleNamespace
    from copy import deepcopy
    from src.engine import sniper_sync as sync, sniper_execution_receipts as receipts
    from src.engine.scalping import entry_split_order_plan as probe
    from src.engine.ai import holding_exit_vote as vote
    today = datetime.now(receipts._KST)
    rows=[dict(owner_type='main_scalping',owner_id='main_scalping:101',position_id='main_scalping:101',
        symbol=SYMBOL,order_date=today.date().isoformat(),side='BUY',action='NEW',state='ORDER_TERMINAL',
        quantity=1,filled_qty=1,fill_amount=10000 if i<2 else 9900,execution_no=str(8000+i),
        fill_observed_at_kst=(today+timedelta(seconds=i)).isoformat(),
        broker_order_no=str(23795+i).zfill(7),event_hash=str(i+1)*64,
        client_intent_id=f'main_scalping:101:101:{"ENTRY_BUY" if i==0 else "ENTRY_RESIDUAL_BUY"}:leg{i}:unique') for i in range(3)]
    order_nos=[r['broker_order_no'] for r in rows]
    bundle=dict(bundle_id='bundle-101',code=SYMBOL,target_id=101,phase='residual_submitted',requested_qty=3,
        order_no=order_nos[0],residual_order_nos=order_nos[1:])
    record=SimpleNamespace(id=101,stock_name='fixture',strategy='SCALPING',status='SELL_ORDERED',
        buy_qty=1,buy_price=10000,buy_time=today,sell_price=0,sell_time=None,scale_in_locked=True)
    target=dict(id=101,code=SYMBOL,status='SELL_ORDERED',buy_qty=2,buy_price=10000,
        broker_symbol_allocation_conflict=True,sell_cancel_reconciliation_required=True,
        sell_cancel_reconciliation_source='missing_original_order_no:pending_context_absent',
        pending_entry_orders=[dict(ord_no=n,qty=1) for n in order_nos])
    if fault=='missing':rows.pop()
    elif fault=='amount':rows[1]['fill_amount']=0
    elif fault=='open':rows[1]['state']='ORDER_BOUND'
    elif fault=='sell':rows[1]['side']='SELL'
    elif fault=='owner':rows[1]['owner_id']='manual_operator:other'
    elif fault=='date':rows[1]['order_date']='2026-10-01'
    elif fault=='bundle':bundle['residual_order_nos']=['7654321',order_nos[2]]
    elif fault=='extra_order':target['pending_entry_orders'].append(dict(ord_no='7654321'))
    elif fault=='foreign_guard':target['sell_cancel_reconciliation_source']='unproved_foreign_cancellation'
    elif fault=='db_price':record.buy_price=9999
    monkeypatch.setattr(probe,'PROBE_RUNTIME_STATE_PATH',tmp_path/'probe.json')
    monkeypatch.setattr(receipts,'_sell_pending_submit_path',lambda _:tmp_path/'sell.json')
    monkeypatch.setattr(receipts,'_sell_receipt_recovery_path',lambda _:tmp_path/'sell-receipt.json')
    if fault=='sell_custody':(tmp_path/'sell.json').write_text('{}')
    monkeypatch.setattr(sync,'evaluate_main_bot_control_exclusion',lambda _:SimpleNamespace(excluded=fault=='manual'))
    monkeypatch.setattr(sync,'ACTIVE_TARGETS',[target])
    monkeypatch.setattr(sync,'resolve_symbol_owner_policy',lambda _:SimpleNamespace(coexistence_enabled=True,
        policy_id='main-native',policy_hash='a'*64))
    registry=SimpleNamespace(symbol_registered=lambda _:True,decision_activation_matches=lambda _:True,position_intents=lambda **_:deepcopy(rows),
        reconcile_symbol_quantity=lambda **_:dict(position_quantities={'main_scalping:101':3},external_manual_remainder=2))
    monkeypatch.setattr(sync,'default_order_owner_registry',lambda:registry)
    monkeypatch.setattr(sync,'log_error',lambda *a:None);monkeypatch.setattr(sync,'log_info',lambda *a:None)
    probe.update_probe_runtime_bundle('bundle-101',phase=bundle['phase'],now=today,
        **{k:v for k,v in bundle.items() if k not in {'bundle_id','phase'}})
    monkeypatch.setattr(receipts,'DATA_DIR',tmp_path/'data')
    if fault in {'db_already','db_already_unbound'}:
        record.buy_qty=3;record.buy_price=29900/3;record.status='HOLDING'
        target['buy_fill_identity_store_gap']='position_generation_mismatch'
        proof=dict(bundle_id='bundle-101',quantity=3,fill_amount=29900,
            registry_event_hashes={r['broker_order_no']:r['event_hash'] for r in rows})
        probe.update_probe_runtime_bundle('bundle-101',phase='complete',now=today,
            registered_entry_recovery=proof if fault=='db_already' else {})
    if fault in {'prior_receipt','receipt_conflict','receipt_time','receipt_price','db_already'}:
        first,last=rows[0],rows[-1]
        orders=[first['broker_order_no'],last['broker_order_no']]
        prior=dict(id=101,code=SYMBOL,buy_qty=2,buy_price=9950,
            buy_time=today+timedelta(seconds=2),entry_filled_qty=2,
            _entry_receipt_filled_by_order_no={n:1 for n in orders},
            _entry_receipt_executions_by_order_no={r['broker_order_no']:{
                ('99999' if fault=='receipt_conflict' else r['execution_no']):dict(cumulative_qty=1)} for r in [first,last]})
        if fault=='receipt_time':prior['buy_time']=today-timedelta(days=1)
        if fault=='receipt_price':prior['buy_price']=9990
        vote.persist_buy_fill_receipt(prior,receipts.DATA_DIR)
    if fault=='receipt_write':
        monkeypatch.setattr(vote,'persist_buy_fill_receipt',lambda *a,**k: (_ for _ in ()).throw(OSError('fixture')))
    before=probe.PROBE_RUNTIME_STATE_PATH.read_bytes()
    assert sync._preserve_coexistence_owner_inventory(record=record,code=SYMBOL,
        real_codes={SYMBOL:dict(qty=5)},source='periodic_account_sync')
    if fault in {None,'db_retry','prior_receipt','db_already'}:
        assert record.buy_qty==3 and record.buy_price==pytest.approx(29900/3) and record.status=='HOLDING'
        restored=dict(id=101,code=SYMBOL,buy_qty=record.buy_qty,buy_price=record.buy_price,buy_time=record.buy_time)
        assert vote.restore_buy_fill_receipt(restored,receipts.DATA_DIR)=='restored'
        assert len(vote.buy_fill_legs_from_runtime(restored))==3
        if fault=='db_already':
            from src.engine import kiwoom_sniper_v2 as main
            restored.update(strategy='SCALPING',status='HOLDING',name='fixture',position_tag='SCALP_BASE')
            monkeypatch.setattr(main,'DATA_DIR',receipts.DATA_DIR)
            monkeypatch.setattr(main,'highest_prices',{})
            monkeypatch.setattr(main.POSITION_PEAK_LEDGER,'restore_peak',lambda stock:(0,'missing'))
            main._restore_holding_runtime_state([restored])
            assert restored['buy_fill_identity_restore_status']=='restored'
            assert 'buy_fill_identity_store_gap' not in restored
        assert target['buy_qty']==3 and target['status']=='HOLDING'
        assert not target.get('sell_cancel_reconciliation_required')
        assert not target.get('broker_symbol_allocation_conflict')
        assert target['scale_in_locked'] if 'scale_in_locked' in target else record.scale_in_locked
        if fault=='db_retry':
            record.buy_qty=1;record.buy_price=10000;record.status='SELL_ORDERED'
            assert sync._restore_registered_entry_buy(record,None,SYMBOL,3,registry)
            assert record.buy_qty==3
    else:
        assert record.buy_qty==(3 if fault=='db_already_unbound' else 1)
        assert record.status==('HOLDING' if fault=='db_already_unbound' else 'SELL_ORDERED')
        assert probe.PROBE_RUNTIME_STATE_PATH.read_bytes()==before
        assert target['broker_symbol_allocation_conflict'] is True


def test_allocation_gap_never_becomes_phantom_sell_cancel(monkeypatch):
    from copy import deepcopy
    from src.engine import sniper_state_handlers as handlers
    stock=dict(id=101,code=SYMBOL,status='HOLDING',buy_qty=1,
        broker_symbol_allocation_conflict=True,sell_cancel_reconciliation_required=True,
        sell_cancel_reconciliation_source='main_owner_registry_quantity_mismatch:registry=2:db=1')
    before=deepcopy(stock)
    monkeypatch.setattr(handlers,'_broker_position_qty_for_sell_reconciliation',
        lambda *a:pytest.fail('allocation conflict must not initiate cancel reconciliation'))
    assert handlers._sell_cancel_reconciliation_blocks_holding(stock,SYMBOL,now_ts=1000) is True
    assert stock==before



def test_initial_registry_receipt_survives_native_consumer_and_late_rest_staging(tmp_path, monkeypatch):
    test_registered_entry_fill_reaches_native_ledger_before_rest_staging(
        tmp_path, monkeypatch, None, 'ENTRY_BUY', native=True)


@pytest.mark.parametrize('fault', [None, 'open', 'owner', 'date', 'extra', 'amount',
    'account', 'source', 'parent', 'bundle', 'residual', 'manual', 'price', 'sell'])
def test_sync_consumes_terminal_initial_probe_without_submitting_residual(tmp_path, monkeypatch, fault):
    from types import SimpleNamespace
    from copy import deepcopy
    from src.engine import sniper_sync as sync, sniper_execution_receipts as receipts
    from src.engine.scalping import entry_split_order_plan as probe
    from src.engine.scalping.strategy_owner_components import digest
    from src.engine.ai import holding_exit_vote as vote
    now = datetime.now(receipts._KST)
    row = dict(owner_type='main_scalping', owner_id='main_scalping:101', position_id='main_scalping:101',
        symbol=SYMBOL, order_date=now.date().isoformat(), side='BUY', action='NEW', state='ORDER_TERMINAL',
        quantity=1, filled_qty=1, fill_amount=10000, execution_no='12544', broker_order_no='0013982',
        event_hash='a'*64, account_key='fixture', route='SOR', fill_observed_at_kst=now.isoformat(),
        client_intent_id='main_scalping:101:101:ENTRY_BUY:entry_split_probe_0:1:nonce')
    source=dict(schema='entry_probe_submit_source_v1', source_date=now.date().isoformat(),
        owner_id='main_scalping:101', record_id='101', position_cycle_id='101', stock_code=SYMBOL,
        bundle_id='probe-101', planned_qty=2, initial_parent_id='parent', account_key='fixture')
    if fault=='parent':source['initial_parent_id']=''
    source['sha256']=digest(source)
    if fault=='source':source['sha256']='b'*64
    bundle=dict(target_id=101, code=SYMBOL, requested_qty=2, order_no='0013982',
        actual_submitted_qty=1, broker_route='SOR', continuation=dict(requested_qty=2,residual_qty=1),
        entry_split_probe_submit_source=source)
    rows=[row]
    if fault=='open':row['state']='ORDER_BOUND'
    if fault=='owner':row['owner_id']='manual_operator:other'
    if fault=='date':row['order_date']='2026-10-01'
    if fault=='extra':rows.append({**row,'broker_order_no':'0013983'})
    if fault=='amount':row['fill_amount']=0
    if fault=='account':row['account_key']='other'
    if fault=='bundle':bundle['order_no']='0013983'
    if fault=='residual':bundle['residual_order_nos']=['0013983']
    monkeypatch.setattr(probe,'PROBE_RUNTIME_STATE_PATH',tmp_path/'probe.json')
    probe.update_probe_runtime_bundle('probe-101',phase='probe_submitted',now=now,**bundle)
    monkeypatch.setattr(receipts,'DATA_DIR',tmp_path/'data')
    monkeypatch.setattr(receipts,'_sell_pending_submit_path',lambda _:tmp_path/'sell.json')
    monkeypatch.setattr(receipts,'_sell_receipt_recovery_path',lambda _:tmp_path/'sell-receipt.json')
    if fault=='sell':(tmp_path/'sell.json').write_text('{}')
    monkeypatch.setattr(sync,'evaluate_main_bot_control_exclusion',lambda _:SimpleNamespace(excluded=fault=='manual'))
    monkeypatch.setattr(sync,'log_error',lambda *a:None)
    record=SimpleNamespace(id=101,strategy='SCALPING',status='BUY_ORDERED',buy_qty=2,
        buy_price=-1 if fault=='price' else 9900,buy_time=None,sell_time=None,sell_price=0)
    target=dict(id=101,code=SYMBOL,status='BUY_ORDERED',pending_entry_orders=[dict(ord_no='0013982')])
    registry=SimpleNamespace(position_intents=lambda **_:deepcopy(rows))
    before=probe.PROBE_RUNTIME_STATE_PATH.read_bytes()
    result=sync._restore_registered_entry_buy(record,target,SYMBOL,1,registry)
    if fault is not None:
        assert result is None and record.buy_qty==2 and record.status=='BUY_ORDERED'
        assert probe.PROBE_RUNTIME_STATE_PATH.read_bytes()==before
        return
    assert result['quantity']==1 and record.buy_qty==1 and record.status=='HOLDING'
    assert record.buy_time==now.replace(tzinfo=None) and record.buy_price==10000
    restored=dict(id=101,code=SYMBOL,buy_qty=1,buy_price=10000,buy_time=record.buy_time)
    assert vote.restore_buy_fill_receipt(restored,receipts.DATA_DIR)=='restored'
    assert len(vote.buy_fill_legs_from_runtime(restored))==1
    state=probe._load_probe_runtime_state(now.date().isoformat())['bundles']['probe-101']
    assert state['phase']=='aborted' and state['terminal_outcome']=='residual_not_submitted'
    assert state['requested_qty']==2 and state['actual_submitted_qty']==1
    assert target['entry_split_probe_residual_expand_forbidden'] is True
    assert 'pending_entry_orders' not in target
    assert sync._restore_registered_entry_buy(record,None,SYMBOL,1,registry)==result
