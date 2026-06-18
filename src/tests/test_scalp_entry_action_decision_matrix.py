import gzip
import json
from dataclasses import replace
from datetime import datetime

from src.engine import scalp_entry_action_decision_matrix as mod
from src.engine import scalp_entry_adm_runtime as runtime_mod


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _write_gzip_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_entry_adm_excludes_early_accel_recheck_retry_rows(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    snapshot_dir = threshold_dir / "snapshots"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", snapshot_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": "62",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:01",
                "emitted_date": "2026-05-18",
                "fields": {
                    "source_stage": "blocked_ai_score",
                    "chosen_action": "NO_BUY_AI",
                    "ai_score": "62",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "order_bundle_submitted",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:02",
                "emitted_date": "2026-05-18",
                "fields": {
                    "actual_order_submitted": "true",
                    "broker_order_submitted": "true",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "blocked_ai_score",
                "stock_code": "222222",
                "record_id": "R2",
                "emitted_at": "2026-05-18T09:11:00",
                "emitted_date": "2026-05-18",
                "fields": {"ai_score": "63"},
            },
        ],
    )

    rows = list(mod._iter_relevant_events("2026-05-18"))

    assert len(rows) == 1
    assert rows[0]["stock_code"] == "222222"


def test_scalp_entry_adm_report_aggregates_actions_and_joins_outcomes(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    snapshot_dir = threshold_dir / "snapshots"
    post_sell_dir = tmp_path / "post_sell"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "stock_name": "A",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {"ai_score": "62", "quote_age_ms": "100"},
            },
            {
                "stage": "entry_submit_revalidation_warning",
                "stock_code": "222222",
                "record_id": "R2",
                "emitted_at": "2026-05-18T09:11:00",
                "emitted_date": "2026-05-18",
                "fields": {"entry_submit_revalidation_warning": True, "quote_age_ms": "1500"},
            },
            {
                "stage": "entry_submit_revalidation_block",
                "stock_code": "333333",
                "record_id": "R3",
                "emitted_at": "2026-05-18T09:12:00",
                "emitted_date": "2026-05-18",
                "fields": {"entry_submit_revalidation_block": True, "quote_stale": True},
            },
            {
                "stage": "pre_submit_liquidity_guard_block",
                "stock_code": "444444",
                "record_id": "R4",
                "emitted_at": "2026-05-18T09:13:00",
                "emitted_date": "2026-05-18",
                "fields": {"blocked_reason": "below_min_liquidity"},
            },
            {
                "stage": "scalp_sim_buy_order_virtual_pending",
                "stock_code": "555555",
                "record_id": "R5P",
                "emitted_at": "2026-05-18T09:13:30",
                "emitted_date": "2026-05-18",
                "fields": {"sim_record_id": "SIM1", "best_ask": "1000", "would_limit_fill": False},
            },
            {
                "stage": "scalp_sim_buy_order_assumed_filled",
                "stock_code": "555555",
                "record_id": "R5",
                "emitted_at": "2026-05-18T09:14:00",
                "emitted_date": "2026-05-18",
                "fields": {"sim_record_id": "SIM1", "best_ask": "1000", "would_limit_fill": False},
            },
            {
                "stage": "scalp_sim_entry_ai_price_skip_order",
                "stock_code": "777777",
                "record_id": "R7",
                "emitted_at": "2026-05-18T09:14:30",
                "emitted_date": "2026-05-18",
                "fields": {
                    "sim_record_id": "SIM2",
                    "entry_adm_candidate_id": "ADM-SIM2",
                    "broker_order_forbidden": True,
                    "actual_order_submitted": False,
                    "decision_authority": "sim_observation_only",
                    "runtime_effect": "simulated_order_skipped",
                },
            },
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "666666",
                "record_id": "R6",
                "emitted_at": "2026-05-18T09:15:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "candidate_id": "ADM2",
                    "chosen_action": "BUY_DEFENSIVE",
                    "entry_adm_prompt_applied": True,
                    "entry_adm_runtime_bias_applied": True,
                    "entry_adm_runtime_effect": "buy_defensive_bias",
                    "entry_adm_forced_action": "BUY",
                    "entry_adm_runtime_reason": "matrix_buy_defensive",
                },
            },
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "888888",
                "record_id": "R8",
                "emitted_at": "2026-05-18T09:16:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "candidate_id": "ADM3",
                    "source_stage": "order_bundle_submitted",
                    "chosen_action": "NO_BUY_AI",
                    "actual_order_submitted": True,
                    "price_resolution_reason": "defensive_order_price",
                },
            },
        ],
    )
    _write_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-18.jsonl",
        [
            {
                "sim_record_id": "SIM1",
                "profit_rate": 1.25,
                "exit_rule": "tp",
                "outcome": "MISSED_UPSIDE",
                "metrics_10m": {"mfe_pct": 1.5, "mae_pct": -0.2, "close_ret_pct": 0.8},
                "metrics_30m": {"mfe_pct": 2.0, "mae_pct": -0.2, "close_ret_pct": 1.1},
                "metrics_60m": {"mfe_pct": 2.4, "mae_pct": -0.2, "close_ret_pct": 1.2},
            },
            {
                "candidate_id": "ADM2",
                "profit_rate": -1.0,
                "exit_rule": "stop",
                "outcome": "GOOD_EXIT",
                "metrics_10m": {"mfe_pct": 0.1, "mae_pct": -1.5, "close_ret_pct": -0.8},
                "metrics_30m": {"mfe_pct": 0.2, "mae_pct": -1.8, "close_ret_pct": -1.0},
                "metrics_60m": {"mfe_pct": 0.3, "mae_pct": -2.0, "close_ret_pct": -1.2},
            },
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")

    counts = report["summary"]["action_counts"]
    assert counts["NO_BUY_AI"] == 1
    assert counts["WAIT_REQUOTE"] == 1
    assert counts["SKIP_STALE"] == 1
    assert counts["SKIP_PRE_SUBMIT_SAFETY"] == 2
    assert counts["BUY_NOW"] == 1
    assert counts["BUY_DEFENSIVE"] == 2
    assert report["summary"]["raw_action_counts"]["NO_BUY_AI"] == 1
    assert report["summary"]["action_normalized_count"] == 1
    assert report["summary"]["action_normalization_counts"] == {
        "submitted_or_latency_pass_non_buy_action_normalized": 1
    }
    assert report["summary"]["joined_sample"] == 2
    buy_now = next(item for item in report["action_summary"] if item["action"] == "BUY_NOW")
    defensive = next(item for item in report["action_summary"] if item["action"] == "BUY_DEFENSIVE")
    assert buy_now["equal_weight_avg_profit_pct"] == 1.25
    assert defensive["equal_weight_avg_profit_pct"] == -1.0
    assert report["summary"]["prompt_applied_count"] == 1
    assert report["summary"]["runtime_bias_applied_count"] == 1
    assert report["summary"]["runtime_effect_counts"]["buy_defensive_bias"] == 1
    assert report["summary"]["forced_action_counts"]["BUY"] == 1
    assert len(report["rows"]) == report["summary"]["total_candidates"]
    assert report["examples"] == report["rows"][:50]
    sim_row = next(item for item in report["rows"] if item["sim_record_id"] == "SIM1")
    assert sim_row["stage"] == "scalp_sim_buy_order_assumed_filled"
    price_skip_row = next(item for item in report["rows"] if item["sim_record_id"] == "SIM2")
    assert price_skip_row["chosen_action"] == "SKIP_PRE_SUBMIT_SAFETY"
    assert (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").exists()


def test_scalp_entry_adm_report_excludes_numeric_inconsistency_rows_from_aggregates(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    snapshot_dir = threshold_dir / "snapshots"
    post_sell_dir = tmp_path / "post_sell"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "candidate_id": "ADM-NUMERIC",
                    "chosen_action": "NO_BUY_AI",
                    "ai_reason_numeric_inconsistency": True,
                    "source_quality_gate": "ai_numeric_consistency_review_required",
                },
            },
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "222222",
                "record_id": "R2",
                "emitted_at": "2026-05-18T09:11:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "candidate_id": "ADM-CLEAN",
                    "chosen_action": "NO_BUY_AI",
                    "source_stage": "ai_confirmed",
                },
            },
        ],
    )
    _write_jsonl(post_sell_dir / "sim_post_sell_evaluations_2026-05-18.jsonl", [])

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")

    assert report["summary"]["total_candidates"] == 2
    assert report["summary"]["aggregate_total_candidates"] == 1
    assert report["summary"]["joined_sample"] == 0
    assert report["summary"]["joined_sample_all_rows"] == 0
    assert report["summary"]["aggregate_joined_sample"] == 0
    assert report["summary"]["numeric_consistency_excluded_count"] == 1
    assert "ai_numeric_consistency_rows_excluded_from_aggregates" in report["warnings"]
    assert "joined_sample_below_sample_floor" in report["warnings"]
    no_buy = next(item for item in report["action_summary"] if item["action"] == "NO_BUY_AI")
    assert no_buy["sample_count"] == 1


