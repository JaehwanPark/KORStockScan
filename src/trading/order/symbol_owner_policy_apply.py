"""Fail-closed PREOPEN producer for exact-date same-symbol owner authority.

Dry-run is the default.  Live publication requires an exact confirmation,
today's KST date, quiescent trading processes, two identical read-only broker
snapshots, complete KRX/NXT inventory coverage, exact open-order registry
reconciliation, and an immutable per-symbol registry activation event.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pwd
import re
import shlex
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from src.trading.config.symbol_owner_policy import (
    BROKER_ACCOUNT_KEY_ENV,
    COEXIST_ENTRY_ENABLED,
    COEXIST_EXIT_ONLY,
    DEFAULT_POLICY_DIR,
    POLICY_FILE_ENV,
    build_symbol_owner_policy_payload,
    normalize_symbol,
    symbol_owner_entry_authority_hash,
)
from src.trading.order.owner_custody_registry import (
    DEFAULT_REGISTRY_PATH,
    REGISTRY_PATH_ENV,
    OrderOwnerRegistry,
    OwnerOrderContext,
    broker_account_key,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
REQUEST_SCHEMA = "symbol_owner_policy_apply_request_v1"
APPLY_RECEIPT_SCHEMA = "symbol_owner_policy_apply_receipt_v1"
OWNER_ENV_FILE = DATA_DIR / "runtime" / "symbol_owner_policy" / "owner_custody.env"
DEFAULT_RECEIPT_DIR = DATA_DIR / "runtime" / "symbol_owner_policy" / "receipts"
DEFAULT_APPLY_LOCK = DATA_DIR / "runtime" / "symbol_owner_policy" / "apply.lock"
VALID_APPLY_MODES = frozenset({COEXIST_ENTRY_ENABLED, COEXIST_EXIT_ONLY})
PREOPEN_APPLY_START = time(8, 35)
PREOPEN_APPLY_END = time(8, 50)
VALID_OWNERS = frozenset(
    {"main_scalping", "widget_auto_trade", "episode", "manual_operator"}
)
TRADING_PROCESS_MARKERS = (
    "src/run_bot.sh",
    "run_bot.sh",
    "bot_main.py",
    "src.trading.widget_auto_trade.service",
    "src.trading.samsung_morning_one_share",
    "src.trading.samsung_midday_one_share",
    "src.trading.samsung_afternoon_one_share",
    "src.trading.low_price_two_leg",
)


class SymbolOwnerPolicyApplyError(RuntimeError):
    """A PREOPEN authority precondition failed closed."""


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _canonical_route(stex_tp: object, sor_yn: object = "") -> str:
    if str(sor_yn or "").strip().upper() == "Y":
        return "SOR"
    raw = str(stex_tp or "").strip().upper()
    return {"1": "KRX", "2": "NXT"}.get(raw, raw)


def _atomic_write(path: Path, content: str, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
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


def _load_request(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolOwnerPolicyApplyError(
            f"symbol_owner_apply_request_unreadable:{type(exc).__name__}"
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema") != REQUEST_SCHEMA:
        raise SymbolOwnerPolicyApplyError("symbol_owner_apply_request_schema_invalid")
    return payload, hashlib.sha256(raw).hexdigest()


def _validate_migration_row(row: dict[str, Any]) -> None:
    context = OwnerOrderContext(
        owner_type=str(row.get("owner_type") or "").strip().lower(),
        owner_id=str(row.get("owner_id") or "").strip(),
        position_id=str(row.get("position_id") or "").strip(),
        client_intent_id=str(row.get("client_intent_id") or "").strip(),
    )
    context.validate()
    try:
        quantity = int(row.get("quantity"))
        average_price = int(row.get("average_price"))
    except (TypeError, ValueError) as exc:
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_migration_quantity_invalid"
        ) from exc
    order_no = str(row.get("broker_order_no") or "").strip()
    evidence_hash = str(row.get("evidence_sha256") or "").strip().lower()
    route = str(row.get("route") or "").strip().upper()
    try:
        date.fromisoformat(str(row.get("order_date") or ""))
    except ValueError as exc:
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_migration_order_date_invalid"
        ) from exc
    if (
        min(quantity, average_price) <= 0
        or route not in {"KRX", "NXT", "SOR"}
        or not (order_no.isdigit() and len(order_no) == 7)
        or len(evidence_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in evidence_hash)
    ):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_migration_contract_invalid"
        )


def _validate_request(
    payload: dict[str, Any], *, now: datetime
) -> tuple[date, str, str, str, dict[str, dict[str, Any]]]:
    try:
        active_date = date.fromisoformat(str(payload.get("active_date") or ""))
    except ValueError as exc:
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_active_date_invalid"
        ) from exc
    policy_id = str(payload.get("policy_id") or "").strip()
    account_key = str(payload.get("broker_account_key") or "").strip()
    generated_at_text = str(payload.get("generated_at_kst") or "").strip()
    try:
        generated_at = datetime.fromisoformat(generated_at_text)
    except ValueError as exc:
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_generated_at_invalid"
        ) from exc
    normalized_now = now.astimezone(KST)
    normalized_generated_at = (
        generated_at.astimezone(KST) if generated_at.tzinfo is not None else None
    )
    if (
        active_date != now.astimezone(KST).date()
        or not policy_id
        or len(policy_id) > 240
        or any(ch in policy_id for ch in "\r\n\t")
        or generated_at.tzinfo is None
        or generated_at.astimezone(KST).date() != active_date
        or normalized_generated_at is None
        or normalized_generated_at > normalized_now
    ):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_exact_date_or_policy_id_invalid"
        )
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", account_key or "") or (
        account_key.lower() == "default"
    ):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_explicit_account_key_invalid"
        )
    symbols = payload.get("symbols")
    if not isinstance(symbols, dict) or not symbols:
        raise SymbolOwnerPolicyApplyError("symbol_owner_apply_symbols_invalid")
    normalized: dict[str, dict[str, Any]] = {}
    migration_order_nos: set[tuple[str, str]] = set()
    migration_intent_ids: set[str] = set()
    for raw_symbol, raw_entry in symbols.items():
        symbol = normalize_symbol(raw_symbol)
        if (
            str(raw_symbol) != symbol
            or not (symbol.isdigit() and len(symbol) == 6)
            or symbol in normalized
            or not isinstance(raw_entry, dict)
        ):
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_symbol_or_entry_invalid"
            )
        mode = str(raw_entry.get("mode") or "").strip().upper()
        owners = sorted(
            {
                str(value or "").strip().lower()
                for value in raw_entry.get("allowed_owners", [])
            }
        )
        if (
            mode not in VALID_APPLY_MODES
            or "main_scalping" not in owners
            or not {"widget_auto_trade", "episode"}.intersection(owners)
            or any(owner not in VALID_OWNERS for owner in owners)
        ):
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_mode_or_owner_set_invalid"
            )
        try:
            broker_quantity = int(raw_entry.get("expected_broker_quantity"))
            external_remainder = int(
                raw_entry.get("expected_external_manual_remainder")
            )
        except (TypeError, ValueError) as exc:
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_expected_quantity_invalid"
            ) from exc
        migrations = raw_entry.get("migrated_positions", [])
        if (
            min(broker_quantity, external_remainder) < 0
            or not isinstance(migrations, list)
            or any(not isinstance(row, dict) for row in migrations)
        ):
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_expected_quantity_or_migration_invalid"
            )
        for migration in migrations:
            _validate_migration_row(migration)
            if str(migration.get("owner_type") or "").strip().lower() not in owners:
                raise SymbolOwnerPolicyApplyError(
                    "symbol_owner_apply_migration_owner_not_allowed"
                )
            if date.fromisoformat(str(migration["order_date"])) > active_date:
                raise SymbolOwnerPolicyApplyError(
                    "symbol_owner_apply_migration_order_date_after_active_date"
                )
            order_identity = (
                str(migration.get("order_date") or "").strip(),
                str(migration.get("broker_order_no") or "").strip(),
            )
            intent_id = str(migration.get("client_intent_id") or "").strip()
            if (
                order_identity in migration_order_nos
                or intent_id in migration_intent_ids
            ):
                raise SymbolOwnerPolicyApplyError(
                    "symbol_owner_apply_duplicate_migration_identity"
                )
            migration_order_nos.add(order_identity)
            migration_intent_ids.add(intent_id)
        normalized[symbol] = {
            "mode": mode,
            "allowed_owners": owners,
            "expected_broker_quantity": broker_quantity,
            "expected_external_manual_remainder": external_remainder,
            "migrated_positions": migrations,
        }
    return (
        active_date,
        policy_id,
        account_key,
        normalized_generated_at.isoformat(),
        normalized,
    )


def find_running_trading_processes() -> list[dict[str, Any]]:
    """Inventory order-capable processes from procfs without shell matching."""

    rows: list[dict[str, Any]] = []
    current_pid = os.getpid()
    for proc_dir in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(proc_dir.name)
            if pid == current_pid:
                continue
            command = (proc_dir / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (OSError, ValueError):
            continue
        if any(marker in command for marker in TRADING_PROCESS_MARKERS):
            rows.append({"pid": pid, "command": command.strip()[:500]})
    return sorted(rows, key=lambda row: row["pid"])


def collect_broker_snapshot(
    token: str,
    symbols: set[str],
    migration_rows: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Collect one canonical read-only all-venue inventory/open-order snapshot."""

    from src.engine import kiwoom_orders
    from src.utils import kiwoom_utils

    inventory, exchanges = kiwoom_orders.get_my_inventory(token)
    if set(exchanges) != {"KRX", "NXT"} or kiwoom_orders.get_last_inventory_errors():
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_inventory_all_venues_incomplete"
        )
    open_orders, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta(
        token, all_stk_tp="0", trde_tp="0", stex_tp="0"
    )
    if not (
        meta.get("request_succeeded") is True
        and meta.get("normalization_contract_complete") is True
    ):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_open_order_snapshot_incomplete"
        )
    inventory_by_symbol = {
        normalize_symbol(row.get("code")): int(row.get("qty") or 0)
        for row in inventory
        if isinstance(row, dict) and normalize_symbol(row.get("code")) in symbols
    }
    selected_orders = [
        {
            "symbol": normalize_symbol(row.get("code")),
            "order_no": str(row.get("ord_no") or "").strip(),
            "side": str(row.get("side") or "").strip(),
            "quantity": int(row.get("qty") or 0),
            "filled_quantity": int(row.get("filled_qty") or 0),
            "remaining_quantity": int(row.get("remaining_qty") or 0),
            "route": _canonical_route(row.get("stex_tp"), row.get("sor_yn")),
        }
        for row in open_orders
        if isinstance(row, dict)
        and normalize_symbol(row.get("code")) in symbols
        and int(row.get("remaining_qty") or 0) > 0
    ]
    if any(
        not (row["order_no"].isdigit() and len(row["order_no"]) == 7)
        for row in selected_orders
    ):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_open_order_identity_invalid"
        )
    migration_receipts: list[dict[str, Any]] = []
    receipt_groups = sorted(
        {
            (
                normalize_symbol(row.get("symbol")),
                str(row.get("order_date") or "").strip(),
            )
            for row in migration_rows
        }
    )
    for symbol, order_date in receipt_groups:
        rows, receipt_meta = kiwoom_utils.get_order_reference_snapshot_kt00007_with_meta(
            token,
            ord_dt=order_date.replace("-", ""),
            qry_tp="4",
            stk_bond_tp="1",
            sell_tp="2",
            stk_cd=symbol,
            dmst_stex_tp="%",
        )
        if not (
            receipt_meta.get("request_succeeded") is True
            and receipt_meta.get("normalization_contract_complete") is True
        ):
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_migration_receipt_snapshot_incomplete"
            )
        requested_order_nos = {
            str(row.get("broker_order_no") or "").strip()
            for row in migration_rows
            if normalize_symbol(row.get("symbol")) == symbol
            and str(row.get("order_date") or "").strip() == order_date
        }
        for order_no in sorted(requested_order_nos):
            matches = [
                row
                for row in rows
                if str(row.get("ord_no") or "").strip() == order_no
                and normalize_symbol(row.get("code")) == symbol
                and str(row.get("side") or "").strip() == "매수"
            ]
            if len(matches) != 1:
                raise SymbolOwnerPolicyApplyError(
                    "symbol_owner_apply_migration_receipt_missing_or_ambiguous:"
                    f"{symbol}:{order_no}"
                )
            match = matches[0]
            canonical_receipt = {
                "symbol": symbol,
                "order_date": order_date,
                "order_no": order_no,
                "side": "매수",
                "quantity": int(match.get("qty") or 0),
                "filled_quantity": int(match.get("filled_qty") or 0),
                "remaining_quantity": int(match.get("remaining_qty") or 0),
                "execution_price": int(match.get("execution_price") or 0),
                "route": _canonical_route(
                    match.get("stex_tp"), match.get("sor_yn")
                ),
            }
            migration_receipts.append(
                {
                    **canonical_receipt,
                    "evidence_sha256": _sha256_payload(canonical_receipt),
                }
            )
    canonical = {
        "verified_exchanges": ["KRX", "NXT"],
        "inventory": {
            symbol: int(inventory_by_symbol.get(symbol, 0))
            for symbol in sorted(symbols)
        },
        "open_orders": sorted(
            selected_orders,
            key=lambda row: (row["symbol"], row["order_no"]),
        ),
        "migration_receipts": sorted(
            migration_receipts,
            key=lambda row: (row["symbol"], row["order_date"], row["order_no"]),
        ),
    }
    return {**canonical, "snapshot_sha256": _sha256_payload(canonical)}


