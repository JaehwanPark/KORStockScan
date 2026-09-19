from __future__ import annotations

import json
import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from src.engine.scalping import scale_in_split_order_plan as split_plan


def _patch_dirs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(split_plan, "DATA_DIR", data_dir)
    monkeypatch.setattr(
        split_plan, "REPORT_DIR", data_dir / "report" / "scale_in_split_order_plan"
    )
    monkeypatch.setattr(
        split_plan,
        "POLICY_DIR",
        data_dir / "threshold_cycle" / "scale_in_split_order_policy",
    )
    return data_dir


def _write_source_quality_pass(data_dir, target_date):
    path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )


def _write_source_quality_excluded_gap(data_dir, target_date):
    path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
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
    path.write_text(
        "\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8"
    )


def test_postclose_report_consumes_atomic_avg_down_sizing_receipt(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-09-15"
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "scale_in_execution_sizing_plan",
                "emitted_at": f"{target_date}T10:00:00+09:00",
                "stock_code": "005930",
                "record_id": 1,
                "strategy": "SCALPING",
                "add_type": "AVG_DOWN",
                "scale_in_execution_sizing_plan_id": "avg-down-sizing-test",
                "scale_in_execution_sizing_valid": True,
                "scale_in_execution_sizing_quantity_conservation_holds": True,
                "actual_order_submitted": False,
            },
            {
                "stage": "scale_in_order_submitted",
                "emitted_at": f"{target_date}T10:00:01+09:00",
                "stock_code": "005930",
                "record_id": 1,
                "strategy": "SCALPING",
                "add_type": "AVG_DOWN",
                "actual_order_submitted": True,
                "submitted_qty": 2,
                "scale_in_execution_sizing_plan_id": "avg-down-sizing-test",
                "scale_in_execution_sizing_valid": True,
            },
        ],
    )

    report = split_plan._build_report_from_events(target_date)

    atomic = report["input_summary"]["atomic_execution_sizing"]
    assert atomic["status"] == "pass"
    assert atomic["daily_plan_valid_count"] == 1
    assert atomic["post_contract_real_submit_with_plan_count"] == 1
    assert atomic["post_contract_real_submit_missing_plan_count"] == 0


def test_postclose_report_does_not_skip_atomic_avg_down_block_without_submit(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-09-15"
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "scale_in_execution_sizing_plan_block",
                "emitted_at": f"{target_date}T10:00:00+09:00",
                "stock_code": "005930",
                "record_id": 1,
                "strategy": "SCALPING",
                "add_type": "AVG_DOWN",
                "scale_in_execution_sizing_plan_id": "avg-down-sizing-invalid",
                "scale_in_execution_sizing_valid": False,
                "scale_in_execution_sizing_blockers": ["quantity_increase_detected"],
                "actual_order_submitted": False,
            }
        ],
    )

    report = split_plan._build_report_from_events(target_date)

    atomic = report["input_summary"]["atomic_execution_sizing"]
    assert atomic["status"] == "fail"
    assert atomic["daily_plan_invalid_count"] == 1
    assert atomic["selection_blocked"] is True


def _valid_runtime_refresh_evidence():
    return {
        "economic_gate_version": "filled_incumbent_bbo_holdout_v4",
        "paired_economic_sample_count": 3,
        "economic_source_dates": ["2026-07-06", "2026-07-07"],
        "economic_source_date_count": 2,
        "runtime_policy_refresh_allowed": True,
        "eligible_runtime_bucket_count": 1,
        "real_outcome_joined_sample": 3,
        "additional_mfe_mae_joined_sample": 3,
        "price_join_coverage": 1.0,
        "source_quality_adjusted_ev_pct": 0.10,
        "modeled_fill_participation": 1.0,
        "downside_p10_profit_rate": 0.05,
        "blockers": [],
        "holdout_evidence": [{"runtime_apply_allowed": True, "runtime_apply_blockers": [], "blockers": [],
            "paired_economic_sample_count": 3, "economic_source_dates": ["2026-07-06", "2026-07-07"],
            "holdout_dates": ["2026-07-06", "2026-07-07"], "calibration_dates": ["2026-07-02", "2026-07-03"],
            "source_quality_adjusted_ev_pct": 0.10, "average_daily_delta_net_pnl_krw": 10,
            "price_join_coverage": 1.0, "modeled_fill_participation": 1.0, "downside_p10_profit_rate": 0.05}],
    }


def _economic_attempt_events(
    *,
    target_date: str,
    idx: int,
    min_price: int = 9970,
    sell_price: int = 10050,
    requested_qty: int = 2,
):
    minute = (idx % 10) * 5
    code = f"{idx:06d}"
    record_id = idx
    order_no = f"BUY{idx}"
    events = [
        {
            "stage": "scale_in_order_submitted",
            "emitted_at": f"{target_date}T09:{minute:02d}:00+09:00",
            "stock_code": code,
            "record_id": record_id,
            "strategy": "SCALPING",
            "add_type": "AVG_DOWN",
            "add_trigger": "late_loss_avg_down_retry",
            "actual_order_submitted": True,
            "submitted_qty": requested_qty,
            "submitted_leg_count": 1,
            "ord_no": order_no,
            "resolved_price": 10000,
            "order_type": "00",
        },
        {
            "stage": "scale_in_executed",
            "emitted_at": f"{target_date}T09:{minute:02d}:01+09:00",
            "stock_code": code,
            "record_id": record_id,
            "add_type": "AVG_DOWN",
            "actual_order_submitted": True,
            "order_no": order_no,
            "execution_no": f"EXEC{idx}",
            "fill_price": 10000,
            "fill_qty": requested_qty,
            "receipt_economics_complete": True,
            "receipt_quantity_contract_complete": True,
            "receipt_unit_fill_consistent": True,
            "broker_execution_provenance_complete": True,
        },
        {
            "stage": "stat_action_decision_snapshot",
            "emitted_at": f"{target_date}T09:{minute:02d}:05+09:00",
            "stock_code": code,
            "record_id": record_id,
            "curr_price": min_price,
        },
        {
            "stage": "stat_action_decision_snapshot",
            "emitted_at": f"{target_date}T09:{minute:02d}:30+09:00",
            "stock_code": code,
            "record_id": record_id,
            "curr_price": 10000,
        },
        {
            "stage": "sell_completed",
            "emitted_at": f"{target_date}T09:{minute + 4:02d}:00+09:00",
            "stock_code": code,
            "record_id": record_id,
            "sell_price": sell_price,
            "order_no": f"SELL{idx}",
            "actual_order_submitted": True,
            "sell_execution_receipt_economics_complete": True,
            "sell_execution_receipt_quantity_contract_complete": True,
            "sell_execution_receipt_unit_fill_consistent": True,
            "broker_execution_provenance_complete": True,
        },
    ]
    for sequence, event in enumerate(events):
        event["broker_route"] = "KRX"
        if "curr_price" in event:
            stamp = datetime.fromisoformat(event["emitted_at"]).timestamp()
            event.update(market_data_effective_best_ask=event["curr_price"], market_data_effective_best_ask_qty=requested_qty,
                         market_data_effective_best_ask_qty_source_valid=True, market_data_effective_quote_reference_epoch=stamp,
                         scale_in_quote_source_receipt={"source_type": "0D", "item": code, "observed_epoch": stamp,
                                                        "transport_epoch": 1, "route_sequence": sequence})
        if event["stage"] == "sell_completed":
            event.update(sell_qty=requested_qty, profit_rate=0.1)
    return events