def test_scalp_entry_adm_loads_gzip_sim_evaluations(tmp_path, monkeypatch):
    post_sell_dir = tmp_path / "post_sell"
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _write_gzip_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-18.jsonl.gz",
        [{"sim_record_id": "SIM1", "candidate_id": "ADM1", "profit_rate": 1.25}],
    )

    rows, meta = mod._load_sim_evaluations("2026-05-18")

    assert meta["artifact"].endswith(".jsonl.gz")
    assert meta["rows"] == 1
    assert rows["SIM1"]["profit_rate"] == 1.25


def test_scalp_entry_adm_event_paths_include_gzip_threshold_events(tmp_path, monkeypatch):
    threshold_dir = tmp_path / "threshold_cycle"
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", threshold_dir / "snapshots")
    _write_gzip_jsonl(
        threshold_dir / "threshold_events_2026-05-18.jsonl.gz",
        [{"stage": "scalp_entry_action_decision_snapshot", "fields": {}}],
    )

    assert mod._event_paths("2026-05-18") == [threshold_dir / "threshold_events_2026-05-18.jsonl.gz"]


def test_scalp_entry_adm_report_warns_on_unknown_bucket_source_quality(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", threshold_dir / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)
    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "chosen_action": "NO_BUY_AI",
                    "entry_adm_bucket_token": "score_unknown|risk_unknown|stale_unknown",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")

    unknown_summary = report["summary"]["unknown_bucket_summary"]
    assert "unknown_bucket_source_quality_gap" in report["warnings"]
    assert unknown_summary["source_quality_gate"] == "source_quality_blocker"
    assert unknown_summary["recommended_route"] == "source_quality_workorder"
    assert 1 <= unknown_summary["affected_rows"] <= unknown_summary["total_rows"]
    assert unknown_summary["not_available_affected_rows"] <= unknown_summary["total_rows"]
    assert unknown_summary["dimension_counts"]["score_bucket"] == 1
    assert unknown_summary["unknown_root_cause_counts"]["score_bucket:source_score_missing"] == 1
    assert "unknown_dimension_occurrence_count" in unknown_summary
    assert "not_available_dimension_counts" in unknown_summary
    assert "recomputed_unknown_count" in unknown_summary
    assert "adm_source_bucket_used_count" in unknown_summary
    assert "unknown_bucket_affected_rows" in (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.md").read_text(
        encoding="utf-8"
    )


def test_scalp_entry_adm_normalizes_submitted_snapshot_action():
    fields = {
        "source_stage": "order_bundle_submitted",
        "chosen_action": "NO_BUY_AI",
        "actual_order_submitted": True,
        "broker_order_submitted": True,
        "broker_order_no": "0046858",
        "order_no": "0046858",
        "ord_no": "0046858",
        "broker_order_no_list": "0046858,0046859",
        "order_response_ord_no": "0046858",
        "submit_attempt_id": "005930:1781160000000:0046858",
        "price_resolution_reason": "defensive_order_price",
    }

    assert mod._chosen_action("scalp_entry_action_decision_snapshot", fields) == "BUY_DEFENSIVE"
    row = mod._base_row(
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "stock_code": "005930",
            "stock_name": "TEST",
            "fields": fields,
        }
    )
    assert row["source_stage"] == "order_bundle_submitted"
    assert row["raw_chosen_action"] == "NO_BUY_AI"
    assert row["chosen_action"] == "BUY_DEFENSIVE"
    assert row["action_normalized"] is True
    assert row["action_normalization_reason"] == "submitted_or_latency_pass_non_buy_action_normalized"
    assert row["broker_order_submitted"] is True
    assert row["broker_order_no"] == "0046858"
    assert row["order_no"] == "0046858"
    assert row["ord_no"] == "0046858"
    assert row["broker_order_no_list"] == "0046858,0046859"
    assert row["order_response_ord_no"] == "0046858"
    assert row["submit_attempt_id"] == "005930:1781160000000:0046858"
    assert (
        mod._chosen_action(
            "scalp_entry_action_decision_snapshot",
            {
                "source_stage": "entry_submit_revalidation_warning",
                "chosen_action": "WAIT_REQUOTE",
            },
        )
        == "WAIT_REQUOTE"
    )


