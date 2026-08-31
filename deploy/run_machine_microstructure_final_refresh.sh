#!/usr/bin/env bash

set -u

PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
PYTHON_BIN="${KORSTOCKSCAN_PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"

cd "$PROJECT_DIR" || exit 1
export PYTHONPATH="${PYTHONPATH:-$PROJECT_DIR}"

completed_target_date_rc=0
completed_target_date="$("$PYTHON_BIN" -c 'from src.engine.monitoring.machine_microstructure_attribution import resolve_completed_machine_target_date; print(resolve_completed_machine_target_date().isoformat())')" || completed_target_date_rc=$?
if ((completed_target_date_rc != 0)) || [[ ! "$completed_target_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  printf '[MACHINE_MICRO_FINAL_REFRESH] target_date=%s target_date_rc=%s\n' \
    "${completed_target_date:-unresolved}" "$completed_target_date_rc" >&2
  if ((completed_target_date_rc != 0)); then
    exit "$completed_target_date_rc"
  fi
  exit 2
fi

expansion_rc=0
"$PYTHON_BIN" -m src.engine.monitoring.widget_collector_expansion_recommendation \
  --target-date "$completed_target_date" \
  --write \
  --notify \
  --source-wait-sec 900 \
  --source-poll-sec 30 || expansion_rc=$?

attribution_rc=0
"$PYTHON_BIN" -m src.engine.monitoring.machine_microstructure_attribution \
  --target-date "$completed_target_date" \
  --write \
  --print-summary || attribution_rc=$?

weakness_hysteresis_rc=0
if ((attribution_rc == 0)); then
  "$PYTHON_BIN" -m src.engine.automation.market_weakness_hysteresis_tuning \
    --target-date "$completed_target_date" \
    --write \
    --print-summary || weakness_hysteresis_rc=$?
fi

entry_timing_rc=0
if ((attribution_rc == 0)); then
  "$PYTHON_BIN" -m src.engine.automation.machine_entry_timing_tuning \
    --target-date "$completed_target_date" \
    --write \
    --print-summary || entry_timing_rc=$?
else
  entry_timing_rc=0
fi

policy_rc=0
"$PYTHON_BIN" -m src.engine.automation.machine_microstructure_policy_approval \
  --phase postclose \
  --target-date "$completed_target_date" \
  --write \
  --notify \
  --notify-objective-followups || policy_rc=$?

# The checklist is the durable fallback for every upstream producer or
# notification failure. Always refresh it from the completed KRX machine date.
builder_rc=0
"$PYTHON_BIN" -m src.engine.build_next_stage2_checklist \
  --completed-machine-source-date "$completed_target_date" || builder_rc=$?

# The builder is the durable fallback and therefore has highest failure
# priority. Policy/notification failure is next, followed by weakness
# hysteresis tuning, entry timing, attribution, and expansion. All codes remain
# visible even when an earlier producer failed and fallback steps still ran.
printf '[MACHINE_MICRO_FINAL_REFRESH] target_date=%s expansion_rc=%s attribution_rc=%s weakness_hysteresis_rc=%s entry_timing_rc=%s policy_rc=%s builder_rc=%s\n' \
  "$completed_target_date" "$expansion_rc" "$attribution_rc" "$weakness_hysteresis_rc" "$entry_timing_rc" "$policy_rc" "$builder_rc" >&2

if ((builder_rc != 0)); then
  exit "$builder_rc"
fi
if ((policy_rc != 0)); then
  exit "$policy_rc"
fi
if ((weakness_hysteresis_rc != 0)); then
  exit "$weakness_hysteresis_rc"
fi
if ((entry_timing_rc != 0)); then
  exit "$entry_timing_rc"
fi
if ((attribution_rc != 0)); then
  exit "$attribution_rc"
fi
exit "$expansion_rc"
