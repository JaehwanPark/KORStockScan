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
if [[ "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" != "true" && "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" != "false" ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion storage purge enabled must be true or false: $MICRO_REVERSION_STORAGE_PURGE_ENABLED"
  exit 2
fi
if [[ "$MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED" != "true" && "$MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED" != "false" ]]; then
  echo "[LOG_CLEANUP_ERROR] micro-reversion storage maintenance enabled must be true or false: $MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED"
  exit 2
fi

mkdir -p "$LOG_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] log_rotation_cleanup target_date=${TARGET_DATE} archive_retention_days=${RETENTION_DAYS} active_log_retention_days=${ACTIVE_LOG_RETENTION_DAYS} active_log_compress_min_index=${ACTIVE_LOG_COMPRESS_MIN_INDEX} archive_compression_quiet_seconds=${ARCHIVE_COMPRESSION_QUIET_SECONDS} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} raw_row_exclusion_backup_retention_days=${RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS} active_log_max_bytes=${ACTIVE_LOG_MAX_BYTES} active_log_backup_count=${ACTIVE_LOG_BACKUP_COUNT} data_maintenance_enabled=${DATA_MAINTENANCE_ENABLED} micro_reversion_storage_maintenance_enabled=${MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED} micro_reversion_storage_purge_enabled=${MICRO_REVERSION_STORAGE_PURGE_ENABLED} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] log_rotation_cleanup target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

archive_log_find_args=(
  "$LOG_DIR" -maxdepth 1 -type f
  \( -name '*.log.[0-9]*' -o -name '*.log.before_*' \)
)
before_count="$(find "${archive_log_find_args[@]}" | wc -l | tr -d ' ')"
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
raw_row_exclusion_deleted_count=0
raw_row_exclusion_backup_deleted_count=0
micro_reversion_storage_action_count=0
micro_reversion_storage_compressed_count=0
micro_reversion_storage_purged_count=0
micro_reversion_storage_source_bytes=0
micro_reversion_storage_status="disabled"
micro_reversion_storage_purge_enabled="$MICRO_REVERSION_STORAGE_PURGE_ENABLED"
micro_reversion_storage_purge_status="maintenance_disabled"
micro_reversion_storage_purge_candidate_count=0
micro_reversion_storage_purge_candidate_bytes=0
micro_reversion_storage_failure_count=0
compressed_archive_count=0
archive_compression_finalized_count=0
archive_collision_reconciled_count=0
archive_compression_failure_count=0
archive_compression_source_preserved_count=0
archive_retention_protected_count=0
archive_pruned_to_backup_limit_count=0
compression_verify_failure_count=0
data_maintenance_failure_count=0
compression_failure_reason="not_run"
compression_action="not_run"
declare -A archive_retention_protected_paths=()
declare -A archive_retention_protection_reasons=()

run_micro_reversion_storage_maintenance() {
  if [[ "$MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED" != "true" ]]; then
    micro_reversion_storage_status="disabled"
    micro_reversion_storage_purge_status="maintenance_disabled"
    return 0
  fi
  micro_reversion_storage_purge_status="pending"

  mkdir -p "$PROJECT_DIR/tmp"
  local result_path lock_path
  result_path="$(mktemp "$PROJECT_DIR/tmp/micro_reversion_storage_maintenance.XXXXXX.json")"
  lock_path="$PROJECT_DIR/tmp/micro_reversion_storage_maintenance.lock"
  exec 9>"$lock_path"
  if ! flock -n 9; then
    rm -f "$result_path"
    exec 9>&-
    micro_reversion_storage_status="lock_busy"
    micro_reversion_storage_purge_status="not_run_lock_busy"
    return 0
  fi
  if ! (
    cd "$KORSTOCKSCAN_CODE_ROOT"
    export PYTHONPATH="$KORSTOCKSCAN_CODE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
    maintenance_command=(
      "$PYTHON_BIN"
      -m src.engine.scalping.micro_reversion.storage_maintenance
      --root "$MICRO_REVERSION_STORAGE_ROOT"
      --as-of-date "$TARGET_DATE"
      --apply
    )
    if [[ "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" == "true" ]]; then
      maintenance_command+=(--purge-expired)
    fi
    if command -v ionice >/dev/null 2>&1; then
      ionice -c 3 nice -n "$MICRO_REVERSION_STORAGE_NICE_LEVEL" \
        "${maintenance_command[@]}"
    else
      nice -n "$MICRO_REVERSION_STORAGE_NICE_LEVEL" \
        "${maintenance_command[@]}"
    fi
  ) >"$result_path"; then
    flock -u 9
    exec 9>&-
    rm -f "$result_path"
    micro_reversion_storage_status="failed"
    micro_reversion_storage_purge_status="execution_failed"
    return 1
  fi

  local parsed
  if ! parsed="$("$PYTHON_BIN" - "$result_path" <<'PY'
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
if any(not isinstance(row, dict) or row.get("applied") is not True for row in actions):
    raise SystemExit("storage maintenance apply action census is invalid")
compressed = sum(
    row.get("action") in {"compress_jsonl", "finalize_verified_compression"}
    for row in actions
    if isinstance(row, dict)
)
purged = sum(row.get("action") == "purge_trade_date" for row in actions if isinstance(row, dict))
purge_enabled = payload.get("purge_enabled")
purge_status = payload.get("purge_status")
if not isinstance(purge_enabled, bool):
    raise SystemExit("storage maintenance purge authority is invalid")
expected_purge_status = (
    "explicit_opt_in_apply" if purge_enabled else "disabled_no_deletion_authority"
)
if purge_status != expected_purge_status:
    raise SystemExit("storage maintenance purge status is invalid")
if not purge_enabled and purged:
    raise SystemExit("storage maintenance purged without explicit authority")
if int(payload.get("purge_applied_count") or 0) != purged:
    raise SystemExit("storage maintenance purge applied census mismatch")
deletion_performed = payload.get("deletion_performed")
if not isinstance(deletion_performed, bool):
    raise SystemExit("storage maintenance deletion status type is invalid")
if deletion_performed != bool(purged):
    raise SystemExit("storage maintenance deletion status mismatch")
for field in ("purge_candidate_count", "purge_candidate_bytes"):
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SystemExit(f"storage maintenance {field} is invalid")
print(
    int(payload.get("action_count") or 0),
    compressed,
    purged,
    int(payload.get("source_bytes") or 0),
    "true" if purge_enabled else "false",
    purge_status,
    int(payload.get("purge_candidate_count") or 0),
    int(payload.get("purge_candidate_bytes") or 0),
)
PY
  )"; then
    flock -u 9
    exec 9>&-
    rm -f "$result_path"
    micro_reversion_storage_status="invalid_result"
    micro_reversion_storage_purge_status="invalid_result"
    return 1
  fi
  read -r \
    micro_reversion_storage_action_count \
    micro_reversion_storage_compressed_count \
    micro_reversion_storage_purged_count \
    micro_reversion_storage_source_bytes \
    micro_reversion_storage_purge_enabled \
    micro_reversion_storage_purge_status \
    micro_reversion_storage_purge_candidate_count \
    micro_reversion_storage_purge_candidate_bytes <<<"$parsed"
  if [[ "$micro_reversion_storage_purge_enabled" != "$MICRO_REVERSION_STORAGE_PURGE_ENABLED" ]]; then
    flock -u 9
    exec 9>&-
    rm -f "$result_path"
    micro_reversion_storage_status="purge_authority_mismatch"
    micro_reversion_storage_purge_status="authority_mismatch"
    return 1
  fi
  flock -u 9
  exec 9>&-
  rm -f "$result_path"
  micro_reversion_storage_status="pass"
}

compress_file_verified() {
  local source_path="$1"
  local quiet_seconds="${2:-0}"
  local collision_generation_enabled="${3:-false}"
  local standard_gzip_path="${source_path}.gz"
  local gzip_path="$standard_gzip_path"
  local tmp_path=""
  local source_size source_mtime_epoch now_epoch source_quiet_age restored_size
  local source_metadata source_sha256 restored_sha256 verified_metadata verified_sha256
  local existing_gzip_sha256 collision_gzip_sha256
  compression_failure_reason="unknown"
  compression_action="failed"
  compression_output_path="$standard_gzip_path"
  compression_preserved_existing_gzip_path=""
  if [[ ! -f "$source_path" ]]; then
    compression_failure_reason="source_missing_before_compression"
    return 1
  fi
  if command -v fuser >/dev/null 2>&1 && fuser -s "$source_path"; then
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

  if [[ -f "$standard_gzip_path" ]]; then
    if ! gzip -t -- "$standard_gzip_path"; then
      compression_failure_reason="existing_gzip_invalid_conflict"
      return 1
    fi
    if ! existing_gzip_sha256="$(gzip -cd -- "$standard_gzip_path" | sha256sum | awk '{print $1}')"; then
      compression_failure_reason="existing_gzip_restore_hash_failed"
      return 1
    fi
    if [[ "$existing_gzip_sha256" == "$source_sha256" ]]; then
      if ! verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path")"; then
        compression_failure_reason="source_missing_before_existing_finalize"
        return 1
      fi
      if ! verified_sha256="$(sha256sum -- "$source_path" | awk '{print $1}')"; then
        compression_failure_reason="source_recheck_hash_failed"
        return 1
      fi
      if [[ "$verified_metadata" != "$source_metadata" || "$verified_sha256" != "$source_sha256" ]]; then
        compression_failure_reason="source_changed_before_existing_finalize"
        return 1
      fi
      if command -v fuser >/dev/null 2>&1 && fuser -s "$source_path"; then
        compression_failure_reason="source_in_use_before_existing_finalize"
        return 1
      fi
      if ! rm -f -- "$source_path"; then
        compression_failure_reason="source_unlink_failed"
        return 1
      fi
      compression_failure_reason="none"
      compression_action="finalized_existing_gzip"
      return 0
    fi
    if [[ "$collision_generation_enabled" != "true" ]]; then
      compression_failure_reason="existing_gzip_content_conflict"
      return 1
    fi

    compression_preserved_existing_gzip_path="$standard_gzip_path"
    gzip_path="${source_path}.generation_${source_sha256:0:16}.gz"
    compression_output_path="$gzip_path"
    if [[ -f "$gzip_path" ]]; then
      if ! gzip -t -- "$gzip_path"; then
        compression_failure_reason="collision_generation_gzip_invalid"
        return 1
      fi
      if ! collision_gzip_sha256="$(gzip -cd -- "$gzip_path" | sha256sum | awk '{print $1}')"; then
        compression_failure_reason="collision_generation_restore_hash_failed"
        return 1
      fi
      if [[ "$collision_gzip_sha256" != "$source_sha256" ]]; then
        compression_failure_reason="collision_generation_hash_mismatch"
        return 1
      fi
      if ! verified_metadata="$(stat -c '%d:%i:%s:%Y:%y' "$source_path")"; then
        compression_failure_reason="source_missing_before_collision_finalize"
        return 1
      fi
      if ! verified_sha256="$(sha256sum -- "$source_path" | awk '{print $1}')"; then
        compression_failure_reason="source_recheck_hash_failed"
        return 1
      fi
      if [[ "$verified_metadata" != "$source_metadata" || "$verified_sha256" != "$source_sha256" ]]; then
        compression_failure_reason="source_changed_before_collision_finalize"
        return 1
      fi
      if command -v fuser >/dev/null 2>&1 && fuser -s "$source_path"; then
        compression_failure_reason="source_in_use_before_collision_finalize"
        return 1
      fi
      if ! rm -f -- "$source_path"; then
        compression_failure_reason="source_unlink_failed"
        return 1
      fi
      compression_failure_reason="none"
      compression_action="finalized_collision_generation"
      return 0
    fi
  fi

  tmp_path="${gzip_path}.tmp.$$"
  rm -f "$tmp_path"
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
  if command -v fuser >/dev/null 2>&1 && fuser -s "$source_path"; then
    compression_failure_reason="source_in_use_after_compression"
    rm -f "$tmp_path"
    return 1
  fi
  if ! mv -f -- "$tmp_path" "$gzip_path"; then
    compression_failure_reason="gzip_publish_failed"
    rm -f "$tmp_path"
    return 1
  fi
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
  if command -v fuser >/dev/null 2>&1 && fuser -s "$source_path"; then
    compression_failure_reason="source_in_use_after_gzip_publish"
    return 1
  fi
  if ! rm -f -- "$source_path"; then
    compression_failure_reason="source_unlink_failed"
    return 1
  fi
  compression_failure_reason="none"
  if [[ -n "$compression_preserved_existing_gzip_path" ]]; then
    compression_action="compressed_collision_generation"
  else
    compression_action="compressed_new_gzip"
  fi
}

# Run the high-volume closed-date storage compaction before generic log archive
# work. A concurrently growing rotated log must never prevent this independent
# storage-only maintenance lane from running.
if [[ "$DATA_MAINTENANCE_ENABLED" == "true" ]]; then
  if ! run_micro_reversion_storage_maintenance; then
    micro_reversion_storage_failure_count=$((micro_reversion_storage_failure_count + 1))
    echo "[MICRO_REVERSION_STORAGE_FAIL] status=${micro_reversion_storage_status} purge_status=${micro_reversion_storage_purge_status} generic_cleanup_will_continue=true"
  else
    echo "[MICRO_REVERSION_STORAGE] status=${micro_reversion_storage_status} actions=${micro_reversion_storage_action_count} compressed=${micro_reversion_storage_compressed_count} purged=${micro_reversion_storage_purged_count} purge_enabled=${micro_reversion_storage_purge_enabled} purge_status=${micro_reversion_storage_purge_status} runtime_effect=false order_authority=false"
  fi
fi

shift_log_backup_slot() {
  local base_path="$1"
  local from_idx="$2"
  local to_idx="$3"
  local from_plain="${base_path}.${from_idx}"
  local from_gz="${from_plain}.gz"
  local to_plain="${base_path}.${to_idx}"
  local to_gz="${to_plain}.gz"

  rm -f "$to_plain" "$to_gz"
  if [[ -f "$from_gz" ]]; then
    mv -f "$from_gz" "$to_gz"
    return 0
  fi
  if [[ -f "$from_plain" ]]; then
    mv -f "$from_plain" "$to_plain"
  fi
}

prune_log_backup_slots_beyond_limit() {
  local base_path="$1"
  local entry_path
  local entry_index

  while IFS= read -r -d '' entry_path; do
    entry_index="${entry_path##*.log.}"
    entry_index="${entry_index%.gz}"
    if [[ ! "$entry_index" =~ ^[0-9]+$ || "$entry_index" -le "$ACTIVE_LOG_BACKUP_COUNT" ]]; then
      continue
    fi
    rm -f "$entry_path"
    archive_pruned_to_backup_limit_count=$((archive_pruned_to_backup_limit_count + 1))
  done < <(
    find "$LOG_DIR" -maxdepth 1 -type f \
      \( -name "$(basename "$base_path").[0-9]*" -o -name "$(basename "$base_path").[0-9]*.gz" \) \
      -print0 | sort -z
  )
}

rotate_active_log_if_needed() {
  local log_path="$1"
  if [[ ! -f "$log_path" ]]; then
    return 0
  fi
  if [[ "$(basename "$log_path")" == "log_rotation_cleanup_cron.log" ]]; then
    return 0
  fi
  local size_bytes
  size_bytes="$(stat -c%s "$log_path" 2>/dev/null || echo 0)"
  if [[ "$size_bytes" -lt "$ACTIVE_LOG_MAX_BYTES" ]]; then
    return 0
  fi

  local idx prev
  if [[ "$ACTIVE_LOG_BACKUP_COUNT" -gt 1 ]]; then
    for ((idx=ACTIVE_LOG_BACKUP_COUNT; idx>=2; idx--)); do
      prev=$((idx - 1))
      shift_log_backup_slot "$log_path" "$prev" "$idx"
    done
  fi
  mv -f "$log_path" "${log_path}.1"
  : > "$log_path"
  prune_log_backup_slots_beyond_limit "$log_path"
  echo "[LOG_ROTATE] active_log=$(basename "$log_path") size_bytes=${size_bytes} rotated_to=$(basename "$log_path").1"
}

rotated_active_count=0
while IFS= read -r active_log; do
  before_inode=""
  if [[ -f "$active_log" ]]; then
    before_inode="$(stat -c%i "$active_log" 2>/dev/null || true)"
  fi
  rotate_active_log_if_needed "$active_log"
  after_inode=""
  if [[ -f "$active_log" ]]; then
    after_inode="$(stat -c%i "$active_log" 2>/dev/null || true)"
  fi
  if [[ -n "$before_inode" && -n "$after_inode" && "$before_inode" != "$after_inode" ]]; then
    rotated_active_count=$((rotated_active_count + 1))
  fi
done < <(
  find "$LOG_DIR" -maxdepth 1 -type f \( \
    -name '*_cron.log' -o \
    -name 'run_*.log' -o \
    -name 'threshold_cycle_*.log' -o \
    -name 'tuning_monitoring_*.log' -o \
    -name 'dashboard_db_archive_*.log' -o \
    -name 'ensemble_scanner.log' -o \
    -name 'update_kospi.log' -o \
    -name 'buy_pause_guard.log' \
  \) | sort
)

if [[ "$ACTIVE_LOG_BACKUP_COUNT" -ge "$ACTIVE_LOG_COMPRESS_MIN_INDEX" ]]; then
  while IFS= read -r -d '' archive_path; do
    archive_index="${archive_path##*.}"
    if [[ ! "$archive_index" =~ ^[0-9]+$ || "$archive_index" -lt "$ACTIVE_LOG_COMPRESS_MIN_INDEX" ]]; then
      continue
    fi
    if ! compress_file_verified "$archive_path" "$ARCHIVE_COMPRESSION_QUIET_SECONDS" true; then
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
      finalized_existing_gzip)
        archive_compression_finalized_count=$((archive_compression_finalized_count + 1))
        ;;
      compressed_collision_generation)
        compressed_archive_count=$((compressed_archive_count + 1))
        archive_collision_reconciled_count=$((archive_collision_reconciled_count + 1))
        archive_retention_protected_paths["$compression_preserved_existing_gzip_path"]=1
        archive_retention_protection_reasons["$compression_preserved_existing_gzip_path"]="reconciled_existing_generation_preserved"
        echo "[ARCHIVE_COLLISION_RECONCILED] archive=$(basename "$archive_path") existing_gzip=$(basename "$compression_preserved_existing_gzip_path") generation_gzip=$(basename "$compression_output_path") action=${compression_action}"
        ;;
      finalized_collision_generation)
        archive_compression_finalized_count=$((archive_compression_finalized_count + 1))
        archive_collision_reconciled_count=$((archive_collision_reconciled_count + 1))
        archive_retention_protected_paths["$compression_preserved_existing_gzip_path"]=1
        archive_retention_protection_reasons["$compression_preserved_existing_gzip_path"]="reconciled_existing_generation_preserved"
        echo "[ARCHIVE_COLLISION_RECONCILED] archive=$(basename "$archive_path") existing_gzip=$(basename "$compression_preserved_existing_gzip_path") generation_gzip=$(basename "$compression_output_path") action=${compression_action}"
        ;;
      *)
        compressed_archive_count=$((compressed_archive_count + 1))
        ;;
    esac
  done < <(
    find "$LOG_DIR" -maxdepth 1 -type f -name '*.log.[0-9]*' -print0 | sort -z
  )
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
  exec 8>"$lock_path"
  flock 8
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
}

