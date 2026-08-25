"""Durable cost guard for offline micro-reversion provider replay.

This module has no provider client, credential loader, runtime-policy consumer,
or order authority.  It only validates a reviewed pricing artifact and issues
durable, append-only attempt reservations before an external caller performs a
network request.  Unknown outcomes keep their full reservation after a timeout
or crash; a caller must never infer that an un-settled reservation is reusable.
"""

from __future__ import annotations

import fcntl
import gzip
import hashlib
import json
import os
import secrets
import stat
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

PRICING_ARTIFACT_SCHEMA = "ai_provider_reviewed_pricing_v2"
PRICING_AUTHORITY = "offline_provider_cost_reference_only"
PUBLIC_RATE_BASIS = "provider_public_rate"
OPERATOR_ZERO_COST_BASIS = "operator_accounting_zero_cost"
LEDGER_RECORD_SCHEMA = "ai_provider_budget_ledger_record_v1"
LEDGER_MANIFEST_SCHEMA = "ai_provider_budget_ledger_manifest_v1"
BUDGET_SUMMARY_SCHEMA = "ai_provider_budget_summary_v1"
BUDGET_CONTRACT_SCHEMA = "ai_provider_budget_contract_v1"

USD_PER_MILLION = Decimal("1000000")
DAILY_ATTEMPT_CAP_MAX = 390
DAILY_USD_CAP_MAX = Decimal("1.0")
DAILY_PARENT_CAP_MAX = 130

_PRICING_ARTIFACT_FIELDS = frozenset(
    {
        "schema",
        "artifact_id",
        "artifact_content_sha256",
        "review_status",
        "reviewed_at",
        "effective_from",
        "effective_to",
        "pricing_basis",
        "raw_pricing_source_path",
        "raw_pricing_source_bytes_sha256",
        "raw_pricing_source_size_bytes",
        "prices",
        "decision_authority",
        "runtime_effect",
        "allowed_runtime_apply",
        "actual_order_submitted",
        "broker_order_forbidden",
    }
)
_PRICING_ROW_FIELDS = frozenset(
    {
        "provider",
        "model",
        "input_usd_per_million_tokens",
        "output_usd_per_million_tokens",
    }
)
_ATTEMPT_IDENTITY_FIELDS = frozenset(
    {
        "target_date",
        "parent_id",
        "request_id",
        "arm",
        "provider",
        "model",
        "attempt_number",
    }
)

AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "offline_provider_replay_cost_guard",
    "decision_authority": "offline_provider_replay_budget_only",
    "window_policy": "KST_execution_date_append_only_attempt_budget",
    "sample_floor": "not_applicable_operational_budget_guard",
    "primary_decision_metric": "committed_cost_usd",
    "source_quality_gate": (
        "reviewed_pricing_hash_effective_window_and_valid_ledger_chain"
    ),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "provider_route_change_allowed": False,
    "network_call_performed_by_module": False,
    "forbidden_uses": [
        "provider_route_or_model_change",
        "runtime_prompt_or_threshold_apply",
        "broker_order_submission_or_cancel",
        "quantity_or_cap_change",
        "hard_safety_or_stale_guard_bypass",
        "bot_restart",
        "credential_or_prompt_persistence",
        "retry_without_a_new_attempt_reservation",
    ],
}

_RECORD_COMMON_FIELDS = frozenset(
    {
        "schema",
        "sequence",
        "previous_record_sha256",
        "record_content_sha256",
        "event_type",
        "recorded_at",
        "execution_date",
        "reservation_id",
        "attempt_identity",
        "attempt_identity_sha256",
        "budget_contract",
        "budget_contract_sha256",
        "pricing_artifact_id",
        "pricing_artifact_content_sha256",
        "pricing_artifact_file_sha256",
        "raw_pricing_source_bytes_sha256",
        "raw_pricing_source_path",
        "raw_pricing_source_size_bytes",
        "pricing_effective_from",
        "pricing_effective_to",
        *AUTHORITY_CONTRACT,
    }
)
_RESERVATION_RECORD_FIELDS = _RECORD_COMMON_FIELDS | {
    "token_ceiling",
    "model_pricing",
    "reserved_cost_usd",
    "reservation_status",
    "unknown_or_crashed_call_refund_allowed",
}
_SETTLEMENT_RECORD_FIELDS = _RECORD_COMMON_FIELDS | {
    "actual_input_tokens",
    "actual_output_tokens",
    "actual_cost_usd",
    "reserved_cost_usd",
    "provider_response_sha256",
    "settlement_status",
    "actual_cost_exceeded_reservation",
    "actual_token_ceiling_exceeded",
    "actual_exceeded_reservation",
    "circuit_breaker_open",
}
_MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "manifest_content_sha256",
        "updated_at",
        "execution_date",
        "ledger_file",
        "ledger_size_bytes",
        "ledger_bytes_sha256",
        "record_count",
        "head_record_sha256",
        "budget_contract_sha256",
        *AUTHORITY_CONTRACT,
    }
)


class ProviderBudgetError(RuntimeError):
    """Base class for fail-closed provider-budget errors."""


class PricingArtifactError(ProviderBudgetError):
    """The reviewed pricing source is missing, stale, or invalid."""


class BudgetLedgerIntegrityError(ProviderBudgetError):
    """The append-only ledger or its manifest failed validation."""


class BudgetExceededError(ProviderBudgetError):
    """A new attempt would exceed its KST daily budget."""


class DuplicateAttemptError(ProviderBudgetError):
    """The exact provider attempt already has a durable reservation."""


class CircuitBreakerOpenError(ProviderBudgetError):
    """Actual provider usage exceeded a reservation."""


class SettlementError(ProviderBudgetError):
    """A provider attempt cannot be settled safely."""


class SingleWorkerRequiredError(ProviderBudgetError):
    """The bounded replay lane only permits a single provider worker."""


class _UnsafePathError(OSError):
    """A persistence path is a symlink, non-regular file, or unstable entry."""


@dataclass(frozen=True, slots=True)
class ModelPricing:
    provider: str
    model: str
    input_usd_per_million_tokens: Decimal
    output_usd_per_million_tokens: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider", _identifier(self.provider, field="provider").lower()
        )
        object.__setattr__(self, "model", _identifier(self.model, field="model"))
        for field in (
            "input_usd_per_million_tokens",
            "output_usd_per_million_tokens",
        ):
            value = getattr(self, field)
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError(f"{field} must be a non-negative finite Decimal")

    def cost(self, *, input_tokens: int, output_tokens: int) -> Decimal:
        _validate_nonnegative_int(input_tokens, field="input_tokens")
        _validate_nonnegative_int(output_tokens, field="output_tokens")
        precision = max(
            50,
            len(str(input_tokens))
            + len(self.input_usd_per_million_tokens.as_tuple().digits)
            + 8,
            len(str(output_tokens))
            + len(self.output_usd_per_million_tokens.as_tuple().digits)
            + 8,
        )
        with localcontext() as context:
            context.prec = precision
            return (
                Decimal(input_tokens) * self.input_usd_per_million_tokens
                + Decimal(output_tokens) * self.output_usd_per_million_tokens
            ) / USD_PER_MILLION

    def as_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
            "input_usd_per_million_tokens": _decimal_text(
                self.input_usd_per_million_tokens
            ),
            "output_usd_per_million_tokens": _decimal_text(
                self.output_usd_per_million_tokens
            ),
        }


@dataclass(frozen=True, slots=True)
class ReviewedPricingArtifact:
    artifact_id: str
    artifact_path: Path
    artifact_file_sha256: str
    artifact_content_sha256: str
    effective_from: date
    effective_to: date
    reviewed_at: str
    pricing_basis: str
    raw_source_path: Path
    raw_source_bytes_sha256: str
    raw_source_size_bytes: int
    prices: tuple[ModelPricing, ...]

    def price_for(self, provider: object, model: object) -> ModelPricing:
        normalized_provider = _identifier(provider, field="provider").lower()
        normalized_model = _identifier(model, field="model")
        matches = [
            price
            for price in self.prices
            if price.provider == normalized_provider and price.model == normalized_model
        ]
        if len(matches) != 1:
            raise PricingArtifactError(
                f"reviewed_pricing_model_missing:{normalized_provider}:{normalized_model}"
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class ProviderModelSelection:
    """One logical pricing key and its exact provider transport identity.

    Bedrock pricing is keyed by the stable logical model family while provider
    calls use a physical ``model_id`` in one AWS region.  Keeping both values in
    the batch preflight prevents a priced logical alias from hiding an
    unreviewed physical route.
    """

    provider: str
    model: str
    physical_model_id: str | None = None
    region_name: str | None = None

    def __post_init__(self) -> None:
        provider = _identifier(self.provider, field="provider").lower()
        model = _identifier(self.model, field="model")
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "model", model)
        if provider == "bedrock":
            if self.physical_model_id is None or self.region_name is None:
                raise ValueError(
                    "bedrock pricing selection requires physical_model_id and "
                    "region_name"
                )
            object.__setattr__(
                self,
                "physical_model_id",
                _identifier(self.physical_model_id, field="physical_model_id"),
            )
            object.__setattr__(
                self,
                "region_name",
                _identifier(self.region_name, field="region_name").lower(),
            )
        elif self.physical_model_id is not None or self.region_name is not None:
            raise ValueError(
                "physical_model_id and region_name are reserved for bedrock"
            )

    def as_dict(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "model": self.model,
            "physical_model_id": self.physical_model_id,
            "region_name": self.region_name,
        }


