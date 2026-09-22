#!/usr/bin/env bash

set -u

SCRIPT_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-$SCRIPT_PROJECT_DIR}"
PYTHON_BIN="${KORSTOCKSCAN_PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"

cd "$PROJECT_DIR" || exit 1
export PYTHONPATH="$PROJECT_DIR"

RECOVERY_MODE=false
if [[ $# -eq 2 && "$2" == "--recover-closed-target" ]]; then
  RECOVERY_MODE=true
elif (($# > 1)); then
  printf 'usage: %s [YYYY-MM-DD]\n' "$0" >&2
  exit 2
fi

completed_target_date_rc=0
resolved_target_date="$("$PYTHON_BIN" -c 'from src.engine.monitoring.machine_microstructure_attribution import resolve_completed_machine_target_date; print(resolve_completed_machine_target_date().isoformat())')" || completed_target_date_rc=$?
if ((completed_target_date_rc == 0)) && [[ ! "$resolved_target_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  completed_target_date_rc=2
fi
if ((completed_target_date_rc != 0)); then
  printf '[MACHINE_MICRO_FINAL_REFRESH] target_date=%s target_date_rc=%s reason=completed_target_date_resolution_failed\n' \
    "${resolved_target_date:-unresolved}" "$completed_target_date_rc" >&2
  exit "$completed_target_date_rc"
fi
completed_target_date="$resolved_target_date"
if (($# >= 1)); then
  requested_target_date="$1"
  normalized_target_date="$(date -d "$requested_target_date 00:00:00" +%F 2>/dev/null)" || completed_target_date_rc=2
  if ((completed_target_date_rc != 0)) || [[ "$normalized_target_date" != "$requested_target_date" ]]; then
    printf '[MACHINE_MICRO_FINAL_REFRESH] target_date=%s target_date_rc=2 reason=invalid_explicit_target_date\n' \
      "$requested_target_date" >&2
    exit 2
  fi
  if [[ "$requested_target_date" > "$resolved_target_date" || ( "$requested_target_date" != "$resolved_target_date" && "$RECOVERY_MODE" != "true" ) ]]; then
    printf '[MACHINE_MICRO_FINAL_REFRESH] target_date=%s target_date_rc=2 reason=explicit_target_date_not_current_completed resolved_target_date=%s\n' \
      "$requested_target_date" "$resolved_target_date" >&2
    exit 2
  fi
  completed_target_date="$requested_target_date"
fi

# Bind publication to the completed source before a long run crosses midnight.
export POSTCLOSE_POLICY_PUBLICATION_DATE="${POSTCLOSE_POLICY_PUBLICATION_DATE:-$completed_target_date}"
export POSTCLOSE_PREPARED_EFFECTIVE_DATE="$("$PYTHON_BIN" -c 'import sys; from src.engine.build_next_stage2_checklist import _next_krx_trading_day; print(_next_krx_trading_day(sys.argv[1]))' "$POSTCLOSE_POLICY_PUBLICATION_DATE")"

stage_args=()
if [[ "$RECOVERY_MODE" == "true" ]]; then stage_args+=(--recover-closed-target); fi
exec "$PYTHON_BIN" -m src.engine.automation.postclose_summary_handoff \
  --stage machine_group --date "$completed_target_date" \
  --publication-date "$POSTCLOSE_POLICY_PUBLICATION_DATE" "${stage_args[@]}"
