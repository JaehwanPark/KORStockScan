#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

export PYTHONPATH=.
export KORSTOCKSCAN_SCALPING_AI_ROUTE="${KORSTOCKSCAN_SCALPING_AI_ROUTE:-openai}"
export KORSTOCKSCAN_OPENAI_TRANSPORT_MODE="${KORSTOCKSCAN_OPENAI_TRANSPORT_MODE:-responses_ws}"
export KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED="${KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED:-true}"
export KORSTOCKSCAN_OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED="${KORSTOCKSCAN_OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED:-false}"
export KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED="${KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED:-true}"
export KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE="${KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE:-shadow}"

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] scalp-sim-overnight-preclose target_date=$TARGET_DATE started_at=$started_at"
"$VENV_PY" -m src.engine.scalp_sim_overnight --date "$TARGET_DATE" --live-openai
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] scalp-sim-overnight-preclose target_date=$TARGET_DATE finished_at=$finished_at"
