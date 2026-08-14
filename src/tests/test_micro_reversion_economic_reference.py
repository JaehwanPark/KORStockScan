from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.micro_reversion.ai_quality_bridge import (
    _verified_cost_config_from_path,
)
from src.engine.scalping.micro_reversion.economic_reference import (
    BRIDGE_COST_PROFILE_SCHEMA,
    BRIDGE_SYMBOL_MASTER_SCHEMA,
    DAILY_RESOLUTION_SCHEMA,
    RAW_BROKER_FEE_SCHEMA,
    RAW_STATUTORY_TAX_SCHEMA,
    RAW_SYMBOL_MASTER_SCHEMA,
    REVIEWED_COST_CATALOG_SCHEMA,
    SOURCE_MANIFEST_SCHEMA,
    atomic_write_json,
    build_daily_resolution,
    content_sha256,
    main,
)
from src.engine.scalping.micro_reversion.economic_reference_owner import MASTER_SPECS
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

TARGET_DATE = "2026-08-14"
GENERATED_AT = datetime.fromisoformat("2026-08-14T18:30:00+09:00")
ORDINARY_TAX_CLASS = "ordinary_taxable_equity_20bps"
KONEX_TAX_CLASS = "konex_taxable_equity_10bps"
UNSUPPORTED_TAX_CLASS = "unsupported_non_equity"
KIS_SOURCE_REPOSITORY = "https://github.com/koreainvestment/open-trading-api"
KIS_PARSER_COMMIT = "b093e42ba32d1df5f5ddad7a71cb715cbc800832"


def _broker_record(
    *,
    record_id: str = "broker-common-v1",
    venues: list[str] | None = None,
    tax_classes: list[str] | None = None,
    buy_fee_bps: float = 1.25,
    sell_fee_bps: float = 1.5,
) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "effective_from": "2026-06-05",
        "effective_to": None,
        "venues": venues or ["KRX"],
        "instrument_types": ["EQUITY"],
        "instrument_tax_classes": tax_classes or [ORDINARY_TAX_CLASS],
        "buy_fee_bps": buy_fee_bps,
        "sell_fee_bps": sell_fee_bps,
    }


def _tax_record(
    *,
    record_id: str = "statutory-common-v1",
    listing_markets: list[str] | None = None,
    tax_class: str = ORDINARY_TAX_CLASS,
    sell_tax_bps: float = 20.0,
) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "effective_from": "2026-06-05",
        "effective_to": None,
        "listing_markets": listing_markets or ["KOSDAQ", "KOSPI"],
        "instrument_types": ["EQUITY"],
        "instrument_tax_classes": [tax_class],
        "statutory_sell_tax_bps": sell_tax_bps,
    }


def _symbol_record(
    symbol: str = "005930",
    *,
    record_id: str | None = None,
    listing_market: str = "KOSPI",
    instrument_type: str = "EQUITY",
    tax_class: str = ORDINARY_TAX_CLASS,
    effective_from: str = "2026-06-05",
    effective_to: str | None = None,
) -> dict[str, Any]:
    return {
        "record_id": record_id or f"symbol-{symbol}-v1",
        "symbol": symbol,
        "listing_market": listing_market,
        "instrument_type": instrument_type,
        "instrument_tax_class": tax_class,
        "effective_from": effective_from,
        "effective_to": effective_to,
    }


def _write_raw(path: Path, payload: dict[str, Any]) -> bytes:
    raw = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()
    path.write_bytes(raw)
    return raw


def _descriptor(*, kind: str, source_id: str, path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "kind": kind,
        "logical_path": f"official://economic-reference/{path.name}",
        "resolved_path": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "effective_from": "2026-06-05",
        "effective_to": None,
    }


