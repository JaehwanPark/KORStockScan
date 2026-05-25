#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$SCRIPT_DIR}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
AUTO_PROMOTE="${KORSTOCKSCAN_SWING_RETRAIN_AUTO_PROMOTE:-true}"
FORCE_RETRAIN="${KORSTOCKSCAN_SWING_RETRAIN_FORCE:-false}"
MODEL_TIER2_REVIEW_PROVIDER="${KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER:-openai}"
REMEDIATION_CONTEXT_JSON="{}"

LOG_DIR="$PROJECT_DIR/logs/swing_model_retrain"
STATUS_DIR="$PROJECT_DIR/data/report/swing_model_retrain/status"
LOCK_ROOT="$PROJECT_DIR/tmp"
LOG_PATH="$LOG_DIR/swing_model_retrain_${TARGET_DATE}.log"
STATUS_PATH="$STATUS_DIR/swing_model_retrain_${TARGET_DATE}.status.json"
REPORT_PATH="$PROJECT_DIR/data/report/swing_model_retrain/swing_model_retrain_${TARGET_DATE}.json"
LOCK_DIR="$LOCK_ROOT/swing_model_retrain_${TARGET_DATE}.lock"
STARTED_AT="$(TZ=Asia/Seoul date --iso-8601=seconds)"

mkdir -p "$LOG_DIR" "$STATUS_DIR" "$LOCK_ROOT"
exec > >(tee -a "$LOG_PATH") 2>&1
echo "[START] swing_model_retrain target_date=${TARGET_DATE} started_at=${STARTED_AT}"
trap 'failed_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"; echo "[FAIL] swing_model_retrain target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

