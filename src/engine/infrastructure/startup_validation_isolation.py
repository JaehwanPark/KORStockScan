"""One-way Linux isolation for a fresh policy-load validation interpreter.

This is a boundary for trusted application code, not a general hostile-code
sandbox. Landlock restricts filesystem writes; seccomp denies networking,
process creation, metadata changes and process-control system calls. A Python
audit hook makes caught application-level forbidden attempts fail validation.
Install before importing any trading entrypoint or native numerical library.
"""

from __future__ import annotations

import ctypes
import errno
import json
import os
from pathlib import Path
import platform
import resource
import signal
import stat
import sys


class IsolationUnavailable(RuntimeError):
    """The required one-way operating-system boundary cannot be installed."""


class IsolationViolation(PermissionError):
    """A forbidden side effect was attempted, even if its caller caught it."""


_STATE: dict | None = None


class _Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]


class _PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


class _Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]


class _Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filters", ctypes.POINTER(_Filter))]


def _record(event: str, reason: str) -> None:
    state = _STATE
    if state is None:
        raise IsolationViolation("validation_isolation_not_installed")
    finding = {"event": event, "reason": reason}
    state["violations"].append(finding)
    # No arguments are logged: paths/URLs may carry tokens or other secrets.
    os.write(state["audit_fd"], (json.dumps(finding, sort_keys=True) + "\n").encode("ascii"))
    os.fsync(state["audit_fd"])


def _forbid(event: str, reason: str) -> None:
    _record(event, reason)
    raise IsolationViolation(errno.EPERM, f"validation_side_effect_forbidden:{event}:{reason}")


def _inside_private(path: object, *, dir_fd: object = None) -> bool:
    if isinstance(path, int):
        try:
            path = os.readlink(f"/proc/self/fd/{path}")
        except OSError:
            return False
    if not isinstance(path, (str, bytes, os.PathLike)):
        return False
    if dir_fd not in (None, -1):
        # Resolve relative *at calls against their actual directory descriptor.
        try:
            base = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
        except OSError:
            return False
        path = base / os.fsdecode(path)
    try:
        resolved = Path(os.fsdecode(path)).resolve(strict=False)
        return resolved.is_relative_to(_STATE["run_dir"])
    except (OSError, RuntimeError, ValueError, TypeError):
        return False


def _audit(event: str, args: tuple) -> None:
    if _STATE is None:
        return
    if event.startswith("socket.") or event.startswith("sqlite3.connect"):
        _forbid(event, "network_or_database")
    if event == "sys.settrace" and _STATE.get("permission_trace_installed"):
        _forbid(event, "permission_monitor_replacement")
    if event in {"fcntl.flock", "fcntl.lockf"} or (
            event == "fcntl.fcntl" and args[1] in {6, 7, 37, 38, 1024}):
        _forbid(event, "operational_file_lock")
    if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty",
                 "os.exec", "os.posix_spawn", "pty.spawn"}:
        _forbid(event, "process_creation")
    if event in {"os.kill", "os.killpg", "os.chmod", "os.chown", "os.utime",
                 "os.setxattr", "os.removexattr", "os.symlink", "os.link"}:
        _forbid(event, "metadata_or_process_control")
    if event == "open":
        path, mode, flags = args
        writes = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writes and not _inside_private(path):
            _forbid(event, "write_outside_private_run")
    elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.truncate"}:
        dir_fd = args[-1] if event in {"os.remove", "os.rmdir", "os.mkdir"} else None
        if not _inside_private(args[0], dir_fd=dir_fd):
            _forbid(event, "mutation_outside_private_run")
    elif event == "os.rename":
        source, destination, source_fd, destination_fd = args
        if not (_inside_private(source, dir_fd=source_fd)
                and _inside_private(destination, dir_fd=destination_fd)):
            _forbid(event, "rename_outside_private_run")


