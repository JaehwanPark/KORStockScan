from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.trading.config.symbol_owner_standing_authority import (
    STANDING_APPLY_BINDING_SCHEMA,
    SymbolOwnerStandingAuthorityError,
    build_standing_authority,
    load_standing_authority,
)
from src.trading.order.owner_custody_registry import (
    OrderOwnerRegistry,
    OwnerRegistryConflict,
)
from src.trading.order.symbol_owner_policy_apply import (
    APPLY_RECEIPT_SCHEMA,
    REQUEST_SCHEMA,
    SymbolOwnerPolicyApplyError,
    apply_symbol_owner_policy,
)
from src.trading.order.symbol_owner_policy_auto_apply import (
    SymbolOwnerPolicyAutoApplyError,
    expected_machine_symbol_owners,
    run_auto_apply,
)

KST = ZoneInfo("Asia/Seoul")
TARGET_DATE = date(2026, 9, 7)
NOW = datetime(2026, 9, 7, 7, 40, tzinfo=KST)
SYMBOL_A = "005930"
SYMBOL_B = "034020"
OWNERS = {
    SYMBOL_A: ["episode", "main_scalping", "manual_operator"],
    SYMBOL_B: [
        "main_scalping",
        "manual_operator",
        "widget_auto_trade",
    ],
}


