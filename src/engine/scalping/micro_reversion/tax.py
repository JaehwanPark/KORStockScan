"""Date-aware statutory sell-tax contracts for micro-reversion research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Mapping

TAX_POLICY_VERSION = "kr_equity_sell_tax_2026_v1"
TAX_POLICY_EFFECTIVE_FROM = date(2026, 1, 1)
TAX_POLICY_VERIFIED_AT = "2026-08-08T00:00:00+09:00"
TAX_POLICY_SOURCE_URL = (
    "https://www.korea.kr/fcatalog/access/ecatalogt.jsp?"
    "Dir=1199&callmode=normal&catimage=&eclang=ko&start=54&um=s"
)


class ListingMarket(StrEnum):
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KOTC = "KOTC"
    KONEX = "KONEX"
    UNKNOWN = "UNKNOWN"


class InstrumentType(StrEnum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    ETN = "ETN"
    REIT = "REIT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class InstrumentTaxClass(StrEnum):
    ORDINARY_TAXABLE_EQUITY_20BPS = "ordinary_taxable_equity_20bps"
    KONEX_TAXABLE_EQUITY_10BPS = "konex_taxable_equity_10bps"
    UNSUPPORTED_NON_EQUITY = "unsupported_non_equity"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class InstrumentMetadata:
    listing_market: ListingMarket = ListingMarket.UNKNOWN
    instrument_type: InstrumentType = InstrumentType.UNKNOWN
    source: str = "missing"
    verified: bool = False


@dataclass(frozen=True, slots=True)
class TaxProfile:
    policy_version: str
    effective_from: str
    verified_at: str
    source_url: str
    listing_market: ListingMarket
    instrument_type: InstrumentType
    instrument_tax_class: InstrumentTaxClass
    securities_transaction_tax_bps: float | None
    rural_special_tax_bps: float | None
    statutory_sell_tax_bps: float | None
    source_quality_status: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["listing_market"] = self.listing_market.value
        payload["instrument_type"] = self.instrument_type.value
        payload["instrument_tax_class"] = self.instrument_tax_class.value
        return payload


def normalize_listing_market(value: object) -> ListingMarket:
    normalized = str(value or "").strip().upper().replace("-", "")
    aliases = {
        "KOSPI": ListingMarket.KOSPI,
        "유가증권": ListingMarket.KOSPI,
        "유가증권시장": ListingMarket.KOSPI,
        "KOSDAQ": ListingMarket.KOSDAQ,
        "코스닥": ListingMarket.KOSDAQ,
        "KOTC": ListingMarket.KOTC,
        "K-OTC": ListingMarket.KOTC,
        "KONEX": ListingMarket.KONEX,
        "코넥스": ListingMarket.KONEX,
    }
    return aliases.get(normalized, ListingMarket.UNKNOWN)


def normalize_instrument_type(value: object) -> InstrumentType:
    normalized = str(value or "").strip().upper().replace(" ", "_")
    if normalized in {
        "EQUITY",
        "STOCK",
        "COMMON_STOCK",
        "ORDINARY_STOCK",
        "PREFERRED_STOCK",
        "보통주",
        "우선주",
        "주식",
        "주권",
    }:
        return InstrumentType.EQUITY
    if "ETF" in normalized or "상장지수펀드" in normalized:
        return InstrumentType.ETF
    if "ETN" in normalized or "상장지수증권" in normalized:
        return InstrumentType.ETN
    if "REIT" in normalized or "리츠" in normalized:
        return InstrumentType.REIT
    if normalized in {"OTHER", "기타"}:
        return InstrumentType.OTHER
    return InstrumentType.UNKNOWN


def metadata_from_mapping(value: Mapping[str, object] | None) -> InstrumentMetadata:
    if not value:
        return InstrumentMetadata()
    return InstrumentMetadata(
        listing_market=normalize_listing_market(value.get("listing_market")),
        instrument_type=normalize_instrument_type(value.get("instrument_type")),
        source=str(value.get("source") or "explicit_symbol_metadata"),
        # Generic mappings are never authoritative. Only VerifiedSymbolMaster
        # constructs verified metadata after effective-date/conflict checks.
        verified=False,
    )


def tax_profile_for(
    *,
    trade_date: date,
    listing_market: ListingMarket | str,
    instrument_type: InstrumentType | str,
) -> TaxProfile:
    market = normalize_listing_market(listing_market)
    security = normalize_instrument_type(instrument_type)
    common = {
        "policy_version": TAX_POLICY_VERSION,
        "effective_from": TAX_POLICY_EFFECTIVE_FROM.isoformat(),
        "verified_at": TAX_POLICY_VERIFIED_AT,
        "source_url": TAX_POLICY_SOURCE_URL,
        "listing_market": market,
        "instrument_type": security,
    }
    if trade_date < TAX_POLICY_EFFECTIVE_FROM:
        return TaxProfile(
            **common,
            instrument_tax_class=InstrumentTaxClass.UNKNOWN,
            securities_transaction_tax_bps=None,
            rural_special_tax_bps=None,
            statutory_sell_tax_bps=None,
            source_quality_status="unsupported_pre_2026_schedule",
        )
    if market is ListingMarket.UNKNOWN or security is InstrumentType.UNKNOWN:
        return TaxProfile(
            **common,
            instrument_tax_class=InstrumentTaxClass.UNKNOWN,
            securities_transaction_tax_bps=None,
            rural_special_tax_bps=None,
            statutory_sell_tax_bps=None,
            source_quality_status="missing_listing_market_or_instrument_type",
        )
    if security is not InstrumentType.EQUITY:
        return TaxProfile(
            **common,
            instrument_tax_class=InstrumentTaxClass.UNSUPPORTED_NON_EQUITY,
            securities_transaction_tax_bps=None,
            rural_special_tax_bps=None,
            statutory_sell_tax_bps=None,
            source_quality_status="unsupported_non_equity_tax_contract",
        )
    if market is ListingMarket.KOSPI:
        return TaxProfile(
            **common,
            instrument_tax_class=InstrumentTaxClass.ORDINARY_TAXABLE_EQUITY_20BPS,
            securities_transaction_tax_bps=5.0,
            rural_special_tax_bps=15.0,
            statutory_sell_tax_bps=20.0,
            source_quality_status="verified_2026_schedule",
        )
    if market in {ListingMarket.KOSDAQ, ListingMarket.KOTC}:
        return TaxProfile(
            **common,
            instrument_tax_class=InstrumentTaxClass.ORDINARY_TAXABLE_EQUITY_20BPS,
            securities_transaction_tax_bps=20.0,
            rural_special_tax_bps=0.0,
            statutory_sell_tax_bps=20.0,
            source_quality_status="verified_2026_schedule",
        )
    if market is ListingMarket.KONEX:
        return TaxProfile(
            **common,
            instrument_tax_class=InstrumentTaxClass.KONEX_TAXABLE_EQUITY_10BPS,
            securities_transaction_tax_bps=10.0,
            rural_special_tax_bps=0.0,
            statutory_sell_tax_bps=10.0,
            source_quality_status="verified_2026_schedule",
        )
    raise AssertionError(f"unhandled listing market: {market}")


def ordinary_taxable_equity_floor_bps(trade_date: date) -> float | None:
    profile = tax_profile_for(
        trade_date=trade_date,
        listing_market=ListingMarket.KOSPI,
        instrument_type=InstrumentType.EQUITY,
    )
    return profile.statutory_sell_tax_bps
