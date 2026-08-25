import gzip
import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from src.engine.scalping.micro_reversion import symbol_master as symbol_master_module
from src.engine.scalping.micro_reversion.symbol_master import (
    MetadataConflictStatus,
    SymbolLookupStatus,
    SymbolMasterRecord,
    VerifiedSymbolMaster,
)
from src.engine.scalping.micro_reversion.tax import InstrumentType, ListingMarket

_SOURCE_HASH = "a" * 64
_SOURCE_LOGICAL_PATH = "policy://micro-reversion/symbol_product_master.json"
_FORBIDDEN_USES = [
    "live_prompt_or_threshold_mutation",
    "broker_order_submission_or_cancel",
    "automated_sell_or_position_sizing",
    "provider_route_or_bot_state_change",
    "position_cap_or_cooldown_change",
    "hard_protect_emergency_or_stale_guard_bypass",
    "unverified_cost_or_symbol_promotion",
]
_AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "trading_runtime_effect": False,
    "trading_decision_effect": False,
    "selection_authority": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "provider_call_performed": False,
    "forbidden_uses": _FORBIDDEN_USES,
}


def _producer_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _record(**overrides):
    values = {
        "symbol": "005930",
        "listing_market": ListingMarket.KOSPI,
        "instrument_type": InstrumentType.EQUITY,
        "instrument_tax_class": "ordinary_taxable_equity_20bps",
        "effective_from": date(2026, 1, 1),
        "effective_to": None,
        "metadata_source": "official_symbol_product_master_v2",
        "source_reference": f"{_SOURCE_LOGICAL_PATH}#sha256={_SOURCE_HASH}",
        "verified_at": "2026-08-08T10:00:00+09:00",
        "conflict_status": MetadataConflictStatus.CLEAN,
    }
    values.update(overrides)
    return SymbolMasterRecord(**values)


def _master_payload() -> dict:
    body = {
        "schema": "scalp_micro_reversion_symbol_master_v1",
        "artifact_id": "test-symbol-master-2026-08-25",
        "source_contract_schema": "micro_reversion_raw_symbol_product_master_v3",
        "verification_status": "verified",
        "verified": True,
        "decision_authority": "instrument_metadata_source_only",
        **_AUTHORITY,
        "source_artifacts": [
            {
                "source_id": "kis-official-common-stock-master-2026-08-25",
                "kind": "symbol_product_master",
                "logical_path": _SOURCE_LOGICAL_PATH,
                "expected_sha256": _SOURCE_HASH,
                "expected_size_bytes": 100,
                "observed_sha256": _SOURCE_HASH,
                "observed_size_bytes": 100,
                "record_count": 1,
                "payload_schema": "micro_reversion_raw_symbol_product_master_v3",
                "status": "verified",
                "verified": True,
                "blockers": [],
                "decision_authority": "offline_economic_reference_source_only",
                **_AUTHORITY,
            }
        ],
        "census": {"record_count": 1, "symbol_count": 1},
        "records": [_record().as_dict()],
    }
    return {**body, "content_sha256": _producer_hash(body)}


def _minimal_legacy_payload() -> dict:
    return {
        "schema": "scalp_micro_reversion_symbol_master_v1",
        "decision_authority": "instrument_metadata_source_only",
        "runtime_effect": False,
        "records": [_record().as_dict()],
    }


def test_verified_symbol_master_effective_date_lookup() -> None:
    master = VerifiedSymbolMaster([_record()])

    result = master.lookup("A005930", as_of=date(2026, 8, 8))

    assert result.status is SymbolLookupStatus.VERIFIED
    assert result.record is not None
    assert result.record.instrument_tax_class.value == "ordinary_taxable_equity_20bps"


def test_verified_symbol_master_from_payload_uses_supplied_generation() -> None:
    master = VerifiedSymbolMaster.from_payload(
        _master_payload(),
        require_canonical_owner=True,
    )

    result = master.lookup("005930", as_of=date(2026, 8, 8))

    assert result.status is SymbolLookupStatus.VERIFIED
    assert result.record is not None


