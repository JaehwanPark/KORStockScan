import json

from src.engine.monitoring.intraday_entry_flow_report import (
    _default_event_cache_path,
    _default_output_paths,
    build_report,
    write_outputs,
)


def _event(code, name, stage, fields, emitted_at="2026-06-29T09:50:00"):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields,
        "emitted_at": emitted_at,
    }


def test_build_report_summarizes_flow_and_rising_blocker(tmp_path):
    event_path = tmp_path / "buy_funnel_sentinel_events_2026-06-29.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "상승",
                        "first_promoted_at": "2026-06-29T09:50:00",
                        "last_event_at": "2026-06-29T09:55:00",
                        "latest_price_delta_since_first_seen_pct": 3.0,
                        "max_price_delta_since_first_seen_pct": 3.0,
                        "real_submit_count": 0,
                        "latest_ai_score": 62,
                        "latest_ai_action": "WAIT",
                        "dominant_blocker": {
                            "stage": "scalping_scanner_watching_runtime_skip",
                            "reason": "scanner_fast_precheck_stability_pending",
                            "count": 3,
                        },
                    }
                ],
                "rising_missed_buy": [{"stock_code": "000001"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000001",
            "상승",
            "scalping_scanner_watching_runtime_skip",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "1.0",
                "skip_reason": "scanner_fast_precheck_stability_pending",
            },
        ),
        _event(
            "000001",
            "상승",
            "ai_confirmed",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "3.0",
                "ai_score": "62",
                "action": "WAIT",
                "quote_age_ms": "3500",
            },
            emitted_at="2026-06-29T09:55:00",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T09:50:00",
        generated_at="fixed",
    )

    assert report["summary"]["symbol_count"] == 1
    assert report["summary"]["rising_symbol_count_by_max_delta"] == 1
    assert report["rising_symbol_blocker_rollup"][0] == {
        "stage": "scalping_scanner_watching_runtime_skip",
        "reason": "scanner_fast_precheck_stability_pending",
        "count": 1,
    }
    assert report["rising_fresh_only_blocker_rollup"] == []
    assert report["rising_stale_mixed_blocker_rollup"][0] == {
        "stage": "scalping_scanner_watching_runtime_skip",
        "reason": "scanner_fast_precheck_stability_pending",
        "count": 1,
    }
    row = report["rows"][0]
    assert row["rise_after_watch"] == "rising"
    assert row["main_blocker_reason"] == "scanner_fast_precheck_stability_pending"
    assert row["stale_eval_count"] == 1
    assert row["dominant_stale_eval_stage"] == "ai_confirmed"
    assert report["summary"]["rising_stale_eval_symbol_count"] == 1
    assert "09:50:00 scalping_scanner_watching_runtime_skip" in row["flow"]


def test_write_outputs_surfaces_freshness_recheck_workorders(tmp_path):
    event_path = tmp_path / "buy_funnel_sentinel_events_2026-06-29.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "상승",
                        "first_promoted_at": "2026-06-29T09:50:00",
                        "last_event_at": "2026-06-29T09:55:00",
                        "latest_price_delta_since_first_seen_pct": 3.0,
                        "max_price_delta_since_first_seen_pct": 3.0,
                        "real_submit_count": 0,
                    }
                ],
                "rising_missed_buy": [{"stock_code": "000001"}],
                "source_quality_workorders": {
                    "rising_missed_freshness_recovery": [
                        {
                            "stock_code": "000001",
                            "stock_name": "상승",
                            "event_count": 3,
                            "diagnostic_quote_age_stale": 2,
                            "pre_ai_stale_or_history_gap": 1,
                            "latest_stage": "blocked_strength_momentum",
                            "latest_reason": "insufficient_history",
                            "next_action": "add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap",
                            "decision_authority": "source_quality_only",
                            "runtime_effect": "false",
                            "allowed_runtime_apply": "false",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000001",
            "상승",
            "blocked_strength_momentum",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "3.0",
                "reason": "insufficient_history",
                "quote_age_ms": "5200",
            },
            emitted_at="2026-06-29T09:55:00",
        )
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T09:50:00",
        generated_at="fixed",
    )
    output_md = tmp_path / "flow.md"
    output_csv = tmp_path / "flow.csv"
    write_outputs(report, output_md=output_md, output_csv=output_csv)

    assert report["freshness_recheck_workorders"][0]["stock_code"] == "000001"
    assert report["freshness_recheck_workorders"][0]["runtime_effect"] is False
    rendered = output_md.read_text(encoding="utf-8")
    assert "## bounded freshness recheck workorders" in rendered
    assert "effect=False,apply=False" in rendered
    assert "add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap" in rendered


