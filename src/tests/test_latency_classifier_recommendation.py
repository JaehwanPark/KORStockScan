import json

from src.engine import latency_classifier_recommendation as mod


def _event(
    code,
    *,
    name="REAL",
    record_id=1,
    age=100,
    jitter=0,
    spread=0.001,
    quote_stale=False,
    reason="latency_fallback_deprecated",
    ai_score=82.0,
):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stage": "latency_block",
        "stock_name": name,
        "stock_code": code,
        "record_id": record_id,
        "fields": {
            "ws_age_ms": str(age),
            "ws_jitter_ms": str(jitter),
            "spread_ratio": str(spread),
            "quote_stale": str(quote_stale),
            "decision": "REJECT_MARKET_CONDITION",
            "latency": (
                "CAUTION" if reason == "latency_fallback_deprecated" else "DANGER"
            ),
            "reason": reason,
            "ai_score": str(ai_score),
            "actual_order_submitted": "false",
            "broker_order_forbidden": "true",
            "runtime_effect": "false",
        },
    }


def _counterfactual_row(
    code,
    record_id,
    *,
    outcome="MISSED_WINNER",
    close_10m_pct=2.5,
    pnl=2500,
    notional=100000,
):
    return {
        "candidate_id": f"{code}:{record_id}",
        "stock_code": code,
        "record_id": record_id,
        "terminal_stage": "latency_block",
        "outcome": outcome,
        "close_10m_pct": close_10m_pct,
        "estimated_counterfactual_pnl_10m_krw": pnl,
        "counterfactual_notional_krw": notional,
    }


def test_counterfactual_labels_prefer_full_rows(tmp_path, monkeypatch):
    monitor_dir = tmp_path / "monitor_snapshots"
    monitor_dir.mkdir()
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    (monitor_dir / "missed_entry_counterfactual_2026-07-08.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        **_counterfactual_row("111111", 1),
                        "terminal_stage": "blocked_ai_score",
                    }
                ],
                "full_rows": [_counterfactual_row("222222", 2)],
            }
        ),
        encoding="utf-8",
    )

    labels, meta = mod._load_counterfactual_labels("2026-07-08")

    assert ("222222", "2") in labels
    assert ("111111", "1") not in labels
    assert meta["row_source"] == "full_rows"
    assert meta["full_row_count"] == 1
    assert meta["display_row_count"] == 1
    assert meta["latency_block_label_count"] == 1


def test_counterfactual_labels_fallback_to_rows(tmp_path, monkeypatch):
    monitor_dir = tmp_path / "monitor_snapshots"
    monitor_dir.mkdir()
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    (monitor_dir / "missed_entry_counterfactual_2026-07-08.json").write_text(
        json.dumps({"rows": [_counterfactual_row("111111", 1)]}),
        encoding="utf-8",
    )

    labels, meta = mod._load_counterfactual_labels("2026-07-08")

    assert ("111111", "1") in labels
    assert meta["row_source"] == "rows"
    assert meta["full_row_count"] == 0
    assert meta["display_row_count"] == 1
    assert meta["latency_block_label_count"] == 1


def test_latency_classifier_recommendation_holds_after_runtime_simplification(
    tmp_path, monkeypatch
):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report"
    monitor_dir = tmp_path / "monitor_snapshots"
    event_dir.mkdir()
    monitor_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)

    rows = []
    for idx in range(24):
        rows.append(
            _event(f"10{idx:04d}", record_id=idx + 1, age=800, jitter=900, spread=0.008)
        )
    rows.append(
        _event("123456", name="TEST", record_id=999, age=800, jitter=900, spread=0.008)
    )
    (event_dir / "pipeline_events_2026-05-18.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    (monitor_dir / "missed_entry_counterfactual_2026-05-18.json").write_text(
        json.dumps(
            {
                "rows": [
                    _counterfactual_row("100000", 1, pnl=3500),
                    _counterfactual_row("100001", 2, pnl=2500),
                    _counterfactual_row("100002", 3, pnl=1500),
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = mod.write_report("2026-05-18")

    assert payload["latency_block_count"] == 24
    assert payload["profile_generation"]["mode"] == "grid_quantile_search"
    candidate = payload["calibration_candidate"]
    assert candidate["calibration_state"] == "hold"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == mod.TARGET_ENV_KEYS
    assert candidate["recommended_values"] == {
        "max_ws_age_ms_for_caution": 800,
        "max_ws_jitter_ms_for_caution": 900,
        "max_spread_ratio_for_caution": 0.008,
        "recovery_enabled": False,
        "recovery_min_signal_score": 75.0,
        "recovery_max_ws_age_ms": 800,
        "recovery_max_ws_jitter_ms": 900,
        "recovery_max_spread_ratio": 0.008,
    }
    assert "CAUTION no longer blocks submit" in candidate["calibration_reason"]
    selected = candidate["source_metrics"]["selected_profile"]
    assert selected["recommended_action"] == "bounded_apply"
    assert selected["would_pass_events"] == 0
    assert selected["would_safe_pass_events"] == 0
    assert selected["would_caution_normal_events"] == 24
    assert selected["would_recovery_canary_events"] == 24
    assert selected["counterfactual_joined_sample"] == 3
    assert selected["counterfactual_ev_pct"] == 2.5
    assert selected["missed_winner_recovered"] == 3
    assert selected["avoided_loser_lost"] == 0
    assert (report_dir / "latency_classifier_recommendation_2026-05-18.json").exists()
    assert (report_dir / "latency_classifier_recommendation_2026-05-18.md").exists()


def test_latency_classifier_recommendation_holds_when_sample_short(
    tmp_path, monkeypatch
):
    event_dir = tmp_path / "pipeline_events"
    monitor_dir = tmp_path / "monitor_snapshots"
    event_dir.mkdir()
    monitor_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    rows = [
        _event("005950", record_id=idx + 1, age=800, jitter=900, spread=0.008)
        for idx in range(3)
    ]
    (event_dir / "pipeline_events_2026-05-18.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    (monitor_dir / "missed_entry_counterfactual_2026-05-18.json").write_text(
        json.dumps(
            {"rows": [_counterfactual_row("005950", idx + 1) for idx in range(3)]}
        ),
        encoding="utf-8",
    )

    payload = mod.build_report("2026-05-18")

    assert payload["latency_block_count"] == 3
    assert (
        payload["calibration_candidate"]["source_metrics"]["selected_profile"][
            "recommended_action"
        ]
        == "reject"
    )
    assert payload["calibration_candidate"]["calibration_state"] == "hold"
    assert payload["calibration_candidate"]["allowed_runtime_apply"] is False
