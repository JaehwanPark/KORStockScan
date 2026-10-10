import gzip
import json
from pathlib import Path
import sys
import types

import pytest

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
    assert not list(snapshot_dir.glob(".trade_review_2026-04-06.json.*.tmp"))


def test_postclose_trade_review_completed_projection_is_sealed_and_consumed(tmp_path, monkeypatch):
    from src.engine import holding_exit_observation_report as holding
    from src.engine.sniper_trade_review_report import completed_census_manifest

    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", snapshot_dir / "manifests")
    day = "2026-09-30"
    payload = {
        "date": day, "code": None, "since": None,
        "meta": {"warnings": [], "snapshot_profile": "postclose_exit",
                 "sell_completed_event_ids": [],
                 "trailing_event_source_receipts": []},
        "metrics": {"canonical_completed_trades": 0, "completed_trades": 0,
                    "open_scalp_position_projection_count": 0,
                    "open_scalp_position_projection_status": "current_db_census"},
        "sections": {"completed_trade_projection": [],
                     "open_scalp_position_projection": []},
    }
    payload["meta"]["completed_census_manifest"] = completed_census_manifest(payload)
    path = service.save_monitor_snapshot("trade_review", day, payload)
    monkeypatch.setattr(holding, "_monitor_snapshot_path",
                        lambda kind, target: path if kind == "trade_review" and target == day else None)
    snapshots, sources = holding._load_saved_snapshots("trade_review", [day])
    assert len(snapshots) == 1
    assert snapshots[0]["schema"] == "trade_review_completed_projection_sidecar_v1"
    assert sources == [str(path.with_suffix(".completed_projection.json"))]
    sidecar = path.with_suffix(".completed_projection.json")
    altered = json.loads(sidecar.read_text())
    altered["metrics"]["canonical_completed_trades"] = 1
    sidecar.write_text(json.dumps(altered))
    assert holding._verified_trade_review_projection(path, day) is None


def test_postclose_snapshot_reuse_requires_exact_hashes_and_pipeline_cutoff(tmp_path, monkeypatch):
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.holding_window_generation import capture_window

    directory = tmp_path / "report" / "monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", directory / "manifests")
    day = "2026-09-30"
    trade = {"date": day, "code": None, "since": None,
             "meta": {"warnings": [], "snapshot_profile": "postclose_exit",
                      "sell_completed_event_ids": [],
                      "trailing_event_source_receipts": []},
             "metrics": {"canonical_completed_trades": 0,
                         "open_scalp_position_projection_count": 0},
             "sections": {"completed_trade_projection": [],
                          "open_scalp_position_projection": []}}
    trade["meta"]["completed_census_manifest"] = completed_census_manifest(trade)
    paths = {"trade_review": service.save_monitor_snapshot("trade_review", day, trade)}
    for kind in ("post_sell_feedback", "missed_entry_counterfactual",
                 "holding_exit_observation"):
        body = {"date": day, "meta": {"snapshot_profile": "postclose_exit"}}
        if kind == "holding_exit_observation":
            window = capture_window(tmp_path, [day])
            body.update(input_window_dependencies=window,
                        input_window_generation_sha256=window["input_window_generation_sha256"])
        paths[kind] = service.save_monitor_snapshot(kind, day, body)
    pipeline = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    pipeline.parent.mkdir()
    pipeline.write_text('{}\n')
    manifest = service.save_monitor_snapshot_manifest(
        day, profile="postclose_exit",
        snapshots={kind: str(path.resolve()) for kind, path in paths.items()})
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) == manifest
    paths["post_sell_feedback"].write_text('{}')
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) is None
    service.save_monitor_snapshot(
        "post_sell_feedback", day, {"date": day, "meta": {"snapshot_profile": "postclose_exit"}})
    service.save_monitor_snapshot_manifest(
        day, profile="postclose_exit",
        snapshots={kind: str(path.resolve()) for kind, path in paths.items()})
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) == manifest
    import os
    newer = manifest.stat().st_mtime_ns + 2_000_000_000
    os.utime(pipeline, ns=(newer, newer))
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) is None