def test_build_report_excludes_before_since_and_sim_rows(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(json.dumps({"summary": {}, "promoted_symbols": [], "rising_missed_buy": []}), encoding="utf-8")
    rows = [
        _event(
            "000001",
            "old",
            "blocked_strength_momentum",
            {"scanner_promotion_id": "old", "price_delta_since_first_seen_pct": "10"},
            emitted_at="2026-06-29T09:49:59",
        ),
        _event(
            "000002",
            "sim",
            "scalp_sim_buy_order_assumed_filled",
            {"scanner_promotion_id": "sim", "simulated_order": "True", "price_delta_since_first_seen_pct": "5"},
        ),
        _event(
            "000003",
            "new",
            "blocked_strength_momentum",
            {"scanner_promotion_id": "new", "price_delta_since_first_seen_pct": "0"},
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T09:50:00",
        generated_at="fixed",
    )

    assert [row["stock_code"] for row in report["rows"]] == ["000003"]
    assert report["summary"]["rising_symbol_count_by_max_delta"] == 0


def test_build_report_filters_diagnostic_promotions_before_since(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    event_path.write_text("", encoding="utf-8")
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "old",
                        "first_promoted_at": "2026-06-29T09:49:59",
                        "max_price_delta_since_first_seen_pct": 5,
                    },
                    {
                        "stock_code": "000002",
                        "stock_name": "new",
                        "first_promoted_at": "2026-06-29T09:50:00",
                        "max_price_delta_since_first_seen_pct": 1,
                    },
                ],
                "rising_missed_buy": [{"stock_code": "000001"}, {"stock_code": "000002"}],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T09:50:00",
        generated_at="fixed",
    )

    assert [row["stock_code"] for row in report["rows"]] == ["000002"]
    assert report["summary"]["rising_missed_symbol_count_in_report"] == 1


def test_build_report_keeps_promotions_active_after_since(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    event_path.write_text("", encoding="utf-8")
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "active",
                        "first_promoted_at": "2026-06-29T09:49:59",
                        "last_event_at": "2026-06-29T09:55:00",
                        "max_price_delta_since_first_seen_pct": 5,
                    },
                    {
                        "stock_code": "000002",
                        "stock_name": "old",
                        "first_promoted_at": "2026-06-29T09:40:00",
                        "last_event_at": "2026-06-29T09:49:59",
                        "max_price_delta_since_first_seen_pct": 1,
                    },
                ],
                "rising_missed_buy": [{"stock_code": "000001"}, {"stock_code": "000002"}],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T09:50:00",
        until="2026-06-29T10:00:00",
        generated_at="fixed",
    )

    assert [row["stock_code"] for row in report["rows"]] == ["000001"]
    assert report["rows"][0]["first_observed_at"] == "09:50:00"
    assert report["summary"]["rising_missed_symbol_count_in_report"] == 1


