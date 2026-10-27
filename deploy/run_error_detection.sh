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
POSTCLOSE_SOURCE_DATE="${2:-}"
LOCK_WAIT_SEC="${ERROR_DETECTION_LOCK_WAIT_SEC:-0}"
if [[ ! "$LOCK_WAIT_SEC" =~ ^(0|[1-9][0-9]*)$ || ( "$LOCK_WAIT_SEC" != 0 && -z "$POSTCLOSE_SOURCE_DATE" ) ]]; then
    echo "[FAIL] error detection reason=invalid_lock_wait_scope"
    exit 2
fi
TARGET_DATE="${POSTCLOSE_SOURCE_DATE:-$(TZ=Asia/Seoul date +%F)}"
REPORT_FILE="${PROJECT_DIR}/data/report/error_detection/error_detection_${TARGET_DATE}.json"
CPU_AFFINITY="${ERROR_DETECTION_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity health)}"
RUN_ID="cron-$(TZ=Asia/Seoul date +%Y%m%dT%H%M%S)-$$"
RUN_REPORT_FILE="${PROJECT_DIR}/tmp/error_detection_${RUN_ID}.json"

mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"
touch "$LOG_FILE"
cd "$PROJECT_DIR"
# Keep each explicit recovery attempt as audit evidence. A valid recovery
# report is authoritative even when it records an unresolved failure; the
# wrapper still exits non-zero after publishing that failure.
if [[ -z "$POSTCLOSE_SOURCE_DATE" ]]; then
    trap 'rm -f "$RUN_REPORT_FILE"' EXIT
fi

exec 9>"$LOCK_FILE"
# Finalization shares its existing wall budget between admission and execution.
# Regular sweeps retain nonblocking admission; no completed report is reused.
lock_args=(-n)
if [[ "$LOCK_WAIT_SEC" != 0 ]]; then
    lock_args=(-w "$LOCK_WAIT_SEC")
fi
if ! flock "${lock_args[@]}" 9; then
    echo "$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S') [SKIP] error detection or ordered deployment holds lock mode=${MODE}" | tee -a "$LOG_FILE"
    if [[ -n "$POSTCLOSE_SOURCE_DATE" ]]; then
        exit 75
    fi
    exit 0
fi

# The router may have selected this root just before a deployment acquired the
# lock. Recheck after acquiring it; never publish an old reader's observation.
if env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" <<'PY'
import os
import sys
from pathlib import Path
from src.engine.infrastructure.runtime_release_router import error_detector_release_is_current

try:
    current = error_detector_release_is_current(
        Path(sys.argv[1]), os.environ.get('KORSTOCKSCAN_RUNTIME_GIT_COMMIT'))
except (OSError, ValueError) as exc:
    print(f"[FAIL] error detection release validation failed: {exc}")
    raise SystemExit(1)
raise SystemExit(0 if current else 75)
PY
then
    :
else
    selection_rc=$?
    if [[ "$selection_rc" -eq 75 ]]; then
        echo "[SKIP] error detection selected release changed before lock mode=${MODE}" | tee -a "$LOG_FILE"
        [[ -z "$POSTCLOSE_SOURCE_DATE" ]] && exit 0
    fi
    exit "$selection_rc"
fi

bash "$SCRIPT_DIR/run_owned_log_rotation.sh" "error_detection_internal" "$LOG_FILE" || \
    echo "[WARN] owned log rotation failed owner=error_detection_internal log=${LOG_FILE}; writer will continue fail-closed"

started_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
echo "[START] error detection mode=${MODE} started_at=${started_at}" | tee -a "$LOG_FILE"

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.error_detector \
    --mode "$MODE" \
    --run-id "$RUN_ID" \
    --report-file "$RUN_REPORT_FILE")
if [[ -n "$POSTCLOSE_SOURCE_DATE" ]]; then
    cmd+=(--postclose-source-date "$POSTCLOSE_SOURCE_DATE")
fi
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
        if [[ -n "$POSTCLOSE_SOURCE_DATE" ]] && env PYTHONPATH=. "$VENV_PY" - "$RUN_REPORT_FILE" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if report.get("summary_severity") == "fail" else 1)
PY
        then
            # A recovery detector can be healthy while correctly observing an
            # unresolved predecessor. Preserve its canonical receipt before
            # returning a failure to finalization.
            finished_at="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
            echo "[FAIL] error detection mode=${MODE} run_id=${RUN_ID} postclose_recovery_unresolved_failure report_published=true finished_at=${finished_at}" | tee -a "$LOG_FILE"
            exit 1
        fi
        notify_cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.notify_error_detection_admin \
            --report-file "$RUN_REPORT_FILE" \
            --mode "$MODE" \
            --log-file "$LOG_FILE")
        if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
            notify_cmd=(taskset -c "$CPU_AFFINITY" "${notify_cmd[@]}")
        fi
        if [[ "${POSTCLOSE_NOTIFICATIONS:-true}" == "true" ]]; then
            "${notify_cmd[@]}" 2>&1 | tee -a "$LOG_FILE" || true
        fi
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