def test_completed_census_seals_actual_saved_profile(tmp_path, monkeypatch):
    from src.engine.sniper_trade_review_report import (
        completed_census_manifest, verify_completed_census_manifest,
    )

    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", tmp_path)
    day = "2026-09-28"
    payload = {
        "date": day, "code": None, "since": None,
        "meta": {"sell_completed_event_ids": [],
                 "trailing_event_source_receipts": []},
        "metrics": {"canonical_completed_trades": 0},
        "sections": {"completed_trade_projection": []},
    }
    payload["meta"]["completed_census_manifest"] = completed_census_manifest(payload)
    prior_run = payload["meta"]["completed_census_manifest"]["run_id"]
    payload["meta"]["snapshot_profile"] = "postclose_exit"

    service.save_monitor_snapshot("trade_review", day, payload)
    loaded = service.load_monitor_snapshot("trade_review", day)
    assert verify_completed_census_manifest(loaded, day) is None
    assert loaded["meta"]["completed_census_manifest"]["profile"] == "postclose_exit"
    assert loaded["meta"]["completed_census_manifest"]["run_id"] != prior_run


def test_monitor_snapshot_atomic_write_preserves_previous_file_on_dump_failure(
    tmp_path, monkeypatch
):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    path = service.save_monitor_snapshot(
        "trade_review", "2026-04-06", {"status": "previous"}
    )

    def _raise_after_partial_write(payload, handle, **kwargs):
        handle.write('{"status":')
        raise RuntimeError("simulated_dump_failure")

    monkeypatch.setattr(service.json, "dump", _raise_after_partial_write)

    with pytest.raises(RuntimeError, match="simulated_dump_failure"):
        service.save_monitor_snapshot(
            "trade_review", "2026-04-06", {"status": "replacement"}
        )

    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "previous"}
    assert not list(snapshot_dir.glob(".trade_review_2026-04-06.json.*.tmp"))


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
        '{"target_date":"2026-04-22","profile":"full","snapshots":{"profile":"full","trend_max_dates":"12","trade_review":"data/report/monitor_snapshots/trade_review_2026-04-22.json","performance_tuning":"data/report/monitor_snapshots/performance_tuning_2026-04-22.json","snapshot_manifest":"data/report/monitor_snapshots/manifests/monitor_snapshot_manifest_2026-04-22_full.json"}}\n',
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
    assert "server_comparison" not in message
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


def test_notify_monitor_snapshot_admin_excludes_stage_metrics_from_count():
    message = _build_message(
        {
            "status": "success",
            "snapshots": {
                "profile": "full",
                "trade_review": "/tmp/trade_review.json",
                "performance_tuning": "/tmp/performance_tuning.json",
                "stage_metrics": json.dumps(
                    {"trade_review": {"process_max_rss_kb": 123}}
                ),
                "snapshot_manifest": "/tmp/manifest.json",
            },
        },
        target_date="2026-08-05",
        profile="full",
        log_file="logs/run_monitor_snapshot.log",
    )

    assert "snapshot_count: 2" in message
    assert "stage_metrics" not in message


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


def test_normalize_result_payload_excludes_stage_metrics_from_snapshot_count(tmp_path):
    result_file = tmp_path / "result.jsonl"
    result_file.write_text(
        json.dumps(
            {
                "status": "success",
                "snapshots": {
                    "profile": "full",
                    "trade_review": "/tmp/trade_review.json",
                    "performance_tuning": "/tmp/performance_tuning.json",
                    "stage_metrics": json.dumps(
                        {"trade_review": {"process_max_rss_kb": 123}}
                    ),
                    "snapshot_manifest": "/tmp/manifest.json",
                },
            }
        ),
        encoding="utf-8",
    )
    payload = runtime.normalize_result_payload(
        target_date="2026-08-05",
        profile="full",
        result_file=str(result_file),
    )

    assert payload["snapshot_count"] == 2


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


