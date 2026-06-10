#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_DIR="$PROJECT_DIR/logs"
RETENTION_DAYS="${1:-${LOG_ROTATION_ARCHIVE_RETENTION_DAYS:-30}}"
TARGET_DATE="${TARGET_DATE:-$(TZ=Asia/Seoul date +%F)}"
ACTIVE_LOG_MAX_BYTES="${LOG_ROTATION_ACTIVE_MAX_BYTES:-${KORSTOCKSCAN_LOG_ROTATE_MAX_BYTES:-20971520}}"
ACTIVE_LOG_BACKUP_COUNT="${LOG_ROTATION_BACKUP_COUNT:-5}"
ACTIVE_LOG_RETENTION_DAYS="${LOG_ROTATION_ACTIVE_RETENTION_DAYS:-14}"
SYSTEM_METRIC_RETENTION_DAYS="${SYSTEM_METRIC_RETENTION_DAYS:-3}"
DATA_MAINTENANCE_ENABLED="${DATA_MAINTENANCE_ENABLED:-true}"
TMP_MAINTENANCE_RETENTION_DAYS="${TMP_MAINTENANCE_RETENTION_DAYS:-2}"
REFRACTOR_DRY_RUN_RETENTION_DAYS="${REFRACTOR_DRY_RUN_RETENTION_DAYS:-7}"
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

mkdir -p "$LOG_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] log_rotation_cleanup target_date=${TARGET_DATE} archive_retention_days=${RETENTION_DAYS} active_log_retention_days=${ACTIVE_LOG_RETENTION_DAYS} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} active_log_max_bytes=${ACTIVE_LOG_MAX_BYTES} active_log_backup_count=${ACTIVE_LOG_BACKUP_COUNT} data_maintenance_enabled=${DATA_MAINTENANCE_ENABLED} started_at=${started_at}"
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
tmp_deleted_count=0
cache_deleted_count=0
sentinel_compressed_count=0
snapshot_compressed_count=0
raw_row_exclusion_deleted_count=0

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
      if [[ -f "${log_path}.${prev}" ]]; then
        mv -f "${log_path}.${prev}" "${log_path}.${idx}"
      fi
    done
  fi
  mv -f "$log_path" "${log_path}.1"
  : > "$log_path"
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
from datetime import datetime, timedelta
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
retention_days = int(sys.argv[3])
cutoff = datetime.now().astimezone() - timedelta(days=retention_days)
retained = 0
pruned = 0
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
        except Exception:
            keep = True
        if keep:
            dst.write(stripped + "\n")
            retained += 1
        else:
            pruned += 1
os.replace(target, source)
os.chmod(source, 0o664)
print(f"{retained} {pruned} {source.stat().st_size}")
PY
}

metric_prune_output=""
if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if [[ -f "$LOG_DIR/system_metric_samples.jsonl" ]]; then
    system_metric_before_size="$(stat -c%s "$LOG_DIR/system_metric_samples.jsonl" 2>/dev/null || echo 0)"
  fi
  metric_prune_output="$(prune_system_metric_samples 2>/dev/null || true)"
  if [[ -n "$metric_prune_output" ]]; then
    system_metric_retained="$(echo "$metric_prune_output" | awk '{print $1}' | tail -1)"
    system_metric_pruned="$(echo "$metric_prune_output" | awk '{print $2}' | tail -1)"
    system_metric_after_size="$(echo "$metric_prune_output" | awk '{print $3}' | tail -1)"
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
      gzip -f -9 "$event_path"
      sentinel_compressed_count=$((sentinel_compressed_count + 1))
    done < <(find "$sentinel_dir" -maxdepth 1 -type f -name '*_events_*.jsonl' -print0 | sort -z)
  fi

  local snapshot_dir="$PROJECT_DIR/data/threshold_cycle/snapshots"
  if [[ -d "$snapshot_dir" ]]; then
    while IFS= read -r -d '' snapshot_path; do
      if [[ "$(basename "$snapshot_path")" == "pipeline_events_${TARGET_DATE}_"*".jsonl" ]]; then
        continue
      fi
      gzip -f -9 "$snapshot_path"
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
  fi
}

run_data_maintenance

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
deleted_count="$(find "${archive_log_find_args[@]}" -mtime "+$RETENTION_DAYS" -print -delete | wc -l | tr -d ' ')"
after_count="$(find "${archive_log_find_args[@]}" | wc -l | tr -d ' ')"
after_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"

echo "[LOG_CLEANUP] archive_retention_days=$RETENTION_DAYS active_log_retention_days=$ACTIVE_LOG_RETENTION_DAYS system_metric_retention_days=$SYSTEM_METRIC_RETENTION_DAYS active_rotated=$rotated_active_count active_deleted=$active_deleted_count archive_deleted=$deleted_count archive_before=$before_count archive_after=$after_count size_before=$before_size size_after=$after_size system_metric_retained=$system_metric_retained system_metric_pruned=$system_metric_pruned system_metric_size_before=$system_metric_before_size system_metric_size_after=$system_metric_after_size data_maintenance_enabled=$DATA_MAINTENANCE_ENABLED tmp_deleted=$tmp_deleted_count cache_deleted=$cache_deleted_count sentinel_compressed=$sentinel_compressed_count snapshot_compressed=$snapshot_compressed_count raw_row_exclusion_deleted=$raw_row_exclusion_deleted_count"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] log_rotation_cleanup target_date=${TARGET_DATE} archive_retention_days=${RETENTION_DAYS} active_log_retention_days=${ACTIVE_LOG_RETENTION_DAYS} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} active_rotated=${rotated_active_count} active_deleted=${active_deleted_count} archive_deleted=${deleted_count} system_metric_pruned=${system_metric_pruned} data_maintenance_enabled=${DATA_MAINTENANCE_ENABLED} tmp_deleted=${tmp_deleted_count} cache_deleted=${cache_deleted_count} sentinel_compressed=${sentinel_compressed_count} snapshot_compressed=${snapshot_compressed_count} raw_row_exclusion_deleted=${raw_row_exclusion_deleted_count} finished_at=${finished_at}"
