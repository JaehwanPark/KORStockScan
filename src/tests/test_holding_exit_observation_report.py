import gzip
import json

from src.engine import holding_exit_observation_report as report_mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_gzip_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _trade(
    trade_id,
    *,
    code="111111",
    name="테스트",
    rec_date="2026-04-24",
    buy_time="2026-04-24 09:30:00",
    sell_time="2026-04-24 09:40:00",
    profit_rate=0.5,
    realized_pnl_krw=1000,
    entry_mode="normal",
    fill_quality="FULL_FILL",
    exit_rule="scalp_trailing_take_profit",
    scale_in=False,
    status="COMPLETED",
):
    timeline = [
        {
            "stage": "position_rebased_after_fill",
            "fields": {
                "id": str(trade_id),
                "fill_quality": fill_quality,
                "add_count": "0",
            },
        },
        {
            "stage": "exit_signal",
            "fields": {
                "exit_rule": exit_rule,
                "profit_rate": str(profit_rate) if profit_rate is not None else "",
            },
        },
    ]
    if scale_in:
        timeline.insert(
            1,
            {
                "stage": "scale_in_executed",
                "fields": {
                    "id": str(trade_id),
                    "add_count": "1",
                    "new_buy_qty": "2",
                },
            },
        )
    return {
        "id": trade_id,
        "rec_date": rec_date,
        "code": code,
        "name": name,
        "status": status,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10000,
        "buy_qty": 1,
        "buy_time": buy_time,
        "sell_price": 10100,
        "sell_time": sell_time,
        "completion_day_basis": "terminal_event",
        "profit_rate": profit_rate,
        "realized_pnl_krw": realized_pnl_krw,
        "entry_mode": entry_mode,
        "timeline": timeline,
    }


def _post_sell_row(
    post_sell_id,
    recommendation_id,
    *,
    exit_rule,
    outcome,
    profit_rate=0.6,
    rebound_buy=False,
):
    candidate = {
        "post_sell_id": post_sell_id,
        "signal_date": "2026-04-24",
        "recommendation_id": recommendation_id,
        "sell_time": "10:00:00",
        "stock_code": "111111",
        "stock_name": "테스트",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10000,
        "sell_price": 10100,
        "profit_rate": profit_rate,
        "buy_qty": 1,
        "exit_rule": exit_rule,
        "same_symbol_soft_stop_cooldown_would_block": True,
    }
    evaluation = {
        **candidate,
        "outcome": outcome,
        "metrics_1m": {"rebound_above_sell": True, "rebound_above_buy": rebound_buy},
        "metrics_3m": {"rebound_above_sell": True, "rebound_above_buy": rebound_buy},
        "metrics_5m": {"rebound_above_sell": True, "rebound_above_buy": rebound_buy},
        "metrics_10m": {
            "mfe_pct": 2.0,
            "mae_pct": -0.3,
            "close_ret_pct": 0.8,
            "rebound_above_sell": True,
            "rebound_above_buy": rebound_buy,
        },
    }
    return candidate, evaluation


def test_full_completed_projection_is_not_capped_by_recent_trades():
    full = [_trade(index) for index in range(1, 13)]
    snapshot = {
        "date": "2026-09-23",
        "meta": {"sell_completed_event_ids": list(range(1, 13))},
        "metrics": {"canonical_completed_trades": 12, "completed_trades": 12},
        "sections": {
            "recent_trades": full[:10],
            "completed_trade_projection": full,
        },
    }

    rows, gaps = report_mod._collect_completed_trade_rows([snapshot])

    assert gaps == []
    assert {row["id"] for row in rows} == set(range(1, 13))


def test_completed_projection_rejects_terminal_event_id_mismatch():
    snapshot = {
        "date": "2026-09-23",
        "meta": {"sell_completed_event_ids": [1, 2]},
        "metrics": {"canonical_completed_trades": 1},
        "sections": {"completed_trade_projection": [_trade(1)]},
    }

    rows, gaps = report_mod._collect_completed_trade_rows([snapshot])

    assert rows == []
    assert gaps[0]["reason"] == "sell_completed_id_census_mismatch"


