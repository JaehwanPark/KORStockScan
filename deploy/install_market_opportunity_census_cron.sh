#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
WRAPPER="$PROJECT_DIR/deploy/run_market_opportunity_census_intraday.sh"
RECEIPT="$PROJECT_DIR/data/runtime/market_opportunity_census/installed_trigger.json"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON" "$TMP_CRON.filtered" "$TMP_CRON.lines"' EXIT

test -x "$WRAPPER"
SYSTEM_TIMEZONE="$(timedatectl show --property=Timezone --value 2>/dev/null || true)"
if [[ "$SYSTEM_TIMEZONE" != "Asia/Seoul" ]]; then
  echo "[FAIL] market opportunity census cron requires system timezone Asia/Seoul; actual=${SYSTEM_TIMEZONE:-unknown}" >&2
  exit 1
fi
crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/MARKET_OPPORTUNITY_CENSUS_/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# market opportunity census source-only capture (5m cadence)
*/5 8 * * 1-5 $WRAPPER \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/run_market_opportunity_census_intraday_cron.log 2>&1 # MARKET_OPPORTUNITY_CENSUS_NXT_PREMARKET_5MIN
*/5 9-14 * * 1-5 $WRAPPER \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/run_market_opportunity_census_intraday_cron.log 2>&1 # MARKET_OPPORTUNITY_CENSUS_KRX_NXT_5MIN
0-30/5 15 * * 1-5 $WRAPPER \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/run_market_opportunity_census_intraday_cron.log 2>&1 # MARKET_OPPORTUNITY_CENSUS_KRX_NXT_CLOSE_5MIN
35-55/5 15 * * 1-5 $WRAPPER \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/run_market_opportunity_census_intraday_cron.log 2>&1 # MARKET_OPPORTUNITY_CENSUS_NXT_TRANSITION_5MIN
*/5 16-19 * * 1-5 $WRAPPER \$(TZ=Asia/Seoul date +\%F) >> $PROJECT_DIR/logs/run_market_opportunity_census_intraday_cron.log 2>&1 # MARKET_OPPORTUNITY_CENSUS_NXT_AFTERMARKET_5MIN
EOF

crontab "$TMP_CRON"
crontab -l | rg 'MARKET_OPPORTUNITY_CENSUS_' > "$TMP_CRON.lines"
test "$(wc -l < "$TMP_CRON.lines")" -eq 5

mkdir -p "$(dirname "$RECEIPT")"
"$PROJECT_DIR/.venv/bin/python" - "$WRAPPER" "$RECEIPT" "$TMP_CRON.lines" <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

wrapper = Path(sys.argv[1]).resolve()
receipt = Path(sys.argv[2])
lines_path = Path(sys.argv[3])
trigger_lines = [line.rstrip() for line in lines_path.read_text(encoding="utf-8").splitlines() if line.strip()]
if len(trigger_lines) != 5:
    raise SystemExit("installed trigger line count mismatch")

sha256 = lambda value: hashlib.sha256(value).hexdigest()
payload = {
    "schema_version": "market_opportunity_census_trigger_v2",
    "trigger_id": "MARKET_OPPORTUNITY_CENSUS_5MIN",
    "enabled": True,
    "contract_source": "installed_crontab_verified",
    "schedule_timezone": "Asia/Seoul",
    "capture_cadence_sec": 300,
    "report_refresh_checkpoints_kst": ["09:15", "12:00", "15:15", "19:45"],
    "installed_exec_start": str(wrapper),
    "wrapper_sha256": sha256(wrapper.read_bytes()),
    "trigger_lines": trigger_lines,
    "trigger_lines_sha256": sha256(("\n".join(trigger_lines) + "\n").encode("utf-8")),
    "installed_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
    "decision_authority": "source_only_scanner_coverage_audit",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
receipt.parent.mkdir(parents=True, exist_ok=True)
fd, temp_name = tempfile.mkstemp(prefix=f".{receipt.name}.", dir=receipt.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_name, receipt)
finally:
    if os.path.exists(temp_name):
        os.unlink(temp_name)
PY

echo "[DONE] market opportunity census cron installed receipt=$RECEIPT"
crontab -l | rg 'MARKET_OPPORTUNITY_CENSUS_'
