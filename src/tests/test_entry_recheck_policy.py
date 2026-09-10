"""Regression tests for report -> PREOPEN -> runtime/receipt recheck contracts."""

import json
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest

from src.engine.scalping import entry_ai_gate_backtest as report
from src.engine.scalping import entry_recheck_policy as policy
from src.engine import threshold_cycle_preopen_apply as preopen
from src.engine import backfill_threshold_cycle_events as backfill
from src.utils import pipeline_event_logger as logger


def history(
    dates=("2026-09-02", "2026-09-03", "2026-09-04"),
    *,
    ai=100,
    budget=10,
    submitted=0,
    axis="UPSTREAM_GATE",
):
    rows = []
    critical = (ai >= 20 and submitted / ai < 0.2) or (
        budget >= 3 and submitted / budget <= 0.1
    )
    for day in dates:
        scope = policy.scope_summary(
            "KRX|KRX_REGULAR",
            {
                "stage_unique": {
                    "ai_confirmed": ai,
                    "budget_pass": budget,
                    "order_bundle_submitted": submitted,
                },
                "primary": "SUBMIT_DROUGHT_CRITICAL" if critical else "NORMAL",
                "critical": critical,
                "causal_bottleneck_axes": [axis],
            },
        )
        rows.append(
            {
                "source_date": day,
                "source_quality_pass": True,
                "denominator_floor_passed": scope["denominator_floor_passed"],
                "critical": scope["critical"],
                "addressable": scope["addressable"],
                "eligible_scopes": [scope],
            }
        )
    return rows


def exact(*, armed=10, submitted=10, completed=10, paired=10, ev=0.03, net=15):
    return {
        "identity_conflict_count": 0,
        "contract_gap_count": 0,
        "invalid_json_row_count": 0,
        "exact_evaluated_count": max(armed, submitted, completed, paired),
        "exact_armed_count": armed,
        "exact_direct_submitted_count": submitted,
        "exact_filled_count": completed,
        "exact_completed_count": completed,
        "exact_paired_economic_sample": paired,
        "exact_profit_sample": paired,
        "exact_net_pnl_sample": paired,
        "paired_economics_by_scope": (
            {
                "KRX|KRX_REGULAR": {
                    "paired_sample": paired,
                    "equal_weight_avg_profit_pct": ev,
                    "realized_net_pnl_krw": net,
                }
            }
            if paired
            else {}
        ),
        "equal_weight_avg_profit_pct": ev,
        "realized_net_pnl_krw": net,
        "funnel_by_scope": {
            "KRX|KRX_REGULAR": {
                "exact_evaluated_count": max(armed, submitted, completed, paired),
                "exact_armed_count": armed,
                "exact_direct_submitted_count": submitted,
                "exact_filled_count": completed,
                "exact_completed_count": completed,
                "exact_paired_economic_sample": paired,
            }
        },
        "paired_economics_by_scope_and_cohort": (
            {
                "KRX|KRX_REGULAR": {
                    "probe_only": {
                        "paired_sample": paired,
                        "equal_weight_avg_profit_pct": ev,
                        "realized_net_pnl_krw": net,
                        "decision_eligible": True,
                    },
                }
            }
            if paired
            else {}
        ),
    }


def decide(hist=None, evidence=None, previous=None):
    hist = history() if hist is None else hist
    return policy.controller_decision(
        history=hist,
        exact=exact() if evidence is None else evidence,
        previous=previous or {},
        target_date=hist[-1]["source_date"],
        baseline="2026-06-05",
    )


@pytest.mark.parametrize("latest_quality_pass", [False, True])
def test_rolling_current_contract_history_recovers_without_prior_live_economics(
    latest_quality_pass,
):
    old_history = history(dates=("2026-09-07", "2026-09-08", "2026-09-09"))
    old_history[0]["source_quality_pass"] = False
    no_live_outcomes = exact(
        armed=0, submitted=0, completed=0, paired=0, ev=None, net=None
    )
    blocked = decide(old_history, no_live_outcomes)
    assert blocked["history_complete"] is True
    assert blocked["history_source_quality_pass"] is False
    assert "drought_history_source_quality_gap" in blocked["stop_reasons"]
    assert blocked["desired_enabled"] is False
    assert blocked["controller_state"]["stop_latched"] is False

    next_history = old_history[1:] + history(dates=("2026-09-10",))
    next_history[-1]["source_quality_pass"] = latest_quality_pass
    recovered = decide(next_history, no_live_outcomes, blocked["controller_state"])
    assert recovered["expected_source_dates"] == [
        "2026-09-08", "2026-09-09", "2026-09-10"
    ]
    assert recovered["history_source_quality_pass"] is latest_quality_pass
    assert recovered["desired_enabled"] is latest_quality_pass
    assert (
        "drought_history_source_quality_gap" in recovered["stop_reasons"]
    ) is (not latest_quality_pass)
    assert recovered["intraday_escalation_allowed"] is False
    # The expired invalid day is not rewritten to manufacture a valid window.
    assert old_history[0]["source_quality_pass"] is False


