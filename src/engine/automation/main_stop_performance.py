"""Isolated native stop-domain performance evidence with explicit coverage.

The capture-only v2 receipt cannot certify Main. The v3 dedicated process
executes the native Main/monitor/guard boundary and concurrent postclose work;
its frozen resource, population and parity checks derive a pass or a block.
Neither mode grants live order, provider or deployment authority.
"""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import threading
import tempfile
import time

from src.engine.scalping import main_stop_policy as policy

SCHEMA = "main_stop_performance_v2"
SCOPE = "isolated_native_capture_and_reader"
COVERED = (
    "pin_lookup",
    "native_quote_context",
    "native_capture",
    "native_stage_receipts",
    "normal_decision_receipt",
    "bounded_queue_admission",
    "native_source_serialization",
    "postclose_source_reader",
)
EXCLUDED = (
    "main_ws_wake_and_scheduling",
    "main_holding_and_fast_dispatch",
    "claim_and_exit_registration",
    "main_lock_wait_and_hold",
    "concurrent_main_and_postclose_load",
    "postclose_selector_publish_handoff",
)
MAX_SCENARIOS = 64
MAX_REPEATS = 100
MAX_BYTES = 8 * 1024 * 1024

# These are offline research acceptance limits, not Main policy thresholds,
# quote deadlines or a claim about the monitor's 250 ms polling cadence.
FULL_SCHEMA = "main_stop_performance_v3"
FULL_SCOPE = "isolated_native_main_stop_and_concurrent_postclose"
FULL_BUDGET = dict(
    pairs=3,
    samples_per_arm_run=512,
    warmup_samples=32,
    min_samples_per_arm=1536,
    min_concurrent_samples_per_run=256,
    tail_relative_noise=0.05,
    tail_absolute_noise_ns=1_000_000,
    stop_p99_limit_ns=250_000_000,
    cpu_relative_noise=0.05,
    io_relative_noise=0.05,
    max_rss_bytes=1024**3,
    max_warm_rss_growth_bytes=64 * 1024**2,
    max_temp_bytes=2 * 1024**3,
    max_receipt_bytes=1024**2,
)
FULL_EXCLUDED = (
    "unrelated_scanner_and_entry_workloads",
    "live_network_and_provider_io",
    "actual_broker_orders",
    "production_account_and_ledger",
    "live_pid_adoption",
    "entry_PASS_and_due_deadlines_not_exercised",
    "ordinary_idle_wait_uses_signalled_frozen_input_adapter",
)
FULL_CALLS = (
    "main_cycle",
    "normal_holding",
    "fast_evaluation",
    "monitor_wake",
    "monitor_ws_wake_dispatch",
    "claim",
    "final_guard",
    "native_exit_registration",
    "isolated_submit",
    "accepted_stage:normal:common_soft",
)
_FULL_ISOLATION = None
_LIVE_DATA_ROOT = None
FULL_CLOCK = "frozen_frame_epoch_plus_real_monotonic_elapsed"
LOCK_BASIS = "per_cycle_maximum_native_acquisition_ns"
FULL_CASES = (
    "common_soft_hold",
    "normal_preset_hard",
    "fast_hard",
    "fast_emergency",
    "manual_veto",
    "inventory_unknown",
    "small_quantity_full",
    "fast_hold",
)
FULL_LOSSES = (
    "missing",
    "duplicate",
    "new_expiry",
    "queue_rejected",
    "source_rejected",
    "evaluation_rejected",
    "wake_unavailable",
)
FULL_METRIC_CONTRACT = dict(
    metric_role="source_quality_and_performance_gate",
    decision_authority="stop_family_performance_gate_only",
    window_policy="frozen_offline_workload_three_alternating_pairs",
    sample_floor="1536_reset_position_observations_per_arm",
    primary_decision_metric="paired_stop_domain_p95_p99_and_complete_native_paths",
    source_quality_gate="same_input_native_guard_parity_zero_loss_duplicate_new_expiry",
    forbidden_uses=[
        "economic_edge",
        "actual_fill_or_profit",
        "live_order_authority",
        "unrelated_entry_or_scanner_performance",
        "live_pid_consumption",
    ],
)


def _full_budget(value):
    """Freeze the agreed finite experiment; callers cannot widen its limits."""
    if not isinstance(value, dict) or value != FULL_BUDGET:
        raise ValueError("stop_performance_frozen_budget_invalid")
    # bool == 1 and integer-valued floats must not evade the typed contract.
    if any(
        type(value[key]) is not type(expected) for key, expected in FULL_BUDGET.items()
    ):
        raise ValueError("stop_performance_frozen_budget_invalid")
    return dict(value)


def _measurement_cell(value):
    if not isinstance(value, str) or value not in {
        role + "|" + market for role in policy.ROLES for market in policy.MARKETS
    }:
        raise ValueError("stop_performance_measurement_cell_invalid")
    return value


def _full_scenarios(value, measurement_cell="SCANNER|REGULAR"):
    """The full certificate covers the preregistered finite native workload."""
    measured_role = _measurement_cell(measurement_cell).split("|")[0]
    if not isinstance(value, list) or [
        row.get("case_id") for row in value if isinstance(row, dict)
    ] != list(FULL_CASES):
        raise ValueError("stop_performance_full_scenarios_incomplete")
    for row in value:
        name = row["case_id"]
        stock = row.get("stock") or {}
        role = (
            measured_role
            if name in ("common_soft_hold", "fast_hard")
            else ("SCALPING" if name == "fast_hold" else "SCALP_PRESET_TP")
        )
        fast = name in ("fast_hard", "fast_emergency", "inventory_unknown", "fast_hold")
        hold = name in (
            "common_soft_hold",
            "fast_hold",
            "manual_veto",
            "inventory_unknown",
        )
        if (
            row.get("dispatch_order") != ("fast_first" if fast else "normal_first")
            or row.get("expected_semantic")
            != {"status": "HOLDING" if hold else "SELL_ORDERED"}
            or stock.get("buy_qty") != (5 if name == "small_quantity_full" else 10)
            or row.get("role") != role
            or (
                role == "SCALP_PRESET_TP"
                and stock.get("exit_mode") != "SCALP_PRESET_TP"
            )
            or len(row.get("companions", []))
            != (2 if name in ("normal_preset_hard", "fast_emergency") else 0)
        ):
            raise ValueError("stop_performance_full_scenario_contract_invalid")
        if (
            name == "manual_veto"
            and stock.get("manual_control_auto_hard_stop_blocked") is not True
        ):
            raise ValueError("stop_performance_full_manual_veto_unexercised")
        if name == "inventory_unknown" and row.get("account_inventory") != {
            "rows": [],
            "successful_exchanges": [],
        }:
            raise ValueError("stop_performance_full_unknown_inventory_unexercised")
    return value


def _io_snapshot():
    values = {}
    for line in Path("/proc/self/io").read_text().splitlines():
        key, value = line.split(":", 1)
        values[key] = int(value)
    return values


def _rss_bytes():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) * 1024
    raise ValueError("stop_performance_rss_unobservable")