def test_legacy_truncated_snapshot_is_excluded_not_treated_as_complete():
    snapshot = {
        "date": "2026-09-23",
        "metrics": {"completed_trades": 12},
        "sections": {"recent_trades": [_trade(index) for index in range(1, 11)]},
    }

    rows, gaps = report_mod._collect_completed_trade_rows([snapshot])

    assert rows == []
    assert gaps[0]["reason"] == "completed_population_truncated"


def test_trade_review_source_warning_cannot_become_valid_empty_population():
    rows, gaps = report_mod._collect_completed_trade_rows(
        [
            {
                "date": "2026-09-23",
                "meta": {"warnings": ["DB connection failed"]},
                "metrics": {"canonical_completed_trades": 0},
                "sections": {"completed_trade_projection": []},
            }
        ]
    )

    assert rows == []
    assert gaps == [{"date": "2026-09-23", "reason": "trade_review_source_warning"}]


def test_legacy_display_profit_is_diagnostic_not_exact_cost():
    rows, gaps = report_mod._collect_completed_trade_rows(
        [
            {
                "date": "2026-09-23",
                "metrics": {"completed_trades": 1},
                "sections": {"recent_trades": [_trade(1, realized_pnl_krw=100)]},
            }
        ]
    )

    assert gaps[0]["reason"] == "legacy_completion_census_unsealed"
    assert rows[0]["realized_pnl_krw"] is None
    assert rows[0]["modeled_realized_pnl_krw"] == 100


def test_missing_realized_pnl_is_not_zero_filled():
    rows = [_trade(1, realized_pnl_krw=100), _trade(2, realized_pnl_krw=None)]

    summary = report_mod._summarize_completed_trades(rows)

    assert summary["trade_count"] == 2
    assert summary["realized_pnl_krw"] is None
    assert summary["realized_pnl_complete_count"] == 1
    assert summary["realized_pnl_missing_count"] == 1


def test_position_outcome_distinguishes_exact_cost_ai_and_post_sell_quality():
    direct = _trade(1, realized_pnl_krw=77)
    direct["exit_signal"] = {
        "exit_rule": "scalp_trailing_take_profit",
        "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
        "inferred": True,
    }
    direct["sell_time_precision"] = "broker_fill_second"
    direct["exact_sell_fill_time"] = "2026-09-23T09:40:00+09:00"
    direct["timeline"].append(
        {
            "stage": "sell_order_sent",
            "fields": {
                "holding_score_role_gate": "unusable_neutral_only",
                "holding_score_negative_exit_usable": "False",
                "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
            },
        }
    )
    reconciled = _trade(2, realized_pnl_krw=None)
    reconciled["sell_time"] = ""
    reconciled["sell_time_precision"] = "order_second_not_fill_second"
    reconciled["sell_time_forbidden_for_intraday_horizon"] = True
    post_sell = [
        {
            "post_sell_id": "a",
            "recommendation_id": 1,
            "signal_date": "2026-09-23",
            "sell_time": "09:40:00",
            "minute_candle_source_quality": "partial_window",
            "metrics_10m": {"mfe_pct": 0.5},
            "outcome": "MISSED_UPSIDE",
        }
    ]

    outcomes, coverage = report_mod._build_position_outcomes(
        [direct, reconciled], post_sell
    )

    assert coverage["completed_valid_trades"] == 2
    assert coverage["exact_cost_trades"] == 1
    assert coverage["full_post_sell_observation_trades"] == 0
    assert outcomes[0]["ai_intervention"] == "unusable"
    assert outcomes[0]["flow_intervention"] == "unproven_source_label_only"
    assert outcomes[0]["exit_rule_provenance"] == "inferred"
    assert outcomes[0]["post_sell_status"] == "partial_window"
    assert outcomes[1]["post_sell_status"] == "not_observable_no_exact_fill_time"


