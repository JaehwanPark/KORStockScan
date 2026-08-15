from __future__ import annotations

import io
import json
import zipfile
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from src.engine.scalping.micro_reversion.ai_quality_cycle import (
    _economic_outputs,
    _validate_economic_owner_report,
)
from src.engine.scalping.micro_reversion.economic_reference import (
    build_daily_resolution,
    content_sha256,
)
from src.engine.scalping.micro_reversion.economic_reference_owner import (
    KIS_KOSDAQ_MASTER_URL,
    KIS_KOSPI_MASTER_URL,
    KIS_REPOSITORY,
    MASTER_SPECS,
    OPERATOR_ZERO_COST_BASIS,
    POLICY_SCHEMA,
    _REVIEWED_AI_TRACE_BASIS,
    _load_policy,
    EconomicReferenceOwnerError,
    build_daily_sources,
)
from src.engine.scalping.micro_reversion.provider_budget import (
    load_reviewed_pricing_artifact,
)


def _policy() -> dict[str, Any]:
    return {
        "schema": POLICY_SCHEMA,
        "policy_id": "main-ai-economic-policy-2026-08-18-v1",
        "effective_from": "2026-08-18",
        "effective_to": None,
        "reviewed_at": "2026-08-15T08:00:00+09:00",
        "broker_fee": {"buy_fee_bps": 1.5, "sell_fee_bps": 1.5},
        "statutory_tax": {"sell_tax_bps": 20.0},
        "official_symbol_master": {
            "source_repository": KIS_REPOSITORY,
            "parser_source_commit": "b093e42ba32d1df5f5ddad7a71cb715cbc800832",
            "allowed_listing_markets": ["KOSDAQ", "KOSPI"],
            "required_security_group_code": "ST",
            "required_preferred_class_code": "0",
        },
        "provider_pricing": {
            "pricing_basis": OPERATOR_ZERO_COST_BASIS,
            "prices": [
                {
                    "provider": "openai",
                    "model": "gpt-5-nano",
                    "input_usd_per_million_tokens": "0",
                    "output_usd_per_million_tokens": "0",
                },
                {
                    "provider": "openai",
                    "model": "gpt-5.4-nano",
                    "input_usd_per_million_tokens": "0",
                    "output_usd_per_million_tokens": "0",
                },
                {
                    "provider": "openai",
                    "model": "gpt-5.4-mini",
                    "input_usd_per_million_tokens": "0",
                    "output_usd_per_million_tokens": "0",
                },
                {
                    "provider": "bedrock",
                    "model": "qwen3_32b",
                    "input_usd_per_million_tokens": "0",
                    "output_usd_per_million_tokens": "0",
                },
                {
                    "provider": "bedrock",
                    "model": "nova_lite_v2",
                    "input_usd_per_million_tokens": "0",
                    "output_usd_per_million_tokens": "0",
                },
            ],
        },
        "provider_budget_basis": {
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
            "source_artifacts": [
                {
                    "target_date": observed_date,
                    "logical_path": (
                        "data/ai_decision_trace/"
                        f"ai_decision_trace_{observed_date}.jsonl"
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
            ],
        },
        "decision_authority": "offline_economic_reference_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _master_line(
    *, market: str, symbol: str, name: str, group: str = "ST", preferred: str = "0"
) -> str:
    spec = next(row for row in MASTER_SPECS if row.market == market)
    trailer = [" " * width for width in spec.widths]
    trailer[0] = group.ljust(spec.widths[0])
    trailer[spec.preferred_index] = preferred
    prefix = f"{symbol:<9}{('KR' + symbol):<12}{name}"
    return prefix + "".join(trailer)


def _archive(market: str) -> bytes:
    spec = next(row for row in MASTER_SPECS if row.market == market)
    rows = [
        _master_line(
            market=market,
            symbol="005930" if market == "KOSPI" else "000250",
            name="ordinary",
        ),
        _master_line(
            market=market,
            symbol="005935" if market == "KOSPI" else "021045",
            name="preferred",
            preferred="1",
        ),
        _master_line(
            market=market,
            symbol="069500" if market == "KOSPI" else "123456",
            name="not-stock",
            group="EF",
        ),
    ]
    member = ("\n".join(rows) + "\n").encode("cp949")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(spec.member_name, member)
    return output.getvalue()


def _write_policy(tmp_path: Path, payload: dict[str, Any] | None = None) -> Path:
    path = tmp_path / "policy.json"
    path.write_text(
        json.dumps(payload or _policy(), ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def test_repository_policy_is_effective_on_requested_start_date() -> None:
    policy_path = (
        Path(__file__).parents[2]
        / "data"
        / "config"
        / "micro_reversion_economic_policy.json"
    )

    policy, raw = _load_policy(policy_path, target_date=date(2026, 8, 18))

    assert policy["effective_from"] == "2026-08-18"
    assert policy["provider_budget_basis"]["daily_parent_cap"] == 130
    assert policy["provider_budget_basis"]["maximum_logical_request_count"] == 390
    assert policy["provider_budget_basis"]["daily_attempt_cap"] == 390
    assert (
        policy["provider_budget_basis"]["daily_parent_cap"]
        * policy["provider_budget_basis"]["logical_requests_per_parent"]
        == policy["provider_budget_basis"]["maximum_logical_request_count"]
    )
    assert 49.9 <= (
        100
        * policy["provider_budget_basis"]["daily_attempt_cap"]
        / policy["provider_budget_basis"]["evaluated_call_median"]
    ) <= 50.0
    assert len(policy["provider_budget_basis"]["source_artifacts"]) == 5
    assert raw == policy_path.read_bytes()


def test_owner_builds_only_official_kospi_kosdaq_common_stocks(
    tmp_path: Path,
) -> None:
    policy_path = _write_policy(tmp_path)
    archives = {
        KIS_KOSPI_MASTER_URL: _archive("KOSPI"),
        KIS_KOSDAQ_MASTER_URL: _archive("KOSDAQ"),
    }

    report = build_daily_sources(
        target_date="2026-08-18",
        policy_path=policy_path,
        output_root=tmp_path / "output",
        fetcher=archives.__getitem__,
        generated_at=datetime.fromisoformat("2026-08-18T18:30:00+09:00"),
    )
    resolution = build_daily_resolution(
        target_date="2026-08-18",
        source_manifest_path=Path(report["economic_manifest_path"]),
        generated_at=datetime.fromisoformat("2026-08-18T18:31:00+09:00"),
    )
    pricing = load_reviewed_pricing_artifact(
        Path(report["provider_pricing_path"]),
        as_of_date=date(2026, 8, 18),
    )
    cost_payload, symbol_payload = _economic_outputs(resolution)
    _validate_economic_owner_report(
        report,
        target_date="2026-08-18",
        policy_path=policy_path,
        manifest_path=Path(report["economic_manifest_path"]),
        pricing_path=Path(report["provider_pricing_path"]),
    )

    assert report["eligible_common_stock_count"] == 2
    assert len(cost_payload["profiles"]) == 6
    assert len(symbol_payload["records"]) == 2
    assert report["eligible_kospi_count"] == 1
    assert report["eligible_kosdaq_count"] == 1
    assert resolution["status"] == "pass"
    assert resolution["summary"]["symbol_master_record_count"] == 2
    assert {
        row["symbol"]
        for row in resolution["canonical_symbol_master_payload"]["records"]
    } == {"000250", "005930"}
    assert all(
        profile["buy_fee_bps"] == 1.5
        and profile["sell_fee_bps"] == 1.5
        and profile["statutory_sell_tax_bps"] == 20.0
        and profile["uncertainty_buffer_bps"] == 0.0
        for profile in resolution["canonical_reviewed_cost_payload"]["profiles"]
    )
    assert pricing.pricing_basis == OPERATOR_ZERO_COST_BASIS
    assert all(
        row.input_usd_per_million_tokens == 0 and row.output_usd_per_million_tokens == 0
        for row in pricing.prices
    )
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False


def test_cycle_owner_receipt_rejects_manifest_changed_after_owner(
    tmp_path: Path,
) -> None:
    policy_path = _write_policy(tmp_path)
    archives = {
        KIS_KOSPI_MASTER_URL: _archive("KOSPI"),
        KIS_KOSDAQ_MASTER_URL: _archive("KOSDAQ"),
    }
    report = build_daily_sources(
        target_date="2026-08-18",
        policy_path=policy_path,
        output_root=tmp_path / "output",
        fetcher=archives.__getitem__,
        generated_at=datetime.fromisoformat("2026-08-18T18:30:00+09:00"),
    )
    manifest_path = Path(report["economic_manifest_path"])
    manifest_path.write_bytes(manifest_path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="owner_report_hash_mismatch"):
        _validate_economic_owner_report(
            report,
            target_date="2026-08-18",
            policy_path=policy_path,
            manifest_path=manifest_path,
            pricing_path=Path(report["provider_pricing_path"]),
        )


def test_cycle_rejects_self_rehashed_nonreviewed_fee(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path)
    archives = {
        KIS_KOSPI_MASTER_URL: _archive("KOSPI"),
        KIS_KOSDAQ_MASTER_URL: _archive("KOSDAQ"),
    }
    report = build_daily_sources(
        target_date="2026-08-18",
        policy_path=policy_path,
        output_root=tmp_path / "output",
        fetcher=archives.__getitem__,
        generated_at=datetime.fromisoformat("2026-08-18T18:30:00+09:00"),
    )
    resolution = build_daily_resolution(
        target_date="2026-08-18",
        source_manifest_path=Path(report["economic_manifest_path"]),
        generated_at=datetime.fromisoformat("2026-08-18T18:31:00+09:00"),
    )
    tampered = deepcopy(resolution)
    cost = tampered["canonical_reviewed_cost_payload"]
    cost["profiles"][0]["buy_fee_bps"] = 1.6
    cost["content_sha256"] = content_sha256(
        {key: value for key, value in cost.items() if key != "content_sha256"}
    )
    tampered["canonical_reviewed_cost_payload_sha256"] = content_sha256(cost)
    tampered["artifact_content_sha256"] = content_sha256(
        {
            key: value
            for key, value in tampered.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(ValueError, match="cost_policy_mismatch"):
        _economic_outputs(tampered)


def test_owner_blocks_before_effective_date_without_fetching(tmp_path: Path) -> None:
    called = False

    def fetcher(_: str) -> bytes:
        nonlocal called
        called = True
        raise AssertionError("must not fetch")

    with pytest.raises(EconomicReferenceOwnerError, match="not_yet_effective"):
        build_daily_sources(
            target_date="2026-08-17",
            policy_path=_write_policy(tmp_path),
            output_root=tmp_path / "output",
            fetcher=fetcher,
        )

    assert called is False


def test_owner_rejects_unreviewed_nonzero_provider_cost(tmp_path: Path) -> None:
    policy = _policy()
    policy["provider_pricing"]["prices"][0]["input_usd_per_million_tokens"] = "1"

    with pytest.raises(EconomicReferenceOwnerError, match="price_nonzero"):
        build_daily_sources(
            target_date="2026-08-18",
            policy_path=_write_policy(tmp_path, policy),
            output_root=tmp_path / "output",
            fetcher=lambda _: b"not-called",
        )
