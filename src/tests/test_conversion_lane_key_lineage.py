import gzip
import json
from pathlib import Path

from src.engine.automation import conversion_lane as lane
from src.engine.automation import key_lineage_ledger as ledger
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer
def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _dual_replay_payload(target_date="2026-09-12"):
    contract = optimizer._entry_cohort_contract(
        {
            "candidate_summaries": [
                {
                    "stage": "entry",
                    "effective_venue": "INTEGRATED",
                    "session_bucket": "KRX_NXT_AFTERMARKET",
                    "market_data_route": "SOR",
                    "cohort_key_version": "v2",
                    "authority_state": "OBSERVE_ONLY",
                }
            ]
        }
    )
    dual = contract["expected_cohorts"][-1]
    digest = contract["contract_content_sha256"]
    batch = {
        "target_date": target_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "cohort_contract": contract,
        "cohort_contract_sha256": digest,
        "candidate_prompt_selection_source": {"cohort_contract_sha256": digest},
        "cohorts": [{
            **dual, "status": "completed_observe_only", "runtime_effect": False,
            "allowed_runtime_apply": False, "actual_order_submitted": False,
            "candidate_contract_sha256": None,
        }],
    }
    consumer = {
        "target_date": target_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_bindings": {"entry_cohort_contract_sha256": digest},
        "request_paths": {"entry_base": {"cohorts": [{
            **dual,
            "path_status": "intentionally_blocked_with_owner_and_acceptance_test",
            "terminality": "terminal_source_observation",
        }]}},
    }
    return batch, consumer


def test_dual_replay_lineage_is_hash_bound_and_observe_only():
    batch, consumer = _dual_replay_payload()
    status = ledger.entry_replay_observe_only_status(
        batch, consumer, target_date="2026-09-12"
    )

    assert status["status"] == "pass"
    assert len(status["cohorts"]) == 1
    candidate = lane._dual_observe_only_conversion_candidate(status["cohorts"][0])
    assert candidate["conversion_state"] == "terminal_source_only_exclusion"
    assert candidate["excluded_from_real_queue_reason"] == (
        "dual_aftermarket_observe_only_no_live_approval"
    )



def _patch_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        ledger, "REPORT_DIR", tmp_path / "report" / "key_lineage_ledger"
    )
    monkeypatch.setattr(
        ledger, "APPLY_PLAN_DIR", tmp_path / "threshold_cycle" / "apply_plans"
    )
    monkeypatch.setattr(
        ledger, "HYPOTHESIS_PLAN_DIR",
        tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans",
    )
    monkeypatch.setattr(lane, "DATA_DIR", tmp_path)
    monkeypatch.setattr(lane, "REPORT_DIR", tmp_path / "report" / "conversion_lane")