def test_post_sell_pass_requires_mature_horizons_and_matching_anchor():
    trade = _trade(1, realized_pnl_krw=77)
    trade["exact_sell_fill_time"] = "2026-09-23T09:40:00+09:00"
    evaluation = {
        "post_sell_id": "a",
        "recommendation_id": 1,
        "evaluation_status": "evaluated",
        "signal_date": "2026-09-23",
        "sell_time": "09:40:00",
        "evaluated_at": "2026-09-23T09:45:00",
        "minute_candle_source_quality": "pass",
        **{f"metrics_{minute}m": {"bars": 1} for minute in (1, 3, 5, 10)},
    }

    outcomes, coverage = report_mod._build_position_outcomes([trade], [evaluation])
    assert outcomes[0]["post_sell_status"] == "source_gap_horizon_maturity_unproven"
    assert coverage["full_post_sell_observation_trades"] == 0

    evaluation["evaluated_at"] = "2026-09-23T09:51:00"
    outcomes, coverage = report_mod._build_position_outcomes([trade], [evaluation])
    assert outcomes[0]["post_sell_status"] == "pass"
    assert coverage["full_post_sell_observation_trades"] == 1


def test_trailing_direct_input_receipt_preserves_trigger_and_source_gap():
    trade = _trade(1)
    fields = {
        "exit_threshold_status": "effective_value_observed",
        "exit_threshold_key": "SCALP_TRAILING_LIMIT_WEAK",
        "exit_threshold_effective_pct": 0.4,
        "exit_threshold_trailing_start_pct": 0.6,
        "exit_threshold_trailing_arm_observed_pct": 1.1,
        "exit_threshold_strong_score_effective": 75,
        "exit_threshold_ai_score_observed": 50,
        "exit_threshold_ai_score_usable": False,
        "exit_threshold_peak_price": 10110,
        "exit_threshold_executable_bid": 10060,
        "exit_threshold_bid_source": "fresh_ws_executable_bid",
        "exit_threshold_trigger_kind": "trailing_peak_worsen_floor",
    }
    trade["exit_signal"] = {
        "exit_rule": "scalp_trailing_take_profit",
        "fields": fields,
    }
    trade["timeline"][1]["fields"].update(fields)
    trade["timeline"].append(
        {
            "stage": "scalp_trailing_input_transition",
            "fields": {
                "armed": True,
                "triggered": False,
                "source_gap": True,
                "evaluation_at_epoch": 1780000000.0,
                "ws_trade_received_at_epoch": 1779999999.8,
                "ws_trade_clock_provenance": "type_specific_0B",
            },
        }
    )
    trade["timeline"].append(
        {
            "stage": "scalp_trailing_input_transition",
            "fields": {
                "armed": True,
                "triggered": True,
                "source_gap": False,
                "evaluation_at_epoch": 1780000001.0,
                "bid_source_received_at_epoch": 1780000000.9,
                "bid_source_clock_provenance": "rest_receive",
            },
        }
    )
    trade["timeline"].append(
        {
            "stage": "scalp_tp_alternative_observed",
            "fields": {
                "exit_rule": "scalp_ai_momentum_decay",
                "would_exit": True,
            },
        }
    )

    outcomes, coverage = report_mod._build_position_outcomes([trade], [])

    assert coverage["trailing_direct_input_receipt_trades"] == 1
    assert coverage["trailing_input_transition_trades"] == 1
    assert coverage["trailing_first_arm_receipt_trades"] == 1
    assert coverage["trailing_first_arm_trade_clock_trades"] == 1
    assert coverage["trailing_first_trigger_bid_clock_trades"] == 1
    assert outcomes[0]["trailing_input_transition_count"] == 2
    assert outcomes[0]["trailing_source_gap_transition_count"] == 1
    assert outcomes[0]["trailing_first_arm_at_epoch"] == 1780000000.0
    assert outcomes[0]["trailing_first_arm_ws_trade_at_epoch"] == 1779999999.8
    assert outcomes[0]["trailing_first_trigger_at_epoch"] == 1780000001.0
    assert outcomes[0]["trailing_first_trigger_bid_at_epoch"] == 1780000000.9
    assert outcomes[0]["exit_threshold_peak_price"] == 10110
    assert outcomes[0]["exit_threshold_executable_bid"] == 10060
    assert outcomes[0]["exit_threshold_ai_score_usable"] is False
    assert outcomes[0]["tp_alternative_observed_rules"] == [
        "scalp_ai_momentum_decay"
    ]
    readiness = report_mod._build_trailing_threshold_readiness(outcomes)
    assert readiness["funnel_ids"]["direct_signal_ids"] == []
    assert readiness["funnel_ids"]["terminal_custody_unproven_ids"] == ["1"]
    assert readiness["funnel_ids"]["paired_replay_eligible_ids"] == []
    assert readiness["axes"]["SCALP_TRAILING_START_PCT"]["qualified_input_count"] == 0
    assert all(
        axis["candidate_value"] is None
        and axis["eligible_for_live_review"] is False
        for axis in readiness["axes"].values()
    )


