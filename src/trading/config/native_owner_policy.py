"""Main/manual authority from the common journal, without daily episode policy.

Historical automatic-owner receipts remain attributed to their original owner.
Only native Main intents may create automatic orders after retirement.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from src.trading.config.owner_identity import normalize_symbol
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
COEXIST_ENTRY_ENABLED = "COEXIST_ENTRY_ENABLED"
COEXIST_EXIT_ONLY = "COEXIST_EXIT_ONLY"
EXCLUSIVE_MANUAL = "EXCLUSIVE_MANUAL"
NATIVE_POLICY_ID = "main_manual_native_custody_v1"


class SymbolOwnerPolicyError(RuntimeError):
    pass


def policy_path(target_date=None) -> Path:
    # Compatibility for callers testing whether custody evidence exists.
    from src.trading.order.owner_custody_registry import registry_path
    return registry_path()


@dataclass(frozen=True)
class NativeOwnerDecision:
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
    account_key: str = ""
    effective_at: str = ""

    @property
    def symbol_selected(self):
        return self.policy_present

    @property
    def coexistence_enabled(self):
        return self.policy_present and self.migration_completed

    def owner_allowed(self, owner, *, new_entry=True):
        return str(owner or "").strip().lower() == "main_scalping" and (
            not self.policy_present or self.migration_completed)

    def as_log_fields(self):
        return {
            "symbol_owner_policy_present": self.policy_present,
            "symbol_owner_policy_id": self.policy_id or "-",
            "symbol_owner_policy_hash": self.policy_hash or "-",
            "symbol_owner_policy_mode": self.mode,
            "symbol_owner_policy_allowed_owners": ",".join(self.allowed_owners),
            "symbol_owner_policy_migration_completed": self.migration_completed,
            "symbol_owner_policy_reason": self.reason,
            "symbol_owner_policy_source": self.source_path,
            "symbol_owner_policy_migration_registry_tail_hash": self.migration_registry_tail_hash or "-",
            "symbol_owner_policy_activation_event_hash": self.activation_event_hash or "-",
            "symbol_owner_policy_entry_authority_hash": self.entry_authority_hash or "-",
            "symbol_owner_policy_broker_snapshot_sha256": "-",
        }


def resolve_symbol_owner_policy(symbol, *, target_date=None):
    from src.trading.order.owner_custody_registry import default_order_owner_registry, OwnerRegistryError
    try:
        status = default_order_owner_registry().native_owner_contract(symbol)
    except OwnerRegistryError as exc:
        raise SymbolOwnerPolicyError(str(exc)) from exc
    day = target_date or datetime.now(KST).date()
    if isinstance(day, datetime):
        day = day.astimezone(KST).date()
    day = date.fromisoformat(str(day)).isoformat()
    if status["registered"] and not status["disposition_hash"]:
        raise SymbolOwnerPolicyError("native_owner_management_disposition_missing")
    binding = {"schema": NATIVE_POLICY_ID, "account_key": status["account_key"],
               "symbol": normalize_symbol(symbol), "disposition_hash": status["disposition_hash"],
               "effective_at": status["effective_at"]}
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return NativeOwnerDecision(
        symbol=binding["symbol"], target_date=day, mode=COEXIST_ENTRY_ENABLED,
        allowed_owners=("main_scalping", "manual_operator"),
        migration_completed=bool(status["disposition_hash"]), policy_present=status["registered"],
        policy_id=NATIVE_POLICY_ID, policy_hash=digest, source_path=status["registry_path"],
        reason="native_main_manual_resolved" if status["registered"] else "exact_date_policy_absent",
        activation_event_hash=status["disposition_hash"], account_key=status["account_key"],
        effective_at=status["effective_at"], entry_authority_hash=digest,
    )


def historical_single_owner_binding(fields, *, observed_at):
    """Validate pre-retirement absent-policy telemetry, without a legacy loader.

    This proves only the source contract. Consumers still verify native date,
    order/quantity and absence of a conflicting frozen journal intent.
    """
    if (fields.get("buy_registry_mode") != "single_owner_unregistered"
        or str(fields.get("buy_owner_policy_selected")).lower() != "false"
        or str(fields.get("buy_owner_policy_coexistence")).lower() != "false"
        or fields.get("buy_owner_policy_reason") != "exact_date_policy_missing_legacy_exclusion_retained"
        or str(fields.get("buy_owner_policy_hash") or "") not in {"", "-"}):
        return False
    try:
        stamp = datetime.fromisoformat(str(observed_at))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=KST)
        if stamp.astimezone(KST).date().isoformat() != fields.get("buy_owner_policy_date"):
            return False
        # The dated original receipt is archive evidence. Never consult today's
        # registry or use this historical shape for post-retirement submissions.
        return stamp.astimezone(KST).date() < date(2026, 10, 8)
    except (ValueError, TypeError, OSError):
        return False
