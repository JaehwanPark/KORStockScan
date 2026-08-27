import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import machine_microstructure_policy_approval as mod
from src.engine.monitoring import machine_microstructure_attribution as attribution_mod

KST = ZoneInfo("Asia/Seoul")
MAIN_AI_QUALITY_REGISTRY_ENTRY = dict(
    mod.TRUSTED_RUNTIME_FAMILY_REGISTRY[mod.MAIN_AI_QUALITY_RUNTIME_FAMILY]
)


def _runtime_registry() -> dict:
    return {
        "widget_micro_entry_confirmation_v1": {
            "enabled": True,
            "stage": "entry",
            "axis": "micro_confirmation_threshold",
            "bounded_contract_sha256": "b" * 64,
            "preopen_consumer": "widget_micro_entry_policy_apply",
            "apply_receipt_owner": "widget_micro_entry_policy_apply",
            "post_apply_attribution_owner": ("widget_micro_entry_policy_attribution"),
        }
    }


@pytest.fixture(autouse=True)
def _trusted_runtime_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mod,
        "TRUSTED_RUNTIME_FAMILY_REGISTRY",
        _runtime_registry(),
    )


def _candidate(
    *,
    candidate_id: str = "widget:005930:entry:micro_axis",
    registered: bool = True,
    recommended_value: float = 0.25,
    first_approval: bool = True,
    source_date: str = "2026-08-14",
) -> dict:
    return {
        "schema": mod.CANDIDATE_SCHEMA,
        "candidate_id": candidate_id,
        "source_date": source_date,
        "evidence_valid_through": "2026-08-31",
        "owner": "widget",
        "owner_scope_id": "005930:KRX_REGULAR",
        "first_operator_approval_required": first_approval,
        "evidence": {
            "observed_trading_days": 5,
            "matched_entry_anchors": 20,
            "bbo_complete_rate_pct": 99.0,
            "depth_window_coverage_pct": 95.0,
            "invalid_contract_row_count": 0,
            "rolling_source_quality_adjusted_ev_pct": {
                "5d": 0.11,
                "10d": 0.09,
                "20d": 0.08,
            },
            "rolling_paired_complete_lifecycle_count": {
                "5d": 5,
                "10d": 10,
                "20d": 20,
            },
            "rolling_paired_complete_lifecycle_floor": {
                "5d": 5,
                "10d": 10,
                "20d": 20,
            },
            "relative_primary_ev_uplift_pct": 1.2,
            "primary_20d_net_profit": 12_000,
            "costs_included": True,
            "source_quality_pass": True,
            "paired_p10_not_worse": True,
            "held_unresolved_not_increased": True,
        },
        "runtime_design": {
            "runtime_family": "widget_micro_entry_confirmation_v1",
            "stage": "entry",
            "axis": "micro_confirmation_threshold",
            "mapping_status": "registered" if registered else "design_required",
            "runtime_registry_verified": registered,
            "same_stage_owner_conflict_free": True,
            "preopen_consumer": "widget_micro_entry_policy_apply",
            "bounded_values": {
                "current": 0.2,
                "recommended": recommended_value,
            },
            "bounded_contract_sha256": "b" * 64,
            "rollback": {
                "trigger": "post_apply_ev_or_source_quality_guard_breach",
                "value": 0.2,
            },
            "post_apply_attribution": {
                "owner": "widget_micro_entry_policy_attribution",
                "window": "5d_10d_20d",
            },
            "forbidden_uses": [
                "broker_guard_bypass",
                "provider_or_bot_or_cap_change",
            ],
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _objective_bound_candidate(
    *,
    source_date: str = "2026-08-14",
    gap_codes: list[str] | None = None,
) -> tuple[dict, dict]:
    resolved_gap_codes = (
        gap_codes
        if gap_codes is not None
        else [
            "rolling_paired_policy_candidate_producer_not_implemented",
            "speed_and_capital_occupancy_not_policy_selection_axes",
        ]
    )
    candidate = _candidate(source_date=source_date)
    candidate["objective_followup_binding"] = {
        "schema": mod.OBJECTIVE_CANDIDATE_BINDING_SCHEMA,
        "followup_id": mod.FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
        "resolved_gap_codes": resolved_gap_codes,
    }
    binding = {
        "schema": mod.OBJECTIVE_HANDOFF_BINDING_SCHEMA,
        "followup_id": mod.FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": mod.candidate_sha256(candidate),
        "required_gap_codes": resolved_gap_codes,
        "resolved_gap_codes": resolved_gap_codes,
    }
    return candidate, binding


def _objective_followup(
    *,
    source_date: str = "2026-08-14",
    state: str = "IMPLEMENTATION_REQUIRED",
    followup_required: bool = True,
    remaining_gap_codes: list[str] | None = None,
    completion_evidence: dict | None = None,
    candidate_handoff_binding: dict | None = None,
) -> dict:
    row = {
        "schema": mod.OBJECTIVE_FOLLOWUP_SCHEMA,
        "followup_id": "machine_lifecycle_turnover_policy_research_v1",
        "source_date": source_date,
        "state": state,
        "state_reason": "rolling_paired_research_not_implemented",
        "followup_required": followup_required,
        "attention_class": "code_improvement_workorder",
        "operator_decision_required": False,
        "current_capability": "diagnostic_observation_only",
        "remaining_gap_codes": (
            remaining_gap_codes
            if remaining_gap_codes is not None
            else [
                "rolling_paired_policy_candidate_producer_not_implemented",
                "speed_and_capital_occupancy_not_policy_selection_axes",
            ]
        ),
        "next_action": "implement_source_only_rolling_paired_policy_research",
        "metric_contract": {
            "metric_role": "machine_lifecycle_objective_completion_followup",
            "decision_authority": "postclose_followup_tracking_only",
            "window_policy": "daily_until_implementation_evidence",
            "sample_floor": {"policy_or_runtime_change": "not_permitted"},
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": ["exact_target_date_machine_attribution"],
            "forbidden_uses": ["runtime_env_or_threshold_or_order_mutation"],
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if completion_evidence is not None:
        row["completion_evidence"] = completion_evidence
    if candidate_handoff_binding is not None:
        row["candidate_handoff_binding"] = candidate_handoff_binding
    return row


def _source_report_payload(*, objective_followups: list[object] | None = None) -> dict:
    payload = {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": "2026-08-14",
        "promotion_candidate_intake_contract": {
            "schema": mod.CANDIDATE_SCHEMA,
            "consumer": "src.engine.automation.machine_microstructure_policy_approval",
            "daily_report_runtime_effect": False,
        },
        "policy_promotion_candidates": [],
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    if objective_followups is not None:
        payload["objective_followups"] = objective_followups
    return payload


def _empty(now: datetime) -> dict:
    return mod._empty_queue(now=now)


def _producer_complete_followup(source_date: str) -> dict:
    return attribution_mod._fast_lifecycle_objective_followup(
        target_date=source_date,
        objective_alignment={
            "reflected_in_real_runtime_policy": True,
            "implementation_boundary": {
                "speed_or_turnover_metric_changes_policy_selection": True,
                "rolling_paired_policy_candidate_producer_present": True,
            },
            "remaining_gaps": [],
        },
        promotion_candidates=[],
    )


def _queue_with_objective_handoff(now: datetime) -> dict:
    source_candidate, handoff_binding = _objective_bound_candidate(
        source_date=now.date().isoformat()
    )
    queue, candidate_rejections = mod.sync_queue(
        _empty(now),
        source_candidates=[source_candidate],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    accepted_keys = queue["last_sync"]["accepted_candidate_queue_keys"]
    queue, followup_rejections = mod.sync_objective_followups(
        queue,
        source_followups=[
            _objective_followup(
                source_date=now.date().isoformat(),
                state="CANDIDATE_QUEUE_HANDOFF",
                followup_required=False,
                remaining_gap_codes=[],
                candidate_handoff_binding=handoff_binding,
            )
        ],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        accepted_candidate_queue_keys=accepted_keys,
        now=now,
    )
    assert candidate_rejections == []
    assert followup_rejections == []
    return queue


def test_evidence_ready_candidate_requires_registered_runtime_design() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, rejected = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate(registered=False)],
        source_path=Path("source.json"),
        as_of_date=date(2026, 8, 14),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    assert rejected == []
    entry = queue["candidates"][0]
    assert entry["state"] == mod.STATE_DESIGN_REQUIRED
    assert "runtime_family_mapping_not_registered" in entry["runtime_design_errors"]
    assert queue["authority"]["runtime_effect"] is False


def test_candidate_cannot_self_declare_trusted_runtime_registration() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, rejected = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
        runtime_registry={},
    )

    assert rejected == []
    entry = queue["candidates"][0]
    assert entry["state"] == mod.STATE_DESIGN_REQUIRED
    assert "runtime_family_not_in_trusted_registry" in entry["runtime_design_errors"]


def test_candidate_cannot_self_declare_post_apply_receipt_owner() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    candidate = _candidate()
    candidate["runtime_design"]["post_apply_attribution"][
        "owner"
    ] = "candidate_controlled_attribution_owner"

    queue, rejected = mod.sync_queue(
        _empty(now),
        source_candidates=[candidate],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    assert rejected == []
    entry = queue["candidates"][0]
    assert entry["state"] == mod.STATE_DESIGN_REQUIRED
    assert "runtime_family_trusted_registry_mismatch" in entry["runtime_design_errors"]


def test_candidate_remains_in_queue_when_daily_source_has_no_candidate() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    carried, rejected = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=Path("missing-next-source.json"),
        as_of_date=date(2026, 8, 18),
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    assert rejected == []
    assert carried["candidates"][0]["state"] == mod.STATE_REVIEW_READY
    assert carried["candidates"][0]["candidate_id"] == _candidate()["candidate_id"]


def test_fresh_loaded_source_withdrawal_blocks_stale_approved_candidate(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve only while rolling evidence remains current.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )

    withdrawn, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=Path("fresh-empty-source.json"),
        as_of_date=date(2026, 8, 18),
        source_status="loaded",
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        approval_artifacts=mod._approval_artifacts(tmp_path / "approvals"),
        apply_receipt_dir=tmp_path / "receipts",
    )

    stale = withdrawn["candidates"][0]
    assert stale["state"] == mod.STATE_REVALIDATION_REQUIRED
    assert stale["state_reason"] == (
        "fresh_source_candidate_withdrawn_revalidation_required"
    )
    assert "operator_decision_artifact" not in stale
    _, handoffs = mod.schedule_preopen_handoffs(
        withdrawn,
        target_date=date(2026, 8, 19),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 19, 7, 40, tzinfo=KST),
    )
    assert handoffs == []


def test_fresh_rejected_candidate_version_blocks_previous_version() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    rejected_version = _candidate(source_date="2026-08-18")
    rejected_version["evidence"]["matched_entry_anchors"] = 19

    revalidation, rejected = mod.sync_queue(
        queue,
        source_candidates=[rejected_version],
        source_path=Path("fresh-rejected-source.json"),
        as_of_date=date(2026, 8, 18),
        source_status="loaded",
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    assert rejected[0]["candidate_id"] == _candidate()["candidate_id"]
    assert "matched_entry_anchors_below_20" in rejected[0]["errors"]
    assert revalidation["candidates"][0]["state"] == (mod.STATE_REVALIDATION_REQUIRED)
    assert revalidation["candidates"][0]["state_reason"] == (
        "fresh_source_candidate_rejected_revalidation_required"
    )


def test_forged_persisted_family_enrollment_is_not_auto_chain_authority(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate(first_approval=False)],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    queue["family_enrollments"] = {
        "widget_micro_entry_confirmation_v1": {
            "runtime_family": "widget_micro_entry_confirmation_v1",
            "stage": "entry",
            "axis": "micro_confirmation_threshold",
            "bounded_contract_sha256": "b" * 64,
            "runtime_registry_entry_sha256": queue["candidates"][0][
                "runtime_registry_entry_sha256"
            ],
            "first_approved_queue_key": "forged",
            "first_apply_receipt": str(tmp_path / "receipts" / "missing.json"),
            "enrolled_after_guarded_apply": True,
        }
    }

    validated, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )

    assert validated["family_enrollments"] == {}
    assert validated["candidates"][0]["state"] == mod.STATE_REVIEW_READY


def test_changed_candidate_hash_expires_old_version_and_cannot_reuse_approval() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    old = queue["candidates"][0]
    approval = {
        "schema": mod.APPROVAL_SCHEMA,
        "queue_key": old["queue_key"],
        "candidate_sha256": old["candidate_sha256"],
        "decision": "approve",
        "decided_at_kst": now.isoformat(),
        "operator_authorization_id": "operator-old",
        "_artifact_path": "old-approval.json",
    }
    changed = _candidate(recommended_value=0.3)
    updated, _ = mod.sync_queue(
        queue,
        source_candidates=[changed],
        source_path=Path("changed.json"),
        as_of_date=now.date(),
        now=now,
        approval_artifacts=[approval],
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    by_hash = {row["candidate_sha256"]: row for row in updated["candidates"]}
    assert by_hash[old["candidate_sha256"]]["state"] == mod.STATE_EXPIRED
    new_hash = mod.candidate_sha256(changed)
    assert by_hash[new_hash]["state"] == mod.STATE_REVIEW_READY
    assert "operator_decision_artifact" not in by_hash[new_hash]


def test_approval_artifact_without_explicit_operator_instruction_is_ignored() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    entry = queue["candidates"][0]
    incomplete = {
        "schema": mod.APPROVAL_SCHEMA,
        "queue_key": entry["queue_key"],
        "candidate_sha256": entry["candidate_sha256"],
        "decision": "approve",
        "decided_at_kst": now.isoformat(),
        "operator_authorization_id": "operator-explicit",
        "_artifact_path": "incomplete.json",
    }

    unchanged, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=now.date(),
        now=now,
        approval_artifacts=[incomplete],
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    assert unchanged["candidates"][0]["state"] == mod.STATE_REVIEW_READY
    assert "operator_decision_artifact" not in unchanged["candidates"][0]


def test_operator_approval_then_preopen_writes_authorization_handoff_only(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    entry = queue["candidates"][0]
    approved, approval_path = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve first bounded family for next PREOPEN only.",
        approval_dir=tmp_path / "approvals",
        now=now,
    )
    assert approval_path.exists()
    assert approved["candidates"][0]["state"] == mod.STATE_USER_APPROVED

    scheduled, handoffs = mod.schedule_preopen_handoffs(
        approved,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )

    assert scheduled["candidates"][0]["state"] == mod.STATE_PREOPEN_SCHEDULED
    assert len(handoffs) == 1
    payload = json.loads(handoffs[0].read_text(encoding="utf-8"))
    assert payload["status"] == "preopen_authorization_handoff_ready"
    assert payload["allowed_runtime_apply"] is True
    assert payload["runtime_effect"] is False
    assert payload["runtime_apply_performed"] is False
    assert payload["actual_order_submitted"] is False

    unchanged, next_handoffs = mod.schedule_preopen_handoffs(
        scheduled,
        target_date=date(2026, 8, 19),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 19, 7, 40, tzinfo=KST),
    )
    assert next_handoffs == []
    assert unchanged["candidates"][0]["preopen_target_date"] == "2026-08-18"


def test_retired_main_ai_quality_family_never_publishes_positive_handoff(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    family = mod.MAIN_AI_QUALITY_RUNTIME_FAMILY
    registry = {family: dict(MAIN_AI_QUALITY_REGISTRY_ENTRY)}
    monkeypatch.setattr(mod, "TRUSTED_RUNTIME_FAMILY_REGISTRY", registry)
    registry_entry = registry[family]
    candidate = _candidate(
        candidate_id="main-ai-quality:entry:legacy-prompt-contract",
        source_date="2026-08-25",
    )
    candidate["runtime_design"] = {
        "runtime_family": family,
        "stage": registry_entry["stage"],
        "axis": registry_entry["axis"],
        "mapping_status": "registered",
        "runtime_registry_verified": True,
        "same_stage_owner_conflict_free": True,
        "preopen_consumer": registry_entry["preopen_consumer"],
        "effective_venue": registry_entry["effective_venue"],
        "session_bucket": registry_entry["session_bucket"],
        "bounded_values": dict(registry_entry["bounded_values"]),
        "bounded_contract_sha256": registry_entry["bounded_contract_sha256"],
        "rollback": {
            "trigger": "any_contract_gap",
            "value": registry_entry["bounded_values"]["current"],
        },
        "post_apply_attribution": {
            "owner": registry_entry["post_apply_attribution_owner"],
            "window": "5d_10d_20d",
        },
        "forbidden_uses": ["runtime_or_order_authority_publication"],
    }
    postclose = datetime(2026, 8, 25, 20, 30, tzinfo=KST)
    queue, rejections = mod.sync_queue(
        mod._empty_queue(now=postclose),
        source_candidates=[candidate],
        source_path=Path("legacy-r3.json"),
        as_of_date=postclose.date(),
        now=postclose,
        apply_receipt_dir=Path("/__no_receipts__"),
        runtime_registry=registry,
    )
    assert rejections == []
    entry = queue["candidates"][0]
    approved, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="standing-main-ai-quality-20260825",
        operator_instruction="Approve only when the family owns runtime authority.",
        approval_dir=tmp_path / "approvals",
        now=postclose,
        runtime_registry=registry,
    )

    scheduled, handoffs = mod.schedule_preopen_handoffs(
        approved,
        target_date=date(2026, 8, 26),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 26, 7, 35, tzinfo=KST),
        runtime_registry=registry,
    )

    assert handoffs == []
    row = scheduled["candidates"][0]
    assert row["state"] == mod.STATE_DESIGN_REQUIRED
    assert row["state_reason"] == ("preopen_blocked_runtime_family_authority_disabled")
    assert row["candidate"]["allowed_runtime_apply"] is False
    assert not list((tmp_path / "handoffs").rglob("*.json"))


def test_invalid_source_report_is_not_silently_treated_as_no_candidate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")

    (
        path,
        candidates,
        _followups,
        status,
        _objective_status,
        _rejections,
        source_artifact,
    ) = mod._load_source_context_snapshot(
        target_date=date(2026, 8, 14), source_report=source
    )
    report = mod.build_status_report(
        _empty(datetime(2026, 8, 14, 20, 30, tzinfo=KST)),
        phase="postclose",
        target_date=date(2026, 8, 14),
        source_path=path,
        source_status=status,
        intake_rejections=[],
        reminder_status="not_needed_or_duplicate",
        source_artifact=source_artifact,
    )

    assert candidates == []
    assert status == "contract_invalid"
    assert report["decision"] == "source_gap_queue_preserved"
    assert report["source_status"] == "contract_invalid"
    assert report["source_artifact"] == {
        "schema": mod.SOURCE_ARTIFACT_PROVENANCE_SCHEMA,
        "path": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "mtime_ns": source.stat().st_mtime_ns,
        "size_bytes": source.stat().st_size,
    }


def test_source_snapshot_rejects_atomic_replacement_during_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    original = _source_report_payload(objective_followups=[])
    source.write_text(json.dumps(original), encoding="utf-8")
    replacement = tmp_path / "replacement.json"
    changed = _source_report_payload(objective_followups=[])
    changed["policy_promotion_candidates"] = [
        _candidate(candidate_id="replacement:005930:entry:micro_axis")
    ]
    replacement.write_text(json.dumps(changed), encoding="utf-8")
    source_path_stat = mod._source_path_stat
    replacement_performed = False

    def _replace_before_path_stat(path: Path) -> os.stat_result:
        nonlocal replacement_performed
        if not replacement_performed:
            os.replace(replacement, path)
            replacement_performed = True
        return source_path_stat(path)

    monkeypatch.setattr(mod, "_source_path_stat", _replace_before_path_stat)

    path, payload, status, source_artifact = mod._load_source_payload_snapshot(
        target_date=date(2026, 8, 14), source_report=source
    )

    assert path == source
    assert payload is None
    assert status == "source_changed_during_snapshot"
    assert source_artifact == {
        "schema": mod.SOURCE_ARTIFACT_PROVENANCE_SCHEMA,
        "path": str(source),
        "sha256": None,
        "mtime_ns": None,
        "size_bytes": None,
    }
    assert json.loads(source.read_text(encoding="utf-8")) == changed


def test_status_report_keeps_exact_loaded_snapshot_after_atomic_replacement(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    original = _source_report_payload(objective_followups=[])
    original["policy_promotion_candidates"] = [
        _candidate(candidate_id="original:005930:entry:micro_axis")
    ]
    original_bytes = json.dumps(original).encode("utf-8")
    source.write_bytes(original_bytes)
    (
        path,
        candidates,
        _followups,
        status,
        objective_status,
        _rejections,
        source_artifact,
    ) = mod._load_source_context_snapshot(
        target_date=date(2026, 8, 14), source_report=source
    )

    replacement = tmp_path / "replacement.json"
    changed = _source_report_payload(objective_followups=[])
    changed["policy_promotion_candidates"] = [
        _candidate(candidate_id="replacement:005930:entry:micro_axis")
    ]
    replacement.write_text(json.dumps(changed), encoding="utf-8")
    os.replace(replacement, source)
    report = mod.build_status_report(
        _empty(datetime(2026, 8, 14, 20, 30, tzinfo=KST)),
        phase="postclose",
        target_date=date(2026, 8, 14),
        source_path=path,
        source_status=status,
        objective_followup_source_status=objective_status,
        intake_rejections=[],
        reminder_status="not_needed_or_duplicate",
        source_artifact=source_artifact,
    )

    assert [row["candidate_id"] for row in candidates] == [
        "original:005930:entry:micro_axis"
    ]
    assert report["source_status"] == "loaded"
    assert (
        report["source_artifact"]["sha256"]
        == hashlib.sha256(original_bytes).hexdigest()
    )
    assert (
        report["source_artifact"]["sha256"]
        != hashlib.sha256(source.read_bytes()).hexdigest()
    )


def test_postclose_rejects_commit_when_source_is_replaced_after_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "source.json"
    original = _source_report_payload(objective_followups=[])
    original["policy_promotion_candidates"] = [
        _candidate(candidate_id="original:005930:entry:micro_axis")
    ]
    source.write_text(json.dumps(original), encoding="utf-8")
    replacement = tmp_path / "replacement.json"
    changed = _source_report_payload(objective_followups=[])
    changed["policy_promotion_candidates"] = [
        _candidate(candidate_id="replacement:005930:entry:micro_axis")
    ]
    replacement.write_text(json.dumps(changed), encoding="utf-8")
    sync_queue = mod.sync_queue
    replacement_performed = False

    def _replace_then_sync(*args: object, **kwargs: object) -> tuple[dict, list]:
        nonlocal replacement_performed
        if not replacement_performed:
            os.replace(replacement, source)
            replacement_performed = True
        return sync_queue(*args, **kwargs)

    monkeypatch.setattr(mod, "sync_queue", _replace_then_sync)
    queue_path = tmp_path / "queue.json"

    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-14",
            "--source-report",
            str(source),
            "--queue-path",
            str(queue_path),
            "--report-dir",
            str(tmp_path / "reports"),
            "--approval-dir",
            str(tmp_path / "approvals"),
            "--apply-receipt-dir",
            str(tmp_path / "receipts"),
            "--write",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert result["status"] == "blocked_contract_error"
    assert result["reason"] == "source_artifact_changed_before_commit"
    assert not queue_path.exists()
    assert not (tmp_path / "reports").exists()


def test_source_candidate_list_requires_the_declared_intake_contract(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    payload = {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": "2026-08-14",
        "promotion_candidate_intake_contract": {
            "schema": mod.CANDIDATE_SCHEMA,
            "consumer": "src.engine.automation.machine_microstructure_policy_approval",
            "daily_report_runtime_effect": False,
        },
        "policy_promotion_candidates": [_candidate()],
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    source.write_text(json.dumps(payload), encoding="utf-8")

    _, candidates, status = mod._load_source_candidates(
        target_date=date(2026, 8, 14), source_report=source
    )
    assert status == "loaded"
    assert candidates == [_candidate()]

    payload["policy_promotion_candidates"].append("invalid-row")
    source.write_text(json.dumps(payload), encoding="utf-8")
    _, candidates, status = mod._load_source_candidates(
        target_date=date(2026, 8, 14), source_report=source
    )
    assert status == "candidate_rows_invalid"
    assert candidates == []


def test_legacy_queue_load_normalizes_separate_objective_ledger(tmp_path: Path) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    legacy = _empty(now)
    legacy.pop("objective_followups")
    path = tmp_path / "queue.json"
    path.write_text(json.dumps(legacy), encoding="utf-8")

    loaded = mod.load_queue(path)

    assert loaded["schema"] == mod.QUEUE_SCHEMA
    assert loaded["metric_contract"] == mod.METRIC_CONTRACT
    assert loaded["objective_followups"] == []


def test_persisted_queue_rejects_duplicate_objective_followup_ids(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, rejections = mod.sync_objective_followups(
        _empty(now),
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    queue["objective_followups"].append(dict(queue["objective_followups"][0]))
    path = tmp_path / "queue.json"
    path.write_text(json.dumps(queue), encoding="utf-8")

    assert rejections == []
    with pytest.raises(
        ValueError, match="approval_queue_objective_followup_contract_invalid"
    ):
        mod.load_queue(path)


@pytest.mark.parametrize(
    "mutation",
    ("nested_hash", "top_level_hash", "queue_key", "unknown_state", "duplicate"),
)
def test_persisted_queue_rejects_forged_candidate_identity(
    tmp_path: Path,
    mutation: str,
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, rejections = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    assert rejections == []
    row = queue["candidates"][0]
    if mutation == "nested_hash":
        row["candidate"]["candidate_sha256"] = "0" * 64
    elif mutation == "top_level_hash":
        row["candidate_sha256"] = "0" * 64
    elif mutation == "queue_key":
        row["queue_key"] = "forged:queue"
    elif mutation == "unknown_state":
        row["state"] = "APPLY_WITHOUT_REVIEW"
    else:
        queue["candidates"].append(dict(row))
    path = tmp_path / "queue.json"
    path.write_text(json.dumps(queue), encoding="utf-8")

    with pytest.raises(ValueError, match="approval_queue_candidate_contract_invalid"):
        mod.load_queue(path)


def test_persisted_queue_rejects_duplicate_json_key(tmp_path: Path) -> None:
    path = tmp_path / "queue.json"
    path.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")

    with pytest.raises(ValueError, match="json_generation_payload_invalid"):
        mod.load_queue(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_path", None),
        ("source_payload_sha256", "not-a-sha"),
        ("first_seen_at_kst", "not-a-time"),
        ("reminders", {"preopen": "2026-08-14"}),
    ],
)
def test_persisted_queue_rejects_invalid_objective_provenance(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(now),
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    queue["objective_followups"][0][field] = value
    path = tmp_path / "queue.json"
    path.write_text(json.dumps(queue), encoding="utf-8")

    with pytest.raises(
        ValueError, match="approval_queue_objective_followup_contract_invalid"
    ):
        mod.load_queue(path)


def test_source_context_loads_followup_and_rejects_authority_escalation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(_source_report_payload(objective_followups=[_objective_followup()])),
        encoding="utf-8",
    )

    (
        path,
        candidates,
        followups,
        status,
        objective_status,
        rejections,
    ) = mod._load_source_context(target_date=date(2026, 8, 14), source_report=source)

    assert path == source
    assert candidates == []
    assert followups == [_objective_followup()]
    assert status == "loaded"
    assert objective_status == "loaded"
    assert rejections == []

    source.write_text(json.dumps(_source_report_payload()), encoding="utf-8")
    (
        _,
        candidates,
        followups,
        status,
        objective_status,
        rejections,
    ) = mod._load_source_context(target_date=date(2026, 8, 14), source_report=source)
    assert candidates == []
    assert followups == []
    assert status == "loaded"
    assert objective_status == "objective_followup_list_missing_or_invalid"
    assert rejections == [
        {
            "followup_id": None,
            "errors": ["objective_followup_list_missing_or_invalid"],
        }
    ]

    escalated = _objective_followup()
    escalated["state"] = "ARBITRARY_RUNTIME_READY"
    escalated["followup_required"] = 1
    escalated["allowed_runtime_apply"] = True
    escalated["runtime_design"] = {"runtime_family": "forged"}
    escalated["metric_contract"]["decision_authority"] = "runtime_policy_selection"
    source.write_text(
        json.dumps(_source_report_payload(objective_followups=[escalated])),
        encoding="utf-8",
    )

    (
        _,
        candidates,
        followups,
        status,
        objective_status,
        rejections,
    ) = mod._load_source_context(target_date=date(2026, 8, 14), source_report=source)

    assert candidates == []
    assert followups == []
    assert status == "loaded"
    assert objective_status == "loaded"
    errors = rejections[0]["errors"]
    assert "objective_followup_state_invalid" in errors
    assert "objective_followup_required_not_boolean" in errors
    assert "objective_followup_metric_decision_authority_invalid" in errors
    assert "objective_followup_allowed_runtime_apply_invalid" in errors
    assert any(
        value.startswith("objective_followup_candidate_authority_fields_forbidden")
        for value in errors
    )
    report = mod.build_status_report(
        _empty(datetime(2026, 8, 14, 21, 15, tzinfo=KST)),
        phase="postclose",
        target_date=date(2026, 8, 14),
        source_path=source,
        source_status="loaded",
        intake_rejections=[],
        objective_followup_rejections=rejections,
        reminder_status="not_needed_or_duplicate",
    )
    assert report["decision"] == "objective_followup_contract_rejected"


@pytest.mark.parametrize(
    ("state", "followup_required"),
    [
        ("IMPLEMENTATION_REQUIRED", True),
        ("EVIDENCE_ACCUMULATING", True),
    ],
)
def test_objective_followup_accepts_only_producer_state_contract(
    state: str, followup_required: bool
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    row = _objective_followup(state=state, followup_required=followup_required)

    queue, rejections = mod.sync_objective_followups(
        _empty(now),
        source_followups=[row],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    assert rejections == []
    assert queue["objective_followups"][0]["state"] == state


def test_open_objective_cannot_preseed_candidate_handoff_binding() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    _, handoff_binding = _objective_bound_candidate()

    queue, rejections = mod.sync_objective_followups(
        _empty(now),
        source_followups=[
            _objective_followup(candidate_handoff_binding=handoff_binding)
        ],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    assert queue["objective_followups"] == []
    assert rejections[0]["errors"] == [
        "objective_followup_source_handoff_binding_forbidden"
    ]


def test_objective_followup_accepts_closed_states_only_with_queue_evidence(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    source_candidate, handoff_binding = _objective_bound_candidate()
    queued_candidate, candidate_rejections = mod.sync_queue(
        _empty(now),
        source_candidates=[source_candidate],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    accepted_keys = queued_candidate["last_sync"]["accepted_candidate_queue_keys"]
    handed_off, handoff_rejections = mod.sync_objective_followups(
        queued_candidate,
        source_followups=[
            _objective_followup(
                state="CANDIDATE_QUEUE_HANDOFF",
                followup_required=False,
                remaining_gap_codes=[],
                candidate_handoff_binding=handoff_binding,
            )
        ],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        accepted_candidate_queue_keys=accepted_keys,
        now=now,
    )

    assert candidate_rejections == []
    assert handoff_rejections == []
    assert handed_off["objective_followups"][0]["state"] == ("CANDIDATE_QUEUE_HANDOFF")
    persisted_handoff = handed_off["objective_followups"][0]["handoff_evidence"]
    assert persisted_handoff["accepted_candidate_queue_key"] == accepted_keys[0]
    assert persisted_handoff["accepted_candidate_sha256"] == (
        handed_off["candidates"][0]["candidate_sha256"]
    )
    assert persisted_handoff["verification"] == (
        "same_run_objective_bound_candidate_intake_accepted"
    )
    assert persisted_handoff["objective_followup_id"] == (
        mod.FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID
    )

    candidate = handed_off["candidates"][0]
    candidate["state"] = mod.STATE_POST_APPLY_ATTRIBUTED
    candidate.update(
        {
            "operator_decision_artifact": "approvals/decision.json",
            "operator_authorization_id": "operator-test",
            "operator_decision_at_kst": "2026-08-14T20:00:00+09:00",
            "operator_registry_entry_sha256": candidate[
                "runtime_registry_entry_sha256"
            ],
            "preopen_handoff": "handoffs/exact.json",
            "preopen_target_date": "2026-08-14",
            "authorization_mode": "first_explicit_operator_approval",
            "family_apply_receipt": "receipts/applied.json",
        }
    )
    candidate["post_apply_attribution_receipt"] = "receipts/attributed.json"
    producer_complete = _producer_complete_followup(now.date().isoformat())
    assert producer_complete["state"] == "COMPLETE"
    assert "completion_evidence" not in producer_complete
    completed, completion_rejections = mod.sync_objective_followups(
        handed_off,
        source_followups=[producer_complete],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    assert completion_rejections == []
    assert completed["objective_followups"][0]["state"] == "COMPLETE"
    persisted_completion = completed["objective_followups"][0]["completion_evidence"]
    assert persisted_completion["candidate_queue_key"] == candidate["queue_key"]
    assert persisted_completion["candidate_sha256"] == candidate["candidate_sha256"]
    assert persisted_completion["post_apply_attribution_receipt"] == (
        "receipts/attributed.json"
    )
    assert persisted_completion["causal_completion_verified"] is True
    assert persisted_completion["objective_followup_id"] == (
        mod.FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID
    )
    queue_path = tmp_path / "completed-queue.json"
    queue_path.write_text(json.dumps(completed), encoding="utf-8")
    assert mod.load_queue(queue_path)["objective_followups"][0]["state"] == ("COMPLETE")


def test_unrelated_accepted_candidate_cannot_close_objective_handoff() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, candidate_rejections = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    _, handoff_binding = _objective_bound_candidate()

    preserved, rejections = mod.sync_objective_followups(
        queue,
        source_followups=[
            _objective_followup(
                state="CANDIDATE_QUEUE_HANDOFF",
                followup_required=False,
                remaining_gap_codes=[],
                candidate_handoff_binding=handoff_binding,
            )
        ],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        accepted_candidate_queue_keys=(queue.get("last_sync") or {}).get(
            "accepted_candidate_queue_keys"
        )
        or [],
        now=now,
    )

    assert candidate_rejections == []
    assert rejections[0]["errors"] == [
        "objective_followup_bound_candidate_not_accepted_this_run"
    ]
    assert preserved["objective_followups"] == []


def test_non_handoff_gap_cannot_be_closed_by_bound_candidate() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    source_candidate, handoff_binding = _objective_bound_candidate(
        gap_codes=["post_apply_attribution_pending"]
    )
    queue, candidate_rejections = mod.sync_queue(
        _empty(now),
        source_candidates=[source_candidate],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )

    preserved, rejections = mod.sync_objective_followups(
        queue,
        source_followups=[
            _objective_followup(
                state="CANDIDATE_QUEUE_HANDOFF",
                followup_required=False,
                remaining_gap_codes=[],
                candidate_handoff_binding=handoff_binding,
            )
        ],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        accepted_candidate_queue_keys=(queue.get("last_sync") or {}).get(
            "accepted_candidate_queue_keys"
        )
        or [],
        now=now,
    )

    assert candidate_rejections == []
    assert "objective_followup_non_handoff_gap_transfer_forbidden" in (
        rejections[0]["errors"]
    )
    assert preserved["objective_followups"] == []


def test_objective_complete_without_prior_handoff_preserves_open_state() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    queue, _ = mod.sync_objective_followups(
        queue,
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    candidate = queue["candidates"][0]
    candidate["state"] = mod.STATE_POST_APPLY_ATTRIBUTED
    candidate["post_apply_attribution_receipt"] = "receipts/attributed.json"

    preserved, rejections = mod.sync_objective_followups(
        queue,
        source_followups=[_producer_complete_followup(now.date().isoformat())],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    assert rejections[0]["errors"] == [
        "complete_objective_followup_handoff_evidence_missing"
    ]
    assert preserved["objective_followups"][0]["state"] == ("IMPLEMENTATION_REQUIRED")


@pytest.mark.parametrize(
    ("candidate_state", "receipt", "expected_error"),
    [
        (
            mod.STATE_REVIEW_READY,
            None,
            "complete_objective_followup_candidate_not_post_apply_attributed",
        ),
        (
            mod.STATE_POST_APPLY_ATTRIBUTED,
            None,
            "complete_objective_followup_attribution_receipt_missing",
        ),
    ],
)
def test_objective_complete_requires_attributed_candidate_and_receipt(
    candidate_state: str,
    receipt: str | None,
    expected_error: str,
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue = _queue_with_objective_handoff(now)
    candidate = queue["candidates"][0]
    candidate["state"] = candidate_state
    candidate.pop("post_apply_attribution_receipt", None)
    if receipt is not None:
        candidate["post_apply_attribution_receipt"] = receipt

    preserved, rejections = mod.sync_objective_followups(
        queue,
        source_followups=[_producer_complete_followup(now.date().isoformat())],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    assert rejections[0]["errors"] == [expected_error]
    assert preserved["objective_followups"][0]["state"] == ("CANDIDATE_QUEUE_HANDOFF")


def test_objective_complete_rejects_ambiguous_handoff_candidate() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue = _queue_with_objective_handoff(now)
    queue["candidates"].append(dict(queue["candidates"][0]))

    with pytest.raises(
        ValueError, match="approval_queue_objective_followup_contract_invalid"
    ):
        mod.sync_objective_followups(
            queue,
            source_followups=[_producer_complete_followup(now.date().isoformat())],
            source_path=Path("source.json"),
            as_of_date=now.date(),
            source_status="loaded",
            now=now,
        )


def test_objective_followup_is_preserved_when_source_is_missing() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queued, rejections = mod.sync_objective_followups(
        _empty(now),
        source_followups=[_objective_followup()],
        source_path=Path("source-2026-08-14.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    carried, missing_rejections = mod.sync_objective_followups(
        queued,
        source_followups=[],
        source_path=Path("missing-2026-08-18.json"),
        as_of_date=date(2026, 8, 18),
        source_status="missing_or_unreadable",
        now=datetime(2026, 8, 18, 21, 15, tzinfo=KST),
    )

    assert rejections == []
    assert missing_rejections == []
    assert carried["objective_followups"] == queued["objective_followups"]
    assert carried["objective_followups"][0]["followup_required"] is True


def test_postclose_combines_candidate_and_objective_reminder_once_per_trading_day() -> (
    None
):
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    queue, _ = mod.sync_objective_followups(
        queue,
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    preopen_sent: list[str] = []
    _, preopen_status = mod.notify_pending(
        queue,
        phase="preopen",
        target_date=now.date(),
        include_objective_followups=True,
        now=now,
        config_loader=lambda: ("token", "admin"),
        sender=lambda _token, _admin, message: preopen_sent.append(message),
    )
    sent: list[str] = []
    notified, status = mod.notify_pending(
        queue,
        phase="postclose",
        target_date=now.date(),
        include_objective_followups=True,
        now=now,
        config_loader=lambda: ("token", "admin"),
        sender=lambda _token, _admin, message: sent.append(message),
    )
    duplicate, duplicate_status = mod.notify_pending(
        notified,
        phase="postclose",
        target_date=now.date(),
        include_objective_followups=True,
        now=now,
        config_loader=lambda: ("token", "admin"),
        sender=lambda _token, _admin, message: sent.append(message),
    )
    next_day, next_status = mod.notify_pending(
        duplicate,
        phase="postclose",
        target_date=date(2026, 8, 18),
        include_objective_followups=True,
        now=datetime(2026, 8, 18, 21, 15, tzinfo=KST),
        config_loader=lambda: ("token", "admin"),
        sender=lambda _token, _admin, message: sent.append(message),
    )

    assert preopen_status == "sent"
    assert "[빠른 회전 목표 후속]" not in preopen_sent[0]
    assert status == "sent"
    assert duplicate_status == "not_needed_or_duplicate"
    assert next_status == "sent"
    assert len(sent) == 2
    assert "[빠른 회전 목표 후속]" in sent[0]
    assert "[정책 후보 승인 대기]" in sent[0]
    assert "정책·주문을 변경하지 않고" in sent[0]
    assert next_day["objective_followups"][0]["reminders"]["postclose"] == "2026-08-18"


@pytest.mark.parametrize(
    ("target_date", "generated_at", "include_objective_followups"),
    [
        (date(2026, 8, 14), datetime(2026, 8, 14, 21, 15, tzinfo=KST), False),
        (date(2026, 8, 14), datetime(2026, 8, 14, 20, 10, tzinfo=KST), True),
        (
            date(2026, 8, 14),
            datetime(2026, 8, 14, 21, 14, 59, tzinfo=KST),
            True,
        ),
        (date(2026, 8, 14), datetime(2026, 8, 18, 21, 15, tzinfo=KST), True),
        (date(2026, 8, 18), datetime(2026, 8, 14, 21, 15, tzinfo=KST), True),
        (date(2026, 8, 15), datetime(2026, 8, 15, 21, 15, tzinfo=KST), True),
    ],
)
def test_objective_reminder_requires_explicit_exact_date_2115_trading_day_opt_in(
    target_date: date,
    generated_at: datetime,
    include_objective_followups: bool,
) -> None:
    source_now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(source_now),
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=source_now.date(),
        source_status="loaded",
        now=source_now,
    )
    sent: list[str] = []

    notified, status = mod.notify_pending(
        queue,
        phase="postclose",
        target_date=target_date,
        include_objective_followups=include_objective_followups,
        now=generated_at,
        config_loader=lambda: ("token", "admin"),
        sender=lambda _token, _admin, message: sent.append(message),
    )

    assert status == "not_needed_or_duplicate"
    assert sent == []
    assert notified["objective_followups"][0]["reminders"] == {}


def test_objective_reminder_sends_at_exact_opted_in_window() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(now),
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    sent: list[str] = []

    notified, status = mod.notify_pending(
        queue,
        phase="postclose",
        target_date=now.date(),
        include_objective_followups=True,
        now=now,
        config_loader=lambda: ("token", "admin"),
        sender=lambda _token, _admin, message: sent.append(message),
    )

    assert status == "sent"
    assert len(sent) == 1
    assert "[빠른 회전 목표 후속]" in sent[0]
    assert notified["objective_followups"][0]["reminders"]["postclose"] == (
        "2026-08-14"
    )


def test_objective_followup_status_and_markdown_remain_non_runtime() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(now),
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )
    report = mod.build_status_report(
        queue,
        phase="postclose",
        target_date=now.date(),
        source_path=Path("source.json"),
        source_status="loaded",
        objective_followup_source_status="loaded",
        intake_rejections=[],
        reminder_status="sent",
        now=now,
    )
    markdown = mod.render_status_markdown(report)

    assert report["decision"] == "objective_followup_required"
    assert report["summary"]["actionable_candidate_count"] == 0
    assert report["summary"]["actionable_objective_followup_count"] == 1
    assert "objective_followups" in report
    row = report["objective_followups"][0]
    assert row["followup_required"] is True
    assert row["operator_decision_required"] is False
    assert row["allowed_runtime_apply"] is False
    assert row["broker_order_forbidden"] is True
    assert row["authority"] == {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    assert "Fast Lifecycle Objective Follow-up" in markdown
    assert "implement_source_only_rolling_paired_policy_research" in markdown
    assert "cannot be approved, scheduled, enrolled, or applied" in markdown


def test_objective_followup_cannot_enter_decision_handoff_or_family_enrollment(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(now),
        source_followups=[_objective_followup()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    with pytest.raises(ValueError, match="candidate_id_and_hash_not_uniquely_found"):
        mod.record_operator_decision(
            queue,
            candidate_id="machine_lifecycle_turnover_policy_research_v1",
            expected_candidate_sha256="a" * 64,
            decision="approve",
            operator_authorization_id="operator-explicit",
            operator_instruction="attempted followup approval",
            approval_dir=tmp_path / "approvals",
            apply_receipt_dir=tmp_path / "receipts",
            now=now,
        )

    scheduled, handoffs = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )
    reconciled, _ = mod.sync_queue(
        scheduled,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 18),
        source_status="not_provided",
        now=datetime(2026, 8, 18, 7, 41, tzinfo=KST),
        apply_receipt_dir=tmp_path / "receipts",
    )

    assert handoffs == []
    assert reconciled["candidates"] == []
    assert reconciled["family_enrollments"] == {}
    assert len(reconciled["objective_followups"]) == 1
    assert not (tmp_path / "handoffs").exists()


def test_postclose_loads_objective_when_candidate_intake_contract_is_invalid(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _source_report_payload(objective_followups=[_objective_followup()])
    payload["promotion_candidate_intake_contract"]["schema"] = "invalid"
    source = tmp_path / "source.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    queue_path = tmp_path / "queue.json"

    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-14",
            "--source-report",
            str(source),
            "--queue-path",
            str(queue_path),
            "--report-dir",
            str(tmp_path / "reports"),
            "--approval-dir",
            str(tmp_path / "approvals"),
            "--apply-receipt-dir",
            str(tmp_path / "receipts"),
            "--write",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["source_status"] == "intake_contract_invalid"
    assert report["objective_followup_source_status"] == "loaded"
    assert report["decision"] == "objective_followup_required"
    assert report["summary"]["actionable_objective_followup_count"] == 1
    assert report["objective_followups"][0]["followup_required"] is True
    assert report["objective_followups"][0]["authority"] == {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    assert queue["candidates"] == []
    assert queue["objective_followups"][0]["followup_required"] is True
    assert queue["objective_followup_last_sync"]["source_status"] == "loaded"


@pytest.mark.parametrize(
    ("extra_args", "reason"),
    [
        (["--notify"], "notify_requires_write"),
        (
            ["--write", "--notify-objective-followups"],
            "notify_objective_followups_requires_notify",
        ),
    ],
)
def test_notification_cli_flags_fail_closed(
    capsys: pytest.CaptureFixture[str],
    extra_args: list[str],
    reason: str,
) -> None:
    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-14",
            *extra_args,
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert output["status"] == "blocked_contract_error"
    assert output["reason"] == reason


def test_missing_queue_and_source_fails_visibly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    queue_path = tmp_path / "missing" / "queue.json"
    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-14",
            "--source-report",
            str(tmp_path / "missing-source.json"),
            "--queue-path",
            str(queue_path),
            "--report-dir",
            str(tmp_path / "reports"),
            "--write",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert output["status"] == "blocked_contract_error"
    assert output["reason"] == "approval_queue_and_source_unavailable"
    assert not queue_path.exists()


def test_future_postclose_target_fails_before_queue_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    generated = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(generated),
        source_followups=[_objective_followup()],
        source_path=Path("source-2026-08-14.json"),
        as_of_date=generated.date(),
        source_status="loaded",
        now=generated,
    )
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue, sort_keys=True), encoding="utf-8")
    before = queue_path.read_bytes()
    payload = _source_report_payload(
        objective_followups=[_objective_followup(source_date="2026-08-18")]
    )
    payload["target_date"] = "2026-08-18"
    source = tmp_path / "source-2026-08-18.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(mod, "_now_kst", lambda now=None: generated)

    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-18",
            "--source-report",
            str(source),
            "--queue-path",
            str(queue_path),
            "--report-dir",
            str(tmp_path / "reports"),
            "--write",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert output["reason"] == "postclose_target_date_in_future"
    assert queue_path.read_bytes() == before
    assert not (tmp_path / "reports").exists()


@pytest.mark.parametrize("failure_status", ["missing_config", "send_failed"])
def test_objective_notification_delivery_failure_is_nonzero_and_durable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure_status: str,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(_source_report_payload(objective_followups=[_objective_followup()])),
        encoding="utf-8",
    )
    queue_path = tmp_path / "queue.json"
    report_dir = tmp_path / "reports"
    generated = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    monkeypatch.setattr(mod, "_now_kst", lambda now=None: generated)
    if failure_status == "missing_config":
        monkeypatch.setattr(mod, "_load_telegram_config", lambda: (None, None))
    else:
        monkeypatch.setattr(mod, "_load_telegram_config", lambda: ("token", "admin"))

        def _raise_send(_token: str, _admin: str, _message: str) -> None:
            raise RuntimeError("telegram unavailable")

        monkeypatch.setattr(mod, "_send_telegram", _raise_send)

    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-14",
            "--source-report",
            str(source),
            "--queue-path",
            str(queue_path),
            "--report-dir",
            str(report_dir),
            "--approval-dir",
            str(tmp_path / "approvals"),
            "--apply-receipt-dir",
            str(tmp_path / "receipts"),
            "--write",
            "--notify",
            "--notify-objective-followups",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    persisted = json.loads(queue_path.read_text(encoding="utf-8"))
    written_report = json.loads(
        (
            report_dir
            / "machine_microstructure_policy_approval_postclose_2026-08-14.json"
        ).read_text(encoding="utf-8")
    )
    assert exit_code == 3
    assert report["summary"]["reminder_status"] == failure_status
    assert written_report["summary"]["reminder_status"] == failure_status
    assert persisted["objective_followups"][0]["reminders"] == {}


def test_rejected_candidate_cannot_close_objective_handoff_and_open_state_persists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_seen = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, rejections = mod.sync_objective_followups(
        _empty(first_seen),
        source_followups=[_objective_followup()],
        source_path=Path("source-2026-08-14.json"),
        as_of_date=first_seen.date(),
        source_status="loaded",
        now=first_seen,
    )
    assert rejections == []
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue), encoding="utf-8")

    rejected_candidate, handoff_binding = _objective_bound_candidate(
        source_date="2026-08-18"
    )
    rejected_candidate["evidence"]["observed_trading_days"] = 4
    handoff_binding["candidate_sha256"] = mod.candidate_sha256(rejected_candidate)
    handoff = _objective_followup(
        source_date="2026-08-18",
        state="CANDIDATE_QUEUE_HANDOFF",
        followup_required=False,
        remaining_gap_codes=[],
        candidate_handoff_binding=handoff_binding,
    )
    payload = _source_report_payload(objective_followups=[handoff])
    payload["target_date"] = "2026-08-18"
    payload["policy_promotion_candidates"] = [rejected_candidate]
    source = tmp_path / "source-2026-08-18.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        mod,
        "_now_kst",
        lambda now=None: datetime(2026, 8, 18, 21, 15, tzinfo=KST),
    )

    exit_code = mod.main(
        [
            "--phase",
            "postclose",
            "--target-date",
            "2026-08-18",
            "--source-report",
            str(source),
            "--queue-path",
            str(queue_path),
            "--report-dir",
            str(tmp_path / "reports"),
            "--approval-dir",
            str(tmp_path / "approvals"),
            "--apply-receipt-dir",
            str(tmp_path / "receipts"),
            "--write",
        ]
    )

    report = json.loads(capsys.readouterr().out)
    persisted = json.loads(queue_path.read_text(encoding="utf-8"))
    errors = report["objective_followup_rejections"][0]["errors"]
    assert exit_code == 0
    assert report["summary"]["intake_rejection_count"] == 1
    assert report["summary"]["objective_followup_rejection_count"] == 1
    assert "objective_followup_candidate_handoff_not_accepted_this_run" in errors
    assert persisted["last_sync"]["accepted_candidate_count"] == 0
    assert persisted["objective_followups"][0]["state"] == ("IMPLEMENTATION_REQUIRED")
    assert persisted["objective_followups"][0]["source_date"] == "2026-08-14"
    assert persisted["objective_followups"][0]["followup_required"] is True


def test_objective_source_date_and_state_updates_are_monotonic_trading_day_only() -> (
    None
):
    first_seen = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue, _ = mod.sync_objective_followups(
        _empty(first_seen),
        source_followups=[_objective_followup()],
        source_path=Path("source-2026-08-14.json"),
        as_of_date=first_seen.date(),
        source_status="loaded",
        now=first_seen,
    )
    evidence_date = date(2026, 8, 18)
    queue, forward_rejections = mod.sync_objective_followups(
        queue,
        source_followups=[
            _objective_followup(
                source_date=evidence_date.isoformat(),
                state="EVIDENCE_ACCUMULATING",
            )
        ],
        source_path=Path("source-2026-08-18.json"),
        as_of_date=evidence_date,
        source_status="loaded",
        now=datetime(2026, 8, 18, 21, 15, tzinfo=KST),
    )
    stale, stale_rejections = mod.sync_objective_followups(
        queue,
        source_followups=[_objective_followup()],
        source_path=Path("stale-2026-08-14.json"),
        as_of_date=first_seen.date(),
        source_status="loaded",
        now=datetime(2026, 8, 18, 21, 16, tzinfo=KST),
    )
    regressed, transition_rejections = mod.sync_objective_followups(
        queue,
        source_followups=[_objective_followup(source_date="2026-08-19")],
        source_path=Path("regressed-2026-08-19.json"),
        as_of_date=date(2026, 8, 19),
        source_status="loaded",
        now=datetime(2026, 8, 19, 21, 15, tzinfo=KST),
    )
    weekend, weekend_rejections = mod.sync_objective_followups(
        queue,
        source_followups=[
            _objective_followup(source_date="2026-08-22", state="EVIDENCE_ACCUMULATING")
        ],
        source_path=Path("weekend-2026-08-22.json"),
        as_of_date=date(2026, 8, 22),
        source_status="loaded",
        now=datetime(2026, 8, 22, 21, 15, tzinfo=KST),
    )

    assert forward_rejections == []
    assert "objective_followup_source_date_regression" in stale_rejections[0]["errors"]
    assert any(
        value.startswith("objective_followup_state_transition_forbidden:")
        for value in transition_rejections[0]["errors"]
    )
    assert "objective_followup_source_date_not_krx_trading_day" in (
        weekend_rejections[0]["errors"]
    )
    for rejected_queue in (stale, regressed, weekend):
        assert rejected_queue["objective_followups"][0]["source_date"] == ("2026-08-18")
        assert rejected_queue["objective_followups"][0]["state"] == (
            "EVIDENCE_ACCUMULATING"
        )


def test_objective_complete_source_cannot_inject_attribution_receipt() -> None:
    now = datetime(2026, 8, 14, 21, 15, tzinfo=KST)
    queue = _queue_with_objective_handoff(now)
    candidate = queue["candidates"][0]
    candidate["state"] = mod.STATE_POST_APPLY_ATTRIBUTED
    candidate["post_apply_attribution_receipt"] = "receipts/real.json"
    completion_evidence = {
        "candidate_queue_key": candidate["queue_key"],
        "candidate_sha256": candidate["candidate_sha256"],
        "candidate_state": mod.STATE_POST_APPLY_ATTRIBUTED,
        "post_apply_attribution_receipt": "receipts/spoofed.json",
        "causal_completion_verified": True,
    }

    preserved, rejections = mod.sync_objective_followups(
        queue,
        source_followups=[
            _objective_followup(
                state="COMPLETE",
                followup_required=False,
                remaining_gap_codes=[],
                completion_evidence=completion_evidence,
            )
        ],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
    )

    assert rejections[0]["errors"] == [
        "complete_objective_followup_source_completion_evidence_forbidden"
    ]
    assert preserved["objective_followups"][0]["state"] == ("CANDIDATE_QUEUE_HANDOFF")


def test_design_required_candidate_cannot_be_approved(tmp_path: Path) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate(registered=False)],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    entry = queue["candidates"][0]

    with pytest.raises(ValueError, match="candidate_not_approval_ready"):
        mod.record_operator_decision(
            queue,
            candidate_id=entry["candidate_id"],
            expected_candidate_sha256=entry["candidate_sha256"],
            decision="approve",
            operator_authorization_id="operator-explicit",
            operator_instruction="approve",
            approval_dir=tmp_path,
            now=now,
        )


def test_reminder_is_once_per_phase_and_date() -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    sent: list[tuple[str, str, str]] = []
    notified, status = mod.notify_pending(
        queue,
        phase="postclose",
        target_date=now.date(),
        config_loader=lambda: ("token", "admin"),
        sender=lambda token, admin, message: sent.append((token, admin, message)),
    )
    duplicate, duplicate_status = mod.notify_pending(
        notified,
        phase="postclose",
        target_date=now.date(),
        config_loader=lambda: ("token", "admin"),
        sender=lambda token, admin, message: sent.append((token, admin, message)),
    )

    assert status == "sent"
    assert duplicate_status == "not_needed_or_duplicate"
    assert len(sent) == 1
    assert "후속 확인" in sent[0][2]
    assert duplicate["candidates"][0]["reminders"]["postclose"] == "2026-08-14"


def test_guarded_family_receipt_enrolls_only_same_bounded_contract(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve first bounded family for next PREOPEN only.",
        approval_dir=tmp_path / "approvals",
        now=now,
    )
    queue, handoffs = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )
    entry = queue["candidates"][0]
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    (receipt_dir / "applied.json").write_text(
        json.dumps(
            {
                "schema": mod.APPLY_RECEIPT_SCHEMA,
                "queue_key": entry["queue_key"],
                "candidate_sha256": entry["candidate_sha256"],
                "runtime_family": "widget_micro_entry_confirmation_v1",
                "stage": "entry",
                "axis": "micro_confirmation_threshold",
                "bounded_contract_sha256": "b" * 64,
                "runtime_registry_entry_sha256": entry["runtime_registry_entry_sha256"],
                "preopen_handoff": str(handoffs[0]),
                "target_date": "2026-08-18",
                "status": "applied_guard_passed",
                "receipt_owner": "widget_micro_entry_policy_apply",
                "applied_at_kst": "2026-08-18T07:45:00+09:00",
                "runtime_effect": True,
                "runtime_apply_performed": True,
                "actual_order_submitted": False,
                "same_stage_owner_conflict_free": True,
                "hard_safety_and_broker_guards_preserved": True,
            }
        ),
        encoding="utf-8",
    )
    applied, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 18),
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )

    assert applied["candidates"][0]["state"] == mod.STATE_APPLIED
    assert (
        applied["family_enrollments"]["widget_micro_entry_confirmation_v1"][
            "enrolled_after_guarded_apply"
        ]
        is True
    )

    decision_candidate = _candidate(
        candidate_id="widget:000660:entry:micro_axis:manual-hold",
        source_date="2026-08-18",
    )
    decision_queue, _ = mod.sync_queue(
        applied,
        source_candidates=[decision_candidate],
        source_path=Path("decision.json"),
        as_of_date=date(2026, 8, 18),
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )
    decision_entry = next(
        row
        for row in decision_queue["candidates"]
        if row["candidate_id"] == decision_candidate["candidate_id"]
    )
    decision_queue, _ = mod.record_operator_decision(
        decision_queue,
        candidate_id=decision_entry["candidate_id"],
        expected_candidate_sha256=decision_entry["candidate_sha256"],
        decision="hold",
        operator_authorization_id="operator-hold-20260818",
        operator_instruction="Hold the unrelated candidate for more evidence.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=receipt_dir,
        now=datetime(2026, 8, 18, 20, 31, tzinfo=KST),
    )
    assert "widget_micro_entry_confirmation_v1" in decision_queue["family_enrollments"]

    subsequent = _candidate(
        candidate_id="widget:005930:entry:micro_axis:v2",
        recommended_value=0.27,
        first_approval=False,
        source_date="2026-08-18",
    )
    auto, _ = mod.sync_queue(
        decision_queue,
        source_candidates=[subsequent],
        source_path=Path("next.json"),
        as_of_date=date(2026, 8, 18),
        now=datetime(2026, 8, 18, 20, 30, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )
    latest = next(
        row for row in auto["candidates"] if row["candidate_id"].endswith(":v2")
    )
    assert latest["state"] == mod.STATE_AUTO_CHAIN_ELIGIBLE
    auto_scheduled, auto_handoffs = mod.schedule_preopen_handoffs(
        auto,
        target_date=date(2026, 8, 19),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 19, 7, 40, tzinfo=KST),
    )
    auto_latest = next(
        row
        for row in auto_scheduled["candidates"]
        if row["candidate_id"].endswith(":v2")
    )
    auto_handoff = next(path for path in auto_handoffs if "micro_axis_v2" in path.name)
    auto_payload = json.loads(auto_handoff.read_text(encoding="utf-8"))
    assert auto_latest["state"] == mod.STATE_PREOPEN_SCHEDULED
    assert (
        auto_payload["authorization_mode"] == "enrolled_same_bounded_family_auto_chain"
    )
    assert auto_payload["operator_decision_artifact"] is None

    post_apply_payload = {
        "schema": mod.APPLY_RECEIPT_SCHEMA,
        "queue_key": entry["queue_key"],
        "candidate_sha256": entry["candidate_sha256"],
        "runtime_family": "widget_micro_entry_confirmation_v1",
        "stage": "entry",
        "axis": "micro_confirmation_threshold",
        "bounded_contract_sha256": "b" * 64,
        "runtime_registry_entry_sha256": entry["runtime_registry_entry_sha256"],
        "preopen_handoff": str(handoffs[0]),
        "target_date": "2026-08-18",
        "status": "post_apply_attribution_complete",
        "receipt_owner": "widget_micro_entry_policy_attribution",
        "attributed_at_kst": "2026-09-02T20:30:00+09:00",
        "runtime_effect": False,
        "runtime_apply_performed": False,
        "actual_order_submitted": False,
        "post_apply_attribution_complete": True,
        "source_apply_receipt": str(receipt_dir / "applied.json"),
        "same_stage_owner_conflict_free": True,
        "hard_safety_and_broker_guards_preserved": True,
    }
    post_apply_path = receipt_dir / "post_apply.json"
    post_apply_path.write_text(json.dumps(post_apply_payload), encoding="utf-8")
    future_blocked, _ = mod.sync_queue(
        auto_scheduled,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 9, 1),
        now=datetime(2026, 9, 1, 20, 30, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )
    original = next(
        row
        for row in future_blocked["candidates"]
        if row["queue_key"] == entry["queue_key"]
    )
    assert original["state"] == mod.STATE_APPLIED

    post_apply_payload["attributed_at_kst"] = "2026-08-19T20:30:00+09:00"
    post_apply_path.write_text(json.dumps(post_apply_payload), encoding="utf-8")
    attributed, _ = mod.sync_queue(
        future_blocked,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 9, 1),
        now=datetime(2026, 9, 1, 20, 31, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )
    original = next(
        row
        for row in attributed["candidates"]
        if row["queue_key"] == entry["queue_key"]
    )
    assert original["state"] == mod.STATE_POST_APPLY_ATTRIBUTED
    assert "widget_micro_entry_confirmation_v1" in attributed["family_enrollments"]


def test_exact_date_handoff_does_not_roll_to_next_session(tmp_path: Path) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve one exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        now=now,
    )
    scheduled, first = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )

    missed, _ = mod.sync_queue(
        scheduled,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 19),
        now=datetime(2026, 8, 19, 7, 40, tzinfo=KST),
        apply_receipt_dir=tmp_path / "receipts",
    )
    unchanged, second = mod.schedule_preopen_handoffs(
        missed,
        target_date=date(2026, 8, 19),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 19, 7, 41, tzinfo=KST),
    )

    assert len(first) == 1
    assert second == []
    missed_entry = unchanged["candidates"][0]
    assert missed_entry["state"] == mod.STATE_PREOPEN_MISSED_REVIEW_REQUIRED
    assert missed_entry["missed_preopen_handoffs"][0]["target_date"] == ("2026-08-18")
    assert "preopen_target_date" not in missed_entry

    reapproved, _ = mod.record_operator_decision(
        unchanged,
        candidate_id=missed_entry["candidate_id"],
        expected_candidate_sha256=missed_entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260819",
        operator_instruction="Re-arm one new exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=datetime(2026, 8, 19, 7, 42, tzinfo=KST),
    )
    rescheduled, replacement = mod.schedule_preopen_handoffs(
        reapproved,
        target_date=date(2026, 8, 19),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 19, 7, 43, tzinfo=KST),
    )
    assert len(replacement) == 1
    assert rescheduled["candidates"][0]["preopen_target_date"] == "2026-08-19"


@pytest.mark.parametrize(
    ("generated_at", "target_date", "error"),
    [
        (
            datetime(2026, 8, 18, 8, 40, tzinfo=KST),
            date(2026, 8, 19),
            "preopen_handoff_target_date_not_generated_kst_date",
        ),
        (
            datetime(2026, 8, 19, 8, 40, tzinfo=KST),
            date(2026, 8, 18),
            "preopen_handoff_target_date_not_generated_kst_date",
        ),
        (
            datetime(2026, 8, 15, 8, 40, tzinfo=KST),
            date(2026, 8, 15),
            "preopen_handoff_target_date_not_krx_trading_day",
        ),
        (
            datetime(2026, 8, 18, 8, 30, tzinfo=KST),
            date(2026, 8, 18),
            "preopen_handoff_generated_at_or_after_market_open_cutoff",
        ),
    ],
)
def test_preopen_handoff_api_rejects_bad_dates_and_after_market_open(
    tmp_path: Path,
    generated_at: datetime,
    target_date: date,
    error: str,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-date-guard",
        operator_instruction="Approve only an exact-date trading-day handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )

    with pytest.raises(ValueError, match=error):
        mod.schedule_preopen_handoffs(
            queue,
            target_date=target_date,
            handoff_dir=tmp_path / "handoffs",
            now=generated_at,
        )

    assert not list((tmp_path / "handoffs").rglob("*.json"))


@pytest.mark.parametrize(
    ("generated_at", "target_date", "error"),
    [
        (
            datetime(2026, 8, 18, 8, 40, tzinfo=KST),
            "2026-08-19",
            "preopen_handoff_target_date_not_generated_kst_date",
        ),
        (
            datetime(2026, 8, 19, 8, 40, tzinfo=KST),
            "2026-08-18",
            "preopen_handoff_target_date_not_generated_kst_date",
        ),
        (
            datetime(2026, 8, 15, 8, 40, tzinfo=KST),
            "2026-08-15",
            "preopen_handoff_target_date_not_krx_trading_day",
        ),
        (
            datetime(2026, 8, 18, 23, 0, tzinfo=KST),
            "2026-08-18",
            "preopen_handoff_generated_at_or_after_market_open_cutoff",
        ),
    ],
)
def test_preopen_handoff_cli_rejects_bad_dates_and_after_market_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    generated_at: datetime,
    target_date: str,
    error: str,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-cli-date-guard",
        operator_instruction="Approve only an exact-date trading-day handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue), encoding="utf-8")
    monkeypatch.setattr(mod, "_now_kst", lambda now=None: generated_at)

    exit_code = mod.main(
        [
            "--phase",
            "preopen",
            "--target-date",
            target_date,
            "--queue-path",
            str(queue_path),
            "--approval-dir",
            str(tmp_path / "empty-approvals"),
            "--handoff-dir",
            str(tmp_path / "handoffs"),
            "--apply-receipt-dir",
            str(tmp_path / "receipts"),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert output["status"] == "blocked_contract_error"
    assert output["reason"] == error
    assert not list((tmp_path / "handoffs").rglob("*.json"))


def test_same_second_redecision_is_newer_than_handoff_invalidation(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve one exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    queue, _ = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )
    missed_at = datetime(2026, 8, 19, 8, 40, tzinfo=KST)
    missed, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=missed_at.date(),
        now=missed_at,
        apply_receipt_dir=tmp_path / "receipts",
    )
    invalidated_at = mod._aware_datetime(
        missed["candidates"][0]["operator_decision_invalidated_at_kst"]
    )
    archived_path = Path(
        missed["candidates"][0]["invalidated_operator_decision_artifacts"][0]
    )
    archived_before_reapproval = json.loads(archived_path.read_text(encoding="utf-8"))
    assert (
        archived_before_reapproval["operator_decision_artifact"][
            "operator_authorization_id"
        ]
        == "operator-explicit-20260814"
    )

    reapproved, artifact_path = mod.record_operator_decision(
        missed,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-same-second",
        operator_instruction="Re-arm after reviewing the missed handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=missed_at,
    )

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    archived_after_reapproval = json.loads(archived_path.read_text(encoding="utf-8"))
    assert reapproved["candidates"][0]["state"] == mod.STATE_USER_APPROVED
    assert mod._aware_datetime(artifact["decided_at_kst"]) > invalidated_at
    assert artifact["operator_authorization_id"] == "operator-explicit-same-second"
    assert archived_after_reapproval == archived_before_reapproval


def test_approval_artifact_seen_during_revalidation_cannot_apply_later(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    withdrawn_at = datetime(2026, 8, 14, 20, 31, tzinfo=KST)
    withdrawn, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=Path("fresh-empty-source.json"),
        as_of_date=withdrawn_at.date(),
        source_status="loaded",
        now=withdrawn_at,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = withdrawn["candidates"][0]
    assert entry["state"] == mod.STATE_REVALIDATION_REQUIRED
    invalidated_at = entry["operator_decision_invalidated_at_kst"]
    registry_digest = mod._registry_entry_sha256(
        _runtime_registry()["widget_micro_entry_confirmation_v1"]
    )
    artifact = {
        "schema": mod.APPROVAL_SCHEMA,
        "queue_key": entry["queue_key"],
        "candidate_id": entry["candidate_id"],
        "candidate_sha256": entry["candidate_sha256"],
        "source_date": entry["source_date"],
        "decision": "approve",
        "decided_at_kst": "2026-08-14T20:31:30.000000+09:00",
        "operator_authorization_id": "operator-invalid-state-injection",
        "operator_instruction": "Approve while source revalidation is unresolved.",
        "runtime_family": "widget_micro_entry_confirmation_v1",
        "runtime_registry_entry_sha256": registry_digest,
        "runtime_effect": False,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "_artifact_path": str(tmp_path / "approvals" / "injected.json"),
    }

    ignored, _ = mod.sync_queue(
        withdrawn,
        source_candidates=[],
        source_path=None,
        as_of_date=withdrawn_at.date(),
        now=datetime(2026, 8, 14, 20, 31, 31, tzinfo=KST),
        approval_artifacts=[artifact],
        apply_receipt_dir=tmp_path / "receipts",
    )
    ignored_entry = ignored["candidates"][0]
    assert ignored_entry["state"] == mod.STATE_REVALIDATION_REQUIRED
    assert ignored_entry["operator_decision_invalidated_at_kst"] == invalidated_at
    assert "operator_decision_artifact" not in ignored_entry
    assert "operator_authorization_id" not in ignored_entry

    revalidated_at = datetime(2026, 8, 14, 20, 32, tzinfo=KST)
    revalidated, _ = mod.sync_queue(
        ignored,
        source_candidates=[_candidate()],
        source_path=Path("fresh-source.json"),
        as_of_date=revalidated_at.date(),
        source_status="loaded",
        now=revalidated_at,
        approval_artifacts=[artifact],
        apply_receipt_dir=tmp_path / "receipts",
    )
    revalidated_entry = revalidated["candidates"][0]
    assert revalidated_entry["state"] == mod.STATE_REVIEW_READY
    assert revalidated_entry["operator_decision_invalidation_reason"] == (
        "fresh_source_candidate_revalidated_new_decision_required"
    )
    assert "operator_decision_artifact" not in revalidated_entry
    assert "operator_authorization_id" not in revalidated_entry


def test_approval_with_invalid_runtime_design_records_no_operator_provenance(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    artifact = {
        "schema": mod.APPROVAL_SCHEMA,
        "queue_key": entry["queue_key"],
        "candidate_id": entry["candidate_id"],
        "candidate_sha256": entry["candidate_sha256"],
        "source_date": entry["source_date"],
        "decision": "approve",
        "decided_at_kst": "2026-08-14T20:31:00.000000+09:00",
        "operator_authorization_id": "operator-no-registry",
        "operator_instruction": "This must not survive a missing trusted registry.",
        "runtime_family": "widget_micro_entry_confirmation_v1",
        "runtime_registry_entry_sha256": "",
        "runtime_effect": False,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "_artifact_path": str(tmp_path / "approvals" / "invalid-design.json"),
    }

    blocked, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=now.date(),
        now=datetime(2026, 8, 14, 20, 31, tzinfo=KST),
        approval_artifacts=[artifact],
        apply_receipt_dir=tmp_path / "receipts",
        runtime_registry={},
    )

    blocked_entry = blocked["candidates"][0]
    assert blocked_entry["state"] == mod.STATE_DESIGN_REQUIRED
    assert blocked_entry["state_reason"] == "approval_ignored_runtime_design_not_ready"
    assert "operator_decision_artifact" not in blocked_entry
    assert "operator_decision_at_kst" not in blocked_entry
    assert "operator_authorization_id" not in blocked_entry


def test_record_decision_does_not_report_success_if_final_state_loses_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    original_sync_queue = mod.sync_queue
    calls = 0

    def raced_sync_queue(*args, **kwargs):
        nonlocal calls
        calls += 1
        updated, rejections = original_sync_queue(*args, **kwargs)
        if calls == 2:
            raced_entry = updated["candidates"][0]
            raced_entry["state"] = mod.STATE_APPLIED
            for field in (
                "operator_decision_artifact",
                "operator_decision_at_kst",
                "operator_authorization_id",
            ):
                raced_entry.pop(field, None)
        return updated, rejections

    monkeypatch.setattr(mod, "sync_queue", raced_sync_queue)
    with pytest.raises(
        ValueError, match="operator_decision_not_applied_after_receipt_reconciliation"
    ):
        mod.record_operator_decision(
            queue,
            candidate_id=entry["candidate_id"],
            expected_candidate_sha256=entry["candidate_sha256"],
            decision="approve",
            operator_authorization_id="operator-race-loser",
            operator_instruction="Do not claim success after a state race.",
            approval_dir=tmp_path / "approvals",
            apply_receipt_dir=tmp_path / "receipts",
            now=now,
        )

    assert calls == 2
    assert not list((tmp_path / "approvals").glob("*.json"))


def test_archive_write_failure_preserves_inline_immutable_decision_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, artifact_path = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-original-evidence",
        operator_instruction="Approve the original exact-date handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    queue, _ = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )
    original_atomic_write = mod._atomic_write_json

    def fail_archive_write(path: Path, payload: dict) -> None:
        if path.parent.name == "invalidated":
            raise OSError("archive filesystem unavailable")
        original_atomic_write(path, payload)

    monkeypatch.setattr(mod, "_atomic_write_json", fail_archive_write)
    missed_at = datetime(2026, 8, 19, 8, 40, tzinfo=KST)
    missed, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=missed_at.date(),
        now=missed_at,
        apply_receipt_dir=tmp_path / "receipts",
    )
    history = missed["candidates"][0]["invalidated_operator_decision_history"]
    assert len(history) == 1
    assert history[0]["archive_status"] == "inline_snapshot_only"
    assert history[0]["archived_artifact_path"] is None
    assert history[0]["operator_decision_artifact_sha256"]
    assert missed["candidates"][0]["invalidated_operator_decision_artifacts"] == []
    assert (
        history[0]["operator_decision_artifact_snapshot"]["operator_authorization_id"]
        == "operator-original-evidence"
    )

    reapproved, rewritten_path = mod.record_operator_decision(
        missed,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-new-evidence",
        operator_instruction="Re-arm after reviewing the missed handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=missed_at,
    )
    rewritten = json.loads(rewritten_path.read_text(encoding="utf-8"))
    preserved = reapproved["candidates"][0]["invalidated_operator_decision_history"][0]
    assert rewritten_path == artifact_path
    assert rewritten["operator_authorization_id"] == "operator-new-evidence"
    assert (
        preserved["operator_decision_artifact_snapshot"]["operator_authorization_id"]
        == "operator-original-evidence"
    )


def test_unreadable_canonical_decision_fails_invalidation_closed(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    approved, artifact_path = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-must-remain-auditable",
        operator_instruction="Fail closed if canonical evidence becomes unreadable.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    artifact_path.unlink()

    with pytest.raises(
        ValueError, match="operator_decision_artifact_unreadable_during_invalidation"
    ):
        mod.sync_queue(
            approved,
            source_candidates=[],
            source_path=Path("fresh-empty-source.json"),
            as_of_date=now.date(),
            source_status="loaded",
            now=datetime(2026, 8, 14, 20, 31, tzinfo=KST),
            apply_receipt_dir=tmp_path / "receipts",
        )

    assert approved["candidates"][0]["state"] == mod.STATE_USER_APPROVED
    assert approved["candidates"][0]["operator_authorization_id"] == (
        "operator-must-remain-auditable"
    )


def test_fresh_postclose_withdrawal_does_not_discard_late_apply_receipt(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    candidate = _candidate()
    candidate["evidence_valid_through"] = "2026-08-18"
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[candidate],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve one exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    queue, handoffs = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )

    postclose, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=Path("fresh-empty-source.json"),
        as_of_date=date(2026, 8, 18),
        source_status="loaded",
        now=datetime(2026, 8, 18, 21, 15, tzinfo=KST),
        apply_receipt_dir=tmp_path / "receipts",
    )
    assert postclose["candidates"][0]["state"] == mod.STATE_PREOPEN_SCHEDULED

    entry = postclose["candidates"][0]
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    (receipt_dir / "late-applied.json").write_text(
        json.dumps(
            {
                "schema": mod.APPLY_RECEIPT_SCHEMA,
                "queue_key": entry["queue_key"],
                "candidate_sha256": entry["candidate_sha256"],
                "runtime_family": "widget_micro_entry_confirmation_v1",
                "stage": "entry",
                "axis": "micro_confirmation_threshold",
                "bounded_contract_sha256": "b" * 64,
                "runtime_registry_entry_sha256": entry["runtime_registry_entry_sha256"],
                "preopen_handoff": str(handoffs[0]),
                "target_date": "2026-08-18",
                "status": "applied_guard_passed",
                "receipt_owner": "widget_micro_entry_policy_apply",
                "applied_at_kst": "2026-08-18T07:45:00+09:00",
                "runtime_effect": True,
                "runtime_apply_performed": True,
                "actual_order_submitted": False,
                "same_stage_owner_conflict_free": True,
                "hard_safety_and_broker_guards_preserved": True,
            }
        ),
        encoding="utf-8",
    )

    applied, _ = mod.sync_queue(
        postclose,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 19),
        now=datetime(2026, 8, 19, 8, 40, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )

    assert applied["candidates"][0]["state"] == mod.STATE_APPLIED
    assert "widget_micro_entry_confirmation_v1" in applied["family_enrollments"]


def test_fresh_candidate_version_does_not_discard_same_day_apply_receipt(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    receipt_dir = tmp_path / "receipts"
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        source_status="loaded",
        now=now,
        apply_receipt_dir=receipt_dir,
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve one exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=receipt_dir,
        now=now,
    )
    queue, handoffs = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )
    scheduled_entry = queue["candidates"][0]
    receipt_dir.mkdir()
    (receipt_dir / "applied.json").write_text(
        json.dumps(
            {
                "schema": mod.APPLY_RECEIPT_SCHEMA,
                "queue_key": scheduled_entry["queue_key"],
                "candidate_sha256": scheduled_entry["candidate_sha256"],
                "runtime_family": "widget_micro_entry_confirmation_v1",
                "stage": "entry",
                "axis": "micro_confirmation_threshold",
                "bounded_contract_sha256": "b" * 64,
                "runtime_registry_entry_sha256": scheduled_entry[
                    "runtime_registry_entry_sha256"
                ],
                "preopen_handoff": str(handoffs[0]),
                "target_date": "2026-08-18",
                "status": "applied_guard_passed",
                "receipt_owner": "widget_micro_entry_policy_apply",
                "applied_at_kst": "2026-08-18T07:45:00+09:00",
                "runtime_effect": True,
                "runtime_apply_performed": True,
                "actual_order_submitted": False,
                "same_stage_owner_conflict_free": True,
                "hard_safety_and_broker_guards_preserved": True,
            }
        ),
        encoding="utf-8",
    )
    fresh_candidate = _candidate(
        source_date="2026-08-18",
        recommended_value=0.27,
    )

    reconciled, _ = mod.sync_queue(
        queue,
        source_candidates=[fresh_candidate],
        source_path=Path("fresh-source.json"),
        as_of_date=date(2026, 8, 18),
        source_status="loaded",
        now=datetime(2026, 8, 18, 21, 15, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )

    prior = next(
        row
        for row in reconciled["candidates"]
        if row["queue_key"] == scheduled_entry["queue_key"]
    )
    assert prior["state"] == mod.STATE_APPLIED
    assert prior["family_apply_receipt"] == str(receipt_dir / "applied.json")
    assert "widget_micro_entry_confirmation_v1" in reconciled["family_enrollments"]


def test_expired_missed_handoff_is_archived_before_terminal_expiry(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    candidate = _candidate()
    candidate["evidence_valid_through"] = "2026-08-18"
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[candidate],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve one exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    scheduled, _ = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )

    expired, _ = mod.sync_queue(
        scheduled,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 19),
        now=datetime(2026, 8, 19, 8, 40, tzinfo=KST),
        apply_receipt_dir=tmp_path / "receipts",
    )

    expired_entry = expired["candidates"][0]
    assert expired_entry["state"] == mod.STATE_EXPIRED
    assert expired_entry["missed_preopen_handoffs"][0]["target_date"] == "2026-08-18"
    assert "preopen_handoff" not in expired_entry


def test_apply_receipt_cannot_bypass_operator_and_preopen_gates(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=Path("/__no_receipts__"),
    )
    entry = queue["candidates"][0]
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    (receipt_dir / "forged.json").write_text(
        json.dumps(
            {
                "schema": mod.APPLY_RECEIPT_SCHEMA,
                "queue_key": entry["queue_key"],
                "candidate_sha256": entry["candidate_sha256"],
                "runtime_family": "widget_micro_entry_confirmation_v1",
                "stage": "entry",
                "axis": "micro_confirmation_threshold",
                "bounded_contract_sha256": "b" * 64,
                "preopen_handoff": "missing.json",
                "target_date": "2026-08-18",
                "status": "applied_guard_passed",
                "same_stage_owner_conflict_free": True,
                "hard_safety_and_broker_guards_preserved": True,
            }
        ),
        encoding="utf-8",
    )

    unchanged, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 18),
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )

    assert unchanged["candidates"][0]["state"] == mod.STATE_REVIEW_READY
    assert unchanged["family_enrollments"] == {}


def test_apply_receipt_requires_target_day_timestamp_and_registered_owner(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 14, 20, 30, tzinfo=KST)
    queue, _ = mod.sync_queue(
        _empty(now),
        source_candidates=[_candidate()],
        source_path=Path("source.json"),
        as_of_date=now.date(),
        now=now,
        apply_receipt_dir=tmp_path / "receipts",
    )
    entry = queue["candidates"][0]
    queue, _ = mod.record_operator_decision(
        queue,
        candidate_id=entry["candidate_id"],
        expected_candidate_sha256=entry["candidate_sha256"],
        decision="approve",
        operator_authorization_id="operator-explicit-20260814",
        operator_instruction="Approve one exact-date PREOPEN handoff.",
        approval_dir=tmp_path / "approvals",
        apply_receipt_dir=tmp_path / "receipts",
        now=now,
    )
    queue, handoffs = mod.schedule_preopen_handoffs(
        queue,
        target_date=date(2026, 8, 18),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 18, 7, 40, tzinfo=KST),
    )
    entry = queue["candidates"][0]
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    receipt = {
        "schema": mod.APPLY_RECEIPT_SCHEMA,
        "queue_key": entry["queue_key"],
        "candidate_sha256": entry["candidate_sha256"],
        "runtime_family": "widget_micro_entry_confirmation_v1",
        "stage": "entry",
        "axis": "micro_confirmation_threshold",
        "bounded_contract_sha256": "b" * 64,
        "runtime_registry_entry_sha256": entry["runtime_registry_entry_sha256"],
        "preopen_handoff": str(handoffs[0]),
        "target_date": "2026-08-18",
        "status": "applied_guard_passed",
        "receipt_owner": "widget_micro_entry_policy_apply",
        "applied_at_kst": "2026-08-19T08:45:00+09:00",
        "runtime_effect": True,
        "runtime_apply_performed": True,
        "actual_order_submitted": False,
        "same_stage_owner_conflict_free": True,
        "hard_safety_and_broker_guards_preserved": True,
    }
    (receipt_dir / "wrong-day.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )
    (receipt_dir / "after-market-open.json").write_text(
        json.dumps(
            {
                **receipt,
                "applied_at_kst": "2026-08-18T08:45:00+09:00",
            }
        ),
        encoding="utf-8",
    )

    unchanged, _ = mod.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 8, 18),
        now=datetime(2026, 8, 18, 9, 0, tzinfo=KST),
        apply_receipt_dir=receipt_dir,
    )

    assert unchanged["candidates"][0]["state"] == mod.STATE_PREOPEN_SCHEDULED
    assert unchanged["family_enrollments"] == {}


def test_readiness_rejects_prebaseline_and_boolean_numeric_evidence() -> None:
    candidate = _candidate(source_date="2026-06-01")
    candidate["evidence"]["observed_trading_days"] = True

    errors = mod.evidence_readiness_errors(candidate)

    assert "source_date_before_clean_baseline" in errors
    assert "observed_trading_days_below_5" in errors


def test_readiness_rejects_thin_or_drifted_rolling_paired_counts() -> None:
    thin = _candidate()
    thin["evidence"]["rolling_paired_complete_lifecycle_count"]["5d"] = 4

    thin_errors = mod.evidence_readiness_errors(thin)

    assert "rolling_5d_paired_lifecycle_count_below_5" in thin_errors

    drifted = _candidate()
    drifted["evidence"]["rolling_paired_complete_lifecycle_floor"]["5d"] = 20

    drifted_errors = mod.evidence_readiness_errors(drifted)

    assert "rolling_paired_lifecycle_floor_contract_invalid" in drifted_errors
