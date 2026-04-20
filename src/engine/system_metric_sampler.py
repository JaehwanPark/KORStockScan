from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "logs" / "system_metric_samples.jsonl"
STATE_PATH = PROJECT_ROOT / "tmp" / "system_metric_sampler_state.json"


def _read_proc_stat() -> dict[str, int]:
    line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0]
    parts = line.split()
    keys = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]
    values = [int(v) for v in parts[1:1 + len(keys)]]
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


def _read_diskstats() -> dict[str, int]:
    read_sectors = 0
    write_sectors = 0
    for line in Path("/proc/diskstats").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        name = parts[2]
        if name.startswith(("loop", "ram", "dm-")):
            continue
        if name[-1].isdigit() and not name.startswith("nvme"):
            continue
        read_sectors += int(parts[5])
        write_sectors += int(parts[9])
    return {"read_sectors": read_sectors, "write_sectors": write_sectors}


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
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=True), encoding="utf-8")


def _cpu_pct(curr: dict[str, int], prev: dict[str, int]) -> dict[str, float]:
    if not prev:
        return {"cpu_busy_pct": 0.0, "iowait_pct": 0.0}
    curr_total = sum(curr.values())
    prev_total = sum(int(prev.get(k, 0)) for k in curr.keys())
    total_delta = curr_total - prev_total
    if total_delta <= 0:
        return {"cpu_busy_pct": 0.0, "iowait_pct": 0.0}
    idle_delta = curr["idle"] - int(prev.get("idle", 0))
    iowait_delta = curr["iowait"] - int(prev.get("iowait", 0))
    busy_pct = max(0.0, min(100.0, (1.0 - (idle_delta / total_delta)) * 100.0))
    iowait_pct = max(0.0, min(100.0, (iowait_delta / total_delta) * 100.0))
    return {"cpu_busy_pct": round(busy_pct, 2), "iowait_pct": round(iowait_pct, 2)}


def _disk_delta(curr: dict[str, int], prev: dict[str, int]) -> dict[str, float]:
    read_delta = max(0, curr["read_sectors"] - int(prev.get("read_sectors", 0)))
    write_delta = max(0, curr["write_sectors"] - int(prev.get("write_sectors", 0)))
    return {
        "disk_read_mb_delta": round((read_delta * 512) / (1024 * 1024), 3),
        "disk_write_mb_delta": round((write_delta * 512) / (1024 * 1024), 3),
    }


def sample_once() -> dict:
    now_ts = time.time()
    now_iso = datetime.fromtimestamp(now_ts).astimezone().isoformat(timespec="seconds")
    prev_state = _load_state()
    cpu = _read_proc_stat()
    disk = _read_diskstats()
    mem = _read_meminfo()
    load1, load5, load15 = os.getloadavg()
    sample = {
        "ts": now_iso,
        "epoch": int(now_ts),
        "loadavg": {"1m": round(load1, 3), "5m": round(load5, 3), "15m": round(load15, 3)},
        "cpu": _cpu_pct(cpu, prev_state.get("cpu", {})),
        "memory": {
            "mem_total_mb": round(mem.get("MemTotal", 0) / 1024, 1),
            "mem_available_mb": round(mem.get("MemAvailable", 0) / 1024, 1),
            "mem_free_mb": round(mem.get("MemFree", 0) / 1024, 1),
            "swap_total_mb": round(mem.get("SwapTotal", 0) / 1024, 1),
            "swap_free_mb": round(mem.get("SwapFree", 0) / 1024, 1),
        },
        "io": _disk_delta(disk, prev_state.get("disk", {})),
        "top": _top_processes(),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(sample, ensure_ascii=True) + "\n")
    _save_state({"cpu": cpu, "disk": disk, "epoch": int(now_ts)})
    return sample


def main() -> int:
    sample_once()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
