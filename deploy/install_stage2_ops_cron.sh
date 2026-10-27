#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
if [[ "${1:-}" == "--market-weakness-research-only" ]]; then
  shift
  cd "$PROJECT_DIR"
  export PYTHONPATH="$PROJECT_DIR"
  exec "$PROJECT_DIR/.venv/bin/python" -m src.engine.automation.main_market_weakness_research \
    --data-root "$PROJECT_DIR/data" --workspace "$PROJECT_DIR" --configure-optional-cron "$@"
fi
mkdir -p "$PROJECT_DIR/data/runtime"
exec 9>"$PROJECT_DIR/data/runtime/runtime_release_set.lock"
flock -n -x 9 || { echo "runtime_release_transition_in_progress" >&2; exit 1; }
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/^# stage2 ops cron$/ && !/LOG_RETENTION_DAILY/ && !/SNAPSHOT_ARCHIVE_DAILY/ && !/cat[[:space:]]+\/dev\/null.*kiwoom_sniper_v2_info[.]log/ && !/truncate.*kiwoom_sniper_v2_info[.]log/ && !/REMOTE_LATENCY_BASELINE_PREOPEN/ && !/REMOTE_LATENCY_BASELINE_MIDMORNING/ && !/REMOTE_LATENCY_BASELINE_AFTERNOON/ && !/RUN_MONITOR_SNAPSHOT_1000/ && !/RUN_MONITOR_SNAPSHOT_1200/ && !/RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09/ && !/RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11/ && !/REMOTE_SCALPING_FETCH_1600/ && !/SYSTEM_METRIC_SAMPLER_1MIN/ && !/RISING_MISSED_INTRADAY_FEEDBACK_5MIN/ && !/SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN/ && !/INTRADAY_WS_FRESHNESS_MONITOR_/ && !/BUY_FUNNEL_SENTINEL_/ && !/PRE_SUBMIT_SOURCE_/ && !/HOLDING_EXIT_SENTINEL_/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# stage2 ops cron
17 6 * * * bash $PROJECT_DIR/deploy/run_runtime_release.sh log-retention \$(TZ=Asia/Seoul date +\%F) # LOG_RETENTION_DAILY
25 6 * * * bash $PROJECT_DIR/deploy/run_runtime_release.sh snapshot-archive \$(TZ=Asia/Seoul date +\%F) # SNAPSHOT_ARCHIVE_DAILY
* * * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner system_metric_sampler_cron --log $PROJECT_DIR/logs/system_metric_sampler_cron.log $PROJECT_DIR/deploy/run_system_metric_sampler_cron.sh # SYSTEM_METRIC_SAMPLER_1MIN
*/5 8-19 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_buy_funnel_sentinel_cron --log $PROJECT_DIR/logs/run_buy_funnel_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh buy-funnel \$(TZ=Asia/Seoul date +\%F) # BUY_FUNNEL_SENTINEL_ALL_SESSIONS_5MIN
2-57/5 8-19 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_pre_submit_source_monitor_cron --log $PROJECT_DIR/logs/run_pre_submit_source_monitor_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh pre-submit-source \$(TZ=Asia/Seoul date +\%F) # PRE_SUBMIT_SOURCE_ALL_SESSIONS_5MIN
5-55/5 8 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_holding_exit_sentinel_cron --log $PROJECT_DIR/logs/run_holding_exit_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh holding-exit-sentinel \$(TZ=Asia/Seoul date +\%F) # HOLDING_EXIT_SENTINEL_PREMARKET_0805_0855
5-55/5 9 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_holding_exit_sentinel_cron --log $PROJECT_DIR/logs/run_holding_exit_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh holding-exit-sentinel \$(TZ=Asia/Seoul date +\%F) # HOLDING_EXIT_SENTINEL_KRX_0905_0955
*/5 10-14 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_holding_exit_sentinel_cron --log $PROJECT_DIR/logs/run_holding_exit_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh holding-exit-sentinel \$(TZ=Asia/Seoul date +\%F) # HOLDING_EXIT_SENTINEL_KRX_1000_1455
0-30/5 15 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_holding_exit_sentinel_cron --log $PROJECT_DIR/logs/run_holding_exit_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh holding-exit-sentinel \$(TZ=Asia/Seoul date +\%F) # HOLDING_EXIT_SENTINEL_KRX_1500_1530
*/5 16-18 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_holding_exit_sentinel_cron --log $PROJECT_DIR/logs/run_holding_exit_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh holding-exit-sentinel \$(TZ=Asia/Seoul date +\%F) # HOLDING_EXIT_SENTINEL_AFTERMARKET_1600_1855
0-50/5 19 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_holding_exit_sentinel_cron --log $PROJECT_DIR/logs/run_holding_exit_sentinel_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh holding-exit-sentinel \$(TZ=Asia/Seoul date +\%F) # HOLDING_EXIT_SENTINEL_AFTERMARKET_1900_1950
*/5 8-19 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner rising_missed_intraday_feedback_cron --log $PROJECT_DIR/logs/run_rising_missed_intraday_feedback_cron.log $PROJECT_DIR/deploy/run_rising_missed_intraday_feedback.sh # RISING_MISSED_INTRADAY_FEEDBACK_5MIN
5-55/5 9-14 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_intraday_ws_freshness_monitor_cron --log $PROJECT_DIR/logs/run_intraday_ws_freshness_monitor_cron.log $PROJECT_DIR/deploy/run_intraday_ws_freshness_monitor.sh # INTRADAY_WS_FRESHNESS_MONITOR_5MIN
0,5,10,15,20 15 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_intraday_ws_freshness_monitor_cron --log $PROJECT_DIR/logs/run_intraday_ws_freshness_monitor_cron.log $PROJECT_DIR/deploy/run_intraday_ws_freshness_monitor.sh # INTRADAY_WS_FRESHNESS_MONITOR_5MIN
*/5 16-18 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_intraday_ws_freshness_monitor_cron --log $PROJECT_DIR/logs/run_intraday_ws_freshness_monitor_cron.log $PROJECT_DIR/deploy/run_intraday_ws_freshness_monitor.sh # INTRADAY_WS_FRESHNESS_MONITOR_AFTERMARKET_5MIN
0-50/5 19 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_intraday_ws_freshness_monitor_cron --log $PROJECT_DIR/logs/run_intraday_ws_freshness_monitor_cron.log $PROJECT_DIR/deploy/run_intraday_ws_freshness_monitor.sh # INTRADAY_WS_FRESHNESS_MONITOR_AFTERMARKET_5MIN
35-55/20 9 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_monitor_snapshot_cron --log $PROJECT_DIR/logs/run_monitor_snapshot_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh monitor-snapshot \$(TZ=Asia/Seoul date +\%F) # RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09
*/20 10-11 * * 1-5 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_monitor_snapshot_cron --log $PROJECT_DIR/logs/run_monitor_snapshot_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh monitor-snapshot \$(TZ=Asia/Seoul date +\%F) # RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11
0 12 * * 1-5 MONITOR_SNAPSHOT_START_JITTER_SEC=0 bash $PROJECT_DIR/deploy/run_with_owned_log.sh --owner run_monitor_snapshot_cron --log $PROJECT_DIR/logs/run_monitor_snapshot_cron.log bash $PROJECT_DIR/deploy/run_runtime_release.sh monitor-snapshot \$(TZ=Asia/Seoul date +\%F) # RUN_MONITOR_SNAPSHOT_1200
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
