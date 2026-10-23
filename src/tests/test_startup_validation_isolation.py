"""Exercise the real kernel boundary in disposable, non-trading children."""

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE = "src.engine.infrastructure.startup_validation_isolation"


def _child(tmp_path, body, *, extra_args=(), pass_fds=(), session=True, before_install=""):
    run = tmp_path / "private"
    run.mkdir(mode=0o700)
    source = f"""
import ctypes, json, os, pathlib, platform, socket, sqlite3, subprocess, sys
from {MODULE} import install_validation_isolation, assert_no_forbidden_attempts, IsolationViolation
run = pathlib.Path(sys.argv[1])
{before_install}
capabilities = install_validation_isolation(run, run / 'audit.jsonl')
""" + textwrap.dedent(body)
    result = subprocess.run(
        [sys.executable, "-B", "-c", source, str(run), *map(str, extra_args)],
        cwd=ROOT, text=True, capture_output=True, start_new_session=session,
        pass_fds=pass_fds, timeout=15,
        env={**os.environ, "PYTHONPATH": str(ROOT), "OPENBLAS_NUM_THREADS": "1"},
    )
    return run, result


@pytest.mark.skipif(sys.platform != "linux", reason="Linux isolation contract")
def test_actual_kernel_allows_private_atomic_receipt_and_read_only_sources(tmp_path):
    source = tmp_path / "source.json"
    source.write_text('{"policy": "original"}')
    run, result = _child(tmp_path, """
        assert pathlib.Path(sys.argv[2]).read_text() == '{"policy": "original"}'
        temporary = run / 'receipt.tmp'
        with temporary.open('w') as stream:
            json.dump(capabilities, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, run / 'receipt.json')
        print(json.dumps(assert_no_forbidden_attempts()))
    """, extra_args=(source,))
    assert result.returncode == 0, result.stderr
    final = json.loads(result.stdout)
    assert final["passed"] is True
    assert final["capabilities"]["landlock_abi"] >= 3
    assert final["capabilities"]["network_access"] is False
    assert final["capabilities"]["process_creation"] is False
    assert final["capabilities"]["no_new_privileges"] is True
    assert final["capabilities"]["process_group"] == final["capabilities"]["session_id"]
    assert json.loads((run / "receipt.json").read_text())["filesystem_write_root"] == str(run)
    assert (run / "audit.jsonl").read_bytes() == b""
    assert source.read_text() == '{"policy": "original"}'


@pytest.mark.parametrize("operation,event", [
    ("pathlib.Path(sys.argv[2]).write_text('corrupt')", "open"),
    ("os.unlink(sys.argv[2])", "os.remove"),
    ("os.chmod(sys.argv[2], 0o777)", "os.chmod"),
    ("os.utime(sys.argv[2], None)", "os.utime"),
    ("os.replace(sys.argv[2], run / 'stolen.json')", "os.rename"),
    ("socket.socket(socket.AF_INET, socket.SOCK_STREAM)", "socket.__new__"),
    ("socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)", "socket.__new__"),
    ("subprocess.run(['/bin/true'])", "subprocess.Popen"),
    ("sqlite3.connect(run / 'database.sqlite')", "sqlite3.connect"),
    ("__import__('fcntl').flock(os.open(sys.argv[2], os.O_RDONLY), 2 | 4)", "fcntl.flock"),
    ("__import__('fcntl').fcntl(0, 6, 0)", "fcntl.fcntl"),
])
def test_caught_python_forbidden_attempt_still_fails_terminal(tmp_path, operation, event):
    source = tmp_path / "source.json"
    source.write_text("unchanged")
    original_mode = source.stat().st_mode
    run, result = _child(tmp_path, f"""
        try:
            {operation}
        except Exception:
            pass
        assert_no_forbidden_attempts()
    """, extra_args=(source,))
    assert result.returncode != 0
    assert "validation_forbidden_attempts_observed" in result.stderr
    events = [json.loads(line)["event"] for line in (run / "audit.jsonl").read_text().splitlines()]
    assert event in events
    assert source.read_text() == "unchanged"
    assert source.stat().st_mode == original_mode
    assert not (run / "stolen.json").exists()
    assert not (run / "database.sqlite").exists()


