import json
from pathlib import Path

from src.engine.scalping import ai_input_quality_baseline_replay as mod


def _event(
    stage,
    *,
    code="005930",
    emitted_at="2026-07-23T10:00:00",
    fields=None,
):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_code": code,
        "emitted_at": emitted_at,
        "emitted_date": emitted_at[:10],
        "fields": fields or {},
    }


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_audit(path: Path, *, allowed=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "warning",
                "generated_at": "2026-07-23T20:00:00+09:00",
                "summary": {
                    "event_count": 10,
                    "hard_blocking_contract_gap_count": 0,
                    "review_warning_count": 1,
                    "tuning_input_allowed": allowed,
                },
            }
        ),
        encoding="utf-8",
    )


def _clean_policy():
    return {
        "enabled": True,
        "clean_tuning_baseline_date": "2026-06-04",
        "clean_tuning_baseline_ts_kst": "2026-06-04T14:29:09+09:00",
    }


def test_replay_keeps_legacy_proxy_separate_from_exact_provenance(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                fields={
                    "rising_missed_effective_venue": "KRX",
                    "rising_missed_market_session_bucket": "krx_regular",
                    "entry_context_quality": "fresh_consistent",
                    "quote_stale": False,
                    "ai_result_source": "live",
                    "ai_response_ms": 100,
                },
            )
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    assert payload["status"] == "ready_baseline_v1"
    assert payload["historical_exact_provenance_row_count"] == 0
    assert payload["can_open_order_authority"] is False
    assert payload["validation_summary"]["venue_attributed_real_row_count"] == 1
    row = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "KRX" and item["decision_point"] == "entry_screen"
    )
    assert row["policy_state"] == "legacy_proxy_observed_not_exact"
    assert row["legacy_proxy_allowed_count"] == 1
    assert row["exact_provenance"] is False


def test_blocked_historical_input_records_provider_call_leak(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "ai_holding_review",
                fields={
                    "rising_missed_effective_venue": "NXT",
                    "rising_missed_market_session_bucket": "nxt_aftermarket",
                    "holding_score_data_quality": "insufficient",
                    "holding_score_effective_usable": False,
                    "ai_result_source": "live",
                    "ai_response_ms": 700,
                },
            )
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    row = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "NXT_AFTERMARKET"
        and item["decision_point"] == "holding_score"
    )
    assert row["legacy_proxy_blocked_count"] == 1
    assert row["provider_called_while_blocked_count"] == 1


def test_holding_row_uses_only_same_day_symbol_lineage_proxy(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-22.jsonl",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                emitted_at="2026-07-22T10:00:00",
                fields={
                    "rising_missed_effective_venue": "KRX",
                    "entry_context_quality": "fresh",
                },
            )
        ],
    )
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "ai_holding_review",
                fields={
                    "holding_score_data_quality": "full",
                    "holding_score_effective_usable": True,
                },
            )
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    unknown = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "UNKNOWN" and item["decision_point"] == "holding_score"
    )
    assert unknown["legacy_proxy_blocked_count"] == 1
    assert unknown["quality_reasons"]["venue_lineage_unavailable"] == 1


def test_sor_order_route_is_attributed_inside_krx_cohort(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "probe_submitted",
                fields={
                    "post_probe_direction_effective_venue": "KRX",
                    "post_probe_direction_market_session_bucket": "krx_regular",
                    "post_probe_live_micro_fresh": True,
                },
            ),
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "order_leg_sent",
                "stock_code": "005930",
                "emitted_at": "2026-07-23T10:00:01",
                "emitted_date": "2026-07-23",
                "fields": {
                    "stock_code": "005930",
                    "effective_dmst_stex_tp": "SOR",
                },
            },
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    krx = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "KRX" and item["decision_point"] == "post_probe"
    )
    overnight = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "OVERNIGHT" and item["decision_point"] == "overnight"
    )
    assert all(item["cohort"] != "SOR" for item in payload["venue_decision_matrix"])
    assert krx["broker_route_counts"] == {"SOR": 1}
    assert krx["broker_route_sources"] == {"same_day_symbol_unique_order_route": 1}
    assert (
        overnight["policy_state"] == "restrictive_only_no_real_reconciliation_evidence"
    )