def _seed_prior_economic_report(data_dir, **kwargs):
    day = "2026-07-06"
    _write_source_quality_pass(data_dir, day)
    _write_pipeline_events(
        data_dir, day, _economic_attempt_events(target_date=day, idx=4, **kwargs)
    )
    split_plan.write_outputs(day, split_plan._build_report_from_events(day))


def _seed_independent_economic_reports(data_dir, **kwargs):
    for day, indices in [("2026-07-02", (4, 5, 6)), ("2026-07-03", (7, 8, 9)), ("2026-07-06", (10, 11, 12))]:
        _write_source_quality_pass(data_dir, day)
        events = [event for idx in indices for event in _economic_attempt_events(target_date=day, idx=idx, **kwargs)]
        _write_pipeline_events(data_dir, day, events)
        split_plan.write_outputs(day, split_plan._build_report_from_events(day))

def test_allocator_preserves_avg_down_qty_and_offsets(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "test-scale-in-split",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
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
                    "runtime_apply_allowed": False,
                },
                "buckets": {
                    "scalping:late_loss_retry:normal": {
                        "context_bucket": "scalping:late_loss_retry:normal",
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weights": [0.7, 0.3],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                        "policy_mode": "counterfactual_tick_band_selector",
                        "split_variant_id": (
                            "scale_in_counterfactual_70_30_offset_0pct_0_3pct"
                        ),
                        "runtime_apply_allowed": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file)
    )

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


def test_allocator_accepts_policy_across_krx_holiday_weekend(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path("2026-07-16")
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "scale-in-holiday-handoff",
                "generated_at": "2026-07-16T20:28:37+09:00",
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
                "default_bucket": {
                    "leg_count": 2,
                    "price_offsets_pct": [0.0, 0.3],
                    "qty_weights": [0.5, 0.5],
                    "qty_weight_min": 0.5,
                    "qty_weight_max": 0.5,
                    "policy_mode": "bounded_equal_scale_in_split_baseline",
                    "split_variant_id": "scale_in_equal_50_50_offset_0pct_0_3pct",
                    "runtime_apply_allowed": False,
                },
                "buckets": {
                    "unknown_strategy:generic_avg_down:normal": {
                        "context_bucket": "unknown_strategy:generic_avg_down:normal",
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weights": [0.5, 0.5],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                        "policy_mode": "bounded_equal_scale_in_split_baseline",
                        "split_variant_id": "scale_in_equal_50_50_offset_0pct_0_3pct",
                        "runtime_apply_allowed": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file)
    )

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 10, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        action={"add_type": "AVG_DOWN"},
        now=datetime(2026, 7, 20, 8, 30, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["scale_in_split_order_policy_applied"] is True
    assert fields["scale_in_split_order_skip_reason"] == ""
    assert [order["qty"] for order in orders] == [5, 5]


def test_allocator_rejects_policy_after_three_krx_trading_days(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path("2026-07-13")
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "scale-in-stale-trading-days",
                "generated_at": "2026-07-13T20:28:37+09:00",
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
                "default_bucket": {"runtime_apply_allowed": False},
                "buckets": {
                    "unknown_strategy:generic_avg_down:normal": {
                        "context_bucket": "unknown_strategy:generic_avg_down:normal",
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weights": [0.5, 0.5],
                        "policy_mode": "bounded_equal_scale_in_split_baseline",
                        "split_variant_id": ("scale_in_equal_50_50_offset_0pct_0_3pct"),
                        "runtime_apply_allowed": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file)
    )

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 10, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        action={"add_type": "AVG_DOWN"},
        now=datetime(2026, 7, 20, 8, 30, tzinfo=timezone(timedelta(hours=9))),
    )

    assert orders == [
        {"qty": 10, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"}
    ]
    assert fields["scale_in_split_order_policy_applied"] is False
    assert fields["scale_in_split_order_skip_reason"] == "stale_policy"


def test_allocator_skips_qty_one_pyramid_and_removed_market_split(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "test-scale-in-split-market",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
                "default_bucket": {
                    "leg_count": 2,
                    "price_offsets_ticks": [0, 1],
                    "qty_weight_min": 0.5,
                    "qty_weight_max": 0.5,
                    "policy_mode": "bounded_equal_scale_in_split_baseline",
                    "split_variant_id": "scale_in_equal_50_50_offset_0pct_0_3pct",
                    "runtime_apply_allowed": False,
                },
                "buckets": {
                    "unknown_strategy:generic_avg_down:normal": {
                        "context_bucket": "unknown_strategy:generic_avg_down:normal",
                        "leg_count": 2,
                        "price_offsets_ticks": "market",
                        "price_offsets_pct": "market",
                        "qty_weights": [0.5, 0.5],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                        "policy_mode": "market_qty_split_only",
                        "split_variant_id": "scale_in_market_qty_split_50_50",
                        "runtime_apply_allowed": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file)
    )

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
    assert market_fields["scale_in_split_order_policy_applied"] is False
    assert len(market_orders) == 1
    assert sum(order["qty"] for order in market_orders) == 4
    assert {order["price"] for order in market_orders} == {0}
    assert best_limit_fields["scale_in_split_order_policy_applied"] is False
    assert len(best_limit_orders) == 1
    assert sum(order["qty"] for order in best_limit_orders) == 4
    assert {order["price"] for order in best_limit_orders} == {0}


def test_allocator_rejects_diagnostic_three_leg_avg_down_policy(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "test-scale-in-split-three-leg",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
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
                        "runtime_apply_allowed": True,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file)
    )

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 8, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        stock={"strategy": "SCALPING"},
        action={"add_type": "AVG_DOWN", "reason": "late_loss_avg_down_retry"},
        price_resolution={"order_price": 10000, "best_bid": 10000},
    )

    assert fields["scale_in_split_order_policy_applied"] is False
    assert (
        fields["scale_in_split_order_skip_reason"]
        == "context_bucket_policy_mode_invalid"
    )
    assert [item["qty"] for item in orders] == [8]
    assert [item["price"] for item in orders] == [10000]
    assert sum(item["qty"] for item in orders) == 8


def test_allocator_fails_closed_when_policy_bucket_missing(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    _patch_dirs(monkeypatch, tmp_path)
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "scale_in_split_order_plan:test",
                "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
                "default_bucket": {
                    "context_bucket": "default",
                    "leg_count": 2,
                    "runtime_apply_allowed": True,
                },
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE", str(policy_file)
    )

    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 2, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        stock={"strategy": "SCALPING"},
        action={"add_type": "AVG_DOWN", "reason": "unmapped_avg_down_reason"},
        price_resolution={"order_price": 10000},
    )

    assert fields["scale_in_split_order_policy_applied"] is False
    assert fields["scale_in_split_order_skip_reason"] == (
        "default_context_runtime_apply_forbidden"
    )
    assert orders == [
        {"qty": 2, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"}
    ]


def test_runtime_loader_rejects_legacy_policy_without_refresh_evidence(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "legacy-scale-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "legacy-without-evidence",
                "runtime_apply_allowed": True,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")

    policy, reason = split_plan._load_policy_from_env(str(policy_file))

    assert policy is None
    assert reason == "runtime_refresh_evidence_missing"


def test_runtime_loader_rejects_env_policy_version_mismatch(monkeypatch, tmp_path):
    policy_file = tmp_path / "scale.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_policy_v4",
                "policy_version": "artifact-version",
                "runtime_apply_allowed": True,
                "runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION", "manifest-version"
    )

    policy, status = split_plan._load_policy_from_env(str(policy_file))

    assert policy is None
    assert status == "policy_version_mismatch"


def test_runtime_bucket_contract_rejects_unbounded_offset():
    status = split_plan._bucket_runtime_contract_error(
        {
            "runtime_apply_allowed": True,
            "policy_mode": split_plan.POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
            "split_variant_id": split_plan.COUNTERFACTUAL_50_50_VARIANT_ID,
            "leg_count": 2,
            "qty_weights": [0.5, 0.5],
            "price_offsets_pct": [0.0, 9.0],
            "price_offsets_ticks": [0, 1],
        }
    )

    assert status == "context_bucket_price_offsets_invalid"






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

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["price_offsets_ticks"] == [0, 1]
    assert candidate["price_offsets_pct"] == [0.0, 0.3]
    assert candidate["qty_weights"] == [0.7, 0.3]
    assert candidate["policy_mode"] == "counterfactual_tick_band_selector"
    assert candidate["post_submit_touch_rates"]["touch_1tick_rate"] == 1.0
    assert candidate["post_submit_touch_rates"]["touch_2tick_rate"] == 0.0
    assert candidate["post_submit_touch_rates"]["touch_0_5pct_rate"] == 0.0


def test_report_selects_70_30_when_touch_low_or_missed_upside_high(
    monkeypatch, tmp_path
):
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

    report = split_plan._build_report_from_events(target_date)
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

    report = split_plan._build_report_from_events(target_date)

    assert report["source_quality"]["tuning_input_allowed"] is True
    assert report["source_quality"]["raw_row_exclusion_applied"] is True
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    evidence = report["recommended_policy"]["runtime_refresh_evidence"]
    assert evidence["runtime_policy_refresh_allowed"] is False
    assert "real_outcome_sample_floor" in evidence["blockers"]
    assert "additional_mfe_mae_sample_floor" in evidence["blockers"]


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

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]
    diagnostic = report["recommended_policy"]["diagnostic_candidates"][0]

    assert candidate["price_offsets_ticks"] == [0, 2]
    assert candidate["price_offsets_pct"] == [0.0, 0.8]
    assert candidate["qty_weights"] == [0.6, 0.4]
    assert candidate["selection_reason"] == "touch_0_8pct_high_with_low_missed_upside"
    assert diagnostic["price_offsets_ticks"] == [0, 1, 2]
    assert diagnostic["price_offsets_pct"] == [0.0, 0.3, 0.8]
    assert diagnostic["runtime_apply_allowed"] is False


def test_report_keeps_three_leg_diagnostic_without_exact_economic_outcomes(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    events = []
    for idx in range(20):
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
                    "record_id": idx + 1,
                    "curr_price": 9980,
                },
            ]
        )
    _write_pipeline_events(data_dir, target_date, events)

    report = split_plan._build_report_from_events(target_date)

    assert report["input_summary"]["runtime_three_leg_candidate_count"] == 0
    assert report["input_summary"]["diagnostic_three_leg_candidate_count"] == 1
    assert len(report["recommended_policy"]["candidates"]) == 1
    candidate = report["recommended_policy"]["candidates"][0]
    assert candidate["leg_count"] == 2
    assert candidate["runtime_apply_allowed"] is False
    assert report["policy_artifact"]["buckets"] == {}


