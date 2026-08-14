import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.automation import machine_microstructure_policy_approval as mod


KST = ZoneInfo("Asia/Seoul")


def _runtime_registry() -> dict:
    return {
        "widget_micro_entry_confirmation_v1": {
            "enabled": True,
            "stage": "entry",
            "axis": "micro_confirmation_threshold",
            "bounded_contract_sha256": "b" * 64,
            "preopen_consumer": "widget_micro_entry_policy_apply",
            "apply_receipt_owner": "widget_micro_entry_policy_apply",
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


def _empty(now: datetime) -> dict:
    return mod._empty_queue(now=now)


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
        now=datetime(2026, 8, 18, 8, 40, tzinfo=KST),
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
        now=datetime(2026, 8, 19, 8, 40, tzinfo=KST),
    )
    assert next_handoffs == []
    assert unchanged["candidates"][0]["preopen_target_date"] == "2026-08-18"


def test_invalid_source_report_is_not_silently_treated_as_no_candidate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")

    path, candidates, status = mod._load_source_candidates(
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
    )

    assert candidates == []
    assert status == "contract_invalid"
    assert report["decision"] == "source_gap_queue_preserved"
    assert report["source_status"] == "contract_invalid"


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
        now=datetime(2026, 8, 18, 8, 40, tzinfo=KST),
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

    subsequent = _candidate(
        candidate_id="widget:005930:entry:micro_axis:v2",
        recommended_value=0.27,
        first_approval=False,
        source_date="2026-08-18",
    )
    auto, _ = mod.sync_queue(
        applied,
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
        now=datetime(2026, 8, 19, 8, 40, tzinfo=KST),
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

    (receipt_dir / "post_apply.json").write_text(
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
                "status": "post_apply_attribution_complete",
                "runtime_effect": False,
                "runtime_apply_performed": False,
                "actual_order_submitted": False,
                "post_apply_attribution_complete": True,
                "source_apply_receipt": str(receipt_dir / "applied.json"),
                "same_stage_owner_conflict_free": True,
                "hard_safety_and_broker_guards_preserved": True,
            }
        ),
        encoding="utf-8",
    )
    attributed, _ = mod.sync_queue(
        auto_scheduled,
        source_candidates=[],
        source_path=None,
        as_of_date=date(2026, 9, 1),
        now=datetime(2026, 9, 1, 20, 30, tzinfo=KST),
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
        now=datetime(2026, 8, 18, 8, 40, tzinfo=KST),
    )

    unchanged, second = mod.schedule_preopen_handoffs(
        scheduled,
        target_date=date(2026, 8, 19),
        handoff_dir=tmp_path / "handoffs",
        now=datetime(2026, 8, 19, 8, 40, tzinfo=KST),
    )

    assert len(first) == 1
    assert second == []
    assert unchanged["candidates"][0]["preopen_target_date"] == "2026-08-18"


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


def test_readiness_rejects_prebaseline_and_boolean_numeric_evidence() -> None:
    candidate = _candidate(source_date="2026-06-01")
    candidate["evidence"]["observed_trading_days"] = True

    errors = mod.evidence_readiness_errors(candidate)

    assert "source_date_before_clean_baseline" in errors
    assert "observed_trading_days_below_5" in errors
