"""Pattern audit repair acceptance: no provider, runtime or economic floor."""

import copy
import hashlib
import json
from datetime import date

import pytest

from src.engine import pattern_lab_ai_review as ai
from src.engine import pattern_lab_currentness_audit as currentness
from src.engine.automation.pattern_lab_source_contract import read_feedback
from src.tests.test_pattern_lab_currentness_audit import _seed_labs

DAY = "2026-09-08"


def context():
    return {
        "date": DAY,
        "strategy_scope": "swing_only",
        "swing_sources_enabled": True,
        "sources": {
            "swing_pattern_lab_automation": {
                "summary": {"economic_evidence": {"net": 1}}
            }
        },
        "currentness_checks": [],
        "feedback_handoff_summary": {},
    }


def response(**changes):
    return {
        "schema_version": 1,
        "interpretation": {"review_items": []},
        "audit": {"status": "pass", "issues": [], "forbidden_use_violations": []},
        "final_conclusions": [
            {
                "review_id": "net_research",
                "domain": "swing",
                "final_state": "source_only_keep_collecting",
                "final_decision": "keep",
                "reason": "Small net evidence is source-only.",
                "required_followup": [],
                **changes,
            }
        ],
    }


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    c = context()
    monkeypatch.setattr(ai, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(ai, "_build_input_context", lambda *a, **k: copy.deepcopy(c))
    monkeypatch.setattr(
        ai,
        "_call_openai_ai_review",
        lambda *a, **k: pytest.fail("No provider call permitted"),
    )
    return c


def build(raw=None):
    return ai.build_pattern_lab_ai_review_report(
        DAY, provider="openai", ai_raw_response=raw or response(), include_swing=True
    )


def test_quality_failure_is_material_and_cannot_keep_pass(isolated):
    isolated["sources"]["observation_source_quality_audit"] = {
        "summary": {"status": "pass", "summary": {"tuning_input_allowed": True}}
    }
    first = build()
    isolated["sources"]["observation_source_quality_audit"]["summary"] = {
        "status": "fail",
        "summary": {
            "tuning_input_allowed": False,
            "blocked_reason": "missing_required_cost",
        },
    }
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert not r["material_review_current"]
    assert r["status"] == "warning"
    assert any(
        o.get("review_id") == "currentness:pattern_review_source_quality_guard"
        for o in r["code_improvement_orders"]
    )
    assert (
        r["ai_two_pass_review"]["input_context_hash"]
        == first["ai_two_pass_review"]["input_context_hash"]
    )


def test_review_material_separates_metadata_from_economic_values():
    value = {
        "generated_at": "first",
        "daily_ev_summary": {"net_krw": 12},
        "source_quality_preflight_gate": {
            "artifact": "a.json",
            "tuning_input_allowed": True,
        },
    }
    original = ai._semantic_review_value(value)
    value["generated_at"] = "second"
    value["source_quality_preflight_gate"]["artifact"] = "b.json"
    assert ai._semantic_review_value(value) == original
    value["daily_ev_summary"]["net_krw"] = -12
    assert ai._semantic_review_value(value) != original


def test_bounded_review_reentry_closes_new_material_and_stops_at_daily_cap(
    isolated, monkeypatch
):
    calls = []

    def provider(c, **kwargs):
        calls.append(copy.deepcopy(c))
        return response(), {
            "provider": "openai",
            "model": "fixture",
            "status": "success",
        }

    monkeypatch.setattr(ai, "_call_openai_ai_review", provider)
    first = ai.review_current_generation(DAY, include_swing=True)
    assert first["material_review_current"] and len(calls) == 1
    isolated["sources"]["swing_pattern_lab_automation"]["summary"][
        "economic_evidence"
    ]["net"] = 2
    metadata = ai.refresh_pattern_lab_ai_review_source_provenance(
        DAY, include_swing=True
    )
    assert metadata["review_reentry"]["new_provider_calls"] == 0
    assert metadata["review_reentry"]["state"] == "pending"
    assert len(calls) == 1
    second = ai.review_current_generation(DAY, include_swing=True)
    assert second["material_review_current"] and len(calls) == 2
    assert second["review_material_hash"] != first["review_material_hash"]
    assert (
        second["review_history"][0]["original_response_hash"]
        == first["ai_two_pass_review"]["original_response_hash"]
    )
    again = ai.review_current_generation(DAY, include_swing=True)
    assert again["review_reentry"]["new_provider_calls"] == 0
    isolated["sources"]["swing_pattern_lab_automation"]["summary"][
        "economic_evidence"
    ]["net"] = 3
    exhausted = ai.review_current_generation(DAY, include_swing=True)
    assert not exhausted["material_review_current"]
    assert exhausted["review_reentry"]["state"] == "budget_exhausted"
    assert exhausted["status"] == "warning" and len(calls) == 2
    assert ai.review_generation_matches(DAY, exhausted)
    from src.engine.automation.automation_chain_trigger_decision import (
        _non_reusable_payload_reason,
    )

    assert _non_reusable_payload_reason(exhausted) is None


def test_metadata_pending_is_a_trigger_even_when_file_is_newer(isolated):
    build()
    isolated["currentness_checks"] = [{"check_id": "new", "status": "fail"}]
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    from src.engine.automation.automation_chain_trigger_decision import (
        _non_reusable_payload_reason,
    )

    assert _non_reusable_payload_reason(r) == "pattern_review_material_pending"


def test_review_reservation_survives_interruption_and_is_not_retried(
    isolated, monkeypatch
):
    calls = []

    def interrupted(*args, **kwargs):
        calls.append(True)
        raise RuntimeError("interrupted provider")

    monkeypatch.setattr(ai, "_call_openai_ai_review", interrupted)
    with pytest.raises(RuntimeError, match="interrupted provider"):
        ai.review_current_generation(DAY, include_swing=True)
    result = ai.review_current_generation(DAY, include_swing=True)
    assert len(calls) == 1
    assert result["review_reentry"]["state"] == "terminal_attempt_not_retried"
    assert not result["material_review_current"]


def test_legacy_review_does_not_invent_unused_provider_budget(isolated):
    build()
    isolated["currentness_checks"] = [{"check_id": "new", "status": "fail"}]
    result = ai.review_current_generation(DAY, include_swing=True)
    assert result["review_reentry"]["state"] == "budget_exhausted"


def test_verifier_detects_unreconciled_primary_generation(isolated):
    r = build()
    assert ai.review_generation_matches(DAY, r)
    isolated["currentness_checks"] = [{"check_id": "changed", "status": "fail"}]
    assert not ai.review_generation_matches(DAY, r)


def test_controller_reconciles_only_enabled_pattern_owner():
    from src.engine.automation.postclose_done_controller import (
        _pattern_review_recovery_actions,
    )

    assert not _pattern_review_recovery_actions(DAY, {})
    active = {"execution_profile": {"flags": {"swing_lifecycle": True, "pattern_lab_ai_review": True}}}
    (action,) = _pattern_review_recovery_actions(DAY, active)
    assert "--review-current-generation" in action.command
    active["execution_profile"]["disabled_stage_flags"] = ["pattern_lab_ai_review"]
    assert not _pattern_review_recovery_actions(DAY, active)


def test_pattern_only_recovery_does_not_rerun_daily_ai_or_preopen(monkeypatch):
    from src.engine.automation import postclose_done_controller as controller

    monkeypatch.setattr(controller, "_latest_failed_tail_stage", lambda target: None)
    report = {
        "stale_downstream_links": ["pattern_lab_ai_review_source_generation_stale"],
        "execution_profile": {
            "flags": {
                "swing_lifecycle": True,
                "pattern_lab_ai_review": True,
                "tuning_performance_control_tower": True,
            }
        },
    }
    actions = controller._recovery_actions(DAY, report, allow_wrapper_rerun=False)
    names = [a.action for a in actions]
    assert "refresh_pattern_lab_ai_review_generation" in names
    assert "refresh_daily_threshold_cycle_report" not in names
    assert "sync_exact_trade_performance_facts" not in names
    assert "refresh_next_preopen_apply" not in names
    assert names[-1] == "verify_postclose_chain"
    assert names.index("refresh_runtime_approval_summary") < names.index(
        "refresh_next_stage2_checklist"
    )


def test_real_late_bound_producer_context_reaches_fixed_point(tmp_path, monkeypatch):
    monkeypatch.setattr(ai, "REPORT_DIR", tmp_path)
    calls = []

    def provider(c, **kwargs):
        calls.append(copy.deepcopy(c))
        return response(), {"provider": "openai", "model": "fixture"}

    monkeypatch.setattr(ai, "_call_openai_ai_review", provider)
    paths = ai._source_paths(DAY, include_swing=True)

    def write(name, payload):
        paths[name].parent.mkdir(parents=True, exist_ok=True)
        paths[name].write_text(json.dumps({"date": DAY, **payload}))

    write("swing_pattern_lab_automation", {"runtime_effect": False, "summary": {}})
    write(
        "pattern_lab_currentness_audit",
        {"status": "pass", "checks": [], "summary": {"fail_count": 0}},
    )
    write(
        "observation_source_quality_audit",
        {"status": "pass", "summary": {"tuning_input_allowed": True}},
    )
    first = ai.review_current_generation(DAY, include_swing=True)
    assert len(calls) == 1
    ev = {"generated_at": "first", "daily_ev_summary": {"realized_pnl_krw": 123}}
    write("threshold_cycle_ev", ev)
    second = ai.review_current_generation(DAY, include_swing=True)
    assert len(calls) == 2 and second["material_review_current"]
    assert first["review_material_hash"] != second["review_material_hash"]
    ev.update(
        generated_at="metadata refresh", pattern_lab_ai_review={"status": "warning"}
    )
    write("threshold_cycle_ev", ev)
    final = ai.review_current_generation(DAY, include_swing=True)
    assert len(calls) == 2 and final["material_review_current"]
    assert ai.review_generation_matches(DAY, final, report_dir=tmp_path)
    write(
        "observation_source_quality_audit",
        {"status": "fail", "summary": {"tuning_input_allowed": False}},
    )
    assert not ai.review_generation_matches(DAY, final, report_dir=tmp_path)
    failed = ai.review_current_generation(DAY, include_swing=True)
    assert not failed["material_review_current"] and failed["status"] == "warning"
    assert ai.review_generation_matches(DAY, failed, report_dir=tmp_path)
    assert len(calls) == 2


def test_review_mutex_prevents_concurrent_call(isolated):
    path = ai.report_paths(DAY)[0].with_suffix(".review-budget.json")
    path.parent.mkdir(parents=True)
    with ai.json_artifact_generation_lock(path, exclusive=True, blocking=False):
        with pytest.raises(OSError, match="lock_busy"):
            ai.review_current_generation(DAY, include_swing=True)


def test_budget_corruption_is_not_reset(isolated):
    path = ai.report_paths(DAY)[0].with_suffix(".review-budget.json")
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema": "pattern_review_attempt_budget_v1",
                "date": DAY,
                "attempts": ["bad"],
            }
        )
    )
    with pytest.raises(ValueError, match="budget_invalid"):
        ai.review_current_generation(DAY, include_swing=True)
    assert not ai.report_paths(DAY)[0].exists()


