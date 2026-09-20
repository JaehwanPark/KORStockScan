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
            --verify --target-date "$target_date" 2>&1
    )"; then
        echo "❌ threshold runtime env handoff 검증 실패: target_date=$target_date"
        printf '%s\n' "$verify_output"
        return 1
    fi
    echo "✅ threshold runtime env handoff 검증 통과: target_date=$target_date"
}

record_threshold_runtime_env_pid_handoff() {
    local target_date="$1"
    local bot_pid="$2"
    local verify_output
    if ! verify_output="$(
        PYTHONPATH=.. ../.venv/bin/python -m src.engine.automation.runtime_policy_bootstrap \
            --verify --target-date "$target_date" --pid "$bot_pid" 2>&1
    )"; then
        echo "⚠️ threshold runtime env PID 소비 receipt 기록 실패: target_date=$target_date pid=$bot_pid"
        printf '%s\n' "$verify_output"
        return 1
    fi
    echo "✅ threshold runtime env PID 소비 receipt 기록: target_date=$target_date pid=$bot_pid"
}

apply_retired_runtime_policy_env() {
    local retirement_commands
    if ! retirement_commands="$(
        PYTHONPATH=.. ../.venv/bin/python \
            -m src.engine.lifecycle.retirement --shell-commands
    )"; then
        echo "❌ retired runtime OFF env 생성 실패"
        return 1
    fi
    eval "$retirement_commands"
    echo "📌 retired runtime namespace OFF 재적용 완료"
}

apply_authoritative_ai_context_promotion() {
    local target_date="$1"
    local promotion_exports
    if ! promotion_exports="$(
        PYTHONPATH=.. ../.venv/bin/python \
            -m src.engine.automation.ai_multi_timeframe_context_promotion \
            --date "$target_date" --mode runtime-env-exports
    )"; then
        echo "❌ committed AI context promotion env 검증 실패: target_date=$target_date"
        printf '%s\n' "$promotion_exports"
        return 1
    fi
    if [ -z "$promotion_exports" ]; then
        return 0
    fi
    eval "$promotion_exports"
    echo "📌 AI context authority overlay 최종 적용: target_date=$target_date (promotion or fail-closed context rollback)"
}

