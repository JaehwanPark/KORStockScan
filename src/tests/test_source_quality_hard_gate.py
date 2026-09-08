import json
import gzip
import pytest

from src.engine.automation import source_quality_hard_gate as mod
from src.engine import observation_source_quality_audit as producer


def test_duplicate_approval_keys_and_invalid_status_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    path = _write_preflight(tmp_path, "2026-09-08", _valid_current_preflight())
    path.write_text(
        '{"status":"pass","summary":{"tuning_input_allowed":false,"tuning_input_allowed":true}}'
    )
    assert (
        mod.load_source_quality_preflight("2026-09-08")["tuning_input_allowed"] is False
    )
    payload = _valid_current_preflight()
    payload["status"] = []
    _write_preflight(tmp_path, "2026-09-08", payload)
    assert (
        mod.load_source_quality_preflight("2026-09-08")["tuning_input_allowed"] is False
    )


def _valid_current_preflight():
    return {
        "target_date": "2026-09-08",
        "status": "pass",
        "source": {"exists": True},
        "summary": {
            "tuning_input_allowed": True,
            "hard_blocking_contract_gap_count": 0,
        },
    }


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda p: p.update(target_date="2026-09-07"), "target_date_mismatch"),
        (lambda p: p["source"].update(exists=False), "source_missing"),
        (
            lambda p: p["summary"].update(tuning_input_allowed="false"),
            "allow_type_invalid",
        ),
        (
            lambda p: p["summary"].update(hard_blocking_contract_gap_count="bad"),
            "gap_count_invalid",
        ),
        (lambda p: p.update(status="success"), "status_invalid"),
    ],
)
def test_current_preflight_rejects_invalid_contract(
    tmp_path, monkeypatch, mutation, reason
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    payload = _valid_current_preflight()
    mutation(payload)
    _write_preflight(tmp_path, "2026-09-08", payload)
    result = mod.load_source_quality_preflight("2026-09-08")
    assert result["tuning_input_allowed"] is False
    assert reason in result["blocked_reason"]


def test_v2_raw_generation_and_lossless_archive_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    raw = tmp_path / "pipeline.jsonl"
    raw.write_text('{"event_type":"other"}\n')
    monkeypatch.setattr(producer, "_pipeline_events_path", lambda d: raw)
    payload = producer.build_observation_source_quality_audit("2026-09-08")
    _write_preflight(tmp_path, "2026-09-08", payload)
    assert (
        mod.load_source_quality_preflight("2026-09-08")["tuning_input_allowed"] is True
    )
    with gzip.open(str(raw) + ".gz", "wb") as handle:
        handle.write(raw.read_bytes())
    raw.unlink()
    assert (
        mod.load_source_quality_preflight("2026-09-08")["tuning_input_allowed"] is True
    )
    with gzip.open(str(raw) + ".gz", "wb") as handle:
        handle.write(b'{"event_type":"changed"}\n')
    assert (
        mod.load_source_quality_preflight("2026-09-08")["tuning_input_allowed"] is False
    )


def test_v2_append_invalidates_previous_audited_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    raw = tmp_path / "pipeline.jsonl"
    raw.write_text("")
    monkeypatch.setattr(producer, "_pipeline_events_path", lambda d: raw)
    payload = producer.build_observation_source_quality_audit("2026-09-08")
    _write_preflight(tmp_path, "2026-09-08", payload)
    assert (
        mod.load_source_quality_preflight("2026-09-08")["tuning_input_allowed"] is True
    )
    raw.write_text('{"event_type":"new"}\n')
    result = mod.load_source_quality_preflight("2026-09-08")
    assert result["tuning_input_allowed"] is False
    assert "generation_changed" in result["blocked_reason"]


def test_final_verifier_consumes_same_exact_artifact_validation(tmp_path, monkeypatch):
    from src.engine import verify_threshold_cycle_postclose_chain as verifier

    raw = tmp_path / "pipeline.jsonl"
    raw.write_text("")
    monkeypatch.setattr(producer, "_pipeline_events_path", lambda d: raw)
    path = tmp_path / "audit.json"
    path.write_text(
        json.dumps(producer.build_observation_source_quality_audit("2026-09-08"))
    )
    before = verifier.load_source_quality_preflight("2026-09-08", artifact_path=path)
    raw.write_text('{"event_type":"new"}\n')
    after = verifier.load_source_quality_preflight("2026-09-08", artifact_path=path)
    for preflight, expected in ((before, True), (after, False)):
        result = verifier._source_quality_hard_block_status(
            preflight,
            ev_report={},
            runtime_summary={},
            ldm_report={},
            bridge_report={},
            workorder={},
        )
        assert result["tuning_input_allowed"] is expected
    assert after["validation_errors"] == [
        "source_quality_preflight_source_generation_changed"
    ]
    # Exercise the production builder, including its target-specific path routing.
    monkeypatch.setattr(verifier, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(verifier, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(verifier, "LOG_PATH", tmp_path / "missing.log")
    monkeypatch.setattr(verifier, "_next_krx_trading_day", lambda d: "2026-09-09")
    monkeypatch.setattr(verifier, "_postclose_not_yet_due", lambda d: False)
    calls = []

    def checked_load(day, *, artifact_path):
        calls.append((day, artifact_path))
        return after

    monkeypatch.setattr(verifier, "load_source_quality_preflight", checked_load)
    report = verifier.build_threshold_cycle_postclose_verification("2026-09-08")
    assert calls == [
        (
            "2026-09-08",
            tmp_path
            / "reports/observation_source_quality_audit/observation_source_quality_audit_2026-09-08.json",
        )
    ]
    assert report["status"] == "fail"
    raw_status = verifier._source_quality_hard_block_status(
        {
            "schema_version": "observation_source_quality_audit_v2",
            "status": "pass",
            "summary": {"tuning_input_allowed": True},
        },
        ev_report={},
        runtime_summary={},
        ldm_report={},
        bridge_report={},
        workorder={},
    )
    assert raw_status["tuning_input_allowed"] is False


def test_verified_archiver_receipt_avoids_decompressing_raw_per_consumer(
    tmp_path, monkeypatch
):
    from src.engine import compress_db_backfilled_files as archive

    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    raw = tmp_path / "pipeline_events_2026-09-08.jsonl"
    raw.write_text('{"event_type":"other"}\n')
    monkeypatch.setattr(producer, "_pipeline_events_path", lambda d: raw)
    _write_preflight(
        tmp_path,
        "2026-09-08",
        producer.build_observation_source_quality_audit("2026-09-08"),
    )
    archive._gzip_file_with_jsonl_generation_lock(raw, dry_run=False)
    monkeypatch.setattr(
        mod,
        "_archived_raw_digest",
        lambda *args: pytest.fail("unexpected full gzip rescan"),
    )
    result = mod.load_source_quality_preflight("2026-09-08")
    assert result["tuning_input_allowed"] is True


def _write_preflight(tmp_path, target_date, payload):
    path = (
        tmp_path
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_source_quality_preflight_missing_artifact_blocks_tuning(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    preflight = mod.load_source_quality_preflight("2026-06-05")

    assert preflight["status"] == "missing"
    assert preflight["tuning_input_allowed"] is False
    assert preflight["allowed_runtime_apply"] is False
    assert preflight["blocked_reason"] == "source_quality_preflight_missing"
    assert mod.source_quality_preflight_blocked(preflight) is True


def test_source_quality_preflight_missing_pre_baseline_is_not_current_gate(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    preflight = mod.load_source_quality_preflight("2026-05-31")

    assert preflight["status"] == "missing"
    assert preflight["clean_baseline_enforced"] is False
    assert preflight["tuning_input_allowed"] is True
    assert preflight["source_quality_gate"] == "pass_or_not_evaluated"
    assert mod.source_quality_preflight_blocked(preflight) is False


def test_source_quality_preflight_invalid_artifact_blocks_tuning(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    path = (
        tmp_path
        / "observation_source_quality_audit"
        / "observation_source_quality_audit_2026-06-05.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{bad json", encoding="utf-8")

    preflight = mod.load_source_quality_preflight("2026-06-05")

    assert preflight["status"] == "invalid"
    assert preflight["tuning_input_allowed"] is False
    assert preflight["blocked_reason"] == "source_quality_preflight_invalid"
    assert mod.source_quality_preflight_blocked(preflight) is True


def test_source_quality_preflight_unknown_token_only_does_not_block(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    artifact = _write_preflight(
        tmp_path,
        "2026-06-04",
        {
            "status": "warning",
            "summary": {
                "tuning_input_allowed": True,
                "hard_blocking_contract_gap_count": 0,
                "review_warning_count": 2,
            },
        },
    )

    preflight = mod.load_source_quality_preflight("2026-06-04")

    assert preflight["artifact"] == str(artifact)
    assert preflight["tuning_input_allowed"] is True
    assert preflight["source_quality_gate"] == "pass"
    assert preflight["review_warning_count"] == 2
    assert mod.source_quality_preflight_blocked(preflight) is False


def test_source_quality_preflight_preserves_raw_row_exclusion_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    artifact = _write_preflight(
        tmp_path,
        "2026-06-04",
        {
            "status": "pass",
            "summary": {
                "tuning_input_allowed": True,
                "hard_blocking_contract_gap_count": 0,
                "hard_blocking_excluded_row_count": 2,
                "raw_row_exclusion_applied": True,
                "raw_row_exclusion_manifest": "/tmp/raw_row_exclusion/manifest.json",
                "review_warning_count": 0,
            },
            "raw_row_exclusion": {
                "manifest_path": "/tmp/raw_row_exclusion/manifest.json",
                "backup_path": "/tmp/raw_row_exclusion/pipeline_events.backup.jsonl",
                "excluded_row_count": 2,
                "stage_counts": {
                    "pyramid_blocked_reason": 1,
                    "reversal_add_blocked_reason": 1,
                },
                "field_gap_counts": {"tick_aggressor_pressure_usable": 2},
                "exclusion_reasons": {"missing_required_field": 2},
                "first_timestamp": "2026-06-04T10:00:00+09:00",
                "last_timestamp": "2026-06-04T10:05:00+09:00",
                "producer_hint": ["sniper_state_handlers"],
                "sample_rows": [{"large": "omitted from preflight gate"}],
                "excluded_rows": [{"large": "omitted from preflight gate"}],
            },
        },
    )

    preflight = mod.load_source_quality_preflight("2026-06-04")

    assert preflight["artifact"] == str(artifact)
    assert preflight["source_quality_gate"] == "pass"
    assert preflight["tuning_input_allowed"] is True
    assert preflight["allowed_runtime_apply"] is True
    assert mod.source_quality_preflight_blocked(preflight) is False
    assert preflight["raw_row_exclusion_applied"] is True
    assert (
        preflight["raw_row_exclusion_manifest"]
        == "/tmp/raw_row_exclusion/manifest.json"
    )
    assert preflight["hard_blocking_excluded_row_count"] == 2
    assert preflight["raw_row_exclusion"]["stage_counts"] == {
        "pyramid_blocked_reason": 1,
        "reversal_add_blocked_reason": 1,
    }
    assert preflight["raw_row_exclusion"]["field_gap_counts"] == {
        "tick_aggressor_pressure_usable": 2,
    }
    assert "sample_rows" not in preflight["raw_row_exclusion"]
    assert "excluded_rows" not in preflight["raw_row_exclusion"]


def test_source_quality_preflight_contract_gap_blocks_and_scrubs_runtime_aliases(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    _write_preflight(
        tmp_path,
        "2026-06-04",
        {
            "status": "warning",
            "summary": {
                "tuning_input_allowed": False,
                "blocked_reason": "blocked_contract_gap",
                "hard_blocking_contract_gap_count": 1,
                "hard_blocking_stages": ["scalp_sim_duplicate_buy_signal"],
            },
        },
    )
    preflight = mod.load_source_quality_preflight("2026-06-04")
    report = {
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "runtime_mutation_allowed": True,
        "approval_requests": [{"family": "entry"}],
        "runtime_approval_candidates": [{"family": "entry"}],
        "runtime_apply_bridge": {
            "selected": [{"family": "entry"}],
            "approved_requests": [{"family": "entry"}],
            "selected_count": 1,
            "approved": 1,
            "env_apply_allowed": True,
        },
        "summary": {
            "runtime_candidate_count": 1,
            "runtime_effect": True,
            "allowed_runtime_apply": True,
        },
    }

    blocked = mod.apply_source_quality_preflight_block(report, preflight)

    assert blocked["status"] == "source_quality_blocked"
    assert blocked["calibration_state"] == "source_quality_blocked"
    assert blocked["approval_requests"] == []
    assert blocked["runtime_approval_candidates"] == []
    assert blocked["runtime_apply_bridge"]["selected"] == []
    assert blocked["runtime_apply_bridge"]["approved_requests"] == []
    assert blocked["runtime_apply_bridge"]["selected_count"] == 0
    assert blocked["runtime_apply_bridge"]["approved"] == 0
    assert blocked["runtime_apply_bridge"]["env_apply_allowed"] is False
    assert blocked["runtime_mutation_allowed"] is False
    assert blocked["summary"]["runtime_candidate_count"] == 0
    assert blocked["summary"]["calibration_state"] == "source_quality_blocked"


def test_filter_source_dates_by_preflight_excludes_each_blocked_date(monkeypatch):
    gates = {
        "2026-06-05": {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
        },
        "2026-06-06": {
            "status": "fail",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "blocked_contract_gap",
            "artifact": "/tmp/audit-2026-06-06.json",
            "hard_blocking_contract_gap_count": 2,
        },
        "2026-06-07": {
            "status": "missing",
            "tuning_input_allowed": False,
            "allowed_runtime_apply": False,
            "source_quality_gate": "blocked_contract_gap",
            "blocked_reason": "source_quality_preflight_missing",
        },
    }
    monkeypatch.setattr(
        mod, "load_source_quality_preflight", lambda source_date: gates[source_date]
    )

    allowed, excluded = mod.filter_source_dates_by_preflight(
        ["2026-06-05", "2026-06-06", "2026-06-07", "2026-06-05"]
    )

    assert allowed == ["2026-06-05"]
    assert [item["source_date"] for item in excluded] == [
        "2026-06-06",
        "2026-06-07",
    ]
    assert excluded[0]["hard_blocking_contract_gap_count"] == 2
    assert excluded[1]["blocked_reason"] == "source_quality_preflight_missing"
