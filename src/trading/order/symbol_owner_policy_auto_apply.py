"""Unattended, fail-closed PREOPEN same-symbol owner policy producer.

The runner consumes one reviewed standing-authority artifact, discovers the
current widget/episode symbol universe, and applies only symbols whose broker
quantity and open orders are already fully represented by the immutable owner
registry.  Unmigrated custody is never inferred; affected symbols retain the
legacy manual exclusion for that date.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.config.symbol_owner_policy import (
    BROKER_ACCOUNT_KEY_ENV,
    POLICY_FILE_ENV,
    resolve_symbol_owner_policy,
)
from src.trading.config.symbol_owner_standing_authority import (
    DEFAULT_STANDING_AUTHORITY_PATH,
    KST,
    STANDING_APPLY_BINDING_SCHEMA,
    load_standing_authority,
    standing_apply_window,
)
from src.trading.low_price_two_leg.profiles import profiles_for_target_date
from src.trading.order.owner_custody_registry import (
    DEFAULT_REGISTRY_PATH,
    REGISTRY_PATH_ENV,
    OrderOwnerRegistry,
    OwnerRegistryError,
)
from src.trading.order.symbol_owner_policy_apply import (
    APPLY_RECEIPT_SCHEMA,
    REQUEST_SCHEMA,
    SymbolOwnerPolicyApplyError,
    apply_symbol_owner_policy,
    collect_broker_snapshot,
    find_running_trading_processes,
    validate_broker_snapshot_contract,
)
from src.trading.widget_auto_trade.policy import STATIC_WIDGET_AUTO_TRADE_SYMBOLS
from src.utils.constants import DATA_DIR
from src.utils.market_day import get_krx_trading_day_status

AUTO_RESULT_SCHEMA = "symbol_owner_policy_auto_apply_result_v1"
DEFAULT_AUTO_DIR = DATA_DIR / "runtime" / "symbol_owner_policy" / "auto_apply"
OFFICIAL_KIWOOM_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit": "234560d213acd8871ae344b5481aecd2f30287fa",
    "inspected_paths": [
        "kiwoom/core/auth.py",
        "kiwoom/core/token_store.py",
        "kiwoom/_data/kiwoom_api_spec.json",
    ],
    "retrieved_at_kst": "2026-09-04T15:15:00+09:00",
}


class SymbolOwnerPolicyAutoApplyError(RuntimeError):
    """Automatic apply could not satisfy an immutable safety precondition."""


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def expected_machine_symbol_owners(target_date) -> dict[str, list[str]]:
    episode_symbols = {
        profile.policy.symbol
        for profile in profiles_for_target_date(target_date).values()
    }
    # The three Samsung time-window machines are episode owners even though
    # they do not live in the lower-price profile catalog.
    episode_symbols.add("005930")
    widget_symbols = set(STATIC_WIDGET_AUTO_TRADE_SYMBOLS)
    owners: dict[str, list[str]] = {}
    for symbol in sorted(episode_symbols | widget_symbols):
        values = {"main_scalping", "manual_operator"}
        if symbol in episode_symbols:
            values.add("episode")
        if symbol in widget_symbols:
            values.add("widget_auto_trade")
        owners[symbol] = sorted(values)
    return owners


def _validate_runtime_scope(
    authority: dict[str, Any], *, target_date
) -> dict[str, list[str]]:
    expected = expected_machine_symbol_owners(target_date)
    configured = authority.get("symbols")
    if not isinstance(configured, dict) or set(configured) != set(expected):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_machine_scope_drift"
        )
    for symbol, owners in expected.items():
        entry = configured.get(symbol)
        if (
            not isinstance(entry, dict)
            or sorted(entry.get("allowed_owners") or []) != owners
            or not manual_control_operator_exclusion_source(symbol)
        ):
            raise SymbolOwnerPolicyAutoApplyError(
                f"symbol_owner_auto_apply_owner_or_manual_scope_mismatch:{symbol}"
            )
    return expected


def _result_path(target_date) -> Path:
    return DEFAULT_AUTO_DIR / f"symbol_owner_policy_auto_apply_{target_date.isoformat()}.json"


def _request_path(target_date) -> Path:
    return (
        DATA_DIR
        / "runtime"
        / "symbol_owner_policy"
        / "requests"
        / f"symbol_owner_policy_apply_{target_date.isoformat()}.json"
    )


def _load_idempotent_result(
    path: Path,
    *,
    authority: dict[str, Any],
    expected_scope: dict[str, list[str]],
    target_date,
    registry: OrderOwnerRegistry,
    observed_at: datetime,
) -> dict[str, Any] | None:
    """Return a verified completed result; reject a forged or stale success."""

    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_result_unreadable"
        ) from exc
    if not isinstance(payload, dict) or payload.get("status") != "applied":
        return None
    expected_hash = str(payload.get("result_content_sha256") or "")
    canonical = {
        key: value
        for key, value in payload.items()
        if key != "result_content_sha256"
    }
    applied_symbols = set(payload.get("applied_symbols") or [])
    skipped_raw = payload.get("skipped_symbols")
    skipped_symbols = set(skipped_raw) if isinstance(skipped_raw, dict) else set()
    apply_receipt = payload.get("apply_receipt")
    request_file = Path(str(payload.get("request_path") or ""))
    owner_env_file = Path(
        str((apply_receipt or {}).get("owner_env_file") or "")
    )
    if (
        payload.get("schema") != AUTO_RESULT_SCHEMA
        or expected_hash != _canonical_sha256(canonical)
        or payload.get("target_date") != target_date.isoformat()
        or payload.get("standing_authorization_id")
        != authority["authorization_id"]
        or payload.get("standing_authorization_sha256")
        != authority["artifact_content_sha256"]
        or not isinstance(skipped_raw, dict)
        or applied_symbols | skipped_symbols != set(expected_scope)
        or applied_symbols & skipped_symbols
        or not applied_symbols
        or payload.get("requested_symbol_count") != len(expected_scope)
        or payload.get("applied_symbol_count") != len(applied_symbols)
        or payload.get("skipped_symbol_count") != len(skipped_symbols)
        or not isinstance(apply_receipt, dict)
        or apply_receipt.get("status") != "applied"
        or apply_receipt.get("runtime_effect") is not True
        or apply_receipt.get("apply_authority") != "standing_exact_scope"
        or set(apply_receipt.get("symbols") or []) != applied_symbols
        or apply_receipt.get("active_date") != target_date.isoformat()
        or apply_receipt.get("standing_authorization_id")
        != authority["authorization_id"]
        or apply_receipt.get("standing_authorization_sha256")
        != authority["artifact_content_sha256"]
        or Path(str(apply_receipt.get("registry_path") or ""))
        != registry.path
        or not request_file.is_absolute()
        or not request_file.is_file()
        or not owner_env_file.is_absolute()
        or not owner_env_file.is_file()
    ):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_result_contract_invalid"
        )
    try:
        request_bytes = request_file.read_bytes()
        request_payload = json.loads(request_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_request_unreadable"
        ) from exc
    if (
        not isinstance(request_payload, dict)
        or _canonical_sha256(request_payload)
        != payload.get("request_content_sha256")
        or hashlib.sha256(request_bytes).hexdigest()
        != apply_receipt.get("request_sha256")
        or set((request_payload.get("symbols") or {}).keys()) != applied_symbols
    ):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_request_mismatch"
        )
    policy_file = Path(str(apply_receipt.get("policy_path") or ""))
    if not policy_file.is_absolute() or not policy_file.is_file():
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_policy_missing"
        )
    try:
        policy_payload = json.loads(policy_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_policy_unreadable"
        ) from exc
    if (
        not isinstance(policy_payload, dict)
        or set((policy_payload.get("symbols") or {}).keys()) != applied_symbols
        or apply_receipt.get("policy_hash") != policy_payload.get("policy_hash")
        or set((apply_receipt.get("activation_event_hashes") or {}).keys())
        != applied_symbols
    ):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_policy_scope_mismatch"
        )
    expected_env_lines = {
        f"{BROKER_ACCOUNT_KEY_ENV}="
        f"{shlex.quote(str(authority['broker_account_key']))}",
        f"{REGISTRY_PATH_ENV}={shlex.quote(str(registry.path))}",
        f"{POLICY_FILE_ENV}={shlex.quote(str(policy_file))}",
    }
    try:
        actual_env_lines = {
            line.strip()
            for line in owner_env_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError as exc:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_owner_env_unreadable"
        ) from exc
    if actual_env_lines != expected_env_lines:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_existing_owner_env_mismatch"
        )
    previous_policy_file = os.environ.get(POLICY_FILE_ENV)
    os.environ[POLICY_FILE_ENV] = str(policy_file)
    try:
        for symbol in sorted(applied_symbols):
            decision = resolve_symbol_owner_policy(symbol, target_date=target_date)
            if (
                not decision.coexistence_enabled
                or not registry.decision_activation_matches(decision)
            ):
                raise SymbolOwnerPolicyAutoApplyError(
                    "symbol_owner_auto_apply_existing_activation_invalid:"
                    f"{symbol}"
                )
    finally:
        if previous_policy_file is None:
            os.environ.pop(POLICY_FILE_ENV, None)
        else:
            os.environ[POLICY_FILE_ENV] = previous_policy_file
    checked = {
        **payload,
        "status": "already_applied",
        "idempotent_recheck_at_kst": observed_at.isoformat(),
    }
    checked["result_content_sha256"] = _canonical_sha256(
        {
            key: value
            for key, value in checked.items()
            if key != "result_content_sha256"
        }
    )
    return checked


def run_auto_apply(
    *,
    observed_at: datetime | None = None,
    authority_path: Path = DEFAULT_STANDING_AUTHORITY_PATH,
    token_loader: Callable[[], str | None] | None = None,
    process_scanner: Callable[[], list[dict[str, Any]]] = find_running_trading_processes,
    snapshot_fetcher: Callable[
        [str, set[str], tuple[dict[str, Any], ...]], dict[str, Any]
    ] = collect_broker_snapshot,
    registry: OrderOwnerRegistry | None = None,
    request_path: Path | None = None,
    result_path: Path | None = None,
    apply_func: Callable[..., dict[str, Any]] = apply_symbol_owner_policy,
) -> dict[str, Any]:
    """Generate and apply today's safe subset under standing authority."""

    now = observed_at or datetime.now(tz=KST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=KST)
    now = now.astimezone(KST)
    target_date = now.date()
    output_result_path = Path(result_path or _result_path(target_date)).resolve()
    is_trading_day, trading_day_reason = get_krx_trading_day_status(target_date)
    if not is_trading_day:
        result = {
            "schema": AUTO_RESULT_SCHEMA,
            "status": "skipped_non_trading_day",
            "runtime_effect": False,
            "target_date": target_date.isoformat(),
            "reason": trading_day_reason,
            "observed_at_kst": now.isoformat(),
        }
        result["result_content_sha256"] = _canonical_sha256(result)
        _atomic_json(output_result_path, result)
        return result

    authority = load_standing_authority(Path(authority_path), observed_at=now)
    start, end = standing_apply_window(authority)
    local_time = now.time().replace(tzinfo=None)
    if not start <= local_time <= end:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_outside_standing_window"
        )
    expected_scope = _validate_runtime_scope(authority, target_date=target_date)
    running = process_scanner()
    if running:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_trading_process_not_quiescent:"
            + ",".join(str(row.get("pid")) for row in running)
        )

    os.environ[BROKER_ACCOUNT_KEY_ENV] = str(authority["broker_account_key"])
    os.environ.setdefault(REGISTRY_PATH_ENV, str(DEFAULT_REGISTRY_PATH))
    target_registry = registry or OrderOwnerRegistry()
    completed = _load_idempotent_result(
        output_result_path,
        authority=authority,
        expected_scope=expected_scope,
        target_date=target_date,
        registry=target_registry,
        observed_at=now,
    )
    if completed is not None:
        return completed
    if token_loader is None:
        from src.utils import kiwoom_utils

        token_loader = lambda: kiwoom_utils.get_kiwoom_token(  # noqa: E731
            require_issued_today=True
        )
    token = token_loader()
    if not token:
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_shared_token_unavailable"
        )

    discovery = snapshot_fetcher(token, set(expected_scope), tuple())
    try:
        validate_broker_snapshot_contract(
            discovery,
            symbols=set(expected_scope),
            migration_receipts_allowed=False,
        )
    except SymbolOwnerPolicyApplyError as exc:
        raise SymbolOwnerPolicyAutoApplyError(
            f"symbol_owner_auto_apply_discovery_snapshot_invalid:{exc}"
        ) from exc
    inventory = discovery.get("inventory")
    open_orders = discovery.get("open_orders")
    if not isinstance(inventory, dict) or not isinstance(open_orders, list):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_discovery_snapshot_invalid"
        )
    eligible: dict[str, dict[str, Any]] = {}
    skipped: dict[str, dict[str, Any]] = {}
    for symbol, owners in expected_scope.items():
        broker_quantity = int(inventory.get(symbol, 0) or 0)
        broker_orders = {
            str(row.get("order_no") or "").strip()
            for row in open_orders
            if isinstance(row, dict) and row.get("symbol") == symbol
        }
        try:
            reconciliation = target_registry.reconcile_symbol_quantity(
                symbol=symbol,
                broker_quantity=broker_quantity,
            )
            unresolved = target_registry.unresolved_intent_summary(
                symbol=symbol,
                active_date=target_date,
            )
        except OwnerRegistryError as exc:
            skipped[symbol] = {
                "reason": "registry_or_broker_custody_conflict",
                "error_type": type(exc).__name__,
                "broker_quantity": broker_quantity,
                "broker_open_order_count": len(broker_orders),
                "legacy_manual_exclusion_retained": True,
            }
            continue
        if int(unresolved["unresolved_intent_count"]) != 0:
            skipped[symbol] = {
                "reason": "unresolved_owner_intent",
                "unresolved_intent_count": int(
                    unresolved["unresolved_intent_count"]
                ),
                "states": unresolved["states"],
                "sides": unresolved["sides"],
                "legacy_manual_exclusion_retained": True,
            }
            continue
        if int(reconciliation["external_manual_remainder"]) != 0:
            skipped[symbol] = {
                "reason": "unmigrated_broker_custody",
                "broker_quantity": broker_quantity,
                "registered_owner_quantity": int(
                    reconciliation["registered_owner_quantity"]
                ),
                "external_manual_remainder": int(
                    reconciliation["external_manual_remainder"]
                ),
                "legacy_manual_exclusion_retained": True,
            }
            continue
        try:
            target_registry.migration_receipt(
                symbol=symbol,
                broker_quantity=broker_quantity,
                active_date=target_date,
                verified_exchanges={"KRX", "NXT"},
                broker_open_order_nos=broker_orders,
                broker_snapshot_sha256=str(discovery.get("snapshot_sha256") or ""),
            )
        except OwnerRegistryError as exc:
            skipped[symbol] = {
                "reason": "unregistered_or_ambiguous_open_order",
                "error_type": type(exc).__name__,
                "broker_open_order_count": len(broker_orders),
                "legacy_manual_exclusion_retained": True,
            }
            continue
        eligible[symbol] = {
            "mode": authority["symbols"][symbol]["mode"],
            "allowed_owners": owners,
            "expected_broker_quantity": broker_quantity,
            "expected_external_manual_remainder": 0,
            "migrated_positions": [],
        }

    if len(eligible) < int(authority.get("minimum_safe_symbol_count") or 0):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_no_reconciled_symbols"
        )
    authority_hash = str(authority["artifact_content_sha256"])
    deterministic_generated_at = datetime.combine(
        target_date,
        start,
        tzinfo=KST,
    ).isoformat()
    request_payload = {
        "schema": REQUEST_SCHEMA,
        "active_date": target_date.isoformat(),
        "policy_id": (
            f"same_symbol_owner_auto:{target_date.isoformat()}:"
            f"{authority_hash[:16]}"
        ),
        "generated_at_kst": deterministic_generated_at,
        "broker_account_key": authority["broker_account_key"],
        "standing_authorization": {
            "schema": STANDING_APPLY_BINDING_SCHEMA,
            "authorization_id": authority["authorization_id"],
            "artifact_content_sha256": authority_hash,
            "active_date": target_date.isoformat(),
            "runner": "src.trading.order.symbol_owner_policy_auto_apply",
        },
        "symbols": dict(sorted(eligible.items())),
    }
    output_request_path = Path(request_path or _request_path(target_date)).resolve()
    _atomic_json(output_request_path, request_payload)
    apply_result = apply_func(
        output_request_path,
        apply=True,
        confirmation=f"APPLY SAME SYMBOL OWNER POLICY {target_date.isoformat()}",
        now=now,
        process_scanner=process_scanner,
        snapshot_fetcher=snapshot_fetcher,
        token_loader=lambda: token,
        registry=target_registry,
        standing_authority_path=Path(authority_path).resolve(),
    )
    if (
        not isinstance(apply_result, dict)
        or apply_result.get("schema") != APPLY_RECEIPT_SCHEMA
        or apply_result.get("status") != "applied"
        or apply_result.get("runtime_effect") is not True
        or apply_result.get("active_date") != target_date.isoformat()
        or apply_result.get("apply_authority") != "standing_exact_scope"
        or apply_result.get("standing_authorization_id")
        != authority["authorization_id"]
        or apply_result.get("standing_authorization_sha256") != authority_hash
        or set(apply_result.get("symbols") or []) != set(eligible)
    ):
        raise SymbolOwnerPolicyAutoApplyError(
            "symbol_owner_auto_apply_receipt_contract_invalid"
        )
    result = {
        "schema": AUTO_RESULT_SCHEMA,
        "status": "applied",
        "runtime_effect": True,
        "target_date": target_date.isoformat(),
        "observed_at_kst": now.isoformat(),
        "standing_authorization_id": authority["authorization_id"],
        "standing_authorization_sha256": authority_hash,
        "scope_contract": authority["scope_contract"],
        "requested_symbol_count": len(expected_scope),
        "applied_symbol_count": len(eligible),
        "skipped_symbol_count": len(skipped),
        "applied_symbols": sorted(eligible),
        "skipped_symbols": skipped,
        "request_path": str(output_request_path),
        "request_content_sha256": _canonical_sha256(request_payload),
        "broker_discovery_snapshot_sha256": discovery.get("snapshot_sha256"),
        "apply_receipt": apply_result,
        "official_kiwoom_reference": OFFICIAL_KIWOOM_REFERENCE,
    }
    result["result_content_sha256"] = _canonical_sha256(result)
    _atomic_json(output_result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--standing-authority",
        type=Path,
        default=DEFAULT_STANDING_AUTHORITY_PATH,
    )
    parser.add_argument("--result-path", type=Path, default=None)
    args = parser.parse_args(argv)
    now = datetime.now(tz=KST)
    output_path = Path(args.result_path or _result_path(now.date())).resolve()
    try:
        result = run_auto_apply(
            observed_at=now,
            authority_path=args.standing_authority,
            result_path=output_path,
        )
    except Exception as exc:
        result = {
            "schema": AUTO_RESULT_SCHEMA,
            "status": "blocked",
            "runtime_effect": False,
            "target_date": now.date().isoformat(),
            "observed_at_kst": now.isoformat(),
            "error_type": type(exc).__name__,
            "reason": str(exc),
            "legacy_manual_exclusion_retained": True,
            "official_kiwoom_reference": OFFICIAL_KIWOOM_REFERENCE,
        }
        result["result_content_sha256"] = _canonical_sha256(result)
        _atomic_json(output_path, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
