#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
MAX_ITERATIONS="${THRESHOLD_CYCLE_MAX_ITERATIONS:-80}"
MAX_INPUT_LINES="${THRESHOLD_CYCLE_MAX_INPUT_LINES_PER_CHUNK:-20000}"
MAX_OUTPUT_LINES="${THRESHOLD_CYCLE_MAX_OUTPUT_LINES_PER_PARTITION:-25000}"
MAX_CPU_BUSY_PCT="${THRESHOLD_CYCLE_MAX_CPU_BUSY_PCT:-95}"
SKIP_DB="${THRESHOLD_CYCLE_SKIP_DB:-false}"
USE_SNAPSHOT="${THRESHOLD_CYCLE_USE_SNAPSHOT:-true}"
AI_CORRECTION_PROVIDER="${THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER:-openai}"
AI_CORRECTION_RESPONSE_JSON="${THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON:-}"
RUN_PATTERN_LABS="${THRESHOLD_CYCLE_RUN_PATTERN_LABS:-true}"
PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-2026-04-21}"
RUN_SWING_LIFECYCLE_AUDIT="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_AUDIT:-true}"
SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-openai}"
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
RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}"
RUN_PATTERN_LAB_PROPAGATION_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}"
RUN_PLAN_REBASE_DAILY_RENEWAL="${THRESHOLD_CYCLE_RUN_PLAN_REBASE_DAILY_RENEWAL:-true}"
SNAPSHOT_RETENTION_DAYS="${THRESHOLD_CYCLE_SNAPSHOT_RETENTION_DAYS:-7}"
ARTIFACT_WAIT_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC:-600}"
ARTIFACT_WAIT_INTERVAL_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_INTERVAL_SEC:-5}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] threshold-cycle postclose target_date=$TARGET_DATE failed_at=$failed_at"' ERR

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] threshold-cycle postclose target_date=$TARGET_DATE max_iterations=$MAX_ITERATIONS started_at=$started_at"

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

