import json
import gzip
from datetime import datetime

from src.engine.monitoring.intraday_entry_blocker_diagnostics import (
    build_report,
    _default_pipeline_path,
    _loop_should_stop,
    _parse_hhmm,
    _within_time_window,
)


def _event(code, name, stage, fields, emitted_at="2026-06-23T08:00:00"):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields,
        "emitted_at": emitted_at,
    }


def test_build_report_surfaces_rising_promoted_without_real_submit(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "010690",
            "화신",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "7.80"},
        ),
        _event(
            "010690",
            "화신",
            "ai_confirmed",
            {"price_delta_since_first_seen_pct": "7.80", "action": "WAIT", "ai_score": "60", "entry_score_threshold": "75"},
        ),
        _event(
            "010690",
            "화신",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "7.80", "reason": "below_buy_ratio", "ai_score": "60"},
        ),
        _event(
            "010690",
            "화신",
            "ai_confirmed_terminal_no_budget",
            {"price_delta_since_first_seen_pct": "7.80", "terminal_reason": "ai_wait"},
        ),
        _event(
            "010690",
            "화신",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "7.80",
                "skip_reason": "scanner_full_eval_loop_budget_deferred",
                "rising_entry_relief_eligible": True,
                "scanner_positive_delta_pct": "7.80",
                "scanner_full_eval_budget_source": "deferred_no_relief",
                "scanner_full_eval_limit": "12",
                "scanner_full_eval_count": "12",
                "scanner_rising_full_eval_extra_limit": "4",
                "scanner_rising_full_eval_relief_count": "4",
                "rising_missed_selection_prior_key": "prior_positive",
                "rising_missed_selection_recommendation": "positive_prior",
                "rising_missed_selection_confidence": "high",
                "rising_missed_selection_score_delta": "20",
                "rising_missed_selection_rank_reason": "positive_prior_test",
            },
        ),
        _event("010690", "화신", "scalp_sim_buy_order_assumed_filled", {"simulated_order": "True"}),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 1
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "010690"
    assert item["real_submit_count"] == 0
    assert "sim_submit_observation_count" not in item
    assert item["dominant_blocker"]["stage"] == "blocked_strength_momentum"
    assert item["latest_blocker"]["reason"] == "scanner_full_eval_loop_budget_deferred"
    assert item["latest_ai_action"] == "WAIT"
    assert report["blocker_rollup"][0] == {"stage": "blocked_strength_momentum", "reason": "below_buy_ratio", "count": 1}
    assert report["relief_blocker_split_rollup"]["rising_missed_buy"][0] == {
        "stage": "scalping_scanner_watching_runtime_skip",
        "reason": "scanner_full_eval_loop_budget_deferred",
        "count": 1,
    }
    assert item["recent_blockers"][-1]["scanner_full_eval_budget_source"] == "deferred_no_relief"
    assert item["recent_blockers"][-1]["rising_missed_selection_recommendation"] == "positive_prior"
    assert item["scanner_full_eval_budget_deferred"]["rising_missed_selection_prior_key"] == "prior_positive"
    assert item["scanner_full_eval_budget_deferred"]["count"] == 1
    assert report["summary"]["rising_missed_full_eval_budget_deferred_count"] == 1
    assert report["summary"]["rising_missed_selection_prior_recommendation_counts"] == [
        {"recommendation": "positive_prior", "count": 1}
    ]
    assert report["summary"]["rising_missed_selection_positive_or_recheck_count"] == 1
    assert report["summary"]["rising_missed_selection_risk_count"] == 0
    assert report["scanner_full_eval_budget_diagnostics"]["top_symbols"][0]["stock_code"] == "010690"
    budget_priority = next(
        item for item in report["root_cause_priorities"] if item["issue"] == "scanner_full_eval_budget_deferred"
    )
    assert budget_priority["decision"] == "treat_only_sla_breach_as_evaluation_throughput_bottleneck"
    assert "threshold_relaxation" in budget_priority["forbidden_uses"]
    assert {
        "class": "runtime_backpressure",
        "stage": "scalping_scanner_watching_runtime_skip",
        "reason": "scanner_full_eval_loop_budget_deferred",
        "count": 1,
    } in report["blocker_taxonomy"]["suppressed_non_actionable_counts"]


