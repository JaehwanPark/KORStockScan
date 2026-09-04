"""Validated standing authority for unattended same-symbol PREOPEN apply.

This artifact is intentionally narrower than the daily owner policy.  It only
authorizes the existing owner-isolation contract to be rebuilt for the current
KRX date.  It cannot migrate legacy custody, change quantities or prices, or
relax any market, broker, account, order, cooldown, or hard-safety guard.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.trading.config.symbol_owner_policy import (
    COEXIST_ENTRY_ENABLED,
    VALID_OWNERS,
    normalize_symbol,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
STANDING_AUTHORITY_SCHEMA = "symbol_owner_policy_standing_authority_v1"
STANDING_APPLY_BINDING_SCHEMA = "symbol_owner_policy_standing_apply_binding_v1"
DEFAULT_STANDING_AUTHORITY_PATH = (
    DATA_DIR / "config" / "symbol_owner_policy_standing_authority.json"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ACCOUNT_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")
STANDING_PREOPEN_START = time(7, 32)
STANDING_PREOPEN_END = time(7, 54)

FORBIDDEN_USES = [
    "migrate_or_infer_legacy_owner_custody",
    "classify_unregistered_broker_quantity_as_manual_custody",
    "accept_unregistered_or_ambiguous_open_orders",
    "change_order_quantity_price_target_threshold_provider_bot_or_cap",
    "relax_market_broker_account_order_cooldown_or_hard_safety",
    "stop_or_cancel_broker_orders",
    "cross_owner_cancel_sell_or_quantity_transfer",
]


class SymbolOwnerStandingAuthorityError(RuntimeError):
    """The checked-in standing authority is absent, stale, or malformed."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def content_sha256(value: Mapping[str, Any]) -> str:
    canonical = {
        key: item for key, item in value.items() if key != "artifact_content_sha256"
    }
    return hashlib.sha256(_canonical_bytes(canonical)).hexdigest()


def _aware_kst(value: object, *, error: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError as exc:
        raise SymbolOwnerStandingAuthorityError(error) from exc
    if parsed.tzinfo is None:
        raise SymbolOwnerStandingAuthorityError(error)
    return parsed.astimezone(KST)


def _clock(value: object, *, error: str) -> time:
    try:
        parsed = time.fromisoformat(str(value or ""))
    except ValueError as exc:
        raise SymbolOwnerStandingAuthorityError(error) from exc
    if parsed.tzinfo is not None:
        raise SymbolOwnerStandingAuthorityError(error)
    return parsed


def build_standing_authority(
    *,
    authorization_id: str,
    operator_instruction: str,
    reviewed_at_kst: str,
    effective_from: str,
    expires_after: str,
    broker_account_key: str,
    preopen_start: str,
    preopen_end: str,
    symbols: Mapping[str, list[str]],
) -> dict[str, Any]:
    """Build the immutable, recurring-but-bounded operator authority artifact."""

    reviewed = _aware_kst(
        reviewed_at_kst, error="symbol_owner_standing_reviewed_at_invalid"
    )
    try:
        first_day = date.fromisoformat(str(effective_from or ""))
        last_day = date.fromisoformat(str(expires_after or ""))
    except ValueError as exc:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_effective_date_invalid"
        ) from exc
    if first_day > last_day or reviewed.date() > first_day:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_effective_range_invalid"
        )
    if (last_day - first_day).days > 370:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_effective_range_too_wide"
        )
    start = _clock(preopen_start, error="symbol_owner_standing_window_invalid")
    end = _clock(preopen_end, error="symbol_owner_standing_window_invalid")
    if start != STANDING_PREOPEN_START or end != STANDING_PREOPEN_END:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_window_invalid"
        )
    account_key = str(broker_account_key or "").strip()
    if not ACCOUNT_KEY_RE.fullmatch(account_key) or account_key.lower() == "default":
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_account_key_invalid"
        )
    normalized_symbols: dict[str, dict[str, Any]] = {}
    for raw_symbol, raw_owners in symbols.items():
        symbol = normalize_symbol(raw_symbol)
        owners = sorted({str(owner or "").strip().lower() for owner in raw_owners})
        if (
            symbol != str(raw_symbol)
            or not (symbol.isdigit() and len(symbol) == 6)
            or symbol in normalized_symbols
            or not owners
            or "main_scalping" not in owners
            or "manual_operator" not in owners
            or not {"widget_auto_trade", "episode"}.intersection(owners)
            or any(owner not in VALID_OWNERS for owner in owners)
        ):
            raise SymbolOwnerStandingAuthorityError(
                "symbol_owner_standing_symbol_scope_invalid"
            )
        normalized_symbols[symbol] = {
            "mode": COEXIST_ENTRY_ENABLED,
            "allowed_owners": owners,
        }
    if not normalized_symbols:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_symbol_scope_empty"
        )
    authority_id = str(authorization_id or "").strip()
    instruction = str(operator_instruction or "").strip()
    if (
        not authority_id
        or len(authority_id) > 160
        or any(ch in authority_id for ch in "\r\n\t")
        or not instruction
        or len(instruction) > 500
    ):
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_instruction_invalid"
        )
    body = {
        "schema": STANDING_AUTHORITY_SCHEMA,
        "status": "active",
        "authorization_id": authority_id,
        "operator_instruction": instruction,
        "reviewed_at_kst": reviewed.isoformat(timespec="seconds"),
        "effective_from": first_day.isoformat(),
        "expires_after": last_day.isoformat(),
        "recurring_exact_date_apply": True,
        "broker_account_key": account_key,
        "preopen_window": {
            "start_kst": start.isoformat(timespec="seconds"),
            "end_kst": end.isoformat(timespec="seconds"),
        },
        "scope_contract": "exact_current_widget_episode_symbol_universe",
        "unresolved_custody_behavior": "skip_symbol_keep_legacy_exclusion",
        "unregistered_open_order_behavior": "skip_symbol_keep_legacy_exclusion",
        "minimum_safe_symbol_count": 1,
        "auto_issue_shared_token": True,
        "symbols": dict(sorted(normalized_symbols.items())),
        "forbidden_uses": list(FORBIDDEN_USES),
    }
    return {**body, "artifact_content_sha256": content_sha256(body)}


