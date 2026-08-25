#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
KORSTOCKSCAN_CODE_ROOT="${KORSTOCKSCAN_CODE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_DIR="$PROJECT_DIR/logs"
RETENTION_DAYS="${1:-${LOG_ROTATION_ARCHIVE_RETENTION_DAYS:-30}}"
TARGET_DATE="${TARGET_DATE:-$(TZ=Asia/Seoul date +%F)}"
ACTIVE_LOG_MAX_BYTES="${LOG_ROTATION_ACTIVE_MAX_BYTES:-${KORSTOCKSCAN_LOG_ROTATE_MAX_BYTES:-20971520}}"
ACTIVE_LOG_BACKUP_COUNT="${LOG_ROTATION_BACKUP_COUNT:-5}"
ACTIVE_LOG_COMPRESS_MIN_INDEX="${LOG_ROTATION_COMPRESS_MIN_INDEX:-2}"
ARCHIVE_COMPRESSION_QUIET_SECONDS="${LOG_ROTATION_ARCHIVE_QUIET_SECONDS:-300}"
WRITER_DEFER_FAILURE_THRESHOLD="${LOG_ROTATION_WRITER_DEFER_FAILURE_THRESHOLD:-3}"
WRITER_DEFER_STATE_FILE="${LOG_ROTATION_WRITER_DEFER_STATE_FILE:-$PROJECT_DIR/tmp/log_rotation_cleanup_writer_defer_state.json}"
ACTIVE_LOG_RETENTION_DAYS="${LOG_ROTATION_ACTIVE_RETENTION_DAYS:-14}"
SYSTEM_METRIC_RETENTION_DAYS="${SYSTEM_METRIC_RETENTION_DAYS:-3}"
DATA_MAINTENANCE_ENABLED="${DATA_MAINTENANCE_ENABLED:-true}"
TMP_MAINTENANCE_RETENTION_DAYS="${TMP_MAINTENANCE_RETENTION_DAYS:-2}"
REFRACTOR_DRY_RUN_RETENTION_DAYS="${REFRACTOR_DRY_RUN_RETENTION_DAYS:-7}"
RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS="${RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS:-7}"
MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED="${MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED:-true}"
MICRO_REVERSION_STORAGE_PURGE_ENABLED="${MICRO_REVERSION_STORAGE_PURGE_ENABLED:-false}"
MICRO_REVERSION_STORAGE_ROOT="${MICRO_REVERSION_STORAGE_ROOT:-$PROJECT_DIR/data/observations/scalp_micro_reversion_forward}"
MICRO_REVERSION_STORAGE_NICE_LEVEL="${MICRO_REVERSION_STORAGE_NICE_LEVEL:-15}"
MICRO_REVERSION_REPORT_ARTIFACT_RETENTION_DAYS="${MICRO_REVERSION_REPORT_ARTIFACT_RETENTION_DAYS:-90}"
MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES="${MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES:-5368709120}"
MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES="${MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES:-1073741824}"
MICRO_REVERSION_STORAGE_CAPACITY_STATUS_PATH="${MICRO_REVERSION_STORAGE_CAPACITY_STATUS_PATH:-$PROJECT_DIR/data/report/micro_reversion_storage_capacity/micro_reversion_storage_capacity_${TARGET_DATE}.json}"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

