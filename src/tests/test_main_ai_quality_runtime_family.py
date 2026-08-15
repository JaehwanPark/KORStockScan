from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import main_ai_quality_runtime_family as mod
from src.engine.automation import main_ai_quality_standing_authorization as standing
from src.engine.automation import machine_microstructure_policy_approval as approval
from src.engine.scalping import main_ai_quality_live_policy as live
from src.engine.scalping.micro_reversion import ai_quality_cycle

KST = ZoneInfo("Asia/Seoul")


def _evidence_contract() -> dict:
    return {
        "clean_baseline_date": "2026-06-05",
        "required_trading_days": [5, 10, 20],
        "minimum_common_parents_20d": 20,
        "minimum_unique_symbols_20d": 10,
        "minimum_bbo_coverage_pct": 95.0,
        "minimum_depth_coverage_pct": 90.0,
        "minimum_relative_uplift_pct": 1.0,
        "requires_positive_notional_net_profit_20d": True,
        "requires_nonworse_p10_tail_and_deferred_rate": True,
        "requires_reconciled_actual_lifecycle": True,
    }


def _symbol_master() -> dict:
    body = {
        "schema": "scalp_micro_reversion_symbol_master_v1",
        "verification_status": "verified",
        "verified": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "records": [
            {
                "symbol": "005930",
                "listing_market": "KOSPI",
                "instrument_type": "EQUITY",
                "instrument_tax_class": "ordinary_taxable_equity_20bps",
                "effective_from": "2026-08-18",
                "effective_to": None,
                "metadata_source": "official_symbol_product_master_v2",
                "conflict_status": "clean",
            }
        ],
    }
    return {**body, "content_sha256": mod._economic_payload_sha256(body)}


def _write_symbol_master(tmp_path: Path) -> Path:
    path = tmp_path / "symbol_master.json"
    path.write_text(json.dumps(_symbol_master()), encoding="utf-8")
    return path


