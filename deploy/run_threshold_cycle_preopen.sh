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

PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_preopen_apply "${args[@]}"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
write_preopen_status succeeded completed 0 1
echo "[DONE] threshold-cycle preopen target_date=$TARGET_DATE finished_at=$finished_at"
