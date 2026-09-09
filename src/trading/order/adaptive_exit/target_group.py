"""Shared-target quantity planning, never broker authority or lot-fill attribution.

The current live port is single-target/single-lot. These pure functions describe
the missing group contract for its existing source census and future owner
coordinator. A source receipt/hash, cancel ACK, or quantity delta cannot release
a live reservation. No implicit FIFO or proportional actual-fill allocation.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from .models import finite, positive_int
from .reducer import OrderKey
from .source import OwnerScope, validate_source_day

SCHEMA = "machine_adaptive_exit_target_group_v1"


def _digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _stamp(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError("target_group_naive_time")
    return int(dt.timestamp() * 1000)


@dataclass(frozen=True)
class TargetGroup:
    scope: OwnerScope
    episode_id: str
    target: OrderKey
    target_price: int
    # Immutable admitted BUY quantities, NOT a SELL-fill allocation rule.
    lots: tuple[tuple[str, OrderKey, int, int, float], ...]
    source_hash: str

    @property
    def quantity(self):
        return sum(row[2] for row in self.lots)

    def validate(self):
        if (
            not isinstance(self.scope, OwnerScope)
            or not isinstance(self.target, OrderKey)
            or not isinstance(self.episode_id, str)
            or not self.episode_id
            or not positive_int(self.target_price)
            or not _digest(self.source_hash)
            or not isinstance(self.lots, tuple)
            or len(self.lots) < 2
        ):
            raise ValueError("shared_target_group_identity_invalid")
        validate_source_day(self.target.trading_date)
        for row in self.lots:
            if (
                not isinstance(row, tuple)
                or len(row) != 5
                or not isinstance(row[0], str)
                or not row[0]
                or not isinstance(row[1], OrderKey)
                or row[1].trading_date != self.target.trading_date
                or row[1] == self.target
                or not positive_int(row[2])
                or not positive_int(row[3])
                or not finite(row[4])
                or row[4] <= 0
                or datetime.fromtimestamp(row[3] / 1000, ZoneInfo("Asia/Seoul"))
                .date()
                .isoformat()
                != self.target.trading_date
            ):
                raise ValueError("shared_target_lot_identity_invalid")
        if len({r[0] for r in self.lots}) != len(self.lots) or len(
            {r[1] for r in self.lots}
        ) != len(self.lots):
            raise ValueError("shared_target_duplicate_lot_or_buy_order")

    def to_payload(self):
        self.validate()
        payload = {"schema": SCHEMA, **asdict(self), "authority": dict(AUTHORITY)}
        return payload | {"canonical_sha256": canonical_sha256(payload)}


def group_from_observation(receipt, *, scope):
    """Validate a frozen target epoch without reconstructing old fills."""
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != "machine_adaptive_exit_target_observation_v1"
        or receipt.get("scope") != asdict(scope)
        or receipt.get("authority") != AUTHORITY
        or any(
            receipt.get("authority", {}).get(k) is not v for k, v in AUTHORITY.items()
        )
        or receipt.get("canonical_sha256") != canonical_sha256(receipt)
        or not isinstance(receipt.get("entry_policy"), dict)
        or not receipt["entry_policy"]
        or receipt.get("entry_policy_hash") != canonical_sha256(receipt["entry_policy"])
    ):
        raise ValueError("shared_target_source_binding_invalid")
    target, entries = receipt["target"], receipt["entries"]
    if not isinstance(entries, list) or len(entries) < 2:
        raise ValueError("shared_target_requires_multiple_lots")
    ack_at = _stamp(receipt["target_ack_observed_at"])
    if (
        datetime.fromtimestamp(ack_at / 1000, ZoneInfo("Asia/Seoul")).date().isoformat()
        != target["order_date"]
    ):
        raise ValueError("shared_target_ack_date_mismatch")
    lots, episodes = [], set()
    for entry in entries:
        clock = entry["first_fill_observation"]
        if (
            not isinstance(clock, dict)
            or clock.get("schema") != "machine_first_fill_observation_v1"
            or clock.get("status") != "first_fill_observed_not_exchange_time"
            or clock.get("timestamp_provenance")
            != "broker_reconciliation_observation_not_exchange_fill_time"
            or not positive_int(entry["quantity"])
            or entry["requested_quantity"] != entry["quantity"]
            or type(entry["requested_quantity"]) is not int
            or not finite(entry.get("price"))
            or entry["price"] <= 0
        ):
            raise ValueError("shared_target_full_fill_clock_required")
        first_at = _stamp(clock["first_observed_at"])
        if first_at > ack_at or (
            clock.get("last_zero_observed_at")
            and _stamp(clock["last_zero_observed_at"]) > first_at
        ):
            raise ValueError("shared_target_fill_ack_clock_conflict")
        lots.append(
            (
                entry["lot_id"],
                OrderKey(entry["order_date"], entry["order_no"]),
                entry["quantity"],
                first_at,
                entry["price"],
            )
        )
        episodes.add(entry["episode_id"])
    if len(episodes) != 1 or target["route"] != scope.route:
        raise ValueError("shared_target_episode_or_route_conflict")
    group = TargetGroup(
        scope,
        next(iter(episodes)),
        OrderKey(target["order_date"], target["order_no"]),
        target["price"],
        tuple(sorted(lots, key=lambda row: row[0])),
        receipt["canonical_sha256"],
    )
    group.validate()
    if type(target["quantity"]) is not int or group.quantity != target["quantity"]:
        raise ValueError("shared_target_quantity_not_conserved")
    return group


def plan_runner_release(
    group, *, runner_lot_ids, target_filled_qty, target_remaining_qty
):
    """Return capacity bounds, NOT a proposed order quantity.

    With pooled SELL fills there is no broker-level BUY-lot attribution. An
    frozen owner-accounting rule must resolve a non-degenerate interval before
    execution; waiting for broker BUY-lot labels is not a solution. The lower
    bound is not silently chosen as a smaller live order.
    """
    group.validate()
    if (
        not isinstance(runner_lot_ids, tuple)
        or not runner_lot_ids
        or any(not isinstance(x, str) for x in runner_lot_ids)
        or len(set(runner_lot_ids)) != len(runner_lot_ids)
        or not set(runner_lot_ids) < {r[0] for r in group.lots}
        or type(target_filled_qty) is not int
        or target_filled_qty < 0
        or type(target_remaining_qty) is not int
        or target_remaining_qty < 0
        or target_filled_qty + target_remaining_qty != group.quantity
    ):
        raise ValueError("shared_target_runner_or_initial_quantity_invalid")
    selected = sum(r[2] for r in group.lots if r[0] in runner_lot_ids)
    low, high = (
        max(0, selected - target_filled_qty),
        min(selected, target_remaining_qty),
    )
    return {
        "runner_lot_ids": list(runner_lot_ids),
        "runner_open_qty_lower_bound": low,
        "runner_open_qty_upper_bound": high,
        "allocation_status": "quantity_unambiguous"
        if low == high
        else "lot_fill_allocation_required",
        "cancel_quantity": None,
        "live_partial_cancel_supported": False,
        "authority": dict(AUTHORITY),
    }


@dataclass(frozen=True)
class CancelAccounting:
    """Normalized post-cancel quantities for offline/coordinator validation.

    This is not a REST parser or trusted live proof. A future adapter must bind
    dated/current/successor receipts and registry intent independently.
    """

    group_hash: str
    target: OrderKey
    cancel_order: OrderKey
    requested_qty: int
    confirmed_canceled_qty: int
    filled_before: int
    remaining_before: int
    filled_after: int
    remaining_after: int
    cancel_terminal_reconciled: bool
    source_hash: str


def reconcile_group_cancel(group, evidence):
    """Quantity algebra only: ACK/missing terminal releases zero authority."""
    group.validate()
    if (
        not isinstance(evidence, CancelAccounting)
        or evidence.group_hash != group.to_payload()["canonical_sha256"]
        or evidence.target != group.target
        or not isinstance(evidence.cancel_order, OrderKey)
        or evidence.cancel_order.trading_date != group.target.trading_date
        or evidence.cancel_order == group.target
        or not _digest(evidence.source_hash)
        or evidence.cancel_terminal_reconciled is not True
        or not positive_int(evidence.requested_qty)
        or any(
            type(v) is not int or v < 0
            for v in (
                evidence.confirmed_canceled_qty,
                evidence.filled_before,
                evidence.remaining_before,
                evidence.filled_after,
                evidence.remaining_after,
            )
        )
    ):
        raise ValueError("shared_target_exact_cancel_accounting_required")
    e = evidence
    if (
        e.filled_before + e.remaining_before != group.quantity
        or not e.filled_before <= e.filled_after <= group.quantity
        or not e.confirmed_canceled_qty <= e.requested_qty <= e.remaining_before
        or e.filled_after + e.remaining_after + e.confirmed_canceled_qty
        != group.quantity
        or e.remaining_after > e.remaining_before
    ):
        raise ValueError("shared_target_cancel_quantity_conflict")
    # The protected remainder does NOT require whole original-order terminal.
    # Retain group accounting, never assign target SELL fills to named BUY lots.
    payload = {
        "schema": "machine_adaptive_exit_group_cancel_accounting_v1",
        "group_hash": e.group_hash,
        "source_hash": e.source_hash,
        "accounting": asdict(e),
        "target_reserved_qty": e.remaining_after,
        "unreserved_qty": e.confirmed_canceled_qty,
        "owned_open_qty": group.quantity - e.filled_after,
        "actual_lot_fill_attribution": None,
        "runtime_reservation_release_allowed": False,
        "authority": dict(AUTHORITY),
    }
    return payload | {"canonical_sha256": canonical_sha256(payload)}
