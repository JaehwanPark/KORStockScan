#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
RECOVERY_MODE=false
if [[ "${2:-}" == "--recover-closed-target" ]]; then
  RECOVERY_MODE=true
elif [[ -n "${2:-}" ]]; then
  echo "[FAIL] postclose_finalization reason=unknown_mode"
  exit 2
fi
cleanup_recovery_args=()
if [[ "${3:-}" == "--recover-storage-only" && "$RECOVERY_MODE" == "true" && $# -eq 3 ]]; then
  cleanup_recovery_args+=(--recover-storage-only)
elif [[ -n "${3:-}" || $# -gt 3 ]]; then
  echo "[FAIL] postclose_finalization reason=unknown_cleanup_recovery_mode"
  exit 2
fi
WAIT_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_WAIT_TIMEOUT_SEC:-5100}"
POLL_SEC="${POSTCLOSE_FINALIZATION_POLL_SEC:-30}"
HARD_DEADLINE_KST="${POSTCLOSE_FINALIZATION_HARD_DEADLINE_KST:-23:20}"
CLEANUP_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_CLEANUP_TIMEOUT_SEC:-600}"
DETECTOR_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_DETECTOR_TIMEOUT_SEC:-600}"
SUMMARY_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_SUMMARY_TIMEOUT_SEC:-600}"
ALLOW_NONCURRENT_TARGET="${POSTCLOSE_FINALIZATION_ALLOW_NONCURRENT_TARGET:-false}"
OWNED_LOG_RUNNER="${POSTCLOSE_FINALIZATION_OWNED_LOG_RUNNER:-$SCRIPT_DIR/run_with_owned_log.sh}"
CLEANUP_RUNNER="${POSTCLOSE_FINALIZATION_CLEANUP_RUNNER:-$SCRIPT_DIR/run_logs_rotation_cleanup_cron.sh}"
ERROR_DETECTION_RUNNER="${POSTCLOSE_FINALIZATION_ERROR_DETECTION_RUNNER:-$SCRIPT_DIR/run_error_detection.sh}"

