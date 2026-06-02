from __future__ import annotations

import json
import gzip

from src.engine.automation import producer_gap_source_bundle as bundle


def test_producer_gap_source_bundle_emits_source_only_sections(monkeypatch, tmp_path):
    monkeypatch.setattr(bundle, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(bundle, "OUT_DIR", tmp_path / "report" / "producer_gap_source_bundle")
    monkeypatch.setattr(bundle, "POST_SELL_DIR", tmp_path / "post_sell")
    (tmp_path / "post_sell").mkdir(parents=True)
    (tmp_path / "post_sell" / "sim_post_sell_evaluations_2026-05-27.jsonl").write_text(
        json.dumps(
            {
                "sim_record_id": "sim-1",
                "code": "005930",
                "stage": "sim_scale_in",
                "would_add": True,
                "assumed_filled": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = bundle.build_producer_gap_source_bundle("2026-05-27")

    sections = {item["section_id"]: item for item in report["sections"]}
    assert sections["sim_scale_in_would_add_counterfactual"]["source_quality_status"] == "implemented"
    assert sections["sim_scale_in_would_add_counterfactual"]["runtime_effect"] is False
    assert sections["sim_scale_in_would_add_counterfactual"]["broker_order_forbidden"] is True
    assert sections["swing_sim_probe_label_gap"]["source_quality_status"] == "implemented_but_hold_sample"


def test_producer_gap_source_bundle_covers_entry_selection_and_missed_fill(monkeypatch, tmp_path):
    monkeypatch.setattr(bundle, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(bundle, "OUT_DIR", tmp_path / "report" / "producer_gap_source_bundle")
    monkeypatch.setattr(bundle, "POST_SELL_DIR", tmp_path / "post_sell")
    (tmp_path / "post_sell").mkdir(parents=True)
    (tmp_path / "post_sell" / "sim_post_sell_candidates_2026-05-27.jsonl").write_text(
        json.dumps(
            {
                "sim_record_id": "sim-entry-1",
                "candidate_id": "cand-1",
                "code": "005930",
                "score": 71,
                "profit_rate": 0.4,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    ldm_dir = tmp_path / "report" / "lifecycle_decision_matrix"
    ldm_dir.mkdir(parents=True)
    (ldm_dir / "lifecycle_decision_matrix_2026-05-27.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "sim_record_id": "sim-fill-1",
                        "code": "005930",
                        "submit_time": "09:05:00",
                        "fill_quality": "missed_fill",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = bundle.build_producer_gap_source_bundle("2026-05-27")

    sections = {item["section_id"]: item for item in report["sections"]}
    assert sections["sim_entry_selection_bucket_producer"]["source_quality_status"] == "implemented"
    assert sections["missed_fill_recovery_counterfactual"]["source_quality_status"] == "implemented"
    assert sections["sim_entry_selection_bucket_producer"]["runtime_effect"] is False
    assert sections["missed_fill_recovery_counterfactual"]["allowed_runtime_apply"] is False


def test_producer_gap_source_bundle_reads_jsonl_gzip_sibling(monkeypatch, tmp_path):
    monkeypatch.setattr(bundle, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(bundle, "OUT_DIR", tmp_path / "report" / "producer_gap_source_bundle")
    monkeypatch.setattr(bundle, "POST_SELL_DIR", tmp_path / "post_sell")
    (tmp_path / "post_sell").mkdir(parents=True)
    gz_path = tmp_path / "post_sell" / "sim_post_sell_evaluations_2026-05-27.jsonl.gz"
    with gzip.open(gz_path, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "sim_record_id": "sim-2",
                    "code": "005930",
                    "stage": "sim_stop",
                    "stop": True,
                    "recovery": True,
                    "sim": True,
                }
            )
            + "\n"
        )

    report = bundle.build_producer_gap_source_bundle("2026-05-27")

    sections = {item["section_id"]: item for item in report["sections"]}
    stop_section = sections["sim_stop_recovery_counterfactual"]
    assert stop_section["source_quality_status"] == "implemented"
    assert stop_section["source_paths"] == [str(gz_path)]
    assert report["sources"]["sim_post_sell_evaluations"] == str(gz_path)


def test_producer_gap_source_bundle_covers_volatile_runner_exit_counterfactual(monkeypatch, tmp_path):
    monkeypatch.setattr(bundle, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(bundle, "OUT_DIR", tmp_path / "report" / "producer_gap_source_bundle")
    monkeypatch.setattr(bundle, "POST_SELL_DIR", tmp_path / "post_sell")
    (tmp_path / "post_sell").mkdir(parents=True)
    (tmp_path / "post_sell" / "sim_post_sell_candidates_2026-05-27.jsonl").write_text(
        json.dumps(
            {
                "recommendation_id": "rec-1",
                "sim_parent_record_id": "real-1",
                "record_id": "sim-1",
                "code": "005930",
                "runner": True,
                "post_exit_mfe": 4.2,
                "peak_drawdown": -0.4,
                "holding_flow_override_state": "runner",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = bundle.build_producer_gap_source_bundle("2026-05-27")

    sections = {item["section_id"]: item for item in report["sections"]}
    volatile = sections["volatile_runner_exit_counterfactual"]
    assert volatile["pattern_type"] == "volatile_runner_exit_counterfactual_missing"
    assert volatile["source_quality_status"] == "implemented"
    assert volatile["runtime_effect"] is False
    assert volatile["allowed_runtime_apply"] is False
    assert volatile["broker_order_forbidden"] is True