def test_default_event_cache_path_prefers_live_pipeline_events(tmp_path, monkeypatch):
    monkeypatch.setattr("src.engine.monitoring.intraday_entry_flow_report.PROJECT_ROOT", tmp_path)
    pipeline_path = tmp_path / "data" / "pipeline_events" / "pipeline_events_2026-06-29.jsonl"
    sentinel_path = (
        tmp_path
        / "data"
        / "runtime"
        / "sentinel_event_cache"
        / "buy_funnel_sentinel_events_2026-06-29.jsonl"
    )
    pipeline_path.parent.mkdir(parents=True)
    sentinel_path.parent.mkdir(parents=True)
    pipeline_path.write_text("", encoding="utf-8")
    sentinel_path.write_text("", encoding="utf-8")

    assert _default_event_cache_path("2026-06-29") == pipeline_path


def test_build_report_accepts_offset_aware_since_for_target_date(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "old",
                        "first_promoted_at": "2026-06-29T14:59:59+09:00",
                        "max_price_delta_since_first_seen_pct": 5,
                    },
                    {
                        "stock_code": "000002",
                        "stock_name": "new",
                        "first_promoted_at": "2026-06-29T15:00:00+09:00",
                        "max_price_delta_since_first_seen_pct": 1,
                    },
                ],
                "rising_missed_buy": [{"stock_code": "000001"}, {"stock_code": "000002"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000001",
            "old",
            "blocked_strength_momentum",
            {"scanner_promotion_id": "old", "price_delta_since_first_seen_pct": "5"},
            emitted_at="2026-06-29T14:59:59+09:00",
        ),
        _event(
            "000002",
            "new",
            "blocked_strength_momentum",
            {"scanner_promotion_id": "new", "price_delta_since_first_seen_pct": "1"},
            emitted_at="2026-06-29T15:00:00+09:00",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T15:00:00+09:00",
        generated_at="fixed",
    )

    assert [row["stock_code"] for row in report["rows"]] == ["000002"]
    assert report["summary"]["symbol_count"] == 1


def test_build_report_accepts_time_only_since_for_target_date(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "old",
                        "first_promoted_at": "2026-06-29T11:29:59",
                        "max_price_delta_since_first_seen_pct": 5,
                    },
                    {
                        "stock_code": "000002",
                        "stock_name": "new",
                        "first_promoted_at": "2026-06-29T11:30:00",
                        "max_price_delta_since_first_seen_pct": 1,
                    },
                ],
                "rising_missed_buy": [{"stock_code": "000001"}, {"stock_code": "000002"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000001",
            "old",
            "blocked_strength_momentum",
            {"scanner_promotion_id": "old", "price_delta_since_first_seen_pct": "5"},
            emitted_at="2026-06-29T11:29:59",
        ),
        _event(
            "000002",
            "new",
            "blocked_strength_momentum",
            {"scanner_promotion_id": "new", "price_delta_since_first_seen_pct": "1"},
            emitted_at="2026-06-29T11:30:00",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="11:30",
        generated_at="fixed",
    )

    assert [row["stock_code"] for row in report["rows"]] == ["000002"]
    assert report["summary"]["symbol_count"] == 1
    assert report["summary"]["rising_missed_symbol_count_in_report"] == 1


def test_write_outputs_uses_since_window_in_title(tmp_path):
    report = {
        "target_date": "2026-06-29",
        "generated_at": "fixed",
        "source_events": "events.jsonl",
        "source_diagnostic": "diag.json",
        "event_window": {"since": "2026-06-29T08:00:00"},
        "summary": {
            "symbol_count": 0,
            "rising_symbol_count_by_max_delta": 0,
            "rising_missed_buy_count_in_latest_diagnostic": 0,
            "rising_missed_symbol_count_in_report": 0,
            "real_submit_symbol_count_in_latest_diagnostic": 0,
            "buy_signal_or_pre_submit_pass_seen_symbols": 0,
            "stale_eval_symbol_count": 0,
            "rising_stale_eval_symbol_count": 0,
            "rising_fresh_only_symbol_count": 0,
        },
        "blocker_rollup": [],
        "rising_symbol_blocker_rollup": [],
        "rising_fresh_only_blocker_rollup": [],
        "rising_stale_mixed_blocker_rollup": [],
        "stale_eval_rollup": [],
        "stale_eval_category_rollup": [],
        "rows": [],
    }

    output_md = tmp_path / "flow.md"
    output_csv = tmp_path / "flow.csv"
    write_outputs(report, output_md=output_md, output_csv=output_csv)

    assert output_md.read_text(encoding="utf-8").splitlines()[0] == "# 2026-06-29 08:00 이후 감시대상 BUY 전 흐름"


def test_write_outputs_uses_time_only_since_window_in_title(tmp_path):
    report = {
        "target_date": "2026-06-29",
        "generated_at": "fixed",
        "source_events": "events.jsonl",
        "source_diagnostic": "diag.json",
        "event_window": {"since": "11:30"},
        "summary": {
            "symbol_count": 0,
            "rising_symbol_count_by_max_delta": 0,
            "rising_missed_buy_count_in_latest_diagnostic": 0,
            "rising_missed_symbol_count_in_report": 0,
            "real_submit_symbol_count_in_latest_diagnostic": 0,
            "buy_signal_or_pre_submit_pass_seen_symbols": 0,
            "stale_eval_symbol_count": 0,
            "rising_stale_eval_symbol_count": 0,
            "rising_fresh_only_symbol_count": 0,
        },
        "blocker_rollup": [],
        "rising_symbol_blocker_rollup": [],
        "rising_fresh_only_blocker_rollup": [],
        "rising_stale_mixed_blocker_rollup": [],
        "stale_eval_rollup": [],
        "stale_eval_category_rollup": [],
        "rows": [],
    }

    output_md = tmp_path / "flow.md"
    output_csv = tmp_path / "flow.csv"
    write_outputs(report, output_md=output_md, output_csv=output_csv)

    assert output_md.read_text(encoding="utf-8").splitlines()[0] == "# 2026-06-29 11:30 이후 감시대상 BUY 전 흐름"


def test_default_output_paths_accept_time_only_since_and_generated_at():
    output_md, output_csv = _default_output_paths("2026-06-29", "11:30", "13:18")

    assert output_md.name == "intraday_entry_flow_2026-06-29_current.md"
    assert output_md.parent.as_posix().endswith("data/report/intraday_entry_flow")
    assert output_csv.name == "intraday_entry_flow_2026-06-29_1130_to_1318.csv"
    assert output_csv.parent.as_posix() == "/tmp"


def test_build_report_separates_refresh_recovered_stale_from_hard_stale(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000001",
                        "stock_name": "refresh",
                        "first_promoted_at": "2026-06-29T11:30:00",
                        "max_price_delta_since_first_seen_pct": 2.0,
                    },
                    {
                        "stock_code": "000002",
                        "stock_name": "hard",
                        "first_promoted_at": "2026-06-29T11:30:00",
                        "max_price_delta_since_first_seen_pct": 1.0,
                    },
                ],
                "rising_missed_buy": [{"stock_code": "000001"}, {"stock_code": "000002"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000001",
            "refresh",
            "ai_confirmed",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "2.0",
                "quote_age_ms": "6500",
                "pre_ai_ws_snapshot_refresh_applied": True,
                "pre_ai_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                "pre_ai_ws_snapshot_refresh_age_ms": "110",
            },
            emitted_at="2026-06-29T11:31:00",
        ),
        _event(
            "000001",
            "refresh",
            "blocked_strength_momentum",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "2.0",
                "quote_age_ms": "6400",
                "refresh_applied": True,
                "refresh_reason": "latest_ws_snapshot_fresh",
                "refresh_age_ms": "90",
            },
            emitted_at="2026-06-29T11:31:10",
        ),
        _event(
            "000002",
            "hard",
            "entry_submit_revalidation_warning",
            {
                "scanner_promotion_id": "p2",
                "price_delta_since_first_seen_pct": "1.0",
                "quote_age_at_submit_ms": "7000",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
            },
            emitted_at="2026-06-29T11:32:00",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-29",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-29T11:30:00",
        generated_at="fixed",
    )

    by_code = {row["stock_code"]: row for row in report["rows"]}
    assert by_code["000001"]["stale_eval_count"] == 0
    assert by_code["000001"]["stale_refresh_recovered_count"] == 2
    assert by_code["000002"]["stale_eval_count"] == 1
    assert by_code["000002"]["dominant_stale_eval_category"] == "pre_submit_stale_context_or_quote"
    assert report["summary"]["stale_eval_symbol_count"] == 1
    assert report["summary"]["rising_fresh_only_symbol_count"] == 1
    assert report["summary"]["stale_refresh_recovered_symbol_count"] == 1
    assert report["rising_fresh_only_blocker_rollup"][0] == {
        "stage": "ai_confirmed",
        "reason": "-",
        "count": 1,
    }
    assert report["rising_stale_mixed_blocker_rollup"][0] == {
        "stage": "entry_submit_revalidation_warning",
        "reason": "stale_context_or_quote",
        "count": 1,
    }
    assert report["stale_eval_category_rollup"][0] == {
        "category": "pre_submit_stale_context_or_quote",
        "count": 1,
    }


