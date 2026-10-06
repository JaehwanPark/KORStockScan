#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
SCHEDULED_EFFECTIVE_TODAY=false
TARGET_EFFECTIVE_DATE=""
if [[ "${1:-}" == "--resolve-effective-today" ]]; then
  SCHEDULED_EFFECTIVE_TODAY=true
  TARGET_EFFECTIVE_DATE="$(TZ=Asia/Seoul date +%F)"
  TARGET_DATE="$(PYTHONPATH="$SCRIPT_DIR/.." "$VENV_PY" - "$TARGET_EFFECTIVE_DATE" <<'PY'
from datetime import date, timedelta
import sys
from src.utils.market_day import is_krx_trading_day

effective = date.fromisoformat(sys.argv[1])
if not is_krx_trading_day(effective):
    print("SKIP_NON_TRADING_EFFECTIVE_DATE")
    raise SystemExit(0)
source = effective - timedelta(days=1)
for _ in range(14):
    if is_krx_trading_day(source):
        print(source.isoformat())
        break
    source -= timedelta(days=1)
else:
    raise SystemExit("previous_krx_trading_date_unresolved")
PY
)" || exit 2
  if [[ "$TARGET_DATE" == "SKIP_NON_TRADING_EFFECTIVE_DATE" ]]; then
    echo "[SKIP] postclose_finalization effective_date=${TARGET_EFFECTIVE_DATE} reason=non_trading_effective_date"
    exit 0
  fi
elif [[ -z "${1:-}" ]]; then
  TARGET_DATE="$(TZ=Asia/Seoul date +%F)"
else
  TARGET_DATE="$1"
fi
RECOVERY_MODE=false
if [[ "${2:-}" == "--recover-closed-target" && "$SCHEDULED_EFFECTIVE_TODAY" == "false" ]]; then
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
WAIT_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_WAIT_TIMEOUT_SEC:-3600}"
POLL_SEC="${POSTCLOSE_FINALIZATION_POLL_SEC:-30}"
HARD_DEADLINE_KST="${POSTCLOSE_FINALIZATION_HARD_DEADLINE_KST:-06:00}"
CLEANUP_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_CLEANUP_TIMEOUT_SEC:-600}"
DETECTOR_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_DETECTOR_TIMEOUT_SEC:-600}"
SUMMARY_TIMEOUT_SEC="${POSTCLOSE_FINALIZATION_SUMMARY_TIMEOUT_SEC:-600}"
FINALIZATION_FINISH_BY_KST="${POSTCLOSE_FINALIZATION_FINISH_BY_KST:-06:50}"
ALLOW_NONCURRENT_TARGET="${POSTCLOSE_FINALIZATION_ALLOW_NONCURRENT_TARGET:-false}"
OWNED_LOG_RUNNER="${POSTCLOSE_FINALIZATION_OWNED_LOG_RUNNER:-$SCRIPT_DIR/run_with_owned_log.sh}"
CLEANUP_RUNNER="${POSTCLOSE_FINALIZATION_CLEANUP_RUNNER:-$SCRIPT_DIR/run_logs_rotation_cleanup_cron.sh}"
ERROR_DETECTION_RUNNER="${POSTCLOSE_FINALIZATION_ERROR_DETECTION_RUNNER:-$SCRIPT_DIR/run_error_detection.sh}"

if [[ ! "$WAIT_TIMEOUT_SEC" =~ ^[0-9]+$ || ! "$POLL_SEC" =~ ^[1-9][0-9]*$ || ! "$CLEANUP_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$DETECTOR_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$SUMMARY_TIMEOUT_SEC" =~ ^[1-9][0-9]*$ || ! "$HARD_DEADLINE_KST" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ || ! "$FINALIZATION_FINISH_BY_KST" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
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
if [[ -z "$TARGET_EFFECTIVE_DATE" ]]; then
  TARGET_EFFECTIVE_DATE="$(PYTHONPATH="$SCRIPT_DIR/.." "$VENV_PY" - "$TARGET_DATE" <<'PY'
from datetime import date, timedelta
import sys
from src.utils.market_day import is_krx_trading_day

candidate = date.fromisoformat(sys.argv[1]) + timedelta(days=1)
for _ in range(14):
    if is_krx_trading_day(candidate):
        print(candidate.isoformat())
        break
    candidate += timedelta(days=1)
else:
    raise SystemExit("effective_krx_trading_date_unresolved")
PY
)" || exit 2
fi
if [[ "$RECOVERY_MODE" != "true" && "$ALLOW_NONCURRENT_TARGET" != "true" \
    && "$TARGET_DATE" != "$(TZ=Asia/Seoul date +%F)" \
    && "$TARGET_EFFECTIVE_DATE" != "$(TZ=Asia/Seoul date +%F)" ]]; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} effective_date=${TARGET_EFFECTIVE_DATE} reason=noncurrent_target_for_final_detector"
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
echo "[START] postclose_finalization target_date=${TARGET_DATE} effective_date=${TARGET_EFFECTIVE_DATE} recovery=${RECOVERY_MODE} wait_timeout_sec=${WAIT_TIMEOUT_SEC} hard_deadline_kst=${HARD_DEADLINE_KST} started_at=${started_at}"

