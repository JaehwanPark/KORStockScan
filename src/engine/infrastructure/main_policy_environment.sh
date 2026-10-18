#!/usr/bin/env bash
# Policy environment shared by the live launcher and load-and-exit validator.
# Sourcing defines functions only; callers own validation and execution.

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

apply_main_policy_defaults() {
    # Parser-compatibility bounds; runtime sizing remains centrally owned.
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
    # Shared completed candles are a source-only projection of the existing
    # durable AL journal. Consumer cutover remains independently opt-in.
    export KORSTOCKSCAN_WS_COMPLETED_BARS_PUBLISH="${KORSTOCKSCAN_WS_COMPLETED_BARS_PUBLISH:-1}"
    export KORSTOCKSCAN_WS_COMPLETED_BAR_SYMBOLS="${KORSTOCKSCAN_WS_COMPLETED_BAR_SYMBOLS:-005930,034020,403870,196170,036930,042660,006800,010140}"
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

}

apply_main_policy_handoff() {
    local policy_target_date="$1" policy_bootstrap_env="$2"
    reset_runtime_policy_env_before_handoff
    if [ -f "$policy_bootstrap_env" ]; then
        echo "📌 threshold runtime env 적용: $policy_bootstrap_env"
        set -a
        # shellcheck source=/dev/null
        . "$policy_bootstrap_env"
        set +a
    fi
    apply_authoritative_ai_context_promotion "$policy_target_date" || return 1
    # Native Main/manual identity uses the common registry, not retired daily policies.
    NATIVE_CUSTODY_ENV="${3:-../data/config/native_owner_custody.env}"
    if [ -f "$NATIVE_CUSTODY_ENV" ]; then
        set -a
        . "$NATIVE_CUSTODY_ENV"
        set +a
    fi
    apply_retired_runtime_policy_env || return 1
}

apply_main_policy_final_environment() {
    # Reassert removed one-off namespaces after verification. bot_main also
    # normalizes every retired prefix before importing trading modules.
    unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC
    unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS
    # This release selects the reviewed zero-base SCALPING discovery owner.
    # It is applied after dated policy/owner overlays so the PID receipt shows
    # the effective scanner route selected by this immutable launcher.
    export KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=true
    # Explicit Main fixed-watch cutover. An operator false value remains the
    # scoped rollback; admission still requires exact broker and owner facts.
    export KORSTOCKSCAN_MAIN_FIXED_WATCH_005930_ENABLED="${KORSTOCKSCAN_MAIN_FIXED_WATCH_005930_ENABLED:-true}"
export KORSTOCKSCAN_MAIN_FIXED_WATCH_034020_ENABLED="${KORSTOCKSCAN_MAIN_FIXED_WATCH_034020_ENABLED:-true}"
export KORSTOCKSCAN_MAIN_FIXED_WATCH_403870_ENABLED="${KORSTOCKSCAN_MAIN_FIXED_WATCH_403870_ENABLED:-true}"
export KORSTOCKSCAN_MAIN_FIXED_WATCH_196170_ENABLED="${KORSTOCKSCAN_MAIN_FIXED_WATCH_196170_ENABLED:-true}"
export KORSTOCKSCAN_MAIN_FIXED_WATCH_036930_ENABLED="${KORSTOCKSCAN_MAIN_FIXED_WATCH_036930_ENABLED:-true}"
}