def test_terminal_provider_failure_does_not_leave_an_actionable_pending_retry(
    isolated, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        ai,
        "_call_openai_ai_review",
        lambda *a, **k: (
            calls.append(1) or None,
            {"provider": "openai", "status": "failed"},
        ),
    )
    result = ai.review_current_generation(DAY, include_swing=True)
    used = len(calls)
    assert 1 <= used <= ai.REVIEW_ATTEMPT_LIMIT
    assert result["review_reentry"]["state"] == "terminal_attempt_not_retried"
    ai.review_current_generation(DAY, include_swing=True)
    assert len(calls) == used


def test_new_target_date_gets_its_own_budget_without_approving_old_date(
    isolated, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        ai,
        "_call_openai_ai_review",
        lambda *a, **k: (calls.append(1) or response(), {"provider": "openai"}),
    )
    r = ai.review_current_generation(DAY, include_swing=True)
    isolated["date"] = "2026-09-09"
    next_day = ai.review_current_generation("2026-09-09", include_swing=True)
    assert len(calls) == 2
    assert next_day["review_reentry"]["attempts_used"] == 1
    assert (
        json.loads(ai.report_paths(DAY)[0].read_bytes())["review_material_hash"]
        == r["review_material_hash"]
    )


def test_ai_cannot_omit_any_failed_currentness_check(isolated):
    isolated["currentness_checks"] = [
        {
            "check_id": f"claude_{n}",
            "status": "fail",
            "severity": "source_quality_blocker",
            "finding": "Bad hash",
        }
        for n in range(35)
    ]
    r = build()
    conclusions = r["ai_two_pass_review"]["final_conclusions"]
    assert {
        i.get("deterministic_check_id")
        for i in conclusions
        if i.get("deterministic_check_id")
    } == {f"claude_{n}" for n in range(35)}
    assert r["status"] == "warning"
    assert len(r["code_improvement_orders"]) == 35
    assert all(
        o["runtime_effect"] is False and o["allowed_runtime_apply"] is False
        for o in r["code_improvement_orders"]
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"final_state": "source_quality_gap"},
        {"auditor_pass": False},
        {"final_state": "source_quality_gap", "auditor_pass": False},
    ],
)
def test_keep_never_erases_unresolved_gap(isolated, changes):
    r = build(response(**changes))
    assert r["status"] == "warning"
    assert r["code_improvement_orders"]


