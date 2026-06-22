#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
SOURCE_DATE="${THRESHOLD_CYCLE_SOURCE_DATE:-}"
APPLY_MODE="${THRESHOLD_CYCLE_APPLY_MODE:-auto_bounded_live}"
AUTO_APPLY="${THRESHOLD_CYCLE_AUTO_APPLY:-true}"
REQUIRE_AI="${THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI:-true}"
STATUS_DIR="$PROJECT_DIR/data/report/threshold_cycle_preopen_status"
STATUS_FILE="$STATUS_DIR/threshold_cycle_preopen_${TARGET_DATE}.status.json"
MANIFEST_CAPTURE_FILE="$STATUS_DIR/threshold_cycle_preopen_${TARGET_DATE}.manifest.json"

mkdir -p "$PROJECT_DIR/logs" "$STATUS_DIR"

write_preopen_status() {
  local status="$1"
  local reason="${2:-}"
  local exit_code="${3:-0}"
  local finished="${4:-0}"
  "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$APPLY_MODE" "$AUTO_APPLY" "$REQUIRE_AI" "$status" "$reason" "$exit_code" "$finished" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, apply_mode, auto_apply, require_ai, status, reason, exit_code, finished = sys.argv[2:10]
project_dir = path.parents[3]
apply_plan_path = project_dir / "data" / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target_date}.json"
runtime_env_path = project_dir / "data" / "threshold_cycle" / "runtime_env" / f"threshold_runtime_env_{target_date}.env"
runtime_env_manifest_path = project_dir / "data" / "threshold_cycle" / "runtime_env" / f"threshold_runtime_env_{target_date}.json"
payload = {}
if path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
payload.update(
    {
        "schema_version": 1,
        "report_type": "threshold_cycle_preopen_status",
        "target_date": target_date,
        "apply_mode": apply_mode,
        "auto_apply": auto_apply,
        "require_ai": require_ai,
        "status": status,
        "reason": reason or None,
        "exit_code": int(exit_code or 0),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": "preopen_runtime_env_apply_only",
        "apply_plan_path": str(apply_plan_path),
        "runtime_env_path": str(runtime_env_path),
        "runtime_env_manifest_path": str(runtime_env_manifest_path),
        "apply_plan_exists": apply_plan_path.exists(),
        "runtime_env_exists": runtime_env_path.exists(),
        "runtime_env_manifest_exists": runtime_env_manifest_path.exists(),
    }
)
payload.setdefault("started_at", payload["updated_at"])
if finished == "1":
    payload["finished_at"] = payload["updated_at"]
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

handle_preopen_apply_result() {
  local manifest_file="$1"
  local exit_code="$2"
  "$VENV_PY" - "$manifest_file" "$exit_code" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
exit_code = int(sys.argv[2])
if not manifest_path.exists():
    raise SystemExit(exit_code)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
status = str(manifest.get("status") or "")
runtime_change = bool(manifest.get("runtime_change"))
runtime_env_file = manifest.get("runtime_env_file")
runtime_env_ready = bool(runtime_env_file and Path(runtime_env_file).exists())

if (
    exit_code == 2
    and status == "operator_runtime_env_lock_ready_missing_source_report"
    and runtime_change
    and runtime_env_ready
):
    raise SystemExit(0)

raise SystemExit(exit_code)
PY
}

trap 'rc=$?; write_preopen_status failed command_failed "$rc" 1 || true; exit "$rc"' ERR
write_preopen_status running started 0 0
LOCK_FILE="$PROJECT_DIR/logs/threshold_cycle_preopen.lock"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  if ! flock -n 9; then
    echo "[SKIP] threshold-cycle preopen already running target_date=$TARGET_DATE lock_file=$LOCK_FILE"
    write_preopen_status skipped lock_busy 0 1
    exit 0
  fi
fi
cd "$PROJECT_DIR"

echo "[START] threshold-cycle preopen target_date=$TARGET_DATE apply_mode=$APPLY_MODE auto_apply=$AUTO_APPLY require_ai=$REQUIRE_AI"

args=(--date "$TARGET_DATE" --apply-mode "$APPLY_MODE")
if [ -n "$SOURCE_DATE" ]; then
  args+=(--source-date "$SOURCE_DATE")
fi
if [ "$AUTO_APPLY" = "true" ] || [ "$AUTO_APPLY" = "1" ]; then
  args+=(--auto-apply)
fi
if [ "$REQUIRE_AI" = "false" ] || [ "$REQUIRE_AI" = "0" ]; then
  args+=(--allow-deterministic-without-ai)
fi

manifest_output="$(
  set +e
  PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_preopen_apply "${args[@]}"
  echo "__THRESHOLD_PREOPEN_EXIT_CODE__:$?"
)"
manifest_exit_code="$(printf '%s\n' "$manifest_output" | awk -F: '/__THRESHOLD_PREOPEN_EXIT_CODE__:/ {print $2}' | tail -n1)"
manifest_json="$(printf '%s\n' "$manifest_output" | sed '/__THRESHOLD_PREOPEN_EXIT_CODE__:/d')"
printf '%s\n' "$manifest_json"
printf '%s\n' "$manifest_json" > "$MANIFEST_CAPTURE_FILE"
handle_preopen_apply_result "$MANIFEST_CAPTURE_FILE" "${manifest_exit_code:-1}"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
preopen_reason="completed"
if "$VENV_PY" - "$MANIFEST_CAPTURE_FILE" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(
    0
    if str(manifest.get("status") or "") == "operator_runtime_env_lock_ready_missing_source_report"
    else 1
)
PY
then
  preopen_reason="operator_runtime_env_lock_preserved_missing_source_report"
fi
write_preopen_status succeeded "$preopen_reason" 0 1
echo "[DONE] threshold-cycle preopen target_date=$TARGET_DATE finished_at=$finished_at"
