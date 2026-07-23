import json

from src.engine import holding_exit_sentinel as sentinel


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "HOLDING_PIPELINE",
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
    }


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
        json.dumps(payload, ensure_ascii=False),
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

    assert report["schema_version"] == 2
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
