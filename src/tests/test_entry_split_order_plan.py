from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from src.engine.scalping import entry_split_order_plan as split_plan
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
    assert urgent["primary_sample_book"] == "real"
    assert urgent["diagnostic_sim_ev_pct"] == 1.2
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
