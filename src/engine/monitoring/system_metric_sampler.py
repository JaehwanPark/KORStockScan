"""System resource sampler implementation for monitoring package."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
import fcntl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_PATH = PROJECT_ROOT / "logs" / "system_metric_samples.jsonl"
STATE_PATH = PROJECT_ROOT / "tmp" / "system_metric_sampler_state.json"
LOCK_PATH = PROJECT_ROOT / "tmp" / "system_metric_samples.lock"


def _read_proc_stat() -> dict[str, int]:
    line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0]
    parts = line.split()
    keys = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]
    values = [int(v) for v in parts[1 : 1 + len(keys)]]
    return dict(zip(keys, values))


def _read_meminfo() -> dict[str, int]:
    out: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value = raw.strip().split()[0]
        if value.isdigit():
            out[key] = int(value)
    return out


def _read_diskstats() -> dict:
    read_sectors = 0
    write_sectors = 0
    devices = {}
    for line in Path("/proc/diskstats").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        name = parts[2]
        block = Path("/sys/class/block") / name
        if (
            name.startswith(("loop", "ram", "zram", "dm-", "md"))
            or (block / "partition").exists()
        ):
            continue
        if not block.exists():
            continue
        read_sectors += int(parts[5])
        write_sectors += int(parts[9])
        devices[name] = dict(
            read_sectors=int(parts[5]),
            write_sectors=int(parts[9]),
            read_ios=int(parts[3]),
            write_ios=int(parts[7]),
            read_ms=int(parts[6]),
            write_ms=int(parts[10]),
            inflight=int(parts[11]),
            io_ms=int(parts[12]),
            weighted_ms=int(parts[13]),
        )
    return {
        "schema": "physical_block_v2",
        "read_sectors": read_sectors,
        "write_sectors": write_sectors,
        "devices": devices,
    }


def _top_processes() -> list[dict[str, str]]:
    cmd = [
        "ps",
        "-eo",
        "pid,pcpu,pmem,comm,args",
        "--sort=-pcpu",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = result.stdout.splitlines()[1:6]
    items: list[dict[str, str]] = []
    for line in lines:
        parts = line.strip().split(None, 4)
        if len(parts) < 5:
            continue
        items.append(
            {
                "pid": parts[0],
                "pcpu": parts[1],
                "pmem": parts[2],
                "comm": parts[3],
                "args": parts[4],
            }
        )
    return items


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_PATH.with_name(f"{STATE_PATH.name}.tmp.{os.getpid()}")
    payload = json.dumps(state, ensure_ascii=True).encode("utf-8")
    try:
        with tmp_path.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, STATE_PATH)
    finally:
        tmp_path.unlink(missing_ok=True)


def _append_json_line_durable(path: Path, payload: dict) -> None:
    """Append one indivisible JSON record, reverting a short/failed write."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=True) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o664)
    original_size = os.fstat(fd).st_size
    try:
        written = os.write(fd, encoded)
        if written != len(encoded):
            os.ftruncate(fd, original_size)
            raise OSError(f"short_system_metric_write:{written}/{len(encoded)}")
        os.fsync(fd)
    except Exception:
        try:
            os.ftruncate(fd, original_size)
            os.fsync(fd)
        except OSError:
            pass
        raise
    finally:
        os.close(fd)


def _cpu_pct(curr: dict[str, int], prev: dict[str, int]) -> dict[str, float]:
    if not prev:
        return {
            "cpu_busy_pct": 0.0,
            "cpu_non_idle_pct": 0.0,
            "cpu_compute_busy_pct": 0.0,
            "iowait_pct": 0.0,
        }
    curr_total = sum(curr.values())
    prev_total = sum(int(prev.get(k, 0)) for k in curr.keys())
    total_delta = curr_total - prev_total
    if total_delta <= 0:
        return {
            "cpu_busy_pct": 0.0,
            "cpu_non_idle_pct": 0.0,
            "cpu_compute_busy_pct": 0.0,
            "iowait_pct": 0.0,
        }
    idle_delta = curr["idle"] - int(prev.get("idle", 0))
    iowait_delta = curr["iowait"] - int(prev.get("iowait", 0))
    busy_pct = max(0.0, min(100.0, (1.0 - (idle_delta / total_delta)) * 100.0))
    iowait_pct = max(0.0, min(100.0, (iowait_delta / total_delta) * 100.0))
    compute_busy_pct = max(0.0, min(100.0, busy_pct - iowait_pct))
    return {
        # Backward-compatible alias. Historically this was all non-idle time,
        # including I/O wait, so retain the value for existing consumers.
        "cpu_busy_pct": round(busy_pct, 2),
        "cpu_non_idle_pct": round(busy_pct, 2),
        "cpu_compute_busy_pct": round(compute_busy_pct, 2),
        "iowait_pct": round(iowait_pct, 2),
    }


