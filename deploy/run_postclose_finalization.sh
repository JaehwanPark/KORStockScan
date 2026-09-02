#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
WAIT_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_WAIT_TIMEOUT_SEC:-5100}"
POLL_SEC="${POSTCLOSE_FINALIZATION_POLL_SEC:-30}"
HARD_DEADLINE_KST="${POSTCLOSE_FINALIZATION_HARD_DEADLINE_KST:-23:20}"
CLEANUP_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_CLEANUP_TIMEOUT_SEC:-600}"
DETECTOR_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_DETECTOR_TIMEOUT_SEC:-600}"
ALLOW_NONCURRENT_TARGET="${POSTCLOSE_FINALIZATION_ALLOW_NONCURRENT_TARGET:-false}"
OWNED_LOG_RUNNER="${POSTCLOSE_FINALIZATION_OWNED_LOG_RUNNER:-$SCRIPT_DIR/run_with_owned_log.sh}"
CLEANUP_RUNNER="${POSTCLOSE_FINALIZATION_CLEANUP_RUNNER:-$SCRIPT_DIR/run_logs_rotation_cleanup_cron.sh}"
ERROR_DETECTION_RUNNER="${POSTCLOSE_FINALIZATION_ERROR_DETECTION_RUNNER:-$SCRIPT_DIR/run_error_detection.sh}"

