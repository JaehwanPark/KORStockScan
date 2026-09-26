import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine import holding_exit_sentinel as sentinel
from src.engine.ai.holding_exit_vote import PATH_POLICY_BY_MARKET, input_snapshot_id
from src.engine.scalping.holding_profit_exit_semantics import audit_profit_exit_flow
from src.engine.scalping.holding_path_vote_policy import policy_path


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    event_fields = {
        "holding_context_venue": "KRX",
        "holding_context_session": "krx_regular",
    }
    event_fields.update(fields or {})
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "HOLDING_PIPELINE",
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": event_fields,
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
    }


def test_profit_semantics_accepts_premarket_zero_vote_first_crossing():
    at = datetime(2026, 9, 28, 8, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    epoch = at.timestamp()
    common = {"pipeline_lifecycle_population_scope": "real_record_bound"}
    transition = sentinel.PipelineEvent(
        at, "HOLDING_PIPELINE", "scalp_trailing_input_transition",
        "Stock", "000001", "7", {
            **common, "position_key": "record:7", "evaluator": "fast_rest_confirmed",
            "first_crossing": json.dumps({
                "at_epoch": epoch, "market": "PREMARKET",
                "threshold_key": "SCALP_TRAILING_LIMIT_WEAK",
            }),
            "trailing_start_pct": "0.4", "tuning_exit_allowed_by_clock": "True",
            "trigger_kind": "trailing_peak_worsen_floor",
        },
    )
    snapshot = sentinel.PipelineEvent(
        at + timedelta(seconds=1), "HOLDING_PIPELINE",
        "holding_path_signal_snapshot", "Stock", "000001", "7", {
            **common, "path_id": "EXIT_TRAILING_TP", "position_key": "record:7",
            "market": "PREMARKET", "session_key": "2026-09-28",
            "signal_id": "first", "signal_at": str(epoch),
            "buy_fill_identity": "a" * 64, "vote_count": "0",
            "decision": "INSUFFICIENT",
            "signal_snapshot_ms": 4, "signal_provider_wait_ms": 0,
            "policy_sha256": input_snapshot_id(
                PATH_POLICY_BY_MARKET[("EXIT_TRAILING_TP", "PREMARKET")]),
        },
    )
    report = audit_profit_exit_flow(
        [transition, snapshot], target_date="2026-09-28",
        load_votes=lambda _: [],
    )
    assert report["status"] == "pass"
    assert report["by_market_trigger"] == {"PREMARKET|fast": 1}
    assert report["by_market_trigger_kind"] == {
        "PREMARKET|fast|trailing_peak_worsen_floor": 1,
    }
    assert report["latency_ms"]["signal_snapshot_ms"]["p99_ms"] == 4
    assert report["latency_ms"]["signal_provider_wait_ms"]["p99_ms"] == 0
    assert report["funnel"]["tp_decision_INSUFFICIENT"] == 1
    broken = sentinel.PipelineEvent(
        snapshot.emitted_at, snapshot.pipeline, snapshot.stage,
        snapshot.stock_name, snapshot.stock_code, snapshot.record_id,
        {**snapshot.fields, "policy_sha256": "0" * 64},
    )
    assert audit_profit_exit_flow(
        [transition, broken], target_date="2026-09-28",
        load_votes=lambda _: [],
    )["status"] == "semantic_contract_invalid"
    unconsumed = sentinel.PipelineEvent(
        snapshot.emitted_at, snapshot.pipeline, snapshot.stage,
        snapshot.stock_name, snapshot.stock_code, snapshot.record_id,
        {**snapshot.fields, "policy_bundle_sha256": "b" * 64,
         "policy_load_status": "baseline_policy_env_missing_or_mismatch"},
    )
    assert audit_profit_exit_flow(
        [transition, unconsumed], target_date="2026-09-28",
        load_votes=lambda _: [], policy_bundle_sha256="b" * 64,
    )["status"] == "runtime_not_consumed"


def test_profit_semantics_distinguishes_empty_and_missing_vote_source():
    assert audit_profit_exit_flow(
        [], target_date="2026-09-28", load_votes=lambda _: [],
    )["status"] == "valid_empty"
    at = datetime(2026, 9, 28, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    signal = sentinel.PipelineEvent(
        at, "HOLDING_PIPELINE", "holding_path_signal_snapshot",
        "Stock", "000001", "8", {
            "pipeline_lifecycle_population_scope": "real_record_bound",
            "path_id": "EXIT_TRAILING_TP", "position_key": "record:8",
            "market": "REGULAR", "session_key": "2026-09-28",
            "signal_id": "first", "signal_at": str(at.timestamp()),
            "buy_fill_identity": "a" * 64, "vote_count": "2",
            "decision": "VETO",
            "policy_sha256": input_snapshot_id(
                PATH_POLICY_BY_MARKET[("EXIT_TRAILING_TP", "REGULAR")]),
        },
    )
    report = audit_profit_exit_flow(
        [signal], target_date="2026-09-28", load_votes=lambda _: [],
    )
    assert report["status"] == "source_gap"
    assert "tp_vote_ledger_missing" in {
        row["reason"] for row in report["source_gaps"]}


def test_empty_natural_flow_still_detects_invalid_selected_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    selected = policy_path(tmp_path, "2026-09-28")
    selected.parent.mkdir(parents=True)
    selected.write_text('{"invalid": true}', encoding="utf-8")
    report = sentinel.build_holding_exit_sentinel_report(
        "2026-09-28", as_of=sentinel._parse_as_of("2026-09-28", "08:10:00"),
    )
    assert report["profit_exit_semantics"]["status"] == "policy_binding_gap"
    assert report["profit_exit_semantics"]["funnel"].get(
        "tp_signal_snapshots", 0) == 0


def test_profit_semantics_detects_tp_exit_without_vote_snapshot():
    at = datetime(2026, 9, 28, 9, 10, tzinfo=ZoneInfo("Asia/Seoul"))
    exit_event = sentinel.PipelineEvent(
        at, "HOLDING_PIPELINE", "exit_signal", "Stock", "000001", "8", {
            "pipeline_lifecycle_population_scope": "real_record_bound",
            "exit_rule": "scalp_trailing_take_profit",
            "holding_path_signal_id": "missing",
        },
    )
    report = audit_profit_exit_flow(
        [exit_event], target_date="2026-09-28", load_votes=lambda _: [],
    )
    assert report["status"] == "source_gap"
    assert report["funnel"]["tp_exit_signals"] == 1
    assert "tp_exit_without_vote_snapshot" in {
        row["reason"] for row in report["source_gaps"]}


def test_profit_semantics_distinguishes_partial_terminal_and_cost_layers():
    at = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    epoch = at.timestamp()
    common = {"pipeline_lifecycle_population_scope": "real_record_bound"}

    def event(offset, stage, fields):
        return sentinel.PipelineEvent(
            at + timedelta(seconds=offset), "HOLDING_PIPELINE", stage,
            "Stock", "000001", "21", {**common, **fields},
        )

    transition = event(0, "scalp_trailing_input_transition", {
        "position_key": "record:21", "evaluator": "normal",
        "first_crossing": {"at_epoch": epoch, "market": "REGULAR",
                           "threshold_key": "SCALP_TRAILING_LIMIT_WEAK"},
        "trailing_start_pct": 0.4, "tuning_exit_allowed_by_clock": True,
        "trigger_kind": "trailing_peak_worsen_floor",
    })
    snapshot = event(1, "holding_path_signal_snapshot", {
        "path_id": "EXIT_TRAILING_TP", "position_key": "record:21",
        "market": "REGULAR", "session_key": "2026-09-28",
        "signal_id": "sig-21", "signal_at": epoch,
        "buy_fill_identity": "a" * 64, "vote_count": 0,
        "decision": "INSUFFICIENT",
        "policy_sha256": input_snapshot_id(
            PATH_POLICY_BY_MARKET[("EXIT_TRAILING_TP", "REGULAR")]),
    })
    exit_signal = event(2, "exit_signal", {
        "exit_rule": "scalp_trailing_take_profit",
        "holding_path_signal_id": "sig-21", "buy_qty": 2,
    })
    sent = event(3, "sell_order_sent", {
        "exit_rule": "scalp_trailing_take_profit",
        "holding_path_signal_id": "sig-21", "ord_no": "SELL-21", "qty": 2,
    })
    partial = event(4, "sell_partial_fill_progress", {
        "exit_rule": "scalp_trailing_take_profit",
        "holding_path_terminal_signal_binding": "same_position_buy_generation",
        "holding_path_signal_id": "sig-21", "order_no": "SELL-21",
    })
    complete = event(5, "sell_completed", {
        "exit_rule": "scalp_trailing_take_profit",
        "holding_path_terminal_signal_binding": "same_position_buy_generation",
        "holding_path_signal_id": "sig-21", "order_no": "SELL-21",
        "remaining_sell_qty": 0,
    })
    pending = audit_profit_exit_flow(
        [transition, snapshot, exit_signal, sent, partial],
        target_date="2026-09-28", load_votes=lambda _: [],
    )
    assert pending["status"] == "pending_terminal"
    assert pending["funnel"]["tp_sell_partial_fill"] == 1
    observation = {
        "completed_population_quality": {"strict_completed_position_ids": ["21"]},
        "position_outcomes": [{
            "record_id": "21", "sell_quantity_conserved": True,
            "profit_rate": 0.5, "realized_pnl_krw": 100,
            "exact_sell_fill_time": "2026-09-28T10:00:05+09:00",
            "post_sell_status": "pass",
        }],
    }
    closed = audit_profit_exit_flow(
        [transition, snapshot, exit_signal, sent, partial, complete],
        target_date="2026-09-28", load_votes=lambda _: [],
        observation=observation,
    )
    assert closed["status"] == "pass"
    assert closed["funnel"]["tp_forward_observed"] == 1
    observation["completed_population_quality"]["strict_completed_position_ids"] = []
    assert audit_profit_exit_flow(
        [transition, snapshot, exit_signal, sent, partial, complete],
        target_date="2026-09-28", load_votes=lambda _: [],
        observation=observation,
    )["status"] == "source_gap"


def test_sell_drought_is_classified_without_cross_venue_denominator(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = [
        _event("2026-05-06", "10:00:00", "exit_signal", record_id=1),
        _event(
            "2026-05-06",
            "17:00:00",
            "exit_signal",
            record_id=2,
            fields={
                "holding_context_venue": "NXT",
                "holding_context_session": "nxt_aftermarket",
            },
        ),
        _event(
            "2026-05-06",
            "17:00:05",
            "sell_order_sent",
            record_id=2,
            fields={
                "holding_context_venue": "NXT",
                "holding_context_session": "nxt_aftermarket",
            },
        ),
    ]
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "17:05:00"),
    )

    scopes = report["current"]["by_venue_session"]
    assert scopes["KRX|KRX_REGULAR"]["classification"]["primary"] == (
        "SELL_EXECUTION_DROUGHT"
    )
    assert scopes["NXT|NXT_AFTERMARKET"]["classification"]["primary"] == "NORMAL"
    assert report["classification"]["scope_key"] == "KRX|KRX_REGULAR"
    assert report["classification"]["primary"] == "SELL_EXECUTION_DROUGHT"
    assert report["current"]["session"]["decision_authority"].startswith(
        "diagnostic_only"
    )


def test_current_holding_nxt_phase_overrides_legacy_krx_entry_venue():
    payload = _event(
        "2026-05-06",
        "17:00:00",
        "sell_order_sent",
        fields={
            "holding_context_venue": "NXT",
            "holding_context_session": "NXT",
            "entry_venue": "KRX",
            "entry_session": "KRX_REGULAR",
        },
    )
    event = sentinel._event_from_cache_row(sentinel._payload_to_cache_row(payload))

    assert event is not None
    assert sentinel._explicit_event_scope(event) == (
        "NXT",
        "NXT_AFTERMARKET",
        "pass",
    )


def test_dual_aftermarket_scope_keeps_broker_actual_venue_separate():
    payload = _event(
        "2026-09-14",
        "19:42:00",
        "sell_order_sent",
        fields={
            "decision_market_scope": "KRX_NXT_INTEGRATED",
            "market_data_route": "krx_nxt_integrated",
            "market_session_regime": "KRX_NXT_AFTERMARKET_CLOSE_ONLY",
            "actual_execution_venue": "KRX",
        },
    )
    event = sentinel._event_from_cache_row(sentinel._payload_to_cache_row(payload))

    assert event is not None
    assert sentinel._explicit_event_scope(event) == (
        "KRX_NXT_INTEGRATED",
        "KRX_NXT_AFTERMARKET_CLOSE_ONLY",
        "pass",
    )
    assert sentinel._actual_execution_venue(event) == "KRX"


def test_dual_aftermarket_missing_actual_venue_stays_unknown():
    payload = _event(
        "2026-09-14",
        "19:46:00",
        "sell_order_sent",
        fields={
            "decision_market_scope": "KRX_NXT_INTEGRATED",
            "market_session_regime": "KRX_NXT_AFTERMARKET_TERMINAL_EXIT",
            "actual_execution_venue": "SOR",
        },
    )
    event = sentinel._event_from_cache_row(sentinel._payload_to_cache_row(payload))

    assert event is not None
    assert sentinel._actual_execution_venue(event) == "UNKNOWN"


def test_premarket_venue_rejects_regular_krx_session():
    payload = _event(
        "2026-05-06",
        "08:30:00",
        "ai_review",
        fields={
            "holding_context_venue": "PREMARKET_KRX_LIKE",
            "holding_context_session": "KRX_REGULAR",
        },
    )
    event = sentinel._event_from_cache_row(sentinel._payload_to_cache_row(payload))

    assert event is not None
    assert sentinel._explicit_event_scope(event) == (
        "CONFLICT",
        "CONFLICT",
        "conflict",
    )


def test_runtime_krx_like_premarket_session_token_is_preserved():
    payload = _event(
        "2026-05-06",
        "08:30:00",
        "ai_review",
        fields={
            "holding_context_venue": "PREMARKET_KRX_LIKE",
            "holding_context_session": "krx_like_premarket",
        },
    )
    event = sentinel._event_from_cache_row(sentinel._payload_to_cache_row(payload))

    assert event is not None
    assert sentinel._explicit_event_scope(event) == (
        "PREMARKET_KRX_LIKE",
        "PREMARKET_KRX_LIKE",
        "pass",
    )


def _write_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{target_date}.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_observation(tmp_path, target_date: str, payload: dict) -> None:
    report_dir = tmp_path / "report" / "monitor_snapshots"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"holding_exit_observation_{target_date}.json").write_text(
        json.dumps({"date": target_date, **payload}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_sell_execution_drought_when_exit_signal_not_sent(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "exit_signal", record_id=1),
            _event("2026-05-06", "10:01:00", "exit_signal", record_id=2),
            _event("2026-05-06", "10:01:05", "sell_order_sent", record_id=1),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "SELL_EXECUTION_DROUGHT"
    assert report["current"]["session"]["stage_unique"]["exit_signal"] == 2
    assert report["current"]["session"]["stage_unique"]["sell_order_sent"] == 1
    assert report["classification"]["sell_execution_scope"]["real_exit_signal"] == 2
    assert report["followup"]["route"] == "sell_receipt_order_path_check"
    assert report["followup"]["operator_action_required"] is True


def test_hold_defer_danger_is_classified(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "2026-05-06",
            f"10:0{idx}:00",
            "holding_flow_override_defer_exit",
            record_id=idx,
            fields={"worsen_pct": "0.35", "exit_rule": "scalp_ai_early_exit"},
        )
        for idx in range(3)
    ]
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "HOLD_DEFER_DANGER"
    assert report["current"]["session"]["holding_flow_scope"]["real_defer_exit"] == 3


def test_non_real_force_exit_does_not_trigger_hold_defer_danger(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "holding_flow_override_force_exit",
                fields={
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            )
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "NORMAL"
    assert "HOLD_DEFER_DANGER" not in report["classification"]["matches"]
    assert report["current"]["session"]["holding_flow_scope"] == {
        "real_defer_exit": 0,
        "real_force_exit": 0,
        "real_exit_confirmed": 0,
        "non_real_defer_exit": 0,
        "non_real_force_exit": 1,
        "non_real_exit_confirmed": 0,
    }


def test_observation_flags_soft_stop_and_trailing(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path, "2026-05-06", [_event("2026-05-06", "10:00:00", "holding_started")]
    )
    _write_observation(
        tmp_path,
        "2026-05-06",
        {
            "soft_stop_rebound": {
                "total_soft_stop": 5,
                "rebound_above_sell_10m_rate": 80.0,
            },
            "exit_rule_quality": [
                {
                    "exit_rule": "scalp_trailing_take_profit",
                    "evaluated_post_sell": 5,
                    "missed_upside_rate": 40.0,
                }
            ],
        },
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "SOFT_STOP_WHIPSAW"
    assert "TRAILING_EARLY_EXIT" in report["classification"]["secondary"]
    assert report["followup"] == {
        "route": "soft_stop_whipsaw_calibration_review",
        "owner": "soft_stop_whipsaw_confirmation",
        "operator_action_required": False,
        "runtime_effect": "report_only_no_mutation",
        "next_artifact": "observation_source_quality_audit",
    }


def test_trailing_followup_uses_native_observation_owner():
    followup = sentinel._followup_route(
        {"primary": "TRAILING_EARLY_EXIT", "sell_execution_scope": {}}
    )

    assert followup == {
        "route": "trailing_threshold_source_review",
        "owner": "scalp_trailing_take_profit",
        "operator_action_required": False,
        "runtime_effect": "report_only_no_mutation",
        "next_artifact": "holding_exit_observation",
    }


def test_stale_after_all_positions_completed_is_not_runtime_ops(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "holding_started", record_id=1),
            _event(
                "2026-05-06",
                "10:01:00",
                "ai_holding_review",
                record_id=1,
                fields={"ai_cache": "miss"},
            ),
            _event("2026-05-06", "10:02:00", "sell_completed", record_id=1),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:30:00"),
    )

    assert report["current"]["session"]["unique_symbols"]["active_holding"] == 0
    assert "RUNTIME_OPS" not in report["classification"]["matches"]


def test_diagnostic_events_without_real_holding_do_not_create_active_holding(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "bad_entry_refined_candidate",
                record_id=1,
            ),
            _event(
                "2026-05-06",
                "10:01:00",
                "ai_holding_review",
                record_id=1,
                fields={"ai_cache": "miss"},
            ),
            _event(
                "2026-05-06",
                "10:02:00",
                "holding_started",
                record_id=2,
                fields={
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:30:00"),
    )

    assert report["current"]["session"]["unique_symbols"]["active_holding"] == 0
    assert "RUNTIME_OPS" not in report["classification"]["matches"]


def test_diagnostic_event_after_sell_completed_does_not_reopen_holding(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "holding_started", record_id=1),
            _event("2026-05-06", "10:01:00", "sell_completed", record_id=1),
            _event(
                "2026-05-06",
                "10:02:00",
                "stat_action_decision_snapshot",
                record_id=1,
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:30:00"),
    )

    assert report["current"]["session"]["unique_symbols"]["active_holding"] == 0
    assert "RUNTIME_OPS" not in report["classification"]["matches"]


def test_stale_with_active_holding_is_runtime_ops(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "holding_started", record_id=1),
            _event(
                "2026-05-06",
                "10:01:00",
                "ai_holding_review",
                record_id=1,
                fields={"ai_cache": "miss"},
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:30:00"),
    )

    assert report["current"]["session"]["unique_symbols"]["active_holding"] == 1
    assert report["classification"]["primary"] == "RUNTIME_OPS"


def test_score50_origin_counts_split_preflight_and_neutralized(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "ai_holding_review",
                record_id=1,
                fields={
                    "holding_score_effective": "50",
                    "holding_score_score50_origin": "preflight_source_quality_blocked",
                    "holding_score_preflight_blocked": "True",
                },
            ),
            _event(
                "2026-05-06",
                "10:01:00",
                "ai_holding_review",
                record_id=2,
                fields={
                    "holding_score_effective": "50",
                    "holding_score_raw": "62",
                    "holding_score_score50_origin": "post_call_source_quality_neutralized",
                    "holding_score_raw_score_non50_neutralized": "True",
                },
            ),
            _event(
                "2026-05-06",
                "10:02:00",
                "ai_holding_reuse_bypass",
                record_id=3,
                fields={"ai_score": "50"},
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )
    session = report["current"]["session"]

    assert session["score50_origin_counts"] == {
        "legacy_or_unclassified_score50": 1,
        "post_call_source_quality_neutralized": 1,
        "preflight_source_quality_blocked": 1,
    }
    assert session["holding_score_preflight_blocked_events"] == 1
    assert session["holding_score_raw_non50_neutralized_events"] == 1
    markdown = sentinel.build_markdown(report)
    assert "score50 origins" in markdown
    assert "score50 raw-non50 neutralized" in markdown


def test_provider_input_preflight_block_is_not_hidden_as_generic_fallback(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "ai_holding_review",
                record_id=1,
                fields={
                    "holding_score_effective": "50",
                    "holding_score_score50_origin": "fallback_score_50",
                    "holding_score_preflight_blocked": "False",
                    "holding_score_source": "input_preflight_blocked",
                    "holding_score_basis": "ai_input_preflight_blocked",
                    "holding_score_excluded_reason": (
                        "holding_score_source_input_preflight_blocked"
                    ),
                },
            ),
            _event(
                "2026-05-06",
                "10:01:00",
                "ai_holding_review",
                record_id=2,
                fields={
                    "holding_score_effective": "49",
                    "holding_score_source": "input_preflight_blocked",
                },
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )
    session = report["current"]["session"]

    assert session["score50_origin_counts"] == {"fallback_score_50": 1}
    assert session["holding_score_preflight_blocked_events"] == 1


def test_policy_excludes_telegram_alert(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path, "2026-05-06", [_event("2026-05-06", "10:00:00", "holding_started")]
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["policy"]["allowed_automations"] == [
        "json_report",
        "markdown_report",
        "action_recommendation",
    ]


def test_non_real_exit_signal_is_split_from_sell_execution_drought(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "exit_signal",
                record_id=1,
                fields={
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
            _event(
                "2026-05-06",
                "10:01:00",
                "exit_signal",
                record_id=2,
                fields={
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["schema_version"] == 3
    assert report["classification"]["primary"] == "NORMAL"
    assert "SELL_EXECUTION_DROUGHT" not in report["classification"]["matches"]
    assert report["classification"]["sell_execution_scope"] == {
        "real_exit_signal": 0,
        "real_sell_order_sent": 0,
        "non_real_exit_signal": 2,
        "non_real_sell_order_sent": 0,
    }
    assert report["current"]["session"]["stage_unique"]["non_real_exit_signal"] == 2
    assert (
        report["current"]["session"]["ratios"][
            "non_real_sell_sent_to_exit_signal_unique_pct"
        ]
        == 0.0
    )


def test_probe_sibling_marks_sparse_exit_signal_as_non_real(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "exit_signal", record_id=1),
            _event(
                "2026-05-06",
                "10:00:01",
                "swing_probe_exit_signal",
                record_id=1,
                fields={
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
            _event(
                "2026-05-06",
                "10:00:02",
                "swing_probe_sell_order_assumed_filled",
                record_id=1,
                fields={
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["classification"]["primary"] == "NORMAL"
    assert "SELL_EXECUTION_DROUGHT" not in report["classification"]["matches"]
    assert report["classification"]["sell_execution_scope"] == {
        "real_exit_signal": 0,
        "real_sell_order_sent": 0,
        "non_real_exit_signal": 1,
        "non_real_sell_order_sent": 0,
    }
    assert report["current"]["session"]["stage_unique"]["exit_signal"] == 1
    assert report["current"]["session"]["stage_unique"]["non_real_exit_signal"] == 1


def test_real_sell_evidence_overrides_non_real_sibling_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "scalp_fast_exit_claimed",
                record_id=1,
                fields={
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "False",
                },
            ),
            _event("2026-05-06", "10:00:01", "exit_signal", record_id=1),
            _event(
                "2026-05-06",
                "10:00:02",
                "sell_order_sent",
                record_id=1,
                fields={"ord_no": "0045325"},
            ),
            _event("2026-05-06", "10:00:03", "sell_completed", record_id=1),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    unique = report["current"]["session"]["stage_unique"]
    assert unique["real_exit_signal"] == 1
    assert unique["real_sell_order_sent"] == 1
    assert unique["real_sell_completed"] == 1
    assert unique["non_real_exit_signal"] == 0
    assert unique["non_real_sell_order_sent"] == 0
    assert unique["non_real_sell_completed"] == 0


def test_explicit_non_real_sell_order_is_not_promoted_by_order_number(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "exit_signal",
                record_id=1,
                fields={
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
            _event(
                "2026-05-06",
                "10:00:01",
                "sell_order_sent",
                record_id=1,
                fields={
                    "ord_no": "SIM-1",
                    "actual_order_submitted": "False",
                    "broker_order_forbidden": "True",
                },
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    unique = report["current"]["session"]["stage_unique"]
    assert unique["real_exit_signal"] == 0
    assert unique["real_sell_order_sent"] == 0
    assert unique["non_real_exit_signal"] == 1
    assert unique["non_real_sell_order_sent"] == 1


def test_conflicting_simulation_provenance_cannot_promote_real_sell(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "exit_signal", record_id=1),
            _event(
                "2026-05-06",
                "10:00:01",
                "sell_order_sent",
                record_id=1,
                fields={
                    "ord_no": "None",
                    "actual_order_submitted": "True",
                    "simulated_order": "True",
                },
            ),
        ],
    )

    report = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    unique = report["current"]["session"]["stage_unique"]
    assert unique["real_exit_signal"] == 0
    assert unique["real_sell_order_sent"] == 0
    assert unique["non_real_exit_signal"] == 1
    assert unique["non_real_sell_order_sent"] == 1


def test_use_cache_reads_only_appended_holding_raw_bytes(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "exit_signal", record_id=1),
            _event("2026-05-06", "10:01:00", "sell_order_sent", record_id=1),
        ],
    )

    first = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        use_cache=True,
    )
    assert first["event_load"]["cache_enabled"] is True
    assert first["current"]["session"]["stage_unique"]["sell_order_sent"] == 1

    event_path = tmp_path / "pipeline_events" / "pipeline_events_2026-05-06.jsonl"
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _event("2026-05-06", "10:06:00", "exit_signal", record_id=2),
                ensure_ascii=False,
            )
            + "\n"
        )

    second = sentinel.build_holding_exit_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
        use_cache=True,
    )
    assert second["current"]["session"]["stage_unique"]["exit_signal"] == 2
    meta_path = (
        tmp_path
        / "runtime"
        / "sentinel_event_cache"
        / "holding_exit_sentinel_events_2026-05-06.meta.json"
    )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["cache_event_count"] == 3
    assert meta["appended_raw_lines"] == 1
