#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"
LOCK_FILE="${MONITOR_SNAPSHOT_LOCK_FILE:-$PROJECT_DIR/tmp/run_monitor_snapshot.lock}"
LOG_FILE="${MONITOR_SNAPSHOT_LOG_FILE:-$PROJECT_DIR/logs/run_monitor_snapshot.log}"
TIMEOUT_SEC="${MONITOR_SNAPSHOT_TIMEOUT_SEC:-1200}"
ALLOW_PREOPEN_WITH_BOT="${ALLOW_PREOPEN_FULL_BUILD_WITH_BOT:-0}"
PROFILE="${MONITOR_SNAPSHOT_PROFILE:-full}"
IO_DELAY_SEC="${MONITOR_SNAPSHOT_IO_DELAY_SEC:-0}"
START_JITTER_SEC="${MONITOR_SNAPSHOT_START_JITTER_SEC:-0}"
NOTIFY_ADMIN=0
ASYNC_MODE="${MONITOR_SNAPSHOT_ASYNC:-1}"
ASYNC_WAIT_SEC="${MONITOR_SNAPSHOT_ASYNC_WAIT_SEC:-0}"
WORKER_MODE="${MONITOR_SNAPSHOT_WORKER:-0}"
KEEP_OUTPUT_FILE="${MONITOR_SNAPSHOT_KEEP_OUTPUT_FILE:-0}"
LOCK_WAIT_SEC="${MONITOR_SNAPSHOT_LOCK_WAIT_SEC:-}"
ALLOW_EXISTING_FULL_BUILD_WITH_BOT="${ALLOW_EXISTING_FULL_BUILD_WITH_BOT:-0}"
COOLDOWN_SEC="${MONITOR_SNAPSHOT_COOLDOWN_SEC:-}"
COOLDOWN_STATE_FILE="${MONITOR_SNAPSHOT_COOLDOWN_STATE_FILE:-}"
FORCE_SNAPSHOT="${MONITOR_SNAPSHOT_FORCE:-0}"
NOTIFY_ONLY="${MONITOR_SNAPSHOT_NOTIFY_ONLY:-0}"
MAX_RETRIES="${MONITOR_SNAPSHOT_MAX_RETRIES:-3}"
RETRY_DELAY_SEC="${MONITOR_SNAPSHOT_RETRY_DELAY_SEC:-5}"
IONICE_CLASS="${MONITOR_SNAPSHOT_IONICE_CLASS:-2}"
IONICE_LEVEL="${MONITOR_SNAPSHOT_IONICE_LEVEL:-6}"
NICE_LEVEL="${MONITOR_SNAPSHOT_NICE_LEVEL:-10}"
NICE_COMMAND="${MONITOR_SNAPSHOT_NICE_COMMAND:-nice}"
CPU_AFFINITY="${MONITOR_SNAPSHOT_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity monitor)}"

if [[ -z "${MONITOR_SNAPSHOT_LOCK_WAIT_SEC:-}" ]]; then
  if [[ "$PROFILE" == "full" ]]; then
    LOCK_WAIT_SEC=180
  else
    LOCK_WAIT_SEC=0
  fi
fi

if [[ -z "${MONITOR_SNAPSHOT_COOLDOWN_SEC:-}" ]]; then
  if [[ "$PROFILE" == "full" ]]; then
    COOLDOWN_SEC=180
  else
    COOLDOWN_SEC=60
  fi
fi

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/tmp"
cd "$PROJECT_DIR"

SAFE_PROFILE="${PROFILE//-/_}"
MANIFEST_PATH="$PROJECT_DIR/data/report/monitor_snapshots/manifests/monitor_snapshot_manifest_${TARGET_DATE}_${SAFE_PROFILE}.json"
if [[ -z "$COOLDOWN_STATE_FILE" ]]; then
  COOLDOWN_STATE_FILE="$PROJECT_DIR/tmp/run_monitor_snapshot_${SAFE_PROFILE}_success.state"