def _full_pair_findings(arms, budget):
    """Derive verdicts from raw paired observations, never from supplied PASS.

    Logical read/write bytes are the paired I/O denominator; physical bytes
    remain diagnostics because the kernel's cache state differs across arms.
    """
    budget = _full_budget(budget)
    findings = []
    for name in ("baseline", "candidate"):
        runs = arms.get(name, [])
        if len(runs) != budget["pairs"]:
            findings.append("incomplete_pairs:" + name)
            continue
        if (
            sum(len(run.get("samples_ns", [])) for run in runs)
            < budget["min_samples_per_arm"]
        ):
            findings.append("insufficient_tail_samples:" + name)
        for index, run in enumerate(runs):
            if len(run.get("samples_ns", [])) != budget["samples_per_arm_run"]:
                findings.append("incomplete_population:" + name + ":" + str(index))
            if (
                max(
                    run.get("peak_rss_bytes", budget["max_rss_bytes"] + 1),
                    run.get("process_lifetime_peak_rss_bytes", 0),
                )
                > budget["max_rss_bytes"]
            ):
                findings.append("rss_budget:" + name + ":" + str(index))
            if (
                run.get(
                    "warm_rss_growth_bytes", budget["max_warm_rss_growth_bytes"] + 1
                )
                > budget["max_warm_rss_growth_bytes"]
            ):
                findings.append("warm_rss_growth:" + name + ":" + str(index))
            if (
                run.get("peak_temp_bytes", budget["max_temp_bytes"] + 1)
                > budget["max_temp_bytes"]
            ):
                findings.append("temp_budget:" + name + ":" + str(index))
            values = run.get("samples_ns", [])
            if values and _summary(values)["p99_ns"] > budget["stop_p99_limit_ns"]:
                findings.append("absolute_p99_budget:" + name + ":" + str(index))
    if any(
        len(arms.get(name, [])) != budget["pairs"] for name in ("baseline", "candidate")
    ):
        return sorted(set(findings))
    for index, (before, after) in enumerate(zip(arms["baseline"], arms["candidate"])):
        for percentile in ("p95_ns", "p99_ns"):
            a = _summary(before.get("samples_ns", []))[percentile]
            b = _summary(after.get("samples_ns", []))[percentile]
            if a is None or b is None:
                continue
            noise = min(
                budget["tail_absolute_noise_ns"], a * budget["tail_relative_noise"]
            )
            if b > a + noise:
                findings.append("tail_regression:" + percentile + ":" + str(index))
        cpu_before = before.get("cpu_ns", 0)
        cpu_after = after.get("cpu_ns", 0)
        if cpu_before <= 0 or cpu_after <= 0:
            findings.append("cpu_unobserved:" + str(index))
        elif cpu_after > cpu_before * (1 + budget["cpu_relative_noise"]):
            findings.append("cpu_regression:" + str(index))
        for field in ("rchar", "wchar"):
            a = before.get("io_delta", {}).get(field)
            b = after.get("io_delta", {}).get(field)
            if type(a) is not int or type(b) is not int or min(a, b) < 0:
                findings.append("io_unobserved:" + field + ":" + str(index))
            elif b > a * (1 + budget["io_relative_noise"]):
                findings.append("io_regression:" + field + ":" + str(index))
    return sorted(set(findings))


def _file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_frozen_reference(reference, *, max_bytes=MAX_BYTES):
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ValueError("stop_performance_input_reference_invalid")
    from src.engine.scalping.main_stop_experiment import _safe_path

    path = _safe_path(reference["path"]).resolve()
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError("stop_performance_input_reference_unbounded")
    if _file_sha(path) != reference["sha256"]:
        raise ValueError("stop_performance_input_reference_changed")
    return path


def _run_postclose_workload(root, request, *, started=None):
    """Native bounded replay/selection and private all-carry publication.

    The candidate preparation and published carry use the same normal code.
    New numeric authority is deliberately not invented while its performance
    evidence is being measured. The later finalized selected commit consumes
    this measurement through the unchanged authority validator.
    """
    from . import main_stop_postclose as post

    required = {
        "data_root",
        "source_date",
        "target_date",
        "parents",
        "parent_receipt",
        "snapshot_receipt",
        "source_files",
    }
    optional = {"experiments", "completed_receipt", "economic_sources"}
    if (
        not isinstance(request, dict)
        or not required <= set(request)
        or set(request) - required - optional
    ):
        raise ValueError("stop_performance_postclose_request_invalid")
    if (
        not isinstance(request["source_files"], list)
        or not 1 <= len(request["source_files"]) <= 64
    ):
        raise ValueError("stop_performance_postclose_sources_invalid")
    paths = [
        _read_frozen_reference(ref, max_bytes=64 * 1024**2)
        for ref in request["source_files"]
    ]
    parent_path = _read_frozen_reference(request["parent_receipt"])
    snapshot_path = _read_frozen_reference(request["snapshot_receipt"])
    from src.engine.scalping.main_stop_experiment import _safe_path
    from src.utils.constants import DATA_DIR

    native_root = _safe_path(request["data_root"]).resolve()
    live_root = Path(_LIVE_DATA_ROOT or str(DATA_DIR)).resolve()
    if native_root == live_root or live_root in native_root.parents:
        raise ValueError("stop_performance_live_postclose_root_forbidden")
    if any(
        not path.is_relative_to(native_root)
        for path in paths + [parent_path, snapshot_path]
    ):
        raise ValueError("stop_performance_postclose_source_root_mismatch")
    completed = []
    extra_paths = []
    if request.get("completed_receipt"):
        completed_path = _read_frozen_reference(request["completed_receipt"])
        if not completed_path.is_relative_to(native_root):
            raise ValueError("stop_performance_postclose_source_root_mismatch")
        extra_paths.append(completed_path)
        completed, _ = policy.bounded_object(completed_path, MAX_BYTES)
        completed = completed["rows"]
    frozen = {
        str(path): _file_sha(path)
        for path in paths + [parent_path, snapshot_path] + extra_paths
    }
    parents = {
        key: policy.StopValues.parse(value) for key, value in request["parents"].items()
    }
    arguments = dict(
        parents=parents,
        parent_receipt=request["parent_receipt"],
        source_paths=paths,
        snapshot_receipt=request["snapshot_receipt"],
        experiments={},
        completed=completed,
        economic_sources=request.get("economic_sources"),
    )
    root = Path(root)
    data = root / "data"
    preparation = root / "preparation"
    data.mkdir(parents=True, exist_ok=True)
    runs = []
    began = time.perf_counter_ns()
    if started is not None:
        started.set()
    for mode in ("cold", "warm"):
        before = time.perf_counter_ns()
        cpu = time.process_time_ns()
        ready, _ = post.prepare_policy_candidate(
            native_root,
            request["source_date"],
            request["target_date"],
            output_root=preparation,
            **dict(arguments, experiments=request.get("experiments", {})),
        )
        bundle, report = post.publish(
            data, request["source_date"], request["target_date"], **arguments
        )
        env, _ = post.handoff(data, request["target_date"])
        loaded = policy.load_bundle(
            env[policy.ENV_FILE], env[policy.ENV_SHA], request["target_date"]
        )
        if loaded != bundle or any(
            cell["status"] == "selected" or cell["authority"]
            for cell in bundle["cells"].values()
        ):
            raise ValueError("stop_performance_postclose_carry_invalid")
        modeled = sum(
            value
            for cell in ready["cells"].values()
            for key, value in cell["source_census"].items()
            if key.startswith("modeled:")
        )
        population = sum(
            cell["source_census"].get("positions", 0)
            for cell in ready["cells"].values()
        )
        if population <= 0 or modeled <= 0:
            raise ValueError("stop_performance_postclose_native_replay_unobserved")
        selected = sum(cell["status"] == "selected" for cell in ready["cells"].values())
        if request.get("experiments") and selected != 1:
            raise ValueError(
                "stop_performance_postclose_candidate_selection_unobserved"
            )
        semantics = dict(
            cells={
                key: dict(
                    values=cell["values"],
                    status=cell["status"],
                    source_census=cell["source_census"],
                )
                for key, cell in bundle["cells"].items()
            },
            prepared_cells={
                key: dict(
                    values=cell["values"],
                    status=cell["status"],
                    aggregates=cell["selection_evidence"]["aggregates"],
                    cost_selection=cell["selection_evidence"].get("cost_selection"),
                )
                for key, cell in ready["cells"].items()
            },
            census=report["census"],
            positions=population,
            modeled=modeled,
        )
        runs.append(
            dict(
                mode=mode,
                wall_ns=time.perf_counter_ns() - before,
                cpu_ns=time.process_time_ns() - cpu,
                positions=population,
                modeled=modeled,
                selected_preparation_cells=selected,
                selected_preparations={
                    key: dict(
                        values=cell["values"],
                        parent_values=cell["parent_values"],
                        candidate=cell["selection_evidence"]["selected_candidate"],
                    )
                    for key, cell in ready["cells"].items()
                    if cell["status"] == "selected"
                },
                semantic_sha256=policy.digest(semantics),
                policy_sha256=bundle["policy_sha256"],
                calls=dict(prepare=1, publish=1, handoff=1, load_bundle=1),
                publication_scope="private_all_carry_same_native_writer_and_reader",
            )
        )
    if len({run["semantic_sha256"] for run in runs}) != 1:
        raise ValueError("stop_performance_postclose_warm_semantics_changed")
    if any(_file_sha(path) != sha for path, sha in frozen.items()):
        raise ValueError("stop_performance_postclose_source_changed")
    return dict(
        started_ns=began,
        finished_ns=time.perf_counter_ns(),
        runs=runs,
        input_files=frozen,
        selected_policy_published=False,
        scope="native_source_replay_selection_private_carry_publish_handoff_loader",
    )


