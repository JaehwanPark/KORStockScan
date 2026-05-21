import json

from src.tests import bedrock_nova_lite_shadow_report as mod


def test_bedrock_nova_lite_shadow_report_summarizes_rows(tmp_path, monkeypatch):
    source = tmp_path / "shadow.jsonl"
    rows = [
        {
            "openai_request_id": "req-1",
            "endpoint_name": "analyze_target",
            "pipeline_stage": "analyze_target",
            "symbol": "000001",
            "record_id": "10",
            "sim_record_id": "SIM-1",
            "sim_parent_record_id": "PARENT-1",
            "entry_adm_candidate_id": "ADM-1",
            "source_event_stage": "scalp_sim_holding_review",
            "cache_key": "ck1",
            "openai_action": "BUY",
            "openai_score": 80,
            "nova_action": "BUY",
            "nova_score": 78,
            "action_match": True,
            "score_delta": -2,
            "openai_latency_ms": 120,
            "nova_latency_ms": 180,
            "estimated_openai_cost_usd": 0.00001,
            "estimated_nova_cost_usd": 0.000004,
            "nova_prompt_cache_enabled": True,
            "nova_input_tokens": 100,
            "nova_cache_read_input_tokens": 1000,
            "nova_cache_write_input_tokens": 0,
            "nova_total_input_tokens": 1100,
            "parse_ok": True,
            "error_type": "",
        },
        {
            "openai_request_id": "req-2",
            "endpoint_name": "analyze_target",
            "pipeline_stage": "analyze_target",
            "symbol": "000002",
            "record_id": "11",
            "cache_key": "ck2",
            "openai_action": "WAIT",
            "openai_score": 51,
            "nova_action": "",
            "nova_score": None,
            "action_match": False,
            "score_delta": None,
            "openai_latency_ms": 100,
            "nova_latency_ms": None,
            "estimated_openai_cost_usd": 0.00002,
            "estimated_nova_cost_usd": 0.0,
            "nova_prompt_cache_enabled": False,
            "nova_input_tokens": 20,
            "nova_cache_read_input_tokens": None,
            "nova_cache_write_input_tokens": None,
            "nova_total_input_tokens": None,
            "parse_ok": False,
            "error_type": "JSONDecodeError",
        },
    ]
    source.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    (post_sell_dir / "sim_post_sell_candidates_2026-05-21.jsonl").write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {
                    "post_sell_id": "POST-1",
                    "sim_record_id": "SIM-1",
                    "stock_name": "테스트",
                    "sell_time": "11:00:00",
                    "profit_rate": 1.2,
                    "exit_rule": "scalp_trailing_take_profit",
                    "entry_adm_candidate_id": "ADM-1",
                },
                {
                    "post_sell_id": "POST-2",
                    "sim_record_id": "SIM-MISSING",
                    "stock_name": "미매칭",
                    "sell_time": "11:01:00",
                    "profit_rate": -0.5,
                    "exit_rule": "scalp_soft_stop_pct",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (post_sell_dir / "sim_post_sell_evaluations_2026-05-21.jsonl").write_text(
        json.dumps(
            {
                "post_sell_id": "POST-1",
                "sim_record_id": "SIM-1",
                "outcome": "MISSED_UPSIDE",
                "metrics_10m": {"mfe_pct": 1.1, "mae_pct": -0.2},
                "metrics_60m": {"mfe_pct": 1.3},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: source)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    report = mod.build_report("2026-05-21")

    assert report["summary"]["row_count"] == 2
    assert report["summary"]["parse_ok_rate"] == 0.5
    assert report["summary"]["action_match_rate"] == 1.0
    assert report["cost"]["estimated_openai_cost_usd"] == 0.00003
    assert report["cost"]["estimated_nova_cost_usd"] == 0.000004
    assert report["prompt_cache"]["enabled_row_count"] == 1
    assert report["prompt_cache"]["nova_cache_read_input_tokens"] == 1000
    assert report["prompt_cache"]["nova_total_input_tokens"] == 1120
    assert report["parse_schema_quality"]["error_counts"] == {"JSONDecodeError": 1}
    assert report["tuning_linkage"]["sample_rows"][0]["openai_request_id"] == "req-1"
    assert report["tuning_linkage"]["sample_rows"][0]["sim_record_id"] == "SIM-1"
    assert report["decision_agreement"]["source_event_stage_counts"]["scalp_sim_holding_review"] == 1
    assert report["outcome_linked_performance"]["exact_matched_count"] == 1
    assert report["outcome_linked_performance"]["unmatched_sell_count"] == 1
    assert report["outcome_linked_performance"]["overall"]["openai_outcome_score_sum"] == 1
    assert report["outcome_linked_performance"]["overall"]["nova_outcome_score_sum"] == 1
    lifecycle = report["outcome_linked_performance"]["lifecycle_quality"]
    assert lifecycle["evaluation_matched_count"] == 1
    assert lifecycle["overall"]["openai_lifecycle_quality_score_sum"] == 1
    assert lifecycle["overall"]["nova_lifecycle_quality_score_sum"] == 1
    assert lifecycle["by_lifecycle_stage"]["holding_exit"]["matched_count"] == 1
    performance = report["outcome_linked_performance"]["engine_decision_performance"]
    assert performance["primary_decision_metric"] == "engine_action_lifecycle_quality_score"
    assert performance["all_exact_matches"]["openai"]["quality_score_sum"] == 1
    assert performance["all_exact_matches"]["nova"]["quality_score_sum"] == 1
    assert performance["evaluated_forward_label_matches"]["row_count"] == 1
    assert report["outcome_linked_performance"]["sample_rows"][0]["mfe_10m_pct"] == 1.1

    json_path, md_path = mod.write_report(report)
    assert json_path.exists()
    assert md_path.exists()
    assert "Decision Agreement" in md_path.read_text(encoding="utf-8")
    assert "Prompt Cache" in md_path.read_text(encoding="utf-8")
    assert "Outcome-Linked Performance" in md_path.read_text(encoding="utf-8")
