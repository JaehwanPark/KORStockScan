"""Full native publication -> bounded observation consumers, without promotion."""

from datetime import datetime
import hashlib
import json
from pathlib import Path

import pytest

from src.engine import runtime_approval_summary as summary
from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.monitoring import submission_bottleneck_monitor as monitor
from src.engine.scalping import entry_split_monitor_projection as projection
from src.engine.scalping import entry_split_order_plan as native

DAY = "2026-10-14"
NOW = datetime(2026, 10, 14, 13, 40)


def _write(path, value, *, padding=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, indent=2).encode() + b" " * padding
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture(params=["rows", "counts"])
def published(tmp_path, monkeypatch, request):
    monkeypatch.setattr(bootstrap, "DATA_DIR", tmp_path)
    monkeypatch.setattr(projection, "MANAGED_DATA_ROOT", tmp_path, raising=False)
    report_path = (
        tmp_path
        / "report/entry_split_order_plan"
        / f"entry_split_order_plan_{DAY}.json"
    )
    policy_path = (
        tmp_path
        / "threshold_cycle/entry_split_order_policy"
        / f"entry_split_order_policy_{DAY}.json"
    )
    atomic = dict(
        entry_execution_sizing_plan_schema=native.ATOMIC_EXECUTION_SIZING_SCHEMA,
        entry_execution_sizing_policy=native.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY,
        entry_price_plan_schema=native.ATOMIC_PRICE_PLAN_SCHEMA,
    )
    report = dict(
        schema_version=native.SCHEMA_VERSION,
        date=DAY,
        recommended_policy=dict(
            policy_version="inactive-fixture-v1", runtime_apply_allowed=False, **atomic
        ),
        economic_acceptance=dict(
            status="source_gap",
            blockers=["operating_paired_source_missing"],
            primary_operating_ev_pct=None,
            robust_paired_delta_ev_lower_bound_pct=None,
            paired_net_ev_delta_pct=None,
            paired_sample_count=0,
            allowed_runtime_apply=False,
            candidates=[{"candidate": 1}, {"candidate": 2}],
            model_rows=[{"model": 1}, {"model": 2}] if request.param == "rows" else 2,
            consumed_holdouts={"one": {}, "two": {}} if request.param == "rows" else 2,
        ),
        operating_candidate_grid=[{"candidate": i} for i in range(3)],
        cumulative_state=dict(
            clean_tuning_baseline_date="2026-06-05", source_dates=["2026-10-13", DAY]
        ),
    )
    policy = dict(
        schema_version=native.POLICY_SCHEMA_VERSION,
        source_date=DAY,
        policy_version="inactive-fixture-v1",
        runtime_apply_allowed=False,
        buckets={},
        **atomic,
    )
    report, policy = native.bind_report_policy_generation(report, policy)
    assert native.validate_report_policy_generation(report, policy) == (
        True,
        "generation_binding_valid",
    )
    generation = report["artifact_generation_binding"]["generation_id"]
    report_sha = _write(report_path, report, padding=8 * 1024 * 1024)
    policy_sha = _write(policy_path, policy)
    immutable_report = (
        report_path.parent
        / "generations"
        / f"entry_split_order_plan_{DAY}_{generation}.json"
    )
    immutable_policy = (
        policy_path.parent
        / "generations"
        / f"entry_split_order_policy_{DAY}_{generation}.json"
    )
    _write(immutable_report, report)
    _write(immutable_policy, policy)
    incumbent = (
        tmp_path / "threshold_cycle/entry_split_order_policy/retained-incumbent.json"
    )
    _write(incumbent, {"policy_version": "retained"})
    _write(
        tmp_path / "runtime/policy_bootstrap" / f"runtime_policy_bootstrap_{DAY}.json",
        dict(
            target_date=DAY,
            pre_submit_delay_handoff=dict(status="not_published", target_date=DAY),
            env_overrides=dict(
                KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE=str(incumbent),
                KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_VERSION="retained",
            ),
        ),
    )
    _write(
        tmp_path
        / "runtime/policy_bootstrap"
        / f"runtime_policy_bootstrap_verify_{DAY}.json",
        dict(target_date=DAY, status="pass", passed=True, pid_passed=True),
    )
    receipt = projection.migrate_verification(report_path, policy_path, source_date=DAY)
    assert receipt["verified"] is True and receipt["report_sha256"] == report_sha
    assert report_sha != report["artifact_generation_binding"]["report_content_sha256"]
    return dict(
        root=tmp_path,
        report=report,
        policy=policy,
        report_path=report_path,
        policy_path=policy_path,
        immutable_report=immutable_report,
        report_sha=report_sha,
        policy_sha=policy_sha,
    )


