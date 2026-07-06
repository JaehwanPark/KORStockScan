#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
DIFF_DAYS="${DIFF_DAYS:-3}"
LOCK_FILE="${TUNING_MONITORING_LOCK_FILE:-$PROJECT_DIR/tmp/run_tuning_monitoring_postclose.lock}"
LOCK_WAIT_SEC="${TUNING_MONITORING_LOCK_WAIT_SEC:-60}"
MAX_RETRIES="${TUNING_MONITORING_MAX_RETRIES:-2}"
RETRY_DELAY_SEC="${TUNING_MONITORING_RETRY_DELAY_SEC:-10}"
STATUS_DIR="${TUNING_MONITORING_STATUS_DIR:-$PROJECT_DIR/data/report/tuning_monitoring/status}"
STATUS_FILE="${TUNING_MONITORING_STATUS_FILE:-$STATUS_DIR/tuning_monitoring_postclose_${TARGET_DATE}.json}"
DRY_RUN="${TUNING_MONITORING_DRY_RUN:-0}"
RUN_PATTERN_LABS="${TUNING_MONITORING_RUN_PATTERN_LABS:-false}"
PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-2026-04-21}"
REQUIRE_THRESHOLD_POSTCLOSE_DONE="${TUNING_MONITORING_REQUIRE_THRESHOLD_POSTCLOSE_DONE:-true}"
PREDECESSOR_LOG="${TUNING_MONITORING_PREDECESSOR_LOG:-$PROJECT_DIR/logs/threshold_cycle_postclose_cron.log}"
PREDECESSOR_WAIT_SEC="${TUNING_MONITORING_PREDECESSOR_WAIT_SEC:-3600}"
PREDECESSOR_WAIT_INTERVAL_SEC="${TUNING_MONITORING_PREDECESSOR_WAIT_INTERVAL_SEC:-60}"

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/tmp" "$STATUS_DIR"
cd "$PROJECT_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] tuning_monitoring_postclose target_date=${TARGET_DATE} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] tuning_monitoring_postclose target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

START_DATE="$(TZ=Asia/Seoul date -d "$TARGET_DATE -$((DIFF_DAYS - 1)) days" +%F)"

validate_int() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

LOCK_WAIT_SEC="$(validate_int "$LOCK_WAIT_SEC" 60)"
MAX_RETRIES="$(validate_int "$MAX_RETRIES" 2)"
RETRY_DELAY_SEC="$(validate_int "$RETRY_DELAY_SEC" 10)"
PREDECESSOR_WAIT_SEC="$(validate_int "$PREDECESSOR_WAIT_SEC" 3600)"
PREDECESSOR_WAIT_INTERVAL_SEC="$(validate_int "$PREDECESSOR_WAIT_INTERVAL_SEC" 60)"

threshold_postclose_terminal_marker() {
  env PYTHONPATH=. "$VENV_PY" - "$PREDECESSOR_LOG" "$TARGET_DATE" "$PROJECT_DIR/data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_${TARGET_DATE}.status.json" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
target_date = sys.argv[2]
status_path = Path(sys.argv[3])

def status_artifact_terminal() -> str | None:
    if not status_path.exists():
        return None
    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if str(payload.get("target_date") or "") != target_date:
        return None
    status = str(payload.get("status") or "").lower()
    try:
        exit_code = int(payload.get("exit_code") or 0)
    except (TypeError, ValueError):
        exit_code = 1
    verification_status = str(
        ((payload.get("manual_recovery") or {}).get("verification_status") or "")
    ).lower()
    if status in {"succeeded", "success", "passed", "pass", "completed"} and exit_code == 0:
        return "done"
    if verification_status == "pass_with_pending_done_marker" and exit_code == 0:
        return "done"
    if status in {"failed", "fail", "error"}:
        return "failed"
    return None

if not path.exists():
    print(status_artifact_terminal() or "missing_log")
    raise SystemExit(0)

marker_re = re.compile(r"\[(START|DONE|FAIL|ERROR|CRITICAL)\].*target_date=" + re.escape(target_date), re.IGNORECASE)
try:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
except OSError:
    print(status_artifact_terminal() or "missing_log")
    raise SystemExit(0)

for line in reversed(lines):
    match = marker_re.search(line)
    if not match:
        continue
    marker = match.group(1).upper()
    if marker == "START":
        print(status_artifact_terminal() or "in_progress")
    elif marker == "DONE":
        print("done")
    else:
        print("failed")
    raise SystemExit(0)
print(status_artifact_terminal() or "missing_marker")
PY
}

