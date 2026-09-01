#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Bash reads scripts lazily.  An editor replacing this wrapper while a long
# postclose run is active can therefore make the running shell parse a mixture
# of old and new lines.  Execute an immutable, syntax-checked sibling snapshot
# so source updates affect only the next invocation.
wrapper_snapshot="${THRESHOLD_CYCLE_WRAPPER_SNAPSHOT_PATH:-}"
ACTIVE_POSTCLOSE_PID=""
ACTIVE_POSTCLOSE_PGID=""
POSTCLOSE_GROUP_STARTING=false
POSTCLOSE_PENDING_SIGNAL=""
POSTCLOSE_OPERATING=false
POSTCLOSE_SIGNAL_GRACE_SEC="${THRESHOLD_CYCLE_SIGNAL_GRACE_SEC:-3}"
if ! [[ "$POSTCLOSE_SIGNAL_GRACE_SEC" =~ ^[0-9]+$ ]] || [ "$POSTCLOSE_SIGNAL_GRACE_SEC" -gt 30 ]; then
  POSTCLOSE_SIGNAL_GRACE_SEC=3
fi
cleanup_wrapper_snapshot() {
  local snapshot_dir="${wrapper_snapshot%/*}"
  local snapshot_name="${wrapper_snapshot##*/}"
  if [ -n "${wrapper_snapshot:-}" ] \
    && [ "$snapshot_dir" = "$SCRIPT_DIR" ] \
    && [[ "$snapshot_name" == .run_threshold_cycle_postclose.snapshot.*.sh ]] \
    && [ -e "$wrapper_snapshot" ]; then
    rm -f -- "$wrapper_snapshot"
  fi
}
terminate_active_postclose_group() {
  local signal_name="${1:-TERM}"
  local active_pid="${ACTIVE_POSTCLOSE_PID:-}"
  local active_pgid="${ACTIVE_POSTCLOSE_PGID:-}"
  local deadline=$((SECONDS + POSTCLOSE_SIGNAL_GRACE_SEC))
  if [[ "$active_pgid" =~ ^[0-9]+$ ]] && [ "$active_pgid" -gt 1 ]; then
    kill -s "$signal_name" -- "-$active_pgid" 2>/dev/null || true
    # A just-launched supervisor deliberately stops before starting the real
    # command.  Resume the owned group after queuing the terminating signal so
    # catchable signals can take effect without waiting for escalation.
    kill -CONT -- "-$active_pgid" 2>/dev/null || true
    while kill -0 -- "-$active_pgid" 2>/dev/null; do
      if [ "$SECONDS" -ge "$deadline" ]; then
        kill -KILL -- "-$active_pgid" 2>/dev/null || true
        break
      fi
      sleep 0.05
    done
  elif [[ "$active_pid" =~ ^[0-9]+$ ]] && [ "$active_pid" -gt 1 ]; then
    kill -s "$signal_name" "$active_pid" 2>/dev/null || true
  fi
  if [[ "$active_pid" =~ ^[0-9]+$ ]] && [ "$active_pid" -gt 1 ]; then
    wait "$active_pid" 2>/dev/null || true
  fi
  ACTIVE_POSTCLOSE_PID=""
  ACTIVE_POSTCLOSE_PGID=""
}
terminate_wrapper_children() {
  local signal_name="${1:-TERM}"
  local child_pids
  local child_pid
  terminate_active_postclose_group "$signal_name"
  # `jobs -pr` returns only waitable children owned by this shell. Avoid a
  # process-table scan whose stale PID could be reused by an unrelated process.
  child_pids="$(jobs -pr 2>/dev/null || true)"
  for child_pid in $child_pids; do
    if [[ "$child_pid" =~ ^[0-9]+$ ]] && [ "$child_pid" -ne "$$" ]; then
      kill -s "$signal_name" "$child_pid" 2>/dev/null || true
      kill -KILL "$child_pid" 2>/dev/null || true
      wait "$child_pid" 2>/dev/null || true
    fi
  done
}
handle_wrapper_signal() {
  local signal_name="${1:-TERM}"
  local exit_code=143
  local reason="terminated"
  if [ "$POSTCLOSE_GROUP_STARTING" = "true" ]; then
    POSTCLOSE_PENDING_SIGNAL="$signal_name"
    return 0
  fi
  case "$signal_name" in
    HUP) exit_code=129; reason="hangup" ;;
    INT) exit_code=130; reason="interrupted" ;;
    TERM) exit_code=143; reason="terminated" ;;
  esac
  terminate_wrapper_children "$signal_name"
  if [ "$POSTCLOSE_OPERATING" = "true" ]; then
    mark_postclose_failed "$reason" "$exit_code"
    restart_postclose_bot_if_requested
  fi
  exit "$exit_code"
}
trap cleanup_wrapper_snapshot EXIT
trap 'handle_wrapper_signal HUP' HUP
trap 'handle_wrapper_signal INT' INT
trap 'handle_wrapper_signal TERM' TERM
if [ "${THRESHOLD_CYCLE_WRAPPER_SNAPSHOT_EXECUTED:-false}" != "true" ]; then
  wrapper_snapshot_ready=false
  for _snapshot_attempt in 1 2 3; do
    wrapper_snapshot="$(mktemp "$SCRIPT_DIR/.run_threshold_cycle_postclose.snapshot.XXXXXX.sh")"
    cp -- "${BASH_SOURCE[0]}" "$wrapper_snapshot"
    chmod 700 "$wrapper_snapshot"
    if bash -n "$wrapper_snapshot"; then
      wrapper_snapshot_ready=true
      break
    fi
    rm -f -- "$wrapper_snapshot"
    wrapper_snapshot=""
    sleep 0.1
  done
  if [ "$wrapper_snapshot_ready" != "true" ]; then
    echo "[threshold-cycle] wrapper snapshot validation failed source=${BASH_SOURCE[0]}" >&2
    exit 2
  fi
  export THRESHOLD_CYCLE_WRAPPER_SNAPSHOT_EXECUTED=true
  export THRESHOLD_CYCLE_WRAPPER_SNAPSHOT_PATH="$wrapper_snapshot"
  exec bash "$wrapper_snapshot" "$@"
fi
# The exec'd shell already holds the immutable inode open.  Unlink it before
# doing any provider or postclose work so TERM/HUP/KILL cannot accumulate a
# sibling snapshot or leave a separate postclose child behind.
cleanup_wrapper_snapshot
wrapper_snapshot=""

PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"
# Compressed snapshots are intentionally capped at 5k input lines per collector
# invocation (one quarter of the default 20k uncompressed chunk).  Keep the
# default total input-line budget equivalent so a healthy, progressing gzip
# collection is not stopped before EOF solely because it needs more invocations.
MAX_ITERATIONS="${THRESHOLD_CYCLE_MAX_ITERATIONS:-320}"
MAX_INPUT_LINES="${THRESHOLD_CYCLE_MAX_INPUT_LINES_PER_CHUNK:-20000}"
MAX_OUTPUT_LINES="${THRESHOLD_CYCLE_MAX_OUTPUT_LINES_PER_PARTITION:-25000}"
MAX_CPU_BUSY_PCT="${THRESHOLD_CYCLE_MAX_CPU_BUSY_PCT:-95}"
POSTCLOSE_CPU_AFFINITY="${THRESHOLD_CYCLE_POSTCLOSE_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity threshold)}"
POSTCLOSE_NICE_LEVEL="${THRESHOLD_CYCLE_POSTCLOSE_NICE_LEVEL:-10}"
POSTCLOSE_IONICE_CLASS="${THRESHOLD_CYCLE_POSTCLOSE_IONICE_CLASS:-2}"
POSTCLOSE_IONICE_LEVEL="${THRESHOLD_CYCLE_POSTCLOSE_IONICE_LEVEL:-7}"
POSTCLOSE_RESOURCE_GUARD="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_GUARD:-true}"
POSTCLOSE_MIN_MEM_AVAILABLE_MB="${THRESHOLD_CYCLE_POSTCLOSE_MIN_MEM_AVAILABLE_MB:-4096}"
POSTCLOSE_MIN_SWAP_FREE_MB="${THRESHOLD_CYCLE_POSTCLOSE_MIN_SWAP_FREE_MB:-256}"
POSTCLOSE_MAX_SWAP_USED_PCT="${THRESHOLD_CYCLE_POSTCLOSE_MAX_SWAP_USED_PCT:-85}"
POSTCLOSE_MAX_IOWAIT_PCT="${THRESHOLD_CYCLE_POSTCLOSE_MAX_IOWAIT_PCT:-35}"
POSTCLOSE_MAX_SAMPLE_AGE_SEC="${THRESHOLD_CYCLE_POSTCLOSE_MAX_SAMPLE_AGE_SEC:-180}"
POSTCLOSE_MAX_LOAD1="${THRESHOLD_CYCLE_POSTCLOSE_MAX_LOAD1:-64}"
POSTCLOSE_RESOURCE_WAIT_SEC="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_WAIT_SEC:-300}"
POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC:-10}"
POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER:-true}"
POSTCLOSE_RESOURCE_SAMPLER_CMD="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_SAMPLER_CMD:-$PROJECT_DIR/deploy/run_system_metric_sampler_cron.sh}"
POSTCLOSE_BOT_ACTION="${THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION:-none}"
POSTCLOSE_BOT_SESSION="${THRESHOLD_CYCLE_POSTCLOSE_BOT_SESSION:-bot}"
POSTCLOSE_BOT_RESTART_WAIT_SEC="${THRESHOLD_CYCLE_POSTCLOSE_BOT_RESTART_WAIT_SEC:-5}"
COMPACT_AVAILABILITY_WAIT_SEC="${THRESHOLD_CYCLE_COMPACT_AVAILABILITY_WAIT_SEC:-900}"
COMPACT_AVAILABILITY_WAIT_INTERVAL_SEC="${THRESHOLD_CYCLE_COMPACT_AVAILABILITY_WAIT_INTERVAL_SEC:-15}"
SKIP_DB="${THRESHOLD_CYCLE_SKIP_DB:-false}"
USE_SNAPSHOT="${THRESHOLD_CYCLE_USE_SNAPSHOT:-true}"
AI_CORRECTION_PROVIDER="${THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER:-openai}"
AI_CORRECTION_RESPONSE_JSON="${THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON:-}"
AI_CORRECTION_MAX_ATTEMPTS="${THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS:-2}"
AI_CORRECTION_RETRY_DELAY_SEC="${THRESHOLD_CYCLE_AI_CORRECTION_RETRY_DELAY_SEC:-20}"
AI_CORRECTION_REUSE_IF_VALID="${THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID:-true}"
RUN_PATTERN_LABS="${THRESHOLD_CYCLE_RUN_PATTERN_LABS:-true}"
PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-${KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE:-2026-06-05}}"
RUN_SWING_POSTCLOSE="${THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE:-false}"
if [[ "$RUN_SWING_POSTCLOSE" == "true" || "$RUN_SWING_POSTCLOSE" == "1" ]]; then
  RUN_SWING_LIFECYCLE_AUDIT="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_AUDIT:-true}"
  RUN_SWING_STRATEGY_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_STRATEGY_DISCOVERY:-true}"
  RUN_SWING_LIFECYCLE_MATRIX="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_MATRIX:-$RUN_SWING_STRATEGY_DISCOVERY}"
  RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_SWING_LIFECYCLE_MATRIX}"
  RUN_DEEPSEEK_SWING_LAB="${THRESHOLD_CYCLE_RUN_DEEPSEEK_SWING_LAB:-true}"
  RUN_SWING_PATTERN_LAB_AUTOMATION="${THRESHOLD_CYCLE_RUN_SWING_PATTERN_LAB_AUTOMATION:-true}"
else
  RUN_SWING_LIFECYCLE_AUDIT=false
  RUN_SWING_STRATEGY_DISCOVERY=false
  RUN_SWING_LIFECYCLE_MATRIX=false
  RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY=false
  RUN_DEEPSEEK_SWING_LAB=false
  RUN_SWING_PATTERN_LAB_AUTOMATION=false
fi
WORKORDER_SWING_ARGS=()
PATTERN_LAB_SWING_ARGS=()
POSTCLOSE_SWING_SCOPE_ARGS=()
if [[ "$RUN_SWING_POSTCLOSE" != "true" && "$RUN_SWING_POSTCLOSE" != "1" ]]; then
  WORKORDER_SWING_ARGS+=(--exclude-swing)
  PATTERN_LAB_SWING_ARGS+=(--exclude-swing)
  POSTCLOSE_SWING_SCOPE_ARGS+=(--exclude-swing)
fi
SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-openai}"
# Postclose standard path defaults Swing lifecycle bucket discovery Tier2 review to OpenAI.
# Direct module execution still defaults to provider=none unless this wrapper/env passes a provider.
SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER:-$SWING_THRESHOLD_AI_REVIEW_PROVIDER}"
BUILD_CODE_IMPROVEMENT_WORKORDER="${THRESHOLD_CYCLE_BUILD_CODE_IMPROVEMENT_WORKORDER:-true}"
CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS="${CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS:-12}"
RUN_PANIC_SELL_DEFENSE_REPORT="${THRESHOLD_CYCLE_RUN_PANIC_SELL_DEFENSE_REPORT:-true}"
RUN_MARKET_PANIC_BREADTH_REPORT="${THRESHOLD_CYCLE_RUN_MARKET_PANIC_BREADTH_REPORT:-true}"
RUN_PIPELINE_EVENT_VERBOSITY_REPORT="${THRESHOLD_CYCLE_RUN_PIPELINE_EVENT_VERBOSITY_REPORT:-true}"
RUN_OBSERVATION_SOURCE_QUALITY_AUDIT="${THRESHOLD_CYCLE_RUN_OBSERVATION_SOURCE_QUALITY_AUDIT:-true}"
RUN_OPENING_ROTATION_PROFILE_TUNING="retired"
RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION="${THRESHOLD_CYCLE_RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION:-true}"
RUN_MAIN_AI_QUALITY_R0_R3="${THRESHOLD_CYCLE_RUN_MAIN_AI_QUALITY_R0_R3:-true}"
RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY="${THRESHOLD_CYCLE_RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY:-true}"
RUN_INTRADAY_WS_FRESHNESS_FINALIZE="${THRESHOLD_CYCLE_RUN_INTRADAY_WS_FRESHNESS_FINALIZE:-$RUN_MAIN_AI_QUALITY_R0_R3}"
MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY:-true}"
MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP:-390}"
MAIN_AI_QUALITY_DAILY_USD_CAP="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_DAILY_USD_CAP:-1.0}"
MAIN_AI_QUALITY_PARENT_CAP="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_PARENT_CAP:-130}"
RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION="${THRESHOLD_CYCLE_RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION:-true}"
RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT="${THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT:-false}"
RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}"
RUN_PATTERN_LAB_AI_REVIEW="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_AI_REVIEW:-true}"
PATTERN_LAB_AI_REVIEW_PROVIDER="${KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER:-openai}"
RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL="${THRESHOLD_CYCLE_RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL:-false}"
TIME_WINDOW_REGIME_MAX_RESUME_ATTEMPTS="${THRESHOLD_CYCLE_TIME_WINDOW_REGIME_MAX_RESUME_ATTEMPTS:-2}"
RUN_PRODUCER_GAP_DISCOVERY="${THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY:-false}"
PRODUCER_GAP_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_PROVIDER:-openai}"
RUN_STAGE_HOOK_WORKORDER_DISCOVERY="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY:-false}"
STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER:-openai}"
RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-false}"
RUN_PATTERN_LAB_PROPAGATION_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}"
RUN_SIM_POST_SELL_FEEDBACK="${THRESHOLD_CYCLE_RUN_SIM_POST_SELL_FEEDBACK:-true}"
RUN_SCALP_SIM_OVERNIGHT_REPORT="${THRESHOLD_CYCLE_RUN_SCALP_SIM_OVERNIGHT_REPORT:-true}"
RUN_SCALP_ENTRY_ADM="${THRESHOLD_CYCLE_RUN_SCALP_ENTRY_ADM:-true}"
RUN_ENTRY_SPLIT_ORDER_PLAN="${THRESHOLD_CYCLE_RUN_ENTRY_SPLIT_ORDER_PLAN:-true}"
RUN_SCALE_IN_SPLIT_ORDER_PLAN="${THRESHOLD_CYCLE_RUN_SCALE_IN_SPLIT_ORDER_PLAN:-true}"
RUN_ENTRY_AI_GATE_BACKTEST="${THRESHOLD_CYCLE_RUN_ENTRY_AI_GATE_BACKTEST:-true}"
# The observer is a persistent daily source-only policy. The postclose cron
# does not necessarily inherit the bot's PREOPEN runtime env, so run the report
# every day and let its activation/source checks expose a missing observer run.
# An explicit report override remains authoritative for emergency rollback.
if [[ -n "${THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT:-}" ]]; then
  RUN_LIMIT_DOWN_WATCH_REPORT="$THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT"
