import json

from src.engine.monitoring import intraday_ws_freshness_monitor as mod


def _event(stage, fields, *, code="000001", emitted_at="2026-07-13T09:10:00+09:00"):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_code": code,
        "stock_name": f"NAME{code}",
        "emitted_at": emitted_at,
        "fields": fields,
    }


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_build_report_splits_subscription_stale_from_trade_tick_quiet(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-13.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-13.jsonl"
    snapshot_path = tmp_path / "ws_snapshot.json"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "ws_last_0b_age_ms": "50000",
                    "ws_last_0d_age_ms": "4000",
                    "source_quality_block_reason": "trade_tick_quiet",
                },
                code="000101",
            ),
            _event(
                "ws_subscription_freshness_snapshot",
                {
                    "freshness_state": "stale",
                    "repair_recommended": "true",
                    "repair_reason": "subscription_stale",
                    "ws_last_0b_age_ms": "61000",
                    "ws_last_0d_age_ms": "61000",
                },
                code="000202",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])
    snapshot_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "stock_code": "000101",
                        "freshness_state": "fresh",
                        "trade_tick_quiet": True,
                        "last_0b_age_sec": 50.0,
                        "last_0d_age_sec": 4.0,
                        "last_trade_cum_volume": 1234,
                        "repair_recommended": False,
                        "repair_reason": "none",
                    },
                    {
                        "stock_code": "000202",
                        "freshness_state": "stale",
                        "repair_recommended": True,
                        "repair_reason": "subscription_stale",
                        "last_receive_age_sec": 61.0,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        subscription_snapshot_path=snapshot_path,
        generated_at="fixed",
    )

    assert report["metric_contract"]["runtime_effect"] is False
    assert report["pipeline_counts"]["trade_tick_quiet"] == 1
    assert report["pipeline_counts"]["subscription_stale"] == 1
    assert report["pipeline_counts"]["both_ws_stale"] == 1
    assert report["pipeline_counts"]["fresh_0d_stale_0b"] == 1
    assert report["snapshot_summary"]["trade_tick_quiet_count"] == 1
    assert report["snapshot_summary"]["repair_recommended_count"] == 1
    order_ids = {item["order_id"] for item in report["workorder_directives"]}
    assert "order_ws_subscription_stale_repair_observability" in order_ids
    assert "order_ws_trade_tick_quiet_low_liquidity_classification" in order_ids
    assert "order_ws_total_stale_escalation" in order_ids
    assert all(item["runtime_effect"] is False for item in report["workorder_directives"])
    assert all(item["allowed_runtime_apply"] is False for item in report["workorder_directives"])


def test_build_report_surfaces_provider_none_as_separate_incident(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-13.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-13.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "ai_confirmed",
                {
                    "ai_provider": "none",
                },
            )
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["pipeline_counts"]["provider_none"] == 1
    assert report["pipeline_counts"].get("both_ws_stale", 0) == 0
    assert report["workorder_summary"]["provider_none_incident_count"] == 1
    assert {
        item["order_id"] for item in report["workorder_directives"]
    } == {"order_ai_provider_none_intraday_incident"}


def test_write_report_outputs_monitor_and_workorder_files(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "monitor")
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", tmp_path / "workorder-report")
    monkeypatch.setattr(mod, "WORKORDER_DOC_DIR", tmp_path / "workorder-docs")
    report = {
        "target_date": "2026-07-13",
        "pipeline_event_count": 0,
        "pipeline_counts": {},
        "pipeline_rates": {},
        "snapshot_summary": {},
        "source_missing": [],
        "workorder_directives": [],
        "workorder_summary": {"selected_order_count": 0},
    }

    monitor_json, monitor_md, workorder_json, workorder_md = mod.write_report(report)

    assert monitor_json.exists()
    assert monitor_md.exists()
    assert workorder_json.exists()
    assert workorder_md.exists()
    payload = json.loads(workorder_json.read_text(encoding="utf-8"))
    assert payload["metric_contract"]["decision_authority"] == "ws_freshness_intraday_monitor_source_only"
    assert payload["summary"]["selected_order_count"] == 0


def test_write_report_monitor_only_skips_workorder_files(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "monitor")
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", tmp_path / "workorder-report")
    monkeypatch.setattr(mod, "WORKORDER_DOC_DIR", tmp_path / "workorder-docs")
    report = {
        "target_date": "2026-07-13",
        "pipeline_event_count": 0,
        "pipeline_counts": {},
        "pipeline_rates": {},
        "snapshot_summary": {},
        "source_missing": [],
        "workorder_directives": [],
        "workorder_summary": {"selected_order_count": 0},
    }

    monitor_json, monitor_md, workorder_json, workorder_md = mod.write_report(report, monitor_only=True)

    assert monitor_json.exists()
    assert monitor_md.exists()
    assert workorder_json is None
    assert workorder_md is None
    assert not (tmp_path / "workorder-report").exists()
    assert not (tmp_path / "workorder-docs").exists()
