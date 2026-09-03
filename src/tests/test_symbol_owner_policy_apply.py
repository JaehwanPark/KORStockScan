from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from src.trading.config.symbol_owner_policy import resolve_symbol_owner_policy
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerOrderContext,
    OwnerRegistryConflict,
)
from src.trading.order.symbol_owner_policy_apply import (
    REQUEST_SCHEMA,
    SymbolOwnerPolicyApplyError,
    apply_symbol_owner_policy,
    collect_broker_snapshot,
)

KST = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 9, 3, 8, 40, tzinfo=KST)
SYMBOL = "005930"


def _request(
    path: Path,
    *,
    broker_quantity: int = 0,
    external_remainder: int = 0,
    migrations: list[dict] | None = None,
) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": REQUEST_SCHEMA,
                "active_date": "2026-09-03",
                "policy_id": "same_symbol_owner_2026-09-03",
                "generated_at_kst": NOW.isoformat(),
                "broker_account_key": "kiwoom-live-primary",
                "symbols": {
                    SYMBOL: {
                        "mode": "COEXIST_ENTRY_ENABLED",
                        "allowed_owners": [
                            "main_scalping",
                            "widget_auto_trade",
                            "episode",
                        ],
                        "expected_broker_quantity": broker_quantity,
                        "expected_external_manual_remainder": external_remainder,
                        "migrated_positions": migrations or [],
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _snapshot(
    *,
    quantity: int = 0,
    open_orders: list[dict] | None = None,
    migration_receipts: list[dict] | None = None,
) -> dict:
    canonical = {
        "verified_exchanges": ["KRX", "NXT"],
        "inventory": {SYMBOL: quantity},
        "open_orders": open_orders or [],
        "migration_receipts": migration_receipts or [],
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return {**canonical, "snapshot_sha256": digest}


def _migration_fixture(
    *,
    owner_type: str = "episode",
    owner_id: str = "episode:samsung_morning",
    position_id: str = "episode:samsung_morning:leg1",
    client_intent_id: str = "migration:samsung_morning:leg1",
    order_date: str = "2026-09-02",
    order_no: str = "1234567",
    quantity: int = 10,
    average_price: int = 70_000,
) -> tuple[dict, dict]:
    receipt = {
        "symbol": SYMBOL,
        "order_date": order_date,
        "order_no": order_no,
        "side": "매수",
        "quantity": quantity,
        "filled_quantity": quantity,
        "remaining_quantity": 0,
        "execution_price": average_price,
        "route": "KRX",
    }
    receipt["evidence_sha256"] = hashlib.sha256(
        json.dumps(
            receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    migration = {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "position_id": position_id,
        "client_intent_id": client_intent_id,
        "order_date": order_date,
        "quantity": quantity,
        "average_price": average_price,
        "route": "KRX",
        "broker_order_no": order_no,
        "evidence_sha256": receipt["evidence_sha256"],
    }
    return migration, receipt


def test_dry_run_is_read_only_and_reports_exact_confirmation(tmp_path, monkeypatch):
    request_path = _request(tmp_path / "request.json")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    policy = tmp_path / "policy.json"
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy))

    result = apply_symbol_owner_policy(
        request_path,
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda _token, _symbols, _migrations: _snapshot(),
        token_loader=lambda: "cached-token",
        registry=registry,
        receipt_dir=tmp_path / "receipts",
        owner_env_file=tmp_path / "owner.env",
        apply_lock_path=tmp_path / "apply.lock",
    )

    assert result["status"] == "dry_run_ready"
    assert result["runtime_effect"] is False
    assert result["required_confirmation"] == (
        "APPLY SAME SYMBOL OWNER POLICY 2026-09-03"
    )
    assert not registry.path.exists()
    assert not policy.exists()
    assert not (tmp_path / "owner.env").exists()


def test_broker_snapshot_rechecks_exact_completed_buy_migration_receipt(monkeypatch):
    from src.engine import kiwoom_orders
    from src.utils import kiwoom_utils

    monkeypatch.setattr(
        kiwoom_orders,
        "get_my_inventory",
        lambda _token: ([{"code": SYMBOL, "qty": 10}], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(kiwoom_orders, "get_last_inventory_errors", lambda: [])
    monkeypatch.setattr(
        kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *_args, **_kwargs: (
            [],
            {"request_succeeded": True, "normalization_contract_complete": True},
        ),
    )
    receipt_calls = []

    def receipt_snapshot(*_args, **kwargs):
        receipt_calls.append(kwargs)
        return (
            [
                {
                    "code": SYMBOL,
                    "ord_no": "1234567",
                    "side": "매수",
                    "qty": 10,
                    "filled_qty": 10,
                    "remaining_qty": 0,
                    "execution_price": 70_000,
                    "stex_tp": "KRX",
                    "sor_yn": "N",
                }
            ],
            {"request_succeeded": True, "normalization_contract_complete": True},
        )

    monkeypatch.setattr(
        kiwoom_utils,
        "get_order_reference_snapshot_kt00007_with_meta",
        receipt_snapshot,
    )

    snapshot = collect_broker_snapshot(
        "cached-token",
        {SYMBOL},
        (
            {
                "symbol": SYMBOL,
                "order_date": "2026-09-02",
                "broker_order_no": "1234567",
            },
        ),
    )

    assert receipt_calls == [
        {
            "ord_dt": "20260902",
            "qry_tp": "4",
            "stk_bond_tp": "1",
            "sell_tp": "2",
            "stk_cd": SYMBOL,
            "dmst_stex_tp": "%",
        }
    ]
    assert snapshot["migration_receipts"][0]["filled_quantity"] == 10
    assert len(snapshot["migration_receipts"][0]["evidence_sha256"]) == 64


def test_apply_publishes_only_after_exact_registry_activation(tmp_path, monkeypatch):
    request_path = _request(tmp_path / "request.json")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    policy = tmp_path / "policy.json"
    owner_env = tmp_path / "owner.env"
    receipt_dir = tmp_path / "receipts"
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry.path))

    result = apply_symbol_owner_policy(
        request_path,
        apply=True,
        confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda _token, _symbols, _migrations: _snapshot(),
        token_loader=lambda: "cached-token",
        registry=registry,
        receipt_dir=receipt_dir,
        owner_env_file=owner_env,
        apply_lock_path=tmp_path / "apply.lock",
        output_policy_path=policy,
    )

    assert result["status"] == "applied"
    assert result["runtime_effect"] is True
    decision = resolve_symbol_owner_policy(SYMBOL, target_date="2026-09-03")
    assert decision.coexistence_enabled is True
    assert registry.decision_activation_matches(decision) is True
    assert "KORSTOCKSCAN_BROKER_ACCOUNT_KEY=kiwoom-live-primary" in (
        owner_env.read_text(encoding="utf-8")
    )
    assert f"KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE={policy}" in (
        owner_env.read_text(encoding="utf-8")
    )
    assert (
        receipt_dir / "symbol_owner_policy_apply_2026-09-03.json"
    ).exists()


def test_apply_migrates_exact_existing_machine_custody_before_activation(
    tmp_path, monkeypatch
):
    request_path = _request(
        tmp_path / "request.json",
        broker_quantity=10,
        migrations=[
            {
                "owner_type": "episode",
                "owner_id": "episode:samsung_morning",
                "position_id": "episode:samsung_morning:leg1",
                "client_intent_id": "migration:samsung_morning:leg1",
                "order_date": "2026-09-02",
                "quantity": 10,
                "average_price": 70_000,
                "route": "KRX",
                "broker_order_no": "1234567",
                "evidence_sha256": "c" * 64,
            }
        ],
    )
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    policy = tmp_path / "policy.json"
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry.path))
    canonical_receipt = {
        "symbol": SYMBOL,
        "order_date": "2026-09-02",
        "order_no": "1234567",
        "side": "매수",
        "quantity": 10,
        "filled_quantity": 10,
        "remaining_quantity": 0,
        "execution_price": 70_000,
        "route": "KRX",
    }
    canonical_receipt["evidence_sha256"] = hashlib.sha256(
        json.dumps(
            canonical_receipt,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    request_payload["symbols"][SYMBOL]["migrated_positions"][0][
        "evidence_sha256"
    ] = canonical_receipt["evidence_sha256"]
    request_path.write_text(json.dumps(request_payload), encoding="utf-8")
    snapshot = _snapshot(quantity=10, migration_receipts=[canonical_receipt])

    apply_symbol_owner_policy(
        request_path,
        apply=True,
        confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda _token, _symbols, _migrations: snapshot,
        token_loader=lambda: "cached-token",
        registry=registry,
        receipt_dir=tmp_path / "receipts",
        owner_env_file=tmp_path / "owner.env",
        apply_lock_path=tmp_path / "apply.lock",
        output_policy_path=policy,
    )

    decision = resolve_symbol_owner_policy(SYMBOL, target_date="2026-09-03")
    assert registry.decision_activation_matches(decision) is True
    assert registry.owner_position_qty(
        "episode:samsung_morning:leg1", symbol=SYMBOL
    ) == 10

    # A process failure after registry activation can safely resume without
    # registering the migration twice or producing a different policy.
    first_policy = policy.read_bytes()
    apply_symbol_owner_policy(
        request_path,
        apply=True,
        confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda _token, _symbols, _migrations: snapshot,
        token_loader=lambda: "cached-token",
        registry=registry,
        receipt_dir=tmp_path / "receipts",
        owner_env_file=tmp_path / "owner.env",
        apply_lock_path=tmp_path / "apply.lock",
        output_policy_path=policy,
    )
    assert policy.read_bytes() == first_policy
    assert registry.owner_position_qty(
        "episode:samsung_morning:leg1", symbol=SYMBOL
    ) == 10


def test_apply_resumes_after_migration_append_before_activation(tmp_path, monkeypatch):
    migration, receipt = _migration_fixture()
    request_path = _request(
        tmp_path / "request.json", broker_quantity=10, migrations=[migration]
    )
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    policy = tmp_path / "policy.json"
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy))
    monkeypatch.setenv("KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry.path))
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "kiwoom-live-primary")
    registry.register_migrated_position(
        context=OwnerOrderContext(
            owner_type=migration["owner_type"],
            owner_id=migration["owner_id"],
            position_id=migration["position_id"],
            client_intent_id=migration["client_intent_id"],
        ),
        symbol=SYMBOL,
        quantity=migration["quantity"],
        average_price=migration["average_price"],
        route=migration["route"],
        order_date=migration["order_date"],
        broker_order_no=migration["broker_order_no"],
        evidence_sha256=migration["evidence_sha256"],
    )
    snapshot = _snapshot(quantity=10, migration_receipts=[receipt])

    result = apply_symbol_owner_policy(
        request_path,
        apply=True,
        confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda _token, _symbols, _migrations: snapshot,
        token_loader=lambda: "cached-token",
        registry=registry,
        receipt_dir=tmp_path / "receipts",
        owner_env_file=tmp_path / "owner.env",
        apply_lock_path=tmp_path / "apply.lock",
        output_policy_path=policy,
    )

    assert result["status"] == "applied"
    assert registry.owner_position_qty(migration["position_id"], symbol=SYMBOL) == 10
    assert len(
        [
            row
            for row in registry.path.read_text(encoding="utf-8").splitlines()
            if '"event":"MIGRATED_POSITION_REGISTERED"' in row
        ]
    ) == 1


def test_apply_rejects_migration_owner_outside_policy_owner_set(tmp_path):
    migration, _receipt = _migration_fixture(owner_type="manual_operator")
    request_path = _request(
        tmp_path / "request.json", broker_quantity=10, migrations=[migration]
    )

    with pytest.raises(SymbolOwnerPolicyApplyError, match="owner_not_allowed"):
        apply_symbol_owner_policy(
            request_path,
            now=NOW,
            process_scanner=lambda: pytest.fail("process scan must not run"),
            token_loader=lambda: pytest.fail("token must not be loaded"),
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
        )


def test_apply_rejects_future_generated_request(tmp_path):
    request_path = _request(tmp_path / "request.json")
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    payload["generated_at_kst"] = NOW.replace(hour=8, minute=41).isoformat()
    request_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        SymbolOwnerPolicyApplyError, match="exact_date_or_policy_id_invalid"
    ):
        apply_symbol_owner_policy(
            request_path,
            now=NOW,
            process_scanner=lambda: pytest.fail("process scan must not run"),
            token_loader=lambda: pytest.fail("token must not be loaded"),
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
        )