def _write_bundle(
    tmp_path: Path,
    *,
    broker_records: list[dict[str, Any]] | None = None,
    tax_records: list[dict[str, Any]] | None = None,
    symbol_records: list[dict[str, Any]] | None = None,
    coverage_symbols: list[str] | None = None,
    coverage_venues: list[str] | None = None,
    mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[Path, dict[str, Path], dict[str, Any]]:
    normalized_symbol_records = symbol_records or [_symbol_record()]
    upstream_sources = []
    for market in ("KOSPI", "KOSDAQ"):
        spec = next(row for row in MASTER_SPECS if row.market == market)
        member_name = f"{market.lower()}_code.mst"
        archive_path = tmp_path / f"{member_name}.zip"
        eligible = {
            str(record["symbol"])
            for record in normalized_symbol_records
            if record.get("listing_market") == market
            and record.get("instrument_type") == "EQUITY"
            and record.get("instrument_tax_class") == ORDINARY_TAX_CLASS
            and len(str(record.get("symbol") or "")) == 6
            and str(record.get("symbol") or "").isdigit()
        }
        rows: list[str] = []
        for symbol in sorted(eligible):
            trailer = [" " * width for width in spec.widths]
            trailer[0] = "ST"
            trailer[spec.preferred_index] = "0"
            rows.append(f"{symbol:<9}{('KR' + symbol):<12}ordinary" + "".join(trailer))
        if not rows:
            trailer = [" " * width for width in spec.widths]
            trailer[0] = "EF"
            trailer[spec.preferred_index] = "0"
            rows.append(f"{'069500':<9}{'KR069500':<12}excluded" + "".join(trailer))
        member_bytes = ("\n".join(rows) + "\n").encode("cp949")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr(member_name, member_bytes)
        archive_bytes = buffer.getvalue()
        archive_path.write_bytes(archive_bytes)
        upstream_sources.append(
            {
                "market": market,
                "source_uri": (
                    "https://new.real.download.dws.co.kr/common/master/"
                    f"{member_name}.zip"
                ),
                "archive_file_name": archive_path.name,
                "archive_path": str(archive_path),
                "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
                "archive_size_bytes": len(archive_bytes),
                "member_name": member_name,
                "member_sha256": hashlib.sha256(member_bytes).hexdigest(),
                "member_size_bytes": len(member_bytes),
                "source_repository": KIS_SOURCE_REPOSITORY,
                "eligible_common_stock_count": len(eligible),
                "excluded_non_six_digit_symbol_count": 0,
                "retrieved_at": GENERATED_AT.isoformat(),
                "parser_source_commit": KIS_PARSER_COMMIT,
            }
        )
    payloads = {
        "broker_fee": {
            "schema": RAW_BROKER_FEE_SCHEMA,
            "source_id": "official-broker-fee-2026",
            "records": broker_records or [_broker_record()],
        },
        "statutory_tax": {
            "schema": RAW_STATUTORY_TAX_SCHEMA,
            "source_id": "official-statutory-tax-2026",
            "records": tax_records or [_tax_record()],
        },
        "symbol_product_master": {
            "schema": RAW_SYMBOL_MASTER_SCHEMA,
            "source_id": "official-symbol-master-2026",
            "upstream_sources": upstream_sources,
            "records": normalized_symbol_records,
        },
    }
    paths: dict[str, Path] = {}
    descriptors: list[dict[str, Any]] = []
    for kind, payload in payloads.items():
        path = tmp_path / f"{kind}.json"
        raw = _write_raw(path, payload)
        paths[kind] = path
        descriptors.append(
            _descriptor(
                kind=kind,
                source_id=str(payload["source_id"]),
                path=path,
                raw=raw,
            )
        )
    manifest = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "artifact_id": "economic-reference-test-v2",
        "raw_sources": descriptors,
        "coverage_request": {
            "symbols": coverage_symbols or ["005930"],
            "venues": coverage_venues or ["KRX"],
        },
        "uncertainty_buffer_bps": 2.75,
    }
    if mutate_manifest is not None:
        mutate_manifest(manifest)
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path, paths, manifest


def _resolve(manifest_path: Path) -> dict[str, Any]:
    return build_daily_resolution(
        target_date=TARGET_DATE,
        source_manifest_path=manifest_path,
        generated_at=GENERATED_AT,
    )


def _assert_no_trading_authority(payload: dict[str, Any]) -> None:
    assert payload["runtime_effect"] is False
    assert payload["allowed_runtime_apply"] is False
    assert payload["trading_runtime_effect"] is False
    assert payload["trading_decision_effect"] is False
    assert payload["selection_authority"] is False
    assert payload["actual_order_submitted"] is False
    assert payload["broker_order_forbidden"] is True
    assert payload["provider_call_performed"] is False


