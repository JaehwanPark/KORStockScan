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


def test_natural_price_terminal_and_retry_use_one_common_refresh_ledger():
    parent = {"scanner_promotion_id": "SCANPROM-010170-P"}
    ai = {**parent, "main_lifecycle_attempt_id": parent["scanner_promotion_id"]}
    refresh = {**parent, "pre_submit_quote_refresh_applied": "true"}
    rows = events(
        ("budget_pass", parent),
        ("latency_pass", refresh),
        (
            "entry_submit_revalidation_block",
            {**parent, "block_reason": "standard_stale_context_or_quote"},
        ),
        ("budget_pass", parent),
        ("latency_pass", refresh),
        ("ai_confirmed", ai),
        ("pre_submit_entry_ai_authority_guard_block", parent),
    )
    exact = inspect(rows)
    assert exact["attempt_count"] == 2
    assert exact["pending_attempt_count"] == 0
    assert exact["axis_terminal_causal_attempt_counts"]["PRICE_REVALIDATION"] == 1
    assert (
        exact["axis_terminal_causal_attempt_counts"]["ENTRY_AI_AUTHORITY_REVALIDATION"]
        == 1
    )
    summary = sentinel._summarize_events(
        rows, start_at=rows[0].emitted_at, end_at=rows[-1].emitted_at
    )
    assert summary["quote_freshness_refresh_latency_pass_count"] == 2
    assert summary["quote_freshness_refresh_latency_pass_record_count"] == 1
    assert summary["quote_freshness_refresh_latency_pass_attempt_count"] == 2
    assert summary["quote_freshness_recovered_downstream_counts"] == {
        "price_guard_or_revalidation": 1,
        "entry_ai_authority_revalidation": 1,
    }


def test_explicit_zero_refresh_blocks_are_not_replaced_by_subtraction():
    root = sentinel._latency_drought_root_cause_summary(
        {
            "quote_freshness_refresh_attempted_count": 3,
            "quote_freshness_refresh_applied_count": 1,
            "quote_freshness_still_latency_blocked_after_refresh_count": 0,
        }
    )
    assert (
        root["quote_freshness_attribution"]["still_latency_blocked_after_refresh_count"]
        == 0
    )


@pytest.mark.parametrize("exclude_summary", [False, True])
def test_price_and_async_rows_survive_cache_and_producer_compaction(exclude_summary):
    from src.engine.pipeline_event_summary import SUMMARY_STAGES

    for stage in (
        "entry_submit_revalidation_block",
        "entry_price_canary_submit_block",
        "pre_submit_entry_ai_authority_async_pending",
        "entry_submit_attempt_finished",
    ):
        payload = {
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "emitted_at": "2026-09-08T09:56:44.824654",
            "stage": stage,
            "record_id": 41181,
            "stock_code": "010170",
            "stock_name": "fixture",
            "fields": {"block_reason": "standard_stale_context_or_quote"},
        }
        assert sentinel._payload_to_cache_row(
            payload, exclude_summary_stages=exclude_summary
        )
        assert stage not in SUMMARY_STAGES


def test_old_lossless_cache_is_rebuilt_before_new_contract_publish(
    monkeypatch, tmp_path
):
    from src.tests.test_buy_funnel_sentinel import _event, _write_events

    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    _write_events(
        tmp_path,
        day,
        [
            _event(day, "10:00:00", "budget_pass", record_id=1),
            _event(day, "10:00:01", "entry_submit_revalidation_block", record_id=1),
        ],
    )
    parser = sentinel._payload_to_cache_row
    with monkeypatch.context() as old:
        old.setattr(sentinel, "LOSSLESS_EVENT_CACHE_SCHEMA_VERSION", 10)
        old.setattr(
            sentinel,
            "_payload_to_cache_row",
            lambda payload, **kw: (
                None
                if payload["stage"] == "entry_submit_revalidation_block"
                else parser(payload, **kw)
            ),
        )
        prior = sentinel.load_pipeline_events(
            day, use_cache=True, exclude_summary_stages=True
        )
        assert len(prior) == 1
    rebuilt = sentinel.load_pipeline_events(
        day, use_cache=True, exclude_summary_stages=True
    )
    assert len(rebuilt) == 2
    assert (
        sentinel._exact_submit_drought_axis_summary(rebuilt)[
            "axis_terminal_causal_attempt_counts"
        ]["PRICE_REVALIDATION"]
        == 1
    )