def test_active_scalping_gap_survives_swing_mention(isolated):
    r = build(
        response(
            final_state="source_quality_gap",
            final_decision="surface_workorder",
            reason="Scalping cost source invalid; Swing is disabled.",
        )
    )
    assert (
        r["ai_two_pass_review"]["final_conclusions"][0]["review_id"] == "net_research"
    )
    assert r["code_improvement_orders"][0]["review_id"] == "net_research"




@pytest.mark.parametrize("raw", ["[]", "null", '"text"', "42", "true", "{bad"])
def test_invalid_root_is_rejected_without_exception(raw):
    assert ai._parse_ai_review_response(raw)[0] == "parse_rejected"


def test_duplicate_native_review_id_rejected():
    raw = response()
    raw["final_conclusions"] *= 2
    assert ai._parse_ai_review_response(raw)[0] == "parse_rejected"


def test_refresh_preserves_original_input_and_response(isolated):
    first = build()
    isolated["sources"]["threshold_cycle_ev"] = {"summary": {"status": "pass"}}
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert r["material_review_current"] is True
    assert r["status"] == "pass"
    assert r["source_context_hash"] != first["source_context_hash"]
    assert (
        r["ai_two_pass_review"]["input_context_hash"]
        == first["ai_two_pass_review"]["input_context_hash"]
    )
    assert (
        r["ai_two_pass_review"]["original_response"]
        == first["ai_two_pass_review"]["original_response"]
    )
    again = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert again["review_material_hash"] == first["review_material_hash"]
    assert again["code_improvement_orders"] == r["code_improvement_orders"]