def test_build_report_excludes_rising_missed_one_share_forced_submit_from_flow_submit_count(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000777",
                        "stock_name": "강제1주",
                        "first_promoted_at": "2026-06-30T09:10:00",
                        "last_event_at": "2026-06-30T09:12:00",
                        "max_price_delta_since_first_seen_pct": 1.2,
                        "latest_price_delta_since_first_seen_pct": 1.2,
                        "real_submit_count": 0,
                    }
                ],
                "rising_missed_buy": [{"stock_code": "000777"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000777",
            "강제1주",
            "broker_buy_submit",
            {
                "scanner_promotion_id": "p1",
                "actual_order_submitted": "true",
                "price_delta_since_first_seen_pct": "1.2",
                "rising_missed_one_share_entry_forced": "true",
                "forced_entry_qty": "1",
                "forced_entry_reason": "rising_missed_one_share_entry",
            },
            emitted_at="2026-06-30T09:11:00",
        )
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T09:00:00",
        generated_at="fixed",
    )

    row = report["rows"][0]
    assert row["stock_code"] == "000777"
    assert row["actual_submit_count"] == 0
    assert report["summary"]["real_submit_symbol_count_in_latest_diagnostic"] == 0
    assert report["summary"]["rising_missed_symbol_count_in_report"] == 1
    assert report["summary"]["rising_missed_forced_scout_event_count"] == 1
    assert report["summary"]["rising_missed_forced_scout_symbol_count"] == 1
    assert report["summary"]["rising_missed_forced_scout_residual_symbol_count"] == 1
    assert report["summary"]["rising_missed_residual_excluding_forced_scout_symbol_count"] == 0
    assert report["forced_scout_observation"] == {
        "event_count": 1,
        "symbol_count": 1,
        "symbols": ["000777"],
        "rising_missed_residual_symbols": ["000777"],
        "rising_missed_residual_excluding_forced_scout_symbols": [],
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
    }