def _install_full_isolation(scratch, output):
    """Dedicated CLI only: deny external effects and writes outside fixtures."""
    import sys
    from contextvars import ContextVar
    from src.utils import constants
    from src.utils.constants import DATA_DIR

    global _FULL_ISOLATION, _LIVE_DATA_ROOT
    _LIVE_DATA_ROOT = str(Path(DATA_DIR).resolve())
    roots = (Path(scratch).resolve(),)
    output = Path(output).resolve()
    # Pin the original live root before installing private import-time paths.
    # Native modules may ensure DATA_DIR children during their first import;
    # explicit postclose request roots remain the read-only source authority.
    bootstrap = roots[0] / "bootstrap"
    bootstrap.mkdir()
    private_data = bootstrap / "data"
    private_data.mkdir()
    constants.DATA_DIR = private_data
    # Numba's import-time cache is an external filesystem dependency, not a
    # Main decision. Keep its native implementation and route its cache here.
    numba_cache = bootstrap / "numba-cache"
    numba_cache.mkdir()
    os.environ["NUMBA_CACHE_DIR"] = str(numba_cache)
    xdg_cache = bootstrap / "xdg-cache"
    xdg_cache.mkdir()
    os.environ["XDG_CACHE_HOME"] = str(xdg_cache)
    for name in ("LOGS_DIR", "LEGACY_LOGS_DIR", "TMP_DIR"):
        destination = bootstrap / name.lower()
        destination.mkdir()
        setattr(constants, name, destination)
    loaded_logger = sys.modules.get("src.utils.logger")
    if loaded_logger is not None:
        for logger in getattr(loaded_logger, "_MODULE_LOGGERS", {}).values():
            for handler in list(logger.handlers):
                logger.removeHandler(handler)
                handler.close()
        loaded_logger._MODULE_LOGGERS.clear()
        loaded_logger.LOGS_DIR = constants.LOGS_DIR
        loaded_logger.LEGACY_LOGS_DIR = constants.LEGACY_LOGS_DIR
    state = dict(
        scratch=str(roots[0]),
        write_roots=[str(p) for p in roots],
        output=str(output),
        denied=Counter(),
        local_capability_probes=Counter(),
        existing_directory_noop_count=0,
        filesystem_open_adapter="validated_dirfd_path_original_os_open",
    )
    opened_path = ContextVar("stop_performance_open_path", default=None)
    original_open = os.open

    def private_open(path, flags, mode=0o777, *, dir_fd=None):
        value = Path(os.fsdecode(path))
        if not value.is_absolute() and dir_fd is not None:
            value = Path(os.readlink("/proc/self/fd/" + str(dir_fd))) / value
        token = opened_path.set(str(value.resolve()))
        try:
            return original_open(path, flags, mode, dir_fd=dir_fd)
        finally:
            opened_path.reset(token)

    def private(path, dir_fd=None):
        if isinstance(path, int):
            return True
        if not isinstance(path, (str, bytes, os.PathLike)):
            return False
        value = Path(os.fsdecode(path))
        if not value.is_absolute() and isinstance(dir_fd, int) and dir_fd >= 0:
            value = Path(os.readlink("/proc/self/fd/" + str(dir_fd))) / value
        value = value.resolve()
        return (
            any(value == root or root in value.parents for root in roots)
            or value in (output, output.parent)
            or value.parent == output.parent
            and value.name.startswith(".stop-experiment-")
        )

    def deny(event, args):
        forbidden = event in {
            "socket.connect",
            "socket.connect_ex",
            "socket.bind",
            "socket.sendto",
            "socket.getaddrinfo",
            "socket.gethostbyname",
            "socket.gethostbyaddr",
            "socket.getnameinfo",
            "subprocess.Popen",
            "os.system",
            "os.exec",
            "os.posix_spawn",
            "os.fork",
            "os.forkpty",
        }
        if event == "socket.bind":
            import socket

            sock, address = args
            # urllib3 checks IPv6 capability during import. Only an ephemeral
            # loopback bind is local; connects and data transfers stay denied.
            if sock.family == socket.AF_INET6 and tuple(address) in (
                ("::1", 0),
                ("::1", 0, 0, 0),
            ):
                state["local_capability_probes"]["ipv6_loopback_ephemeral_bind"] += 1
                forbidden = False
        if event == "open":
            mode = args[1]
            flags = args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int)
                and bool(
                    flags
                    & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
                )
            )
            forbidden = writing and not private(opened_path.get() or args[0])
        elif event in {"os.remove", "os.rmdir"}:
            forbidden = not private(args[0], args[1] if len(args) > 1 else None)
        elif event in {"os.mkdir", "os.chmod"}:
            forbidden = not private(args[0], args[2] if len(args) > 2 else None)
        elif event == "os.utime":
            forbidden = not private(args[0], args[3] if len(args) > 3 else None)
        elif event == "sqlite3.connect":
            forbidden = not private(args[0])
        elif event in {"os.rename", "os.link", "os.symlink"}:
            forbidden = not private(
                args[0], args[2] if len(args) > 2 else None
            ) or not private(args[1], args[3] if len(args) > 3 else None)
        if forbidden:
            state["denied"][event] += 1
            raise RuntimeError("stop_performance_external_effect_forbidden:" + event)

    sys.dont_write_bytecode = True
    sys.addaudithook(deny)
    os.open = private_open
    original_makedirs = os.makedirs

    def existing_directory_or_create(name, mode=0o777, exist_ok=False):
        # Import-time ensure-directory calls on existing read-only resources
        # have no filesystem effect. Missing external directories still fail
        # through the unchanged mutation guard.
        if exist_ok and Path(name).is_dir():
            if not private(name):
                state["existing_directory_noop_count"] += 1
            return None
        return original_makedirs(name, mode=mode, exist_ok=exist_ok)

    os.makedirs = existing_directory_or_create
    _FULL_ISOLATION = state


def _disk_bytes(root):
    total = 0
    for path in Path(root).rglob("*"):
        if path.is_symlink():
            raise ValueError("stop_performance_scratch_symlink")
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            pass  # A native atomic temporary has just committed.
    return total


