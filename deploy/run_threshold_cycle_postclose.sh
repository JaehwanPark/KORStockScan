#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"
MAX_ITERATIONS="${THRESHOLD_CYCLE_MAX_ITERATIONS:-80}"
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
PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-${KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE:-2026-06-04}}"
RUN_SWING_LIFECYCLE_AUDIT="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_AUDIT:-true}"
RUN_SWING_STRATEGY_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_STRATEGY_DISCOVERY:-true}"
RUN_SWING_LIFECYCLE_MATRIX="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_MATRIX:-$RUN_SWING_STRATEGY_DISCOVERY}"
RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_SWING_LIFECYCLE_MATRIX}"
SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-openai}"
# Postclose standard path defaults Swing lifecycle bucket discovery Tier2 review to OpenAI.
# Direct module execution still defaults to provider=none unless this wrapper/env passes a provider.
SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER:-$SWING_THRESHOLD_AI_REVIEW_PROVIDER}"
BUILD_CODE_IMPROVEMENT_WORKORDER="${THRESHOLD_CYCLE_BUILD_CODE_IMPROVEMENT_WORKORDER:-true}"
CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS="${CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS:-12}"
RUN_DEEPSEEK_SWING_LAB="${THRESHOLD_CYCLE_RUN_DEEPSEEK_SWING_LAB:-true}"
RUN_PANIC_SELL_DEFENSE_REPORT="${THRESHOLD_CYCLE_RUN_PANIC_SELL_DEFENSE_REPORT:-true}"
RUN_PANIC_BUYING_REPORT="${THRESHOLD_CYCLE_RUN_PANIC_BUYING_REPORT:-true}"
RUN_MARKET_PANIC_BREADTH_REPORT="${THRESHOLD_CYCLE_RUN_MARKET_PANIC_BREADTH_REPORT:-true}"
RUN_OPENAI_WS_STABILITY_REPORT="${THRESHOLD_CYCLE_RUN_OPENAI_WS_STABILITY_REPORT:-true}"
RUN_PIPELINE_EVENT_VERBOSITY_REPORT="${THRESHOLD_CYCLE_RUN_PIPELINE_EVENT_VERBOSITY_REPORT:-true}"
RUN_OBSERVATION_SOURCE_QUALITY_AUDIT="${THRESHOLD_CYCLE_RUN_OBSERVATION_SOURCE_QUALITY_AUDIT:-true}"
RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT="${THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT:-true}"
RUN_SCALP_SIM_AI_DEFERRED_REVIEW="${THRESHOLD_CYCLE_RUN_SCALP_SIM_AI_DEFERRED_REVIEW:-true}"
RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}"
RUN_PATTERN_LAB_AI_REVIEW="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_AI_REVIEW:-true}"
PATTERN_LAB_AI_REVIEW_PROVIDER="${KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER:-openai}"
RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL="${THRESHOLD_CYCLE_RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL:-true}"
TIME_WINDOW_REGIME_MAX_RESUME_ATTEMPTS="${THRESHOLD_CYCLE_TIME_WINDOW_REGIME_MAX_RESUME_ATTEMPTS:-2}"
RUN_PRODUCER_GAP_DISCOVERY="${THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY:-true}"
PRODUCER_GAP_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_PRODUCER_GAP_DISCOVERY_AI_PROVIDER:-openai}"
RUN_STAGE_HOOK_WORKORDER_DISCOVERY="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY:-true}"
STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER:-openai}"
RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-true}"
RUN_PATTERN_LAB_PROPAGATION_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}"
RUN_SIM_POST_SELL_FEEDBACK="${THRESHOLD_CYCLE_RUN_SIM_POST_SELL_FEEDBACK:-true}"
RUN_SCALP_SIM_OVERNIGHT_REPORT="${THRESHOLD_CYCLE_RUN_SCALP_SIM_OVERNIGHT_REPORT:-true}"
RUN_SCALP_ENTRY_ADM="${THRESHOLD_CYCLE_RUN_SCALP_ENTRY_ADM:-true}"
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
FORCE_DUPLICATE_REFRESH="${THRESHOLD_CYCLE_FORCE_DUPLICATE_REFRESH:-false}"
FORCE_LIFECYCLE_BUCKET_WINDOWS="${THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS:-false}"
FORCE_DEEP_AUDITS="${THRESHOLD_CYCLE_FORCE_DEEP_AUDITS:-false}"
FORCE_WORKORDER_BRANCH="${THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH:-false}"
SNAPSHOT_RETENTION_DAYS="${THRESHOLD_CYCLE_SNAPSHOT_RETENTION_DAYS:-7}"
ARTIFACT_WAIT_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC:-600}"
ARTIFACT_WAIT_INTERVAL_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_INTERVAL_SEC:-5}"
STATUS_DIR="$PROJECT_DIR/data/report/threshold_cycle_postclose_status"
STATUS_FILE="$STATUS_DIR/threshold_cycle_postclose_${TARGET_DATE}.status.json"
POSTCLOSE_MARKER_LOG="${THRESHOLD_CYCLE_POSTCLOSE_MARKER_LOG:-$PROJECT_DIR/logs/threshold_cycle_postclose_cron.log}"
POSTCLOSE_MARKER_LOG_ENABLED="${THRESHOLD_CYCLE_POSTCLOSE_MARKER_LOG_ENABLED:-true}"
POSTCLOSE_BOT_ISOLATION_MARKER="$PROJECT_DIR/tmp/postclose_bot_isolation.json"
AI_CORRECTION_FINAL_STATUS="not_run"