def _disk_delta(curr: dict[str, int], prev: dict[str, int]) -> dict[str, float]:
    if (
        not prev
        or curr.get("schema") != prev.get("schema")
        or curr.get("devices", {}).keys() != prev.get("devices", {}).keys()
        or curr["read_sectors"] < prev.get("read_sectors", 0)
        or curr["write_sectors"] < prev.get("write_sectors", 0)
    ):
        return {
            "disk_read_mb_delta": None,
            "disk_write_mb_delta": None,
            "measurement_status": "baseline_or_device_generation_changed",
        }
    read_delta = max(0, curr["read_sectors"] - int(prev.get("read_sectors", 0)))
    write_delta = max(0, curr["write_sectors"] - int(prev.get("write_sectors", 0)))
    return {
        "measurement_status": "observed",
        "disk_read_mb_delta": round((read_delta * 512) / (1024 * 1024), 3),
        "disk_write_mb_delta": round((write_delta * 512) / (1024 * 1024), 3),
    }


def _io_pressure():
    result = {}
    try:
        for line in Path("/proc/pressure/io").read_text().splitlines():
            name, *pairs = line.split()
            result[name] = {k: float(v) for k, v in (pair.split("=") for pair in pairs)}
    except (OSError, ValueError):
        return {"status": "unobserved"}
    return {"status": "observed", **result}


def _device_intervals(current, previous, seconds):
    result = {}
    counters = ("read_ios", "write_ios", "read_ms", "write_ms", "io_ms", "weighted_ms")
    for name, row in current.get("devices", {}).items():
        old = previous.get("devices", {}).get(name)
        if (
            not old
            or seconds <= 0
            or current.get("schema") != previous.get("schema")
            or any(row[k] < old.get(k, row[k] + 1) for k in counters)
        ):
            result[name] = {"status": "baseline_or_counter_reset"}
            continue
        d = {k: row[k] - old[k] for k in counters}
        ios = d["read_ios"] + d["write_ios"]
        result[name] = dict(
            status="observed",
            interval_sec=seconds,
            inflight=row["inflight"],
            await_ms=round((d["read_ms"] + d["write_ms"]) / ios, 3) if ios else None,
            average_queue_depth=round(d["weighted_ms"] / (seconds * 1000), 4),
            busy_pct=round(d["io_ms"] / (seconds * 10), 3),
        )
    return result


def _swap_counters():
    try:
        fields = dict(
            line.split() for line in Path("/proc/vmstat").read_text().splitlines()
        )
        return {name: int(fields[name]) for name in ("pswpin", "pswpout")}
    except (OSError, ValueError, KeyError):
        return {}


