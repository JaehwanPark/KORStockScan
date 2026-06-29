import json

from src.engine.monitoring.intraday_entry_flow_report import _default_output_paths, build_report, write_outputs


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

    assert output_md.name == "intraday_entry_flow_2026-06-29_1130_to_1318.md"
    assert output_csv.name == "intraday_entry_flow_2026-06-29_1130_to_1318.csv"


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
