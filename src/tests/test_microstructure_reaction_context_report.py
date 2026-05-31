import json

from src.engine.scalping import microstructure_reaction_context as mod


def test_microstructure_reaction_context_report_preserves_contract_and_keys(tmp_path, monkeypatch):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "microstructure_reaction_context"
    event_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    event_path = event_dir / "pipeline_events_2026-05-31.jsonl"
    event_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "ai_confirmed",
                        "stock_code": "A005930",
                        "stock_name": "Samsung",
                        "record_id": "real-1",
                        "emitted_at": "2026-05-31T09:01:00+09:00",
                        "fields": {
                            "source_event_stage": "ai_confirmed",
                            "actual_order_submitted": True,
                            "broker_order_forbidden": False,
                            "microstructure_reaction_context_version": "microstructure_reaction_context_v1",
                            "microstructure_reaction_context_status": "ok",
                            "microstructure_reaction_ask_sweep_score": 72,
                            "microstructure_reaction_post_sweep_hold_score": 68,
                            "microstructure_reaction_bid_replenishment_score": 61,
                            "microstructure_reaction_wall_replenishment_risk_score": 35,
                            "microstructure_reaction_vi_proximity_risk": 10,
                            "microstructure_reaction_entry_reaction_quality": "favorable_reaction",
                            "microstructure_reaction_source_quality": "fresh_short_window",
                            "microstructure_reaction_context_hash": "abc123",
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "blocked_liquidity",
                        "stock_code": "A000660",
                        "record_id": "probe-1",
                        "emitted_at": "2026-05-31T09:02:00+09:00",
                        "fields": {
                            "source_event_stage": "blocked_liquidity",
                            "sim_record_id": "sim-1",
                            "sim_parent_record_id": "parent-1",
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "microstructure_reaction_context_version": "microstructure_reaction_context_v1",
                            "microstructure_reaction_context_status": "stale",
                            "microstructure_reaction_ask_sweep_score": 50,
                            "microstructure_reaction_post_sweep_hold_score": 50,
                            "microstructure_reaction_bid_replenishment_score": 50,
                            "microstructure_reaction_wall_replenishment_risk_score": 50,
                            "microstructure_reaction_vi_proximity_risk": 0,
                            "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
                            "microstructure_reaction_source_quality": "stale_tick_or_quote",
                            "microstructure_reaction_context_hash": "def456",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_microstructure_reaction_context_report("2026-05-31")

    assert report["report_type"] == "microstructure_reaction_context"
    assert report["runtime_effect"] is False
    assert report["decision_authority"] == "entry_confidence_modifier_source_only"
    assert report["metric_role"] == "feature_context"
    assert report["primary_decision_metric"] == "source_quality_adjusted_ev_pct"
    assert "standalone_buy" in report["forbidden_uses"]
    assert "broker_guard_bypass" in report["forbidden_uses"]
    assert report["summary"]["row_count"] == 2
    assert report["summary"]["ok_count"] == 1
    assert report["summary"]["real_submitted_count"] == 1
    assert report["rows"][0]["stock_code"] == "005930"
    assert report["rows"][1]["sim_record_id"] == "sim-1"
    assert report["rows"][1]["sim_parent_record_id"] == "parent-1"
    assert report["rows"][1]["broker_order_forbidden"] is True
    assert (report_dir / "microstructure_reaction_context_2026-05-31.json").exists()
    assert (report_dir / "microstructure_reaction_context_2026-05-31.md").exists()