def _run_full_arm(
    root, scenarios, values, postclose, budget, *, measurement_cell="SCANNER|REGULAR"
):
    """Call only the repository's native frozen-input execution boundary."""
    from .main_stop_runtime_workload import isolated_main_workload

    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    samples = []
    cycle_totals = []
    setup_samples = []
    semantics = []
    keys = []
    calls = Counter()
    losses = Counter()
    lock_wait = []
    lock_hold = []
    lock_wait_totals = []
    lock_hold_totals = []
    lock_counts = []
    raw_dispositions = []
    frame_durations = []
    source_gaps = Counter()
    concurrent = []
    peak_temp = 0
    call_cells = {}
    measured_quote_clocks = {}
    temp_root = Path(_FULL_ISOLATION["scratch"]) if _FULL_ISOLATION else root
    (root / "capture").mkdir()
    with (
        _isolated_native_capture(root / "capture") as (
            _,
            queue,
            capture_path,
            sink_calls,
        ),
        isolated_main_workload(
            root / "runtime", values, scenarios, measurement_cell=measurement_cell
        ) as fixture,
    ):
        for index in range(budget["warmup_samples"]):
            fixture.run_cycle(index)
        warm_rss = _rss_bytes()
        peak_rss = warm_rss
        io_before = _io_snapshot()
        cpu = time.process_time_ns()
        before = time.perf_counter_ns()
        ready = threading.Event()
        stop = threading.Event()
        sampler_errors = []

        def observe_resources():
            nonlocal peak_rss, peak_temp
            try:
                while not stop.wait(0.1):
                    peak_rss = max(peak_rss, _rss_bytes())
                    peak_temp = max(peak_temp, _disk_bytes(temp_root))
            except Exception as exc:
                sampler_errors.append(str(exc))

        sampler = threading.Thread(
            target=observe_resources, name="stop-research-resource-sample", daemon=True
        )
        sampler.start()
        try:
            with ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="stop-native-postclose"
            ) as executor:
                background = executor.submit(
                    _run_postclose_workload,
                    root / "postclose",
                    postclose,
                    started=ready,
                )
                if not ready.wait(30):
                    if background.done():
                        background.result()
                    raise ValueError("stop_performance_postclose_did_not_start")
                for index in range(budget["samples_per_arm_run"]):
                    overlapping = not background.done()
                    sample_start = time.perf_counter_ns()
                    result = fixture.run_cycle(index + budget["warmup_samples"])
                    total_elapsed = time.perf_counter_ns() - sample_start
                    if not isinstance(result, dict) or not isinstance(
                        result.get("semantic"), (dict, list)
                    ):
                        raise ValueError("stop_performance_native_trace_missing")
                    elapsed = result["native_elapsed_ns"]
                    setup = result["setup_ns"]
                    if (
                        type(elapsed) is not int
                        or not 0 < elapsed <= total_elapsed
                        or type(setup) is not int
                        or not 0 <= setup <= total_elapsed
                    ):
                        raise ValueError("stop_performance_native_timing_invalid")
                    start, end = result.get("frame_start_epoch"), result.get(
                        "frame_end_epoch"
                    )
                    if (
                        result.get("clock_basis") != FULL_CLOCK
                        or type(start) not in (int, float)
                        or type(end) not in (int, float)
                        or not math.isfinite(start)
                        or not math.isfinite(end)
                        or end <= start
                    ):
                        raise ValueError("stop_performance_native_clock_invalid")
                    frame_durations.append(round((end - start) * 1e9))
                    samples.append(elapsed)
                    semantics.append(policy.digest(result["semantic"]))
                    cycle_totals.append(total_elapsed)
                    setup_samples.append(setup)
                    keys.append(result["position_key"])
                    calls.update(result["calls"])
                    measured_quote_clocks[result["position_key"]] = start
                    for cell, counts in result["actual_call_cells"].items():
                        call_cells.setdefault(cell, Counter()).update(counts)
                    losses.update(result["losses"])
                    waits, holds = result["lock_wait_ns"], result["lock_hold_ns"]
                    if any(type(n) is not int or n < 0 for n in waits + holds):
                        raise ValueError("stop_performance_native_lock_invalid")
                    lock_wait.append(max(waits, default=0))
                    lock_hold.append(max(holds, default=0))
                    lock_wait_totals.append(sum(waits))
                    lock_hold_totals.append(sum(holds))
                    lock_counts.append(dict(wait=len(waits), hold=len(holds)))
                    raw_dispositions.append(
                        dict(
                            case_id=result.get("case_id"),
                            disposition=result["raw_disposition"],
                            pending_custody_reason=result.get("pending_custody_reason"),
                        )
                    )
                    for field in ("source_gap", "evaluation_source_gap"):
                        if result.get(field):
                            source_gaps[field + ":" + str(result[field])] += 1
                    if overlapping and not background.done():
                        concurrent.append(elapsed)
                post_result = background.result(timeout=60)
            native_drain = fixture.drain()
            trace = native_drain.pop("transport_trace")
            native_drain["transport_trace_evidence"] = dict(
                count=len(trace),
                sha256=policy.digest(trace),
                examples=trace[:16],
                examples_limit=16,
            )
            complete = queue.close(timeout=30)
            queue_stats = dict(queue._stats)
            from .main_stop_postclose import source_events
            from .main_stop_source_index import extract

            decoded = 0
            capture_census = Counter()
            cell_phases = {}
            measured_keys = set(keys)
            for event in source_events(capture_path, capture_census):
                if event.get("stage") != "main_stop_source":
                    continue
                row = extract(event)
                if not row or row.get("source_sha256") != policy.digest(
                    {k: v for k, v in row.items() if k != "source_sha256"}
                ):
                    raise ValueError("stop_performance_capture_readback_invalid")
                decoded += 1
                if (
                    row.get("schema") == "main_stop_evaluation_source_v1"
                    and row.get("position_key") in measured_keys
                    and row.get("quote_at")
                    == measured_quote_clocks[row["position_key"]]
                ):
                    cell = str(row.get("role")) + "|" + str(row.get("market"))
                    phase = str(row.get("evaluator")) + ":" + str(row.get("stage"))
                    cell_phases.setdefault(cell, Counter())[phase] += 1
            loss_count = sum(
                queue_stats.get(key, 0)
                for key in (
                    "failed",
                    "unavailable",
                    "append_failed",
                    "append_unobservable",
                    "completed_without_append_receipt",
                    "intentionally_not_written",
                )
            )
            drain = dict(
                complete=complete,
                loss_count=loss_count,
                append_confirmed=queue_stats.get("append_confirmed"),
                decoded_rows=decoded,
                queue=queue_stats,
                native=native_drain,
                sink_calls=dict(sink_calls),
                capture_census=dict(capture_census),
            )
        finally:
            stop.set()
            sampler.join(timeout=2)
            if sampler.is_alive():
                raise ValueError("stop_performance_resource_sampler_unfinished")
        finished = time.perf_counter_ns()
        io_after = _io_snapshot()
        if sampler_errors:
            raise ValueError(
                "stop_performance_resource_measurement_failed:" + sampler_errors[0]
            )
        peak_rss = max(peak_rss, _rss_bytes())
        peak_temp = max(peak_temp, _disk_bytes(temp_root))
        if len(keys) != len(set(keys)):
            raise ValueError("stop_performance_position_reset_identity_reused")
        return dict(
            samples_ns=samples,
            latency=_summary(samples),
            cycle_total_ns=cycle_totals,
            fixture_setup_ns=setup_samples,
            semantic_hashes=semantics,
            position_keys=keys,
            calls=dict(calls),
            losses=dict(losses),
            lock_wait_ns=lock_wait,
            lock_hold_ns=lock_hold,
            lock_wait=_summary(lock_wait),
            lock_hold=_summary(lock_hold),
            lock_metric_basis=LOCK_BASIS,
            lock_wait_total_ns=lock_wait_totals,
            lock_hold_total_ns=lock_hold_totals,
            lock_acquisition_counts=lock_counts,
            raw_dispositions=dict(
                count=len(raw_dispositions),
                sha256=policy.digest(raw_dispositions),
                census=dict(
                    Counter(json.dumps(row, sort_keys=True) for row in raw_dispositions)
                ),
                examples=raw_dispositions[:16],
                examples_limit=16,
            ),
            source_gap_census=dict(source_gaps),
            clock_basis=FULL_CLOCK,
            frame_elapsed_ns=frame_durations,
            capture_cell_phases={
                cell: dict(counts) for cell, counts in cell_phases.items()
            },
            capture_cell_phase_scope="measured_primary_positions_exact_input_quote_clock_no_priming",
            actual_call_cells={
                cell: dict(counts) for cell, counts in call_cells.items()
            },
            concurrent_samples=len(concurrent),
            concurrent_samples_ns=concurrent,
            concurrent_latency=_summary(concurrent),
            postclose=post_result,
            drain=drain,
            wall_ns=finished - before,
            cpu_ns=time.process_time_ns() - cpu,
            io_delta={key: io_after[key] - value for key, value in io_before.items()},
            peak_rss_bytes=peak_rss,
            warm_rss_growth_bytes=max(0, peak_rss - warm_rss),
            warm_rss_bytes=warm_rss,
            process_lifetime_peak_rss_bytes=resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss
            * 1024,
            peak_temp_bytes=peak_temp,
        )


def _coverage_cells(arms):
    common = None
    for name in ("baseline", "candidate"):
        for run in arms[name]:
            cells = {
                cell
                for cell, phases in run["capture_cell_phases"].items()
                if cell
                in {
                    role + "|" + market
                    for role in policy.ROLES
                    for market in policy.MARKETS
                }
                and phases.get("normal:common_soft", 0) > 0
                and phases.get("fast:preset_safety", 0) > 0
                and all(
                    run["actual_call_cells"].get(cell, {}).get(key, 0) > 0
                    for key in ("final_guard", "isolated_submit")
                )
            }
            common = cells if common is None else common & cells
    return sorted(common or ())


def _native_losses_verified(losses):
    return (
        isinstance(losses, dict)
        and set(FULL_LOSSES) <= set(losses)
        and all(type(n) is int and n == 0 for n in losses.values())
    )


def _certified_cells(arms):
    cells = set(_coverage_cells(arms))
    for name in ("baseline", "candidate"):
        for run in arms[name]:
            for stage in run["postclose"]["runs"]:
                cells.intersection_update(stage["selected_preparations"])
    return sorted(cells)


