import gzip
import json
from pathlib import Path
import sys
import types

from src.engine import log_archive_service as service
from src.engine import monitor_snapshot_runtime as runtime
from src.engine.notify_monitor_snapshot_admin import _build_message, _load_json_line


def test_monitor_snapshot_roundtrip(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    payload = {"date": "2026-04-06", "value": 123}
    path = service.save_monitor_snapshot("trade_review", "2026-04-06", payload)

    assert path == snapshot_dir / "trade_review_2026-04-06.json"
    loaded = service.load_monitor_snapshot("trade_review", "2026-04-06")
    assert loaded is not None
    assert loaded == payload


def test_load_monitor_snapshot_reads_gzip_file(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)

    payload = {"date": "2026-04-06", "value": 456}
    with gzip.open(
        snapshot_dir / "trade_review_2026-04-06.json.gz", "wt", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle)

    loaded = service.load_monitor_snapshot("trade_review", "2026-04-06")

    assert loaded == payload


def test_notify_monitor_snapshot_admin_builds_cutoff_message(tmp_path):
    result_file = tmp_path / "snapshot.out"
    result_file.write_text(
        "noise\n"
        '{"target_date":"2026-04-22","profile":"full","snapshots":{"profile":"full","trend_max_dates":"12","trade_review":"data/report/monitor_snapshots/trade_review_2026-04-22.json","performance_tuning":"data/report/monitor_snapshots/performance_tuning_2026-04-22.json","snapshot_manifest":"data/report/monitor_snapshots/manifests/monitor_snapshot_manifest_2026-04-22_full.json","server_comparison_status":"policy_disabled"}}\n',
        encoding="utf-8",
    )

    payload = _load_json_line(result_file)
    message = _build_message(
        payload,
        target_date="2026-04-22",
        profile="full",
        log_file="logs/run_monitor_snapshot.log",
    )

    assert "snapshot_count: 2" in message
    assert "trend_max_dates: 12" in message
    assert "max_date_basis: 2026-04-22" in message
    assert "server_comparison: policy_disabled" in message
    assert "next_prompt_hint:" in message


def test_monitor_snapshot_runtime_load_json_line_reads_tail(tmp_path):
    result_file = tmp_path / "snapshot.out"
    result_file.write_text(
        '{"status":"old","value":1}\n' "noise\n" '{"status":"latest","value":2}\n',
        encoding="utf-8",
    )

    payload = runtime.load_json_line(result_file)

    assert payload == {"status": "latest", "value": 2}


def test_notify_monitor_snapshot_admin_builds_skipped_message():
    message = _build_message(
        {
            "target_date": "2026-04-22",
            "skipped": True,
            "reason": "lock_busy",
            "lock_file": "tmp/run_monitor_snapshot.lock",
        },
        target_date="2026-04-22",
        profile="full",
        log_file="logs/run_monitor_snapshot.log",
    )

    assert "monitor snapshot skipped" in message
    assert "reason: lock_busy" in message
    assert "lock_file: tmp/run_monitor_snapshot.lock" in message


def test_normalize_result_payload_detects_cooldown_skip():
    payload = runtime.normalize_result_payload(
        target_date="2026-04-24",
        profile="intraday_light",
        output_text="[SKIP] snapshot cooldown active for intraday_light (remaining=30s) target_date=2026-04-24",
    )

    assert payload["status"] == "skipped"
    assert payload["reason"] == "cooldown_active"
    assert (
        "중복 실행" in payload["next_prompt_hint"]
        or "기존 결과" in payload["next_prompt_hint"]
    )


def test_dispatch_monitor_snapshot_job_disables_admin_notice_by_default(
    tmp_path, monkeypatch
):
    captured = {}

    def fake_run(cmd, cwd, env, text, capture_output, check):
        captured["cmd"] = cmd
        captured["env"] = env
        return types.SimpleNamespace(
            returncode=0,
            stdout=(
                "[INFO] monitor snapshot async response status=dispatched "
                "date=2026-04-24 profile=full worker_pid=123 output_file=/tmp/snapshot.out\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runtime, "completion_artifact_path", lambda *args: tmp_path / "completion.json"
    )
    monkeypatch.setattr(
        runtime, "write_completion_artifact", lambda *args, **kwargs: None
    )

    result = runtime.dispatch_monitor_snapshot_job(
        target_date="2026-04-24", profile="full"
    )

    assert captured["env"]["MONITOR_SNAPSHOT_NOTIFY_ADMIN"] == "0"
    assert result["status"] == "dispatched"
    assert "completion artifact" in result["next_prompt_hint"]


def test_completion_artifact_roundtrip(tmp_path):
    artifact_path = tmp_path / "monitor_snapshot_completion_2026-04-24_full.json"
    payload = {
        "status": "dispatched",
        "target_date": "2026-04-24",
        "profile": "full",
        "next_prompt_hint": "completion artifact를 확인하세요.",
    }
    runtime.write_completion_artifact(artifact_path, payload)

    loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert loaded["status"] == "dispatched"
    assert loaded["next_prompt_hint"] == "completion artifact를 확인하세요."


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


def test_save_monitor_snapshots_for_date_includes_missed_entry_counterfactual(
    tmp_path, monkeypatch
):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
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
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(service, "SERVER_COMPARISON_REPORT_DIR", report_dir)
    monkeypatch.setattr(service, "DOCS_DIR", docs_dir)
    monkeypatch.setenv("KORSTOCKSCAN_ENABLE_SERVER_COMPARISON", "1")

    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_trade_review_report",
        types.SimpleNamespace(
            build_trade_review_report=lambda **kwargs: {
                "date": kwargs["target_date"],
                "meta": {},
            }
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_performance_tuning_report",
        types.SimpleNamespace(
            build_performance_tuning_report=lambda **kwargs: {
                "date": kwargs["target_date"],
                "meta": {},
            }
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_post_sell_feedback",
        types.SimpleNamespace(
            build_post_sell_feedback_report=lambda **kwargs: {
                "date": kwargs["target_date"],
                "meta": {},
            }
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_missed_entry_counterfactual",
        types.SimpleNamespace(
            build_missed_entry_counterfactual_report=lambda **kwargs: {
                "date": kwargs["target_date"],
                "meta": {},
            }
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.holding_exit_observation_report",
        types.SimpleNamespace(
            build_holding_exit_observation_report=lambda **kwargs: {
                "date": kwargs["target_date"],
                "meta": {},
            }
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.wait6579_ev_cohort_report",
        types.SimpleNamespace(
            build_wait6579_ev_cohort_report=lambda **kwargs: {
                "date": kwargs["target_date"],
                "meta": {},
            }
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.engine.buy_pause_guard",
        types.SimpleNamespace(
            evaluate_buy_pause_guard=lambda *args, **kwargs: {"status": "ok"}
        ),
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
                "sections": [
                    {
                        "label": "Trade Review",
                        "status": "ok",
                        "differing_metric_count": 1,
                        "top_diffs": [
                            {
                                "label": "completed_trades",
                                "local": 1,
                                "remote": 2,
                                "delta_remote_minus_local": 1.0,
                            }
                        ],
                    }
                ],
            },
            render_markdown_report=lambda comparison: "# mock report\n",
            render_checklist_append_block=lambda comparison, report_relpath: "### 본서버 vs songstockscan 자동 비교\n\n- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-09.md`\n",
        ),
    )

    result = service.save_monitor_snapshots_for_date("2026-04-09")

    assert "missed_entry_counterfactual" in result
    assert "holding_exit_observation" in result
    assert "wait6579_ev_cohort" in result
    assert "add_blocked_lock" not in result
    assert "snapshot_manifest" in result
    assert "server_comparison_snapshot" in result
    assert "server_comparison_report" in result
    saved = service.load_monitor_snapshot("missed_entry_counterfactual", "2026-04-09")
    assert saved is not None
    assert saved["meta"]["snapshot_kind"] == "missed_entry_counterfactual"
    assert saved["meta"]["buy_pause_guard"] == {"status": "ok"}
    holding_exit_saved = service.load_monitor_snapshot(
        "holding_exit_observation", "2026-04-09"
    )
    assert holding_exit_saved is not None
    assert holding_exit_saved["meta"]["snapshot_kind"] == "holding_exit_observation"
    assert holding_exit_saved["meta"]["buy_pause_guard"] == {"status": "ok"}
    wait6579_saved = service.load_monitor_snapshot("wait6579_ev_cohort", "2026-04-09")
    assert wait6579_saved is not None
    assert wait6579_saved["meta"]["snapshot_kind"] == "wait6579_ev_cohort"
    assert wait6579_saved["meta"]["buy_pause_guard"] == {"status": "ok"}
    comparison_saved = service.load_monitor_snapshot("server_comparison", "2026-04-09")
    assert comparison_saved is not None
    assert comparison_saved["date"] == "2026-04-09"
    manifest_payload = json.loads(
        Path(result["snapshot_manifest"]).read_text(encoding="utf-8")
    )
    assert manifest_payload["target_date"] == "2026-04-09"
    assert "trade_review" in manifest_payload["snapshot_paths"]
    assert "add_blocked_lock" not in manifest_payload["snapshot_paths"]
    assert (report_dir / "server_comparison_2026-04-09.md").exists()
    updated_checklist = checklist_path.read_text(encoding="utf-8")
    assert "본서버 vs songstockscan 자동 비교" in updated_checklist