metric_prune_output=""
if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if [[ -f "$LOG_DIR/system_metric_samples.jsonl" ]]; then
    system_metric_before_size="$(stat -c%s "$LOG_DIR/system_metric_samples.jsonl" 2>/dev/null || echo 0)"
  fi
  metric_prune_output="$(prune_system_metric_samples 2>/dev/null)"
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

  local tmp_dir="$PROJECT_DIR/tmp"
  if [[ -d "$tmp_dir" ]]; then
    tmp_deleted_count="$(
      {
        find "$tmp_dir" -mindepth 1 -maxdepth 2 \( \
          -path "$tmp_dir/codex_worktrees/*" -o \
          -name 'workorder-*' -o \
          -name 'workorder_*' \
        \) -mtime "+$TMP_MAINTENANCE_RETENTION_DAYS" -print -exec rm -rf {} + 2>/dev/null || true
        find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d -name 'refactor_dry_run_*' -mtime "+$REFRACTOR_DRY_RUN_RETENTION_DAYS" -print -exec rm -rf {} + 2>/dev/null || true
      } | wc -l | tr -d ' '
    )"
  fi

  cache_deleted_count="$(
    {
      find "$PROJECT_DIR" -path "$PROJECT_DIR/.venv" -prune -o \( \
        -type d -name '__pycache__' -o \
        -type d -name '.pytest_cache' -o \
        -type d -name '.mypy_cache' -o \
        -type d -name '.ruff_cache' \
      \) -prune -print -exec rm -rf {} + 2>/dev/null || true
    } | wc -l | tr -d ' '
  )"

  local sentinel_dir="$PROJECT_DIR/data/runtime/sentinel_event_cache"
  if [[ -d "$sentinel_dir" ]]; then
    while IFS= read -r -d '' event_path; do
      if [[ "$(basename "$event_path")" == *"_${TARGET_DATE}.jsonl" ]]; then
        continue
      fi
      if ! compress_file_verified "$event_path"; then
        compression_verify_failure_count=$((compression_verify_failure_count + 1))
        return 1
      fi
      sentinel_compressed_count=$((sentinel_compressed_count + 1))
    done < <(find "$sentinel_dir" -maxdepth 1 -type f -name '*_events_*.jsonl' -print0 | sort -z)
  fi

  local snapshot_dir="$PROJECT_DIR/data/threshold_cycle/snapshots"
  if [[ -d "$snapshot_dir" ]]; then
    while IFS= read -r -d '' snapshot_path; do
      if [[ "$(basename "$snapshot_path")" == "pipeline_events_${TARGET_DATE}_"*".jsonl" ]]; then
        continue
      fi
      if ! compress_file_verified "$snapshot_path"; then
        compression_verify_failure_count=$((compression_verify_failure_count + 1))
        return 1
      fi
      snapshot_compressed_count=$((snapshot_compressed_count + 1))
    done < <(find "$snapshot_dir" -maxdepth 1 -type f -name 'pipeline_events_*.jsonl' -print0 | sort -z)
  fi

  local exclusion_dir="$PROJECT_DIR/data/source_quality/raw_row_exclusion"
  if [[ -d "$exclusion_dir" ]]; then
    while IFS= read -r source_date; do
      [[ -n "$source_date" ]] || continue
      mapfile -t runs < <(find "$exclusion_dir" -mindepth 1 -maxdepth 1 -type d -name "${source_date}_*" -printf '%f\n' | sort)
      if [[ "${#runs[@]}" -le 1 ]]; then
        continue
      fi
      local idx
      for ((idx=0; idx<${#runs[@]}-1; idx++)); do
        rm -rf "$exclusion_dir/${runs[$idx]}"
        raw_row_exclusion_deleted_count=$((raw_row_exclusion_deleted_count + 1))
      done
    done < <(find "$exclusion_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2})_.*/\1/' | sort -u)

    while IFS= read -r -d '' backup_path; do
      local manifest_path
      manifest_path="$(dirname "$backup_path")/manifest.json"
      rm -f "$backup_path"
      if [[ -f "$manifest_path" ]]; then
        "$PYTHON_BIN" - "$manifest_path" "$backup_path" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

manifest_path = Path(sys.argv[1])
backup_path = sys.argv[2]
try:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
if isinstance(payload, dict) and payload.get("backup_path") == backup_path:
    payload["backup_path"] = None
    payload["backup_retention_expired"] = True
    payload["backup_deleted_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
      fi
      raw_row_exclusion_backup_deleted_count=$((raw_row_exclusion_backup_deleted_count + 1))
    done < <(
      find "$exclusion_dir" -mindepth 2 -maxdepth 2 -type f -name 'pipeline_events_*.jsonl.gz' \
        -mtime "+$RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS" -print0 | sort -z
    )
  fi

}

if ! run_data_maintenance; then
  data_maintenance_failure_count=$((data_maintenance_failure_count + 1))
  echo "[DATA_MAINTENANCE_FAIL] compression_verify_failures=${compression_verify_failure_count} cleanup_will_continue=true"
fi

active_deleted_count="$(
  find "$LOG_DIR" -maxdepth 1 -type f \( \
    -name '*_cron.log' -o \
    -name 'run_*.log' -o \
    -name 'threshold_cycle_*.log' -o \
    -name 'tuning_monitoring_*.log' -o \
    -name 'dashboard_db_archive_*.log' -o \
    -name 'ensemble_scanner.log' -o \
    -name 'update_kospi.log' -o \
    -name 'buy_pause_guard.log' \
  \) ! -name 'log_rotation_cleanup_cron.log' -mtime "+$ACTIVE_LOG_RETENTION_DAYS" -print -delete | wc -l | tr -d ' '
)"
deleted_count=0
while IFS= read -r -d '' expired_archive_path; do
  if [[ -n "${archive_retention_protected_paths[$expired_archive_path]:-}" ]]; then
    archive_retention_protected_count=$((archive_retention_protected_count + 1))
    echo "[ARCHIVE_RETENTION_SKIP] archive=$(basename "$expired_archive_path") reason=${archive_retention_protection_reasons[$expired_archive_path]:-protected_archive_evidence}"
    continue
  fi
  rm -f -- "$expired_archive_path"
  deleted_count=$((deleted_count + 1))
done < <(find "${archive_log_find_args[@]}" -mtime "+$RETENTION_DAYS" -print0 | sort -z)
after_count="$(find "${archive_log_find_args[@]}" | wc -l | tr -d ' ')"
after_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"

echo "[LOG_CLEANUP] archive_retention_days=$RETENTION_DAYS active_log_retention_days=$ACTIVE_LOG_RETENTION_DAYS active_log_compress_min_index=$ACTIVE_LOG_COMPRESS_MIN_INDEX archive_compression_quiet_seconds=$ARCHIVE_COMPRESSION_QUIET_SECONDS system_metric_retention_days=$SYSTEM_METRIC_RETENTION_DAYS raw_row_exclusion_backup_retention_days=$RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS active_rotated=$rotated_active_count active_deleted=$active_deleted_count archive_deleted=$deleted_count archive_compressed=$compressed_archive_count archive_compression_finalized=$archive_compression_finalized_count archive_collision_reconciled=$archive_collision_reconciled_count archive_compression_failures=$archive_compression_failure_count archive_compression_sources_preserved=$archive_compression_source_preserved_count archive_retention_protected=$archive_retention_protected_count archive_pruned_to_backup_limit=$archive_pruned_to_backup_limit_count archive_before=$before_count archive_after=$after_count size_before=$before_size size_after=$after_size system_metric_retained=$system_metric_retained system_metric_pruned=$system_metric_pruned system_metric_invalid=$system_metric_invalid system_metric_size_before=$system_metric_before_size system_metric_size_after=$system_metric_after_size data_maintenance_enabled=$DATA_MAINTENANCE_ENABLED data_maintenance_failures=$data_maintenance_failure_count tmp_deleted=$tmp_deleted_count cache_deleted=$cache_deleted_count sentinel_compressed=$sentinel_compressed_count snapshot_compressed=$snapshot_compressed_count compression_verify_failures=$compression_verify_failure_count raw_row_exclusion_deleted=$raw_row_exclusion_deleted_count raw_row_exclusion_backup_deleted=$raw_row_exclusion_backup_deleted_count micro_reversion_storage_status=$micro_reversion_storage_status micro_reversion_storage_failures=$micro_reversion_storage_failure_count micro_reversion_storage_actions=$micro_reversion_storage_action_count micro_reversion_storage_compressed=$micro_reversion_storage_compressed_count micro_reversion_storage_purged=$micro_reversion_storage_purged_count micro_reversion_storage_source_bytes=$micro_reversion_storage_source_bytes micro_reversion_storage_purge_enabled=$micro_reversion_storage_purge_enabled micro_reversion_storage_purge_status=$micro_reversion_storage_purge_status micro_reversion_storage_purge_candidates=$micro_reversion_storage_purge_candidate_count micro_reversion_storage_purge_candidate_bytes=$micro_reversion_storage_purge_candidate_bytes"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
if [[ "$archive_compression_failure_count" -gt 0 || "$data_maintenance_failure_count" -gt 0 || "$micro_reversion_storage_failure_count" -gt 0 ]]; then
  echo "[FAIL] log_rotation_cleanup target_date=${TARGET_DATE} archive_compression_failures=${archive_compression_failure_count} archive_compression_sources_preserved=${archive_compression_source_preserved_count} archive_retention_protected=${archive_retention_protected_count} data_maintenance_failures=${data_maintenance_failure_count} micro_reversion_storage_status=${micro_reversion_storage_status} micro_reversion_storage_failures=${micro_reversion_storage_failure_count} compression_verify_failures=${compression_verify_failure_count} finished_at=${finished_at}"
  trap - ERR
  exit 1
fi
echo "[DONE] log_rotation_cleanup target_date=${TARGET_DATE} archive_retention_days=${RETENTION_DAYS} active_log_retention_days=${ACTIVE_LOG_RETENTION_DAYS} active_log_compress_min_index=${ACTIVE_LOG_COMPRESS_MIN_INDEX} archive_compression_quiet_seconds=${ARCHIVE_COMPRESSION_QUIET_SECONDS} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} raw_row_exclusion_backup_retention_days=${RAW_ROW_EXCLUSION_BACKUP_RETENTION_DAYS} active_rotated=${rotated_active_count} active_deleted=${active_deleted_count} archive_deleted=${deleted_count} archive_compressed=${compressed_archive_count} archive_compression_finalized=${archive_compression_finalized_count} archive_collision_reconciled=${archive_collision_reconciled_count} archive_compression_failures=${archive_compression_failure_count} archive_compression_sources_preserved=${archive_compression_source_preserved_count} archive_retention_protected=${archive_retention_protected_count} archive_pruned_to_backup_limit=${archive_pruned_to_backup_limit_count} system_metric_pruned=${system_metric_pruned} system_metric_invalid=${system_metric_invalid} data_maintenance_enabled=${DATA_MAINTENANCE_ENABLED} data_maintenance_failures=${data_maintenance_failure_count} tmp_deleted=${tmp_deleted_count} cache_deleted=${cache_deleted_count} sentinel_compressed=${sentinel_compressed_count} snapshot_compressed=${snapshot_compressed_count} compression_verify_failures=${compression_verify_failure_count} raw_row_exclusion_deleted=${raw_row_exclusion_deleted_count} raw_row_exclusion_backup_deleted=${raw_row_exclusion_backup_deleted_count} micro_reversion_storage_status=${micro_reversion_storage_status} micro_reversion_storage_failures=${micro_reversion_storage_failure_count} micro_reversion_storage_actions=${micro_reversion_storage_action_count} micro_reversion_storage_compressed=${micro_reversion_storage_compressed_count} micro_reversion_storage_purged=${micro_reversion_storage_purged_count} micro_reversion_storage_source_bytes=${micro_reversion_storage_source_bytes} micro_reversion_storage_purge_enabled=${micro_reversion_storage_purge_enabled} micro_reversion_storage_purge_status=${micro_reversion_storage_purge_status} micro_reversion_storage_purge_candidates=${micro_reversion_storage_purge_candidate_count} micro_reversion_storage_purge_candidate_bytes=${micro_reversion_storage_purge_candidate_bytes} finished_at=${finished_at}"
