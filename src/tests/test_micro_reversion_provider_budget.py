import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from multiprocessing import get_context
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.micro_reversion.provider_budget import (
    PRICING_ARTIFACT_SCHEMA,
    PRICING_AUTHORITY,
    OPERATOR_ZERO_COST_BASIS,
    PUBLIC_RATE_BASIS,
    AttemptIdentity,
    BudgetExceededError,
    BudgetLedgerIntegrityError,
    CircuitBreakerOpenError,
    DuplicateAttemptError,
    PricingArtifactError,
    ProviderModelSelection,
    ProviderBudgetLedger,
    ProviderBudgetError,
    SettlementError,
    SingleWorkerRequiredError,
    TokenCeiling,
    conservative_token_ceiling,
    load_reviewed_pricing_artifact,
    pricing_artifact_content_sha256,
    validate_batch_pricing_coverage,
)

KST = ZoneInfo("Asia/Seoul")
EXECUTION_DATE = date(2026, 8, 14)
NOW = datetime(2026, 8, 14, 21, 30, tzinfo=KST)


def _write_pricing_artifact(
    tmp_path: Path,
    *,
    effective_from: str = "2026-08-01",
    effective_to: str = "2026-08-31",
    prices: list[dict] | None = None,
    raw_hash_override: str | None = None,
    raw_size_override: int | None = None,
    pricing_basis: str = PUBLIC_RATE_BASIS,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    raw_path = tmp_path / "provider-pricing-source.txt"
    raw_bytes = b"reviewed provider pricing source\n"
    raw_path.write_bytes(raw_bytes)
    payload = {
        "schema": PRICING_ARTIFACT_SCHEMA,
        "artifact_id": "provider-pricing-2026-08-v1",
        "review_status": "reviewed",
        "reviewed_at": "2026-08-13T18:00:00+09:00",
        "effective_from": effective_from,
        "effective_to": effective_to,
        "pricing_basis": pricing_basis,
        "raw_pricing_source_path": raw_path.name,
        "raw_pricing_source_bytes_sha256": (
            raw_hash_override or hashlib.sha256(raw_bytes).hexdigest()
        ),
        "raw_pricing_source_size_bytes": (
            len(raw_bytes) if raw_size_override is None else raw_size_override
        ),
        "prices": prices
        or [
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "10",
            }
        ],
        "decision_authority": PRICING_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    payload["artifact_content_sha256"] = pricing_artifact_content_sha256(payload)
    artifact_path = tmp_path / "provider-pricing.json"
    artifact_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return artifact_path


def _pricing(tmp_path: Path):
    return load_reviewed_pricing_artifact(
        _write_pricing_artifact(tmp_path), as_of_date=EXECUTION_DATE
    )


def _identity(attempt_number: int = 1, *, request_id: str = "request-1"):
    return AttemptIdentity(
        target_date="2026-08-14",
        parent_id="parent-1",
        request_id=request_id,
        arm="replay_candidate_exact_plus_micro",
        provider="openai",
        model="gpt-test",
        attempt_number=attempt_number,
    )


def _budget(
    tmp_path: Path,
    *,
    attempt_cap: int = 10,
    usd_cap: str = "1",
    worker_count: int = 1,
):
    return ProviderBudgetLedger(
        ledger_path=tmp_path / "provider-budget-2026-08-14.jsonl",
        pricing=_pricing(tmp_path),
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=attempt_cap,
        daily_usd_cap=usd_cap,
        worker_count=worker_count,
    )


def _reserve_from_process(artifact_path: str, ledger_path: str, request_id: str) -> int:
    pricing = load_reviewed_pricing_artifact(
        Path(artifact_path), as_of_date=EXECUTION_DATE
    )
    budget = ProviderBudgetLedger(
        ledger_path=Path(ledger_path),
        pricing=pricing,
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=12,
        daily_usd_cap="1",
        worker_count=1,
    )
    permit = budget.reserve_attempt(
        _identity(request_id=request_id),
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )
    return permit.sequence


def test_pricing_artifact_verifies_raw_bytes_window_and_model(tmp_path: Path) -> None:
    pricing = _pricing(tmp_path)

    model = pricing.price_for("OPENAI", "gpt-test")
    assert pricing.effective_from == date(2026, 8, 1)
    assert pricing.effective_to == date(2026, 8, 31)
    assert pricing.raw_source_size_bytes == len(
        (tmp_path / "provider-pricing-source.txt").read_bytes()
    )
    assert model.input_usd_per_million_tokens == Decimal("1")
    assert model.output_usd_per_million_tokens == Decimal("10")


@pytest.mark.parametrize(
    ("artifact_kwargs", "error"),
    [
        ({"raw_hash_override": "0" * 64}, "raw_source_sha256_mismatch"),
        ({"raw_size_override": 1}, "raw_source_size_mismatch"),
        (
            {"effective_from": "2026-08-15", "effective_to": "2026-08-31"},
            "not_yet_effective",
        ),
        (
            {"effective_from": "2026-07-01", "effective_to": "2026-08-13"},
            "stale",
        ),
    ],
)
def test_pricing_artifact_fails_closed_on_source_or_window_gap(
    tmp_path: Path, artifact_kwargs: dict, error: str
) -> None:
    artifact = _write_pricing_artifact(tmp_path, **artifact_kwargs)

    with pytest.raises(PricingArtifactError, match=error):
        load_reviewed_pricing_artifact(artifact, as_of_date=EXECUTION_DATE)


def test_pricing_artifact_missing_or_model_missing_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(PricingArtifactError, match="artifact_unreadable"):
        load_reviewed_pricing_artifact(
            tmp_path / "missing.json", as_of_date=EXECUTION_DATE
        )

    pricing = _pricing(tmp_path)
    with pytest.raises(PricingArtifactError, match="model_missing"):
        pricing.price_for("openai", "unknown-model")


def test_pricing_artifact_and_raw_source_symlinks_fail_closed(
    tmp_path: Path,
) -> None:
    artifact = _write_pricing_artifact(tmp_path / "artifact")
    artifact_link = tmp_path / "artifact-link.json"
    artifact_link.symlink_to(artifact)
    with pytest.raises(PricingArtifactError, match="artifact_unreadable"):
        load_reviewed_pricing_artifact(artifact_link, as_of_date=EXECUTION_DATE)

    raw_source = artifact.parent / "provider-pricing-source.txt"
    raw_target = artifact.parent / "provider-pricing-source-real.txt"
    raw_source.rename(raw_target)
    raw_source.symlink_to(raw_target.name)
    with pytest.raises(PricingArtifactError, match="raw_source_unreadable"):
        load_reviewed_pricing_artifact(artifact, as_of_date=EXECUTION_DATE)


def test_pricing_artifact_rejects_symlinked_parent_component(tmp_path: Path) -> None:
    real_directory = tmp_path / "real"
    artifact = _write_pricing_artifact(real_directory)
    alias = tmp_path / "alias"
    alias.symlink_to(real_directory, target_is_directory=True)

    with pytest.raises(PricingArtifactError, match="artifact_unreadable"):
        load_reviewed_pricing_artifact(
            alias / artifact.name,
            as_of_date=EXECUTION_DATE,
        )


def test_pricing_artifact_content_hash_and_rate_basis_fail_closed(
    tmp_path: Path,
) -> None:
    path = _write_pricing_artifact(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["prices"][0]["input_usd_per_million_tokens"] = "2"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PricingArtifactError, match="content_sha256_mismatch"):
        load_reviewed_pricing_artifact(path, as_of_date=EXECUTION_DATE)

    zero_rate = _write_pricing_artifact(
        tmp_path / "zero",
        prices=[
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "0",
                "output_usd_per_million_tokens": "10",
            }
        ],
    )
    with pytest.raises(PricingArtifactError, match="public_pricing_rate"):
        load_reviewed_pricing_artifact(zero_rate, as_of_date=EXECUTION_DATE)