export_runtime_source_provenance() {
    local commit source_dirty source_status
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

reset_runtime_policy_env_before_handoff() {
    # Intraday authority must be re-sourced explicitly for this startup/date.
    # Never inherit yesterday's pinned exception from the long-lived shell.
    unset KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_PATH
    unset KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_SHA256
    # Persistent rollout is reloaded from the current operator handoff; deletion
    # must not leave a stale pin in this long-lived supervisor.
    unset KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH
    unset KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_SHA256
    # V2.15+ promotion authority is also reloaded only from the current
    # immutable operator handoff; never inherit a prior supervisor generation.
    unset KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH
    unset KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_SHA256
    # The supervisor is long-lived across graceful child restarts. Clear
    # startup-retired authority before loading the reviewed PREOPEN/operator
    # handoff; the verifier must reject any sourced layer that restores it.
    unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS
    unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED
    unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE
    unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION
    unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_TIMEOUT_SEC
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_SLIPPAGE_BPS
    unset KORSTOCKSCAN_ENTRY_SPLIT_PROBE_ANCHOR_MODE
    unset KORSTOCKSCAN_NXT_RISING_MISSED_PARTIAL_FILL_REPRICE_ENABLED
    unset KORSTOCKSCAN_NXT_RISING_MISSED_PARTIAL_FILL_REPRICE_ACTIVE_DATE
    unset KORSTOCKSCAN_NXT_RISING_MISSED_TP1_CONTEXT_REFRESH_ENABLED
    unset KORSTOCKSCAN_NXT_RISING_MISSED_TP1_CONTEXT_REFRESH_ACTIVE_DATE
    unset KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_REST_FALLBACK_ENABLED
    unset KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_REST_FALLBACK_ACTIVE_DATE
    unset KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_ENABLED
    unset KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_FILE
    unset KORSTOCKSCAN_SCALE_IN_SPLIT_ORDER_POLICY_VERSION
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ACTIVE_DATE
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_KRX_ENABLED
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_NXT_ENABLED
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_PREMARKET_ENABLED
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_CENTRAL_SIZING_KRX_ENABLED
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_CENTRAL_SIZING_NXT_ENABLED
    unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_CENTRAL_SIZING_PREMARKET_ENABLED
    unset KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_ENABLED
    unset KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_FILE
    unset KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_VERSION
    unset KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_SOURCE_DATE
    unset KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_SHA256
    unset KORSTOCKSCAN_KRX_AFTERMARKET_SOR_POLICY_ACTIVE_DATE
}

# 무한 루프 시작
while true; do
    echo "🚀 KORStockScan 스나이퍼 엔진을 시작합니다..."

    # Parser-compatibility bounds only. Runtime sizing authority is the central
    # five-tier allocator (10/15/20/25/25%, absolute cap 25%).
    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN=0.10
    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX=0.25
    export KORSTOCKSCAN_SCALPING_MAX_BUY_BUDGET_KRW=0
    export KORSTOCKSCAN_SCALPING_MIN_ONE_SHARE_FLOOR_ENABLED=true
    export KORSTOCKSCAN_SCALPING_SCALE_IN_MIN_ONE_SHARE_FLOOR_ENABLED=true
    export KORSTOCKSCAN_SCALPING_ENTRY_PRICE_DEFENSE_MODE=percent_bps
    export KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS=25
    export KORSTOCKSCAN_SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS=10
    export KORSTOCKSCAN_SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS=15
    export KORSTOCKSCAN_SCALPING_NORMAL_WEAK_DEFENSIVE_BPS=40
    export KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_EXIT_ENABLED=true
    export KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_PROFIT_PCT=1.0
    export KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_SEC=180
    export KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MAX_PROFIT_MOVE_PCT=0.15
    export KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MAX_PEAK_IMPROVE_PCT=0.10
    export KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_MIN_AI_SCORE=45
    export KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_HARD_EXIT_ENABLED=true
    export KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT=0.20
    export KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MAX_ADJUSTED_PROFIT_PCT=1.00
    export KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC=1800
    export KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_ASSUMED_EXIT_SLIPPAGE_BPS=15
    # Persistent source-observation policy. Daily threshold env generation does
    # not own this lane; an explicit operator/daily override may still set it
    # false as the documented rollback.
    export KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws
    export KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true
    export KORSTOCKSCAN_OPENAI_RESPONSES_WS_POOL_SIZE=2
    export KORSTOCKSCAN_OPENAI_RESPONSES_WS_TIMEOUT_MS=15000
    export KORSTOCKSCAN_OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512
    export KORSTOCKSCAN_OPENAI_REASONING_EFFORT=auto
    export KORSTOCKSCAN_OPENAI_HOLDING_SCORE_MODEL=gpt-5.4-nano
    export KORSTOCKSCAN_OPENAI_HOLDING_FLOW_MODEL=gpt-5.4-mini
    export KORSTOCKSCAN_OPENAI_HOLDING_FLOW_TIMEOUT_MS=15000
    export KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=holding_flow
    export KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY=lite_v2
    export KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000
    export KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=off
    export KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE=primary
    export KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY=qwen3_32b
    export KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY=lite_v2
    export KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_ENABLED=true
    export KORSTOCKSCAN_BEDROCK_QWEN3_32B_MODEL_ID=qwen.qwen3-32b-v1:0
    export KORSTOCKSCAN_BEDROCK_QWEN3_32B_REGION=us-west-2
    export KORSTOCKSCAN_BEDROCK_QWEN3_32B_TIMEOUT_MS=7000
    export KORSTOCKSCAN_BEDROCK_QWEN3_32B_MAX_OUTPUT_TOKENS=768
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_MODEL_ID=apac.amazon.nova-lite-v1:0
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_REGION=ap-northeast-2
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_WORKERS=1
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_QUEUE_MAX=200
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_TIMEOUT_MS=7000
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_SAMPLE_RATE=1.0
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_MAX_OUTPUT_TOKENS=768
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_PROMPT_CACHE_ENABLED=true
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MODEL_ID=global.amazon.nova-2-lite-v1:0
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_REGION=ap-northeast-2
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_WORKERS=1
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_QUEUE_MAX=200
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_TIMEOUT_MS=7000
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_SAMPLE_RATE=1.0
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_MAX_OUTPUT_TOKENS=768
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_PROMPT_CACHE_ENABLED=true
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_V2_TARGET_RUN_DATE=2026-05-26
    export KORSTOCKSCAN_BEDROCK_KEY_ROTATION_ENABLED=true
    export KORSTOCKSCAN_SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=true
    export KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_OPEN=10
    export KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_DAILY=30
    export KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1

    THRESHOLD_RUNTIME_ENV="../data/runtime/policy_bootstrap/runtime_policy_bootstrap_$(TZ=Asia/Seoul date +%F).env"
    wait_for_threshold_runtime_env "$THRESHOLD_RUNTIME_ENV" || exit 1
    reset_runtime_policy_env_before_handoff
    if [ -f "$THRESHOLD_RUNTIME_ENV" ]; then
        echo "📌 threshold runtime env 적용: $THRESHOLD_RUNTIME_ENV"
        set -a
        # shellcheck source=/dev/null
        . "$THRESHOLD_RUNTIME_ENV"
        set +a
    fi
    RUNTIME_TARGET_DATE="$(TZ=Asia/Seoul date +%F)"
    apply_authoritative_ai_context_promotion "$RUNTIME_TARGET_DATE" || exit 1
    # Load custody identity after every general runtime/operator layer so none
    # can silently replace the account/registry bound by the apply receipt.
    OWNER_CUSTODY_RUNTIME_ENV="../data/runtime/symbol_owner_policy/owner_custody.env"
    if [ -f "$OWNER_CUSTODY_RUNTIME_ENV" ]; then
        echo "📌 same-symbol owner custody env 적용: $OWNER_CUSTODY_RUNTIME_ENV"
        set -a
        # shellcheck source=/dev/null
        . "$OWNER_CUSTODY_RUNTIME_ENV"
        set +a
    fi
    apply_retired_runtime_policy_env || exit 1
    verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE" || exit 1
    # Reassert removed one-off namespaces after verification. bot_main also
    # normalizes every retired prefix before importing trading modules.
    unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS
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
    record_threshold_runtime_env_pid_handoff "$RUNTIME_TARGET_DATE" "$BOT_PID" || true
    # The tmux supervisor is not the trading process.  Attest the actual bot
    # child only after it has inherited this selected release's src cwd.  A
    # receipt failure is observable but must not turn a provenance write into
    # a bot/process or policy-control authority.
    RUNTIME_WORKSPACE="$(dirname "$(readlink -f "$PROJECT_DIR/data")")"
    if ! /bin/bash "$RUNTIME_WORKSPACE/deploy/run_runtime_release.sh" \
        --record-pid "$BOT_PID" \
        --record-release-root "$PROJECT_DIR" \
        --record-git-commit "$KORSTOCKSCAN_RUNTIME_GIT_COMMIT"; then
        echo "⚠️ runtime PID 소비 receipt 기록 실패: pid=$BOT_PID release=$PROJECT_DIR"
    fi
    wait "$BOT_PID"

    echo "🛑 봇 프로세스가 종료되었습니다."
    echo "⏳ 5초 후 엔진을 재가동합니다. (완전 종료를 원하면 지금 Ctrl+C를 누르세요)"
    sleep 5
done

# 깃허브 연동 테스트
