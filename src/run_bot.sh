#!/bin/bash

THRESHOLD_RUNTIME_ENV_WAIT_SEC="${KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_WAIT_SEC:-1800}"
THRESHOLD_RUNTIME_ENV_REQUIRED="${KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_REQUIRED:-true}"
THRESHOLD_RUNTIME_ENV_BOOTSTRAP="${KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_BOOTSTRAP:-true}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHER_SOURCE_LOADED_AT_KST="$(TZ=Asia/Seoul date --iso-8601=seconds)"
LAUNCHER_SOURCE_GIT_COMMIT="$(
    git -C "$PROJECT_DIR" rev-parse --verify HEAD 2>/dev/null || true
)"
if [ -z "$LAUNCHER_SOURCE_GIT_COMMIT" ]; then
    LAUNCHER_SOURCE_GIT_COMMIT="unknown"
fi
if command -v sha256sum >/dev/null 2>&1; then
    LAUNCHER_SOURCE_RUN_BOT_SHA256="$(
        sha256sum "${BASH_SOURCE[0]}" 2>/dev/null | awk '{print $1}'
    )"
else
    LAUNCHER_SOURCE_RUN_BOT_SHA256="unknown"
fi
if [ -z "$LAUNCHER_SOURCE_RUN_BOT_SHA256" ]; then
    LAUNCHER_SOURCE_RUN_BOT_SHA256="unknown"
fi
readonly LAUNCHER_SOURCE_LOADED_AT_KST
readonly LAUNCHER_SOURCE_GIT_COMMIT
readonly LAUNCHER_SOURCE_RUN_BOT_SHA256
# shellcheck source=../deploy/cpu_affinity_profile.sh
. "$PROJECT_DIR/deploy/cpu_affinity_profile.sh"
DEFAULT_BOT_CPU_AFFINITY="$(korstockscan_default_cpu_affinity bot)"
# Opaque digest namespace only. Every native policy/PID check still runs.
VALIDATION_SESSION_ID="${KORSTOCKSCAN_VALIDATION_SESSION_ID:-$(tr -d '-' </proc/sys/kernel/random/uuid)}"
if [[ ! "$VALIDATION_SESSION_ID" =~ ^[0-9a-f]{32}$ ]]; then
    echo "invalid validation session identity" >&2
    exit 1
fi
unset KORSTOCKSCAN_VALIDATION_SESSION_ID

wait_for_threshold_runtime_env() {
    local env_path="$1"
    local waited=0
    if [ "$THRESHOLD_RUNTIME_ENV_REQUIRED" != "true" ] && [ "$THRESHOLD_RUNTIME_ENV_REQUIRED" != "1" ]; then
        return 0
    fi
    if [ ! -f "$env_path" ] && { [ "$THRESHOLD_RUNTIME_ENV_BOOTSTRAP" = "true" ] || [ "$THRESHOLD_RUNTIME_ENV_BOOTSTRAP" = "1" ]; }; then
        echo "🧭 threshold runtime env 생성 시도: $env_path"
        (
            cd ..
            THRESHOLD_CYCLE_APPLY_MODE="${THRESHOLD_CYCLE_APPLY_MODE:-auto_bounded_live}" \
            THRESHOLD_CYCLE_AUTO_APPLY="${THRESHOLD_CYCLE_AUTO_APPLY:-true}" \
            THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI="${THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI:-true}" \
            ./deploy/run_threshold_cycle_preopen.sh "$(TZ=Asia/Seoul date +%F)"
        )
    fi
    while [ ! -f "$env_path" ]; do
        if [ "$waited" -ge "$THRESHOLD_RUNTIME_ENV_WAIT_SEC" ]; then
            echo "❌ threshold runtime env 미생성으로 봇 기동 중단: $env_path (waited=${waited}s)"
            return 1
        fi
        if [ "$waited" -eq 0 ]; then
            echo "⏳ threshold runtime env 대기: $env_path"
        fi
        sleep 5
        waited=$((waited + 5))
    done
    return 0
}

