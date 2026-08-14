"""Contracts for the source-only scalping micro-reversion V0 workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from .tax import (
    InstrumentType,
    ListingMarket,
    TaxProfile,
    normalize_instrument_type,
    normalize_listing_market,
    tax_profile_for,
)

CLEAN_BASELINE_DATE = date(2026, 6, 5)
DEFAULT_HORIZONS_SEC = (15, 30, 60, 120, 180, 300, 600)
OBSERVATION_SCHEMA = "scalp_micro_reversion_price_observation_v4"
EVENT_SCHEMA = "scalp_micro_reversion_shock_event_v3"
OUTCOME_SCHEMA = "scalp_micro_reversion_outcome_label_v3"
REPORT_SCHEMA = "scalp_micro_reversion_v0_report_v5"
POLICY_VERSION = "scalp_micro_reversion_v0_robust_hysteresis_v1"

DECISION_AUTHORITY = "diagnostic_replay_only_no_runtime_activation"
METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "primary_ev_and_source_quality_diagnostic",
    "decision_authority": DECISION_AUTHORITY,
    "window_policy": (
        "clean_baseline_walk_forward_symbol_venue_session_with_"
        "15_30_60_120_180_300_600_second_outcomes"
    ),
    "sample_floor": (
        "collector_health_is_separate_from_clustered_confirmation_economic_gate"
    ),
    "primary_decision_metric": "coverage_adjusted_lower_bound_pct",
    "source_quality_gate": (
        "positive_price_and_horizon_observed_within_lag_and_coverage_tier_"
        "not_imputed"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "buy_score_or_threshold_change",
        "tp_stop_or_trailing_change",
        "provider_or_bot_change",
        "quantity_or_cap_change",
        "real_execution_quality_approval",
        "missing_microstructure_imputation",
    ),
}


class CoverageTier(StrEnum):
    """Highest source-quality tier supported by one price observation."""

    PRICE_PATH = "price_path"
    BBO_CONTEXT = "bbo_context"
    MICRO_CONTEXT = "micro_context"


def normalize_symbol(value: object) -> str:
    raw = str(value or "").strip().upper()
    digits = "".join(character for character in raw if character.isdigit())
    if digits:
        return digits[-6:].zfill(6)
    return raw


def normalize_venue(value: object) -> str:
    venue = str(value or "").strip().upper()
    if venue in {"KRX", "NXT"}:
        return venue
    if venue in {"SOR", "SMART"}:
        return "SOR"
    return "UNKNOWN"


def registration_item_identity(value: object) -> tuple[str, str]:
    """Return the symbol and explicit venue encoded by a Kiwoom WS item."""

    raw = str(value or "").strip().upper()
    if raw.endswith("_AL"):
        base, venue = raw[:-3], "SOR"
    elif raw.endswith("_NX"):
        base, venue = raw[:-3], "NXT"
    else:
        base, venue = raw, "KRX"
    if len(base) != 6 or not base.isdigit():
        return "", "UNKNOWN"
    return base, venue


def coverage_tier_for(
    *,
    best_bid: float | None,
    best_ask: float | None,
    quote_age_ms: float | None,
    aggressive_sell_ratio: float | None,
    ofi: float | None,
    qi: float | None,
    max_quote_age_ms: float = 2_500.0,
) -> CoverageTier:
    bbo_ready = (
        best_bid is not None
        and best_ask is not None
        and best_bid > 0
        and best_ask >= best_bid
        and quote_age_ms is not None
        and 0 <= quote_age_ms <= max_quote_age_ms
    )
    micro_ready = (
        bbo_ready
        and aggressive_sell_ratio is not None
        and (ofi is not None or qi is not None)
    )
    if micro_ready:
        return CoverageTier.MICRO_CONTEXT
    if bbo_ready:
        return CoverageTier.BBO_CONTEXT
    return CoverageTier.PRICE_PATH


@dataclass(frozen=True, slots=True)
class PriceObservation:
    symbol: str
    observed_at_ms: int
    price: float
    trade_date: str
    venue: str = "UNKNOWN"
    session_bucket: str = "KRX_REGULAR"
    source_event_id: str = ""
    price_source_field: str = "current_price_observed"
    best_bid: float | None = None
    best_ask: float | None = None
    quote_age_ms: float | None = None
    micro_vwap: float | None = None
    aggressive_sell_ratio: float | None = None
    ofi: float | None = None
    qi: float | None = None
    source_quality_status: str = "price_path_only"
    listing_market: ListingMarket = ListingMarket.UNKNOWN
    instrument_type: InstrumentType = InstrumentType.UNKNOWN
    instrument_metadata_source: str = "missing"
    instrument_metadata_verified: bool = False
    schema: str = OBSERVATION_SCHEMA

    def __post_init__(self) -> None:
        normalized_symbol = normalize_symbol(self.symbol)
        if not normalized_symbol:
            raise ValueError("symbol is required")
        if self.observed_at_ms <= 0:
            raise ValueError("observed_at_ms must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if not self.price_source_field:
            raise ValueError("price_source_field is required")
        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "venue", normalize_venue(self.venue))
        object.__setattr__(
            self, "listing_market", normalize_listing_market(self.listing_market)
        )
        object.__setattr__(
            self, "instrument_type", normalize_instrument_type(self.instrument_type)
        )

    @property
    def series_key(self) -> tuple[str, str, str, str]:
        return self.trade_date, self.symbol, self.venue, self.session_bucket

    @property
    def coverage_tier(self) -> CoverageTier:
        return coverage_tier_for(
            best_bid=self.best_bid,
            best_ask=self.best_ask,
            quote_age_ms=self.quote_age_ms,
            aggressive_sell_ratio=self.aggressive_sell_ratio,
            ofi=self.ofi,
            qi=self.qi,
        )

    @property
    def tax_profile(self) -> TaxProfile:
        return tax_profile_for(
            trade_date=date.fromisoformat(self.trade_date),
            listing_market=self.listing_market,
            instrument_type=self.instrument_type,
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["listing_market"] = self.listing_market.value
        payload["instrument_type"] = self.instrument_type.value
        payload["coverage_tier"] = self.coverage_tier.value
        payload["tax_profile"] = self.tax_profile.as_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ShockEvent:
    event_id: str
    symbol: str
    venue: str
    session_bucket: str
    trade_date: str
    detected_at_ms: int
    reference_at_ms: int
    reference_price: float
    shock_price: float
    shock_return_bps: float
    return_robust_z: float | None
    acceleration_robust_z: float | None
    micro_vwap: float | None
    coverage_tier: CoverageTier
    source_quality_status: str
    listing_market: ListingMarket = ListingMarket.UNKNOWN
    instrument_type: InstrumentType = InstrumentType.UNKNOWN
    instrument_metadata_source: str = "missing"
    instrument_metadata_verified: bool = False
    policy_version: str = POLICY_VERSION
    schema: str = EVENT_SCHEMA

    def __post_init__(self) -> None:
        normalized_symbol = normalize_symbol(self.symbol)
        if not normalized_symbol:
            raise ValueError("symbol is required")
        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(
            self, "listing_market", normalize_listing_market(self.listing_market)
        )
        object.__setattr__(
            self, "instrument_type", normalize_instrument_type(self.instrument_type)
        )

    @property
    def shock_size(self) -> float:
        return max(0.0, self.reference_price - self.shock_price)

    @property
    def series_key(self) -> tuple[str, str, str, str]:
        return self.trade_date, self.symbol, self.venue, self.session_bucket

    @property
    def tax_profile(self) -> TaxProfile:
        return tax_profile_for(
            trade_date=date.fromisoformat(self.trade_date),
            listing_market=self.listing_market,
            instrument_type=self.instrument_type,
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["coverage_tier"] = self.coverage_tier.value
        payload["listing_market"] = self.listing_market.value
        payload["instrument_type"] = self.instrument_type.value
        payload["tax_profile"] = self.tax_profile.as_dict()
        payload.update(
            {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
                "decision_authority": DECISION_AUTHORITY,
                **METRIC_CONTRACT,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class HorizonOutcome:
    horizon_sec: int
    complete: bool
    observation_lag_ms: int | None = None
    path_observation_count: int = 0
    max_path_gap_ms: int | None = None
    path_continuity_status: str = "not_evaluated"
    terminal_return_bps: float | None = None
    cost_adjusted_terminal_return_bps: float | None = None
    mfe_bps: float | None = None
    mae_bps: float | None = None
    full_reclaim: bool | None = None
    half_reclaim: bool | None = None
    continuation_half_shock: bool | None = None
    micro_vwap_reclaimed: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OutcomeLabel:
    event_id: str
    symbol: str
    trade_date: str
    venue: str
    session_bucket: str
    coverage_tier: CoverageTier
    outcomes: tuple[HorizonOutcome, ...]
    listing_market: ListingMarket = ListingMarket.UNKNOWN
    instrument_type: InstrumentType = InstrumentType.UNKNOWN
    instrument_metadata_source: str = "missing"
    instrument_metadata_verified: bool = False
    first_full_reclaim_ms: int | None = None
    first_half_reclaim_ms: int | None = None
    first_continuation_ms: int | None = None
    outcome_source_quality_status: str = "partial"
    exclusion_reasons: tuple[str, ...] = field(default_factory=tuple)
    schema: str = OUTCOME_SCHEMA

    def __post_init__(self) -> None:
        normalized_symbol = normalize_symbol(self.symbol)
        if not normalized_symbol:
            raise ValueError("symbol is required")
        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(
            self, "listing_market", normalize_listing_market(self.listing_market)
        )
        object.__setattr__(
            self, "instrument_type", normalize_instrument_type(self.instrument_type)
        )

    @property
    def mature_horizon_count(self) -> int:
        return sum(outcome.complete for outcome in self.outcomes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "event_id": self.event_id,
            "symbol": self.symbol,
            "trade_date": self.trade_date,
            "venue": self.venue,
            "session_bucket": self.session_bucket,
            "coverage_tier": self.coverage_tier.value,
            "listing_market": self.listing_market.value,
            "instrument_type": self.instrument_type.value,
            "instrument_metadata_source": self.instrument_metadata_source,
            "instrument_metadata_verified": self.instrument_metadata_verified,
            "tax_profile": tax_profile_for(
                trade_date=date.fromisoformat(self.trade_date),
                listing_market=self.listing_market,
                instrument_type=self.instrument_type,
            ).as_dict(),
            "outcomes": [outcome.as_dict() for outcome in self.outcomes],
            "first_full_reclaim_ms": self.first_full_reclaim_ms,
            "first_half_reclaim_ms": self.first_half_reclaim_ms,
            "first_continuation_ms": self.first_continuation_ms,
            "outcome_source_quality_status": self.outcome_source_quality_status,
            "exclusion_reasons": list(self.exclusion_reasons),
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "decision_authority": DECISION_AUTHORITY,
            **METRIC_CONTRACT,
        }
