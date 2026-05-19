import json

from src.engine import scalp_sim_overnight as overnight


def test_build_report_counts_overnight_events(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    events_dir = data_dir / "pipeline_events"
    events_dir.mkdir(parents=True)
    target_date = "2026-05-19"
    (events_dir / f"pipeline_events_{target_date}.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "scalp_sim_overnight_decision",
                        "stock_name": "A",
                        "stock_code": "000001",
                        "emitted_at": "2026-05-19T15:31:00",
                        "fields": {
                            "sim_record_id": "SIM-A",
                            "simulation_book": "scalp_ai_buy_all",
                            "actual_order_submitted": "False",
                            "broker_order_forbidden": "True",
                            "decision_authority": "sim_observation_only",
                            "runtime_effect": "sim_observation_only",
                            "overnight_schema": "overnight_v1",
                            "ai_action": "HOLD_OVERNIGHT",
                            "ai_confidence": "80",
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_overnight_hold",
                        "stock_name": "A",
                        "stock_code": "000001",
                        "emitted_at": "2026-05-19T15:31:01",
                        "fields": {
                            "sim_record_id": "SIM-A",
                            "simulation_book": "scalp_ai_buy_all",
                            "actual_order_submitted": "False",
                            "broker_order_forbidden": "True",
                            "decision_authority": "sim_observation_only",
                            "runtime_effect": "sim_observation_only_active_carry",
                            "overnight_schema": "overnight_v1",
                            "ai_action": "HOLD_OVERNIGHT",
                            "ai_confidence": "80",
                        },
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "stage": "scalp_sim_sell_order_assumed_filled",
                        "stock_name": "B",
                        "stock_code": "000002",
                        "emitted_at": "2026-05-19T15:31:02",
                        "fields": {
                            "sim_record_id": "SIM-B",
                            "simulation_book": "scalp_ai_buy_all",
                            "exit_rule": "scalp_sim_overnight_sell_today",
                            "actual_order_submitted": "False",
                            "broker_order_forbidden": "True",
                            "profit_rate": "+0.50",
                        },
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "active_positions": [
                    {
                        "sim_record_id": "SIM-A",
                        "scalp_sim_overnight_status": "HOLD_OVERNIGHT",
                        "scalp_sim_overnight_decision_date": target_date,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(overnight, "DATA_DIR", data_dir)

    report = overnight.build_report(target_date, state_path)

    assert report["runtime_effect"] is False
    assert report["decision_authority"] == "sim_observation_only"
    assert report["summary"]["decision_target"] == 1
    assert report["summary"]["hold_overnight"] == 1
    assert report["summary"]["sell_assumed_filled"] == 1
    assert report["summary"]["carry_open_count"] == 1
    assert all(row["actual_order_submitted"] in {"False", None} for row in report["rows"])


def test_write_outputs_creates_json_and_md(tmp_path):
    report = {
        "target_date": "2026-05-19",
        "generated_at": "2026-05-19T15:31:00",
        "artifact_role": "postclose_source_packet_for_scalp_sim_overnight_ai_carry",
        "runtime_effect": False,
        "decision_authority": "sim_observation_only",
        "summary": {"decision_target": 0, "stage_counts": {}},
        "rows": [],
    }

    json_path, md_path = overnight.write_outputs(report, tmp_path)

    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["decision_authority"] == "sim_observation_only"