if [[ ! "$WAIT_TIMEOUT_SEC" =~ ^[0-9]+$ || ! "$POLL_SEC" =~ ^[1-9][0-9]*$ || ! "$CLEANUP_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$DETECTOR_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$SUMMARY_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$HARD_DEADLINE_KST" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=invalid_wait_config"
  exit 2
fi
if [[ "$RECOVERY_MODE" == "true" ]]; then
  "$VENV_PY" - "$TARGET_DATE" <<'PY'
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
day = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
assert day.isoformat() == sys.argv[1]
assert datetime.strptime("2026-06-05", "%Y-%m-%d").date() <= day <= datetime.now(ZoneInfo("Asia/Seoul")).date()
PY
  if [[ ! -s "$PROJECT_DIR/data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_${TARGET_DATE}.status.json" ]]; then
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=recovery_requires_retained_source_terminal"
    exit 2
  fi
  WAIT_TIMEOUT_SEC=0
fi
if [[ "$RECOVERY_MODE" != "true" && "$ALLOW_NONCURRENT_TARGET" != "true" && "$TARGET_DATE" != "$(TZ=Asia/Seoul date +%F)" ]]; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=noncurrent_target_for_final_detector"
  exit 2
fi

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/tmp"
cd "$PROJECT_DIR"
exec 8>"$PROJECT_DIR/tmp/postclose_finalization_${TARGET_DATE}.lock"
if ! flock -n 8; then
  echo "[SKIP] postclose_finalization target_date=${TARGET_DATE} reason=active_owner"
  exit 75
fi
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] postclose_finalization target_date=${TARGET_DATE} recovery=${RECOVERY_MODE} wait_timeout_sec=${WAIT_TIMEOUT_SEC} hard_deadline_kst=${HARD_DEADLINE_KST} started_at=${started_at}"

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

if target_date >= "2026-09-09":
    from src.engine.automation.postclose_summary_handoff import installed_producer_terminal_states
    checks.update(installed_producer_terminal_states(target_date, report_dir=project / "data/report"))

failed = sorted(key for key, value in checks.items() if value.startswith("fail"))
waiting = sorted(
    key for key, value in checks.items() if value not in {"done", "done_off_masked"} and key not in failed
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
  local detector_args=(full)
  if [[ "$RECOVERY_MODE" == "true" ]]; then
    detector_args+=("$TARGET_DATE")
  fi
  timeout --foreground "${DETECTOR_TIMEOUT_SEC}s" bash "$OWNED_LOG_RUNNER" \
    --owner error_detection_cron \
    --log "$PROJECT_DIR/logs/run_error_detection_cron.log" \
    env POSTCLOSE_FINALIZATION_DETECTOR_PARENT_PID="$$" POSTCLOSE_FINALIZATION_DETECTOR_DATE="$TARGET_DATE" \
    bash "$ERROR_DETECTION_RUNNER" "${detector_args[@]}"
}

waited=0
while true; do
  if [[ "$RECOVERY_MODE" != "true" && "$ALLOW_NONCURRENT_TARGET" != "true" ]]; then
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

if [[ "$TARGET_DATE" > "2026-09-08" ]]; then
  # Independent 20:10/21:15 producers may finish after main's original DONE.
  # Reuse the controller after exact independent terminal validation. No EV,
  # provider, workorder producer, live apply, or whole-wrapper recovery here.
  controller_started_after_ns="$(date +%s%N)"
  if ! timeout --kill-after=10s "${SUMMARY_TIMEOUT_SEC}s" env PYTHONPATH=. \
    POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED=false "$VENV_PY" \
    -m src.engine.automation.postclose_done_controller --date "$TARGET_DATE" \
    --require-independent-producers --max-attempts 2 --predecessor-timeout-sec 0; then
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=summary_handoff_refresh_failed"
    run_final_detector || true
    exit 1
  fi
controller_receipt="$(env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" "$controller_started_after_ns" <<'PY'
import json
import sys
from pathlib import Path
from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues

project = Path(sys.argv[1])
target_date = sys.argv[2]
started_after_ns = int(sys.argv[3])
report_path = project / "data/report/postclose_done_controller" / f"postclose_done_controller_{target_date}.json"
issues = done_terminal_receipt_issues(report_path, target_date, started_after_ns=started_after_ns)
print(json.dumps({"status": "pass" if not issues else "blocked", "issues": issues}, sort_keys=True))
raise SystemExit(0 if not issues else 1)
PY
)" || {
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=controller_terminal_receipt_invalid details=${controller_receipt}"
    run_final_detector || true
    exit 1
  }
  echo "[INFO] postclose_finalization controller_terminal_receipt=${controller_receipt}"
  echo "[INFO] postclose_finalization summary_handoff_verified target_date=${TARGET_DATE}"
fi

if ! timeout --foreground "${CLEANUP_TIMEOUT_SEC}s" bash "$OWNED_LOG_RUNNER" \
  --owner log_rotation_cleanup_cron \
  --log "$PROJECT_DIR/logs/log_rotation_cleanup_cron.log" \
  env TARGET_DATE="$TARGET_DATE" "$CLEANUP_RUNNER" 30 "${cleanup_recovery_args[@]}"; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=cleanup_failed"
  run_final_detector || true
  exit 1
fi
echo "[INFO] postclose_finalization cleanup_done target_date=${TARGET_DATE}"

# The child detector reports its live ancestor as pending, never as PASS.
echo "[INFO] postclose_finalization target_date=${TARGET_DATE} cleanup=done detector_handoff=started"
if ! run_final_detector; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=final_detector_failed"
  exit 1
fi
detector_finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_finalization target_date=${TARGET_DATE} cleanup=done detector=done finished_at=${detector_finished_at}"
echo "[DONE] postclose_final_detector target_date=${TARGET_DATE} finalization=done detector=done finished_at=${detector_finished_at}"