def test_report_builds_reachable_exact_economic_gate(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _seed_independent_economic_reports(data_dir)
    _write_source_quality_pass(data_dir, target_date)
    events = []
    for idx in range(1, 4):
        events.extend(_economic_attempt_events(target_date=target_date, idx=idx))
    _write_pipeline_events(data_dir, target_date, events)

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]
    evidence = report["recommended_policy"]["runtime_refresh_evidence"]

    assert report["input_summary"]["daily_unique_attempt_count"] == 3
    assert report["input_summary"]["rolling_eligible_runtime_attempt_count"] == 12
    assert candidate["real_outcome_joined_sample"] == 6
    assert candidate["additional_mfe_mae_joined_sample"] == 6
    assert candidate["source_quality_adjusted_ev_pct"] > 0
    assert candidate["modeled_fill_participation"] == 1.0
    assert candidate["runtime_apply_allowed"] is True
    assert evidence["runtime_policy_refresh_allowed"] is True
    assert split_plan.runtime_refresh_contract_error(evidence) == ""
    assert report["recommended_policy"]["runtime_apply_allowed"] is True
    assert len(report["policy_artifact"]["buckets"]) == 1
    split_plan.write_outputs(target_date, report)
    monkeypatch.setenv("KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION",
        report["policy_artifact"]["policy_version"],
    )
    orders, fields = split_plan.apply_scale_in_split_order_policy(
        {"qty": 2, "price": 10000, "order_type_code": "00", "add_type": "AVG_DOWN"},
        stock={"strategy": "SCALPING"},
        action={"add_type": "AVG_DOWN", "add_trigger": "late_loss_avg_down_retry"},
        policy_file=str(split_plan.policy_path(target_date)),
    )
    assert fields["scale_in_split_order_policy_applied"] is True
    assert [order["qty"] for order in orders] == [1, 1]
    assert [order["price"] for order in orders] == [10000, 9970]


def test_report_selects_best_existing_two_leg_variant_by_cost_adjusted_ev(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _seed_independent_economic_reports(data_dir, requested_qty=10)
    _write_source_quality_pass(data_dir, target_date)
    events = []
    for idx in range(1, 4):
        events.extend(
            _economic_attempt_events(
                target_date=target_date,
                idx=idx,
                requested_qty=10,
            )
        )
    _write_pipeline_events(data_dir, target_date, events)

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["heuristic_selection_reason"] == (
        "touch_0_3pct_low_or_missed_upside_high"
    )
    assert candidate["split_variant_id"] == (split_plan.COUNTERFACTUAL_50_50_VARIANT_ID)
    assert candidate["selection_reason"] == (
        f"economic_grid_best:{split_plan.COUNTERFACTUAL_50_50_VARIANT_ID}"
    )
    assert len(candidate["evaluated_variant_economics"]) == 3


def test_three_leg_remains_diagnostic_even_with_strong_evidence():
    result = split_plan._three_leg_candidate(
        "scalping:late_loss_retry:normal",
        {
            "post_submit_observed_sample": 100,
            "eligible_runtime_attempt_count": 100,
            "touch_1tick_rate": 1.0,
            "touch_2tick_rate": 1.0,
            "rolling_anchor_results": _paired_anchors(),
        },
    )
    assert result["diagnostic_only"] is True
    assert result["runtime_apply_allowed"] is False
    assert "three_leg_diagnostic_only" in result["runtime_apply_blockers"]


def test_counterfactual_price_path_excludes_pre_anchor_and_next_attempt_prices():
    target_date = "2026-07-07"
    events = _economic_attempt_events(target_date=target_date, idx=1)
    anchor = events[0]
    events.extend(
        [
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": f"{target_date}T09:04:55+09:00",
                "stock_code": "000001",
                "record_id": 1,
                "curr_price": 9000,
            },
            {
                "stage": "scale_in_order_submitted",
                "emitted_at": f"{target_date}T09:05:40+09:00",
                "stock_code": "000001",
                "record_id": 1,
                "strategy": "SCALPING",
                "add_type": "AVG_DOWN",
                "actual_order_submitted": True,
                "submitted_qty": 2,
                "ord_no": "BUY-NEXT",
                "resolved_price": 10000,
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": f"{target_date}T09:05:50+09:00",
                "stock_code": "000001",
                "record_id": 1,
                "curr_price": 9100,
            },
        ]
    )

    result = split_plan._counterfactual_for_anchor(
        anchor,
        events=events,
        observations_by_code=split_plan._build_post_submit_observations(events),
    )

    assert result["min_observed_price"] == 9970
    assert result["additional_mae_pct"] == -0.3