def _process_io_snapshot(top):
    """Bounded known owners, with birth identity; no FD or source-file scans."""
    candidates = {}
    main_identity = None
    try:
        selection = json.loads(
            (PROJECT_ROOT / "data/runtime/runtime_release_selection.json").read_text()
        )
        if selection.get("actual_pid_consumed") is True:
            candidates[int(selection["actual_pid_receipt"]["pid"])] = "main"
            main_identity = selection["actual_pid_receipt"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    # Enumerate names/parents once, then read counters only for known jobs.
    # The CPU top-five cannot identify an I/O-blocked reporter or developer job.
    inventory = []
    try:
        output = subprocess.run(
            ["ps", "-eo", "pid,ppid,comm,args"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        ).stdout
        for line in output.splitlines()[1:1025]:
            parts = line.split(None, 3)
            if len(parts) == 4:
                inventory.append(
                    dict(pid=parts[0], ppid=parts[1], comm=parts[2], args=parts[3])
                )
    except (OSError, subprocess.SubprocessError):
        inventory = top
    for item in inventory:
        args = item.get("args", "")
        owner = (
            "sentinel"
            if "src.engine.buy_funnel_sentinel" in args
            else (
                "pytest"
                if "pytest" in args
                else (
                    "codex"
                    if "codex" in item.get("comm", "").lower()
                    else (
                        "research"
                        if any(
                            name in args
                            for name in (
                                "-m src.engine.paired",
                                "-m src.engine.automation.pre_submit_delay_partitioned_research",
                            )
                        )
                        else None
                    )
                )
            )
        )
        if owner and len(candidates) < 64:
            candidates[int(item["pid"])] = owner
    # Preserve the actual parent chain, without claiming all writers were seen.
    for _ in range(4):
        for item in inventory:
            if (
                int(item.get("ppid", 0)) in candidates
                and int(item["pid"]) not in candidates
                and len(candidates) < 64
            ):
                candidates[int(item["pid"])] = candidates[int(item["ppid"])] + "_child"
    rows = []
    for pid, owner in candidates.items():
        proc = Path("/proc") / str(pid)
        row = {"pid": pid, "owner": owner, "status": "unobserved"}
        try:
            fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            if (
                owner == "main"
                and main_identity is not None
                and (
                    str((proc / "cwd").resolve()) != main_identity.get("process_cwd")
                    or (
                        main_identity.get("start_ticks") is not None
                        and str(main_identity["start_ticks"]) != fields[19]
                    )
                )
            ):
                raise ValueError("selected_main_identity_changed")
            row.update(
                ppid=int(fields[1]),
                start_ticks=int(fields[19]),
                major_faults=int(fields[9]),
                rss_pages=int(fields[21]),
            )
            io = dict(
                line.split(":", 1) for line in (proc / "io").read_text().splitlines()
            )
            end = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            if end[19] != fields[19]:
                raise ValueError("process_replaced")
            row.update(
                status="observed",
                io={
                    k: int(io[k])
                    for k in ("rchar", "wchar", "read_bytes", "write_bytes")
                },
            )
        except (OSError, ValueError, KeyError, IndexError):
            pass
        rows.append(row)
    return rows


def _process_io_deltas(current, previous):
    old = {(x["pid"], x.get("start_ticks")): x for x in previous}
    for row in current:
        before = old.get((row["pid"], row.get("start_ticks")))
        if (
            row["status"] == "observed"
            and before
            and before.get("status") == "observed"
            and all(row["io"][k] >= before["io"][k] for k in row["io"])
        ):
            row["io_delta"] = {k: row["io"][k] - before["io"][k] for k in row["io"]}
        else:
            row["io_delta"] = None
    return current


def _sample_locked() -> dict:
    now_ts = time.time()
    now_iso = datetime.fromtimestamp(now_ts).astimezone().isoformat(timespec="seconds")
    prev_state = _load_state()
    cpu = _read_proc_stat()
    disk = _read_diskstats()
    mem = _read_meminfo()
    top = _top_processes()
    process_io = _process_io_deltas(
        _process_io_snapshot(top), prev_state.get("process_io", [])
    )
    swap = _swap_counters()
    load1, load5, load15 = os.getloadavg()
    sample = {
        "ts": now_iso,
        "epoch": int(now_ts),
        "loadavg": {
            "1m": round(load1, 3),
            "5m": round(load5, 3),
            "15m": round(load15, 3),
        },
        "cpu": _cpu_pct(cpu, prev_state.get("cpu", {})),
        "memory": {
            "mem_total_mb": round(mem.get("MemTotal", 0) / 1024, 1),
            "mem_available_mb": round(mem.get("MemAvailable", 0) / 1024, 1),
            "mem_free_mb": round(mem.get("MemFree", 0) / 1024, 1),
            "swap_total_mb": round(mem.get("SwapTotal", 0) / 1024, 1),
            "swap_free_mb": round(mem.get("SwapFree", 0) / 1024, 1),
        },
        "io": _disk_delta(disk, prev_state.get("disk", {})),
        "io_pressure": _io_pressure(),
        "swap_pages_delta": (
            {k: swap[k] - prev_state["swap"][k] for k in swap}
            if (
                swap
                and set(swap) <= prev_state.get("swap", {}).keys()
                and all(swap[k] >= prev_state["swap"][k] for k in swap)
            )
            else None
        ),
        "process_io": process_io,
        "process_io_scope": "selected_main_named_jobs_and_bounded_descendants_no_group_sum",
        "disk_devices": disk.get("devices", {}),
        "disk_intervals": _device_intervals(
            disk, prev_state.get("disk", {}), now_ts - prev_state.get("epoch", now_ts)
        ),
        "top": top,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _append_json_line_durable(LOG_PATH, sample)
    _save_state(
        {
            "cpu": cpu,
            "disk": disk,
            "epoch": int(now_ts),
            "process_io": process_io,
            "swap": swap,
        }
    )
    return sample


def sample_once() -> dict:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a", encoding="utf-8") as lock_fp:
        fcntl.flock(lock_fp.fileno(), fcntl.LOCK_EX)
        return _sample_locked()


def main() -> int:
    sample_once()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
