import json

from src.tests import bedrock_nova_lite_one_day_decision as mod


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_lite_one_day_holding_flow_future_join_and_within_1pct_routes_lite(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "holding_flow",
                "source_event_stage": "holding_flow",
                "record_id": "R1",
                "openai_model": "gpt-5.4-mini",
                "openai_action": "HOLD",
                "nova_action": "TRIM",
            }
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [
            {
                "sim_record_id": "SIM-1",
                "sim_parent_record_id": "R1",
                "sell_time": "10:20:00",
                "profit_rate": -1.0,
                "metrics_10m": {"close_ret_pct": 0.6, "mfe_pct": 0.7, "mae_pct": -0.3},
            }
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")
    holding = report["profile_results"]["holding_flow"]

    assert holding["unique_valid_join_rows"] == 1
    assert holding["openai_source_quality_adjusted_ev_pct"] == 0.6
    assert holding["lite_source_quality_adjusted_ev_pct"] == 0.0
    assert report["winner"] == "lite"
    assert report["route_candidate"] == "tier2_nova_lite_v1"
    assert report["route_candidate_created"] is True


def test_lite_one_day_entry_price_defensive_bucket_is_included(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "entry_price",
                "source_event_stage": "entry_price",
                "sim_record_id": "SIM-1",
                "openai_model": "gpt-5.4-mini",
                "openai_action": "USE_DEFENSIVE",
                "nova_action": "USE_DEFENSIVE",
            }
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [
            {
                "sim_record_id": "SIM-1",
                "sell_time": "10:10:00",
                "profit_rate": -0.4,
                "metrics_10m": {"close_ret_pct": -0.2},
            }
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")
    row = report["profile_results"]["entry_price"]["sample_rows"][0]

    assert row["entry_price_bucket"] == "entry_price_defensive"
    assert row["action_pair_bucket"] == "USE_DEFENSIVE->USE_DEFENSIVE"
    assert report["overall"]["unique_valid_join_rows"] == 1
    assert report["winner"] == "lite"


def test_lite_one_day_excludes_prior_rows_and_dedupes_sim_id(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "holding_flow",
                "record_id": "PRIOR",
                "openai_action": "HOLD",
                "nova_action": "HOLD",
            },
            {
                "parse_ok": True,
                "created_at": "2026-05-22T11:00:00+09:00",
                "endpoint_name": "holding_flow",
                "record_id": "DUP",
                "openai_action": "HOLD",
                "nova_action": "HOLD",
            },
            {
                "parse_ok": True,
                "created_at": "2026-05-22T11:01:00+09:00",
                "endpoint_name": "holding_flow",
                "record_id": "DUP",
                "openai_action": "HOLD",
                "nova_action": "HOLD",
            },
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [
            {"sim_record_id": "SIM-OLD", "sim_parent_record_id": "PRIOR", "sell_time": "09:59:00", "profit_rate": 2.0},
            {
                "sim_record_id": "SIM-DUP",
                "sim_parent_record_id": "DUP",
                "sell_time": "11:30:00",
                "profit_rate": 0.5,
                "metrics_10m": {"close_ret_pct": 0.5},
            },
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")
    holding = report["profile_results"]["holding_flow"]

    assert holding["prior_only_excluded_count"] == 1
    assert holding["valid_join_rows"] == 1
    assert holding["unique_valid_join_rows"] == 1


def test_lite_one_day_weak_join_is_reference_only(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "holding_flow",
                "symbol": "약한매칭",
                "openai_action": "HOLD",
                "nova_action": "TRIM",
            }
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [{"sim_record_id": "SIM-WEAK", "stock_name": "약한매칭", "sell_time": "10:30:00", "profit_rate": 5.0}],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")
    holding = report["profile_results"]["holding_flow"]

    assert holding["weak_reference_count"] == 1
    assert holding["unique_valid_join_rows"] == 0
    assert report["status"] == "fail_primary_metric_join_contract"
    assert report["route_candidate_created"] is False


def test_lite_one_day_profile_underperformance_blocks_tier2_route(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "holding_flow",
                "record_id": "R1",
                "openai_action": "HOLD",
                "nova_action": "TRIM",
            }
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [
            {
                "sim_record_id": "SIM-1",
                "sim_parent_record_id": "R1",
                "sell_time": "10:30:00",
                "profit_rate": 1.0,
                "metrics_10m": {"close_ret_pct": 2.2},
            }
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")

    assert report["winner"] == "openai"
    assert report["route_candidate_created"] is False
    assert report["profile_results"]["holding_flow"]["lite_profile_underperformance_blocker"] is True


def test_lite_one_day_no_valid_sample_does_not_route_lite(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(shadow, [])
    _write_jsonl(post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl", [])
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")

    assert report["status"] == "fail_primary_metric_join_contract"
    assert report["winner"] == "openai"
    assert report["route_candidate_created"] is False
    assert report["next_action"] == "fail_primary_metric_join_contract"
