from copy import deepcopy
from datetime import datetime, timedelta
import json

import pytest

from src.engine import buy_funnel_sentinel as sentinel
from src.engine.automation.submit_drought_contract import (
    make_scope_evidence,
    validate_scope_evidence,
    validate_submit_drought_contract,
)
from src.engine.scalping import entry_ai_gate_backtest as controller
from src.engine.scalping.entry_recheck_policy import scope_summary
from src.tests.submit_drought_fixtures import make_report


def events(*sequence):
    result = []
    for i, item in enumerate(sequence):
        stage, fields = item if isinstance(item, tuple) else (item, {})
        result.append(
            sentinel.PipelineEvent(
                datetime(2026, 9, 7, 10) + timedelta(seconds=i),
                "ENTRY_PIPELINE",
                stage,
                "fixture",
                "000001",
                "1",
                fields,
            )
        )
    return result


def inspect(rows):
    report = make_report(events=rows)
    contract = report["entry_submit_drought_contract"]
    status = validate_submit_drought_contract(report, contract, require_current=True)
    assert status["status"] in {"pass", "source_quality_blocked"}, status
    return contract["exact_attempt_contract"]


@pytest.mark.parametrize(
    "stage",
    [
        "blocked_liquidity",
        "blocked_overbought",
        "blocked_strength_momentum",
        "blocked_vpw",
        "blocked_gap",
        "blocked_zero_qty",
        "entry_armed_expired",
    ],
)
def test_actual_upstream_terminals_are_not_no_signal(stage):
    exact = inspect(events("ai_confirmed", stage))
    assert exact["axis_terminal_causal_attempt_counts"]["UPSTREAM_GATE"] == 1


@pytest.mark.parametrize(
    "attempts,responses,mode,axis",
    [
        (1, 0, "broker_submit_failed_or_unacknowledged", "BROKER_RECEIPT"),
        (1, 1, "broker_acknowledged_order_identity_missing", "BROKER_RECEIPT"),
        (0, 0, "pre_broker_blocked", "UPSTREAM_GATE"),
    ],
)
def test_real_order_bundle_failure_modes(attempts, responses, mode, axis):
    fields = {
        "broker_submit_attempt_count": str(attempts),
        "broker_submit_success_response_count": str(responses),
        "order_bundle_failure_mode": mode,
    }
    exact = inspect(
        events("budget_pass", "latency_pass", ("order_bundle_failed", fields))
    )
    assert exact["axis_terminal_causal_attempt_counts"][axis] == 1


def test_unknown_or_inconsistent_broker_failure_is_explicit_gap():
    exact = inspect(events("budget_pass", "latency_pass", "order_bundle_failed"))
    assert exact["unclassified_terminal_attempt_count"] == 1
    assert exact["status"] == "source_quality_gap_excluded"
    assert exact["terminal_causal_attempt_count"] == 0


@pytest.mark.parametrize(
    "reason", ["ai_engine_unavailable", "above_best_ask", "skip_low_confidence"]
)
def test_nonblocking_price_fallback_is_not_causal(reason):
    exact = inspect(
        events(
            "budget_pass",
            "latency_pass",
            ("entry_ai_price_canary_fallback", {"reason": reason}),
        )
    )
    assert exact["axis_terminal_causal_attempt_counts"]["PRICE_REVALIDATION"] == 0
    assert exact["pending_attempt_count"] == 1


def test_budget_retry_preserves_prior_latency_block_not_false_recovery():
    exact = inspect(
        events(
            "budget_pass",
            ("latency_block", {"reason": "latency_state_danger"}),
            "budget_pass",
        )
    )
    assert exact["attempt_count"] == 2
    assert exact["axis_terminal_causal_attempt_counts"]["LATENCY_PRE_SUBMIT"] == 1
    assert exact["axis_later_progress_attempt_counts"]["LATENCY_PRE_SUBMIT"] == 0
    assert exact["pending_attempt_count"] == 1


