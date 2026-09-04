from __future__ import annotations

import json
from datetime import date, datetime

import pytest

from src.engine import kiwoom_orders
from src.engine import sniper_execution_receipts
from src.engine import sniper_state_handlers
from src.engine import sniper_sync
from src.engine.risk import manual_control_exclusion
from src.trading.config.symbol_owner_policy import (
    COEXIST_ENTRY_ENABLED,
    COEXIST_EXIT_ONLY,
    EXCLUSIVE_MANUAL,
    SymbolOwnerPolicyError,
    build_symbol_owner_policy_payload,
    policy_content_hash,
    resolve_symbol_owner_policy,
    symbol_owner_entry_authority_hash,
)
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
    OwnerRegistryBusy,
    OwnerRegistryConflict,
    OwnerRegistryError,
)

TARGET_DATE = date(2026, 9, 3)
SYMBOL = "005930"


@pytest.fixture(autouse=True)
def _explicit_owner_account(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "test-account")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH",
        str(tmp_path / "registry.jsonl"),
    )


def _write_policy(
    path,
    *,
    migration_completed=True,
    active_date=TARGET_DATE,
    mode=COEXIST_ENTRY_ENABLED,
):
    policy_id = f"same_symbol_owner_{active_date.isoformat()}"
    if mode == EXCLUSIVE_MANUAL:
        entry = {
            "mode": mode,
            "allowed_owners": ["manual_operator"],
            "migration_completed": False,
        }
    else:
        assert migration_completed is True
        registry = OrderOwnerRegistry()
        receipt = registry.migration_receipt(
            symbol=SYMBOL,
            broker_quantity=0,
            active_date=active_date,
            verified_exchanges={"KRX", "NXT"},
            broker_open_order_nos=set(),
            broker_snapshot_sha256="d" * 64,
        )
        entry = {
            "mode": mode,
            "allowed_owners": [
                "main_scalping",
                "widget_auto_trade",
                "episode",
            ],
            "migration_completed": True,
            "rollback_mode": "COEXIST_EXIT_ONLY",
            "migration_receipt": receipt,
        }
        entry_hash = symbol_owner_entry_authority_hash(
            active_date=active_date,
            policy_id=policy_id,
            symbol=SYMBOL,
            entry=entry,
        )
        entry["activation_receipt"] = registry.activate_policy_entry(
            active_date=active_date,
            policy_id=policy_id,
            symbol=SYMBOL,
            mode=mode,
            allowed_owners=entry["allowed_owners"],
            migration_receipt=receipt,
            entry_authority_hash=entry_hash,
        )
    payload = build_symbol_owner_policy_payload(
        active_date=active_date,
        policy_id=policy_id,
        generated_at_kst=f"{active_date.isoformat()}T07:00:00+09:00",
        symbol_entries={SYMBOL: entry},
    )
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


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


def test_exact_date_policy_allows_main_and_machine_without_removing_manual_marker(
    tmp_path, monkeypatch
):
    policy_path = tmp_path / "policy.json"
    exclusion_path = tmp_path / "excluded.txt"
    _write_policy(policy_path)
    exclusion_path.write_text(f"{SYMBOL} # manual_operator widget_episode\n")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(exclusion_path)
    )
    manual_control_exclusion._invalidate_file_cache()

    raw = manual_control_exclusion.evaluate_manual_control_exclusion(SYMBOL)
    main = manual_control_exclusion.evaluate_main_bot_control_exclusion(
        SYMBOL, target_date=TARGET_DATE
    )
    machine_source = manual_control_exclusion.independent_machine_ownership_source(
        SYMBOL, owner="episode", target_date=TARGET_DATE
    )

    assert raw.excluded is True
    assert main.excluded is False
    assert main.reason == "exact_date_coexistence_policy_allows_main_bot"
    assert machine_source.startswith("symbol_owner_policy:same_symbol_owner_")