def test_unique_attempts_merge_overlapping_leg_receipts_but_keep_new_order():
    common = {
        "stock_code": "123456",
        "record_id": 10,
        "add_type": "AVG_DOWN",
        "actual_order_submitted": True,
    }
    rows = [
        {
            **common,
            "stage": "scale_in_order_submitted",
            "emitted_at": "2026-07-07T09:00:02+09:00",
            "ord_no": "A,B",
        },
        {
            **common,
            "stage": "late_loss_avg_down_retry_submitted",
            "emitted_at": "2026-07-07T09:00:00+09:00",
            "ord_no": "A",
        },
        {
            **common,
            "stage": "scale_in_executed",
            "emitted_at": "2026-07-07T09:00:01+09:00",
            "order_no": "B",
        },
        {
            **common,
            "stage": "scale_in_order_submitted",
            "emitted_at": "2026-07-07T09:01:00+09:00",
            "ord_no": "C",
        },
    ]

    anchors = split_plan._unique_attempt_anchors(rows)

    assert len(anchors) == 2
    assert [split_plan._order_numbers(item) for item in anchors] == [
        {"A", "B"},
        {"C"},
    ]


def test_report_blocks_negative_cost_adjusted_split_economics(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    events = []
    for idx in range(1, 4):
        events.extend(
            _economic_attempt_events(
                target_date=target_date,
                idx=idx,
                min_price=10000,
                sell_price=10100,
            )
        )
    _write_pipeline_events(data_dir, target_date, events)

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    economic = split_plan._evaluate_candidate_economics(report["daily_attempt_outcomes"], candidate)
    assert economic["source_quality_adjusted_ev_pct"] < 0
    assert "cost_adjusted_ev_not_positive" in economic["runtime_apply_blockers"]
    assert "modeled_fill_participation_floor" in economic["runtime_apply_blockers"]
    assert candidate["runtime_apply_allowed"] is False
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    assert report["policy_artifact"]["buckets"] == {}


def test_report_rolls_unique_attempt_outcomes_across_dates(monkeypatch, tmp_path):
    first_date = "2026-07-07"
    target_date = "2026-07-08"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, first_date)
    _write_pipeline_events(
        data_dir,
        first_date,
        [
            event
            for idx in range(1, 3)
            for event in _economic_attempt_events(target_date=first_date, idx=idx)
        ],
    )
    split_plan.write_outputs(first_date, split_plan._build_report_from_events(first_date))
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        _economic_attempt_events(target_date=target_date, idx=3),
    )

    report = split_plan._build_report_from_events(target_date)

    assert report["rolling_summary"]["historical_source_dates"] == [first_date]
    assert report["rolling_summary"]["current_unique_attempt_count"] == 1
    assert report["rolling_summary"]["rolling_unique_attempt_count"] == 3
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    assert "independent_calibration_sample_floor" in report["recommended_policy"]["candidates"][0]["holdout_evidence"]["blockers"]


def test_three_leg_candidate_stays_diagnostic_when_missed_upside_is_high():
    candidate = split_plan._three_leg_candidate(
        "scalping:late_loss_retry:normal",
        {
            "post_submit_observed_sample": 20,
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

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["policy_mode"] == "market_qty_split_only"
    assert candidate["price_offsets_ticks"] == "market"
    assert candidate["qty_weights"] == [0.5, 0.5]


def test_report_reconstructs_submitted_anchor_from_execution_without_reason(
    monkeypatch, tmp_path
):
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

    report = split_plan._build_report_from_events(target_date)
    candidates = report["recommended_policy"]["candidates"]

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["context_bucket"] == "unknown_strategy:late_loss_retry:normal"
    assert candidate["counterfactual_anchor_count"] == 1
    assert candidate["post_submit_observed_sample"] == 1
    assert candidate["price_observation_join_gap_count"] == 0
    assert candidate["base_price_reconstruction_gap_count"] == 0
    assert (
        candidate["anchor_samples"][0]["base_price_source"]
        == "reconstructed_from_scale_in_executed"
    )
    assert candidate["policy_mode"] == "counterfactual_tick_band_selector"


def test_report_falls_back_when_anchor_price_reconstruction_fails(
    monkeypatch, tmp_path
):
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

    report = split_plan._build_report_from_events(target_date)
    candidate = report["recommended_policy"]["candidates"][0]

    assert candidate["policy_mode"] == "bounded_equal_scale_in_split_baseline"
    assert (
        candidate["selection_reason"]
        == "counterfactual_sample_or_price_observation_missing"
    )
    assert report["input_summary"]["base_price_reconstruction_gap_count"] == 1


def test_report_streams_projected_events_without_retaining_large_payload(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "unrelated",
                "emitted_at": "2026-07-07T08:59:00+09:00",
                "fields": {"large_payload": "x" * 100_000},
            },
            {
                "stage": "late_loss_avg_down_retry_submitted",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "reason": "late_loss_avg_down_retry",
                "actual_order_submitted": True,
                "request_price": 10000,
                "order_type": "00",
                "fields": {"large_payload": "y" * 100_000},
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:10+09:00",
                "stock_code": "123456",
                "curr_price": 9990,
                "fields": {"large_payload": "z" * 100_000},
            },
        ],
    )

    report = split_plan._build_report_from_events(target_date)

    contract = report["input_summary"]["source_read_contract"]
    assert contract["read_mode"] == "streaming_relevant_field_projection"
    assert contract["full_source_materialized"] is False
    assert contract["source_event_count"] == 3
    assert contract["retained_event_count"] == 2
    assert "large_payload" not in json.dumps(report)


def test_report_skips_json_decode_when_no_eligible_real_avg_down_attempt(
    monkeypatch, tmp_path
):
    target_date = "2026-07-07"
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_source_quality_pass(data_dir, target_date)
    _write_pipeline_events(
        data_dir,
        target_date,
        [
            {
                "stage": "scalp_sim_scale_in_order_assumed_filled",
                "emitted_at": "2026-07-07T09:00:00+09:00",
                "stock_code": "123456",
                "add_type": "AVG_DOWN",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "qty": 10,
            },
            {
                "stage": "stat_action_decision_snapshot",
                "emitted_at": "2026-07-07T09:00:10+09:00",
                "stock_code": "123456",
                "reason": "AVG_DOWN diagnostic only",
                "fields": {"large_payload": "z" * 100_000},
            },
        ],
    )

    report = split_plan._build_report_from_events(target_date)

    contract = report["input_summary"]["source_read_contract"]
    assert contract["read_mode"] == "avg_down_attempt_presence_precheck"
    assert contract["json_parse_skipped"] is True
    assert contract["retained_scope"] == "no_real_avg_down_attempt_anchor"
    assert report["input_summary"]["daily_unique_attempt_count"] == 0
    assert report["recommended_policy"]["runtime_apply_allowed"] is False


