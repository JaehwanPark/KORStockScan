from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from src.engine import daily_threshold_cycle_report as daily_report
from src.engine import threshold_cycle_preopen_apply as preopen_apply
from src.engine.scalping import scale_in_split_order_plan as split_plan


def _patch_dirs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(split_plan, "DATA_DIR", data_dir)
    monkeypatch.setattr(split_plan, "REPORT_DIR", data_dir / "report" / "scale_in_split_order_plan")
    monkeypatch.setattr(split_plan, "POLICY_DIR", data_dir / "threshold_cycle" / "scale_in_split_order_policy")
    return data_dir


def _write_source_quality_pass(data_dir, target_date):
    path = data_dir / "report" / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )


def _write_source_quality_excluded_gap(data_dir, target_date):
    path = data_dir / "report" / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "pass",
                "summary": {
                    "hard_blocking_contract_gap_count": 2,
                    "hard_blocking_excluded_row_count": 2,
                    "raw_row_exclusion_applied": True,
                },
            }
        ),
        encoding="utf-8",
    )


def _write_pipeline_events(data_dir, target_date, events):
    path = data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


def test_allocator_preserves_avg_down_qty_and_offsets(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale_in_split_order_plan:test",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "default_bucket": {
                    "context_bucket": "default",
                    "leg_count": 2,
                    "price_offsets_ticks": [0, 1],
                    "price_offsets_pct": [0.0, 0.3],
                    "qty_weights": [0.7, 0.3],
                    "qty_weight_min": 0.5,
                    "qty_weight_max": 0.5,
                    "policy_mode": "bounded_equal_scale_in_split_baseline",
                    "split_variant_id": "scale_in_equal_50_50_offset_0pct_0_3pct",
                },
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 5, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        stock={"strategy": "SCALPING"},
        action={"add_type": "AVG_DOWN", "reason": "late_loss_avg_down_retry"},
        price_resolution={"order_price": 10000, "best_bid": 10000},
    )

    assert fields["scale_in_split_order_policy_applied"] is True
    assert fields["scale_in_split_order_leg_count"] == 2
    assert sum(order["qty"] for order in orders) == 5
    assert min(order["qty"] for order in orders) >= 1
    assert [order["qty"] for order in orders] == [4, 1]
    assert orders[0]["price"] == 10000
    assert orders[1]["price"] == 9970
    assert fields["scale_in_split_order_price_offsets_pct"] == "0.0,0.3"


def test_allocator_skips_qty_one_pyramid_and_splits_market_avg_down(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale_in_split_order_plan:test",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "default_bucket": {
                    "leg_count": 2,
                    "price_offsets_ticks": [0, 1],
                    "qty_weight_min": 0.5,
                    "qty_weight_max": 0.5,
                    "policy_mode": "bounded_equal_scale_in_split_baseline",
                    "split_variant_id": "scale_in_equal_50_50_offset_0pct_0_3pct",
                },
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    _, qty_fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 1, "price": 10000, "add_type": "AVG_DOWN"},
        action={"add_type": "AVG_DOWN"},
    )
    _, pyramid_fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 4, "price": 10000, "add_type": "PYRAMID"},
        action={"add_type": "PYRAMID"},
    )
    market_orders, market_fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 4, "price": 0, "order_type_code": "3", "add_type": "AVG_DOWN"},
        action={"add_type": "AVG_DOWN"},
        price_resolution={"order_price": 0, "best_bid": 10000},
    )
    best_limit_orders, best_limit_fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 4, "price": 0, "order_type_code": "6", "add_type": "AVG_DOWN"},
        action={"add_type": "AVG_DOWN"},
        price_resolution={"order_price": 0, "best_bid": 10000},
    )

    assert qty_fields["scale_in_split_order_skip_reason"] == "qty_lte_1"
    assert pyramid_fields["scale_in_split_order_skip_reason"] == "not_avg_down"
    assert market_fields["scale_in_split_order_policy_applied"] is True
    assert market_fields["scale_in_split_order_market_order_applied"] is True
    assert sum(order["qty"] for order in market_orders) == 4
    assert {order["price"] for order in market_orders} == {0}
    assert best_limit_fields["scale_in_split_order_policy_applied"] is True
    assert best_limit_fields["scale_in_split_order_market_order_applied"] is True
    assert sum(order["qty"] for order in best_limit_orders) == 4
    assert {order["price"] for order in best_limit_orders} == {0}