def test_coexistence_never_bypasses_automatic_safety_exclusion(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    exclusion_path = tmp_path / "excluded.txt"
    _write_policy(policy_path)
    exclusion_path.write_text(
        f"{SYMBOL} # manual_operator widget_episode\n"
        f"{SYMBOL} # auto_hard_stop_handoff\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(exclusion_path)
    )
    manual_control_exclusion._invalidate_file_cache()

    decision = manual_control_exclusion.evaluate_main_bot_control_exclusion(
        SYMBOL, target_date=TARGET_DATE
    )

    assert decision.excluded is True


def test_coexistence_never_bypasses_file_auto_safety_when_operator_env_matches(
    tmp_path, monkeypatch
):
    policy_path = tmp_path / "policy.json"
    exclusion_path = tmp_path / "excluded.txt"
    _write_policy(policy_path)
    exclusion_path.write_text(
        f"{SYMBOL} # auto_hard_stop_handoff\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES", SYMBOL)
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(exclusion_path)
    )
    manual_control_exclusion._invalidate_file_cache()

    decision = manual_control_exclusion.evaluate_main_bot_control_exclusion(
        SYMBOL, target_date=TARGET_DATE
    )

    assert decision.excluded is True


def test_policy_requires_migration_and_exact_hash(tmp_path, monkeypatch):
    path = tmp_path / "policy.json"
    payload = _write_policy(path)
    payload["symbols"][SYMBOL]["migration_completed"] = False
    payload["policy_hash"] = policy_content_hash(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(path))
    with pytest.raises(SymbolOwnerPolicyError, match="migration_incomplete"):
        resolve_symbol_owner_policy(SYMBOL, target_date=TARGET_DATE)

    payload["symbols"][SYMBOL]["migration_completed"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SymbolOwnerPolicyError, match="hash_mismatch"):
        resolve_symbol_owner_policy(SYMBOL, target_date=TARGET_DATE)


@pytest.mark.parametrize(
    "symbol", ["1234567", "X005930", "005930_BAD", "005930_NX7", "ABC"]
)
def test_policy_rejects_malformed_symbol_without_truncation(
    tmp_path, monkeypatch, symbol
):
    path = tmp_path / "policy.json"
    _write_policy(path)
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(path))

    with pytest.raises(SymbolOwnerPolicyError, match="symbol_invalid"):
        resolve_symbol_owner_policy(symbol, target_date=TARGET_DATE)


@pytest.mark.parametrize("symbol", ["A005930", "005930_NX", "005930_AL"])
def test_policy_accepts_declared_kiwoom_symbol_wrappers(tmp_path, monkeypatch, symbol):
    path = tmp_path / "policy.json"
    _write_policy(path)
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(path))

    decision = resolve_symbol_owner_policy(symbol, target_date=TARGET_DATE)

    assert decision.symbol == SYMBOL


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


def test_preflight_ownership_sources_require_reachable_registry_tail(
    tmp_path, monkeypatch
):
    policy_path = tmp_path / "policy.json"
    payload = _write_policy(policy_path)
    payload["symbols"][SYMBOL]["migration_receipt"]["registry_tail_hash"] = "f" * 64
    payload["policy_hash"] = policy_content_hash(payload)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    exclusion_path = tmp_path / "excluded.txt"
    exclusion_path.write_text(f"{SYMBOL} # manual_operator widget_episode\n")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(tmp_path / "registry.jsonl")
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(exclusion_path)
    )
    manual_control_exclusion._invalidate_file_cache()

    main = manual_control_exclusion.evaluate_main_bot_control_exclusion(
        SYMBOL, target_date=TARGET_DATE
    )
    episode_source = manual_control_exclusion.independent_machine_ownership_source(
        SYMBOL, owner="episode", target_date=TARGET_DATE
    )

    assert main.excluded is True
    assert main.reason == "symbol_owner_policy_fail_closed:SymbolOwnerPolicyError"
    assert episode_source == ""


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("verified_exchanges", ["KRX"], "all_venues_not_verified"),
        ("broker_open_order_nos", ["1234567"], "open_orders_invalid"),
        ("broker_open_order_nos", ["not-an-order"], "open_orders_invalid"),
        ("broker_account_key", "different-account", "migration_receipt_invalid"),
    ],
)
def test_policy_rejects_incomplete_migration_reconciliation(
    tmp_path, monkeypatch, field, value, expected
):
    path = tmp_path / "policy.json"
    payload = _write_policy(path)
    payload["symbols"][SYMBOL]["migration_receipt"][field] = value
    payload["policy_hash"] = policy_content_hash(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(path))

    with pytest.raises(SymbolOwnerPolicyError, match=expected):
        resolve_symbol_owner_policy(SYMBOL, target_date=TARGET_DATE)


