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
    record_id: int | str = 1,
    pipeline: str = "ENTRY_PIPELINE",
    fields: dict | None = None,
) -> dict:
    event_fields = {
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    event_fields.update(fields or {})
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": name,
        "stock_code": code,
        "record_id": record_id,
        "fields": event_fields,
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
    }


def test_submit_drought_is_classified_without_cross_venue_denominator(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(20):
        rows.append(
            _event(
                "2026-05-06",
                f"10:{idx:02d}:00",
                "ai_confirmed",
                record_id=idx,
            )
        )
        rows.append(
            _event(
                "2026-05-06",
                f"17:{idx:02d}:00",
                "ai_confirmed",
                record_id=100 + idx,
                fields={
                    "effective_venue": "NXT",
                    "market_session_bucket": "nxt_aftermarket",
                },
            )
        )
        rows.append(
            _event(
                "2026-05-06",
                f"17:{idx:02d}:10",
                "budget_pass",
                record_id=100 + idx,
                fields={
                    "effective_venue": "NXT",
                    "market_session_bucket": "nxt_aftermarket",
                },
            )
        )
        rows.append(
            _event(
                "2026-05-06",
                f"17:{idx:02d}:20",
                "order_bundle_submitted",
                record_id=100 + idx,
                fields={
                    "effective_venue": "NXT",
                    "market_session_bucket": "nxt_aftermarket",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "17:20:00"),
    )

    scopes = report["current"]["by_venue_session"]
    assert scopes["KRX|KRX_REGULAR"]["classification"]["primary"] == (
        "SUBMIT_DROUGHT_CRITICAL"
    )
    assert scopes["NXT|NXT_AFTERMARKET"]["classification"]["primary"] == "NORMAL"
    assert report["classification"]["scope_key"] == "KRX|KRX_REGULAR"
    assert report["classification"]["primary"] == "SUBMIT_DROUGHT_CRITICAL"
    assert report["current"]["session"]["decision_authority"].startswith(
        "diagnostic_only"
    )


def test_effective_nxt_scope_overrides_legacy_entry_venue_and_uses_time_phase():
    payload = _event(
        "2026-05-06",
        "17:00:00",
        "ai_confirmed",
        fields={
            "effective_venue": "NXT",
            "entry_venue": "KRX",
            "market_session_bucket": "NXT",
        },
    )
    event = sentinel._event_from_cache_row(sentinel._payload_to_cache_row(payload))

    assert event is not None
    assert sentinel._explicit_event_scope(event) == (
        "NXT",
        "NXT_AFTERMARKET",
        "pass",
    )


def test_premarket_venue_rejects_regular_krx_session():
    payload = _event(
        "2026-05-06",
        "08:30:00",
        "ai_confirmed",
        fields={
            "effective_venue": "PREMARKET_KRX_LIKE",
            "market_session_bucket": "KRX_REGULAR",
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
        "ai_confirmed",
        fields={
            "effective_venue": "PREMARKET_KRX_LIKE",
            "market_session_bucket": "krx_like_premarket",
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


def test_previous_trading_day_skips_20260505_holiday(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        sentinel,
        "is_krx_trading_day",
        lambda target: target == date(2026, 5, 4) or target == date(2026, 5, 6),
    )
    _write_events(
        tmp_path, "2026-05-04", [_event("2026-05-04", "10:00:00", "ai_confirmed")]
    )

    assert sentinel.previous_trading_day_with_events("2026-05-06") == "2026-05-04"


def test_prev_close_gainer_handoff_uses_unique_scanner_promotion_identity(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for hhmmss, promotion_id, status, record_id in (
        ("10:00:00", "PROMO-A", "first_unique_promotion_handoff", 1),
        ("10:00:01", "PROMO-A", "first_unique_promotion_handoff", 1),
        ("10:00:02", "PROMO-B", "first_unique_promotion_handoff", 1),
        ("10:00:03", "unproven", "promotion_id_missing_attempt_only", 2),
    ):
        rows.append(
            _event(
                "2026-05-06",
                hhmmss,
                "prev_close_gainer_entry_ai_handoff",
                record_id=record_id,
                fields={
                    "market_gainer_handoff_counting_key": promotion_id,
                    "market_gainer_handoff_counting_status": status,
                    "metric_role": "funnel_count",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
        use_cache=True,
        use_summary=True,
    )

    session = report["current"]["session"]
    assert session["stage_events"]["prev_close_gainer_entry_ai_handoff"] == 4
    assert session["stage_unique"]["prev_close_gainer_entry_ai_handoff"] == 3
    assert session["market_gainer_handoff"] == {
        "raw_event_count": 4,
        "unique_scanner_promotion_count": 2,
        "duplicate_proven_promotion_event_count": 1,
        "promotion_id_missing_attempt_count": 1,
        "counting_status": "promotion_id_gap_present",
    }
    assert (
        report["event_load"]["cache_schema_version"]
        == sentinel.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION
    )


def test_upstream_ai_threshold_classification_uses_previous_day_baseline(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        sentinel,
        "is_krx_trading_day",
        lambda target: target == date(2026, 5, 4) or target == date(2026, 5, 6),
    )
    baseline_rows = []
    for idx in range(10):
        baseline_rows.append(
            _event("2026-05-04", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx)
        )
    for idx in range(8):
        baseline_rows.append(
            _event("2026-05-04", f"10:{idx:02d}:10", "budget_pass", record_id=idx)
        )
    for idx in range(4):
        baseline_rows.append(
            _event(
                "2026-05-04",
                f"10:{idx:02d}:20",
                "order_bundle_submitted",
                record_id=idx,
            )
        )
    _write_events(tmp_path, "2026-05-04", baseline_rows)

    current_rows = []
    for idx in range(10):
        current_rows.append(
            _event("2026-05-06", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx)
        )
    current_rows.append(_event("2026-05-06", "10:01:10", "budget_pass", record_id=1))
    current_rows.extend(
        [
            _event(
                "2026-05-06",
                "10:02:00",
                "blocked_ai_score",
                record_id=20,
                fields={"score": "65"},
            ),
            _event(
                "2026-05-06",
                "10:03:00",
                "blocked_ai_score",
                record_id=21,
                fields={"score": "50", "reason": "ai_score_50_buy_hold_override"},
            ),
            _event(
                "2026-05-06",
                "10:04:00",
                "wait65_79_ev_candidate",
                record_id=22,
                fields={"ai_score": "74"},
            ),
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
    blocker_labels = [
        item["label"] for item in report["current"]["session"]["blocker_top"]
    ]
    assert "blocked_ai_score:score_65" in blocker_labels
    assert "blocked_ai_score:ai_score_50_buy_hold_override" in blocker_labels


def test_ai_confirmed_terminal_no_budget_is_split_by_terminal_reason(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(10):
        rows.append(
            _event("2026-05-06", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx)
        )
    for idx in range(3):
        rows.append(
            _event(
                "2026-05-06",
                f"10:{idx:02d}:10",
                "ai_confirmed_terminal_no_budget",
                record_id=100 + idx,
                fields={
                    "terminal_reason": "first_ai_wait_big_bite_not_confirmed",
                    "source_stage": "first_ai_wait",
                    "ai_action": "WAIT",
                    "ai_score": "63.0",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        )
    for idx in range(2):
        rows.append(
            _event(
                "2026-05-06",
                f"10:{idx:02d}:20",
                "ai_confirmed_terminal_no_budget",
                record_id=200 + idx,
                fields={
                    "terminal_reason": "blocked_ai_score_below_buy_score_threshold",
                    "source_stage": "blocked_ai_score",
                    "ai_action": "WAIT",
                    "ai_score": "62.0",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
        use_cache=True,
        use_summary=True,
    )

    terminal_reasons = {
        item["label"]: item["count"]
        for item in report["current"]["session"]["ai_terminal_reason_top"]
    }
    blockers = {
        item["label"]: item["count"]
        for item in report["current"]["session"]["blocker_top"]
    }
    assert terminal_reasons["ai_terminal:first_ai_wait_big_bite_not_confirmed"] == 3
    assert (
        terminal_reasons["ai_terminal:blocked_ai_score_below_buy_score_threshold"] == 2
    )
    assert "ai_terminal:first_ai_wait_big_bite_not_confirmed" not in blockers
    assert "ai_confirmed_terminal_no_budget:-" not in blockers
    assert (
        report["current"]["session"]["stage_events"]["ai_confirmed_terminal_no_budget"]
        == 5
    )
    assert (
        report["event_load"]["cache_schema_version"]
        == sentinel.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION
    )


def test_latency_drought_when_budget_pass_exists_but_no_submitted(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
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
    assert (
        "lifecycle_decision_matrix.submit_bucket_attribution"
        in contract["required_downstream"]
    )
    assert "BROKER_RECEIPT" in contract["weak_contract_matches"]
    breakdown = contract["observation_breakdown"]
    assert breakdown["decision_authority"] == "submit_drought_attribution_only"
    assert breakdown["runtime_effect"] is False
    assert breakdown["allowed_runtime_apply"] is False
    assert breakdown["broker_order_submit_allowed"] is False
    assert breakdown["axis_order"] == [
        "UPSTREAM_GATE",
        "BUDGET_PASS_COLLAPSE",
        "LATENCY_PRE_SUBMIT",
        "PRICE_REVALIDATION",
        "ENTRY_AI_AUTHORITY_REVALIDATION",
        "BROKER_RECEIPT",
        "ECONOMIC_PARTICIPATION",
        "SIM_REAL_AUTHORITY",
        "SOURCE_TAXONOMY_LEAKAGE",
    ]
    assert set(breakdown["axes"]) == set(breakdown["axis_order"])
    assert breakdown["axes"]["LATENCY_PRE_SUBMIT"]["status"] == "observed"
    assert breakdown["axes"]["LATENCY_PRE_SUBMIT"]["observed_count"] == 5
    assert (
        breakdown["axes"]["LATENCY_PRE_SUBMIT"]["evidence"][
            "unknown_latency_reason_count"
        ]
        == 5
    )
    assert breakdown["axes"]["BROKER_RECEIPT"]["status"] == "no_current_signal"
    assert breakdown["axes"]["PRICE_REVALIDATION"]["status"] == ("no_current_signal")
    assert breakdown["axes"]["ENTRY_AI_AUTHORITY_REVALIDATION"]["status"] == (
        "no_current_signal"
    )
    assert breakdown["axes"]["SIM_REAL_AUTHORITY"]["status"] == "observed"
    assert breakdown["causal_bottleneck_axes"] == ["LATENCY_PRE_SUBMIT"]
    assert breakdown["observation_only_axes"] == [
        "BUDGET_PASS_COLLAPSE",
        "SIM_REAL_AUTHORITY",
    ]
    assert "BROKER_RECEIPT" in breakdown["no_current_signal_axes"]
    assert contract["causal_bottleneck_axes"] == ["LATENCY_PRE_SUBMIT"]
    assert "broker_order_submit" in breakdown["forbidden_uses"]
    assert "provider_route_change" in breakdown["forbidden_uses"]
    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["unknown_latency_reason"] == 5
    assert root_cause["unknown_latency_workorder_required"] is True
    assert report["current"]["session"]["stage_unique"]["budget_pass"] == 5
    assert report["current"]["session"]["stage_unique"]["order_bundle_submitted"] == 0
    assert report["current"]["session"]["latency_state_danger_unique"] == 5
    assert report["current"]["session"]["latency_blocked_budget_unique"] == 5
    markdown = sentinel.build_markdown(report)
    assert (
        "- latency causal join: `raw_danger_events=5, raw_unique=5, "
        "joined_budget_events=5, joined_budget_unique=5, budget_missing_key=0, "
        "latency_missing_key=0`" in markdown
    )


def test_submit_drought_without_latency_block_does_not_claim_latency_drought(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(3):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx)
        )
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["classification"]["primary"] == "SUBMIT_DROUGHT_CRITICAL"
    assert "LATENCY_DROUGHT" not in report["classification"]["matches"]
    assert report["current"]["session"]["latency_state_danger_events"] == 0
    contract = report["entry_submit_drought_contract"]
    assert "LATENCY_PRE_SUBMIT" not in contract["weak_contract_matches"]
    latency_axis = contract["observation_breakdown"]["axes"]["LATENCY_PRE_SUBMIT"]
    assert latency_axis["status"] == "no_current_signal"
    assert latency_axis["observed_count"] == 0


def test_unrelated_latency_block_does_not_claim_budget_pass_latency_drought(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(3):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx)
        )
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
    rows.append(
        _event(
            "2026-05-06",
            "10:04:00",
            "latency_block",
            record_id=99,
            fields={"reason": "latency_state_danger"},
        )
    )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert report["classification"]["primary"] == "SUBMIT_DROUGHT_CRITICAL"
    assert "LATENCY_DROUGHT" not in report["classification"]["matches"]
    session = report["current"]["session"]
    assert session["latency_state_danger_events"] == 1
    assert session["latency_state_danger_unique"] == 1
    assert session["latency_blocked_budget_events"] == 0
    assert session["latency_blocked_budget_unique"] == 0
    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"] == {}
    assert root_cause["unknown_latency_workorder_required"] is False
    contract = report["entry_submit_drought_contract"]
    assert "LATENCY_PRE_SUBMIT" not in contract["weak_contract_matches"]
    latency_axis = contract["observation_breakdown"]["axes"]["LATENCY_PRE_SUBMIT"]
    assert latency_axis["status"] == "no_current_signal"
    assert latency_axis["observed_count"] == 0
    assert latency_axis["evidence"]["latency_state_danger_events"] == 1
    assert latency_axis["evidence"]["latency_state_danger_unique"] == 1
    assert latency_axis["evidence"]["latency_blocked_budget_unique"] == 0


def test_repeated_latency_events_do_not_inflate_unique_drought_condition(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.extend(
            [
                _event(
                    "2026-05-06",
                    f"10:0{idx}:00",
                    "ai_confirmed",
                    record_id=idx + 1,
                ),
                _event(
                    "2026-05-06",
                    f"10:0{idx}:10",
                    "budget_pass",
                    record_id=idx + 1,
                ),
                _event(
                    "2026-05-06",
                    f"10:0{idx}:20",
                    "latency_pass",
                    record_id=idx + 1,
                ),
            ]
        )
    for second in range(10):
        rows.append(
            _event(
                "2026-05-06",
                f"10:05:{second:02d}",
                "latency_block",
                record_id=1,
                fields={"reason": "latency_state_danger"},
            )
        )
    for idx in (1, 2):
        rows.append(
            _event(
                "2026-05-06",
                f"10:06:0{idx}",
                "order_bundle_submitted",
                record_id=idx,
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert "LATENCY_DROUGHT" not in report["classification"]["matches"]
    session = report["current"]["session"]
    assert session["latency_state_danger_events"] == 10
    assert session["latency_state_danger_unique"] == 1
    assert session["latency_blocked_budget_events"] == 10
    assert session["latency_blocked_budget_unique"] == 1


def test_missing_record_id_cannot_create_latency_causal_join(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(3):
        code = f"00000{idx + 1}"
        missing_record_id = "0" if idx == 0 else 0
        rows.extend(
            [
                _event(
                    "2026-05-06",
                    f"10:0{idx}:00",
                    "ai_confirmed",
                    code=code,
                    record_id=missing_record_id,
                ),
                _event(
                    "2026-05-06",
                    f"10:0{idx}:10",
                    "budget_pass",
                    code=code,
                    record_id=missing_record_id,
                ),
                _event(
                    "2026-05-06",
                    f"10:0{idx}:20",
                    "latency_block",
                    code=code,
                    record_id=missing_record_id,
                    fields={"reason": "latency_state_danger"},
                ),
            ]
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    assert "LATENCY_DROUGHT" not in report["classification"]["matches"]
    session = report["current"]["session"]
    assert session["budget_pass_missing_exact_attempt_key_events"] == 3
    assert session["latency_danger_missing_exact_attempt_key_events"] == 3
    assert session["latency_blocked_budget_events"] == 0
    assert session["latency_blocked_budget_unique"] == 0


def test_budget_census_gap_is_observation_only_without_explicit_ai_lineage(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-11"
    rows = [
        _event(
            target_date,
            f"10:{idx:02d}:00",
            "ai_confirmed",
            record_id=idx,
            fields={"ai_decision_trace_id": f"trace-{idx}", "action": "WAIT"},
        )
        for idx in range(20)
    ]
    rows.extend(
        _event(target_date, f"10:{idx:02d}:05", "budget_pass", record_id=idx)
        for idx in range(3)
    )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:30:00"),
    )
    breakdown = report["entry_submit_drought_contract"]["observation_breakdown"]
    budget_axis = breakdown["axes"]["BUDGET_PASS_COLLAPSE"]

    assert budget_axis["status"] == "observation_only"
    assert budget_axis["observed_count"] == 0
    assert budget_axis["evidence"]["legacy_stage_census_gap"] == 17
    assert budget_axis["evidence"]["legacy_stage_census_gap_is_causal"] is False
    assert budget_axis["evidence"]["budget_ai_lineage"]["status"] == (
        "instrumentation_gap_parent_ai_trace_missing"
    )
    assert "BUDGET_PASS_COLLAPSE" not in breakdown["causal_bottleneck_axes"]
    assert "BUDGET_PASS_COLLAPSE" in breakdown["observation_only_axes"]


def test_pre_ai_budget_events_are_not_counted_as_lineage_join_failures(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-11"
    rows = [
        _event(
            target_date,
            "10:00:00",
            "budget_pass",
            fields={
                "pre_submit_parent_ai_decision_trace_id": "-",
                "pre_submit_parent_ai_attempt_trace_id": "-",
                "pre_submit_parent_ai_action": "NOT_EVALUATED",
                "pre_submit_parent_ai_result_source": "not_available",
                "pre_submit_parent_ai_lineage_status": "missing_ai_trace",
                "pre_submit_parent_ai_attempt_trusted": False,
                "pre_submit_parent_ai_source_fresh": False,
            },
        ),
        _event(
            target_date,
            "10:00:05",
            "ai_confirmed",
            fields={"ai_decision_trace_id": "trace-1", "action": "WAIT"},
        ),
        _event(
            target_date,
            "10:00:10",
            "budget_pass",
            fields={
                "pre_submit_parent_ai_decision_trace_id": "trace-1",
                "pre_submit_parent_ai_attempt_trace_id": "trace-1",
                "pre_submit_parent_ai_action": "WAIT",
                "pre_submit_parent_ai_result_source": "live",
                "pre_submit_parent_ai_lineage_status": (
                    "exact_latest_watching_ai_trace"
                ),
                "pre_submit_parent_ai_attempt_trusted": True,
                "pre_submit_parent_ai_source_fresh": True,
            },
            record_id=2,
        ),
    ]
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:30:00"),
    )
    lineage = report["current"]["session"]["budget_ai_lineage"]

    assert lineage["budget_or_block_event_count"] == 2
    assert lineage["lineage_contract_event_count"] == 2
    assert lineage["pre_ai_parent_not_expected_event_count"] == 1
    assert lineage["lineage_join_eligible_event_count"] == 1
    assert lineage["lineage_contract_missing_event_count"] == 0
    assert lineage["parent_trace_missing_when_expected_event_count"] == 0
    assert lineage["parent_attempt_without_trusted_result_event_count"] == 0
    assert lineage["parent_trace_missing_without_attempt_event_count"] == 0
    assert lineage["lineage_joined_event_count"] == 1
    assert lineage["lineage_untrusted_or_stale_event_count"] == 0
    assert lineage["lineage_untrusted_or_stale_reason_counts"] == {}
    assert lineage["exact_parent_trace_unresolved_event_count"] == 0
    assert lineage["lineage_join_coverage_pct"] == 100.0
    assert lineage["raw_event_lineage_join_coverage_pct"] == 50.0
    assert lineage["lineage_join_coverage_denominator"] == (
        "events_with_a_trusted_ai_result_expected; excludes_pre_ai_and_explicit_"
        "attempt_result_unavailable"
    )


def test_pre_ai_only_budget_lineage_is_an_expected_observation() -> None:
    event = sentinel.PipelineEvent(
        emitted_at=sentinel._parse_as_of("2026-05-11", "10:00:00"),
        pipeline="ENTRY_PIPELINE",
        stage="budget_pass",
        stock_name="테스트종목",
        stock_code="000001",
        record_id="1",
        fields={
            "pre_submit_parent_ai_decision_trace_id": "-",
            "pre_submit_parent_ai_attempt_trace_id": "-",
            "pre_submit_parent_ai_action": "NOT_EVALUATED",
            "pre_submit_parent_ai_result_source": "not_available",
            "pre_submit_parent_ai_lineage_status": "missing_ai_trace",
        },
    )

    lineage = sentinel._budget_ai_lineage_summary([event])

    assert lineage["status"] == "pre_ai_budget_order_observed_no_parent_expected"
    assert lineage["pre_ai_parent_not_expected_event_count"] == 1
    assert lineage["lineage_join_eligible_event_count"] == 0
    assert lineage["parent_trace_missing_when_expected_event_count"] == 0
    assert lineage["parent_attempt_without_trusted_result_event_count"] == 0
    assert lineage["parent_trace_missing_without_attempt_event_count"] == 0
    assert lineage["lineage_contract_coverage_pct"] == 100.0


def test_budget_lineage_splits_attempt_without_result_from_missing_attempt() -> None:
    event = sentinel.PipelineEvent(
        emitted_at=sentinel._parse_as_of("2026-05-11", "10:00:00"),
        pipeline="ENTRY_PIPELINE",
        stage="budget_pass",
        stock_name="테스트종목",
        stock_code="000001",
        record_id="1",
        fields={
            "pre_submit_parent_ai_decision_trace_id": "-",
            "pre_submit_parent_ai_attempt_trace_id": "attempt-1",
            "pre_submit_parent_ai_action": "NOT_EVALUATED",
            "pre_submit_parent_ai_result_source": (
                "attempt_untrusted_or_not_available"
            ),
            "pre_submit_parent_ai_lineage_status": "missing_ai_trace",
            "pre_submit_parent_ai_attempt_trusted": False,
            "pre_submit_parent_ai_source_fresh": False,
        },
    )

    lineage = sentinel._budget_ai_lineage_summary([event])

    assert lineage["status"] == "ai_attempt_result_unavailable_no_parent_expected"
    assert lineage["lineage_join_eligible_event_count"] == 0
    assert lineage["parent_trace_missing_when_expected_event_count"] == 0
    assert lineage["parent_attempt_without_trusted_result_event_count"] == 1
    assert lineage["ai_attempt_result_unavailable_parent_not_expected_event_count"] == 1
    assert lineage["parent_trace_missing_without_attempt_event_count"] == 0


def test_budget_block_is_causal_only_when_parent_ai_trace_joins(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-12"
    rows = []
    for idx in range(20):
        trace_id = f"trace-{idx}"
        rows.append(
            _event(
                target_date,
                f"10:{idx:02d}:00",
                "ai_confirmed",
                record_id=idx,
                fields={"ai_decision_trace_id": trace_id, "action": "WAIT"},
            )
        )
        if idx < 3:
            rows.append(
                _event(
                    target_date,
                    f"10:{idx:02d}:05",
                    "blocked_zero_qty" if idx == 0 else "budget_pass",
                    record_id=idx,
                    fields={
                        "pre_submit_parent_ai_decision_trace_id": trace_id,
                        "pre_submit_parent_ai_attempt_trace_id": trace_id,
                        "pre_submit_parent_ai_lineage_status": (
                            "exact_latest_watching_ai_trace"
                        ),
                        "pre_submit_parent_ai_attempt_trusted": True,
                        "pre_submit_parent_ai_source_fresh": True,
                    },
                )
            )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:30:00"),
    )
    breakdown = report["entry_submit_drought_contract"]["observation_breakdown"]
    budget_axis = breakdown["axes"]["BUDGET_PASS_COLLAPSE"]
    lineage = budget_axis["evidence"]["budget_ai_lineage"]

    assert budget_axis["status"] == "observed"
    assert budget_axis["observed_count"] == 1
    assert lineage["linked_budget_block_trace_count"] == 1
    assert lineage["linked_budget_pass_trace_count"] == 2
    assert lineage["lineage_exact_trusted_count"] == 3
    assert lineage["raw_ai_budget_census_is_causal"] is False
    assert "BUDGET_PASS_COLLAPSE" in breakdown["causal_bottleneck_axes"]


def test_budget_block_rejects_untrusted_or_stale_parent_ai_trace(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-13"
    rows = []
    for idx in range(20):
        trace_id = f"trace-{idx}"
        rows.append(
            _event(
                target_date,
                f"10:{idx:02d}:00",
                "ai_confirmed",
                record_id=idx,
                fields={"ai_decision_trace_id": trace_id, "action": "WAIT"},
            )
        )
    rows.append(
        _event(
            target_date,
            "10:00:05",
            "blocked_zero_qty",
            record_id=0,
            fields={
                "pre_submit_parent_ai_decision_trace_id": "trace-0",
                "pre_submit_parent_ai_attempt_trace_id": "trace-0",
                "pre_submit_parent_ai_lineage_status": (
                    "latest_watching_ai_trace_untrusted_or_stale"
                ),
                "pre_submit_parent_ai_attempt_trusted": False,
                "pre_submit_parent_ai_source_fresh": True,
            },
        )
    )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:30:00"),
    )
    budget_axis = report["entry_submit_drought_contract"]["observation_breakdown"][
        "axes"
    ]["BUDGET_PASS_COLLAPSE"]

    assert budget_axis["status"] == "observation_only"
    assert budget_axis["observed_count"] == 0
    assert budget_axis["evidence"]["budget_ai_lineage"]["status"] == (
        "parent_ai_trace_untrusted_or_not_exact"
    )
    assert budget_axis["evidence"]["budget_ai_lineage"][
        "lineage_untrusted_or_stale_reason_counts"
    ] == {"attempt_untrusted": 1}


def test_budget_lineage_splits_untrusted_and_stale_reasons() -> None:
    def lineage_event(
        trace_id: str,
        attempt_trace_id: str,
        *,
        trusted: bool,
        fresh: bool,
    ) -> sentinel.PipelineEvent:
        return sentinel.PipelineEvent(
            emitted_at=sentinel._parse_as_of("2026-05-13", "10:00:00"),
            pipeline="ENTRY_PIPELINE",
            stage="budget_pass",
            stock_name="테스트종목",
            stock_code="000001",
            record_id=trace_id,
            fields={
                "pre_submit_parent_ai_decision_trace_id": trace_id,
                "pre_submit_parent_ai_attempt_trace_id": attempt_trace_id,
                "pre_submit_parent_ai_lineage_status": (
                    "latest_watching_ai_trace_untrusted_or_stale"
                ),
                "pre_submit_parent_ai_attempt_trusted": trusted,
                "pre_submit_parent_ai_source_fresh": fresh,
            },
        )

    lineage = sentinel._budget_ai_lineage_summary(
        [
            lineage_event("trace-1", "attempt-1", trusted=False, fresh=True),
            lineage_event("trace-2", "trace-2", trusted=True, fresh=False),
            lineage_event("trace-3", "attempt-3", trusted=False, fresh=False),
        ]
    )

    assert lineage["lineage_untrusted_or_stale_event_count"] == 3
    assert lineage["lineage_untrusted_or_stale_reason_counts"] == {
        "source_stale": 1,
        "trace_id_mismatch": 1,
        "trace_id_mismatch_and_source_stale": 1,
    }


def test_budget_lineage_joins_trusted_runtime_recheck_trace() -> None:
    trace_id = "recheck-trace-1"
    result_event = sentinel.PipelineEvent(
        emitted_at=sentinel._parse_as_of("2026-05-13", "10:00:00"),
        pipeline="ENTRY_PIPELINE",
        stage="early_accel_strong_bundle_recheck_failed",
        stock_name="테스트종목",
        stock_code="000001",
        record_id="1",
        fields={
            "ai_decision_trace_id": trace_id,
            "ai_result_source": "live",
            "ai_decision_evaluation_status": "evaluated",
            "ai_parse_ok": "True",
            "decision_quality_contract_status": "pass",
        },
    )
    budget_event = sentinel.PipelineEvent(
        emitted_at=sentinel._parse_as_of("2026-05-13", "10:00:01"),
        pipeline="ENTRY_PIPELINE",
        stage="budget_pass",
        stock_name="테스트종목",
        stock_code="000001",
        record_id="1",
        fields={
            "pre_submit_parent_ai_decision_trace_id": trace_id,
            "pre_submit_parent_ai_attempt_trace_id": trace_id,
            "pre_submit_parent_ai_lineage_status": ("exact_latest_watching_ai_trace"),
            "pre_submit_parent_ai_attempt_trusted": True,
            "pre_submit_parent_ai_source_fresh": True,
        },
    )

    lineage = sentinel._budget_ai_lineage_summary([result_event, budget_event])

    assert lineage["lineage_joined_event_count"] == 1
    assert lineage["exact_parent_trace_unresolved_event_count"] == 0
    assert lineage["ai_trace_source_stage_counts"] == {
        "early_accel_strong_bundle_recheck_failed": 1
    }


def test_budget_lineage_rejects_untrusted_runtime_recheck_trace() -> None:
    result_event = sentinel.PipelineEvent(
        emitted_at=sentinel._parse_as_of("2026-05-13", "10:00:00"),
        pipeline="ENTRY_PIPELINE",
        stage="ai_numeric_consistency_recheck_failed",
        stock_name="테스트종목",
        stock_code="000001",
        record_id="1",
        fields={
            "ai_decision_trace_id": "recheck-trace-2",
            "ai_result_source": "live",
            "ai_decision_evaluation_status": "evaluated",
            "ai_parse_ok": "False",
            "decision_quality_contract_status": "pass",
        },
    )

    lineage = sentinel._budget_ai_lineage_summary([result_event])

    assert lineage["ai_trace_count"] == 0
    assert lineage["ai_trace_source_stage_counts"] == {}


def test_runtime_recheck_trace_stage_is_kept_in_lossless_cache() -> None:
    payload = _event(
        "2026-05-13",
        "10:00:00",
        "ai_numeric_consistency_recheck_corrected",
        fields={
            "ai_decision_trace_id": "recheck-trace-3",
            "ai_result_source": "live",
            "ai_decision_evaluation_status": "evaluated",
            "ai_parse_ok": True,
            "decision_quality_contract_status": "pass",
            "ai_call_trigger_reason": "ai_numeric_consistency_recheck",
        },
    )

    row = sentinel._payload_to_cache_row(payload)

    assert row is not None
    assert row["stage"] == "ai_numeric_consistency_recheck_corrected"
    assert row["fields"]["ai_decision_trace_id"] == "recheck-trace-3"


def test_submit_drought_separates_price_revalidation_from_broker_receipt(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-07"
    rows = []
    for idx in range(5):
        rows.extend(
            [
                _event(target_date, f"10:0{idx}:00", "ai_confirmed", record_id=idx),
                _event(target_date, f"10:0{idx}:05", "budget_pass", record_id=idx),
                _event(target_date, f"10:0{idx}:10", "latency_pass", record_id=idx),
                _event(
                    target_date,
                    f"10:0{idx}:15",
                    "pre_submit_price_guard_block",
                    record_id=idx,
                    fields={"reason": "price_revalidation_failed"},
                ),
            ]
        )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:10:00"),
    )
    breakdown = report["entry_submit_drought_contract"]["observation_breakdown"]

    assert breakdown["axes"]["PRICE_REVALIDATION"]["status"] == "observed"
    assert breakdown["axes"]["PRICE_REVALIDATION"]["observed_count"] == 5
    assert breakdown["axes"]["BROKER_RECEIPT"]["status"] == "no_current_signal"
    assert breakdown["axes"]["BROKER_RECEIPT"]["observed_count"] == 0
    assert "PRICE_REVALIDATION" in breakdown["causal_bottleneck_axes"]
    assert "BROKER_RECEIPT" in breakdown["no_current_signal_axes"]
    assert breakdown["metric_role"] == "funnel_count"
    assert breakdown["decision_authority"] == "submit_drought_attribution_only"


def test_submit_drought_separates_entry_ai_authority_from_price_and_broker(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-10"
    rows = []
    for idx in range(5):
        rows.extend(
            [
                _event(target_date, f"10:0{idx}:00", "ai_confirmed", record_id=idx),
                _event(target_date, f"10:0{idx}:05", "budget_pass", record_id=idx),
                _event(target_date, f"10:0{idx}:10", "latency_pass", record_id=idx),
                _event(
                    target_date,
                    f"10:0{idx}:15",
                    "pre_submit_entry_ai_authority_guard_block",
                    record_id=idx,
                    fields={"reason": "entry_ai_result_stale_or_untrusted"},
                ),
            ]
        )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:10:00"),
    )
    breakdown = report["entry_submit_drought_contract"]["observation_breakdown"]

    authority = breakdown["axes"]["ENTRY_AI_AUTHORITY_REVALIDATION"]
    assert authority["status"] == "observed"
    assert authority["observed_count"] == 5
    assert breakdown["axes"]["PRICE_REVALIDATION"]["status"] == "no_current_signal"
    assert breakdown["axes"]["BROKER_RECEIPT"]["status"] == "no_current_signal"
    assert "ENTRY_AI_AUTHORITY_REVALIDATION" in breakdown["causal_bottleneck_axes"]


def test_submit_drought_does_not_treat_scale_in_price_guard_as_entry_blocker(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-09"
    rows = []
    for idx in range(5):
        rows.extend(
            [
                _event(target_date, f"10:0{idx}:00", "ai_confirmed", record_id=idx),
                _event(target_date, f"10:0{idx}:10", "latency_pass", record_id=idx),
                _event(
                    target_date,
                    f"10:0{idx}:15",
                    "scale_in_price_guard_block",
                    record_id=idx,
                ),
            ]
        )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:10:00"),
    )
    breakdown = report["entry_submit_drought_contract"]["observation_breakdown"]

    assert breakdown["axes"]["PRICE_REVALIDATION"]["status"] == "no_current_signal"
    assert breakdown["axes"]["PRICE_REVALIDATION"]["observed_count"] == 0
    assert "PRICE_REVALIDATION" in breakdown["no_current_signal_axes"]


def test_submit_drought_broker_axis_requires_explicit_submit_failure(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-08"
    rows = []
    for idx in range(5):
        rows.extend(
            [
                _event(target_date, f"10:0{idx}:00", "ai_confirmed", record_id=idx),
                _event(target_date, f"10:0{idx}:05", "budget_pass", record_id=idx),
                _event(target_date, f"10:0{idx}:10", "latency_pass", record_id=idx),
            ]
        )
    rows.append(
        _event(
            target_date,
            "10:04:15",
            "broker_submit_failed",
            record_id=4,
            fields={"reason": "broker_rejected"},
        )
    )
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:10:00"),
    )
    broker_axis = report["entry_submit_drought_contract"]["observation_breakdown"][
        "axes"
    ]["BROKER_RECEIPT"]

    assert broker_axis["status"] == "observed"
    assert broker_axis["observed_count"] == 1
    assert broker_axis["evidence"]["broker_submit_failure_unique"] == 1


def test_probe_only_bundle_is_not_counted_as_full_economic_submission(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-07-23"
    rows = [
        _event(
            target_date,
            "10:00:00",
            "probe_submitted",
            record_id=1,
            fields={
                "probe_bundle_id": "A",
                "qty": 1,
                "actual_order_submitted": True,
                "rising_missed_effective_venue": "KRX",
                "forced_entry_qty": 5,
            },
        ),
        _event(
            target_date,
            "10:00:01",
            "probe_filled",
            record_id=1,
            fields={"probe_bundle_id": "A", "fill_qty": 1, "fill_price": 100},
        ),
        _event(
            target_date,
            "10:00:02",
            "residual_submitted",
            record_id=1,
            fields={
                "probe_bundle_id": "A",
                "order_no": "R1",
                "qty": 4,
                "price": 100,
                "actual_order_submitted": True,
                "rising_missed_effective_venue": "KRX",
            },
        ),
        _event(
            target_date,
            "10:00:03",
            "order_bundle_submitted",
            record_id=1,
            fields={
                "requested_qty": 5,
                "order_price": 100,
                "rising_missed_effective_venue": "KRX",
            },
        ),
        _event(
            target_date,
            "10:01:00",
            "probe_submitted",
            record_id=2,
            fields={
                "probe_bundle_id": "B",
                "qty": 1,
                "actual_order_submitted": True,
                "rising_missed_effective_venue": "UNKNOWN",
                "venue": "KRX",
                "forced_entry_qty": 10,
            },
        ),
        _event(
            target_date,
            "10:01:01",
            "probe_filled",
            record_id=2,
            fields={"probe_bundle_id": "B", "fill_qty": 1, "fill_price": 200},
        ),
        _event(
            target_date,
            "10:01:02",
            "residual_blocked",
            record_id=2,
            fields={
                "probe_bundle_id": "B",
                "reason": "residual_revalidation_timeout",
                "actual_order_submitted": False,
                "rising_missed_effective_venue": "UNKNOWN",
                "venue": "KRX",
            },
        ),
        _event(
            target_date,
            "10:01:03",
            "order_bundle_submitted",
            record_id=2,
            fields={
                "requested_qty": 10,
                "order_price": 200,
                "rising_missed_effective_venue": "UNKNOWN",
                "venue": "KRX",
            },
        ),
    ]
    _write_events(tmp_path, target_date, rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:02:00"),
        dry_run=True,
    )
    economic = report["current"]["session"]["economic_participation"]

    assert economic["observed_bundle_count"] == 2
    assert economic["source_quality_valid_bundle_count"] == 2
    assert economic["full_submitted_bundle_count"] == 1
    assert economic["probe_only_bundle_count"] == 1
    assert economic["requested_qty"] == 15
    assert economic["submitted_qty"] == 6
    assert economic["submitted_qty_to_requested_qty_pct"] == 40.0
    assert economic["requested_notional_krw"] == 2500
    assert economic["submitted_notional_krw"] == 700
    assert economic["submitted_notional_to_requested_notional_pct"] == 28.0
    assert economic["by_venue"]["KRX"]["probe_only_bundle_count"] == 1
    assert economic["decision_authority"] == "submit_drought_attribution_only"
    assert economic["runtime_effect"] is False


def test_cached_economic_participation_keeps_probe_bundle_lifecycle(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-06"
    _write_events(
        tmp_path,
        target_date,
        [
            _event(
                target_date,
                "10:00:00",
                "order_bundle_submitted",
                record_id=1,
                fields={
                    "requested_qty": 10,
                    "order_price": 10_000,
                    "rising_missed_effective_venue": "KRX",
                },
            ),
            _event(
                target_date,
                "10:00:01",
                "probe_submitted",
                record_id=1,
                fields={
                    "probe_bundle_id": "B1",
                    "qty": 1,
                    "order_no": "1001",
                    "actual_order_submitted": True,
                    "rising_missed_effective_venue": "KRX",
                },
            ),
            _event(
                target_date,
                "10:00:02",
                "probe_filled",
                record_id=1,
                fields={
                    "probe_bundle_id": "B1",
                    "fill_qty": 1,
                    "fill_price": 10_000,
                    "actual_order_submitted": True,
                    "rising_missed_effective_venue": "KRX",
                },
            ),
            _event(
                target_date,
                "10:00:03",
                "residual_blocked",
                record_id=1,
                fields={
                    "probe_bundle_id": "B1",
                    "reason": "residual_revalidation_timeout",
                    "actual_order_submitted": False,
                    "rising_missed_effective_venue": "KRX",
                },
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "10:05:00"),
        use_cache=True,
        use_summary=True,
    )

    economic = report["current"]["session"]["economic_participation"]
    assert economic["observed_bundle_count"] == 1
    assert economic["source_quality_valid_bundle_count"] == 1
    assert economic["probe_only_bundle_count"] == 1
    assert economic["requested_qty"] == 10
    assert economic["submitted_qty"] == 1
    assert economic["submitted_notional_to_requested_notional_pct"] == 10.0


def test_economic_participation_counts_bounded_single_share_order_bundle(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-06"
    _write_events(
        tmp_path,
        target_date,
        [
            _event(
                target_date,
                "12:25:05",
                "order_bundle_submitted",
                record_id=1,
                fields={
                    "requested_qty": 1,
                    "submitted_qty": 1,
                    "order_price": 15_410,
                    "order_no": "0039766",
                    "actual_order_submitted": True,
                    "forced_entry_reason": "rising_missed_one_share_entry",
                    "rising_missed_effective_venue": "KRX",
                },
            )
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "12:30:00"),
        dry_run=True,
    )
    economic = report["current"]["session"]["economic_participation"]

    assert economic["observed_bundle_count"] == 1
    assert economic["source_quality_valid_bundle_count"] == 1
    assert economic["probe_only_bundle_count"] == 1
    assert economic["full_submitted_bundle_count"] == 0
    assert economic["requested_qty"] == 1
    assert economic["submitted_qty"] == 1
    assert economic["submitted_notional_krw"] == 15_410
    assert economic["submitted_notional_to_requested_notional_pct"] == 100.0
    assert economic["rows"][0]["probe_submission_source"] == (
        "single_share_order_bundle"
    )
    axis = report["entry_submit_drought_contract"]["observation_breakdown"]["axes"][
        "ECONOMIC_PARTICIPATION"
    ]
    assert axis["status"] == "observed"
    assert (
        "submission participation alone is not execution EV"
        in axis["next_repair_action"]
    )


def test_economic_participation_excludes_unapproved_or_sim_single_share_bundles(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-06"
    _write_events(
        tmp_path,
        target_date,
        [
            _event(
                target_date,
                "12:25:05",
                "order_bundle_submitted",
                record_id=1,
                fields={
                    "requested_qty": 1,
                    "submitted_qty": 1,
                    "order_price": 15_410,
                    "order_no": "0039766",
                    "actual_order_submitted": True,
                    "forced_entry_reason": "normal_entry",
                    "rising_missed_effective_venue": "KRX",
                },
            ),
            _event(
                target_date,
                "12:25:06",
                "order_bundle_submitted",
                record_id=2,
                fields={
                    "requested_qty": 1,
                    "submitted_qty": 1,
                    "order_price": 15_410,
                    "order_no": "SIM-0039767",
                    "actual_order_submitted": False,
                    "forced_entry_reason": "rising_missed_one_share_entry",
                    "rising_missed_effective_venue": "KRX",
                },
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "12:30:00"),
        dry_run=True,
    )
    economic = report["current"]["session"]["economic_participation"]

    assert economic["observed_bundle_count"] == 0
    assert economic["source_quality_valid_bundle_count"] == 0
    assert economic["submitted_qty"] == 0
    assert economic["rows"] == []


def test_economic_participation_separates_reused_record_id_by_attempt(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    target_date = "2026-05-06"
    first_attempt = "SCANPROM-003350-first"
    second_attempt = "SCANPROM-003350-second"
    _write_events(
        tmp_path,
        target_date,
        [
            _event(
                target_date,
                "12:25:05",
                "order_bundle_submitted",
                record_id=34702,
                fields={
                    "requested_qty": 1,
                    "submitted_qty": 1,
                    "order_price": 11_630,
                    "order_no": "0043176",
                    "actual_order_submitted": True,
                    "forced_entry_reason": "rising_missed_one_share_entry",
                    "main_lifecycle_attempt_id": first_attempt,
                    "rising_missed_effective_venue": "KRX",
                },
            ),
            _event(
                target_date,
                "12:26:05",
                "order_bundle_submitted",
                record_id=34702,
                fields={
                    "requested_qty": 1,
                    "submitted_qty": 1,
                    "order_price": 11_750,
                    "order_no": "0045294",
                    "actual_order_submitted": True,
                    "forced_entry_reason": "rising_missed_one_share_entry",
                    "scanner_promotion_id": second_attempt,
                    "rising_missed_effective_venue": "KRX",
                },
            ),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        target_date,
        as_of=sentinel._parse_as_of(target_date, "12:30:00"),
        dry_run=True,
    )
    economic = report["current"]["session"]["economic_participation"]

    assert economic["observed_bundle_count"] == 2
    assert economic["requested_qty"] == 2
    assert economic["submitted_qty"] == 2
    assert economic["submitted_qty_to_requested_qty_pct"] == 100.0
    assert {row["attempt_key"] for row in economic["rows"]} == {
        f"attempt:{first_attempt}",
        f"attempt:{second_attempt}",
    }


def test_latency_drought_uses_latency_danger_reason_breakdown(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "latency_danger_reasons": "quote_stale,ws_age_too_high",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["quote_stale"] == 10
    assert root_cause["unknown_latency_reason_count"] == 0
    assert root_cause["unknown_latency_workorder_required"] is False


def test_latency_drought_classifies_ws_jitter_as_quote_stale(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "latency_danger_reasons": "ws_jitter_too_high",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["quote_stale"] == 5
    assert root_cause["unknown_latency_reason_count"] == 0


def test_latency_drought_splits_orderbook_microstructure_spread(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "latency_danger_reasons": "ws_age_too_high",
                    "orderbook_micro_spread_ticks": "6",
                    "orderbook_micro_ofi_bucket_key": "spread=wide|price=high|depth=normal|sample=rich",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["quote_stale"] == 5
    assert root_cause["latency_root_cause_counts"]["spread_microstructure_guard"] == 5
    assert root_cause["unknown_latency_reason_count"] == 0


def test_latency_drought_classifies_other_danger_as_order_rtt_guard(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "latency_danger_reasons": "other_danger",
                    "pre_submit_quote_refresh_reason": "quote_not_stale",
                    "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["order_rtt_guard"] == 5
    assert root_cause["unknown_latency_reason_count"] == 0


def test_latency_drought_splits_pre_submit_quote_refresh_observer_failure(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "pre_submit_quote_refresh_enabled": True,
                    "pre_submit_quote_refresh_applied": False,
                    "pre_submit_quote_refresh_reason": "observer_quote_missing",
                    "pre_submit_quote_refresh_strategy_id": "KOSPI_ML",
                    "pre_submit_quote_refresh_env_value": "true",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["observer_unhealthy"] == 5
    assert (
        root_cause["quote_freshness_attribution"]["refresh_subreason_counts"][
            "observer_quote_refresh_failed_missing"
        ]
        == 5
    )
    assert root_cause["unknown_latency_reason_count"] == 0
    assert root_cause["unknown_latency_workorder_required"] is False


def test_latency_drought_splits_pre_submit_ws_snapshot_stale(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "pre_submit_ws_snapshot_refresh_enabled": True,
                    "pre_submit_ws_snapshot_refresh_applied": False,
                    "pre_submit_ws_snapshot_refresh_reason": "latest_snapshot_stale",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["quote_stale"] == 5
    assert (
        root_cause["quote_freshness_attribution"]["refresh_subreason_counts"][
            "ws_snapshot_refresh_failed_stale"
        ]
        == 5
    )
    assert root_cause["unknown_latency_reason_count"] == 0
    assert root_cause["unknown_latency_workorder_required"] is False


def test_latency_drought_splits_pre_submit_ws_snapshot_none_as_missing(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "pre_submit_ws_snapshot_refresh_enabled": True,
                    "pre_submit_ws_snapshot_refresh_applied": False,
                    "pre_submit_ws_snapshot_refresh_reason": "None",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"]["observer_unhealthy"] == 5
    assert (
        root_cause["quote_freshness_attribution"]["refresh_subreason_counts"][
            "ws_snapshot_refresh_failed_missing"
        ]
        == 5
    )
    assert root_cause["unknown_latency_reason_count"] == 0
    assert root_cause["unknown_latency_workorder_required"] is False


def test_latency_drought_quote_freshness_attribution_counts_recovered_pass_and_submit(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx)
        )
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
    rows.extend(
        [
            _event("2026-05-06", "10:05:40", "ai_confirmed", record_id=100),
            _event("2026-05-06", "10:05:50", "budget_pass", record_id=100),
            _event("2026-05-06", "10:06:40", "ai_confirmed", record_id=101),
            _event("2026-05-06", "10:06:50", "budget_pass", record_id=101),
        ]
    )
    rows.append(
        _event(
            "2026-05-06",
            "10:06:00",
            "latency_pass",
            record_id=100,
            fields={
                "pre_submit_ws_snapshot_refresh_applied": True,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
            },
        )
    )
    rows.append(
        _event(
            "2026-05-06",
            "10:06:03",
            "order_bundle_submitted",
            record_id=100,
            fields={
                "pre_submit_ws_snapshot_refresh_applied": True,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
            },
        )
    )
    rows.append(
        _event(
            "2026-05-06",
            "10:07:00",
            "latency_block",
            record_id=101,
            fields={
                "reason": "latency_state_danger",
                "pre_submit_quote_refresh_enabled": True,
                "pre_submit_quote_refresh_applied": False,
                "pre_submit_quote_refresh_reason": "observer_quote_missing",
            },
        )
    )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    quote = report["classification"]["submit_drought_root_cause"][
        "quote_freshness_attribution"
    ]
    assert (
        quote["decision_authority"] == "submit_drought_quote_freshness_attribution_only"
    )
    assert quote["runtime_effect"] is False
    assert quote["refresh_attempted_count"] == 2
    assert quote["refresh_applied_count"] == 1
    assert quote["latency_pass_recovered_count"] == 1
    assert quote["order_bundle_submitted_after_refresh_count"] == 1
    assert (
        quote["refresh_subreason_counts"]["observer_quote_refresh_failed_missing"] == 1
    )
    assert quote["still_latency_blocked_after_refresh_count"] == 1


def test_refresh_still_blocked_count_uses_latency_block_events_not_attempt_minus_applied(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx)
        )
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
    rows.extend(
        [
            _event("2026-05-06", "10:05:40", "ai_confirmed", record_id=100),
            _event("2026-05-06", "10:05:50", "budget_pass", record_id=100),
        ]
    )
    rows.append(
        _event(
            "2026-05-06",
            "10:06:00",
            "latency_block",
            record_id=100,
            fields={
                "reason": "latency_state_danger",
                "pre_submit_quote_refresh_enabled": True,
                "pre_submit_quote_refresh_applied": False,
                "pre_submit_quote_refresh_reason": "observer_quote_missing",
            },
        )
    )
    rows.append(
        _event(
            "2026-05-06",
            "10:06:05",
            "latency_pass",
            record_id=100,
            fields={
                "pre_submit_ws_snapshot_refresh_applied": True,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
            },
        )
    )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    quote = report["classification"]["submit_drought_root_cause"][
        "quote_freshness_attribution"
    ]
    assert quote["refresh_attempted_count"] == 1
    assert quote["refresh_applied_count"] == 1
    assert quote["latency_pass_recovered_count"] == 1
    assert quote["still_latency_blocked_after_refresh_count"] == 1


def test_refresh_recovered_latency_pass_downstream_breakdown(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx)
        )
        rows.append(_event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx))
    rows.extend(
        [
            _event("2026-05-06", "10:05:40", "ai_confirmed", record_id=100),
            _event("2026-05-06", "10:05:50", "budget_pass", record_id=100),
            _event("2026-05-06", "10:06:40", "ai_confirmed", record_id=101),
            _event("2026-05-06", "10:06:50", "budget_pass", record_id=101),
            _event("2026-05-06", "10:07:40", "ai_confirmed", record_id=102),
            _event("2026-05-06", "10:07:50", "budget_pass", record_id=102),
        ]
    )
    rows.extend(
        [
            _event(
                "2026-05-06",
                "10:06:00",
                "latency_pass",
                record_id=100,
                fields={
                    "pre_submit_quote_refresh_applied": True,
                    "pre_submit_quote_refresh_reason": "observer_quote_fresh",
                },
            ),
            _event(
                "2026-05-06",
                "10:06:01",
                "pre_submit_price_guard_block",
                record_id=100,
                fields={"reason": "price_gap_guard"},
            ),
            _event(
                "2026-05-06",
                "10:07:00",
                "latency_pass",
                record_id=101,
                fields={
                    "pre_submit_ws_snapshot_refresh_applied": True,
                    "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                },
            ),
            _event("2026-05-06", "10:07:01", "entry_armed_expired", record_id=101),
            _event(
                "2026-05-06",
                "10:08:00",
                "latency_pass",
                record_id=102,
                fields={
                    "pre_submit_quote_refresh_applied": True,
                    "pre_submit_quote_refresh_reason": "observer_quote_fresh",
                },
            ),
            _event("2026-05-06", "10:08:01", "order_bundle_submitted", record_id=102),
        ]
    )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    quote = report["classification"]["submit_drought_root_cause"][
        "quote_freshness_attribution"
    ]
    assert quote["latency_pass_recovered_count"] == 3
    assert quote["order_bundle_submitted_after_refresh_count"] == 1
    assert quote["latency_pass_recovered_downstream_counts"] == {
        "armed_expired_before_submit": 1,
        "order_bundle_submitted": 1,
        "price_guard_or_revalidation": 1,
    }
    assert quote["latency_pass_recovered_downstream_stage_counts"] == {
        "entry_armed_expired": 1,
        "order_bundle_submitted": 1,
        "pre_submit_price_guard_block": 1,
    }


def test_quote_not_stale_refresh_enabled_is_not_counted_as_attempt(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = [
        _event("2026-05-06", "10:00:00", "ai_confirmed", record_id=1),
        _event("2026-05-06", "10:00:10", "budget_pass", record_id=1),
        _event(
            "2026-05-06",
            "10:00:20",
            "latency_pass",
            record_id=1,
            fields={
                "pre_submit_quote_refresh_enabled": True,
                "pre_submit_quote_refresh_applied": False,
                "pre_submit_quote_refresh_reason": "quote_not_stale",
            },
        ),
    ]
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    quote = report["classification"]["submit_drought_root_cause"][
        "quote_freshness_attribution"
    ]
    assert quote["refresh_attempted_count"] == 0
    assert quote["refresh_applied_count"] == 0
    assert quote["latency_pass_recovered_count"] == 0


def test_latest_ws_snapshot_fresh_is_not_counted_as_refresh_attempt(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = [
        _event("2026-05-06", "10:00:00", "ai_confirmed", record_id=1),
        _event("2026-05-06", "10:00:10", "budget_pass", record_id=1),
        _event(
            "2026-05-06",
            "10:00:20",
            "latency_pass",
            record_id=1,
            fields={
                "pre_submit_ws_snapshot_refresh_enabled": True,
                "pre_submit_ws_snapshot_refresh_applied": False,
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
            },
        ),
    ]
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    quote = report["classification"]["submit_drought_root_cause"][
        "quote_freshness_attribution"
    ]
    assert quote["refresh_attempted_count"] == 0
    assert quote["refresh_applied_count"] == 0
    assert quote["latency_pass_recovered_count"] == 0


def test_fresh_ws_snapshot_reason_does_not_pollute_latency_danger_breakdown(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "latency_danger_reasons": "quote_stale",
                    "pre_submit_ws_snapshot_refresh_enabled": True,
                    "pre_submit_ws_snapshot_refresh_applied": False,
                    "pre_submit_ws_snapshot_refresh_reason": "latest_snapshot_fresh",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"] == {"quote_stale": 5}
    assert root_cause["quote_freshness_attribution"]["refresh_subreason_counts"] == {}
    assert root_cause["quote_freshness_attribution"]["refresh_attempted_count"] == 0


def test_input_snapshot_fresh_reason_is_report_provenance_not_unknown_workorder(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event("2026-05-06", f"10:0{idx}:00", "ai_confirmed", record_id=idx + 1)
        )
        rows.append(
            _event("2026-05-06", f"10:0{idx}:10", "budget_pass", record_id=idx + 1)
        )
        rows.append(
            _event(
                "2026-05-06",
                f"10:0{idx}:20",
                "latency_block",
                record_id=idx + 1,
                fields={
                    "reason": "latency_state_danger",
                    "pre_submit_ws_snapshot_refresh_enabled": True,
                    "pre_submit_ws_snapshot_refresh_applied": False,
                    "pre_submit_ws_snapshot_refresh_reason": "input_snapshot_fresh",
                },
            )
        )
    _write_events(tmp_path, "2026-05-06", rows)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:10:00"),
    )

    root_cause = report["classification"]["submit_drought_root_cause"]
    assert root_cause["latency_root_cause_counts"] == {
        "quote_freshness_input_snapshot_noop": 5
    }
    assert root_cause["unknown_latency_reason_count"] == 0
    assert root_cause["unknown_latency_workorder_required"] is False


def test_latency_drought_root_cause_uses_full_reason_counts_not_only_top10():
    current = {
        "latency_state_danger_events": 13,
        "latency_danger_reason_top": [
            {"label": f"quote_stale_{idx}", "count": 1} for idx in range(10)
        ],
        "latency_danger_reason_counts": {
            **{f"quote_stale_{idx}": 1 for idx in range(12)},
            "unclassified_submit_drought": 1,
        },
        "quote_freshness_refresh_attempted_count": 0,
        "quote_freshness_refresh_applied_count": 0,
        "quote_freshness_refresh_latency_pass_count": 0,
        "quote_freshness_refresh_order_bundle_submitted_count": 0,
    }

    root_cause = sentinel._latency_drought_root_cause_summary(current)

    assert root_cause["latency_root_cause_counts"]["quote_stale"] == 12
    assert root_cause["latency_root_cause_counts"]["unknown_latency_reason"] == 1
    assert root_cause["unknown_latency_workorder_required"] is True


def test_manual_and_test_events_are_excluded(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "ai_confirmed",
                name="제룡전기",
                code="033100",
                record_id=1,
            ),
            _event(
                "2026-05-06",
                "10:01:00",
                "ai_confirmed",
                name="TEST",
                code="123456",
                record_id=2,
            ),
            _event(
                "2026-05-06",
                "10:02:00",
                "ai_confirmed",
                name="정상종목",
                code="000003",
                record_id=3,
            ),
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
    _write_events(
        tmp_path, "2026-05-06", [_event("2026-05-06", "10:00:00", "ai_confirmed")]
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "10:05:00"),
    )

    assert report["policy"]["allowed_automations"] == [
        "json_report",
        "markdown_report",
        "action_recommendation",
    ]


def test_buy_funnel_sentinel_excludes_early_accel_recheck_retry_rows(
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
        rows.append(
            _event("2026-05-06", f"10:{idx:02d}:00", "ai_confirmed", record_id=idx)
        )
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

    assert report["schema_version"] == 3
    assert report["classification"]["primary"] == "UPSTREAM_AI_THRESHOLD"
    assert report["followup"]["route"] == "score65_74_counterfactual_review"
    assert report["followup"]["operator_action_required"] is False
    assert report["followup"]["runtime_effect"] == "report_only_no_mutation"


def test_before_scheduled_sentinel_start_is_not_yet_due(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-06",
        [
            _event("2026-05-06", "09:01:00", "budget_pass", record_id=1),
            _event("2026-05-06", "09:02:00", "budget_pass", record_id=2),
            _event("2026-05-06", "09:03:00", "budget_pass", record_id=3),
        ],
    )

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "09:04:59"),
    )

    assert report["classification"]["primary"] == "NOT_YET_DUE"
    assert report["classification"]["matches"] == []
    assert report["classification"]["reasons"] == [
        "sentinel session window has not opened"
    ]
    assert report["classification"]["submit_drought_handoff_state"] == "not_required"
    assert report["entry_submit_drought_contract"]["critical"] is False
    lineage = report["current"]["session"]["budget_ai_lineage"]
    assert lineage["status"] == "not_applicable_before_sentinel_start"
    assert lineage["canonical_source_state"] == (
        "instrumentation_gap_parent_ai_trace_missing"
    )
    assert report["followup"] == {
        "route": "not_yet_due",
        "owner": "scheduled_buy_funnel_sentinel",
        "operator_action_required": False,
        "runtime_effect": "report_only_no_mutation",
        "next_artifact": "buy_funnel_sentinel_in_session",
    }
    assert report["recommended_actions"] == [
        "Wait for the sentinel session window; no runtime action is required."
    ]


def test_empty_budget_ai_lineage_is_no_current_signal() -> None:
    lineage = sentinel._budget_ai_lineage_summary([])

    assert lineage["status"] == "no_current_signal"
    assert lineage["ai_trace_count"] == 0
    assert lineage["budget_or_block_event_count"] == 0
    assert lineage["lineage_contract_missing_event_count"] == 0


def test_scheduled_sentinel_start_evaluates_runtime_ops(monkeypatch, tmp_path):
    monkeypatch.setattr(sentinel, "DATA_DIR", tmp_path)

    report = sentinel.build_buy_funnel_sentinel_report(
        "2026-05-06",
        as_of=sentinel._parse_as_of("2026-05-06", "09:05:00"),
    )

    assert report["classification"]["primary"] == "RUNTIME_OPS"
    assert report["classification"]["matches"] == ["RUNTIME_OPS"]
    assert report["followup"]["route"] == "runtime_ops_playbook"
    assert report["current"]["session"]["budget_ai_lineage"]["status"] == (
        "no_current_signal"
    )


def test_followup_route_auto_handoffs_submit_drought_even_when_runtime_ops_primary():
    actions = sentinel._recommend_actions(
        {
            "primary": "RUNTIME_OPS",
            "matches": ["RUNTIME_OPS", "SUBMIT_DROUGHT_CRITICAL"],
        }
    )
    followup = sentinel._followup_route(
        {
            "primary": "RUNTIME_OPS",
            "matches": ["RUNTIME_OPS", "SUBMIT_DROUGHT_CRITICAL"],
        }
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
            _event(
                "2026-05-06",
                "10:01:00",
                "blocked_ai_score",
                record_id=2,
                fields={"score": "65"},
            ),
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
    meta_path = (
        tmp_path
        / "runtime"
        / "sentinel_event_cache"
        / "buy_funnel_sentinel_events_2026-05-06.meta.json"
    )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["cache_event_count"] == 3
    assert meta["appended_raw_lines"] == 1


def test_use_summary_counts_high_volume_blockers_and_keeps_lossless_cache_slim(
    monkeypatch, tmp_path
):
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
                fields={
                    "reason": "below_buy_ratio",
                    "buy_ratio": "0.41",
                    "strategy": "SCALP",
                },
            ),
            _event(
                "2026-05-06",
                "10:00:20",
                "blocked_strength_momentum",
                record_id=3,
                fields={
                    "reason": "below_buy_ratio",
                    "buy_ratio": "0.43",
                    "strategy": "SCALP",
                },
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
    assert (
        report["event_load"]["summary_lossless_cache_excludes_summary_stages"] is True
    )
    assert report["current"]["session"]["stage_unique"]["ai_confirmed"] == 1
    assert (
        report["current"]["session"]["stage_events"]["blocked_strength_momentum"] == 2
    )
    assert (
        report["current"]["session"]["stage_events"]["strength_momentum_observed"] == 1
    )
    assert report["current"]["session"]["blocker_top"][0] == {
        "label": "blocked_strength_momentum:below_buy_ratio",
        "count": 2,
    }

    meta_path = (
        tmp_path
        / "runtime"
        / "sentinel_event_cache"
        / "buy_funnel_sentinel_events_2026-05-06.meta.json"
    )
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


def test_summary_stage_actual_order_payload_stays_lossless_without_double_count(
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
    meta_path = (
        tmp_path
        / "runtime"
        / "sentinel_event_cache"
        / "buy_funnel_sentinel_events_2026-05-06.meta.json"
    )
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
    assert (
        "SOURCE_TAXONOMY_LEAKAGE"
        not in report["entry_submit_drought_contract"]["weak_contract_matches"]
    )