def test_build_report_excludes_non_actionable_rising_missed_class_from_residual(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "486990",
                        "stock_name": "노타",
                        "first_promoted_at": "2026-06-30T12:00:00",
                        "last_event_at": "2026-06-30T12:15:00",
                        "max_price_delta_since_first_seen_pct": 3.48,
                        "latest_price_delta_since_first_seen_pct": 3.48,
                        "real_submit_count": 0,
                    }
                ],
                "rising_missed_buy": [
                    {
                        "stock_code": "486990",
                        "rising_missed_class": "intended_guard_preserved",
                        "rising_missed_one_share_eligible": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "486990",
            "노타",
            "same_symbol_loss_reentry_cooldown",
            {"scanner_promotion_id": "p1", "price_delta_since_first_seen_pct": "3.48"},
            emitted_at="2026-06-30T12:11:42",
        )
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T12:00:00",
        generated_at="fixed",
    )

    assert report["summary"]["rising_missed_buy_count_in_latest_diagnostic"] == 1
    assert report["summary"]["rising_missed_symbol_count_in_report"] == 1
    assert report["summary"]["rising_missed_residual_excluding_forced_scout_symbol_count"] == 0
    assert report["forced_scout_observation"]["rising_missed_residual_excluding_forced_scout_symbols"] == []