def test_exit_only_policy_cannot_fall_back_to_legacy_entry_authority(
    tmp_path, monkeypatch
):
    policy_path = tmp_path / "policy.json"
    exclusion_path = tmp_path / "excluded.txt"
    _write_policy(policy_path, mode=COEXIST_EXIT_ONLY)
    exclusion_path.write_text(f"{SYMBOL} # manual_operator widget_episode\n")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(exclusion_path)
    )
    manual_control_exclusion._invalidate_file_cache()

    main = manual_control_exclusion.evaluate_main_bot_control_exclusion(
        SYMBOL, target_date=TARGET_DATE
    )
    main_custody = manual_control_exclusion.evaluate_main_bot_control_exclusion(
        SYMBOL, target_date=TARGET_DATE, new_entry=False
    )
    machine_source = manual_control_exclusion.independent_machine_ownership_source(
        SYMBOL, owner="episode", target_date=TARGET_DATE
    )
    custody_source = manual_control_exclusion.independent_machine_ownership_source(
        SYMBOL, owner="episode", target_date=TARGET_DATE, new_entry=False
    )

    assert main.excluded is True
    assert main.reason == "exact_date_owner_policy_blocks_main_bot_entry"
    assert main_custody.excluded is False
    assert main_custody.reason == "exact_date_coexistence_policy_allows_main_bot"
    assert machine_source == ""
    assert custody_source.startswith("symbol_owner_policy:same_symbol_owner_")


def test_exit_only_main_state_guard_blocks_entry_but_allows_existing_custody(
    tmp_path, monkeypatch
):
    runtime_date = datetime.now(kiwoom_orders.KST).date()
    policy_path = tmp_path / "policy.json"
    exclusion_path = tmp_path / "excluded.txt"
    _write_policy(policy_path, mode=COEXIST_EXIT_ONLY, active_date=runtime_date)
    exclusion_path.write_text(f"{SYMBOL} # manual_operator widget_episode\n")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(tmp_path / "registry.jsonl")
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(exclusion_path)
    )
    manual_control_exclusion._invalidate_file_cache()
    stock = {"code": SYMBOL, "status": "HOLDING", "strategy": "SCALPING"}

    entry_blocked = sniper_state_handlers._manual_control_exclusion_blocked(
        stock,
        SYMBOL,
        pipeline="entry",
        stage="test_exit_only_entry",
        now_ts=1.0,
    )
    custody_blocked = sniper_state_handlers._manual_control_exclusion_blocked(
        stock,
        SYMBOL,
        pipeline="holding",
        stage="test_exit_only_custody",
        now_ts=2.0,
    )
    pending_buy_management_blocked = (
        sniper_state_handlers._manual_control_exclusion_blocked(
            stock,
            SYMBOL,
            pipeline="entry",
            stage="test_exit_only_pending_buy_management",
            now_ts=3.0,
            new_entry=False,
        )
    )

    assert entry_blocked is True
    assert custody_blocked is False
    assert pending_buy_management_blocked is False


def test_exclusive_manual_policy_allows_only_manual_owner(tmp_path, monkeypatch):
    policy_path = tmp_path / "policy.json"
    _write_policy(policy_path, mode=EXCLUSIVE_MANUAL)
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    payload["symbols"][SYMBOL]["allowed_owners"] = ["manual_operator"]
    payload["policy_hash"] = policy_content_hash(payload)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))

    decision = resolve_symbol_owner_policy(SYMBOL, target_date=TARGET_DATE)

    assert decision.owner_allowed("manual_operator", new_entry=True) is True
    assert decision.owner_allowed("main_scalping", new_entry=True) is False