else
  RUN_LIMIT_DOWN_WATCH_REPORT=true
fi
RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE="${THRESHOLD_CYCLE_RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE:-true}"
RUN_RISING_MISSED_SCOUT_WORKORDER="${THRESHOLD_CYCLE_RUN_RISING_MISSED_SCOUT_WORKORDER:-true}"
RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE="${THRESHOLD_CYCLE_RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE:-true}"
RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION="${THRESHOLD_CYCLE_RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION:-true}"
RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION="${THRESHOLD_CYCLE_RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION:-true}"
RUN_RISING_MISSED_CLASSIFIER_PRIOR="${THRESHOLD_CYCLE_RUN_RISING_MISSED_CLASSIFIER_PRIOR:-true}"
RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY="${THRESHOLD_CYCLE_RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY:-true}"
RUN_SAMSUNG_MACHINE_ENTRY_TUNING="${THRESHOLD_CYCLE_RUN_SAMSUNG_MACHINE_ENTRY_TUNING:-true}"
RUN_LOW_PRICE_TWO_LEG_TUNING="${THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_TUNING:-true}"
RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION="${THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION:-true}"
RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION="${THRESHOLD_CYCLE_RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION:-true}"
RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL="${THRESHOLD_CYCLE_RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL:-true}"
ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER="${KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER:-openai}"
RUN_INSTITUTIONAL_FLOW_CONTEXT="${THRESHOLD_CYCLE_RUN_INSTITUTIONAL_FLOW_CONTEXT:-true}"
RUN_MICROSTRUCTURE_REACTION_CONTEXT="${THRESHOLD_CYCLE_RUN_MICROSTRUCTURE_REACTION_CONTEXT:-true}"
RUN_LIFECYCLE_DECISION_MATRIX="${THRESHOLD_CYCLE_RUN_LIFECYCLE_DECISION_MATRIX:-true}"
RUN_LIFECYCLE_AI_CONTEXT="${THRESHOLD_CYCLE_RUN_LIFECYCLE_AI_CONTEXT:-true}"
RUN_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_LIFECYCLE_DECISION_MATRIX}"
RUN_LDM_HYPOTHESIS_PARENT_REFINEMENT="${THRESHOLD_CYCLE_RUN_LDM_HYPOTHESIS_PARENT_REFINEMENT:-$RUN_LIFECYCLE_BUCKET_DISCOVERY}"
RUN_LIFECYCLE_BUCKET_WINDOWS="${THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_WINDOWS:-true}"
LIFECYCLE_BUCKET_WINDOWS="${THRESHOLD_CYCLE_LIFECYCLE_BUCKET_WINDOWS:-rolling5d,rolling10d,mtd}"
LIFECYCLE_BUCKET_PROMOTION_WINDOW="${THRESHOLD_CYCLE_LIFECYCLE_BUCKET_PROMOTION_WINDOW:-mtd}"
RUN_RUNTIME_APPLY_BRIDGE="${THRESHOLD_CYCLE_RUN_RUNTIME_APPLY_BRIDGE:-$RUN_LIFECYCLE_BUCKET_DISCOVERY}"
RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER="${THRESHOLD_CYCLE_RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER:-$RUN_LIFECYCLE_BUCKET_DISCOVERY}"
RUN_LATENCY_CLASSIFIER_RECOMMENDATION="${THRESHOLD_CYCLE_RUN_LATENCY_CLASSIFIER_RECOMMENDATION:-true}"
RUN_TUNING_PERFORMANCE_CONTROL_TOWER="${THRESHOLD_CYCLE_RUN_TUNING_PERFORMANCE_CONTROL_TOWER:-true}"
EV_SCOPE_ARGS=("${POSTCLOSE_SWING_SCOPE_ARGS[@]}")
if [[ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" != "true" && "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" != "1" ]]; then
  EV_SCOPE_ARGS+=(--disabled-source codebase_performance_workorder)
fi
if [[ "$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL" != "true" && "$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL" != "1" ]]; then
  EV_SCOPE_ARGS+=(--disabled-source time_window_regime_counterfactual)
fi
if [[ "$RUN_PRODUCER_GAP_DISCOVERY" != "true" && "$RUN_PRODUCER_GAP_DISCOVERY" != "1" ]]; then
  EV_SCOPE_ARGS+=(--disabled-source producer_gap_discovery)
fi
if [[ "$RUN_STAGE_HOOK_WORKORDER_DISCOVERY" != "true" && "$RUN_STAGE_HOOK_WORKORDER_DISCOVERY" != "1" ]]; then
  EV_SCOPE_ARGS+=(--disabled-source stage_hook_workorder_discovery)
fi
if [[ "$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD" != "true" && "$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD" != "1" ]]; then
  EV_SCOPE_ARGS+=(--disabled-source stage_hook_runtime_scaffold)
fi
export RUN_ENTRY_AI_GATE_BACKTEST
FORCE_DUPLICATE_REFRESH="${THRESHOLD_CYCLE_FORCE_DUPLICATE_REFRESH:-false}"
FORCE_LIFECYCLE_BUCKET_WINDOWS="${THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS:-false}"
FORCE_DEEP_AUDITS="${THRESHOLD_CYCLE_FORCE_DEEP_AUDITS:-false}"
FORCE_WORKORDER_BRANCH="${THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH:-false}"
REUSE_COMPLETED_REPORT_STEPS="${THRESHOLD_CYCLE_REUSE_COMPLETED_REPORT_STEPS:-true}"
POSTCLOSE_RECOVERY_REUSE_MODE=false
SNAPSHOT_RETENTION_DAYS="${THRESHOLD_CYCLE_SNAPSHOT_RETENTION_DAYS:-7}"
SNAPSHOT_TEMP_PATH=""
ARTIFACT_WAIT_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC:-600}"
ARTIFACT_WAIT_INTERVAL_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_INTERVAL_SEC:-5}"
STATUS_DIR="$PROJECT_DIR/data/report/threshold_cycle_postclose_status"
STATUS_FILE="$STATUS_DIR/threshold_cycle_postclose_${TARGET_DATE}.status.json"
POSTCLOSE_MARKER_LOG="${THRESHOLD_CYCLE_POSTCLOSE_MARKER_LOG:-$PROJECT_DIR/logs/threshold_cycle_postclose_cron.log}"
POSTCLOSE_MARKER_LOG_ENABLED="${THRESHOLD_CYCLE_POSTCLOSE_MARKER_LOG_ENABLED:-true}"
POSTCLOSE_BOT_ISOLATION_MARKER="$PROJECT_DIR/tmp/postclose_bot_isolation.json"
AI_CORRECTION_FINAL_STATUS="not_run"
AUTOMATION_TRIGGER_DECISION_REPORT_JSON="$PROJECT_DIR/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_${TARGET_DATE}.json"
AUTOMATION_TRIGGER_DECISION_CACHE_MARKER="$PROJECT_DIR/tmp/automation_trigger_decision_${TARGET_DATE}_$$.cached"
AUTOMATION_TRIGGER_DECISION_OUTPUT_TEMP="$PROJECT_DIR/tmp/automation_trigger_decision_${TARGET_DATE}_$$.out"
BACKFILL_OUTPUT_TEMP="$PROJECT_DIR/tmp/threshold_cycle_backfill_${TARGET_DATE}_$$.out"

mkdir -p "$PROJECT_DIR/logs" "$STATUS_DIR" "$PROJECT_DIR/tmp"
rm -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER"
cd "$PROJECT_DIR"

write_postclose_status() {
  local status="$1"
  local reason="${2:-}"
  local exit_code="${3:-0}"
  local finished="${4:-0}"
  "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$status" "$reason" "$exit_code" "$finished" "$AI_CORRECTION_PROVIDER" "$AI_CORRECTION_FINAL_STATUS" <<'PY'
import json
import os
import sys
from datetime import datetime
from pathlib import Path

path = Path(sys.argv[1])
target_date, status, reason, exit_code, finished, ai_provider, ai_status = sys.argv[2:9]
payload = {}
if path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
payload.update(
    {
        "schema_version": 1,
        "report_type": "threshold_cycle_postclose_status",
        "target_date": target_date,
        "status": status,
        "reason": reason or None,
        "exit_code": int(exit_code or 0),
        "ai_correction_provider": ai_provider,
        "ai_correction_status": ai_status,
        "producer_flags": {
            "entry_ai_gate_backtest": os.environ.get("RUN_ENTRY_AI_GATE_BACKTEST"),
        },
        "runtime_effect": False,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
)
payload.setdefault("started_at", payload["updated_at"])
if finished == "1":
    payload["finished_at"] = payload["updated_at"]
else:
    payload.pop("finished_at", None)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

detect_postclose_recovery_reuse_mode() {
  if [ "$REUSE_COMPLETED_REPORT_STEPS" != "true" ] && [ "$REUSE_COMPLETED_REPORT_STEPS" != "1" ]; then
    return 0
  fi
  if [ ! -s "$STATUS_FILE" ]; then
    return 0
  fi
  if "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
target_date = sys.argv[2]
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
is_recovery = (
    str(payload.get("target_date") or "") == target_date
    and str(payload.get("status") or "").lower() == "failed"
)
raise SystemExit(0 if is_recovery else 1)
PY
  then
    POSTCLOSE_RECOVERY_REUSE_MODE=true
  fi
}

postclose_marker_log_enabled() {
  [ "$POSTCLOSE_MARKER_LOG_ENABLED" = "true" ] || [ "$POSTCLOSE_MARKER_LOG_ENABLED" = "1" ]
}

emit_postclose_marker() {
  local line="$1"
  echo "$line"
  if postclose_marker_log_enabled; then
    mkdir -p "$(dirname "$POSTCLOSE_MARKER_LOG")"
    local stdout_target
    local marker_target
    stdout_target="$(readlink -f /proc/$$/fd/1 2>/dev/null || true)"
    marker_target="$(readlink -f "$POSTCLOSE_MARKER_LOG" 2>/dev/null || true)"
    if [ -n "$stdout_target" ] && [ "$stdout_target" = "$marker_target" ]; then
      return 0
    fi
    if ! printf '%s\n' "$line" >> "$POSTCLOSE_MARKER_LOG"; then
      echo "[threshold-cycle] marker log append failed path=$POSTCLOSE_MARKER_LOG" >&2
    fi
  fi
}

BOT_WAS_RUNNING=false
BOT_RESTART_DONE=false

write_postclose_bot_isolation_marker() {
  local started_at
  started_at="$(TZ=Asia/Seoul date +%FT%T%:z)"
  "$VENV_PY" - "$POSTCLOSE_BOT_ISOLATION_MARKER" "$TARGET_DATE" "$POSTCLOSE_BOT_SESSION" "$POSTCLOSE_BOT_ACTION" "$started_at" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
target_date, session, action, started_at = sys.argv[2:6]
payload = {
    "schema_version": 1,
    "active": True,
    "target_date": target_date,
    "session": session,
    "action": action,
    "reason": "threshold_cycle_postclose_resource_isolation",
    "started_at": started_at,
    "runtime_effect": False,
}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

clear_postclose_bot_isolation_marker() {
  rm -f "$POSTCLOSE_BOT_ISOLATION_MARKER"
}

bot_session_exists() {
  command -v tmux >/dev/null 2>&1 && tmux has-session -t "$POSTCLOSE_BOT_SESSION" 2>/dev/null
}

stop_postclose_bot_if_requested() {
  case "$POSTCLOSE_BOT_ACTION" in
    none|"")
      return 0
      ;;
    stop|restart)
      ;;
    *)
      echo "[threshold-cycle] postclose bot action ignored unknown_action=$POSTCLOSE_BOT_ACTION" >&2
      return 0
      ;;
  esac

  if bot_session_exists; then
    BOT_WAS_RUNNING=true
    echo "[threshold-cycle] stopping bot for postclose resource isolation session=$POSTCLOSE_BOT_SESSION action=$POSTCLOSE_BOT_ACTION"
    tmux kill-session -t "$POSTCLOSE_BOT_SESSION" 2>/dev/null || true
    write_postclose_bot_isolation_marker
    run_postclose_cmd sleep "$POSTCLOSE_BOT_RESTART_WAIT_SEC"
  else
    echo "[threshold-cycle] bot stop skipped reason=session_not_running session=$POSTCLOSE_BOT_SESSION action=$POSTCLOSE_BOT_ACTION"
    if [ "$POSTCLOSE_BOT_ACTION" = "restart" ]; then
      write_postclose_bot_isolation_marker
    fi
  fi
}

restart_postclose_bot_if_requested() {
  if [ "$POSTCLOSE_BOT_ACTION" != "restart" ] || [ "$BOT_RESTART_DONE" = "true" ]; then
    return 0
  fi
  BOT_RESTART_DONE=true
  if bot_session_exists; then
    echo "[threshold-cycle] bot restart skipped reason=session_already_running session=$POSTCLOSE_BOT_SESSION"
    clear_postclose_bot_isolation_marker
    return 0
  fi
  if [ "$BOT_WAS_RUNNING" = "true" ]; then
    echo "[threshold-cycle] restarting bot after postclose session=$POSTCLOSE_BOT_SESSION"
  else
    echo "[threshold-cycle] starting bot after postclose session=$POSTCLOSE_BOT_SESSION reason=restart_action_requested"
  fi
  tmux new-session -d -s "$POSTCLOSE_BOT_SESSION" \
    "/bin/bash -c 'cd \"$PROJECT_DIR/src\" && source ../.venv/bin/activate && ./run_bot.sh'" || {
      echo "[threshold-cycle] bot restart failed session=$POSTCLOSE_BOT_SESSION" >&2
      return 0
    }
  clear_postclose_bot_isolation_marker
}

mark_postclose_failed() {
  local reason="${1:-command_failed}"
  local rc="${2:-1}"
  local failed_at
  failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"
  write_postclose_status failed "$reason" "$rc" 1 || true
  emit_postclose_marker "[FAIL] threshold-cycle postclose target_date=$TARGET_DATE reason=$reason failed_at=$failed_at"
}