def test_scalp_entry_adm_preserves_submit_refresh_provenance():
    row = mod._base_row(
        {
            "stage": "order_bundle_submitted",
            "stock_code": "005930",
            "stock_name": "TEST",
            "record_id": "R1",
            "emitted_at": "2026-05-18T09:10:02",
            "fields": {
                "actual_order_submitted": "true",
                "broker_order_submitted": "true",
                "broker_order_no": "0046858",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
                "quote_age_at_submit_ms": "2628",
                "best_bid_at_submit": "16860",
                "best_ask_at_submit": "16910",
                "submitted_order_price": "16830",
                "latency_state": "SAFE",
                "latency_danger_reasons": "spread_too_wide",
                "pre_submit_quote_refresh_enabled": "true",
                "pre_submit_quote_refresh_applied": "false",
                "pre_submit_quote_refresh_reason": "observer_quote_stale",
                "pre_submit_quote_refresh_source": "orderbook_micro_observer",
                "pre_submit_quote_refresh_quote_age_ms": "1500",
                "pre_submit_quote_refresh_strategy_id": "KOSPI_ML",
                "pre_submit_quote_refresh_env_value": "true",
                "pre_submit_ws_snapshot_refresh_enabled": "true",
                "pre_submit_ws_snapshot_refresh_applied": "true",
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                "pre_submit_ws_snapshot_refresh_source": "ws_manager_latest_data",
                "pre_submit_ws_snapshot_refresh_age_ms": "12",
            },
        }
    )

    assert row["entry_submit_revalidation_warning"] == "stale_context_or_quote"
    assert row["quote_age_ms"] == 2628.0
    assert row["best_bid"] == 16860.0
    assert row["best_ask"] == 16910.0
    assert row["resolved_order_price"] == 16830.0
    assert row["latency_state"] == "SAFE"
    assert row["latency_reason"] == "spread_too_wide"
    assert row["pre_submit_quote_refresh_enabled"] is True
    assert row["pre_submit_quote_refresh_applied"] is False
    assert row["pre_submit_quote_refresh_reason"] == "observer_quote_stale"
    assert row["pre_submit_quote_refresh_source"] == "orderbook_micro_observer"
    assert row["pre_submit_quote_refresh_quote_age_ms"] == 1500.0
    assert row["pre_submit_quote_refresh_strategy_id"] == "KOSPI_ML"
    assert row["pre_submit_quote_refresh_env_value"] == "true"
    assert row["pre_submit_ws_snapshot_refresh_enabled"] is True
    assert row["pre_submit_ws_snapshot_refresh_applied"] is True
    assert row["pre_submit_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert row["pre_submit_ws_snapshot_refresh_source"] == "ws_manager_latest_data"
    assert row["pre_submit_ws_snapshot_refresh_age_ms"] == 12.0


def test_scalp_entry_adm_runtime_context_adds_prompt_and_cache_token(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    bucket_token = "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close"
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [
                    {
                        "bucket_token": bucket_token,
                        "dominant_action": "BUY_NOW",
                        "sample_count": 25,
                        "joined_sample": 21,
                        "source_quality_adjusted_ev_pct": 0.42,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 151,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 4.0,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )

    assert context["applied"] is True
    assert context["cache_token"] == f"entry_adm:scalp_entry_adm_v1_2026-05-18:{bucket_token}"
    assert "[Entry ADM Advisory Context]" in context["prompt_context"]
    merged = runtime_mod.merge_scalp_entry_adm_result_fields({"action": "BUY", "score": 78}, context)
    assert merged["entry_adm_prompt_applied"] is True
    assert merged["entry_adm_bucket_token"] == bucket_token
    assert merged["entry_adm_bucket_schema_version"] == "entry_adm_bucket_v2"
    assert merged["entry_adm_market_regime_continuous_bucket"] == "-"
    assert merged["entry_adm_recommended_action"] == "BUY_NOW"
    assert merged["entry_adm_decision_alignment"] == "aligned_buy_bucket"

    disabled = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={},
        advisory_enabled=False,
        now=datetime(2026, 5, 18, 16, 30),
    )
    assert disabled["prompt_context"] == ""
    assert disabled["fields"]["entry_adm_prompt_applied"] is False

    excluded = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="swing",
        ws_data={},
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
    )
    assert excluded["status"] == "excluded_non_entry_prompt"


def test_scalp_entry_adm_runtime_bias_forces_wait_on_negative_buy_bucket(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    bucket_token = "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close"
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [
                    {
                        "bucket_token": bucket_token,
                        "dominant_action": "BUY_NOW",
                        "sample_count": 20,
                        "joined_sample": 10,
                        "source_quality_adjusted_ev_pct": -2.54,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 151,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 4.0,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )

    merged = runtime_mod.merge_scalp_entry_adm_result_fields({"action": "BUY", "score": 78}, context)

    assert merged["action"] == "WAIT"
    assert merged["entry_adm_runtime_bias_applied"] is True
    assert merged["entry_adm_runtime_effect"] == "force_wait"
    assert merged["entry_adm_runtime_reason"] == "bucket_negative_source_quality_adjusted_ev"


def test_scalp_entry_adm_runtime_maps_runtime_context_without_unknown_buckets(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps({"date": "2026-05-18", "matrix_version": "scalp_entry_adm_v1_2026-05-18", "bucket_summary": []}),
        encoding="utf-8",
    )

    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "current_ai_score": 62.0,
            "latest_strength": 70,
            "buy_pressure_10t": 35,
            "quote_stale": "False",
            "curr": 10_000,
            "volume": 100_000,
            "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]},
            "scalp_pre_ai_gate_context": {
                "strength_momentum": {
                    "risk_state": "weak_momentum_context",
                    "gate_action": "risk_context_only",
                },
                "overbought": {
                    "risk_state": "pullback_observed",
                    "risk_bucket": "pullback_candidate",
                },
            },
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
    )

    fields = context["fields"]
    assert fields["entry_adm_score_bucket"] == "score50_64"
    assert fields["entry_adm_risk_context_bucket"] == "weak_strength_momentum"
    assert fields["entry_adm_market_regime_continuous_bucket"] == "-"
    assert fields["entry_adm_stale_bucket"] == "fresh"
    assert fields["entry_adm_price_resolution_bucket"] == "quote_based"
    assert fields["entry_adm_liquidity_bucket"] == "liquidity_high"
    assert fields["entry_adm_overbought_bucket"] == "overbought_ok"
    assert "unknown" not in fields["entry_adm_bucket_token"]


def test_scalp_entry_adm_report_and_runtime_share_market_regime_bucket_contract(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "ai_confirmed",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": "78",
                    "action": "BUY",
                    "latest_strength": "150",
                    "quote_age_ms": "300",
                    "best_ask": "1000",
                    "trade_value_krw": "300000000",
                    "intraday_range_pct": "5.0",
                    "market_regime_continuous_label": "RISK_ON",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    report_token = report["rows"][0]["entry_adm_bucket_token_recomputed"]
    assert report["rows"][0]["market_regime_continuous_bucket"] == "market_regime_risk_on"

    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "current_ai_score": 78,
            "latest_strength": 150,
            "quote_age_ms": 300,
            "best_ask": 1000,
            "trade_value_krw": 300000000,
            "intraday_range_pct": 5.0,
            "market_regime_continuous_label": "RISK_ON",
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 9, 10),
    )

    fields = context["fields"]
    assert fields["entry_adm_market_regime_continuous_bucket"] == "market_regime_risk_on"
    assert fields["entry_adm_bucket_token"] == report_token


def test_scalp_entry_adm_bucket_sample_floor_blocks_force_wait(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    bucket_token = "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close"
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [
                    {
                        "bucket_token": bucket_token,
                        "dominant_action": "WAIT_REQUOTE",
                        "sample_count": 4,
                        "joined_sample": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 151,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 4.0,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )

    merged = runtime_mod.merge_scalp_entry_adm_result_fields({"action": "BUY", "score": 78}, context)

    assert merged["action"] == "BUY"
    assert merged["entry_adm_runtime_bias_applied"] is False
    assert merged["entry_adm_runtime_reason"] == "bucket_sample_below_floor"


def test_scalp_entry_adm_hypothesis_fallback_is_provenance_only_by_default(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps({"date": "2026-05-18", "matrix_version": "scalp_entry_adm_v1_2026-05-18", "bucket_summary": []}),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 70,
            "buy_pressure": 35,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 19.0,
            "distance_from_day_high_pct": -0.3,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )

    merged = runtime_mod.merge_scalp_entry_adm_result_fields({"action": "BUY", "score": 78}, context)

    assert merged["action"] == "BUY"
    assert merged["entry_adm_runtime_bias_applied"] is False
    assert merged["entry_adm_runtime_reason"] == "hypothesis_weak_momentum_chase_risk_provenance_only"


def test_scalp_entry_adm_prioritizes_adm_source_buckets_over_raw_recompute(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "chosen_action": "BUY_NOW",
                    "entry_adm_score_bucket": "score75_84",
                    "entry_adm_risk_context_bucket": "strong_strength_momentum",
                    "entry_adm_stale_bucket": "fresh",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "entry_adm_overbought_bucket": "overbought_normal",
                    "entry_adm_bucket_token": "score75_84|strong_strength_momentum|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000",
                    "best_ask": "1000",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    row = report["rows"][0]

    assert row["score_bucket"] == "score75_84"
    assert row["risk_context_bucket"] == "strong_strength_momentum"
    assert row["stale_bucket"] == "fresh"
    assert row["price_resolution_bucket"] == "quote_based"
    assert row["liquidity_bucket"] == "liquidity_high"
    assert row["overbought_bucket"] == "overbought_normal"
    assert row["entry_adm_bucket_token"] == "score75_84|strong_strength_momentum|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000"
    assert row["entry_adm_bucket_token_recomputed"] == "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000"
    assert row["entry_adm_bucket_schema_version"] == "entry_adm_bucket_v2"
    assert row["raw_token_preserved"] is True
    assert row["adm_token_backfill_applied"] is True
    provenance = row.get("bucket_field_provenance")
    assert isinstance(provenance, dict)
    assert provenance["score_bucket"] == "adm_field"
    assert provenance["risk_context_bucket"] == "adm_field"


def test_scalp_entry_adm_falls_back_to_raw_when_adm_fields_missing(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "ai_confirmed",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": "78",
                    "action": "BUY",
                    "latest_strength": "150",
                    "quote_age_ms": "300",
                    "best_ask": "1000",
                    "trade_value_krw": "300000000",
                    "intraday_range_pct": "5.0",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    row = report["rows"][0]

    assert row["score_bucket"] == "score75_84"
    provenance = row.get("bucket_field_provenance")
    assert isinstance(provenance, dict)
    assert provenance["score_bucket"] == "raw_recomputed"


def test_scalp_entry_adm_uses_current_ai_score_as_score_source(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "ai_confirmed",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "current_ai_score": "66",
                    "action": "BUY",
                    "latest_strength": "120",
                    "quote_age_ms": "300",
                    "best_ask": "1000",
                    "trade_value_krw": "300000000",
                    "intraday_range_pct": "5.0",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    row = report["rows"][0]

    assert row["score_bucket"] == "score65_74"
    assert row["score_source_value"] == 66.0
    assert "score_bucket" not in report["summary"]["unknown_bucket_summary"]["dimension_counts"]


def test_scalp_entry_adm_unknown_bucket_summary_separates_unknown_from_not_available(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "chosen_action": "NO_BUY_AI",
                    "entry_adm_score_bucket": "score_unknown",
                    "entry_adm_risk_context_bucket": "neutral_strength_momentum",
                    "entry_adm_stale_bucket": "stale_not_available",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "entry_adm_overbought_bucket": "overbought_normal",
                    "entry_adm_bucket_token": "score_unknown|risk_unknown|-|stale_not_available|-|-|-|-",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    unknown_summary = report["summary"]["unknown_bucket_summary"]

    assert unknown_summary["affected_rows"] == 1
    assert unknown_summary["affected_rows"] <= unknown_summary["total_rows"]
    assert unknown_summary["not_available_affected_rows"] >= 0
    assert unknown_summary["not_available_affected_rows"] <= unknown_summary["total_rows"]
    assert unknown_summary["adm_source_bucket_used_count"] >= 1
    assert "adm_source_bucket_field_count" in unknown_summary
    assert "recomputed_unknown_count" in unknown_summary
    assert "unknown_dimension_occurrence_count" in unknown_summary
    assert "not_available_dimension_occurrence_count" in unknown_summary
    assert "not_available_dimension_counts" in unknown_summary
    assert unknown_summary["unknown_root_cause_counts"]["score_bucket:adm_field_unknown"] == 1
    assert unknown_summary["examples"][0]["bucket_token"].count("|") == 7


def test_scalp_entry_adm_unknown_bucket_summary_splits_context_root_causes():
    summary = mod._unknown_bucket_summary(
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "risk_context_bucket": "risk_unknown",
                "price_resolution_bucket": "quote_based",
                "score_bucket": "score65_74",
                "bucket_field_provenance": {"risk_context_bucket": "raw_recomputed"},
            },
            {
                "stage": "holding",
                "stock_code": "222222",
                "risk_context_bucket": "neutral_strength_momentum",
                "price_resolution_bucket": "price_unknown",
                "score_bucket": "score_not_available",
                "bucket_field_provenance": {"price_resolution_bucket": "raw_recomputed"},
            },
        ]
    )

    assert summary["unknown_root_cause_counts"]["risk_context_bucket:source_field_missing"] == 1
    assert summary["unknown_root_cause_counts"]["price_resolution_bucket:post_submit_or_exit_not_required"] == 1
    assert summary["unknown_root_cause_detail_counts"] == {
        "risk_context_bucket:source_field_missing": 1,
        "price_resolution_bucket:post_submit_or_exit_not_required": 1,
    }
    assert summary["unknown_resolution_route_counts"] == {
        "source_field_missing": 1,
        "post_submit_or_exit_not_required": 1,
    }
    assert summary["source_quality_gate"] == "source_quality_blocker"
    assert summary["recommended_route"] == "source_quality_workorder"
    assert summary["actionable_unknown_route_counts"] == {
        "risk_context_bucket:source_field_missing": 1,
    }
    assert not any("risk_context_source_missing" in key for key in summary["unknown_root_cause_counts"])
    assert not any("price_context_source_missing" in key for key in summary["unknown_root_cause_counts"])


def test_scalp_entry_adm_non_actionable_context_unknown_does_not_create_source_quality_workorder():
    summary = mod._unknown_bucket_summary(
        [
            {
                "stage": "holding",
                "stock_code": "222222",
                "risk_context_bucket": "risk_unknown",
                "price_resolution_bucket": "price_unknown",
                "score_bucket": "score_not_available",
                "bucket_field_provenance": {
                    "risk_context_bucket": "raw_recomputed",
                    "price_resolution_bucket": "raw_recomputed",
                },
            }
        ]
    )

    assert summary["affected_rows"] == 1
    assert summary["source_quality_gate"] == "classified_non_actionable"
    assert summary["recommended_route"] == "classified_not_applicable_no_workorder"
    assert summary["actionable_unknown_route_counts"] == {}
    assert summary["unknown_resolution_route_counts"] == {"post_submit_or_exit_not_required": 2}


def test_scalp_entry_adm_pre_submit_missing_context_is_not_available(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "source_stage": "latency_block",
                    "ai_score": 66,
                    "chosen_action": "SKIP_PRE_SUBMIT_SAFETY",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    row = report["rows"][0]
    unknown_summary = report["summary"]["unknown_bucket_summary"]

    assert row["stage"] == "scalp_entry_action_decision_snapshot"
    assert row["source_stage"] == "latency_block"
    assert row["risk_context_bucket"] == "risk_context_not_available"
    assert row["price_resolution_bucket"] == "price_not_available_pre_submit"
    assert "risk_context_bucket" not in unknown_summary["dimension_counts"]
    assert "price_resolution_bucket" not in unknown_summary["dimension_counts"]
    assert unknown_summary["not_available_dimension_counts"]["risk_context_bucket"] == 1
    assert unknown_summary["not_available_dimension_counts"]["price_resolution_bucket"] == 1


def test_scalp_entry_adm_post_entry_missing_score_is_not_available(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_sim_sell_order_assumed_filled",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T10:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "chosen_action": "WAIT_REQUOTE",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "entry_adm_risk_context_bucket": "neutral_strength_momentum",
                    "entry_adm_stale_bucket": "fresh",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "entry_adm_overbought_bucket": "overbought_normal",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    row = report["rows"][0]
    unknown_summary = report["summary"]["unknown_bucket_summary"]

    assert row["score_bucket"] == "score_not_available"
    assert "score_bucket" not in unknown_summary["dimension_counts"]
    assert unknown_summary["not_available_dimension_counts"]["score_bucket"] == 1
    assert unknown_summary["score_root_cause_counts"]["not_applicable"] == 1
    assert "unknown_bucket_source_quality_gap" not in report["warnings"]


def test_scalp_entry_adm_pre_submit_missing_score_backfills_from_nearby_entry_event(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": 66,
                    "chosen_action": "NO_BUY_AI",
                },
            },
            {
                "stage": "scalp_sim_pre_submit_liquidity_guard_would_block",
                "stock_code": "111111",
                "record_id": "R2",
                "emitted_at": "2026-05-18T09:10:30",
                "emitted_date": "2026-05-18",
                "fields": {
                    "source_stage": "entry_pre_submit",
                    "chosen_action": "SKIP_PRE_SUBMIT_SAFETY",
                    "entry_adm_risk_context_bucket": "neutral_strength_momentum",
                    "entry_adm_stale_bucket": "fresh",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "below_min_liquidity",
                    "entry_adm_overbought_bucket": "overbought_normal",
                },
            },
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    rows = {row["record_id"]: row for row in report["rows"]}
    row = rows["R2"]
    unknown_summary = report["summary"]["unknown_bucket_summary"]

    assert row["score_bucket"] == "score65_74"
    assert row["score_source_value"] == 66.0
    assert row["score_backfill_source"] == "prior_score_event"
    assert row["score_backfill_match_type"] == "prior_same_stock_time"
    assert row["bucket_field_provenance"]["score_bucket"] == "backfilled"
    assert "score_bucket" not in unknown_summary["dimension_counts"]
    assert unknown_summary["score_root_cause_counts"]["backfilled"] >= 1
    assert unknown_summary["score_backfill_match_type_counts"]["prior_same_stock_time"] >= 1


def test_scalp_entry_adm_score_backfill_does_not_use_future_event(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_sim_pre_submit_liquidity_guard_would_block",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "source_stage": "entry_pre_submit",
                    "chosen_action": "SKIP_PRE_SUBMIT_SAFETY",
                    "entry_adm_risk_context_bucket": "neutral_strength_momentum",
                    "entry_adm_stale_bucket": "fresh",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "below_min_liquidity",
                    "entry_adm_overbought_bucket": "overbought_normal",
                },
            },
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "record_id": "R2",
                "emitted_at": "2026-05-18T09:10:30",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": 66,
                    "chosen_action": "NO_BUY_AI",
                },
            },
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    rows = {row["record_id"]: row for row in report["rows"]}
    row = rows["R1"]
    unknown_summary = report["summary"]["unknown_bucket_summary"]

    assert row["score_bucket"] == "score_unknown"
    assert row.get("score_backfill_source") is None
    assert unknown_summary["unknown_root_cause_counts"]["score_bucket:source_score_missing"] == 1


def test_scalp_entry_adm_score_backfill_prefers_exact_key_over_nearer_stock_event(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "record_id": "NEAR",
                "emitted_at": "2026-05-18T09:10:10",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": 60,
                    "chosen_action": "NO_BUY_AI",
                },
            },
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "record_id": "SCORE",
                "emitted_at": "2026-05-18T09:09:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "candidate_id": "C1",
                    "ai_score": 72,
                    "chosen_action": "NO_BUY_AI",
                },
            },
            {
                "stage": "scalp_sim_pre_submit_liquidity_guard_would_block",
                "stock_code": "111111",
                "record_id": "TARGET",
                "emitted_at": "2026-05-18T09:10:30",
                "emitted_date": "2026-05-18",
                "fields": {
                    "candidate_id": "C1",
                    "source_stage": "entry_pre_submit",
                    "chosen_action": "SKIP_PRE_SUBMIT_SAFETY",
                    "entry_adm_risk_context_bucket": "neutral_strength_momentum",
                    "entry_adm_stale_bucket": "fresh",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "below_min_liquidity",
                    "entry_adm_overbought_bucket": "overbought_normal",
                },
            },
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    rows = {row["record_id"]: row for row in report["rows"]}
    row = rows["TARGET"]

    assert row["score_source_value"] == 72.0
    assert row["score_bucket"] == "score65_74"
    assert row["score_backfill_match_type"] == "exact_key"
    assert row["score_backfill_source_candidate_id"] == "C1"
    assert row["score_backfill_seconds_since_source"] == 90.0


