"""Live market-scoped entry/cancel guard for widget and episode owners.

The market-weakness observer remains a source-only producer.  This consumer is
the separately approved execution bridge: it may veto a *new* widget or
episode buy and cancel only the broker-reconciled unfilled remainder of an
exact buy order owned by that same runtime.  It has no sell, holding, price,
target, quantity-resize, manual-order, other-owner, or main-bot authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils.constants import PROJECT_ROOT
from src.utils.jsonl_io import (
    read_json_object_strict,
    write_json_object_generation_safe,
)

KST = ZoneInfo("Asia/Seoul")
SUPPORTED_LISTING_MARKETS = frozenset({"KOSPI", "KOSDAQ"})
SUPPORTED_OWNERS = frozenset({"widget", "episode"})

DEFAULT_STATE_PATH = PROJECT_ROOT / "tmp" / "market_weakness_observer_state.json"
DEFAULT_SYMBOL_MASTER_DIR = (
    PROJECT_ROOT / "data/report/micro_reversion_economic_reference"
)
DEFAULT_BLOCKED_ENTRY_OBSERVATION_DIR = (
    PROJECT_ROOT / "data/report/machine_market_weakness_blocked_entries"
)
BLOCKED_ENTRY_OBSERVATION_SCHEMA = "machine_market_weakness_blocked_entry_v1"
ENABLE_ENV = "KORSTOCKSCAN_WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_GUARD_ENABLED"
POLICY_ID = "WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2"
OPERATOR_APPROVAL_DATE = "2026-08-31"


@dataclass(frozen=True, slots=True)
class MarketWeaknessEntryDecision:
    blocked: bool
    reason: str
    symbol: str
    owner: str
    listing_market: str | None
    phase: str
    active_markets: tuple[str, ...]
    session_key: str
    observation_id: str
    observation_as_of: str
    source_status: str
    state_path: str
    symbol_master_path: str | None

    @property
    def exact_market_open_buy_cancel_allowed(self) -> bool:
        """True only for a current, verified, exact-market active latch.

        Entry is fail-closed when an active latch has invalid market scope or
        the symbol market cannot be resolved.  Cancellation is deliberately
        stricter because it is a broker write: an invalid or unresolved scope
        must never be used to cancel an order.
        """

        return bool(
            self.blocked
            and self.reason == "entry_blocked_market_weakness_active"
            and self.phase in {"active", "release_pending"}
            and self.listing_market in SUPPORTED_LISTING_MARKETS
            and self.listing_market in self.active_markets
            and self.session_key
        )

    def event_fields(self) -> dict[str, Any]:
        return {
            "market_weakness_entry_guard_policy_id": POLICY_ID,
            "market_weakness_entry_guard_operator_approval_date": (
                OPERATOR_APPROVAL_DATE
            ),
            "market_weakness_entry_guard_owner": self.owner,
            "market_weakness_entry_guard_symbol": self.symbol,
            "market_weakness_entry_guard_listing_market": self.listing_market,
            "market_weakness_entry_guard_phase": self.phase,
            "market_weakness_entry_guard_active_markets": list(self.active_markets),
            "market_weakness_entry_guard_session_key": self.session_key,
            "market_weakness_entry_guard_observation_id": self.observation_id,
            "market_weakness_entry_guard_observation_as_of": self.observation_as_of,
            "market_weakness_entry_guard_source_status": self.source_status,
            "market_weakness_entry_guard_state_path": self.state_path,
            "market_weakness_entry_guard_symbol_master_path": (self.symbol_master_path),
            "market_weakness_entry_guard_blocked": self.blocked,
            "market_weakness_open_buy_cancel_allowed": (
                self.exact_market_open_buy_cancel_allowed
            ),
            "market_weakness_open_buy_cancel_scope": (
                "exact_owner_current_day_broker_reconciled_unfilled_buy_remainder"
            ),
            "market_weakness_entry_guard_runtime_effect": True,
            "market_weakness_entry_guard_allowed_runtime_apply": True,
            "market_weakness_entry_guard_actual_order_submitted": False,
            "market_weakness_entry_guard_forbidden_uses": [
                "main_bot_entry_block",
                "sell_or_target_change",
                "requested_quantity_resize_or_price_change",
                "holding_or_exit_change",
                "manual_order_control",
                "other_owner_order_control",
                "unreconciled_or_cross_market_order_cancel",
            ],
        }


def _blocked_entry_observation_id(identity: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"machine-weakness-block-{digest}"


def _blocked_entry_content_sha256(payload: dict[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key != "content_sha256"}
    return hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def market_weakness_blocked_entry_contract_errors(
    payload: Any,
    *,
    target_date: str,
) -> list[str]:
    """Validate one immutable blocked-entry counterfactual source artifact."""

    if not isinstance(payload, dict):
        return ["blocked_entry_payload_not_object"]
    errors: list[str] = []
    observed_at_text = str(payload.get("observed_at") or "")
    try:
        parsed_observed_at = datetime.fromisoformat(observed_at_text)
        observed_at = (
            parsed_observed_at.astimezone(KST)
            if parsed_observed_at.tzinfo is not None
            else None
        )
    except (TypeError, ValueError):
        observed_at = None
    venues = payload.get("expected_venues")
    normalized_venues = (
        [str(value).strip().upper() for value in venues]
        if isinstance(venues, list)
        else []
    )
    quantity = payload.get("required_quantity")
    counterfactual = payload.get("counterfactual_contract")
    if payload.get("schema") != BLOCKED_ENTRY_OBSERVATION_SCHEMA:
        errors.append("blocked_entry_schema_invalid")
    if payload.get("trade_date") != target_date:
        errors.append("blocked_entry_trade_date_mismatch")
    if observed_at is None or observed_at.date().isoformat() != target_date:
        errors.append("blocked_entry_observed_at_invalid")
    if payload.get("owner") not in SUPPORTED_OWNERS:
        errors.append("blocked_entry_owner_invalid")
    if payload.get("listing_market") not in SUPPORTED_LISTING_MARKETS:
        errors.append("blocked_entry_listing_market_invalid")
    symbol = str(payload.get("symbol") or "")
    if len(symbol) != 6 or not symbol.isdigit():
        errors.append("blocked_entry_symbol_invalid")
    for field in (
        "scope_id",
        "session",
        "source_signal_id",
        "signal_bar",
        "guard_observation_id",
        "guard_observation_as_of",
    ):
        if not str(payload.get(field) or "").strip():
            errors.append(f"blocked_entry_{field}_missing")
    if (
        not isinstance(venues, list)
        or not venues
        or any(value not in {"KRX", "NXT", "SOR"} for value in normalized_venues)
        or venues != sorted(set(normalized_venues))
    ):
        errors.append("blocked_entry_expected_venues_invalid")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        errors.append("blocked_entry_required_quantity_invalid")
    for field in ("reference_price", "target_price"):
        value = payload.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            errors.append(f"blocked_entry_{field}_invalid")
    if (
        payload.get("guard_policy_id") != POLICY_ID
        or payload.get("decision_authority") != POLICY_ID
        or payload.get("runtime_effect") is not True
        or payload.get("allowed_runtime_apply") is not True
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not False
    ):
        errors.append("blocked_entry_authority_invalid")
    if not (
        isinstance(counterfactual, dict)
        and counterfactual.get("runtime_effect") is False
        and counterfactual.get("allowed_runtime_apply") is False
        and counterfactual.get("actual_order_submitted") is False
        and counterfactual.get("broker_order_forbidden") is True
        and counterfactual.get("horizons_minutes") == [1, 3, 5, 10, 20, 30]
        and counterfactual.get("entry_price")
        == "first_fresh_depth_backed_executable_best_ask"
        and counterfactual.get("exit_price")
        == "fresh_depth_backed_executable_best_bid_at_horizon"
        and counterfactual.get("missing_data") == "source_quality_blocked_no_imputation"
    ):
        errors.append("blocked_entry_counterfactual_contract_invalid")
    identity = {
        field: payload.get(field)
        for field in (
            "trade_date",
            "owner",
            "scope_id",
            "symbol",
            "session",
            "source_signal_id",
            "signal_bar",
        )
    }
    if payload.get("observation_id") != _blocked_entry_observation_id(identity):
        errors.append("blocked_entry_observation_id_invalid")
    if payload.get("content_sha256") != _blocked_entry_content_sha256(payload):
        errors.append("blocked_entry_content_sha256_invalid")
    return sorted(set(errors))


def record_market_weakness_blocked_entry(
    decision: MarketWeaknessEntryDecision,
    *,
    now: datetime,
    scope_id: str,
    session: str,
    source_signal_id: str,
    signal_bar: str,
    reference_price: int | float | None,
    target_price: int | float | None,
    required_quantity: int,
    expected_venues: tuple[str, ...] | list[str],
    output_dir: Path = DEFAULT_BLOCKED_ENTRY_OBSERVATION_DIR,
) -> dict[str, Any]:
    """Persist one immutable, idempotent blocked-signal counterfactual anchor.

    Recording failure never grants an entry and never changes the already-made
    guard decision.  The returned status is copied into the owner audit so a
    postclose source gap remains explicit instead of being imputed.
    """

    observed_at = now.astimezone(KST)
    clean_scope = str(scope_id or "").strip()
    clean_session = str(session or "").strip().upper()
    clean_signal = str(source_signal_id or "").strip()
    clean_bar = str(signal_bar or "").strip()
    venues = sorted(
        {
            str(value or "").strip().upper()
            for value in expected_venues
            if str(value or "").strip()
        }
    )
    try:
        quantity = int(required_quantity)
        reference = float(reference_price) if reference_price is not None else None
        target = float(target_price) if target_price is not None else None
    except (TypeError, ValueError):
        quantity = 0
        reference = None
        target = None
    identity = {
        "trade_date": observed_at.date().isoformat(),
        "owner": decision.owner,
        "scope_id": clean_scope,
        "symbol": decision.symbol,
        "session": clean_session,
        "source_signal_id": clean_signal,
        "signal_bar": clean_bar,
    }
    observation_id = _blocked_entry_observation_id(identity)
    path = output_dir / observed_at.date().isoformat() / f"{observation_id}.json"
    if not (
        decision.blocked
        and decision.reason == "entry_blocked_market_weakness_active"
        and clean_scope
        and clean_session
        and clean_signal
        and clean_bar
        and quantity > 0
        and venues
    ):
        return {
            "status": "blocked_entry_observation_contract_invalid",
            "observation_id": observation_id,
            "path": str(path),
        }
    payload = {
        "schema": BLOCKED_ENTRY_OBSERVATION_SCHEMA,
        "observation_id": observation_id,
        **identity,
        "observed_at": observed_at.isoformat(),
        "listing_market": decision.listing_market,
        "expected_venues": venues,
        "reference_price": reference if reference and reference > 0 else None,
        "target_price": target if target and target > 0 else None,
        "required_quantity": quantity,
        "guard_observation_id": decision.observation_id,
        "guard_observation_as_of": decision.observation_as_of,
        "guard_policy_id": POLICY_ID,
        "decision_authority": POLICY_ID,
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "counterfactual_contract": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "horizons_minutes": [1, 3, 5, 10, 20, 30],
            "entry_price": "first_fresh_depth_backed_executable_best_ask",
            "exit_price": "fresh_depth_backed_executable_best_bid_at_horizon",
            "missing_data": "source_quality_blocked_no_imputation",
        },
    }
    payload["content_sha256"] = _blocked_entry_content_sha256(payload)
    try:
        if path.exists() or path.with_name(path.name + ".gz").exists():
            existing = read_json_object_strict(path)
            existing_errors = market_weakness_blocked_entry_contract_errors(
                existing,
                target_date=observed_at.date().isoformat(),
            )
            if existing_errors:
                return {
                    "status": "existing_immutable_observation_invalid",
                    "observation_id": observation_id,
                    "path": str(path),
                    "validation_errors": existing_errors,
                }
            immutable_fields = (
                "schema",
                "trade_date",
                "owner",
                "scope_id",
                "symbol",
                "session",
                "source_signal_id",
                "signal_bar",
                "listing_market",
                "expected_venues",
                "reference_price",
                "target_price",
                "required_quantity",
                "guard_observation_id",
                "guard_observation_as_of",
                "guard_policy_id",
                "decision_authority",
                "counterfactual_contract",
            )
            conflict_fields = [
                field
                for field in immutable_fields
                if existing.get(field) != payload.get(field)
            ]
            if conflict_fields:
                return {
                    "status": "existing_immutable_observation_conflict",
                    "observation_id": observation_id,
                    "path": str(path),
                    "conflict_fields": conflict_fields,
                }
            return {
                "status": "existing_immutable_observation",
                "observation_id": observation_id,
                "path": str(path),
                "content_sha256": existing.get("content_sha256"),
            }
        write_json_object_generation_safe(
            path,
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            trailing_newline=True,
        )
    except (OSError, TypeError, ValueError) as exc:
        return {
            "status": f"blocked_entry_observation_write_failed:{type(exc).__name__}",
            "observation_id": observation_id,
            "path": str(path),
        }
    return {
        "status": "recorded",
        "observation_id": observation_id,
        "path": str(path),
    }


def _enabled() -> bool:
    raw = os.getenv(ENABLE_ENV)
    if raw is None:
        return True
    return str(raw).strip().lower() not in {"0", "false", "no", "off", "disabled"}


def _logical_master_date(path: Path) -> date | None:
    name = path.name
    for suffix in (".json.gz", ".json"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    prefix = "micro_reversion_symbol_master_"
    if not name.startswith(prefix):
        return None
    try:
        return date.fromisoformat(name[len(prefix) :])
    except ValueError:
        return None


def _select_symbol_master(directory: Path, as_of: date) -> Path | None:
    candidates: list[tuple[date, Path]] = []
    for pattern in (
        "micro_reversion_symbol_master_*.json",
        "micro_reversion_symbol_master_*.json.gz",
    ):
        for path in directory.glob(pattern):
            source_date = _logical_master_date(path)
            if source_date is not None and source_date <= as_of:
                candidates.append((source_date, path))
    if not candidates:
        return None
    # Prefer the plain logical generation if both plain and gzip are present.
    return max(
        candidates,
        key=lambda item: (item[0], item[1].name.endswith(".json")),
    )[1]


@lru_cache(maxsize=8)
def _load_verified_master(path_text: str, mtime_ns: int) -> VerifiedSymbolMaster:
    del mtime_ns
    payload = read_json_object_strict(Path(path_text))
    source_date = _logical_master_date(Path(path_text))
    if source_date is None or payload.get("artifact_id") != (
        f"main-ai-economic-reference-{source_date.isoformat()}-symbol-master"
    ):
        raise ValueError("verified_symbol_master_artifact_identity_invalid")
    return VerifiedSymbolMaster.from_payload(payload, require_canonical_owner=True)


def _resolve_listing_market(
    symbol: str,
    *,
    as_of: date,
    symbol_master_dir: Path,
) -> tuple[str | None, str, str | None]:
    path = _select_symbol_master(symbol_master_dir, as_of)
    if path is None:
        return None, "verified_symbol_master_missing", None
    try:
        master = _load_verified_master(str(path), path.stat().st_mtime_ns)
        result = master.lookup(symbol, as_of=as_of)
    except (OSError, TypeError, ValueError):
        return None, "verified_symbol_master_invalid", str(path)
    if not result.economic_metadata_allowed or result.record is None:
        return None, f"symbol_market_{result.status.value}", str(path)
    market = result.record.listing_market.value
    if market not in SUPPORTED_LISTING_MARKETS:
        return None, "symbol_listing_market_unsupported", str(path)
    return market, "verified_symbol_market_loaded", str(path)


def _normalized_active_markets(value: object) -> tuple[tuple[str, ...], bool]:
    if not isinstance(value, list):
        return (), False
    normalized = tuple(
        sorted(
            {
                str(item).strip().upper()
                for item in value
                if str(item).strip().upper() in SUPPORTED_LISTING_MARKETS
            }
        )
    )
    return normalized, len(normalized) == len(value)


def _decision(
    *,
    blocked: bool,
    reason: str,
    symbol: str,
    owner: str,
    listing_market: str | None,
    phase: str = "",
    active_markets: tuple[str, ...] = (),
    session_key: str = "",
    observation_id: str = "",
    observation_as_of: str = "",
    source_status: str,
    state_path: Path,
    symbol_master_path: str | None = None,
) -> MarketWeaknessEntryDecision:
    return MarketWeaknessEntryDecision(
        blocked=blocked,
        reason=reason,
        symbol=symbol,
        owner=owner,
        listing_market=listing_market,
        phase=phase,
        active_markets=active_markets,
        session_key=session_key,
        observation_id=observation_id,
        observation_as_of=observation_as_of,
        source_status=source_status,
        state_path=str(state_path),
        symbol_master_path=symbol_master_path,
    )


def evaluate_market_weakness_entry_guard(
    *,
    symbol: object,
    owner: str,
    now: datetime,
    state_path: Path = DEFAULT_STATE_PATH,
    symbol_master_dir: Path = DEFAULT_SYMBOL_MASTER_DIR,
    listing_market: str | None = None,
) -> MarketWeaknessEntryDecision:
    """Return an entry veto/cancel authorization without mutating any state."""

    clean_symbol = str(symbol or "").strip().zfill(6)
    clean_owner = str(owner or "").strip().lower()
    observed_at = now.astimezone(KST)
    if clean_owner not in SUPPORTED_OWNERS:
        raise ValueError(f"market_weakness_entry_guard_owner_invalid:{owner}")
    if not _enabled():
        return _decision(
            blocked=False,
            reason="market_weakness_entry_guard_disabled",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            source_status="operator_rollback_disabled",
            state_path=state_path,
        )
    try:
        payload = read_json_object_strict(Path(state_path))
    except FileNotFoundError:
        return _decision(
            blocked=False,
            reason="market_weakness_state_not_available",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            source_status="state_missing",
            state_path=state_path,
        )
    except (OSError, TypeError, ValueError):
        return _decision(
            blocked=False,
            reason="market_weakness_state_not_available",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            source_status="state_invalid",
            state_path=state_path,
        )
    state = payload.get("market_weakness")
    if not isinstance(state, dict):
        return _decision(
            blocked=False,
            reason="market_weakness_state_not_available",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            source_status="market_weakness_state_missing",
            state_path=state_path,
        )
    session_key = str(state.get("session_key") or "")[:10]
    phase = str(state.get("phase") or "")
    observation_id = str(state.get("last_observation_id") or "")
    observation_as_of = str(state.get("last_observation_as_of") or "")
    active_markets, active_market_scope_valid = _normalized_active_markets(
        state.get("active_markets")
    )
    if session_key != observed_at.date().isoformat():
        return _decision(
            blocked=False,
            reason="market_weakness_state_not_current_session",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            phase=phase,
            active_markets=active_markets,
            session_key=session_key,
            observation_id=observation_id,
            observation_as_of=observation_as_of,
            source_status="state_session_mismatch",
            state_path=state_path,
        )
    latch_active = phase in {"active", "release_pending"}
    if latch_active and (not active_market_scope_valid or not active_markets):
        return _decision(
            blocked=True,
            reason="entry_blocked_market_weakness_state_invalid",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            phase=phase,
            active_markets=active_markets,
            session_key=session_key,
            observation_id=observation_id,
            observation_as_of=observation_as_of,
            source_status="active_latch_market_scope_invalid",
            state_path=state_path,
        )
    if not latch_active or not active_markets:
        return _decision(
            blocked=False,
            reason="market_weakness_latch_not_active",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=listing_market,
            phase=phase,
            active_markets=active_markets,
            session_key=session_key,
            observation_id=observation_id,
            observation_as_of=observation_as_of,
            source_status="current_session_latch_inactive",
            state_path=state_path,
        )
    normalized_market = str(listing_market or "").strip().upper() or None
    master_path: str | None = None
    market_source_status = "caller_verified_listing_market"
    if normalized_market not in SUPPORTED_LISTING_MARKETS:
        normalized_market, market_source_status, master_path = _resolve_listing_market(
            clean_symbol,
            as_of=observed_at.date(),
            symbol_master_dir=Path(symbol_master_dir),
        )
    if normalized_market is None:
        return _decision(
            blocked=True,
            reason="entry_blocked_market_weakness_symbol_market_unresolved",
            symbol=clean_symbol,
            owner=clean_owner,
            listing_market=None,
            phase=phase,
            active_markets=active_markets,
            session_key=session_key,
            observation_id=observation_id,
            observation_as_of=observation_as_of,
            source_status=market_source_status,
            state_path=state_path,
            symbol_master_path=master_path,
        )
    blocked = normalized_market in active_markets
    return _decision(
        blocked=blocked,
        reason=(
            "entry_blocked_market_weakness_active"
            if blocked
            else "market_weakness_active_other_market"
        ),
        symbol=clean_symbol,
        owner=clean_owner,
        listing_market=normalized_market,
        phase=phase,
        active_markets=active_markets,
        session_key=session_key,
        observation_id=observation_id,
        observation_as_of=observation_as_of,
        source_status=market_source_status,
        state_path=state_path,
        symbol_master_path=master_path,
    )