def _full_contract_findings(body):
    findings = _full_pair_findings(body["arms"], body["budget"])
    semantic = []
    keys = []
    for name in ("baseline", "candidate"):
        for index, run in enumerate(body["arms"][name]):
            label = name + ":" + str(index)
            if any(run["calls"].get(phase, 0) <= 0 for phase in FULL_CALLS):
                findings.append("native_phase_unobserved:" + label)
            if run["calls"].get("main_cycle") != body["budget"]["samples_per_arm_run"]:
                findings.append("native_main_population_incomplete:" + label)
            if not _native_losses_verified(run["losses"]):
                findings.append("native_population_loss:" + label)
            if not all(
                value["wait"] > 0 and value["hold"] > 0
                for value in run["lock_acquisition_counts"]
            ):
                findings.append("native_lock_unobserved:" + label)
            if (
                run["concurrent_samples"]
                < body["budget"]["min_concurrent_samples_per_run"]
            ):
                findings.append("concurrent_postclose_insufficient_samples:" + label)
            post_runs = run["postclose"]["runs"]
            if (
                len(post_runs) != 2
                or [x["mode"] for x in post_runs] != ["cold", "warm"]
                or any(
                    x["selected_preparation_cells"] != 1
                    or x["positions"] <= 0
                    or x["modeled"] <= 0
                    or x["calls"]
                    != dict(prepare=1, publish=1, handoff=1, load_bundle=1)
                    for x in post_runs
                )
            ):
                findings.append("native_postclose_selection_unobserved:" + label)
            for stage in post_runs:
                selections = stage["selected_preparations"]
                if len(selections) != 1 or any(
                    cell not in body["coverage_cells"]
                    or policy.digest(selected["values"])
                    != policy.digest(body["candidate_values"])
                    or policy.digest(selected["parent_values"])
                    != policy.digest(body["baseline_values"])
                    for cell, selected in selections.items()
                ):
                    findings.append("postclose_selected_pair_not_measured:" + label)
            drain = run.get("drain") or {}
            if (
                drain.get("complete") is not True
                or drain.get("loss_count") != 0
                or drain.get("append_confirmed", 0) <= 0
                or drain.get("append_confirmed") != drain.get("decoded_rows")
            ):
                findings.append("native_capture_drain_unverified:" + label)
            if drain.get("native", {}).get("complete") is not True or drain.get(
                "native", {}
            ).get("errors"):
                findings.append("native_worker_drain_unverified:" + label)
            semantic.append(policy.digest(run["semantic_hashes"]))
            keys.append(policy.digest(run["position_keys"]))
    if len(set(semantic)) != 1:
        findings.append("paired_native_semantics_changed")
    if len(set(keys)) != 1:
        findings.append("paired_reset_inputs_changed")
    if not _certified_cells(body["arms"]):
        findings.append("native_cell_coverage_unobserved")
    if _certified_cells(body["arms"]) != [body["measurement_cell"]]:
        findings.append("requested_measurement_cell_unverified")
    if body["isolation"]["denied"]:
        findings.append("external_effect_attempted")
    return sorted(set(findings))