def test_registry_serializes_unbound_lane_and_forbids_cross_owner_cancel(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    main = _context("main_scalping", "101")
    widget = _context("widget_auto_trade", "005930")
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
    episode = _context("episode", "morning")
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
            owner_type="episode",
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
            owner_type="episode",
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
            owner_type="episode",
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
                owner_type="episode",
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
    episode = _context("episode", "legacy-morning")
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


def test_migration_receipt_uses_one_locked_registry_generation(tmp_path, monkeypatch):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    episode = _context("episode", "atomic-migration-receipt")
    registry.register_migrated_position(
        context=episode,
        symbol=SYMBOL,
        quantity=20,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="2734568",
        evidence_sha256="a" * 64,
    )
    original_read = registry._read_locked
    read_count = 0

    def counted_read():
        nonlocal read_count
        read_count += 1
        return original_read()

    monkeypatch.setattr(registry, "_read_locked", counted_read)

    receipt = registry.migration_receipt(
        symbol=SYMBOL,
        broker_quantity=20,
        active_date=TARGET_DATE,
        verified_exchanges={"KRX", "NXT"},
        broker_open_order_nos=(),
        broker_snapshot_sha256="e" * 64,
    )

    assert read_count == 1
    assert receipt["registered_owner_quantity"] == 20
    assert receipt["external_manual_remainder"] == 0
    assert receipt["registry_tail_hash"] != "0" * 64


def test_manual_exit_receipt_is_charged_to_one_exact_custody_owner(tmp_path):
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    episode = _context("episode", "manual-exit-owner")
    registry.register_migrated_position(
        context=episode,
        symbol=SYMBOL,
        quantity=20,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="2744567",
        evidence_sha256="a" * 64,
    )
    manual_receipt_context = OwnerOrderContext(
        owner_type=episode.owner_type,
        owner_id=episode.owner_id,
        position_id=episode.position_id,
        client_intent_id="manual-reconcile:2744568",
    )

    registry.register_reconciled_manual_exit(
        custody_context=manual_receipt_context,
        symbol=SYMBOL,
        quantity=10,
        average_price=69_000,
        route="NXT",
        order_date=TARGET_DATE,
        broker_order_no="2744568",
        evidence_sha256="b" * 64,
    )

    assert registry.owner_position_qty(episode.position_id, symbol=SYMBOL) == 10
    owner = registry.order_owner(order_date=TARGET_DATE, broker_order_no="2744568")
    assert owner is not None
    assert owner["owner_type"] == "episode"
    assert owner["execution_owner_type"] == "manual_operator"
    with pytest.raises(OwnerRegistryConflict, match="exceeds_owner_available"):
        registry.register_reconciled_manual_exit(
            custody_context=OwnerOrderContext(
                owner_type=episode.owner_type,
                owner_id=episode.owner_id,
                position_id=episode.position_id,
                client_intent_id="manual-reconcile:overdraw",
            ),
            symbol=SYMBOL,
            quantity=11,
            average_price=69_000,
            route="NXT",
            order_date=TARGET_DATE,
            broker_order_no="2744569",
            evidence_sha256="c" * 64,
        )


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
        owner_type="episode",
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


def test_kiwoom_order_surface_requires_context_only_for_selected_coexistence_symbol(
    tmp_path, monkeypatch
):
    runtime_date = datetime.now(kiwoom_orders.KST).date()
    policy_path = tmp_path / "policy.json"
    registry_path = tmp_path / "registry.jsonl"
    _write_policy(policy_path, active_date=runtime_date)
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry_path))
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(kiwoom_orders, "is_scalping_buy_window_blocked", lambda: False)
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_time_blocked", lambda: False)
    broker_calls = []

    class Response:
        status_code = 200

    def fake_post(*args, **kwargs):
        broker_calls.append((args, kwargs))
        return Response(), {
            "return_code": "0",
            "return_msg": "accepted",
            "ord_no": "4234567",
        }

    monkeypatch.setattr(kiwoom_orders, "_post_kiwoom_with_auth_retry", fake_post)
    blocked = kiwoom_orders.send_buy_order_market(SYMBOL, 1, "token")
    assert blocked["return_code"] == "OWNER_REGISTRY_BLOCKED"
    assert broker_calls == []

    accepted = kiwoom_orders.send_buy_order_market(
        SYMBOL,
        1,
        "token",
        owner_context=_context("main_scalping", "401"),
    )
    assert accepted["return_code"] == "0"
    assert accepted["owner_registry_intent_id"]
    assert len(broker_calls) == 1