def _forbid_full_reads(monkeypatch, value):
    original_open = Path.open
    forbidden = {value["report_path"], value["immutable_report"]}
    policy_reads = []

    def open_bounded(path, mode="r", *args, **kwargs):
        if "r" in mode:
            assert path not in forbidden, "warm consumers must not reopen a full report"
            if path == value["policy_path"]:
                policy_reads.append(path)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_bounded)
    return policy_reads


def test_monitor_reads_verified_projection_and_exact_policy_once(
    published, monkeypatch
):
    policy_reads = _forbid_full_reads(monkeypatch, published)
    result = monitor.entry_execution_tuning_semantics(published["root"], NOW)
    split = result["entry_split"]
    assert result["status"] == "observed" and result["issues"] == {}
    assert split["read_mode"] == "verified_monitor_projection"
    assert split["verification"] == "verified" and split["status"] == "source_gap"
    assert split["blockers"] == ["operating_paired_source_missing"]
    assert split["operating_candidate_count"] == 3
    assert split["paired_model_row_count"] == split["consumed_holdout_count"] == 2
    assert split["cumulative_source_date_count"] == 2
    assert (
        split["paired_net_ev_delta_pct"] is None
        and split["primary_operating_ev_pct"] is None
    )
    assert split["policy_runtime_apply_allowed"] is False
    assert (
        split["bootstrap_policy_binding"]
        == "incumbent_preserved_candidate_not_promoted"
    )
    assert split["runtime_consumption"] == "bootstrap_manifest_bound_not_pid_proven"
    assert split["verification_receipt"]["report_sha256"] == published["report_sha"]
    assert "_validated_policy" not in split["verification_receipt"]
    assert len(policy_reads) == 1


def test_runtime_summary_projection_matches_native_economics_and_exact_bytes(
    published, monkeypatch
):
    expected = summary._economic_projection("entry_split", published["report"])
    policy_reads = _forbid_full_reads(monkeypatch, published)
    payload, proof, error = summary._large_companion(
        "entry_split",
        published["report_path"],
        DAY,
        published["report_sha"],
        {"entry_split_policy": published["policy_path"]},
    )
    assert error is None and proof["verified"] is True
    assert proof["report_sha256"] == published["report_sha"]
    assert proof["sha256"] == proof["policy_sha256"] == published["policy_sha"]
    assert len(policy_reads) == 1
    assert "_validated_policy" not in proof
    assert summary._economic_projection("entry_split", payload) == expected
    assert payload["observation_projection"]["runtime_effect"] is False
    assert payload["observation_projection"]["allowed_runtime_apply"] is False


def test_runtime_summary_rejects_canonical_hash_used_as_report_byte_hash(
    published, monkeypatch
):
    _forbid_full_reads(monkeypatch, published)
    semantic = published["report"]["artifact_generation_binding"][
        "report_content_sha256"
    ]
    payload, proof, error = summary._large_companion(
        "entry_split",
        published["report_path"],
        DAY,
        semantic,
        {"entry_split_policy": published["policy_path"]},
    )
    assert payload == {} and error == "semantic_unverified_large_source"
    assert proof["verified"] is False and proof["artifact_sha_matches"] is False


def test_monitor_accepts_trusted_release_data_mount_without_weakening_child_checks(
    published, monkeypatch
):
    release = published["root"] / "release"
    release.mkdir()
    (release / "data").symlink_to(published["root"], target_is_directory=True)
    _forbid_full_reads(monkeypatch, published)
    result = monitor.entry_execution_tuning_semantics(release / "data", NOW)
    assert result["entry_split"]["verification"] == "verified"
    assert result["entry_split"]["policy_generation_binding"] == "matched"
    assert result["entry_split"]["status"] == "source_gap"
    assert (
        result["entry_split"]["verification_receipt"]["report_sha256"]
        == published["report_sha"]
    )
    assert result["status"] == "observed"
