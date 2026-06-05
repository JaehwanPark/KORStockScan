#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
if [[ -n "${VENV_PY:-}" ]]; then
  VENV_PY="$VENV_PY"
elif [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  VENV_PY="$PROJECT_DIR/.venv/bin/python"
elif [[ -x "$PROJECT_DIR/venv/bin/python" ]]; then
  VENV_PY="$PROJECT_DIR/venv/bin/python"
elif [[ -x "$PROJECT_DIR/.venv/Scripts/python.exe" ]]; then
  VENV_PY="$PROJECT_DIR/.venv/Scripts/python.exe"
elif [[ -x "$PROJECT_DIR/venv/Scripts/python.exe" ]]; then
  VENV_PY="$PROJECT_DIR/venv/Scripts/python.exe"
else
  VENV_PY="python"
fi
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
MAX_ATTEMPTS="${POSTCLOSE_DONE_CONTROLLER_MAX_ATTEMPTS:-3}"
PREDECESSOR_WAIT_SEC="${POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_WAIT_SEC:-60}"
PREDECESSOR_TIMEOUT_SEC="${POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC:-14400}"
ALLOW_WRAPPER_RERUN="${POSTCLOSE_DONE_CONTROLLER_ALLOW_WRAPPER_RERUN:-true}"
RUN_CODEX="${POSTCLOSE_DONE_CONTROLLER_RUN_CODEX:-true}"
CODEX_BATCH_SIZE="${POSTCLOSE_DONE_CONTROLLER_CODEX_BATCH_SIZE:-${POSTCLOSE_DONE_CONTROLLER_CODEX_MAX_ORDERS:-5}}"
CODEX_MODEL_POLICY="${POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL_POLICY:-credit_min}"
CODEX_MODEL="${POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL:-}"
CODEX_EFFORT="${POSTCLOSE_DONE_CONTROLLER_CODEX_EFFORT:-}"
CODEX_COMMIT="${POSTCLOSE_DONE_CONTROLLER_CODEX_COMMIT:-true}"
CODEX_AUTO_PUSH_MAIN="${POSTCLOSE_DONE_CONTROLLER_AUTO_PUSH_MAIN:-true}"
REQUIRE_CODEX_COMPLETED="${POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED:-true}"
DRY_RUN="${POSTCLOSE_DONE_CONTROLLER_DRY_RUN:-false}"

cd "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/logs"

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] postclose_done_controller target_date=${TARGET_DATE} started_at=${started_at}"

controller_args=(
  --date "$TARGET_DATE"
  --max-attempts "$MAX_ATTEMPTS"
  --predecessor-wait-sec "$PREDECESSOR_WAIT_SEC"
  --predecessor-timeout-sec "$PREDECESSOR_TIMEOUT_SEC"
)
if [[ "$ALLOW_WRAPPER_RERUN" == "1" || "$ALLOW_WRAPPER_RERUN" == "true" ]]; then
  controller_args+=(--allow-wrapper-rerun)
fi
if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
  controller_args+=(--dry-run)
fi

env PYTHONPATH=. POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED=false "$VENV_PY" -m src.engine.automation.postclose_done_controller "${controller_args[@]}"

if [[ "$RUN_CODEX" == "1" || "$RUN_CODEX" == "true" ]]; then
  controller_report="$PROJECT_DIR/data/report/postclose_done_controller/postclose_done_controller_${TARGET_DATE}.json"
  controller_status="$("$VENV_PY" - "$controller_report" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("missing_or_invalid")
    raise SystemExit(0)
print(str(payload.get("status") or "missing"))
PY
)"
  if [[ "$controller_status" != "done" && "$controller_status" != "dry_run_planned" ]]; then
    echo "[SKIP] codex_workorder_runner target_date=${TARGET_DATE} controller_status=${controller_status}"
    exit 1
  fi
  codex_args=(--date "$TARGET_DATE" --max-orders "$CODEX_BATCH_SIZE" --model-policy "$CODEX_MODEL_POLICY")
  if [[ -n "$CODEX_MODEL" ]]; then
    codex_args+=(--model "$CODEX_MODEL")
  fi
  if [[ -n "$CODEX_EFFORT" ]]; then
    codex_args+=(--effort "$CODEX_EFFORT")
  fi
  if [[ "$CODEX_COMMIT" == "1" || "$CODEX_COMMIT" == "true" ]]; then
    codex_args+=(--commit)
  else
    codex_args+=(--no-commit)
  fi
  if [[ "$CODEX_AUTO_PUSH_MAIN" == "1" || "$CODEX_AUTO_PUSH_MAIN" == "true" ]]; then
    codex_args+=(--auto-push-main)
  else
    codex_args+=(--no-auto-push-main)
  fi
  if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
    codex_args+=(--dry-run)
  fi
  codex_rc=0
  env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.codex_workorder_runner "${codex_args[@]}" || codex_rc=$?
  codex_report="$PROJECT_DIR/data/report/codex_workorder_runner/codex_workorder_runner_${TARGET_DATE}.json"
  codex_status="$("$VENV_PY" - "$codex_report" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("missing_or_invalid")
    raise SystemExit(0)
print(str(payload.get("status") or "missing"))
PY
)"
  if [[ "$codex_rc" -ne 0 ]]; then
    echo "[FAIL] codex_workorder_runner target_date=${TARGET_DATE} status=${codex_status} exit_code=${codex_rc}" >&2
    exit "$codex_rc"
  fi
  if [[ "$codex_status" != "completed" && "$codex_status" != "dry_run_planned" ]]; then
    echo "[FAIL] codex_workorder_runner target_date=${TARGET_DATE} status=${codex_status} strict_completion_required=true" >&2
    exit 1
  fi
  if [[ "$REQUIRE_CODEX_COMPLETED" == "1" || "$REQUIRE_CODEX_COMPLETED" == "true" ]]; then
    env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.postclose_done_controller "${controller_args[@]}" --require-codex-completed
  fi
elif [[ "$REQUIRE_CODEX_COMPLETED" == "1" || "$REQUIRE_CODEX_COMPLETED" == "true" ]]; then
  echo "[FAIL] codex_workorder_runner disabled while strict completion is required target_date=${TARGET_DATE}" >&2
  exit 1
fi

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_done_controller target_date=${TARGET_DATE} finished_at=${finished_at}"
