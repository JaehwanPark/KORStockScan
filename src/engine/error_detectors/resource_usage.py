from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from src.utils.constants import PROJECT_ROOT, TRADING_RULES
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)

SAMPLER_JSONL = PROJECT_ROOT / "logs" / "system_metric_samples.jsonl"
RECENT_SAMPLES = 5


@register_detector
class ResourceUsageDetector(BaseDetector):
    id = "resource_usage"
    name = "Resource Usage Detector"
    category = "resource"

    def check(self) -> DetectionResult:
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []

        cpu_busy_max = float(
            getattr(TRADING_RULES, "ERROR_DETECTOR_CPU_BUSY_MAX_PCT", 95.0)
        )
        mem_avail_min = float(
            getattr(TRADING_RULES, "ERROR_DETECTOR_MEM_AVAILABLE_MIN_MB", 500.0)
        )
        disk_free_min = float(
            getattr(TRADING_RULES, "ERROR_DETECTOR_DISK_FREE_MIN_MB", 2048.0)
        )
        swap_used_max = float(
            getattr(TRADING_RULES, "ERROR_DETECTOR_SWAP_USED_MAX_PCT", 80.0)
        )
        loadavg_15m_max = float(
            getattr(TRADING_RULES, "ERROR_DETECTOR_LOADAVG_15M_MAX", 8.0)
        )
        trading_day = is_krx_trading_day(datetime.now().astimezone().date())
        details["trading_day"] = trading_day

        latest_sample = self._read_latest_sample()
        if latest_sample:
            sampler_age_sec = self._sampler_age_sec(latest_sample)
            details["sampler_age_sec"] = round(sampler_age_sec, 1)
            max_sample_age = getattr(
                TRADING_RULES, "ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC", 600
            )

            if not trading_day:
                details["sampler_status"] = "skip_non_trading_day"
            elif sampler_age_sec > max_sample_age * 2:
                issues.append(
                    f"Sampler data stale ({sampler_age_sec:.0f}s > {max_sample_age * 2:.0f}s)"
                )
            elif sampler_age_sec > max_sample_age:
                warnings.append(
                    f"Sampler data aging ({sampler_age_sec:.0f}s > {max_sample_age}s)"
                )

            cpu_pct = latest_sample.get("cpu", {}).get("cpu_busy_pct", 0)
            mem = latest_sample.get("memory", {})
            mem_avail_mb = mem.get("mem_available_mb", 0)
            swap_free_mb = mem.get("swap_free_mb", 0)
            swap_total_mb = mem.get("swap_total_mb", 0)
            load15 = latest_sample.get("loadavg", {}).get("15m", 0)

            details["cpu_busy_pct"] = cpu_pct
            details["mem_available_mb"] = mem_avail_mb
            details["swap_total_mb"] = swap_total_mb
            details["swap_free_mb"] = swap_free_mb
            details["loadavg_15m"] = load15

            swap_used_pct = 0.0
            if swap_total_mb > 0:
                swap_used_pct = ((swap_total_mb - swap_free_mb) / swap_total_mb) * 100
                details["swap_used_pct"] = round(swap_used_pct, 1)

            if cpu_pct >= cpu_busy_max * 0.9:
                if cpu_pct >= cpu_busy_max:
                    issues.append(f"CPU busy {cpu_pct}% >= {cpu_busy_max}%")
                else:
                    warnings.append(f"CPU busy {cpu_pct}% approaching {cpu_busy_max}%")
            if mem_avail_mb < mem_avail_min * 2:
                if mem_avail_mb < mem_avail_min:
                    issues.append(
                        f"Memory available {mem_avail_mb}MB < {mem_avail_min}MB"
                    )
                else:
                    warnings.append(
                        f"Memory available {mem_avail_mb}MB approaching {mem_avail_min}MB"
                    )
            healthy_mem_floor_mb = mem_avail_min * 4
            if swap_used_pct >= swap_used_max * 0.9:
                if swap_used_pct >= swap_used_max:
                    if mem_avail_mb >= healthy_mem_floor_mb:
                        warnings.append(
                            f"Swap used {swap_used_pct}% >= {swap_used_max}% but memory available {mem_avail_mb}MB remains healthy"
                        )
                        details["swap_pressure_state"] = "swap_high_memory_healthy"
                    else:
                        issues.append(f"Swap used {swap_used_pct}% >= {swap_used_max}%")
                else:
                    warnings.append(
                        f"Swap used {swap_used_pct}% approaching {swap_used_max}%"
                    )
            if load15 >= loadavg_15m_max * 0.9:
                if load15 >= loadavg_15m_max:
                    issues.append(f"Loadavg 15m {load15} >= {loadavg_15m_max}")
                else:
                    warnings.append(
                        f"Loadavg 15m {load15} approaching {loadavg_15m_max}"
                    )
        else:
            details["sampler_status"] = (
                "skip_non_trading_day" if not trading_day else "no_data"
            )
            try:
                load1, load5, load15 = os.getloadavg()
                details["loadavg_15m"] = load15
                loadavg_15m_max = float(
                    getattr(TRADING_RULES, "ERROR_DETECTOR_LOADAVG_15M_MAX", 8.0)
                )
                if load15 >= loadavg_15m_max:
                    issues.append(f"Loadavg 15m {load15:.1f} >= {loadavg_15m_max}")
            except Exception:
                pass

        disk_free = self._check_disk_free()
        details["disk_free_mb"] = round(disk_free, 1)
        if disk_free < disk_free_min * 2:
            if disk_free < disk_free_min:
                issues.append(f"Disk free {disk_free:.0f}MB < {disk_free_min}MB")
                self._auto_rotate_logs(details)
            else:
                warnings.append(
                    f"Disk free {disk_free:.0f}MB approaching {disk_free_min}MB"
                )

        severity, summary = self._classify(issues, warnings)
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, issues),
        )

    @staticmethod
    def _read_latest_sample() -> dict | None:
        if not SAMPLER_JSONL.exists():
            return None
        try:
            with SAMPLER_JSONL.open("rb") as fh:
                try:
                    fh.seek(-65536, os.SEEK_END)
                except OSError:
                    fh.seek(0)
                lines = fh.read().decode("utf-8", errors="replace").strip().splitlines()
            if not lines:
                return None
            latest = lines[-1]
            return json.loads(latest)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _sampler_age_sec(sample: dict) -> float:
        epoch = sample.get("epoch")
        if epoch and isinstance(epoch, (int, float)):
            return time.time() - float(epoch)
        ts_str = sample.get("ts", "")
        try:
            dt = datetime.fromisoformat(ts_str)
            return time.time() - dt.timestamp()
        except (ValueError, TypeError):
            return float("inf")

    _ROTATE_COOLDOWN_STATE = (
        PROJECT_ROOT / "tmp" / "error_detector_last_log_rotate_ts.txt"
    )

    def _auto_rotate_logs(self, details: dict):
        if self.dry_run:
            details["log_rotate_trigger"] = "skipped_dry_run"
            return
        if not bool(
            getattr(TRADING_RULES, "ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED", True)
        ):
            details["log_rotate_trigger"] = "disabled_via_flag"
            return

        now_ts = time.time()
        last_ts = self._read_rotate_cooldown_ts()
        if last_ts > 0 and now_ts - last_ts < 1800:
            details["log_rotate_trigger"] = "cooldown_active"
            return
        rotate_script = PROJECT_ROOT / "deploy" / "run_logs_rotation_cleanup_cron.sh"
        if not rotate_script.exists():
            details["log_rotate_trigger"] = "script_not_found"
            return
        try:
            result = subprocess.run(
                ["bash", str(rotate_script), "30"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(PROJECT_ROOT),
            )
            self._write_rotate_cooldown_ts(now_ts)
            details["log_rotate_trigger"] = "ok"
            details["log_rotate_output"] = (
                result.stdout.strip().rsplit("\n", 1)[-1] if result.stdout else ""
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            details["log_rotate_trigger"] = f"error: {e}"

    @staticmethod
    def _check_disk_free() -> float:
        try:
            stat = os.statvfs(str(PROJECT_ROOT))
            free_bytes = stat.f_frsize * stat.f_bavail
            return free_bytes / (1024 * 1024)
        except OSError:
            return float("inf")

    @staticmethod
    def _classify(issues: list[str], warnings: list[str]) -> tuple[str, str]:
        if issues:
            return "fail", f"Resource issues: {'; '.join(issues[:5])}"
        if warnings:
            return "warning", f"Resource warnings: {'; '.join(warnings[:5])}"
        return "pass", "All resources within thresholds."

    @staticmethod
    def _recommend_action(severity: str, issues: list[str]) -> str:
        if severity == "fail":
            return f"Address resource issues: {'; '.join(issues[:3])}"
        if severity == "warning":
            return "Resource usage approaching thresholds. Monitor."
        return ""

    @staticmethod
    def _read_rotate_cooldown_ts() -> float:
        state = ResourceUsageDetector._ROTATE_COOLDOWN_STATE
        if not state.exists():
            return 0.0
        try:
            return float(state.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            return 0.0

    @staticmethod
    def _write_rotate_cooldown_ts(ts: float):
        state = ResourceUsageDetector._ROTATE_COOLDOWN_STATE
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(str(ts), encoding="utf-8")