def two_scope_case(krx=(10, 0.1, 100), nxt=(10, -0.1, -100)):
    hist = history()
    for day in hist:
        row = deepcopy(day["eligible_scopes"][0])
        row["scope"] = "NXT|NXT_AFTERMARKET"
        day["eligible_scopes"].append(row)
    n = krx[0] + nxt[0]
    evidence = exact(
        armed=n,
        submitted=n,
        completed=n,
        paired=n,
        ev=(krx[0] * krx[1] + nxt[0] * nxt[1]) / n,
        net=krx[2] + nxt[2],
    )
    for key in (
        "funnel_by_scope",
        "paired_economics_by_scope",
        "paired_economics_by_scope_and_cohort",
    ):
        evidence[key] = {}
    for scope, (pairs, ev, net) in zip(
        ("KRX|KRX_REGULAR", "NXT|NXT_AFTERMARKET"), (krx, nxt)
    ):
        evidence["funnel_by_scope"][scope] = {key: pairs for key in policy.FUNNEL_KEYS}
        metric = {
            "paired_sample": pairs,
            "equal_weight_avg_profit_pct": ev,
            "realized_net_pnl_krw": net,
        }
        evidence["paired_economics_by_scope"][scope] = metric
        evidence["paired_economics_by_scope_and_cohort"][scope] = {
            "probe_only": {**metric, "decision_eligible": True}
        }
    return hist, evidence


@pytest.mark.parametrize(
    "nxt,expected",
    [
        ((1, -2, -200), ["KRX|KRX_REGULAR", "NXT|NXT_AFTERMARKET"]),
        ((10, -0.1, -100), ["KRX|KRX_REGULAR"]),
    ],
)
def test_scope_losses_never_stop_profitable_other_market(nxt, expected):
    hist, evidence = two_scope_case(krx=(10, 0.3, 300), nxt=nxt)
    result = decide(hist, evidence)
    assert result["exact_attribution_source_quality_pass"] is True
    assert result["desired_enabled"] is True
    assert result["allowed_scopes"] == expected
    assert result["intraday_escalation_scopes"] == ["KRX|KRX_REGULAR"]


def test_full_and_partial_fill_cohorts_cannot_pool_to_pass_sample_floor():
    evidence = exact()
    metric = {
        "paired_sample": 5,
        "equal_weight_avg_profit_pct": 0.03,
        "realized_net_pnl_krw": 7.5,
        "decision_eligible": True,
    }
    evidence["paired_economics_by_scope_and_cohort"] = {
        "KRX|KRX_REGULAR": {
            "probe_residual_full_fill": dict(metric),
            "probe_residual_partial_fill": dict(metric),
        }
    }
    result = decide(evidence=evidence)
    assert result["exact_attribution_source_quality_pass"] is True
    assert result["desired_enabled"] is True
    assert result["intraday_escalation_allowed"] is False


def test_scope_stop_and_renewal_state_do_not_change_other_market_window():
    hist, evidence = two_scope_case(krx=(10, -0.1, -100), nxt=(10, 0.3, 300))
    first = decide(hist, evidence)
    assert first["allowed_scopes"] == ["NXT|NXT_AFTERMARKET"]
    later, empty = two_scope_case()
    for day, source_date in zip(later, ("2026-10-06", "2026-10-07", "2026-10-08")):
        day["source_date"] = source_date
        day["eligible_scopes"][0]["causal_bottleneck_axes"] = [
            "ENTRY_AI_AUTHORITY_REVALIDATION"
        ]
    empty = exact(armed=0, submitted=0, completed=0, paired=0)
    renewed = decide(later, empty, first["controller_state"])
    states = renewed["controller_state"]["scope_states"]
    assert renewed["allowed_scopes"] == ["KRX|KRX_REGULAR", "NXT|NXT_AFTERMARKET"]
    assert states["KRX|KRX_REGULAR"]["evidence_start_date"] == "2026-10-09"
    assert states["NXT|NXT_AFTERMARKET"]["evidence_start_date"] == "2026-06-05"