if [[ ! "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] retention days must be integer: $RETENTION_DAYS"
  exit 2
fi
if [[ ! "$ACTIVE_LOG_MAX_BYTES" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] active log max bytes must be integer: $ACTIVE_LOG_MAX_BYTES"
  exit 2
fi
if [[ ! "$ACTIVE_LOG_BACKUP_COUNT" =~ ^[0-9]+$ || "$ACTIVE_LOG_BACKUP_COUNT" -lt 1 ]]; then
  echo "[LOG_CLEANUP_ERROR] active log backup count must be positive integer: $ACTIVE_LOG_BACKUP_COUNT"
  exit 2
fi
if [[ ! "$ACTIVE_LOG_COMPRESS_MIN_INDEX" =~ ^[0-9]+$ || "$ACTIVE_LOG_COMPRESS_MIN_INDEX" -lt 2 ]]; then
  echo "[LOG_CLEANUP_ERROR] active log compress min index must be integer >= 2: $ACTIVE_LOG_COMPRESS_MIN_INDEX"
  exit 2
fi
if [[ ! "$ARCHIVE_COMPRESSION_QUIET_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] archive compression quiet seconds must be integer: $ARCHIVE_COMPRESSION_QUIET_SECONDS"
  exit 2
fi
if [[ ! "$WRITER_DEFER_FAILURE_THRESHOLD" =~ ^[0-9]+$ || "$WRITER_DEFER_FAILURE_THRESHOLD" -lt 1 ]]; then
  echo "[LOG_CLEANUP_ERROR] writer defer failure threshold must be positive integer: $WRITER_DEFER_FAILURE_THRESHOLD"
  exit 2
fi
if [[ ! "$ACTIVE_LOG_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] active log retention days must be integer: $ACTIVE_LOG_RETENTION_DAYS"
  exit 2
fi
if [[ ! "$SYSTEM_METRIC_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] system metric retention days must be integer: $SYSTEM_METRIC_RETENTION_DAYS"
  exit 2
fi
if [[ ! "$TMP_MAINTENANCE_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] tmp maintenance retention days must be integer: $TMP_MAINTENANCE_RETENTION_DAYS"
  exit 2
fi
if [[ ! "$REFRACTOR_DRY_RUN_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] refactor dry-run retention days must be integer: $REFRACTOR_DRY_RUN_RETENTION_DAYS"
  exit 2
fi
if [[ ! "$RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] raw_row_exclusion backup retention days must be integer: $RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS"
  exit 2
fi
if [[ ! "$MICRO_REVERSION_STORAGE_NICE_LEVEL" =~ ^([0-9]|1[0-9])$ ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion storage nice level must be 0..19: $MICRO_REVERSION_STORAGE_NICE_LEVEL"
  exit 2
fi
if [[ ! "$MICRO_REVERSION_REPORT_ARTIFACT_RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion report artifact retention days must be positive integer: $MICRO_REVERSION_REPORT_ARTIFACT_RETENTION_DAYS"
  exit 2
fi
if [[ ! "$MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES" =~ ^[0-9]+$ || ! "$MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion capacity watermarks must be non-negative integers"
  exit 2
fi
if [[ "$MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES" -lt "$MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES" ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion low disk watermark must not be below critical watermark"
  exit 2
fi
if [[ "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" != "true" && "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" != "false" ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion storage purge enabled must be true or false: $MICRO_REVERSION_STORAGE_PURGE_ENABLED"
  exit 2
fi
if [[ "$MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED" != "true" && "$MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED" != "false" ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion storage maintenance enabled must be true or false: $MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED"
  exit 2
fi

mkdir -p "$LOG_DIR" "$PROJECT_DIR/tmp"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
cleanup_run_id="${TARGET_DATE}:$$:$(date +%s%N)"
echo "[START] log_rotation_cleanup target_date=${TARGET_DATE} archive_retention_days=${RETENTION_DAYS} active_log_retention_days=${ACTIVE_LOG_RETENTION_DAYS} active_log_compress_min_index=${ACTIVE_LOG_COMPRESS_MIN_INDEX} archive_compression_quiet_seconds=${ARCHIVE_COMPRESSION_QUIET_SECONDS} writer_defer_failure_threshold=${WRITER_DEFER_FAILURE_THRESHOLD} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} raw_row_exclusion_backup_retention_days=${RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS} active_log_max_bytes=${ACTIVE_LOG_MAX_BYTES} active_log_backup_count=${ACTIVE_LOG_BACKUP_COUNT} active_rotation_status=disabled_pending_writer_owner data_maintenance_enabled=${DATA_MAINTENANCE_ENABLED} micro_reversion_storage_maintenance_enabled=${MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED} micro_reversion_storage_purge_enabled=${MICRO_REVERSION_STORAGE_PURGE_ENABLED} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] log_rotation_cleanup target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

writer_defer_keys_file="$(mktemp "$PROJECT_DIR/tmp/.log_rotation_writer_defer_keys.XXXXXX")"
writer_defer_result_file="$(mktemp "$PROJECT_DIR/tmp/.log_rotation_writer_defer_result.XXXXXX")"
trap 'rm -f "$writer_defer_keys_file" "$writer_defer_result_file"' EXIT

archive_log_find_args=(
  "$LOG_DIR" -maxdepth 1 -type f
  \( -name '*.log.[0-9]*' -o -name '*.log.generation_*.gz' -o -name '*.log.before_*' \)
)
before_count=0
before_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"
system_metric_before_size=0
system_metric_after_size=0
system_metric_retained=0
system_metric_pruned=0
system_metric_invalid=0
tmp_deleted_count=0
cache_deleted_count=0
sentinel_compressed_count=0
snapshot_compressed_count=0
sentinel_verified_existing_source_preserved_count=0
snapshot_verified_existing_source_preserved_count=0
raw_row_exclusion_deleted_count=0
raw_row_exclusion_backup_deleted_count=0
raw_row_exclusion_delete_deferred_count=0
raw_row_exclusion_backup_delete_deferred_count=0
raw_row_exclusion_delete_deferred_bytes=0
raw_row_exclusion_backup_delete_deferred_bytes=0
micro_reversion_storage_action_count=0
micro_reversion_storage_compressed_count=0
micro_reversion_storage_purged_count=0
micro_reversion_storage_purge_partial_count=0
micro_reversion_storage_source_bytes=0
micro_reversion_storage_status="disabled"
micro_reversion_storage_purge_enabled="$MICRO_REVERSION_STORAGE_PURGE_ENABLED"
micro_reversion_storage_purge_status="maintenance_disabled"
micro_reversion_storage_purge_candidate_count=0
micro_reversion_storage_purge_candidate_bytes=0
micro_reversion_storage_failure_count=0
micro_reversion_storage_partition_failure_count=0
micro_reversion_storage_failed_candidate_count=0
micro_reversion_storage_failed_candidate_bytes=0
micro_reversion_storage_recovery_required_count=0
micro_reversion_report_artifact_action_count=0
micro_reversion_report_artifact_compressed_count=0
micro_reversion_report_artifact_source_bytes=0
micro_reversion_report_artifact_failure_count=0
micro_reversion_report_artifact_retention_candidate_count=0
micro_reversion_report_artifact_retention_candidate_bytes=0
micro_reversion_artifact_set_count=0
micro_reversion_artifact_set_terminal_count=0
micro_reversion_artifact_set_superseded_count=0
micro_reversion_artifact_set_incomplete_count=0
micro_reversion_artifact_set_stale_workorder_count=0
micro_reversion_artifact_set_stale_workorder_bytes=0
micro_reversion_immutable_source_artifact_count=0
micro_reversion_immutable_source_artifact_bytes=0
micro_reversion_checkpoint_journal_count=0
micro_reversion_checkpoint_terminal_count=0
micro_reversion_checkpoint_superseded_count=0
micro_reversion_checkpoint_incomplete_count=0
micro_reversion_checkpoint_stale_workorder_count=0
micro_reversion_checkpoint_stale_workorder_bytes=0
micro_reversion_provider_budget_ledger_count=0
micro_reversion_provider_budget_ledger_bytes=0
micro_reversion_provider_budget_retention_candidate_count=0
micro_reversion_provider_budget_retention_candidate_bytes=0
micro_reversion_exact_ai_artifact_count=0
micro_reversion_exact_ai_artifact_bytes=0
micro_reversion_exact_ai_compressed_count=0
micro_reversion_exact_ai_failure_count=0
micro_reversion_exact_ai_retention_candidate_count=0
micro_reversion_exact_ai_retention_candidate_bytes=0
micro_reversion_daily_owner_partition_count=0
micro_reversion_daily_owner_file_count=0
micro_reversion_daily_owner_bytes=0
micro_reversion_daily_owner_exact_date_file_count=0
micro_reversion_daily_owner_exact_date_bytes=0
micro_reversion_daily_owner_retention_candidate_count=0
micro_reversion_daily_owner_retention_candidate_bytes=0
micro_reversion_daily_owner_failure_count=0
micro_reversion_daily_owner_status="not_run"
micro_reversion_daily_owner_archive_offload_status="not_run"
micro_reversion_storage_disk_free_bytes_before=0
micro_reversion_storage_disk_free_bytes_after=0
micro_reversion_storage_disk_free_bytes_delta=0
micro_reversion_storage_retained_physical_bytes_after=0
micro_reversion_storage_compressed_target_bytes=0
micro_reversion_storage_bytes_reclaimed=0
micro_reversion_storage_capacity_state="not_run"
micro_reversion_storage_capacity_warning="false"
micro_reversion_storage_capacity_failure="false"
micro_reversion_storage_capacity_workorder_required="false"
micro_reversion_storage_capacity_status_written="false"
micro_reversion_storage_capacity_status_write_failures=0
compressed_archive_count=0
archive_compression_finalized_count=0
archive_verified_existing_source_preserved_count=0
archive_collision_reconciled_count=0
archive_generation_compressed_count=0
archive_generation_verified_count=0
archive_compression_failure_count=0
archive_compression_source_preserved_count=0
archive_writer_active_deferred_count=0
archive_writer_active_deferred_bytes=0
archive_retention_protected_count=0
archive_pruned_to_backup_limit_count=0
active_rotation_status="disabled_pending_writer_owner"
active_rotation_deferred_count=0
writer_defer_tracked_count=0
writer_defer_escalated_count=0
writer_defer_max_consecutive=0
writer_defer_state_failure_count=0
active_log_retention_failure_count=0
archive_retention_failure_count=0
active_log_retention_deferred_count=0
active_log_retention_deferred_bytes=0
archive_retention_deferred_count=0
archive_retention_deferred_bytes=0
archive_source_unlink_deferred_count=0
archive_source_unlink_deferred_bytes=0
data_source_unlink_deferred_count=0
data_source_unlink_deferred_bytes=0
compression_verify_failure_count=0
data_maintenance_failure_count=0
find_enumeration_failure_count=0
compression_failure_reason="not_run"
compression_action="not_run"
declare -A archive_retention_protected_paths=()
declare -A archive_retention_protection_reasons=()

collect_find_results() {
  local lane="$1"
  local output_path="$2"
  shift 2
  if ! find "$@" -print0 >"$output_path"; then
    find_enumeration_failure_count=$((find_enumeration_failure_count + 1))
    : >"$output_path"
    echo "[CLEANUP_ENUMERATION_FAIL] lane=${lane} cleanup_will_continue=true"
    return 1
  fi
  if ! sort -z -o "$output_path" "$output_path"; then
    find_enumeration_failure_count=$((find_enumeration_failure_count + 1))
    : >"$output_path"
    echo "[CLEANUP_ENUMERATION_FAIL] lane=${lane}_sort cleanup_will_continue=true"
    return 1
  fi
  return 0
}

register_writer_defer() {
  local lane="$1"
  local path="$2"
  local reason="$3"
  local observed_slot identity
  observed_slot="$(basename "$path")"
  identity="$observed_slot"
  if [[ "$lane" == "numeric_archive" && "$observed_slot" =~ ^(.+\.log)\.[0-9]+$ ]]; then
    identity="${BASH_REMATCH[1]}"
  fi
  printf '%s\t%s\t%s\t%s\n' "$lane" "$identity" "$observed_slot" "$reason" >>"$writer_defer_keys_file"
}

compression_reason_is_writer_active() {
  case "$1" in
    source_in_use|source_not_quiet|source_changed_during_compression|source_in_use_after_compression|source_changed_after_gzip_publish|source_in_use_after_gzip_publish|source_changed_or_open_during_existing_verify|source_changed_or_open_during_generation_verify)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

update_writer_defer_state() {
  if ! "$PYTHON_BIN" - "$WRITER_DEFER_STATE_FILE" "$writer_defer_keys_file" "$writer_defer_result_file" "$WRITER_DEFER_FAILURE_THRESHOLD" "$TARGET_DATE" "$cleanup_run_id" "$find_enumeration_failure_count" <<'PY'
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

state_path = Path(sys.argv[1])
keys_path = Path(sys.argv[2])
result_path = Path(sys.argv[3])
threshold = int(sys.argv[4])
target_date = sys.argv[5]
run_id = sys.argv[6]
observation_complete = int(sys.argv[7]) == 0

if state_path.is_symlink():
    raise SystemExit("writer defer state path must not be a symlink")

previous = {}
if state_path.exists():
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(payload.get("entries"), dict):
            previous = payload["entries"]
        else:
            raise ValueError("writer defer state entries must be an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"writer defer state unreadable: {type(exc).__name__}") from exc

current = {}
for raw in keys_path.read_text(encoding="utf-8", errors="replace").splitlines():
    parts = raw.split("\t", 3)
    if len(parts) != 4:
        continue
    lane, identity, observed_slot, reason = parts
    current[f"{lane}:{identity}"] = {
        "lane": lane,
        "identity": identity,
        "observed_slot": observed_slot,
        "reason": reason,
    }

entries = {}
for key, item in sorted(current.items()):
    old = previous.get(key) if isinstance(previous.get(key), dict) else {}
    old_count = int(old.get("consecutive_count") or 0)
    count = old_count if old.get("last_run_id") == run_id else old_count + 1
    entries[key] = {
        **item,
        "consecutive_count": count,
        "first_seen_target_date": old.get("first_seen_target_date") or target_date,
        "last_seen_target_date": target_date,
        "last_run_id": run_id,
    }
if not observation_complete:
    for key, old in previous.items():
        if key not in entries and isinstance(old, dict):
            entries[key] = old

escalated = [
    {"key": key, **item}
    for key, item in entries.items()
    if int(item["consecutive_count"]) >= threshold
]
state_payload = {
    "schema_version": 1,
    "target_date": target_date,
    "last_run_id": run_id,
    "failure_threshold": threshold,
    "observation_complete": observation_complete,
    "entries": entries,
}
state_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = state_path.with_name(f".{state_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
try:
    tmp_path.write_text(json.dumps(state_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, state_path)
finally:
    tmp_path.unlink(missing_ok=True)

result_payload = {
    "tracked_count": len(entries),
    "escalated_count": len(escalated),
    "max_consecutive": max((int(item["consecutive_count"]) for item in entries.values()), default=0),
    "escalated": escalated,
}
result_path.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")
PY
  then
    writer_defer_state_failure_count=1
    echo "[WRITER_DEFER_STATE_FAIL] state_file=${WRITER_DEFER_STATE_FILE}"
    return 1
  fi

  read -r writer_defer_tracked_count writer_defer_escalated_count writer_defer_max_consecutive < <(
    "$PYTHON_BIN" - "$writer_defer_result_file" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload["tracked_count"], payload["escalated_count"], payload["max_consecutive"])
PY
  )
  "$PYTHON_BIN" - "$writer_defer_result_file" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for item in payload.get("escalated", []):
    print(
        "[WRITER_DEFER_ESCALATED] "
        f"lane={item['lane']} identity={item['identity']} "
        f"observed_slot={item['observed_slot']} reason={item['reason']} "
        f"consecutive_count={item['consecutive_count']}"
    )
PY
}

run_with_safe_lock() {
  local lock_path="$1"
  local lock_mode="$2"
  shift 2
  "$PYTHON_BIN" -c '
import fcntl
import os
import stat
import sys

lock_path = os.path.abspath(sys.argv[1])
lock_mode = sys.argv[2]
command = sys.argv[3:]
if lock_mode not in {"blocking", "nonblocking"} or not command:
    raise SystemExit(64)

parent_path, lock_name = os.path.split(lock_path)
directory_fd = -1
try:
    directory_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    for component in (part for part in parent_path.split(os.sep) if part):
        next_fd = os.open(
            component,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        os.close(directory_fd)
        directory_fd = next_fd
    lock_fd = os.open(
        lock_name,
        os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
        0o640,
        dir_fd=directory_fd,
    )
except OSError as exc:
    print(f"unsafe cleanup lock path:{lock_path}:{type(exc).__name__}", file=sys.stderr)
    raise SystemExit(76) from exc
finally:
    if directory_fd >= 0:
        os.close(directory_fd)

if not stat.S_ISREG(os.fstat(lock_fd).st_mode):
    os.close(lock_fd)
    raise SystemExit(76)
try:
    fcntl.flock(
        lock_fd,
        fcntl.LOCK_EX | (fcntl.LOCK_NB if lock_mode == "nonblocking" else 0),
    )
except BlockingIOError:
    os.close(lock_fd)
    raise SystemExit(75)
os.set_inheritable(lock_fd, True)
os.execvp(command[0], command)
' "$lock_path" "$lock_mode" "$@"
}

initial_archive_find_path="$(mktemp "$LOG_DIR/.cleanup_find_initial.XXXXXX")"
if collect_find_results "archive_initial_census" "$initial_archive_find_path" "${archive_log_find_args[@]}"; then
  before_count="$(tr -cd '\0' <"$initial_archive_find_path" | wc -c | tr -d ' ')"
fi
rm -f "$initial_archive_find_path"

run_micro_reversion_storage_maintenance() {
  if [[ "$MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED" != "true" ]]; then
    micro_reversion_storage_status="disabled"
    micro_reversion_storage_purge_status="maintenance_disabled"
    return 0
  fi
  micro_reversion_storage_purge_status="pending"

  mkdir -p "$PROJECT_DIR/tmp"
  local result_path lock_path lock_rc
  result_path="$(mktemp "$PROJECT_DIR/tmp/micro_reversion_storage_maintenance.XXXXXX.json")"
  lock_path="$PROJECT_DIR/tmp/micro_reversion_storage_maintenance.lock"
  lock_rc=0
  (
    cd "$KORSTOCKSCAN_CODE_ROOT"
    export PYTHONPATH="$KORSTOCKSCAN_CODE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
    maintenance_command=(
      "$PYTHON_BIN"
      -m src.engine.scalping.micro_reversion.storage_maintenance
      --root "$MICRO_REVERSION_STORAGE_ROOT"
      --as-of-date "$TARGET_DATE"
      --apply
      --report-artifact-root "$PROJECT_DIR/data/report/ai_micro_reversion_materialized_replay_requests"
      --report-artifact-root "$PROJECT_DIR/data/report/micro_reversion_ai_quality_bridge"
      --report-artifact-root "$PROJECT_DIR/data/report/main_ai_quality_r0_r3"
      --report-artifact-root "$PROJECT_DIR/data/report/micro_reversion_storage_capacity"
      --report-artifact-root "$PROJECT_DIR/data/report/ai_prompt_paired_replay"
      --report-artifact-root "$PROJECT_DIR/data/report/micro_reversion_economic_reference"
      --report-artifact-root "$PROJECT_DIR/data/offline_provider_budget"
      --exact-ai-artifact-root "$PROJECT_DIR/data/ai_decision_payloads"
      --exact-ai-artifact-root "$PROJECT_DIR/data/ai_decision_trace"
      --exact-ai-artifact-root "$PROJECT_DIR/data/ai_decision_outcomes"
      --exact-ai-artifact-root "$PROJECT_DIR/data/ai_decision_requests"
      --exact-ai-artifact-root "$PROJECT_DIR/data/ai_decision_prompts"
      --exact-ai-artifact-root "$PROJECT_DIR/data/report/ai_decision_outcome_labels"
      --micro-reversion-daily-owner-root "$PROJECT_DIR/data/policy/micro_reversion/daily"
      --report-artifact-retention-days "$MICRO_REVERSION_REPORT_ARTIFACT_RETENTION_DAYS"
      --low-disk-watermark-bytes "$MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES"
      --critical-disk-watermark-bytes "$MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES"
      --capacity-status-path "$MICRO_REVERSION_STORAGE_CAPACITY_STATUS_PATH"
    )
    if [[ "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" == "true" ]]; then
      maintenance_command+=(--purge-expired)
    fi
    if command -v ionice >/dev/null 2>&1; then
      run_with_safe_lock "$lock_path" nonblocking \
        ionice -c 3 nice -n "$MICRO_REVERSION_STORAGE_NICE_LEVEL" \
        "${maintenance_command[@]}"
    else
      run_with_safe_lock "$lock_path" nonblocking \
        nice -n "$MICRO_REVERSION_STORAGE_NICE_LEVEL" \
        "${maintenance_command[@]}"
    fi
  ) >"$result_path" || lock_rc=$?
  if [[ "$lock_rc" -eq 75 ]]; then
    rm -f "$result_path"
      micro_reversion_storage_status="lock_busy"
      micro_reversion_storage_purge_status="not_run_lock_busy"
    return 1
  fi
  if [[ "$lock_rc" -eq 76 ]]; then
    rm -f "$result_path"
      micro_reversion_storage_status="unsafe_lock"
      micro_reversion_storage_purge_status="not_run_unsafe_lock"
    return 1
  fi
  if [[ "$lock_rc" -ne 0 && ! -s "$result_path" ]]; then
    rm -f "$result_path"
    micro_reversion_storage_status="failed"
    micro_reversion_storage_purge_status="execution_failed"
    return 1
  fi

  local parsed
  if ! parsed="$("$PYTHON_BIN" - "$result_path" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("schema") != "scalp_micro_reversion_storage_maintenance_v1":
    raise SystemExit("storage maintenance schema mismatch")
if payload.get("mode") != "apply":
    raise SystemExit("storage maintenance did not apply")
if payload.get("actual_order_submitted") is not False:
    raise SystemExit("storage maintenance order authority mismatch")
if payload.get("broker_order_forbidden") is not True:
    raise SystemExit("storage maintenance broker authority mismatch")
if payload.get("trading_runtime_effect") is not False:
    raise SystemExit("storage maintenance runtime authority mismatch")
actions = payload.get("actions")
if not isinstance(actions, list):
    raise SystemExit("storage maintenance actions are invalid")
allowed_actions = {
    "compress_jsonl",
    "finalize_verified_compression",
    "publish_verified_gzip_source_preserved",
    "repair_manifest_reference",
    "purge_trade_date",
    "purge_trade_date_partial",
}


def native_nonnegative_int(value, *, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SystemExit(f"storage maintenance {field} is invalid")
    return value


def native_int(value, *, field):
    if isinstance(value, bool) or not isinstance(value, int):
        raise SystemExit(f"storage maintenance {field} is invalid")
    return value


def validate_capacity(payload, *, field_prefix):
    low = native_nonnegative_int(
        payload.get("low_disk_watermark_bytes"),
        field=f"{field_prefix} low_disk_watermark_bytes",
    )
    critical = native_nonnegative_int(
        payload.get("critical_disk_watermark_bytes"),
        field=f"{field_prefix} critical_disk_watermark_bytes",
    )
    if low < critical:
        raise SystemExit(f"storage maintenance {field_prefix} watermarks conflict")
    for field in (
        "disk_total_bytes",
        "disk_used_bytes_after",
        "disk_free_bytes_before",
        "disk_free_bytes_after",
        "retained_physical_bytes_before",
        "retained_physical_bytes_after",
        "compressed_target_bytes",
        "bytes_reclaimed",
    ):
        native_nonnegative_int(
            payload.get(field), field=f"{field_prefix} {field}"
        )
    native_int(
        payload.get("disk_free_bytes_delta"),
        field=f"{field_prefix} disk_free_bytes_delta",
    )
    native_int(
        payload.get("retained_physical_bytes_delta"),
        field=f"{field_prefix} retained_physical_bytes_delta",
    )
    if payload.get("disk_free_bytes_delta") != (
        payload.get("disk_free_bytes_after") - payload.get("disk_free_bytes_before")
    ):
        raise SystemExit(f"storage maintenance {field_prefix} free delta mismatch")
    if payload.get("retained_physical_bytes_delta") != (
        payload.get("retained_physical_bytes_after")
        - payload.get("retained_physical_bytes_before")
    ):
        raise SystemExit(
            f"storage maintenance {field_prefix} retained byte delta mismatch"
        )
    if payload.get("bytes_reclaimed") != max(
        0,
        payload.get("retained_physical_bytes_before")
        - payload.get("retained_physical_bytes_after"),
    ):
        raise SystemExit(
            f"storage maintenance {field_prefix} reclaimed byte mismatch"
        )
    free_after = payload.get("disk_free_bytes_after")
    expected_state = (
        "critical"
        if free_after < critical
        else ("low_warning" if free_after < low else "healthy")
    )
    if payload.get("capacity_state") != expected_state:
        raise SystemExit(f"storage maintenance {field_prefix} capacity state mismatch")
    expected_warning = expected_state == "low_warning"
    expected_failure = expected_state == "critical"
    if (
        payload.get("capacity_warning") is not expected_warning
        or payload.get("capacity_failure") is not expected_failure
        or payload.get("capacity_workorder_required")
        is not (expected_state != "healthy")
    ):
        raise SystemExit(
            f"storage maintenance {field_prefix} capacity flags mismatch"
        )
    reason_codes = payload.get("capacity_reason_codes")
    expected_reasons = (
        ["disk_free_below_critical_watermark"]
        if expected_failure
        else (["disk_free_below_low_watermark"] if expected_warning else [])
    )
    if reason_codes != expected_reasons:
        raise SystemExit(
            f"storage maintenance {field_prefix} capacity reasons mismatch"
        )
    return expected_state


capacity_state = validate_capacity(payload, field_prefix="root")
capacity_status_path = payload.get("capacity_status_artifact_path")
capacity_status_written = payload.get("capacity_status_written")
capacity_status_write_failure_count = native_nonnegative_int(
    payload.get("capacity_status_write_failure_count"),
    field="capacity_status_write_failure_count",
)
if not isinstance(capacity_status_path, str) or not capacity_status_path:
    raise SystemExit("storage maintenance capacity status path missing")
if capacity_status_written is not (capacity_status_write_failure_count == 0):
    raise SystemExit("storage maintenance capacity status write census mismatch")
if capacity_status_write_failure_count:
    if not isinstance(payload.get("capacity_status_write_failure_reason"), str):
        raise SystemExit("storage maintenance capacity status failure missing")
else:
    capacity_artifact_path = Path(capacity_status_path)
    capacity_artifact = json.loads(capacity_artifact_path.read_text(encoding="utf-8"))
    if capacity_artifact.get("schema") != (
        "scalp_micro_reversion_storage_capacity_status_v1"
    ):
        raise SystemExit("storage maintenance capacity artifact schema mismatch")
    declared_hash = capacity_artifact.get("artifact_content_sha256")
    content = {
        key: value
        for key, value in capacity_artifact.items()
        if key != "artifact_content_sha256"
    }
    encoded = json.dumps(
        content,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    if (
        not isinstance(declared_hash, str)
        or hashlib.sha256(encoded).hexdigest() != declared_hash
    ):
        raise SystemExit("storage maintenance capacity artifact hash mismatch")
    if (
        capacity_artifact.get("target_date") != payload.get("as_of_date")
        or capacity_artifact.get("capacity_state") != capacity_state
        or capacity_artifact.get("disk_free_bytes_after")
        != payload.get("disk_free_bytes_after")
        or capacity_artifact.get("retained_physical_bytes_after")
        != payload.get("retained_physical_bytes_after")
        or capacity_artifact.get("compressed_target_bytes")
        != payload.get("compressed_target_bytes")
        or capacity_artifact.get("bytes_reclaimed")
        != payload.get("bytes_reclaimed")
    ):
        raise SystemExit("storage maintenance capacity artifact binding mismatch")
    if (
        capacity_artifact.get("runtime_effect") is not False
        or capacity_artifact.get("allowed_runtime_apply") is not False
        or capacity_artifact.get("actual_order_submitted") is not False
        or capacity_artifact.get("broker_order_forbidden") is not True
        or capacity_artifact.get("trading_runtime_effect") is not False
        or capacity_artifact.get("provider_runtime_effect") is not False
        or capacity_artifact.get("provider_route_change_allowed") is not False
        or capacity_artifact.get("network_call_performed_by_module") is not False
        or capacity_artifact.get("automatic_deletion_authorized") is not False
    ):
        raise SystemExit("storage maintenance capacity artifact authority mismatch")


action_source_bytes = 0
for row in actions:
    if not isinstance(row, dict) or row.get("applied") is not True:
        raise SystemExit("storage maintenance apply action census is invalid")
    if row.get("action") not in allowed_actions:
        raise SystemExit("storage maintenance action taxonomy is invalid")
    action_source_bytes += native_nonnegative_int(
        row.get("source_bytes"), field="action source_bytes"
    )
action_count = native_nonnegative_int(payload.get("action_count"), field="action_count")
source_bytes = native_nonnegative_int(payload.get("source_bytes"), field="source_bytes")
if action_count != len(actions):
    raise SystemExit("storage maintenance action count mismatch")
if source_bytes != action_source_bytes:
    raise SystemExit("storage maintenance action source byte census mismatch")
partition_failures = payload.get("partition_failures")
partition_failure_count = payload.get("partition_failure_count")
if not isinstance(partition_failures, list):
    raise SystemExit("storage maintenance partition failures are invalid")
if (
    isinstance(partition_failure_count, bool)
    or not isinstance(partition_failure_count, int)
    or partition_failure_count != len(partition_failures)
):
    raise SystemExit("storage maintenance partition failure census mismatch")
report_artifacts = payload.get("report_artifact_maintenance")
report_artifact_action_count = 0
report_artifact_compressed_count = 0
report_artifact_source_bytes = 0
report_artifact_failure_count = 0
report_artifact_retention_candidate_count = 0
report_artifact_retention_candidate_bytes = 0
artifact_set_count = 0
artifact_set_terminal_count = 0
artifact_set_superseded_count = 0
artifact_set_incomplete_count = 0
artifact_set_stale_workorder_count = 0
artifact_set_stale_workorder_bytes = 0
immutable_source_artifact_count = 0
immutable_source_artifact_bytes = 0
checkpoint_journal_count = 0
checkpoint_terminal_count = 0
checkpoint_superseded_count = 0
checkpoint_incomplete_count = 0
checkpoint_stale_workorder_count = 0
checkpoint_stale_workorder_bytes = 0
provider_budget_ledger_count = 0
provider_budget_ledger_bytes = 0
provider_budget_retention_candidate_count = 0
provider_budget_retention_candidate_bytes = 0
exact_ai_artifact_count = 0
exact_ai_artifact_bytes = 0
exact_ai_compressed_count = 0
exact_ai_failure_count = 0
exact_ai_retention_candidate_count = 0
exact_ai_retention_candidate_bytes = 0
daily_owner_partition_count = 0
daily_owner_file_count = 0
daily_owner_bytes = 0
daily_owner_exact_date_file_count = 0
daily_owner_exact_date_bytes = 0
daily_owner_retention_candidate_count = 0
daily_owner_retention_candidate_bytes = 0
daily_owner_failure_count = 0
daily_owner_status = "not_run"
daily_owner_archive_offload_status = "not_run"
if report_artifacts is not None:
    if not isinstance(report_artifacts, dict) or report_artifacts.get("schema") != (
        "scalp_micro_reversion_report_artifact_storage_maintenance_v1"
    ):
        raise SystemExit("report artifact maintenance schema mismatch")
    if report_artifacts.get("mode") != "apply":
        raise SystemExit("report artifact maintenance did not apply")
    if (
        report_artifacts.get("actual_order_submitted") is not False
        or report_artifacts.get("broker_order_forbidden") is not True
        or report_artifacts.get("trading_runtime_effect") is not False
        or report_artifacts.get("provider_runtime_effect") is not False
        or report_artifacts.get("provider_route_change_allowed") is not False
        or report_artifacts.get("deletion_performed") is not False
    ):
        raise SystemExit("report artifact maintenance authority mismatch")
    report_capacity_state = validate_capacity(
        report_artifacts, field_prefix="report artifact"
    )
    report_actions = report_artifacts.get("actions")
    report_failures = report_artifacts.get("failures")
    if not isinstance(report_actions, list) or not isinstance(report_failures, list):
        raise SystemExit("report artifact maintenance census invalid")
    allowed_report_actions = {
        "compress_json_artifact",
        "finalize_verified_json_artifact_compression",
        "publish_verified_json_artifact_gzip_source_preserved",
        "compress_checkpoint_record_json",
        "finalize_verified_checkpoint_record_compression",
        "publish_verified_checkpoint_record_gzip_source_preserved",
        "compress_provider_budget_jsonl",
        "finalize_verified_provider_budget_compression",
        "publish_verified_provider_budget_gzip_source_preserved",
        "compress_exact_ai_jsonl",
        "finalize_verified_exact_ai_jsonl_compression",
        "publish_verified_exact_ai_jsonl_gzip_source_preserved",
        "compress_exact_ai_json",
        "finalize_verified_exact_ai_json_compression",
        "publish_verified_exact_ai_json_gzip_source_preserved",
    }
    for row in report_actions:
        if (
            not isinstance(row, dict)
            or row.get("applied") is not True
            or row.get("action") not in allowed_report_actions
        ):
            raise SystemExit("report artifact maintenance action invalid")
    report_artifact_action_count = native_nonnegative_int(
        report_artifacts.get("action_count"), field="report artifact action_count"
    )
    report_artifact_compressed_count = native_nonnegative_int(
        report_artifacts.get("compressed_count"),
        field="report artifact compressed_count",
    )
    report_artifact_source_bytes = native_nonnegative_int(
        report_artifacts.get("source_bytes"), field="report artifact source_bytes"
    )
    report_artifact_failure_count = native_nonnegative_int(
        report_artifacts.get("failure_count"), field="report artifact failure_count"
    )
    report_artifact_retention_candidate_count = native_nonnegative_int(
        report_artifacts.get("retention_candidate_count"),
        field="report artifact retention_candidate_count",
    )
    report_artifact_retention_candidate_bytes = native_nonnegative_int(
        report_artifacts.get("retention_candidate_bytes"),
        field="report artifact retention_candidate_bytes",
    )
    artifact_set_census = report_artifacts.get("artifact_set_census")
    checkpoint_census = report_artifacts.get("checkpoint_journal_census")
    provider_budget_census = report_artifacts.get("provider_budget_ledger_census")
    exact_ai_census = report_artifacts.get("exact_ai_artifact_maintenance")
    daily_owner_census = report_artifacts.get("micro_reversion_daily_owner_census")
    if (
        not isinstance(artifact_set_census, dict)
        or not isinstance(checkpoint_census, dict)
        or not isinstance(provider_budget_census, dict)
        or not isinstance(exact_ai_census, dict)
        or not isinstance(daily_owner_census, dict)
    ):
        raise SystemExit("report artifact terminal ledger census invalid")
    artifact_set_count = native_nonnegative_int(
        artifact_set_census.get("set_count"), field="artifact set_count"
    )
    artifact_set_terminal_count = native_nonnegative_int(
        artifact_set_census.get("terminal_count"), field="artifact terminal_count"
    )
    artifact_set_superseded_count = native_nonnegative_int(
        artifact_set_census.get("explicitly_superseded_count"),
        field="artifact explicitly_superseded_count",
    )
    artifact_set_incomplete_count = native_nonnegative_int(
        artifact_set_census.get("incomplete_resumable_count"),
        field="artifact incomplete_resumable_count",
    )
    artifact_set_stale_workorder_count = native_nonnegative_int(
        artifact_set_census.get("stale_workorder_count"),
        field="artifact stale_workorder_count",
    )
    artifact_set_stale_workorder_bytes = native_nonnegative_int(
        artifact_set_census.get("stale_workorder_bytes"),
        field="artifact stale_workorder_bytes",
    )
    immutable_source_artifact_count = native_nonnegative_int(
        artifact_set_census.get("immutable_source_artifact_count"),
        field="immutable source artifact_count",
    )
    immutable_source_artifact_bytes = native_nonnegative_int(
        artifact_set_census.get("immutable_source_artifact_bytes"),
        field="immutable source artifact_bytes",
    )
    if artifact_set_count != (
        artifact_set_terminal_count
        + artifact_set_superseded_count
        + artifact_set_incomplete_count
    ):
        raise SystemExit("artifact set state census mismatch")
    if artifact_set_stale_workorder_count > artifact_set_incomplete_count:
        raise SystemExit("artifact set stale workorder census mismatch")
    checkpoint_journal_count = native_nonnegative_int(
        checkpoint_census.get("journal_count"), field="checkpoint journal_count"
    )
    checkpoint_terminal_count = native_nonnegative_int(
        checkpoint_census.get("terminal_count"), field="checkpoint terminal_count"
    )
    checkpoint_superseded_count = native_nonnegative_int(
        checkpoint_census.get("superseded_count"),
        field="checkpoint superseded_count",
    )
    checkpoint_incomplete_count = native_nonnegative_int(
        checkpoint_census.get("incomplete_resumable_count"),
        field="checkpoint incomplete_resumable_count",
    )
    checkpoint_stale_workorder_count = native_nonnegative_int(
        checkpoint_census.get("stale_workorder_count"),
        field="checkpoint stale_workorder_count",
    )
    checkpoint_stale_workorder_bytes = native_nonnegative_int(
        checkpoint_census.get("stale_workorder_bytes"),
        field="checkpoint stale_workorder_bytes",
    )
    if checkpoint_journal_count != (
        checkpoint_terminal_count
        + checkpoint_superseded_count
        + checkpoint_incomplete_count
    ):
        raise SystemExit("checkpoint journal state census mismatch")
    if checkpoint_stale_workorder_count > checkpoint_incomplete_count:
        raise SystemExit("checkpoint stale workorder census mismatch")
    provider_budget_ledger_count = native_nonnegative_int(
        provider_budget_census.get("ledger_count"),
        field="provider budget ledger_count",
    )
    provider_budget_ledger_bytes = native_nonnegative_int(
        provider_budget_census.get("ledger_bytes"),
        field="provider budget ledger_bytes",
    )
    provider_budget_retention_candidate_count = native_nonnegative_int(
        provider_budget_census.get("retention_candidate_count"),
        field="provider budget retention_candidate_count",
    )
    provider_budget_retention_candidate_bytes = native_nonnegative_int(
        provider_budget_census.get("retention_candidate_bytes"),
        field="provider budget retention_candidate_bytes",
    )
    if provider_budget_retention_candidate_count > provider_budget_ledger_count:
        raise SystemExit("provider budget retention census mismatch")
    if exact_ai_census.get("schema") != (
        "scalp_micro_reversion_exact_ai_artifact_storage_maintenance_v1"
    ):
        raise SystemExit("exact AI artifact maintenance schema mismatch")
    exact_ai_artifact_count = native_nonnegative_int(
        exact_ai_census.get("artifact_count"), field="exact AI artifact_count"
    )
    exact_ai_artifact_bytes = native_nonnegative_int(
        exact_ai_census.get("artifact_bytes"), field="exact AI artifact_bytes"
    )
    exact_ai_compressed_count = native_nonnegative_int(
        exact_ai_census.get("compressed_count"), field="exact AI compressed_count"
    )
    exact_ai_failure_count = native_nonnegative_int(
        exact_ai_census.get("failure_count"), field="exact AI failure_count"
    )
    exact_ai_retention_candidate_count = native_nonnegative_int(
        exact_ai_census.get("retention_candidate_count"),
        field="exact AI retention_candidate_count",
    )
    exact_ai_retention_candidate_bytes = native_nonnegative_int(
        exact_ai_census.get("retention_candidate_bytes"),
        field="exact AI retention_candidate_bytes",
    )
    exact_ai_receipts = exact_ai_census.get("artifact_receipts")
    if not isinstance(exact_ai_receipts, list) or len(exact_ai_receipts) != (
        exact_ai_artifact_count
    ):
        raise SystemExit("exact AI artifact receipt census mismatch")
    exact_ai_receipt_bytes = 0
    for receipt in exact_ai_receipts:
        physical = receipt.get("physical_representations") if isinstance(receipt, dict) else None
        decoded_hash = receipt.get("decoded_content_sha256") if isinstance(receipt, dict) else None
        if (
            not isinstance(physical, list)
            or not physical
            or not isinstance(decoded_hash, str)
            or len(decoded_hash) != 64
        ):
            raise SystemExit("exact AI artifact receipt invalid")
        for representation in physical:
            if not isinstance(representation, dict):
                raise SystemExit("exact AI physical receipt invalid")
            exact_ai_receipt_bytes += native_nonnegative_int(
                representation.get("stored_bytes"),
                field="exact AI receipt stored_bytes",
            )
            stored_hash = representation.get("stored_sha256")
            if not isinstance(stored_hash, str) or len(stored_hash) != 64:
                raise SystemExit("exact AI receipt stored hash invalid")
    if exact_ai_receipt_bytes != exact_ai_artifact_bytes:
        raise SystemExit("exact AI artifact byte census mismatch")
    if (
        exact_ai_retention_candidate_count > exact_ai_artifact_count
        or exact_ai_census.get("deletion_performed") is not False
        or exact_ai_census.get("archive_offload_performed") is not False
        or exact_ai_census.get("status")
        != ("partial_failure" if exact_ai_failure_count else "pass")
    ):
        raise SystemExit("exact AI artifact maintenance contract mismatch")
    if daily_owner_census.get("schema") != (
        "scalp_micro_reversion_daily_owner_storage_census_v1"
    ):
        raise SystemExit("micro-reversion daily owner census schema mismatch")
    daily_owner_partition_count = native_nonnegative_int(
        daily_owner_census.get("partition_count"), field="daily owner partition_count"
    )
    daily_owner_file_count = native_nonnegative_int(
        daily_owner_census.get("file_count"), field="daily owner file_count"
    )
    daily_owner_bytes = native_nonnegative_int(
        daily_owner_census.get("physical_bytes"), field="daily owner physical_bytes"
    )
    daily_owner_exact_date_file_count = native_nonnegative_int(
        daily_owner_census.get("exact_date_file_count"),
        field="daily owner exact_date_file_count",
    )
    daily_owner_exact_date_bytes = native_nonnegative_int(
        daily_owner_census.get("exact_date_bytes"),
        field="daily owner exact_date_bytes",
    )
    daily_owner_retention_candidate_count = native_nonnegative_int(
        daily_owner_census.get("retention_candidate_count"),
        field="daily owner retention_candidate_count",
    )
    daily_owner_retention_candidate_bytes = native_nonnegative_int(
        daily_owner_census.get("retention_candidate_bytes"),
        field="daily owner retention_candidate_bytes",
    )
    daily_owner_failure_count = native_nonnegative_int(
        daily_owner_census.get("failure_count"), field="daily owner failure_count"
    )
    daily_owner_archive_offload_status = daily_owner_census.get(
        "durable_archive_offload_owner_status"
    )
    daily_owner_status = daily_owner_census.get("status")
    daily_owner_receipts = daily_owner_census.get("partition_receipts")
    if (
        not isinstance(daily_owner_receipts, list)
        or len(daily_owner_receipts) != daily_owner_partition_count
        or sum(
            native_nonnegative_int(
                row.get("file_count") if isinstance(row, dict) else None,
                field="daily owner receipt file_count",
            )
            for row in daily_owner_receipts
        )
        != daily_owner_file_count
        or sum(
            native_nonnegative_int(
                row.get("physical_bytes") if isinstance(row, dict) else None,
                field="daily owner receipt physical_bytes",
            )
            for row in daily_owner_receipts
        )
        != daily_owner_bytes
    ):
        raise SystemExit("micro-reversion daily owner receipt census mismatch")
    if (
        daily_owner_retention_candidate_count > daily_owner_partition_count
        or daily_owner_census.get("automatic_compression_authorized") is not False
        or daily_owner_census.get("automatic_deletion_authorized") is not False
        or daily_owner_census.get("archive_offload_authorized") is not False
        or daily_owner_archive_offload_status
        != "open_owner_required_no_automatic_archive_offload_or_deletion"
        or daily_owner_status
        not in (
            {"partial_failure"}
            if daily_owner_failure_count
            else {"pass", "not_present"}
        )
    ):
        raise SystemExit("micro-reversion daily owner census contract mismatch")
    expected_report_compressed = sum(
        row.get("action")
        in {
            "compress_json_artifact",
            "finalize_verified_json_artifact_compression",
            "compress_checkpoint_record_json",
            "finalize_verified_checkpoint_record_compression",
            "compress_provider_budget_jsonl",
            "finalize_verified_provider_budget_compression",
            "compress_exact_ai_jsonl",
            "finalize_verified_exact_ai_jsonl_compression",
            "compress_exact_ai_json",
            "finalize_verified_exact_ai_json_compression",
        }
        for row in report_actions
    )
    if (
        report_artifact_action_count != len(report_actions)
        or report_artifact_compressed_count != expected_report_compressed
        or report_artifact_failure_count != len(report_failures)
        or report_artifacts.get("status")
        != (
            "partial_failure"
            if report_failures or report_capacity_state == "critical"
            else "pass"
        )
    ):
        raise SystemExit("report artifact maintenance declared census mismatch")
expected_status = (
    "partial_failure"
    if (
        partition_failure_count
        or report_artifact_failure_count
        or capacity_state == "critical"
        or capacity_status_write_failure_count
    )
    else "pass"
)
if payload.get("status") != expected_status:
    raise SystemExit("storage maintenance status mismatch")
failure_candidate_count = 0
failure_candidate_bytes = 0
failure_recovery_required_count = 0
for row in partition_failures:
    if not isinstance(row, dict):
        raise SystemExit("storage maintenance partition failure row is invalid")
    raw_candidate_count = row.get("candidate_count")
    raw_candidate_bytes = row.get("candidate_bytes")
    if isinstance(raw_candidate_count, bool) or isinstance(raw_candidate_bytes, bool):
        raise SystemExit("storage maintenance failure candidate census is invalid")
    try:
        candidate_count = int(raw_candidate_count)
        candidate_bytes = int(raw_candidate_bytes)
    except (TypeError, ValueError) as exc:
        raise SystemExit("storage maintenance failure candidate census is invalid") from exc
    if candidate_count < 0 or candidate_bytes < 0:
        raise SystemExit("storage maintenance failure candidate census is invalid")
    recovery_required = row.get("recovery_required")
    if recovery_required not in {"true", "false"}:
        raise SystemExit("storage maintenance recovery flag is invalid")
    failure_candidate_count += candidate_count
    failure_candidate_bytes += candidate_bytes
    failure_recovery_required_count += recovery_required == "true"
failed_candidate_count = native_nonnegative_int(
    payload.get("failed_candidate_count"), field="failed_candidate_count"
)
failed_candidate_bytes = native_nonnegative_int(
    payload.get("failed_candidate_bytes"), field="failed_candidate_bytes"
)
recovery_required_count = native_nonnegative_int(
    payload.get("recovery_required_count"), field="recovery_required_count"
)
if failed_candidate_count != failure_candidate_count:
    raise SystemExit("storage maintenance failed candidate count mismatch")
if failed_candidate_bytes != failure_candidate_bytes:
    raise SystemExit("storage maintenance failed candidate byte census mismatch")
if recovery_required_count != failure_recovery_required_count:
    raise SystemExit("storage maintenance recovery census mismatch")
compressed = sum(
    row.get("action") in {"compress_jsonl", "finalize_verified_compression"}
    for row in actions
    if isinstance(row, dict)
)
purged = sum(row.get("action") == "purge_trade_date" for row in actions if isinstance(row, dict))
purged_partial = sum(
    row.get("action") == "purge_trade_date_partial"
    for row in actions
    if isinstance(row, dict)
)
purge_enabled = payload.get("purge_enabled")
purge_status = payload.get("purge_status")
if not isinstance(purge_enabled, bool):
    raise SystemExit("storage maintenance purge authority is invalid")
expected_purge_status = (
    "explicit_opt_in_apply" if purge_enabled else "disabled_no_deletion_authority"
)
if purge_status != expected_purge_status:
    raise SystemExit("storage maintenance purge status is invalid")
if not purge_enabled and (purged or purged_partial):
    raise SystemExit("storage maintenance purged without explicit authority")
purge_applied_count = native_nonnegative_int(
    payload.get("purge_applied_count"), field="purge_applied_count"
)
purge_partial_applied_count = native_nonnegative_int(
    payload.get("purge_partial_applied_count"), field="purge_partial_applied_count"
)
if purge_applied_count != purged:
    raise SystemExit("storage maintenance purge applied census mismatch")
if purge_partial_applied_count != purged_partial:
    raise SystemExit("storage maintenance partial purge census mismatch")
deletion_performed = payload.get("deletion_performed")
if not isinstance(deletion_performed, bool):
    raise SystemExit("storage maintenance deletion status type is invalid")
if deletion_performed != bool(purged or purged_partial):
    raise SystemExit("storage maintenance deletion status mismatch")
for field in ("purge_candidate_count", "purge_candidate_bytes"):
    native_nonnegative_int(payload.get(field), field=field)
print(
    action_count,
    compressed,
    purged,
    purged_partial,
    source_bytes,
    "true" if purge_enabled else "false",
    purge_status,
    int(payload.get("purge_candidate_count") or 0),
    int(payload.get("purge_candidate_bytes") or 0),
    partition_failure_count,
    failed_candidate_count,
    failed_candidate_bytes,
    recovery_required_count,
    report_artifact_action_count,
    report_artifact_compressed_count,
    report_artifact_source_bytes,
    report_artifact_failure_count,
    report_artifact_retention_candidate_count,
    report_artifact_retention_candidate_bytes,
    artifact_set_count,
    artifact_set_terminal_count,
    artifact_set_superseded_count,
    artifact_set_incomplete_count,
    artifact_set_stale_workorder_count,
    artifact_set_stale_workorder_bytes,
    immutable_source_artifact_count,
    immutable_source_artifact_bytes,
    checkpoint_journal_count,
    checkpoint_terminal_count,
    checkpoint_superseded_count,
    checkpoint_incomplete_count,
    checkpoint_stale_workorder_count,
    checkpoint_stale_workorder_bytes,
    provider_budget_ledger_count,
    provider_budget_ledger_bytes,
    provider_budget_retention_candidate_count,
    provider_budget_retention_candidate_bytes,
    exact_ai_artifact_count,
    exact_ai_artifact_bytes,
    exact_ai_compressed_count,
    exact_ai_failure_count,
    exact_ai_retention_candidate_count,
    exact_ai_retention_candidate_bytes,
    daily_owner_partition_count,
    daily_owner_file_count,
    daily_owner_bytes,
    daily_owner_exact_date_file_count,
    daily_owner_exact_date_bytes,
    daily_owner_retention_candidate_count,
    daily_owner_retention_candidate_bytes,
    daily_owner_failure_count,
    daily_owner_status,
    daily_owner_archive_offload_status,
    payload.get("disk_free_bytes_before"),
    payload.get("disk_free_bytes_after"),
    payload.get("disk_free_bytes_delta"),
    payload.get("retained_physical_bytes_after"),
    payload.get("compressed_target_bytes"),
    payload.get("bytes_reclaimed"),
    capacity_state,
    "true" if payload.get("capacity_warning") is True else "false",
    "true" if payload.get("capacity_failure") is True else "false",
    "true" if payload.get("capacity_workorder_required") is True else "false",
    "true" if capacity_status_written is True else "false",
    capacity_status_write_failure_count,
)
PY
  )"; then
    rm -f "$result_path"
    micro_reversion_storage_status="invalid_result"
    micro_reversion_storage_purge_status="invalid_result"
    return 1
  fi
  read -r \
    micro_reversion_storage_action_count \
    micro_reversion_storage_compressed_count \
    micro_reversion_storage_purged_count \
    micro_reversion_storage_purge_partial_count \
    micro_reversion_storage_source_bytes \
    micro_reversion_storage_purge_enabled \
    micro_reversion_storage_purge_status \
    micro_reversion_storage_purge_candidate_count \
    micro_reversion_storage_purge_candidate_bytes \
    micro_reversion_storage_partition_failure_count \
    micro_reversion_storage_failed_candidate_count \
    micro_reversion_storage_failed_candidate_bytes \
    micro_reversion_storage_recovery_required_count \
    micro_reversion_report_artifact_action_count \
    micro_reversion_report_artifact_compressed_count \
    micro_reversion_report_artifact_source_bytes \
    micro_reversion_report_artifact_failure_count \
    micro_reversion_report_artifact_retention_candidate_count \
    micro_reversion_report_artifact_retention_candidate_bytes \
    micro_reversion_artifact_set_count \
    micro_reversion_artifact_set_terminal_count \
    micro_reversion_artifact_set_superseded_count \
    micro_reversion_artifact_set_incomplete_count \
    micro_reversion_artifact_set_stale_workorder_count \
    micro_reversion_artifact_set_stale_workorder_bytes \
    micro_reversion_immutable_source_artifact_count \
    micro_reversion_immutable_source_artifact_bytes \
    micro_reversion_checkpoint_journal_count \
    micro_reversion_checkpoint_terminal_count \
    micro_reversion_checkpoint_superseded_count \
    micro_reversion_checkpoint_incomplete_count \
    micro_reversion_checkpoint_stale_workorder_count \
    micro_reversion_checkpoint_stale_workorder_bytes \
    micro_reversion_provider_budget_ledger_count \
    micro_reversion_provider_budget_ledger_bytes \
    micro_reversion_provider_budget_retention_candidate_count \
    micro_reversion_provider_budget_retention_candidate_bytes \
    micro_reversion_exact_ai_artifact_count \
    micro_reversion_exact_ai_artifact_bytes \
    micro_reversion_exact_ai_compressed_count \
    micro_reversion_exact_ai_failure_count \
    micro_reversion_exact_ai_retention_candidate_count \
    micro_reversion_exact_ai_retention_candidate_bytes \
    micro_reversion_daily_owner_partition_count \
    micro_reversion_daily_owner_file_count \
    micro_reversion_daily_owner_bytes \
    micro_reversion_daily_owner_exact_date_file_count \
    micro_reversion_daily_owner_exact_date_bytes \
    micro_reversion_daily_owner_retention_candidate_count \
    micro_reversion_daily_owner_retention_candidate_bytes \
    micro_reversion_daily_owner_failure_count \
    micro_reversion_daily_owner_status \
    micro_reversion_daily_owner_archive_offload_status \
    micro_reversion_storage_disk_free_bytes_before \
    micro_reversion_storage_disk_free_bytes_after \
    micro_reversion_storage_disk_free_bytes_delta \
    micro_reversion_storage_retained_physical_bytes_after \
    micro_reversion_storage_compressed_target_bytes \
    micro_reversion_storage_bytes_reclaimed \
    micro_reversion_storage_capacity_state \
    micro_reversion_storage_capacity_warning \
    micro_reversion_storage_capacity_failure \
    micro_reversion_storage_capacity_workorder_required \
    micro_reversion_storage_capacity_status_written \
    micro_reversion_storage_capacity_status_write_failures <<<"$parsed"
  if [[ "$micro_reversion_storage_purge_enabled" != "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" ]]; then
    rm -f "$result_path"
    micro_reversion_storage_status="purge_authority_mismatch"
    micro_reversion_storage_purge_status="authority_mismatch"
    return 1
  fi
  if [[ "$micro_reversion_storage_capacity_status_write_failures" -gt 0 ]]; then
    rm -f "$result_path"
    micro_reversion_storage_status="capacity_status_write_failure"
    return 1
  fi
  if [[ "$micro_reversion_storage_capacity_failure" == "true" ]]; then
    rm -f "$result_path"
    micro_reversion_storage_status="critical_capacity"
    return 1
  fi
  if [[ "$micro_reversion_storage_partition_failure_count" -gt 0 || "$micro_reversion_report_artifact_failure_count" -gt 0 ]]; then
    rm -f "$result_path"
    micro_reversion_storage_status="partial_failure"
    return 1
  fi
  if [[ "$lock_rc" -ne 0 ]]; then
    rm -f "$result_path"
    micro_reversion_storage_status="unexpected_nonzero_exit"
    return 1
  fi
  rm -f "$result_path"
  micro_reversion_storage_status="pass"
}

path_has_open_fd() {
  local path="$1"
  local path_dev_inode=""
  local fd_path=""
  local fd_dev_inode=""

  if [[ ! -e "$path" ]]; then
    return 1
  fi
  if command -v fuser >/dev/null 2>&1; then
    if fuser -s -I "$path"; then
      return 0
    fi
  fi
  if [[ ! -d /proc ]]; then
    return 0
  fi
  if ! path_dev_inode="$(stat -Lc '%d:%i' "$path" 2>/dev/null)"; then
    return 0
  fi
  for fd_path in /proc/[0-9]*/fd/*; do
    if [[ ! -e "$fd_path" && ! -L "$fd_path" ]]; then
      continue
    fi
    fd_dev_inode="$(stat -Lc '%d:%i' "$fd_path" 2>/dev/null || true)"
    if [[ -n "$fd_dev_inode" && "$fd_dev_inode" == "$path_dev_inode" ]]; then
      return 0
    fi
  done
  return 1
}

compress_file_verified() {
  local source_path="$1"
  local quiet_seconds="${2:-0}"
  local generation_identity_enabled="${3:-false}"
  local standard_gzip_path="${source_path}.gz"
  local generation_base_path=""
  local gzip_path="$standard_gzip_path"
  local tmp_path=""
  local source_size source_mtime_epoch now_epoch source_quiet_age restored_size
  local source_metadata source_sha256 restored_sha256 verified_metadata verified_sha256
  local target_metadata target_verified_metadata target_sha256 target_file_sha256 target_verified_sha256
  local collision_generation_hash=""
  compression_failure_reason="unknown"
  compression_action="failed"
  compression_output_path="$standard_gzip_path"
  compression_preserved_existing_gzip_path=""
  if [[ ! -f "$source_path" ]]; then
    compression_failure_reason="source_missing_before_compression"
    return 1
  fi
  if path_has_open_fd "$source_path"; then
    compression_failure_reason="source_in_use"
    return 1
  fi
  if ! source_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path")"; then
    compression_failure_reason="source_stat_failed"
    return 1
  fi
  if ! source_size="$(stat -c%s "$source_path")"; then
    compression_failure_reason="source_size_failed"
    return 1
  fi
  if ! source_mtime_epoch="$(stat -c%Y "$source_path")"; then
    compression_failure_reason="source_mtime_failed"
    return 1
  fi
  now_epoch="$(date +%s)"
  source_quiet_age=$((now_epoch - source_mtime_epoch))
  if [[ "$source_quiet_age" -lt "$quiet_seconds" ]]; then
    compression_failure_reason="source_not_quiet"
    return 1
  fi
  if ! source_sha256="$(sha256sum -- "$source_path" | awk '{print $1}')"; then
    compression_failure_reason="source_hash_failed"
    return 1
  fi
  if [[ "$generation_identity_enabled" == "true" ]]; then
    if [[ ! "$(basename "$source_path")" =~ ^.+\.log\.[0-9]+$ ]]; then
      compression_failure_reason="numeric_generation_source_name_invalid"
      return 1
    fi
    collision_generation_hash="${source_sha256:0:16}"
    generation_base_path="${source_path%.*}"
    standard_gzip_path="${generation_base_path}.generation_${collision_generation_hash}.gz"
    gzip_path="$standard_gzip_path"
    compression_output_path="$gzip_path"
  fi

  if [[ -e "$standard_gzip_path" || -L "$standard_gzip_path" ]]; then
    if [[ ! -f "$standard_gzip_path" || -L "$standard_gzip_path" ]]; then
      compression_failure_reason="existing_gzip_unsafe_type"
      return 1
    fi
    if path_has_open_fd "$standard_gzip_path"; then
      compression_failure_reason="existing_gzip_in_use"
      return 1
    fi
    if ! target_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$standard_gzip_path")"; then
      compression_failure_reason="existing_gzip_stat_failed"
      return 1
    fi
    if ! target_file_sha256="$(sha256sum -- "$standard_gzip_path" | awk '{print $1}')"; then
      compression_failure_reason="existing_gzip_file_hash_failed"
      return 1
    fi
    if ! gzip -t -- "$standard_gzip_path"; then
      compression_failure_reason="existing_gzip_invalid_conflict"
      return 1
    fi
    if ! target_sha256="$(gzip -cd -- "$standard_gzip_path" | sha256sum | awk '{print $1}')"; then
      compression_failure_reason="existing_gzip_restore_hash_failed"
      return 1
    fi
    if ! target_verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$standard_gzip_path")" || \
       ! target_verified_sha256="$(sha256sum -- "$standard_gzip_path" | awk '{print $1}')"; then
      compression_failure_reason="existing_gzip_recheck_failed"
      return 1
    fi
    if [[ "$target_verified_metadata" != "$target_metadata" || "$target_verified_sha256" != "$target_file_sha256" ]] || \
       path_has_open_fd "$standard_gzip_path"; then
      compression_failure_reason="existing_gzip_changed_or_open_during_verify"
      return 1
    fi
    if [[ "$target_sha256" != "$source_sha256" ]]; then
      if [[ "$generation_identity_enabled" == "true" ]]; then
        compression_failure_reason="generation_identity_content_mismatch"
        return 1
      else
        compression_failure_reason="existing_gzip_content_conflict_source_authoritative"
        return 1
      fi
    else
      if ! verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path")" || \
         ! verified_sha256="$(sha256sum -- "$source_path" | awk '{print $1}')"; then
        compression_failure_reason="source_recheck_failed"
        return 1
      fi
      if [[ "$verified_metadata" != "$source_metadata" || "$verified_sha256" != "$source_sha256" ]] || \
         path_has_open_fd "$source_path"; then
        if [[ "$generation_identity_enabled" == "true" ]]; then
          compression_failure_reason="source_changed_or_open_during_generation_verify"
        else
          compression_failure_reason="source_changed_or_open_during_existing_verify"
        fi
        return 1
      fi
      compression_failure_reason="none"
      if [[ "$generation_identity_enabled" == "true" ]]; then
        compression_action="verified_generation_source_preserved"
      else
        compression_action="verified_existing_gzip_source_preserved"
      fi
      return 0
    fi
  fi

  if ! tmp_path="$(mktemp "${gzip_path}.tmp.XXXXXX")"; then
    compression_failure_reason="gzip_temp_create_failed"
    return 1
  fi
  if ! gzip -9 -c -- "$source_path" >"$tmp_path"; then
    verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path" 2>/dev/null || true)"
    if [[ -n "$verified_metadata" && "$verified_metadata" != "$source_metadata" ]]; then
      compression_failure_reason="source_changed_during_compression"
    else
      compression_failure_reason="gzip_failed"
    fi
    rm -f "$tmp_path"
    return 1
  fi
  if ! gzip -t -- "$tmp_path"; then
    compression_failure_reason="gzip_integrity_failed"
    rm -f "$tmp_path"
    return 1
  fi
  if ! restored_size="$(gzip -cd -- "$tmp_path" | wc -c | tr -d ' ')"; then
    compression_failure_reason="gzip_restore_size_failed"
    rm -f "$tmp_path"
    return 1
  fi
  if [[ "$restored_size" != "$source_size" ]]; then
    compression_failure_reason="gzip_restore_size_mismatch"
    rm -f "$tmp_path"
    return 1
  fi
  if ! restored_sha256="$(gzip -cd -- "$tmp_path" | sha256sum | awk '{print $1}')"; then
    compression_failure_reason="gzip_restore_hash_failed"
    rm -f "$tmp_path"
    return 1
  fi
  if [[ "$restored_sha256" != "$source_sha256" ]]; then
    compression_failure_reason="gzip_restore_hash_mismatch"
    rm -f "$tmp_path"
    return 1
  fi
  if ! verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path")"; then
    compression_failure_reason="source_missing_after_compression"
    rm -f "$tmp_path"
    return 1
  fi
  if ! verified_sha256="$(sha256sum -- "$source_path" | awk '{print $1}')"; then
    compression_failure_reason="source_recheck_hash_failed"
    rm -f "$tmp_path"
    return 1
  fi
  if [[ "$verified_metadata" != "$source_metadata" || "$verified_sha256" != "$source_sha256" ]]; then
    compression_failure_reason="source_changed_during_compression"
    rm -f "$tmp_path"
    return 1
  fi
  if path_has_open_fd "$source_path"; then
    compression_failure_reason="source_in_use_after_compression"
    rm -f "$tmp_path"
    return 1
  fi
  if [[ -e "$gzip_path" || -L "$gzip_path" ]]; then
    compression_failure_reason="gzip_publish_target_appeared"
    rm -f "$tmp_path"
    return 1
  fi
  if ! ln -- "$tmp_path" "$gzip_path"; then
    compression_failure_reason="gzip_publish_no_clobber_failed"
    rm -f "$tmp_path"
    return 1
  fi
  rm -f "$tmp_path"
  if ! verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path")"; then
    compression_failure_reason="source_missing_after_gzip_publish"
    return 1
  fi
  if ! verified_sha256="$(sha256sum -- "$source_path" | awk '{print $1}')"; then
    compression_failure_reason="source_hash_failed_after_gzip_publish"
    return 1
  fi
  if [[ "$verified_metadata" != "$source_metadata" || "$verified_sha256" != "$source_sha256" ]]; then
    compression_failure_reason="source_changed_after_gzip_publish"
    return 1
  fi
  if path_has_open_fd "$source_path"; then
    compression_failure_reason="source_in_use_after_gzip_publish"
    return 1
  fi
  if path_has_open_fd "$gzip_path"; then
    compression_failure_reason="gzip_target_in_use_after_publish"
    return 1
  fi
  if ! target_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$gzip_path")" || \
     ! target_sha256="$(sha256sum -- "$gzip_path" | awk '{print $1}')" || \
     ! restored_sha256="$(gzip -cd -- "$gzip_path" | sha256sum | awk '{print $1}')"; then
    compression_failure_reason="gzip_target_recheck_failed"
    return 1
  fi
  if [[ "$restored_sha256" != "$source_sha256" ]]; then
    compression_failure_reason="gzip_target_restore_hash_mismatch"
    return 1
  fi
  if ! target_verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$gzip_path")" || \
     ! target_verified_sha256="$(sha256sum -- "$gzip_path" | awk '{print $1}')"; then
    compression_failure_reason="gzip_target_final_recheck_failed"
    return 1
  fi
  if [[ "$target_verified_metadata" != "$target_metadata" || "$target_verified_sha256" != "$target_sha256" ]] || \
     path_has_open_fd "$gzip_path"; then
    compression_failure_reason="gzip_target_changed_or_open_after_publish"
    return 1
  fi
  compression_failure_reason="none"
  if [[ "$generation_identity_enabled" == "true" ]]; then
    compression_action="compressed_generation_source_preserved"
  elif [[ "$gzip_path" == "$standard_gzip_path" ]]; then
    compression_action="compressed_copy_source_preserved"
  else
    compression_action="compressed_collision_generation_source_preserved"
  fi
}

# Run the high-volume closed-date storage compaction before generic log archive
# work. A concurrently growing rotated log must never prevent this independent
# storage-only maintenance lane from running.
if [[ "$DATA_MAINTENANCE_ENABLED" == "true" ]]; then
  if ! run_micro_reversion_storage_maintenance; then
    micro_reversion_storage_failure_count=$((micro_reversion_storage_failure_count + 1))
    echo "[MICRO_REVERSION_STORAGE_FAIL] status=${micro_reversion_storage_status} purge_status=${micro_reversion_storage_purge_status} capacity_state=${micro_reversion_storage_capacity_state} disk_free_bytes_after=${micro_reversion_storage_disk_free_bytes_after} retained_physical_bytes_after=${micro_reversion_storage_retained_physical_bytes_after} compressed_target_bytes=${micro_reversion_storage_compressed_target_bytes} bytes_reclaimed=${micro_reversion_storage_bytes_reclaimed} capacity_workorder_required=${micro_reversion_storage_capacity_workorder_required} capacity_status_written=${micro_reversion_storage_capacity_status_written} generic_cleanup_will_continue=true"
  else
    if [[ "$micro_reversion_storage_capacity_warning" == "true" ]]; then
      echo "[MICRO_REVERSION_STORAGE_CAPACITY_WARNING] capacity_state=${micro_reversion_storage_capacity_state} disk_free_bytes_after=${micro_reversion_storage_disk_free_bytes_after} low_disk_watermark_bytes=${MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES} critical_disk_watermark_bytes=${MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES} capacity_workorder_required=${micro_reversion_storage_capacity_workorder_required} capacity_status_written=${micro_reversion_storage_capacity_status_written} cleanup_will_continue=true"
    fi
    echo "[MICRO_REVERSION_STORAGE] status=${micro_reversion_storage_status} actions=${micro_reversion_storage_action_count} compressed=${micro_reversion_storage_compressed_count} purged=${micro_reversion_storage_purged_count} purge_partial=${micro_reversion_storage_purge_partial_count} purge_enabled=${micro_reversion_storage_purge_enabled} purge_status=${micro_reversion_storage_purge_status} report_artifact_actions=${micro_reversion_report_artifact_action_count} report_artifact_compressed=${micro_reversion_report_artifact_compressed_count} report_artifact_source_bytes=${micro_reversion_report_artifact_source_bytes} report_artifact_failures=${micro_reversion_report_artifact_failure_count} report_artifact_retention_candidates=${micro_reversion_report_artifact_retention_candidate_count} report_artifact_retention_candidate_bytes=${micro_reversion_report_artifact_retention_candidate_bytes} artifact_sets=${micro_reversion_artifact_set_count} artifact_set_terminal=${micro_reversion_artifact_set_terminal_count} artifact_set_superseded=${micro_reversion_artifact_set_superseded_count} artifact_set_incomplete=${micro_reversion_artifact_set_incomplete_count} artifact_set_stale_workorders=${micro_reversion_artifact_set_stale_workorder_count} artifact_set_stale_workorder_bytes=${micro_reversion_artifact_set_stale_workorder_bytes} immutable_source_artifacts=${micro_reversion_immutable_source_artifact_count} immutable_source_artifact_bytes=${micro_reversion_immutable_source_artifact_bytes} checkpoint_journals=${micro_reversion_checkpoint_journal_count} checkpoint_terminal=${micro_reversion_checkpoint_terminal_count} checkpoint_superseded=${micro_reversion_checkpoint_superseded_count} checkpoint_incomplete=${micro_reversion_checkpoint_incomplete_count} checkpoint_stale_workorders=${micro_reversion_checkpoint_stale_workorder_count} checkpoint_stale_workorder_bytes=${micro_reversion_checkpoint_stale_workorder_bytes} provider_budget_ledgers=${micro_reversion_provider_budget_ledger_count} provider_budget_ledger_bytes=${micro_reversion_provider_budget_ledger_bytes} provider_budget_retention_candidates=${micro_reversion_provider_budget_retention_candidate_count} provider_budget_retention_candidate_bytes=${micro_reversion_provider_budget_retention_candidate_bytes} exact_ai_artifacts=${micro_reversion_exact_ai_artifact_count} exact_ai_artifact_bytes=${micro_reversion_exact_ai_artifact_bytes} exact_ai_compressed=${micro_reversion_exact_ai_compressed_count} exact_ai_failures=${micro_reversion_exact_ai_failure_count} exact_ai_retention_candidates=${micro_reversion_exact_ai_retention_candidate_count} exact_ai_retention_candidate_bytes=${micro_reversion_exact_ai_retention_candidate_bytes} daily_owner_status=${micro_reversion_daily_owner_status} daily_owner_partitions=${micro_reversion_daily_owner_partition_count} daily_owner_files=${micro_reversion_daily_owner_file_count} daily_owner_bytes=${micro_reversion_daily_owner_bytes} daily_owner_exact_date_files=${micro_reversion_daily_owner_exact_date_file_count} daily_owner_exact_date_bytes=${micro_reversion_daily_owner_exact_date_bytes} daily_owner_retention_candidates=${micro_reversion_daily_owner_retention_candidate_count} daily_owner_retention_candidate_bytes=${micro_reversion_daily_owner_retention_candidate_bytes} daily_owner_archive_offload_status=${micro_reversion_daily_owner_archive_offload_status} disk_free_bytes_before=${micro_reversion_storage_disk_free_bytes_before} disk_free_bytes_after=${micro_reversion_storage_disk_free_bytes_after} disk_free_bytes_delta=${micro_reversion_storage_disk_free_bytes_delta} retained_physical_bytes_after=${micro_reversion_storage_retained_physical_bytes_after} compressed_target_bytes=${micro_reversion_storage_compressed_target_bytes} bytes_reclaimed=${micro_reversion_storage_bytes_reclaimed} capacity_state=${micro_reversion_storage_capacity_state} capacity_workorder_required=${micro_reversion_storage_capacity_workorder_required} capacity_status_written=${micro_reversion_storage_capacity_status_written} runtime_effect=false order_authority=false provider_authority=false deletion_authority=false archive_offload_authority=false"
  fi
fi

# Active/writer-owned logs are never renamed, truncated, or shifted here. The
# cleanup wrapper only reports oversized files until the explicit writer owner
# supplies a single-file/signal-safe rotation contract.
rotated_active_count=0
active_find_path="$(mktemp "$LOG_DIR/.cleanup_find_active.XXXXXX")"
collect_find_results "active_rotation_census" "$active_find_path" \
  "$LOG_DIR" -maxdepth 1 -type f \( \
    -name '*_cron.log' -o \
    -name 'run_*.log' -o \
    -name 'threshold_cycle_*.log' -o \
    -name 'tuning_monitoring_*.log' -o \
    -name 'dashboard_db_archive_*.log' -o \
    -name 'ensemble_scanner.log' -o \
    -name 'update_kospi.log' -o \
    -name 'buy_pause_guard.log' \
  \) || true
while IFS= read -r -d '' active_log; do
  if [[ "$(basename "$active_log")" == "log_rotation_cleanup_cron.log" ]]; then
    continue
  fi
  active_size_bytes="$(stat -c%s "$active_log" 2>/dev/null || echo 0)"
  if [[ "$active_size_bytes" -ge "$ACTIVE_LOG_MAX_BYTES" ]]; then
    active_rotation_deferred_count=$((active_rotation_deferred_count + 1))
    register_writer_defer "active_log" "$active_log" "writer_owned_oversize"
    archive_retention_protected_paths["$active_log"]=1
    archive_retention_protection_reasons["$active_log"]="active_rotation_disabled_pending_writer_owner"
    echo "[ACTIVE_LOG_ROTATION_DEFERRED] active_log=$(basename "$active_log") size_bytes=${active_size_bytes} status=deferred_writer_active owner_status=${active_rotation_status} active_preserved=true numeric_rename_shift_prune_disabled=true cleanup_will_continue=true"
  fi
done <"$active_find_path"
rm -f "$active_find_path"

if [[ "$ACTIVE_LOG_BACKUP_COUNT" -ge "$ACTIVE_LOG_COMPRESS_MIN_INDEX" ]]; then
  archive_compression_find_path="$(mktemp "$LOG_DIR/.cleanup_find_archive_compression.XXXXXX")"
  collect_find_results "archive_compression_census" "$archive_compression_find_path" \
    "$LOG_DIR" -maxdepth 1 -type f -name '*.log.[0-9]*' || true
  while IFS= read -r -d '' archive_path; do
    archive_index="${archive_path##*.}"
    if [[ ! "$archive_index" =~ ^[0-9]+$ || "$archive_index" -lt "$ACTIVE_LOG_COMPRESS_MIN_INDEX" ]]; then
      continue
    fi
    archive_source_unlink_deferred_count=$((archive_source_unlink_deferred_count + 1))
    archive_source_unlink_deferred_bytes=$((archive_source_unlink_deferred_bytes + $(stat -c%s "$archive_path" 2>/dev/null || echo 0)))
    echo "[ARCHIVE_SOURCE_UNLINK_DEFERRED] archive=$(basename "$archive_path") status=disabled_pending_writer_owner source_authoritative=true cleanup_will_continue=true"
    if ! compress_file_verified "$archive_path" "$ARCHIVE_COMPRESSION_QUIET_SECONDS" true; then
      if compression_reason_is_writer_active "$compression_failure_reason"; then
        archive_writer_active_deferred_count=$((archive_writer_active_deferred_count + 1))
        archive_writer_active_deferred_bytes=$((archive_writer_active_deferred_bytes + $(stat -c%s "$archive_path" 2>/dev/null || echo 0)))
        register_writer_defer "numeric_archive" "$archive_path" "$compression_failure_reason"
        archive_retention_protected_paths["$archive_path"]=1
        archive_retention_protection_reasons["$archive_path"]="deferred_writer_active"
        echo "[ARCHIVE_COMPRESSION_DEFERRED] archive=$(basename "$archive_path") status=deferred_writer_active reason=${compression_failure_reason} source_preserved=true cleanup_will_continue=true"
        continue
      fi
      compression_verify_failure_count=$((compression_verify_failure_count + 1))
      archive_compression_failure_count=$((archive_compression_failure_count + 1))
      source_preserved="false"
      if [[ -f "$archive_path" ]]; then
        source_preserved="true"
        archive_compression_source_preserved_count=$((archive_compression_source_preserved_count + 1))
      fi
      archive_retention_protected_paths["$archive_path"]=1
      archive_retention_protected_paths["${archive_path}.gz"]=1
      archive_retention_protection_reasons["$archive_path"]="failed_compression_evidence_preserved"
      archive_retention_protection_reasons["${archive_path}.gz"]="failed_compression_evidence_preserved"
      if [[ -n "${compression_output_path:-}" ]]; then
        archive_retention_protected_paths["$compression_output_path"]=1
        archive_retention_protection_reasons["$compression_output_path"]="failed_compression_evidence_preserved"
      fi
      if [[ -n "${compression_preserved_existing_gzip_path:-}" ]]; then
        archive_retention_protected_paths["$compression_preserved_existing_gzip_path"]=1
        archive_retention_protection_reasons["$compression_preserved_existing_gzip_path"]="failed_compression_evidence_preserved"
      fi
      echo "[ARCHIVE_COMPRESSION_FAIL] archive=$(basename "$archive_path") reason=${compression_failure_reason} source_preserved=${source_preserved} micro_reversion_storage_status=${micro_reversion_storage_status} cleanup_will_continue=true"
      continue
    fi
    case "$compression_action" in
      verified_generation_source_preserved)
        archive_verified_existing_source_preserved_count=$((archive_verified_existing_source_preserved_count + 1))
        archive_generation_verified_count=$((archive_generation_verified_count + 1))
        ;;
      compressed_generation_source_preserved)
        compressed_archive_count=$((compressed_archive_count + 1))
        archive_generation_compressed_count=$((archive_generation_compressed_count + 1))
        ;;
      verified_existing_gzip_source_preserved)
        archive_verified_existing_source_preserved_count=$((archive_verified_existing_source_preserved_count + 1))
        ;;
      verified_collision_generation_source_preserved)
        archive_collision_reconciled_count=$((archive_collision_reconciled_count + 1))
        ;;
      compressed_collision_generation_source_preserved)
        compressed_archive_count=$((compressed_archive_count + 1))
        archive_collision_reconciled_count=$((archive_collision_reconciled_count + 1))
        ;;
      *)
        compressed_archive_count=$((compressed_archive_count + 1))
        ;;
    esac
  done <"$archive_compression_find_path"
  rm -f "$archive_compression_find_path"
fi

prune_system_metric_samples() {
  local sample_path="$LOG_DIR/system_metric_samples.jsonl"
  local lock_path="$PROJECT_DIR/tmp/system_metric_samples.lock"
  if [[ ! -f "$sample_path" ]]; then
    return 0
  fi
  system_metric_before_size="$(stat -c%s "$sample_path" 2>/dev/null || echo 0)"
  mkdir -p "$PROJECT_DIR/tmp"
  local tmp_path
  tmp_path="$(mktemp "$PROJECT_DIR/tmp/system_metric_samples.XXXXXX")"
  if ! run_with_safe_lock "$lock_path" blocking \
    "$PYTHON_BIN" - "$sample_path" "$tmp_path" "$SYSTEM_METRIC_RETENTION_DAYS" <<'PY'
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
retention_days = int(sys.argv[3])
cutoff = datetime.now().astimezone() - timedelta(days=retention_days)
invalid_path = source.with_name("system_metric_samples.invalid.jsonl")
retained = 0
pruned = 0
invalid = 0
invalid_records = []
with source.open("r", encoding="utf-8", errors="replace") as src, target.open("w", encoding="utf-8") as dst:
    for line in src:
        stripped = line.strip()
        if not stripped:
            continue
        keep = True
        try:
            payload = json.loads(stripped)
            ts = str(payload.get("ts") or "").strip()
            if ts:
                keep = datetime.fromisoformat(ts) >= cutoff
        except Exception as exc:
            invalid += 1
            invalid_records.append(
                {
                    "quarantined_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "reason": f"{type(exc).__name__}:{exc}",
                    "raw_sha256": hashlib.sha256(stripped.encode("utf-8", errors="replace")).hexdigest(),
                    "raw_line": stripped[:8192],
                    "raw_truncated": len(stripped) > 8192,
                }
            )
            continue
        if keep:
            dst.write(stripped + "\n")
            retained += 1
        else:
            pruned += 1
    dst.flush()
    os.fsync(dst.fileno())
if invalid_records:
    with invalid_path.open("a", encoding="utf-8") as quarantine:
        for record in invalid_records:
            quarantine.write(json.dumps(record, ensure_ascii=False) + "\n")
        quarantine.flush()
        os.fsync(quarantine.fileno())
os.replace(target, source)
os.chmod(source, 0o664)
print(f"{retained} {pruned} {source.stat().st_size} {invalid}")
PY
  then
    rm -f "$tmp_path"
    return 1
  fi
}

metric_prune_output=""
if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if [[ -f "$LOG_DIR/system_metric_samples.jsonl" ]]; then
    system_metric_before_size="$(stat -c%s "$LOG_DIR/system_metric_samples.jsonl" 2>/dev/null || echo 0)"
  fi
  if ! metric_prune_output="$(prune_system_metric_samples 2>/dev/null)"; then
    data_maintenance_failure_count=$((data_maintenance_failure_count + 1))
    metric_prune_output=""
    echo "[SYSTEM_METRIC_PRUNE_FAIL] source_preserved=unknown cleanup_will_continue=true"
  fi
  if [[ -n "$metric_prune_output" ]]; then
    system_metric_retained="$(echo "$metric_prune_output" | awk '{print $1}' | tail -1)"
    system_metric_pruned="$(echo "$metric_prune_output" | awk '{print $2}' | tail -1)"
    system_metric_after_size="$(echo "$metric_prune_output" | awk '{print $3}' | tail -1)"
    system_metric_invalid="$(echo "$metric_prune_output" | awk '{print $4}' | tail -1)"
  fi
fi
if [[ -f "$LOG_DIR/system_metric_samples.jsonl" ]]; then
  system_metric_after_size="$(stat -c%s "$LOG_DIR/system_metric_samples.jsonl" 2>/dev/null || echo 0)"
fi

run_data_maintenance() {
  if [[ "$DATA_MAINTENANCE_ENABLED" != "true" ]]; then
    return 0
  fi

  local maintenance_lane_failure_count=0
  local remove_rc=0
  local find_path=""
  local tmp_dir="$PROJECT_DIR/tmp"
  if [[ -d "$tmp_dir" ]]; then
    find_path="$(mktemp "$LOG_DIR/.cleanup_find_tmp.XXXXXX")"
    if ! collect_find_results "tmp_retention_census" "$find_path" \
      "$tmp_dir" -mindepth 1 -maxdepth 2 \( \
        -path "$tmp_dir/codex_worktrees/*" -o \
        -name 'workorder-*' -o \
        -name 'workorder_*' \
      \) -mtime "+$TMP_MAINTENANCE_RETENTION_DAYS" -prune; then
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
    while IFS= read -r -d '' stale_tmp_path; do
      remove_rc=0
      rm -rf -- "$stale_tmp_path" || remove_rc=$?
      if [[ ! -e "$stale_tmp_path" && ! -L "$stale_tmp_path" ]]; then
        tmp_deleted_count=$((tmp_deleted_count + 1))
        if [[ "$remove_rc" -ne 0 ]]; then
          echo "[DATA_MAINTENANCE_DELETE_ANOMALOUS_RC] lane=tmp path=${stale_tmp_path} removed=true rm_rc=${remove_rc}"
        fi
      else
        echo "[DATA_MAINTENANCE_DELETE_FAIL] lane=tmp path=${stale_tmp_path} preserved=true cleanup_will_continue=true"
        maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
      fi
    done <"$find_path"
    rm -f "$find_path"

    find_path="$(mktemp "$LOG_DIR/.cleanup_find_refactor_tmp.XXXXXX")"
    if ! collect_find_results "refactor_tmp_retention_census" "$find_path" \
      "$tmp_dir" -mindepth 1 -maxdepth 1 -type d -name 'refactor_dry_run_*' \
      -mtime "+$REFRACTOR_DRY_RUN_RETENTION_DAYS" -prune; then
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
    while IFS= read -r -d '' stale_tmp_path; do
      remove_rc=0
      rm -rf -- "$stale_tmp_path" || remove_rc=$?
      if [[ ! -e "$stale_tmp_path" && ! -L "$stale_tmp_path" ]]; then
        tmp_deleted_count=$((tmp_deleted_count + 1))
        if [[ "$remove_rc" -ne 0 ]]; then
          echo "[DATA_MAINTENANCE_DELETE_ANOMALOUS_RC] lane=refactor_tmp path=${stale_tmp_path} removed=true rm_rc=${remove_rc}"
        fi
      else
        echo "[DATA_MAINTENANCE_DELETE_FAIL] lane=refactor_tmp path=${stale_tmp_path} preserved=true cleanup_will_continue=true"
        maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
      fi
    done <"$find_path"
    rm -f "$find_path"
  fi

  find_path="$(mktemp "$LOG_DIR/.cleanup_find_cache.XXXXXX")"
  if ! collect_find_results "cache_retention_census" "$find_path" \
    "$PROJECT_DIR" -path "$PROJECT_DIR/.venv" -prune -o \( \
      -type d -name '__pycache__' -o \
      -type d -name '.pytest_cache' -o \
      -type d -name '.mypy_cache' -o \
      -type d -name '.ruff_cache' \
    \) -prune; then
    maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
  fi
  while IFS= read -r -d '' stale_cache_path; do
    remove_rc=0
    rm -rf -- "$stale_cache_path" || remove_rc=$?
    if [[ ! -e "$stale_cache_path" && ! -L "$stale_cache_path" ]]; then
      cache_deleted_count=$((cache_deleted_count + 1))
      if [[ "$remove_rc" -ne 0 ]]; then
        echo "[DATA_MAINTENANCE_DELETE_ANOMALOUS_RC] lane=cache path=${stale_cache_path} removed=true rm_rc=${remove_rc}"
      fi
    else
      echo "[DATA_MAINTENANCE_DELETE_FAIL] lane=cache path=${stale_cache_path} preserved=true cleanup_will_continue=true"
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
  done <"$find_path"
  rm -f "$find_path"

  local sentinel_dir="$PROJECT_DIR/data/runtime/sentinel_event_cache"
  if [[ -d "$sentinel_dir" ]]; then
    find_path="$(mktemp "$LOG_DIR/.cleanup_find_sentinel.XXXXXX")"
    if ! collect_find_results "sentinel_compression_census" "$find_path" \
      "$sentinel_dir" -maxdepth 1 -type f -name '*_events_*.jsonl'; then
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
    while IFS= read -r -d '' event_path; do
      if [[ "$(basename "$event_path")" == *"_${TARGET_DATE}.jsonl" ]]; then
        continue
      fi
      data_source_unlink_deferred_count=$((data_source_unlink_deferred_count + 1))
      data_source_unlink_deferred_bytes=$((data_source_unlink_deferred_bytes + $(stat -c%s "$event_path" 2>/dev/null || echo 0)))
      if ! compress_file_verified "$event_path"; then
        compression_verify_failure_count=$((compression_verify_failure_count + 1))
        maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
        echo "[DATA_COMPRESSION_FAIL] lane=sentinel path=${event_path} reason=${compression_failure_reason} source_preserved=true cleanup_will_continue=true"
        continue
      fi
      case "$compression_action" in
        compressed_copy_source_preserved)
          sentinel_compressed_count=$((sentinel_compressed_count + 1))
          ;;
        verified_existing_gzip_source_preserved)
          sentinel_verified_existing_source_preserved_count=$((sentinel_verified_existing_source_preserved_count + 1))
          ;;
        *)
          compression_verify_failure_count=$((compression_verify_failure_count + 1))
          maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
          echo "[DATA_COMPRESSION_FAIL] lane=sentinel path=${event_path} reason=unknown_success_action source_preserved=true cleanup_will_continue=true"
          ;;
      esac
    done <"$find_path"
    rm -f "$find_path"
  fi

  local snapshot_dir="$PROJECT_DIR/data/threshold_cycle/snapshots"
  if [[ -d "$snapshot_dir" ]]; then
    find_path="$(mktemp "$LOG_DIR/.cleanup_find_snapshot.XXXXXX")"
    if ! collect_find_results "snapshot_compression_census" "$find_path" \
      "$snapshot_dir" -maxdepth 1 -type f -name 'pipeline_events_*.jsonl'; then
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
    while IFS= read -r -d '' snapshot_path; do
      if [[ "$(basename "$snapshot_path")" == "pipeline_events_${TARGET_DATE}_"*".jsonl" ]]; then
        continue
      fi
      data_source_unlink_deferred_count=$((data_source_unlink_deferred_count + 1))
      data_source_unlink_deferred_bytes=$((data_source_unlink_deferred_bytes + $(stat -c%s "$snapshot_path" 2>/dev/null || echo 0)))
      if ! compress_file_verified "$snapshot_path"; then
        compression_verify_failure_count=$((compression_verify_failure_count + 1))
        maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
        echo "[DATA_COMPRESSION_FAIL] lane=snapshot path=${snapshot_path} reason=${compression_failure_reason} source_preserved=true cleanup_will_continue=true"
        continue
      fi
      case "$compression_action" in
        compressed_copy_source_preserved)
          snapshot_compressed_count=$((snapshot_compressed_count + 1))
          ;;
        verified_existing_gzip_source_preserved)
          snapshot_verified_existing_source_preserved_count=$((snapshot_verified_existing_source_preserved_count + 1))
          ;;
        *)
          compression_verify_failure_count=$((compression_verify_failure_count + 1))
          maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
          echo "[DATA_COMPRESSION_FAIL] lane=snapshot path=${snapshot_path} reason=unknown_success_action source_preserved=true cleanup_will_continue=true"
          ;;
      esac
    done <"$find_path"
    rm -f "$find_path"
  fi

  local exclusion_dir="$PROJECT_DIR/data/source_quality/raw_row_exclusion"
  if [[ -d "$exclusion_dir" ]]; then
    local previous_raw_date=""
    local previous_raw_path=""
    local raw_date=""
    find_path="$(mktemp "$LOG_DIR/.cleanup_find_raw_runs.XXXXXX")"
    if ! collect_find_results "raw_row_run_census" "$find_path" \
      "$exclusion_dir" -mindepth 1 -maxdepth 1 -type d; then
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
    while IFS= read -r -d '' raw_run_path; do
      raw_date="$(basename "$raw_run_path" | sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2})_.*/\1/')"
      if [[ -n "$previous_raw_path" && "$raw_date" == "$previous_raw_date" ]]; then
        local duplicate_run_path="$previous_raw_path"
        raw_row_exclusion_delete_deferred_count=$((raw_row_exclusion_delete_deferred_count + 1))
        raw_row_exclusion_delete_deferred_bytes=$((raw_row_exclusion_delete_deferred_bytes + $(du -sb "$duplicate_run_path" 2>/dev/null | awk '{print $1}' || echo 0)))
        echo "[RAW_ROW_EXCLUSION_DELETE_DEFERRED] lane=duplicate path=${duplicate_run_path} status=disabled_pending_storage_owner source_preserved=true cleanup_will_continue=true"
      fi
      previous_raw_date="$raw_date"
      previous_raw_path="$raw_run_path"
    done <"$find_path"
    rm -f "$find_path"

    find_path="$(mktemp "$LOG_DIR/.cleanup_find_raw_backups.XXXXXX")"
    if ! collect_find_results "raw_row_backup_census" "$find_path" \
      "$exclusion_dir" -mindepth 2 -maxdepth 2 -type f \
      -name 'pipeline_events_*.jsonl.gz' \
      -mtime "+$RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS"; then
      maintenance_lane_failure_count=$((maintenance_lane_failure_count + 1))
    fi
    while IFS= read -r -d '' backup_path; do
      raw_row_exclusion_backup_delete_deferred_count=$((raw_row_exclusion_backup_delete_deferred_count + 1))
      raw_row_exclusion_backup_delete_deferred_bytes=$((raw_row_exclusion_backup_delete_deferred_bytes + $(stat -c%s "$backup_path" 2>/dev/null || echo 0)))
      echo "[RAW_ROW_EXCLUSION_DELETE_DEFERRED] lane=backup path=${backup_path} status=disabled_pending_storage_owner source_preserved=true cleanup_will_continue=true"
    done <"$find_path"
    rm -f "$find_path"
  fi

  [[ "$maintenance_lane_failure_count" -eq 0 ]]
}

if ! run_data_maintenance; then
  data_maintenance_failure_count=$((data_maintenance_failure_count + 1))
  echo "[DATA_MAINTENANCE_FAIL] compression_verify_failures=${compression_verify_failure_count} cleanup_will_continue=true"
fi

active_deleted_count=0
active_retention_find_path="$(mktemp "$LOG_DIR/.cleanup_find_active_retention.XXXXXX")"
collect_find_results "active_retention_census" "$active_retention_find_path" \
  "$LOG_DIR" -maxdepth 1 -type f \( \
    -name '*_cron.log' -o \
    -name 'run_*.log' -o \
    -name 'threshold_cycle_*.log' -o \
    -name 'tuning_monitoring_*.log' -o \
    -name 'dashboard_db_archive_*.log' -o \
    -name 'ensemble_scanner.log' -o \
    -name 'update_kospi.log' -o \
    -name 'buy_pause_guard.log' \
  \) ! -name 'log_rotation_cleanup_cron.log' \
  -mtime "+$ACTIVE_LOG_RETENTION_DAYS" || true
while IFS= read -r -d '' expired_active_path; do
  active_log_retention_deferred_count=$((active_log_retention_deferred_count + 1))
  active_log_retention_deferred_bytes=$((active_log_retention_deferred_bytes + $(stat -c%s "$expired_active_path" 2>/dev/null || echo 0)))
  echo "[ACTIVE_LOG_RETENTION_DEFERRED] active_log=$(basename "$expired_active_path") status=disabled_pending_writer_owner source_preserved=true"
done <"$active_retention_find_path"
rm -f "$active_retention_find_path"

deleted_count=0
archive_retention_find_path="$(mktemp "$LOG_DIR/.cleanup_find_archive_retention.XXXXXX")"
collect_find_results "archive_retention_census" "$archive_retention_find_path" \
  "${archive_log_find_args[@]}" -mtime "+$RETENTION_DAYS" || true
while IFS= read -r -d '' expired_archive_path; do
  if [[ -n "${archive_retention_protected_paths[$expired_archive_path]:-}" ]]; then
    archive_retention_protected_count=$((archive_retention_protected_count + 1))
  fi
  archive_retention_deferred_count=$((archive_retention_deferred_count + 1))
  archive_retention_deferred_bytes=$((archive_retention_deferred_bytes + $(stat -c%s "$expired_archive_path" 2>/dev/null || echo 0)))
  echo "[ARCHIVE_RETENTION_DEFERRED] archive=$(basename "$expired_archive_path") status=disabled_pending_writer_owner source_preserved=true reason=${archive_retention_protection_reasons[$expired_archive_path]:-unknown_writer_owner}"
done <"$archive_retention_find_path"
rm -f "$archive_retention_find_path"

after_count=0
after_archive_find_path="$(mktemp "$LOG_DIR/.cleanup_find_after.XXXXXX")"
if collect_find_results "archive_final_census" "$after_archive_find_path" "${archive_log_find_args[@]}"; then
  after_count="$(tr -cd '\0' <"$after_archive_find_path" | wc -c | tr -d ' ')"
fi
rm -f "$after_archive_find_path"
after_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"

update_writer_defer_state || true

echo "[DATA_COMPRESSION] sentinel_compressed=$sentinel_compressed_count sentinel_verified_existing_source_preserved=$sentinel_verified_existing_source_preserved_count snapshot_compressed=$snapshot_compressed_count snapshot_verified_existing_source_preserved=$snapshot_verified_existing_source_preserved_count source_unlink_deferred=$data_source_unlink_deferred_count source_unlink_deferred_bytes=$data_source_unlink_deferred_bytes"
echo "[LOG_CLEANUP] archive_retention_days=$RETENTION_DAYS active_log_retention_days=$ACTIVE_LOG_RETENTION_DAYS active_log_compress_min_index=$ACTIVE_LOG_COMPRESS_MIN_INDEX archive_compression_quiet_seconds=$ARCHIVE_COMPRESSION_QUIET_SECONDS writer_defer_failure_threshold=$WRITER_DEFER_FAILURE_THRESHOLD writer_defer_tracked=$writer_defer_tracked_count writer_defer_escalated=$writer_defer_escalated_count writer_defer_max_consecutive=$writer_defer_max_consecutive writer_defer_state_failures=$writer_defer_state_failure_count system_metric_retention_days=$SYSTEM_METRIC_RETENTION_DAYS raw_row_exclusion_backup_retention_days=$RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS active_rotation_status=$active_rotation_status active_rotation_deferred=$active_rotation_deferred_count active_rotated=$rotated_active_count active_retention_failures=$active_log_retention_failure_count active_retention_deferred=$active_log_retention_deferred_count active_retention_deferred_bytes=$active_log_retention_deferred_bytes active_deleted=$active_deleted_count archive_deleted=$deleted_count archive_compressed=$compressed_archive_count archive_compression_finalized=$archive_compression_finalized_count archive_verified_existing_source_preserved=$archive_verified_existing_source_preserved_count archive_collision_reconciled=$archive_collision_reconciled_count archive_generation_compressed=$archive_generation_compressed_count archive_generation_verified=$archive_generation_verified_count archive_compression_failures=$archive_compression_failure_count archive_compression_sources_preserved=$archive_compression_source_preserved_count archive_writer_active_deferred=$archive_writer_active_deferred_count archive_writer_active_deferred_bytes=$archive_writer_active_deferred_bytes archive_source_unlink_deferred=$archive_source_unlink_deferred_count archive_source_unlink_deferred_bytes=$archive_source_unlink_deferred_bytes archive_retention_failures=$archive_retention_failure_count archive_retention_deferred=$archive_retention_deferred_count archive_retention_deferred_bytes=$archive_retention_deferred_bytes archive_retention_protected=$archive_retention_protected_count archive_pruned_to_backup_limit=$archive_pruned_to_backup_limit_count archive_before=$before_count archive_after=$after_count size_before=$before_size size_after=$after_size find_enumeration_failures=$find_enumeration_failure_count system_metric_retained=$system_metric_retained system_metric_pruned=$system_metric_pruned system_metric_invalid=$system_metric_invalid system_metric_size_before=$system_metric_before_size system_metric_size_after=$system_metric_after_size data_maintenance_enabled=$DATA_MAINTENANCE_ENABLED data_maintenance_failures=$data_maintenance_failure_count tmp_deleted=$tmp_deleted_count cache_deleted=$cache_deleted_count sentinel_compressed=$sentinel_compressed_count snapshot_compressed=$snapshot_compressed_count data_source_unlink_deferred=$data_source_unlink_deferred_count data_source_unlink_deferred_bytes=$data_source_unlink_deferred_bytes compression_verify_failures=$compression_verify_failure_count raw_row_exclusion_deleted=$raw_row_exclusion_deleted_count raw_row_exclusion_delete_deferred=$raw_row_exclusion_delete_deferred_count raw_row_exclusion_delete_deferred_bytes=$raw_row_exclusion_delete_deferred_bytes raw_row_exclusion_backup_deleted=$raw_row_exclusion_backup_deleted_count raw_row_exclusion_backup_delete_deferred=$raw_row_exclusion_backup_delete_deferred_count raw_row_exclusion_backup_delete_deferred_bytes=$raw_row_exclusion_backup_delete_deferred_bytes micro_reversion_storage_status=$micro_reversion_storage_status micro_reversion_storage_failures=$micro_reversion_storage_failure_count micro_reversion_storage_partition_failures=$micro_reversion_storage_partition_failure_count micro_reversion_storage_failed_candidates=$micro_reversion_storage_failed_candidate_count micro_reversion_storage_failed_candidate_bytes=$micro_reversion_storage_failed_candidate_bytes micro_reversion_storage_recovery_required=$micro_reversion_storage_recovery_required_count micro_reversion_storage_actions=$micro_reversion_storage_action_count micro_reversion_storage_compressed=$micro_reversion_storage_compressed_count micro_reversion_storage_purged=$micro_reversion_storage_purged_count micro_reversion_storage_purge_partial=$micro_reversion_storage_purge_partial_count micro_reversion_storage_source_bytes=$micro_reversion_storage_source_bytes micro_reversion_storage_purge_enabled=$micro_reversion_storage_purge_enabled micro_reversion_storage_purge_status=$micro_reversion_storage_purge_status micro_reversion_storage_purge_candidates=$micro_reversion_storage_purge_candidate_count micro_reversion_storage_purge_candidate_bytes=$micro_reversion_storage_purge_candidate_bytes"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
if [[ "$writer_defer_escalated_count" -gt 0 || "$writer_defer_state_failure_count" -gt 0 || "$active_log_retention_failure_count" -gt 0 || "$archive_compression_failure_count" -gt 0 || "$archive_retention_failure_count" -gt 0 || "$data_maintenance_failure_count" -gt 0 || "$micro_reversion_storage_failure_count" -gt 0 || "$find_enumeration_failure_count" -gt 0 ]]; then
  echo "[FAIL] log_rotation_cleanup target_date=${TARGET_DATE} active_rotation_status=${active_rotation_status} active_rotation_deferred=${active_rotation_deferred_count} writer_defer_escalated=${writer_defer_escalated_count} writer_defer_max_consecutive=${writer_defer_max_consecutive} writer_defer_state_failures=${writer_defer_state_failure_count} active_retention_failures=${active_log_retention_failure_count} archive_compression_failures=${archive_compression_failure_count} archive_compression_sources_preserved=${archive_compression_source_preserved_count} archive_writer_active_deferred=${archive_writer_active_deferred_count} archive_retention_failures=${archive_retention_failure_count} archive_retention_protected=${archive_retention_protected_count} find_enumeration_failures=${find_enumeration_failure_count} data_maintenance_failures=${data_maintenance_failure_count} micro_reversion_storage_status=${micro_reversion_storage_status} micro_reversion_storage_failures=${micro_reversion_storage_failure_count} micro_reversion_storage_partition_failures=${micro_reversion_storage_partition_failure_count} micro_reversion_storage_failed_candidates=${micro_reversion_storage_failed_candidate_count} micro_reversion_storage_failed_candidate_bytes=${micro_reversion_storage_failed_candidate_bytes} micro_reversion_storage_recovery_required=${micro_reversion_storage_recovery_required_count} compression_verify_failures=${compression_verify_failure_count} finished_at=${finished_at}"
  trap - ERR
  exit 1
fi
echo "[DONE] log_rotation_cleanup target_date=${TARGET_DATE} archive_retention_days=${RETENTION_DAYS} active_log_retention_days=${ACTIVE_LOG_RETENTION_DAYS} active_log_compress_min_index=${ACTIVE_LOG_COMPRESS_MIN_INDEX} archive_compression_quiet_seconds=${ARCHIVE_COMPRESSION_QUIET_SECONDS} writer_defer_failure_threshold=${WRITER_DEFER_FAILURE_THRESHOLD} writer_defer_tracked=${writer_defer_tracked_count} writer_defer_escalated=${writer_defer_escalated_count} writer_defer_max_consecutive=${writer_defer_max_consecutive} writer_defer_state_failures=${writer_defer_state_failure_count} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} raw_row_exclusion_backup_retention_days=${RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS} active_rotation_status=${active_rotation_status} active_rotation_deferred=${active_rotation_deferred_count} active_rotated=${rotated_active_count} active_retention_failures=${active_log_retention_failure_count} active_retention_deferred=${active_log_retention_deferred_count} active_retention_deferred_bytes=${active_log_retention_deferred_bytes} active_deleted=${active_deleted_count} archive_deleted=$deleted_count archive_compressed=$compressed_archive_count archive_compression_finalized=$archive_compression_finalized_count archive_verified_existing_source_preserved=$archive_verified_existing_source_preserved_count archive_collision_reconciled=$archive_collision_reconciled_count archive_generation_compressed=$archive_generation_compressed_count archive_generation_verified=$archive_generation_verified_count archive_compression_failures=$archive_compression_failure_count archive_compression_sources_preserved=$archive_compression_source_preserved_count archive_writer_active_deferred=$archive_writer_active_deferred_count archive_writer_active_deferred_bytes=$archive_writer_active_deferred_bytes archive_source_unlink_deferred=$archive_source_unlink_deferred_count archive_source_unlink_deferred_bytes=$archive_source_unlink_deferred_bytes archive_retention_failures=$archive_retention_failure_count archive_retention_deferred=$archive_retention_deferred_count archive_retention_deferred_bytes=$archive_retention_deferred_bytes archive_retention_protected=$archive_retention_protected_count archive_pruned_to_backup_limit=$archive_pruned_to_backup_limit_count find_enumeration_failures=$find_enumeration_failure_count system_metric_pruned=$system_metric_pruned system_metric_invalid=$system_metric_invalid data_maintenance_enabled=$DATA_MAINTENANCE_ENABLED data_maintenance_failures=$data_maintenance_failure_count tmp_deleted=$tmp_deleted_count cache_deleted=$cache_deleted_count sentinel_compressed=$sentinel_compressed_count snapshot_compressed=$snapshot_compressed_count data_source_unlink_deferred=$data_source_unlink_deferred_count data_source_unlink_deferred_bytes=$data_source_unlink_deferred_bytes compression_verify_failures=$compression_verify_failure_count raw_row_exclusion_deleted=$raw_row_exclusion_deleted_count raw_row_exclusion_delete_deferred=$raw_row_exclusion_delete_deferred_count raw_row_exclusion_delete_deferred_bytes=$raw_row_exclusion_delete_deferred_bytes raw_row_exclusion_backup_deleted=$raw_row_exclusion_backup_deleted_count raw_row_exclusion_backup_delete_deferred=$raw_row_exclusion_backup_delete_deferred_count raw_row_exclusion_backup_delete_deferred_bytes=$raw_row_exclusion_backup_delete_deferred_bytes micro_reversion_storage_status=$micro_reversion_storage_status micro_reversion_storage_failures=$micro_reversion_storage_failure_count micro_reversion_storage_partition_failures=$micro_reversion_storage_partition_failure_count micro_reversion_storage_failed_candidates=$micro_reversion_storage_failed_candidate_count micro_reversion_storage_failed_candidate_bytes=$micro_reversion_storage_failed_candidate_bytes micro_reversion_storage_recovery_required=$micro_reversion_storage_recovery_required_count micro_reversion_storage_actions=$micro_reversion_storage_action_count micro_reversion_storage_compressed=$micro_reversion_storage_compressed_count micro_reversion_storage_purged=$micro_reversion_storage_purged_count micro_reversion_storage_source_bytes=$micro_reversion_storage_source_bytes micro_reversion_storage_purge_enabled=$micro_reversion_storage_purge_enabled micro_reversion_storage_purge_status=$micro_reversion_storage_purge_status micro_reversion_storage_purge_candidates=$micro_reversion_storage_purge_candidate_count micro_reversion_storage_purge_candidate_bytes=$micro_reversion_storage_purge_candidate_bytes finished_at=$finished_at"