write_status() {
  local status="$1"
  local exit_code="$2"
  local reason="$3"
  local finished_at
  local status_py
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  status_py="$VENV_PY"
  if [[ ! -x "$status_py" ]]; then
    status_py="$(command -v python3 || true)"
  fi
  if [[ -z "$status_py" ]]; then
    printf '{"schema_version":1,"report_type":"swing_model_retrain_status","target_date":"%s","status":"%s","reason":"%s","exit_code":%s}\n' \
      "$TARGET_DATE" "$status" "$reason" "$exit_code" > "$STATUS_PATH"
    return
  fi
  STATUS_VALUE="$status" \
  EXIT_CODE_VALUE="$exit_code" \
  REASON_VALUE="$reason" \
  TARGET_DATE_VALUE="$TARGET_DATE" \
  STARTED_AT_VALUE="$STARTED_AT" \
  FINISHED_AT_VALUE="$finished_at" \
  LOG_PATH_VALUE="$LOG_PATH" \
  REPORT_PATH_VALUE="$REPORT_PATH" \
  STATUS_PATH_VALUE="$STATUS_PATH" \
  REMEDIATION_CONTEXT_VALUE="$REMEDIATION_CONTEXT_JSON" \
  "$status_py" - <<'PY'
import json
import os
from pathlib import Path

report_path = Path(os.environ["REPORT_PATH_VALUE"])
status_path = Path(os.environ["STATUS_PATH_VALUE"])
payload = {}
if report_path.exists():
    try:
        loaded = json.loads(report_path.read_text(encoding="utf-8"))
        payload = loaded if isinstance(loaded, dict) else {}
    except Exception:
        payload = {}

promotion = payload.get("promotion") if isinstance(payload.get("promotion"), dict) else {}
report_remediation = payload.get("remediation") if isinstance(payload.get("remediation"), dict) else {}
try:
    remediation_context = json.loads(os.environ.get("REMEDIATION_CONTEXT_VALUE") or "{}")
    if not isinstance(remediation_context, dict):
        remediation_context = {}
except Exception:
    remediation_context = {}
if not remediation_context:
    remediation_context = report_remediation or (promotion.get("remediation") if isinstance(promotion.get("remediation"), dict) else {})

def _object(value):
    return value if isinstance(value, dict) else {}

def _retry_env_keys(value):
    keys = value.get("retry_env_keys") if isinstance(value, dict) else []
    if keys:
        return keys
    retry_env = value.get("retry_env") if isinstance(value, dict) and isinstance(value.get("retry_env"), dict) else {}
    return sorted(retry_env)

status_payload = {
    "schema_version": 1,
    "report_type": "swing_model_retrain_status",
    "target_date": os.environ["TARGET_DATE_VALUE"],
    "status": os.environ["STATUS_VALUE"],
    "reason": os.environ["REASON_VALUE"],
    "started_at": os.environ["STARTED_AT_VALUE"],
    "finished_at": os.environ["FINISHED_AT_VALUE"],
    "exit_code": int(os.environ["EXIT_CODE_VALUE"]),
    "log_path": os.environ["LOG_PATH_VALUE"],
    "json_artifact": os.environ["REPORT_PATH_VALUE"],
    "promotion_guard": _object(payload.get("promotion_guard")),
    "ai_tier2_review": _object(payload.get("ai_tier2_review")) or _object(promotion.get("ai_tier2_review")),
    "selected_candidate_family": payload.get("candidate_family"),
    "current_manifest": promotion.get("current_manifest"),
    "recommendation_smoke": _object(promotion.get("smoke")),
    "rollback_files": promotion.get("rollback_files") or [],
    "remediation_applied": bool(remediation_context.get("remediation_applied")),
    "remediation_state": remediation_context.get("remediation_state"),
    "retry_count": remediation_context.get("retry_count"),
    "retry_env_keys": _retry_env_keys(remediation_context),
    "remediation": remediation_context,
    "runtime_change": "model_artifact_promote_only_if_guard_passed",
}
status_path.write_text(json.dumps(status_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

read_report_status() {
  if [[ -x "$VENV_PY" && -f "$REPORT_PATH" ]]; then
    "$VENV_PY" - "$REPORT_PATH" <<'PY' || true
import json
import sys
from pathlib import Path

try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(str(payload.get("status") or ""))
except Exception:
    print("")
PY
  fi
}

if [[ ! -x "$VENV_PY" ]]; then
  write_status "failed" 127 "venv_python_missing"
  echo "venv python missing: $VENV_PY"
  exit 127
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  write_status "skipped" 75 "lock_exists"
  echo "swing model retrain already running for ${TARGET_DATE}: ${LOCK_DIR}"
  exit 75
fi
trap 'rm -rf "$LOCK_DIR"' EXIT

cd "$PROJECT_DIR"

resolve_remediation() {
  "$VENV_PY" -m src.model.swing_model_auto_remediation --resolve-cron "$TARGET_DATE" 2>/dev/null || printf '{}\n'
}

apply_remediation_env() {
  local context_json="$1"
  "$VENV_PY" - "$context_json" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    payload = {}
retry_env = payload.get("retry_env") if isinstance(payload.get("retry_env"), dict) else {}
for key, value in sorted(retry_env.items()):
    print(f"{key}={str(value)}")
PY
}

REMEDIATION_CONTEXT_JSON="$(resolve_remediation)"
remediation_action="$("$VENV_PY" - "$REMEDIATION_CONTEXT_JSON" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    payload = {}
print(payload.get("action") or "ignore")
PY
)"
if [[ "$remediation_action" = "apply_retry_env" ]]; then
  while IFS='=' read -r key value; do
    [[ -z "$key" ]] && continue
    export "$key=$value"
  done < <(apply_remediation_env "$REMEDIATION_CONTEXT_JSON")
  FORCE_RETRAIN="${KORSTOCKSCAN_SWING_RETRAIN_FORCE:-$FORCE_RETRAIN}"
  MODEL_TIER2_REVIEW_PROVIDER="${KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER:-$MODEL_TIER2_REVIEW_PROVIDER}"
  echo "[INFO] swing_model_retrain remediation retry env applied: ${REMEDIATION_CONTEXT_JSON}"
elif [[ "$remediation_action" = "exit" ]]; then
  remediation_state="$("$VENV_PY" - "$REMEDIATION_CONTEXT_JSON" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    payload = {}
print(payload.get("remediation_state") or "manual_required")
PY
)"
  write_status "remediation_${remediation_state}" 0 "remediation_${remediation_state}"
  echo "[DONE] swing_model_retrain target_date=${TARGET_DATE} status=remediation_${remediation_state}"
  exit 0
fi

args=(--date "$TARGET_DATE")
if [[ "$AUTO_PROMOTE" = "true" || "$AUTO_PROMOTE" = "1" ]]; then
  args+=(--auto-promote)
fi
if [[ "$FORCE_RETRAIN" = "true" || "$FORCE_RETRAIN" = "1" ]]; then
  args+=(--force)
fi

set +e
KORSTOCKSCAN_SWING_MODEL_TIER2_REVIEW_PROVIDER="$MODEL_TIER2_REVIEW_PROVIDER" \
PYTHONPATH=. "$VENV_PY" -m src.model.swing_retrain_pipeline "${args[@]}"
rc=$?
set -e

if [[ "$rc" -eq 0 ]]; then
  report_status="$(read_report_status)"
  if [[ "$report_status" = "not_promoted_ai_tier2_blocked" ]]; then
    write_status "blocked_ai_tier2" 0 "ai_tier2_not_approved"
  else
    write_status "succeeded" 0 "completed"
  fi
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  echo "[DONE] swing_model_retrain target_date=${TARGET_DATE} status=$(read_report_status) finished_at=${finished_at}"
else
  write_status "failed" "$rc" "pipeline_failed"
  finished_at="$(TZ=Asia/Seoul date --iso-8601=seconds)"
  echo "[FAIL] swing_model_retrain target_date=${TARGET_DATE} exit_code=${rc} reason=pipeline_failed finished_at=${finished_at}"
fi
exit "$rc"