def test_unknown_scope_with_accepted_orders_fails_closed():
    evidence = exact()
    evidence["funnel_by_scope"]["UNKNOWN"] = evidence["funnel_by_scope"].pop(
        "KRX|KRX_REGULAR"
    )
    assert decide(evidence=evidence)["desired_enabled"] is False


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    for name in (
        "REPORT_DIR",
        "DROUGHT_REPORT_DIR",
        "THRESHOLD_CYCLE_DIR",
        "RUNTIME_ENV_DIR",
        "BUY_FUNNEL_SENTINEL_DIR",
    ):
        monkeypatch.setattr(report, name, tmp_path / name)
    monkeypatch.setattr(
        report,
        "load_source_quality_preflight",
        lambda day: {"status": "pass", "tuning_input_allowed": True},
    )
    return monkeypatch


@pytest.mark.parametrize("ai,budget", [(100, 0), (5, 3)])
def test_original_or_denominator_branches_remain_attainable(ai, budget):
    result = decide(history(ai=ai, budget=budget))
    assert result["desired_enabled"] is True
    assert result["allowed_scopes"] == ["KRX|KRX_REGULAR"]


def test_critical_and_addressable_cannot_join_across_scopes():
    hist = history(axis="LATENCY_PRE_SUBMIT")
    other = policy.scope_summary(
        "NXT|NXT_AFTERMARKET",
        {
            "stage_unique": {
                "ai_confirmed": 100,
                "budget_pass": 30,
                "order_bundle_submitted": 30,
            },
            "critical": False,
            "causal_bottleneck_axes": ["UPSTREAM_GATE"],
        },
    )
    for day in hist:
        day["eligible_scopes"].append(other)
        day["addressable"] = True
    assert decide(hist)["activation_triggered"] is False
    assert decide(hist)["allowed_scopes"] == []


@pytest.mark.parametrize("pairs", [0, 1, 9])
def test_incomplete_economic_pairs_never_escalate(pairs):
    result = decide(evidence=exact(paired=pairs))
    assert result["intraday_escalation_allowed"] is False
    assert result["desired_enabled"] is True


def test_intraday_escalation_is_approved_per_scope_not_all_or_nothing():
    hist = history()
    for day in hist:
        nxt = policy.scope_summary(
            "NXT|NXT_AFTERMARKET",
            {
                "stage_unique": {
                    "ai_confirmed": 100,
                    "budget_pass": 0,
                    "order_bundle_submitted": 0,
                },
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "critical": True,
                "causal_bottleneck_axes": ["UPSTREAM_GATE"],
            },
        )
        day["eligible_scopes"].append(nxt)
    evidence = exact()
    result = decide(hist, evidence)

    assert result["allowed_scopes"] == [
        "KRX|KRX_REGULAR",
        "NXT|NXT_AFTERMARKET",
    ]
    assert result["intraday_escalation_allowed"] is True
    assert result["intraday_escalation_scopes"] == ["KRX|KRX_REGULAR"]


@pytest.mark.parametrize(
    "ev,net", [(float("nan"), 15), (0.03, float("inf")), (-0.01, 15), (0.03, -1)]
)
def test_invalid_or_nonpositive_economics_cannot_escalate(ev, net):
    result = decide(evidence=exact(ev=ev, net=net))
    assert result["intraday_escalation_allowed"] is False
    assert result["stop_triggered"] is True


def test_stopped_episode_requires_new_evidence_not_elapsed_time():
    stopped = decide(evidence=exact(armed=20, submitted=1, completed=0, paired=0))
    assert stopped["controller_state"]["stop_latched"] is True
    later = history(("2026-10-06", "2026-10-07", "2026-10-08"))
    empty = exact(armed=0, submitted=0, completed=0, paired=0)
    unchanged = decide(later, empty, stopped["controller_state"])
    assert unchanged["desired_enabled"] is False
    changed = history(
        ("2026-10-06", "2026-10-07", "2026-10-08"),
        axis="ENTRY_AI_AUTHORITY_REVALIDATION",
    )
    renewed = decide(changed, empty, stopped["controller_state"])
    assert renewed["desired_enabled"] is True
    assert renewed["episode_renewed"] is True
    assert (
        renewed["controller_state"]["scope_states"]["KRX|KRX_REGULAR"][
            "evidence_start_date"
        ]
        == "2026-10-09"
    )
    assert renewed["intraday_escalation_allowed"] is False


