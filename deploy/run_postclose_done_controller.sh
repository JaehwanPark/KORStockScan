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
PREDECESSOR_TIMEOUT_SEC="${POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC:-43200}"
ALLOW_WRAPPER_RERUN="${POSTCLOSE_DONE_CONTROLLER_ALLOW_WRAPPER_RERUN:-true}"
RUN_CODEX="${POSTCLOSE_DONE_CONTROLLER_RUN_CODEX:-false}"
RUN_ENTRY_SETUP_REPLAY_FOLLOWUP="${POSTCLOSE_DONE_CONTROLLER_RUN_ENTRY_SETUP_REPLAY_FOLLOWUP:-true}"
ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC="${POSTCLOSE_DONE_CONTROLLER_ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC:-0}"
ENTRY_SETUP_REPLAY_ACTIVE_WAIT_SEC="${POSTCLOSE_DONE_CONTROLLER_ENTRY_SETUP_REPLAY_ACTIVE_WAIT_SEC:-3600}"
ENTRY_SETUP_REPLAY_ACTIVE_POLL_SEC="${POSTCLOSE_DONE_CONTROLLER_ENTRY_SETUP_REPLAY_ACTIVE_POLL_SEC:-15}"
CODEX_BATCH_SIZE="${POSTCLOSE_DONE_CONTROLLER_CODEX_BATCH_SIZE:-${POSTCLOSE_DONE_CONTROLLER_CODEX_MAX_ORDERS:-5}}"
CODEX_MODEL_POLICY="${POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL_POLICY:-credit_min}"
CODEX_MODEL="${POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL:-}"
CODEX_EFFORT="${POSTCLOSE_DONE_CONTROLLER_CODEX_EFFORT:-}"
CODEX_COMMIT="${POSTCLOSE_DONE_CONTROLLER_CODEX_COMMIT:-true}"
CODEX_AUTO_PUSH_MAIN="${POSTCLOSE_DONE_CONTROLLER_AUTO_PUSH_MAIN:-true}"
REQUIRE_CODEX_COMPLETED="${POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED:-false}"
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

env PYTHONPATH=. POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED=false "$VENV_PY" -m src.engine.automation.postclose_done_controller "${controller_args[@]}"

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