def test_build_report_uses_one_pct_rising_missed_threshold(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000990",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "0.99"},
        ),
        _event(
            "001000",
            "B",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "1.00"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["thresholds"]["rising_missed_pct"] == 1.0
    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["summary"]["rising_missed_class_counts"] == [
        {"class": "rising_missed_raw", "count": 1}
    ]
    assert report["summary"]["rising_missed_one_share_eligible_symbol_count"] == 1
    assert report["rising_missed_buy"][0]["stock_code"] == "001000"
    assert report["rising_missed_buy"][0]["rising_missed_class"] == "rising_missed_raw"
    assert report["rising_missed_buy"][0]["rising_missed_one_share_eligible"] is True
    assert {item["stock_code"] for item in report["promoted_symbols"]} == {"000990", "001000"}


def test_build_report_excludes_not_evaluated_entry_ai_from_rising_missed(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "004990",
            "금호건설",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "2.30"},
            emitted_at="2026-06-23T09:00:00",
        ),
        _event(
            "004990",
            "금호건설",
            "ai_confirmed",
            {"price_delta_since_first_seen_pct": "2.30", "action": "not_evaluated"},
            emitted_at="2026-06-23T09:00:01",
        ),
        _event(
            "004990",
            "금호건설",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "2.30", "reason": "below_buy_ratio"},
            emitted_at="2026-06-23T09:00:02",
        ),
        _event(
            "099990",
            "제출스냅샷",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "3.10"},
            emitted_at="2026-06-23T09:01:00",
        ),
        _event(
            "099990",
            "제출스냅샷",
            "ai_confirmed",
            {"price_delta_since_first_seen_pct": "3.10", "action": "WAIT"},
            emitted_at="2026-06-23T09:01:01",
        ),
        _event(
            "099990",
            "제출스냅샷",
            "order_bundle_submitted",
            {"price_delta_since_first_seen_pct": "3.10", "ai_action": "not_evaluated"},
            emitted_at="2026-06-23T09:01:02",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 0
    assert report["summary"]["rising_missed_ai_not_evaluated_excluded_count"] == 2
    assert set(report["summary"]["rising_missed_ai_not_evaluated_excluded_symbols"]) == {
        "004990",
        "099990",
    }
    excluded = {item["stock_code"]: item for item in report["rising_missed_ai_not_evaluated_excluded"]}
    assert excluded["004990"]["rising_missed_class"] == "source_quality_excluded"
    assert excluded["004990"]["rising_missed_class_reason"] == "entry_ai_action_not_evaluated"
    assert excluded["004990"]["rising_missed_one_share_eligible"] is False
    assert excluded["004990"]["rising_missed_entry_ai_action_stage"] == "ai_confirmed"
    assert excluded["099990"]["rising_missed_entry_ai_action_stage"] == "order_bundle_submitted"
    assert excluded["099990"]["rising_missed_entry_ai_action_source"] == "ai_action"


def test_build_report_not_evaluated_does_not_promote_below_threshold_to_rising_missed(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "004990",
            "금호건설",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "0.50"},
            emitted_at="2026-06-23T09:00:00",
        ),
        _event(
            "004990",
            "금호건설",
            "ai_confirmed",
            {"price_delta_since_first_seen_pct": "0.50", "action": "not_evaluated"},
            emitted_at="2026-06-23T09:00:01",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 0
    assert report["summary"]["rising_missed_ai_not_evaluated_excluded_count"] == 0
    item = report["promoted_symbols"][0]
    assert item["rising_missed_class"] == "not_rising_missed"
    assert item["rising_missed_class_reason"] == "below_rising_missed_threshold"
    assert item["rising_missed_entry_ai_not_evaluated_excluded"] is True


def test_build_report_excludes_runtime_attach_identity_mismatch_from_one_share(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000390",
            "매드업",
            "scalping_scanner_candidate_promoted",
            {
                "scanner_promotion_id": "SCANPROM-000390-1",
                "price_delta_since_first_seen_pct": "0.00",
            },
            emitted_at="2026-06-23T10:04:09",
        ),
        _event(
            "000390",
            "매드업",
            "scalping_scanner_runtime_target_attach",
            {
                "scanner_promotion_id": "SCANPROM-000390-1",
                "runtime_target_attach_outcome": "skipped",
                "runtime_target_attach_reason": "scanner_identity_name_mismatch",
                "scanner_identity_payload_name": "매드업",
                "scanner_identity_db_name": "SP삼화",
                "scanner_identity_mismatch_expired": "True",
                "price_delta_since_first_seen_pct": "0.00",
            },
            emitted_at="2026-06-23T10:04:10",
        ),
        _event(
            "000390",
            "매드업",
            "scalping_scanner_candidate_promoted",
            {
                "scanner_promotion_id": "SCANPROM-000390-2",
                "price_delta_since_first_seen_pct": "2.47",
            },
            emitted_at="2026-06-23T10:06:11",
        ),
        _event(
            "000390",
            "매드업",
            "scalping_scanner_runtime_target_attach",
            {
                "scanner_promotion_id": "SCANPROM-000390-2",
                "runtime_target_attach_outcome": "skipped",
                "runtime_target_attach_reason": "scanner_identity_name_mismatch",
                "scanner_identity_payload_name": "매드업",
                "scanner_identity_db_name": "SP삼화",
                "scanner_identity_mismatch_expired": "True",
                "price_delta_since_first_seen_pct": "2.47",
            },
            emitted_at="2026-06-23T10:06:12",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["summary"]["rising_missed_class_counts"] == [
        {"class": "source_quality_excluded", "count": 1}
    ]
    assert report["summary"]["rising_missed_one_share_eligible_symbol_count"] == 0
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "000390"
    assert item["rising_missed_class"] == "source_quality_excluded"
    assert item["rising_missed_one_share_eligible"] is False
    assert item["runtime_attach_identity_mismatch"] == {
        "count": 2,
        "latest_at": "2026-06-23T10:06:12",
        "latest_reason": "scanner_identity_name_mismatch",
        "payload_name": "매드업",
        "db_name": "SP삼화",
        "mismatch_expired": "True",
    }
    assert report["summary"]["rising_missed_runtime_attach_identity_mismatch_workorder_count"] == 1
    workorders = report["source_quality_workorders"]["rising_missed_runtime_attach_identity_mismatch"]
    assert workorders == [
        {
            "workorder_type": "scanner_runtime_attach_identity_mismatch",
            "stock_code": "000390",
            "stock_name": "매드업",
            "event_count": 2,
            "latest_at": "2026-06-23T10:06:12",
            "latest_reason": "scanner_identity_name_mismatch",
            "payload_name": "매드업",
            "db_name": "SP삼화",
            "mismatch_expired": "True",
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "implementation_status": "implemented_source_quality_contract_available",
            "implementation_provenance": {
                "implementation_type": "scanner_runtime_attach_identity_source_quality_provenance",
                "metric_role": "source_quality_gate",
                "decision_authority": "source_quality_only",
                "latest_reason": "scanner_identity_name_mismatch",
                "payload_name": "매드업",
                "db_name": "SP삼화",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "root_cause_closure_status_hint": "implementation_done",
            },
            "forbidden_uses": [
                "buy_score_relaxation",
                "ai_threshold_relaxation",
                "broker_guard_bypass",
                "stale_submit_bypass",
                "real_order_approval",
                "forced_one_share_success_counting",
            ],
            "next_action": (
                "check_scanner_promotion_payload_and_db_runtime_target_attach_identity_normalization"
            ),
        }
    ]


def test_build_report_suppresses_known_latency_guard_as_resolved_non_major(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "475150",
            "SK이터닉스",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "4.06"},
            emitted_at="2026-06-23T10:11:58",
        ),
        _event(
            "475150",
            "SK이터닉스",
            "latency_block",
            {
                "price_delta_since_first_seen_pct": "4.06",
                "reason": "latency_state_danger",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
                "spread_ratio": "0.0112",
                "ws_age_ms": "81",
                "orderbook_micro_spread_ticks": "5",
                "orderbook_micro_state": "neutral",
                "orderbook_micro_ofi_bucket_key": "spread=wide|price=high|depth=normal|sample=rich",
            },
            emitted_at="2026-06-23T10:16:55",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["rising_missed_class"] == "intended_guard_preserved"
    assert item["rising_missed_one_share_eligible"] is False
    assert item["latest_blocker"]["stage"] == "latency_block"
    assert item["latest_blocker"]["reason"] == "latency_state_danger"
    assert item["dominant_actionable_blocker"] == {
        "stage": "",
        "reason": "",
        "count": 0,
        "class": "non_actionable_guard_or_backpressure",
        "route": "observe_only",
    }
    assert item["latency_danger_root_cause"]["top_cause"] == "spread_too_wide"
    assert item["latency_danger_root_cause"]["spread_ratio"] == {"min": 0.0112, "median": 0.0112, "max": 0.0112}
    assert item["recent_blockers"][-1]["latency_root_cause"] == "spread_too_wide"
    assert item["recent_blockers"][-1]["ofi_bucket"] == "spread=wide|price=high|depth=normal|sample=rich"
    assert item["recent_blockers"][-1]["taxonomy"] == {
        "class": "pre_submit_quality_guard",
        "actionable": False,
        "major_blocker": False,
        "route": "known_spread_too_wide_guard_preserved_no_bypass",
    }
    assert {
        "class": "pre_submit_quality_guard",
        "stage": "latency_block",
        "reason": "latency_state_danger",
        "count": 1,
    } in report["blocker_taxonomy"]["suppressed_non_actionable_counts"]
    assert report["blocker_taxonomy"]["actionable_major_blocker_counts"] == []


def test_build_report_keeps_unknown_latency_guard_as_actionable_major(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000001",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "4.06"},
            emitted_at="2026-06-23T10:11:58",
        ),
        _event(
            "000001",
            "A",
            "latency_block",
            {
                "price_delta_since_first_seen_pct": "4.06",
                "reason": "latency_state_danger",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
                "latency_danger_reasons": "other_danger",
                "ws_age_ms": "81",
            },
            emitted_at="2026-06-23T10:16:55",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["rising_missed_class"] == "actionable_major_missed"
    assert item["rising_missed_one_share_eligible"] is True
    assert item["latency_danger_root_cause"]["top_cause"] == "other_danger"
    assert item["dominant_actionable_blocker"] == {
        "stage": "latency_block",
        "reason": "latency_state_danger",
        "count": 1,
        "class": "pre_submit_quality_guard",
        "route": "inspect_latency_danger_or_slippage_without_guard_bypass",
    }
    assert {
        "class": "pre_submit_quality_guard",
        "stage": "latency_block",
        "reason": "latency_state_danger",
        "count": 1,
    } in report["blocker_taxonomy"]["actionable_major_blocker_counts"]


def test_build_report_keeps_entry_ai_authority_guard_as_actionable_major(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000001",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "1.25"},
            emitted_at="2026-06-23T10:11:58",
        ),
        _event(
            "000001",
            "A",
            "pre_submit_entry_ai_authority_guard_block",
            {
                "price_delta_since_first_seen_pct": "1.25",
                "block_reason": "entry_ai_score_unavailable",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
                "entry_ai_submit_authority_score": "0.0",
                "entry_ai_submit_authority_action": "not_evaluated",
            },
            emitted_at="2026-06-23T10:16:55",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["rising_missed_class"] == "actionable_major_missed"
    assert item["rising_missed_one_share_eligible"] is True
    assert item["dominant_actionable_blocker"] == {
        "stage": "pre_submit_entry_ai_authority_guard_block",
        "reason": "entry_ai_score_unavailable",
        "count": 1,
        "class": "pre_submit_quality_guard",
        "route": "restore_entry_ai_authority_before_submit_without_broker_guard_bypass",
    }
    assert {
        "class": "pre_submit_quality_guard",
        "stage": "pre_submit_entry_ai_authority_guard_block",
        "reason": "entry_ai_score_unavailable",
        "count": 1,
    } in report["blocker_taxonomy"]["actionable_major_blocker_counts"]


def test_build_report_splits_mixed_known_and_unknown_latency_causes(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000001",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "4.06"},
            emitted_at="2026-06-23T10:11:58",
        ),
        _event(
            "000001",
            "A",
            "latency_block",
            {
                "price_delta_since_first_seen_pct": "4.06",
                "reason": "latency_state_danger",
                "spread_ratio": "0.0112",
            },
            emitted_at="2026-06-23T10:16:55",
        ),
        _event(
            "000001",
            "A",
            "latency_block",
            {
                "price_delta_since_first_seen_pct": "4.06",
                "reason": "latency_state_danger",
                "latency_danger_reasons": "other_danger",
                "ws_age_ms": "81",
            },
            emitted_at="2026-06-23T10:17:55",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert {
        "class": "pre_submit_quality_guard",
        "stage": "latency_block",
        "reason": "latency_state_danger",
        "count": 1,
    } in report["blocker_taxonomy"]["actionable_major_blocker_counts"]
    assert {
        "class": "pre_submit_quality_guard",
        "stage": "latency_block",
        "reason": "latency_state_danger",
        "count": 1,
    } in report["blocker_taxonomy"]["suppressed_non_actionable_counts"]


def test_build_report_splits_relief_blockers_for_non_rising(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.20"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.20", "skip_reason": "entry_cooldown_active"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 0
    assert report["relief_blocker_split_rollup"]["rising_missed_buy"] == []
    assert report["relief_blocker_split_rollup"]["non_rising_promoted"] == [
        {"stage": "scalping_scanner_watching_runtime_skip", "reason": "entry_cooldown_active", "count": 1}
    ]


def test_build_report_suppresses_normal_cooldown_and_single_deferred_as_major_blockers(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.30"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.30", "skip_reason": "entry_cooldown_active"},
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.40"}),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "0.40",
                "skip_reason": "scanner_full_eval_loop_budget_deferred",
                "scanner_full_eval_limit": "4",
                "scanner_full_eval_count": "4",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    taxonomy = report["blocker_taxonomy"]
    assert taxonomy["suppressed_non_major_counts"] == taxonomy["suppressed_non_actionable_counts"]
    assert taxonomy["suppressed_non_actionable_counts"] == [
        {
            "class": "intended_guard",
            "stage": "scalping_scanner_watching_runtime_skip",
            "reason": "entry_cooldown_active",
            "count": 1,
        },
        {
            "class": "runtime_backpressure",
            "stage": "scalping_scanner_watching_runtime_skip",
            "reason": "scanner_full_eval_loop_budget_deferred",
            "count": 1,
        },
    ]
    assert all(item["issue"] != "scanner_full_eval_budget_deferred" for item in report["root_cause_priorities"])
    assert report["summary"]["suppressed_non_actionable_blocker_count"] == 2


def test_build_report_treats_same_symbol_loss_reentry_cooldown_as_intended_guard(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.30"}),
        _event("000001", "A", "same_symbol_loss_reentry_cooldown", {"price_delta_since_first_seen_pct": "1.30"}),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["summary"]["rising_missed_class_counts"] == [
        {"class": "intended_guard_preserved", "count": 1}
    ]
    assert report["summary"]["rising_missed_one_share_eligible_symbol_count"] == 0
    item = report["rising_missed_buy"][0]
    assert item["rising_missed_class"] == "intended_guard_preserved"
    assert item["rising_missed_one_share_eligible"] is False
    assert item["dominant_actionable_blocker"] == {
        "stage": "",
        "reason": "",
        "count": 0,
        "class": "non_actionable_guard_or_backpressure",
        "route": "observe_only",
    }
    assert item["latest_blocker"] == {
        "stage": "same_symbol_loss_reentry_cooldown",
        "reason": "",
        "emitted_at": "2026-06-23T08:00:00",
        "price_delta_since_first_seen_pct": 1.3,
        "ai_score": None,
    }
    assert item["recent_blockers"][-1]["taxonomy"] == {
        "class": "intended_guard",
        "actionable": False,
        "major_blocker": False,
        "route": "normal_cooldown_guard",
    }
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "intended_guard",
            "stage": "same_symbol_loss_reentry_cooldown",
            "reason": "",
            "count": 1,
        }
    ]


def test_build_report_treats_manual_control_runtime_attach_skip_as_intended_guard(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("005930", "삼성전자", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.05"}),
        _event(
            "005930",
            "삼성전자",
            "scalping_scanner_runtime_target_attach",
            {
                "price_delta_since_first_seen_pct": "1.05",
                "runtime_target_attach_outcome": "skipped",
                "runtime_target_attach_reason": "operator_manual_control_excluded_symbol",
                "manual_control_exclusion_applied": "True",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["summary"]["rising_missed_class_counts"] == [
        {"class": "intended_guard_preserved", "count": 1}
    ]
    assert report["summary"]["rising_missed_one_share_eligible_symbol_count"] == 0
    item = report["rising_missed_buy"][0]
    assert item["rising_missed_class"] == "intended_guard_preserved"
    assert item["dominant_actionable_blocker"] == {
        "stage": "",
        "reason": "",
        "count": 0,
        "class": "non_actionable_guard_or_backpressure",
        "route": "observe_only",
    }
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "intended_guard",
            "stage": "scalping_scanner_runtime_target_attach",
            "reason": "operator_manual_control_excluded_symbol",
            "count": 1,
        }
    ]


def test_build_report_keeps_repeated_high_delta_cooldown_non_major(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "4.00"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "4.00", "skip_reason": "entry_cooldown_active"},
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "4.00", "skip_reason": "entry_cooldown_active"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["blocker_taxonomy"]["actionable_major_blocker_counts"] == []
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "intended_guard",
            "stage": "scalping_scanner_watching_runtime_skip",
            "reason": "entry_cooldown_active",
            "count": 2,
        }
    ]


def test_build_report_splits_full_eval_deferred_then_evaluated_status(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.30"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.30",
                "skip_reason": "scanner_full_eval_loop_budget_deferred",
                "scanner_full_eval_limit": "4",
                "scanner_full_eval_count": "4",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "1.30",
                "reason": "below_strength_base",
            },
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.40"}),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.40",
                "skip_reason": "scanner_full_eval_loop_budget_deferred",
                "scanner_full_eval_limit": "4",
                "scanner_full_eval_count": "4",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")
    by_code = {item["stock_code"]: item for item in report["rising_missed_buy"]}

    assert by_code["000001"]["scanner_full_eval_budget_deferred"]["status"] == "deferred_then_evaluated"
    assert by_code["000002"]["scanner_full_eval_budget_deferred"]["status"] == "deferred_never_evaluated"
    assert {
        item["status"]: item["count"]
        for item in report["scanner_full_eval_budget_diagnostics"]["status_counts"]
    } == {
        "deferred_then_evaluated": 1,
        "deferred_never_evaluated": 1,
    }


def test_build_report_splits_ws_snapshot_missing_as_recovering_or_evictable_budget_state(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.30"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.30", "skip_reason": "ws_snapshot_missing_or_zero"},
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.30"}),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.30", "skip_reason": "ws_snapshot_missing_or_zero"},
        ),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.30", "skip_reason": "ws_snapshot_missing_or_zero"},
        ),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.30", "skip_reason": "ws_snapshot_missing_or_zero"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    by_code = {item["stock_code"]: item for item in report["promoted_symbols"]}
    assert by_code["000001"]["dominant_actionable_blocker"]["class"] == "non_actionable_guard_or_backpressure"
    assert by_code["000002"]["dominant_actionable_blocker"]["class"] == "non_actionable_guard_or_backpressure"
    assert report["blocker_taxonomy"]["actionable_major_blocker_counts"] == []
    assert report["blocker_taxonomy"]["suppressed_non_major_counts"] == report["blocker_taxonomy"]["suppressed_non_actionable_counts"]
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "source_freshness_evictable",
            "stage": "scalping_scanner_watching_runtime_skip",
            "reason": "ws_snapshot_missing_or_zero",
            "count": 3,
        },
        {
            "class": "source_freshness_recovering",
            "stage": "scalping_scanner_watching_runtime_skip",
            "reason": "ws_snapshot_missing_or_zero",
            "count": 1,
        },
    ]


