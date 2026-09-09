"""Strict, shared exit input normalization. No broker or market-data requests.

One scope is an owner/profile/symbol/route/session, not a selected performance
subset. An episode can contain several independently protected lots. Source
receipts must come from their owner; legacy minute-bar anchors cannot invent
the first broker fill, target ACK, or post-target ordered path.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from copy import deepcopy
from datetime import date, datetime
from typing import Mapping

from .models import Clock, Position, Snapshot, finite, positive_int


@dataclass(frozen=True, order=True)
class OwnerScope:
    owner: str
    profile: str
    symbol: str
    route: str
    session: str

    def __post_init__(self):
        if (
            self.owner not in ("widget", "episode")
            or not self.profile
            or not self.session
            or not self.symbol.isascii()
            or not self.symbol.isdigit()
            or len(self.symbol) != 6
            or self.route not in ("KRX", "NXT", "SOR")
            or any("|" in v for v in asdict(self).values())
        ):
            raise ValueError("invalid_owner_scope")

    @property
    def key(self) -> str:
        return "|".join(asdict(self).values())


def normalize_position(payload: Mapping, *, scope: OwnerScope) -> Position:
    if not isinstance(payload, Mapping):
        raise ValueError("position_not_mapping")
    try:
        position = Position(**payload)
    except (TypeError, KeyError) as exc:
        raise ValueError("position_schema_invalid") from exc
    if (
        position.owner_id != scope.owner
        or position.scope_key != scope.key
        or any(
            not isinstance(v, str) or not v
            for v in (
                position.episode_id,
                position.lot_id,
                position.position_epoch,
                position.cost_contract_hash,
            )
        )
        or not positive_int(position.first_fill_at_ms)
        or not positive_int(position.open_qty)
        or any(
            not finite(v) or v <= 0
            for v in (
                position.entry_price,
                position.original_target,
                position.tick_size,
            )
        )
        or position.original_target <= position.entry_price
        or not finite(position.round_trip_cost_pct)
        or position.round_trip_cost_pct < 0
    ):
        raise ValueError("position_identity_price_quantity_or_cost_invalid")
    return position


def normalize_observation(
    payload: Mapping, *, position: Position
) -> tuple[Clock, Snapshot]:
    """Accept only normalized receipts, not raw FID guesses or horizon marks."""
    try:
        clock = Clock(**payload["clock"])
        raw = dict(payload["snapshot"])
        raw["bid_levels"] = tuple(tuple(level) for level in raw["bid_levels"])
        snapshot = Snapshot(**raw)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("observation_schema_invalid") from exc
    if (
        snapshot.scope_key != position.scope_key
        or snapshot.position_epoch != position.position_epoch
    ):
        raise ValueError("observation_scope_or_epoch_mismatch")
    return clock, snapshot


def catalog_from_owner_inventories(
    widget_symbols: Mapping,
    episode_profiles: Mapping,
    *,
    errors: list[str] | None = None,
) -> tuple[OwnerScope, ...]:
    """Use the existing producer's complete catalog, including zero-anchor rows.

    Research-only symbols and quarantined profiles remain visible in the
    denominator. Catalog inclusion grants neither entry nor exit authority.
    """
    scopes: set[OwnerScope] = set()
    for owner, inventory in (("widget", widget_symbols), ("episode", episode_profiles)):
        if not isinstance(inventory, Mapping):
            if errors is None:
                raise ValueError("owner_inventory_missing")
            errors.append(owner + ":owner_inventory_missing")
            continue
        for identity, row in inventory.items():
            if errors is not None:
                try:
                    singleton = {identity: row}
                    scopes.update(
                        catalog_from_owner_inventories(
                            singleton if owner == "widget" else {},
                            singleton if owner == "episode" else {},
                        )
                    )
                except (ValueError, TypeError, AttributeError) as exc:
                    errors.append(f"{owner}:{identity}:{exc}")
                continue
            if not isinstance(row, Mapping):
                raise ValueError("owner_inventory_row_invalid")
            symbol = row.get("symbol", identity if owner == "widget" else None)
            bindings = set()
            contexts = row.get("session_contexts")
            if owner == "widget" and isinstance(contexts, Mapping):
                for scope_id, context in contexts.items():
                    if (
                        not isinstance(context, Mapping)
                        or not isinstance(scope_id, str)
                        or ":" not in scope_id
                    ):
                        raise ValueError("widget_session_inventory_invalid")
                    session = scope_id.rsplit(":", 1)[-1]
                    for venue in context.get("expected_venues") or []:
                        bindings.add((scope_id, session, venue))
            else:
                session = row.get("session")
                for venue in row.get("expected_venues") or []:
                    bindings.add((str(identity), session, venue))
            if not bindings:
                raise ValueError("owner_route_session_inventory_missing")
            for profile, session, route in bindings:
                if not isinstance(session, str) or not session:
                    raise ValueError("owner_session_missing")
                scopes.add(
                    OwnerScope(
                        owner, str(profile), str(symbol), str(route), str(session)
                    )
                )
    return tuple(sorted(scopes))


def validate_source_day(value: str) -> date:
    result = date.fromisoformat(value)
    if result.isoformat() != value or result < date(2026, 6, 5):
        raise ValueError("invalid_or_prebaseline_source_day")
    return result


def record_first_fill_observation(
    record: dict, *, previous_filled_qty: int, filled_qty: int, observed_at: str
) -> None:
    """Additive owner instrumentation, never an exchange timestamp substitute.

    Existing filled inventory cannot acquire a fabricated new first-fill clock
    after deployment. Persisted first observation survives further partial fills
    and restart; a last exact zero-fill read bounds observation uncertainty.
    """
    field = "adaptive_exit_first_fill_observation"
    if field in record and not isinstance(record[field], dict):
        return  # Preserve corrupt original evidence; do not overwrite it.
    state = record.setdefault(
        field,
        {
            "schema": "machine_first_fill_observation_v1",
            "timestamp_provenance": "broker_reconciliation_observation_not_exchange_fill_time",
            "first_observed_at": None,
            "last_zero_observed_at": None,
            "last_observed_at": None,
            "status": "not_yet_observed",
        },
    )
    try:
        ts = datetime.fromisoformat(observed_at)
        if (
            state.get("schema") != "machine_first_fill_observation_v1"
            or state.get("timestamp_provenance")
            != "broker_reconciliation_observation_not_exchange_fill_time"
            or ts.tzinfo is None
            or any(
                type(v) is not int or v < 0 for v in (previous_filled_qty, filled_qty)
            )
            or filled_qty < previous_filled_qty
        ):
            raise ValueError("invalid_fill_observation")
        last = (
            state.get("last_observed_at")
            or state.get("first_observed_at")
            or state.get("last_zero_observed_at")
        )
        if last and ts < datetime.fromisoformat(last):
            raise ValueError("observation_time_regression")
    except (TypeError, ValueError):
        state["status"] = "observation_contract_invalid"
        return
    if state.get("status") == "observation_contract_invalid":
        return
    state["last_observed_at"] = observed_at
    if state.get("first_observed_at") is not None:
        return
    if previous_filled_qty > 0:
        state["status"] = "legacy_first_fill_unavailable"
    elif filled_qty > 0 and state.get("status") != "legacy_first_fill_unavailable":
        state["first_observed_at"] = observed_at
        state["status"] = "first_fill_observed_not_exchange_time"
    elif filled_qty == 0:
        state["last_zero_observed_at"] = observed_at


def record_target_observation(
    record: dict,
    *,
    target: Mapping,
    entries: list[dict],
    owner: str,
    profile: str,
    symbol: str,
    session: str,
    entry_policy: Mapping,
    observed_at: str,
) -> None:
    """Freeze accepted target/entry provenance in the existing owner's state.

    This is an additive source receipt, NOT an exit policy or a fill proof.
    A duplicate accepted order never overwrites its original lot/price basis.
    Failed instrumentation is explicit but cannot interrupt target management.
    """
    from src.trading.config.machine_adaptive_exit_policy import (
        AUTHORITY,
        canonical_sha256,
    )

    field = "adaptive_exit_target_observations"
    if field in record and not isinstance(record[field], dict):
        record["adaptive_exit_source_gap"] = "target_receipt_container_invalid"
        return
    try:
        scope = OwnerScope(owner, profile, symbol, str(target["route"]), session)
        stamp = datetime.fromisoformat(observed_at)
        if stamp.utcoffset() is None:
            raise ValueError("target_observation_naive_time")
        validate_source_day(str(target["order_date"]))
        if not isinstance(target["order_no"], str) or not target["order_no"]:
            raise ValueError("target_order_identity_missing")
        if not positive_int(target["quantity"]) or not positive_int(target["price"]):
            raise ValueError("target_price_or_quantity_invalid")
        if not entries or not isinstance(entry_policy, Mapping) or not entry_policy:
            raise ValueError("target_entry_binding_missing")
        payload = {
            "schema": "machine_adaptive_exit_target_observation_v1",
            "authority": dict(AUTHORITY),
            "scope": asdict(scope),
            "target": dict(target),
            "entries": deepcopy(entries),
            "entry_policy": deepcopy(dict(entry_policy)),
            "entry_policy_hash": canonical_sha256(entry_policy),
            "target_ack_observed_at": observed_at,
            "timestamp_provenance": "local_broker_response_observation_not_exchange_time",
        }
        payload["canonical_sha256"] = canonical_sha256(payload)
        key = str(target["order_date"]) + ":" + target["order_no"]
        receipts = record.setdefault(field, {})
        if key in receipts:
            previous = receipts[key]
            # A later poll changes neither the ACK time nor the frozen basis.
            comparable = dict(payload)
            if isinstance(previous, dict):
                comparable["target_ack_observed_at"] = previous.get(
                    "target_ack_observed_at"
                )
            if not isinstance(previous, dict) or (
                previous.get("canonical_sha256") != canonical_sha256(previous)
                or canonical_sha256(comparable) != canonical_sha256(previous)
            ):
                record["adaptive_exit_source_gap"] = "conflicting_target_observation"
            return
        receipts[key] = payload
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError) as exc:
        record["adaptive_exit_source_gap"] = f"target_observation_invalid:{exc}"