def measure_full_pair(
    output,
    *,
    scenarios,
    baseline,
    candidate,
    postclose,
    source_sha256,
    budget,
    measurement_cell="SCANNER|REGULAR",
):
    """Measure the actual stop-domain chain in an isolated dedicated process."""
    from src.engine.scalping.main_stop_experiment import _write_immutable

    if _FULL_ISOLATION is None:
        raise ValueError("stop_performance_full_requires_dedicated_cli")
    measurement_cell = _measurement_cell(measurement_cell)
    budget = _full_budget(budget)
    scenarios = _full_scenarios(_frozen(scenarios), measurement_cell)
    postclose = _frozen(postclose)
    if (
        not isinstance(source_sha256, str)
        or len(source_sha256) != 64
        or any(c not in "0123456789abcdef" for c in source_sha256)
    ):
        raise ValueError("stop_performance_source_sha_invalid")
    if policy._LOADED or policy._SOURCE_SINK is not None:
        raise ValueError("stop_performance_requires_idle_offline_process")
    baseline = policy.StopValues.parse(asdict(baseline))
    candidate = policy.StopValues.parse(asdict(candidate))
    code = policy.implementation_sha()
    started = time.time()
    arms = {"baseline": [], "candidate": []}
    order = []
    scratch = Path(_FULL_ISOLATION["scratch"])
    for repeat in range(budget["pairs"]):
        for name in (
            ("baseline", "candidate") if repeat % 2 == 0 else ("candidate", "baseline")
        ):
            order.append(name)
            arms[name].append(
                _run_full_arm(
                    scratch / f"{repeat}-{name}",
                    scenarios,
                    baseline if name == "baseline" else candidate,
                    postclose,
                    budget,
                    measurement_cell=measurement_cell,
                )
            )
    if policy.implementation_sha() != code:
        raise ValueError("stop_performance_code_generation_changed")
    body = dict(
        schema=FULL_SCHEMA,
        status="measured",
        scope=FULL_SCOPE,
        code_sha256=code,
        source_sha256=source_sha256,
        source_sha256_role="expected_inventory_context_not_benchmark_input_provenance",
        input_origin="frozen_offline_native_producer_fixture",
        input_scenarios=scenarios,
        measurement_cell=measurement_cell,
        postclose_request=postclose,
        input_sha256=policy.digest(
            dict(
                scenarios=scenarios,
                postclose=postclose,
                measurement_cell=measurement_cell,
            )
        ),
        budget=budget,
        budget_sha256=policy.digest(budget),
        execution_order=order,
        arms=arms,
        runtime_coverage_cells=_coverage_cells(arms),
        coverage_cells=_certified_cells(arms),
        baseline_values=asdict(baseline),
        candidate_values=asdict(candidate),
        comparison_provenance="same_current_native_code_different_policy_values_not_prior_release",
        sample_independence="reset_native_position_and_ledger_identity_each_cycle_shared_process_and_host",
        warmup_scope="32_untimed_native_reset_cycles_per_arm",
        resource_measurement_scope="whole_process_including_measurement_overhead_100ms_sampler_and_final_stat",
        temp_measurement_scope="whole_job_scratch_across_all_arms",
        lock_metric_basis=LOCK_BASIS,
        clock_basis=FULL_CLOCK,
        metric_contract=FULL_METRIC_CONTRACT,
        coverage_scope=list(FULL_CALLS)
        + [
            "native_postclose_selection",
            "private_all_carry_publish_handoff_loader",
            "bounded_capture_drain_readback",
        ],
        excluded_phases=list(FULL_EXCLUDED),
        isolation=dict(
            mode="dedicated_cli_audit_guard",
            filesystem_open_adapter=_FULL_ISOLATION["filesystem_open_adapter"],
            local_capability_probes=dict(_FULL_ISOLATION["local_capability_probes"]),
            existing_directory_noop_count=_FULL_ISOLATION[
                "existing_directory_noop_count"
            ],
            denied=dict(_FULL_ISOLATION["denied"]),
        ),
        started_at=started,
        completed_at=time.time(),
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        actual_provider_called=False,
    )
    body["unresolved_findings"] = _full_contract_findings(body)
    body["full_runtime_gate_status"] = (
        "blocked" if body["unresolved_findings"] else "pass"
    )
    body["performance_sha256"] = policy.digest(body)
    if (
        len(
            json.dumps(
                body, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        )
        > budget["max_receipt_bytes"]
    ):
        raise ValueError("stop_performance_receipt_budget_exceeded")
    validate_full_receipt(
        body, code_sha=code, source_sha=source_sha256, require_full=False
    )
    reference = _write_immutable(output, body, "performance_sha256")
    return body, {key: reference[key] for key in ("path", "sha256")}


def validate_full_receipt(body, *, code_sha, source_sha, require_full):
    if (
        not isinstance(body, dict)
        or body.get("schema") != FULL_SCHEMA
        or body.get("scope") != FULL_SCOPE
        or body.get("status") != "measured"
        or body.get("code_sha256") != code_sha
        or body.get("source_sha256") != source_sha
        or body.get("source_sha256_role")
        != "expected_inventory_context_not_benchmark_input_provenance"
        or body.get("input_origin") != "frozen_offline_native_producer_fixture"
        or body.get("input_sha256")
        != policy.digest(
            dict(
                scenarios=body.get("input_scenarios"),
                postclose=body.get("postclose_request"),
                measurement_cell=body.get("measurement_cell"),
            )
        )
        or body.get("metric_contract") != FULL_METRIC_CONTRACT
        or body.get("excluded_phases") != list(FULL_EXCLUDED)
        or body.get("coverage_scope")
        != list(FULL_CALLS)
        + [
            "native_postclose_selection",
            "private_all_carry_publish_handoff_loader",
            "bounded_capture_drain_readback",
        ]
        or body.get("comparison_provenance")
        != "same_current_native_code_different_policy_values_not_prior_release"
        or body.get("resource_measurement_scope")
        != "whole_process_including_measurement_overhead_100ms_sampler_and_final_stat"
        or body.get("temp_measurement_scope") != "whole_job_scratch_across_all_arms"
        or body.get("lock_metric_basis") != LOCK_BASIS
        or body.get("clock_basis") != FULL_CLOCK
        or body.get("allowed_runtime_apply") is not False
        or body.get("actual_order_submitted") is not False
        or body.get("actual_provider_called") is not False
        or body.get("performance_sha256")
        != policy.digest({k: v for k, v in body.items() if k != "performance_sha256"})
    ):
        raise ValueError("stop_performance_full_receipt_invalid")
    budget = _full_budget(body.get("budget"))
    _full_scenarios(body.get("input_scenarios"), body.get("measurement_cell"))
    policy.StopValues.parse(body.get("baseline_values"))
    policy.StopValues.parse(body.get("candidate_values"))
    if (
        body.get("budget_sha256") != policy.digest(budget)
        or body.get("execution_order")
        != ["baseline", "candidate", "candidate", "baseline", "baseline", "candidate"]
        or body.get("isolation", {}).get("mode") != "dedicated_cli_audit_guard"
        or body.get("isolation", {}).get("filesystem_open_adapter")
        != "validated_dirfd_path_original_os_open"
    ):
        raise ValueError("stop_performance_full_contract_invalid")
    try:
        for name in ("baseline", "candidate"):
            for run in body["arms"][name]:
                samples = run["samples_ns"]
                if (
                    not isinstance(samples, list)
                    or any(type(n) is not int or n <= 0 for n in samples)
                    or run["latency"] != _summary(samples)
                    or len(run["semantic_hashes"]) != len(samples)
                    or len(run["position_keys"]) != len(samples)
                    or len(set(run["position_keys"])) != len(samples)
                    or run["lock_wait"] != _summary(run["lock_wait_ns"])
                    or run["lock_hold"] != _summary(run["lock_hold_ns"])
                    or run["concurrent_samples"] != len(run["concurrent_samples_ns"])
                    or run["concurrent_latency"]
                    != _summary(run["concurrent_samples_ns"])
                    or Counter(run["concurrent_samples_ns"]) - Counter(samples)
                    or any(
                        type(n) is not int or n < 0
                        for n in run["lock_wait_ns"] + run["lock_hold_ns"]
                    )
                ):
                    raise ValueError("stop_performance_full_samples_invalid")
                if (
                    len(run["cycle_total_ns"]) != len(samples)
                    or len(run["fixture_setup_ns"]) != len(samples)
                    or any(
                        type(total) is not int
                        or type(setup) is not int
                        or not 0 < native <= total
                        or not 0 <= setup <= total
                        for native, total, setup in zip(
                            samples, run["cycle_total_ns"], run["fixture_setup_ns"]
                        )
                    )
                ):
                    raise ValueError("stop_performance_full_timing_invalid")
                if (
                    run["clock_basis"] != FULL_CLOCK
                    or len(run["frame_elapsed_ns"]) != len(samples)
                    or any(
                        type(n) is not int or n <= 0 for n in run["frame_elapsed_ns"]
                    )
                    or run["lock_metric_basis"] != LOCK_BASIS
                    or any(
                        len(run[field]) != len(samples)
                        for field in (
                            "lock_wait_ns",
                            "lock_hold_ns",
                            "lock_wait_total_ns",
                            "lock_hold_total_ns",
                            "lock_acquisition_counts",
                        )
                    )
                ):
                    raise ValueError("stop_performance_full_clock_or_lock_invalid")
                for wait, hold, total_wait, total_hold, counts in zip(
                    run["lock_wait_ns"],
                    run["lock_hold_ns"],
                    run["lock_wait_total_ns"],
                    run["lock_hold_total_ns"],
                    run["lock_acquisition_counts"],
                ):
                    if (
                        type(total_wait) is not int
                        or type(total_hold) is not int
                        or total_wait < wait
                        or total_hold < hold
                        or set(counts) != {"wait", "hold"}
                        or any(type(n) is not int or n < 0 for n in counts.values())
                    ):
                        raise ValueError("stop_performance_full_lock_invalid")
                evidence = run["raw_dispositions"]
                if (
                    evidence["count"] != len(samples)
                    or sum(evidence["census"].values()) != len(samples)
                    or len(evidence["examples"]) != min(16, len(samples))
                    or evidence["examples_limit"] != 16
                    or len(evidence["sha256"]) != 64
                    or any(
                        type(n) is not int or n <= 0
                        for n in evidence["census"].values()
                    )
                ):
                    raise ValueError("stop_performance_full_disposition_invalid")
                for mapping in (run["calls"], run["losses"], run["io_delta"]):
                    if not isinstance(mapping, dict) or any(
                        type(v) is not int or v < 0 for v in mapping.values()
                    ):
                        raise ValueError("stop_performance_full_counters_invalid")
                if (
                    run["capture_cell_phase_scope"]
                    != "measured_primary_positions_exact_input_quote_clock_no_priming"
                ):
                    raise ValueError("stop_performance_full_cell_phase_scope_invalid")
                for cells in (run["capture_cell_phases"], run["actual_call_cells"]):
                    if not isinstance(cells, dict) or any(
                        not isinstance(counts, dict)
                        or any(type(n) is not int or n < 0 for n in counts.values())
                        for counts in cells.values()
                    ):
                        raise ValueError("stop_performance_full_cell_counters_invalid")
                for field in (
                    "cpu_ns",
                    "wall_ns",
                    "peak_rss_bytes",
                    "warm_rss_bytes",
                    "warm_rss_growth_bytes",
                    "process_lifetime_peak_rss_bytes",
                    "peak_temp_bytes",
                ):
                    if type(run.get(field)) is not int or run[field] < 0:
                        raise ValueError("stop_performance_full_resource_invalid")
                if run["warm_rss_growth_bytes"] != max(
                    0, run["peak_rss_bytes"] - run["warm_rss_bytes"]
                ):
                    raise ValueError("stop_performance_full_warm_rss_invalid")
                post = run["postclose"]
                if (
                    post["selected_policy_published"] is not False
                    or post["finished_ns"] < post["started_ns"]
                    or not post["input_files"]
                    or len({x["semantic_sha256"] for x in post["runs"]}) != 1
                ):
                    raise ValueError("stop_performance_full_postclose_invalid")
                for stage in post["runs"]:
                    if any(
                        type(stage[k]) is not int or stage[k] <= 0
                        for k in ("wall_ns", "cpu_ns", "positions", "modeled")
                    ):
                        raise ValueError(
                            "stop_performance_full_postclose_measurement_invalid"
                        )
                if any(
                    not isinstance(value, str)
                    or len(value) != 64
                    or any(c not in "0123456789abcdef" for c in value)
                    for value in run["semantic_hashes"]
                ):
                    raise ValueError("stop_performance_full_semantics_invalid")
        findings = _full_contract_findings(body)
        if body.get("runtime_coverage_cells") != _coverage_cells(
            body["arms"]
        ) or body.get("coverage_cells") != _certified_cells(body["arms"]):
            raise ValueError("stop_performance_full_cell_coverage_changed")
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError("stop_performance_full_population_invalid") from exc
    if body.get("unresolved_findings") != findings or body.get(
        "full_runtime_gate_status"
    ) != ("blocked" if findings else "pass"):
        raise ValueError("stop_performance_full_verdict_changed")
    if require_full and findings:
        raise ValueError(
            "stop_performance_full_runtime_unresolved:" + ",".join(findings)
        )
    return body


def _summary(values):
    ordered = sorted(values)
    if not ordered:
        return dict(n=0, p50_ns=None, p95_ns=None, p99_ns=None, max_ns=None)
    return dict(
        n=len(ordered),
        **{
            f"p{p}_ns": ordered[max(0, math.ceil(len(ordered) * p / 100) - 1)]
            for p in (50, 95, 99)
        },
        max_ns=ordered[-1],
    )


def _frozen(value):
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("stop_performance_input_unbounded")
    return json.loads(raw)


@contextmanager
def _isolated_native_capture(root):
    """Only local adapter routing changes; the native capture/queue stay real.

    Call in an otherwise idle offline process. No handler/Main startup or
    broker/provider method is invoked. Restore every module-global binding.
    """
    from src.engine import sniper_state_handlers as handlers
    from src.utils import pipeline_event_logger as logger

    old = (handlers.DATA_DIR, logger.emit_pipeline_event, policy._SOURCE_SINK)
    path = root / "captured.jsonl"
    calls = Counter()
    append_lock = threading.Lock()

    def append(
        pipeline,
        name,
        code,
        stage,
        *,
        record_id=None,
        fields=None,
        observed_at_epoch=None,
    ):
        # Filesystem adapter only: _append_source still seals the native bytes,
        # and the production bounded queue freezes/admit/drains its envelope.
        event = dict(
            pipeline=pipeline,
            name=name,
            code=code,
            stage=stage,
            record_id=record_id,
            fields=fields,
            observed_at_epoch=observed_at_epoch,
        )
        raw = (
            json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        )
        with append_lock:
            with path.open("a") as handle:
                handle.write(raw)
            calls["native_serialized_events"] += 1
            calls["serialized_bytes"] += len(raw.encode())
        return dict(structured_append_succeeded=True)

    handlers.DATA_DIR = root
    logger.emit_pipeline_event = append
    try:
        with ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="stop-offline-capture"
        ) as executor:
            queue = logger.BoundedObservationQueue(executor)
            policy.configure_source_sink(queue.submit)
            try:
                yield handlers, queue, path, calls
            finally:
                if not queue.close(timeout=10):
                    raise ValueError("stop_performance_queue_drain_incomplete")
    finally:
        handlers.DATA_DIR, logger.emit_pipeline_event = old[:2]
        policy.configure_source_sink(old[2])