def test_registered_symbol_stays_fail_closed_when_next_exact_policy_is_missing(
    tmp_path, monkeypatch
):
    missing_policy = tmp_path / "missing-policy.json"
    registry_path = tmp_path / "registry.jsonl"
    registry = OrderOwnerRegistry(registry_path)
    registry.register_migrated_position(
        context=_context("episode", "sticky-custody"),
        symbol=SYMBOL,
        quantity=10,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="5234567",
        evidence_sha256="b" * 64,
    )
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(missing_policy))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry_path))
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(kiwoom_orders, "is_scalping_buy_window_blocked", lambda: False)
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_time_blocked", lambda: False)
    broker_calls = []
    monkeypatch.setattr(
        kiwoom_orders,
        "_post_kiwoom_with_auth_retry",
        lambda *args, **kwargs: broker_calls.append((args, kwargs)),
    )

    blocked = kiwoom_orders.send_buy_order_market(
        SYMBOL,
        1,
        "token",
        owner_context=_context("main_scalping", "sticky-main"),
    )

    assert blocked["return_code"] == "OWNER_REGISTRY_BLOCKED"
    assert "requires_exact_date_policy" in blocked["return_msg"]
    assert blocked["broker_order_attempted"] is False
    assert broker_calls == []


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


def test_receipt_before_sor_retry_blocks_second_broker_order(tmp_path, monkeypatch):
    runtime_date = datetime.now(kiwoom_orders.KST).date()
    policy_path = tmp_path / "policy.json"
    registry_path = tmp_path / "registry.jsonl"
    _write_policy(policy_path, active_date=runtime_date)
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry_path))
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(kiwoom_orders, "is_scalping_buy_window_blocked", lambda: False)
    monkeypatch.setattr(kiwoom_orders, "is_buy_side_time_blocked", lambda: False)
    broker_calls = []

    class Response:
        status_code = 400

    def reject_after_receipt(*args, **kwargs):
        broker_calls.append((args, kwargs))
        registry = OrderOwnerRegistry(registry_path)
        owner = registry.bind_unique_pending_receipt(
            symbol=SYMBOL,
            side="BUY",
            order_date=runtime_date,
            broker_order_no="6244567",
            broker_order_qty=1,
        )
        assert owner is not None
        context = OwnerOrderContext(
            owner_type=owner["owner_type"],
            owner_id=owner["owner_id"],
            position_id=owner["position_id"],
            client_intent_id=owner["client_intent_id"],
        )
        registry.record_fill(
            context=context,
            symbol=SYMBOL,
            side="BUY",
            order_quantity=1,
            order_date=runtime_date,
            broker_order_no="6244567",
            cumulative_filled_qty=1,
            cumulative_fill_amount=70_000,
        )
        registry.transition(
            owner["intent_id"],
            state="ORDER_TERMINAL",
            broker_order_no="6244567",
            reason="receipt_won_race",
        )
        return Response(), {
            "return_code": "571034",
            "return_msg": "SOR 시장가 주문은 08:30 이후",
        }

    monkeypatch.setattr(
        kiwoom_orders, "_post_kiwoom_with_auth_retry", reject_after_receipt
    )

    result = kiwoom_orders.send_buy_order_market(
        SYMBOL,
        1,
        "token",
        order_type="3",
        owner_context=_context("main_scalping", "sor-race"),
    )

    assert result["return_code"] == "OWNER_REGISTRY_BLOCKED"
    assert result["broker_order_attempted"] is True
    assert len(broker_calls) == 1


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