def _assert_embedded_content_hash(payload: dict[str, Any]) -> None:
    body = {key: value for key, value in payload.items() if key != "content_sha256"}
    assert payload["content_sha256"] == content_sha256(body)


def test_verified_raw_sources_materialize_canonical_bridge_payloads(
    tmp_path: Path,
) -> None:
    manifest_path, paths, _ = _write_bundle(tmp_path)

    report = _resolve(manifest_path)

    assert report["schema"] == DAILY_RESOLUTION_SCHEMA
    assert report["status"] == "pass"
    assert report["verified"] is True
    assert report["tuning_input_allowed"] is True
    assert report["blockers"] == []
    assert report["summary"] == {
        "requested_pair_count": 1,
        "eligible_pair_count": 1,
        "excluded_pair_count": 0,
        "reviewed_cost_profile_count": 1,
        "symbol_master_record_count": 1,
        "source_contract_verified": True,
    }
    _assert_no_trading_authority(report)
    for source in report["source_artifacts"]:
        raw = paths[source["kind"]].read_bytes()
        assert source["logical_path"].startswith("official://")
        assert source["resolved_path"] == str(paths[source["kind"]])
        assert source["observed_sha256"] == hashlib.sha256(raw).hexdigest()
        assert source["observed_size_bytes"] == len(raw)
        assert source["verified"] is True
        _assert_no_trading_authority(source)

    catalog = report["canonical_reviewed_cost_payload"]
    assert catalog["schema"] == REVIEWED_COST_CATALOG_SCHEMA
    assert catalog["verified"] is True
    assert catalog["census"] == {
        "profile_count": 1,
        "venue_count": 1,
        "listing_market_count": 1,
        "instrument_type_count": 1,
        "instrument_tax_class_count": 1,
    }
    _assert_embedded_content_hash(catalog)
    _assert_no_trading_authority(catalog)
    assert report["canonical_reviewed_cost_payload_sha256"] == content_sha256(catalog)

    profile = catalog["profiles"][0]
    assert profile["buy_fee_bps"] == 1.25
    assert profile["sell_fee_bps"] == 1.5
    assert profile["statutory_sell_tax_bps"] == 20.0
    assert profile["uncertainty_buffer_bps"] == 2.75
    assert (
        profile["buy_fee_bps"]
        + profile["sell_fee_bps"]
        + profile["statutory_sell_tax_bps"]
        + profile["uncertainty_buffer_bps"]
        == 25.5
    )
    assert profile["source_bindings"]["symbol_master_source_sha256"]
    _assert_embedded_content_hash(profile)
    _assert_no_trading_authority(profile)

    bridge_payload = profile["bridge_reviewed_cost_payload"]
    assert bridge_payload["schema"] == BRIDGE_COST_PROFILE_SCHEMA
    assert profile["bridge_reviewed_cost_payload_sha256"] == content_sha256(
        bridge_payload
    )
    _assert_no_trading_authority(bridge_payload)
    bridge_path = tmp_path / "bridge_cost.json"
    atomic_write_json(bridge_path, bridge_payload)
    bridge_config = _verified_cost_config_from_path(
        bridge_path, target_date=date.fromisoformat(TARGET_DATE)
    )
    assert bridge_config.cost_profile_verified is True
    assert bridge_config.statutory_sell_tax_bps == 20.0

    symbol_payload = report["canonical_symbol_master_payload"]
    assert symbol_payload["schema"] == BRIDGE_SYMBOL_MASTER_SCHEMA
    assert symbol_payload["verified"] is True
    assert symbol_payload["census"] == {"record_count": 1, "symbol_count": 1}
    assert "#sha256=" in symbol_payload["records"][0]["source_reference"]
    _assert_embedded_content_hash(symbol_payload)
    _assert_no_trading_authority(symbol_payload)
    symbol_path = tmp_path / "symbol_master_bridge.json"
    atomic_write_json(symbol_path, symbol_payload)
    master = VerifiedSymbolMaster.from_json_path(symbol_path)
    assert master.lookup("005930", as_of=date.fromisoformat(TARGET_DATE)).record