def test_recovery_then_new_drought_can_renew_same_causal_scope():
    stopped = decide(evidence=exact(armed=20, submitted=1, completed=0, paired=0))
    recovered = decide(
        history(("2026-09-07", "2026-09-08", "2026-09-09"), submitted=30),
        previous=stopped["controller_state"],
    )
    assert recovered["controller_state"]["recovery_observed"] is True
    renewed = decide(
        history(("2026-09-10", "2026-09-11", "2026-09-14")),
        previous=recovered["controller_state"],
    )
    assert renewed["episode_renewed"] is True


def test_bad_source_cannot_record_recovery_or_renew_same_cause():
    stopped = decide(evidence=exact(armed=20, submitted=1, completed=0, paired=0))
    bad_history = history(("2026-09-07", "2026-09-08", "2026-09-09"), submitted=30)
    bad_history[-1]["source_quality_pass"] = False
    blocked = decide(bad_history, previous=stopped["controller_state"])
    assert blocked["controller_state"]["recovery_observed"] is False
    renewed = decide(
        history(("2026-09-10", "2026-09-11", "2026-09-14")),
        previous=blocked["controller_state"],
    )
    assert renewed["episode_renewed"] is False
    assert renewed["desired_enabled"] is False


def test_omitted_env_profile_recovers_and_preopen_rechecks_pairs(isolated):
    from src.tests.submit_drought_fixtures import bind_history

    isolated.setattr(
        report,
        "_load_json_with_status",
        lambda path: ({"env_overrides": {}}, {"status": "loaded", "path": str(path)}),
    )
    isolated.setattr(
        report,
        "_buy_funnel_drought_history",
        lambda *args, **kwargs: bind_history(history()),
    )
    isolated.setattr(
        report, "_entry_recheck_exact_attribution", lambda **kwargs: exact(paired=1)
    )
    result = report._drought_conditional_policy(
        target_date="2026-09-04", clean_baseline_date="2026-06-05"
    )
    candidate = report._entry_recheck_drought_candidate(
        target_date="2026-09-04",
        clean_baseline_date="2026-06-05",
        drought_policy=result,
    )[0]
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["recommended_values"]["enabled"] is True
    assert candidate["recommended_values"]["require_explicit_buy_action"] is False
    assert preopen._entry_recheck_drought_candidate_contract_error(candidate) == ""
    candidate["recommended_values"]["intraday_escalation_enabled"] = True
    assert (
        preopen._entry_recheck_drought_candidate_contract_error(candidate)
        == "drought_escalation_runtime_mismatch"
    )


def test_scope_stop_survives_producer_preopen_contract_without_global_off(isolated):
    from src.tests.submit_drought_fixtures import bind_history

    hist, evidence = two_scope_case()
    bind_history(hist)
    isolated.setattr(
        report,
        "_load_json_with_status",
        lambda path: ({"env_overrides": {}}, {"status": "loaded", "path": str(path)}),
    )
    isolated.setattr(
        report, "_buy_funnel_drought_history", lambda *args, **kwargs: hist
    )
    isolated.setattr(
        report, "_entry_recheck_exact_attribution", lambda **kwargs: evidence
    )
    result = report._drought_conditional_policy(
        target_date="2026-09-04", clean_baseline_date="2026-06-05"
    )
    candidate = report._entry_recheck_drought_candidate(
        target_date="2026-09-04",
        clean_baseline_date="2026-06-05",
        drought_policy=result,
    )[0]
    assert candidate["recommended_values"]["enabled"] is True
    assert candidate["recommended_values"]["allowed_scopes"] == "KRX|KRX_REGULAR"
    assert preopen._entry_recheck_drought_candidate_contract_error(candidate) == ""
    candidate["recommended_values"]["allowed_scopes"] += ",NXT|NXT_AFTERMARKET"
    assert preopen._entry_recheck_drought_candidate_contract_error(candidate)