def test_explicit_attempts_never_borrow_latency_pass():
    seq = [
        (stage, {"main_lifecycle_attempt_id": key})
        for stage, key in (
            ("budget_pass", "A"),
            ("latency_pass", "A"),
            ("pre_submit_price_guard_block", "A"),
            ("budget_pass", "B"),
            ("order_bundle_submitted", "B"),
        )
    ]
    exact = inspect(events(*seq))
    assert exact["denominator_exact_attempt_counts"]["order_bundle_submitted"] == 0
    assert exact["stage_order_violation_event_count"] == 1
    assert exact["axis_terminal_causal_attempt_counts"]["PRICE_REVALIDATION"] == 1


def test_real_downstream_pass_recovers_same_attempt():
    exact = inspect(
        events(
            "budget_pass",
            ("latency_block", {"reason": "latency_state_danger"}),
            "latency_pass",
            "order_bundle_submitted",
        )
    )
    assert exact["attempt_count"] == 1
    assert exact["terminal_causal_attempt_count"] == 0
    assert exact["submitted_attempt_count"] == 1


def test_unknown_terminal_is_not_silent_success():
    exact = inspect(events("ai_confirmed", "blocked_undefined_new_guard"))
    assert exact["unclassified_terminal_attempt_count"] == 1
    assert exact["status"] == "source_quality_gap_excluded"


def test_duplicate_rows_do_not_start_retries():
    rows = events(
        "budget_pass",
        ("latency_block", {"reason": "latency_state_danger"}),
        "budget_pass",
    )
    exact = inspect(rows + rows)
    assert exact["attempt_count"] == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "denominator",
        "ratio",
        "critical",
        "ledger",
        "fractional",
        "axis_list",
        "schema",
        "record_binding",
    ],
)
def test_shared_validator_rejects_decision_or_census_drift(mutation):
    report = make_report()
    contract = report["entry_submit_drought_contract"]
    if mutation == "denominator":
        contract["stage_unique"]["budget_pass"] = 999
    elif mutation == "ratio":
        contract["ratios"]["submitted_to_ai_unique_pct"] = 50
    elif mutation == "critical":
        contract["critical"] = False
    elif mutation == "ledger":
        contract["exact_attempt_contract"]["attempt_ledger"].pop()
    elif mutation == "fractional":
        contract["exact_attempt_contract"]["terminal_causal_attempt_count"] = 20.5
    elif mutation == "axis_list":
        contract["causal_bottleneck_axes"] = [{}]
    elif mutation == "record_binding":
        contract["exact_attempt_contract"]["attempt_ledger"][0]["record_id"] = ""
    else:
        report["schema_version"] = 3
    assert validate_submit_drought_contract(report, contract)["status"] == "invalid"


def test_runtime_history_excludes_bad_scope_and_keeps_valid_survivor(
    monkeypatch, tmp_path
):
    report = make_report()
    by_scope = report["entry_submit_drought_contract"]["by_venue_session"]
    by_scope["NXT|NXT_AFTERMARKET"] = deepcopy(by_scope["KRX|KRX_REGULAR"])
    by_scope["NXT|NXT_AFTERMARKET"].pop("exact_attempt_contract")
    path = tmp_path / "buy_funnel_sentinel_2026-09-07.json"
    path.write_text(json.dumps(report))
    monkeypatch.setattr(
        controller,
        "load_source_quality_preflight",
        lambda day: {"status": "pass", "tuning_input_allowed": True},
    )
    day = controller._drought_day_summary(path)
    assert day["source_quality_pass"] is True
    assert [r["scope"] for r in day["eligible_scopes"]] == ["KRX|KRX_REGULAR"]
    assert day["excluded_sentinel_scopes"] == ["NXT|NXT_AFTERMARKET"]
    by_scope["KRX|KRX_REGULAR"].pop("exact_attempt_contract")
    path.write_text(json.dumps(report))
    day = controller._drought_day_summary(path)
    assert day["source_quality_pass"] is False
    assert day["addressable"] is False