def test_canonical_cost_catalog_passes_source_bundle_cost_contract(
    tmp_path: Path,
) -> None:
    manifest_path, _, _ = _write_bundle(tmp_path)
    report = _resolve(manifest_path)
    catalog = report["canonical_reviewed_cost_payload"]
    profile = catalog["profiles"][0]
    catalog_path = tmp_path / "reviewed_cost_catalog.json"
    atomic_write_json(catalog_path, catalog)
    config = _verified_cost_config_from_path(
        catalog_path, target_date=date.fromisoformat(TARGET_DATE)
    )
    evidence = {
        "economics": {
            "cost_profile_verified": True,
            "cost_profile_scope_status": "reviewed_artifact_applicable",
            "instrument_type": "EQUITY",
            "listing_market": "KOSPI",
            "instrument_tax_class": ORDINARY_TAX_CLASS,
            "cost_catalog_content_sha256": catalog["content_sha256"],
            "selected_cost_profile_id": profile["profile_id"],
            "selected_cost_profile_content_sha256": profile["content_sha256"],
            "buy_fee_bps": profile["buy_fee_bps"],
            "sell_fee_bps": profile["sell_fee_bps"],
            "statutory_sell_tax_bps": profile["statutory_sell_tax_bps"],
            "uncertainty_buffer_bps": profile["uncertainty_buffer_bps"],
        }
    }

    quality._validate_micro_reversion_cost_profile_artifact(
        config=config,
        artifact=None,
        target_date=TARGET_DATE,
        effective_venue="KRX",
        evidence=evidence,
    )

    evidence["economics"]["selected_cost_profile_content_sha256"] = "0" * 64
    with pytest.raises(
        ValueError, match="micro_reversion_selected_cost_profile_hash_mismatch"
    ):
        quality._validate_micro_reversion_cost_profile_artifact(
            config=config,
            artifact=None,
            target_date=TARGET_DATE,
            effective_venue="KRX",
            evidence=evidence,
        )


def test_missing_manifest_emits_durable_blocked_artifact(tmp_path: Path) -> None:
    missing = tmp_path / "missing-manifest.json"

    report = _resolve(missing)

    assert report["status"] == "blocked"
    assert report["blockers"] == ["source_manifest_missing"]
    assert report["verified"] is False
    assert report["tuning_input_allowed"] is False
    assert report["canonical_reviewed_cost_payload"]["profiles"] == []
    assert report["canonical_reviewed_cost_payload"]["verified"] is False
    assert report["canonical_symbol_master_payload"]["records"] == []
    assert report["canonical_symbol_master_payload"]["verified"] is False
    _assert_no_trading_authority(report)


@pytest.mark.parametrize(
    ("mutation", "expected_blocker"),
    [
        ("tamper", "source_sha256_mismatch:official-broker-fee-2026"),
        ("missing", "source_file_missing:official-broker-fee-2026"),
        ("size", "source_size_mismatch:official-broker-fee-2026"),
    ],
)
def test_raw_source_missing_tamper_and_size_mismatch_fail_closed(
    tmp_path: Path, mutation: str, expected_blocker: str
) -> None:
    manifest_path, paths, manifest = _write_bundle(tmp_path)
    broker_path = paths["broker_fee"]
    if mutation == "tamper":
        broker_path.write_bytes(broker_path.read_bytes().replace(b"1.25", b"9.25"))
    elif mutation == "missing":
        broker_path.unlink()
    else:
        manifest["raw_sources"][0]["size_bytes"] += 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert expected_blocker in report["blockers"]
    assert report["summary"]["eligible_pair_count"] == 0
    assert report["canonical_reviewed_cost_payload"]["verified"] is False
    assert report["canonical_symbol_master_payload"]["verified"] is False


def test_official_symbol_upstream_archive_tamper_fails_closed(tmp_path: Path) -> None:
    manifest_path, paths, _ = _write_bundle(tmp_path)
    payload = json.loads(paths["symbol_product_master"].read_text(encoding="utf-8"))
    archive_path = Path(payload["upstream_sources"][0]["archive_path"])
    archive_path.write_bytes(archive_path.read_bytes() + b"tampered")

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert any(
        "archive_hash_or_size_mismatch" in blocker for blocker in report["blockers"]
    )
    assert report["summary"]["eligible_pair_count"] == 0