def test_scalp_entry_adm_runtime_pre_submit_missing_context_is_not_available():
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "stage": "latency_block",
            "current_ai_score": 66,
        },
        now=datetime(2026, 5, 18, 9, 10),
        advisory_enabled=False,
    )
    fields = context["fields"]

    assert fields["entry_adm_risk_context_bucket"] == "risk_context_not_available"
    assert fields["entry_adm_price_resolution_bucket"] == "price_not_available_pre_submit"


def test_scalp_entry_adm_bucket_token_still_valid_with_adm_source_but_unknown_dimensions(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENT_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "threshold_cycle" / "snapshots")
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "chosen_action": "NO_BUY_AI",
                    "entry_adm_score_bucket": "score_unknown",
                    "entry_adm_risk_context_bucket": "weak_strength_momentum",
                    "entry_adm_stale_bucket": "fresh",
                    "entry_adm_price_resolution_bucket": "quote_based",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "entry_adm_overbought_bucket": "overbought_normal",
                    "entry_adm_bucket_token": "score_unknown|weak_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_0900_1000",
                },
            }
        ],
    )

    report = mod.build_scalp_entry_action_decision_matrix_report("2026-05-18")
    unknown_summary = report["summary"]["unknown_bucket_summary"]

    assert "unknown_bucket_source_quality_gap" in report["warnings"]
    assert unknown_summary["source_quality_gate"] == "source_quality_blocker"
    assert unknown_summary["affected_rows"] == 1


