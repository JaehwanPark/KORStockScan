from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import main_ai_quality_standing_authorization as mod

KST = ZoneInfo("Asia/Seoul")


def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _evidence() -> dict:
    return {
        "clean_baseline_date": "2026-06-05",
        "required_trading_days": [5, 10, 20],
        "minimum_common_parents_20d": 20,
        "minimum_unique_symbols_20d": 10,
    }


def _registry_entry() -> dict:
    return {
        "enabled": True,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "bounded_contract_sha256": "b" * 64,
        "preopen_consumer": "reviewed_prompt_policy_preopen_consumer",
        "apply_receipt_owner": "reviewed_prompt_policy_apply_receipt",
        "post_apply_attribution_owner": "reviewed_prompt_policy_attribution",
    }


def _authorization(*, registry_sha: str | None = None) -> dict:
    entry = _registry_entry()
    return mod.build_standing_authorization(
        operator_authorization_id="operator-first-ai-quality-20260814",
        operator_instruction=(
            "Authorize only the first exact reviewed prompt candidate; retain all "
            "runtime and order safety gates."
        ),
        reviewed_at_kst="2026-08-14T21:00:00+09:00",
        expires_at_kst="2026-09-14T21:00:00+09:00",
        runtime_family="main_ai_quality_prompt_contract_v1",
        stage="entry",
        axis="prompt_contract_effect",
        bounded_values={"current": "c" * 64, "recommended": "d" * 64},
        bounded_contract_sha256="b" * 64,
        evidence_contract=_evidence(),
        expected_runtime_registry_entry_sha256=registry_sha or _sha(entry),
        expected_preopen_consumer="reviewed_prompt_policy_preopen_consumer",
        effective_venue="KRX",
        session_bucket="morning",
    )