def test_official_symbol_normalized_records_must_derive_from_archives(
    tmp_path: Path,
) -> None:
    manifest_path, paths, manifest = _write_bundle(tmp_path)
    payload = json.loads(paths["symbol_product_master"].read_text(encoding="utf-8"))
    payload["records"][0]["symbol"] = "000660"
    raw = _write_raw(paths["symbol_product_master"], payload)
    descriptor = next(
        row for row in manifest["raw_sources"] if row["kind"] == "symbol_product_master"
    )
    descriptor["sha256"] = hashlib.sha256(raw).hexdigest()
    descriptor["size_bytes"] = len(raw)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert (
        "official_symbol_normalized_records_derivation_mismatch" in report["blockers"]
    )
    assert report["summary"]["eligible_pair_count"] == 0


def test_input_verified_flag_is_rejected_instead_of_trusted(tmp_path: Path) -> None:
    def add_forbidden_flag(manifest: dict[str, Any]) -> None:
        manifest["verified"] = True

    manifest_path, _, _ = _write_bundle(tmp_path, mutate_manifest=add_forbidden_flag)

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert "input_verified_flag_forbidden:source_manifest" in report["blockers"]
    assert report["verified"] is False
    assert report["canonical_reviewed_cost_payload"]["verified"] is False
    assert report["canonical_symbol_master_payload"]["verified"] is False