def test_conversion_lane_merges_lineage_match_into_existing_lifecycle_candidate(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    source_bucket_id = "bucket:source:1"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [
                {
                    "source_key_id": source_bucket_id,
                    "source_key_type": "bucket",
                    "same_key_continuity": "pass",
                    "conversion_state": "matched",
                    "runtime_match_key": source_bucket_id,
                    "postclose_observed_key": source_bucket_id,
                    "evidence": {"primary_ev": 1.2, "sample": 12, "sample_floor": 10},
                }
            ],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket:source",
                    "source_bucket_id": source_bucket_id,
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "sample": 12,
                    "sample_floor": 10,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    candidate = next(
        item
        for item in report["conversion_candidates"]
        if item["source_key_id"] == source_bucket_id
    )

    assert candidate["conversion_state"] == "runtime_observed"
    assert candidate["runtime_observed_same_key"] is True
    assert (
        candidate["runtime_observation_scope"]
        == "previous_preopen_policy_runtime_observed"
    )
    assert report["summary"]["positive_ev_runtime_observed_count"] == 1


def test_conversion_lane_does_not_count_non_positive_ev_as_positive(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [
                {
                    "source_key_id": "lifecycle_flow:combo_entry:abc123",
                    "source_key_type": "bucket",
                    "source_artifact": "scalp_sim_policy_catalog",
                    "same_key_continuity": "pass",
                    "conversion_state": "matched",
                    "evidence": {
                        "classification_state": "lifecycle_flow_sim_probe_candidate",
                        "primary_ev": -0.1,
                        "sample": 4,
                        "bucket_id": "lifecycle_flow:combo_entry",
                    },
                }
            ],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {},
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["real_conversion_queue_count"] == 0
    assert report["summary"]["positive_ev_runtime_observed_count"] == 0
    assert report["summary"]["top_blocker_ranked_class"] == "sample_floor"
    assert report["summary"]["top_blocker_by_count_class"] == "sample_floor"
    assert report["summary"]["positive_ev_real_conversion_queue_count"] == 0


def test_conversion_lane_promotes_lineage_blocker_to_rank(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 1},
            "lineage_rows": [],
            "lineage_blockers": [
                {
                    "blocker_id": "b1",
                    "source_key_id": "seed_x",
                    "source_key_type": "active_seed",
                    "next_repair_action": "runtime_observed_seed_not_in_catalog",
                }
            ],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket_a",
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "sample": 3,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["key_lineage_blocker_count"] == 1
    assert report["conversion_blocker_rank"][0]["blocker_class"] == "key_lineage"


def test_conversion_lane_submit_drought_blockers_have_split_axes(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {},
    )
    _write(
        tmp_path
        / "report"
        / "buy_funnel_sentinel"
        / f"buy_funnel_sentinel_{target}.json",
        {
            "schema_version": 4,
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
                "submit_drought_handoff_state": "handoff_required",
                "submit_drought_root_cause": {
                    "latency_root_cause_counts": {"unknown_latency_reason": 7},
                    "quote_freshness_attribution": {
                        "refresh_subreason_counts": {
                            "ws_snapshot_refresh_failed_stale": 3,
                            "observer_quote_refresh_failed_missing": 2,
                            "observer_quote_refresh_failed_stale": 1,
                        },
                        "refresh_attempted_count": 5,
                        "refresh_applied_count": 0,
                        "latency_pass_recovered_count": 1,
                        "order_bundle_submitted_after_refresh_count": 1,
                    },
                    "unknown_latency_reason_count": 7,
                    "unknown_latency_workorder_required": True,
                },
            },
            "entry_submit_drought_contract": {
                "core_handoff_axes": [
                    "UPSTREAM_GATE",
                    "LATENCY_PRE_SUBMIT",
                    "ENTRY_AI_AUTHORITY_REVALIDATION",
                    "PRICE_REVALIDATION",
                    "BROKER_RECEIPT",
                ],
                "exact_attempt_contract": {
                    "identity_field": "record_id",
                    "identity_fallback_allowed": False,
                    "status": "pass",
                    "exclusion_applied": True,
                    "terminal_causal_partition_disjoint": True,
                    "core_handoff_axes": [
                        "UPSTREAM_GATE",
                        "LATENCY_PRE_SUBMIT",
                        "ENTRY_AI_AUTHORITY_REVALIDATION",
                        "PRICE_REVALIDATION",
                        "BROKER_RECEIPT",
                    ],
                },
                "causal_bottleneck_axes": [
                    "LATENCY_PRE_SUBMIT",
                    "BUDGET_PASS_COLLAPSE",
                ],
                "observation_only_axes": ["SIM_REAL_AUTHORITY"],
                "no_current_signal_axes": ["BROKER_RECEIPT"],
                "observation_breakdown": {
                    "exact_attempt_contract": {
                        "identity_field": "record_id",
                        "identity_fallback_allowed": False,
                        "status": "pass",
                        "exclusion_applied": True,
                        "terminal_causal_partition_disjoint": True,
                        "core_handoff_axes": [
                            "UPSTREAM_GATE",
                            "LATENCY_PRE_SUBMIT",
                            "ENTRY_AI_AUTHORITY_REVALIDATION",
                            "PRICE_REVALIDATION",
                            "BROKER_RECEIPT",
                        ],
                    },
                    "axes": {
                        "LATENCY_PRE_SUBMIT": {
                            "status": "observed",
                            "observed_count": 7,
                            "exact_join_valid": True,
                        }
                    },
                },
            },
        },
    )

    from datetime import datetime, timedelta
    from src.engine.buy_funnel_sentinel import PipelineEvent
    from src.tests.submit_drought_fixtures import make_report

    rows = []
    for i in range(7):
        for offset, stage in enumerate(("budget_pass", "latency_block")):
            rows.append(
                PipelineEvent(
                    datetime.fromisoformat(f"{target}T10:00:00")
                    + timedelta(seconds=2 * i + offset),
                    "ENTRY_PIPELINE",
                    stage,
                    "fixture",
                    "000001",
                    str(i + 1),
                    {"reason": "latency_state_danger"},
                )
            )
    path = (
        tmp_path
        / "report"
        / "buy_funnel_sentinel"
        / f"buy_funnel_sentinel_{target}.json"
    )
    payload = json.loads(path.read_text())
    source = make_report(target, events=rows)
    payload.update(
        schema_version=5,
        target_date=target,
        as_of=source["as_of"],
        entry_submit_drought_contract=source["entry_submit_drought_contract"],
    )
    _write(path, payload)
    report = lane.build_conversion_lane(target)

    assert report["summary"]["submit_drought_split_complete"] is True
    assert report["summary"]["submit_drought_closure_axis_count"] == 1
    assert report["summary"]["submit_drought_causal_bottleneck_axes"] == [
        "LATENCY_PRE_SUBMIT",
    ]
    assert report["summary"]["submit_drought_observation_only_axes"] == [
        "BUDGET_PASS_COLLAPSE",
        "SIM_REAL_AUTHORITY",
    ]
    assert (
        "BROKER_RECEIPT" in report["summary"]["submit_drought_no_current_signal_axes"]
    )
    assert report["summary"]["submit_funnel_blocker_count"] == 1
    assert report["summary"]["submit_drought_is_ldm_bucket_blocker"] is False
    assert report["summary"]["buy_funnel_source_present"] is True
    assert (
        report["summary"]["buy_funnel_classification_primary"]
        == "SUBMIT_DROUGHT_CRITICAL"
    )
    assert (
        report["summary"]["submit_drought_blocker_source_state"]
        == "submit_drought_critical"
    )
    assert report["summary"]["submit_drought_unknown_latency_reason_count"] == 7
    assert (
        report["summary"]["submit_drought_unknown_latency_workorder_required"] is True
    )
    assert report["summary"]["submit_drought_refresh_attempted_count"] == 5
    assert (
        report["summary"]["submit_drought_quote_freshness_subaction_counts"][
            "close_ws_snapshot_refresh_stale_source"
        ]
        == 3
    )
    assert (
        report["summary"]["submit_drought_quote_freshness_subaction_counts"][
            "close_observer_quote_missing"
        ]
        == 2
    )
    assert (
        report["summary"]["submit_drought_quote_freshness_subaction_counts"][
            "close_observer_quote_stale_source"
        ]
        == 1
    )
    assert (
        report["summary"]["submit_drought_quote_freshness_subaction_counts"][
            "close_unknown_latency_reason"
        ]
        == 7
    )
    assert report["summary"]["top_ldm_bucket_blocker_class"] is None
    submit_blockers = [
        item
        for item in report["conversion_blocker_rank"]
        if item["blocker_class"] == "submit_drought"
    ]
    assert {item["blocker_axis"] for item in submit_blockers} == {
        "LATENCY_PRE_SUBMIT",
    }
    latency_blocker = next(
        item for item in submit_blockers if item["blocker_axis"] == "LATENCY_PRE_SUBMIT"
    )
    assert (
        latency_blocker["next_repair_action"]
        == "close_submit_drought_latency_pre_submit_quote_freshness"
    )
    assert (
        latency_blocker["quote_freshness_subaction_counts"][
            "close_observer_quote_missing"
        ]
        == 2
    )
    assert all(item["blocker_runtime_effect"] is False for item in submit_blockers)
    assert all(
        item["blocker_allowed_runtime_apply"] is False for item in submit_blockers
    )


def test_conversion_lane_preserves_price_revalidation_axis_contract(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path
        / "report"
        / "buy_funnel_sentinel"
        / f"buy_funnel_sentinel_{target}.json",
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL", "PRICE_GUARD_DROUGHT"],
            },
            "entry_submit_drought_contract": {
                "causal_bottleneck_axes": ["PRICE_REVALIDATION"],
                "observation_breakdown": {
                    "metric_role": "funnel_count",
                    "window_policy": "same_session_unique_attempt_submit_funnel",
                    "sample_floor": "one_explicit_attempt_per_axis",
                    "primary_decision_metric": (
                        "causal_bottleneck_axis_observed_count"
                    ),
                    "source_quality_gate": (
                        "lossless_attempt_key_and_explicit_stage_provenance"
                    ),
                    "forbidden_uses": ["broker_order_submit"],
                    "axes": {
                        "PRICE_REVALIDATION": {
                            "status": "observed",
                            "observed_count": 14,
                            "evidence": {
                                "price_guard_unique": 14,
                                "order_bundle_submitted_unique": 0,
                            },
                            "next_repair_action": (
                                "join executable BBO and first-hit outcomes"
                            ),
                        }
                    },
                },
            },
        },
    )

    report = lane.build_conversion_lane(target)
    blocker = next(
        item
        for item in report["conversion_blocker_rank"]
        if item["blocker_axis"] == "PRICE_REVALIDATION"
    )

    assert blocker["axis_observed_count"] == 14
    assert blocker["axis_evidence"]["price_guard_unique"] == 14
    assert "nonblocking fallback" in blocker["acceptance_test"]
    assert "standalone runtime authority" in blocker["acceptance_test"]
    assert blocker["blocker_runtime_effect"] is False
    assert blocker["blocker_allowed_runtime_apply"] is False