def test_holding_exit_observation_report_splits_required_cohorts(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"

    trades = [
        *[
            _trade(
                100 + idx,
                code=f"11111{idx}",
                buy_time=f"2026-04-24 09:{30 + idx:02d}:00",
                sell_time=f"2026-04-24 09:{40 + idx:02d}:00",
                profit_rate=0.6 + (idx * 0.1),
                exit_rule="scalp_trailing_take_profit",
            )
            for idx in range(5)
        ],
        _trade(
            201,
            code="222222",
            buy_time="2026-04-20 09:30:00",
            sell_time="2026-04-20 09:45:00",
            profit_rate=-0.7,
            fill_quality="PARTIAL_FILL",
            exit_rule="scalp_soft_stop_pct",
        ),
        _trade(
            301,
            code="333333",
            buy_time="2026-04-24 10:00:00",
            sell_time="2026-04-24 10:10:00",
            profit_rate=-1.6,
            exit_rule="scalp_soft_stop_pct",
        ),
        _trade(
            302,
            code="333333",
            buy_time="2026-04-24 10:35:00",
            sell_time="2026-04-24 10:50:00",
            profit_rate=-0.8,
            exit_rule="scalp_preset_hard_stop_pct",
            scale_in=True,
        ),
        _trade(401, profit_rate=None),
        _trade(402, profit_rate=0.2, status="OPEN"),
    ]
    soft_trade = next(row for row in trades if row["id"] == 301)
    soft_trade["timeline"][1:1] = [
        {
            "stage": "ai_holding_review",
            "fields": {
                "profit_rate": "-0.80",
                "ai_score": "34",
                "held_sec": "190",
                "low_score_hits": "0/3",
            },
        },
        {
            "stage": "ai_holding_review",
            "fields": {
                "profit_rate": "-0.90",
                "ai_score": "32",
                "held_sec": "205",
                "low_score_hits": "1/3",
            },
        },
        {
            "stage": "ai_holding_review",
            "fields": {
                "profit_rate": "-1.00",
                "ai_score": "31",
                "held_sec": "220",
                "low_score_hits": "3/3",
            },
        },
    ]
    _write_json(
        snapshot_dir / "trade_review_2026-04-24.json",
        {
            "date": "2026-04-24",
            "sections": {"recent_trades": trades},
            "metrics": {"completed_trades": 9},
        },
    )
    _write_json(
        snapshot_dir / "performance_tuning_2026-04-24.json",
        {
            "date": "2026-04-24",
            "metrics": {
                "order_bundle_submitted_events": 20,
                "full_fill_events": 7,
                "partial_fill_events": 1,
            },
        },
    )
    _write_json(
        snapshot_dir / "missed_entry_counterfactual_2026-04-24.json",
        {
            "date": "2026-04-24",
            "summary": {
                "outcome_counts": {"MISSED_WINNER": 3, "AVOIDED_LOSER": 1, "NEUTRAL": 1}
            },
            "metrics": {
                "evaluated_candidates": 5,
                "estimated_counterfactual_pnl_10m_krw_sum": 12345,
            },
            "rows": [
                {"terminal_stage": "latency_block"},
                {"terminal_stage": "latency_block"},
                {"terminal_stage": "blocked_liquidity"},
            ],
        },
    )

    candidates = []
    evaluations = []
    for idx in range(5):
        candidate, evaluation = _post_sell_row(
            f"trail-{idx}",
            100 + idx,
            exit_rule="scalp_trailing_take_profit",
            outcome="MISSED_UPSIDE" if idx < 4 else "GOOD_EXIT",
            profit_rate=0.7,
        )
        candidates.append(candidate)
        evaluations.append(evaluation)
    for idx, rebound_buy in enumerate([True, False]):
        candidate, evaluation = _post_sell_row(
            f"soft-{idx}",
            301,
            exit_rule="scalp_soft_stop_pct",
            outcome="MISSED_UPSIDE",
            profit_rate=-1.6,
            rebound_buy=rebound_buy,
        )
        candidates.append(candidate)
        evaluations.append(evaluation)
    candidate, evaluation = _post_sell_row(
        "hard-0",
        302,
        exit_rule="scalp_preset_hard_stop_pct",
        outcome="GOOD_EXIT",
        profit_rate=-0.8,
    )
    candidates.append(candidate)
    evaluations.append(evaluation)
    _write_jsonl(
        tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl", candidates
    )
    _write_jsonl(
        tmp_path / "post_sell" / "post_sell_evaluations_2026-04-24.jsonl", evaluations
    )
    _write_jsonl(
        tmp_path / "pipeline_events" / "pipeline_events_2026-04-24.jsonl",
        [{"stage": "order_bundle_submitted", "fields": {}} for _ in range(20)],
    )
    report = report_mod.build_holding_exit_observation_report(
        target_date="2026-04-24",
        month_start="2026-04-24",
    )

    for key in [
        "readiness",
        "cohorts",
        "exit_rule_quality",
        "trailing_threshold_readiness",
        "soft_stop_rebound",
        "same_symbol_reentry",
        "opportunity_cost",
        "load_distribution_evidence",
    ]:
        assert key in report

    assert report["readiness"]["observation_ready"] is True
    assert report["readiness"]["completed_valid_trades"] == 7
    assert report["readiness"]["directional_only"] is True
    assert report["cohorts"]["normal_only"]["trade_count"] == 8
    assert report["cohorts"]["post_fallback_deprecation"]["trade_count"] == 7
    assert report["cohorts"]["full_fill"]["trade_count"] == 7
    assert report["cohorts"]["partial_fill"]["trade_count"] == 1
    assert report["cohorts"]["initial-only"]["trade_count"] == 7
    assert report["cohorts"]["pyramid-activated"]["trade_count"] == 1
    assert report["trailing_threshold_readiness"]["status"] == (
        "source_gap_paired_replay_unavailable"
    )
    assert report["economic_input_complete"] is False
    assert report["trailing_threshold_readiness"]["axes"][
        "SCALP_TRAILING_LIMIT_WEAK"
    ]["candidate_value"] is None
    assert report["soft_stop_rebound"]["rebound_above_buy_10m_rate"] == 50.0
    assert report["soft_stop_rebound"]["whipsaw_signal"] is True
    assert report["soft_stop_rebound"]["whipsaw_windows"][3]["window"] == "10m"
    assert report["soft_stop_rebound"]["whipsaw_windows"][3]["mfe_ge_1_0_rate"] == 100.0
    assert report["soft_stop_rebound"]["cooldown_live_allowed"] is False
    assert (
        report["soft_stop_rebound"]["hard_stop_auxiliary"]["evaluated_post_sell"] == 1
    )
    assert (
        report["soft_stop_rebound"]["hard_stop_auxiliary"]["completed_valid_trades"]
        == 1
    )
    assert report["same_symbol_reentry"]["after_soft_stop_next_loss_count"] == 1
    assert report["opportunity_cost"]["outcome_counts"]["MISSED_WINNER"] == 3
    assert report["opportunity_cost"]["terminal_stage_top"][0] == {
        "label": "latency_block",
        "count": 2,
    }


def test_holding_exit_observation_reads_gzip_post_sell_rows(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    candidate, evaluation = _post_sell_row(
        "soft-0",
        301,
        exit_rule="scalp_soft_stop_pct",
        outcome="MISSED_UPSIDE",
        profit_rate=-1.6,
        rebound_buy=True,
    )
    _write_gzip_jsonl(
        tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl.gz", [candidate]
    )
    _write_gzip_jsonl(
        tmp_path / "post_sell" / "post_sell_evaluations_2026-04-24.jsonl.gz",
        [evaluation],
    )

    rows, paths = report_mod._load_post_sell_rows(["2026-04-24"])

    assert len(rows) == 1
    assert paths == [
        str(tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl.gz"),
        str(tmp_path / "post_sell" / "post_sell_evaluations_2026-04-24.jsonl.gz"),
    ]


def test_post_sell_candidate_without_evaluation_stays_unmatured(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    candidate, _evaluation = _post_sell_row(
        "waiting-1", 301, exit_rule="scalp_soft_stop_pct", outcome="NEUTRAL"
    )
    _write_jsonl(
        tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl",
        [candidate],
    )

    rows, _paths = report_mod._load_post_sell_rows(["2026-04-24"])

    assert len(rows) == 1
    assert rows[0]["evaluation_status"] == "candidate_only"
    assert "metrics_10m" not in rows[0]


def test_holding_exit_observation_defaults_to_clean_baseline_window(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        report_mod,
        "clean_baseline_policy",
        lambda: {
            "enabled": True,
            "clean_tuning_baseline_date": "2026-06-05",
            "pre_baseline_decision": "decision_disqualified_archive_only",
        },
    )

    report = report_mod.build_holding_exit_observation_report(target_date="2026-06-06")

    assert report["month_start"] == "2026-06-05"
    assert report["analysis_window"] == {
        "start_date": "2026-06-05",
        "end_date": "2026-06-06",
        "selection": "clean_tuning_baseline_default",
        "clean_tuning_baseline_date": "2026-06-05",
        "clean_tuning_baseline_enabled": True,
        "pre_baseline_decision": "decision_disqualified_archive_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    assert report["completed_population_quality"]["complete"] is False
    assert {
        item["date"]
        for item in report["completed_population_quality"]["source_gap_dates"]
    } == {"2026-06-05", "2026-06-06"}


def test_holding_exit_observation_uses_calendar_month_when_baseline_disabled(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        report_mod,
        "clean_baseline_policy",
        lambda: {
            "enabled": False,
            "clean_tuning_baseline_date": "2026-06-05",
            "pre_baseline_decision": "decision_disqualified_archive_only",
        },
    )

    report = report_mod.build_holding_exit_observation_report(target_date="2026-09-11")

    assert report["month_start"] == "2026-09-01"
    assert report["analysis_window"]["selection"] == "calendar_month_policy_disabled"


def test_target_pipeline_summary_streams_large_rows(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-08-05"
    _write_jsonl(
        tmp_path / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "stage": "order_bundle_submitted",
                "fields": {"exact_payload": "x" * 100_000},
            },
            {
                "stage": "position_rebased_after_fill",
                "fields": {"fill_quality": "PARTIAL_FILL"},
            },
            {
                "stage": "diagnostic",
                "fields": {"legacy_owner": "fallback_single"},
            },
        ],
    )
    monkeypatch.setattr(
        report_mod,
        "_read_jsonl",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("daily pipeline must not use list loader")
        ),
    )

    summary, paths, row_count = report_mod._summarize_target_pipeline_events(
        target_date
    )

    assert row_count == 3
    assert summary == {
        "order_bundle_submitted_events": 1,
        "full_fill_events": 0,
        "partial_fill_events": 1,
        "fallback_regression_count": 1,
    }
    assert paths == [
        str(tmp_path / "pipeline_events" / f"pipeline_events_{target_date}.jsonl")
    ]