def test_build_report_marks_watch_eviction_as_budget_reallocated(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.30"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watch_eviction",
            {
                "price_delta_since_first_seen_pct": "0.30",
                "eviction_reason": "stale_recovery_failed",
                "terminal_reason": "ws_snapshot_missing_or_zero",
                "eviction_attempt_count": "4",
                "stale_age_sec": "91.0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["promoted_symbols"][0]["recent_blockers"][-1]["taxonomy"] == {
        "class": "watch_budget_reallocated",
        "actionable": False,
        "major_blocker": False,
        "route": "watch_budget_reallocated_after_stale_or_terminal_expiry",
    }
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "watch_budget_reallocated",
            "stage": "scalping_scanner_watch_eviction",
            "reason": "stale_recovery_failed",
            "count": 1,
        }
    ]


def test_build_report_routes_rising_missed_not_rising_eviction_as_budget_reallocated(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.00"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "budget_reallocated",
                "fast_precheck_reason": "rising_missed_not_rising_without_recovery_signal",
                "scanner_rising_missed_recovery_signal_present": "False",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watch_eviction",
            {
                "eviction_reason": "rising_missed_not_rising_budget_reallocated",
                "terminal_reason": "rising_missed_not_rising_without_recovery_signal",
                "fast_precheck_result": "budget_reallocated",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert {
        "class": "watch_budget_reallocated",
        "route": "watch_budget_reallocated_after_rising_missed_not_rising_fast_reject",
        "count": 1,
    } in report["blocker_taxonomy"]["route_counts"]
    assert {
        "class": "watch_budget_reallocated",
        "stage": "scalping_scanner_watch_eviction",
        "reason": "rising_missed_not_rising_budget_reallocated",
        "count": 1,
    } in report["blocker_taxonomy"]["suppressed_non_actionable_counts"]


def test_build_report_splits_low_ai_pressure_by_eval_freshness(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "quote_age_ms": "1200",
                "tick_latest_age_ms": "900",
                "reason": "below_strength_base",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "50",
                "quote_age_ms": "18000",
                "reason": "stale_quote_or_context",
            },
        ),
        _event(
            "000001",
            "A",
            "scalp_entry_action_decision_snapshot",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "buy_pressure_10t": "-12.5",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    expected = {"fresh_eval": 1, "stale_or_delayed_eval": 1, "unknown_eval_quality": 1}
    assert report["summary"]["rising_missed_low_ai_or_negative_pressure_eval_quality"] == expected
    assert report["rising_missed_buy"][0]["low_ai_or_negative_pressure_eval_quality"] == expected
    assert report["summary"]["rising_missed_stale_or_delayed_eval_category_counts"] == {
        "diagnostic_quote_age_stale": 1,
        "full_eval_delay": 0,
        "ws_quote_missing": 0,
        "pre_ai_stale_or_history_gap": 0,
        "pre_submit_hard_stale": 0,
    }


def test_build_report_excludes_recovery_observations_from_blockers(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "scanner_fast_precheck_subscription_recheck_snapshot_applied",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "before_strategy_start",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "reason": "below_strength_base",
                "ws_strength_history_count": "12",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["blocker_count"] == 1
    assert item["dominant_blocker"] == {
        "stage": "blocked_strength_momentum",
        "reason": "below_strength_base",
        "count": 1,
    }
    assert item["latest_blocker"]["reason"] == "below_strength_base"
    assert report["summary"]["repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []


def test_build_report_keeps_strategy_rejects_out_of_actionable_major_counts(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.30"}),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "1.30", "reason": "below_strength_base"},
        ),
        _event(
            "000001",
            "A",
            "ai_confirmed_terminal_no_budget",
            {
                "price_delta_since_first_seen_pct": "1.30",
                "terminal_reason": "blocked_ai_score_below_buy_score_threshold",
                "ai_score": "62",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["blocker_taxonomy"]["actionable_major_blocker_counts"] == []
    assert report["summary"]["actionable_major_blocker_count"] == 0
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "strategy_reject",
            "stage": "blocked_strength_momentum",
            "reason": "below_strength_base",
            "count": 1,
        },
        {
            "class": "strategy_reject",
            "stage": "ai_confirmed_terminal_no_budget",
            "reason": "blocked_ai_score_below_buy_score_threshold",
            "count": 1,
        },
    ]


def test_build_report_suppresses_source_quality_excluded_freshness_from_major_counts(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.00"}),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "2.00",
                "reason": "insufficient_history",
                "quote_age_ms": "2000",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "2.00",
                "reason": "insufficient_history",
                "quote_age_ms": "2100",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["rising_missed_buy"][0]["rising_missed_class"] == "source_quality_excluded"
    assert report["blocker_taxonomy"]["actionable_major_blocker_counts"] == []
    assert report["summary"]["actionable_major_blocker_count"] == 0
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "source_quality_exclusion_candidate",
            "stage": "blocked_strength_momentum",
            "reason": "insufficient_history",
            "count": 2,
        }
    ]


def test_build_report_suppresses_non_rising_freshness_from_major_counts(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.00"}),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "0.00",
                "reason": "insufficient_history",
                "quote_age_ms": "2000",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["promoted_symbols"][0]["rising_missed_class"] == "not_rising_missed"
    assert report["blocker_taxonomy"]["actionable_major_blocker_counts"] == []
    assert report["summary"]["actionable_major_blocker_count"] == 0
    assert report["blocker_taxonomy"]["suppressed_non_actionable_counts"] == [
        {
            "class": "source_quality_exclusion_candidate",
            "stage": "blocked_strength_momentum",
            "reason": "insufficient_history",
            "count": 1,
        }
    ]


def test_build_report_treats_recovered_stale_ws_as_recovered_not_stale_eval(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "quote_age_ms": "1200",
                "skip_reason": "scanner_fast_precheck_stale_ws_recovered",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "scanner_fast_precheck_stale_ws_recovered",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    expected = {"fresh_eval": 1, "stale_or_delayed_eval": 0, "unknown_eval_quality": 0}
    assert report["summary"]["rising_missed_low_ai_or_negative_pressure_eval_quality"] == expected
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []


def test_build_report_splits_stale_or_delayed_eval_categories(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "quote_age_ms": "7000",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "skip_reason": "scanner_full_eval_loop_budget_deferred",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "skip_reason": "ws_snapshot_missing_or_zero",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "reason": "insufficient_history",
            },
        ),
        _event(
            "000001",
            "A",
            "entry_submit_revalidation_warning",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    expected = {
        "diagnostic_quote_age_stale": 1,
        "full_eval_delay": 1,
        "ws_quote_missing": 1,
        "pre_ai_stale_or_history_gap": 1,
        "pre_submit_hard_stale": 1,
    }
    assert report["rising_missed_buy"][0]["stale_or_delayed_eval_category_counts"] == expected
    assert report["summary"]["rising_missed_stale_or_delayed_eval_category_counts"] == expected
    priority = next(
        item for item in report["root_cause_priorities"] if item["issue"] == "scanner_strength_history_or_stale_eval"
    )
    assert priority["evidence"]["stale_or_delayed_eval_category_counts"] == expected
    assert report["summary"]["rising_missed_freshness_recovery_workorder_count"] == 1
    freshness_workorders = report["source_quality_workorders"]["rising_missed_freshness_recovery"]
    assert freshness_workorders[0]["workorder_type"] == "bounded_rising_candidate_freshness_recheck"
    assert freshness_workorders[0]["diagnostic_quote_age_stale"] == 1
    assert freshness_workorders[0]["pre_ai_stale_or_history_gap"] == 1
    assert freshness_workorders[0]["runtime_effect"] is False
    assert freshness_workorders[0]["allowed_runtime_apply"] is False
    assert "stale_submit_bypass" in freshness_workorders[0]["forbidden_uses"]


def test_build_report_surfaces_repeated_zero_strength_history_workorder(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "insufficient_history",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "ws_strength_history_count": "0",
            },
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.30"}),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.30",
                "skip_reason": "insufficient_history",
                "ws_strength_history_count": "0",
            },
        ),
        _event("000003", "C", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.20"}),
        _event(
            "000003",
            "C",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "0.20",
                "skip_reason": "insufficient_history",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000003",
            "C",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "0.20",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["repeated_zero_strength_history_workorder_count"] == 2
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 1
    rising_workorders = report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"]
    assert [item["stock_code"] for item in rising_workorders] == ["000001"]
    assert rising_workorders[0]["decision_authority"] == "source_quality_only"
    assert rising_workorders[0]["runtime_effect"] is False
    assert rising_workorders[0]["implementation_status"] == "implemented_source_quality_contract_available"
    assert (
        rising_workorders[0]["implementation_provenance"]["implementation_type"]
        == "scanner_strength_history_source_quality_provenance"
    )
    assert rising_workorders[0]["implementation_provenance"]["runtime_effect"] is False
    assert "strength_threshold_relaxation" in rising_workorders[0]["forbidden_uses"]
    single_zero_history = next(item for item in report["rising_missed_buy"] if item["stock_code"] == "000002")
    assert single_zero_history["zero_strength_history_source_quality"]["source_quality_route"] == (
        "observe_until_repeated"
    )


def test_build_report_suppresses_transient_zero_history_after_downstream_progress(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "fast_precheck_result": "stability_pending",
                "fast_precheck_reason": "stale_ws_snapshot",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "fast_precheck_result": "stability_pending",
                "fast_precheck_reason": "stale_ws_snapshot",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
                "ws_strength_history_count": "3",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "below_strength_base",
                "ai_score": "62",
                "ws_strength_history_count": "3",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    quality = report["rising_missed_buy"][0]["zero_strength_history_source_quality"]
    assert quality["event_count"] == 0
    assert quality["raw_event_count"] == 2
    assert quality["recovered_by_downstream_progress"] is True
    assert quality["source_quality_route"] == "transient_stale_recovered_to_downstream_blocker"
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []
    assert all(
        item["issue"] != "scanner_strength_history_or_stale_eval"
        for item in report["root_cause_priorities"]
    )


def test_build_report_excludes_eligible_fast_precheck_relief_from_zero_history_workorder(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "rising_stale_ws_snapshot_full_eval_relief",
                "ws_strength_history_count": "0",
                "quote_age_ms": "908795.538",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "rising_rest_quote_recovery_without_realtime_strength",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    quality = report["rising_missed_buy"][0]["zero_strength_history_source_quality"]
    assert quality["event_count"] == 0
    assert quality["raw_event_count"] == 0
    assert quality["source_quality_route"] == "observe_until_repeated"
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []
    assert all(
        item["issue"] != "scanner_strength_history_or_stale_eval"
        for item in report["root_cause_priorities"]
    )


def test_build_report_excludes_sim_and_keeps_falling_real_submit(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "-0.20"}),
        _event(
            "000001",
            "A",
            "broker_buy_submit",
            {"price_delta_since_first_seen_pct": "-0.20", "actual_order_submitted": "True"},
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "-0.30"}),
        _event(
            "000002",
            "B",
            "scalp_sim_buy_order_assumed_filled",
            {
                "price_delta_since_first_seen_pct": "-0.30",
                "simulated_order": "True",
                "actual_order_submitted": "False",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert [item["stock_code"] for item in report["falling_real_submitted"]] == ["000001"]
    assert "falling_sim_submitted" not in report
    assert report["summary"]["falling_real_submitted_count"] == 1
    assert report["summary"]["excluded_analysis_scope"] == "sim_swing_and_rising_missed_forced_one_share_events"


def test_build_report_excludes_sim_price_rows_from_real_entry_price_diagnostics(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}),
        _event(
            "000001",
            "A",
            "scalp_entry_action_decision_snapshot",
            {
                "reason": "scalp_live_simulator",
                "submitted_order_price": "0",
                "best_bid_at_submit": "10000",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
            },
        ),
        _event(
            "000001",
            "A",
            "scalp_entry_action_decision_snapshot",
            {
                "simulation_book": "scalp_ai_buy_all",
                "submitted_order_price": "0",
                "best_bid_at_submit": "10000",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["entry_price_execution"]["event_count"] == 0
    assert report["entry_price_execution"]["candidate_failure_count"] == 0
    assert not any(item["issue"] == "entry_price_or_submit_price_guard_block" for item in report["root_cause_priorities"])


def test_build_report_prioritizes_real_entry_price_candidate_failures(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}),
        _event(
            "000001",
            "A",
            "entry_ai_price_canary_fallback",
            {"reason": "invalid_price", "action": "IMPROVE_LIMIT"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["entry_price_execution"]["candidate_failure_count"] == 1
    assert report["entry_price_execution"]["candidate_failure_reason_counts"] == [
        {"reason": "invalid_price", "count": 1}
    ]


def test_build_report_uses_submitted_price_for_entry_cancel_recent_issue(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}),
        _event(
            "000001",
            "A",
            "entry_order_cancel_confirmed",
            {
                "submitted_price": "24800",
                "best_bid_at_submit": "24850",
                "quote_age_at_submit_ms": "1166",
                "cancel_reason": "entry_timeout_or_reconcile",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    recent_issue = report["entry_price_execution"]["recent_issues"][-1]
    assert recent_issue["submitted_order_price"] == 24800
    assert recent_issue["best_bid_at_submit"] == 24850
    priority = next(item for item in report["root_cause_priorities"] if item["issue"] == "entry_price_or_submit_price_guard_block")
    assert priority["evidence"]["block_or_unfilled_count"] == 1
    assert "stale_submit_bypass" in priority["forbidden_uses"]


def test_build_report_since_filters_out_older_real_submit(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}, "2026-06-23T14:00:00"),
        _event(
            "000001",
            "A",
            "broker_buy_submit",
            {"price_delta_since_first_seen_pct": "1.00", "actual_order_submitted": "True"},
            "2026-06-23T14:05:00",
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}, "2026-06-23T14:16:00"),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        generated_at="fixed",
        since="2026-06-23T14:15:00",
    )

    assert report["event_window"]["since"] == "2026-06-23T14:15:00"
    assert report["summary"]["real_submit_symbol_count"] == 0
    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["rising_missed_buy"][0]["stock_code"] == "000002"


def test_build_report_since_keeps_previously_promoted_active_rising_candidate(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000001",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "0.00"},
            "2026-06-23T15:55:00",
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
            },
            "2026-06-23T16:00:30",
        ),
        _event(
            "000001",
            "A",
            "ai_confirmed_terminal_no_budget",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "terminal_reason": "blocked_ai_score_below_buy_score_threshold",
                "ai_score": "68",
            },
            "2026-06-23T16:01:00",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        generated_at="fixed",
        since="2026-06-23T16:00:00",
    )

    assert report["summary"]["promoted_symbol_count"] == 1
    assert report["summary"]["promoted_before_window_symbol_count"] == 1
    assert report["summary"]["rising_missed_buy_count"] == 1
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "000001"
    assert item["promoted_in_event_window"] is False
    assert item["first_promoted_at"] == "2026-06-23T15:55:00"
    assert item["latest_blocker"]["reason"] == "blocked_ai_score_below_buy_score_threshold"


def test_build_report_time_only_window_bounds_filter_with_target_date(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000001",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "1.20"},
            "2026-06-23T08:03:00",
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "1.20", "reason": "below_buy_ratio"},
            "2026-06-23T08:04:00",
        ),
        _event(
            "000002",
            "B",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "2.00"},
            "2026-06-23T08:06:00",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        generated_at="fixed",
        since="08:00",
        event_until="08:05",
    )

    assert report["event_window"] == {"since": "08:00", "until": "08:05"}
    assert report["summary"]["promoted_symbol_count"] == 1
    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["rising_missed_buy"][0]["stock_code"] == "000001"


def test_build_report_reads_gzip_pipeline_events(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-22.jsonl.gz"
    row = _event("000003", "C", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"})
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = build_report(target_date="2026-06-22", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["promoted_symbol_count"] == 1
    assert report["rising_missed_buy"][0]["stock_code"] == "000003"


def test_default_pipeline_path_prefers_gzip_when_plain_missing(monkeypatch, tmp_path):
    base = tmp_path / "data" / "pipeline_events"
    base.mkdir(parents=True)
    gz_path = base / "pipeline_events_2026-06-22.jsonl.gz"
    gz_path.write_bytes(b"")
    monkeypatch.setattr(
        "src.engine.monitoring.intraday_entry_blocker_diagnostics.PROJECT_ROOT",
        tmp_path,
    )

    assert _default_pipeline_path("2026-06-22") == gz_path


def test_build_report_adds_entry_price_scale_in_and_post_sell_diagnostics(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "pre_submit_price_guard_block",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "entry_price_guard": "defensive_order_price",
                "resolution_reason": "defensive_order_price",
                "price_below_bid_bps": "95",
                "submitted_order_price": "9900",
                "best_bid_at_submit": "10000",
                "quote_age_at_submit_ms": "450",
                "pre_submit_liquidity_guard_action": "PASS",
            },
        ),
        {
            "pipeline": "HOLDING_PIPELINE",
            "stock_code": "000002",
            "stock_name": "B",
            "stage": "stat_action_decision_snapshot",
            "fields": {
                "profit_rate": "-1.2",
                "peak_profit": "0.2",
                "current_ai_score": "73",
                "scale_in_gate_allowed": "False",
                "scale_in_gate_reason": "scalping_buy_window_blocked",
                "scale_in_blocker_reason": "scalping_buy_window_blocked",
                "scale_in_action_type": "AVG_DOWN",
                "distance_to_buy_bps": "-120",
            },
            "emitted_at": "2026-06-23T09:10:00",
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stock_code": "000002",
            "stock_name": "B",
            "stage": "stat_action_decision_snapshot",
            "fields": {
                "profit_rate": "1.8",
                "peak_profit": "2.1",
                "current_ai_score": "78",
                "scale_in_gate_allowed": "True",
                "scale_in_gate_reason": "ok",
                "scale_in_blocker_reason": "scalping_pyramid_ok",
                "scale_in_action_type": "PYRAMID",
                "distance_to_buy_bps": "140",
            },
            "emitted_at": "2026-06-23T09:11:00",
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stock_code": "000005",
            "stock_name": "E",
            "stage": "stat_action_decision_snapshot",
            "fields": {
                "profit_rate": "0.1",
                "peak_profit": "0.8",
                "current_ai_score": "72",
                "scale_in_gate_allowed": "False",
                "scale_in_gate_reason": "-",
                "scale_in_blocker_reason": "MFE protect exit",
                "scale_in_action_type": "-",
                "distance_to_buy_bps": "30",
            },
            "emitted_at": "2026-06-23T09:12:00",
        },
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    (post_sell_dir / "post_sell_candidates_2026-06-23.jsonl").write_text(
        json.dumps({"post_sell_id": "p1"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (post_sell_dir / "post_sell_evaluations_2026-06-23.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "post_sell_id": "p1",
                        "stock_code": "000003",
                        "stock_name": "C",
                        "sell_time": "09:20:00",
                        "profit_rate": "1.5",
                        "exit_rule": "scalp_trailing_take_profit",
                        "outcome": "MISSED_UPSIDE",
                        "metrics_10m": {"mfe_pct": "3.2", "mfe_vs_buy_pct": "4.4"},
                        "ai_score_at_exit": "71",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "post_sell_id": "p2",
                        "stock_code": "000004",
                        "stock_name": "D",
                        "sell_time": "09:25:00",
                        "profit_rate": "-2.1",
                        "exit_rule": "scalp_soft_stop_pct",
                        "outcome": "GOOD_EXIT",
                        "metrics_10m": {"mfe_pct": "0.1", "mfe_vs_buy_pct": "-1.0"},
                        "ai_score_at_exit": "55",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        post_sell_dir=post_sell_dir,
        generated_at="fixed",
    )

    assert report["entry_price_execution"]["block_or_unfilled_count"] == 1
    assert report["entry_price_execution"]["candidate_failure_count"] == 0
    assert report["entry_price_execution"]["recent_issues"][0]["price_below_bid_bps"] == 95.0
    assert report["scale_in_diagnostics"]["blocked_count"] == 1
    assert report["scale_in_diagnostics"]["blocker_reason_counts"][0] == {
        "reason": "scalping_buy_window_blocked",
        "count": 1,
    }
    post_sell = report["post_sell_flow_diagnostics"]
    assert post_sell["candidate_count"] == 1
    assert post_sell["evaluated_count"] == 2
    assert post_sell["missed_upside_count"] == 1
    assert post_sell["bad_entry_after_sell_count"] == 1
    assert post_sell["top_missed_upside"][0]["flow"] == "take_profit_flow"
    assert post_sell["bad_entry_examples"][0]["stock_code"] == "000004"
    priorities = report["root_cause_priorities"]
    assert [item["issue"] for item in priorities] == [
        "entry_price_or_submit_price_guard_block",
        "scale_in_blocked",
        "post_sell_missed_upside_or_bad_entry",
    ]
    assert priorities[0]["runtime_effect"] is False
    assert "stale_submit_bypass" in priorities[0]["forbidden_uses"]


def test_build_report_prioritizes_stale_observation_before_ai_threshold(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "ws_strength_history_count": "0",
                "quote_age_ms": "9000",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "score_62.0",
                "ai_score": "62",
                "quote_age_ms": "9000",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    priorities = report["root_cause_priorities"]
    assert priorities[0]["issue"] == "scanner_strength_history_or_stale_eval"
    assert priorities[0]["decision"] == "fix_observation_freshness_before_threshold_tuning"
    assert priorities[0]["evidence"]["top_unresolved_stale_eval_symbols"][0]["stock_code"] == "000001"
    assert priorities[1]["issue"] == "ai_wait_or_baseline_prior_score_block"
    assert "broad_buy_score_relaxation" in priorities[1]["forbidden_uses"]


def test_build_report_does_not_prioritize_recovered_stale_low_ai_eval(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "score_62.0",
                "ai_score": "62",
                "quote_age_ms": "9000",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
                "quote_age_ms": "300",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "score_62.0",
                "ai_score": "62",
                "quote_age_ms": "300",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["low_ai_or_negative_pressure_eval_quality"]["stale_or_delayed_eval"] == 1
    assert item["unresolved_stale_low_ai_or_pressure_eval_count"] == 0
    assert all(
        item["issue"] != "scanner_strength_history_or_stale_eval"
        for item in report["root_cause_priorities"]
    )


def test_build_report_uses_fast_precheck_observed_history_for_zero_history_workorders(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "fast_precheck_result": "stability_pending",
                "fast_precheck_reason": "stale_ws_snapshot",
                "ws_strength_history_count": "0",
                "fast_precheck_observed_ws_strength_history_count": "13",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "fast_precheck_result": "stability_pending",
                "fast_precheck_reason": "stale_ws_snapshot",
                "ws_strength_history_count": "0",
                "fast_precheck_observed_ws_strength_history_count": "12",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    quality = report["rising_missed_buy"][0]["zero_strength_history_source_quality"]
    assert quality["event_count"] == 0
    assert quality["raw_event_count"] == 0
    assert quality["source_quality_route"] == "observe_until_repeated"
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []


def test_build_report_does_not_prioritize_stale_low_ai_after_heavy_eval_repair(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "ai_confirmed_terminal_no_budget",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "blocked_ai_score_below_buy_score_threshold",
                "ai_score": "62",
                "quote_age_ms": "8200",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_heavy_eval_stale_snapshot_recheck",
                "quote_age_ms": "8400",
                "scanner_heavy_eval_recheck_age_sec": "8.4",
                "scanner_heavy_eval_recheck_fresh_sec": "3.0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["low_ai_or_negative_pressure_eval_quality"]["stale_or_delayed_eval"] == 1
    assert item["unresolved_stale_low_ai_or_pressure_eval_count"] == 0
    assert all(
        item["issue"] != "scanner_strength_history_or_stale_eval"
        for item in report["root_cause_priorities"]
    )


def test_loop_window_helpers():
    buy_start = _parse_hhmm("09:00")
    buy_end = _parse_hhmm("15:20")

    assert _within_time_window(datetime(2026, 6, 25, 9, 0), start=buy_start, end=buy_end)
    assert _within_time_window(datetime(2026, 6, 25, 15, 20), start=buy_start, end=buy_end)
    assert not _within_time_window(datetime(2026, 6, 25, 15, 21), start=buy_start, end=buy_end)
    assert not _loop_should_stop(datetime(2026, 6, 25, 19, 0), until=_parse_hhmm("19:00"))
    assert _loop_should_stop(datetime(2026, 6, 25, 19, 0, 1), until=_parse_hhmm("19:00"))


def test_build_report_excludes_rising_missed_one_share_forced_submit_from_general_buy_metrics(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-30.jsonl"
    rows = [
        _event(
            "000777",
            "강제1주",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "1.20"},
            emitted_at="2026-06-30T09:10:00",
        ),
        _event(
            "000777",
            "강제1주",
            "order_bundle_submitted",
            {
                "actual_order_submitted": "true",
                "price_delta_since_first_seen_pct": "1.20",
                "rising_missed_one_share_entry_forced": "true",
                "forced_entry_qty": "5",
                "forced_entry_reason": "rising_missed_one_share_entry",
            },
            emitted_at="2026-06-30T09:11:00",
        ),
        _event(
            "000777",
            "강제1주",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "1.20", "reason": "below_strength_base"},
            emitted_at="2026-06-30T09:12:00",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-30", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["real_submit_symbol_count"] == 0
    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["summary"]["excluded_analysis_scope"] == "sim_swing_and_rising_missed_forced_one_share_events"
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "000777"
    assert item["real_submit_count"] == 0


def test_build_report_excludes_unflagged_submit_after_rising_missed_forced_scout(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-30.jsonl"
    rows = [
        _event(
            "240810",
            "원익IPS",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "1.05"},
            emitted_at="2026-06-30T11:04:00",
        ),
        _event(
            "240810",
            "원익IPS",
            "budget_pass",
            {
                "price_delta_since_first_seen_pct": "1.05",
                "order_quantity": "1",
                "forced_entry_reason": "rising_missed_one_share_entry",
                "rising_missed_one_share_entry_forced": "true",
            },
            emitted_at="2026-06-30T11:04:10",
        ),
        _event(
            "240810",
            "원익IPS",
            "latency_pass",
            {
                "actual_order_submitted": "False",
                "broker_order_forbidden": "False",
                "price_delta_since_first_seen_pct": "1.05",
                "reason": "safe_normal_entry_allowed",
            },
            emitted_at="2026-06-30T11:04:16",
        ),
        _event(
            "240810",
            "원익IPS",
            "order_bundle_submitted",
            {
                "actual_order_submitted": "true",
                "broker_order_submitted": "True",
                "price_delta_since_first_seen_pct": "1.05",
            },
            emitted_at="2026-06-30T11:04:20",
        ),
        _event(
            "240810",
            "원익IPS",
            "holding_started",
            {
                "actual_order_submitted": "True",
                "order_requested_qty": "1",
                "order_filled_qty": "1",
                "fill_qty": "1",
            },
            emitted_at="2026-06-30T11:05:20",
        ),
        _event(
            "240810",
            "원익IPS",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "1.05", "reason": "below_buy_ratio"},
            emitted_at="2026-06-30T11:06:00",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-30", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["real_submit_symbol_count"] == 0
    assert report["summary"]["rising_missed_buy_count"] == 1
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "240810"
    assert item["real_submit_count"] == 0
    assert item["latest_blocker"]["stage"] == "blocked_strength_momentum"


def test_build_report_event_until_excludes_later_submit_from_window(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-30.jsonl"
    rows = [
        _event(
            "000888",
            "상한필터",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "1.00"},
            emitted_at="2026-06-30T09:59:00",
        ),
        _event(
            "000888",
            "상한필터",
            "broker_buy_submit",
            {"price_delta_since_first_seen_pct": "1.00", "actual_order_submitted": "true"},
            emitted_at="2026-06-30T10:00:01",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        pipeline_path=path,
        generated_at="fixed",
        since="2026-06-30T08:00:00",
        event_until="2026-06-30T10:00:00",
    )

    assert report["summary"]["real_submit_symbol_count"] == 0
    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["event_window"]["until"] == "2026-06-30T10:00:00"
