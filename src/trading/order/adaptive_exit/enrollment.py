"""New-position admission and frozen-policy authority for original owners.

No broker call, registry mutation or separate custody store. The original
owner atomically persists the returned session AND enrollment receipt before
its adaptive loop can run. Services must still supply the original lifecycle
lock, fresh market/clock and all account/order/manual safety checks.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from src.trading.config.machine_adaptive_exit_activation import (
    _digest,
    _literal_contract,
    _require,
    _signed,
    aware_kst,
    read_plain,
    validate_applied,
)
from src.trading.config.machine_adaptive_exit_policy import (
    AUTHORITY,
    canonical_sha256,
    parse_exit_policy,
)
from src.trading.order.owner_custody_registry import (
    OwnerOrderContext,
    OwnerRegistryError,
)
from src.trading.order.tick_utils import get_tick_size
from .driver import DriverState, ExecutionBounds
from .models import DecisionState, Position, finite, positive_int
from .reducer import ExitState, OrderKey
from .runtime import OwnerSession
from .source import OwnerScope, normalize_position

ENROLLMENT_KEY = "adaptive_exit_enrollment"
SCHEMA = "machine_adaptive_exit_initial_enrollment_v1"


def _ms(value):
    return int(aware_kst(value).timestamp() * 1000)


def _construct(
    source,
    *,
    scope,
    context,
    target_intent_id,
    approved,
    publication_hash,
    started_at,
    admitted_at,
    valid_from,
    valid_until,
):
    _signed(source, "machine_adaptive_exit_target_observation_v1")
    _literal_contract(
        source.get("authority"), AUTHORITY, "target_observation_source_only_required"
    )
    _require(source.get("scope") == asdict(scope), "enrollment_source_scope_mismatch")
    _require(
        source.get("timestamp_provenance")
        == "local_broker_response_observation_not_exchange_time",
        "target_ack_observation_provenance_required",
    )
    entries, target = source.get("entries"), source.get("target")
    _require(
        isinstance(entries, list)
        and len(entries) == 1
        and isinstance(entries[0], dict)
        and isinstance(target, dict),
        "independent_target_lot_required",
    )
    entry = entries[0]
    _require(
        source.get("entry_policy_hash") == canonical_sha256(source["entry_policy"])
        and source["entry_policy_hash"] in approved["entry_policy_hashes"],
        "enrollment_entry_policy_mismatch",
    )
    _require(
        positive_int(entry.get("quantity"))
        and type(entry.get("requested_quantity")) is int
        and type(target.get("quantity")) is int
        and entry["quantity"] == entry["requested_quantity"] == target.get("quantity")
        and finite(entry.get("price"))
        and entry["price"] > 0,
        "enrollment_original_full_fill_required",
    )
    observation = entry.get("first_fill_observation")
    _require(
        isinstance(observation, dict)
        and observation.get("schema") == "machine_first_fill_observation_v1"
        and observation.get("status") == "first_fill_observed_not_exchange_time"
        and observation.get("timestamp_provenance")
        == "broker_reconciliation_observation_not_exchange_fill_time",
        "new_first_fill_observation_required",
    )
    first, ack, admitted, started = map(
        _ms,
        (
            observation["first_observed_at"],
            source["target_ack_observed_at"],
            admitted_at,
            started_at,
        ),
    )
    _require(
        _ms(valid_from) <= first <= ack <= admitted < _ms(valid_until)
        and started <= first
        and started <= admitted,
        "new_position_admission_clock_invalid",
    )
    zero = observation.get("last_zero_observed_at")
    _require(zero is None or _ms(zero) <= first, "first_fill_clock_regression")
    _require(
        first <= _ms(observation["last_observed_at"]) <= admitted,
        "first_fill_observation_clock_invalid",
    )
    day = aware_kst(admitted_at).date().isoformat()
    _require(
        entry.get("order_date") == target.get("order_date") == day
        and target.get("route") == scope.route,
        "new_target_date_or_route_invalid",
    )
    buy = OrderKey(entry["order_date"], entry["order_no"])
    sell = OrderKey(target["order_date"], target["order_no"])
    _require(
        all(
            k.order_no.isascii() and k.order_no.isdigit() and int(k.order_no) > 0
            for k in (buy, sell)
        ),
        "exact_numeric_broker_order_required",
    )
    _require(buy != sell, "entry_target_order_collision")
    context.validate()
    _require(
        context.owner_type
        == {"widget": "widget_auto_trade", "episode": "episode"}[scope.owner],
        "enrollment_owner_type_mismatch",
    )
    cost = approved["execution_cost_guard"]
    position = Position(
        scope.owner,
        scope.key,
        context.position_id,
        entry["lot_id"],
        source["canonical_sha256"],
        first,
        entry["quantity"],
        entry["price"],
        target["price"],
        cost["round_trip_cost_pct"],
        cost["source_sha256"],
        get_tick_size(entry["price"]),
    )
    normalize_position(asdict(position), scope=scope)
    policy = parse_exit_policy(approved["policy"])
    session = OwnerSession(
        policy,
        position,
        ExecutionBounds(**approved["execution_bounds"]),
        context,
        target_intent_id,
        publication_hash,
        DriverState(
            ExitState(
                scope.owner,
                context.position_id,
                position.lot_id,
                policy.policy_hash,
                position.position_epoch,
                sell,
                position.open_qty,
            ),
            DecisionState(
                policy.policy_hash, position.position_epoch, first, position.open_qty
            ),
        ),
    )
    session.validate()
    return session


def validate_registered_admission(session, source, registry):
    """Read exact original custody; admission must never create/migrate it."""
    scope = OwnerScope(**source["scope"])
    entry, target = source["entries"][0], source["target"]
    for side, order, filled in (("BUY", entry, entry["quantity"]), ("SELL", target, 0)):
        row = registry.assert_owner(
            context=session.context,
            order_date=order["order_date"],
            broker_order_no=order["order_no"],
        )
        _require(
            row.get("symbol") == scope.symbol
            and row.get("route") == scope.route
            and row.get("side") == side
            and row.get("action") == "NEW"
            and row.get("quantity") == order["quantity"]
            and row.get("filled_qty", 0) == filled
            and row.get("state") in {"ORDER_BOUND", "ORDER_PARTIAL", "ORDER_TERMINAL"}
            and not row.get("migration_evidence_sha256")
            and (
                side != "SELL"
                or (
                    row.get("state") == "ORDER_BOUND"
                    and row.get("intent_id") == session.target_intent_id
                    and row.get("client_intent_id") == session.context.client_intent_id
                )
            ),
            "enrollment_registered_original_order_mismatch",
        )


class EnrollmentReloadRequired(RuntimeError):
    """An owner save may have published; no further writes before reload."""


@dataclass(frozen=True)
class InitialPolicyAdmission:
    policy_path: Path
    envelope_path: Path
    expected_envelope_sha256: str
    runtime_code_sha256: str
    started_at: datetime

    def _read(self):
        approval = read_plain(self.envelope_path)
        applied = read_plain(self.policy_path)
        validate_applied(
            applied.payload,
            envelope=approval.payload,
            expected_sha256=self.expected_envelope_sha256,
            runtime_code_sha256=self.runtime_code_sha256,
        )
        _require(
            read_plain(self.envelope_path) == approval
            and read_plain(self.policy_path) == applied,
            "admission_artifact_changed",
        )
        return approval.payload, applied.payload

    def prepare(
        self,
        *,
        source_receipt,
        context: OwnerOrderContext,
        target_intent_id: str,
        now: datetime,
    ):
        """Return a proposal for the owner's atomic store, not a broker action."""
        envelope, applied = self._read()
        scope = OwnerScope(**source_receipt["scope"])
        approved = envelope["scopes"].get(scope.key)
        _require(approved is not None, "new_target_scope_not_selected")
        session = _construct(
            source_receipt,
            scope=scope,
            context=context,
            target_intent_id=target_intent_id,
            approved=approved,
            publication_hash=applied["publication_receipt"]["canonical_sha256"],
            started_at=self.started_at,
            admitted_at=now,
            valid_from=envelope["valid_from"],
            valid_until=envelope["valid_until"],
        )
        receipt = {
            "schema": SCHEMA,
            "envelope_sha256": self.expected_envelope_sha256,
            "applied_sha256": applied["canonical_sha256"],
            "binding_sha256": session.binding_hash,
            "started_at": aware_kst(self.started_at).isoformat(),
            "admitted_at": aware_kst(now).isoformat(),
            "target_observation": deepcopy(source_receipt),
            "clock_basis": "local_first_fill_observation_not_exchange_fill_time",
            "actual_order_submitted_by_enrollment": False,
        }
        receipt["canonical_sha256"] = canonical_sha256(receipt)
        return session, receipt

    def authorize(self, binding, receipt, *, now: datetime) -> bool:
        """Revalidate retained sessions after restart/expiry without re-enrolling."""
        try:
            envelope, applied = self._read()
            _signed(receipt, SCHEMA)
            _require(
                set(receipt)
                == {
                    "schema",
                    "envelope_sha256",
                    "applied_sha256",
                    "binding_sha256",
                    "started_at",
                    "admitted_at",
                    "target_observation",
                    "clock_basis",
                    "actual_order_submitted_by_enrollment",
                    "canonical_sha256",
                },
                "enrollment_receipt_fields_invalid",
            )
            _require(
                receipt["envelope_sha256"] == self.expected_envelope_sha256
                and receipt["applied_sha256"] == applied["canonical_sha256"]
                and receipt["binding_sha256"] == canonical_sha256(binding)
                and receipt["actual_order_submitted_by_enrollment"] is False
                and receipt["clock_basis"]
                == "local_first_fill_observation_not_exchange_fill_time"
                and aware_kst(receipt["admitted_at"]) <= aware_kst(now),
                "enrollment_receipt_binding_invalid",
            )
            source = receipt["target_observation"]
            scope = OwnerScope(**source["scope"])
            expected = _construct(
                source,
                scope=scope,
                context=OwnerOrderContext(**binding["context"]),
                target_intent_id=binding["target_intent_id"],
                approved=envelope["scopes"][scope.key],
                publication_hash=applied["publication_receipt"]["canonical_sha256"],
                started_at=receipt["started_at"],
                admitted_at=receipt["admitted_at"],
                valid_from=envelope["valid_from"],
                valid_until=envelope["valid_until"],
            )
            return canonical_sha256(expected.binding) == canonical_sha256(binding)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            OwnerRegistryError,
        ):
            return False


