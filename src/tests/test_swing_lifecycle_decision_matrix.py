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


def test_swing_lifecycle_flow_bucket_complete_flow_and_carry_normalization():
    rows = []
    for stage, label in (("entry", None), ("carry", None), ("scale_in", None), ("exit", 1.4)):
        rows.append(
            {
                "lifecycle_stage": stage,
                "source_book": "swing_intraday_live_equiv_probe",
                "source_stage": f"swing_{stage}",
                "stock_code": "005930",
                "event_time": f"2026-05-22T09:0{len(rows)}:00+09:00",
                "row_id": f"row_{stage}",
                "runtime_features": {
                    "lifecycle_flow_bridge_key": "FLOW-1",
                    "origin": "safe_pool",
                    "block_reason": "none",
                    "position_tag": "probe",
                    "strategy": "probe_v1",
                    "broker_order_forbidden": True,
                },
                "label_fields": {"final_return_pct": label, "mfe_pct": 2.0, "mae_pct": -0.3},
                "source_quality_status": "pass",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
            }
        )

    attribution = mod._swing_lifecycle_flow_bucket_attribution(rows)

    assert attribution["metric_scope"] == "swing_lifecycle_bundle_ev"
    assert attribution["summary"]["complete_flow_count"] == 1
    assert attribution["summary"]["identity_join_rate"] == 1.0
    assert attribution["flows"][0]["identity_quality"] == "lifecycle_flow_bridge_key"
    assert attribution["flows"][0]["stage_presence"] == {"entry": True, "holding": True, "exit": True}
    assert attribution["flows"][0]["scale_in_bucket_ids"]
    assert attribution["buckets"][0]["source_quality_gate"] == "hold_sample"
    assert attribution["runtime_approval_candidates"] == []


def test_swing_lifecycle_flow_fallback_identity_does_not_promote():
    rows = [
        {
            "lifecycle_stage": stage,
            "source_book": "swing_intraday_live_equiv_probe",
            "stock_code": "005930",
            "event_time": f"2026-05-22T09:0{idx}:00+09:00",
            "runtime_features": {"origin": "safe_pool"},
            "label_fields": {"final_return_pct": 1.0},
            "source_quality_status": "pass",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        }
        for idx, stage in enumerate(("entry", "holding", "exit"))
    ]

    attribution = mod._swing_lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["complete_flow_count"] == 0
    assert attribution["summary"]["join_contract_blocked"] is True
    assert attribution["summary"]["incomplete_flow_reason_counts"]["fallback_identity_incomplete"] == 3
    assert all(flow["source_quality_gate"] == "fallback_identity_incomplete" for flow in attribution["flows"])
    assert attribution["runtime_approval_candidates"] == []


def test_swing_lifecycle_flow_arm_identity_is_stock_scoped():
    rows = [
        {
            "lifecycle_stage": "entry",
            "source_book": "swing_strategy_discovery_sim",
            "stock_code": "005930",
            "event_time": "2026-05-22",
            "runtime_features": {"swing_strategy_discovery_arm_id": "shared_arm"},
            "label_fields": {"final_return_pct": 1.0},
            "source_quality_status": "pass",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
        {
            "lifecycle_stage": "holding",
            "source_book": "swing_strategy_discovery_sim",
            "stock_code": "000660",
            "event_time": "2026-05-22",
            "runtime_features": {"swing_strategy_discovery_arm_id": "shared_arm"},
            "label_fields": {"final_return_pct": 1.0},
            "source_quality_status": "pass",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
        {
            "lifecycle_stage": "exit",
            "source_book": "swing_strategy_discovery_sim",
            "stock_code": "000660",
            "event_time": "2026-05-22",
            "runtime_features": {"swing_strategy_discovery_arm_id": "shared_arm"},
            "label_fields": {"final_return_pct": 1.0},
            "source_quality_status": "pass",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
    ]

    attribution = mod._swing_lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["complete_flow_count"] == 0
    assert attribution["summary"]["incomplete_flow_count"] == 2
    identities = {item["flow_instance_id"] for item in attribution["flows"]}
    assert identities == {
        "swing_strategy_discovery_arm_id:005930:shared_arm",
        "swing_strategy_discovery_arm_id:000660:shared_arm",
    }


def test_pipeline_event_probe_fields_are_consumed(tmp_path, monkeypatch):
    target = "2026-05-22"
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report" / "swing_lifecycle_decision_matrix")

    with (event_dir / f"pipeline_events_{target}.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "event_type": "pipeline_event",
                    "stage": "swing_probe_sell_order_assumed_filled",
                    "stock_code": "005930",
                    "record_id": None,
                    "fields": {
                        "simulation_book": "swing_intraday_live_equiv_probe",
                        "swing_intraday_probe": "True",
                        "actual_order_submitted": "False",
                        "broker_order_forbidden": "True",
                        "record_id": "field-record-10",
                        "probe_origin_stage": "blocked_gatekeeper_reject",
                        "position_tag": "probe",
                        "strategy": "probe_v1",
                        "profit_rate": "2.4",
                        "exit_rule": "time_stop",
                    },
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    monkeypatch.setattr(mod, "_load_discovery_lifecycle_rows", lambda target_date, db_url, lookback_days: ([], {}))

    report = mod.build_swing_lifecycle_decision_matrix(target, db_url="sqlite://")

    assert report["summary"]["probe_rows"] == 1
    assert report["summary"]["source_book_counts"]["swing_intraday_live_equiv_probe"] == 1
    assert "swing_intraday_live_equiv_probe_missing" not in report["warnings"]
    assert report["lifecycle_rows"][0]["source_stage"] == "swing_probe_sell_order_assumed_filled"
    assert report["lifecycle_rows"][0]["row_id"] == "field-record-10"


def test_swing_ldm_stage_only_candidates_remain_child_evidence(tmp_path, monkeypatch):
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

    assert candidates == []
    assert report["holding_exit_bucket_attribution"]["summary"]["bucket_count"] > 0
    assert report["holding_exit_bucket_attribution"]["summary"]["sim_auto_candidate_count"] == 0
    assert report["swing_lifecycle_flow_bucket_attribution"]["runtime_approval_candidates"] == []


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