def _authorization() -> dict:
    return standing.build_standing_authorization(
        operator_authorization_id=(
            "operator-main-ai-quality-first-bounded-family-20260815"
        ),
        operator_instruction=mod.OPERATOR_INSTRUCTION,
        reviewed_at_kst="2026-08-15T09:30:00+09:00",
        expires_at_kst="2026-09-15T09:30:00+09:00",
        runtime_family=approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        stage="entry",
        axis="prompt_contract_effect",
        bounded_values={
            "current": live.CONTROL_PROMPT_SHA256,
            "recommended": live.RECOMMENDED_PROMPT_SHA256,
        },
        bounded_contract_sha256=(approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        evidence_contract=_evidence_contract(),
        expected_runtime_registry_entry_sha256=mod._registry_sha256(),
        expected_preopen_consumer=mod.PREOPEN_CONSUMER,
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
    )


def _r3_candidate() -> dict:
    content = {
        "candidate_family": standing.SOURCE_CANDIDATE_FAMILY,
        "decision_stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "tuning_axis": standing.TUNING_AXIS,
        "current_contract_sha256": "1" * 64,
        "recommended_contract_sha256": "2" * 64,
        "current_prompt_sha256": live.CONTROL_PROMPT_SHA256,
        "recommended_prompt_sha256": live.RECOMMENDED_PROMPT_SHA256,
        "selected_cost_profile_id": "krx_common_stock",
        "selected_cost_profile_content_sha256": "3" * 64,
        "economic_reference_bindings_sha256": "4" * 64,
        "economic_reference_binding_count": 20,
        "latest_symbol_master_source_date": "2026-08-17",
        "latest_symbol_master_artifact_sha256": mod._economic_payload_sha256(
            _symbol_master()
        ),
        "rolling_window_sha256": "5" * 64,
        "evidence_contract": _evidence_contract(),
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
        "candidate_id": "main-ai-quality-test",
        "candidate_sha256": mod._sha256(content),
        **content,
    }


def _manifest(candidate: dict | None = None) -> dict:
    candidates = [candidate or _r3_candidate()]
    body = {
        "schema": standing.R3_SCHEMA,
        "target_date": "2026-08-17",
        "status": "source_only_candidates_ready",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "first_runtime_candidate_auto_apply_performed": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "artifact_content_sha256": mod._sha256(body)}


def _window(days: int) -> dict:
    return {
        "window_trading_days": days,
        "observed_trading_days": days,
        "common_parent_count": 20,
        "unique_symbol_count": 10,
        "candidate_source_quality_adjusted_ev_pct": 0.12,
        "control_source_quality_adjusted_ev_pct": 0.10,
        "paired_ev_delta_pct": 0.02,
        "relative_uplift_pct": 20.0,
        "control_p10_ev_pct": -0.20,
        "candidate_p10_ev_pct": -0.15,
        "control_severe_tail_count": 1,
        "candidate_severe_tail_count": 1,
        "control_deferred_count": 3,
        "candidate_deferred_count": 2,
        "candidate_total_notional_net_profit_krw": 10000,
        "bbo_coverage_pct": 99.0,
        "depth_coverage_pct": 95.0,
        "invalid_transition_count": 0,
    }


def _rolling() -> dict:
    candidate = _r3_candidate()
    partition = {
        "decision_stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "control_contract_sha256": candidate["current_contract_sha256"],
        "candidate_contract_sha256": candidate["recommended_contract_sha256"],
        "current_prompt_sha256": candidate["current_prompt_sha256"],
        "recommended_prompt_sha256": candidate["recommended_prompt_sha256"],
        "latest_symbol_master_source_date": candidate[
            "latest_symbol_master_source_date"
        ],
        "latest_symbol_master_artifact_sha256": candidate[
            "latest_symbol_master_artifact_sha256"
        ],
        "windows": {str(days): _window(days) for days in (5, 10, 20)},
        "gate_findings": {str(days): [] for days in (5, 10, 20)},
        "r3_source_candidate_eligible": True,
    }
    body = {
        "schema": ai_quality_cycle.ROLLING_SCHEMA,
        "target_date": "2026-08-17",
        "global_candidate_blockers": [],
        "partitions": [partition],
    }
    return {**body, "artifact_content_sha256": mod._sha256(body)}


def _post_apply_rolling() -> dict:
    rolling = _rolling()
    rolling["target_date"] = "2026-08-18"
    partition = rolling["partitions"][0]
    partition["current_prompt_sha256"] = live.RECOMMENDED_PROMPT_SHA256
    partition["source_dates"] = ["2026-08-18"]
    partition["latest_symbol_master_source_date"] = "2026-08-18"
    window = partition["windows"]["5"]
    window["observed_trading_days"] = 1
    window["control_p10_ev_pct"] = -0.14
    window["control_severe_tail_count"] = 1
    window["control_deferred_count"] = 2
    rolling["artifact_content_sha256"] = mod._sha256(
        {
            key: value
            for key, value in rolling.items()
            if key != "artifact_content_sha256"
        }
    )
    return rolling


def _enrolled_queue(candidate: dict) -> dict:
    return {
        "candidates": [
            {
                "queue_key": "first-queue-key",
                "candidate_id": candidate["candidate_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "candidate": candidate,
                "state": approval.STATE_POST_APPLY_ATTRIBUTED,
                "family_apply_receipt": "/receipts/first_apply.json",
                "post_apply_attribution_receipt": "/receipts/post_apply.json",
            }
        ],
        "family_enrollments": {
            approval.MAIN_AI_QUALITY_RUNTIME_FAMILY: {
                "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
                "stage": "entry",
                "axis": "prompt_contract_effect",
                "bounded_contract_sha256": (
                    approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256
                ),
                "runtime_registry_entry_sha256": mod._registry_sha256(),
                "first_approved_queue_key": "first-queue-key",
                "first_apply_receipt": "/receipts/first_apply.json",
                "post_apply_attribution_receipt": "/receipts/post_apply.json",
                "enrolled_after_guarded_apply": True,
                "enrolled_after_post_apply_attribution": True,
            }
        },
    }


def _applied_queue(tmp_path: Path) -> tuple[dict, Path, Path]:
    authorization = _authorization()
    candidate = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )
    handoff = {
        "schema": approval.HANDOFF_SCHEMA,
        "target_date": "2026-08-18",
        "created_at_kst": "2026-08-18T07:30:00+09:00",
        "queue_key": "queue-key",
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "operator_authorization_id": authorization["operator_authorization_id"],
        "authorization_mode": "first_explicit_operator_approval",
        "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "effective_venue": live.TARGET_VENUE,
        "session_bucket": live.TARGET_SESSION,
        "bounded_values": candidate["runtime_design"]["bounded_values"],
        "bounded_contract_sha256": (approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        "runtime_registry_entry_sha256": mod._registry_sha256(),
        "preopen_consumer": mod.PREOPEN_CONSUMER,
        "status": "preopen_authorization_handoff_ready",
        "runtime_effect": False,
        "runtime_apply_performed": False,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    activation_path = tmp_path / "activation.json"
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    apply_path = receipt_dir / "apply.json"
    activation = mod.build_preopen_activation(
        handoff_path=handoff_path,
        handoff=handoff,
        candidate=candidate,
        authorization=authorization,
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
        activation_artifact_path=activation_path,
        apply_receipt_path=apply_path,
        symbol_master_path=_write_symbol_master(tmp_path),
    )
    activation_path.write_text(json.dumps(activation), encoding="utf-8")
    apply_path.write_text(json.dumps(mod.apply_receipt(activation)), encoding="utf-8")
    queue = {
        "candidates": [
            {
                "queue_key": "queue-key",
                "candidate_id": candidate["candidate_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "candidate": candidate,
                "state": approval.STATE_PREOPEN_SCHEDULED,
                "preopen_target_date": "2026-08-18",
                "preopen_handoff": str(handoff_path),
            }
        ],
        "family_enrollments": {},
    }
    applied, rejected = approval.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 0, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    assert rejected == []
    assert applied["candidates"][0]["state"] == approval.STATE_APPLIED
    return applied, receipt_dir, activation_path


def test_exact_standing_candidate_materializes_registered_promotion() -> None:
    candidate = mod.build_promotion_candidate(
        authorization=_authorization(),
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )

    assert candidate["first_operator_approval_required"] is True
    assert approval.evidence_readiness_errors(candidate) == []
    assert approval.runtime_design_errors(candidate) == []
    assert candidate["runtime_effect"] is False
    assert candidate["actual_order_submitted"] is False


def test_postclose_dry_run_never_writes_operator_decision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    authorization_path = tmp_path / "standing.json"
    manifest_path = tmp_path / "r3.json"
    rolling_path = tmp_path / "rolling.json"
    authorization_path.write_text(json.dumps(_authorization()), encoding="utf-8")
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    rolling_path.write_text(json.dumps(_rolling()), encoding="utf-8")
    monkeypatch.setattr(mod, "STANDING_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(ai_quality_cycle, "r3_manifest_path", lambda _: manifest_path)
    monkeypatch.setattr(ai_quality_cycle, "rolling_report_path", lambda _: rolling_path)
    monkeypatch.setattr(
        approval,
        "record_operator_decision",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("dry-run must not write an operator decision")
        ),
    )

    result = mod._postclose(
        target_date="2026-08-17",
        write=False,
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
        queue_path=tmp_path / "queue.json",
    )

    assert result["status"] == "first_exact_candidate_ready_for_auto_approval_dry_run"
    assert result["runtime_effect"] is False
    assert result["actual_order_submitted"] is False


def test_postclose_write_auto_approves_only_the_exact_first_candidate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    authorization_path = tmp_path / "standing.json"
    manifest_path = tmp_path / "r3.json"
    rolling_path = tmp_path / "rolling.json"
    source_path = tmp_path / "runtime_source.json"
    queue_path = tmp_path / "queue.json"
    approval_dir = tmp_path / "approvals"
    receipt_dir = tmp_path / "receipts"
    authorization_path.write_text(json.dumps(_authorization()), encoding="utf-8")
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    rolling_path.write_text(json.dumps(_rolling()), encoding="utf-8")
    monkeypatch.setattr(mod, "STANDING_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(ai_quality_cycle, "r3_manifest_path", lambda _: manifest_path)
    monkeypatch.setattr(ai_quality_cycle, "rolling_report_path", lambda _: rolling_path)
    monkeypatch.setattr(mod, "source_report_path", lambda _: source_path)

    result = mod._postclose(
        target_date="2026-08-17",
        write=True,
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
        queue_path=queue_path,
        approval_dir=approval_dir,
        apply_receipt_dir=receipt_dir,
    )

    assert result["status"] == "first_exact_candidate_approved_for_next_preopen"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert len(queue["candidates"]) == 1
    assert queue["candidates"][0]["state"] == approval.STATE_USER_APPROVED
    assert queue["authority"]["actual_order_submitted"] is False
    decisions = list(approval_dir.glob("*.json"))
    assert len(decisions) == 1
    decision = json.loads(decisions[0].read_text(encoding="utf-8"))
    assert decision["candidate_sha256"] == result["candidate_sha256"]
    assert decision["allowed_runtime_apply"] is True
    assert decision["actual_order_submitted"] is False
    source = json.loads(source_path.read_text(encoding="utf-8"))
    assert source["candidate_count"] == 1
    assert source["runtime_effect"] is False


def test_postclose_passing_attribution_queues_next_day_exact_carry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    applied, receipt_dir, _ = _applied_queue(tmp_path)
    authorization_path = tmp_path / "standing.json"
    manifest_path = tmp_path / "r3.json"
    rolling_path = tmp_path / "rolling.json"
    source_path = tmp_path / "runtime_source.json"
    queue_path = tmp_path / "queue.json"
    authorization_path.write_text(json.dumps(_authorization()), encoding="utf-8")
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    rolling_path.write_text(json.dumps(_post_apply_rolling()), encoding="utf-8")
    queue_path.write_text(json.dumps(applied), encoding="utf-8")
    monkeypatch.setattr(mod, "STANDING_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(ai_quality_cycle, "r3_manifest_path", lambda _: manifest_path)
    monkeypatch.setattr(ai_quality_cycle, "rolling_report_path", lambda _: rolling_path)
    monkeypatch.setattr(mod, "source_report_path", lambda _: source_path)

    result = mod._postclose(
        target_date="2026-08-18",
        write=True,
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        queue_path=queue_path,
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=receipt_dir,
    )

    assert result["status"] == "post_apply_continuation_queued"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    prior = [
        row
        for row in queue["candidates"]
        if row["state"] == approval.STATE_POST_APPLY_ATTRIBUTED
    ]
    continuation = [
        row
        for row in queue["candidates"]
        if row["state"] == approval.STATE_AUTO_CHAIN_ELIGIBLE
    ]
    assert len(prior) == 1
    assert len(continuation) == 1
    assert continuation[0]["candidate"]["first_operator_approval_required"] is False
    assert continuation[0]["candidate"]["runtime_effect"] is False
    assert continuation[0]["candidate"]["actual_order_submitted"] is False
    source = json.loads(source_path.read_text(encoding="utf-8"))
    assert source["post_apply_continuation"] is True
    assert source["broker_order_forbidden"] is True

    rerun = mod._postclose(
        target_date="2026-08-18",
        write=True,
        now=datetime(2026, 8, 18, 20, 35, tzinfo=KST),
        queue_path=queue_path,
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=receipt_dir,
    )
    assert rerun["status"] == "post_apply_continuation_queued"
    rerun_queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert len(rerun_queue["candidates"]) == 2


def test_unreviewed_prompt_hash_fails_closed() -> None:
    candidate = _r3_candidate()
    candidate["recommended_prompt_sha256"] = "9" * 64
    content = {
        key: value
        for key, value in candidate.items()
        if key not in {"candidate_id", "candidate_sha256"}
    }
    candidate["candidate_sha256"] = mod._sha256(content)

    with pytest.raises(ValueError, match="standing_intent_exact_candidate_not_bound"):
        mod.build_promotion_candidate(
            authorization=_authorization(),
            r3_manifest=_manifest(candidate),
            rolling=_rolling(),
            approval_queue={"candidates": [], "family_enrollments": {}},
            now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
        )


def test_expired_standing_intent_allows_only_post_attributed_continuation() -> None:
    authorization = _authorization()
    first = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )
    after_expiry = datetime(2026, 9, 16, 7, 30, tzinfo=KST)

    with pytest.raises(ValueError, match="standing_authorization_expired"):
        mod.build_promotion_candidate(
            authorization=authorization,
            r3_manifest=_manifest(),
            rolling=_rolling(),
            approval_queue={
                "candidates": [
                    {
                        "candidate": first,
                        "state": approval.STATE_POST_APPLY_ATTRIBUTED,
                    }
                ],
                "family_enrollments": {},
            },
            now=after_expiry,
        )

    mismatched_enrollment = _enrolled_queue(first)
    mismatched_enrollment["candidates"][0][
        "family_apply_receipt"
    ] = "/receipts/different.json"
    with pytest.raises(ValueError, match="standing_authorization_expired"):
        mod.build_promotion_candidate(
            authorization=authorization,
            r3_manifest=_manifest(),
            rolling=_rolling(),
            approval_queue=mismatched_enrollment,
            now=after_expiry,
        )

    continuation = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue=_enrolled_queue(first),
        now=after_expiry,
    )
    assert continuation["first_operator_approval_required"] is False


def test_enrolled_auto_chain_preopen_does_not_reuse_first_intent_expiry(
    tmp_path: Path,
) -> None:
    authorization = _authorization()
    first = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )
    candidate = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue=_enrolled_queue(first),
        now=datetime(2026, 9, 16, 7, 30, tzinfo=KST),
    )
    handoff = {
        "schema": approval.HANDOFF_SCHEMA,
        "target_date": "2026-09-16",
        "queue_key": "continuation-queue-key",
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "authorization_mode": "enrolled_same_bounded_family_auto_chain",
        "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "effective_venue": live.TARGET_VENUE,
        "session_bucket": live.TARGET_SESSION,
        "bounded_values": candidate["runtime_design"]["bounded_values"],
        "bounded_contract_sha256": (approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        "runtime_registry_entry_sha256": mod._registry_sha256(),
        "preopen_consumer": mod.PREOPEN_CONSUMER,
        "status": "preopen_authorization_handoff_ready",
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")

    activation = mod.build_preopen_activation(
        handoff_path=handoff_path,
        handoff=handoff,
        candidate=candidate,
        authorization=authorization,
        now=datetime(2026, 9, 16, 7, 40, tzinfo=KST),
        activation_artifact_path=tmp_path / "activation.json",
        apply_receipt_path=tmp_path / "apply.json",
        symbol_master_path=_write_symbol_master(tmp_path),
    )
    assert activation["runtime_effect"] is True
    assert activation["actual_order_submitted"] is False


def test_preopen_activation_and_live_selector_require_exact_binding(
    tmp_path: Path,
) -> None:
    candidate = mod.build_promotion_candidate(
        authorization=_authorization(),
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )
    handoff = {
        "schema": approval.HANDOFF_SCHEMA,
        "target_date": "2026-08-18",
        "queue_key": "queue-key",
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "operator_authorization_id": _authorization()["operator_authorization_id"],
        "authorization_mode": "first_explicit_operator_approval",
        "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "effective_venue": live.TARGET_VENUE,
        "session_bucket": live.TARGET_SESSION,
        "bounded_values": candidate["runtime_design"]["bounded_values"],
        "bounded_contract_sha256": (approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        "runtime_registry_entry_sha256": mod._registry_sha256(),
        "preopen_consumer": mod.PREOPEN_CONSUMER,
        "status": "preopen_authorization_handoff_ready",
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    activation_path = tmp_path / "activation.json"
    receipt_path = tmp_path / "apply.json"
    symbol_master_path = _write_symbol_master(tmp_path)
    activation = mod.build_preopen_activation(
        handoff_path=handoff_path,
        handoff=handoff,
        candidate=candidate,
        authorization=_authorization(),
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
        activation_artifact_path=activation_path,
        apply_receipt_path=receipt_path,
        symbol_master_path=symbol_master_path,
    )
    activation_path.write_text(json.dumps(activation), encoding="utf-8")
    receipt_path.write_text(json.dumps(mod.apply_receipt(activation)), encoding="utf-8")

    selected = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert selected["enabled"] is True
    assert selected["selected_prompt_version"] == live.RECOMMENDED_PROMPT_VERSION
    assert selected["actual_order_submitted"] is False

    outside_master = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="069500",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert outside_master["enabled"] is False
    assert outside_master["status"] == ("fallback_outside_verified_common_stock_master")

    master_snapshot = symbol_master_path.read_text(encoding="utf-8")
    tampered_master = _symbol_master()
    tampered_master["records"][0]["instrument_type"] = "ETF"
    symbol_master_path.write_text(json.dumps(tampered_master), encoding="utf-8")
    invalid_master = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert invalid_master["enabled"] is False
    assert (
        "activation_symbol_master_invalid_or_empty"
        in invalid_master["blocking_reasons"]
    )
    symbol_master_path.write_text(master_snapshot, encoding="utf-8")

    receipt_snapshot = receipt_path.read_text(encoding="utf-8")
    receipt_path.unlink()
    no_receipt = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert no_receipt["enabled"] is False
    assert "apply_receipt_hash_mismatch" in no_receipt["blocking_reasons"]
    receipt_path.write_text(receipt_snapshot, encoding="utf-8")

    activation["candidate_sha256"] = "0" * 64
    activation_path.write_text(json.dumps(activation), encoding="utf-8")
    rejected = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert rejected["enabled"] is False
    assert rejected["runtime_effect"] is False


def test_cli_preopen_cannot_synthesize_a_different_runtime_date() -> None:
    with pytest.raises(
        ValueError, match="preopen_runtime_target_date_not_current_kst_date"
    ):
        mod._cli_now_for_phase(
            phase="preopen",
            target_day=datetime(2026, 8, 18, tzinfo=KST).date(),
            current=datetime(2026, 8, 17, 7, 40, tzinfo=KST),
        )

    historical = mod._cli_now_for_phase(
        phase="postclose",
        target_day=datetime(2026, 8, 17, tzinfo=KST).date(),
        current=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
    )
    assert historical.date().isoformat() == "2026-08-18"


def test_postclose_runtime_control_write_rejects_historical_target(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match="postclose_runtime_family_write_target_date_not_current"
    ):
        mod._postclose(
            target_date="2026-08-17",
            write=True,
            now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
            queue_path=tmp_path / "queue.json",
        )


def test_cli_write_persists_fail_closed_diagnostic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "blocked.json"
    monkeypatch.setattr(mod, "report_path", lambda *_: output)
    monkeypatch.setattr(
        mod,
        "_postclose",
        lambda **_: (_ for _ in ()).throw(ValueError("candidate_not_ready")),
    )

    return_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-17",
            "--queue-path",
            str(tmp_path / "queue.json"),
            "--write",
        ]
    )

    assert return_code == 2
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "blocked_fail_closed"
    assert report["reason"] == "candidate_not_ready"
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False


def test_family_enrolls_only_after_exact_post_apply_attribution(
    tmp_path: Path,
) -> None:
    authorization = _authorization()
    candidate = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )
    handoff = {
        "schema": approval.HANDOFF_SCHEMA,
        "target_date": "2026-08-18",
        "created_at_kst": "2026-08-18T07:30:00+09:00",
        "queue_key": "queue-key",
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "operator_authorization_id": authorization["operator_authorization_id"],
        "authorization_mode": "first_explicit_operator_approval",
        "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "effective_venue": live.TARGET_VENUE,
        "session_bucket": live.TARGET_SESSION,
        "bounded_values": candidate["runtime_design"]["bounded_values"],
        "bounded_contract_sha256": (approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        "runtime_registry_entry_sha256": mod._registry_sha256(),
        "preopen_consumer": mod.PREOPEN_CONSUMER,
        "status": "preopen_authorization_handoff_ready",
        "runtime_effect": False,
        "runtime_apply_performed": False,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    handoff_path = tmp_path / "handoff.json"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    activation_path = tmp_path / "activation.json"
    apply_path = tmp_path / "apply.json"
    activation = mod.build_preopen_activation(
        handoff_path=handoff_path,
        handoff=handoff,
        candidate=candidate,
        authorization=authorization,
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
        activation_artifact_path=activation_path,
        apply_receipt_path=apply_path,
        symbol_master_path=_write_symbol_master(tmp_path),
    )
    apply_path.write_text(json.dumps(mod.apply_receipt(activation)), encoding="utf-8")
    activation_path.write_text(json.dumps(activation), encoding="utf-8")
    queue = {
        "candidates": [
            {
                "queue_key": "queue-key",
                "candidate_id": candidate["candidate_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "candidate": candidate,
                "state": approval.STATE_PREOPEN_SCHEDULED,
                "preopen_target_date": "2026-08-18",
                "preopen_handoff": str(handoff_path),
            }
        ],
        "family_enrollments": {},
    }
    applied, rejected = approval.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 0, tzinfo=KST),
        apply_receipt_dir=tmp_path,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    assert rejected == []
    assert applied["candidates"][0]["state"] == approval.STATE_APPLIED
    assert applied["family_enrollments"] == {}

    attribution = mod.build_post_apply_attribution_receipt(
        entry=applied["candidates"][0],
        rolling=_post_apply_rolling(),
        target_date="2026-08-18",
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
    )
    attribution_path = tmp_path / "post_apply.json"
    tampered = dict(attribution)
    tampered["continuation_checks"] = {
        **attribution["continuation_checks"],
        "source_quality_adjusted_ev_positive": False,
    }
    attribution_path.write_text(json.dumps(tampered), encoding="utf-8")
    still_applied, rejected = approval.sync_queue(
        applied,
        source_candidates=[],
        source_path=None,
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 35, tzinfo=KST),
        apply_receipt_dir=tmp_path,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    assert rejected == []
    assert still_applied["candidates"][0]["state"] == approval.STATE_APPLIED
    assert still_applied["family_enrollments"] == {}

    attribution_path.write_text(json.dumps(attribution), encoding="utf-8")
    attributed, rejected = approval.sync_queue(
        still_applied,
        source_candidates=[],
        source_path=None,
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 40, tzinfo=KST),
        apply_receipt_dir=tmp_path,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    assert rejected == []
    assert attributed["candidates"][0]["state"] == approval.STATE_POST_APPLY_ATTRIBUTED
    enrollment = attributed["family_enrollments"][
        approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
    ]
    assert enrollment["enrolled_after_post_apply_attribution"] is True

    continuation = mod.build_post_apply_continuation_candidate(
        entry=applied["candidates"][0],
        attribution=attribution,
        attribution_path=attribution_path,
        rolling=_post_apply_rolling(),
        target_date="2026-08-18",
    )
    assert continuation["first_operator_approval_required"] is False
    assert (
        continuation["source_bindings"]["prior_applied_candidate_sha256"]
        == applied["candidates"][0]["candidate_sha256"]
    )
    next_queue, rejected = approval.sync_queue(
        attributed,
        source_candidates=[continuation],
        source_path=tmp_path / "rolling.json",
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 45, tzinfo=KST),
        apply_receipt_dir=tmp_path,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    assert rejected == []
    continuation_entries = [
        row
        for row in next_queue["candidates"]
        if row["candidate_sha256"] == continuation["candidate_sha256"]
    ]
    assert len(continuation_entries) == 1
    assert continuation_entries[0]["state"] == approval.STATE_AUTO_CHAIN_ELIGIBLE