@dataclass(frozen=True, slots=True)
class TokenCeiling:
    input_utf8_bytes: int
    input_token_ceiling: int
    max_output_tokens: int

    def __post_init__(self) -> None:
        _validate_positive_int(self.input_utf8_bytes, field="input_utf8_bytes")
        _validate_positive_int(self.input_token_ceiling, field="input_token_ceiling")
        _validate_positive_int(self.max_output_tokens, field="max_output_tokens")
        if self.input_utf8_bytes != self.input_token_ceiling:
            raise ValueError(
                "input token ceiling must equal the UTF-8 byte upper bound"
            )

    @property
    def total_token_ceiling(self) -> int:
        return self.input_token_ceiling + self.max_output_tokens

    def as_dict(self) -> dict[str, int | str]:
        return {
            "estimator": "utf8_bytes_as_input_token_upper_bound_v1",
            "input_utf8_bytes": self.input_utf8_bytes,
            "input_token_ceiling": self.input_token_ceiling,
            "max_output_tokens": self.max_output_tokens,
            "total_token_ceiling": self.total_token_ceiling,
        }


@dataclass(frozen=True, slots=True)
class AttemptIdentity:
    target_date: str
    parent_id: str
    request_id: str
    arm: str
    provider: str
    model: str
    attempt_number: int

    def __post_init__(self) -> None:
        if not isinstance(self.target_date, str):
            raise ValueError("target_date must be YYYY-MM-DD")
        try:
            normalized_date = date.fromisoformat(self.target_date)
        except ValueError as exc:
            raise ValueError("target_date must be YYYY-MM-DD") from exc
        object.__setattr__(self, "target_date", normalized_date.isoformat())
        for field in ("parent_id", "request_id", "arm", "provider", "model"):
            value = _identifier(getattr(self, field), field=field)
            if field == "provider":
                value = value.lower()
            object.__setattr__(self, field, value)
        _validate_positive_int(self.attempt_number, field="attempt_number")

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_date": self.target_date,
            "parent_id": self.parent_id,
            "request_id": self.request_id,
            "arm": self.arm,
            "provider": self.provider,
            "model": self.model,
            "attempt_number": self.attempt_number,
        }

    @property
    def content_sha256(self) -> str:
        return _sha256_json(self.as_dict())


@dataclass(frozen=True, slots=True)
class ReservationPermit:
    reservation_id: str
    attempt_identity_sha256: str
    sequence: int
    execution_date: str
    reserved_cost_usd: Decimal
    provider_call_budget_reserved: bool = True
    network_call_performed_by_module: bool = False


@dataclass(frozen=True, slots=True)
class SettlementReceipt:
    reservation_id: str
    attempt_identity_sha256: str
    sequence: int
    actual_cost_usd: Decimal
    exceeded_reservation: bool
    circuit_breaker_open: bool
    network_call_performed_by_module: bool = False


@dataclass(slots=True)
class _LedgerState:
    records: list[dict[str, Any]]
    reservations: dict[str, dict[str, Any]]
    settlements: dict[str, dict[str, Any]]
    ledger_bytes: bytes
    directory_fd: int

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def head_sha256(self) -> str | None:
        if not self.records:
            return None
        return str(self.records[-1]["record_content_sha256"])


def pricing_artifact_content_sha256(payload: Mapping[str, Any]) -> str:
    """Return the canonical hash declared by a reviewed pricing artifact."""

    content = {
        key: value for key, value in payload.items() if key != "artifact_content_sha256"
    }
    return _sha256_json(content)


