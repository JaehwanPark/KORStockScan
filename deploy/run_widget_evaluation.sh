#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-$SCRIPT_PROJECT_DIR}"
PYTHON_BIN="${KORSTOCKSCAN_PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"
EOD_WAIT_REQUIRED="${KORSTOCKSCAN_WIDGET_EVALUATION_WAIT_FOR_EOD:-true}"
EOD_WAIT_SEC="${KORSTOCKSCAN_WIDGET_EVALUATION_EOD_WAIT_SEC:-5400}"
EOD_WAIT_INTERVAL_SEC="${KORSTOCKSCAN_WIDGET_EVALUATION_EOD_WAIT_INTERVAL_SEC:-30}"
source "$SCRIPT_PROJECT_DIR/deploy/eod_terminal_gate.sh"

cd "$PROJECT_DIR"
# Python -c/-m searches cwd first; bind both cwd and imports to this code root.
export PYTHONPATH="$PROJECT_DIR"

if [[ "${POSTCLOSE_STAGE_WORKER:-0}" != "1" ]]; then
  target="${1:-$($PYTHON_BIN -c 'from src.engine.monitoring.widget_auto_trade_policy_calibration import resolve_completed_policy_target_date; print(resolve_completed_policy_target_date().isoformat())')}"
  stage_args=()
  if [[ "${2:-}" == "--recover-closed-target" ]]; then stage_args+=(--recover-closed-target); fi
  exec "$PYTHON_BIN" -m src.engine.automation.postclose_summary_handoff --stage widget_policy --date "$target" "${stage_args[@]}"
fi
completed_target_date="${POSTCLOSE_SOURCE_DATE:?stage source date required}"
RECOVERY_MODE=false
source_args=()
resume_signal=false
if [[ ( $# -eq 2 || ( $# -eq 3 && "$3" == "--resume-signal-research" ) ) && "$2" == "--recover-closed-target" ]]; then
  completed_target_date="$1"
  RECOVERY_MODE=true
  source_args=(--retained-source-only)
  if [[ $# -eq 3 ]]; then
    resume_signal=true
  fi
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [YYYY-MM-DD --recover-closed-target]" >&2
  exit 2
fi
"$PYTHON_BIN" - "$completed_target_date" <<'PYDATE'
from datetime import date, datetime
from zoneinfo import ZoneInfo
import sys
day = date.fromisoformat(sys.argv[1])
assert day.isoformat() == sys.argv[1] and day <= datetime.now(ZoneInfo("Asia/Seoul")).date()
PYDATE
mkdir -p "$PROJECT_DIR/tmp"
exec 9>"$PROJECT_DIR/tmp/widget_evaluation_${completed_target_date}.lock"
flock -n 9 || exit 75
if [[ ! "$completed_target_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  printf '[WIDGET_EVALUATION] invalid completed target date=%s\n' \
    "${completed_target_date:-missing}" >&2
  exit 2
fi

PHASE_BUDGET_SEC="${KORSTOCKSCAN_WIDGET_EVALUATION_PHASE_BUDGET_SEC:-5400}"
if [[ ! "$PHASE_BUDGET_SEC" =~ ^[0-9]+$ ]]; then
  printf '[WIDGET_EVALUATION] invalid phase budget target_date=%s\n' "$completed_target_date" >&2
  exit 2
fi
active_stage="initialization"
stage_started=0
trap 'stage_rc=$?; printf "[WIDGET_EVALUATION] failed target_date=%s stage=%s exit=%s wall=%ss\n" "$completed_target_date" "$active_stage" "$stage_rc" "$((SECONDS-stage_started))" >&2; exit "$stage_rc"' ERR
run_stage() {
  active_stage="$1"
  shift
  stage_started=$SECONDS
  printf '[WIDGET_EVALUATION] stage_start target_date=%s stage=%s phase_budget=%ss\n' \
    "$completed_target_date" "$active_stage" "$PHASE_BUDGET_SEC"
  if [[ "$PHASE_BUDGET_SEC" -gt 0 ]]; then
    /usr/bin/time -f '[WIDGET_EVALUATION] child_resources wall=%e user_cpu=%U system_cpu=%S peak_rss_kib=%M' \
      timeout --signal=TERM --kill-after=30 "$PHASE_BUDGET_SEC" "$@"
  else
    /usr/bin/time -f '[WIDGET_EVALUATION] child_resources wall=%e user_cpu=%U system_cpu=%S peak_rss_kib=%M' "$@"
  fi
  printf '[WIDGET_EVALUATION] stage_end target_date=%s stage=%s wall=%ss\n' \
    "$completed_target_date" "$active_stage" "$((SECONDS-stage_started))"
}

active_stage="eod_wait"
stage_started=$SECONDS
if [[ "$EOD_WAIT_REQUIRED" == "true" || "$EOD_WAIT_REQUIRED" == "1" ]]; then
  wait_for_eod_terminal "$PROJECT_DIR" "$completed_target_date" WIDGET_EVALUATION "$EOD_WAIT_SEC" "$EOD_WAIT_INTERVAL_SEC"
else
  printf '[WIDGET_EVALUATION] EOD gate skipped target_date=%s\n' "$completed_target_date"
fi
printf '[WIDGET_EVALUATION] stage_end target_date=%s stage=eod_wait wall=%ss\n' "$completed_target_date" "$((SECONDS-stage_started))"
if [[ "$resume_signal" != "true" ]]; then
run_stage advisory "$PYTHON_BIN" -m src.engine.monitoring.widget_advisory_calibration \
  --target-date "$completed_target_date" \
  --write
run_stage auto_policy "$PYTHON_BIN" -m src.engine.monitoring.widget_auto_trade_policy_calibration \
  --target-date "$completed_target_date" \
  --write
fi
run_stage signal_research "$PYTHON_BIN" -m src.engine.monitoring.widget_symbol_signal_policy_research \
  --end-date "$completed_target_date" "${source_args[@]}" \
  --write
run_stage runtime_policy "$PYTHON_BIN" -m src.engine.automation.machine_research_closed_loop_refresh \
  --source-date "$completed_target_date" --family widget --write --source-wait-sec 0

printf '[WIDGET_EVALUATION] completed target_date=%s\n' "$completed_target_date"