def test_policy_builder_is_deterministic_and_does_not_publish(tmp_path):
    entry = _write_policy(tmp_path / "source.json")["symbols"][SYMBOL]
    first = build_symbol_owner_policy_payload(
        active_date=TARGET_DATE,
        policy_id="same_symbol_owner_2026-09-03",
        symbol_entries={SYMBOL: entry},
        generated_at_kst="2026-09-03T07:00:00+09:00",
    )
    second = build_symbol_owner_policy_payload(
        active_date=TARGET_DATE,
        policy_id="same_symbol_owner_2026-09-03",
        symbol_entries={SYMBOL: entry},
        generated_at_kst="2026-09-03T07:00:00+09:00",
    )

    assert first == second
    assert first["policy_hash"] == policy_content_hash(first)
    assert not (tmp_path / "symbol_owner_policy_2026-09-03.json").exists()


def test_policy_builder_rejects_an_unloadable_symbol_entry(tmp_path):
    entry = _write_policy(tmp_path / "source.json")["symbols"][SYMBOL]
    entry["migration_receipt"]["verified_exchanges"] = ["KRX"]

    with pytest.raises(SymbolOwnerPolicyError, match="all_venues_not_verified"):
        build_symbol_owner_policy_payload(
            active_date=TARGET_DATE,
            policy_id="invalid-candidate",
            symbol_entries={SYMBOL: entry},
            generated_at_kst="2026-09-03T07:00:00+09:00",
        )


def test_policy_loader_rejects_partial_artifact_with_invalid_other_symbol(
    tmp_path, monkeypatch
):
    path = tmp_path / "policy.json"
    payload = _write_policy(path)
    payload["symbols"]["000660"] = {
        **payload["symbols"][SYMBOL],
        "mode": "NOT_A_MODE",
    }
    payload["policy_hash"] = policy_content_hash(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(path))

    with pytest.raises(SymbolOwnerPolicyError, match="mode_invalid"):
        resolve_symbol_owner_policy(SYMBOL, target_date=TARGET_DATE)


def test_main_sell_classifier_preserves_post_broker_registry_ambiguity():
    classified = sniper_state_handlers._classify_sell_submit_response(
        {
            "return_code": "OWNER_REGISTRY_BLOCKED",
            "return_msg": "journal failed",
            "ord_no": "9334567",
            "broker_order_attempted": True,
            "owner_registry_required": True,
        }
    )

    assert classified["state"] == "ambiguous"
    assert classified["broker_order_attempted"] is True
    assert classified["order_no"] == "9334567"


def test_main_receipt_target_lookup_uses_exact_registry_owner_identity(monkeypatch):
    first = {"id": 101, "code": SYMBOL, "status": "BUY_ORDERED"}
    second = {"id": 202, "code": SYMBOL, "status": "BUY_ORDERED"}
    monkeypatch.setattr(sniper_execution_receipts, "ACTIVE_TARGETS", [first, second])

    matched = sniper_execution_receipts._find_execution_target(
        SYMBOL,
        "BUY",
        "7234567",
        owner_target_id="202",
    )

    assert matched is second


def test_aggregate_balance_never_overwrites_registered_symbol_without_daily_policy(
    tmp_path, monkeypatch
):
    missing_policy = tmp_path / "missing-policy.json"
    registry_path = tmp_path / "registry.jsonl"
    registry = OrderOwnerRegistry(registry_path)
    registry.register_migrated_position(
        context=_context("episode", "sticky-sync"),
        symbol=SYMBOL,
        quantity=10,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="8234567",
        evidence_sha256="c" * 64,
    )
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(missing_policy))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry_path))
    target = {"id": 11, "code": SYMBOL, "status": "BUY_ORDERED"}
    record = type(
        "Record",
        (),
        {"id": 11, "buy_qty": 0, "stock_name": "Samsung", "scale_in_locked": False},
    )()
    monkeypatch.setattr(sniper_sync, "ACTIVE_TARGETS", [target])

    preserved = sniper_sync._preserve_coexistence_owner_inventory(
        record=record,
        code=SYMBOL,
        real_codes={SYMBOL: {"qty": 10}},
        source="test_balance_sync",
    )

    assert preserved is True
    assert record.buy_qty == 0
    assert record.scale_in_locked is True
    assert target["broker_holding_qty"] == 10
    assert target["broker_symbol_allocation_conflict"] is True
    assert "requires_exact_date_policy" in target["sell_cancel_reconciliation_source"]