def test_runtime_refresh_evidence_requires_outcome_mfe_mae_and_price_coverage():
    evidence = split_plan._runtime_refresh_evidence(
        [
            {
                "paired_economic_sample_count": 3,
                "economic_source_dates": ["2026-07-06", "2026-07-07"],
                "runtime_apply_allowed": True,
                "real_outcome_joined_sample": 3,
                "additional_mfe_mae_joined_sample": 3,
                "price_observation_joined_sample": 4,
                "price_observation_join_gap_count": 1,
                "economic_delta_pnl_krw": 30,
                "economic_base_notional_krw": 30000,
                "modeled_fill_participation": 1.0,
                "downside_p10_profit_rate": 0.05,
            }
        ]
    )

    assert evidence["runtime_policy_refresh_allowed"] is True
    assert evidence["price_join_coverage"] == 0.8
    assert evidence["blockers"] == []


def test_runtime_refresh_contract_rejects_non_finite_economics():
    evidence = _valid_runtime_refresh_evidence()
    evidence["source_quality_adjusted_ev_pct"] = float("nan")

    assert split_plan.runtime_refresh_contract_error(evidence) == (
        "runtime_refresh_cost_adjusted_ev_floor"
    )


def test_runtime_refresh_contract_requires_minimum_cost_adjusted_ev():
    evidence = _valid_runtime_refresh_evidence()
    evidence["source_quality_adjusted_ev_pct"] = 0.09

    assert split_plan.runtime_refresh_contract_error(evidence) == (
        "runtime_refresh_cost_adjusted_ev_floor"
    )
    evidence["source_quality_adjusted_ev_pct"] = 0.10
    assert split_plan.runtime_refresh_contract_error(evidence) == ""


def test_policy_artifact_repeats_runtime_refresh_gate():
    blocked_evidence = split_plan._runtime_refresh_evidence([])
    blocked = split_plan._build_policy(
        "2026-08-04", [], refresh_evidence=blocked_evidence
    )
    ready_evidence = split_plan._runtime_refresh_evidence(
        [
            {
                "paired_economic_sample_count": 3,
                "economic_source_dates": ["2026-07-06", "2026-07-07"],
                "context_bucket": "scalping:late_loss_retry:normal",
                "runtime_apply_allowed": True,
                "holdout_evidence": _valid_runtime_refresh_evidence()["holdout_evidence"][0],
                "real_outcome_joined_sample": 3,
                "additional_mfe_mae_joined_sample": 3,
                "price_observation_joined_sample": 4,
                "price_observation_join_gap_count": 0,
                "economic_delta_pnl_krw": 30,
                "economic_base_notional_krw": 30000,
                "modeled_fill_participation": 1.0,
                "downside_p10_profit_rate": 0.05,
            }
        ]
    )
    ready = split_plan._build_policy(
        "2026-08-04",
        [
            {
                "context_bucket": "scalping:late_loss_retry:normal",
                "runtime_apply_allowed": True,
                "holdout_evidence": _valid_runtime_refresh_evidence()["holdout_evidence"][0],
            }
        ],
        refresh_evidence=ready_evidence,
    )

    assert blocked["runtime_apply_allowed"] is False
    assert blocked["default_bucket"]["runtime_apply_allowed"] is False
    assert (
        blocked["runtime_refresh_evidence"]["insufficient_evidence_action"]
        == "block_refresh_until_validated_prior_policy_available"
    )
    assert ready["runtime_apply_allowed"] is True
    assert ready["default_bucket"]["runtime_apply_allowed"] is False
    assert "scalping:late_loss_retry:normal" in ready["buckets"]


def test_generated_policy_contract_detects_content_change():
    candidate = {
        "context_bucket": "scalping:late_loss_retry:normal",
        "runtime_apply_allowed": True,
        "policy_mode": split_plan.POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
        "split_variant_id": split_plan.COUNTERFACTUAL_50_50_VARIANT_ID,
        "leg_count": 2,
        "qty_weights": [0.5, 0.5],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "price_offsets_pct": [0.0, 0.3],
        "price_offsets_ticks": [0, 1],
    }
    policy = split_plan._build_policy(
        "2026-08-04",
        [candidate],
        refresh_evidence=_valid_runtime_refresh_evidence(),
    )

    assert split_plan.policy_runtime_contract_error(policy) == ""
    policy["buckets"]["scalping:late_loss_retry:normal"]["selection_reason"] = (
        "tampered"
    )
    assert split_plan.policy_runtime_contract_error(policy) == (
        "policy_content_hash_mismatch"
    )


def test_current_scale_in_policy_requires_atomic_execution_sizing_contract():
    candidate = {
        "context_bucket": "scalping:late_loss_retry:normal",
        "runtime_apply_allowed": True,
        "policy_mode": split_plan.POLICY_MODE_COUNTERFACTUAL_TICK_BAND,
        "split_variant_id": split_plan.COUNTERFACTUAL_50_50_VARIANT_ID,
        "leg_count": 2,
        "qty_weights": [0.5, 0.5],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "price_offsets_pct": [0.0, 0.3],
        "price_offsets_ticks": [0, 1],
    }
    policy = split_plan._build_policy(
        "2026-09-16",
        [candidate],
        refresh_evidence=_valid_runtime_refresh_evidence(),
    )
    policy.pop("scale_in_execution_sizing_plan_schema")

    assert split_plan.policy_runtime_contract_error(policy) == (
        "scale_in_atomic_execution_sizing_schema_invalid"
    )

    policy = split_plan._build_policy(
        "2026-09-16",
        [candidate],
        refresh_evidence=_valid_runtime_refresh_evidence(),
    )
    policy.pop("scale_in_price_plan_schema")
    assert split_plan.policy_runtime_contract_error(policy) == (
        "scale_in_atomic_price_plan_schema_invalid"
    )

    policy = split_plan._build_policy(
        "2026-09-15",
        [candidate],
        refresh_evidence=_valid_runtime_refresh_evidence(),
    )
    policy.pop("scale_in_price_plan_schema")
    assert split_plan.policy_runtime_contract_error(policy) == ""


def _anchor_from_events(events):
    events = deepcopy(events)
    for sequence, event in enumerate(events):
        if "curr_price" in event and "market_data_effective_best_ask" in event:
            stamp = datetime.fromisoformat(event["emitted_at"]).timestamp()
            event["market_data_effective_best_ask"] = event["curr_price"]
            event["market_data_effective_quote_reference_epoch"] = stamp
            event["scale_in_quote_source_receipt"].update(observed_epoch=stamp, route_sequence=sequence)
    events = sorted(events, key=split_plan._event_time)
    anchor = next(
        item for item in events if item["stage"] == "scale_in_order_submitted"
    )
    return split_plan._counterfactual_for_anchor(
        anchor,
        events=events,
        observations_by_code={split_plan._stock_code(anchor): events},
    )


def _paired_anchors():
    return [
        _anchor_from_events(_economic_attempt_events(target_date=day, idx=idx))
        for idx, day in enumerate(["2026-07-06", "2026-07-07", "2026-07-07"], 1)
    ]


def _equal_variant():
    return split_plan._selected_policy_from_counterfactual({})


def test_terminal_sell_joins_lifecycle_not_buy_order_number():
    events = _economic_attempt_events(target_date="2026-07-07", idx=1)
    assert events[0]["ord_no"] != events[-1]["order_no"]
    assert _anchor_from_events(events)["real_outcome_joined"] is True
    events[-1]["record_id"] = 99
    assert _anchor_from_events(events)["real_outcome_joined"] is False