def test_build_report_excludes_prior_forced_scout_symbol_from_window_residual(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "001260",
                        "stock_name": "남광토건",
                        "first_promoted_at": "2026-06-30T11:50:00",
                        "last_event_at": "2026-06-30T12:20:00",
                        "max_price_delta_since_first_seen_pct": 5.11,
                        "latest_price_delta_since_first_seen_pct": 5.11,
                        "real_submit_count": 0,
                    }
                ],
                "rising_missed_buy": [
                    {
                        "stock_code": "001260",
                        "rising_missed_class": "rising_missed_raw",
                        "rising_missed_one_share_eligible": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "001260",
            "남광토건",
            "rising_missed_one_share_entry",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "5.11",
                "forced_entry_reason": "rising_missed_one_share_entry",
                "forced_entry_qty": "1",
            },
            emitted_at="2026-06-30T11:57:42",
        ),
        _event(
            "001260",
            "남광토건",
            "scalping_scanner_promotion_latency_trace",
            {"scanner_promotion_id": "p1", "price_delta_since_first_seen_pct": "5.11"},
            emitted_at="2026-06-30T12:19:39",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T12:00:00",
        generated_at="fixed",
    )

    assert report["summary"]["rising_missed_forced_scout_event_count"] == 0
    assert report["summary"]["rising_missed_forced_scout_symbol_count"] == 1
    assert report["summary"]["rising_missed_forced_scout_residual_symbol_count"] == 1
    assert report["summary"]["rising_missed_residual_excluding_forced_scout_symbol_count"] == 0
    assert report["forced_scout_observation"]["symbols"] == ["001260"]
    assert report["forced_scout_observation"]["rising_missed_residual_symbols"] == ["001260"]
    assert report["forced_scout_observation"]["rising_missed_residual_excluding_forced_scout_symbols"] == []


def test_build_report_excludes_unflagged_submit_after_forced_scout_from_flow_submit_count(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "240810",
                        "stock_name": "원익IPS",
                        "first_promoted_at": "2026-06-30T11:04:00",
                        "last_event_at": "2026-06-30T11:06:00",
                        "max_price_delta_since_first_seen_pct": 0.55,
                        "latest_price_delta_since_first_seen_pct": 0.55,
                        "real_submit_count": 0,
                    }
                ],
                "rising_missed_buy": [{"stock_code": "240810"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "240810",
            "원익IPS",
            "budget_pass",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "0.55",
                "order_quantity": "1",
                "forced_entry_reason": "rising_missed_one_share_entry",
                "rising_missed_one_share_entry_forced": "true",
            },
            emitted_at="2026-06-30T11:04:10",
        ),
        _event(
            "240810",
            "원익IPS",
            "latency_pass",
            {
                "scanner_promotion_id": "p1",
                "actual_order_submitted": "False",
                "price_delta_since_first_seen_pct": "0.55",
                "reason": "safe_normal_entry_allowed",
            },
            emitted_at="2026-06-30T11:04:16",
        ),
        _event(
            "240810",
            "원익IPS",
            "order_bundle_submitted",
            {
                "scanner_promotion_id": "p1",
                "actual_order_submitted": "true",
                "price_delta_since_first_seen_pct": "0.55",
            },
            emitted_at="2026-06-30T11:04:20",
        ),
        _event(
            "240810",
            "원익IPS",
            "blocked_strength_momentum",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "0.55",
                "reason": "below_buy_ratio",
            },
            emitted_at="2026-06-30T11:06:00",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T11:00:00",
        generated_at="fixed",
    )

    row = report["rows"][0]
    assert row["stock_code"] == "240810"
    assert row["actual_submit_count"] == 0
    assert row["buy_signal_seen"] is False
    assert report["summary"]["rising_missed_forced_scout_event_count"] == 1
    assert report["summary"]["rising_missed_forced_scout_residual_symbol_count"] == 1