def test_previous_partition_cannot_be_relabelled_as_current_without_rebuild():
    report = make_report()
    report["schema_version"] = 5
    assert (
        validate_submit_drought_contract(
            report, report["entry_submit_drought_contract"], require_current=True
        )["status"]
        == "invalid"
    )
    report["schema_version"] = 6
    contract = report["entry_submit_drought_contract"]
    contract["exact_attempt_contract"]["schema_version"] = 2
    assert (
        validate_submit_drought_contract(report, contract, require_current=True)[
            "status"
        ]
        == "invalid"
    )


def test_promotion_change_before_ai_does_not_leave_old_latency_pending():
    rows = events(
        (
            "ai_confirmed",
            {
                "main_lifecycle_attempt_id": "SCANPROM-old",
                "scanner_promotion_id": "SCANPROM-old",
            },
        ),
        ("budget_pass", {"scanner_promotion_id": "SCANPROM-new"}),
        ("latency_pass", {"scanner_promotion_id": "SCANPROM-new"}),
        (
            "ai_confirmed",
            {
                "main_lifecycle_attempt_id": "SCANPROM-new",
                "scanner_promotion_id": "SCANPROM-new",
            },
        ),
        (
            "pre_submit_entry_ai_authority_guard_block",
            {"scanner_promotion_id": "SCANPROM-new"},
        ),
    )
    exact = inspect(rows)
    assert exact["attempt_count"] == 2
    assert exact["pending_attempt_count"] == 0
    assert exact["unclassified_terminal_attempt_count"] == 1
    assert exact["attempt_ledger"][1]["stages"] == [
        "budget_pass",
        "latency_pass",
        "ai_confirmed",
    ]


def test_partial_main_id_on_same_promotion_cannot_resume_old_timeout_cycle():
    parent = {"scanner_promotion_id": "SCANPROM-P"}
    ai = {**parent, "main_lifecycle_attempt_id": "SCANPROM-P"}
    rows = events(
        ("budget_pass", parent),
        ("latency_pass", parent),
        ("ai_confirmed", ai),
        ("pre_submit_entry_ai_authority_guard_block", parent),
        ("budget_pass", parent),
        ("latency_pass", parent),
        ("ai_confirmed", ai),
        ("pre_submit_entry_ai_authority_guard_block", parent),
    )
    exact = inspect(rows)
    assert exact["attempt_count"] == 2
    assert exact["pending_attempt_count"] == 0
    assert exact["terminal_causal_attempt_count"] == 2


def test_unclosed_retry_is_lineage_gap_not_normal_pending():
    exact = inspect(events("budget_pass", "latency_pass", "budget_pass"))
    assert exact["pending_attempt_count"] == 1
    assert exact["unclassified_terminal_attempt_count"] == 1
    assert (
        exact["attempt_ledger"][0]["lineage_gap_reason"]
        == "new_evaluation_without_previous_terminal"
    )


@pytest.mark.parametrize(
    "stage,axis",
    [
        ("entry_price_canary_submit_block", "PRICE_REVALIDATION"),
        ("rising_missed_tick_speed_entry_block", "UPSTREAM_GATE"),
        ("real_weak_ai_micro_entry_block", "UPSTREAM_GATE"),
        ("pre_submit_micro_unavailable_block", "UPSTREAM_GATE"),
        ("rising_missed_reversal_pre_submit_block", "UPSTREAM_GATE"),
    ],
)
def test_actual_before_latency_terminals_are_preserved_across_retry(stage, axis):
    exact = inspect(events("budget_pass", stage, "budget_pass"))
    assert exact["attempt_count"] == 2
    assert exact["axis_terminal_causal_attempt_counts"][axis] == 1
    assert exact["pending_attempt_count"] == 1
    assert exact["unclassified_terminal_attempt_count"] == 0


def test_async_wait_is_explicit_and_does_not_mask_later_terminal():
    rows = events(
        "budget_pass",
        ("latency_pass", {"pre_submit_quote_refresh_applied": "true"}),
        "pre_submit_entry_ai_authority_async_pending",
    )
    exact = inspect(rows)
    assert exact["pending_attempt_count"] == 1
    assert exact["unclassified_terminal_attempt_count"] == 0
    summary = sentinel._summarize_events(
        rows, start_at=rows[0].emitted_at, end_at=rows[-1].emitted_at
    )
    assert summary["quote_freshness_recovered_downstream_counts"] == {
        "entry_ai_authority_async_pending": 1
    }


