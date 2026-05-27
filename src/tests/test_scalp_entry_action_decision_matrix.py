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
    assert counts["BUY_DEFENSIVE"] == 1
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


def test_scalp_entry_adm_runtime_context_adds_prompt_and_cache_token(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    bucket_token = "score75_84|strong_strength_momentum|fresh|quote_based|liquidity_high|overbought_normal|time_outside_regular"
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
    bucket_token = "score75_84|strong_strength_momentum|fresh|quote_based|liquidity_high|overbought_normal|time_outside_regular"
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


def test_scalp_entry_adm_bucket_sample_floor_blocks_force_wait(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    bucket_token = "score75_84|strong_strength_momentum|fresh|quote_based|liquidity_high|overbought_normal|time_outside_regular"
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
