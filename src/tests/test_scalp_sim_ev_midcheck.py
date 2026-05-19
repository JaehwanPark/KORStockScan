import json

import src.engine.scalp_sim_ev_midcheck as midcheck


def _event(stage, sim_id, *, name="Alpha", code="111111", fields=None, emitted_at=None):
    payload = {
        "stage": stage,
        "stock_name": name,
        "stock_code": code,
        "fields": {
            "simulation_book": "scalp_ai_buy_all",
            "sim_record_id": sim_id,
            "actual_order_submitted": "False",
            **(fields or {}),
        },
        "emitted_at": emitted_at or "2026-05-11T10:00:00",
    }
    return payload


def test_scalp_sim_midcheck_splits_exit_only_avg_down_pyramid_and_order_check(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    event_dir = data_dir / "pipeline_events"
    event_dir.mkdir(parents=True)
    target_date = "2026-05-11"
    path = event_dir / f"pipeline_events_{target_date}.jsonl"
    rows = [
        _event(
            "scalp_sim_entry_armed",
            "SIM-EXIT",
            fields={"qty": "10", "uncapped_qty": "10", "qty_source": "uncapped_buy_capacity", "cap_applied": "False"},
            emitted_at="2026-05-11T10:00:00",
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "SIM-EXIT",
            fields={"profit_rate": "+1.00", "exit_rule": "tp"},
            emitted_at="2026-05-11T10:05:00",
        ),
        _event("scalp_sim_entry_armed", "SIM-AVG", name="Beta", code="222222", emitted_at="2026-05-11T10:10:00"),
        _event(
            "scalp_sim_scale_in_order_assumed_filled",
            "SIM-AVG",
            name="Beta",
            code="222222",
            fields={"add_type": "AVG_DOWN", "qty": "3", "would_qty": "3", "effective_qty": "3"},
            emitted_at="2026-05-11T10:11:00",
        ),
        _event(
            "scalp_sim_probe_after_add",
            "SIM-AVG",
            name="Beta",
            code="222222",
            fields={"profit_rate": "+0.25"},
            emitted_at="2026-05-11T10:12:00",
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "SIM-AVG",
            name="Beta",
            code="222222",
            fields={"profit_rate": "-0.50", "exit_rule": "hard_stop"},
            emitted_at="2026-05-11T10:15:00",
        ),
        _event("scalp_sim_entry_armed", "SIM-PYR", name="Gamma", code="333333", emitted_at="2026-05-11T10:20:00"),
        _event(
            "scalp_sim_scale_in_order_assumed_filled",
            "SIM-PYR",
            name="Gamma",
            code="333333",
            fields={"add_type": "PYRAMID", "qty": "4", "would_qty": "4", "effective_qty": "4"},
            emitted_at="2026-05-11T10:21:00",
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "SIM-PYR",
            name="Gamma",
            code="333333",
            fields={"profit_rate": "+2.00", "exit_rule": "trailing"},
            emitted_at="2026-05-11T10:30:00",
        ),
        _event("scalp_sim_entry_armed", "SIM-UNFILLED", name="Delta", code="444444", emitted_at="2026-05-11T10:40:00"),
        _event(
            "scalp_sim_scale_in_order_unfilled",
            "SIM-UNFILLED",
            name="Delta",
            code="444444",
            fields={"add_type": "PYRAMID", "qty": "2", "would_qty": "2", "effective_qty": "2"},
            emitted_at="2026-05-11T10:41:00",
        ),
        _event(
            "scalp_sim_sell_order_assumed_filled",
            "SIM-UNFILLED",
            name="Delta",
            code="444444",
            fields={"profit_rate": "+0.10", "exit_rule": "timeout"},
            emitted_at="2026-05-11T10:45:00",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(midcheck, "DATA_DIR", data_dir)

    report = midcheck.build_report(target_date)
    analysis = report["scale_in_analysis"]

    assert analysis["arm_metrics"]["exit_only"]["sample"] == 2
    assert analysis["arm_metrics"]["avg_down"]["sample"] == 1
    assert analysis["arm_metrics"]["pyramid"]["sample"] == 1
    assert analysis["scale_in_counts"]["positions_with_scale_in"] == 2
    assert analysis["scale_in_counts"]["positions_without_scale_in"] == 2
    assert analysis["scale_in_counts"]["filled_by_add_type"] == {"AVG_DOWN": 1, "PYRAMID": 1}
    assert analysis["scale_in_counts"]["unfilled_by_add_type"] == {"PYRAMID": 1}
    assert analysis["actual_order_submission_check"]["passed"] is True

    avg_down_row = next(row for row in analysis["positions"] if row["sim_record_id"] == "SIM-AVG")
    assert avg_down_row["mfe_after_add_pct"] == 0.25
    assert avg_down_row["mae_after_add_pct"] == -0.5
    assert avg_down_row["final_exit_profit_pct"] == -0.5

    qty_provenance = report["initial_qty_provenance"]
    assert qty_provenance["method"] == "actual_sim_qty_provenance_only"
    assert qty_provenance["summary"]["sample"] == 4
    assert qty_provenance["summary"]["cap_applied_count"] == 0
    assert qty_provenance["summary"]["uncapped_qty_source_count"] == 1
    exit_qty = next(row for row in qty_provenance["positions"] if row["sim_record_id"] == "SIM-EXIT")
    assert exit_qty["sim_qty"] == 10
    assert exit_qty["uncapped_qty"] == 10
    assert "one_share_pnl_krw" not in exit_qty


def test_scalp_sim_midcheck_summarizes_ai_budget_critical_classes(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    event_dir = data_dir / "pipeline_events"
    event_dir.mkdir(parents=True)
    target_date = "2026-05-11"
    path = event_dir / f"pipeline_events_{target_date}.jsonl"
    rows = [
        _event(
            "scalp_sim_ai_holding_live_call",
            "SIM-HARD",
            fields={
                "critical_class": "hard_critical",
                "critical_reason": "hard_loss",
            },
        ),
        _event(
            "scalp_sim_ai_holding_deferred",
            "SIM-SOFT",
            fields={
                "critical_class": "soft_critical",
                "critical_reason": "soft_loss,feature_signature_changed",
            },
        ),
        _event(
            "sim_ai_critical_bypass",
            "SIM-HARD",
            fields={
                "critical_class": "hard_critical",
                "critical_reason": "hard_loss",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(midcheck, "DATA_DIR", data_dir)

    report = midcheck.build_report(target_date)
    budget = report["sim_ai_budget_counts"]

    assert budget["scalp_sim_ai_holding_live_call"] == 1
    assert budget["scalp_sim_ai_holding_deferred"] == 1
    assert budget["sim_ai_critical_bypass"] == 1
    assert budget["critical_class_counts"] == {"hard_critical": 1, "soft_critical": 1}
    assert budget["critical_reason_counts"] == {
        "feature_signature_changed": 1,
        "hard_loss": 1,
        "soft_loss": 1,
    }
    assert budget["critical_bypass_ratio_pct"] == 100.0
    assert budget["deferred_ratio_pct"] == 50.0