def test_scalp_entry_adm_hypothesis_force_requires_explicit_flag(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(
            runtime_mod.TRADING_RULES,
            SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True,
            SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED=True,
        ),
    )
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps({"date": "2026-05-18", "matrix_version": "scalp_entry_adm_v1_2026-05-18", "bucket_summary": []}),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 70,
            "buy_pressure": 35,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 19.0,
            "distance_from_day_high_pct": -0.3,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )

    merged = runtime_mod.merge_scalp_entry_adm_result_fields({"action": "BUY", "score": 78}, context)

    assert merged["action"] == "WAIT"
    assert merged["entry_adm_runtime_bias_applied"] is True
    assert merged["entry_adm_runtime_reason"] == "hypothesis_weak_momentum_chase_risk"


def test_adm_bucket_lookup_status_matched_prior_bucket():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    payload = {"bucket_summary": [{"bucket_token": "tk", "sample_count": 114, "joined_sample": 32}]}
    matched = {"bucket_token": "tk", "sample_count": 114, "joined_sample": 32}
    assert _bucket_lookup_status(payload, matched) == "matched_prior_bucket"


def test_adm_bucket_lookup_status_new_or_unseen_token():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    payload = {"bucket_summary": [{"bucket_token": "other"}]}
    assert _bucket_lookup_status(payload, {}) == "new_or_unseen_token_vs_prior_adm"


