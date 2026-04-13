from pathlib import Path
import sys
import types

from src.engine import log_archive_service as service


def test_monitor_snapshot_roundtrip(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)

    payload = {"date": "2026-04-06", "value": 123}
    path = service.save_monitor_snapshot("trade_review", "2026-04-06", payload)

    assert path == snapshot_dir / "trade_review_2026-04-06.json"
    assert service.load_monitor_snapshot("trade_review", "2026-04-06") == payload


def test_archive_and_replay_daily_log_slice(tmp_path, monkeypatch):
    archive_dir = tmp_path / "log_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "LOG_ARCHIVE_DIR", archive_dir)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "sniper_state_handlers_info.log"
    rotated_path = logs_dir / "sniper_state_handlers_info.log.1"

    rotated_path.write_text(
        "[2026-04-05 15:30:00] old\n"
        "[2026-04-06 09:10:00] keep [HOLDING_PIPELINE] first\n",
        encoding="utf-8",
    )
    log_path.write_text(
        "[2026-04-06 09:11:00] keep [HOLDING_PIPELINE] second\n"
        "[2026-04-07 09:00:00] future\n",
        encoding="utf-8",
    )

    archived = service.archive_target_date_logs("2026-04-06", [log_path])

    assert len(archived) == 1
    archive_path = archive_dir / "2026-04-06" / "sniper_state_handlers_info.log.gz"
    assert archive_path.exists()

    log_path.unlink()
    rotated_path.unlink()

    lines = service.iter_target_log_lines(
        [log_path],
        target_date="2026-04-06",
        marker="[HOLDING_PIPELINE]",
    )
    assert sorted(lines) == [
        "[2026-04-06 09:10:00] keep [HOLDING_PIPELINE] first",
        "[2026-04-06 09:11:00] keep [HOLDING_PIPELINE] second",
    ]


def test_save_monitor_snapshots_for_date_includes_missed_entry_counterfactual(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    report_dir = tmp_path / "server_comparison"
    report_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    checklist_path = docs_dir / "2026-04-09-stage2-todo-checklist.md"
    checklist_path.write_text(
        "### 12:00 스냅샷 기준 1차 실질 해석 (`2026-04-09 12:00 KST` 예정)\n\n"
        "## 2026-04-09 장후 체크리스트 (15:30~)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(service, "SERVER_COMPARISON_REPORT_DIR", report_dir)
    monkeypatch.setattr(service, "DOCS_DIR", docs_dir)

    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_trade_review_report",
        types.SimpleNamespace(build_trade_review_report=lambda **kwargs: {"date": kwargs["target_date"], "meta": {}}),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_performance_tuning_report",
        types.SimpleNamespace(build_performance_tuning_report=lambda **kwargs: {"date": kwargs["target_date"], "meta": {}}),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_post_sell_feedback",
        types.SimpleNamespace(build_post_sell_feedback_report=lambda **kwargs: {"date": kwargs["target_date"], "meta": {}}),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_missed_entry_counterfactual",
        types.SimpleNamespace(build_missed_entry_counterfactual_report=lambda **kwargs: {"date": kwargs["target_date"], "meta": {}}),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.buy_pause_guard",
        types.SimpleNamespace(evaluate_buy_pause_guard=lambda *args, **kwargs: {"status": "ok"}),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.server_report_comparison",
        types.SimpleNamespace(
            compare_server_reports=lambda **kwargs: {
                "date": kwargs["target_date"],
                "remote_base_url": kwargs["remote_base_url"],
                "since_time": kwargs["since_time"],
                "generated_at": "2026-04-09 12:00:05",
                "policy": {"reason": "safe only"},
                "sections": {
                    "trade_review": {
                        "label": "Trade Review",
                        "status": "ok",
                        "safe_metric_rows": [
                            {
                                "label": "completed_trades",
                                "local": 1,
                                "remote": 2,
                                "delta_remote_minus_local": 1.0,
                            }
                        ],
                    }
                },
            },
            build_snapshot_summary=lambda comparison: {
                "generated_at": comparison["generated_at"],
                "sections": [{"label": "Trade Review", "status": "ok", "differing_metric_count": 1, "top_diffs": [{"label": "completed_trades", "local": 1, "remote": 2, "delta_remote_minus_local": 1.0}]}],
            },
            render_markdown_report=lambda comparison: "# mock report\n",
            render_checklist_append_block=lambda comparison, report_relpath: "### 본서버 vs songstockscan 자동 비교\n\n- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-09.md`\n",
        ),
    )

    result = service.save_monitor_snapshots_for_date("2026-04-09")

    assert "missed_entry_counterfactual" in result
    assert "server_comparison_snapshot" in result
    assert "server_comparison_report" in result
    saved = service.load_monitor_snapshot("missed_entry_counterfactual", "2026-04-09")
    assert saved is not None
    assert saved["meta"]["snapshot_kind"] == "missed_entry_counterfactual"
    assert saved["meta"]["buy_pause_guard"] == {"status": "ok"}
    comparison_saved = service.load_monitor_snapshot("server_comparison", "2026-04-09")
    assert comparison_saved is not None
    assert comparison_saved["date"] == "2026-04-09"
    assert (report_dir / "server_comparison_2026-04-09.md").exists()
    updated_checklist = checklist_path.read_text(encoding="utf-8")
    assert "본서버 vs songstockscan 자동 비교" in updated_checklist