@pytest.mark.parametrize(
    "touch_seconds,expected_fill", [(5, 1.0), (19, 1.0), (20, 0.5), (170, 0.5)]
)
def test_replay_uses_leg_ttl_not_180_second_minimum(touch_seconds, expected_fill):
    events = _economic_attempt_events(target_date="2026-07-07", idx=1, min_price=10000)
    touch = deepcopy(events[2])
    touch["curr_price"] = 9970
    touch["emitted_at"] = (
        split_plan._event_time(events[0]) + timedelta(seconds=touch_seconds)
    ).isoformat()
    if touch_seconds == 5:
        events[2] = touch
    else:
        events.append(touch)
    anchor = _anchor_from_events(events)
    replay = split_plan._replay_execution(anchor, _equal_variant())
    assert replay["fill_participation"] == expected_fill


def test_unresolved_short_path_is_missing_not_zero_pnl():
    events = _economic_attempt_events(target_date="2026-07-07", idx=1, min_price=10000)
    events.pop(3)  # No observation at or after the second-leg TTL.
    anchor = _anchor_from_events(events)
    assert split_plan._replay_execution(anchor, _equal_variant()) is None


def test_own_fill_is_not_a_price_path_or_fixed_control():
    events = _economic_attempt_events(target_date="2026-07-07", idx=1)
    events = [
        item for item in events if item["stage"] != "stat_action_decision_snapshot"
    ]
    anchor = _anchor_from_events(events)
    assert anchor["real_outcome_joined"] is True
    assert anchor["additional_mfe_mae_joined"] is False
    events = _economic_attempt_events(target_date="2026-07-07", idx=1)
    events[0].pop("resolved_price")
    anchor = _anchor_from_events(events)
    assert anchor["fixed_control_price_complete"] is False
    assert split_plan._replay_execution(anchor, _equal_variant()) is None


def test_economic_floor_counts_paired_intersection_not_marginal_counts():
    anchors = _paired_anchors()
    extra = deepcopy(anchors[-1])
    extra["attempt_id"] += ":extra"
    anchors.append(extra)
    anchors[0]["additional_mfe_mae_joined"] = False
    anchors[3]["real_outcome_joined"] = False
    result = split_plan._evaluate_candidate_economics(anchors, _equal_variant())
    assert result["real_outcome_joined_sample"] == 3
    assert result["additional_mfe_mae_joined_sample"] == 3
    assert result["paired_economic_sample_count"] == 2
    assert "paired_economic_sample_floor" in result["runtime_apply_blockers"]
    assert result["runtime_apply_allowed"] is False


def test_economic_promotion_needs_two_dates_not_daily_only():
    anchors = _paired_anchors()
    assert (
        split_plan._evaluate_candidate_economics(anchors, _equal_variant())[
            "runtime_apply_allowed"
        ]
        is True
    )
    for item in anchors:
        item["source_date"] = "2026-07-07"
    result = split_plan._evaluate_candidate_economics(anchors, _equal_variant())
    assert result["paired_economic_sample_count"] == 3
    assert result["runtime_apply_blockers"] == ["economic_source_date_floor"]


def test_current_incumbent_self_comparison_preserves_policy_and_records_versioned_r6():
    anchors = _paired_anchors()
    before = split_plan._evaluate_candidate_economics(anchors, _equal_variant())
    for item in anchors:
        item.update(
            actual_split_applied=True,
            incumbent_policy=_equal_variant(),
            actual_fill_price=9985,
            applied_policy_version="split:v3:test",
            applied_variant_id=split_plan.BASELINE_SPLIT_VARIANT_ID,
        )
    after = split_plan._evaluate_candidate_economics(anchors, _equal_variant())
    assert before["source_quality_adjusted_ev_pct"] > 0
    assert after["source_quality_adjusted_ev_pct"] == 0
    assert after["runtime_apply_allowed"] is False
    attribution = split_plan._post_apply_attribution(anchors)
    result = attribution["policy_versions"][0]
    assert result["policy_version"] == "split:v3:test"
    assert result["paired_full_fill_sample_count"] == 3
    assert result["source_quality_adjusted_ev_pct"] > 0
    assert result["negative_economic_evidence"] is False
    assert result["cancel_rate_delta"] is None
    for item in anchors:
        item["actual_fill_price"] = 10020
    assert (
        split_plan._post_apply_attribution(anchors)["policy_versions"][0][
            "negative_economic_evidence"
        ]
        is True
    )




@pytest.mark.parametrize("flag", [False, "false", 0, None])
def test_false_rising_missed_flag_does_not_change_context_bucket(flag):
    row = {
        "strategy": "SCALPING",
        "add_type": "AVG_DOWN",
        "fields": {"rising_missed_scout": flag},
    }
    assert "rising_missed" not in split_plan._context_bucket(row)
    row["fields"]["rising_missed_scout"] = True
    assert "rising_missed" in split_plan._context_bucket(row)


@pytest.mark.parametrize(
    "corruption",
    ["overfill", "missing_execution_no", "conflicting_receipt", "stale_path"],
)
def test_corrupt_receipt_or_stale_path_cannot_be_paired(corruption):
    events = _economic_attempt_events(target_date="2026-07-07", idx=1)
    if corruption == "overfill":
        events[1]["fill_qty"] = 3
    elif corruption == "missing_execution_no":
        events[1].pop("execution_no")
    elif corruption == "conflicting_receipt":
        events.append({**events[1], "fill_price": 9990})
    else:
        for item in events:
            if item["stage"] == "stat_action_decision_snapshot":
                item["quote_stale"] = True
    anchor = _anchor_from_events(events)
    result = split_plan._evaluate_candidate_economics([anchor], _equal_variant())
    assert result["paired_economic_sample_count"] == 0


def test_policy_v2_economics_and_single_date_are_not_runtime_authority():
    evidence = _valid_runtime_refresh_evidence()
    evidence["economic_gate_version"] = "cost_adjusted_split_delta_v1"
    assert (
        split_plan.runtime_refresh_contract_error(evidence)
        == "runtime_refresh_economic_gate_version_mismatch"
    )
    evidence = _valid_runtime_refresh_evidence()
    evidence["economic_source_dates"] = ["2026-07-07"]
    evidence["economic_source_date_count"] = 1
    assert (
        split_plan.runtime_refresh_contract_error(evidence)
        == "runtime_refresh_source_date_floor"
    )


def test_partial_submit_and_conflicting_terminal_do_not_promote():
    events = _economic_attempt_events(target_date="2026-07-07", idx=1)
    events[0].update(
        scale_in_split_order_original_qty=4,
        submitted_qty=2,
        partial_submit_failure="second_leg_failed",
    )
    result = _anchor_from_events(events)
    assert result["requested_qty"] == 4
    assert result["real_outcome_joined"] is False
    assert result["fixed_control_price_complete"] is False
    events = _economic_attempt_events(target_date="2026-07-07", idx=1)
    events.append({**events[-1], "sell_price": 9000})
    assert _anchor_from_events(events)["real_outcome_joined"] is False


