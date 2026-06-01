#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
POSTCLOSE_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
POSTCLOSE_STATUS_PATH="$PROJECT_DIR/data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_${POSTCLOSE_DATE}.status.json"
WAIT_TIMEOUT_SEC="${SWING_LDM_ROLLING_WAIT_TIMEOUT_SEC:-21600}"
WAIT_INTERVAL_SEC="${SWING_LDM_ROLLING_WAIT_INTERVAL_SEC:-60}"
LOCK_PATH="$PROJECT_DIR/tmp/swing_ldm_rolling_backfill_${POSTCLOSE_DATE}.lock"
LOG_DIR="$PROJECT_DIR/logs"
LOG_PATH="$LOG_DIR/swing_ldm_rolling_backfill_${POSTCLOSE_DATE}.log"
CRON_TAG="${SWING_LDM_ROLLING_CRON_TAG:-}"
SWING_DATES="${SWING_LDM_ROLLING_DATES:-2026-05-18 2026-05-19 2026-05-20 2026-05-21 2026-05-22 2026-05-26 2026-05-27 2026-05-28 2026-05-29 2026-06-01}"

mkdir -p "$PROJECT_DIR/tmp" "$LOG_DIR"
exec >> "$LOG_PATH" 2>&1

echo "[swing-ldm-rolling] start postclose_date=$POSTCLOSE_DATE started_at=$(TZ=Asia/Seoul date --iso-8601=seconds)"

if [ -n "$CRON_TAG" ]; then
  tmp_cron="$(mktemp)"
  trap 'rm -f "$tmp_cron"' EXIT
  crontab -l 2>/dev/null | grep -v "$CRON_TAG" > "$tmp_cron" || true
  crontab "$tmp_cron"
  echo "[swing-ldm-rolling] one-shot cron entry removed tag=$CRON_TAG"
fi

exec 9>"$LOCK_PATH"
if ! flock -n 9; then
  echo "[swing-ldm-rolling] skipped reason=lock_busy lock=$LOCK_PATH"
  exit 75
fi

cd "$PROJECT_DIR"

postclose_status() {
  "$VENV_PY" - "$POSTCLOSE_STATUS_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("missing")
    raise SystemExit(0)
print(str(payload.get("status") or "missing"))
PY
}

waited=0
while true; do
  status="$(postclose_status)"
  if [ "$status" = "succeeded" ]; then
    echo "[swing-ldm-rolling] postclose_ready date=$POSTCLOSE_DATE waited=${waited}s"
    break
  fi
  if [ "$status" = "failed" ] || [ "$status" = "skipped" ]; then
    echo "[swing-ldm-rolling] abort reason=postclose_terminal_status status=$status date=$POSTCLOSE_DATE"
    exit 2
  fi
  if [ "$waited" -ge "$WAIT_TIMEOUT_SEC" ]; then
    echo "[swing-ldm-rolling] abort reason=postclose_wait_timeout status=$status waited=${waited}s date=$POSTCLOSE_DATE"
    exit 3
  fi
  echo "[swing-ldm-rolling] waiting_postclose date=$POSTCLOSE_DATE status=$status waited=${waited}s"
  sleep "$WAIT_INTERVAL_SEC"
  waited=$((waited + WAIT_INTERVAL_SEC))
done

for target_date in $SWING_DATES; do
  echo "[swing-ldm-rolling] rebuild date=$target_date"
  bash "$PROJECT_DIR/deploy/run_swing_daily_simulation_report.sh" "$target_date"
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_sim --date "$target_date"
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_label_builder --date "$target_date" --refresh-matured
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_ev_report --date "$target_date"
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_decision_matrix --date "$target_date"
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_bucket_discovery --date "$target_date" --ai-provider openai
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit --date "$target_date" --ai-review-provider openai
done

echo "[swing-ldm-rolling] done postclose_date=$POSTCLOSE_DATE finished_at=$(TZ=Asia/Seoul date --iso-8601=seconds)"