cleanup_threshold_cycle_snapshot_temp() {
  if [ -n "${SNAPSHOT_TEMP_PATH:-}" ] && [ -f "$SNAPSHOT_TEMP_PATH" ]; then
    rm -f -- "$SNAPSHOT_TEMP_PATH"
  fi
  if [ -n "${BACKFILL_OUTPUT_TEMP:-}" ] && [ -f "$BACKFILL_OUTPUT_TEMP" ]; then
    rm -f -- "$BACKFILL_OUTPUT_TEMP"
  fi
  if [ -n "${AUTOMATION_TRIGGER_DECISION_OUTPUT_TEMP:-}" ] \
    && [ -f "$AUTOMATION_TRIGGER_DECISION_OUTPUT_TEMP" ]; then
    rm -f -- "$AUTOMATION_TRIGGER_DECISION_OUTPUT_TEMP"
  fi
  if [ -n "${AUTOMATION_TRIGGER_DECISION_CACHE_MARKER:-}" ] \
    && [ -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER" ]; then
    rm -f -- "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER"
  fi
  cleanup_wrapper_snapshot
}

trap 'rc=$?; mark_postclose_failed command_failed "$rc"; restart_postclose_bot_if_requested; exit "$rc"' ERR
trap 'cleanup_threshold_cycle_snapshot_temp' EXIT
POSTCLOSE_OPERATING=true

run_postclose_cmd() {
  local cmd=("$@")
  local command_pid
  local command_rc=0
  local observed_pgid=""
  local observed_state=""
  local observed_process=""
  local pending_signal=""
  local supervisor_python="${VENV_PY:-/usr/bin/python3}"
  if command -v nice >/dev/null 2>&1; then
    cmd=(nice -n "$POSTCLOSE_NICE_LEVEL" "${cmd[@]}")
  fi
  if command -v ionice >/dev/null 2>&1 && [[ "$POSTCLOSE_IONICE_CLASS" -ge 0 ]]; then
    cmd=(ionice -c "$POSTCLOSE_IONICE_CLASS" -n "$POSTCLOSE_IONICE_LEVEL" -t "${cmd[@]}")
  fi
  if command -v taskset >/dev/null 2>&1 \
    && [[ -n "$POSTCLOSE_CPU_AFFINITY" ]] \
    && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
    cmd=(taskset -c "$POSTCLOSE_CPU_AFFINITY" "${cmd[@]}")
  fi
  if ! command -v setsid >/dev/null 2>&1 \
    || ! command -v ps >/dev/null 2>&1 \
    || [ ! -x "$supervisor_python" ]; then
    echo "[threshold-cycle] process-group isolation unavailable command=${cmd[0]}" >&2
    return 127
  fi
  POSTCLOSE_GROUP_STARTING=true
  POSTCLOSE_PENDING_SIGNAL=""
  # Keep a verified process-group leader alive even for commands such as
  # `true` that finish before the parent can inspect /proc.  The supervisor
  # stops before spawning the real command; the parent validates PID == PGID
  # and only then resumes it.  Signals received in this launch window are
  # recorded by handle_wrapper_signal and delivered to the verified group.
  setsid -- "$supervisor_python" -c '
import os
import signal
import subprocess
import sys

for signal_number in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
    signal.signal(signal_number, signal.SIG_DFL)
os.kill(os.getpid(), signal.SIGSTOP)
completed = subprocess.run(sys.argv[1:], check=False)
returncode = completed.returncode
raise SystemExit(returncode if returncode >= 0 else 128 - returncode)
  ' "${cmd[@]}" <&0 &
  command_pid=$!
  ACTIVE_POSTCLOSE_PID="$command_pid"
  for _pgid_attempt in {1..100}; do
    observed_process="$(ps -o pgid=,stat= -p "$command_pid" 2>/dev/null || true)"
    read -r observed_pgid observed_state <<< "$observed_process"
    observed_pgid="${observed_pgid//[[:space:]]/}"
    if [ "$observed_pgid" = "$command_pid" ] && [[ "$observed_state" == *T* ]]; then
      break
    fi
    if ! kill -0 "$command_pid" 2>/dev/null; then
      break
    fi
    sleep 0.01
  done
  if [ "$observed_pgid" != "$command_pid" ] || [[ "$observed_state" != *T* ]]; then
    if [ "$observed_pgid" = "$command_pid" ]; then
      kill -KILL -- "-$command_pid" 2>/dev/null || true
    else
      kill -KILL "$command_pid" 2>/dev/null || true
    fi
    wait "$command_pid" 2>/dev/null || command_rc=$?
    if [ "$command_rc" -eq 0 ]; then
      command_rc=125
    fi
    ACTIVE_POSTCLOSE_PID=""
    ACTIVE_POSTCLOSE_PGID=""
    POSTCLOSE_GROUP_STARTING=false
    pending_signal="$POSTCLOSE_PENDING_SIGNAL"
    POSTCLOSE_PENDING_SIGNAL=""
    if [ -n "$pending_signal" ]; then
      handle_wrapper_signal "$pending_signal"
    fi
    echo "[threshold-cycle] process-group isolation failed pid=$command_pid observed_pgid=${observed_pgid:-missing} observed_state=${observed_state:-missing}" >&2
    return "$command_rc"
  fi
  ACTIVE_POSTCLOSE_PGID="$command_pid"
  POSTCLOSE_GROUP_STARTING=false
  pending_signal="$POSTCLOSE_PENDING_SIGNAL"
  POSTCLOSE_PENDING_SIGNAL=""
  if [ -n "$pending_signal" ]; then
    # The verified supervisor is still stopped and has not spawned the real
    # command.  Kill it unconditionally so even a disposition inherited as
    # ignored by an unusual launcher cannot begin provider or postclose work.
    kill -KILL -- "-$command_pid" 2>/dev/null || true
    wait "$command_pid" 2>/dev/null || true
    ACTIVE_POSTCLOSE_PID=""
    ACTIVE_POSTCLOSE_PGID=""
    handle_wrapper_signal "$pending_signal"
  fi
  kill -CONT -- "-$command_pid"
  wait "$command_pid" || command_rc=$?
  ACTIVE_POSTCLOSE_PID=""
  ACTIVE_POSTCLOSE_PGID=""
  return "$command_rc"
}

detect_postclose_recovery_reuse_mode
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
write_postclose_status running started 0 0
emit_postclose_marker "[START] threshold-cycle postclose target_date=$TARGET_DATE max_iterations=$MAX_ITERATIONS recovery_reuse=$POSTCLOSE_RECOVERY_REUSE_MODE started_at=$started_at"
stop_postclose_bot_if_requested

reusable_completed_artifact() {
  local json_path="$1"
  local markdown_path="$2"
  local expected_report_type="$3"
  shift 3
  [ "$POSTCLOSE_RECOVERY_REUSE_MODE" = "true" ] || return 1
  "$VENV_PY" - "$json_path" "$markdown_path" "$TARGET_DATE" "$expected_report_type" "$@" <<'PY'
import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])
markdown_text = sys.argv[2]
target_date = sys.argv[3]
expected_report_type = sys.argv[4]
source_paths = [Path(value) for value in sys.argv[5:]]
if not json_path.is_file() or json_path.stat().st_size <= 0:
    raise SystemExit(1)
if markdown_text != "-":
    markdown_path = Path(markdown_text)
    if not markdown_path.is_file() or markdown_path.stat().st_size <= 0:
        raise SystemExit(1)
try:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if str(payload.get("target_date") or "") != target_date:
    raise SystemExit(1)
if expected_report_type != "-" and payload.get("report_type") != expected_report_type:
    raise SystemExit(1)

artifact_mtime = json_path.stat().st_mtime
if markdown_text != "-":
    artifact_mtime = min(artifact_mtime, markdown_path.stat().st_mtime)
for source_path in source_paths:
    if not source_path.exists():
        raise SystemExit(1)
    if source_path.is_dir():
        source_mtime = max(
            (child.stat().st_mtime for child in source_path.rglob("*") if child.is_file()),
            default=source_path.stat().st_mtime,
        )
    else:
        source_mtime = source_path.stat().st_mtime
    if source_mtime > artifact_mtime:
        raise SystemExit(1)

blocked_tokens = ("fail", "error", "retry", "source_blocked", "source_quality_blocked")
status_keys = {"status", "state", "report_status", "ai_status", "final_status"}

def has_blocked_status(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in status_keys and isinstance(item, str):
                normalized = item.strip().lower()
                if any(token in normalized for token in blocked_tokens):
                    return True
            if has_blocked_status(item):
                return True
    elif isinstance(value, list):
        return any(has_blocked_status(item) for item in value)
    return False

raise SystemExit(1 if has_blocked_status(payload) else 0)
PY
}

one_share_ai_review_reusable() {
  local json_path="$1"
  "$VENV_PY" - "$json_path" "$ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_provider = sys.argv[2]
review = payload.get("ai_review") if isinstance(payload.get("ai_review"), dict) else {}
valid = (
    expected_provider != "none"
    and review.get("provider") == expected_provider
    and review.get("status") == "parsed"
)
raise SystemExit(0 if valid else 1)
PY
}

low_price_candidate_recommendation_reusable() {
  local json_path="$1"
  "$VENV_PY" - "$json_path" "$TARGET_DATE" <<'PY'
import json
import sys
from pathlib import Path

from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import (
    CandidateRecommendationNotifier,
    REPORT_SCHEMA,
)

try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
target_date = sys.argv[2]
valid = (
    isinstance(payload, dict)
    and payload.get("schema") == REPORT_SCHEMA
    and payload.get("report_type") == "low_price_two_leg_expanded_candidate_research"
    and payload.get("target_date") == target_date
    and payload.get("end_date") == target_date
    and payload.get("status")
    in {
        "recommendations_ready",
        "no_qualified_candidate",
        "partial_source_quality",
        "source_quality_blocked",
    }
    and CandidateRecommendationNotifier._valid_report(payload)
    and payload.get("telegram_status")
    in {"sent", "duplicate", "sent_state_persist_failed"}
    and payload.get("authority")
    == "lower_price_machine_candidate_recommendation_only"
    and payload.get("recommendation_only") is True
    and payload.get("machine_created") is False
    and payload.get("service_started") is False
    and payload.get("runtime_effect") is False
    and payload.get("allowed_runtime_apply") is False
    and payload.get("actual_order_submitted") is False
    and payload.get("broker_order_forbidden") is True
    and isinstance(payload.get("recommendations"), list)
)
raise SystemExit(0 if valid else 1)
PY
}

resource_guard_enabled() {
  [ "$POSTCLOSE_RESOURCE_GUARD" = "true" ] || [ "$POSTCLOSE_RESOURCE_GUARD" = "1" ]
}

postclose_resource_status() {
  "$VENV_PY" - "$PROJECT_DIR/logs/system_metric_samples.jsonl" \
    "$POSTCLOSE_MIN_MEM_AVAILABLE_MB" \
    "$POSTCLOSE_MIN_SWAP_FREE_MB" \
    "$POSTCLOSE_MAX_SWAP_USED_PCT" \
    "$POSTCLOSE_MAX_IOWAIT_PCT" \
    "$MAX_CPU_BUSY_PCT" \
    "$POSTCLOSE_MAX_SAMPLE_AGE_SEC" \
    "$POSTCLOSE_MAX_LOAD1" <<'PY'
import json
import sys
import time
from pathlib import Path

path = Path(sys.argv[1])
min_mem = float(sys.argv[2])
min_swap_free = float(sys.argv[3])
max_swap = float(sys.argv[4])
max_iowait = float(sys.argv[5])
max_cpu_busy = float(sys.argv[6])
max_sample_age = float(sys.argv[7])
max_load1 = float(sys.argv[8])
if not path.exists():
    print(json.dumps({"ok": False, "issues": ["sampler_missing"]}))
    raise SystemExit(0)
last = None
with path.open("rb") as fh:
    try:
        fh.seek(-65536, 2)
    except OSError:
        fh.seek(0)
    lines = fh.read().decode("utf-8", errors="ignore").splitlines()
for line in lines[-200:]:
    line = line.strip()
    if not line:
        continue
    try:
        last = json.loads(line)
    except json.JSONDecodeError:
        continue
if not last:
    print(json.dumps({"ok": False, "issues": ["sampler_empty"]}))
    raise SystemExit(0)
memory = last.get("memory") or {}
cpu = last.get("cpu") or {}
loadavg = last.get("loadavg") or {}
swap_total = float(memory.get("swap_total_mb") or 0.0)
swap_free = float(memory.get("swap_free_mb") or 0.0)
swap_used_pct = 0.0
if swap_total > 0:
    swap_used_pct = ((swap_total - swap_free) / swap_total) * 100.0
mem_available = float(memory.get("mem_available_mb") or 0.0)
iowait = float(cpu.get("iowait_pct") or 0.0)
cpu_busy = float(cpu.get("cpu_busy_pct") or 0.0)
load1 = float(loadavg.get("1m") or 0.0)
sample_epoch = float(last.get("epoch") or 0.0)
sample_age_sec = max(0.0, time.time() - sample_epoch) if sample_epoch > 0 else 999999.0
issues = []
if sample_age_sec > max_sample_age:
    issues.append(f"sample_age_sec={sample_age_sec:.0f}>{max_sample_age:.0f}")
if mem_available < min_mem:
    issues.append(f"mem_available_mb={mem_available:.1f}<{min_mem:.1f}")
if swap_total > 0 and swap_free < min_swap_free:
    issues.append(f"swap_free_mb={swap_free:.1f}<{min_swap_free:.1f}")
if swap_used_pct > max_swap:
    issues.append(f"swap_used_pct={swap_used_pct:.1f}>{max_swap:.1f}")
if iowait > max_iowait:
    issues.append(f"iowait_pct={iowait:.1f}>{max_iowait:.1f}")
if cpu_busy > max_cpu_busy:
    issues.append(f"cpu_busy_pct={cpu_busy:.1f}>{max_cpu_busy:.1f}")
if load1 > max_load1:
    issues.append(f"load1={load1:.1f}>{max_load1:.1f}")
print(json.dumps({
    "ok": not issues,
    "issues": issues,
    "mem_available_mb": round(mem_available, 1),
    "swap_free_mb": round(swap_free, 1),
    "swap_used_pct": round(swap_used_pct, 1),
    "iowait_pct": round(iowait, 1),
    "cpu_busy_pct": round(cpu_busy, 1),
    "load1": round(load1, 1),
    "sample_age_sec": round(sample_age_sec, 1),
    "sample_ts": last.get("ts"),
}))
PY
}

refresh_postclose_resource_sample_if_stale() {
  local label="$1"
  local waited="$2"
  local status="$3"
  local stale
  if [ "$POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER" != "true" ] && [ "$POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER" != "1" ]; then
    return 1
  fi
  if [ "$waited" -ne 0 ] && [ $((waited % 60)) -ne 0 ]; then
    return 1
  fi
  stale="$(printf '%s' "$status" | "$VENV_PY" -c '
import json, sys
payload = json.load(sys.stdin)
issues = [str(item) for item in payload.get("issues") or []]
print(str(any(item.startswith("sample_age_sec=") or item in {"sampler_missing", "sampler_empty"} for item in issues)).lower())
')"
  if [ "$stale" != "true" ] || [ ! -x "$POSTCLOSE_RESOURCE_SAMPLER_CMD" ]; then
    return 1
  fi
  if run_postclose_cmd "$POSTCLOSE_RESOURCE_SAMPLER_CMD" >/dev/null 2>&1; then
    echo "[threshold-cycle] resource sampler refreshed label=$label waited=${waited}s command=$POSTCLOSE_RESOURCE_SAMPLER_CMD" >&2
    return 0
  fi
  echo "[threshold-cycle] resource sampler refresh failed label=$label waited=${waited}s command=$POSTCLOSE_RESOURCE_SAMPLER_CMD" >&2
  return 1
}

wait_for_postclose_resources() {
  local label="$1"
  local waited=0
  if ! resource_guard_enabled; then
    return 0
  fi
  while true; do
    local status ok
    status="$(postclose_resource_status)"
    ok="$(printf '%s' "$status" | "$VENV_PY" -c 'import json,sys; print(str(json.load(sys.stdin).get("ok", True)).lower())')"
    if [ "$ok" = "true" ]; then
      echo "[threshold-cycle] resource guard pass label=$label status=$status" >&2
      return 0
    fi
    if [ "$waited" -ge "$POSTCLOSE_RESOURCE_WAIT_SEC" ]; then
      echo "[threshold-cycle] resource guard timeout label=$label waited=${waited}s status=$status" >&2
      return 1
    fi
    refresh_postclose_resource_sample_if_stale "$label" "$waited" "$status" || true
    echo "[threshold-cycle] resource guard wait label=$label waited=${waited}s status=$status" >&2
    run_postclose_cmd sleep "$POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC"
    waited=$((waited + POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC))
  done
}