def load_standing_authority(
    path: Path = DEFAULT_STANDING_AUTHORITY_PATH,
    *,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    now = observed_at or datetime.now(tz=KST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=KST)
    now = now.astimezone(KST)
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SymbolOwnerStandingAuthorityError(
            f"symbol_owner_standing_authority_unreadable:{type(exc).__name__}"
        ) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != STANDING_AUTHORITY_SCHEMA
    ):
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_authority_schema_invalid"
        )
    if payload.get("artifact_content_sha256") != content_sha256(payload):
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_authority_hash_mismatch"
        )
    if payload.get("status") != "active":
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_authority_not_active"
        )
    raw_symbols = payload.get("symbols")
    if not isinstance(raw_symbols, dict):
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_symbol_scope_invalid"
        )
    rebuilt = build_standing_authority(
        authorization_id=str(payload.get("authorization_id") or ""),
        operator_instruction=str(payload.get("operator_instruction") or ""),
        reviewed_at_kst=str(payload.get("reviewed_at_kst") or ""),
        effective_from=str(payload.get("effective_from") or ""),
        expires_after=str(payload.get("expires_after") or ""),
        broker_account_key=str(payload.get("broker_account_key") or ""),
        preopen_start=str(
            (payload.get("preopen_window") or {}).get("start_kst") or ""
        ),
        preopen_end=str(
            (payload.get("preopen_window") or {}).get("end_kst") or ""
        ),
        symbols={
            str(symbol): list(entry.get("allowed_owners") or [])
            for symbol, entry in raw_symbols.items()
            if isinstance(entry, dict)
        },
    )
    if rebuilt != payload:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_authority_contract_mismatch"
        )
    first_day = date.fromisoformat(payload["effective_from"])
    last_day = date.fromisoformat(payload["expires_after"])
    if not first_day <= now.date() <= last_day:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_authority_outside_effective_range"
        )
    return payload


def standing_apply_window(authority: Mapping[str, Any]) -> tuple[time, time]:
    window = authority.get("preopen_window")
    if not isinstance(window, Mapping):
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_window_invalid"
        )
    return (
        _clock(window.get("start_kst"), error="symbol_owner_standing_window_invalid"),
        _clock(window.get("end_kst"), error="symbol_owner_standing_window_invalid"),
    )


def validate_apply_binding(
    authority: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    active_date: date,
) -> None:
    binding = request.get("standing_authorization")
    expected = {
        "schema": STANDING_APPLY_BINDING_SCHEMA,
        "authorization_id": authority.get("authorization_id"),
        "artifact_content_sha256": authority.get("artifact_content_sha256"),
        "active_date": active_date.isoformat(),
        "runner": "src.trading.order.symbol_owner_policy_auto_apply",
    }
    if binding != expected:
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_apply_binding_mismatch"
        )
    if not SHA256_RE.fullmatch(str(authority.get("artifact_content_sha256") or "")):
        raise SymbolOwnerStandingAuthorityError(
            "symbol_owner_standing_authority_hash_invalid"
        )