def test_submit_observation_id_is_call_local_nested_and_exception_safe():
    from concurrent.futures import ThreadPoolExecutor
    from src.engine.monitoring.entry_attempt_identity import (
        observe_submit_attempt,
        submit_attempt_fields,
    )

    stock = {"id": 41181, "scanner_promotion_id": "parent"}
    seen = []

    @observe_submit_attempt
    def run(stock, code, *, nested=False, fail=False):
        before = submit_attempt_fields(stock, code)
        seen.append(before["entry_submit_attempt_id"])
        assert submit_attempt_fields({"id": 99}, code) == {}
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(submit_attempt_fields, stock, code).result() == {}
        if nested:
            run(stock, code)
            assert submit_attempt_fields(stock, code) == before
        if fail:
            raise ValueError("fixture")
        return before

    first = run(stock, "010170", nested=True)
    assert run(stock, "010170") != first
    with pytest.raises(ValueError):
        run(stock, "010170", fail=True)
    assert submit_attempt_fields(stock, "010170") == {}
    assert len(seen) == len(set(seen))
    assert stock == {"id": 41181, "scanner_promotion_id": "parent"}


def test_true_submit_ids_partition_retries_even_with_shared_promotion():
    def f(key):
        return {
            "entry_submit_attempt_id": key,
            "scanner_promotion_id": "SCANPROM-P",
            "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
            "entry_submit_attempt_authority": "observation_only",
        }

    exact = inspect(
        events(
            ("budget_pass", f("A")),
            ("latency_pass", f("A")),
            ("entry_submit_revalidation_block", f("A")),
            ("budget_pass", f("B")),
            ("order_bundle_submitted", f("B")),
        )
    )
    assert exact["attempt_count"] == 2
    assert exact["submitted_attempt_count"] == 0
    assert exact["stage_order_violation_event_count"] == 1


def test_finished_call_without_terminal_is_not_perpetual_pending():
    fields = {
        "entry_submit_attempt_id": "A",
        "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
        "entry_submit_attempt_authority": "observation_only",
    }
    exact = inspect(
        events(
            ("budget_pass", fields),
            (
                "entry_submit_attempt_finished",
                {
                    **fields,
                    "submit_call_outcome": "returned_false",
                },
            ),
        )
    )
    assert exact["pending_attempt_count"] == 0
    assert exact["unclassified_terminal_attempt_count"] == 1


def test_duplicate_call_local_submit_does_not_create_new_attempt_or_veto():
    fields = {
        "entry_submit_attempt_id": "A",
        "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
        "entry_submit_attempt_authority": "observation_only",
    }
    exact = inspect(
        events(
            *[
                (stage, fields)
                for stage in (
                    "budget_pass",
                    "latency_pass",
                    "order_bundle_submitted",
                    "order_bundle_submitted",
                    "pre_submit_price_guard_block",
                )
            ]
        )
    )
    assert exact["attempt_count"] == 1
    assert exact["submitted_attempt_count"] == 1
    assert exact["terminal_causal_attempt_count"] == 0


def test_exception_after_async_wait_is_not_normal_waiting():
    fields = {
        "entry_submit_attempt_id": "A",
        "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
        "entry_submit_attempt_authority": "observation_only",
    }
    exact = inspect(
        events(
            ("budget_pass", fields),
            ("pre_submit_entry_ai_authority_async_pending", fields),
            (
                "entry_submit_attempt_finished",
                {**fields, "submit_call_outcome": "raised"},
            ),
        )
    )
    assert exact["pending_attempt_count"] == 0
    assert exact["unclassified_terminal_attempt_count"] == 1


def test_finished_call_preserves_submit_or_explicit_wait():
    fields = {
        "entry_submit_attempt_id": "A",
        "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
        "entry_submit_attempt_authority": "observation_only",
    }
    for tail, state in (
        ("order_bundle_submitted", "submitted"),
        ("pre_submit_entry_ai_authority_async_pending", "pending"),
    ):
        exact = inspect(
            events(
                ("budget_pass", fields),
                ("latency_pass", fields),
                (tail, fields),
                (
                    "entry_submit_attempt_finished",
                    {
                        **fields,
                        "submit_call_outcome": (
                            "returned_true"
                            if state == "submitted"
                            else "returned_false"
                        ),
                    },
                ),
            )
        )
        assert exact["attempt_count"] == 1
        assert exact["attempt_ledger"][0]["state"] == state


def test_malformed_call_identity_cannot_support_causal_or_refresh_counts():
    exact = inspect(
        events(
            ("budget_pass", {"entry_submit_attempt_id": "untrusted"}),
            (
                "entry_submit_revalidation_block",
                {"entry_submit_attempt_id": "untrusted"},
            ),
        )
    )
    assert exact["terminal_causal_attempt_count"] == 0
    assert exact["denominator_exact_attempt_counts"]["budget_pass"] == 0
    assert exact["unclassified_terminal_attempt_count"] == 1