cleanup_threshold_cycle_snapshots() {
  local snapshot_dir="$1"
  local retention_days="$2"
  run_postclose_cmd python3 - "$snapshot_dir" "$retention_days" <<'PY'
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import re
import sys

snapshot_dir = Path(sys.argv[1])
retention_days = int(sys.argv[2])
if not snapshot_dir.exists():
    print("[threshold-cycle] snapshot cleanup skipped reason=missing_dir")
    raise SystemExit(0)

pattern = re.compile(r"pipeline_events_(\d{4}-\d{2}-\d{2})_(\d{8}_\d{6})\.jsonl(?:\.gz)?$")
groups: dict[str, list[Path]] = defaultdict(list)
for path in snapshot_dir.glob("pipeline_events_*.jsonl*"):
    match = pattern.match(path.name)
    if not match:
        continue
    groups[match.group(1)].append(path)

removed: list[Path] = []
cutoff_date = datetime.now() - timedelta(days=retention_days)
for date_key, paths in groups.items():
    paths = sorted(paths)
    keep = paths[-1]
    for path in paths[:-1]:
        removed.append(path)
    try:
        parsed_date = datetime.strptime(date_key, "%Y-%m-%d")
    except ValueError:
        parsed_date = None
    if parsed_date is not None and parsed_date < cutoff_date:
        removed.append(keep)

seen = set()
removed_unique = []
for path in removed:
    if path in seen or not path.exists():
        continue
    seen.add(path)
    removed_unique.append(path)

removed_bytes = 0
for path in removed_unique:
    removed_bytes += path.stat().st_size
    path.unlink()

print(
    f"[threshold-cycle] snapshot cleanup retention_days={retention_days} "
    f"removed={len(removed_unique)} removed_bytes={removed_bytes}"
)
PY
}

json_is_valid() {
  local path="$1"
  "$VENV_PY" - "$path" <<'PY' >/dev/null 2>&1
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
json.loads(path.read_text(encoding="utf-8"))
PY
}

wait_for_file_artifact() {
  local path="$1"
  local label="$2"
  local waited=0

  while [ ! -s "$path" ]; do
    if [ "$waited" -ge "$ARTIFACT_WAIT_SEC" ]; then
      echo "[threshold-cycle] artifact wait timeout label=$label path=$path waited=${waited}s" >&2
      return 1
    fi
    if [ "$waited" -eq 0 ]; then
      echo "[threshold-cycle] waiting for artifact label=$label path=$path"
    fi
    run_postclose_cmd sleep "$ARTIFACT_WAIT_INTERVAL_SEC"
    waited=$((waited + ARTIFACT_WAIT_INTERVAL_SEC))
  done

  echo "[threshold-cycle] artifact ready label=$label path=$path waited=${waited}s"
  return 0
}

wait_for_json_artifact() {
  local path="$1"
  local label="$2"
  local waited=0

  while true; do
    if [ -s "$path" ] && json_is_valid "$path"; then
      echo "[threshold-cycle] artifact ready label=$label path=$path waited=${waited}s json_valid=true"
      return 0
    fi
    if [ "$waited" -ge "$ARTIFACT_WAIT_SEC" ]; then
      echo "[threshold-cycle] artifact wait timeout label=$label path=$path waited=${waited}s json_valid=false" >&2
      return 1
    fi
    if [ "$waited" -eq 0 ]; then
      echo "[threshold-cycle] waiting for artifact label=$label path=$path json_check=pending"
    fi
    run_postclose_cmd sleep "$ARTIFACT_WAIT_INTERVAL_SEC"
    waited=$((waited + ARTIFACT_WAIT_INTERVAL_SEC))
  done
}

wait_for_report_artifact() {
  local json_path="$1"
  local md_path="$2"
  local label="$3"

  wait_for_json_artifact "$json_path" "$label.json"
  wait_for_file_artifact "$md_path" "$label.md"
}

bottom_rebound_source_contract_ok() {
  local path="$1"
  [ -s "$path" ] || return 1
  "$VENV_PY" - "$path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
ok = (
    payload.get("report_type") == "swing_bottom_rebound_candidate_source"
    and payload.get("decision_authority") == "swing_sim_candidate_source_only"
    and payload.get("runtime_effect") is False
    and payload.get("broker_order_forbidden") is True
    and payload.get("allowed_runtime_apply") is False
    and bool(payload.get("candidate_rows"))
)
raise SystemExit(0 if ok else 1)
PY
}

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

threshold_cycle_ev_refresh_decision() {
  local json_path="$1"
  local md_path="$2"
  local force_duplicate_refresh="$3"
  shift 3 || true

  if [ "$force_duplicate_refresh" = "true" ] || [ "$force_duplicate_refresh" = "1" ]; then
    printf 'run\n'
    return 0
  fi
  if [ "$#" -eq 0 ] || [ ! -s "$json_path" ] || [ ! -s "$md_path" ]; then
    printf 'run\n'
    return 0
  fi

  local source_path=""
  for source_path in "$@"; do
    if [ ! -e "$source_path" ]; then
      printf 'run\n'
      return 0
    fi
    if [ "$source_path" -nt "$json_path" ] || [ "$source_path" -nt "$md_path" ]; then
      printf 'run\n'
      return 0
    fi
  done
  printf 'skip\n'
}

automation_trigger_decision() {
  local step_id="$1"
  local decision="run"
  local output_temp="${AUTOMATION_TRIGGER_DECISION_OUTPUT_TEMP:-${TMPDIR:-/tmp}/korstockscan_automation_trigger_${TARGET_DATE}_$$.out}"
  AUTOMATION_TRIGGER_DECISION_RESULT="run"
  if [ ! -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER" ]; then
    if run_postclose_cmd env \
      THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS="$FORCE_LIFECYCLE_BUCKET_WINDOWS" \
      THRESHOLD_CYCLE_FORCE_DEEP_AUDITS="$FORCE_DEEP_AUDITS" \
      THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH="$FORCE_WORKORDER_BRANCH" \
      THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_WINDOWS="${RUN_LIFECYCLE_BUCKET_WINDOWS:-true}" \
      THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}" \
      THRESHOLD_CYCLE_RUN_PATTERN_LAB_AI_REVIEW="${RUN_PATTERN_LAB_AI_REVIEW:-true}" \
      THRESHOLD_CYCLE_RUN_OBSERVATION_SOURCE_QUALITY_AUDIT="${RUN_OBSERVATION_SOURCE_QUALITY_AUDIT:-true}" \
      THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT="${RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT:-false}" \
      THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY="${RUN_PRODUCER_GAP_DISCOVERY:-false}" \
      THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY="${RUN_STAGE_HOOK_WORKORDER_DISCOVERY:-false}" \
      THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-false}" \
      THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT="${RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}" \
      THRESHOLD_CYCLE_BUILD_CODE_IMPROVEMENT_WORKORDER="${BUILD_CODE_IMPROVEMENT_WORKORDER:-true}" \
      PYTHONPATH=. "$VENV_PY" -m src.engine.automation.automation_chain_trigger_decision \
        --date "$TARGET_DATE" \
        --scope all \
        --write >/dev/null 2>&1; then
      mkdir -p "$(dirname "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER")"
      : > "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER"
    fi
  fi
  if [ -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER" ] && [ -f "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON" ]; then
    if decision="$("$VENV_PY" - "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON" "$step_id" <<'PY'
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
step_id = sys.argv[2]
payload = json.loads(report_path.read_text(encoding="utf-8"))
decision = "run"
for item in payload.get("decisions", []):
    if item.get("step_id") == step_id:
        decision = str(item.get("decision") or "run")
        break
print(decision)
PY
    )"; then
      if [ "$decision" = "skip" ] || [ "$decision" = "disabled_success" ]; then
        AUTOMATION_TRIGGER_DECISION_RESULT="skip"
        return 0
      fi
      if [ "$decision" = "run" ]; then
        return 0
      fi
    fi
  fi
  rm -f -- "$output_temp"
  if run_postclose_cmd env \
    THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS="$FORCE_LIFECYCLE_BUCKET_WINDOWS" \
    THRESHOLD_CYCLE_FORCE_DEEP_AUDITS="$FORCE_DEEP_AUDITS" \
    THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH="$FORCE_WORKORDER_BRANCH" \
    THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_WINDOWS="${RUN_LIFECYCLE_BUCKET_WINDOWS:-true}" \
    THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}" \
    THRESHOLD_CYCLE_RUN_PATTERN_LAB_AI_REVIEW="${RUN_PATTERN_LAB_AI_REVIEW:-true}" \
    THRESHOLD_CYCLE_RUN_OBSERVATION_SOURCE_QUALITY_AUDIT="${RUN_OBSERVATION_SOURCE_QUALITY_AUDIT:-true}" \
    THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT="${RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT:-false}" \
    THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY="${RUN_PRODUCER_GAP_DISCOVERY:-false}" \
    THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY="${RUN_STAGE_HOOK_WORKORDER_DISCOVERY:-false}" \
    THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-false}" \
    THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT="${RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}" \
    THRESHOLD_CYCLE_BUILD_CODE_IMPROVEMENT_WORKORDER="${BUILD_CODE_IMPROVEMENT_WORKORDER:-true}" \
    PYTHONPATH=. "$VENV_PY" -m src.engine.automation.automation_chain_trigger_decision \
      --date "$TARGET_DATE" \
      --scope all \
      --step "$step_id" >"$output_temp" 2>/dev/null; then
    decision="$(<"$output_temp")"
    if [ "$decision" = "skip" ] || [ "$decision" = "disabled_success" ]; then
      AUTOMATION_TRIGGER_DECISION_RESULT="skip"
    fi
  fi
  rm -f -- "$output_temp"
  return 0
}

automation_trigger_reason() {
  local step_id="$1"
  if [ -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER" ] && [ -f "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON" ]; then
    "$VENV_PY" - "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON" "$step_id" <<'PY'
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
step_id = sys.argv[2]
payload = json.loads(report_path.read_text(encoding="utf-8"))
reason = "unknown_trigger_reason"
for item in payload.get("decisions", []):
    if item.get("step_id") != step_id:
        continue
    reasons = [str(value) for value in item.get("trigger_reasons", []) if str(value)]
    if reasons:
        reason = ",".join(reasons)
    break
print(reason)
PY
    return 0
  fi
  printf 'decision_cache_unavailable\n'
}

automation_trigger_source() {
  if [ -f "$AUTOMATION_TRIGGER_DECISION_CACHE_MARKER" ] && [ -f "$AUTOMATION_TRIGGER_DECISION_REPORT_JSON" ]; then
    printf 'cached_trigger_snapshot\n'
    return 0
  fi
  printf 'per_step_live_probe\n'
}

skip_triggered_step() {
  local step_id="$1"
  local reason="$2"
  local trigger_reason
  local trigger_source
  trigger_reason="$(automation_trigger_reason "$step_id" 2>/dev/null || printf 'unknown_trigger_reason\n')"
  trigger_source="$(automation_trigger_source)"
  emit_postclose_marker "[SKIP] threshold-cycle postclose target_date=$TARGET_DATE step=$step_id reason=$reason trigger_decision=skip trigger_reason=$trigger_reason trigger_source=$trigger_source"
}

run_threshold_cycle_ev_and_wait() {
  local pass_label="$1"
  shift || true
  local json_path="$PROJECT_DIR/data/report/threshold_cycle_ev/threshold_cycle_ev_${TARGET_DATE}.json"
  local md_path="$PROJECT_DIR/data/report/threshold_cycle_ev/threshold_cycle_ev_${TARGET_DATE}.md"

  wait_for_postclose_resources "threshold_cycle_ev_${pass_label}"
  if [ "$(threshold_cycle_ev_refresh_decision "$json_path" "$md_path" "$FORCE_DUPLICATE_REFRESH" "$@")" = "skip" ]; then
    emit_postclose_marker "[SKIP] threshold-cycle postclose target_date=$TARGET_DATE step=threshold_cycle_ev_${pass_label} reason=duplicate_refresh_fresh force_duplicate_refresh=$FORCE_DUPLICATE_REFRESH"
    wait_for_report_artifact "$json_path" "$md_path" "threshold_cycle_ev_${pass_label}"
    return 0
  fi
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_ev_report --date "$TARGET_DATE" "${EV_SCOPE_ARGS[@]}"
  wait_for_report_artifact "$json_path" "$md_path" "threshold_cycle_ev_${pass_label}"
}

next_stage2_checklist_path() {
  SOURCE_DATE="$TARGET_DATE" PYTHONPATH=. "$VENV_PY" - <<'PY'
import os

from src.engine.build_next_stage2_checklist import _next_krx_trading_day, stage2_checklist_path

source_date = os.environ["SOURCE_DATE"]
target_date = _next_krx_trading_day(source_date)
print(stage2_checklist_path(target_date))
PY
}

SOURCE_ARGS=()
if [ "$USE_SNAPSHOT" = "true" ]; then
  SNAPSHOT_DIR="$PROJECT_DIR/data/threshold_cycle/snapshots"
  CHECKPOINT_PATH="$PROJECT_DIR/data/threshold_cycle/checkpoints/${TARGET_DATE}.json"
  mkdir -p "$SNAPSHOT_DIR"
  SNAPSHOT_TS="$(TZ=Asia/Seoul date +%Y%m%d_%H%M%S)"
  RAW_SOURCE="$PROJECT_DIR/data/pipeline_events/pipeline_events_${TARGET_DATE}.jsonl"
  EXISTING_SNAPSHOT_PATH="$(
    find "$SNAPSHOT_DIR" -maxdepth 1 -type f \( -name "pipeline_events_${TARGET_DATE}_*.jsonl" -o -name "pipeline_events_${TARGET_DATE}_*.jsonl.gz" \) | sort | tail -n 1
  )"
  SNAPSHOT_PATH="$SNAPSHOT_DIR/pipeline_events_${TARGET_DATE}_${SNAPSHOT_TS}.jsonl.gz"
  if [ -f "$CHECKPOINT_PATH" ] && [ -n "$EXISTING_SNAPSHOT_PATH" ] && [ -f "$EXISTING_SNAPSHOT_PATH" ]; then
    SOURCE_ARGS=(--source-path "$EXISTING_SNAPSHOT_PATH")
    REUSE_EXISTING_SNAPSHOT="true"
    echo "[threshold-cycle] reusing immutable snapshot source=$EXISTING_SNAPSHOT_PATH checkpoint=$CHECKPOINT_PATH"
  elif [ -f "$RAW_SOURCE" ]; then
    if [ -n "$EXISTING_SNAPSHOT_PATH" ] && [ -f "$EXISTING_SNAPSHOT_PATH" ]; then
      echo "[threshold-cycle] removing orphan snapshot without checkpoint source=$EXISTING_SNAPSHOT_PATH"
      rm -f -- "$EXISTING_SNAPSHOT_PATH"
    fi
    SNAPSHOT_TEMP_PATH="${SNAPSHOT_PATH}.tmp.$$"
    run_postclose_cmd gzip -1 -c -- "$RAW_SOURCE" > "$SNAPSHOT_TEMP_PATH"
    if [ ! -s "$SNAPSHOT_TEMP_PATH" ]; then
      echo "[threshold-cycle] compressed snapshot is empty source=$RAW_SOURCE" >&2
      false
    fi
    mv -- "$SNAPSHOT_TEMP_PATH" "$SNAPSHOT_PATH"
    SNAPSHOT_TEMP_PATH=""
    SOURCE_ARGS=(--source-path "$SNAPSHOT_PATH")
    REUSE_EXISTING_SNAPSHOT="false"
    echo "[threshold-cycle] using immutable snapshot source=$SNAPSHOT_PATH"
  else
    echo "[threshold-cycle] raw source missing, falling back to default source target_date=$TARGET_DATE"
  fi
  cleanup_threshold_cycle_snapshots "$SNAPSHOT_DIR" "$SNAPSHOT_RETENTION_DAYS"
