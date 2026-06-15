import json
from datetime import date

from src.engine import buy_funnel_sentinel as sentinel


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    name: str = "테스트종목",
    code: str = "000001",
    record_id: int = 1,
    pipeline: str = "ENTRY_PIPELINE",
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": name,
        "stock_code": code,
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
    }


def _write_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{target_date}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_previous_trading_day_skips_20260505_holiday(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        sentinel,
        "is_krx_trading_day",
        lambda target: target == date(2026, 5, 4) or target == date(2026, 5, 6),
    )
    _write_events(tmp_path, "2026-05-04", [_event("2026-05-04", "10:00:00", "ai_confirmed")])

    assert sentinel.previous_trading_day_with_events("2026-05-06") == "2026-05-04"


def test_upstream_ai_threshold_classification_uses_previous_day_baseline(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        sentinel,
        "is_krx_trading_day",
        lambda target: target == date(2026, 5, 4) or target == date(2026, 5, 6),
    )
    baseline_rows = []
    for idx in range(10):
        baseline_rows.append(_event("2026-05-04", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx))
    for idx in range(8):
        baseline_rows.append(_event("2026-05-04", f"10:{idx:02d}:10", "budget_pass", record_id=idx))
    for idx in range(4):
        baseline_rows.append(_event("2026-05-04", f"10:{idx:02d}:20", "order_bundle_submitted", record_id=idx))
    _write_events(tmp_path, "2026-05-04", baseline_rows)

    current_rows = []
    for idx in range(10):
        current_rows.append(_event("2026-05-06", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx))
    current_rows.append(_event("2026-05-06", "10:01:10", "budget_pass", record_id=1))
    current_rows.extend(
        [
            _event("2026-05-06", "10:02:00", "blocked_ai_score", record_id=20, fields={"score": "65"}),
            _event(
                "2026-05-06",
                "10:03:00",
                "blocked_ai_score",
                record_id=21,
                fields={"score": "50", "reason": "ai_score_50_buy_hold_override"},
            ),
            _event("2026-05-06", "10:04:00", "wait65_79_ev_candidate", record_id=22, fields={"ai_score": "74"}),
        ]
    )
    _write_events(tmp_path, "2026-05-06", current_rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["baseline"]["date"] == "2026-05-04"
    assert report["classification"]["primary"] == "UPSTREAM_AI_THRESHOLD"
    assert report["current"]["session"]["ratios"]["budget_to_ai_unique_pct"] == 10.0
    blocker_labels = [item["label"] for item in report["current"]["session"]["blocker_top"]]
    assert "blocked_ai_score:score_65" in blocker_labels
    assert "blocked_ai_score:ai_score_50_buy_hold_override" in blocker_labels


def test_latency_drought_when_budget_pass_exists_but_no_submitted(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(_event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx))
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx,
                fields={"reason": "latency_state_danger"},
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["classification"]["primary"] == "SUBMIT_DROUGHT_CRITICAL"
    assert "LATENCY_DROUGHT" in report["classification"]["secondary"]
    assert report["followup"]["route"] == "entry_submit_drought_auto_workorder"
    assert report["followup"]["operator_action_required"] is False
    contract = report["entry_submit_drought_contract"]
    assert contract["operator_action_required"] is False
    assert contract["runtime_effect"] is False
    assert contract["allowed_runtime_apply"] is False
    assert "code_improvement_workorder" in contract["required_downstream"]
    assert "lifecycle_decision_matrix.submit_bucket_attribution" in contract["required_downstream"]
    assert "BROKER_RECEIPT" in contract["weak_contract_matches"]
    assert report["current"]["session"]["stage_unique"]["budget_pass"] == 5
    assert report["current"]["session"]["stage_unique"]["order_bundle_submitted"] == 0


def test_manual_and_test_events_are_excluded(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "ai_confirmed", name="제룡전기", code="033100", record_id=1),
            _event("2026-05-06", "10:01:00", "ai_confirmed", name="TEST", code="123456", record_id=2),
            _event("2026-05-06", "10:02:00", "ai_confirmed", name="정상종목", code="000003", record_id=3),
            _event(
                "2026-05-06",
                "10:02:10",
                "holding_started",
                name="정상종목",
                code="000003",
                record_id=3,
                pipeline="HOLDING_PIPELINE",
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["current"]["session"]["stage_unique"]["ai_confirmed"] == 1
    assert report["current"]["session"]["stage_unique"]["holding_started"] == 1


def test_policy_excludes_telegram_alert(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(tmp_path, "2026-05-06", [_event("2026-05-06", "10:00:00", "ai_confirmed")])

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["policy"]["allowed_automations"] == ["json_report", "markdown_report", "action_recommendation"]


def test_buy_funnel_sentinel_excludes_early_accel_recheck_retry_rows(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "ai_confirmed",
                record_id=1,
                fields={
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            ),
            _event("2026-05-06", "10:01:00", "ai_confirmed", record_id=2),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["current"]["session"]["stage_unique"]["ai_confirmed"] == 1
    assert report["current"]["session"]["lossless_event_count"] == 1


def test_followup_route_is_report_only_for_upstream_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(10):
        rows.append(_event("2026-05-06", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx))
    for idx in range(10, 20):
        rows.append(
            _event(
                "2026-05-06",
                f"10:{idx - 10:02d}:10",
                "blocked_ai_score",
                record_id=idx,
                fields={"score": "68"},
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["schema_version"] == 2
    assert report["classification"]["primary"] == "UPSTREAM_AI_THRESHOLD"
    assert report["followup"]["route"] == "score65_74_counterfactual_review"
    assert report["followup"]["operator_action_required"] is False
    assert report["followup"]["runtime_effect"] == "report_only_no_mutation"


def test_followup_route_auto_handoffs_submit_drought_even_when_runtime_ops_primary():
    actions = sentinel._recommend_actions(
        {"primary": "RUNTIME_OPS", "matches": ["RUNTIME_OPS", "SUBMIT_DROUGHT_CRITICAL"]}
    )
    followup = sentinel._followup_route(
        {"primary": "RUNTIME_OPS", "matches": ["RUNTIME_OPS", "SUBMIT_DROUGHT_CRITICAL"]}
    )

    assert actions[0].startswith("Auto-route")
    assert followup["route"] == "entry_submit_drought_auto_workorder"
    assert followup["operator_action_required"] is False
    assert followup["runtime_effect"] == "auto_workorder_no_intraday_mutation"


def test_use_cache_reads_only_appended_raw_bytes(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "ai_confirmed", record_id=1),
            _event("2026-05-06", "10:01:00", "blocked_ai_score", record_id=2, fields={"score": "65"}),
        ],
    )

    first = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        use_cache=True,
    )
    assert first["event_load"]["cache_enabled"] is True
    assert first["current"]["session"]["stage_unique"]["ai_confirmed"] == 1

    event_path = tmp_path / "pipeline_events" / "pipeline_events_2026-05-06.jsonl"
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _event("2026-05-06", "10:06:00", "ai_confirmed", record_id=3),
                ensure_ascii=False,
            )
            + "\n"
        )

    second = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
        use_cache=True,
    )
    assert second["current"]["session"]["stage_unique"]["ai_confirmed"] == 2
    meta_path = tmp_path / "runtime" / "sentinel_event_cache" / "buy_funnel_sentinel_events_2026-05-06.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["cache_event_count"] == 3
    assert meta["appended_raw_lines"] == 1


