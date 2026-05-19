#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-none}"
RUN_LIFECYCLE_AUDIT="${SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT:-false}"

cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs/swing_live_dry_run"
STATUS_DIR="$PROJECT_DIR/data/report/swing_selection_funnel/status"
LOCK_ROOT="$PROJECT_DIR/tmp"
LOG_PATH="$LOG_DIR/swing_live_dry_run_${TARGET_DATE}.log"
STATUS_PATH="$STATUS_DIR/swing_live_dry_run_${TARGET_DATE}.status.json"
LOCK_DIR="$LOCK_ROOT/swing_live_dry_run_${TARGET_DATE}.lock"
STARTED_AT="$(TZ=Asia/Seoul date --iso-8601=seconds)"

mkdir -p "$LOG_DIR" "$STATUS_DIR" "$LOCK_ROOT"
exec > >(tee -a "$LOG_PATH") 2>&1
echo "[START] swing_live_dry_run target_date=${TARGET_DATE} started_at=${STARTED_AT}"
trap 'failed_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"; echo "[FAIL] swing_live_dry_run target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

run_lifecycle_audit_enabled() {
  [ "$RUN_LIFECYCLE_AUDIT" = "true" ] || [ "$RUN_LIFECYCLE_AUDIT" = "1" ]
}

write_status() {
  local status="$1"
  local exit_code="$2"
  local reason="$3"
  local finished_at
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  printf '{\n' > "$STATUS_PATH"
  printf '  "schema_version": 1,\n' >> "$STATUS_PATH"
  printf '  "report_type": "swing_live_order_dry_run_status",\n' >> "$STATUS_PATH"
  printf '  "target_date": "%s",\n' "$TARGET_DATE" >> "$STATUS_PATH"
  printf '  "status": "%s",\n' "$status" >> "$STATUS_PATH"
  printf '  "reason": "%s",\n' "$reason" >> "$STATUS_PATH"
  printf '  "started_at": "%s",\n' "$STARTED_AT" >> "$STATUS_PATH"
  printf '  "finished_at": "%s",\n' "$finished_at" >> "$STATUS_PATH"
  printf '  "exit_code": %s,\n' "$exit_code" >> "$STATUS_PATH"
  printf '  "log_path": "%s",\n' "$LOG_PATH" >> "$STATUS_PATH"
  printf '  "json_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_selection_funnel/swing_selection_funnel_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "markdown_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_selection_funnel/swing_selection_funnel_${TARGET_DATE}.md" >> "$STATUS_PATH"
  printf '  "lifecycle_audit_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_lifecycle_audit/swing_lifecycle_audit_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "threshold_ai_review_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_threshold_ai_review/swing_threshold_ai_review_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "improvement_automation_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_improvement_automation/swing_improvement_automation_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "runtime_approval_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_runtime_approval/swing_runtime_approval_${TARGET_DATE}.json" >> "$STATUS_PATH"
  printf '  "runtime_approval_markdown_artifact": "%s",\n' "$PROJECT_DIR/data/report/swing_runtime_approval/swing_runtime_approval_${TARGET_DATE}.md" >> "$STATUS_PATH"
  if run_lifecycle_audit_enabled; then
    printf '  "lifecycle_audit_mode": "inline",\n' >> "$STATUS_PATH"
  else
    printf '  "lifecycle_audit_mode": "postclose_deferred",\n' >> "$STATUS_PATH"
  fi
  printf '  "runtime_change": false\n' >> "$STATUS_PATH"
  printf '}\n' >> "$STATUS_PATH"
}

if [[ ! -x "$VENV_PY" ]]; then
  write_status "failed" 127 "venv_python_missing"
  echo "venv python missing: $VENV_PY"
  exit 127
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  write_status "skipped" 75 "lock_exists"
  echo "swing live dry-run report already running for ${TARGET_DATE}: ${LOCK_DIR}"
  exit 75
fi
trap 'rm -rf "$LOCK_DIR"' EXIT

set +e
PYTHONPATH=. "$VENV_PY" -m src.engine.swing_selection_funnel_report "$TARGET_DATE"
selection_rc=$?
if [[ "$selection_rc" -eq 0 ]] && run_lifecycle_audit_enabled; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit \
    --date "$TARGET_DATE" \
    --ai-review-provider "$SWING_THRESHOLD_AI_REVIEW_PROVIDER"
  lifecycle_rc=$?
else
  lifecycle_rc=0
fi
set -e

rc="$selection_rc"
if [[ "$selection_rc" -eq 0 && "$lifecycle_rc" -ne 0 ]]; then
  rc="$lifecycle_rc"
fi
if [[ "$selection_rc" -eq 0 && "$lifecycle_rc" -eq 0 ]] && run_lifecycle_audit_enabled; then
  runtime_approval_json="$PROJECT_DIR/data/report/swing_runtime_approval/swing_runtime_approval_${TARGET_DATE}.json"
  if [[ ! -s "$runtime_approval_json" ]]; then
    echo "runtime approval artifact missing after lifecycle audit: $runtime_approval_json"
    rc=66
  fi
fi

if [[ "$rc" -eq 0 ]]; then
  if run_lifecycle_audit_enabled; then
    write_status "succeeded" 0 "completed"
  else
    write_status "succeeded" 0 "selection_completed_lifecycle_deferred_to_postclose"
  fi
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  echo "[DONE] swing_live_dry_run target_date=${TARGET_DATE} finished_at=${finished_at}"
elif [[ "$rc" -eq 66 ]]; then
  write_status "failed" "$rc" "runtime_approval_missing"
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  echo "[FAIL] swing_live_dry_run target_date=${TARGET_DATE} exit_code=${rc} reason=runtime_approval_missing finished_at=${finished_at}"
else
  write_status "failed" "$rc" "report_command_failed"
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  echo "[FAIL] swing_live_dry_run target_date=${TARGET_DATE} exit_code=${rc} reason=report_command_failed finished_at=${finished_at}"
fi
exit "$rc"