def _validate_broker_snapshot(
    snapshot: dict[str, Any], entries: dict[str, dict[str, Any]]
) -> None:
    if not isinstance(snapshot, dict):
        raise SymbolOwnerPolicyApplyError("symbol_owner_apply_snapshot_invalid")
    canonical = {
        "verified_exchanges": snapshot.get("verified_exchanges"),
        "inventory": snapshot.get("inventory"),
        "open_orders": snapshot.get("open_orders"),
        "migration_receipts": snapshot.get("migration_receipts"),
    }
    if (
        canonical["verified_exchanges"] != ["KRX", "NXT"]
        or not isinstance(canonical["inventory"], dict)
        or not isinstance(canonical["open_orders"], list)
        or not isinstance(canonical["migration_receipts"], list)
        or snapshot.get("snapshot_sha256") != _sha256_payload(canonical)
    ):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_snapshot_contract_or_hash_invalid"
        )
    for symbol, entry in entries.items():
        actual_quantity = int(snapshot["inventory"].get(symbol, 0))
        if actual_quantity != entry["expected_broker_quantity"]:
            raise SymbolOwnerPolicyApplyError(
                f"symbol_owner_apply_broker_quantity_mismatch:{symbol}"
            )
        for migration in entry["migrated_positions"]:
            matches = [
                receipt
                for receipt in canonical["migration_receipts"]
                if receipt.get("symbol") == symbol
                and receipt.get("order_date") == migration.get("order_date")
                and receipt.get("order_no") == migration.get("broker_order_no")
            ]
            if len(matches) != 1:
                raise SymbolOwnerPolicyApplyError(
                    f"symbol_owner_apply_migration_receipt_not_verified:{symbol}"
                )
            receipt = matches[0]
            if (
                receipt.get("side") != "매수"
                or int(receipt.get("remaining_quantity") or 0) != 0
                or int(receipt.get("quantity") or 0)
                != int(migration.get("quantity"))
                or int(receipt.get("filled_quantity") or 0)
                != int(migration.get("quantity"))
                or int(receipt.get("execution_price") or 0)
                != int(migration.get("average_price"))
                or receipt.get("route")
                != str(migration.get("route") or "").strip().upper()
                or receipt.get("evidence_sha256")
                != str(migration.get("evidence_sha256") or "").strip().lower()
            ):
                raise SymbolOwnerPolicyApplyError(
                    f"symbol_owner_apply_migration_receipt_mismatch:{symbol}"
                )


