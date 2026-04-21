#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
DIFF_DAYS="${DIFF_DAYS:-3}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

START_DATE="$(TZ=Asia/Seoul date -d "$TARGET_DATE -$((DIFF_DAYS - 1)) days" +%F)"

PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
  --dataset pipeline_events \
  --single-date "$TARGET_DATE"

PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
  --dataset post_sell \
  --single-date "$TARGET_DATE"

PYTHONPATH=. "$VENV_PY" -m src.engine.build_tuning_monitoring_parquet \
  --dataset system_metric_samples \
  --single-date "$TARGET_DATE"

PYTHONPATH=. "$VENV_PY" -m src.engine.compare_tuning_shadow_diff \
  --start "$START_DATE" \
  --end "$TARGET_DATE"

"$PROJECT_DIR/analysis/gemini_scalping_pattern_lab/run.sh"
"$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh"
