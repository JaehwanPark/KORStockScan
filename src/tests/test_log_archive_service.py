import gzip
import json
from pathlib import Path
import sys
import types

import pytest

from src.engine import log_archive_service as service
from src.engine import monitor_snapshot_runtime as runtime
from src.engine.notify_monitor_snapshot_admin import _build_message, _load_json_line


def test_import_under_replay_guard_does_not_create_archive_directories(tmp_path):
    import subprocess

    target = tmp_path / "absent-data"
    script = """
from pathlib import Path
import sys
from src.utils import constants
constants.DATA_DIR = Path(sys.argv[1])
from src.engine.lifecycle.avg_down_policy_replay import _install_effect_guard
_install_effect_guard()
from src.engine import log_archive_service as archive
assert archive.LOG_ARCHIVE_DIR == constants.DATA_DIR / 'log_archive'
assert archive.load_monitor_snapshot('missing', '2026-10-23') is None
assert not constants.DATA_DIR.exists()
print('read_only_import')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(target)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "read_only_import" in result.stdout
    assert not target.exists()


def _postclose_phase_fixture(tmp_path, monkeypatch):
    from src.engine import sniper_trade_review_report as trades
    from src.engine import sniper_post_sell_feedback as post_sell
    from src.engine import sniper_missed_entry_counterfactual as missed
    from src.engine import holding_exit_observation_report as holding
    from src.engine import buy_pause_guard
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    from src.engine.lifecycle.holding_window_generation import capture_window
    from src.engine.scalping.holding_vote_experiment import code_sha

    day = "2026-10-16"
    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(
        service, "MONITOR_SNAPSHOT_MANIFEST_DIR", directory / "manifests"
    )
    monkeypatch.setattr(
        buy_pause_guard, "evaluate_buy_pause_guard", lambda *a, **k: {"status": "ok"}
    )
    auxiliary = tmp_path / "ai_decision_requests/requests_2026-10-16.jsonl"
    auxiliary.parent.mkdir()
    auxiliary.write_text("before\n")
    calls = []

    def trade(**kwargs):
        calls.append("trade_review")
        payload = dict(
            date=day,
            scope="entered",
            code=None,
            since=None,
            meta=dict(
                warnings=[],
                sell_completed_event_ids=[],
                actual_cost_source_generation=source_generation(tmp_path, day),
            ),
            metrics=dict(
                total_trades=0, canonical_completed_trades=0, completed_trades=0
            ),
            sections=dict(
                recent_trades=[],
                strategy_position_fact_projection=[],
                completed_trade_projection=[],
                open_scalp_position_projection=[],
            ),
        )
        payload["meta"]["completed_census_manifest"] = trades.completed_census_manifest(
            payload
        )
        return payload

    def basic(kind):
        def build(**kwargs):
            calls.append(kind)
            return dict(date=day, meta={})

        return build

    def held(**kwargs):
        calls.append("holding_exit_observation")
        window = capture_window(tmp_path, [day])
        return dict(
            date=day,
            meta={},
            input_window_dependencies=window,
            input_window_generation_sha256=window["input_window_generation_sha256"],
            actual_cost_source_generations={day: source_generation(tmp_path, day)},
            holding_path_vote_replay={
                "vote_numeric_research": {
                    "status": "experiment_not_armed",
                    "code_sha256": code_sha(),
                }
            },
            fixture_auxiliary_source=auxiliary.read_text(),
        )

    monkeypatch.setattr(trades, "build_trade_review_report", trade)
    monkeypatch.setattr(
        post_sell, "build_post_sell_feedback_report", basic("post_sell_feedback")
    )
    monkeypatch.setattr(
        missed,
        "build_missed_entry_counterfactual_report",
        basic("missed_entry_counterfactual"),
    )
    monkeypatch.setattr(holding, "build_holding_exit_observation_report", held)
    return day, directory, auxiliary, calls


def test_postclose_phases_freeze_prefix_then_hold_after_auxiliary_without_recompute(
    tmp_path, monkeypatch
):
    day, directory, auxiliary, calls = _postclose_phase_fixture(tmp_path, monkeypatch)
    prefix = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    assert calls == [
        "trade_review",
        "post_sell_feedback",
        "missed_entry_counterfactual",
    ]
    full_manifest = (
        directory / "manifests" / f"monitor_snapshot_manifest_{day}_postclose_exit.json"
    )
    assert not full_manifest.exists() and "holding_exit_observation" not in prefix
    assert service.verified_postclose_exit_prefix_manifest(
        day, data_root=tmp_path
    ) == Path(prefix["snapshot_manifest"])
    prefix_bytes = Path(prefix["snapshot_manifest"]).read_bytes()
    before = {
        key: Path(prefix[key]).read_bytes() for key in service.POSTCLOSE_PREFIX_KINDS
    }
    auxiliary.write_text("before\nafter-auxiliary-producer\n")
    suffix = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="holding_suffix"
    )
    assert calls == [
        "trade_review",
        "post_sell_feedback",
        "missed_entry_counterfactual",
        "holding_exit_observation",
    ]
    assert suffix["full_snapshot_native_verified"] is True
    assert json.loads(Path(suffix["holding_exit_observation"]).read_bytes())[
        "fixture_auxiliary_source"
    ].endswith("after-auxiliary-producer\n")
    assert {
        key: Path(suffix[key]).read_bytes() for key in service.POSTCLOSE_PREFIX_KINDS
    } == before
    assert Path(prefix["snapshot_manifest"]).read_bytes() == prefix_bytes
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        == full_manifest
    )
    assert set(
        json.loads(full_manifest.read_bytes())["snapshot_kinds"]
    ) == service.POSTCLOSE_PREFIX_KINDS | {"holding_exit_observation"}
    assert not list(
        full_manifest.parent.glob(
            f".{full_manifest.name}.holding_suffix.*.candidate.json"
        )
    )


@pytest.mark.parametrize(
    "mutation", ["prefix_bytes", "fact_projection", "cost", "pipeline", "manifest"]
)
def test_postclose_holding_suffix_rejects_changed_prefix_before_holding_build(
    tmp_path, monkeypatch, mutation
):
    import os
    from src.engine.lifecycle.broker_cost_reconciliation import receipt_path

    day, directory, _, calls = _postclose_phase_fixture(tmp_path, monkeypatch)
    prefix = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    if mutation == "prefix_bytes":
        with Path(prefix["post_sell_feedback"]).open("ab") as handle:
            handle.write(b" ")
    elif mutation == "fact_projection":
        with (directory / f"trade_review_{day}.fact_projection.json").open(
            "ab"
        ) as handle:
            handle.write(b" ")
    elif mutation == "cost":
        path = receipt_path(tmp_path, day, "1")
        path.parent.mkdir(parents=True)
        path.write_text('{"corrected":true}')
    elif mutation == "pipeline":
        path = tmp_path / f"pipeline_events/pipeline_events_{day}.jsonl"
        path.parent.mkdir()
        path.write_text("{}\n")
        stamp = Path(prefix["snapshot_manifest"]).stat().st_mtime_ns + 1000000000
        os.utime(path, ns=(stamp, stamp))
    else:
        with Path(prefix["snapshot_manifest"]).open("ab") as handle:
            handle.write(b"x")
    assert (
        service.verified_postclose_exit_prefix_manifest(day, data_root=tmp_path) is None
    )
    with pytest.raises((ValueError, OSError)):
        service.save_monitor_snapshots_for_date_with_profile(
            day, profile="postclose_exit", postclose_phase="holding_suffix"
        )
    assert calls == [
        "trade_review",
        "post_sell_feedback",
        "missed_entry_counterfactual",
    ]


def test_postclose_holding_suffix_prefix_mutation_during_holding_does_not_publish_full(
    tmp_path, monkeypatch
):
    from src.engine import holding_exit_observation_report as holding

    day, directory, _, _ = _postclose_phase_fixture(tmp_path, monkeypatch)
    prefix = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    original = holding.build_holding_exit_observation_report

    def changed(**kwargs):
        result = original(**kwargs)
        with Path(prefix["post_sell_feedback"]).open("ab") as handle:
            handle.write(b" ")
        return result

    monkeypatch.setattr(holding, "build_holding_exit_observation_report", changed)
    with pytest.raises(ValueError, match="prefix_changed_during_holding_build"):
        service.save_monitor_snapshots_for_date_with_profile(
            day, profile="postclose_exit", postclose_phase="holding_suffix"
        )
    assert not (
        directory / "manifests" / f"monitor_snapshot_manifest_{day}_postclose_exit.json"
    ).exists()


@pytest.mark.parametrize(
    "suffix",
    [
        ".jsonl",
        ".late.jsonl",
        ".jsonl.gz",
        ".late.jsonl.gz",
        ".jsonl.archive_receipt.json",
        ".late.jsonl.archive_receipt.json",
        ".jsonl.gz.archive_receipt.json",
        ".late.jsonl.gz.archive_receipt.json",
    ],
)
@pytest.mark.parametrize("existed", [False, True])
def test_postclose_prefix_raw_seal_rejects_new_or_changed_partition_even_restored_mtime(
    tmp_path, monkeypatch, suffix, existed
):
    import os

    day, _, _, calls = _postclose_phase_fixture(tmp_path, monkeypatch)
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}{suffix}"
    raw.parent.mkdir()
    if existed:
        raw.write_bytes(b"original\n")
    prefix = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    stamp = (
        raw.stat().st_mtime_ns
        if existed
        else Path(prefix["snapshot_manifest"]).stat().st_mtime_ns - 1000000
    )
    raw.write_bytes(b"modified\n")
    os.utime(raw, ns=(stamp, stamp))
    assert (
        service.verified_postclose_exit_prefix_manifest(day, data_root=tmp_path) is None
    )
    with pytest.raises(ValueError, match="pipeline_generation_changed"):
        service.save_monitor_snapshots_for_date_with_profile(
            day, profile="postclose_exit", postclose_phase="holding_suffix"
        )
    assert calls == [
        "trade_review",
        "post_sell_feedback",
        "missed_entry_counterfactual",
    ]


def test_postclose_prefix_raw_mutation_during_producer_does_not_publish_prefix(
    tmp_path, monkeypatch
):
    from src.engine import sniper_post_sell_feedback as post_sell

    day, directory, _, _ = _postclose_phase_fixture(tmp_path, monkeypatch)
    original = post_sell.build_post_sell_feedback_report

    def changed(**kwargs):
        raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.late.jsonl"
        raw.parent.mkdir()
        raw.write_text("{}\n")
        return original(**kwargs)

    monkeypatch.setattr(post_sell, "build_post_sell_feedback_report", changed)
    with pytest.raises(ValueError, match="pipeline_changed_during_build"):
        service.save_monitor_snapshots_for_date_with_profile(
            day, profile="postclose_exit", postclose_phase="completion_prefix"
        )
    assert not (
        directory
        / "manifests"
        / f"monitor_snapshot_manifest_{day}_postclose_exit_completion_prefix.json"
    ).exists()


@pytest.mark.parametrize(
    "mutation_time",
    ["before_native_validation", "during_native_validation", "after_native_validation"],
)
@pytest.mark.parametrize("previous_exists", [False, True])
def test_postclose_suffix_full_publication_keeps_raw_generation_seal(
    tmp_path, monkeypatch, mutation_time, previous_exists
):
    day, directory, _, _ = _postclose_phase_fixture(tmp_path, monkeypatch)
    service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    manifest = (
        directory / "manifests" / f"monitor_snapshot_manifest_{day}_postclose_exit.json"
    )
    previous = b'{"original_previous_canonical_bytes":true}\n'
    if previous_exists:
        manifest.write_bytes(previous)
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.late.jsonl"

    def advance():
        raw.parent.mkdir(exist_ok=True)
        raw.write_text("{}\n")

    if mutation_time == "during_native_validation":
        original = service._sha256_file

        def changed(path):
            candidates = manifest.parent.glob(
                f".{manifest.name}.holding_suffix.*.candidate.json"
            )
            if path.name == f"holding_exit_observation_{day}.json" and any(
                p.stat().st_size for p in candidates
            ):
                advance()
            return original(path)

        monkeypatch.setattr(service, "_sha256_file", changed)
        with pytest.raises(ValueError, match="full_generation_invalid"):
            service.save_monitor_snapshots_for_date_with_profile(
                day, profile="postclose_exit", postclose_phase="holding_suffix"
            )
    elif mutation_time == "before_native_validation":
        original = service.save_monitor_snapshot_manifest

        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            advance()
            return result

        monkeypatch.setattr(service, "save_monitor_snapshot_manifest", changed)
        with pytest.raises(ValueError, match="full_generation_invalid"):
            service.save_monitor_snapshots_for_date_with_profile(
                day, profile="postclose_exit", postclose_phase="holding_suffix"
            )
    else:
        original = service._verified_postclose_exit_snapshot_manifest

        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            advance()
            return result

        monkeypatch.setattr(
            service, "_verified_postclose_exit_snapshot_manifest", changed
        )
        with pytest.raises(
            ValueError, match="prefix_changed_during_holding_publication"
        ):
            service.save_monitor_snapshots_for_date_with_profile(
                day, profile="postclose_exit", postclose_phase="holding_suffix"
            )
    if previous_exists:
        assert manifest.read_bytes() == previous
    else:
        assert not manifest.exists()
    candidates = list(
        manifest.parent.glob(f".{manifest.name}.holding_suffix.*.candidate.json")
    )
    assert len(candidates) == 1
    failed = json.loads(candidates[0].read_bytes())
    assert failed["postclose_phase"] == "holding_suffix"
    assert set(failed["snapshot_kinds"]) == service.POSTCLOSE_PREFIX_KINDS | {
        "holding_exit_observation"
    }


def test_postclose_suffix_full_manifest_allows_existing_lossless_raw_archive(
    tmp_path, monkeypatch
):
    from src.engine import compress_db_backfilled_files as archive

    day, _, _, _ = _postclose_phase_fixture(tmp_path, monkeypatch)
    raw = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir()
    raw.write_text("{}\n")
    service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    result = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="holding_suffix"
    )
    # Use the existing native archive producer, including verified bytes and
    # its distinct raw-pipeline receipt; the temporal seal is not a startup gate.
    assert archive._gzip_file(raw, dry_run=False)[0] is True
    receipt = json.loads(Path(str(raw) + ".gz.archive_receipt.json").read_bytes())
    assert receipt["schema"] == "pipeline_raw_archive_identity_v1"
    assert gzip.decompress(Path(str(raw) + ".gz").read_bytes()) == b"{}\n"
    assert "raw_pipeline_generation" not in json.loads(
        Path(result["snapshot_manifest"]).read_bytes()
    )
    assert service.verified_postclose_exit_snapshot_manifest(
        day, data_root=tmp_path
    ) == Path(result["snapshot_manifest"])


def test_postclose_phase_all_preserves_original_four_snapshot_mode(
    tmp_path, monkeypatch
):
    day, _, _, calls = _postclose_phase_fixture(tmp_path, monkeypatch)
    result = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit"
    )
    assert calls == [
        "trade_review",
        "post_sell_feedback",
        "missed_entry_counterfactual",
        "holding_exit_observation",
    ]
    assert set(
        json.loads(Path(result["snapshot_manifest"]).read_bytes())["snapshot_kinds"]
    ) == set(calls)
    assert service.verified_postclose_exit_snapshot_manifest(
        day, data_root=tmp_path
    ) == Path(result["snapshot_manifest"])


@pytest.mark.parametrize("phase", ["completion_prefix", "holding_suffix"])
def test_postclose_phase_rejected_for_other_profiles(tmp_path, monkeypatch, phase):
    with pytest.raises(ValueError, match="snapshot_phase_invalid"):
        service.save_monitor_snapshots_for_date_with_profile(
            "2026-10-16", profile="intraday_light", postclose_phase=phase
        )


@pytest.mark.parametrize(
    "phase,valid",
    [
        ("completion_prefix", True),
        ("holding_suffix", True),
        ("completion_prefix", False),
        ("holding_suffix", False),
    ],
)
def test_postclose_phase_wrapper_preserves_prefix_receipt_and_only_aliases_verified_full(
    tmp_path, phase, valid
):
    import os, subprocess

    root = Path(__file__).resolve().parents[2]
    script = (root / "deploy/run_monitor_snapshot_safe.sh").read_text()
    function = (
        "write_completion_artifact() {"
        + script.split("write_completion_artifact() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    project = tmp_path / "project with spaces"
    (project / "tmp").mkdir(parents=True)
    day = "2026-10-16"
    directory = project / "data/report/monitor_snapshots"
    (directory / "manifests").mkdir(parents=True)
    kinds = {"trade_review", "post_sell_feedback", "missed_entry_counterfactual"}
    if phase == "holding_suffix":
        kinds.add("holding_exit_observation")
    suffix = "_completion_prefix" if phase == "completion_prefix" else ""
    manifest = (
        directory
        / "manifests"
        / f"monitor_snapshot_manifest_{day}_postclose_exit{suffix}.json"
    )
    paths = {kind: str(directory / f"{kind}_{day}.json") for kind in kinds}
    manifest.write_text(
        json.dumps(
            dict(
                target_date=day,
                profile="postclose_exit",
                postclose_phase=phase,
                snapshot_kinds=sorted(kinds),
                snapshot_paths=paths,
            )
        )
    )
    snapshots = {
        **paths,
        "postclose_phase": phase,
        "snapshot_manifest": str(manifest),
        "completion_scope": (
            "completion_prefix_only"
            if phase == "completion_prefix"
            else "full_postclose_snapshot"
        ),
    }
    if phase == "holding_suffix":
        snapshots["full_snapshot_native_verified"] = valid
    elif not valid:
        snapshots["holding_exit_observation"] = "/wrong/holding.json"
    result = tmp_path / "output.json"
    result.write_text(
        json.dumps(
            dict(
                target_date=day,
                profile="postclose_exit",
                postclose_phase=phase,
                status="success",
                snapshots=snapshots,
            )
        )
        + "\n"
    )
    canonical = (
        project / "tmp" / f"monitor_snapshot_completion_{day}_postclose_exit.json"
    )
    canonical.write_text('{"status":"original_full"}')
    artifact = (
        project
        / "tmp"
        / f"monitor_snapshot_completion_{day}_postclose_exit_{phase}.json"
    )
    completed = subprocess.run(
        [
            "bash",
            "-c",
            function + '\nwrite_completion_artifact "" "$RESULT_FILE" 123\n',
        ],
        cwd=root,
        env={
            **os.environ,
            "PROJECT_DIR": str(project),
            "VENV_PY": str(root / ".venv/bin/python"),
            "TARGET_DATE": day,
            "PROFILE": "postclose_exit",
            "POSTCLOSE_PHASE": phase,
            "COMPLETION_ARTIFACT_FILE": str(artifact),
            "ASYNC_RESULT_HINT": str(tmp_path / "absent"),
            "LOG_FILE": str(tmp_path / "snapshot.log"),
            "RESULT_FILE": str(result),
        },
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(artifact.read_bytes())
    assert payload["status"] == ("success" if valid else "failed")
    assert payload["postclose_phase"] == phase
    if phase == "holding_suffix" and valid:
        assert canonical.read_bytes() == artifact.read_bytes()
        assert payload["snapshot_count"] == 4
    else:
        assert canonical.read_text() == '{"status":"original_full"}'
    if phase == "completion_prefix" and valid:
        assert payload["snapshot_count"] == 3


def test_postclose_phase_safe_wrapper_passes_explicit_phase_to_existing_cli():
    import os, subprocess

    root = Path(__file__).resolve().parents[2]
    script = (root / "deploy/run_monitor_snapshot_safe.sh").read_text()
    function = (
        "build_throttled_command() {"
        + script.split("build_throttled_command() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    completed = subprocess.run(
        [
            "bash",
            "-c",
            function
            + '\nSNAPSHOT_CMD=(); build_throttled_command SNAPSHOT_CMD; printf "%s\\n" "${SNAPSHOT_CMD[@]}"',
        ],
        env={
            **os.environ,
            "TARGET_DATE": "2026-10-16",
            "PROFILE": "postclose_exit",
            "POSTCLOSE_PHASE": "completion_prefix",
            "VENV_PY": "/project/.venv/bin/python",
            "IO_DELAY_SEC": "0",
            "IONICE_CLASS": "-1",
            "NICE_COMMAND": "missing-test-command",
            "CPU_AFFINITY": "",
        },
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    args = completed.stdout.splitlines()
    assert args[args.index("--postclose-phase") + 1] == "completion_prefix"
    assert args[args.index("-m") + 1] == "src.engine.run_monitor_snapshot"


@pytest.mark.parametrize("mutation", ["growth", "replace"])
def test_phase_completion_manifest_read_is_bounded_and_replacement_guarded(
    tmp_path, monkeypatch, mutation
):
    import io
    import os

    day = "2026-10-16"
    phase = "completion_prefix"
    kinds = set(service.POSTCLOSE_PREFIX_KINDS)
    manifest = (
        tmp_path
        / f"monitor_snapshot_manifest_{day}_postclose_exit_completion_prefix.json"
    )
    paths = {key: str(tmp_path / f"{key}.json") for key in kinds}
    body = dict(
        target_date=day,
        profile="postclose_exit",
        postclose_phase=phase,
        snapshot_kinds=sorted(kinds),
        snapshot_paths=paths,
    )
    raw = json.dumps(body).encode()
    manifest.write_bytes(raw)
    result = tmp_path / "result.json"
    result.write_text(
        json.dumps(
            dict(
                status="success",
                target_date=day,
                snapshots={
                    **paths,
                    "postclose_phase": phase,
                    "snapshot_manifest": str(manifest),
                },
            )
        )
    )
    original_open = Path.open
    original_fdopen = os.fdopen
    reads = []

    class MutatingRead(io.BytesIO):
        def read(self, n=-1):
            reads.append(n)
            assert n == 1024 * 1024 + 1
            value = super().read(n)
            if mutation == "replace":
                replacement = manifest.with_suffix(".replacement")
                with original_open(replacement, "wb") as handle:
                    handle.write(raw)
                replacement.replace(manifest)
            return value

    def opened(descriptor, *args, **kwargs):
        if os.readlink(f"/proc/self/fd/{descriptor}") == str(manifest):
            return MutatingRead(
                b" " * (1024 * 1024 + 1) if mutation == "growth" else raw
            )
        return original_fdopen(descriptor, *args, **kwargs)

    monkeypatch.setattr(os, "fdopen", opened)
    normalized = runtime.normalize_result_payload(
        target_date=day,
        profile="postclose_exit",
        result_file=str(result),
        postclose_phase=phase,
    )
    assert reads == [1024 * 1024 + 1]
    assert normalized["status"] == "failed"
    assert normalized["error_kind"] == "SnapshotPhaseContractInvalid"


@pytest.mark.parametrize("reader", ["completion", "prefix"])
@pytest.mark.parametrize("mutation", ["fifo", "replace_fifo", "replace_symlink"])
def test_phase_metadata_rejects_special_files_and_open_time_replacement(
    tmp_path, monkeypatch, reader, mutation
):
    import os

    day, directory, _, _ = _postclose_phase_fixture(tmp_path, monkeypatch)
    prefix = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    manifest = Path(prefix["snapshot_manifest"])
    result = tmp_path / "phase-result.json"
    result.write_text(
        json.dumps(dict(status="success", target_date=day, snapshots=prefix))
    )
    original_open = os.open
    original_path_open = Path.open
    seen = []

    # A regressed blocking Path.open fails immediately instead of hanging the
    # regression suite on a FIFO with no writer.
    def reject_blocking(path, *args, **kwargs):
        if path == manifest:
            pytest.fail("phase metadata used blocking pathname open")
        return original_path_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", reject_blocking)
    if mutation == "fifo":
        manifest.unlink()
        os.mkfifo(manifest)
    else:
        alternative = manifest.with_suffix(".replacement.json")
        alternative.write_text("{}")

        def replaced(path, flags, *args, **kwargs):
            if Path(path) == manifest and not seen:
                seen.append(flags)
                assert flags & os.O_NOFOLLOW and flags & os.O_NONBLOCK
                manifest.unlink()
                if mutation == "replace_fifo":
                    os.mkfifo(manifest)
                else:
                    manifest.symlink_to(alternative)
            return original_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(os, "open", replaced)
    if reader == "prefix":
        assert (
            service.verified_postclose_exit_prefix_manifest(day, data_root=tmp_path)
            is None
        )
    else:
        observed = runtime.normalize_result_payload(
            target_date=day,
            profile="postclose_exit",
            result_file=str(result),
            postclose_phase="completion_prefix",
        )
        assert observed["status"] == "failed"
        assert observed["error_kind"] == "SnapshotPhaseContractInvalid"
    assert bool(seen) == (mutation != "fifo")


def test_snapshot_async_wait_propagates_actual_failed_child_status(tmp_path):
    import os, subprocess

    script = (
        Path(__file__).resolve().parents[2] / "deploy/run_monitor_snapshot_safe.sh"
    ).read_text()
    function = (
        "wait_for_async_completion() {"
        + script.split("wait_for_async_completion() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    invoked = tmp_path / "writer-status"
    shell = (
        function
        + '\nwrite_completion_artifact() { printf "%s" "$1" > "$STATUS_FILE"; }\n(exit 7) &\nchild=$!\nwait_for_async_completion "$child" /unused\n'
    )
    completed = subprocess.run(
        ["bash", "-c", shell],
        env={**os.environ, "ASYNC_WAIT_SEC": "5", "STATUS_FILE": str(invoked)},
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 7, completed.stdout + completed.stderr
    assert invoked.read_text() == "failed"


@pytest.mark.parametrize("normalized_status", ["success", "failed"])
def test_snapshot_sync_cooldown_and_exit_follow_normalized_completion(
    tmp_path, normalized_status
):
    import os, subprocess

    script = (
        Path(__file__).resolve().parents[2] / "deploy/run_monitor_snapshot_safe.sh"
    ).read_text()
    function = (
        "run_snapshot_once() {"
        + script.split("run_snapshot_once() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    output = tmp_path / "output"
    cooldown = tmp_path / "success.state"
    stubs = """