fi

compact_availability_waited=0
for i in $(seq 1 "$MAX_ITERATIONS"); do
  resume_args=(--resume)
  if [ "$i" = "1" ] && [ "$USE_SNAPSHOT" = "true" ] && [ "${REUSE_EXISTING_SNAPSHOT:-false}" != "true" ]; then
    resume_args=(--overwrite)
  fi
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events \
    --date "$TARGET_DATE" \
    --mode incremental \
    "${resume_args[@]}" \
    "${SOURCE_ARGS[@]}" \
    --max-input-lines-per-chunk "$MAX_INPUT_LINES" \
    --max-output-lines-per-partition "$MAX_OUTPUT_LINES" \
    --max-cpu-busy-pct "$MAX_CPU_BUSY_PCT" \
    > "$BACKFILL_OUTPUT_TEMP"
  out="$(<"$BACKFILL_OUTPUT_TEMP")"
  rm -f -- "$BACKFILL_OUTPUT_TEMP"
  echo "$out"
  summary_json="$(
    printf '%s\n' "$out" | "$VENV_PY" -c '
import json
import sys

for line in reversed(sys.stdin.read().splitlines()):
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        continue
    if isinstance(payload, dict):
        print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
        break
else:
    raise SystemExit("backfill summary JSON object missing from stdout")
'
  )"
  completed="$(printf '%s' "$summary_json" | "$VENV_PY" -c 'import json,sys; print(str(json.load(sys.stdin).get("completed", False)).lower())')"
  status="$(printf '%s' "$summary_json" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("status", ""))')"
  paused_reason="$(printf '%s' "$summary_json" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("paused_reason") or "")')"
  if [ "$completed" = "true" ]; then
    break
  fi
  if [ "$status" = "paused_by_availability_guard" ] && [ -n "$paused_reason" ]; then
    if [ "$compact_availability_waited" -ge "$COMPACT_AVAILABILITY_WAIT_SEC" ]; then
      echo "[threshold-cycle] availability guard timeout target_date=$TARGET_DATE reason=$paused_reason waited=${compact_availability_waited}s"
      break
    fi
    echo "[threshold-cycle] availability guard wait target_date=$TARGET_DATE reason=$paused_reason waited=${compact_availability_waited}s"
    run_postclose_cmd sleep "$COMPACT_AVAILABILITY_WAIT_INTERVAL_SEC"
    compact_availability_waited=$((compact_availability_waited + COMPACT_AVAILABILITY_WAIT_INTERVAL_SEC))
    continue
  fi
  compact_availability_waited=0
  run_postclose_cmd sleep 1
done

if [ "${completed:-false}" != "true" ]; then
  echo "[threshold-cycle] compact collection incomplete target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-}" >&2
  failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"
  failure_reason="compact_collection_incomplete:${status:-unknown}"
  if [ -n "${paused_reason:-}" ]; then
    failure_reason="${failure_reason}:${paused_reason}"
  fi
  write_postclose_status failed "$failure_reason" 2 1
  if [ "${status:-}" = "paused_by_availability_guard" ]; then
    emit_postclose_marker "[PAUSED] threshold-cycle postclose target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-} failed_at=$failed_at"
  fi
  emit_postclose_marker "[FAIL] threshold-cycle postclose target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-} failed_at=$failed_at"
  exit 2
fi

if [ "$RUN_SIM_POST_SELL_FEEDBACK" = "true" ] || [ "$RUN_SIM_POST_SELL_FEEDBACK" = "1" ]; then
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.sniper_post_sell_feedback \
    --date "$TARGET_DATE" \
    --backfill-sim-candidates \
    --evaluate-sim \
    --materialize-monitor-snapshot
fi
if [ "$RUN_LIMIT_DOWN_WATCH_REPORT" = "true" ] || [ "$RUN_LIMIT_DOWN_WATCH_REPORT" = "1" ]; then
  wait_for_postclose_resources "limit_down_watch_report"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.limit_down_watch_report \
    --target-date "$TARGET_DATE" \
    --write
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/limit_down_watch/limit_down_watch_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/limit_down_watch/limit_down_watch_${TARGET_DATE}.md" \
    "limit_down_watch_report"
fi
if [ "$RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE" = "true" ] || [ "$RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE" = "1" ]; then
  wait_for_postclose_resources "rising_missed_intraday_feedback_postclose"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.rising_missed_intraday_feedback \
    --target-date "$TARGET_DATE" \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_${TARGET_DATE}.md" \
    "rising_missed_intraday_feedback_postclose"
fi
if [ "$RUN_RISING_MISSED_SCOUT_WORKORDER" = "true" ] || [ "$RUN_RISING_MISSED_SCOUT_WORKORDER" = "1" ]; then
  wait_for_postclose_resources "rising_missed_scout_workorder"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.rising_missed_scout_workorder --target-date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_${TARGET_DATE}.md" \
    "rising_missed_scout_workorder"
fi
if [ "$RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE" = "true" ] || [ "$RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE" = "1" ]; then
  wait_for_postclose_resources "scalping_pyramid_intraday_feedback_postclose"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.scalping_pyramid_intraday_feedback \
    --target-date "$TARGET_DATE" \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_${TARGET_DATE}.md" \
    "scalping_pyramid_intraday_feedback_postclose"
fi
if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "true" ] || [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "1" ]; then
  wait_for_postclose_resources "observation_source_quality_preflight"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.observation_source_quality_audit --target-date "$TARGET_DATE" --write
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
    "observation_source_quality_preflight"
fi
if [ "$RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION" = "true" ] || [ "$RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION" = "1" ]; then
  wait_for_postclose_resources "scalping_pyramid_quality_calibration"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.scalping_pyramid_quality_calibration \
    --target-date "$TARGET_DATE" \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_${TARGET_DATE}.md" \
    "scalping_pyramid_quality_calibration"
fi
if [ "$RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION" = "true" ] || [ "$RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION" = "1" ]; then
  avg_down_report_json="$PROJECT_DIR/data/report/scalping_avg_down_recovery_calibration/scalping_avg_down_recovery_calibration_${TARGET_DATE}.json"
  avg_down_report_md="$PROJECT_DIR/data/report/scalping_avg_down_recovery_calibration/scalping_avg_down_recovery_calibration_${TARGET_DATE}.md"
  if reusable_completed_artifact \
    "$avg_down_report_json" \
    "$avg_down_report_md" \
    "scalping_avg_down_recovery_calibration" \
    "$PROJECT_DIR/data/pipeline_events" \
    "$PROJECT_DIR/src/engine/automation/source_quality_hard_gate.py" \
    "$PROJECT_DIR/src/engine/monitoring/scalping_avg_down_recovery_calibration.py"; then
    emit_postclose_marker "[REUSE] scalping_avg_down_recovery_calibration target_date=$TARGET_DATE reason=completed_artifact_checkpoint"
  else
    wait_for_postclose_resources "scalping_avg_down_recovery_calibration"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.scalping_avg_down_recovery_calibration \
      --target-date "$TARGET_DATE" \
      --print-summary
  fi
  wait_for_report_artifact \
    "$avg_down_report_json" \
    "$avg_down_report_md" \
    "scalping_avg_down_recovery_calibration"
fi
if [ "$RUN_SAMSUNG_MACHINE_ENTRY_TUNING" = "true" ] || [ "$RUN_SAMSUNG_MACHINE_ENTRY_TUNING" = "1" ]; then
  wait_for_postclose_resources "samsung_machine_entry_tuning"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.samsung_machine_entry_tuning \
    --target-date "$TARGET_DATE" \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/samsung_machine_entry_tuning/samsung_machine_entry_tuning_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/samsung_machine_entry_tuning/samsung_machine_entry_tuning_${TARGET_DATE}.md" \
    "samsung_machine_entry_tuning"
  wait_for_file_artifact \
    "$PROJECT_DIR/data/threshold_cycle/samsung_machine_entry_policy/candidates/samsung_machine_entry_policy_candidate_${TARGET_DATE}.json" \
    "samsung_machine_entry_policy_candidate"
fi
if [ "$RUN_LOW_PRICE_TWO_LEG_TUNING" = "true" ] || [ "$RUN_LOW_PRICE_TWO_LEG_TUNING" = "1" ]; then
  wait_for_postclose_resources "low_price_two_leg_tuning"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.low_price_two_leg_tuning \
    --target-date "$TARGET_DATE" \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_${TARGET_DATE}.md" \
    "low_price_two_leg_tuning"
  wait_for_file_artifact \
    "$PROJECT_DIR/data/threshold_cycle/low_price_two_leg/candidates/low_price_two_leg_policy_candidate_${TARGET_DATE}.json" \
    "low_price_two_leg_policy_candidate"
fi
if [ "$RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION" = "true" ] || [ "$RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION" = "1" ]; then
  candidate_recommendation_json="$PROJECT_DIR/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_${TARGET_DATE}.json"
  candidate_recommendation_md="$PROJECT_DIR/data/report/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_${TARGET_DATE}.md"
  if reusable_completed_artifact \
    "$candidate_recommendation_json" \
    "$candidate_recommendation_md" \
    "low_price_two_leg_expanded_candidate_research" \
    "$PROJECT_DIR/src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py" \
    && low_price_candidate_recommendation_reusable "$candidate_recommendation_json"
  then
    echo "[threshold-cycle] reuse completed low-price machine candidate recommendation date=$TARGET_DATE"
  else
    wait_for_postclose_resources "low_price_two_leg_candidate_recommendation"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
      -m src.engine.monitoring.low_price_two_leg_expanded_candidate_research \
      --target-date "$TARGET_DATE" \
      --write \
      --notify \
      --print-summary
  fi
  wait_for_report_artifact \
    "$candidate_recommendation_json" \
    "$candidate_recommendation_md" \
    "low_price_two_leg_candidate_recommendation"
fi
if [ "$RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION" = "true" ] || [ "$RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION" = "1" ]; then
  wait_for_postclose_resources "machine_microstructure_attribution"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
    -m src.engine.monitoring.machine_microstructure_attribution \
    --target-date "$TARGET_DATE" \
    --write \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/machine_microstructure_attribution/machine_microstructure_attribution_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/machine_microstructure_attribution/machine_microstructure_attribution_${TARGET_DATE}.md" \
    "machine_microstructure_attribution"
  wait_for_postclose_resources "market_weakness_hysteresis_tuning"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
    -m src.engine.automation.market_weakness_hysteresis_tuning \
    --target-date "$TARGET_DATE" \
    --write \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/market_weakness_hysteresis_tuning/market_weakness_hysteresis_tuning_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/market_weakness_hysteresis_tuning/market_weakness_hysteresis_tuning_${TARGET_DATE}.md" \
    "market_weakness_hysteresis_tuning"
  wait_for_postclose_resources "machine_entry_timing_tuning"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
    -m src.engine.automation.machine_entry_timing_tuning \
    --target-date "$TARGET_DATE" \
    --write \
    --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/machine_entry_timing_tuning/machine_entry_timing_tuning_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/machine_entry_timing_tuning/machine_entry_timing_tuning_${TARGET_DATE}.md" \
    "machine_entry_timing_tuning"
fi
if [ "$RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL" = "true" ] || [ "$RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL" = "1" ]; then
  wait_for_postclose_resources "machine_microstructure_policy_approval"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
    -m src.engine.automation.machine_microstructure_policy_approval \
    --phase postclose \
    --target-date "$TARGET_DATE" \
    --write \
    --notify
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/machine_microstructure_policy_approval/machine_microstructure_policy_approval_postclose_${TARGET_DATE}.md" \
    "machine_microstructure_policy_approval"
fi
if [ "$RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY" = "true" ] || [ "$RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY" = "1" ]; then
  one_share_report_json="$PROJECT_DIR/data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_${TARGET_DATE}.json"
  one_share_report_md="$PROJECT_DIR/data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_${TARGET_DATE}.md"
  if reusable_completed_artifact \
    "$one_share_report_json" \
    "$one_share_report_md" \
    "one_share_threshold_opportunity" \
    "$PROJECT_DIR/data/pipeline_events" \
    "$PROJECT_DIR/data/post_sell" \
    "$PROJECT_DIR/src/engine/monitoring/one_share_threshold_opportunity.py" && \
    one_share_ai_review_reusable "$one_share_report_json"; then
    emit_postclose_marker "[REUSE] one_share_threshold_opportunity target_date=$TARGET_DATE reason=completed_artifact_checkpoint"
  else
    wait_for_postclose_resources "one_share_threshold_opportunity"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.one_share_threshold_opportunity \
      --target-date "$TARGET_DATE" \
      --ai-provider "$ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER"
  fi
  wait_for_report_artifact \
    "$one_share_report_json" \
    "$one_share_report_md" \
    "one_share_threshold_opportunity"
fi
if [ "$RUN_SCALP_ENTRY_ADM" = "true" ] || [ "$RUN_SCALP_ENTRY_ADM" = "1" ]; then
  wait_for_postclose_resources "scalp_entry_action_decision_matrix"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalp_entry_action_decision_matrix --date "$TARGET_DATE" --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.md" \
    "scalp_entry_action_decision_matrix"
fi
if [ "$RUN_ENTRY_AI_GATE_BACKTEST" = "true" ] || [ "$RUN_ENTRY_AI_GATE_BACKTEST" = "1" ]; then
  wait_for_postclose_resources "entry_ai_gate_backtest"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.entry_ai_gate_backtest \
    --target-date "$TARGET_DATE" \
    --start-date "${KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE:-2026-06-05}" \
    --end-date "$TARGET_DATE" \
    --write
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_${TARGET_DATE}.md" \
    "entry_ai_gate_backtest"
fi
if [ "$RUN_SCALP_SIM_OVERNIGHT_REPORT" = "true" ] || [ "$RUN_SCALP_SIM_OVERNIGHT_REPORT" = "1" ]; then
  wait_for_postclose_resources "scalp_sim_overnight"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalp_sim_overnight --date "$TARGET_DATE" --report-only
  scalp_sim_overnight_report="$PROJECT_DIR/data/report/scalp_sim_overnight/scalp_sim_overnight_${TARGET_DATE}.json"
  scalp_sim_overnight_active_undecided="$(
    "$VENV_PY" - "$scalp_sim_overnight_report" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    print(int((summary or {}).get("active_undecided_count") or 0))
except Exception:
    print(-1)
PY
  )"
  if [ "$scalp_sim_overnight_active_undecided" -lt 0 ]; then
    echo "[FAIL] scalp_sim_overnight late-position preflight invalid report=$scalp_sim_overnight_report"
    exit 1
  fi
  if [ "$scalp_sim_overnight_active_undecided" -gt 0 ]; then
    echo "[threshold-cycle] scalp_sim_overnight late-position recovery active_undecided=$scalp_sim_overnight_active_undecided provider=openai runtime_effect=false"
    run_postclose_cmd env \
      PYTHONPATH=. \
      KORSTOCKSCAN_OPENAI_TRANSPORT_MODE="${KORSTOCKSCAN_OPENAI_TRANSPORT_MODE:-responses_ws}" \
      KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED="${KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED:-true}" \
      KORSTOCKSCAN_OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED="${KORSTOCKSCAN_OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED:-false}" \
      KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=off \
      "$VENV_PY" -m src.engine.scalp_sim_overnight --date "$TARGET_DATE" --live-openai
  fi
  wait_for_report_artifact \
    "$scalp_sim_overnight_report" \
    "$PROJECT_DIR/data/report/scalp_sim_overnight/scalp_sim_overnight_${TARGET_DATE}.md" \
    "scalp_sim_overnight"
fi
if [ "$RUN_INSTITUTIONAL_FLOW_CONTEXT" = "true" ] || [ "$RUN_INSTITUTIONAL_FLOW_CONTEXT" = "1" ]; then
  wait_for_postclose_resources "institutional_flow_context"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.institutional_flow_context --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/institutional_flow_context/institutional_flow_context_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/institutional_flow_context/institutional_flow_context_${TARGET_DATE}.md" \
    "institutional_flow_context"
