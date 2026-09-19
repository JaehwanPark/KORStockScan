import json

import pytest

from src.engine.automation import postclose_summary_handoff as mod


def _publish(tmp_path, target="2026-09-07"):
    reports = tmp_path / "data" / "report"
    tower_path = (
        reports
        / "tuning_performance_control_tower"
        / f"tuning_performance_control_tower_{target}.json"
    )
    tower_path.parent.mkdir(parents=True)
    tower_path.write_text(
        json.dumps(
            {
                "date": target,
                "source_generation_contract": mod.source_receipt(
                    mod.source_paths(reports, target, "tower"), target
                ),
            }
        )
    )
    checklist = tmp_path / "2026-09-08-stage2-todo-checklist.md"
    checklist.write_text(
        mod.checklist_marker(
            mod.source_receipt(mod.source_paths(reports, target, "checklist"), target)
        )
    )
    return reports, tower_path, checklist


def test_exact_receipts_and_optional_absence_pass(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    result = mod.verify_summary_handoff(
        "2026-09-07", report_dir=reports, checklist_path=checklist
    )
    assert result["status"] == "pass"
    assert result["runtime_effect"] is False


def test_late_source_arrival_invalidates_both_consumers(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    source = mod.source_paths(reports, "2026-09-07", "tower")[
        "code_improvement_workorder"
    ]
    source.parent.mkdir(parents=True)
    source.write_text('{"date":"2026-09-07","orders":[]}')
    result = mod.verify_summary_handoff(
        "2026-09-07", report_dir=reports, checklist_path=checklist
    )
    assert len(result["issues"]) == 2


def test_route_session_venue_provenance_hashes_bind_both_consumers(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    for consumer in ("tower", "checklist"):
        labels = mod.source_paths(reports, "2026-09-07", consumer)
        assert {"key_lineage_ledger", "conversion_lane"} <= labels.keys()

    source = mod.source_paths(reports, "2026-09-07", "checklist")[
        "conversion_lane"
    ]
    source.parent.mkdir(parents=True)
    source.write_text(
        '{"route":"SOR","session_bucket":"KRX_NXT_AFTERMARKET",'
        '"effective_venue":"INTEGRATED"}',
        encoding="utf-8",
    )

    result = mod.verify_summary_handoff(
        "2026-09-07", report_dir=reports, checklist_path=checklist
    )
    assert result["status"] == "fail"
    assert len(result["issues"]) == 2


def test_verifier_refresh_does_not_create_cycle(tmp_path):
    reports, _, checklist = _publish(tmp_path)
    path = reports / "threshold_cycle_postclose_verification"
    path.mkdir()
    (path / "threshold_cycle_postclose_verification_2026-09-07.json").write_text(
        '{"status":"warning"}'
    )
    assert (
        mod.verify_summary_handoff(
            "2026-09-07", report_dir=reports, checklist_path=checklist
        )["status"]
        == "pass"
    )


@pytest.mark.parametrize(
    "mutation", ["date", "authority", "hash", "duplicate_marker", "no_marker"]
)
def test_invalid_contracts_fail(tmp_path, mutation):
    reports, tower, checklist = _publish(tmp_path)
    payload = json.loads(tower.read_text())
    if mutation == "date":
        payload["date"] = "2026-09-04"
    elif mutation == "authority":
        payload["source_generation_contract"]["allowed_runtime_apply"] = True
    elif mutation == "hash":
        payload["source_generation_contract"]["sources"]["code_improvement_workorder"][
            "sha256"
        ] = ("0" * 64)
    elif mutation == "duplicate_marker":
        checklist.write_text(checklist.read_text() * 2)
    else:
        checklist.write_text("# No receipt")
    if mutation in {"date", "authority", "hash"}:
        tower.write_text(json.dumps(payload))
    assert (
        mod.verify_summary_handoff(
            "2026-09-07", report_dir=reports, checklist_path=checklist
        )["status"]
        == "fail"
    )


def test_explicitly_disabled_consumers_are_not_missing(tmp_path):
    result = mod.verify_summary_handoff(
        "2026-09-07",
        report_dir=tmp_path,
        checklist_path=tmp_path / "missing.md",
        require_tower=False,
        require_checklist=False,
    )
    assert result["status"] == "pass"
    assert result["checked_consumers"] == []


def test_concurrent_source_change_prevents_publish(tmp_path):
    path = tmp_path / "source.json"
    paths = {"source": path}
    receipt = mod.source_receipt(paths, "2026-09-07")
    path.write_text("{}")
    with pytest.raises(RuntimeError, match="changed_during_render"):
        mod.assert_sources_unchanged(receipt, paths)


def test_pipeline_diagnostic_arrival_invalidates_both_exact_consumers(tmp_path):
    reports = tmp_path / "report"
    day = "2026-09-17"
    before = {consumer: mod.source_receipt(mod.source_paths(reports, day, consumer), day)
              for consumer in ("tower", "checklist")}
    path = mod.source_paths(reports, day, "tower")["pipeline_event_verbosity"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"target_date":"2026-09-17","state":"resource_deferred"}')
    for consumer in ("tower", "checklist"):
        after = mod.source_receipt(mod.source_paths(reports, day, consumer), day)
        assert after != before[consumer]


def test_retired_common_layer_handoff_uses_direct_sources_without_cycle(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-19"
    paths = mod.source_paths(reports, day, "tower")

    assert set(paths) == {"runtime_approval_summary"}
    assert "postclose_verifier" not in paths
    assert "threshold_cycle_ev" not in paths
    assert "preopen_apply_plan" not in paths


def test_retired_handoff_records_future_bootstrap_without_hashing_it(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-19"
    summary = reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    summary.parent.mkdir(parents=True)
    payload = {
        "date": day,
        "preopen_consumption_state": "pending",
        "preopen_consumption_receipt": {
            "apply_date": "2026-09-21",
            "manifest_path": "/runtime/runtime_policy_bootstrap_2026-09-21.json",
            "verification_path": "/runtime/runtime_policy_bootstrap_verify_2026-09-21.json",
        },
        "sources": {},
    }
    summary.write_text(json.dumps(payload), encoding="utf-8")

    paths = mod.source_paths(reports, day, "tower")
    before = mod.source_receipt(paths, day)
    bootstrap = reports.parent / "runtime" / "policy_bootstrap" / "runtime_policy_bootstrap_2026-09-21.json"
    bootstrap.parent.mkdir(parents=True)
    bootstrap.write_text('{"status":"ready"}', encoding="utf-8")
    after = mod.source_receipt(paths, day)

    assert set(paths) == {"runtime_approval_summary"}
    assert before == after
    assert mod.direct_future_handoff(payload, day)["manifest_path"].endswith(
        "runtime_policy_bootstrap_2026-09-21.json"
    )


def test_schema_v3_pre_retirement_source_uses_direct_handoff(tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-17"
    summary = reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    summary.parent.mkdir(parents=True)
    summary.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "date": day,
                "preopen_consumption_receipt": {"apply_date": "2026-09-21"},
            }
        ),
        encoding="utf-8",
    )

    paths = mod.source_paths(reports, day, "checklist")

    assert set(paths) == {"runtime_approval_summary"}


def test_retired_common_layer_handoff_skips_legacy_intake(monkeypatch, tmp_path):
    reports = tmp_path / "data" / "report"
    day = "2026-09-19"
    summary = {
        "date": day,
        "preopen_consumption_state": "not_due",
        "preopen_consumption_receipt": {},
        "sources": {},
    }
    summary_path = reports / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    receipt = mod.source_receipt(mod.source_paths(reports, day, "tower"), day)
    tower = reports / "tuning_performance_control_tower" / f"tuning_performance_control_tower_{day}.json"
    tower.parent.mkdir(parents=True)
    tower.write_text(json.dumps({"date": day, "source_generation_contract": receipt}))
    checklist = tmp_path / "checklist.md"
    checklist.write_text(
        mod.checklist_marker(receipt)
        + "\n"
        + mod.direct_future_handoff_marker(mod.direct_future_handoff(summary, day))
    )
    monkeypatch.setattr(
        "src.engine.automation.postclose_recommendation_intake.build_intake",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("retired intake must not run")
        ),
    )

    result = mod.verify_summary_handoff(
        day, report_dir=reports, checklist_path=checklist
    )

    assert result["status"] == "pass"