fi
ASYNC_PID_FILE="${MONITOR_SNAPSHOT_ASYNC_PID_FILE:-$PROJECT_DIR/tmp/run_monitor_snapshot_${SAFE_PROFILE}_${TARGET_DATE}.pid}"
ASYNC_RESULT_HINT="${MONITOR_SNAPSHOT_ASYNC_RESULT_HINT:-$PROJECT_DIR/tmp/run_monitor_snapshot_${SAFE_PROFILE}_${TARGET_DATE}.result}"
COMPLETION_ARTIFACT_FILE="${MONITOR_SNAPSHOT_COMPLETION_ARTIFACT_FILE:-$PROJECT_DIR/tmp/monitor_snapshot_completion_${TARGET_DATE}_${SAFE_PROFILE}.json}"

# PREOPEN(08:00~09:00 KST)에는 bot_main 동작 중 full build를 막는다.
KST_HM="$(TZ=Asia/Seoul date +%H%M)"
KST_DOW="$(TZ=Asia/Seoul date +%u)" # 1=Mon ... 7=Sun
KST_HM_INT=$((10#$KST_HM))
IN_PREOPEN=0
if [[ "$KST_DOW" -ge 1 && "$KST_DOW" -le 5 && "$KST_HM_INT" -ge 800 && "$KST_HM_INT" -lt 900 ]]; then
  IN_PREOPEN=1
fi

BOT_RUNNING=0
if pgrep -f "[b]ot_main[.]py" >/dev/null 2>&1; then
  BOT_RUNNING=1
fi

validate_int() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

validate_float() {
  local value="$1"
  local fallback="$2"
  if [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    echo "$value"
  else
    echo "$fallback"
  fi
}

LOCK_WAIT_SEC="$(validate_int "$LOCK_WAIT_SEC" 0)"
COOLDOWN_SEC="$(validate_int "$COOLDOWN_SEC" 0)"
START_JITTER_SEC="$(validate_int "$START_JITTER_SEC" 0)"
MAX_RETRIES="$(validate_int "$MAX_RETRIES" 3)"
RETRY_DELAY_SEC="$(validate_int "$RETRY_DELAY_SEC" 5)"
ASYNC_WAIT_SEC="$(validate_int "$ASYNC_WAIT_SEC" 0)"
IONICE_CLASS="$(validate_int "$IONICE_CLASS" 2)"
IONICE_LEVEL="$(validate_int "$IONICE_LEVEL" 6)"
NICE_LEVEL="$(validate_int "$NICE_LEVEL" 10)"
IO_DELAY_SEC="$(validate_float "$IO_DELAY_SEC" 0)"

check_recent_success() {
  if [[ "$FORCE_SNAPSHOT" == "1" ]]; then
    return 1
  fi
  if [[ "$COOLDOWN_SEC" -le 0 ]]; then
    return 1
  fi
  if [[ ! -f "$COOLDOWN_STATE_FILE" ]]; then
    return 1
  fi
  local last_ts=0
  if ! last_ts="$(date -r "$COOLDOWN_STATE_FILE" +%s 2>/dev/null || echo 0)"; then
    return 1
  fi
  if [[ "$last_ts" -eq 0 ]]; then
    return 1
  fi
  local now_ts
  now_ts="$(date +%s)"
  local elapsed=$((now_ts - last_ts))
  if [[ "$elapsed" -lt "$COOLDOWN_SEC" ]]; then
    local remaining=$((COOLDOWN_SEC - elapsed))
    echo "[SKIP] snapshot cooldown active for ${PROFILE} (remaining=${remaining}s) target_date=${TARGET_DATE}"
    echo "[HINT] set MONITOR_SNAPSHOT_FORCE=1 to override for this run."
    return 0
  fi
  return 1
}

build_throttled_command() {
  local -n output_cmd="$1"
  output_cmd=(env PYTHONPATH=. MONITOR_SNAPSHOT_FROM_WRAPPER=1 "$VENV_PY" -m src.engine.run_monitor_snapshot --date "$TARGET_DATE" --profile "$PROFILE" --io-delay-sec "$IO_DELAY_SEC" --skip-lock)
  if command -v ionice >/dev/null 2>&1 && [[ "$IONICE_CLASS" -ge 0 ]]; then
    output_cmd=(ionice -c "$IONICE_CLASS" -n "$IONICE_LEVEL" -t "${output_cmd[@]}")
  fi

  if command -v "$NICE_COMMAND" >/dev/null 2>&1; then
    output_cmd=("$NICE_COMMAND" -n "$NICE_LEVEL" "${output_cmd[@]}")
  fi

  if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
    output_cmd=(taskset -c "$CPU_AFFINITY" "${output_cmd[@]}")
  fi
}

print_summary() {
  local output_file="$1"
  if [[ ! -s "$output_file" ]]; then
    echo "[SUMMARY] monitor snapshot completed: output_file_empty"
    return
  fi
  if ! "$VENV_PY" - "$output_file" "$TARGET_DATE" "$PROFILE" <<'PY'
import json
import sys

path, target_date, profile = sys.argv[1:4]
payload = {}
for raw_line in open(path, encoding="utf-8", errors="ignore").read().splitlines():
    raw_line = raw_line.strip()
    if not raw_line.startswith("{") or not raw_line.endswith("}"):
        continue
    try:
        parsed = json.loads(raw_line)
    except json.JSONDecodeError:
        continue
    if isinstance(parsed, dict):
        payload = parsed

status = payload.get("status") or ("skipped" if payload.get("skipped") else "success")
if status == "skipped":
    print(f"[SUMMARY] monitor snapshot skipped: date={target_date} profile={profile} status=skipped reason={payload.get('reason','-')} duration_sec={payload.get('duration_sec','-')}")
    sys.exit(0)

snapshots = payload.get("snapshots")
if not isinstance(snapshots, dict):
    snapshots = {}
snapshot_kinds = [
    key
    for key in snapshots
    if key
    not in {
        "profile",
        "io_delay_sec",
        "trend_max_dates",
        "io_delay_sec_per_stage",
        "stage_metrics",
        "snapshot_manifest",
    }
]
print(
    "[SUMMARY] monitor snapshot complete: "
    f"date={target_date} "
    f"profile={profile} "
    f"status={status} "
    f"kind_count={len(snapshot_kinds)} "
    f"kinds={','.join(snapshot_kinds) if snapshot_kinds else '-'} "
    f"duration_sec={payload.get('duration_sec', '-')}"
)
PY
  then
    return
  fi
}

append_failure_payload() {
  local output_file="$1"
  local exit_code="$2"
  local finished_at
  finished_at="$(date '+%Y-%m-%d %H:%M:%S')"
  if "$VENV_PY" - "$output_file" <<'PY'
import json
import sys

path = sys.argv[1]
payload = {}
for raw_line in open(path, encoding="utf-8", errors="ignore").read().splitlines():
    raw_line = raw_line.strip()
    if not raw_line.startswith("{") or not raw_line.endswith("}"):
        continue
    try:
        parsed = json.loads(raw_line)
    except json.JSONDecodeError:
        continue
    if isinstance(parsed, dict) and parsed.get("status"):
        payload = parsed

if not payload:
    sys.exit(1)
sys.exit(0)
PY
  then
    return
  fi

  "$VENV_PY" - "$output_file" "$TARGET_DATE" "$PROFILE" "$exit_code" "$finished_at" <<'PY'
import json
import sys

path, target_date, profile, exit_code, finished_at = sys.argv[1:6]
payload = {
    "target_date": target_date,
    "status": "failed",
    "profile": profile,
    "io_delay_sec": 0.0,
    "skip_lock": False,
    "started_at": finished_at,
    "finished_at": finished_at,
    "duration_sec": 0.0,
    "error_kind": "TimeoutOrExternalStop",
    "error": f"snapshot command exited with code={exit_code}",
    "snapshots": {},
}
with open(path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
PY
}

append_skip_payload() {
  local output_file="$1"
  local reason="$2"
  local finished_at
  finished_at="$(date '+%Y-%m-%d %H:%M:%S')"
  "$VENV_PY" - "$output_file" "$TARGET_DATE" "$PROFILE" "$reason" "$finished_at" <<'PY'
import json
import sys

path, target_date, profile, reason, finished_at = sys.argv[1:6]
payload = {
    "target_date": target_date,
    "status": "skipped",
    "skipped": True,
    "reason": reason,
    "profile": profile,
    "started_at": finished_at,
    "finished_at": finished_at,
    "duration_sec": 0.0,
    "snapshots": {},
}
with open(path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
PY
}

is_async_worker_running() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local existing_pid
  existing_pid="$(tr -cd '0-9' < "$pid_file" | tr -d '\n' | tr -d '\r' || true)"
  if [[ -z "$existing_pid" ]]; then
    rm -f "$pid_file"
    return 1
  fi

  if kill -0 "$existing_pid" >/dev/null 2>&1; then
    echo "[INFO] monitor snapshot async worker already running"
    print_standard_async_response "already_running" "$existing_pid" "${MONITOR_SNAPSHOT_ASYNC_RESULT_HINT:-}"
    return 0
  fi

  rm -f "$pid_file"
  return 1
}

print_standard_async_response() {
  local status="$1"
  local worker_pid="${2:-}"
  local output_file="${3:-}"

  echo "[INFO] monitor snapshot async response status=${status} date=${TARGET_DATE} profile=${PROFILE} worker_pid=${worker_pid:-"-"} output_file=${output_file:-"-"}"
  echo "[HINT] 작업은 백그라운드에서 실행되며 완료 상태는 completion artifact와 cron log로 확인합니다."
  if [[ "$status" == "dispatched" ]]; then
    echo "[HINT] completion artifact가 success/failed/skipped로 갱신된 뒤 결과를 기반으로 다음 지시를 이어 주세요."
  else
    echo "[HINT] 기존 completion artifact 또는 worker pid를 확인하기 전까지 동일 작업은 중복 실행하지 마세요."
  fi
  write_completion_artifact "$status" "${output_file:-}" "${worker_pid:-}"
}

wait_for_async_completion() {
  local worker_pid="$1"
  local output_file="$2"
  local waited=0
  local sleep_sec=2
  local artifact_status=""

  if [[ "$ASYNC_WAIT_SEC" -le 0 ]]; then
    return 0
  fi

  echo "[INFO] waiting for monitor snapshot async completion pid=${worker_pid} timeout_sec=${ASYNC_WAIT_SEC}"
  while kill -0 "$worker_pid" >/dev/null 2>&1; do
    if [[ "$waited" -ge "$ASYNC_WAIT_SEC" ]]; then
      write_completion_artifact "failed" "$output_file" "$worker_pid"
      echo "[ERROR] monitor snapshot async worker timed out after ${ASYNC_WAIT_SEC}s pid=${worker_pid}"
      return 124
    fi
    sleep "$sleep_sec"
    waited=$((waited + sleep_sec))
  done

  if ! wait "$worker_pid"; then
    local worker_status=$?
    write_completion_artifact "" "$output_file" "$worker_pid"
    echo "[ERROR] monitor snapshot async worker failed status=${worker_status} pid=${worker_pid}"
    return "$worker_status"
  fi

  write_completion_artifact "" "$output_file" "$worker_pid"
  artifact_status="$("$VENV_PY" - "$COMPLETION_ARTIFACT_FILE" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("unknown")
else:
    print(str(payload.get("status") or "unknown").lower())
PY
)"
  case "$artifact_status" in
    success|skipped)
      echo "[INFO] monitor snapshot async completed status=${artifact_status} pid=${worker_pid}"
      return 0
      ;;
    *)
      echo "[ERROR] monitor snapshot async completed with non-success status=${artifact_status} pid=${worker_pid}"
      return 1
      ;;
  esac
}

write_completion_artifact() {
  local status="$1"
  local output_file="${2:-}"
  local worker_pid="${3:-}"
  local result_file=""
  if [[ -n "$output_file" && "$output_file" != "-" ]]; then
    result_file="$output_file"
  elif [[ -f "$ASYNC_RESULT_HINT" ]]; then
    result_file="$(cat "$ASYNC_RESULT_HINT" 2>/dev/null || true)"
  fi

  env PYTHONPATH=. "$VENV_PY" - "$TARGET_DATE" "$PROFILE" "$COMPLETION_ARTIFACT_FILE" "$result_file" "$status" "$worker_pid" "$LOG_FILE" <<'PY'
from pathlib import Path
import sys

from src.engine.monitor_snapshot_runtime import normalize_result_payload, write_completion_artifact

target_date, profile, artifact_file, result_file, status, worker_pid, log_file = sys.argv[1:8]
result_text = ""
if result_file:
    result_path = Path(result_file)
    if result_path.exists():
        result_text = result_path.read_text(encoding="utf-8", errors="replace")
normalized = normalize_result_payload(
    target_date=target_date,
    profile=profile,
    result_file=result_file or None,
    output_text=result_text,
    status_override=status or None,
    worker_pid=worker_pid or None,
    output_file=result_file or None,
    log_file=log_file or None,
)
write_completion_artifact(Path(artifact_file), normalized)
PY
}

run_snapshot_once() {
  local output_file="$1"
  local attempt=1
  local jitter_wait=0
  local attempt_output
  local overall_status=0
  local snapshot_skipped=0
  local non_retryable_resource_exit=0

  : > "$output_file"

  for attempt in $(seq 1 "$MAX_RETRIES"); do
    SNAPSHOT_STATUS=0
    snapshot_skipped=0
    attempt_output="${output_file}.attempt_${attempt}"
    : > "$attempt_output"

    {
      if check_recent_success; then
        append_skip_payload "$attempt_output" "cooldown_active"
        snapshot_skipped=1
      fi

      if [[ "$snapshot_skipped" -ne 1 ]]; then
        flock -w "$LOCK_WAIT_SEC" 9 || {
          echo "[SKIP] run_snapshot already running after wait=${LOCK_WAIT_SEC}s (lock: $LOCK_FILE)"
          append_skip_payload "$attempt_output" "lock_busy"
          snapshot_skipped=1
        }
      fi

      if [[ "$snapshot_skipped" -ne 1 && "$IN_PREOPEN" -eq 1 && "$BOT_RUNNING" -eq 1 && "$ALLOW_PREOPEN_WITH_BOT" != "1" ]]; then
        echo "[SKIP] PREOPEN full build blocked while bot_main is running (08:00~09:00 KST)."
        echo "[HINT] set ALLOW_PREOPEN_FULL_BUILD_WITH_BOT=1 to override for emergency."
        append_skip_payload "$attempt_output" "preopen_blocked"
        snapshot_skipped=1
      fi

      if [[ "$snapshot_skipped" -ne 1 && "$PROFILE" == "full" && "$BOT_RUNNING" -eq 1 && -f "$MANIFEST_PATH" && "$ALLOW_EXISTING_FULL_BUILD_WITH_BOT" != "1" ]]; then
        echo "[SKIP] existing full snapshot manifest detected while bot_main is running."
        echo "[HINT] manifest=$MANIFEST_PATH"
        echo "[HINT] set ALLOW_EXISTING_FULL_BUILD_WITH_BOT=1 to force duplicate full rebuild."
        append_skip_payload "$attempt_output" "existing_manifest"
        snapshot_skipped=1
      fi

      if [[ "$snapshot_skipped" -ne 1 && "$START_JITTER_SEC" -gt 0 ]]; then
        jitter_wait=$((RANDOM % (START_JITTER_SEC + 1)))
        echo "[INFO] run_snapshot_once jitter wait=${jitter_wait}s (max=${START_JITTER_SEC}s) attempt=${attempt}/${MAX_RETRIES}"
        sleep "$jitter_wait"
      fi

      if [[ "$snapshot_skipped" -ne 1 ]]; then
        SNAPSHOT_CMD=()
        build_throttled_command SNAPSHOT_CMD
        echo "[INFO] run_snapshot_once start attempt=${attempt}/${MAX_RETRIES} date=$TARGET_DATE preopen=$IN_PREOPEN bot_running=$BOT_RUNNING profile=$PROFILE io_delay_sec=$IO_DELAY_SEC notify_admin=$NOTIFY_ADMIN lock_wait_sec=$LOCK_WAIT_SEC cooldown_sec=$COOLDOWN_SEC force=$FORCE_SNAPSHOT"

        set +e
        timeout "$TIMEOUT_SEC" "${SNAPSHOT_CMD[@]}" > "$attempt_output" 2>&1
        SNAPSHOT_STATUS=$?
        set -e

        if [[ "$SNAPSHOT_STATUS" -ne 0 ]]; then
          append_failure_payload "$attempt_output" "$SNAPSHOT_STATUS"
        fi
      fi
    } 9>"$LOCK_FILE" >> "$LOG_FILE" 2>&1

    grep -E '"event"[[:space:]]*:[[:space:]]*"monitor_snapshot_stage_(start|complete)"' "$attempt_output" >> "$LOG_FILE" || true
    non_retryable_resource_exit=0
    if [[ "$SNAPSHOT_STATUS" -ne 0 ]]; then
      case "$SNAPSHOT_STATUS" in
        124|130|137|143) non_retryable_resource_exit=1 ;;
      esac
      if grep -Eq '"error_kind"[[:space:]]*:[[:space:]]*"MemoryError"' "$attempt_output"; then
        non_retryable_resource_exit=1
      fi
    fi
    if [[ "$KEEP_OUTPUT_FILE" == "1" ]]; then
      cat "$attempt_output" >> "$output_file"
    else
      cat "$attempt_output" >> "$output_file"
      rm -f "$attempt_output"
    fi
    if [[ "$SNAPSHOT_STATUS" -ne 0 ]]; then
      overall_status=$SNAPSHOT_STATUS
      # Retrying the same multi-gigabyte workload immediately after timeout,
      # OOM/SIGKILL, interrupt, or SIGTERM compounds host pressure and can
      # starve the live bot.  Preserve the failed completion artifact and let
      # the next scheduled/operator run start only after the cause is fixed.
      if [[ "$attempt" -lt "$MAX_RETRIES" && "$non_retryable_resource_exit" -ne 1 ]]; then
        echo "[WARN] run_snapshot_once failed attempt=${attempt}/${MAX_RETRIES}. Retrying after ${RETRY_DELAY_SEC}s"
        sleep "$RETRY_DELAY_SEC"
        continue
      fi

      if [[ "$NOTIFY_ONLY" == "1" || "$SNAPSHOT_STATUS" -ne 0 ]]; then
        print_summary "$output_file"
      else
        cat "$output_file"
      fi
      write_completion_artifact "" "$output_file" "$$"
      if [[ "$non_retryable_resource_exit" -eq 1 ]]; then
        echo "[ERROR] run_snapshot_once stopped without retry after resource/external exit status=$SNAPSHOT_STATUS"
      else
        echo "[ERROR] run_snapshot_once failed after ${attempt} attempts status=$SNAPSHOT_STATUS"
      fi
      echo "[ERROR] check log: $output_file"
      echo "[INFO] run_snapshot_once done date=$TARGET_DATE"
      return "$SNAPSHOT_STATUS"
    fi

    print_summary "$output_file"
    if [[ "$SNAPSHOT_STATUS" -eq 0 && "$snapshot_skipped" -ne 1 ]]; then
      touch "$COOLDOWN_STATE_FILE"
    fi
    write_completion_artifact "" "$output_file" "$$"
    if [[ "$KEEP_OUTPUT_FILE" != "1" ]]; then
      rm -f "$output_file"
    fi
    echo "[INFO] run_snapshot_once done date=$TARGET_DATE"
    return 0
  done

  return "$overall_status"
}

