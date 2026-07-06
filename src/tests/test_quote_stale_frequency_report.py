from __future__ import annotations

import json

from src.engine.monitoring import quote_stale_frequency_report as mod


def _event(
    stage: str,
    fields: dict,
    *,
    code: str = "000001",
    name: str = "Alpha",
    emitted_at: str = "2026-07-06T09:00:00",
):
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_code": code,
        "stock_name": name,
        "fields": fields,
        "emitted_at": emitted_at,
    }


def test_quote_stale_frequency_report_summarizes_stale_classes(monkeypatch, tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    pipeline_dir.mkdir()
    threshold_dir.mkdir()
    target_date = "2026-07-06"
    rows = [
        _event(
            "scalping_scanner_fast_precheck",
            {"quote_age_ms": "4000", "quote_age_source": "missing"},
            code="000001",
            emitted_at="2026-07-06T09:00:00",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            {"quote_age_ms": "4500", "quote_age_source": "missing"},
            code="000001",
            emitted_at="2026-07-06T09:00:01",
        ),
        _event(
            "stat_action_decision_snapshot",
            {"quote_age_ms": "5000", "quote_age_source": "last_ws_update_ts"},
            code="000002",
            name="Beta",
            emitted_at="2026-07-06T12:00:00",
        ),
        _event(
            "order_bundle_submitted",
            {"actual_order_submitted": "True", "quote_age_at_submit_ms": "100"},
            code="000003",
            name="Gamma",
            emitted_at="2026-07-06T16:10:00",
        ),
        _event(
            "scale_in_feature_context_refresh",
            {
                "scale_in_feature_refresh_attempted": "True",
                "scale_in_feature_refresh_applied": "False",
                "scale_in_feature_refresh_reason": "refreshed_feature_still_stale",
                "scale_in_feature_refresh_existing_quality": "stale",
                "scale_in_feature_refresh_new_quality": "stale",
                "scale_in_feature_refresh_existing_stale_reason": "quote_stale,quote_age_gt_max",
                "scale_in_feature_refresh_new_stale_reason": "quote_stale,tick_context_stale",
            },
            code="000004",
            name="Delta",
        ),
    ]
    (pipeline_dir / f"pipeline_events_{target_date}.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    (threshold_dir / f"threshold_events_{target_date}.jsonl").write_text("", encoding="utf-8")
    repair_log = tmp_path / "bot_history.log"
    repair_log.write_text(
        "\n".join(
            [
                "[2026-07-06 09:00:00] persistent repair no-tick cooldown entered: code=000001 attempts=3 cooldown_sec=240.0",
                "[2026-07-06 09:00:01] persistent repair 등록 제한: allowed=['000002'] skipped=['000001'] max_codes=28 ttl_sec=8.0",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", threshold_dir)
    monkeypatch.setattr(mod, "BOT_HISTORY_LOG", repair_log)

    report = mod.build_quote_stale_frequency_report(target_date)

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert "stale_quote_bypass" in report["forbidden_uses"]
    assert report["summary"]["rows_with_quote_age"] == 4
    assert report["summary"]["stale_count"] == 3
    assert report["summary"]["quote_age_source_missing_count"] == 2
    by_class = {row["class"]: row for row in report["by_class"]}
    assert by_class["scanner_watch"]["stale_count"] == 2
    assert by_class["holding_scale_input"]["stale_count"] == 1
    assert by_class["actual_submit"]["stale_count"] == 0
    assert report["top_stale_streaks"][0]["stock_code"] == "000001"
    assumptions = {
        item["topic"]: item
        for item in report["kiwoom_freshness_operating_assumptions"]
    }
    assert assumptions["subscription_item_limit"]["status"] == "official_number_not_documented"
    assert any("concurrent subscription limit" in question for question in report["kiwoom_support_questions"])
    refresh = report["scale_in_feature_context_refresh"]
    assert refresh["counts"]["total"] == 1
    assert refresh["reasons"][0] == {"key": "refreshed_feature_still_stale", "count": 1}
    assert {"key": "quote_stale", "count": 2} in refresh["stale_reason_tokens"]
    repair = report["ws_repair_log_summary"]
    assert repair["counts"]["persistent_no_tick_cooldown"] == 1
    assert repair["top_codes"]["persistent_no_tick_cooldown"][0] == {"stock_code": "000001", "count": 1}


def test_quote_stale_frequency_write_outputs(monkeypatch, tmp_path):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    pipeline_dir.mkdir()
    threshold_dir.mkdir()
    target_date = "2026-07-06"
    (pipeline_dir / f"pipeline_events_{target_date}.jsonl").write_text(
        json.dumps(
            _event("ai_holding_review", {"quote_age_ms": "1000", "quote_age_source": "last_ws_update_ts"}),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (threshold_dir / f"threshold_events_{target_date}.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "THRESHOLD_EVENTS_DIR", threshold_dir)
    monkeypatch.setattr(mod, "BOT_HISTORY_LOG", tmp_path / "missing.log")

    report = mod.build_quote_stale_frequency_report(target_date)
    json_path, md_path = mod.write_quote_stale_frequency_report(report, output_dir=tmp_path / "out")

    assert json_path.exists()
    assert md_path.exists()
    rendered = md_path.read_text(encoding="utf-8")
    assert "Quote Stale Frequency Report 2026-07-06" in rendered
    assert "runtime_effect: `False`" in rendered
    assert "## Kiwoom Freshness Operating Assumptions" in rendered
    assert "## Kiwoom Support Questions" in rendered
