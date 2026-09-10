import json
import subprocess

import pytest

from src.engine.infrastructure import runtime_release_router as router


@pytest.fixture
def release(tmp_path, monkeypatch):
    workspace = tmp_path / "project"
    root = tmp_path / "project-runtime-releases" / "reviewed"
    root.mkdir(parents=True)
    for name in ("data", "logs", "tmp", ".venv", "docs"):
        (workspace / name).mkdir(parents=True)
        (root / name).symlink_to(workspace / name, target_is_directory=True)
    (root / "restart.flag").symlink_to(workspace / "restart.flag")
    (workspace / "data/runtime").mkdir()
    selection = {
        "schema": "runtime_release_selection_v1",
        "workspace": str(workspace),
        "release_root": str(root),
        "git_commit": "a" * 40,
    }
    manifest = workspace / "data/runtime/runtime_release_selection.json"
    manifest.write_text(json.dumps(selection))
    monkeypatch.setattr(
        router, "git", lambda _, *args: "a" * 40 if args[0] == "rev-parse" else ""
    )
    return workspace, root, manifest, selection


def test_release_shares_operator_flag_and_docs(release):
    workspace, root, _, _ = release
    assert router.selected_release(workspace) == (root, "a" * 40)
    assert not (workspace / "restart.flag").exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema", "unknown"),
        ("workspace", "/wrong"),
        ("release_root", "relative"),
        ("git_commit", "abc"),
        ("git_commit", "b" * 40),
    ],
)
def test_bad_selection_rejected(release, key, value):
    workspace, _, manifest, selection = release
    selection[key] = value
    manifest.write_text(json.dumps(selection))
    with pytest.raises(ValueError):
        router.selected_release(workspace)


@pytest.mark.parametrize("payload", ["[]", "null", "{invalid"])
def test_bad_json_rejected(release, payload):
    workspace, _, manifest, _ = release
    manifest.write_text(payload)
    with pytest.raises(ValueError):
        router.selected_release(workspace)


def test_outside_root_rejected(release):
    workspace, _, manifest, selection = release
    selection["release_root"] = str(workspace)
    manifest.write_text(json.dumps(selection))
    with pytest.raises(ValueError, match="outside_managed"):
        router.selected_release(workspace)


def test_dirty_source_rejected(release, monkeypatch):
    workspace, _, _, _ = release
    monkeypatch.setattr(
        router,
        "git",
        lambda _, *args: "a" * 40 if args[0] == "rev-parse" else " M src/file.py",
    )
    with pytest.raises(ValueError, match="source_dirty"):
        router.selected_release(workspace)


@pytest.mark.parametrize(
    "name", ["docs", "data", "logs", "tmp", ".venv", "restart.flag"]
)
def test_split_shared_state_rejected(release, name):
    workspace, root, _, _ = release
    (root / name).unlink()
    (root / name).mkdir()
    with pytest.raises(ValueError, match="shared_path_mismatch"):
        router.selected_release(workspace)


@pytest.mark.parametrize("op", router.OPERATIONS)
def test_all_operations_pin_release_and_target_date(release, op):
    workspace, root, _, _ = release
    plan = router.make_plan(workspace, root, "a" * 40, op, "2026-09-11")
    assert plan["release_root"] == str(root)
    assert plan["target_date"] == "2026-09-11"
    assert str(root) in " ".join(plan["command"])
    assert "existing_exact_date_gates_unchanged" == plan["policy_authority"]
    if op in router.OWNED or op == "paired-replay":
        assert plan["command"][-1] == "2026-09-11"
    if op == "start":
        assert f"PYTHONPATH={root}" in plan["command"][-1]
        assert plan["cwd"] == str(root / "src")


@pytest.mark.parametrize(
    "value", ["2026-9-11", "2026-09-31", "20260911", "2026-09-11; touch /tmp/no"]
)
def test_invalid_date_rejected(release, value):
    workspace, root, _, _ = release
    with pytest.raises(ValueError):
        router.make_plan(workspace, root, "a" * 40, "postclose", value)