verify_threshold_runtime_env_handoff() {
    local target_date="$1"
    local verify_output
    if ! verify_output="$(
        PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.runtime_policy_bootstrap \
            --verify --target-date "$target_date" --validation-session "$VALIDATION_SESSION_ID" 2>&1
    )"; then
        echo "❌ threshold runtime env handoff 검증 실패: target_date=$target_date"
        printf '%s\n' "$verify_output"
        return 1
    fi
    echo "✅ threshold runtime env handoff 검증 통과: target_date=$target_date"
}

verify_exact_preopen_completion() {
    local target_date="$1"
    PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.next_preopen_readiness \
        --verify-completion --target-date "$target_date" \
        --selected-release-commit "$LAUNCHER_SOURCE_GIT_COMMIT"
}

record_threshold_runtime_env_pid_handoff() {
    local target_date="$1"
    local bot_pid="$2"
    local verify_output
    if ! verify_output="$(
        PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.runtime_policy_bootstrap \
            --verify --target-date "$target_date" --pid "$bot_pid" \
            --write-verify-artifact --validation-session "$VALIDATION_SESSION_ID" 2>&1
    )"; then
        echo "⚠️ threshold runtime env PID 소비 receipt 기록 실패: target_date=$target_date pid=$bot_pid"
        printf '%s\n' "$verify_output"
        return 1
    fi
    PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.intraday_release_handoff \
        --consume --target-date "$target_date" --pid "$bot_pid" --validation-session "$VALIDATION_SESSION_ID" || return 1
    PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.intraday_release_handoff \
        --verify --target-date "$target_date" --pid "$bot_pid" --validation-session "$VALIDATION_SESSION_ID" || return 1
    echo "✅ threshold runtime env PID 소비 receipt 기록: target_date=$target_date pid=$bot_pid"
}

. "$PROJECT_DIR/src/engine/infrastructure/main_policy_environment.sh"

export_runtime_source_provenance() {
    local commit source_dirty source_status
    # A tmux supervisor may inherit another immutable release's import path.
    # Bind imports to the same source root as the child and its receipt.
    export PYTHONPATH="$PROJECT_DIR"
    commit="$(git -C "$PROJECT_DIR" rev-parse --verify HEAD 2>/dev/null || true)"
    if [ -z "$commit" ]; then
        commit="unknown"
    fi
    source_dirty="unknown"
    if source_status="$(git -C "$PROJECT_DIR" status --porcelain --untracked-files=normal -- src deploy 2>/dev/null)"; then
        source_dirty="false"
    fi
    if [ -n "${source_status:-}" ]; then
        source_dirty="true"
    fi
    export KORSTOCKSCAN_RUNTIME_GIT_COMMIT="$commit"
    export KORSTOCKSCAN_RUNTIME_LAUNCHER_GIT_COMMIT="$LAUNCHER_SOURCE_GIT_COMMIT"
    export KORSTOCKSCAN_RUNTIME_LAUNCHER_RUN_BOT_SHA256="$LAUNCHER_SOURCE_RUN_BOT_SHA256"
    export KORSTOCKSCAN_RUNTIME_LAUNCHER_LOADED_AT_KST="$LAUNCHER_SOURCE_LOADED_AT_KST"
    export KORSTOCKSCAN_RUNTIME_SOURCE_ROOT="$PROJECT_DIR"
    export KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY="$source_dirty"
    export KORSTOCKSCAN_RUNTIME_STARTED_AT_KST="$(TZ=Asia/Seoul date --iso-8601=seconds)"
    echo "📌 runtime source provenance: commit=$commit launcher_commit=$KORSTOCKSCAN_RUNTIME_LAUNCHER_GIT_COMMIT launcher_sha256=$KORSTOCKSCAN_RUNTIME_LAUNCHER_RUN_BOT_SHA256 launcher_loaded_at=$KORSTOCKSCAN_RUNTIME_LAUNCHER_LOADED_AT_KST source_root=$PROJECT_DIR source_dirty=$source_dirty started_at=$KORSTOCKSCAN_RUNTIME_STARTED_AT_KST"
}