fi
if [ "$RUN_MICROSTRUCTURE_REACTION_CONTEXT" = "true" ] || [ "$RUN_MICROSTRUCTURE_REACTION_CONTEXT" = "1" ]; then
  wait_for_postclose_resources "microstructure_reaction_context"
  if run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.microstructure_reaction_context --date "$TARGET_DATE"; then
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/microstructure_reaction_context/microstructure_reaction_context_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/microstructure_reaction_context/microstructure_reaction_context_${TARGET_DATE}.md" \
      "microstructure_reaction_context" || echo "[WARN] optional microstructure_reaction_context artifact wait failed target_date=$TARGET_DATE"
  else
    echo "[WARN] optional microstructure_reaction_context failed target_date=$TARGET_DATE"
  fi
fi
if [ "$RUN_LIFECYCLE_DECISION_MATRIX" = "true" ] || [ "$RUN_LIFECYCLE_DECISION_MATRIX" = "1" ]; then
  wait_for_postclose_resources "scale_in_incremental_counterfactual"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle.scale_in_incremental_counterfactual --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scale_in_incremental_counterfactual/scale_in_incremental_counterfactual_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/scale_in_incremental_counterfactual/scale_in_incremental_counterfactual_${TARGET_DATE}.md" \
    "scale_in_incremental_counterfactual"
  wait_for_postclose_resources "lifecycle_decision_matrix"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.md" \
    "lifecycle_decision_matrix"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalp_sim_scale_in_window_approval --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_${TARGET_DATE}.json" \
    "scalp_sim_scale_in_window_approval"
  if [ "$RUN_LIFECYCLE_AI_CONTEXT" = "true" ] || [ "$RUN_LIFECYCLE_AI_CONTEXT" = "1" ]; then
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode attribution
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_${TARGET_DATE}.md" \
      "lifecycle_ai_context_attribution"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.md" \
      "lifecycle_decision_matrix_feedback_refresh"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode context
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/lifecycle_ai_context/lifecycle_ai_context_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/lifecycle_ai_context/lifecycle_ai_context_${TARGET_DATE}.md" \
      "lifecycle_ai_context"
  fi
fi
if [ "$RUN_LDM_HYPOTHESIS_PARENT_REFINEMENT" = "true" ] || [ "$RUN_LDM_HYPOTHESIS_PARENT_REFINEMENT" = "1" ]; then
  wait_for_postclose_resources "ldm_hypothesis_parent_refinement"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.ldm_hypothesis_parent_refinement --date "$TARGET_DATE" --write
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/ldm_hypothesis_parent_refinement/ldm_hypothesis_parent_refinement_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/ldm_hypothesis_parent_refinement/ldm_hypothesis_parent_refinement_${TARGET_DATE}.md" \
    "ldm_hypothesis_parent_refinement"
fi
if [ "$RUN_LIFECYCLE_BUCKET_DISCOVERY" = "true" ] || [ "$RUN_LIFECYCLE_BUCKET_DISCOVERY" = "1" ]; then
  wait_for_postclose_resources "lifecycle_bucket_discovery"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_bucket_discovery --date "$TARGET_DATE" --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.md" \
    "lifecycle_bucket_discovery"
  if [ "$RUN_LIFECYCLE_BUCKET_WINDOWS" = "true" ] || [ "$RUN_LIFECYCLE_BUCKET_WINDOWS" = "1" ]; then
    IFS=',' read -r -a lifecycle_bucket_window_items <<< "$LIFECYCLE_BUCKET_WINDOWS"
    for lifecycle_bucket_window in "${lifecycle_bucket_window_items[@]}"; do
      lifecycle_bucket_window="$(printf '%s' "$lifecycle_bucket_window" | tr -d '[:space:]')"
      [ -n "$lifecycle_bucket_window" ] || continue
      automation_trigger_decision "lifecycle_window_${lifecycle_bucket_window}"
      if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
        skip_triggered_step "lifecycle_bucket_windows_${lifecycle_bucket_window}" "fresh_outputs_no_trigger"
        continue
      fi
      lifecycle_bucket_start_date="$("$VENV_PY" - "$TARGET_DATE" "$lifecycle_bucket_window" <<'PY'
import sys
from datetime import date, timedelta

target = date.fromisoformat(sys.argv[1])
window = sys.argv[2]
if window == "rolling5d":
    start = target - timedelta(days=4)
elif window == "rolling10d":
    start = target - timedelta(days=9)
elif window == "mtd":
    start = target.replace(day=1)
else:
    raise SystemExit(f"unsupported_lifecycle_bucket_window:{window}")
print(start.isoformat())
PY
)"
      wait_for_postclose_resources "lifecycle_decision_matrix_${lifecycle_bucket_window}"
      if ! run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_decision_matrix \
        --target-date "$TARGET_DATE" \
        --start-date "$lifecycle_bucket_start_date" \
        --end-date "$TARGET_DATE" \
        --window-policy "$lifecycle_bucket_window" \
        --output-suffix "$lifecycle_bucket_window"; then
        echo "[threshold-cycle] lifecycle_decision_matrix_${lifecycle_bucket_window} failed; verifier will fail-closed if required" >&2
        continue
      fi
      if ! wait_for_report_artifact \
        "$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}_${lifecycle_bucket_window}.json" \
        "$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}_${lifecycle_bucket_window}.md" \
        "lifecycle_decision_matrix_${lifecycle_bucket_window}"; then
        echo "[threshold-cycle] lifecycle_decision_matrix_${lifecycle_bucket_window} artifact missing; verifier will fail-closed if required" >&2
        continue
      fi
      wait_for_postclose_resources "lifecycle_bucket_discovery_${lifecycle_bucket_window}"
      if ! run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_bucket_discovery \
        --target-date "$TARGET_DATE" \
        --source-suffix "$lifecycle_bucket_window" \
        --output-suffix "$lifecycle_bucket_window" \
        --print-summary; then
        echo "[threshold-cycle] lifecycle_bucket_discovery_${lifecycle_bucket_window} failed; verifier will fail-closed if required" >&2
        continue
      fi
      if ! wait_for_report_artifact \
        "$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}_${lifecycle_bucket_window}.json" \
        "$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}_${lifecycle_bucket_window}.md" \
        "lifecycle_bucket_discovery_${lifecycle_bucket_window}"; then
        echo "[threshold-cycle] lifecycle_bucket_discovery_${lifecycle_bucket_window} artifact missing; verifier will fail-closed if required" >&2
        continue
      fi
    done
  fi
fi
if [ "$RUN_RUNTIME_APPLY_BRIDGE" = "true" ] || [ "$RUN_RUNTIME_APPLY_BRIDGE" = "1" ]; then
  wait_for_postclose_resources "runtime_apply_bridge"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_apply_bridge --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/runtime_apply_bridge/runtime_apply_bridge_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/runtime_apply_bridge/runtime_apply_bridge_${TARGET_DATE}.md" \
    "runtime_apply_bridge"
fi
if [ "$RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER" = "true" ] || [ "$RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER" = "1" ]; then
  wait_for_postclose_resources "scalp_sim_auto_approval_control_tower"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.scalp_sim_auto_approval_control_tower --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_${TARGET_DATE}.json" \
    "scalp_sim_auto_approval_control_tower"
fi
if [ "$RUN_LATENCY_CLASSIFIER_RECOMMENDATION" = "true" ] || [ "$RUN_LATENCY_CLASSIFIER_RECOMMENDATION" = "1" ]; then
  wait_for_postclose_resources "latency_classifier_recommendation"
  latency_args=(--date "$TARGET_DATE")
  if [ "${#SOURCE_ARGS[@]}" -gt 0 ]; then
    latency_args+=("${SOURCE_ARGS[@]}")
  fi
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.latency_classifier_recommendation "${latency_args[@]}" --print-summary
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/latency_classifier_recommendation/latency_classifier_recommendation_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/latency_classifier_recommendation/latency_classifier_recommendation_${TARGET_DATE}.md" \
    "latency_classifier_recommendation"
fi

if { [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "true" ] || [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "1" ]; } && { [ "$RUN_MARKET_PANIC_BREADTH_REPORT" = "true" ] || [ "$RUN_MARKET_PANIC_BREADTH_REPORT" = "1" ]; }; then
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.market_panic_breadth_collector \
    --date "$TARGET_DATE"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/market_panic_breadth/market_panic_breadth_${TARGET_DATE}.json" \
    "market_panic_breadth_postclose"
fi
if [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "true" ] || [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "1" ]; then
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.panic_sell_defense_report \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/panic_sell_defense/panic_sell_defense_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/panic_sell_defense/panic_sell_defense_${TARGET_DATE}.md" \
    "panic_sell_defense_postclose"
fi
if [ "$RUN_ENTRY_SPLIT_ORDER_PLAN" = "true" ] || [ "$RUN_ENTRY_SPLIT_ORDER_PLAN" = "1" ]; then
  wait_for_postclose_resources "entry_split_order_plan"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.entry_split_order_plan \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/entry_split_order_plan/entry_split_order_plan_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/entry_split_order_plan/entry_split_order_plan_${TARGET_DATE}.md" \
    "entry_split_order_plan"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_${TARGET_DATE}.json" \
    "entry_split_order_policy"
fi

if [ "$RUN_SCALE_IN_SPLIT_ORDER_PLAN" = "true" ] || [ "$RUN_SCALE_IN_SPLIT_ORDER_PLAN" = "1" ]; then
  wait_for_postclose_resources "scale_in_split_order_plan"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.scale_in_split_order_plan \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scale_in_split_order_plan/scale_in_split_order_plan_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/scale_in_split_order_plan/scale_in_split_order_plan_${TARGET_DATE}.md" \
    "scale_in_split_order_plan"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_${TARGET_DATE}.json" \
    "scale_in_split_order_policy"
fi

report_args=(--date "$TARGET_DATE")
if [ "$SKIP_DB" = "true" ]; then
  report_args+=(--skip-db)
fi
if [ -n "$AI_CORRECTION_RESPONSE_JSON" ]; then
  report_args+=(--ai-correction-response-json "$AI_CORRECTION_RESPONSE_JSON")
else
  report_args+=(--ai-correction-provider "$AI_CORRECTION_PROVIDER")
  if [[ "$AI_CORRECTION_REUSE_IF_VALID" == "1" || "$AI_CORRECTION_REUSE_IF_VALID" == "true" ]]; then
    report_args+=(--reuse-ai-review-if-valid)
  fi
fi

# Refresh exact execution-derived facts after the NXT session before the
# calibration reads completed trades.  The recovery controller uses the same
# explicit ordering rather than hiding this database write in a report build.
if [ "$SKIP_DB" != "true" ]; then
  wait_for_postclose_resources "strategy_position_performance_sync"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.strategy_position_performance_report \
    --date "$TARGET_DATE"
else
  echo "[threshold-cycle] skip exact trade fact sync target_date=$TARGET_DATE reason=skip_db"
fi

ai_review_json="$PROJECT_DIR/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_${TARGET_DATE}_postclose.json"
ai_review_md="$PROJECT_DIR/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_${TARGET_DATE}_postclose.md"
ai_correction_attempt=1
ai_correction_status="missing"
while true; do
  wait_for_postclose_resources "daily_threshold_cycle_report"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report \
    --calibration-run-phase postclose \
    "${report_args[@]}"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/threshold_cycle_${TARGET_DATE}.json" \
    "threshold_cycle_postclose_report"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/threshold_cycle_calibration/threshold_cycle_calibration_${TARGET_DATE}_postclose.json" \
    "threshold_cycle_calibration_postclose"
  wait_for_report_artifact \
    "$ai_review_json" \
    "$ai_review_md" \
    "threshold_cycle_ai_review_postclose"
  ai_correction_status="$(threshold_cycle_ai_review_status "$ai_review_json")"
  echo "[threshold-cycle] ai correction status target_date=$TARGET_DATE attempt=${ai_correction_attempt}/${AI_CORRECTION_MAX_ATTEMPTS} provider=$AI_CORRECTION_PROVIDER status=$ai_correction_status"
  if [ "$AI_CORRECTION_PROVIDER" = "none" ] || [ -n "$AI_CORRECTION_RESPONSE_JSON" ] || [ "$ai_correction_status" = "parsed" ] || [ "$ai_correction_attempt" -ge "$AI_CORRECTION_MAX_ATTEMPTS" ]; then
    break
  fi
  echo "[threshold-cycle] ai correction retry target_date=$TARGET_DATE next_attempt=$((ai_correction_attempt + 1)) delay=${AI_CORRECTION_RETRY_DELAY_SEC}s status=$ai_correction_status" >&2
	  run_postclose_cmd sleep "$AI_CORRECTION_RETRY_DELAY_SEC"
	  ai_correction_attempt=$((ai_correction_attempt + 1))
	done
	AI_CORRECTION_FINAL_STATUS="$ai_correction_status"
	if [ "$AI_CORRECTION_PROVIDER" != "none" ] && [ -z "$AI_CORRECTION_RESPONSE_JSON" ] && [ "$ai_correction_status" != "parsed" ]; then
	  echo "[threshold-cycle] ai correction final unavailable target_date=$TARGET_DATE provider=$AI_CORRECTION_PROVIDER status=$ai_correction_status action=postclose_verifier_will_fail_if_runtime_candidates_blocked" >&2
	fi
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.entry_cancel_wait_tuning \
  --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_${TARGET_DATE}.md" \
  "entry_cancel_wait_tuning"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/statistical_action_weight/statistical_action_weight_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/statistical_action_weight/statistical_action_weight_${TARGET_DATE}.md" \
  "statistical_action_weight"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_${TARGET_DATE}.md" \
  "holding_exit_decision_matrix"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_${TARGET_DATE}.md" \
  "threshold_cycle_cumulative"
if [ "$RUN_SWING_LIFECYCLE_AUDIT" = "true" ] || [ "$RUN_SWING_LIFECYCLE_AUDIT" = "1" ]; then
  wait_for_postclose_resources "swing_daily_simulation"
  run_postclose_cmd bash "$PROJECT_DIR/deploy/run_swing_daily_simulation_report.sh" "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.md" \
    "swing_daily_simulation"
  if [ "$RUN_SWING_STRATEGY_DISCOVERY" = "true" ] || [ "$RUN_SWING_STRATEGY_DISCOVERY" = "1" ]; then
    wait_for_postclose_resources "swing_strategy_discovery_sim"
    BOTTOM_REBOUND_SOURCE_JSON="$PROJECT_DIR/data/report/swing_bottom_rebound_candidate_source/swing_bottom_rebound_candidate_source_${TARGET_DATE}.json"
    if bottom_rebound_source_contract_ok "$BOTTOM_REBOUND_SOURCE_JSON"; then
      echo "[threshold-cycle] bottom_rebound_source_contract=pass path=$BOTTOM_REBOUND_SOURCE_JSON"
      run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_sim \
        --date "$TARGET_DATE" \
        --include-bottom-rebound-source
    else
      echo "[threshold-cycle] bottom_rebound_source_contract=missing_or_invalid path=$BOTTOM_REBOUND_SOURCE_JSON safe_pool_only=true"
      run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_sim --date "$TARGET_DATE"
    fi
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_${TARGET_DATE}.md" \
      "swing_strategy_discovery_sim"
    wait_for_postclose_resources "swing_strategy_discovery_labels"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_label_builder \
      --date "$TARGET_DATE" \
      --refresh-matured
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_${TARGET_DATE}.md" \
      "swing_strategy_discovery_labels"
    wait_for_postclose_resources "swing_strategy_discovery_ev"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_strategy_discovery_ev_report --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_${TARGET_DATE}.md" \
      "swing_strategy_discovery_ev"
  fi
  if [ "$RUN_SWING_LIFECYCLE_MATRIX" = "true" ] || [ "$RUN_SWING_LIFECYCLE_MATRIX" = "1" ]; then
    wait_for_postclose_resources "swing_lifecycle_decision_matrix"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_decision_matrix --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_${TARGET_DATE}.md" \
      "swing_lifecycle_decision_matrix"
  fi
  if [ "$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY" = "true" ] || [ "$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY" = "1" ]; then
    wait_for_postclose_resources "swing_lifecycle_bucket_discovery"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_bucket_discovery \
      --date "$TARGET_DATE" \
      --ai-provider "$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_${TARGET_DATE}.md" \
      "swing_lifecycle_bucket_discovery"
  fi
  wait_for_postclose_resources "swing_lifecycle_audit"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit \
    --date "$TARGET_DATE" \
    --ai-review-provider "$SWING_THRESHOLD_AI_REVIEW_PROVIDER"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_lifecycle_audit/swing_lifecycle_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_lifecycle_audit/swing_lifecycle_audit_${TARGET_DATE}.md" \
    "swing_lifecycle_audit"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_threshold_ai_review/swing_threshold_ai_review_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_threshold_ai_review/swing_threshold_ai_review_${TARGET_DATE}.md" \
    "swing_threshold_ai_review"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_improvement_automation/swing_improvement_automation_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_improvement_automation/swing_improvement_automation_${TARGET_DATE}.md" \
    "swing_improvement_automation"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_runtime_approval/swing_runtime_approval_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_runtime_approval/swing_runtime_approval_${TARGET_DATE}.md" \
    "swing_runtime_approval"