def test_conversion_lane_requires_exact_valid_core_axis_for_new_reports():
    buy_funnel = {
        "schema_version": 4,
        "classification": {
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
        },
        "entry_submit_drought_contract": {
            "exact_attempt_contract": {"status": "source_quality_gap_excluded"},
            "causal_bottleneck_axes": ["PRICE_REVALIDATION"],
            "observation_breakdown": {
                "axes": {
                    "PRICE_REVALIDATION": {
                        "status": "observed",
                        "observed_count": 3,
                        "exact_join_valid": False,
                    }
                }
            },
        },
    }

    assert lane._submit_drought_causal_axes(buy_funnel) == []
    assert lane._submit_drought_blockers(buy_funnel) == []


def test_conversion_lane_does_not_manufacture_legacy_critical_axes():
    buy_funnel = {
        "classification": {
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
        },
        "entry_submit_drought_contract": {},
    }

    assert lane._submit_drought_causal_axes(buy_funnel) == []
    assert lane._submit_drought_blockers(buy_funnel) == []


def test_conversion_lane_preserves_entry_ai_authority_axis_contract(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path
        / "report"
        / "buy_funnel_sentinel"
        / f"buy_funnel_sentinel_{target}.json",
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": [
                    "SUBMIT_DROUGHT_CRITICAL",
                    "ENTRY_AI_AUTHORITY_DROUGHT",
                ],
            },
            "entry_submit_drought_contract": {
                "causal_bottleneck_axes": ["ENTRY_AI_AUTHORITY_REVALIDATION"],
                "observation_breakdown": {
                    "axes": {
                        "ENTRY_AI_AUTHORITY_REVALIDATION": {
                            "status": "observed",
                            "observed_count": 14,
                            "evidence": {
                                "entry_ai_authority_guard_unique": 14,
                                "order_bundle_submitted_unique": 0,
                            },
                        }
                    }
                },
            },
        },
    )

    report = lane.build_conversion_lane(target)
    blocker = next(
        item
        for item in report["conversion_blocker_rank"]
        if item["blocker_axis"] == "ENTRY_AI_AUTHORITY_REVALIDATION"
    )

    assert blocker["axis_observed_count"] == 14
    assert "exact payload lineage" in blocker["acceptance_test"]
    assert "does not depend on positive EV samples" in blocker["acceptance_test"]
    assert blocker["blocker_runtime_effect"] is False


