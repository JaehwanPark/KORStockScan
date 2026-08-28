#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 OWNER LOG_PATH" >&2
  exit 2
fi

OWNER="$1"
LOG_PATH="$2"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MAX_BYTES="${LOG_ROTATION_ACTIVE_MAX_BYTES:-${KORSTOCKSCAN_LOG_ROTATE_MAX_BYTES:-20971520}}"
LOCK_WAIT_SEC="${OWNED_LOG_ROTATION_LOCK_WAIT_SEC:-10}"
TARGET_DATE="${TARGET_DATE:-$(TZ=Asia/Seoul date +%F)}"
RECEIPT_DIR="${OWNED_LOG_ROTATION_RECEIPT_DIR:-$PROJECT_DIR/data/report/log_writer_rollover_receipts}"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

if [[ ! "$MAX_BYTES" =~ ^[0-9]+$ || ! "$LOCK_WAIT_SEC" =~ ^[0-9]+$ ]]; then
  echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} reason=invalid_numeric_config" >&2
  exit 2
fi
if [[ -z "$OWNER" || "$OWNER" == *$'\t'* || "$OWNER" == *$'\n'* ]]; then
  echo "[OWNED_LOG_ROTATION_ERROR] reason=invalid_owner" >&2
  exit 2
fi

mkdir -p "$(dirname "$LOG_PATH")" "$PROJECT_DIR/tmp" "$RECEIPT_DIR"
if [[ -L "$LOG_PATH" || ( -e "$LOG_PATH" && ! -f "$LOG_PATH" ) ]]; then
  echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} reason=unsafe_log_type" >&2
  exit 1
fi
touch "$LOG_PATH"

log_identity="$(printf '%s' "$LOG_PATH" | sha256sum | awk '{print $1}')"
lock_path="$PROJECT_DIR/tmp/owned_log_rotation_${log_identity}.lock"
exec 8>"$lock_path"
if ! flock -w "$LOCK_WAIT_SEC" 8; then
  echo "[OWNED_LOG_ROTATION_DEFERRED] owner=${OWNER} log=${LOG_PATH} reason=rotation_lock_busy" >&2
  exit 0
fi