def _permission_trace(frame, event, argument):
    # The open audit event omits dir_fd. Landlock still denies such escapes,
    # and this records their PermissionError even when application code catches
    # it and substitutes a fallback. Never suppress an operating-system denial.
    if event == "exception":
        _, error, _ = argument
        if isinstance(error, PermissionError) and not isinstance(error, IsolationViolation):
            _record("python.PermissionError", "permission_denial_observed")
    return _permission_trace


def _syscall(libc: ctypes.CDLL, number: int, *args) -> int:
    result = libc.syscall(ctypes.c_long(number), *args)
    if result < 0:
        error = ctypes.get_errno()
        raise IsolationUnavailable(f"isolation_syscall_failed:{number}:{error}")
    return int(result)


def _landlock(libc: ctypes.CDLL, root: Path, *, test_roots: tuple[Path, ...] = ()) -> int:
    abi = _syscall(libc, 444, ctypes.c_void_p(), ctypes.c_size_t(0), ctypes.c_uint(1))
    if abi < 3:
        raise IsolationUnavailable("landlock_abi_requires_truncate_protection")
    # Handle every write right supported through ABI 5. Reads are unrestricted.
    handled = sum(1 << bit for bit in (1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))
    if abi >= 5:
        handled |= 1 << 15  # IOCTL_DEV: no device-control permission granted.
    allowed = sum(1 << bit for bit in (1, 4, 5, 7, 8, 13, 14))
    attributes = _Ruleset(handled)
    ruleset_fd = _syscall(libc, 444, ctypes.byref(attributes), ctypes.sizeof(attributes), 0)
    try:
        # Validation retains its exact single-directory rights. Unit tests use
        # private scratch/cache roots, inherited by every subprocess as well.
        for path in test_roots or (root,):
            is_directory = path.is_dir()
            rights = (handled & ~(1 << 15)) if test_roots and is_directory else allowed
            if not is_directory:
                rights = (1 << 1) | (1 << 14)
            descriptor = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                rule = _PathRule(rights, descriptor)
                _syscall(libc, 445, ruleset_fd, 1, ctypes.byref(rule), 0)
            finally:
                os.close(descriptor)
        if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
            raise IsolationUnavailable(f"no_new_privs_failed:{ctypes.get_errno()}")
        _syscall(libc, 446, ruleset_fd, 0)
    finally:
        os.close(ruleset_fd)
    return abi