def test_unbound_event_cannot_borrow_one_of_two_concurrent_call_ids():
    def f(key):
        return {
            "entry_submit_attempt_id": key,
            "entry_submit_attempt_schema": "call_local_submit_attempt_v1",
            "entry_submit_attempt_authority": "observation_only",
            "scanner_promotion_id": "P",
        }

    exact = inspect(
        events(
            ("budget_pass", f("A")),
            ("budget_pass", f("B")),
            ("latency_pass", {"scanner_promotion_id": "P"}),
        )
    )
    assert exact["denominator_exact_attempt_counts"]["latency_pass"] == 0
    assert exact["unclassified_terminal_attempt_count"] == 1
    assert exact["pending_attempt_count"] == 2


def test_completion_observer_cannot_change_return_or_mask_original_exception(caplog):
    from src.engine.monitoring.entry_attempt_identity import (
        observe_submit_attempt,
        submit_attempt_fields,
    )

    recorded = []

    def finish(stock, code, outcome):
        recorded.append((outcome, submit_attempt_fields(stock, code)))
        raise RuntimeError("observer failure")

    @observe_submit_attempt(on_finish=finish)
    def run(stock, code, fail=False):
        if fail:
            raise ValueError("original")
        return False

    assert run({"id": 1}, "000001") is False
    with pytest.raises(ValueError, match="original"):
        run({"id": 1}, "000001", fail=True)
    assert [r[0] for r in recorded] == ["returned_false", "raised"]
    assert all(r[1]["entry_submit_attempt_id"] for r in recorded)
    assert "Submit completion telemetry failed" in caplog.text
    assert submit_attempt_fields({"id": 1}, "000001") == {}


def test_live_submit_guard_and_logger_share_call_id_without_order_io(monkeypatch):
    from src.engine import sniper_state_handlers as sh

    emitted = []
    monkeypatch.setattr(
        sh, "emit_pipeline_event", lambda *a, **kw: emitted.append((a[3], kw["fields"]))
    )
    for name in (
        "_remember_scanner_terminal_block",
        "observe_candidate_transition_safe",
        "_maybe_register_rising_missed_nxt_downstream_block_sampler",
    ):
        monkeypatch.setattr(sh, name, lambda *a, **kw: None)
    stock = {
        "id": 41181,
        "name": "TEST",
        "strategy": "SCALPING",
        "scanner_promotion_id": "SCANPROM-P",
        "entry_submit_identity_reconciliation_required": True,
    }
    runtime = {
        "strategy": "SCALPING",
        "ratio": 0.1,
        "curr_price": 1000,
        "liquidity_value": 0,
        "msg": "",
        "now_ts": 1,
        "cooldowns": {},
        "alerted_stocks": set(),
    }
    assert (
        sh._submit_watching_triggered_entry(stock, "010170", {}, None, runtime) is False
    )
    assert [stage for stage, _ in emitted] == [
        "entry_submit_identity_reconciliation_blocked",
        "entry_submit_attempt_finished",
    ]
    first_id = emitted[0][1]["entry_submit_attempt_id"]
    assert emitted[1][1]["entry_submit_attempt_id"] == first_id
    assert emitted[1][1]["submit_call_outcome"] == "returned_false"
    from src.engine import observation_source_quality_audit as audit

    contract = audit.STAGE_CONTRACTS["entry_submit_attempt_finished"]

    def violations(fields):
        return audit._row_contract_violations(
            "entry_submit_attempt_finished", {"fields": fields}, contract
        )

    assert not any(violations(emitted[1][1]).values())
    assert any(violations({**emitted[1][1], "allowed_runtime_apply": True}).values())
    assert (
        sh._submit_watching_triggered_entry(stock, "010170", {}, None, runtime) is False
    )
    assert emitted[2][1]["entry_submit_attempt_id"] != first_id
    assert stock["entry_submit_identity_reconciliation_required"] is True
    sh._log_entry_pipeline(
        stock, "010170", "budget_pass", entry_submit_attempt_id="spoofed"
    )
    assert "entry_submit_attempt_id" not in emitted[-1][1]


def test_identity_allocation_failure_does_not_skip_original_guard(monkeypatch, caplog):
    from src.engine.monitoring import entry_attempt_identity as identity

    def fail():
        raise OSError("fixture entropy failure")

    monkeypatch.setattr(identity, "uuid4", fail)
    called = []

    @identity.observe_submit_attempt
    def run(stock, code):
        called.append(True)
        assert identity.submit_attempt_fields(stock, code) == {}
        return False

    assert run({"id": 1}, "000001") is False
    assert called == [True]
    assert "Submit identity telemetry failed" in caplog.text


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