def test_allocator_applies_explicit_three_leg_avg_down_policy(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale_in_split_order_plan:test-three-leg",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "buckets": {
                    "scalping:late_loss_retry:normal": {
                        "context_bucket": "scalping:late_loss_retry:normal",
                        "leg_count": 3,
                        "price_offsets_ticks": [0, 1, 2],
                        "price_offsets_pct": [0.0, 0.3, 0.8],
                        "qty_weights": [0.5, 0.25, 0.25],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.25,
                        "policy_mode": "bounded_three_leg_tick_band",
                        "split_variant_id": "scale_in_bounded_50_25_25_offset_0pct_0_3pct_0_8pct",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 8, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        stock={"strategy": "SCALPING"},
        action={"add_type": "AVG_DOWN", "reason": "late_loss_avg_down_retry"},
        price_resolution={"order_price": 10000, "best_bid": 10000},
    )

    assert fields["scale_in_split_order_policy_applied"] is True
    assert fields["scale_in_split_order_policy_requested_leg_count"] == 3
    assert fields["scale_in_split_order_leg_count"] == 3
    assert fields["scale_in_split_order_leg_count_clipped"] is False
    assert [item["qty"] for item in orders] == [4, 2, 2]
    assert [item["price"] for item in orders] == [10000, 9970, 9920]
    assert sum(item["qty"] for item in orders) == 8


def test_allocator_runtime_default_uses_one_pct_when_policy_bucket_missing(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v1",
                "policy_version": "scale_in_split_order_plan:test",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 2, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        stock={"strategy": "SCALPING"},
        action={"add_type": "AVG_DOWN", "reason": "unmapped_avg_down_reason"},
        price_resolution={"order_price": 10000},
    )

    assert fields["scale_in_split_order_policy_applied"] is True
    assert fields["scale_in_split_order_runtime_default_policy_applied"] is True
    assert fields["scale_in_split_order_price_offsets_pct"] == "0.0,0.3"
    assert [order["price"] for order in orders] == [10000, 9970]


def test_report_and_preopen_env_handoff(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    report_dir = tmp_path / "report" / "scale_in_split_order_plan"
    policy_file = (
        tmp_path
        / "threshold_cycle"
        / "scale_in_split_order_policy"
        / f"scale_in_split_order_policy_{target_date}.json"
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daily_report, "SCALE_IN_SPLIT_ORDER_PLAN_DIR", report_dir)
    (report_dir / f"scale_in_split_order_plan_{target_date}.json").write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_plan_v1",
                "source_quality": {"status": "pass", "tuning_input_allowed": True},
                "input_summary": {"avg_down_observation_count": 3},
                "candidate_grid": [
                    {
                        "context_bucket": "scalping:late_loss_retry:normal",
                        "real_sample_count": 1,
                        "sim_sample_count": 2,
                        "policy_mode": "bounded_equal_scale_in_split_baseline",
                    }
                ],
                "recommended_policy": {
                    "policy_file": str(policy_file),
                    "policy_version": "scale_in_split_order_plan:test",
                    "candidates": [
                        {
                            "context_bucket": "scalping:late_loss_retry:normal",
                            "policy_mode": "bounded_equal_scale_in_split_baseline",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    family = daily_report._build_scale_in_split_order_plan_family(target_date=target_date)
    candidates = daily_report._build_calibration_candidates([family], {})
    candidate = next(item for item in candidates if item["family"] == "scale_in_split_order_plan")

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["recommended_values"]["enabled"] is True
    overrides = preopen_apply._env_overrides_for_candidate(candidate)
    assert overrides["KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert overrides["KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE"] == str(policy_file)
    assert overrides["KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION"] == "scale_in_split_order_plan:test"


def test_report_selects_low_pct_touch_70_30_counterfactual(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "request_price": 10000,
                "order_type": "00",
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:20+09:00",
                "stock_code": "123456",
                "curr_price": 9990,
            },
        ],
    )

    report = split_plan.build_report(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["price_offsets_ticks"] == [0, 1]
    assert candidate["price_offsets_pct"] == [0.0, 0.3]
    assert candidate["qty_weights"] == [0.7, 0.3]
    assert candidate["policy_mode"] == "counterfactual_tick_band_selector"
    assert candidate["post_submit_touch_rates"]["touch_1tick_rate"] == 1.0
    assert candidate["post_submit_touch_rates"]["touch_2tick_rate"] == 0.0
    assert candidate["post_submit_touch_rates"]["touch_0_5pct_rate"] == 0.0


def test_report_selects_70_30_when_touch_low_or_missed_upside_high(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "request_price": 10000,
                "order_type": "00",
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:10+09:00",
                "stock_code": "123456",
                "curr_price": 10010,
            },
        ],
    )

    report = split_plan.build_report(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["price_offsets_ticks"] == [0, 1]
    assert candidate["price_offsets_pct"] == [0.0, 0.3]
    assert candidate["qty_weights"] == [0.7, 0.3]
    assert candidate["selection_reason"] == "touch_0_3pct_low_or_missed_upside_high"


def test_report_allows_source_quality_gap_when_rows_are_excluded(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_excluded_gap(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "request_price": 10000,
                "order_type": "00",
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:20+09:00",
                "stock_code": "123456",
                "curr_price": 9990,
            },
        ],
    )

    report = split_plan.build_report(target_date)

    assert report["source_quality"]["tuning_input_allowed"] is True
    assert report["source_quality"]["raw_row_exclusion_applied"] is True
    assert report["recommended_policy"]["runtime_apply_allowed"] is True


def test_report_selects_0_2tick_60_40_when_two_tick_touch_high(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "request_price": 10000,
                "order_type": "00",
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:20+09:00",
                "stock_code": "123456",
                "curr_price": 9850,
            },
        ],
    )

    report = split_plan.build_report(target_date)
    candidate = report["recommended_policy"]["candidates"][0]
    diagnostic = report["recommended_policy"]["diagnostic_candidates"][0]

    assert candidate["price_offsets_ticks"] == [0, 2]
    assert candidate["price_offsets_pct"] == [0.0, 0.8]
    assert candidate["qty_weights"] == [0.6, 0.4]
    assert candidate["selection_reason"] == "touch_0_8pct_high_with_low_missed_upside"
    assert diagnostic["price_offsets_ticks"] == [0, 1, 2]
    assert diagnostic["price_offsets_pct"] == [0.0, 0.3, 0.8]
    assert diagnostic["runtime_apply_allowed"] is False


def test_report_promotes_three_leg_candidate_after_runtime_sample_floor(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    events = []
    for idx in range(split_plan.THREE_LEG_RUNTIME_SAMPLE_FLOOR):
        code = f"{idx:06d}"
        minute = idx % 60
        events.extend(
            [
                {
                    "stage": "late_loss_avg_down_retry_submitted",
                    "emitted_at": f"2026-07-07T09:{minute:02d}:00+09:00",
                    "stock_code": code,
                    "record_id": idx + 1,
                    "strategy": "SCALPING",
                    "add_type": "AVG_DOWN",
                    "reason": "late_loss_avg_down_retry",
                    "actual_order_submitted": True,
                    "request_price": 10000,
                    "order_type": "00",
                },
                {
                    "stage": "stat_action_decision_snapshot",
                    "emitted_at": f"2026-07-07T09:{minute:02d}:20+09:00",
                    "stock_code": code,
                    "curr_price": 9980,
                },
            ]
        )
    _write_pipeline_events(data_dir, target_date, events)

    report = split_plan.build_report(target_date)

    assert report["input_summary"]["runtime_three_leg_candidate_count"] == 1
    assert report["input_summary"]["diagnostic_three_leg_candidate_count"] == 0
    assert len(report["recommended_policy"]["candidates"]) == 1
    candidate = report["recommended_policy"]["candidates"][0]
    assert candidate["leg_count"] == 3
    assert candidate["policy_mode"] == split_plan.POLICY_MODE_BOUNDED_THREE_LEG
    assert candidate["runtime_apply_allowed"] is True
    assert (
        report["policy_artifact"]["buckets"]["scalping:late_loss_retry:normal"]["leg_count"]
        == 3
    )


def test_three_leg_candidate_stays_diagnostic_when_missed_upside_is_high():
    candidate = split_plan._three_leg_candidate(
        "scalping:late_loss_retry:normal",
        {
            "post_submit_observed_sample": split_plan.THREE_LEG_RUNTIME_SAMPLE_FLOOR,
            "touch_1tick_rate": 0.8,
            "touch_2tick_rate": 0.5,
            "missed_upside_proxy_rate": 0.4,
        },
    )

    assert candidate is not None
    assert candidate["runtime_apply_allowed"] is False
    assert candidate["diagnostic_only"] is True
    assert candidate["policy_mode"] == split_plan.POLICY_MODE_DIAGNOSTIC_THREE_LEG


def test_report_keeps_market_avg_down_qty_split_only(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "stop_line_touch_mandatory_avg_down_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "stop_line_touch_mandatory_avg_down",
                "actual_order_submitted": True,
                "final_price": 0,
                "order_type": "3",
                "price_source": "stop_line_touch_market",
            },
        ],
    )

    report = split_plan.build_report(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["policy_mode"] == "market_qty_split_only"
    assert candidate["price_offsets_ticks"] == "market"
    assert candidate["qty_weights"] == [0.5, 0.5]


def test_report_reconstructs_submitted_anchor_from_execution_without_reason(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "record_id": 17,
                "add_type": "AVG_DOWN",
                "add_reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "order_type": "00",
            },
            {
                "stage": "scale_in_executed",
                "emitted_at": "2026-07-07T09:00:01+09:00",
                "stock_code": "123456",
                "record_id": 17,
                "add_type": "AVG_DOWN",
                "actual_order_submitted": True,
                "fill_price": 10000,
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:30+09:00",
                "stock_code": "123456",
                "record_id": 17,
                "curr_price": 9990,
            },
            {
                "stage": "sell_order_sent",
                "emitted_at": "2026-07-07T09:01:00+09:00",
                "stock_code": "123456",
                "record_id": 17,
                "reason": "trailing profit sell reason must not become scale-in bucket",
                "curr_price": 10020,
            },
        ],
    )

    report = split_plan.build_report(target_date)
    candidates = report["recommended_policy"]["candidates"]

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["context_bucket"] == "unknown_strategy:late_loss_retry:normal"
    assert candidate["counterfactual_anchor_count"] == 1
    assert candidate["post_submit_observed_sample"] == 1
    assert candidate["price_observation_join_gap_count"] == 0
    assert candidate["base_price_reconstruction_gap_count"] == 0
    assert candidate["anchor_samples"][0]["base_price_source"] == "reconstructed_from_scale_in_executed"
    assert candidate["policy_mode"] == "counterfactual_tick_band_selector"


def test_report_falls_back_when_anchor_price_reconstruction_fails(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "order_type": "00",
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:20+09:00",
                "stock_code": "123456",
                "curr_price": 9990,
            },
        ],
    )

    report = split_plan.build_report(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["policy_mode"] == "bounded_equal_scale_in_split_baseline"
    assert candidate["selection_reason"] == "counterfactual_sample_or_price_observation_missing"
    assert report["input_summary"]["base_price_reconstruction_gap_count"] == 1