def test_operator_reviewed_zero_cost_pricing_is_exact_and_budgeted(
    tmp_path: Path,
) -> None:
    zero_prices = [
        {
            "provider": "openai",
            "model": "gpt-test",
            "input_usd_per_million_tokens": "0",
            "output_usd_per_million_tokens": "0",
        }
    ]
    path = _write_pricing_artifact(
        tmp_path,
        prices=zero_prices,
        pricing_basis=OPERATOR_ZERO_COST_BASIS,
    )
    pricing = load_reviewed_pricing_artifact(path, as_of_date=EXECUTION_DATE)
    budget = ProviderBudgetLedger(
        ledger_path=tmp_path / "zero-budget.jsonl",
        pricing=pricing,
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=1,
        daily_usd_cap="1",
    )

    permit = budget.reserve_attempt(
        _identity(),
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )

    assert pricing.pricing_basis == OPERATOR_ZERO_COST_BASIS
    assert permit.reserved_cost_usd == Decimal("0")
    assert budget.summary(now=NOW)["pricing_basis"] == OPERATOR_ZERO_COST_BASIS


def test_daily_parent_cap_is_shared_across_historical_target_dates(
    tmp_path: Path,
) -> None:
    path = _write_pricing_artifact(
        tmp_path,
        prices=[
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "0",
                "output_usd_per_million_tokens": "0",
            }
        ],
        pricing_basis=OPERATOR_ZERO_COST_BASIS,
    )
    budget = ProviderBudgetLedger(
        ledger_path=tmp_path / "shared-parent-budget.jsonl",
        pricing=load_reviewed_pricing_artifact(path, as_of_date=EXECUTION_DATE),
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=390,
        daily_usd_cap="1",
    )
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    for index in range(130):
        budget.reserve_attempt(
            AttemptIdentity(
                target_date=("2026-08-13" if index % 2 else "2026-08-14"),
                parent_id=f"parent-{index:03d}",
                request_id=f"request-{index:03d}",
                arm="replay_candidate_exact_plus_micro",
                provider="openai",
                model="gpt-test",
                attempt_number=1,
            ),
            token_ceiling=ceiling,
            now=NOW,
        )

    # Another arm/retry for an already admitted parent remains legal.
    budget.reserve_attempt(
        AttemptIdentity(
            target_date="2026-08-14",
            parent_id="parent-000",
            request_id="request-000-control",
            arm="replay_control_exact_plus_micro",
            provider="openai",
            model="gpt-test",
            attempt_number=1,
        ),
        token_ceiling=ceiling,
        now=NOW,
    )
    with pytest.raises(BudgetExceededError, match="daily_parent_cap"):
        budget.reserve_attempt(
            AttemptIdentity(
                target_date="2026-08-13",
                parent_id="parent-130",
                request_id="request-130",
                arm="replay_candidate_exact_plus_micro",
                provider="openai",
                model="gpt-test",
                attempt_number=1,
            ),
            token_ceiling=ceiling,
            now=NOW,
        )