remaining_before_finalization_cutoff() {
  "$VENV_PY" - "$TARGET_EFFECTIVE_DATE" "$FINALIZATION_FINISH_BY_KST" <<'PY'
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
import sys
deadline = datetime.combine(date.fromisoformat(sys.argv[1]), time.fromisoformat(sys.argv[2]), ZoneInfo("Asia/Seoul"))
print(max(0, int((deadline - datetime.now(ZoneInfo("Asia/Seoul"))).total_seconds())))
PY
}

bounded_stage_budget() {
  local requested="$1"
  local remaining
  if [[ "$RECOVERY_MODE" == "true" || "$ALLOW_NONCURRENT_TARGET" == "true" ]]; then
    printf '%s\n' "$requested"
    return 0
  fi
  remaining="$(remaining_before_finalization_cutoff)" || return 1
  (( remaining > 0 )) || return 1
  if (( requested < remaining )); then
    printf '%s\n' "$requested"
  else
    printf '%s\n' "$remaining"
  fi
}

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
  local detector_budget
  detector_args+=("$TARGET_DATE")
  detector_budget="$(bounded_stage_budget "$DETECTOR_TIMEOUT_SEC")" || {
    echo "[SKIP] postclose_final_detector target_date=${TARGET_DATE} reason=finish_by_cutoff_elapsed"
    return 1
  }
  timeout --foreground "${detector_budget}s" bash "$OWNED_LOG_RUNNER" \
    --owner error_detection_cron \
    --log "$PROJECT_DIR/logs/run_error_detection_cron.log" \
    env POSTCLOSE_FINALIZATION_DETECTOR_PARENT_PID="$$" POSTCLOSE_FINALIZATION_DETECTOR_DATE="$TARGET_DATE" \
    POSTCLOSE_PREPARED_EFFECTIVE_DATE="$TARGET_EFFECTIVE_DATE" \
    bash "$ERROR_DETECTION_RUNNER" "${detector_args[@]}"
}

waited=0
while true; do
  if [[ "$RECOVERY_MODE" != "true" && "$ALLOW_NONCURRENT_TARGET" != "true" ]]; then
    deadline_reached="$(TZ=Asia/Seoul "$VENV_PY" - "$TARGET_EFFECTIVE_DATE" "$HARD_DEADLINE_KST" <<'PY'
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
import sys
deadline = datetime.combine(date.fromisoformat(sys.argv[1]), time.fromisoformat(sys.argv[2]), ZoneInfo("Asia/Seoul"))
print("true" if datetime.now(ZoneInfo("Asia/Seoul")) >= deadline else "false")
PY
)"
    if [[ "$deadline_reached" == "true" ]]; then
      current_kst="$(TZ=Asia/Seoul date +%FT%T)"
      echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} effective_date=${TARGET_EFFECTIVE_DATE} reason=effective_date_hard_deadline current_kst=${current_kst} hard_deadline_kst=${HARD_DEADLINE_KST}"
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
  # A closed source may have a valid v2 predecessor generation. Recompute only
  # its summary with the current v3 owner before resealing the controller;
  # never synthesize v3 policy/research terminals or replay those producers.
  if [[ "$RECOVERY_MODE" == "true" ]]; then
    migrate_summary="$(env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" <<'PY'
import sys
from pathlib import Path
from src.engine.automation.postclose_summary_handoff import _load_json, stage_path, stage_receipt_issues
receipt = _load_json(stage_path(Path(sys.argv[1]) / 'data/report', sys.argv[2], 'summary_handoff'))
issues = stage_receipt_issues(Path(sys.argv[1]) / 'data/report', sys.argv[2], 'summary_handoff') if receipt else []
print('true' if receipt and issues else 'false')
PY
)" || {
      echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=summary_stage_migration_check_failed"
      run_final_detector || true
      exit 1
    }
    if [[ "$migrate_summary" == "true" ]]; then
      summary_budget="$(bounded_stage_budget "$SUMMARY_TIMEOUT_SEC")" || {
        echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finish_by_cutoff_elapsed_before_summary"
        run_final_detector || true
        exit 1
      }
      if ! timeout --kill-after=10s "${summary_budget}s" env PYTHONPATH=. POSTCLOSE_STAGE_WORKER=1 \
        "$VENV_PY" -m src.engine.automation.postclose_summary_handoff \
        --stage summary_handoff --date "$TARGET_DATE" \
        --publication-date "$(TZ=Asia/Seoul date +%F)" --recover-closed-target \
        --timeout-sec "$summary_budget"; then
        echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=summary_stage_migration_failed"
        run_final_detector || true
        exit 1
      fi
    fi
  fi
  controller_started_after_ns="$(date +%s%N)"
  summary_budget="$(bounded_stage_budget "$SUMMARY_TIMEOUT_SEC")" || {
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finish_by_cutoff_elapsed_before_summary"
    run_final_detector || true
    exit 1
  }
  if ! timeout --kill-after=10s "${summary_budget}s" env PYTHONPATH=. POSTCLOSE_STAGE_WORKER=1 \
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