# 무한 루프 시작
while true; do
    if [ -e "$PROJECT_DIR/data/runtime/operator_startup_hold.json" ] || [ -L "$PROJECT_DIR/data/runtime/operator_startup_hold.json" ]; then
        echo "[BLOCK] operator_postclose_startup_hold_active"
        exit 75
    fi
    echo "🚀 KORStockScan 스나이퍼 엔진을 시작합니다..."

    apply_main_policy_defaults
    RUNTIME_TARGET_DATE="$(TZ=Asia/Seoul date +%F)"
    THRESHOLD_RUNTIME_ENV="../data/runtime/policy_bootstrap/runtime_policy_bootstrap_${RUNTIME_TARGET_DATE}.env"
    wait_for_threshold_runtime_env "$THRESHOLD_RUNTIME_ENV" || exit 1
    if [ "$RUNTIME_TARGET_DATE" \> "2026-10-01" ]; then
        verify_exact_preopen_completion "$RUNTIME_TARGET_DATE" || exit 1
    fi
    apply_main_policy_handoff "$RUNTIME_TARGET_DATE" "$THRESHOLD_RUNTIME_ENV" || exit 1
    verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE" || exit 1
    PYTHONPATH=.. ../.venv/bin/python -m src.engine.scalping.mechanistic_entry_runtime_policy \
        --validate-current --target-date "$RUNTIME_TARGET_DATE" --data-root ../data || exit 1
    PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.auxiliary_reader_readiness \
        --target-date "$RUNTIME_TARGET_DATE" --data-root ../data || exit 1
    apply_main_policy_final_environment
    export_runtime_source_provenance

    # 봇 실행 (경로나 파일명은 환경에 맞게 수정)
    BOT_CPU_AFFINITY="${KORSTOCKSCAN_BOT_CPU_AFFINITY:-$DEFAULT_BOT_CPU_AFFINITY}"
    cmd=(../.venv/bin/python bot_main.py)
    if command -v taskset >/dev/null 2>&1 && [ -n "$BOT_CPU_AFFINITY" ] && [ "$(korstockscan_nproc)" -gt 1 ]; then
        cmd=(taskset -c "$BOT_CPU_AFFINITY" "${cmd[@]}")
    fi
    "${cmd[@]}" &
    BOT_PID=$!
    # The pre-start verifier proves the frozen bootstrap.  Re-run the same
    # verifier against the actual child so later postclose acceptance cannot
    # confuse a generated policy file with PID consumption.
    # The tmux supervisor is not the trading process.  Attest the actual bot
    # child only after native policy consumption binds to that same identity.
    # A failed receipt cannot attest deployment success or authorize a kill.
    if record_threshold_runtime_env_pid_handoff "$RUNTIME_TARGET_DATE" "$BOT_PID"; then
        RUNTIME_WORKSPACE="$(dirname "$(readlink -f "$PROJECT_DIR/data")")"
        if ! ../.venv/bin/python -I "$PROJECT_DIR/src/engine/infrastructure/runtime_release_router.py" \
            --workspace "$RUNTIME_WORKSPACE" \
            --record-pid "$BOT_PID" \
            --record-release-root "$PROJECT_DIR" \
            --record-git-commit "$KORSTOCKSCAN_RUNTIME_GIT_COMMIT"; then
            echo "⚠️ runtime PID 소비 receipt 기록 실패: pid=$BOT_PID release=$PROJECT_DIR"
        fi
    else
        echo "⚠️ native PID 소비 검증 실패: selector 성공 기록 생략 pid=$BOT_PID release=$PROJECT_DIR"
    fi
    wait "$BOT_PID"

    echo "🛑 봇 프로세스가 종료되었습니다."
    echo "⏳ 5초 후 엔진을 재가동합니다. (완전 종료를 원하면 지금 Ctrl+C를 누르세요)"
    sleep 5
done

# 깃허브 연동 테스트