def _run_arm(root, scenarios, values):
    from src.engine.scalping.position_peak_ledger import position_cycle_id
    from .main_stop_postclose import source_events
    from .main_stop_source_index import extract

    root.mkdir(parents=True, exist_ok=True)
    timings = []
    receipts = []
    contexts = []
    calls = Counter()
    decisions = []
    quantity = Counter()
    started = time.perf_counter_ns()
    cpu = time.process_time_ns()
    with _isolated_native_capture(root) as (h, queue, path, sink_calls):
        for scenario in scenarios:
            stock = deepcopy(scenario["stock"])
            quote_inputs = deepcopy(scenario["quote_inputs"])
            at = quote_inputs["now_ts"]
            code = stock["code"]
            key = position_cycle_id(stock)
            # A private, already-loaded pin is the hot-path baseline. Native
            # preload/bootstrap/durable first-pin are explicitly excluded.
            pinned = policy.pin(
                position_key=key,
                role=scenario["role"],
                market=quote_inputs["market_type"],
                target=scenario["target_date"],
                baseline=values,
            )
            stock.update(
                main_stop_policy_pin=pinned,
                _main_stop_typed_values=values,
                _main_stop_position_key=key,
            )
            before = time.perf_counter_ns()
            policy.pin_values(pinned, key)
            calls["pin_lookup"] += 1
            context = h._main_stop_quote_context(stock, code, **quote_inputs)
            calls["native_quote_context"] += 1
            stock["_main_stop_current_quote_context"] = context
            contexts.append(
                dict(complete=context["complete"], bid=context["bid"], at=context["at"])
            )
            accepted = h._capture_main_stop_observation(stock, code, context)
            calls["native_capture"] += 1
            if not accepted:
                raise ValueError(
                    "stop_performance_native_capture_rejected:"
                    + str(stock.get("main_stop_source_gap"))
                )
            predecessor = None
            for evaluator, stage in scenario.get(
                "evaluation_sequence", [["normal", "common_soft"]]
            ):
                stock["_main_stop_current_quote_context"] = dict(
                    context, evaluator=evaluator
                )
                if stage == "preset_safety":
                    stage_receipt = h._observe_main_stop_preset_evaluation(
                        stock,
                        code,
                        at=at,
                        evaluator=evaluator,
                        decision_price=context["bid"],
                        decision_price_basis="executable_bid",
                        profit_rate=context["decision_profit_pct"],
                        hard_pct=-5.0,
                        emergency_pct=-6.0,
                        grace_sec=0,
                        held_sec=60.0,
                    )
                    if evaluator == "normal":
                        predecessor = stage_receipt
                elif stage == "common_soft":
                    stage_receipt = h._observe_main_stop_evaluation(
                        stock,
                        code,
                        at=at,
                        evaluator=evaluator,
                        stage=stage,
                        decision_price=context["bid"],
                        decision_price_basis="executable_bid",
                        decision_profit_pct=context["decision_profit_pct"],
                        preset_predecessor=predecessor,
                        decision_inputs=dict(
                            grace_enabled=True,
                            after_add=False,
                            handoff_enabled=False,
                            protect_enabled=True,
                            vote_max_worsen_pct=0.8,
                        ),
                    )
                else:
                    raise ValueError("stop_performance_stage_invalid")
                if stage_receipt is None:
                    raise ValueError(
                        "stop_performance_native_stage_rejected:"
                        + str(stock.get("main_stop_evaluation_source_gap"))
                    )
                calls["native_stage_receipts"] += 1
                calls["stage:" + evaluator + ":" + stage] += 1
                quantity[
                    str((stage_receipt.get("quantity_source") or {}).get("status"))
                ] += 1
                receipts.append(stage_receipt["source_sha256"])
            # The native pure decision result is retained separately from the
            # source/capture cost. Neither result dispatches an order.
            decision = policy.soft_decision(
                values, profit_pct=context["decision_profit_pct"], now=at
            )
            decisions.append(asdict(decision))
            receipt = policy.normal_exit_decision_source(
                stock,
                at=at,
                price=context["bid"],
                executable_bid=context["bid"],
                mark_price=context["bid"],
                exit_rule="scalp_trailing_take_profit",
            )
            receipts.append(receipt["source_sha256"])
            calls["normal_decision_receipt"] += 1
            timings.append(time.perf_counter_ns() - before)
        if not queue.close(timeout=10):
            raise ValueError("stop_performance_queue_drain_incomplete")
        queue_stats = dict(queue._stats)
        calls.update(sink_calls)
    census = Counter()
    decoded = 0
    read_started = time.perf_counter_ns()
    if path.exists():
        for event in source_events(path, census):
            observed = extract(event)
            if not isinstance(observed, dict) or observed.get(
                "source_sha256"
            ) != policy.digest(
                {k: v for k, v in observed.items() if k != "source_sha256"}
            ):
                raise ValueError("stop_performance_capture_readback_invalid")
            decoded += 1
    reader_ns = time.perf_counter_ns() - read_started
    expected = len(scenarios) + calls["native_stage_receipts"]
    if decoded != expected or queue_stats["append_confirmed"] != expected:
        raise ValueError("stop_performance_capture_reader_population_mismatch")
    return dict(
        samples_ns=timings,
        capture=_summary(timings),
        reader_ns=reader_ns,
        wall_ns=time.perf_counter_ns() - started,
        cpu_ns=time.process_time_ns() - cpu,
        calls=dict(calls),
        queue=queue_stats,
        decoded_rows=decoded,
        census=dict(census),
        quantity_census=dict(quantity),
        decision_sha256=policy.digest(decisions),
        receipt_sha256=policy.digest(receipts),
        context_sha256=policy.digest(contexts),
        capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def measure_capture_pair(
    output, *, scenarios, baseline, candidate, source_sha256, repeats=3
):
    """Alternate equal frozen workloads; create measured, bounded evidence.

    Callers provide native quote-context inputs, not a timing/PASS dictionary.
    The immutable receipt explicitly excludes full Main and normal postclose
    publication, so successful capture measurements cannot promote a policy.
    """
    from src.engine.scalping.main_stop_experiment import _write_immutable

    if policy._LOADED or policy._SOURCE_SINK is not None:
        raise ValueError("stop_performance_requires_idle_offline_process")
    if type(repeats) is not int or not 3 <= repeats <= MAX_REPEATS:
        raise ValueError("stop_performance_repeats_invalid")
    scenarios = _frozen(scenarios)
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= MAX_SCENARIOS:
        raise ValueError("stop_performance_scenarios_invalid")
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise ValueError("stop_performance_source_sha_invalid")
    baseline = policy.StopValues.parse(asdict(baseline))
    candidate = policy.StopValues.parse(asdict(candidate))
    output = Path(output).absolute()
    from src.utils.constants import DATA_DIR

    if output.is_relative_to(Path(DATA_DIR).resolve()) or output.is_symlink():
        raise ValueError("stop_performance_live_output_forbidden")
    code = policy.implementation_sha()
    started = time.time()
    arms = {"baseline": [], "candidate": []}
    order = []
    with tempfile.TemporaryDirectory(prefix="stop-capture-pair-") as scratch:
        for repeat in range(repeats):
            for name in (
                ("baseline", "candidate")
                if repeat % 2 == 0
                else ("candidate", "baseline")
            ):
                order.append(name)
                arms[name].append(
                    _run_arm(
                        Path(scratch) / f"{repeat}-{name}",
                        scenarios,
                        baseline if name == "baseline" else candidate,
                    )
                )
    if policy.implementation_sha() != code:
        raise ValueError("stop_performance_code_generation_changed")
    body = dict(
        schema=SCHEMA,
        status="measured",
        scope=SCOPE,
        code_sha256=code,
        source_sha256=source_sha256,
        source_sha256_role="expected_inventory_context_not_benchmark_input_provenance",
        input_sha256=policy.digest(scenarios),
        input_scenarios=scenarios,
        input_origin="frozen_offline_fixture",
        started_at=started,
        completed_at=time.time(),
        repeats=repeats,
        execution_order=order,
        baseline_values=asdict(baseline),
        candidate_values=asdict(candidate),
        arms=arms,
        coverage_scope=list(COVERED),
        excluded_phases=list(EXCLUDED)
        + ["preload_and_durable_first_pin", "production_pipeline_filesystem_adapter"],
        full_runtime_gate_status="blocked",
        unresolved_findings=["unmeasured:" + phase for phase in EXCLUDED],
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        actual_provider_called=False,
    )
    body["performance_sha256"] = policy.digest(body)
    validate_receipt(body, code_sha=code, source_sha=source_sha256, require_full=False)
    ref = _write_immutable(output, body, "performance_sha256")
    return body, {k: ref[k] for k in ("path", "sha256")}


def validate_receipt(body, *, code_sha, source_sha, require_full):
    """Recompute the producer's measured population and coverage conclusions."""
    if isinstance(body, dict) and body.get("schema") == FULL_SCHEMA:
        return validate_full_receipt(
            body, code_sha=code_sha, source_sha=source_sha, require_full=require_full
        )
    if (
        body.get("schema") != SCHEMA
        or body.get("scope") != SCOPE
        or body.get("status") != "measured"
        or body.get("code_sha256") != code_sha
        or body.get("source_sha256") != source_sha
        or body.get("source_sha256_role")
        != "expected_inventory_context_not_benchmark_input_provenance"
        or body.get("input_origin") != "frozen_offline_fixture"
        or body.get("performance_sha256")
        != policy.digest({k: v for k, v in body.items() if k != "performance_sha256"})
        or body.get("allowed_runtime_apply") is not False
        or body.get("actual_order_submitted") is not False
        or body.get("actual_provider_called") is not False
        or body.get("coverage_scope") != list(COVERED)
        or body.get("full_runtime_gate_status") != "blocked"
        or body.get("unresolved_findings")
        != ["unmeasured:" + phase for phase in EXCLUDED]
        or body.get("excluded_phases")
        != list(EXCLUDED)
        + ["preload_and_durable_first_pin", "production_pipeline_filesystem_adapter"]
        or body.get("input_sha256") != policy.digest(body.get("input_scenarios"))
    ):
        raise ValueError("stop_performance_producer_receipt_invalid")
    n = len(body["input_scenarios"])
    repeat = body.get("repeats")
    if (
        type(repeat) is not int
        or not 3 <= repeat <= MAX_REPEATS
        or not 1 <= n <= MAX_SCENARIOS
    ):
        raise ValueError("stop_performance_population_invalid")
    stages = sum(
        len(s.get("evaluation_sequence", [["normal", "common_soft"]]))
        for s in body["input_scenarios"]
    )
    stage_calls = Counter(
        "stage:" + evaluator + ":" + stage
        for scenario in body["input_scenarios"]
        for evaluator, stage in scenario.get(
            "evaluation_sequence", [["normal", "common_soft"]]
        )
    )
    expected = n + stages
    contexts = []
    for name in ("baseline", "candidate"):
        runs = body.get("arms", {}).get(name, [])
        if len(runs) != repeat:
            raise ValueError("stop_performance_population_invalid")
        for run in runs:
            samples = run.get("samples_ns", [])
            if (
                len(samples) != n
                or any(type(v) is not int or v <= 0 for v in samples)
                or run.get("capture") != _summary(samples)
                or run.get("decoded_rows") != expected
                or any(
                    run.get("calls", {}).get(key) != n
                    for key in (
                        "pin_lookup",
                        "native_quote_context",
                        "native_capture",
                        "normal_decision_receipt",
                    )
                )
                or run.get("calls", {}).get("native_serialized_events") != expected
                or run.get("calls", {}).get("native_stage_receipts") != stages
                or run.get("queue", {}).get("append_confirmed") != expected
                or run["queue"].get("queued") != expected
                or run["queue"].get("completed") != expected
                or any(
                    run["queue"].get(key) != 0
                    for key in (
                        "failed",
                        "unavailable",
                        "append_failed",
                        "append_unobservable",
                        "completed_without_append_receipt",
                        "intentionally_not_written",
                    )
                )
                or any(
                    run["calls"].get(key) != count for key, count in stage_calls.items()
                )
                or any(
                    type(value) is not int or value < 0
                    for value in run.get("quantity_census", {}).values()
                )
                or sum(run.get("quantity_census", {}).values()) != stages
            ):
                raise ValueError("stop_performance_population_invalid")
            contexts.append(run.get("context_sha256"))
    if len(set(contexts)) != 1:
        raise ValueError("stop_performance_paired_input_changed")
    if require_full:
        raise ValueError(
            "stop_performance_full_runtime_unmeasured:" + ",".join(EXCLUDED)
        )
    return body


def main():
    """Dedicated offline CLI. Requests contain inputs, never timing or PASS."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request, _ = policy.bounded_object(args.request, MAX_BYTES)
    full = request.get("mode") == "full"
    expected = (
        {
            "mode",
            "scenarios",
            "baseline",
            "candidate",
            "source_sha256",
            "budget",
            "postclose",
        }
        if full
        else {"scenarios", "baseline", "candidate", "source_sha256", "repeats"}
    )
    if set(request) != (
        expected
        | ({"measurement_cell"} if full and "measurement_cell" in request else set())
    ):
        raise ValueError("stop_performance_request_invalid")
    if full:
        from src.engine.scalping.main_stop_experiment import _safe_path
        from src.utils.constants import DATA_DIR

        output = _safe_path(args.output).resolve()
        if (
            output == Path(DATA_DIR).resolve()
            or Path(DATA_DIR).resolve() in output.parents
        ):
            raise ValueError("stop_performance_live_output_forbidden")
        output.parent.mkdir(parents=True, exist_ok=True)
        # The guard's directory is created before the audit hook is installed.
        # All subsequent native writes, SQL stores and final receipts are local.
        with tempfile.TemporaryDirectory(prefix="stop-native-full-") as scratch:
            _install_full_isolation(scratch, output)
            body, reference = measure_full_pair(
                output,
                scenarios=request["scenarios"],
                baseline=policy.StopValues.parse(request["baseline"]),
                candidate=policy.StopValues.parse(request["candidate"]),
                source_sha256=request["source_sha256"],
                postclose=request["postclose"],
                budget=request["budget"],
                measurement_cell=request.get("measurement_cell", "SCANNER|REGULAR"),
            )
        print(
            json.dumps(
                dict(
                    reference=reference,
                    status=body["status"],
                    scope=body["scope"],
                    full_runtime_gate_status=body["full_runtime_gate_status"],
                    unresolved_findings=body["unresolved_findings"],
                )
            )
        )
        return 0

    # A dedicated child process is the reproducible isolation boundary. Audit
    # denial is installed before any native handler is imported or called.
    def deny_external(event, args):
        if event in {
            "socket.connect",
            "socket.connect_ex",
            "socket.bind",
            "socket.sendto",
            "subprocess.Popen",
            "os.system",
            "os.exec",
            "os.posix_spawn",
        }:
            raise RuntimeError("stop_performance_external_effect_forbidden")

    sys.addaudithook(deny_external)
    body, reference = measure_capture_pair(
        args.output,
        scenarios=request["scenarios"],
        baseline=policy.StopValues.parse(request["baseline"]),
        candidate=policy.StopValues.parse(request["candidate"]),
        source_sha256=request["source_sha256"],
        repeats=request["repeats"],
    )
    print(
        json.dumps(
            dict(
                reference=reference,
                status=body["status"],
                scope=body["scope"],
                full_runtime_gate_status=body["full_runtime_gate_status"],
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