def test_preopen_requires_bound_exact_evidence_not_just_flags():
    from src.engine import threshold_cycle_preopen_apply as preopen
    from src.tests.test_threshold_cycle_preopen_apply import (
        _valid_entry_recheck_candidate,
    )

    candidate = _valid_entry_recheck_candidate()
    assert preopen._entry_recheck_drought_candidate_contract_error(candidate) == ""
    day = candidate["source_metrics"]["drought_conditional_policy"]["history"][0]
    day["eligible_scopes"][0].pop("sentinel_evidence")
    assert (
        preopen._entry_recheck_drought_candidate_contract_error(candidate)
        == "drought_sentinel_exact_contract_invalid"
    )


def test_scope_evidence_rejects_date_scope_and_payload_drift():
    report = make_report()
    scope = "KRX|KRX_REGULAR"
    contract = report["entry_submit_drought_contract"]["by_venue_session"][scope]
    evidence = make_scope_evidence(report, scope, contract)
    assert validate_scope_evidence(evidence, source_date="2026-09-07", scope=scope)
    assert not validate_scope_evidence(evidence, source_date="2026-09-08", scope=scope)
    assert not validate_scope_evidence(
        evidence, source_date="2026-09-07", scope="NXT|NXT_AFTERMARKET"
    )
    evidence["contract"]["stage_unique"]["budget_pass"] = 999
    assert not validate_scope_evidence(evidence, source_date="2026-09-07", scope=scope)


@pytest.mark.parametrize(
    "stage", ["blocked_liquidity", "blocked_zero_qty", "entry_armed_expired"]
)
def test_wider_upstream_diagnostics_do_not_widen_recheck_authority(stage):
    report = make_report(terminal_stage=stage)
    contract = report["entry_submit_drought_contract"]
    assert contract["causal_bottleneck_axes"] == ["UPSTREAM_GATE"]
    row = scope_summary("KRX|KRX_REGULAR", contract)
    assert row["critical"] is True
    assert row["addressable"] is False


def test_interleaved_explicit_attempts_keep_their_own_stages():
    seq = [
        (stage, {"main_lifecycle_attempt_id": key})
        for stage, key in (
            ("budget_pass", "A"),
            ("budget_pass", "B"),
            ("latency_pass", "A"),
            ("order_bundle_submitted", "A"),
            ("order_bundle_submitted", "B"),
        )
    ]
    exact = inspect(events(*seq))
    assert exact["attempt_count"] == 2
    assert exact["submitted_attempt_count"] == 1
    assert (
        exact["denominator_stage_order_violation_events"]["order_bundle_submitted"] == 1
    )


def test_reused_scanner_promotion_id_does_not_reuse_previous_cycle_pass():
    # Runtime lifecycle attempt IDs originate from scanner promotions and may
    # persist across repeated entry evaluations on the same record.
    seq = [
        (stage, {"main_lifecycle_attempt_id": "promotion-A"})
        for stage in (
            "budget_pass",
            "latency_pass",
            "pre_submit_price_guard_block",
            "budget_pass",
            "order_bundle_submitted",
        )
    ]
    exact = inspect(events(*seq))
    assert exact["attempt_count"] == 2
    assert exact["axis_terminal_causal_attempt_counts"]["PRICE_REVALIDATION"] == 1
    assert exact["submitted_attempt_count"] == 0
    assert exact["stage_order_violation_event_count"] == 1


def test_inherited_override_text_on_progress_is_not_an_upstream_block():
    row = events(("budget_pass", {"reason": "previous_ai_score_50_buy_hold_override"}))[
        0
    ]
    assert sentinel._submit_drought_axis_for_event(row) is None


def test_conversion_does_not_accept_current_date_schema_downgrade():
    from src.engine.automation import conversion_lane

    report = make_report()
    report["schema_version"] = 3
    assert conversion_lane._submit_drought_causal_axes(report) == []


