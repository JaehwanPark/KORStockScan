import json

from src.tests import bedrock_nova_lite_v2_shadow_report as mod


def test_lite_v2_shadow_report_summarizes_v1_v2_rows(tmp_path, monkeypatch):
    report_dir = tmp_path / "bedrock_nova_lite_v2_shadow"
    report_dir.mkdir()
    path = report_dir / "bedrock_nova_lite_v2_shadow_2026-05-26.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "endpoint_name": "holding_flow",
                        "baseline_action": "HOLD",
                        "candidate_action": "HOLD",
                        "v1_v2_action_match": True,
                        "v2_parse_ok": True,
                        "v2_latency_ms": 123,
                        "baseline_bedrock_model_id": "apac.amazon.nova-lite-v1:0",
                        "candidate_bedrock_model_id": "global.amazon.nova-2-lite-v1:0",
                    }
                ),
                json.dumps(
                    {
                        "endpoint_name": "entry_price",
                        "baseline_action": "USE_DEFENSIVE",
                        "candidate_action": "SKIP",
                        "v1_v2_action_match": False,
                        "v2_parse_ok": True,
                        "v2_latency_ms": 200,
                        "baseline_bedrock_model_id": "apac.amazon.nova-lite-v1:0",
                        "candidate_bedrock_model_id": "global.amazon.nova-2-lite-v1:0",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    report = mod.build_report("2026-05-26")

    assert report["summary"]["row_count"] == 2
    assert report["summary"]["parse_ok_rate"] == 1.0
    assert report["summary"]["v1_v2_action_match_rate"] == 0.5
    assert report["endpoint_counts"] == {"holding_flow": 1, "entry_price": 1}