def _candidate(*, candidate_id: str = "main-ai-quality-one") -> dict:
    body = {
        "candidate_family": mod.SOURCE_CANDIDATE_FAMILY,
        "decision_stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "morning",
        "tuning_axis": mod.TUNING_AXIS,
        "current_contract_sha256": "c" * 64,
        "recommended_contract_sha256": "d" * 64,
        "current_prompt_sha256": "c" * 64,
        "recommended_prompt_sha256": "d" * 64,
        "reviewed_cost_profile_sha256": "e" * 64,
        "symbol_master_artifact_sha256": "f" * 64,
        "latest_symbol_master_source_date": "2026-08-31",
        "latest_symbol_master_artifact_sha256": "f" * 64,
        "rolling_window_sha256": "a" * 64,
        "evidence_contract": _evidence(),
        "runtime_design_status": "design_required_no_registered_consumer",
        "first_exact_candidate_approval_required": True,
        "continuous_auto_chain_eligible": False,
        "provider_or_order_authority": False,
        "decision_authority": "postclose_source_only_ai_quality_research",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {
        "candidate_id": candidate_id,
        "candidate_sha256": _sha(body),
        **body,
    }


def _manifest(candidates: list[dict]) -> dict:
    body = {
        "schema": mod.R3_SCHEMA,
        "target_date": "2026-08-31",
        "status": "source_only_candidates_ready",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "first_runtime_candidate_auto_apply_performed": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "artifact_content_sha256": _sha(body)}


def test_unique_exact_candidate_is_bound_but_never_approved_or_scheduled() -> None:
    result = mod.resolve_standing_authorization(
        _authorization(),
        _manifest([_candidate()]),
        approval_queue={"candidates": []},
        runtime_registry={"main_ai_quality_prompt_contract_v1": _registry_entry()},
        now=datetime(2026, 8, 31, 20, 0, tzinfo=KST),
    )

    assert result["status"] == "candidate_bound_awaiting_runtime_design"
    assert result["candidate_binding"]["candidate_id"] == "main-ai-quality-one"
    assert result["exact_candidate_bound_operator_decision_created"] is False
    assert result["preopen_handoff_created"] is False
    assert "promotion_candidate_contract_not_materialized" in result["blocker_codes"]
    assert result["allowed_runtime_apply"] is False


@pytest.mark.parametrize(
    ("registry", "expected"),
    [
        ({}, "runtime_family_not_in_trusted_registry"),
        (
            {"main_ai_quality_prompt_contract_v1": _registry_entry()},
            "runtime_registry_entry_sha256_drift",
        ),
    ],
)
def test_missing_or_drifted_registry_fails_closed(
    registry: dict, expected: str
) -> None:
    authorization = _authorization(
        registry_sha=("0" * 64 if registry else _sha(_registry_entry()))
    )
    result = mod.resolve_standing_authorization(
        authorization,
        _manifest([_candidate()]),
        approval_queue={"candidates": []},
        runtime_registry=registry,
        now=datetime(2026, 8, 31, 20, 0, tzinfo=KST),
    )
    assert expected in result["blocker_codes"]
    assert result["candidate_binding"] is None
    assert result["preopen_handoff_created"] is False


def test_multiple_exact_candidates_and_unknown_prompt_fail_closed() -> None:
    duplicate_shape = _candidate(candidate_id="main-ai-quality-two")
    tied = mod.resolve_standing_authorization(
        _authorization(),
        _manifest([_candidate(), duplicate_shape]),
        approval_queue={"candidates": []},
        runtime_registry={"main_ai_quality_prompt_contract_v1": _registry_entry()},
        now=datetime(2026, 8, 31, 20, 0, tzinfo=KST),
    )
    assert "r3_exact_candidate_multiple" in tied["blocker_codes"]
    assert tied["candidate_binding"] is None

    unknown = _candidate()
    unknown["recommended_prompt_sha256"] = "9" * 64
    unknown["candidate_sha256"] = _sha(
        {
            key: value
            for key, value in unknown.items()
            if key not in {"candidate_id", "candidate_sha256"}
        }
    )
    rejected = mod.resolve_standing_authorization(
        _authorization(),
        _manifest([unknown]),
        approval_queue={"candidates": []},
        runtime_registry={"main_ai_quality_prompt_contract_v1": _registry_entry()},
        now=datetime(2026, 8, 31, 20, 0, tzinfo=KST),
    )
    assert "unreviewed_prompt_contract" in rejected["blocker_codes"]
    assert "r3_exact_candidate_missing" in rejected["blocker_codes"]
    assert rejected["candidate_binding"] is None


def test_missing_exact_candidate_is_distinct_from_duplicate_candidate() -> None:
    result = mod.resolve_standing_authorization(
        _authorization(),
        _manifest([]),
        approval_queue={"candidates": []},
        runtime_registry={"main_ai_quality_prompt_contract_v1": _registry_entry()},
        now=datetime(2026, 8, 31, 20, 0, tzinfo=KST),
    )

    assert "r3_exact_candidate_missing" in result["blocker_codes"]
    assert "r3_exact_candidate_multiple" not in result["blocker_codes"]
    assert result["candidate_binding"] is None


def test_prior_candidate_requires_post_apply_attribution() -> None:
    prior_candidate = {
        "runtime_design": {"runtime_family": "main_ai_quality_prompt_contract_v1"}
    }
    result = mod.resolve_standing_authorization(
        _authorization(),
        _manifest([_candidate()]),
        approval_queue={
            "candidates": [{"candidate": prior_candidate, "state": "APPLIED"}]
        },
        runtime_registry={"main_ai_quality_prompt_contract_v1": _registry_entry()},
        now=datetime(2026, 8, 31, 20, 0, tzinfo=KST),
    )
    assert "prior_family_candidate_not_post_apply_attributed" in result["blocker_codes"]
    assert result["preopen_handoff_created"] is False


def test_tampered_authorization_and_expired_intent_fail_closed() -> None:
    authorization = _authorization()
    authorization["bounded_values"]["recommended"] = "8" * 64
    result = mod.resolve_standing_authorization(
        authorization,
        _manifest([_candidate()]),
        approval_queue={"candidates": []},
        runtime_registry={"main_ai_quality_prompt_contract_v1": _registry_entry()},
        now=datetime(2026, 10, 1, 20, 0, tzinfo=KST),
    )
    assert "standing_authorization_hash_mismatch" in result["blocker_codes"]
    assert "standing_authorization_expired" in result["blocker_codes"]
    assert result["candidate_binding"] is None


def test_artifact_writer_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "standing.json"
    mod.write_artifact(path, _authorization())

    with pytest.raises(FileExistsError):
        mod.write_artifact(path, _authorization())

    assert json.loads(path.read_text(encoding="utf-8"))["one_shot"] is True
