#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
MODE="${1:-full}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"

LOCK_FILE="${PROJECT_DIR}/tmp/run_error_detection.lock"
LOG_FILE="${PROJECT_DIR}/logs/run_error_detection.log"
REPORT_FILE="${PROJECT_DIR}/data/report/error_detection/error_detection_$(TZ=Asia/Seoul date +%F).json"
CPU_AFFINITY="${ERROR_DETECTION_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity health)}"
RUN_ID="cron-$(TZ=Asia/Seoul date +%Y%m%dT%H%M%S)-$$"
RUN_REPORT_FILE="${PROJECT_DIR}/tmp/error_detection_${RUN_ID}.json"
TARGET_DATE="$(TZ=Asia/Seoul date +%F)"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
touch "$LOG_FILE"
cd "$PROJECT_DIR"
trap 'rm -f "$RUN_REPORT_FILE"' EXIT

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S') [SKIP] error detection already running mode=${MODE}" | tee -a "$LOG_FILE"
    exit 0
fi

bash "$SCRIPT_DIR/run_owned_log_rotation.sh" "error_detection_internal" "$LOG_FILE" || \
    echo "[WARN] owned log rotation failed owner=error_detection_internal log=${LOG_FILE}; writer will continue fail-closed"

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] error detection mode=${MODE} started_at=${started_at}" | tee -a "$LOG_FILE"

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.error_detector \
    --mode "$MODE" \
    --run-id "$RUN_ID" \
    --report-file "$RUN_REPORT_FILE")
if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
    cmd=(taskset -c "$CPU_AFFINITY" "${cmd[@]}")
fi

if "${cmd[@]}" 2>&1 | tee -a "$LOG_FILE"; then
    if env PYTHONPATH=. "$VENV_PY" - "$RUN_REPORT_FILE" "$REPORT_FILE" "$MODE" "$RUN_ID" "$TARGET_DATE" <<'PY'
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from src.engine.error_detector import validate_report_contract

run_path = Path(sys.argv[1])
canonical_path = Path(sys.argv[2])
expected_mode = sys.argv[3]
expected_run_id = sys.argv[4]
expected_target_date = sys.argv[5]
try:
    report = json.loads(run_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"[ERROR] invocation report unreadable path={run_path} error={exc}")
    raise SystemExit(1)
errors = validate_report_contract(
    report,
    expected_mode=expected_mode,
    expected_run_id=expected_run_id,
    expected_target_date=expected_target_date,
)
if errors:
    print(f"[ERROR] invocation report contract invalid errors={','.join(errors)}")
    raise SystemExit(1)
canonical_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = canonical_path.with_name(
    f".{canonical_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
)
try:
    shutil.copyfile(run_path, tmp_path)
    os.replace(tmp_path, canonical_path)
finally:
    tmp_path.unlink(missing_ok=True)
print(
    f"[INFO] invocation report validated and promoted run_id={expected_run_id} "
    f"report_file={canonical_path}"
)
PY
    then
        notify_cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.notify_error_detection_admin \
            --report-file "$RUN_REPORT_FILE" \
            --mode "$MODE" \
            --log-file "$LOG_FILE")
        if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
            notify_cmd=(taskset -c "$CPU_AFFINITY" "${notify_cmd[@]}")
        fi
        "${notify_cmd[@]}" 2>&1 | tee -a "$LOG_FILE" || true
        finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
        echo "[DONE] error detection mode=${MODE} run_id=${RUN_ID} finished_at=${finished_at}" | tee -a "$LOG_FILE"
    else
        finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
        echo "[FAIL] error detection mode=${MODE} run_id=${RUN_ID} report_validation_failed finished_at=${finished_at}" | tee -a "$LOG_FILE"
        exit 2
    fi
else
    exit_code=$?
    finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
    echo "[FAIL] error detection mode=${MODE} exit_code=${exit_code} finished_at=${finished_at}" | tee -a "$LOG_FILE"
    exit "$exit_code"
fi