fi
if [ "$RUN_DEEPSEEK_SWING_LAB" = "true" ] || [ "$RUN_DEEPSEEK_SWING_LAB" = "1" ]; then
  echo "[threshold-cycle] running deepseek swing pattern lab target_date=$TARGET_DATE"
  wait_for_postclose_resources "deepseek_swing_pattern_lab"
  ANALYSIS_START_DATE="$TARGET_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    run_postclose_cmd bash "$PROJECT_DIR/analysis/deepseek_swing_pattern_lab/run_all.sh" "$TARGET_DATE" || \
    echo "[threshold-cycle] deepseek swing pattern lab failed (non-fatal)" >&2
fi
if [ "$RUN_PATTERN_LABS" = "true" ] || [ "$RUN_PATTERN_LABS" = "1" ]; then
  wait_for_postclose_resources "claude_scalping_pattern_lab"
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    run_postclose_cmd "$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh" || \
    echo "[threshold-cycle] claude scalping pattern lab failed (non-fatal); downstream automation will mark freshness=false" >&2
  echo "[threshold-cycle] gemini scalping pattern lab skipped: retired_from_automatic_execution" >&2
fi
wait_for_postclose_resources "scalping_pattern_lab_automation"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping_pattern_lab_automation --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_${TARGET_DATE}.md" \
  "scalping_pattern_lab_automation"
if [ "$RUN_SWING_PATTERN_LAB_AUTOMATION" = "true" ] || [ "$RUN_SWING_PATTERN_LAB_AUTOMATION" = "1" ]; then
  wait_for_postclose_resources "swing_pattern_lab_automation"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_pattern_lab_automation --date "$TARGET_DATE" || \
    echo "[threshold-cycle] swing pattern lab automation failed (non-fatal)" >&2
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_${TARGET_DATE}.md" \
    "swing_pattern_lab_automation"
else
  echo "[threshold-cycle] swing pattern lab automation skipped by swing postclose operator policy"
fi
if [ "$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" = "true" ] || [ "$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" = "1" ]; then
  automation_trigger_decision "pattern_lab_currentness_audit"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
    skip_triggered_step "pattern_lab_currentness_audit" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.md" \
      "pattern_lab_currentness_audit"
  else
    wait_for_postclose_resources "pattern_lab_currentness_audit"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_currentness_audit \
      --date "$TARGET_DATE" "${PATTERN_LAB_SWING_ARGS[@]}"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.md" \
      "pattern_lab_currentness_audit"
  fi
fi
if [ "$RUN_PATTERN_LAB_AI_REVIEW" = "true" ] || [ "$RUN_PATTERN_LAB_AI_REVIEW" = "1" ]; then
  automation_trigger_decision "pattern_lab_ai_review"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
    skip_triggered_step "pattern_lab_ai_review" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.md" \
      "pattern_lab_ai_review"
  else
    wait_for_postclose_resources "pattern_lab_ai_review"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_ai_review \
      --date "$TARGET_DATE" \
      --provider "$PATTERN_LAB_AI_REVIEW_PROVIDER" \
      "${PATTERN_LAB_SWING_ARGS[@]}"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.md" \
      "pattern_lab_ai_review"
  fi
fi
if [ "$RUN_PIPELINE_EVENT_VERBOSITY_REPORT" = "true" ] || [ "$RUN_PIPELINE_EVENT_VERBOSITY_REPORT" = "1" ]; then
  pipeline_verbosity_json="$PROJECT_DIR/data/report/pipeline_event_verbosity/pipeline_event_verbosity_${TARGET_DATE}.json"
  pipeline_verbosity_md="$PROJECT_DIR/data/report/pipeline_event_verbosity/pipeline_event_verbosity_${TARGET_DATE}.md"
  pipeline_verbosity_inputs=(
    "$RAW_SOURCE"
    "$PROJECT_DIR/src/engine/pipeline_event_verbosity_report.py"
    "$PROJECT_DIR/src/engine/pipeline_event_summary.py"
  )
  pipeline_producer_summary="$PROJECT_DIR/data/pipeline_event_summaries/pipeline_event_producer_summary_${TARGET_DATE}.jsonl"
  pipeline_producer_summary_gz="${pipeline_producer_summary}.gz"
  pipeline_producer_manifest="$PROJECT_DIR/data/pipeline_event_summaries/pipeline_event_producer_summary_manifest_${TARGET_DATE}.json"
  if [ -s "$pipeline_producer_summary" ]; then
    pipeline_verbosity_inputs+=("$pipeline_producer_summary")
  elif [ -s "$pipeline_producer_summary_gz" ]; then
    pipeline_verbosity_inputs+=("$pipeline_producer_summary_gz")
  fi
  if [ -s "$pipeline_producer_manifest" ]; then
    pipeline_verbosity_inputs+=("$pipeline_producer_manifest")
  fi
  pipeline_verbosity_refresh_decision="run"
  if [ -s "$pipeline_verbosity_md" ] && json_is_valid "$pipeline_verbosity_json"; then
    pipeline_verbosity_refresh_decision="$(threshold_cycle_ev_refresh_decision \
      "$pipeline_verbosity_json" \
      "$pipeline_verbosity_md" \
      "$FORCE_DUPLICATE_REFRESH" \
      "${pipeline_verbosity_inputs[@]}")"
  fi
  if [ "$pipeline_verbosity_refresh_decision" = "skip" ]; then
    skip_triggered_step "pipeline_event_verbosity" "verified_artifacts_fresher_than_inputs"
  else
    wait_for_postclose_resources "pipeline_event_verbosity"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pipeline_event_verbosity_report --date "$TARGET_DATE"
  fi
  wait_for_report_artifact \
    "$pipeline_verbosity_json" \
    "$pipeline_verbosity_md" \
    "pipeline_event_verbosity"
fi
if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "true" ] || [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "1" ]; then
  automation_trigger_decision "observation_source_quality_audit"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
    skip_triggered_step "observation_source_quality_audit" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
      "observation_source_quality_audit"
  else
    wait_for_postclose_resources "observation_source_quality_audit"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.observation_source_quality_audit --target-date "$TARGET_DATE" --write --print-summary
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
      "observation_source_quality_audit"
  fi
fi
if [ "$RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION" = "true" ] || [ "$RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION" = "1" ]; then
  wait_for_postclose_resources "ai_decision_quality_daily_materialization"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.ai_decision_quality \
    --date "$TARGET_DATE" \
    --mode postclose \
    --write
  wait_for_json_artifact \
    "$PROJECT_DIR/data/runtime/ai_decision_quality_control_${TARGET_DATE}.json" \
    "ai_decision_quality_control"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/ai_decision_outcome_labels/ai_decision_outcome_labels_${TARGET_DATE}.json" \
    "ai_decision_outcome_labels"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/ai_decision_quality_baseline/ai_decision_quality_baseline_${TARGET_DATE}.json" \
    "ai_decision_quality_baseline"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/ai_prompt_paired_replay/ai_prompt_paired_replay_${TARGET_DATE}.json" \
    "ai_prompt_paired_replay_preparation"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/entry_candidate_lifecycle_state/entry_candidate_lifecycle_state_${TARGET_DATE}.json" \
    "entry_candidate_lifecycle_state"
fi
if [ "$RUN_MAIN_AI_QUALITY_R0_R3" = "true" ] || [ "$RUN_MAIN_AI_QUALITY_R0_R3" = "1" ]; then
  main_ai_quality_args=(
    --date "$TARGET_DATE"
    --write
    --daily-attempt-cap "$MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP"
    --daily-usd-cap "$MAIN_AI_QUALITY_DAILY_USD_CAP"
    --parent-cap "$MAIN_AI_QUALITY_PARENT_CAP"
  )
  if [ "$MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY" = "true" ] || [ "$MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY" = "1" ]; then
    main_ai_quality_args+=(--execute-provider-replay)
  fi
  main_ai_quality_rc=0
  main_ai_quality_failure_reason=""
  wait_for_postclose_resources "main_ai_quality_r0_r3" || {
    main_ai_quality_rc=$?
    main_ai_quality_failure_reason="resource_wait_failed"
  }
  if [ "$main_ai_quality_rc" -eq 0 ]; then
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
      -m src.engine.scalping.micro_reversion.ai_quality_cycle \
      "${main_ai_quality_args[@]}" || {
        main_ai_quality_rc=$?
        main_ai_quality_failure_reason="cycle_command_failed_or_deferred"
      }
  fi
  if [ "$main_ai_quality_rc" -eq 0 ]; then
    if ! wait_for_json_artifact \
      "$PROJECT_DIR/data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_${TARGET_DATE}.json" \
      "main_ai_quality_r0_r3"; then
      main_ai_quality_rc=1
      main_ai_quality_failure_reason="artifact_missing_or_invalid"
    fi
  fi
  if [ "$main_ai_quality_rc" -ne 0 ]; then
    emit_postclose_marker "[WARN] main-ai-quality-r0-r3 target_date=$TARGET_DATE rc=$main_ai_quality_rc reason=$main_ai_quality_failure_reason runtime_effect=false actual_order_submitted=false"
  fi
fi
if [ "$RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY" = "true" ] || [ "$RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY" = "1" ]; then
  main_ai_quality_family_rc=0
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" \
    -m src.engine.automation.main_ai_quality_runtime_family \
    --phase postclose \
    --target-date "$TARGET_DATE" \
    --write || main_ai_quality_family_rc=$?
  if [ "$main_ai_quality_family_rc" -ne 0 ]; then
    emit_postclose_marker "[WARN] main-ai-quality-runtime-family target_date=$TARGET_DATE rc=$main_ai_quality_family_rc status=blocked_fail_closed runtime_effect=false actual_order_submitted=false"
  fi
fi
if [ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION" = "true" ] || [ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION" = "1" ]; then
  wait_for_postclose_resources "ai_decision_action_outcome_calibration"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.ai_action_outcome_calibration \
    --target-date "$TARGET_DATE" \
    --write \
    --print-summary
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_${TARGET_DATE}.json" \
    "ai_decision_action_outcome_calibration"
fi
if [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" = "true" ] || [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" = "1" ]; then
  automation_trigger_decision "codebase_performance_workorder"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
    skip_triggered_step "codebase_performance_workorder" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/codebase_performance_workorder/codebase_performance_workorder_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/codebase_performance_workorder/codebase_performance_workorder_${TARGET_DATE}.md" \
      "codebase_performance_workorder"
  else
    wait_for_postclose_resources "codebase_performance_workorder"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.codebase_performance_workorder_report --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/codebase_performance_workorder/codebase_performance_workorder_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/codebase_performance_workorder/codebase_performance_workorder_${TARGET_DATE}.md" \
      "codebase_performance_workorder"
  fi
fi
if [ "$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL" = "true" ] || [ "$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL" = "1" ]; then
  wait_for_postclose_resources "time_window_regime_counterfactual"
  time_window_attempt=1
  time_window_resume_arg=()
  while [ "$time_window_attempt" -le "$TIME_WINDOW_REGIME_MAX_RESUME_ATTEMPTS" ]; do
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.time_window_regime_counterfactual \
      --date "$TARGET_DATE" \
      --backfill \
      "${time_window_resume_arg[@]}"
    time_window_status="$("$VENV_PY" - "$PROJECT_DIR/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_${TARGET_DATE}.json" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
print("resume" if summary.get("resume_required") else "done")
PY
)"
    if [ "$time_window_status" = "done" ]; then
      break
    fi
    time_window_attempt=$((time_window_attempt + 1))
    time_window_resume_arg=(--resume)
    wait_for_postclose_resources "time_window_regime_counterfactual_resume"
  done
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_${TARGET_DATE}.md" \
    "time_window_regime_counterfactual"
fi
if [ "$RUN_PRODUCER_GAP_DISCOVERY" = "true" ] || [ "$RUN_PRODUCER_GAP_DISCOVERY" = "1" ]; then
  wait_for_postclose_resources "producer_gap_source_bundle"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.producer_gap_source_bundle \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/producer_gap_source_bundle/producer_gap_source_bundle_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/producer_gap_source_bundle/producer_gap_source_bundle_${TARGET_DATE}.md" \
    "producer_gap_source_bundle"
  automation_trigger_decision "producer_gap_discovery"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" != "skip" ]; then
    wait_for_postclose_resources "producer_gap_discovery"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.producer_gap_discovery \
      --date "$TARGET_DATE" \
      --provider "$PRODUCER_GAP_DISCOVERY_AI_PROVIDER" \
      --rolling-sim-scan || \
      echo "[threshold-cycle] producer gap discovery returned fail-closed report (non-fatal); downstream verification will consume artifact" >&2
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.md" \
      "producer_gap_discovery"
  else
    skip_triggered_step "producer_gap_discovery" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.md" \
      "producer_gap_discovery"
  fi
fi
if [ "$RUN_STAGE_HOOK_WORKORDER_DISCOVERY" = "true" ] || [ "$RUN_STAGE_HOOK_WORKORDER_DISCOVERY" = "1" ]; then
  automation_trigger_decision "stage_hook_workorder_discovery"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" != "skip" ]; then
    wait_for_postclose_resources "stage_hook_workorder_discovery"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.stage_hook_workorder_discovery \
      --date "$TARGET_DATE" \
      --provider "$STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER" || \
      echo "[threshold-cycle] stage hook workorder discovery returned fail-closed report (non-fatal); downstream verification will consume artifact" >&2
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.md" \
      "stage_hook_workorder_discovery"
  else
    skip_triggered_step "stage_hook_workorder_discovery" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.md" \
      "stage_hook_workorder_discovery"
  fi
fi
if [ "$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD" = "true" ] || [ "$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD" = "1" ]; then
  automation_trigger_decision "stage_hook_runtime_scaffold"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" != "skip" ]; then
    wait_for_postclose_resources "stage_hook_runtime_scaffold"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.stage_hook_runtime_scaffold --date "$TARGET_DATE" || \
      echo "[threshold-cycle] stage hook runtime scaffold returned fail-closed report (non-fatal); downstream verification will consume artifact" >&2
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.md" \
      "stage_hook_runtime_scaffold"
  else
    skip_triggered_step "stage_hook_runtime_scaffold" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.md" \
      "stage_hook_runtime_scaffold"
  fi