def test_save_monitor_snapshots_for_date_includes_expected_snapshot_sources(
    tmp_path, monkeypatch, capsys
):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

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
    result = service.save_monitor_snapshots_for_date("2026-04-09")

    assert "missed_entry_counterfactual" in result
    assert "holding_exit_observation" in result
    assert "wait6579_ev_cohort" in result
    assert "add_blocked_lock" not in result
    assert "snapshot_manifest" in result
    stage_metrics = json.loads(result["stage_metrics"])
    assert set(stage_metrics) == {
        "trade_review",
        "performance_tuning",
        "wait6579_ev_cohort",
        "post_sell_feedback",
        "missed_entry_counterfactual",
        "holding_exit_observation",
    }
    assert all(item["process_max_rss_kb"] > 0 for item in stage_metrics.values())
    saved = service.load_monitor_snapshot("missed_entry_counterfactual", "2026-04-09")
    assert saved is not None
    assert saved["meta"]["snapshot_kind"] == "missed_entry_counterfactual"
    assert saved["meta"]["buy_pause_guard"] == {"status": "ok"}
    postclose_result = service.save_monitor_snapshots_for_date_with_profile(
        "2026-04-09", profile="postclose_exit"
    )
    assert "missed_entry_counterfactual" in postclose_result
    postclose_stages = [
        event["snapshot_kind"]
        for line in capsys.readouterr().out.splitlines()
        if (event := json.loads(line)).get("event") == "monitor_snapshot_stage_start"
        and event.get("profile") == "postclose_exit"
    ]
    assert postclose_stages == [
        "trade_review", "post_sell_feedback",
        "missed_entry_counterfactual", "holding_exit_observation",
    ]
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
    manifest_payload = json.loads(
        Path(result["snapshot_manifest"]).read_text(encoding="utf-8")
    )
    assert manifest_payload["target_date"] == "2026-04-09"
    assert "trade_review" in manifest_payload["snapshot_paths"]
    assert "add_blocked_lock" not in manifest_payload["snapshot_paths"]


def test_cost_only_revision_invalidates_sidecar_and_manifest_without_pipeline_changes(tmp_path, monkeypatch):
    from src.engine import holding_exit_observation_report as holding
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation, receipt_path
    from src.engine.lifecycle.holding_window_generation import capture_window
    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", directory / "manifests")
    day = "2026-10-08"
    def save():
        trade = {"date": day, "code": None, "since": None,
            "meta": {"warnings": [], "snapshot_profile": "postclose_exit", "sell_completed_event_ids": [],
                     "actual_cost_source_generation": source_generation(tmp_path, day)},
            "metrics": {"canonical_completed_trades": 0},
            "sections": {"completed_trade_projection": [], "open_scalp_position_projection": []}}
        trade["meta"]["completed_census_manifest"] = completed_census_manifest(trade)
        paths = {"trade_review": service.save_monitor_snapshot("trade_review", day, trade)}
        for kind in ("post_sell_feedback", "missed_entry_counterfactual", "holding_exit_observation"):
            body = {"date": day, "meta": {"snapshot_profile": "postclose_exit"},
                    "actual_cost_source_generations": {day: source_generation(tmp_path, day)}}
            if kind == "holding_exit_observation":
                window = capture_window(tmp_path, [day])
                body.update(input_window_dependencies=window,
                            input_window_generation_sha256=window["input_window_generation_sha256"])
            paths[kind] = service.save_monitor_snapshot(kind, day, body)
        manifest = service.save_monitor_snapshot_manifest(day, profile="postclose_exit",
            snapshots={kind: str(path) for kind, path in paths.items()})
        return paths, manifest
    paths, manifest = save()
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) == manifest
    cost_path = receipt_path(tmp_path, day, "1")
    cost_path.parent.mkdir(parents=True)
    cost_path.write_text('{"revision":1}')
    assert holding._verified_trade_review_projection(paths["trade_review"], day, data_root=tmp_path) is None
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) is None
    with pytest.raises(ValueError):
        service.save_monitor_snapshot_manifest(day, profile="postclose_exit", snapshots={k: str(v) for k,v in paths.items()})
    paths, manifest = save()
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) == manifest
    cost_path.write_text('{"revision":2}')
    assert service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path) is None
