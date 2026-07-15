import hashlib
import json

from src.engine import codebase_performance_workorder_report as mod


def test_codebase_performance_workorder_report_classifies_candidates(
    tmp_path, monkeypatch
):
    source_doc = tmp_path / "codebase-performance-bottleneck-analysis.md"
    source_doc.write_text("# perf report\n\ncontent", encoding="utf-8")
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "SOURCE_DOC", source_doc)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    report = mod.build_codebase_performance_workorder_report("2026-05-14")

    expected_hash = hashlib.sha256(source_doc.read_bytes()).hexdigest()
    assert report["source_doc_hash"] == expected_hash
    assert report["summary"]["accepted_count"] == 7
    assert report["summary"]["implemented_count"] >= 1
    assert report["summary"]["pending_accepted_count"] <= 6
    assert report["summary"]["deferred_count"] == 3
    assert report["summary"]["rejected_count"] == 2
    assert report["policy"]["runtime_effect"] is False
    assert report["policy"]["strategy_effect"] is False
    assert report["policy"]["data_quality_effect"] is False
    assert report["policy"]["tuning_axis_effect"] is False

    for item in report["accepted_candidates"]:
        assert item["candidate_state"] == "accepted"
        assert item["runtime_effect"] is False
        assert item["strategy_effect"] is False
        assert item["data_quality_effect"] is False
        assert item["tuning_axis_effect"] is False
        assert item["parity_contract"]
        assert item["implementation_status"] in {
            "implemented",
            "pending",
            "not_checked",
        }
        assert isinstance(item["implementation_checks"], list)
        assert "runtime_threshold_mutation" in item["forbidden_uses"]

    json_path = report_dir / "codebase_performance_workorder_2026-05-14.json"
    md_path = report_dir / "codebase_performance_workorder_2026-05-14.md"
    assert json_path.exists()
    assert md_path.exists()
    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["source_doc_hash"] == expected_hash
    markdown = md_path.read_text(encoding="utf-8")
    assert "Accepted Candidates" in markdown
    assert "order_perf_buy_funnel_json_scan" in markdown