@dataclass(frozen=True)
class PolicyAdmissionCatalog:
    """Explicit generation routing, not automatic policy discovery/approval.

    Only ``current`` may admit a new position. Retained generations may only
    revalidate their already persisted enrollment receipts. ``current=None``
    disables new enrollment without discarding existing managers. Each entry
    keeps separate immutable files; no latest/date fallback or file writes.

    All entries must be approved for the caller's same verified code generation.
    This does not approve a code migration or certify overnight broker custody.
    """

    runtime_code_sha256: str
    current: InitialPolicyAdmission | None
    retained: tuple[InitialPolicyAdmission, ...] = ()

    def __post_init__(self):
        _require(
            _digest(self.runtime_code_sha256)
            and (
                self.current is None or isinstance(self.current, InitialPolicyAdmission)
            )
            and isinstance(self.retained, tuple)
            and all(isinstance(x, InitialPolicyAdmission) for x in self.retained),
            "policy_catalog_configuration_invalid",
        )
        generations = self._generations()
        _require(bool(generations), "policy_catalog_generations_required")
        hashes, paths = set(), set()
        for admission in generations:
            digest = admission.expected_envelope_sha256
            _require(
                _digest(digest)
                and digest not in hashes
                and admission.runtime_code_sha256 == self.runtime_code_sha256,
                "policy_catalog_generation_pin_invalid",
            )
            hashes.add(digest)
            for path in (admission.policy_path, admission.envelope_path):
                _require(isinstance(path, Path), "policy_catalog_path_invalid")
                resolved = path.resolve()
                _require(resolved not in paths, "policy_catalog_generation_path_alias")
                paths.add(resolved)

    def _generations(self):
        return (() if self.current is None else (self.current,)) + self.retained

    def prepare(self, *, source_receipt, context, target_intent_id, now):
        _require(self.current is not None, "new_position_admission_disabled")
        # Never try an expired/retained policy if the current policy rejects it.
        return self.current.prepare(
            source_receipt=source_receipt,
            context=context,
            target_intent_id=target_intent_id,
            now=now,
        )

    def authorize(self, binding, receipt, *, now):
        if not isinstance(receipt, dict):
            return False
        digest = receipt.get("envelope_sha256")
        if not _digest(digest):
            return False
        for admission in self._generations():
            if admission.expected_envelope_sha256 == digest:
                # Full frozen-source/binding validation, not hash-only authority.
                # A missing unrelated current generation must not stop this one.
                return admission.authorize(binding, receipt, now=now)
        return False