def test_conversion_lane_terminal_entry_metadata_is_not_open_bridge_blocker(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    candidate_id = "entry_wait6579_score66_69_recovery_gate_v1:2026-06-04"
    _write(
        tmp_path
        / "report"
        / "runtime_apply_gap_audit"
        / f"runtime_apply_gap_audit_{target}.json",
        {
            "candidate_route_ledger": [
                {
                    "candidate_id": candidate_id,
                    "domain": "scalping",
                    "producer_state": "entry_only_bridge_metadata",
                    "bridge_state": "excluded",
                    "final_disposition": "source_only_explicit_exclusion",
                    "derived_review_category": "source_only_explicit_exclusion",
                    "failure_reason": ("entry_only_bridge_metadata_not_live_candidate"),
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    candidate = next(
        item
        for item in report["conversion_candidates"]
        if item["candidate_id"] == candidate_id
    )

    assert candidate["conversion_state"] == "terminal_source_only_exclusion"
    assert candidate["next_blocker"] == "not_applicable"
    assert candidate["strategy_scope"] == "scalp"
    assert report["summary"]["terminal_source_only_exclusion_count"] == 1
    assert report["summary"]["unscoped_conversion_candidate_count"] == 0
    assert not any(
        item["conversion_candidate_id"] == candidate_id
        for item in report["conversion_blocker_rank"]
    )


def test_conversion_lane_records_buy_funnel_non_submit_drought_source_state(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {},
    )
    _write(
        tmp_path
        / "report"
        / "buy_funnel_sentinel"
        / f"buy_funnel_sentinel_{target}.json",
        {
            "report_type": "buy_funnel_sentinel",
            "classification": {
                "primary": "PRICE_GUARD_DROUGHT",
                "matches": ["PRICE_GUARD_DROUGHT", "LATENCY_DROUGHT"],
            },
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["submit_funnel_blocker_count"] == 0
    assert report["summary"]["submit_drought_split_complete"] is False
    assert report["summary"]["buy_funnel_source_present"] is True
    assert report["summary"]["buy_funnel_report_type"] == "buy_funnel_sentinel"
    assert (
        report["summary"]["buy_funnel_classification_primary"] == "PRICE_GUARD_DROUGHT"
    )
    assert report["summary"]["buy_funnel_classification_matches"] == [
        "PRICE_GUARD_DROUGHT",
        "LATENCY_DROUGHT",
    ]
    assert (
        report["summary"]["submit_drought_blocker_source_state"]
        == "not_submit_drought_critical"
    )


def test_conversion_lane_marks_new_positive_postclose_candidate_not_due_until_next_preopen(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {
                "lineage_blocker_count": 0,
                "runtime_policy_source_date": "2026-06-04",
                "postclose_candidate_source_date": target,
                "new_postclose_candidates_due_state": "not_due_until_next_preopen",
            },
            "lineage_rows": [],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "entry:source_stage:wait6579_ev_cohort",
                    "source_bucket_id": "entry:source_stage:wait6579_ev_cohort:abc",
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 2.0,
                    "sample": 52,
                    "sample_floor": 10,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    assert report["conversion_candidates"] == []


def test_conversion_lane_counts_known_positive_sample_floor_shortfall(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "lifecycle_flow:thin_positive",
                    "source_bucket_id": "lifecycle_flow:thin_positive:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "sample": 1,
                    "sample_floor": 10,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)
    assert report["conversion_candidates"] == []


def test_conversion_lane_marks_mixed_sample_floor_windows(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path
        / "report"
        / "key_lineage_ledger"
        / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [],
            "lineage_blockers": [],
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {"source_window_policy": "scalp_daily_window"},
            "surfaced_candidates": [
                {
                    "bucket_id": "scalp:thin_positive",
                    "source_bucket_id": "scalp:thin_positive:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "sample": 1,
                    "sample_floor": 10,
                }
            ],
        },
    )
    _write(
        tmp_path
        / "report"
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {"source_window_policy": "swing_rolling_window"},
            "surfaced_candidates": [
                {
                    "bucket_id": "swing:thin_positive",
                    "source_bucket_id": "swing:thin_positive:abc",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.8,
                    "sample": 1,
                    "sample_floor": 10,
                }
            ],
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 1
    assert (
        report["summary"]["positive_ev_sample_floor_window_policy"]
        == "swing_rolling_window"
    )
    assert report["summary"]["positive_ev_sample_floor_window_policy_counts"] == {
        "swing_rolling_window": 1,
    }
    markdown = lane._render_markdown(report)
    assert "window_counts=`{'swing_rolling_window': 1}`" in markdown

    scalp_only = lane.build_conversion_lane(target, include_swing=False)

    assert scalp_only["strategy_scope"] == "scalp_only"
    assert scalp_only["swing_sources_enabled"] is False
    assert scalp_only["summary"]["conversion_candidate_count"] == 0
    assert scalp_only["summary"]["swing_conversion_candidate_count"] == 0
    assert scalp_only["conversion_candidates"] == []


def test_key_lineage_marks_mixed_sample_floor_windows(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-05"
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {"summary": {"source_window_policy": "scalp_daily_window"}},
    )
    _write(
        tmp_path
        / "threshold_cycle"
        / "scalp_sim_policies"
        / "scalp_sim_policy_catalog_2026-06-04.json",
        {
            "hypothesis_observation_plan": {
                "hypotheses": [{"hypothesis_id": "hypothesis_a"}]
            }
        },
    )
    _write(
        tmp_path
        / "threshold_cycle"
        / "swing_sim_policies"
        / "swing_sim_policy_catalog_2026-06-04.json",
        {},
    )
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": "2026-06-04",
            "scalp_sim_auto_approval": {
                "catalog": str(
                    tmp_path
                    / "threshold_cycle"
                    / "scalp_sim_policies"
                    / "scalp_sim_policy_catalog_2026-06-04.json"
                )
            },
            "swing_sim_auto_approval": {
                "catalog": str(
                    tmp_path
                    / "threshold_cycle"
                    / "swing_sim_policies"
                    / "swing_sim_policy_catalog_2026-06-04.json"
                )
            },
        },
    )
    _write(
        tmp_path
        / "report"
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target}.json",
        {
            "summary": {"source_window_policy": "scalp_daily_window"},
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket_a",
                    "source_bucket_id": "bucket_a:source",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.6,
                    "sample": 1,
                    "sample_floor": 10,
                },
                {
                    "bucket_id": "bucket_b",
                    "source_bucket_id": "bucket_b:source",
                    "classification_state": "lifecycle_flow_sim_probe_candidate",
                    "source_quality_adjusted_ev_pct": 0.7,
                    "sample": 1,
                    "sample_floor": 10,
                    "sample_floor_window_policy": "bucket_custom_window",
                },
            ],
        },
    )

    report = ledger.build_key_lineage_ledger(target)
    assert report["summary"]["positive_ev_sample_floor_blocked_count"] == 0


def test_conversion_blocker_class_ignores_source_key_field_names():
    row = {
        "source_key_type": "bucket",
        "source_key_id": "bucket_a",
        "next_blocker": "bridge_contract",
        "bridge_state": "blocked_contract_gap",
    }

    assert lane._blocker_class("bridge_contract", row) == "bridge_contract"


def test_conversion_lane_separates_incomplete_lifecycle_from_source_quality():
    candidate = lane._candidate_from_lifecycle(
        {
            "bucket_id": "lifecycle_flow:incomplete_a",
            "classification_state": "source_only_keep_collecting",
            "source_dimension_gap": "lifecycle_flow_incomplete_stage_contract",
            "flow_sim_transition_blocker": ("lifecycle_flow_incomplete_stage_contract"),
            "recommended_resolution": "explicit_lifecycle_flow_source_only_blocker",
            "sample": 8,
        },
        "scalp",
    )

    assert candidate["source_quality_state"] == "pass"
    assert candidate["conversion_state"] == "source_only_incomplete_lifecycle"
    assert candidate["next_blocker"] == "lifecycle_stage_underproduction"
    assert (
        lane._blocker_class(candidate["next_blocker"], candidate)
        == "lifecycle_stage_underproduction"
    )


def test_conversion_lane_marks_not_applicable_without_open_blocker():
    candidate = lane._candidate_from_lifecycle(
        {
            "bucket_id": "entry:exit_rule:exit_unknown",
            "classification_state": "source_only_keep_collecting",
            "source_dimension_gap": "entry_label_missing",
            "recommended_resolution": "entry_label_not_applicable",
        },
        "scalp",
    )

    assert candidate["source_quality_state"] == "pass"
    assert candidate["conversion_state"] == "terminal_not_applicable"
    assert candidate["next_blocker"] == "not_applicable"


def test_key_lineage_event_io_guard_streams_and_truncates_untracked_ids(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_KEY_LINEAGE_EVENT_UNTRACKED_VALUE_LIMIT", "1")
    target = "2026-06-04"
    _write(
        catalog_path := tmp_path
        / "threshold_cycle"
        / "swing_sim_policies"
        / f"swing_sim_policy_catalog_{target}.json",
        {
            "schema_version": "swing_sim_policy_catalog_v1",
            "active_arm_priority_policies": [
                {
                    "priority_policy_id": "tracked_policy",
                    "status": "active",
                    "source_report_date": target,
                    "priority_arm_id": "arm-1",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                }
            ]
        },
    )
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": target,
            "swing_sim_auto_approval": {"catalog": str(catalog_path)},
        },
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        "\n".join(
            [
                json.dumps({"fields": {"priority_policy_id": "unknown_a"}}),
                json.dumps({"fields": {"priority_policy_id": "unknown_b"}}),
                json.dumps({"fields": {"priority_policy_id": "tracked_policy"}}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["same_key_continuity_pass_count"] == 1
    guard = report["summary"]["event_io_guard"]
    assert guard["mode"] == "streaming_jsonl"
    assert guard["lines_read"] == 3
    assert guard["truncated_untracked_value_count"] == 1
    assert guard["truncated_untracked_value_count_by_field"] == {
        "priority_policy_id": 1
    }


def test_key_lineage_event_io_guard_skips_oversized_lines(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_KEY_LINEAGE_EVENT_LINE_BYTES_LIMIT", "20")
    target = "2026-06-04"
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps({"fields": {"priority_policy_id": "too_large"}}) + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["source_key_count"] == 0
    assert report["summary"]["event_io_guard"]["oversized_line_skipped_count"] == 1


def test_key_lineage_streams_gzip_event_artifact(tmp_path):
    path = tmp_path / "pipeline_events_2026-07-31.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"stage": "test", "fields": {"x": 1}}) + "\n")
    values = {
        "io_guard": {
            "lines_read": 0,
            "oversized_line_skipped_count": 0,
            "json_decode_error_count": 0,
            "file_read_error_count": 0,
        }
    }

    rows = list(ledger._iter_jsonl_payloads(path, values, line_bytes_limit=1000))

    assert rows[0]["fields"]["x"] == 1
    assert values["io_guard"]["lines_read"] == 1
    assert values["io_guard"]["file_read_error_count"] == 0