def test_partial_execution_r6_is_not_pooled_with_full_fill_ev():
    anchors = _paired_anchors()
    for item in anchors:
        item.update(
            actual_split_applied=True,
            applied_policy_version="test-v3",
            applied_variant_id=split_plan.BASELINE_SPLIT_VARIANT_ID,
        )
    anchors[0].update(
        actual_fill_class="partial_or_unfilled",
        real_outcome_joined=False,
        actual_fill_qty=1,
    )
    result = split_plan._post_apply_attribution(anchors)["policy_versions"][0]
    assert result["paired_full_fill_sample_count"] == 2
    assert result["partial_or_unfilled_attempt_count"] == 1
    assert result["negative_economic_evidence"] is False




def test_runtime_ttl_decorator_and_submission_provenance_contract():
    source = Path("src/engine/sniper_state_handlers.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    decorator = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_decorate_scale_in_split_leg_ttls"
    )
    namespace = {
        "scale_in_leg_ttl_seconds": split_plan.scale_in_leg_ttl_seconds,
        "_rule_int": lambda *args: 30,
    }
    exec(
        compile(ast.Module(body=[decorator], type_ignores=[]), "ttl_test", "exec"),
        namespace,
    )
    result = namespace[decorator.name]([{"qty": 1}, {"qty": 1}], {}, "SCALPING")
    assert [row["split_leg_ttl_sec"] for row in result] == [10, 20]
    assert [row["split_bundle_hard_ttl_sec"] for row in result] == [20, 20]
    summary = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_log_holding_pipeline"
        and len(node.args) >= 3
        and isinstance(node.args[2], ast.Constant)
        and node.args[2].value == "scale_in_order_submitted"
    )
    assert any(
        keyword.arg is None
        and isinstance(keyword.value, ast.Name)
        and keyword.value.id == "scale_in_split_fields"
        for keyword in summary.keywords
    )
    assert {"final_price", "order_type_code", "partial_submit_failure"} <= {
        keyword.arg for keyword in summary.keywords
    }


def test_daily_partition_cannot_supply_another_source_date(monkeypatch, tmp_path):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-07-07"
    _write_source_quality_pass(data_dir, day)
    events = _economic_attempt_events(target_date=day, idx=1)
    events.extend(_economic_attempt_events(target_date="2026-07-06", idx=2))
    _write_pipeline_events(data_dir, day, events)
    report = split_plan._build_report_from_events(day)
    evidence = report["recommended_policy"]["runtime_refresh_evidence"]
    assert evidence["economic_source_dates"] == []
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    assert report["input_summary"]["excluded_other_date_count"] == 5
    assert report["recommended_policy"]["runtime_apply_allowed"] is False


def test_unattributed_split_provenance_has_source_only_workorder():
    from src.engine.build_code_improvement_workorder import (
        _scale_in_split_order_plan_followup_orders,
    )

    orders = _scale_in_split_order_plan_followup_orders(
        {
            "scale_in_split_order_plan": {
                "available": True,
                "status": "pass",
                "schema_version": split_plan.SCHEMA_VERSION,
                "recommended_policy_candidate_count": 1,
                "unattributed_split_attempt_count": 1,
            }
        }
    )
    assert len(orders) == 1
    assert orders[0]["improvement_type"] == "post_apply_policy_provenance_gap"
    assert orders[0]["runtime_effect"] is False
    assert orders[0]["allowed_runtime_apply"] is False


def _write_fact_catalog(data_dir, day, events=()):
    rows = [split_plan._project_relevant_input_event(event, source_name="pipeline_events", event_date=day)
            for event in events]
    payload = {"schema_version": 1, "report_type": "strategy_position_fact_sync", "target_date": day, "status": "succeeded", "consumer_ready": True, "issues": [],
               "scale_in_execution_projection": {"contract": "scale_in_execution_projection_v1",
                                                   "target_date": day, "rows": [r for r in rows if r is not None]}}
    payload["artifact_sha256"] = split_plan._semantic_digest(payload)
    path = data_dir / "report/strategy_position_fact_sync" / f"strategy_position_fact_sync_{day}.status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return path


def _actual_inventory(day, idx=1, status="COMPLETED", qty=2):
    events = _economic_attempt_events(target_date=day, idx=idx, requested_qty=qty)
    return {"history_id": idx, "record_id": str(idx), "code": f"{idx:06d}", "order_no": f"BUY{idx}",
            "source_date": day, "fill_time": events[1]["emitted_at"], "request_qty": qty, "fill_qty": qty,
            "fill_price": 10000, "request_price": 10000, "status": status,
            "sell_time": events[-1]["emitted_at"] if status == "COMPLETED" else None,
            "sell_price": 10050 if status == "COMPLETED" else None,
            "profit_rate": 0.1 if status == "COMPLETED" else None}


@pytest.mark.parametrize("inventory,status", [([], "skipped_no_actual_fill"),
    ([_actual_inventory("2026-09-17", qty=1)], "skipped_no_applicable_fill"),
    ([_actual_inventory("2026-09-17", status="HOLDING")], "pending_filled_outcome")])
def test_public_trigger_skips_raw_and_grid_without_new_ready_fill(monkeypatch, tmp_path, inventory, status):
    data = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-09-17"
    _write_source_quality_pass(data, day)
    _write_fact_catalog(data, day)
    monkeypatch.setattr(split_plan, "_query_actual_fill_inventory", lambda _: inventory)
    def forbidden(*args, **kwargs):
        pytest.fail("no ready actual fill must not read raw or evaluate candidates")
    monkeypatch.setattr(split_plan, "_iter_input_events", forbidden)
    monkeypatch.setattr(split_plan, "_build_report_from_events", forbidden)
    report = split_plan.build_report(day)
    assert report["evaluation_state"]["status"] == status
    assert report["evaluation_state"]["modeled_ev_pct"] is None
    assert report["recommended_policy"]["runtime_apply_allowed"] is False


def test_public_trigger_invalid_catalog_is_blocked_not_zero_fill(monkeypatch, tmp_path):
    data = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-09-17"
    _write_source_quality_pass(data, day)
    path = _write_fact_catalog(data, day)
    payload = json.loads(path.read_text())
    payload["consumer_ready"] = False
    path.write_text(json.dumps(payload))
    monkeypatch.setattr(split_plan, "_query_actual_fill_inventory", lambda _: pytest.fail("invalid catalog"))
    report = split_plan.build_report(day)
    assert report["evaluation_state"]["status"] == "blocked_execution_source"
    assert report["evaluation_state"]["modeled_ev_pct"] is None


def test_public_filled_outcome_and_unchanged_revision_do_not_repeat_grid(monkeypatch, tmp_path):
    data = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-07-07"
    _seed_independent_economic_reports(data)
    _write_source_quality_pass(data, day)
    events = [e for idx in (1, 2, 3) for e in _economic_attempt_events(target_date=day, idx=idx)]
    _write_fact_catalog(data, day, events)
    monkeypatch.setattr(split_plan, "_query_actual_fill_inventory", lambda _: [_actual_inventory(day, idx) for idx in (1, 2, 3)])
    report = split_plan.build_report(day)
    assert report["evaluation_state"]["status"] == "evaluated"
    assert report["recommended_policy"]["runtime_apply_allowed"] is True
    split_plan.write_outputs(day, report)
    monkeypatch.setattr(split_plan, "_build_report_from_events", lambda *a, **k: pytest.fail("unchanged outcome replayed"))
    again = split_plan.build_report(day)
    assert again["evaluation_state"]["status"] == "skipped_unchanged_filled_outcome"
    assert again["evaluation_state"]["modeled_ev_pct"] is None
    assert again["last_valid_evaluation"]["inventory_key"] == report["evaluation_state"]["inventory_key"]
    assert len(again["outcome_revisions"]) == 6
    assert len({r["attempt_id"] for r in again["outcome_revisions"]}) == 6


