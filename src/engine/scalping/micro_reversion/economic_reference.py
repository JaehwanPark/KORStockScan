"""Canonical, source-only economic references for micro-reversion research.

The resolver validates immutable broker-fee, statutory-tax, and official
symbol/product-master JSON snapshots against byte-level hashes declared in a
small source manifest.  It then resolves target-date symbol/venue coverage and
materializes bridge-compatible payloads without granting runtime authority.

No fee, tax, product class, or ``verified`` flag is inferred from strategy
labels, symbol names, execution venues, or the generic 23 bps reporting
fallback.  Missing or inconsistent sources produce a durable blocked artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .contracts import CLEAN_BASELINE_DATE, normalize_symbol, normalize_venue
from .tax import (
    InstrumentTaxClass,
    InstrumentType,
    ListingMarket,
    normalize_instrument_type,
    normalize_listing_market,
    tax_profile_for,
)

SOURCE_MANIFEST_SCHEMA = "micro_reversion_economic_reference_source_manifest_v2"
RAW_BROKER_FEE_SCHEMA = "micro_reversion_raw_broker_fee_v2"
RAW_STATUTORY_TAX_SCHEMA = "micro_reversion_raw_statutory_tax_v2"
RAW_SYMBOL_MASTER_SCHEMA = "micro_reversion_raw_symbol_product_master_v3"
DAILY_RESOLUTION_SCHEMA = "micro_reversion_economic_reference_daily_resolution_v2"
REVIEWED_COST_CATALOG_SCHEMA = "micro_reversion_reviewed_cost_catalog_v2"
BRIDGE_COST_PROFILE_SCHEMA = "micro_reversion_reviewed_cost_profile_v1"
BRIDGE_SYMBOL_MASTER_SCHEMA = "scalp_micro_reversion_symbol_master_v1"

SOURCE_KINDS = (
    "broker_fee",
    "statutory_tax",
    "symbol_product_master",
)
RAW_SCHEMA_BY_KIND = {
    "broker_fee": RAW_BROKER_FEE_SCHEMA,
    "statutory_tax": RAW_STATUTORY_TAX_SCHEMA,
    "symbol_product_master": RAW_SYMBOL_MASTER_SCHEMA,
}
SUPPORTED_EXECUTION_VENUES = frozenset({"KRX", "NXT", "SOR"})
SUPPORTED_LISTING_MARKETS = frozenset({"KOSPI", "KOSDAQ"})
SUPPORTED_ECONOMIC_INSTRUMENT = InstrumentType.EQUITY.value
MAX_BPS = 1_000.0
OFFICIAL_MASTER_SOURCE_URIS = frozenset(
    {
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
    }
)
OFFICIAL_MASTER_REPOSITORY = "https://github.com/koreainvestment/open-trading-api"
OFFICIAL_MASTER_PARSER_COMMIT = "b093e42ba32d1df5f5ddad7a71cb715cbc800832"
_KST = ZoneInfo("Asia/Seoul")
_OFFICIAL_MASTER_LAYOUT = {
    "KOSPI": {"trailer_width": 227, "preferred_offset": 158},
    "KOSDAQ": {"trailer_width": 221, "preferred_offset": 153},
}

AUTHORITY_CONTRACT: dict[str, Any] = {
    "decision_authority": "offline_economic_reference_source_only",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "trading_runtime_effect": False,
    "trading_decision_effect": False,
    "selection_authority": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "provider_call_performed": False,
    "forbidden_uses": [
        "live_prompt_or_threshold_mutation",
        "broker_order_submission_or_cancel",
        "automated_sell_or_position_sizing",
        "provider_route_or_bot_state_change",
        "position_cap_or_cooldown_change",
        "hard_protect_emergency_or_stale_guard_bypass",
        "unverified_cost_or_symbol_promotion",
    ],
}


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    source_id: str
    kind: str
    logical_path: str
    resolved_path: Path
    expected_sha256: str
    expected_size_bytes: int
    effective_from: date
    effective_to: date | None

    def active_on(self, target_date: date) -> bool:
        return _date_in_window(target_date, self.effective_from, self.effective_to)


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    descriptor: SourceDescriptor
    payload: Mapping[str, Any] | None
    observed_sha256: str | None
    observed_size_bytes: int | None
    record_count: int
    blockers: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return not self.blockers and self.payload is not None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.descriptor.source_id,
            "kind": self.descriptor.kind,
            "logical_path": self.descriptor.logical_path,
            "resolved_path": str(self.descriptor.resolved_path),
            "expected_sha256": self.descriptor.expected_sha256,
            "observed_sha256": self.observed_sha256,
            "expected_size_bytes": self.descriptor.expected_size_bytes,
            "observed_size_bytes": self.observed_size_bytes,
            "effective_from": self.descriptor.effective_from.isoformat(),
            "effective_to": _date_text(self.descriptor.effective_to),
            "payload_schema": RAW_SCHEMA_BY_KIND[self.descriptor.kind],
            "record_count": self.record_count,
            "status": "verified" if self.verified else "blocked",
            "verified": self.verified,
            "blockers": list(self.blockers),
            **AUTHORITY_CONTRACT,
        }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    ).encode("utf-8")


def content_sha256(value: Any) -> str:
    """Return the canonical JSON content hash used by downstream adapters."""

    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _raw_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _date_text(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _parse_date(value: Any, *, field: str) -> date:
    try:
        return date.fromisoformat(str(value or ""))
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc


def _parse_window(value: Mapping[str, Any], *, prefix: str) -> tuple[date, date | None]:
    effective_from = _parse_date(
        value.get("effective_from"), field=f"{prefix}_effective_from"
    )
    effective_to_raw = value.get("effective_to")
    effective_to = (
        None
        if effective_to_raw in {None, ""}
        else _parse_date(effective_to_raw, field=f"{prefix}_effective_to")
    )
    if effective_to is not None and effective_to < effective_from:
        raise ValueError(f"{prefix}_effective_window_invalid")
    return effective_from, effective_to


def _date_in_window(
    value: date, effective_from: date, effective_to: date | None
) -> bool:
    return effective_from <= value and (effective_to is None or value <= effective_to)


def _windows_overlap(
    left_from: date,
    left_to: date | None,
    right_from: date,
    right_to: date | None,
) -> bool:
    return (left_to is None or right_from <= left_to) and (
        right_to is None or left_from <= right_to
    )


def _window_within(
    child_from: date,
    child_to: date | None,
    parent_from: date,
    parent_to: date | None,
) -> bool:
    return child_from >= parent_from and (
        parent_to is None or (child_to is not None and child_to <= parent_to)
    )


def _number(value: Any, *, field: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not 0.0 <= float(value) <= MAX_BPS
    ):
        raise ValueError(f"{field}_invalid")
    return float(value)


def _string_list(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field}_invalid")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field}_invalid")
    rows = tuple(str(item or "").strip() for item in value)
    if any(not item for item in rows) or len(rows) != len(set(rows)):
        raise ValueError(f"{field}_invalid")
    return rows


def _normalized_venues(value: Any, *, field: str) -> tuple[str, ...]:
    rows = _string_list(value, field=field)
    venues = tuple(normalize_venue(row) for row in rows)
    if any(venue not in SUPPORTED_EXECUTION_VENUES for venue in venues):
        raise ValueError(f"{field}_invalid")
    if tuple(sorted(set(venues))) != tuple(venues):
        raise ValueError(f"{field}_must_be_sorted_unique")
    return venues


def _coverage_venues(value: Any) -> tuple[str, ...]:
    rows = _string_list(value, field="coverage_venues")
    normalized = tuple(
        (
            normalize_venue(row)
            if normalize_venue(row) != "UNKNOWN"
            else str(row).strip().upper()
        )
        for row in rows
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError("coverage_venues_invalid")
    return normalized


def _instrument_types(value: Any, *, field: str) -> tuple[str, ...]:
    rows = _string_list(value, field=field)
    normalized = tuple(normalize_instrument_type(row).value for row in rows)
    if any(item == InstrumentType.UNKNOWN.value for item in normalized):
        raise ValueError(f"{field}_invalid")
    if tuple(sorted(set(normalized))) != tuple(normalized):
        raise ValueError(f"{field}_must_be_sorted_unique")
    return normalized


def _tax_classes(value: Any, *, field: str) -> tuple[str, ...]:
    rows = _string_list(value, field=field)
    try:
        normalized = tuple(InstrumentTaxClass(row).value for row in rows)
    except ValueError as exc:
        raise ValueError(f"{field}_invalid") from exc
    if tuple(sorted(set(normalized))) != tuple(normalized):
        raise ValueError(f"{field}_must_be_sorted_unique")
    return normalized


def _listing_markets(value: Any, *, field: str) -> tuple[str, ...]:
    rows = _string_list(value, field=field)
    normalized = tuple(normalize_listing_market(row).value for row in rows)
    if any(item == ListingMarket.UNKNOWN.value for item in normalized):
        raise ValueError(f"{field}_invalid")
    if tuple(sorted(set(normalized))) != tuple(normalized):
        raise ValueError(f"{field}_must_be_sorted_unique")
    return normalized


def _contains_verified_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).strip().lower() == "verified" or _contains_verified_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_verified_key(child) for child in value)
    return False


def _exact_fields(value: Mapping[str, Any], expected: set[str], *, error: str) -> None:
    if set(value) != expected:
        raise ValueError(error)


def _read_stable_bytes(path: Path) -> tuple[bytes, os.stat_result]:
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        raise ValueError("source_changed_during_read")
    return raw, after


def _source_path(raw_path: str, *, manifest_path: Path) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = manifest_path.parent / candidate
    return candidate.resolve(strict=False)


def _parse_descriptor(
    value: Any, *, index: int, manifest_path: Path
) -> SourceDescriptor:
    if not isinstance(value, Mapping):
        raise ValueError(f"source_descriptor_not_object:{index}")
    _exact_fields(
        value,
        {
            "source_id",
            "kind",
            "logical_path",
            "resolved_path",
            "sha256",
            "size_bytes",
            "effective_from",
            "effective_to",
        },
        error=f"source_descriptor_fields_invalid:{index}",
    )
    source_id = str(value.get("source_id") or "").strip()
    kind = str(value.get("kind") or "").strip()
    logical_path = str(value.get("logical_path") or "").strip()
    resolved_path_raw = str(value.get("resolved_path") or "").strip()
    expected_sha256 = str(value.get("sha256") or "").strip().lower()
    size_value = value.get("size_bytes")
    if not source_id:
        raise ValueError(f"source_id_missing:{index}")
    if kind not in SOURCE_KINDS:
        raise ValueError(f"source_kind_invalid:{source_id}")
    if not logical_path or not resolved_path_raw:
        raise ValueError(f"source_path_missing:{source_id}")
    if len(expected_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in expected_sha256
    ):
        raise ValueError(f"source_sha256_invalid:{source_id}")
    if (
        isinstance(size_value, bool)
        or not isinstance(size_value, int)
        or size_value < 0
    ):
        raise ValueError(f"source_size_invalid:{source_id}")
    effective_from, effective_to = _parse_window(value, prefix=f"source_{source_id}")
    return SourceDescriptor(
        source_id=source_id,
        kind=kind,
        logical_path=logical_path,
        resolved_path=_source_path(resolved_path_raw, manifest_path=manifest_path),
        expected_sha256=expected_sha256,
        expected_size_bytes=size_value,
        effective_from=effective_from,
        effective_to=effective_to,
    )


def _load_source_snapshot(
    descriptor: SourceDescriptor, *, expected_date: date
) -> SourceSnapshot:
    blockers: list[str] = []
    observed_sha256: str | None = None
    observed_size: int | None = None
    payload: Mapping[str, Any] | None = None
    record_count = 0
    try:
        raw, stat = _read_stable_bytes(descriptor.resolved_path)
        observed_size = stat.st_size
        observed_sha256 = _raw_sha256(raw)
    except FileNotFoundError:
        blockers.append(f"source_file_missing:{descriptor.source_id}")
        raw = None
    except (OSError, ValueError) as exc:
        blockers.append(f"source_read_failed:{descriptor.source_id}:{exc}")
        raw = None
    if raw is not None:
        if observed_size != descriptor.expected_size_bytes:
            blockers.append(f"source_size_mismatch:{descriptor.source_id}")
        if observed_sha256 != descriptor.expected_sha256:
            blockers.append(f"source_sha256_mismatch:{descriptor.source_id}")
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append(f"source_json_invalid:{descriptor.source_id}")
        else:
            if not isinstance(parsed, Mapping):
                blockers.append(f"source_payload_not_object:{descriptor.source_id}")
            elif _contains_verified_key(parsed):
                blockers.append(f"input_verified_flag_forbidden:{descriptor.source_id}")
            else:
                expected_schema = RAW_SCHEMA_BY_KIND[descriptor.kind]
                try:
                    expected_fields = {"schema", "source_id", "records"}
                    if descriptor.kind == "symbol_product_master":
                        expected_fields.add("upstream_sources")
                    _exact_fields(
                        parsed,
                        expected_fields,
                        error=f"source_payload_fields_invalid:{descriptor.source_id}",
                    )
                except ValueError as exc:
                    blockers.append(str(exc))
                if parsed.get("schema") != expected_schema:
                    blockers.append(f"source_schema_invalid:{descriptor.source_id}")
                if parsed.get("source_id") != descriptor.source_id:
                    blockers.append(f"source_id_mismatch:{descriptor.source_id}")
                records = parsed.get("records")
                if not isinstance(records, list):
                    blockers.append(f"source_records_invalid:{descriptor.source_id}")
                else:
                    record_count = len(records)
                    if not records:
                        blockers.append(f"source_records_empty:{descriptor.source_id}")
                if descriptor.kind == "symbol_product_master":
                    upstream_blockers, official_common_stocks = (
                        _official_symbol_upstream_contract(
                            parsed.get("upstream_sources"),
                            source_path=descriptor.resolved_path,
                            expected_date=expected_date,
                        )
                    )
                    blockers.extend(upstream_blockers)
                    declared_common_stocks: set[tuple[str, str]] = set()
                    if isinstance(records, list):
                        for record in records:
                            if not isinstance(record, Mapping):
                                continue
                            if (
                                str(record.get("listing_market") or "").strip()
                                not in SUPPORTED_LISTING_MARKETS
                                or str(record.get("instrument_type") or "").strip()
                                != SUPPORTED_ECONOMIC_INSTRUMENT
                                or str(record.get("instrument_tax_class") or "").strip()
                                != InstrumentTaxClass.ORDINARY_TAXABLE_EQUITY_20BPS.value
                            ):
                                continue
                            symbol = normalize_symbol(record.get("symbol"))
                            market = str(record.get("listing_market") or "").strip()
                            if symbol:
                                declared_common_stocks.add((symbol, market))
                    if (
                        not upstream_blockers
                        and declared_common_stocks != official_common_stocks
                    ):
                        blockers.append(
                            "official_symbol_normalized_records_derivation_mismatch"
                        )
                if not blockers:
                    payload = parsed
    return SourceSnapshot(
        descriptor=descriptor,
        payload=payload,
        observed_sha256=observed_sha256,
        observed_size_bytes=observed_size,
        record_count=record_count,
        blockers=tuple(sorted(set(blockers))),
    )


def _derived_official_common_stocks(
    member_bytes: bytes, *, market: str
) -> tuple[set[tuple[str, str]], int]:
    layout = _OFFICIAL_MASTER_LAYOUT[market]
    trailer_width = layout["trailer_width"]
    preferred_offset = layout["preferred_offset"]
    try:
        lines = member_bytes.decode("cp949").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("member_encoding_invalid") from exc
    if not lines:
        raise ValueError("member_rows_empty")
    records: set[tuple[str, str]] = set()
    excluded_non_six_digit_symbol_count = 0
    for line_number, line in enumerate(lines, start=1):
        if len(line) <= trailer_width + 21:
            raise ValueError(f"member_row_too_short:{line_number}")
        prefix = line[:-trailer_width]
        trailer = line[-trailer_width:]
        symbol = prefix[:9].strip()
        standard_code = prefix[9:21].strip()
        korean_name = prefix[21:].strip()
        security_group = trailer[:2].strip()
        preferred_class = trailer[preferred_offset : preferred_offset + 1]
        if security_group != "ST" or preferred_class != "0":
            continue
        if len(symbol) != 6 or not symbol.isdigit():
            excluded_non_six_digit_symbol_count += 1
            continue
        if not standard_code or not korean_name:
            raise ValueError(f"member_common_stock_identity_missing:{line_number}")
        identity = (symbol, market)
        if identity in records:
            raise ValueError(f"member_common_stock_duplicate:{symbol}")
        records.add(identity)
    return records, excluded_non_six_digit_symbol_count


def _official_symbol_upstream_contract(
    value: Any, *, source_path: Path, expected_date: date
) -> tuple[list[str], set[tuple[str, str]]]:
    blockers: list[str] = []
    official_common_stocks: set[tuple[str, str]] = set()
    if not isinstance(value, list) or len(value) != 2:
        return ["official_symbol_upstream_sources_invalid"], official_common_stocks
    expected_markets = {"KOSPI", "KOSDAQ"}
    seen_markets: set[str] = set()
    expected_fields = {
        "market",
        "source_uri",
        "archive_file_name",
        "archive_path",
        "archive_sha256",
        "archive_size_bytes",
        "member_name",
        "member_sha256",
        "member_size_bytes",
        "source_repository",
        "eligible_common_stock_count",
        "excluded_non_six_digit_symbol_count",
        "retrieved_at",
        "parser_source_commit",
    }
    for index, raw in enumerate(value):
        prefix = f"official_symbol_upstream:{index}"
        if not isinstance(raw, Mapping) or set(raw) != expected_fields:
            blockers.append(f"{prefix}:fields_invalid")
            continue
        market = str(raw.get("market") or "")
        source_uri = str(raw.get("source_uri") or "")
        archive_name = str(raw.get("archive_file_name") or "")
        archive_sha = str(raw.get("archive_sha256") or "").lower()
        member_name = str(raw.get("member_name") or "")
        member_sha = str(raw.get("member_sha256") or "").lower()
        parser_commit = str(raw.get("parser_source_commit") or "").lower()
        if market not in expected_markets or market in seen_markets:
            blockers.append(f"{prefix}:market_invalid")
        seen_markets.add(market)
        expected_uri = next(
            (
                uri
                for uri in OFFICIAL_MASTER_SOURCE_URIS
                if f"/{market.lower()}_code.mst.zip" in uri
            ),
            None,
        )
        if source_uri != expected_uri:
            blockers.append(f"{prefix}:source_uri_invalid")
        if raw.get("source_repository") != OFFICIAL_MASTER_REPOSITORY:
            blockers.append(f"{prefix}:source_repository_invalid")
        if archive_name != f"{market.lower()}_code.mst.zip":
            blockers.append(f"{prefix}:archive_name_invalid")
        if member_name != f"{market.lower()}_code.mst":
            blockers.append(f"{prefix}:member_name_invalid")
        if parser_commit != OFFICIAL_MASTER_PARSER_COMMIT:
            blockers.append(f"{prefix}:parser_commit_invalid")
        try:
            retrieved = datetime.fromisoformat(str(raw.get("retrieved_at") or ""))
        except ValueError:
            blockers.append(f"{prefix}:retrieved_at_invalid")
        else:
            if retrieved.tzinfo is None:
                blockers.append(f"{prefix}:retrieved_at_invalid")
            elif retrieved.astimezone(_KST).date() != expected_date:
                blockers.append(f"{prefix}:retrieved_at_date_mismatch")
        archive_size = raw.get("archive_size_bytes")
        member_size = raw.get("member_size_bytes")
        eligible_count = raw.get("eligible_common_stock_count")
        excluded_symbol_count = raw.get("excluded_non_six_digit_symbol_count")
        for field, observed in (
            ("archive_sha256", archive_sha),
            ("member_sha256", member_sha),
        ):
            if len(observed) != 64 or any(
                character not in "0123456789abcdef" for character in observed
            ):
                blockers.append(f"{prefix}:{field}_invalid")
        for field, observed in (
            ("eligible_common_stock_count", eligible_count),
            ("excluded_non_six_digit_symbol_count", excluded_symbol_count),
        ):
            if (
                isinstance(observed, bool)
                or not isinstance(observed, int)
                or observed < 0
            ):
                blockers.append(f"{prefix}:{field}_invalid")
        for field, observed in (
            ("archive_size_bytes", archive_size),
            ("member_size_bytes", member_size),
        ):
            if (
                isinstance(observed, bool)
                or not isinstance(observed, int)
                or observed <= 0
            ):
                blockers.append(f"{prefix}:{field}_invalid")
        archive_path = Path(str(raw.get("archive_path") or ""))
        if not archive_path.is_absolute():
            archive_path = source_path.parent / archive_path
        archive_path = archive_path.resolve(strict=False)
        if archive_path.name != archive_name:
            blockers.append(f"{prefix}:archive_path_invalid")
            continue
        try:
            archive_bytes, archive_stat = _read_stable_bytes(archive_path)
        except (OSError, ValueError):
            blockers.append(f"{prefix}:archive_unreadable")
            continue
        if (
            archive_stat.st_size != archive_size
            or _raw_sha256(archive_bytes) != archive_sha
        ):
            blockers.append(f"{prefix}:archive_hash_or_size_mismatch")
            continue
        try:
            with zipfile.ZipFile(archive_path) as bundle:
                members = bundle.infolist()
                if len(members) != 1 or members[0].filename != member_name:
                    blockers.append(f"{prefix}:member_inventory_invalid")
                    continue
                member_bytes = bundle.read(members[0])
        except (OSError, RuntimeError, zipfile.BadZipFile):
            blockers.append(f"{prefix}:archive_zip_invalid")
            continue
        if len(member_bytes) != member_size or _raw_sha256(member_bytes) != member_sha:
            blockers.append(f"{prefix}:member_hash_or_size_mismatch")
            continue
        try:
            derived, derived_excluded_count = _derived_official_common_stocks(
                member_bytes,
                market=market,
            )
        except ValueError as exc:
            blockers.append(f"{prefix}:{exc}")
            continue
        if eligible_count != len(derived):
            blockers.append(f"{prefix}:eligible_common_stock_count_mismatch")
        if excluded_symbol_count != derived_excluded_count:
            blockers.append(f"{prefix}:excluded_symbol_count_mismatch")
        if official_common_stocks.intersection(derived):
            blockers.append(f"{prefix}:cross_market_symbol_duplicate")
        official_common_stocks.update(derived)
    if seen_markets != expected_markets:
        blockers.append("official_symbol_upstream_market_coverage_invalid")
    return blockers, official_common_stocks


def _record_window(
    value: Mapping[str, Any], *, prefix: str, descriptor: SourceDescriptor
) -> tuple[date, date | None]:
    effective_from, effective_to = _parse_window(value, prefix=prefix)
    if not _window_within(
        effective_from,
        effective_to,
        descriptor.effective_from,
        descriptor.effective_to,
    ):
        raise ValueError(f"record_window_outside_source_window:{prefix}")
    return effective_from, effective_to


def _parse_broker_records(
    snapshot: SourceSnapshot,
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    raw_records = (snapshot.payload or {}).get("records") or []
    for index, raw in enumerate(raw_records):
        prefix = f"broker_fee:{snapshot.descriptor.source_id}:{index}"
        try:
            if not isinstance(raw, Mapping):
                raise ValueError(f"record_not_object:{prefix}")
            _exact_fields(
                raw,
                {
                    "record_id",
                    "effective_from",
                    "effective_to",
                    "venues",
                    "instrument_types",
                    "instrument_tax_classes",
                    "buy_fee_bps",
                    "sell_fee_bps",
                },
                error=f"record_fields_invalid:{prefix}",
            )
            record_id = str(raw.get("record_id") or "").strip()
            if not record_id:
                raise ValueError(f"record_id_missing:{prefix}")
            effective_from, effective_to = _record_window(
                raw, prefix=prefix, descriptor=snapshot.descriptor
            )
            record = {
                "record_id": record_id,
                "effective_from": effective_from,
                "effective_to": effective_to,
                "venues": _normalized_venues(
                    raw.get("venues"), field=f"{prefix}_venues"
                ),
                "instrument_types": _instrument_types(
                    raw.get("instrument_types"), field=f"{prefix}_instrument_types"
                ),
                "instrument_tax_classes": _tax_classes(
                    raw.get("instrument_tax_classes"),
                    field=f"{prefix}_instrument_tax_classes",
                ),
                "buy_fee_bps": _number(
                    raw.get("buy_fee_bps"), field=f"{prefix}_buy_fee_bps"
                ),
                "sell_fee_bps": _number(
                    raw.get("sell_fee_bps"), field=f"{prefix}_sell_fee_bps"
                ),
                "source_id": snapshot.descriptor.source_id,
                "source_sha256": snapshot.observed_sha256,
            }
            record["record_sha256"] = content_sha256(_public_record(record))
            records.append(record)
        except (TypeError, ValueError) as exc:
            blockers.append(str(exc))
    return records, blockers


def _parse_tax_records(
    snapshot: SourceSnapshot,
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    raw_records = (snapshot.payload or {}).get("records") or []
    for index, raw in enumerate(raw_records):
        prefix = f"statutory_tax:{snapshot.descriptor.source_id}:{index}"
        try:
            if not isinstance(raw, Mapping):
                raise ValueError(f"record_not_object:{prefix}")
            _exact_fields(
                raw,
                {
                    "record_id",
                    "effective_from",
                    "effective_to",
                    "listing_markets",
                    "instrument_types",
                    "instrument_tax_classes",
                    "statutory_sell_tax_bps",
                },
                error=f"record_fields_invalid:{prefix}",
            )
            record_id = str(raw.get("record_id") or "").strip()
            if not record_id:
                raise ValueError(f"record_id_missing:{prefix}")
            effective_from, effective_to = _record_window(
                raw, prefix=prefix, descriptor=snapshot.descriptor
            )
            listing_markets = _listing_markets(
                raw.get("listing_markets"), field=f"{prefix}_listing_markets"
            )
            instrument_types = _instrument_types(
                raw.get("instrument_types"), field=f"{prefix}_instrument_types"
            )
            tax_classes = _tax_classes(
                raw.get("instrument_tax_classes"),
                field=f"{prefix}_instrument_tax_classes",
            )
            statutory_bps = _number(
                raw.get("statutory_sell_tax_bps"),
                field=f"{prefix}_statutory_sell_tax_bps",
            )
            policy_date = max(effective_from, CLEAN_BASELINE_DATE)
            expected_tax_classes: set[str] = set()
            for listing_market in listing_markets:
                for instrument_type in instrument_types:
                    profile = tax_profile_for(
                        trade_date=policy_date,
                        listing_market=listing_market,
                        instrument_type=instrument_type,
                    )
                    expected_tax_classes.add(profile.instrument_tax_class.value)
                    if profile.statutory_sell_tax_bps != statutory_bps:
                        raise ValueError(f"statutory_tax_policy_mismatch:{prefix}")
            if set(tax_classes) != expected_tax_classes:
                raise ValueError(f"statutory_tax_class_scope_mismatch:{prefix}")
            record = {
                "record_id": record_id,
                "effective_from": effective_from,
                "effective_to": effective_to,
                "listing_markets": listing_markets,
                "instrument_types": instrument_types,
                "instrument_tax_classes": tax_classes,
                "statutory_sell_tax_bps": statutory_bps,
                "source_id": snapshot.descriptor.source_id,
                "source_sha256": snapshot.observed_sha256,
            }
            record["record_sha256"] = content_sha256(_public_record(record))
            records.append(record)
        except (TypeError, ValueError) as exc:
            blockers.append(str(exc))
    return records, blockers


def _parse_symbol_records(
    snapshot: SourceSnapshot,
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    raw_records = (snapshot.payload or {}).get("records") or []
    for index, raw in enumerate(raw_records):
        prefix = f"symbol_product_master:{snapshot.descriptor.source_id}:{index}"
        try:
            if not isinstance(raw, Mapping):
                raise ValueError(f"record_not_object:{prefix}")
            _exact_fields(
                raw,
                {
                    "record_id",
                    "symbol",
                    "listing_market",
                    "instrument_type",
                    "instrument_tax_class",
                    "effective_from",
                    "effective_to",
                },
                error=f"record_fields_invalid:{prefix}",
            )
            record_id = str(raw.get("record_id") or "").strip()
            symbol = normalize_symbol(raw.get("symbol"))
            if not record_id:
                raise ValueError(f"record_id_missing:{prefix}")
            if len(symbol) != 6 or not symbol.isdigit():
                raise ValueError(f"symbol_invalid:{prefix}")
            effective_from, effective_to = _record_window(
                raw, prefix=prefix, descriptor=snapshot.descriptor
            )
            listing_market = normalize_listing_market(raw.get("listing_market"))
            instrument_type = normalize_instrument_type(raw.get("instrument_type"))
            try:
                tax_class = InstrumentTaxClass(raw.get("instrument_tax_class"))
            except ValueError as exc:
                raise ValueError(f"instrument_tax_class_invalid:{prefix}") from exc
            if listing_market is ListingMarket.UNKNOWN:
                raise ValueError(f"listing_market_invalid:{prefix}")
            if instrument_type is InstrumentType.UNKNOWN:
                raise ValueError(f"instrument_type_invalid:{prefix}")
            expected_class = tax_profile_for(
                trade_date=max(effective_from, CLEAN_BASELINE_DATE),
                listing_market=listing_market,
                instrument_type=instrument_type,
            ).instrument_tax_class
            if tax_class is not expected_class:
                raise ValueError(f"instrument_tax_class_mismatch:{prefix}")
            record = {
                "record_id": record_id,
                "symbol": symbol,
                "listing_market": listing_market.value,
                "instrument_type": instrument_type.value,
                "instrument_tax_class": tax_class.value,
                "effective_from": effective_from,
                "effective_to": effective_to,
                "source_id": snapshot.descriptor.source_id,
                "source_sha256": snapshot.observed_sha256,
            }
            record["record_sha256"] = content_sha256(_public_record(record))
            records.append(record)
        except (TypeError, ValueError) as exc:
            blockers.append(str(exc))
    return records, blockers


def _public_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: (
            _date_text(value)
            if isinstance(value, date)
            else list(value) if isinstance(value, tuple) else value
        )
        for key, value in record.items()
        if key != "record_sha256"
    }


def _duplicate_record_id_blockers(
    kind: str, records: Sequence[Mapping[str, Any]]
) -> list[str]:
    counts: dict[str, int] = {}
    for record in records:
        record_id = str(record["record_id"])
        counts[record_id] = counts.get(record_id, 0) + 1
    return [
        f"duplicate_{kind}_record_id:{record_id}"
        for record_id, count in sorted(counts.items())
        if count > 1
    ]


def _snapshot_with_additional_blockers(
    snapshot: SourceSnapshot, blockers: Sequence[str]
) -> SourceSnapshot:
    return SourceSnapshot(
        descriptor=snapshot.descriptor,
        payload=snapshot.payload,
        observed_sha256=snapshot.observed_sha256,
        observed_size_bytes=snapshot.observed_size_bytes,
        record_count=snapshot.record_count,
        blockers=tuple(sorted(set(snapshot.blockers).union(blockers))),
    )


def _descriptor_overlap_blockers(descriptors: Sequence[SourceDescriptor]) -> list[str]:
    blockers: list[str] = []
    for kind in SOURCE_KINDS:
        rows = sorted(
            (row for row in descriptors if row.kind == kind),
            key=lambda row: (row.effective_from, row.source_id),
        )
        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                if _windows_overlap(
                    left.effective_from,
                    left.effective_to,
                    right.effective_from,
                    right.effective_to,
                ):
                    blockers.append(
                        f"overlapping_source_windows:{kind}:{left.source_id}:{right.source_id}"
                    )
    return blockers


def _record_overlap_blockers(
    *,
    broker_records: Sequence[Mapping[str, Any]],
    tax_records: Sequence[Mapping[str, Any]],
    symbol_records: Sequence[Mapping[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    for index, left in enumerate(broker_records):
        for right in broker_records[index + 1 :]:
            if (
                _windows_overlap(
                    left["effective_from"],
                    left["effective_to"],
                    right["effective_from"],
                    right["effective_to"],
                )
                and set(left["venues"]).intersection(right["venues"])
                and set(left["instrument_types"]).intersection(
                    right["instrument_types"]
                )
                and set(left["instrument_tax_classes"]).intersection(
                    right["instrument_tax_classes"]
                )
            ):
                blockers.append(
                    "overlapping_broker_fee_record_windows:"
                    f"{left['record_id']}:{right['record_id']}"
                )
    for index, left in enumerate(tax_records):
        for right in tax_records[index + 1 :]:
            if (
                _windows_overlap(
                    left["effective_from"],
                    left["effective_to"],
                    right["effective_from"],
                    right["effective_to"],
                )
                and set(left["listing_markets"]).intersection(right["listing_markets"])
                and set(left["instrument_types"]).intersection(
                    right["instrument_types"]
                )
                and set(left["instrument_tax_classes"]).intersection(
                    right["instrument_tax_classes"]
                )
            ):
                blockers.append(
                    "overlapping_statutory_tax_record_windows:"
                    f"{left['record_id']}:{right['record_id']}"
                )
    by_symbol: dict[str, list[Mapping[str, Any]]] = {}
    for record in symbol_records:
        by_symbol.setdefault(str(record["symbol"]), []).append(record)
    for symbol, rows in by_symbol.items():
        ordered = sorted(
            rows, key=lambda row: (row["effective_from"], row["record_id"])
        )
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                if _windows_overlap(
                    left["effective_from"],
                    left["effective_to"],
                    right["effective_from"],
                    right["effective_to"],
                ):
                    blockers.append(
                        "overlapping_symbol_record_windows:"
                        f"{symbol}:{left['record_id']}:{right['record_id']}"
                    )
    return blockers


def _active(
    records: Iterable[Mapping[str, Any]], target_date: date
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in records
        if _date_in_window(
            target_date, record["effective_from"], record["effective_to"]
        )
    ]


def _source_provenance_for_payload(
    snapshots: Sequence[SourceSnapshot],
) -> list[dict[str, Any]]:
    return [
        snapshot.as_dict()
        for snapshot in sorted(snapshots, key=lambda row: row.descriptor.kind)
    ]


def _symbol_master_payload(
    *,
    artifact_id: str,
    symbol_records: Sequence[Mapping[str, Any]],
    source_snapshot: SourceSnapshot | None,
    generated_at: str,
    verified: bool,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if verified and source_snapshot is not None:
        logical = source_snapshot.descriptor.logical_path
        raw_sha = source_snapshot.observed_sha256
        for record in sorted(
            symbol_records,
            key=lambda row: (row["symbol"], row["effective_from"], row["record_id"]),
        ):
            records.append(
                {
                    "symbol": record["symbol"],
                    "listing_market": record["listing_market"],
                    "instrument_type": record["instrument_type"],
                    "instrument_tax_class": record["instrument_tax_class"],
                    "effective_from": record["effective_from"].isoformat(),
                    "effective_to": _date_text(record["effective_to"]),
                    "metadata_source": "official_symbol_product_master_v2",
                    "source_reference": f"{logical}#sha256={raw_sha}",
                    "verified_at": generated_at,
                    "conflict_status": "clean",
                }
            )
    body = {
        "schema": BRIDGE_SYMBOL_MASTER_SCHEMA,
        "artifact_id": artifact_id,
        "source_contract_schema": RAW_SYMBOL_MASTER_SCHEMA,
        "verification_status": "verified" if verified else "blocked",
        "verified": verified,
        **AUTHORITY_CONTRACT,
        "decision_authority": "instrument_metadata_source_only",
        "source_artifacts": (
            [] if source_snapshot is None else [source_snapshot.as_dict()]
        ),
        "census": {
            "record_count": len(records),
            "symbol_count": len({row["symbol"] for row in records}),
        },
        "records": records,
    }
    return {**body, "content_sha256": content_sha256(body)}


def _profile_window(records: Sequence[Mapping[str, Any]]) -> tuple[date, date | None]:
    effective_from = max(record["effective_from"] for record in records)
    finite_ends = [
        record["effective_to"] for record in records if record["effective_to"]
    ]
    effective_to = min(finite_ends) if finite_ends else None
    return effective_from, effective_to


def _cost_profile(
    *,
    venue: str,
    symbol_record: Mapping[str, Any],
    broker_record: Mapping[str, Any],
    tax_record: Mapping[str, Any],
    uncertainty_buffer_bps: float,
) -> dict[str, Any]:
    effective_from, effective_to = _profile_window(
        (symbol_record, broker_record, tax_record)
    )
    identity = {
        "venue": venue,
        "listing_market": symbol_record["listing_market"],
        "instrument_type": symbol_record["instrument_type"],
        "instrument_tax_class": symbol_record["instrument_tax_class"],
        "broker_record_sha256": broker_record["record_sha256"],
        "tax_record_sha256": tax_record["record_sha256"],
        "buy_fee_bps": broker_record["buy_fee_bps"],
        "sell_fee_bps": broker_record["sell_fee_bps"],
        "statutory_sell_tax_bps": tax_record["statutory_sell_tax_bps"],
        "uncertainty_buffer_bps": uncertainty_buffer_bps,
        "effective_from": effective_from.isoformat(),
        "effective_to": _date_text(effective_to),
    }
    profile_id = f"economic-reference-v2-{content_sha256(identity)[:20]}"
    bridge_payload = {
        "schema": BRIDGE_COST_PROFILE_SCHEMA,
        "artifact_id": profile_id,
        "effective_date": effective_from.isoformat(),
        "venues": [venue],
        "instrument_scope": "domestic_common_or_preferred_stock",
        "source": f"canonical_economic_reference_v2:{profile_id}",
        "buy_fee_bps": broker_record["buy_fee_bps"],
        "sell_fee_bps": broker_record["sell_fee_bps"],
        "statutory_sell_tax_bps": tax_record["statutory_sell_tax_bps"],
        "uncertainty_buffer_bps": uncertainty_buffer_bps,
        **AUTHORITY_CONTRACT,
    }
    body = {
        "profile_id": profile_id,
        "effective_from": effective_from.isoformat(),
        "effective_to": _date_text(effective_to),
        "venues": [venue],
        "listing_markets": [symbol_record["listing_market"]],
        "instrument_types": [symbol_record["instrument_type"]],
        "instrument_tax_classes": [symbol_record["instrument_tax_class"]],
        "buy_fee_bps": broker_record["buy_fee_bps"],
        "sell_fee_bps": broker_record["sell_fee_bps"],
        "statutory_sell_tax_bps": tax_record["statutory_sell_tax_bps"],
        "uncertainty_buffer_bps": uncertainty_buffer_bps,
        "source_bindings": {
            "symbol_master_source_id": symbol_record["source_id"],
            "symbol_master_source_sha256": symbol_record["source_sha256"],
            "broker_fee_source_id": broker_record["source_id"],
            "broker_fee_source_sha256": broker_record["source_sha256"],
            "broker_fee_record_sha256": broker_record["record_sha256"],
            "statutory_tax_source_id": tax_record["source_id"],
            "statutory_tax_source_sha256": tax_record["source_sha256"],
            "statutory_tax_record_sha256": tax_record["record_sha256"],
        },
        "bridge_reviewed_cost_payload": bridge_payload,
        "bridge_reviewed_cost_payload_sha256": content_sha256(bridge_payload),
        "verification_status": "verified",
        "verified": True,
        **AUTHORITY_CONTRACT,
    }
    return {**body, "content_sha256": content_sha256(body)}


def _catalog_payload(
    *,
    artifact_id: str,
    target_date: str,
    profiles: Sequence[Mapping[str, Any]],
    verified: bool,
) -> dict[str, Any]:
    body = {
        "schema": REVIEWED_COST_CATALOG_SCHEMA,
        "artifact_id": artifact_id,
        "target_date": target_date,
        "verification_status": "verified" if verified else "blocked",
        "verified": verified,
        "profile_count": len(profiles),
        "census": {
            "profile_count": len(profiles),
            "venue_count": len(
                {venue for profile in profiles for venue in profile.get("venues", [])}
            ),
            "listing_market_count": len(
                {
                    market
                    for profile in profiles
                    for market in profile.get("listing_markets", [])
                }
            ),
            "instrument_type_count": len(
                {
                    instrument
                    for profile in profiles
                    for instrument in profile.get("instrument_types", [])
                }
            ),
            "instrument_tax_class_count": len(
                {
                    tax_class
                    for profile in profiles
                    for tax_class in profile.get("instrument_tax_classes", [])
                }
            ),
        },
        "profiles": list(profiles),
        **AUTHORITY_CONTRACT,
    }
    return {**body, "content_sha256": content_sha256(body)}


def _blocked_artifact(
    *,
    target_date: date,
    generated_at: str,
    manifest_path: Path,
    manifest_sha256: str | None,
    manifest_size_bytes: int | None,
    artifact_id: str,
    blockers: Sequence[str],
    coverage_symbols: Sequence[str] = (),
    coverage_venues: Sequence[str] = (),
    sources: Sequence[SourceSnapshot] = (),
) -> dict[str, Any]:
    exclusions = [
        {
            "symbol": symbol,
            "venue": venue,
            "status": "excluded",
            "reason_codes": sorted(set(blockers)),
        }
        for symbol in coverage_symbols
        for venue in coverage_venues
    ]
    symbol_payload = _symbol_master_payload(
        artifact_id=f"{artifact_id}-symbol-master",
        symbol_records=(),
        source_snapshot=None,
        generated_at=generated_at,
        verified=False,
    )
    catalog = _catalog_payload(
        artifact_id=f"{artifact_id}-cost-catalog",
        target_date=target_date.isoformat(),
        profiles=(),
        verified=False,
    )
    body = {
        "schema": DAILY_RESOLUTION_SCHEMA,
        "artifact_id": artifact_id,
        "target_date": target_date.isoformat(),
        "generated_at": generated_at,
        "status": "blocked",
        "decision": "source_quality_blocked_no_economic_promotion",
        "verified": False,
        "tuning_input_allowed": False,
        "raw_row_exclusion_applied": bool(exclusions),
        "blockers": sorted(set(blockers)),
        "source_manifest": {
            "logical_path": str(manifest_path),
            "resolved_path": str(manifest_path.resolve(strict=False)),
            "sha256": manifest_sha256,
            "size_bytes": manifest_size_bytes,
        },
        "source_artifacts": _source_provenance_for_payload(sources),
        "coverage_request": {
            "symbols": list(coverage_symbols),
            "venues": list(coverage_venues),
        },
        "coverage_rows": exclusions,
        "row_exclusions": exclusions,
        "summary": {
            "requested_pair_count": len(exclusions),
            "eligible_pair_count": 0,
            "excluded_pair_count": len(exclusions),
            "reviewed_cost_profile_count": 0,
            "symbol_master_record_count": 0,
        },
        "canonical_reviewed_cost_payload": catalog,
        "canonical_reviewed_cost_payload_sha256": content_sha256(catalog),
        "canonical_symbol_master_payload": symbol_payload,
        "canonical_symbol_master_payload_sha256": content_sha256(symbol_payload),
        **AUTHORITY_CONTRACT,
    }
    return {**body, "artifact_content_sha256": content_sha256(body)}


def build_daily_resolution(
    *,
    target_date: str,
    source_manifest_path: Path,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Validate raw sources and build one target-date source-only resolution."""

    target = _parse_date(target_date, field="target_date")
    if target < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_before_clean_baseline")
    generated = generated_at or datetime.now().astimezone()
    if generated.tzinfo is None:
        raise ValueError("generated_at_timezone_missing")
    generated_text = generated.isoformat()
    manifest_path = Path(source_manifest_path)
    manifest_sha256: str | None = None
    manifest_size: int | None = None
    try:
        manifest_raw, manifest_stat = _read_stable_bytes(manifest_path)
        manifest_sha256 = _raw_sha256(manifest_raw)
        manifest_size = manifest_stat.st_size
    except FileNotFoundError:
        return _blocked_artifact(
            target_date=target,
            generated_at=generated_text,
            manifest_path=manifest_path,
            manifest_sha256=None,
            manifest_size_bytes=None,
            artifact_id=f"economic-reference-{target.isoformat()}",
            blockers=("source_manifest_missing",),
        )
    except (OSError, ValueError) as exc:
        return _blocked_artifact(
            target_date=target,
            generated_at=generated_text,
            manifest_path=manifest_path,
            manifest_sha256=None,
            manifest_size_bytes=None,
            artifact_id=f"economic-reference-{target.isoformat()}",
            blockers=(f"source_manifest_read_failed:{exc}",),
        )
    try:
        manifest = json.loads(manifest_raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _blocked_artifact(
            target_date=target,
            generated_at=generated_text,
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            manifest_size_bytes=manifest_size,
            artifact_id=f"economic-reference-{target.isoformat()}",
            blockers=("source_manifest_json_invalid",),
        )
    if not isinstance(manifest, Mapping):
        return _blocked_artifact(
            target_date=target,
            generated_at=generated_text,
            manifest_path=manifest_path,
            manifest_sha256=manifest_sha256,
            manifest_size_bytes=manifest_size,
            artifact_id=f"economic-reference-{target.isoformat()}",
            blockers=("source_manifest_not_object",),
        )

    artifact_id = str(manifest.get("artifact_id") or "").strip() or (
        f"economic-reference-{target.isoformat()}"
    )
    blockers: list[str] = []
    coverage_symbols: tuple[str, ...] = ()
    coverage_venues: tuple[str, ...] = ()
    uncertainty_buffer_bps = 0.0
    if _contains_verified_key(manifest):
        blockers.append("input_verified_flag_forbidden:source_manifest")
    try:
        _exact_fields(
            manifest,
            {
                "schema",
                "artifact_id",
                "raw_sources",
                "coverage_request",
                "uncertainty_buffer_bps",
            },
            error="source_manifest_fields_invalid",
        )
    except ValueError as exc:
        blockers.append(str(exc))
    if manifest.get("schema") != SOURCE_MANIFEST_SCHEMA:
        blockers.append("source_manifest_schema_invalid")
    if not str(manifest.get("artifact_id") or "").strip():
        blockers.append("source_manifest_artifact_id_missing")
    try:
        uncertainty_buffer_bps = _number(
            manifest.get("uncertainty_buffer_bps"),
            field="uncertainty_buffer_bps",
        )
    except ValueError as exc:
        blockers.append(str(exc))
    coverage = manifest.get("coverage_request")
    if not isinstance(coverage, Mapping):
        blockers.append("coverage_request_invalid")
    else:
        try:
            _exact_fields(
                coverage,
                {"symbols", "venues"},
                error="coverage_request_fields_invalid",
            )
            raw_symbols = _string_list(
                coverage.get("symbols"), field="coverage_symbols"
            )
            normalized_symbols = tuple(
                normalize_symbol(symbol) for symbol in raw_symbols
            )
            if any(
                len(symbol) != 6 or not symbol.isdigit()
                for symbol in normalized_symbols
            ):
                raise ValueError("coverage_symbols_invalid")
            if len(set(normalized_symbols)) != len(normalized_symbols):
                raise ValueError("coverage_symbols_ambiguous")
            coverage_symbols = tuple(sorted(normalized_symbols))
            coverage_venues = _coverage_venues(coverage.get("venues"))
        except ValueError as exc:
            blockers.append(str(exc))

    descriptors: list[SourceDescriptor] = []
    raw_descriptors = manifest.get("raw_sources")
    if not isinstance(raw_descriptors, list) or not raw_descriptors:
        blockers.append("raw_sources_missing")
    else:
        for index, raw_descriptor in enumerate(raw_descriptors):
            try:
                descriptors.append(
                    _parse_descriptor(
                        raw_descriptor,
                        index=index,
                        manifest_path=manifest_path,
                    )
                )
            except (TypeError, ValueError) as exc:
                blockers.append(str(exc))
    source_ids = [descriptor.source_id for descriptor in descriptors]
    if len(source_ids) != len(set(source_ids)):
        blockers.append("source_id_duplicate")
    descriptor_overlap = _descriptor_overlap_blockers(descriptors)
    blockers.extend(descriptor_overlap)

    active_descriptors: dict[str, SourceDescriptor] = {}
    for kind in SOURCE_KINDS:
        active = [
            descriptor
            for descriptor in descriptors
            if descriptor.kind == kind and descriptor.active_on(target)
        ]
        if not active:
            blockers.append(f"active_source_missing:{kind}")
        elif len(active) > 1:
            blockers.append(f"ambiguous_active_source:{kind}")
        else:
            active_descriptors[kind] = active[0]

    snapshots: dict[str, SourceSnapshot] = {}
    for kind, descriptor in active_descriptors.items():
        snapshot = _load_source_snapshot(descriptor, expected_date=target)
        snapshots[kind] = snapshot
        blockers.extend(snapshot.blockers)

    broker_records: list[dict[str, Any]] = []
    tax_records: list[dict[str, Any]] = []
    symbol_records: list[dict[str, Any]] = []
    record_blockers_by_kind: dict[str, list[str]] = {kind: [] for kind in SOURCE_KINDS}
    if (snapshot := snapshots.get("broker_fee")) is not None and snapshot.verified:
        broker_records, record_blockers_by_kind["broker_fee"] = _parse_broker_records(
            snapshot
        )
    if (snapshot := snapshots.get("statutory_tax")) is not None and snapshot.verified:
        tax_records, record_blockers_by_kind["statutory_tax"] = _parse_tax_records(
            snapshot
        )
    if (
        snapshot := snapshots.get("symbol_product_master")
    ) is not None and snapshot.verified:
        symbol_records, record_blockers_by_kind["symbol_product_master"] = (
            _parse_symbol_records(snapshot)
        )
    for kind_blockers in record_blockers_by_kind.values():
        blockers.extend(kind_blockers)
    duplicate_blockers_by_kind = {
        "broker_fee": _duplicate_record_id_blockers("broker_fee", broker_records),
        "statutory_tax": _duplicate_record_id_blockers("statutory_tax", tax_records),
        "symbol_product_master": _duplicate_record_id_blockers(
            "symbol_product_master", symbol_records
        ),
    }
    for duplicate_blockers in duplicate_blockers_by_kind.values():
        blockers.extend(duplicate_blockers)
    overlap_blockers = _record_overlap_blockers(
        broker_records=broker_records,
        tax_records=tax_records,
        symbol_records=symbol_records,
    )
    blockers.extend(overlap_blockers)
    overlap_prefix_by_kind = {
        "broker_fee": "overlapping_broker_fee_record_windows",
        "statutory_tax": "overlapping_statutory_tax_record_windows",
        "symbol_product_master": "overlapping_symbol_record_windows",
    }
    for kind, snapshot in list(snapshots.items()):
        record_contract_blockers = [
            *record_blockers_by_kind[kind],
            *duplicate_blockers_by_kind[kind],
            *(
                blocker
                for blocker in overlap_blockers
                if blocker.startswith(overlap_prefix_by_kind[kind])
            ),
        ]
        if record_contract_blockers:
            snapshots[kind] = _snapshot_with_additional_blockers(
                snapshot, record_contract_blockers
            )
    blockers = sorted(set(blockers))

    source_contract_valid = not blockers
    kind_valid = {
        kind: bool(
            source_contract_valid
            and kind in snapshots
            and snapshots[kind].verified
            and not record_blockers_by_kind[kind]
            and not any(
                blocker.startswith(overlap_prefix_by_kind[kind])
                for blocker in overlap_blockers
            )
            and not any(
                blocker.startswith(f"overlapping_source_windows:{kind}:")
                or blocker == f"ambiguous_active_source:{kind}"
                for blocker in blockers
            )
        )
        for kind in SOURCE_KINDS
    }

    coverage_rows: list[dict[str, Any]] = []
    row_exclusions: list[dict[str, Any]] = []
    profiles_by_id: dict[str, dict[str, Any]] = {}
    nonisolatable_blockers = [
        blocker
        for blocker in blockers
        if not blocker.startswith(("coverage_", "unsupported_"))
    ]
    for symbol in coverage_symbols:
        active_symbols = [
            record
            for record in _active(symbol_records, target)
            if record["symbol"] == symbol
        ]
        for venue in coverage_venues:
            reasons = list(nonisolatable_blockers)
            symbol_record: Mapping[str, Any] | None = None
            broker_record: Mapping[str, Any] | None = None
            tax_record: Mapping[str, Any] | None = None
            if venue not in SUPPORTED_EXECUTION_VENUES:
                if "PRE" in venue:
                    reasons.append(f"premarket_venue_uncovered:{venue}")
                else:
                    reasons.append(f"unsupported_or_unknown_venue:{venue}")
            if not active_symbols:
                reasons.append(f"symbol_uncovered:{symbol}")
            elif len(active_symbols) > 1:
                reasons.append(f"ambiguous_active_symbol_record:{symbol}")
            else:
                symbol_record = active_symbols[0]
                instrument_type = str(symbol_record["instrument_type"])
                listing_market = str(symbol_record["listing_market"])
                if instrument_type != SUPPORTED_ECONOMIC_INSTRUMENT:
                    reasons.append(f"unsupported_instrument_type:{instrument_type}")
                if listing_market not in SUPPORTED_LISTING_MARKETS:
                    reasons.append(f"unsupported_listing_market:{listing_market}")
            if symbol_record is not None and venue in SUPPORTED_EXECUTION_VENUES:
                broker_matches = [
                    record
                    for record in _active(broker_records, target)
                    if venue in record["venues"]
                    and symbol_record["instrument_type"] in record["instrument_types"]
                    and symbol_record["instrument_tax_class"]
                    in record["instrument_tax_classes"]
                ]
                if not broker_matches:
                    reasons.append(f"broker_fee_venue_uncovered:{venue}")
                elif len(broker_matches) > 1:
                    reasons.append(f"ambiguous_active_broker_fee_record:{venue}")
                else:
                    broker_record = broker_matches[0]
                tax_matches = [
                    record
                    for record in _active(tax_records, target)
                    if symbol_record["listing_market"] in record["listing_markets"]
                    and symbol_record["instrument_type"] in record["instrument_types"]
                    and symbol_record["instrument_tax_class"]
                    in record["instrument_tax_classes"]
                ]
                if not tax_matches:
                    reasons.append("statutory_tax_scope_uncovered")
                elif len(tax_matches) > 1:
                    reasons.append("ambiguous_active_statutory_tax_record")
                else:
                    tax_record = tax_matches[0]
            reasons = sorted(set(reasons))
            row = {
                "symbol": symbol,
                "venue": venue,
                "status": "excluded" if reasons else "eligible",
                "reason_codes": reasons,
                "symbol_record_id": (
                    None if symbol_record is None else symbol_record["record_id"]
                ),
                "symbol_record_sha256": (
                    None if symbol_record is None else symbol_record["record_sha256"]
                ),
                "broker_fee_record_id": (
                    None if broker_record is None else broker_record["record_id"]
                ),
                "broker_fee_record_sha256": (
                    None if broker_record is None else broker_record["record_sha256"]
                ),
                "statutory_tax_record_id": (
                    None if tax_record is None else tax_record["record_id"]
                ),
                "statutory_tax_record_sha256": (
                    None if tax_record is None else tax_record["record_sha256"]
                ),
                "reviewed_cost_profile_id": None,
            }
            if (
                not reasons
                and symbol_record is not None
                and broker_record is not None
                and tax_record is not None
            ):
                profile = _cost_profile(
                    venue=venue,
                    symbol_record=symbol_record,
                    broker_record=broker_record,
                    tax_record=tax_record,
                    uncertainty_buffer_bps=uncertainty_buffer_bps,
                )
                profile_id = str(profile["profile_id"])
                profiles_by_id.setdefault(profile_id, profile)
                row["reviewed_cost_profile_id"] = profile_id
            else:
                row_exclusions.append(dict(row))
            coverage_rows.append(row)

    profiles = [profiles_by_id[key] for key in sorted(profiles_by_id)]
    eligible_count = sum(row["status"] == "eligible" for row in coverage_rows)
    requested_count = len(coverage_rows)
    excluded_count = requested_count - eligible_count
    all_sources_valid = all(kind_valid.values())
    tuning_input_allowed = bool(eligible_count and all_sources_valid)
    status = (
        "blocked"
        if not tuning_input_allowed
        else "partial" if excluded_count else "pass"
    )
    symbol_source = snapshots.get("symbol_product_master")
    symbol_payload = _symbol_master_payload(
        artifact_id=f"{artifact_id}-symbol-master",
        symbol_records=symbol_records,
        source_snapshot=symbol_source,
        generated_at=generated_text,
        verified=all_sources_valid,
    )
    catalog = _catalog_payload(
        artifact_id=f"{artifact_id}-cost-catalog",
        target_date=target.isoformat(),
        profiles=profiles,
        verified=bool(profiles and all_sources_valid),
    )
    body = {
        "schema": DAILY_RESOLUTION_SCHEMA,
        "artifact_id": artifact_id,
        "target_date": target.isoformat(),
        "generated_at": generated_text,
        "status": status,
        "decision": (
            "canonical_economic_reference_ready_source_only"
            if status == "pass"
            else (
                "canonical_economic_reference_partial_with_row_exclusions"
                if status == "partial"
                else "source_quality_blocked_no_economic_promotion"
            )
        ),
        "verified": bool(tuning_input_allowed),
        "tuning_input_allowed": tuning_input_allowed,
        "raw_row_exclusion_applied": bool(row_exclusions),
        "blockers": blockers,
        "source_manifest": {
            "logical_path": str(manifest_path),
            "resolved_path": str(manifest_path.resolve(strict=False)),
            "sha256": manifest_sha256,
            "size_bytes": manifest_size,
            "schema": SOURCE_MANIFEST_SCHEMA,
        },
        "source_artifacts": _source_provenance_for_payload(list(snapshots.values())),
        "coverage_request": {
            "symbols": list(coverage_symbols),
            "venues": list(coverage_venues),
        },
        "coverage_rows": coverage_rows,
        "row_exclusions": row_exclusions,
        "summary": {
            "requested_pair_count": requested_count,
            "eligible_pair_count": eligible_count,
            "excluded_pair_count": excluded_count,
            "reviewed_cost_profile_count": len(profiles),
            "symbol_master_record_count": len(symbol_payload["records"]),
            "source_contract_verified": all_sources_valid,
        },
        "canonical_reviewed_cost_payload": catalog,
        "canonical_reviewed_cost_payload_sha256": content_sha256(catalog),
        "canonical_symbol_master_payload": symbol_payload,
        "canonical_symbol_master_payload_sha256": content_sha256(symbol_payload),
        **AUTHORITY_CONTRACT,
    }
    return {**body, "artifact_content_sha256": content_sha256(body)}


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    """Atomically publish JSON in the destination directory."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        try:
            directory_fd = os.open(destination.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_daily_resolution(
            target_date=args.target_date,
            source_manifest_path=args.source_manifest,
        )
    except ValueError as exc:
        parser.error(str(exc))
    atomic_write_json(args.output, report)
    print(
        json.dumps(
            {
                "schema": report["schema"],
                "target_date": report["target_date"],
                "status": report["status"],
                "decision": report["decision"],
                "tuning_input_allowed": report["tuning_input_allowed"],
                "eligible_pair_count": report["summary"]["eligible_pair_count"],
                "excluded_pair_count": report["summary"]["excluded_pair_count"],
                "output": str(args.output),
                **AUTHORITY_CONTRACT,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
