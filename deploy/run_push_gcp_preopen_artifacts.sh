#!/usr/bin/env bash
set -euo pipefail

# Push same-day AWS-generated PREOPEN artifacts to the GCP follower staging tree.
#
# Manual same-day recovery:
#   1. Generate AWS preopen artifacts for the chosen date:
#      THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live THRESHOLD_CYCLE_AUTO_APPLY=true THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true deploy/run_threshold_cycle_preopen.sh TARGET_DATE
#   2. Push the exact same TARGET_DATE to GCP:
#      GCP_PUSH_HOST=... GCP_PUSH_USER=... GCP_PUSH_PROJECT_DIR=/path/to/KORStockScan deploy/run_push_gcp_preopen_artifacts.sh TARGET_DATE
#
# This wrapper copies artifacts only. It does not generate preopen artifacts,
# read GCP state, or change broker/order/provider/runtime thresholds.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
STATUS_DIR="$PROJECT_DIR/data/report/gcp_preopen_push_status"
STATUS_FILE="$STATUS_DIR/gcp_preopen_push_${TARGET_DATE}.status.json"
PREOPEN_STATUS_FILE="$PROJECT_DIR/data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_${TARGET_DATE}.status.json"
APPLY_PLAN_FILE="$PROJECT_DIR/data/threshold_cycle/apply_plans/threshold_apply_${TARGET_DATE}.json"
RUNTIME_ENV_FILE="$PROJECT_DIR/data/threshold_cycle/runtime_env/threshold_runtime_env_${TARGET_DATE}.env"
RUNTIME_ENV_MANIFEST_FILE="$PROJECT_DIR/data/threshold_cycle/runtime_env/threshold_runtime_env_${TARGET_DATE}.json"
RUNTIME_ENV_VERIFY_FILE="$PROJECT_DIR/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_${TARGET_DATE}.json"

mkdir -p "$PROJECT_DIR/logs" "$STATUS_DIR"

PUSHED_FILES=()
REMOTE_DESTINATION=""