def test_real_logger_general_sell_partition_recovers_missing_companion(
    isolated, tmp_path
):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 4, 10, 0, tzinfo=tz)

    isolated.setattr(logger, "DATA_DIR", tmp_path)
    isolated.setattr(logger, "datetime", FixedDateTime)
    isolated.setattr(logger, "_PRODUCER_COMPACTOR", None)
    isolated.setattr(logger, "_get_producer_compactor", lambda: None)
    isolated.setattr(
        logger,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )
    isolated.setattr(report, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    fields = {
        "entry_opportunity_recheck_attribution_schema": policy.ATTRIBUTION_VERSION,
        "entry_opportunity_recheck_armed_at": datetime(
            2026, 9, 4, 9, 0, tzinfo=timezone(timedelta(hours=9))
        ).timestamp(),
        "entry_opportunity_recheck_scope": "KRX|KRX_REGULAR",
        "entry_opportunity_recheck_economics_complete": True,
        "entry_opportunity_recheck_economics_schema": "entry_recheck_position_economics_v1",
        "entry_opportunity_recheck_economics_cohort": "probe_only",
        "entry_opportunity_recheck_economics_decision_eligible": True,
        "entry_opportunity_recheck_attempt_id": "eor-fixture",
        "entry_opportunity_recheck_armed": True,
        "entry_opportunity_recheck_submit_observed": True,
        "entry_opportunity_recheck_direct_submit": True,
        "entry_opportunity_recheck_broker_order_no": "B1",
        "entry_opportunity_recheck_requested_qty": 1,
        "entry_opportunity_recheck_fill_observed": True,
        "entry_opportunity_recheck_fill_order_no": "B1",
        "entry_opportunity_recheck_terminal_outcome": "sell_completed",
        "entry_opportunity_recheck_cost_adjusted_profit_pct": 0.03,
        "entry_opportunity_recheck_realized_net_pnl_krw": 15,
    }
    for _ in range(2):  # Durable outbox replay must not double-count.
        emitted = logger.emit_pipeline_event(
            "HOLDING_PIPELINE",
            "TEST",
            "005930",
            "sell_completed",
            record_id=7,
            fields=fields,
        )
        assert emitted["structured_append_succeeded"] is True
    evaluated_fields = {
        "entry_opportunity_recheck_attribution_schema": policy.ATTRIBUTION_VERSION,
        "entry_opportunity_recheck_attempt_id": "eor-fixture",
        "entry_opportunity_recheck_scope": "KRX|KRX_REGULAR",
        "entry_opportunity_recheck_reason": (
            "edge_wait_recovery_probe_intent_fresh_strong_micro"
        ),
    }
    emitted = logger.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "TEST",
        "005930",
        "entry_opportunity_recheck_evaluated",
        record_id=7,
        fields=evaluated_fields,
    )
    assert emitted["structured_append_succeeded"] is True
    logger.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "TEST",
        "005930",
        "entry_opportunity_recheck_probe_armed",
        record_id=7,
        fields=fields,
    )
    isolated.setattr(backfill, "DATA_DIR", tmp_path)
    isolated.setattr(backfill, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    backfill.backfill_threshold_cycle_events(
        "2026-09-04", max_cpu_busy_pct=101, max_iowait_pct=101, min_mem_available_mb=0
    )
    assert list(
        (
            tmp_path
            / "threshold_cycle/date=2026-09-04/family=statistical_action_weight"
        ).glob("*.jsonl")
    )
    result = report._entry_recheck_exact_attribution(
        start_date="2026-09-04", end_date="2026-09-04"
    )
    assert (
        result["exact_completed_count"] == result["exact_paired_economic_sample"] == 1
    )
    assert result["realized_net_pnl_krw"] == 15


def test_rejected_evaluations_with_old_arm_flags_never_create_conversion_stop(
    isolated, tmp_path
):
    path = report.THRESHOLD_CYCLE_DIR / (
        "date=2026-09-04/family=entry_opportunity_recheck_runtime/part-000001.jsonl"
    )
    path.parent.mkdir(parents=True)
    rows = [
        {
            "record_id": 7,
            "stock_code": "005930",
            "stage": "entry_opportunity_recheck_evaluated",
            "fields": {
                "entry_opportunity_recheck_attribution_schema": policy.ATTRIBUTION_VERSION,
                "entry_opportunity_recheck_attempt_id": f"rejected-{index}",
                "entry_opportunity_recheck_scope": "KRX|KRX_REGULAR",
                "entry_opportunity_recheck_reason": "symbol_recheck_cap_exhausted",
                "entry_opportunity_recheck_allowed": False,
                "entry_opportunity_recheck_armed": True,
                "entry_opportunity_recheck_armed_at": 1788483600,
            },
        }
        for index in range(20)
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows))
    result = report._entry_recheck_exact_attribution(
        start_date="2026-09-04", end_date="2026-09-04"
    )
    assert result["exact_evaluated_count"] == 20
    assert result["exact_armed_count"] == 0
    assert decide(evidence=result)["desired_enabled"] is True


