"""Build effective-dated, source-only economic references for AI replay.

The owner downloads the official KIS KOSPI/KOSDAQ master archives, preserves
their exact bytes, and derives only ordinary domestic shares from documented
fixed-width fields.  It also materializes the operator-reviewed fee, tax, and
zero-cost Provider accounting inputs used by the offline R0-R3 lane.

This module has no live runtime, provider, credential, or order authority.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .economic_reference import (
    AUTHORITY_CONTRACT,
    OFFICIAL_MASTER_PARSER_COMMIT,
    RAW_BROKER_FEE_SCHEMA,
    RAW_STATUTORY_TAX_SCHEMA,
    RAW_SYMBOL_MASTER_SCHEMA,
    SOURCE_MANIFEST_SCHEMA,
    content_sha256,
)
from .provider_budget import (
    PRICING_ARTIFACT_SCHEMA,
    PRICING_AUTHORITY,
    pricing_artifact_content_sha256,
)

KST = ZoneInfo("Asia/Seoul")

POLICY_SCHEMA = "micro_reversion_economic_reference_owner_policy_v1"
OWNER_REPORT_SCHEMA = "micro_reversion_economic_reference_owner_report_v1"
OPERATOR_ZERO_COST_BASIS = "operator_accounting_zero_cost"

KIS_REPOSITORY = "https://github.com/koreainvestment/open-trading-api"
KIS_KOSPI_MASTER_URL = (
    "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
)
KIS_KOSDAQ_MASTER_URL = (
    "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip"
)
MAX_MASTER_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_MASTER_MEMBER_BYTES = 16 * 1024 * 1024

_POLICY_FIELDS = {
    "schema",
    "policy_id",
    "effective_from",
    "effective_to",
    "reviewed_at",
    "broker_fee",
    "statutory_tax",
    "official_symbol_master",
    "provider_pricing",
    "provider_budget_basis",
    "decision_authority",
    "runtime_effect",
    "allowed_runtime_apply",
    "actual_order_submitted",
    "broker_order_forbidden",
}

_KOSPI_WIDTHS = (
    2,
    1,
    4,
    4,
    4,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    9,
    5,
    5,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    2,
    2,
    2,
    3,
    1,
    3,
    12,
    12,
    8,
    15,
    21,
    2,
    7,
    1,
    1,
    1,
    1,
    1,
    9,
    9,
    9,
    5,
    9,
    8,
    9,
    3,
    1,
    1,
    1,
)
_KOSDAQ_WIDTHS = (
    2,
    1,
    4,
    4,
    4,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    9,
    5,
    5,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    2,
    2,
    2,
    3,
    1,
    3,
    12,
    12,
    8,
    15,
    21,
    2,
    7,
    1,
    1,
    1,
    1,
    9,
    9,
    9,
    5,
    9,
    8,
    9,
    3,
    1,
    1,
    1,
)


@dataclass(frozen=True, slots=True)
class MasterSpec:
    market: str
    url: str
    member_name: str
    widths: tuple[int, ...]
    preferred_index: int


MASTER_SPECS = (
    MasterSpec(
        market="KOSPI",
        url=KIS_KOSPI_MASTER_URL,
        member_name="kospi_code.mst",
        widths=_KOSPI_WIDTHS,
        preferred_index=54,
    ),
    MasterSpec(
        market="KOSDAQ",
        url=KIS_KOSDAQ_MASTER_URL,
        member_name="kosdaq_code.mst",
        widths=_KOSDAQ_WIDTHS,
        preferred_index=49,
    ),
)

_REVIEWED_AI_TRACE_BASIS = (
    (
        "2026-08-10",
        "40e9db47bab0129054184a1f3595f8e007a4024c707d61509e6530c5b5f721bf",
        6042290,
        857,
        712,
        676,
    ),
    (
        "2026-08-11",
        "818e32f8006531080efb378f10259af81a42798563b9489c9ac5bf8df7916fbe",
        3078450,
        429,
        370,
        369,
    ),
    (
        "2026-08-12",
        "1ec08ed849ed44e05d80882ae3b1496e089bda1cad182c21505ef1232361f41f",
        6101606,
        871,
        788,
        781,
    ),
    (
        "2026-08-13",
        "afdbb5a2ce040dda568ae8f0092c19a43732011b3e5bf0ee17a01026d3ef1cd6",
        12588442,
        1848,
        1120,
        1113,
    ),
    (
        "2026-08-14",
        "bb34d4982d873ccd6dd1b8e176714f2c2ef7e29248a89c2280b780df7209aac0",
        10014231,
        1443,
        1046,
        999,
    ),
)


class EconomicReferenceOwnerError(RuntimeError):
    """A source policy or official master failed closed."""


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _load_policy(path: Path, *, target_date: date) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        policy = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EconomicReferenceOwnerError("economic_policy_unreadable") from exc
    if not isinstance(policy, dict) or set(policy) != _POLICY_FIELDS:
        raise EconomicReferenceOwnerError("economic_policy_fields_invalid")
    if policy.get("schema") != POLICY_SCHEMA:
        raise EconomicReferenceOwnerError("economic_policy_schema_invalid")
    if policy.get("policy_id") != "main-ai-economic-policy-2026-08-18-v1":
        raise EconomicReferenceOwnerError("economic_policy_id_invalid")
    if policy.get("decision_authority") != "offline_economic_reference_source_only":
        raise EconomicReferenceOwnerError("economic_policy_authority_invalid")
    for field, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if policy.get(field) is not expected:
            raise EconomicReferenceOwnerError(
                f"economic_policy_authority_invalid:{field}"
            )
    try:
        effective_from = date.fromisoformat(str(policy.get("effective_from") or ""))
        effective_to_raw = policy.get("effective_to")
        effective_to = (
            None
            if effective_to_raw in {None, ""}
            else date.fromisoformat(str(effective_to_raw))
        )
        reviewed_at = datetime.fromisoformat(str(policy.get("reviewed_at") or ""))
    except ValueError as exc:
        raise EconomicReferenceOwnerError("economic_policy_window_invalid") from exc
    if reviewed_at.tzinfo is None:
        raise EconomicReferenceOwnerError("economic_policy_reviewed_at_naive")
    if reviewed_at.astimezone(KST).date() > target_date:
        raise EconomicReferenceOwnerError("economic_policy_reviewed_at_in_future")
    if effective_from != date(2026, 8, 18) or effective_to is not None:
        raise EconomicReferenceOwnerError("economic_policy_effective_window_invalid")
    if effective_to is not None and effective_to < effective_from:
        raise EconomicReferenceOwnerError("economic_policy_window_reversed")
    if target_date < effective_from:
        raise EconomicReferenceOwnerError("economic_policy_not_yet_effective")
    if effective_to is not None and target_date > effective_to:
        raise EconomicReferenceOwnerError("economic_policy_stale")
    broker_fee = policy.get("broker_fee")
    if not isinstance(broker_fee, dict) or set(broker_fee) != {
        "buy_fee_bps",
        "sell_fee_bps",
    }:
        raise EconomicReferenceOwnerError("economic_policy_broker_fee_invalid")
    if broker_fee != {"buy_fee_bps": 1.5, "sell_fee_bps": 1.5}:
        raise EconomicReferenceOwnerError(
            "economic_policy_broker_fee_not_reviewed_value"
        )
    statutory_tax = policy.get("statutory_tax")
    if not isinstance(statutory_tax, dict) or statutory_tax != {"sell_tax_bps": 20.0}:
        raise EconomicReferenceOwnerError("economic_policy_statutory_tax_invalid")
    official_master = policy.get("official_symbol_master")
    if not isinstance(official_master, dict) or set(official_master) != {
        "source_repository",
        "parser_source_commit",
        "allowed_listing_markets",
        "required_security_group_code",
        "required_preferred_class_code",
    }:
        raise EconomicReferenceOwnerError("economic_policy_symbol_master_invalid")
    if official_master.get("source_repository") != KIS_REPOSITORY:
        raise EconomicReferenceOwnerError("economic_policy_symbol_master_owner_invalid")
    parser_commit = str(official_master.get("parser_source_commit") or "").lower()
    if parser_commit != OFFICIAL_MASTER_PARSER_COMMIT:
        raise EconomicReferenceOwnerError("economic_policy_parser_commit_invalid")
    if official_master.get("allowed_listing_markets") != ["KOSDAQ", "KOSPI"]:
        raise EconomicReferenceOwnerError("economic_policy_listing_market_invalid")
    if official_master.get("required_security_group_code") != "ST":
        raise EconomicReferenceOwnerError("economic_policy_security_group_invalid")
    if official_master.get("required_preferred_class_code") != "0":
        raise EconomicReferenceOwnerError("economic_policy_preferred_class_invalid")
    provider_pricing = policy.get("provider_pricing")
    if not isinstance(provider_pricing, dict) or set(provider_pricing) != {
        "pricing_basis",
        "prices",
    }:
        raise EconomicReferenceOwnerError("economic_policy_provider_pricing_invalid")
    if provider_pricing.get("pricing_basis") != OPERATOR_ZERO_COST_BASIS:
        raise EconomicReferenceOwnerError(
            "economic_policy_provider_pricing_basis_invalid"
        )
    prices = provider_pricing.get("prices")
    if not isinstance(prices, list) or not prices:
        raise EconomicReferenceOwnerError("economic_policy_provider_prices_missing")
    seen_prices: set[tuple[str, str]] = set()
    for price in prices:
        if not isinstance(price, dict) or set(price) != {
            "provider",
            "model",
            "input_usd_per_million_tokens",
            "output_usd_per_million_tokens",
        }:
            raise EconomicReferenceOwnerError("economic_policy_provider_price_invalid")
        key = (str(price.get("provider") or ""), str(price.get("model") or ""))
        if not all(key) or key in seen_prices:
            raise EconomicReferenceOwnerError(
                "economic_policy_provider_price_identity_invalid"
            )
        seen_prices.add(key)
        if (
            str(price.get("input_usd_per_million_tokens")) != "0"
            or str(price.get("output_usd_per_million_tokens")) != "0"
        ):
            raise EconomicReferenceOwnerError("economic_policy_provider_price_nonzero")
    if seen_prices != {
        ("openai", "gpt-5-nano"),
        ("openai", "gpt-5.4-nano"),
        ("openai", "gpt-5.4-mini"),
        ("bedrock", "qwen3_32b"),
        ("bedrock", "nova_lite_v2"),
    }:
        raise EconomicReferenceOwnerError("economic_policy_provider_models_invalid")
    budget_basis = policy.get("provider_budget_basis")
    expected_source_artifacts = [
        {
            "target_date": observed_date,
            "logical_path": (
                f"data/ai_decision_trace/ai_decision_trace_{observed_date}.jsonl"
            ),
            "content_sha256": content_hash,
            "content_size_bytes": content_size,
            "row_count": row_count,
            "provider_called_count": provider_called_count,
            "evaluated_call_count": evaluated_call_count,
        }
        for (
            observed_date,
            content_hash,
            content_size,
            row_count,
            provider_called_count,
            evaluated_call_count,
        ) in _REVIEWED_AI_TRACE_BASIS
    ]
    if not isinstance(budget_basis, dict) or budget_basis != {
        "observation_window_start": "2026-08-10",
        "observation_window_end": "2026-08-14",
        "evaluated_call_counts": [676, 369, 781, 1113, 999],
        "evaluated_call_median": 781,
        "target_share_of_evaluated_median_pct": 50.0,
        "daily_parent_cap": 130,
        "logical_requests_per_parent": 3,
        "maximum_logical_request_count": 390,
        "maximum_schema_attempts_per_request": 4,
        "daily_attempt_cap": 390,
        "source_artifacts": expected_source_artifacts,
    }:
        raise EconomicReferenceOwnerError(
            "economic_policy_provider_budget_basis_invalid"
        )
    return policy, raw


def _download(url: str) -> bytes:
    if url not in {KIS_KOSPI_MASTER_URL, KIS_KOSDAQ_MASTER_URL}:
        raise EconomicReferenceOwnerError("official_master_url_not_allowlisted")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "KORStockScan-source-only-master/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            if response.geturl() != url:
                raise EconomicReferenceOwnerError("official_master_redirected")
            raw = response.read(MAX_MASTER_ARCHIVE_BYTES + 1)
    except (OSError, ValueError) as exc:
        raise EconomicReferenceOwnerError("official_master_download_failed") from exc
    if not raw or len(raw) > MAX_MASTER_ARCHIVE_BYTES:
        raise EconomicReferenceOwnerError("official_master_archive_size_invalid")
    return raw


def _split_fixed_width(value: str, widths: tuple[int, ...]) -> list[str]:
    rows: list[str] = []
    offset = 0
    for width in widths:
        rows.append(value[offset : offset + width].strip())
        offset += width
    if offset != len(value):
        raise EconomicReferenceOwnerError("official_master_trailer_width_mismatch")
    return rows


def _parse_master(
    archive: bytes,
    *,
    spec: MasterSpec,
    effective_from: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], bytes]:
    archive_path = Path(spec.member_name + ".zip")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            members = bundle.infolist()
            if len(members) != 1 or members[0].filename != spec.member_name:
                raise EconomicReferenceOwnerError("official_master_member_invalid")
            member = members[0]
            if member.file_size <= 0 or member.file_size > MAX_MASTER_MEMBER_BYTES:
                raise EconomicReferenceOwnerError("official_master_member_size_invalid")
            member_bytes = bundle.read(member)
    except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
        raise EconomicReferenceOwnerError("official_master_zip_invalid") from exc
    try:
        lines = member_bytes.decode("cp949").splitlines()
    except UnicodeDecodeError as exc:
        raise EconomicReferenceOwnerError("official_master_encoding_invalid") from exc
    if not lines:
        raise EconomicReferenceOwnerError("official_master_rows_empty")
    trailer_width = sum(spec.widths)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    excluded_non_six_digit_symbol_count = 0
    for line_number, line in enumerate(lines, start=1):
        if len(line) <= trailer_width + 21:
            raise EconomicReferenceOwnerError(
                f"official_master_row_too_short:{spec.market}:{line_number}"
            )
        prefix = line[:-trailer_width]
        trailer = _split_fixed_width(line[-trailer_width:], spec.widths)
        symbol = prefix[:9].strip()
        standard_code = prefix[9:21].strip()
        korean_name = prefix[21:].strip()
        security_group = trailer[0]
        preferred_class = trailer[spec.preferred_index]
        if security_group != "ST" or preferred_class != "0":
            continue
        if len(symbol) != 6 or not symbol.isdigit():
            excluded_non_six_digit_symbol_count += 1
            continue
        if not standard_code or not korean_name:
            raise EconomicReferenceOwnerError(
                f"official_common_stock_identity_missing:{spec.market}:{line_number}"
            )
        if symbol in seen:
            raise EconomicReferenceOwnerError(
                f"official_common_stock_duplicate:{spec.market}:{symbol}"
            )
        seen.add(symbol)
        records.append(
            {
                "record_id": f"kis-{spec.market.lower()}-{symbol}-{effective_from}",
                "symbol": symbol,
                "listing_market": spec.market,
                "instrument_type": "EQUITY",
                "instrument_tax_class": "ordinary_taxable_equity_20bps",
                "effective_from": effective_from,
                "effective_to": None,
            }
        )
    if not records:
        raise EconomicReferenceOwnerError(
            f"official_common_stock_rows_empty:{spec.market}"
        )
    provenance = {
        "market": spec.market,
        "source_uri": spec.url,
        "archive_file_name": archive_path.name,
        "archive_sha256": _sha256(archive),
        "archive_size_bytes": len(archive),
        "member_name": spec.member_name,
        "member_sha256": _sha256(member_bytes),
        "member_size_bytes": len(member_bytes),
        "source_repository": KIS_REPOSITORY,
        "eligible_common_stock_count": len(records),
        "excluded_non_six_digit_symbol_count": excluded_non_six_digit_symbol_count,
    }
    return records, provenance, member_bytes


def _source_descriptor(
    *, kind: str, source_id: str, path: Path, raw: bytes, effective_from: str
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "kind": kind,
        "logical_path": f"policy://micro-reversion/{path.name}",
        "resolved_path": str(path),
        "sha256": _sha256(raw),
        "size_bytes": len(raw),
        "effective_from": effective_from,
        "effective_to": None,
    }


def build_daily_sources(
    *,
    target_date: str,
    policy_path: Path,
    output_root: Path,
    fetcher: Callable[[str], bytes] = _download,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    target = date.fromisoformat(target_date)
    policy, policy_raw = _load_policy(policy_path, target_date=target)
    effective_from = str(policy["effective_from"])
    generated = generated_at or datetime.now(KST)
    if generated.tzinfo is None:
        raise EconomicReferenceOwnerError("generated_at_timezone_missing")
    if generated.astimezone(KST).date() != target:
        raise EconomicReferenceOwnerError("official_master_target_date_mismatch")

    daily_root = Path(output_root) / "daily" / target_date
    upstream_rows: list[dict[str, Any]] = []
    symbol_records: list[dict[str, Any]] = []
    for spec in MASTER_SPECS:
        archive = fetcher(spec.url)
        if (
            not isinstance(archive, bytes)
            or not archive
            or len(archive) > MAX_MASTER_ARCHIVE_BYTES
        ):
            raise EconomicReferenceOwnerError("official_master_archive_size_invalid")
        records, provenance, _ = _parse_master(
            archive, spec=spec, effective_from=target_date
        )
        archive_path = daily_root / provenance["archive_file_name"]
        _atomic_write(archive_path, archive)
        provenance["archive_path"] = str(archive_path)
        provenance["retrieved_at"] = generated.isoformat()
        provenance["parser_source_commit"] = str(
            policy["official_symbol_master"]["parser_source_commit"]
        )
        upstream_rows.append(provenance)
        symbol_records.extend(records)
    symbols = [row["symbol"] for row in symbol_records]
    if len(symbols) != len(set(symbols)):
        raise EconomicReferenceOwnerError(
            "official_common_stock_cross_market_duplicate"
        )
    symbol_records.sort(key=lambda row: (row["listing_market"], row["symbol"]))

    broker_policy = policy["broker_fee"]
    tax_policy = policy["statutory_tax"]
    broker_source = {
        "schema": RAW_BROKER_FEE_SCHEMA,
        "source_id": f"operator-reviewed-kiwoom-fee-{effective_from}",
        "records": [
            {
                "record_id": f"kiwoom-cash-equity-fee-{effective_from}",
                "effective_from": effective_from,
                "effective_to": None,
                "venues": ["KRX", "NXT", "SOR"],
                "instrument_types": ["EQUITY"],
                "instrument_tax_classes": ["ordinary_taxable_equity_20bps"],
                "buy_fee_bps": broker_policy["buy_fee_bps"],
                "sell_fee_bps": broker_policy["sell_fee_bps"],
            }
        ],
    }
    tax_source = {
        "schema": RAW_STATUTORY_TAX_SCHEMA,
        "source_id": f"operator-reviewed-statutory-tax-{effective_from}",
        "records": [
            {
                "record_id": f"kospi-kosdaq-common-stock-tax-{effective_from}",
                "effective_from": effective_from,
                "effective_to": None,
                "listing_markets": ["KOSDAQ", "KOSPI"],
                "instrument_types": ["EQUITY"],
                "instrument_tax_classes": ["ordinary_taxable_equity_20bps"],
                "statutory_sell_tax_bps": tax_policy["sell_tax_bps"],
            }
        ],
    }
    symbol_source = {
        "schema": RAW_SYMBOL_MASTER_SCHEMA,
        "source_id": f"kis-official-common-stock-master-{target_date}",
        "upstream_sources": upstream_rows,
        "records": symbol_records,
    }

    source_values = {
        "broker_fee": broker_source,
        "statutory_tax": tax_source,
        "symbol_product_master": symbol_source,
    }
    descriptors: list[dict[str, Any]] = []
    for kind, value in source_values.items():
        path = daily_root / f"{kind}.json"
        raw = _canonical_bytes(value)
        _atomic_write(path, raw)
        descriptors.append(
            _source_descriptor(
                kind=kind,
                source_id=str(value["source_id"]),
                path=path,
                raw=raw,
                effective_from=(
                    target_date if kind == "symbol_product_master" else effective_from
                ),
            )
        )

    manifest = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "artifact_id": f"main-ai-economic-reference-{target_date}",
        "raw_sources": descriptors,
        "coverage_request": {
            "symbols": sorted(symbols),
            "venues": ["KRX", "NXT", "SOR"],
        },
        "uncertainty_buffer_bps": 0.0,
    }
    manifest_path = Path(output_root) / "economic_reference_sources.json"
    manifest_raw = _canonical_bytes(manifest)
    _atomic_write(manifest_path, manifest_raw)

    pricing = {
        "schema": PRICING_ARTIFACT_SCHEMA,
        "artifact_id": f"operator-zero-provider-pricing-{effective_from}",
        "review_status": "reviewed",
        "reviewed_at": str(policy["reviewed_at"]),
        "effective_from": effective_from,
        "effective_to": str(policy.get("effective_to") or "2099-12-31"),
        "pricing_basis": OPERATOR_ZERO_COST_BASIS,
        "raw_pricing_source_path": str(Path(policy_path).resolve()),
        "raw_pricing_source_bytes_sha256": _sha256(policy_raw),
        "raw_pricing_source_size_bytes": len(policy_raw),
        "prices": list(policy["provider_pricing"]["prices"]),
        "decision_authority": PRICING_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    pricing["artifact_content_sha256"] = pricing_artifact_content_sha256(pricing)
    pricing_path = Path(output_root) / "provider_pricing.json"
    pricing_raw = _canonical_bytes(pricing)
    _atomic_write(pricing_path, pricing_raw)

    body = {
        "schema": OWNER_REPORT_SCHEMA,
        "target_date": target_date,
        "generated_at": generated.isoformat(),
        "status": "pass",
        "policy_path": str(Path(policy_path).resolve()),
        "policy_sha256": _sha256(policy_raw),
        "effective_from": effective_from,
        "eligible_common_stock_count": len(symbol_records),
        "eligible_kospi_count": sum(
            row["listing_market"] == "KOSPI" for row in symbol_records
        ),
        "eligible_kosdaq_count": sum(
            row["listing_market"] == "KOSDAQ" for row in symbol_records
        ),
        "economic_manifest_path": str(manifest_path),
        "economic_manifest_sha256": _sha256(manifest_raw),
        "economic_manifest_size_bytes": len(manifest_raw),
        "provider_pricing_path": str(pricing_path),
        "provider_pricing_sha256": _sha256(pricing_raw),
        "provider_pricing_size_bytes": len(pricing_raw),
        "provider_pricing_content_sha256": pricing["artifact_content_sha256"],
        "provider_budget_basis": dict(policy["provider_budget_basis"]),
        **AUTHORITY_CONTRACT,
    }
    report = {**body, "artifact_content_sha256": content_sha256(body)}
    _atomic_write(daily_root / "owner_report.json", _canonical_bytes(report))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_daily_sources(
            target_date=args.target_date,
            policy_path=args.policy,
            output_root=args.output_root,
        )
    except (EconomicReferenceOwnerError, OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