def _migration_context(row: dict[str, Any]) -> OwnerOrderContext:
    context = OwnerOrderContext(
        owner_type=str(row.get("owner_type") or "").strip().lower(),
        owner_id=str(row.get("owner_id") or "").strip(),
        position_id=str(row.get("position_id") or "").strip(),
        client_intent_id=str(row.get("client_intent_id") or "").strip(),
    )
    context.validate()
    return context


def _register_requested_migrations(
    registry: OrderOwnerRegistry,
    *,
    active_date: date,
    policy_id: str,
    entries: dict[str, dict[str, Any]],
) -> None:
    for symbol, entry in entries.items():
        if registry.policy_activation_record(
            active_date=active_date,
            policy_id=policy_id,
            symbol=symbol,
        ) is not None:
            continue
        for row in entry["migrated_positions"]:
            registry.register_migrated_position(
                context=_migration_context(row),
                symbol=symbol,
                quantity=int(row.get("quantity")),
                average_price=int(row.get("average_price")),
                route=str(row.get("route") or "").strip().upper(),
                order_date=str(row.get("order_date") or "").strip(),
                broker_order_no=str(row.get("broker_order_no") or "").strip(),
                evidence_sha256=str(row.get("evidence_sha256") or "").strip(),
            )


def _build_activated_entries(
    registry: OrderOwnerRegistry,
    *,
    active_date: date,
    policy_id: str,
    request_sha256: str,
    snapshot: dict[str, Any],
    entries: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    activated: dict[str, dict[str, Any]] = {}
    for symbol, requested in entries.items():
        existing = registry.policy_activation_record(
            active_date=active_date,
            policy_id=policy_id,
            symbol=symbol,
        )
        if existing is not None:
            receipt = existing.get("migration_receipt")
            if not isinstance(receipt, dict):
                raise SymbolOwnerPolicyApplyError(
                    f"symbol_owner_apply_activation_resume_receipt_missing:{symbol}"
                )
            entry = {
                "mode": requested["mode"],
                "allowed_owners": requested["allowed_owners"],
                "migration_completed": True,
                "rollback_mode": COEXIST_EXIT_ONLY,
                "migration_receipt": receipt,
                "apply_request_sha256": request_sha256,
            }
            entry_hash = symbol_owner_entry_authority_hash(
                active_date=active_date,
                policy_id=policy_id,
                symbol=symbol,
                entry=entry,
            )
            if (
                existing.get("mode") != requested["mode"]
                or tuple(existing.get("allowed_owners") or ())
                != tuple(requested["allowed_owners"])
                or existing.get("broker_snapshot_sha256")
                != snapshot["snapshot_sha256"]
                or existing.get("entry_authority_hash") != entry_hash
            ):
                raise SymbolOwnerPolicyApplyError(
                    f"symbol_owner_apply_activation_resume_conflict:{symbol}"
                )
            entry["activation_receipt"] = {
                "schema": "owner_custody_policy_activation_v1",
                "active_date": active_date.isoformat(),
                "policy_id": policy_id,
                "symbol": symbol,
                "broker_account_key": existing["account_key"],
                "migration_registry_tail_hash": existing[
                    "migration_registry_tail_hash"
                ],
                "broker_snapshot_sha256": existing["broker_snapshot_sha256"],
                "entry_authority_hash": entry_hash,
                "activation_event_hash": existing["event_hash"],
            }
            activated[symbol] = entry
            continue
        broker_orders = {
            row["order_no"]
            for row in snapshot["open_orders"]
            if row["symbol"] == symbol
        }
        receipt = registry.migration_receipt(
            symbol=symbol,
            broker_quantity=requested["expected_broker_quantity"],
            active_date=active_date,
            verified_exchanges={"KRX", "NXT"},
            broker_open_order_nos=broker_orders,
            broker_snapshot_sha256=snapshot["snapshot_sha256"],
        )
        if (
            receipt["external_manual_remainder"]
            != requested["expected_external_manual_remainder"]
        ):
            raise SymbolOwnerPolicyApplyError(
                f"symbol_owner_apply_external_remainder_mismatch:{symbol}"
            )
        entry = {
            "mode": requested["mode"],
            "allowed_owners": requested["allowed_owners"],
            "migration_completed": True,
            "rollback_mode": COEXIST_EXIT_ONLY,
            "migration_receipt": receipt,
            "apply_request_sha256": request_sha256,
        }
        entry_hash = symbol_owner_entry_authority_hash(
            active_date=active_date,
            policy_id=policy_id,
            symbol=symbol,
            entry=entry,
        )
        entry["activation_receipt"] = registry.activate_policy_entry(
            active_date=active_date,
            policy_id=policy_id,
            symbol=symbol,
            mode=requested["mode"],
            allowed_owners=requested["allowed_owners"],
            migration_receipt=receipt,
            entry_authority_hash=entry_hash,
        )
        activated[symbol] = entry
    return activated


def apply_symbol_owner_policy(
    request_path: Path,
    *,
    apply: bool = False,
    confirmation: str = "",
    now: datetime | None = None,
    process_scanner: Callable[[], list[dict[str, Any]]] = find_running_trading_processes,
    snapshot_fetcher: Callable[
        [str, set[str], tuple[dict[str, Any], ...]], dict[str, Any]
    ] = collect_broker_snapshot,
    token_loader: Callable[[], str | None] | None = None,
    registry: OrderOwnerRegistry | None = None,
    receipt_dir: Path = DEFAULT_RECEIPT_DIR,
    owner_env_file: Path = OWNER_ENV_FILE,
    apply_lock_path: Path = DEFAULT_APPLY_LOCK,
    output_policy_path: Path | None = None,
) -> dict[str, Any]:
    """Validate or atomically publish one exact-date coexistence policy."""

    observed_at = now or datetime.now(tz=KST)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=KST)
    request, request_hash = _load_request(Path(request_path))
    (
        active_date,
        policy_id,
        account_key,
        generated_at_kst,
        entries,
    ) = _validate_request(request, now=observed_at)
    expected_confirmation = f"APPLY SAME SYMBOL OWNER POLICY {active_date.isoformat()}"
    if apply and confirmation != expected_confirmation:
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_confirmation_mismatch"
        )
    local_time = observed_at.astimezone(KST).time().replace(tzinfo=None)
    if apply and not (PREOPEN_APPLY_START <= local_time <= PREOPEN_APPLY_END):
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_outside_preopen_window"
        )
    if apply and pwd.getpwuid(os.geteuid()).pw_name != "ubuntu":
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_effective_user_must_match_runtime_user:ubuntu"
        )
    os.environ[BROKER_ACCOUNT_KEY_ENV] = account_key
    os.environ.setdefault(REGISTRY_PATH_ENV, str(DEFAULT_REGISTRY_PATH))
    if broker_account_key(require_explicit=True) != account_key:
        raise SymbolOwnerPolicyApplyError("symbol_owner_apply_account_key_mismatch")
    target_registry = registry or OrderOwnerRegistry()
    output_path = (
        Path(output_policy_path)
        if output_policy_path is not None
        else DEFAULT_POLICY_DIR
        / f"symbol_owner_policy_{active_date.isoformat()}.json"
    )
    if not target_registry.path.is_absolute() or not output_path.is_absolute():
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_runtime_path_must_be_absolute"
        )
    running = process_scanner()
    if running:
        raise SymbolOwnerPolicyApplyError(
            "symbol_owner_apply_trading_process_not_quiescent:"
            + ",".join(str(row.get("pid")) for row in running)
        )
    if token_loader is None:
        from src.utils import kiwoom_utils

        token_loader = kiwoom_utils.get_cached_kiwoom_token
    token = token_loader()
    if not token:
        raise SymbolOwnerPolicyApplyError("symbol_owner_apply_cached_token_missing")
    symbols = set(entries)
    migration_rows = tuple(
        {**row, "symbol": symbol}
        for symbol, entry in sorted(entries.items())
        for row in entry["migrated_positions"]
    )
    first_snapshot = snapshot_fetcher(token, symbols, migration_rows)
    second_snapshot = snapshot_fetcher(token, symbols, migration_rows)
    _validate_broker_snapshot(first_snapshot, entries)
    _validate_broker_snapshot(second_snapshot, entries)
    if first_snapshot != second_snapshot:
        raise SymbolOwnerPolicyApplyError("symbol_owner_apply_broker_snapshot_drift")

    current_reconciliation: dict[str, dict[str, Any]] = {}
    for symbol, entry in entries.items():
        current = target_registry.reconcile_symbol_quantity(
            symbol=symbol,
            broker_quantity=entry["expected_broker_quantity"],
        )
        activation_exists = target_registry.policy_activation_record(
            active_date=active_date,
            policy_id=policy_id,
            symbol=symbol,
        ) is not None
        new_migration_quantity = 0
        if not activation_exists:
            for migration in entry["migrated_positions"]:
                already_registered = (
                    target_registry.matched_migrated_position_quantity(
                        context=_migration_context(migration),
                        symbol=symbol,
                        quantity=int(migration.get("quantity")),
                        average_price=int(migration.get("average_price")),
                        route=str(migration.get("route") or "").strip().upper(),
                        order_date=str(migration.get("order_date") or "").strip(),
                        broker_order_no=str(
                            migration.get("broker_order_no") or ""
                        ).strip(),
                        evidence_sha256=str(
                            migration.get("evidence_sha256") or ""
                        ).strip(),
                    )
                )
                new_migration_quantity += int(migration.get("quantity")) - int(
                    already_registered
                )
        projected_registered = (
            current["registered_owner_quantity"] + new_migration_quantity
        )
        if (
            projected_registered
            + entry["expected_external_manual_remainder"]
            != entry["expected_broker_quantity"]
        ):
            raise SymbolOwnerPolicyApplyError(
                f"symbol_owner_apply_projected_quantity_mismatch:{symbol}"
            )
        current_reconciliation[symbol] = current
    dry_result = {
        "schema": APPLY_RECEIPT_SCHEMA,
        "status": "dry_run_ready" if not apply else "preconditions_passed",
        "runtime_effect": False,
        "active_date": active_date.isoformat(),
        "policy_id": policy_id,
        "generated_at_kst": generated_at_kst,
        "broker_account_key": account_key,
        "request_path": str(Path(request_path).resolve()),
        "request_sha256": request_hash,
        "broker_snapshot_sha256": first_snapshot["snapshot_sha256"],
        "policy_path": str(output_path),
        "registry_path": str(target_registry.path),
        "symbols": sorted(entries),
        "current_reconciliation": current_reconciliation,
        "required_confirmation": expected_confirmation,
    }
    if not apply:
        return dry_result

    apply_lock_path.parent.mkdir(parents=True, exist_ok=True)
    with apply_lock_path.open("a+", encoding="utf-8") as apply_lock:
        fcntl.flock(apply_lock.fileno(), fcntl.LOCK_EX)
        running = process_scanner()
        if running:
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_trading_process_started_during_apply:"
                + ",".join(str(row.get("pid")) for row in running)
            )
        _register_requested_migrations(
            target_registry,
            active_date=active_date,
            policy_id=policy_id,
            entries=entries,
        )
        post_migration_snapshot = snapshot_fetcher(token, symbols, migration_rows)
        if post_migration_snapshot != first_snapshot:
            raise SymbolOwnerPolicyApplyError(
                "symbol_owner_apply_post_migration_broker_snapshot_drift"
            )
        activated_entries = _build_activated_entries(
            target_registry,
            active_date=active_date,
            policy_id=policy_id,
            request_sha256=request_hash,
            snapshot=post_migration_snapshot,
            entries=entries,
        )
        payload = build_symbol_owner_policy_payload(
            active_date=active_date,
            policy_id=policy_id,
            symbol_entries=activated_entries,
            generated_at_kst=generated_at_kst,
        )
        if output_path.exists():
            try:
                existing = json.loads(output_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SymbolOwnerPolicyApplyError(
                    "symbol_owner_apply_existing_policy_unreadable"
                ) from exc
            if existing != payload:
                raise SymbolOwnerPolicyApplyError(
                    "symbol_owner_apply_existing_policy_conflict"
                )
        receipt = {
            **dry_result,
            "status": "applied",
            "runtime_effect": True,
            "applied_at_kst": datetime.now(tz=KST).isoformat(),
            "policy_path": str(output_path),
            "policy_hash": payload["policy_hash"],
            "registry_path": str(target_registry.path),
            "activation_event_hashes": {
                symbol: entry["activation_receipt"]["activation_event_hash"]
                for symbol, entry in activated_entries.items()
            },
        }
        receipt_path = receipt_dir / (
            f"symbol_owner_policy_apply_{active_date.isoformat()}.json"
        )
        env_content = (
            f"{BROKER_ACCOUNT_KEY_ENV}={shlex.quote(account_key)}\n"
            f"{REGISTRY_PATH_ENV}={shlex.quote(str(target_registry.path))}\n"
            f"{POLICY_FILE_ENV}={shlex.quote(str(output_path))}\n"
        )
        _atomic_write(owner_env_file, env_content)
        _atomic_write(
            receipt_path,
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        # Policy is the final commit point.  A crash before this replace leaves
        # activation evidence but no runtime authority, which remains fail-closed.
        _atomic_write(
            output_path,
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        fcntl.flock(apply_lock.fileno(), fcntl.LOCK_UN)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        result = apply_symbol_owner_policy(
            args.request,
            apply=args.apply,
            confirmation=args.confirm,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema": APPLY_RECEIPT_SCHEMA,
                    "status": "blocked",
                    "runtime_effect": False,
                    "reason": str(exc),
                    "error_type": type(exc).__name__,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