if [[ "$WORKER_MODE" == "1" ]]; then
  RUN_OUTPUT_FILE="${MONITOR_SNAPSHOT_OUTPUT_FILE:-$(mktemp "$PROJECT_DIR/tmp/run_snapshot_worker_${SAFE_PROFILE}_${TARGET_DATE}.XXXXXX")}"
  KEEP_OUTPUT_FILE="${MONITOR_SNAPSHOT_KEEP_OUTPUT_FILE:-1}"
  if [[ -n "${MONITOR_SNAPSHOT_ASYNC_PID_FILE:-}" ]]; then
    echo "$$" > "$MONITOR_SNAPSHOT_ASYNC_PID_FILE"
    trap 'rm -f "$MONITOR_SNAPSHOT_ASYNC_PID_FILE"' EXIT
  fi
  if [[ -n "${MONITOR_SNAPSHOT_ASYNC_RESULT_HINT:-}" ]]; then
    echo "$RUN_OUTPUT_FILE" > "$MONITOR_SNAPSHOT_ASYNC_RESULT_HINT"
  fi
  set +e
  run_snapshot_once "$RUN_OUTPUT_FILE"
  WORKER_STATUS=$?
  set -e
  if [[ -f "$RUN_OUTPUT_FILE" ]]; then
    write_completion_artifact "" "$RUN_OUTPUT_FILE" "$$"
  else
    write_completion_artifact "unknown" "" "$$"
  fi
  exit $WORKER_STATUS