def test_refresh_does_not_relabel_new_economics_as_reviewed(isolated):
    first = build()
    isolated["sources"]["swing_pattern_lab_automation"]["summary"][
        "economic_evidence"
    ]["net"] = -5
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert r["material_review_current"] is False
    assert r["status"] == "warning"
    assert (
        "material_inputs_changed_requires_review"
        in r["summary"]["ai_review_followup_reasons"]
    )
    assert (
        r["ai_two_pass_review"]["input_context_hash"]
        == first["ai_two_pass_review"]["input_context_hash"]
    )
    assert r["source_provenance_refresh"]["new_provider_call"] is False
    again = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert again["code_improvement_orders"] == r["code_improvement_orders"]


def test_new_currentness_failure_enforced_during_refresh(isolated):
    build()
    isolated["currentness_checks"] = [
        {
            "check_id": "claude_hash",
            "status": "fail",
            "severity": "source_quality_blocker",
            "finding": "New hash invalid",
        }
    ]
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert r["status"] == "warning"
    assert any(
        o.get("review_id") == "currentness:claude_hash"
        for o in r["code_improvement_orders"]
    )


@pytest.mark.parametrize(
    "value", [[], None, {}, {"date": "2026-09-07"}, {"date": DAY, "status": "failed"}]
)
def test_feedback_rejects_malformed_wrong_date_or_failed(tmp_path, value):
    p = tmp_path / "feedback.json"
    p.write_text(json.dumps(value))
    assert read_feedback(p, DAY, DAY)["validation_status"] == "invalid"