wait_for_threshold_postclose_done() {
  if [[ "$REQUIRE_THRESHOLD_POSTCLOSE_DONE" != "1" && "$REQUIRE_THRESHOLD_POSTCLOSE_DONE" != "true" ]]; then
    echo "[INFO] threshold_cycle_postclose predecessor check skipped target_date=${TARGET_DATE}"
    return 0
  fi

  local waited=0
  local status
  while true; do
    status="$(threshold_postclose_terminal_marker)"
    case "$status" in
      done)
        echo "[INFO] threshold_cycle_postclose predecessor done target_date=${TARGET_DATE} waited=${waited}s"
        return 0
        ;;
      failed)
        if [[ "$waited" -ge "$PREDECESSOR_WAIT_SEC" ]]; then
          echo "[FAIL] tuning_monitoring_postclose target_date=${TARGET_DATE} reason=threshold_cycle_postclose_failed waited=${waited}s"
          return 1
        fi
        if [[ "$waited" -eq 0 ]]; then
          echo "[WARN] threshold_cycle_postclose predecessor failed; waiting for recovery target_date=${TARGET_DATE}"
        fi
        ;;
    esac

    if [[ "$waited" -ge "$PREDECESSOR_WAIT_SEC" ]]; then
      echo "[FAIL] tuning_monitoring_postclose target_date=${TARGET_DATE} reason=threshold_cycle_postclose_not_done waited=${waited}s status=${status}"
      return 1
    fi
    if [[ "$waited" -eq 0 ]]; then
      echo "[INFO] waiting for threshold_cycle_postclose predecessor target_date=${TARGET_DATE} status=${status}"
    fi
    sleep "$PREDECESSOR_WAIT_INTERVAL_SEC"
    waited=$((waited + PREDECESSOR_WAIT_INTERVAL_SEC))
  done
}