def test_verifier_checks_downstream_exact_generation_copy():
    from src.engine import verify_threshold_cycle_postclose_chain as verifier

    report = make_report()
    report["followup"] = {"route": "entry_submit_drought_auto_workorder"}
    contract = report["entry_submit_drought_contract"]
    summary = {
        "primary": "SUBMIT_DROUGHT_CRITICAL",
        "entry_submit_drought_contract": contract,
    }
    ev = {
        "buy_funnel_sentinel": summary,
        "entry_funnel": {"entry_submit_drought_handoff_selected": True},
    }
    runtime = {
        "buy_funnel_sentinel": deepcopy(summary),
        "summary": {"entry_submit_drought_handoff_selected": True},
    }
    workorder = {
        "orders": [
            {"order_id": key}
            for key in verifier.ENTRY_SUBMIT_DROUGHT_REQUIRED_ORDER_IDS
        ]
    }
    before = verifier._buy_funnel_submit_drought_handoff_status(
        report, {}, ev, runtime, workorder
    )
    assert before["status"] == "pass", before
    runtime["buy_funnel_sentinel"]["entry_submit_drought_contract"]["stage_unique"][
        "ai_confirmed"
    ] = 999
    after = verifier._buy_funnel_submit_drought_handoff_status(
        report, {}, ev, runtime, workorder
    )
    assert after["status"] == "fail"
    assert after["root_cause_closure_status"] == "artifact_regeneration_required"
    assert after["unresolved_root_cause_present"] is True
    assert "runtime_approval_summary_sentinel_contract_generation_mismatch" in str(
        after
    )


@pytest.mark.parametrize("use_summary", [False, True])
@pytest.mark.parametrize("raw_terminal_present", [False, True])
def test_compacted_terminal_is_exclusion_evidence_not_an_invented_attempt(
    monkeypatch, tmp_path, use_summary, raw_terminal_present
):
    from src.tests.test_buy_funnel_sentinel import _event, _write_events

    day = "2026-09-07"
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(sentinel, "previous_trading_day_with_events", lambda _: None)
    terminal = _event(
        day,
        "10:00:10",
        "blocked_overbought",
        record_id=1,
        fields={"reason": "near_day_high"},
    )
    rows = [_event(day, "10:00:00", "ai_confirmed", record_id=1)]
    if raw_terminal_present:
        rows.append(terminal)
    _write_events(tmp_path, day, rows)
    summary_dir = tmp_path / "pipeline_event_summaries"
    summary_dir.mkdir()
    producer_row = {
        "pipeline": "ENTRY_PIPELINE",
        "stage": "blocked_overbought",
        "stock_code": "000001",
        "stock_name": "테스트종목",
        "bucket_start": f"{day}T10:00:00",
        "event_count": 1,
        "first_seen": f"{day}T10:00:10",
        "last_seen": f"{day}T10:00:10",
        "reason_label": sentinel._blocker_label_from_stage_fields(
            terminal["stage"], terminal["fields"]
        ),
    }
    (summary_dir / f"pipeline_event_producer_summary_{day}.jsonl").write_text(
        json.dumps(producer_row) + "\n"
    )
    report = sentinel.build_buy_funnel_sentinel_report(
        day, as_of=datetime(2026, 9, 7, 10, 1), use_cache=True, use_summary=use_summary
    )
    contract = report["entry_submit_drought_contract"]
    assert validate_submit_drought_contract(report, contract)["status"] == (
        "pass" if raw_terminal_present else "source_quality_blocked"
    )
    exact = contract["exact_attempt_contract"]
    assert exact["summary_terminal_identity_gap_events"] == int(
        not raw_terminal_present
    )
    assert exact["axis_terminal_causal_attempt_counts"]["UPSTREAM_GATE"] == int(
        raw_terminal_present
    )
    scope = "KRX|KRX_REGULAR"
    evidence = make_scope_evidence(report, scope, contract["by_venue_session"][scope])
    assert (
        validate_scope_evidence(evidence, source_date=day, scope=scope)
        is raw_terminal_present
    )


@pytest.mark.parametrize("stage", sorted(sentinel.UPSTREAM_BLOCK_STAGES))
def test_upstream_terminals_always_survive_producer_suppression(stage):
    from src.engine.pipeline_event_summary import payload_has_lossless_authority

    assert payload_has_lossless_authority(
        {"pipeline": "ENTRY_PIPELINE", "stage": stage, "fields": {}}
    )
