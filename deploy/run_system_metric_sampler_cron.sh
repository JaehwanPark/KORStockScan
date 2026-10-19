#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"
CPU_AFFINITY="${SYSTEM_METRIC_SAMPLER_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity sampler)}"

cd "$PROJECT_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] system_metric_sampler target_date=${TARGET_DATE} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] system_metric_sampler target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

cmd=(env PYTHONPATH=. "$VENV_PY" -m src.engine.monitoring.system_metric_sampler)
if command -v taskset >/dev/null 2>&1 && [[ -n "$CPU_AFFINITY" ]] && [[ "$(korstockscan_nproc)" -gt 1 ]]; then
  cmd=(taskset -c "$CPU_AFFINITY" "${cmd[@]}")
fi

"${cmd[@]}"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] system_metric_sampler target_date=${TARGET_DATE} finished_at=${finished_at}"
