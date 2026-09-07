from __future__ import annotations

import fcntl
import time
from pathlib import Path

from src.utils.constants import PROJECT_ROOT, TRADING_RULES
from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)

LOCK_DIR = PROJECT_ROOT / "tmp"
MAX_LOCK_AGE_SEC = 3600
MAX_LOCKS_TO_CLEAN = 20  # Compatibility name; inspection never deletes a lock file.


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
        max_age = int(
            getattr(
                TRADING_RULES, "ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC", MAX_LOCK_AGE_SEC
            )
        )
        observations = []
        unknown = []
        # An old marker is not a stale mutex. Do not unlink even an unlocked
        # inode: a concurrent waiter may already hold an open descriptor to it.
        for path in sorted(LOCK_DIR.glob("*.lock")):
            try:
                stat = path.stat()
                if not path.is_file():
                    continue
                age = now_ts - stat.st_mtime
                state = self._inspect_lock(path)
            except OSError:
                state, age = "inspection_unavailable", None
            row = {
                "path": str(path),
                "state": state,
                "age_sec": age,
                "age_threshold_exceeded": age is not None and age >= max_age,
                "owner_health": "not_assessed",
                "deleted": False,
            }
            observations.append(row)
            if state == "inspection_unavailable":
                unknown.append(str(path))
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity="warning" if unknown else "pass",
            summary=(
                "Lock occupancy inspection incomplete."
                if unknown
                else "Lock occupancy inspected; age alone does not establish stale ownership."
            ),
            details={
                "locks_checked": len(observations),
                "lock_observations": observations,
                "inspection_unavailable": unknown,
                "cleanup_performed": False,
                "metric_contract": {
                    "metric_role": "source_quality_diagnostic",
                    "decision_authority": "read_only_lock_occupancy_observation",
                    "window_policy": "current_check_each_existing_lock_inode",
                    "sample_floor": "per_lock_inspection_not_economic_sampling",
                    "primary_decision_metric": "lock_observations",
                    "source_quality_gate": "unreadable_occupancy_remains_unknown",
                    "forbidden_uses": [
                        "lock_deletion",
                        "owner_health_from_age_or_occupancy",
                        "process_restart",
                        "trading_authority",
                    ],
                },
                "decision_authority": "read_only_lock_occupancy_observation",
                "held_owner_progress_check_required": any(
                    r["state"] == "held" for r in observations
                ),
            },
            recommended_action="Check holder PID/start time and progress before classifying any held lock as stale.",
        )

    @staticmethod
    def _inspect_lock(path: Path) -> str:
        try:
            with path.open("rb") as stream:
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return "held"
                fcntl.flock(stream, fcntl.LOCK_UN)
                return "unheld_marker_preserved"
        except OSError:
            return "inspection_unavailable"