def test_adm_bucket_lookup_status_prior_bucket_missing_sample():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    payload = {"bucket_summary": [{"bucket_token": "tk", "sample_count": 0, "joined_sample": 0}]}
    matched = {"bucket_token": "tk", "sample_count": 0, "joined_sample": 0}
    assert _bucket_lookup_status(payload, matched) == "prior_bucket_present_but_runtime_sample_missing"


def test_adm_bucket_lookup_status_no_payload():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status
    assert _bucket_lookup_status({}, {}) == "bucket_lookup_not_performed"


def test_adm_lookup_none_is_classified_for_advisory_only_stage():
    from src.engine.scalp_entry_action_decision_matrix import _classify_adm_lookup_not_applicable

    rows = [
        {
            "stage": "ai_confirmed",
            "entry_adm_bucket_token": "score50_64|weak_strength_momentum|-|fresh",
            "entry_adm_bucket_token_recomputed": "score50_64|weak_strength_momentum|-|fresh",
            "entry_adm_bucket_lookup_status": "",
        },
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "entry_adm_bucket_token": "score65_74|weak_strength_momentum|-|fresh",
            "entry_adm_bucket_lookup_status": "",
        },
    ]

    _classify_adm_lookup_not_applicable(rows)

    assert rows[0]["entry_adm_bucket_lookup_status"] == "advisory_only_stage_without_prior_lookup"
    assert rows[0]["entry_adm_bucket_joined_sample"] == 0
    assert rows[1]["entry_adm_bucket_lookup_status"] == ""


