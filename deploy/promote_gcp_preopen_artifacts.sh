#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
STATUS_DIR="$PROJECT_DIR/data/report/gcp_preopen_bridge_status"
STATUS_FILE="$STATUS_DIR/gcp_preopen_bridge_${TARGET_DATE}.status.json"

STAGING_ROOT="$PROJECT_DIR/data/threshold_cycle_remote"
LIVE_ROOT="$PROJECT_DIR/data/threshold_cycle"
STAGING_REPORT_ROOT="$STAGING_ROOT/report"
LIVE_REPORT_ROOT="$PROJECT_DIR/data/report"

STAGING_APPLY_FILE="$STAGING_ROOT/apply_plans/threshold_apply_${TARGET_DATE}.json"
STAGING_RUNTIME_ENV_FILE="$STAGING_ROOT/runtime_env/threshold_runtime_env_${TARGET_DATE}.env"
STAGING_RUNTIME_ENV_MANIFEST_FILE="$STAGING_ROOT/runtime_env/threshold_runtime_env_${TARGET_DATE}.json"
STAGING_RUNTIME_ENV_VERIFY_FILE="$STAGING_ROOT/runtime_env/threshold_runtime_env_verify_${TARGET_DATE}.json"
STAGING_PREOPEN_STATUS_FILE="$STAGING_REPORT_ROOT/threshold_cycle_preopen_status/threshold_cycle_preopen_${TARGET_DATE}.status.json"

LIVE_APPLY_FILE="$LIVE_ROOT/apply_plans/threshold_apply_${TARGET_DATE}.json"
LIVE_RUNTIME_ENV_FILE="$LIVE_ROOT/runtime_env/threshold_runtime_env_${TARGET_DATE}.env"
LIVE_RUNTIME_ENV_MANIFEST_FILE="$LIVE_ROOT/runtime_env/threshold_runtime_env_${TARGET_DATE}.json"
LIVE_RUNTIME_ENV_VERIFY_FILE="$LIVE_ROOT/runtime_env/threshold_runtime_env_verify_${TARGET_DATE}.json"
LIVE_PREOPEN_STATUS_FILE="$LIVE_REPORT_ROOT/threshold_cycle_preopen_status/threshold_cycle_preopen_${TARGET_DATE}.status.json"

PROMOTED_FILES=()

mkdir -p "$STATUS_DIR" "$LIVE_ROOT/apply_plans" "$LIVE_ROOT/runtime_env" "$LIVE_REPORT_ROOT/threshold_cycle_preopen_status"

write_bridge_status() {
  local status="$1"
  local reason="${2:-}"
  local exit_code="${3:-0}"
  "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$status" "$reason" "$exit_code" "${PROMOTED_FILES[@]}" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, status, reason, exit_code = sys.argv[2:6]
promoted_files = list(sys.argv[6:])
payload = {
    "schema_version": 1,
    "report_type": "gcp_preopen_bridge_status",
    "target_date": target_date,
    "status": status,
    "reason": reason or None,
    "exit_code": int(exit_code or 0),
    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "runtime_effect": False,
    "decision_authority": "artifact_promotion_only",
    "promoted_files": promoted_files,
}
if status in {"succeeded", "failed", "skipped"}:
    payload["finished_at"] = payload["updated_at"]
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

fail_bridge() {
  local reason="$1"
  local exit_code="${2:-1}"
  echo "[FAIL] gcp-preopen-bridge target_date=$TARGET_DATE reason=$reason"
  write_bridge_status failed "$reason" "$exit_code" || true
  exit "$exit_code"
}

trap 'rc=$?; if [ "$rc" -ne 0 ]; then write_bridge_status failed command_failed "$rc" || true; echo "[FAIL] gcp-preopen-bridge target_date=$TARGET_DATE reason=command_failed exit_code=$rc"; fi' ERR

echo "[START] gcp-preopen-bridge target_date=$TARGET_DATE"
write_bridge_status running started 0

validate_staging_artifacts() {
  "$VENV_PY" - "$TARGET_DATE" \
    "$STAGING_PREOPEN_STATUS_FILE" \
    "$STAGING_APPLY_FILE" \
    "$STAGING_RUNTIME_ENV_FILE" \
    "$STAGING_RUNTIME_ENV_MANIFEST_FILE" <<'PY'
import json
import sys
from pathlib import Path

target_date = sys.argv[1]
preopen_status_path = Path(sys.argv[2])
apply_plan_path = Path(sys.argv[3])
runtime_env_path = Path(sys.argv[4])
runtime_manifest_path = Path(sys.argv[5])

for path in [preopen_status_path, apply_plan_path, runtime_env_path, runtime_manifest_path]:
    if not path.exists():
        raise SystemExit(f"missing_staging_artifact:{path}")

preopen_status = json.loads(preopen_status_path.read_text(encoding="utf-8"))
if preopen_status.get("target_date") != target_date:
    raise SystemExit("staging_preopen_status_target_date_mismatch")
if preopen_status.get("status") != "succeeded":
    raise SystemExit(f"staging_preopen_status_not_succeeded:{preopen_status.get('status')}")

apply_plan = json.loads(apply_plan_path.read_text(encoding="utf-8"))
if apply_plan.get("target_date") != target_date:
    raise SystemExit("staging_apply_plan_target_date_mismatch")

runtime_manifest = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
if runtime_manifest.get("target_date") != target_date:
    raise SystemExit("staging_runtime_env_manifest_target_date_mismatch")
if runtime_manifest.get("report_type") != "threshold_runtime_env":
    raise SystemExit(f"staging_runtime_env_manifest_report_type_invalid:{runtime_manifest.get('report_type')}")
PY
}

if [ ! -f "$STAGING_RUNTIME_ENV_FILE" ] && [ ! -f "$STAGING_APPLY_FILE" ] && [ ! -f "$STAGING_RUNTIME_ENV_MANIFEST_FILE" ] && [ ! -f "$STAGING_PREOPEN_STATUS_FILE" ]; then
  echo "[SKIP] gcp-preopen-bridge target_date=$TARGET_DATE reason=no_staging_artifacts"
  write_bridge_status skipped no_staging_artifacts 0
  exit 0
fi

if ! validation_output="$(validate_staging_artifacts 2>&1)"; then
  fail_bridge "$validation_output"
fi

promote_file() {
  local src="$1"
  local dst="$2"
  local tmp="${dst}.tmp.bridge_${TARGET_DATE}_$$"
  cp "$src" "$tmp"
  mv -f "$tmp" "$dst"
  PROMOTED_FILES+=("$dst")
}

promote_file "$STAGING_PREOPEN_STATUS_FILE" "$LIVE_PREOPEN_STATUS_FILE"
promote_file "$STAGING_APPLY_FILE" "$LIVE_APPLY_FILE"
promote_file "$STAGING_RUNTIME_ENV_FILE" "$LIVE_RUNTIME_ENV_FILE"
promote_file "$STAGING_RUNTIME_ENV_MANIFEST_FILE" "$LIVE_RUNTIME_ENV_MANIFEST_FILE"

if [ -f "$STAGING_RUNTIME_ENV_VERIFY_FILE" ]; then
  promote_file "$STAGING_RUNTIME_ENV_VERIFY_FILE" "$LIVE_RUNTIME_ENV_VERIFY_FILE"
fi

write_bridge_status succeeded promoted 0
echo "[DONE] gcp-preopen-bridge target_date=$TARGET_DATE promoted_count=${#PROMOTED_FILES[@]}"