def test_read_only_reservation_census_is_exact_and_does_not_mutate_custody(
    tmp_path: Path,
) -> None:
    pricing_path = _write_pricing_artifact(
        tmp_path,
        prices=[
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "0",
                "output_usd_per_million_tokens": "0",
            }
        ],
        pricing_basis=OPERATOR_ZERO_COST_BASIS,
    )
    ledger_path = tmp_path / "read-only-census.jsonl"
    budget = ProviderBudgetLedger(
        ledger_path=ledger_path,
        pricing=load_reviewed_pricing_artifact(
            pricing_path,
            as_of_date=EXECUTION_DATE,
        ),
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=390,
        daily_usd_cap="1",
    )
    identity = AttemptIdentity(
        target_date="2026-08-14",
        parent_id="parent-read-only",
        request_id="request-read-only",
        arm="replay_candidate_exact_plus_micro",
        provider="openai",
        model="gpt-test",
        attempt_number=1,
    )
    permit = budget.reserve_attempt(
        identity,
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )
    custody_paths = (ledger_path, budget.manifest_path, budget.lock_path)
    before = {path: path.stat().st_mtime_ns for path in custody_paths}

    assert budget.validated_reservation_census_read_only() == (
        {
            "execution_date": EXECUTION_DATE.isoformat(),
            "reservation_id": permit.reservation_id,
            "attempt_identity": identity.as_dict(),
            "attempt_identity_sha256": identity.content_sha256,
            "settled": False,
        },
    )
    assert {path: path.stat().st_mtime_ns for path in custody_paths} == before


def test_read_only_reservation_census_rejects_deleted_ledger_behind_summary(
    tmp_path: Path,
) -> None:
    pricing_path = _write_pricing_artifact(
        tmp_path,
        prices=[
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "0",
                "output_usd_per_million_tokens": "0",
            }
        ],
        pricing_basis=OPERATOR_ZERO_COST_BASIS,
    )
    ledger_path = tmp_path / "read-only-summary-custody.jsonl"
    budget = ProviderBudgetLedger(
        ledger_path=ledger_path,
        pricing=load_reviewed_pricing_artifact(
            pricing_path,
            as_of_date=EXECUTION_DATE,
        ),
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=390,
        daily_usd_cap="1",
    )
    budget.reserve_attempt(
        AttemptIdentity(
            target_date="2026-08-14",
            parent_id="parent-summary-custody",
            request_id="request-summary-custody",
            arm="replay_candidate_exact_plus_micro",
            provider="openai",
            model="gpt-test",
            attempt_number=1,
        ),
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )
    budget.write_summary(ledger_path.with_suffix(".json"), now=NOW)
    ledger_path.unlink()
    budget.manifest_path.unlink()

    with pytest.raises(BudgetLedgerIntegrityError, match="summary_custody_mismatch"):
        budget.validated_reservation_census_read_only()