run_threshold_cycle_ev_and_wait() {
  local pass_label="$1"

  PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_ev_report --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/threshold_cycle_ev/threshold_cycle_ev_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/threshold_cycle_ev/threshold_cycle_ev_${TARGET_DATE}.md" \
    "threshold_cycle_ev_${pass_label}"
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

for i in $(seq 1 "$MAX_ITERATIONS"); do
  resume_args=(--resume)
  if [ "$i" = "1" ] && [ "$USE_SNAPSHOT" = "true" ] && [ "${REUSE_EXISTING_SNAPSHOT:-false}" != "true" ]; then
    resume_args=(--overwrite)
  fi
  out="$(
    PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events \
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
    echo "[threshold-cycle] availability guard paused target_date=$TARGET_DATE reason=$paused_reason"
    break
  fi
  sleep 1
done

if [ "${completed:-false}" != "true" ]; then
  echo "[threshold-cycle] compact collection incomplete target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-}" >&2
  failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"
  if [ "${status:-}" = "paused_by_availability_guard" ]; then
    echo "[PAUSED] threshold-cycle postclose target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-} failed_at=$failed_at"
  fi
  echo "[FAIL] threshold-cycle postclose target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-} failed_at=$failed_at"
  exit 2
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
  PYTHONPATH=. "$VENV_PY" -m src.engine.openai_ws_stability_report \
    --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/openai_ws/openai_ws_stability_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/openai_ws/openai_ws_stability_${TARGET_DATE}.md" \
    "openai_ws_stability_postclose"
fi

report_args=(--date "$TARGET_DATE")
if [ "$SKIP_DB" = "true" ]; then
  report_args+=(--skip-db)
fi
if [ -n "$AI_CORRECTION_RESPONSE_JSON" ]; then
  report_args+=(--ai-correction-response-json "$AI_CORRECTION_RESPONSE_JSON")
else
  report_args+=(--ai-correction-provider "$AI_CORRECTION_PROVIDER")
fi

PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report \
  --calibration-run-phase postclose \
  "${report_args[@]}"
wait_for_json_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_${TARGET_DATE}.json" \
  "threshold_cycle_postclose_report"
wait_for_json_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_calibration/threshold_cycle_calibration_${TARGET_DATE}_postclose.json" \
  "threshold_cycle_calibration_postclose"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_${TARGET_DATE}_postclose.json" \
  "$PROJECT_DIR/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_${TARGET_DATE}_postclose.md" \
  "threshold_cycle_ai_review_postclose"
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
  bash "$PROJECT_DIR/deploy/run_swing_daily_simulation_report.sh" "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.md" \
    "swing_daily_simulation"
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit \
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
  ANALYSIS_START_DATE="$TARGET_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    bash "$PROJECT_DIR/analysis/deepseek_swing_pattern_lab/run_all.sh" "$TARGET_DATE" || \
    echo "[threshold-cycle] deepseek swing pattern lab failed (non-fatal)" >&2
fi
if [ "$RUN_PATTERN_LABS" = "true" ] || [ "$RUN_PATTERN_LABS" = "1" ]; then
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    "$PROJECT_DIR/analysis/gemini_scalping_pattern_lab/run.sh" || \
    echo "[threshold-cycle] gemini scalping pattern lab failed (non-fatal); downstream automation will mark freshness=false" >&2
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    "$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh" || \
    echo "[threshold-cycle] claude scalping pattern lab failed (non-fatal); downstream automation will mark freshness=false" >&2
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.scalping_pattern_lab_automation --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_${TARGET_DATE}.md" \
  "scalping_pattern_lab_automation"
PYTHONPATH=. "$VENV_PY" -m src.engine.swing_pattern_lab_automation --date "$TARGET_DATE" || \
  echo "[threshold-cycle] swing pattern lab automation failed (non-fatal)" >&2
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_${TARGET_DATE}.md" \
  "swing_pattern_lab_automation"
if [ "$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" = "true" ] || [ "$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_currentness_audit --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.md" \
    "pattern_lab_currentness_audit"
fi
if [ "$RUN_PIPELINE_EVENT_VERBOSITY_REPORT" = "true" ] || [ "$RUN_PIPELINE_EVENT_VERBOSITY_REPORT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.pipeline_event_verbosity_report --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/pipeline_event_verbosity/pipeline_event_verbosity_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/pipeline_event_verbosity/pipeline_event_verbosity_${TARGET_DATE}.md" \
    "pipeline_event_verbosity"
fi
if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "true" ] || [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.observation_source_quality_audit --target-date "$TARGET_DATE" --write
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/observation_source_quality_audit/observation_source_quality_audit_${TARGET_DATE}.md" \
    "observation_source_quality_audit"
fi
if [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" = "true" ] || [ "$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.codebase_performance_workorder_report --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/codebase_performance_workorder/codebase_performance_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/codebase_performance_workorder/codebase_performance_workorder_${TARGET_DATE}.md" \
    "codebase_performance_workorder"
fi
run_threshold_cycle_ev_and_wait "pre_workorder"
if [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "true" ] || [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.build_code_improvement_workorder \
    --date "$TARGET_DATE" \
    --max-orders "$CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json" \
    "$PROJECT_DIR/docs/code-improvement-workorders/code_improvement_workorder_${TARGET_DATE}.md" \
    "code_improvement_workorder"
fi
run_threshold_cycle_ev_and_wait "post_workorder_refresh"
if [ "$RUN_PATTERN_LAB_PROPAGATION_AUDIT" = "true" ] || [ "$RUN_PATTERN_LAB_PROPAGATION_AUDIT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.pattern_lab_propagation_audit --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.md" \
    "pattern_lab_propagation_audit"
  run_threshold_cycle_ev_and_wait "post_propagation_audit_refresh"
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_approval_summary --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.md" \
  "runtime_approval_summary"
if [ "$RUN_PLAN_REBASE_DAILY_RENEWAL" = "true" ] || [ "$RUN_PLAN_REBASE_DAILY_RENEWAL" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.plan_rebase_daily_renewal --date "$TARGET_DATE"
  wait_for_report_artifact \
    "$PROJECT_DIR/data/report/plan_rebase_daily_renewal/plan_rebase_daily_renewal_${TARGET_DATE}.json" \
    "$PROJECT_DIR/data/report/plan_rebase_daily_renewal/plan_rebase_daily_renewal_${TARGET_DATE}.md" \
    "plan_rebase_daily_renewal"
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.build_next_stage2_checklist --source-date "$TARGET_DATE"
wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist"
PYTHONPATH=. "$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain --date "$TARGET_DATE"
wait_for_report_artifact \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json" \
  "$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.md" \
  "threshold_cycle_postclose_verification"
PYTHONPATH=. "$VENV_PY" -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500 >/dev/null
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] threshold-cycle postclose target_date=$TARGET_DATE ai_correction_provider=$AI_CORRECTION_PROVIDER panic_sell_defense=$RUN_PANIC_SELL_DEFENSE_REPORT panic_buying=$RUN_PANIC_BUYING_REPORT market_panic_breadth=$RUN_MARKET_PANIC_BREADTH_REPORT openai_ws_stability=$RUN_OPENAI_WS_STABILITY_REPORT pipeline_event_verbosity=$RUN_PIPELINE_EVENT_VERBOSITY_REPORT observation_source_quality_audit=$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT codebase_performance_workorder=$RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT pattern_lab_currentness_audit=$RUN_PATTERN_LAB_CURRENTNESS_AUDIT pattern_lab_propagation_audit=$RUN_PATTERN_LAB_PROPAGATION_AUDIT plan_rebase_daily_renewal=$RUN_PLAN_REBASE_DAILY_RENEWAL swing_lifecycle=$RUN_SWING_LIFECYCLE_AUDIT swing_ai_review_provider=$SWING_THRESHOLD_AI_REVIEW_PROVIDER pattern_labs=$RUN_PATTERN_LABS deepseek_swing_lab=$RUN_DEEPSEEK_SWING_LAB code_improvement_workorder=$BUILD_CODE_IMPROVEMENT_WORKORDER daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=$finished_at"
