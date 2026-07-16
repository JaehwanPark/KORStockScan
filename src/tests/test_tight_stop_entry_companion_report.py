import json

from src.engine.scalping import tight_stop_entry_companion_report as mod


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _event(stage, emitted_at, *, record_id, profit_rate=None, **fields):
    payload = {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": fields.pop("pipeline", "ENTRY_PIPELINE"),
        "stage": stage,
        "stock_code": fields.pop("stock_code", "000001"),
        "record_id": record_id,
        "fields": fields,
        "emitted_at": emitted_at,
        "emitted_date": emitted_at[:10],
    }
    if profit_rate is not None:
        payload["fields"]["profit_rate"] = profit_rate
    return payload


def _entry_path(
    record_id,
    *,
    pressure=90,
    tick_accel=1.25,
    micro_vwap=12,
    quote_age=120,
    stop_first=False,
):
    entry = _event(
        "order_bundle_submitted",
        "2026-07-10T09:00:00+09:00",
        record_id=record_id,
        actual_order_submitted=True,
        broker_order_forbidden=False,
        ai_score=70,
        ai_action="BUY",
        buy_pressure_10t=pressure,
        tick_acceleration_ratio=tick_accel,
        curr_vs_micro_vwap_bp=micro_vwap,
        quote_age_ms=quote_age,
    )
    if stop_first:
        path = [
            _event(
                "holding_mark",
                "2026-07-10T09:01:00+09:00",
                record_id=record_id,
                profit_rate=-0.8,
            ),
            _event(
                "holding_mark",
                "2026-07-10T09:04:00+09:00",
                record_id=record_id,
                profit_rate=0.4,
            ),
        ]
    else:
        path = [
            _event(
                "holding_mark",
                "2026-07-10T09:01:00+09:00",
                record_id=record_id,
                profit_rate=0.35,
            ),
            _event(
                "holding_mark",
                "2026-07-10T09:04:00+09:00",
                record_id=record_id,
                profit_rate=-0.2,
            ),
        ]
    return [entry, *path]