def test_landlock_denies_native_write_bypassing_python_audit_hook(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("unchanged")
    _, result = _child(tmp_path, """
        libc = ctypes.CDLL(None, use_errno=True)
        descriptor = libc.open(os.fsencode(sys.argv[2]), os.O_WRONLY | os.O_TRUNC)
        assert descriptor == -1, descriptor
        assert ctypes.get_errno() in (1, 13)
        print('native_write_denied')
    """, extra_args=(source,))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "native_write_denied"
    assert source.read_text() == "unchanged"


def test_caught_landlock_dir_fd_escape_cannot_be_reported_passed(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("unchanged")
    run, result = _child(tmp_path, """
        outside = os.open(str(pathlib.Path(sys.argv[2]).parent), os.O_RDONLY | os.O_DIRECTORY)
        os.chdir(run)
        def attempt_escape():
            try:
                os.open('source.json', os.O_WRONLY | os.O_TRUNC, dir_fd=outside)
            except PermissionError:
                pass
        attempt_escape()
        assert_no_forbidden_attempts()
    """, extra_args=(source,))
    assert result.returncode != 0
    assert "validation_forbidden_attempts_observed" in result.stderr
    events = [json.loads(line)["event"] for line in (run / "audit.jsonl").read_text().splitlines()]
    assert "python.PermissionError" in events
    assert source.read_text() == "unchanged"


@pytest.mark.parametrize("kind", ["socket", "clone", "chmod", "xattr", "xattr_at", "file_setattr", "ioctl",
                                   "flock", "fcntl_lock", "sched_setaffinity", "prlimit"])
def test_seccomp_traps_native_side_effects_and_marks_caught_attempt(tmp_path, kind):
    calls = {
        "socket": "198 if platform.machine() == 'aarch64' else 41",
        "clone": "220 if platform.machine() == 'aarch64' else 56",
        "chmod": "52 if platform.machine() == 'aarch64' else 91",
        "xattr": "5 if platform.machine() == 'aarch64' else 188",
        "xattr_at": "463",
        "file_setattr": "469",
        "ioctl": "29 if platform.machine() == 'aarch64' else 16",
        "flock": "32 if platform.machine() == 'aarch64' else 73",
        "fcntl_lock": "25 if platform.machine() == 'aarch64' else 72",
        "sched_setaffinity": "122 if platform.machine() == 'aarch64' else 203",
        "prlimit": "261 if platform.machine() == 'aarch64' else 302",
    }
    run, result = _child(tmp_path, f"""
        libc = ctypes.CDLL(None, use_errno=True)
        try:
            libc.syscall(ctypes.c_long({calls[kind]}), 0, {6 if kind == 'fcntl_lock' else 0}, 0, 0, 0)
        except Exception:
            pass
        assert_no_forbidden_attempts()
    """)
    assert result.returncode != 0
    assert "validation_forbidden_attempts_observed" in result.stderr
    assert json.loads((run / "audit.jsonl").read_text())["event"] == "seccomp.SIGSYS"


def test_inherited_regular_file_descriptor_is_closed(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("unchanged")
    fd = os.open(source, os.O_WRONLY | os.O_APPEND)
    try:
        _, result = _child(tmp_path, """
            inherited = int(sys.argv[2])
            # Its numeric slot can be reused by our private audit file. In either
            # case it must no longer refer to the inherited source inode.
            try:
                target = os.readlink(f'/proc/self/fd/{inherited}')
                assert target.startswith(str(run)), target
            except FileNotFoundError:
                pass
            assert capabilities['closed_inherited_fds'] >= 1
            assert_no_forbidden_attempts()
        """, extra_args=(fd,), pass_fds=(fd,))
    finally:
        os.close(fd)
    assert result.returncode == 0, result.stderr
    assert source.read_text() == "unchanged"


def test_private_session_is_required_before_any_loader_import(tmp_path):
    _, result = _child(tmp_path, "raise AssertionError('must not reach loader')", session=False)
    assert result.returncode != 0
    assert "validation_requires_private_process_session" in result.stderr
    assert "must not reach loader" not in result.stderr


def test_nonprivate_run_directory_is_refused_before_installation(tmp_path):
    run = tmp_path / "public"
    run.mkdir(mode=0o755)
    result = subprocess.run(
        [sys.executable, "-B", "-c", f"from {MODULE} import install_validation_isolation; "
         "import sys; install_validation_isolation(sys.argv[1],sys.argv[1]+'/audit.jsonl')", str(run)],
        cwd=ROOT, text=True, capture_output=True, start_new_session=True, timeout=15,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert result.returncode != 0
    assert "validation_run_directory_not_private" in result.stderr
    assert not (run / "audit.jsonl").exists()


def test_installer_uses_single_process_and_cannot_be_reused(tmp_path):
    _, result = _child(tmp_path, """
        try:
            install_validation_isolation(run, run / 'second-audit.jsonl')
        except RuntimeError as error:
            assert str(error) == 'validation_isolation_already_installed'
        else:
            raise AssertionError('second sandbox must be refused')
        assert_no_forbidden_attempts()
    """)
    assert result.returncode == 0, result.stderr


def test_privileged_effective_identity_is_refused_before_installation(tmp_path):
    run, result = _child(tmp_path, "raise AssertionError('loader must not run')",
                         before_install="os.geteuid = lambda: 0")
    assert result.returncode != 0
    assert "validation_requires_unprivileged_identity" in result.stderr
    assert not (run / "audit.jsonl").exists()


def test_existing_effective_capability_is_refused_before_installation(tmp_path):
    override = (f"import {MODULE} as isolation; "
                "isolation._process_capabilities = lambda: {'CapEff': 1, 'CapPrm': 1, 'CapAmb': 0}")
    run, result = _child(tmp_path, "raise AssertionError('loader must not run')",
                         before_install=override)
    assert result.returncode != 0
    assert "validation_requires_unprivileged_identity" in result.stderr
    assert not (run / "audit.jsonl").exists()


def test_terminal_read_query_does_not_allow_regular_file_metadata_mutation(tmp_path):
    _, result = _child(tmp_path, """
        import fcntl
        try:
            fcntl.ioctl(1, 0x5401, bytearray(64))
        except OSError as error:
            assert error.errno == 25  # stdout is a pipe, not a terminal.
        assert_no_forbidden_attempts()
    """)
    assert result.returncode == 0, result.stderr


def test_regular_file_setflags_ioctl_is_trapped_with_readonly_descriptor(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("unchanged")
    run, result = _child(tmp_path, """
        import fcntl
        descriptor = os.open(sys.argv[2], os.O_RDONLY)
        try:
            fcntl.ioctl(descriptor, 0x40086602, bytearray(8))
        except Exception:
            pass
        assert_no_forbidden_attempts()
    """, extra_args=(source,))
    assert result.returncode != 0
    assert "validation_forbidden_attempts_observed" in result.stderr
    assert json.loads((run / "audit.jsonl").read_text())["event"] == "seccomp.SIGSYS"
    assert source.read_text() == "unchanged"


def test_readonly_descriptor_flag_query_remains_available(tmp_path):
    _, result = _child(tmp_path, """
        import fcntl
        assert isinstance(fcntl.fcntl(0, fcntl.F_GETFL), int)
        assert_no_forbidden_attempts()
    """)
    assert result.returncode == 0, result.stderr


def test_test_filesystem_boundary_is_inherited_by_exec_children(tmp_path):
    source = tmp_path / 'sealed-summary.json'
    source.write_text('original')
    private = tmp_path / 'scratch'; private.mkdir()
    script = r"""
import ctypes, os, pathlib, subprocess, sys
from src.engine.infrastructure.startup_validation_isolation import _landlock
private, source = map(pathlib.Path, sys.argv[1:])
_landlock(ctypes.CDLL(None,use_errno=True),private,test_roots=(private,pathlib.Path('/dev/null')))
(private/'allowed').write_text('test output')
code = "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('corrupt')"
child = subprocess.run([sys.executable,'-B','-c',code,str(source)],capture_output=True,text=True)
assert child.returncode != 0 and 'PermissionError' in child.stderr, child.stderr
libc=ctypes.CDLL(None,use_errno=True)
assert libc.open(os.fsencode(source),os.O_WRONLY|os.O_TRUNC)==-1
assert source.read_text()=='original'
print('native_and_exec_writes_denied')
"""
    result = subprocess.run([sys.executable,'-B','-c',script,str(private),str(source)],
        cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT)},capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='native_and_exec_writes_denied'
    assert source.read_text()=='original'