def test_adm_lookup_closure_splits_new_bucket_and_producer_context_missing():
    from src.engine.scalp_entry_action_decision_matrix import _adm_lookup_closure_summary

    rows = [
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "entry_adm_bucket_lookup_status": "new_or_unseen_token_vs_prior_adm",
            "entry_adm_bucket_token_recomputed": "score70p|strong|-|fresh|quote_based|liquidity_high",
        },
        {
            "stage": "blocked_ai_score",
            "entry_adm_bucket_lookup_status": "new_or_unseen_token_vs_prior_adm",
            "entry_adm_bucket_token_recomputed": "score50_64|weak|-|fresh|price_not_available_pre_submit|liquidity_not_available",
        },
        {
            "stage": "ai_confirmed",
            "entry_adm_bucket_lookup_status": "new_or_unseen_token_vs_prior_adm",
            "entry_adm_bucket_token_recomputed": "score50_64|weak|-|fresh|quote_based|liquidity_mid",
        },
    ]

    summary = _adm_lookup_closure_summary(rows)

    assert summary["closure_status"] == "closed_with_producer_followup"
    assert summary["followup_required"] is True
    assert summary["status_counts"] == {
        "new_bucket_candidate_waiting_prior_rollup": 1,
        "producer_context_missing": 1,
        "advisory_or_not_applicable_stage": 1,
    }
    assert summary["producer_context_missing_counts"] == {
        "price_not_available_pre_submit": 1,
        "liquidity_not_available": 1,
    }