entry_setup_replay_followup_state() {
  local batch_report="$PROJECT_DIR/data/report/ai_entry_setup_paired_replay_batch/ai_entry_setup_paired_replay_batch_${TARGET_DATE}.json"
  "$VENV_PY" - "$PROJECT_DIR" "$TARGET_DATE" "$batch_report" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

project_dir = Path(sys.argv[1]).resolve()
target_date = sys.argv[2]
batch_path = Path(sys.argv[3])

try:
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
except Exception:
    print("retry_required:batch_missing_or_invalid")
    raise SystemExit(0)

if batch.get("target_date") != target_date:
    print("retry_required:batch_target_date_mismatch")
    raise SystemExit(0)
if batch.get("status") != "completed_offline_only":
    print(f"retry_required:batch_status_{batch.get('status') or 'missing'}")
    raise SystemExit(0)

candidate_ref = batch.get("krx_bounded_live_candidate")
if candidate_ref is None:
    print("terminal_ready:no_krx_candidate")
    raise SystemExit(0)
if not isinstance(candidate_ref, dict):
    print("retry_required:candidate_reference_invalid")
    raise SystemExit(0)

candidate_path_raw = candidate_ref.get("path")
if not isinstance(candidate_path_raw, str) or not candidate_path_raw.strip():
    print("retry_required:candidate_path_missing")
    raise SystemExit(0)
candidate_path = Path(candidate_path_raw)
if not candidate_path.is_absolute():
    candidate_path = project_dir / candidate_path
expected_candidate_path = (
    project_dir
    / "data"
    / "threshold_cycle"
    / "bounded_live_candidates"
    / f"entry_setup_v2_14_bounded_live_candidate_{target_date}.json"
)
if candidate_path.resolve() != expected_candidate_path.resolve():
    print("retry_required:candidate_path_mismatch")
    raise SystemExit(0)
try:
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
except Exception:
    print("retry_required:candidate_missing_or_invalid")
    raise SystemExit(0)

declared_artifact_sha256 = candidate.get("artifact_sha256")
candidate_without_hash = {
    key: value for key, value in candidate.items() if key != "artifact_sha256"
}
computed_artifact_sha256 = hashlib.sha256(
    json.dumps(
        candidate_without_hash,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
).hexdigest()
if declared_artifact_sha256 != computed_artifact_sha256:
    print("retry_required:candidate_artifact_self_hash_mismatch")
    raise SystemExit(0)

if candidate.get("source_date") != target_date:
    print("retry_required:candidate_source_date_mismatch")
    raise SystemExit(0)
if candidate.get("status") != candidate_ref.get("status"):
    print("retry_required:candidate_status_mismatch")
    raise SystemExit(0)
if candidate.get("effective_date") != candidate_ref.get("effective_date"):
    print("retry_required:candidate_effective_date_mismatch")
    raise SystemExit(0)
if candidate.get("effective_date_policy") != "first_available_krx_preopen_v1":
    print("retry_required:candidate_effective_date_policy_mismatch")
    raise SystemExit(0)
if candidate.get("preopen_candidate_cutoff_kst") != "07:35:00":
    print("retry_required:candidate_preopen_cutoff_mismatch")
    raise SystemExit(0)
candidate_contract_sha256 = candidate.get("candidate_contract_sha256")
if not isinstance(candidate_contract_sha256, str) or len(candidate_contract_sha256) != 64:
    print("retry_required:candidate_contract_hash_missing_or_invalid")
    raise SystemExit(0)
if candidate.get("artifact_sha256") != candidate_ref.get("artifact_sha256"):
    print("retry_required:candidate_hash_mismatch")
    raise SystemExit(0)
print("terminal_ready:validated_batch_and_candidate")
PY
}

run_entry_setup_replay_followup() {
  if [[ "$RUN_ENTRY_SETUP_REPLAY_FOLLOWUP" != "1" && "$RUN_ENTRY_SETUP_REPLAY_FOLLOWUP" != "true" ]]; then
    echo "[SKIP] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=disabled"
    return 0
  fi
  if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
    echo "[SKIP] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=controller_dry_run"
    return 0
  fi
  if [[ "$controller_status" != "done" ]]; then
    echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=controller_not_done controller_status=${controller_status}" >&2
    return 1
  fi
  if ! [[ "$ENTRY_SETUP_REPLAY_ACTIVE_WAIT_SEC" =~ ^[0-9]+$ ]] || ! [[ "$ENTRY_SETUP_REPLAY_ACTIVE_POLL_SEC" =~ ^[1-9][0-9]*$ ]]; then
    echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=invalid_active_wait_config" >&2
    return 2
  fi

  local maturity_epoch now_epoch followup_state runner_path runner_rc lock_path active_wait_started_at
  if ! maturity_epoch="$(TZ=Asia/Seoul date -d "${TARGET_DATE} 21:05:00" +%s)"; then
    echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=invalid_maturity_date" >&2
    return 2
  fi
  now_epoch="$(TZ=Asia/Seoul date +%s)"
  if ((now_epoch < maturity_epoch)); then
    echo "[SKIP] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=awaiting_fixed_2105_trigger"
    return 0
  fi

  followup_state="$(entry_setup_replay_followup_state)"
  if [[ "$followup_state" == terminal_ready:* ]]; then
    echo "[SKIP] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=${followup_state}"
    return 0
  fi

  lock_path="$PROJECT_DIR/tmp/ai_entry_setup_paired_replay_${TARGET_DATE}.lock"
  mkdir -p "$PROJECT_DIR/tmp"
  active_wait_started_at="$now_epoch"
  while ! flock -n "$lock_path" -c true; do
    followup_state="$(entry_setup_replay_followup_state)"
    if [[ "$followup_state" == terminal_ready:* ]]; then
      echo "[SKIP] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=${followup_state} owner=active_fixed_runner"
      return 0
    fi
    now_epoch="$(TZ=Asia/Seoul date +%s)"
    if ((now_epoch - active_wait_started_at >= ENTRY_SETUP_REPLAY_ACTIVE_WAIT_SEC)); then
      echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=active_runner_timeout state=${followup_state}" >&2
      return 1
    fi
    echo "[WAIT] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=active_fixed_runner state=${followup_state}"
    sleep "$ENTRY_SETUP_REPLAY_ACTIVE_POLL_SEC"
  done

  runner_path="$PROJECT_DIR/deploy/run_ai_entry_setup_paired_replay_postclose.sh"
  if [[ ! -x "$runner_path" ]]; then
    echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=runner_missing_or_not_executable path=${runner_path}" >&2
    return 2
  fi
  echo "[START] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=${followup_state} predecessor_wait_sec=${ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC}"
  runner_rc=0
  AI_ENTRY_SETUP_REPLAY_PREDECESSOR_WAIT_SEC="$ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC" \
    "$runner_path" "$TARGET_DATE" || runner_rc=$?
  if [[ "$runner_rc" -ne 0 ]]; then
    echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} exit_code=${runner_rc}" >&2
    return "$runner_rc"
  fi

  followup_state="$(entry_setup_replay_followup_state)"
  if [[ "$followup_state" != terminal_ready:* ]]; then
    echo "[FAIL] ai_entry_setup_replay_followup target_date=${TARGET_DATE} reason=nonterminal_after_runner state=${followup_state}" >&2
    return 1
  fi
  echo "[DONE] ai_entry_setup_replay_followup target_date=${TARGET_DATE} state=${followup_state}"
}