def _write_authority(path: Path, *, owners=None) -> dict:
    payload = build_standing_authority(
        authorization_id="test-standing-authority",
        operator_instruction="Apply exact-date coexistence unattended.",
        reviewed_at_kst="2026-09-04T15:20:00+09:00",
        effective_from="2026-09-07",
        expires_after="2026-12-31",
        broker_account_key="kiwoom-live-primary",
        preopen_start="07:32:00",
        preopen_end="07:54:00",
        symbols=owners or OWNERS,
    )
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def _snapshot(*, open_orders=None, quantities=None) -> dict:
    canonical = {
        "verified_exchanges": ["KRX", "NXT"],
        "inventory": {
            symbol: int((quantities or {}).get(symbol, 0))
            for symbol in sorted(OWNERS)
        },
        "open_orders": open_orders or [],
        "migration_receipts": [],
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {**canonical, "snapshot_sha256": digest}


class _Registry:
    def __init__(
        self,
        path: Path,
        *,
        conflicts=(),
        open_order_conflicts=(),
        unresolved=(),
    ):
        self.path = path.resolve()
        self._conflicts = set(conflicts)
        self._open_order_conflicts = set(open_order_conflicts)
        self._unresolved = set(unresolved)

    def reconcile_symbol_quantity(self, *, symbol, broker_quantity):
        if symbol in self._conflicts:
            raise OwnerRegistryConflict("owner_registry_broker_quantity_deficit")
        return {
            "registered_owner_quantity": int(broker_quantity),
            "external_manual_remainder": 0,
        }

    def unresolved_intent_summary(self, *, symbol, active_date):
        return {
            "symbol": symbol,
            "active_date": active_date.isoformat(),
            "unresolved_intent_count": 1 if symbol in self._unresolved else 0,
            "states": ["INTENT_AMBIGUOUS"] if symbol in self._unresolved else [],
            "sides": ["BUY"] if symbol in self._unresolved else [],
        }

    def migration_receipt(self, *, symbol, **_kwargs):
        if symbol in self._open_order_conflicts:
            raise OwnerRegistryConflict("owner_registry_migration_open_order_set_mismatch")
        return {"validated": True}


@pytest.fixture
def auto_scope(monkeypatch):
    monkeypatch.setattr(
        "src.trading.order.symbol_owner_policy_auto_apply."
        "expected_machine_symbol_owners",
        lambda _target_date: OWNERS,
    )
    monkeypatch.setattr(
        "src.trading.order.symbol_owner_policy_auto_apply."
        "manual_control_operator_exclusion_source",
        lambda _symbol: "manual_operator",
    )
    monkeypatch.setattr(
        "src.trading.order.symbol_owner_policy_auto_apply."
        "get_krx_trading_day_status",
        lambda _target_date: (True, "trading_day"),
    )


def test_expected_scope_covers_all_current_widget_and_episode_symbols():
    scope = expected_machine_symbol_owners(TARGET_DATE)

    assert len(scope) == 18
    assert set(scope) == {
        "002900",
        "005930",
        "006800",
        "010140",
        "015760",
        "017670",
        "028050",
        "028670",
        "034020",
        "035720",
        "042660",
        "079160",
        "080220",
        "105630",
        "111770",
        "137310",
        "181710",
        "475150",
    }
    assert all("main_scalping" in owners for owners in scope.values())
    assert all("manual_operator" in owners for owners in scope.values())


def test_auto_apply_skips_stale_registry_symbol_and_applies_safe_subset(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    authority = _write_authority(authority_path)
    request_path = tmp_path / "request.json"
    result_path = tmp_path / "result.json"
    registry = _Registry(tmp_path / "registry.jsonl", conflicts={SYMBOL_A})
    captured = {}

    def fake_apply(path, **kwargs):
        captured["request"] = json.loads(Path(path).read_text(encoding="utf-8"))
        captured["kwargs"] = kwargs
        return {
            "schema": APPLY_RECEIPT_SCHEMA,
            "status": "applied",
            "runtime_effect": True,
            "active_date": TARGET_DATE.isoformat(),
            "apply_authority": "standing_exact_scope",
            "standing_authorization_id": authority["authorization_id"],
            "standing_authorization_sha256": authority[
                "artifact_content_sha256"
            ],
            "symbols": [SYMBOL_B],
        }

    result = run_auto_apply(
        observed_at=NOW,
        authority_path=authority_path,
        token_loader=lambda: "shared-token",
        process_scanner=lambda: [],
        snapshot_fetcher=lambda *_args: _snapshot(),
        registry=registry,
        request_path=request_path,
        result_path=result_path,
        apply_func=fake_apply,
    )

    assert result["status"] == "applied"
    assert result["applied_symbols"] == [SYMBOL_B]
    assert result["skipped_symbols"][SYMBOL_A]["reason"] == (
        "registry_or_broker_custody_conflict"
    )
    assert captured["request"]["symbols"].keys() == {SYMBOL_B}
    assert captured["request"]["generated_at_kst"] == (
        "2026-09-07T07:32:00+09:00"
    )
    assert captured["request"]["standing_authorization"] == {
        "schema": STANDING_APPLY_BINDING_SCHEMA,
        "authorization_id": authority["authorization_id"],
        "artifact_content_sha256": authority["artifact_content_sha256"],
        "active_date": TARGET_DATE.isoformat(),
        "runner": "src.trading.order.symbol_owner_policy_auto_apply",
    }
    assert captured["kwargs"]["standing_authority_path"] == authority_path.resolve()


def test_auto_apply_skips_unregistered_open_order_per_symbol(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    authority = _write_authority(authority_path)
    registry = _Registry(
        tmp_path / "registry.jsonl", open_order_conflicts={SYMBOL_A}
    )
    open_order = {
        "symbol": SYMBOL_A,
        "order_no": "1234567",
        "side": "매수",
        "quantity": 10,
        "filled_quantity": 0,
        "remaining_quantity": 10,
        "route": "KRX",
    }

    result = run_auto_apply(
        observed_at=NOW,
        authority_path=authority_path,
        token_loader=lambda: "shared-token",
        process_scanner=lambda: [],
        snapshot_fetcher=lambda *_args: _snapshot(open_orders=[open_order]),
        registry=registry,
        request_path=tmp_path / "request.json",
        result_path=tmp_path / "result.json",
        apply_func=lambda *_args, **_kwargs: {
            "schema": APPLY_RECEIPT_SCHEMA,
            "status": "applied",
            "runtime_effect": True,
            "active_date": TARGET_DATE.isoformat(),
            "apply_authority": "standing_exact_scope",
            "standing_authorization_id": authority["authorization_id"],
            "standing_authorization_sha256": authority[
                "artifact_content_sha256"
            ],
            "symbols": [SYMBOL_B],
        },
    )

    assert result["applied_symbols"] == [SYMBOL_B]
    assert result["skipped_symbols"][SYMBOL_A]["reason"] == (
        "unregistered_or_ambiguous_open_order"
    )


def test_auto_apply_skips_same_date_unresolved_owner_intent(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    authority = _write_authority(authority_path)
    registry = _Registry(tmp_path / "registry.jsonl", unresolved={SYMBOL_A})

    result = run_auto_apply(
        observed_at=NOW,
        authority_path=authority_path,
        token_loader=lambda: "shared-token",
        process_scanner=lambda: [],
        snapshot_fetcher=lambda *_args: _snapshot(),
        registry=registry,
        request_path=tmp_path / "request.json",
        result_path=tmp_path / "result.json",
        apply_func=lambda *_args, **_kwargs: {
            "schema": APPLY_RECEIPT_SCHEMA,
            "status": "applied",
            "runtime_effect": True,
            "active_date": TARGET_DATE.isoformat(),
            "apply_authority": "standing_exact_scope",
            "standing_authorization_id": authority["authorization_id"],
            "standing_authorization_sha256": authority[
                "artifact_content_sha256"
            ],
            "symbols": [SYMBOL_B],
        },
    )

    assert result["applied_symbols"] == [SYMBOL_B]
    assert result["skipped_symbols"][SYMBOL_A]["reason"] == (
        "unresolved_owner_intent"
    )


def test_auto_apply_fails_before_token_when_order_process_is_active(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    _write_authority(authority_path)

    with pytest.raises(SymbolOwnerPolicyAutoApplyError, match="not_quiescent"):
        run_auto_apply(
            observed_at=NOW,
            authority_path=authority_path,
            token_loader=lambda: pytest.fail("token must not be loaded"),
            process_scanner=lambda: [{"pid": 101, "command": "bot_main.py"}],
            registry=_Registry(tmp_path / "registry.jsonl"),
            result_path=tmp_path / "result.json",
        )


def test_auto_apply_rejects_discovery_snapshot_hash_before_apply(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    _write_authority(authority_path)
    snapshot = _snapshot()
    snapshot["snapshot_sha256"] = "0" * 64

    with pytest.raises(SymbolOwnerPolicyAutoApplyError):
        run_auto_apply(
            observed_at=NOW,
            authority_path=authority_path,
            token_loader=lambda: "shared-token",
            process_scanner=lambda: [],
            snapshot_fetcher=lambda *_args: snapshot,
            registry=_Registry(tmp_path / "registry.jsonl"),
            result_path=tmp_path / "result.json",
            apply_func=lambda *_args, **_kwargs: pytest.fail("must not apply"),
        )


def test_auto_apply_rejects_current_machine_scope_drift(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    _write_authority(authority_path, owners={SYMBOL_A: OWNERS[SYMBOL_A]})

    with pytest.raises(SymbolOwnerPolicyAutoApplyError, match="scope_drift"):
        run_auto_apply(
            observed_at=NOW,
            authority_path=authority_path,
            token_loader=lambda: pytest.fail("token must not be loaded"),
            process_scanner=lambda: [],
            registry=_Registry(tmp_path / "registry.jsonl"),
            result_path=tmp_path / "result.json",
        )


def test_standing_authority_rejects_content_tampering(tmp_path):
    authority_path = tmp_path / "authority.json"
    payload = _write_authority(authority_path)
    payload["preopen_window"]["end_kst"] = "08:50:00"
    authority_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SymbolOwnerStandingAuthorityError, match="hash_mismatch"):
        load_standing_authority(authority_path, observed_at=NOW)


def test_standing_authority_builder_rejects_a_different_apply_window():
    with pytest.raises(SymbolOwnerStandingAuthorityError, match="window_invalid"):
        build_standing_authority(
            authorization_id="test-standing-authority",
            operator_instruction="Apply exact-date coexistence unattended.",
            reviewed_at_kst="2026-09-04T15:20:00+09:00",
            effective_from="2026-09-07",
            expires_after="2026-12-31",
            broker_account_key="kiwoom-live-primary",
            preopen_start="07:33:00",
            preopen_end="07:54:00",
            symbols=OWNERS,
        )


def test_non_trading_day_result_has_verified_terminal_hash(
    tmp_path, monkeypatch
):
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(
        "src.trading.order.symbol_owner_policy_auto_apply."
        "get_krx_trading_day_status",
        lambda _target_date: (False, "krx_holiday"),
    )

    result = run_auto_apply(
        observed_at=NOW,
        authority_path=tmp_path / "must-not-be-read.json",
        token_loader=lambda: pytest.fail("token must not be loaded"),
        process_scanner=lambda: pytest.fail("processes must not be scanned"),
        result_path=result_path,
    )

    expected_hash = result.pop("result_content_sha256")
    assert expected_hash == hashlib.sha256(
        json.dumps(
            result,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert json.loads(result_path.read_text(encoding="utf-8"))[
        "result_content_sha256"
    ] == expected_hash


def test_standing_authority_opens_only_its_early_exact_date_window(
    tmp_path, monkeypatch
):
    authority_path = tmp_path / "authority.json"
    authority = _write_authority(authority_path)
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "schema": REQUEST_SCHEMA,
                "active_date": TARGET_DATE.isoformat(),
                "policy_id": "standing-policy-2026-09-07",
                "generated_at_kst": NOW.isoformat(),
                "broker_account_key": "kiwoom-live-primary",
                "standing_authorization": {
                    "schema": STANDING_APPLY_BINDING_SCHEMA,
                    "authorization_id": authority["authorization_id"],
                    "artifact_content_sha256": authority[
                        "artifact_content_sha256"
                    ],
                    "active_date": TARGET_DATE.isoformat(),
                    "runner": "src.trading.order.symbol_owner_policy_auto_apply",
                },
                "symbols": {
                    SYMBOL_A: {
                        "mode": "COEXIST_ENTRY_ENABLED",
                        "allowed_owners": OWNERS[SYMBOL_A],
                        "expected_broker_quantity": 0,
                        "expected_external_manual_remainder": 0,
                        "migrated_positions": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    policy_path = tmp_path / "policy.json"
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry.path)
    )
    monkeypatch.setenv("KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE", str(policy_path))
    snapshot = _snapshot()
    snapshot["inventory"] = {SYMBOL_A: 0}
    canonical = {
        key: snapshot[key]
        for key in (
            "verified_exchanges",
            "inventory",
            "open_orders",
            "migration_receipts",
        )
    }
    snapshot["snapshot_sha256"] = hashlib.sha256(
        json.dumps(
            canonical,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    result = apply_symbol_owner_policy(
        request_path,
        apply=True,
        confirmation=f"APPLY SAME SYMBOL OWNER POLICY {TARGET_DATE.isoformat()}",
        now=NOW,
        process_scanner=lambda: [],
        snapshot_fetcher=lambda *_args: snapshot,
        token_loader=lambda: "shared-token",
        registry=registry,
        receipt_dir=tmp_path / "receipts",
        owner_env_file=tmp_path / "owner.env",
        apply_lock_path=tmp_path / "apply.lock",
        output_policy_path=policy_path,
        standing_authority_path=authority_path,
    )

    assert result["status"] == "applied"
    assert result["apply_authority"] == "standing_exact_scope"
    assert result["standing_authorization_sha256"] == authority[
        "artifact_content_sha256"
    ]

    with pytest.raises(SymbolOwnerPolicyApplyError, match="outside_preopen_window"):
        apply_symbol_owner_policy(
            request_path,
            apply=True,
            confirmation=f"APPLY SAME SYMBOL OWNER POLICY {TARGET_DATE.isoformat()}",
            now=NOW,
            process_scanner=lambda: [],
            token_loader=lambda: "shared-token",
            registry=registry,
        )


def test_auto_apply_retry_validates_and_reuses_exact_completed_generation(
    tmp_path, monkeypatch, auto_scope
):
    authority_path = tmp_path / "authority.json"
    _write_authority(authority_path)
    registry = OrderOwnerRegistry(tmp_path / "registry.jsonl")
    request_path = tmp_path / "request.json"
    result_path = tmp_path / "result.json"
    policy_path = tmp_path / "policy.json"
    monkeypatch.setenv(
        "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH", str(registry.path)
    )

    def apply_in_tmp(path, **kwargs):
        return apply_symbol_owner_policy(
            path,
            receipt_dir=tmp_path / "receipts",
            owner_env_file=tmp_path / "owner.env",
            apply_lock_path=tmp_path / "apply.lock",
            output_policy_path=policy_path,
            **kwargs,
        )

    first = run_auto_apply(
        observed_at=NOW,
        authority_path=authority_path,
        token_loader=lambda: "shared-token",
        process_scanner=lambda: [],
        snapshot_fetcher=lambda *_args: _snapshot(),
        registry=registry,
        request_path=request_path,
        result_path=result_path,
        apply_func=apply_in_tmp,
    )
    second = run_auto_apply(
        observed_at=NOW.replace(minute=41),
        authority_path=authority_path,
        token_loader=lambda: pytest.fail("completed retry must not load token"),
        process_scanner=lambda: [],
        snapshot_fetcher=lambda *_args: pytest.fail(
            "completed retry must not query broker"
        ),
        registry=registry,
        request_path=request_path,
        result_path=result_path,
        apply_func=lambda *_args, **_kwargs: pytest.fail(
            "completed retry must not apply again"
        ),
    )

    assert first["status"] == "applied"
    assert second["status"] == "already_applied"
    assert second["idempotent_recheck_at_kst"].startswith("2026-09-07T07:41:00")
    assert json.loads(result_path.read_text(encoding="utf-8"))["status"] == "applied"
    assert "KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE" not in os.environ


def test_deployment_orders_auto_apply_before_all_order_services():
    after = "korstockscan-symbol-owner-policy-auto-apply.service"
    unit_paths = [
        "deploy/systemd/korstockscan-widget-signal-auto-trader.service",
        "deploy/systemd/korstockscan-samsung-morning-one-share.service",
        "deploy/systemd/korstockscan-samsung-one-share-preflight.service",
        "deploy/systemd/korstockscan-samsung-midday-one-share.service",
        "deploy/systemd/korstockscan-samsung-midday-one-share-preflight.service",
        "deploy/systemd/korstockscan-samsung-afternoon-one-share.service",
        "deploy/systemd/korstockscan-samsung-afternoon-one-share-preflight.service",
        "deploy/systemd/korstockscan-low-price-two-leg@.service",
        "deploy/systemd/korstockscan-low-price-two-leg-preflight@.service",
    ]
    for path in unit_paths:
        assert after in Path(path).read_text(encoding="utf-8")

    timer = Path(
        "deploy/systemd/korstockscan-symbol-owner-policy-auto-apply.timer"
    ).read_text(encoding="utf-8")
    wrapper = Path("deploy/run_symbol_owner_policy_auto_apply.sh").read_text(
        encoding="utf-8"
    )
    assert "07:32:00 Asia/Seoul" in timer
    assert "Persistent=false" in timer
    assert "trap on_exit EXIT" in wrapper
    assert "runuser --user ubuntu" in wrapper
    assert "systemctl stop" in wrapper
    assert "systemctl start" in wrapper