@pytest.mark.parametrize(
    "gap", ["missing", "nan", "split_rows", "incomplete_receipt", "old_episode"]
)
def test_exact_aggregation_never_fabricates_paired_economics(isolated, tmp_path, gap):
    fields = {
        "entry_opportunity_recheck_attribution_schema": policy.ATTRIBUTION_VERSION,
        "entry_opportunity_recheck_attempt_id": "eor-test",
        "entry_opportunity_recheck_armed": True,
        "entry_opportunity_recheck_armed_at": datetime.fromisoformat(
            "2026-09-04T09:00:00+09:00"
        ).timestamp(),
        "entry_opportunity_recheck_scope": "KRX|KRX_REGULAR",
        "entry_opportunity_recheck_submit_observed": True,
        "entry_opportunity_recheck_direct_submit": True,
        "entry_opportunity_recheck_broker_order_no": "B1",
        "entry_opportunity_recheck_requested_qty": 1,
        "entry_opportunity_recheck_fill_observed": True,
        "entry_opportunity_recheck_fill_order_no": "B1",
        "entry_opportunity_recheck_terminal_outcome": "sell_completed",
        "entry_opportunity_recheck_economics_complete": True,
        "entry_opportunity_recheck_cost_adjusted_profit_pct": 0.003,
        "entry_opportunity_recheck_realized_net_pnl_krw": 1,
    }
    if gap in {"missing", "split_rows"}:
        fields["entry_opportunity_recheck_realized_net_pnl_krw"] = None
    elif gap == "nan":
        fields["entry_opportunity_recheck_cost_adjusted_profit_pct"] = float("nan")
    elif gap == "incomplete_receipt":
        fields["entry_opportunity_recheck_economics_complete"] = False
    else:
        fields["entry_opportunity_recheck_armed_at"] -= 86400
    row = {
        "record_id": 7,
        "stock_code": "005930",
        "stage": "sell_completed",
        "fields": fields,
    }
    rows = [row]
    if gap == "split_rows":
        rows.append(
            {
                **row,
                "fields": {
                    **fields,
                    "entry_opportunity_recheck_cost_adjusted_profit_pct": None,
                    "entry_opportunity_recheck_realized_net_pnl_krw": 1,
                },
            }
        )
    path = (
        report.THRESHOLD_CYCLE_DIR
        / "date=2026-09-04/family=statistical_action_weight/part-000001.jsonl"
    )
    path.parent.mkdir(parents=True)
    path.write_text("\n".join(json.dumps(row) for row in rows))
    result = report._entry_recheck_exact_attribution(
        start_date="2026-09-04", end_date="2026-09-04"
    )
    assert result["exact_paired_economic_sample"] == 0
    assert result["equal_weight_avg_profit_pct"] is None


def test_changed_source_cannot_renew_before_cooldown():
    stopped = decide(evidence=exact(armed=20, submitted=1, completed=0, paired=0))
    changed = history(
        ("2026-09-03", "2026-09-04", "2026-09-07"),
        axis="ENTRY_AI_AUTHORITY_REVALIDATION",
    )
    assert (
        decide(changed, previous=stopped["controller_state"])["desired_enabled"]
        is False
    )


def test_malformed_previous_state_fails_closed():
    result = decide(
        previous={
            "policy_version": policy.POLICY_VERSION,
            "evidence_start_date": "wrong",
        }
    )
    assert result["desired_enabled"] is False
    assert result["controller_state"]["invalid"] is True


@pytest.mark.parametrize("bad_metric", [[1], "invalid", True])
def test_malformed_scoped_economics_fails_closed(bad_metric):
    evidence = exact()
    evidence["paired_economics_by_scope"]["KRX|KRX_REGULAR"] = bad_metric
    result = decide(evidence=evidence)
    assert result["desired_enabled"] is False
    assert result["intraday_escalation_allowed"] is False