def test_main_cancel_reconciliation_uses_owner_qty_not_aggregate_balance(
    tmp_path, monkeypatch
):
    runtime_date = datetime.now(kiwoom_orders.KST).date()
    registry_path = tmp_path / "registry.jsonl"
    registry = OrderOwnerRegistry(registry_path)
    main_position = OwnerOrderContext(
        owner_type="main_scalping",
        owner_id="main_scalping:11",
        position_id="main_scalping:11",
        client_intent_id="migration:main:11",
    )
    episode_position = _context("episode", "coexisting-cancel")
    registry.register_migrated_position(
        context=main_position,
        symbol=SYMBOL,
        quantity=5,
        average_price=70_000,
        route="KRX",
        order_date=runtime_date,
        broker_order_no="8244567",
        evidence_sha256="1" * 64,
    )
    registry.register_migrated_position(
        context=episode_position,
        symbol=SYMBOL,
        quantity=10,
        average_price=70_000,
        route="KRX",
        order_date=runtime_date,
        broker_order_no="8244568",
        evidence_sha256="2" * 64,
    )
    open_context = OwnerOrderContext(
        owner_type="main_scalping",
        owner_id="main_scalping:11",
        position_id="main_scalping:11",
        client_intent_id="main:11:open-buy",
    )
    intent = registry.reserve(
        context=open_context,
        symbol=SYMBOL,
        side="BUY",
        quantity=2,
        route="SOR",
        order_date=runtime_date,
    )
    registry.transition(intent, state="ORDER_BOUND", broker_order_no="8244569")
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry_path))
    monkeypatch.setattr(sniper_state_handlers, "KIWOOM_TOKEN", "token")
    stock = {"id": 11, "code": SYMBOL, "status": "BUY_ORDERED"}
    monkeypatch.setattr(sniper_state_handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(
        sniper_state_handlers.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: ([], {"request_succeeded": True}),
    )
    monkeypatch.setattr(
        sniper_state_handlers.kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": SYMBOL, "qty": 15}], {"KRX", "NXT"}),
    )

    reconciled, reason, observed_qty = (
        sniper_state_handlers._order_terminal_inventory_reconciliation(
            stock,
            SYMBOL,
            ["8244569"],
            expected_runtime_qty=5,
        )
    )

    assert reconciled is True
    assert reason == "terminal_absence_and_owner_inventory_exact"
    assert observed_qty == 5
    owner = registry.order_owner(order_date=runtime_date, broker_order_no="8244569")
    assert owner is not None
    assert owner["state"] == "ORDER_TERMINAL"


def test_main_sell_reconciliation_returns_exact_owner_qty(tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.jsonl"
    registry = OrderOwnerRegistry(registry_path)
    registry.register_migrated_position(
        context=OwnerOrderContext(
            owner_type="main_scalping",
            owner_id="main_scalping:11",
            position_id="main_scalping:11",
            client_intent_id="migration:main:sell-reconcile",
        ),
        symbol=SYMBOL,
        quantity=5,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="8254567",
        evidence_sha256="3" * 64,
    )
    registry.register_migrated_position(
        context=_context("widget_auto_trade", "sell-reconcile"),
        symbol=SYMBOL,
        quantity=10,
        average_price=70_000,
        route="KRX",
        order_date=TARGET_DATE,
        broker_order_no="8254568",
        evidence_sha256="4" * 64,
    )
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry_path))
    stock = {"id": 11, "code": SYMBOL, "status": "SELL_ORDERED"}
    monkeypatch.setattr(sniper_state_handlers, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(sniper_state_handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        sniper_state_handlers.kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": SYMBOL, "qty": 15}], {"KRX", "NXT"}),
    )

    quantity, source = (
        sniper_state_handlers._broker_position_qty_for_sell_reconciliation(
            SYMBOL, stock
        )
    )

    assert quantity == 5
    assert source == "owner_registry_plus_all_venue_inventory"