run_entry_setup_replay_followup

if [[ "$RUN_CODEX" == "1" || "$RUN_CODEX" == "true" ]]; then
  if [[ "$controller_status" != "done" && "$controller_status" != "dry_run_planned" ]]; then
    echo "[SKIP] codex_workorder_runner target_date=${TARGET_DATE} controller_status=${controller_status}"
    exit 1
  fi
  codex_args=(--date "$TARGET_DATE" --max-orders "$CODEX_BATCH_SIZE" --model-policy "$CODEX_MODEL_POLICY")
  if [[ -n "$CODEX_MODEL" ]]; then
    codex_args+=(--model "$CODEX_MODEL")
  fi
  if [[ -n "$CODEX_EFFORT" ]]; then
    codex_args+=(--effort "$CODEX_EFFORT")
  fi
  if [[ "$CODEX_COMMIT" == "1" || "$CODEX_COMMIT" == "true" ]]; then
    codex_args+=(--commit)
  else
    codex_args+=(--no-commit)
  fi
  if [[ "$CODEX_AUTO_PUSH_MAIN" == "1" || "$CODEX_AUTO_PUSH_MAIN" == "true" ]]; then
    codex_args+=(--auto-push-main)
  else
    codex_args+=(--no-auto-push-main)
  fi
  if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
    codex_args+=(--dry-run)
  fi
  codex_rc=0
  env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.codex_workorder_runner "${codex_args[@]}" || codex_rc=$?
  codex_report="$PROJECT_DIR/data/report/codex_workorder_runner/codex_workorder_runner_${TARGET_DATE}.json"
  codex_status="$("$VENV_PY" - "$codex_report" <<'PY'
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
  if [[ "$codex_rc" -ne 0 ]]; then
    echo "[FAIL] codex_workorder_runner target_date=${TARGET_DATE} status=${codex_status} exit_code=${codex_rc}" >&2
    exit "$codex_rc"
  fi
  if [[ "$codex_status" != "completed" && "$codex_status" != "dry_run_planned" ]]; then
    echo "[FAIL] codex_workorder_runner target_date=${TARGET_DATE} status=${codex_status} strict_completion_required=true" >&2
    exit 1
  fi
  if [[ "$REQUIRE_CODEX_COMPLETED" == "1" || "$REQUIRE_CODEX_COMPLETED" == "true" ]]; then
    env PYTHONPATH=. "$VENV_PY" -m src.engine.automation.postclose_done_controller "${controller_args[@]}" --require-codex-completed
  fi
else
  echo "[SKIP] codex_workorder_runner target_date=${TARGET_DATE} reason=disabled_by_default set_POSTCLOSE_DONE_CONTROLLER_RUN_CODEX=true_to_opt_in"
fi

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] postclose_done_controller target_date=${TARGET_DATE} finished_at=${finished_at}"