def load_reviewed_pricing_artifact(
    path: Path,
    *,
    as_of_date: date,
) -> ReviewedPricingArtifact:
    """Load and fully verify one effective-dated provider pricing artifact."""

    if not isinstance(as_of_date, date) or isinstance(as_of_date, datetime):
        raise PricingArtifactError("reviewed_pricing_as_of_date_invalid")
    artifact_path = _absolute_path_without_symlink_resolution(path)
    try:
        artifact_bytes = _read_regular_file_nofollow(artifact_path)
    except OSError as exc:
        raise PricingArtifactError("reviewed_pricing_artifact_unreadable") from exc
    try:
        payload = _json_loads_strict(artifact_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PricingArtifactError("reviewed_pricing_artifact_json_invalid") from exc
    if not isinstance(payload, dict):
        raise PricingArtifactError("reviewed_pricing_artifact_not_object")
    if payload.get("schema") != PRICING_ARTIFACT_SCHEMA:
        raise PricingArtifactError("reviewed_pricing_artifact_schema_invalid")
    if set(payload) != _PRICING_ARTIFACT_FIELDS:
        raise PricingArtifactError("reviewed_pricing_artifact_fields_invalid")
    if payload.get("review_status") != "reviewed":
        raise PricingArtifactError("reviewed_pricing_review_status_invalid")
    if payload.get("decision_authority") != PRICING_AUTHORITY:
        raise PricingArtifactError("reviewed_pricing_authority_invalid")
    for field, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if payload.get(field) is not expected:
            raise PricingArtifactError(f"reviewed_pricing_authority_invalid:{field}")

    try:
        artifact_id = _identifier(payload.get("artifact_id"), field="artifact_id")
    except ValueError as exc:
        raise PricingArtifactError("reviewed_pricing_artifact_id_invalid") from exc
    declared_content_hash = _sha256_field(
        payload.get("artifact_content_sha256"),
        field="artifact_content_sha256",
        error_type=PricingArtifactError,
    )
    if declared_content_hash != pricing_artifact_content_sha256(payload):
        raise PricingArtifactError("reviewed_pricing_content_sha256_mismatch")
    reviewed_timestamp = _aware_timestamp(
        payload.get("reviewed_at"),
        field="reviewed_at",
        error_type=PricingArtifactError,
    )
    if reviewed_timestamp.astimezone(KST).date() > as_of_date:
        raise PricingArtifactError("reviewed_pricing_reviewed_at_in_future")
    reviewed_at = reviewed_timestamp.isoformat()
    pricing_basis = str(payload.get("pricing_basis") or "").strip()
    if pricing_basis not in {PUBLIC_RATE_BASIS, OPERATOR_ZERO_COST_BASIS}:
        raise PricingArtifactError("reviewed_pricing_basis_invalid")
    try:
        effective_from = date.fromisoformat(str(payload.get("effective_from") or ""))
        effective_to = date.fromisoformat(str(payload.get("effective_to") or ""))
    except ValueError as exc:
        raise PricingArtifactError("reviewed_pricing_effective_window_invalid") from exc
    if effective_to < effective_from:
        raise PricingArtifactError("reviewed_pricing_effective_window_reversed")
    if as_of_date < effective_from:
        raise PricingArtifactError("reviewed_pricing_not_yet_effective")
    if as_of_date > effective_to:
        raise PricingArtifactError("reviewed_pricing_stale")

    try:
        declared_source_path = _identifier(
            payload.get("raw_pricing_source_path"), field="raw_pricing_source_path"
        )
    except ValueError as exc:
        raise PricingArtifactError("reviewed_pricing_raw_source_path_invalid") from exc
    source_path = Path(declared_source_path)
    if not source_path.is_absolute():
        source_path = artifact_path.parent / source_path
    source_path = _absolute_path_without_symlink_resolution(source_path)
    try:
        source_hash, source_size = _file_sha256_and_size(source_path)
    except OSError as exc:
        raise PricingArtifactError("reviewed_pricing_raw_source_unreadable") from exc
    declared_source_hash = _sha256_field(
        payload.get("raw_pricing_source_bytes_sha256"),
        field="raw_pricing_source_bytes_sha256",
        error_type=PricingArtifactError,
    )
    declared_source_size = payload.get("raw_pricing_source_size_bytes")
    _validate_positive_int(
        declared_source_size,
        field="raw_pricing_source_size_bytes",
        error_type=PricingArtifactError,
    )
    if source_size != declared_source_size:
        raise PricingArtifactError("reviewed_pricing_raw_source_size_mismatch")
    if source_hash != declared_source_hash:
        raise PricingArtifactError("reviewed_pricing_raw_source_sha256_mismatch")

    raw_prices = payload.get("prices")
    if not isinstance(raw_prices, list) or not raw_prices:
        raise PricingArtifactError("reviewed_pricing_prices_missing")
    prices: list[ModelPricing] = []
    seen: set[tuple[str, str]] = set()
    for raw_price in raw_prices:
        if not isinstance(raw_price, dict):
            raise PricingArtifactError("reviewed_pricing_price_row_invalid")
        if set(raw_price) != _PRICING_ROW_FIELDS:
            raise PricingArtifactError("reviewed_pricing_price_fields_invalid")
        try:
            provider = _identifier(raw_price.get("provider"), field="provider").lower()
            model = _identifier(raw_price.get("model"), field="model")
        except ValueError as exc:
            raise PricingArtifactError(
                "reviewed_pricing_provider_model_invalid"
            ) from exc
        key = (provider, model)
        if key in seen:
            raise PricingArtifactError("reviewed_pricing_provider_model_duplicate")
        seen.add(key)
        input_rate = _nonnegative_decimal(
            raw_price.get("input_usd_per_million_tokens"),
            field="input_usd_per_million_tokens",
            error_type=PricingArtifactError,
        )
        output_rate = _nonnegative_decimal(
            raw_price.get("output_usd_per_million_tokens"),
            field="output_usd_per_million_tokens",
            error_type=PricingArtifactError,
        )
        prices.append(
            ModelPricing(
                provider=provider,
                model=model,
                input_usd_per_million_tokens=input_rate,
                output_usd_per_million_tokens=output_rate,
            )
        )
    all_rates = [
        value
        for price in prices
        for value in (
            price.input_usd_per_million_tokens,
            price.output_usd_per_million_tokens,
        )
    ]
    if pricing_basis == PUBLIC_RATE_BASIS and any(value <= 0 for value in all_rates):
        raise PricingArtifactError("reviewed_public_pricing_rate_must_be_positive")
    if pricing_basis == OPERATOR_ZERO_COST_BASIS and any(
        value != 0 for value in all_rates
    ):
        raise PricingArtifactError("reviewed_operator_zero_cost_rate_must_be_zero")
    return ReviewedPricingArtifact(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        artifact_file_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        artifact_content_sha256=declared_content_hash,
        effective_from=effective_from,
        effective_to=effective_to,
        reviewed_at=reviewed_at,
        pricing_basis=pricing_basis,
        raw_source_path=source_path,
        raw_source_bytes_sha256=declared_source_hash,
        raw_source_size_bytes=declared_source_size,
        prices=tuple(prices),
    )


def conservative_token_ceiling(
    *inputs: str | bytes,
    max_output_tokens: int,
) -> TokenCeiling:
    """Bound input tokens by exact UTF-8 bytes and output by the declared cap.

    The helper intentionally returns counts only.  Prompt or payload content is
    never retained in a budget record or summary.
    """

    _validate_positive_int(max_output_tokens, field="max_output_tokens")
    byte_count = 0
    for value in inputs:
        if isinstance(value, str):
            byte_count += len(value.encode("utf-8"))
        elif isinstance(value, bytes):
            byte_count += len(value)
        else:
            raise TypeError("token ceiling inputs must be str or bytes")
    if byte_count <= 0:
        raise ValueError("token ceiling input must not be empty")
    return TokenCeiling(
        input_utf8_bytes=byte_count,
        input_token_ceiling=byte_count,
        max_output_tokens=max_output_tokens,
    )


def validate_batch_pricing_coverage(
    pricing: ReviewedPricingArtifact,
    selections: Iterable[ProviderModelSelection],
) -> tuple[ProviderModelSelection, ...]:
    """Fail closed unless every selected batch route has reviewed pricing.

    This is deliberately a batch preflight rather than a per-attempt fallback.
    The caller must build all possible primary/failback selections, invoke this
    helper before constructing a provider client, and retain the returned
    normalized census as execution provenance.
    """

    if not isinstance(pricing, ReviewedPricingArtifact):
        raise PricingArtifactError("reviewed_pricing_artifact_required")
    try:
        selected = tuple(selections)
    except TypeError as exc:
        raise PricingArtifactError("reviewed_pricing_batch_selection_invalid") from exc
    if not selected:
        raise PricingArtifactError("reviewed_pricing_batch_selection_missing")

    normalized: dict[
        tuple[str, str, str | None, str | None], ProviderModelSelection
    ] = {}
    logical_routes: dict[tuple[str, str], tuple[str | None, str | None]] = {}
    for selection in selected:
        if not isinstance(selection, ProviderModelSelection):
            raise PricingArtifactError("reviewed_pricing_batch_selection_invalid")
        try:
            pricing.price_for(selection.provider, selection.model)
        except (TypeError, ValueError) as exc:
            raise PricingArtifactError(
                "reviewed_pricing_batch_selection_invalid"
            ) from exc
        physical_route = (selection.physical_model_id, selection.region_name)
        logical_key = (selection.provider, selection.model)
        previous_route = logical_routes.setdefault(logical_key, physical_route)
        if previous_route != physical_route:
            raise PricingArtifactError(
                "reviewed_pricing_batch_physical_route_conflict:"
                f"{selection.provider}:{selection.model}"
            )
        key = (*logical_key, *physical_route)
        normalized[key] = selection
    return tuple(normalized[key] for key in sorted(normalized, key=_selection_sort_key))


class ProviderBudgetLedger:
    """Single-worker, hash-chained KST daily provider-attempt budget."""

    def __init__(
        self,
        *,
        ledger_path: Path,
        pricing: ReviewedPricingArtifact,
        execution_date: date,
        daily_attempt_cap: int,
        daily_usd_cap: Decimal | str | int | float,
        worker_count: int = 1,
    ) -> None:
        if (
            isinstance(worker_count, bool)
            or not isinstance(worker_count, int)
            or worker_count != 1
        ):
            raise SingleWorkerRequiredError("provider_budget_single_worker_required")
        if not isinstance(execution_date, date) or isinstance(execution_date, datetime):
            raise ValueError("execution_date must be a date")
        if not isinstance(pricing, ReviewedPricingArtifact):
            raise PricingArtifactError("reviewed_pricing_artifact_required")
        _validate_positive_int(daily_attempt_cap, field="daily_attempt_cap")
        normalized_usd_cap = _positive_decimal(
            daily_usd_cap,
            field="daily_usd_cap",
            error_type=ValueError,
        )
        if daily_attempt_cap > DAILY_ATTEMPT_CAP_MAX:
            raise ValueError("daily_attempt_cap exceeds reviewed maximum")
        if normalized_usd_cap > DAILY_USD_CAP_MAX:
            raise ValueError("daily_usd_cap exceeds reviewed maximum")
        if not pricing.effective_from <= execution_date <= pricing.effective_to:
            raise PricingArtifactError(
                "reviewed_pricing_not_effective_for_execution_date"
            )
        self.ledger_path = _absolute_path_without_symlink_resolution(ledger_path)
        self.manifest_path = self.ledger_path.with_suffix(".manifest.json")
        self.lock_path = self.ledger_path.with_suffix(".lock")
        self.pricing = pricing
        self.execution_date = execution_date
        self.daily_attempt_cap = daily_attempt_cap
        self.daily_usd_cap = normalized_usd_cap
        self._budget_contract = {
            "schema": BUDGET_CONTRACT_SCHEMA,
            "execution_date": execution_date.isoformat(),
            "daily_attempt_cap": daily_attempt_cap,
            "daily_usd_cap": _decimal_text(normalized_usd_cap),
            "pricing_artifact_content_sha256": pricing.artifact_content_sha256,
            "pricing_artifact_file_sha256": pricing.artifact_file_sha256,
            "pricing_basis": pricing.pricing_basis,
        }
        self._budget_contract_sha256 = _sha256_json(self._budget_contract)

    def reserve_attempt(
        self,
        identity: AttemptIdentity,
        *,
        token_ceiling: TokenCeiling,
        now: datetime | None = None,
    ) -> ReservationPermit:
        """Durably reserve one exact attempt before any network call."""

        timestamp = _kst_now(now)
        if timestamp.date() != self.execution_date:
            raise ProviderBudgetError(
                "provider_budget_reservation_execution_date_mismatch"
            )
        if not isinstance(identity, AttemptIdentity):
            raise TypeError("identity must be AttemptIdentity")
        if not isinstance(token_ceiling, TokenCeiling):
            raise TypeError("token_ceiling must be TokenCeiling")
        if date.fromisoformat(identity.target_date) > self.execution_date:
            raise ProviderBudgetError("provider_budget_target_date_in_future")
        price = self.pricing.price_for(identity.provider, identity.model)
        reserved_cost = price.cost(
            input_tokens=token_ceiling.input_token_ceiling,
            output_tokens=token_ceiling.max_output_tokens,
        )
        with self._locked_state() as state:
            identity_hash = identity.content_sha256
            if identity_hash in state.reservations:
                raise DuplicateAttemptError(
                    f"provider_budget_attempt_already_reserved:{identity_hash}"
                )
            if self._circuit_breaker_open(state):
                raise CircuitBreakerOpenError("provider_budget_circuit_breaker_open")
            if len(state.reservations) + 1 > self.daily_attempt_cap:
                raise BudgetExceededError("provider_budget_daily_attempt_cap_exceeded")
            parent_key = (identity.target_date, identity.parent_id)
            reserved_parent_keys = {
                (
                    str(record["attempt_identity"]["target_date"]),
                    str(record["attempt_identity"]["parent_id"]),
                )
                for record in state.reservations.values()
            }
            if (
                parent_key not in reserved_parent_keys
                and len(reserved_parent_keys) >= DAILY_PARENT_CAP_MAX
            ):
                raise BudgetExceededError("provider_budget_daily_parent_cap_exceeded")
            committed_cost = self._committed_cost(state)
            if committed_cost + reserved_cost > self.daily_usd_cap:
                raise BudgetExceededError("provider_budget_daily_usd_cap_exceeded")

            reservation_id = (
                "provider-reservation-"
                + _sha256_json(
                    {
                        "execution_date": self.execution_date.isoformat(),
                        "attempt_identity_sha256": identity_hash,
                        "pricing_artifact_content_sha256": (
                            self.pricing.artifact_content_sha256
                        ),
                    }
                )[:32]
            )
            event = {
                "event_type": "reservation",
                "recorded_at": timestamp.isoformat(),
                "execution_date": self.execution_date.isoformat(),
                "reservation_id": reservation_id,
                "attempt_identity": identity.as_dict(),
                "attempt_identity_sha256": identity_hash,
                "token_ceiling": token_ceiling.as_dict(),
                "model_pricing": price.as_dict(),
                "reserved_cost_usd": _decimal_text(reserved_cost),
                "reservation_status": "reserved_before_provider_call",
                "unknown_or_crashed_call_refund_allowed": False,
                **self._record_common(),
            }
            record = self._append_event(state, event, timestamp=timestamp)
            return ReservationPermit(
                reservation_id=reservation_id,
                attempt_identity_sha256=identity_hash,
                sequence=int(record["sequence"]),
                execution_date=self.execution_date.isoformat(),
                reserved_cost_usd=reserved_cost,
            )

    def settle_attempt(
        self,
        identity: AttemptIdentity,
        *,
        actual_input_tokens: int,
        actual_output_tokens: int,
        now: datetime | None = None,
        provider_response_sha256: str | None = None,
    ) -> SettlementReceipt:
        """Append actual usage; an over-reservation opens the lane breaker."""

        timestamp = _kst_now(now)
        if not isinstance(identity, AttemptIdentity):
            raise TypeError("identity must be AttemptIdentity")
        _validate_nonnegative_int(actual_input_tokens, field="actual_input_tokens")
        _validate_nonnegative_int(actual_output_tokens, field="actual_output_tokens")
        response_hash = None
        if provider_response_sha256 is not None:
            response_hash = _sha256_field(
                provider_response_sha256,
                field="provider_response_sha256",
                error_type=SettlementError,
            )
        price = self.pricing.price_for(identity.provider, identity.model)
        actual_cost = price.cost(
            input_tokens=actual_input_tokens,
            output_tokens=actual_output_tokens,
        )
        with self._locked_state() as state:
            identity_hash = identity.content_sha256
            reservation = state.reservations.get(identity_hash)
            if reservation is None:
                raise SettlementError("provider_budget_reservation_missing")
            if identity_hash in state.settlements:
                raise SettlementError("provider_budget_attempt_already_settled")
            reservation_timestamp = _aware_timestamp(
                reservation.get("recorded_at"),
                field="reservation_recorded_at",
                error_type=SettlementError,
            )
            if timestamp < reservation_timestamp:
                raise SettlementError("provider_budget_settlement_precedes_reservation")
            reserved_cost = _stored_decimal(
                reservation.get("reserved_cost_usd"), field="reserved_cost_usd"
            )
            reservation_ceiling = reservation["token_ceiling"]
            cost_exceeded = actual_cost > reserved_cost
            token_ceiling_exceeded = bool(
                actual_input_tokens > reservation_ceiling["input_token_ceiling"]
                or actual_output_tokens > reservation_ceiling["max_output_tokens"]
            )
            exceeded_reservation = cost_exceeded or token_ceiling_exceeded
            event = {
                "event_type": "settlement",
                "recorded_at": timestamp.isoformat(),
                "execution_date": self.execution_date.isoformat(),
                "reservation_id": reservation["reservation_id"],
                "attempt_identity": identity.as_dict(),
                "attempt_identity_sha256": identity_hash,
                "actual_input_tokens": actual_input_tokens,
                "actual_output_tokens": actual_output_tokens,
                "actual_cost_usd": _decimal_text(actual_cost),
                "reserved_cost_usd": _decimal_text(reserved_cost),
                "provider_response_sha256": response_hash,
                "settlement_status": (
                    "actual_exceeded_reservation_circuit_breaker"
                    if exceeded_reservation
                    else "actual_usage_settled"
                ),
                "actual_cost_exceeded_reservation": cost_exceeded,
                "actual_token_ceiling_exceeded": token_ceiling_exceeded,
                "actual_exceeded_reservation": exceeded_reservation,
                "circuit_breaker_open": exceeded_reservation,
                **self._record_common(),
            }
            record = self._append_event(state, event, timestamp=timestamp)
            return SettlementReceipt(
                reservation_id=str(reservation["reservation_id"]),
                attempt_identity_sha256=identity_hash,
                sequence=int(record["sequence"]),
                actual_cost_usd=actual_cost,
                exceeded_reservation=exceeded_reservation,
                circuit_breaker_open=exceeded_reservation,
            )

    def summary(self, *, now: datetime | None = None) -> dict[str, Any]:
        """Return a hash-validated authority-neutral daily budget summary."""

        generated_at = _kst_now(now)
        with self._locked_state() as state:
            outstanding = [
                record
                for identity_hash, record in state.reservations.items()
                if identity_hash not in state.settlements
            ]
            actual_cost = sum(
                (
                    _stored_decimal(row["actual_cost_usd"], field="actual_cost_usd")
                    for row in state.settlements.values()
                ),
                Decimal(0),
            )
            outstanding_cost = sum(
                (
                    _stored_decimal(row["reserved_cost_usd"], field="reserved_cost_usd")
                    for row in outstanding
                ),
                Decimal(0),
            )
            committed_cost = actual_cost + outstanding_cost
            circuit_breaker_open = self._circuit_breaker_open(state)
            status = (
                "circuit_breaker_open"
                if circuit_breaker_open
                else (
                    "daily_budget_exhausted"
                    if len(state.reservations) >= self.daily_attempt_cap
                    or committed_cost >= self.daily_usd_cap
                    else "daily_budget_available"
                )
            )
            summary_without_hash = {
                "schema": BUDGET_SUMMARY_SCHEMA,
                "generated_at": generated_at.isoformat(),
                "execution_date": self.execution_date.isoformat(),
                "status": status,
                "daily_attempt_cap": self.daily_attempt_cap,
                "daily_usd_cap": _decimal_text(self.daily_usd_cap),
                "reservation_count": len(state.reservations),
                "settlement_count": len(state.settlements),
                "outstanding_reservation_count": len(outstanding),
                "actual_cost_usd": _decimal_text(actual_cost),
                "outstanding_reserved_cost_usd": _decimal_text(outstanding_cost),
                "committed_cost_usd": _decimal_text(committed_cost),
                "remaining_attempt_count": max(
                    0, self.daily_attempt_cap - len(state.reservations)
                ),
                "remaining_usd": _decimal_text(
                    max(Decimal(0), self.daily_usd_cap - committed_cost)
                ),
                "circuit_breaker_open": circuit_breaker_open,
                "ledger_record_count": state.record_count,
                "ledger_head_sha256": state.head_sha256,
                "ledger_bytes_sha256": hashlib.sha256(state.ledger_bytes).hexdigest(),
                "budget_contract_sha256": self._budget_contract_sha256,
                "pricing_artifact_id": self.pricing.artifact_id,
                "pricing_artifact_content_sha256": (
                    self.pricing.artifact_content_sha256
                ),
                "pricing_artifact_file_sha256": self.pricing.artifact_file_sha256,
                "pricing_basis": self.pricing.pricing_basis,
                "raw_pricing_source_bytes_sha256": (
                    self.pricing.raw_source_bytes_sha256
                ),
                "raw_pricing_source_path": str(self.pricing.raw_source_path),
                "raw_pricing_source_size_bytes": self.pricing.raw_source_size_bytes,
                "pricing_effective_from": self.pricing.effective_from.isoformat(),
                "pricing_effective_to": self.pricing.effective_to.isoformat(),
                "provider_model_attempt_counts": self._provider_model_counts(state),
                **AUTHORITY_CONTRACT,
            }
            return {
                **summary_without_hash,
                "summary_content_sha256": _sha256_json(summary_without_hash),
            }

    def validated_reservation_census_read_only(self) -> tuple[dict[str, Any], ...]:
        """Return exact reservations without creating or repairing custody files.

        Historical replay admission uses this path to detect a Provider call that
        reached the physical-day ledger but not the result checkpoint.  Reading a
        prior ledger must therefore neither create its lock nor repair a stale
        manifest: either would mutate immutable audit evidence during preflight.
        """

        directory_fd = -1
        lock_descriptor = -1
        lock_handle: Any | None = None
        try:
            directory_fd = _open_parent_directory_nofollow(self.ledger_path)
            pinned_parent = os.fstat(directory_fd)
            lock_descriptor = _open_regular_file_at(
                directory_fd,
                self.lock_path.name,
                flags=os.O_RDONLY,
            )
            lock_handle = os.fdopen(lock_descriptor, "rb")
            lock_descriptor = -1
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_SH)
            _verify_descriptor_entry(
                directory_fd,
                self.lock_path.name,
                lock_handle.fileno(),
            )
            archived_path = self.ledger_path.with_suffix(
                f"{self.ledger_path.suffix}.gz"
            )
            summary_path = self.ledger_path.with_suffix(".json")
            summary_gzip_path = summary_path.with_name(summary_path.name + ".gz")
            custody_present = any(
                _regular_entry_exists_at(directory_fd, name)
                for name in (
                    self.ledger_path.name,
                    archived_path.name,
                    self.manifest_path.name,
                    summary_path.name,
                    summary_gzip_path.name,
                )
            )
            if not custody_present:
                raise BudgetLedgerIntegrityError("provider_budget_lock_without_custody")
            state = self._load_state(
                repair_manifest=False,
                directory_fd=directory_fd,
            )
            summary_bytes = _read_optional_regular_file_at(
                directory_fd,
                summary_path.name,
            )
            if _regular_entry_exists_at(directory_fd, summary_gzip_path.name):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_summary_gzip_generation_forbidden"
                )
            if summary_bytes is not None:
                try:
                    summary = _json_loads_strict(summary_bytes)
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_summary_json_invalid"
                    ) from exc
                if not isinstance(summary, dict):
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_summary_not_object"
                    )
                summary_content = {
                    key: value
                    for key, value in summary.items()
                    if key != "summary_content_sha256"
                }
                if (
                    summary.get("schema") != BUDGET_SUMMARY_SCHEMA
                    or summary.get("summary_content_sha256")
                    != _sha256_json(summary_content)
                    or summary.get("execution_date") != self.execution_date.isoformat()
                    or summary.get("reservation_count") != len(state.reservations)
                    or summary.get("settlement_count") != len(state.settlements)
                    or summary.get("ledger_record_count") != state.record_count
                    or summary.get("ledger_head_sha256") != state.head_sha256
                    or summary.get("ledger_bytes_sha256")
                    != hashlib.sha256(state.ledger_bytes).hexdigest()
                    or summary.get("budget_contract_sha256")
                    != self._budget_contract_sha256
                    or summary.get("pricing_artifact_content_sha256")
                    != self.pricing.artifact_content_sha256
                    or any(
                        summary.get(field) != expected
                        for field, expected in AUTHORITY_CONTRACT.items()
                    )
                ):
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_summary_custody_mismatch"
                    )
            _verify_descriptor_entry(
                directory_fd,
                self.lock_path.name,
                lock_handle.fileno(),
            )
            current_parent_fd = _open_parent_directory_nofollow(self.ledger_path)
            try:
                current_parent = os.fstat(current_parent_fd)
                if (pinned_parent.st_dev, pinned_parent.st_ino) != (
                    current_parent.st_dev,
                    current_parent.st_ino,
                ):
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_parent_changed_during_read"
                    )
            finally:
                os.close(current_parent_fd)
            return tuple(
                {
                    "execution_date": self.execution_date.isoformat(),
                    "reservation_id": str(record["reservation_id"]),
                    "attempt_identity": dict(record["attempt_identity"]),
                    "attempt_identity_sha256": str(record["attempt_identity_sha256"]),
                    "settled": identity_hash in state.settlements,
                }
                for identity_hash, record in state.reservations.items()
            )
        except BudgetLedgerIntegrityError:
            raise
        except OSError as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_read_only_census_failed"
            ) from exc
        finally:
            if lock_handle is not None:
                try:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
                finally:
                    lock_handle.close()
            elif lock_descriptor >= 0:
                os.close(lock_descriptor)
            if directory_fd >= 0:
                os.close(directory_fd)

    def write_summary(
        self,
        path: Path,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Atomically persist the authority-neutral daily summary artifact."""

        target = _absolute_path_without_symlink_resolution(path)
        if target in {self.ledger_path, self.manifest_path, self.lock_path}:
            raise ValueError("provider budget summary path conflicts with ledger files")
        summary = self.summary(now=now)
        _atomic_write_json(target, summary)
        return summary

    def _record_common(self) -> dict[str, Any]:
        return {
            "budget_contract": dict(self._budget_contract),
            "budget_contract_sha256": self._budget_contract_sha256,
            "pricing_artifact_id": self.pricing.artifact_id,
            "pricing_artifact_content_sha256": (self.pricing.artifact_content_sha256),
            "pricing_artifact_file_sha256": self.pricing.artifact_file_sha256,
            "raw_pricing_source_bytes_sha256": (self.pricing.raw_source_bytes_sha256),
            "raw_pricing_source_path": str(self.pricing.raw_source_path),
            "raw_pricing_source_size_bytes": self.pricing.raw_source_size_bytes,
            "pricing_effective_from": self.pricing.effective_from.isoformat(),
            "pricing_effective_to": self.pricing.effective_to.isoformat(),
            **AUTHORITY_CONTRACT,
        }

    def _locked_state(self) -> _LockedLedgerState:
        return _LockedLedgerState(self)

    def _append_event(
        self,
        state: _LedgerState,
        event: dict[str, Any],
        *,
        timestamp: datetime,
    ) -> dict[str, Any]:
        if state.records:
            previous_timestamp = _aware_timestamp(
                state.records[-1].get("recorded_at"),
                field="previous_recorded_at",
                error_type=BudgetLedgerIntegrityError,
            )
            if timestamp < previous_timestamp:
                raise ProviderBudgetError(
                    "provider_budget_record_timestamp_precedes_ledger_head"
                )
        content = {
            "schema": LEDGER_RECORD_SCHEMA,
            "sequence": state.record_count + 1,
            "previous_record_sha256": state.head_sha256,
            **event,
        }
        record = {**content, "record_content_sha256": _sha256_json(content)}
        encoded = (_canonical_json(record) + "\n").encode("utf-8")
        self._append_ledger_bytes(encoded, state=state)
        state.records.append(record)
        state.ledger_bytes += encoded
        identity_hash = str(record["attempt_identity_sha256"])
        if record["event_type"] == "reservation":
            state.reservations[identity_hash] = record
        else:
            state.settlements[identity_hash] = record
        self._write_manifest(state, updated_at=timestamp)
        return record

    def _append_ledger_bytes(self, encoded: bytes, *, state: _LedgerState) -> None:
        archived_path = self.ledger_path.with_suffix(f"{self.ledger_path.suffix}.gz")
        try:
            archived_exists = _regular_entry_exists_at(
                state.directory_fd,
                archived_path.name,
            )
            ledger_exists = _regular_entry_exists_at(
                state.directory_fd,
                self.ledger_path.name,
            )
        except OSError as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_ledger_path_invalid"
            ) from exc
        if archived_exists:
            if not ledger_exists:
                raise ProviderBudgetError("provider_budget_archived_ledger_read_only")
            raise BudgetLedgerIntegrityError(
                "provider_budget_plain_gzip_ledger_conflict"
            )
        descriptor = -1
        try:
            descriptor = _open_regular_file_at(
                state.directory_fd,
                self.ledger_path.name,
                flags=os.O_APPEND | os.O_CREAT | os.O_RDWR,
                mode=0o640,
            )
            current_bytes = _read_all_from_descriptor(descriptor)
            if current_bytes != state.ledger_bytes:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_ledger_changed_after_validation"
                )
            if _regular_entry_exists_at(state.directory_fd, archived_path.name):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_plain_gzip_ledger_conflict"
                )
            os.lseek(descriptor, 0, os.SEEK_END)
            remaining = memoryview(encoded)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("provider budget ledger append made no progress")
                remaining = remaining[written:]
            os.fsync(descriptor)
            if _regular_entry_exists_at(state.directory_fd, archived_path.name):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_plain_gzip_ledger_conflict"
                )
            _verify_descriptor_entry(
                state.directory_fd,
                self.ledger_path.name,
                descriptor,
            )
        except BudgetLedgerIntegrityError:
            raise
        except OSError as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_ledger_append_failed"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if not ledger_exists:
            os.fsync(state.directory_fd)

    def _load_state(
        self,
        *,
        repair_manifest: bool,
        directory_fd: int,
    ) -> _LedgerState:
        current_pricing = load_reviewed_pricing_artifact(
            self.pricing.artifact_path,
            as_of_date=self.execution_date,
        )
        if current_pricing != self.pricing:
            raise PricingArtifactError("reviewed_pricing_artifact_changed_after_load")
        archived_path = self.ledger_path.with_suffix(f"{self.ledger_path.suffix}.gz")
        try:
            plain_bytes = _read_optional_regular_file_at(
                directory_fd,
                self.ledger_path.name,
            )
            archived_bytes = _read_optional_regular_file_at(
                directory_fd,
                archived_path.name,
            )
            if plain_bytes is not None and archived_bytes is not None:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_plain_gzip_ledger_conflict"
                )
            if plain_bytes is not None:
                ledger_bytes = plain_bytes
            elif archived_bytes is not None:
                ledger_bytes = gzip.decompress(archived_bytes)
            else:
                ledger_bytes = b""
        except BudgetLedgerIntegrityError:
            raise
        except (gzip.BadGzipFile, EOFError, OSError) as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_ledger_unreadable"
            ) from exc
        if ledger_bytes and not ledger_bytes.endswith(b"\n"):
            raise BudgetLedgerIntegrityError("provider_budget_ledger_partial_tail")
        records: list[dict[str, Any]] = []
        reservations: dict[str, dict[str, Any]] = {}
        settlements: dict[str, dict[str, Any]] = {}
        previous_hash: str | None = None
        for index, raw_line in enumerate(ledger_bytes.splitlines(), start=1):
            try:
                record = _json_loads_strict(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_ledger_json_invalid"
                ) from exc
            if not isinstance(record, dict):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_ledger_row_not_object"
                )
            self._validate_record(
                record,
                expected_sequence=index,
                expected_previous_hash=previous_hash,
                reservations=reservations,
                settlements=settlements,
            )
            records.append(record)
            previous_hash = str(record["record_content_sha256"])
            identity_hash = str(record["attempt_identity_sha256"])
            if record["event_type"] == "reservation":
                reservations[identity_hash] = record
            else:
                settlements[identity_hash] = record
        state = _LedgerState(
            records=records,
            reservations=reservations,
            settlements=settlements,
            ledger_bytes=ledger_bytes,
            directory_fd=directory_fd,
        )
        self._validate_budget_history(state)
        manifest_status = self._validate_manifest(state)
        if repair_manifest and manifest_status in {"missing", "stale_valid_prefix"}:
            self._write_manifest(state, updated_at=datetime.now(KST))
        return state

    def _validate_record(
        self,
        record: dict[str, Any],
        *,
        expected_sequence: int,
        expected_previous_hash: str | None,
        reservations: dict[str, dict[str, Any]],
        settlements: dict[str, dict[str, Any]],
    ) -> None:
        if record.get("schema") != LEDGER_RECORD_SCHEMA:
            raise BudgetLedgerIntegrityError("provider_budget_record_schema_invalid")
        event_type = record.get("event_type")
        expected_fields = (
            _RESERVATION_RECORD_FIELDS
            if event_type == "reservation"
            else (
                _SETTLEMENT_RECORD_FIELDS if event_type == "settlement" else frozenset()
            )
        )
        if not expected_fields:
            raise BudgetLedgerIntegrityError("provider_budget_event_type_invalid")
        if set(record) != expected_fields:
            raise BudgetLedgerIntegrityError("provider_budget_record_fields_invalid")
        declared_hash = _sha256_field(
            record.get("record_content_sha256"),
            field="record_content_sha256",
            error_type=BudgetLedgerIntegrityError,
        )
        content = {
            key: value
            for key, value in record.items()
            if key != "record_content_sha256"
        }
        if declared_hash != _sha256_json(content):
            raise BudgetLedgerIntegrityError("provider_budget_record_hash_mismatch")
        _validate_positive_int(
            record.get("sequence"),
            field="sequence",
            error_type=BudgetLedgerIntegrityError,
        )
        if record.get("sequence") != expected_sequence:
            raise BudgetLedgerIntegrityError("provider_budget_record_sequence_mismatch")
        if record.get("previous_record_sha256") != expected_previous_hash:
            raise BudgetLedgerIntegrityError("provider_budget_record_chain_mismatch")
        if record.get("execution_date") != self.execution_date.isoformat():
            raise BudgetLedgerIntegrityError("provider_budget_execution_date_mismatch")
        if record.get("budget_contract") != self._budget_contract:
            raise BudgetLedgerIntegrityError("provider_budget_contract_mismatch")
        if record.get("budget_contract_sha256") != self._budget_contract_sha256:
            raise BudgetLedgerIntegrityError("provider_budget_contract_hash_mismatch")
        if record.get("pricing_artifact_id") != self.pricing.artifact_id:
            raise BudgetLedgerIntegrityError("provider_budget_pricing_id_mismatch")
        for field, expected in (
            (
                "pricing_artifact_content_sha256",
                self.pricing.artifact_content_sha256,
            ),
            ("pricing_artifact_file_sha256", self.pricing.artifact_file_sha256),
            (
                "raw_pricing_source_bytes_sha256",
                self.pricing.raw_source_bytes_sha256,
            ),
            ("raw_pricing_source_path", str(self.pricing.raw_source_path)),
            (
                "raw_pricing_source_size_bytes",
                self.pricing.raw_source_size_bytes,
            ),
            ("pricing_effective_from", self.pricing.effective_from.isoformat()),
            ("pricing_effective_to", self.pricing.effective_to.isoformat()),
        ):
            if record.get(field) != expected:
                raise BudgetLedgerIntegrityError(
                    f"provider_budget_pricing_hash_mismatch:{field}"
                )
        for field, expected in AUTHORITY_CONTRACT.items():
            if record.get(field) != expected:
                raise BudgetLedgerIntegrityError(
                    f"provider_budget_record_authority_invalid:{field}"
                )
        recorded_at = _aware_timestamp(
            record.get("recorded_at"),
            field="recorded_at",
            error_type=BudgetLedgerIntegrityError,
        )
        identity = self._identity_from_record(record)
        identity_hash = identity.content_sha256
        if record.get("attempt_identity_sha256") != identity_hash:
            raise BudgetLedgerIntegrityError(
                "provider_budget_attempt_identity_hash_mismatch"
            )
        try:
            price = self.pricing.price_for(identity.provider, identity.model)
        except (PricingArtifactError, ValueError) as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_record_model_pricing_missing"
            ) from exc
        if event_type == "reservation":
            if recorded_at.astimezone(KST).date() != self.execution_date:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_reservation_recorded_date_mismatch"
                )
            if identity_hash in reservations:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_duplicate_reservation_in_ledger"
                )
            if identity_hash in settlements:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_reservation_after_settlement"
                )
            ceiling = record.get("token_ceiling")
            if not isinstance(ceiling, dict):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_token_ceiling_invalid"
                )
            input_ceiling = ceiling.get("input_token_ceiling")
            output_ceiling = ceiling.get("max_output_tokens")
            input_bytes = ceiling.get("input_utf8_bytes")
            _validate_positive_int(
                input_ceiling,
                field="input_token_ceiling",
                error_type=BudgetLedgerIntegrityError,
            )
            _validate_positive_int(
                input_bytes,
                field="input_utf8_bytes",
                error_type=BudgetLedgerIntegrityError,
            )
            _validate_positive_int(
                output_ceiling,
                field="max_output_tokens",
                error_type=BudgetLedgerIntegrityError,
            )
            if (
                ceiling.get("estimator") != "utf8_bytes_as_input_token_upper_bound_v1"
                or input_ceiling != input_bytes
                or ceiling.get("total_token_ceiling") != input_ceiling + output_ceiling
            ):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_token_ceiling_contract_invalid"
                )
            expected_cost = price.cost(
                input_tokens=input_ceiling,
                output_tokens=output_ceiling,
            )
            if (
                _stored_decimal(
                    record.get("reserved_cost_usd"), field="reserved_cost_usd"
                )
                != expected_cost
            ):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_reserved_cost_mismatch"
                )
            if record.get("model_pricing") != price.as_dict():
                raise BudgetLedgerIntegrityError(
                    "provider_budget_model_pricing_mismatch"
                )
            expected_reservation_id = (
                "provider-reservation-"
                + _sha256_json(
                    {
                        "execution_date": self.execution_date.isoformat(),
                        "attempt_identity_sha256": identity_hash,
                        "pricing_artifact_content_sha256": (
                            self.pricing.artifact_content_sha256
                        ),
                    }
                )[:32]
            )
            if record.get("reservation_id") != expected_reservation_id:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_reservation_id_mismatch"
                )
            if (
                record.get("reservation_status") != "reserved_before_provider_call"
                or record.get("unknown_or_crashed_call_refund_allowed") is not False
            ):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_reservation_status_invalid"
                )
        elif event_type == "settlement":
            reservation = reservations.get(identity_hash)
            if reservation is None:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_settlement_without_reservation"
                )
            if identity_hash in settlements:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_duplicate_settlement_in_ledger"
                )
            if record.get("reservation_id") != reservation.get("reservation_id"):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_settlement_reservation_mismatch"
                )
            reservation_timestamp = _aware_timestamp(
                reservation.get("recorded_at"),
                field="reservation_recorded_at",
                error_type=BudgetLedgerIntegrityError,
            )
            if recorded_at < reservation_timestamp:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_settlement_precedes_reservation"
                )
            actual_input = record.get("actual_input_tokens")
            actual_output = record.get("actual_output_tokens")
            _validate_nonnegative_int(
                actual_input,
                field="actual_input_tokens",
                error_type=BudgetLedgerIntegrityError,
            )
            _validate_nonnegative_int(
                actual_output,
                field="actual_output_tokens",
                error_type=BudgetLedgerIntegrityError,
            )
            actual_cost = price.cost(
                input_tokens=actual_input,
                output_tokens=actual_output,
            )
            reserved_cost = _stored_decimal(
                reservation["reserved_cost_usd"], field="reserved_cost_usd"
            )
            reservation_ceiling = reservation["token_ceiling"]
            cost_exceeded = actual_cost > reserved_cost
            token_ceiling_exceeded = bool(
                actual_input > reservation_ceiling["input_token_ceiling"]
                or actual_output > reservation_ceiling["max_output_tokens"]
            )
            exceeded = cost_exceeded or token_ceiling_exceeded
            if (
                _stored_decimal(record.get("actual_cost_usd"), field="actual_cost_usd")
                != actual_cost
                or _stored_decimal(
                    record.get("reserved_cost_usd"), field="reserved_cost_usd"
                )
                != reserved_cost
                or record.get("actual_cost_exceeded_reservation") is not cost_exceeded
                or record.get("actual_token_ceiling_exceeded")
                is not token_ceiling_exceeded
                or record.get("actual_exceeded_reservation") is not exceeded
                or record.get("circuit_breaker_open") is not exceeded
                or record.get("settlement_status")
                != (
                    "actual_exceeded_reservation_circuit_breaker"
                    if exceeded
                    else "actual_usage_settled"
                )
            ):
                raise BudgetLedgerIntegrityError(
                    "provider_budget_settlement_cost_contract_invalid"
                )
            response_hash = record.get("provider_response_sha256")
            if response_hash is not None:
                _sha256_field(
                    response_hash,
                    field="provider_response_sha256",
                    error_type=BudgetLedgerIntegrityError,
                )

    def _validate_budget_history(self, state: _LedgerState) -> None:
        committed = Decimal(0)
        reservation_costs: dict[str, Decimal] = {}
        reservation_count = 0
        reserved_parent_keys: set[tuple[str, str]] = set()
        breaker_open = False
        previous_timestamp: datetime | None = None
        for record in state.records:
            recorded_at = _aware_timestamp(
                record["recorded_at"],
                field="recorded_at",
                error_type=BudgetLedgerIntegrityError,
            )
            if previous_timestamp is not None and recorded_at < previous_timestamp:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_record_timestamp_not_monotonic"
                )
            previous_timestamp = recorded_at
            identity_hash = str(record["attempt_identity_sha256"])
            if record["event_type"] == "reservation":
                if breaker_open:
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_reservation_after_circuit_breaker"
                    )
                reservation_count += 1
                if reservation_count > self.daily_attempt_cap:
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_historical_attempt_cap_exceeded"
                    )
                identity = record["attempt_identity"]
                reserved_parent_keys.add(
                    (str(identity["target_date"]), str(identity["parent_id"]))
                )
                if len(reserved_parent_keys) > DAILY_PARENT_CAP_MAX:
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_historical_parent_cap_exceeded"
                    )
                reservation_cost = _stored_decimal(
                    record["reserved_cost_usd"], field="reserved_cost_usd"
                )
                reservation_costs[identity_hash] = reservation_cost
                committed += reservation_cost
                if committed > self.daily_usd_cap:
                    raise BudgetLedgerIntegrityError(
                        "provider_budget_historical_usd_cap_exceeded"
                    )
                continue
            reserved_cost = reservation_costs[identity_hash]
            actual_cost = _stored_decimal(
                record["actual_cost_usd"], field="actual_cost_usd"
            )
            committed += actual_cost - reserved_cost
            if actual_cost > reserved_cost:
                breaker_open = True
            elif committed > self.daily_usd_cap:
                raise BudgetLedgerIntegrityError(
                    "provider_budget_historical_usd_cap_exceeded"
                )

    def _identity_from_record(self, record: Mapping[str, Any]) -> AttemptIdentity:
        raw = record.get("attempt_identity")
        if not isinstance(raw, dict) or set(raw) != _ATTEMPT_IDENTITY_FIELDS:
            raise BudgetLedgerIntegrityError("provider_budget_attempt_identity_invalid")
        try:
            return AttemptIdentity(
                target_date=raw.get("target_date"),
                parent_id=raw.get("parent_id"),
                request_id=raw.get("request_id"),
                arm=raw.get("arm"),
                provider=raw.get("provider"),
                model=raw.get("model"),
                attempt_number=raw.get("attempt_number"),
            )
        except (TypeError, ValueError) as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_attempt_identity_invalid"
            ) from exc

    def _committed_cost(self, state: _LedgerState) -> Decimal:
        cost = Decimal(0)
        for identity_hash, reservation in state.reservations.items():
            settlement = state.settlements.get(identity_hash)
            if settlement is None:
                cost += _stored_decimal(
                    reservation["reserved_cost_usd"], field="reserved_cost_usd"
                )
            else:
                cost += _stored_decimal(
                    settlement["actual_cost_usd"], field="actual_cost_usd"
                )
        return cost

    @staticmethod
    def _circuit_breaker_open(state: _LedgerState) -> bool:
        return any(
            settlement.get("circuit_breaker_open") is True
            for settlement in state.settlements.values()
        )

    @staticmethod
    def _provider_model_counts(state: _LedgerState) -> list[dict[str, Any]]:
        counts: dict[tuple[str, str], int] = {}
        for record in state.reservations.values():
            identity = record["attempt_identity"]
            key = (str(identity["provider"]), str(identity["model"]))
            counts[key] = counts.get(key, 0) + 1
        return [
            {"provider": key[0], "model": key[1], "attempt_count": value}
            for key, value in sorted(counts.items())
        ]

    def _validate_manifest(self, state: _LedgerState) -> str:
        try:
            manifest_bytes = _read_optional_regular_file_at(
                state.directory_fd,
                self.manifest_path.name,
            )
            if manifest_bytes is None:
                return "missing"
        except OSError as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_unreadable"
            ) from exc
        try:
            manifest = _json_loads_strict(manifest_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_json_invalid"
            ) from exc
        if not isinstance(manifest, dict):
            raise BudgetLedgerIntegrityError("provider_budget_manifest_not_object")
        if manifest.get("schema") != LEDGER_MANIFEST_SCHEMA:
            raise BudgetLedgerIntegrityError("provider_budget_manifest_schema_invalid")
        if set(manifest) != _MANIFEST_FIELDS:
            raise BudgetLedgerIntegrityError("provider_budget_manifest_fields_invalid")
        declared_hash = _sha256_field(
            manifest.get("manifest_content_sha256"),
            field="manifest_content_sha256",
            error_type=BudgetLedgerIntegrityError,
        )
        content = {
            key: value
            for key, value in manifest.items()
            if key != "manifest_content_sha256"
        }
        if declared_hash != _sha256_json(content):
            raise BudgetLedgerIntegrityError("provider_budget_manifest_hash_mismatch")
        if (
            manifest.get("execution_date") != self.execution_date.isoformat()
            or manifest.get("ledger_file") != self.ledger_path.name
            or manifest.get("budget_contract_sha256") != self._budget_contract_sha256
        ):
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_identity_mismatch"
            )
        for field, expected in AUTHORITY_CONTRACT.items():
            if manifest.get(field) != expected:
                raise BudgetLedgerIntegrityError(
                    f"provider_budget_manifest_authority_invalid:{field}"
                )
        _aware_timestamp(
            manifest.get("updated_at"),
            field="updated_at",
            error_type=BudgetLedgerIntegrityError,
        )
        manifest_size = manifest.get("ledger_size_bytes")
        manifest_count = manifest.get("record_count")
        _validate_nonnegative_int(
            manifest_size,
            field="ledger_size_bytes",
            error_type=BudgetLedgerIntegrityError,
        )
        _validate_nonnegative_int(
            manifest_count,
            field="record_count",
            error_type=BudgetLedgerIntegrityError,
        )
        if manifest_size > len(state.ledger_bytes):
            raise BudgetLedgerIntegrityError("provider_budget_manifest_ahead_of_ledger")
        prefix = state.ledger_bytes[:manifest_size]
        if prefix and not prefix.endswith(b"\n"):
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_prefix_not_record_boundary"
            )
        prefix_count = len(prefix.splitlines())
        if prefix_count != manifest_count or manifest_count > state.record_count:
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_record_count_mismatch"
            )
        prefix_head = (
            state.records[manifest_count - 1]["record_content_sha256"]
            if manifest_count
            else None
        )
        if (
            manifest.get("ledger_bytes_sha256") != hashlib.sha256(prefix).hexdigest()
            or manifest.get("head_record_sha256") != prefix_head
        ):
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_ledger_binding_mismatch"
            )
        if manifest_size == len(state.ledger_bytes):
            return "current"
        return "stale_valid_prefix"

    def _write_manifest(self, state: _LedgerState, *, updated_at: datetime) -> None:
        content = {
            "schema": LEDGER_MANIFEST_SCHEMA,
            "updated_at": updated_at.astimezone(KST).isoformat(),
            "execution_date": self.execution_date.isoformat(),
            "ledger_file": self.ledger_path.name,
            "ledger_size_bytes": len(state.ledger_bytes),
            "ledger_bytes_sha256": hashlib.sha256(state.ledger_bytes).hexdigest(),
            "record_count": state.record_count,
            "head_record_sha256": state.head_sha256,
            "budget_contract_sha256": self._budget_contract_sha256,
            **AUTHORITY_CONTRACT,
        }
        manifest = {
            **content,
            "manifest_content_sha256": _sha256_json(content),
        }
        try:
            _atomic_write_json_at(
                state.directory_fd,
                self.manifest_path.name,
                manifest,
            )
        except OSError as exc:
            raise BudgetLedgerIntegrityError(
                "provider_budget_manifest_write_failed"
            ) from exc


class _LockedLedgerState:
    def __init__(self, ledger: ProviderBudgetLedger) -> None:
        self._ledger = ledger
        self._handle: Any | None = None
        self._directory_fd: int | None = None
        self._state: _LedgerState | None = None

    def __enter__(self) -> _LedgerState:
        self._ledger.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._directory_fd = _open_parent_directory_nofollow(
                self._ledger.ledger_path
            )
            lock_descriptor = _open_regular_file_at(
                self._directory_fd,
                self._ledger.lock_path.name,
                flags=os.O_CREAT | os.O_RDWR,
                mode=0o640,
            )
            try:
                self._handle = os.fdopen(lock_descriptor, "a+b")
            except Exception:
                os.close(lock_descriptor)
                raise
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
            _verify_descriptor_entry(
                self._directory_fd,
                self._ledger.lock_path.name,
                self._handle.fileno(),
            )
        except OSError as exc:
            if self._handle is not None:
                self._handle.close()
                self._handle = None
            if self._directory_fd is not None:
                os.close(self._directory_fd)
                self._directory_fd = None
            raise BudgetLedgerIntegrityError(
                "provider_budget_lock_path_invalid"
            ) from exc
        try:
            self._state = self._ledger._load_state(
                repair_manifest=True,
                directory_fd=self._directory_fd,
            )
        except Exception:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()
            self._handle = None
            os.close(self._directory_fd)
            self._directory_fd = None
            raise
        return self._state

    def __exit__(self, *_: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()
        if self._directory_fd is not None:
            os.close(self._directory_fd)
        self._handle = None
        self._directory_fd = None
        self._state = None


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    directory_fd = _open_parent_directory_nofollow(path)
    try:
        _atomic_write_json_at(directory_fd, path.name, payload)
    finally:
        os.close(directory_fd)


def _atomic_write_json_at(
    directory_fd: int,
    name: str,
    payload: Mapping[str, Any],
) -> None:
    _validate_entry_name(name)
    _regular_entry_exists_at(directory_fd, name)
    encoded = (_canonical_json(payload) + "\n").encode("utf-8")
    temporary_name = ""
    descriptor = -1
    for _ in range(32):
        candidate = f".{name}.{secrets.token_hex(12)}.tmp"
        try:
            descriptor = os.open(
                candidate,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0),
                0o600,
                dir_fd=directory_fd,
            )
        except FileExistsError:
            continue
        temporary_name = candidate
        break
    if descriptor < 0:
        raise OSError("provider budget temporary file allocation failed")
    try:
        _write_all_to_descriptor(descriptor, encoded)
        os.fchmod(descriptor, 0o640)
        os.fsync(descriptor)
        _verify_descriptor_entry(directory_fd, temporary_name, descriptor)
        os.replace(
            temporary_name,
            name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass


def _file_sha256_and_size(path: Path) -> tuple[str, int]:
    absolute = _absolute_path_without_symlink_resolution(path)
    directory_fd = _open_parent_directory_nofollow(absolute)
    descriptor = -1
    try:
        descriptor = _open_regular_file_at(
            directory_fd,
            absolute.name,
            flags=os.O_RDONLY,
        )
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
        _verify_descriptor_entry(directory_fd, absolute.name, descriptor)
        return digest.hexdigest(), size
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(directory_fd)


def _absolute_path_without_symlink_resolution(path: Path) -> Path:
    raw_path = os.fspath(path)
    if not raw_path or "\x00" in raw_path:
        raise ValueError("path must be a non-empty filesystem path")
    return Path(os.path.abspath(raw_path))


def _open_parent_directory_nofollow(path: Path) -> int:
    absolute = _absolute_path_without_symlink_resolution(path)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(os.sep, directory_flags)
    try:
        for component in absolute.parent.parts[1:]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _validate_entry_name(name: str) -> None:
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or os.sep in name
        or (os.altsep is not None and os.altsep in name)
        or "\x00" in name
    ):
        raise _UnsafePathError("unsafe directory entry name")


def _open_regular_file_at(
    directory_fd: int,
    name: str,
    *,
    flags: int,
    mode: int = 0o640,
) -> int:
    _validate_entry_name(name)
    descriptor = os.open(
        name,
        flags | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        mode,
        dir_fd=directory_fd,
    )
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise _UnsafePathError("persistence entry must be a regular file")
        _verify_descriptor_entry(directory_fd, name, descriptor)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _verify_descriptor_entry(
    directory_fd: int,
    name: str,
    descriptor: int,
) -> None:
    _validate_entry_name(name)
    descriptor_stat = os.fstat(descriptor)
    entry_stat = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if (
        not stat.S_ISREG(descriptor_stat.st_mode)
        or not stat.S_ISREG(entry_stat.st_mode)
        or (descriptor_stat.st_dev, descriptor_stat.st_ino)
        != (entry_stat.st_dev, entry_stat.st_ino)
    ):
        raise _UnsafePathError("persistence entry changed during descriptor use")


def _regular_entry_exists_at(directory_fd: int, name: str) -> bool:
    _validate_entry_name(name)
    try:
        entry_stat = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(entry_stat.st_mode):
        raise _UnsafePathError("persistence entry must be a regular file")
    return True


def _read_optional_regular_file_at(
    directory_fd: int,
    name: str,
) -> bytes | None:
    try:
        descriptor = _open_regular_file_at(
            directory_fd,
            name,
            flags=os.O_RDONLY,
        )
    except FileNotFoundError:
        return None
    try:
        contents = _read_all_from_descriptor(descriptor)
        _verify_descriptor_entry(directory_fd, name, descriptor)
        return contents
    finally:
        os.close(descriptor)


def _read_regular_file_nofollow(path: Path) -> bytes:
    absolute = _absolute_path_without_symlink_resolution(path)
    directory_fd = _open_parent_directory_nofollow(absolute)
    try:
        contents = _read_optional_regular_file_at(directory_fd, absolute.name)
        if contents is None:
            raise FileNotFoundError(absolute)
        return contents
    finally:
        os.close(directory_fd)


def _read_all_from_descriptor(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _write_all_to_descriptor(descriptor: int, encoded: bytes) -> None:
    remaining = memoryview(encoded)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("provider budget write made no progress")
        remaining = remaining[written:]


def _selection_sort_key(
    value: tuple[str, str, str | None, str | None],
) -> tuple[str, str, str, str]:
    return (value[0], value[1], value[2] or "", value[3] or "")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _json_loads_strict(value: bytes) -> Any:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = item
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(
        value.decode("utf-8"),
        object_pairs_hook=object_pairs,
        parse_constant=reject_constant,
    )


def _decimal_text(value: Decimal) -> str:
    normalized = format(value, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def _positive_decimal(
    value: object,
    *,
    field: str,
    error_type: type[Exception],
) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise error_type(f"{field} must be a positive finite number")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise error_type(f"{field} must be a positive finite number") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise error_type(f"{field} must be a positive finite number")
    return parsed


def _nonnegative_decimal(
    value: object,
    *,
    field: str,
    error_type: type[Exception],
) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise error_type(f"{field} must be a non-negative finite number")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise error_type(f"{field} must be a non-negative finite number") from exc
    if not parsed.is_finite() or parsed < 0:
        raise error_type(f"{field} must be a non-negative finite number")
    return parsed


def _stored_decimal(value: object, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BudgetLedgerIntegrityError(f"provider_budget_{field}_invalid") from exc
    if not parsed.is_finite() or parsed < 0 or _decimal_text(parsed) != value:
        raise BudgetLedgerIntegrityError(f"provider_budget_{field}_invalid")
    return parsed


def _validate_positive_int(
    value: object,
    *,
    field: str,
    error_type: type[Exception] = ValueError,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise error_type(f"{field} must be a positive integer")


def _validate_nonnegative_int(
    value: object,
    *,
    field: str,
    error_type: type[Exception] = ValueError,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise error_type(f"{field} must be a non-negative integer")


def _identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a bounded printable identifier")
    text = value.strip()
    if not text or len(text) > 256 or any(ord(character) < 32 for character in text):
        raise ValueError(f"{field} must be a bounded printable identifier")
    return text


def _sha256_field(
    value: object,
    *,
    field: str,
    error_type: type[Exception],
) -> str:
    text = str(value or "").strip().lower()
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise error_type(f"{field} must be a lowercase SHA-256 hex digest")
    return text


def _aware_timestamp(
    value: object,
    *,
    field: str,
    error_type: type[Exception],
) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise error_type(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise error_type(f"{field} must include a timezone offset")
    return parsed


def _kst_now(value: datetime | None) -> datetime:
    timestamp = value or datetime.now(KST)
    if not isinstance(timestamp, datetime):
        raise TypeError("now must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("now must include a timezone offset")
    return timestamp.astimezone(KST)


def pricing_models(pricing: ReviewedPricingArtifact) -> Iterable[tuple[str, str]]:
    """Expose the reviewed provider/model census without pricing source bytes."""

    return ((row.provider, row.model) for row in pricing.prices)