def test_tight_stop_entry_companion_report_surfaces_source_only_companion_candidates(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    rows = []
    for idx in range(20):
        rows.extend(_entry_path(f"good-{idx}"))
    for idx in range(5):
        rows.extend(
            _entry_path(
                f"bad-{idx}",
                pressure=45,
                tick_accel=0.8,
                micro_vwap=-20,
                stop_first=True,
            )
        )
    _write_jsonl(mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl", rows)

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )

    assert report["allowed_runtime_apply"] is False
    assert report["runtime_effect"] is False
    assert report["summary"]["entry_path_sample_count"] == 25
    assert report["summary"]["overall"]["mfe_before_tight_stop_rate"] == 0.8
    assert report["summary"]["overall"]["tight_stop_first_rate"] == 0.2
    assert report["summary"]["row_authority_counts"] == {
        "real_submitted_path_observation": 25
    }
    assert (
        report["summary"]["companion_candidate_policy"]["exclude_unknown_context"]
        is True
    )
    assert (
        report["summary"]["companion_candidate_policy"][
            "require_positive_survival_edge"
        ]
        is True
    )
    assert report["metric_contract"]["metric_role"] == "diagnostic_win_rate"
    assert report["companion_candidates"]
    assert report["companion_candidates"][0]["allowed_runtime_apply"] is False
    assert report["companion_candidates"][0]["tight_stop_survival_edge"] > 0
    assert report["real_submitted_path_validation"]["sample_floor_passed"] is True
    assert report["real_submitted_path_validation"]["companion_candidate_count"] > 0
    assert report["real_submitted_path_validation"]["allowed_runtime_apply"] is False


def test_tight_stop_entry_companion_report_filters_unknown_and_negative_candidates(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    rows = []
    for idx in range(20):
        rows.extend(
            [
                _event(
                    "order_bundle_submitted",
                    "2026-07-10T09:00:00+09:00",
                    record_id=f"unknown-good-{idx}",
                    actual_order_submitted=True,
                    broker_order_forbidden=False,
                ),
                _event(
                    "holding_mark",
                    "2026-07-10T09:01:00+09:00",
                    record_id=f"unknown-good-{idx}",
                    profit_rate=0.35,
                ),
            ]
        )
    for idx in range(20):
        rows.extend(_entry_path(f"known-bad-{idx}", stop_first=True))
    _write_jsonl(mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl", rows)

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )

    assert report["summary"]["entry_path_sample_count"] == 40
    assert report["companion_candidates"] == []
    assert report["summary"]["top_companion_candidate_count"] == 0
    assert (
        report["real_submitted_path_validation"]["decision"]
        == "hold_no_positive_real_submitted_pattern"
    )
    assert report["real_submitted_path_validation"]["companion_candidates"] == []


def test_tight_stop_entry_companion_report_blocks_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )

    assert report["source_quality"]["status"] == "source_quality_blocked"
    assert report["allowed_runtime_apply"] is False
    assert report["summary"]["entry_path_sample_count"] == 0


def test_tight_stop_entry_companion_report_excludes_sell_order_paths(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    rows = [
        _event(
            "sell_order_submitted",
            "2026-07-10T09:00:00+09:00",
            record_id="sell-1",
            actual_order_submitted=True,
            side="SELL",
            ai_action="SELL_TODAY",
            pipeline="EXIT_PIPELINE",
        ),
        _event(
            "holding_mark",
            "2026-07-10T09:01:00+09:00",
            record_id="sell-1",
            profit_rate=0.5,
        ),
    ]
    rows.extend(_entry_path("buy-1"))
    _write_jsonl(mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl", rows)

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )

    assert report["summary"]["entry_path_sample_count"] == 1
    assert report["entry_path_rows"][0]["key"] == "2026-07-10:real:buy-1"


def test_tight_stop_entry_companion_report_filters_blocked_source_dates(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )

    def _preflight(source_date):
        if source_date == "2026-07-09":
            return {
                "status": "fail",
                "tuning_input_allowed": False,
                "allowed_runtime_apply": False,
                "source_quality_gate": "blocked_contract_gap",
                "blocked_reason": "test_contract_gap",
                "clean_baseline_enforced": True,
            }
        return {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        }

    monkeypatch.setattr(mod, "load_source_quality_preflight", _preflight)
    _write_jsonl(
        mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-09.jsonl",
        _entry_path("blocked-1"),
    )
    _write_jsonl(
        mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl",
        _entry_path("passed-1"),
    )

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-09", end_date="2026-07-10"
    )

    assert report["source_dates"] == ["2026-07-10"]
    assert report["summary"]["entry_path_sample_count"] == 1
    assert report["entry_path_rows"][0]["key"] == "2026-07-10:real:passed-1"
    assert report["source_quality"]["status"] == "warning_source_quality_excluded"
    assert report["source_quality"]["source_date_preflight"]["blocked_count"] == 1
    assert (
        report["source_quality"]["source_date_preflight"]["blocked_dates"][0]["date"]
        == "2026-07-09"
    )


def test_tight_stop_entry_companion_report_preserves_zero_feature_values(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    rows = [
        _event(
            "order_bundle_submitted",
            "2026-07-10T09:00:00+09:00",
            record_id="zero-1",
            actual_order_submitted=True,
            ai_score=0,
            current_ai_score=80,
            buy_pressure_10t=0,
            buy_pressure=90,
            tick_acceleration_ratio=0,
            tick_accel=1.3,
            curr_vs_micro_vwap_bp=0,
            micro_vwap_bp=-20,
            quote_age_ms=0,
        ),
        _event(
            "holding_mark",
            "2026-07-10T09:01:00+09:00",
            record_id="zero-1",
            profit_rate=0.35,
        ),
    ]
    _write_jsonl(mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl", rows)

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )
    row = report["entry_path_rows"][0]

    assert row["score"] == 0.0
    assert row["score_band"] == "score_lt60"
    assert row["buy_pressure_10t"] == 0.0
    assert row["buy_pressure_bucket"] == "pressure_lt55"
    assert row["tick_acceleration_ratio"] == 0.0
    assert row["tick_accel_bucket"] == "tick_accel_lt095"
    assert row["curr_vs_micro_vwap_bp"] == 0.0
    assert row["micro_vwap_bucket"] == "micro_vwap_0_10bp"
    assert row["quote_age_ms"] == 0.0
    assert row["quote_age_bucket"] == "quote_age_le300ms"


def test_tight_stop_entry_companion_report_maps_scalp_sim_entry_context(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    rows = [
        _event(
            "scalp_sim_buy_order_virtual_pending",
            "2026-07-10T09:00:00+09:00",
            record_id="real-parent-1",
            actual_order_submitted=False,
            broker_order_forbidden=True,
            sim_record_id="SIM-1",
            scalp_sim_candidate_window_original_score=62.0,
            scalp_sim_candidate_window_original_reason=(
                "mixed core signals: strong order_flow_pressure_score (80.5) "
                "and accelerating entry_momentum (76) support delay"
            ),
            quote_age_at_submit_ms=815.0,
        ),
        _event(
            "scalp_sim_holding_mark",
            "2026-07-10T09:01:00+09:00",
            record_id=None,
            sim_record_id="SIM-1",
            profit_rate=0.35,
        ),
    ]
    _write_jsonl(mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl", rows)

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )
    row = report["entry_path_rows"][0]

    assert row["row_authority"] == "sim_assumed_fill_path_observation"
    assert row["score"] == 62.0
    assert row["score_band"] == "score60_64"
    assert row["buy_pressure_10t"] == 80.5
    assert row["buy_pressure_bucket"] == "pressure_70_84"
    assert row["tick_acceleration_ratio"] is None
    assert row["tick_accel_bucket"] == "tick_accel_unknown"
    assert row["quote_age_ms"] == 815.0
    assert row["quote_age_bucket"] == "quote_age_301_1000ms"


def test_tight_stop_entry_companion_report_merges_parent_pipeline_context(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    monkeypatch.setattr(mod, "is_krx_trading_day", lambda day: True)
    monkeypatch.setattr(mod, "filter_allowed_dates", lambda dates, policy: (dates, []))
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-04"},
    )
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
            "clean_baseline_enforced": True,
        },
    )
    rows = [
        _event(
            "bad_entry_refined_candidate",
            "2026-07-10T09:00:00+09:00",
            record_id="real-parent-2",
            buy_pressure_10t=83.0,
            tick_acceleration_ratio=1.18,
            curr_vs_micro_vwap_bp=6.5,
            quote_age_ms=450.0,
        ),
        _event(
            "scalp_sim_buy_order_virtual_pending",
            "2026-07-10T09:00:10+09:00",
            record_id=None,
            actual_order_submitted=False,
            broker_order_forbidden=True,
            sim_record_id="SIM-2",
            sim_parent_record_id="real-parent-2",
            scalp_sim_candidate_window_original_score=72.0,
        ),
        _event(
            "scalp_sim_holding_mark",
            "2026-07-10T09:01:00+09:00",
            record_id=None,
            sim_record_id="SIM-2",
            profit_rate=0.35,
        ),
    ]
    _write_jsonl(mod.PIPELINE_EVENTS_DIR / "pipeline_events_2026-07-10.jsonl", rows)

    report = mod.build_report(
        "2026-07-10", start_date="2026-07-10", end_date="2026-07-10"
    )
    row = report["entry_path_rows"][0]

    assert row["key"] == "2026-07-10:sim:SIM-2"
    assert row["row_authority"] == "sim_assumed_fill_path_observation"
    assert row["score_band"] == "score70_74"
    assert row["buy_pressure_bucket"] == "pressure_70_84"
    assert row["tick_accel_bucket"] == "tick_accel_105_119"
    assert row["micro_vwap_bucket"] == "micro_vwap_0_10bp"
    assert row["quote_age_bucket"] == "quote_age_301_1000ms"