def test_dry_run_rejects_migration_receipt_order_quantity_mismatch(
    tmp_path, monkeypatch
):
    migration, receipt = _migration_fixture()
    receipt["quantity"] = 20
    receipt["evidence_sha256"] = hashlib.sha256(
        json.dumps(
            {key: value for key, value in receipt.items() if key != "evidence_sha256"},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    migration["evidence_sha256"] = receipt["evidence_sha256"]
    request_path = _request(
        tmp_path / "request.json", broker_quantity=10, migrations=[migration]
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(tmp_path / "registry.jsonl")
    )

    with pytest.raises(SymbolOwnerPolicyApplyError, match="receipt_mismatch"):
        apply_symbol_owner_policy(
            request_path,
            now=NOW,
            process_scanner=lambda: [],
            snapshot_fetcher=lambda _token, _symbols, _migrations: _snapshot(
                quantity=10, migration_receipts=[receipt]
            ),
            token_loader=lambda: "cached-token",
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
        )


def test_same_broker_order_number_on_different_dates_is_not_duplicate(tmp_path):
    first, first_receipt = _migration_fixture()
    second, second_receipt = _migration_fixture(
        position_id="episode:samsung_morning:leg2",
        client_intent_id="migration:samsung_morning:leg2",
        order_date="2026-09-01",
    )
    request_path = _request(
        tmp_path / "request.json",
        broker_quantity=20,
        migrations=[first, second],
    )

    result = apply_symbol_owner_policy(
        request_path,
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda _token, _symbols, _migrations: _snapshot(
            quantity=20, migration_receipts=[first_receipt, second_receipt]
        ),
        token_loader=lambda: "cached-token",
        registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
    )

    assert result["status"] == "dry_run_ready"


def test_live_apply_requires_same_effective_user_as_services(tmp_path, monkeypatch):
    request_path = _request(tmp_path / "request.json")
    monkeypatch.setattr(
        "src.trading.order.symbol_owner_policy_apply.pwd.getpwuid",
        lambda _uid: SimpleNamespace(pw_name="root"),
    )

    with pytest.raises(SymbolOwnerPolicyApplyError, match="runtime_user:ubuntu"):
        apply_symbol_owner_policy(
            request_path,
            apply=True,
            confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
            now=NOW,
            process_scanner=lambda: pytest.fail("process scan must not run"),
            token_loader=lambda: pytest.fail("token must not be loaded"),
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
        )

def test_apply_fails_before_mutation_when_broker_snapshot_drifts(
    tmp_path, monkeypatch
):
    request_path = _request(tmp_path / "request.json")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(tmp_path / "policy.json")
    )
    snapshots = iter(
        [
            _snapshot(),
            _snapshot(
                open_orders=[
                    {
                        "symbol": "000660",
                        "order_no": "7654321",
                        "side": "매수",
                        "quantity": 1,
                        "filled_quantity": 0,
                        "remaining_quantity": 1,
                        "route": "KRX",
                    }
                ]
            ),
        ]
    )

    with pytest.raises(SymbolOwnerPolicyApplyError, match="snapshot_drift"):
        apply_symbol_owner_policy(
            request_path,
            apply=True,
            confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
            now=NOW,
            process_scanner=lambda: [],
            snapshot_fetcher=lambda _token, _symbols, _migrations: next(snapshots),
            token_loader=lambda: "cached-token",
            registry=registry,
            receipt_dir=tmp_path / "receipts",
            owner_env_file=tmp_path / "owner.env",
            apply_lock_path=tmp_path / "apply.lock",
        )

    assert not registry.path.exists()
    assert not (tmp_path / "policy.json").exists()


def test_apply_requires_quiescent_trading_processes(tmp_path):
    request_path = _request(tmp_path / "request.json")

    with pytest.raises(SymbolOwnerPolicyApplyError, match="not_quiescent"):
        apply_symbol_owner_policy(
            request_path,
            apply=True,
            confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
            now=NOW,
            process_scanner=lambda: [{"pid": 101, "command": "bot_main.py"}],
            token_loader=lambda: pytest.fail("token must not be loaded"),
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
            receipt_dir=tmp_path / "receipts",
            owner_env_file=tmp_path / "owner.env",
            apply_lock_path=tmp_path / "apply.lock",
        )


def test_apply_is_forbidden_outside_bounded_preopen_window(tmp_path):
    request_path = _request(tmp_path / "request.json")

    with pytest.raises(SymbolOwnerPolicyApplyError, match="outside_preopen_window"):
        apply_symbol_owner_policy(
            request_path,
            apply=True,
            confirmation="APPLY SAME SYMBOL OWNER POLICY 2026-09-03",
            now=NOW.replace(hour=10),
            process_scanner=lambda: pytest.fail("process scan must not run"),
            token_loader=lambda: pytest.fail("token must not be loaded"),
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
            receipt_dir=tmp_path / "receipts",
            owner_env_file=tmp_path / "owner.env",
            apply_lock_path=tmp_path / "apply.lock",
        )


@pytest.mark.parametrize(
    ("field_path", "value", "reason"),
    [
        (("broker_account_key",), "default", "explicit_account_key_invalid"),
        (
            ("symbols", SYMBOL, "mode"),
            "MAIN_ONLY",
            "mode_or_owner_set_invalid",
        ),
        (
            ("symbols", SYMBOL, "mode"),
            "MACHINE_EXCLUSIVE",
            "mode_or_owner_set_invalid",
        ),
    ],
)
def test_apply_rejects_unsafe_or_implicit_authority(
    tmp_path, field_path, value, reason
):
    request_path = _request(tmp_path / "request.json")
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    target = payload
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = value
    request_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SymbolOwnerPolicyApplyError, match=reason):
        apply_symbol_owner_policy(
            request_path,
            now=NOW,
            process_scanner=lambda: [],
            token_loader=lambda: pytest.fail("token must not be loaded"),
            registry=OrderOwnerRegistry(tmp_path / "registry.jsonl"),
            receipt_dir=tmp_path / "receipts",
            owner_env_file=tmp_path / "owner.env",
            apply_lock_path=tmp_path / "apply.lock",
        )


