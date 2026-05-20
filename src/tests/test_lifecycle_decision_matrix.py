import json

from src.engine import lifecycle_decision_matrix as mod


def test_lifecycle_matrix_builder_separates_runtime_features_and_labels(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    entry_dir.mkdir(parents=True)
    post_sell_dir.mkdir(parents=True)
    monitor_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    examples = [
        {
            "candidate_id": f"cand-{idx}",
            "stock_code": f"000{idx:03d}",
            "event_time": "2026-05-18T09:01:00+09:00",
            "stage": "scalp_entry_action_decision_snapshot",
            "chosen_action": "WAIT_REQUOTE",
            "ai_score": 67 + (idx % 3),
            "ai_action": "WAIT",
            "mfe_10m_pct": 1.2,
            "mae_10m_pct": -0.3,
            "close_10m_pct": 0.8,
            "outcome_joined": True,
        }
        for idx in range(25)
    ]
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps({"examples": examples}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-18")

    assert report["summary"]["total_rows"] == 25
    assert report["summary"]["joined_rows"] == 25
    assert "ai_score" in report["runtime_feature_keys"]
    assert "mfe_10m_pct" not in report["runtime_feature_keys"]
    assert "mfe_10m_pct" in report["label_keys"]
    assert report["examples"][0]["runtime_features"]["ai_score"] >= 67
    assert "mfe_10m_pct" not in report["examples"][0]["runtime_features"]
    assert "mfe_10m_pct" in report["examples"][0]["labels"]
    assert report["fixed_threshold_contract"]["roles"]["baseline_prior"]
    assert any(item["stage"] == "entry" and item["source_quality_gate"] == "pass" for item in report["policy_entries"])
    assert (matrix_dir / "lifecycle_decision_matrix_2026-05-18.json").exists()
    assert (matrix_dir / "lifecycle_decision_matrix_2026-05-18.md").exists()


def test_lifecycle_matrix_ingests_scalp_sim_scale_in_rows(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    entry_dir.mkdir(parents=True)
    post_sell_dir.mkdir(parents=True)
    monitor_dir.mkdir(parents=True)
    pipeline_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    events = [
        {
            "stage": "scalp_sim_scale_in_order_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:00:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "ord_no": "SIMADD-1",
                "add_type": "PYRAMID",
                "qty": "2",
                "limit_price": "1000",
                "curr_price": "1000",
                "best_bid": "990",
                "best_ask": "1000",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
            },
        },
        {
            "stage": "scalp_sim_holding_snapshot",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:01:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "profit_rate": "1.2",
            },
        },
        {
            "stage": "scalp_sim_holding_snapshot",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:02:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "profit_rate": "-0.4",
            },
        },
        {
            "stage": "scalp_sim_sell_order_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:03:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "profit_rate": "0.7",
                "exit_rule": "trailing_take_profit",
                "actual_order_submitted": "False",
            },
        },
    ]
    (pipeline_dir / "pipeline_events_2026-05-19.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-19")

    scale_rows = [row for row in report["examples"] if row.get("stage") == "scale_in"]
    assert len(scale_rows) == 1
    assert scale_rows[0]["source"] == "scalp_sim_scale_in_pipeline_events"
    assert scale_rows[0]["runtime_features"]["add_type"] == "PYRAMID"
    assert scale_rows[0]["runtime_features"]["actual_order_submitted"] == "False"
    assert "mfe_10m_pct" not in scale_rows[0]["runtime_features"]
    assert scale_rows[0]["labels"]["profit_rate"] == 0.7
    assert scale_rows[0]["labels"]["mfe_10m_pct"] == 1.2
    assert scale_rows[0]["labels"]["mae_10m_pct"] == -0.4
    assert report["sources"]["scalp_sim_scale_in"]["filled_events"] == 1
    assert any(item["stage"] == "scale_in" and item["sample"] == 1 for item in report["policy_entries"])


def test_lifecycle_matrix_joins_institutional_flow_features(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    flow_dir = tmp_path / "institutional_flow_context"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, flow_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "institutional_flow_report_paths",
        lambda target_date: (
            flow_dir / f"institutional_flow_context_{target_date}.json",
            flow_dir / f"institutional_flow_context_{target_date}.md",
        ),
    )
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-20.json").write_text(
        json.dumps(
            {
                "examples": [
                    {
                        "candidate_id": "cand-1",
                        "stock_code": "005930",
                        "event_time": "2026-05-20T09:01:00+09:00",
                        "stage": "scalp_entry_action_decision_snapshot",
                        "chosen_action": "WAIT_REQUOTE",
                        "ai_score": 66,
                        "mfe_10m_pct": 1.2,
                        "mae_10m_pct": -0.3,
                        "close_10m_pct": 0.8,
                        "outcome_joined": True,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (flow_dir / "institutional_flow_context_2026-05-20.json").write_text(
        json.dumps(
            {
                "summary": {"row_count": 1},
                "rows": [
                    {
                        "stock_code": "005930",
                        "foreign_net_roll5": 100,
                        "inst_net_roll5": 200,
                        "dual_net_buy": True,
                        "institutional_flow_status": "OK",
                        "institutional_flow_regime": "DUAL_ACCUMULATION",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-20")

    features = report["examples"][0]["runtime_features"]
    assert features["foreign_net_roll5"] == 100
    assert features["inst_net_roll5"] == 200
    assert features["institutional_flow_status"] == "OK"
    assert report["sources"]["institutional_flow_context"]["joined_rows"] == 1
