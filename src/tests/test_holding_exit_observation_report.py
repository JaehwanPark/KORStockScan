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
        "profit_rate": profit_rate,
        "realized_pnl_krw": realized_pnl_krw,
        "entry_mode": entry_mode,
        "timeline": timeline,
    }


def _post_sell_row(post_sell_id, recommendation_id, *, exit_rule, outcome, profit_rate=0.6, rebound_buy=False):
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
            "fields": {"profit_rate": "-0.80", "ai_score": "34", "held_sec": "190", "low_score_hits": "0/3"},
        },
        {
            "stage": "ai_holding_review",
            "fields": {"profit_rate": "-0.90", "ai_score": "32", "held_sec": "205", "low_score_hits": "1/3"},
        },
        {
            "stage": "ai_holding_review",
            "fields": {"profit_rate": "-1.00", "ai_score": "31", "held_sec": "220", "low_score_hits": "3/3"},
        },
    ]
    _write_json(
        snapshot_dir / "trade_review_2026-04-24.json",
        {
            "date": "2026-04-24",
            "sections": {"recent_trades": trades},
            "metrics": {"completed_trades": 8},
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
            "summary": {"outcome_counts": {"MISSED_WINNER": 3, "AVOIDED_LOSER": 1, "NEUTRAL": 1}},
            "metrics": {"evaluated_candidates": 5, "estimated_counterfactual_pnl_10m_krw_sum": 12345},
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
    _write_jsonl(tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl", candidates)
    _write_jsonl(tmp_path / "post_sell" / "post_sell_evaluations_2026-04-24.jsonl", evaluations)
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
        "trailing_continuation",
        "soft_stop_rebound",
        "same_symbol_reentry",
        "opportunity_cost",
        "load_distribution_evidence",
    ]:
        assert key in report

    assert report["readiness"]["observation_ready"] is True
    assert report["readiness"]["completed_valid_trades"] == 8
    assert report["readiness"]["directional_only"] is True
    assert report["cohorts"]["normal_only"]["trade_count"] == 8
    assert report["cohorts"]["post_fallback_deprecation"]["trade_count"] == 7
    assert report["cohorts"]["full_fill"]["trade_count"] == 7
    assert report["cohorts"]["partial_fill"]["trade_count"] == 1
    assert report["cohorts"]["initial-only"]["trade_count"] == 7
    assert report["cohorts"]["pyramid-activated"]["trade_count"] == 1
    assert report["trailing_continuation"]["eligible_for_live_review"] is True
    assert report["trailing_continuation"]["qualifying_cohort_count"] == 5
    assert report["soft_stop_rebound"]["rebound_above_buy_10m_rate"] == 50.0
    assert report["soft_stop_rebound"]["whipsaw_signal"] is True
    assert report["soft_stop_rebound"]["whipsaw_windows"][3]["window"] == "10m"
    assert report["soft_stop_rebound"]["whipsaw_windows"][3]["mfe_ge_1_0_rate"] == 100.0
    assert report["soft_stop_rebound"]["cooldown_live_allowed"] is False
    assert report["soft_stop_rebound"]["hard_stop_auxiliary"]["evaluated_post_sell"] == 1
    assert report["soft_stop_rebound"]["hard_stop_auxiliary"]["completed_valid_trades"] == 1
    assert report["same_symbol_reentry"]["after_soft_stop_next_loss_count"] == 1
    assert report["opportunity_cost"]["outcome_counts"]["MISSED_WINNER"] == 3
    assert report["opportunity_cost"]["terminal_stage_top"][0] == {"label": "latency_block", "count": 2}


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
    _write_gzip_jsonl(tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl.gz", [candidate])
    _write_gzip_jsonl(tmp_path / "post_sell" / "post_sell_evaluations_2026-04-24.jsonl.gz", [evaluation])

    rows, paths = report_mod._load_post_sell_rows(["2026-04-24"])

    assert len(rows) == 1
    assert paths == [
        str(tmp_path / "post_sell" / "post_sell_candidates_2026-04-24.jsonl.gz"),
        str(tmp_path / "post_sell" / "post_sell_evaluations_2026-04-24.jsonl.gz"),
    ]
