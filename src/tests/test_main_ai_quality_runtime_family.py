from __future__ import annotations

import gzip
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
    return ai_quality_cycle._r3_evidence_contract(
        ai_quality_cycle.LEGACY_DESIGN_VERSION
    )


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
    return ai_quality_cycle.project_r3_candidates_from_validated_r2(_rolling())[0]


def _manifest(candidate: dict | None = None) -> dict:
    rolling = _rolling()
    candidates = [candidate or _r3_candidate()]
    body = {
        "schema": standing.R3_SCHEMA,
        "target_date": "2026-08-17",
        "status": "source_only_candidates_ready",
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "source_provider_ablation_floor_bindings_sha256": rolling[
            "provider_ablation_floor_bindings_sha256"
        ],
        "source_current_run_global_blockers_sha256": rolling[
            "current_run_global_blockers_sha256"
        ],
        "candidate_count": len(candidates),
        "candidates": candidates,
        "global_candidate_blockers": [],
        "blocked_pre_clear_candidate_count": 0,
        "first_runtime_candidate_auto_apply_performed": False,
        **ai_quality_cycle.OFFLINE_AUTHORITY,
    }
    return {**body, "artifact_content_sha256": mod._sha256(body)}


def _window(days: int) -> dict:
    return {
        "window_trading_days": days,
        "observed_trading_days": days,
        "selected_dates": ["2026-08-17"] * days,
        "common_parent_count": 20,
        "decision_level_parent_count": 20,
        "unique_lifecycle_count": 20,
        "unique_lifecycle_census_sha256": "6" * 64,
        "promotion_economics_input_census_sha256": "7" * 64,
        "unique_lifecycle_stage_cluster_count": 20,
        "lifecycle_stage_cluster_census_sha256": "8" * 64,
        "lifecycle_promotion_estimated_parent_count": 20,
        "lifecycle_promotion_censored_parent_count": 0,
        "lifecycle_no_divergence_count": 0,
        "lifecycle_selected_parent_census_sha256": "9" * 64,
        "lifecycle_promotion_estimator_id": (
            ai_quality_cycle.LIFECYCLE_PROMOTION_ESTIMATOR_ID
        ),
        "lifecycle_promotion_estimator_contract_sha256": ai_quality_cycle._sha256(
            ai_quality_cycle.LIFECYCLE_PROMOTION_ESTIMATOR_CONTRACT
        ),
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
        "decision_level_candidate_notional_eligible_count": 20,
        "candidate_notional_eligible_count": 20,
        "candidate_total_notional_net_profit_krw": 10000,
        "session_exposure_hours": 1.0,
        "eligible_signals_per_session_hour": 20.0,
        "average_actual_holding_duration_sec": 60.0,
        "capital_time_krw_hours": 1.0,
        "net_profit_per_capital_krw_hour": 10000.0,
        "bbo_coverage_pct": 99.0,
        "depth_coverage_pct": 95.0,
        "invalid_transition_count": 0,
    }


