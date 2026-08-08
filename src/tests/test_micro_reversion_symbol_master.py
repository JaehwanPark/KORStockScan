from datetime import date

import pytest

from src.engine.scalping.micro_reversion.symbol_master import (
    MetadataConflictStatus,
    SymbolLookupStatus,
    SymbolMasterRecord,
    VerifiedSymbolMaster,
)
from src.engine.scalping.micro_reversion.tax import InstrumentType, ListingMarket


def _record(**overrides):
    values = {
        "symbol": "005930",
        "listing_market": ListingMarket.KOSPI,
        "instrument_type": InstrumentType.EQUITY,
        "instrument_tax_class": "ordinary_taxable_equity_20bps",
        "effective_from": date(2026, 1, 1),
        "effective_to": None,
        "metadata_source": "official_kiwoom_export",
        "source_reference": "artifact:sha256:abc",
        "verified_at": "2026-08-08T10:00:00+09:00",
        "conflict_status": MetadataConflictStatus.CLEAN,
    }
    values.update(overrides)
    return SymbolMasterRecord(**values)


def test_verified_symbol_master_effective_date_lookup() -> None:
    master = VerifiedSymbolMaster([_record()])

    result = master.lookup("A005930", as_of=date(2026, 8, 8))

    assert result.status is SymbolLookupStatus.VERIFIED
    assert result.record is not None
    assert result.record.instrument_tax_class.value == "ordinary_taxable_equity_20bps"


def test_symbol_master_conflict_fails_closed() -> None:
    master = VerifiedSymbolMaster([_record(conflict_status="conflict")])

    result = master.lookup("005930", as_of=date(2026, 8, 8))

    assert result.status is SymbolLookupStatus.CONFLICT
    assert result.record is None


def test_symbol_master_rejects_overlapping_windows() -> None:
    with pytest.raises(ValueError, match="overlap"):
        VerifiedSymbolMaster(
            [
                _record(effective_to=date(2026, 6, 30)),
                _record(effective_from=date(2026, 6, 30)),
            ]
        )


def test_verified_record_rejects_unknown_metadata() -> None:
    with pytest.raises(ValueError, match="known listing_market"):
        _record(listing_market=ListingMarket.UNKNOWN)


def test_verified_record_rejects_conflicting_declared_tax_class() -> None:
    with pytest.raises(ValueError, match="instrument_tax_class conflicts"):
        _record(instrument_tax_class="konex_taxable_equity_10bps")
