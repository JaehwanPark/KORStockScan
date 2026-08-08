"""Verified, effective-dated instrument metadata for micro-reversion research.

The master consumes an operator-supplied, independently verified JSON artifact.
It does not infer listing market from execution venue, numeric market codes,
strategy labels, or symbol names.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from .contracts import normalize_symbol
from .tax import (
    TAX_POLICY_EFFECTIVE_FROM,
    InstrumentTaxClass,
    InstrumentType,
    ListingMarket,
    normalize_instrument_type,
    normalize_listing_market,
    tax_profile_for,
)

SYMBOL_MASTER_SCHEMA = "scalp_micro_reversion_symbol_master_v1"


class MetadataConflictStatus(StrEnum):
    CLEAN = "clean"
    CONFLICT = "conflict"


class SymbolLookupStatus(StrEnum):
    VERIFIED = "verified"
    MISSING = "missing"
    OUTSIDE_EFFECTIVE_WINDOW = "outside_effective_window"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class SymbolMasterRecord:
    symbol: str
    listing_market: ListingMarket
    instrument_type: InstrumentType
    instrument_tax_class: InstrumentTaxClass
    effective_from: date
    effective_to: date | None
    metadata_source: str
    source_reference: str
    verified_at: str
    conflict_status: MetadataConflictStatus = MetadataConflictStatus.CLEAN

    def __post_init__(self) -> None:
        symbol = normalize_symbol(self.symbol)
        if not symbol:
            raise ValueError("symbol is required")
        listing_market = normalize_listing_market(self.listing_market)
        instrument_type = normalize_instrument_type(self.instrument_type)
        instrument_tax_class = InstrumentTaxClass(self.instrument_tax_class)
        if listing_market is ListingMarket.UNKNOWN:
            raise ValueError("verified symbol master requires a known listing_market")
        if instrument_type is InstrumentType.UNKNOWN:
            raise ValueError("verified symbol master requires a known instrument_type")
        expected_tax_class = tax_profile_for(
            trade_date=max(self.effective_from, TAX_POLICY_EFFECTIVE_FROM),
            listing_market=listing_market,
            instrument_type=instrument_type,
        ).instrument_tax_class
        if instrument_tax_class is not expected_tax_class:
            raise ValueError(
                "instrument_tax_class conflicts with listing market, instrument type, "
                "or current tax policy"
            )
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")
        if not str(self.metadata_source).strip():
            raise ValueError("metadata_source is required")
        if not str(self.source_reference).strip():
            raise ValueError("source_reference is required")
        _parse_aware_timestamp(self.verified_at, field_name="verified_at")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "listing_market", listing_market)
        object.__setattr__(self, "instrument_type", instrument_type)
        object.__setattr__(self, "instrument_tax_class", instrument_tax_class)
        object.__setattr__(
            self,
            "conflict_status",
            MetadataConflictStatus(self.conflict_status),
        )

    def active_on(self, as_of: date) -> bool:
        return self.effective_from <= as_of and (
            self.effective_to is None or as_of <= self.effective_to
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "listing_market": self.listing_market.value,
                "instrument_type": self.instrument_type.value,
                "instrument_tax_class": self.instrument_tax_class.value,
                "effective_from": self.effective_from.isoformat(),
                "effective_to": (
                    None if self.effective_to is None else self.effective_to.isoformat()
                ),
                "conflict_status": self.conflict_status.value,
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class SymbolLookupResult:
    status: SymbolLookupStatus
    record: SymbolMasterRecord | None

    @property
    def economic_metadata_allowed(self) -> bool:
        return self.status is SymbolLookupStatus.VERIFIED and self.record is not None


class VerifiedSymbolMaster:
    """Immutable, conflict-aware effective-date lookup."""

    def __init__(self, records: Iterable[SymbolMasterRecord]) -> None:
        grouped: dict[str, list[SymbolMasterRecord]] = {}
        for record in records:
            grouped.setdefault(record.symbol, []).append(record)
        self._records = {
            symbol: tuple(
                sorted(rows, key=lambda item: (item.effective_from, item.verified_at))
            )
            for symbol, rows in grouped.items()
        }
        self._validate_overlaps()

    @property
    def symbol_count(self) -> int:
        return len(self._records)

    @property
    def record_count(self) -> int:
        return sum(len(records) for records in self._records.values())

    def lookup(self, symbol: object, *, as_of: date) -> SymbolLookupResult:
        normalized = normalize_symbol(symbol)
        records = self._records.get(normalized)
        if not records:
            return SymbolLookupResult(SymbolLookupStatus.MISSING, None)
        active = tuple(record for record in records if record.active_on(as_of))
        if not active:
            return SymbolLookupResult(SymbolLookupStatus.OUTSIDE_EFFECTIVE_WINDOW, None)
        if (
            len(active) != 1
            or active[0].conflict_status is MetadataConflictStatus.CONFLICT
        ):
            return SymbolLookupResult(SymbolLookupStatus.CONFLICT, None)
        return SymbolLookupResult(SymbolLookupStatus.VERIFIED, active[0])

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SYMBOL_MASTER_SCHEMA,
            "decision_authority": "instrument_metadata_source_only",
            "runtime_effect": False,
            "records": [
                record.as_dict()
                for symbol in sorted(self._records)
                for record in self._records[symbol]
            ],
        }

    @classmethod
    def from_json_path(cls, path: Path) -> VerifiedSymbolMaster:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != SYMBOL_MASTER_SCHEMA
        ):
            raise ValueError(f"symbol master schema must be {SYMBOL_MASTER_SCHEMA}")
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            raise ValueError("symbol master records must be a list")
        return cls(_record_from_mapping(row) for row in raw_records)

    def _validate_overlaps(self) -> None:
        for symbol, records in self._records.items():
            for previous, current in zip(records, records[1:], strict=False):
                if previous.effective_to is None:
                    raise ValueError(
                        f"open-ended symbol master record overlaps for {symbol}"
                    )
                if current.effective_from <= previous.effective_to:
                    raise ValueError(
                        f"symbol master effective windows overlap for {symbol}"
                    )


def _record_from_mapping(raw: object) -> SymbolMasterRecord:
    if not isinstance(raw, dict):
        raise ValueError("symbol master record must be an object")
    effective_to_raw = raw.get("effective_to")
    return SymbolMasterRecord(
        symbol=str(raw.get("symbol") or ""),
        listing_market=normalize_listing_market(raw.get("listing_market")),
        instrument_type=normalize_instrument_type(raw.get("instrument_type")),
        instrument_tax_class=InstrumentTaxClass(
            raw.get("instrument_tax_class", InstrumentTaxClass.UNKNOWN.value)
        ),
        effective_from=date.fromisoformat(str(raw.get("effective_from") or "")),
        effective_to=(
            None
            if effective_to_raw in {None, ""}
            else date.fromisoformat(str(effective_to_raw))
        ),
        metadata_source=str(raw.get("metadata_source") or ""),
        source_reference=str(raw.get("source_reference") or ""),
        verified_at=str(raw.get("verified_at") or ""),
        conflict_status=MetadataConflictStatus(
            raw.get("conflict_status", MetadataConflictStatus.CLEAN.value)
        ),
    )


def _parse_aware_timestamp(value: str, *, field_name: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed
