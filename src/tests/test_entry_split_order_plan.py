from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

from src.engine.scalping import entry_split_order_plan as split_plan
from src.engine import sniper_post_sell_feedback as post_sell_feedback
from src.engine import daily_threshold_cycle_report as daily_report
from src.engine import threshold_cycle_preopen_apply as preopen_apply


def test_runtime_apply_authority_contract_rejects_unknown_semantics():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": True,
            "runtime_apply_compatibility_semantics": "unknown_union_contract",
            "exploration_seed_allowed": True,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": ["bounded_exploration_seed"],
        }
    )

    assert valid is False
    assert reason == "runtime_apply_compatibility_semantics_invalid"


def test_runtime_apply_authority_contract_rejects_string_boolean():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": "true",
            "runtime_apply_compatibility_semantics": (
                split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
            ),
            "exploration_seed_allowed": True,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": ["bounded_exploration_seed"],
        }
    )

    assert valid is False
    assert reason == "runtime_apply_allowed_not_boolean"


def test_runtime_apply_authority_contract_rejects_malformed_authority_classes():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": False,
            "runtime_apply_compatibility_semantics": (
                split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
            ),
            "exploration_seed_allowed": False,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": "none",
        }
    )

    assert valid is False
    assert reason == "runtime_apply_authority_classes_not_string_list"


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _patch_dirs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(split_plan, "DATA_DIR", data_dir)
    monkeypatch.setattr(
        split_plan, "REPORT_DIR", data_dir / "report" / "entry_split_order_plan"
    )
    monkeypatch.setattr(
        split_plan,
        "POLICY_DIR",
        data_dir / "threshold_cycle" / "entry_split_order_policy",
    )
    return data_dir


def test_build_report_excludes_source_quality_hard_block_and_keeps_real_sim_split(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    events = []
    for idx in range(20):
        events.append(
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
                "stock_code": f"R{idx:03d}",
            }
        )
    for idx in range(10):
        events.append(
            {
                "date": target_date,
                "stage": "scalp_sim_buy_order_assumed_filled",
                "actual_order_submitted": False,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
                "stock_code": f"S{idx:03d}",
            }
        )
    events.append(
        {
            "date": target_date,
            "stage": "order_leg_sent",
            "actual_order_submitted": False,
            "spread_bps": 5,
            "buy_pressure_10t": 72,
            "stock_code": "SIMLIKE_FALSE_REAL_STAGE",
        }
    )
    events.append(
        {
            "date": target_date,
            "stage": "bad_contract_stage",
            "actual_order_submitted": True,
            "spread_bps": 5,
            "buy_pressure_10t": 72,
        }
    )
    events.append(
        {
            "date": target_date,
            "stage": "entry_split_order_plan_skipped",
            "actual_order_submitted": False,
            "broker_order_forbidden": False,
            "spread_bps": 5,
            "buy_pressure_10t": 72,
        }
    )
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", events
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {
                    "tuning_input_allowed": True,
                    "hard_blocking_stages": ["bad_contract_stage"],
                    "raw_row_exclusion_applied": True,
                },
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        data_dir / "post_sell" / f"sim_post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "profit_rate": 1.2,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
            for _ in range(10)
        ],
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "actual_order_submitted": True,
                "profit_rate": 1.4,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
            for _ in range(20)
        ]
        + [
            {
                "date": target_date,
                "actual_order_submitted": False,
                "profit_rate": 99.0,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
        ],
    )

    report = split_plan.build_report(target_date, write=True)

    assert report["schema_version"] == "entry_split_order_plan_v1"
    assert report["input_summary"]["excluded_source_quality_event_count"] == 1
    urgent = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "urgent_tight_spread"
    )
    assert urgent["real_sample_count"] == 20
    assert urgent["sim_sample_count"] == 10
    assert urgent["real_outcome_joined_sample"] == 20
    assert urgent["primary_sample_book"] == "real_submit_execution_shape"
    assert urgent["real_bucket_outcome_ev_pct"] == 1.4
    assert urgent["real_split_variant_outcome_joined_sample"] == 0
    assert urgent["diagnostic_sim_ev_pct"] == 1.2
    assert urgent["source_quality_adjusted_ev_pct"] is None
    assert urgent["policy_mode"] == "bounded_equal_split_baseline"
    assert urgent["candidate_passed"] is True
    assert urgent["exploration_seed_allowed"] is True
    assert urgent["ev_validated_runtime_apply_allowed"] is False
    assert urgent["runtime_apply_authority_class"] == "bounded_exploration_seed"
    assert report["recommended_policy"]["runtime_apply_allowed"] is True
    assert report["recommended_policy"]["exploration_seed_allowed"] is True
    assert report["recommended_policy"]["ev_validated_runtime_apply_allowed"] is False
    assert report["recommended_policy"]["candidate_count"] == 1
    assert report["recommended_policy"]["baseline_runtime_defaults_enabled"] is True
    assert report["recommended_policy"]["explicit_bucket_count"] == 0
    assert report["recommended_policy"]["runtime_apply_scope"] == [
        "baseline_split_structure"
    ]
    assert report["recommended_policy"]["post_apply_attribution"]["required"] is True
    assert (
        report["recommended_policy"]["rollback_guard"]["action"]
        == "carry_forward_previous_runtime_policy"
    )
    assert (
        report["recommended_policy"]["candidates"][0]["runtime_apply_scope"]
        == "baseline_split_structure"
    )
    assert (
        report["recommended_policy"]["candidates"][0]["source_quality_adjusted_ev_pct"]
        is None
    )
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["runtime_apply_allowed"] is True
    assert policy["exploration_seed_allowed"] is True
    assert policy["ev_validated_runtime_apply_allowed"] is False
    assert policy["runtime_apply_authority_classes"] == ["bounded_exploration_seed"]
    assert policy["baseline_runtime_defaults_enabled"] is True
    assert policy["explicit_bucket_count"] == 0
    assert policy["buckets"] == {}
    assert split_plan.policy_path(target_date).exists()


def test_build_report_suppresses_policy_candidates_when_source_quality_blocked(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    events = [
        {
            "date": target_date,
            "stage": (
                "order_leg_sent" if idx < 20 else "scalp_sim_buy_order_assumed_filled"
            ),
            "actual_order_submitted": idx < 20,
            "spread_bps": 5,
            "buy_pressure_10t": 72,
        }
        for idx in range(70)
    ]
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", events
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "fail", "summary": {"tuning_input_allowed": False}}),
        encoding="utf-8",
    )
    _write_jsonl(
        data_dir / "post_sell" / f"sim_post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "profit_rate": 1.2,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
            for _ in range(50)
        ],
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "actual_order_submitted": True,
                "profit_rate": 1.3,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
            for _ in range(20)
        ],
    )

    report = split_plan.build_report(target_date, write=True)

    assert report["source_quality"]["tuning_input_allowed"] is False
    assert report["candidate_grid"] == []
    assert report["input_summary"]["excluded_source_quality_event_count"] == 70
    assert report["recommended_policy"]["candidate_count"] == 0
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    assert report["recommended_policy"]["baseline_runtime_defaults_enabled"] is False
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["runtime_apply_allowed"] is False
    assert policy["exploration_seed_allowed"] is False
    assert policy["ev_validated_runtime_apply_allowed"] is False
    assert policy["buckets"] == {}


def test_build_report_merges_late_candidate_and_reconstructs_split_provenance(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_bundle_submitted",
                "record_id": 123,
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
                "entry_split_order_policy_applied": True,
                "entry_split_order_policy_mode": "bounded_equal_split_baseline",
                "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "entry_split_order_leg_count": 2,
            }
        ],
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_candidates_{target_date}.jsonl",
        [
            {
                "post_sell_id": "late-candidate",
                "signal_date": target_date,
                "recommendation_id": 123,
                "actual_order_submitted": True,
                "profit_rate": 1.25,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=False)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["real_outcome_joined_sample"] == 1
    assert balanced["real_split_variant_outcome_joined_sample"] == 1
    assert balanced["real_split_variant_ev_pct"] == 1.25
    assert balanced["observed_real_split_outcome_count"] == 1
    assert balanced["observed_real_split_variants"] == [
        {
            "split_variant_id": "equal_50_50_offset_0pct_0_3pct",
            "sample_count": 1,
            "equal_weight_avg_profit_pct": 1.25,
        }
    ]
    assert report["input_summary"]["real_post_sell_join"] == {
        "candidate_count": 1,
        "evaluation_count": 0,
        "matched_evaluation_count": 0,
        "pending_evaluation_count": 1,
        "merged_count": 1,
        "reconstructed_split_provenance_count": 1,
    }


def test_provenance_reconstruction_ignores_false_split_flags_and_keeps_explicit_bucket():
    rows = [
        {
            "recommendation_id": 123,
            "actual_order_submitted": True,
            "profit_rate": 1.0,
        },
        {
            "recommendation_id": 456,
            "actual_order_submitted": True,
            "profit_rate": 2.0,
        },
    ]
    events = [
        {
            "stage": "order_bundle_submitted",
            "record_id": 123,
            "entry_split_order_policy_applied": False,
            "entry_split_order_runtime_default_policy_applied": False,
        },
        {
            "stage": "order_bundle_submitted",
            "record_id": 456,
            "entry_split_order_policy_applied": True,
            "entry_split_order_bucket": "balanced_normal",
            "entry_split_order_policy_mode": "bounded_equal_split_baseline",
            "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
        },
    ]

    enriched, reconstructed_count = split_plan._enrich_real_post_sell_provenance(
        rows, events
    )

    assert reconstructed_count == 1
    assert "entry_split_order_policy_applied" not in enriched[0]
    assert split_plan._context_bucket(enriched[1]) == "balanced_normal"


def test_build_report_reads_threshold_cycle_events_from_contract_path(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    _write_jsonl(
        data_dir / "threshold_cycle" / f"threshold_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=False)

    assert report["input_summary"]["source_paths"]["threshold_events"] == str(
        data_dir / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"
    )
    assert report["input_summary"]["loaded_event_count"] == 1
    assert report["candidate_grid"][0]["real_sample_count"] == 1


def test_build_report_updates_cumulative_judgment_from_one_mature_outcome(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    target_date = "2026-07-07"
    for day in (source_date, target_date):
        _write_jsonl(
            data_dir / "pipeline_events" / f"pipeline_events_{day}.jsonl",
            [
                {
                    "date": day,
                    "stage": "order_bundle_submitted",
                    "record_id": 100 if day == source_date else 200,
                    "actual_order_submitted": True,
                    "broker_order_submitted": True,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_policy_applied": True,
                    "entry_split_order_policy_mode": ("bounded_equal_split_baseline"),
                    "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
                }
            ],
        )
        source_quality_path = (
            data_dir
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json"
        )
        source_quality_path.parent.mkdir(parents=True, exist_ok=True)
        source_quality_path.write_text(
            json.dumps(
                {
                    "status": "warning",
                    "summary": {"tuning_input_allowed": True},
                }
            ),
            encoding="utf-8",
        )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{source_date}.jsonl",
        [
            {
                "date": source_date,
                "recommendation_id": 100,
                "actual_order_submitted": True,
                "profit_rate": 1.25,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
                "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
            }
        ],
    )

    report = split_plan.build_report(target_date, write=False)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert report["execution_contract"] == {
        "schedule": "daily_postclose",
        "wrapper_default_enabled": True,
        "calibration_window": "clean_baseline_cumulative_through_target_date",
    }
    assert report["input_summary"]["source_dates"] == [source_date, target_date]
    assert balanced["real_sample_count"] == 1
    assert balanced["target_date_contribution"]["real_sample_count"] == 1
    assert balanced["cumulative_judgment_quality"] == {
        "learning_sample_floor": 1,
        "learning_sample_count": 1,
        "learning_updated": True,
        "learning_update_policy": (
            "one_mature_split_variant_outcome_updates_cumulative_judgment_quality"
        ),
        "equal_weight_avg_profit_pct": 1.25,
        "runtime_promotion_sample_floor": {
            "real_submit": 20,
            "real_split_variant_outcome": 20,
        },
        "split_variant_quality": [
            {
                "split_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "sample_count": 1,
                "equal_weight_avg_profit_pct": 1.25,
                "learning_sample_floor": 1,
                "learning_updated": True,
                "runtime_promotion_sample_floor": 20,
                "runtime_promotion_sample_ready": False,
                "downside_p10_profit_rate": 1.25,
                "runtime_evidence_ready": False,
                "runtime_promotion_requires_shape_provenance": True,
            }
        ],
        "learning_floor_grants_runtime_promotion": False,
    }
    assert balanced["candidate_passed"] is False
    assert report["recommended_policy"]["runtime_apply_allowed"] is False


def test_quality_counts_deduplicates_submit_lifecycle_and_ignores_propagated_flag():
    events = [
        {
            "source_date": "2026-07-07",
            "stage": "order_bundle_submitted",
            "record_id": 123,
            "stock_code": "005930",
            "actual_order_submitted": True,
            "broker_order_submitted": True,
            "spread_bps": 18,
            "buy_pressure_10t": 55,
        },
        {
            "source_date": "2026-07-07",
            "stage": "order_leg_sent",
            "record_id": 123,
            "stock_code": "005930",
            "actual_order_submitted": True,
            "broker_order_submitted": True,
            "spread_bps": 18,
            "buy_pressure_10t": 55,
        },
        {
            "source_date": "2026-07-07",
            "stage": "sell_completed",
            "record_id": 123,
            "stock_code": "005930",
            "actual_order_submitted": True,
            "spread_bps": 18,
            "buy_pressure_10t": 55,
        },
    ]

    counts, excluded = split_plan._quality_counts(
        events, {"tuning_input_allowed": True}
    )

    assert excluded == 0
    assert counts["balanced_normal"]["real_sample_count"] == 1
    assert counts["balanced_normal"]["real_submitted_count"] == 1


def test_build_report_uses_prior_cumulative_state_for_daily_increment(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    target_date = "2026-07-07"
    for day, record_id, profit_rate in (
        (source_date, 100, 1.0),
        (target_date, 200, 2.0),
    ):
        _write_jsonl(
            data_dir / "pipeline_events" / f"pipeline_events_{day}.jsonl",
            [
                {
                    "date": day,
                    "stage": "order_bundle_submitted",
                    "record_id": record_id,
                    "actual_order_submitted": True,
                    "broker_order_submitted": True,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
                }
            ],
        )
        _write_jsonl(
            data_dir / "post_sell" / f"post_sell_evaluations_{day}.jsonl",
            [
                {
                    "date": day,
                    "recommendation_id": record_id,
                    "actual_order_submitted": True,
                    "profit_rate": profit_rate,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
                }
            ],
        )
        source_quality_path = (
            data_dir
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json"
        )
        source_quality_path.parent.mkdir(parents=True, exist_ok=True)
        source_quality_path.write_text(
            json.dumps(
                {
                    "status": "warning",
                    "summary": {"tuning_input_allowed": True},
                }
            ),
            encoding="utf-8",
        )

    split_plan.build_report(source_date, write=True)
    (data_dir / "pipeline_events" / f"pipeline_events_{source_date}.jsonl").unlink()
    (data_dir / "post_sell" / f"post_sell_evaluations_{source_date}.jsonl").unlink()

    report = split_plan.build_report(target_date, write=False)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert (
        report["input_summary"]["aggregation_mode"]
        == "incremental_from_prior_cumulative_state"
    )
    assert report["input_summary"]["source_dates"] == [source_date, target_date]
    assert report["cumulative_state"]["through_date"] == target_date
    assert report["cumulative_state"]["clean_tuning_baseline_date"] == "2026-06-05"
    assert balanced["real_sample_count"] == 2
    assert balanced["cumulative_judgment_quality"]["learning_sample_count"] == 2
    assert balanced["cumulative_judgment_quality"]["equal_weight_avg_profit_pct"] == 1.5


def test_prior_cumulative_state_is_rejected_after_source_quality_refresh(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    report_path = split_plan.REPORT_DIR / f"entry_split_order_plan_{source_date}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.SCHEMA_VERSION,
                "cumulative_state": {
                    "window_policy": ("clean_baseline_cumulative_through_target_date"),
                    "through_date": source_date,
                    "clean_tuning_baseline_date": "2026-06-05",
                    "source_dates": [source_date],
                },
            }
        ),
        encoding="utf-8",
    )
    os.utime(report_path, (1, 1))
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{source_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps(
            {
                "status": "pass",
                "summary": {"tuning_input_allowed": True},
            }
        ),
        encoding="utf-8",
    )

    state, state_path = split_plan._latest_prior_cumulative_state("2026-07-07")

    assert state == {}
    assert state_path == ""


def test_build_report_creates_bounded_equal_baseline_without_real_outcome(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
            for _ in range(20)
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["real_sample_count"] == 20
    assert balanced["real_outcome_joined_sample"] == 0
    assert balanced["candidate_passed"] is True
    assert balanced["policy_mode"] == "bounded_equal_split_baseline"
    assert balanced["leg_count"] == 2
    assert balanced["price_offsets_ticks"] == [0, 1]
    assert balanced["qty_weight_min"] == 0.5
    assert balanced["qty_weight_max"] == 0.5
    assert balanced["source_quality_adjusted_ev_pct"] is None
    assert report["recommended_policy"]["candidate_count"] == 1
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["baseline_runtime_defaults_enabled"] is True
    assert policy["explicit_bucket_count"] == 0
    assert policy["buckets"] == {}

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE",
        str(split_plan.policy_path(target_date)),
    )
    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "quote_stale": False,
            "order_price": 1000,
        },
        now=datetime.now(timezone(timedelta(hours=9))),
    )
    assert fields["entry_split_order_policy_applied"] is True
    assert [item["qty"] for item in orders] == [1, 1]
    assert fields["entry_split_order_price_offsets_pct"] == "0.0,0.3"
    assert [item["price"] for item in orders] == [1000, 997]
    assert (
        fields["entry_split_order_policy_variant_id"]
        == split_plan.RUNTIME_FALLBACK_VARIANT_ID
    )
    assert fields["entry_split_order_variant_id"] == (
        f"{split_plan.RUNTIME_FALLBACK_VARIANT_ID}__runtime_first_weight_40"
    )
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True


def test_build_report_uses_split_variant_outcome_as_primary_ev(monkeypatch, tmp_path):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
            for _ in range(20)
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "actual_order_submitted": True,
                "profit_rate": 1.4,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
                "entry_split_order_policy_applied": True,
                "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "entry_split_order_policy_mode": "bounded_equal_split_baseline",
                "entry_split_order_leg_count": 2,
                "entry_split_order_price_offsets_ticks": "0,1",
                "entry_split_order_qty_weight_min": 0.5,
            }
            for _ in range(20)
        ],
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["primary_sample_book"] == "real_split_variant"
    assert balanced["real_split_variant_outcome_joined_sample"] == 20
    assert balanced["source_quality_adjusted_ev_pct"] == 1.4
    assert balanced["policy_mode"] == "real_primary_ev_optimized"
    assert balanced["candidate_passed"] is True
    assert balanced["exploration_seed_allowed"] is False
    assert balanced["ev_validated_runtime_apply_allowed"] is True
    assert balanced["runtime_apply_authority_class"] == "ev_validated_variant"
    assert report["recommended_policy"]["ev_validated_runtime_apply_allowed"] is True


def test_build_report_uses_post_submit_low_tick_band_for_price_offsets(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    rows = []
    for idx in range(20):
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:00",
                "stage": "order_bundle_submitted",
                "record_id": 2000 + idx,
                "stock_code": f"T{idx:05d}"[:6],
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "order_price": 10000,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:30",
                "stage": "holding_price_observed",
                "record_id": 2000 + idx,
                "stock_code": f"T{idx:05d}"[:6],
                "actual_order_submitted": False,
                "current_price_observed": 9980,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", rows
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["policy_mode"] == "post_submit_tick_band_seed"
    assert balanced["optimization_basis"] == "post_submit_observed_low_tick_band"
    assert balanced["leg_count"] == 3
    assert balanced["price_offsets_ticks"] == [0, 1, 2]
    assert balanced["qty_weight_min"] == 0.34
    assert balanced["post_submit_low_tick_band"]["sample_count"] == 20
    assert balanced["post_submit_low_tick_band"]["p75_down_ticks"] == 2.0
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert (
        policy["buckets"]["balanced_normal"]["policy_mode"]
        == "post_submit_tick_band_seed"
    )
    assert policy["buckets"]["balanced_normal"]["price_offsets_ticks"] == [0, 1, 2]
    assert policy["explicit_bucket_count"] == 1


def test_post_submit_tick_band_excludes_source_quality_hard_blocked_rows(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    rows = []
    for idx in range(20):
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:00+09:00",
                "stage": "order_bundle_submitted",
                "record_id": 3000 + idx,
                "stock_code": f"B{idx:05d}"[:6],
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "order_price": 10000,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:30+09:00",
                "stage": "hard_blocked_price_observed",
                "record_id": 3000 + idx,
                "stock_code": f"B{idx:05d}"[:6],
                "current_price_observed": 9980,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", rows
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {
                    "tuning_input_allowed": True,
                    "hard_blocking_stages": ["hard_blocked_price_observed"],
                    "raw_row_exclusion_applied": True,
                },
            }
        ),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["post_submit_low_tick_band"] == {}
    assert balanced["policy_mode"] == "bounded_equal_split_baseline"
    assert balanced["price_offsets_ticks"] == [0, 1]


def test_post_sell_candidate_preserves_entry_split_variant_metadata(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(post_sell_feedback, "DATA_DIR", tmp_path / "data")
    post_sell_feedback._RECORDED_KEYS.clear()
    stock = {
        "name": "TEST",
        "strategy": "SCALPING",
        "fast_exit_decision_mark_price": 1012,
        "fast_exit_decision_executable_sell_price": 1010,
        "fast_exit_decision_peak_price": 1020,
        "fast_exit_decision_quote_state": "consistent",
        "fast_exit_decision_quote_reason": "ok",
        "pending_entry_orders": [
            {
                "entry_split_order_policy_applied": True,
                "entry_split_order_bucket": "balanced_normal",
                "entry_split_order_policy_version": "entry_split_order_plan:test",
                "entry_split_order_policy_mode": "bounded_equal_split_baseline",
                "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "entry_split_order_leg_count": 2,
                "entry_split_order_price_offsets_ticks": "0,1",
                "entry_split_order_qty_weight_min": 0.5,
                "entry_split_order_qty_weight_max": 0.5,
                "entry_split_order_runtime_default_policy_applied": True,
            }
        ],
    }

    payload = post_sell_feedback.record_post_sell_candidate(
        recommendation_id=123,
        stock=stock,
        code="000001",
        sell_time=datetime(2026, 7, 7, 10, 30, tzinfo=timezone(timedelta(hours=9))),
        buy_price=1000,
        sell_price=1010,
        profit_rate=1.0,
        buy_qty=2,
        exit_rule="test_exit",
        strategy="SCALPING",
    )

    assert payload is not None
    assert payload["actual_order_submitted"] is True
    assert payload["entry_split_order_policy_applied"] is True
    assert payload["entry_split_order_variant_id"] == "equal_50_50_offset_0pct_0_3pct"
    assert payload["entry_split_order_price_offsets_ticks"] == "0,1"
    assert payload["entry_split_order_runtime_default_policy_applied"] is True
    assert payload["exit_decision_mark_price"] == 1012
    assert payload["exit_decision_executable_sell_price"] == 1010
    assert payload["exit_decision_peak_price"] == 1020
    assert payload["actual_fill_price"] == 1010


def test_post_sell_candidate_prefers_standard_exit_decision_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(post_sell_feedback, "DATA_DIR", tmp_path / "data")
    post_sell_feedback._RECORDED_KEYS.clear()
    stock = {
        "name": "LG전자",
        "strategy": "SCALPING",
        "last_exit_decision_source": "HOLDING_FLOW_OVERRIDE",
        "exit_decision_mark_price": 184_000,
        "exit_decision_executable_sell_price": 184_000,
        "exit_decision_peak_price": 184_100,
        "exit_decision_quote_state": "single_source",
        "exit_decision_quote_reason": "rest_only_fresh",
        "fast_exit_decision_mark_price": 1,
    }

    payload = post_sell_feedback.record_post_sell_candidate(
        recommendation_id=23086,
        stock=stock,
        code="066570",
        sell_time=datetime(2026, 7, 23, 12, 52, 55),
        buy_price=182_350,
        sell_price=184_000,
        profit_rate=0.67,
        buy_qty=1,
        exit_rule="scalp_low_profit_stagnation_hard_exit",
        strategy="SCALPING",
    )

    assert payload is not None
    assert payload["exit_decision_mark_price"] == 184_000
    assert payload["exit_decision_executable_sell_price"] == 184_000
    assert payload["exit_decision_peak_price"] == 184_100
    assert payload["exit_decision_quote_state"] == "single_source"
    assert payload["exit_decision_quote_reason"] == "rest_only_fresh"


def test_allocator_preserves_qty_and_respects_leg_limits(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {
                    "urgent_tight_spread": {
                        "leg_count": 3,
                        "price_offsets_ticks": [0, 1, 2],
                        "qty_weight_min": 0.6,
                        "qty_weight_max": 0.8,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 5,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        stock={"buy_pressure_10t": 75},
        latency_gate={
            "spread_bps": 5,
            "latency_state": "SAFE",
            "quote_stale": False,
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert len(orders) == 2
    assert sum(item["qty"] for item in orders) == 5
    assert min(item["qty"] for item in orders) >= 1
    assert orders[0]["price"] >= orders[1]["price"]


def test_allocator_uses_runtime_default_for_missing_bucket_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 7,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert (
        fields["entry_split_order_policy_mode"]
        == "runtime_default_passive_center_40_60_0_3pct"
    )
    assert (
        fields["entry_split_order_policy_variant_id"]
        == "runtime_default_passive_center_40_60_offset_0pct_0_3pct"
    )
    assert (
        fields["entry_split_order_variant_id"]
        == "runtime_default_passive_center_40_60_offset_0pct_0_3pct__runtime_first_weight_40"
    )
    assert fields["entry_split_order_price_offsets_ticks"] == "0,1"
    assert fields["entry_split_order_price_offsets_pct"] == "0.0,0.3"
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.4
    assert fields["entry_split_order_qty_weight_max"] == 0.4
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert (
        fields["entry_split_order_passive_bias_reason"]
        == "passive_center_first_leg_cap"
    )
    assert [item["qty"] for item in orders] == [3, 4]
    assert [item["price"] for item in orders] == [1000, 997]


def test_allocator_uses_three_leg_runtime_default_for_missing_passive_bucket(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE", target_date
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 10,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 40,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert fields["entry_split_order_policy_requested_leg_count"] == 3
    assert fields["entry_split_order_leg_count"] == 3
    assert fields["entry_split_order_leg_count_clipped"] is False
    assert [item["qty"] for item in orders] == [5, 2, 3]
    assert [item["price"] for item in orders] == [1000, 997, 992]
    assert [item["order_type_code"] for item in orders] == ["3", "00", "00"]
    assert [item["entry_split_order_execution_mode"] for item in orders] == [
        "market_first",
        "resolver_limit",
        "resolver_limit",
    ]
    assert sum(item["qty"] for item in orders) == 10


def test_allocator_records_qty_clipping_for_three_leg_entry_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 4,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 40,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert len(orders) == 2
    assert fields["entry_split_order_policy_requested_leg_count"] == 3
    assert fields["entry_split_order_max_leg_count_for_qty"] == 2
    assert fields["entry_split_order_leg_count_clipped"] is True
    assert fields["entry_split_order_variant_id"].endswith(
        "__qty_clipped_legs2__runtime_first_weight_40"
    )
    assert sum(item["qty"] for item in orders) == 4


def test_allocator_biases_ai_wait_high_spread_to_passive_leg(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {
                    "passive_wide_or_weak": {
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                        "policy_mode": "bounded_equal_split_baseline",
                        "split_variant_id": "equal_50_50_offset_0pct_0_3pct",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 5,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 50,
            "latency_state": "SAFE",
            "quote_stale": False,
            "pre_submit_effective_quote_stale": False,
            "entry_ai_submit_authority_action": "WAIT",
            "reason": "mixed signals with stale quote and high spread",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_passive_bias_applied"] is True
    assert (
        fields["entry_split_order_policy_variant_id"]
        == "equal_50_50_offset_0pct_0_3pct"
    )
    assert (
        fields["entry_split_order_variant_id"]
        == "equal_50_50_offset_0pct_0_3pct__runtime_first_weight_20"
    )
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.2
    assert fields["entry_split_order_qty_weight_max"] == 0.2
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert fields["entry_split_order_passive_bias_reason"].startswith("ai_wait_with_")
    assert [item["qty"] for item in orders] == [1, 4]
    assert [item["price"] for item in orders] == [1000, 997]
    assert sum(item["qty"] for item in orders) == 5


def test_allocator_passive_centers_buy_action_without_wait_warning(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {
                    "passive_wide_or_weak": {
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 5,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 50,
            "latency_state": "SAFE",
            "entry_ai_submit_authority_action": "BUY",
            "reason": "high spread but positive entry confirmation",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_passive_bias_applied"] is True
    assert (
        fields["entry_split_order_passive_bias_reason"]
        == "passive_center_first_leg_cap"
    )
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.4
    assert fields["entry_split_order_qty_weight_max"] == 0.4
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert [item["qty"] for item in orders] == [2, 3]


def test_allocator_market_first_uses_policy_weight_and_keeps_residual_at_resolver(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-14"
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-market-first",
                "source_date": "2026-07-13",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE", target_date
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 32,
                "price": 12160,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 41.017,
            "buy_pressure_10t": 50,
            "latency_state": "CAUTION",
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_action": "WAIT",
            "best_ask_at_submit": 12240,
            "order_price": 12160,
        },
        now=datetime(2026, 7, 14, 12, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_market_first_leg_applied"] is True
    assert fields["entry_split_order_market_first_leg_qty"] == 16
    assert fields["entry_split_order_qty_weight_min"] == 0.5
    assert fields["entry_split_order_passive_bias_reason"] == ""
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is False
    assert [item["qty"] for item in orders] == [16, 8, 8]
    assert orders[0]["order_type_code"] == "3"
    assert orders[0]["entry_split_order_execution_mode"] == "market_first"
    assert orders[0]["entry_split_order_market_reference_price"] == 12240
    assert orders[1]["order_type_code"] == "00"
    assert orders[1]["entry_split_order_execution_mode"] == "resolver_limit"
    assert orders[1]["price"] < orders[0]["price"]
    assert orders[2]["order_type_code"] == "00"
    assert orders[2]["entry_split_order_execution_mode"] == "resolver_limit"
    assert orders[2]["price"] < orders[1]["price"]


def test_allocator_probe_first_reserves_one_share_and_builds_fill_anchored_residuals(
    monkeypatch, tmp_path
):
    target_date = "2026-07-20"
    policy_file = tmp_path / "entry-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "probe-test",
                "source_date": "2026-07-16",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "3")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "false")

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 10, "price": 10000, "tif": "DAY"}],
        stock={"id": 7, "code": "123456", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 10050,
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_blocked": False,
            "entry_ai_submit_authority_action": "WAIT",
            "entry_ai_submit_authority_result_source": "live",
            "entry_ai_submit_authority_confirmed_at": 100.25,
            "entry_ai_submit_authority_action_source": "latest_stock_ai",
            "entry_ai_submit_authority_wait_probe_required": True,
            "entry_ai_submit_authority_decision_trace_id": "entry-trace-1",
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_probe_first_applied"] is True
    assert fields["entry_split_order_split_qty"] == 10
    assert len(orders) == 1
    assert orders[0]["qty"] == 1
    assert orders[0]["entry_split_order_leg_index"] == 0
    assert orders[0]["entry_split_order_execution_mode"] == "probe_first_market"
    continuation = orders[0]["entry_split_order_probe_continuation"]
    assert sum(continuation["residual_quantities"]) == 9
    runtime_state = split_plan.probe_runtime_state_snapshot(
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    )
    reserved_bundle = runtime_state["bundles"][
        orders[0]["entry_split_order_probe_bundle_id"]
    ]
    assert reserved_bundle["phase"] == "planned"
    assert reserved_bundle["requested_qty"] == 10
    assert reserved_bundle["continuation"] == continuation
    assert reserved_bundle["probe_submit_best_ask"] == 10050
    assert reserved_bundle["timeout_sec"] == 3
    assert reserved_bundle["ai_action_at_submit"] == "WAIT"
    assert reserved_bundle["ai_result_source_at_submit"] == "live"
    assert reserved_bundle["ai_confirmed_at_submit"] == 100.25
    assert reserved_bundle["ai_action_source_at_submit"] == "latest_stock_ai"
    assert reserved_bundle["wait_contract_at_submit"] is True
    assert reserved_bundle["ai_decision_trace_id"] == "entry-trace-1"

    bundle_id = orders[0]["entry_split_order_probe_bundle_id"]
    split_plan.update_probe_runtime_bundle(
        bundle_id,
        phase="probe_submitting",
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    fill_race_stock = {
        "id": 7,
        "code": "123456",
        "strategy": "SCALPING",
        "entry_split_probe_phase": "probe_submitting",
        "entry_split_probe_bundle_id": bundle_id,
        "entry_split_probe_requested_qty": 10,
        "entry_split_probe_continuation": continuation,
        "entry_split_probe_submit_best_ask": 10050,
        "entry_split_probe_ai_action_at_submit": "-",
        "entry_split_probe_ai_result_source_at_submit": "not_available",
        "entry_split_probe_ai_confirmed_at_submit": 0.0,
        "entry_split_probe_ai_action_source_at_submit": "-",
        "entry_split_probe_ai_decision_trace_id": "-",
    }
    recovered = split_plan.recover_probe_submit_contract_for_fill(
        fill_race_stock,
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    assert recovered["recovered"] is True
    assert fill_race_stock["entry_split_probe_ai_action_at_submit"] == "WAIT"
    assert fill_race_stock["entry_split_probe_ai_result_source_at_submit"] == "live"
    assert fill_race_stock["entry_split_probe_ai_confirmed_at_submit"] == 100.25
    assert (
        fill_race_stock["entry_split_probe_ai_action_source_at_submit"]
        == "latest_stock_ai"
    )
    assert fill_race_stock["entry_split_probe_wait_contract_at_submit"] is True
    assert fill_race_stock["entry_split_probe_ai_decision_trace_id"] == "entry-trace-1"

    untrusted_orders, _ = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 9000, "tif": "DAY"}],
        stock={"code": "654321", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 9050,
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_blocked": True,
            "entry_ai_submit_authority_action": "WAIT",
            "entry_ai_submit_authority_result_source": "live",
            "entry_ai_submit_authority_confirmed_at": 100.25,
            "entry_ai_submit_authority_wait_probe_required": True,
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    untrusted_bundle = split_plan.probe_runtime_state_snapshot(
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    )["bundles"][untrusted_orders[0]["entry_split_order_probe_bundle_id"]]
    assert "ai_action_at_submit" not in untrusted_bundle
    assert "wait_contract_at_submit" not in untrusted_bundle

    drop_orders, _ = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 8900, "tif": "DAY"}],
        stock={"id": 9, "code": "654322", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 8950,
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_blocked": False,
            "entry_ai_submit_authority_action": "DROP",
            "entry_ai_submit_authority_result_source": "live",
            "entry_ai_submit_authority_confirmed_at": 100.25,
            "entry_ai_submit_authority_action_source": "latest_stock_ai",
            "entry_ai_submit_authority_decision_trace_id": "drop-trace",
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    drop_bundle = split_plan.probe_runtime_state_snapshot(
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    )["bundles"][drop_orders[0]["entry_split_order_probe_bundle_id"]]
    assert "ai_action_at_submit" not in drop_bundle
    assert "wait_contract_at_submit" not in drop_bundle
    drop_bundle_id = drop_orders[0]["entry_split_order_probe_bundle_id"]
    split_plan.update_probe_runtime_bundle(
        drop_bundle_id,
        phase="probe_submitting",
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    incomplete_recovery = split_plan.recover_probe_submit_contract_for_fill(
        {
            "id": 9,
            "code": "654322",
            "strategy": "SCALPING",
            "entry_split_probe_phase": "probe_submitting",
            "entry_split_probe_bundle_id": drop_bundle_id,
            "entry_split_probe_requested_qty": 4,
            "entry_split_probe_continuation": drop_bundle["continuation"],
            "entry_split_probe_submit_best_ask": 8950,
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    assert incomplete_recovery["recovered"] is False
    assert (
        incomplete_recovery["reason"]
        == "probe_submit_bundle_missing_immutable_ai_contract"
    )

    residuals, residual_fields = split_plan.build_probe_residual_orders(
        continuation,
        probe_fill_price=10080,
        best_bid=10000,
        best_ask=10020,
    )

    assert residual_fields["allowed"] is True
    assert residual_fields["probe_anchor_price"] == 10020
    assert 1 + sum(order["qty"] for order in residuals) == 10
    assert residuals[0]["price"] == 10020
    assert all(order["order_type_code"] == "00" for order in residuals)

    p1_prices = [9970] + [9920] * (len(continuation["residual_quantities"]) - 1)
    p1_residuals, p1_fields = split_plan.build_probe_residual_orders(
        continuation,
        probe_fill_price=10080,
        best_bid=10000,
        best_ask=10020,
        resolved_leg_prices=p1_prices,
    )

    assert p1_fields["allowed"] is True
    assert p1_fields["residual_price_authority"] == ("dynamic_entry_price_resolver_p1")
    assert [order["price"] for order in p1_residuals] == p1_prices
    assert all(
        order["entry_split_order_price_authority"] == "dynamic_entry_price_resolver_p1"
        for order in p1_residuals
    )

    fallback_orders, fallback_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 10, "price": 10000, "tif": "DAY"}],
        stock={"code": "654321", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 10050,
            "quote_stale_at_submit": False,
        },
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )
    assert fallback_fields["entry_split_order_probe_first_skip_reason"] == (
        "probe_active_bundle_cap_reached"
    )
    assert fallback_orders == []
    assert fallback_fields["entry_split_order_probe_first_required"] is True
    assert fallback_fields["entry_split_order_probe_capacity_deferred"] is True

    split_plan.update_probe_runtime_bundle(
        orders[0]["entry_split_order_probe_bundle_id"],
        phase="complete",
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )
    next_orders, next_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 10, "price": 10000, "tif": "DAY"}],
        stock={"code": "654322", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 10050,
            "quote_stale_at_submit": False,
        },
        now=datetime(2026, 7, 20, 10, 2, tzinfo=timezone(timedelta(hours=9))),
    )
    assert next_fields["entry_split_order_probe_first_applied"] is True
    assert len(next_orders) == 1
    assert next_orders[0]["qty"] == 1


def test_probe_first_capacity_counts_all_nonterminal_bundle_phases(
    monkeypatch, tmp_path
):
    target_date = "2026-07-20"
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
                "target_date": target_date,
                "submitted_bundle_count": 1,
                "circuit_open": False,
                "circuit_reason": "",
                "bundles": {
                    "inflight": {"phase": "probe_recheck_pending"},
                    "aborted": {"phase": "aborted"},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "1")

    bundle_id, reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654321", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={
            "continuation": {
                "requested_qty": 2,
                "residual_qty": 1,
                "residual_quantities": [1],
            },
            "probe_submit_best_ask": 10_000,
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert bundle_id == ""
    assert reason == "probe_active_bundle_cap_reached"

    split_plan.update_probe_runtime_bundle(
        "inflight",
        phase="aborted",
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )
    released_bundle_id, released_reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654322", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={
            "continuation": {
                "requested_qty": 2,
                "residual_qty": 1,
                "residual_quantities": [1],
            },
            "probe_submit_best_ask": 10_000,
        },
        now=datetime(2026, 7, 20, 10, 2, tzinfo=timezone(timedelta(hours=9))),
    )

    assert released_bundle_id
    assert released_reason == "reserved"


def test_probe_runtime_reservation_rejects_incomplete_submit_contract(
    monkeypatch, tmp_path
):
    target_date = "2026-07-20"
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")

    bundle_id, reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654323", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={"continuation": {"requested_qty": 2}},
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert bundle_id == ""
    assert reason == "probe_submit_contract_invalid"
    assert state_path.exists() is False

    empty_bundle_id, empty_reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654324", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={
            "continuation": {},
            "probe_submit_best_ask": 10_000,
        },
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )

    assert empty_bundle_id == ""
    assert empty_reason == "probe_submit_contract_invalid"
    assert state_path.exists() is False


def test_allocator_probe_first_applies_to_real_rising_missed_initial_entry(
    monkeypatch, tmp_path
):
    target_date = "2026-07-21"
    policy_file = tmp_path / "entry-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "rising-missed-probe-test",
                "source_date": "2026-07-16",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "5")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE", target_date
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "false")

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 6, "price": 59200, "tif": "DAY"}],
        stock={
            "code": "475150",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "buy_qty": 0,
            "position_tag": "SCANNER",
            "rising_missed_one_share_scout": True,
            "rising_missed_one_share_entry_forced": True,
            # The real initial-scout producer sets this before entering the
            # common submit path. It is not itself an upgrade order marker.
            "rising_missed_scout_upgrade_pending": True,
        },
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 59900,
            "quote_stale_at_submit": False,
        },
        now=datetime(2026, 7, 21, 10, 22, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_probe_first_applied"] is True
    assert len(orders) == 1
    assert orders[0]["qty"] == 1
    assert orders[0]["order_type_code"] == "3"
    assert orders[0]["entry_split_order_execution_mode"] == "probe_first_market"
    assert orders[0]["entry_split_order_probe_continuation"]["residual_qty"] == 5


def test_probe_first_still_excludes_simulated_and_additional_buy_paths():
    opening_rotation = {
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "OPENING_ROTATION",
    }
    simulated = {
        "code": "123456",
        "strategy": "SCALPING",
        "rising_missed_one_share_scout": True,
        "scalp_live_simulator": True,
    }
    additional = {
        "code": "123456",
        "strategy": "SCALPING",
        "rising_missed_one_share_scout": True,
        "pending_add_order": True,
    }
    scout_upgrade = {
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_qty": 1,
        "rising_missed_one_share_entry_forced": True,
        "rising_missed_one_share_scout": True,
        "rising_missed_scout_upgrade_pending": True,
    }
    scout_upgrade_order_pending = {
        "code": "123456",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "buy_qty": 0,
        "rising_missed_one_share_entry_forced": True,
        "rising_missed_one_share_scout": True,
        "rising_missed_scout_upgrade_pending": True,
        "rising_missed_scout_upgrade_order_pending": True,
    }

    assert split_plan._probe_first_eligible(opening_rotation, 6) == (True, "eligible")
    assert split_plan._probe_first_eligible(simulated, 6) == (
        False,
        "simulated_entry_excluded",
    )
    assert split_plan._probe_first_eligible(additional, 6) == (
        False,
        "non_initial_entry_excluded",
    )
    assert split_plan._probe_first_eligible(scout_upgrade, 6) == (
        False,
        "non_initial_entry_excluded",
    )
    assert split_plan._probe_first_eligible(scout_upgrade_order_pending, 6) == (
        False,
        "non_initial_entry_excluded",
    )


def test_probe_runtime_restart_recovery_restores_bundle_and_fails_closed_on_mismatch(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    continuation = {
        "requested_qty": 5,
        "residual_qty": 4,
        "residual_quantities": [2, 2],
    }
    split_plan.update_probe_runtime_bundle(
        "123456-probe-restart",
        phase="probe_filled",
        now=now,
        code="123456",
        target_id=7,
        requested_qty=5,
        continuation=continuation,
        probe_submit_best_ask=10000,
        timeout_sec=3,
        max_slippage_bps=50,
        anchor_mode="fill_clamped_to_fresh_bbo",
        submitted_at=100.0,
        filled_at=101.0,
        fill_price=10010,
        fill_qty=1,
        order_no="P0",
        broker_route="SOR",
        broker_route_resolution="explicit_request",
        effective_venue="KRX",
        ai_action_at_submit="WAIT",
        ai_result_source_at_submit="live",
        ai_confirmed_at_submit=99.8,
        ai_action_source_at_submit="latest_stock_ai",
        wait_contract_at_submit=True,
        probe_confirmation_count=1,
        probe_confirmation_last_at=101.1,
        probe_confirmation_last_state="STRONG",
        probe_confirmation_last_signature="price+tape",
        entry_split_probe_scale_in_forbidden=True,
        probe_expand_forbidden=False,
        residual_orders=[
            {"tag": "planned_only", "qty": 2, "status": "OPEN"},
            {"tag": "submitted", "qty": 2, "status": "OPEN", "ord_no": "R1"},
        ],
    )

    unrelated_stock = {
        "id": 8,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
    }
    unrelated = split_plan.recover_probe_runtime_bundle_for_stock(
        unrelated_stock, now=now
    )
    assert unrelated == {"recovered": False, "reason": "no_incomplete_bundle"}
    assert "entry_split_probe_bundle_id" not in unrelated_stock

    recovered_stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
    }
    result = split_plan.recover_probe_runtime_bundle_for_stock(recovered_stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "incomplete_bundle_restored",
        "phase": "probe_filled",
    }
    assert recovered_stock["entry_split_probe_phase"] == "probe_filled"
    assert recovered_stock["entry_split_probe_continuation"] == continuation
    assert recovered_stock["entry_split_probe_scale_in_forbidden"] is True
    assert recovered_stock["probe_expand_forbidden"] is False
    assert recovered_stock["probe_confirmation_count"] == 1
    assert recovered_stock["probe_confirmation_last_at"] == 101.1
    assert recovered_stock["probe_confirmation_last_state"] == "STRONG"
    assert recovered_stock["probe_confirmation_last_signature"] == "price+tape"
    assert recovered_stock["entry_split_probe_ai_action_at_submit"] == "WAIT"
    assert recovered_stock["entry_split_probe_wait_contract_at_submit"] is True
    assert recovered_stock["entry_split_probe_ai_result_source_at_submit"] == "live"
    assert recovered_stock["entry_split_probe_ai_confirmed_at_submit"] == 99.8
    assert recovered_stock["entry_execution_broker_route"] == "SOR"
    assert (
        recovered_stock["entry_execution_broker_route_resolution"] == "explicit_request"
    )
    assert recovered_stock["entry_execution_route_recorded_at"] == 100.0
    assert recovered_stock["effective_venue"] == "KRX"
    assert recovered_stock["entry_execution_cohort"] == "KRX"
    assert (
        recovered_stock["entry_split_probe_ai_action_source_at_submit"]
        == "latest_stock_ai"
    )
    assert recovered_stock["pending_entry_orders"] == [
        {"tag": "submitted", "qty": 2, "status": "OPEN", "ord_no": "R1"}
    ]

    mismatched_stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 2,
        "status": "HOLDING",
    }
    mismatch = split_plan.recover_probe_runtime_bundle_for_stock(
        mismatched_stock, now=now
    )
    assert mismatch["circuit_open"] is True
    assert mismatched_stock["entry_split_probe_phase"] == "aborted"
    assert mismatched_stock["entry_split_probe_scale_in_forbidden"] is True
    assert mismatched_stock["probe_expand_forbidden"] is True
    assert mismatched_stock["entry_execution_broker_route"] == "SOR"
    assert (
        mismatched_stock["entry_execution_broker_route_resolution"]
        == "explicit_request"
    )
    assert mismatched_stock["entry_execution_route_recorded_at"] == 100.0
    assert mismatched_stock["entry_execution_cohort"] == "KRX"
    state = split_plan._load_json(state_path)
    assert state["circuit_open"] is True
    assert state["circuit_reason"] == "probe_restart_recovery_quantity_mismatch"
    assert (
        state["bundles"]["123456-probe-restart"]["entry_split_probe_scale_in_forbidden"]
        is True
    )
    assert state["bundles"]["123456-probe-restart"]["probe_expand_forbidden"] is True


def test_probe_submitted_restart_mismatch_keeps_confirmed_route_fail_closed(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 8, 13, 12, 49, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "144960-probe-restart",
        phase="probe_submitted",
        now=now,
        code="144960",
        target_id=31480,
        requested_qty=21,
        submitted_at=100.0,
        order_no="0044348",
        broker_route="SOR",
        broker_route_resolution="explicit_request",
        effective_venue="KRX",
    )
    stock = {
        "id": 31480,
        "code": "144960",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": False,
        "reason": "probe_restart_recovery_quantity_mismatch",
        "circuit_open": True,
    }
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_execution_broker_route"] == "SOR"
    assert stock["entry_execution_broker_route_resolution"] == "explicit_request"
    assert stock["entry_execution_route_recorded_at"] == 100.0
    assert stock["entry_execution_cohort"] == "KRX"


def test_probe_restart_mismatch_does_not_overwrite_existing_execution_route(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 8, 13, 12, 49, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "123456-probe-existing-route-mismatch",
        phase="probe_submitted",
        now=now,
        code="123456",
        target_id=9,
        requested_qty=5,
        submitted_at=100.0,
        broker_route="SOR",
        broker_route_resolution="explicit_request",
        effective_venue="KRX",
    )
    stock = {
        "id": 9,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
        "entry_execution_broker_route": "NXT",
        "entry_execution_broker_route_resolution": "broker_fill_receipt",
        "entry_execution_route_recorded_at": 90.0,
        "entry_execution_cohort": "NXT",
        "effective_venue": "NXT",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["circuit_open"] is True
    assert stock["entry_execution_broker_route"] == "NXT"
    assert stock["entry_execution_broker_route_resolution"] == "broker_fill_receipt"
    assert stock["entry_execution_route_recorded_at"] == 90.0
    assert stock["entry_execution_cohort"] == "NXT"
    assert stock["effective_venue"] == "NXT"


def test_probe_recovered_execution_provenance_rejects_unconfirmed_requested_route():
    fields = split_plan._probe_recovered_execution_provenance(
        {
            "dmst_stex_tp": "SOR",
            "effective_venue": "UNKNOWN",
            "submitted_at": 100.0,
        }
    )

    assert fields == {}


def test_probe_runtime_restart_backfills_provenance_for_already_hydrated_bundle(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_ENABLED", "true")
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "123456-probe-already-hydrated"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "123456",
                    "broker_route": "SOR",
                    "broker_route_resolution": "broker_response",
                    "effective_venue": "KRX",
                    "submitted_at": 100.0,
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
        "effective_venue": "KRX",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "already_hydrated_provenance_restored",
        "phase": "aborted",
    }
    assert stock["entry_execution_broker_route"] == "SOR"
    assert stock["entry_execution_broker_route_resolution"] == "broker_response"
    assert stock["entry_execution_route_recorded_at"] == 100.0
    assert stock["entry_execution_cohort"] == "KRX"


def test_probe_runtime_restart_does_not_mix_existing_route_with_bundle_provenance(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "123456-probe-existing-route"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "123456",
                    "broker_route": "SOR",
                    "broker_route_resolution": "broker_response",
                    "effective_venue": "KRX",
                    "submitted_at": 100.0,
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
        "entry_execution_broker_route": "NXT",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {"recovered": False, "reason": "already_hydrated"}
    assert stock["entry_execution_broker_route"] == "NXT"
    assert "entry_execution_broker_route_resolution" not in stock
    assert "entry_execution_cohort" not in stock


def test_probe_runtime_restart_rejects_hydrated_bundle_code_mismatch(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "654321-probe-mismatched"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "654321",
                    "broker_route": "SOR",
                    "effective_venue": "KRX",
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {"recovered": False, "reason": "hydrated_bundle_code_mismatch"}
    assert "entry_execution_broker_route" not in stock


def test_probe_runtime_restart_backfills_hydrated_immutable_contract(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "123456-probe-contract"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "123456",
                    "wait_contract_at_submit": True,
                    "terminal_abort_detail_reason": (
                        "timeout_wait_confirmation_not_reached"
                    ),
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
        "entry_execution_broker_route": "KRX",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "already_hydrated_contract_restored",
        "phase": "aborted",
    }
    assert stock["entry_split_probe_wait_contract_at_submit"] is True
    assert (
        stock["entry_split_probe_terminal_abort_detail_reason"]
        == "timeout_wait_confirmation_not_reached"
    )


def test_probe_runtime_restart_clears_pending_recheck_without_opening_circuit(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "123456-probe-recheck-restart",
        phase="probe_recheck_pending",
        now=now,
        code="123456",
        target_id=7,
        requested_qty=5,
        fill_qty=1,
        recheck_count=2,
        post_probe_direction_state="UNKNOWN",
    )
    stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "post_probe_recheck_cleared_on_restart",
        "phase": "aborted",
    }
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_requested_qty"] == 1
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_split_probe_residual_expand_forbidden"] is True
    assert stock["probe_confirmation_count"] == 0
    assert stock["probe_confirmation_last_state"] == "UNKNOWN"
    assert "entry_split_probe_direction_state" not in stock
    assert stock["entry_split_probe_terminal_outcome"] == "residual_not_submitted"
    assert (
        stock["entry_split_probe_terminal_abort_reason"]
        == "post_probe_recheck_cleared_on_restart"
    )
    state = split_plan._load_json(state_path)
    assert state["circuit_open"] is False
    persisted = state["bundles"]["123456-probe-recheck-restart"]
    assert persisted["phase"] == "aborted"
    assert persisted["entry_split_probe_scale_in_forbidden"] is True
    assert persisted["probe_expand_forbidden"] is True


def test_probe_runtime_restart_releases_source_quality_recheck_for_scale_in(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 23, 12, 22, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "001520-probe-source-recheck",
        phase="probe_recheck_pending",
        now=now,
        code="001520",
        target_id=117,
        requested_qty=1013,
        fill_qty=1,
        recheck_count=5,
        post_probe_direction_state="UNKNOWN",
        post_probe_direction_reason="post_probe_stale_or_conflicted_fresh_quote",
        source_quality_recheck_pending=True,
    )
    stock = {
        "id": 117,
        "code": "001520",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["reason"] == "post_probe_recheck_cleared_on_restart"
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_soft_abort"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["probe_expand_forbidden"] is False
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert (
        stock["entry_split_probe_scale_in_recheck_origin"]
        == "source_quality_restart_recovery"
    )
    assert stock["entry_split_probe_source_quality_recheck_released"] is True
    assert stock["entry_split_probe_source_quality_recheck_unfilled_qty"] == 1012


def test_probe_runtime_restart_preserves_persisted_soft_abort_quantity_truth(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 23, 12, 23, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "001520-probe-soft-abort",
        phase="aborted",
        now=now,
        code="001520",
        target_id=117,
        requested_qty=1013,
        fill_qty=1,
        soft_abort=True,
        scale_in_recheck_allowed=True,
        scale_in_recheck_reason=(
            "residual_revalidation_timeout:source_quality_recovery"
        ),
        source_quality_recheck_released=True,
        source_quality_recheck_unfilled_qty=1012,
        source_quality_recheck_reason=("post_probe_stale_or_conflicted_fresh_quote"),
    )
    stock = {
        "id": 117,
        "code": "001520",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["phase"] == "aborted"
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["probe_expand_forbidden"] is False
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert stock["entry_requested_qty"] == 1
    assert stock["requested_buy_qty"] == 1
    assert stock["entry_split_probe_source_quality_recheck_unfilled_qty"] == 1012
    persisted = split_plan._load_json(state_path)["bundles"]["001520-probe-soft-abort"]
    assert persisted["entry_split_probe_scale_in_forbidden"] is False
    assert persisted["probe_expand_forbidden"] is False


def test_probe_runtime_restart_restores_terminal_abort_guards_and_confirmation(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 24, 12, 0, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "096770-probe-hard-abort",
        phase="aborted",
        now=now,
        code="096770",
        target_id=23735,
        requested_qty=8,
        fill_qty=1,
        reason="residual_revalidation_timeout",
        soft_abort=False,
        probe_confirmation_count=1,
        probe_confirmation_last_at=100.25,
        probe_confirmation_last_state="STRONG",
        probe_confirmation_last_signature="price+tape",
        terminal_at=100.5,
        terminal_outcome="residual_not_submitted",
        terminal_abort_reason="residual_revalidation_timeout",
        terminal_abort_detail_reason="timeout_negative_group_persisted",
        terminal_direction_state="WEAK",
        terminal_direction_reason="post_probe_wait_negative_group",
        terminal_continuation_action="DEFER",
        terminal_positive_groups="-",
        terminal_negative_groups="orderbook",
        terminal_confirmation_count=1,
        terminal_failure_signature=(
            "residual_revalidation_timeout|WEAK|"
            "post_probe_wait_negative_group|orderbook|1/2"
        ),
    )
    stock = {
        "id": 23735,
        "code": "096770",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "incomplete_bundle_restored",
        "phase": "aborted",
    }
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["probe_confirmation_count"] == 1
    assert stock["probe_confirmation_last_at"] == 100.25
    assert stock["probe_confirmation_last_state"] == "STRONG"
    assert stock["probe_confirmation_last_signature"] == "price+tape"
    assert stock["entry_split_probe_terminal_at"] == 100.5
    assert (
        stock["entry_split_probe_abort_detail_reason"]
        == "timeout_negative_group_persisted"
    )
    assert (
        stock["entry_split_probe_terminal_abort_detail_reason"]
        == "timeout_negative_group_persisted"
    )
    assert stock["entry_split_probe_terminal_direction_state"] == "WEAK"
    assert stock["entry_split_probe_terminal_negative_groups"] == "orderbook"
    assert stock["entry_split_probe_terminal_confirmation_count"] == 1
    persisted = split_plan._load_json(state_path)["bundles"]["096770-probe-hard-abort"]
    assert persisted["entry_split_probe_scale_in_forbidden"] is True
    assert persisted["probe_expand_forbidden"] is True


def test_probe_runtime_restart_restores_residual_terminal_scale_in_recheck_lane(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 31, 15, 20, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "066570-probe-recheck",
        phase="aborted",
        now=now,
        code="066570",
        target_id=25602,
        requested_qty=2,
        fill_qty=1,
        reason="residual_revalidation_timeout",
        soft_abort=False,
        scale_in_recheck_allowed=True,
        scale_in_recheck_origin="normal_winner_recovery",
        scale_in_recheck_reason="residual_revalidation_timeout",
        entry_split_probe_scale_in_forbidden=False,
        probe_expand_forbidden=True,
        entry_split_probe_residual_expand_forbidden=True,
        terminal_at=1_785_486_344.269,
        terminal_outcome="residual_not_submitted",
        terminal_abort_reason="residual_revalidation_timeout",
        terminal_direction_state="WEAK",
        terminal_direction_reason="post_probe_wait_negative_group",
        terminal_continuation_action="DEFER",
        terminal_positive_groups="-",
        terminal_negative_groups="price_tick,orderbook",
        terminal_confirmation_count=0,
        terminal_failure_signature=(
            "residual_revalidation_timeout|WEAK|"
            "post_probe_wait_negative_group|price_tick,orderbook|0/2"
        ),
    )
    stock = {
        "id": 25602,
        "code": "066570",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["phase"] == "aborted"
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_split_probe_residual_expand_forbidden"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert (
        stock["entry_split_probe_scale_in_recheck_origin"] == "normal_winner_recovery"
    )
    assert stock["entry_split_probe_terminal_direction_state"] == "WEAK"
    assert stock["entry_split_probe_terminal_negative_groups"] == "price_tick,orderbook"


def test_probe_runtime_restart_ignores_partial_complete_bundle(monkeypatch, tmp_path):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "123456-probe-partial-complete",
        phase="partial_complete",
        now=now,
        code="123456",
        target_id=7,
        requested_qty=10,
        filled_qty=4,
        reason="submitted_residual_orders_terminal",
    )
    stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 4,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {"recovered": False, "reason": "no_incomplete_bundle"}
    assert "entry_split_probe_bundle_id" not in stock
    state = split_plan._load_json(state_path)
    assert state["circuit_open"] is False


def test_allocator_date_bounded_policy_becomes_inactive(monkeypatch, tmp_path):
    policy_file = tmp_path / "entry-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "date-bounded",
                "source_date": "2026-07-13",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", "2026-07-14"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 15, 9, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == "policy_inactive_date"
    assert orders[0]["qty"] == 4


def test_allocator_daily_operator_contract_keeps_probe_first_and_policy_active(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-daily.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "daily-operator",
                "source_date": "2026-07-01",
                "runtime_apply_allowed": True,
                "baseline_runtime_defaults_enabled": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        split_plan, "PROBE_RUNTIME_STATE_PATH", tmp_path / "probe-state.json"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "false")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE", str(policy_file)
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "5")

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "best_ask": 1000,
            "best_bid": 999,
        },
        now=datetime(2026, 8, 3, 9, 3, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_probe_first_applied"] is True
    assert fields["entry_split_order_daily_operator_contract_enabled"] is True
    assert fields["entry_split_order_daily_baseline_fallback_applied"] is True
    assert fields["entry_split_order_stale_policy_operator_authorized"] is True
    assert len(orders) == 1
    assert orders[0]["qty"] == 1


def test_allocator_daily_contract_does_not_authorize_stale_standard_policy(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-stale-standard.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "stale-standard",
                "source_date": "2026-07-01",
                "runtime_apply_allowed": True,
                "baseline_runtime_defaults_enabled": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", "2026-08-03"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED", "true"
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={"spread_bps": 18, "latency_state": "SAFE"},
        now=datetime(2026, 8, 3, 9, 3, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == "stale_policy"
    assert orders == [{"tag": "normal", "qty": 4, "price": 1000}]


def test_allocator_requires_date_bounded_operator_fallback_for_denied_policy(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-denied.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "denied-policy",
                "source_date": "2026-07-13",
                "runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone(timedelta(hours=9)))

    _, blocked_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=now,
    )
    assert (
        blocked_fields["entry_split_order_skip_reason"]
        == "policy_runtime_apply_not_allowed"
    )

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE", "2026-07-14"
    )
    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=now,
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_operator_fallback_authorized"] is True
    assert all(
        item["entry_split_order_operator_fallback_authorized"] is True
        for item in orders
    )


def test_allocator_rejects_contradictory_runtime_apply_authority_contract(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-invalid-authority.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "invalid-authority",
                "source_date": "2026-07-14",
                "runtime_apply_allowed": True,
                "runtime_apply_compatibility_semantics": (
                    "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed"
                ),
                "exploration_seed_allowed": False,
                "ev_validated_runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 14, 12, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert orders == [{"tag": "normal", "qty": 4, "price": 1000}]
    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == (
        "invalid_policy_authority_contract:runtime_apply_authority_union_mismatch"
    )


def test_allocator_allows_split_when_source_quote_stale_recovered_before_submit(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    recovered, recovered_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "quote_stale": True,
            "quote_stale_at_submit": False,
            "pre_submit_effective_quote_stale": False,
            "order_price": 1000,
        },
    )
    assert recovered_fields["entry_split_order_policy_applied"] is True
    assert [item["qty"] for item in recovered] == [1, 1]

    blocked, blocked_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "quote_stale": True,
            "quote_stale_at_submit": True,
            "order_price": 1000,
        },
    )
    assert blocked_fields["entry_split_order_skip_reason"] == "stale_quote"
    assert blocked[0]["qty"] == 2


def test_allocator_fail_closed_for_qty_one_missing_invalid_and_stale_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    one, one_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 1, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert one_fields["entry_split_order_skip_reason"] == "qty_lte_1"
    assert one[0]["qty"] == 1

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(tmp_path / "missing.json")
    )
    _, missing_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert missing_fields["entry_split_order_skip_reason"] == "policy_file_not_found"

    multi, multi_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "a", "qty": 1, "price": 1000}, {"tag": "b", "qty": 1, "price": 995}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert (
        multi_fields["entry_split_order_skip_reason"]
        == "multi_order_input_not_supported_v1"
    )
    assert [item["tag"] for item in multi] == ["a", "b"]

    stale_file = tmp_path / "stale.json"
    stale_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "stale",
                "source_date": "2026-06-01",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(stale_file))
    _, stale_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 7, tzinfo=timezone(timedelta(hours=9))),
    )
    assert stale_fields["entry_split_order_skip_reason"] == "stale_policy"


def test_daily_report_candidate_and_preopen_env_handoff(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    report_dir = tmp_path / "report" / "entry_split_order_plan"
    policy_file = (
        tmp_path
        / "threshold_cycle"
        / "entry_split_order_policy"
        / f"entry_split_order_policy_{target_date}.json"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daily_report, "ENTRY_SPLIT_ORDER_PLAN_DIR", report_dir)
    (report_dir / f"entry_split_order_plan_{target_date}.json").write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_plan_v1",
                "source_quality": {"status": "warning", "tuning_input_allowed": True},
                "input_summary": {"excluded_source_quality_event_count": 2},
                "candidate_grid": [
                    {
                        "context_bucket": "urgent_tight_spread",
                        "real_sample_count": 20,
                        "real_outcome_joined_sample": 20,
                        "sim_sample_count": 10,
                        "primary_sample_book": "real",
                        "source_quality_adjusted_ev_pct": 1.1,
                        "notional_weighted_ev_pct": 1.1,
                        "downside_p10_profit_rate": 0.2,
                    }
                ],
                "recommended_policy": {
                    "runtime_apply_allowed": True,
                    "runtime_apply_compatibility_semantics": "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed",
                    "exploration_seed_allowed": False,
                    "ev_validated_runtime_apply_allowed": True,
                    "runtime_apply_authority_classes": ["ev_validated_variant"],
                    "policy_file": str(policy_file),
                    "policy_version": "entry_split_order_plan:test",
                    "candidates": [
                        {
                            "context_bucket": "urgent_tight_spread",
                            "source_quality_adjusted_ev_pct": 1.1,
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    family = daily_report._build_entry_split_order_plan_family(target_date=target_date)
    candidates = daily_report._build_calibration_candidates([family], {})
    candidate = next(
        item for item in candidates if item["family"] == "entry_split_order_plan"
    )

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["apply_mode"] == "calibrated_apply_candidate"
    assert candidate["source_metrics"]["runtime_apply_authority"] == (
        "ev_validated_variant"
    )
    assert (
        candidate["source_metrics"]["primary_decision_metric"]
        == "source_quality_adjusted_ev_pct"
    )
    assert candidate["recommended_values"]["enabled"] is True
    assert candidate["recommended_values"]["policy_file"] == str(policy_file)
    overrides = preopen_apply._env_overrides_for_candidate(candidate)
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"] == str(policy_file)
    assert (
        overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION"]
        == "entry_split_order_plan:test"
    )


def test_daily_report_handoff_accepts_bounded_equal_baseline(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    report_dir = tmp_path / "report" / "entry_split_order_plan"
    policy_file = (
        tmp_path
        / "threshold_cycle"
        / "entry_split_order_policy"
        / f"entry_split_order_policy_{target_date}.json"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daily_report, "ENTRY_SPLIT_ORDER_PLAN_DIR", report_dir)
    (report_dir / f"entry_split_order_plan_{target_date}.json").write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_plan_v1",
                "source_quality": {"status": "warning", "tuning_input_allowed": True},
                "candidate_grid": [
                    {
                        "context_bucket": "balanced_normal",
                        "real_sample_count": 20,
                        "real_outcome_joined_sample": 0,
                        "sim_sample_count": 0,
                        "primary_sample_book": "real_submit_execution_shape",
                        "policy_mode": "bounded_equal_split_baseline",
                        "source_quality_adjusted_ev_pct": None,
                        "notional_weighted_ev_pct": None,
                    }
                ],
                "recommended_policy": {
                    "runtime_apply_allowed": True,
                    "runtime_apply_compatibility_semantics": "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed",
                    "exploration_seed_allowed": True,
                    "ev_validated_runtime_apply_allowed": False,
                    "runtime_apply_authority_classes": ["bounded_exploration_seed"],
                    "policy_file": str(policy_file),
                    "policy_version": "entry_split_order_plan:baseline",
                    "candidates": [
                        {
                            "context_bucket": "balanced_normal",
                            "policy_mode": "bounded_equal_split_baseline",
                            "source_quality_adjusted_ev_pct": None,
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    family = daily_report._build_entry_split_order_plan_family(target_date=target_date)
    candidates = daily_report._build_calibration_candidates([family], {})
    candidate = next(
        item for item in candidates if item["family"] == "entry_split_order_plan"
    )

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["apply_mode"] == "bounded_exploration_seed_candidate"
    assert candidate["source_metrics"]["runtime_apply_authority"] == (
        "bounded_exploration_seed"
    )
    assert (
        candidate["source_metrics"]["primary_decision_metric"]
        == "qty_preserving_execution_shape_guard"
    )
    assert "양의 EV 판정이 아니다" in candidate["calibration_reason"]
    assert (
        candidate["source_metrics"]["bounded_equal_split_baseline_candidate_count"] == 1
    )
    assert candidate["source_metrics"]["baseline_runtime_defaults_enabled"] is False
    assert candidate["source_metrics"]["explicit_policy_bucket_count"] == 0
    overrides = preopen_apply._env_overrides_for_candidate(candidate)
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"] == str(policy_file)


def test_daily_report_handoff_blocks_runtime_disallowed_policy(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    report_dir = tmp_path / "report" / "entry_split_order_plan"
    policy_file = (
        tmp_path
        / "threshold_cycle"
        / "entry_split_order_policy"
        / f"entry_split_order_policy_{target_date}.json"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daily_report, "ENTRY_SPLIT_ORDER_PLAN_DIR", report_dir)
    (report_dir / f"entry_split_order_plan_{target_date}.json").write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_plan_v1",
                "source_quality": {"status": "pass", "tuning_input_allowed": True},
                "candidate_grid": [
                    {
                        "context_bucket": "balanced_normal",
                        "real_sample_count": 20,
                        "real_outcome_joined_sample": 20,
                        "sim_sample_count": 0,
                        "primary_sample_book": "real_submit_execution_shape",
                        "policy_mode": "bounded_equal_split_baseline",
                    }
                ],
                "recommended_policy": {
                    "runtime_apply_allowed": False,
                    "runtime_apply_compatibility_semantics": "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed",
                    "exploration_seed_allowed": False,
                    "ev_validated_runtime_apply_allowed": False,
                    "policy_file": str(policy_file),
                    "policy_version": "entry_split_order_plan:runtime-blocked",
                    "candidates": [
                        {
                            "context_bucket": "balanced_normal",
                            "policy_mode": "bounded_equal_split_baseline",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    family = daily_report._build_entry_split_order_plan_family(target_date=target_date)
    candidate = next(
        item
        for item in daily_report._build_calibration_candidates([family], {})
        if item["family"] == "entry_split_order_plan"
    )

    assert family["recommended"]["enabled"] is False
    assert family["sample"]["runtime_apply_allowed"] is False
    assert candidate["recommended_value"] is False
    assert candidate["calibration_state"] == "hold"


def test_daily_report_handoff_does_not_expose_declared_authority_when_contract_invalid(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    report_dir = tmp_path / "report" / "entry_split_order_plan"
    policy_file = (
        tmp_path
        / "threshold_cycle"
        / "entry_split_order_policy"
        / f"entry_split_order_policy_{target_date}.json"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daily_report, "ENTRY_SPLIT_ORDER_PLAN_DIR", report_dir)
    (report_dir / f"entry_split_order_plan_{target_date}.json").write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_plan_v1",
                "source_quality": {"status": "pass", "tuning_input_allowed": True},
                "candidate_grid": [
                    {
                        "context_bucket": "balanced_normal",
                        "real_sample_count": 20,
                        "real_outcome_joined_sample": 0,
                        "sim_sample_count": 0,
                        "primary_sample_book": "real_submit_execution_shape",
                        "policy_mode": "bounded_equal_split_baseline",
                    }
                ],
                "recommended_policy": {
                    "runtime_apply_allowed": True,
                    "runtime_apply_compatibility_semantics": (
                        split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
                    ),
                    "exploration_seed_allowed": True,
                    "ev_validated_runtime_apply_allowed": False,
                    "runtime_apply_authority_classes": "bounded_exploration_seed",
                    "policy_file": str(policy_file),
                    "policy_version": "entry_split_order_plan:invalid-contract",
                    "candidates": [
                        {
                            "context_bucket": "balanced_normal",
                            "policy_mode": "bounded_equal_split_baseline",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    family = daily_report._build_entry_split_order_plan_family(target_date=target_date)
    candidate = next(
        item
        for item in daily_report._build_calibration_candidates([family], {})
        if item["family"] == "entry_split_order_plan"
    )

    assert family["sample"]["runtime_apply_authority_contract_valid"] is False
    assert family["sample"]["runtime_apply_authority"] == "invalid_explicit_contract"
    assert family["sample"]["declared_exploration_seed_allowed"] is True
    assert family["sample"]["exploration_seed_allowed"] is False
    assert family["recommended"]["enabled"] is False
    assert candidate["calibration_state"] == "hold"