def test_build_report_summarizes_latency_danger_root_cause(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000500",
                        "stock_name": "가온전선",
                        "first_promoted_at": "2026-06-30T11:17:00",
                        "last_event_at": "2026-06-30T11:19:00",
                        "max_price_delta_since_first_seen_pct": 20.44,
                        "dominant_actionable_blocker": {
                            "stage": "latency_block",
                            "reason": "latency_state_danger",
                            "count": 2,
                            "class": "pre_submit_quality_guard",
                        },
                    }
                ],
                "rising_missed_buy": [{"stock_code": "000500"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000500",
            "가온전선",
            "latency_block",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "20.44",
                "reason": "latency_state_danger",
                "spread_ratio": "0.0111",
                "ws_age_ms": "35",
                "orderbook_micro_spread_ticks": "5",
                "orderbook_micro_state": "neutral",
                "orderbook_micro_ofi_bucket_key": "spread=wide|price=high|depth=normal|sample=rich",
            },
            emitted_at="2026-06-30T11:17:44",
        ),
        _event(
            "000500",
            "가온전선",
            "latency_block",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "20.44",
                "reason": "latency_state_danger",
                "spread_ratio": "0.0113",
                "ws_age_ms": "81",
                "orderbook_micro_spread_ticks": "5",
                "orderbook_micro_state": "neutral",
                "orderbook_micro_ofi_bucket_key": "spread=wide|price=high|depth=normal|sample=rich",
            },
            emitted_at="2026-06-30T11:18:58",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T11:00:00",
        generated_at="fixed",
    )

    root = report["latency_danger_root_cause"][0]
    assert root["stock_code"] == "000500"
    assert root["event_count"] == 2
    assert root["top_cause"] == "spread_too_wide"
    assert root["spread_ratio"] == {"min": 0.0111, "median": 0.0112, "max": 0.0113}
    assert root["ws_age_ms"] == {"min": 35.0, "median": 58.0, "max": 81.0}
    assert root["top_ofi_bucket"] == "spread=wide|price=high|depth=normal|sample=rich"


def test_build_report_marks_wide_microstructure_latency_cause_below_ratio_cap(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "475150",
                        "stock_name": "SK이터닉스",
                        "first_promoted_at": "2026-06-30T11:21:00",
                        "max_price_delta_since_first_seen_pct": 4.06,
                    }
                ],
                "rising_missed_buy": [{"stock_code": "475150"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "475150",
            "SK이터닉스",
            "latency_block",
            {
                "scanner_promotion_id": "p1",
                "price_delta_since_first_seen_pct": "4.06",
                "reason": "latency_state_danger",
                "spread_ratio": "0.0096",
                "ws_age_ms": "81",
                "orderbook_micro_spread_ticks": "5",
                "orderbook_micro_state": "neutral",
                "orderbook_micro_ofi_bucket_key": "spread=wide|price=high|depth=thick|sample=rich",
            },
            emitted_at="2026-06-30T11:21:09",
        ),
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T11:00:00",
        generated_at="fixed",
    )

    root = report["latency_danger_root_cause"][0]
    assert root["top_cause"] == "spread_microstructure_wide"
    assert root["spread_ratio"] == {"min": 0.0096, "median": 0.0096, "max": 0.0096}