def _seccomp(libc: ctypes.CDLL) -> str:
    machine = platform.machine().lower()
    # Include newer *at metadata/mount calls: distro headers may predate the
    # running kernel. Numbers are shared by supported 64-bit architectures.
    common = {424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 435, 442,
              440, 452, 460, 463, 466, 467, 469, 472}
    if machine in {"aarch64", "arm64"}:
        architecture, seccomp_number, ioctl_number, fcntl_number = 0xC00000B7, 277, 29, 25
        denied = common | set(range(198, 213)) | {
            5, 6, 7, 14, 15, 16, 32, 33, 39, 40, 41, 52, 53, 54, 55, 88, 97,
            117, 118, 119, 122, 129, 130, 131, 140,
            220, 221, 241, 242, 243, 261, 265, 268, 269, 271, 280, 281,
        }
    elif machine in {"x86_64", "amd64"}:
        architecture, seccomp_number, ioctl_number, fcntl_number = 0xC000003E, 317, 16, 72
        denied = common | set(range(41, 60)) | {
            62, 73, 90, 91, 92, 93, 94, 101, 132, 133, 141, 142, 144, 155, 165, 166, 200, 203,
            188, 189, 190, 197, 198, 199, 234, 235, 259, 260, 261, 268, 272, 280, 288, 298, 299,
            302, 304, 307, 308, 311, 321, 322,
        }
    else:
        raise IsolationUnavailable(f"unsupported_seccomp_architecture:{machine}")
    # Refuse another ABI; trap all forbidden calls without executing them.
    instructions = [_Filter(0x20, 0, 0, 4), _Filter(0x15, 1, 0, architecture),
                    _Filter(0x06, 0, 0, 0x80000000), _Filter(0x20, 0, 0, 0)]
    if architecture == 0xC000003E:
        instructions += [_Filter(0x35, 0, 1, 0x40000000),
                         _Filter(0x06, 0, 0, 0x00030000)]
    # Text IO checks terminal status even for a regular file. Permit only known
    # read queries (TCGETS, TIOCGWINSZ, FIONREAD); mutating regular-file ioctls
    # such as FS_IOC_SETFLAGS remain trapped, including on read-only FDs.
    ioctl_checks = [_Filter(0x20, 0, 0, 24)]  # seccomp_data.args[1], low 32 bits
    for request in (0x5401, 0x5413, 0x541B):
        ioctl_checks += [_Filter(0x15, 0, 1, request), _Filter(0x06, 0, 0, 0x7FFF0000)]
    ioctl_checks.append(_Filter(0x06, 0, 0, 0x00030000))
    instructions += [_Filter(0x15, 0, len(ioctl_checks), ioctl_number), *ioctl_checks]
    # A read-only FD can still hold an operational publisher's advisory lock.
    # Preserve descriptor queries/flags, but forbid POSIX and OFD lock commands.
    lock_checks = [_Filter(0x20, 0, 0, 24)]
    for command in (6, 7, 37, 38, 1024):  # POSIX/OFD locks and F_SETLEASE
        lock_checks += [_Filter(0x15, 0, 1, command), _Filter(0x06, 0, 0, 0x00030000)]
    lock_checks.append(_Filter(0x06, 0, 0, 0x7FFF0000))
    instructions += [_Filter(0x15, 0, len(lock_checks), fcntl_number), *lock_checks]
    for number in sorted(denied):
        instructions += [_Filter(0x15, 0, 1, number), _Filter(0x06, 0, 0, 0x00030000)]
    instructions.append(_Filter(0x06, 0, 0, 0x7FFF0000))
    filters = (_Filter * len(instructions))(*instructions)
    program = _Program(len(instructions), filters)

    def denied_syscall(signum, frame):
        _forbid("seccomp.SIGSYS", "forbidden_system_call")

    signal.signal(signal.SIGSYS, denied_syscall)
    # TSYNC ensures all threads share the boundary, even though preflight also
    # requires a fresh single-threaded interpreter.
    result = _syscall(libc, seccomp_number, 1, 1, ctypes.byref(program))
    if result != 0:
        # TSYNC returns an offending thread ID (a positive value) on failure.
        raise IsolationUnavailable("seccomp_thread_synchronization_failed")
    return machine


def _close_and_validate_fds(root: Path, close_inherited_fds: bool) -> int:
    descriptors = [int(item.name) for item in Path("/proc/self/fd").iterdir()]
    extra = []
    for fd in descriptors:
        if fd <= 2:
            continue
        try:
            os.fstat(fd)
        except OSError:
            continue  # Directory enumeration descriptor already closed.
        extra.append(fd)
    if extra and not close_inherited_fds:
        raise IsolationUnavailable("inherited_descriptors_present")
    for fd in extra:
        os.close(fd)
    null_fd = os.open(os.devnull, os.O_RDONLY | os.O_CLOEXEC)
    try:
        os.dup2(null_fd, 0)
    finally:
        if null_fd != 0:
            os.close(null_fd)
    for fd in (1, 2):
        info = os.fstat(fd)
        if stat.S_ISFIFO(info.st_mode):
            continue
        target = Path(os.readlink(f"/proc/self/fd/{fd}")).resolve()
        if (stat.S_ISREG(info.st_mode) and target.is_relative_to(root)) or target == Path(os.devnull):
            continue
        raise IsolationUnavailable(f"unsafe_standard_descriptor:{fd}")
    return len(extra)