write_status() {
  local overall_status="$1"
  local failed_step="${2:-}"
  local exit_code="${3:-0}"
  local finished="${4:-0}"
  env PYTHONPATH=. "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$START_DATE" "$overall_status" "$failed_step" "$exit_code" "$finished" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, start_date, overall_status, failed_step, exit_code, finished = sys.argv[2:8]
payload = {}
if overall_status != "running" and path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
payload.setdefault("target_date", target_date)
payload.setdefault("start_date", start_date)
payload.setdefault("started_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
payload.setdefault("steps", [])
payload["status"] = overall_status
payload["failed_step"] = failed_step or None
payload["exit_code"] = int(exit_code or 0)
if finished == "1":
    payload["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

record_step() {
  local step_name="$1"
  local status="$2"
  local attempt="$3"
  local exit_code="$4"
  local command_text="$5"
  env PYTHONPATH=. "$VENV_PY" - "$STATUS_FILE" "$step_name" "$status" "$attempt" "$exit_code" "$command_text" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
step_name, status, attempt, exit_code, command_text = sys.argv[2:7]
payload = {}
if path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
payload.setdefault("steps", [])
payload["steps"].append(
    {
        "step": step_name,
        "status": status,
        "attempt": int(attempt),
        "exit_code": int(exit_code),
        "command": command_text,
        "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

run_step() {
  local step_name="$1"
  shift
  local attempt=1
  local status=0
  local command_text="$*"

  for attempt in $(seq 1 "$MAX_RETRIES"); do
    record_step "$step_name" "started" "$attempt" 0 "$command_text"
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "[DRY_RUN] $step_name: $command_text"
      record_step "$step_name" "success" "$attempt" 0 "$command_text"
      return 0
    fi

    set +e
    "$@"
    status=$?
    set -e

    if [[ "$status" -eq 0 ]]; then
      record_step "$step_name" "success" "$attempt" 0 "$command_text"
      return 0
    fi

    record_step "$step_name" "failed" "$attempt" "$status" "$command_text"
    if [[ "$attempt" -lt "$MAX_RETRIES" ]]; then
      echo "[WARN] $step_name failed attempt=${attempt}/${MAX_RETRIES}; retrying in ${RETRY_DELAY_SEC}s"
      sleep "$RETRY_DELAY_SEC"
    fi
  done

  return "$status"
}

main() {
  write_status "running" "" 0 0
  wait_for_threshold_postclose_done

  run_step "build_parquet_pipeline_events" env PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
    --dataset pipeline_events \
    --single-date "$TARGET_DATE"

  run_step "build_parquet_post_sell" env PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
    --dataset post_sell \
    --single-date "$TARGET_DATE"

  run_step "build_parquet_system_metric_samples" env PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
    --dataset system_metric_samples \
    --single-date "$TARGET_DATE"

  run_step "compare_tuning_shadow_diff" env PYTHONPATH=. "$VENV_PY" -m src.engine.compare_tuning_shadow_diff \
    --start "$START_DATE" \
    --end "$TARGET_DATE"

  if [[ "$RUN_PATTERN_LABS" == "1" || "$RUN_PATTERN_LABS" == "true" ]]; then
    run_step "claude_scalping_pattern_lab" env ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" "$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh"
    record_step "gemini_scalping_pattern_lab" "skipped" 0 0 "retired_from_automatic_execution"
  else
    record_step "pattern_labs" "skipped" 1 0 "canonical_runner=THRESHOLD_CYCLE_POSTCLOSE"
  fi

  write_status "success" "" 0 1
  echo "[INFO] tuning monitoring postclose completed status_file=$STATUS_FILE"
}

set +e
flock -w "$LOCK_WAIT_SEC" "$LOCK_FILE" bash -c "$(declare -f validate_int write_status record_step run_step threshold_postclose_terminal_marker wait_for_threshold_postclose_done main); set -euo pipefail; PROJECT_DIR='$PROJECT_DIR' VENV_PY='$VENV_PY' TARGET_DATE='$TARGET_DATE' START_DATE='$START_DATE' STATUS_FILE='$STATUS_FILE' MAX_RETRIES='$MAX_RETRIES' RETRY_DELAY_SEC='$RETRY_DELAY_SEC' DRY_RUN='$DRY_RUN' RUN_PATTERN_LABS='$RUN_PATTERN_LABS' PATTERN_LAB_START_DATE='$PATTERN_LAB_START_DATE' REQUIRE_THRESHOLD_POSTCLOSE_DONE='$REQUIRE_THRESHOLD_POSTCLOSE_DONE' PREDECESSOR_LOG='$PREDECESSOR_LOG' PREDECESSOR_WAIT_SEC='$PREDECESSOR_WAIT_SEC' PREDECESSOR_WAIT_INTERVAL_SEC='$PREDECESSOR_WAIT_INTERVAL_SEC'; main"
RUN_STATUS=$?
set -e

if [[ "$RUN_STATUS" -ne 0 ]]; then
  write_status "failed" "see_steps" "$RUN_STATUS" 1
  echo "[ERROR] tuning monitoring postclose failed status=${RUN_STATUS} status_file=$STATUS_FILE"
  finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
  echo "[FAIL] tuning_monitoring_postclose target_date=${TARGET_DATE} exit_code=${RUN_STATUS} finished_at=${finished_at}"
  exit "$RUN_STATUS"
fi
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] tuning_monitoring_postclose target_date=${TARGET_DATE} finished_at=${finished_at}"