def test_source_quality_audit_failure_keeps_artifact_not_ready(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "probe_submitted",
                fields={
                    "post_probe_direction_effective_venue": "KRX",
                    "post_probe_live_micro_fresh": True,
                },
            )
        ],
    )
    _write_audit(
        audit_dir / "observation_source_quality_audit_2026-07-23.json",
        allowed=False,
    )

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    assert payload["status"] == "not_ready"
    assert payload["allowed_runtime_apply"] is False
    assert "source_quality_audit_not_allowed" in payload["readiness_blockers"]


def test_prebaseline_rows_are_excluded(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-06-04.jsonl",
        [
            _event(
                "probe_submitted",
                emitted_at="2026-06-04T14:00:00",
                fields={"post_probe_direction_effective_venue": "KRX"},
            )
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    assert payload["eligible_real_row_count"] == 0
    assert payload["status"] == "not_ready"
    assert "no_clean_baseline_real_ai_input_rows" in payload["readiness_blockers"]


def test_nxt_without_session_is_not_inferred_as_regular_overlap(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "probe_submitted",
                fields={
                    "post_probe_direction_effective_venue": "NXT",
                    "post_probe_live_micro_fresh": True,
                },
            )
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    unknown = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "UNKNOWN" and item["decision_point"] == "post_probe"
    )
    assert unknown["real_row_count"] == 1
    assert unknown["venue_lineage_sources"]["explicit_nxt_session_missing"] == 1


def test_explicit_nxt_entry_window_uses_clock_only_for_session_split(tmp_path):
    events_dir = tmp_path / "events"
    audit_dir = tmp_path / "audit"
    _write_jsonl(
        events_dir / "pipeline_events_2026-07-23.jsonl",
        [
            _event(
                "probe_submitted",
                code="005930",
                emitted_at="2026-07-23T10:00:00",
                fields={
                    "post_probe_direction_effective_venue": "NXT",
                    "post_probe_direction_market_session_bucket": "nxt_entry_window",
                    "post_probe_live_micro_fresh": True,
                },
            ),
            _event(
                "probe_submitted",
                code="000660",
                emitted_at="2026-07-23T18:00:00",
                fields={
                    "post_probe_direction_effective_venue": "NXT",
                    "post_probe_direction_market_session_bucket": "nxt_entry_window",
                    "post_probe_live_micro_fresh": True,
                },
            ),
        ],
    )
    _write_audit(audit_dir / "observation_source_quality_audit_2026-07-23.json")

    payload = mod.build_baseline_policy(
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
        source_audit_dir=audit_dir,
        clean_policy=_clean_policy(),
    )

    regular = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "NXT_REGULAR_OVERLAP"
        and item["decision_point"] == "post_probe"
    )
    after = next(
        item
        for item in payload["venue_decision_matrix"]
        if item["cohort"] == "NXT_AFTERMARKET"
        and item["decision_point"] == "post_probe"
    )
    assert regular["real_row_count"] == 1
    assert after["real_row_count"] == 1
    assert after["venue_lineage_sources"]["explicit_venue_session_clock"] == 1


def test_plain_pipeline_file_wins_over_same_date_gzip(tmp_path):
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    plain = events_dir / "pipeline_events_2026-07-23.jsonl"
    zipped = events_dir / "pipeline_events_2026-07-23.jsonl.gz"
    plain.write_text("", encoding="utf-8")
    zipped.write_bytes(b"not-a-gzip-stream")

    paths = mod._pipeline_paths(
        baseline_date="2026-06-04",
        target_date="2026-07-23",
        pipeline_events_dir=events_dir,
    )

    assert paths == [plain]
