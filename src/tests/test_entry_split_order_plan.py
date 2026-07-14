from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from src.engine.scalping import entry_split_order_plan as split_plan
from src.engine import sniper_post_sell_feedback as post_sell_feedback
from src.engine import daily_threshold_cycle_report as daily_report
from src.engine import threshold_cycle_preopen_apply as preopen_apply


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _patch_dirs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(split_plan, "DATA_DIR", data_dir)
    monkeypatch.setattr(split_plan, "REPORT_DIR", data_dir / "report" / "entry_split_order_plan")
    monkeypatch.setattr(split_plan, "POLICY_DIR", data_dir / "threshold_cycle" / "entry_split_order_policy")
    return data_dir


def test_build_report_excludes_source_quality_hard_block_and_keeps_real_sim_split(monkeypatch, tmp_path):
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
    _write_jsonl(data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", events)
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
    urgent = next(item for item in report["candidate_grid"] if item["context_bucket"] == "urgent_tight_spread")
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
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    assert report["recommended_policy"]["candidate_count"] == 1
    assert split_plan.policy_path(target_date).exists()


def test_build_report_suppresses_policy_candidates_when_source_quality_blocked(monkeypatch, tmp_path):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    events = [
        {
            "date": target_date,
            "stage": "order_leg_sent" if idx < 20 else "scalp_sim_buy_order_assumed_filled",
            "actual_order_submitted": idx < 20,
            "spread_bps": 5,
            "buy_pressure_10t": 72,
        }
        for idx in range(70)
    ]
    _write_jsonl(data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", events)
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
        [{"date": target_date, "profit_rate": 1.2, "spread_bps": 5, "buy_pressure_10t": 72} for _ in range(50)],
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
    assert any(item["candidate_passed"] for item in report["candidate_grid"])
    assert report["recommended_policy"]["candidate_count"] == 0
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["buckets"] == {}


def test_build_report_reads_threshold_cycle_events_from_contract_path(monkeypatch, tmp_path):
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


def test_build_report_creates_bounded_equal_baseline_without_real_outcome(monkeypatch, tmp_path):
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

    balanced = next(item for item in report["candidate_grid"] if item["context_bucket"] == "balanced_normal")
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
    assert policy["buckets"]["balanced_normal"]["policy_mode"] == "bounded_equal_split_baseline"

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(split_plan.policy_path(target_date)))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE", target_date)
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
    assert fields["entry_split_order_policy_variant_id"] == "equal_50_50_offset_0pct_0_3pct"
    assert fields["entry_split_order_variant_id"] == "equal_50_50_offset_0pct_0_3pct__runtime_first_weight_40"
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

    balanced = next(item for item in report["candidate_grid"] if item["context_bucket"] == "balanced_normal")
    assert balanced["primary_sample_book"] == "real_split_variant"
    assert balanced["real_split_variant_outcome_joined_sample"] == 20
    assert balanced["source_quality_adjusted_ev_pct"] == 1.4
    assert balanced["policy_mode"] == "real_primary_ev_optimized"
    assert balanced["candidate_passed"] is True


def test_build_report_uses_post_submit_low_tick_band_for_price_offsets(monkeypatch, tmp_path):
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
    _write_jsonl(data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", rows)
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

    balanced = next(item for item in report["candidate_grid"] if item["context_bucket"] == "balanced_normal")
    assert balanced["policy_mode"] == "post_submit_tick_band_seed"
    assert balanced["optimization_basis"] == "post_submit_observed_low_tick_band"
    assert balanced["leg_count"] == 3
    assert balanced["price_offsets_ticks"] == [0, 1, 2]
    assert balanced["qty_weight_min"] == 0.34
    assert balanced["post_submit_low_tick_band"]["sample_count"] == 20
    assert balanced["post_submit_low_tick_band"]["p75_down_ticks"] == 2.0
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["buckets"]["balanced_normal"]["policy_mode"] == "post_submit_tick_band_seed"
    assert policy["buckets"]["balanced_normal"]["price_offsets_ticks"] == [0, 1, 2]


def test_post_submit_tick_band_excludes_source_quality_hard_blocked_rows(monkeypatch, tmp_path):
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
    _write_jsonl(data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", rows)
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

    balanced = next(item for item in report["candidate_grid"] if item["context_bucket"] == "balanced_normal")
    assert balanced["post_submit_low_tick_band"] == {}
    assert balanced["policy_mode"] == "bounded_equal_split_baseline"
    assert balanced["price_offsets_ticks"] == [0, 1]


def test_post_sell_candidate_preserves_entry_split_variant_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(post_sell_feedback, "DATA_DIR", tmp_path / "data")
    post_sell_feedback._RECORDED_KEYS.clear()
    stock = {
        "name": "TEST",
        "strategy": "SCALPING",
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
        [{"tag": "normal", "qty": 5, "price": 1000, "order_type_code": "00", "tif": "DAY"}],
        stock={"buy_pressure_10t": 75},
        latency_gate={"spread_bps": 5, "latency_state": "SAFE", "quote_stale": False, "order_price": 1000},
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert len(orders) == 2
    assert sum(item["qty"] for item in orders) == 5
    assert min(item["qty"] for item in orders) >= 1
    assert orders[0]["price"] >= orders[1]["price"]


def test_allocator_uses_runtime_default_for_missing_bucket_policy(monkeypatch, tmp_path):
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
        [{"tag": "normal", "qty": 7, "price": 1000, "order_type_code": "00", "tif": "DAY"}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert fields["entry_split_order_policy_mode"] == "runtime_default_passive_center_40_60_0_3pct"
    assert fields["entry_split_order_policy_variant_id"] == "runtime_default_passive_center_40_60_offset_0pct_0_3pct"
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
    assert fields["entry_split_order_passive_bias_reason"] == "passive_center_first_leg_cap"
    assert [item["qty"] for item in orders] == [3, 4]
    assert [item["price"] for item in orders] == [1000, 997]


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
        [{"tag": "normal", "qty": 5, "price": 1000, "order_type_code": "00", "tif": "DAY"}],
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
    assert fields["entry_split_order_policy_variant_id"] == "equal_50_50_offset_0pct_0_3pct"
    assert fields["entry_split_order_variant_id"] == "equal_50_50_offset_0pct_0_3pct__runtime_first_weight_20"
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.2
    assert fields["entry_split_order_qty_weight_max"] == 0.2
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert fields["entry_split_order_passive_bias_reason"].startswith("ai_wait_with_")
    assert [item["qty"] for item in orders] == [1, 4]
    assert [item["price"] for item in orders] == [1000, 997]
    assert sum(item["qty"] for item in orders) == 5


def test_allocator_passive_centers_buy_action_without_wait_warning(monkeypatch, tmp_path):
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
        [{"tag": "normal", "qty": 5, "price": 1000, "order_type_code": "00", "tif": "DAY"}],
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
    assert fields["entry_split_order_passive_bias_reason"] == "passive_center_first_leg_cap"
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.4
    assert fields["entry_split_order_qty_weight_max"] == 0.4
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert [item["qty"] for item in orders] == [2, 3]


def test_allocator_market_first_uses_policy_weight_and_keeps_residual_at_resolver(monkeypatch, tmp_path):
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
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE", target_date)

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 32, "price": 12160, "order_type_code": "00", "tif": "DAY"}],
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
    assert [item["qty"] for item in orders] == [16, 16]
    assert orders[0]["order_type_code"] == "3"
    assert orders[0]["entry_split_order_execution_mode"] == "market_first"
    assert orders[0]["entry_split_order_market_reference_price"] == 12240
    assert orders[1]["order_type_code"] == "00"
    assert orders[1]["entry_split_order_execution_mode"] == "resolver_limit"
    assert orders[1]["price"] < orders[0]["price"]


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
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", "2026-07-14")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 15, 9, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == "policy_inactive_date"
    assert orders[0]["qty"] == 4


def test_allocator_requires_date_bounded_operator_fallback_for_denied_policy(monkeypatch, tmp_path):
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
    assert blocked_fields["entry_split_order_skip_reason"] == "policy_runtime_apply_not_allowed"

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE", "2026-07-14")
    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=now,
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_operator_fallback_authorized"] is True
    assert all(item["entry_split_order_operator_fallback_authorized"] is True for item in orders)


def test_allocator_allows_split_when_source_quote_stale_recovered_before_submit(monkeypatch, tmp_path):
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


def test_allocator_fail_closed_for_qty_one_missing_invalid_and_stale_policy(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    one, one_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 1, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert one_fields["entry_split_order_skip_reason"] == "qty_lte_1"
    assert one[0]["qty"] == 1

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(tmp_path / "missing.json"))
    _, missing_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert missing_fields["entry_split_order_skip_reason"] == "policy_file_not_found"

    multi, multi_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "a", "qty": 1, "price": 1000}, {"tag": "b", "qty": 1, "price": 995}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert multi_fields["entry_split_order_skip_reason"] == "multi_order_input_not_supported_v1"
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
    policy_file = tmp_path / "threshold_cycle" / "entry_split_order_policy" / f"entry_split_order_policy_{target_date}.json"
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
    candidate = next(item for item in candidates if item["family"] == "entry_split_order_plan")

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["recommended_values"]["enabled"] is True
    assert candidate["recommended_values"]["policy_file"] == str(policy_file)
    overrides = preopen_apply._env_overrides_for_candidate(candidate)
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"] == str(policy_file)
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION"] == "entry_split_order_plan:test"


def test_daily_report_handoff_accepts_bounded_equal_baseline(monkeypatch, tmp_path):
    target_date = "2026-07-07"
    report_dir = tmp_path / "report" / "entry_split_order_plan"
    policy_file = tmp_path / "threshold_cycle" / "entry_split_order_policy" / f"entry_split_order_policy_{target_date}.json"
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
    candidate = next(item for item in candidates if item["family"] == "entry_split_order_plan")

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["source_metrics"]["bounded_equal_split_baseline_candidate_count"] == 1
    overrides = preopen_apply._env_overrides_for_candidate(candidate)
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED"] == "true"
    assert overrides["KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"] == str(policy_file)