path_has_open_fd() {
  local path="$1"
  local path_dev_inode=""
  local fd_path=""
  local fd_dev_inode=""
  if command -v fuser >/dev/null 2>&1 && fuser -s -I "$path"; then
    return 0
  fi
  if [[ ! -d /proc ]]; then
    return 0
  fi
  path_dev_inode="$(stat -Lc '%d:%i' "$path" 2>/dev/null || true)"
  if [[ -z "$path_dev_inode" ]]; then
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

write_receipt() {
  local status="$1"
  local reason="$2"
  local source_size="${3:-0}"
  local source_sha="${4:-not_available}"
  local archive_path="${5:-not_available}"
  local archive_sha="${6:-not_available}"
  local receipt_path="$RECEIPT_DIR/log_writer_rollover_${TARGET_DATE}.jsonl"
  if ! "$PYTHON_BIN" - "$receipt_path" "$OWNER" "$LOG_PATH" "$status" "$reason" "$source_size" "$source_sha" "$archive_path" "$archive_sha" <<'PY'
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

path = Path(sys.argv[1])
payload = {
    "schema_version": "log_writer_rollover_receipt_v1",
    "recorded_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
    "writer_owner": sys.argv[2],
    "active_log_path": sys.argv[3],
    "status": sys.argv[4],
    "reason": sys.argv[5],
    "source_size_bytes": int(sys.argv[6]),
    "source_sha256": sys.argv[7],
    "archive_path": sys.argv[8],
    "archive_sha256": sys.argv[9],
    "runtime_effect": False,
    "order_authority": False,
    "provider_authority": False,
    "threshold_authority": False,
}
path.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
try:
    os.write(fd, (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    os.fsync(fd)
finally:
    os.close(fd)
PY
  then
    echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} reason=receipt_write_failed status=${status}" >&2
    return 1
  fi
}

source_size="$(stat -c%s "$LOG_PATH")"
if [[ "$source_size" -lt "$MAX_BYTES" ]]; then
  exit 0
fi
if path_has_open_fd "$LOG_PATH"; then
  write_receipt "deferred_writer_active" "active_inode_open" "$source_size" || true
  echo "[OWNED_LOG_ROTATION_DEFERRED] owner=${OWNER} log=${LOG_PATH} size_bytes=${source_size} reason=active_inode_open active_preserved=true" >&2
  exit 0
fi

source_mode="$(stat -c '%a' "$LOG_PATH")"
source_metadata="$(stat -c '%d:%i:%s:%Y' "$LOG_PATH")"
source_sha="$(sha256sum -- "$LOG_PATH" | awk '{print $1}')"
verified_metadata="$(stat -c '%d:%i:%s:%Y' "$LOG_PATH")"
verified_sha="$(sha256sum -- "$LOG_PATH" | awk '{print $1}')"
if [[ "$verified_metadata" != "$source_metadata" || "$verified_sha" != "$source_sha" ]] || path_has_open_fd "$LOG_PATH"; then
  write_receipt "deferred_writer_active" "active_changed_during_preflight" "$source_size" "$source_sha" || true
  echo "[OWNED_LOG_ROTATION_DEFERRED] owner=${OWNER} log=${LOG_PATH} size_bytes=${source_size} reason=active_changed_during_preflight active_preserved=true" >&2
  exit 0
fi

stamp="$(TZ=Asia/Seoul date +%Y%m%dT%H%M%S%N%z)"
plain_archive="${LOG_PATH}.before_${stamp}_${source_sha:0:16}"
gzip_archive="${LOG_PATH}.generation_${source_sha:0:16}.gz"
if [[ -e "$plain_archive" || -L "$plain_archive" ]]; then
  echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} reason=plain_archive_collision" >&2
  exit 1
fi

mv -- "$LOG_PATH" "$plain_archive"
if ! install -m "$source_mode" /dev/null "$LOG_PATH"; then
  mv -- "$plain_archive" "$LOG_PATH" || true
  echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} reason=active_recreate_failed" >&2
  exit 1
fi
if [[ "$(sha256sum -- "$plain_archive" | awk '{print $1}')" != "$source_sha" ]]; then
  echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} archive=${plain_archive} reason=renamed_source_hash_mismatch source_preserved=true" >&2
  exit 1
fi

tmp_gzip="$(mktemp "${gzip_archive}.tmp.XXXXXX")"
trap 'rm -f "${tmp_gzip:-}"' EXIT
gzip -9 -c -- "$plain_archive" >"$tmp_gzip"
gzip -t -- "$tmp_gzip"
restored_sha="$(gzip -cd -- "$tmp_gzip" | sha256sum | awk '{print $1}')"
if [[ "$restored_sha" != "$source_sha" ]]; then
  echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} archive=${plain_archive} reason=gzip_roundtrip_hash_mismatch source_preserved=true" >&2
  exit 1
fi
if [[ -e "$gzip_archive" || -L "$gzip_archive" ]]; then
  if [[ ! -f "$gzip_archive" ]] || ! gzip -t -- "$gzip_archive" || \
     [[ "$(gzip -cd -- "$gzip_archive" | sha256sum | awk '{print $1}')" != "$source_sha" ]]; then
    echo "[OWNED_LOG_ROTATION_ERROR] owner=${OWNER} log=${LOG_PATH} archive=${gzip_archive} reason=generation_collision source_preserved=true" >&2
    exit 1
  fi
else
  ln -- "$tmp_gzip" "$gzip_archive"
fi
archive_sha="$(sha256sum -- "$gzip_archive" | awk '{print $1}')"
rm -f "$tmp_gzip"
trap - EXIT
rm -- "$plain_archive"
write_receipt "rotated_verified" "owner_preopen_rollover" "$source_size" "$source_sha" "$gzip_archive" "$archive_sha"
echo "[OWNED_LOG_ROTATED] owner=${OWNER} log=${LOG_PATH} size_bytes=${source_size} source_sha256=${source_sha} archive=${gzip_archive} archive_sha256=${archive_sha} active_recreated=true"