def _process_capabilities() -> dict[str, int]:
    values = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        key, separator, value = line.partition(":")
        if separator and key in {"CapEff", "CapPrm", "CapAmb"}:
            values[key] = int(value.strip(), 16)
    if set(values) != {"CapEff", "CapPrm", "CapAmb"}:
        raise IsolationUnavailable("validation_capability_state_unavailable")
    return values


def install_validation_isolation(
    run_dir: str | Path, audit_path: str | Path, *, close_inherited_fds: bool = True,
) -> dict:
    """Install irreversible isolation; call only inside a dedicated child.

    The caller creates a new, mode-0700 run directory and starts the child with
    ``start_new_session=True, close_fds=True``. No exec, subprocess or thread may
    be started after this function. Receipts must remain inside ``run_dir``.
    A failure must terminate that child; continuing without isolation is unsafe.
    """
    global _STATE
    if _STATE is not None:
        raise IsolationUnavailable("validation_isolation_already_installed")
    if sys.platform != "linux":
        raise IsolationUnavailable("validation_isolation_requires_linux")
    if (os.getuid() == 0 or os.getuid() != os.geteuid() or os.getgid() != os.getegid()
            or any(_process_capabilities().values())):
        # no_new_privs prevents acquiring privilege; it does not remove any
        # privilege already held when this fresh child starts.
        raise IsolationUnavailable("validation_requires_unprivileged_identity")
    root_input = Path(run_dir).absolute()
    root = root_input.resolve(strict=True)
    info = root_input.lstat()
    if (root_input != root or not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700 or root == Path("/")):
        raise IsolationUnavailable("validation_run_directory_not_private")
    audit = Path(audit_path).absolute()
    if audit.resolve(strict=False) != audit or not audit.is_relative_to(root):
        raise IsolationUnavailable("validation_audit_path_outside_private_run")
    if len(list(Path("/proc/self/task").iterdir())) != 1:
        raise IsolationUnavailable("validation_requires_fresh_single_threaded_child")
    if os.getsid(0) != os.getpid() or os.getpgrp() != os.getpid():
        raise IsolationUnavailable("validation_requires_private_process_session")
    closed_fds = _close_and_validate_fds(root, close_inherited_fds)
    audit_fd = os.open(audit, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    _STATE = {"run_dir": root, "audit_fd": audit_fd, "violations": []}
    sys.dont_write_bytecode = True
    sys.addaudithook(_audit)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    abi = _landlock(libc, root)
    architecture = _seccomp(libc)
    sys.settrace(_permission_trace)
    _STATE["permission_trace_installed"] = True
    result = {
        "schema": "main_startup_validation_isolation_v1",
        "landlock_abi": abi,
        "filesystem_write_root": str(root),
        "network_access": False,
        "process_creation": False,
        "metadata_changes": False,
        "operational_file_locks": False,
        "blocked_process_controls": ["signals", "ptrace", "process_vm_writev", "affinity",
                                     "scheduler", "priority", "resource_limits", "process_madvise"],
        "readonly_ioctl_requests": [0x5401, 0x5413, 0x541B],
        "no_new_privileges": True,
        "caught_permission_denials_fail": True,
        "seccomp_architecture": architecture,
        "closed_inherited_fds": closed_fds,
        "process_group": os.getpgrp(),
        "session_id": os.getsid(0),
        "audit_path": str(audit),
    }
    _STATE["capabilities"] = result
    return result


def assert_no_forbidden_attempts() -> dict:
    """Fail terminal validation after a caller swallowed a denied operation."""
    if _STATE is None or "capabilities" not in _STATE:
        raise IsolationUnavailable("validation_isolation_not_complete")
    if _STATE["violations"]:
        raise IsolationViolation("validation_forbidden_attempts_observed")
    return {"passed": True, "forbidden_attempt_count": 0,
            "capabilities": dict(_STATE["capabilities"])}
