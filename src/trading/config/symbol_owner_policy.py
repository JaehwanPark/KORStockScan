"""Exact-date authority for same-symbol multi-owner trading.

The legacy contract makes a ``manual_operator`` exclusion a symbol-wide main
bot veto.  This module provides the only supported exception: an exact-date,
hash-verifiable policy that explicitly names the owners allowed to coexist.
Absence, staleness, malformed content, or an incomplete migration all retain
the legacy exclusive behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
POLICY_SCHEMA = "symbol_owner_policy_v2"
ACTIVATION_SCHEMA = "owner_custody_policy_activation_v1"
POLICY_FILE_ENV = "KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE"
BROKER_ACCOUNT_KEY_ENV = "KORSTOCKSCAN_BROKER_ACCOUNT_KEY"
DEFAULT_POLICY_DIR = DATA_DIR / "runtime" / "symbol_owner_policy"

COEXIST_ENTRY_ENABLED = "COEXIST_ENTRY_ENABLED"
COEXIST_EXIT_ONLY = "COEXIST_EXIT_ONLY"
EXCLUSIVE_MANUAL = "EXCLUSIVE_MANUAL"
VALID_MODES = frozenset(
    {
        COEXIST_ENTRY_ENABLED,
        COEXIST_EXIT_ONLY,
        EXCLUSIVE_MANUAL,
    }
)
VALID_OWNERS = frozenset(
    {"main_scalping", "widget_auto_trade", "episode", "manual_operator"}
)


class SymbolOwnerPolicyError(RuntimeError):
    """Raised when a configured policy cannot safely grant authority."""


def normalize_symbol(value: object) -> str:
    raw = str(value or "").strip().upper()
    base = raw
    if base.endswith(("_NX", "_AL")):
        base = base[:-3]
    if base.startswith("A"):
        base = base[1:]
    if base.isdigit() and 1 <= len(base) <= 6:
        return base.zfill(6)
    # Preserve malformed input so the strict six-digit caller check can fail
    # closed. Never truncate a longer identifier into another listed symbol.
    return raw


def _canonical_hash(payload: dict[str, Any]) -> str:
    content = dict(payload)
    content.pop("policy_hash", None)
    encoded = json.dumps(
        content, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _target_date(value: date | datetime | str | None) -> date:
    if value is None:
        return datetime.now(tz=KST).date()
    if isinstance(value, datetime):
        current = value if value.tzinfo else value.replace(tzinfo=KST)
        return current.astimezone(KST).date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def policy_path(target_date: date | datetime | str | None = None) -> Path:
    configured = str(os.getenv(POLICY_FILE_ENV, "") or "").strip()
    if configured:
        return Path(configured).expanduser()
    day = _target_date(target_date)
    return DEFAULT_POLICY_DIR / f"symbol_owner_policy_{day.isoformat()}.json"


def _broker_account_key(*, require_explicit: bool = False) -> str:
    configured = os.getenv(BROKER_ACCOUNT_KEY_ENV)
    value = str(configured or "default").strip()
    if not value or len(value) > 80 or any(ch in value for ch in "\r\n\t"):
        raise SymbolOwnerPolicyError("symbol_owner_policy_broker_account_key_invalid")
    if require_explicit and (configured is None or value.lower() == "default"):
        raise SymbolOwnerPolicyError(
            "symbol_owner_policy_explicit_broker_account_key_required"
        )
    return value


def symbol_owner_entry_authority_hash(
    *,
    active_date: date | datetime | str,
    policy_id: str,
    symbol: object,
    entry: dict[str, Any],
) -> str:
    """Hash the exact per-symbol authority before its activation receipt.

    The registry activation event binds this digest while holding the journal
    lock.  The final top-level policy hash then binds the activation receipt.
    This two-step contract avoids a circular policy/event hash dependency.
    """

    day = _target_date(active_date)
    clean_symbol = normalize_symbol(symbol)
    content = dict(entry)
    content.pop("activation_receipt", None)
    payload = {
        "active_date": day.isoformat(),
        "policy_id": str(policy_id or "").strip(),
        "symbol": clean_symbol,
        "entry": content,
    }
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class SymbolOwnerDecision:
    symbol: str
    target_date: str
    mode: str
    allowed_owners: tuple[str, ...]
    migration_completed: bool
    policy_present: bool
    policy_id: str
    policy_hash: str
    source_path: str
    reason: str
    migration_registry_tail_hash: str = ""
    activation_event_hash: str = ""
    entry_authority_hash: str = ""
    broker_snapshot_sha256: str = ""

    def owner_allowed(self, owner: str, *, new_entry: bool = True) -> bool:
        normalized_owner = str(owner or "").strip().lower()
        if not self.policy_present:
            return False
        if normalized_owner not in self.allowed_owners:
            return False
        if self.mode in {COEXIST_ENTRY_ENABLED, COEXIST_EXIT_ONLY} and not (
            self.migration_completed
        ):
            return False
        if self.mode == COEXIST_ENTRY_ENABLED:
            return True
        if self.mode == COEXIST_EXIT_ONLY:
            return not new_entry
        if self.mode == EXCLUSIVE_MANUAL:
            return normalized_owner == "manual_operator"
        return False

    @property
    def coexistence_enabled(self) -> bool:
        return bool(
            self.policy_present
            and self.migration_completed
            and self.mode in {COEXIST_ENTRY_ENABLED, COEXIST_EXIT_ONLY}
            and "main_scalping" in self.allowed_owners
            and bool({"widget_auto_trade", "episode"}.intersection(self.allowed_owners))
        )

    @property
    def symbol_selected(self) -> bool:
        """Whether this exact-date artifact explicitly governs the symbol."""

        return bool(self.policy_present and self.reason == "exact_date_policy_resolved")

    def as_log_fields(self) -> dict[str, object]:
        return {
            "symbol_owner_policy_present": self.policy_present,
            "symbol_owner_policy_id": self.policy_id or "-",
            "symbol_owner_policy_hash": self.policy_hash or "-",
            "symbol_owner_policy_mode": self.mode,
            "symbol_owner_policy_allowed_owners": ",".join(self.allowed_owners),
            "symbol_owner_policy_migration_completed": self.migration_completed,
            "symbol_owner_policy_reason": self.reason,
            "symbol_owner_policy_source": self.source_path,
            "symbol_owner_policy_migration_registry_tail_hash": (
                self.migration_registry_tail_hash or "-"
            ),
            "symbol_owner_policy_activation_event_hash": (
                self.activation_event_hash or "-"
            ),
            "symbol_owner_policy_entry_authority_hash": (
                self.entry_authority_hash or "-"
            ),
            "symbol_owner_policy_broker_snapshot_sha256": (
                self.broker_snapshot_sha256 or "-"
            ),
            "metric_role": "order_owner_runtime_guard",
            "decision_authority": "exact_date_same_symbol_owner_policy",
            "window_policy": "one_exact_kst_trade_date",
            "sample_floor": "not_applicable_owner_authority",
            "primary_decision_metric": "owner_and_action_authorized",
            "source_quality_gate": (
                "exact_date_hash_schema_migration_and_activation_complete"
            ),
            "runtime_effect": True,
            "forbidden_uses": (
                "cross_owner_cancel|cross_owner_sell|aggregate_balance_owner_inference|"
                "threshold_change|quantity_or_cap_change|broker_guard_relaxation"
            ),
        }


def _validate_symbol_entry(
    raw: object,
    *,
    normalized_symbol: str,
    day: date,
    policy_id: str,
) -> tuple[str, tuple[str, ...], bool, str, str, str, str]:
    if not (normalized_symbol.isdigit() and len(normalized_symbol) == 6):
        raise SymbolOwnerPolicyError("symbol_owner_policy_symbol_invalid")
    if not isinstance(raw, dict):
        raise SymbolOwnerPolicyError("symbol_owner_policy_symbol_entry_invalid")
    mode = str(raw.get("mode") or "").strip().upper()
    if mode not in VALID_MODES:
        raise SymbolOwnerPolicyError("symbol_owner_policy_mode_invalid")
    owners_raw = raw.get("allowed_owners")
    if not isinstance(owners_raw, list) or not owners_raw:
        raise SymbolOwnerPolicyError("symbol_owner_policy_allowed_owners_invalid")
    owners = tuple(sorted({str(item).strip().lower() for item in owners_raw}))
    if any(owner not in VALID_OWNERS for owner in owners):
        raise SymbolOwnerPolicyError("symbol_owner_policy_unknown_owner")
    migration_completed = raw.get("migration_completed") is True
    registry_tail_hash = ""
    activation_event_hash = ""
    entry_authority_hash = ""
    broker_snapshot_hash = ""
    if mode in {COEXIST_ENTRY_ENABLED, COEXIST_EXIT_ONLY}:
        if not migration_completed:
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_coexist_migration_incomplete"
            )
        if "main_scalping" not in owners or not {
            "widget_auto_trade",
            "episode",
        }.intersection(owners):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_coexist_owner_set_invalid"
            )
        rollback_mode = str(raw.get("rollback_mode") or "").strip().upper()
        if rollback_mode != COEXIST_EXIT_ONLY:
            raise SymbolOwnerPolicyError("symbol_owner_policy_rollback_mode_invalid")
        migration = raw.get("migration_receipt")
        if not isinstance(migration, dict):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_receipt_missing"
            )
        if (
            migration.get("schema") != "owner_custody_migration_receipt_v1"
            or migration.get("symbol") != normalized_symbol
            or migration.get("active_date") != day.isoformat()
            or migration.get("broker_account_key")
            != _broker_account_key(require_explicit=True)
            or migration.get("validated") is not True
        ):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_receipt_invalid"
            )
        try:
            broker_quantity = int(migration.get("broker_quantity"))
            registered_quantity = int(migration.get("registered_owner_quantity"))
            external_remainder = int(migration.get("external_manual_remainder"))
        except (TypeError, ValueError) as exc:
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_quantity_invalid"
            ) from exc
        if (
            min(broker_quantity, registered_quantity, external_remainder) < 0
            or registered_quantity + external_remainder != broker_quantity
        ):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_conservation_invalid"
            )
        registry_tail_hash = str(migration.get("registry_tail_hash") or "").lower()
        if len(registry_tail_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in registry_tail_hash
        ):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_registry_hash_invalid"
            )
        verified_exchanges = {
            str(item or "").strip().upper()
            for item in (migration.get("verified_exchanges") or [])
        }
        if not {"KRX", "NXT"}.issubset(verified_exchanges):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_all_venues_not_verified"
            )
        broker_orders = migration.get("broker_open_order_nos")
        registered_orders = migration.get("registered_open_order_nos")
        broker_order_values = (
            [str(item).strip() for item in broker_orders]
            if isinstance(broker_orders, list)
            else []
        )
        registered_order_values = (
            [str(item).strip() for item in registered_orders]
            if isinstance(registered_orders, list)
            else []
        )
        if (
            not isinstance(broker_orders, list)
            or not isinstance(registered_orders, list)
            or any(
                not (value.isdigit() and len(value) == 7)
                for value in broker_order_values + registered_order_values
            )
            or sorted(set(broker_order_values)) != sorted(set(registered_order_values))
        ):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_open_orders_invalid"
            )
        broker_snapshot_hash = (
            str(migration.get("broker_snapshot_sha256") or "").strip().lower()
        )
        if len(broker_snapshot_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in broker_snapshot_hash
        ):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_migration_broker_snapshot_hash_invalid"
            )
        activation = raw.get("activation_receipt")
        if not isinstance(activation, dict):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_activation_receipt_missing"
            )
        activation_event_hash = str(
            activation.get("activation_event_hash") or ""
        ).strip().lower()
        entry_authority_hash = str(
            activation.get("entry_authority_hash") or ""
        ).strip().lower()
        expected_entry_hash = symbol_owner_entry_authority_hash(
            active_date=day,
            policy_id=policy_id,
            symbol=normalized_symbol,
            entry=raw,
        )
        if (
            activation.get("schema") != ACTIVATION_SCHEMA
            or activation.get("symbol") != normalized_symbol
            or activation.get("active_date") != day.isoformat()
            or activation.get("policy_id") != policy_id
            or activation.get("broker_account_key")
            != _broker_account_key(require_explicit=True)
            or activation.get("migration_registry_tail_hash")
            != registry_tail_hash
            or activation.get("broker_snapshot_sha256") != broker_snapshot_hash
            or entry_authority_hash != expected_entry_hash
            or len(activation_event_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in activation_event_hash)
        ):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_activation_receipt_invalid"
            )
    elif mode == EXCLUSIVE_MANUAL:
        if owners != ("manual_operator",):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_exclusive_manual_owner_set_invalid"
            )
        if migration_completed:
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_exclusive_manual_migration_invalid"
            )
    return (
        mode,
        owners,
        migration_completed,
        registry_tail_hash,
        activation_event_hash,
        entry_authority_hash,
        broker_snapshot_hash,
    )


def resolve_symbol_owner_policy(
    symbol: object,
    *,
    target_date: date | datetime | str | None = None,
) -> SymbolOwnerDecision:
    normalized_symbol = normalize_symbol(symbol)
    if not (normalized_symbol.isdigit() and len(normalized_symbol) == 6):
        raise SymbolOwnerPolicyError("symbol_owner_policy_symbol_invalid")
    day = _target_date(target_date)
    path = policy_path(day)
    if not path.exists():
        return SymbolOwnerDecision(
            normalized_symbol,
            day.isoformat(),
            EXCLUSIVE_MANUAL,
            tuple(),
            False,
            False,
            "",
            "",
            str(path),
            "exact_date_policy_missing_legacy_exclusion_retained",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolOwnerPolicyError(
            f"symbol_owner_policy_unreadable:{type(exc).__name__}"
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema") != POLICY_SCHEMA:
        raise SymbolOwnerPolicyError("symbol_owner_policy_schema_invalid")
    if str(payload.get("active_date") or "") != day.isoformat():
        raise SymbolOwnerPolicyError("symbol_owner_policy_active_date_mismatch")
    expected_hash = str(payload.get("policy_hash") or "").strip().lower()
    actual_hash = _canonical_hash(payload)
    if len(expected_hash) != 64 or expected_hash != actual_hash:
        raise SymbolOwnerPolicyError("symbol_owner_policy_hash_mismatch")
    symbols = payload.get("symbols")
    if not isinstance(symbols, dict):
        raise SymbolOwnerPolicyError("symbol_owner_policy_symbols_invalid")
    policy_id = str(payload.get("policy_id") or "").strip()
    if not policy_id or len(policy_id) > 240 or any(ch in policy_id for ch in "\r\n\t"):
        raise SymbolOwnerPolicyError("symbol_owner_policy_id_invalid")
    try:
        generated = datetime.fromisoformat(str(payload.get("generated_at_kst") or ""))
    except ValueError as exc:
        raise SymbolOwnerPolicyError(
            "symbol_owner_policy_generated_at_invalid"
        ) from exc
    if generated.tzinfo is None or generated.astimezone(KST).date() != day:
        raise SymbolOwnerPolicyError("symbol_owner_policy_generated_at_date_mismatch")
    validated_entries = {}
    for policy_symbol, policy_entry in symbols.items():
        clean_policy_symbol = normalize_symbol(policy_symbol)
        if str(policy_symbol) != clean_policy_symbol:
            raise SymbolOwnerPolicyError("symbol_owner_policy_symbol_key_invalid")
        validated_entries[clean_policy_symbol] = _validate_symbol_entry(
            policy_entry,
            normalized_symbol=clean_policy_symbol,
            day=day,
            policy_id=policy_id,
        )
    raw = symbols.get(normalized_symbol)
    if raw is None:
        return SymbolOwnerDecision(
            normalized_symbol,
            day.isoformat(),
            EXCLUSIVE_MANUAL,
            tuple(),
            False,
            True,
            policy_id,
            actual_hash,
            str(path),
            "symbol_not_selected_legacy_exclusion_retained",
        )
    (
        mode,
        owners,
        migration_completed,
        registry_tail_hash,
        activation_event_hash,
        entry_authority_hash,
        broker_snapshot_hash,
    ) = validated_entries[normalized_symbol]
    return SymbolOwnerDecision(
        normalized_symbol,
        day.isoformat(),
        mode,
        owners,
        migration_completed,
        True,
        policy_id,
        actual_hash,
        str(path),
        "exact_date_policy_resolved",
        registry_tail_hash,
        activation_event_hash,
        entry_authority_hash,
        broker_snapshot_hash,
    )


def policy_content_hash(payload: dict[str, Any]) -> str:
    """Public deterministic helper used by the policy builder/tests."""

    return _canonical_hash(payload)


def build_symbol_owner_policy_payload(
    *,
    active_date: date | datetime | str,
    policy_id: str,
    symbol_entries: dict[object, dict[str, Any]],
    generated_at_kst: str,
) -> dict[str, Any]:
    """Build immutable content; publishing remains an explicit apply action."""

    day = _target_date(active_date)
    clean_policy_id = str(policy_id or "").strip()
    if (
        not clean_policy_id
        or len(clean_policy_id) > 240
        or any(ch in clean_policy_id for ch in "\r\n\t")
        or not isinstance(symbol_entries, dict)
        or not symbol_entries
    ):
        raise SymbolOwnerPolicyError("symbol_owner_policy_builder_input_invalid")
    try:
        generated = datetime.fromisoformat(str(generated_at_kst))
    except ValueError as exc:
        raise SymbolOwnerPolicyError(
            "symbol_owner_policy_generated_at_invalid"
        ) from exc
    if generated.tzinfo is None or generated.astimezone(KST).date() != day:
        raise SymbolOwnerPolicyError("symbol_owner_policy_generated_at_date_mismatch")
    normalized_entries: dict[str, dict[str, Any]] = {}
    for symbol, raw in symbol_entries.items():
        clean_symbol = normalize_symbol(symbol)
        if clean_symbol in normalized_entries or not isinstance(raw, dict):
            raise SymbolOwnerPolicyError(
                "symbol_owner_policy_builder_symbol_collision_or_invalid"
            )
        _validate_symbol_entry(
            raw,
            normalized_symbol=clean_symbol,
            day=day,
            policy_id=clean_policy_id,
        )
        normalized_entries[clean_symbol] = dict(raw)
    payload: dict[str, Any] = {
        "schema": POLICY_SCHEMA,
        "active_date": day.isoformat(),
        "policy_id": clean_policy_id,
        "generated_at_kst": generated.astimezone(KST).isoformat(),
        "symbols": dict(sorted(normalized_entries.items())),
    }
    payload["policy_hash"] = _canonical_hash(payload)
    return payload