mkdir -p "$PROJECT_DIR/logs" "$STATUS_DIR"
cd "$PROJECT_DIR"

write_postclose_status() {
  local status="$1"
  local reason="${2:-}"
  local exit_code="${3:-0}"
  local finished="${4:-0}"
  "$VENV_PY" - "$STATUS_FILE" "$TARGET_DATE" "$status" "$reason" "$exit_code" "$finished" "$AI_CORRECTION_PROVIDER" "$AI_CORRECTION_FINAL_STATUS" <<'PY'
import json
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
    sleep "$POSTCLOSE_BOT_RESTART_WAIT_SEC"
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

trap 'rc=$?; mark_postclose_failed command_failed "$rc"; restart_postclose_bot_if_requested; exit "$rc"' ERR
trap 'mark_postclose_failed interrupted 130; restart_postclose_bot_if_requested; exit 130' INT
trap 'mark_postclose_failed terminated 143; restart_postclose_bot_if_requested; exit 143' TERM

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
write_postclose_status running started 0 0
emit_postclose_marker "[START] threshold-cycle postclose target_date=$TARGET_DATE max_iterations=$MAX_ITERATIONS started_at=$started_at"
stop_postclose_bot_if_requested

run_postclose_cmd() {
  local cmd=("$@")
  if command -v nice >/dev/null 2>&1; then
    cmd=(nice -n "$POSTCLOSE_NICE_LEVEL" "${cmd[@]}")
  fi
  if command -v ionice >/dev/null 2>&1 && [[ "$POSTCLOSE_IONICE_CLASS" -ge 0 ]]; then
    cmd=(ionice -c "$POSTCLOSE_IONICE_CLASS" -n "$POSTCLOSE_IONICE_LEVEL" -t "${cmd[@]}")
  fi
  korstockscan_apply_taskset "$POSTCLOSE_CPU_AFFINITY" "${cmd[@]}"
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
    echo "[threshold-cycle] resource guard wait label=$label waited=${waited}s status=$status" >&2
    sleep "$POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC"
    waited=$((waited + POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC))
  done
}

cleanup_threshold_cycle_snapshots() {
  local snapshot_dir="$1"
  local retention_days="$2"
  python3 - "$snapshot_dir" "$retention_days" <<'PY'
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
    sleep "$ARTIFACT_WAIT_INTERVAL_SEC"
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
    sleep "$ARTIFACT_WAIT_INTERVAL_SEC"
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
  if decision="$(THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS="$FORCE_LIFECYCLE_BUCKET_WINDOWS" \
    THRESHOLD_CYCLE_FORCE_DEEP_AUDITS="$FORCE_DEEP_AUDITS" \
    THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH="$FORCE_WORKORDER_BRANCH" \
    PYTHONPATH=. "$VENV_PY" -m src.engine.automation.automation_chain_trigger_decision \
      --date "$TARGET_DATE" \
      --scope all \
      --step "$step_id" \
      --write 2>/dev/null)"; then
    if [ "$decision" = "skip" ]; then
      printf 'skip\n'
      return 0
    fi
  fi
  printf 'run\n'
}

skip_triggered_step() {
  local step_id="$1"
  local reason="$2"
  emit_postclose_marker "[SKIP] threshold-cycle postclose target_date=$TARGET_DATE step=$step_id reason=$reason trigger_decision=skip"
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
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_ev_report --date "$TARGET_DATE"
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
  SNAPSHOT_PATH="$SNAPSHOT_DIR/pipeline_events_${TARGET_DATE}_${SNAPSHOT_TS}.jsonl"
  if [ -f "$CHECKPOINT_PATH" ] && [ -n "$EXISTING_SNAPSHOT_PATH" ] && [ -f "$EXISTING_SNAPSHOT_PATH" ]; then
    SOURCE_ARGS=(--source-path "$EXISTING_SNAPSHOT_PATH")
    REUSE_EXISTING_SNAPSHOT="true"
    echo "[threshold-cycle] reusing immutable snapshot source=$EXISTING_SNAPSHOT_PATH checkpoint=$CHECKPOINT_PATH"
  elif [ -f "$RAW_SOURCE" ]; then
    cp --reflink=auto "$RAW_SOURCE" "$SNAPSHOT_PATH"
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
  out="$(
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events \
      --date "$TARGET_DATE" \
      --mode incremental \
      "${resume_args[@]}" \
      "${SOURCE_ARGS[@]}" \
      --max-input-lines-per-chunk "$MAX_INPUT_LINES" \
      --max-output-lines-per-partition "$MAX_OUTPUT_LINES" \
      --max-cpu-busy-pct "$MAX_CPU_BUSY_PCT"
  )"
  echo "$out"
  completed="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(str(json.load(sys.stdin).get("completed", False)).lower())')"
  status="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("status", ""))')"
  paused_reason="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("paused_reason") or "")')"
  if [ "$completed" = "true" ]; then
    break
  fi
  if [ "$status" = "paused_by_availability_guard" ] && [ -n "$paused_reason" ]; then
    if [ "$compact_availability_waited" -ge "$COMPACT_AVAILABILITY_WAIT_SEC" ]; then
      echo "[threshold-cycle] availability guard timeout target_date=$TARGET_DATE reason=$paused_reason waited=${compact_availability_waited}s"
      break
    fi
    echo "[threshold-cycle] availability guard wait target_date=$TARGET_DATE reason=$paused_reason waited=${compact_availability_waited}s"
    sleep "$COMPACT_AVAILABILITY_WAIT_INTERVAL_SEC"
    compact_availability_waited=$((compact_availability_waited + COMPACT_AVAILABILITY_WAIT_INTERVAL_SEC))
    continue
  fi
  compact_availability_waited=0
  sleep 1
done

if [ "${completed:-false}" != "true" ]; then
  echo "[threshold-cycle] compact collection incomplete target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-}" >&2
  failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"
  if [ "${status:-}" = "paused_by_availability_guard" ]; then
    emit_postclose_marker "[PAUSED] threshold-cycle postclose target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-} failed_at=$failed_at"
  fi
  emit_postclose_marker "[FAIL] threshold-cycle postclose target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-} failed_at=$failed_at"
  exit 2
fi

if [ "$RUN_SIM_POST_SELL_FEEDBACK" = "true" ] || [ "$RUN_SIM_POST_SELL_FEEDBACK" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.sniper_post_sell_feedback \
    --date "$TARGET_DATE" \
    --backfill-sim-candidates \
    --evaluate-sim
fi
if [ "$RUN_SCALP_ENTRY_ADM" = "true" ] || [ "$RUN_SCALP_ENTRY_ADM" = "1" ]; then
  wait_for_postclose_resources "scalp_entry_action_decision_matrix"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalp_entry_action_decision_matrix --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.md" \
    "scalp_entry_action_decision_matrix"
fi
if [ "$RUN_SCALP_SIM_OVERNIGHT_REPORT" = "true" ] || [ "$RUN_SCALP_SIM_OVERNIGHT_REPORT" = "1" ]; then
  wait_for_postclose_resources "scalp_sim_overnight"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalp_sim_overnight --date "$TARGET_DATE" --report-only
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/scalp_sim_overnight/scalp_sim_overnight_${TARGET_DATE}.json" \
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
if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "true" ] || [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "1" ]; then
  wait_for_postclose_resources "observation_source_quality_preflight"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.observation_source_quality_audit --target-date "$TARGET_DATE" --write
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
    "observation_source_quality_preflight"
fi
if [ "$RUN_LIFECYCLE_DECISION_MATRIX" = "true" ] || [ "$RUN_LIFECYCLE_DECISION_MATRIX" = "1" ]; then
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
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle_bucket_discovery --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.md" \
    "lifecycle_bucket_discovery"
  if [ "$RUN_LIFECYCLE_BUCKET_WINDOWS" = "true" ] || [ "$RUN_LIFECYCLE_BUCKET_WINDOWS" = "1" ]; then
    IFS=',' read -r -a lifecycle_bucket_window_items <<< "$LIFECYCLE_BUCKET_WINDOWS"
    for lifecycle_bucket_window in "${lifecycle_bucket_window_items[@]}"; do
      lifecycle_bucket_window="$(printf '%s' "$lifecycle_bucket_window" | tr -d '[:space:]')"
      [ -n "$lifecycle_bucket_window" ] || continue
      if [ "$(automation_trigger_decision "lifecycle_window_${lifecycle_bucket_window}")" = "skip" ]; then
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
        --output-suffix "$lifecycle_bucket_window"; then
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
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.latency_classifier_recommendation "${latency_args[@]}"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/latency_classifier_recommendation/latency_classifier_recommendation_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/latency_classifier_recommendation/latency_classifier_recommendation_${TARGET_DATE}.md" \
    "latency_classifier_recommendation"
fi

if { [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "true" ] || [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "1" ] || [ "$RUN_PANIC_BUYING_REPORT" = "true" ] || [ "$RUN_PANIC_BUYING_REPORT" = "1" ]; } && { [ "$RUN_MARKET_PANIC_BREADTH_REPORT" = "true" ] || [ "$RUN_MARKET_PANIC_BREADTH_REPORT" = "1" ]; }; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.market_panic_breadth_collector \
    --date "$TARGET_DATE"
  wait_for_json_artifact \
    "$PROJECT_DIR/data/report/market_panic_breadth/market_panic_breadth_${TARGET_DATE}.json" \
    "market_panic_breadth_postclose"
fi
if [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "true" ] || [ "$RUN_PANIC_SELL_DEFENSE_REPORT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.panic_sell_defense_report \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/panic_sell_defense/panic_sell_defense_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/panic_sell_defense/panic_sell_defense_${TARGET_DATE}.md" \
    "panic_sell_defense_postclose"
fi
if [ "$RUN_PANIC_BUYING_REPORT" = "true" ] || [ "$RUN_PANIC_BUYING_REPORT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.panic_buying_report \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/panic_buying/panic_buying_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/panic_buying/panic_buying_${TARGET_DATE}.md" \
    "panic_buying_postclose"
fi
if [ "$RUN_OPENAI_WS_STABILITY_REPORT" = "true" ] || [ "$RUN_OPENAI_WS_STABILITY_REPORT" = "1" ]; then
  wait_for_postclose_resources "openai_ws_stability"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.openai_ws_stability_report \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/openai_ws/openai_ws_stability_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/openai_ws/openai_ws_stability_${TARGET_DATE}.md" \
    "openai_ws_stability_postclose"
fi

if [ "$RUN_SCALP_SIM_AI_DEFERRED_REVIEW" = "true" ] || [ "$RUN_SCALP_SIM_AI_DEFERRED_REVIEW" = "1" ]; then
  if [ "$(automation_trigger_decision "scalp_sim_ai_deferred_review")" = "skip" ]; then
    skip_triggered_step "scalp_sim_ai_deferred_review" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/scalp_sim_ai_deferred_review/scalp_sim_ai_deferred_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/scalp_sim_ai_deferred_review/scalp_sim_ai_deferred_review_${TARGET_DATE}.md" \
      "scalp_sim_ai_deferred_review"
  else
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalp_sim_ai_deferred_review \
      --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/scalp_sim_ai_deferred_review/scalp_sim_ai_deferred_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/scalp_sim_ai_deferred_review/scalp_sim_ai_deferred_review_${TARGET_DATE}.md" \
      "scalp_sim_ai_deferred_review"
  fi
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
	  sleep "$AI_CORRECTION_RETRY_DELAY_SEC"
	  ai_correction_attempt=$((ai_correction_attempt + 1))
	done
	AI_CORRECTION_FINAL_STATUS="$ai_correction_status"
	if [ "$AI_CORRECTION_PROVIDER" != "none" ] && [ -z "$AI_CORRECTION_RESPONSE_JSON" ] && [ "$ai_correction_status" != "parsed" ]; then
	  echo "[threshold-cycle] ai correction final unavailable target_date=$TARGET_DATE provider=$AI_CORRECTION_PROVIDER status=$ai_correction_status action=postclose_verifier_will_fail_if_runtime_candidates_blocked" >&2
	fi
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
  wait_for_postclose_resources "gemini_scalping_pattern_lab"
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    run_postclose_cmd "$PROJECT_DIR/analysis/gemini_scalping_pattern_lab/run.sh" || \
    echo "[threshold-cycle] gemini scalping pattern lab failed (non-fatal); downstream automation will mark freshness=false" >&2
  wait_for_postclose_resources "claude_scalping_pattern_lab"
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    run_postclose_cmd "$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh" || \
    echo "[threshold-cycle] claude scalping pattern lab failed (non-fatal); downstream automation will mark freshness=false" >&2
fi
wait_for_postclose_resources "scalping_pattern_lab_automation"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.scalping_pattern_lab_automation --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_${TARGET_DATE}.md" \
  "scalping_pattern_lab_automation"
wait_for_postclose_resources "swing_pattern_lab_automation"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_pattern_lab_automation --date "$TARGET_DATE" || \
  echo "[threshold-cycle] swing pattern lab automation failed (non-fatal)" >&2
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_${TARGET_DATE}.md" \
  "swing_pattern_lab_automation"
if [ "$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" = "true" ] || [ "$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" = "1" ]; then
  if [ "$(automation_trigger_decision "pattern_lab_currentness_audit")" = "skip" ]; then
    skip_triggered_step "pattern_lab_currentness_audit" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.md" \
      "pattern_lab_currentness_audit"
  else
    wait_for_postclose_resources "pattern_lab_currentness_audit"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_currentness_audit --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.md" \
      "pattern_lab_currentness_audit"
  fi
fi
if [ "$RUN_PATTERN_LAB_AI_REVIEW" = "true" ] || [ "$RUN_PATTERN_LAB_AI_REVIEW" = "1" ]; then
  if [ "$(automation_trigger_decision "pattern_lab_ai_review")" = "skip" ]; then
    skip_triggered_step "pattern_lab_ai_review" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.md" \
      "pattern_lab_ai_review"
  else
    wait_for_postclose_resources "pattern_lab_ai_review"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_ai_review \
      --date "$TARGET_DATE" \
      --provider "$PATTERN_LAB_AI_REVIEW_PROVIDER"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.md" \
      "pattern_lab_ai_review"
  fi
fi
if [ "$RUN_PIPELINE_EVENT_VERBOSITY_REPORT" = "true" ] || [ "$RUN_PIPELINE_EVENT_VERBOSITY_REPORT" = "1" ]; then
  wait_for_postclose_resources "pipeline_event_verbosity"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pipeline_event_verbosity_report --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/pipeline_event_verbosity/pipeline_event_verbosity_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/pipeline_event_verbosity/pipeline_event_verbosity_${TARGET_DATE}.md" \
    "pipeline_event_verbosity"
fi
if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "true" ] || [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "1" ]; then
  if [ "$(automation_trigger_decision "observation_source_quality_audit")" = "skip" ]; then
    skip_triggered_step "observation_source_quality_audit" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
      "observation_source_quality_audit"
  else
    wait_for_postclose_resources "observation_source_quality_audit"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.observation_source_quality_audit --target-date "$TARGET_DATE" --write
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
      "observation_source_quality_audit"
  fi
fi
if [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" = "true" ] || [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" = "1" ]; then
  if [ "$(automation_trigger_decision "codebase_performance_workorder")" = "skip" ]; then
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
  if [ "$(automation_trigger_decision "producer_gap_discovery")" != "skip" ]; then
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
  if [ "$(automation_trigger_decision "stage_hook_workorder_discovery")" != "skip" ]; then
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
  if [ "$(automation_trigger_decision "stage_hook_runtime_scaffold")" != "skip" ]; then
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
run_threshold_cycle_ev_and_wait "pre_workorder"
if [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "true" ] || [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "1" ]; then
  if [ "$(automation_trigger_decision "workorder_branch")" = "skip" ]; then
    skip_triggered_step "code_improvement_workorder_branch" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
      "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md" \
      "code_improvement_workorder"
  else
    wait_for_postclose_resources "code_improvement_workorder"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_code_improvement_workorder \
      --date "$TARGET_DATE" \
      --max-orders "$CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS"
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
  if [ "$(automation_trigger_decision "pattern_lab_propagation_audit")" = "skip" ]; then
    skip_triggered_step "pattern_lab_propagation_audit" "fresh_outputs_no_trigger"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md" \
      "pattern_lab_propagation_audit"
  else
    wait_for_postclose_resources "pattern_lab_propagation_audit"
    run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_propagation_audit --date "$TARGET_DATE"
    wait_for_report_artifact \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md" \
      "pattern_lab_propagation_audit"
    run_threshold_cycle_ev_and_wait "post_propagation_audit_refresh" \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
      "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md"
  fi
fi
wait_for_postclose_resources "runtime_approval_summary"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_approval_summary --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.md" \
  "runtime_approval_summary"
if [ "$(automation_trigger_decision "runtime_apply_gap_audit")" = "skip" ]; then
  skip_triggered_step "runtime_apply_gap_audit" "fresh_outputs_no_trigger"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.md" \
    "runtime_apply_gap_audit"
else
  wait_for_postclose_resources "runtime_apply_gap_audit"
  run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_apply_gap_audit --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.md" \
    "runtime_apply_gap_audit"
fi
wait_for_postclose_resources "build_next_stage2_checklist"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.build_next_stage2_checklist --source-date "$TARGET_DATE"
wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist"
wait_for_postclose_resources "verify_threshold_cycle_postclose_chain"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain --date "$TARGET_DATE" --allow-pending-done-marker
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.md" \
  "threshold_cycle_postclose_verification"
PYTHONPATH=. "$VENV_PY" -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500 >/dev/null
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
write_postclose_status succeeded completed 0 1
emit_postclose_marker "[DONE] threshold-cycle postclose target_date=$TARGET_DATE ai_correction_provider=$AI_CORRECTION_PROVIDER panic_sell_defense=$RUN_PANIC_SELL_DEFENSE_REPORT panic_buying=$RUN_PANIC_BUYING_REPORT market_panic_breadth=$RUN_MARKET_PANIC_BREADTH_REPORT openai_ws_stability=$RUN_OPENAI_WS_STABILITY_REPORT scalp_sim_ai_deferred_review=$RUN_SCALP_SIM_AI_DEFERRED_REVIEW pipeline_event_verbosity=$RUN_PIPELINE_EVENT_VERBOSITY_REPORT observation_source_quality_audit=$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT codebase_performance_workorder=$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT pattern_lab_currentness_audit=$RUN_PATTERN_LAB_CURRENTNESS_AUDIT pattern_lab_ai_review=$RUN_PATTERN_LAB_AI_REVIEW time_window_regime_counterfactual=$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL producer_gap_discovery=$RUN_PRODUCER_GAP_DISCOVERY stage_hook_workorder_discovery=$RUN_STAGE_HOOK_WORKORDER_DISCOVERY stage_hook_runtime_scaffold=$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD pattern_lab_propagation_audit=$RUN_PATTERN_LAB_PROPAGATION_AUDIT scalp_sim_overnight=$RUN_SCALP_SIM_OVERNIGHT_REPORT scalp_entry_adm=$RUN_SCALP_ENTRY_ADM institutional_flow_context=$RUN_INSTITUTIONAL_FLOW_CONTEXT microstructure_reaction_context=$RUN_MICROSTRUCTURE_REACTION_CONTEXT lifecycle_decision_matrix=$RUN_LIFECYCLE_DECISION_MATRIX lifecycle_ai_context=$RUN_LIFECYCLE_AI_CONTEXT ldm_hypothesis_parent_refinement=$RUN_LDM_HYPOTHESIS_PARENT_REFINEMENT lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY lifecycle_bucket_windows=$RUN_LIFECYCLE_BUCKET_WINDOWS lifecycle_bucket_window_list=$LIFECYCLE_BUCKET_WINDOWS lifecycle_bucket_promotion_window=$LIFECYCLE_BUCKET_PROMOTION_WINDOW force_lifecycle_bucket_windows=$FORCE_LIFECYCLE_BUCKET_WINDOWS force_deep_audits=$FORCE_DEEP_AUDITS force_workorder_branch=$FORCE_WORKORDER_BRANCH runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE scalp_sim_auto_approval_control_tower=$RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER latency_classifier_recommendation=$RUN_LATENCY_CLASSIFIER_RECOMMENDATION tuning_performance_control_tower=$RUN_TUNING_PERFORMANCE_CONTROL_TOWER swing_lifecycle=$RUN_SWING_LIFECYCLE_AUDIT swing_strategy_discovery=$RUN_SWING_STRATEGY_DISCOVERY swing_lifecycle_matrix=$RUN_SWING_LIFECYCLE_MATRIX swing_lifecycle_bucket_discovery=$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY swing_ai_review_provider=$SWING_THRESHOLD_AI_REVIEW_PROVIDER swing_lifecycle_bucket_discovery_ai_provider=$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER pattern_lab_ai_review_provider=$PATTERN_LAB_AI_REVIEW_PROVIDER producer_gap_discovery_ai_provider=$PRODUCER_GAP_DISCOVERY_AI_PROVIDER stage_hook_workorder_discovery_ai_provider=$STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER pattern_labs=$RUN_PATTERN_LABS deepseek_swing_lab=$RUN_DEEPSEEK_SWING_LAB code_improvement_workorder=$BUILD_CODE_IMPROVEMENT_WORKORDER daily_ev=true runtime_approval_summary=true runtime_apply_gap_audit=true next_stage2_checklist=true finished_at=$finished_at"
wait_for_postclose_resources "verify_threshold_cycle_postclose_chain_final"
run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain --date "$TARGET_DATE"
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