@pytest.mark.parametrize("schema", ["bad", True, None, [], {}])
def test_currentness_malformed_schema_is_a_finding_not_crash(schema):
    assert currentness._metric_contract_ok({"schema_version": schema}) is False


def test_prompt_uses_active_owners_and_small_net_objective():
    prompt = ai._build_ai_review_instructions()
    assert prompt.isascii()
    assert "If LDM/threshold feedback is missing" not in prompt
    assert "are retired" in prompt
    assert "small net profits" in prompt


def test_refresh_keeps_retired_words_in_original_response(isolated):
    raw = response(required_followup=["scalp_entry_adm", "lifecycle_decision_matrix"])
    first = build(raw)
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert r["ai_two_pass_review"]["original_response"] == raw
    assert (
        r["ai_two_pass_review"]["original_response_hash"]
        == first["ai_two_pass_review"]["original_response_hash"]
    )


def test_provider_cannot_assert_its_own_deterministic_resolution(isolated):
    r = build(
        response(
            final_state="source_quality_gap",
            final_decision="surface_workorder",
            source_context_resolution={"status": "resolved_fake_contract"},
        )
    )
    assert r["status"] == "warning"
    assert r["code_improvement_orders"]


def test_refresh_tampered_response_does_not_overwrite_previous(isolated):
    r = build()
    path, _ = ai.report_paths(DAY)
    r["ai_two_pass_review"]["original_response"]["final_conclusions"][0][
        "reason"
    ] = "tampered"
    path.write_text(json.dumps(r))
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match="response_hash_mismatch"):
        ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert path.read_bytes() == before


def test_material_review_pending_reaches_workorder_and_ev(isolated, monkeypatch):
    from src.engine import build_code_improvement_workorder as workorder
    from src.engine import threshold_cycle_ev_report as ev

    first = build()
    isolated["sources"]["swing_pattern_lab_automation"]["summary"][
        "economic_evidence"
    ] = {"net": -1}
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    order = next(
        o for o in r["code_improvement_orders"] if o.get("material_review_pending")
    )
    classified = workorder._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "defer_evidence"
    assert "fresh exact-generation" in classified.reason
    summary, _, warnings = ev._audit_summary(
        DAY, ai.REPORT_TYPE, ai.REPORT_DIR / ai.REPORT_TYPE
    )
    assert summary["status"] == "warning"
    assert summary["ai_review_followup_required"] is True
    assert warnings
    assert first["runtime_effect"] is False and r["runtime_effect"] is False


def test_trigger_tracks_primary_generation_and_contract_code():
    from src.engine.automation import automation_chain_trigger_decision as trigger

    specs = {s.step_id: s for s in trigger._step_specs(DAY)}
    current = specs["pattern_lab_currentness_audit"].source_paths
    assert all("claude_scalping_pattern_lab" not in path for path in current)
    assert "src/engine/automation/pattern_lab_source_contract.py" in current
    review = specs["pattern_lab_ai_review"].source_paths
    assert "src/engine/pattern_lab_ai_review.py" in review
    assert any("swing_pattern_lab_automation" in s for s in review)