def test_use_summary_counts_high_volume_blockers_and_keeps_lossless_cache_slim(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "10:00:00", "ai_confirmed", record_id=1),
            _event(
                "2026-05-06",
                "10:00:10",
                "blocked_strength_momentum",
                record_id=2,
                fields={"reason": "below_buy_ratio", "buy_ratio": "0.41", "strategy": "SCALP"},
            ),
            _event(
                "2026-05-06",
                "10:00:20",
                "blocked_strength_momentum",
                record_id=3,
                fields={"reason": "below_buy_ratio", "buy_ratio": "0.43", "strategy": "SCALP"},
            ),
            _event(
                "2026-05-06",
                "10:01:00",
                "strength_momentum_observed",
                record_id=4,
                fields={"buy_ratio": "0.44"},
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        use_cache=True,
        use_summary=True,
    )

    assert report["event_load"]["summary_status"] == "ok"
    assert report["event_load"]["summary_lossless_cache_excludes_summary_stages"] is True
    assert report["current"]["session"]["stage_unique"]["ai_confirmed"] == 1
    assert report["current"]["session"]["stage_events"]["blocked_strength_momentum"] == 2
    assert report["current"]["session"]["stage_events"]["strength_momentum_observed"] == 1
    assert report["current"]["session"]["blocker_top"][0] == {
        "label": "blocked_strength_momentum:below_buy_ratio",
        "count": 2,
    }

    meta_path = tmp_path / "runtime" / "sentinel_event_cache" / "buy_funnel_sentinel_events_2026-05-06.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["schema_version"] == sentinel.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION
    assert meta["cache_event_count"] == 1