def test_operator_zero_cost_basis_rejects_any_nonzero_rate(tmp_path: Path) -> None:
    path = _write_pricing_artifact(
        tmp_path,
        pricing_basis=OPERATOR_ZERO_COST_BASIS,
    )
    with pytest.raises(PricingArtifactError, match="zero_cost_rate_must_be_zero"):
        load_reviewed_pricing_artifact(path, as_of_date=EXECUTION_DATE)


def test_budget_revalidates_pricing_and_raw_source_before_reservation(
    tmp_path: Path,
) -> None:
    artifact_path = _write_pricing_artifact(tmp_path)
    pricing = load_reviewed_pricing_artifact(artifact_path, as_of_date=EXECUTION_DATE)
    budget = ProviderBudgetLedger(
        ledger_path=tmp_path / "budget.jsonl",
        pricing=pricing,
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=1,
        daily_usd_cap="1",
    )
    pricing.raw_source_path.write_bytes(b"changed after pricing load")

    with pytest.raises(PricingArtifactError, match="raw_source"):
        budget.reserve_attempt(
            _identity(),
            token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
            now=NOW,
        )


def test_pricing_artifact_rejects_unknown_fields_that_could_hold_secrets(
    tmp_path: Path,
) -> None:
    path = _write_pricing_artifact(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["api_key"] = "must-not-be-accepted"
    payload["artifact_content_sha256"] = pricing_artifact_content_sha256(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PricingArtifactError, match="fields_invalid"):
        load_reviewed_pricing_artifact(path, as_of_date=EXECUTION_DATE)


def test_token_ceiling_uses_utf8_bytes_and_never_returns_content() -> None:
    ceiling = conservative_token_ceiling(
        "ASCII", "한글", b"\x00\xff", max_output_tokens=80
    )

    assert ceiling.input_utf8_bytes == len("ASCII한글".encode()) + 2
    assert ceiling.input_token_ceiling == ceiling.input_utf8_bytes
    assert ceiling.total_token_ceiling == ceiling.input_utf8_bytes + 80
    assert "ASCII" not in json.dumps(ceiling.as_dict())
    with pytest.raises(ValueError, match="must equal"):
        TokenCeiling(
            input_utf8_bytes=10,
            input_token_ceiling=9,
            max_output_tokens=1,
        )


def test_batch_pricing_coverage_binds_bedrock_physical_route(tmp_path: Path) -> None:
    artifact = _write_pricing_artifact(
        tmp_path,
        prices=[
            {
                "provider": "openai",
                "model": "gpt-test",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "10",
            },
            {
                "provider": "bedrock",
                "model": "nova_lite_v2",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "2",
            },
        ],
    )
    pricing = load_reviewed_pricing_artifact(artifact, as_of_date=EXECUTION_DATE)
    openai = ProviderModelSelection(provider="OPENAI", model="gpt-test")
    bedrock = ProviderModelSelection(
        provider="bedrock",
        model="nova_lite_v2",
        physical_model_id="us.amazon.nova-lite-v2:0",
        region_name="US-WEST-2",
    )

    census = validate_batch_pricing_coverage(
        pricing,
        [bedrock, openai, bedrock],
    )

    assert census == (bedrock, openai)
    assert census[0].physical_model_id == "us.amazon.nova-lite-v2:0"
    assert census[0].region_name == "us-west-2"


def test_batch_pricing_coverage_fails_on_gap_or_physical_route_conflict(
    tmp_path: Path,
) -> None:
    pricing = _pricing(tmp_path)
    missing = ProviderModelSelection(provider="openai", model="missing")
    with pytest.raises(PricingArtifactError, match="model_missing"):
        validate_batch_pricing_coverage(pricing, [missing])
    with pytest.raises(ValueError, match="physical_model_id"):
        ProviderModelSelection(provider="bedrock", model="nova_lite_v2")

    artifact = _write_pricing_artifact(
        tmp_path / "bedrock",
        prices=[
            {
                "provider": "bedrock",
                "model": "nova_lite_v2",
                "input_usd_per_million_tokens": "1",
                "output_usd_per_million_tokens": "2",
            }
        ],
    )
    bedrock_pricing = load_reviewed_pricing_artifact(
        artifact,
        as_of_date=EXECUTION_DATE,
    )
    first = ProviderModelSelection(
        provider="bedrock",
        model="nova_lite_v2",
        physical_model_id="us.amazon.nova-lite-v2:0",
        region_name="us-west-2",
    )
    second = ProviderModelSelection(
        provider="bedrock",
        model="nova_lite_v2",
        physical_model_id="eu.amazon.nova-lite-v2:0",
        region_name="eu-west-1",
    )
    with pytest.raises(PricingArtifactError, match="physical_route_conflict"):
        validate_batch_pricing_coverage(bedrock_pricing, [first, second])


def test_budget_requires_positive_caps_and_exactly_one_worker(tmp_path: Path) -> None:
    pricing = _pricing(tmp_path)
    common = {
        "ledger_path": tmp_path / "budget.jsonl",
        "pricing": pricing,
        "execution_date": EXECUTION_DATE,
        "daily_attempt_cap": 1,
        "daily_usd_cap": "1",
    }
    with pytest.raises(SingleWorkerRequiredError, match="single_worker"):
        ProviderBudgetLedger(**common, worker_count=2)
    with pytest.raises(SingleWorkerRequiredError, match="single_worker"):
        ProviderBudgetLedger(**common, worker_count=1.0)
    with pytest.raises(ValueError, match="daily_attempt_cap"):
        ProviderBudgetLedger(**{**common, "daily_attempt_cap": 0})
    with pytest.raises(ValueError, match="daily_attempt_cap"):
        ProviderBudgetLedger(**{**common, "daily_attempt_cap": 391})
    with pytest.raises(ValueError, match="daily_usd_cap"):
        ProviderBudgetLedger(**{**common, "daily_usd_cap": "0"})
    with pytest.raises(ValueError, match="daily_usd_cap"):
        ProviderBudgetLedger(**{**common, "daily_usd_cap": "1.0000001"})


def test_reservation_is_durable_before_call_and_summary_has_no_authority(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    secret_prompt = "prompt-secret-that-must-not-be-persisted"
    ceiling = conservative_token_ceiling(secret_prompt, max_output_tokens=100)

    permit = budget.reserve_attempt(_identity(), token_ceiling=ceiling, now=NOW)
    summary = budget.summary(now=NOW)

    assert permit.provider_call_budget_reserved is True
    assert permit.network_call_performed_by_module is False
    assert summary["reservation_count"] == 1
    assert summary["outstanding_reservation_count"] == 1
    assert summary["runtime_effect"] is False
    assert summary["allowed_runtime_apply"] is False
    assert summary["actual_order_submitted"] is False
    assert summary["broker_order_forbidden"] is True
    assert summary["network_call_performed_by_module"] is False
    assert budget.manifest_path.exists()
    assert secret_prompt not in budget.ledger_path.read_text(encoding="utf-8")

    persisted = budget.write_summary(tmp_path / "budget-summary.json", now=NOW)
    loaded = json.loads((tmp_path / "budget-summary.json").read_text())
    assert loaded == persisted
    assert loaded["summary_content_sha256"]
    assert loaded["runtime_effect"] is False


def test_duplicate_attempt_is_blocked_but_retry_number_is_a_new_attempt(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    budget.reserve_attempt(_identity(1), token_ceiling=ceiling, now=NOW)

    with pytest.raises(DuplicateAttemptError, match="already_reserved"):
        budget.reserve_attempt(_identity(1), token_ceiling=ceiling, now=NOW)

    budget.reserve_attempt(_identity(2), token_ceiling=ceiling, now=NOW)
    assert budget.summary(now=NOW)["reservation_count"] == 2


def test_reservation_rejects_future_target_or_wrong_kst_execution_day(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    future = AttemptIdentity(
        target_date="2026-08-15",
        parent_id="parent-1",
        request_id="request-1",
        arm="candidate",
        provider="openai",
        model="gpt-test",
        attempt_number=1,
    )
    with pytest.raises(ProviderBudgetError, match="target_date_in_future"):
        budget.reserve_attempt(future, token_ceiling=ceiling, now=NOW)
    with pytest.raises(ProviderBudgetError, match="execution_date_mismatch"):
        budget.reserve_attempt(
            _identity(),
            token_ceiling=ceiling,
            now=datetime(2026, 8, 15, 0, 1, tzinfo=KST),
        )


def test_timeout_or_crash_keeps_reservation_after_reopen(tmp_path: Path) -> None:
    budget = _budget(tmp_path)
    identity = _identity()
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    budget.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)

    reopened = _budget(tmp_path)
    summary = reopened.summary(now=NOW)
    assert summary["outstanding_reservation_count"] == 1
    assert Decimal(summary["outstanding_reserved_cost_usd"]) > 0
    with pytest.raises(DuplicateAttemptError, match="already_reserved"):
        reopened.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)


def test_attempt_and_usd_caps_fail_before_new_reservation(tmp_path: Path) -> None:
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    attempt_budget = _budget(tmp_path / "attempt", attempt_cap=1)
    attempt_budget.reserve_attempt(_identity(), token_ceiling=ceiling, now=NOW)
    with pytest.raises(BudgetExceededError, match="attempt_cap"):
        attempt_budget.reserve_attempt(
            _identity(request_id="request-2"), token_ceiling=ceiling, now=NOW
        )

    one_request_cost = Decimal(7) / Decimal(1_000_000) + Decimal(100) / Decimal(
        1_000_000
    )
    usd_budget = _budget(
        tmp_path / "usd", usd_cap=str(one_request_cost - Decimal("0.000001"))
    )
    with pytest.raises(BudgetExceededError, match="usd_cap"):
        usd_budget.reserve_attempt(_identity(), token_ceiling=ceiling, now=NOW)
    assert not usd_budget.ledger_path.exists()


def test_settlement_replaces_reserve_with_actual_usage_and_is_append_only(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    identity = _identity()
    ceiling = conservative_token_ceiling("request", max_output_tokens=100)
    permit = budget.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)

    receipt = budget.settle_attempt(
        identity,
        actual_input_tokens=3,
        actual_output_tokens=5,
        now=NOW,
        provider_response_sha256="a" * 64,
    )
    summary = budget.summary(now=NOW)

    assert receipt.reservation_id == permit.reservation_id
    assert receipt.actual_cost_usd == Decimal("0.000053")
    assert receipt.circuit_breaker_open is False
    assert summary["settlement_count"] == 1
    assert summary["outstanding_reservation_count"] == 0
    assert summary["actual_cost_usd"] == "0.000053"
    assert summary["ledger_record_count"] == 2
    with pytest.raises(SettlementError, match="already_settled"):
        budget.settle_attempt(
            identity,
            actual_input_tokens=3,
            actual_output_tokens=5,
            now=NOW,
        )


def test_settlement_cannot_precede_its_reservation(tmp_path: Path) -> None:
    budget = _budget(tmp_path)
    identity = _identity()
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    budget.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)

    with pytest.raises(SettlementError, match="precedes_reservation"):
        budget.settle_attempt(
            identity,
            actual_input_tokens=1,
            actual_output_tokens=1,
            now=datetime(2026, 8, 14, 21, 29, tzinfo=KST),
        )
    assert budget.summary(now=NOW)["outstanding_reservation_count"] == 1


def test_actual_cost_above_reserve_opens_persistent_circuit_breaker(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    identity = _identity()
    ceiling = conservative_token_ceiling("x", max_output_tokens=1)
    budget.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)

    receipt = budget.settle_attempt(
        identity,
        actual_input_tokens=1,
        actual_output_tokens=10,
        now=NOW,
    )

    assert receipt.exceeded_reservation is True
    assert budget.summary(now=NOW)["status"] == "circuit_breaker_open"
    with pytest.raises(CircuitBreakerOpenError, match="circuit_breaker"):
        budget.reserve_attempt(
            _identity(request_id="request-2"), token_ceiling=ceiling, now=NOW
        )
    assert _budget(tmp_path).summary(now=NOW)["circuit_breaker_open"] is True


def test_token_ceiling_breach_opens_breaker_even_when_dollars_remain_reserved(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    identity = _identity()
    ceiling = conservative_token_ceiling("x" * 1_000, max_output_tokens=1)
    permit = budget.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)

    receipt = budget.settle_attempt(
        identity,
        actual_input_tokens=0,
        actual_output_tokens=2,
        now=NOW,
    )

    assert receipt.actual_cost_usd < permit.reserved_cost_usd
    assert receipt.exceeded_reservation is True
    assert receipt.circuit_breaker_open is True


def test_valid_orphan_ledger_tail_repairs_stale_atomic_manifest(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    budget.reserve_attempt(_identity(), token_ceiling=ceiling, now=NOW)
    first_manifest = budget.manifest_path.read_bytes()
    budget.reserve_attempt(
        _identity(request_id="request-2"), token_ceiling=ceiling, now=NOW
    )

    budget.manifest_path.write_bytes(first_manifest)
    reopened = _budget(tmp_path)
    assert reopened.summary(now=NOW)["reservation_count"] == 2
    repaired = json.loads(reopened.manifest_path.read_text(encoding="utf-8"))
    assert repaired["record_count"] == 2


def test_verified_gzip_ledger_preserves_manifest_hash_and_is_read_only(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    identity = _identity()
    permit = budget.reserve_attempt(identity, token_ceiling=ceiling, now=NOW)
    expected = budget.summary(now=NOW)
    ledger_bytes = budget.ledger_path.read_bytes()
    manifest = json.loads(budget.manifest_path.read_text(encoding="utf-8"))
    archived_path = budget.ledger_path.with_suffix(f"{budget.ledger_path.suffix}.gz")
    with gzip.open(archived_path, "wb") as handle:
        handle.write(ledger_bytes)
    budget.ledger_path.unlink()

    reopened = _budget(tmp_path)
    observed = reopened.summary(now=NOW)

    assert observed["ledger_record_count"] == expected["ledger_record_count"]
    assert observed["ledger_bytes_sha256"] == hashlib.sha256(ledger_bytes).hexdigest()
    assert observed["ledger_bytes_sha256"] == manifest["ledger_bytes_sha256"]
    assert reopened.validated_reservation_census_read_only() == (
        {
            "execution_date": EXECUTION_DATE.isoformat(),
            "reservation_id": permit.reservation_id,
            "attempt_identity": identity.as_dict(),
            "attempt_identity_sha256": identity.content_sha256,
            "settled": False,
        },
    )
    with pytest.raises(ProviderBudgetError, match="archived_ledger_read_only"):
        reopened.reserve_attempt(
            _identity(request_id="request-2"),
            token_ceiling=ceiling,
            now=NOW,
        )
    assert not reopened.ledger_path.exists()
    with gzip.open(archived_path, "rb") as handle:
        assert handle.read() == ledger_bytes


def test_plain_and_gzip_provider_budget_ledger_conflict_fails_closed(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    budget.reserve_attempt(
        _identity(),
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )
    archived_path = budget.ledger_path.with_suffix(f"{budget.ledger_path.suffix}.gz")
    with gzip.open(archived_path, "wb") as handle:
        handle.write(budget.ledger_path.read_bytes())

    with pytest.raises(BudgetLedgerIntegrityError, match="plain_gzip_ledger_conflict"):
        budget.summary(now=NOW)
    with pytest.raises(BudgetLedgerIntegrityError, match="plain_gzip_ledger_conflict"):
        budget.reserve_attempt(
            _identity(request_id="request-2"),
            token_ceiling=conservative_token_ceiling("request-2", max_output_tokens=10),
            now=NOW,
        )


def test_corrupt_archived_provider_budget_ledger_fails_closed(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    budget.reserve_attempt(
        _identity(),
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )
    archived_path = budget.ledger_path.with_suffix(f"{budget.ledger_path.suffix}.gz")
    budget.ledger_path.unlink()
    archived_path.write_bytes(b"not-a-gzip-ledger")

    with pytest.raises(BudgetLedgerIntegrityError, match="ledger_unreadable"):
        budget.summary(now=NOW)


def test_ledger_and_lock_symlinks_fail_closed_without_touching_target(
    tmp_path: Path,
) -> None:
    ledger_budget = _budget(tmp_path / "ledger")
    ledger_target = tmp_path / "ledger-target.jsonl"
    ledger_target.write_bytes(b"")
    ledger_budget.ledger_path.symlink_to(ledger_target)

    with pytest.raises(BudgetLedgerIntegrityError, match="ledger_unreadable"):
        ledger_budget.summary(now=NOW)
    assert ledger_target.read_bytes() == b""

    lock_budget = _budget(tmp_path / "lock")
    lock_target = tmp_path / "lock-target"
    lock_target.write_bytes(b"do-not-lock-or-change")
    lock_budget.lock_path.symlink_to(lock_target)
    with pytest.raises(BudgetLedgerIntegrityError, match="lock_path_invalid"):
        lock_budget.summary(now=NOW)
    assert lock_target.read_bytes() == b"do-not-lock-or-change"


def test_manifest_symlink_fails_closed_without_overwriting_target(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    budget.reserve_attempt(
        _identity(),
        token_ceiling=conservative_token_ceiling("request", max_output_tokens=10),
        now=NOW,
    )
    manifest_target = tmp_path / "manifest-target.json"
    manifest_target.write_bytes(b"do-not-read-or-change")
    budget.manifest_path.unlink()
    budget.manifest_path.symlink_to(manifest_target)

    with pytest.raises(BudgetLedgerIntegrityError, match="manifest_unreadable"):
        budget.summary(now=NOW)
    assert manifest_target.read_bytes() == b"do-not-read-or-change"


def test_ledger_or_manifest_tamper_fails_closed(tmp_path: Path) -> None:
    budget = _budget(tmp_path)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    budget.reserve_attempt(_identity(), token_ceiling=ceiling, now=NOW)
    original_ledger = budget.ledger_path.read_bytes()

    row = json.loads(original_ledger)
    row["reservation_status"] = "tampered"
    budget.ledger_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(BudgetLedgerIntegrityError, match="record_hash_mismatch"):
        budget.summary(now=NOW)

    budget.ledger_path.write_bytes(original_ledger)
    manifest = json.loads(budget.manifest_path.read_text(encoding="utf-8"))
    manifest["record_count"] = 999
    budget.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(BudgetLedgerIntegrityError, match="manifest_hash_mismatch"):
        budget.summary(now=NOW)


def test_rehashed_row_with_wrong_parent_still_fails_chain_validation(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)
    budget.reserve_attempt(_identity(), token_ceiling=ceiling, now=NOW)
    budget.reserve_attempt(
        _identity(request_id="request-2"), token_ceiling=ceiling, now=NOW
    )
    rows = [
        json.loads(line)
        for line in budget.ledger_path.read_text(encoding="utf-8").splitlines()
    ]
    rows[1]["previous_record_sha256"] = "0" * 64
    content = {
        key: value for key, value in rows[1].items() if key != "record_content_sha256"
    }
    rows[1]["record_content_sha256"] = hashlib.sha256(
        json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    budget.ledger_path.write_text(
        "".join(
            json.dumps(
                row,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

    with pytest.raises(BudgetLedgerIntegrityError, match="record_chain_mismatch"):
        budget.summary(now=NOW)


def test_concurrent_reservations_are_serialized_into_one_valid_chain(
    tmp_path: Path,
) -> None:
    budget = _budget(tmp_path, attempt_cap=12)
    ceiling = conservative_token_ceiling("request", max_output_tokens=10)

    def reserve(index: int):
        return budget.reserve_attempt(
            _identity(request_id=f"request-{index}"),
            token_ceiling=ceiling,
            now=NOW,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        permits = list(executor.map(reserve, range(8)))

    summary = _budget(tmp_path, attempt_cap=12).summary(now=NOW)
    assert len({permit.sequence for permit in permits}) == 8
    assert summary["reservation_count"] == 8
    assert summary["ledger_record_count"] == 8
    manifest = json.loads(budget.manifest_path.read_text(encoding="utf-8"))
    assert manifest["record_count"] == 8


def test_cross_process_reservations_are_serialized_by_flock(tmp_path: Path) -> None:
    artifact_path = _write_pricing_artifact(tmp_path)
    ledger_path = tmp_path / "provider-budget-process.jsonl"
    request_ids = [f"process-request-{index}" for index in range(4)]

    with ProcessPoolExecutor(max_workers=4, mp_context=get_context("fork")) as executor:
        sequences = list(
            executor.map(
                _reserve_from_process,
                [str(artifact_path)] * 4,
                [str(ledger_path)] * 4,
                request_ids,
            )
        )

    pricing = load_reviewed_pricing_artifact(artifact_path, as_of_date=EXECUTION_DATE)
    budget = ProviderBudgetLedger(
        ledger_path=ledger_path,
        pricing=pricing,
        execution_date=EXECUTION_DATE,
        daily_attempt_cap=12,
        daily_usd_cap="1",
    )
    assert sorted(sequences) == [1, 2, 3, 4]
    assert budget.summary(now=NOW)["reservation_count"] == 4
