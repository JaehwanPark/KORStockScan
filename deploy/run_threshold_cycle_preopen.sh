#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
STATUS_DIR="$PROJECT_DIR/data/report/threshold_cycle_preopen_status"
STATUS_FILE="$STATUS_DIR/threshold_cycle_preopen_${TARGET_DATE}.status.json"
BOOTSTRAP_ENV="$PROJECT_DIR/data/runtime/policy_bootstrap/runtime_policy_bootstrap_${TARGET_DATE}.env"

mkdir -p "$PROJECT_DIR/logs" "$STATUS_DIR"

write_status() {
  local status="$1" reason="${2:-}" exit_code="${3:-0}"
  "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$status" "$reason" "$exit_code" "$BOOTSTRAP_ENV" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, status, reason, exit_code, env_file = sys.argv[2:7]
payload = {
    "schema_version": 2,
    "report_type": "runtime_policy_preopen_status",
    "target_date": target_date,
    "status": status,
    "reason": reason or None,
    "exit_code": int(exit_code),
    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "runtime_effect": "approved_policy_bootstrap_only",
    "runtime_env_path": env_file,
    "runtime_env_exists": Path(env_file).exists(),
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
}

failed() {
  local rc="${1:-1}"
  trap - ERR
  write_status failed command_failed "$rc" || true
  echo "[FAIL] runtime-policy preopen target_date=$TARGET_DATE exit_code=$rc"
  exit "$rc"
}

trap 'failed "$?"' ERR
write_status running started 0
exec 9>"$PROJECT_DIR/logs/runtime_policy_preopen.lock"
if command -v flock >/dev/null 2>&1 && ! flock -n 9; then
  write_status skipped lock_busy 0
  echo "[SKIP] runtime-policy preopen already running target_date=$TARGET_DATE"
  exit 0
fi
cd "$PROJECT_DIR"

echo "[START] runtime-policy preopen target_date=$TARGET_DATE"

# Family publishers retain their own evidence and apply contracts. Failures do
# not manufacture a replacement candidate in the common bootstrap.
if ! PYTHONPATH=. "$VENV_PY" -m src.engine.automation.low_price_two_leg_policy_apply \
  --target-date "$TARGET_DATE" --write; then
  echo "[WARN] low-price family publisher failed; approved incumbent preserved"
fi
if ! PYTHONPATH=. "$VENV_PY" -m src.engine.automation.machine_microstructure_policy_approval \
  --phase preopen --target-date "$TARGET_DATE" --write --notify; then
  echo "[WARN] machine microstructure family publisher failed; approved incumbent preserved"
fi
if ! PYTHONPATH=. "$VENV_PY" -m src.engine.automation.machine_entry_timing_tuning \
  --phase preopen --target-date "$TARGET_DATE" --write; then
  echo "[WARN] machine entry-timing family publisher failed; approved incumbent preserved"
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.scanner_lookup_attention_policy \
  --target-date "$TARGET_DATE" --write
PYTHONPATH=. "$VENV_PY" -m src.engine.automation.scalp_trailing_mechanical_policy_apply \
  --target-date "$TARGET_DATE" --write

# Activate the next-day machine choice before bootstrap captures policy receipts.
# A missing candidate carries the current machine; a broken staged receipt
# fails the common PREOPEN handoff rather than silently using an unknown pair.
PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.mechanistic_entry_runtime_policy \
  --activate-dated-winrate --target-date "$TARGET_DATE"

# Select the reviewed AI successor before bootstrap captures policy receipts.
# An unqualified/mismatched candidate leaves the current pair unchanged.
if ! PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.mechanistic_entry_runtime_policy \
  --activate-dated-auxiliary --target-date "$TARGET_DATE"; then
  echo "[WARN] auxiliary successor not activated; current machine/AI pair preserved"
fi

bootstrap_args=(
  --date "$TARGET_DATE"
  --write
  --receipt "$PROJECT_DIR/data/threshold_cycle/low_price_two_leg/applied/low_price_two_leg_policy_${TARGET_DATE}.json"
  --receipt "$PROJECT_DIR/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_preopen_${TARGET_DATE}.json"
  --receipt "$PROJECT_DIR/data/report/machine_entry_timing_tuning/machine_entry_timing_tuning_${TARGET_DATE}.json"
  --receipt "$PROJECT_DIR/data/threshold_cycle/scanner_lookup_attention_preopen/scanner_lookup_attention_preopen_${TARGET_DATE}.json"
)
rising_missed_policy="$PROJECT_DIR/data/report/rising_missed_classifier_prior/rising_missed_tp1_policy_${TARGET_DATE}.json"
if [[ -s "$rising_missed_policy" ]]; then
  bootstrap_args+=(--receipt "$rising_missed_policy")
fi
scalp_trailing_policy="$PROJECT_DIR/data/report/scalp_trailing_mechanical_policy/scalp_trailing_mechanical_policy_${TARGET_DATE}.json"
bootstrap_args+=(--receipt "$scalp_trailing_policy")
PYTHONPATH=. "$VENV_PY" -m src.engine.automation.runtime_policy_bootstrap "${bootstrap_args[@]}"

entry_setup_args=(
  --all-cohorts
  --target-date "$TARGET_DATE"
  --runtime-env-file "$BOOTSTRAP_ENV"
  --operator-env-file "$PROJECT_DIR/data/threshold_cycle/runtime_env/operator_runtime_overrides.env"
  --dated-operator-env-file "$PROJECT_DIR/data/threshold_cycle/runtime_env/operator_runtime_overrides_${TARGET_DATE}.env"
  --write
)
if [[ "$TARGET_DATE" > "2026-09-14" ]]; then
  entry_setup_args+=(--require-machine-primary)
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.entry_setup_live_policy "${entry_setup_args[@]}"
PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.holding_prompt_live_policy \
  --phase preopen --target-date "$TARGET_DATE" --write

write_status succeeded completed 0
echo "[DONE] runtime-policy preopen target_date=$TARGET_DATE"