if [[ ! "$WAIT_TIMEOUT_SEC" =~ ^[0-9]+$ || ! "$POLL_SEC" =~ ^[1-9][0-9]*$ || ! "$CLEANUP_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$DETECTOR_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$HARD_DEADLINE_KST" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=invalid_wait_config"
  exit 2
fi
if [[ "$ALLOW_NONCURRENT_TARGET" != "true" && "$TARGET_DATE" != "$(TZ=Asia/Seoul date +%F)" ]]; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=noncurrent_target_for_final_detector"
  exit 2
fi

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/tmp"
cd "$PROJECT_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] postclose_finalization target_date=${TARGET_DATE} wait_timeout_sec=${WAIT_TIMEOUT_SEC} hard_deadline_kst=${HARD_DEADLINE_KST} started_at=${started_at}"

predecessor_state() {
  env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" <<'PY'
import json
import re
import sys
from pathlib import Path

project = Path(sys.argv[1])
target_date = sys.argv[2]


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def safe_int(value, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def terminal_failure_status(value) -> bool:
    status = str(value or "").strip().lower()
    return status.startswith(("fail", "error", "blocked"))


def latest_marker(path: Path, owner: str) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "missing"
    pattern = re.compile(
        rf"\[(START|DONE|FAIL)\]\s+{re.escape(owner)}\b.*\btarget_date={re.escape(target_date)}\b",
        re.IGNORECASE,
    )
    for line in reversed(lines):
        match = pattern.search(line)
        if match:
            return match.group(1).lower()
    return "missing"


checks = {}
threshold = load(
    project
    / "data/report/threshold_cycle_postclose_status"
    / f"threshold_cycle_postclose_{target_date}.status.json"
)
if threshold is None:
    checks["threshold_artifact"] = "waiting"
elif str(threshold.get("target_date") or "") != target_date:
    checks["threshold_artifact"] = "failed_target_date"
elif str(threshold.get("status") or "").lower() in {
    "succeeded", "success", "completed", "pass", "passed"
} and safe_int(threshold.get("exit_code") or 0) == 0:
    checks["threshold_artifact"] = "done"
elif terminal_failure_status(threshold.get("status")):
    checks["threshold_artifact"] = "failed"
else:
    checks["threshold_artifact"] = "waiting"

controller = load(
    project
    / "data/report/postclose_done_controller"
    / f"postclose_done_controller_{target_date}.json"
)
if controller is None:
    checks["controller_artifact"] = "waiting"
elif str(controller.get("date") or controller.get("target_date") or "") != target_date:
    checks["controller_artifact"] = "failed_target_date"
elif str(controller.get("status") or "").lower() == "done":
    checks["controller_artifact"] = "done"
elif terminal_failure_status(controller.get("status")):
    checks["controller_artifact"] = "failed"
else:
    checks["controller_artifact"] = "waiting"

tuning = load(
    project
    / "data/report/tuning_monitoring/status"
    / f"tuning_monitoring_postclose_{target_date}.json"
)
if tuning is None:
    checks["tuning_artifact"] = "waiting"
elif str(tuning.get("target_date") or "") != target_date:
    checks["tuning_artifact"] = "failed_target_date"
elif str(tuning.get("status") or "").lower() in {
    "succeeded", "success", "completed", "pass", "passed"
} and safe_int(tuning.get("exit_code") or 0) == 0:
    checks["tuning_artifact"] = "done"
elif terminal_failure_status(tuning.get("status")):
    checks["tuning_artifact"] = "failed"
else:
    checks["tuning_artifact"] = "waiting"

checks["threshold_log"] = latest_marker(
    project / "logs/threshold_cycle_postclose_cron.log", "threshold-cycle postclose"
)
checks["controller_log"] = latest_marker(
    project / "logs/postclose_done_controller_cron.log", "postclose_done_controller"
)
checks["tuning_log"] = latest_marker(
    project / "logs/tuning_monitoring_postclose_cron.log", "tuning_monitoring_postclose"
)
checks["dashboard_log"] = latest_marker(
    project / "logs/dashboard_db_archive_cron.log", "dashboard_db_archive"
)

failed = sorted(key for key, value in checks.items() if value.startswith("fail"))
waiting = sorted(
    key for key, value in checks.items() if value != "done" and key not in failed
)
detail = ",".join(f"{key}:{checks[key]}" for key in sorted(checks))
if failed:
    print(f"failed|{','.join(failed)}|{detail}")
elif waiting:
    print(f"waiting|{','.join(waiting)}|{detail}")
else:
    print(f"ready|-|{detail}")
PY
}

run_final_detector() {
  timeout --foreground "${DETECTOR_TIMEOUT_SEC}s" bash "$OWNED_LOG_RUNNER" \
    --owner error_detection_cron \
    --log "$PROJECT_DIR/logs/run_error_detection_cron.log" \
    bash "$ERROR_DETECTION_RUNNER" full
}

waited=0
while true; do
  if [[ "$ALLOW_NONCURRENT_TARGET" != "true" ]]; then
    current_hm="$(TZ=Asia/Seoul date +%H:%M)"
    current_total=$((10#${current_hm%:*} * 60 + 10#${current_hm#*:}))
    deadline_total=$((10#${HARD_DEADLINE_KST%:*} * 60 + 10#${HARD_DEADLINE_KST#*:}))
    if ((current_total >= deadline_total)); then
      echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=same_date_hard_deadline current_kst=${current_hm} hard_deadline_kst=${HARD_DEADLINE_KST}"
      run_final_detector || true
      exit 1
    fi
  fi
  if ! state_line="$(predecessor_state)"; then
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=predecessor_check_error"
    run_final_detector || true
    exit 1
  fi
  state="${state_line%%|*}"
  remainder="${state_line#*|}"
  blockers="${remainder%%|*}"
  details="${remainder#*|}"
  case "$state" in
    ready)
      echo "[INFO] postclose_finalization predecessors_ready target_date=${TARGET_DATE} waited=${waited}s details=${details}"
      break
      ;;
    failed)
      echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=predecessor_terminal_failure blockers=${blockers} details=${details}"
      run_final_detector || true
      exit 1
      ;;
  esac
  if ((waited >= WAIT_TIMEOUT_SEC)); then
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=predecessor_timeout waited=${waited}s blockers=${blockers} details=${details}"
    run_final_detector || true
    exit 1
  fi
  if ((waited == 0)); then
    echo "[INFO] postclose_finalization waiting target_date=${TARGET_DATE} blockers=${blockers}"
  fi
  sleep "$POLL_SEC"
  waited=$((waited + POLL_SEC))
done

if ! timeout --foreground "${CLEANUP_TIMEOUT_SEC}s" bash "$OWNED_LOG_RUNNER" \
  --owner log_rotation_cleanup_cron \
  --log "$PROJECT_DIR/logs/log_rotation_cleanup_cron.log" \
  env TARGET_DATE="$TARGET_DATE" "$CLEANUP_RUNNER" 30; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=cleanup_failed"
  run_final_detector || true
  exit 1
fi
echo "[INFO] postclose_finalization cleanup_done target_date=${TARGET_DATE}"

# The final detector audits this wrapper through the cron-completion registry.
# Publish the predecessor+cleanup terminal marker synchronously before handing
# off to that detector, otherwise the detector can only observe its own parent
# as in-progress. A detector execution failure appends a later FAIL marker, so
# the latest-terminal contract remains fail-closed.
finalization_finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_finalization target_date=${TARGET_DATE} cleanup=done detector_handoff=started finished_at=${finalization_finished_at}"
if ! run_final_detector; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=final_detector_failed"
  exit 1
fi
detector_finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_final_detector target_date=${TARGET_DATE} finalization=done detector=done finished_at=${detector_finished_at}"