check_recent_success() { return 1; }
build_throttled_command() { SNAPSHOT_CMD=(bash -c 'printf "{\\\"status\\\":\\\"success\\\"}\\n"'); }
print_summary() { :; }
write_completion_artifact() { :; }
completion_artifact_status() { printf "%s" "$NORMALIZED_STATUS"; }
if run_snapshot_once "$OUTPUT_FILE"; then exit 0; else exit $?; fi
"""
    env = {
        **os.environ,
        "NORMALIZED_STATUS": normalized_status,
        "OUTPUT_FILE": str(output),
        "COOLDOWN_STATE_FILE": str(cooldown),
        "MAX_RETRIES": "1",
        "LOCK_WAIT_SEC": "0",
        "LOCK_FILE": str(tmp_path / "snapshot.lock"),
        "LOG_FILE": str(tmp_path / "snapshot.log"),
        "IN_PREOPEN": "0",
        "BOT_RUNNING": "0",
        "ALLOW_PREOPEN_WITH_BOT": "0",
        "PROFILE": "postclose_exit",
        "MANIFEST_PATH": str(tmp_path / "manifest"),
        "ALLOW_EXISTING_FULL_BUILD_WITH_BOT": "0",
        "START_JITTER_SEC": "0",
        "TARGET_DATE": "2026-10-16",
        "IO_DELAY_SEC": "0",
        "NOTIFY_ADMIN": "0",
        "COOLDOWN_SEC": "60",
        "FORCE_SNAPSHOT": "0",
        "TIMEOUT_SEC": "10",
        "KEEP_OUTPUT_FILE": "1",
        "NOTIFY_ONLY": "0",
    }
    completed = subprocess.run(
        ["bash", "-c", function + stubs], env=env, capture_output=True, text=True
    )
    assert completed.returncode == (0 if normalized_status == "success" else 1), (
        completed.stdout + completed.stderr
    )
    assert cooldown.exists() == (normalized_status == "success")
    assert output.exists()


def test_monitor_snapshot_roundtrip(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    manifest_dir = snapshot_dir / "manifests"
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    payload = {"date": "2026-04-06", "value": 123}
    path = service.save_monitor_snapshot("trade_review", "2026-04-06", payload)

    assert path == snapshot_dir / "trade_review_2026-04-06.json"
    loaded = service.load_monitor_snapshot("trade_review", "2026-04-06")
    assert loaded is not None
    assert loaded == payload
    assert not list(snapshot_dir.glob(".trade_review_2026-04-06.json.*.tmp"))
    manifest = service.save_monitor_snapshot_manifest(
        "2026-04-06",
        profile="full",
        snapshots={"trade_review": str(path)},
    )
    assert manifest.parent == manifest_dir
    assert json.loads(manifest.read_text())["snapshot_paths"] == {
        "trade_review": str(path)
    }


@pytest.mark.parametrize("transactional", [False, True])
def test_snapshot_date_header_survives_sorted_payload_roundtrip(
    tmp_path, monkeypatch, transactional
):
    from src.engine.automation.postclose_finalization_generation import _snapshot_date
    from src.engine.infrastructure.research_release_transition import Transition

    snapshot_dir = tmp_path / "data/report/monitor_snapshots"
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    payload = {"a_large": "x" * 5000, "date": "2026-10-08"}
    saved = []

    def write():
        saved.append(
            service.save_monitor_snapshot(
                "holding_exit_observation", "2026-10-08", payload
            )
        )

    if transactional:
        tx = Transition(tmp_path, "date_header")
        with tx.owner():
            tx.execute([write], verify=lambda: None)
    else:
        write()
    assert _snapshot_date(saved[0], compressed=False) == "2026-10-08"
    assert json.loads(saved[0].read_bytes()) == payload
    assert next(iter(payload)) == "a_large"


@pytest.mark.parametrize("database_only", [False, True])
def test_postclose_trade_review_completed_projection_is_sealed_and_consumed(
    tmp_path, monkeypatch, database_only
):
    from src.engine import holding_exit_observation_report as holding
    from src.engine.sniper_trade_review_report import completed_census_manifest

    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(
        service, "MONITOR_SNAPSHOT_MANIFEST_DIR", snapshot_dir / "manifests"
    )
    day = "2026-09-30"
    payload = {
        "date": day,
        "code": None,
        "since": None,
        "meta": {
            "warnings": [],
            "snapshot_profile": "postclose_exit",
            "sell_completed_event_ids": [],
            "trailing_event_source_receipts": [],
        },
        "metrics": {
            "canonical_completed_trades": 0,
            "completed_trades": 0,
            "open_scalp_position_projection_count": 0,
            "open_scalp_position_projection_status": "current_db_census",
        },
        "sections": {
            "completed_trade_projection": [],
            "open_scalp_position_projection": [],
        },
    }
    if database_only:
        witness = "a" * 64
        payload["meta"]["database_completed_sources"] = [
            dict(
                id=49362,
                status="COMPLETED",
                sell_time=day + " 09:44:00",
                source_row_sha256=witness,
            )
        ]
        payload["sections"]["completed_trade_projection"] = [
            dict(
                id=49362,
                status="COMPLETED",
                completion_observed_date=day,
                profit_rate=None,
                database_completion_source_sha256=witness,
                completion_source_status="database_completed_native_terminal_unobserved",
                strict_completion_status="excluded",
                strict_completion_reasons=[
                    "source_gap_native_sell_completed_event_missing"
                ],
            )
        ]
        payload["metrics"].update(
            canonical_completed_trades=1,
            native_sell_completed_trade_count=0,
            database_only_completed_trade_count=1,
        )
    payload["meta"]["completed_census_manifest"] = completed_census_manifest(payload)
    path = service.save_monitor_snapshot("trade_review", day, payload)
    monkeypatch.setattr(
        holding,
        "_monitor_snapshot_path",
        lambda kind, target: path if kind == "trade_review" and target == day else None,
    )
    snapshots, sources = holding._load_saved_snapshots("trade_review", [day])
    assert len(snapshots) == 1
    assert snapshots[0]["schema"] == "trade_review_completed_projection_sidecar_v1"
    collected, gaps = holding._collect_completed_trade_rows(
        snapshots, data_root=tmp_path
    )
    assert len(collected) == int(database_only)
    assert gaps == (
        [{"date": day, "reason": "completion_day_terminal_receipt_missing"}]
        if database_only
        else []
    )
    assert sources == [str(path.with_suffix(".completed_projection.json"))]
    sidecar = path.with_suffix(".completed_projection.json")
    observed = {
        p: (p.read_bytes(), p.stat().st_ino, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
        for p in (path, sidecar)
    }
    for mutation in ("ids", "census_missing", "open_missing", "wrong_date"):
        invalid = json.loads(json.dumps(payload))
        if mutation == "ids":
            invalid["meta"]["sell_completed_event_ids"] = [49363]
        elif mutation == "census_missing":
            invalid["meta"].pop("completed_census_manifest")
        elif mutation == "open_missing":
            invalid["sections"].pop("open_scalp_position_projection")
        else:
            invalid["date"] = "2026-10-01"
        with pytest.raises(
            ValueError,
            match="trade_review_(completed_projection_invalid|open_position_projection_missing)",
        ):
            service.save_monitor_snapshot("trade_review", day, invalid)
        for source, before in observed.items():
            assert (
                source.read_bytes(),
                source.stat().st_ino,
                source.stat().st_mtime_ns,
                source.stat().st_ctime_ns,
            ) == before
    altered = json.loads(sidecar.read_text())
    altered["metrics"]["canonical_completed_trades"] += 1
    sidecar.write_text(json.dumps(altered))
    assert holding._verified_trade_review_projection(path, day) is None


@pytest.mark.parametrize("day", ["2026-09-30", "2026-10-12"])
def test_postclose_snapshot_reuse_requires_exact_hashes_and_pipeline_cutoff(
    tmp_path, monkeypatch, day
):
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.holding_window_generation import capture_window

    directory = tmp_path / "report" / "monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(
        service, "MONITOR_SNAPSHOT_MANIFEST_DIR", directory / "manifests"
    )
    trade = {
        "date": day,
        "code": None,
        "since": None,
        "meta": {
            "warnings": [],
            "snapshot_profile": "postclose_exit",
            "sell_completed_event_ids": [],
            "trailing_event_source_receipts": [],
        },
        "metrics": {
            "canonical_completed_trades": 0,
            "open_scalp_position_projection_count": 0,
        },
        "sections": {
            "completed_trade_projection": [],
            "open_scalp_position_projection": [],
        },
    }
    trade["meta"]["completed_census_manifest"] = completed_census_manifest(trade)
    paths = {"trade_review": service.save_monitor_snapshot("trade_review", day, trade)}
    for kind in (
        "post_sell_feedback",
        "missed_entry_counterfactual",
        "holding_exit_observation",
    ):
        body = {"date": day, "meta": {"snapshot_profile": "postclose_exit"}}
        if kind == "holding_exit_observation":
            window = capture_window(tmp_path, [day])
            body.update(
                input_window_dependencies=window,
                input_window_generation_sha256=window["input_window_generation_sha256"],
            )
            if day >= "2026-10-12":
                from src.engine.scalping.holding_vote_experiment import code_sha

                body["holding_path_vote_replay"] = {
                    "vote_numeric_research": {
                        "status": "experiment_not_armed",
                        "code_sha256": code_sha(),
                    }
                }
        paths[kind] = service.save_monitor_snapshot(kind, day, body)
    pipeline = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    pipeline.parent.mkdir()
    pipeline.write_text("{}\n")
    manifest = service.save_monitor_snapshot_manifest(
        day,
        profile="postclose_exit",
        snapshots={kind: str(path.resolve()) for kind, path in paths.items()},
    )
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        == manifest
    )
    if day >= "2026-10-12":
        from src.engine.scalping import holding_vote_experiment as experiment

        with monkeypatch.context() as patch:
            patch.setattr(experiment, "code_sha", lambda: "changed-code")
            assert (
                service.verified_postclose_exit_snapshot_manifest(
                    day, data_root=tmp_path
                )
                is None
            )
        holding = paths["holding_exit_observation"]
        body = json.loads(holding.read_bytes())
        body["holding_path_vote_replay"]["vote_numeric_research"][
            "status"
        ] = "incumbent_unverified"
        service.save_monitor_snapshot("holding_exit_observation", day, body)
        service.save_monitor_snapshot_manifest(
            day,
            profile="postclose_exit",
            snapshots={kind: str(path.resolve()) for kind, path in paths.items()},
        )
        assert (
            service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
            is None
        )
        body["holding_path_vote_replay"]["vote_numeric_research"][
            "status"
        ] = "experiment_not_armed"
        service.save_monitor_snapshot("holding_exit_observation", day, body)
        service.save_monitor_snapshot_manifest(
            day,
            profile="postclose_exit",
            snapshots={kind: str(path.resolve()) for kind, path in paths.items()},
        )
    paths["post_sell_feedback"].write_text("{}")
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        is None
    )
    service.save_monitor_snapshot(
        "post_sell_feedback",
        day,
        {"date": day, "meta": {"snapshot_profile": "postclose_exit"}},
    )
    service.save_monitor_snapshot_manifest(
        day,
        profile="postclose_exit",
        snapshots={kind: str(path.resolve()) for kind, path in paths.items()},
    )
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        == manifest
    )
    import os

    newer = manifest.stat().st_mtime_ns + 2_000_000_000
    os.utime(pipeline, ns=(newer, newer))
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        is None
    )


def test_completed_census_seals_actual_saved_profile(tmp_path, monkeypatch):
    from src.engine.sniper_trade_review_report import (
        completed_census_manifest,
        verify_completed_census_manifest,
    )

    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", tmp_path)
    day = "2026-09-28"
    payload = {
        "date": day,
        "code": None,
        "since": None,
        "meta": {"sell_completed_event_ids": [], "trailing_event_source_receipts": []},
        "metrics": {"canonical_completed_trades": 0},
        "sections": {
            "completed_trade_projection": [],
            "open_scalp_position_projection": [],
        },
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


@pytest.mark.parametrize("failure_stage", ["dump", "replace"])
def test_completion_artifact_write_failure_preserves_previous_bytes(
    tmp_path, monkeypatch, failure_stage
):
    artifact = tmp_path / "monitor_snapshot_completion_2026-10-16_intraday_light.json"
    previous = b'{"status":"success","generation":"previous"}\n'
    artifact.write_bytes(previous)

    def fail_dump(payload, handle, **kwargs):
        handle.write('{"status":"failed",')
        handle.flush()
        raise OSError("fixture_completion_dump_failed")

    def fail_replace(source, destination):
        assert Path(source).parent == artifact.parent
        assert Path(destination) == artifact
        raise OSError("fixture_completion_replace_failed")

    if failure_stage == "dump":
        monkeypatch.setattr(runtime.json, "dump", fail_dump)
    else:
        monkeypatch.setattr(runtime.os, "replace", fail_replace)

    with pytest.raises(OSError, match=f"fixture_completion_{failure_stage}_failed"):
        runtime.write_completion_artifact(artifact, {"status": "failed"})

    assert artifact.read_bytes() == previous
    assert set(tmp_path.iterdir()) == {artifact}


def test_completion_artifact_readers_keep_complete_generation_during_partial_writes(
    tmp_path, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    day, profile = "2026-10-16", "intraday_light"
    monkeypatch.setattr(runtime, "TMP_DIR", tmp_path)
    artifact = runtime.completion_artifact_path(day, profile)

    def generation(number):
        return {
            "target_date": day,
            "profile": profile,
            "status": "success",
            "generation": number,
            "detail": str(number) * 2048,
        }

    previous = generation(0)
    runtime.write_completion_artifact(artifact, previous)
    partial_written, finish_write = Event(), Event()

    def paused_dump(payload, handle, **kwargs):
        encoded = json.dumps(payload, **kwargs)
        midpoint = len(encoded) // 2
        handle.write(encoded[:midpoint])
        handle.flush()
        partial_written.set()
        assert finish_write.wait(timeout=5), "reader did not release completion writer"
        handle.write(encoded[midpoint:])

    monkeypatch.setattr(runtime.json, "dump", paused_dump)
    with ThreadPoolExecutor(max_workers=1) as executor:
        for number in range(1, 9):
            partial_written.clear()
            finish_write.clear()
            following = generation(number)
            writer = executor.submit(
                runtime.write_completion_artifact, artifact, following
            )
            try:
                assert partial_written.wait(
                    timeout=5
                ), "writer did not reach partial output"
                for _ in range(16):
                    assert runtime.load_completion_artifact(day, profile) == previous
            finally:
                finish_write.set()
            assert writer.result(timeout=5) == artifact
            assert runtime.load_completion_artifact(day, profile) == following
            previous = following

    assert set(tmp_path.iterdir()) == {artifact}


def test_archive_and_replay_daily_log_slice(tmp_path, monkeypatch):
    archive_dir = tmp_path / "log_archive"
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

    from src.engine.sniper_trade_review_report import (
        completed_census_manifest,
        verify_completed_census_manifest,
    )

    def empty_trade_review(**kwargs):
        body = {
            "date": kwargs["target_date"],
            "meta": {"sell_completed_event_ids": []},
            "metrics": {"canonical_completed_trades": 0},
            "sections": {
                "completed_trade_projection": [],
                "open_scalp_position_projection": [],
            },
        }
        body["meta"]["completed_census_manifest"] = completed_census_manifest(body)
        return body

    monkeypatch.setitem(
        sys.modules,
        "src.engine.sniper_trade_review_report",
        types.SimpleNamespace(
            build_trade_review_report=empty_trade_review,
            completed_census_manifest=completed_census_manifest,
            verify_completed_census_manifest=verify_completed_census_manifest,
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
        "trade_review",
        "post_sell_feedback",
        "missed_entry_counterfactual",
        "holding_exit_observation",
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


def test_cost_only_revision_invalidates_sidecar_and_manifest_without_pipeline_changes(
    tmp_path, monkeypatch
):
    from src.engine import holding_exit_observation_report as holding
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.broker_cost_reconciliation import (
        source_generation,
        receipt_path,
    )
    from src.engine.lifecycle.holding_window_generation import capture_window

    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(service, "DATA_DIR", tmp_path)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(
        service, "MONITOR_SNAPSHOT_MANIFEST_DIR", directory / "manifests"
    )
    day = "2026-10-08"

    def save():
        trade = {
            "date": day,
            "code": None,
            "since": None,
            "meta": {
                "warnings": [],
                "snapshot_profile": "postclose_exit",
                "sell_completed_event_ids": [],
                "actual_cost_source_generation": source_generation(tmp_path, day),
            },
            "metrics": {"canonical_completed_trades": 0},
            "sections": {
                "completed_trade_projection": [],
                "open_scalp_position_projection": [],
            },
        }
        trade["meta"]["completed_census_manifest"] = completed_census_manifest(trade)
        paths = {
            "trade_review": service.save_monitor_snapshot("trade_review", day, trade)
        }
        for kind in (
            "post_sell_feedback",
            "missed_entry_counterfactual",
            "holding_exit_observation",
        ):
            body = {
                "date": day,
                "meta": {"snapshot_profile": "postclose_exit"},
                "actual_cost_source_generations": {
                    day: source_generation(tmp_path, day)
                },
            }
            if kind == "holding_exit_observation":
                window = capture_window(tmp_path, [day])
                body.update(
                    input_window_dependencies=window,
                    input_window_generation_sha256=window[
                        "input_window_generation_sha256"
                    ],
                )
            paths[kind] = service.save_monitor_snapshot(kind, day, body)
        manifest = service.save_monitor_snapshot_manifest(
            day,
            profile="postclose_exit",
            snapshots={kind: str(path) for kind, path in paths.items()},
        )
        return paths, manifest

    paths, manifest = save()
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        == manifest
    )
    cost_path = receipt_path(tmp_path, day, "1")
    cost_path.parent.mkdir(parents=True)
    cost_path.write_text('{"revision":1}')
    assert (
        holding._verified_trade_review_projection(
            paths["trade_review"], day, data_root=tmp_path
        )
        is None
    )
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        is None
    )
    with pytest.raises(ValueError):
        service.save_monitor_snapshot_manifest(
            day,
            profile="postclose_exit",
            snapshots={k: str(v) for k, v in paths.items()},
        )
    paths, manifest = save()
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        == manifest
    )
    cost_path.write_text('{"revision":2}')
    assert (
        service.verified_postclose_exit_snapshot_manifest(day, data_root=tmp_path)
        is None
    )


@pytest.mark.parametrize(
    "mutation",
    ["missing", "changed_current_code", "changed_recorded_code", "changed_cost_code"],
)
def test_prefix_reuse_requires_original_current_producer_generation(
    tmp_path, monkeypatch, mutation
):
    from src.engine.lifecycle.broker_cost_reconciliation import digest

    day, _, _, _ = _postclose_phase_fixture(tmp_path, monkeypatch)
    result = service.save_monitor_snapshots_for_date_with_profile(
        day, profile="postclose_exit", postclose_phase="completion_prefix"
    )
    path = Path(result["snapshot_manifest"])
    assert (
        service.verified_postclose_exit_prefix_manifest(day, data_root=tmp_path) == path
    )
    before = path.read_bytes()
    if mutation == "changed_cost_code":
        original = service._sha256_file
        monkeypatch.setattr(
            service,
            "_sha256_file",
            lambda p: (
                "f" * 64 if Path(p).name == "broker_cost_allocation.py" else original(p)
            ),
        )
    elif mutation == "changed_current_code":
        code = dict(service._postclose_prefix_producer_code_generation())
        code["sniper_trade_review_report.py"] = "f" * 64
        monkeypatch.setattr(
            service, "_postclose_prefix_producer_code_generation", lambda: code
        )
    else:
        body = json.loads(before)
        if mutation == "missing":
            body.pop("producer_code_generation")
        else:
            body["producer_code_generation"]["sniper_trade_review_report.py"] = "f" * 64
        body["artifact_sha256"] = digest(
            {k: v for k, v in body.items() if k != "artifact_sha256"}
        )
        path.write_text(json.dumps(body))
    assert (
        service.verified_postclose_exit_prefix_manifest(day, data_root=tmp_path) is None
    )
    if mutation == "changed_current_code":
        assert path.read_bytes() == before


@pytest.mark.parametrize("compressed", [False, True])
def test_snapshot_selected_sections_preserve_recent_rows_without_census(
    tmp_path, monkeypatch, compressed
):
    import gzip
    import json
    from src.engine import log_archive_service as owner

    monkeypatch.setattr(owner, "MONITOR_SNAPSHOT_DIR", tmp_path)
    path = tmp_path / "trade_review_2026-10-19.json"
    original = {
        "sections": {
            "recent_trades": [{"id": "a", "profit_rate": None}],
            "completed_trade_projection": [{"id": i} for i in range(3000)],
        },
        "meta": {"warnings": ["source_gap"]},
    }
    raw = json.dumps(original).encode()
    if compressed:
        path.with_suffix(".json.gz").write_bytes(gzip.compress(raw))
    else:
        path.write_bytes(raw)
    result = owner.load_monitor_snapshot(
        "trade_review", "2026-10-19", section_names=("recent_trades",)
    )
    assert result == {
        "sections": {"recent_trades": original["sections"]["recent_trades"]},
        "meta": original["meta"],
    }


def test_log_tail_is_bounded_and_matches_original_lines(tmp_path, monkeypatch):
    from src.engine.log_archive_service import tail_log_lines

    path = tmp_path / "cron.log"
    raw = (
        "prefix padding " * 30000
        + "\n"
        + "\n".join(f"line {i} 한글" for i in range(6000))
    ).encode()
    path.write_bytes(raw)
    assert tail_log_lines(path) == raw.decode().splitlines()[-5000:]
    monkeypatch.setattr(
        Path, "read_text", lambda *a, **k: pytest.fail("whole file read_text")
    )
    assert tail_log_lines(path, 2) == ["line 5998 한글", "line 5999 한글"]


def test_date_log_filter_keeps_late_rotation_and_archive_fallback(
    tmp_path, monkeypatch
):
    from src.engine import log_archive_service as owner
    import gzip

    monkeypatch.setattr(owner, "LOG_ARCHIVE_DIR", tmp_path / "archive")
    log = tmp_path / "live.log"
    log.write_text("[2026-10-18 09:00] OLD\n[2026-10-19 09:00] NEW\n")
    rotated = tmp_path / "live.log.1"
    rotated.write_text("[2026-10-19 08:00] LATE\n")
    archive = owner.archived_log_path(log, "2026-10-19")
    archive.parent.mkdir(parents=True)
    archive.write_bytes(gzip.compress(b"[2026-10-19 07:00] ARCHIVED\n"))
    assert owner.iter_target_log_lines([log], target_date="2026-10-19") == [
        "[2026-10-19 09:00] NEW",
        "[2026-10-19 08:00] LATE",
    ]
    log.unlink()
    rotated.unlink()
    assert owner.iter_target_log_lines([log], target_date="2026-10-19") == [
        "[2026-10-19 07:00] ARCHIVED"
    ]


def test_date_log_reuse_is_bound_to_generation_and_keeps_late_rows(
    tmp_path, monkeypatch
):
    from src.engine import log_archive_service as owner
    from src.engine.infrastructure.validation_digest_session import postclose_session

    path = tmp_path / "events.log"
    path.write_text(
        "[2026-10-18 10:00] OLD\n[2026-10-19 10:00] A\n[2026-10-19 10:01] B\n"
    )
    import builtins

    native = builtins.open
    opened = []

    def counted(candidate, *args, **kwargs):
        opened.append(candidate)
        return native(candidate, *args, **kwargs)

    monkeypatch.setattr(owner, "open", counted, raising=False)
    with postclose_session(tmp_path, "2026-10-19"):
        assert owner._read_matching_lines(
            path, target_date="2026-10-19", marker="A"
        ) == ["[2026-10-19 10:00] A"]
        assert owner._read_matching_lines(
            path, target_date="2026-10-19", marker="B"
        ) == ["[2026-10-19 10:01] B"]
        assert len(opened) == 1
        with path.open("a") as handle:
            handle.write("[2026-10-19 10:02] A late\n")
        assert (
            len(owner._read_matching_lines(path, target_date="2026-10-19", marker="A"))
            == 2
        )
        assert len(opened) == 2


def test_dated_log_cache_does_not_retain_large_unselected_population(tmp_path):
    from src.engine import log_archive_service as owner
    from src.engine.infrastructure.validation_digest_session import postclose_session

    path = tmp_path / "events.log"
    path.write_text(
        ("[2026-10-19 09:00] OTHER " + "x" * 1000 + "\n") * 1100
        + "[2026-10-19 09:01] SELECTED\n"
    )
    with postclose_session(tmp_path, "2026-10-19") as session:
        assert owner._read_matching_lines(
            path, target_date="2026-10-19", marker="SELECTED"
        ) == ["[2026-10-19 09:01] SELECTED"]
        assert not session.semantic_objects


def test_snapshot_rows_preserve_json_hash_order_slices_and_insert(tmp_path):
    import hashlib
    from src.engine.log_archive_service import SnapshotRows, snapshot_json_sha256

    values = [{"fields": {"한글": "큰 원천" * 100, "a": [1, None]}}, {"last": True}]
    rows = SnapshotRows(values)
    rows.insert(1, {"terminal": "observed"})
    values.insert(1, {"terminal": "observed"})
    assert rows == values
    assert rows[-1] == values[-1]
    assert rows[:2] == values[:2]
    assert list(reversed(list(rows))) == values[::-1]
    assert json.loads(json.dumps({"timeline": rows})) == {"timeline": values}
    path = tmp_path / "snapshot.json"
    with path.open("w") as output:
        json.dump({"timeline": rows}, output, ensure_ascii=False, indent=2)
    assert json.loads(path.read_text()) == {"timeline": values}
    expected = hashlib.sha256(
        json.dumps(
            values, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert snapshot_json_sha256(rows) == expected
    assert snapshot_json_sha256(SnapshotRows()) == snapshot_json_sha256([])
    rows._file.seek(rows._rows[0][0])
    rows._file.write(b"X")
    rows._cached = None
    with pytest.raises(ValueError, match="snapshot_private_row_changed"):
        rows[0]


def test_snapshot_timeline_build_has_bounded_resident_payload():
    import tracemalloc
    from src.engine.sniper_trade_review_report import HoldingEvent, _build_timeline

    def events():
        for index in range(1024):
            yield HoldingEvent(
                "2026-10-26 09:00:00",
                "TEST",
                "123456",
                "scalp_trailing_input_transition",
                {"id": "1", "proof": str(index) + "x" * 32768},
                "",
            )

    tracemalloc.start()
    try:
        timeline = _build_timeline(events())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(timeline) == 1024
    assert timeline[-1]["fields"]["proof"].startswith("1023")
    assert peak < 8 * 1024 * 1024


@pytest.mark.parametrize("compressed", [False, True])
@pytest.mark.parametrize("corrupt", [False, True])
def test_snapshot_row_projection_validates_excluded_timeline(
    tmp_path, monkeypatch, compressed, corrupt
):
    import gzip
    from src.engine import log_archive_service as owner
    from src.engine import sniper_performance_tuning_report as consumer

    monkeypatch.setattr(owner, "MONITOR_SNAPSHOT_DIR", tmp_path)
    path = tmp_path / "trade_review_2026-10-26.json"
    raw = '{"sections":{"recent_trades":[{"id":1,"profit_rate":null,"timeline":['
    raw += '{"stage":"quote","fields":{"reason":"kept"}},' * 3000
    raw += "INVALID" if corrupt else '{"stage":"terminal"}'
    raw += '],"compact_timeline":[{"stage":"terminal"}]}]},"meta":{"warnings":["source_gap"]}}'
    if compressed:
        path = path.with_suffix(".json.gz")
        path.write_bytes(gzip.compress(raw.encode()))
    else:
        path.write_text(raw)
    projected = owner.load_monitor_snapshot(
        "trade_review",
        "2026-10-26",
        section_names=("recent_trades",),
        excluded_row_fields=("timeline",),
    )
    if corrupt:
        assert projected is None
    else:
        expected = [
            {"id": 1, "profit_rate": None, "compact_timeline": [{"stage": "terminal"}]}
        ]
        assert projected["sections"]["recent_trades"] == expected
        assert consumer._build_current_trade_rows("2026-10-26") == (
            expected,
            ["source_gap"],
        )
        assert (
            gzip.decompress(path.read_bytes()).decode()
            if compressed
            else path.read_text()
        ) == raw


def test_snapshot_scratch_failure_is_not_published_as_a_source_gap(monkeypatch):
    from src.engine.log_archive_service import SnapshotRows

    rows = SnapshotRows()

    def failed_write(raw):
        raise OSError("scratch full")

    monkeypatch.setattr(rows._file, "write", failed_write)
    with pytest.raises(RuntimeError, match="snapshot_private_storage_write_failed"):
        rows.append({"source": "valid"})
    assert len(rows) == 0


def test_snapshot_private_storage_compresses_and_reuses_identical_rows():
    from src.engine.log_archive_service import SnapshotRows

    value = {"fields": {"evidence": "preserved quote " * 10000}, "pnl": None}
    rows = SnapshotRows([value] * 100)
    assert len(rows) == 100 and all(row == value for row in rows)
    assert len(set(rows._rows)) == 1
    assert rows._file.seek(0, 2) < len(json.dumps(value)) // 10


@pytest.mark.parametrize("compressed", [False, True])
def test_compact_snapshot_preserves_carry_reader_and_whole_source_binding(
    tmp_path, monkeypatch, compressed
):
    import hashlib
    from src.engine import compress_db_backfilled_files as archive
    from src.engine.lifecycle.snapshot_archive import generation

    day = "2026-10-26"
    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", directory)
    # Force the large-source reader without a resident multi-GB fixture.
    event = dict(
        stage="holding_started",
        timestamp=day + " 09:00:00",
        fields={"id": "1", "proof": "x" * 1000},
    )
    carried = dict(
        stage="position_rebased_after_fill",
        timestamp=day + " 09:01:00",
        fields={"id": "1", "fill_qty": 1, "cost": None},
    )
    body = dict(
        date=day,
        meta={"warnings": []},
        metrics={"open_scalp_position_projection_status": "current_db_census"},
        sections={
            "recent_trades": [{"timeline": [event] * 9000}],
            "open_scalp_position_projection": [
                dict(id=1, code="123456", timeline=[carried])
            ],
        },
    )
    path = service.save_monitor_snapshot("trade_review", day, body)
    raw = path.read_bytes()
    assert len(raw) < len(json.dumps(body, ensure_ascii=False, indent=2).encode())
    assert json.loads(raw) == body
    assert b'\n    "open_scalp_position_projection": [' in raw
    manifest = (
        directory / "manifests" / f"monitor_snapshot_manifest_{day}_postclose_exit.json"
    )
    manifest.parent.mkdir()
    manifest.write_text(
        json.dumps(
            dict(
                target_date=day,
                profile="postclose_exit",
                snapshot_paths={"trade_review": str(path)},
                snapshot_sha256={"trade_review": hashlib.sha256(raw).hexdigest()},
            )
        )
    )
    before = generation(path)
    if compressed:
        archive._gzip_file(path, dry_run=False)
    projected, receipt = service.load_prior_entry_projection(day, data_root=tmp_path)
    assert projected["sections"]["open_scalp_position_projection"][0]["timeline"] == [
        carried
    ]
    assert generation(path) == before
    manifest.write_text(
        manifest.read_text().replace(hashlib.sha256(raw).hexdigest(), "0" * 64)
    )
    with pytest.raises(ValueError, match="source_hash_invalid"):
        service.load_prior_entry_projection(day, data_root=tmp_path)