def test_known_bad_attempt_exclusion_does_not_block_valid_probe_evidence():
    evidence = exact(paired=1)
    evidence["identity_conflict_count"] = 1
    assert decide(evidence=evidence)["desired_enabled"] is False
    evidence["excluded_attempts"] = [
        {"attempt_id": "conflicting-attempt", "reasons": ["identity_conflict"]}
    ]
    result = decide(evidence=evidence)
    assert result["desired_enabled"] is True
    assert result["intraday_escalation_allowed"] is False
    evidence["invalid_json_row_count"] = 1
    assert decide(evidence=evidence)["desired_enabled"] is False


@pytest.mark.parametrize(
    "bad_policy",
    [
        [1],
        {"policy_version": policy.POLICY_VERSION, "controller_state": [1]},
        {"policy_version": "unknown_future_version", "controller_state": {}},
    ],
)
def test_malformed_checkpoint_structure_fails_closed(isolated, bad_policy):
    path = report.DROUGHT_REPORT_DIR / (
        "entry_recheck_drought_controller_2026-09-04.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {"target_date": "2026-09-04", "drought_conditional_policy": bad_policy}
        )
    )
    state, source = report._previous_drought_state("2026-09-07", "2026-06-05")
    assert state["invalid"] is True and source == str(path)


def test_failed_report_publication_preserves_previous_json(isolated):
    path, _ = report.report_paths("2026-09-04")
    path.parent.mkdir(parents=True)
    path.write_text('{"old_checkpoint":true}')
    original_replace = report.os.replace

    def fail_json(source, target):
        if target == path:
            raise OSError("injected publication failure")
        original_replace(source, target)

    isolated.setattr(report.os, "replace", fail_json)
    isolated.setattr(report, "render_markdown", lambda value: "report\n")
    with pytest.raises(OSError):
        report.write_report({"target_date": "2026-09-04"})
    assert json.loads(path.read_text()) == {"old_checkpoint": True}
    assert not list(path.parent.glob(".*.json.*"))


def test_fixed_checkpoint_is_revisited_after_generated_freeze(isolated):
    report.DROUGHT_REPORT_DIR.mkdir(parents=True)
    original = report.DROUGHT_REPORT_DIR / (
        "entry_recheck_drought_controller_2026-09-04.json"
    )
    frozen = report.DROUGHT_REPORT_DIR / (
        "entry_recheck_drought_controller_2026-09-07.json"
    )
    original.write_text("{broken")
    frozen.write_text(
        json.dumps(
            {
                "target_date": "2026-09-07",
                "drought_conditional_policy": {
                    "policy_version": policy.POLICY_VERSION,
                    "controller_state": {"invalid": True},
                    "previous_controller_state": {"invalid": True},
                    "previous_controller_state_path": str(original),
                },
            }
        )
    )
    state, _ = report._previous_drought_state("2026-09-08", "2026-06-05")
    assert state["invalid"] is True
    repaired = decide()["controller_state"]
    original.write_text(
        json.dumps(
            {
                "target_date": "2026-09-04",
                "drought_conditional_policy": {
                    "policy_version": policy.POLICY_VERSION,
                    "controller_state": repaired,
                },
            }
        )
    )
    state, path = report._previous_drought_state("2026-09-08", "2026-06-05")
    assert state == repaired and path == str(original)


def test_legacy_backtest_checkpoint_migrates_only_when_new_controller_has_none(
    isolated,
):
    legacy = report.REPORT_DIR / "entry_ai_gate_backtest_2026-09-04.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        json.dumps(
            {
                "target_date": "2026-09-04",
                "drought_conditional_policy": {
                    "policy_version": (
                        "entry_opportunity_recheck_drought_controller_v2"
                    ),
                    "controller_state": {
                        "policy_version": (
                            "entry_opportunity_recheck_drought_controller_v2"
                        ),
                        "evidence_start_date": "2026-06-05",
                        "stop_latched": True,
                        "stopped_at": "2026-09-04",
                        "stop_context": {"KRX|KRX_REGULAR": ["UPSTREAM_GATE"]},
                        "recovery_observed": False,
                        "last_source_date": "2026-09-04",
                        "active_scopes": [],
                    },
                },
            }
        )
    )

    state, source = report._previous_drought_state("2026-09-07", "2026-06-05")

    assert source == str(legacy)
    assert state["policy_version"] == policy.POLICY_VERSION
    assert state["stop_latched"] is True