def test_activation_rejects_migration_receipt_after_intervening_append(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    receipt = registry.migration_receipt(
        symbol=SYMBOL,
        broker_quantity=0,
        active_date="2026-09-03",
        verified_exchanges={"KRX", "NXT"},
        broker_open_order_nos=set(),
        broker_snapshot_sha256="d" * 64,
    )
    registry.reserve(
        context=OwnerOrderContext(
            owner_type="episode",
            owner_id="episode:other",
            position_id="episode:other:position",
            client_intent_id="episode:other:pending",
        ),
        symbol="000660",
        side="BUY",
        quantity=1,
        route="KRX",
        order_date="2026-09-03",
    )

    with pytest.raises(OwnerRegistryConflict, match="stale_migration_tail"):
        registry.activate_policy_entry(
            active_date="2026-09-03",
            policy_id="same_symbol_owner_2026-09-03",
            symbol=SYMBOL,
            mode="COEXIST_ENTRY_ENABLED",
            allowed_owners=("main_scalping", "episode"),
            migration_receipt=receipt,
            entry_authority_hash="e" * 64,
        )


def test_exact_migration_registration_is_idempotent_before_activation(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    context = OwnerOrderContext(
        owner_type="episode",
        owner_id="episode:samsung_morning",
        position_id="episode:samsung_morning:leg1",
        client_intent_id="migration:samsung_morning:leg1",
    )
    arguments = {
        "context": context,
        "symbol": SYMBOL,
        "quantity": 10,
        "average_price": 70_000,
        "route": "KRX",
        "order_date": "2026-09-03",
        "broker_order_no": "1234567",
        "evidence_sha256": "c" * 64,
    }

    first = registry.register_migrated_position(**arguments)
    second = registry.register_migrated_position(**arguments)

    assert first == second
    assert len(registry.path.read_text(encoding="utf-8").splitlines()) == 1


def test_migration_append_is_forbidden_after_any_symbol_activation(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "test-account")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    receipt = registry.migration_receipt(
        symbol=SYMBOL,
        broker_quantity=0,
        active_date="2026-09-03",
        verified_exchanges={"KRX", "NXT"},
        broker_open_order_nos=set(),
        broker_snapshot_sha256="d" * 64,
    )
    registry.activate_policy_entry(
        active_date="2026-09-03",
        policy_id="same_symbol_owner_2026-09-03",
        symbol=SYMBOL,
        mode="COEXIST_ENTRY_ENABLED",
        allowed_owners=("main_scalping", "episode"),
        migration_receipt=receipt,
        entry_authority_hash="e" * 64,
    )

    with pytest.raises(OwnerRegistryConflict, match="after_policy_activation"):
        registry.register_migrated_position(
            context=OwnerOrderContext(
                owner_type="episode",
                owner_id="episode:samsung_morning",
                position_id="episode:samsung_morning:leg1",
                client_intent_id="migration:samsung_morning:leg1",
            ),
            symbol=SYMBOL,
            quantity=10,
            average_price=70_000,
            route="KRX",
            order_date="2026-09-02",
            broker_order_no="1234567",
            evidence_sha256="c" * 64,
        )


def test_registered_symbol_fails_closed_when_shared_account_identity_is_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY", "account-a")
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    registry.register_migrated_position(
        context=OwnerOrderContext(
            owner_type="episode",
            owner_id="episode:samsung_morning",
            position_id="episode:samsung_morning:leg1",
            client_intent_id="migration:samsung_morning:leg1",
        ),
        symbol=SYMBOL,
        quantity=10,
        average_price=70_000,
        route="KRX",
        order_date="2026-09-02",
        broker_order_no="1234567",
        evidence_sha256="c" * 64,
    )
    monkeypatch.delenv("KORSTOCKSCAN_BROKER_ACCOUNT_KEY")

    with pytest.raises(OwnerRegistryConflict, match="account_identity_missing"):
        registry.symbol_registered(SYMBOL)


def test_all_order_process_launchers_load_shared_owner_account_identity():
    environment_file = (
        "EnvironmentFile=-/home/ubuntu/KORStockScan/data/runtime/"
        "symbol_owner_policy/owner_custody.env"
    )
    unit_paths = [
        "deploy/systemd/korstockscan-widget-signal-auto-trader.service",
        "deploy/systemd/korstockscan-samsung-morning-one-share.service",
        "deploy/systemd/korstockscan-samsung-one-share-preflight.service",
        "deploy/systemd/korstockscan-samsung-midday-one-share.service",
        "deploy/systemd/korstockscan-samsung-afternoon-one-share.service",
        "deploy/systemd/korstockscan-low-price-two-leg@.service",
        "deploy/systemd/korstockscan-samsung-midday-one-share-preflight.service",
        "deploy/systemd/korstockscan-samsung-afternoon-one-share-preflight.service",
        "deploy/systemd/korstockscan-low-price-two-leg-preflight@.service",
    ]
    for path in unit_paths:
        assert environment_file in Path(path).read_text(encoding="utf-8")

    launcher = Path("src/run_bot.sh").read_text(encoding="utf-8")
    assert "OWNER_CUSTODY_RUNTIME_ENV" in launcher
    assert '. "$OWNER_CUSTODY_RUNTIME_ENV"' in launcher
