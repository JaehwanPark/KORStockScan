#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
# shellcheck source=cpu_affinity_profile.sh
. "$SCRIPT_DIR/cpu_affinity_profile.sh"
CPU_AFFINITY="${MONITOR_SNAPSHOT_CPU_AFFINITY:-$(korstockscan_default_cpu_affinity monitor)}"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] monitor_snapshot target_date=${TARGET_DATE} profile=${MONITOR_SNAPSHOT_PROFILE:-full} started_at=${started_at}"

trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] monitor_snapshot target_date=${TARGET_DATE} profile=${MONITOR_SNAPSHOT_PROFILE:-full} failed_at=${failed_at}"' ERR

# noon full 점검은 유지하되 remote 비교/일시 burst를 줄이는 기본값을 적용한다.
MONITOR_SNAPSHOT_PROFILE="${MONITOR_SNAPSHOT_PROFILE:-full}" \
MONITOR_SNAPSHOT_IO_DELAY_SEC="${MONITOR_SNAPSHOT_IO_DELAY_SEC:-1.0}" \
MONITOR_SNAPSHOT_START_JITTER_SEC="${MONITOR_SNAPSHOT_START_JITTER_SEC:-0}" \
MONITOR_SNAPSHOT_FULL_TREND_MAX_DATES="${MONITOR_SNAPSHOT_FULL_TREND_MAX_DATES:-12}" \
MONITOR_SNAPSHOT_COOLDOWN_SEC="${MONITOR_SNAPSHOT_COOLDOWN_SEC:-180}" \
MONITOR_SNAPSHOT_LOCK_WAIT_SEC="${MONITOR_SNAPSHOT_LOCK_WAIT_SEC:-180}" \
MONITOR_SNAPSHOT_NOTIFY_ONLY="${MONITOR_SNAPSHOT_NOTIFY_ONLY:-1}" \
MONITOR_SNAPSHOT_ASYNC="${MONITOR_SNAPSHOT_ASYNC:-1}" \
MONITOR_SNAPSHOT_ASYNC_WAIT_SEC="${MONITOR_SNAPSHOT_ASYNC_WAIT_SEC:-1200}" \
MONITOR_SNAPSHOT_IONICE_CLASS="${MONITOR_SNAPSHOT_IONICE_CLASS:-2}" \
MONITOR_SNAPSHOT_IONICE_LEVEL="${MONITOR_SNAPSHOT_IONICE_LEVEL:-6}" \
MONITOR_SNAPSHOT_NICE_LEVEL="${MONITOR_SNAPSHOT_NICE_LEVEL:-10}" \
MONITOR_SNAPSHOT_NOTIFY_ADMIN="${MONITOR_SNAPSHOT_NOTIFY_ADMIN:-0}" \
MONITOR_SNAPSHOT_CPU_AFFINITY="$CPU_AFFINITY" \
"$PROJECT_DIR/deploy/run_monitor_snapshot_safe.sh" "$TARGET_DATE"

finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] monitor_snapshot target_date=${TARGET_DATE} profile=${MONITOR_SNAPSHOT_PROFILE:-full} finished_at=${finished_at}"