finalization_generation=""
if [[ "$TARGET_DATE" > "2026-09-29" ]]; then
  finalization_generation="$(env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" <<'PY'
import sys
from pathlib import Path
from src.engine.automation.postclose_finalization_generation import capture_finalization_generation

receipt = capture_finalization_generation(Path(sys.argv[1]), sys.argv[2])
print(receipt["chain_sha256"], receipt["snapshot_sha256"])
PY
)" || {
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finalization_generation_invalid"
    run_final_detector || true
    exit 1
  }
fi

cleanup_budget="$(bounded_stage_budget "$CLEANUP_TIMEOUT_SEC")" || {
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finish_by_cutoff_elapsed_before_cleanup"
  run_final_detector || true
  exit 1
}
if ! timeout --foreground "${cleanup_budget}s" bash "$OWNED_LOG_RUNNER" \
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
detector_started_after_ns="$(date +%s%N)"
if ! run_final_detector; then
  echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=final_detector_failed"
  exit 1
fi
detector_generation_fields=""
if [[ -n "$finalization_generation" ]]; then
  detector_receipt="$(env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" "$detector_started_after_ns" <<'PY'
import sys
from pathlib import Path
from src.engine.automation.postclose_finalization_generation import capture_final_detector_receipt

receipt = capture_final_detector_receipt(
    Path(sys.argv[1]), sys.argv[2], started_after_ns=int(sys.argv[3])
)
print(receipt["run_id"], receipt["report_sha256"])
PY
)" || {
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=final_detector_receipt_invalid"
    exit 1
  }
  read -r detector_run_id detector_report_sha256 <<< "$detector_receipt"
  detector_generation_fields=" detector_run_id=${detector_run_id} detector_report_sha256=${detector_report_sha256}"
fi
if [[ -n "$finalization_generation" ]]; then
  current_generation="$(env PYTHONPATH=. "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" <<'PY'
import sys
from pathlib import Path
from src.engine.automation.postclose_finalization_generation import capture_finalization_generation

receipt = capture_finalization_generation(Path(sys.argv[1]), sys.argv[2])
print(receipt["chain_sha256"], receipt["snapshot_sha256"])
PY
)" || {
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finalization_generation_changed_after_detector"
    exit 1
  }
  if [[ "$current_generation" != "$finalization_generation" ]]; then
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finalization_generation_changed_after_detector"
    exit 1
  fi
  read -r chain_sha256 snapshot_generation_sha256 <<< "$finalization_generation"
  finalization_generation_fields=" chain_sha256=${chain_sha256} snapshot_generation_sha256=${snapshot_generation_sha256}"
else
  finalization_generation_fields=""
fi
if [[ "$TARGET_DATE" > "2026-09-27" ]]; then
  preparation_disposition="$(env PYTHONPATH=. "$VENV_PY" - "$TARGET_DATE" "$TARGET_EFFECTIVE_DATE" "$RECOVERY_MODE" <<'PY'
import sys
from src.engine.automation.next_preopen_readiness import finalization_preparation_disposition
print(finalization_preparation_disposition(sys.argv[1], sys.argv[2], recovery=sys.argv[3] == 'true'))
PY
)" || {
    echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=preopen_source_session_mismatch"
    exit 1
  }
  if [[ "$preparation_disposition" == "historical_recovery_no_prepare" ]]; then
    echo "[INFO] postclose_finalization target_date=${TARGET_DATE} effective_date=${TARGET_EFFECTIVE_DATE} preopen=not_applicable_historical_recovery runtime_effect=false"
  else
    prepare_budget="$(bounded_stage_budget 120)" || {
      echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=finish_by_cutoff_elapsed_before_preopen_preparation"
      exit 1
    }
    if ! timeout --kill-after=10s "${prepare_budget}s" env PYTHONPATH=. "$VENV_PY" \
      -m src.engine.automation.next_preopen_readiness --prepare --source-date "$TARGET_DATE" \
      --target-date "$TARGET_EFFECTIVE_DATE"; then
      echo "[FAIL] postclose_finalization target_date=${TARGET_DATE} reason=next_preopen_preparation_failed"
      exit 1
    fi
  fi
fi
detector_finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_finalization target_date=${TARGET_DATE} cleanup=done detector=done${finalization_generation_fields}${detector_generation_fields} finished_at=${detector_finished_at}"
echo "[DONE] postclose_final_detector target_date=${TARGET_DATE} finalization=done detector=done${finalization_generation_fields}${detector_generation_fields} finished_at=${detector_finished_at}"