fi
if [ "$RUN_INTRADAY_WS_FRESHNESS_FINALIZE" = "true" ] || [ "$RUN_INTRADAY_WS_FRESHNESS_FINALIZE" = "1" ]; then
  intraday_ws_symbol_master="$PROJECT_DIR/data/report/micro_reversion_economic_reference/micro_reversion_symbol_master_${TARGET_DATE}.json"
  intraday_ws_state="$PROJECT_DIR/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_${TARGET_DATE}.json"
  wait_for_postclose_resources "intraday_ws_freshness_finalize"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.intraday_ws_freshness_monitor \
    --target-date "$TARGET_DATE" \
    --incremental-state-path "$intraday_ws_state" \
    --symbol-master-path "$intraday_ws_symbol_master" \
    --write \
    --monitor-only
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_${TARGET_DATE}.md" \
    "intraday_ws_freshness_finalize"
fi
run_threshold_cycle_ev_and_wait "pre_workorder"
if [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "true" ] || [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "1" ]; then
  automation_trigger_decision "workorder_branch"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
    skip_triggered_step "code_improvement_workorder_branch" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
      "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md" \
      "code_improvement_workorder"
  else
    wait_for_postclose_resources "code_improvement_workorder"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_code_improvement_workorder \
      --date "$TARGET_DATE" \
      --max-orders "$CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS" \
      "${WORKORDER_SWING_ARGS[@]}"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
      "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md" \
      "code_improvement_workorder"
  fi
fi
run_threshold_cycle_ev_and_wait "post_workorder_refresh" \
  "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
  "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md"
if [ "$RUN_PATTERN_LAB_PROPAGATION_AUDIT" = "true" ] || [ "$RUN_PATTERN_LAB_PROPAGATION_AUDIT" = "1" ]; then
  automation_trigger_decision "pattern_lab_propagation_audit"
  if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
    skip_triggered_step "pattern_lab_propagation_audit" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md" \
      "pattern_lab_propagation_audit"
  else
    wait_for_postclose_resources "pattern_lab_propagation_audit"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_propagation_audit \
      --date "$TARGET_DATE" "${PATTERN_LAB_SWING_ARGS[@]}"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md" \
      "pattern_lab_propagation_audit"
  fi
  if [ "$RUN_PATTERN_LAB_AI_REVIEW" = "true" ] || [ "$RUN_PATTERN_LAB_AI_REVIEW" = "1" ]; then
    wait_for_postclose_resources "pattern_lab_ai_review_source_provenance_refresh"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_ai_review \
      --date "$TARGET_DATE" \
      --refresh-source-provenance \
      "${PATTERN_LAB_SWING_ARGS[@]}"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.md" \
      "pattern_lab_ai_review_source_provenance_refresh"
  fi
  run_threshold_cycle_ev_and_wait "post_propagation_audit_refresh" \
    "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md" \
    "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.md"
fi
wait_for_postclose_resources "runtime_approval_summary"
RUNTIME_APPROVAL_SCOPE_ARGS=("${POSTCLOSE_SWING_SCOPE_ARGS[@]}")
if [[ "$RUN_PRODUCER_GAP_DISCOVERY" != "true" && "$RUN_PRODUCER_GAP_DISCOVERY" != "1" ]]; then
  RUNTIME_APPROVAL_SCOPE_ARGS+=(--producer-gap-disabled)
fi
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_approval_summary \
  --date "$TARGET_DATE" "${RUNTIME_APPROVAL_SCOPE_ARGS[@]}"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.md" \
  "runtime_approval_summary"
automation_trigger_decision "runtime_apply_gap_audit"
if [ "$AUTOMATION_TRIGGER_DECISION_RESULT" = "skip" ]; then
  skip_triggered_step "runtime_apply_gap_audit" "fresh_outputs_no_trigger"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.md" \
    "runtime_apply_gap_audit"
else
  wait_for_postclose_resources "runtime_apply_gap_audit"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_apply_gap_audit \
    --date "$TARGET_DATE" "${POSTCLOSE_SWING_SCOPE_ARGS[@]}"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.md" \
    "runtime_apply_gap_audit"
fi
wait_for_postclose_resources "key_lineage_ledger"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.key_lineage_ledger \
  --date "$TARGET_DATE" "${POSTCLOSE_SWING_SCOPE_ARGS[@]}"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/key_lineage_ledger/key_lineage_ledger_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/key_lineage_ledger/key_lineage_ledger_${TARGET_DATE}.md" \
  "key_lineage_ledger"
wait_for_postclose_resources "conversion_lane"
CONVERSION_LANE_SWING_ARGS=()
if [[ "$RUN_SWING_POSTCLOSE" != "true" && "$RUN_SWING_POSTCLOSE" != "1" ]]; then
  CONVERSION_LANE_SWING_ARGS+=(--exclude-swing)
fi
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.conversion_lane \
  --date "$TARGET_DATE" "${CONVERSION_LANE_SWING_ARGS[@]}"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/conversion_lane/conversion_lane_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/conversion_lane/conversion_lane_${TARGET_DATE}.md" \
  "conversion_lane"
if [ "$RUN_RISING_MISSED_CLASSIFIER_PRIOR" = "true" ] || [ "$RUN_RISING_MISSED_CLASSIFIER_PRIOR" = "1" ]; then
  wait_for_postclose_resources "rising_missed_classifier_prior"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.rising_missed_classifier_prior \
    --target-date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_${TARGET_DATE}.md" \
    "rising_missed_classifier_prior"
  wait_for_postclose_resources "rising_missed_scout_workorder_prior_refresh"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.rising_missed_scout_workorder \
    --target-date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_${TARGET_DATE}.md" \
    "rising_missed_scout_workorder_prior_refresh"
  if [ "$RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER" = "true" ] || [ "$RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER" = "1" ]; then
    # The cumulative prior depends on lifecycle/lineage artifacts produced after
    # the first sim-control-tower pass. Refresh the catalog here so downstream
    # workorders, summaries, and PREOPEN handoff consume the same-date prior.
    wait_for_postclose_resources "scalp_sim_auto_approval_control_tower_prior_refresh"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping.scalp_sim_auto_approval_control_tower --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_${TARGET_DATE}.json" \
      "scalp_sim_auto_approval_control_tower_prior_refresh"
  fi
fi
if [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "true" ] || [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "1" ]; then
  wait_for_postclose_resources "code_improvement_workorder_post_conversion_lane"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_code_improvement_workorder \
    --date "$TARGET_DATE" \
    --max-orders "$CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS" \
    "${WORKORDER_SWING_ARGS[@]}"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md" \
    "code_improvement_workorder_post_conversion_lane"
  run_threshold_cycle_ev_and_wait "post_conversion_lane_workorder_refresh" \
    "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md"
  wait_for_postclose_resources "runtime_approval_summary_post_conversion_lane_workorder"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_approval_summary \
    --date "$TARGET_DATE" "${RUNTIME_APPROVAL_SCOPE_ARGS[@]}"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.md" \
    "runtime_approval_summary_post_conversion_lane_workorder"
fi
wait_for_postclose_resources "build_next_stage2_checklist"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_next_stage2_checklist --source-date "$TARGET_DATE"
wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist"
VERIFY_DISABLED_STAGE_ARGS=()
if [[ "$RUN_SWING_LIFECYCLE_AUDIT" != "true" && "$RUN_SWING_LIFECYCLE_AUDIT" != "1" ]]; then
  VERIFY_DISABLED_STAGE_ARGS+=(--disabled-stage swing_lifecycle)
fi
if [[ "$RUN_SWING_STRATEGY_DISCOVERY" != "true" && "$RUN_SWING_STRATEGY_DISCOVERY" != "1" ]]; then
  VERIFY_DISABLED_STAGE_ARGS+=(--disabled-stage swing_strategy_discovery)
fi
if [[ "$RUN_SWING_LIFECYCLE_MATRIX" != "true" && "$RUN_SWING_LIFECYCLE_MATRIX" != "1" ]]; then
  VERIFY_DISABLED_STAGE_ARGS+=(--disabled-stage swing_lifecycle_matrix)
fi
if [[ "$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY" != "true" && "$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY" != "1" ]]; then
  VERIFY_DISABLED_STAGE_ARGS+=(--disabled-stage swing_lifecycle_bucket_discovery)
fi
if [[ "$RUN_DEEPSEEK_SWING_LAB" != "true" && "$RUN_DEEPSEEK_SWING_LAB" != "1" ]]; then
  VERIFY_DISABLED_STAGE_ARGS+=(--disabled-stage deepseek_swing_lab)
fi
run_threshold_cycle_ev_and_wait "final_consumer_refresh"   "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json"   "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md"   "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json"   "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json"   "$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json"   "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json"
if [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "true" ] || [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "1" ]; then
  wait_for_postclose_resources "code_improvement_workorder_final_source_refresh"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_code_improvement_workorder \
    --date "$TARGET_DATE" \
    --max-orders "$CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS" \
    "${WORKORDER_SWING_ARGS[@]}"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md" \
    "code_improvement_workorder_final_source_refresh"
fi
wait_for_postclose_resources "runtime_approval_summary_final_refresh"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_approval_summary \
  --date "$TARGET_DATE" "${RUNTIME_APPROVAL_SCOPE_ARGS[@]}"
wait_for_report_artifact   "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json"   "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.md"   "runtime_approval_summary_final_refresh"
wait_for_postclose_resources "build_next_stage2_checklist_final_refresh"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_next_stage2_checklist --source-date "$TARGET_DATE"
wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist_final_refresh"
wait_for_postclose_resources "verify_threshold_cycle_postclose_chain"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain \
  --date "$TARGET_DATE" \
  --allow-pending-done-marker \
  "${VERIFY_DISABLED_STAGE_ARGS[@]}"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.md" \
  "threshold_cycle_postclose_verification"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500 >/dev/null
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
write_postclose_status succeeded completed 0 1
emit_postclose_marker "[STATUS] machine_microstructure_policy_approval target_date=$TARGET_DATE enabled=$RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL runtime_effect=false"
emit_postclose_marker "[STATUS] intraday_ws_freshness_finalize target_date=$TARGET_DATE enabled=$RUN_INTRADAY_WS_FRESHNESS_FINALIZE runtime_effect=false"
emit_postclose_marker "[DONE] threshold-cycle postclose target_date=$TARGET_DATE ai_correction_provider=$AI_CORRECTION_PROVIDER panic_sell_defense=$RUN_PANIC_SELL_DEFENSE_REPORT market_panic_breadth=$RUN_MARKET_PANIC_BREADTH_REPORT pipeline_event_verbosity=$RUN_PIPELINE_EVENT_VERBOSITY_REPORT limit_down_watch_report=$RUN_LIMIT_DOWN_WATCH_REPORT observation_source_quality_audit=$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT opening_rotation_profile_tuning=$RUN_OPENING_ROTATION_PROFILE_TUNING ai_decision_quality_daily_materialization=$RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION main_ai_quality_r0_r3=$RUN_MAIN_AI_QUALITY_R0_R3 main_ai_quality_provider_replay=$MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY ai_decision_action_outcome_calibration=$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION codebase_performance_workorder=$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT pattern_lab_currentness_audit=$RUN_PATTERN_LAB_CURRENTNESS_AUDIT pattern_lab_ai_review=$RUN_PATTERN_LAB_AI_REVIEW time_window_regime_counterfactual=$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL producer_gap_discovery=$RUN_PRODUCER_GAP_DISCOVERY stage_hook_workorder_discovery=$RUN_STAGE_HOOK_WORKORDER_DISCOVERY stage_hook_runtime_scaffold=$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD pattern_lab_propagation_audit=$RUN_PATTERN_LAB_PROPAGATION_AUDIT scalp_sim_overnight=$RUN_SCALP_SIM_OVERNIGHT_REPORT scalp_entry_adm=$RUN_SCALP_ENTRY_ADM entry_split_order_plan=$RUN_ENTRY_SPLIT_ORDER_PLAN scale_in_split_order_plan=$RUN_SCALE_IN_SPLIT_ORDER_PLAN entry_ai_gate_backtest=$RUN_ENTRY_AI_GATE_BACKTEST rising_missed_intraday_feedback_postclose=$RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE rising_missed_scout_workorder=$RUN_RISING_MISSED_SCOUT_WORKORDER scalping_pyramid_intraday_feedback_postclose=$RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE scalping_pyramid_quality_calibration=$RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION scalping_avg_down_recovery_calibration=$RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION rising_missed_classifier_prior=$RUN_RISING_MISSED_CLASSIFIER_PRIOR samsung_machine_entry_tuning=$RUN_SAMSUNG_MACHINE_ENTRY_TUNING low_price_two_leg_tuning=$RUN_LOW_PRICE_TWO_LEG_TUNING low_price_two_leg_candidate_recommendation=$RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION machine_microstructure_attribution=$RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION one_share_threshold_opportunity=$RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY one_share_threshold_opportunity_ai_provider=$ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER institutional_flow_context=$RUN_INSTITUTIONAL_FLOW_CONTEXT microstructure_reaction_context=$RUN_MICROSTRUCTURE_REACTION_CONTEXT lifecycle_decision_matrix=$RUN_LIFECYCLE_DECISION_MATRIX lifecycle_ai_context=$RUN_LIFECYCLE_AI_CONTEXT ldm_hypothesis_parent_refinement=$RUN_LDM_HYPOTHESIS_PARENT_REFINEMENT lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY lifecycle_bucket_windows=$RUN_LIFECYCLE_BUCKET_WINDOWS lifecycle_bucket_window_list=$LIFECYCLE_BUCKET_WINDOWS lifecycle_bucket_promotion_window=$LIFECYCLE_BUCKET_PROMOTION_WINDOW force_lifecycle_bucket_windows=$FORCE_LIFECYCLE_BUCKET_WINDOWS force_deep_audits=$FORCE_DEEP_AUDITS force_workorder_branch=$FORCE_WORKORDER_BRANCH runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE scalp_sim_auto_approval_control_tower=$RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER latency_classifier_recommendation=$RUN_LATENCY_CLASSIFIER_RECOMMENDATION tuning_performance_control_tower=$RUN_TUNING_PERFORMANCE_CONTROL_TOWER swing_lifecycle=$RUN_SWING_LIFECYCLE_AUDIT swing_strategy_discovery=$RUN_SWING_STRATEGY_DISCOVERY swing_lifecycle_matrix=$RUN_SWING_LIFECYCLE_MATRIX swing_lifecycle_bucket_discovery=$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY swing_ai_review_provider=$SWING_THRESHOLD_AI_REVIEW_PROVIDER swing_lifecycle_bucket_discovery_ai_provider=$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER pattern_lab_ai_review_provider=$PATTERN_LAB_AI_REVIEW_PROVIDER producer_gap_discovery_ai_provider=$PRODUCER_GAP_DISCOVERY_AI_PROVIDER stage_hook_workorder_discovery_ai_provider=$STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER pattern_labs=$RUN_PATTERN_LABS deepseek_swing_lab=$RUN_DEEPSEEK_SWING_LAB code_improvement_workorder=$BUILD_CODE_IMPROVEMENT_WORKORDER daily_ev=true runtime_approval_summary=true runtime_apply_gap_audit=true key_lineage_ledger=true conversion_lane=true next_stage2_checklist=true finished_at=$finished_at"
wait_for_postclose_resources "verify_threshold_cycle_postclose_chain_final"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain \
  --date "$TARGET_DATE" \
  "${VERIFY_DISABLED_STAGE_ARGS[@]}"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.md" \
  "threshold_cycle_postclose_verification_final"
if [ "$RUN_TUNING_PERFORMANCE_CONTROL_TOWER" = "true" ] || [ "$RUN_TUNING_PERFORMANCE_CONTROL_TOWER" = "1" ]; then
  wait_for_postclose_resources "tuning_performance_control_tower"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.tuning_performance_control_tower --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/tuning_performance_control_tower/tuning_performance_control_tower_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/tuning_performance_control_tower/tuning_performance_control_tower_${TARGET_DATE}.md" \
    "tuning_performance_control_tower"
fi
restart_postclose_bot_if_requested