def test_source_authority_violation_cannot_be_hidden_by_keep(isolated):
    isolated["sources"]["swing_pattern_lab_automation"]["summary"][
        "allowed_runtime_apply"
    ] = True
    r = build()
    assert r["status"] == "warning"
    assert any(
        "source_only_authority" in o.get("review_id", "")
        for o in r["code_improvement_orders"]
    )


@pytest.mark.parametrize("value", ["false", 1, None, []])
def test_auditor_flag_must_be_boolean(value):
    assert (
        ai._parse_ai_review_response(response(auditor_pass=value))[0]
        == "parse_rejected"
    )


def test_colliding_native_id_slug_is_rejected():
    raw = response(review_id="source:a")
    raw["final_conclusions"].append(
        {**raw["final_conclusions"][0], "review_id": "source-a"}
    )
    assert ai._parse_ai_review_response(raw)[0] == "parse_rejected"


def test_hidden_cohort_change_invalidates_material_fingerprint(monkeypatch):
    evidence = {
        "claude": {"windows": {"rolling": {"cohorts": [{"net": 1} for _ in range(21)]}}}
    }
    payload = {"date": DAY, "economic_evidence": evidence}
    monkeypatch.setattr(
        ai,
        "_load_json",
        lambda p: payload if "swing_pattern_lab_automation" in str(p) else {},
    )
    first = ai._build_input_context(DAY, include_swing=True)
    evidence["claude"]["windows"]["rolling"]["cohorts"][-1]["net"] = -5
    second = ai._build_input_context(DAY, include_swing=True)
    assert ai._material_context_hash(first) != ai._material_context_hash(second)


def test_wrong_date_refresh_preserves_previous_file(isolated):
    r = build()
    path, _ = ai.report_paths(DAY)
    r["date"] = "2026-09-07"
    path.write_text(json.dumps(r))
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match="date_mismatch"):
        ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert path.read_bytes() == before


def test_old_model_patch_cannot_be_applied_to_new_generation(isolated):
    first = build(
        response(
            final_state="code_patch_required",
            final_decision="surface_workorder",
            reason="Generation A needs a specific parser fix",
        )
    )
    assert any(
        o.get("review_id") == "net_research" for o in first["code_improvement_orders"]
    )
    isolated["sources"]["swing_pattern_lab_automation"]["summary"][
        "economic_evidence"
    ] = {"net": 3}
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert not any(
        o.get("review_id") == "net_research" for o in r["code_improvement_orders"]
    )
    assert (
        r["ai_two_pass_review"]["original_response"]
        == first["ai_two_pass_review"]["original_response"]
    )
    assert (
        r["ai_two_pass_review"]["effective_review_authority"]
        == "deterministic_current_sources_only"
    )


def test_changed_reviewer_instructions_invalidate_old_material_hash(
    isolated, monkeypatch
):
    build()
    monkeypatch.setattr(
        ai, "_build_ai_review_instructions", lambda: "Changed review contract"
    )
    r = ai.refresh_pattern_lab_ai_review_source_provenance(DAY, include_swing=True)
    assert r["material_review_current"] is False


def test_currentness_native_order_handoff_is_not_duplicate_implementation(isolated):
    from src.engine import build_code_improvement_workorder as workorder

    isolated["currentness_checks"] = [
        {
            "check_id": "claude_hash",
            "status": "fail",
            "severity": "source_quality_blocker",
            "finding": "Bad generation",
            "upstream_order_id": "order_pattern_lab_currentness_audit_claude_hash",
        }
    ]
    r = build()
    order = next(
        o
        for o in r["code_improvement_orders"]
        if o.get("upstream_currentness_order_id")
    )
    classified = workorder._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "attach_existing_family"
    assert order["upstream_currentness_order_id"] in classified.automation_reentry
    assert r["status"] == "warning"