def test_build_report_uses_diagnostic_latency_root_cause_when_event_cache_missing(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    event_path.write_text("", encoding="utf-8")
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "033100",
                        "stock_name": "제룡전기",
                        "first_promoted_at": "2026-06-30T08:01:00",
                        "max_price_delta_since_first_seen_pct": 5.25,
                        "dominant_actionable_blocker": {
                            "stage": "latency_block",
                            "reason": "latency_state_danger",
                            "count": 3,
                            "class": "pre_submit_quality_guard",
                        },
                        "latency_danger_root_cause": {
                            "event_count": 3,
                            "top_cause": "quote_stale",
                            "cause_counts": [{"cause": "quote_stale", "count": 2}, {"cause": "spread_too_wide", "count": 1}],
                            "spread_ratio": {"min": 0.001, "median": 0.007, "max": 0.012},
                            "ws_age_ms": {"min": 121.0, "median": 764.0, "max": 1085.0},
                            "spread_ticks": {"min": 1.0, "median": 6.0, "max": 7.0},
                            "top_micro_state": "neutral",
                            "top_ofi_bucket": "spread=wide|price=mid|depth=normal|sample=rich",
                        },
                    }
                ],
                "rising_missed_buy": [{"stock_code": "033100"}],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T11:00:00",
        generated_at="fixed",
    )

    root = report["latency_danger_root_cause"][0]
    assert root["stock_code"] == "033100"
    assert root["event_count"] == 3
    assert root["top_cause"] == "quote_stale"
    assert root["top_ofi_bucket"] == "spread=wide|price=mid|depth=normal|sample=rich"


def test_build_report_marks_diagnostic_only_latency_provenance_gap(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    event_path.write_text("", encoding="utf-8")
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "033100",
                        "stock_name": "제룡전기",
                        "first_promoted_at": "2026-06-30T08:01:00",
                        "max_price_delta_since_first_seen_pct": 5.25,
                        "dominant_actionable_blocker": {
                            "stage": "latency_block",
                            "reason": "latency_state_danger",
                            "count": 34,
                            "class": "pre_submit_quality_guard",
                        },
                    }
                ],
                "rising_missed_buy": [{"stock_code": "033100"}],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T11:00:00",
        generated_at="fixed",
    )

    root = report["latency_danger_root_cause"][0]
    assert root["stock_code"] == "033100"
    assert root["event_count"] == 34
    assert root["top_cause"] == "latency_provenance_gap"
    assert root["top_ofi_bucket"] == "diagnostic_latency_without_source_event_fields"


def test_build_report_until_excludes_later_event_cache_submit(tmp_path):
    event_path = tmp_path / "events.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    diagnostic_path.write_text(
        json.dumps(
            {
                "summary": {"real_submit_symbol_count": 0},
                "promoted_symbols": [
                    {
                        "stock_code": "000888",
                        "stock_name": "상한필터",
                        "first_promoted_at": "2026-06-30T09:59:00",
                        "max_price_delta_since_first_seen_pct": 1.0,
                        "real_submit_count": 0,
                    }
                ],
                "rising_missed_buy": [{"stock_code": "000888"}],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _event(
            "000888",
            "상한필터",
            "broker_buy_submit",
            {
                "scanner_promotion_id": "p1",
                "actual_order_submitted": "true",
                "price_delta_since_first_seen_pct": "1.0",
            },
            emitted_at="2026-06-30T10:00:01",
        )
    ]
    event_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-30",
        event_cache_path=event_path,
        diagnostic_path=diagnostic_path,
        since="2026-06-30T08:00:00",
        until="2026-06-30T10:00:00",
        generated_at="fixed",
    )

    row = report["rows"][0]
    assert row["actual_submit_count"] == 0
    assert report["event_window"]["until"] == "2026-06-30T10:00:00"