def _rolling() -> dict:
    floor_bindings: list[dict] = []
    floor_sha256 = ai_quality_cycle._sha256(floor_bindings)
    partition = {
        "decision_stage": "entry",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "control_contract_sha256": "1" * 64,
        "candidate_contract_sha256": "2" * 64,
        "selected_cost_profile_id": "krx_common_stock",
        "selected_cost_profile_content_sha256": "3" * 64,
        "current_prompt_sha256": live.CONTROL_PROMPT_SHA256,
        "recommended_prompt_sha256": live.RECOMMENDED_PROMPT_SHA256,
        "ablation_design_version": ai_quality_cycle.LEGACY_DESIGN_VERSION,
        "tuning_axis": standing.TUNING_AXIS,
        "economic_reference_bindings_sha256": "4" * 64,
        "economic_reference_binding_count": 20,
        "latest_symbol_master_source_date": "2026-08-17",
        "latest_symbol_master_artifact_sha256": mod._economic_payload_sha256(
            _symbol_master()
        ),
        "source_row_count": 20,
        "source_dates": ["2026-08-17"],
        "windows": {str(days): _window(days) for days in (5, 10, 20)},
        "gate_findings": {str(days): [] for days in (5, 10, 20)},
        "r3_source_candidate_eligible": True,
    }
    body = {
        "schema": ai_quality_cycle.ROLLING_SCHEMA,
        "target_date": "2026-08-17",
        "status": "rolling_evaluated",
        "provider_ablation_floor_bindings": floor_bindings,
        "provider_ablation_floor_bindings_sha256": floor_sha256,
        "global_candidate_blockers": [],
        "current_run_global_blockers": [],
        "current_run_global_blockers_sha256": ai_quality_cycle._sha256([]),
        "blocked_pre_clear_candidate_count": 0,
        "partitions": [partition],
        **ai_quality_cycle.OFFLINE_AUTHORITY,
    }
    return {**body, "artifact_content_sha256": mod._sha256(body)}


def _post_apply_rolling() -> dict:
    rolling = _rolling()
    rolling["target_date"] = "2026-08-18"
    partition = rolling["partitions"][0]
    partition["ablation_design_version"] = ai_quality_cycle.CURRENT_DESIGN_VERSION
    partition["tuning_axis"] = "prompt_contract_effect_on_ask_depletion_context"
    partition["current_prompt_sha256"] = live.RECOMMENDED_PROMPT_SHA256
    partition["source_dates"] = ["2026-08-18"]
    partition["latest_symbol_master_source_date"] = "2026-08-18"
    window = partition["windows"]["5"]
    window["observed_trading_days"] = 1
    window["control_p10_ev_pct"] = -0.14
    window["control_severe_tail_count"] = 1
    window["control_deferred_count"] = 2
    for metrics in partition["windows"].values():
        metrics.update(
            {
                "ablation_design_version": ai_quality_cycle.CURRENT_DESIGN_VERSION,
                "baseline_metric_parent_count": metrics["common_parent_count"],
                "feature_ev_delta_pct": 0.0,
                "composite_ev_delta_pct": 0.02,
                "composite_relative_uplift_pct": 20.0,
                "baseline_p10_ev_pct": -0.20,
                "baseline_severe_tail_count": 1,
                "baseline_deferred_count": 3,
            }
        )
    partition["gate_findings"] = {
        key: ai_quality_cycle._window_gate_findings(metrics)
        for key, metrics in partition["windows"].items()
    }
    partition["r3_source_candidate_eligible"] = all(
        not findings for findings in partition["gate_findings"].values()
    )
    rolling["artifact_content_sha256"] = mod._sha256(
        {
            key: value
            for key, value in rolling.items()
            if key != "artifact_content_sha256"
        }
    )
    return rolling


