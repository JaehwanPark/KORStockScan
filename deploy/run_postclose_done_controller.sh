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
CODEX_MAX_ORDERS="${POSTCLOSE_DONE_CONTROLLER_CODEX_MAX_ORDERS:-5}"
CODEX_COMMIT="${POSTCLOSE_DONE_CONTROLLER_CODEX_COMMIT:-true}"
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

env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.postclose_done_controller "${controller_args[@]}"

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
  codex_args=(--date "$TARGET_DATE" --max-orders "$CODEX_MAX_ORDERS")
  if [[ "$CODEX_COMMIT" == "1" || "$CODEX_COMMIT" == "true" ]]; then
    codex_args+=(--commit)
  fi
  if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
    codex_args+=(--dry-run)
  fi
  env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.codex_workorder_runner "${codex_args[@]}"
fi

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_done_controller target_date=${TARGET_DATE} finished_at=${finished_at}"