def test_current_authority_rejects_minimal_legacy_symbol_master() -> None:
    with pytest.raises(ValueError, match="symbol_master_canonical_fields_invalid"):
        VerifiedSymbolMaster.from_payload(
            _minimal_legacy_payload(),
            require_canonical_owner=True,
        )


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    (
        ("verified", False, "symbol_master_canonical_verified_invalid"),
        (
            "verification_status",
            "blocked",
            "symbol_master_canonical_verification_status_invalid",
        ),
        (
            "source_contract_schema",
            "fabricated",
            "symbol_master_canonical_source_contract_schema_invalid",
        ),
        (
            "runtime_effect",
            True,
            "symbol_master_canonical_authority_invalid:runtime_effect",
        ),
    ),
)
def test_current_authority_rejects_resealed_canonical_header_tampering(
    field: str, value: object, expected_error: str
) -> None:
    payload = _master_payload()
    payload[field] = value
    payload["content_sha256"] = _producer_hash(
        {key: item for key, item in payload.items() if key != "content_sha256"}
    )

    with pytest.raises(ValueError, match=expected_error):
        VerifiedSymbolMaster.from_payload(payload, require_canonical_owner=True)


def test_current_authority_rejects_census_or_content_hash_tampering() -> None:
    bad_census = _master_payload()
    bad_census["census"]["record_count"] = 2
    bad_census["content_sha256"] = _producer_hash(
        {key: item for key, item in bad_census.items() if key != "content_sha256"}
    )
    with pytest.raises(ValueError, match="symbol_master_canonical_census_mismatch"):
        VerifiedSymbolMaster.from_payload(
            bad_census,
            require_canonical_owner=True,
        )

    bad_hash = _master_payload()
    bad_hash["content_sha256"] = "0" * 64
    with pytest.raises(
        ValueError,
        match="symbol_master_canonical_content_sha256_mismatch",
    ):
        VerifiedSymbolMaster.from_payload(bad_hash, require_canonical_owner=True)


def test_current_authority_rejects_resealed_fabricated_master_identity() -> None:
    payload = _master_payload()
    payload["source_artifacts"][0]["source_id"] = "fabricated-master"
    payload["content_sha256"] = _producer_hash(
        {key: item for key, item in payload.items() if key != "content_sha256"}
    )

    with pytest.raises(
        ValueError,
        match="symbol_master_canonical_source_identity_invalid",
    ):
        VerifiedSymbolMaster.from_payload(payload, require_canonical_owner=True)


def test_symbol_master_path_is_strictly_read_once_before_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "symbol_master.json"
    path.write_text(json.dumps(_master_payload()), encoding="utf-8")
    strict_reads: list[Path] = []
    strict_reader = symbol_master_module.read_json_object_strict

    def read_then_replace(selected: Path) -> dict:
        payload = strict_reader(selected)
        strict_reads.append(selected)
        selected.write_text(
            json.dumps({**_master_payload(), "records": []}),
            encoding="utf-8",
        )
        return payload

    monkeypatch.setattr(
        symbol_master_module,
        "read_json_object_strict",
        read_then_replace,
    )

    master = VerifiedSymbolMaster.from_json_path(path)

    assert strict_reads == [path]
    assert master.lookup("005930", as_of=date(2026, 8, 8)).status is (
        SymbolLookupStatus.VERIFIED
    )


@pytest.mark.parametrize(
    ("unsafe_generation", "expected_error"),
    (
        ("broken_symlink", "json_artifact_path_type_invalid"),
        ("duplicate_key", "duplicate JSON key:schema"),
        ("divergent_plain_gzip", "json_artifact_plain_gzip_conflict"),
    ),
)
def test_symbol_master_strict_reader_rejects_unsafe_generation(
    tmp_path: Path,
    unsafe_generation: str,
    expected_error: str,
) -> None:
    path = tmp_path / "symbol_master.json"
    if unsafe_generation == "broken_symlink":
        path.symlink_to(tmp_path / "missing-symbol-master.json")
    elif unsafe_generation == "duplicate_key":
        path.write_text(
            '{"schema":"scalp_micro_reversion_symbol_master_v1",'
            '"schema":"scalp_micro_reversion_symbol_master_v1","records":[]}',
            encoding="utf-8",
        )
    else:
        path.write_text(json.dumps(_master_payload()), encoding="utf-8")
        divergent = {**_master_payload(), "records": []}
        path.with_name(f"{path.name}.gz").write_bytes(
            gzip.compress(json.dumps(divergent).encode("utf-8"))
        )

    with pytest.raises(ValueError, match=expected_error):
        VerifiedSymbolMaster.from_json_path(path)


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