def test_summary_window_counts_bucket_boundary_by_second(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:04:20",
                "blocked_overbought",
                record_id=1,
                fields={"reason": "near_day_high"},
            ),
            _event(
                "2026-05-06",
                "10:04:40",
                "blocked_overbought",
                record_id=2,
                fields={"reason": "near_day_high"},
            ),
            _event(
                "2026-05-06",
                "10:05:10",
                "blocked_overbought",
                record_id=3,
                fields={"reason": "near_day_high"},
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:30"),
        windows_min=(1,),
        use_summary=True,
    )

    assert report["current"]["session"]["blocker_top"][0]["count"] == 3
    assert report["current"]["windows"]["1m"]["blocker_top"][0] == {
        "label": "blocked_overbought:near_day_high",
        "count": 2,
    }


def test_summary_end_boundary_matches_raw_microsecond_exclusion(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:04:59.900000",
                "blocked_overbought",
                record_id=1,
                fields={"reason": "near_day_high"},
            ),
            _event(
                "2026-05-06",
                "10:05:00.100000",
                "blocked_overbought",
                record_id=2,
                fields={"reason": "near_day_high"},
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        windows_min=(1,),
        use_summary=True,
    )

    assert report["current"]["session"]["blocker_top"][0] == {
        "label": "blocked_overbought:near_day_high",
        "count": 1,
    }


def test_summary_stage_actual_order_payload_stays_lossless_without_double_count(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "blocked_overbought",
                record_id=1,
                fields={"reason": "near_day_high", "actual_order_submitted": "true"},
            )
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        use_cache=True,
        use_summary=True,
    )

    assert report["current"]["session"]["stage_events"]["blocked_overbought"] == 1
    assert report["current"]["session"]["blocker_top"][0] == {
        "label": "blocked_overbought:near_day_high",
        "count": 1,
    }
    meta_path = tmp_path / "runtime" / "sentinel_event_cache" / "buy_funnel_sentinel_events_2026-05-06.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["cache_event_count"] == 1


def test_summary_failure_falls_back_to_raw_events(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "blocked_swing_gap",
                record_id=1,
                fields={"reason": "gap_pct_high"},
            )
        ],
    )

    monkeypatch.setattr(
        sentinel,
        "load_pipeline_event_summaries",
        lambda target_date: ([], {"enabled": True, "status": "summary_unavailable"}),
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        use_summary=True,
    )

    assert report["event_load"]["summary_status"] == "summary_unavailable"
    assert report["event_load"]["fallback_to_raw_cache"] is True
    assert report["current"]["session"]["blocker_top"] == []
    assert report["current"]["session"]["swing_blocker_top"][0] == {
        "label": "blocked_swing_gap:gap_pct_high",
        "count": 1,
    }
    assert report["entry_submit_drought_contract"]["source_taxonomy_leakage"] is False
    assert "SOURCE_TAXONOMY_LEAKAGE" not in report["entry_submit_drought_contract"]["weak_contract_matches"]