write_push_status() {
  local status="$1"
  local reason="${2:-}"
  local exit_code="${3:-0}"
  "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$status" "$reason" "$exit_code" "$REMOTE_DESTINATION" "${PUSHED_FILES[@]}" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, status, reason, exit_code, destination = sys.argv[2:7]
pushed_files = list(sys.argv[7:])
payload = {
    "schema_version": 1,
    "report_type": "gcp_preopen_push_status",
    "target_date": target_date,
    "status": status,
    "reason": reason or None,
    "exit_code": int(exit_code or 0),
    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "runtime_effect": False,
    "decision_authority": "artifact_transport_only",
    "destination": destination or None,
    "pushed_files": pushed_files,
}
if status in {"succeeded", "failed"}:
    payload["finished_at"] = payload["updated_at"]
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

fail_push() {
  local reason="$1"
  local exit_code="${2:-1}"
  echo "[FAIL] gcp-preopen-artifact-push target_date=$TARGET_DATE reason=$reason"
  write_push_status failed "$reason" "$exit_code" || true
  exit "$exit_code"
}

trap 'rc=$?; if [ "$rc" -ne 0 ]; then write_push_status failed command_failed "$rc" || true; echo "[FAIL] gcp-preopen-artifact-push target_date=$TARGET_DATE reason=command_failed exit_code=$rc"; fi' ERR

echo "[START] gcp-preopen-artifact-push target_date=$TARGET_DATE"
write_push_status running started 0

for required_var in GCP_PUSH_HOST GCP_PUSH_USER GCP_PUSH_PROJECT_DIR; do
  if [ -z "${!required_var:-}" ]; then
    fail_push "missing_env:${required_var}"
  fi
done

if [[ "$GCP_PUSH_PROJECT_DIR" == *"'"* ]]; then
  fail_push "invalid_env:GCP_PUSH_PROJECT_DIR_contains_single_quote"
fi

REMOTE_DESTINATION="${GCP_PUSH_USER}@${GCP_PUSH_HOST}:${GCP_PUSH_PROJECT_DIR}/data/threshold_cycle_remote"
REMOTE_APPLY_DIR="$GCP_PUSH_PROJECT_DIR/data/threshold_cycle_remote/apply_plans"
REMOTE_RUNTIME_DIR="$GCP_PUSH_PROJECT_DIR/data/threshold_cycle_remote/runtime_env"
REMOTE_REPORT_PREOPEN_STATUS_DIR="$GCP_PUSH_PROJECT_DIR/data/threshold_cycle_remote/report/threshold_cycle_preopen_status"

remote_quote() {
  if [[ "$1" == *"'"* ]]; then
    fail_push "remote_path_contains_single_quote"
  fi
  printf "'%s'" "$1"
}

validate_local_artifacts() {
  "$VENV_PY" - "$TARGET_DATE" "$PREOPEN_STATUS_FILE" "$APPLY_PLAN_FILE" "$RUNTIME_ENV_FILE" "$RUNTIME_ENV_MANIFEST_FILE" <<'PY'
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
        raise SystemExit(f"missing_local_artifact:{path}")

preopen_status = json.loads(preopen_status_path.read_text(encoding="utf-8"))
if preopen_status.get("target_date") != target_date:
    raise SystemExit("preopen_status_target_date_mismatch")
if preopen_status.get("status") != "succeeded":
    raise SystemExit(f"preopen_status_not_succeeded:{preopen_status.get('status')}")

apply_plan = json.loads(apply_plan_path.read_text(encoding="utf-8"))
if apply_plan.get("target_date") != target_date:
    raise SystemExit("apply_plan_target_date_mismatch")

runtime_manifest = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
if runtime_manifest.get("target_date") != target_date:
    raise SystemExit("runtime_env_manifest_target_date_mismatch")
if runtime_manifest.get("report_type") != "threshold_runtime_env":
    raise SystemExit(f"runtime_env_manifest_report_type_invalid:{runtime_manifest.get('report_type')}")
PY
}

if ! validation_output="$(validate_local_artifacts 2>&1)"; then
  fail_push "$validation_output"
fi

LOCAL_FILES=(
  "$PREOPEN_STATUS_FILE"
  "$APPLY_PLAN_FILE"
  "$RUNTIME_ENV_FILE"
  "$RUNTIME_ENV_MANIFEST_FILE"
)
REMOTE_FILES=(
  "$REMOTE_REPORT_PREOPEN_STATUS_DIR/threshold_cycle_preopen_${TARGET_DATE}.status.json"
  "$REMOTE_APPLY_DIR/threshold_apply_${TARGET_DATE}.json"
  "$REMOTE_RUNTIME_DIR/threshold_runtime_env_${TARGET_DATE}.env"
  "$REMOTE_RUNTIME_DIR/threshold_runtime_env_${TARGET_DATE}.json"
)
if [ -f "$RUNTIME_ENV_VERIFY_FILE" ]; then
  LOCAL_FILES+=("$RUNTIME_ENV_VERIFY_FILE")
  REMOTE_FILES+=("$REMOTE_RUNTIME_DIR/threshold_runtime_env_verify_${TARGET_DATE}.json")
fi

SSH_OPTS=()
SCP_OPTS=()
if [ -n "${GCP_PUSH_SSH_KEY:-}" ]; then
  SSH_OPTS+=("-i" "$GCP_PUSH_SSH_KEY")
  SCP_OPTS+=("-i" "$GCP_PUSH_SSH_KEY")
fi
if [ -n "${GCP_PUSH_PORT:-}" ]; then
  SSH_OPTS+=("-p" "$GCP_PUSH_PORT")
  SCP_OPTS+=("-P" "$GCP_PUSH_PORT")
fi

SSH_TARGET="${GCP_PUSH_USER}@${GCP_PUSH_HOST}"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "mkdir -p -- $(remote_quote "$REMOTE_APPLY_DIR") $(remote_quote "$REMOTE_RUNTIME_DIR")"
ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "mkdir -p -- $(remote_quote "$REMOTE_REPORT_PREOPEN_STATUS_DIR")"

for idx in "${!LOCAL_FILES[@]}"; do
  local_file="${LOCAL_FILES[$idx]}"
  remote_file="${REMOTE_FILES[$idx]}"
  remote_tmp="${remote_file}.tmp.aws_push_${TARGET_DATE}_$$"
  scp "${SCP_OPTS[@]}" "$local_file" "$SSH_TARGET:$remote_tmp"
  ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "mv -f -- $(remote_quote "$remote_tmp") $(remote_quote "$remote_file")"
  PUSHED_FILES+=("$local_file")
done

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
write_push_status succeeded completed 0
echo "[DONE] gcp-preopen-artifact-push target_date=$TARGET_DATE finished_at=$finished_at pushed_count=${#PUSHED_FILES[@]}"