def test_post_apply_attribution_rejects_resealed_current_run_blocker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    applied, _, _ = _applied_queue(monkeypatch, tmp_path)
    rolling = _post_apply_rolling()
    attribution = mod.build_post_apply_attribution_receipt(
        entry=applied["candidates"][0],
        rolling=rolling,
        target_date="2026-08-18",
        now=datetime(2026, 8, 18, 20, 25, tzinfo=KST),
    )
    rolling["current_run_global_blockers"] = ["source_quality_audit_not_pass"]
    rolling["current_run_global_blockers_sha256"] = ai_quality_cycle._sha256(
        rolling["current_run_global_blockers"]
    )
    rolling["artifact_content_sha256"] = mod._sha256(
        {
            key: value
            for key, value in rolling.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="r2_current_run_global_blocker_projection_invalid"
    ):
        mod.build_post_apply_attribution_receipt(
            entry=applied["candidates"][0],
            rolling=rolling,
            target_date="2026-08-18",
            now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        )
    with pytest.raises(
        ValueError, match="r2_current_run_global_blocker_projection_invalid"
    ):
        mod.build_post_apply_continuation_candidate(
            entry=applied["candidates"][0],
            attribution=attribution,
            attribution_path=tmp_path / "post_apply.json",
            rolling=rolling,
            target_date="2026-08-18",
        )


def test_r2_validator_rejects_current_partition_with_legacy_window_contract() -> None:
    rolling = _post_apply_rolling()
    rolling["partitions"][0]["windows"]["5"].pop("ablation_design_version")
    rolling["artifact_content_sha256"] = mod._sha256(
        {
            key: value
            for key, value in rolling.items()
            if key != "artifact_content_sha256"
        }
    )

    with pytest.raises(
        ValueError, match="r2_partition_window_ablation_design_mismatch"
    ):
        ai_quality_cycle.validate_r2_rolling_artifact(rolling)


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


def _applied_queue(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[dict, Path, Path]:
    test_data = tmp_path / "data"
    handoff_root = test_data / "threshold_cycle" / "handoffs"
    receipt_dir = (
        test_data
        / "threshold_cycle"
        / "machine_microstructure_policy"
        / "apply_receipts"
    )
    activation_root = test_data / "runtime" / "main_ai_quality_prompt_contract"
    monkeypatch.setattr(live, "DATA_DIR", test_data)
    monkeypatch.setattr(live, "ACTIVATION_DIR", activation_root)
    monkeypatch.setattr(approval, "HANDOFF_DIR", handoff_root)
    monkeypatch.setattr(approval, "APPLY_RECEIPT_DIR", receipt_dir)
    authorization = _authorization()
    candidate = mod.build_promotion_candidate(
        authorization=authorization,
        r3_manifest=_manifest(),
        rolling=_rolling(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )
    queue_key = approval._queue_key(
        candidate["candidate_id"], candidate["candidate_sha256"]
    )
    handoff = {
        "schema": approval.HANDOFF_SCHEMA,
        "target_date": "2026-08-18",
        "created_at_kst": "2026-08-18T07:30:00+09:00",
        "queue_key": queue_key,
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
    handoff_path = (
        handoff_root
        / "2026-08-18"
        / (
            f"{approval._safe_id(candidate['candidate_id'])}_"
            f"{candidate['candidate_sha256'][:16]}.json"
        )
    )
    mod._atomic_write_json(handoff_path, handoff)
    activation_path = live.activation_path("2026-08-18")
    apply_path = receipt_dir / (
        f"2026-08-18_{candidate['candidate_sha256']}_applied.json"
    )
    symbol_master_path = (
        test_data
        / "report"
        / "micro_reversion_economic_reference"
        / "micro_reversion_symbol_master_2026-08-17.json"
    )
    mod._atomic_write_json(symbol_master_path, _symbol_master())
    activation = mod.build_preopen_activation(
        handoff_path=handoff_path,
        handoff=handoff,
        candidate=candidate,
        authorization=authorization,
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
        activation_artifact_path=activation_path,
        apply_receipt_path=apply_path,
        symbol_master_path=symbol_master_path,
    )
    mod._atomic_write_json(activation_path, activation)
    mod._atomic_write_json(apply_path, mod.apply_receipt(activation))
    queue = {
        "candidates": [
            {
                "queue_key": queue_key,
                "candidate_id": candidate["candidate_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "candidate": candidate,
                "state": approval.STATE_PREOPEN_SCHEDULED,
                "source_date": candidate["source_date"],
                "evidence_valid_through": candidate["evidence_valid_through"],
                "operator_decision_artifact": str(tmp_path / "decision.json"),
                "operator_authorization_id": authorization["operator_authorization_id"],
                "operator_decision_at_kst": "2026-08-17T20:30:00+09:00",
                "operator_registry_entry_sha256": mod._registry_sha256(),
                "runtime_registry_entry_sha256": mod._registry_sha256(),
                "preopen_target_date": "2026-08-18",
                "preopen_handoff": str(handoff_path),
                "authorization_mode": "first_explicit_operator_approval",
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

    assert candidate["evidence"]["rolling_paired_complete_lifecycle_count"] == {
        "5d": 20,
        "10d": 20,
        "20d": 20,
    }
    assert candidate["evidence"]["rolling_paired_complete_lifecycle_floor"] == (
        approval.ROLLING_PAIRED_LIFECYCLE_FLOORS
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
    applied, receipt_dir, _ = _applied_queue(monkeypatch, tmp_path)
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


def test_unreviewed_prompt_hash_fails_before_standing_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _r3_candidate()
    candidate["recommended_prompt_sha256"] = "9" * 64
    content = {
        key: value
        for key, value in candidate.items()
        if key not in {"candidate_id", "candidate_sha256"}
    }
    candidate["candidate_sha256"] = mod._sha256(content)
    monkeypatch.setattr(
        standing,
        "resolve_standing_authorization",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("fabricated R3 must not reach standing resolution")
        ),
    )

    with pytest.raises(ValueError, match="r3_manifest_candidate_projection_mismatch"):
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
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    test_data = tmp_path / "data"
    monkeypatch.setattr(live, "DATA_DIR", test_data)
    monkeypatch.setattr(
        live,
        "ACTIVATION_DIR",
        test_data / "runtime" / "main_ai_quality_prompt_contract",
    )
    monkeypatch.setattr(
        approval,
        "HANDOFF_DIR",
        test_data / "threshold_cycle" / "handoffs",
    )
    monkeypatch.setattr(
        approval,
        "APPLY_RECEIPT_DIR",
        test_data
        / "threshold_cycle"
        / "machine_microstructure_policy"
        / "apply_receipts",
    )
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
        "runtime_effect": False,
        "runtime_apply_performed": False,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    handoff_path = (
        approval.HANDOFF_DIR
        / "2026-08-18"
        / (
            f"{approval._safe_id(candidate['candidate_id'])}_"
            f"{candidate['candidate_sha256'][:16]}.json"
        )
    )
    mod._atomic_write_json(handoff_path, handoff)
    activation_path = live.activation_path("2026-08-18")
    receipt_path = approval.APPLY_RECEIPT_DIR / (
        f"2026-08-18_{candidate['candidate_sha256']}_applied.json"
    )
    symbol_master_path = (
        test_data
        / "report"
        / "micro_reversion_economic_reference"
        / "micro_reversion_symbol_master_2026-08-17.json"
    )
    mod._atomic_write_json(symbol_master_path, _symbol_master())
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
    mod._atomic_write_json(activation_path, activation)
    mod._atomic_write_json(receipt_path, mod.apply_receipt(activation))

    selected = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert selected["enabled"] is False
    assert selected["selected_prompt_version"] == live.CONTROL_PROMPT_VERSION
    assert selected["status"] == "fallback_legacy_runtime_authority_disabled"
    assert selected["blocking_reasons"] == [live.LEGACY_RUNTIME_AUTHORITY_BLOCKER]
    assert selected["runtime_effect"] is False
    assert selected["runtime_apply_performed"] is False
    assert selected["allowed_runtime_apply"] is False
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
    assert outside_master["status"] == "fallback_legacy_runtime_authority_disabled"
    assert outside_master["blocking_reasons"] == [live.LEGACY_RUNTIME_AUTHORITY_BLOCKER]

    master_snapshot = symbol_master_path.read_text(encoding="utf-8")
    tampered_master = _symbol_master()
    tampered_master["records"][0]["instrument_type"] = "ETF"
    mod._atomic_write_json(symbol_master_path, tampered_master)
    invalid_master = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert invalid_master["enabled"] is False
    assert invalid_master["blocking_reasons"] == [live.LEGACY_RUNTIME_AUTHORITY_BLOCKER]
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
    assert no_receipt["blocking_reasons"] == [live.LEGACY_RUNTIME_AUTHORITY_BLOCKER]
    receipt_path.write_text(receipt_snapshot, encoding="utf-8")

    activation_snapshot = activation_path.read_text(encoding="utf-8")
    duplicate_activation = activation_snapshot.rstrip()
    duplicate_activation = (
        duplicate_activation[:-1] + f',"schema":"{live.ACTIVATION_SCHEMA}"}}'
    )
    activation_path.write_text(duplicate_activation, encoding="utf-8")
    duplicate_key = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert duplicate_key["status"] == "fallback_legacy_runtime_authority_disabled"
    assert duplicate_key["blocking_reasons"] == [live.LEGACY_RUNTIME_AUTHORITY_BLOCKER]
    activation_path.write_text(activation_snapshot, encoding="utf-8")

    with gzip.open(
        activation_path.with_name(activation_path.name + ".gz"),
        "wt",
        encoding="utf-8",
    ) as handle:
        json.dump({"schema": "divergent"}, handle)
    dual_generation = live.resolve_main_ai_quality_live_policy(
        configured_prompt_version="hot_v1",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        stock_code="005930",
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        path=activation_path,
    )
    assert dual_generation["status"] == "fallback_legacy_runtime_authority_disabled"
    assert dual_generation["blocking_reasons"] == [
        live.LEGACY_RUNTIME_AUTHORITY_BLOCKER
    ]
    activation_path.with_name(activation_path.name + ".gz").unlink()

    activation["candidate_sha256"] = "0" * 64
    mod._atomic_write_json(activation_path, activation)
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


@pytest.mark.parametrize("candidate_count", [0, 1, 2])
def test_preopen_is_fail_closed_regardless_of_candidate_cardinality(
    candidate_count: int,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    candidate = {
        "runtime_design": {
            "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        }
    }
    row = {
        "state": approval.STATE_PREOPEN_SCHEDULED,
        "preopen_target_date": "2026-08-18",
        "candidate": candidate,
    }
    monkeypatch.setattr(
        approval,
        "load_queue",
        lambda *_args, **_kwargs: {
            "candidates": [dict(row) for _ in range(candidate_count)]
        },
    )

    result = mod._preopen(
        target_date="2026-08-18",
        write=False,
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
        queue_path=tmp_path / "queue.json",
    )

    assert result["status"] == "blocked_fail_closed"
    assert result["reason"] == live.LEGACY_RUNTIME_AUTHORITY_BLOCKER
    assert result["runtime_effect"] is False
    assert result["allowed_runtime_apply"] is False


def test_preopen_exact_candidate_write_is_zero_publish_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(approval, "DEFAULT_QUEUE_PATH", queue_path)
    monkeypatch.setattr(
        approval,
        "load_queue",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("disabled PREOPEN must not consume authority artifacts")
        ),
    )

    result = mod._preopen(
        target_date="2026-08-18",
        write=True,
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
        queue_path=queue_path,
    )

    assert result == mod._preopen_runtime_authority_blocked_result(
        target_date="2026-08-18"
    )
    assert list(tmp_path.iterdir()) == []


def test_cli_preopen_disabled_reports_failure_without_activation_publish(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    report = tmp_path / "preopen-report.json"
    monkeypatch.setattr(mod, "report_path", lambda *_args: report)
    monkeypatch.setattr(
        mod,
        "_cli_now_for_phase",
        lambda **_kwargs: datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )

    return_code = mod.main(
        ["--phase", "preopen", "--target-date", "2026-08-18", "--write"]
    )

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert return_code == 2
    assert payload["status"] == "blocked_fail_closed"
    assert payload["reason"] == live.LEGACY_RUNTIME_AUTHORITY_BLOCKER
    assert payload["runtime_effect"] is False
    assert "activation_path" not in payload


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


def test_postclose_runtime_control_allows_bounded_cross_midnight_tail() -> None:
    target_day = datetime(2026, 8, 25, tzinfo=KST).date()

    assert mod._postclose_write_time_valid(
        target_day=target_day,
        current=datetime(2026, 8, 26, 2, 47, tzinfo=KST),
    )
    assert not mod._postclose_write_time_valid(
        target_day=target_day,
        current=datetime(2026, 8, 26, 12, 0, tzinfo=KST),
    )
    assert not mod._postclose_write_time_valid(
        target_day=target_day,
        current=datetime(2026, 8, 24, 23, 59, tzinfo=KST),
    )


def test_preopen_write_rejects_noncanonical_queue_before_any_publish(
    tmp_path: Path,
) -> None:
    queue_path = tmp_path / "forged-queue.json"

    with pytest.raises(ValueError, match="preopen_write_queue_path_not_canonical"):
        mod._preopen(
            target_date="2026-08-18",
            write=True,
            now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
            queue_path=queue_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_postclose_two_applied_candidates_leave_zero_attribution_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    authorization_path = tmp_path / "standing.json"
    rolling_path = tmp_path / "rolling.json"
    receipt_dir = tmp_path / "receipts"
    mod._atomic_write_json(authorization_path, _authorization())
    mod._atomic_write_json(rolling_path, {"target_date": "2026-08-18"})
    monkeypatch.setattr(mod, "STANDING_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(ai_quality_cycle, "rolling_report_path", lambda _: rolling_path)
    candidate = {
        "runtime_design": {
            "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        }
    }
    queue = {
        "candidates": [
            {
                "state": approval.STATE_APPLIED,
                "candidate_sha256": char * 64,
                "candidate": candidate,
            }
            for char in ("a", "b")
        ],
        "family_enrollments": {},
    }
    monkeypatch.setattr(approval, "load_queue", lambda *_args, **_kwargs: queue)
    monkeypatch.setattr(
        approval,
        "sync_queue",
        lambda value, *_args, **_kwargs: (value, []),
    )
    monkeypatch.setattr(
        mod,
        "build_post_apply_attribution_receipt",
        lambda **kwargs: {
            "target_date": "2026-08-18",
            "candidate_sha256": kwargs["entry"]["candidate_sha256"],
        },
    )

    with pytest.raises(
        ValueError,
        match="post_apply_attribution_candidate_not_unique",
    ):
        mod._postclose(
            target_date="2026-08-18",
            write=True,
            now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
            queue_path=tmp_path / "queue.json",
            approval_dir=tmp_path / "approvals",
            apply_receipt_dir=receipt_dir,
        )

    assert not list(receipt_dir.glob("*.json"))


def test_postclose_two_applied_mixed_r6_validity_is_zero_write_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    authorization_path = tmp_path / "standing.json"
    rolling_path = tmp_path / "rolling.json"
    receipt_dir = tmp_path / "receipts"
    queue_path = tmp_path / "queue.json"
    source_path = tmp_path / "runtime-source.json"
    mod._atomic_write_json(authorization_path, _authorization())
    mod._atomic_write_json(rolling_path, {"target_date": "2026-08-18"})
    monkeypatch.setattr(mod, "STANDING_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(ai_quality_cycle, "rolling_report_path", lambda _: rolling_path)
    monkeypatch.setattr(mod, "source_report_path", lambda _: source_path)
    candidate = {
        "runtime_design": {
            "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        }
    }
    queue = {
        "candidates": [
            {
                "state": approval.STATE_APPLIED,
                "candidate_sha256": char * 64,
                "candidate": candidate,
            }
            for char in ("a", "b")
        ],
        "family_enrollments": {},
    }
    monkeypatch.setattr(approval, "load_queue", lambda *_args, **_kwargs: queue)
    monkeypatch.setattr(
        approval,
        "sync_queue",
        lambda value, *_args, **_kwargs: (value, []),
    )
    build_calls: list[str] = []

    def mixed_builder(**kwargs: object) -> dict:
        entry = kwargs["entry"]
        assert isinstance(entry, dict)
        digest = str(entry["candidate_sha256"])
        build_calls.append(digest)
        if digest == "b" * 64:
            raise ValueError("crafted_r6_invalid")
        return {"target_date": "2026-08-18", "candidate_sha256": digest}

    monkeypatch.setattr(mod, "build_post_apply_attribution_receipt", mixed_builder)

    with pytest.raises(
        ValueError,
        match="post_apply_attribution_candidate_not_unique",
    ):
        mod._postclose(
            target_date="2026-08-18",
            write=True,
            now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
            queue_path=queue_path,
            approval_dir=tmp_path / "approvals",
            apply_receipt_dir=receipt_dir,
        )

    assert build_calls == []
    assert not list(receipt_dir.glob("*.json"))
    assert not queue_path.exists()
    assert not source_path.exists()


def test_standing_authorization_cannot_be_used_before_review_time() -> None:
    authorization = standing.build_standing_authorization(
        operator_authorization_id="operator-future-review",
        operator_instruction=mod.OPERATOR_INSTRUCTION,
        reviewed_at_kst="2026-08-18T09:00:00+09:00",
        expires_at_kst="2026-09-18T09:00:00+09:00",
        runtime_family=approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        stage="entry",
        axis="prompt_contract_effect",
        bounded_values={
            "current": live.CONTROL_PROMPT_SHA256,
            "recommended": live.RECOMMENDED_PROMPT_SHA256,
        },
        bounded_contract_sha256=approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256,
        evidence_contract=_evidence_contract(),
        expected_runtime_registry_entry_sha256=mod._registry_sha256(),
        expected_preopen_consumer=mod.PREOPEN_CONSUMER,
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
    )

    resolved = standing.resolve_standing_authorization(
        authorization,
        _manifest(),
        approval_queue={"candidates": [], "family_enrollments": {}},
        now=datetime(2026, 8, 17, 20, 30, tzinfo=KST),
    )

    assert "standing_authorization_not_yet_reviewed" in resolved["blocker_codes"]


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
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    applied, receipt_dir, _ = _applied_queue(monkeypatch, tmp_path)
    assert applied["candidates"][0]["state"] == approval.STATE_APPLIED
    assert applied["family_enrollments"] == {}
    rolling_path = tmp_path / "rolling.json"
    rolling = _post_apply_rolling()
    mod._atomic_write_json(rolling_path, rolling)
    monkeypatch.setattr(ai_quality_cycle, "rolling_report_path", lambda _: rolling_path)

    attribution = mod.build_post_apply_attribution_receipt(
        entry=applied["candidates"][0],
        rolling=rolling,
        target_date="2026-08-18",
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
    )
    attribution_path = receipt_dir / (
        f"2026-08-18_{applied['candidates'][0]['candidate_sha256']}_post_apply.json"
    )
    tampered = dict(attribution)
    tampered["continuation_checks"] = {
        **attribution["continuation_checks"],
        "source_quality_adjusted_ev_positive": False,
    }
    tampered["receipt_content_sha256"] = mod._sha256(
        {
            key: value
            for key, value in tampered.items()
            if key != "receipt_content_sha256"
        }
    )
    mod._atomic_write_json(attribution_path, tampered)
    still_applied, rejected = approval.sync_queue(
        applied,
        source_candidates=[],
        source_path=None,
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 35, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    assert rejected == []
    assert still_applied["candidates"][0]["state"] == approval.STATE_APPLIED
    assert still_applied["family_enrollments"] == {}

    mod._atomic_write_json(attribution_path, attribution)
    attributed, rejected = approval.sync_queue(
        still_applied,
        source_candidates=[],
        source_path=None,
        as_of_date=datetime(2026, 8, 18, tzinfo=KST).date(),
        now=datetime(2026, 8, 18, 20, 40, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
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
        rolling=rolling,
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
        apply_receipt_dir=receipt_dir,
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
