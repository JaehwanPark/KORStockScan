#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
RUN_PHASE="${THRESHOLD_CYCLE_CALIBRATION_PHASE:-intraday}"
AI_CORRECTION_PROVIDER="${THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER:-openai}"
AI_CORRECTION_RESPONSE_JSON="${THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON:-}"
AI_CORRECTION_MAX_ATTEMPTS="${THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS:-2}"
AI_CORRECTION_RETRY_DELAY_SEC="${THRESHOLD_CYCLE_AI_CORRECTION_RETRY_DELAY_SEC:-20}"
AI_CORRECTION_REUSE_IF_VALID="${THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID:-true}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"
CPU_AFFINITY="${THRESHOLD_CYCLE_CALIBRATION_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity threshold)}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] threshold-cycle calibration target_date=$TARGET_DATE phase=$RUN_PHASE failed_at=$failed_at"' ERR

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] threshold-cycle calibration target_date=$TARGET_DATE phase=$RUN_PHASE ai_correction_provider=$AI_CORRECTION_PROVIDER started_at=$started_at"

AI_CORRECTION_ARGS=(--ai-correction-provider "$AI_CORRECTION_PROVIDER")
if [ -n "$AI_CORRECTION_RESPONSE_JSON" ]; then
  AI_CORRECTION_ARGS=(--ai-correction-response-json "$AI_CORRECTION_RESPONSE_JSON")
elif [[ "$AI_CORRECTION_REUSE_IF_VALID" == "1" || "$AI_CORRECTION_REUSE_IF_VALID" == "true" ]]; then
  AI_CORRECTION_ARGS+=(--reuse-ai-review-if-valid)
fi

threshold_cycle_ai_review_status() {
  local path="$1"
  "$VENV_PY" - "$path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    print("missing")
    raise SystemExit(0)
print(str(payload.get("ai_status") or "missing"))
PY
}

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report \
  --date "$TARGET_DATE" \
  --skip-db \
  --calibration-run-phase "$RUN_PHASE" \
  --calibration-only \
  "${AI_CORRECTION_ARGS[@]}")

if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
  cmd=(taskset -c "$CPU_AFFINITY" "${cmd[@]}")
fi

ai_review_json="$PROJECT_DIR/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_${TARGET_DATE}_${RUN_PHASE}.json"
ai_correction_attempt=1
ai_correction_status="missing"
while true; do
  "${cmd[@]}"
  ai_correction_status="$(threshold_cycle_ai_review_status "$ai_review_json")"
  echo "[threshold-cycle] ai correction status target_date=$TARGET_DATE phase=$RUN_PHASE attempt=${ai_correction_attempt}/${AI_CORRECTION_MAX_ATTEMPTS} provider=$AI_CORRECTION_PROVIDER status=$ai_correction_status"
  if [ "$AI_CORRECTION_PROVIDER" = "none" ] || [ -n "$AI_CORRECTION_RESPONSE_JSON" ] || [ "$ai_correction_status" = "parsed" ] || [ "$ai_correction_attempt" -ge "$AI_CORRECTION_MAX_ATTEMPTS" ]; then
    break
  fi
  echo "[threshold-cycle] ai correction retry target_date=$TARGET_DATE phase=$RUN_PHASE next_attempt=$((ai_correction_attempt + 1)) delay=${AI_CORRECTION_RETRY_DELAY_SEC}s status=$ai_correction_status" >&2
  sleep "$AI_CORRECTION_RETRY_DELAY_SEC"
  ai_correction_attempt=$((ai_correction_attempt + 1))
done
if [ "$AI_CORRECTION_PROVIDER" != "none" ] && [ -z "$AI_CORRECTION_RESPONSE_JSON" ] && [ "$ai_correction_status" != "parsed" ]; then
  echo "[threshold-cycle] ai correction final unavailable target_date=$TARGET_DATE phase=$RUN_PHASE provider=$AI_CORRECTION_PROVIDER status=$ai_correction_status" >&2
  exit 1
fi

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] threshold-cycle calibration target_date=$TARGET_DATE phase=$RUN_PHASE finished_at=$finished_at"
