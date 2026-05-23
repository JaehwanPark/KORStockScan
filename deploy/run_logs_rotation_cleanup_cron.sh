#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_DIR="$PROJECT_DIR/logs"
RETENTION_DAYS="${1:-7}"
TARGET_DATE="${TARGET_DATE:-$(TZ=Asia/Seoul date +%F)}"
ACTIVE_LOG_MAX_BYTES="${LOG_ROTATION_ACTIVE_MAX_BYTES:-${KORSTOCKSCAN_LOG_ROTATE_MAX_BYTES:-20971520}}"
ACTIVE_LOG_BACKUP_COUNT="${LOG_ROTATION_BACKUP_COUNT:-5}"
SYSTEM_METRIC_RETENTION_DAYS="${SYSTEM_METRIC_RETENTION_DAYS:-3}"
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
if [[ ! "$SYSTEM_METRIC_RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] system metric retention days must be integer: $SYSTEM_METRIC_RETENTION_DAYS"
  exit 2
fi

mkdir -p "$LOG_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] log_rotation_cleanup target_date=${TARGET_DATE} retention_days=${RETENTION_DAYS} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} active_log_max_bytes=${ACTIVE_LOG_MAX_BYTES} active_log_backup_count=${ACTIVE_LOG_BACKUP_COUNT} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] log_rotation_cleanup target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

before_count="$(find "$LOG_DIR" -maxdepth 1 -type f -regex '.*\.log\.[0-9]+' | wc -l | tr -d ' ')"
before_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"
system_metric_before_size=0
system_metric_after_size=0
system_metric_retained=0
system_metric_pruned=0

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

deleted_count="$(find "$LOG_DIR" -maxdepth 1 -type f -regex '.*\.log\.[0-9]+' -mtime "+$RETENTION_DAYS" -print -delete | wc -l | tr -d ' ')"
after_count="$(find "$LOG_DIR" -maxdepth 1 -type f -regex '.*\.log\.[0-9]+' | wc -l | tr -d ' ')"
after_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"

echo "[LOG_CLEANUP] retention_days=$RETENTION_DAYS system_metric_retention_days=$SYSTEM_METRIC_RETENTION_DAYS active_rotated=$rotated_active_count deleted=$deleted_count rotated_before=$before_count rotated_after=$after_count size_before=$before_size size_after=$after_size system_metric_retained=$system_metric_retained system_metric_pruned=$system_metric_pruned system_metric_size_before=$system_metric_before_size system_metric_size_after=$system_metric_after_size"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] log_rotation_cleanup target_date=${TARGET_DATE} retention_days=${RETENTION_DAYS} system_metric_retention_days=${SYSTEM_METRIC_RETENTION_DAYS} active_rotated=${rotated_active_count} deleted=${deleted_count} system_metric_pruned=${system_metric_pruned} finished_at=${finished_at}"
