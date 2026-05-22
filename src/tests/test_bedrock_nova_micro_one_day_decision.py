import json

from src.tests import bedrock_nova_micro_one_day_decision as mod


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def test_one_day_decision_joins_future_rows_and_computes_entry_ev(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "analyze_target",
                "source_event_stage": "watching_analyze_target",
                "record_id": "R1",
                "symbol": "테스트",
                "openai_action": "WAIT",
                "openai_score": 62,
                "nova_action": "BUY",
                "nova_score": 95,
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
                "profit_rate": 1.25,
                "outcome": "GOOD_EXIT",
                "metrics_10m": {"close_ret_pct": 0.5, "mfe_pct": 0.8, "mae_pct": -0.2},
            }
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")

    entry = report["scope_results"]["entry_watch_buy"]
    assert entry["unique_valid_join_rows"] == 1
    assert entry["openai_source_quality_adjusted_ev_pct"] == 0.0
    assert entry["nova_micro_source_quality_adjusted_ev_pct"] == 1.25
    assert report["winner"] == "nova_micro"
    assert report["winning_profile"] == "entry_watch_buy_nova_micro_v1"


def test_one_day_decision_excludes_prior_rows_and_dedupes_sim_id(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "analyze_target",
                "source_event_stage": "watching_analyze_target",
                "record_id": "PRIOR",
                "openai_action": "WAIT",
                "nova_action": "BUY",
            },
            {
                "parse_ok": True,
                "created_at": "2026-05-22T11:00:00+09:00",
                "endpoint_name": "analyze_target",
                "source_event_stage": "watching_analyze_target",
                "record_id": "DUP",
                "openai_action": "WAIT",
                "nova_action": "BUY",
            },
            {
                "parse_ok": True,
                "created_at": "2026-05-22T11:01:00+09:00",
                "endpoint_name": "analyze_target",
                "source_event_stage": "watching_analyze_target",
                "record_id": "DUP",
                "openai_action": "WAIT",
                "nova_action": "BUY",
            },
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [
            {"sim_record_id": "SIM-OLD", "sim_parent_record_id": "PRIOR", "sell_time": "09:59:00", "profit_rate": 9.0},
            {"sim_record_id": "SIM-DUP", "sim_parent_record_id": "DUP", "sell_time": "11:30:00", "profit_rate": 0.5},
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")
    entry = report["scope_results"]["entry_watch_buy"]

    assert entry["prior_only_excluded_count"] == 1
    assert entry["valid_join_rows"] == 1
    assert entry["unique_valid_join_rows"] == 1
    assert entry["nova_micro_source_quality_adjusted_ev_pct"] == 0.5


def test_one_day_decision_tie_breakers_never_defer(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "analyze_target",
                "source_event_stage": "watching_analyze_target",
                "record_id": "R1",
                "openai_action": "WAIT",
                "nova_action": "BUY",
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
                "profit_rate": 0.0,
                "metrics_10m": {"mae_pct": -1.0, "close_ret_pct": 0.0},
            }
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")

    assert report["winner"] in {"openai", "nova_micro"}
    assert report["winner"] == "openai"
    assert report["winner_reason"] == "entry_tie_breaker_lower_mae_exposure"
    assert report["no_defer_policy"] is True


def test_one_day_decision_no_sample_still_selects_winner(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(shadow, [])
    _write_jsonl(post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl", [])
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")

    assert report["winner"] == "openai"
    assert report["winning_profile"] == "openai_baseline"
    assert report["winner_reason"] == "no_valid_samples_final_tie_breaker_openai_baseline"


def test_one_day_decision_weak_join_is_reference_only(tmp_path, monkeypatch):
    shadow = tmp_path / "shadow.jsonl"
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    _write_jsonl(
        shadow,
        [
            {
                "parse_ok": True,
                "created_at": "2026-05-22T10:00:00+09:00",
                "endpoint_name": "analyze_target",
                "source_event_stage": "watching_analyze_target",
                "symbol": "약한매칭",
                "openai_action": "WAIT",
                "nova_action": "BUY",
            }
        ],
    )
    _write_jsonl(
        post_sell / "sim_post_sell_evaluations_2026-05-22.jsonl",
        [
            {
                "sim_record_id": "SIM-WEAK",
                "stock_name": "약한매칭",
                "sell_time": "10:30:00",
                "profit_rate": 5.0,
                "outcome": "GOOD_EXIT",
            }
        ],
    )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22")
    entry = report["scope_results"]["entry_watch_buy"]

    assert entry["weak_reference_count"] == 1
    assert entry["unique_valid_join_rows"] == 0
    assert entry["nova_micro_source_quality_adjusted_ev_pct"] == 0.0
    assert report["winner"] == "openai"


def test_cumulative_decision_merges_daily_exact_join_scopes(tmp_path, monkeypatch):
    post_sell = tmp_path / "post_sell"
    post_sell.mkdir()
    shadow_by_date = {}
    for day, record_id, profit in [
        ("2026-05-21", "R1", 1.0),
        ("2026-05-22", "R2", -3.0),
    ]:
        shadow = tmp_path / f"shadow_{day}.jsonl"
        shadow_by_date[day] = shadow
        _write_jsonl(
            shadow,
            [
                {
                    "parse_ok": True,
                    "created_at": f"{day}T10:00:00+09:00",
                    "endpoint_name": "analyze_target",
                    "source_event_stage": "watching_analyze_target",
                    "record_id": record_id,
                    "openai_action": "WAIT",
                    "nova_action": "BUY",
                }
            ],
        )
        _write_jsonl(
            post_sell / f"sim_post_sell_evaluations_{day}.jsonl",
            [
                {
                    "sim_record_id": f"SIM-{record_id}",
                    "sim_parent_record_id": record_id,
                    "sell_time": "10:30:00",
                    "profit_rate": profit,
                }
            ],
        )
    monkeypatch.setattr(mod, "shadow_jsonl_path", lambda target_date: shadow_by_date[target_date])
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell)

    report = mod.build_decision("2026-05-22", start_date="2026-05-21")
    entry = report["scope_results"]["entry_watch_buy"]

    assert report["window_policy"] == "cumulative"
    assert report["source_dates"] == ["2026-05-21", "2026-05-22"]
    assert entry["unique_valid_join_rows"] == 2
    assert entry["nova_micro_source_quality_adjusted_ev_pct"] == -1.0