def test_raw_source_verified_flag_is_rejected_even_with_matching_bytes(
    tmp_path: Path,
) -> None:
    manifest_path, paths, manifest = _write_bundle(tmp_path)
    broker_payload = json.loads(paths["broker_fee"].read_bytes())
    broker_payload["verified"] = True
    raw = _write_raw(paths["broker_fee"], broker_payload)
    manifest["raw_sources"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["raw_sources"][0]["size_bytes"] = len(raw)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert (
        "input_verified_flag_forbidden:official-broker-fee-2026" in report["blockers"]
    )
    broker_source = next(
        source
        for source in report["source_artifacts"]
        if source["kind"] == "broker_fee"
    )
    assert broker_source["verified"] is False


def test_overlapping_records_are_ambiguous_and_excluded(tmp_path: Path) -> None:
    records = [
        _symbol_record(record_id="symbol-005930-left"),
        _symbol_record(record_id="symbol-005930-right", effective_from="2026-07-01"),
    ]
    manifest_path, _, _ = _write_bundle(tmp_path, symbol_records=records)

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert (
        "overlapping_symbol_record_windows:005930:"
        "symbol-005930-left:symbol-005930-right" in report["blockers"]
    )
    reasons = report["coverage_rows"][0]["reason_codes"]
    assert "ambiguous_active_symbol_record:005930" in reasons
    assert report["coverage_rows"][0]["status"] == "excluded"


def test_overlapping_source_windows_block_ambiguous_owner(tmp_path: Path) -> None:
    def add_overlapping_broker_source(manifest: dict[str, Any]) -> None:
        duplicate = dict(manifest["raw_sources"][0])
        duplicate["source_id"] = "official-broker-fee-overlap"
        duplicate["logical_path"] = "official://economic-reference/broker-overlap"
        manifest["raw_sources"].append(duplicate)

    manifest_path, _, _ = _write_bundle(
        tmp_path, mutate_manifest=add_overlapping_broker_source
    )

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert "ambiguous_active_source:broker_fee" in report["blockers"]
    assert any(
        blocker.startswith("overlapping_source_windows:broker_fee:")
        for blocker in report["blockers"]
    )


def test_official_tax_content_must_match_statutory_policy(tmp_path: Path) -> None:
    manifest_path, _, _ = _write_bundle(
        tmp_path, tax_records=[_tax_record(sell_tax_bps=19.0)]
    )

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert any(
        blocker.startswith("statutory_tax_policy_mismatch:")
        for blocker in report["blockers"]
    )
    assert report["summary"]["eligible_pair_count"] == 0
    tax_source = next(
        source
        for source in report["source_artifacts"]
        if source["kind"] == "statutory_tax"
    )
    assert tax_source["verified"] is False
    assert any(
        blocker.startswith("statutory_tax_policy_mismatch:")
        for blocker in tax_source["blockers"]
    )


@pytest.mark.parametrize("instrument_type", ["ETF", "ETN", "REIT"])
def test_non_equity_products_are_explicit_row_exclusions(
    tmp_path: Path, instrument_type: str
) -> None:
    symbol = {"ETF": "069500", "ETN": "500001", "REIT": "088980"}[instrument_type]
    manifest_path, _, _ = _write_bundle(
        tmp_path,
        symbol_records=[
            _symbol_record(
                symbol,
                instrument_type=instrument_type,
                tax_class=UNSUPPORTED_TAX_CLASS,
            )
        ],
        coverage_symbols=[symbol],
    )

    report = _resolve(manifest_path)

    assert report["status"] == "blocked"
    assert report["blockers"] == []
    reasons = report["coverage_rows"][0]["reason_codes"]
    assert f"unsupported_instrument_type:{instrument_type}" in reasons
    assert "statutory_tax_scope_uncovered" in reasons
    assert report["canonical_reviewed_cost_payload"]["profiles"] == []


def test_konex_is_excluded_while_supported_krx_row_remains_eligible(
    tmp_path: Path,
) -> None:
    broker = _broker_record(tax_classes=[KONEX_TAX_CLASS, ORDINARY_TAX_CLASS])
    taxes = [
        _tax_record(),
        _tax_record(
            record_id="statutory-konex-v1",
            listing_markets=["KONEX"],
            tax_class=KONEX_TAX_CLASS,
            sell_tax_bps=10.0,
        ),
    ]
    symbols = [
        _symbol_record(),
        _symbol_record(
            "123456",
            listing_market="KONEX",
            tax_class=KONEX_TAX_CLASS,
        ),
    ]
    manifest_path, _, _ = _write_bundle(
        tmp_path,
        broker_records=[broker],
        tax_records=taxes,
        symbol_records=symbols,
        coverage_symbols=["005930", "123456"],
    )

    report = _resolve(manifest_path)

    assert report["status"] == "partial"
    assert report["tuning_input_allowed"] is True
    rows = {row["symbol"]: row for row in report["coverage_rows"]}
    assert rows["005930"]["status"] == "eligible"
    assert rows["123456"]["status"] == "excluded"
    assert "unsupported_listing_market:KONEX" in rows["123456"]["reason_codes"]


def test_nxt_sor_and_pre_coverage_do_not_receive_krx_fallback(tmp_path: Path) -> None:
    manifest_path, _, _ = _write_bundle(
        tmp_path,
        coverage_venues=["KRX", "NXT", "SOR", "PREMARKET"],
    )

    report = _resolve(manifest_path)

    assert report["status"] == "partial"
    assert report["tuning_input_allowed"] is True
    rows = {row["venue"]: row for row in report["coverage_rows"]}
    assert rows["KRX"]["status"] == "eligible"
    assert rows["NXT"]["status"] == "excluded"
    assert "broker_fee_venue_uncovered:NXT" in rows["NXT"]["reason_codes"]
    assert rows["SOR"]["status"] == "excluded"
    assert "broker_fee_venue_uncovered:SOR" in rows["SOR"]["reason_codes"]
    assert rows["PREMARKET"]["status"] == "excluded"
    assert "premarket_venue_uncovered:PREMARKET" in rows["PREMARKET"]["reason_codes"]
    assert len(report["canonical_reviewed_cost_payload"]["profiles"]) == 1


def test_cli_atomically_writes_blocked_or_ready_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest_path, _, _ = _write_bundle(tmp_path)
    output = tmp_path / "daily" / "economic_reference.json"

    exit_code = main(
        [
            "--target-date",
            TARGET_DATE,
            "--source-manifest",
            str(manifest_path),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["status"] == "pass"
    assert persisted["artifact_content_sha256"] == content_sha256(
        {
            key: value
            for key, value in persisted.items()
            if key != "artifact_content_sha256"
        }
    )
    stdout = json.loads(capsys.readouterr().out)
    assert stdout["output"] == str(output)
    assert stdout["provider_call_performed"] is False
    assert not list(output.parent.glob(f".{output.name}.*.tmp"))