def test_late_evaluation_cannot_reuse_consumed_earlier_fill_dates(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    rows = [
        {"record_id": f"{day}:{idx}", "source_date": day,
         "real_outcome_joined": True, "additional_mfe_mae_joined": True,
         "outcome_available_at": f"{day}T15:00:00+09:00"}
        for day in ("2026-07-02", "2026-07-03", "2026-07-06", "2026-07-07")
        for idx in range(2)
    ]
    split_plan.REPORT_DIR.mkdir(parents=True)
    ledger = split_plan.report_paths("2026-07-08")[0]
    ledger.write_text(json.dumps({"consumed_holdout_dates": ["2026-07-06", "2026-07-07"]}))
    _, _, partition = split_plan._partition_outcomes(rows)
    assert partition["holdout_dates"] == ["2026-07-06", "2026-07-07"]
    assert "holdout_already_consumed" in partition["blockers"]


def test_existing_fill_late_terminal_rejoins_original_date(monkeypatch, tmp_path):
    data = _patch_dirs(monkeypatch, tmp_path)
    origin, day = "2026-07-07", "2026-07-08"
    old_events = _economic_attempt_events(target_date=origin, idx=1)[:-1]
    _write_source_quality_pass(data, origin)
    _write_pipeline_events(data, origin, old_events)
    _write_fact_catalog(data, origin, old_events)
    split_plan.write_outputs(origin, split_plan._build_report_from_events(origin))
    terminal = _economic_attempt_events(target_date=day, idx=1)[-1]
    _write_source_quality_pass(data, day)
    _write_fact_catalog(data, day, [terminal])
    inventory = _actual_inventory(origin)
    inventory["sell_time"] = terminal["emitted_at"]
    monkeypatch.setattr(split_plan, "_query_actual_fill_inventory", lambda _: [inventory])
    report = split_plan.build_report(day)
    assert report["evaluation_state"]["status"] == "evaluated"
    assert len(report["daily_attempt_outcomes"]) == 1
    outcome = report["daily_attempt_outcomes"][0]
    assert outcome["source_date"] == origin
    assert outcome["real_outcome_joined"] is True
    assert outcome["outcome_available_at"].startswith(day)
    assert report["recommended_policy"]["runtime_apply_allowed"] is False


def test_missing_all_atomic_plans_is_detected_from_actual_submit(monkeypatch, tmp_path):
    data = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-09-17"
    _write_source_quality_pass(data, day)
    _write_pipeline_events(data, day, _economic_attempt_events(target_date=day, idx=1))
    report = split_plan._build_report_from_events(day)
    atomic = report["input_summary"]["atomic_execution_sizing"]
    assert atomic["post_contract_real_submit_missing_plan_count"] == 1
    assert atomic["status"] == "fail"


def test_touch_only_and_repeated_quote_cannot_manufacture_fills():
    anchor = _paired_anchors()[0]
    for sample in anchor["execution_price_samples"]:
        sample["liquidity_source_valid"] = False
    assert split_plan._replay_execution(anchor, _equal_variant()) is None
    anchor = _paired_anchors()[0]
    for sample in anchor["execution_price_samples"]:
        sample["ask_qty"] = 1
        sample["quote_sequence"] = 1
    assert split_plan._replay_execution(anchor, _equal_variant()) is None


def test_no_fill_main_generates_dated_base_order_policy_for_preopen(monkeypatch, tmp_path):
    data = _patch_dirs(monkeypatch, tmp_path)
    source, target = "2026-09-17", "2026-09-21"
    _write_source_quality_pass(data, source)
    _write_fact_catalog(data, source)
    monkeypatch.setattr(split_plan, "_query_actual_fill_inventory", lambda _: [])
    assert split_plan.main(["--date", source, "--preopen-date", target]) == 0
    handoff = split_plan.preopen_policy_handoff(source, target)
    assert handoff["available"] is True
    assert handoff["split_enabled"] is False
    assert handoff["effective_execution_policy"] == "incumbent_unsplit_base_order"
    assert handoff["new_edge_claim"] is False
    assert split_plan.preopen_policy_handoff(source, "2026-09-22")["available"] is False


def test_old_market_order_does_not_exclude_later_limit_retry(monkeypatch, tmp_path):
    data = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-09-17"
    _write_source_quality_pass(data, day)
    _write_fact_catalog(data, day)
    old = {"source_quality": {"tuning_input_allowed": True}, "daily_attempt_outcomes": [{"record_id": "1", "attempt_id": f"{day}:000001:order:OLD", "market_like_order": True}]}
    path = split_plan.report_paths(day)[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(old))
    monkeypatch.setattr(split_plan, "_query_actual_fill_inventory", lambda _: [_actual_inventory(day, status="HOLDING")])
    report = split_plan.build_report(day)
    assert report["evaluation_state"]["status"] == "pending_filled_outcome"
    assert report["evaluation_state"]["applicable_receipt_count"] == 1
    assert report["evaluation_state"]["excluded_receipt_reasons"]["market_like_from_frozen_anchor"] == 0


def test_actual_fill_inventory_keeps_main_scanner_and_excludes_other_custody(monkeypatch, tmp_path):
    from contextlib import contextmanager
    from types import SimpleNamespace
    from src.database import db_manager
    _patch_dirs(monkeypatch, tmp_path)
    day = "2026-09-17"
    pairs = []
    for idx, tag in enumerate(("SCANNER", "SCALP_BASE", "WIDGET", "EPISODE", "MANUAL"), 1):
        receipt = SimpleNamespace(id=idx, recommendation_id=idx, order_no=f"BUY{idx}",
            event_time=datetime.fromisoformat(f"{day}T10:00:00"), executed_price=10000,
            stock_code=f"{idx:06d}", request_qty=4, executed_qty=4, request_price=10000)
        position = SimpleNamespace(strategy="SCALPING", position_tag=tag, sell_time=None, status="COMPLETED" if tag == "SCANNER" else "HOLDING", sell_price=None, profit_rate=None)
        pairs.append((receipt, position))
    class Session:
        def query(self, *args): return self
        def outerjoin(self, *args): return self
        def filter(self, *args): return self
        def order_by(self, *args): return self
        def all(self): return pairs
    @contextmanager
    def session(): yield Session()
    monkeypatch.setattr(db_manager, "DBManager", lambda: SimpleNamespace(get_session=session))
    result = split_plan._query_actual_fill_inventory(day)
    assert [row["record_id"] for row in result] == ["1", "2"]
    assert result[0]["status"] == "COMPLETED"
    assert result[0]["outcome_timing_status"] == "missing_completed_terminal_clock"


def test_runtime_refresh_rejects_reversed_holdout_and_future_approval_dates():
    evidence = _valid_runtime_refresh_evidence()
    evidence["holdout_evidence"][0]["calibration_dates"] = ["2026-07-08", "2026-07-09"]
    assert split_plan.runtime_refresh_contract_error(evidence) == "runtime_refresh_holdout_chronology_invalid"
    policy = {"runtime_refresh_evidence": _valid_runtime_refresh_evidence(),
              "policy_version": "scale_in_split_order_plan:2026-07-03:untrusted"}
    assert split_plan.policy_runtime_contract_error(policy) == "runtime_refresh_holdout_after_approval_source_date"
