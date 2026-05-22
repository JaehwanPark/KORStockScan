import json

from src.engine import swing_lifecycle_decision_matrix as mod


def test_probe_and_discovery_rows_build_swing_ldm_contract(tmp_path, monkeypatch):
    target = "2026-05-22"
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report" / "swing_lifecycle_decision_matrix")

    records = [
        {
            "event": "swing_probe_holding_started",
            "simulation_book": "swing_intraday_live_equiv_probe",
            "stock_code": "005930",
            "probe_origin_stage": "safe_pool",
            "block_reason": "swing_probe_entry_candidate",
            "position_tag": "probe",
            "strategy": "probe_v1",
            "gap_pct": 1.2,
            "score": 78,
            "v_pw": 1.1,
            "qty_source": "sim_budget",
            "entry_price_provenance": "assumed_fill",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        {
            "event": "swing_probe_sell_order_assumed_filled",
            "simulation_book": "swing_intraday_live_equiv_probe",
            "stock_code": "005930",
            "probe_origin_stage": "safe_pool",
            "block_reason": "swing_probe_entry_candidate",
            "position_tag": "probe",
            "strategy": "probe_v1",
            "profit_rate": 2.4,
            "mfe_pct": 3.1,
            "mae_pct": -0.8,
            "exit_rule": "time_stop",
        },
    ]
    with (event_dir / f"pipeline_events_{target}.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    discovery_source = {
        "source_date": target,
        "stock_code": "000660",
        "arm_row_id": 10,
        "arm_id": "arm_a",
        "entry_policy": "pullback",
        "sizing_policy": "one_share",
        "exit_policy": "policy_exit",
        "selection_arm": "lifecycle_rank",
        "legacy_pick_type": "legacy_ml",
        "position_tag": "discovery",
        "block_reason": "safe_pool",
        "sector": "semiconductor",
        "theme_tags": "ai",
        "label_status": "labeled",
        "final_return_pct": 1.6,
        "realized_exit_return_pct": 1.6,
        "mfe_pct": 2.0,
        "mae_pct": -0.5,
        "source_quality_status": "pass",
    }
    monkeypatch.setattr(
        mod,
        "_load_discovery_lifecycle_rows",
        lambda target_date, db_url, lookback_days: ([mod._discovery_row(discovery_source)], {"READY": 1}),
    )

    report = mod.build_swing_lifecycle_decision_matrix(target, db_url="sqlite://", lookback_days=5)

    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert report["input_contract"]["swing_daily_simulation_consumed"] is False
    assert report["summary"]["probe_rows"] == 2
    assert report["summary"]["discovery_rows"] == 1
    assert report["summary"]["source_book_counts"] == {
        "swing_intraday_live_equiv_probe": 2,
        "swing_strategy_discovery_sim": 1,
    }
    assert report["entry_bucket_attribution"]["metric_contract"]["forbidden_uses"]
    assert report["entry_bucket_attribution"]["summary"]["bucket_count"] > 0
    assert all(row["source_book"] != "swing_daily_simulation" for row in report["lifecycle_rows"])


def test_swing_ldm_sim_auto_candidates_remain_sim_only(tmp_path, monkeypatch):
    target = "2026-05-22"
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report" / "swing_lifecycle_decision_matrix")

    with (event_dir / f"pipeline_events_{target}.jsonl").open("w", encoding="utf-8") as handle:
        for idx in range(3):
            handle.write(
                json.dumps(
                    {
                        "event": "swing_probe_sell_order_assumed_filled",
                        "simulation_book": "swing_intraday_live_equiv_probe",
                        "stock_code": f"00000{idx}",
                        "probe_origin_stage": "safe_pool",
                        "block_reason": "swing_probe_entry_candidate",
                        "position_tag": "probe",
                        "strategy": "probe_v1",
                        "profit_rate": 1.0 + idx,
                    }
                )
                + "\n"
            )
    monkeypatch.setattr(mod, "_load_discovery_lifecycle_rows", lambda target_date, db_url, lookback_days: ([], {}))

    report = mod.build_swing_lifecycle_decision_matrix(target, db_url="sqlite://")
    candidates = report["holding_exit_bucket_attribution"]["sim_auto_approval_candidates"]

    assert candidates
    assert {item["classification_hint"] for item in candidates} == {"sim_auto_approved"}
    assert all(item["actual_order_submitted"] is False for item in candidates)
    assert all(item["broker_order_forbidden"] is True for item in candidates)
    assert all(item["allowed_runtime_apply"] is False for item in candidates)
    assert all("real_order_submit" in item["forbidden_uses"] for item in candidates)


def test_swing_ldm_workorders_remain_source_only(tmp_path, monkeypatch):
    target = "2026-05-22"
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report" / "swing_lifecycle_decision_matrix")

    with (event_dir / f"pipeline_events_{target}.jsonl").open("w", encoding="utf-8") as handle:
        for idx in range(3):
            handle.write(
                json.dumps(
                    {
                        "event": "swing_probe_sell_order_assumed_filled",
                        "simulation_book": "swing_intraday_live_equiv_probe",
                        "stock_code": f"00593{idx}",
                        "profit_rate": 1.0,
                    }
                )
                + "\n"
            )
    monkeypatch.setattr(mod, "_load_discovery_lifecycle_rows", lambda target_date, db_url, lookback_days: ([], {}))

    report = mod.build_swing_lifecycle_decision_matrix(target, db_url="sqlite://")
    workorders = report["holding_exit_bucket_attribution"]["code_improvement_workorders"]

    assert workorders
    assert all(item["runtime_effect"] is False for item in workorders)
    assert all(item["allowed_runtime_apply"] is False for item in workorders)
    assert all(item["actual_order_submitted"] is False for item in workorders)
    assert all(item["broker_order_forbidden"] is True for item in workorders)
    assert all("runtime_threshold_mutation" in item["forbidden_uses"] for item in workorders)