fi

if [[ "$ASYNC_MODE" == "1" ]]; then
  if is_async_worker_running "$ASYNC_PID_FILE"; then
    exit 0
  fi

  RUN_OUTPUT_FILE="$(mktemp "$PROJECT_DIR/tmp/run_snapshot_${SAFE_PROFILE}_${TARGET_DATE}_async.XXXXXX")"
  echo "$RUN_OUTPUT_FILE" > "$ASYNC_RESULT_HINT"
  KEEP_OUTPUT_FILE=1

  MONITOR_SNAPSHOT_WORKER=1 \
    MONITOR_SNAPSHOT_ASYNC=0 \
    MONITOR_SNAPSHOT_OUTPUT_FILE="$RUN_OUTPUT_FILE" \
    MONITOR_SNAPSHOT_KEEP_OUTPUT_FILE=1 \
    MONITOR_SNAPSHOT_ASYNC_PID_FILE="$ASYNC_PID_FILE" \
    MONITOR_SNAPSHOT_ASYNC_RESULT_HINT="$ASYNC_RESULT_HINT" \
    nohup "$0" "$TARGET_DATE" >/dev/null 2>&1 &
  JOB_PID=$!
  echo "$JOB_PID" > "$ASYNC_PID_FILE"

  if ! kill -0 "$JOB_PID" >/dev/null 2>&1; then
    rm -f "$ASYNC_PID_FILE"
    echo "[ERROR] snapshot async dispatch failed to start"
    exit 1
  fi

  print_standard_async_response "dispatched" "$JOB_PID" "$RUN_OUTPUT_FILE"
  wait_for_async_completion "$JOB_PID" "$RUN_OUTPUT_FILE"
  exit 0
fi

RUN_OUTPUT_FILE="$(mktemp "$PROJECT_DIR/tmp/run_monitor_snapshot.XXXXXX")"
set +e
run_snapshot_once "$RUN_OUTPUT_FILE"
RUN_STATUS=$?
set -e
if [[ -f "$RUN_OUTPUT_FILE" ]]; then
  write_completion_artifact "" "$RUN_OUTPUT_FILE" "$$"
fi
exit $RUN_STATUS
