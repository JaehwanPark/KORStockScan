from __future__ import annotations

from datetime import date

from src.engine.scalping.micro_reversion.tax import (
    InstrumentTaxClass,
    InstrumentType,
    ListingMarket,
    normalize_instrument_type,
    normalize_listing_market,
    tax_profile_for,
)


def test_2026_ordinary_equity_sell_tax_schedule() -> None:
    kospi = tax_profile_for(
        trade_date=date(2026, 8, 7),
        listing_market=ListingMarket.KOSPI,
        instrument_type=InstrumentType.EQUITY,
    )
    kosdaq = tax_profile_for(
        trade_date=date(2026, 8, 7),
        listing_market=ListingMarket.KOSDAQ,
        instrument_type=InstrumentType.EQUITY,
    )

    assert kospi.instrument_tax_class is (
        InstrumentTaxClass.ORDINARY_TAXABLE_EQUITY_20BPS
    )
    assert kospi.securities_transaction_tax_bps == 5.0
    assert kospi.rural_special_tax_bps == 15.0
    assert kospi.statutory_sell_tax_bps == 20.0
    assert kosdaq.securities_transaction_tax_bps == 20.0
    assert kosdaq.rural_special_tax_bps == 0.0
    assert kosdaq.statutory_sell_tax_bps == 20.0


def test_missing_or_non_equity_metadata_fails_closed() -> None:
    missing = tax_profile_for(
        trade_date=date(2026, 8, 7),
        listing_market=ListingMarket.UNKNOWN,
        instrument_type=InstrumentType.UNKNOWN,
    )
    etf = tax_profile_for(
        trade_date=date(2026, 8, 7),
        listing_market=ListingMarket.KOSPI,
        instrument_type=InstrumentType.ETF,
    )

    assert missing.statutory_sell_tax_bps is None
    assert missing.instrument_tax_class is InstrumentTaxClass.UNKNOWN
    assert etf.statutory_sell_tax_bps is None
    assert etf.instrument_tax_class is InstrumentTaxClass.UNSUPPORTED_NON_EQUITY


def test_tax_metadata_aliases_are_normalized_without_numeric_market_guessing() -> None:
    assert normalize_listing_market("코스닥") is ListingMarket.KOSDAQ
    assert normalize_listing_market("0") is ListingMarket.UNKNOWN
    assert normalize_instrument_type("common_stock") is InstrumentType.EQUITY