def original_cron(workspace):
    lines = [
        "# unchanged",
        "* * * * * /unrelated/widget",
        "30 7 * * 1-5 /usr/bin/tmux kill-session -t bot",
        f"55 7 * * 1-5 /usr/bin/tmux new-session -d -s bot 'cd {workspace}/src && ./run_bot.sh'",
    ]
    for tag, op in router.TAGS.items():
        if op in router.OWNED:
            script, owner = router.OWNED[op]
            cmd = (
                f"bash {workspace}/deploy/run_with_owned_log.sh --owner {owner} "
                f"--log {workspace}/logs/{owner}.log {workspace}/deploy/run_{script}.sh"
            )
        elif op == "paired-replay":
            cmd = f"{workspace}/deploy/run_ai_entry_setup_paired_replay_postclose.sh"
        elif op == "eod":
            cmd = f"cd {workspace} && {workspace}/.venv/bin/python src/utils/update_kospi.py"
        else:
            cmd = f"{workspace}/deploy/run_dashboard_db_archive_cron.sh 0"
        tail = (
            " $(TZ=Asia/Seoul date +\\%F)"
            if op in router.OWNED or op == "paired-replay"
            else ""
        )
        lines.append(
            f"10 20 * * 1-5 KEEP_POLICY_ENV=true {cmd}{tail} >> /preserved.log 2>&1 # {tag}"
        )
    return "\n".join(lines) + "\n"


def test_cron_preserves_unrelated_env_schedule_date_and_logs(tmp_path):
    before = original_cron(tmp_path)
    after = router.render_crontab(before, tmp_path)
    assert after.splitlines()[:3] == before.splitlines()[:3]
    assert after.count("run_runtime_release.sh") == 9
    assert after.count("KEEP_POLICY_ENV=true") == 8
    assert after.count("$(TZ=Asia/Seoul date +\\%F)") == 6
    assert after.count(">> /preserved.log 2>&1") == 8
    assert router.render_crontab(after, tmp_path) == after


@pytest.mark.parametrize("mode", ["missing", "duplicate", "unexpected_command"])
def test_cron_drift_blocks_install(tmp_path, mode):
    before = original_cron(tmp_path)
    if mode == "missing":
        before = "\n".join(before.splitlines()[:-1])
    elif mode == "duplicate":
        before += before.splitlines()[-1] + "\n"
    else:
        before = before.replace("run_threshold_cycle_postclose.sh", "unexpected.sh")
    with pytest.raises(ValueError):
        router.render_crontab(before, tmp_path)


def test_cron_check_never_installs(release, monkeypatch):
    workspace, _, _, _ = release
    monkeypatch.setattr(
        subprocess, "check_output", lambda *a, **k: original_cron(workspace)
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not install")
    )
    with pytest.raises(ValueError, match="not_installed"):
        router.manage_cron(workspace, False)


def test_cron_wrong_operation_prefix_is_not_a_valid_route(tmp_path):
    valid = router.render_crontab(original_cron(tmp_path), tmp_path)
    invalid = valid.replace(
        "run_runtime_release.sh postclose ", "run_runtime_release.sh postclose-invalid "
    )
    with pytest.raises(ValueError, match="command_unrecognized"):
        router.render_crontab(invalid, tmp_path)


def test_cron_concurrent_edit_prevents_write(release, monkeypatch):
    workspace, _, _, _ = release
    values = iter(
        [original_cron(workspace), original_cron(workspace) + "# concurrent\n"]
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: next(values))
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not overwrite")
    )
    with pytest.raises(ValueError, match="changed_during_install"):
        router.manage_cron(workspace, True)


def test_print_plan_never_starts_or_restarts(release, monkeypatch, capsys):
    workspace, root, _, _ = release
    monkeypatch.setattr(
        router,
        "__file__",
        str(workspace / "src/engine/infrastructure/runtime_release_router.py"),
    )
    monkeypatch.setattr(router.sys, "argv", ["router", "restart", "--print-plan"])
    monkeypatch.setattr(
        router.os, "execvpe", lambda *a: pytest.fail("must not execute")
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not start")
    )
    assert router.main() == 0
    assert json.loads(capsys.readouterr().out)["release_root"] == str(root)


def test_missing_manifest_cannot_fall_back_to_workspace(release, monkeypatch, capsys):
    workspace, _, manifest, _ = release
    manifest.unlink()
    monkeypatch.setattr(
        router,
        "__file__",
        str(workspace / "src/engine/infrastructure/runtime_release_router.py"),
    )
    monkeypatch.setattr(router.sys, "argv", ["router", "start"])
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("must not start")
    )
    assert router.main() == 2
    assert "runtime_release_route_blocked" in capsys.readouterr().err


def test_cron_install_backups_and_readback(release, monkeypatch):
    workspace, _, _, _ = release
    before = original_cron(workspace)
    after = router.render_crontab(before, workspace)
    readings = iter([before, before, after])
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: next(readings))
    writes = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: writes.append(k["input"]))
    router.manage_cron(workspace, True)
    assert writes == [after]
    backups = list((workspace / "tmp").glob("runtime-release-cron-*"))
    assert len(backups) == 1
    assert (backups[0] / "before.crontab").read_text() == before
