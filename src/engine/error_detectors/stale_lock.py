from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

from src.utils.constants import PROJECT_ROOT, TRADING_RULES

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)

LOCK_DIR = PROJECT_ROOT / "tmp"
MAX_LOCK_AGE_SEC = 3600
MAX_LOCKS_TO_CLEAN = 20


@register_detector
class StaleLockDetector(BaseDetector):
    id = "stale_lock"
    name = "Stale Lock Detector"
    category = "process"

    def check(self) -> DetectionResult:
        if not LOCK_DIR.exists():
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="pass",
                summary="Lock directory not found.",
            )
        now_ts = time.time()
        cleaned: list[str] = []
        stale_not_cleaned: list[str] = []
        would_clean: list[str] = []
        details: dict = {}
        max_age = int(
            getattr(
                TRADING_RULES, "ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC", MAX_LOCK_AGE_SEC
            )
        )
        cleanup_enabled = bool(
            getattr(TRADING_RULES, "ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED", True)
        )

        lock_files = sorted(
            [p for p in LOCK_DIR.glob("*.lock") if p.is_file()],
            key=lambda p: p.stat().st_mtime,
        )
        if len(lock_files) > MAX_LOCKS_TO_CLEAN:
            lock_files = lock_files[:MAX_LOCKS_TO_CLEAN]

        for lock_path in lock_files:
            try:
                mtime = lock_path.stat().st_mtime
            except OSError:
                continue
            age_sec = now_ts - mtime
            if age_sec < max_age:
                continue
            if self.dry_run:
                would_clean.append(f"{lock_path.name}({age_sec:.0f}s)")
                continue
            if not cleanup_enabled:
                stale_not_cleaned.append(f"{lock_path.name}({age_sec:.0f}s)")
                continue
            was_stale = self._try_remove_stale_lock(lock_path)
            if was_stale:
                cleaned.append(f"{lock_path.name}({age_sec:.0f}s)")
            else:
                stale_not_cleaned.append(f"{lock_path.name}({age_sec:.0f}s)")

        if cleaned:
            details["stale_locks_cleaned"] = cleaned
        if stale_not_cleaned:
            details["stale_locks_cannot_remove"] = stale_not_cleaned
        if would_clean:
            details["stale_locks_would_clean_dry_run"] = would_clean

        if cleaned or stale_not_cleaned or would_clean:
            parts: list[str] = []
            if cleaned:
                parts.append(f"cleaned {len(cleaned)} stale locks")
            if stale_not_cleaned:
                parts.append(f"{len(stale_not_cleaned)} still locked")
            if would_clean:
                parts.append(f"{len(would_clean)} would clean (dry-run)")
            summary = (
                "Stale locks: " + "; ".join(parts) if parts else "All locks healthy."
            )
            severity = "warning" if (cleaned or stale_not_cleaned) else "pass"
            action = f"Cleanup performed: {', '.join(cleaned[:5])}" if cleaned else ""
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity=severity,
                summary=summary,
                details=details,
                recommended_action=action,
            )

        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity="pass",
            summary="All lock files healthy.",
            details={"locks_checked": len(lock_files)},
        )

    @staticmethod
    def _try_remove_stale_lock(lock_path: Path) -> bool:
        try:
            with open(lock_path, "a+b") as fp:
                try:
                    import fcntl

                    fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    os.remove(lock_path)
                    return True
                except (BlockingIOError, OSError):
                    return False
        except OSError:
            return False
