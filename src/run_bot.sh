#!/bin/bash

THRESHOLD_RUNTIME_ENV_WAIT_SEC="${KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_WAIT_SEC:-1800}"
THRESHOLD_RUNTIME_ENV_REQUIRED="${KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_REQUIRED:-true}"
THRESHOLD_RUNTIME_ENV_BOOTSTRAP="${KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_BOOTSTRAP:-true}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../deploy/cpu_affinity_profile.sh
. "$PROJECT_DIR/deploy/cpu_affinity_profile.sh"
BOT_CPU_AFFINITY="${KORSTOCKSCAN_BOT_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity bot)}"

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

# 무한 루프 시작
while true; do
    echo "🚀 KORStockScan 스나이퍼 엔진을 시작합니다..."

    # 2026-06-10 operator sizing release:
    # real scalping initial BUY uses 10%~30% of orderable cash, with no hard
    # share cap and a one-share floor only when orderable cash can cover it.
    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN=0.10
    export KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX=0.30
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
    export KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws
    export KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true
    export KORSTOCKSCAN_OPENAI_RESPONSES_WS_POOL_SIZE=2
    export KORSTOCKSCAN_OPENAI_RESPONSES_WS_TIMEOUT_MS=15000
    export KORSTOCKSCAN_OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512
    export KORSTOCKSCAN_OPENAI_REASONING_EFFORT=auto
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_FAMILY=lite_v2
    export KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS=holding_flow
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
    export KORSTOCKSCAN_BEDROCK_PRIMARY_FAILBACK_TO_OPENAI=true
    export KORSTOCKSCAN_BEDROCK_KEY_ROTATION_ENABLED=true
    export KORSTOCKSCAN_SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=true
    export KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_OPEN=10
    export KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_DAILY=30
    export KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=1

    THRESHOLD_RUNTIME_ENV="../data/threshold_cycle/runtime_env/threshold_runtime_env_$(TZ=Asia/Seoul date +%F).env"
    wait_for_threshold_runtime_env "$THRESHOLD_RUNTIME_ENV" || exit 1
    if [ -f "$THRESHOLD_RUNTIME_ENV" ]; then
        echo "📌 threshold runtime env 적용: $THRESHOLD_RUNTIME_ENV"
        set -a
        # shellcheck source=/dev/null
        . "$THRESHOLD_RUNTIME_ENV"
        set +a
    fi

    # 봇 실행 (경로나 파일명은 환경에 맞게 수정)
    cmd=(../.venv/bin/python bot_main.py)
    if command -v taskset >/dev/null 2>&1 && [ -n "$BOT_CPU_AFFINITY" ] && [ "$(korstockscan_nproc)" -gt 1 ]; then
        cmd=(taskset -c "$BOT_CPU_AFFINITY" "${cmd[@]}")
    fi
    "${cmd[@]}"

    echo "🛑 봇 프로세스가 종료되었습니다."
    echo "⏳ 5초 후 엔진을 재가동합니다. (완전 종료를 원하면 지금 Ctrl+C를 누르세요)"
    sleep 5
done

# 깃허브 연동 테스트
